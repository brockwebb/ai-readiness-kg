#!/usr/bin/env python3
"""Register G1 v2 headline numbers as Seldon Results (task 2026-09-03_g1_eval_v2 step 6).

Reads one reviewed v2 results file per split (`dev`, `holdout`, `control`, `pooled_opus`, or a
v1-evidence re-score `rescore_v1_<split>`) and emits one `seldon result register` per number:
per surface_type x compression_level x mode — families, scored, unparseable, L3+ count, rate,
Wilson bounds, level distribution, failure classes, estimate status; per family type; the
genuine-loss count by the reviewer criterion; and the D11 covariate summaries. Every Result is
`computed_from` the split's DataFile and `generated_by` the Script `rescore_g1_v2`, and its
description carries the derivation path into the JSON.

    python3 scripts/register_g1_v2_results.py --split holdout --file assessment/results/g1_v2_holdout_reviewed.json \
        --data-name g1_v2_holdout_reviewed [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _cmd(name, value, desc, data_name):
    return ["seldon", "result", "register", "--value", str(value), "--units", name, "--description", desc,
            "--script-name", "rescore_g1_v2", "--data-name", data_name]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--data-name", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    r = json.loads(Path(a.file).read_text(encoding="utf-8"))
    models = ", ".join(r["g1"]["observed"].get("model_ids") or [])
    base = (f"G1 EVAL v2, split {a.split}, parser {r.get('parser_version')}, scorer {r.get('scorer_version')}, "
            f"model(s) {models}, prompt epochs {', '.join(r['g1']['observed'].get('prompt_epochs') or [])}; "
            f"derivation: scripts/rescore_g1_v2.py -> {a.file} (path in JSON given)")
    cmds = []
    P = f"g1_v2_{a.split}"

    def reg(name, value, path_note):
        if value is None:
            return
        cmds.append(_cmd(f"{P}_{name}", value, f"{base}: {path_note}", a.data_name))

    def cell(prefix, c, path, full=True):
        reg(f"{prefix}_families", c["n"], f"{path}.n (family records)")
        reg(f"{prefix}_scored", c["n_scored"], f"{path}.n_scored")
        reg(f"{prefix}_unparseable", c["n_unparseable"], f"{path}.n_unparseable")
        reg(f"{prefix}_L3plus", c["preserved"], f"{path}.preserved")
        reg(f"{prefix}_preservation_rate", c["preservation_rate"], f"{path}.preservation_rate (L3+ share of scored families)")
        if c["wilson95"][0] is not None:
            reg(f"{prefix}_wilson95_lower", c["wilson95"][0], f"{path}.wilson95[0] (z=1.959964)")
            reg(f"{prefix}_wilson95_upper", c["wilson95"][1], f"{path}.wilson95[1]")
        if full:
            for lvl, n in c["levels"].items():
                reg(f"{prefix}_level_{lvl}", n, f"{path}.levels.{lvl}")
            for fc, n in c["failure_classes"].items():
                reg(f"{prefix}_failure_{fc}", n, f"{path}.failure_classes.{fc}")
            for st, n in c["estimate_status"].items():
                reg(f"{prefix}_estimate_{st}", n, f"{path}.estimate_status.{st}")

    obs = r["g1"]["observed"]
    cell("all", obs["all"], "g1.observed.all")
    reg("all_qualifier_forms", obs.get("n_qualifiers"), "g1.observed.n_qualifiers (published forms behind the families)")
    for mode, c in obs["by_mode"].items():
        cell(mode, c, f"g1.observed.by_mode.{mode}", full=False)
    for comp, c in obs.get("by_compression_indirect", {}).items():
        cell(f"indirect_{comp}", c, f"g1.observed.by_compression_indirect.{comp}")
    for sf, cells in obs.get("by_surface_and_compression", {}).items():
        for comp, c in cells.items():
            cell(f"{sf}_{comp}", c, f"g1.observed.by_surface_and_compression.{sf}.{comp}")
    for fam, modes in obs.get("by_family_and_mode", {}).items():
        for mode, c in modes.items():
            cell(f"family_{fam}_{mode}", c, f"g1.observed.by_family_and_mode.{fam}.{mode}", full=False)
    rv = r.get("review")
    if rv:
        reg("genuine_losses", rv["genuine_losses"], f"review.genuine_losses (reviewer {rv['reviewer']}; criterion on the file)")
        reg("parser_misses", rv["parser_misses"], "review.parser_misses")
        reg("review_queue", rv["queue"], "review.queue (family records at L0/L1/L2 or unparseable)")
    cs = r.get("covariate_summaries") or {}
    for comp, q in cs.get("compression_ratio_by_level", {}).items():
        if q.get("n"):
            reg(f"compression_ratio_{comp}_median", q["median"], f"covariate_summaries.compression_ratio_by_level.{comp}.median (passage tokens / response tokens)")
            reg(f"compression_ratio_{comp}_n", q["n"], f"covariate_summaries.compression_ratio_by_level.{comp}.n")
    rd = cs.get("relative_deviation_among_L0") or {}
    if rd.get("n"):
        reg("relative_deviation_L0_median", rd["median"], "covariate_summaries.relative_deviation_among_L0.median (signed, restated vs source)")
        reg("relative_deviation_L0_n", rd["n"], "covariate_summaries.relative_deviation_among_L0.n")
    for d, n in (cs.get("rounding_direction_among_L0") or {}).items():
        reg(f"L0_rounding_{d}", n, f"covariate_summaries.rounding_direction_among_L0.{d}")
    ex = r.get("expectations_v2") or {}
    for k, v in ex.items():
        if k == "E4":
            for comp, c in v["by_level"].items():
                if c.get("loss_rate") is not None:
                    reg(f"E4_loss_rate_{comp}", c["loss_rate"], f"expectations_v2.E4.by_level.{comp}.loss_rate ({v['verdict']})")
        if k == "E6":
            for comp in ("none", "tight"):
                if v[comp].get("rate") is not None:
                    reg(f"E6_L2_rate_{comp}", v[comp]["rate"], f"expectations_v2.E6.{comp}.rate ({v['verdict']})")
    if a.dry_run:
        print("\n".join(" ".join(c[:6]) for c in cmds))
        print(len(cmds), "results")
        return 0
    ok = 0
    for c in cmds:
        out = subprocess.run(c, capture_output=True, text=True, cwd=REPO)
        if out.returncode == 0:
            ok += 1
        else:
            print("FAILED:", c[5], out.stderr.strip()[-200:])
    print(f"registered {ok}/{len(cmds)} Results for split {a.split}")
    return 0 if ok == len(cmds) else 1


if __name__ == "__main__":
    raise SystemExit(main())
