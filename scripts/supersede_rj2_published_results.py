#!/usr/bin/env python3
"""Mark the `_rj2` Results the re-snapshot replaced as no longer the published answer. **Zero
spend, no network. Nothing deleted, no value touched.**

`cc_tasks/2026-09-19_resnapshot_rj4.md` decision 1: "the `_rj2` ones they succeed are marked
superseded". The report now quotes `scan_2026-09-10_rj4`'s Results by name; every `_rj2` Result
it quoted was moved to `published` by `scripts/publish_result_states.py` on 2026-09-12 and would
otherwise go on saying so after the document that published it stopped quoting it.

**There is no `superseded` state on the Result state machine,** and this is where that shows.
`seldon/domain/research.yaml` gives `published -> [stale]` and nothing else, and `stale` is the
machine's own word for "the value stands as measured and is no longer the current answer" —
the reading `scripts/withdraw_g1d_results.py` gave it for DD-066's withdrawal, with the reason
on the artifact. The same here: state `stale`, and `superseded_by` / `superseded_reason` /
`superseded_by_task` on the artifact, where a reader of the Result finds them. The one Result in
the graph whose state is literally `superseded` (`scan_evidence_store`) predates the state
machine and is not a precedent.

**Selected by construction.** A Result is moved exactly when it is `published`, its name
carries the `_2026-09-10_rj2` suffix, and the same metric under the `_rj4` suffix exists and is
itself `published` — so this runs AFTER `publish_result_states.py publish`, and a successor that
is not yet the published answer leaves its predecessor alone.

    /opt/anaconda3/bin/python3 scripts/supersede_rj2_published_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TASK = "cc_tasks/2026-09-19_resnapshot_rj4.md"
OLD, NEW = "_2026-09-10_rj2", "_2026-09-10_rj4"
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
    out, unmatched = [], []
    try:
        with driver.session(database=db) as s:
            old = s.run("MATCH (r:Result {state: 'published'}) WHERE r.name ENDS WITH $sfx "
                        "RETURN r.name AS name, r.artifact_id AS id, r.value AS value "
                        "ORDER BY name", sfx=OLD).data()
            names = [r["name"][: -len(OLD)] + NEW for r in old]
            new = {r["name"]: r for r in s.run(
                "MATCH (r:Result) WHERE r.name IN $n "
                "RETURN r.name AS name, r.state AS state, r.value AS value", n=names).data()}
        for r in old:
            succ = r["name"][: -len(OLD)] + NEW
            n = new.get(succ)
            if n is None or n["state"] != "published":
                unmatched.append({"name": r["name"], "successor": succ,
                                  "successor_state": n and n["state"]})
                continue
            rec = {"name": r["name"], "value": r["value"], "successor": succ,
                   "successor_value": n["value"], "moved_value": r["value"] != n["value"]}
            if not a.dry_run:
                transition_state(project_dir=REPO, driver=driver, database=db,
                                 domain_config=domain, artifact_id=r["id"],
                                 artifact_type="Result", current_state="published",
                                 new_state=TARGET_STATE, actor="cc", authority="accepted",
                                 session_id=session_id)
                update_artifact(
                    project_dir=REPO, driver=driver, database=db, artifact_id=r["id"],
                    properties={
                        "superseded_by": succ,
                        "superseded_reason": (
                            "the L0 report was re-snapshotted from scan_2026-09-10_rj2 onto "
                            "scan_2026-09-10_rj4 (DN-004: a published number would change); "
                            f"the report now quotes {succ}. The value stands as measured "
                            "under generation 9 (AD-028: a name binds once)."),
                        "superseded_by_task": TASK},
                    actor="cc", authority="accepted", session_id=session_id)
            out.append(rec)
    finally:
        driver.close()
    print(json.dumps({"task": TASK, "target_state": TARGET_STATE, "dry_run": a.dry_run,
                      "moved": len(out), "values_that_differ": [r for r in out
                                                                if r["moved_value"]],
                      "not_moved_successor_not_published": unmatched, "results": out},
                     indent=1, default=str))
    return 1 if unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
