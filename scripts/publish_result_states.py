#!/usr/bin/env python3
"""Move the Results the L0 report tags through `proposed -> verified -> published`.

`cc_tasks/2026-09-12_publish_l0.md` §1 and §2, implementing DN-002 decision 3:
*Result states are real before publication.* **Zero model spend, zero network.**

Two verbs, and the order between them is the whole point:

    verify   proposed -> verified, and ONLY for a Result whose value was re-derived from its
             generating artifact in this session and reproduced. The evidence is the report
             `scripts/rederive_tagged_results.py` writes; this script reads it and refuses
             anything it does not find there with verdict `reproduces`. A state that can be
             set without the evidence is a label, not a state.

    publish  verified -> published, stamped with the commit that published the tree. That
             commit cannot exist before the commit is made, so this runs AFTER the publish
             commit and takes its sha on the command line. The state transition writes an
             `artifact_state_changed` event; the sha rides on the `artifact_updated` event
             that follows it, because `transition_state`'s payload shape is fixed and adding
             a field to it would be an edit to Seldon's event contract.

**Why not `seldon result verify`.** It exists and it does the right transition, and it records
`actor="human"`. The actor on these transitions is this session, and an event log that says a
person verified fifty-nine Results nobody looked at is worse than no actor field at all. The
transition itself goes through `seldon.core.artifacts.transition_state` — Seldon's own
validated path, which checks the move against the domain state machine, appends the event and
updates Neo4j — so nothing here re-implements a state machine.

    /opt/anaconda3/bin/python3 scripts/publish_result_states.py verify \
        --report state/rederive_tagged_2026-09-12.json [--dry-run]
    /opt/anaconda3/bin/python3 scripts/publish_result_states.py publish \
        --report state/rederive_tagged_2026-09-12.json --commit <sha> [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, "/Users/brock/GitHub/seldon")
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-12_publish_l0.md"

#: What each verb may move, and from where. Declared as a table rather than branched in the
#: body so the legal moves are readable in one place and agree with `research.yaml`'s
#: `state_machines.Result` (proposed -> verified -> published).
MOVES = {"verify": ("proposed", "verified"), "publish": ("verified", "published")}


def reproducing(report_path: Path) -> list:
    """The tagged names the re-derivation reproduced. Refuses a report that is not a PASS."""
    if not report_path.is_file():
        raise SystemExit(f"FATAL: {report_path} does not exist. Nothing is verified without "
                         f"the re-derivation that justifies it; run "
                         f"scripts/rederive_tagged_results.py first.")
    doc = json.loads(report_path.read_text(encoding="utf-8"))
    if doc.get("gate") != "PASS":
        raise SystemExit(f"FATAL: {report_path.name} records gate {doc.get('gate')!r}. "
                         f"§1 stops on a Result that does not re-derive; no state moves.")
    names = [r["name"] for r in doc["rows"] if r["verdict"] == "reproduces"]
    if len(names) != doc["tagged"]:
        raise SystemExit(f"FATAL: {report_path.name} says {doc['tagged']} tagged and only "
                         f"{len(names)} reproduce; a PASS and a shortfall cannot both be true")
    return names


def head_sha() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot read HEAD: {r.stderr.strip()[-200:]}")
    return r.stdout.strip()


def run(verb: str, names: list, commit: str | None, dry: bool) -> dict:
    from seldon.config import get_current_session, get_neo4j_driver, load_project_config
    from seldon.core.artifacts import transition_state, update_artifact
    from seldon.core.graph import get_artifact
    from seldon.commands.result import _get_domain_config

    frm, to = MOVES[verb]
    cfg = load_project_config(REPO)
    db = cfg["neo4j"]["database"]
    driver = get_neo4j_driver(cfg)
    # Seldon's own resolver: `load_domain_config` takes a PATH, and the mapping from
    # `project.domain` to `seldon/domain/<name>.yaml` lives in exactly one place upstream.
    domain = _get_domain_config(cfg)
    session_id = get_current_session(REPO)

    moved, already, wrong_state, missing = [], [], [], []
    try:
        for name in names:
            with driver.session(database=db) as s:
                rows = s.run("MATCH (r:Result {name: $n}) WHERE r.state <> 'superseded' "
                             "RETURN r.artifact_id AS id, r.state AS state", n=name).data()
            if len(rows) != 1:
                missing.append(f"{name}: {len(rows)} live Results")
                continue
            aid, state = rows[0]["id"], rows[0]["state"]
            if state == to:
                already.append(name)
                continue
            if state != frm:
                wrong_state.append(f"{name}: {state}, expected {frm}")
                continue
            if dry:
                moved.append(name)
                continue
            transition_state(project_dir=REPO, driver=driver, database=db,
                             domain_config=domain, artifact_id=aid, artifact_type="Result",
                             current_state=state, new_state=to, actor="cc",
                             authority="accepted", session_id=session_id)
            if verb == "publish":
                update_artifact(project_dir=REPO, driver=driver, database=db, artifact_id=aid,
                                properties={"published_commit": commit,
                                            "published_at": datetime.now(timezone.utc)
                                            .isoformat().replace("+00:00", "Z"),
                                            "published_by_task": TASK},
                                actor="cc", authority="accepted", session_id=session_id)
            moved.append(name)
    finally:
        driver.close()

    out = {"verb": verb, "from": frm, "to": to, "of": len(names), "moved": len(moved),
           "already_at_target": len(already), "wrong_state": wrong_state, "missing": missing,
           "dry_run": dry}
    if verb == "publish":
        out["commit"] = commit
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", choices=sorted(MOVES))
    ap.add_argument("--report", required=True,
                    help="the re-derivation report that justifies the move")
    ap.add_argument("--commit", default=None,
                    help="publish only: the sha of the commit that published the tree")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    names = reproducing(Path(a.report))
    commit = None
    if a.verb == "publish":
        commit = a.commit or head_sha()
        if len(commit) < 12:
            raise SystemExit(f"FATAL: {commit!r} is not a commit sha")
    out = run(a.verb, names, commit, a.dry_run)
    print(json.dumps(out, indent=1))
    return 1 if out["wrong_state"] or out["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
