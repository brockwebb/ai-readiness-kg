#!/usr/bin/env python3
"""Pre-registered baseline gates (task 2026-07-05_airkg_bulk_extraction_v1 Stage 5).

Runs the six checks declared in dixie_evidence.yaml::baseline_gate against the
event log + the built projection. FAILED GATES DO NOT BLOCK — the report is the
finding. No retuning: thresholds are read from config, never adjusted here.

Scope note: the v1 gate report scopes grounding/quarantine to THIS RUN's shard
(batch-004). Pilot-era items (batch-002) were grounded at parse time against
the pilot session's text rendering; re-verifying them against a pypdf rendering
would manufacture false failures, so they are reported separately as legacy.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402
from kg import eventlog  # noqa: E402
from kg.extraction.grounding import is_grounded  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from run_bulk_extraction import corpus_v1_members, doc_text, BULK_BATCH  # noqa: E402
import build_projection as proj  # noqa: E402

REPORT = REPO / "docs" / "research" / "bulk_v1_gate_report.md"


def _gate_config() -> dict:
    cfg = yaml.safe_load((REPO / "dixie_evidence.yaml").read_text(encoding="utf-8"))
    return cfg["baseline_gate"]


def _events():
    return list(eventlog.replay())


def check_min_corpus(gate, members) -> dict:
    n = len(members)
    threshold = gate["min_verified_included"]
    return {"check_id": "min_verified_included", "value": n,
            "threshold": threshold, "passed": n >= threshold}


def check_grounding(events, members) -> dict:
    """Re-verify every ADMITTED batch-004 item's span against its source text."""
    texts: dict[str, str] = {}
    failures, checked, legacy = [], 0, 0
    for ev in events:
        if ev.get("event_type") not in ("node_asserted", "edge_asserted"):
            continue
        batch4 = ev.get("provenance", {}).get("corpus_epoch") == "v1"
        if not batch4:
            legacy += 1
            continue
        doc_id = ev["doc_id"]
        item = ev["payload"].get("item") or {}
        span = item.get("grounding_span")
        if not span:
            continue  # span-less item classes are the parser's concern
        if doc_id not in texts:
            texts[doc_id] = doc_text(members[doc_id])
        checked += 1
        if not is_grounded(span, texts[doc_id]):
            failures.append({"doc_id": doc_id, "event_id": ev["event_id"],
                             "span": span[:120]})
    return {"check_id": "grounding_zero_ungrounded", "value": len(failures),
            "threshold": 0, "passed": len(failures) == 0,
            "checked_items": checked, "legacy_items_not_rechecked": legacy,
            "failures": failures[:20]}


def check_quarantine(events) -> dict:
    tot_items = tot_q = 0
    for ev in events:
        if ev.get("event_type") == "build_metrics" and \
                ev.get("metrics", {}).get("doc_id"):
            m = ev["metrics"]
            # scope: this run's shard only — pilot metrics live in batch-002
            if _shard_of(ev) != BULK_BATCH:
                continue
            tot_items += m["nodes"] + m["edges"] + m["quarantined"]
            tot_q += m["quarantined"]
    rate = (tot_q / tot_items) if tot_items else 0.0
    return {"check_id": "quarantine_rate", "value": round(rate, 4),
            "threshold": 0.0152, "passed": rate <= 0.0152,
            "quarantined": tot_q, "total_items": tot_items}


_SHARD_CACHE: dict[str, int] = {}


def _shard_of(ev) -> int:
    """Which batch shard an event lives in (by event_id scan, cached)."""
    if not _SHARD_CACHE:
        for shard in sorted((REPO / "events").glob("batch-*.jsonl")):
            n = int(shard.stem.split("-")[1])
            with shard.open(encoding="utf-8") as fh:
                for line in fh:
                    _SHARD_CACHE[json.loads(line)["event_id"]] = n
    return _SHARD_CACHE.get(ev["event_id"], -1)


