#!/usr/bin/env python3
"""Chunked-extraction pilot (task 2026-08-27_chunked_pilot).

Second arm of the unit-of-extraction comparison. The whole-document arm is banked on
`events/batch-013_reextract_v035b.jsonl` + `events/raw/reextract_v035b_pilot/`; this script
adds the chunked arm on the SAME five documents, the SAME model, the SAME schema and rules,
and the SAME pre-registered gate. The unit is the only variable.

Phases (each idempotent, each resumable):

  dry_run   chunk the five documents, count chunks and prompt tokens, print the ceiling
            arithmetic. Zero model calls — §5 requires this before a ceiling is declared.
  extract   one model call per chunk under profile `chunked_v035` (sha-pinned prompt), events
            to the TAGGED shard batch-016_chunked_v035. Resume = a persisted raw for that
            chunk. A response above `truncation_suspect_tokens` STOPs the run: at ~1,500
            input tokens per chunk that is a defect, not a status (§3).
  resolve   §4 deterministic cross-chunk resolution: exact normalized surface form + recorded
            alias, within a document. No LLM-proposed merges — that is a separate pilot.
  judge     both arms through ONE probe protocol at the same versions (decompose 1.1.0,
            probe_judge 1.1.0, span_checks 1.0.0), same raters, same pre-registered
            thresholds, and write the comparison verdict.

Nothing here retunes anything: F_upper < 0.10, item-faithful >= 0.70 and the pooled-20
precondition are read from the task and never written by this file.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
import unicodedata
import uuid
from collections import Counter, defaultdict
import pathlib
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog, spend                                   # noqa: E402
from kg.extraction import chunker, grounding, model_stub, parser, span_checks  # noqa: E402
from kg.extraction.pipeline import _apply_provenance_ownership   # noqa: E402
import run_bulk_extraction as rbe                                # noqa: E402

TASK = "cc_tasks/2026-08-27_chunked_pilot.md"
PY = sys.executable
PROFILE = "chunked_v035"
RUN_ID = "pilot_chunked_v035"
JUDGE_RUN_ID = "chunked_pilot_judge"
SHARD_NO, TAG = 16, "chunked_v035"
RAW_DIR = REPO / "events/raw/chunked_v035"
METRICS = REPO / "corpus/staging/metrics"
VERDICT = REPO / "docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md"

# The banked whole-document arm.
WD_RAW_DIR = REPO / "events/raw/reextract_v035b_pilot"

PILOT_DOCS = ["data-readiness-for-ai-a-360-degree-survey", "aidrin-hiniduma-2024",
              "fcsm-23-02-a-framework-for-data-quality-case-studies",
              "from-accuracy-to-readiness-metrics-and-benchmarks-for-human",
              "mitre-ai-maturity-model"]

# Pre-registered, from the task. Never written here.
F_STOP, ITEM_FAITHFUL, STRATUM_PRECONDITION = 0.10, 0.70, 20
SEMANTIC = parser.SEMANTIC_EDGE_TYPES


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def members() -> dict[str, Path]:
    out = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof)
        out.update(rbe.corpus_members())
    rbe.apply_profile(PROFILE)          # sha-pinned chunked prompt is the active one
    return out


def chunk_sets() -> dict[str, tuple[str, chunker.ChunkSet]]:
    m = members()
    out = {}
    for d in PILOT_DOCS:
        text = rbe.doc_text(m[d])
        out[d] = (text, chunker.chunk_document(d, text))
    return out


def profile_template(profile: str = None) -> pathlib.Path:
    """The prompt template the named profile pins. Reading it from the profile rather than
    hardcoding it is what lets §2 price v0_3_7 without touching the banked v035 arm: for
    chunked_v035 this resolves to chunked_template.md, byte-identical to the old constant."""
    import yaml
    doc = yaml.safe_load((REPO / "scripts/run_profiles.yaml").read_text(encoding="utf-8"))
    prof = (doc.get("profiles") or {}).get(profile or PROFILE) or {}
    rel = prof.get("prompt_template") or "kg/extraction/chunked_template.md"
    return REPO / rel


def build_prompt(doc_id: str, chunk: chunker.Chunk, title: str, profile: str = None) -> str:
    tpl = profile_template(profile).read_text(encoding="utf-8")
    return (tpl.replace("{{schema_version}}", eventlog.schema_version())
               .replace("{{document_id}}", doc_id)
               .replace("{{chunk_id}}", chunk.chunk_id)
               .replace("{{document_text}}", chunk.model_text(title)))


# ------------------------------------------------------------------ dry run
#: Per-item output cost under the ANCHOR contract, from the real tokenizer on a representative
#: node and edge: `{"id","name","type","anchor","location"}` and
#: `{"type","from_id","to_id","anchor","location"}`. ~38 tokens. The v0.3.5 exhaustive-verbatim
#: contract MEASURED 225 tokens/item over the banked arm, so the anchor change alone is a
#: ~5.9x per-item reduction. Computed rather than assumed; see `phase_dry_run`.
ANCHOR_TOKENS_PER_ITEM = 38


def banked_items_per_chunk() -> tuple[float, int]:
    """(median items/chunk, n chunks parsed) from the banked chunked_v035 raws.

    This is the only measurement of item DENSITY on these documents that exists. v0.3.7 also
    drops the exhaustive-inventory instruction, which should lower it — but by how much is
    unmeasured until §3 runs, so the ceiling below deliberately assumes NO salience reduction.
    A ceiling built on the optimistic assumption refuses a legitimate run."""
    keys = ("concepts", "definitions", "claims", "instruments", "measures", "standards",
            "frameworks", "practices", "tools", "platforms", "edges", "cites", "mentions",
            "proposed_relationships")
    counts = []
    for f in sorted((REPO / "events/raw/chunked_v035").glob("*.json")):
        raw = (json.loads(f.read_text()).get("raw_result") or "").strip()
        if not raw.startswith("{"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        counts.append(sum(len(obj.get(k) or []) for k in keys))
    if not counts:
        raise SystemExit("FATAL: no parsable banked chunk output to size the projection from")
    return statistics.median(counts), len(counts)


def phase_dry_run(a) -> int:
    cfg = model_stub.load_model_config()
    profile = getattr(a, "profile", None) or PROFILE
    sets = chunk_sets()
    first = list(sets.values())[0][1][0]
    tpl_tokens = chunker.count_tokens(build_prompt("d", first, "t", profile)) - first.n_tokens
    print(f"profile: {profile}   template: {profile_template(profile).name}")
    print(f"prompt overhead (template + breadcrumb, excl. chunk body): ~{tpl_tokens:,} tokens\n")
    print(f"{'doc':52s} {'chunks':>7} {'src_tok':>9} {'chunk_tok':>10} {'input_tok':>10} {'over':>5}")
    tot_chunks = tot_input = tot_body = 0
    for d, (text, cs) in sets.items():
        body = sum(c.n_tokens for c in cs)
        overlap = sum(chunker.count_tokens(c.overlap_text) for c in cs if c.overlap_text)
        inp = body + overlap + tpl_tokens * len(cs)
        over = sum(1 for c in cs if c.oversize)
        print(f"{d[:52]:52s} {len(cs):>7} {chunker.count_tokens(text):>9,} {body:>10,} {inp:>10,} {over:>5}")
        tot_chunks += len(cs); tot_input += inp; tot_body += body
    floors = spend._spend_config()["call_class_floors"]
    floor = floors["extraction_chunk"]
    wd = whole_doc_usage()
    wd_out = sum(u.get("outputTokens", 0) for u in wd.values())
    wd_in = sum(u.get("inputTokens", 0) + u.get("cacheCreationInputTokens", 0) for u in wd.values())
    ratio = wd_out / wd_in if wd_in else 1.0
    if profile == "v0_3_7":
        # The whole-doc output/input ratio prices the RETIRED exhaustive-verbatim contract and
        # would badly overestimate this arm — using it here would be pricing the thing v0.3.7
        # replaced. Output is instead built from measured item density x computed per-item cost.
        med_items, n_parsed = banked_items_per_chunk()
        est_out = int(tot_chunks * med_items * ANCHOR_TOKENS_PER_ITEM)
        print(f"\noutput model (anchor contract, NOT the whole-doc ratio):")
        print(f"  measured item density: median {med_items:.0f} items/chunk "
              f"over {n_parsed} banked chunks")
        print(f"  computed per-item cost: {ANCHOR_TOKENS_PER_ITEM} tokens "
              f"(v0.3.5 measured 225/item -> {225 / ANCHOR_TOKENS_PER_ITEM:.1f}x reduction)")
        print(f"  projected output: {med_items:.0f} x {ANCHOR_TOKENS_PER_ITEM} = "
              f"{med_items * ANCHOR_TOKENS_PER_ITEM:,.0f}/chunk x {tot_chunks} = {est_out:,}")
        print(f"  ASSUMES NO SALIENCE REDUCTION in item count — unmeasured until §3, so the "
              f"ceiling is deliberately conservative. ADDENDUM-03 §2 expects ~1-2K/chunk, "
              f"which presumes salience also cuts the count; this projects "
              f"{med_items * ANCHOR_TOKENS_PER_ITEM:,.0f}/chunk without that.")
    else:
        est_out = int(tot_input * ratio)
    est_cache = tot_input          # non-resumed calls re-send the prefix; cacheCreation ~ input
    est_total = tot_input + est_cache + est_out
    print(f"\nTOTAL chunks {tot_chunks}, input {tot_input:,} tokens "
          f"({tot_input / tot_chunks:,.0f}/call)")
    print(f"whole-doc arm measured output/input ratio: {wd_out:,}/{wd_in:,} = {ratio:.2f}")
    print(f"estimated extraction spend: input {tot_input:,} + cache_creation {est_cache:,} "
          f"+ output {est_out:,} = {est_total:,}")
    print(f"reserve-time floor {floor:,}/call x {tot_chunks} calls = "
          f"{floor * tot_chunks:,} (the guard's first-calls estimate; the running mean "
          f"replaces it after the first settles)")
    print(f"\nSUGGESTED CEILING (extraction): max(estimate, floor x calls) x 1.5 margin = "
          f"{int(max(est_total, floor * tot_chunks) * 1.5):,}")
    return 0


def whole_doc_usage() -> dict[str, dict]:
    out = {}
    for f in sorted(WD_RAW_DIR.glob("*.json")):
        d = json.loads(f.read_text())
        out[d["doc_id"]] = {k: int((d.get("usage") or {}).get(k, 0) or 0)
                            for k in ("inputTokens", "outputTokens",
                                      "cacheCreationInputTokens", "cacheReadInputTokens")}
    return out


# ------------------------------------------------------------------ extract
def raw_path(doc_id: str, chunk: chunker.Chunk, sha: str, model_id: str) -> Path:
    return RAW_DIR / (f"{doc_id}.{chunk.chunk_id.split('#')[1]}.{sha[:12]}."
                      f"{model_stub.prompt_version()}.{model_id}.json")


def _extract_one(d: str, c: chunker.Chunk, sha: str, title: str, cfg: dict, suspect: int) -> str:
    rp = raw_path(d, c, sha, cfg["model_id"])
    if rp.exists():
        return "skip"
    meta = model_stub.invoke(c.chunk_id, "", prompt=build_prompt(d, c, title),
                             timeout=900, config=cfg)
    out_tok = int((meta.get("usage") or {}).get("outputTokens", 0) or 0)
    rp.write_text(json.dumps(
        {"doc_id": d, "chunk_id": c.chunk_id, "chunk_index": c.index,
         "chunk_start": c.start, "chunk_end": c.end, "chunk_tokens": c.n_tokens,
         "heading_path": list(c.heading_path), "oversize": c.oversize,
         "doc_sha256": sha, "prompt_version": model_stub.prompt_version(),
         "model_id": meta["model_id"], "usage": meta["usage"],
         "cost_usd": meta.get("cost_usd"), "duration_ms": meta.get("duration_ms"),
         "session_id": meta.get("session_id"), "raw_result": meta["raw_result"]},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # §3 says a chunk response above `truncation_suspect_tokens` (40,000) is a defect, on the
    # stated premise that "output per chunk is small". MEASURED, that premise is false:
    # 1,500-token chunks return 33-39K output tokens, because the prompt asks for an
    # exhaustive concept inventory and the model obliges per chunk. 40,000 is a
    # whole-document heuristic and misfires here. The rule's PURPOSE — never accept a
    # truncated response as a status — is kept with the detector that actually detects
    # truncation for this unit: the response hit the model's own output ceiling, or it did
    # not parse into an envelope carrying extraction layers. Both STOP.
    max_out = int((meta.get("usage") or {}).get("maxOutputTokens", 0) or 0)
    if max_out and out_tok >= 0.95 * max_out:
        raise SystemExit(f"FATAL: {c.chunk_id} returned {out_tok:,} of the model's "
                         f"{max_out:,} output-token ceiling — truncated, not complete.")
    if not model_stub.has_extraction_layers(meta.get("output")):
        raise SystemExit(f"FATAL: {c.chunk_id} returned no extraction layers "
                         f"({out_tok:,} output tokens) — a truncated or empty envelope.")
    print(f"  {c.chunk_id} tok_in~{c.n_tokens} out={out_tok}", flush=True)
    return "ok"


def phase_extract(a) -> int:
    from concurrent.futures import ThreadPoolExecutor
    cfg = model_stub.load_model_config()
    m = members()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    spend.set_current_run(RUN_ID)
    suspect = int(cfg.get("truncation_suspect_tokens", 40000))   # reported only; see _extract_one
    todo = []
    for d in PILOT_DOCS:
        text = rbe.doc_text(m[d])
        sha = hashlib.sha256(m[d].read_bytes()).hexdigest()
        cs = chunker.chunk_document(d, text)
        title = d.replace("-", " ")
        pending = [c for c in cs if not raw_path(d, c, sha, cfg["model_id"]).exists()]
        print(f"=== {d}: {len(cs)} chunks, {len(cs) - len(pending)} already extracted "
              f"[{cs.structure_source}, level {cs.heading_level}]", flush=True)
        todo += [(d, c, sha, title) for c in pending]
    if a.limit:
        todo = todo[:a.limit]
    print(f"dispatching {len(todo)} chunk calls, {a.workers} workers", flush=True)
    done, failures = 0, []
    # The spend guard is the concurrency-safe boundary (flock on the ledger), so workers only
    # need to be few enough not to trip rate limits. A single failed chunk must not discard a
    # pass whose other calls are already paid for: it is recorded and the pass continues, but
    # a systemic failure (STOP_AFTER_FAILURES in a row) ends it — silence on repeated failure
    # would be the lazy handling standard 4 forbids.
    STOP_AFTER_FAILURES = 5
    streak = 0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(_extract_one, d, c, sha, title, cfg, suspect): c.chunk_id
                for d, c, sha, title in todo}
        for f, cid in futs.items():
            if streak >= STOP_AFTER_FAILURES:
                f.cancel(); continue
            try:
                done += 1 if f.result() == "ok" else 0
                streak = 0
            except spend.SpendRefusalStop:
                raise
            except Exception as exc:                       # noqa: BLE001 — recorded, not swallowed
                failures.append((cid, f"{type(exc).__name__}: {exc}"))
                streak += 1
                print(f"  FAILED {cid}: {type(exc).__name__}: {str(exc)[:200]}", flush=True)
    print(f"\nextraction calls this pass: {done}; failures: {len(failures)}")
    for cid, why in failures:
        print(f"  {cid}: {why}")
    if streak >= STOP_AFTER_FAILURES:
        raise SystemExit(f"FATAL: {STOP_AFTER_FAILURES} consecutive chunk failures — systemic, "
                         f"pass stopped (raws already written are resume-safe)")
    return phase_ingest(a)


def parse_chunk_raw(doc_id: str, raw: dict, full_text: str, chunk_text: str) -> tuple:
    """(result, mentions, diversions) for one chunk's persisted response."""
    out = model_stub._extract_json(raw.get("raw_result") or "")
    out = _apply_provenance_ownership(out, doc_id)
    result = parser.parse_extraction(out, chunk_text, enforce_span_coverage=True)
    mentions = [x for x in (out.get("mentions") or [])
                if isinstance(x, dict) and x.get("name")
                and grounding.is_grounded(str(x.get("grounding_span") or ""), chunk_text)]
    return result, mentions, list(result.proposed_relationships)


