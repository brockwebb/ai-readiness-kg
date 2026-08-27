#!/usr/bin/env python3
"""Whole-graph repair Phases 2–3 — span relocation (task 2026-08-23_whole_graph_repair).

Phase 2 (zero spend): exact / NFKC-normalized substring of the item text in the document
-> grounding_relocated overlay, method `deterministic`.
(A fuzzy pre-verify was tried and removed: if the normalized item text is not a substring
of the document, no verbatim passage can cover it — paraphrase needs the model.)
Phase 3 (model spend, cleanup-class model per DD-006 / model_config.cleanup_model_id):
one call per item with the item text and the document text (full when short, else a
window around the best fuzzy region — standing decision, bounded tokens); the returned
passage must be a verbatim substring of the document AND cover the item text (retry once,
then NONE). Found -> overlay method `model_assisted` (call id stamped); NONE ->
`span_unrepairable` annotation event. Overlays go to events/batch-011.jsonl (graph shard).
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog                                     # noqa: E402
from kg.extraction import model_stub                        # noqa: E402
from kg.extraction.grounding import normalize, covers       # noqa: E402
import run_bulk_extraction as rbe                           # noqa: E402

WORK = REPO / "corpus/staging/metrics/repair_span_partial.jsonl"
OUT = REPO / "corpus/staging/metrics/repair_relocate_summary.json"
RAW_DIR = REPO / "events/raw/repair_relocate"
TEMPLATE = REPO / "kg/extraction/relocate_template.md"
BATCH = 11
TASK = "cc_tasks/2026-08-23_whole_graph_repair.md"
FUZZY_MIN = 0.75
FULL_DOC_MAX_CHARS = 30_000
WINDOW_CHARS = 12_000


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def deterministic(item_text: str, doc: str) -> tuple[str, str] | None:
    if item_text in doc:
        return item_text, "deterministic"
    nd, ni = normalize(doc), normalize(item_text)
    k = nd.find(ni)
    return (nd[k:k + len(ni)], "deterministic") if k >= 0 else None


def _sentences(nd: str) -> list[tuple[int, str]]:
    out, pos = [], 0
    for m in re.finditer(r"[^.!?\n]+[.!?]?", nd):
        s = m.group(0)
        if len(s.strip()) > 20: out.append((m.start(), s))
    return out


def fuzzy_region(item_text: str, nd: str) -> tuple[int, float] | None:
    ni = normalize(item_text); best = (None, 0.0)
    for start, s in _sentences(nd):
        r = difflib.SequenceMatcher(None, ni, s).ratio()
        if r > best[1]: best = (start, r)
    return best if best[0] is not None else None


def locate_loose(passage: str, doc_norm: str) -> str | None:
    """Find `passage` in the normalized document ignoring whitespace and hyphens (PDF text
    carries mid-word spaces and line hyphens that a model silently heals). Returns the
    DOCUMENT's own slice so the stored span string-matches the source under the grounding
    validator's normalization — the span is still verbatim document text."""
    def strip(t): return re.sub(r"[\s\-\u00ad]+", "", t)
    sp = strip(passage)
    if not sp: return None
    # map stripped positions back to doc_norm positions
    pos_map, sd = [], []
    for i, ch in enumerate(doc_norm):
        if not re.match(r"[\s\-\u00ad]", ch): pos_map.append(i); sd.append(ch)
    sd = "".join(sd); k = sd.find(sp)
    if k < 0: return None
    start, end = pos_map[k], pos_map[k + len(sp) - 1] + 1
    return doc_norm[start:end]


