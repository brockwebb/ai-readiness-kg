#!/usr/bin/env python3
"""Minimal events→Neo4j projection (task 2026-07-05_airkg_bulk_extraction_v1 Stage 5).

The S1 spike finding made explicit: this repo had ZERO projection code — the KG
existed only as events. This is the minimal disposable projection needed to run
the pre-registered health checks. Reset-and-replay (fss pattern): every build
deletes ONLY the KG-schema labels and replays all event shards. Seldon's
artifact projection (:Artifact, :_SeldonMeta) in the same database is never
touched.

Target database: `seldon-ai-readiness-kg` — the hive's declared KG database per
repo convention (seldon.yaml::neo4j.database, federation registry). KG content
coexists with Seldon's artifact graph under disjoint labels.

Rel types come ONLY from the schema.yaml edge_types whitelist — an edge event
with an unknown type is skipped and counted (never string-interpolated into
Cypher from payload text).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402
from kg import eventlog  # noqa: E402

PROTECTED_DBS = ("wintermute-intake", "fss-policy-kg", "neo4j", "system")


def _load_schema() -> dict:
    return yaml.safe_load((REPO / "kg" / "schema.yaml").read_text(encoding="utf-8"))


def _neo4j_creds() -> tuple[str, str, str]:
    """URI, user, password from env; fallback names parsed from ~/.wintermute/.env
    (values never printed)."""
    env = dict(os.environ)
    if not (env.get("NEO4J_USERNAME") or env.get("NEO4J_USER")):
        wm_env = Path.home() / ".wintermute" / ".env"
        if wm_env.is_file():
            for line in wm_env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    uri = env.get("NEO4J_URI", "bolt://localhost:7687")
    user = env.get("NEO4J_USERNAME") or env.get("NEO4J_USER")
    pw = env.get("NEO4J_PASSWORD") or env.get("NEO4J_PASS")
    if not (user and pw):
        raise SystemExit("FATAL: no Neo4j credentials in env or ~/.wintermute/.env")
    return uri, user, pw


def _database() -> str:
    seldon_cfg = yaml.safe_load((REPO / "seldon.yaml").read_text(encoding="utf-8"))
    db = seldon_cfg["neo4j"]["database"]
    if db in PROTECTED_DBS:
        raise SystemExit(f"FATAL: refusing protected database {db!r}")
    return db


def _scalar_props(item: dict) -> dict:
    """Flatten an asserted item to Neo4j-safe props (scalars + string lists)."""
    out = {}
    for k, v in (item or {}).items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list) and all(isinstance(x, (str, int, float)) for x in v):
            out[k] = v
        else:
            out[k] = json.dumps(v, ensure_ascii=False)
    return out


def build(session, kg_labels: list[str], edge_whitelist: set[str]) -> dict:
    counts = {"nodes": 0, "edges": 0, "documents": 0,
              "skipped_unknown_edge_type": 0}
    # reset ONLY KG labels
    label_pred = " OR ".join(f"n:{lbl}" for lbl in kg_labels)
    session.run(f"MATCH (n) WHERE {label_pred} DETACH DELETE n")

    for ev in eventlog.replay():
        et = ev.get("event_type")
        if et == "manifest_add":
            p = ev["payload"]
            session.run(
                "MERGE (d:Document {id: $id}) SET d.doc_id = $id, d.title = $title, "
                "d.source_type = $st, d.pub_date = $pd, d.primary_url = $url, "
                "d.content_hash = $ch, d.prov_manifest_event = $ev",
                id=p["doc_id"], title=p.get("title"), st=p.get("source_type"),
                pd=p.get("pub_date"), url=p.get("primary_url"),
                ch=p.get("content_hash"), ev=ev.get("event_id"))
            counts["documents"] += 1
        elif et == "node_asserted":
            p = ev["payload"]
            label = p.get("type")
            if label not in kg_labels:
                continue
            prov = ev.get("provenance", {})
            props = _scalar_props(p.get("item", {}))
            props.update({
                "prov_model_id": prov.get("model_id"),
                "prov_prompt_version": prov.get("prompt_version"),
                "prov_schema_version": prov.get("schema_version"),
                "prov_corpus_epoch": prov.get("corpus_epoch"),
                "prov_source_sha256": prov.get("source_sha256"),
                "prov_extraction_event_id": prov.get("extraction_event_id"),
                "prov_wasDerivedFrom": ev.get("doc_id"),
            })
            session.run(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                id=p["id"], props=props)
            counts["nodes"] += 1
        elif et in ("edge_asserted", "curated_promotion"):
            p = ev["payload"] if et == "edge_asserted" else ev
            rel = p.get("type") if et == "edge_asserted" else p.get("edge")
            if rel not in edge_whitelist:
                counts["skipped_unknown_edge_type"] += 1
                continue
            prov = (p.get("provenance") or ev.get("provenance") or {})
            session.run(
                f"MERGE (a {{id: $from_id}}) MERGE (b {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel.upper()}]->(b) "
                "SET r.prov_method = $method, r.prov_doc = $doc, "
                "r.grounding_span = $span",
                from_id=p["from_id"], to_id=p["to_id"],
                method=prov.get("method") or prov.get("model_id") or "asserted",
                doc=ev.get("doc_id"), span=(p.get("item") or {}).get(
                    "grounding_span") or p.get("grounding_span"))
            counts["edges"] += 1
    return counts


def fingerprint(session, kg_labels: list[str]) -> dict:
    """Deterministic shape summary for the drift check."""
    fp = {}
    for lbl in kg_labels:
        fp[f"n:{lbl}"] = session.run(
            f"MATCH (n:{lbl}) RETURN count(n) AS c").single()["c"]
    rels = session.run(
        "MATCH ()-[r]->() WHERE r.prov_doc IS NOT NULL OR r.prov_method IS NOT NULL "
        "RETURN type(r) AS t, count(r) AS c ORDER BY t")
    for rec in rels:
        fp[f"r:{rec['t']}"] = rec["c"]
    return fp


def main() -> int:
    schema = _load_schema()
    kg_labels = list(schema["node_types"])
    edge_whitelist = set(schema["edge_types"])
    uri, user, pw = _neo4j_creds()
    db = _database()

    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    with driver.session(database=db) as session:
        counts = build(session, kg_labels, edge_whitelist)
        fp = fingerprint(session, kg_labels)
    driver.close()
    print(json.dumps({"database": db, "counts": counts, "fingerprint": fp}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