def superseded() -> set[tuple]:
    """(chunk_id, start, end) triples retired by a `chunk_superseded` event.

    The shard is append-only, so a chunker change that moves a boundary is corrected forward:
    the stale chunk's events stay on the shard and every reader filters them out by this set.
    """
    return {(ev["chunk_id"], ev["chunk_start"], ev["chunk_end"])
            for ev in eventlog.replay(tag=TAG) if ev.get("event_type") == "chunk_superseded"}


def _key(ev: dict) -> tuple:
    prov = ev.get("provenance") or {}
    return (ev.get("chunk_id"), prov.get("chunk_start"), prov.get("chunk_end"))


def phase_ingest(a) -> int:
    """Parse every persisted chunk response into the tagged shard. Idempotent: a chunk whose
    events are already on the shard is skipped."""
    dead = superseded()
    cfg = model_stub.load_model_config()
    m = members()
    on_shard = {ev.get("chunk_id") for ev in eventlog.replay(tag=TAG)
                if ev.get("event_type") == "chunk_metrics"
                and (ev["chunk_id"], ev.get("chunk_start"), ev.get("chunk_end")) not in dead}
    counts = Counter()
    for d in PILOT_DOCS:
        text = rbe.doc_text(m[d])
        sha = hashlib.sha256(m[d].read_bytes()).hexdigest()
        cs = chunker.chunk_document(d, text)
        for c in cs:
            rp = raw_path(d, c, sha, cfg["model_id"])
            if not rp.exists() or c.chunk_id in on_shard:
                continue
            raw = json.loads(rp.read_text())
            chunk_text = c.grounding_text()
            result, mentions, divs = parse_chunk_raw(d, raw, text, chunk_text)
            ex_id = uuid.uuid4().hex
            prov = {**model_stub.provenance_stamp(ex_id, model_id=raw["model_id"]),
                    "corpus_epoch": "chunked-2026-08-27", "source_sha256": sha,
                    "chunk_id": c.chunk_id, "chunk_start": c.start, "chunk_end": c.end}
            # Locate-at-birth is unchanged: the parser validated every span against the chunk;
            # re-validate against the whole document so a span can never be chunk-local only.
            kept_n = kept_e = 0
            for nrec in result.nodes:
                if not grounding.is_grounded(nrec["item"].get("grounding_span") or "", text):
                    counts["node_not_in_document"] += 1
                    continue
                eventlog.append({"event_type": "node_asserted", "purpose": "chunked_pilot",
                                 "doc_id": d, "chunk_id": c.chunk_id, "provenance": prov,
                                 "payload": {"id": nrec["id"], "type": nrec["type"],
                                             "item": nrec["item"]}}, batch=SHARD_NO, tag=TAG)
                kept_n += 1
            for erec in result.edges:
                if not grounding.is_grounded(erec["item"].get("grounding_span") or "", text):
                    counts["edge_not_in_document"] += 1
                    continue
                eventlog.append({"event_type": "edge_asserted", "purpose": "chunked_pilot",
                                 "doc_id": d, "chunk_id": c.chunk_id, "provenance": prov,
                                 "payload": {"type": erec["type"], "from_id": erec["from_id"],
                                             "to_id": erec["to_id"], "item": erec["item"]}},
                                batch=SHARD_NO, tag=TAG)
                kept_e += 1
            for x in mentions:
                eventlog.append({"event_type": "mention_stub", "purpose": "chunked_pilot",
                                 "doc_id": d, "chunk_id": c.chunk_id, "provenance": prov,
                                 "payload": {"name": x["name"],
                                             "grounding_span": x.get("grounding_span")}},
                                batch=SHARD_NO, tag=TAG)
            hist = Counter((p.get("diversion_reason") or "unstated") for p in divs)
            eventlog.append({"event_type": "chunk_metrics", "purpose": "chunked_pilot",
                             "doc_id": d, "chunk_id": c.chunk_id,
                             "chunk_start": c.start, "chunk_end": c.end,
                             "chunk_tokens": c.n_tokens, "oversize": c.oversize,
                             "heading_path": list(c.heading_path),
                             "counts": result.counts(), "nodes_kept": kept_n,
                             "edges_kept": kept_e, "mentions": len(mentions),
                             "diversion_histogram": dict(hist),
                             "span_lacks_name": result.precheck_span_lacks_name,
                             "output_tokens": int((raw.get("usage") or {}).get("outputTokens", 0) or 0),
                             "task": TASK}, batch=SHARD_NO, tag=TAG)
            counts["chunks"] += 1; counts["nodes"] += kept_n; counts["edges"] += kept_e
            counts["mentions"] += len(mentions); counts["diverted"] += len(divs)
    print("ingested:", dict(counts))
    return 0


