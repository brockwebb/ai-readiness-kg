#!/usr/bin/env python3
"""The concise report's model calls: write, join, control, check, revise, read. **Model spend,
bounded.**

`cc_tasks/2026-10-07_concise_report_prose.md` decisions 1 to 6, implementing DN-013-R5 (the
report written as prose by a model, then every claim checked against the evidence map) and R6
(the prose gate, `scripts/concise_report_gate.py`). The order is the task's SEQUENCING line:

1. **Inputs** (decision 1). `docs/evidence/FROZEN.md` names the composite; the claims file must
   name the same one as its cycle of record, and must not name another cycle in any claim's
   text. Either failing is a stop before any call.
2. **Write** (decision 3). One call per section, in order, given that section's claims with
   their evidence lines, the section's framing context, and the previous section's last
   paragraph. A sentence that states a fact ends with `[c:<claim id>]`.
3. **Joins.** One call over the whole draft rewrites the opening paragraph of sections 2 to 6.
   Code keeps a rewrite only when its claim markers and its digit strings are exactly the
   paragraph's own, so a join adds no claim and no number; the claim check then reads it.
4. **Control** (decision 4; DCAT-003 ADDENDUM 01 item 5 precedent). One known-false sentence
   (`report_config.yaml` `controls`) planted after each section's middle sentence; the checker
   must label every plant `unsupported`. One miss stops the run before the real check.
5. **Claim check.** One call per section, a model of a different family from the writer's,
   seeing only the section's sentences (markers stripped) and its claims, labels every sentence
   `supported` (with claim ids), `unsupported` or `no factual content`. An unsupported sentence
   is cut, never reworded. The digit check (code) then cuts a sentence any digit string of which
   is not a value of a claim it cites.
6. **Prose gate** (decision 5), by code, then **one revision round**: every section with a gate
   failure, a repetition warning or a cut goes back to its writer once with the list; the
   revised draft is joined, checked and gated again.
7. **Fresh reader** (decision 6). A third model, launched by the same choke point from an empty
   directory with no project context, reads the built report alone and answers three
   questions; code grades the answers by rules `report_config.yaml` fixed before it ran. A
   section behind a wrong answer goes back once (rewrite, check, cut), and the reader reads
   again. Both rounds are recorded verbatim.

**Prior art.** Attribution as AIS defines it (Rashkin et al. 2021); per-claim support checking
(FActScore, Min et al. 2023); planted positive controls (this repository's methodology 7.5 and
7.6; DCAT-003 ADDENDUM 01 item 5); topic position and stress position (Gopen and Swan 1990);
Coh-Metrix and TAACO for the reported cohesion measures. The machinery is DCAT-003's
(`scripts/dcat_faq_run.py`), imported, not copied: the checkpoint, the unit key, the call and its
STOP contract, the JSON reader.

**Checkpoint** (`~/GitHub/CLAUDE.md` §15): unit = one call; key = sha1(kind | section | input
sha256 | model | template sha256), so a changed draft, prompt or model is a new unit and a
stale result is never reused; `reports/concise/run/checkpoint.jsonl`, appended and fsynced,
every prompt and response beside it in `run/raw/`. Re-running `--run` is the resume. Pilot: the
first write's measured tokens project `run.expected_calls` against the ceiling before the
second call. Ceilings: the run's declared ledger ceiling (`run.ceiling_tokens`, enforced by the
ledger before each dispatch) and `run.max_wall_seconds`. Progress every 60 s or every 2 units to
stdout and `logs/2026-10-11_concise_report_progress.log`.

    /opt/anaconda3/bin/python3 scripts/concise_report_run.py --dry-run
    /opt/anaconda3/bin/python3 scripts/concise_report_run.py --run
    /opt/anaconda3/bin/python3 scripts/concise_report_build.py      # no call
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

import concise_report_gate as G  # noqa: E402
import dcat_faq_run as FR  # noqa: E402

TASK = "cc_tasks/2026-10-07_concise_report_prose.md"
GENERATOR = "scripts/concise_report_run.py"
OUT = REPO / "reports" / "concise"
CONFIG = OUT / "report_config.yaml"
RUN_DIR = OUT / "run"
PIPELINE = "pipeline.json"
PROGRESS_LOG = REPO / "logs" / "2026-10-11_concise_report_progress.log"
LABELS = ("supported", "unsupported", "no_factual_content")

REGISTER = """REGISTER
- Technical and readable. The reader is a federal statistician or a manager at a statistical agency: expert in statistics, not in web crawling or AI.
- Each paragraph carries one thought, stated in its first sentence (the topic sentence); the rest of the paragraph develops it.
- In each sentence, put what the reader already knows first and what is new last, where the stress falls (Gopen and Swan, "The Science of Scientific Writing", 1990).
- Wherever the logic turns (a contrast, a cause, a consequence, an example), say so with a connective word: but, so, because, therefore, for example, however.
- Write whole sentences with a finite verb. Do not follow a long sentence with a short fragment or a short qualifying sentence (for example "Not a browser." or "Only the public pages."); fold the qualification into the sentence it qualifies. This pattern is measured and a section that repeats it fails.
- Vary sentence length naturally. Do not repeat a phrase you have already used; find the plain word for each thing and use it once where once is enough.
- Never use the em dash or the en dash. Never use these words: load-bearing, load bearing, hallucinate (or any form of it; say confabulate), delve, testament. Do not cite Gartner.
- Plain names, no codes. Name a statistical body by its name (the NAMES table gives it), never by a code such as CENSUS or BLS. Name a check by what it tests (for example "the check for a machine-readable licence"), never by a letter-and-number code such as D1 or B2. Do not use task codes, decision numbers, file names, file paths, field names in backticks, or words like harness, pipeline, record node, leg, route, cycle id; call the measuring client "the scanner". The one identifier you may write is the name of the measurement cycle, scan_2026-10-07_composite_d, at most once in the whole report, where the section says what was measured.
- Do not use Markdown formatting inside sentences: no bold, no italics, no backticks, no bullet lists."""

FACTS = """FACTS
- Every fact you state must come from the CLAIMS below. Do not use anything you know from elsewhere, even if you are sure it is true. FRAMING text, if any, tells you what the work is for; it is not a source of facts, and a fact taken from it that no claim states will be cut.
- A sentence that states a fact ends with the ids of the claims that support every part of it, written as [c:CL-035] or [c:CL-035, CL-036], placed before the final full stop. A sentence with no fact in it (a transition, a statement of what the section does) has no marker.
- Write every number exactly as a claim states it, in digits, with its thousands separator (1,055, not 1055 or one thousand and fifty-five). Do not compute a new number (no sums, differences, percentages or ratios that no claim states). A number that is not in a claim the sentence cites will be cut.
- Do not overstate. A claim that says "at most", "a bound, not a value", "notional", "not established" or "candidate" keeps that qualification in your sentence.
- A sentence that the claims do not support will be cut, not repaired, and the argument will have a hole where it was."""

OUTPUT = """Return ONLY a JSON object, with no prose before or after it and no code fence:
{"paragraphs": [["first sentence of paragraph one [c:CL-001].", "second sentence."], ["first sentence of paragraph two."]]}
Each paragraph is a list of its sentences, in order; each sentence is one string."""

WRITE_TEMPLATE = """TASK: WRITE ONE SECTION

