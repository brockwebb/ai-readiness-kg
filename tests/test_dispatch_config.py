"""This project's `dispatch:` block, and the one assertion that has to live on this side.

`cc_tasks/2026-09-15_standing_dispatcher.md` decision 2: "c4 resolves the standing band through
a reference (`seldon.yaml dispatch.standing_band_ref: controls.yaml#spend.daily_tokens`), never
a copied number; **a test asserts the resolved value equals what `kg/spend.py` reads**."

That test cannot live in the Seldon repo — `kg/spend.py` is this project's module and Seldon
has no business importing it — so the reference-resolution MECHANISM is tested there against a
fixture and the EQUALITY is tested here against the two real readers. Between them the claim is
whole: the resolver reads what it is pointed at, and what it is pointed at is what the spend
guard enforces.

The failure this guards is a number, not a bug: a `standing_band: 55000000` written into
`seldon.yaml` instead of a reference would agree with `controls.yaml` on the day it was typed
and diverge the first time the operator moved the cap, with nothing to say it had.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

DISPATCH = yaml.safe_load((REPO / "seldon.yaml").read_text(encoding="utf-8"))["dispatch"]


def test_the_standing_band_reference_resolves_to_what_kg_spend_reads():
    """The whole point of decision 2's `_ref` suffix, asserted against both readers."""
    from seldon.core.dispatch import resolve_standing_band
    from kg import spend

    resolved = resolve_standing_band(REPO, DISPATCH["standing_band_ref"])
    enforced = int(spend._spend_config()["daily_tokens"])
    assert resolved == enforced, (
        f"seldon.yaml dispatch.standing_band_ref resolves to {resolved:,} and the spend guard "
        f"enforces {enforced:,}; the dispatcher would admit a task the guard refuses")


def test_the_band_is_a_reference_and_no_copied_number_sits_beside_it():
    """`standing_band_ref` and nothing else. A second key holding the value — under any name —
    is the copy this design forbids, and it would be read by whoever found it first."""
    assert DISPATCH["standing_band_ref"] == "controls.yaml#spend.daily_tokens"
    numeric = {k: v for k, v in DISPATCH.items()
               if isinstance(v, int) and not isinstance(v, bool) and v > 1_000_000}
    assert numeric == {}, f"a token-scale number is written into the dispatch block: {numeric}"


def test_the_dispatch_block_is_complete_and_the_dispatcher_is_enabled():
    """**Enabled since 2026-09-16**, by `cc_tasks/2026-09-16_cadence_and_enable.md` decision 3.

    The standing-dispatcher task shipped this `false` and said so; the cadence task turned it on
    after its own gate passed. The assertion is inverted rather than deleted because the value
    is a decision either way: a dispatcher silently switched off is the same defect as one
    silently switched on, and the test is where a reader finds out which is true today.

    To stop the world without touching this file, the STOP file is the mechanism
    (`.seldon/DISPATCH_STOP`) — which is why flipping this key is not the routine control."""
    from seldon.core.dispatch import load_dispatch_config
    cfg = load_dispatch_config(REPO)
    assert cfg["enabled"] is True
    assert cfg["branch"] == "main"
    assert cfg["permission_mode"] == "bypassPermissions"
    assert cfg["poll_interval_s"] == 300


def test_the_plist_interval_and_the_declared_interval_are_one_number():
    """One parameter written twice: the file that EXPLAINS it is `seldon.yaml`, the file that
    ACTS on it is the plist. The wrapper refuses a pass when they disagree; this catches the
    disagreement at the gate instead of at 3 a.m."""
    import re
    plist = (REPO / "scripts" / "jobs" / "com.brock.airkg-dispatch.plist").read_text(
        encoding="utf-8")
    m = re.search(r"<key>StartInterval</key>\s*<integer>(\d+)</integer>", plist)
    assert m, "the plist declares no StartInterval"
    assert int(m.group(1)) == DISPATCH["poll_interval_s"]