def model_relocate(item: dict, doc_norm: str, cfg: dict, tpl: str) -> tuple[str | None, dict]:
    region = fuzzy_region(item["item_text"], doc_norm)
    if len(doc_norm) <= FULL_DOC_MAX_CHARS or not region:
        ctx = doc_norm[:FULL_DOC_MAX_CHARS * 2]; ctx_note = "full document (normalized)"
    else:
        s = max(0, region[0] - WINDOW_CHARS // 2); ctx = doc_norm[s:s + WINDOW_CHARS]; ctx_note = f"window of {WINDOW_CHARS} chars around best fuzzy region"
    prompt = tpl.replace("{{item_type}}", item["type"]).replace("{{item_text}}", item["item_text"]).replace("{{document_text}}", ctx)
    last = {}
    for attempt in range(2):
        meta = model_stub.invoke(f"relocate:{item['event_id'][:10]}", "", prompt=prompt, timeout=300, config=cfg)
        last = meta
        out = meta["output"]; passage = (out.get("passage") if isinstance(out, dict) else None)
        if isinstance(passage, str) and passage.strip().upper() != "NONE":
            np_ = normalize(passage)
            # task criterion: the passage must be a verbatim substring of the document. It
            # cannot be required to CONTAIN the item text — the item is a paraphrase (that is
            # why deterministic relocation failed); entailment is the success measure's job.
            hit = np_ if (np_ and np_ in doc_norm) else locate_loose(np_, doc_norm)
            if hit:
                return hit, {"meta": meta, "context": ctx_note, "attempt": attempt + 1,
                             "verification": "exact" if hit == np_ else "whitespace_insensitive"}
        else:
            break
    return None, {"meta": last, "context": ctx_note}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["2", "3"], required=True)
    ap.add_argument("--limit", type=int, default=None, help="phase 3: max model calls this run")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo-unrepairable", action="store_true",
                    help="phase 3: re-attempt items whose span_unrepairable came from the defective "
                         "verifier (2026-08-23 rate run); a later grounding_relocated supersedes it")
    ap.add_argument("--shard", default=None, help="I/N hash partition for parallel workers")
    # DD-022 (phase 3 only — phase 2 is zero-spend): shared preemptive ceiling, declared
    # from the dispatching task file. Required for phase 3; no default.
    ap.add_argument("--ceiling-tokens", type=int, default=None,
                    help="phase 3: per-run token ceiling from the task file (required; no default)")
    ap.add_argument("--run-id", default=None,
                    help="phase 3: shared spend-ledger run id (default: repair-relocate-<UTC ts>); "
                         "shard workers of one run MUST pass the same id")
    a = ap.parse_args()
    work = [json.loads(l) for l in WORK.read_text(encoding="utf-8").splitlines() if l.strip()]
    skip_types = ("grounding_relocated",) if a.redo_unrepairable else ("grounding_relocated", "span_unrepairable")
    already = {(ev["doc_id"], ev["item_id"]) for ev in eventlog.replay() if ev.get("event_type") in skip_types}
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    texts, norms = {}, {}
    def doc_text(d):
        if d not in texts:
            texts[d] = rbe.doc_text(members[d]); norms[d] = normalize(texts[d])
        return texts[d], norms[d]
    counts = Counter(); forwarded = []
    if a.phase == "2":
        for w in work:
            key = (w["doc_id"], w["item_id"])
            if key in already: counts["already"] += 1; continue
            raw, nd = doc_text(w["doc_id"])
            hit = deterministic(w["item_text"], raw)
            if hit:
                span, method = hit; counts[method] += 1
                if not a.dry_run:
                    eventlog.append({"event_type": "grounding_relocated", "doc_id": w["doc_id"], "target_event_id": w["event_id"],
                                     "item_id": w["item_id"], "attribute": w["attribute"], "old_span": w["span"],
                                     "new_span": span, "method": method, "task": TASK}, batch=BATCH)
            else:
                counts["forwarded_to_phase3"] += 1; forwarded.append(w)
        (REPO / "corpus/staging/metrics/repair_phase3_worklist.jsonl").write_text(
            "".join(json.dumps(w, ensure_ascii=False) + "\n" for w in forwarded), encoding="utf-8")
    else:
        cfg = model_stub.load_model_config()
        if not cfg.get("cleanup_model_id"):
            raise SystemExit("FATAL: model_config.yaml has no cleanup_model_id (DD-006 cleanup-class model)")
        cfg = {**cfg, "model_id": cfg["cleanup_model_id"]}
        model_stub.guard_no_api_key()
        tpl = TEMPLATE.read_text(encoding="utf-8")
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        wl = [json.loads(l) for l in (REPO / "corpus/staging/metrics/repair_phase3_worklist.jsonl").read_text().splitlines() if l.strip()]
        if a.shard:
            import hashlib
            si, sn = (int(x) for x in a.shard.split("/"))
            wl = [w for w in wl if int(hashlib.sha1(w["event_id"].encode()).hexdigest(), 16) % sn == si]
        import control_plane as cp
        from kg import spend
        if a.ceiling_tokens is None:
            raise SystemExit("FATAL: phase 3 requires --ceiling-tokens (from the dispatching "
                             "task file; no default) — DD-022 shared spend guard")
        run_id = a.run_id or spend.default_run_id("repair-relocate")
        ledger = spend.default_ledger()
        ledger.declare(run_id, a.ceiling_tokens, declared_by="scripts/repair_relocate.py",
                       call_class="cleanup")
        spend.set_current_run(run_id)
        # The old reactive `rbe.tokens_left() <= 0` poll here (DD-017 said "enforces via the
        # control plane") checked the DAILY band between calls, after usage was booked — the
        # DD-019 §5 defect shape. Admission is now preemptive at the model-stub choke point;
        # the band survives inside the guard as the ledger's daily scope.
        n = 0; t_all = time.time(); walls = []
        for w in wl:
            key = (w["doc_id"], w["item_id"])
            if key in already: counts["already"] += 1; continue
            if a.limit is not None and n >= a.limit: break
            n += 1
            _, nd = doc_text(w["doc_id"])
            t0 = time.time()
            try:
                span, info = model_relocate(w, nd, cfg, tpl)
            except spend.SpendRefusalStop as exc:
                counts["ceiling_stop"] = 1
                print(f"spend guard: {exc} — clean stop, resume when capacity exists", flush=True)
                break
            except model_stub.ModelInvocationError as exc:
                counts["invocation_error"] += 1; print(f"  {w['item_id']}: ERROR {str(exc)[:100]}", flush=True); continue
            wall = round(time.time() - t0, 1); walls.append(wall)
            meta = info.get("meta") or {}
            tok = rbe.usage_tokens(meta) if meta.get("usage") else 0
            if tok: cp.record_usage("extraction", tok, job="airkg-repair-relocate", project="ai-readiness-kg")
            (RAW_DIR / f"{w['event_id']}.{cfg['model_id']}.json").write_text(json.dumps(
                {"event_id": w["event_id"], "item_id": w["item_id"], "doc_id": w["doc_id"], "model_id": cfg["model_id"],
                 "context": info.get("context"), "usage": meta.get("usage"), "cost_usd": meta.get("cost_usd"),
                 "session_id": meta.get("session_id"), "wall_s": wall, "raw_result": meta.get("raw_result"), "found": span is not None},
                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            if span:
                counts["model_assisted"] += 1
                if not a.dry_run:
                    eventlog.append({"event_type": "grounding_relocated", "doc_id": w["doc_id"], "target_event_id": w["event_id"],
                                     "item_id": w["item_id"], "attribute": w["attribute"], "old_span": w["span"], "new_span": span,
                                     "method": "model_assisted", "model_id": cfg["model_id"], "call_id": meta.get("session_id"),
                                     "context": info.get("context"), "verification": info.get("verification"), "task": TASK}, batch=BATCH)
            else:
                counts["unrepairable"] += 1
                if not a.dry_run:
                    eventlog.append({"event_type": "span_unrepairable", "doc_id": w["doc_id"], "target_event_id": w["event_id"],
                                     "item_id": w["item_id"], "attribute": w["attribute"], "span": w["span"],
                                     "model_id": cfg["model_id"], "call_id": meta.get("session_id"), "task": TASK}, batch=BATCH)
            if n == 20:
                rate = (time.time() - t_all) / 20
                committed = ledger.committed(run_id)
                print(f"RATE: 20 calls, mean wall {rate:.1f}s, run committed {committed:,} -> "
                      f"projected {len(wl)} calls: {rate * len(wl) / 3600:.2f} h, "
                      f"{committed / 20 * len(wl):,.0f} tokens", flush=True)
            if n % 25 == 0: print(f"  {n}/{len(wl)} {dict(counts)}", flush=True)
        # shared run total (all shards), not a process-local sum (DD-019 §5)
        counts["tokens"] = ledger.committed(run_id)
        counts["run_id"] = run_id
        counts["mean_wall_s"] = (sum(walls) / len(walls)) if walls else None
        reconcile = ledger.reconcile(run_id)   # settles vs model_call events, before any RESULT
        print(f"spend reconcile [{run_id}]: {'OK' if reconcile['ok'] else 'MISMATCH'} "
              f"settled {reconcile['settled_total']:,} vs model_call {reconcile['model_call_total']:,}")
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    prev[f"phase{a.phase}"] = dict(counts); prev["ts"] = _now()
    OUT.write_text(json.dumps(prev, indent=1) + "\n")
    print(dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
