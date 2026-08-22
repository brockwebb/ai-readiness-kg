#!/usr/bin/env python3
"""Per-document quality monitors with control limits (task 2026-08-21_v03_visibility_kernel
Phase 6; DD-005 promotion-gate metrics).

Prior art: Shewhart individuals (X) chart — per-unit measurements against mean ± k·SD of a
baseline period (Shewhart 1931; Montgomery, *Introduction to Statistical Quality Control*).
The baseline is the v0.2 corpus (profile `v1`); every later run is charted against it.

Monitors (each returns fired: bool + evidence):
  grounding       — an ADMITTED node/edge in scope whose span fails the verifier (absolute zero)
  evidence_grade  — a Claim stamped schema >= 0.3 missing/invalid evidence_grade, or a doc whose
                    missing-fraction exceeds the declared STOP fraction
  concept_density — per-doc concepts/1k tokens outside the baseline control limits
  quarantine      — per-doc quarantine rate above the UCL or the declared STOP rate
  proposed_rate   — per-doc proposed_relationships rate above the UCL

Outputs (under the configured metrics_dir): control_limits.json, quality_monitors.json.
`--mutation-test` runs the positive control: copies the event shards to a scratch dir, seeds
one synthetic known-bad extraction (ungrounded span + Claim with no evidence_grade + a
build_metrics row with out-of-control density/quarantine/proposed), re-runs every monitor on
the scratch copy and reports which fired. A monitor that has not fired on a seeded bad is
not verified. The live log is never touched.
"""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import statistics
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).parent))

import yaml  # noqa: E402
from kg import eventlog  # noqa: E402
from kg.extraction.grounding import is_grounded  # noqa: E402
from kg.extraction.schema_loader import load_schema  # noqa: E402

# run_bulk_extraction / run_baseline_gates pull in dixie + the Wintermute control plane
# (anaconda python only). They are imported lazily inside the functions that need the
# runner (profiles, source text) so the pure metric/limit/monitor functions stay testable
# under the plain test interpreter.


def _rbe():
    import run_bulk_extraction as rbe
    return rbe


def live_events(events: list[dict]) -> list[dict]:
    from run_baseline_gates import live_events as _live
    return _live(events)


def _shard_of(ev: dict) -> int:
    from run_baseline_gates import _shard_of as _s
    return _s(ev)


def _cfg() -> dict:
    doc = yaml.safe_load((REPO / "dixie_evidence.yaml").read_text(encoding="utf-8"))
    if "quality_monitors" not in doc:
        raise SystemExit("FATAL: dixie_evidence.yaml has no quality_monitors section")
    return doc["quality_monitors"]


def _ver(v) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


# --------------------------------------------------------------------------------------
# Per-document metrics
# --------------------------------------------------------------------------------------

