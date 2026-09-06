#!/usr/bin/env python3
"""Measure the bare-grounding-span population before touching it. **Zero model spend.**

Task `cc_tasks/2026-09-06_bare_span_backfill.md` §1. Issue `e21b9ab3`: a grounding span equal
to the node's own name gives a judge, a rater or a reader nothing to resolve on, and it is
measured as the direct cause of the §2.3 homograph control failure, of all three ER gold
`uncertain` verdicts, and of 45 of 212 judged terms having at most one evidenced arm.

**Invariant 3 ("no grounding span, no write") is satisfied by a bare span**, which is why the
floor was never enforced: the span is present, verbatim and grounded — it is simply the term
itself, so it carries no context. Luhn (1960), "Key word-in-context index for technical
literature", *American Documentation* 11(4): the useful unit is the mention **plus its bounded
context**, not the mention.

    /opt/anaconda3/bin/python3 scripts/bare_span_measure.py
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TASK = "cc_tasks/2026-09-06_bare_span_backfill.md"
OUT = REPO / "state" / "bare_span_census_2026-09-06.json"
TOP_DOCS = REPO / "state" / "bare_span_top_documents_2026-09-06.json"

#: Labels that carry both a `name` and a `grounding_span`. `Claim`, `Definition`, `Measure`
#: and `Practice` carry no `name`, so "span equals name" is undefined for them — reported as
#: not-applicable rather than as zero, which would read like a clean bill of health.
NAMED_LABELS = ("Concept", "Instrument", "Standard", "Framework", "Platform", "Tool")
UNNAMED_LABELS = ("Claim", "Definition", "Measure", "Practice")

_WS = re.compile(r"\s+")


def norm(s) -> str:
    return _WS.sub(" ", (s or "").strip()).lower()


def is_bare(span, name) -> bool:
    """The span carries no context beyond the name itself."""
    return bool(name) and norm(span) == norm(name)


def location_kind(loc: str) -> str:
    """What one `location` value looks like.

    Answering §1's question — 'read the extractor's `location` semantics from the code, not
    from the RESULT's guess'. The prompt (`prompt_template_v0_3_8.md`) requires a `location`
    on every node and edge but never defines its format, so the model authors it freely. What
    landed is a HEADING PATH in prose: `Stages of the journey > Readiness`, `Introduction`,
    `title/intro`, `DIME PROJECT banner`. It is not an offset, not a stable section id, and
    not guaranteed to match a heading in the substrate — so §2 can use it only to DISAMBIGUATE
    between candidate matches, never to resolve a position.
    """
    if not loc:
        return "null"
    if ">" in loc:
        return "heading_path"
    if re.fullmatch(r"[\d.]+", loc.strip()):
        return "numeric"
    if re.search(r"\b(p\.?|page|line|offset|char)\s*\d+", loc, re.I):
        return "positional"
    if len(loc.split()) <= 6:
        return "heading_single"
    return "prose"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)

    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    rows = []
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            for label in NAMED_LABELS:
                rows += [dict(r, label=label) for r in s.run(
                    f"MATCH (n:{label}) RETURN n.key AS key, n.name AS name, "
                    f"n.grounding_span AS span, n.doc_id AS doc_id, n.location AS location"
                ).data()]
            unnamed = {lbl: s.run(f"MATCH (n:{lbl}) RETURN count(n)").single()[0]
                       for lbl in UNNAMED_LABELS}
    finally:
        driver.close()

    by_label = collections.Counter()
    total_by_label = collections.Counter()
    bare_rows = []
    for r in rows:
        total_by_label[r["label"]] += 1
        if is_bare(r["span"], r["name"]):
            by_label[r["label"]] += 1
            bare_rows.append(r)

    by_doc = collections.Counter(r["doc_id"] for r in bare_rows)
    kinds = collections.Counter(location_kind(r["location"]) for r in bare_rows)
    kinds_all = collections.Counter(location_kind(r["location"]) for r in rows)

    top = [{"doc_id": d, "bare_nodes": n,
            "total_named_nodes": sum(1 for r in rows if r["doc_id"] == d),
            "bare_share": round(n / max(1, sum(1 for r in rows if r["doc_id"] == d)), 4)}
           for d, n in by_doc.most_common(20)]
    TOP_DOCS.write_text(json.dumps({"task": TASK, "top_20_documents_by_bare_span_count": top},
                                   indent=1) + "\n", encoding="utf-8")

    out = {
        "task": TASK,
        "named_labels": list(NAMED_LABELS),
        "nodes_examined": len(rows),
        "bare_by_label": {l: by_label.get(l, 0) for l in NAMED_LABELS},
        "total_by_label": {l: total_by_label.get(l, 0) for l in NAMED_LABELS},
        "bare_share_by_label": {l: round(by_label.get(l, 0) / total_by_label[l], 6)
                                for l in NAMED_LABELS if total_by_label.get(l)},
        "bare_total": len(bare_rows),
        "bare_share": round(len(bare_rows) / len(rows), 6) if rows else None,
        "labels_without_a_name_property": unnamed,
        "documents_contributing_bare_spans": len(by_doc),
        "top_20_documents": top,
        "location_kinds_bare": dict(kinds),
        "location_kinds_all_named_nodes": dict(kinds_all),
        "location_semantics": (
            "MODEL-AUTHORED HEADING PATH, free text. prompt_template_v0_3_8.md requires a "
            "`location` on every node and edge and never defines its format, so the model "
            "writes what it likes: 'Stages of the journey > Readiness', 'Introduction', "
            "'title/intro', 'DIME PROJECT banner'. Not an offset, not a stable section id, "
            "not guaranteed to match a heading in the substrate. §2 therefore uses it only to "
            "DISAMBIGUATE between candidate matches of the name, never to resolve a position."),
    }
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "top_20_documents"}, indent=1))
    print("\ntop 10 documents by bare-span count:")
    for t in top[:10]:
        print(f"  {t['bare_nodes']:4d} / {t['total_named_nodes']:4d}  ({t['bare_share']:.2f})  {t['doc_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
