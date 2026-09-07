#!/usr/bin/env python3
"""Make the framework of record consistent with itself. **Zero model spend, idempotent.**

Task `cc_tasks/2026-09-07_scan_hygiene.md` §3. Two writers minted `EVIDENCED_BY_INTERNAL`
edges in two shapes: `build_framework_graph.py` wrote `{to: "internal:<ref>", properties:
{artifact_path: <ref>}}` for seventeen of them, and `add_candidate_indicator.py` wrote
`{to: "<ref>", properties: {ref: <ref>}}` for A12's three. `load_framework_graph.py` was taught
to read both (`:111`), which kept the projection right and left the record ambiguous — and an
ambiguity a loader papers over is one the next writer copies. This normalises the three onto
the seventeen's shape and fixes the writer, so the next candidate is minted correctly rather
than needing a third repair.

**`counts` is NOT drifting and this does not "fix" it.** The task file's premise was that
`counts` reads `constructs: 47, indicators: 48` against 48 and 49 nodes in the file. It does,
and both are right: those keys are candidate-excluded under DD-054 and A12 is a candidate.
`scripts/framework_writeback.py::recount` reproduces every stored value exactly — run
`--check` and read `counts_drift: {}`. What this task actually installs is the guard: one
definition of every denominator, regenerated on every write-back from now on, and a gate that
reads it.

    /opt/anaconda3/bin/python3 scripts/framework_writeback_normalize.py --check
    /opt/anaconda3/bin/python3 scripts/framework_writeback_normalize.py --dry-run
    /opt/anaconda3/bin/python3 scripts/framework_writeback_normalize.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw                                    # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_hygiene.md"
SCRIPT = "scripts/framework_writeback_normalize.py"
#: The shape seventeen of the twenty already use, and therefore the shape. `to` is the node id
#: the loader MERGEs on, so the prefix is not decoration: without it an internal reference and
#: a corpus `doc:` reference could collide on a bare path.
KEY = "artifact_path"
PREFIX = "internal:"


def normalize(g: dict) -> dict:
    """Rewrite every `EVIDENCED_BY_INTERNAL` edge onto the `artifact_path` + `internal:` shape.

    The reference text itself is never rewritten — only the key it sits under and the prefix on
    the node id. A12's three cite a RESULT section, a DD section and a state file, and those
    strings are the evidence.
    """
    touched = {"key_renamed": 0, "prefix_added": 0}
    for e in g["edges"]:
        if e["type"] != "EVIDENCED_BY_INTERNAL":
            continue
        props = e.setdefault("properties", {})
        if KEY not in props:
            ref = props.pop("ref", None) or str(e["to"]).removeprefix(PREFIX)
            props[KEY] = ref
            touched["key_renamed"] += 1
        # Any other key would be a third shape; refuse rather than silently drop it.
        extra = set(props) - {KEY}
        if extra:
            raise SystemExit(f"REFUSING: EVIDENCED_BY_INTERNAL edge to {e['to']!r} carries "
                             f"unexpected properties {sorted(extra)}")
        if not str(e["to"]).startswith(PREFIX):
            e["to"] = PREFIX + str(e["to"])
            touched["prefix_added"] += 1
    return touched


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="report self-consistency and write nothing")
    a = ap.parse_args(argv)
    g = json.loads(fw.FRAMEWORK.read_text(encoding="utf-8"))
    if a.check:
        from assessment.harness.scan.rules import BY_LEG
        print(json.dumps(fw.check(g, set(BY_LEG.values())), indent=1))
        return 0
    touched = normalize(g)
    out = fw.save(g, script=SCRIPT, task=TASK, changes=touched, dry_run=a.dry_run)
    print(json.dumps({k: v for k, v in out.items() if k != "counts"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