You are writing one section of a short technical report: "{title}". The report is about an AI-readiness framework for federal statistical publishers, and one measurement made under it. It argues in this order: (1) what the framework is for; (2) what was measured, on whom, when and how; (3) and (4) what was found, strongest evidence first; (5) what the measurement cannot say; (6) what an agency can do, and what is measured next. The whole report is three to five pages, so a section is two to four paragraphs.

SECTION {sid} of 6: {section_title}
WHAT THIS SECTION MUST DO: {job}

{previous}

{register}

{facts}

{output}

NAMES (a code in a claim, and the name to write instead)
{names}

CLAIMS (the only source of facts; each with its status and the evidence lines behind it)
{claims}

{framing}"""

JOIN_TEMPLATE = """TASK: REWRITE THE JOINS

Below is a draft report in six sections. Each section was written separately, so the joins between them are rough. Rewrite the OPENING PARAGRAPH of sections 2, 3, 4, 5 and 6 so that each section's opening carries the reader on from the end of the section before it.

RULES
1. Change only the opening paragraphs of sections 2 to 6. Do not touch any other paragraph.
2. Add no fact and drop no fact. Every sentence's markers, written like [c:CL-035], stay exactly as they are, on the sentence that carries that fact; every number stays exactly as written. A rewrite that adds, drops or moves a marker or changes a number is discarded.
3. You may reorder the sentences of an opening paragraph, rephrase them, and add or reword a connective or a short linking clause that states no fact.
4. Keep the register: technical and readable; one thought per paragraph, in its first sentence; known information before new; no em dash or en dash; no fragments after long sentences; none of the words load-bearing, hallucinate, delve, testament.
5. If an opening already joins well, return it unchanged.

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"2": ["sentence one of section 2's opening paragraph [c:CL-034].", "sentence two."], "3": [...], "4": [...], "5": [...], "6": [...]}}

DRAFT
{draft}"""

CHECK_TEMPLATE = """TASK: CHECK EACH SENTENCE AGAINST THE CLAIMS

You are an adversarial fact checker. Your job is to find every sentence below that says something the CLAIMS do not support. Do not pass a sentence to be agreeable and do not fail one to look diligent. A sentence may read as confident or well written; that is evidence about its writer, not about the claims.

Label every sentence with exactly one of:
- "supported": every factual part of the sentence (each number, each name, each count, each comparison, each cause, each "most", "all", "only" or "none") is stated by one or more of the claims, or follows from them directly with no new number. Give the ids of the claims that together support it.
- "unsupported": any factual part is not stated by the claims, contradicts them, changes a number, drops a qualification a claim carries ("at most", "a bound", "notional", "not established", "candidate"), or states a number no claim states. Say which part, in the reason.
- "no_factual_content": the sentence states nothing that could be true or false about the world: a transition, a statement of what the section will do, a definition of a word the report uses.

The NAMES table maps a code in a claim to the name a sentence uses; a sentence that uses the name is read as if it used the code. A sentence that names a statistical body is checked against the claims for that body.

Return ONLY a JSON array, one object per sentence, in order, with no prose before or after it and no code fence:
[{{"sentence_id": "S1", "label": "supported", "claim_ids": ["CL-035"], "reason": "one short sentence"}}]

NAMES
{names}

CLAIMS
{claims}

SENTENCES
{sentences}"""

REVISE_TEMPLATE = """TASK: REVISE ONE SECTION

You wrote section {sid} of 6, "{section_title}", of the report "{title}". It was checked, and it comes back to you once with the notes below. Rewrite the whole section so that the notes no longer apply, keeping its argument and keeping every fact you can keep under the rules.

