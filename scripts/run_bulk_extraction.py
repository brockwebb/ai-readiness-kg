#!/usr/bin/env python3
"""Bulk extraction v1 runner (task cc_tasks/2026-07-05_airkg_bulk_extraction_v1.md Stage 4).

Corpus: exactly the v1 baseline set — the member_doc_ids of the dixie
`corpus_epoch_declared` epoch=v1 event. Model: pinned per kg/extraction/
model_config.yaml, Max OAuth only (model_stub guards + substitution gate).

Per-document loop:
  budget check (declared caps, bound HERE — project runs admission OBSERVE)
  -> gate() admission record (project-tagged, class deadline)
  -> model_stub.invoke  -> RAW RESPONSE PERSISTED (non-negotiable, S1 finding)
  -> pipeline.extract_document (grounding: ungrounded items quarantined at
     parse, never admitted; provenance stamps + corpus_epoch + source sha256)
  -> record_usage (actual envelope tokens)
  -> per-doc STOP discipline: quarantine_rate > 10% or model substitution
     -> STOP file written; run halts until the operator removes it.

Chunk-resumable: completed docs are detected from batch-004 build_metrics
events; an interrupted run re-fires without re-burning. Cap exhaustion is a
CLEAN NO-OP (exit 0) — the next window resumes automatically (panel day-roll
clears tripped:daily).

Raw-response path convention (alongside events, keyed by doc sha256 + prompt
epoch + model_id): events/raw/bulk_v1/<doc_id>.<sha12>.<prompt_epoch>.<model_id>.json
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path.home() / ".wintermute" / "scripts" / "lib"))

from kg import eventlog                              # noqa: E402
from kg.extraction import model_stub, pipeline, state  # noqa: E402
import control_plane as cp                           # noqa: E402
from dixie.evidence.config import load_config as dixie_config      # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog           # noqa: E402
from dixie.evidence.manifest import build_manifest                 # noqa: E402

# --- run constants (task-declared, not tunables) --------------------------------
CORPUS_EPOCH = "v1"
BULK_BATCH = 4                     # events/batch-004.jsonl — this run's shard
CIRCUIT = "extraction"
PROJECT = "ai-readiness-kg"
JOB = "airkg-extraction-burn"
PRIORITY_CLASS = "deadline"
QUARANTINE_STOP_RATE = 0.10        # pilot v5 pre-registered per-doc STOP (threshold — do NOT retune)
# STOP-trigger scope. "per_doc" (default) = pre-registered behavior: any single doc over
# the threshold halts. "systemic" (opt-in via env, 2026-07-08 boost) = an isolated breach
# is recorded as a finding and the burn continues; it hard-STOPs only when the last
# QUARANTINE_SYSTEMIC_WINDOW consecutive docs ALL exceed the threshold (genuine
# degradation, not one outlier). The 0.10 threshold is unchanged either way.
QUARANTINE_STOP_MODE = os.environ.get("BURN_QUARANTINE_STOP_MODE", "per_doc")
QUARANTINE_SYSTEMIC_WINDOW = 3
MAX_DOC_CHARS = 250_000            # oversize docs are DEFERRED with reason, never truncated
# Per-doc oversize clearances (operator-authorized, ledgered). A named allowlist —
# NOT a raised cap — so genuinely-unfit docs (e.g. mis-acquired enclosing statutes
# that exceed context) keep deferring. Each entry is a single full-context call;
# truncation is still forbidden. Cleared 2026-07-07 by operator: the TRL report is a
# 329k-char JRC technical report (~82k tok), fits one Opus call with grounding intact.
OVERSIZE_ALLOW = {
    "ai-watch-revisiting-technology-readiness-levels-for-relevant",
    # 2026-07-08 boost: two legitimate large reports (fit one Opus call; grounding
    # intact). NOT information-quality-act (2.1M chars = a provision inside a whole
    # statute, almost certainly mis-acquired like the megastatutes — stays deferred
    # pending refetch).
    "arm-ai-readiness-index",          # ~250k chars / ~62k tok — ARM AI readiness index
    "nist-ai-rmf-playbook",            # ~339k chars / ~85k tok — NIST AI RMF Playbook
}
PER_DOC_TIMEOUT_S = 1800
MAX_DOC_ATTEMPTS = 2               # transport retry discipline: verbatim retry once

RAW_DIR = REPO / "events" / "raw" / "bulk_v1"
STOP_FILE = REPO / "events" / "bulk_v1_STOP.json"
RESULT_FILE = REPO / "cc_tasks" / "2026-07-05_airkg_bulk_extraction_v1_RESULT.md"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def corpus_v1_members() -> dict[str, Path]:
    """doc_id -> absolute source path for every v1 member, from the dixie ledger."""
    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    log = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    members: list[str] | None = None
    for ev in log.replay():
        if ev["event_type"] == "corpus_epoch_declared" and \
                ev["payload"].get("epoch") == CORPUS_EPOCH:
            members = ev["payload"]["member_doc_ids"]
    if not members:
        raise SystemExit(f"FATAL: no corpus_epoch_declared {CORPUS_EPOCH} event in the ledger")
    entries = build_manifest(log)
    out: dict[str, Path] = {}
    for doc_id in members:
        e = entries.get(doc_id)
        path = e and e["identity"].get("canonical_path")
        if not path or not (REPO / path).is_file():
            raise SystemExit(f"FATAL: v1 member {doc_id!r} has no verified file on disk "
                             f"({path}) — the frozen baseline is damaged; refusing to run")
        out[doc_id] = REPO / path
    return out


def resume_state() -> tuple[set[str], dict[str, int]]:
    """(done doc_ids, failed-attempt counts) from this run's shard."""
    done: set[str] = set()
    fails: dict[str, int] = {}
    shard = REPO / "events" / f"batch-{BULK_BATCH:03d}.jsonl"
    if shard.is_file():
        with shard.open(encoding="utf-8") as fh:
            for line in fh:
                ev = json.loads(line)
                if ev.get("event_type") == "build_metrics":
                    done.add(ev["doc_id"])
                elif ev.get("event_type") == "bulk_doc_failed":
                    fails[ev["doc_id"]] = fails.get(ev["doc_id"], 0) + 1
    return done, fails


