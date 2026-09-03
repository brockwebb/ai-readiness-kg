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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402
from kg import eventlog  # noqa: E402
from kg.extraction.grounding import is_grounded  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import run_bulk_extraction as rbe  # noqa: E402
from run_bulk_extraction import doc_text  # noqa: E402
import build_projection as proj  # noqa: E402

REPORT = REPO / "docs" / "research" / "bulk_v1_gate_report.md"

# Run scope (task 2026-08-21_v03_visibility_kernel Phase 6): the gates measure the union of
# the selected run profiles — each profile contributes its corpus epoch (members +
# grounding scope) and its event shard (quarantine / empty-extraction scope). Default is
# the v1 profile alone, so the existing report is reproduced byte-for-byte in meaning.
EPOCHS: set[str] = set()
SHARDS: set[int] = set()


def scope_profiles(names: list[str]) -> dict:
    """Resolve profiles -> (members union, EPOCHS, SHARDS). Fail loud on an unknown name."""
    global EPOCHS, SHARDS
    members: dict = {}
    for n in names:
        rbe.apply_profile(n)
        EPOCHS.add(rbe.CORPUS_EPOCH)
        SHARDS.add(rbe.BULK_BATCH)
        members.update(rbe.corpus_members())
    return members


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


def read_overlays(events) -> tuple[set, dict]:
    """The two append-only overlays from the 2026-08-14 closeout. Shared by every
    check, because applying them to one check and not its sibling is exactly the
    defect this helper exists to prevent: check_edges honoured the supersession
    while check_grounding did not, so the replaced extraction's spans were
    re-verified against the REPLACEMENT source and 96 items reported ungrounded.
    """
    superseded, aliases = set(), {}
    for ev in events:
        et = ev.get("event_type")
        if et == "extraction_superseded":
            superseded.add((ev["doc_id"], ev["superseded_source_sha256"]))
        elif et == "edge_endpoint_alias":
            aliases[ev["alias_id"]] = ev["canonical_id"]
    return superseded, aliases


def live_events(events) -> list:
    """`events` minus the assertions of superseded extractions. The prior extraction
    stays in the log (never deleted); it is simply no longer part of the graph the
    gates measure, which is the same graph build_projection.py builds."""
    superseded, _ = read_overlays(events)
    if not superseded:
        return events

    # build_metrics carries no source sha, only an extraction_event_id. Map that id
    # to a sha via the assertions it produced, so the replaced run's metrics drop
    # precisely rather than by "keep the newest timestamp" guesswork. Without this,
    # a superseded doc contributes its metrics TWICE to quarantine_rate.
    sha_of_extraction: dict[str, str] = {}
    for ev in events:
        if ev.get("event_type") in ("node_asserted", "edge_asserted"):
            prov = ev.get("provenance") or {}
            eid, sha = prov.get("extraction_event_id"), prov.get("source_sha256")
            if eid and sha:
                sha_of_extraction[eid] = sha

    def keep(ev) -> bool:
        et = ev.get("event_type")
        if et in ("node_asserted", "edge_asserted"):
            return (ev.get("doc_id"),
                    (ev.get("provenance") or {}).get("source_sha256")) not in superseded
        if et == "build_metrics":
            sha = sha_of_extraction.get(ev.get("extraction_event_id"))
            return sha is None or (ev.get("doc_id"), sha) not in superseded
        return True

    return [ev for ev in events if keep(ev)]


def check_grounding(events, members) -> dict:
    """Re-verify every ADMITTED batch-004 item's span against its source text."""
    events = live_events(events)
    texts: dict[str, str] = {}
    failures, checked, legacy = [], 0, 0
    for ev in events:
        if ev.get("event_type") not in ("node_asserted", "edge_asserted"):
            continue
        in_scope = ev.get("provenance", {}).get("corpus_epoch") in EPOCHS
        if not in_scope:
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
    events = live_events(events)
    tot_items = tot_q = 0
    for ev in events:
        if ev.get("event_type") == "build_metrics" and \
                ev.get("metrics", {}).get("doc_id"):
            m = ev["metrics"]
            # scope: the selected run shards only — pilot metrics live in batch-002
            if _shard_of(ev) not in SHARDS:
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
            m = re.fullmatch(r"batch-(\d+)", shard.stem)
            if not m:          # tagged (non-graph) shards, e.g. batch-008_tevv_retest
                continue
            n = int(m.group(1))
            with shard.open(encoding="utf-8") as fh:
                for line in fh:
                    _SHARD_CACHE[json.loads(line)["event_id"]] = n
    return _SHARD_CACHE.get(ev["event_id"], -1)


