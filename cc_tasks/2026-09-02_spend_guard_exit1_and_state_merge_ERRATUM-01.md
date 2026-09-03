# ERRATUM-01 to `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md` — §2.4 closing sentence

**Date:** 2026-09-02
**Issued by:** `cc_tasks/2026-09-02_post_burn_reconciliation.md` (finding F1)
**The RESULT is immutable and is not edited. This file corrects it.**

## What §2.4 says (wrong)

> **15/15 match** the file on disk and §21.6 (13 accept, 1 sampling_inconclusive, 0 reject).
> Sum of fabrications/facts over the 14 judged batches: 37/1,474, as §21.6 states.

The closing sentence copied §21.6 of `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md`
instead of summing the table immediately above it. That table has fourteen judged rows with
facts and one `sampling_inconclusive` row without; its own column sums are:

| | value |
|---|---:|
| judged batches (rows with facts) | 14 |
| accept | 14 |
| sampling_inconclusive | 1 (b010) |
| Σ facts | 3+3+0+0+11+5+0+2+1+3+4+0+2+3 fabrications over 110+110+55+55+220+165+55+105+110+110+110+55+110+110 = **37 / 1,480** |

"13 accept" is likewise §21.6's figure, not the table's, which shows fourteen `accept` rows.

## Corrected sentence

> **15/15 match** the file on disk (14 accept, 1 sampling_inconclusive, 0 reject). Sum of
> fabrications/facts over the 14 judged batches: 37/1,480 (0.0250, Wilson 95% [0.0182, 0.0343]);
> §21.6's 37/1,474 and "13 accept" are transcription errors, corrected in
> `cc_tasks/2026-08-30_bulk_extraction_v038_ERRATUM-01.md`.

## What is unaffected

The reconstruction itself — batch-by-batch verdicts from `corpus/staging/metrics/burn_*_aggregate.json`
via `sprt_decide`, compared with the state file on disk — matches 15/15 and stands. The defect
analysis, the merge writer, and the test evidence in that RESULT do not depend on the pooled sum.
