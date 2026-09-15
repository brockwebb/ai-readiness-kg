#!/usr/bin/env python3
"""Withdraw the published host-level G1-D Results. **Zero spend, no network. Nothing deleted.**

`cc_tasks/2026-09-15_g1d_leaves_l0_ADDENDUM_01.md`: "The published Results that quote G1-D at
host level ... move to `withdrawn` with the reason 'host-level G1-D leg withdrawn, DD-066; the
surface cannot carry the property', **not deleted**."

**There is no `withdrawn` state on the Result state machine,** and this is where that shows.
`seldon/domain/research.yaml` gives Result `proposed -> [verified, rejected]`,
`verified -> [published, stale]`, `published -> [stale]`, `stale -> [verified]`. The reachable
terminal from `published` is `stale`, and `stale` is the state machine's own word for exactly
what the addendum describes: the value stands as measured and is no longer the current
instrument's answer. It is also reversible (`stale -> verified`), which a withdrawal of a
measurement that was correctly taken ought to be. Adding a `withdrawn` state to a state machine
four projects share, for one leg in one project, would be the heavier and worse change.

So: **state `stale`, and the withdrawal reason on the artifact** as `withdrawn_reason` /
`withdrawn_by`, where a reader of the Result finds it. The value is untouched, the name is
untouched, the provenance edges are untouched.

    /opt/anaconda3/bin/python3 scripts/withdraw_g1d_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TASK = "cc_tasks/2026-09-15_g1d_leaves_l0.md"
REASON = ("host-level G1-D leg withdrawn, DD-066; the surface cannot carry the property")
#: The two disagreement counts are withdrawn for a consequence of that withdrawal rather than
#: for the withdrawal itself, and the record should say which.
REASON_BY_NAME = {
    "scan_l0_home_flagship_disagreement_cells_2026-09-10_rj2":
        "computed over the five surface-judged tier-0 legs that included G1-D; DD-066 "
        "withdrew that leg, so the comparison is now over four and is registered under "
        "`scan_l0_home_flagship_disagreement_cells_over_four_legs_2026-09-10_rj2`. The value "
        "stands as the five-leg count (AD-028: a name binds once).",
    "scan_l0_home_flagship_disagreement_bodies_2026-09-10_rj2":
        "computed over the five surface-judged tier-0 legs that included G1-D; DD-066 "
        "withdrew that leg, so the comparison is now over four and is registered under "
        "`scan_l0_home_flagship_disagreement_bodies_over_four_legs_2026-09-10_rj2`. The value "
        "stands as the five-leg count (AD-028: a name binds once).",
}

#: The Results to move, named rather than pattern-matched. Three, and they are the three the
#: published report tagged: the host-level G1-D pass count, its denominator and the Wilson
#: upper bound quoted beside them. NAMED because a pattern over `g1_d` would sweep 130 further
#: Results — every prior cycle's counts, every re-judgement's, the Tier C family, the product
#: family — none of which this task withdraws and all of which stay exactly as measured.
NAMES = ("scan_l0_g1_d_pass_2026-09-10_rj2",
         "scan_l0_g1_d_applicable_n_2026-09-10_rj2",
         "scan_l0_host_leg_rate_g1_d_upper95_2026-09-10_rj2",
         # Two the addendum did not anticipate, and they are the same withdrawal one step
         # removed. `surface_disagreements` counts cells where a body's home and flagship
         # surfaces answer the same host-level check differently, over the surface-judged
         # tier-0 legs — FIVE of them while G1-D was one, FOUR now. The published pair is bound
         # at 17 cells across 8 bodies (AD-028: a name binds once), which is the true count
         # over the five-leg comparison and cannot be re-bound at the four-leg one. So they are
         # withdrawn with the rest and the new comparison is registered under a name that says
         # which legs it compared — the same remedy DD-056 and `leg_results(family=...)` use
         # for a name that did not carry the dimension it varied on.
         "scan_l0_home_flagship_disagreement_cells_2026-09-10_rj2",
         "scan_l0_home_flagship_disagreement_bodies_2026-09-10_rj2")

TARGET_STATE = "stale"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    from seldon.config import get_current_session, get_neo4j_driver, load_project_config
    from seldon.core.artifacts import transition_state, update_artifact
    from seldon.domain.loader import load_domain_config

    cfg = load_project_config(REPO)
    db = cfg["neo4j"]["database"]
    driver = get_neo4j_driver(cfg)
    domain = load_domain_config(Path("/Users/brock/GitHub/seldon/seldon/domain/research.yaml"))
    session_id = get_current_session(REPO)
    moved = []
    try:
        with driver.session(database=db) as s:
            rows = {r["name"]: dict(r) for r in s.run(
                "MATCH (r:Result) WHERE r.name IN $n "
                "RETURN r.name AS name, r.artifact_id AS id, r.state AS state, "
                "       r.value AS value", n=list(NAMES))}
        missing = [n for n in NAMES if n not in rows]
        if missing:
            raise SystemExit(f"FATAL: no Result named {missing}; nothing was moved")
        for name in NAMES:
            r = rows[name]
            rec = {"name": name, "id": r["id"], "value": r["value"],
                   "before": r["state"], "after": r["state"]}
            if r["state"] == TARGET_STATE:
                rec["note"] = "already withdrawn"
            elif not a.dry_run:
                transition_state(project_dir=REPO, driver=driver, database=db,
                                 domain_config=domain, artifact_id=r["id"],
                                 artifact_type="Result", current_state=r["state"],
                                 new_state=TARGET_STATE, actor="cc", authority="accepted",
                                 session_id=session_id)
                update_artifact(project_dir=REPO, driver=driver, database=db,
                                artifact_id=r["id"],
                                properties={"withdrawn_reason": REASON_BY_NAME.get(name,
                                                                                    REASON),
                                            "withdrawn_by": TASK},
                                actor="cc", authority="accepted", session_id=session_id)
                rec["after"] = TARGET_STATE
            else:
                rec["after"] = f"{TARGET_STATE} (dry run)"
            moved.append(rec)
    finally:
        driver.close()
    print(json.dumps({"task": TASK, "reason": REASON, "target_state": TARGET_STATE,
                      "results": moved}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
