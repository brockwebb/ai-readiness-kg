#!/usr/bin/env python3
"""The DCAT-US 3.0 brief's model calls: the R6 table, the prose sections and the fresh reader.
**Model spend, bounded.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decisions 3 to 6,
implementing DN-011 ADDENDUM 01 R6 to R8. The machinery is DCAT-003's
(`scripts/dcat_faq_run.py`), imported and not copied: the checkpoint, the unit key, the call and
its STOP contract, the v2 validator template (entailment and responsiveness, adversarial-review
baseline rubric v1.3.0) and the keep-or-cut rule (`decide`: a sentence survives only on `pass`
with a support span `kg/extraction/grounding.is_grounded` finds in a passage it cites, and a
"yes" to "does this answer the question"). What is new here:

* **The R6 answer** (`NEED_TEMPLATE`): one call per need over `evidence/need_<n>.json`. For each
  of R6's three questions it returns a code and one plain sentence carrying it. The validator
  sees each sentence with the classification it must support appended, so a sentence that is
  true but does not support its code is cut. Negative answers ("the public record does not ask
  for it", "no element carries it") go to the validator as NOT_KNOWN items, read against the
  need's passages and against passages found by the statement's own words across every scope,
  PDF pages included (`dcat_faq_evidence.brief_absence_evidence`).
* **The outcome letter is code** (`outcome`, the rule as `brief_config.yaml` states it). A
  Dataset property's level is read from the element table, never taken from the model. A need
  whose answer lost a part to the validator is asked once more with the cut reasons shown
  (`reask`); if a part is still cut, the row is `unassigned` and reported, never guessed.
* **The yes-or-no** (`verdict`, R7) is computed from the letters.
* **The prose sections** (`SECTION_TEMPLATE`) 1, 2, 5, 6 and 7, one call each over that
  section's evidence, checked by the same validator. Sections 3, 4 and 8 are built by code from
  the table (`scripts/dcat_brief_build.py`): a model call cannot add to a computed answer.
* **The fresh reader** (R8; DN-009 d7): `claude -p` from an empty directory, no project context,
  reading BRIEF.md alone, graded by code against the computed answers.

**Prior art.** Attribution as AIS defines it (Rashkin et al. 2021); per-claim support checking
(FActScore, Min et al. 2023); citation precision (ALCE, Gao et al. 2023); responsiveness as
SAFE's relevance step (Wei et al. 2024) and RAGAS answer relevance (Es et al. 2023); positive
controls (methodology 7.5, 7.6). The five-outcome rule is DN-011-R6's, new and saying so.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15): unit = one call; key = sha1(kind | id | input hash |
model | template hash); `reports/dcat_us_3_brief/run/checkpoint.jsonl`, appended and fsynced,
raws beside it; re-running the same phase is the resume. Pilot: the two controls run first and
their measured tokens project the rest against the ceiling before any R6 call. Ceilings: the
run's declared ledger ceiling (`run.ceiling_tokens`) and `run.max_wall_seconds`.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_run.py --phase controls
    /opt/anaconda3/bin/python3 scripts/dcat_brief_run.py --phase table
    /opt/anaconda3/bin/python3 scripts/dcat_brief_run.py --phase sections
    /opt/anaconda3/bin/python3 scripts/dcat_brief_run.py --phase reader --round 1
    /opt/anaconda3/bin/python3 scripts/dcat_brief_run.py --phase assemble     # no call
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

import dcat_faq_evidence as EV  # noqa: E402
import dcat_faq_run as FR  # noqa: E402

TASK = "cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md"
GENERATOR = "scripts/dcat_brief_run.py"
OUT = EV.BRIEF_OUT
RUN_DIR = OUT / "run"
ANSWERS = OUT / "answers.json"
CONTROL_OUT = OUT / "run" / "controls.json"
PROGRESS_LOG = REPO / "logs" / "2026-10-07_DCAT-004_brief_progress.log"
FAQ_DIR = REPO / "reports" / "dcat_us_3_faq"

ASKED = ("asked", "publicly_not_asked", "not_found_in_public_record")
LANDED = ("mandatory", "recommended", "optional", "dropped", "absent")
LITERATURE = ("matches", "carries_3_0_does_not", "carries_differently_than_asked", "not_at_catalog_layer")
LEVEL_RANK = {"Mandatory": 3, "Recommended": 2, "Optional": 1}
#: The validator, revision r3. r2 (DCAT-003 ADDENDUM 01: one judge, `primary_judge_model_id`,
#: template `CHECK_TEMPLATE_V2`) passed its positive control on 2026-10-05 (unit
#: dcfdd8601dc80360) and FAILED the same control, same unit key, same inputs, on 2026-10-07 in
#: this task's run: it kept the planted StatDCAT-AP agent-roles sentence as responsive. One
#: judge's responsiveness verdict varies from run to run on identical input, so a single
#: sample of it is not a measurement. r3 is a panel of two judges from different model
#: families (`primary_judge_model_id` and `secondary_judge_model_id`, the probe's two raters),
#: each running the unchanged v2 template, and an item is kept only when both keep it: a panel
#: of diverse LLM judges reduces single-judge variance and bias (Verga et al. 2024, "Replacing
#: Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models"), and
#: unanimity to keep is the conservative aggregation for cut-not-reword. Both controls are
#: re-run under r3 before any verdict is used.
INSTRUMENT = {"revision": "r3", "template_sha256": FR.CHECK_TEMPLATE_V2_SHA, "rubric_version": FR.RUBRIC_VERSION,
              "panel": ["primary_judge_model_id", "secondary_judge_model_id"], "aggregation": "keep only if every judge keeps"}
#: Unit-id question numbers for the non-need units, clear of needs 1-8 and the FAQ control's 0.
BRIEF_CONTROL_QID, SECTION_QID0, READER_QID0 = 90, 100, 200

NEED_TEMPLATE = """You are filling one row of a table in a one-to-two page briefing on DCAT-US 3.0, the federal government's standard for describing its datasets in a catalog. The briefing goes to the Office of Management and Budget, and its reader is not technical. The row is about one statistical need. Answer three questions about it from the numbered passages below.

