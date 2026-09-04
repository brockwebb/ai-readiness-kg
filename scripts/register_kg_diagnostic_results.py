#!/usr/bin/env python3
"""Register the KG structural diagnostic's figures as Seldon Results (task
2026-09-04_kg_diagnostic_and_cq_harness §0.1). **Zero model spend.**

One Result per scalar figure, named `kg_diag_<metric>`, `computed_from` the graph snapshot
DataFile and `generated_by` the Script `kg_diagnostic`. The rule this enforces, recorded in
the DD this task appends: **any graph figure quoted in a handoff, memo or decision must
resolve to one of these names.** A number that cannot is a memory of a chat.

Collection-valued keys (the label census, the largest duplicate groups, the edge triples)
stay in the snapshot JSON and are not registered as Results — a Result carries one number.
The label census is the exception: each label's count is a figure people quote, so those are
registered individually as `kg_diag_label_<Label>`.

    /opt/anaconda3/bin/python3 scripts/register_kg_diagnostic_results.py \
        --snapshot state/kg_snapshot_2026-09-04.json --data-name kg_snapshot_2026-09-04 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md"

#: Keys that are context rather than a figure, or whose value is a collection.
SKIP = {"generated_at", "database", "kg_labels", "label_counts", "concept_dup_largest_groups",
        "domain_edge_triples", "domain_edges_by_type", "claims_without_asserts_sample"}


def rows(snap: dict) -> list:
    out = []
    for key, value in snap.items():
        if key in SKIP or not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        out.append((f"kg_diag_{key}", value, f"{key} from the structural diagnostic"))
    for label, count in (snap.get("label_counts") or {}).items():
        out.append((f"kg_diag_label_{label}", count, f"nodes carrying the {label} label"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", default="state/kg_snapshot_2026-09-04.json")
    ap.add_argument("--data-name", default="kg_snapshot_2026-09-04")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    snap = json.loads(Path(a.snapshot).read_text(encoding="utf-8"))
    base = (f"KG structural diagnostic of database '{snap.get('database')}' at "
            f"{snap.get('generated_at')}, re-deriving in code the figures a Desktop session "
            f"had run in chat ({TASK} §0). Derivation: scripts/kg_diagnostic.py -> {a.snapshot}")
    data = rows(snap)
    if a.dry_run:
        for name, value, note in data:
            print(f"{name}\t{value}\t{note}")
        print(len(data), "Results")
        return 0
    ok = 0
    data = data[a.skip:]
    for name, value, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{base}: {note}",
                            "--script-name", "kg_diagnostic", "--data-name", a.data_name],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} diagnostic Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
