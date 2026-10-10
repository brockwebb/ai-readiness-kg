#!/usr/bin/env python3
"""Build the DCAT-US 3.0 plain-language brief from the checked answers. **Zero spend, no
network.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decisions 4 to 6,
implementing DN-011 ADDENDUM 01 R6 to R8. Reads `reports/dcat_us_3_brief/answers.json`
(written by `scripts/dcat_brief_run.py`), the evidence files and `brief_config.yaml`, and
writes under `reports/dcat_us_3_brief/`:

* `BRIEF.md` / `BRIEF.pdf`: the operator-reviewed structure of 8 October 2026
  (`cc_tasks/2026-10-08_dcat_brief_pdfs_from_build_ADDENDUM_01.md`, the reference being
  `BRIEF_v2_2026-10-08.md`): title as a question, byline, a bottom line computed from the
  table, sections 1 to 6, the AI-use statement in FCSM 26-01's form, sources. The validated
  sentences are printed verbatim; the table, its plain result labels and the bottom line are
  built by code; the two operator-authored paragraphs are carried verbatim and named in
  `build_report.json`.
* `ROWS.md` / `ROWS.pdf`: the evidence behind each table row, in the shape of
  `ROWS_v2_2026-10-08.md` (ADDENDUM 02): the brief's labels, the three questions per need,
  repeated statements of one finding cut to one, source numbers from the brief's list.
* `DEMO.pdf`, from `DEMO.md` when it is present (no script writes `DEMO.md`).
* `build_report.json`: what the code added, what it cut, the operator text, the plain-language
  gate, page counts, each PDF's Markdown hash, and the comparison with the v2 references.

Every reader-facing file ships a PDF from this build (the base task, decision 1): the operator
reads PDFs, and a PDF no script regenerates goes stale (34ccb843).

**DCAT-005** (`cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb.md`): the rows are read
from the overlay `run/corrections.json` (`scripts/dcat_brief_correct.py`), never from DCAT-004
v2's `answers.json` alone; every table cell that says what 3.0 carries cites a published page,
the 2025 working draft is named as such, and the build refuses otherwise (decision 4); and the
body is held to the amendment's word limit, also refused over it (decision 5).

Citations are the FAQ's form (`scripts/dcat_faq_build.py` `citation`, `canonical`), one
numbered list at the end, numbered in order of first citation (the Vancouver convention). The
lint is DCAT-003 ADDENDUM 01's (`scripts/dcat_faq_lint.py`) and refuses the build on any
finding, before any file is written.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_build.py [--no-pdf]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import dcat_faq_build as FB  # noqa: E402
import dcat_faq_evidence as EV  # noqa: E402
import dcat_faq_lint as LINT  # noqa: E402

OUT = EV.BRIEF_OUT
ANSWERS = OUT / "answers.json"
CORRECTIONS = OUT / "run" / "corrections.json"
#: The run records the AI-use statement's model list and dates are read from (ADDENDUM 01
#: item 3): this brief's, and the questions-and-answers paper's it quotes and cites.
RUN_DIRS = (OUT / "run", REPO / "reports" / "dcat_us_3_faq" / "run")
#: The published Overview as served 2026-10-05, which names DCAT-US (DCAT-005 decision 4).
OVERVIEW = "dcat-us-3-overview-2026-10-05"
AMEND = "amendment_2026_10_07_dcat005"
BRIEF_MD, BRIEF_PDF = OUT / "BRIEF.md", OUT / "BRIEF.pdf"
ROWS_MD, ROWS_PDF = OUT / "ROWS.md", OUT / "ROWS.pdf"
DEMO_MD, DEMO_PDF = OUT / "DEMO.md", OUT / "DEMO.pdf"
#: The operator-reviewed references the build is compared with (ADDENDUM 01 item 5, ADDENDUM 02
#: item 3). Read, never written.
V2_BRIEF, V2_ROWS = OUT / "BRIEF_v2_2026-10-08.md", OUT / "ROWS_v2_2026-10-08.md"
BUILD_REPORT = OUT / "build_report.json"
AUTHOR = "Brock Webb, U.S. Census Bureau"
PREPARED = "8 October 2026"
TITLE = "DCAT-US 3.0 and federal statistics: was FCSM's input included?"
ROWS_TITLE = "DCAT-US 3.0 and federal statistics: the evidence behind each row"

# ------------------------------------------------------------------ operator-authored text
#
# Carried verbatim from the operator-reviewed v2 files of 8 October 2026, outside the
# validator (ADDENDUM 01 item 4, ADDENDUM 02 item 1), and listed in `build_report.json` under
# "operator_authored". `{c1}` is the citation mark of the published Overview.

NEXT_STEP = ("**Proposed next step (the author's).** The federal statistical system could do the same: adopt a "
             "statistical profile of DCAT-US 3.0 as a community standard, endorsed by the Interagency Council on "
             "Statistical Policy (ICSP). The profile names which of 3.0's Optional fields statistical agencies fill "
             "and adds the few statistical fields 3.0 lacks, on StatDCAT-AP's model. It stays optional for the "
             "government at large and is expected practice for statistical data.")
CHECKING = ("**Checking it is automated.** DCAT-US 3.0 is published as a machine-readable JSON Schema, and agencies "
            "can check their metadata against it with Data.gov's online validator or the published validation "
            "script. {c1} Both are programs that report records that do not conform, not checklists. A statistical "
            "profile can be published the same way, as a stricter schema, and checked by the same programs.")
#: The validated sentence the CHECKING paragraph replaces (it says the same, with the source's
#: detail). Matched exactly; the build refuses if the validated set no longer holds it.
SUPERSEDED_BY_OPERATOR = {
    "6": ["Data.gov's overview page says agencies can automatically check their dataset descriptions against "
          "the version 3.0 schema, using an online validator or their own tools."],
}
#: Plain names for two needs, as the brief's table and the rows file print them.
NEED_PLAIN = {"dimensions": "dimensions (breakdowns such as place, item, time)",
              "uncertainty": "uncertainty (margins of error)"}
#: A dropped element in plain words: (table cell, bottom-line subject).
DROPPED_PLAIN = {"inSeries": ("the series link", "the link that marks a dataset as part of a series")}
#: The level cell of a need whose only property sits on another class than Dataset (ADDENDUM 02
#: item 2), keyed by that property as `corrections.json` names it.
NO_FIELD_PLAIN = {"QualityMeasurement unitMeasure":
                  "No field for the data's unit; unitMeasure gives the unit of a quality score"}
LEGEND = [
    ("Optional only", "it has a field in 3.0, but agencies may leave it out."),
    ("Recommended", "agencies are expected to fill it; it is not required."),
    ("Dropped", "it was in the 2025 working draft and is not in the published 3.0."),
    ("No field", "3.0 has no field for it."),
    ("Different form", "the international standards (StatDCAT-AP, the European statistical version of DCAT, and "
                       "W3C vocabularies) carry it differently from how FCSM asked for it."),
    ("Not confirmed / not checked", "the source check could not confirm that part."),
]
#: The brief adds this to the "Different form" line; the rows file has no section 4.
LEGEND_BRIEF_TAIL = {"Different form": " Section 4 gives each case."}
ROWS_HOW_TO = ("**How to use this file.** The brief's table (section 3) gives one line per statistical need. This "
               "file gives the evidence behind each line, in the same order and numbered 1 to {n} as in the table. "
               "Each need answers the table's three questions in turn: did the Federal Committee on Statistical "
               "Methodology (FCSM) ask for it, where did it land in DCAT-US 3.0, and what do the international "
               "standards say. Each answer is a sentence drawn from the source cited after it, and the source "
               "numbers match the brief's source list. Where the source check could not confirm an answer, the "
               "file says so and gives none.")
#: The FCSM 26-01 statement ("Communicating Generative AI Use in Federal Statistical Products",
#: September 2026), its five elements: contribution; how used; tools with version and dates;
#: human oversight; where to find more. `{models}` and `{dates}` come from the run records.
AI_USE = {
    "brief": ("Generative AI made a meaningful contribution. It located passages in the source documents, drafted "
              "the summary sentences from them, checked each sentence against the passage it cites, and laid out "
              "this version from the author's direction. Sentences the check could not confirm were removed, not "
              "reworded. The models were Anthropic's {models}, used through Claude Code under a commercial "
              "subscription, {dates}. The author reviewed and approved the content and is responsible for it. The "
              "passage behind every statement is quoted in the companion detail file and the questions-and-answers "
              "attachment of 5 October 2026."),
    "rows": ("Generative AI made a meaningful contribution. It located passages in the source documents, drafted "
             "the sentences in this file from them, checked each sentence against the passage it cites, and laid "
             "out this version from the author's direction. Sentences the check could not confirm were removed, "
             "not reworded, and repeated statements of the same finding were cut to one. The models were "
             "Anthropic's {models}, used through Claude Code under a commercial subscription, {dates}. The author "
             "reviewed and approved the content and is responsible for it. The passages themselves are quoted in "
             "the questions-and-answers attachment of 5 October 2026."),
}
OPERATOR_AUTHORED = ["byline", "section 5: Proposed next step", "section 5: Checking it is automated",
                     "need plain names (NEED_PLAIN)", "dropped and no-field cell wording (DROPPED_PLAIN, "
                     "NO_FIELD_PLAIN)", "result legend", "rows file: How to use this file",
                     "AI-use statements (model list and dates generated from the run records)"]

#: Near-duplicate cut in the rows file (ADDENDUM 02 item 1). Word-set resemblance (Jaccard), the
#: unigram case of Broder's shingle resemblance ("On the resemblance and containment of
#: documents", 1997), over lowercased words with a short stop list removed and a plural "s"
#: stripped. 0.23 is the midpoint of the gap measured on the operator's own cuts in
#: `ROWS_v2_2026-10-08.md`: every pair he cut scores at least 0.29, every pair he kept at most
#: 0.17 (8 needs, 17 asked sentences). A threshold fitted to seven cuts, and said so.
NEAR_DUP_JACCARD = 0.23
_STOP = frozenset("a an the of to and or for in on at by with as is are be it its that this from which their "
                  "was were".split())

LEVEL_LABEL = {"mandatory": "Mandatory", "recommended": "Recommended", "optional": "Optional",
               "dropped": "Dropped", "no_field": "No field"}
NUM_WORD = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
            8: "eight", 9: "nine", 10: "ten"}
REPORT: dict = {"added_by_code": [], "cut_by_build": []}
#: The working draft's source line (DCAT-005 decision 4). Set from the amendment in `main`.
DRAFT_TITLE = "The 2025 working draft of DCAT-US Version 3 (Candidate Recommendation Snapshot, not the published 3.0)"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _num(n: int) -> str:
    return NUM_WORD.get(n, str(n))


class Cites:
    """One numbered source list for the whole brief, in first-use order (the FAQ's citation
    form, `dcat_faq_build.citation`). The rows file marks through the same object, so its
    numbers are the brief's."""

    def __init__(self, faq_cfg: dict):
        self.cfg, self.refs, self.metas, self.secs = faq_cfg, {}, {}, {}

    def key_meta(self, it: dict) -> tuple:
        if it["kind"] == "crosswalk row":
            return "s015", {"title": "S-015 readiness crosswalk: the presenter's own "
                                     "crosswalk of quality terms (unpublished), quoting "
                                     "W3C and ISO/IEC 25012 definitions",
                            "issuer": "", "date": "14 September 2026", "url": ""}
        if it["kind"] == "element table row":
            return "table", {"title": "Requirement level of each Dataset element, read from four "
                                      "versions of the DCAT-US Dataset page and schema (v1.1; 2025 "
                                      "working draft; pages of 21 August, 15 September and 5 October "
                                      "2026), as tabled in the attachment to the questions-and-answers "
                                      "paper of 5 October 2026", "issuer": "", "date": "", "url": ""}
        if it["kind"] == "catalog record (not admitted)":
            # The record's own fields, as the FAQ's question 14 prints them; its notes are
            # the cataloguer's working text and are not a citation (the 2026-10-05 lint
            # defect, scripts/dcat_faq_lint.py).
            rec = it.get("record") or {}
            return f"catalog:{it['doc_id']}", {
                "title": f"{rec.get('title')} (not published)", "issuer": rec.get("issuer") or "",
                "date": FB._plain_date(rec.get("date")), "url": ""}
        key, meta = FB.canonical(it, FB.DOCS, self.cfg)
        if it["doc_id"] == EV.DRAFT:
            # DCAT-005 decision 4: cited only as the working draft, never as 3.0.
            meta = {**meta, "title": DRAFT_TITLE}
        return key, meta

    def mark(self, items: list) -> str:
        nums = []
        for it in items:
            key, meta = self.key_meta(it)
            if key not in self.refs:
                self.refs[key], self.metas[key], self.secs[key] = len(self.refs) + 1, meta, []
            sec = it.get("section") or ""
            if sec and sec not in self.secs[key] and it["kind"] not in ("element table row", "crosswalk row",
                                                                         "catalog record (not admitted)"):
                self.secs[key].append(sec)
            nums.append(self.refs[key])
            if it["kind"] == "element table row":
                # The level a row is read for is the page as served on 5 October 2026; that
                # published page is cited beside the table (DCAT-005 decision 4).
                nums.append(self.mark_one({"doc_id": EV.LIVE, "kind": "document text", "section": ""}))
        return "".join(f"[{n}]" for n in sorted(set(nums)))

    def mark_one(self, it: dict) -> int:
        return int(self.mark([it]).strip("[]"))

    def lines(self, only: set | None = None) -> list:
        return [f"{n}. {FB.citation(self.metas[k], self.secs[k])}" for k, n in self.refs.items()
                if only is None or n in only]