WHAT THIS SECTION MUST DO: {job}

NOTES
{notes}

SENTENCES ALREADY CUT (a checker found them unsupported, or a number in them was not in a claim they cite). Do not state these facts again in any wording; the claims do not support them.
{cuts}

THE SECTION AS IT STANDS (markers in place)
{current}

{register}

{facts}

{output}

NAMES (a code in a claim, and the name to write instead)
{names}

CLAIMS (the only source of facts)
{claims}"""

READER_TEMPLATE = """TASK: READ AND ANSWER

Below is a short report. Read it, and answer three questions using only what the report says. Do not use anything you know from elsewhere.

1. {q1}
2. {q2}
3. {q3}

Return ONLY a JSON object, with no prose before or after it and no code fence:
{{"q1": "your answer in one or two sentences", "q2": "your answer in one sentence", "q3": "your answer in one or two sentences"}}

REPORT
{report}"""

TEMPLATES = {"write": WRITE_TEMPLATE, "join": JOIN_TEMPLATE, "control": CHECK_TEMPLATE, "check": CHECK_TEMPLATE,
             "revise": REVISE_TEMPLATE, "fix": REVISE_TEMPLATE, "reader": READER_TEMPLATE}
TEMPLATE_SHA = {k: FR.sha(v) for k, v in TEMPLATES.items()}


# ------------------------------------------------------------------------------ inputs

def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def frozen_composite(path: Path) -> str:
    m = re.search(r"\|\s*Composite\s*\|\s*`([^`]+)`", path.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"FATAL: {path} names no composite")
    return m.group(1)


def load_claims(cfg: dict) -> dict:
    """Decision 1's stop condition, then id -> claim. The claims file must cite the composite
    FROZEN.md names as its cycle of record, and no claim's text may name another cycle."""
    composite = frozen_composite(REPO / cfg["inputs"]["frozen"])
    doc = yaml.safe_load((REPO / cfg["inputs"]["claims"]).read_text(encoding="utf-8"))
    if doc.get("cycle_of_record") != composite:
        raise SystemExit(f"FATAL: claims cite {doc.get('cycle_of_record')!r}, FROZEN.md names {composite!r}")
    other = sorted({c["id"] for c in doc["claims"]
                    for cyc in re.findall(r"scan_\d{4}-\d{2}-\d{2}_[a-z0-9_]+", c["text"]) if cyc != composite})
    if other:
        raise SystemExit(f"FATAL: claims whose text names a cycle other than {composite}: {other}")
    return {c["id"]: c for c in doc["claims"]}


def load_names(cfg: dict) -> dict:
    """code -> plain name: body codes from the scan frame, indicator codes from the record."""
    t = json.loads((REPO / cfg["inputs"]["body_names"]).read_text(encoding="utf-8"))
    names = {}
    for h in t["hosts"]:
        if h.get("agency") and h.get("agency_name"):
            names[h["agency"]] = h["agency_name"]
    rec = json.loads((REPO / cfg["inputs"]["framework_record"]).read_text(encoding="utf-8"))
    for n in rec["nodes"]:
        if "AssessmentIndicator" in n["labels"]:
            p = n["properties"]
            names[p["code"]] = f"the check for {p['construct'].lower()} ({p['indicator']})"
    return names


def context_text(cfg: dict, key: str) -> str:
    c = cfg["inputs"]["context"][key]
    lines = (REPO / c["path"]).read_text(encoding="utf-8").splitlines()
    a, b = c["lines"]
    return "\n".join(lines[a - 1:b]).strip()


def claim_block(ids: list, claims: dict) -> str:
    """Each claim with its status, text, note and evidence lines (where, quote, note, title);
    locators are repository paths and stay out of a prompt for prose."""
    out = []
    for i in ids:
        c = claims[i]
        lines = [f"[{i}] ({c['status']}) {' '.join(c['text'].split())}"]
        if c.get("note"):
            lines.append(f"    note: {' '.join(str(c['note']).split())}")
        for e in c.get("evidence") or []:
            parts = [str(e[k]) for k in ("author", "year", "title", "where") if e.get(k)]
            if e.get("quote"):
                parts.append(f'quote: "{e["quote"]}"')
            if e.get("note"):
                parts.append(f"note: {e['note']}")
            if parts and e.get("kind") in ("document", "citation", "indicator", "finding"):
                lines.append("    evidence: " + " | ".join(" ".join(p.split()) for p in parts))
        out.append("\n".join(lines))
    return "\n\n".join(out)


def names_block(ids: list, claims: dict, names: dict) -> str:
    text = " ".join(claims[i]["text"] for i in ids)
    used = [k for k in names if re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", text)]
    return "\n".join(f"{k}: {names[k]}" for k in sorted(used)) or "(none)"


# ------------------------------------------------------------------------------ drafts

def flat(paragraphs: list) -> list:
    return [s for p in paragraphs for s in p]


def para_text(p: list) -> str:
    return " ".join(p)


def draft_text(sections: dict, cfg: dict, markers: bool = True) -> str:
    out = []
    for s in cfg["sections"]:
        out.append(f"## {s['id']}. {s['title']}")
        for p in sections[s["id"]]:
            out.append(para_text(p) if markers else " ".join(G.strip_markers(x) for x in p))
    return "\n\n".join(out)


def parse_paragraphs(text: str) -> list:
    obj = FR._json_payload(text)
    paras = obj.get("paragraphs") if isinstance(obj, dict) else None
    if not isinstance(paras, list) or not paras:
        raise ValueError("no paragraphs list")
    out = []
    for p in paras:
        if not isinstance(p, list) or not all(isinstance(s, str) and s.strip() for s in p):
            raise ValueError("a paragraph is not a list of sentences")
        out.append([" ".join(s.split()) for s in p])
    return out


def parse_joins(text: str) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict):
        raise ValueError("joins are not an object")
    out = {}
    for k, v in obj.items():
        if not (str(k).isdigit() and isinstance(v, list) and all(isinstance(s, str) and s.strip() for s in v)):
            raise ValueError(f"join {k!r} is not a list of sentences")
        # String keys, as JSON keeps them: a result read back from the checkpoint is the same
        # object as the one parsed live, so a resumed run applies the same joins.
        out[str(int(k))] = [" ".join(s.split()) for s in v]
    return out


