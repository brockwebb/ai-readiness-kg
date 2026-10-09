#!/usr/bin/env python3
"""Answer and check the DCAT-US 3.0 FAQ, one question at a time. **Model spend, bounded.**

`cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md` steps 2 and 3, implementing
DN-011-R5. For each question, two calls:

1. **Answer** (the extraction model, `model_config.yaml::model_id`). It sees only that
   question's evidence file (`scripts/dcat_faq_evidence.py`) and returns at most
   `run.max_answer_sentences` sentences, each citing passage ids, plus "not known" statements
   for the parts the passages do not answer.
2. **Check** (the judge model, `model_config.yaml::primary_judge_model_id`, a different model
   from the writer). It sees the same passages and the answer, and marks each sentence and each
   "not known" statement `pass`, `flag` or `fail`. The prompt is an overlay of the
   adversarial-review baseline rubric v1.3.0 (role, anti-anchoring, the verbatim grounding rule,
   the closed defect classes), stamped on every row as `rubric_version`.

**What is kept is decided by code, not by either model.** A sentence survives only when the
checker says `pass` AND its `support_span` is found verbatim (whitespace-normalised) in a
passage the sentence cites (`kg/extraction/grounding.is_grounded`: NFKC, de-hyphenation, whitespace
collapse; case-sensitive, not fuzzy); a sentence citing a passage id that is not in the evidence file is
cut before the check. A "not known" statement survives only on `pass`. Everything else is CUT,
never reworded, and recorded with its verdict and reason. This is per-claim attribution
checking as AIS defines it (Rashkin et al. 2021) and FActScore measures it (Min et al. 2023);
the cut-not-repair rule is the task's.

Question 14 is answered last, from the "not known" statements kept on questions 1-13 and the
catalog records of documents that were looked for and are not public. Since DCAT-003 ADDENDUM 01
it is built by code (`built_by_code` in the config, `scripts/dcat_faq_build.py`) and makes no call.

**Template versions (ADDENDUM 01 step 5).** The questions named under `rerun` in the config are
answered and checked under the v2 templates; every other question keeps its v1 units, found by
the v1 template hashes, so nothing already checked is re-asked. v2 adds four answer rules (a
draft's statement says it is a draft and whether the published schema carries it; a stated
requirement level names its version; no em dash; each sentence answers the question, and a
question's named options each get a sentence or a "not known" item). The v2 check asks a second
question per sentence, "does this sentence answer the question asked?", and a "no" is cut as an
unsupported claim is cut. It also folds the absence check into the one validator call: the "not
known" items are read against the question's passages and against the passages found by their
own words (ids `A1`...), in the same call. Before any v2 verdict is used, a positive control
(`rerun.control`, methodology 7.6) plants one entailed but non-responsive sentence and one
responsive sentence; the validator must cut the first as non-responsive and keep the second.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15, the shape of `scripts/run_definition_pairs.py`). Unit
= one call. Key = sha1(kind | question | input hash | model | prompt-template hash): an answer's
input hash is its evidence file's content hash, a check's is the answer's text, so a changed
evidence file, prompt or model is a new unit and a stale result is never reused. Every attempt
is appended and fsynced to `run/checkpoint.jsonl` before the next result is awaited; the raw
prompt and response sit beside it under `run/raw/`. Re-running is the resume command. The pilot
(`run.pilot_questions`) runs first and its measured tokens per call project the rest before any
other call is made. The token ceiling is the shared spend ledger's (DD-022, reserve before
dispatch); the wall-clock ceiling is `run.max_wall_seconds`. A failed or unparseable call is a
row and is retried up to `run.max_attempts`.

    /opt/anaconda3/bin/python3 scripts/dcat_faq_run.py --dry-run          # prompts and plan, no call
    /opt/anaconda3/bin/python3 scripts/dcat_faq_run.py --run              # pilot, then the rest
    /opt/anaconda3/bin/python3 scripts/dcat_faq_run.py --rerun            # control, then the v2 questions
    /opt/anaconda3/bin/python3 scripts/dcat_faq_run.py --assemble         # answers.json from the checkpoint

Exit 0 when every question is answered and checked (or exhausted its attempts), 3 when a
ceiling or a model substitution stopped it; the checkpoint keeps every completed call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import dcat_faq_evidence as EV  # noqa: E402

TASK = "cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md"
GENERATOR = "scripts/dcat_faq_run.py"
OUT = EV.OUT
RUN_DIR = OUT / "run"
ANSWERS = OUT / "answers.json"
PROGRESS_LOG = REPO / "logs" / "2026-10-05_DCAT-003_faq_progress.log"
RUN_ID = "dcat_us_3_faq_2026-10-05"
ADDENDUM_TASK = "cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md"
CONTROL_OUT = OUT / "control" / "control_result.json"
#: The control's units are keyed under this question id, so they never collide with a question's.
CONTROL_QID = 0
RUBRIC_VERSION = "v1.3.0"
OVERLAY = "faq-claim-attribution (project-local, ai-readiness-kg)"
PROVIDER = "claude_max_oauth"   # the CLI is the seldon lock's (AD-035 R3, task MODEL-001)
DEFECT_CLASSES = ("relation_unlicensed", "boundary_imprecision", "surface_form_absent",
                  "mention_context_invalid", "granularity_dispute")
VERDICTS = ("pass", "flag", "fail")
#: Words per answer sentence. The answer is read aloud in a briefing (DN-011-R5: "each answer
#: is short"); the first pilot answer, written without a limit, ran 60 to 80 words a sentence.
MAX_WORDS = 35

ANSWER_TEMPLATE = """You are answering one question for a briefing on DCAT-US 3.0 to the Office of Management and Budget. The person briefing will say your answer out loud and hand it over, so every sentence must be backed by the numbered passages below.

RULES
1. Use ONLY the numbered passages below. Do not use anything you know from elsewhere, even if you are sure it is true. A fact that is in no passage does not exist for this answer.
2. Write at most {max_sentences} sentences, each at most {max_words} words: a short answer the reader can say out loud, with the detail left to the passages. Make one point per sentence. Each sentence cites the ids of the passages that support it, for example ["E3", "E12"]. Cite only passages that, read on their own, support every part of the sentence.
3. Plain language. Use the exact word a document uses for a requirement (Mandatory, Recommended, Optional, must, should, may). Do not soften or strengthen it.
4. When documents could disagree, name the document a fact comes from (for example "the Dataset page as captured on 15 September 2026 lists ...").
5. Where the passages do not answer part of the question, add a "not_known" statement of the form "The sources do not state ...", one per missing part, at most three. Do not guess what the answer would be.
6. Do not recommend anything. If the question asks about options, report only what a passage says or supports, and say which document says it.
7. Passages of kind "catalog record (not admitted)" describe documents that were looked for and are not in the collection; cite them only for what they say about that document.
8. Passages of kind "element table row" quote, for one schema element, the line each version of the schema gives it; "Not listed in" names the versions that do not list the element.
9. Do not mention passage ids, graphs, tables or this collection in the sentence text; the ids go in the evidence list only.

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"sentences": [{{"text": "...", "evidence": ["E1"]}}], "not_known": ["The sources do not state ..."]}}

