"""The DCAT-US 3.0 plain-language brief: the R6 rule, the R7 yes-or-no, the level reading, the
answer parsing, checkpoint resume under SIGKILL, and the shipped files.

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md`; DN-011 ADDENDUM 01 R6
to R8. No test here calls a model or reads a graph.
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
sys.path.insert(0, str(REPO))

import dcat_brief_run as BR  # noqa: E402
import dcat_faq_evidence as EV  # noqa: E402
import dcat_faq_lint as LINT  # noqa: E402

OUT = REPO / "reports" / "dcat_us_3_brief"
BCFG = yaml.safe_load((OUT / "brief_config.yaml").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------ the R6 rule

@pytest.mark.parametrize("asked,landed,deferred,lit,want", [
    ("not_found_in_public_record", "mandatory", False, "matches", "E"),
    ("not_found_in_public_record", "absent", False, "carries_3_0_does_not", "E"),
    ("asked", "recommended", False, "matches", "A"),
    ("asked", "mandatory", False, "carries_3_0_does_not", "A"),
    ("asked", "recommended", True, "matches", "B"),          # deferred
    ("asked", "optional", False, "matches", "B"),
    ("asked", "dropped", False, "carries_3_0_does_not", "B"),
    ("asked", "absent", False, "carries_3_0_does_not", "B"),
    ("asked", "recommended", False, "carries_differently_than_asked", "D"),
    ("asked", "optional", False, "not_at_catalog_layer", "D"),
    ("publicly_not_asked", "absent", False, "carries_3_0_does_not", "C"),
    ("publicly_not_asked", "optional", False, "matches", "C"),
    ("publicly_not_asked", "absent", False, "not_at_catalog_layer", "outside_rule"),
])
def test_outcome_rule(asked, landed, deferred, lit, want):
    assert BR.outcome(asked, landed, deferred, lit) == want


def test_the_config_rule_matches_the_code():
    """The config's rule table names the letters in the order the code applies them."""
    assert [r["letter"] for r in BCFG["outcome_rule"]] == ["E", "D", "A", "B", "C"]
    assert set(BCFG["outcomes"]) == set("ABCDE")


@pytest.mark.parametrize("letters,want", [
    ({4: "B", 7: "E"}, "no"), ({4: "D", 7: "C"}, "no"), ({4: "A", 7: "B"}, "partly"),
    ({4: "A", 7: "A"}, "yes"), ({4: "unassigned", 7: "A"}, "partly"),
])
def test_r7_fitness_for_use(letters, want):
    rows = {i: {"outcome": x} for i, x in letters.items()}
    rows.update({i: {"outcome": "A"} for i in (1, 2, 3)})
    assert BR.verdict(rows, BCFG)["fitness_for_use"]["answer"] == want


def test_r7_over_open_letters_is_determined_only_when_every_placement_agrees():
    rows = {1: {"outcome": "E"}, 2: {"outcome": "D"}, 3: {"outcome": "unplaced", "open": ["B", "C", "D", "E"]},
            4: {"outcome": "unplaced", "open": ["A", "B"]}, 7: {"outcome": "D"}}
    v = BR.verdict(rows, BCFG)
    assert v["findability"]["answer"] == "no" and v["findability"]["determined"]
    assert v["fitness_for_use"]["answer"] == "no or partly" and not v["fitness_for_use"]["determined"]


def _round(asked, landed, lit, ok, elements=("hasQualityMeasurement",)):
    return {"status": "done", "parts_validated": dict(zip(("asked", "landed", "literature"), ok)),
            "answer": {"asked": {"code": asked}, "landed": {"code": landed, "elements": list(elements), "deferred": False},
                       "literature": {"code": lit}}, "items": []}