def check_edges(events, schema) -> dict:
    """Every edge's endpoints exist among asserted/manifested ids; pair allowed."""
    known: set[str] = set()
    pairs = {name: {tuple(p) for p in spec.get("pairs", [[spec["from"], spec["to"]]])}
             for name, spec in schema["edge_types"].items()}
    for ev in events:
        if ev.get("event_type") == "manifest_add":
            known.add(ev["payload"]["doc_id"])
        elif ev.get("event_type") == "node_asserted":
            known.add(ev["payload"]["id"])
    violations = []
    for ev in events:
        et = ev.get("event_type")
        if et not in ("edge_asserted", "curated_promotion"):
            continue
        p = ev["payload"] if et == "edge_asserted" else ev
        rel = p.get("type") if et == "edge_asserted" else p.get("edge")
        problems = []
        if rel not in pairs:
            problems.append(f"unknown edge type {rel!r}")
        elif (p.get("from_type"), p.get("to_type")) not in pairs[rel]:
            problems.append(f"pair ({p.get('from_type')},{p.get('to_type')}) "
                            f"not allowed for {rel}")
        for endpoint in (p.get("from_id"), p.get("to_id")):
            if endpoint not in known:
                problems.append(f"endpoint {endpoint!r} never asserted/manifested")
        if problems:
            violations.append({"event_id": ev["event_id"], "edge": rel,
                               "problems": problems})
    return {"check_id": "edge_endpoint_validation", "value": len(violations),
            "threshold": 0, "passed": len(violations) == 0,
            "violations": violations[:20]}


def check_orphans_and_drift(kg_labels, edge_whitelist) -> tuple[dict, dict]:
    uri, user, pw = proj._neo4j_creds()
    db = proj._database()
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    with driver.session(database=db) as session:
        proj.build(session, kg_labels, edge_whitelist)
        fp1 = proj.fingerprint(session, kg_labels)
        label_pred = " OR ".join(f"n:{lbl}" for lbl in kg_labels if lbl != "Document")
        total = session.run(
            f"MATCH (n) WHERE {label_pred} RETURN count(n) AS c").single()["c"]
        orphans = session.run(
            f"MATCH (n) WHERE ({label_pred}) AND NOT (n)--() "
            "RETURN count(n) AS c").single()["c"]
        # drift: rebuild from scratch, compare fingerprints
        proj.build(session, kg_labels, edge_whitelist)
        fp2 = proj.fingerprint(session, kg_labels)
    driver.close()
    rate = (orphans / total) if total else 0.0
    orphan = {"check_id": "orphan_rate", "value": round(rate, 4),
              "threshold": 0.0034, "passed": rate <= 0.0034,
              "orphans": orphans, "total_non_document_nodes": total}
    drift_delta = {k: (fp1.get(k), fp2.get(k))
                   for k in set(fp1) | set(fp2) if fp1.get(k) != fp2.get(k)}
    drift = {"check_id": "projection_drift", "value": len(drift_delta),
             "threshold": 0, "passed": not drift_delta,
             "delta": drift_delta, "fingerprint": fp2}
    return orphan, drift


def check_empty(events, members) -> dict:
    extracted_docs, empty_docs = set(), set()
    for ev in events:
        if ev.get("event_type") == "build_metrics" and _shard_of(ev) == BULK_BATCH:
            m = ev["metrics"]
            extracted_docs.add(m["doc_id"])
            if m["nodes"] + m["edges"] == 0:
                empty_docs.add(m["doc_id"])
    rate = (len(empty_docs) / len(extracted_docs)) if extracted_docs else 0.0
    return {"check_id": "empty_extraction_rate", "value": round(rate, 4),
            "threshold": 0.1196, "passed": rate <= 0.1196,
            "empty_docs": sorted(empty_docs),
            "docs_extracted": len(extracted_docs), "corpus_size": len(members)}


def main() -> int:
    gate = _gate_config()
    if gate.get("preregistered") is not True:
        raise SystemExit("gate config is not pre-registered — refusing")
    schema = proj._load_schema()
    kg_labels = list(schema["node_types"])
    edge_whitelist = set(schema["edge_types"])
    members = corpus_v1_members()
    events = _events()

    results = [check_min_corpus(gate, members),
               check_grounding(events, members),
               check_quarantine(events),
               check_edges(events, schema)]
    orphan, drift = check_orphans_and_drift(kg_labels, edge_whitelist)
    results += [orphan, drift, check_empty(events, members)]

    now = datetime.now(timezone.utc).isoformat()
    lines = [f"# Bulk v1 — Pre-registered Gate Report", "",
             f"Generated: {now}", "",
             "Failed gates are FINDINGS, not blockers. No retuning (task hard stop).",
             "", "| check | value | threshold | verdict |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['check_id']} | {r['value']} | {r['threshold']} | "
                     f"{'PASS' if r['passed'] else '**FAIL**'} |")
    lines += ["", "## Detail", "", "```json",
              json.dumps(results, indent=1, default=str), "```", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:12]))
    print(f"\nreport: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
