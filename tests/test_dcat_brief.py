"""The DCAT-US 3.0 plain-language brief: the R6 rule, the R7 yes-or-no, the level reading, the
answer parsing, checkpoint resume under SIGKILL, and the shipped files.

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md`; DN-011 ADDENDUM 01 R6
to R8. DCAT-005 (`cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb.md`): R7 as written,
the uncapped read of the asked record, the published-pages gate, the overlay the build reads,
and the word limit. No test here calls a model or reads a graph.
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
    # R7 as written (DCAT-005 decision 2): "no if every quality and uncertainty need is in B, C or
    # E; partly if at least one is in A". Nothing else.
    ({4: "B", 7: "E"}, "no"), ({4: "C", 7: "C"}, "no"), ({4: "A", 7: "B"}, "partly"),
    ({4: "unassigned", 7: "A"}, "partly"),
    # A D row is neither in B, C or E nor in A: with no A, the rule does not decide. DCAT-004 v2
    # had counted D as not A and answered "no" here.
    ({4: "D", 7: "C"}, "not decided"), ({4: "D", 7: "D"}, "not decided"),
    # Every need in A satisfies the "partly" clause; R7 has no "yes" clause, and none is added.
    ({4: "A", 7: "A"}, "partly"),
])
def test_r7_fitness_for_use_as_written(letters, want):
    rows = {i: {"outcome": x} for i, x in letters.items()}
    rows.update({i: {"outcome": "A"} for i in (1, 2, 3)})
    assert BR.verdict(rows, BCFG)["fitness_for_use"]["answer"] == want


def test_r7_over_open_letters_is_decided_only_when_every_placement_agrees():
    rows = {1: {"outcome": "E"}, 2: {"outcome": "D"}, 3: {"outcome": "unplaced", "open": ["B", "C", "D", "E"]},
            4: {"outcome": "unplaced", "open": ["A", "B"]}, 7: {"outcome": "D"}}
    v = BR.verdict(rows, BCFG)
    f, u = v["findability"], v["fitness_for_use"]
    assert (f["answer"], f["determined"], f["partly_if"]) == ("not decided", False, [])
    assert [x["row"] for x in f["no_needs"]] == [2, 3]
    assert (u["answer"], u["determined"], u["partly_if"]) == ("not decided", False, [4])
    assert [x["row"] for x in u["no_needs"]] == [4, 7]
    # Open letters that all give one decided answer decide it.
    rows.update({4: {"outcome": "unplaced", "open": ["B", "C"]}, 7: {"outcome": "E"}})
    u = BR.verdict(rows, BCFG)["fitness_for_use"]
    assert (u["answer"], u["determined"]) == ("no", True)


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


# ----------------------------------------------------------- DCAT-005: the overlay on a row

def _fr(verdict, kept=()):
    return {"verdict": verdict, "evidence_file": "need_1_full_read.json", "kept": list(kept), "matched": 3,
            "read": 3, "batches": 1, "readers": ["m1", "m2"], "dropped_by_cap": 0, "status": "done"}


def _res(*rounds):
    return {"need_id": 1, "need": "series", "rounds": list(rounds)}


def test_a_full_read_with_no_ask_keeps_the_row_in_e_and_says_it_was_read():
    r = BR.row_from_need(_res(_round("not_found_in_public_record", "dropped", "carries_3_0_does_not",
                                     (True, True, True), ("inSeries",))), LEVELS, {"full_read": _fr("not_found_in_full_read")})
    assert (r["outcome"], r["asked_read"], r["part_round"]["asked"]) == ("E", "not_found_in_full_read", "full_read")
    assert [x["kind"] for x in r["items"] if x["part"] == "asked"] == ["FULL_READ"]


def test_a_full_read_that_finds_an_ask_re_places_the_row():
    ask = {"item_id": "S1", "kind": "SENTENCE", "part": "asked", "sentence": "FCSM asks for it.",
           "evidence": ["E4"], "evidence_file": "need_1_full_read.json", "kept": True, "verdict": "pass",
           "responsive": "yes", "support_span": "x", "reason": "r", "cut_reason": None, "panel": []}
    base = _round("not_found_in_public_record", "dropped", "carries_3_0_does_not", (True, True, True), ("inSeries",))
    r = BR.row_from_need(_res(base), LEVELS, {"full_read": _fr("asked", [ask])})
    # asked, dropped (inSeries is in the working draft only), the literature carries it: B.
    assert (r["outcome"], r["asked"]) == ("B", "asked")
    assert [x["evidence_file"] for x in r["items"] if x["part"] == "asked"] == ["need_1_full_read.json"]


def test_a_full_read_that_did_not_finish_changes_nothing():
    base = _round("not_found_in_public_record", "dropped", "carries_3_0_does_not", (True, True, True), ("inSeries",))
    fr = {**_fr(None), "status": "incomplete"}
    r = BR.row_from_need(_res(base), LEVELS, {"full_read": fr})
    assert r["outcome"] == "E" and r["asked_read"] is None


def test_a_draft_citation_cut_on_recheck_unvalidates_that_part():
    rnd = _round("asked", "optional", "matches", (True, False, True))
    rnd["items"] = [{"item_id": "S2", "kind": "SENTENCE", "part": "literature", "sentence": "3.0 does too.",
                     "evidence": ["E1", "E23"], "kept": True}]
    res = {"need_id": 4, "need": "uncertainty", "rounds": [rnd]}
    kept = BR.row_from_need(res, LEVELS, {"rechecks": [{"round": 1, "part": "literature", "kept": True,
                                                       "evidence_published": ["E1"]}]})
    assert kept["literature"] == "matches" and kept["items"][0]["evidence"] == ["E1"]
    cut = BR.row_from_need(res, LEVELS, {"rechecks": [{"round": 1, "part": "literature", "kept": False,
                                                      "evidence_published": ["E1"], "cut_reason": "fail"}]})
    assert cut["literature"] is None and cut["outcome"] == "unplaced"
    assert res["rounds"][0]["parts_validated"]["literature"] is True, "the DCAT-004 round was modified"


def test_parse_read_refuses_a_quote_the_passage_does_not_hold():
    import dcat_brief_correct as BC
    ev = {"items": [{"id": "E1", "text": "Agencies should report the series a dataset belongs to."},
                    {"id": "E2", "text": "Other text."}]}
    ok = BC.parse_read(json.dumps({"asks": [{"id": "E1", "quote": "report the series", "sentence": "S."}]}), ev, ["E1"])
    assert ok["asks"][0]["id"] == "E1"
    for bad in ({"id": "E1", "quote": "report the vintage", "sentence": "S."},
                {"id": "E2", "quote": "Other text", "sentence": "S."},          # not in this batch
                {"id": "E1", "quote": "report the series", "sentence": ""}):
        with pytest.raises(ValueError):
            BC.parse_read(json.dumps({"asks": [bad]}), ev, ["E1"])


def test_published_gate_refuses_a_3_0_claim_resting_on_the_draft(monkeypatch):
    import dcat_brief_build as BB
    ev = {"items": [{"id": "E1", "doc_id": EV.DRAFT, "kind": "document text"},
                    {"id": "E2", "doc_id": "w3c-dqv", "kind": "document text"},
                    {"id": "E3", "doc_id": EV.LIVE, "kind": "element table row"}]}
    monkeypatch.setattr(BB, "load_ev", lambda name: ev)

    def row(evidence, code="matches"):
        return {"1": {"landed": None, "literature": code, "items": [
            {"part": "literature", "kind": "SENTENCE", "kept": True, "evidence": evidence}]}}
    assert BB.published_gate(row(["E2", "E3"]), BCFG) == []
    assert BB.published_gate(row(["E1", "E2"]), BCFG) == ["row 1 literature: no published page cited",
                                                         "row 1 literature: cites the 2025 working draft for what 3.0 carries"]
    assert BB.published_gate(row(["E2"], "carries_differently_than_asked"), BCFG) == []


def test_full_read_evidence_reads_every_match_uncapped(monkeypatch, tmp_path):
    sd = tmp_path / "substrate"
    sd.mkdir()
    need = {"id": 1, "name": "series", "plain": "p", "asked": ["series"]}
    docs = BCFG["scopes"]["asked"]["airkg"]
    paras = [f"Paragraph {i} about a series of releases, long enough to stand alone as a passage." for i in range(60)]
    (sd / f"{docs[0]}.md").write_text("# Head\n\n" + "\n\n".join(paras + [paras[0]]) + "\n", encoding="utf-8")
    monkeypatch.setattr(EV, "REPO", tmp_path)
    monkeypatch.setattr(EV, "pdf_passages", lambda *a, **k: [])
    monkeypatch.setattr(EV, "airkg_node_passages", lambda *a, **k: [
        {"graph": "g", "kind": "extracted claim span", "doc_id": docs[0], "locator": {"node": "n1"}, "section": "",
         "text": "about a series of releases"},                                   # inside paragraph text
        {"graph": "g", "kind": "extracted claim span", "doc_id": docs[0], "locator": {"node": "n2"}, "section": "",
         "text": "a series named only in the graph"}])
    monkeypatch.setattr(EV, "fss_passages", lambda *a, **k: [])
    (tmp_path / "corpus").mkdir()
    (tmp_path / "corpus" / "manifest.json").write_text(json.dumps({"entries": {d: {"identity": {
        "canonical_path": f"corpus/{d}.pdf"}} for d in docs}}), encoding="utf-8")
    meta = {d: {"title": d} for d in docs + BCFG["scopes"]["asked"]["fss"]}
    cfg = {**BCFG, "caps": {p: {**BCFG["caps"][p], "max_chars": 1000} for p in ("asked", "landed", "literature")}}
    ev = EV.full_read_evidence(need, cfg, None, meta, sd)
    assert ev["dropped_by_cap"] == 0
    assert (ev["matched"], ev["graph_passages_inside_document_text"], ev["exact_repeats"]) == (63, 1, 1)
    assert ev["read"] == len(ev["items"]) == 61
    ids = [i for b in ev["batches"] for i in b]
    assert ids == [it["id"] for it in ev["items"]], "every passage read once, in order"
    by = {it["id"]: it for it in ev["items"]}
    assert all(sum(len(by[i]["text"]) for i in b) <= 3000 for b in ev["batches"])
    assert len(ev["batches"]) > 1


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


def _fr_fixture(tmp: Path) -> dict:
    """Three needs' full-read evidence, three batches each, and passing controls."""
    ev_dir = tmp / "evidence"
    ev_dir.mkdir()
    for nid in BCFG["amendment_2026_10_07_dcat005"]["full_read"]["needs"]:
        items = [{"id": f"E{i}", "doc_id": "d", "kind": "document text", "part": "asked", "section": "",
                  "locator": {"file": "f", "line": i}, "text": f"Passage {i} of need {nid}, long enough to read."}
                 for i in range(1, 7)]
        ev = {"question_id": nid, "question": f"need {nid}", "documents": {}, "items": items, "matched": 6,
              "read": 6, "dropped_by_cap": 0, "batches": [["E1", "E2"], ["E3", "E4"], ["E5", "E6"]]}
        ev["evidence_sha256"] = EV.evidence_sha(ev)
        (ev_dir / f"need_{nid}_full_read.json").write_text(json.dumps(ev), encoding="utf-8")
    run = tmp / "run"
    run.mkdir()
    (run / "controls_dcat005.json").write_text(json.dumps({"faq_item5_control": {"passed": True},
                                                          "brief_control": {"passed": True}}), encoding="utf-8")
    (tmp / "answers.json").write_text(json.dumps({"needs": {}}), encoding="utf-8")
    return {"ev": ev_dir, "run": run, "spec": tmp / "spec.json"}


