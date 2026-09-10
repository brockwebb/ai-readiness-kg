#!/usr/bin/env python3
"""NAO 216-128 §3.01 as a Definition, §4.05 and §5.02.d as normative Claims. **No model calls.**

Task `cc_tasks/2026-09-10_corpus_noaa_esip.md` §1 decision 2. Curated, not extracted: the spans
are read off the OCR text by hand and **validated with the same `kg.extraction.grounding` the
parser uses** before any event is written. Invariant 3 is "no grounding span, no write", and a
hand-authored assertion is not exempt from it — it is exactly the kind that needs it.

**The task asks for Obligations and this repo's schema has no such type.** `kg/schema.yaml`'s
catalogue is Document, Definition, Concept, Construct, Instrument, Measure, Claim, Standard,
Framework, Practice, Tool, Platform — there is no `Obligation` node and no deontic-force
vocabulary anywhere in it. (There is one in `fss-policy-kg`, a different graph with a different
schema, which is where the task's wording comes from.) Invariant 4: the schema is the single type
catalogue and changes go through operator review, never a silent edit.

So the two directives are recorded as `Claim` with `claim_type: normative` — the catalogue's own
description of a Claim is *"a falsifiable assertion a document makes (X improves Y, **A requires
B**)"*, which is what a `shall` clause is — and the request for a real `Obligation` type with a
force property is STAGED for review at `corpus/staging/proposed_schema/`. What is lost by the
substitution is named there: `obligation` vs `prohibition` vs `permission` vs `recommendation`
is a distinction `claim_type: normative` cannot carry.

    /opt/anaconda3/bin/python3 scripts/assert_noaa_definition.py --dry-run
    /opt/anaconda3/bin/python3 scripts/assert_noaa_definition.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import eventlog                                             # noqa: E402
from kg.extraction import grounding                                 # noqa: E402

TASK = "cc_tasks/2026-09-10_corpus_noaa_esip.md"
DOC_ID = "nao-216-128-artificial-intelligence-in-noaa"
OCR = REPO / "corpus" / "noaa_esip" / "NAO_216-128.ocr.txt"
PROPOSAL = REPO / "corpus" / "staging" / "proposed_schema" / "obligation_node_type.jsonl"
#: Its own shard, checked free before use — `publish.py` records what happened the time
#: batch 27 was not checked. 43 is the first unused number.
BATCH = 43

#: §3.01, verbatim from the OCR. `Al-Ready` with a lower-case L is what tesseract read and what
#: the stored text says; the grounding check is case-sensitive, so the span must be the text
#: that EXISTS. The TERM is `AI-Ready Data`, which is what the document says — the subject line
#: and §3.02's "Artificial Intelligence (AI)" both read correctly where the letters are spaced,
#: and `NAO_216-128.ocr.json` records the substitution. Recording the span as the corrected
#: string would fail the grounding check, and passing it by correcting the SOURCE would be
#: editing evidence.
DEFINITION_SPAN = (
    "Al-Ready Data: Data that is discoverable, machine-readable and "
    "machine-understandable, and has sufficient quality, documentation, and access methods "
    "to support the full AI application development and use life cycle.")

#: Decision 2: the five components, split as sub-properties. Each is a fragment OF the span
#: above, so each is checked to be covered by it — a component that is not in the definition it
#: claims to decompose is a component somebody invented.
COMPONENTS = {
    "component_discoverable": "discoverable",
    "component_machine_readable_understandable": "machine-readable and "
                                                 "machine-understandable",
    "component_sufficient_quality": "sufficient quality",
    "component_documentation": "documentation",
    "component_access_methods": "access methods",
}

CLAIMS = [
    {"id": "nao216-4-05", "location": "§4.05",
     "claim_text": ("NOAA shall undertake efforts to define, develop, and make publicly "
                    "available data that is Al-ready to support efficient and trustworthy AI "
                    "use."),
     "intended_force": "obligation"},
    {"id": "nao216-5-02-d", "location": "§5.02.d",
     "claim_text": ("Establish data and metadata standards for Al-ready data in accordance "
                    "with applicable NOAA policies and industry best practices;"),
     "intended_force": "obligation"},
]


def provenance(src_sha: str) -> dict:
    """Curated provenance. No `model_id`, because no model was called — a provenance block that
    names a model for a hand-authored assertion would be a false statement about how it was
    made, and `pipeline.py` re-stamps model identity precisely so that cannot happen silently."""
    return {"method": "curated_from_ocr", "operator": f"cc, {TASK} decision 2",
            "schema_version": "0.3.7", "source_sha256": src_sha,
            "ocr": "tesseract 5.5.0, mean word confidence 94.52; NAO_216-128.ocr.json",
            "rationale": ("§3.01 is the definition the L0 crosswalk measures this instrument "
                          "against; §4.05 and §5.02.d are its operative directives.")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    src = OCR.read_text(encoding="utf-8")
    src_sha = hashlib.sha256(OCR.read_bytes()).hexdigest()

    if not grounding.is_grounded(DEFINITION_SPAN, src):
        raise SystemExit("FATAL: the §3.01 span is not in the OCR text; no grounding span, "
                         "no write (invariant 3)")
    for prop, frag in COMPONENTS.items():
        if not grounding.covers(DEFINITION_SPAN, frag):
            raise SystemExit(f"FATAL: {prop} ({frag!r}) is not inside the definition it claims "
                             f"to decompose")
    for c in CLAIMS:
        if not grounding.is_grounded(c["claim_text"], src):
            raise SystemExit(f"FATAL: {c['location']} is not in the OCR text")

    already = {ev.get("payload", {}).get("id") for ev in eventlog.replay()
               if ev.get("event_type") == "node_asserted" and ev.get("doc_id") == DOC_ID}
    events = []
    if "nao216-ai-ready-data" not in already:
        events.append(("node_asserted", {
            "doc_id": DOC_ID,
            "payload": {"type": "Definition", "id": "nao216-ai-ready-data",
                        "item": {"name": "AI-Ready Data", "term": "AI-Ready Data",
                                 "verbatim_text": DEFINITION_SPAN,
                                 "grounding_span": DEFINITION_SPAN,
                                 "normative_status": "policy",
                                 "as_of_date": "2026-04-16",
                                 "location": "§3.01",
                                 "term_as_ocrd": "Al-Ready Data",
                                 **COMPONENTS}},
            "provenance": provenance(src_sha)}))
    for c in CLAIMS:
        if c["id"] in already:
            continue
        events.append(("node_asserted", {
            "doc_id": DOC_ID,
            "payload": {"type": "Claim", "id": c["id"],
                        "item": {"name": f"NAO 216-128 {c['location']}",
                                 "claim_text": c["claim_text"],
                                 "grounding_span": c["claim_text"],
                                 "claim_type": "normative",
                                 "evidence_grade": "platform_official",
                                 "location": c["location"]}},
            "provenance": provenance(src_sha)}))

    if a.dry_run:
        print(json.dumps([{"type": e[1]["payload"]["type"], "id": e[1]["payload"]["id"],
                           "grounded": True} for e in events], indent=1))
        print(f"{len(events)} event(s) would be written; "
              f"{len(already & {'nao216-ai-ready-data', *[c['id'] for c in CLAIMS]})} already on "
              f"the log")
        return 0

    for et, payload in events:
        eventlog.append({"event_type": et, **payload}, BATCH)

    PROPOSAL.parent.mkdir(parents=True, exist_ok=True)
    with PROPOSAL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "proposed_node_type": "Obligation",
            "requested_by": TASK,
            "why": ("NAO 216-128 §4.05 and §5.02.d are DIRECTIVES, and the catalogue has no "
                    "type for one. They are recorded as Claim/normative, which is the closest "
                    "the schema can say and which loses the deontic distinction: obligation vs "
                    "prohibition vs permission vs recommendation. fss-policy-kg carries that "
                    "vocabulary on its Obligation nodes and is the prior art to copy."),
            "properties": ["obligation_text", "grounding_span", "deontic_force",
                           "addressee", "location"],
            "property_values": {"deontic_force": ["obligation", "prohibition", "permission",
                                                  "recommendation"]},
            "recorded_as": [{"id": c["id"], "type": "Claim", "claim_type": "normative",
                             "intended_force": c["intended_force"],
                             "location": c["location"]} for c in CLAIMS],
            "review": "operator batch review, docs/schema_v0.1.md §6",
        }) + "\n")

    print(json.dumps({"events_written": len(events),
                      "definition": "nao216-ai-ready-data",
                      "claims": [c["id"] for c in CLAIMS],
                      "schema_proposal": str(PROPOSAL.relative_to(REPO))}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