def load_ev(name: str) -> dict:
    return json.loads((EV.BRIEF_EVIDENCE_DIR / name).read_text(encoding="utf-8"))


def kept_sentences(sec: dict, ev: dict, cites: Cites, skip: list = ()) -> list:
    """A section's kept sentences, verbatim, each with its marks; a sentence in `skip` (one the
    operator's text replaces) is left out and recorded."""
    by = {it["id"]: it for it in ev["items"]}
    out = []
    for s in sec.get("kept") or []:
        if s["text"].rstrip() in skip:
            REPORT["cut_by_build"].append({"superseded_by_operator_text": s["text"].rstrip()})
            continue
        out.append(FB.shown(s["text"], -1, {}).rstrip() + " " + cites.mark([by[e] for e in s["evidence"]]))
    return out


def row_cell_items(row: dict, ev: dict, part: str) -> list:
    """The passages a cell cites: its kept sentence's, from the evidence file the sentence was
    checked against (the need's own, or its full-read file, DCAT-005 decision 1)."""
    for x in row["items"]:
        if x["part"] == part and x["kind"] == "SENTENCE" and x["kept"]:
            return sentence_items(x, ev)
    return []


def sentence_items(x: dict, ev: dict) -> list:
    src = load_ev(x["evidence_file"]) if x.get("evidence_file") else ev
    by = {it["id"]: it for it in src["items"]}
    return [by[e] for e in x["evidence"]]


