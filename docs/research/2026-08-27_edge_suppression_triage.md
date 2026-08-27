# Edge-suppression mechanical triage (ADDENDUM-05 §3a) — zero spend

Cue list: `kg/extraction/edge_cues.yaml` sha256 `8f8216d12b13e9fd…` (version 2026-08-27.1). Window: ≤ 3 sentences and ≤ 800 chars. Candidates: `corpus/staging/metrics/edge_suppression_candidates.jsonl`.

### p1_proposed_v035b (n=28)

| doc | single_span | evidence_set | unlocatable |
|---|---|---|---|
| `data-readiness-for-ai-a-360-degree-survey` | 0 | 1 | 1 |
| `aidrin-hiniduma-2024` | 2 | 1 | 4 |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | 9 | 3 | 1 |
| `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` | 0 | 0 | 6 |
| `mitre-ai-maturity-model` | 0 | 0 | 0 |
| **pooled** | **11** | **5** | **12** |

### p2_live_kernel_era (n=145)

| doc | single_span | evidence_set | unlocatable |
|---|---|---|---|
| `data-readiness-for-ai-a-360-degree-survey` | 2 | 2 | 8 |
| `aidrin-hiniduma-2024` | 2 | 5 | 20 |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | 12 | 4 | 20 |
| `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` | 3 | 8 | 27 |
| `mitre-ai-maturity-model` | 17 | 11 | 4 |
| **pooled** | **36** | **30** | **79** |

**Pooled locatable (single_span + evidence_set): 82** (3b proceeds iff ≥ 20; single_span pooled = 47 would indicate model over-diversion under the current rule).