QUESTION {qid}: {question}

PASSAGES
{passages}
"""

CHECK_TEMPLATE = """You are an adversarial reviewer (adversarial-review baseline rubric {rubric_version}, overlay {overlay}). Your job is to find what is WRONG with each item below, not to agree with it. A clean item gets "pass" with no defect. Do not manufacture a defect to look diligent, and do not pass an item to be agreeable. The answer you are checking may read as confident; that is evidence about its writer, not about the passages.

There are two kinds of item.

SENTENCE items claim facts and cite passages. Judge a SENTENCE only against the passages it cites. Anything you know from elsewhere does not count, for it or against it.
- "pass": every factual part of the sentence is stated by the cited passages. Put in support_span a run of text copied character for character from ONE cited passage that carries the core of the claim.
- "flag": the cited passages support it only in part, or the sentence overstates or understates them: a stronger or weaker modal, a wider scope, a date, number or name the passages do not give, a claim about one document that a different document makes.
- "fail": the cited passages do not contain the claim, or contradict it.

NOT_KNOWN items claim that the passages do not state something. Judge a NOT_KNOWN item against ALL the passages.
- "pass": no passage states the thing the item says is not known.
- "fail": a passage does state it. Put the passage text that states it in support_span.

Grounding rule (non-negotiable): support_span is copied character for character from one passage. Do not paraphrase, repair, abbreviate or join fragments. If you cannot quote, the item is not a "pass".

defect_class is null on "pass"; on "flag" or "fail" it is exactly one of: relation_unlicensed (the passage does not say this of that subject), boundary_imprecision (the extent is wrong: modal, scope, number, date), surface_form_absent (the content is not in the cited passages at all), mention_context_invalid (the words are there but only in a context that asserts nothing: an example, a navigation list, a heading, a question), granularity_dispute (right referent, wrong level).

Return ONLY a JSON array, one object per item, in the order given, with no prose and no code fence:
[{{"item_id": "S1", "verdict": "pass", "defect_class": null, "support_span": "...", "reason": "one sentence", "confidence": 0.9}}]

QUESTION {qid}: {question}

PASSAGES
{passages}

ITEMS
{items}
"""


#: v2 (ADDENDUM 01 step 5). The v1 rules stand; 5 is widened to five "not known" items so a
#: question with named options can give each one; 10 to 13 are new, 14 is filled in only for a
#: question with named options.
ANSWER_TEMPLATE_V2 = ANSWER_TEMPLATE.replace(
    "one per missing part, at most three.", "one per missing part, at most five.").replace(
    """9. Do not mention passage ids, graphs, tables or this collection in the sentence text; the ids go in the evidence list only.
""", """9. Do not mention passage ids, graphs, tables or this collection in the sentence text; the ids go in the evidence list only.
10. A statement taken from a draft (a passage whose document is a working draft or a Candidate Recommendation) says so in the sentence, for example "the 2025 Candidate Recommendation says ...". Then say whether the published schema carries it: cite a passage from a published DCAT-US 3.0 page that states it, or, if no passage does, add a "not_known" statement of the form "The sources do not state that the published DCAT-US 3.0 schema carries ...".
11. A sentence that states a requirement level (Mandatory, Recommended, Optional) names the version of the page it reads, for example "the Dataset page as served on 5 October 2026" or "the 2025 Candidate Recommendation".
12. Do not use the em dash character anywhere. Use a comma, a colon or two sentences instead.
13. Each sentence must answer the question asked, or one part of it. A sentence that is true of its passages but does not bear on what the question asks is not an answer; leave it out.
{options_rule}""")
OPTIONS_RULE = ("14. The question names these options: {options}. For each option, either write a "
                "sentence that a passage supports about that option, naming the option, or add a "
                "not_known statement about that option. Report what the passages say; do not "
                "recommend.\n")

CHECK_TEMPLATE_V2 = CHECK_TEMPLATE.replace(
    """- "fail": the cited passages do not contain the claim, or contradict it.

NOT_KNOWN items""", """- "fail": the cited passages do not contain the claim, or contradict it.
Then answer a second question for every SENTENCE: does this sentence answer the question asked, or a part of it? First name to yourself the subject the QUESTION asks about and what it asks of that subject. The sentence is responsive ("yes") only if it states, about that subject, something the question asks for, or something about one of the options the question names as applied to that subject. It is "no" when its subject is something else, even when it shares words or a field with the question, and "no" when it is a true background fact about the subject that the question does not ask for. Put "yes" or "no" in "responsive". Judge responsiveness against the QUESTION text only, never against what the passages happen to contain. For NOT_KNOWN items put null.

NOT_KNOWN items""").replace(
    """NOT_KNOWN items claim that the passages do not state something. Judge a NOT_KNOWN item against ALL the passages.""",
    """NOT_KNOWN items claim that the passages do not state something. Judge a NOT_KNOWN item against ALL the passages: those with ids E... were gathered for the question, and those with ids A... were found by searching the same documents with the NOT_KNOWN items' own words.""").replace(
    """[{{"item_id": "S1", "verdict": "pass", "defect_class": null, "support_span": "...", "reason": "one sentence", "confidence": 0.9}}]""",
    """[{{"item_id": "S1", "verdict": "pass", "defect_class": null, "support_span": "...", "responsive": "yes", "reason": "one sentence", "confidence": 0.9}}]""")
RESPONSIVE = ("yes", "no")
#: Revision history of the v2 check's responsiveness question. r1 (template sha 8efb45bc...)
#: FAILED its positive control on 2026-10-05: it kept the planted StatDCAT-AP agent-roles
#: sentence as responsive to Q13 (control unit 0973f64820b65388, 53,890 tokens). r2 asks for
#: relevance to the subject the question asks about, as SAFE's relevance step does (Wei et al.
#: 2024, "Long-form factuality in large language models") and as RAGAS answer relevance
#: penalises an on-topic-sounding answer that does not address the question (Es et al. 2023);
#: its control adds a held-out off-subject plant, so a pass is not fitted to one sentence.


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


ANSWER_TEMPLATE_SHA = sha(ANSWER_TEMPLATE)
CHECK_TEMPLATE_SHA = sha(CHECK_TEMPLATE)
ANSWER_TEMPLATE_V2_SHA = sha(ANSWER_TEMPLATE_V2)
CHECK_TEMPLATE_V2_SHA = sha(CHECK_TEMPLATE_V2)
for _t in (ANSWER_TEMPLATE_V2, CHECK_TEMPLATE_V2):
    assert _t not in (ANSWER_TEMPLATE, CHECK_TEMPLATE), "a v2 template failed to patch its v1 base"


