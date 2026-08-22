# Phase 6 — Projection, gates, quality monitors (task 2026-08-21_v03_visibility_kernel)

Run: 2026-08-22 01:55–02:20 UTC. Thresholds frozen (`dixie_evidence.yaml: baseline_gate`); fails are findings.

## Projection
`build_projection.py` → `seldon-ai-readiness-kg`: **9,018 nodes / 12,224 rels / 134 Documents** (71 v1 + 63 kernel). New v0.3 labels project without script changes (labels come from `schema.yaml`): Practice 305, Tool 82, Platform 85; RECOMMENDS 336, APPLIES_TO 257, TARGETS 61, CONSUMES 59, SUPPORTED_BY 59, IMPLEMENTED_BY 32, SUPERSEDES 0 (manifest-path edge, DD-012). Skipped superseded extraction events 236 (the OECD overlay, as before); unknown edge types 0.

## Pre-registered gates — `docs/research/2026-08-21_v03_kernel_gate_report.md`
`run_baseline_gates.py --profiles v1,kernel_v03` (scoped by run profile — new flag; default `v1` reproduces the old report).

| check | Phase 0 baseline (v1) | v1 + kernel | Δ | kernel-v03 only | verdict (union) |
|---|---|---|---|---|---|
| min_verified_included | 71 | 134 | +63 | 63 (threshold is the v1 freeze count; scope artefact, not a failure of the kernel) | PASS |
| **grounding_zero_ungrounded** | 0 | **0** | 0 | 0 (6,935 kernel items re-verified against source) | **PASS — no STOP** |
| quarantine_rate | 0.0343 | 0.0237 | −0.0106 | **0.0109 (PASS)** | FAIL (finding; v1 legacy dominates) |
| edge_endpoint_validation | 747 | 1209 | +462 | 1209 (projection-wide check) | FAIL (finding) |
| orphan_rate | 0.098 | 0.0877 | −0.0103 | 0.0877 (projection-wide) | FAIL (finding) |
| projection_drift | 0 | 0 | 0 | 0 | PASS |
| empty_extraction_rate | 0.0141 | 0.0075 | −0.0066 | 0.0 | PASS |

Findings, not retuned:
- `edge_endpoint_validation` +462: every sampled violation is a `cites` edge to a Document id never manifested (e.g. `doc-omb-m-25-05`, `doc-44-usc-3563`, `hiniduma-2024-360-survey`) — the same class as the v1 747 and the 721-entry `refetch_candidates.jsonl`. The kernel cites into federal statute/OMB memos and the FAIR/GEO literature the same way v1 did. Closing them is the refetch lane (out of scope here; DD-012 harvester).
- `orphan_rate` improved 0.098 → 0.0877 as kernel docs connect previously-orphan Concepts (and vice-versa); still far above the statutory-corpus port value, as the v1 closeout predicted for a heterogeneous corpus.
- `quarantine_rate` improved overall and **passes on the kernel alone** — the v0.3 parser's new checks (evidence_grade, enums) caused zero quarantines; kernel quarantines are unresolved-endpoint edges and a handful of grounding misses, as in the pilot.

## Quality monitors (new) — `scripts/quality_monitors.py`, config `dixie_evidence.yaml: quality_monitors`
Prior art: Shewhart individuals chart (mean ± 3·SD over the baseline period). Baseline = v0.2 corpus (epoch v1, n=71): concepts/1k tok mean 6.899 SD 12.773 (UCL 45.22); quarantine_rate mean 0.0317 SD 0.0466 (UCL 0.1715); proposed_rate mean 0.0376 SD 0.0274 (UCL 0.1198). Persisted: `corpus/staging/metrics/control_limits.json`, `quality_monitors.json` (per-doc density, quarantine, evidence-grade distribution, proposed rate). Caveat recorded: density is heavy-tailed (short checklists at 80+/1k), so the SD-based UCL is wide; a moving-range or log-scale chart is the obvious refinement for the next run.

Kernel-v03 run against those limits: **no monitor fired** — grounding 0 failures; evidence_grade 568/568 Claims graded (platform_official 213, practitioner_assertion 193, measured_practitioner 81, inference 49, peer_reviewed_experiment 32), 0 missing; every doc inside the density/quarantine/proposed limits (max quarantine 0.1245 < UCL 0.1715 < declared stop 0.15).

**Positive control (mutation test)** — `--mutation-test --scratch <scratchpad>`: the event shards were copied to a scratch dir and one synthetic known-bad extraction seeded (Claim with an unmatchable grounding span and no `evidence_grade`; a build_metrics row with density 9999, quarantine 0.999, proposed 999). Result, run on both the v1 scope and the kernel scope: all five monitors fired **on the seeded doc** — grounding ✔, evidence_grade ✔, concept_density ✔, quarantine ✔, proposed_rate ✔ (`docs/research/2026-08-21_v03_monitor_mutation_test.json`). Live `events/` untouched (verified: only `batch-006.jsonl` and `raw/kernel_v03/` are new).

Tests: `tests/test_quality_monitors.py` (8 tests: metric derivation incl. shard fallback for empty extractions, control-limit math and refusal on a tiny baseline, each monitor's firing rule, the seed writer). Suite: **117 passed**.
