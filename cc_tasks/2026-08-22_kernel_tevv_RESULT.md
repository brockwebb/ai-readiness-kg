# RESULT — Kernel TEVV: stability, faithfulness, evidence-grade calibration

**Task:** `cc_tasks/2026-08-22_kernel_tevv.md` (immutable; not edited) · **Seldon task:** `de7ae80b`
**Executed:** 2026-08-22 12:40 → 14:40 UTC. Max OAuth only; `ANTHROPIC_API_KEY` unset (runner, retest and judge all guard on it).
**Execution model:** orchestrator serial for Phases 0, 1, 4, 5, 6; Phase 2 (retest) and Phase 3 (judge) ran as two concurrent detached streams (= the operator's 2-stream ceiling).
**Sub-RESULTs:** `docs/research/2026-08-22_tevv_{phase0_preflight, sample, stability, faithfulness, grade_calibration, platform_operator_decisions, retest_log, gate_report, monitor_mutation_test.json}`.

## Headline
**The extraction process is reproducible; the extractions are not yet valid by the pre-registered bars.** Six of seven TEVV gates fail. Each failure has a named cause and a follow-on; no threshold was touched.

## Phase status
| phase | status |
|---|---|
| 0 Preflight | done — 117 → 125 tests; schema v0.3.1 (`Document.is_platform_operator`); 134 annotations in `events/batch-007.jsonl` (30 true / 104 false) |
| 1 Sample | done — seed `20260822`; 8 stability docs; 200 faithfulness items in 17 strata (all ≥ 10); 40-item human subset written, unlabelled |
| 2 Stability retest | done — 8/8 re-extracted under original model/prompt/schema into `events/batch-008_tevv_retest.jsonl` (1,024 events, `purpose: tevv_retest`) |
| 3 Faithfulness | done — 200/200 judged, judge 1.0.0, status `uncalibrated_pending_human` |
| 4 Grade calibration | done — no phase STOP (platform_official 0.831 ≥ 0.70) |
| 5 Gates + monitors | done — realized values appended to `tevv_gates`; gate evaluation in `run_baseline_gates.py`; per-type stability monitor added and mutation-verified |
| 6 Close | done — controls restored; DD-013/DD-014; 6 Seldon results registered; grounding 0 after rebuild; **136 tests**; committed + pushed |

## Sample
- **Stability (8):** v1 — `census-…-standard-f2-prov` (federal), `ai-data-readiness-checklist-digital-government-hub` (industry), `undp-…-aira` (intergovernmental), `beyond-model-readiness-…` (academic); kernel-v03 — `lighthouse-docs-overview` (industry), `dcat-us-3-dataset-schema` (standard), `jacobsen-2020-fair-principles-interpretations` (academic), `gsa-site-scanning-engine-readme` (federal). Excluded: the two 0.10–0.15 quarantine docs and 9 docs > 120K chars (listed in the sample file).
- **Faithfulness (200):** Concept 20, edge:document_structural 20, edge:semantic 20, and 10 each for Definition, Framework, Instrument, Measure, Standard, Practice, Tool, Platform, and Claim × {ungraded, platform_official, practitioner_assertion, measured_practitioner, inference, peer_reviewed_experiment}.

## Rate
Retest first doc alone: 31,884 chars → **381 s, 98,718 tokens**; 8 docs ≈ 42 min, 834,313 tokens. Judge ≈ 7–27 s/item.

## Stability (κ / positive agreement / span Jaccard)
| | κ | positive agreement (Dice) |
|---|---|---|
| all items pooled | **−0.590** | 0.409 |
| nodes pooled | −0.520 | 0.479 |
| edges pooled | −0.639 | 0.358 |
| mean span Jaccard | **0.285** | — |

Per type (κ / PA): Measure −0.11 / 0.81 · Platform 0.00 / 0.67 · Tool −0.36 / 0.63 · Concept −0.47 / 0.52 · Standard −0.30 / 0.62 · Definition −0.43 / 0.48 · Framework −0.47 / 0.48 · Claim −0.72 / 0.28 · Instrument −0.75 / 0.22 · Practice −0.79 / 0.16. Per-doc tables in the stability sub-RESULT.
Reading: κ is negative by the **kappa paradox** (no both-absent cell in a union universe; Cicchetti & Feinstein 1990) — reported as pre-registered, with positive specific agreement beside it. The paradox-free number is still low: under exact normalized-text identity fewer than half the items recur; naming variance (not content variance) is a large share, which is why concept dedup is already on the critical path.

## Faithfulness (strict entailment by the grounding span alone) — `uncalibrated_pending_human`
**Pooled 0.535**; stratum range 0.00 (Instrument) – 0.90 (Claim:platform_official, edge:document_structural). Of 93 rejections: **65 = span grounds the item's name but not its attributes** (owner/year/steward/version/response_type/description filled from elsewhere or from world knowledge), **17 = truncated mid-sentence spans**, 11 other. Finding: *"no grounding span, no write" certifies provenance of location, not entailment of content.*

## Grade calibration (568 kernel Claims)
| grade | TP | FP | FN | TN | precision | recall |
|---|---|---|---|---|---|---|
| platform_official vs is_platform_operator | 177 | 36 | 57 | 298 | **0.831** | 0.756 |
| peer_reviewed_experiment vs source_type=academic | 32 | 0 | 109 | 427 | **1.000** | 0.227 |

29 of the 36 platform_official FPs are standards stewards documenting their own spec (SDMX 12, W3C Data Cube 10, Census API 7): official, not a platform. Phase STOP (< 0.70) not triggered; gate written and failed.

## Gate table — pre-registered vs realized (`docs/research/2026-08-22_tevv_gate_report.md`)
| check | threshold | realized | verdict |
|---|---|---|---|
| stability_kappa_pooled | ≥ 0.61 | −0.590 | FAIL |
| stability_kappa_per_type_min | ≥ 0.61 | −0.789 | FAIL |
| stability_jaccard_pooled | ≥ 0.70 | 0.285 | FAIL |
| faithfulness_precision_pooled | ≥ 0.90 | 0.535 | FAIL |
| faithfulness_precision_stratum_min | ≥ 0.85 | 0.000 | FAIL |
| grade_platform_official_precision | ≥ 0.90 | 0.831 | FAIL |
| grade_peer_reviewed_precision | ≥ 0.90 | 1.000 | PASS |

Graph gates unchanged from 2026-08-21 (grounding **0**, drift 0, 134 docs) — the retest shard is invisible to replay/projection by construction (`skipped_non_graph_purpose` 0 because `replay()` never yields it; the projection filter is the second guard).

## Monitors
`stability_per_type` added (`scripts/quality_monitors.py`, floors in `dixie_evidence.yaml: quality_monitors`). Mutation test on the kernel scope: all **six** monitors fire on the seeded bad (`docs/research/2026-08-22_tevv_monitor_mutation_test.json`). Live run: only `stability_per_type` fires (all 10 types), as the data says.

## Tokens / cost
Retest 834,313 + judge 7,160,002 = **7,994,315 tokens**. **Cost UNKNOWN** — every call unpriced by the control plane; CLI envelope estimates (retest ≈ n/a, judge ≈ $40.00) are lower bounds, not the spend.

## controls.yaml
before `611d5dda…3684` → task `2e259690…148f` (extract on, 20/day) → after **`611d5dda…3684`** (byte-identical to HEAD, verified).

## Standing decisions (judgment calls, logged here)
1. **Faithfulness strata:** literal per-edge-type strata (≈30 × floor 10) cannot fit 200, and proportional-with-merge collapsed every Claim grade into `other`; edges were grouped into two families (document-structural / semantic) so the per-grade strata the gate depends on survive.
2. **κ universe = union of runs** (pre-registered identity has no negative class); positive specific agreement reported beside it as the kappa-paradox remedy; registered in Seldon as a third stability result. Recommended: re-pre-register stability on PA (or a fixed candidate universe) in a follow-on.
3. **v1 retests pinned to prompt 0.2.0 / schema 0.2** from git `69ebfdc` (`scripts/tevv_pins/`, sha-verified on every run), and their events stamped `schema_version 0.2` — "identical to the original" taken literally.
4. **`preprint` truth class:** the schema enum has no `preprint`; peer-reviewed precision uses `academic` only (arXiv papers are manifested `academic`).
5. **GSA → true** per the task; the v1 GSA AI-CoE guide and Pearson/AWS resolve true under the literal org-level rule and are flagged in the decision table.
6. **Judge strictness:** v1.0.0 requires every displayed attribute to be supported by the span; this is the pre-registered definition. A lenient "core supported" mode was not added (it would be a different claim).
7. **Exact-version schema test** (`== "0.3"`) relaxed to the 0.3 line; patch releases are append-only by construction and machine-checked.
8. **Judge crash at item 59** (CLI auto-update at 13:17 UTC made `claude` unresolvable for seconds; both passes died): relaunched, resumed by item id; no duplicate judgments.

## Discrepancies vs the task (reported, not reconciled)
| task said | live |
|---|---|
| "Emit … in a new shard `events/batch-007.jsonl`" / retest in `events/batch-008_tevv_retest.jsonl` | Done; `eventlog` gained tagged-shard support (`append(tag=)`, `replay(tag=)`) because the untagged regex would otherwise have silently ignored the named file. |
| Seldon registration "for κ pooled, Jaccard pooled, faithfulness pooled, grade precisions" | Registered 6 (adds positive agreement). `--script-path` links show "no" — script artifacts are not registered in this project's Seldon graph; results stand alone (`seldon result list`). |
| `source_type in {academic, preprint}` | No `preprint` in the enum (see decision 4). |
| Phase 5 "if stability κ for any node type < 0.61, add a per-type monitor" | All ten types; one monitor with per-type output, mutation-verified. |

## Follow-ons (recommended, separate tasks)
1. Extraction prompt v0.3.1: attributes null unless span-covered (or per-attribute spans); sentence-complete spans enforced mechanically in the parser beside the string match.
2. `platform_official` definition tightened to machine-consumer operators, or a `standard_official` grade (append-only).
3. Re-pre-register stability on positive agreement / a canonicalized identity after concept dedup.
4. Operator fills `tevv_human_subset.jsonl` (40 items) → judge–human κ → faithfulness status re-stamped.

## Files
**New:** `scripts/{annotate_platform_operator.py, platform_operators.yaml, tevv_retest.py, tevv_judge.py, tevv_stability.py, tevv_grade_calibration.py, tevv_pins/}`, `kg/extraction/judge_template.md`, `events/batch-007.jsonl`, `events/batch-008_tevv_retest.jsonl`, `events/raw/{tevv_retest, tevv_judge}/`, `corpus/staging/metrics/tevv_*`, `tests/{test_build_projection_filters, test_tevv_stability, test_tevv_gates}.py`, `docs/research/2026-08-22_tevv_*`.
**Modified:** `kg/{eventlog.py, schema.yaml}`, `scripts/{build_projection.py, run_baseline_gates.py, quality_monitors.py}`, `dixie_evidence.yaml` (tevv_gates + realized; stability monitor floors), `docs/{schema_v0.1.md, design_decisions.md}`, tests ×3.
