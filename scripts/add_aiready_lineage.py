#!/usr/bin/env python3
"""Write the AI-ready lineage layer into the framework record: the four USAFacts criteria, the
three extension groups the project added, and the DESCENDS_FROM edge from each of the sixteen
instrument checks up to the criterion or group it operationalizes. **Zero spend.**

`cc_tasks/2026-11-02_icsp_rollup_of_the_sixteen_checks.md` Part A, implementing DN-005 section 2.1
(the validity layer) at the level an ICSP member reads: the line from each check to the AI-ready
data framework the operator operationalized and extended. The roll-up build product (Part B)
renders this lineage rather than restating it.

Two sources, transcribed verbatim, with provenance on each node:

* **The four `AiReadyCriterion` nodes** carry the guide's own one-sentence statement of the
  criterion, verbatim from the corpus copy `state/docling_md/usafacts-ai-ready-data-guide.md`
  (the numbered statement heading under each criterion name). That file is gitignored, so it is
  not in a clean worktree; the text is embedded here as a literal with the docling line range it
  was transcribed from, the same way `apply_fcsm_concerns.py` embeds DN-018's fixed constants.
  The guide gives each criterion a one-sentence statement heading, so no criterion falls back to
  its first body sentence (Part A item 1).
* **The three `ExtensionGroup` nodes** carry the construct-list sentence of their bullet in the
  operationalization brief's "Shape of the instrument" section
  (`docs/crosswalk/usafacts_operationalization_brief.md`), verbatim. The bold label, the indicator
  count, and the `*Exemplar*` sentence are not part of the stored text: the first because it is
  not a sentence, the count because it is a bare number, and the exemplar because it names check
  codes (A6, C2, ...) the rendered roll-up forbids.

Through `scripts/framework_writeback.py::save` only (the single-writer rule,
`tests/test_framework_single_writer.py`): this module builds the nodes and edges in memory and
hands them to `save`, which recounts, refuses any drop without `--force --reason`, and puts the
delta on the `framework_writeback` event. A re-run upserts by identity and so writes the same
bytes (`save` reports `unchanged`). A write-back is not finished until a projection follows it
(DD-057): run `scripts/load_framework_graph.py` and `tests/test_framework_projection_roundtrip.py`.

    /opt/anaconda3/bin/python3 scripts/add_aiready_lineage.py [--dry-run] [--force --reason TEXT]
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

SCRIPT = "scripts/add_aiready_lineage.py"
TASK = "cc_tasks/2026-11-02_icsp_rollup_of_the_sixteen_checks.md"

CRITERION_SOURCE = "USAFacts 2026 (usafacts-ai-ready-data-guide)"
#: The docling copy the criterion statements were transcribed from, for the build report / RESULT.
DOCLING = "state/docling_md/usafacts-ai-ready-data-guide.md"
BRIEF = "docs/crosswalk/usafacts_operationalization_brief.md"

#: The four USAFacts criteria. `text` is the guide's own one-sentence statement of the criterion,
#: verbatim from the numbered statement heading under the criterion name; `docling_lines` names the
#: criterion-name line and the statement-heading line it was read from (Part A item 1).
CRITERIA = [
    {"id": "aiready:accessible", "letter": "A", "name": "Accessible",
     "text": "Data Must Be Machine-Readable and Easy to Access",
     "docling_lines": "37 (name), 39 (statement)"},
    {"id": "aiready:understandable", "letter": "B", "name": "Understandable",
     "text": "Data Must Be Machine Understandable with Easily Retrievable, WellStructured "
             "Documentation and Metadata",
     "docling_lines": "54 (name), 56 (statement)"},
    {"id": "aiready:accurate", "letter": "C", "name": "Accurate",
     "text": "Agencies Should Provide Clear Evaluation Benchmarks and Make Them Public",
     "docling_lines": "72 (name), 74 (statement)"},
    {"id": "aiready:open", "letter": "D", "name": "Open",
     "text": "Data Must Be Unencumbered and Open to All Citizens",
     "docling_lines": "87 (name), 89 (statement)"},
]

#: The three extension groups the project added (delta table B: E, F, G are additions). `text` is
#: the construct-list sentence of the group's bullet in the brief's "Shape of the instrument"
#: section, verbatim; `brief_lines` names the bullet line it was read from.
EXTENSION_GROUPS = [
    {"id": "ext:E", "letter": "E", "name": "TEVV loop",
     "text": "Verification/validation split, pre-registered acceptance thresholds, instrument "
             "versioning, contamination policy, positive controls, failure attribution, "
             "corrective-action closure, drift sentinels, adversarial evaluation.",
     "brief_lines": "37"},
    {"id": "ext:F", "letter": "F", "name": "Release engineering",
     "text": "Pre-release gates, contract stability, vintage-transition regression, change "
             "legibility, staged rollout, release authenticity.",
     "brief_lines": "38"},
    {"id": "ext:G", "letter": "G", "name": "Statistical-system constructs",
     "text": "Uncertainty legibility, revision semantics, classification identity, authority "
             "metadata, disclosure semantics, measurement-protocol provenance.",
     "brief_lines": "39"},
]

#: letter -> lineage node id. DESCENDS_FROM is routed by the check's code letter (Part A item 3).
LETTER_TO_NODE = {c["letter"]: c["id"] for c in CRITERIA}
LETTER_TO_NODE.update({e["letter"]: e["id"] for e in EXTENSION_GROUPS})


def criterion_nodes() -> list[dict]:
    out = []
    for c in CRITERIA:
        out.append({"id": c["id"], "labels": ["AiReadyCriterion"], "properties": {
            "letter": c["letter"], "name": c["name"], "text": c["text"],
            "source": CRITERION_SOURCE, "source_file": DOCLING,
            "docling_lines": c["docling_lines"]}})
    return out


def extension_group_nodes() -> list[dict]:
    out = []
    for e in EXTENSION_GROUPS:
        out.append({"id": e["id"], "labels": ["ExtensionGroup"], "properties": {
            "letter": e["letter"], "name": e["name"], "text": e["text"],
            "source": BRIEF, "brief_section": "Shape of the instrument",
            "brief_lines": e["brief_lines"]}})
    return out


def instrument_specs(g: dict) -> list[tuple[str, str]]:
    """`(leg, spec_id)` for the sixteen instrument checks (`instrument_state` set)."""
    out = []
    for n in g["nodes"]:
        p = n["properties"]
        if "MeasurementSpec" in n["labels"] and p.get("instrument_state"):
            out.append((p["leg"], n["id"]))
    return out


def descends_from_edges(g: dict) -> list[dict]:
    """One DESCENDS_FROM edge per instrument spec, to the criterion or group its code letter
    names. Fails loudly if a leg's letter has no lineage node, or if the count is not sixteen."""
    specs = instrument_specs(g)
    if len(specs) != 16:
        raise SystemExit(f"FATAL: {len(specs)} instrument specs, expected 16: "
                         f"{sorted(l for l, _ in specs)}")
    edges = []
    for leg, spec_id in specs:
        letter = leg[0]
        if letter not in LETTER_TO_NODE:
            raise SystemExit(f"FATAL: check {leg} has code letter {letter!r} with no lineage node")
        edges.append({"from": spec_id, "type": "DESCENDS_FROM", "to": LETTER_TO_NODE[letter]})
    return edges