def _fr_cmd(tmp: Path, f: dict) -> list:
    return [sys.executable, str(REPO / "scripts" / "dcat_brief_correct.py"), "--phase", "full_read",
            "--run-dir", str(f["run"]), "--evidence-dir", str(f["ev"]), "--answers", str(tmp / "answers.json"),
            "--progress-log", str(tmp / "progress.log")]


def _fr_final(tmp: Path) -> dict:
    c = json.loads((tmp / "run" / "corrections.json").read_text(encoding="utf-8"))
    return {k: (v["status"], v["verdict"], sorted((r["batch"], r["model_id"]) for r in v["reads"]))
            for k, v in c["full_read"].items()}


def test_full_read_sigkill_mid_loop_resumes_without_repeating_a_completed_call(tmp_path):
    """§15 item 8 for DCAT-005's reading loop: kill it mid-loop, re-run the same command, and get
    the uninterrupted run's result with no completed unit called twice."""
    ref = tmp_path / "ref"
    ref.mkdir()
    f = _fr_fixture(ref)
    f["spec"].write_text(json.dumps({"calls_log": str(ref / "calls.log"), "sleep_s": 0}), encoding="utf-8")
    env = {**os.environ, "DCATFAQ_SCRIPTED_CONSUMER": str(f["spec"])}
    done = subprocess.run(_fr_cmd(ref, f), env=env, capture_output=True, text=True, cwd=REPO)
    assert done.returncode == 0, done.stdout + done.stderr

    run = tmp_path / "killed"
    run.mkdir()
    g = _fr_fixture(run)
    g["spec"].write_text(json.dumps({"calls_log": str(run / "calls.log"), "sleep_s": 0.3}), encoding="utf-8")
    env = {**os.environ, "DCATFAQ_SCRIPTED_CONSUMER": str(g["spec"])}
    proc = subprocess.Popen(_fr_cmd(run, g), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=REPO)
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
    assert 0 < len(before) < 20, "the kill did not land mid-loop"
    calls_before = len((run / "calls.log").read_text().splitlines())

    again = subprocess.run(_fr_cmd(run, g), env=env, capture_output=True, text=True, cwd=REPO)
    assert again.returncode == 0, again.stdout + again.stderr
    after = (run / "calls.log").read_text().splitlines()[calls_before:]
    repeated = {c.split(".")[1] for c in after} & before
    assert not repeated, f"completed units called again: {sorted(repeated)}"
    assert _fr_final(run) == _fr_final(ref)
    assert all(v[:2] == ("done", "not_found_in_full_read") and len(v[2]) == 6 for v in _fr_final(run).values())


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


