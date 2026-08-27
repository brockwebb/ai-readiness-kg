#!/usr/bin/env python3
"""Batched repair resume — Phase 2 engine (task 2026-08-23_batched_repair_resume, Seldon
a2d3fb42; DD-019 binding cost rule).

Dispatch unit = the batch (target 40 items, floor 25, ceiling 50), grouped BY DOCUMENT with
the document text ahead of the items so consecutive batches on one document share a cached
prefix. No tools on calls (model_stub already passes an empty allowlist; hermetic cwd).
2% planted decoys per batch (synthetic-unsupported must return NONE/stays_null;
known-supported must return found) with a rolling 200 acceptance window per shard — a decoy
miss halts the shard for diagnosis. Cache-read vs cache-write ratio measured on the first 3
calls; cache reads must be dominant by call 3 or the run STOPS for prefix diagnosis.
Token ceiling 12M (control-plane recorded); sharded and resumable.

Worklists (from live repair state):
  relocate  : span_partial entries with neither grounding_relocated nor a NON-superseded
              span_unrepairable... under --redo-unrepairable prior NONEs are re-asked.
  attribute : attribute_nulled overlays (re-adjudication) + deferred filled_attr entries,
              in dependency order (an item's relocation verdict lands before its attributes).

Writes: grounding_relocated (method model_assisted_batch) / attribute_restored /
span_unrepairable to events/batch-012.jsonl. attribute_restored supersedes the null;
confirmed nulls write nothing.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog, spend                             # noqa: E402
from kg.extraction import model_stub                       # noqa: E402
from kg.extraction.grounding import normalize              # noqa: E402
import run_bulk_extraction as rbe                          # noqa: E402
from repair_relocate import locate_loose                   # noqa: E402
import control_plane as cp                                 # noqa: E402

SPAN_WORK = REPO / "corpus/staging/metrics/repair_span_partial.jsonl"
ATTR_WORK = REPO / "corpus/staging/metrics/repair_filled_attr.jsonl"
TEMPLATE = REPO / "kg/extraction/batch_repair_template.md"
RAW_DIR = REPO / "events/raw/batch_repair"
OUT = REPO / "corpus/staging/metrics/batch_repair_summary.json"
BATCH_EVENTS = 12
TASK = "cc_tasks/2026-08-23_batched_repair_resume.md"
BATCH_TARGET, BATCH_FLOOR, BATCH_CEIL = 40, 25, 50
DECOY_RATE = 0.02
# The process-local TOKEN_CEILING that used to live here is the DD-019 §5 defect (two shard
# workers each honored their own 12M and jointly spent 22.03M). The ceiling is now declared
# on the shared ledger (--ceiling-tokens, kg/spend.py) and enforced preemptively at the
# model-stub choke point. Deleted, not disabled — two mechanisms is how the 22M happened.
SEED = 20260823


def template_version() -> str:
    for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*batch_repair_version:\s*(\S+)", line)
        if m: return m.group(1)
    raise model_stub.ModelConfigError("no batch_repair_version header")


def live_state() -> tuple[dict, set, dict, set]:
    reloc, unrep, nulled, restored = {}, set(), {}, set()
    for ev in eventlog.replay():
        et = ev.get("event_type"); key = (ev.get("doc_id"), ev.get("item_id"))
        if et == "grounding_relocated": reloc[key] = ev["new_span"]
        elif et == "span_unrepairable": unrep.add(key)
        elif et == "attribute_nulled": nulled[(key[0], key[1], ev["attribute"])] = ev.get("old_value")
        elif et == "attribute_restored": restored.add((key[0], key[1], ev["attribute"]))
    return reloc, unrep, nulled, restored


def build_worklist(redo_unrepairable: bool) -> list[dict]:
    reloc, unrep, nulled, restored = live_state()
    tasks = []
    for l in SPAN_WORK.read_text().splitlines():
        if not l.strip(): continue
        w = json.loads(l); key = (w["doc_id"], w["item_id"])
        if key in reloc: continue
        if key in unrep and not redo_unrepairable: continue
        tasks.append({"kind": "relocate", "id": f"r::{w['event_id']}", "doc_id": w["doc_id"],
                      "item_id": w["item_id"], "event_id": w["event_id"], "attribute": w["attribute"],
                      "item_text": w["item_text"], "old_span": w["span"]})
    # attribute re-adjudication: all nulls not yet restored + deferred entries
    seen = set()
    for (d, i, a), old in nulled.items():
        if (d, i, a) in restored or (d, i, a) in seen: continue
        seen.add((d, i, a))
        tasks.append({"kind": "attribute", "id": f"a::{d}::{i}::{a}", "doc_id": d, "item_id": i,
                      "attribute": a, "value": old})
    for l in ATTR_WORK.read_text().splitlines():
        if not l.strip(): continue
        w = json.loads(l); k3 = (w["doc_id"], w["item_id"], w["attribute"])
        if k3 in seen or k3 in restored or k3 in {(d, i, a) for (d, i, a) in nulled}: continue
        seen.add(k3)
        tasks.append({"kind": "attribute", "id": f"a::{w['doc_id']}::{w['item_id']}::{w['attribute']}",
                      "doc_id": w["doc_id"], "item_id": w["item_id"], "attribute": w["attribute"], "value": w["value"]})
    return tasks


def salvage_rows(text: str) -> list[dict]:
    """Recover every individually-valid {...} row from a reply whose enclosing array is
    malformed (observed: one row with an unquoted `"A" and "B"` passage kills the array).
    Balanced-brace scan; keep dicts that parse and carry an id."""
    rows, i, n = [], 0, len(text)
    while i < n:
        if text[i] == "{":
            depth, j, in_str, esc = 0, i, False, False
            while j < n:
                ch = text[j]
                if in_str:
                    if esc: esc = False
                    elif ch == "\\": esc = True
                    elif ch == '"': in_str = False
                else:
                    if ch == '"': in_str = True
                    elif ch == "{": depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                obj = json.loads(text[i:j + 1])
                                if isinstance(obj, dict) and obj.get("id"):
                                    rows.append(obj)
                            except json.JSONDecodeError:
                                pass
                            i = j
                            break
                j += 1
        i += 1
    return rows


def make_decoys(rng: random.Random, doc_id: str, doc_norm: str, n: int, known_pool: list[dict]) -> list[dict]:
    out = []
    for j in range(n):
        if j % 2 == 0 or not known_pool:
            out.append({"kind": "relocate", "id": f"decoy_none::{doc_id}::{rng.randrange(10**9)}",
                        "item_text": rng.choice([
                            "The committee voted 7-2 to adopt quantum blockchain telemetry for all field offices.",
                            "Penguins were selected as the reference species for the annual latency audit.",
                            "This standard mandates the use of carrier pigeons for bulk data distribution."]),
                        "decoy": "must_be_none"})
        else:
            k = rng.choice(known_pool)
            out.append({"kind": "relocate", "id": f"decoy_known::{doc_id}::{rng.randrange(10**9)}",
                        "item_text": k["text"], "decoy": "must_be_found", "true_passage": k["span"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--redo-unrepairable", action="store_true")
    ap.add_argument("--max-batches", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ceiling-tokens", type=int, required=True,
                    help="per-run token ceiling from the dispatching task file (required; no default)")
    ap.add_argument("--run-id", default=None,
                    help="shared spend-ledger run id (default: batch-repair-<UTC ts>); "
                         "shard workers of one run MUST pass the same id")
    a = ap.parse_args()
    run_id = a.run_id or spend.default_run_id("batch-repair")
    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens, declared_by="scripts/batch_repair.py",
                   call_class="cleanup")
    spend.set_current_run(run_id)
    model_stub.guard_no_api_key()
    cfg = model_stub.load_model_config()
    cfg = {**cfg, "model_id": cfg["cleanup_model_id"]}
    tv = template_version(); tpl = TEMPLATE.read_text(encoding="utf-8")
    tasks = build_worklist(a.redo_unrepairable)
    si, sn = (int(x) for x in a.shard.split("/"))
    by_doc = defaultdict(list)
    for t in tasks:
        if int(hashlib.sha1(t["doc_id"].encode()).hexdigest(), 16) % sn == si:
            by_doc[t["doc_id"]].append(t)
    total = sum(len(v) for v in by_doc.values())
    print(f"shard {a.shard}: {total} tasks over {len(by_doc)} docs "
          f"(relocate {sum(1 for v in by_doc.values() for t in v if t['kind']=='relocate')}, "
          f"attribute {sum(1 for v in by_doc.values() for t in v if t['kind']=='attribute')})", flush=True)
    if a.dry_run:
        return 0
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    # known-supported decoy pool: deterministic relocations (true passage known)
    known = defaultdict(list)
    for ev in eventlog.replay():
        if ev.get("event_type") == "grounding_relocated" and ev.get("method") == "deterministic":
            known[ev["doc_id"]].append({"text": ev["new_span"], "span": ev["new_span"]})
    rng = random.Random(f"{SEED}:{a.shard}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    counts = Counter(); call_no = 0
    decoy_window = deque(maxlen=200); halted = False
    ratio_log = []
    for doc_id in sorted(by_doc, key=lambda d: len(by_doc[d]), reverse=True):
        if halted: break
        doc_tasks = by_doc[doc_id]
        raw_text = rbe.doc_text(members[doc_id]); doc_norm = normalize(raw_text)
        doc_session = None       # one session per document; batches resume it (DD-019)
        for b in range(0, len(doc_tasks), BATCH_TARGET):
            if halted: break
            if a.max_batches is not None and call_no >= a.max_batches:
                halted = True; counts["max_batches_stop"] = 1; break
            batch = doc_tasks[b:b + BATCH_TARGET]
            n_dec = max(1, round(len(batch) * DECOY_RATE))
            decoys = make_decoys(rng, doc_id, doc_norm, n_dec, known.get(doc_id, []))
            items = batch + decoys
            rng.shuffle(items)
            payload = [{k: t[k] for k in ("kind", "id", "item_text", "attribute", "value") if k in t} for t in items]
            items_json = json.dumps(payload, ensure_ascii=False, indent=1)
            if doc_session is None:
                prompt = (tpl.replace("{{document_id}}", doc_id)
                            .replace("{{document_text}}", doc_norm[:250_000])
                            .replace("{{items_json}}", items_json))
            else:      # resumed turn: document already in the session; send only the tasks
                prompt = ("Next batch of tasks against the SAME document, same contract, "
                          "same output format:\n" + items_json)
            call_no += 1
            bid = f"br.{a.shard.replace('/','of')}.{call_no:04d}"
            try:
                meta = model_stub.invoke(f"batchrepair:{bid}", "", prompt=prompt, timeout=900,
                                         config=cfg, resume_session_id=doc_session)
            except spend.SpendRefusalStop as exc:
                # Preemptive shared ceiling (DD-022): refused BEFORE dispatch — clean stop.
                counts["ceiling_stop"] = 1
                print(f"spend guard: {exc} — clean stop", flush=True)
                halted = True; break
            except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError) as exc:
                counts["call_error"] += 1; print(f"  {bid}: ERROR {str(exc)[:100]}", flush=True)
                doc_session = None      # dead session: next batch re-establishes with the doc
                continue
            doc_session = meta.get("session_id") or doc_session
            u = meta.get("usage") or {}
            tok = rbe.usage_tokens(meta)
            cp.record_usage("extraction", tok, job="airkg-batch-repair", project="ai-readiness-kg")
            cr, cw, inp = (int(u.get(k, 0) or 0) for k in ("cacheReadInputTokens", "cacheCreationInputTokens", "inputTokens"))
            ratio_log.append({"call": call_no, "cache_read": cr, "cache_write": cw, "input": inp})
            if call_no <= 3:
                print(f"  CACHE call {call_no}: read {cr:,} write {cw:,} input {inp:,}", flush=True)
            if call_no == 3 and not (cr > cw and cr > inp):
                counts["cache_ratio_stop"] = 1
                print("BINDING COST RULE STOP: cache reads not dominant by call 3 — diagnose prefix.", flush=True)
                halted = True
            (RAW_DIR / f"{bid}.json").write_text(json.dumps(
                {"batch_id": bid, "doc_id": doc_id, "n_items": len(batch), "n_decoys": n_dec,
                 "model_id": cfg["model_id"], "template_version": tv, "usage": u,
                 "cost_usd": meta.get("cost_usd"), "session_id": meta.get("session_id"),
                 "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            out = meta["output"]
            rows = out if isinstance(out, list) else (out.get("results") or out.get("judgments") or [])
            got = {r.get("id"): r for r in rows if isinstance(r, dict)}
            if len(got) < len(items):     # salvage rows an enclosing malformed array dropped
                for r in salvage_rows(meta["raw_result"] or ""):
                    got.setdefault(r["id"], r)
                if len(got) > len(rows):
                    counts["salvaged_rows"] += len(got) - len(rows)

            def lookup(task_id: str):
                """Tolerant id match: exact, else the model's echo with a kind prefix added
                or dropped (observed: decoy id echoed as 'r::<id>'), else unique suffix."""
                if task_id in got:
                    return got[task_id]
                for rid, r in got.items():
                    if not isinstance(rid, str):
                        continue
                    if rid.endswith("::" + task_id) or task_id.endswith("::" + rid)                             or rid == "r::" + task_id or rid == "a::" + task_id:
                        return r
                return None
            if not got and len(items) > 1:
                # parse failure: one retry with the batch split in half (binding rule 1)
                counts["parse_retry_split"] += 1
                for half in (items[:len(items) // 2], items[len(items) // 2:]):
                    hp = ("Next batch of tasks against the SAME document, same contract, same "
                          "output format:\n" + json.dumps(
                              [{k: t[k] for k in ("kind", "id", "item_text", "attribute", "value") if k in t}
                               for t in half], ensure_ascii=False, indent=1))
                    try:
                        m2 = model_stub.invoke(f"batchrepair:{bid}.split", "", prompt=hp, timeout=900,
                                               config=cfg, resume_session_id=doc_session)
                    except spend.SpendRefusalStop as exc:
                        counts["ceiling_stop"] = 1
                        print(f"spend guard: {exc} — clean stop", flush=True)
                        halted = True; break
                    except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError):
                        continue
                    doc_session = m2.get("session_id") or doc_session
                    t2 = rbe.usage_tokens(m2)
                    cp.record_usage("extraction", t2, job="airkg-batch-repair", project="ai-readiness-kg")
                    o2 = m2["output"]; r2 = o2 if isinstance(o2, list) else (o2.get("results") or [])
                    got.update({r.get("id"): r for r in r2 if isinstance(r, dict)})
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for t in items:
                r = lookup(t["id"])
                if t.get("decoy"):
                    ok = bool(r) and ((t["decoy"] == "must_be_none" and str(r.get("verdict")).upper() in ("NONE", "STAYS_NULL"))
                                      or (t["decoy"] == "must_be_found" and r.get("passage")))
                    decoy_window.append(ok); counts["decoy_ok" if ok else "decoy_MISS"] += 1
                    if not ok:
                        print(f"  DECOY MISS in {bid} ({t['decoy']}) — halting shard for diagnosis", flush=True)
                        halted = True
                    continue
                if not r:
                    counts["missing_in_reply"] += 1; continue
                verdict = str(r.get("verdict") or "").lower(); passage = r.get("passage")
                if t["kind"] == "relocate":
                    hit = None
                    if passage and verdict != "none":
                        np_ = normalize(str(passage)); hit = np_ if np_ in doc_norm else locate_loose(np_, doc_norm)
                    if hit:
                        counts["relocated"] += 1
                        eventlog.append({"event_type": "grounding_relocated", "doc_id": doc_id, "target_event_id": t["event_id"],
                                         "item_id": t["item_id"], "attribute": t["attribute"], "old_span": t["old_span"],
                                         "new_span": hit, "method": "model_assisted_batch", "model_id": cfg["model_id"],
                                         "call_id": meta.get("session_id"), "batch_id": bid, "template_version": tv,
                                         "task": TASK}, batch=BATCH_EVENTS)
                    else:
                        counts["unrepairable"] += 1
                        eventlog.append({"event_type": "span_unrepairable", "doc_id": doc_id, "target_event_id": t["event_id"],
                                         "item_id": t["item_id"], "attribute": t["attribute"], "span": t["old_span"],
                                         "model_id": cfg["model_id"], "call_id": meta.get("session_id"), "batch_id": bid,
                                         "method": "model_assisted_batch", "task": TASK}, batch=BATCH_EVENTS)
                else:
                    if verdict == "supported" and passage:
                        np_ = normalize(str(passage)); hit = np_ if np_ in doc_norm else locate_loose(np_, doc_norm)
                        if hit:
                            counts["restored"] += 1
                            eventlog.append({"event_type": "attribute_restored", "doc_id": doc_id, "item_id": t["item_id"],
                                             "attribute": t["attribute"], "value": t["value"], "supporting_passage": hit,
                                             "model_id": cfg["model_id"], "call_id": meta.get("session_id"), "batch_id": bid,
                                             "template_version": tv, "task": TASK}, batch=BATCH_EVENTS)
                        else:
                            counts["stays_null_nonverbatim"] += 1
                    else:
                        counts["stays_null"] += 1
            if call_no % 10 == 0:
                print(f"  {call_no} calls | run committed {ledger.committed(run_id):,} tok "
                      f"| {dict(counts)}", flush=True)
    # `tokens` = the SHARED run's committed total (all shards), not a process-local sum —
    # the per-process number is exactly what mislaid the 22M (DD-019 §5).
    counts["tokens"] = ledger.committed(run_id); counts["calls"] = call_no
    reconcile = ledger.reconcile(run_id)   # settles vs model_call events, before any RESULT
    print(f"spend reconcile [{run_id}]: {'OK' if reconcile['ok'] else 'MISMATCH'} "
          f"settled {reconcile['settled_total']:,} vs model_call {reconcile['model_call_total']:,}")
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    prev[f"shard_{a.shard.replace('/','of')}"] = {**counts, "cache_first3": ratio_log[:3],
                                                  "run_id": run_id}
    OUT.write_text(json.dumps(prev, indent=1) + "\n")
    print(dict(counts))
    # Spend-guard refusal is a CLEAN stop (exit 0, resume when capacity exists) — the same
    # contract as the STOP file; exit 3 stays reserved for diagnostic halts (decoy miss,
    # cache-ratio stop) that need operator review before resuming.
    if counts.get("ceiling_stop"):
        return 0
    return 0 if not halted else 3


if __name__ == "__main__":
    raise SystemExit(main())
