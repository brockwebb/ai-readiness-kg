"""The shipped concise report (`reports/concise/`, cc_tasks/2026-10-07_concise_report_prose.md
decision 7) agrees with the run that produced it: the PDF was rendered from this Markdown
(checked by hash, since git keeps no file times), no kept sentence is unsupported or fails the
digit check, the control caught every plant, the gate and reader files are the run's, and the
Markdown passes the lint."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import concise_report_build as B  # noqa: E402
import concise_report_gate as G  # noqa: E402
import concise_report_run as R  # noqa: E402
import dcat_faq_lint  # noqa: E402

OUT = REPO / "reports" / "concise"
PIPE = json.loads((OUT / "run" / "pipeline.json").read_text(encoding="utf-8"))
CFG = R.load_config()
R.load_claims(CFG)          # the live file still cites the composite FROZEN.md names


def frozen_claims() -> dict:
    """The claims the report was written from: `docs/evidence/claims.yaml` AT the commit
    `docs/evidence/FROZEN.md` names. FROZEN.md says the report "still cites the composite above,
    at the commit above", and the evidence map is a view that later tasks rebuild
    (`cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards.md`
    decision 4: "the report is not rebuilt here"). Read from the live file, this guard went red
    the first time the corpus grew under a frozen report (CL-044, 282 -> 287 admitted)."""
    text = (REPO / "docs" / "evidence" / "FROZEN.md").read_text(encoding="utf-8")
    m = re.search(r"\| Commit \| `([0-9a-f]{40})`", text)
    assert m, "FROZEN.md names no commit"
    doc = yaml.safe_load(subprocess.run(
        ["git", "show", f"{m.group(1)}:docs/evidence/claims.yaml"], cwd=REPO, check=True,
        capture_output=True, text=True).stdout)
    return {c["id"]: c for c in doc["claims"]}


CLAIMS = frozen_claims()


def test_the_pdf_is_rendered_from_this_markdown():
    rep = json.loads((OUT / "build_report.json").read_text(encoding="utf-8"))["render"]
    md = (OUT / "REPORT.md").read_bytes()
    assert rep["md_sha256"] == hashlib.sha256(md).hexdigest()
    assert rep["pdf_sha256"] == hashlib.sha256((OUT / "REPORT.pdf").read_bytes()).hexdigest()
    assert rep["pages"] >= 3


def test_the_markdown_is_the_build_of_the_run_and_passes_the_lint():
    md = (OUT / "REPORT.md").read_text(encoding="utf-8")
    assert md == B.report_markdown(CFG, PIPE["final"]["sections"], CLAIMS, B.written_note(PIPE))
    assert dcat_faq_lint.lint(md) == [] and G.dash_findings(md) == []
    assert "[c:" not in md


def test_every_kept_sentence_is_checked_and_holds_only_numbers_its_claims_hold():
    assert PIPE["control"]["passed"] and all(c["caught"] for c in PIPE["control"]["rows"])
    final_sentences = [s for sec in PIPE["final"]["sections"].values() for p in sec for s in p]
    rows = {r["sentence"]: r for sec in PIPE["final"]["rows"].values() for r in sec["rows"]}
    for s in final_sentences:
        r = rows[s]
        assert r["kept"] and r["label"] in ("supported", "no_factual_content"), s
        assert G.digit_check(s, CLAIMS)["ok"], s


def test_the_trace_gate_and_reader_files_are_the_runs():
    trace = json.loads((OUT / "claims_trace.json").read_text(encoding="utf-8"))
    assert trace["final"] == PIPE["final"]["rows"]
    gate = json.loads((OUT / "prose_gate.json").read_text(encoding="utf-8"))
    assert gate["rounds"]["round1"] == PIPE["round1"]["gate"] and gate["final"] == PIPE["final"]["gate"]
    reader = json.loads((OUT / "fresh_reader.json").read_text(encoding="utf-8"))
    assert sorted(reader["rounds"]) == ["1", "2"] and reader["rounds"] == PIPE["reader"]