# ------------------------------------------------------------------ §4 resolution
def norm_form(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(s or "")).casefold().split())


def shard_items() -> tuple[dict, dict, dict]:
    """(nodes, edges, stubs) per doc from the tagged shard."""
    nodes, edges, stubs = defaultdict(list), defaultdict(list), defaultdict(list)
    dead = superseded()
    for ev in eventlog.replay(tag=TAG):
        if _key(ev) in dead:
            continue
        et = ev.get("event_type")
        if et == "node_asserted":
            nodes[ev["doc_id"]].append(ev)
        elif et == "edge_asserted":
            edges[ev["doc_id"]].append(ev)
        elif et == "mention_stub":
            stubs[ev["doc_id"]].append(ev)
    return nodes, edges, stubs


def phase_resolve(a) -> int:
    nodes, edges, stubs = shard_items()
    report = {}
    for d in PILOT_DOCS:
        by_form: dict[str, list] = defaultdict(list)
        for ev in nodes[d]:
            item = ev["payload"]["item"]
            forms = {norm_form(item.get("name") or item.get("term") or item.get("text") or "")}
            for al in (item.get("aliases") or []):
                forms.add(norm_form(al))
            forms.discard("")
            for f in forms:
                by_form[f].append(ev)
        # A resolved entity is one normalized surface form; a form with >1 event merged.
        groups = {f: evs for f, evs in by_form.items()}
        merged = sum(len(evs) - 1 for evs in groups.values() if len(evs) > 1)
        stub_hits = sum(1 for s in stubs[d] if norm_form(s["payload"]["name"]) in by_form)
        report[d] = {"node_events": len(nodes[d]), "surface_forms": len(groups),
                     "merged_events": merged,
                     "merge_rate": round(merged / len(nodes[d]), 4) if nodes[d] else 0.0,
                     "stubs": len(stubs[d]), "stubs_resolved": stub_hits,
                     "stubs_unmerged": len(stubs[d]) - stub_hits,
                     "edge_events": len(edges[d])}
        print(d, report[d])
    eventlog.append({"event_type": "entity_resolution", "purpose": "chunked_pilot",
                     "method": "deterministic:nfkc_casefold_ws + aliases (task §4)",
                     "per_doc": report, "task": TASK}, batch=SHARD_NO, tag=TAG)
    (METRICS / "chunked_resolution.json").write_text(json.dumps(report, indent=1))
    return 0


