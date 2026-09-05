#!/usr/bin/env python3
"""Register the extraction-gap classification's figures as Seldon Results. **Zero model spend.**

The first run (`state/extraction_gap_2026-09-04.json`, task
`2026-09-04_extraction_gap_diagnostic`) registered its 16 `kg_diag_gap_*` Results from an
ad-hoc command in the session that produced them, with no script to re-run. That is exactly
the defect DD-040 records about numbers computed in chat: the figures were right and nothing
could reproduce them. This script is the path, and the rerun in
`2026-09-04_extract_g1eval_17_and_rerun` §1.4 is its first user.

`--suffix` follows the DD-041 rerun convention — a rerun never overwrites a registered
measurement, so the post-extraction figures carry `_2026-09-04b` and the un-suffixed names
stay bound to the pre-extraction run.

    /opt/anaconda3/bin/python3 scripts/register_gap_results.py \
        --gap state/extraction_gap_2026-09-04b.json --data-name extraction_gap_2026-09-04b \
        --suffix _2026-09-04b [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-04_extract_g1eval_17_and_rerun.md"

#: Top-level keys that are context rather than a figure.
SKIP = {"generated_at", "database", "rows", "counts", "estimate", "cq_overlap",
        "manifest_documents_without_a_document_node_ids",
        "manifest_documents_without_a_document_node_epochs"}


def rows(gap: dict, suffix: str = "") -> list:
    out = []
    for key, value in gap.items():
        if key in SKIP or not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        out.append((f"kg_diag_gap_{key}{suffix}", value, f"{key} from the extraction-gap classification"))
    for cls, n in (gap.get("counts") or {}).items():
        out.append((f"kg_diag_gap_{cls}{suffix}", n, f"gap documents classified {cls}"))
    est = (gap.get("estimate") or {}).get("to_run") or {}
    for key in ("documents", "chunks", "tokens_at_chunk_floor"):
        if key in est:
            out.append((f"kg_diag_gap_estimate_{key}{suffix}", est[key],
                        f"{key} in the set extraction would close, priced at the call-class "
                        f"floor (an upper bound on the count, NOT a price — see DD-042)"))
    ov = gap.get("cq_overlap") or {}
    for key in ("cqs_examined", "cqs_term_testable",
                "cqs_with_at_least_one_unextracted_document_mentioning_their_terms",
                "documents_with_readable_text"):
        if key in ov:
            out.append((f"kg_diag_gap_{key}{suffix}", ov[key], f"{key} from the CQ-overlap pass"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gap", default="state/extraction_gap_2026-09-04b.json")
    ap.add_argument("--data-name", default="extraction_gap_2026-09-04b")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    gap = json.loads(Path(a.gap).read_text(encoding="utf-8"))
    base = (f"Per-document classification of the corpus documents contributing no edges to the "
            f"graph, at {gap.get('generated_at')}. Derivation: "
            f"scripts/extraction_gap_diagnostic.py -> {a.gap} ({TASK})")
    data = rows(gap, a.suffix)
    if a.dry_run:
        for name, value, note in data:
            print(f"{name}\t{value}\t{note[:80]}")
        print(len(data), "Results")
        return 0
    ok = 0
    for name, value, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{base}: {note}",
                            "--script-name", "extraction_gap_diagnostic",
                            "--data-name", a.data_name],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} gap Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
