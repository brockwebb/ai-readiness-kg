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
import shutil
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
#: A RE-JUDGED cycle gets its own shard too, and for a sharper reason than a measured one: its
#: Findings cite `obs_id`s that live on ANOTHER shard, so "the events of the re-judgement" is
#: only a file if the judgements are alone in it. `cc_tasks/2026-09-08_scan_harness_v4.md` §1.5.
CYCLE_BATCH = {"scan_2026-09-07": 31, "scan_2026-09-07b": 38,
               "scan_2026-09-07_rj1": 40, "scan_2026-09-07b_rj1": 41,
               "scan_2026-09-09": 42}
OBS_EVENT = "observation_recorded"
FIND_EVENT = "finding_derived"
#: `cc_tasks/2026-09-07_scan_hygiene.md` §1. A Finding whose `evidence` names `obs_id`s the log
#: does not hold is the same class of claim as a grounding span whose bytes are missing
#: (invariant 3). One of these events, written by `scripts/annotate_orphan_findings.py`, is the
#: append-only admission that the evidence is gone — and it is the ONLY thing that licenses
#: such a Finding to sit on the log. See `write_events`.
UNRETAINED_EVENT = "finding_evidence_unretained"
#: `cc_tasks/2026-09-07_scan_harness_v3.md` §1.2. The same append-only shape one layer down: an
#: Observation's `error_class` was misfiled by a fallback the closed set gave no better answer
#: to, and the line is never edited (its `obs_id` is DERIVED from that class, so an edit would
#: re-identify the record and orphan the Findings citing it). The overlay carries the class it
#: should have had; the projection reads it and keeps the recorded one beside it.
RECLASSIFIED_EVENT = "observation_error_reclassified"


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
    """Append this cycle's Observations and Findings, refusing any Finding whose evidence the
    log will not hold.

    The refusal (`cc_tasks/2026-09-07_scan_hygiene.md` §1) is the standing rule the 120 orphan
    control Findings of 2026-09-06 exist because nothing enforced: the scaffold published
    Findings derived from fixture Observations it had already dropped, and an append-only log
    then kept them forever. A Finding is admitted only if every `obs_id` it cites is on the log
    or in this same payload — or if it carries a `finding_evidence_unretained` annotation, the
    append-only way of saying "the evidence is gone and here is why".

    It fails LOUD and writes nothing: the observations are appended after the check, so a
    refused payload leaves the log exactly as it found it.
    """
    from kg import eventlog
    batch = batch_for(payload)
    seen_obs, seen_fnd, annotated = set(), set(), set()
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == OBS_EVENT:
            seen_obs.add(ev.get("obs_id"))
        elif t == FIND_EVENT:
            seen_fnd.add(ev.get("finding_id"))
        elif t == UNRETAINED_EVENT:
            annotated.add(ev.get("finding_id"))

    findings = payload["findings_detail"] + payload.get("control_findings_detail", [])
    admissible = seen_obs | {o["obs_id"] for o in payload["observations_detail"]}
    ungrounded = [
        (f["finding_id"], sorted(set(f.get("evidence") or []) - admissible))
        for f in findings
        if f["finding_id"] not in annotated
        and not set(f.get("evidence") or []) <= admissible
    ]
    if ungrounded:
        detail = "; ".join(f"{fid} misses {ids}" for fid, ids in ungrounded[:5])
        raise SystemExit(
            f"REFUSING: {len(ungrounded)} Finding(s) cite obs_ids that are neither on the log "
            f"nor in this payload, and carry no `{UNRETAINED_EVENT}` annotation: {detail}"
            f"{' …' if len(ungrounded) > 5 else ''}. Publish the Observations with them, or "
            f"annotate the Findings (scripts/annotate_orphan_findings.py).")

    n_o = n_f = 0
    for o in payload["observations_detail"]:
        if o["obs_id"] in seen_obs:
            continue
        eventlog.append({"event_type": OBS_EVENT, **o}, batch=batch)
        n_o += 1
    for f in findings:
        if f["finding_id"] in seen_fnd:
            continue
        eventlog.append({"event_type": FIND_EVENT, **f}, batch=batch)
        n_f += 1
    return {"observation_events_written": n_o, "finding_events_written": n_f,
            "findings_evidence_unretained": sum(1 for f in findings
                                                if f["finding_id"] in annotated),
            "shard": f"events/batch-{batch:03d}.jsonl"}


