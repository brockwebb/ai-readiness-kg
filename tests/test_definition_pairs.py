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
        # written to the cross-document shard (and projected), or quarantined at the
        # grounding gate with its reason: exactly one disposition
        written = bool(r["edge_event_id"])
        quarantined = r["quarantined"] == "true" and bool(r["quarantine_reason"])
        assert written != quarantined, r["pair_id"]


def test_the_edge_shard_is_one_the_projection_reads():
    """The completion task's decision 2: the shard `--emit-edges` writes is a tag
    `build_projection.py` replays, so a written edge is a projected edge."""
    import build_projection as bp
    assert R.HELD_TAG in bp.CROSS_DOCUMENT_EDGE_TAGS


def test_every_method_citation_is_retrieved_and_cited():
    """Decision 4: every key `definition_pairs.md` cites is an entry of `method_sources.bib`
    with a url, a retrieval date and an establishing quotation under 15 words."""
    import re
    bib = (REPO / "docs" / "evidence" / "method_sources.bib").read_text(encoding="utf-8")
    entries = dict(re.findall(r"@\w+\{([^,\s]+),(.*?)\n\}", bib, re.S))
    md = R.OUT_MD.read_text(encoding="utf-8")
    for key in ("podsakoff2016concept", "mackenzie2011construct", "walker2011strategies",
                "euzenat2013ontology"):
        assert f"`{key}`" in md, key
    for key, body in entries.items():
        for field in ("author", "title", "year", "url", "urldate", "note"):
            assert re.search(rf"^\s*{field}\s*=\s*\{{.+\}},?\s*$", body, re.M), (key, field)
        assert re.search(r"url\s*=\s*\{https://", body), key
        quotes = re.findall(r'"([^"]+)"', re.search(r"note\s*=\s*\{(.*)\}", body).group(1))
        assert quotes and len(quotes[0].split()) < 15, key
    assert "recalled, not retrieved" not in md


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


# ----------------------------------------------------------------------------- control re-check
# Task `cc_tasks/2026-10-04_definition_pairs_completion.md` decision 1: a resumed run under a
# new run id judges the controls again and is gated on that re-check, not on the old one.

def _defs_file(rows: list, tmp: Path) -> Path:
    defs = {r["node_key"]: {"key": r["node_key"], "term": r["term"], "span": r["quote"],
                            "doc_id": r["doc_id"], "locator": r["locator"]} for r in rows}
    dp = tmp / "defs.json"
    dp.write_text(json.dumps(defs), encoding="utf-8")
    return dp


def _recheck_cmd(tmp: Path, defs: Path, run_id: str) -> list:
    return [sys.executable, str(SCRIPT), "--run", "--workers", "1", "--run-id", run_id,
            "--recheck-controls", "--defs-json", str(defs), "--checkpoint", str(tmp / "ck.jsonl"),
            "--raw-dir", str(tmp / "raw")]


def test_recheck_judges_every_control_again_and_nothing_else(q1, tmp_path):
    rows, _ = q1
    dp = _defs_file(rows, tmp_path)
    units = R.build_units(rows, json.loads(dp.read_text()), "scripted-model")
    env = {**os.environ, "DEFPAIRS_SCRIPTED_CONSUMER": str(_spec(tmp_path, units, 0))}
    first = subprocess.run(_cmd(tmp_path, dp), env=env, capture_output=True, text=True, cwd=REPO)
    assert first.returncode == 0, first.stdout + first.stderr
    ck = tmp_path / "ck.jsonl"
    decided_before = _decided(ck)
    n_calls = len((tmp_path / "calls.log").read_text().splitlines())

    again = subprocess.run(_recheck_cmd(tmp_path, dp, "t-recheck"), env=env, capture_output=True,
                           text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    new_calls = (tmp_path / "calls.log").read_text().splitlines()[n_calls:]
    ctrl = {u["unit_id"] for u in units if u["unit_kind"] != "pair"}
    assert sorted(c.split(".")[1] for c in new_calls) == sorted(ctrl)
    rech = [r for r in R.read_checkpoint(ck) if r.get("recheck")]
    assert len(rech) == len(ctrl) and all(r["run_id"] == "t-recheck" and r["attempt"] == 2
                                          for r in rech)
    assert _decided(ck) == decided_before, "a re-check must not replace the reported judgment"
    for r in rech:
        assert (tmp_path / "raw" / f"{r['unit_id']}.a1.json").is_file()
        assert (tmp_path / "raw" / f"{r['unit_id']}.a2.json").is_file()

    # resume of the same re-check is a no-op: no control is called a third time
    third = subprocess.run(_recheck_cmd(tmp_path, dp, "t-recheck"), env=env, capture_output=True,
                           text=True, cwd=REPO)
    assert third.returncode == 0, third.stdout + third.stderr
    assert len((tmp_path / "calls.log").read_text().splitlines()) == n_calls + len(ctrl)


def test_recheck_gate_failure_stops_before_any_pair(q1, tmp_path):
    """Positive control for the gate: the first run passes; the re-check answers every unit
    `differs_no_conflict`, so the negative controls fail and no pair may be judged."""
    rows, _ = q1
    dp = _defs_file(rows, tmp_path)
    units = R.build_units(rows, json.loads(dp.read_text()), "scripted-model")
    pairs = [u for u in units if u["unit_kind"] == "pair"]
    ok_env = {**os.environ, "DEFPAIRS_SCRIPTED_CONSUMER": str(_spec(tmp_path, units, 0))}
    # a full first run, with the last pair's row removed so one pair is left to judge; then a
    # re-check under a judge that gets the negative controls wrong
    first = subprocess.run(_cmd(tmp_path, dp), env=ok_env, capture_output=True, text=True, cwd=REPO)
    assert first.returncode == 0, first.stdout + first.stderr
    ck = tmp_path / "ck.jsonl"
    keep = [l for l in ck.read_text().splitlines() if json.loads(l)["unit_id"] != pairs[-1]["unit_id"]]
    ck.write_text("\n".join(keep) + "\n")
    bad = json.loads((tmp_path / "spec.json").read_text())
    bad["answers"] = {}
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    n_calls = len((tmp_path / "calls.log").read_text().splitlines())
    env = {**os.environ, "DEFPAIRS_SCRIPTED_CONSUMER": str(tmp_path / "bad.json")}
    out = subprocess.run(_recheck_cmd(tmp_path, dp, "t-recheck-bad"), env=env, capture_output=True,
                         text=True, cwd=REPO)
    assert out.returncode == 4, out.stdout + out.stderr
    called = {c.split(".")[1] for c in (tmp_path / "calls.log").read_text().splitlines()[n_calls:]}
    assert pairs[-1]["unit_id"] not in called, "a pair was judged after the re-check failed"