def published_gate(rows: dict, bcfg: dict) -> list:
    """DCAT-005 decision 4, mechanically: a landed cell (other than "dropped", a draft-versus-final
    statement by definition, or "left out") and a literature cell that says what 3.0 carries
    must each cite at least one published page, and neither may cite the working draft. Returns
    the findings; the build refuses on any."""
    pub = set(bcfg[AMEND]["published"]["pages"])
    out = []
    for nid in sorted(rows, key=int):
        r = rows[nid]
        ev = load_ev(f"need_{nid}.json")
        for part, needs_pub in (("landed", r["landed"] not in (None, "dropped", "absent")),
                                ("literature", r["literature"] in ("matches", "carries_3_0_does_not"))):
            if not needs_pub:
                continue
            items = row_cell_items(r, ev, part)
            if not any(it["kind"] == "element table row" or it["doc_id"] in pub for it in items):
                out.append(f"row {nid} {part}: no published page cited")
            if any(it["doc_id"] == EV.DRAFT and it["kind"] != "element table row" for it in items):
                out.append(f"row {nid} {part}: cites the 2025 working draft for what 3.0 carries")
    return out


def void_rows(rows: dict) -> list:
    """The rows outcome C could still apply to if the unpublished plan showed the need was not
    asked for (DCAT-005 decision 3): a row in E whose literature part is unconfirmed or says
    the standards carry the need (`matches`, `carries_3_0_does_not`), and an unplaced row that
    C is still open for."""
    out = []
    for nid in sorted(rows, key=int):
        r = rows[nid]
        if r["outcome"] == "E" and r["literature"] in (None, "matches", "carries_3_0_does_not"):
            out.append(nid)
        elif r["outcome"] == "unplaced" and "C" in (r["open"] or []):
            out.append(nid)
    return out


# ------------------------------------------------------------------ the table, by code

def level(r: dict) -> str | None:
    """The need's level in 3.0 as the brief states it. ADDENDUM 02 item 2: a need whose every
    named property sits on a class other than Dataset ("QualityMeasurement unitMeasure") has
    no field of its own, whatever level that other class gives the property, so it is "no
    field", never "Optional". "Left out" (`absent`) is also no field."""
    if r["landed"] is None:
        return None
    if r["landed"] == "absent":
        return "no_field"
    els = r.get("elements") or []
    if els and all(len(e.split()) == 2 and e.split()[0] != "Dataset" for e in els):
        return "no_field"
    if r["landed"] not in LEVEL_LABEL:
        raise SystemExit(f"FATAL: need {r['need']!r} has a level the brief has no label for: {r['landed']!r}")
    return r["landed"]


def result_label(r: dict) -> str:
    """The plain result label (ADDENDUM 01 item 2): the level, then how the standards carry the
    need, then what the check could not confirm. No letter codes."""
    lv, lit = level(r), r["literature"]
    if lit not in (None, "matches", "carries_3_0_does_not", "carries_differently_than_asked"):
        raise SystemExit(f"FATAL: need {r['need']!r} has a literature code the brief has no label for: {lit!r}")
    diff = lit == "carries_differently_than_asked"
    if lv is None:
        out = "**Different form**; level not confirmed" if diff else "Not confirmed"
    elif diff:
        out = f"**{LEVEL_LABEL[lv]}**, and **different form**"
    elif lv in ("mandatory", "recommended", "optional") and lit is None:
        out = f"**{LEVEL_LABEL[lv]}**; form not checked"
    elif lv == "optional":
        out = "**Optional only**"
    else:
        out = f"**{LEVEL_LABEL[lv]}**"
    if r["asked"] is None:
        out += "; FCSM ask not confirmed"
    elif r["asked"] != "asked":
        out += "; not asked in public documents"
    return out


