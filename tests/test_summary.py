"""The executive summary: its build (text check, page count, md/pdf pairing) and its
verification (interleave, the checks, the §15 SIGKILL resume).

cc_tasks/2026-10-12_executive_summary_from_brief_v2.md.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import dcat_faq_run as FR  # noqa: E402
import summary_build as SB  # noqa: E402
import summary_text_check as TC  # noqa: E402
import summary_verify as SV  # noqa: E402

SRC = REPO / "reports" / "summary" / "summary_source.yaml"


# --------------------------------------------------------------------------------- text check

def test_text_check_passes_on_the_built_summary():
    src = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    manifest = json.loads((REPO / src["inputs"]["manifest"]).read_text(encoding="utf-8"))
    md = SB.full_markdown(src, manifest)
    assert TC.check(md) == [], "the shipped summary must pass its own text check"


@pytest.mark.parametrize("bad,rule", [
    ("The measurement cycle ran on Tuesday.", "process_word"),
    ("The verdict was a fail.", "process_word"),
    ("This runs through the pipeline.", "process_word"),
    ("The check A13 found a gap.", "indicator_code"),
    ("This is an AI readiness summary.", "ai_outside_title"),
    ("Artificial Intelligence is the point.", "ai_outside_title"),
    ("A dash — here.", "dash"),
])
def test_text_check_catches_each_forbidden_thing(bad, rule):
    md = f"# Title\n\nPrepared today.\n\n{bad}\n"
    rules = {f["rule"] for f in TC.check(md)}
    assert rule in rules, f"{bad!r} should trip {rule}; got {rules}"


def test_text_check_skips_the_sources_section():
    # A published title with AI, a code and a dash is lawful inside the Sources section.
    md = ("# Title\n\nPrepared today.\n\nClean body.\n\n## Sources\n\n"
          "1. NAO 216-128: Artificial Intelligence in NOAA — the title. <https://x>\n")
    assert TC.check(md) == []


# ----------------------------------------------------------------------------- the interleave

def test_controls_are_spread_not_bunched():
    reals = [f"real {i}" for i in range(8)]
    controls = [{"text": "c1"}, {"text": "c2"}, {"text": "c3"}]
    combined, positions = SV.interleaved(reals, controls)
    assert len(combined) == 11
    assert [combined[p] for p in positions] == ["c1", "c2", "c3"]
    # no two controls adjacent, none first
    assert positions[0] > 0
    assert all(positions[i + 1] - positions[i] >= 2 for i in range(len(positions) - 1))


def test_factual_sentences_all_carry_markers():
    src = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    import concise_report_gate as G
    for s in SV.factual_sentences(src):
        assert G.marker_ids(s), f"a factual sentence with no claim marker: {s!r}"


# ------------------------------------------------------------------- build render (needs pandoc)

@pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not available")
def test_body_is_exactly_two_pages_and_pdf_matches_markdown(tmp_path):
    out = tmp_path / "summary"
    out.mkdir()
    rc = subprocess.run([sys.executable, str(REPO / "scripts" / "summary_build.py"),
                         "--out-dir", str(out), "--source", str(SRC)],
                        capture_output=True, text=True, cwd=REPO)
    assert rc.returncode == 0, rc.stdout + rc.stderr
    report = json.loads((out / "build_report.json").read_text(encoding="utf-8"))
    assert report["body_pages"] == 2, f"the body must be exactly 2 pages, got {report['body_pages']}"
    import hashlib
    md = (out / "SUMMARY.md").read_bytes()
    assert hashlib.sha256(md).hexdigest() == report["render"]["md_sha256"]


# --------------------------------------------------------------------- §15 item 8: SIGKILL resume

def _spec(run: Path, sleep: float) -> Path:
    p = run / "spec.json"
    p.write_text(json.dumps({
        "calls_log": str(run / "calls.log"), "sleep_s": sleep,
        "control_prefixes": ["Every one of the 1,055", "A machine reaches all 29",
                             "The Census Bureau passes every one"]}), encoding="utf-8")
    return p


def _cmd(run: Path) -> list:
    return [sys.executable, str(REPO / "scripts" / "summary_verify.py"), "--check",
            "--run-dir", str(run / "run"), "--source", str(SRC),
            "--progress-log", str(run / "progress.log")]


def _check(run: Path) -> dict:
    v = json.loads((run / "run" / SV.VERIFY).read_text(encoding="utf-8"))["check"]
    return {"caught": v["controls_caught"], "passed": v["unsupported_check_passed"],
            "controls": [(c["label"], c["caught"]) for c in v["controls"]],
            "reals": [(r["label"], r["supported"]) for r in v["reals"]]}


def test_scripted_check_catches_controls_and_passes_reals(tmp_path):
    env = {**os.environ, "SUMMARY_SCRIPTED_CONSUMER": str(_spec(tmp_path, 0))}
    r = subprocess.run(_cmd(tmp_path), env=env, capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    res = _check(tmp_path)
    assert res["caught"] and res["passed"]
    assert all(c == ("unsupported", True) for c in res["controls"])
    assert all(rr == ("supported", True) for rr in res["reals"])


def test_completed_call_is_not_repeated_on_rerun(tmp_path):
    env = {**os.environ, "SUMMARY_SCRIPTED_CONSUMER": str(_spec(tmp_path, 0))}
    subprocess.run(_cmd(tmp_path), env=env, capture_output=True, text=True, cwd=REPO, check=True)
    n1 = len((tmp_path / "calls.log").read_text().splitlines())
    subprocess.run(_cmd(tmp_path), env=env, capture_output=True, text=True, cwd=REPO, check=True)
    n2 = len((tmp_path / "calls.log").read_text().splitlines())
    assert n1 == n2 == 1, "a completed check call must not be made again on resume"


def test_sigkill_mid_call_resumes_and_matches_uninterrupted(tmp_path):
    ref = tmp_path / "ref"
    ref.mkdir()
    env_ref = {**os.environ, "SUMMARY_SCRIPTED_CONSUMER": str(_spec(ref, 0))}
    subprocess.run(_cmd(ref), env=env_ref, capture_output=True, text=True, cwd=REPO, check=True)

    run = tmp_path / "killed"
    run.mkdir()
    env = {**os.environ, "SUMMARY_SCRIPTED_CONSUMER": str(_spec(run, 1.0)),
           "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}
    proc = subprocess.Popen(_cmd(run), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=REPO)
    calls = run / "calls.log"
    deadline = time.time() + 30
    while time.time() < deadline and not (calls.is_file() and calls.read_text().splitlines()):
        time.sleep(0.02)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    ck = run / "run" / "checkpoint.jsonl"
    done_before = [r for r in FR.Checkpoint(ck).read() if r["status"] == "done"] if ck.is_file() else []
    assert not done_before, "the kill should land before the call was checkpointed"

    again = subprocess.run(_cmd(run), env=env, capture_output=True, text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    assert _check(run) == _check(ref)
    done = [r for r in FR.Checkpoint(ck).read() if r["status"] == "done"]
    assert len({r["unit_id"] for r in done}) == len(done) == 1
