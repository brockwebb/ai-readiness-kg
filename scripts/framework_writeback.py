#!/usr/bin/env python3
"""The one place a write-back to the framework of record goes through. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_hygiene.md` §3, last sentence: *every write-back from now on
regenerates `counts`, and that lives in the shared helper, not in three scripts.* Before this
module there were four writers (`framework_writeback_rules`, `_measured`, `_decisions`,
`add_candidate_indicator`), each recomputing the handful of counters it happened to touch, and
the one nobody recomputed was the one that drifted — which is the defect DD-040 names and
`framework_writeback_rules`'s own docstring records having hit once already.

**What `recount` does NOT do is change any denominator.** The task file that ordered this work
recorded a premise that `counts` disagrees with the file — `constructs: 47, indicators: 48`
against 48 and 49 nodes. It does not. Those two keys are CANDIDATE-EXCLUDED by DD-054 (the
framework does not adopt what the instrument found about itself without the operator), which
`add_candidate_indicator.py` applies and comments in place. Recounting them as totals would
adopt A12 into the framework's headline numbers as a side effect of a hygiene pass — exactly
the silent adoption DD-054 forbids. So each key below states its denominator, and `recount`
reproduces every value the file already holds.

The split between the two groups is not stylistic:

* **candidate-excluded** — counts of what the FRAMEWORK holds. A candidate is recorded and
  reported, and it is not part of the framework until the operator adopts it (DD-054).
* **candidate-inclusive** — counts of what the INSTRUMENT holds. A `MeasurementSpec` exists
  whether or not its indicator has been adopted, and `tests/test_framework_graph.py` asserts
  `measurement_specs == len(specs)` over all of them.

**This module is the ONLY code that writes `framework/ai_readiness_framework.json`**
(`cc_tasks/2026-09-11_framework_single_writer.md` decision 1;
`tests/test_framework_single_writer.py` asserts it statically over every module in the repo).
A generator (`build_framework_graph.py`, `build_measurement_specs.py`) produces its output in
memory and hands it to `save`, which does three things no caller may skip:

* **refuses a write that removes anything** — a node, an edge, or a key of `counts` present in
  the file on disk — unless the caller passes `force=True` with a `reason`, in which case the
  reason is on the event (decision 2). The refusal names what would be dropped and how many.
  This is the guard for the incident `2026-09-11_a3_a10_sources_RESULT.md` §7 records:
  regenerating from the skeleton silently deleted 22 `MEASURED_BY` edges and undid DD-054;
* **puts the delta on the event** — nodes and edges added, removed and changed, with before
  and after values, and every `counts` key that moved — so a replay from the ledger is possible
  rather than only a sha256 to compare against (decision 4);
* **writes nothing and logs nothing when the bytes would be identical** — a `framework_writeback`
  event that records no change is noise on the provenance trail, and the sha256 the previous
  event carries already names the revision.

`rules_built` is in neither group and is deliberately absent from `recount`: it is a fact about
`assessment/harness/scan/rules`, not about the JSON, and five spec `rule_id`s name rules that
were never built (`RULE-C4-auto-v0`, `RULE-F2-v0`, `RULE-F3-v0`, `RULE-G1-O-v0`, `RULE-G3-v0`),
so deriving it from the specs would overcount by five. `framework_writeback_rules` owns it;
`check` returns it separately so a gate can still cover it rather than pass it by.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
#: A TAGGED shard: `kg/eventlog.replay()` skips tagged shards, and it must, because the
#: framework layer is projected from the JSON (`scripts/load_framework_graph.py`), never from
#: the log. These events are the provenance trail of who changed the record of record and
#: when — not a projection source. Mixing them into the untagged shards would put events into
#: the graph replay that no projector knows how to read.
BATCH = 33
TAG = "framework"
EVENT = "framework_writeback"

#: The DD-054 rule, on the face of the record, so a reader of the JSON never has to find this
#: module to know what a number in `counts` is a count OF.
COUNTS_BASIS = (
    "Node and edge counts of the framework itself (criteria, constructs, indicators, "
    "evidenced_by, evidenced_by_internal, gaps, indicators_measured) EXCLUDE candidate "
    "indicators and their constructs (DD-054: the framework does not adopt what the "
    "instrument found about itself without the operator); candidate_indicators counts them. "
    "Counts of the instrument (measurement_specs, collectors_none_known, "
    "specs_with_recorded_decision) include every spec, adopted or not. rules_built is a fact "
    "about assessment/harness/scan/rules, not about this file. Regenerated by "
    "scripts/framework_writeback.py::recount on every write-back."
)


def _candidate_ids(g: dict) -> set:
    """Nodes DD-054 holds out of the framework: candidate indicators and their constructs."""
    return {n["id"] for n in g["nodes"] if n["properties"].get("status") == "candidate"}


def recount(g: dict) -> dict:
    """Every `counts` key derivable from `nodes`/`edges`, recomputed. See the module docstring
    for why two different denominators are correct rather than a bug."""
    nodes, edges = g["nodes"], g["edges"]
    cand = _candidate_ids(g)

    def n_label(label: str, exclude_candidates: bool) -> int:
        return sum(1 for n in nodes if label in n["labels"]
                   and not (exclude_candidates and n["id"] in cand))

    def n_edge(etype: str) -> int:
        return sum(1 for e in edges if e["type"] == etype and e["from"] not in cand)

    specs = [n["properties"] for n in nodes if "MeasurementSpec" in n["labels"]]
    inds = [n for n in nodes if "AssessmentIndicator" in n["labels"]]
    return {
        # ---- the framework's own content: candidates excluded (DD-054) ----
        "criteria": n_label("AssessmentCriterion", True),
        "constructs": n_label("AssessmentConstruct", True),
        "indicators": n_label("AssessmentIndicator", True),
        "evidenced_by": n_edge("EVIDENCED_BY"),
        "evidenced_by_internal": n_edge("EVIDENCED_BY_INTERNAL"),
        "gaps": sum(1 for n in nodes if n["properties"].get("gap") and n["id"] not in cand),
        "indicators_measured": sum(
            1 for n in inds if n["properties"].get("measurement_status") == "measured"
            and n["id"] not in cand),
        # ---- the instrument: every spec, adopted or not ----
        "measurement_specs": len(specs),
        "collectors_none_known": sum(1 for s in specs if s.get("collector") == "none_known"),
        "specs_with_recorded_decision": sum(1 for s in specs if s.get("decision")),
        # ---- the candidates themselves ----
        "candidate_indicators": len(
            [n for n in inds if n["properties"].get("status") == "candidate"]),
    }


def apply_counts(g: dict) -> dict:
    """Merge `recount` over `g["counts"]` and stamp `counts_basis`. Returns the keys that
    MOVED, so a caller reports drift rather than swallowing it — a counter silently corrected
    is a counter nobody learns was wrong."""
    fresh = recount(g)
    before = dict(g.get("counts") or {})
    moved = {k: [before.get(k), v] for k, v in fresh.items() if before.get(k) != v}
    g.setdefault("counts", {}).update(fresh)
    g["counts_basis"] = COUNTS_BASIS
    return moved


def check(g: dict, built_rule_ids: set | None = None) -> dict:
    """Read-only self-consistency report. `{counts_drift, internal_ref_key_shapes,
    rules_built_expected}`; every value empty or matching means the file agrees with itself."""
    out = {"counts_drift": {k: [(g.get("counts") or {}).get(k), v]
                            for k, v in recount(g).items()
                            if (g.get("counts") or {}).get(k) != v}}
    shapes = sorted({tuple(sorted((e.get("properties") or {}).keys()))
                     for e in g["edges"] if e["type"] == "EVIDENCED_BY_INTERNAL"})
    prefixed = all(str(e["to"]).startswith("internal:") for e in g["edges"]
                   if e["type"] == "EVIDENCED_BY_INTERNAL")
    out["internal_ref_key_shapes"] = [list(s) for s in shapes]
    out["internal_refs_all_prefixed"] = prefixed
    if built_rule_ids is not None:
        out["rules_built_expected"] = len(built_rule_ids)
        out["rules_built_recorded"] = (g.get("counts") or {}).get("rules_built")
    return out


class RefusedWrite(RuntimeError):
    """`save` refused: the write would drop something the file on disk holds, and the caller
    did not say so on purpose (`force=True` with a `reason`)."""


#: Keys of a node/edge entry that identify it; everything else is content the delta compares.
_NODE_KEY = "id"


def _edge_key(e: dict) -> tuple:
    return (e["from"], e["type"], e["to"])


def _node_label(n: dict) -> str:
    return (n.get("labels") or ["?"])[0]


def delta(before: dict | None, after: dict) -> dict:
    """What `after` changes relative to `before`, by identity: nodes by `id`, edges by
    `(from, type, to)`, `counts` by key.

    Added and removed entries are carried WHOLE (a removed node is recoverable from the event);
    a changed entry carries only the keys that differ, as `{key: [before, after]}`. A `before`
    of `None` (no file on disk yet) is an all-added delta.
    """
    b_nodes = {n[_NODE_KEY]: n for n in (before or {}).get("nodes", [])}
    a_nodes = {n[_NODE_KEY]: n for n in after.get("nodes", [])}
    b_edges = {_edge_key(e): e for e in (before or {}).get("edges", [])}
    a_edges = {_edge_key(e): e for e in after.get("edges", [])}
    b_counts = dict((before or {}).get("counts") or {})
    a_counts = dict(after.get("counts") or {})

    def changed_keys(x: dict, y: dict) -> dict:
        return {k: [x.get(k), y.get(k)] for k in sorted(set(x) | set(y)) if x.get(k) != y.get(k)}

    nodes_changed = []
    for nid in a_nodes:
        if nid in b_nodes and a_nodes[nid] != b_nodes[nid]:
            bp, ap_ = b_nodes[nid].get("properties") or {}, a_nodes[nid].get("properties") or {}
            entry = {"id": nid, "properties": changed_keys(bp, ap_)}
            if b_nodes[nid].get("labels") != a_nodes[nid].get("labels"):
                entry["labels"] = [b_nodes[nid].get("labels"), a_nodes[nid].get("labels")]
            nodes_changed.append(entry)
    edges_changed = []
    for k in a_edges:
        if k in b_edges and a_edges[k] != b_edges[k]:
            edges_changed.append({"from": k[0], "type": k[1], "to": k[2],
                                  "properties": changed_keys(b_edges[k].get("properties") or {},
                                                             a_edges[k].get("properties") or {})})
    return {
        "nodes_added": [a_nodes[k] for k in a_nodes if k not in b_nodes],
        "nodes_removed": [b_nodes[k] for k in b_nodes if k not in a_nodes],
        "nodes_changed": nodes_changed,
        "edges_added": [a_edges[k] for k in a_edges if k not in b_edges],
        "edges_removed": [b_edges[k] for k in b_edges if k not in a_edges],
        "edges_changed": edges_changed,
        "counts_keys_dropped": sorted(k for k in b_counts if k not in a_counts),
        "counts_moved": changed_keys(b_counts, a_counts),
    }


def summarize_delta(d: dict) -> dict:
    """Counts per kind, for a log line and for the refusal message."""
    from collections import Counter
    return {
        "nodes_added": dict(Counter(_node_label(n) for n in d["nodes_added"])),
        "nodes_removed": dict(Counter(_node_label(n) for n in d["nodes_removed"])),
        "nodes_changed": len(d["nodes_changed"]),
        "edges_added": dict(Counter(e["type"] for e in d["edges_added"])),
        "edges_removed": dict(Counter(e["type"] for e in d["edges_removed"])),
        "edges_changed": len(d["edges_changed"]),
        "counts_keys_dropped": list(d["counts_keys_dropped"]),
        "counts_moved": d["counts_moved"],
    }


def drops(d: dict) -> list:
    """Human-readable lines for everything the delta REMOVES; empty means nothing is dropped."""
    out = []
    if d["nodes_removed"]:
        by = summarize_delta(d)["nodes_removed"]
        ids = ", ".join(n["id"] for n in d["nodes_removed"][:8])
        more = "" if len(d["nodes_removed"]) <= 8 else f", ... (+{len(d['nodes_removed']) - 8})"
        out.append(f"{len(d['nodes_removed'])} node(s) {by}: {ids}{more}")
    if d["edges_removed"]:
        by = summarize_delta(d)["edges_removed"]
        ids = ", ".join(f"{e['from']}-[{e['type']}]->{e['to']}" for e in d["edges_removed"][:8])
        more = "" if len(d["edges_removed"]) <= 8 else f", ... (+{len(d['edges_removed']) - 8})"
        out.append(f"{len(d['edges_removed'])} edge(s) {by}: {ids}{more}")
    if d["counts_keys_dropped"]:
        out.append(f"{len(d['counts_keys_dropped'])} counts key(s): "
                   f"{', '.join(d['counts_keys_dropped'])}")
    return out


def serialize(g: dict) -> str:
    """The one serialisation of the record. Byte identity between two revisions means
    `serialize(a) == serialize(b)`, and nothing else writes these bytes."""
    return json.dumps(g, indent=1, ensure_ascii=False) + "\n"


def load(path: Path | None = None) -> dict | None:
    """The record as it is on disk, or None when there is no file yet."""
    path = path or FRAMEWORK
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def add_force_args(ap) -> None:
    """The two flags every writer's CLI exposes, so a deliberate drop is spelled the same way
    everywhere: `--force --reason "<why>"`. Pass the parsed namespace to `force_kwargs`."""
    ap.add_argument("--force", action="store_true",
                    help="allow this write to REMOVE nodes, edges or counts keys the record "
                         "holds; requires --reason, which lands on the framework_writeback event")
    ap.add_argument("--reason", default=None, metavar="TEXT",
                    help="why the removal is right; recorded on the event (with --force)")


def force_kwargs(a) -> dict:
    return {"force": bool(getattr(a, "force", False)), "reason": getattr(a, "reason", None)}


def save(g: dict, script: str, task: str, changes: dict, dry_run: bool = False,
         path: Path | None = None, force: bool = False, reason: str | None = None) -> dict:
    """Write the framework JSON and append the `framework_writeback` event that says who did.

    The event carries the sha256 of the bytes written AND the delta against the file that was
    on disk (`delta`), so "which revision of the record does this projection correspond to"
    and "what did this write-back change" are both answerable from the log. A write that would
    REMOVE a node, an edge, or a `counts` key is refused (`RefusedWrite`) unless `force=True`
    and a non-empty `reason` is given; the reason lands on the event under `forced`. A dry run
    writes neither, but still computes and returns the delta and the refusal. A write whose
    bytes equal the file's is not written and not logged (`unchanged: True`).
    """
    path = path or FRAMEWORK
    before = load(path)
    moved = apply_counts(g)
    body = serialize(g)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    d = delta(before, g)
    dropped = drops(d)
    record = {"event_type": EVENT, "script": script, "task": task,
              "framework_path": str(path.relative_to(REPO)) if path.is_relative_to(REPO)
              else str(path),
              "framework_sha256": digest, "changes": changes, "counts_moved": moved,
              "counts": g["counts"], "delta": d, "delta_summary": summarize_delta(d)}
    if dropped:
        if not force:
            raise RefusedWrite(
                "REFUSED: this write would drop what the record on disk holds, and nothing "
                "said so on purpose. Would drop: " + "; ".join(dropped) + ". Nothing was "
                "written. Pass force=True (CLI: --force --reason \"<why>\") to drop them "
                "deliberately; the reason is recorded on the framework_writeback event.")
        if not (reason and reason.strip()):
            raise RefusedWrite("REFUSED: --force without --reason. A deliberate drop is "
                               "recorded with why it is right, or it is not deliberate. "
                               "Would drop: " + "; ".join(dropped) + ". Nothing was written.")
        record["forced"] = {"reason": reason.strip(), "dropped": dropped}
    if before is not None and body == path.read_text(encoding="utf-8"):
        return {**record, "written": False, "unchanged": True}
    if dry_run:
        return {**record, "written": False}
    path.write_text(body, encoding="utf-8")
    from kg import eventlog
    event_id = eventlog.append(record, batch=BATCH, tag=TAG)
    return {**record, "written": True, "event_id": event_id,
            "shard": f"events/batch-{BATCH:03d}_{TAG}.jsonl"}
