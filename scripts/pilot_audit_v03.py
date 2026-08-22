#!/usr/bin/env python3
"""Phase 4 pilot audit (task 2026-08-21_v03_visibility_kernel; schema §9 pilot gate).

For the named pilot docs (kernel_v03 profile): proposed_relationships volume + names,
concept density vs the v0.2 (v1 epoch) baseline, quarantine rate with REASONS (re-parsed
read-only from the persisted raw responses — the log stores only counts), evidence_grade
distribution, and the grading-confusion signal (Claims graded `platform_official` from
non-platform sources, where "platform source" = inclusion-rule clause b).

Schema patch rule (task, decide-don't-escalate): a proposed relationship name appearing
>= PATCH_MIN_OCCURRENCES times across >= PATCH_MIN_DOCS pilot docs with grounded spans is
a v0.3.1 candidate; the script reports candidates, it does not edit the schema.
Writes docs/research/2026-08-21_v03_pilot_audit.json; the markdown audit is authored from it.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog                                   # noqa: E402
from kg.extraction import parser as kparser               # noqa: E402
from kg.extraction.grounding import is_grounded           # noqa: E402
import run_bulk_extraction as rbe                         # noqa: E402

PATCH_MIN_OCCURRENCES = 3   # task Phase 4 schema patch rule
PATCH_MIN_DOCS = 2
STOP_QUARANTINE = 0.15      # task Phase 4 STOP
STOP_GRADE_MISSING = 0.10   # task Phase 4 STOP (fraction of Claims)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True, help="comma-separated pilot doc_ids")
    ap.add_argument("--profile", default="kernel_v03")
    ap.add_argument("--out", default="docs/research/2026-08-21_v03_pilot_audit.json")
    a = ap.parse_args()
    docs = [d.strip() for d in a.docs.split(",") if d.strip()]
    rbe.apply_profile(a.profile)
    members = rbe.corpus_members()
    events = list(eventlog.replay())

    clause, src_type = {}, {}
    for ev in events:
        if ev.get("event_type") == "manifest_add":
            p = ev["payload"]; clause[p["doc_id"]] = (p.get("acquisition") or {}).get("clause")
            src_type[p["doc_id"]] = p.get("source_type")
    # v0.2 baseline density: v1-epoch build_metrics (from the quality monitors' control limits)
    cl = json.loads((REPO / "corpus/staging/metrics/control_limits.json").read_text())
    base_density = cl["metrics"]["concepts_per_1k_tokens"]

    per_doc, grades_all, proposed_names = {}, Counter(), defaultdict(lambda: {"n": 0, "docs": set(), "grounded": 0})
    for d in docs:
        if d not in members:
            raise SystemExit(f"FATAL: {d} is not a {rbe.CORPUS_EPOCH} member")
        bm = [ev for ev in events if ev.get("event_type") == "build_metrics" and ev["doc_id"] == d]
        if not bm:
            per_doc[d] = {"status": "not_extracted"}; continue
        m = bm[-1]["metrics"]
        text = rbe.doc_text(members[d])
        # re-parse the persisted raw response for quarantine reasons (read-only)
        raws = sorted(rbe.RAW_DIR.glob(f"{d}.*.json"))
        reasons, pr = Counter(), []
        if raws:
            raw = json.loads(raws[-1].read_text(encoding="utf-8"))
            try:
                out = rbe.model_stub._extract_json(raw["raw_result"] or "")
                # same harness-owned provenance injection the pipeline applies (v3 contract)
                out = rbe.pipeline._apply_provenance_ownership(out, d)
                res = kparser.parse_extraction(out, text)
                for q in res.quarantined:
                    reasons[q["reason"][:90]] += 1
                pr = res.proposed_relationships
            except Exception as exc:  # audit must not die on one bad raw; report it
                reasons[f"RE-PARSE FAILED: {str(exc)[:80]}"] += 1
        for p in pr:
            name = p.get("suggested_edge") or p.get("edge") or "?"
            g = bool(p.get("grounding_span")) and is_grounded(p["grounding_span"], text)
            e = proposed_names[name]; e["n"] += 1; e["docs"].add(d); e["grounded"] += int(g)
        grades = Counter()
        po_nonplatform = 0
        for ev in events:
            if ev.get("event_type") == "node_asserted" and ev["doc_id"] == d and \
                    ev["payload"].get("type") == "Claim":
                g = (ev["payload"].get("item") or {}).get("evidence_grade") or "MISSING"
                grades[g] += 1
                if g == "platform_official" and clause.get(d) != "b":
                    po_nonplatform += 1
        grades_all.update(grades)
        n_claims = sum(grades.values())
        per_doc[d] = {
            "status": "extracted", "clause": clause.get(d), "source_type": src_type.get(d),
            "chars": len(text), "nodes": m["nodes"], "edges": m["edges"],
            "quarantined": m["quarantined"], "quarantine_rate": m["quarantine_rate"],
            "quarantine_reasons": dict(reasons),
            "concepts_per_1k_tokens": m["concepts_per_1k_tokens"],
            "density_z_vs_v02": round((m["concepts_per_1k_tokens"] - base_density["mean"]) / base_density["sd"], 3),
            "proposed_relationships_count": m.get("proposed_relationships_count", 0),
            "proposed_names": sorted({(p.get("suggested_edge") or p.get("edge") or "?") for p in pr}),
            "claims": n_claims, "evidence_grade_distribution": dict(grades),
            "grade_missing_fraction": round(grades.get("MISSING", 0) / n_claims, 4) if n_claims else 0.0,
            "platform_official_from_nonplatform": po_nonplatform,
            "stop_quarantine": m["quarantine_rate"] > STOP_QUARANTINE,
            "stop_grade_missing": (grades.get("MISSING", 0) / n_claims if n_claims else 0) > STOP_GRADE_MISSING,
        }
    ext = [v for v in per_doc.values() if v["status"] == "extracted"]
    candidates = {k: {"n": v["n"], "docs": sorted(v["docs"]), "grounded": v["grounded"]}
                  for k, v in proposed_names.items()}
    patch = [k for k, v in candidates.items()
             if v["n"] >= PATCH_MIN_OCCURRENCES and len(v["docs"]) >= PATCH_MIN_DOCS and v["grounded"] >= PATCH_MIN_OCCURRENCES]
    summary = {
        "docs": per_doc, "extracted": len(ext),
        "v02_density_baseline": base_density,
        "pilot_density_mean": statistics.fmean(v["concepts_per_1k_tokens"] for v in ext) if ext else None,
        "pilot_quarantine_rate_pooled": (sum(v["quarantined"] for v in ext) /
                                         max(1, sum(v["nodes"] + v["edges"] + v["quarantined"] for v in ext))) if ext else None,
        "evidence_grade_distribution_all": dict(grades_all),
        "platform_official_from_nonplatform_total": sum(v["platform_official_from_nonplatform"] for v in ext),
        "claims_total": sum(v["claims"] for v in ext),
        "proposed_relationship_names": candidates,
        "schema_patch_rule": {"min_occurrences": PATCH_MIN_OCCURRENCES, "min_docs": PATCH_MIN_DOCS,
                              "candidates_v031": patch},
        "stop_triggered": any(v["stop_quarantine"] or v["stop_grade_missing"] for v in ext),
    }
    out = REPO / a.out
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "docs"}, indent=1, default=str))
    for d, v in per_doc.items():
        print(d, {k: v[k] for k in v if k in ("status", "quarantine_rate", "concepts_per_1k_tokens", "claims", "grade_missing_fraction", "proposed_relationships_count")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
