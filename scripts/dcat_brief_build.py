#!/usr/bin/env python3
"""Build the DCAT-US 3.0 plain-language brief from the checked answers. **Zero spend, no
network.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decisions 4 to 6,
implementing DN-011 ADDENDUM 01 R6 to R8. Reads `reports/dcat_us_3_brief/answers.json`
(written by `scripts/dcat_brief_run.py`), the evidence files and `brief_config.yaml`, and
writes under `reports/dcat_us_3_brief/`:

* `BRIEF.md` / `BRIEF.pdf`: the eight sections in decision 5's order. Sections 1, 2, 5, 6 and 7
  print the sentences the validator kept, verbatim. Sections 3, 4 and 8, and the list of
  outcome-E needs in section 7, are built by code from the table: the yes-or-no is computed
  (R7), the table's cells are read off the validated codes, and the five outcomes are explained
  in the config's own sentences.
* `ROWS.md`: each need's three validated sentences with their sources, the detail behind a
  table row.
* `build_report.json`: what the code added, the plain-language gate (lint, Flesch-Kincaid grade
  with its implementation named, each acronym with the line of its expansion), page count.

**DCAT-005** (`cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb.md`): the rows and the
yes-or-no are read from the overlay `run/corrections.json` (`scripts/dcat_brief_correct.py`),
never from DCAT-004 v2's `answers.json` alone; R7 is applied as written, so an answer may be
"not decided", printed with what would decide it (decision 2); section 5 states the void as the
rule's limit, not as a finding (decision 3); every table cell that says what 3.0 carries cites a
published page, the 2025 working draft is named as such, and the build refuses otherwise
(decision 4); and the body is held to the amendment's word limit, also refused over it
(decision 5).

Citations are the FAQ's form (`scripts/dcat_faq_build.py` `citation`, `canonical`), one
numbered list at the end. The lint is DCAT-003 ADDENDUM 01's (`scripts/dcat_faq_lint.py`) and
refuses the build on any finding, before any file is written.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_build.py [--no-pdf]
"""
from __future__ import annotations

import argparse
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
#: The published Overview as served 2026-10-05, which names DCAT-US (DCAT-005 decision 4).
OVERVIEW = "dcat-us-3-overview-2026-10-05"
AMEND = "amendment_2026_10_07_dcat005"
BRIEF_MD, BRIEF_PDF, ROWS_MD = OUT / "BRIEF.md", OUT / "BRIEF.pdf", OUT / "ROWS.md"
BUILD_REPORT = OUT / "build_report.json"
PREPARED = "7 October 2026"
TITLE = "The federal data catalog standard (DCAT-US 3.0) and statistics: a short brief"

#: Short names for the documents a table cell cites, so a cell can say who says it. Every
#: acronym here is expanded in the "Names used" line the build prints before the table.
SHORT = [
    (r"^statdcat-ap", "StatDCAT-AP"), (r"^sdmx-", "SDMX"), (r"^ddi-", "DDI"),
    (r"^w3c-rdf-data-cube", "W3C Data Cube"), (r"^w3c-dqv", "W3C Data Quality Vocabulary"),
    (r"^w3c-dwbp", "W3C Data on the Web Best Practices"), (r"^w3c-dcat-3|^w3c_dcat_3", "W3C DCAT 3"),
    (r"^wilkinson-2016", "FAIR principles"), (r"^jacobsen-2020", "FAIR interpretations"),
    (r"^dcat-ap-", "DCAT-AP"), (r"^s-015", "quality crosswalk"),
    (r"^fcsm-19-01", "FCSM 19-01"), (r"^fcsm-20-04|^fcsm_20_04", "FCSM 20-04"),
    (r"^fcsm-23-02", "FCSM 23-02"), (r"^fcsm-25-03|^fcsm_25_03", "FCSM 25-03"),
    (r"^fairness-project-wiki|^fairness_project_wiki", "FAIRness Project wiki"),
    (r"^fcsm-2024-b3-3", "FAIRness Project slides, 2024"),
    (r"^cdoc-dswg", "CDO Council data sharing report, 2022"),
    (r"^dcat-us-3-implementation-guide|^dcat_us_3_implementation_guide", "Implementation Guide"),
    (r"^dcat-us-3-candidate", "2025 working draft"), (r"^dcat-us-3-dataset-series", "Dataset Series page"),
    (r"^dcat-us-3-quality-governance", "Quality and Governance page"),
    (r"^dcat-us-3-temporal-spatial", "Temporal, Spatial and Metrics page"),
    (r"^dcat-us-3-overview", "Overview page"), (r"^dcat-us-3-dataset-schema", "Dataset page"),
]
#: Expansions for the "Names used" line, each from the named document's own title.
EXPANSIONS = {
    "DCAT": "Data Catalog Vocabulary, a World Wide Web Consortium (W3C) standard; DCAT-US is its United States version",
    "FCSM": "the Federal Committee on Statistical Methodology",
    "CDO": "Chief Data Officers",
    "SDMX": "Statistical Data and Metadata eXchange",
    "DDI": "Data Documentation Initiative",
    "DCAT-AP": "the European Union's version of DCAT",
    "StatDCAT-AP": "the European Union's statistical version of DCAT",
    "FAIR": "Findable, Accessible, Interoperable and Reusable",
    "W3C": "the World Wide Web Consortium",
}
LANDED_WORD = {"mandatory": "Mandatory", "recommended": "Recommended", "optional": "Optional",
               "dropped": "Dropped", "absent": "Left out"}
