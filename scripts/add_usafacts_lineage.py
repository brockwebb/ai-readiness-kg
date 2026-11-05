#!/usr/bin/env python3
"""Write USAFacts' three-track August-2026 framework into the record as the lineage layer the
sixteen checks now hang from, beside the predecessor four-criteria layer. **Zero spend.**

`cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md`
Part A, implementing DN-020 (sections 1, 3, 4). The base document is USAFacts' August 2026
framework: three tracks (Agentic Access, Agentic Context, Agentic Evaluation), three levels in
each, three prerequisites before any level applies, modelled on SLSA (DN-020 section 1). The
sixteen measured checks are PLACED on that ladder (DN-020 section 4): nothing is re-measured,
the cycle of record is untouched, this edits the record's lineage layer only.

Three node labels are added beside `AiReadyCriterion` and `ExtensionGroup`:

* **`UsafactsTrack` (3)** — the track, its one-line description verbatim from the overview
  (`usafacts-ai-ready-framework-overview-2026`, the deck's slide 16 carries only the level
  captions, not a one-line per-track description — a DN-020/task premise corrected in the RESULT).
* **`UsafactsLevel` (9)** — a rung. `name` is the deck's "How it works" caption for that level
  (verbatim); `text` is the level's detail-slide bullets where the docling output captured them
  cleanly (Context slide 19, Evaluation slide 20) and the caption itself where it did not (the
  Access detail slide 18 OCR'd as only two of its bullets — noted per node and in the RESULT).
* **`UsafactsPrerequisite` (3)** — a prerequisite, name and text verbatim from slide 15.

Every USAFacts phrase is transcribed from the gitignored docling copies, embedded here as a
literal with the docling line it was read from, the way `add_aiready_lineage.py` embeds the
guide's statements. OCR artefacts (a space around a hyphen, "machine -readable"; a doubled
article, "the open the web") are de-hyphenated / de-doubled the way `kg/extraction/grounding.py`
normalises, and the correction is named on the node's `docling_lines` where it applies.

The sixteen new `DESCENDS_FROM` edges (`spec:*` -> rung, `basis: DN-020 §4`) are resolved by
the spec's `rf_name_brief`, not by the letter-code DN-020 section 4 prints: those codes are the
roll-up's DISPLAY codes and do not equal the record's spec ids (e.g. the check named "The data
page is in the site's list of pages" is display A3 but record `spec:A5`). The placement is keyed
on the verbatim name; a name that resolves to no spec, or to more than one, stops the task on
that row (DN-020 section 4: the task confirms each). The sixteen existing `DESCENDS_FROM` edges
to `aiready:*`/`ext:*` stay and gain `lineage: predecessor`.

Track -> level is `DECOMPOSES_INTO` (the existing edge type, as criterion -> construct ->
indicator is): the loader's generic MERGE branch accepts it for the Usafacts labels. Levels are
cumulative in SLSA, but the record models the decomposition (track owns its levels), not the
cumulation, so `DECOMPOSES_INTO` is the right relation and no `REQUIRES` chain is written
(RESULT says which and why).

Through `scripts/framework_writeback.py::save` only (the single-writer rule). Additive: no node,
edge or counts key is dropped, so no `--force` is needed. A re-run upserts by identity and writes
the same bytes (`save` reports `unchanged`). Not finished until a projection follows it (DD-057):
run `scripts/load_framework_graph.py` and `tests/test_framework_projection_roundtrip.py`.

    /opt/anaconda3/bin/python3 scripts/add_usafacts_lineage.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw  # noqa: E402

SCRIPT = "scripts/add_usafacts_lineage.py"
TASK = "cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md"

SOURCE = "USAFacts 2026-08 (usafacts-ai-ready-framework-deck-2026-08)"
DECK = "state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md"
OVERVIEW = "state/docling_md/usafacts-ai-ready-framework-overview-2026.md"

#: The three tracks. `text` is the one-line track description, verbatim from the overview (the
#: clean single-sentence description of each track); the deck's slide 16 "How it works" carries
#: only the nine level captions, not a per-track one-liner, so the overview is the source. OCR
#: "publ ic" on the evaluation line is de-spaced to "public".
TRACKS = [
    {"id": "usaf:access", "name": "Agentic Access",
     "text": "Enable agents to easily access and parse published government data in an "
             "unencumbered way.",
     "source_file": OVERVIEW, "docling_lines": "13 (overview, track description)"},
    {"id": "usaf:context", "name": "Agentic Context",
     "text": "Provide proper context and documentation so that agents can consistently and "
             "accurately understand and use government data.",
     "source_file": OVERVIEW, "docling_lines": "14 (overview, track description)"},
    {"id": "usaf:evaluation", "name": "Agentic Evaluation",
     "text": "Publish public evaluation datasets and run benchmarks on common models to ensure "
             "government data is consistently cited by AI models in an accurate way and with "
             "proper context.",
     "source_file": OVERVIEW, "docling_lines": "15 (overview, track description; OCR 'publ ic' -> 'public')"},
]

#: The nine levels. `name` = the deck's "How it works" caption (verbatim, lines 441-461), OCR
#: hyphen-spaces closed ("machine -readable" -> "machine-readable"). `text` = the level's detail
#: slide bullets where docling captured them cleanly; the Access detail slide (18) OCR'd as only
#: two of its bullets (lines 491, 493-495), so Access I has no detail bullets and its `text`
#: repeats the verbatim caption (noted on the node).
LEVELS = [
    {"id": "usaf:access:1", "track": "usaf:access", "level": 1,
     "name": "Data is published in machine-readable files",
     "text": "Data is published in machine-readable files.",
     "docling_lines": "441 (caption); Access detail slide 18 OCR captured no Level I bullet, text repeats the caption"},
    {"id": "usaf:access:2", "track": "usaf:access", "level": 2,
     "name": "Stable, documented endpoints agents can crawl",
     "text": "Lineage/change notes.",
     "docling_lines": "443 (caption), 491 (detail)"},
    {"id": "usaf:access:3", "track": "usaf:access", "level": 3,
     "name": "Agent-native interface for live, structured queries",
     "text": "Pilot programs on emerging technology and patterns.",
     "docling_lines": "445 (caption), 493-495 (detail)"},
    {"id": "usaf:context:1", "track": "usaf:context", "level": 1,
     "name": "Definitions and units documented for humans",
     "text": "Published methodology documentation; Made available on the open web without restriction.",
     "docling_lines": "449 (caption), 537-539 (detail)"},
    {"id": "usaf:context:2", "track": "usaf:context", "level": 2,
     "name": "Methodology and caveats travel with each dataset",
     "text": "Field-level descriptions; Provenance and update cadence; Documented best practices.",
     "docling_lines": "451 (caption), 543-547 (detail)"},
    {"id": "usaf:context:3", "track": "usaf:context", "level": 3,
     "name": "Context is machine-readable and citable in an answer",
     "text": "Pragmatics and additional expert context; Documented edge cases; Context-specific MCP access.",
     "docling_lines": "453 (caption), 551-555 (detail)"},
    {"id": "usaf:evaluation:1", "track": "usaf:evaluation", "level": 1,
     "name": "A published evaluation set with reported pass rates",
     "text": "Public evaluation dataset; Published under an open license; Available for review and re-use.",
     "docling_lines": "457 (caption), 587-591 (detail)"},
    {"id": "usaf:evaluation:2", "track": "usaf:evaluation", "level": 2,
     "name": "Continuous automated evaluation at scale",
     "text": "Regular benchmarks run against commercial models; Scores and failures published publicly; Feedback loop to address failures.",
     "docling_lines": "459 (caption), 595-599 (detail)"},
    {"id": "usaf:evaluation:3", "track": "usaf:evaluation", "level": 3,
     "name": "Integrated quality assurance programs across agencies and industry",
     "text": "Coordinated evaluation across peer agencies; Red-teaming and adversarial testing; Communication programs with AI Labs.",
     "docling_lines": "461 (caption), 603-607 (detail)"},
]

#: The three prerequisites, name and text verbatim from slide 15 (lines 471, 473, 475). The
#: discoverable sentence OCR'd "the open the web"; the doubled article is dropped ("the open web").
PREREQUISITES = [
    {"id": "usaf:pre:open", "name": "Open by default",
     "text": "Data should be published as open data under the OPEN Government Data Act, with no "
             "unresolved licensing or classification questions.",
     "docling_lines": "471"},
    {"id": "usaf:pre:discoverable", "name": "Discoverable",
     "text": "Data should be registered on Data.gov or otherwise accessible through the open web.",
     "docling_lines": "473 (OCR 'the open the web' -> 'the open web')"},
    {"id": "usaf:pre:licensed", "name": "Clearly licensed",
     "text": "The data's usage license stated in plain language on the data product's landing "
             "page, not just buried in metadata.",
     "docling_lines": "475"},
]

#: DN-020 section 4, keyed on the rung node id and the spec's verbatim `rf_name_brief` (NOT the
#: display letter-code the note prints, which does not equal the record spec id). `display` is
#: the roll-up's code, carried for the RESULT's sixteen pairs. The order within a rung is the
#: order DN-020 section 4 lists them.
PLACEMENT = [
    ("usaf:pre:discoverable", "A3", "The data page is in the site's list of pages"),
    ("usaf:pre:discoverable", "A6", "The page labels itself as a dataset"),
    ("usaf:pre:discoverable", "D1", "The product is listed in the agency's data inventory"),
    ("usaf:pre:licensed", "D2", "The terms of reuse, under a recognised name"),
    ("usaf:access:1", "A1", "Data offered as a file a program can read"),
    ("usaf:access:1", "A2", "The whole dataset in one download"),
    ("usaf:access:1", "A4", "Whether the site's visitor rules let AI tools in"),
    ("usaf:access:1", "A12", "The site serves what its own rules permit"),
    ("usaf:access:1", "A11", "What the site states about automated access"),
    ("usaf:access:1", "A10", "The interactive data tool answers honestly"),
    ("usaf:access:2", "A5", "A published description of the agency's data service"),
    ("usaf:access:2", "A9", "A front door built for programs"),
    ("usaf:access:2", "A13", "From a data page to the data service, terms, change log and inventory"),
    ("usaf:access:2", "F3", "A change history a program can follow"),
    ("usaf:context:1", "B1", "The methods are readable as plain text"),
    ("usaf:context:2", "A8", "The release date, and a link to the latest release"),
]


def track_nodes() -> list[dict]:
    return [{"id": t["id"], "labels": ["UsafactsTrack"], "properties": {
        "name": t["name"], "text": t["text"], "source": SOURCE,
        "source_file": t["source_file"], "docling_lines": t["docling_lines"]}} for t in TRACKS]


def level_nodes() -> list[dict]:
    return [{"id": l["id"], "labels": ["UsafactsLevel"], "properties": {
        "track": l["track"], "level": l["level"], "name": l["name"], "text": l["text"],
        "source": SOURCE, "source_file": DECK, "docling_lines": l["docling_lines"]}} for l in LEVELS]


def prerequisite_nodes() -> list[dict]:
    return [{"id": p["id"], "labels": ["UsafactsPrerequisite"], "properties": {
        "name": p["name"], "text": p["text"], "source": SOURCE,
        "source_file": DECK, "docling_lines": p["docling_lines"]}} for p in PREREQUISITES]


def decomposes_edges() -> list[dict]:
    """Track -> its three levels (the existing DECOMPOSES_INTO edge type, no properties)."""
    return [{"from": l["track"], "type": "DECOMPOSES_INTO", "to": l["id"]} for l in LEVELS]


def resolve_placement(g: dict) -> tuple[list[dict], list[dict]]:
    """Return `(sixteen_pairs, new_descends_edges)`. Each placement row is resolved by matching
    its verbatim `rf_name_brief` to exactly one `MeasurementSpec`; a miss or an ambiguity stops
    the task on that row (DN-020 section 4)."""
    by_name: dict = {}
    for n in g["nodes"]:
        if "MeasurementSpec" in n["labels"] and n["properties"].get("instrument_state"):
            nm = n["properties"].get("rf_name_brief")
            by_name.setdefault(nm, []).append(n["id"])
    pairs, edges, bad = [], [], []
    for rung, display, name in PLACEMENT:
        hits = by_name.get(name, [])
        if len(hits) != 1:
            bad.append(f"{display} {name!r} -> {len(hits)} specs {hits}")
            continue
        spec_id = hits[0]
        pairs.append({"rung": rung, "display_code": display, "rf_name_brief": name,
                      "spec_id": spec_id})
        edges.append({"from": spec_id, "type": "DESCENDS_FROM", "to": rung,
                      "properties": {"basis": "DN-020 §4"}})
    if bad:
        raise SystemExit("FATAL: DN-020 §4 placement did not resolve one row to one spec:\n  "
                         + "\n  ".join(bad))
    if len(edges) != 16:
        raise SystemExit(f"FATAL: {len(edges)} placements, expected 16")
    return pairs, edges


def tag_predecessor_edges(g: dict) -> int:
    """Give every existing `DESCENDS_FROM` edge (to `aiready:*`/`ext:*`) `lineage: predecessor`.
    Returns the count tagged; it must be sixteen."""
    n = 0
    for e in g["edges"]:
        if e["type"] == "DESCENDS_FROM" and (e["to"].startswith("aiready:")
                                             or e["to"].startswith("ext:")):
            props = e.setdefault("properties", {})
            props["lineage"] = "predecessor"
            n += 1
    if n != 16:
        raise SystemExit(f"FATAL: tagged {n} predecessor DESCENDS_FROM edges, expected 16")
    return n


def build(g: dict) -> tuple[dict, list[dict]]:
    nodes = track_nodes() + level_nodes() + prerequisite_nodes()
    pairs, new_edges = resolve_placement(g)
    tag_predecessor_edges(g)
    dec_edges = decomposes_edges()

    by_id = {n["id"]: i for i, n in enumerate(g["nodes"])}
    for node in nodes:
        if node["id"] in by_id:
            g["nodes"][by_id[node["id"]]] = node
        else:
            g["nodes"].append(node)
    eidx = {fw._edge_key(e): i for i, e in enumerate(g["edges"])}
    for e in dec_edges + new_edges:
        k = fw._edge_key(e)
        if k in eidx:
            g["edges"][eidx[k]] = e
        else:
            g["edges"].append(e)

    g.setdefault("counts", {})
    g["counts"]["usafacts_track_nodes"] = len(TRACKS)
    g["counts"]["usafacts_level_nodes"] = len(LEVELS)
    g["counts"]["usafacts_prerequisite_nodes"] = len(PREREQUISITES)
    g["counts"]["usafacts_descends_from_edges"] = len(new_edges)
    return g, pairs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    g, pairs = build(fw.load())
    ev = fw.save(g, script=SCRIPT, task=TASK,
                 changes={"implements": "DN-020 sections 1, 3, 4",
                          "usafacts_track_nodes": g["counts"]["usafacts_track_nodes"],
                          "usafacts_level_nodes": g["counts"]["usafacts_level_nodes"],
                          "usafacts_prerequisite_nodes": g["counts"]["usafacts_prerequisite_nodes"],
                          "usafacts_descends_from_edges": g["counts"]["usafacts_descends_from_edges"]},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({"written": ev["written"], "unchanged": ev.get("unchanged", False),
                      "event_id": ev.get("event_id"), "framework_sha256": ev["framework_sha256"],
                      "delta": ev["delta_summary"],
                      "sixteen_pairs": [{"display": p["display_code"], "spec": p["spec_id"],
                                         "rung": p["rung"], "name": p["rf_name_brief"]}
                                        for p in pairs],
                      "counts": {k: g["counts"][k] for k in (
                          "usafacts_track_nodes", "usafacts_level_nodes",
                          "usafacts_prerequisite_nodes", "usafacts_descends_from_edges")}},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
