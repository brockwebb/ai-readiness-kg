#!/usr/bin/env python3
"""Register the D14 pre-registered statements' counts as Seldon Results (task
2026-09-03_g1_freeze_calibration_redefinition_findings, step 3). **Zero model calls.**

`scripts/register_g1_v2_results.py` registered the E4 loss rates and the E6 L2 rates but not
the counts behind E5, H3, H4, H5 and C1, so §3 of the findings memo could not cite them without
literals. They are read here from a results file's own `expectations_v2` block — the same block
`harness/g1_expectations.py` computed at score time — and never retyped.

    g1_v2_expect_E5_{failures_at_tight,L0,L1,L2}
    g1_v2_expect_H3_{table_coded,prose_labeled}_{n,preserved,lost,loss_rate}
    g1_v2_expect_H4_{flagged_cell_reliability,interval_all_surfaces}_{n,preserved,lost,loss_rate}
    g1_v2_expect_H5_{footnoted,inline,tercile_low,tercile_mid,tercile_high}_{n,preserved,lost,loss_rate}
    g1_v2_expect_H5_distance_cut_{low_mid,mid_high}
    g1_v2_expect_C1_{level}_{control,consumer}_loss_rate          (from the C1 comparison file)

Verdict words ("supported", "underpowered") are not numbers and stay in the file; the memo
quotes them and cites the block.

    /opt/anaconda3/bin/python3 scripts/register_g1_expectation_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "assessment" / "results"
POOLED = RESULTS / "g1_v2_pooled_opus_reviewed.json"
C1FILE = RESULTS / "g1_v2_c1_control_vs_opus.json"
TASK = "cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md"

CELL_FIELDS = ("n", "preserved", "lost", "loss_rate")


def _cell(prefix: str, cell: dict, where: str) -> list:
    out = []
    for f in CELL_FIELDS:
        if cell.get(f) is None:
            continue
        out.append((f"{prefix}_{f}", cell[f], f"{where}.{f}"))
    return out


def rows() -> list:
    e = json.loads(POOLED.read_text(encoding="utf-8"))["expectations_v2"]
    P = "g1_v2_expect"
    src = "assessment/results/g1_v2_pooled_opus_reviewed.json expectations_v2"
    out: list = []

    v = e["E5"]
    out.append((f"{P}_E5_failures_at_tight", v["failures_at_tight"],
                f"{src}.E5.failures_at_tight (scored families below L3 at compression tight; verdict {v['verdict']})"))
    for lvl, n in v["by_level"].items():
        out.append((f"{P}_E5_{lvl}", n, f"{src}.E5.by_level.{lvl} (failures at tight at that level)"))
    for fc, n in v["failure_classes"].items():
        out.append((f"{P}_E5_class_{fc}", n, f"{src}.E5.failure_classes.{fc}"))

    v = e["H3"]
    for arm in ("table_coded", "prose_labeled"):
        out += _cell(f"{P}_H3_{arm}", v[arm], f"{src}.H3.{arm} (verdict {v['verdict']}; {v['direction']})")

    v = e["H4"]
    for arm in ("flagged_cell_reliability", "interval_all_surfaces"):
        out += _cell(f"{P}_H4_{arm}", v[arm], f"{src}.H4.{arm} (verdict {v['verdict']})")

    v = e["H5"]
    for arm in ("footnoted", "inline"):
        out += _cell(f"{P}_H5_{arm}", v[arm], f"{src}.H5.{arm} (verdict {v['verdict']})")
    t = v["by_distance_tercile"]
    for arm in ("low", "mid", "high"):
        if arm in t:
            out += _cell(f"{P}_H5_tercile_{arm}", t[arm], f"{src}.H5.by_distance_tercile.{arm}")
    cuts = t.get("cuts") or []
    for name, cut in zip(("low_mid", "mid_high"), cuts):
        out.append((f"{P}_H5_distance_cut_{name}", cut,
                    f"{src}.H5.by_distance_tercile.cuts ({name} boundary, footnote_distance_chars)"))

    if C1FILE.exists():
        c1 = json.loads(C1FILE.read_text(encoding="utf-8"))
        by = c1.get("by_level") or (c1.get("C1") or {}).get("by_level") or {}
        for lvl, cell in by.items():
            for arm in ("control", "consumer"):
                if isinstance(cell.get(arm), dict) and cell[arm].get("loss_rate") is not None:
                    out.append((f"{P}_C1_{lvl}_{arm}_loss_rate", cell[arm]["loss_rate"],
                                f"assessment/results/g1_v2_c1_control_vs_opus.json by_level.{lvl}.{arm}.loss_rate "
                                f"(control claude-haiku-4-5-20251001 beside the pinned consumer on the holdout "
                                f"grid; never pooled)"))
                    out.append((f"{P}_C1_{lvl}_{arm}_n", cell[arm]["n"],
                                f"assessment/results/g1_v2_c1_control_vs_opus.json by_level.{lvl}.{arm}.n"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for name, value, note in data:
            print(f"{name}\t{value}\t{note[:110]}")
        print(len(data), "Results")
        return 0
    ok = 0
    data = data[a.skip:]
    for name, value, note in data:
        cmd = ["seldon", "result", "register", "--value", str(value), "--units", name,
               "--description", (f"G1 EVAL v2 pre-registered statement (D14), pooled pinned consumer "
                                 f"claude-opus-5, parser g1-parse-v2, scorer g1-score-v2; registered by "
                                 f"scripts/register_g1_expectation_results.py for {TASK}: {note}"),
               "--script-name", "rescore_g1_v2", "--data-name", "g1_v2_pooled_opus_reviewed"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-200:])
    print(f"registered {ok}/{len(data)} expectation Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