The passages come in three parts, named in each passage's header: "asked" passages are the statistical side's public record (the FAIRness Project wiki and slides, the Chief Data Officers Council's data sharing report, and the Federal Committee on Statistical Methodology (FCSM) papers); "landed" passages are the DCAT-US 3.0 pages, the 2025 working draft and the Implementation Guide, and "element table row" passages give one Dataset element's requirement level as each version of the schema states it, the page as served on 5 October 2026 first; "literature" passages are statistical and web metadata standards.

RULES
1. Use ONLY the passages below. Do not use anything you know from elsewhere, even if you are sure it is true.
2. For each question write ONE sentence of at most {max_words} words that answers that question for THIS need, and cite the ids of the passages that support every part of it, for example ["E3", "E12"].
3. Question 1, asked. Choose one code:
   "asked": an "asked" passage shows FCSM, the FAIRness Project or the Chief Data Officers Council recommending, calling for, requiring or proposing this need, for metadata, for catalogs, or for what is reported to data users. The sentence names the document and what it asks for.
   "publicly_not_asked": an "asked" passage shows they considered this need and chose not to ask for it, or asked against it. The sentence names the document and says so.
   "not_found_in_public_record": no passage does either. Then write no sentence; put this statement in "not_asked_statement", completed for this need: "The public record of what FCSM and the FAIRness Project asked for does not ask for <the need>."
   A passage that uses the same word for a different thing (a "dimension" of data quality is not a statistical dimension; a software "version" is not a data revision) is not an ask.
4. Question 2, landed. Name the DCAT-US 3.0 elements that carry this need, exactly as the passages write them (a property of another class is named with its class, for example "QualityMeasurement unitMeasure"), and choose one code for the strongest level any of them has on the Dataset page as served on 5 October 2026: "mandatory", "recommended", "optional", "dropped" (listed in DCAT-US v1.1 or the 2025 working draft, not on the page as served on 5 October 2026), or "absent" (no element carries it). Set "deferred" to true only if an Implementation Guide or Overview passage says this need was put off to a later version, and then the sentence says so and cites it. For "absent", write no sentence; put the statement "No DCAT-US 3.0 element, as served on 5 October 2026, carries <the need>." in "absent_statement".
5. Question 3, literature. Choose one code:
   "matches": a standard carries this need, and DCAT-US 3.0 carries it the same way.
   "carries_3_0_does_not": a standard carries this need, and DCAT-US 3.0 does not.
   "carries_differently_than_asked": a standard carries it in a different way from what the statistical side asked for; the sentence names the difference.
   "not_at_catalog_layer": the standards put it in the data or in documentation, not in catalog metadata.
   The sentence names the standard and how it carries the need. For "matches" and "carries_3_0_does_not" it also cites a "landed" passage for what DCAT-US 3.0 does.
6. Plain language. Use short, common words. Define a term of art in the sentence that first uses it, or do not use it. Spell out an acronym the first time it appears in a sentence. Use the exact word a document uses for a requirement level (Mandatory, Recommended, Optional). Do not use the em dash character.
7. Do not mention passage ids, parts, graphs or tables in a sentence; ids go in the evidence lists only.
8. Where the passages do not answer part of a question, add at most two "not_known" statements of the form "The sources do not state ...".

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"asked": {{"code": "...", "sentence": {{"text": "...", "evidence": ["E1"]}}, "not_asked_statement": null}},
 "landed": {{"code": "...", "elements": ["..."], "deferred": false, "sentence": {{"text": "...", "evidence": ["E2"]}}, "absent_statement": null}},
 "literature": {{"code": "...", "standards": ["..."], "sentence": {{"text": "...", "evidence": ["E3"]}}}},
 "not_known": []}}
Use null for "sentence" where rule 3 or 4 says to write none.
{reask}
QUESTION {qid}: {question}

PASSAGES
{passages}
"""

REASK_NOTE = """
A FIRST ANSWER TO THIS ROW WAS CHECKED, AND THESE PARTS WERE CUT. Answer the whole row again from the passages; do not repeat a cut claim unless a passage supports every part of it.
{cuts}
"""

SECTION_TEMPLATE = """You are writing one section of a one-to-two page briefing on DCAT-US 3.0 for the Office of Management and Budget. The reader is not technical. The person briefing will hand it over, so every sentence must be backed by the numbered passages below.

SECTION {qid}: {title}
WHAT THE SECTION MUST SAY: {question}

RULES
1. Use ONLY the numbered passages below. Do not use anything you know from elsewhere, even if you are sure it is true. A fact that is in no passage does not exist for this section.
2. Write at most {max_sentences} sentences, each at most {max_words} words, one point per sentence. Each sentence cites the ids of the passages that support every part of it, for example ["E3", "E12"].
3. Plain language: short, common words a reader with no technical background can follow. Define a term of art in the sentence that first uses it, or do not use it. Spell out every acronym the first time it appears, for example "the Federal Committee on Statistical Methodology (FCSM)". Do not use the em dash character.
4. Use the exact word a document uses for a requirement (Mandatory, Recommended, Optional, must, should, may). Do not soften or strengthen it. A requirement level names the version of the page it comes from.
5. Do not recommend anything. Report what a passage says and name the document that says it.
6. Each sentence must say something the section asks for.
7. Do not mention passage ids, graphs, tables or this collection in a sentence; ids go in the evidence list only.
8. Where the passages do not support part of what the section must say, add a "not_known" statement of the form "The sources do not state ...", at most two.

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"sentences": [{{"text": "...", "evidence": ["E1"]}}], "not_known": ["The sources do not state ..."]}}

PASSAGES
{passages}
"""

READER_TEMPLATE = """Below is a short briefing. Read it, and answer three questions using only what the briefing says. Do not use anything you know from elsewhere.

1. {q1}
2. {q2}
3. {q3}

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"q1": "your answer in one or two sentences", "q2": {{"finding": "yes|no|partly", "fitness_for_use": "yes|no|partly", "text": "your answer in one or two sentences"}}, "q3": "your answer in one or two sentences"}}

