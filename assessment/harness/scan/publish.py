#!/usr/bin/env python3
"""Write a cycle's Observations and Findings to the event log, and project them. **Zero spend.**

Task §2.2 and §3. Observations are evidence and evidence belongs on the append-only log; the
graph is a projection of it, as everywhere else here. Idempotent on `obs_id` / `finding_id`,
both of which are DERIVED, so re-running a cycle that observed the same thing under the same
params adds nothing.

**Labelled Cypher only** — the lint from `230b282f` applies, and DD-020's
`<doc_id>::<item_id>` non-uniqueness is why.

    /opt/anaconda3/bin/python3 assessment/harness/scan/publish.py --from state/scan_smoke_2026-09-06.json
    /opt/anaconda3/bin/python3 assessment/harness/scan/publish.py --project
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

#: Its own shard, and this time checked to be free before use — batch 27 was not, and the
#: 2026-09-06 bare-span backfill had to record that rather than move its events.
SCAN_BATCH = 29
OBS_EVENT = "observation_recorded"
FIND_EVENT = "finding_derived"


def write_events(payload: dict) -> dict:
    from kg import eventlog
    seen_obs = {ev.get("obs_id") for ev in eventlog.replay() if ev.get("event_type") == OBS_EVENT}
    seen_fnd = {ev.get("finding_id") for ev in eventlog.replay()
                if ev.get("event_type") == FIND_EVENT}
    n_o = n_f = 0
    for o in payload["observations_detail"]:
        if o["obs_id"] in seen_obs:
            continue
        eventlog.append({"event_type": OBS_EVENT, **o}, batch=SCAN_BATCH)
        n_o += 1
    for f in payload["findings_detail"] + payload.get("control_findings_detail", []):
        if f["finding_id"] in seen_fnd:
            continue
        eventlog.append({"event_type": FIND_EVENT, **f}, batch=SCAN_BATCH)
        n_f += 1
    return {"observation_events_written": n_o, "finding_events_written": n_f}


SCAN_LABELS = ("Observation", "Finding", "Rule")


def project() -> dict:
    from kg import eventlog
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    #: `observed_on_missing_document` is an INTEGRITY check — an observation of a surface the
    #: graph has no Document for. Control observations legitimately have none (a fixture is
    #: not a corpus document), so they are counted apart; folding them in would leave the
    #: check permanently non-zero and therefore meaningless.
    counts = {"observations": 0, "findings": 0, "rules": 0, "observed_on": 0, "supports": 0,
              "ruled_by": 0, "observed_on_missing_document": 0, "control_observations": 0}
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            pred = " OR ".join(f"n:{l}" for l in SCAN_LABELS)
            s.run(f"MATCH (n) WHERE {pred} DETACH DELETE n")
            for ev in eventlog.replay():
                t = ev.get("event_type")
                if t == OBS_EVENT:
                    s.run("MERGE (o:Observation {obs_id: $id}) SET o.leg = $leg, "
                          "o.indicator_code = $code, o.surface_doc_id = $doc, "
                          "o.captured_at = $at, o.collector = $col, "
                          "o.evidence_hash = $hash, o.raw_ref = $ref, "
                          "o.error_class = $err, o.params_hash = $ph",
                          id=ev["obs_id"], leg=ev["leg"], code=ev["spec_code"],
                          doc=ev["target_doc_id"], at=ev["captured_at"],
                          col=ev["collector"],
                          hash=(ev.get("response") or {}).get("body_sha256"),
                          ref=(ev.get("response") or {}).get("body_path"),
                          err=ev.get("error_class"), ph=ev["params_hash"])
                    counts["observations"] += 1
                    hit = s.run("MATCH (d:Document {doc_id: $d}) RETURN count(d) AS n",
                                d=ev["target_doc_id"]).single()["n"]
                    if hit:
                        s.run("MATCH (o:Observation {obs_id: $id}) "
                              "MATCH (d:Document {doc_id: $d}) MERGE (o)-[:OBSERVED_ON]->(d)",
                              id=ev["obs_id"], d=ev["target_doc_id"])
                        counts["observed_on"] += 1
                    elif str(ev["target_doc_id"]).startswith("control:"):
                        counts["control_observations"] += 1
                    else:
                        counts["observed_on_missing_document"] += 1
                elif t == FIND_EVENT:
                    s.run("MERGE (f:Finding {finding_id: $id}) SET f.rule_id = $rid, "
                          "f.indicator_code = $code, f.verdict = $v, f.reason = $r, "
                          "f.params_hash = $ph, f.target_doc_id = $doc",
                          id=ev["finding_id"], rid=ev["rule_id"], code=ev["spec_code"],
                          v=ev["verdict"], r=ev["reason"], ph=ev["params_hash"],
                          doc=ev["target_doc_id"])
                    counts["findings"] += 1
                    s.run("MERGE (r:Rule {rule_id: $rid}) SET r.version = $ver",
                          rid=ev["rule_id"], ver=ev["rule_version"])
                    s.run("MATCH (f:Finding {finding_id: $id}) MATCH (r:Rule {rule_id: $rid}) "
                          "MERGE (f)-[:RULED_BY]->(r)", id=ev["finding_id"], rid=ev["rule_id"])
                    counts["ruled_by"] += 1
                    for oid in ev.get("evidence") or []:
                        s.run("MATCH (o:Observation {obs_id: $o}) "
                              "MATCH (f:Finding {finding_id: $f}) MERGE (o)-[:SUPPORTS]->(f)",
                              o=oid, f=ev["finding_id"])
                        counts["supports"] += 1
            counts["rules"] = s.run("MATCH (r:Rule) RETURN count(r)").single()[0]
    finally:
        driver.close()
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default=None)
    ap.add_argument("--project", action="store_true")
    a = ap.parse_args(argv)
    out = {}
    if a.src:
        out.update(write_events(json.loads(Path(a.src).read_text(encoding="utf-8"))))
    if a.project:
        out.update(project())
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
