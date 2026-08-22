# Phase 0 — Preflight (task 2026-08-21_v03_visibility_kernel)

Run: 2026-08-21, Max OAuth only (`ANTHROPIC_API_KEY` unset, verified).

## Tests
- Baseline: **74 passed, 1 failed** — `tests/test_extraction_model_stub.py::test_extract_json_tolerates_fences`.
  Discrepancy vs task ("must pass at baseline"): the test asserted `ModelConfigError` for a
  no-JSON response, but the 2026-07-09 root-cause fix deliberately made that a per-document
  `ModelInvocationError` (documented in `_extract_json`'s docstring). Stale assertion; test
  updated to the documented behavior. No production code changed.
- After fix: **75 passed**.

## Baseline gates (comparison values for Phase 6)
`build_projection.py` and `run_baseline_gates.py` ran clean against the current log.

| check | value | threshold | verdict |
|---|---|---|---|
| min_verified_included | 71 | 71 | PASS |
| grounding_zero_ungrounded | 0 | 0 | PASS |
| quarantine_rate | 0.0343 | 0.0152 | FAIL (finding) |
| edge_endpoint_validation | 747 | 0 | FAIL (finding) |
| orphan_rate | 0.098 | 0.0034 | FAIL (finding) |
| projection_drift | 0 | 0 | PASS |
| empty_extraction_rate | 0.0141 | 0.1196 | PASS |

Matches the task's expected values (grounding 0, edge_endpoint_validation 747, 71 docs).
Projection node/rel counts: 71 Document; rels incl. MENTIONS 2332, HAS_COMPONENT 810, ASSERTS 883, CITES 756.

## controls.yaml (AUTH-3)
- Before: `611d5dda0834900ea77ca619f8d0cd4368efb471cd3914ac76a15378b5344684`
- Change applied: `extract: off → on`, `extract_daily_docs: 10 → 60`. `forage` stays `off`.
- After (task-duration): `1e3729b0720e433150ac5250db50cb1bf565069a510d4a36a8b1ae366b7b94a8`
- Byte-exact prior copy saved in scratchpad for restore in Phase 7.

## corpus/staging/inbox/
- `FCSM.20.04_A_Framework_for_Data_Quality.pdf` (1,111,516 B) — provenance backup, already in corpus
- `FCSM.23.02_DQ_Case_Studies.pdf` (781,887 B) — provenance backup, already in corpus
- `OECD_AI_Capability_Indicators.pdf` (2,223,074 B) — already in corpus (superseded 2026-08-14)
- **No "Visibility Diagnostic" file present.** Discrepancy vs task (which anticipated it as
  possible): pilot slot 4 falls to the digital.gov DAP guide per the task's stated fallback.
  `corpus/inbox/` (dixie inbox_dir) is empty.