BRIEFING
{brief}
"""

#: The prose sections a model writes (decision 5's order). Sections 3, 4 and 8 are built by code.
#: `faq`: questions of the DCAT-003 FAQ whose checked answers' cited passages are this section's
#: evidence ("the FAQ's answers are evidence for the brief and may be reused where their
#: validator passed"); the passages are reused, the FAQ's wording is not.
SECTIONS = {
    1: {"title": "What DCAT-US 3.0 is", "faq": [1, 3], "max_sentences": 3,
        "question": "What DCAT-US 3.0 is, in three sentences a reader with no background can follow: "
                    "that it is a catalog card for every dataset the government publishes; that it is a "
                    "United States version of a world standard; and what agencies must do by 30 September 2026."},
    2: {"title": "Who made it, and what part the Federal Committee on Statistical Methodology played",
        "faq": [2], "max_sentences": 3,
        "question": "Who made DCAT-US 3.0, and what part the Federal Committee on Statistical "
                    "Methodology (FCSM) and its FAIRness Project played."},
    5: {"title": "The void and the mismatch", "faq": [], "max_sentences": 4,
        "question": "In plain words, for each statistical need listed here, what the standards say a "
                    "catalog should carry that DCAT-US 3.0 does not (the void), or how the standards "
                    "say a need is better carried than the way the statistical side asked (the "
                    "mismatch), each with the document that says so. Needs: {needs}."},
    6: {"title": "What could happen next", "faq": [13], "max_sentences": 3,
        "question": "What options for next steps the sources support: a statistical application "
                    "profile; raising requirement levels through guidance; conformance checking. "
                    "Report what each source says; recommend nothing beyond the sources."},
    7: {"title": "What cannot be known from the public record", "faq": [], "max_sentences": 2,
        "question": "Why what the FAIRness Project recommended cannot be read from the public record: "
                    "the status of its sequencing plan, the deliverable that held its key findings and "
                    "recommendations."},
}
SECTION7_TERMS = ["sequencing", "transition plan", "provided to office of management", "key findings"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cfg() -> dict:
    return yaml.safe_load(EV.BRIEF_CONFIG.read_text(encoding="utf-8"))


def need_cfg(bcfg: dict, nid: int) -> dict:
    return next(n for n in bcfg["needs"] if n["id"] == nid)


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def load_ev(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"FATAL: {p} missing")
    ev = json.loads(p.read_text(encoding="utf-8"))
    if EV.evidence_sha(ev) != ev.get("evidence_sha256"):
        raise SystemExit(f"FATAL: {p} does not hash to its recorded evidence_sha256")
    return ev


def element_levels() -> dict:
    """element -> its row of the element table (the five versions' levels), read by code."""
    rows = json.loads(EV.TABLE_JSON.read_text(encoding="utf-8"))["rows"]
    return {r["element"]: r for r in rows}


def passage_block(ev: dict) -> str:
    """FR.passage_block with the part named in each header, so the answer can tell the
    statistical side's record from the standards."""
    out = []
    for it in ev["items"]:
        meta = ev["documents"].get(it["doc_id"]) or {}
        head = " | ".join(x for x in (f"part: {it['part']}" if it.get("part") else None,
                                       meta.get("title") or it["doc_id"], meta.get("issuer"),
                                       str(meta.get("date") or "") or None, it.get("section") or None,
                                       it["kind"]) if x)
        out.append(f"[{it['id']}] {head}\n{it['text']}")
    return "\n\n".join(out)


# ------------------------------------------------------------------------------- parsing

def parse_need_answer(text: str, ev: dict) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict):
        raise ValueError("need answer is not a JSON object")
    ids = {it["id"] for it in ev["items"]}

    def sent(s, where):
        if s is None:
            return None
        if not isinstance(s, dict) or not str(s.get("text") or "").strip():
            raise ValueError(f"{where}: sentence malformed")
        cites = [str(c) for c in (s.get("evidence") or [])]
        bad = [c for c in cites if c not in ids]
        if not cites or bad:
            raise ValueError(f"{where}: cites {'no passage' if not cites else 'ids not in the evidence file: ' + ', '.join(bad)}")
        return {"text": str(s["text"]).strip(), "evidence": cites}

    a, l, t = obj.get("asked") or {}, obj.get("landed") or {}, obj.get("literature") or {}
    if a.get("code") not in ASKED or l.get("code") not in LANDED or t.get("code") not in LITERATURE:
        raise ValueError(f"off-vocabulary code: asked={a.get('code')!r} landed={l.get('code')!r} "
                         f"literature={t.get('code')!r}")
    out = {"asked": {"code": a["code"], "sentence": sent(a.get("sentence"), "asked"),
                     "not_asked_statement": (str(a.get("not_asked_statement") or "").strip() or None)},
           "landed": {"code": l["code"], "elements": [str(e) for e in (l.get("elements") or [])],
                      "deferred": bool(l.get("deferred")), "sentence": sent(l.get("sentence"), "landed"),
                      "absent_statement": (str(l.get("absent_statement") or "").strip() or None)},
           "literature": {"code": t["code"], "standards": [str(s) for s in (t.get("standards") or [])],
                          "sentence": sent(t.get("sentence"), "literature")},
           "not_known": [str(x).strip() for x in (obj.get("not_known") or []) if str(x).strip()][:2]}
    if out["asked"]["code"] == "not_found_in_public_record":
        if not out["asked"]["not_asked_statement"]:
            raise ValueError("asked: not_found_in_public_record without its statement")
        out["asked"]["sentence"] = None
    elif out["asked"]["sentence"] is None:
        raise ValueError(f"asked: code {out['asked']['code']} without a sentence")
    if out["landed"]["code"] == "absent":
        if not out["landed"]["absent_statement"]:
            raise ValueError("landed: absent without its statement")
        out["landed"]["sentence"] = None
    elif out["landed"]["sentence"] is None:
        raise ValueError(f"landed: code {out['landed']['code']} without a sentence")
    if out["literature"]["sentence"] is None:
        raise ValueError("literature: no sentence")
    return out


def classification(part: str, ans: dict, need: dict) -> str:
    """What a part's sentence must support, in plain words, appended to its text for the
    validator. The validator passes the item only if the cited passages support this too."""
    n = need["name"]
    if part == "asked":
        c = ans["asked"]["code"]
        return (f"FCSM, the FAIRness Project or the Chief Data Officers Council publicly asked for {n}."
                if c == "asked" else
                f"FCSM, the FAIRness Project or the Chief Data Officers Council considered {n} and did not ask for it.")
    if part == "landed":
        l = ans["landed"]
        lvl = {"dropped": "listed in an earlier version and not on the page as served on 5 October 2026"}.get(
            l["code"], f"at the {l['code'].capitalize()} level on the page as served on 5 October 2026")
        d = "; a DCAT-US 3.0 document says it was deferred to a later version" if l["deferred"] else ""
        return f"In DCAT-US 3.0, {n} is carried by {', '.join(l['elements']) or 'the named element'}, {lvl}{d}."
    c = ans["literature"]["code"]
    return {"matches": f"A standard carries {n}, and DCAT-US 3.0 carries it the same way.",
            "carries_3_0_does_not": f"A standard carries {n}, and DCAT-US 3.0 does not.",
            "carries_differently_than_asked": f"A standard carries {n} differently from what the statistical side asked for.",
            "not_at_catalog_layer": f"The standards carry {n} in the data or its documentation, not in catalog metadata."}[c]


def need_items(ans: dict, need: dict) -> list:
    """The validator's items: one SENTENCE per answered part, the classification appended; a
    NOT_KNOWN item for each negative answer and each "not known" statement."""
    items = []
    for part in ("asked", "landed", "literature"):
        s = ans[part]["sentence"]
        if s is not None:
            items.append({"item_id": f"S{len(items) + 1}", "kind": "SENTENCE", "part": part,
                          "sentence": s["text"], "evidence": s["evidence"],
                          "text": f"{s['text']} [Classification this sentence must support: "
                                  f"{classification(part, ans, need)}]"})
    negs = []
    if ans["asked"]["code"] == "not_found_in_public_record":
        negs.append(("asked", ans["asked"]["not_asked_statement"]))
    if ans["landed"]["code"] == "absent":
        negs.append(("landed", ans["landed"]["absent_statement"]))
    negs += [("not_known", t) for t in ans["not_known"]]
    for i, (part, t) in enumerate(negs, 1):
        items.append({"item_id": f"N{i}", "kind": "NOT_KNOWN", "part": part, "text": t,
                      "sentence": t, "evidence": []})
    return items


def negatives(items: list) -> list:
    return [it["text"] for it in items if it["kind"] == "NOT_KNOWN"]


# --------------------------------------------------------------------------- the R6 rule

