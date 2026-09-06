#!/usr/bin/env python3
"""Register the framework graph's counts and the progress fractions. **Zero model spend.**

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §2.3, §3, §4. DD-040: every figure
quoted resolves to a named Result. Fractions carry their counts and no composite is registered
— that is DD-050's coverage model, and a `framework_readiness_score` Result would be exactly
the composite protocol §3 forbids.

    /opt/anaconda3/bin/python3 scripts/register_framework_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
G = REPO / "framework" / "ai_readiness_framework.json"
P = REPO / "docs" / "progress" / "framework_progress_2026-09-06.json"
RT = REPO / "state" / "framework_roundtrip_2026-09-06.json"


def rows() -> list:
    g = json.loads(G.read_text(encoding="utf-8"))
    p = json.loads(P.read_text(encoding="utf-8"))
    rt = json.loads(RT.read_text(encoding="utf-8"))
    c, w, ms = g["counts"], p["whole"], p["measurement_specs"]
    out = [
        ("framework_indicators", w["indicators"], "graph",
         f"AssessmentIndicator nodes in the framework of record. The skeleton holds "
         f"{rt['indicator_rows_in_skeleton']} indicator ROWS; G1 is two indicator nodes under "
         f"one construct (DD-036's two-leg rule), so nodes = rows + 1. The skeleton header's "
         f"'45 indicators' is STALE — A10 and A11 were added in v0.2.1 and the count was never "
         f"updated."),
        ("framework_criteria", c["criteria"], "graph", "AssessmentCriterion nodes, A-G."),
        ("framework_constructs", c["constructs"], "graph",
         "AssessmentConstruct nodes — the skeleton's Construct column, deduplicated."),
        ("framework_evidenced_by_edges", c["evidenced_by"], "graph",
         "EVIDENCED_BY edges from an indicator to an admitted corpus Document. Written only "
         "where corpus/manifest.json holds the doc_id AND the graph holds a Document node; "
         "neither check dropped anything silently."),
        ("framework_evidenced_by_internal_edges", c["evidenced_by_internal"], "graph",
         "Evidence-cell references that are internal artifacts (a DD, a methodology section, "
         "a harness path) rather than corpus documents."),
        ("framework_roundtrip_unexplained_diffs", len(rt["unexplained_diffs"]), "graph",
         f"DD-050's adoption gate: cells where rendering the JSON back to the skeleton's "
         f"tables does not reproduce v0.2.9 after whitespace normalisation. ZERO across all "
         f"{rt['indicator_rows_rendered']} rows, so the JSON is the framework of record and "
         f"the tables are a rendered projection. A source of truth that cannot reproduce the "
         f"document it replaces is not a source of truth."),
        ("framework_indicators_evidenced", w["evidenced"]["n"], "progress",
         f"Indicators with at least one corpus doc_id in their Evidence cell, of "
         f"{w['evidenced']['of']} ({w['evidenced']['fraction']:.1%}). The skeleton header's "
         f"'25 resolved, 20 gaps' is stale against the same A10/A11 addition."),
        ("framework_indicators_gap", w["gap"]["n"], "progress",
         f"Indicators whose Evidence cell is a registered gap, of {w['gap']['of']}. A gap is a "
         f"demand-pull target (DD-024), not a to-do that was skipped."),
        ("framework_indicators_measured", w["by_measurement_status"]["measured"]["n"], "progress",
         f"Indicators at measurement_status=measured, of {w['indicators']}: G1-D and G1-O, the "
         f"only legs with a built and run harness (DD-036, frozen at v2). Everything else is "
         f"`specified`."),
        ("framework_indicators_specified", w["by_measurement_status"]["specified"]["n"], "progress",
         f"Indicators at measurement_status=specified, of {w['indicators']} — a spec exists, "
         f"no harness has been built."),
        ("framework_public_tier_indicators", p["by_tier"]["public"]["indicators"], "progress",
         "Indicators at tier `public`: runnable by anyone from outside, with no agency "
         "instrumentation and no paid product."),
        ("framework_measurement_specs", ms["total"], "progress",
         f"MeasurementSpec nodes: {ms['auto_legs']} AUTO legs specified against a named "
         f"collector or `none_known`, plus the G1-O harness pointer. No collector was "
         f"installed or run; rules are placeholders (`RULE-<code>-v0`) written by the harness "
         f"task."),
        ("framework_specs_with_named_collector", ms["with_named_collector"]["n"], "progress",
         f"AUTO legs with a named, pinned open-source collector, of "
         f"{ms['with_named_collector']['of']} ({ms['with_named_collector']['fraction']:.0%}): "
         f"httpx, protego, extruct, pyshacl, scrapy, ultimate-sitemap-parser, the Project Open "
         f"Data validator, Lighthouse, and the frozen g1_declared probe."),
        ("framework_specs_collector_none_known", len(ms["none_known"]), "progress",
         f"AUTO legs where NO open-source collector exists: {', '.join(ms['none_known'])}. "
         f"C4-auto needs a generative engine's citations (the EVAL half); E5 is a property of "
         f"the harness's own cycle; F2 and F3 need two vintages, so a single-point scan cannot "
         f"observe them; G3 has no admitted source. This count is the only thing licensing a "
         f"commercial fallback later, and it is recorded now rather than discovered then."),
        ("framework_specs_with_fuji_metric", len(ms["with_fuji_metric"]), "progress",
         f"AUTO legs that genuinely overlap an F-UJI FAIR metric and name its id rather than "
         f"reimplementing it: {', '.join(ms['with_fuji_metric'])} (FsF-A1-03D; FsF-F4-01M + "
         f"FsF-I1-01M; FsF-R1.1-01M). Three of {ms['auto_legs']} — F-UJI measures metadata "
         f"FAIRness and this instrument measures machine-consumability of a published product "
         f"surface, so the overlap being small is the expected result, not a shortfall."),
    ]
    for code, blk in sorted(p["by_criterion"].items()):
        out.append((f"framework_indicators_criterion_{code}", blk["indicators"], "progress",
                    f"Indicators under criterion {code}: {blk['evidenced']['n']} evidenced, "
                    f"{blk['gap']['n']} gaps."))
    return out


SCRIPT = {"graph": "build_framework_graph", "progress": "framework_progress"}
DATA = {"graph": "ai_readiness_framework", "progress": "framework_progress_2026-09-06"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for n, v, s, note in data:
            print(f"{n}\t{v}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    ok = 0
    for n, v, s, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description",
                            f"{note} Derivation: scripts/{SCRIPT[s]}.py ({TASK}).",
                            "--script-name", SCRIPT[s], "--data-name", DATA[s]],
                           capture_output=True, text=True, cwd=REPO)
        ok += 1 if r.returncode == 0 else 0
        if r.returncode:
            print("FAILED:", n, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