def per_doc_metrics(events: list[dict], epochs: set[str],
                    shard_epoch: dict[int, str] | None = None) -> dict[str, dict]:
    """doc_id -> metrics for every doc extracted under one of `epochs` (live events only).
    build_metrics carries no epoch: resolve it from the extraction's assertions, else (an
    EMPTY extraction has none) from the shard the build_metrics event lives in, via
    `shard_epoch` (batch -> epoch from the run profiles)."""
    events = live_events(events)
    out: dict[str, dict] = {}
    epoch_of: dict[str, str] = {}
    for ev in events:
        if ev.get("event_type") in ("node_asserted", "edge_asserted"):
            prov = ev.get("provenance") or {}
            if prov.get("extraction_event_id") and prov.get("corpus_epoch"):
                epoch_of[prov["extraction_event_id"]] = prov["corpus_epoch"]
    for ev in events:
        if ev.get("event_type") != "build_metrics":
            continue
        ep = epoch_of.get(ev.get("extraction_event_id"))
        if ep is None and shard_epoch:
            ep = shard_epoch.get(_shard_of(ev))
        if ep not in epochs:
            continue
        m = ev["metrics"]
        total = m["nodes"] + m["edges"] + m["quarantined"]
        proposed = int(m.get("proposed_relationships_count", 0) or 0)
        out[m["doc_id"]] = {
            "doc_id": m["doc_id"], "epoch": ep,
            "extraction_event_id": ev.get("extraction_event_id"),
            "schema_version": ev.get("schema_version"),
            "concepts_per_1k_tokens": float(m["concepts_per_1k_tokens"]),
            "quarantine_rate": float(m["quarantine_rate"]),
            "proposed_rate": (proposed / (total + proposed)) if (total + proposed) else 0.0,
            "items": total, "proposed_relationships_count": proposed,
            "claims": {"total": 0, "graded": 0, "missing": 0, "invalid": 0, "distribution": {}},
        }
    # evidence-grade distribution from Claim assertions
    schema = load_schema()
    valid = set((schema["node_types"]["Claim"].get("property_values") or {})
                .get("evidence_grade") or [])
    for ev in events:
        if ev.get("event_type") != "node_asserted" or \
                (ev.get("payload") or {}).get("type") != "Claim":
            continue
        d = out.get(ev["doc_id"])
        if d is None:
            continue
        g = (ev["payload"].get("item") or {}).get("evidence_grade")
        c = d["claims"]
        c["total"] += 1
        if g is None:
            c["missing"] += 1
        elif valid and g not in valid:
            c["invalid"] += 1
        else:
            c["graded"] += 1
            c["distribution"][g] = c["distribution"].get(g, 0) + 1
    return out


def control_limits(baseline: dict[str, dict], sigma: float) -> dict:
    """Shewhart individuals limits (mean ± sigma·SD) per metric over the baseline docs."""
    lim = {"n": len(baseline), "sigma": sigma, "metrics": {}}
    for key in ("concepts_per_1k_tokens", "quarantine_rate", "proposed_rate"):
        xs = [d[key] for d in baseline.values()]
        if len(xs) < 2:
            raise SystemExit(f"FATAL: baseline has {len(xs)} docs — cannot set control limits")
        mean, sd = statistics.fmean(xs), statistics.stdev(xs)
        lim["metrics"][key] = {"mean": mean, "sd": sd,
                               "lcl": max(0.0, mean - sigma * sd), "ucl": mean + sigma * sd}
    return lim


# --------------------------------------------------------------------------------------
# Monitors
# --------------------------------------------------------------------------------------

def monitor_grounding(events, members: dict[str, Path], epochs: set[str]) -> dict:
    events = live_events(events)
    texts: dict[str, str] = {}
    failures = []
    checked = 0
    for ev in events:
        if ev.get("event_type") not in ("node_asserted", "edge_asserted"):
            continue
        if (ev.get("provenance") or {}).get("corpus_epoch") not in epochs:
            continue
        span = ((ev.get("payload") or {}).get("item") or {}).get("grounding_span")
        if not span:
            continue
        doc_id = ev["doc_id"]
        if doc_id not in members:
            failures.append({"doc_id": doc_id, "event_id": ev["event_id"],
                             "reason": "no source file for doc in scope"})
            continue
        if doc_id not in texts:
            texts[doc_id] = _rbe().doc_text(members[doc_id])
        checked += 1
        if not is_grounded(span, texts[doc_id]):
            failures.append({"doc_id": doc_id, "event_id": ev["event_id"], "span": span[:120]})
    return {"monitor": "grounding", "fired": bool(failures), "checked": checked,
            "failures": failures[:25], "failure_count": len(failures)}