def test_the_wrapper_refuses_when_the_two_intervals_disagree(tmp_path):
    """The refusal itself, exercised — not merely asserted to exist. Run the wrapper against a
    copy of the repo whose plist says something else, and it must exit 2 having dispatched
    nothing."""
    import shutil
    fake = tmp_path / "repo"
    (fake / "scripts" / "jobs").mkdir(parents=True)
    (fake / "logs").mkdir()
    shutil.copy(REPO / "scripts" / "jobs" / "airkg_dispatch.sh",
                fake / "scripts" / "jobs" / "airkg_dispatch.sh")
    shutil.copy(REPO / "controls.yaml", fake / "controls.yaml")
    (fake / "seldon.yaml").write_text(
        yaml.safe_dump({"dispatch": {**DISPATCH, "poll_interval_s": 900}}), encoding="utf-8")
    plist = (REPO / "scripts" / "jobs" / "com.brock.airkg-dispatch.plist").read_text(
        encoding="utf-8")
    (fake / "scripts" / "jobs" / "com.brock.airkg-dispatch.plist").write_text(
        plist, encoding="utf-8")
    r = subprocess.run(["/bin/bash", str(fake / "scripts" / "jobs" / "airkg_dispatch.sh")],
                       capture_output=True, text=True)
    assert r.returncode == 2, r.stdout + r.stderr
    log = (fake / "logs" / "airkg_dispatch.log").read_text(encoding="utf-8")
    assert "REFUSING" in log and "poll_interval_s=900" in log


def test_the_lease_and_the_dispatch_logs_are_gitignored():
    """A dispatched session's transcript is a local artifact; what ships is the RESULT it
    wrote. The lease is runtime state and belongs to no commit."""
    for rel in (DISPATCH["log_dir"] + "/example.log", DISPATCH["lease_file"]):
        r = subprocess.run(["git", "check-ignore", "-q", rel], cwd=REPO)
        assert r.returncode == 0, f"{rel} is not gitignored"


def test_claude_md_carries_the_marker_rule_and_the_no_hand_dispatch_rule():
    """DN-006 decision 3 and decision 10, as amended by the task's ADDENDUM_01: the bootloader
    says what makes a task dispatchable, because a rule that lives only in a design note is a
    rule the next session has to go looking for."""
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    protocol = text.split("## CC dispatch protocol", 1)[1].split("###", 1)[0]
    assert "**Status:** SUPERSEDED" in protocol
    assert "within its first ten lines" in protocol
    for header in ("**Spend:**", "**Network:**", "**Framework layer served"):
        assert header in protocol, header
    assert "the operator does not hand-dispatch" in protocol
    assert "DN-006 decision 10" in protocol


# ---------------------------------------------------------------------------
# The launchd environment, and the credentials it does not have
# ---------------------------------------------------------------------------
#
# `cc_tasks/2026-09-16_cadence_and_enable.md` §3. The first scheduled pass fired on time and
# died on `neo4j.exceptions.AuthError`: **a launchd job inherits almost no environment**, so the
# NEO4J_* variables a hand-run `seldon dispatch` picks up from the shell are simply absent. The
# wrapper now falls back to `~/.wintermute/.env`, which is this repo's existing convention
# (CLAUDE.md; `scripts/build_projection.py::_neo4j_creds` is the parse it copies).
#
# Both halves of the fix are tested, because the first attempt at it passed the "does it find
# credentials" question and still failed: `tr -d` deleted EVERY quote character in the value,
# and this password contains one, so it authenticated with a password one character short —
# `AuthError`, indistinguishable from a wrong password and from no password at all.

WRAPPER = REPO / "scripts" / "jobs" / "airkg_dispatch.sh"


def _bare_env_run(home: Path):
    """The wrapper under `env -i`, which is as close to launchd's environment as a test gets."""
    return subprocess.run(
        ["/usr/bin/env", "-i", f"HOME={home}", "PATH=/usr/bin:/bin", "/bin/bash", str(WRAPPER)],
        capture_output=True, text=True, cwd=REPO)


