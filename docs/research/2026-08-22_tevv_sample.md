# TEVV sample (task 2026-08-22_kernel_tevv, Phase 1)

Seed: `20260822` (`random.Random(SEED)`, strata shuffled then one seeded choice per stratum, epochs in order v1, kernel-v03).

## Stability set (8 docs)

| epoch | source_type stratum | doc_id | chars (≈4×est. tokens) |
|---|---|---|---|
| v1 | federal | `census-bureau-statistical-quality-standards-standard-f2-prov` | 31,884 |
| v1 | industry | `ai-data-readiness-checklist-digital-government-hub` | 1,560 |
| v1 | intergovernmental | `undp-artificial-intelligence-readiness-assessment-aira` | 17,544 |
| v1 | academic | `beyond-model-readiness-institutional-readiness-for-ai-deploy` | 45,028 |
| kernel-v03 | industry | `lighthouse-docs-overview` | 9,624 |
| kernel-v03 | standard | `dcat-us-3-dataset-schema` | 86,664 |
| kernel-v03 | academic | `jacobsen-2020-fair-principles-interpretations` | 65,888 |
| kernel-v03 | federal | `gsa-site-scanning-engine-readme` | 7,364 |

Exclusions: two 0.10–0.15 quarantine docs (`anthropic-crawler-support-article`, `chen-2025-geo-how-to-dominate-ai-search`); 18 docs > 120K chars (cost control): `ai-real-toolkit-ai-readiness-assessment-guide`, `ai-watch-revisiting-technology-readiness-levels-for-relevant`, `arm-ai-readiness-index`, `building-an-ai-ready-public-workforce`, `data-readiness-for-ai-a-360-degree-survey`, `executive-order-14110-safe-secure-and-trustworthy-developmen`, `fcsm-19-01-transparent-reporting-for-integrated-data-quality`, `fcsm-20-04-a-framework-for-data-quality`, `fcsm-23-02-a-framework-for-data-quality-case-studies`, `from-school-ai-readiness-to-student-ai-literacy`, `gsa-ai-guide-for-government-ai-capability-maturity-model-ai`, `introducing-the-oecd-ai-capability-indicators`, `nist-ai-rmf-playbook`, `nist-generative-ai-profile-ai-600-1`, `openapi-specification-core`, `technology-readiness-levels-for-machine-learning-systems-mlt`, `w3c-dcat-3`, `w3c-dwbp-2017`.
Eligible pool: 114 of 134. Strata available — v1: ['academic', 'federal', 'industry', 'intergovernmental', 'standard']; kernel-v03: ['academic', 'federal', 'industry', 'standard']. Four strata are drawn per epoch from those available (seeded shuffle of strata), so `practitioner` (0 docs) and any epoch with fewer than four strata is filled from the pool — none needed.

## Faithfulness set (200 items)

Population: 21,173 admitted, grounded, live nodes+edges across 134 docs (superseded extractions excluded). Strata: node type, Claims split by `evidence_grade` (v1 Claims = `Claim:ungraded`); edges in two families — `edge:document_structural` (mentions/defines/asserts/about/recommends/cites, i.e. Document→item) and `edge:semantic` (all other edge types). Proportional allocation with a floor of 10 per stratum (rescaled to 200 by trimming the largest strata); strata with population < 10 merged into `other` (none). Seeded `random.sample` within each stratum (pool sorted by event_id).

**Standing decision:** a literal per-edge-type stratification (≈30 edge types × floor 10) cannot fit 200 items, and proportional-with-merge collapsed every Claim grade into `other` — which would defeat the per-stratum faithfulness threshold the task pre-registers. Two edge families keep the grade strata intact.

| stratum | population | sampled |
|---|---|---|
| Claim:inference | 49 | 10 |
| Claim:measured_practitioner | 81 | 10 |
| Claim:peer_reviewed_experiment | 32 | 10 |
| Claim:platform_official | 213 | 10 |
| Claim:practitioner_assertion | 193 | 10 |
| Claim:ungraded | 930 | 10 |
| Concept | 4,707 | 20 |
| Definition | 906 | 10 |
| Framework | 255 | 10 |
| Instrument | 160 | 10 |
| Measure | 528 | 10 |
| Platform | 98 | 10 |
| Practice | 336 | 10 |
| Standard | 430 | 10 |
| Tool | 100 | 10 |
| edge:document_structural | 9,261 | 20 |
| edge:semantic | 2,894 | 20 |

File: `corpus/staging/metrics/tevv_faithfulness_sample.jsonl`. Human calibration subset: 40 of the 200 (same seed) → `corpus/staging/metrics/tevv_human_subset.jsonl` with `human_label: null` — non-blocking; judge results carry status `uncalibrated_pending_human` until filled.
