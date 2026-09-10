#!/usr/bin/env python3
"""NOAA's AI-Ready Data definition against this instrument's indicators. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_corpus_noaa_esip.md` §2 decision 3, which fixes the mapping:

    discoverable                        -> A4, A5, A11
    machine-readable/understandable     -> A1, A2, A6, A8, D1
    access methods                      -> A9, B3, F4
    documentation                       -> partial (license, vintage)
    quality                             -> none

That mapping is the operator's and is implemented as given. What this script adds is the two
things a table of component names cannot carry on its own: each component is tied to the SPAN of
§3.01 it comes from, and each `measured` level is checked against the legs the scan actually
runs, so the file cannot claim coverage from an indicator no cycle measures.

`measured` means the same thing here as in the ESIP crosswalk, and the two are built to be read
side by side: `full` the leg measures exactly this, `partial` a public-surface proxy, `none` no
measured leg sees it.
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

from kg.extraction import grounding                                 # noqa: E402

TASK = "cc_tasks/2026-09-10_corpus_noaa_esip.md"
NAME = "crosswalk_noaa_ai_ready_2026-09-10"
DOC_ID = "nao-216-128-artificial-intelligence-in-noaa"
DEFINITION_ID = "nao216-ai-ready-data"
OCR = REPO / "corpus" / "noaa_esip" / "NAO_216-128.ocr.txt"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
OUT = REPO / "state" / f"{NAME}.json"

MEASURED_LEGS = ("A1", "A2", "A3", "A4", "A5", "A6", "A8", "A9", "A10", "A11", "A12",
                 "B3", "D1", "D4", "F4", "G1-D")

DEFINITION_SPAN = (
    "Al-Ready Data: Data that is discoverable, machine-readable and "
    "machine-understandable, and has sufficient quality, documentation, and access methods "
    "to support the full AI application development and use life cycle.")

#: (component, span fragment, indicators, measured, why). The mapping is decision 3's.
COMPONENTS = [
    ("discoverable", "discoverable", ["A4", "A5", "A11"], "full",
     "A4 is whether robots.txt and any AI-crawler policy PERMIT retrieval, A5 whether a "
     "sitemap or llms.txt makes the products findable, A11 the three-layer declared-vs-enforced "
     "comparison. Discoverability by a machine is what these three legs measure and all three "
     "run every cycle."),
    ("machine-readable and machine-understandable",
     "machine-readable and machine-understandable",
     ["A1", "A2", "A6", "A8", "D1"], "full",
     "READABLE is A1 (structured data served, classified on the response rather than the href) "
     "and A2 (a documented API); UNDERSTANDABLE is A6 (schema.org/DCAT/Croissant markup), A8 "
     "(machine-readable release date and latest-vintage pointer) and D1 (machine-readable "
     "licence). All five run every cycle."),
    ("sufficient quality", "sufficient quality", ["B4", "C5", "G1-D"], "none",
     "The definition's word is SUFFICIENT — a judgement about the data against a use. This "
     "instrument reads a public surface: G1-D sees whether error measures are DECLARED as "
     "structured fields, which is a legibility fact and not a quality one, and B4 and C5 are in "
     "the framework and unmeasured. Decision 3 says none, and the reason is that no leg "
     "inspects the data at all."),
    ("documentation", "documentation", ["D1", "A8", "B3", "B1"], "partial",
     "Decision 3's own wording: partial, licence and vintage. D1 and A8 are exactly those two "
     "and both are measured; B3 adds whether methodology is linked and legible. What is NOT "
     "measured is the documentation the definition is mostly about — variable-level metadata "
     "and a data dictionary (B1), which no cycle runs."),
    ("access methods", "access methods", ["A9", "B3", "F4"], "full",
     "A9 is the machine-first entry point, B3 the methodology route, F4 the machine-readable "
     "changelog. Decision 3's set, all three measured. A3 (bulk download) is arguably an access "
     "method too and is NOT in decision 3's mapping; it is left out rather than added, because "
     "the mapping is the operator's."),
]


def indicator_codes() -> set:
    f = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    return {n["properties"]["code"] for n in f["nodes"]
            if "AssessmentIndicator" in n["labels"]}


def build() -> dict:
    src = OCR.read_text(encoding="utf-8")
    if not grounding.is_grounded(DEFINITION_SPAN, src):
        raise SystemExit("FATAL: the definition span is not in the OCR text")
    codes = indicator_codes()
    rows = []
    for comp, frag, inds, measured, why in COMPONENTS:
        if not grounding.covers(DEFINITION_SPAN, frag):
            raise SystemExit(f"FATAL: component {comp!r} is not inside §3.01")
        unknown = [i for i in inds if i not in codes]
        if unknown:
            raise SystemExit(f"FATAL: {comp} cites indicators absent from the framework: "
                             f"{unknown}")
        if measured != "none" and not any(i in MEASURED_LEGS for i in inds):
            raise SystemExit(f"FATAL: {comp} claims measured={measured!r} with no measured leg")
        rows.append({"component": comp, "span_fragment": frag, "indicators": inds,
                     "indicators_measured_by_the_scan": [i for i in inds if i in MEASURED_LEGS],
                     "measured": measured, "why": why})

    by = {m: sum(1 for r in rows if r["measured"] == m) for m in ("full", "partial", "none")}
    return {
        "name": NAME, "task": TASK,
        "generated_by": "scripts/build_noaa_crosswalk.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_doc_id": DOC_ID, "definition_node_id": DEFINITION_ID,
        "definition_location": "§3.01",
        "definition_verbatim": DEFINITION_SPAN,
        "definition_term": "AI-Ready Data",
        "source_path": str(OCR.relative_to(REPO)),
        "source_sha256": hashlib.sha256(OCR.read_bytes()).hexdigest(),
        "source_is_ocr": True,
        "ocr_sidecar": "corpus/noaa_esip/NAO_216-128.ocr.json",
        "framework": "framework/ai_readiness_framework.json",
        "measured_legs": list(MEASURED_LEGS),
        "scale": {"full": "a measured leg measures exactly this property",
                  "partial": "a measured leg measures a public-surface proxy for it",
                  "none": "no measured leg sees it"},
        "components": len(rows),
        "by_measured": by,
        "headline": (f"{by['full']} of {len(rows)} components measured in full, "
                     f"{by['partial']} in part, {by['none']} not at all"),
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
            print(f"  {r['measured']:8s} {','.join(r['indicators']):20s} {r['component']}")
        return 0
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
