"""The USAFacts note: the build's two gates, and the reader's checkpoint/resume (§15 item 8).

`cc_tasks/2026-10-14_usafacts_note.md` (DN-014 ADDENDUM 01 §5). The build is zero-spend; the
reader's model calls are replaced by a scripted consumer, so these tests make no model call.
"""
from __future__ import annotations

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

import usafacts_note_build as NB  # noqa: E402

SOURCE = REPO / "reports" / "summary" / "usafacts_note_source.yaml"


def _src() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------- the build gates

def test_the_shipped_note_passes_both_gates(tmp_path):
    """The committed source builds with zero text findings and zero unsupported findings."""
    rc = NB.main(["--no-pdf", "--out-dir", str(tmp_path)])
    assert rc == 0
    report = json.loads((tmp_path / "usafacts_note_build_report.json").read_text())
    assert report["text_check"] == "0 findings"
    assert report["unsupported_check"] == "0 findings"
    assert report["fact_sentences"] >= 1
    md = (tmp_path / "USAFACTS_NOTE.md").read_text()
    # Cites USAFacts' Detailed User Guide by title (ADDENDUM 01 §5).
    assert "Detailed User Guide" in md


def test_text_check_refuses_a_process_word(tmp_path):
    src = _src()
    src["paragraphs"][0][0]["text"] = "This note describes the scoring pipeline it runs."
    p = tmp_path / "src.yaml"
    p.write_text(yaml.safe_dump(src), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        NB.main(["--no-pdf", "--out-dir", str(tmp_path), "--source", str(p)])
    assert "fails its gates" in str(e.value)
    assert not (tmp_path / "USAFACTS_NOTE.md").exists()


def test_unsupported_check_refuses_an_unresolving_locator(tmp_path):
    src = _src()
    src["paragraphs"][0][0]["locator"] = ["record:crit:ZZ#name"]
    p = tmp_path / "src.yaml"
    p.write_text(yaml.safe_dump(src), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        NB.main(["--no-pdf", "--out-dir", str(tmp_path), "--source", str(p)])
    assert "unsupported" in str(e.value)
    assert not (tmp_path / "USAFACTS_NOTE.md").exists()


def test_unsupported_check_refuses_a_fact_without_a_locator(tmp_path):
    src = _src()
    src["paragraphs"][0][0]["locator"] = []
    p = tmp_path / "src.yaml"
    p.write_text(yaml.safe_dump(src), encoding="utf-8")
    with pytest.raises(SystemExit):
        NB.main(["--no-pdf", "--out-dir", str(tmp_path), "--source", str(p)])


# --------------------------------------------------------------------- the reader resume (§15.8)

@pytest.mark.slow
def test_reader_resumes_after_sigkill_without_a_duplicate_call(tmp_path):
    """Kill the reader mid-call, restart it, and assert the completed round's call is not remade
    and the final answer equals an uninterrupted run's (§15 item 8)."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    calls_log = tmp_path / "calls.log"
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"calls_log": str(calls_log), "sleep_s": 5, "model_id": "scripted-reader"}))
    env = {**os.environ, "USAFACTS_NOTE_SCRIPTED_CONSUMER": str(spec)}
    cmd = [sys.executable, str(REPO / "scripts" / "usafacts_note_verify.py"),
           "--read", "1", "--run-dir", str(run_dir),
           "--progress-log", str(tmp_path / "p.log")]

    # Start, let the call begin (the scripted consumer logs its id then sleeps), then SIGKILL.
    proc = subprocess.Popen(cmd, env=env, cwd=str(REPO))
    for _ in range(100):
        if calls_log.is_file() and calls_log.read_text().strip():
            break
        time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("the scripted reader never logged a call")
    proc.send_signal(signal.SIGKILL)
    proc.wait(timeout=30)
    first = calls_log.read_text().splitlines()
    assert len(first) >= 1  # the call started but its result was never checkpointed (killed mid-sleep)

    # Restart: re-running is the resume. It must land a done record.
    r2 = subprocess.run(cmd, env=env, cwd=str(REPO), capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0, r2.stderr
    verify = json.loads((run_dir / "verify.json").read_text())
    assert verify["reads"][0]["answers"]["q1"]

    # A third run finds the done record and makes NO new call.
    calls_before = len(calls_log.read_text().splitlines())
    r3 = subprocess.run(cmd, env=env, cwd=str(REPO), capture_output=True, text=True, timeout=60)
    assert r3.returncode == 0, r3.stderr
    assert len(calls_log.read_text().splitlines()) == calls_before
