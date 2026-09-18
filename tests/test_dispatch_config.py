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

import os
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


def test_claude_md_headless_rule_is_the_launch_prompts_clause_byte_for_byte():
    """`cc_tasks/2026-09-16_headless_session_polls_to_completion.md` decision 2. The launch
    prompt tells a dispatched session it is headless; CLAUDE.md tells an interactive reader why.
    One sentence in two places drifts unless a test holds them together, so this reads the
    rule from the paragraph and compares it to the dispatcher's own constant."""
    from seldon.commands.dispatch import DISPATCH_LINE, HEADLESS_CLAUSE, HEADLESS_ENV
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    section = text.split("### Long-running commands", 1)[1].split("\n### ", 1)[0]
    para = [p for p in section.split("\n\n") if p.startswith("**Headless sessions**")]
    assert len(para) == 1, "CLAUDE.md long-running-commands section lacks the headless paragraph"
    head = "asserts the two are byte-identical: "
    tail = " The dispatcher also launches"
    rule = para[0].split(head, 1)[1].split(tail, 1)[0]
    assert rule.encode("utf-8") == HEADLESS_CLAUSE.encode("utf-8")
    assert DISPATCH_LINE.endswith(HEADLESS_CLAUSE)
    assert "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1" in para[0]
    assert HEADLESS_ENV == {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}
    assert "2026-09-16T14:44:47Z" in para[0]


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


#: The wrapper's own log. Only the tests that run a REAL pass write to it, and they read it back.
LIVE_LOG = REPO / "logs" / "airkg_dispatch.log"


def _bare_env_run(home: Path, log: Path):
    """The wrapper under `env -i`, which is as close to launchd's environment as a test gets.

    `AIRKG_DISPATCH_LOG` points the wrapper at a file under `tmp_path`: a refusal this fixture
    provokes is not a pass, and it does not belong in the live log beside real ones
    (cc_tasks/2026-09-17_dispatcher_notifies.md decision 4)."""
    return subprocess.run(
        ["/usr/bin/env", "-i", f"HOME={home}", "PATH=/usr/bin:/bin",
         f"AIRKG_DISPATCH_LOG={log}", "/bin/bash", str(WRAPPER)],
        capture_output=True, text=True, cwd=REPO)


def test_the_wrapper_refuses_loudly_when_no_credentials_can_be_found(tmp_path):
    """Fail loud and early, naming what is missing — never a pass that runs without a queue it
    can read. Exit 3 is distinct from the interval refusal's 2, so the log says which."""
    (tmp_path / ".wintermute").mkdir()
    (tmp_path / ".wintermute" / ".env").write_text("OPENALEX_API_KEY=x\n", encoding="utf-8")
    log = tmp_path / "logs" / "airkg_dispatch.log"
    live = LIVE_LOG
    live_before = live.read_text(encoding="utf-8") if live.is_file() else ""
    r = _bare_env_run(tmp_path, log)
    assert r.returncode == 3, r.stdout + r.stderr
    text = log.read_text(encoding="utf-8")
    assert "REFUSING" in text and "no Neo4j credentials" in text
    # The live log may gain a real launchd pass while this runs; it may not gain this refusal.
    live_added = (live.read_text(encoding="utf-8") if live.is_file() else "")[len(live_before):]
    assert "no Neo4j credentials" not in live_added


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


# ---------------------------------------------------------------------------
# DN-006 decision 7, as ADDENDUM_03 amends it: the invariant is IDEMPOTENCE
# ---------------------------------------------------------------------------
#
# The test that used to sit here asserted that ONE pass leaves the event log byte-identical,
# and it could not hold. `cc_tasks/2026-09-16_publication_guards_RESULT.md` §0: the suite ran
# for the first time inside a dispatched session, the lease was held by the very process that
# launched that session, and the pass wrote `dispatch_refused{lease_held}` — correctly. Every
# dispatched task from then on would have reported a red gate for a reason that had nothing to
# do with the task.
#
# Two things changed. The dispatcher now writes ONE `lease_held` refusal per lease ACQUISITION
# rather than one per pass (DN-006 ADDENDUM_03 §1), and the claim asserted here is the one that
# is true in every state the dispatcher can be in: a second pass changes nothing.

SELDON_CHECKOUT = REPO / ".." / "seldon"


def _neo4j_up() -> bool:
    sys.path.insert(0, str(REPO))
    from scripts import build_projection as proj
    return proj.neo4j_reachable()