def test_a_row_keeps_only_the_letters_its_validated_parts_allow():
    # Asked and literature validated as D-shaped: landed does not matter (R6's first match).
    r = BR.row_from_need({"need_id": 2, "need": "dimensions", "rounds": [
        _round("asked", "recommended", "carries_differently_than_asked", (True, False, True))]}, LEVELS)
    assert r["outcome"] == "D"
    # Asked and literature validated, not D-shaped, landed unconfirmed: A or B stays open.
    r = BR.row_from_need({"need_id": 4, "need": "uncertainty", "rounds": [
        _round("asked", "optional", "matches", (True, False, True))]}, LEVELS)
    assert r["outcome"] == "unplaced" and r["open"] == ["A", "B"]
    # Two rounds intersect: round 1 pins the literature, round 2 the ask.
    r = BR.row_from_need({"need_id": 7, "need": "quality dimensions", "rounds": [
        _round("asked", "optional", "carries_differently_than_asked", (False, True, True)),
        _round("asked", "optional", "matches", (True, True, False))]}, LEVELS)
    assert r["outcome"] == "D"
    # All three validated: exactly `outcome`.
    r = BR.row_from_need({"need_id": 1, "need": "x", "rounds": [
        _round("asked", "optional", "matches", (True, True, True))]}, LEVELS)
    assert r["outcome"] == BR.outcome("asked", "optional", False, "matches") == "B"


def test_r7_groups_are_the_configured_needs():
    assert BCFG["verdict"] == {"findability": [1, 2, 3], "fitness_for_use": [4, 7]}
    assert {n["id"] for n in BCFG["needs"] if n["group"] == "fitness_for_use"} == {4, 7}
    assert {n["id"] for n in BCFG["needs"] if n["group"] == "findability"} == {1, 2, 3}


# ------------------------------------------------------------------- reading the level

LEVELS = {e: {"element": e, "level_2026_10_05": l10, "v11_required": v11, "draft_level": dr}
          for e, l10, v11, dr in [("hasQualityMeasurement", "Optional", "None", "Optional"),
                                  ("describedBy", "Recommended", "No", "Recommended"),
                                  ("dataQuality", None, "No", None),
                                  ("inSeries", None, "None", "Optional")]}


def _ans(code, elements, deferred=False):
    return {"landed": {"code": code, "elements": elements, "deferred": deferred}}


def test_level_is_read_from_the_table_not_the_model():
    r = BR.landed_level(_ans("recommended", ["hasQualityMeasurement"]), LEVELS)
    assert r["code"] == "optional" and r["overridden"]


def test_strongest_named_element_wins():
    assert BR.landed_level(_ans("optional", ["hasQualityMeasurement", "Dataset describedBy"]),
                           LEVELS)["code"] == "recommended"


def test_dropped_when_only_earlier_versions_list_it():
    assert BR.landed_level(_ans("dropped", ["dataQuality"]), LEVELS)["code"] == "dropped"
    assert BR.landed_level(_ans("optional", ["inSeries"]), LEVELS)["code"] == "dropped"


def test_a_property_of_another_class_keeps_the_validated_code():
    r = BR.landed_level(_ans("optional", ["QualityMeasurement unitMeasure"]), LEVELS)
    assert r["code"] == "optional" and r["elements_outside_table"] == ["QualityMeasurement unitMeasure"]


def test_another_class_with_a_dataset_property_name_is_not_read_from_the_dataset_row():
    r = BR.landed_level(_ans("optional", ["Distribution describedBy"]), LEVELS)
    assert r["code"] == "optional" and r["read_from"].startswith("validated sentence")


# ---------------------------------------------------------------------- answer parsing

EV1 = {"items": [{"id": "E1"}, {"id": "E2"}]}


def _raw(**over):
    s = {"text": "A sentence.", "evidence": ["E1"]}
    d = {"asked": {"code": "asked", "sentence": s, "not_asked_statement": None},
         "landed": {"code": "optional", "elements": ["hasQualityMeasurement"], "deferred": False,
                    "sentence": s, "absent_statement": None},
         "literature": {"code": "matches", "standards": [], "sentence": s}, "not_known": []}
    for k, v in over.items():
        d[k] = {**d[k], **v}
    return json.dumps(d)


def test_parse_accepts_a_well_formed_row():
    p = BR.parse_need_answer(_raw(), EV1)
    assert p["asked"]["code"] == "asked" and p["landed"]["elements"] == ["hasQualityMeasurement"]