LIT_WORD = {"matches": "{s} {v} it, and 3.0 does too",
            "carries_3_0_does_not": "{s} {v} it; 3.0 does not",
            "carries_differently_than_asked": "{s} {v} it differently from the ask",
            "not_at_catalog_layer": "Belongs in the data or its documentation ({s})"}
REPORT: dict = {"added_by_code": [], "cut_by_build": []}
#: The working draft's source line (DCAT-005 decision 4). Set from the amendment in `main`.
DRAFT_TITLE = "The 2025 working draft of DCAT-US Version 3 (Candidate Recommendation Snapshot, not the published 3.0)"


def short(doc_id: str) -> str:
    for pat, name in SHORT:
        if re.search(pat, doc_id):
            return name
    return doc_id


class Cites:
    """One numbered source list for the whole brief, in first-use order (the FAQ's citation
    form, `dcat_faq_build.citation`)."""

    def __init__(self, faq_cfg: dict):
        self.cfg, self.refs, self.metas, self.secs = faq_cfg, {}, {}, {}

    def mark(self, items: list) -> str:
        nums = []
        for it in items:
            if it["kind"] == "crosswalk row":
                key, meta = "s015", {"title": "S-015 readiness crosswalk: the presenter's own "
                                              "crosswalk of quality terms (unpublished), quoting "
                                              "W3C and ISO/IEC 25012 definitions",
                                     "issuer": "", "date": "14 September 2026", "url": ""}
            elif it["kind"] == "element table row":
                key, meta = "table", {"title": "Requirement level of each Dataset element, read from four "
                                               "versions of the DCAT-US Dataset page and schema (v1.1; 2025 "
                                               "working draft; pages of 21 August, 15 September and 5 October "
                                               "2026), as tabled in the attachment to the questions-and-answers "
                                               "paper of 5 October 2026", "issuer": "", "date": "", "url": ""}
            elif it["kind"] == "catalog record (not admitted)":
                # The record's own fields, as the FAQ's question 14 prints them; its notes are
                # the cataloguer's working text and are not a citation (the 2026-10-05 lint
                # defect, scripts/dcat_faq_lint.py).
                rec = it.get("record") or {}
                key, meta = f"catalog:{it['doc_id']}", {
                    "title": f"{rec.get('title')} (not published)", "issuer": rec.get("issuer") or "",
                    "date": FB._plain_date(rec.get("date")), "url": ""}
            else:
                key, meta = FB.canonical(it, FB.DOCS, self.cfg)
                if it["doc_id"] == EV.DRAFT:
                    # DCAT-005 decision 4: cited only as the working draft, never as 3.0.
                    meta = {**meta, "title": DRAFT_TITLE}
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

    def lines(self) -> list:
        return [f"{n}. {FB.citation(self.metas[k], self.secs[k])}" for k, n in self.refs.items()]


