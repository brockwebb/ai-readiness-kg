# Overnight burn 2026-08-26 → 27 — SUMMARY (driver exit)

Task: `cc_tasks/2026-08-26_overnight_burn.md`. Written 2026-08-28T01:33:07.697715+00:00 by scripts/overnight_burn.py.
CEILING (execute line carried an unfilled placeholder; interpreted as the standing declared band, no band change): **55,000,000** tokens; `spend.daily_tokens` untouched at 55M.

## Ledger totals per run (`python -m kg.spend status`)

| run | ceiling | committed | settled | outstanding | refusals | reconcile |
|---|---|---|---|---|---|---|
| edge_suppression_judge | 2,000,000 | 1,323,023 | 1,323,023 | 0 | 0 | OK |
| pilot_chunked_v035 | 5,000,000 | 3,383,718 | 2,335,359 | 1,048,359 | 0 | OK |
| pilot_instr_sem | 3,000,000 | 1,050,000 | 1,050,000 | 0 | 0 | OK |
| pilot_v035 | 3,000,000 | 1,532,559 | 1,532,559 | 0 | 0 | OK |
| pilot_v035b_opus5 | 4,000,000 | 5,628,758 | 5,517,758 | 111,000 | 2 | OK |
| repair_resume | 55,000,000 | 0 | 0 | 0 | 0 | OK |
| restoration_v2_accept | 55,000,000 | 1,773,285 | 1,773,285 | 0 | 0 | OK |
| restoration_v2_resume | 55,000,000 | 24,495,724 | 24,495,724 | 0 | 1 | OK |
| restoration_v2_s1 | 55,000,000 | 21,550,241 | 21,514,241 | 36,000 | 0 | OK |
| restoration_v2_s2 | 55,000,000 | 7,524,116 | 7,458,511 | 65,605 | 0 | OK |
| restv2test | 1,000,000 | 0 | 0 | 0 | 0 | OK |

Committed today (daily band 55,000,000): **11,023,420**

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
  "state": "exited",
  "ts": "2026-08-27T17:30:42.753127+00:00",
  "ceiling": 55000000,
  "wall_stop": "2026-08-28T03:30:00+00:00",
  "pid": 70582,
  "reason": "Lane 1 FAIL/STOP \u2014 pre-registered rule",
  "lanes": [
   "1b"
  ],
  "lane1_pass": false,
  "lane1b_pass": false
 },
 "lane1_pilot": {
  "state": "FAIL",
  "ts": "2026-08-27T11:32:01.991746+00:00",
  "pilot_docs": [
   "data-readiness-for-ai-a-360-degree-survey",
   "aidrin-hiniduma-2024",
   "fcsm-23-02-a-framework-for-data-quality-case-studies"
  ],
  "doc": "fcsm-23-02-a-framework-for-data-quality-case-studies",
  "instruments": 1,
  "semantic_edges": 0,
  "reason": "precondition 1/3 docs with both strata",
  "span_lacks_name": 4,
  "emission": "single_pass"
 },
 "lane3_triage": {
  "state": "skipped",
  "ts": "2026-08-27T03:26:50.987469+00:00",
  "reason": "Lane 3 depends on Lane 1 PASS (extraction under the corrected prompt)"
 },
 "lane4_repair": {
  "state": "stopped",
  "ts": "2026-08-28T01:33:05.981441+00:00",
  "stage": "2",
  "rc": 0,
  "detail": "Command '['/opt/anaconda3/bin/python3', 'scripts/restoration_v2.py', '--stage', '2', '--ceiling-tokens', '55000000', '--run-id', 'restoration_v2_s2']' timed out after 3898 seconds",
  "mode": "resume",
  "until": "2026-08-28T00:05:00+00:00",
  "seconds": 18720,
  "accepted": 4021,
  "rate": 0.9,
  "n_facts": 130,
  "reason": "wall clock / STOP file"
 },
 "lane1b_pilot": {
  "state": "STOP",
  "ts": "2026-08-27T17:30:42.752202+00:00",
  "docs": [
   "data-readiness-for-ai-a-360-degree-survey",
   "aidrin-hiniduma-2024",
   "fcsm-23-02-a-framework-for-data-quality-case-studies",
   "from-accuracy-to-readiness-metrics-and-benchmarks-for-human",
   "mitre-ai-maturity-model"
  ],
  "semantic_doc_prior_counts": {
   "from-accuracy-to-readiness-metrics-and-benchmarks-for-human": 38,
   "mitre-ai-maturity-model": 32
  },
  "doc": "from-accuracy-to-readiness-metrics-and-benchmarks-for-human",
  "instruments": 1,
  "semantic_edges": 0,
  "span_lacks_name": 1,
  "emission": "per_layer",
  "output_tokens": 119626,
  "reason": "spend guard: spend guard refused dispatch (over_ceiling, scope=run): committed 3,907,767 + estimate 257,708 vs ceiling 4,000,000 [run pilot_v035b_opus5]"
 }
}
```

Gate verdicts, counts, and artifacts: see the lane states above, `docs/research/2026-08-26_pilot_reextract_v034_verdict.md`, `corpus/staging/metrics/restoration_v2_summary.json`, `corpus/staging/metrics/batch_repair_summary.json`, and the per-lane shards (batch-013_reextract_v034 / batch-014_restoration_v2 / batch-015 / batch-016).