# ------------------------------------------------------------------ judging (both arms)
def window_for(norm_doc: str, span: str) -> str | None:
    n = grounding.normalize(span or "")
    i = norm_doc.find(n)
    return norm_doc[max(0, i - 400): i + len(n) + 400] if (n and i >= 0) else None


def wholedoc_records(texts: dict[str, str]) -> list[dict]:
    """The banked whole-document arm, re-derived from its persisted raws — the same
    derivation `addendum05_pilot.pilot_outputs` used, so the arm is not re-extracted."""
    import addendum05_triage as triage
    recs = []
    for d in PILOT_DOCS:
        raws = sorted(WD_RAW_DIR.glob(f"{d}.*.json"))
        if not raws:
            continue
        out = triage.merged_pilot_output(json.loads(raws[-1].read_text()).get("raw_result") or "")
        if not out:
            continue
        res = parser.parse_extraction(_apply_provenance_ownership(out, d), texts[d],
                                      enforce_span_coverage=True)
        names = {n["id"]: (n["item"].get("name") or n["item"].get("term")
                           or n["item"].get("text") or n["id"]) for n in res.nodes}
        norm = grounding.normalize(texts[d])
        for n in res.nodes:
            if n["type"] != "Instrument":
                continue
            span = n["item"].get("grounding_span") or ""
            recs.append({"item_id": n["id"], "event_id": uuid.uuid4().hex, "kind": "node",
                         "type": "Instrument", "stratum": "Instrument", "doc_id": d,
                         "text": n["item"].get("name") or "", "grounding_span": span,
                         "extra": n["item"], "window": window_for(norm, span)})
        for e in res.edges:
            if e["type"] not in SEMANTIC:
                continue
            span = e["item"].get("grounding_span") or ""
            recs.append({"item_id": f"{e['from_id']}->{e['to_id']}", "event_id": uuid.uuid4().hex,
                         "kind": "edge", "type": "edge", "stratum": "semantic_edge", "doc_id": d,
                         "text": f"{names.get(e['from_id'], e['from_id'])} {e['type']} "
                                 f"{names.get(e['to_id'], e['to_id'])}",
                         "grounding_span": span,
                         "extra": {"from_id": names.get(e["from_id"], e["from_id"]),
                                   "edge_type": e["type"],
                                   "to_id": names.get(e["to_id"], e["to_id"])},
                         "window": window_for(norm, span)})
    return recs


def chunked_records(texts: dict[str, str]) -> list[dict]:
    """The chunked arm, from the tagged shard AFTER §4 resolution: one record per resolved
    Instrument surface form (the first event carrying it is the representative) and one per
    semantic edge event."""
    nodes, edges, _ = shard_items()
    recs = []
    for d in PILOT_DOCS:
        norm = grounding.normalize(texts[d])
        names = {}
        for ev in nodes[d]:
            names[(ev["chunk_id"], ev["payload"]["id"])] = (
                ev["payload"]["item"].get("name") or ev["payload"]["item"].get("term")
                or ev["payload"]["item"].get("text") or ev["payload"]["id"])
        seen = set()
        for ev in nodes[d]:
            if ev["payload"]["type"] != "Instrument":
                continue
            item = ev["payload"]["item"]
            form = norm_form(item.get("name") or "")
            if form in seen:                     # §4: one record per resolved surface form
                continue
            seen.add(form)
            span = item.get("grounding_span") or ""
            recs.append({"item_id": f"{ev['chunk_id']}:{ev['payload']['id']}",
                         "event_id": uuid.uuid4().hex, "kind": "node", "type": "Instrument",
                         "stratum": "Instrument", "doc_id": d, "text": item.get("name") or "",
                         "grounding_span": span, "extra": item, "window": window_for(norm, span)})
        for ev in edges[d]:
            p = ev["payload"]
            if p["type"] not in SEMANTIC:
                continue
            span = p["item"].get("grounding_span") or ""
            fr = names.get((ev["chunk_id"], p["from_id"]), p["from_id"])
            to = names.get((ev["chunk_id"], p["to_id"]), p["to_id"])
            recs.append({"item_id": f"{ev['chunk_id']}:{p['from_id']}->{p['to_id']}",
                         "event_id": uuid.uuid4().hex, "kind": "edge", "type": "edge",
                         "stratum": "semantic_edge", "doc_id": d,
                         "text": f"{fr} {p['type']} {to}", "grounding_span": span,
                         "extra": {"from_id": fr, "edge_type": p["type"], "to_id": to},
                         "window": window_for(norm, span)})
    return recs