def template_version(cfg: dict, qid: int) -> str:
    rr = cfg.get("rerun") or {}
    return rr.get("template", "v1") if qid in (rr.get("questions") or []) else "v1"


def is_code_built(cfg: dict, qid: int) -> bool:
    return any(q["id"] == qid and q.get("built_by_code") for q in cfg["questions"])


def nws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# ---------------------------------------------------------------------------- prompt parts

def passage_block(ev: dict) -> str:
    out = []
    for it in ev["items"]:
        meta = ev["documents"].get(it["doc_id"]) or {}
        head = " | ".join(x for x in (meta.get("title") or it["doc_id"], meta.get("issuer"),
                                       str(meta.get("date") or "") or None, it.get("section") or None,
                                       it["kind"]) if x)
        out.append(f"[{it['id']}] {head}\n{it['text']}")
    return "\n\n".join(out)


def answer_prompt(ev: dict, max_sentences: int, version: str = "v1", options: list | None = None) -> str:
    if version == "v2":
        rule = OPTIONS_RULE.format(options="; ".join(options)) if options else ""
        return ANSWER_TEMPLATE_V2.format(max_sentences=max_sentences, max_words=MAX_WORDS,
                                         qid=ev["question_id"], question=ev["question"],
                                         passages=passage_block(ev), options_rule=rule)
    return ANSWER_TEMPLATE.format(max_sentences=max_sentences, max_words=MAX_WORDS, qid=ev["question_id"],
                                  question=ev["question"], passages=passage_block(ev))


def check_items(answer: dict) -> list:
    items = []
    for i, s in enumerate(answer["sentences"], 1):
        items.append({"item_id": f"S{i}", "kind": "SENTENCE", "text": s["text"],
                      "evidence": s["evidence"]})
    for i, t in enumerate(answer["not_known"], 1):
        items.append({"item_id": f"N{i}", "kind": "NOT_KNOWN", "text": t, "evidence": []})
    return items


def check_prompt(ev: dict, items: list, version: str = "v1") -> str:
    lines = []
    for it in items:
        cites = f" (cites {', '.join(it['evidence'])})" if it["kind"] == "SENTENCE" else ""
        lines.append(f"{it['item_id']} [{it['kind']}]{cites}: {it['text']}")
    t = CHECK_TEMPLATE_V2 if version == "v2" else CHECK_TEMPLATE
    return t.format(rubric_version=RUBRIC_VERSION, overlay=OVERLAY,
                    qid=ev["question_id"], question=ev["question"],
                    passages=passage_block(ev), items="\n".join(lines))


def combined_evidence(ev: dict, ab: dict | None) -> dict:
    """The v2 check's passages: the question's (ids E...) and those the absence search found by
    the "not known" items' own words, renumbered A1... so a sentence can cite only the former."""
    if not ab:
        return ev
    extra = [{**it, "id": f"A{i}"} for i, it in enumerate(ab["items"], 1)]
    return {**ev, "documents": {**ab.get("documents", {}), **ev.get("documents", {})},
            "items": ev["items"] + extra}


# --------------------------------------------------------------------------------- parsing

