"""The DCAT-US 3.0 FAQ (`cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md`).

Stdlib + pyyaml. No Neo4j, no network, no model: the element-table tests read the converted
schema texts (skipping, with the rebuild command, when they are absent), the keep/cut tests run
the decision code on hand-made answers, and the resume test drives the runner with its scripted
consumer.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import dcat_faq_evidence as EV  # noqa: E402
import dcat_faq_run as R  # noqa: E402

SUBSTRATE = REPO / "state" / "substrate_md"
REBUILD = "/opt/anaconda3/bin/python3 -m kg.ingest.gate --doc <doc_id> --no-task"
OUT = REPO / "reports" / "dcat_us_3_faq"


def _need(*docs):
    for d in docs:
        if not (SUBSTRATE / f"{d}.md").is_file():
            pytest.skip(f"no substrate for {d} (gitignored); rebuild: {REBUILD}")


# ----------------------------------------------------------------------- the element table

def test_final_dataset_page_has_exactly_the_four_mandatory_elements():
    _need(EV.FINAL)
    lv = EV.final_levels(EV.FINAL, SUBSTRATE)
    assert sorted(k for k, v in lv.items() if v["level"] == "Mandatory") == \
        ["contactPoint", "description", "identifier", "title"]
    assert lv["publisher"]["level"] == "Recommended"
    assert lv["hasQualityMeasurement"]["level"] == "Optional"


def test_the_earlier_capture_has_publisher_mandatory():
    """The rewrite between the two captures is a recorded difference, not a parse artifact."""
    _need(EV.EARLIER)
    assert EV.final_levels(EV.EARLIER, SUBSTRATE)["publisher"]["level"] == "Mandatory"


def test_every_draft_dataset_property_is_read_and_none_is_guessed():
    _need(EV.DRAFT)
    lines = (SUBSTRATE / f"{EV.DRAFT}.md").read_text(encoding="utf-8").splitlines()
    a, b = lines.index("## Dataset"), lines.index("## Dataset Series")
    n = sum(1 for l in lines[a:b] if l.startswith("#### Property:"))
    d = EV.draft_levels(EV.DRAFT, SUBSTRATE)
    assert len(d) == n == 49
    assert d["contactPoint"]["level"] == "Recommended"
    assert d["geographicBoundingBox"]["level"] == "Recommended"
    assert d["hasVersion"]["level"] == "not stated"


def test_v11_required_fields_include_the_agency_codes():
    _need(EV.V11)
    v = EV.v11_levels(EV.V11, SUBSTRATE)
    assert v["bureauCode"]["status"].startswith("Yes, for United States Federal Government")
    assert v["dataQuality"]["status"] == "No"
    assert not any("→" in k for k in v)


def test_every_table_cell_quotes_the_line_it_was_read_from():
    _need(EV.FINAL, EV.EARLIER, EV.DRAFT, EV.V11)
    for r in EV.element_table(SUBSTRATE):
        for doc, src in r["sources"].items():
            line = (SUBSTRATE / f"{doc}.md").read_text(encoding="utf-8").splitlines()[src["line"] - 1]
            assert r["element"] in line or src["text"].split(" | ")[0].split(": ")[-1] in line, (r["element"], doc)


# ------------------------------------------------------------------------- evidence files

def test_shipped_evidence_files_hash_to_their_recorded_sha():
    files = sorted((OUT / "evidence").glob("Q*.json"))
    if not files:
        pytest.skip("no evidence files; run scripts/dcat_faq_evidence.py")
    for p in files:
        ev = json.loads(p.read_text(encoding="utf-8"))
        assert EV.evidence_sha(ev) == ev["evidence_sha256"], p.name
        assert all(it["id"] == f"E{i}" for i, it in enumerate(ev["items"], 1)), p.name


# ------------------------------------------------------------------------ keep or cut rules

EVD = {"question_id": 1, "question": "q", "documents": {},
       "items": [{"id": "E1", "doc_id": "d", "kind": "passage", "text": "Only title,  description\nand identifier are Mandatory."},
                 {"id": "E2", "doc_id": "d", "kind": "passage", "text": "Publisher is Recommended."}]}


def _decide(sentences, verdicts, not_known=()):
    ans = R.parse_answer(json.dumps({"sentences": sentences, "not_known": list(not_known)}), EVD, 3)
    items = R.check_items(ans)
    return R.decide(EVD, ans, items, verdicts)


def test_a_pass_whose_quote_is_in_a_cited_passage_is_kept_whitespace_normalised():
    d = _decide([{"text": "Three are Mandatory.", "evidence": ["E1"]}],
                [{"item_id": "S1", "verdict": "pass", "defect_class": None,
                  "support_span": "Only title, description and identifier are Mandatory."}])
    assert len(d["kept"]) == 1 and not d["cut"]


def test_a_pass_quoting_an_uncited_passage_is_cut():
    d = _decide([{"text": "Publisher is Recommended.", "evidence": ["E1"]}],
                [{"item_id": "S1", "verdict": "pass", "defect_class": None,
                  "support_span": "Publisher is Recommended."}])
    assert not d["kept"] and "not found in the cited passages" in d["cut"][0]["cut_reason"]


def test_flag_and_fail_are_cut_never_kept():
    d = _decide([{"text": "a", "evidence": ["E1"]}, {"text": "b", "evidence": ["E2"]}],
                [{"item_id": "S1", "verdict": "flag", "defect_class": "boundary_imprecision"},
                 {"item_id": "S2", "verdict": "fail", "defect_class": "surface_form_absent"}])
    assert not d["kept"] and len(d["cut"]) == 2


def test_a_sentence_citing_an_id_not_in_the_file_is_cut_before_the_check():
    ans = R.parse_answer(json.dumps({"sentences": [{"text": "x", "evidence": ["E9"]},
                                                   {"text": "y", "evidence": []}]}), EVD, 3)
    assert not ans["sentences"] and len(ans["precut"]) == 2
    assert not R.check_items(ans)


def test_sentences_beyond_the_limit_are_cut():
    ans = R.parse_answer(json.dumps({"sentences": [{"text": str(i), "evidence": ["E1"]} for i in range(5)]}), EVD, 3)
    assert len(ans["sentences"]) == 3 and len(ans["precut"]) == 2


def test_a_contradicted_not_known_is_cut_and_an_unchecked_one_too():
    d = _decide([], [{"item_id": "N1", "verdict": "fail", "defect_class": "relation_unlicensed",
                      "support_span": "Publisher is Recommended."}],
                not_known=["The sources do not state the publisher's level.", "The sources do not state x."])
    assert not d["not_known_kept"] and len(d["not_known_cut"]) == 2


def test_a_flag_without_a_closed_class_is_malformed():
    items = [{"item_id": "S1", "kind": "SENTENCE", "text": "a", "evidence": ["E1"]}]
    v = R.parse_check(json.dumps([{"item_id": "S1", "verdict": "flag", "defect_class": "vague"}]), items)
    assert v[0]["malformed"]


# ------------------------------------------------------------------- §15: kill and resume

def _fixture(tmp: Path) -> tuple:
    cfg = yaml.safe_load(EV.CONFIG.read_text(encoding="utf-8"))
    cfg["questions"] = [{"id": i, "text": f"question {i}"} for i in (1, 2, 3, 4)] + \
        [{"id": 14, "text": "gaps", "gaps_from_questions": [1, 2, 3, 4]}]
    cfg["run"].update({"workers": 1, "pilot_questions": [1], "progress_every_units": 1})
    cfg["absence"]["enabled"] = False      # the absence check reads the graphs; this test reads none
    (tmp / "cfg.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    ev_dir = tmp / "evidence"
    ev_dir.mkdir()
    for i in (1, 2, 3, 4):
        ev = {"question_id": i, "question": f"question {i}", "documents": {},
              "items": [{"id": "E1", "doc_id": "d", "kind": "passage", "section": "",
                         "locator": {"segment": f"d#s{i}"},
                         "text": f"Passage text for question {i}, long enough to quote from."}]}
        ev["evidence_sha256"] = EV.evidence_sha(ev)
        (ev_dir / f"Q{i}.json").write_text(json.dumps(ev), encoding="utf-8")
    (ev_dir / "catalog_entries.json").write_text(json.dumps({"items": [
        {"graph": "g", "kind": "catalog record (not admitted)", "doc_id": "plan",
         "locator": {"catalog_entry": "plan"}, "section": "", "text": "A plan, not published."}]}),
        encoding="utf-8")
    return tmp / "cfg.yaml", ev_dir


def _cmd(run: Path, cfg: Path, ev_dir: Path) -> list:
    return [sys.executable, str(REPO / "scripts" / "dcat_faq_run.py"), "--run", "--config", str(cfg),
            "--evidence-dir", str(ev_dir), "--run-dir", str(run / "run"),
            "--answers", str(run / "answers.json"), "--progress-log", str(run / "progress.log")]


def _spec(run: Path, sleep: float) -> Path:
    p = run / "spec.json"
    p.write_text(json.dumps({"calls_log": str(run / "calls.log"), "sleep_s": sleep}), encoding="utf-8")
    return p


def _final(run: Path) -> dict:
    a = json.loads((run / "answers.json").read_text(encoding="utf-8"))
    return {q["question_id"]: ([k["text"] for k in q["kept"]], [k["text"] for k in q["not_known_kept"]])
            for q in a["questions"]}


def test_sigkill_mid_loop_resumes_without_repeating_a_completed_call(tmp_path):
    ref = tmp_path / "ref"
    ref.mkdir()
    cfg, ev_ref = _fixture(ref)
    env = {**os.environ, "DCATFAQ_SCRIPTED_CONSUMER": str(_spec(ref, 0))}
    done = subprocess.run(_cmd(ref, cfg, ev_ref), env=env, capture_output=True, text=True, cwd=REPO)
    assert done.returncode == 0, done.stdout + done.stderr

    run = tmp_path / "killed"
    run.mkdir()
    cfg, ev_dir = _fixture(run)
    env = {**os.environ, "DCATFAQ_SCRIPTED_CONSUMER": str(_spec(run, 0.3))}
    proc = subprocess.Popen(_cmd(run, cfg, ev_dir), env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, cwd=REPO)
    ck = run / "run" / "checkpoint.jsonl"
    deadline = time.time() + 60
    while time.time() < deadline:
        if ck.is_file() and len(ck.read_text().splitlines()) >= 4:
            break
        time.sleep(0.02)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    before = {r["unit_id"] for r in R.Checkpoint(ck).read() if r["status"] == "done"}
    assert 0 < len(before) < 10, "the kill did not land mid-loop"
    calls_before = len((run / "calls.log").read_text().splitlines())

    again = subprocess.run(_cmd(run, cfg, ev_dir), env=env, capture_output=True, text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    after = (run / "calls.log").read_text().splitlines()[calls_before:]
    repeated = {c.split(".")[1] for c in after} & before
    assert not repeated, f"completed units called again: {sorted(repeated)}"
    assert _final(run) == _final(ref)
    assert len(_final(run)) == 5


# ---------------------------------------------------------------------- the shipped files

BANNED = [r"\bgraphs?\b", r"\bnodes?\b", r"ai-readiness-kg", r"fss-policy-kg", r"cc_tasks", r"\bDN-0\d\d",
          r"\bDCAT-00\d", r"checkpoint", r"\bvalidator\b", r"\bmodel call", r"\bpipeline\b",
          r"\bextract(ed|ion)\b", r"\bsubstrate\b", r"\bepoch\b"]


@pytest.mark.parametrize("name", ["FAQ.md", "ATTACHMENT_evidence.md"])
def test_shipped_files_carry_no_pipeline_vocabulary(name):
    p = OUT / name
    if not p.is_file():
        pytest.skip(f"{name} not built yet")
    # Quoted source passages ("> " lines) are the sources' own words and are exempt: the
    # DCAT-US overview itself speaks of the "schema validator".
    text = "\n".join(l for l in p.read_text(encoding="utf-8").splitlines() if not l.startswith(">"))
    hits = {b: re.findall(b, text, re.I)[:3] for b in BANNED if re.search(b, text, re.I)}
    assert not hits, hits


# ------------------------------------------------------------------------ the absence check

def test_content_terms_stem_and_drop_the_statement_frame():
    stop = set(yaml.safe_load(EV.CONFIG.read_text(encoding="utf-8"))["absence"]["stopwords"])
    t = EV.content_terms("The sources do not state what M-25-05 itself requires for any metadata element.", stop)
    assert "m-25-05" in t and "requir" in t and "element" in t
    assert not {"sources", "state", "what"} & set(t)
    assert "requirements".startswith(EV.stem("requires"))


def test_a_not_known_survives_only_an_absence_pass():
    d = {"kept": [], "cut": [], "not_known_cut": [],
         "not_known_kept": [{"text": "The sources do not state a."}, {"text": "The sources do not state b."},
                            {"text": "The sources do not state c."}]}
    ab = {"items": [{"id": "E1", "text": "b is stated here."}]}
    out = R.apply_absence(d, ab, [{"item_id": "N1", "verdict": "pass", "defect_class": None},
                                  {"item_id": "N2", "verdict": "fail", "defect_class": "relation_unlicensed",
                                   "support_span": "b is stated here."}])
    assert [r["text"] for r in out["not_known_kept"]] == ["The sources do not state a."]
    assert len(out["not_known_cut"]) == 2
    assert out["not_known_cut"][0]["absence_span_located"] is True


# --------------------------------------------------------------------- the built documents

import dcat_faq_build as B  # noqa: E402


def test_anchor_links_show_as_text_and_url_underscores_survive():
    assert B.anchor_links_as_text("See [Class QualityMeasurement #](#quality-measurement).") == \
        "See Class QualityMeasurement."
    assert "id_/" in B._clean("https://web.archive.org/web/20250504194000id_/https://x/")
    assert B._clean("Welcome to the _FAIRness_ Project.") == "Welcome to the FAIRness Project"


def _shipped():
    if not (OUT / "answers.json").is_file() or not (OUT / "FAQ.md").is_file():
        pytest.skip("FAQ not built yet")
    return (json.loads((OUT / "answers.json").read_text(encoding="utf-8")),
            (OUT / "FAQ.md").read_text(encoding="utf-8"),
            (OUT / "ATTACHMENT_evidence.md").read_text(encoding="utf-8"))


def test_the_faq_prints_every_kept_sentence_verbatim_and_no_cut_one():
    """Cut, never reworded: what the check kept is printed as written, and what it cut is not
    printed at all, not even reworded into something that contains it."""
    answers, faq, _ = _shipped()
    for q in answers["questions"]:
        for s in q["kept"]:
            assert s["text"] in faq, (q["question_id"], s["text"])
        for n in q["not_known_kept"]:
            assert n["text"] in faq, (q["question_id"], n["text"])
        for s in q["cut"] + q["not_known_cut"]:
            assert s["text"] not in faq, (q["question_id"], s["text"])


def test_the_attachment_quotes_every_passage_a_kept_sentence_cites():
    answers, _, att = _shipped()
    for q in answers["questions"]:
        ev = json.loads((OUT / "evidence" / f"Q{q['question_id']}.json").read_text(encoding="utf-8"))
        by_id = {it["id"]: it for it in ev["items"]}
        for s in q["kept"]:
            for eid in s["evidence"]:
                head = B.anchor_links_as_text(by_id[eid]["text"]).replace("\n", " ").strip()[:60]
                assert head in att, (q["question_id"], eid)
