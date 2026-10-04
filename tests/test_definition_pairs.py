"""Tests for the cross-document definition conflict pass (`scripts/run_definition_pairs.py`).

Task `cc_tasks/2026-10-04_definition_conflict_pass.md`: the pair list is complete and
unordered-unique, same-document pairs are excluded and counted, the vocabularies are closed,
every `conflict` row has a kind and two spans, the controls are recorded, and the paid loop
survives a SIGKILL without repeating a completed call (`~/GitHub/CLAUDE.md` §15 item 8).
No test here makes a model call or needs Neo4j.
"""
from __future__ import annotations

import csv
import io
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import run_definition_pairs as R  # noqa: E402

SCRIPT = REPO / "scripts" / "run_definition_pairs.py"


@pytest.fixture(scope="module")
def q1():
    rows, epoch = R.load_q1()
    return rows, epoch


@pytest.fixture(scope="module")
def shipped_rows():
    if not R.OUT_CSV.is_file():
        pytest.fail(f"{R.OUT_CSV} missing: the pass has not been rendered")
    return list(csv.DictReader(io.StringIO(R.OUT_CSV.read_text(encoding="utf-8"))))


# ----------------------------------------------------------------------------- pair list

def test_pair_list_complete_and_unordered_unique(q1):
    rows, _ = q1
    pairs, same_doc = R.build_pairs(rows)
    doc = {r["node_key"]: r["doc_id"] for r in rows}
    keys = sorted(doc)
    expected = {(a, b) for i, a in enumerate(keys) for b in keys[i + 1:] if doc[a] != doc[b]}
    got = [(p["key_a"], p["key_b"]) for p in pairs]
    assert len(got) == len(set(got)), "a pair appears twice"
    assert all(a < b for a, b in got), "a pair is not in canonical (unordered) order"
    assert set(got) == expected
    assert len({frozenset(g) for g in got}) == len(got)
    assert len(got) + same_doc == len(rows) * (len(rows) - 1) // 2


def test_same_document_pairs_excluded_and_counted(q1):
    rows, _ = q1
    pairs, same_doc = R.build_pairs(rows)
    assert all(p["doc_a"] != p["doc_b"] for p in pairs)
    per_doc: dict = {}
    for r in rows:
        per_doc[r["doc_id"]] = per_doc.get(r["doc_id"], 0) + 1
    assert same_doc == sum(n * (n - 1) // 2 for n in per_doc.values())
    assert same_doc > 0, "positive control for the skip: the set has documents with >1 definition"


def test_pair_build_is_insensitive_to_input_order(q1):
    rows, _ = q1
    assert R.build_pairs(rows) == R.build_pairs(list(reversed(rows)))


def test_controls_are_pairs_of_the_set(q1):
    rows, _ = q1
    R.validate_controls(rows)
    assert len(R.POSITIVE_CONTROLS) >= 6 and len(R.NEGATIVE_CONTROLS) >= 4


# ----------------------------------------------------------------------------- judge parts

def test_parser_closed_vocabulary():
    ok = R.parse_answer("OUTCOME: conflict\nKIND: scope\nCONFIDENCE: 0.7\nREASON: x \"a\" y.")
    assert ok["status"] == "judged" and ok["kind"] == "scope"
    for bad in ("OUTCOME: contradicts\nKIND: scope\nCONFIDENCE: 0.7\nREASON: r",
                "OUTCOME: conflict\nKIND: none\nCONFIDENCE: 0.7\nREASON: r",       # conflict needs a kind
                "OUTCOME: consistent\nKIND: scope\nCONFIDENCE: 0.7\nREASON: r",    # consistent takes none
                "OUTCOME: not_comparable\nKIND: none\nCONFIDENCE: 0.7\nREASON:",   # reason required
                "no answer at all"):
        assert R.parse_answer(bad)["status"] == "unparsed", bad
    nc = R.parse_answer("OUTCOME: not_comparable\nKIND: none\nCONFIDENCE: 0.9\nREASON: a person vs data.")
    assert nc["status"] == "judged" and nc["kind"] is None


def test_reason_check_is_mechanical():
    a, b = "data that is discoverable and documented", "the human capability to work"
    assert R.reason_check('"discoverable" against "human capability"', a, b) == "ok"
    assert R.reason_check("no quotes at all", a, b) == "no_quote"
    assert R.reason_check('"discoverable" against "machine learning"', a, b) == "quote_not_in_spans"


def test_paraphrase_is_deterministic_and_changes_every_negative_control_surface_only():
    t = "Institutional readiness is an organisational capacity, a skill, and **judgment** [12]"
    out, applied = R.script_paraphrase(t)
    assert out == R.script_paraphrase(t)[0]
    assert out == "Institutional readiness is an organizational capacity, a skill and judgment"
    assert set(applied) == {"strip_markdown_emphasis", "strip_numeric_citations",
                            "drop_serial_comma", "american_spelling"}


def test_criteria_version_is_the_rubric_hash():
    import hashlib
    assert R.CRITERIA_VERSION == hashlib.sha256(R.INSTRUCTIONS.encode()).hexdigest()[:16]


def test_prompt_is_blind():
    p = R.build_prompt("t1", "span one", "t2", "span two")
    assert "doc" not in p.split("---", 1)[1].lower()


# ----------------------------------------------------------------------------- shipped CSV

def test_csv_covers_exactly_the_pair_list(q1, shipped_rows):
    rows, _ = q1
    pairs, _ = R.build_pairs(rows)
    assert [r["pair_id"] for r in shipped_rows] == [p["pair_id"] for p in pairs]
    assert list(shipped_rows[0].keys()) == list(R.CSV_COLUMNS)


def test_csv_closed_vocabularies(shipped_rows):
    for r in shipped_rows:
        assert r["status"] in R.STATUSES
        assert r["adjudicated"] == "false"
        assert r["quarantined"] in ("true", "false")
        if r["status"] == "judged":
            assert r["outcome"] in R.OUTCOMES
            if r["outcome"] in R.KINDED:
                assert r["kind"] in R.KINDS, r["pair_id"]
            else:
                assert r["kind"] == "", r["pair_id"]
            assert r["reason"], r["pair_id"]
        else:
            assert r["outcome"] == "" and r["kind"] == ""


def test_every_conflict_row_has_kind_two_spans_and_an_edge_disposition(shipped_rows):
    for r in shipped_rows:
        if r["outcome"] != "conflict":
            assert r["quarantined"] == "false" and r["edge_event_id"] == ""
            continue
        assert r["kind"] in R.KINDS
        assert r["quote_a"] and r["quote_b"]
        for q in (r["quote_a"], r["quote_b"]):
            assert len(q.replace(" …", "").split()) < 15
        assert r["quarantined"] == "true" and r["quarantine_reason"]


def test_controls_recorded(shipped_rows):
    pos = [r for r in shipped_rows if r["control"] == "positive"]
    assert len(pos) == len(R.POSITIVE_CONTROLS)
    assert all(r["control_source"] for r in pos)
    md = R.OUT_MD.read_text(encoding="utf-8")
    assert R.CONTROL_CRITERION["positive"] in md and R.CONTROL_CRITERION["negative"] in md
    assert md.count("| negative |") == len(R.NEGATIVE_CONTROLS)
    assert md.count("| positive |") == len(R.POSITIVE_CONTROLS)


def test_check_reports_no_drift():
    out = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True,
                         cwd=REPO)
    assert out.returncode == 0, out.stdout + out.stderr