def monitor_evidence_grade(metrics: dict[str, dict], cfg: dict) -> dict:
    floor = _ver(cfg["evidence_grade_required_from_schema"])
    stop_frac = float(cfg["evidence_grade_missing_stop_fraction"])
    hits = []
    for d in metrics.values():
        if _ver(d.get("schema_version")) < floor:
            continue
        c = d["claims"]
        bad = c["missing"] + c["invalid"]
        frac = (bad / c["total"]) if c["total"] else 0.0
        if bad:
            hits.append({"doc_id": d["doc_id"], "missing": c["missing"], "invalid": c["invalid"],
                         "total": c["total"], "missing_fraction": round(frac, 4),
                         "over_stop_fraction": frac > stop_frac})
    return {"monitor": "evidence_grade", "fired": bool(hits), "stop_fraction": stop_frac,
            "docs": hits}


def _limit_monitor(name: str, key: str, metrics: dict, limits: dict,
                   hard_ceiling: float | None = None, two_sided: bool = True) -> dict:
    lim = limits["metrics"][key]
    hits = []
    for d in metrics.values():
        x = d[key]
        reasons = []
        if x > lim["ucl"]:
            reasons.append(f"> UCL {lim['ucl']:.4f}")
        if two_sided and x < lim["lcl"]:
            reasons.append(f"< LCL {lim['lcl']:.4f}")
        if hard_ceiling is not None and x > hard_ceiling:
            reasons.append(f"> declared stop {hard_ceiling}")
        if reasons:
            hits.append({"doc_id": d["doc_id"], "epoch": d["epoch"], "value": round(x, 4),
                         "reasons": reasons})
    return {"monitor": name, "metric": key, "fired": bool(hits),
            "limits": lim, "hard_ceiling": hard_ceiling, "docs": hits}


def monitor_stability(stability: dict | None, kappa_floor: float, pa_floor: float) -> dict:
    """Per-node-type test-retest stability (task 2026-08-22_kernel_tevv Phase 5). Fires when
    any type's pooled kappa < kappa_floor OR positive agreement < pa_floor. Reads the
    artifact scripts/tevv_stability.py writes; None -> not evaluated (never a silent pass)."""
    if not stability:
        return {"monitor": "stability_per_type", "fired": False, "evaluated": False, "types": []}
    hits = []
    for typ, v in (stability.get("pooled") or {}).get("per_type", {}).items():
        k, pa = v.get("kappa"), v.get("positive_agreement")
        reasons = []
        if k is not None and k < kappa_floor:
            reasons.append(f"kappa {k:.3f} < {kappa_floor}")
        if pa is not None and pa < pa_floor:
            reasons.append(f"positive_agreement {pa:.3f} < {pa_floor}")
        if reasons:
            hits.append({"type": typ, "kappa": k, "positive_agreement": pa, "reasons": reasons})
    return {"monitor": "stability_per_type", "fired": bool(hits), "evaluated": True,
            "kappa_floor": kappa_floor, "pa_floor": pa_floor, "types": hits}


def run_monitors(profiles: list[str], cfg: dict, events_dir: Path | None = None) -> dict:
    if events_dir is not None:
        eventlog._EVENTS_DIR = events_dir   # module global, read at call time (tests do the same)
    events = list(eventlog.replay())
    # scope
    rbe = _rbe()
    members: dict[str, Path] = {}
    epochs: set[str] = set()
    shard_epoch: dict[int, str] = {}
    for n in profiles:
        rbe.apply_profile(n)
        epochs.add(rbe.CORPUS_EPOCH)
        shard_epoch[rbe.BULK_BATCH] = rbe.CORPUS_EPOCH
        members.update(rbe.corpus_members())
    rbe.apply_profile(cfg["baseline_profile"])
    base_epoch = rbe.CORPUS_EPOCH
    shard_epoch[rbe.BULK_BATCH] = base_epoch
    metrics_all = per_doc_metrics(events, epochs | {base_epoch}, shard_epoch)
    baseline = {k: v for k, v in metrics_all.items() if v["epoch"] == base_epoch}
    scoped = {k: v for k, v in metrics_all.items() if v["epoch"] in epochs}
    limits = control_limits(baseline, float(cfg["sigma"]))
    limits["baseline_epoch"] = base_epoch
    monitors = [
        monitor_grounding(events, members, epochs),
        monitor_evidence_grade(scoped, cfg),
        _limit_monitor("concept_density", "concepts_per_1k_tokens", scoped, limits),
        _limit_monitor("quarantine", "quarantine_rate", scoped, limits,
                       hard_ceiling=float(cfg["quarantine_stop_rate"]), two_sided=False),
        _limit_monitor("proposed_rate", "proposed_rate", scoped, limits, two_sided=False),
    ]
    stab_path = REPO / cfg.get("stability_artifact", "corpus/staging/metrics/tevv_stability.json")
    stab = json.loads(stab_path.read_text()) if stab_path.is_file() else None
    monitors.append(monitor_stability(stab, float(cfg["stability_kappa_floor"]),
                                      float(cfg["stability_pa_floor"])))
    return {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "profiles": profiles, "epochs": sorted(epochs), "baseline_epoch": base_epoch,
            "control_limits": limits, "monitors": monitors, "per_doc": scoped}


