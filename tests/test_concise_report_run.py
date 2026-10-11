"""The concise report's run (`scripts/concise_report_run.py`, cc_tasks/2026-10-07_concise_report_prose.md):
the input stop condition, the join guard, the cut rule, the reader's grade, label parsing, and
checkpoint resume under SIGKILL (~/GitHub/CLAUDE.md §15 item 8) with a scripted consumer."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import concise_report_run as R  # noqa: E402
import dcat_faq_run as FR  # noqa: E402

CFG = R.load_config()


def test_inputs_cite_the_frozen_composite_and_every_section_claim_exists():
    claims = R.load_claims(CFG)
    assert R.frozen_composite(REPO / CFG["inputs"]["frozen"]) == "scan_2026-10-07_composite_d"
    for s in CFG["sections"]:
        assert all(i in claims for i in s["claims"]), s["id"]
    assert sorted(CFG["controls"]) == [s["id"] for s in CFG["sections"]]
    for sid, c in CFG["controls"].items():
        assert c["contradicts"] in next(s for s in CFG["sections"] if s["id"] == sid)["claims"]


def test_a_claims_file_on_another_composite_stops_before_any_call(tmp_path, monkeypatch):
    frozen = tmp_path / "FROZEN.md"
    frozen.write_text("| Composite | `scan_2099-01-01_other` |\n", encoding="utf-8")
    cfg = {**CFG, "inputs": {**CFG["inputs"], "frozen": str(frozen)}}
    with pytest.raises(SystemExit, match="FROZEN.md names"):
        R.load_claims(cfg)


def test_a_join_that_moves_a_marker_or_a_number_is_discarded():
    old = ["Of 1,055 findings, 341 are denials [c:CL-035].", "That is a finding about access."]
    assert R.guard_join(old, ["Turning to access, of 1,055 findings, 341 are denials [c:CL-035].",
                              "That is a finding about access."]) is None
    assert "markers" in R.guard_join(old, ["Of 1,055 findings, 341 are denials [c:CL-035, CL-036]."])
    assert "numbers" in R.guard_join(old, ["Of 1,055 findings, 340 are denials [c:CL-035]."])


def test_unsupported_and_digit_failures_are_cut_and_nothing_is_reworded():
    claims = R.load_claims(CFG)
    paras = [["Of the 1,055 findings, 341 are access denials [c:CL-035].",
              "Of the 1,055 findings, 400 are access denials [c:CL-035].",
              "The hosts were slow on purpose [c:CL-035].",
              "The next section turns to what was served."]]
    labels = [{"label": "supported", "claim_ids": ["CL-035"], "reason": ""},
              {"label": "supported", "claim_ids": ["CL-035"], "reason": ""},
              {"label": "unsupported", "claim_ids": [], "reason": "no claim says slow"},
              {"label": "no_factual_content", "claim_ids": [], "reason": ""}]
    a = R.apply_check(paras, labels, claims, ["CL-035"])
    assert a["kept"] == [[paras[0][0], paras[0][3]]]
    assert [r["kept"] for r in a["rows"]] == [True, False, False, True]
    assert a["rows"][1]["cut_reason"].startswith("digit check") and a["rows"][2]["cut_reason"].startswith("checker")


def test_labels_must_cover_every_sentence():
    with pytest.raises(ValueError, match="no label"):
        R.parse_labels(json.dumps([{"sentence_id": "S1", "label": "supported", "claim_ids": ["CL-1"]}]), 2)
    with pytest.raises(ValueError, match="label"):
        R.parse_labels(json.dumps([{"sentence_id": "S1", "label": "maybe"}]), 1)


def test_the_reader_is_graded_by_the_rules_fixed_before_it_ran():
    claims = R.load_claims(CFG)
    cited = {"CL-050", "CL-035", "CL-116"}
    right = {"q1": "The scanner checked whether 16 statistical bodies serve a machine client.",
             "q2": "Most checks did not pass: hosts refused the client or did not serve the item.",
             "q3": "Publish a machine-readable licence; the Census Bureau failed that check."}
    g = R.grade(right, CFG, claims, cited)
    assert all(v["right"] for v in g.values()), g
    wrong = {**right, "q1": "It measured 40 websites.", "q3": "Hire more staff."}
    g = R.grade(wrong, CFG, claims, cited)
    assert not g["q1"]["right"] and g["q1"]["numbers_not_in_claims"] == ["40"] and not g["q3"]["right"]


def _cmd(tmp: Path) -> list:
    return [sys.executable, str(REPO / "scripts" / "concise_report_run.py"), "--run",
            "--run-dir", str(tmp / "run"), "--progress-log", str(tmp / "progress.log")]


def _spec(tmp: Path, sleep: float) -> dict:
    spec = tmp / "spec.json"
    spec.write_text(json.dumps({"calls_log": str(tmp / "calls.log"), "sleep_s": sleep,
                                "plants": [c["sentence"] for c in CFG["controls"].values()]}), encoding="utf-8")
    return {**os.environ, "CONCISE_SCRIPTED_CONSUMER": str(spec)}


def _final(tmp: Path) -> dict:
    p = json.loads((tmp / "run" / "pipeline.json").read_text(encoding="utf-8"))
    return {"final": p["final"]["sections"], "control": p["control"]["passed"],
            "reader": {k: v["answers"] for k, v in p["reader"].items()}}


def test_sigkill_mid_loop_resumes_without_repeating_a_completed_call(tmp_path):
    ref = tmp_path / "ref"
    ref.mkdir()
    done = subprocess.run(_cmd(ref), env=_spec(ref, 0), capture_output=True, text=True, cwd=REPO)
    assert done.returncode == 0, done.stdout + done.stderr

    run = tmp_path / "killed"
    run.mkdir()
    env = _spec(run, 0.3)
    proc = subprocess.Popen(_cmd(run), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=REPO)
    ck = run / "run" / "checkpoint.jsonl"
    deadline = time.time() + 60
    while time.time() < deadline:
        if ck.is_file() and len(ck.read_text().splitlines()) >= 8:
            break
        time.sleep(0.02)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    before = {r["unit_id"] for r in FR.Checkpoint(ck).read() if r["status"] == "done"}
    total = len({r["unit_id"] for r in FR.Checkpoint(ref / "run" / "checkpoint.jsonl").read()})
    assert 0 < len(before) < total, "the kill did not land mid-loop"
    calls_before = len((run / "calls.log").read_text().splitlines())

    again = subprocess.run(_cmd(run), env=env, capture_output=True, text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    after = (run / "calls.log").read_text().splitlines()[calls_before:]
    repeated = {c.split(".")[1] for c in after} & before
    assert not repeated, f"completed units called again: {sorted(repeated)}"
    assert _final(run) == _final(ref)
    assert _final(ref)["control"] is True