def build(g: dict) -> dict:
    """Upsert the seven lineage nodes and sixteen edges into `g` by identity, and set the three
    counts keys. Idempotent: a second call reproduces the same record (so `save` writes nothing)."""
    nodes = criterion_nodes() + extension_group_nodes()
    edges = descends_from_edges(g)

    by_id = {n["id"]: i for i, n in enumerate(g["nodes"])}
    for node in nodes:
        if node["id"] in by_id:
            g["nodes"][by_id[node["id"]]] = node
        else:
            g["nodes"].append(node)
    eidx = {fw._edge_key(e): i for i, e in enumerate(g["edges"])}
    for e in edges:
        k = fw._edge_key(e)
        if k in eidx:
            g["edges"][eidx[k]] = e
        else:
            g["edges"].append(e)
    g.setdefault("counts", {})
    g["counts"]["aiready_criterion_nodes"] = len(CRITERIA)
    g["counts"]["extension_group_nodes"] = len(EXTENSION_GROUPS)
    g["counts"]["descends_from_edges"] = len(edges)
    return g


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    g = build(fw.load())
    ev = fw.save(g, script=SCRIPT, task=TASK,
                 changes={"implements": "DN-005 section 2.1",
                          "aiready_criterion_nodes": g["counts"]["aiready_criterion_nodes"],
                          "extension_group_nodes": g["counts"]["extension_group_nodes"],
                          "descends_from_edges": g["counts"]["descends_from_edges"]},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({"written": ev["written"], "unchanged": ev.get("unchanged", False),
                      "event_id": ev.get("event_id"), "framework_sha256": ev["framework_sha256"],
                      "delta": ev["delta_summary"], "counts": {
                          "aiready_criterion_nodes": g["counts"]["aiready_criterion_nodes"],
                          "extension_group_nodes": g["counts"]["extension_group_nodes"],
                          "descends_from_edges": g["counts"]["descends_from_edges"]}},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
