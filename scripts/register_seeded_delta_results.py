#!/usr/bin/env python3
"""Register the seeded delta's existence-versus-discoverability counts as Results.
**Zero spend, no network beyond Neo4j and Seldon.**

`cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards.md`
decision 2: "If the delta's headline is not yet a registered Result, register it (`seldon result
register`) with `scripts/seeded_delta.py` as its generator before the claim cites it." It was
not: no Result in the graph carried any of these numbers on 2026-10-11. The claims
`build_evidence_map.py` writes for DN-013-R1 quote only numbers that are a Finding or a
registered Result, and these are neither until this runs.

Every value is READ from `state/seeded_delta_2026-10-11.json`, which `scripts/seeded_delta.py`
writes from `RULE-A13-v1`'s own `_exists` and `per_object` over the stored Observations of
`scan_2026-10-07_seeded` (the part of `scan_2026-10-07_composite_d` its A13 Findings come from).
The script refuses unless `seeded_delta.py --check` reports the file CURRENT, so a Result can
never be bound to a stale table. A name already bound at the same value is reported and
skipped (AD-028: a Result name is bound once); one bound at another value is a failure.

    /opt/anaconda3/bin/python3 scripts/register_seeded_delta_results.py --dry-run
    /opt/anaconda3/bin/python3 scripts/register_seeded_delta_results.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from seldon_artifacts import live_artifact                          # noqa: E402

TASK = ("cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_"
        "standards.md")
DELTA = REPO / "state" / "seeded_delta_2026-10-11.json"
#: The cycle whose stored Observations the delta reads; every name carries it (DD-056).
CYCLE_SUFFIX = "2026-10-07_seeded"
OBJECTS = ("api", "terms", "changelog", "inventory")

ARTIFACTS = [
    ("Script", "seeded_delta", "scripts/seeded_delta.py",
     "Splits RULE-A13-v1's per-surface Findings of scan_2026-10-07_seeded per body and object: "
     "existence (_exists) against discoverability (per_object), over the stored Observations, "
     "judging nothing new. cc_tasks/2026-10-07_seed_known_locations_verify.md decision 6."),
    ("DataFile", "seeded_delta_2026-10-11", "state/seeded_delta_2026-10-11.json",
     "The seeded delta table scripts/seeded_delta.py writes: per body and object, existence and "
     "discoverability, with the headline counts. "
     "cc_tasks/2026-10-07_seed_known_locations_verify.md decision 6."),
]

#: What every description says once, so a reader of any one Result knows what it is.
_WHAT = ("Existence and discoverability are RULE-A13-v1's own _exists and per_object over each "
         "surface's stored Observations of scan_2026-10-07_seeded (the A13 part of the cycle of "
         "record scan_2026-10-07_composite_d); a body x object pair is 'unreachable' when the "
         "object exists and A13 is fail for that object on every product surface of the body. "
         "A13 is a candidate (DD-054): in no level and no score. DN-013-R1.")


def results(d: dict) -> list:
    """`[(name, value, units, sentence)]`, every value read from the delta."""
    h = d["headline"]
    out = [
        (f"seeded_delta_pairs_exist_unreachable_{CYCLE_SUFFIX}",
         h["pairs_exist_unreachable_from_every_product_page"], "body-object pairs",
         "Body x object pairs where the object exists and no product page of the body reaches "
         "it."),
        (f"seeded_delta_bodies_with_unreachable_pair_{CYCLE_SUFFIX}",
         h["bodies_with_such_a_pair"], "bodies",
         "Bodies holding at least one body x object pair where the object exists and no "
         "product page reaches it."),
        (f"seeded_delta_pairs_exist_{CYCLE_SUFFIX}", h["pairs_exist"], "body-object pairs",
         "Body x object pairs where the object exists."),
        (f"seeded_delta_surface_pairs_exist_unreachable_{CYCLE_SUFFIX}",
         h["surface_object_pairs_exist_and_fail"], "surface-object pairs",
         "Surface x object pairs where the object exists and A13 is fail for it on that "
         "product page."),
        (f"seeded_delta_surface_pairs_exist_{CYCLE_SUFFIX}", h["surface_object_pairs_exist"],
         "surface-object pairs", "Surface x object pairs where the object exists."),
    ]
    for o in OBJECTS:
        rows = [r for r in d["rows"] if r["object"] == o]
        if not rows:
            raise SystemExit(f"FATAL: the delta has no rows for object {o!r}")
        out.append((f"seeded_delta_{o}_pairs_exist_{CYCLE_SUFFIX}",
                    sum(1 for r in rows if r["exists"] == "yes"), "bodies",
                    f"Bodies whose {o} exists."))
        out.append((f"seeded_delta_{o}_pairs_exist_unreachable_{CYCLE_SUFFIX}",
                    sum(1 for r in rows if r["exists_unreachable_from_every_page"]), "bodies",
                    f"Bodies whose {o} exists and no product page of the body reaches it."))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    chk = subprocess.run([sys.executable, str(REPO / "scripts" / "seeded_delta.py"), "--check"],
                         capture_output=True, text=True, cwd=REPO)
    if chk.returncode:
        raise SystemExit(f"REFUSING: seeded_delta.py --check says {chk.stdout.strip()!r}; "
                         f"no Result is bound to a stale table")
    raw = DELTA.read_bytes()
    d = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()
    rows = results(d)
    if a.dry_run:
        for name, v, units, s in rows:
            print(f"{name}\t{v}\t{units}\t{s}")
        return 0
    for kind, art_name, path, desc in ARTIFACTS:
        if live_artifact(art_name):
            continue
        r = subprocess.run(["seldon", "artifact", "create", kind, "-p", f"name={art_name}",
                            "-p", f"path={path}", "-p", f"description={desc}", "--actor", "cc"],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create {kind} {art_name}: "
                             f"{r.stderr.strip()[-400:]}")
    script_id, data_id = live_artifact("seeded_delta"), live_artifact("seeded_delta_2026-10-11")
    failed = 0
    for name, v, units, sentence in rows:
        desc = f"{sentence} {_WHAT} Registered by {TASK}."
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", name,
                            "--units", units, "--description", desc, "--script-id", script_id,
                            "--data-ids", data_id, "--input-hash", sha],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            print(f"registered {name} = {v}")
        elif "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
            print(f"{name} already bound at {v}")
        else:
            failed += 1
            print(f"FAILED {name}: {r.stderr.strip()[-400:]}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
