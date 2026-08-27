# Overnight burn 2026-08-26 → 27 — SUMMARY (driver exit)

Task: `cc_tasks/2026-08-26_overnight_burn.md`. Written 2026-08-27T08:45:00.078414+00:00 by scripts/overnight_burn.py.
CEILING (execute line carried an unfilled placeholder; interpreted as the standing declared band, no band change): **55,000,000** tokens; `spend.daily_tokens` untouched at 55M.

## Ledger totals per run (`python -m kg.spend status`)

| run | ceiling | committed | settled | outstanding | refusals | reconcile |
|---|---|---|---|---|---|---|
| pilot_instr_sem | 3,000,000 | 1,050,000 | 1,050,000 | 0 | 0 | OK |
| restoration_v2_s1 | 55,000,000 | 21,550,241 | 21,514,241 | 36,000 | 0 | OK |
| restoration_v2_s2 | 55,000,000 | 7,524,116 | 7,458,511 | 65,605 | 0 | OK |
| restv2test | 1,000,000 | 0 | 0 | 0 | 0 | OK |

Committed today (daily band 55,000,000): **30,124,357**

## Lane states

```json
{
 "driver_run1": {
  "note": "first launch aborted 02:56Z \u2014 lane1 parse ownership bug, fixed",
  "driver": {
   "state": "lanes_2_3_skipped",
   "ts": "2026-08-27T02:56:09.645636+00:00",
   "ceiling": 55000000,
   "wall_stop": "2026-08-27T08:45:00+00:00",
   "pid": 24838,
   "reason": "Lane 1 FAIL/STOP \u2014 pre-registered rule"
  },
  "lane1_pilot": {
   "state": "error",
   "ts": "2026-08-27T02:56:09.645250+00:00",
   "pilot_docs": [
    "data-readiness-for-ai-a-360-degree-survey",
    "aidrin-hiniduma-2024",
    "fcsm-23-02-a-framework-for-data-quality-case-studies"
   ],
   "detail": "extraction output missing 'document_id'"
  }
 },
 "driver": {
  "state": "lanes_2_3_skipped",
  "ts": "2026-08-27T03:26:50.987321+00:00",
  "ceiling": 55000000,
  "wall_stop": "2026-08-27T08:45:00+00:00",
  "pid": 25659,
  "reason": "Lane 1 FAIL/STOP \u2014 pre-registered rule"
 },
 "lane1_pilot": {
  "state": "FAIL",
  "ts": "2026-08-27T03:26:50.986943+00:00",
  "pilot_docs": [
   "data-readiness-for-ai-a-360-degree-survey",
   "aidrin-hiniduma-2024",
   "fcsm-23-02-a-framework-for-data-quality-case-studies"
  ],
  "doc": "fcsm-23-02-a-framework-for-data-quality-case-studies",
  "instruments": 0,
  "semantic_edges": 0,
  "reason": "zero items in both strata"
 },
 "lane3_triage": {
  "state": "skipped",
  "ts": "2026-08-27T03:26:50.987469+00:00",
  "reason": "Lane 3 depends on Lane 1 PASS (extraction under the corrected prompt)"
 },
 "lane4_repair": {
  "state": "error",
  "ts": "2026-08-27T08:44:59.442039+00:00",
  "stage": "1",
  "rc": 0,
  "detail": "Command '['/opt/anaconda3/bin/python3', 'scripts/restoration_v2.py', '--stage', '2', '--ceiling-tokens', '55000000', '--run-id', 'restoration_v2_s2']' timed out after 3898 seconds"
 }
}
```

Gate verdicts, counts, and artifacts: see the lane states above, `docs/research/2026-08-26_pilot_reextract_v034_verdict.md`, `corpus/staging/metrics/restoration_v2_summary.json`, `corpus/staging/metrics/batch_repair_summary.json`, and the per-lane shards (batch-013_reextract_v034 / batch-014_restoration_v2 / batch-015 / batch-016).