def load_ev(name: str) -> dict:
    return json.loads((EV.BRIEF_EVIDENCE_DIR / name).read_text(encoding="utf-8"))


def kept_section(sec: dict, ev: dict, cites: Cites) -> list:
    by = {it["id"]: it for it in ev["items"]}
    return [FB.shown(s["text"], -1, {}).rstrip() + " " + cites.mark([by[e] for e in s["evidence"]])
            for s in sec.get("kept") or []]


def row_cell_items(row: dict, ev: dict, part: str) -> list:
    """The passages a cell cites: its kept sentence's, from the evidence file the sentence was
    checked against (the need's own, or its full-read file, DCAT-005 decision 1)."""
    for x in row["items"]:
        if x["part"] == part and x["kind"] == "SENTENCE" and x["kept"]:
            src = load_ev(x["evidence_file"]) if x.get("evidence_file") else ev
            by = {it["id"]: it for it in src["items"]}
            return [by[e] for e in x["evidence"]]
    return []


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


def outcome_cell(r: dict) -> str:
    if r["outcome"] == "unplaced":
        return "Not placed: " + " or ".join(x for x in r["open"] if x != "outside_rule")
    if r["outcome"] == "unassigned":
        return "Not placed"
    return r["outcome"]


def row_range(ids: list) -> str:
    """The rows an answer rests on, as R7 asks them named: "rows 1 to 3", "rows 4 and 7"."""
    return (f"rows {ids[0]} to {ids[-1]}" if len(ids) > 2 and ids == list(range(ids[0], ids[-1] + 1))
            else "rows " + FB._join([str(i) for i in ids]))


def _where(r: dict) -> str:
    return "not placed" if r["outcome"] in ("unplaced", "unassigned") else f"now {r['outcome']}"


def grounds(name: str, v: dict, rows: dict, bcfg: dict) -> str:
    """R7's grounds, computed: which needs count, then, for an answer the rule decides, where
    each is; for one it does not decide, what each row would need to become (DCAT-005
    decision 2: `partly_if` and `no_needs` from `dcat_brief_run.verdict`)."""
    ids = v["rows"]
    out = []
    if v["determined"]:
        for i in ids:
            r = rows[str(i)]
            out.append(f"{r['need'][:1].upper() + r['need'][1:]} is in outcome {r['outcome']}.")
        return " ".join(out)
    no = [f"{rows[str(x['row'])]['need']} (row {x['row']}, {_where(rows[str(x['row'])])})" for x in v["no_needs"]]
    each = "were each" if len(no) > 1 else "were"
    if v["partly_if"]:
        pa = FB._join([f"{rows[str(i)]['need']} (row {i})" for i in v["partly_if"]])
        out.append(f"The rule would say \u201cpartly\u201d if {pa} were in A. It would say \u201cno\u201d if "
                   f"{FB._join(no)} {each} in B, C or E.")
    else:
        out.append(f"The rule would say \u201cno\u201d only if {FB._join(no)} {each} in B, C or E. "
                   "No row can be in A.")
    return " ".join(out)


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


