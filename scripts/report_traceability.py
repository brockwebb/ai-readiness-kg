#!/usr/bin/env python3
"""Does the graph link each reported check to a construct, a definition and a primary source?
**Read-only, zero spend, no network beyond Neo4j.**

`cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 5: *measured and reported, not
gated*. For each of the six tier-0 legs and A3, state by Cypher whether the rule's indicator
node reaches a construct, a definition or a source node — the survey item -> construct ->
definition -> primary source crosswalk this repo's CLAUDE.md calls the validity layer. Where the
answer is "no edge", the RESULT says so and the report is not changed for it.

**The "Sources per check" appendix is generated here** (`cc_tasks/2026-09-11_report_sources_
appendix.md` decision 1): one row per (check, admitted source) for every check the report
carries — the seven legs above plus every product leg the prose names by a
`{{result:scan_l0_product_<leg>_...}}` tag — the source rendered as a citation from
`corpus/manifest.json` (decision 2) and the locator read from the indicator's evidence cell in
the framework of record. Nothing in it is authored: a document missing a metadata field renders
with what it has and the gap is reported; a check that reaches no admitted source gets a row
that says so rather than no row. `build_l0_report.build` writes it beside the matrices as
`docs/reports/generated/sources_per_check.md`.

    /opt/anaconda3/bin/python3 scripts/report_traceability.py [--cycle scan_2026-09-10_rj2]
    /opt/anaconda3/bin/python3 scripts/report_traceability.py --appendix   # print the fragment
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
MANIFEST = REPO / "corpus" / "manifest.json"
SECTIONS = REPO / "docs" / "reports" / "sections"
FRAGMENT = REPO / "docs" / "reports" / "generated" / "sources_per_check.md"

#: The report's six host-level checks, plus the product check decision 4 writes a paragraph
#: about. The report names these and no others as its own legs.
LEGS = ["A4", "A5", "A10", "A11-declared", "A12", "G1-D", "A3"]

Q = """
MATCH (i:AssessmentIndicator {code: $code})
// The construct DECOMPOSES INTO the indicator, not the other way round: a criterion
// decomposes into constructs and a construct into indicators. Written the wrong way round
// once here, which reported every leg as having no construct.
OPTIONAL MATCH (c:AssessmentConstruct)-[:DECOMPOSES_INTO]->(i)
OPTIONAL MATCH (crit:AssessmentCriterion)-[:DECOMPOSES_INTO]->(c)
OPTIONAL MATCH (i)-[:EVIDENCED_BY]->(d:Document)
OPTIONAL MATCH (i)-[:MEASURED_BY]->(m:MeasurementSpec)
OPTIONAL MATCH (r:Rule)-[:MEASURES]->(i)
// `(Document)-[:DEFINES]->(Definition)`, not the reverse: the document is where the
// definition is stated. Written the other way round once here, which reported every leg as
// reaching no definition when two of them reach hundreds.
OPTIONAL MATCH (i)-[:EVIDENCED_BY]->(:Document)-[:DEFINES]->(def:Definition)
OPTIONAL MATCH (i)-[:EVIDENCED_BY_INTERNAL]->(x:AssessmentInternalRef)
RETURN i.construct AS construct_property,
       count(DISTINCT c) AS constructs,
       count(DISTINCT crit) AS criteria,
       count(DISTINCT def) AS definitions,
       count(DISTINCT d) AS sources,
       count(DISTINCT m) AS specs,
       count(DISTINCT r) AS rules,
       count(DISTINCT x) AS internal_refs,
       collect(DISTINCT coalesce(c.name, c.construct))[..4] AS construct_names,
       collect(DISTINCT d.doc_id)[..4] AS source_ids,
       collect(DISTINCT d.doc_id) AS all_source_ids
