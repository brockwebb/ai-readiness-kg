#!/usr/bin/env python3
"""The DD-029 acceptance sample on the cohort DCAT-004 v2 extracted. **Model spend, bounded.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decision 1: "run the DD-029
acceptance sample on the batch (audit A-07 applies to this cohort)". Audit A-07
(`docs/audit/2026-10-04_full_audit.md`) found the Commerce and DCAT cohorts projected with no
faithfulness sample because their driver, `scripts/run_dcat_extraction.py`, never called the
burn's judge. This script calls it: `run_chunked_bulk.judge_batch`, the standing sequential test
(Wald SPRT on the batch fabrication rate, p0 = 0.05, p1 = 0.10, alpha = beta = 0.05, DD-029),
with the burn's own budget rule (twice the expected sample number at the indifference rate) and
raters (`primary_judge_model_id`, `secondary_judge_model_id`), over the cohort's admitted node
items, read from the live shard by `chunked_pilot.shard_items` exactly as the burn reads them.
Nothing is copied; the cohort binding is `scripts/dcat_brief_extract.py`'s.

The batch is the epoch `dcat-us-3-brief-2026-10-07`. Its judge run is declared on the shared
ledger before any call (ceiling: 1.15 x the largest measured bulk_v038 batch judge run, 3,870,131
on b005, rounded up). The probe's labels persist under `corpus/staging/metrics/`, so re-running
is the resume, as the burn's is.

**On a reject.** DD-029 quarantines a rejected batch's shard out of the projection with a
`bulk_batch_quarantined` event naming it. `build_projection.quarantined_batches` excludes events
by their `batch_id`, and this cohort's node events carry none (the DCAT driver stamps no batch
id, audit A-07's own finding), so such an event would exclude nothing. On a reject this script
records the event and the verdict, and exits 4 so the caller does not project; it does not
pretend the exclusion took effect.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_acceptance.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import dcat_brief_extract as DBE  # noqa: E402  (registers the cohort)
import run_dcat_extraction as rde  # noqa: E402
import chunked_pilot as cp  # noqa: E402
import run_chunked_bulk as rcb  # noqa: E402
import run_bulk_extraction as rbe  # noqa: E402
from kg import spend  # noqa: E402
from kg.extraction import model_stub  # noqa: E402

BATCH_ID = "dcat_us_3_brief_2026-10-07"
#: 1.15 x the largest measured bulk_v038 batch judge run (b005, 3,870,131 settled).
JUDGE_CEILING = 4_450_651
VERDICT = REPO / "reports" / "dcat_us_3_brief" / "run" / "acceptance_sample.json"


def main() -> int:
    vars(rde).update(rde.COHORTS[DBE.COHORT])
    docs = rde.cohort()
    rde.bind(docs)
    nodes, _e, _s = cp.shard_items()
    items = [ev for d in docs for ev in nodes.get(d, [])]
    b = rcb.sprt_boundaries()
    n_min = rcb.min_facts_for_accept(b)
    budget = int(math.ceil(2 * rcb.expected_sample_number(b, b["slope"])))
    cfg = model_stub.load_model_config()
    raters = [cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]]
    print(f"{BATCH_ID}: {len(items)} admitted node items over {docs}; SPRT minimum {n_min} facts, "
          f"budget {budget} facts; raters {raters}", flush=True)
    if len(items) < n_min:
        verdict = {"outcome": "sampling_inconclusive", "batch_id": BATCH_ID, "items_available": len(items)}
    else:
        rcb.declare_once(rcb.judge_run_id(BATCH_ID), JUDGE_CEILING, "judge")
        m = cp.members()
        texts = {d: rbe.doc_text(m[d], d) for d in docs}
        try:
            verdict = rcb.judge_batch(BATCH_ID, items, texts, budget, raters)
        except spend.SpendRefusalStop as exc:
            verdict = {"outcome": "stopped_by_spend_refusal", "batch_id": BATCH_ID, "reason": str(exc)}
    verdict.update({"task": DBE.TASK, "documents": docs, "plan": {k: b[k] for k in ("p0", "p1", "alpha", "beta")},
                    "budget_facts": budget, "min_facts_for_accept": n_min, "raters": raters,
                    "judge_run": rcb.judge_run_id(BATCH_ID), "judge_ceiling": JUDGE_CEILING})
    VERDICT.parent.mkdir(parents=True, exist_ok=True)
    VERDICT.write_text(json.dumps(verdict, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: verdict.get(k) for k in ("outcome", "facts", "fabrications", "items_sampled",
                                                  "items_available", "sprt_trace")}, indent=1, default=str))
    if verdict["outcome"] == "reject":
        rcb.quarantine_batch(BATCH_ID, "SPRT reject boundary crossed (events carry no batch_id; "
                                       "see scripts/dcat_brief_acceptance.py)", verdict)
        return 4
    return 0 if verdict["outcome"] in ("accept", "sampling_inconclusive") else 3


if __name__ == "__main__":
    raise SystemExit(main())
