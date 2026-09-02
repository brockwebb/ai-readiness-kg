"""The burn state file merges by batch id; it never drops another batch's verdict.

Task 2026-09-02_spend_guard_exit1_and_state_merge, defect 2. `write_burn_state` rewrote
`state/bulk_v038_burn.json` wholesale from the rows the CURRENT run's loop had reached, so
the 2026-09-01 tome run (pid 46272) dropped b006, b007 and b010–b015 at its first write
(after b005, 00:14:57Z) and, dying at b009, never reached b010–b015 to carry them back.
The relaunch re-judged them from persisted labels at zero cost — a driver that could not
replay would have re-spent ~9M tokens.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import run_chunked_bulk as rcb  # noqa: E402


def _row(bid, outcome, **extra):
    return {"batch_id": f"bulk_v038_{bid}", "outcome": outcome, "facts": 110,
            "fabrications": 2, **extra}


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(rcb, "STATE_DIR", tmp_path)
    return tmp_path


def _write(rows, stopped=None):
    st = rcb.BurnState()
    for r in rows:
        st.record(r["outcome"])
    st.stopped_by = stopped
    rcb.write_burn_state(rows, st, rcb.sprt_boundaries(), 463, 55)


def _read(state_dir):
    return json.loads((state_dir / "bulk_v038_burn.json").read_text(encoding="utf-8"))


# --- positive control: A, then B through the same path; A survives -----------------------
def test_writing_batch_b_keeps_batch_a(state_dir):
    _write([_row("b001", "accept")])
    _write([_row("b002", "sampling_inconclusive")])          # a later run that never saw A
    out = _read(state_dir)
    assert [(r["batch_id"], r["outcome"]) for r in out["batches"]] == [
        ("bulk_v038_b001", "accept"), ("bulk_v038_b002", "sampling_inconclusive")]
    assert out["outcomes"] == ["accept", "sampling_inconclusive"]
    assert out["batches"][0]["facts"] == 110, "the kept row keeps its evidence"


def test_the_2026_09_01_shape_a_run_whose_loop_never_reaches_later_batches(state_dir):
    """Disk holds b001–b004, b006, b007, b010–b015 (the scoped burn). A tome run judges
    b005 and writes. Every earlier verdict must still be there — including the ones the
    tome run's loop had not reached."""
    scoped = [_row(f"b{n:03d}", "sampling_inconclusive" if n == 10 else "accept")
              for n in (1, 2, 3, 4, 6, 7, 10, 11, 12, 13, 14, 15)]
    _write(scoped)
    _write([_row("b005", "accept")])
    out = _read(state_dir)
    ids = [r["batch_id"][-4:] for r in out["batches"]]
    assert ids == [f"b{n:03d}" for n in range(1, 16) if n not in (8, 9)]
    assert out["outcomes"].count("sampling_inconclusive") == 1
    assert len(out["batches"]) == len(out["outcomes"])


# --- a verdict is immutable; a conflicting rewrite is refused and logged ------------------
@pytest.mark.parametrize("first", ["accept", "reject", "sampling_inconclusive", "quarantine"])
def test_a_second_write_with_a_different_verdict_is_refused_and_logged(state_dir, first,
                                                                        capsys):
    _write([_row("b003", first)])
    other = "reject" if first != "reject" else "accept"
    _write([_row("b003", other, facts=999)])
    out = _read(state_dir)
    assert len(out["batches"]) == 1
    assert out["batches"][0]["outcome"] == first
    assert out["batches"][0]["facts"] == 110, "the refused row changed nothing"
    conflicts = out["verdict_conflicts"]
    assert len(conflicts) == 1
    assert conflicts[0]["batch_id"] == "bulk_v038_b003"
    assert conflicts[0]["kept"] == first and conflicts[0]["refused"] == other
    assert conflicts[0]["ts"]
    assert "verdict_conflict" in capsys.readouterr().err


def test_the_same_verdict_may_be_updated_in_place(state_dir):
    """`phase_burn` writes a batch twice: once with the verdict, once with report-only yield
    flags attached. Same verdict, richer row — that is an update, not a conflict."""
    _write([_row("b001", "accept")])
    _write([_row("b001", "accept", yield_flags={"academic": "above_envelope"})])
    out = _read(state_dir)
    assert len(out["batches"]) == 1
    assert out["batches"][0]["yield_flags"] == {"academic": "above_envelope"}
    assert out.get("verdict_conflicts", []) == []


def test_a_non_verdict_row_may_be_replaced_by_a_verdict(state_dir):
    _write([_row("b001", "protocol_failed")])
    _write([_row("b001", "accept")])
    assert _read(state_dir)["batches"][0]["outcome"] == "accept"


def test_a_row_without_a_batch_id_is_refused_loudly(state_dir):
    with pytest.raises(ValueError, match="batch_id"):
        _write([{"outcome": "accept"}])


def test_the_header_reflects_this_run_and_the_stop_reason(state_dir):
    _write([_row("b001", "accept")], stopped="spend refusal on b002")
    out = _read(state_dir)
    assert out["stopped"] == "spend refusal on b002"
    assert out["task"] == rcb.TASK and out["profile"] == rcb.PROFILE
    assert out["written_at"]


def test_a_corrupt_state_file_is_not_silently_replaced(state_dir):
    (state_dir / "bulk_v038_burn.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        _write([_row("b001", "accept")])
    assert (state_dir / "bulk_v038_burn.json").read_text() == "{not json"
