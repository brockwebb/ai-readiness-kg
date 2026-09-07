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
#: 2026-09-06 bare-span backfill had to record that rather than move its events. Each CYCLE
#: gets its own shard: two cycles sharing one would be readable but would make "the events of
#: the 2026-09-07 cycle" a query rather than a file, and the shard is the unit an operator
#: reaches for when something is wrong.
SCAN_BATCH = 29
CYCLE_BATCH = {"scan_2026-09-07": 31}
OBS_EVENT = "observation_recorded"
FIND_EVENT = "finding_derived"


def batch_for(payload: dict) -> int:
    """The shard this cycle's events belong on, refusing a shard that already holds another
    cycle's. A cycle silently appended to a shard it does not own is exactly the defect the
    bare-span backfill had to record instead of fixing."""
    cycle = payload.get("cycle")
    batch = CYCLE_BATCH.get(cycle, SCAN_BATCH)
    path = REPO / "events" / f"batch-{batch:03d}.jsonl"
    if path.is_file() and cycle in CYCLE_BATCH:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            other = ev.get("params_hash")
            if other and other != payload["params_hash"]:
                raise SystemExit(
                    f"REFUSING: events/batch-{batch:03d}.jsonl already holds events under "
                    f"params_hash {other[:12]}…, not this cycle's {payload['params_hash'][:12]}…")
    return batch


def write_events(payload: dict) -> dict:
    from kg import eventlog
    batch = batch_for(payload)
    seen_obs = {ev.get("obs_id") for ev in eventlog.replay() if ev.get("event_type") == OBS_EVENT}
    seen_fnd = {ev.get("finding_id") for ev in eventlog.replay()
                if ev.get("event_type") == FIND_EVENT}
    n_o = n_f = 0
    for o in payload["observations_detail"]:
        if o["obs_id"] in seen_obs:
            continue
        eventlog.append({"event_type": OBS_EVENT, **o}, batch=batch)
        n_o += 1
    for f in payload["findings_detail"] + payload.get("control_findings_detail", []):
        if f["finding_id"] in seen_fnd:
            continue
        eventlog.append({"event_type": FIND_EVENT, **f}, batch=batch)
        n_f += 1
    return {"observation_events_written": n_o, "finding_events_written": n_f,
            "shard": f"events/batch-{batch:03d}.jsonl"}


SCAN_LABELS = ("Observation", "Finding", "Rule")


def link_rules_to_indicators(session) -> dict:
    """`Rule -[:MEASURES]-> AssessmentIndicator`, and the Rule properties that edge implies.

    The two layers are projected by two scripts with two sources — the scan layer from the
    event log (here), the framework layer from `framework/ai_readiness_framework.json`
    (`scripts/load_framework_graph.py`) — and each one's reset removes the edge BETWEEN them.
    So the bridge is rebuilt by whichever ran last: both projectors call this, and running
    either alone leaves the graph whole. That is the whole reason this is a function and not
    four lines inlined in `project()`.

    `Rule.version` is parsed from the rule id, never read from the Finding's `rule_version`:
    that field is the literal `"v1"` for every rule ever shipped (`rules/_common.py`) and it
    is an INPUT to the derived `finding_id`, so it cannot be corrected in the events without
    re-identifying all 1,353 stored Findings. See `rules.parse_rule_id`.

    An unresolvable rule id or an indicator code with no node is COUNTED, never skipped
    silently — a Rule with no MEASURES edge is the defect this exists to make visible.
    """
    from scan.rules import CURRENT, parse_rule_id
    counts = {"measures": 0, "rules_seen": 0, "rules_unparseable": [],
              "rules_without_indicator": []}
    current_ids = set(CURRENT.values())
    for rec in list(session.run("MATCH (r:Rule) RETURN r.rule_id AS rid ORDER BY rid")):
        rid = rec["rid"]
        counts["rules_seen"] += 1
        try:
            parsed = parse_rule_id(rid)
        except ValueError:
            counts["rules_unparseable"].append(rid)
            continue
        session.run("MATCH (r:Rule {rule_id: $rid}) SET r.version = $ver, "
                    "r.indicator_code = $code, r.qualifier = $q, r.current = $cur",
                    rid=rid, ver=parsed["version"], code=parsed["indicator_code"],
                    q=parsed["qualifier"], cur=rid in current_ids)
        n = session.run("MATCH (r:Rule {rule_id: $rid}) "
                        "MATCH (i:AssessmentIndicator {code: $code}) "
                        "MERGE (r)-[:MEASURES]->(i) RETURN count(*) AS n",
                        rid=rid, code=parsed["indicator_code"]).single()["n"]
        if n:
            counts["measures"] += 1
        else:
            counts["rules_without_indicator"].append(rid)
    return counts


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
              "ruled_by": 0, "observed_on_missing_document": 0, "control_observations": 0,
              "host_observations": 0}
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
                    # A well-known set is a SYNTHETIC host surface: nothing was admitted for
                    # it because there is nothing to admit. Same reasoning as the control
                    # observations above — folding either into the integrity check leaves it
                    # permanently non-zero and therefore meaningless.
                    elif str(ev["target_doc_id"]).startswith("host:"):
                        counts["host_observations"] += 1
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
            counts.update(link_rules_to_indicators(s))
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