def build(answers: dict, corr: dict, bcfg: dict, faq_cfg: dict) -> tuple:
    rows = {str(k): v for k, v in corr["rows"].items()}
    cites = Cites(faq_cfg)
    secs = answers.get("sections") or {}
    def doc(d):
        return {"doc_id": d, "kind": "document text", "section": ""}
    # DCAT-005 decision 4: the name is cited from the published Overview ("a U.S. application
    # profile of the W3C Data Catalog Vocabulary (DCAT) version 3"), not from the working draft.
    out = [f"# {TITLE}", "",
           "Names used. DCAT-US is the United States version of the Data Catalog Vocabulary (DCAT) of the "
           f"World Wide Web Consortium (W3C) {cites.mark([doc(OVERVIEW), doc('w3c-dcat-3')])}. FAIR stands for "
           "findable, accessible, interoperable and reusable. The FAIRness Project is the federal Chief Data "
           "Officers Council's project with the Federal Committee on Statistical Methodology (FCSM) "
           f"{cites.mark([doc('fairness-project-wiki-home')])}.", "",
           f"Prepared {PREPARED} for the Office of Management and Budget. One artificial intelligence model "
           "wrote each sentence from the documents listed at the end. Two others checked it. A sentence "
           "they did not both confirm was cut. The questions-and-answers paper of 5 October 2026 and the "
           "companion rows file quote every passage.", ""]
    names_used = []

    def section(k: int, title: str):
        out.extend([f"## {k}. {title}", ""])

    # 1 and 2: model-written, checked.
    for k, title in ((1, "What DCAT-US 3.0 is"), (2, "Who made it")):
        section(k, title)
        s = secs.get(str(k)) or {}
        ev = load_ev(f"section_{k}.json")
        lines = kept_section(s, ev, cites)
        out += [" ".join(lines) if lines else FB.NONE_KEPT, ""]
    # 3: computed (R7).
    section(3, "Does it deliver for statistics?")
    v = corr["verdict"]
    for name, label in (("findability", "Finding statistical data"),
                        ("fitness_for_use", "Judging whether data are fit for a use")):
        out += [f"**{label} ({row_range(v[name]['rows'])}): {v[name]['answer']}.** "
                f"{grounds(name, v[name], rows, bcfg)}", ""]
    out += ["A rule fixed in advance, not a model, reads the table in section 4. It says \u201cno\u201d if "
            "every need is in outcome B, C or E, and \u201cpartly\u201d if at least one is in A. Otherwise it does not "
            "decide.", ""]
    REPORT["added_by_code"].append("section 3: both answers and their grounds, from the table")
    # 4: the table, computed.
    section(4, "The statistical needs, by outcome")
    table, used = [], set()
    for nid in sorted(rows, key=int):
        r = rows[nid]
        ev = load_ev(f"need_{nid}.json")
        # Every kept ask, not the first: the full read (DCAT-005 decision 1) can keep asks from
        # several documents, and the cell names each.
        a_items = [it for x in r["items"] if x["part"] == "asked" and x["kind"] == "SENTENCE" and x["kept"]
                   for it in row_cell_items({"items": [x]}, ev, "asked")]
        l_items = row_cell_items(r, ev, "landed")
        t_items = row_cell_items(r, ev, "literature")
        if r["asked"] is None:
            asked = "Not confirmed"
        elif r["asked"] == "asked":
            who = sorted({short(it["doc_id"]) for it in a_items})
            asked = f"Yes: {FB._join(who)} {cites.mark(a_items)}"
        elif r["asked"] == "publicly_not_asked":
            asked = f"No, on the record {cites.mark(a_items)}"
        elif r.get("asked_read") == "not_found_in_full_read":
            asked = "Not in public documents (read in full)"
        else:
            asked = "Not in the public record"
        if r["landed"] is None:
            landed = "Not confirmed"
        else:
            names = [e.split()[-1] for e in r.get("elements") or []] if r["landed"] != "absent" else []
            els = names[0] + (f" and {len(names) - 1} more" if len(names) > 1 else "") if names else ""
            landed = (LANDED_WORD[r["landed"]] + (f" ({els})" if els else "")
                      + (", put off to a later version" if r["deferred"] else ""))
            landed += f" {cites.mark(l_items)}" if l_items else ""
        stds = sorted({short(it["doc_id"]) for it in t_items if it.get("part") == "literature"})
        used |= set(stds) | {short(it["doc_id"]) for it in a_items}
        lit = ("Not confirmed" if r["literature"] is None else
               LIT_WORD[r["literature"]].format(s=FB._join(stds) if stds else "The standards",
                                                 v="carries" if len(stds) == 1 else "carry") + " " + cites.mark(t_items))
        table.append(f"| {r['need']} | {asked} | {landed} | {lit.strip()} | {outcome_cell(r)} |")
    acr = [a for a in ("FCSM", "CDO", "SDMX", "DDI", "DCAT-AP", "StatDCAT-AP", "FAIR", "W3C")
           if any(re.search(rf"(?<![\w-]){re.escape(a)}(?![\w-])", u) for u in used | {"FCSM"})]
    acr = [a for a in acr if a not in ("FCSM", "W3C", "FAIR")]      # expanded in the opening names
    names_used = acr
    # The level's date is in the column head (DCAT-005 decision 5): the levels are the published
    # Dataset page's, as served on 5 October 2026.
    out += (["; ".join(f"{a} is {EXPANSIONS[a]}" for a in acr) + ".", ""] if acr else []) + [
            "| Need | Asked for in public? | Where it landed in 3.0 (page of 5 October 2026) | What the standards say | Outcome |",
            "|:----|:------|:--------|:----------|:----|", *table, ""]
    outcomes = bcfg[AMEND].get("outcomes") or bcfg["outcomes"]
    out += ["The five outcomes:", ""] + [f"- **{k}.** {t}" for k, t in outcomes.items()] + [""]
    if any(r["outcome"] in ("unplaced", "unassigned") for r in rows.values()):
        out += ["\u201cNot confirmed\u201d: the check could not confirm it in two tries. \u201cNot "
                "placed\u201d: the outcomes still possible are shown.", ""]
    REPORT["added_by_code"].append("section 4: the table and the outcome sentences (config)")
    # 5: model-written over the C and D rows' passages, or a computed line.
    section(5, "The void and the mismatch")
    s5 = secs.get("5") or {}
    if s5.get("status") == "none":
        out += ["No need fell in outcome C (the void) or outcome D (the mismatch) under the rule.", ""]
        REPORT["added_by_code"].append("section 5: no C or D row")
    else:
        cd = {x: [rows[k]["need"] for k in sorted(rows, key=int) if rows[k]["outcome"] == x] for x in "CD"}
        lead = []
        if cd["D"]:
            lead.append(f"{FB._join(cd['D'])[:1].upper() + FB._join(cd['D'])[1:]} "
                        f"{'is' if len(cd['D']) == 1 else 'are'} in outcome D, the mismatch.")
        if cd["C"]:
            lead.append(f"{FB._join(cd['C'])} {'is' if len(cd['C']) == 1 else 'are'} in outcome C, the void.")
        vr = void_rows(rows)
        if vr:
            # DCAT-005 decision 3: the void as the rule's limit. R6 question 1 records a need the
            # unpublished plan may have asked for as not knowable, so no need can be shown not
            # asked, and C cannot be reached from the public record.
            lead.append("Whether the statistical side left out a need the standards call for (outcome C, the "
                        "void) cannot be shown while the plan is unpublished. That is open for "
                        f"{FB._join([rows[k]['need'] for k in vr])} "
                        f"({'row' if len(vr) == 1 else 'rows'} {FB._join(vr)}).")
        REPORT["added_by_code"].append("section 5: the lead sentences naming the D rows and the rows the void "
                                       "cannot be ruled out for")
        lines = kept_section(s5, load_ev("section_5.json"), cites)
        out += [" ".join(lead), "", " ".join(lines) if lines else FB.NONE_KEPT, ""]
    # 6: model-written.
    section(6, "What could happen next")
    lines = kept_section(secs.get("6") or {}, load_ev("section_6.json"), cites)
    out += [" ".join(lines) if lines else FB.NONE_KEPT, ""]
    # 7: the E rows by code, then the model-written sentences on the plan.
    section(7, "What the public record cannot show")
    e = [rows[k]["need"] for k in sorted(rows, key=int) if rows[k]["outcome"] == "E"]
    if e:
        full = [rows[k]["need"] for k in sorted(rows, key=int)
                if rows[k]["outcome"] == "E" and rows[k].get("asked_read") == "not_found_in_full_read"]
        rest = [x for x in e if x not in full]
        n_docs = len(bcfg["scopes"]["asked"]["airkg"])
        words = {8: "eight"}.get(n_docs, str(n_docs))
        if full:
            n = FB._join(full)
            out += [f"{n[:1].upper() + n[1:]} {'is' if len(full) == 1 else 'are'} in outcome E. The statistical "
                    f"side's {words} public documents, read in full, do not ask for "
                    f"{'it' if len(full) == 1 else 'them'}. The plan below may have."]
        if rest:
            out += [f"Whether the statistical side asked for {FB._join(rest)} cannot be told from the public "
                    "record (outcome E in the table)."]
        out += [""]
        REPORT["added_by_code"].append("section 7: the outcome-E needs, and the full read behind them")
    lines = kept_section(secs.get("7") or {}, load_ev("section_7.json"), cites)
    out += [" ".join(lines) if lines else FB.NONE_KEPT, ""]
    # 8 (DCAT-004 v2's "Where the detail is") is folded into the opening paragraph: DCAT-005
    # decision 5, two pages, cut repetition first.
    out += ["## Sources", ""] + cites.lines() + [""]
    return "\n".join(out), names_used, cites