def check_edges(events, schema) -> dict:
    """Every edge's endpoints exist among asserted/manifested ids; pair allowed.

    Reads the same two append-only overlays the projection reads (2026-08-14 closeout),
    so the gate measures the graph that was actually built rather than the raw log:
    superseded extractions are excluded, and aliased citation endpoints resolve to
    their canonical doc_id. THRESHOLD IS UNCHANGED (0) -- this corrects what is counted,
    it does not retune what passes.
    """
    _, aliases = read_overlays(events)
    events = live_events(events)
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
        for endpoint in (aliases.get(p.get("from_id"), p.get("from_id")),
                         aliases.get(p.get("to_id"), p.get("to_id"))):
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


def refuse_if_projection_stale() -> tuple[str, int]:
    """Refuse to report while the projection lacks the newest declared corpus epoch (task
    2026-09-02_post_burn_reconciliation §4). Returns (epoch, member count) when current.

    Runs AFTER `check_orphans_and_drift` has replayed the projection, so a refusal here means
    the newest epoch's members are not reaching the graph at all — a member with no
    `manifest_add` on the event log, or a replay that drops them — not merely a graph that
    had not been rebuilt yet. Either way the numbers below would describe a different corpus
    than the one the epoch declares, so no report is written."""
    epoch, members = proj.newest_corpus_epoch()
    missing = proj.missing_epoch_members(proj.projected_document_ids_live(), members)
    if missing:
        raise proj.ProjectionStaleError(
            f"REFUSING TO REPORT: the projection lacks {len(missing)} of {len(members)} "
            f"documents of the newest corpus epoch {epoch!r}: {missing}. Replay it "
            f"(python scripts/build_projection.py) and check that every member has a "
            f"manifest_add event; gate values off a stale projection are not findings.")
    print(f"projection current: newest epoch {epoch!r}, all {len(members)} members present")
    return epoch, len(members)


def check_empty(events, members) -> dict:
    events = live_events(events)
    extracted_docs, empty_docs = set(), set()
    for ev in events:
        if ev.get("event_type") == "build_metrics" and _shard_of(ev) in SHARDS:
            m = ev["metrics"]
            extracted_docs.add(m["doc_id"])
            if m["nodes"] + m["edges"] == 0:
                empty_docs.add(m["doc_id"])
    rate = (len(empty_docs) / len(extracted_docs)) if extracted_docs else 0.0
    return {"check_id": "empty_extraction_rate", "value": round(rate, 4),
            "threshold": 0.1196, "passed": rate <= 0.1196,
            "empty_docs": sorted(empty_docs),
            "docs_extracted": len(extracted_docs), "corpus_size": len(members)}


# --- TEVV gates (task 2026-08-22_kernel_tevv, Phase 5) ---------------------------------
# Pre-registered in dixie_evidence.yaml::tevv_gates. Evaluated only when the retest shard
# exists; realized values come from the three TEVV artifacts. Pure function (testable).

TEVV_STABILITY = REPO / "corpus/staging/metrics/tevv_stability.json"
TEVV_JUDGMENTS = REPO / "corpus/staging/metrics/tevv_faithfulness_judgments.jsonl"
TEVV_CALIBRATION = REPO / "corpus/staging/metrics/tevv_grade_calibration.json"


def faithfulness_precision(judgments: list[dict]) -> dict:
    """Pooled and per-stratum entailment precision over judged (non-error) items."""
    scored = [j for j in judgments if j.get("entailed") is not None]
    by = {}
    for j in scored:
        s = by.setdefault(j["stratum"], {"n": 0, "entailed": 0})
        s["n"] += 1; s["entailed"] += int(bool(j["entailed"]))
    per = {k: (v["entailed"] / v["n"] if v["n"] else None) for k, v in by.items()}
    pooled = (sum(int(bool(j["entailed"])) for j in scored) / len(scored)) if scored else None
    return {"pooled": pooled, "per_stratum": per, "counts": by,
            "judged": len(scored), "errors": len(judgments) - len(scored)}