def landed_level(ans: dict, levels: dict) -> dict:
    """R6 question 2's code as the rule reads it: for named Dataset properties, from the element
    table (the page as served 2026-10-05; `dropped` when v1.1 or the working draft lists one and
    that page does not); for anything else, the validated answer's code. A disagreement with
    the model's code is recorded, and the table wins."""
    l = ans["landed"]
    # "Dataset hasQualityMeasurement" and "hasQualityMeasurement" are the same table row; a
    # property of another class ("QualityMeasurement unitMeasure") has none.
    def local(e: str) -> str:
        return re.split(r"[\s.:>]+", e.strip().strip("`"))[-1]
    rows = [levels[local(e)] for e in l["elements"]
            if local(e) in levels and not re.match(r"^(?!Dataset\b)[A-Z]\w*[\s.:>]", e.strip())]
    other = [e for e in l["elements"] if levels.get(local(e)) not in rows]
    if l["code"] == "absent":
        return {"code": "absent", "read_from": "validated absence statement", "model_code": "absent"}
    if not rows:
        return {"code": l["code"], "read_from": "validated sentence (no named Dataset property)",
                "model_code": l["code"], "elements_outside_table": other}
    live = [r["level_2026_10_05"] for r in rows if r["level_2026_10_05"]]
    if live:
        code = max(live, key=lambda x: LEVEL_RANK.get(x, 0)).lower()
    elif any(r["v11_required"] not in (None, "None") or r["draft_level"] for r in rows):
        code = "dropped"
    else:
        code = "absent"
    if other and LEVEL_RANK.get(l["code"].capitalize(), 0) > LEVEL_RANK.get(code.capitalize(), 0):
        # A property of another class (no table row) carries it at a stronger level than any
        # Dataset property named: the validated sentence is the only reading of that level.
        code = l["code"]
    return {"code": code, "read_from": "element table, page as served 2026-10-05",
            "model_code": l["code"], "overridden": code != l["code"],
            "rows": {r["element"]: r["level_2026_10_05"] for r in rows}, "elements_outside_table": other}


def outcome(asked: str, landed: str, deferred: bool, literature: str) -> str:
    """DN-011-R6, `brief_config.yaml` `outcome_rule`, first match wins."""
    if asked == "not_found_in_public_record":
        return "E"
    if asked == "asked":
        if literature in ("carries_differently_than_asked", "not_at_catalog_layer"):
            return "D"
        if landed in ("mandatory", "recommended") and not deferred:
            return "A"
        return "B"
    if literature in ("matches", "carries_3_0_does_not"):
        return "C"
    return "outside_rule"


def r7_answer(letters: list) -> str:
    n_a = sum(1 for x in letters if x == "A")
    return "yes" if n_a == len(letters) else "partly" if n_a else "no"


def verdict(rows: dict, bcfg: dict) -> dict:
    """DN-011-R7 over the letters (`brief_config.yaml` `verdict`): no if none of the group's
    needs is in A, partly if at least one is, yes if all are. A row the rule could not place
    carries the set of letters still open (`open`); the answer is computed for every
    combination of them and is determined only when all give the same answer. Otherwise it is
    reported as the set ("no or partly"), never as one of them."""
    import itertools
    out = {}
    for name, ids in bcfg["verdict"].items():
        sets = [rows[i].get("open") or [rows[i]["outcome"]] for i in ids]
        answers = sorted({r7_answer(list(c)) for c in itertools.product(*sets)},
                         key=["no", "partly", "yes"].index)
        out[name] = {"answer": " or ".join(answers), "determined": len(answers) == 1,
                     "rows": ids, "letters": {i: rows[i]["outcome"] for i in ids},
                     "open": {i: sets[k] for k, i in enumerate(ids)}}
    return out


# ---------------------------------------------------------------------------- the runner

