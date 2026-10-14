#!/usr/bin/env python3
"""Profile one full projection: queries, transactions and time per phase, split into server
work and driver round trip (task `cc_tasks/2026-10-12_projection_replay_measured_then_batched.md`
decision 1).

Runs `scripts/build_projection.py::main` unchanged, with the Neo4j driver's `Session.run` and
`Transaction.run` wrapped at class level, so the KG replay, the scan layer (which opens its own
driver through seldon) and the framework layer are all measured by the same instrument. Each
wrapped call buffers its records, which is what the callers do anyway (`.single()`, iteration,
or the next `run` on the session), so the measured wall time is the whole call.

Per query it records:
  * wall      — `run()` entry to records buffered, client side;
  * server    — `t_first + t_last` from the result metadata: Neo4j's own planning+execution
                and streaming time in ms (the Bolt `result_available_after` /
                `result_consumed_after` pair);
  * round trip = wall - server: driver, network and Bolt overhead, which is the cost a
    batching change would remove.

An auto-commit `Session.run` is one transaction, so transactions per phase = auto-commit calls
+ explicit transactions begun. The template key is the query text with whitespace collapsed,
truncated; queries are written with parameters here, so the template set is small.

`--sweep` instead measures commit cost by batch size and index, on scratch nodes (`sweep()`).

Writes `logs/projection_profile_<stamp>.json` after every phase change and at the end; a
killed profile keeps the phases it finished. The projection's own progress log is untouched.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import build_projection as bp  # noqa: E402

#: Characters of collapsed query text kept as the template key: long enough to tell every
#: query in build_projection / publish / load_framework_graph apart, short enough to read.
TEMPLATE_CHARS = 110

_state = {"phase": "pre"}
_stats: dict = collections.defaultdict(lambda: {
    "queries": 0, "autocommit_tx": 0, "explicit_tx": 0, "wall_s": 0.0, "server_s": 0.0,
    "templates": collections.defaultdict(lambda: {"n": 0, "wall_s": 0.0, "server_s": 0.0})})


def _template(q) -> str:
    text = q if isinstance(q, str) else getattr(q, "text", str(q))
    return re.sub(r"\s+", " ", text).strip()[:TEMPLATE_CHARS]


def _record(query, t0: float, res, autocommit: bool) -> None:
    wall = time.perf_counter() - t0
    md = getattr(res, "_metadata", {}) or {}
    server = ((md.get("t_first") or 0) + (md.get("t_last") or 0)) / 1000.0
    st = _stats[_state["phase"]]
    st["queries"] += 1
    st["autocommit_tx"] += 1 if autocommit else 0
    st["wall_s"] += wall
    st["server_s"] += server
    tp = st["templates"][_template(query)]
    tp["n"] += 1
    tp["wall_s"] += wall
    tp["server_s"] += server


def _install() -> None:
    from neo4j._sync.work.session import Session
    from neo4j._sync.work.transaction import TransactionBase
    s_run, t_run, s_begin = Session.run, TransactionBase.run, Session.begin_transaction

    def session_run(self, query, parameters=None, **kw):
        t0 = time.perf_counter()
        res = s_run(self, query, parameters, **kw)
        res._buffer_all()
        _record(query, t0, res, autocommit=True)
        return res

    def tx_run(self, query, parameters=None, **kw):
        t0 = time.perf_counter()
        res = t_run(self, query, parameters, **kw)
        res._buffer_all()
        _record(query, t0, res, autocommit=False)
        return res

    def begin(self, *a, **kw):
        _stats[_state["phase"]]["explicit_tx"] += 1
        return s_begin(self, *a, **kw)

    Session.run, TransactionBase.run, Session.begin_transaction = session_run, tx_run, begin


def _dump(path: Path, phase_wall: dict) -> None:
    out = {}
    for ph, st in _stats.items():
        tpls = sorted(st["templates"].items(), key=lambda kv: -kv[1]["wall_s"])
        out[ph] = {k: (round(v, 3) if isinstance(v, float) else v)
                   for k, v in st.items() if k != "templates"}
        out[ph]["phase_wall_s"] = round(phase_wall.get(ph, 0.0), 3)
        out[ph]["round_trip_s"] = round(st["wall_s"] - st["server_s"], 3)
        out[ph]["templates"] = [{"q": q, "n": t["n"], "wall_s": round(t["wall_s"], 3),
                                 "server_s": round(t["server_s"], 3),
                                 "ms_per_q": round(1000 * t["wall_s"] / t["n"], 3)}
                                for q, t in tpls]
    path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


#: Scratch label for `--sweep`; matches publish.py's `Scratch<word>_` convention, so no real
#: label can be hit, and it is DETACH DELETEd (and its index dropped) before the sweep returns.
SWEEP_LABEL = "ScratchProbe_Node"
#: Batch sizes from the task's own example (decision 2), plus 1 = today's auto-commit per row.
SWEEP_BATCHES = (1, 500, 2_000, 10_000)
#: Rows per sweep arm: 10,000 is the largest batch, so every arm writes the same rows.
SWEEP_ROWS = 10_000


def sweep() -> dict:
    """What batching and indexing are each worth, measured on scratch nodes: `SWEEP_ROWS`
    `MERGE (n:Label {key}) SET n.v` rows per arm, written at each batch size (`UNWIND $rows`
    in one explicit transaction per batch), with no index on `key` and then with one. The
    unindexed arms MERGE into a label that already holds the rows, so every row pays a label
    scan of `SWEEP_ROWS` nodes, about the size of the larger KG labels. Every arm writes NEW
    values (`v` is offset by the arm number): a SET to an unchanged value commits nothing to the
    transaction log, and a sweep that rewrote identical values measured no commit at all."""
    from neo4j import GraphDatabase
    uri, user, pw = bp._neo4j_creds()
    db = bp._database()
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    rows = [{"k": f"probe::{i}", "v": i} for i in range(SWEEP_ROWS)]
    q = f"UNWIND $rows AS r MERGE (n:{SWEEP_LABEL} {{key: r.k}}) SET n.v = r.v"
    out: dict = {"rows": SWEEP_ROWS, "arms": []}
    try:
        with driver.session(database=db) as s:
            s.run(f"MATCH (n:{SWEEP_LABEL}) DETACH DELETE n").consume()
            s.run(q, rows=rows).consume()                      # the label holds the rows
            for indexed in (False, True):
                if indexed:
                    s.run(f"CREATE INDEX scratch_probe_key IF NOT EXISTS "
                          f"FOR (n:{SWEEP_LABEL}) ON (n.key)").consume()
                    s.run("CALL db.awaitIndexes(300)").consume()
                for b in SWEEP_BATCHES:
                    arm_no = len(out["arms"]) + 1
                    rows = [{"k": r["k"], "v": arm_no * SWEEP_ROWS + i}
                            for i, r in enumerate(rows)]
                    t0 = time.perf_counter()
                    if b == 1:
                        for r in rows:
                            s.run(f"MERGE (n:{SWEEP_LABEL} {{key: $k}}) SET n.v = $v",
                                  k=r["k"], v=r["v"]).consume()
                    else:
                        for i in range(0, len(rows), b):
                            s.execute_write(lambda tx, chunk: tx.run(q, rows=chunk).consume(),
                                            rows[i:i + b])
                    secs = time.perf_counter() - t0
                    arm = {"indexed": indexed, "batch": b, "seconds": round(secs, 3),
                           "ms_per_row": round(1000 * secs / len(rows), 4)}
                    out["arms"].append(arm)
                    print(json.dumps(arm), flush=True)
    finally:
        with driver.session(database=db) as s:
            s.run("DROP INDEX scratch_probe_key IF EXISTS").consume()
            s.run(f"MATCH (n:{SWEEP_LABEL}) DETACH DELETE n").consume()
            left = s.run(f"MATCH (n:{SWEEP_LABEL}) RETURN count(n) AS c").single()["c"]
        driver.close()
    if left:
        raise SystemExit(f"FATAL: {left} {SWEEP_LABEL} nodes survived the sweep cleanup")
    out["cleanup_left"] = left
    return out


def main() -> int:
    if "--sweep" in sys.argv[1:]:
        res = sweep()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = bp.LOGS_DIR / f"projection_sweep_{stamp}.json"
        path.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print(f"sweep written: {path}", flush=True)
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = bp.LOGS_DIR / f"projection_profile_{stamp}.json"
    print(f"profile: {path}", flush=True)
    _install()
    phase_wall: dict = {}
    orig_phase, orig_finish = bp.Progress.phase, bp.Progress.finish

    def phase(self, name, *a, **kw):
        orig_phase(self, name, *a, **kw)
        for nm, secs in self.timings:
            phase_wall[nm] = secs
        _state["phase"] = name
        _dump(path, phase_wall)

    def finish(self, *a, **kw):
        table = orig_finish(self, *a, **kw)
        for nm, secs in self.timings:
            phase_wall[nm] = secs
        _state["phase"] = "post"
        _dump(path, phase_wall)
        return table

    bp.Progress.phase, bp.Progress.finish = phase, finish
    rc = bp.main([])
    _dump(path, phase_wall)
    print(f"profile written: {path}", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
