#!/usr/bin/env python3
"""Annotate every Finding on the log whose evidence the log does not hold. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_hygiene.md` §1. A Finding whose `evidence` names `obs_id`s that
no `observation_recorded` event carries is the same class of claim as a grounding span whose
bytes are missing: invariant 3 says no grounding span, no write, and a verdict nobody can
trace to a stored fact is a verdict nobody can check.

**Append-only correction, never a deletion** — the pattern this repo already uses for
`extraction_superseded` (batch-004) and `edge_endpoint_alias` (batch-005). The Findings keep
their ids and their lines; a new `finding_evidence_unretained` event says, on its face, that
the evidence behind them is gone and why.

How it happened, verified rather than assumed: `run_controls` in
`assessment/harness/scan/run.py` returns `control_obs + fixture_obs`, and its comment
("Retained, not discarded. The re-derivation gate can only check a Finding whose evidence it
still holds") records that an earlier working-tree version returned only the two synthetic E5
observations and dropped the thirty per-leg fixture observations. Findings derived from those
thirty were published; their Observations never were. Corroboration: two of the three
`params_hash` values these Findings carry match NO committed revision of
`assessment/harness/scan/params.yaml`, so they were produced by a working tree that was never
a commit — see `--report`, which prints the resolution for each.

    /opt/anaconda3/bin/python3 scripts/annotate_orphan_findings.py --report
    /opt/anaconda3/bin/python3 scripts/annotate_orphan_findings.py
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from kg import eventlog                                              # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_hygiene.md"
#: Its own shard, checked to be free before use — `publish.py::batch_for` records why a shard
#: silently shared between two purposes is a defect rather than a convenience.
BATCH = 32
EVENT = "finding_evidence_unretained"
OBS_EVENT = "observation_recorded"
FIND_EVENT = "finding_derived"
PARAMS_PATH = "assessment/harness/scan/params.yaml"

REASON = ("control observations discarded by the 2026-09-06 scaffold before publish; "
          "evidence not recoverable")


def params_hash_history() -> dict:
    """`params_hash -> commit` for every committed revision of `params.yaml`.

    Recomputed from the bytes in git, not remembered: this is the same recovery the harness's
    history gate performs, and it is what makes "these Findings were derived under parameters
    that were never committed" a checked statement rather than a guess.
    """
    from scan.model import params_hash
    import yaml
    out = {}
    log = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_PATH],
                         capture_output=True, text=True, cwd=REPO)
    if log.returncode:
        raise SystemExit(f"FATAL: git log failed: {log.stderr.strip()}")
    for commit in log.stdout.split():
        blob = subprocess.run(["git", "show", f"{commit}:{PARAMS_PATH}"],
                              capture_output=True, text=True, cwd=REPO)
        if blob.returncode:
            continue
        out.setdefault(params_hash(yaml.safe_load(blob.stdout)), commit[:8])
    return out


def cycle_by_params_hash() -> dict:
    """`params_hash -> cycle payload name` for every cycle payload still in `state/`.

    A Finding does not carry its cycle; the payload that published it does, and the payload's
    `params_hash` is the join. Where no payload survives, the cycle is genuinely unrecoverable
    and the annotation says so rather than inventing a name.
    """
    out = {}
    for p in sorted((REPO / "state").glob("scan_*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"FATAL: cannot read {p}: {exc}")
        ph = doc.get("params_hash")
        if ph:
            out.setdefault(ph, doc.get("cycle") or p.stem)
    return out


def orphans() -> list:
    """Every `finding_derived` event citing at least one `obs_id` no `observation_recorded`
    event carries, with the shard it sits on."""
    obs, finds = set(), []
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == OBS_EVENT:
            obs.add(ev["obs_id"])
        elif t == FIND_EVENT:
            finds.append(ev)
    return [ev for ev in finds
            if any(o not in obs for o in (ev.get("evidence") or []))]


def annotated() -> set:
    """`finding_id`s already carrying an unretained annotation. Makes this idempotent."""
    return {ev["finding_id"] for ev in eventlog.replay() if ev.get("event_type") == EVENT}


def rows() -> list:
    """One annotation event body per orphan Finding, ready to append."""
    hist, cycles = params_hash_history(), cycle_by_params_hash()
    out = []
    for ev in orphans():
        ph = ev["params_hash"]
        out.append({
            "event_type": EVENT,
            "finding_id": ev["finding_id"],
            "rule_id": ev["rule_id"],
            "leg": ev["leg"],
            "target_doc_id": ev["target_doc_id"],
            "cycle": cycles.get(ph),
            "params_hash": ph,
            # Two independent recoverability facts, both checked, neither assumed. A Finding
            # under parameters that were never committed cannot be re-derived even if its
            # Observations were somehow recovered, and that is a stronger statement than
            # "the evidence is missing".
            "params_committed_at": hist.get(ph),
            "params_recoverable": ph in hist,
            "missing_obs_ids": sorted(ev.get("evidence") or []),
            "reason": REASON,
            "annotated_by": TASK,
        })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="print the resolution, write nothing")
    a = ap.parse_args(argv)
    data = rows()
    already = annotated()
    todo = [r for r in data if r["finding_id"] not in already]
    summary = {
        "orphan_findings": len(data),
        "already_annotated": len(data) - len(todo),
        "to_annotate": len(todo),
        "by_target": dict(collections.Counter(r["target_doc_id"] for r in data)),
        "by_params_hash": {ph[:12]: n for ph, n in
                           collections.Counter(r["params_hash"] for r in data).items()},
        "params_never_committed": sum(1 for r in data if not r["params_recoverable"]),
        "cycle_unrecoverable": sum(1 for r in data if r["cycle"] is None),
        "shard": f"events/batch-{BATCH:03d}.jsonl",
    }
    if a.report:
        print(json.dumps(summary, indent=1))
        return 0
    shard = REPO / "events" / f"batch-{BATCH:03d}.jsonl"
    if shard.is_file():
        for line in shard.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("event_type") != EVENT:
                raise SystemExit(f"REFUSING: {shard.name} already holds events of another "
                                 f"kind; this annotation gets its own shard")
    for r in todo:
        eventlog.append(r, batch=BATCH)
    summary["written"] = len(todo)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