def test_the_wrapper_refuses_loudly_when_no_credentials_can_be_found(tmp_path):
    """Fail loud and early, naming what is missing — never a pass that runs without a queue it
    can read. Exit 3 is distinct from the interval refusal's 2, so the log says which."""
    (tmp_path / ".wintermute").mkdir()
    (tmp_path / ".wintermute" / ".env").write_text("OPENALEX_API_KEY=x\n", encoding="utf-8")
    log = REPO / "logs" / "airkg_dispatch.log"
    before = log.read_text(encoding="utf-8") if log.is_file() else ""
    r = _bare_env_run(tmp_path)
    assert r.returncode == 3, r.stdout + r.stderr
    added = (log.read_text(encoding="utf-8") if log.is_file() else "")[len(before):]
    assert "REFUSING" in added and "no Neo4j credentials" in added


def test_the_credential_parse_strips_one_surrounding_quote_pair_and_no_more(tmp_path):
    """The defect that made the first fix wrong, isolated from Neo4j.

    A value written `"pa'ss"` is the ten characters between the outer quotes, apostrophe
    included. Deleting every quote character yields nine, and nine authenticates against
    nothing."""
    home = tmp_path / "home"
    (home / ".wintermute").mkdir(parents=True)
    (home / ".wintermute" / ".env").write_text(
        'NEO4J_USER="neo4j"\nNEO4J_PASS="pa\'ss word"\nOTHER=ignored\n', encoding="utf-8")
    # The wrapper's parse, lifted verbatim from the file so the test cannot drift from it.
    block = WRAPPER.read_text(encoding="utf-8")
    start = block.index('WM_ENV="$HOME/.wintermute/.env"')
    end = block.index("if [ -z \"${NEO4J_USERNAME:-}${NEO4J_USER:-}\" ] || ")
    # Comments dropped before the block is run: `tests/conftest.py` refuses to spawn any
    # command whose text mentions the projection replay script, and one of these comments cites
    # it by path. The guard is right; the comment is not code.
    script = "\n".join(ln for ln in block[start:end].splitlines()
                       if not ln.lstrip().startswith("#"))
    script += '\nprintf "%s|%s" "$NEO4J_USER" "$NEO4J_PASS"\n'
    r = subprocess.run(["/usr/bin/env", "-i", f"HOME={home}", "PATH=/usr/bin:/bin",
                        "/bin/bash", "-c", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout == "neo4j|pa'ss word", repr(r.stdout)


@pytest.mark.skipif(
    not (REPO / ".." / "seldon").exists(), reason="seldon checkout not beside this repo")
def test_a_pass_in_a_launchd_shaped_environment_reaches_the_queue_and_writes_no_event():
    """End to end, in the environment that actually broke: no shell, no exported credentials.

    The pass must reach the graph, find nothing eligible, exit 0, and leave the event log
    **byte-identical** — DN-006 decision 7. Skipped rather than failed when Neo4j is down,
    because that is a fact about the machine and not about this wrapper."""
    import hashlib
    sys.path.insert(0, str(REPO))
    from scripts import build_projection as proj
    if not proj.neo4j_reachable():
        pytest.skip("Neo4j is not reachable")

    events = REPO / "seldon_events.jsonl"
    before = hashlib.sha256(events.read_bytes()).hexdigest()
    r = _bare_env_run(Path.home())
    after = hashlib.sha256(events.read_bytes()).hexdigest()
    log = (REPO / "logs" / "airkg_dispatch.log").read_text(encoding="utf-8")
    tail = log[log.rfind("=== 20"):]
    assert r.returncode == 0, tail
    assert "AuthError" not in tail and "Traceback" not in tail
    assert "=== rc=0" in tail
    assert after == before, "a pass wrote to the event log"