# --------------------------------------------------------------------------------------
# Positive control (mutation test)
# --------------------------------------------------------------------------------------

def seed_known_bad(scratch_events: Path, doc_id: str, epoch: str, batch: int) -> dict:
    """Append one synthetic known-bad extraction to the SCRATCH shard: an ungrounded Claim
    with no evidence_grade, plus a build_metrics row far outside every control limit."""
    eid = uuid.uuid4().hex
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    prov = {"model_id": "synthetic-mutation-test", "schema_version": "0.3",
            "prompt_version": "0.3.0", "extraction_event_id": eid, "timestamp": stamp,
            "corpus_epoch": epoch, "source_sha256": "0" * 64}
    node = {"event_type": "node_asserted", "doc_id": doc_id, "extraction_event_id": eid,
            "provenance": prov,
            "payload": {"id": "claim_mutation_seed", "type": "Claim",
                        "item": {"id": "claim_mutation_seed",
                                 "claim_text": "synthetic seeded bad claim",
                                 "claim_type": "empirical",
                                 "grounding_span": "ZZZ-THIS-SPAN-DOES-NOT-OCCUR-IN-ANY-SOURCE-ZZZ"}},
            "event_id": uuid.uuid4().hex, "timestamp": stamp, "schema_version": "0.3"}
    bm = {"event_type": "build_metrics", "doc_id": doc_id, "extraction_event_id": eid,
          "metrics": {"doc_id": doc_id, "estimated_tokens": 1000, "concepts": 9999,
                      "concepts_per_1k_tokens": 9999.0, "definitions_count": 0,
                      "claims_count": 1, "nodes": 1, "edges": 0, "quarantined": 999,
                      "quarantine_rate": 0.999, "proposed_relationships_count": 999},
          "event_id": uuid.uuid4().hex, "timestamp": stamp, "schema_version": "0.3"}
    shard = scratch_events / f"batch-{batch:03d}.jsonl"
    with shard.open("a", encoding="utf-8") as fh:
        for ev in (node, bm):
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return {"extraction_event_id": eid, "doc_id": doc_id, "shard": shard.name}


