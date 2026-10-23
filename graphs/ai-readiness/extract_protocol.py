"""The ai-readiness graph's extraction protocol for the kit's stage 10a (squiddy SQ-021; DN-049 R-211).

`engine.extract.protocol` names this file; `squiddy.extract.extract_document` calls `plan` and `rows` (the contract is
in `squiddy.extract.graph_protocol`). It runs the instrument SQ-021 piloted, on the tier the pilot adopted:

- THE TIER. A document's class is its `doc_type` (the dixie record's `identity.doc_type`, else the entry's own
  `doc_type`). Its tier is `extract/control.yaml` `tiers.<class>`, written by `tools/sq021_pilot.py adopt` from the
  pilot gate. A class with no tier, or a closed one, takes no extraction: the plan's role is None with the reason, and
  the stage records it. The role is a seldon registry role, resolved by the kit's client through the lock (MODEL-001).
- THE UNITS AND PROMPTS. ai-readiness-kg's chunk protocol (`pilot_arms.profile`, bulk_v038), cut and rendered by
  `airkg_chunk_worker.py` in that repository's interpreter, exactly as the pilot's units were.
- THE ROWS. Each answer parsed by the same worker and each item located by the same function the pilot measured with
  (squiddy `tools/sq021_pilot.ground_result`, which calls `tools/l002_adopt.ground`, the rule every item of this graph
  was admitted by), then the adopter's endpoint rules (squiddy `tools/l002_adopt.adopt_airkg`): an edge is kept only
  when each endpoint is an item kept here or an in-graph document, and its endpoint key carries one label. Items are
  merged per key across chunks the way ai-readiness-kg's projection merges them (`SET n += $props`), the first
  located span kept. A row is the shape the emitter's `emit_extraction` reads (`claim`, `span`, `airkg`), its
  `airkg.model_id` the model that answered, so every item carries `prov_extractor` (R-211).

Imports squiddy's `tools/` from the checkout of the kit that is running (the parent of the `squiddy` package), so the
rows are cut by the code the pilot was measured with, never a copy of it.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

#: rows that are not items, kept in the evidence file under these statuses
FAILED_CALL, FAILED_PARSE = "task_failed", "unparseable"


def _kit_tools():
    import squiddy
    root = str(Path(squiddy.__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    from tools import sq021_pilot as sp
    return sp


def _control(graph) -> dict:
    from squiddy import extract_daemon as xd
    return yaml.safe_load(xd.dirs(graph)["control"].read_text(encoding="utf-8")) or {}


def doc_class(entry: dict) -> str | None:
    raw = entry.get("dixie_record")
    ident = (json.loads(raw) if raw else {}).get("identity") or {}
    return ident.get("doc_type") or entry.get("doc_type")


def _path(graph, entry: dict) -> Path:
    lp = entry.get("local_path")
    if not lp:
        raise SystemExit(f"FATAL: {entry['id']} holds no text (`local_path`); nothing to extract")
    p = Path(lp)
    if not p.is_absolute():
        p = graph.root / p
    if not p.is_file():
        raise SystemExit(f"FATAL: {entry['id']}: {p} does not exist")
    return p


def plan(graph, entry: dict) -> dict:
    sp = _kit_tools()
    control = _control(graph)
    cfg = control.get("pilot_arms") or {}
    tiers = control.get("tiers") or {}
    cls = doc_class(entry)
    tier = tiers.get(cls) if cls else None
    if tier is None:
        return {"role": None, "units": [], "why": f"document class {cls!r} has no extraction tier "
                                                  f"(extract/control.yaml tiers: {sorted(tiers)})"}
    if tier.get("closed"):
        return {"role": None, "units": [], "why": f"document class {cls!r} is closed: {tier.get('why')}"}
    if tier.get("protocol") != cfg.get("profile"):
        raise SystemExit(f"FATAL: tier {cls} names protocol {tier.get('protocol')!r} and the piloted protocol is "
                         f"{cfg.get('profile')!r}")
    path = _path(graph, entry)
    got = sp.worker(graph, cfg, "units", {"doc_ids": [entry["id"]], "paths": {entry["id"]: str(path)}})
    doc = got["docs"][entry["id"]]
    units = [{"id": c["chunk_id"], "prompt": c["prompt"], "prompt_sha256": c["prompt_sha256"], "start": c["start"],
              "end": c["end"], "overlap_start": c["overlap_start"], "chars": c["end"] - c["start"],
              "oversize": c["oversize"]} for c in doc["chunks"]]
    t = dict(cfg.get("transport") or {})
    t["in_flight"] = cfg.get("in_flight")
    # the spend node the piloted instrument was metered under (tools/sq021_pilot.py), so the governor prices a document
    # from the pilot's measured calls on the same model and transport (R-177) rather than cutting it to a pilot
    return {"role": tier["role"], "units": units, "transport": t, "class": cls, "path": str(path),
            "spend_node": "sq021_pilot_extract",
            "doc": {k: doc[k] for k in ("source_sha256", "text_sha256", "chars")},
            "instrument": {"protocol": cfg.get("profile"), "prompt_version": got["prompt_version"],
                           "schema_version": got["schema_version"], "template_sha256": got["template_sha256"],
                           "class": cls, "tier_arm": tier.get("arm"), "role": tier["role"],
                           "tier_evidence": tier.get("evidence"), "tier_decided_at": tier.get("decided_at")}}


def _merge(props: dict, new: dict) -> None:
    """`SET n += $props`: each key set, a null removing it (ai-readiness-kg's projection; tools/l002_adopt._merge)."""
    for k, v in new.items():
        if v is None:
            props.pop(k, None)
        else:
            props[k] = v


def rows(graph, entry: dict, plan: dict, results: list[dict]) -> list[dict]:
    sp = _kit_tools()
    from squiddy import manifest as mf
    cfg = _control(graph).get("pilot_arms") or {}
    span_classes = set((cfg.get("lines") or {}).get("span_classes") or [])
    doc_id = entry["id"]
    raw, plain = sp.doc_texts(graph, plan["path"], doc_id)
    if hashlib.sha256(raw.encode("utf-8")).hexdigest() != plan["doc"]["text_sha256"]:
        raise SystemExit(f"FATAL: {doc_id}: the text read now is not the text the plan cut its chunks from")
    resp = [{"chunk_id": r["unit"]["id"], "content": r["content"]} for r in results if r["status"] == "ok"]
    parsed = {x["chunk_id"]: x for x in sp.worker(graph, cfg, "parse", {"doc_id": doc_id, "responses": resp,
                                                                      "paths": {doc_id: plan["path"]}})["results"]} \
        if resp else {}
    inst = plan["instrument"]
    out_failed, nodes, edges = [], {}, {}
    for r in results:
        u = r["unit"]
        if r["status"] != "ok":
            out_failed.append({"status": r["status"], "chunk_id": u["id"], "error": r.get("error")})
            continue
        res = parsed[u["id"]]
        g = sp.ground_result(res, u, raw, plain, span_classes)
        if res["status"] != "parsed":
            out_failed.append({"status": FAILED_PARSE if res["status"] in ("unparseable", "empty") else res["status"],
                               "chunk_id": u["id"], "error": res.get("detail")})
            continue
        stamp = {"model_id": r.get("resolved_model"), "prompt_version": inst["prompt_version"],
                 "schema_version": inst["schema_version"], "corpus_epoch": f"squiddy-sq021-tier:{inst['class']}",
                 "extraction_event_id": hashlib.sha256(f"{doc_id}|{u['id']}|{u['prompt_sha256']}|"
                                                       f"{r.get('resolved_model')}".encode()).hexdigest()[:32],
                 "source_sha256": plan["doc"]["source_sha256"], "chunk_id": u["id"],
                 "timestamp": datetime.now(timezone.utc).isoformat(), "batch": None, "event_id": None,
                 "receipt": r.get("receipt"), "role": inst["role"], "tier_evidence": inst["tier_evidence"]}
        for x in g["ungrounded"]:
            out_failed.append({"status": "ungrounded", "chunk_id": u["id"], "why": x.get("why"),
                               "detail": x.get("detail"), "key": x.get("key")})
        for row in g["grounded"]:
            c = row["claim"]
            airkg = {**stamp, "source_changed": False, "span_ambiguous": row["span_ambiguous"],
                     "grounded_in": row["grounded_in"], **({} if row["span_raw_equal"] else {"span_raw_equal": False})}
            if c["kind"] == "node":
                k = (c["key"], c["claim_kind"])
                if k in nodes:
                    _merge(nodes[k]["claim"]["props"], c["props"])
                    continue
                nodes[k] = {"status": "grounded", "text": row["text"], "span": row["span"], "airkg": airkg,
                            "claim": {**c, "props": dict(c["props"])}}
            else:
                k = (c["subject"], c["claim_kind"], c["object"])
                if k in edges:
                    _merge(edges[k]["claim"]["props"], c["props"])
                    continue
                edges[k] = {"status": "grounded", "text": row["text"], "span": row["span"], "airkg": airkg,
                            "claim": {**c, "props": dict(c["props"])}}
    # the adopter's endpoint rules (tools/l002_adopt.adopt_airkg)
    _s, _m, docs = mf.load_manifest(graph.manifest_path)
    in_graph = {d["id"] for d in docs if d.get("stage") == graph.engine["manifest"]["in_graph_stage"]} | {doc_id}
    labels: dict[str, set] = {}
    for key, label in nodes:
        labels.setdefault(key, set()).add(label)
    kept_edges = []
    for (s, rel, o), row in edges.items():
        ends = [s, o]
        if not all(x in labels or x in in_graph for x in ends):
            out_failed.append({"status": "kept_out", "why": "endpoint_not_in_graph", "edge": [s, rel, o]})
            continue
        if any(len(labels.get(x, set()) | ({"Document"} if x in in_graph else set())) != 1 for x in ends):
            out_failed.append({"status": "kept_out", "why": "endpoint_label_ambiguous", "edge": [s, rel, o]})
            continue
        kept_edges.append(row)
    return list(nodes.values()) + kept_edges + out_failed