def rows_md(corr: dict, bcfg: dict, faq_cfg: dict) -> str:
    cites = Cites(faq_cfg)
    out = ["# The table's rows, in detail", "",
           f"Prepared {PREPARED}. For each statistical need: the answers the check confirmed, each "
           "with its sources, and the outcome the rule assigns.", ""]
    for nid in sorted(corr["rows"], key=lambda x: int(x)):
        r = corr["rows"][nid]
        out += [f"## {nid}. {r['need']}: {outcome_cell(r).replace('Not placed', 'not placed') if r['outcome'] in ('unplaced', 'unassigned') else 'outcome ' + r['outcome']}", ""]
        if r.get("reason"):
            out += [f"Why it is not placed: {r['reason'].replace('by the panel', 'by the check')}.", ""]
        ev = load_ev(f"need_{nid}.json")
        for x in r["items"]:
            if not x["kept"] or x["part"] == "not_known":
                continue
            src = load_ev(x["evidence_file"]) if x.get("evidence_file") else ev
            by = {it["id"]: it for it in src["items"]}
            label = {"asked": "Asked for?", "landed": "Where it landed", "literature": "What the standards say"}[x["part"]]
            out += [f"- **{label}** {x['sentence']} {cites.mark([by[e] for e in x['evidence']])}".rstrip()]
        out += [""]
    out += ["## Sources", ""] + cites.lines() + [""]
    return "\n".join(out)


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
    md = md.replace("| Need |", f"```{{=typst}}\n#set text(size: {PDF_TABLE_PT}pt)\n#set par(justify: false)\n```\n\n| Need |", 1)
    md = md.replace("The five outcomes:", f"```{{=typst}}\n#set text(size: {PDF_BODY_PT}pt)\n#set par(justify: true)\n```\n\nThe five outcomes:", 1)
    return md.replace("## Sources", f"## Sources\n\n```{{=typst}}\n#set text(size: {PDF_SOURCES_PT}pt)\n```", 1)


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
    brief, names, _ = build(answers, corr, bcfg, faq_cfg)
    rows = rows_md(corr, bcfg, faq_cfg)
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
              "lint": {"BRIEF.md": 0, "ROWS.md": 0, "implementation": "scripts/dcat_faq_lint.py"},
              "readability": {**fk_grade(body_text(brief)), "target_grade": bcfg["readability"]["target_grade"],
                              "body": "lines of BRIEF.md that are not headings, table rows or sources; citation marks removed"},
              "body_words": {**wc, "max": bcfg[AMEND]["max_body_words"]},
              "published_gate": "passed: every landed and 3.0 literature cell cites a published page",
              "acronyms": acronyms(brief)}
    if not a.no_pdf:
        build_dir = OUT / "build"
        build_dir.mkdir(exist_ok=True)
        (build_dir / "brief.md").write_text(pdf_markdown(brief), encoding="utf-8")
        render_pdf(build_dir / "brief.md", BRIEF_PDF, TITLE)
        (build_dir / "brief.md").unlink()
        build_dir.rmdir()
        report["pdf_pages"] = pdf_pages(BRIEF_PDF)
    BUILD_REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("readability", "pdf_pages") if k in report}, indent=1))
    print("acronyms not expanded before first use:",
          [x["acronym"] for x in report["acronyms"] if not x["ok"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