def _survey() -> dict:
    """`seldon dispatch status --json`, which writes no event. The pass's own criteria vector,
    read without running a pass."""
    import json
    r = subprocess.run(["/opt/anaconda3/bin/seldon", "dispatch", "status", "--json"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


def _wrapper_tail() -> str:
    log = REPO / "logs" / "airkg_dispatch.log"
    text = log.read_text(encoding="utf-8") if log.is_file() else ""
    return text[text.rfind("=== 20"):]


@pytest.mark.skipif(
    not SELDON_CHECKOUT.exists(), reason="seldon checkout not beside this repo")
def test_two_passes_in_a_launchd_shaped_environment_leave_the_event_log_byte_identical():
    """DN-006 decision 7 as ADDENDUM_03 §3 restates it, end to end, in the environment that
    actually broke: no shell, no exported credentials, the real wrapper, the real graph.

    **This test never skips on the state of the queue**, which is the whole point of stating
    the invariant as idempotence. It holds with a task in flight, with a STOP file present,
    with a dirty tree, when disabled and when nothing is eligible — and a test that skipped
    whenever a task was in flight would never run at all, because a dispatched session always
    has one. Neo4j being down is a fact about the machine, not about this wrapper, and is the
    one skip.

    The first pass is allowed its one event: a lease acquisition, a STOP-file appearance and a
    DD-007 refusal are each worth exactly one line. What no state is allowed is a second."""
    import hashlib
    if not _neo4j_up():
        pytest.skip("Neo4j is not reachable")

    # A pass that would LAUNCH is not an idempotence experiment, and running one from inside
    # the suite would start a CC session out of a test. Fail rather than skip: in the only
    # environment DN-006 decision 10 permits the suite to run in — inside a dispatched session
    # — the lease is held for the length of that session and nothing is eligible, so an
    # eligible task here means the checkout is in a state the rule says it cannot be in.
    eligible = _survey()["eligible"]
    assert not eligible, (
        f"a pass would launch {eligible}; the suite must not dispatch a session. Under DN-006 "
        f"decision 10 the operator does not hand-dispatch while the dispatcher is enabled")

    events = REPO / "seldon_events.jsonl"
    first = _bare_env_run(Path.home(), LIVE_LOG)
    after_first = hashlib.sha256(events.read_bytes()).hexdigest()
    tail_first = _wrapper_tail()
    second = _bare_env_run(Path.home(), LIVE_LOG)
    after_second = hashlib.sha256(events.read_bytes()).hexdigest()
    tail_second = _wrapper_tail()

    for r, tail in ((first, tail_first), (second, tail_second)):
        assert r.returncode == 0, tail
        assert "AuthError" not in tail and "Traceback" not in tail, tail
        assert "=== rc=0" in tail
        assert "launching" not in tail, tail

    assert after_second == after_first, (
        "a second pass with nothing changed between them wrote to the event log; "
        f"first pass said: {tail_first!r}")


#: **`interactive_only`**: a test whose precondition a dispatched session cannot be in.
#:
#: The dispatcher sets `SELDON_SESSION_ID` on every session it launches and on no other
#: (`seldon/commands/dispatch.py::_run`; `seldon/config.py::SESSION_ENV_VARS`). Such a session
#: runs holding a claim — its own task is `in_progress` from the moment it starts, and the tree
#: is dirty with its own edits — so the quiet state below does not exist inside it, and the
#: dynamic skip that test states would fire on every dispatched run. Declared here, on the
#: record, so a reader can tell a skip by design from a skip by accident
#: (`cc_tasks/2026-09-17_figure_gate_reads_cycle_of_record.md` decision 3). A named `skipif`
#: rather than a custom marker, so it needs no registration and cannot be silently unknown.
interactive_only = pytest.mark.skipif(
    bool(os.environ.get("SELDON_SESSION_ID")),
    reason="interactive_only: SELDON_SESSION_ID is set, so this is a dispatched session, which "
           "holds its own task's claim and dirties the tree for its whole life; the quiet "
           "checkout this test asserts cannot exist inside one. Run it from an operator shell.")


@interactive_only
@pytest.mark.skipif(
    not SELDON_CHECKOUT.exists(), reason="seldon checkout not beside this repo")
def test_a_single_pass_writes_no_event_when_there_is_nothing_to_assert():
    """Decision 7's original claim, kept and narrowed to the state it is true in.

    That state is the one the cadence task observed: nothing eligible, no claim in flight, a
    clean tree, and the lease free. It is a real state — it is the state the dispatcher spends
    almost all of its life in, twelve passes an hour between sessions — and in it a pass must
    write **nothing at all**, because there is no assertion to record.

    It states its precondition and skips when the checkout is not in it. That is not the skip
    ADDENDUM_03 §3 forbids: the idempotence test above covers every state including this one,
    and this adds the stronger claim where the stronger claim holds.

    It has no configuration-invariant half to split out: every assertion is about what one
    pass does in the quiet state. The half that holds in every state, dispatched sessions
    included, is the idempotence test above, which never skips on queue state.

    Two kinds of skip, and they are different. `interactive_only` is the declared one: inside a
    dispatched session the state cannot be quiet. The reasons listed below are data conditions
    in an operator shell: the state could be quiet, and at this moment is not."""
    import hashlib
    if not _neo4j_up():
        pytest.skip("Neo4j is not reachable")
    s = _survey()
    reasons = []
    if s["eligible"]:
        reasons.append(f"eligible: {s['eligible']}")
    if s["claim_in_flight"]:
        reasons.append("a claim is in flight")
    if s["tree_dirty"]:
        reasons.append(f"tree dirty ({s['tree_dirty_count']} path(s))")
    if (s["lease"] or {}).get("holder"):
        reasons.append(f"lease held by {s['lease']['holder']}")
    if s["stop_file_present"]:
        reasons.append("STOP file present")
    if not s["enabled"]:
        reasons.append("dispatch disabled")
    if reasons:
        pytest.skip("not the quiet state this asserts: " + "; ".join(reasons))

    events = REPO / "seldon_events.jsonl"
    before = hashlib.sha256(events.read_bytes()).hexdigest()
    r = _bare_env_run(Path.home(), LIVE_LOG)
    tail = _wrapper_tail()
    assert r.returncode == 0, tail
    assert "=== rc=0" in tail and "launching" not in tail
    assert hashlib.sha256(events.read_bytes()).hexdigest() == before, (
        "a pass with nothing to assert wrote to the event log")


def test_the_repo_carries_the_addendum_that_amended_decision_seven():
    """The rule §1 of it states — a standing condition earns an event only when its beginning
    is recorded nowhere else — is the one a reader needs to decide the NEXT refusal reason. A
    rule that lives only in a commit message is a rule the next author re-invents."""
    add = REPO / "docs" / "design" / \
        "2026-09-15_DN-006_standing_dispatcher_ADDENDUM_03.md"
    text = add.read_text(encoding="utf-8")
    assert "**Status:** AMENDS" in "\n".join(text.splitlines()[:10])
    for reason in ("lease_held", "stop_file", "dirty_tree", "disabled", "above_band",
                   "network_undeclared", "api_key_present", "claim_failed"):
        assert reason in text, f"{reason} is not accounted for in ADDENDUM_03's table"
    assert "one per acquisition" in text


# ---------------------------------------------------------------------------
# The first Monday: nothing renders, because this project has no schedule
# ---------------------------------------------------------------------------
#
# `cc_tasks/2026-09-18_cadence_off.md` decision 3. Until 2026-09-18 this section asserted that
# cycle 5 fell due at the 2026-10-05 tick and named the reasons a tick could be blocked. The
# operator turned the schedule off that day (DN-006 ADDENDUM_07): a scan cycle is requested, not
# scheduled. What this asserts now is the absence: at the instant the old rule would have fired,
# the installed dispatcher's cadence step evaluates nothing, creates nothing and says nothing.
#
# Run against a scratch directory, not this checkout, so a render could not land in `cc_tasks/`.

#: 2026-10-05 is the first Monday of October 2026 and 00:30Z was inside the old rule's due
#: window: the one instant a leftover entry would have fired.
FIRST_MONDAY_TICK = "2026-10-05T00:30:00+00:00"


def test_nothing_renders_on_the_first_monday(tmp_path, monkeypatch, capsys):
    from datetime import datetime
    from seldon.commands import dispatch as CMD
    from seldon.core.dispatch import load_dispatch_config
    cfg = load_dispatch_config(REPO)
    assert cfg["cadence"] == []
    monkeypatch.setattr(CMD, "_utcnow", lambda: datetime.fromisoformat(FIRST_MONDAY_TICK))
    tree = {"branch": "main", "dirty": False, "dirty_paths": [], "dirty_count": 0}
    rows = CMD._cadence(tmp_path, {}, None, None, None, None, cfg, tree, None, False)
    captured = capsys.readouterr()
    assert rows == []
    assert "cadence" not in captured.out + captured.err
    assert list(tmp_path.rglob("*")) == []


def test_the_pass_commits_the_dispatchers_lines_and_registered_files_before_the_cadence():
    """The ordering decision 3 re-reads the gate against: the dispatcher's own leftover lines
    and any registered-but-uncommitted Desktop file are committed BEFORE `_cadence` looks at
    the tree, so neither can be the dirt that blocks a tick. Read from the installed source,
    because the ordering is the claim."""
    import inspect
    from seldon.commands import dispatch as CMD
    src = inspect.getsource(CMD._pass)
    body = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    own = body.index("_record_own_lines(")
    registered = body.index("_commit_registered(")
    cadence = body.index("_cadence(")
    assert own < registered < cadence, (own, registered, cadence)
