#!/usr/bin/env python3
"""Write the executive-summary grid's plain names into the framework of record. **Zero spend.**

`cc_tasks/2026-10-14_executive_summary_v3_grid.md` Part A, under DN-014 ADDENDUM 01 §3. The
record carries no plain-language name for any check or tier, which is why a table built from it
reads as code. This adds, through the ONE writer (`framework_writeback.save`, never a hand edit):

* `measurement_tiers` (a top-level record key): the `display_name` of each `tier` value —
  public tier, agency-enabled tier, paid-tool tier (DN-014 §5);
* `plain_name` on every public-tier rule the grid shows (at most six words, what a machine met);
* `fix_line` on every Action a grid rule's failing outcomes map to (one imperative sentence);
* `declared: true` on every rule that records what an agency declares (excluded from the grid).

The strings are AUTHORED in `framework/summary_grid_vocab.yaml`; this script only applies them.
It adds and never removes, so `save` writes without `--force`; the delta is on the
`framework_writeback` event. A projection MUST follow (`scripts/load_framework_graph.py`), or a
Cypher answer over the framework labels is stale (DD-057).

    /opt/anaconda3/bin/python3 scripts/apply_grid_plain_names.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import framework_writeback as fw  # noqa: E402

SCRIPT = "scripts/apply_grid_plain_names.py"
TASK = "cc_tasks/2026-10-14_executive_summary_v3_grid.md"
VOCAB = REPO / "framework" / "summary_grid_vocab.yaml"


def apply(g: dict, vocab: dict) -> dict:
    """Mutate `g` in place with the authored names; return a report of what was set and any
    name in the vocab that matched no node (a drift the caller must see, not swallow)."""
    tier_names = vocab["tier_display_names"]
    plain = vocab["plain_names"]
    fixes = vocab["fix_lines"]
    declared = set(vocab["declared_codes"])

    g["measurement_tiers"] = {t: {"display_name": name} for t, name in tier_names.items()}

    set_plain, set_declared, set_fix = [], [], []
    seen_codes, seen_actions = set(), set()
    for n in g["nodes"]:
        p = n["properties"]
        if "AssessmentIndicator" in n["labels"]:
            code = p.get("code")
            seen_codes.add(code)
            if code in plain:
                p["plain_name"] = plain[code]
                set_plain.append(code)
            if code in declared:
                p["declared"] = True
                set_declared.append(code)
        if "Action" in n["labels"]:
            seen_actions.add(n["id"])
            if n["id"] in fixes:
                p["fix_line"] = fixes[n["id"]]
                set_fix.append(n["id"])

    return {
        "tiers": list(tier_names),
        "plain_name_set": sorted(set_plain),
        "declared_set": sorted(set_declared),
        "fix_line_set_count": len(set_fix),
        # names in the vocab that reached no node — a fatal drift, listed for the caller
        "plain_names_unmatched": sorted(set(plain) - seen_codes),
        "declared_unmatched": sorted(declared - seen_codes),
        "fix_lines_unmatched": sorted(set(fixes) - seen_actions),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vocab", default=str(VOCAB))
    fw.add_force_args(ap)
    a = ap.parse_args(argv)

    vocab = yaml.safe_load(Path(a.vocab).read_text(encoding="utf-8"))
    g = fw.load()
    if g is None:
        raise SystemExit("FATAL: framework record not found")
    report = apply(g, vocab)
    unmatched = (report["plain_names_unmatched"] + report["declared_unmatched"]
                 + report["fix_lines_unmatched"])
    if unmatched:
        raise SystemExit(f"FATAL: vocab entries matched no node: {unmatched}; nothing written")

    ev = fw.save(g, script=SCRIPT, task=TASK,
                 changes={"applied": "grid plain_name/fix_line/declared/measurement_tiers",
                          "plain_names": report["plain_name_set"],
                          "declared": report["declared_set"],
                          "fix_lines": report["fix_line_set_count"]},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    import json
    print(json.dumps({**report, "written": ev["written"],
                      "unchanged": ev.get("unchanged", False),
                      "event_id": ev.get("event_id"),
                      "framework_sha256": ev["framework_sha256"],
                      "delta": ev["delta_summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
