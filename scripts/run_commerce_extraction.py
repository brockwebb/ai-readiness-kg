#!/usr/bin/env python3
"""Chunk-level extraction of Commerce's "Generative AI and Open Data" guidance, one document.

Task `cc_tasks/2026-10-02_commerce_guidance_admission.md` decision 3. **Model spend, bounded:**
the run is declared on the shared ledger with the task's per-run ceiling (3,000,000 tokens),
reserve-then-settle at `kg/extraction/model_stub.invoke`. Claude Max OAuth only — the stub
refuses `ANTHROPIC_API_KEY` by name (DD-007) and that refusal is a stop, never a fallback.

**Why a driver rather than `run_bulk_extraction.py --only`, which the task names.** The task
says to use the standing runner "under the same profile the v038 burn used". That profile is
`bulk_v038`, whose emission contract is `anchor` (chunk-unit, DD-023), and
`run_bulk_extraction.apply_profile` refuses it by design — the runner is whole-document and
would send a chunk-local prompt over a whole document. The only code that runs `bulk_v038` is
`chunked_pilot`, reached through a driver that supplies a worklist; `run_g1eval_extraction.py`
and `run_strand_extraction.py` are the two precedents and this is the same file with a
one-document cohort. **Every extraction primitive is delegated to `chunked_pilot`, imported
and not copied** — the scientific requirement `run_chunked_bulk` records: Phase A qualified a
harness, and a run through different code would have qualified something else.

Checkpointing is `chunked_pilot`'s (engineering standard §15): each chunk's raw response is
persisted under `events/raw/bulk_v038/` as it lands, keyed by doc, chunk, source sha and model,
and a re-run skips every chunk whose raw exists — re-running `--phase extract` IS the resume.

    /opt/anaconda3/bin/python3 scripts/run_commerce_extraction.py --phase plan --productive-tokens N
    /opt/anaconda3/bin/python3 scripts/run_commerce_extraction.py --phase extract --ceiling-tokens 3000000 [--workers 6]
    /opt/anaconda3/bin/python3 scripts/run_commerce_extraction.py --phase ingest
    /opt/anaconda3/bin/python3 scripts/run_commerce_extraction.py --phase spend
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

import chunked_pilot as cp  # noqa: E402
import run_chunked_bulk as rcb  # noqa: E402
import run_g1eval_extraction as rge  # noqa: E402  (REQUESTED_STATES: why `extracted` counts)
import run_strand_extraction as rse  # noqa: E402  (plan, ceiling, settled_by_run)

TASK = "cc_tasks/2026-10-02_commerce_guidance_admission.md"
PROFILE = rcb.PROFILE                      # bulk_v038, the pinned production profile
RUN_ID = "commerce_guidance_extraction_2026-10-02"
STATE = REPO / "state" / "commerce_guidance_extraction_2026-10-02.json"
DOC_ID = "generative-ai-and-open-data-guidelines-and-best-practices-de"

#: The most recent MEASURED productive rate (DD-042), from the strand run: 10,988,869 tokens
#: settled over 225 chunks under this same profile, prompt and model. Read off the
#: registered Result by the caller and passed in; the denominator is fixed here because it
#: is the chunk count that Result was measured over.
RATE_RESULT = "strand_extraction_tokens_productive"
RATE_CHUNKS = 225


def cohort() -> list:
    """One document, and only if the queue can show an `extraction_request` for it."""
    row = queue.project().get(DOC_ID) or {}
    if row.get("extraction_state") not in rge.REQUESTED_STATES:
        raise SystemExit(f"FATAL: {DOC_ID} carries no extraction_request (state "
                         f"{row.get('extraction_state')!r}) — run `python -m kg queue add` first")
    return [DOC_ID]


def bind(docs: list) -> dict:
    """The strand driver's binding, under this run's id. Nothing else is rebound."""
    prof = cp.apply_arm(PROFILE, None, RUN_ID)
    if prof.get("shard_tag"):
        raise SystemExit(
            f"FATAL: profile {PROFILE!r} declares shard_tag={prof['shard_tag']!r}; "
            f"eventlog.replay() skips tagged shards, so this run would never reach the graph.")
    cp.PURPOSE = PROFILE
    cp.DOC_PATHS = rcb.document_paths()
    if DOC_ID not in cp.DOC_PATHS:
        raise SystemExit(f"FATAL: {DOC_ID} has no canonical_path in the manifest")
    cp.DOCS = list(docs)
    cp.CHUNK_FILTER = None                 # every chunk of the document
    return prof


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "extract", "ingest", "spend"), required=True)
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--productive-tokens", type=int, default=None,
                    help=f"the measured productive total behind the rate ({RATE_RESULT})")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reingest", action="store_true")
    a = ap.parse_args(argv)

    docs = cohort()
    bind(docs)

    if a.phase == "plan":
        p = rse.plan(docs)
        if a.productive_tokens:
            c = rse.ceiling(p["chunks"], a.productive_tokens, RATE_CHUNKS)
            c["rate_result"] = RATE_RESULT
            p["ceiling"] = c
        print(json.dumps(p, indent=1))
        STATE.write_text(json.dumps({"task": TASK, "run_id": RUN_ID, "profile": PROFILE,
                                     "cohort": docs, "plan": p}, indent=1) + "\n",
                         encoding="utf-8")
        print(f"-> {STATE.relative_to(REPO)}", file=sys.stderr)
        return 0

    if a.phase == "spend":
        print(json.dumps(rse.settled_by_run(RUN_ID), indent=1))
        return 0

    if a.phase == "extract":
        if not a.ceiling_tokens:
            raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
        spend.default_ledger().declare(RUN_ID, a.ceiling_tokens,
                                       declared_by=f"scripts/run_commerce_extraction.py ({TASK})",
                                       call_class="extraction_chunk")
        p = rse.plan(docs)
        print(f"{p['chunks']} chunks, profile {PROFILE}, ceiling {a.ceiling_tokens:,} "
              f"(floor estimate {p['tokens_at_floor']:,})", flush=True)
        args = type("A", (), {"shared_with": None, "only": None, "limit": None,
                              "workers": a.workers})()
        return cp.phase_extract(args)

    return cp.phase_ingest(type("A", (), {"reingest": bool(a.reingest)})())


if __name__ == "__main__":
    raise SystemExit(main())
