#!/usr/bin/env python3
"""Record on `ind:G1-D` which instrument it was withdrawn FROM. **Zero spend, no network.**

`cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md` decision 4, under DD-066.

**Why the record and not the builder.** Decision 4 says the published appendix row gains
`measurement_tier: product` and `withdrawn_from: host-level` *read from the framework record's
indicator node, never typed*. `scripts/tag_g1d_product_tier.py` put the first of those two on
the node; the second was on no node at all — it lived in `params.tier0.legs_withdrawn` (the
instrument's own parameter) and in the report's generated prose, and nowhere the appendix
builder reads. A builder that types the string itself is the defect the decision names, so the
fact goes where the appendix already looks: on the indicator.

**The withdrawal is read, not asserted.** This refuses to write unless
`params.tier0.legs_withdrawn` actually carries G1-D, and it carries the parameter's own
`from_surfaces`, `effective` and `decision` onto the event's `changes` so the write can be
audited against the instrument that justified it. The one string this file supplies is
`host-level`, which is this project's name for those surface kinds — the same equivalence
`scripts/withdrawn_legs.py::_HOST_DEFAULT` documents and the report's sentence states in words.

Written through `framework_writeback.save`, the single writer (`tests/test_framework_single_
writer.py` asserts it statically). **A projection must follow** (DD-057):

    /opt/anaconda3/bin/python3 scripts/tag_g1d_withdrawn_from.py [--dry-run]
    /opt/anaconda3/bin/python3 scripts/load_framework_graph.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

TASK = "cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md"
SCRIPT = "tag_g1d_withdrawn_from"
NODE_ID = "ind:G1-D"
LEG = "G1-D"

#: What this project calls the surface kinds a host-level check is asked of. The same pair
#: `scripts/withdrawn_legs.py` reads out of `from_surfaces` and the same instrument the report's
#: withdrawal sentence names. Asserted against the parameter below rather than assumed: a
#: withdrawal from some other surface set is a different fact and would need a different word.
HOST_LEVEL = "host-level"
HOST_SURFACES = ("home", "well_known")


def withdrawal(leg: str = LEG) -> dict:
    """The instrument's own record of the withdrawal, or a hard stop. Read from
    `params.tier0.legs_withdrawn`, which is what `run.targets` and `build_l0_matrices` read."""
    from scan import load_params
    entries = (load_params().get("tier0", {}).get("legs_withdrawn") or [])
    entry = next((w for w in entries if w.get("leg") == leg), None)
    if entry is None:
        raise SystemExit(f"FATAL: params.tier0.legs_withdrawn names no {leg}; the instrument "
                         f"does not say this leg was withdrawn and the record may not either")
    surfaces = tuple(entry.get("from_surfaces") or ())
    if surfaces != HOST_SURFACES:
        raise SystemExit(f"FATAL: {leg} is withdrawn from {list(surfaces)}, not "
                         f"{list(HOST_SURFACES)}; {HOST_LEVEL!r} is this project's name for "
                         f"the latter and would be the wrong word for the former")
    return entry


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    entry = withdrawal()

    import framework_writeback as fw
    g = fw.load()
    node = next((n for n in g["nodes"] if n["id"] == NODE_ID), None)
    if node is None:
        raise SystemExit(f"FATAL: no {NODE_ID} in the framework record")
    if not node["properties"].get("measurement_tier"):
        raise SystemExit(f"FATAL: {NODE_ID} carries no measurement_tier; a leg recorded as "
                         f"withdrawn from one tier with no record of where it IS measured is "
                         f"the state `scripts/tag_g1d_product_tier.py` exists to prevent")

    keys = ("withdrawn_from", "withdrawn_from_source")
    before = {k: node["properties"].get(k) for k in keys}
    node["properties"]["withdrawn_from"] = HOST_LEVEL
    node["properties"]["withdrawn_from_source"] = (
        f"{entry['decision']} ({TASK}), effective {entry['effective']}. "
        f"`params.tier0.legs_withdrawn` withdraws {LEG} from surfaces "
        f"{list(entry.get('from_surfaces') or [])}, which is what this instrument calls "
        f"{HOST_LEVEL} (`scripts/withdrawn_legs.py`). Why: {' '.join(str(entry['why']).split())}")

    changes = {"node": NODE_ID, "before": before,
               "after": {k: node["properties"][k] for k in keys},
               "read_from": {"params.tier0.legs_withdrawn": entry}}
    out = fw.save(g, script=SCRIPT, task=TASK, changes=changes, dry_run=a.dry_run)
    print(json.dumps({"changes": changes,
                      "save": {k: v for k, v in out.items() if k != "delta"}},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
