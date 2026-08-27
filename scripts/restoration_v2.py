#!/usr/bin/env python3
"""Restoration v2 — two-stage attribute restoration (task 2026-08-26_overnight_burn Lane 4).

The v1 single-call restoration class was REVERSED at the acceptance gate (0.78 fact-level
entailment < 0.90, task a2d3fb42): the cheap model returned related-but-not-entailing
passages. The fix is two-stage, gate-before-wire:

  stage 1 (cleanup model, batch 40, one headless session per document, DD-019): PROPOSE a
      verbatim passage for each nulled attribute. Proposals whose passage is not a verbatim
      document substring are dropped mechanically. 2% must_be_none decoys per batch; a decoy
      miss halts the run; cache-read ratio checked on the first 3 calls.
  stage 2 (secondary judge model, batch 10 — the probe's second rater): independent
      entailment judgment per proposal, BLIND to stage 1's reasoning (only attribute, value,
      passage are shown). Only `entailed` proposals become `attribute_restored` events.

Events land in the TAGGED shard events/batch-014_restoration_v2.jsonl (attribute_restored /
restoration_rejected, purpose restoration_v2) — tagged shards are never replayed into the
graph, so NOTHING projects until a `restoration_class_accepted` event (written by the
driver after the 100-restoration acceptance sample passes ≥ 0.90) unlocks the class in
build_projection.py.

Scope: every open attribute_nulled overlay plus the deferred filled-attr worklist,
INCLUDING keys the reversed v1 class had "restored" (their events are void); Instrument
attributes are excluded entirely (Lane 2 re-extracts that stratum — repairing it is wasted
spend).

Usage:
    /opt/anaconda3/bin/python3 scripts/restoration_v2.py --stage 1|2 \
        --ceiling-tokens N [--run-id R] [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog, spend                             # noqa: E402
from kg.extraction import model_stub                       # noqa: E402
from kg.extraction.grounding import normalize              # noqa: E402
import run_bulk_extraction as rbe                          # noqa: E402
import batch_repair as br                                  # noqa: E402
from repair_relocate import locate_loose                   # noqa: E402

TASK = "cc_tasks/2026-08-26_overnight_burn.md"
SHARD_NO, SHARD_TAG = 14, "restoration_v2"
PROPOSALS = REPO / "corpus/staging/metrics/restoration_v2_proposals.jsonl"
ENTAIL_TEMPLATE = REPO / "kg/extraction/restoration_entailment_template.md"
STAGE2_BATCH = 10
SUMMARY = REPO / "corpus/staging/metrics/restoration_v2_summary.json"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def entailment_version() -> str:
    for line in ENTAIL_TEMPLATE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*restoration_entailment_version:\s*(\S+)", line)
        if m:
            return m.group(1)
    raise model_stub.ModelConfigError("no restoration_entailment_version header")


def key_types() -> dict[tuple[str, str], str]:
    """(doc_id, item_id) -> node type, from the detection worklists (for the Instrument
    exclusion; keys absent from both files stay includable)."""
    out = {}
    for path in (br.ATTR_WORK, br.SPAN_WORK):
        for l in path.read_text().splitlines():
            if l.strip():
                w = json.loads(l)
                out[(w["doc_id"], w["item_id"])] = w.get("type")
    return out


def build_worklist() -> list[dict]:
    """Nulled attributes to re-adjudicate. Unlike batch_repair.build_worklist, keys touched
    only by the REVERSED v1 restoration class are still open (its events are void), and any
    v2 event (tagged shard) closes its key."""
    _, _, nulled, _ = br.live_state()
    v2_done = {(ev["doc_id"], ev["item_id"], ev["attribute"])
               for ev in eventlog.replay(tag=SHARD_TAG)
               if ev.get("event_type") in ("attribute_restored", "restoration_rejected")}
    ktypes = key_types()
    tasks, seen = [], set()
    for (d, i, a), old in nulled.items():
        seen.add((d, i, a))
        if (d, i, a) in v2_done or ktypes.get((d, i)) == "Instrument":
            continue
        tasks.append({"kind": "attribute", "id": f"a::{d}::{i}::{a}", "doc_id": d,
                      "item_id": i, "attribute": a, "value": old, "type": ktypes.get((d, i))})
    for l in br.ATTR_WORK.read_text().splitlines():
        if not l.strip():
            continue
        w = json.loads(l)
        k3 = (w["doc_id"], w["item_id"], w["attribute"])
        if k3 in seen or k3 in v2_done or w.get("type") == "Instrument":
            continue
        seen.add(k3)
        tasks.append({"kind": "attribute", "id": f"a::{w['doc_id']}::{w['item_id']}::{w['attribute']}",
                      "doc_id": w["doc_id"], "item_id": w["item_id"],
                      "attribute": w["attribute"], "value": w["value"], "type": w.get("type")})
    return [t for t in tasks if t["value"] not in (None, "", [], {})]


def load_proposals() -> list[dict]:
    if not PROPOSALS.exists():
        return []
    return [json.loads(l) for l in PROPOSALS.read_text().splitlines() if l.strip()]


def stage1(a, cfg, ledger, run_id) -> int:
    """Propose passages (cleanup model, batched by document, session resume, decoys)."""
    tasks = build_worklist()
    proposed = {(p["doc_id"], p["item_id"], p["attribute"]) for p in load_proposals()}
    tasks = [t for t in tasks if (t["doc_id"], t["item_id"], t["attribute"]) not in proposed]
    if a.limit:
        tasks = tasks[:a.limit]
    by_doc = defaultdict(list)
    for t in tasks:
        by_doc[t["doc_id"]].append(t)
    print(f"stage 1: {len(tasks)} open attributes over {len(by_doc)} docs", flush=True)
    if a.dry_run:
        return 0
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    tpl = br.TEMPLATE.read_text(encoding="utf-8")
    tv = br.template_version()
    rng = random.Random(f"restoration_v2:{a.run_id}")
    counts = Counter(); call_no = 0; ratio_log = []
    out = PROPOSALS.open("a", encoding="utf-8")
    for doc_id in sorted(by_doc, key=lambda d: len(by_doc[d]), reverse=True):
        if doc_id not in members:
            counts["doc_not_in_corpus"] += len(by_doc[doc_id]); continue
        doc_norm = normalize(rbe.doc_text(members[doc_id]))
        doc_session = None
        doc_tasks = by_doc[doc_id]
        for b in range(0, len(doc_tasks), br.BATCH_TARGET):
            batch = doc_tasks[b:b + br.BATCH_TARGET]
            n_dec = max(1, round(len(batch) * br.DECOY_RATE))
            decoys = br.make_decoys(rng, doc_id, doc_norm, n_dec, [])
            items = batch + decoys
            rng.shuffle(items)
            payload = [{k: t[k] for k in ("kind", "id", "item_text", "attribute", "value") if k in t}
                       for t in items]
            items_json = json.dumps(payload, ensure_ascii=False, indent=1)
            if doc_session is None:
                prompt = (tpl.replace("{{document_id}}", doc_id)
                            .replace("{{document_text}}", doc_norm[:250_000])
                            .replace("{{items_json}}", items_json))
            else:
                prompt = ("Next batch of tasks against the SAME document, same contract, "
                          "same output format:\n" + items_json)
            call_no += 1
            try:
                meta = model_stub.invoke(f"restv2:{call_no:04d}", "", prompt=prompt,
                                         timeout=900, config=cfg, resume_session_id=doc_session)
            except spend.SpendRefusalStop as exc:
                print(f"spend guard: {exc} — clean stop", flush=True)
                counts["ceiling_stop"] = 1
                out.close(); _write_summary(counts, run_id, "stage1")
                return 0
            except model_stub.ModelRateLimitError:
                raise                                     # driver owns backoff policy
            except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError) as exc:
                counts["call_error"] += 1
                print(f"  call {call_no}: ERROR {str(exc)[:100]}", flush=True)
                doc_session = None
                continue
            doc_session = meta.get("session_id") or doc_session
            u = meta.get("usage") or {}
            cr, cw, inp = (int(u.get(k, 0) or 0) for k in
                           ("cacheReadInputTokens", "cacheCreationInputTokens", "inputTokens"))
            ratio_log.append((cr, cw, inp))
            if call_no == 3 and not (cr > cw and cr > inp):
                print("BINDING COST RULE STOP: cache reads not dominant by call 3", flush=True)
                counts["cache_ratio_stop"] = 1
                out.close(); _write_summary(counts, run_id, "stage1")
                return 3
            rows = meta["output"] if isinstance(meta["output"], list) else \
                (meta["output"].get("results") or [])
            got = {r.get("id"): r for r in rows if isinstance(r, dict)}
            if len(got) < len(items):
                for r in br.salvage_rows(meta["raw_result"] or ""):
                    got.setdefault(r["id"], r)
            for t in items:
                r = got.get(t["id"])
                if t.get("decoy"):
                    ok = bool(r) and str(r.get("verdict")).upper() in ("NONE", "STAYS_NULL")
                    counts["decoy_ok" if ok else "decoy_MISS"] += 1
                    if not ok:
                        print(f"  DECOY MISS call {call_no} — halting for diagnosis", flush=True)
                        out.close(); _write_summary(counts, run_id, "stage1")
                        return 3
                    continue
                if not r:
                    counts["missing_in_reply"] += 1; continue
                passage = r.get("passage")
                verdict = str(r.get("verdict") or "").lower()
                if verdict != "supported" or not passage:
                    counts["stage1_none"] += 1; continue
                np_ = normalize(str(passage))
                hit = np_ if np_ in doc_norm else locate_loose(np_, doc_norm)
                if not hit:
                    counts["stage1_nonverbatim"] += 1; continue
                counts["proposed"] += 1
                out.write(json.dumps({"doc_id": t["doc_id"], "item_id": t["item_id"],
                                      "attribute": t["attribute"], "value": t["value"],
                                      "type": t.get("type"), "passage": hit,
                                      "stage1_model": cfg["model_id"],
                                      "stage1_call": call_no, "ts": _now()},
                                     ensure_ascii=False) + "\n")
                out.flush()
            if call_no % 10 == 0:
                print(f"  {call_no} calls | committed {ledger.committed(run_id):,} | {dict(counts)}",
                      flush=True)
    out.close()
    _write_summary(counts, run_id, "stage1")
    print("stage 1 done:", dict(counts))
    return 0


def stage2(a, cfg, ledger, run_id) -> int:
    """Independent entailment judgments; entailed -> attribute_restored (tagged shard)."""
    ev_version = entailment_version()
    judged = {(ev["doc_id"], ev["item_id"], ev["attribute"])
              for ev in eventlog.replay(tag=SHARD_TAG)
              if ev.get("event_type") in ("attribute_restored", "restoration_rejected")}
    proposals = [p for p in load_proposals()
                 if (p["doc_id"], p["item_id"], p["attribute"]) not in judged]
    # blind stage: only attribute, value, passage cross the boundary
    if a.limit:
        proposals = proposals[:a.limit]
    print(f"stage 2: {len(proposals)} proposals to judge", flush=True)
    if a.dry_run:
        return 0
    tpl = ENTAIL_TEMPLATE.read_text(encoding="utf-8")
    counts = Counter()
    s2_cfg = {**cfg, "model_id": cfg["secondary_judge_model_id"]}
    for b in range(0, len(proposals), STAGE2_BATCH):
        batch = proposals[b:b + STAGE2_BATCH]
        payload = [{"id": f"p{j}", "attribute": p["attribute"], "value": p["value"],
                    "passage": p["passage"]} for j, p in enumerate(batch)]
        prompt = tpl.replace("{{items_json}}", json.dumps(payload, ensure_ascii=False, indent=1))
        try:
            meta = model_stub.invoke(f"restv2judge:{b:05d}", "", prompt=prompt,
                                     timeout=600, config=s2_cfg)
        except spend.SpendRefusalStop as exc:
            print(f"spend guard: {exc} — clean stop", flush=True)
            counts["ceiling_stop"] = 1
            break
        except model_stub.ModelRateLimitError:
            raise
        except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError) as exc:
            counts["call_error"] += 1
            print(f"  batch@{b}: ERROR {str(exc)[:100]}", flush=True)
            continue
        if b < 3 * STAGE2_BATCH:
            u = meta.get("usage") or {}
            print(f"CACHE stage2 call {b // STAGE2_BATCH + 1}: "
                  f"read {int(u.get('cacheReadInputTokens', 0) or 0):,} "
                  f"write {int(u.get('cacheCreationInputTokens', 0) or 0):,} "
                  f"input {int(u.get('inputTokens', 0) or 0):,} "
                  f"(fresh judge batches: no shared prefix expected — logged per ADDENDUM-02, not gated)",
                  flush=True)
        rows = meta["output"] if isinstance(meta["output"], list) else \
            (meta["output"].get("results") or meta["output"].get("judgments") or [])
        got = {r.get("id"): r for r in rows if isinstance(r, dict)}
        for j, p in enumerate(batch):
            r = got.get(f"p{j}")
            verdict = str((r or {}).get("verdict") or "").lower()
            common = {"doc_id": p["doc_id"], "item_id": p["item_id"],
                      "attribute": p["attribute"], "value": p["value"],
                      "supporting_passage": p["passage"], "purpose": SHARD_TAG,
                      "stage1_model": p.get("stage1_model"),
                      "stage2_model": s2_cfg["model_id"],
                      "entailment_version": ev_version,
                      "restoration_class": "restoration_v2", "task": TASK}
            if verdict == "entailed":
                eventlog.append({"event_type": "attribute_restored", **common},
                                batch=SHARD_NO, tag=SHARD_TAG)
                counts["restored"] += 1
            else:
                eventlog.append({"event_type": "restoration_rejected", **common,
                                 "stage2_verdict": verdict or "missing"},
                                batch=SHARD_NO, tag=SHARD_TAG)
                counts["rejected"] += 1
        if (b // STAGE2_BATCH) % 10 == 0:
            print(f"  {b + len(batch)}/{len(proposals)} | {dict(counts)}", flush=True)
    _write_summary(counts, run_id, "stage2")
    print("stage 2 done:", dict(counts))
    return 0


def _write_summary(counts: Counter, run_id: str, stage: str) -> None:
    prev = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
    prev[stage] = {**dict(counts), "run_id": run_id, "ts": _now()}
    SUMMARY.write_text(json.dumps(prev, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["1", "2"], required=True)
    ap.add_argument("--ceiling-tokens", type=int, required=True,
                    help="per-run token ceiling from the task file (required; no default)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    model_stub.guard_no_api_key()
    # one run id per stage: the two stages carry different call classes, and a declare with
    # a conflicting class is (correctly) refused by the ledger
    run_id = a.run_id or spend.default_run_id(f"restoration-v2-s{a.stage}")
    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens, declared_by="scripts/restoration_v2.py",
                   call_class="cleanup" if a.stage == "1" else "judge")
    spend.set_current_run(run_id)
    cfg = model_stub.load_model_config()
    if a.stage == "1":
        if not cfg.get("cleanup_model_id"):
            raise SystemExit("FATAL: no cleanup_model_id in model_config.yaml (DD-006)")
        return stage1(a, {**cfg, "model_id": cfg["cleanup_model_id"]}, ledger, run_id)
    if not cfg.get("secondary_judge_model_id"):
        raise SystemExit("FATAL: no secondary_judge_model_id in model_config.yaml (DD-015)")
    return stage2(a, cfg, ledger, run_id)


if __name__ == "__main__":
    raise SystemExit(main())