class BriefRunner(FR.Runner):
    def __init__(self, bcfg: dict, faq_cfg: dict, ac, cc, am, cm, log, rc_consumer=None, rm=None):
        cfg = {"run": bcfg["run"], "rerun": faq_cfg["rerun"], "questions": [],
               "absence": {"enabled": False}}
        super().__init__(cfg, EV.BRIEF_EVIDENCE_DIR, RUN_DIR, ac, cc, am, cm, bcfg["run"]["workers"], log)
        self.bcfg, self.faq_cfg = bcfg, faq_cfg
        self.rc_consumer, self.rm = rc_consumer, rm
        self.absence_builder = None

    def max_attempts(self, qid: int) -> int:
        return 1 if qid in (FR.CONTROL_QID, BRIEF_CONTROL_QID) else int(self.bcfg["run"]["max_attempts"])

    def progress(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self.last_progress < self.rc["progress_every_seconds"]:
            return
        self.last_progress = now
        recs = self.ck.read()
        tok = sum(r.get("tokens", 0) for r in recs)
        done = sum(1 for r in FR.decided(recs).values() if r["status"] == "done")
        fails = sum(1 for r in recs if r["status"] != "done")
        self.log(f"[brief +{now - self.t0:7.1f}s] units done {done} calls this run {self.calls} "
                 f"tokens so far {tok:,} failures so far {fails}")

    # -- the validator panel (instrument r3)
    def panel(self, kind: str, qid: int, input_sha: str, prompt: str, parse) -> list:
        """One check by each judge of the panel, the primary first. The primary's unit keeps
        the key a single-judge check had, so a verdict already paid for is reused."""
        recs = [self._unit(kind, qid, input_sha, prompt, self.cc, self.cm, parse, FR.CHECK_TEMPLATE_V2_SHA)]
        if recs[0]["status"] == "done":
            recs.append(self._unit(f"{kind}_panel2", qid, input_sha, prompt, self.rc_consumer, self.rm,
                                   parse, FR.CHECK_TEMPLATE_V2_SHA))
        return recs

    def run_plants(self, kind: str, qid: int, input_sha: str, ev: dict, plants: list) -> dict:
        answer = FR.parse_answer(json.dumps({"sentences": [{"text": p["text"], "evidence": p["evidence"]}
                                                           for p in plants], "not_known": []}), ev, len(plants))
        if answer["precut"]:
            raise SystemExit(f"FATAL: a control plant cites an id not in its evidence: {answer['precut']}")
        items = FR.check_items(answer)
        recs = self.panel(kind, qid, input_sha, FR.check_prompt(ev, items, "v2"),
                          lambda t: FR.parse_check(t, items, "v2"))
        if any(r["status"] != "done" for r in recs) or len(recs) < 2:
            return {"passed": False, "unit_ids": [r["unit_id"] for r in recs], "reason": "a control call did not complete"}
        d = panel_decide(ev, answer, items, [r["parsed"] for r in recs], [self.cm, self.rm])
        rows = []
        for i, p in enumerate(plants):
            kept = next((r for r in d["kept"] if r["text"] == p["text"]), None)
            cut = next((r for r in d["cut"] if r["text"] == p["text"]), None)
            got = ("kept" if kept else "cut_non_responsive"
                   if cut and cut["cut_reason"].startswith("non-responsive") else "cut_unsupported")
            rows.append({"item_id": f"S{i + 1}", "expect": p["expect"], "got": got,
                         "panel": (kept or cut or {}).get("panel")})
        return {"passed": all(r["expect"] == r["got"] for r in rows), "unit_ids": [r["unit_id"] for r in recs],
                "tokens": sum(r["tokens"] for r in recs), "models": [self.cm, self.rm], "rows": rows}

    def faq_control(self) -> dict:
        """DCAT-003 ADDENDUM 01 item 5's control, its plants and frozen evidence unchanged, under
        the panel. The primary judge's unit has the same key as `dcat_faq_run.Runner.control`."""
        cc = self.faq_cfg["rerun"]["control"]
        ev = load_ev(REPO / cc["evidence"])
        return self.run_plants("control", FR.CONTROL_QID,
                               FR.sha(ev["evidence_sha256"] + json.dumps(cc, sort_keys=True)), ev, cc["sentences"])

    def brief_control(self) -> dict:
        """This task's positive control on need 4's evidence (`controls.plants` in the config)."""
        cc = self.bcfg["controls"]
        ev = load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{cc['need']}.json")
        plants = cc.get("plants") or []
        if not plants:
            raise SystemExit("FATAL: controls.plants is empty; write them before any R6 call")
        return self.run_plants("control", BRIEF_CONTROL_QID,
                               FR.sha(ev["evidence_sha256"] + json.dumps(plants, sort_keys=True)), ev, plants)

    def controls(self) -> int:
        try:
            faq = self.faq_control()
            mine = self.brief_control()
        except FR.StopRun as exc:
            self.log(f"STOP: {exc}")
            return 3
        # The FAQ control is gated on DCAT-003 ADDENDUM 01 item 5's own words: "The validator must
        # cut the first and keep the second before its verdicts are used." `passed` above is the
        # stricter test `dcat_faq_run.Runner.control` encoded (each cut plant cut AS
        # non-responsive); both are recorded, and the strict one is reported in the RESULT.
        # This task's own control is gated strictly.
        faq["passed_strict"] = faq["passed"]
        faq["passed"] = bool(faq.get("rows")) and all((r["got"] == "kept") == (r["expect"] == "kept")
                                                      for r in faq["rows"])
        faq["gate"] = "item 5 text: every plant expected cut is cut, every plant expected kept is kept"
        res = {"generated_by": GENERATOR, "generated_at": _now(), "check_template_sha256": FR.CHECK_TEMPLATE_V2_SHA,
               "instrument": INSTRUMENT, "faq_item5_control": faq, "brief_control": mine}
        write_json(CONTROL_OUT, res)
        self.log(f"CONTROL faq item 5: {'PASS' if faq['passed'] else 'FAIL'} {json.dumps(faq.get('rows'))}")
        self.log(f"CONTROL brief need {self.bcfg['controls']['need']}: {'PASS' if mine['passed'] else 'FAIL'} "
                 f"{json.dumps(mine.get('rows'))}")
        return 0 if faq["passed"] and mine["passed"] else 3

    def controls_passed(self) -> bool:
        if not CONTROL_OUT.is_file():
            return False
        c = json.loads(CONTROL_OUT.read_text(encoding="utf-8"))
        return bool(c["faq_item5_control"]["passed"] and c["brief_control"]["passed"])

    # -- one need
    def absence_for(self, nid: int, statements: list, tag: str) -> dict | None:
        if not statements:
            return None
        p = EV.BRIEF_EVIDENCE_DIR / f"need_{nid}_absence{tag}.json"
        ab = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
        if ab is None or [x["statement"] for x in ab["statements"]] != statements:
            if self.absence_builder is None:
                raise SystemExit(f"FATAL: {p} missing or stale and no graph access to rebuild it")
            ab = self.absence_builder(statements)
            ab["evidence_sha256"] = EV.evidence_sha(ab)
            write_json(p, ab)
        return ab

    def need_round(self, ev: dict, need: dict, reask: str, tag: str) -> dict:
        nid = ev["question_id"]
        prompt = NEED_TEMPLATE.format(max_words=self.bcfg["run"]["max_words"], qid=nid,
                                      question=ev["question"], passages=passage_block(ev), reask=reask)
        kind = "need_answer" if not reask else "need_reask"
        a = self._unit(kind, nid, FR.sha(ev["evidence_sha256"] + reask), prompt, self.ac, self.am,
                       lambda t: parse_need_answer(t, ev), FR.sha(NEED_TEMPLATE))
        if a["status"] != "done":
            return {"status": "unanswered", "answer_unit": a["unit_id"]}
        items = need_items(a["parsed"], need)
        ab = self.absence_for(nid, negatives(items), tag)
        cev = FR.combined_evidence(ev, ab)
        cs = self.panel("need_check" if not reask else "need_recheck", nid,
                        FR.check_input_sha_v2(a["parsed"], ab), FR.check_prompt(cev, items, "v2"),
                        lambda t: FR.parse_check(t, items, "v2"))
        if len(cs) < 2 or any(c["status"] != "done" for c in cs):
            return {"status": "unchecked", "answer_unit": a["unit_id"], "check_units": [c["unit_id"] for c in cs]}
        return judge_round(cev, a, cs, items, [self.cm, self.rm])

    def need(self, nid: int) -> dict:
        ev = load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{nid}.json")
        need = need_cfg(self.bcfg, nid)
        r1 = self.need_round(ev, need, "", "")
        out = {"need_id": nid, "need": need["name"], "rounds": [r1]}
        if r1.get("status") == "done" and r1["cut_parts"]:
            cuts = "\n".join(f"- {c['part']}: {c['sentence']!r} was cut ({c['cut_reason']}; validator: {c.get('reason')})"
                             for c in r1["cut_items"] if c["part"] in ("asked", "landed", "literature"))
            out["rounds"].append(self.need_round(ev, need, REASK_NOTE.format(cuts=cuts), "_r2"))
        return out

    # -- sections
    def section(self, k: int, ev: dict) -> dict:
        s = SECTIONS[k]
        qid = SECTION_QID0 + k
        prompt = SECTION_TEMPLATE.format(qid=k, title=s["title"], question=ev["question"],
                                         max_sentences=s["max_sentences"], max_words=self.bcfg["run"]["max_words"],
                                         passages=FR.passage_block(ev))
        a = self._unit("section_answer", qid, ev["evidence_sha256"], prompt, self.ac, self.am,
                       lambda t: FR.parse_answer(t, ev, s["max_sentences"]), FR.sha(SECTION_TEMPLATE))
        if a["status"] != "done":
            return {"section": k, "status": "unanswered"}
        items = FR.check_items(a["parsed"])
        cs = self.panel("section_check", qid, FR.check_input_sha_v2(a["parsed"], None),
                        FR.check_prompt(ev, items, "v2"), lambda t: FR.parse_check(t, items, "v2"))
        if len(cs) < 2 or any(c["status"] != "done" for c in cs):
            return {"section": k, "status": "unchecked"}
        d = panel_decide(ev, a["parsed"], items, [c["parsed"] for c in cs], [self.cm, self.rm])
        return {"section": k, "status": "done", "answer_unit": a["unit_id"], "check_units": [c["unit_id"] for c in cs],
                "tokens": {"answer": a["tokens"], "check": sum(c["tokens"] for c in cs)}, **d}

    # -- the fresh reader
    def reader(self, rnd: int, brief_text: str) -> dict:
        fr = self.bcfg["fresh_reader"]["questions"]
        prompt = READER_TEMPLATE.format(q1=fr[0], q2=fr[1], q3=fr[2], brief=brief_text)

        def parse(t):
            o = FR._json_payload(t)
            if not isinstance(o, dict) or not all(k in o for k in ("q1", "q2", "q3")):
                raise ValueError("reader answer lacks q1, q2 or q3")
            return o
        rec = self._unit("reader", READER_QID0 + rnd, FR.sha(brief_text), prompt, self.rc_consumer, self.rm,
                         parse, FR.sha(READER_TEMPLATE))
        return rec


def panel_decide(ev: dict, answer: dict, items: list, verdict_lists: list, models: list) -> dict:
    """FR.decide once per judge; an item is kept only when every judge's verdict keeps it
    (instrument r3, `INSTRUMENT`). A cut row carries the first cutting judge's reason, and every
    row carries each judge's verdict under `panel`."""
    ds = [FR.decide(ev, answer, items, v) for v in verdict_lists]

    def bytext(d):
        m = {r["text"]: (r, True) for r in d["kept"] + d["not_known_kept"]}
        m.update({r["text"]: (r, False) for r in d["cut"] + d["not_known_cut"]})
        return m
    maps = [bytext(d) for d in ds]
    out = {"kept": [], "cut": [], "not_known_kept": [], "not_known_cut": []}
    nk = {r["text"] for d in ds for r in d["not_known_kept"] + d["not_known_cut"]}
    for text, (row0, _) in maps[0].items():
        got = [m.get(text, (None, False)) for m in maps]
        panel = [{"model": md, "kept": k, "verdict": (r or {}).get("verdict"), "responsive": (r or {}).get("responsive"),
                  "reason": (r or {}).get("reason"), "cut_reason": (r or {}).get("cut_reason")}
                 for md, (r, k) in zip(models, got)]
        keep = all(k for _, k in got)
        first_cut = next((r for r, k in got if not k and r), row0)
        row = {**(row0 if keep else first_cut), "panel": panel}
        if not keep and "cut_reason" not in row:
            row["cut_reason"] = "cut by a judge of the panel"
        key = ("not_known_" if text in nk else "") + ("kept" if keep else "cut")
        out[key].append(row)
    return out


def judge_round(cev: dict, a: dict, cs: list, items: list, models: list) -> dict:
    """Keep or cut each item (the panel), then read the three codes off what was kept."""
    d = panel_decide(cev, {"precut": []}, items, [c["parsed"] for c in cs], models)
    c = {"unit_id": [x["unit_id"] for x in cs], "tokens": sum(x["tokens"] for x in cs)}
    kept_text = {r["text"] for r in d["kept"]} | {r["text"] for r in d["not_known_kept"]}
    rows, cut_items = [], []
    for it in items:
        ok = it["text"] in kept_text
        row = next((r for r in d["kept"] + d["cut"] + d["not_known_kept"] + d["not_known_cut"]
                    if r["text"] == it["text"]), {})
        rows.append({**{k: it[k] for k in ("item_id", "kind", "part", "sentence", "evidence")},
                     "kept": ok, "verdict": row.get("verdict"), "responsive": row.get("responsive"),
                     "support_span": row.get("support_span"), "reason": row.get("reason"),
                     "cut_reason": row.get("cut_reason"), "panel": row.get("panel")})
        if not ok:
            cut_items.append(rows[-1])
    parts_ok = {p: all(r["kept"] for r in rows if r["part"] == p) and any(r["part"] == p for r in rows)
                for p in ("asked", "landed", "literature")}
    return {"status": "done", "answer_unit": a["unit_id"], "check_unit": c["unit_id"],
            "answer": a["parsed"], "items": rows, "parts_validated": parts_ok,
            "cut_parts": [p for p, ok in parts_ok.items() if not ok], "cut_items": cut_items,
            "tokens": {"answer": a["tokens"], "check": c["tokens"]}}


def round_letters(r: dict, levels: dict) -> tuple:
    """The letters the R6 rule can give, from one round's VALIDATED parts: a validated part
    contributes its code (a Dataset property's level read from the table), an unvalidated one
    every code it could take. With all three validated this is exactly `outcome`'s one letter.
    Returns (letters, the codes used per part, or None where the part was not validated)."""
    import itertools
    if r.get("status") != "done":
        return None, {}
    ok, ans = r["parts_validated"], r["answer"]
    asked = [ans["asked"]["code"]] if ok["asked"] else list(ASKED)
    if ok["landed"]:
        lv = landed_level(ans, levels)
        landed, deferred = [lv["code"]], [ans["landed"]["deferred"]]
    else:
        lv, landed, deferred = None, list(LANDED), [True, False]
    lit = [ans["literature"]["code"]] if ok["literature"] else list(LITERATURE)
    letters = {outcome(a, l, d, t) for a, l, d, t in itertools.product(asked, landed, deferred, lit)}
    used = {"asked": ans["asked"]["code"] if ok["asked"] else None,
            "landed": lv["code"] if lv else None, "landed_reading": lv,
            "deferred": ans["landed"]["deferred"] if ok["landed"] else None,
            "literature": ans["literature"]["code"] if ok["literature"] else None}
    return letters, used


def row_from_need(res: dict, levels: dict) -> dict:
    """The table row. Each round constrains the letter by its validated parts; the rounds'
    letter sets are intersected (both rounds' validated parts are evidence). One letter left:
    the row is placed. More: `outcome` is `unplaced` and `open` names the letters still
    possible. None: the rounds validated conflicting codes, and the row says so. For each part
    the row keeps the latest round's validated sentence, which the brief and the claims cite."""
    base = {"need_id": res["need_id"], "need": res["need"], "rounds": len(res["rounds"])}
    letters, per_round = set("ABCDE") | {"outside_rule"}, []
    for r in res["rounds"]:
        ls, used = round_letters(r, levels)
        per_round.append({"letters": sorted(ls) if ls else None, "codes": {k: v for k, v in used.items()
                                                                            if k != "landed_reading"}})
        if ls is not None:
            letters &= ls
    parts = {}
    for k, r in enumerate(res["rounds"], 1):
        if r.get("status") != "done":
            continue
        for p in ("asked", "landed", "literature"):
            if r["parts_validated"][p]:
                _, used = round_letters(r, levels)
                parts[p] = {"round": k, "code": used[p], "items": [x for x in r["items"] if x["part"] == p]}
                if p == "landed":
                    parts[p].update(reading=used["landed_reading"], deferred=used["deferred"],
                                    elements=r["answer"]["landed"]["elements"])
    items = [x for p in ("asked", "landed", "literature") if p in parts for x in parts[p]["items"]]
    if not letters:
        outcome_, why = "unassigned", "the rounds validated codes that no single letter fits"
    elif len(letters) == 1:
        outcome_, why = next(iter(letters)), None
    else:
        outcome_, why = "unplaced", ("parts left unconfirmed by the panel in both rounds: "
                                     + ", ".join(p for p in ("asked", "landed", "literature") if p not in parts))
    return {**base, "outcome": outcome_, "open": sorted(letters) if outcome_ == "unplaced" else None,
            "reason": why, "per_round": per_round,
            "asked": (parts.get("asked") or {}).get("code"), "landed": (parts.get("landed") or {}).get("code"),
            "landed_reading": (parts.get("landed") or {}).get("reading"),
            "deferred": (parts.get("landed") or {}).get("deferred"),
            "elements": (parts.get("landed") or {}).get("elements") or [],
            "literature": (parts.get("literature") or {}).get("code"),
            "part_round": {p: v["round"] for p, v in parts.items()}, "items": items}


# ------------------------------------------------------------------------ section evidence

def faq_cited_items(qids: list) -> list:
    """The passages cited by the FAQ's kept sentences of `qids`, verbatim from its evidence
    files, deduplicated by document and locator."""
    answers = json.loads((FAQ_DIR / "answers.json").read_text(encoding="utf-8"))
    out, seen = [], set()
    for q in answers["questions"]:
        if q["question_id"] not in qids:
            continue
        ev = json.loads((FAQ_DIR / "evidence" / f"Q{q['question_id']}.json").read_text(encoding="utf-8"))
        by = {it["id"]: it for it in ev["items"]}
        for s in q["kept"]:
            for e in s["evidence"]:
                it = by[e]
                key = (it["doc_id"], json.dumps(it["locator"], sort_keys=True))
                if key not in seen:
                    seen.add(key)
                    out.append({**{k: v for k, v in it.items() if k not in ("id", "terms_matched")},
                                "faq_question": q["question_id"], "documents": ev["documents"]})
    return out


def section_evidence(k: int, items: list, question: str) -> dict:
    docs = {}
    for it in items:
        docs.update({d: m for d, m in (it.pop("documents", None) or {}).items() if d == it["doc_id"]})
    for i, it in enumerate(items, 1):
        it["id"] = f"E{i}"
    ev = {"question_id": k, "question": question, "generated_by": GENERATOR, "generated_at": _now(),
          "documents": docs, "items": items}
    ev["evidence_sha256"] = EV.evidence_sha(ev)
    return ev


def build_section_evidence(k: int, rows: dict, bcfg: dict, drv=None) -> dict | None:
    s = SECTIONS[k]
    q = s["question"]
    if k == 5:
        cd = [r for r in rows.values() if r["outcome"] in ("C", "D")]
        if not cd:
            return None
        items, seen = [], set()
        for r in cd:
            ev = load_ev(EV.BRIEF_EVIDENCE_DIR / f"need_{r['need_id']}.json")
            by = {it["id"]: it for it in ev["items"]}
            for x in r["items"]:
                if x["kind"] == "SENTENCE" and x["kept"] and x["part"] in ("asked", "literature"):
                    for e in x["evidence"]:
                        it = by[e]
                        key = (it["doc_id"], json.dumps(it["locator"], sort_keys=True))
                        if key not in seen:
                            seen.add(key)
                            items.append({**{kk: v for kk, v in it.items() if kk not in ("id", "terms_matched")},
                                          "documents": ev["documents"]})
        q = q.format(needs="; ".join(f"{r['need']} (outcome {r['outcome']})" for r in cd))
        return section_evidence(k, items, q)
    if k == 7:
        meta = EV.doc_meta(drv, bcfg)
        sd = REPO / bcfg["graphs"]["substrate_dir"]
        docs_a = bcfg["scopes"]["asked"]["airkg"] + ["dcat-us-3-implementation-guide"]
        found = EV.pdf_passages(docs_a, SECTION7_TERMS, sd, bcfg["pdf_passage_chars"])
        found += EV.substrate_passages(docs_a, SECTION7_TERMS, sd)
        found += EV.airkg_node_passages(drv, bcfg["graphs"]["airkg_database"], bcfg["graphs"]["airkg_labels"],
                                        docs_a, SECTION7_TERMS)
        cat = json.loads((FAQ_DIR / "evidence" / "catalog_entries.json").read_text(encoding="utf-8"))["items"]
        found = [dict(it, pinned=True) for it in cat if it["doc_id"] == "fairness_project_sequencing_plan"] + found
        kept, _ = EV.select(found, SECTION7_TERMS, bcfg["caps"]["asked"])
        for it in kept:
            it.pop("terms_matched", None)
            it["documents"] = {it["doc_id"]: meta[it["doc_id"]]} if it["doc_id"] in meta else {}
        return section_evidence(k, kept, q)
    return section_evidence(k, faq_cited_items(s["faq"]), q)


# ------------------------------------------------------------------------------ main

class ScriptedBriefConsumer(FR.ScriptedFileConsumer):
    """Test double for the SIGKILL resume test (§15 item 8), selected by
    `DCATFAQ_SCRIPTED_CONSUMER` as the FAQ's is. A need prompt gets a row whose three sentences
    cite E1; a check prompt is answered by the FAQ double (every item `pass`, quoting E1). Never
    selected in production."""

    def complete(self, prompt: str, *, call_id: str):
        if "\nITEMS\n" in prompt or "filling one row of a table" not in prompt:
            return super().complete(prompt, call_id=call_id)
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        from harness.consumers import Completion
        s = {"text": "Scripted sentence.", "evidence": ["E1"]}
        text = json.dumps({"asked": {"code": "asked", "sentence": s, "not_asked_statement": None},
                           "landed": {"code": "optional", "elements": ["hasQualityMeasurement"],
                                      "deferred": False, "sentence": s, "absent_statement": None},
                           "literature": {"code": "matches", "standards": ["x"], "sentence": s},
                           "not_known": []})
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 1, "outputTokens": 1})


