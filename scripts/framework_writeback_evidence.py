#!/usr/bin/env python3
"""Carry an indicator's EVIDENCE cell from the skeleton into the framework of record.
**Zero spend, no network.**

Task `cc_tasks/2026-09-11_a3_a10_sources.md` §1 and decision 2. A3 and A10 reached no source
document, so two of the published report's seven checks rested on an uncited indicator
(`cc_tasks/2026-09-11_l0_report_cycle4_revision_RESULT.md` §6). The citation belongs in the
skeleton, which is where the framework is authored; this carries that one cell into the JSON.

**Why not just re-run `scripts/build_framework_graph.py`.** Because it regenerates the whole
file from the skeleton, and the file has been WRITTEN BACK to ever since: the measurement specs,
every `MEASURED_BY` edge, the `measured_by` blocks, A12's adoption as a candidate under
criterion G (DD-054), the recorded spec decisions. A full rebuild was run once here and dropped
**22 `MEASURED_BY` edges, three of A12's internal refs, and A12's construct out of criterion G**
— 843 deleted lines — and it did so silently, because regenerating is exactly what it is for.
The skeleton is the source of the AUTHORED cells; it is not the source of the whole record.

So this is a write-back like every other one, through the one helper
(`scripts/framework_writeback.py`) that recounts, writes and logs the event with the sha256 of
the bytes. What it touches is stated per indicator and nothing else moves.

**Nothing here parses evidence.** `build_framework_graph.evidence_edges` does it, against
`corpus/manifest.json`, so the rule that a `doc_id` becomes an edge ONLY if the manifest holds
it is the same code in both paths rather than two that agree today. A `doc_id` the manifest does
not hold is reported and refused, never written as an edge to a document nobody admitted.

`tests/test_framework_graph.py::test_the_round_trip_reproduces_every_row_cell_for_cell` is what
makes this safe: the JSON must render back to the skeleton cell for cell, so a write-back that
carried the cell inexactly fails there rather than leaving the two quietly apart.

    /opt/anaconda3/bin/python3 scripts/framework_writeback_evidence.py --indicator A3 \\
        --indicator A10 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import build_framework_graph as bfg                                 # noqa: E402
import framework_writeback as fw                                    # noqa: E402

TASK = "cc_tasks/2026-09-11_a3_a10_sources.md"
SCRIPT = "scripts/framework_writeback_evidence.py"


def skeleton_rows() -> dict:
    """`{code: row}` as the parser reads the skeleton — the same parse the builder uses."""
    rows, unparsed = bfg.parse(bfg.SKELETON.read_text(encoding="utf-8"))
    if unparsed:
        raise SystemExit(f"FATAL: {len(unparsed)} skeleton row(s) do not parse; fix the table "
                         f"before carrying a cell out of it: {unparsed[:2]}")
    return {r["code"]: r for r in bfg.split_g1(rows)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--indicator", action="append", required=True, metavar="CODE",
                    help="indicator code whose evidence cell to carry over (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)

    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    rows = skeleton_rows()
    manifest_ids = set(json.loads(
        (REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"])

    nodes = {n["properties"].get("code"): n for n in g["nodes"]
             if "AssessmentIndicator" in n["labels"]}
    changes, refused = {}, []
    for code in a.indicator:
        if code not in rows:
            raise SystemExit(f"FATAL: {code} is not a row in the skeleton")
        if code not in nodes:
            raise SystemExit(f"FATAL: {code} has no AssessmentIndicator node in the record")
        row, node = rows[code], nodes[code]
        iid = node["id"]
        real, internal, gap = bfg.evidence_edges(row, manifest_ids)

        # Every backticked slug the cell names that the manifest does NOT hold. Reported and
        # refused: an EVIDENCED_BY edge to an unadmitted document is a citation a stranger
        # cannot follow, which is the whole thing this task is about.
        named = bfg._DOCID.findall(row["evidence_raw"])
        refused += [(code, d) for d in dict.fromkeys(named) if d not in manifest_ids]

        before = sorted(e["to"] for e in g["edges"]
                        if e["from"] == iid and e["type"] == "EVIDENCED_BY")
        g["edges"] = [e for e in g["edges"]
                      if not (e["from"] == iid and
                              e["type"] in ("EVIDENCED_BY", "EVIDENCED_BY_INTERNAL"))]
        for d in real:
            g["edges"].append({"from": iid, "type": "EVIDENCED_BY", "to": f"doc:{d}",
                               "properties": {"doc_id": d}})
        for ref in internal:
            g["edges"].append({"from": iid, "type": "EVIDENCED_BY_INTERNAL",
                               "to": f"internal:{ref}", "properties": {"artifact_path": ref}})
        node["properties"]["evidence_raw"] = row["evidence_raw"]
        node["properties"]["gap"] = gap
        changes[code] = {
            "evidenced_by_before": before,
            "evidenced_by_after": sorted(f"doc:{d}" for d in real),
            "evidenced_by_internal_after": sorted(f"internal:{r}" for r in internal),
            "gap_before_was_set": bool(node["properties"].get("gap")) or gap is None,
            "gap_after": gap,
        }

    if refused:
        for code, d in refused:
            print(f"REFUSED {code}: `{d}` is not in corpus/manifest.json", file=sys.stderr)
        raise SystemExit("FATAL: an evidence cell names a document the corpus has not "
                         "admitted; admit it through `python -m kg.manifest add` (then the "
                         "Dixie sweep and `rebuild`) or remove it from the cell. Nothing was "
                         "written.")

    out = fw.save(g, script=SCRIPT, task=TASK, changes=changes, dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({k: v for k, v in out.items() if k != "changes"}, indent=1))
    print(json.dumps(changes, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
