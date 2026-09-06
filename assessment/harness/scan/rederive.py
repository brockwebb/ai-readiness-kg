#!/usr/bin/env python3
"""Re-derivation gate: delete every Finding, re-judge from stored Observations, demand
byte-identical output. **Zero model calls, no network.**

Task §3. Skeleton §6b.5 claims that "thresholds can change and history can be re-scored
without re-measurement". This is the test of that claim, and it is a real test only because a
Finding's id is DERIVED — `sha256(rule_id | rule_version | sorted obs_ids | params_hash)` —
rather than assigned by a counter or a clock. An id from either would make the comparison
vacuous: it would differ every run whether or not the judgement did.

    /opt/anaconda3/bin/python3 assessment/harness/scan/rederive.py --from state/scan_smoke_2026-09-06.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))

from scan import load_params                                   # noqa: E402
from scan.model import Observation, params_hash                # noqa: E402
from scan.rules import BY_LEG, judge as judge_rule             # noqa: E402


def rehydrate(rows: list) -> list:
    return [Observation(**r) for r in rows]


def rederive(payload: dict, params: dict) -> dict:
    """Re-judge every leg from stored Observations alone and diff against the recorded
    Findings. Nothing is fetched; if this needed the network the split would be a fiction.

    The gate asks whether the RULES are deterministic, so it must hold the parameters fixed.
    Re-deriving under a different `params_hash` legitimately produces different Findings —
    that is §6b.5's whole point, that thresholds may change and history be re-scored — and
    comparing across the change would test the wrong thing and fail for the right reason,
    confusingly. So a params mismatch is reported as itself, not as a broken gate.
    """
    recorded_hash = payload.get("params_hash")
    current_hash = params_hash(params)
    if recorded_hash and recorded_hash != current_hash:
        return {"identical": False, "params_changed": True,
                "recorded_params_hash": recorded_hash, "current_params_hash": current_hash,
                "note": ("params.yaml has changed since this cycle ran, so its Findings carry "
                         "different ids by construction. Re-run the cycle; do not compare "
                         "across a parameter change.")}
    obs = rehydrate(payload["observations_detail"])
    # Control Findings are re-derived too. They are the ones whose determinism matters most —
    # they are what licenses the cycle — and the first version of this gate compared only the
    # surface Findings, so retaining the fixture Observations made it report the control
    # Findings as `unexpected_after_rederive` rather than checking them.
    recorded = {f["finding_id"]: f for f in
                payload["findings_detail"] + payload.get("control_findings_detail", [])}
    # Grouped by (surface, leg) — except E5, which judges the CYCLE. Its two control
    # Observations are one group, not one per fixture; grouping them per fixture re-derived
    # two E5 Findings where the cycle recorded one, which is how this was found.
    by_key: dict = {}
    for o in obs:
        by_key.setdefault(("*cycle*" if o.leg == "E5" else o.target_doc_id, o.leg), []).append(o)

    rederived, mismatches = {}, []
    for (doc_id, leg), group in sorted(by_key.items()):
        rule_id = BY_LEG.get(leg)
        if rule_id is None:
            continue
        f = judge_rule(rule_id, group, params)
        rederived[f.finding_id] = f.to_dict()

    missing = sorted(set(recorded) - set(rederived))
    extra = sorted(set(rederived) - set(recorded))
    for fid in sorted(set(recorded) & set(rederived)):
        if recorded[fid] != rederived[fid]:
            mismatches.append(fid)
    return {"recorded": len(recorded), "rederived": len(rederived),
            "missing_after_rederive": missing, "unexpected_after_rederive": extra,
            "field_mismatches": mismatches,
            "identical": not (missing or extra or mismatches)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default=str(REPO / "state" / "scan_smoke_2026-09-06.json"))
    a = ap.parse_args(argv)
    payload = json.loads(Path(a.src).read_text(encoding="utf-8"))
    res = rederive(payload, load_params())
    print(json.dumps(res, indent=1))
    print("RE-DERIVATION GATE:", "PASS" if res["identical"] else "FAIL")
    return 0 if res["identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
