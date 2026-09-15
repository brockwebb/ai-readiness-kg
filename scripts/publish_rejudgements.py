#!/usr/bin/env python3
"""Put every re-judgement the project has asserted on the append-only log, oldest first.
**Zero model calls. No network. No host is contacted and no evidence is promoted.**

Task `cc_tasks/2026-09-14_rejudgements_on_the_log.md`, implementing DN-003 decisions 1 to 6.
Fourteen re-judged payloads live in `state/`; two of them (`scan_2026-09-07_rj1`,
`scan_2026-09-07b_rj1`) reached the log in 2026-09-08 and twelve never did — including
`scan_2026-09-10_rj2`, the judgement of record for the published report. A judgement of record
that is not on the log fails DD-001: a stranger replaying the log gets a different instrument
than the one that published.

**§1 runs before anything is written and STOPS on any payload whose cited `obs_id`s are not
already on the log.** Such a payload is one whose SOURCE cycle was never published, and it is
named here rather than discovered afterwards as an orphan Finding that an append-only log then
keeps forever (`cc_tasks/2026-09-07_scan_hygiene.md` §1, and the 120 that taught it).

**Generation order** (DN-003 decision 5) is derived from the names, not typed:
`publish.publication_order` sorts by `(generation, cycle)` so no judgement is published before
the one it replaces. Each cycle is written and then projected, so the graph is never a
generation behind the log.

**`--project-once` is a wall-clock fix and not a different result**
(`2026-09-14_rejudgements_on_the_log_RESULT.md` §7 item 4). Publishing the fourteen cycles took
3 h 46 m, almost all of it in fourteen full projections that each produced the same end state
the last one does. `project()` is RESET-AND-REPLAY: it deletes every scan-schema label and
rebuilds them from the whole log, so it is a pure function of the log and running it N times
leaves exactly what running it once leaves. The per-cycle default is kept, because for a LIVE
cadence — one cycle, published as it is judged — the graph should never be a generation behind
the log even for the length of a run; `--project-once` is for a BACKLOG, where the intermediate
states are ones nobody reads and every one of them is discarded by the next reset.

    /opt/anaconda3/bin/python3 scripts/publish_rejudgements.py --dry-run
    /opt/anaconda3/bin/python3 scripts/publish_rejudgements.py --no-project    # write only
    /opt/anaconda3/bin/python3 scripts/publish_rejudgements.py --project-once  # a backlog
    /opt/anaconda3/bin/python3 scripts/publish_rejudgements.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

TASK = "cc_tasks/2026-09-14_rejudgements_on_the_log.md"
OUT = REPO / "state" / "rejudgements_on_the_log_2026-09-14.json"


def _publish():
    """`scan/publish.py` BY PATH — `assessment/harness/` holds a second `run.py` and the same
    ambiguity is why every loader in this repo is path-based."""
    spec = importlib.util.spec_from_file_location(
        "scan_publish_rj", REPO / "assessment" / "harness" / "scan" / "publish.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def payloads(pub) -> dict:
    """`cycle -> payload` for every re-judged payload in `state/`, keyed by FILE STEM.

    Not by the `cycle` field: `state/scan_2026-09-07b_rj2.json` names itself `_rj1`, a recorded
    defect of the tool that wrote it, and keying on the field would silently collapse two
    judgements of cycle 2 into one entry (`publish.cycle_of`).
    """
    out = {}
    for path in sorted((REPO / "state").glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(doc, dict) and "findings_detail" in doc and pub.is_rejudgement(doc):
            out[path.stem] = doc
    return out


def shard_digests() -> dict:
    """`shard name -> (bytes, sha256)` for every shard the graph replay reads.

    The baseline half of the append-only check. Taken before a single event is written and
    compared after: a shard that SHRANK, or whose recorded bytes are no longer a prefix of what
    it holds, is a rewritten log, and no gate downstream of that means anything.
    """
    from kg import eventlog
    return {p.name: [p.stat().st_size,
                     hashlib.sha256(p.read_bytes()).hexdigest()]
            for p in eventlog.shards()}


def preflight(pub, docs: dict) -> dict:
    """§1. Everything that would make a write wrong, checked before any write happens.

    Three questions, and each has exactly one answer that lets the run continue:

    * is every `obs_id` this payload cites already on the log? (its source cycle was published)
    * does the payload it supersedes exist on disk? (the chain is complete)
    * do the payloads and the log agree about what has already been published? (nothing is
      being written twice, and nothing already written is being contradicted)
    """
    from kg import eventlog
    on_log_obs, on_log_find, paired = set(), set(), set()
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == pub.OBS_EVENT:
            on_log_obs.add(ev["obs_id"])
        elif t == pub.FIND_EVENT:
            on_log_find.add(ev["finding_id"])
        elif t == pub.SUPERSEDES_EVENT:
            paired.add(ev["finding_id"])

    rows, stop = [], []
    for cycle in pub.publication_order(docs):
        doc = docs[cycle]
        fids = [f["finding_id"] for f in doc["findings_detail"]]
        cited = {o for f in doc["findings_detail"] for o in (f.get("evidence") or [])}
        missing = sorted(cited - on_log_obs)
        pred = pub.supersedes_of(cycle)
        pred_path = REPO / "state" / f"{pred}.json" if pred else None
        row = {
            "cycle": cycle,
            "generation": pub.generation(cycle),
            "source_cycle": pub.source_cycle_of(doc),
            "supersedes": pred,
            "supersedes_payload_present": bool(pred_path and pred_path.is_file()),
            "findings": len(fids),
            "observations_on_payload": len(doc.get("observations_detail") or []),
            "cited_obs_ids": len(cited),
            "cited_obs_ids_not_on_log": len(missing),
            "findings_already_on_log": sum(1 for f in fids if f in on_log_find),
            "supersession_already_on_log": sum(1 for f in fids if f in paired),
            "shard": pub.shard_name(pub.shard_for(cycle, fids)),
        }
        if missing:
            stop.append(f"{cycle} cites {len(missing)} obs_id(s) that are not on the log "
                        f"(e.g. {missing[:3]}): its source cycle "
                        f"{pub.source_cycle_of(doc)} was never published")
        if doc.get("observations_detail"):
            stop.append(f"{cycle} carries {len(doc['observations_detail'])} Observation(s); "
                        f"a re-judgement creates no evidence")
        if pred and not pred_path.is_file():
            stop.append(f"{cycle} supersedes {pred}, whose payload is not on disk")
        rows.append(row)
    return {"cycles": rows, "stop": stop}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="run §1 and print the plan; write nothing")
    ap.add_argument("--no-project", action="store_true",
                    help="write the events without projecting at all")
    ap.add_argument("--project-once", action="store_true",
                    help="project ONCE after the last cycle instead of after each one. Same "
                         "end-state graph; see the module docstring.")
    ap.add_argument("--only", default=None, metavar="CYCLE")
    a = ap.parse_args(argv)

    pub = _publish()
    docs = payloads(pub)
    if a.only:
        docs = {k: v for k, v in docs.items() if k == a.only}
        if not docs:
            raise SystemExit(f"REFUSING: {a.only} is not a re-judged payload in state/")
    pre = preflight(pub, docs)
    before = shard_digests()
    print(json.dumps({"rejudged_payloads": len(docs),
                      "publication_order": [r["cycle"] for r in pre["cycles"]],
                      "preflight": pre["cycles"], "stop": pre["stop"],
                      "shards_before": before}, indent=1))
    if pre["stop"]:
        print("\nSTOP — nothing written:\n  " + "\n  ".join(pre["stop"]), file=sys.stderr)
        return 2
    if a.dry_run:
        print("\nDRY RUN — nothing written", file=sys.stderr)
        return 0

    if a.no_project and a.project_once:
        raise SystemExit("REFUSING: --no-project and --project-once contradict each other")

    def _project(rec):
        counts = pub.project()
        rec["projection"] = {k: counts[k] for k in
                             ("observations", "findings", "supports", "supersedes",
                              "supersedes_unresolved", "findings_current",
                              "findings_superseded")}

    written, projections = [], 0
    for row in pre["cycles"]:
        cycle = row["cycle"]
        src = REPO / "state" / f"{cycle}.json"
        rec = {"cycle": cycle, "generation": row["generation"]}
        rec.update(pub.write_events(docs[cycle], src))
        rec.update(pub.write_supersession(docs[cycle], src))
        if not (a.no_project or a.project_once):
            _project(rec)
            projections += 1
        written.append(rec)
        print(json.dumps(rec, indent=1), flush=True)
    if a.project_once and written:
        _project(written[-1])
        projections += 1
        print(json.dumps({"projected_once_after": written[-1]["cycle"],
                          "projection": written[-1]["projection"]}, indent=1), flush=True)

    after = shard_digests()
    shrank = [n for n, (size, _) in before.items() if after.get(n, [0])[0] < size]
    record = {"task": TASK, "rejudged_payloads": len(docs),
              "publication_order": [r["cycle"] for r in written],
              "projection_mode": ("none" if a.no_project
                                  else "once" if a.project_once else "per_cycle"),
              "projections_run": projections,
              "written": written, "shards_before": before, "shards_after": after,
              "shards_that_shrank": shrank,
              "census": pub.census()}
    OUT.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"written_cycles": len(written), "projections_run": projections,
                      "shards_that_shrank": shrank,
                      "record": str(OUT.relative_to(REPO))}, indent=1))
    return 1 if shrank else 0


if __name__ == "__main__":
    raise SystemExit(main())