def evaluate_tevv_gates(cfg: dict, stability: dict | None, judgments: list[dict] | None,
                        calibration: dict | None) -> list[dict]:
    """Realized value per pre-registered check. Missing inputs -> value None, passed None
    (not evaluated), never a silent PASS."""
    checks = cfg["checks"]
    pool = (stability or {}).get("pooled") or {}
    faith = faithfulness_precision(judgments) if judgments else None
    cal = calibration or {}
    values = {
        "stability_kappa_pooled": pool.get("kappa_all_items_pooled"),
        "stability_kappa_per_type_min": (min(v["kappa"] for v in pool["per_type"].values() if v["kappa"] is not None)
                                         if pool.get("per_type") else None),
        "stability_jaccard_pooled": pool.get("jaccard_spans_mean"),
        "faithfulness_precision_pooled": faith["pooled"] if faith else None,
        "faithfulness_precision_stratum_min": (min(v for v in faith["per_stratum"].values() if v is not None)
                                               if faith and faith["per_stratum"] else None),
        "grade_platform_official_precision": (cal.get("platform_official") or {}).get("precision"),
        "grade_peer_reviewed_precision": (cal.get("peer_reviewed_experiment") or {}).get("precision"),
    }
    out = []
    for c in checks:
        v = values.get(c["check_id"])
        thr = c["threshold"]
        if v is None:
            passed = None
        elif c["comparator"] == "gte":
            passed = v >= thr
        elif c["comparator"] == "lte":
            passed = v <= thr
        elif c["comparator"] == "eq":
            passed = v == thr
        else:
            raise ValueError(f"unknown comparator {c['comparator']!r}")
        rec = {"check_id": c["check_id"], "value": (round(v, 4) if isinstance(v, float) else v),
               "threshold": thr, "passed": passed}
        if c.get("phase_stop_below") is not None and v is not None:
            rec["phase_stop_triggered"] = v < c["phase_stop_below"]
        out.append(rec)
    return out


def tevv_inputs() -> tuple[dict | None, list[dict] | None, dict | None]:
    stab = json.loads(TEVV_STABILITY.read_text()) if TEVV_STABILITY.is_file() else None
    judg = ([json.loads(l) for l in TEVV_JUDGMENTS.read_text().splitlines() if l.strip()]
            if TEVV_JUDGMENTS.is_file() else None)
    cal = json.loads(TEVV_CALIBRATION.read_text()) if TEVV_CALIBRATION.is_file() else None
    return stab, judg, cal


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", default="v1",
                    help="comma-separated run profiles from scripts/run_profiles.yaml (default v1)")
    ap.add_argument("--report", default=None, help="report path (default docs/research/bulk_v1_gate_report.md)")
    ap.add_argument("--title", default="Bulk v1")
    args = ap.parse_args()
    report = Path(args.report) if args.report else REPORT
    if not report.is_absolute():
        report = REPO / report
    gate = _gate_config()
    if gate.get("preregistered") is not True:
        raise SystemExit("gate config is not pre-registered — refusing")
    schema = proj._load_schema()
    kg_labels = list(schema["node_types"])
    edge_whitelist = set(schema["edge_types"])
    members = scope_profiles([n.strip() for n in args.profiles.split(",") if n.strip()])
    events = _events()

    results = [check_min_corpus(gate, members),
               check_grounding(events, members),
               check_quarantine(events),
               check_edges(events, schema)]
    orphan, drift = check_orphans_and_drift(kg_labels, edge_whitelist)
    results += [orphan, drift, check_empty(events, members)]
    refuse_if_projection_stale()          # SystemExit before any report is written

    # TEVV gates: only when the retest shard exists (task 2026-08-22_kernel_tevv Phase 5)
    tevv_cfg = yaml.safe_load((REPO / "dixie_evidence.yaml").read_text(encoding="utf-8")).get("tevv_gates")
    tevv_results = []
    if tevv_cfg and any(True for _ in eventlog.replay(tag=tevv_cfg["retest_shard_tag"])):
        if tevv_cfg.get("preregistered") is not True:
            raise SystemExit("tevv_gates are not pre-registered — refusing")
        tevv_results = evaluate_tevv_gates(tevv_cfg, *tevv_inputs())

    now = datetime.now(timezone.utc).isoformat()
    lines = [f"# {args.title} — Pre-registered Gate Report", "",
             f"Scope: profiles={args.profiles} epochs={sorted(EPOCHS)} shards={sorted(SHARDS)}", "",
             f"Generated: {now}", "",
             "Failed gates are FINDINGS, not blockers. No retuning (task hard stop).",
             "", "| check | value | threshold | verdict |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['check_id']} | {r['value']} | {r['threshold']} | "
                     f"{'PASS' if r['passed'] else '**FAIL**'} |")
    if tevv_results:
        lines += ["", "## TEVV gates (pre-registered 2026-08-22; fails are findings)", "",
                  "| check | realized | threshold | verdict |", "|---|---|---|---|"]
        for r in tevv_results:
            verdict = "not evaluated" if r["passed"] is None else ("PASS" if r["passed"] else "**FAIL**")
            lines.append(f"| {r['check_id']} | {r['value']} | {r['threshold']} | {verdict} |")
        results = results + tevv_results
    lines += ["", "## Detail", "", "```json",
              json.dumps(results, indent=1, default=str), "```", ""]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:14]))
    print(f"\nreport: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