def tokens_left() -> int:
    caps = cp.declared_caps(CIRCUIT) or {}
    panel = cp.load_panel()
    u = panel["circuits"][CIRCUIT]["usage"]
    day_left = max(0, caps.get("daily_tokens", 0) - u["day_tokens"])
    week_left = max(0, caps.get("weekly_tokens", 0) - u["week_tokens"])
    return min(day_left, week_left)


def doc_text(path: Path) -> str:
    if path.suffix.lower() in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    raise ValueError(f"unhandled source format: {path}")


def persist_raw(doc_id: str, doc_sha: str, meta: dict, error: str | None = None) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    model_id = meta.get("model_id") or "unreported"
    out = RAW_DIR / (f"{doc_id}.{doc_sha[:12]}."
                     f"{model_stub.prompt_version()}.{model_id}.json")
    out.write_text(json.dumps({
        "doc_id": doc_id, "doc_sha256": doc_sha,
        "prompt_version": model_stub.prompt_version(),
        "schema_version": eventlog.schema_version(),
        "corpus_epoch": CORPUS_EPOCH,
        "model_id": meta.get("model_id"),
        "usage": meta.get("usage"), "cost_usd": meta.get("cost_usd"),
        "duration_ms": meta.get("duration_ms"), "session_id": meta.get("session_id"),
        "ts": _now(), "error": error,
        "raw_result": meta.get("raw_result"),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def write_stop(reason: str, detail: dict):
    STOP_FILE.write_text(json.dumps(
        {"reason": reason, "detail": detail, "ts": _now(),
         "resume": "operator: review, then delete this file to resume"},
        indent=1) + "\n", encoding="utf-8")
    eventlog.append({"event_type": "bulk_run_stop", "reason": reason,
                     "detail": detail}, batch=BULK_BATCH)


def append_progress(lines: list[str]):
    """Per-day progress appended to the RESULT as the task requires."""
    stamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    block = f"\n### Burn progress — {stamp}\n\n" + "\n".join(lines) + "\n"
    with RESULT_FILE.open("a", encoding="utf-8") as fh:
        fh.write(block)


def usage_tokens(meta: dict) -> int:
    u = meta.get("usage") or {}
    total = sum(int(u.get(k, 0) or 0) for k in
                ("inputTokens", "outputTokens", "cacheCreationInputTokens",
                 "cacheReadInputTokens"))
    return total or cp.estimate_tokens("", meta.get("raw_result") or "")


def run(max_docs: int | None = None, dry_run: bool = False) -> int:
    if STOP_FILE.exists():
        print(f"STOP file present ({STOP_FILE}) — operator review required. Exiting.")
        return 2
    state.EXTRACTION_BATCH = BULK_BATCH  # this run's shard (resolved at call time)

    members = corpus_v1_members()
    done, fails = resume_state()
    # BURN_ORDER: "size_desc" knocks out the big docs first (boost mode — uses a wide
    # window on the expensive docs); default alphabetical. Resume is done-set based, so
    # reordering is safe (order affects only which undone doc goes next, not correctness).
    if os.environ.get("BURN_ORDER") == "size_desc":
        ordered = sorted(members, key=lambda d: members[d].stat().st_size, reverse=True)
    else:
        ordered = sorted(members)
    todo = [d for d in ordered if d not in done
            and fails.get(d, 0) < MAX_DOC_ATTEMPTS]
    print(f"corpus v1: {len(members)} docs | done: {len(done)} | "
          f"skipped(failed x{MAX_DOC_ATTEMPTS}): "
          f"{sum(1 for d in members if fails.get(d, 0) >= MAX_DOC_ATTEMPTS)} | todo: {len(todo)}")
    if not todo:
        print("nothing to do — burn complete (or all remainders failed; see events).")
        return 0
    if dry_run:
        for d in todo[:10]:
            print("  would extract:", d, "<-", members[d].name)
        print(f"budget now: {tokens_left()} tokens")
        return 0

    if not cp.acquire_burn_lease(PROJECT, JOB):
        print("burn lease held elsewhere — exiting cleanly.")
        return 0
    processed, progress = 0, []
    q_over_streak = 0  # consecutive docs over the quarantine threshold (systemic mode)
    try:
        for doc_id in todo:
            if max_docs is not None and processed >= max_docs:
                break
            left = tokens_left()
            if left <= 0:
                print(f"declared cap exhausted (0 tokens left) — clean no-op; "
                      f"resumes next window.")
                progress.append(f"- cap exhausted after {processed} docs this window")
                break
            ok, reason = cp.gate(CIRCUIT, project=PROJECT, priority_class=PRIORITY_CLASS)
            if not ok:  # observe never denies below master; this catches master-off
                print(f"admission denied: {reason} — exiting cleanly.")
                progress.append(f"- admission denied: {reason}")
                break

            path = members[doc_id]
            doc_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            try:
                text = doc_text(path)
            except Exception as exc:
                eventlog.append({"event_type": "bulk_doc_failed", "doc_id": doc_id,
                                 "stage": "text_extraction", "error": str(exc)[:400]},
                                batch=BULK_BATCH)
                progress.append(f"- {doc_id}: text extraction failed ({exc})")
                continue
            if len(text) > MAX_DOC_CHARS and doc_id not in OVERSIZE_ALLOW:
                eventlog.append({"event_type": "bulk_doc_skipped_oversize",
                                 "doc_id": doc_id, "chars": len(text),
                                 "limit": MAX_DOC_CHARS,
                                 "note": "deferred — never truncated (grounding integrity)"},
                                batch=BULK_BATCH)
                print(f"  {doc_id}: OVERSIZE ({len(text)} chars) — deferred with event")
                progress.append(f"- {doc_id}: deferred oversize ({len(text):,} chars)")
                continue
            if len(text) > MAX_DOC_CHARS and doc_id in OVERSIZE_ALLOW:
                eventlog.append({"event_type": "bulk_doc_oversize_cleared",
                                 "doc_id": doc_id, "chars": len(text),
                                 "limit": MAX_DOC_CHARS,
                                 "note": "operator-cleared 2026-07-07; single full-context "
                                         "call, not truncated"},
                                batch=BULK_BATCH)
                print(f"  {doc_id}: OVERSIZE ({len(text)} chars) — operator-cleared, extracting")

            print(f"  extracting {doc_id} ({len(text):,} chars) …", flush=True)
            try:
                meta = model_stub.invoke(doc_id, text, timeout=PER_DOC_TIMEOUT_S)
            except model_stub.ModelSubstitutionError as exc:
                persist_raw(doc_id, doc_sha, {"raw_result": None}, error=str(exc))
                write_stop("model_substitution", {"doc_id": doc_id,
                                                  "expected": exc.expected,
                                                  "observed": exc.observed})
                progress.append(f"- STOP: model substitution on {doc_id} "
                                f"({exc.observed} != {exc.expected})")
                return 2
            except model_stub.ModelInvocationError as exc:
                eventlog.append({"event_type": "bulk_doc_failed", "doc_id": doc_id,
                                 "stage": "model_invocation", "error": str(exc)[:400]},
                                batch=BULK_BATCH)
                progress.append(f"- {doc_id}: invocation failed "
                                f"(attempt {fails.get(doc_id, 0) + 1}/{MAX_DOC_ATTEMPTS}): "
                                f"{str(exc)[:120]}")
                continue

            raw_path = persist_raw(doc_id, doc_sha, meta)
            burned = usage_tokens(meta)
            cp.record_usage(CIRCUIT, burned, job=JOB, project=PROJECT)

            try:
                summary = pipeline.extract_document(
                    doc_id, text, output=meta["output"], model_meta=meta,
                    extra_provenance={"corpus_epoch": CORPUS_EPOCH,
                                      "source_sha256": doc_sha})
            except Exception as exc:
                eventlog.append({"event_type": "bulk_doc_failed", "doc_id": doc_id,
                                 "stage": "parse_pipeline", "error": str(exc)[:400],
                                 "raw_response": str(raw_path.relative_to(REPO))},
                                batch=BULK_BATCH)
                progress.append(f"- {doc_id}: pipeline failed after raw persisted: "
                                f"{str(exc)[:120]}")
                continue

            m = summary["metrics"]
            processed += 1
            progress.append(
                f"- {doc_id}: {m['nodes']} nodes, {m['edges']} edges, "
                f"quarantined {m['quarantined']} "
                f"(rate {m['quarantine_rate']:.3f}), {burned:,} tokens")
            print(f"    ok: {m['nodes']}n/{m['edges']}e/{m['quarantined']}q "
                  f"| quarantine_rate {m['quarantine_rate']:.3f} "
                  f"| {burned:,} tokens | raw: {raw_path.name}")

            over = m["quarantine_rate"] > QUARANTINE_STOP_RATE
            if over:
                eventlog.append({"event_type": "bulk_doc_quarantine_high",
                                 "doc_id": doc_id, "rate": m["quarantine_rate"],
                                 "threshold": QUARANTINE_STOP_RATE}, batch=BULK_BATCH)
            if QUARANTINE_STOP_MODE == "systemic":
                q_over_streak = q_over_streak + 1 if over else 0
                if q_over_streak >= QUARANTINE_SYSTEMIC_WINDOW:
                    write_stop("quarantine_rate_systemic",
                               {"doc_id": doc_id, "streak": q_over_streak,
                                "rate": m["quarantine_rate"],
                                "threshold": QUARANTINE_STOP_RATE})
                    progress.append(f"- STOP: {q_over_streak} consecutive docs over "
                                    f"quarantine {QUARANTINE_STOP_RATE} (systemic)")
                    return 2
            elif over:  # per_doc (default, pre-registered)
                write_stop("quarantine_rate_exceeded",
                           {"doc_id": doc_id, "rate": m["quarantine_rate"],
                            "threshold": QUARANTINE_STOP_RATE})
                progress.append(f"- STOP: {doc_id} quarantine rate "
                                f"{m['quarantine_rate']:.3f} > {QUARANTINE_STOP_RATE}")
                return 2
    finally:
        cp.release_burn_lease()
        # only windows that did work (or hit a STOP) earn a RESULT section —
        # hourly cap-exhausted no-ops log to the wrapper log, not the report
        if processed or any(line.startswith("- STOP") for line in progress):
            done_after, _ = resume_state()
            progress.append(f"- window total: {processed} docs extracted; "
                            f"{len(done_after)}/{len(members)} complete; "
                            f"tokens left in band: {tokens_left():,}")
            append_progress(progress)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-docs", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return run(max_docs=args.max_docs, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
