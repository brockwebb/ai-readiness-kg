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


def test_the_dispatch_block_is_complete_and_ships_disabled():
    """**This task does not enable it.** Enabling is the first line of the cadence task, after
    the operator-dispatched queue has drained under DN-006 decision 10."""
    from seldon.core.dispatch import load_dispatch_config
    cfg = load_dispatch_config(REPO)
    assert cfg["enabled"] is False
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