"""

#: A leg whose FRAMEWORK code is not its leg code. `A11-declared` is one half of indicator A11 —
#: the report measures the DECLARED layer only — and there is no `A11-declared` indicator node.
#: Declared here rather than discovered by a fuzzy match, so a leg with no indicator at all
#: reports as one instead of being silently paired with a neighbour.
FRAMEWORK_CODE = {"A11-declared": "A11"}


#: A product leg the report's prose names, as the tag it names it by. The product matrix
#: carries ten legs; the appendix lists the ones the prose quotes a rate for, because those are
#: the checks the report makes a claim about in words.
_PROSE_PRODUCT_TAG = re.compile(r"\{\{result:scan_l0_product_([a-z]\d{1,2})_")


def product_legs_named_by_prose(sections_dir: Path = SECTIONS) -> list:
    """Product legs the section prose names by a `{{result:scan_l0_product_<leg>_...}}` tag,
    in code order, excluding any already in `LEGS`."""
    found = set()
    for f in sorted(sections_dir.glob("*.md")):
        found |= {m.upper() for m in _PROSE_PRODUCT_TAG.findall(f.read_text(encoding="utf-8"))}
    return sorted(found - set(LEGS))


def appendix_legs() -> list:
    """Every check the report carries: the seven pinned legs, then the prose-named product legs."""
    return LEGS + product_legs_named_by_prose()


def measure(session, legs: list | None = None) -> dict:
    """`{leg: row}` for every leg the report publishes. **The one measurement, one place.**

    `main` prints it and `tests/test_report_traceability.py` asserts its shape
    (`cc_tasks/2026-09-11_a3_a10_sources.md` decision 5). A test that re-derived the query
    would be checking its own copy of it, and the two Cypher directions this file got wrong on
    the first pass are exactly the kind of thing a second copy preserves. `legs` defaults to
    `LEGS`; the appendix passes `appendix_legs()`.
    """
    out = {}
    for leg in (legs or LEGS):
        code = FRAMEWORK_CODE.get(leg, leg)
        rows = list(session.run(Q, code=code))
        row = dict(rows[0]) if rows else {}
        exists = bool(session.run(
            "MATCH (i:AssessmentIndicator {code:$c}) RETURN count(i) AS n",
            c=code).single()["n"])
        out[leg] = {"framework_code": code, "indicator_node": exists, **row}
    return out


# ---------------------------------------------------------------------------
# The "Sources per check" appendix
# ---------------------------------------------------------------------------

#: A backticked doc_id in an evidence cell, optionally followed by its locator in parentheses:
#: `w3c-dwbp-2017` (BP 17, provide bulk download: "...").  The locator is whatever the cell's
#: author put in the parentheses; balanced, so a quoted phrase with its own parenthesis inside
#: is kept whole.
_CELL_DOCID = re.compile(r"`([a-z0-9][a-z0-9._-]{6,})`")


def locators(evidence_raw: str) -> dict:
    """`{doc_id: locator}` for every backticked slug in an evidence cell that is followed by a
    parenthetical; a slug with none maps to ''."""
    out = {}
    for m in _CELL_DOCID.finditer(evidence_raw):
        doc = m.group(1)
        i = m.end()
        while i < len(evidence_raw) and evidence_raw[i] == " ":
            i += 1
        loc = ""
        if i < len(evidence_raw) and evidence_raw[i] == "(":
            depth, j = 0, i
            while j < len(evidence_raw):
                if evidence_raw[j] == "(":
                    depth += 1
                elif evidence_raw[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            loc = evidence_raw[i + 1:j].strip() if depth == 0 else ""
        out.setdefault(doc, loc)
    return out


#: The manifest identity fields a citation is rendered from, in the order they print. The task
#: names `primary_url`; the manifest's field is `source_url` (the projection from the dixie
#: ledger), and that is what is read.
CITATION_FIELDS = ("authors_or_org", "title", "pub_year", "source_url")


def citation(entry: dict) -> tuple:
    """(markdown citation, missing fields) from a manifest entry's `identity`. Fields present
    render; nothing is typed to fill a gap."""
    ident = entry.get("identity") or {}
    year = str(ident.get("pub_year") or "")
    # `n.d.` is the manifest's own "no date" and `(unspecified)` its "no author"; a placeholder
    # is a missing field, not a value to print.
    has_year = bool(re.match(r"\d{4}", year))
    who = ident.get("authors_or_org")
    who = [w for w in (who if isinstance(who, list) else [who] if who else [])
           if w and not _PLACEHOLDER.match(str(w))]
    missing = [f for f in CITATION_FIELDS
               if (not has_year if f == "pub_year" else
                   not who if f == "authors_or_org" else not ident.get(f))]
    parts = []
    if who:
        parts.append("; ".join(who))
    if ident.get("title"):
        parts.append(f"*{ident['title']}*")          # `_cell` is applied once, at the join
    if has_year:
        parts.append(year[:4])
    if ident.get("source_url"):
        # An autolink: clickable in the PDF, the URL itself in the markdown. typst breaks link
        # text at punctuation to keep it in the column, which would split a numeral inside the
        # URL; `build_report_pdf.render` boxes every digit run so it cannot.
        parts.append(f"<{ident['source_url']}>")
    # `et al.` already ends in a period; joining on ". " must not double it.
    return ". ".join(_cell(x).rstrip(".") for x in parts) + ".", missing


_PLACEHOLDER = re.compile(r"^\(?\s*(unspecified|unknown|n\.?\s?d\.?|none|-+)\s*\)?$", re.I)


def _cell(text: str) -> str:
    """Table-safe: a pipe would split the cell, a newline would end the row."""
    return re.sub(r"\s+", " ", str(text)).replace("|", "\\|").strip()


def sources_appendix(session, framework: dict | None = None, manifest: dict | None = None) -> tuple:
    """(fragment markdown, report). The report carries `legs`, `rows`, `legs_without_source`,
    `missing_fields` by doc_id, and `doc_ids_not_in_manifest` — the last is FATAL to the
    caller, because a citation a stranger cannot follow is the thing this appendix exists to
    rule out."""
    framework = framework or json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    manifest = manifest or json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
    inds = {n["properties"]["code"]: n["properties"] for n in framework["nodes"]
            if "AssessmentIndicator" in n["labels"]}
    legs = appendix_legs()
    table = measure(session, legs)
    rows, legs_without, missing_fields, not_in_manifest = [], [], {}, []
    for leg in legs:
        code = FRAMEWORK_CODE.get(leg, leg)
        ind = inds.get(code) or {}
        locs = locators(ind.get("evidence_raw") or "")
        indicator = f"{code} · {_cell(ind.get('construct') or '')}".rstrip(" ·")
        sources = sorted(table[leg].get("all_source_ids") or [])
        if not sources:
            legs_without.append(leg)
            rows.append((leg, indicator, "no admitted source", "", ""))
            continue
        for doc in sources:
            entry = manifest.get(doc)
            if entry is None:
                not_in_manifest.append((leg, doc))
                continue
            cite, miss = citation(entry)
            if miss:
                missing_fields[doc] = miss
            rows.append((leg, indicator, cite, doc, _cell(locs.get(doc, ""))))
    lines = [
        "One row per check and admitted source: the check as the report names it, the framework "
        "indicator it measures, the source as the corpus manifest records it, its document id "
        "in the manifest, and the locator inside the source as the indicator's evidence cell "
        "states it. Generated from the graph; nothing in this table is typed.",
        "",
        "| Check | Indicator | Source | doc_id | Locator |",
        # Relative column widths, which pandoc reads off the separator when a row is wider
        # than the page: the Source column carries a whole citation and needs the room, or
        # every column collapses to a fifth of the page and wraps every four words.
        "|-----|--------------|----------------------------------------------|-----------------|------------------|",
    ]
    for leg, ind, cite, doc, loc in rows:
        lines.append(f"| {leg} | {ind} | {cite} | {'`' + doc + '`' if doc else ''} | {loc} |")
    report = {"legs": legs, "rows": len(rows),
              "rows_per_leg": {l: sum(1 for r in rows if r[0] == l and r[3]) for l in legs},
              "legs_without_source": legs_without, "missing_fields": missing_fields,
              "doc_ids_not_in_manifest": not_in_manifest}
    return "\n".join(lines) + "\n", report


def write_sources_appendix(session, path: Path = FRAGMENT) -> dict:
    """Write the fragment; refuse (write nothing) if any row's doc_id is outside the manifest."""
    text, report = sources_appendix(session)
    if report["doc_ids_not_in_manifest"]:
        raise SystemExit("FATAL: the sources appendix would cite a document the manifest does "
                         f"not hold: {report['doc_ids_not_in_manifest']}. Nothing was written.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {**report, "fragment": str(path.relative_to(REPO))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", default="scan_2026-09-10_rj2")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--appendix", action="store_true",
                    help="print the Sources-per-check fragment and its report; write nothing")
    a = ap.parse_args(argv)
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    drv = get_neo4j_driver(cfg)
    try:
        with drv.session(database=cfg["neo4j"]["database"]) as s:
            if a.appendix:
                text, report = sources_appendix(s)
                print(text)
                print(json.dumps(report, indent=1), file=sys.stderr)
                return 0
            out = measure(s)
    finally:
        drv.close()
    if a.json:
        print(json.dumps(out, indent=1))
        return 0
    print(f"{'leg':14s} {'code':6s} {'node':5s} {'constr':>6s} {'defin':>6s} {'source':>6s} "
          f"{'spec':>5s} {'rule':>5s}  construct")
    for leg, r in out.items():
        print(f"{leg:14s} {r['framework_code']:6s} {str(r['indicator_node']):5s} "
              f"{r.get('constructs', 0):6d} {r.get('definitions', 0):6d} "
              f"{r.get('sources', 0):6d} {r.get('specs', 0):5d} {r.get('rules', 0):5d}  "
              f"{(r.get('construct_property') or '-')[:42]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
