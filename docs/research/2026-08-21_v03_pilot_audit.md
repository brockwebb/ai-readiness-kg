# Phase 4 — Pilot audit, schema v0.3 (task 2026-08-21_v03_visibility_kernel)

Run: 2026-08-21 21:50–22:23 UTC, serial, `--profile kernel_v03 --only <doc>`, model `claude-opus-4-8` (pinned, Max OAuth; `ANTHROPIC_API_KEY` unset), prompt 0.3.0, schema 0.3, shard `events/batch-006.jsonl`, raw at `events/raw/kernel_v03/`. Audit data: `docs/research/2026-08-21_v03_pilot_audit.json` (`scripts/pilot_audit_v03.py`).

Pilot slot 4: the SME "Visibility Diagnostic" file was not in the inbox (Phase 0), so the task's named fallback — the digital.gov DAP guide — was used.

## Per document
| doc | clause | chars | nodes | edges | quar. | q-rate | concepts/1k tok | proposed | Claims | evidence_grade | PO from non-platform |
|---|---|---|---|---|---|---|---|---|---|---|---|
| google-dataset-structured-data | b | 34,516 | 74 | 96 | 6 | 0.034 | 2.55 (z=-0.341) | 5 | 9 | {'platform_official': 8, 'practitioner_assertion': 1} | 0 |
| w3c-dwbp-2017 | a | 177,270 | 153 | 231 | 1 | 0.003 | 1.51 (z=-0.422) | 5 | 13 | {'inference': 11, 'practitioner_assertion': 2} | 0 |
| aggarwal-2024-geo-generative-engine-optimization | c | 69,803 | 84 | 129 | 1 | 0.005 | 2.06 (z=-0.379) | 4 | 16 | {'peer_reviewed_experiment': 13, 'inference': 3} | 0 |
| digital-gov-dap-guide | d | 3,826 | 23 | 37 | 0 | 0.000 | 11.51 (z=0.361) | 4 | 6 | {'platform_official': 5, 'practitioner_assertion': 1} | 5 |
| cloudflare-ai-crawl-control | b | 3,501 | 25 | 41 | 0 | 0.000 | 12.57 (z=0.444) | 3 | 4 | {'practitioner_assertion': 1, 'platform_official': 3} | 0 |

Wall-clock / tokens (envelope usage): google 436 s / 106,180; DWBP 586 s / 219,851; GEO 471 s / 139,881; DAP 307 s / 194,218; Cloudflare 179 s / 56,497. **Cost: UNKNOWN** (control plane reports 5 unpriced calls; `day_cost_usd` is a lower bound, not the spend).

## Headline
- **STOP conditions:** none. Max per-doc quarantine 0.034 (< 0.15); `evidence_grade` missing on **0/48** Claims (< 10%). Also under the runner's stricter pre-registered 0.10 per-doc STOP.
- **Quarantine (pooled 0.0089, 8/899 items):** 7 = `unresolved endpoint id` (edge to a node the model never emitted), 1 = `grounding_span not found in source text` (GEO). No quarantine was caused by the new v0.3 enforcement (no missing/invalid grade, no enum violation).
- **Concept density:** pilot mean 6.04 /1k tokens vs v0.2 baseline mean 6.90 (SD 12.77); every pilot doc within the 3σ control limits (UCL 45.2). Long specs (DWBP 1.5, Google 2.5) sit low; short pages (DAP 11.5, Cloudflare 12.6) sit high — the same length effect the v0.2 corpus shows.
- **evidence_grade distribution (48 Claims):** platform_official 16, inference 14, peer_reviewed_experiment 13, practitioner_assertion 5. Coherent with source: GEO (clause c) → 13 peer_reviewed_experiment; Google/Cloudflare (clause b) → platform_official; DWBP (a standard, not a platform) → inference/practitioner_assertion, zero platform_official.
- **Grading-confusion signal:** 5/48 Claims graded `platform_official` from a non-clause-b source — all five from the DAP guide (federal, clause d). Reading them: the DAP guide is GSA documenting the behaviour of a platform GSA itself operates (the Digital Analytics Program), which fits DD-010's definition ("the operator's own documentation about its own behavior") even though the *inclusion clause* is federal. Recorded as a definitional edge case, not a model error: the signal conflates "platform-official" with "harvest clause b". Zero confusion on the cleaner cases (DWBP, GEO). Follow-on: tag Document with an `is_platform_operator` signal rather than inferring from clause.
- **proposed_relationships:** 21 names, 21 occurrences, every one grounded, **none repeated across documents** — `belongs_to_catalog`, `combines_with`, `complemented_by`, `consumed_by_user_agent`, `distinct_from`, `effect_varies_by_ranking_tier`, `enterprise_version_of`, `has_evidence_requirement`, `has_format`, `has_release_status`, `has_required_property`, `has_subdataset`, `implemented_via`, `mandates_use_of`, `most_effective_in_domain`, `provided_by_org_GSA`, `provides_benefit`, `related_product`, `renamed_from`, `serializable_as`, `uses`. **Schema patch rule (≥3 occurrences across ≥2 docs): no candidate → no v0.3.1.** Decision logged here; the names stay in `corpus/staging/proposed_relationships/` for operator batch review (§6). Observed themes worth watching in bulk: part-whole on datasets (`has_subdataset`, `belongs_to_catalog`), format/serialization (`has_format`, `serializable_as`), provenance of products (`renamed_from`, `enterprise_version_of`).
- **New v0.3 layers are being used** (5 docs, admitted events): Practice 58, Tool 10, Platform 7 nodes; edges `recommends` 58, `applies_to` 53, `supported_by` 14, `implemented_by` 7, `targets` 5, `consumes` 4, `supersedes` 0 (expected — it is a manifest-path edge, DD-012).

## Decision
Pilot passes the §9 gate under v0.3 as written. Proceed to Phase 5 bulk with no schema patch and no prompt change. Tests unchanged (117 passing).