@pytest.mark.parametrize("over", [
    {"asked": {"code": "maybe"}},
    {"landed": {"sentence": {"text": "x", "evidence": ["E9"]}}},
    {"asked": {"code": "not_found_in_public_record", "sentence": None, "not_asked_statement": None}},
    {"landed": {"code": "absent", "sentence": None, "absent_statement": None}},
    {"literature": {"sentence": None}},
])
def test_parse_refuses_a_malformed_row(over):
    with pytest.raises(ValueError):
        BR.parse_need_answer(_raw(**over), EV1)


def test_negatives_go_to_the_validator_as_not_known_items():
    p = BR.parse_need_answer(_raw(
        asked={"code": "not_found_in_public_record", "sentence": None,
               "not_asked_statement": "The public record does not ask for units."},
        landed={"code": "absent", "sentence": None, "absent_statement": "No element carries units."}), EV1)
    items = BR.need_items(p, {"name": "units of measure"})
    assert [(i["kind"], i["part"]) for i in items] == [("SENTENCE", "literature"), ("NOT_KNOWN", "asked"),
                                                       ("NOT_KNOWN", "landed")]
    assert "Classification this sentence must support" in items[0]["text"]
    assert BR.negatives(items) == ["The public record does not ask for units.", "No element carries units."]


# ------------------------------------------------------------------------ evidence

def test_pdf_blocks_keep_the_page_text():
    page = ("First sentence about margins of error. Second one; it continues. " * 20).strip()
    blocks = EV.pdf_blocks(page, 200)
    assert all(len(b) <= 200 for b in blocks)
    assert re.sub(r"\s+", " ", " ".join(blocks)) == re.sub(r"\s+", " ", page)


# ------------------------------------------------------------------- §15: kill and resume

def _fixture(tmp: Path) -> dict:
    ev_dir = tmp / "evidence"
    ev_dir.mkdir()
    for n in BCFG["needs"]:
        ev = {"question_id": n["id"], "question": f"need {n['id']}", "documents": {},
              "items": [{"id": "E1", "doc_id": "d", "kind": "passage", "part": "asked", "section": "",
                         "locator": {"segment": f"d#s{n['id']}"},
                         "text": f"Passage text for need {n['id']}, long enough to quote from."}]}
        ev["evidence_sha256"] = EV.evidence_sha(ev)
        (ev_dir / f"need_{n['id']}.json").write_text(json.dumps(ev), encoding="utf-8")
    run = tmp / "run"
    run.mkdir()
    (run / "controls.json").write_text(json.dumps({"faq_item5_control": {"passed": True},
                                                   "brief_control": {"passed": True}}), encoding="utf-8")
    spec = tmp / "spec.json"
    return {"ev": ev_dir, "run": run, "spec": spec}


def _cmd(tmp: Path, f: dict) -> list:
    return [sys.executable, str(REPO / "scripts" / "dcat_brief_run.py"), "--phase", "table", "--no-graph",
            "--run-dir", str(f["run"]), "--evidence-dir", str(f["ev"]), "--answers", str(tmp / "answers.json"),
            "--progress-log", str(tmp / "progress.log")]


def _final(tmp: Path) -> dict:
    a = json.loads((tmp / "answers.json").read_text(encoding="utf-8"))
    return {k: (r["outcome"], r.get("asked"), r.get("landed"), r.get("literature")) for k, r in a["rows"].items()}


