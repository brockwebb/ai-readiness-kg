#!/usr/bin/env python3
"""Run the self-scan: `run.py`'s own cycle, with the cycle IDENTITY overlaid and nothing else.

`cc_tasks/2026-09-13_self_row.md` decision 1. **Zero model spend. Network: the published
authority only** — the frame names one host, the manners are the harness's own, and the socket
counter on the payload is what proves it.

**This does not re-implement a cycle.** It calls `scan.run.main()` — the same entry point every
other cycle ran through, with the same control gate first, the same collectors, the same rules,
the same staging of evidence and the same payload shape — and it changes exactly one thing:
`run.main` reads its parameters through the module attribute `load_params`, and this script
replaces that attribute with one that returns the committed parameters **plus a two-key cycle
overlay**. That is the repo's call-time-indirection convention (CLAUDE.md, "Conventions specific
to this repo") applied to the one seam that decides which cycle is running. A self-scan that
needed the harness bent is not a self-scan.

**Why the live cycle's declaration is NOT edited, which is the thing this script exists for.**
The obvious way to run a cycle here is to edit `params.cycle` in
`assessment/harness/scan/params.yaml`. That cannot be done for this cycle: `params.cycle.targets`
is read at RE-DERIVATION time by `scripts/register_l0_report_results.py::netlocs_declared`, which
counts the netlocs on whatever target file is currently declared — and the Result it registers,
`fss_scan_netlocs_2026-09`, is one of the 59 the L0 report tags and is `published`. Pointing
`params.cycle.targets` at a one-host frame would make that Result re-derive to 1 against a
registered 22, so `scripts/rederive_tagged_results.py` would BLOCK and the publication's own
gate would fail — for a reason that has nothing to do with the self-scan. Measured, not assumed:
`netlocs_declared(load_params())` is 22 today.

So the overlay is in memory, and its provenance is on the payload instead:

    params_hash         the hash of the OVERLAID parameters, which is what every Observation
                        and Finding of this cycle carries
    base_params_hash    the hash of `assessment/harness/scan/params.yaml` as committed
    params_overlay      the exact overlay, so `base + overlay` is reconstructible by anyone

`tests/test_self_row.py` reconstructs the parameters that way — the committed file recovered from
git by `base_params_hash`, the overlay applied, the result hashed and checked against
`params_hash` — and then re-derives every Finding. A payload nothing can re-derive is the defect
this repo has fought twice (the two `_rj1` payloads sat outside the standing set for a task), and
an in-memory overlay with no record of itself would have created exactly that.

    /opt/anaconda3/bin/python3 scripts/run_self_scan.py --cycle self_2026-09-13 \\
        --targets scan_targets_self_2026-09-13 [--dry-run]

Refuses: a targets file that does not exist; a cycle whose payload already exists (`run.py`'s own
`refuse_clobber` also guards this); an overlay that changes anything but `cycle`.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-13_self_row.md"


def overlaid(base: dict, cycle: str, targets: str) -> dict:
    """`base` with the cycle identity replaced. **Only `cycle` may differ.**

    Asserted rather than trusted: the whole argument for an in-memory overlay is that the self
    row is measured by the SAME instrument — the same manners, the same rules, the same
    thresholds — as every federal host in the report. An overlay that touched anything else
    would quietly make it a different instrument.
    """
    params = copy.deepcopy(base)
    params["cycle"] = {"name": cycle, "targets": targets}
    differing = sorted(k for k in set(base) | set(params) if base.get(k) != params.get(k))
    if differing != ["cycle"]:
        raise SystemExit(f"FATAL: the overlay changes {differing}; only 'cycle' may differ, or "
                         f"the self row is not measured by the same instrument as the report")
    return params


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycle", required=True)
    ap.add_argument("--targets", required=True, help="the frame, without .json")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the overlay and the targets it resolves, run nothing")
    a = ap.parse_args(argv)

    from scan import load_params, run as run_mod
    from scan.model import params_hash

    frame_path = REPO / "state" / f"{a.targets}.json"
    if not frame_path.is_file():
        raise SystemExit(f"FATAL: {frame_path.relative_to(REPO)} does not exist; build it with "
                         f"scripts/build_self_frame.py first")

    base = load_params()
    params = overlaid(base, a.cycle, a.targets)
    base_hash, cycle_hash = params_hash(base), params_hash(params)

    if a.dry_run:
        print(json.dumps({"cycle": a.cycle, "targets": a.targets,
                          "base_params_hash": base_hash, "params_hash": cycle_hash,
                          "targets_resolved": run_mod.targets(params)}, indent=1, default=str))
        return 0

    # The one seam. `run.main` calls `load_params()` once, through this module attribute; every
    # collector and rule then receives that dict explicitly, so replacing it here is enough and
    # nothing else in the harness has to know.
    real = run_mod.load_params
    run_mod.load_params = lambda *args, **kwargs: params
    try:
        rc = run_mod.main(["--task", TASK])
    finally:
        run_mod.load_params = real
    if rc:
        print(f"run.py exited {rc}; nothing further was written", file=sys.stderr)
        return rc

    # The overlay's provenance, onto the payload `run.py` just wrote. Added AFTER the run and
    # outside `params_hash`'s input, so no Finding is re-identified by it; what it does is make
    # the parameters this cycle was measured under reconstructible by a stranger.
    payload_path, _ = run_mod.out_paths(params)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload["params_hash"] != cycle_hash:
        raise SystemExit(f"FATAL: the payload carries params_hash {payload['params_hash'][:12]} "
                         f"and the overlay hashes to {cycle_hash[:12]}; the run did not use the "
                         f"parameters this script built")
    payload["base_params_hash"] = base_hash
    payload["base_params_path"] = "assessment/harness/scan/params.yaml"
    payload["params_overlay"] = {"cycle": params["cycle"]}
    payload["params_overlay_note"] = (
        "This cycle ran under the committed base parameters with its cycle IDENTITY overlaid in "
        "memory: base_params_hash is `assessment/harness/scan/params.yaml` as committed, and "
        "applying params_overlay to it reproduces params_hash exactly. The live cycle's "
        "declaration was deliberately not edited, because `params.cycle.targets` is read at "
        "re-derivation time by register_l0_report_results.netlocs_declared, whose Result "
        "fss_scan_netlocs_2026-09 is published and tagged by the report. "
        f"Task {TASK} decision 1; asserted by tests/test_self_row.py.")
    payload_path.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")

    print(json.dumps({"cycle": a.cycle, "payload": str(payload_path.relative_to(REPO)),
                      "params_hash": cycle_hash, "base_params_hash": base_hash,
                      "surfaces": payload["surfaces"], "findings": payload["findings"],
                      "observations": payload["observations"],
                      "verdict_counts": payload["verdict_counts"],
                      "requests_per_host": payload["requests_per_host"],
                      "control_verdict": payload["control_verdict"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