def parse_labels(text: str, n: int) -> list:
    arr = FR._json_payload(text)
    if not isinstance(arr, list):
        raise ValueError("labels are not an array")
    by = {}
    for x in arr:
        sid = str(x.get("sentence_id", ""))
        lab = str(x.get("label", "")).strip().lower().replace(" ", "_")
        if lab not in LABELS:
            raise ValueError(f"label {lab!r} for {sid}")
        by[sid] = {"label": lab, "claim_ids": [str(i).upper() for i in x.get("claim_ids") or []],
                   "reason": str(x.get("reason") or "")}
    missing = [f"S{i}" for i in range(1, n + 1) if f"S{i}" not in by]
    if missing:
        raise ValueError(f"no label for {missing}")
    return [by[f"S{i}"] for i in range(1, n + 1)]


def parse_reader(text: str) -> dict:
    obj = FR._json_payload(text)
    if not isinstance(obj, dict) or not all(isinstance(obj.get(k), str) for k in ("q1", "q2", "q3")):
        raise ValueError("reader answer lacks q1, q2 or q3")
    return {k: obj[k] for k in ("q1", "q2", "q3")}


def guard_join(old: list, new: list) -> str | None:
    """None when the rewrite carries exactly the old paragraph's markers and digit strings."""
    om = Counter(i for s in old for i in G.marker_ids(s))
    nm = Counter(i for s in new for i in G.marker_ids(s))
    if om != nm:
        return f"markers changed: {dict(om)} -> {dict(nm)}"
    od = Counter(d for s in old for d in G.digit_strings(G.strip_markers(s)))
    nd = Counter(d for s in new for d in G.digit_strings(G.strip_markers(s)))
    if od != nd:
        return f"numbers changed: {dict(od)} -> {dict(nd)}"
    return None


def apply_check(paragraphs: list, labels: list, claims: dict, section_claims: list) -> dict:
    """Decision 4: cut what the checker labels unsupported (or supported with no claim id) and
    what fails the digit check; keep the rest. Returns the kept paragraphs and a row per
    sentence for the trace."""
    rows, kept, n = [], [], 0
    for p in paragraphs:
        kp = []
        for s in p:
            lab = labels[n]
            n += 1
            dc = G.digit_check(s, {k: claims[k] for k in section_claims})
            label = lab["label"]
            if label == "supported" and not lab["claim_ids"]:
                label = "unsupported"
            cut = None
            if label == "unsupported":
                cut = f"checker: {lab['reason']}"
            elif not dc["ok"]:
                cut = (f"digit check: {dc['missing']} not in cited claims {dc['ids']}" if dc["missing"]
                       else f"digit check: cites a claim this section was not given: {dc['unknown_ids']}")
            rows.append({"sentence": s, "text": G.strip_markers(s), "marker_ids": G.marker_ids(s),
                         "label": label, "checker_claim_ids": lab["claim_ids"], "reason": lab["reason"],
                         "digit_check": {k: dc[k] for k in ("ok", "digits", "missing")}, "kept": cut is None,
                         "cut_reason": cut})
            if cut is None:
                kp.append(s)
        if kp:
            kept.append(kp)
    return {"kept": kept, "rows": rows}


# ------------------------------------------------------------------------------ grading

def report_values(claims: dict, ids) -> set:
    out = set()
    for i in ids:
        out |= G.claim_values(claims[i])
    return out


def grade(answers: dict, cfg: dict, claims: dict, cited: set) -> dict:
    out = {}
    allowed = report_values(claims, cited)
    for q, g in cfg["fresh_reader"]["grade"].items():
        a = answers.get(q, "")
        groups = [[p for p in grp if re.search(p, a, re.I)] for grp in g["all_of"]]
        bad_numbers = [d for d in G.digit_strings(a) if d not in allowed]
        ok = all(groups) and not bad_numbers
        out[q] = {"right": ok, "matched": groups, "numbers_not_in_claims": bad_numbers,
                  "sections": g["sections"]}
    return out


# ------------------------------------------------------------------------------ runner