def _json_payload(text: str):
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    # The outermost structure is whichever bracket opens first: an array of objects must not
    # be read as its first object.
    pairs = sorted((("{", "}"), ("[", "]")), key=lambda p: (t.find(p[0]) == -1, t.find(p[0])))
    for opener, closer in pairs:
        a, b = t.find(opener), t.rfind(closer)
        if a != -1 and b > a:
            try:
                return json.loads(t[a:b + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON payload")


def parse_answer(text: str, ev: dict, max_sentences: int) -> dict:
    """The answer as written, plus what the harness cut before any check: sentences beyond the
    limit, and sentences citing an id that is not in the evidence file (the §3.1 input
    contract: a claim is checked only against passages that exist)."""
    obj = _json_payload(text)
    if not isinstance(obj, dict) or not isinstance(obj.get("sentences"), list):
        raise ValueError("answer is not {sentences: [...]}")
    ids = {it["id"] for it in ev["items"]}
    sentences, precut = [], []
    for i, s in enumerate(obj["sentences"]):
        if not isinstance(s, dict) or not str(s.get("text") or "").strip():
            raise ValueError(f"sentence {i + 1} malformed")
        cites = [str(c) for c in (s.get("evidence") or [])]
        row = {"text": str(s["text"]).strip(), "evidence": cites}
        if i >= max_sentences:
            precut.append({**row, "cut_reason": f"over the {max_sentences}-sentence limit"})
        elif not cites:
            precut.append({**row, "cut_reason": "cites no passage"})
        elif any(c not in ids for c in cites):
            precut.append({**row, "cut_reason": "cites a passage id that is not in the evidence file: "
                                                + ", ".join(c for c in cites if c not in ids)})
        else:
            sentences.append(row)
    nk = [str(x).strip() for x in (obj.get("not_known") or []) if str(x).strip()]
    return {"sentences": sentences, "not_known": nk, "precut": precut}


def parse_check(text: str, items: list, version: str = "v1") -> list:
    arr = _json_payload(text)
    if not isinstance(arr, list):
        raise ValueError("check is not a JSON array")
    by_id = {str(r.get("item_id")): r for r in arr if isinstance(r, dict)}
    out = []
    for it in items:
        r = by_id.get(it["item_id"])
        if r is None or r.get("verdict") not in VERDICTS:
            out.append({"item_id": it["item_id"], "malformed": True,
                        "malformed_reason": "missing or off-vocabulary verdict"})
            continue
        dc = r.get("defect_class")
        if version == "v2" and it["kind"] == "SENTENCE" and r.get("responsive") not in RESPONSIVE:
            out.append({"item_id": it["item_id"], "malformed": True,
                        "malformed_reason": "no yes/no answer to \"does this sentence answer the question?\""})
            continue
        if r["verdict"] != "pass" and dc not in DEFECT_CLASSES:
            out.append({"item_id": it["item_id"], "malformed": True,
                        "malformed_reason": f"{r['verdict']} without a defect class from the closed set"})
            continue
        out.append({"item_id": it["item_id"], "verdict": r["verdict"],
                    "defect_class": dc if r["verdict"] != "pass" else None,
                    "support_span": r.get("support_span"), "reason": r.get("reason"),
                    "confidence": r.get("confidence"),
                    **({"responsive": r.get("responsive")} if version == "v2" else {})})
    return out


def decide(ev: dict, answer: dict, items: list, verdicts: list) -> dict:
    """Keep or cut each item. The rule is mechanical (module docstring)."""
    from kg.extraction.grounding import is_grounded   # the repo's one verbatim-match rule
    texts = {it["id"]: it["text"] for it in ev["items"]}
    vby = {v["item_id"]: v for v in verdicts}
    kept, cut, nk_kept, nk_cut = [], list(answer["precut"]), [], []
    for it in items:
        v = vby.get(it["item_id"]) or {"malformed": True, "malformed_reason": "no verdict"}
        span = v.get("support_span") or ""
        if it["kind"] == "SENTENCE":
            located = any(is_grounded(span, texts[c]) for c in it["evidence"])
            row = {"text": it["text"], "evidence": it["evidence"], "verdict": v.get("verdict"),
                   "defect_class": v.get("defect_class"), "reason": v.get("reason"),
                   "support_span": v.get("support_span"), "span_located": located,
                   **({"responsive": v["responsive"]} if "responsive" in v else {})}
            if v.get("malformed"):
                cut.append({**row, "cut_reason": f"check malformed: {v['malformed_reason']}"})
            elif v["verdict"] == "pass" and located and v.get("responsive") == "no":
                # v2: entailed but not an answer (ADDENDUM 01 step 5), cut as an unsupported
                # claim is cut. A v1 verdict has no `responsive` key and never reaches here.
                cut.append({**row, "cut_reason": "non-responsive: supported, but does not answer the question"})
            elif v["verdict"] == "pass" and located:
                kept.append(row)
            elif v["verdict"] == "pass":
                cut.append({**row, "cut_reason": "passed, but its quoted support was not found in the cited passages"})
            else:
                cut.append({**row, "cut_reason": f"{v['verdict']}: {v.get('defect_class')}"})
        else:
            row = {"text": it["text"], "verdict": v.get("verdict"), "reason": v.get("reason"),
                   "support_span": v.get("support_span"),
                   "span_located": any(is_grounded(span, t) for t in texts.values())}
            if not v.get("malformed") and v["verdict"] == "pass":
                nk_kept.append(row)
            else:
                nk_cut.append({**row, "cut_reason": (f"check malformed: {v['malformed_reason']}"
                                                     if v.get("malformed") else
                                                     f"{v['verdict']}: a passage states it")})
    return {"kept": kept, "cut": cut, "not_known_kept": nk_kept, "not_known_cut": nk_cut}


def absence_items(statements: list) -> list:
    return [{"item_id": f"N{i}", "kind": "NOT_KNOWN", "text": t, "evidence": []}
            for i, t in enumerate(statements, 1)]


def absence_input_sha(ab: dict, statements: list) -> str:
    return sha(ab["evidence_sha256"] + json.dumps(statements, ensure_ascii=False))


def apply_absence(d: dict, ab: dict, verdicts: list) -> dict:
    """A "not known" statement kept by the check survives only on an absence `pass`. On any other
    verdict, or a malformed one, it is cut, with the passage the checker quoted."""
    from kg.extraction.grounding import is_grounded
    texts = [it["text"] for it in ab["items"]]
    vby = {v["item_id"]: v for v in verdicts}
    kept, cut = [], list(d["not_known_cut"])
    for i, row in enumerate(d["not_known_kept"], 1):
        v = vby.get(f"N{i}") or {"malformed": True, "malformed_reason": "no verdict"}
        span = v.get("support_span") or ""
        row = {**row, "absence_verdict": v.get("verdict"), "absence_reason": v.get("reason"),
               "absence_span": span or None,
               "absence_span_located": any(is_grounded(span, t) for t in texts)}
        if not v.get("malformed") and v["verdict"] == "pass":
            kept.append(row)
        else:
            cut.append({**row, "cut_reason": ("absence check malformed: " + v["malformed_reason"]
                                              if v.get("malformed") else
                                              f"absence check {v['verdict']}: a passage found by the "
                                              f"statement's own words states it")})
    return {**d, "not_known_kept": kept, "not_known_cut": cut}


# ------------------------------------------------------------------------------ checkpoint

class Checkpoint:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, rec: dict) -> None:
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
        with self.lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())

    def read(self) -> list:
        if not self.path.is_file():
            return []
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]


def decided(records: list) -> dict:
    """unit_id -> the record that decides it: the first `done` attempt, else the latest."""
    out = {}
    for r in records:
        cur = out.get(r["unit_id"])
        if cur is None or (cur["status"] != "done" and (r["status"] == "done" or r["attempt"] > cur["attempt"])):
            out[r["unit_id"]] = r
    return out


def unit_id(kind: str, qid: int, input_sha: str, model: str, template_sha: str) -> str:
    return hashlib.sha1(f"{kind}|{qid}|{input_sha}|{model}|{template_sha}".encode()).hexdigest()[:16]


def _tokens(usage: dict) -> int:
    return sum(int((usage or {}).get(k, 0) or 0) for k in
               ("inputTokens", "outputTokens", "cacheCreationInputTokens", "cacheReadInputTokens"))


class StopRun(Exception):
    pass


class ScriptedFileConsumer:
    """Test double for the SIGKILL resume test (§15 item 8), selected by the environment variable
    `DCATFAQ_SCRIPTED_CONSUMER=<json spec>`. An answer prompt gets one sentence citing E1; a
    check prompt gets `pass` for every item, quoting the first 30 characters of passage E1. Each
    call id is appended to `calls_log` BEFORE answering, so a test sees every call made. Never
    selected in production."""

    def __init__(self, spec_path: str):
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.sleep_s = float(spec.get("sleep_s", 0))
        self.calls_log = Path(spec["calls_log"])
        self.model_id = spec.get("model_id", "scripted-model")

    def complete(self, prompt: str, *, call_id: str):
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        from harness.consumers import Completion
        if "\nITEMS\n" in prompt:
            e1 = prompt.split("[E1]", 1)[1].split("\n", 2)[1]
            ids = re.findall(r"^([SN]\d+) \[", prompt.split("\nITEMS\n", 1)[1], re.M)
            text = json.dumps([{"item_id": i, "verdict": "pass", "defect_class": None,
                                "support_span": e1[:30], "reason": "scripted", "confidence": 1.0}
                               for i in ids])
        else:
            text = json.dumps({"sentences": [{"text": "Scripted sentence.", "evidence": ["E1"]}],
                               "not_known": ["The sources do not state a scripted gap."]})
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 1, "outputTokens": 1})