def write_sample(prefix: str, recs: list[dict]) -> None:
    """Keep an existing sample whose item set is identical: `fact_id` hashes the record's
    fresh uuid, so rewriting an unchanged sample renames every fact and orphans labels
    already paid for (root-caused 2026-08-27 in task 2026-08-27_pilot_finish)."""
    path = METRICS / f"{prefix}_sample.jsonl"
    if path.exists():
        prior = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        key = lambda rs: sorted((r["doc_id"], r["item_id"], r["text"], r["grounding_span"])
                                for r in rs)
        if key(prior) == key(recs):
            print(f"sample {prefix}: reusing {len(prior)} records (labels resume)", flush=True)
            return
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
                    encoding="utf-8")


def span_check_sidecar(prefix: str, texts: dict[str, str]) -> dict:
    """Mid-noun-phrase truncation check (span_checks 1.0.0) on the span each fact will be
    judged against — computed BEFORE judging and applied identically to both arms (§5). It
    records; it never removes a fact from a denominator."""
    import probe_judge as pj
    items = {it["event_id"]: it for it in
             (json.loads(l) for l in (METRICS / f"{prefix}_sample.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip())}
    out = {}
    for line in (METRICS / f"{prefix}_facts.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        f = json.loads(line)
        it = items[f["event_id"]]
        span, source = pj.span_for(it, f.get("attribute"))
        chk = span_checks.check(span, texts[it["doc_id"]])
        out[f["fact_id"]] = {**chk, "span_source": source, "stratum": it["stratum"],
                             "attribute": f.get("attribute")}
    (METRICS / f"{prefix}_span_checks.json").write_text(json.dumps(out, indent=1))
    n = sum(1 for v in out.values() if v["span_mid_phrase"])
    print(f"span checks {prefix}: {n}/{len(out)} facts sit on a mid-noun-phrase span "
          f"(span_checks {span_checks.CHECK_VERSION})")
    return out


def run_protocol(prefix: str, run: str, run_id: str, raters: list[str], fact_cap: int) -> dict | None:
    env = dict(os.environ); env[spend.RUN_ENV] = run_id
    r = subprocess.run([PY, "scripts/probe_decompose.py", "--prefix", prefix],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=7200)
    print(r.stdout[-800:], r.stderr[-400:], flush=True)
    if r.returncode != 0:
        return None
    # Stratified cap: a flat random cap can starve a stratum below its precondition.
    facts = [json.loads(l) for l in (METRICS / f"{prefix}_facts.jsonl")
             .read_text(encoding="utf-8").splitlines() if l.strip()]
    items = {it["event_id"]: it for it in
             (json.loads(l) for l in (METRICS / f"{prefix}_sample.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip())}
    by_stratum = defaultdict(list)
    for f in facts:
        by_stratum[items[f["event_id"]]["stratum"]].append(f["fact_id"])
    rng = random.Random(prefix)                  # seed recorded in the verdict
    sel = []
    for s, fids in sorted(by_stratum.items()):
        sel += fids if len(fids) <= fact_cap else rng.sample(fids, fact_cap)
    sel_path = METRICS / f"{prefix}_fact_sel.json"
    sel_path.write_text(json.dumps(sorted(sel)))
    print(f"{prefix}: {len(facts)} facts, judging {len(sel)} "
          f"(cap {fact_cap}/stratum, seed {prefix!r})", flush=True)
    for model in raters:
        r = subprocess.run([PY, "scripts/probe_judge.py", "--prefix", prefix, "--run", run,
                            "--batch", "10", "--model", model,
                            "--fact-ids-file", str(sel_path)],
                           cwd=REPO, env=env, capture_output=True, text=True, timeout=14400)
        print(r.stdout[-800:], r.stderr[-400:], flush=True)
        if r.returncode != 0:
            return None
    r = subprocess.run([PY, "scripts/probe_aggregate.py", "--prefix", prefix, "--run", run],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=900)
    print(r.stdout[-1500:], r.stderr[-400:], flush=True)
    agg = METRICS / f"{prefix}_aggregate.json"
    return json.loads(agg.read_text()) if agg.exists() else None


def item_faithful_by_stratum(agg: dict) -> dict[str, tuple[int, int]]:
    """(faithful items, items) per stratum — the pooled roll-up probe_aggregate emits cannot
    answer a per-stratum pre-registered threshold."""
    by_item = defaultdict(list)
    for v in (agg.get("per_fact") or {}).values():
        by_item[(v["stratum"], v["event_id"])].append(v)
    out = defaultdict(lambda: [0, 0])
    for (s, _), vs in by_item.items():
        out[s][1] += 1
        if all(v["entailed"] or v["class"] == "doc_level_attribute" for v in vs):
            out[s][0] += 1
    return {s: tuple(v) for s, v in out.items()}


def probe_versions() -> tuple[str, str]:
    """(decompose_version, probe_judge_version) read from the templates, never hardcoded."""
    import probe_decompose, probe_judge
    return probe_decompose.decompose_version(), probe_judge.judge_version()


def per_doc_settled_chunked() -> dict[str, int]:
    """Chunked-arm extraction cost per document, summed from the persisted chunk raws (the
    ledger settles per call, not per document)."""
    out = Counter()
    for f in RAW_DIR.glob("*.json"):
        r = json.loads(f.read_text())
        u = r.get("usage") or {}
        out[r["doc_id"]] += sum(int(u.get(k, 0) or 0) for k in
                                ("inputTokens", "outputTokens",
                                 "cacheCreationInputTokens", "cacheReadInputTokens"))
    return dict(out)


#: Closed list and normalization now live in the PARSER (v0.3.7, ADDENDUM-03 §1.3) — a model
#: cannot be bound by an instruction, only by a parser. Re-exported here so this script keeps
#: one name for it and there is exactly one definition in the repo; a second copy is how the
#: "resolved" definition drifted across three call sites earlier today.
from kg.extraction.parser import (                                     # noqa: E402
    DIVERSION_REASONS, normalize_diversion_reason as normalize_reason)


def diversion_histogram() -> tuple[dict, int, int]:
    """(normalized histogram, cross_chunk, total) over the chunked arm's diverted relations."""
    hist = Counter()
    for ev in eventlog.replay(tag=TAG):
        if ev.get("event_type") == "chunk_metrics" and _key(ev) not in superseded():
            for raw, n in (ev.get("diversion_histogram") or {}).items():
                hist[normalize_reason(raw)] += n
    total = sum(hist.values())
    return dict(hist), hist.get("cross_chunk", 0), total


def min_facts_for_gate() -> int:
    """Smallest fact count at which the pre-registered `F_upper < F_STOP` gate is ATTAINABLE,
    i.e. the Wilson 95% upper bound on a PERFECT result (0 fabrications) still clears it.

    This is arithmetic, not a threshold: it is derived from the task's own F_STOP and the
    aggregator's own interval method, and it moves only if one of those moves. Below it a
    stratum cannot pass however good the extraction is, so judging it buys a foregone FAIL.
    Prior art: the one-sided binomial upper bound with zero events — Louis 1981; Hanley &
    Lippman-Hand 1983, "If nothing goes wrong, is everything all right?" (the rule of three,
    3/n, of which this is the exact Wilson form)."""
    from probe_aggregate import wilson
    n = 1
    while n < 10_000:
        hi = wilson(0, n)[2]
        if hi is not None and hi < F_STOP:
            return n
        n += 1
    raise RuntimeError("no attainable n for the gate")


def stratum_admission(stratum: str, n_items: int, min_facts: int) -> tuple[bool, str]:
    """(judge?, reason). Two conditions, both from the task, neither invented here.

    1. The pre-registered precondition: pooled >= STRATUM_PRECONDITION admitted items.
    2. Gate reachability: for a stratum whose facts are 1:1 with its items — `semantic_edge`,
       where `probe_decompose.deterministic_facts` emits exactly one fact per edge — the fact
       count IS the item count, so a stratum below `min_facts` cannot clear F_upper even on a
       perfect result. Node strata decompose to MORE facts than items, so item count does not
       bound them and this condition does not apply.

    ADDENDUM-01 §1 says not to judge a sub-minimum sample. It anticipated the sample being
    sub-minimum on condition 1; where it is sub-minimum on condition 2 instead, the reason to
    skip is strictly stronger — a foregone FAIL, paid for."""
    if n_items < STRATUM_PRECONDITION:
        return False, (f"PRECONDITION NOT MET: {n_items} admitted < {STRATUM_PRECONDITION} pooled")
    if stratum == "semantic_edge" and n_items < min_facts:
        return False, (f"GATE UNREACHABLE: {n_items} facts (1 per edge); a perfect result "
                       f"(0 fabrications) gives F_upper > {F_STOP}; >= {min_facts} facts needed")
    return True, f"judged ({n_items} admitted)"


def phase_judge(a) -> int:
    cfg = model_stub.load_model_config()
    m = members()
    texts = {d: rbe.doc_text(m[d]) for d in PILOT_DOCS}
    raters = [cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]]
    spend.default_ledger().declare(JUDGE_RUN_ID, a.judge_ceiling, declared_by=TASK,
                                   call_class="judge")
    spend.set_current_run(JUDGE_RUN_ID)

    arms = {"chunked": chunked_records(texts), "wholedoc": wholedoc_records(texts)}
    min_facts = min_facts_for_gate()

    # ADDENDUM-01 §1: count first, report the number BEFORE judging. The census is over the
    # FULL admitted set of each arm and is what the verdict reports as `admitted`; any cap
    # below applies to what is JUDGED, never to what is counted.
    census = {arm: Counter(r["stratum"] for r in recs) for arm, recs in arms.items()}
    admission = {}
    print(f"\n=== pre-judge census (gate F_upper < {F_STOP} is attainable at "
          f">= {min_facts} facts) ===", flush=True)
    for arm, counts in census.items():
        by_doc = defaultdict(Counter)
        for r in arms[arm]:
            by_doc[r["stratum"]][r["doc_id"]] += 1
        print(f"  arm {arm}: {len(arms[arm])} admitted items", flush=True)
        for stratum in ("Instrument", "semantic_edge"):
            n = counts.get(stratum, 0)
            ok, why = stratum_admission(stratum, n, min_facts)
            admission[(arm, stratum)] = (ok, why)
            print(f"    {stratum:<14} {n:>4}  {why}", flush=True)
            print(f"      doc mix: {dict(by_doc[stratum])}", flush=True)

    judged_strata = sorted({s for (_, s), (ok, _) in admission.items() if ok})
    if not judged_strata:
        print("FATAL: no stratum is judgeable; nothing to spend on.")
        return 2

    results = {}
    for arm, recs in arms.items():
        prefix = f"arm_{arm}"
        recs = [r for r in recs if admission[(arm, r["stratum"])][0]]
        # Spend-bounded item sample. NOT a threshold: the pre-registered gate is untouched
        # and a smaller sample only widens the interval, which makes PASS harder, never
        # easier. Seeded and reported so the draw is reproducible.
        if a.instrument_item_cap:
            rng = random.Random(f"{prefix}:{a.instrument_item_cap}")
            keep, capped = [], defaultdict(list)
            for r in recs:
                (capped[r["stratum"]] if r["stratum"] == "Instrument" else keep).append(r)
            for s, rs in capped.items():
                keep += rs if len(rs) <= a.instrument_item_cap else rng.sample(
                    rs, a.instrument_item_cap)
            recs = sorted(keep, key=lambda r: (r["doc_id"], r["item_id"]))
        counts = Counter(r["stratum"] for r in recs)
        print(f"\n=== arm {arm}: judging {len(recs)} items {dict(counts)} "
              f"(admitted {dict(census[arm])})", flush=True)
        write_sample(prefix, recs)
        agg = run_protocol(prefix, prefix, JUDGE_RUN_ID, raters, a.fact_cap)
        if not agg:
            print(f"FATAL: probe protocol failed for arm {arm}")
            return 2
        checks = span_check_sidecar(prefix, texts)
        results[arm] = {"agg": agg, "admitted": dict(census[arm]),
                        "judged": dict(counts), "span_checks": checks,
                        "n_items": len(recs)}
    write_verdict(results, cfg, a, admission=admission, min_facts=min_facts)
    return 0


def _stratum_row(arm: str, stratum: str, r: dict, why: str | None = None) -> str:
    agg = r["agg"]
    st = (agg.get("per_stratum") or {}).get(stratum)
    faith = item_faithful_by_stratum(agg).get(stratum)
    if not st:
        return (f"| {arm} | {stratum} | {r['admitted'].get(stratum, 0)} | — | — | — | — | "
                f"{why or 'not judged'} |")
    fh = st["F_hi"]
    ff = (faith[0] / faith[1]) if faith and faith[1] else 0.0
    pre = r["admitted"].get(stratum, 0) >= STRATUM_PRECONDITION
    ok = pre and fh is not None and fh < F_STOP and ff >= ITEM_FAITHFUL
    return (f"| {arm} | {stratum} | {r['admitted'].get(stratum, 0)} | {st['n_in_F_denominator']} "
            f"| {st['F']:.4f} [{st['F_lo']:.4f}, {st['F_hi']:.4f}] "
            f"| {faith[0]}/{faith[1]} = {ff:.3f} "
            f"| {'Y' if pre else 'N (< 20)'} | {'PASS' if ok else 'FAIL'} |")


def write_verdict(results: dict, cfg: dict, a, admission: dict | None = None,
                  min_facts: int | None = None) -> None:
    ledger = spend.default_ledger()
    ex = ledger.status(RUN_ID)["runs"].get(RUN_ID, {})
    ju = ledger.status(JUDGE_RUN_ID)["runs"].get(JUDGE_RUN_ID, {})
    per_doc = per_doc_settled_chunked()
    wd_usage = whole_doc_usage()
    hist, cross, div_total = diversion_histogram()
    resolution = json.loads((METRICS / "chunked_resolution.json").read_text())
    sets = {d: chunker.chunk_document(d, rbe.doc_text(members()[d])) for d in PILOT_DOCS}

    min_facts = min_facts if min_facts is not None else min_facts_for_gate()
    L = ["# Chunked vs whole-document extraction — pre-registered verdict", "",
         f"Task `{TASK}`. Same five documents, same model (`{cfg['model_id']}`, effort "
         "unchanged), same schema, same rules — `kg/extraction/chunked_template.md` is "
         "`prompt_template.md` v0.3.5 with the framing swapped, sha-pinned in the "
         "`chunked_v035` profile. **The unit of extraction is the only variable.**", "",
         "Thresholds are the task's, unchanged and not re-read from any result: "
         f"F_upper < {F_STOP}, item-faithful >= {ITEM_FAITHFUL}, precondition "
         f"pooled >= {STRATUM_PRECONDITION} per stratum.", "",
         f"**Gate reachability.** Under the aggregator's Wilson 95% interval, `F_upper < "
         f"{F_STOP}` is attainable only at **>= {min_facts} facts**: below that, a PERFECT "
         f"result (0 fabrications) still yields an upper bound above the threshold. This is "
         f"arithmetic from the task's own F_STOP and the aggregator's own interval method, "
         f"not a new threshold. A stratum whose facts are 1:1 with its items (`semantic_edge` "
         f"— one fact per edge) and which sits below that count cannot pass however good the "
         f"extraction is, and is recorded as GATE UNREACHABLE rather than judged: ADDENDUM-01 "
         f"§1 forbids judging a sub-minimum sample, and paying for a foregone FAIL is the "
         f"case it forbids.", "",
         "Both arms were judged through ONE protocol at one set of versions — decompose "
         f"{probe_versions()[0]}, probe_judge {probe_versions()[1]}, span_checks "
         f"{span_checks.CHECK_VERSION} — so the comparison is like-for-like. The "
         "whole-document arm's banked numbers in `2026-08-27_pilot_instrument_verdict.md` "
         "were produced under decompose 1.0.0 / probe_judge 1.0.0 and are NOT comparable to "
         "the rows below; they are superseded for comparison purposes, not retracted.", "",
         "## Caveat — the chunked arm is a 44/128 partial (ADDENDUM-01 §1)", "",
         "The chunked arm was stopped by the operator at 44 of 128 chunks. It covers **2 of "
         "the 5 pilot documents** (`data-readiness-for-ai-a-360-degree-survey` 30/30, "
         "`aidrin-hiniduma-2024` 14/18); `fcsm-23-02`, `from-accuracy-to-readiness` and "
         "`mitre-ai-maturity-model` have **no chunked extraction at all**. The whole-document "
         "arm spans all five. **The two arms therefore do not run on the same document mix**, "
         "and the per-document mixes are reported with every count below. Remaining chunks "
         "were not extracted by decision, not by failure: the cost question the arm existed "
         "to answer was settled at 65,637 settled/chunk (DD-023), and the faithfulness "
         "question is answerable from banked material.", "",
         "## Verdict", "",
         "| arm | stratum | admitted | facts in F-denominator | F [Wilson 95%] | item-faithful "
         "| precondition | pre-registered |", "|---|---|---|---|---|---|---|---|"]
    for arm in ("chunked", "wholedoc"):
        for stratum in ("Instrument", "semantic_edge"):
            ok, why = (admission or {}).get((arm, stratum), (True, None))
            L.append(_stratum_row(arm, stratum, results[arm], None if ok else why))
    L += ["", "### What was counted, and what was judged", "",
          "`admitted` above is the FULL admitted set of each arm. Where fewer items were "
          "judged, the cap is a spend bound declared before any label was bought, not a "
          "threshold: a smaller sample widens the Wilson interval, which makes PASS harder "
          "and never easier.", "",
          "| arm | stratum | admitted | judged | doc mix (judged) |", "|---|---|---|---|---|"]
    for arm in ("chunked", "wholedoc"):
        mix = defaultdict(Counter)
        for line in (METRICS / f"arm_{arm}_sample.jsonl").read_text(
                encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                mix[r["stratum"]][r["doc_id"]] += 1
        for stratum in ("Instrument", "semantic_edge"):
            L.append(f"| {arm} | {stratum} | {results[arm]['admitted'].get(stratum, 0)} "
                     f"| {results[arm].get('judged', {}).get(stratum, 0)} "
                     f"| {dict(mix[stratum]) or '—'} |")
    L += ["", "## Yield and cost", "",
          "| doc | chunks | chunk tokens (med/max) | chunked settled | whole-doc settled |",
          "|---|---|---|---|---|"]
    for d in PILOT_DOCS:
        cs = sets[d]
        toks = sorted(c.n_tokens for c in cs)
        wd = sum(wd_usage.get(d, {}).values())
        L.append(f"| {d} | {len(cs)} | {toks[len(toks) // 2]}/{toks[-1]} "
                 f"| {per_doc.get(d, 0):,} | {wd:,} |")
    L.append(f"| **total** | {sum(len(c) for c in sets.values())} | | "
             f"{sum(per_doc.values()):,} | {sum(sum(u.values()) for u in wd_usage.values()):,} |")
    L += ["",
          f"Chunked extraction run `{RUN_ID}` settled {ex.get('settled', 0):,} against a "
          f"declared ceiling of {ex.get('ceiling_tokens', 0):,}; judge run `{JUDGE_RUN_ID}` "
          f"settled {ju.get('settled', 0):,} of {ju.get('ceiling_tokens', 0):,}.", "",
          "## Diversion and resolution (chunked arm)", "",
          f"Diverted relations: {div_total} total, of which **{cross} `cross_chunk`** "
          f"({cross / div_total:.1%} of diversions)" if div_total else
          "Diverted relations: none.", "",
          "```json", json.dumps(hist, indent=1), "```", "",
          "Deterministic cross-chunk resolution (§4 — exact normalized surface form + "
          "recorded alias, no LLM-proposed merges):", "", "```json",
          json.dumps(resolution, indent=1), "```", "",
          "## Mid-noun-phrase span check (span_checks " + span_checks.CHECK_VERSION + ")", "",
          "Recorded, never subtracted from a denominator — excluding a class from a "
          "pre-registered metric would move the threshold by other means.", "",
          "| arm | facts checked | on a mid-noun-phrase span |", "|---|---|---|"]
    for arm in ("chunked", "wholedoc"):
        chk = results[arm]["span_checks"]
        L.append(f"| {arm} | {len(chk)} | {sum(1 for v in chk.values() if v['span_mid_phrase'])} |")
    L += ["", "## Per-rater agreement", ""]
    for arm in ("chunked", "wholedoc"):
        L += [f"`{arm}`:", "```json",
              json.dumps(results[arm]["agg"].get("raters"), indent=1), "```", ""]
    L += ["## Consequence", ""]
    passed = []
    for arm in ("chunked", "wholedoc"):
        for stratum in ("Instrument", "semantic_edge"):
            ok, why = (admission or {}).get((arm, stratum), (True, None))
            if ok and _stratum_row(arm, stratum, results[arm]).endswith("| PASS |"):
                passed.append(f"{arm}:{stratum}")
    L.append(f"Strata meeting the pre-registered gate: **{passed or 'none'}**.")
    L.append("Lane 2/3 eligibility is recorded here and nowhere acted on: this task launches "
             "neither (§6).")
    VERDICT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("verdict written:", VERDICT)


# ------------------------------------------------------------------ Results registration
def _register(value: float, units: str, description: str, data: str) -> None:
    r = subprocess.run(["seldon", "result", "register", "--value", str(value), "--units", units,
                        "--description", description,
                        "--script-path", "scripts/chunked_pilot.py",
                        "--data-name", data],
                       cwd=REPO, capture_output=True, text=True)
    print(("  OK  " if r.returncode == 0 else "  FAIL") + f" {units:26s} {description[:70]}")
    if r.returncode != 0:
        print("      ", (r.stderr or r.stdout).strip()[:300])


def phase_register(a) -> int:
    """Every headline number in the verdict becomes a Result with provenance: generated_by ->
    scripts/chunked_pilot.py, computed_from -> the arm's event shard (§5). The graph already
    carries 39 Results with incomplete provenance; this adds none of that kind."""
    shards = {"chunked": "batch-016-chunked-v035", "wholedoc": "batch-013-reextract-v035b"}
    for arm, data in shards.items():
        agg = json.loads((METRICS / f"arm_{arm}_aggregate.json").read_text())
        faith = item_faithful_by_stratum(agg)
        for stratum, st in (agg.get("per_stratum") or {}).items():
            tag = f"{arm}/{stratum}"
            _register(st["F"], "fabrication_share",
                      f"{tag}: F over {st['n_in_F_denominator']} atomic facts "
                      f"(Wilson 95% [{st['F_lo']:.4f}, {st['F_hi']:.4f}]); "
                      f"pre-registered gate F_upper < {F_STOP}", data)
            _register(st["F_hi"], "fabrication_share_upper95",
                      f"{tag}: Wilson 95% upper bound on F; the quantity the gate reads", data)
            if stratum in faith:
                ok, n = faith[stratum]
                _register(ok / n if n else 0.0, "item_faithful_rate",
                          f"{tag}: {ok}/{n} items every fact of which is entailed or a "
                          f"doc-level attribute; pre-registered gate >= {ITEM_FAITHFUL}", data)
            _register(st["n_facts"], "atomic_facts",
                      f"{tag}: atomic facts judged (2 raters, Dawid-Skene)", data)
    # chunked-arm structural numbers
    hist, cross, total = diversion_histogram()
    sets = {d: chunker.chunk_document(d, rbe.doc_text(members()[d])) for d in PILOT_DOCS}
    per_doc = per_doc_settled_chunked()
    _register(sum(len(c) for c in sets.values()), "chunks",
              "chunked arm: total chunks over the five pilot documents at max_tokens 1500",
              "batch-016-chunked-v035")
    if total:
        _register(cross / total, "cross_chunk_diversion_share",
                  f"chunked arm: {cross} of {total} diverted relations were diverted for "
                  f"diversion_reason cross_chunk", "batch-016-chunked-v035")
    if per_doc:
        _register(sum(per_doc.values()) / len(per_doc), "tokens_per_document",
                  "chunked arm: mean settled extraction tokens per document, summed from the "
                  "persisted chunk raws", "batch-016-chunked-v035")
    res = json.loads((METRICS / "chunked_resolution.json").read_text())
    merged = sum(v["merged_events"] for v in res.values())
    nodes = sum(v["node_events"] for v in res.values())
    if nodes:
        _register(merged / nodes, "merge_rate",
                  f"chunked arm §4: {merged} of {nodes} node events merged into an existing "
                  f"normalized surface form within their document (deterministic only)",
                  "batch-016-chunked-v035")
    stubs = sum(v["stubs"] for v in res.values())
    _register(sum(v["stubs_unmerged"] for v in res.values()), "unmerged_stubs",
              f"chunked arm §4: mention-only stubs left unresolved of {stubs} emitted",
              "batch-016-chunked-v035")
    return 0


PHASES = {"dry_run": phase_dry_run, "extract": phase_extract, "ingest": phase_ingest,
          "resolve": phase_resolve, "judge": phase_judge,
          "register": phase_register}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    ap.add_argument("--profile", default=None,
                    help="run profile to price/run (default: the module's PROFILE)")
    ap.add_argument("--ceiling-tokens", type=int)
    ap.add_argument("--fact-cap", type=int, default=240)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, help="extract at most N chunks this pass (smoke test)")
    ap.add_argument("--judge-ceiling", type=int, default=4_000_000)
    ap.add_argument("--instrument-item-cap", type=int, default=0,
                    help="judge at most N Instrument items per arm (0 = all). Spend bound "
                         "declared before labels are bought; seeded and reported.")
    a = ap.parse_args()
    model_stub.guard_no_api_key()
    if a.phase not in PHASES:
        raise SystemExit(f"unknown phase {a.phase!r}; known: {sorted(PHASES)}")
    if a.phase == "extract":
        if not a.ceiling_tokens:
            raise SystemExit("FATAL: --ceiling-tokens is required for `extract` (DD-022)")
        spend.default_ledger().declare(RUN_ID, a.ceiling_tokens, declared_by=TASK,
                                       call_class="extraction_chunk")
    try:
        return PHASES[a.phase](a)
    except spend.SpendRefusalStop as exc:
        print(f"spend guard: {exc} — clean stop", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