def consumers(bcfg: dict, scripted: str | None):
    if scripted:
        c = ScriptedBriefConsumer(scripted)
        return c, c, c.model_id, c.model_id, c, c.model_id
    from kg.extraction import model_stub
    from kg import spend
    from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
    mc = model_stub.load_model_config()
    rc = bcfg["run"]
    am, cm, rm = mc[rc["answer_model_key"]], mc[rc["validator_model_key"]], mc["secondary_judge_model_id"]
    model_stub.guard_no_api_key()
    led = spend.default_ledger()
    st = led.status().get("runs", {}).get(rc["run_id"])
    if st is None or int(st.get("ceiling_tokens") or 0) != rc["ceiling_tokens"]:
        led.declare(rc["run_id"], rc["ceiling_tokens"], declared_by=f"{GENERATOR} ({TASK})",
                    call_class=rc["call_class"], **({"supersede": True} if st else {}))
    spend.set_current_run(rc["run_id"])

    def mk(m):
        return ClaudeCLIConsumer(ConsumerConfig(model_id=m, provider=FR.PROVIDER, cli=FR.CLI,
                                                timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"]))
    return mk(am), mk(cm), am, cm, mk(rm), rm


def grade_reader(ans: dict, rows: dict, v: dict, bcfg: dict) -> dict:
    """The fresh reader graded by code, by the rules `brief_config.yaml` `fresh_reader` fixed
    before the reader ran. Returns each question's verdict and what it matched."""
    fr = bcfg["fresh_reader"]
    q1 = str(ans.get("q1") or "").lower()
    q1_ok = all(any(t in q1 for t in group) for group in fr["q1_terms_all_of"])
    q2 = ans.get("q2") or {}
    allowed = {k: set(v[k]["answer"].split(" or ")) for k in ("findability", "fitness_for_use")}
    q2_ok = (str(q2.get("finding", "")).lower() in allowed["findability"]
             and str(q2.get("fitness_for_use", "")).lower() in allowed["fitness_for_use"])
    q3 = str(ans.get("q3") or "")
    named = sorted(int(k) for k, pat in fr["need_patterns"].items() if re.search(pat, q3, re.I))
    letters = {int(k): set(r.get("open") or [r["outcome"]]) for k, r in rows.items()}
    bcd = {k for k, ls in letters.items() if ls & set("BCD")}
    placed_b = {k for k, ls in letters.items() if ls == {"B"}}
    a_or_e = {k for k, ls in letters.items() if ls <= {"A", "E"}}
    q3_ok = bool(set(named) & bcd) and placed_b <= set(named) and not (set(named) & a_or_e)
    return {"q1": {"right": q1_ok}, "q2": {"right": q2_ok, "allowed": {k: sorted(x) for k, x in allowed.items()}},
            "q3": {"right": q3_ok, "named": named, "can_be_b_c_or_d": sorted(bcd), "placed_b": sorted(placed_b),
                   "in_a_or_e": sorted(a_or_e)},
            "send_back": [sec for q, sec in (("q1", 1), ("q2", 3), ("q3", 4))
                          if not {"q1": q1_ok, "q2": q2_ok, "q3": q3_ok}[q]]}


def assemble(runner: BriefRunner, bcfg: dict) -> dict:
    """answers.json from the checkpoint: re-reads every unit (no call), applies the rule."""
    levels = element_levels()
    out = {"generated_by": GENERATOR, "task": TASK, "generated_at": _now(), "rows": {}, "sections": {}}
    old = json.loads(ANSWERS.read_text(encoding="utf-8")) if ANSWERS.is_file() else {}
    for nid, res in (old.get("needs") or {}).items():
        out["rows"][int(nid)] = row_from_need(res, levels)
    out["needs"] = old.get("needs") or {}
    out["sections"] = old.get("sections") or {}
    out["readers"] = old.get("readers") or {}
    if len(out["rows"]) == len(bcfg["needs"]):
        out["verdict"] = verdict(out["rows"], bcfg)
        rows_s = {str(k): v for k, v in out["rows"].items()}
        for rnd, rd in out["readers"].items():
            if rd.get("answers"):
                rd["grade"] = grade_reader(rd["answers"], rows_s, out["verdict"], bcfg)
    recs = runner.ck.read()
    out["spend"] = {"calls": len(recs), "done": sum(1 for r in recs if r["status"] == "done"),
                    "tokens": sum(r.get("tokens", 0) for r in recs)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("controls", "table", "sections", "reader", "assemble"), required=True)
    ap.add_argument("--only", type=int, default=None, help="one need (table phase)")
    ap.add_argument("--round", type=int, default=1, help="fresh-reader round (1 or 2)")
    # Test seams (the SIGKILL resume test): a scratch run directory, evidence and answers file,
    # and no graph. Without the graph a negative answer cannot be absence-checked, and the run
    # stops on it rather than skip the check.
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--evidence-dir", default=None)
    ap.add_argument("--answers", default=None)
    ap.add_argument("--progress-log", default=None)
    ap.add_argument("--no-graph", action="store_true")
    a = ap.parse_args(argv)
    global RUN_DIR, ANSWERS, CONTROL_OUT, PROGRESS_LOG
    if a.run_dir:
        RUN_DIR = Path(a.run_dir)
        CONTROL_OUT = RUN_DIR / "controls.json"
    if a.evidence_dir:
        EV.BRIEF_EVIDENCE_DIR = Path(a.evidence_dir)
    if a.answers:
        ANSWERS = Path(a.answers)
    if a.progress_log:
        PROGRESS_LOG = Path(a.progress_log)
    bcfg = load_cfg()
    faq_cfg = EV.load_config()
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{_now()} {msg}\n")

    FR.RUN_ID = bcfg["run"]["run_id"]          # read at call time by FR.Runner._unit's records
    scripted = os.environ.get("DCATFAQ_SCRIPTED_CONSUMER")
    if a.phase == "assemble":
        ac = cc = rcons = None
        from kg.extraction import model_stub
        mc = model_stub.load_model_config()
        am, cm, rm = mc[bcfg["run"]["answer_model_key"]], mc[bcfg["run"]["validator_model_key"]], mc["secondary_judge_model_id"]
    else:
        ac, cc, am, cm, rcons, rm = consumers(bcfg, scripted)
    runner = BriefRunner(bcfg, faq_cfg, ac, cc, am, cm, log, rcons, rm)
    old = json.loads(ANSWERS.read_text(encoding="utf-8")) if ANSWERS.is_file() else {}
    rc = 0
    if a.phase == "controls":
        rc = runner.controls()
    elif a.phase in ("table", "sections"):
        if not runner.controls_passed():
            raise SystemExit("FATAL: the positive controls have not both passed; no verdict may be used")
        drv = None if a.no_graph else EV.driver()
        try:
            if drv is not None:
                meta = EV.doc_meta(drv, bcfg)
                sd = REPO / bcfg["graphs"]["substrate_dir"]
                runner.absence_builder = lambda st: EV.brief_absence_evidence(st, bcfg, drv, meta, sd,
                                                                              faq_cfg["absence"])
            if a.phase == "table":
                needs = old.get("needs") or {}
                ids = [n["id"] for n in bcfg["needs"] if not a.only or n["id"] == a.only]
                try:
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=bcfg["run"]["workers"]) as ex:
                        for res in ex.map(runner.need, ids):
                            needs[str(res["need_id"])] = res
                except FR.StopRun as exc:
                    log(f"STOP: {exc}")
                    rc = 3
                old["needs"] = needs
                write_json(ANSWERS, old)
            else:
                rows = assemble(runner, bcfg)["rows"]
                secs = old.get("sections") or {}
                for k in SECTIONS:
                    ev = build_section_evidence(k, rows, bcfg, drv)
                    if ev is None:
                        secs[str(k)] = {"section": k, "status": "none", "reason": "no row in outcome C or D"}
                        continue
                    write_json(EV.BRIEF_EVIDENCE_DIR / f"section_{k}.json", ev)
                    try:
                        secs[str(k)] = runner.section(k, ev)
                    except FR.StopRun as exc:
                        log(f"STOP: {exc}")
                        rc = 3
                        break
                old["sections"] = secs
                write_json(ANSWERS, old)
        finally:
            if drv is not None:
                drv.close()
    elif a.phase == "reader":
        brief = (OUT / "BRIEF.md").read_text(encoding="utf-8")
        try:
            rec = runner.reader(a.round, brief)
        except FR.StopRun as exc:
            log(f"STOP: {exc}")
            return 3
        readers = old.get("readers") or {}
        readers[str(a.round)] = {"unit_id": rec["unit_id"], "status": rec["status"], "model_id": rm,
                                 "brief_sha256": FR.sha(brief), "answers": rec.get("parsed"),
                                 "tokens": rec.get("tokens")}
        old["readers"] = readers
        write_json(ANSWERS, old)
    out = assemble(runner, bcfg)
    write_json(ANSWERS, out)
    runner.progress(force=True)
    log("rows: " + json.dumps({k: v["outcome"] for k, v in out["rows"].items()})
        + (" verdict: " + json.dumps({k: v["answer"] for k, v in out["verdict"].items()}) if out.get("verdict") else ""))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