class ScriptedConsumer:
    """Test double for the SIGKILL resume test (§15 item 8), selected by
    `CONCISE_SCRIPTED_CONSUMER=<json spec>`: a writer gets one sentence per claim in its
    prompt, a checker labels every sentence supported except a planted control, a join returns
    nothing, a reader answers from fixed text. Each call id is appended to `calls_log` BEFORE
    answering. Never selected in production."""

    def __init__(self, spec_path: str):
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.sleep_s = float(spec.get("sleep_s", 0))
        self.calls_log = Path(spec["calls_log"])
        self.plants = spec.get("plants", [])
        self.model_id = spec.get("model_id", "scripted-model")

    def complete(self, prompt: str, *, call_id: str):
        with self.calls_log.open("a", encoding="utf-8") as fh:
            fh.write(call_id + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        time.sleep(self.sleep_s)
        from harness.consumers import Completion
        head = prompt.split("\n", 1)[0]
        if head.startswith("TASK: CHECK"):
            sents = re.findall(r"^(S\d+): (.*)$", prompt.split("\nSENTENCES\n", 1)[1], re.M)
            text = json.dumps([{"sentence_id": i, "label": "unsupported" if t in self.plants else "supported",
                                "claim_ids": re.findall(r"CL-\d+", prompt.split("\nCLAIMS\n", 1)[1])[:1],
                                "reason": "scripted"} for i, t in sents])
        elif head.startswith("TASK: REWRITE THE JOINS"):
            text = "{}"
        elif head.startswith("TASK: READ"):
            text = json.dumps({"q1": "16 statistical bodies, checked for machine access.",
                               "q2": "Most checks did not pass because hosts refused the client.",
                               "q3": "Publish a machine-readable licence; the Census check failed."})
        else:
            ids = re.findall(r"^\[(CL-\d+)\]", prompt.split("\nCLAIMS", 1)[1], re.M)
            words = ("first", "second", "third")
            text = json.dumps({"paragraphs": [[f"The record states its {w} claim in words [c:{i}]."
                                               for w, i in zip(words, ids)]]})
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 1, "outputTokens": 1})


class StopRun(Exception):
    pass


