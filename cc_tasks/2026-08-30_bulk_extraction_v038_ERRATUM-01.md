# ERRATUM-01 to `cc_tasks/2026-08-30_bulk_extraction_v038_RESULT.md` — §21.6 pooled-F denominator and accept count

**Date:** 2026-09-02
**Issued by:** `cc_tasks/2026-09-02_post_burn_reconciliation.md` (finding F1)
**The RESULT is immutable and is not edited. This file corrects it.**

## What §21.6 says (wrong)

> **Full burn, fourteen judged batches.** 37 fabrications in 1,474 facts = **0.0251, Wilson 95%
> [0.0183, 0.0344]**, against the pre-registered upper-bound gate of 0.10. 13 accept, 1
> `sampling_inconclusive` (b010, unsatisfiable minimum-n, §20.3), 0 rejects, 0 quarantines.

Three values in that passage are transcription errors: the fact denominator (1,474), the accept
count (13), and the interval that follows from the wrong denominator. The fabrication count (37),
the gate verdict, and the b010 disposition are correct.

## Measured values and derivation

Source: `state/bulk_v038_burn.json` (read only), `batches[*].facts` and `batches[*].fabrications`,
summed batch by batch. The same table appears in `cc_tasks/2026-09-02_deck_numbers_post_burn_RESULT.md`
§2 and in `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md` §2.4 (reconstructed
from the persisted judge aggregates, 15/15 match).

| batch | outcome | facts | fabrications |
|---|---|---:|---:|
| b001 | accept | 110 | 3 |
| b002 | accept | 110 | 3 |
| b003 | accept | 55 | 0 |
| b004 | accept | 55 | 0 |
| b005 | accept | 220 | 11 |
| b006 | accept | 165 | 5 |
| b007 | accept | 55 | 0 |
| b008 | accept | 105 | 2 |
| b009 | accept | 110 | 1 |
| b010 | sampling_inconclusive | — | — |
| b011 | accept | 110 | 3 |
| b012 | accept | 110 | 4 |
| b013 | accept | 55 | 0 |
| b014 | accept | 110 | 2 |
| b015 | accept | 110 | 3 |
| **sum** | **14 accept, 1 sampling_inconclusive** | **1,480** | **37** |

Fifteen batches were walked; fourteen were judged (b010 never reached the judge: 33 admitted
items < 55-fact minimum, §20.3). All fourteen judged batches were accepted. §21.6's "13 accept"
undercounts by one and its 1,474 undercounts by 6 facts; the tome batches b005 (220) and b008
(105) are in §21.5's own table with those values, so the error is in the §21.6 sum, not the record.

Wilson 95% interval, recomputed here (z = 1.959964), not copied:

```
python3 - <<'PY'
import math
k,n,z=37,1480,1.959964; p=k/n
d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print(round(p,4), round(c-h,4), round(c+h,4))
PY
# 0.025 0.0182 0.0343
```

For the record, §21.6's interval [0.0183, 0.0344] is the correct Wilson interval for 37/1,474;
it inherited the wrong denominator, it was not miscomputed.

## Corrected sentence

> **Full burn, fifteen batches, fourteen judged.** 37 fabrications in 1,480 facts = **0.0250,
> Wilson 95% [0.0182, 0.0343]**, against the pre-registered upper-bound gate of 0.10. 14 accept,
> 1 `sampling_inconclusive` (b010, unsatisfiable minimum-n, §20.3), 0 rejects, 0 quarantines.

## Propagation

The wrong values were copied once, into `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_RESULT.md`
§2.4 — see `cc_tasks/2026-09-02_spend_guard_exit1_and_state_merge_ERRATUM-01.md`. The deck task
(`cc_tasks/2026-09-02_deck_numbers_post_burn_RESULT.md` §3 item 1) recomputed independently and
reported the disagreement; slide 15 already carries the measured values. The measured values are
registered as Seldon Result artifacts by the issuing task; any future document resolves to those.
