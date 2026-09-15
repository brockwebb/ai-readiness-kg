#!/usr/bin/env python3
"""Tag G1-D `measurement_tier: product` on the framework record. **Zero spend, no network.**

`cc_tasks/2026-09-15_g1d_leaves_l0.md` decision 3, under DN-005 §2.2 (capability tiering) and
DD-066.

**The first `measurement_tier` value in the record.** DN-005 §4 item 2 is the task that tiers
every indicator; this writes the one the withdrawal forces, because a leg removed from the
host-level instrument with nothing on the record saying where it IS measured is a leg that
looks dropped rather than relocated.

Three properties are written on `ind:G1-D` and nothing else moves:

* `measurement_tier: product` — the surface kind the construct can be measured on at all.
* `measurement_tier_source` — why, with the evidence: the verdict census this task's §0 ran.
* `construct_restated` — the operator's own restatement of 2026-09-15, which is the definition
  DD-066 adopts: *uncertainty present for the human reader and absent from the markup.*

Written through `framework_writeback.save`, the single writer (`tests/test_framework_single_
writer.py` asserts it statically). A projection must follow (DD-057).

    /opt/anaconda3/bin/python3 scripts/tag_g1d_product_tier.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

TASK = "cc_tasks/2026-09-15_g1d_leaves_l0.md"
SCRIPT = "tag_g1d_product_tier"
NODE_ID = "ind:G1-D"

#: The operator's restatement of 2026-09-15, adopted by DD-066 as the construct's definition.
CONSTRUCT = "uncertainty present for the human reader and absent from the markup"

#: Named in DD-066 as the standards a product-tier rule would bind to, and named as NOT YET
#: EVALUATED against any federal data product by this project. Recorded on the node so the
#: tiering task (DN-005 §4 item 2) inherits the reading list rather than redoing the search.
PRIOR_ART = ("SDMX observation-status and confidence attributes; "
             "W3C Data Quality Vocabulary (DQV); "
             "schema.org Dataset variable metadata. "
             "None has yet been evaluated against a federal data product by this project.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    import framework_writeback as fw
    g = fw.load()
    node = next((n for n in g["nodes"] if n["id"] == NODE_ID), None)
    if node is None:
        raise SystemExit(f"FATAL: no {NODE_ID} in the framework record")

    before = {k: node["properties"].get(k) for k in
              ("measurement_tier", "measurement_tier_source", "construct_restated")}
    node["properties"]["measurement_tier"] = "product"
    node["properties"]["measurement_tier_source"] = (
        f"DD-066 ({TASK}). The host-level leg was withdrawn after the census in that task's "
        f"RESULT §0: on host-level surfaces (`home`, `well_known`) across every body, every "
        f"reference host and every cycle the rule returned 126 `fail`, 28 `error` and 0 "
        f"`pass`; on product surfaces the same rule returned 104 `pass`. The construct is "
        f"carryable and the home page is not where it is carried. Standards a product-tier "
        f"rule would bind to: {PRIOR_ART}")
    node["properties"]["construct_restated"] = CONSTRUCT

    changes = {"node": NODE_ID, "before": before,
               "after": {k: node["properties"][k] for k in before}}
    out = fw.save(g, script=SCRIPT, task=TASK, changes=changes, dry_run=a.dry_run)
    print(json.dumps({"changes": changes, "save": {k: v for k, v in out.items()
                                                   if k not in ("delta",)}},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