class Runner:
    def __init__(self, cfg: dict, claims: dict, names: dict, run_dir: Path, consumers: dict, models: dict, log=print):
        self.cfg, self.rc = cfg, cfg["run"]
        self.claims, self.names = claims, names
        self.run_dir = run_dir
        self.ck = FR.Checkpoint(run_dir / "checkpoint.jsonl")
        self.raw = run_dir / "raw"
        self.cons, self.models = consumers, models
        self.log = log
        self.t0 = time.time()
        self.calls = 0
        self.last_progress = 0.0
        self.sec = {s["id"]: s for s in cfg["sections"]}

    # -- one unit, with attempts
    def unit(self, kind: str, sid: int, prompt: str, role: str, parse) -> dict:
        model = self.models[role]
        tsha = TEMPLATE_SHA[kind]
        uid = FR.unit_id(kind, sid, FR.sha(prompt), model, tsha)
        prior = [r for r in self.ck.read() if r["unit_id"] == uid]
        done = next((r for r in prior if r["status"] == "done"), None)
        if done:
            return done
        attempt = max((r["attempt"] for r in prior), default=0)
        cap = self.rc["max_attempts"]
        rec = max(prior, key=lambda r: r["attempt"]) if prior else None
        while attempt < cap:
            attempt += 1
            if time.time() - self.t0 > self.rc["max_wall_seconds"]:
                raise StopRun(f"wall_clock: {self.rc['max_wall_seconds']} s")
            base = {"unit_id": uid, "kind": kind, "question_id": sid, "attempt": attempt, "model_id": model,
                    "role": role, "input_sha256": FR.sha(prompt), "template_sha256": tsha,
                    "prompt_sha256": FR.sha(prompt), "run_id": self.rc["run_id"]}
            t = time.time()
            try:
                comp, err = FR.call(self.cons[role], model, prompt, f"concise.{uid}.{kind}.s{sid}.a{attempt}")
            except FR.StopRun as exc:
                raise StopRun(str(exc)) from exc
            self.calls += 1
            if comp is None:
                rec = {**base, "status": "error", "error": err, "tokens": 0, "usage": {}, "ts": FR._now()}
                self.ck.append(rec)
                continue
            self.raw.mkdir(parents=True, exist_ok=True)
            (self.raw / f"{uid}.a{attempt}.json").write_text(json.dumps(
                {"unit_id": uid, "kind": kind, "section": sid, "attempt": attempt, "model_id": model,
                 "model_receipt": getattr(comp, "receipt", None), "prompt": prompt, "response_text": comp.text,
                 "usage": comp.usage}, indent=1, ensure_ascii=False), encoding="utf-8")
            try:
                parsed, status, error = parse(comp.text), "done", None
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                parsed, status, error = None, "unparsed", str(exc)[:300]
            rec = {**base, "status": status, "error": error, "parsed": parsed, "usage": comp.usage,
                   "tokens": FR._tokens(comp.usage), "wall_s": round(time.time() - t, 2), "ts": FR._now()}
            self.ck.append(rec)
            self.progress()
            if status == "done":
                return rec
        if rec is None or rec["status"] != "done":
            raise StopRun(f"unit {kind} s{sid} not done in {cap} attempts: {rec and rec.get('error')}")
        return rec

    def progress(self, force: bool = False) -> None:
        now = time.time()
        recs = self.ck.read()
        done = sum(1 for r in FR.decided(recs).values() if r["status"] == "done")
        if not force and now - self.last_progress < self.rc["progress_every_seconds"] \
                and done % self.rc["progress_every_units"]:
            return
        self.last_progress = now
        tok = sum(r.get("tokens", 0) for r in recs)
        fails = sum(1 for r in recs if r["status"] != "done")
        total = self.rc["expected_calls"]
        el = now - self.t0
        rate = self.calls / el if el > 0 and self.calls else 0
        eta = max(total - done, 0) / rate if rate else None
        self.log(f"[concise +{el:7.1f}s] units done {done}/~{total} calls this run {self.calls} "
                 f"tokens so far {tok:,} failures so far {fails} eta {'?' if eta is None else f'{eta:.0f}s'}")

    def pool(self, fn, items: list) -> list:
        with ThreadPoolExecutor(max_workers=self.rc["workers"]) as ex:
            return list(ex.map(fn, items))

    # -- prompts
    def ctx(self, s: dict) -> dict:
        ids = s["claims"]
        return {"claims": claim_block(ids, self.claims), "names": names_block(ids, self.claims, self.names)}

    def write(self, sid: int, previous: str) -> list:
        s = self.sec[sid]
        framing = "\n\n".join(f"FRAMING ({k}; not a source of facts)\n{context_text(self.cfg, k)}" for k in s["context"])
        prev = (f"THE PREVIOUS SECTION ENDED WITH THIS PARAGRAPH (carry the reader on from it; do not repeat it):\n{previous}"
                if previous else "This is the first section; the report's title comes before it.")
        p = WRITE_TEMPLATE.format(title=self.cfg["title"], sid=sid, section_title=s["title"], job=s["job"],
                                  previous=prev, register=REGISTER, facts=FACTS, output=OUTPUT, framing=framing,
                                  **self.ctx(s))
        return self.unit("write", sid, p, "writer", parse_paragraphs)["parsed"]

    def joins(self, sections: dict, rnd: int) -> tuple:
        p = JOIN_TEMPLATE.format(draft=draft_text(sections, self.cfg))
        rec = self.unit("join", 900 + rnd, p, "writer", parse_joins)
        out, log = {k: [list(x) for x in v] for k, v in sections.items()}, {}
        for sid in sorted(sections):
            if sid == self.cfg["sections"][0]["id"]:
                continue
            new = rec["parsed"].get(str(sid))
            if new is None:
                log[sid] = "not returned; kept"
                continue
            why = guard_join(sections[sid][0], new)
            if why:
                log[sid] = f"discarded: {why}"
            else:
                out[sid][0] = new
                log[sid] = "applied" if new != sections[sid][0] else "unchanged"
        return out, {"unit_id": rec["unit_id"], "per_section": log}

    def check_prompt(self, sid: int, sentences: list) -> str:
        s = self.sec[sid]
        lines = "\n".join(f"S{i}: {G.strip_markers(x)}" for i, x in enumerate(sentences, 1))
        return CHECK_TEMPLATE.format(sentences=lines, **self.ctx(s))

    def check(self, sid: int, paragraphs: list, kind: str = "check") -> list:
        sents = flat(paragraphs)
        return self.unit(kind, sid, self.check_prompt(sid, sents), "checker",
                         lambda t: parse_labels(t, len(sents)))

    def control(self, sid: int, paragraphs: list) -> dict:
        sents = flat(paragraphs)
        plant = self.cfg["controls"][sid]["sentence"]
        at = len(sents) // 2 + 1 if sents else 0
        planted = sents[:at] + [plant] + sents[at:]
        rec = self.unit("control", sid, self.check_prompt(sid, planted), "checker",
                        lambda t: parse_labels(t, len(planted)))
        got = rec["parsed"][at]
        return {"section": sid, "plant": plant, "position": f"S{at + 1}", "label": got["label"],
                "reason": got["reason"], "caught": got["label"] == "unsupported", "unit_id": rec["unit_id"],
                "tokens": rec.get("tokens")}

    def revise(self, sid: int, paragraphs: list, notes: list, cuts: list, kind: str = "revise") -> list:
        s = self.sec[sid]
        current = "\n\n".join(para_text(p) for p in paragraphs) or "(every sentence was cut)"
        p = REVISE_TEMPLATE.format(title=self.cfg["title"], sid=sid, section_title=s["title"], job=s["job"],
                                   notes="\n".join(f"- {n}" for n in notes) or "- none",
                                   cuts="\n".join(f"- {c}" for c in cuts) or "- none", current=current,
                                   register=REGISTER, facts=FACTS, output=OUTPUT, **self.ctx(s))
        return self.unit(kind, sid, p, "writer", parse_paragraphs)["parsed"]

    def reader(self, rnd: int, report: str) -> dict:
        q = self.cfg["fresh_reader"]["questions"]
        p = READER_TEMPLATE.format(report=report, **q)
        rec = self.unit("reader", 800 + rnd, p, "reader", parse_reader)
        return {"unit_id": rec["unit_id"], "model_id": rec["model_id"], "prompt_sha256": rec["prompt_sha256"],
                "answers": rec["parsed"], "response_text": json.dumps(rec["parsed"], ensure_ascii=False)}

    # -- phases
    def checked(self, sections: dict, prior: dict | None = None) -> tuple:
        """Check every section (a section whose text is unchanged reuses its unit by key), apply
        the cuts, and return (kept sections, trace rows per section)."""
        recs = dict(zip(sorted(sections), self.pool(lambda sid: self.check(sid, sections[sid]), sorted(sections))))
        kept, rows = {}, {}
        for sid in sorted(sections):
            a = apply_check(sections[sid], recs[sid]["parsed"], self.claims, self.sec[sid]["claims"])
            kept[sid], rows[sid] = a["kept"], {"check_unit": recs[sid]["unit_id"], "rows": a["rows"]}
        return kept, rows

    def notes_for(self, sid: int, gate: dict, rows: list) -> tuple:
        g = gate["sections"][sid]
        notes = []
        for fp in g["flagged_pairs"]:
            notes.append(f"Short clarification after a long sentence ({fp['why']}): \"{fp['first']}\" then "
                         f"\"{fp['second']}\". Fold the second into the first, or make it a full sentence.")
        if g["flagged_pair_count"] > self.cfg["gate"]["pair"]["max_flagged_pairs_per_section"]:
            notes.append(f"The section has {g['flagged_pair_count']} such pairs; at most "
                         f"{self.cfg['gate']['pair']['max_flagged_pairs_per_section']} pass.")
        for d in g["dashes"]:
            notes.append(f"A forbidden dash ({d['rule']}). Remove it.")
        for b in g["banned"]:
            notes.append(f"A forbidden word: {b['match']!r}. Remove it.")
        for lem, n in g["lemmas_over_limit"].items():
            notes.append(f"The word {lem!r} (in some form) is used {n} times in this section; use it at most "
                         f"{self.cfg['gate']['repetition']['max_lemma_per_section']} times.")
        for gram, v in gate["repeated_3grams"].items():
            if sid in v["sections"]:
                notes.append(f"The phrase (by its content words) {gram!r} occurs {v['count']} times in the report, "
                             f"in sections {v['sections']}; say it once and refer back.")
        cuts = [f"\"{r['text']}\" ({r['cut_reason']})" for r in rows if not r["kept"]]
        return notes, cuts

    def gate(self, sections: dict) -> dict:
        rep = G.gate_report({sid: flat(sections[sid]) for sid in sorted(sections)}, self.cfg["gate"])
        return rep

    def pilot(self) -> None:
        recs = [r for r in self.ck.read() if r["status"] == "done" and r.get("tokens")]
        if not recs:
            return
        per = sum(r["tokens"] for r in recs) / len(recs)
        proj = per * self.rc["expected_calls"]
        self.log(f"PILOT: {len(recs)} call(s) measured, {per:,.0f} tokens per call; projected for "
                 f"{self.rc['expected_calls']} calls: {proj:,.0f}, ceiling {self.rc['ceiling_tokens']:,}")
        if proj > self.rc["ceiling_tokens"]:
            raise StopRun(f"pilot projects {proj:,.0f} tokens past the ceiling {self.rc['ceiling_tokens']:,}")

    def run(self, build_report) -> dict:
        cfg, out = self.cfg, {"generated_by": GENERATOR, "task": TASK, "models": self.models,
                              "template_sha256": TEMPLATE_SHA}
        order = [s["id"] for s in cfg["sections"]]
        # 2. write, in order, each given the previous section's last paragraph
        r1, prev = {}, ""
        for i, sid in enumerate(order):
            r1[sid] = self.write(sid, prev)
            prev = " ".join(G.strip_markers(x) for x in r1[sid][-1])
            if i == 0:
                self.pilot()
        out["round1"] = {"written": r1}
        # 3. joins
        j1, jlog = self.joins(r1, 1)
        out["round1"]["joins"], out["round1"]["joined"] = jlog, j1
        # 4. controls, all before any real check
        ctl = self.pool(lambda sid: self.control(sid, j1[sid]), order)
        out["control"] = {"passed": all(c["caught"] for c in ctl), "rows": ctl}
        if not out["control"]["passed"]:
            out["stopped"] = "control: the checker missed a planted false sentence; no check verdict is used"
            return out
        # 5. claim check and digit check
        k1, rows1 = self.checked(j1)
        out["round1"]["check"], out["round1"]["kept"] = rows1, k1
        # 6. prose gate, round 1
        g1 = self.gate(k1)
        out["round1"]["gate"] = g1
        # 6b. one revision round
        r2, sent_back = {}, {}
        for sid in order:
            notes, cuts = self.notes_for(sid, g1, rows1[sid]["rows"])
            if notes or cuts:
                sent_back[sid] = {"notes": notes, "cuts": cuts}
        revised = dict(zip(sent_back, self.pool(
            lambda sid: self.revise(sid, k1[sid], sent_back[sid]["notes"], sent_back[sid]["cuts"]), list(sent_back))))
        for sid in order:
            r2[sid] = revised.get(sid, k1[sid])
        j2, jlog2 = self.joins(r2, 2)
        k2, rows2 = self.checked(j2)
        g2 = self.gate(k2)
        out["round2"] = {"sent_back": sent_back, "revised": revised, "joins": jlog2, "joined": j2,
                         "check": rows2, "kept": k2, "gate": g2}
        # 7. fresh reader, round 1
        cited = {i for sid in k2 for r in rows2[sid]["rows"] if r["kept"] for i in r["marker_ids"]}
        rep1 = build_report(cfg, k2, self.claims)
        rd1 = self.reader(1, rep1)
        gr1 = grade(rd1["answers"], cfg, self.claims, cited)
        out["reader"] = {"1": {**rd1, "grade": gr1, "report_sha256": FR.sha(rep1)}}
        wrong = sorted({s for q, v in gr1.items() if not v["right"] for s in v["sections"]})
        final, rows_final, gate_final = k2, rows2, g2
        if wrong:
            fixed = {}
            for sid in wrong:
                notes = [f"A reader who read only the report was asked: \"{cfg['fresh_reader']['questions'][q]}\" "
                         f"and answered: \"{rd1['answers'][q]}\". That answer was graded wrong. A right answer holds: "
                         f"{cfg['fresh_reader']['grade'][q]['expect']}. Make this section carry it, from its claims."
                         for q, v in gr1.items() if not v["right"] and sid in v["sections"]]
                cuts = [f"\"{r['text']}\" ({r['cut_reason']})" for r in rows1[sid]["rows"] + rows2[sid]["rows"]
                        if not r["kept"]]
                fixed[sid] = self.revise(sid, k2[sid], notes, cuts, kind="fix")
            j3 = {sid: fixed.get(sid, k2[sid]) for sid in order}
            k3, rows3 = self.checked(j3)
            final, rows_final, gate_final = k3, rows3, self.gate(k3)
            out["round3"] = {"sent_back_by_reader": wrong, "fixed": fixed, "check": rows3, "kept": k3,
                             "gate": gate_final}
            cited = {i for sid in k3 for r in rows3[sid]["rows"] if r["kept"] for i in r["marker_ids"]}
        # 7b. fresh reader, round 2: the report as it now stands (unchanged if nothing went back)
        rep2 = build_report(cfg, final, self.claims)
        rd2 = self.reader(2, rep2)
        out["reader"]["2"] = {**rd2, "grade": grade(rd2["answers"], cfg, self.claims, cited),
                              "report_sha256": FR.sha(rep2), "sections_sent_back": wrong}
        out["final"] = {"sections": final, "rows": rows_final, "gate": gate_final}
        return out


