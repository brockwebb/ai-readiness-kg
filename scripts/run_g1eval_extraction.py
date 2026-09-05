#!/usr/bin/env python3
"""Chunk-level extraction of the 17 `g1eval-2026-09-02` prior-art sources.

Task `cc_tasks/2026-09-04_extract_g1eval_17_and_rerun.md` §1. **Model spend, bounded:** the
run is declared on the shared ledger with the task's own ceiling (13,280,000, priced in the
extraction-gap RESULT §3 at 664 chunks × the 20,000 `extraction_chunk` floor), reserve-then-
settle at `kg/extraction/model_stub.invoke` as normal. Claude Max OAuth only — the stub
refuses `ANTHROPIC_API_KEY` by name (DD-007) and that refusal is a stop, never a fallback.

**Why a driver rather than `run_chunked_bulk.py --phase burn`:** that driver's worklist is
`compute_cut()`, the DD-024 demand-pull cut over `state/t2_priority.json`. These 17 carry no
consumer demand — being unasked-for is the whole reason they were never extracted — so the
burn set does not contain them and cannot be made to without editing the priority file, which
belongs to the biblio cron. This driver supplies only the worklist and the ledger
declaration; **every extraction primitive is delegated to `chunked_pilot`, imported and not
copied**, exactly as `run_chunked_bulk.apply_production_profile` / `bind_confirmation_run` do
it. That delegation is the same scientific requirement `run_chunked_bulk` records: Phase A
qualified a harness, and a run using different code would have qualified something else.

    /opt/anaconda3/bin/python3 scripts/run_g1eval_extraction.py --phase plan
    /opt/anaconda3/bin/python3 scripts/run_g1eval_extraction.py --phase extract --ceiling-tokens 13280000 [--workers 2]
    /opt/anaconda3/bin/python3 scripts/run_g1eval_extraction.py --phase ingest
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

TASK = "cc_tasks/2026-09-04_extract_g1eval_17_and_rerun.md"
EPOCH = "g1eval-2026-09-02"
PROFILE = rcb.PROFILE                      # bulk_v038, the pinned production profile
RUN_ID = "g1eval_extraction_2026-09-04"
STATE = REPO / "state" / "g1eval_extraction_2026-09-04.json"


def cohort() -> list:
    """The 17, as the intersection of the epoch declaration and the live worklist. Both
    conditions are required: the epoch says which documents these are, and the worklist says
    an `extraction_request` justifies running them (nothing runs off an ad-hoc list)."""
    members = set(queue.corpus_epochs().get(EPOCH) or ())
    if not members:
        raise SystemExit(f"FATAL: no corpus_epoch_declared {EPOCH} in the dixie ledger")
    requested = set(queue.worklist(PROFILE))
    cohort = sorted(members & requested)
    missing = sorted(members - requested)
    if missing:
        raise SystemExit(f"FATAL: {len(missing)} epoch member(s) carry no live extraction_request "
                         f"— run `python -m kg queue add` first: {missing[:5]}")
    return cohort


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
    """Chunk count per document under the pipeline's own chunker, and the reserve estimate."""
    # `rbe.doc_text` is the loader `chunked_pilot.chunk_sets` itself calls: DD-030 substrate
    # where one exists, the PDF reader otherwise. Reading the file directly instead — which
    # this function did in its first draft — feeds a PDF's raw bytes to the chunker and
    # inflates the plan twentyfold (13,121 chunks against the true 664). A plan computed on
    # text the extractor will not see is not a plan.
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


def settled_by_run(run_id: str = RUN_ID) -> dict:
    """(reserved, settled, per-doc settled) read back off the shared ledger — the record, not
    a tally this script keeps."""
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
            doc = (res.get(r.get("reservation_id")) or "").split("#")[0]
            per[doc] = per.get(doc, 0) + n
    return {"reserved_tokens": reserved, "settled_tokens": settled, "settled_per_document": per}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "extract", "ingest", "spend"), required=True)
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reingest", action="store_true")
    a = ap.parse_args(argv)

    docs = cohort()
    bind(docs)

    if a.phase == "plan":
        p = plan(docs)
        print(json.dumps(p, indent=1))
        STATE.write_text(json.dumps({"task": TASK, "run_id": RUN_ID, "profile": PROFILE,
                                     "cohort": docs, "plan": p}, indent=1) + "\n",
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
                                       declared_by=f"scripts/run_g1eval_extraction.py ({TASK})",
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
