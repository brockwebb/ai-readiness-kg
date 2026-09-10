#!/usr/bin/env python3
"""Crosswalk the ESIP AI-ready checklist to the framework's indicators. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_corpus_noaa_esip.md` §2, decision 4: *"crosswalked the same way, item
by item"* as decision 3 crosswalks the NOAA definition — each item against the indicators that
measure it, with `measured: full | partial | none`.

**Two different questions, kept apart, because collapsing them is how a crosswalk lies.**

* `indicators` — which framework indicators are ABOUT this item. A framework question.
* `measured`   — what the SCAN INSTRUMENT can see of it on a public product surface:
                 `full`    the leg measures exactly this property;
                 `partial` the leg measures a public-surface proxy, not the property;
                 `none`    no measured leg sees it at all.

An item can be covered by the framework and invisible to the instrument — most of Data Quality
and all of Data Preparation are, because they are properties of the DATA and the scan reads the
SURFACE. Reporting one number for both would turn "we do not measure this" into "this is not in
the framework", and the whole point of the crosswalk is that the reader can see the difference.

**Every row is grounded**: `line` and `verbatim` name where in the admitted document the item is,
and `tests/test_noaa_esip_crosswalk.py` re-reads the file and fails if a verbatim has moved. The
document is content-addressed in the manifest, so "the file" is a specific 12,831 bytes.

Apparatus is not crosswalked: the About/History/citation blocks, the appendix definitions and the
references say what the checklist IS, and ask nothing about a dataset.

    /opt/anaconda3/bin/python3 scripts/build_esip_crosswalk.py --dry-run
    /opt/anaconda3/bin/python3 scripts/build_esip_crosswalk.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-10_corpus_noaa_esip.md"
NAME = "crosswalk_esip_ai_readiness_2026-09-10"
DOC_ID = "esip-ai-ready-data-checklist-v1-0"
SOURCE = REPO / "corpus" / "noaa_esip" / "esip-ai-ready-data-checklist-v1.0.md"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
OUT = REPO / "state" / f"{NAME}.json"

#: The legs the scan actually runs (`params.tier0.legs` plus the framework set the cycles judge).
#: A row may cite an indicator OUTSIDE this set — that is the framework covering something the
#: instrument does not, and it is exactly what `measured: none` records.
MEASURED_LEGS = ("A1", "A2", "A3", "A4", "A5", "A6", "A8", "A9", "A10", "A11", "A12",
                 "B3", "D1", "D4", "F4", "G1-D")

#: (line, section, indicators, measured, why). `line` is 1-based into the admitted file and the
#: verbatim is READ FROM THERE, never retyped: a crosswalk that carries its own copy of the
#: source text is a crosswalk that can disagree with the source.
ITEMS = [
    # ---------------------------------------------------------------- General Information
    (29, "General Information", ["A7", "A10"], "partial",
     "the scan resolves the product landing page and records its final URL, and A10 measures "
     "whether a data tool behind it exposes stable, directly-requestable deep links; A7 — is "
     "that URL a DECLARED persistent identifier — is in the framework and unmeasured"),
    (31, "General Information", ["A8", "G3"], "partial",
     "A8 reads a machine-readable release date and a latest-vintage pointer off the surface; "
     "the dataset's own version string is not read"),
    (32, "General Information", ["G4"], "none",
     "point of contact is not a leg; G4 (authority metadata) is in the framework and unmeasured"),
    (33, "General Information", ["A8"], "partial",
     "first-publication date is not distinguished from the surface's declared release date"),
    (34, "General Information", ["D3"], "none", "raw-vs-derived is a lineage property; D3 unmeasured"),
    (35, "General Information", ["D3"], "none", "observational/model/synthetic is a lineage property"),
    (36, "General Information", ["D3"], "none", "single-source vs aggregated is a lineage property"),
    # ---------------------------------------------------------------- Data Quality
    (40, "Data Quality", ["A8"], "partial",
     "whether a dataset WILL be updated is a commitment; A8 sees only whether a release date "
     "and a latest pointer are published now"),
    (41, "Data Quality", ["A8"], "none", "update frequency is not published in a form any leg reads"),
    (45, "Data Quality", ["G2"], "none",
     "staged/preliminary updates are revision semantics; G2 is in the framework and unmeasured"),
    (49, "Data Quality", ["G2"], "none", "supersession between versions is revision semantics"),
    (52, "Data Quality", ["B4"], "none",
     "completeness documentation is quality metadata; B4 is in the framework and unmeasured"),
    (54, "Data Quality", ["B4"], "none", "spatial completeness is a property of the data"),
    (56, "Data Quality", ["B4"], "none", "temporal completeness is a property of the data"),
    (59, "Data Quality", ["B5"], "none", "self-consistency of units and types; B5 unmeasured"),
    (61, "Data Quality", ["B5"], "none", "cross-collection consistency; B5 unmeasured"),
    (63, "Data Quality", ["B5", "F1"], "none", "consistency monitoring is a release-process property"),
    (67, "Data Quality", ["B4"], "none", "known bias is a property of the data"),
    (69, "Data Quality", ["B4"], "none", "bias examination is a property of the data"),
    (72, "Data Quality", ["B4"], "none", "reported bias is a property of the data"),
    (76, "Data Quality", ["B1"], "none",
     "spatial/temporal resolution is variable-level metadata; B1 unmeasured"),
    (77, "Data Quality", ["B3", "B4"], "partial",
     "B3 measures whether METHODOLOGY is linked and legible from the product surface, which is "
     "the published-procedures half of this item; the report's content is not read"),
    (79, "Data Quality", ["D3"], "none", "provenance tracking; D3 unmeasured"),
    (80, "Data Quality", ["F6"], "none", "checksums are release authenticity; F6 unmeasured"),
    (81, "Data Quality", ["A3"], "partial",
     "A3 sees whether a whole-product download is offered, not how large it is"),
    # ---------------------------------------------------------------- Data Documentation
    (85, "Data Documentation", ["A6"], "partial",
     "A6 validates schema.org/DCAT/Croissant markup on the product page — a metadata standard "
     "on the SURFACE. A domain convention (CF, ISO 19115) inside the dataset is not read"),
    (87, "Data Documentation", ["A6"], "full",
     "machine-readable dataset metadata on the surface is precisely what A6 measures"),
    (88, "Data Documentation", ["A6"], "partial",
     "spatial/temporal extent is read only if it is in the surface markup"),
    (89, "Data Documentation", ["B1"], "none", "data dictionary/codebook; B1 unmeasured"),
    (92, "Data Documentation", ["B1"], "none", "machine-readable data dictionary; B1 unmeasured"),
    (93, "Data Documentation", ["B2", "B5"], "none", "parameter standards; unmeasured"),
    (95, "Data Documentation", ["B2"], "none", "ontology crosswalk of parameters; B2 unmeasured"),
    (96, "Data Documentation", ["A7"], "none",
     "a persistent identifier (DOI) is A7, which the scan does not measure"),
    (97, "Data Documentation", ["G4"], "none", "subject-matter contact; G4 unmeasured"),
    (98, "Data Documentation", ["B6"], "none", "feedback mechanism; no leg reads it"),
    (99, "Data Documentation", ["A2", "B6"], "partial",
     "A2 records a documented API, which is where example notebooks usually hang; the examples "
     "themselves are not looked for"),
    (100, "Data Documentation", ["D1"], "full",
     "D1 measures an explicit licence on the product and the API, which is this item"),
    (102, "Data Documentation", ["D1"], "full",
     "D1's subject is a MACHINE-READABLE licence, which is this item exactly"),
    (103, "Data Documentation", ["D2"], "none", "prior AI/ML use; D2 unmeasured"),
    (104, "Data Documentation", ["D2"], "none", "intended-use recommendations; D2 unmeasured"),
    # ---------------------------------------------------------------- Data Access
    (108, "Data Access", ["A1"], "full",
     "A1 classifies the format SERVED, on the response rather than the href, which is this item"),
    (109, "Data Access", ["A1"], "full", "machine-readability of the served format is A1"),
    (110, "Data Access", ["A1"], "full",
     "A1's structured set is open, non-proprietary formats; PDF-only fails it"),
    (111, "Data Access", ["A9"], "partial",
     "conversion tools are not a leg; A9 sees a machine-first entry point where they usually sit"),
    (114, "Data Access", ["A2", "A12"], "partial",
     "A2 records the auth model where the API declares one; A12 measures whether an identified "
     "compliant client is actually SERVED, which is the enforced half of the same question"),
    (115, "Data Access", ["A3"], "full",
     "A3 is whether a full-product download exists and is linked from the product page"),
    (116, "Data Access", ["A2", "A9"], "full",
     "A2 is a documented public API; A9 is the machine-first entry point"),
    (118, "Data Access", ["A2"], "partial",
     "an open standard protocol is recorded where the API declares it; conformance is not tested"),
    (119, "Data Access", ["A2"], "full", "A2's subject is a DOCUMENTED API"),
    (121, "Data Access", ["A9", "D4"], "partial",
     "cloud availability is usually declared in an inventory (D4) or a machine entry point (A9)"),
    (122, "Data Access", ["D2"], "none",
     "restricted-access provisions are a permissions question; D2 unmeasured"),
    (124, "Data Access", ["G5"], "none", "aggregation to reduce granularity is disclosure semantics"),
    (125, "Data Access", ["G5"], "none", "anonymisation is disclosure semantics; G5 unmeasured"),
    (126, "Data Access", ["A2"], "none", "authorised-user access paths are not measured"),
    # ---------------------------------------------------------------- Data Preparation
    (129, "Data Preparation", ["B4"], "none", "gap filling is a property of the data"),
    (130, "Data Preparation", ["B4"], "none", "outlier handling is a property of the data"),
    (131, "Data Preparation", ["B1"], "none", "gridding is a property of the data"),
    (139, "Data Preparation", ["B1"], "none",
     "training labels are a property of the data; nothing on the surface declares them"),
]


def indicator_codes() -> set:
    f = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    return {n["properties"]["code"] for n in f["nodes"]
            if "AssessmentIndicator" in n["labels"]}


def build() -> dict:
    src = SOURCE.read_text(encoding="utf-8")
    lines = src.splitlines()
    codes = indicator_codes()
    rows = []
    for line, section, inds, measured, why in ITEMS:
        unknown = [i for i in inds if i not in codes]
        if unknown:
            raise SystemExit(f"FATAL: line {line} cites indicators that are not in the "
                             f"framework: {unknown}")
        if measured not in ("full", "partial", "none"):
            raise SystemExit(f"FATAL: line {line} has measured={measured!r}")
        # `measured` is a claim about the INSTRUMENT, so it has to rest on a leg the instrument
        # runs. A row that cites only unmeasured indicators and still claims `full` or `partial`
        # is the collapse this crosswalk exists to avoid, stated in its own table.
        if measured != "none" and not any(i in MEASURED_LEGS for i in inds):
            raise SystemExit(
                f"FATAL: line {line} claims measured={measured!r} but cites no measured leg "
                f"({inds}); either the row means `none` or it is citing the wrong indicator")
        rows.append({
            "line": line, "section": section,
            "verbatim": lines[line - 1].strip(),
            "indicators": inds,
            "indicators_measured_by_the_scan": [i for i in inds if i in MEASURED_LEGS],
            "measured": measured, "why": why})

    by_measured = {m: sum(1 for r in rows if r["measured"] == m)
                   for m in ("full", "partial", "none")}
    by_section = {}
    for r in rows:
        s = by_section.setdefault(r["section"], {"full": 0, "partial": 0, "none": 0})
        s[r["measured"]] += 1
    return {
        "name": NAME, "task": TASK,
        "generated_by": "scripts/build_esip_crosswalk.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_doc_id": DOC_ID,
        "source_path": str(SOURCE.relative_to(REPO)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "citation": ("ESIP Data Readiness Cluster (2023): Checklist to Examine AI-readiness for "
                     "Open Environmental Datasets v.1.0. ESIP. Online resource. "
                     "https://doi.org/10.6084/m9.figshare.19983722.v1"),
        "framework": "framework/ai_readiness_framework.json",
        "measured_legs": list(MEASURED_LEGS),
        "scale": {"full": "a measured leg measures exactly this property",
                  "partial": "a measured leg measures a public-surface proxy for it",
                  "none": "no measured leg sees it"},
        "items": len(rows),
        "by_measured": by_measured,
        "by_section": by_section,
        "indicators_cited": sorted({i for r in rows for i in r["indicators"]}),
        "indicators_cited_not_measured": sorted({i for r in rows for i in r["indicators"]
                                                 if i not in MEASURED_LEGS}),
        "rows": rows,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    print(json.dumps({k: v for k, v in doc.items() if k != "rows"}, indent=1))
    if a.dry_run:
        for r in doc["rows"]:
            print(f"  {r['line']:4d} {r['measured']:8s} {','.join(r['indicators']):12s} "
                  f"{r['verbatim'][:72]}")
        return 0
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
