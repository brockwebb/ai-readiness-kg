"""The instrument specification (DN-015; task db464d5f): the entries, their checker, page two's
verdict, the reader's checkpoint, and the record write-back."""
from __future__ import annotations

import copy
import hashlib
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

import instrument as INS  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return INS.load_config()


@pytest.fixture(scope="module")
def entries():
    return INS.load_entries()


@pytest.fixture(scope="module")
def findings(cfg):
    return INS.cycle_findings(INS.load_grid(cfg)["cycle"])


def _problems(cfg, entries, findings):
    return INS.check(cfg, entries, findings, unverifiable=[])


# ------------------------------------------------------------------------------- the entries

def test_every_entry_passes_the_check(cfg, entries, findings):
    assert _problems(cfg, entries, findings) == []


def test_one_entry_per_audited_rule(entries):
    """The 13 v3 grid columns, the two site-level checks off the grid (A11-declared, A12) and the
    discoverability candidate the task names (A13): 16 rules, one entry each."""
    legs = {e["leg"] for e in entries}
    grid = json.loads((REPO / "reports" / "summary" / "grid.json").read_text())
    assert {c["leg"] for c in grid["columns"]} <= legs
    assert {"A11-declared", "A12", "A13"} <= legs
    assert len(entries) == len(legs) == 16


@pytest.mark.parametrize("path", ["question", "claims", "test", "expected_behavior"])
def test_check_lists_a_missing_field(cfg, entries, findings, path):
    bad = copy.deepcopy(entries)
    del bad[0][path]
    probs = _problems(cfg, bad, findings)
    assert any(f"missing field `{path}`" in p for p in probs)


def test_check_refuses_prose_as_a_source(cfg, entries, findings):
    bad = copy.deepcopy(entries)
    bad[0]["expected_behavior"]["sources"] = ["W3C says so"]
    assert any("prose is not a source" in p for p in _problems(cfg, bad, findings))


def test_check_refuses_an_unadmitted_doc_and_an_unreceipted_url(cfg, entries, findings):
    bad = copy.deepcopy(entries)
    bad[0]["expected_behavior"]["sources"] = [{"doc_id": "not-a-corpus-doc", "section": "§1"},
                                               {"url": "https://example.org/x", "section": "§1"}]
    probs = _problems(cfg, bad, findings)
    assert any("not an admitted corpus document" in p for p in probs)
    assert any("has no 200 receipt" in p for p in probs)


def test_state_must_be_the_weakest_branch(cfg, entries, findings):
    bad = copy.deepcopy(entries)
    e = next(x for x in bad if x["state"] == "project_defined")
    e["state"] = "specified"
    assert any("weakest branch" in p for p in _problems(cfg, bad, findings))


def test_every_decided_finding_rests_on_exactly_one_branch(cfg, entries, findings):
    bad = copy.deepcopy(entries)
    e = next(x for x in bad if x["leg"] == "A2")
    e["branches"] = [b for b in e["branches"] if b["verdict"] != "fail"]
    assert any("matches 0 branches" in p for p in _problems(cfg, bad, findings))


def test_a_planted_quote_is_caught(cfg, entries):
    e = copy.deepcopy(next(x for x in entries if x["leg"] == "A4"))
    if INS.source_text(cfg, "rfc-9309-robots-exclusion-protocol") is None:
        pytest.skip("corpus body not on this machine (corpus binaries are gitignored)")
    e["expected_behavior"]["quotes"] = [{"source": "rfc-9309-robots-exclusion-protocol",
                                         "quote": "crawlers MUST NOT access any resources when robots.txt is missing"}]
    probs, unv = [], []
    INS.check_quotes(cfg, e, probs, unv)
    assert probs and not unv


def test_the_api_entry_settles_the_four_points(entries):
    e = next(x for x in entries if x["leg"] == "A2")
    s = e["settles"]
    assert set(s) == {"search_engine_location_is_not_the_behavior", "dataset_search_depends_on_markup",
                      "robots_is_declared_policy_firewall_is_enforcement", "data_page_not_api_endpoint"}
    assert "google-dataset-structured-data" in s["dataset_search_depends_on_markup"]
    assert "not a claim that the agency has no API" in e["claims"]["fail"]


# ---------------------------------------------------------------------- page two (DN-015 §6)

@pytest.mark.parametrize("pages,want", [
    (["pass"], "pass"), (["fail"], "fail"), (["error"], "could_not_measure"),
    (["pass", "pass"], "pass"), (["fail", "fail"], "fail"), (["pass", "fail"], "partial"),
    (["pass", "error"], "could_not_measure"), (["fail", "error"], "could_not_measure"),
    (["pass", "fail", "error"], "partial"), (["error", "error"], "could_not_measure"),
])
def test_four_state_rule(pages, want):
    assert INS.four_state(pages) == want


def test_verdict_counts_recomputed_by_hand(cfg, entries, findings):
    grid = INS.load_grid(cfg)
    v = INS.page_two(cfg, entries, grid, findings)
    cnm = changed = 0
    for row in grid["rows"]:
        for cell in row["cells"].values():
            verdicts = [p["verdict"] for p in cell["pages"]]
            if "error" in verdicts and not ({"pass", "fail"} <= set(verdicts)):
                cnm += 1
            new = INS.four_state(verdicts)
            changed += new != cell["state"]
    assert v["could_not_measure"] == cnm
    assert v["cells_changing_state"] == changed
    assert v["cells"] == sum(len(r["cells"]) for r in grid["rows"])
    assert sum(v["could_not_measure_by_agency"].values()) == cnm