#: `cc_tasks/2026-09-07_scan_run_2.md` §1.1. The one direction bytes may travel into the
#: committed evidence store.
def promote_evidence(payload: dict, staging: Path | None = None,
                     committed: Path | None = None) -> dict:
    """Copy into `corpus/evidence/scan/` exactly the bodies this payload's Observations cite,
    then delete the staging directory.

    Inverts the default that produced two separate hygiene defects: `run.py` used to write
    every body it fetched straight into the committed store, so a diagnostic run, an aborted
    run, and a fixture run all left bytes behind that nothing ever cited (418 tracked bodies
    cited by no Observation; 260 fixture blobs quarantined). Content-addressed storage makes
    that cheap to do and impossible to undo cleanly — the digest tells you nothing about who
    wanted the body.

    Promotion is CITATION-driven, which is the same rule invariant 3 states one layer up: no
    grounding span, no write. A body in the committed store is a claim that some Observation
    on the log points at it, and this is the only thing that makes the claim true.

    A cited digest with no body anywhere is a hard failure, not a warning: publishing a
    Finding whose evidence the repo does not hold is precisely the orphan-Finding defect
    `cc_tasks/2026-09-07_scan_hygiene.md` §1 had to annotate 120 of.

    Paths are REWRITTEN on the payload's observations, because a `body_path` pointing into a
    staging directory that this function then deletes is a dangling reference on an
    append-only log. Safe to rewrite: `body_path` is not an input to the derived `obs_id`
    (`model.Observation.make` hashes `body_sha256`), so the record keeps its identity.
    """
    from scan.model import EVIDENCE_ROOT
    committed = committed or EVIDENCE_ROOT
    staging = Path(staging or payload.get("evidence_root") or "")
    if not staging.is_absolute():
        staging = REPO / staging
    obs = payload.get("observations_detail") or []
    cited = {(o.get("response") or {}).get("body_sha256") for o in obs}
    cited.discard(None)

    promoted, already, missing = [], [], []
    for digest in sorted(cited):
        dest = committed / digest[:2] / digest
        if dest.exists():
            already.append(digest)
            continue
        src = staging / digest[:2] / digest
        if not src.is_file():
            missing.append(digest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        promoted.append(digest)
    if missing:
        raise SystemExit(
            f"REFUSING: {len(missing)} body digest(s) cited by this payload's Observations are "
            f"in neither the staging root ({staging}) nor the committed store: "
            f"{missing[:5]}{' …' if len(missing) > 5 else ''}. A Finding whose evidence the "
            f"repo does not hold is not evidence (invariant 3).")

    for o in obs:
        d = (o.get("response") or {}).get("body_sha256")
        if d:
            o["response"]["body_path"] = str(
                (committed / d[:2] / d).relative_to(REPO)
                if str(committed).startswith(str(REPO)) else committed / d[:2] / d)
    if staging.is_dir() and staging != committed:
        shutil.rmtree(staging)
    return {"evidence_promoted": len(promoted),
            "evidence_already_committed": len(already),
            "evidence_cited_digests": len(cited),
            "staging_removed": str(staging) if staging.name else None}


#: The synthetic id scheme, defined in `model.py` beside the rest of the id model.
#: Imported rather than repeated: see the comment there for the 957 observations a
#: second copy cost.
#:
#: ABSOLUTE, because this file is BOTH a module the tests import as `scan.publish` and a script
#: the cycle runs as `python assessment/harness/scan/publish.py`. A relative import works in the
#: first case and raises `ImportError: attempted relative import with no known parent package`
#: in the second — which is how cycle 4 found it, after the run and before the publish. The
#: `sys.path` inserts at the top of this file are what make the absolute form work either way.
from scan.model import SYNTHETIC_PREFIXES                            # noqa: E402
CONTROL_PREFIX = "control:"

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
              "host_observations": 0, "findings_evidence_unretained": 0,
              "observations_error_reclassified": 0}
    # Read the annotations BEFORE the replay, because an annotation may be appended to a later
    # shard than the Finding it corrects — that is what an append-only correction is — and a
    # single forward pass would project the Finding before it had seen the event that qualifies
    # it. `edge_endpoint_alias` in batch-005 has the same shape for the same reason.
    unretained, reclassified = set(), {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == UNRETAINED_EVENT:
            unretained.add(ev.get("finding_id"))
        elif t == RECLASSIFIED_EVENT:
            reclassified[ev["obs_id"]] = ev["error_class"]
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
                          "o.error_class = $err, o.error_class_recorded = $err0, "
                          "o.error_reclassified = $recl, o.params_hash = $ph",
                          id=ev["obs_id"], leg=ev["leg"], code=ev["spec_code"],
                          doc=ev["target_doc_id"], at=ev["captured_at"],
                          col=ev["collector"],
                          hash=(ev.get("response") or {}).get("body_sha256"),
                          ref=(ev.get("response") or {}).get("body_path"),
                          err=reclassified.get(ev["obs_id"], ev.get("error_class")),
                          err0=ev.get("error_class"),
                          recl=ev["obs_id"] in reclassified, ph=ev["params_hash"])
                    counts["observations"] += 1
                    counts["observations_error_reclassified"] += int(
                        ev["obs_id"] in reclassified)
                    hit = s.run("MATCH (d:Document {doc_id: $d}) RETURN count(d) AS n",
                                d=ev["target_doc_id"]).single()["n"]
                    if hit:
                        s.run("MATCH (o:Observation {obs_id: $id}) "
                              "MATCH (d:Document {doc_id: $d}) MERGE (o)-[:OBSERVED_ON]->(d)",
                              id=ev["obs_id"], d=ev["target_doc_id"])
                        counts["observed_on"] += 1
                    elif str(ev["target_doc_id"]).startswith(CONTROL_PREFIX):
                        counts["control_observations"] += 1
                    # A well-known set is a SYNTHETIC host surface: nothing was admitted for
                    # it because there is nothing to admit. Same reasoning as the control
                    # observations above — folding either into the integrity check leaves it
                    # permanently non-zero and therefore meaningless.
                    elif str(ev["target_doc_id"]).startswith(SYNTHETIC_PREFIXES):
                        counts["host_observations"] += 1
                    else:
                        counts["observed_on_missing_document"] += 1
                elif t == FIND_EVENT:
                    # `evidence_unretained` is set on EVERY Finding, true or false, rather
                    # than only on the annotated ones: a property that is absent and a property
                    # that is false read the same way to `coalesce`, and the integrity check
                    # this exists for ("a Finding with no SUPPORTS edge and no annotation")
                    # deserves an answer that is stored rather than inferred from a missing key.
                    unret = ev["finding_id"] in unretained
                    s.run("MERGE (f:Finding {finding_id: $id}) SET f.rule_id = $rid, "
                          "f.indicator_code = $code, f.verdict = $v, f.reason = $r, "
                          "f.params_hash = $ph, f.target_doc_id = $doc, "
                          "f.evidence_unretained = $unret",
                          id=ev["finding_id"], rid=ev["rule_id"], code=ev["spec_code"],
                          v=ev["verdict"], r=ev["reason"], ph=ev["params_hash"],
                          doc=ev["target_doc_id"], unret=unret)
                    counts["findings"] += 1
                    counts["findings_evidence_unretained"] += int(unret)
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
    ap.add_argument("--no-promote", action="store_true",
                    help="publish without promoting staged bodies (for a payload whose "
                         "evidence is already in the committed store)")
    a = ap.parse_args(argv)
    out = {}
    if a.src:
        src = Path(a.src)
        payload = json.loads(src.read_text(encoding="utf-8"))
        # Promote BEFORE the events are written, so the `body_path` that lands on the
        # append-only log already points into the committed store. The other order would put
        # a staging path — a directory this run then deletes — on a line that can never be
        # edited. `--no-promote` exists for the four cycles published before staging existed,
        # whose bodies are already committed and have no staging root to find.
        if not a.no_promote:
            out.update(promote_evidence(payload))
            src.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")
        out.update(write_events(payload))
    if a.project:
        out.update(project())
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