def call(consumer, model: str, prompt: str, call_id: str) -> tuple:
    """One model call. Returns (completion or None, error). Raises StopRun on a spend refusal or
    a model substitution (the repo's STOP contract)."""
    from kg import spend
    from kg.extraction import model_stub
    try:
        comp = consumer.complete(prompt, call_id=call_id)
    except spend.SpendRefusalStop as exc:
        raise StopRun(f"spend_refusal: {exc}") from exc
    except model_stub.ModelSubstitutionError as exc:
        # Named by the exception's reason: `model_substituted` (seldon AD-035 R6), or
        # `model_side_call` under this repo's invariant 5 (task MODEL-001).
        raise StopRun(f"{exc.reason}: {exc}") from exc
    except (model_stub.ModelRateLimitError, model_stub.ModelInvocationError) as exc:
        return None, str(exc)[:500]
    if comp.model_id != model:
        raise StopRun(f"model_substituted: envelope {comp.model_id!r}, expected {model!r}")
    return comp, None


# ------------------------------------------------------------------------------------- run

class Runner:
    def __init__(self, cfg: dict, evidence_dir: Path, run_dir: Path, answer_consumer, check_consumer,
                 answer_model: str, check_model: str, workers: int, log=print):
        self.cfg, self.rc = cfg, cfg["run"]
        self.evidence_dir, self.run_dir = evidence_dir, run_dir
        self.ck = Checkpoint(run_dir / "checkpoint.jsonl")
        self.raw = run_dir / "raw"
        self.ac, self.cc = answer_consumer, check_consumer
        self.am, self.cm = answer_model, check_model
        self.workers, self.log = workers, log
        self.t0 = time.time()
        self.calls = 0
        self.last_progress = 0.0
        #: (qcfg, statements) -> absence evidence. Set by `main` for a real run (it reads both
        #: graphs); None leaves an absence file that is already on disk as the only source.
        self.absence_builder = None
        self.absence_on = bool((cfg.get("absence") or {}).get("enabled"))

    # -- evidence
    def evidence(self, qid: int) -> dict:
        p = self.evidence_dir / f"Q{qid}.json"
        if not p.is_file():
            raise SystemExit(f"FATAL: {p} missing; run scripts/dcat_faq_evidence.py first")
        ev = json.loads(p.read_text(encoding="utf-8"))
        if EV.evidence_sha(ev) != ev.get("evidence_sha256"):
            raise SystemExit(f"FATAL: {p} does not hash to its recorded evidence_sha256")
        return ev

    # -- one unit, with attempts
    def max_attempts(self, qid: int) -> int:
        if template_version(self.cfg, qid) == "v2" or qid == CONTROL_QID:
            return int((self.cfg.get("rerun") or {}).get("max_attempts", self.rc["max_attempts"]))
        return self.rc["max_attempts"]

    def _unit(self, kind: str, qid: int, input_sha: str, prompt: str, consumer, model: str,
              parse, tsha: str) -> dict:
        uid = unit_id(kind, qid, input_sha, model, tsha)
        prior = [r for r in self.ck.read() if r["unit_id"] == uid]
        done = next((r for r in prior if r["status"] == "done"), None)
        if done:
            return done
        attempt = max((r["attempt"] for r in prior), default=0)
        cap = self.max_attempts(qid)
        if attempt >= cap:
            # Every allowed attempt is spent and none parsed: report, never call again.
            return max(prior, key=lambda r: r["attempt"])
        while attempt < cap:
            attempt += 1
            if time.time() - self.t0 > self.rc["max_wall_seconds"]:
                raise StopRun(f"wall_clock: {self.rc['max_wall_seconds']} s")
            base = {"unit_id": uid, "kind": kind, "question_id": qid, "attempt": attempt,
                    "model_id": model, "input_sha256": input_sha, "template_sha256": tsha,
                    "prompt_sha256": sha(prompt), "rubric_version": RUBRIC_VERSION,
                    "overlay": OVERLAY, "run_id": RUN_ID}
            t = time.time()
            comp, err = call(consumer, model, prompt, f"dcatfaq.{uid}.{kind}.q{qid}.a{attempt}")
            self.calls += 1
            if comp is None:
                rec = {**base, "status": "error", "error": err, "tokens": 0, "usage": {}, "ts": _now()}
                self.ck.append(rec)
                continue
            self.raw.mkdir(parents=True, exist_ok=True)
            (self.raw / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {"unit_id": uid, "kind": kind, "question_id": qid, "attempt": attempt, "model_id": model,
                 "model_receipt": comp.receipt,
                 "prompt": prompt, "response_text": comp.text, "usage": comp.usage}, indent=1,
                ensure_ascii=False), encoding="utf-8")
            try:
                parsed = parse(comp.text)
                status, error = "done", None
            except (ValueError, KeyError, TypeError) as exc:
                parsed, status, error = None, "unparsed", str(exc)[:300]
            rec = {**base, "status": status, "error": error, "parsed": parsed,
                   "usage": comp.usage, "tokens": _tokens(comp.usage),
                   "wall_s": round(time.time() - t, 2), "ts": _now()}
            self.ck.append(rec)
            self.progress()
            if status == "done":
                return rec
        return rec

    def answer(self, ev: dict) -> dict:
        qid = ev["question_id"]
        v = template_version(self.cfg, qid)
        opts = ((self.cfg.get("rerun") or {}).get("options") or {}).get(qid)
        prompt = answer_prompt(ev, self.rc["max_answer_sentences"], v, opts)
        return self._unit("answer", qid, ev["evidence_sha256"], prompt, self.ac, self.am,
                          lambda t: parse_answer(t, ev, self.rc["max_answer_sentences"]),
                          ANSWER_TEMPLATE_V2_SHA if v == "v2" else ANSWER_TEMPLATE_SHA)

    def absence_v2_file(self, qid: int) -> Path:
        return self.evidence_dir / f"Q{qid}_absence_v2.json"

    def absence_v2(self, qid: int, statements: list) -> dict | None:
        """The absence passages for a v2 check, for the answer's "not known" statements as
        written (the check has not run yet). Read from disk when it is for these statements,
        else built from the graphs and written beside the v1 absence file, never over it."""
        if not statements:
            return None
        p = self.absence_v2_file(qid)
        ab = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
        if ab is None or [x["statement"] for x in ab["statements"]] != statements:
            if self.absence_builder is None:
                raise SystemExit(f"FATAL: {p} missing or stale and no graph access to rebuild it")
            qcfg = next(q for q in self.cfg["questions"] if q["id"] == qid)
            ab = self.absence_builder(qcfg, statements)
            ab["evidence_sha256"] = EV.evidence_sha(ab)
            p.write_text(json.dumps(ab, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return ab

    def check(self, ev: dict, ans_rec: dict) -> dict:
        items = check_items(ans_rec["parsed"])
        if not items:
            return {"status": "done", "parsed": [], "tokens": 0, "unit_id": None, "attempt": 0}
        qid = ev["question_id"]
        if template_version(self.cfg, qid) == "v2":
            ab = self.absence_v2(qid, ans_rec["parsed"]["not_known"])
            cev = combined_evidence(ev, ab)
            prompt = check_prompt(cev, items, "v2")
            return self._unit("check", qid, check_input_sha_v2(ans_rec["parsed"], ab), prompt, self.cc,
                              self.cm, lambda t: parse_check(t, items, "v2"), CHECK_TEMPLATE_V2_SHA)
        prompt = check_prompt(ev, items)
        return self._unit("check", qid, sha(json.dumps(ans_rec["parsed"], sort_keys=True)),
                          prompt, self.cc, self.cm, lambda t: parse_check(t, items), CHECK_TEMPLATE_SHA)

    def control(self) -> dict:
        """The positive control (methodology 7.6) for the v2 check: planted sentences on frozen
        evidence, one v2 check call, and the verdict compared with what each plant expects.
        Returns the comparison; `passed` False means no v2 verdict may be used."""
        cc = (self.cfg.get("rerun") or {})["control"]
        path = REPO / cc["evidence"]
        ev = json.loads(path.read_text(encoding="utf-8"))
        if EV.evidence_sha(ev) != ev.get("evidence_sha256"):
            raise SystemExit(f"FATAL: {path} does not hash to its recorded evidence_sha256")
        answer = parse_answer(json.dumps({"sentences": [{"text": x["text"], "evidence": x["evidence"]}
                                                        for x in cc["sentences"]], "not_known": []}),
                              ev, len(cc["sentences"]))
        if answer["precut"]:
            raise SystemExit(f"FATAL: a control sentence cites an id not in {path}: {answer['precut']}")
        items = check_items(answer)
        rec = self._unit("control", CONTROL_QID, sha(ev["evidence_sha256"] + json.dumps(cc, sort_keys=True)),
                         check_prompt(ev, items, "v2"), self.cc, self.cm,
                         lambda t: parse_check(t, items, "v2"), CHECK_TEMPLATE_V2_SHA)
        if rec["status"] != "done":
            return {"passed": False, "unit_id": rec["unit_id"], "reason": f"control call {rec['status']}"}
        d = decide(ev, answer, items, rec["parsed"])
        rows = []
        for i, x in enumerate(cc["sentences"]):
            kept = next((r for r in d["kept"] if r["text"] == x["text"]), None)
            cut = next((r for r in d["cut"] if r["text"] == x["text"]), None)
            got = ("kept" if kept else "cut_non_responsive"
                   if cut and cut["cut_reason"].startswith("non-responsive") else "cut_unsupported")
            rows.append({"item_id": f"S{i + 1}", "expect": x["expect"], "got": got,
                         "verdict": (kept or cut or {}).get("verdict"),
                         "responsive": (kept or cut or {}).get("responsive"),
                         "reason": (kept or cut or {}).get("reason")})
        return {"passed": all(r["expect"] == r["got"] for r in rows), "unit_id": rec["unit_id"],
                "tokens": rec["tokens"], "check_template_sha256": CHECK_TEMPLATE_V2_SHA,
                "model_id": self.cm, "evidence": cc["evidence"], "rows": rows}

    def absence_file(self, qid: int) -> Path:
        return self.evidence_dir / f"Q{qid}_absence.json"

    def absence(self, qid: int, statements: list) -> dict:
        """The absence check: the "not known" statements the check kept, read against passages
        found by their own words (`dcat_faq_evidence.absence_evidence`). Same template and
        model as the check, so the only thing that differs is the passages."""
        p = self.absence_file(qid)
        ab = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
        if ab is None or [x["statement"] for x in ab["statements"]] != statements:
            if self.absence_builder is None:
                raise SystemExit(f"FATAL: {p} missing or stale and no graph access to rebuild it")
            qcfg = next(q for q in self.cfg["questions"] if q["id"] == qid)
            ab = self.absence_builder(qcfg, statements)
            ab["evidence_sha256"] = EV.evidence_sha(ab)
            p.write_text(json.dumps(ab, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        items = absence_items(statements)
        prompt = check_prompt(ab, items)
        return self._unit("absence", qid, absence_input_sha(ab, statements), prompt, self.cc, self.cm,
                          lambda t: parse_check(t, items), CHECK_TEMPLATE_SHA)

    def question(self, qid: int, ev: dict | None = None) -> dict:
        ev = ev or self.evidence(qid)
        a = self.answer(ev)
        if a["status"] != "done":
            return {"question_id": qid, "status": "unanswered", "answer_unit": a["unit_id"]}
        c = self.check(ev, a)
        if c["status"] != "done":
            return {"question_id": qid, "status": "unchecked", "answer_unit": a["unit_id"],
                    "check_unit": c["unit_id"]}
        if self.absence_on and template_version(self.cfg, qid) == "v1":
            items = check_items(a["parsed"])
            nk = [r["text"] for r in decide(ev, a["parsed"], items, c["parsed"])["not_known_kept"]]
            if nk:
                b = self.absence(qid, nk)
                if b["status"] != "done":
                    return {"question_id": qid, "status": "unchecked", "answer_unit": a["unit_id"],
                            "check_unit": c.get("unit_id"), "absence_unit": b["unit_id"]}
        return {"question_id": qid, "status": "done", "answer_unit": a["unit_id"],
                "check_unit": c.get("unit_id")}

    def progress(self, force: bool = False) -> None:
        now = time.time()
        recs = self.ck.read()
        done = sum(1 for r in decided(recs).values() if r["status"] == "done")
        if not force and now - self.last_progress < self.rc["progress_every_seconds"] \
                and done % self.rc["progress_every_units"]:
            return
        self.last_progress = now
        tok = sum(r.get("tokens", 0) for r in recs)
        fails = sum(1 for r in recs if r["status"] != "done")
        total = sum(0 if is_code_built(self.cfg, q["id"]) else
                    2 if template_version(self.cfg, q["id"]) == "v2" else
                    (3 if self.absence_on else 2) for q in self.cfg["questions"]) \
            + (1 if (self.cfg.get("rerun") or {}).get("control") else 0)
        el = now - self.t0
        rate = done / el if el > 0 and done else 0
        eta = (total - done) / rate if rate else None
        self.log(f"[faq +{el:7.1f}s] units done {done}/{total} calls this run {self.calls} "
                 f"tokens so far {tok:,} failures so far {fails} "
                 f"eta {'?' if eta is None else f'{eta:.0f}s'}")

    def run_pool(self, qids: list) -> list:
        out = []
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(self.question, q): q for q in qids}
            for f in as_completed(futs):
                out.append(f.result())
        return out

    def gaps(self, qids: list) -> list:
        g = []
        for q in qids:
            r = assemble_one(self, q)
            for n, row in enumerate(r.get("not_known_kept", []), 1):
                g.append({"question_id": q, "n": n, "text": row["text"]})
        return g

    def rerun(self, control_out: Path) -> int:
        """ADDENDUM 01 step 5: the positive control first (it is also the pilot: its measured
        tokens project the rest against the ceiling), then the v2 questions. A failed control
        stops the run before any v2 question is asked."""
        rr = self.cfg["rerun"]
        try:
            res = self.control()
            control_out.parent.mkdir(parents=True, exist_ok=True)
            control_out.write_text(json.dumps({"generated_by": GENERATOR, "generated_at": _now(), **res},
                                              indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            self.log(f"CONTROL: {'PASS' if res['passed'] else 'FAIL'} "
                     + json.dumps(res.get("rows") or res.get("reason")))
            if not res["passed"]:
                self.log("STOP: the positive control failed; no v2 verdict is used and no v2 question runs")
                return 3
            per = res.get("tokens") or 0
            calls = 2 * len(rr["questions"])
            self.log(f"PILOT: the control call measured {per:,} tokens; projected for {calls} more calls "
                     f"at that rate: {per * calls:,}, ceiling {rr['ceiling_tokens']:,}")
            if per * (calls + 1) > rr["ceiling_tokens"]:
                self.log("STOP: the pilot projects past the declared ceiling; nothing else runs")
                return 3
            out = self.run_pool(rr["questions"])
            bad = [o for o in out if o["status"] != "done"]
            if bad:
                self.log(f"STOP: not answered and checked within the allowed attempts: {bad}")
                return 3
        except StopRun as exc:
            self.progress(force=True)
            self.log(f"STOP: {exc}")
            return 3
        self.progress(force=True)
        return 0

    def run(self) -> int:
        qs = [q["id"] for q in self.cfg["questions"] if not q.get("gaps_from_questions")]
        gq = [q for q in self.cfg["questions"] if q.get("gaps_from_questions") and not q.get("built_by_code")]
        pilot = [q for q in self.rc["pilot_questions"] if q in qs]
        try:
            for q in pilot:
                self.question(q)
            recs = [r for r in self.ck.read() if r["status"] == "done" and r["question_id"] in pilot]
            if recs:
                per = sum(r["tokens"] for r in recs) / len(recs)
                calls = (3 if self.absence_on else 2) * (len(qs) + len(gq))
                self.log(f"PILOT: {len(recs)} calls on question(s) {pilot}, {per:,.0f} tokens per call "
                         f"(measured); projected for {calls} calls: {per * calls:,.0f} tokens, "
                         f"ceiling {self.rc['ceiling_tokens']:,}")
                if per * calls > self.rc["ceiling_tokens"]:
                    self.log("STOP: the pilot projects past the declared ceiling; nothing else runs")
                    return 3
            self.run_pool([q for q in qs if q not in pilot])
            for g in gq:
                ev = EV.build_gaps_question(g, self.cfg, self.gaps(g["gaps_from_questions"]),
                                            json.loads((self.evidence_dir / "catalog_entries.json")
                                                       .read_text(encoding="utf-8"))["items"])
                ev["evidence_sha256"] = EV.evidence_sha(ev)
                (self.evidence_dir / f"Q{g['id']}.json").write_text(
                    json.dumps(ev, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
                self.question(g["id"], ev)
        except StopRun as exc:
            self.progress(force=True)
            self.log(f"STOP: {exc}")
            return 3
        self.progress(force=True)
        return 0


# -------------------------------------------------------------------------------- assemble

def check_input_sha_v2(parsed: dict, ab: dict | None) -> str:
    return sha(json.dumps(parsed, sort_keys=True) + ((ab or {}).get("evidence_sha256") or ""))


def assemble_one(runner: Runner, qid: int) -> dict:
    if is_code_built(runner.cfg, qid):
        q = next(x for x in runner.cfg["questions"] if x["id"] == qid)
        return {"question_id": qid, "question": q["text"], "status": "done", "built_by_code": True,
                "kept": [], "cut": [], "not_known_kept": [], "not_known_cut": []}
    if template_version(runner.cfg, qid) == "v2":
        return assemble_one_v2(runner, qid)
    ev = runner.evidence(qid)
    recs = runner.ck.read()
    a_id = unit_id("answer", qid, ev["evidence_sha256"], runner.am, ANSWER_TEMPLATE_SHA)
    a = decided(recs).get(a_id)
    if not a or a["status"] != "done":
        return {"question_id": qid, "question": ev["question"], "status": "unanswered",
                "kept": [], "cut": [], "not_known_kept": [], "not_known_cut": []}
    items = check_items(a["parsed"])
    if items:
        c_id = unit_id("check", qid, sha(json.dumps(a["parsed"], sort_keys=True)), runner.cm,
                       CHECK_TEMPLATE_SHA)
        c = decided(recs).get(c_id)
        if not c or c["status"] != "done":
            return {"question_id": qid, "question": ev["question"], "status": "unchecked",
                    "kept": [], "cut": [], "not_known_kept": [], "not_known_cut": []}
        verdicts, c_tokens = c["parsed"], c["tokens"]
    else:
        verdicts, c_tokens, c_id = [], 0, None
    d = decide(ev, a["parsed"], items, verdicts)
    b_id, b_tokens = None, 0
    if runner.absence_on and d["not_known_kept"]:
        statements = [r["text"] for r in d["not_known_kept"]]
        p = runner.absence_file(qid)
        ab = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
        b = None
        if ab and [x["statement"] for x in ab["statements"]] == statements:
            b_id = unit_id("absence", qid, absence_input_sha(ab, statements), runner.cm, CHECK_TEMPLATE_SHA)
            b = decided(recs).get(b_id)
        if not b or b["status"] != "done":
            return {"question_id": qid, "question": ev["question"], "status": "unchecked",
                    "kept": [], "cut": [], "not_known_kept": [], "not_known_cut": []}
        d = apply_absence(d, ab, b["parsed"])
        b_tokens = b["tokens"]
    return {"question_id": qid, "question": ev["question"], "status": "done",
            "answer_model": runner.am, "check_model": runner.cm, "rubric_version": RUBRIC_VERSION,
            "overlay": OVERLAY, "answer_unit": a_id, "check_unit": c_id, "absence_unit": b_id,
            "evidence_sha256": ev["evidence_sha256"],
            "tokens": {"answer": a["tokens"], "check": c_tokens, "absence": b_tokens}, **d}


def assemble_one_v2(runner: Runner, qid: int) -> dict:
    ev = runner.evidence(qid)
    recs = decided(runner.ck.read())
    empty = {"question_id": qid, "question": ev["question"], "kept": [], "cut": [],
             "not_known_kept": [], "not_known_cut": [], "template": "v2"}
    a_id = unit_id("answer", qid, ev["evidence_sha256"], runner.am, ANSWER_TEMPLATE_V2_SHA)
    a = recs.get(a_id)
    if not a or a["status"] != "done":
        return {**empty, "status": "unanswered"}
    items = check_items(a["parsed"])
    p = runner.absence_v2_file(qid)
    ab = json.loads(p.read_text(encoding="utf-8")) if a["parsed"]["not_known"] and p.is_file() else None
    if ab and [x["statement"] for x in ab["statements"]] != a["parsed"]["not_known"]:
        ab = None
    if a["parsed"]["not_known"] and ab is None:
        return {**empty, "status": "unchecked"}
    c_id = unit_id("check", qid, check_input_sha_v2(a["parsed"], ab), runner.cm, CHECK_TEMPLATE_V2_SHA) \
        if items else None
    c = recs.get(c_id) if c_id else {"parsed": [], "tokens": 0}
    if not c or (c_id and c["status"] != "done"):
        return {**empty, "status": "unchecked"}
    d = decide(combined_evidence(ev, ab), a["parsed"], items, c["parsed"])
    return {**empty, "status": "done", "answer_model": runner.am, "check_model": runner.cm,
            "rubric_version": RUBRIC_VERSION, "overlay": OVERLAY, "answer_unit": a_id,
            "check_unit": c_id, "absence_unit": None,
            "absence": "folded into the check (v2)", "absence_evidence_sha256": (ab or {}).get("evidence_sha256"),
            "evidence_sha256": ev["evidence_sha256"],
            "tokens": {"answer": a["tokens"], "check": c["tokens"], "absence": 0}, **d}


def assemble(runner: Runner) -> dict:
    out = {"generated_by": GENERATOR, "task": TASK, "generated_at": _now(), "questions": []}
    for q in runner.cfg["questions"]:
        p = runner.evidence_dir / f"Q{q['id']}.json"
        if p.is_file():
            out["questions"].append(assemble_one(runner, q["id"]))
    recs = runner.ck.read()
    out["spend"] = {"calls": len(recs), "done": sum(1 for r in recs if r["status"] == "done"),
                    "tokens": sum(r.get("tokens", 0) for r in recs)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--rerun", action="store_true", help="ADDENDUM 01: the control, then the v2 questions")
    g.add_argument("--assemble", action="store_true")
    ap.add_argument("--evidence-dir", default=None, help="test seam (default: reports/dcat_us_3_faq/evidence)")
    ap.add_argument("--run-dir", default=None, help="test seam (default: reports/dcat_us_3_faq/run)")
    ap.add_argument("--answers", default=None, help="test seam (default: reports/dcat_us_3_faq/answers.json)")
    ap.add_argument("--config", default=None, help="test seam (default: faq_config.yaml)")
    ap.add_argument("--progress-log", default=None, help="test seam (default: logs/2026-10-05_DCAT-003_faq_progress.log)")
    ap.add_argument("--control-out", default=None, help="test seam (default: reports/dcat_us_3_faq/control/control_result.json)")
    a = ap.parse_args(argv)

    cfg = EV.load_config(Path(a.config) if a.config else EV.CONFIG)
    rc = cfg["run"]
    evidence_dir = Path(a.evidence_dir) if a.evidence_dir else EV.EVIDENCE_DIR
    run_dir = Path(a.run_dir) if a.run_dir else RUN_DIR
    answers = Path(a.answers) if a.answers else ANSWERS
    plog = Path(a.progress_log) if a.progress_log else PROGRESS_LOG
    plog.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with plog.open("a", encoding="utf-8") as fh:
            fh.write(f"{_now()} {msg}\n")

    scripted = os.environ.get("DCATFAQ_SCRIPTED_CONSUMER")
    if scripted:
        ac = cc = ScriptedFileConsumer(scripted)
        am = cm = ac.model_id
    else:
        from kg.extraction import model_stub
        mc = model_stub.load_model_config()
        am, cm = mc[rc["answer_model_key"]], mc[rc["validator_model_key"]]
        ac = cc = None

    if a.dry_run:
        ev = json.loads((evidence_dir / "Q1.json").read_text(encoding="utf-8"))
        p = answer_prompt(ev, rc["max_answer_sentences"])
        print(p[:3000] + "\n...")
        sizes = {}
        for q in cfg["questions"]:
            f = evidence_dir / f"Q{q['id']}.json"
            if f.is_file():
                e = json.loads(f.read_text(encoding="utf-8"))
                sizes[q["id"]] = len(answer_prompt(e, rc["max_answer_sentences"]))
        print(json.dumps({"answer_model": am, "check_model": cm, "answer_prompt_chars": sizes,
                          "ceiling_tokens": rc["ceiling_tokens"]}, indent=1))
        return 0

    if not scripted and (a.run or a.rerun):
        from kg import spend
        from kg.extraction import model_stub
        from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
        model_stub.guard_no_api_key()
        led = spend.default_ledger()
        run_id, ceiling, task = ((cfg["rerun"]["run_id"], cfg["rerun"]["ceiling_tokens"], ADDENDUM_TASK)
                                 if a.rerun else (RUN_ID, rc["ceiling_tokens"], TASK))
        st = led.status().get("runs", {}).get(run_id)
        if st is None or int(st.get("ceiling_tokens") or 0) != ceiling:
            led.declare(run_id, ceiling, declared_by=f"{GENERATOR} ({task})",
                        call_class=rc["call_class"], **({"supersede": True} if st else {}))
        spend.set_current_run(run_id)
        # Each consumer launches the ROLE behind its model_config key (seldon AD-035 R4);
        # `am`/`cm` are that role's lock id, which every record names.
        ac = ClaudeCLIConsumer(ConsumerConfig(role=model_stub.role_for_model(am, mc), provider=PROVIDER,
                                              timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"]))
        cc = ClaudeCLIConsumer(ConsumerConfig(role=model_stub.role_for_model(cm, mc), provider=PROVIDER,
                                              timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"]))

    runner = Runner(cfg, evidence_dir, run_dir, ac, cc, am, cm, rc["workers"], log)
    if (a.run or a.rerun) and runner.absence_on and not scripted:
        drv = EV.driver()
        meta = EV.doc_meta(drv, cfg)
        substrate_dir = REPO / cfg["graphs"]["substrate_dir"]
        runner.absence_builder = lambda qcfg, st: EV.absence_evidence(qcfg, cfg, drv, meta, st, substrate_dir)
    rc_code = 0
    if a.run:
        rc_code = runner.run()
    elif a.rerun:
        rc_code = runner.rerun(Path(a.control_out) if a.control_out else CONTROL_OUT)
    out = assemble(runner)
    answers.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    log(f"wrote {answers}: " + json.dumps({q["question_id"]: (q["status"], len(q["kept"]), len(q["cut"]))
                                           for q in out["questions"]}))
    return rc_code


if __name__ == "__main__":
    raise SystemExit(main())
