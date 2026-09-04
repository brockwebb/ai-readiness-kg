#!/usr/bin/env python3
"""KG structural diagnostic — the queries that were run in chat, as code.

**The defect this file exists to close** (task `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md`
§0): on 2026-09-04 a Desktop session ran four diagnostic Cypher queries against
`seldon-ai-readiness-kg` through an MCP client, in chat, and drew conclusions from the answers.
Nothing consequential in this project may live only in a chat transcript — a number nobody can
re-derive is not a measurement, it is a memory. Every figure that session quoted is re-derived
here, by name, from one script whose output is registered.

Emits JSON on stdout (or to `--out`). Every top-level key is a metric registered as a Result
named `kg_diag_<key>` by `scripts/register_kg_diagnostic_results.py`.

**Scope, stated because the counts depend on it:** the KG layer is the eleven domain labels in
`KG_LABELS`. Seldon's own artifact labels (Result, DataFile, ResearchTask, DesignNote, Script,
Issue, OntologyTerm, …) live in the same database under disjoint labels and are excluded from
every domain figure — the same partition `build_projection.py` uses when it rebuilds.

    /opt/anaconda3/bin/python3 scripts/kg_diagnostic.py [--database NAME] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, "/Users/brock/GitHub/seldon")

#: The KG's own labels. Everything else in this database is a Seldon artifact.
KG_LABELS = ["Concept", "Claim", "Definition", "Measure", "Practice", "Standard",
             "Framework", "Instrument", "Platform", "Document", "Tool"]

#: The canonical key the duplicate measurement groups on: exact match after lowering and
#: trimming. Deliberately the weakest possible collapse — it counts only duplicates nobody
#: could dispute, so the redundancy figure is a floor, not an estimate (Zaveri et al. 2016
#: conciseness: redundancy of entities).
CANON = "toLower(trim(n.name))"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect(session) -> dict:
    """Every figure the chat session quoted, plus the label census behind them."""
    out: dict = {"generated_at": _now(), "kg_labels": KG_LABELS}

    one = lambda q, **kw: session.run(q, **kw).single()          # noqa: E731
    rows = lambda q, **kw: session.run(q, **kw).data()           # noqa: E731

    out["nodes_total"] = one("MATCH (n) RETURN count(n) AS n")["n"]
    out["label_counts"] = {r["label"]: r["c"] for r in rows(
        "CALL db.labels() YIELD label "
        "CALL {WITH label MATCH (n) WHERE label IN labels(n) RETURN count(n) AS c} "
        "RETURN label, c ORDER BY c DESC")}
    out["concept_total"] = out["label_counts"].get("Concept", 0)
    out["claim_total"] = out["label_counts"].get("Claim", 0)
    out["document_total"] = out["label_counts"].get("Document", 0)

    # --- duplication (conciseness) -------------------------------------------------------
    dup = one(
        f"MATCH (n:Concept) WITH {CANON} AS k, count(*) AS c WHERE c > 1 "
        "RETURN count(*) AS groups, sum(c) AS nodes")
    out["concept_dup_groups"] = dup["groups"] or 0
    out["concept_dup_nodes"] = dup["nodes"] or 0
    out["concept_dup_node_share"] = (round(out["concept_dup_nodes"] / out["concept_total"], 6)
                                     if out["concept_total"] else None)
    out["concept_dup_largest_groups"] = rows(
        f"MATCH (n:Concept) WITH {CANON} AS k, count(*) AS c WHERE c > 1 "
        "RETURN k AS key, c AS nodes ORDER BY c DESC, k LIMIT 15")
    ai = one(
        f"MATCH (n:Concept) WHERE {CANON} = 'ai readiness' "
        "OPTIONAL MATCH ()-[r]->(n) RETURN count(DISTINCT n) AS nodes, count(r) AS in_edges")
    out["ai_readiness_nodes"] = ai["nodes"]
    out["ai_readiness_in_edges"] = ai["in_edges"]

    # --- concept connectivity ------------------------------------------------------------
    # Group by NODE, never by name: with 1,122 duplicate-name groups in this graph, grouping
    # by `n.name` silently merges duplicates and reports a connectivity the nodes do not have
    # (it inflated max degree 26 -> 66 on the first draft of this script). Degree is every
    # incident relationship, in or out.
    degs = sorted(r["d"] for r in rows(
        "MATCH (n:Concept) OPTIONAL MATCH (n)-[r]-() WITH n, count(r) AS d RETURN d"))
    out["concept_degree_median"] = degs[len(degs) // 2] if degs else None
    out["concept_degree_max"] = degs[-1] if degs else None
    out["concept_degree_1"] = sum(1 for d in degs if d == 1)
    out["concept_degree_0"] = sum(1 for d in degs if d == 0)
    out["concept_degree_ge5"] = sum(1 for d in degs if d >= 5)

    # --- domain edges --------------------------------------------------------------------
    triples = rows(
        "MATCH (a)-[r]->(b) WHERE any(l IN labels(a) WHERE l IN $kg) "
        "AND any(l IN labels(b) WHERE l IN $kg) "
        "RETURN labels(a)[0] AS a, type(r) AS t, labels(b)[0] AS b, count(*) AS n "
        "ORDER BY n DESC", kg=KG_LABELS)
    # "Domain edges" = edges with NO Artifact endpoint: the KG layer as distinct from Seldon's
    # artifact graph, which is the partition build_projection.py uses. Reported alongside the
    # stricter both-endpoints-are-KG-labels count, because the two differ by the edges that
    # touch a node carrying neither kind of label and the difference is not an error.
    out["domain_edges_total"] = one(
        "MATCH (a)-[r]->(b) WHERE NOT a:Artifact AND NOT b:Artifact RETURN count(r) AS n")["n"]
    out["domain_edges_both_kg_labels"] = sum(t["n"] for t in triples)
    out["edges_total"] = one("MATCH ()-[r]->() RETURN count(r) AS n")["n"]
    out["domain_edge_triples"] = triples[:20]
    by_type: dict = {}
    for t in triples:
        by_type[t["t"]] = by_type.get(t["t"], 0) + t["n"]
    out["domain_edges_by_type"] = dict(sorted(by_type.items(), key=lambda kv: -kv[1]))

    # --- cross-document integration ------------------------------------------------------
    out["document_cites_document"] = one(
        "MATCH (:Document)-[r:CITES]->(:Document) RETURN count(r) AS n")["n"]
    out["claim_conflicts_claim"] = one(
        "MATCH (:Claim)-[r:CONFLICTS_WITH]->(:Claim) RETURN count(r) AS n")["n"]
    out["definition_conflicts"] = one(
        "MATCH (:Definition)-[r:CONFLICTS_WITH]->() RETURN count(r) AS n")["n"]

    # --- claims and documents ------------------------------------------------------------
    out["claims_without_asserts_source"] = one(
        "MATCH (c:Claim) WHERE NOT (:Document)-[:ASSERTS]->(c) RETURN count(c) AS n")["n"]
    out["claims_without_asserts_sample"] = [r["id"] for r in rows(
        "MATCH (c:Claim) WHERE NOT (:Document)-[:ASSERTS]->(c) "
        "RETURN coalesce(c.claim_id, c.id, elementId(c)) AS id ORDER BY id LIMIT 5")]
    per_doc = sorted(r["c"] for r in rows(
        "MATCH (d:Document) OPTIONAL MATCH (d)-[r]->(x) "
        "WHERE any(l IN labels(x) WHERE l IN $kg) WITH d, count(r) AS c RETURN c", kg=KG_LABELS))
    out["documents_without_extractions"] = sum(1 for c in per_doc if c == 0)
    out["document_extractions_median"] = per_doc[len(per_doc) // 2] if per_doc else None

    # --- provenance completeness ---------------------------------------------------------
    out["concept_with_doc_id"] = one(
        "MATCH (n:Concept) WHERE n.doc_id IS NOT NULL RETURN count(n) AS n")["n"]
    out["concept_with_grounding_span"] = one(
        "MATCH (n:Concept) WHERE n.grounding_span IS NOT NULL RETURN count(n) AS n")["n"]
    out["concept_with_aliases"] = one(
        "MATCH (n:Concept) WHERE n.aliases IS NOT NULL RETURN count(n) AS n")["n"]
    # The property is `content_hash`, not `prov_source_sha256` — that name appears in the task
    # file and in no node in this graph (checked: 0 Documents carry it, 211 carry content_hash).
    out["document_with_content_hash"] = one(
        "MATCH (d:Document) WHERE d.content_hash IS NOT NULL RETURN count(d) AS n")["n"]
    out["document_with_prov_source_sha256"] = one(
        "MATCH (d:Document) WHERE d.prov_source_sha256 IS NOT NULL RETURN count(d) AS n")["n"]
    out["documents_extracted"] = out["document_total"] - out["documents_without_extractions"]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--database", default=None, help="defaults to the project's configured database")
    ap.add_argument("--out", default=None, help="write the JSON here as well as to stdout")
    a = ap.parse_args(argv)

    from seldon.config import get_neo4j_driver, load_project_config
    config = load_project_config(REPO)
    database = a.database or config["neo4j"]["database"]
    driver = get_neo4j_driver(config)
    try:
        with driver.session(database=database) as session:
            data = collect(session)
    finally:
        driver.close()
    data["database"] = database
    text = json.dumps(data, indent=1, ensure_ascii=False, default=str)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.out}", file=sys.stderr)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