def test_sigkill_mid_loop_resumes_without_repeating_a_completed_call(tmp_path):
    ref = tmp_path / "ref"
    ref.mkdir()
    f = _fixture(ref)
    f["spec"].write_text(json.dumps({"calls_log": str(ref / "calls.log"), "sleep_s": 0}), encoding="utf-8")
    env = {**os.environ, "DCATFAQ_SCRIPTED_CONSUMER": str(f["spec"])}
    done = subprocess.run(_cmd(ref, f), env=env, capture_output=True, text=True, cwd=REPO)
    assert done.returncode == 0, done.stdout + done.stderr

    run = tmp_path / "killed"
    run.mkdir()
    g = _fixture(run)
    g["spec"].write_text(json.dumps({"calls_log": str(run / "calls.log"), "sleep_s": 0.3}), encoding="utf-8")
    env = {**os.environ, "DCATFAQ_SCRIPTED_CONSUMER": str(g["spec"])}
    proc = subprocess.Popen(_cmd(run, g), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=REPO)
    ck = g["run"] / "checkpoint.jsonl"
    deadline = time.time() + 60
    while time.time() < deadline:
        if ck.is_file() and len(ck.read_text().splitlines()) >= 5:
            break
        time.sleep(0.02)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    import dcat_faq_run as FR
    before = {r["unit_id"] for r in FR.Checkpoint(ck).read() if r["status"] == "done"}
    assert 0 < len(before) < 16, "the kill did not land mid-loop"
    calls_before = len((run / "calls.log").read_text().splitlines())

    again = subprocess.run(_cmd(run, g), env=env, capture_output=True, text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    after = (run / "calls.log").read_text().splitlines()[calls_before:]
    repeated = {c.split(".")[1] for c in after} & before
    assert not repeated, f"completed units called again: {sorted(repeated)}"
    assert _final(run) == _final(ref)
    assert len(_final(run)) == len(BCFG["needs"])


# ---------------------------------------------------------------------- the shipped files

BRIEF = OUT / "BRIEF.md"
ANSWERS = OUT / "answers.json"


def test_brief_passes_the_lint():
    assert LINT.lint(BRIEF.read_text(encoding="utf-8")) == []
    assert LINT.lint((OUT / "ROWS.md").read_text(encoding="utf-8")) == []


def test_every_model_sentence_in_the_brief_is_one_the_validator_kept_and_no_cut_one_is():
    text = BRIEF.read_text(encoding="utf-8")
    a = json.loads(ANSWERS.read_text(encoding="utf-8"))
    for k, s in a["sections"].items():
        for row in s.get("kept") or []:
            assert row["text"].rstrip() in text, f"section {k}: kept sentence missing"
        for row in s.get("cut") or []:
            assert row["text"].rstrip() not in text, f"section {k}: cut sentence printed"


def test_the_table_and_the_verdict_are_what_the_rule_computes():
    import dcat_brief_build as BB
    a = json.loads(ANSWERS.read_text(encoding="utf-8"))
    levels = BR.element_levels()
    rows = {int(k): BR.row_from_need(res, levels) for k, res in a["needs"].items()}
    for k, r in rows.items():
        assert (r["outcome"], r["open"]) == (a["rows"][str(k)]["outcome"], a["rows"][str(k)]["open"])
    v = BR.verdict(rows, BCFG)
    text = BRIEF.read_text(encoding="utf-8")
    assert {k: x["answer"] for k, x in v.items()} == {k: x["answer"] for k, x in a["verdict"].items()}
    assert f"**Finding statistical data: {v['findability']['answer']}.**" in text
    assert f"**Judging whether data are fit for a use: {v['fitness_for_use']['answer']}.**" in text
    for r in rows.values():
        assert re.search(rf"^\| {re.escape(r['need'])} \|.*\| {re.escape(BB.outcome_cell(r))} \|$", text, re.M)


def test_no_acronym_is_used_before_its_expansion():
    rep = json.loads((OUT / "build_report.json").read_text(encoding="utf-8"))
    assert [x["acronym"] for x in rep["acronyms"] if not x["ok"]] == []


@pytest.mark.parametrize("name", ["BRIEF.md", "ROWS.md"])
def test_shipped_files_carry_no_pipeline_vocabulary(name):
    """The FAQ's list (`tests/test_dcat_faq.py` BANNED), the same reader."""
    import test_dcat_faq as TF
    text = (OUT / name).read_text(encoding="utf-8")
    hits = [(p, m.group(0)) for p in TF.BANNED for m in re.finditer(p, text, re.I)]
    assert not hits, hits