def test_only_specified_non_declarations_stay_on_page_two(cfg, entries, findings):
    v = INS.page_two(cfg, entries, INS.load_grid(cfg), findings)
    by_leg = {e["leg"]: e for e in entries}
    for leg in v["kept_on_page_two"]:
        assert by_leg[leg]["state"] == "specified" and not by_leg[leg].get("declaration")
    for leg in v["removed_from_page_two"]:
        assert by_leg[leg]["state"] != "specified" or by_leg[leg].get("declaration")


def test_built_reports_match_their_markdown_by_hash():
    rep = json.loads((REPO / "reports" / "instrument" / "build_report.json").read_text())
    for r in rep["reports"]:
        md = (REPO / "reports" / "instrument" / r["markdown"]).read_text(encoding="utf-8")
        assert hashlib.sha256(md.encode("utf-8")).hexdigest() == r["md_sha256"], r["markdown"]
        assert r.get("pdf") and (REPO / "reports" / "instrument" / r["pdf"]).is_file()


# --------------------------------------------------------------------------- the write-back

def test_record_carries_each_entry_state_and_name(entries):
    g = json.loads((REPO / "framework" / "ai_readiness_framework.json").read_text())
    nodes = {n["id"]: n["properties"] for n in g["nodes"]}
    for e in entries:
        assert nodes[f"spec:{e['leg']}"].get("instrument_state") == e["state"], e["leg"]
        if e.get("plain_name"):
            assert nodes[e["indicator"]].get("plain_name") == e["plain_name"], e["leg"]
        flc = e["fix_line_check"]
        if flc["verdict"] == "rewritten":
            assert nodes[flc["action"]].get("fix_line") == flc["new_fix_line"]


def test_grid_vocabulary_agrees_with_the_entries(entries):
    import yaml
    import apply_instrument_state as A
    vocab = yaml.safe_load((REPO / "framework" / "summary_grid_vocab.yaml").read_text())
    assert A.vocab_drift(A.wanted(entries), vocab) == []


# ------------------------------------------------------------------ the reader resume (§15.8)

def _reader_cmd(run_dir: Path, plog: Path) -> list:
    return [sys.executable, str(REPO / "scripts" / "instrument_read.py"), "--round", "1",
            "--only", "RULE-A1-v5", "RULE-A3-v8", "RULE-A5-v2",
            "--run-dir", str(run_dir), "--progress-log", str(plog)]


@pytest.mark.slow
def test_reader_resumes_after_sigkill_without_a_duplicate_call(tmp_path):
    """SIGKILL the reader after its first unit is checkpointed and while the second is in flight;
    restart; assert no completed unit's call is made twice and the final reads equal an
    uninterrupted run's (§15 item 8)."""
    calls = tmp_path / "calls.log"
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"calls_log": str(calls), "sleep_s": 2, "model_id": "scripted-reader"}))
    env = {**os.environ, "INSTRUMENT_READ_SCRIPTED_CONSUMER": str(spec)}
    run = tmp_path / "run"
    proc = subprocess.Popen(_reader_cmd(run, tmp_path / "p.log"), env=env, cwd=str(REPO))
    ck = run / "checkpoint.jsonl"
    for _ in range(300):
        if ck.is_file() and ck.read_text().strip() and len(calls.read_text().splitlines()) >= 2:
            break
        time.sleep(0.05)
    else:
        proc.kill()
        pytest.fail("the scripted reader never reached its second unit")
    proc.send_signal(signal.SIGKILL)
    proc.wait(timeout=30)
    done_before = {json.loads(l)["unit_id"] for l in ck.read_text().splitlines() if '"done"' in l}
    assert len(done_before) == 1

    r2 = subprocess.run(_reader_cmd(run, tmp_path / "p.log"), env=env, cwd=str(REPO),
                        capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0, r2.stderr
    ids = [c.split(".")[1] for c in calls.read_text().splitlines()]
    for uid in done_before:
        assert ids.count(uid) == 1, "a completed unit was called again"

    clean = tmp_path / "clean"
    calls2 = tmp_path / "calls2.log"
    spec2 = tmp_path / "spec2.json"
    spec2.write_text(json.dumps({"calls_log": str(calls2), "sleep_s": 0, "model_id": "scripted-reader"}))
    r3 = subprocess.run(_reader_cmd(clean, tmp_path / "p2.log"),
                        env={**os.environ, "INSTRUMENT_READ_SCRIPTED_CONSUMER": str(spec2)},
                        cwd=str(REPO), capture_output=True, text=True, timeout=120)
    assert r3.returncode == 0, r3.stderr

    def answers(d):
        v = json.loads((d / "verify.json").read_text())
        return sorted((r["rule_id"], r["unit_id"], json.dumps(r["answers"], sort_keys=True)) for r in v["reads"])
    assert answers(run) == answers(clean)