def mutation_test(profiles: list[str], cfg: dict, scratch_root: Path) -> dict:
    scratch = scratch_root / "events_mutation"
    if scratch.exists():
        shutil.rmtree(scratch)
    shutil.copytree(REPO / "events", scratch, ignore=shutil.ignore_patterns("raw", "*STOP*"))
    rbe = _rbe()
    rbe.apply_profile(profiles[-1])
    members = rbe.corpus_members()
    doc_id = sorted(members)[0]
    seed = seed_known_bad(scratch, doc_id, rbe.CORPUS_EPOCH, rbe.BULK_BATCH)
    res = run_monitors(profiles, cfg, events_dir=scratch)
    eventlog._EVENTS_DIR = REPO / "events"   # restore
    # stability positive control: a synthetic retest of the seeded doc sharing NOTHING with
    # the original -> every per-type kappa/PA collapses -> the monitor must fire.
    import tevv_stability as ts
    orig = [ev for ev in eventlog.replay() if ev.get("doc_id") == doc_id]
    fake_retest = [{"event_type": "node_asserted", "doc_id": doc_id,
                    "payload": {"id": f"mut{i}", "type": ev["payload"]["type"],
                                "item": {ts.PRIMARY_TEXT.get(ev["payload"]["type"], "name"): f"MUTATION-{i}",
                                         "grounding_span": "ZZZ"}}}
                   for i, ev in enumerate(e for e in orig if e.get("event_type") == "node_asserted")]
    stab = {"pooled": ts.pooled_from_events(orig, fake_retest, [doc_id])}
    # the live-artifact stability monitor is not part of the positive control; replace it
    res["monitors"] = [m for m in res["monitors"] if m["monitor"] != "stability_per_type"]
    res["monitors"].append(monitor_stability(stab, float(cfg["stability_kappa_floor"]),
                                             float(cfg["stability_pa_floor"])))
    verdicts = []
    for m in res["monitors"]:
        fired_on_seed = False
        if m["monitor"] == "grounding":
            fired_on_seed = any(f.get("doc_id") == doc_id and "ZZZ" in (f.get("span") or "")
                                for f in m["failures"])
        elif m["monitor"] == "stability_per_type":
            fired_on_seed = bool(m["types"])      # computed on the seeded retest only
        else:
            fired_on_seed = any(d["doc_id"] == doc_id for d in m["docs"])
        verdicts.append({"monitor": m["monitor"], "fired": m["fired"],
                         "fired_on_seed": fired_on_seed,
                         "verified": bool(m["fired"] and fired_on_seed)})
    return {"seed": seed, "scratch": str(scratch), "verdicts": verdicts,
            "all_verified": all(v["verified"] for v in verdicts)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", default="v1", help="comma-separated run profiles in scope")
    ap.add_argument("--mutation-test", action="store_true",
                    help="positive control on a scratch copy of the log; live log untouched")
    ap.add_argument("--scratch", default=None, help="scratch root for --mutation-test")
    ap.add_argument("--out-dir", default=None, help="override metrics_dir")
    args = ap.parse_args()
    cfg = _cfg()
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    out_dir = Path(args.out_dir) if args.out_dir else REPO / cfg["metrics_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mutation_test:
        if not args.scratch:
            raise SystemExit("FATAL: --mutation-test requires --scratch DIR (never the live log)")
        res = mutation_test(profiles, cfg, Path(args.scratch))
        (out_dir / "mutation_test.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        for v in res["verdicts"]:
            print(f"  {v['monitor']:16s} fired={v['fired']!s:5s} on_seed={v['fired_on_seed']!s:5s} "
                  f"-> {'VERIFIED' if v['verified'] else 'NOT VERIFIED'}")
        print("all_verified:", res["all_verified"])
        return 0 if res["all_verified"] else 1

    res = run_monitors(profiles, cfg)
    (out_dir / "control_limits.json").write_text(
        json.dumps(res["control_limits"], indent=1) + "\n", encoding="utf-8")
    (out_dir / "quality_monitors.json").write_text(
        json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"scope epochs={res['epochs']} baseline={res['baseline_epoch']} "
          f"(n={res['control_limits']['n']}, sigma={res['control_limits']['sigma']})")
    for k, v in res["control_limits"]["metrics"].items():
        print(f"  {k:24s} mean={v['mean']:.4f} sd={v['sd']:.4f} lcl={v['lcl']:.4f} ucl={v['ucl']:.4f}")
    for m in res["monitors"]:
        n = m.get("failure_count", len(m.get("docs", m.get("types", []))))
        print(f"  {m['monitor']:16s} fired={m['fired']!s:5s} hits={n}")
    print("written:", out_dir / "quality_monitors.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
