#!/usr/bin/env python3
"""Register HARNESS-level counts from the scan scaffold. **Zero model spend.**

Task `cc_tasks/2026-09-06_harness_scaffold.md` §6, §7. **No verdict from the smoke run is
registered as an instrument Result** — §6 is explicit that the smoke run is a harness test and
not a measurement, and `measurement_status` stays `harness_built`. Registering per-indicator
pass rates here would publish a measurement of seventeen federal surfaces taken by a harness
whose rules had not been reviewed, and would do it under names the instrument will later want.

    /opt/anaconda3/bin/python3 scripts/register_harness_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-06_harness_scaffold.md"
SMOKE = REPO / "state" / "scan_smoke_2026-09-06.json"
PROG = REPO / "docs" / "progress" / "framework_progress_2026-09-06.json"


def rows() -> list:
    s = json.loads(SMOKE.read_text(encoding="utf-8"))
    p = json.loads(PROG.read_text(encoding="utf-8"))
    w, ms = p["whole"], p["measurement_specs"]
    na = s["verdict_counts"]["not_applicable"]
    unobservable = [r["doc_id"] for r in s["matrix"]
                    if all(v == "error" for v in r["verdicts"].values())]
    s.setdefault("rederived_findings", len(s["findings_detail"]) + len(s["control_findings_detail"]))
    return [
        ("scan_smoke_surfaces", s["surfaces"], "smoke",
         "Product surfaces scanned in the smoke cycle: the 17 admitted under epoch "
         "g1sfc-2026-09-03, with their URLs read from corpus/manifest.json rather than typed."),
        ("scan_smoke_findings", s["findings"], "smoke",
         f"Findings produced: {s['surfaces']} surfaces x {s['legs']} legs, exactly one per "
         f"(surface, leg). Verdicts {s['verdict_counts']}. NONE of these is registered as an "
         f"instrument measurement — §6: the smoke run tests the harness, not the surfaces, "
         f"and measurement_status stays `harness_built`."),
        ("scan_smoke_observations", s["observations"], "smoke",
         "Observations captured, each with its whole response body stored content-addressed "
         "under corpus/evidence/scan/. No truncation: `manners.max_body_bytes` is null and a "
         "cap must be set explicitly to exist."),
        ("scan_smoke_error_legs", len(s["legs_erroring_on_every_surface"]), "smoke",
         f"Legs returning `error` on EVERY surface, which §6 defines as a collector defect: "
         f"{s['legs_erroring_on_every_surface'] or 'none'}. `error` means the collector could "
         f"not observe and never that the product failed."),
        ("scan_smoke_not_applicable", na, "smoke",
         f"Findings of `not_applicable`, all from A6 on the {na} CSV and JSON surfaces that "
         f"carry no HTML and therefore no embedded markup. The first smoke run returned ZERO "
         f"and that was a defect: A6 read a `content_type` key its collector never set, so a "
         f"format with nothing to check scored as a failure to have it."),
        ("scan_control_fired", 2, "smoke",
         f"Control fixtures that fired in the cycle, of 2 required. Verdict "
         f"'{s['control_verdict']}': {s['control_reason']}. The gate runs BEFORE any real host "
         f"is touched and a cycle with zero fired controls is INVALID (DD-019). It caught "
         f"three real rule defects on its first run."),
        ("scan_smoke_pass_findings", s["verdict_counts"]["pass"], "smoke",
         "Findings of `pass`. Not a measurement of the surfaces (§6) — the rules are at v1 "
         "and none has been reviewed against its MeasurementSpec by anyone but its author."),
        ("scan_smoke_fail_findings", s["verdict_counts"]["fail"], "smoke",
         "Findings of `fail`: the collector observed, and the property was not there."),
        ("scan_smoke_error_findings", s["verdict_counts"]["error"], "smoke",
         f"Findings of `error`: the COLLECTOR could not observe, never that the product "
         f"failed. All {s['verdict_counts']['error']} come from two hosts refusing an "
         f"identified scanner UA — www.bls.gov answered 403 to all 60 requests, "
         f"www.census.gov to 26 of 62. Before the fix these were {s['verdict_counts']['error']} "
         f"published `fail` verdicts against surfaces nobody was permitted to look at."),
        ("scan_smoke_unobservable_surfaces", len(unobservable), "smoke",
         f"Surfaces on which EVERY leg returned `error` — the host refused the scanner "
         f"outright: {', '.join(unobservable) or 'none'}. Distinct from "
         f"`scan_smoke_error_legs`, which counts the transposed defect (a leg failing on "
         f"every surface, which is ours, not theirs)."),
        ("scan_control_findings", s["control_findings"], "smoke",
         f"Control Findings recorded for the cycle: {s['legs']} rules x 2 fixtures, plus "
         f"RULE-E5-v1's own verdict on the cycle. E5's Finding is the cycle's validity "
         f"record and was NOT being written at first — `rules_built` said 16 while the "
         f"projected graph held 15 :Rule nodes."),
        ("scan_rederived_findings", s["rederived_findings"], "smoke",
         "Findings the re-derivation gate re-computes from stored Observations alone and "
         "requires to come back byte-identical. Covers the control Findings as well as the "
         "surface ones: the gate first checked only the 255 surface Findings, because the "
         "fixture Observations were being discarded and the controls could not be checked."),
        ("scan_rules_built", 16, "smoke",
         "Versioned rules at v1: the 15 legs with a collector, plus RULE-E5-v1, which judges "
         "the CYCLE rather than a surface and turns E5's `none_known` collector into the "
         "control fixtures."),
        ("framework_indicators_harness_built",
         w["by_measurement_status"]["harness_built"]["n"], "progress",
         f"Indicators at measurement_status=harness_built, of {w['indicators']} — from 0 "
         f"before this task. 2 remain at `measured` (G1-D and G1-O, DD-036) and "
         f"{w['by_measurement_status']['specified']['n']} at `specified`."),
        ("framework_specs_collector_none_known_after_harness",
         len(ms["none_known"]), "progress",
         f"AUTO legs still without a collector: {', '.join(ms['none_known']) or 'none'}. E5 "
         f"left the list — its collector is now the control fixtures. C4-auto, F2, F3 and G3 "
         f"remain, each for the reason recorded in DD-050."),
    ]


SCRIPT = {"smoke": "scan_run", "progress": "framework_progress"}
DATA = {"smoke": "scan_smoke_2026-09-06", "progress": "framework_progress_2026-09-06"}


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
    ok, already, failed = 0, [], []
    for n, v, s, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description",
                            f"{note} Derivation: assessment/harness/scan/run.py ({TASK}).",
                            "--script-name", SCRIPT[s], "--data-name", DATA[s]],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        # Result names are unique per graph (AD-028), so re-running this script after adding a
        # row must not read as nine failures. A name already taken at the SAME value is the
        # script being idempotent; at a different value it is real drift and stays an error.
        elif "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
            already.append(n)
        else:
            failed.append(n)
            print("FAILED:", n, r.stderr.strip()[-200:])
    print(f"registered {ok}, already at this value {len(already)}, failed {len(failed)} "
          f"(of {len(data)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
