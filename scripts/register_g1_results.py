#!/usr/bin/env python3
"""Register G1 v1 headline numbers as Seldon Results (task 2026-09-03 step 6).

Reads one reviewed results file per split (dev / holdout / pooled) and emits one
`seldon result register` per number: per class x mode x split — n, scored, unparseable,
L3+ count, rate, Wilson bounds; level distribution; failure-class counts; estimate-status
counts; and the genuine-loss count (reviewer = CC, criterion recorded on the file). Every
Result is `computed_from` the split's DataFile and `generated_by` the rescore Script, and
its description carries the derivation path into the JSON.

    python3 scripts/register_g1_results.py --split dev --file assessment/results/g1_v1_dev_reviewed.json --data-name g1_v1_dev_reviewed [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _cmd(name, value, desc, data_name):
    return ["seldon", "result", "register", "--value", str(value), "--units", name, "--description", desc,
            "--script-name", "rescore_g1", "--data-name", data_name]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "holdout", "pooled", "prefix_v0", "prefix_v1"])
    ap.add_argument("--file", required=True)
    ap.add_argument("--data-name", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    r = json.loads(Path(a.file).read_text(encoding="utf-8"))
    pv = r.get("parser_version", "?")
    base = (f"G1 EVAL v1, split {a.split}, parser {pv}, model claude-opus-5, prompt epoch g1-v0-2026-09-02; "
            f"derivation: scripts/rescore_g1.py -> {a.file} (path in JSON given)")
    cmds = []
    P = f"g1_v1_{a.split}"

    def reg(name, value, path_note):
        if value is None:
            return
        cmds.append(_cmd(f"{P}_{name}", value, f"{base}: {path_note}", a.data_name))

    def cell(prefix, c, path):
        reg(f"{prefix}_n", c["n"], f"{path}.n")
        reg(f"{prefix}_scored", c["n_scored"], f"{path}.n_scored")
        reg(f"{prefix}_unparseable", c["n_unparseable"], f"{path}.n_unparseable")
        reg(f"{prefix}_L3plus", c["preserved"], f"{path}.preserved")
        reg(f"{prefix}_preservation_rate", c["preservation_rate"], f"{path}.preservation_rate (L3+ share of scored)")
        if c["wilson95"][0] is not None:
            reg(f"{prefix}_wilson95_lower", c["wilson95"][0], f"{path}.wilson95[0] (z=1.959964)")
            reg(f"{prefix}_wilson95_upper", c["wilson95"][1], f"{path}.wilson95[1]")

    obs = r["g1"]["observed"]
    cell("all", obs["all"], "g1.observed.all")
    for lvl, n in obs["all"]["levels"].items():
        reg(f"all_level_{lvl}", n, f"g1.observed.all.levels.{lvl}")
    for fc, n in obs["all"]["failure_classes"].items():
        reg(f"all_failure_{fc}", n, f"g1.observed.all.failure_classes.{fc}")
    for st, n in obs["all"]["estimate_status"].items():
        reg(f"all_estimate_{st}", n, f"g1.observed.all.estimate_status.{st}")
    for mode, c in obs["by_mode"].items():
        cell(mode, c, f"g1.observed.by_mode.{mode}")
    for cls, modes in obs["by_class_and_mode"].items():
        for mode, c in modes.items():
            cell(f"{cls}_{mode}", c, f"g1.observed.by_class_and_mode.{cls}.{mode}")
    rv = r.get("review")
    if rv:
        reg("genuine_losses", rv["genuine_losses"], f"review.genuine_losses (reviewer {rv['reviewer']}; criterion on the file)")
        reg("parser_misses", rv["parser_misses"], "review.parser_misses")
        reg("review_queue", rv["queue"], "review.queue (records at L0/L1/L2 or unparseable)")
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