def need_name(r: dict) -> str:
    return NEED_PLAIN.get(r["need"], r["need"])


def asked_items(r: dict, ev: dict) -> list:
    """Every kept ask's passages: the full read (DCAT-005 decision 1) can keep asks from several
    documents."""
    return [it for x in r["items"] if x["part"] == "asked" and x["kind"] == "SENTENCE" and x["kept"]
            for it in sentence_items(x, ev)]


def asked_cell(r: dict, a_items: list, cites: Cites) -> str:
    if r["asked"] is None:
        return "Not confirmed"
    if r["asked"] == "asked":
        return f"Yes {cites.mark(a_items)}"
    if r["asked"] == "publicly_not_asked":
        return f"No, on the record {cites.mark(a_items)}"
    if r.get("asked_read") == "not_found_in_full_read":
        return "Not in public documents (read in full)"
    return "Not in the public record"


def level_cell(r: dict, l_items: list, cites: Cites) -> str:
    lv = level(r)
    if lv is None:
        return "Not confirmed"
    els = r.get("elements") or []
    if lv == "dropped":
        plain = [DROPPED_PLAIN[e][0] for e in els if e in DROPPED_PLAIN]
        cell = "Dropped" + (f" ({FB._join(plain)})" if plain else "")
    elif lv == "no_field":
        plain = [NO_FIELD_PLAIN[e] for e in els if e in NO_FIELD_PLAIN]
        cell = "; ".join(plain) if plain else "No field"
    else:
        cell = LEVEL_LABEL[lv]
    cell += ", put off to a later version" if r.get("deferred") else ""
    return cell + (f" {cites.mark(l_items)}" if l_items else "")


def bottom_line(rows: dict) -> tuple:
    """The bottom line (ADDENDUM 01 item 1), computed from the table: the needs asked for, and
    per level among them. The answer reads R6's outcome A on level alone: "partly" if at least
    one asked need is Mandatory or Recommended, "yes" if every one is, "no" if none is and every
    asked need's level is confirmed, otherwise "not decided". Returns (text without marks,
    counts, the asked rows)."""
    asked = [k for k in sorted(rows, key=int) if rows[k]["asked"] == "asked"]
    by = {lv: [k for k in asked if level(rows[k]) == lv] for lv in (*LEVEL_LABEL, None)}
    mr = len(by["mandatory"]) + len(by["recommended"])
    answer = ("yes" if asked and mr == len(asked) else "partly" if mr else
              "no" if not by[None] else "not decided")
    n, na = len(rows), len(asked)
    s = [f"**Bottom line: {answer}.** The Federal Committee on Statistical Methodology (FCSM) publicly asked for "
         f"{_num(na)} of the {_num(n)} statistical needs in the table below."]

    def named(lv: str, word: str) -> str:
        ks = by[lv]
        if not ks:
            return f"In DCAT-US 3.0 none of the {_num(na)} is {word}." if lv == "mandatory" else f"None is {word}."
        names = FB._join([rows[k]["need"] for k in ks])
        return f"{_cap(_num(len(ks)))}, {names}, {'is' if len(ks) == 1 else 'are'} {word}."
    s += [named("mandatory", "Mandatory"), named("recommended", "Recommended")]
    rest = []
    if by["optional"]:
        k = len(by["optional"])
        rest.append(f"{_num(k)} {'is an Optional field' if k == 1 else 'are Optional fields'} that agencies may "
                    "leave out")
    for k in by["dropped"]:
        subj = [DROPPED_PLAIN[e][1] for e in rows[k].get("elements") or [] if e in DROPPED_PLAIN]
        rest.append(f"{FB._join(subj) if subj else rows[k]['need']} was dropped")
    for k in by["no_field"]:
        rest.append(f"{rows[k]['need']} has no field")
    if by[None]:
        rest.append(f"the published page does not settle where {FB._join([rows[k]['need'] for k in by[None]])} "
                    "landed")
    if rest:
        s.append(_cap(", ".join(rest[:-1]) + (", and " if len(rest) > 1 else "") + rest[-1]) + ".")
    counts = {"asked": na, "of": n, "answer": answer,
              **{(lv or "not_confirmed"): len(ks) for lv, ks in by.items()}}
    return " ".join(s), counts, asked


# ------------------------------------------------------------------ the AI-use statement

def _model_name(mid: str) -> str:
    """"claude-opus-4-8" -> "Claude Opus 4.8"."""
    parts = mid.split("-")
    return " ".join(p.capitalize() for p in parts[:2]) + " " + ".".join(parts[2:])


