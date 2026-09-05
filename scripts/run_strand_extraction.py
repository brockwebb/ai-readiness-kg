#!/usr/bin/env python3
"""Chunk-level extraction of the AI-ready-data-product strand.

Task `cc_tasks/2026-09-05_extract_ai_ready_strand_11.md` §1-§2. **Model spend, bounded:** the
run is declared on the shared ledger with a per-run ceiling COMPUTED FROM THE MEASURED RATE
(DD-042), reserve-then-settle at `kg/extraction/model_stub.invoke`. Claude Max OAuth only —
the stub refuses `ANTHROPIC_API_KEY` by name (DD-007) and that refusal is a stop, never a
fallback.

**The cohort is derived, not listed.** `cohort()` recomputes the §3a rule — a document with
at least `MIN_HITS` sentences judged `data_product_consumption` in
`assessment/results/ai_ready_term_contexts_2026-09-04.jsonl` — from the registered DataFile
itself, then intersects it with the documents the queue can show a live `extraction_request`
for. A hardcoded list of eleven doc_ids would have been shorter and would have made the task
file, not the evidence, the authority for who is in the strand; it would also have silently
kept the UK duplicate that §0.1 cut, because a list does not know about a deferral.

**Why a driver rather than `run_chunked_bulk.py --phase burn`:** identical to the reason
recorded in `run_g1eval_extraction.py` — that driver's worklist is `compute_cut()` over
`state/t2_priority.json`, the DD-024 demand-pull cut owned by the biblio cron. This strand's
consumer is a competency question, not the priority file. This driver supplies only the
worklist and the ledger declaration; **every extraction primitive is delegated to
`chunked_pilot`, imported and not copied.**

    /opt/anaconda3/bin/python3 scripts/run_strand_extraction.py --phase plan
    /opt/anaconda3/bin/python3 scripts/run_strand_extraction.py --phase extract --ceiling-tokens N [--workers 2]
    /opt/anaconda3/bin/python3 scripts/run_strand_extraction.py --phase ingest
    /opt/anaconda3/bin/python3 scripts/run_strand_extraction.py --phase spend
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg import queue, spend  # noqa: E402
from kg.extraction import chunker  # noqa: E402

import chunked_pilot as cp  # noqa: E402
import run_bulk_extraction as rbe  # noqa: E402
import run_chunked_bulk as rcb  # noqa: E402

TASK = "cc_tasks/2026-09-05_extract_ai_ready_strand_11.md"
PROFILE = rcb.PROFILE                      # bulk_v038, the pinned production profile
RUN_ID = "strand_extraction_2026-09-05"
STATE = REPO / "state" / "strand_extraction_2026-09-05.json"

#: The §3a harvest, as registered. The senses on it are a person's judgments, merged by
#: `harvest_ai_ready_contexts.py --judge`; this script re-reads them and never re-judges.
HARVEST = REPO / "assessment" / "results" / "ai_ready_term_contexts_2026-09-04.jsonl"
SENSE = "data_product_consumption"

#: §0.1's inclusion threshold. Three is the operator's line, declared in the task before the
#: per-document counts below it were looked at; it is a config value here rather than a magic
#: number in a comprehension because moving it is a scientific decision, not a code change.
MIN_HITS = 3

#: The g1eval run's MEASURED productive rate and the headroom §1 declares. DD-042: a ceiling
#: is computed from the measured rate, never from the call-class floor — the floor is the
#: guard's first-call estimate and priced the g1eval run at a fifth of its true cost.
RATE_RESULT = "g1eval_extraction_tokens_productive"     # 31,299,448 tokens
RATE_CHUNKS = 688                                       # over 688 chunks
HEADROOM = 1.15


def sense_hits() -> dict:
    """{doc_id: number of `data_product_consumption` sentences} from the §3a harvest."""
    if not HARVEST.is_file():
        raise SystemExit(f"FATAL: {HARVEST.relative_to(REPO)} is missing; the cohort rule has "
                         f"no evidence to read")
    out: dict = {}
    for line in HARVEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("sense") == SENSE:
            out[r["doc_id"]] = out.get(r["doc_id"], 0) + 1
    return out


def cohort() -> list:
    """The strand, by rule: >= MIN_HITS `data_product_consumption` sentences, minus anything
    a live deferral cuts, intersected with the documents carrying an extraction_request."""
    hits = sense_hits()
    selected = {d for d, n in hits.items() if n >= MIN_HITS}
    defers = queue.deferrals()
    cut = {d: (defers[d].get("reason") or "") for d in selected if d in defers
           and (defers[d].get("reason") or "").startswith("duplicate_of:")}
    selected -= set(cut)
    rows = queue.project()
    # `extracted` is in the set for the reason `run_g1eval_extraction.REQUESTED_STATES`
    # records: a completed run consumes its request, so gating on the live worklist makes
    # every read-only phase fail the moment the extraction it reports on succeeds.
    ok = {d for d in selected
          if (rows.get(d) or {}).get("extraction_state") in
          ("queued", "stale", "extracting", "extracted")}
    missing = sorted(selected - ok)
    if missing:
        raise SystemExit(f"FATAL: {len(missing)} strand member(s) carry no extraction_request "
                         f"— run `python -m kg queue add` first: {missing[:5]}")
    return sorted(ok)


def bind(docs: list) -> dict:
    """Point `chunked_pilot`'s extraction path at this cohort under the production profile.
    Same three rebindings `run_chunked_bulk` performs, and nothing else."""
    prof = cp.apply_arm(PROFILE, None, RUN_ID)
    if prof.get("shard_tag"):
        raise SystemExit(
            f"FATAL: profile {PROFILE!r} declares shard_tag={prof['shard_tag']!r}; "
            f"eventlog.replay() skips tagged shards, so this run would never reach the graph.")
    cp.PURPOSE = PROFILE
    cp.DOC_PATHS = rcb.document_paths()
    cp.DOCS = list(docs)
    cp.CHUNK_FILTER = None                 # every chunk of every cohort document
    return prof


def plan(docs: list) -> dict:
    """Chunk count per document under the pipeline's own chunker, and the DD-042 ceiling.

    `rbe.doc_text` is the loader `chunked_pilot.chunk_sets` itself calls (DD-030 substrate
    where one exists, the PDF reader otherwise). A plan computed on text the extractor will
    not see is not a plan."""
    cfg = chunker.load_config()
    per, total = {}, 0
    for d in docs:
        path = cp.DOC_PATHS.get(d)
        text = rbe.doc_text(pathlib.Path(path), d) if path else ""
        n = len(chunker.chunk_document(d, text, cfg).chunks) if text.strip() else 0
        per[d] = n
        total += n
    floor = int(spend._spend_config()["call_class_floors"]["extraction_chunk"])
    return {"documents": len(docs), "chunks_per_document": per, "chunks": total,
            "chunk_floor": floor, "tokens_at_floor": total * floor}


def ceiling(chunks: int, productive: int, chunk_denominator: int = RATE_CHUNKS) -> dict:
    """DD-042: chunks x the MEASURED tokens/chunk x headroom, rounded up to a whole token.

    `productive` is passed in rather than read here so the caller has to name where the
    measurement came from; the caller reads it off the registered Result."""
    rate = productive / chunk_denominator
    return {"chunks": chunks, "rate_result": RATE_RESULT,
            "rate_productive_tokens": productive, "rate_chunks": chunk_denominator,
            "measured_tokens_per_chunk": rate, "headroom": HEADROOM,
            "ceiling_tokens": int(-(-chunks * rate * HEADROOM // 1))}


def settled_by_run(run_id: str = RUN_ID) -> dict:
    """(reserved, settled, per-doc settled) read back off the shared ledger — the record, not
    a tally this script keeps. `wasted` is settled tokens on a reservation whose document
    produced no accepted extraction, which §2 requires be reported even when it is zero."""
    per, reserved, settled = {}, 0, 0
    res = {}
    for line in (REPO / "state" / "spend_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("run_id") != run_id:
            continue
        if r.get("record") == "reserve":
            reserved += int(r.get("estimate_tokens") or 0)
            res[r.get("reservation_id")] = r.get("doc_id")
        elif r.get("record") == "settle":
            n = int(r.get("actual_tokens") or 0)
            settled += n
            key = res.get(r.get("reservation_id")) or ""
            per[key] = per.get(key, 0) + n
    return {"reserved_tokens": reserved, "settled_tokens": settled,
            "settled_per_chunk_key": per}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "extract", "ingest", "spend"), required=True)
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--productive-tokens", type=int, default=None,
                    help="the measured productive total behind the rate; required for --phase plan")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reingest", action="store_true")
    a = ap.parse_args(argv)

    docs = cohort()
    bind(docs)

    if a.phase == "plan":
        p = plan(docs)
        if a.productive_tokens:
            p["ceiling"] = ceiling(p["chunks"], a.productive_tokens)
        print(json.dumps(p, indent=1))
        STATE.write_text(json.dumps({"task": TASK, "run_id": RUN_ID, "profile": PROFILE,
                                     "cohort": docs, "sense_hits": sense_hits(),
                                     "min_hits": MIN_HITS, "plan": p}, indent=1) + "\n",
                         encoding="utf-8")
        print(f"-> {STATE.relative_to(REPO)}", file=sys.stderr)
        return 0

    if a.phase == "spend":
        print(json.dumps(settled_by_run(), indent=1))
        return 0

    if a.phase == "extract":
        if not a.ceiling_tokens:
            raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
        spend.default_ledger().declare(RUN_ID, a.ceiling_tokens,
                                       declared_by=f"scripts/run_strand_extraction.py ({TASK})",
                                       call_class="extraction_chunk")
        p = plan(docs)
        print(f"{p['chunks']} chunks over {len(docs)} documents, profile {PROFILE}, "
              f"ceiling {a.ceiling_tokens:,} (floor estimate {p['tokens_at_floor']:,})")
        args = type("A", (), {"shared_with": None, "only": None, "limit": None,
                              "workers": a.workers})()
        return cp.phase_extract(args)

    return cp.phase_ingest(type("A", (), {"reingest": bool(a.reingest)})())


if __name__ == "__main__":
    raise SystemExit(main())