def consumers(cfg: dict, scripted: str | None) -> tuple:
    rc = cfg["run"]
    if scripted:
        c = ScriptedConsumer(scripted)
        return {r: c for r in ("writer", "checker", "reader")}, {r: c.model_id for r in ("writer", "checker", "reader")}
    from kg import spend
    from kg.extraction import model_stub
    from harness.consumers import ClaudeCLIConsumer, ConsumerConfig
    mc = model_stub.load_model_config()
    models = {"writer": mc[rc["writer_model_key"]], "checker": mc[rc["checker_model_key"]],
              "reader": mc[rc["reader_model_key"]]}
    if len(set(models.values())) != 3:
        raise SystemExit(f"FATAL: writer, checker and reader must be three models; the lock gives {models}")
    model_stub.guard_no_api_key()
    led = spend.default_ledger()
    st = led.status().get("runs", {}).get(rc["run_id"])
    if st is None or int(st.get("ceiling_tokens") or 0) != rc["ceiling_tokens"]:
        led.declare(rc["run_id"], rc["ceiling_tokens"], declared_by=f"{GENERATOR} ({TASK})",
                    call_class=rc["call_class"], **({"supersede": True} if st else {}))
    spend.set_current_run(rc["run_id"])

    def mk(m):
        # The ROLE behind the model_config key that named `m` (seldon AD-035 R4, MODEL-001).
        return ClaudeCLIConsumer(ConsumerConfig(role=model_stub.role_for_model(m, mc), provider=FR.PROVIDER,
                                                timeout_seconds=rc["timeout_seconds"], call_class=rc["call_class"]))
    return {r: mk(m) for r, m in models.items()}, models