def ai_use_records() -> dict:
    """ADDENDUM 01 item 3: the models and dates, from the records, never typed. The models that
    located, drafted and checked are the served models in the run records (`RUN_DIRS`); the
    model that laid out the operator-reviewed v2 is the commit trailer of the commits that wrote
    the v2 references, and its date is theirs."""
    mids, dates = set(), set()
    for d in RUN_DIRS:
        for p in sorted(d.rglob("*")):
            if p.suffix not in (".json", ".jsonl"):
                continue
            t = p.read_text(encoding="utf-8")
            mids |= set(re.findall(r'"(?:model_id|model|reader)":\s*"(claude-[a-z]+-[0-9][0-9-]*)"', t))
            dates |= set(re.findall(r'"ts":\s*"(\d{4}-\d{2}-\d{2})T', t))
    if not mids or not dates:
        raise SystemExit(f"FATAL: no model ids or call dates in the run records {[str(d) for d in RUN_DIRS]}")
    r = subprocess.run(["git", "log", "--format=%cs%x09%(trailers:key=Co-Authored-By,valueonly,separator=%x1f)",
                        "--", str(V2_BRIEF.relative_to(REPO)), str(V2_ROWS.relative_to(REPO))],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode or not r.stdout.strip():
        raise SystemExit(f"FATAL: cannot read the v2 references' commit trailers from git: {r.stderr.strip()}")
    layout = []
    for line in r.stdout.strip().splitlines():
        day, _, trailers = line.partition("\t")
        dates.add(day)
        for t in trailers.split("\x1f"):
            name = re.sub(r"\s*<[^>]*>", "", t).strip()
            if name and name not in layout:
                layout.append(name)

    def order(m: str) -> tuple:
        fam, *ver = m.split("-")[1:]
        return (fam, [-int(v) for v in ver])
    models = [_model_name(m) for m in sorted(mids, key=order)]
    models += [m for m in sorted(layout) if m not in models]
    d0, d1 = (dt.date.fromisoformat(x) for x in (min(dates), max(dates)))
    if (d0.year, d0.month) == (d1.year, d1.month):
        span = f"{d0.day} to {d1.day} {d1:%B %Y}" if d0 != d1 else f"{d1.day} {d1:%B %Y}"
    else:
        span = f"{d0.day} {d0:%B %Y} to {d1.day} {d1:%B %Y}"
    return {"models": models, "dates": span, "run_model_ids": sorted(mids), "layout_models": layout,
            "date_range": [min(dates), max(dates)]}


# ------------------------------------------------------------------ BRIEF.md

def build(answers: dict, corr: dict, bcfg: dict, faq_cfg: dict, ai: dict) -> tuple:
    rows = {str(k): v for k, v in corr["rows"].items()}
    cites = Cites(faq_cfg)
    secs = answers.get("sections") or {}

    def doc(d):
        return {"doc_id": d, "kind": "document text", "section": ""}

    evs = {nid: load_ev(f"need_{nid}.json") for nid in rows}
    a_items = {nid: asked_items(rows[nid], evs[nid]) for nid in rows}
    l_items = {nid: row_cell_items(rows[nid], evs[nid], "landed") for nid in rows}
    # The bottom line cites what its counts rest on: the asked needs' asks and levels.
    text, counts, asked = bottom_line(rows)
    REPORT["bottom_line"] = counts
    out = [f"# {TITLE}", "", f"{AUTHOR}. {PREPARED}.", "",
           text + " " + cites.mark([it for k in asked for it in a_items[k] + l_items[k]]), ""]
    REPORT["added_by_code"].append("bottom line: the answer and the counts, from the table")

    # 1 and 2: model-written, checked; one code-built sentence each, from the old "names used"
    # line. DCAT-005 decision 4: the name is cited from the published Overview, not the draft.
    s1 = kept_sentences(secs.get("1") or {}, load_ev("section_1.json"), cites)
    names = ("It is the United States version of the World Wide Web Consortium's Data Catalog Vocabulary "
             f"(DCAT). {cites.mark([doc(OVERVIEW), doc('w3c-dcat-3')])}")
    s1 = s1[:1] + [names] + s1[1:]
    out += ["## 1. What DCAT-US 3.0 is", "", " ".join(s1) if s1 else FB.NONE_KEPT, ""]
    s2 = kept_sentences(secs.get("2") or {}, load_ev("section_2.json"), cites)
    s2.append("Their joint effort is the FAIRness Project (FAIR: findable, accessible, interoperable and "
              f"reusable). {cites.mark([doc('fairness-project-wiki-home')])}")
    out += ["## 2. Who made it", "", " ".join(s2), ""]
    REPORT["added_by_code"].append("sections 1 and 2: what DCAT-US is a version of, and the FAIRness Project's name")

    # 3: the table, computed. The level's date is in the column head (DCAT-005 decision 5).
    out += ["## 3. What FCSM asked for, and where it landed", "",
            "| Statistical need | Asked for by FCSM? | Level in DCAT-US 3.0 (page of 5 October 2026) | Result |",
            "|:----|:------|:--------|:----------|"]
    for nid in sorted(rows, key=int):
        r = rows[nid]
        out.append(f"| {need_name(r)} | {asked_cell(r, a_items[nid], cites)} | "
                   f"{level_cell(r, l_items[nid], cites)} | {result_label(r)} |")
    out += ["", "What the results mean:", ""]
    out += [f"- **{k}:** {t}{LEGEND_BRIEF_TAIL.get(k, '')}" for k, t in LEGEND] + [""]
    REPORT["added_by_code"].append("section 3: the table, its plain result labels and the legend")

    # 4: the "different form" rows. Section 5 of the run (model-written over the C and D rows'
    # passages), then each different-form row's validated literature sentence that shares no
    # source with those sentences, so every such row is explained once; then the void as the
    # rule's limit (DCAT-005 decision 3).
    out += ["## 4. Where the standards carry it differently", ""]
    s5 = secs.get("5") or {}
    ev5 = load_ev("section_5.json")
    by5 = {it["id"]: it for it in ev5["items"]}
    s5_keys = {cites.key_meta(by5[e])[0] for s in s5.get("kept") or [] for e in s["evidence"]}
    lines = kept_sentences(s5, ev5, cites)
    for nid in sorted(rows, key=int):
        r = rows[nid]
        if r["literature"] != "carries_differently_than_asked":
            continue
        for x in r["items"]:
            if x["part"] == "literature" and x["kind"] == "SENTENCE" and x["kept"]:
                its = sentence_items(x, evs[nid])
                if not {cites.key_meta(it)[0] for it in its} & s5_keys:
                    lines.append(x["sentence"].rstrip() + " " + cites.mark(its))
                    REPORT["added_by_code"].append(f"section 4: the validated literature sentence of need {nid} "
                                                   f"({r['need']}), which section 5's sentences do not cover")
                break
    out += [" ".join(lines) if lines else FB.NONE_KEPT, ""]
    if void_rows(rows):
        out += ["Whether FCSM left out something the standards call for cannot be shown from the public record "
                "while the project's sequencing plan is unpublished.", ""]
        REPORT["added_by_code"].append("section 4: the void as the rule's limit")

    # 5: model-written, then the operator's two paragraphs (ADDENDUM 01 item 4).
    lines = kept_sentences(secs.get("6") or {}, load_ev("section_6.json"), cites, SUPERSEDED_BY_OPERATOR["6"])
    missing = [t for t in SUPERSEDED_BY_OPERATOR["6"] if t not in
               [s["text"].rstrip() for s in (secs.get("6") or {}).get("kept") or []]]
    if missing:
        raise SystemExit(f"FATAL: the sentence the operator's paragraph replaces is no longer kept: {missing}")
    out += ["## 5. A path forward", "", " ".join(lines) if lines else FB.NONE_KEPT, "", NEXT_STEP, "",
            CHECKING.format(c1=cites.mark([doc(OVERVIEW)])), ""]

    # 6: the needs nobody can place from the public record, by code, then the model-written
    # sentences on the plan.
    out += ["## 6. What the public record cannot show", ""]
    e = [rows[k] for k in sorted(rows, key=int) if rows[k]["outcome"] == "E"]
    if e:
        full = [r["need"] for r in e if r.get("asked_read") == "not_found_in_full_read"]
        rest = [r["need"] for r in e if r.get("asked_read") != "not_found_in_full_read"]
        words = _num(len(bcfg["scopes"]["asked"]["airkg"]))
        if full:
            out += [f"FCSM's {words} public documents, read in full, do not ask for {FB._join(full)}; the plan "
                    "below may have."]
        if rest:
            out += [f"Whether FCSM asked for {FB._join(rest)} cannot be told from the public record."]
        out += [""]
        REPORT["added_by_code"].append("section 6: the needs the public record cannot place")
    lines = kept_sentences(secs.get("7") or {}, load_ev("section_7.json"), cites)
    out += [" ".join(lines) if lines else FB.NONE_KEPT, ""]

    out += ["## AI use in this document", "", AI_USE["brief"].format(models=FB._join(ai["models"]), dates=ai["dates"]), ""]
    out += ["## Sources", ""] + cites.lines() + [""]
    return "\n".join(out), cites


# ------------------------------------------------------------------ ROWS.md

def _toks(s: str) -> set:
    w = re.findall(r"[a-z0-9]+", s.lower())
    return {x[:-1] if x.endswith("s") and len(x) > 3 else x for x in w if x not in _STOP}


def resemblance(a: str, b: str) -> float:
    ta, tb = _toks(a), _toks(b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 1.0


def dedupe(sentences: list) -> tuple:
    """Keep the first statement of each finding (ADDENDUM 02 item 1): a sentence that is an
    exact repeat of, or resembles at `NEAR_DUP_JACCARD` or more, a sentence already kept is cut.
    Returns (kept indexes, cuts with what each repeated)."""
    kept, cuts = [], []
    for i, s in enumerate(sentences):
        best = max(((resemblance(s, sentences[j]), j) for j in kept), default=(0.0, None))
        if s.strip() in {sentences[j].strip() for j in kept} or best[0] >= NEAR_DUP_JACCARD:
            cuts.append({"cut": s, "repeats": sentences[best[1]], "resemblance": round(best[0], 2),
                         "exact": s.strip() == sentences[best[1]].strip()})
        else:
            kept.append(i)
    return kept, cuts


def rows_md(corr: dict, cites: Cites, ai: dict) -> str:
    rows = {str(k): v for k, v in corr["rows"].items()}
    out = [f"# {ROWS_TITLE}", "", f"Companion to the brief of {PREPARED}. {AUTHOR}.", "",
           ROWS_HOW_TO.format(n=len(rows)), "", "The result for each need uses the brief's labels:", ""]
    out += [f"- **{k}:** {t}" for k, t in LEGEND] + [""]
    before = set(cites.refs)
    used: set = set()
    REPORT["rows_cut_as_repeats"] = {}
    for nid in sorted(rows, key=int):
        r = rows[nid]
        ev = load_ev(f"need_{nid}.json")
        label = re.sub(r"\*\*", "", result_label(r))
        out += [f"## {nid}. {need_name(r)}", "", f"**Result: {label}.**", ""]
        for part, head in (("asked", "Did FCSM ask for it?"), ("landed", "Where it landed in DCAT-US 3.0"),
                           ("literature", "What the international standards say")):
            xs = [x for x in r["items"] if x["part"] == part and x["kind"] == "SENTENCE" and x["kept"]]
            keep, cuts = dedupe([x["sentence"] for x in xs])
            if cuts:
                REPORT["rows_cut_as_repeats"].setdefault(f"{nid}. {r['need']}", []).extend(
                    {"part": part, **c} for c in cuts)
            out += [f"*{head}*", ""]
            if not keep:
                out += ["- Not confirmed by the source check.", ""]
                continue
            for i in keep:
                m = cites.mark(sentence_items(xs[i], ev))
                used |= {int(n) for n in re.findall(r"\d+", m)}
                out.append(f"- {xs[i]['sentence'].rstrip()} {m}")
            out += [""]
    new = set(cites.refs) - before
    if new:
        REPORT["rows_only_sources"] = sorted(cites.refs[k] for k in new)
    out += ["## AI use in this document", "", AI_USE["rows"].format(models=FB._join(ai["models"]), dates=ai["dates"]), ""]
    out += ["## Sources (numbered as in the brief)", ""] + cites.lines(used) + [""]
    return "\n".join(out)


# ------------------------------------------------------------------ the v2 comparison

_MARK = re.compile(r"\s*(?:\[\d+\])+")


def _structure(md: str) -> dict:
    """What ADDENDUM 01 item 5 compares: the section order, the table rows and the bottom line,
    each with citation marks removed (numbering follows first use, so marks may differ)."""
    body = md.split("\n## Sources")[0]
    heads = [ln for ln in body.splitlines() if ln.startswith("## ")]
    table = [_MARK.sub("", ln) for ln in body.splitlines() if ln.startswith("| ") and not ln.startswith("| Statistical")]
    bottom = next((_MARK.sub("", ln) for ln in body.splitlines() if ln.startswith("**Bottom line")), None)
    results = [ln for ln in body.splitlines() if ln.startswith("**Result:")]
    paras = [_MARK.sub("", ln).strip() for ln in body.splitlines()
             if ln.strip() and not ln.startswith(("#", "|"))]
    return {"sections": heads, "table": table, "bottom_line": bottom, "results": results, "paragraphs": paras}


def compare_v2(built: str, ref: str) -> dict:
    b, v = _structure(built), _structure(ref)
    return {"sections_equal": b["sections"] == v["sections"],
            "table_rows_equal": b["table"] == v["table"],
            "bottom_line_equal": b["bottom_line"] == v["bottom_line"],
            "results_equal": b["results"] == v["results"],
            "table_rows_differing": [[x, y] for x, y in zip(b["table"], v["table"]) if x != y],
            "lines_only_in_build": [p for p in b["paragraphs"] if p not in v["paragraphs"]],
            "lines_only_in_v2": [p for p in v["paragraphs"] if p not in b["paragraphs"]]}

# --------------------------------------------------------------------- plain-language gate

def body_text(md: str) -> str:
    """R8's "body", as fixed in `brief_config.yaml` before the build: every line that is not a
    heading, a table row, a source line, or the list under a heading; citation marks removed."""
    keep = []
    in_sources = False
    for line in md.splitlines():
        if line.startswith("## Sources"):
            in_sources = True
        if in_sources or line.startswith("#") or line.lstrip().startswith("|") or not line.strip():
            continue
        keep.append(re.sub(r"\[\d+\]", "", line).replace("**", ""))
    return "\n".join(keep)


def body_words(md: str) -> dict:
    """DCAT-005 decision 5's count: everything above the source list (headings and the table
    included), citation marks, table rules and bold marks removed, counted by
    `textstat.lexicon_count`."""
    import textstat
    t = re.sub(r"\[\d+\]", "", md.split("## Sources")[0])
    t = re.sub(r"\|:?-+:?", "", t).replace("|", " ").replace("**", "")
    return {"words": textstat.lexicon_count(t),
            "implementation": f"textstat {textstat.__version__}, textstat.lexicon_count, above the source list"}


def fk_grade(text: str) -> dict:
    import textstat
    return {"implementation": f"textstat {textstat.__version__}, textstat.flesch_kincaid_grade",
            "grade": round(textstat.flesch_kincaid_grade(text), 2),
            "words": textstat.lexicon_count(text), "sentences": textstat.sentence_count(text)}


ACR_RE = re.compile(r"(?<![\w-])([A-Z][A-Za-z]*[A-Z][A-Za-z0-9]*(?:-[A-Z0-9][A-Za-z0-9.]*)*)(?![\w-])")


def acronyms(md: str) -> list:
    """Every acronym in the brief above its source list, the line it first appears on, and the
    line of its expansion: "Full Name (ACR)", "ACR is ..." in the names line, or a title line
    of the form "... (ACR ...)". An acronym whose first use precedes its expansion is a finding."""
    lines = md.split("## Sources")[0].splitlines()
    first, exp = {}, {}
    for n, line in enumerate(lines, 1):
        for m in ACR_RE.finditer(line):
            a = m.group(1)
            if sum(1 for ch in a if ch.isupper()) < 2 or a in ("AI",) and False:
                continue
            first.setdefault(a, n)
        for m in re.finditer(r"\(([A-Z][A-Za-z0-9-]*[A-Z0-9][A-Za-z0-9.-]*)[^)]*\)", line):
            exp.setdefault(m.group(1).split()[0], n)
        for m in re.finditer(r"(?:^|[;:.] |\bthe )([A-Z][A-Za-z0-9-]+) (?:is|stands for) ", line):
            exp.setdefault(m.group(1), n)
    out = []
    for a, n in sorted(first.items(), key=lambda x: x[1]):
        e = exp.get(a)
        if e is None:
            # "FAIRness" is FAIR plus a lowercase suffix, and "DCAT-AP" is DCAT plus a qualifier:
            # each is expanded where its base is.
            base = next((b for b in exp if a.startswith(b + "-") or a.startswith(b + " ")
                         or (a.startswith(b) and a[len(b):].isalpha() and a[len(b):].islower())), None)
            e = exp.get(base) if base else None
        out.append({"acronym": a, "first_line": n, "expansion_line": e,
                    "ok": e is not None and e <= n})
    return out


#: Type sizes for the one-to-two page PDF (decision 5). The body stays at 10 pt; the table and
#: the source list, which the reader consults rather than reads, are set smaller. Raw typst
#: blocks in the PDF's copy of the markdown only; BRIEF.md itself is unchanged by them.
PDF_TABLE_PT, PDF_SOURCES_PT, PDF_BODY_PT = 7.5, 6.5, 9.5


def pdf_markdown(md: str) -> str:
    md = FB.strip_title(md)
    md = md.replace("| Statistical need |", f"```{{=typst}}\n#set text(size: {PDF_TABLE_PT}pt)\n#set par(justify: false)\n```\n\n| Statistical need |", 1)
    md = md.replace("What the results mean:", f"```{{=typst}}\n#set text(size: {PDF_BODY_PT}pt)\n#set par(justify: true)\n```\n\nWhat the results mean:", 1)
    return md.replace("\n## Sources", f"\n## Sources\n\n```{{=typst}}\n#set text(size: {PDF_SOURCES_PT}pt)\n```", 1)


def render_pdf(md: Path, pdf: Path, title: str) -> None:
    """`dcat_faq_build.render_pdf`'s pandoc and typst call, with the brief's margins."""
    cmd = ["pandoc", str(md), "--from=markdown+pipe_tables+raw_attribute-smart", "--pdf-engine=typst",
           "--metadata", f"title={title}", "--variable", "papersize=us-letter",
           "--variable", "header-includes=#set text(hyphenate: false)\n#show figure: set block(breakable: true)",
           "--variable", "margin-x=1.4cm", "--variable", "margin-y=1.2cm",
           "--variable", f"fontsize={PDF_BODY_PT}pt", "-o", str(pdf)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/typst failed for {md.name}:\n{r.stderr[-1500:]}")


def h1(md: str) -> str:
    m = re.match(r"\A# (.*)\n", md)
    if not m:
        raise SystemExit("FATAL: a report to render has no title line")
    return m.group(1)


def render_report(md_path: Path, pdf_path: Path, pdf_md: str) -> dict:
    """Render one reader-facing file (the base task, decision 1) from the Markdown as it stands
    on disk, through a scratch copy that carries the PDF-only typst blocks, and record what the
    PDF was rendered from: the Markdown's sha256 (git does not keep file times, so a test checks
    the PDF against its source by hash, not by mtime), the PDF's, and its page count."""
    md = md_path.read_text(encoding="utf-8")
    build_dir = OUT / "build"
    build_dir.mkdir(exist_ok=True)
    scratch = build_dir / md_path.name
    try:
        scratch.write_text(pdf_md, encoding="utf-8")
        render_pdf(scratch, pdf_path, h1(md))
    finally:
        scratch.unlink(missing_ok=True)
        build_dir.rmdir()
    return {"markdown": md_path.name, "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
            "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(), "pages": pdf_pages(pdf_path)}


def pdf_pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args(argv)
    global DRAFT_TITLE
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))
    bcfg = yaml.safe_load(EV.BRIEF_CONFIG.read_text(encoding="utf-8"))
    faq_cfg = EV.load_config()
    if not CORRECTIONS.is_file():
        raise SystemExit(f"FATAL: {CORRECTIONS.relative_to(REPO)} missing; run scripts/dcat_brief_correct.py")
    corr = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    if not corr.get("verdict") or len(corr.get("rows") or {}) != len(bcfg["needs"]):
        raise SystemExit("FATAL: the corrections overlay has no verdict; the table is not complete")
    fr = {k: v.get("status") for k, v in (corr.get("full_read") or {}).items()}
    if sorted(fr) != sorted(str(n) for n in bcfg[AMEND]["full_read"]["needs"]) or set(fr.values()) != {"done"}:
        raise SystemExit(f"FATAL: the full read is not complete for every need it names: {fr}")
    dn = bcfg[AMEND]["published"]["draft_name"]
    DRAFT_TITLE = f"{dn[:1].upper() + dn[1:]} of DCAT-US Version 3 (Candidate Recommendation Snapshot, not the published 3.0)"
    bad = [k for k, s in (answers.get("sections") or {}).items() if s.get("status") not in ("done", "none")]
    if bad or not answers.get("sections"):
        raise SystemExit(f"FATAL: sections not answered and checked: {bad or 'none run'}")
    docs = {}
    for p in sorted(EV.BRIEF_EVIDENCE_DIR.glob("*.json")):
        docs.update(json.loads(p.read_text(encoding="utf-8")).get("documents") or {})
    FB.DOCS = {**FB.all_documents(), **docs}
    gate = published_gate({str(k): v for k, v in corr["rows"].items()}, bcfg)
    if gate:
        raise SystemExit("FATAL: a 3.0 claim without a published page (DCAT-005 decision 4):\n  " + "\n  ".join(gate))
    ai = ai_use_records()
    brief, cites = build(answers, corr, bcfg, faq_cfg, ai)
    rows = rows_md(corr, cites, ai)
    found = {n: LINT.lint(t) for n, t in (("BRIEF.md", brief), ("ROWS.md", rows))}
    if any(found.values()):
        raise SystemExit("FATAL: lint (scripts/dcat_faq_lint.py) refuses the build:\n" + "\n".join(
            f"  {n}:{f['line']} [{f['rule']}] {f['match']!r} in {f['context']!r}" for n, fs in found.items() for f in fs))
    wc = body_words(brief)
    if wc["words"] > bcfg[AMEND]["max_body_words"]:
        raise SystemExit(f"FATAL: the body is {wc['words']} words, over the {bcfg[AMEND]['max_body_words']} "
                         "the amendment allows (DCAT-005 decision 5)")
    BRIEF_MD.write_text(brief, encoding="utf-8")
    ROWS_MD.write_text(rows, encoding="utf-8")
    report = {"generated_by": "scripts/dcat_brief_build.py", **REPORT,
              "operator_authored": OPERATOR_AUTHORED,
              "ai_use": ai,
              "lint": {"BRIEF.md": 0, "ROWS.md": 0, "implementation": "scripts/dcat_faq_lint.py"},
              "readability": {**fk_grade(body_text(brief)), "target_grade": bcfg["readability"]["target_grade"],
                              "body": "lines of BRIEF.md that are not headings, table rows or sources; citation marks removed"},
              "body_words": {**wc, "max": bcfg[AMEND]["max_body_words"]},
              "published_gate": "passed: every landed and 3.0 literature cell cites a published page",
              "acronyms": acronyms(brief),
              "compared_with_v2": {V2_BRIEF.name: compare_v2(brief, V2_BRIEF.read_text(encoding="utf-8")),
                                   V2_ROWS.name: compare_v2(rows, V2_ROWS.read_text(encoding="utf-8"))}}
    if not a.no_pdf:
        report["pdfs"] = {BRIEF_PDF.name: render_report(BRIEF_MD, BRIEF_PDF, pdf_markdown(brief)),
                          ROWS_PDF.name: render_report(ROWS_MD, ROWS_PDF, FB.strip_title(rows))}
        if DEMO_MD.is_file():
            # No script writes DEMO.md (hand-written 7 October 2026); the build renders it so
            # its PDF never goes stale against it.
            demo = DEMO_MD.read_text(encoding="utf-8")
            report["pdfs"][DEMO_PDF.name] = {**render_report(DEMO_MD, DEMO_PDF, FB.strip_title(demo)),
                                             "note": "DEMO.md is hand-written; no script writes it. Rendered as found."}
        else:
            report["pdfs"][DEMO_PDF.name] = {"note": "DEMO.md not present; nothing rendered"}
        report["pdf_pages"] = report["pdfs"][BRIEF_PDF.name]["pages"]
    BUILD_REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("readability", "body_words", "bottom_line") if k in report}, indent=1))
    print("pages:", {k: v.get("pages") for k, v in (report.get("pdfs") or {}).items()})
    print("acronyms not expanded before first use:",
          [x["acronym"] for x in report["acronyms"] if not x["ok"]])
    for name, c in report["compared_with_v2"].items():
        print(name, {k: v for k, v in c.items() if k.endswith("_equal")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