CORR = OUT / "run" / "corrections.json"


def test_the_table_and_the_verdict_are_what_the_rule_computes():
    """DCAT-004 v2's record with DCAT-005's overlay, recomputed here, is what the overlay file
    holds and what the brief prints."""
    import dcat_brief_build as BB
    import dcat_brief_correct as BC
    a = json.loads(ANSWERS.read_text(encoding="utf-8"))
    c = json.loads(CORR.read_text(encoding="utf-8"))
    levels = BR.element_levels()
    rows = {int(k): BR.row_from_need(res, levels, BC.overlay_for(c, int(k))) for k, res in a["needs"].items()}
    for k, r in rows.items():
        assert (r["outcome"], r["open"]) == (c["rows"][str(k)]["outcome"], c["rows"][str(k)]["open"])
    v = BR.verdict(rows, BCFG)
    text = BRIEF.read_text(encoding="utf-8")
    assert {k: x["answer"] for k, x in v.items()} == {k: x["answer"] for k, x in c["verdict"].items()}
    for name, label in (("findability", "Finding statistical data"),
                        ("fitness_for_use", "Judging whether data are fit for a use")):
        assert f"**{label} ({BB.row_range(v[name]['rows'])}): {v[name]['answer']}.**" in text
    for r in rows.values():
        assert re.search(rf"^\| {re.escape(r['need'])} \|.*\| {re.escape(BB.outcome_cell(r))} \|$", text, re.M)