# ----------------------------------------------------------------------------- §15 item 8

def _spec(tmp: Path, units: list, sleep_s: float) -> Path:
    neg = {u["unit_id"] for u in units if u["unit_kind"] == "negative_control"}
    consistent = "OUTCOME: consistent\nKIND: none\nCONFIDENCE: 0.9\nREASON: same \"x\"."
    differs = "OUTCOME: differs_no_conflict\nKIND: scope\nCONFIDENCE: 0.6\nREASON: other \"x\"."
    spec = {"answer": differs, "answers": {u: consistent for u in neg}, "sleep_s": sleep_s,
            "calls_log": str(tmp / "calls.log"), "model_id": "scripted-model"}
    p = tmp / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


def _cmd(tmp: Path, defs: Path) -> list:
    return [sys.executable, str(SCRIPT), "--run", "--workers", "1", "--run-id", "t-defpairs",
            "--defs-json", str(defs), "--checkpoint", str(tmp / "ck.jsonl"),
            "--raw-dir", str(tmp / "raw")]


def _decided(path: Path) -> dict:
    return {k: (v["outcome"], v["kind"], v["reason"], v["status"])
            for k, v in R.latest_by_unit(R.read_checkpoint(path)).items()}


def test_sigkill_mid_loop_resumes_without_repeating_a_completed_call(q1, tmp_path):
    rows, _ = q1
    defs = {r["node_key"]: {"key": r["node_key"], "term": r["term"], "span": r["quote"],
                            "doc_id": r["doc_id"], "locator": r["locator"]} for r in rows}
    dp = tmp_path / "defs.json"
    dp.write_text(json.dumps(defs), encoding="utf-8")
    units = R.build_units(rows, defs, "scripted-model")

    ref = tmp_path / "ref"
    ref.mkdir()
    env_ref = {**os.environ, "DEFPAIRS_SCRIPTED_CONSUMER": str(_spec(ref, units, 0))}
    done = subprocess.run(_cmd(ref, dp), env=env_ref, capture_output=True, text=True, cwd=REPO)
    assert done.returncode == 0, done.stdout + done.stderr

    run = tmp_path / "killed"
    run.mkdir()
    env = {**os.environ, "DEFPAIRS_SCRIPTED_CONSUMER": str(_spec(run, units, 0.05))}
    proc = subprocess.Popen(_cmd(run, dp), env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, cwd=REPO)
    ck = run / "ck.jsonl"
    deadline = time.time() + 60
    while time.time() < deadline:
        if ck.is_file() and len(ck.read_text().splitlines()) >= 25:
            break
        time.sleep(0.02)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    before = set(R.latest_by_unit(R.read_checkpoint(ck)))
    assert 0 < len(before) < len(units), "the kill did not land mid-loop"
    calls_before = len((run / "calls.log").read_text().splitlines())

    again = subprocess.run(_cmd(run, dp), env=env, capture_output=True, text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    after_calls = (run / "calls.log").read_text().splitlines()[calls_before:]
    repeated = {c.split(".")[1] for c in after_calls} & before
    assert not repeated, f"completed units called again: {sorted(repeated)}"
    assert _decided(ck) == _decided(ref / "ck.jsonl")
    assert len(_decided(ck)) == len(units)