def main(argv=None) -> int:
    import concise_report_build as B
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="check the inputs and print the first prompt; no call")
    g.add_argument("--run", action="store_true")
    ap.add_argument("--run-dir", default=None, help="test seam (default: reports/concise/run)")
    ap.add_argument("--progress-log", default=None, help="test seam")
    a = ap.parse_args(argv)
    cfg = load_config()
    claims = load_claims(cfg)
    for s in cfg["sections"]:
        bad = [i for i in s["claims"] if i not in claims]
        if bad:
            raise SystemExit(f"FATAL: section {s['id']} lists claims not in the claims file: {bad}")
    names = load_names(cfg)
    run_dir = Path(a.run_dir) if a.run_dir else RUN_DIR
    plog = Path(a.progress_log) if a.progress_log else PROGRESS_LOG
    plog.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with plog.open("a", encoding="utf-8") as fh:
            fh.write(f"{FR._now()} {msg}\n")

    if a.dry_run:
        r = Runner(cfg, claims, names, run_dir, {}, {"writer": "-", "checker": "-", "reader": "-"}, log)
        s = cfg["sections"][0]
        print(WRITE_TEMPLATE.format(title=cfg["title"], sid=1, section_title=s["title"], job=s["job"],
                                    previous="(first)", register=REGISTER, facts=FACTS, output=OUTPUT,
                                    framing="(framing)", **r.ctx(s))[:6000])
        print(json.dumps({"sections": {s["id"]: len(s["claims"]) for s in cfg["sections"]},
                          "ceiling_tokens": cfg["run"]["ceiling_tokens"]}, indent=1))
        return 0
    cons, models = consumers(cfg, os.environ.get("CONCISE_SCRIPTED_CONSUMER"))
    runner = Runner(cfg, claims, names, run_dir, cons, models, log)
    code = 0
    try:
        out = runner.run(B.report_markdown)
        if out.get("stopped"):
            log(f"STOP: {out['stopped']}")
            code = 3
    except StopRun as exc:
        runner.progress(force=True)
        log(f"STOP: {exc}")
        out, code = {"generated_by": GENERATOR, "stopped": str(exc)}, 3
    runner.progress(force=True)
    out["tokens"] = sum(r.get("tokens", 0) for r in runner.ck.read())
    out["calls_recorded"] = len(runner.ck.read())
    (run_dir / PIPELINE).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=list) + "\n", encoding="utf-8")
    log(f"wrote {run_dir / PIPELINE} (exit {code})")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