def test_the_dcat004_record_is_not_rewritten():
    """DCAT-005 corrects by overlay: answers.json still holds DCAT-004 v2's own rows and verdict."""
    a = json.loads(ANSWERS.read_text(encoding="utf-8"))
    assert a["task"] == "cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md"
    assert "full_read" not in a and "rechecks" not in a


def test_the_full_read_left_nothing_unread():
    """DN-012 d1: every need the amendment names was read uncapped, every batch by both readers."""
    c = json.loads(CORR.read_text(encoding="utf-8"))
    am = BCFG["amendment_2026_10_07_dcat005"]
    assert sorted(c["full_read"]) == sorted(str(n) for n in am["full_read"]["needs"])
    for nid, fr in c["full_read"].items():
        ev = json.loads((OUT / "evidence" / fr["evidence_file"]).read_text(encoding="utf-8"))
        assert ev["dropped_by_cap"] == 0 and fr["status"] == "done"
        assert sorted(i for b in ev["batches"] for i in b) == sorted(it["id"] for it in ev["items"])
        assert {(r["batch"], r["model_id"]) for r in fr["reads"] if r["status"] == "done"} == {
            (k, m) for k in range(1, len(ev["batches"]) + 1) for m in fr["readers"]}
        assert len(set(fr["readers"])) == 2


def test_section_5_states_the_void_as_the_rule_s_limit():
    text = BRIEF.read_text(encoding="utf-8")
    assert "No need is in outcome C" not in text
    assert "cannot be shown while the plan is unpublished" in text


def test_the_body_is_within_the_word_limit():
    rep = json.loads((OUT / "build_report.json").read_text(encoding="utf-8"))
    assert rep["body_words"]["words"] <= BCFG["amendment_2026_10_07_dcat005"]["max_body_words"]


def test_the_working_draft_is_cited_only_as_the_draft():
    text = BRIEF.read_text(encoding="utf-8")
    src = text.split("## Sources")[1]
    for line in src.splitlines():
        if "Candidate Recommendation" in line:
            assert "the 2025 working draft" in line.lower() or "2025 working draft" in line, line


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
