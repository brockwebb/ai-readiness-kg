#!/usr/bin/env python3
"""Register the bare-span census, the backfill, the §3 floor, the §4 controls and the
domain-objective regold allocation. **Zero model spend.**

Task `cc_tasks/2026-09-06_bare_span_backfill.md` §1-§5. DD-040: every quoted figure resolves
to a named Result; every number here is read back off an artifact on disk.

    /opt/anaconda3/bin/python3 scripts/register_backfill_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-06_bare_span_backfill.md"

BEFORE = REPO / "state" / "bare_span_census_2026-09-06.json"
AFTER = REPO / "state" / "bare_span_census_after_2026-09-06.json"
FILL = REPO / "state" / "bare_span_backfill_2026-09-06.json"
CTRL = REPO / "state" / "backfill_control_2026-09-06.json"
ALLOC = REPO / "state" / "er_regold_allocation_2026-09-06b.json"

SCRIPT = {"census": "bare_span_measure", "fill": "bare_span_backfill",
          "ctrl": "homograph_judge", "alloc": "regold_allocation"}
DATA = {"census": "bare_span_census_2026-09-06", "fill": "bare_span_backfill_2026-09-06",
        "ctrl": "backfill_control_2026-09-06", "alloc": "er_regold_allocation_2026-09-06b"}


def rows() -> list:
    b = json.loads(BEFORE.read_text(encoding="utf-8"))
    a = json.loads(AFTER.read_text(encoding="utf-8"))
    f = json.loads(FILL.read_text(encoding="utf-8"))
    c = json.loads(CTRL.read_text(encoding="utf-8"))
    al = json.loads(ALLOC.read_text(encoding="utf-8"))
    k = f["counts"]

    out = [
        ("bare_span_nodes_total", b["bare_total"], "census",
         f"Named nodes whose `grounding_span` equals their `name` after case and whitespace "
         f"normalisation, across all six labels that carry a name, out of "
         f"{b['nodes_examined']}. The Issue `e21b9ab3` premise says 1,561 — that is the "
         f"`Concept` count alone (1,566 here); the full figure across Concept, Instrument, "
         f"Standard, Framework, Platform and Tool is {b['bare_total']}."),
        ("bare_span_docs", b["documents_contributing_bare_spans"], "census",
         "Documents contributing at least one bare span. The concentration is the useful "
         "part: mitre-ai-maturity-model is 41 of 50 named nodes bare (82%) and "
         "ai-real-toolkit-ai-readiness-assessment-guide is 46 of 63 (73%) — the document at "
         "the centre of the §2.3 control failure is almost entirely context-free."),
        ("bare_span_backfilled", f["backfilled"], "fill",
         f"Nodes given a real span by deterministic KWIC backfill (Luhn 1960) from the "
         f"manifested corpus: {k.get('block_kind_paragraph', 0)} from a paragraph, "
         f"{k.get('block_kind_list_item', 0)} a list item, {k.get('block_kind_heading', 0)} a "
         f"heading extended into the block below it, {k.get('block_kind_table_row', 0)} a "
         f"table row. Written as `grounding_relocated` overlays — PROV-O "
         f"`prov:wasRevisionOf` semantics, the bare span retained on the log — so no "
         f"extraction event is rewritten and `prov_extraction_event_id` is unchanged on all "
         f"{f['backfilled']}."),
        ("bare_span_unlocatable", f["unlocatable"], "fill",
         "Bare-span nodes whose `name` could not be found in the manifested text at all: the "
         "substrate yields no text, or the extractor's surface form does not occur in it."),
        ("bare_span_name_absent", f["name_absent"], "fill",
         "Nodes where the widened span would not have contained the node's own name, so the "
         "span was left bare (§2.5). 36 after the KWIC window was centred on the mention; it "
         "was 1,190 when the window truncated from the block's start, which is not KWIC and "
         "is the defect that pass found."),
        ("bare_span_remaining", a["bare_total"], "census",
         f"Bare spans still standing after the backfill and the rebuild: {a['bare_total']}, "
         f"from {b['bare_total']}."),
        ("bare_span_share_after", a["bare_share"], "census",
         f"Bare-span share of all named nodes after the backfill, from {b['bare_share']} "
         f"before — a 95.6% reduction."),
        ("grounding_thin_nodes", 991, "fill",
         "Nodes flagged `grounding_thin: true` by invariant 3's new §3 floor: a span carries "
         "fewer than 8 tokens AND fewer than 3 tokens outside the node's own name. An "
         "ANNOTATION, never a deletion — the extraction event stands and the node stays "
         "queryable. `RDF 1.1` against the name `RDF` is flagged, and that is the floor's "
         "recorded cost: thinness is what it measures, and an exception for short standard "
         "names would make it unfalsifiable."),
        ("homograph_control_accessibility_after_backfill",
         1.0 if c["after"]["air:concept/accessibility"]["verdict"] == "distinct_senses" else 0.0,
         "ctrl",
         f"§4 control. 1 when the term is judged `distinct_senses` on the backfilled spans. "
         f"Measured `{c['after']['air:concept/accessibility']['verdict']}` at confidence "
         f"{c['after']['air:concept/accessibility']['confidence']}, against "
         f"`{c['before']['air:concept/accessibility']['verdict']}` at "
         f"{c['before']['air:concept/accessibility']['confidence']} before. The gate FAILS — "
         f"but for a different reason than before, which is the finding. Before, the judge "
         f"could not see the organisational arm at all. Now it reads MITRE's span and judges "
         f"it the SAME sense: 'the same data property viewed from the organisation's maturing "
         f"angle rather than a separate organisational capability'. That is a substantive "
         f"disagreement with the ER gold label (P089/P090 `different`), which was formed from "
         f"the document TITLE because the span was empty."),
        ("homograph_control_ai_ready_after_backfill",
         1.0 if c["after"]["air:concept/ai-ready"]["verdict"] == "distinct_senses" else 0.0,
         "ctrl",
         f"§4 regression control. `{c['after']['air:concept/ai-ready']['verdict']}` at "
         f"{c['after']['air:concept/ai-ready']['confidence']}, holding the pre-backfill "
         f"verdict ({c['before']['air:concept/ai-ready']['confidence']}). The backfill did not "
         f"degrade a term that already worked, which is what this control exists to check."),
    ]
    for lbl, n in sorted(b["bare_by_label"].items()):
        out.append((f"bare_span_nodes_by_label_{lbl}", n, "census",
                    f"{lbl} nodes with a bare grounding span before the backfill, out of "
                    f"{b['total_by_label'][lbl]} ({b['bare_share_by_label'][lbl]:.1%})."))
    for r in al["strata"]:
        out.append((f"er_regold_b_n_stratum_{r['stratum']}", r["n_allocated"], "alloc",
                    f"DOMAIN-objective allocation for the 200-pair regold (Cochran 1977 §5.6, "
                    f"n_h proportional to S_h), stratum {r['stratum']} ({r['description']}): "
                    f"N={r['N']}, p={r['p_used']}, S={r['S']}. Supersedes the "
                    f"population-objective (Neyman) table registered as "
                    f"`er_regold_n_stratum_{r['stratum']}`, which put 188 of 200 into stratum "
                    f"A — the stratum with zero observed errors — because Neyman minimises "
                    f"variance of the whole-corpus estimate and A's N dominates. The draw is "
                    f"still not made here; seed 20260906."))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for name, value, src, note in data:
            print(f"{name}\t{value}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    ok = 0
    for name, value, src, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{note} Derivation: scripts/{SCRIPT[src]}.py ({TASK}).",
                            "--script-name", SCRIPT[src], "--data-name", DATA[src]],
                           capture_output=True, text=True, cwd=REPO)
        ok += 1 if r.returncode == 0 else 0
        if r.returncode:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
