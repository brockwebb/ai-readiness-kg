#!/usr/bin/env python3
"""Mark a registered DataFile as EPHEMERAL: derived on demand, deliberately not held.

`cc_tasks/2026-09-13_ephemeral_provenance.md` decision 1. **Zero model spend, no network
beyond Neo4j.**

**The problem this exists for.** A Result is `COMPUTED_FROM` a DataFile, and the DataFile names
a path. Four published Results name `state/scan_matrix_2026-09-10.json`, which nothing writes
and nothing holds: that cycle was measured and deliberately never reported, the judgement of
record is the re-judgement `_rj2`, and `tests/test_scan_figures.py::matrix` skips the whole
figure suite on exactly that absence (`cc_tasks/2026-09-10_harness_v5_blind.md` decision 6). A
stranger following the provenance chain reaches a dead path. The re-derivation script reached
the value anyway — because it carried, in code, the knowledge that this one generator must be
run into a temporary tree.

**That knowledge belongs on the node.** Re-pointing the Results at a file the repo does hold
would rewrite what happened: the matrix WAS computed and they WERE computed from it. So the
DataFile keeps its name, its path and its description, and gains three properties and an edge:

  materialized       false — the repository does not hold this path, by decision
  derivable_from     the artifact it can be recomputed from, which the repository DOES hold
  derivation_command the exact command that recomputes it, argv included
  derivation_note    why the absence is a decision rather than an omission
  -[:GENERATED_BY]-> the Script that would write it

`scripts/rederive_tagged_results.py` then reads the set of ephemeral DataFiles from the graph
and drives each one's `derivation_command` with its output root pointed at a temporary tree. No
generator is named in that engine, and the rule — *a DataFile whose absence is a decision is
re-derived into a temporary tree* — is stated once, in the registry.

**Nothing about the Results changes.** No value, no state, no `COMPUTED_FROM` edge. What
changes is what the DataFile says about itself.

**The update path is the registry's own.** `seldon.core.artifacts.update_artifact` writes an
`artifact_updated` event to `seldon_events.jsonl` and then updates the node in place — no new
node, no supersession, and the change is on the event log where a replay will find it. It is
called through Python rather than `seldon artifact update` because `-p KEY=VALUE` on the CLI can
only carry strings, and `materialized` has to be a real boolean: a node property reading
`"false"` is truthy to every consumer that tests it.

    /opt/anaconda3/bin/python3 scripts/mark_ephemeral_datafile.py \\
        --data-file scan_matrix_2026-09-10 \\
        --derivable-from state/scan_2026-09-10.json \\
        --generator scan_report \\
        --derivation-command 'scripts/scan_report.py --cycle scan_2026-09-10' \\
        --note '...' [--dry-run]

Refuses, before writing anything:

* a DataFile name that does not resolve to exactly one live artifact;
* a DataFile whose path the repository DOES hold — a file that exists is materialized, and
  marking it otherwise would be a false statement about the tree;
* a `derivable_from` the repository does NOT hold — the whole claim is that the value is still
  reachable, and an unreachable source makes it a dead end with extra words;
* a generator that does not resolve, or whose registered path is not what the derivation
  command runs.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, "/Users/brock/GitHub/seldon")
sys.path.insert(0, str(REPO / "scripts"))

TASK = "cc_tasks/2026-09-13_ephemeral_provenance.md"

#: The property that says "the repository does not hold this path, by decision". Named here so
#: the engine, the site builder and the tests all spell it one way.
MATERIALIZED = "materialized"


def _driver():
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    return get_neo4j_driver(cfg), cfg["neo4j"]["database"]


def node_properties(name: str) -> dict:
    """Every property of the one live artifact with this name, plus its outgoing edges."""
    driver, db = _driver()
    try:
        with driver.session(database=db) as s:
            rows = s.run(
                "MATCH (a {name: $n}) WHERE coalesce(a.state, '') <> 'superseded' "
                "OPTIONAL MATCH (a)-[rel]->(b) "
                "RETURN properties(a) AS props, "
                "       collect(DISTINCT type(rel) + ' -> ' + coalesce(b.name, '?')) AS edges",
                n=name).data()
    finally:
        driver.close()
    if len(rows) != 1:
        raise SystemExit(f"FATAL: {name!r} resolves to {len(rows)} live artifacts; exactly one "
                         f"is required before anything is written")
    props = dict(rows[0]["props"])
    props["_edges"] = sorted(e for e in rows[0]["edges"] if not e.startswith("null"))
    return props


def link(from_id: str, rel: str, to_id: str) -> None:
    """One `seldon link create`, which MERGEs, so re-running this script adds no second edge."""
    import subprocess
    r = subprocess.run(["seldon", "link", "create", from_id, rel, to_id, "--actor", "cc"],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot link {from_id} -{rel}-> {to_id}: "
                         f"{r.stderr.strip()[-400:]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-file", required=True, help="the registered DataFile's name")
    ap.add_argument("--derivable-from", required=True, metavar="PATH",
                    help="repo-relative path of the artifact it can be recomputed from")
    ap.add_argument("--generator", required=True,
                    help="the registered Script that would write it")
    ap.add_argument("--derivation-command", required=True,
                    help="the exact command that recomputes it, argv included; its first token "
                         "must be the generator's registered path")
    ap.add_argument("--note", required=True,
                    help="why the absence is a decision rather than an omission")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate and print the before/after, write nothing")
    a = ap.parse_args(argv)

    from seldon_artifacts import live_artifact

    before = node_properties(a.data_file)
    if before.get("artifact_type") != "DataFile":
        raise SystemExit(f"FATAL: {a.data_file!r} is a {before.get('artifact_type')}, not a "
                         f"DataFile; only a data file can be ephemeral")

    path = before.get("path")
    if not path:
        raise SystemExit(f"FATAL: DataFile {a.data_file!r} declares no path; there is nothing "
                         f"to say is absent")
    if (REPO / path).exists():
        raise SystemExit(
            f"FATAL: the repository HOLDS {path}. A file that exists is materialized, and "
            f"marking it `{MATERIALIZED}: false` would be a false statement about the tree. "
            f"Nothing written.")
    if not (REPO / a.derivable_from).exists():
        raise SystemExit(
            f"FATAL: the repository does not hold {a.derivable_from}, so this DataFile would "
            f"be derivable from nothing. The point of the mark is that the value is still "
            f"reachable; an unreachable source is a dead end with extra words. Nothing written.")

    gen = node_properties(a.generator)
    if gen.get("artifact_type") != "Script":
        raise SystemExit(f"FATAL: generator {a.generator!r} is a {gen.get('artifact_type')}, "
                         f"not a Script")
    first = shlex.split(a.derivation_command)[0]
    if first != gen.get("path"):
        raise SystemExit(
            f"FATAL: the derivation command runs {first!r} and the generator {a.generator!r} is "
            f"registered at {gen.get('path')!r}. The command and the GENERATED_BY edge have to "
            f"name one script or the node describes two different derivations.")

    props = {MATERIALIZED: False, "derivable_from": a.derivable_from,
             "derivation_command": a.derivation_command, "derivation_note": a.note}

    if a.dry_run:
        print(json.dumps({"dry_run": True, "before": before, "would_set": props,
                          "would_link": f"{a.data_file} -GENERATED_BY-> {a.generator}"},
                         indent=1, default=str))
        return 0

    from seldon.core.artifacts import update_artifact
    driver, db = _driver()
    try:
        update_artifact(project_dir=REPO, driver=driver, database=db,
                        artifact_id=before["artifact_id"], properties=props,
                        actor="cc", authority="accepted")
    finally:
        driver.close()

    link(before["artifact_id"], "generated_by", gen["artifact_id"])

    after = node_properties(a.data_file)
    for k, v in props.items():
        if after.get(k) != v:
            raise SystemExit(f"FATAL: wrote {k}={v!r} and the node reads {after.get(k)!r}")
    if not any(e.startswith("GENERATED_BY") for e in after["_edges"]):
        raise SystemExit(f"FATAL: the GENERATED_BY edge is not on the node after linking: "
                         f"{after['_edges']}")
    print(json.dumps({"task": TASK, "data_file": a.data_file, "before": before,
                      "after": after}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
