#!/usr/bin/env python3
"""Chunk-level extraction of the DCAT-US 3.0 intake (epoch `dcat-us-3-2026-10-04`).

Task `cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md` step 2, DN-011-R2: the documents
are admitted so they are queryable, and `search_text` reads the graph's Definition layer, which
only extraction writes. **Model spend, bounded:** the run is declared on the shared ledger with
a per-run ceiling computed per DD-042 from a measured rate, reserve-then-settle at
`kg/extraction/model_stub.invoke`. Claude Max OAuth only — the stub refuses
`ANTHROPIC_API_KEY` by name (DD-007) and that refusal is a stop, never a fallback.

This is `scripts/run_commerce_extraction.py` with an epoch cohort in place of one document, for
the reason that file records: the pinned production profile `bulk_v038` is anchor-contract and
chunk-unit (DD-023), `run_bulk_extraction.apply_profile` refuses it, and the only code that runs
it is `chunked_pilot`. **Every extraction primitive is delegated to `chunked_pilot`, imported
and not copied.**

Checkpointing is `chunked_pilot`'s (engineering standard §15): each chunk's raw response is
persisted under `events/raw/bulk_v038/` as it lands, keyed by doc, chunk, source sha and model,
and a re-run skips every chunk whose raw exists — re-running `--phase extract` IS the resume.
`--only DOC` restricts a phase to one document, which is how the pilot is run. `--cohort a01`
runs the epoch DCAT-002's ADDENDUM_01 declared, under its own run id.

    /opt/anaconda3/bin/python3 scripts/run_dcat_extraction.py --phase plan
    /opt/anaconda3/bin/python3 scripts/run_dcat_extraction.py --phase extract --ceiling-tokens N [--only DOC] [--workers 4]
    /opt/anaconda3/bin/python3 scripts/run_dcat_extraction.py --phase ingest
    /opt/anaconda3/bin/python3 scripts/run_dcat_extraction.py --phase spend
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
import run_strand_extraction as rse  # noqa: E402  (plan, settled_by_run)

TASK = "cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md"
PROFILE = rcb.PROFILE                      # bulk_v038, the pinned production profile
RUN_ID = "dcat_us_3_extraction_2026-10-04"
EPOCH = "dcat-us-3-2026-10-04"
STATE = REPO / "state" / "dcat_us_3_extraction_2026-10-04.json"

#: Each epoch this driver has extracted, by the name `--cohort` takes. `base` is DCAT-002's own
#: and the module defaults above; `a01` is its ADDENDUM_01 (DN-011-R4), admitted by
#: `scripts/admit_dcat_002_a01.py`. A cohort is its own run on the spend ledger, so its ceiling
#: and settled total are reported apart from the base run's.
COHORTS = {
    "base": dict(TASK=TASK, RUN_ID=RUN_ID, EPOCH=EPOCH, STATE=STATE),
    "a01": dict(
        TASK="cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md",
        RUN_ID="dcat_us_3_a01_extraction_2026-10-05",
        EPOCH="dcat-us-3-a01-2026-10-05",
        STATE=REPO / "state" / "dcat_us_3_a01_extraction_2026-10-05.json"),
}


def cohort(only: str | None = None) -> list:
    """The epoch's members, each only if the queue can show an `extraction_request` for it.

    Membership is read from the `corpus_epoch_declared` event through `kg.queue.corpus_epochs`,
    the reader `run_bulk_extraction.corpus_members` also uses. Ledger entries carry no epoch
    field, which is why `python -m kg queue add-epoch` (it reads entry fields) finds none of
    these documents and they are queued by doc_id instead."""
    members = sorted(queue.corpus_epochs().get(EPOCH) or [])
    if not members:
        raise SystemExit(f"FATAL: no corpus_epoch_declared {EPOCH!r} event in the ledger")
    rows = queue.project()
    unrequested = [d for d in members
                   if (rows.get(d) or {}).get("extraction_state") not in rge.REQUESTED_STATES]
    if unrequested:
        raise SystemExit(f"FATAL: no extraction_request for {unrequested} — run "
                         f"`python -m kg queue add <doc_id> ...` first")
    if only:
        if only not in members:
            raise SystemExit(f"FATAL: {only} is not a member of {EPOCH}")
        return [only]
    return members


def bind(docs: list) -> dict:
    """The strand driver's binding, under this run's id. Nothing else is rebound."""
    prof = cp.apply_arm(PROFILE, None, RUN_ID)
    if prof.get("shard_tag"):
        raise SystemExit(
            f"FATAL: profile {PROFILE!r} declares shard_tag={prof['shard_tag']!r}; "
            f"eventlog.replay() skips tagged shards, so this run would never reach the graph.")
    cp.PURPOSE = PROFILE
    cp.DOC_PATHS = rcb.document_paths()
    missing = [d for d in docs if d not in cp.DOC_PATHS]
    if missing:
        raise SystemExit(f"FATAL: no canonical_path in the manifest for {missing}")
    cp.DOCS = list(docs)
    cp.CHUNK_FILTER = None                 # every chunk of each document
    return prof


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "extract", "ingest", "spend"), required=True)
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--only", default=None, help="restrict the phase to one epoch member")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reingest", action="store_true")
    ap.add_argument("--cohort", choices=sorted(COHORTS), default="base",
                    help="which declared epoch to run (default: base, DCAT-002's own)")
    a = ap.parse_args(argv)
    globals().update(COHORTS[a.cohort])     # the module globals every function reads

    docs = cohort(a.only)
    bind(docs)

    if a.phase == "plan":
        p = rse.plan(docs)
        print(json.dumps(p, indent=1))
        STATE.write_text(json.dumps({"task": TASK, "run_id": RUN_ID, "profile": PROFILE,
                                     "epoch": EPOCH, "cohort": docs, "plan": p}, indent=1)
                         + "\n", encoding="utf-8")
        print(f"-> {STATE.relative_to(REPO)}", file=sys.stderr)
        return 0

    if a.phase == "spend":
        print(json.dumps(rse.settled_by_run(RUN_ID), indent=1))
        return 0

    if a.phase == "extract":
        if not a.ceiling_tokens:
            raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
        led = spend.default_ledger()
        status = led.status().get("runs", {}).get(RUN_ID) if hasattr(led, "status") else None
        if status is None or int(status.get("ceiling_tokens") or 0) != a.ceiling_tokens:
            led.declare(RUN_ID, a.ceiling_tokens,
                        declared_by=f"scripts/run_dcat_extraction.py ({TASK})",
                        call_class="extraction_chunk",
                        **({"supersede": True} if status is not None else {}))
        p = rse.plan(docs)
        print(f"{p['chunks']} chunks over {len(docs)} document(s), profile {PROFILE}, run "
              f"ceiling {a.ceiling_tokens:,} (floor estimate {p['tokens_at_floor']:,})",
              flush=True)
        args = type("A", (), {"shared_with": None, "only": None, "limit": None,
                              "workers": a.workers})()
        return cp.phase_extract(args)

    return cp.phase_ingest(type("A", (), {"reingest": bool(a.reingest)})())


if __name__ == "__main__":
    raise SystemExit(main())
