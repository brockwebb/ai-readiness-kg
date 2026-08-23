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


def read_overlays() -> tuple[set[tuple[str, str]], dict[str, str]]:
    """Two append-only overlays introduced by the 2026-08-14 bulk-v1 closeout.

    Neither mutates a prior event; both are resolved at READ time, so the log stays
    the truth and the projection stays its function.

      extraction_superseded  -> drop the node/edge events of a replaced extraction.
        Keyed on (doc_id, source_sha256), NOT doc_id alone: a doc_id-only rule would
        also drop the replacement, since both extractions carry the same doc_id.

      edge_endpoint_alias    -> rewrite a citation endpoint onto its canonical doc_id.
        Written only where the alias is a token-prefix of the canonical id (or differs
        by stopwords) AND every numeric identifier agrees. Similarity matching was
        rejected during the closeout: it mapped executive-order-14110 onto 13960,
        nist-cybersecurity-framework onto nist-ai-rmf, and cisco-2024 onto cisco-2025.
    """
    superseded: set[tuple[str, str]] = set()
    aliases: dict[str, str] = {}
    for ev in eventlog.replay():
        et = ev.get("event_type")
        if et == "extraction_superseded":
            superseded.add((ev["doc_id"], ev["superseded_source_sha256"]))
        elif et == "edge_endpoint_alias":
            aliases[ev["alias_id"]] = ev["canonical_id"]
    return superseded, aliases


# Events that are NOT part of the graph. TEVV re-extractions (task 2026-08-22_kernel_tevv
# Phase 2) are flagged `purpose: tevv_retest` on every event and live in a tagged shard;
# they measure stability and must never be projected — a retest that leaked into the
# graph would double every node of the retested docs.
NON_GRAPH_PURPOSES = {"tevv_retest", "probe"}   # probe = judge_label events (task 2026-08-22_faithfulness_probe)


def is_projectable(ev: dict) -> bool:
    """False for events flagged with a non-graph purpose (e.g. TEVV retests)."""
    return ev.get("purpose") not in NON_GRAPH_PURPOSES


# Document annotations (schema v0.3.1, task 2026-08-22_kernel_tevv): harness-set document
# properties written as `document_annotation` events. Only whitelisted properties project,
# so an arbitrary payload key can never become a Cypher property name.
ANNOTATABLE_DOCUMENT_PROPERTIES = {"is_platform_operator"}
# attribute_nulled overlays may clear only these (schema attributes the probe can class as
# filled_attribute); the property name is never taken from the payload unchecked.
NULLABLE_ATTRIBUTES = {"description", "steward", "owner", "year", "version", "operator",
                       "license", "url", "response_type", "method", "measurement_notes", "aliases",
                       "term"}   # term: Definition's span_entailable attribute (repair 2026-08-23)


def annotation_update(ev: dict) -> tuple[str, str, object] | None:
    """(doc_id, property, value) for a projectable document_annotation, else None."""
    if ev.get("event_type") != "document_annotation":
        return None
    prop = ev.get("property")
    if prop not in ANNOTATABLE_DOCUMENT_PROPERTIES or not ev.get("doc_id"):
        return None
    return ev["doc_id"], prop, ev.get("value")


def build(session, kg_labels: list[str], edge_whitelist: set[str]) -> dict:
    counts = {"nodes": 0, "edges": 0, "documents": 0, "annotations": 0,
              "overlays_relocated": 0, "overlays_nulled": 0,
              "skipped_unknown_edge_type": 0,
              "skipped_superseded_extraction": 0, "skipped_non_graph_purpose": 0,
              "aliased_endpoints": 0}
    superseded, aliases = read_overlays()
    # reset ONLY KG labels
    label_pred = " OR ".join(f"n:{lbl}" for lbl in kg_labels)
    session.run(f"MATCH (n) WHERE {label_pred} DETACH DELETE n")

    for ev in eventlog.replay():
        et = ev.get("event_type")
        if not is_projectable(ev):
            counts["skipped_non_graph_purpose"] += 1
            continue
        ann = annotation_update(ev)
        if ann is not None:
            doc_id, prop, value = ann
            session.run(f"MATCH (d:Document {{id: $id}}) SET d.{prop} = $value",
                        id=doc_id, value=value)
            counts["annotations"] += 1
            continue
        if et in ("node_asserted", "edge_asserted"):
            src_sha = (ev.get("provenance") or {}).get("source_sha256")
            if (ev.get("doc_id"), src_sha) in superseded:
                counts["skipped_superseded_extraction"] += 1
                continue
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
            from_id, to_id = p["from_id"], p["to_id"]
            for _orig, _resolved in (("from_id", aliases.get(from_id)),
                                     ("to_id", aliases.get(to_id))):
                if _resolved:
                    counts["aliased_endpoints"] += 1
            from_id = aliases.get(from_id, from_id)
            to_id = aliases.get(to_id, to_id)
            session.run(
                f"MERGE (a {{id: $from_id}}) MERGE (b {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel.upper()}]->(b) "
                "SET r.prov_method = $method, r.prov_doc = $doc, "
                "r.grounding_span = $span",
                from_id=from_id, to_id=to_id,
                method=prov.get("method") or prov.get("model_id") or "asserted",
                doc=ev.get("doc_id"), span=(p.get("item") or {}).get(
                    "grounding_span") or p.get("grounding_span"))
            counts["edges"] += 1
    # Repair overlays (task 2026-08-22_faithfulness_probe Phase 7) are applied LAST so they
    # win over the original assertion regardless of shard order. Never mutate the log.
    for ev in eventlog.replay():
        et = ev.get("event_type")
        if et == "grounding_relocated":
            session.run("MATCH (n {id: $id}) WHERE n.prov_wasDerivedFrom = $doc "
                        "SET n.grounding_span = $span, n.grounding_relocated_from = $old, "
                        "n.grounding_relocation_method = $m",
                        id=ev["item_id"], doc=ev["doc_id"], span=ev["new_span"], old=ev["old_span"], m=ev["method"])
            counts["overlays_relocated"] += 1
        elif et == "attribute_nulled":
            attr = ev["attribute"]
            if attr not in NULLABLE_ATTRIBUTES:
                continue
            session.run(f"MATCH (n {{id: $id}}) WHERE n.prov_wasDerivedFrom = $doc "
                        f"SET n.{attr} = null, n.nulled_attributes = coalesce(n.nulled_attributes, []) + $attr",
                        id=ev["item_id"], doc=ev["doc_id"], attr=attr)
            counts["overlays_nulled"] += 1
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
