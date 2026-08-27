# ADDENDUM-02 to `2026-08-26_overnight_burn.md` (Seldon cd8449de)

**Date:** 2026-08-27 ~07:50 ET
**Supersedes:** ADDENDUM-01's pilot precondition and every wall-clock stop in the task and ADDENDUM-01. Prompt stays **v0.3.5** — no v0.3.6. Threshold unchanged (F_upper < 0.10 per stratum, item-level faithful ≥ 0.70).

## Defects acknowledged (Desktop authorship, both)

1. ADDENDUM-01's precondition was a per-document conjunction. A document that states no relations produces zero semantic edges under a correct prompt; the precondition read that as failure. The precondition's job is to distinguish "prompt/harness produced nothing" from "document contains nothing" — a per-doc conjunction cannot, a pooled per-stratum count can.
2. The 04:45 ET stop was written for a night that had already ended when CC executed. Wall stops below are absolute UTC timestamps, not clock times.

## Wall stop (all invocations)

`WALL_STOP=2026-08-28T03:30:00Z` (23:30 ET tonight). On a `scope=daily` refusal before that time, the lane **sleeps until 00:05Z and retries** rather than stopping — the UTC band rolls at 20:00 ET and the operator's instruction is to run to the limit. `scope=run` refusals and gate FAILs stop as before.

## Lane 1″ — pilot, stratum-matched docs, pooled precondition; run id `pilot_v035b`, ceiling 4M

- **Docs (5):** the 3 prior pilot docs (already cached, re-extraction under v0.3.5 is already on disk — reuse those extractions, do not re-run them) **plus** the 2 manifested documents with the highest semantic-edge count in the current projection (`has_component`/`subtype_of`/`consumes`/`extends`/`implements`, either epoch), excluding the 3. Report the 2 ids and their prior edge counts.
- **Precondition (pooled, pre-registered here):** across the 5 docs, admitted Instrument nodes ≥ 20 **and** admitted semantic edges ≥ 20. Not met ⇒ `FAIL:harness_or_prompt`, no judge, raws diagnosed. Met ⇒ judge.
- **Judge:** all admitted items in both strata across the 5 docs, capped at 120 facts per stratum (random if over); probe protocol unchanged (decompose, two raters, batch 10, Dawid-Skene, ±400 window, literal-attribute full-document check).
- Verdict: `docs/research/2026-08-27_pilot_reextract_v035b_verdict.md`. PASS ⇒ Lanes 2 ∥ 3 exactly as the task specifies, profile `reextract_v035`, second detached invocation. FAIL ⇒ closed; top-3 patterns; no further prompt revision today.

## Lane 4 — resume, not restart

State on the shard: 5,554 stage-1 proposals, 1,240 stage-2 judgments. Resume stage 2 from the first unjudged proposal (idempotent: skip any proposal with an existing judgment event). Then, in order, exactly as the task specifies: the 100-item class acceptance sample at ≥ 0.90 (gate before wire; `restoration_class_accepted` only on PASS), relocation resume under `repair_resume`, the 50-item re-judge. Run id `restoration_v2_resume`, ceiling 55M. Runs concurrently with Lane 1″ (Lane 4 gets `MAX_CONCURRENT_MODEL_CALLS=2`, Lane 1″ gets 1).

## Exit for CC

Lane 1″ verdict on disk; Lane 4 resumed and its first 3 stage-2 calls' cache-read check logged; on PASS, Lanes 2 ∥ 3 running detached. Dated section appended to the RESULT. The SUMMARY at final driver exit (`docs/research/2026-08-27_overnight_burn_SUMMARY.md`) is the closeout for the whole task across all invocations, read from the ledger.
