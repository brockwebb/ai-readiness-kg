# RESULT — AIRKG schema v0.3 + machine-visibility kernel corpus

**Task:** `cc_tasks/2026-08-21_v03_visibility_kernel.md` (immutable; not edited)
**Executed:** 2026-08-21 21:05 → 2026-08-22 02:25 UTC. Max OAuth only; `ANTHROPIC_API_KEY` unset throughout (runner + harvester guard on it).
**Execution model:** orchestrator + two parallel subagents (Phase 1 schema, Phase 2 harvest); Phases 3–7 serial in the orchestrator; bulk via the 2-worker fleet.
**Left uncommitted** per burn convention — operator commits. The dixie package (`~/GitHub/dixie`) also carries two uncommitted one-line fixes (below).

## Phase status
| phase | status | sub-RESULT |
|---|---|---|
| 0 Preflight | done | `docs/research/2026-08-21_v03_phase0_preflight.md` |
| 1 Schema v0.3 | done (109 tests) | `…_v03_phase1_schema.md` |
| 2 Kernel harvest | done — 63 fetched / 1 failed / 4 excluded / 0 oversize | `…_v03_phase2_harvest.md`, rule at `…_kernel_inclusion_rule.md` |
| 3 Manifest adds | done — **63 added**, 0 skipped-at-gate, 5 deferred | `…_v03_phase3_manifest.md` (+ `_summary.json`) |
| 4 Pilot | done — passed, no STOP, no schema patch | `…_v03_pilot_audit.md` (+ `.json`) |
| 5 Bulk | done — **63/63 extracted**, 0 manifested-not-extracted | `…_v03_phase5_bulk.md` |
| 6 Gates + monitors | done — grounding 0, monitors verified by mutation test | `…_v03_phase6_gates_monitors.md`, gate report `…_v03_kernel_gate_report.md` |
| 7 Docs closeout | done — README, DD-009..012, schema changelog, controls restored | this file |

## Headline numbers
- **Tests:** 74 passed + 1 stale failure at baseline → 75 (after fixing the stale assertion) → **117 passed** final.
- **Schema / template stamped in events:** `schema_version: "0.3"`, `prompt_version: 0.3.0`, `model_id: claude-opus-4-8`, `corpus_epoch: kernel-v03` on every kernel assertion (`events/batch-006.jsonl`, 9,652 lines; raw responses ×63 in `events/raw/kernel_v03/`).
- **Candidate register:** 68 kernel lines appended (159 total; lines 1–91 byte-identical to HEAD). `refetch_candidates.jsonl` untouched (721).
- **Manifest:** 63 kernel `manifest_add` events (by clause a=21, b=25, c=8, d=9; 5 with `extent_note` per AUTH-4); `corpus/manifest.json` 97 → 162 entries; dixie epoch `kernel-v03` declared with 63 members.
- **Pilot:** 5 docs, max quarantine 0.034, `evidence_grade` 48/48, 21 proposed-relationship names each occurring once → no v0.3.1 patch.
- **Bulk:** rate doc 158 s / 111,409 tok; projection 5.84 h serial → fleet 2 (operator ceiling) 3h16m actual; no cut point needed; one doc failed once and succeeded on verbatim retry. Extraction wall-clock ≈ 4h01m (AUTH-5 window 5 h).
- **Tokens:** 6,864,272 across 64 calls (63 + the retried one's first attempt had no usage). **Cost: UNKNOWN** — control plane reports every call unpriced; the CLI envelope's own `cost_usd` sums to $86.43 and is recorded as a lower-bound estimate, not the spend. Declared budget band never tripped (55M tokens left at start).
- **Gates (v1 + kernel; Phase 0 baseline → final):** min_verified 71→134 PASS · **grounding 0→0 PASS** · quarantine 0.0343→0.0237 FAIL-finding (kernel alone 0.0109 PASS) · edge_endpoint 747→1209 FAIL-finding (`cites` to unmanifested docs, same class) · orphan 0.098→0.0877 FAIL-finding · drift 0→0 PASS · empty 0.0141→0.0075 PASS.
- **Monitors:** 5 monitors with Shewhart limits over the v0.2 corpus (n=71); kernel run fires none; mutation test fires all five on the seeded bad on both scopes (`docs/research/2026-08-21_v03_monitor_mutation_test.json`).
- **controls.yaml:** before `611d5dda0834900ea77ca619f8d0cd4368efb471cd3914ac76a15378b5344684` → during task `1e3729b0…94a8` (extract on, 60/day) → after restore **`611d5dda…3684` (byte-identical to HEAD, verified with git diff)**.

## Discrepancies between the task's stated numbers/premises and live (reported, not reconciled)
| task said | live |
|---|---|
| Phase 0: tests "must pass at baseline" | 74/75 — `test_extract_json_tolerates_fences` asserted `ModelConfigError` for a no-JSON response; the 2026-07-09 fix made that `ModelInvocationError` by documented design. Stale test fixed; no production code changed. |
| "Visibility Diagnostic" file may be in inbox | Not present. Pilot slot 4 → digital.gov DAP guide (task's stated fallback). Registered `excluded_by_rule`. |
| Expected ≈45–55 candidates | 68 registered / 63 fetched (schema.org type pages count individually per the task's own instruction). |
| Named pages: JSON-LD 1.1 primer; SDMX primer; Bing Webmaster APIs page; Cloudflare Content Signals Policy; three crawler-doc URLs | No steward JSON-LD primer exists (Rec taken at §1,2,3,8); SDMX has an overview not a "primer"; Bing API page 404 (Microsoft Learn used); Content Signals lives at contentsignals.org; three crawler URLs redirect. All recorded per entry in `scripts/kernel_list.yaml` / Phase 2 §6. |
| Akamai Bot Manager bot-reports docs | SAML login-gated — `fetch_failed`, 4 URLs tried. |
| Pilot STOP 0.15 / bulk flag 0.15 | Runner's pre-registered per-doc STOP is 0.10. Pilot never reached 0.10. Bulk used `BURN_QUARANTINE_STOP_MODE=systemic` so an isolated 0.10–0.15 breach is a finding (two docs: 0.1245, 0.1158), matching the task's "flagged, not re-run". None exceeded 0.15. |
| Phase 5 "remaining manifested kernel docs" via "the standard runner" | The runner was hard-wired to epoch v1 / batch-004. Made profile-driven (`scripts/run_profiles.yaml`, `--profile`); v1 default verified unchanged by dry-run. |
| Phase 6 gate expectation "grounding 0" | Met. Note `min_verified_included` threshold (71) is the v1 freeze count; on a kernel-only scope it reads 63 — scope artefact. |
| "Any doc whose quarantine rate exceeds 0.15 is flagged" | Zero. |
| Phase 3 identity check: "nothing already manifested is re-added" | Held; but the Phase 2 register marked the three already-held Census standards `excluded`, which dixie's register import would have read as a corpus exclusion. Lines updated to `manifested/already_manifested` before the sweep (repo convention); recorded in Phase 3. |
| — (not in task) | `kg.manifest verify` reports 4 pre-existing `hash_mismatch` entries (fcsm-19-01, two Acts, §515) from v1 re-acquisitions never re-manifested in `kg.manifest`. Pre-existing at HEAD; untouched. |
| — (not in task) | Two latent dixie bugs surfaced and fixed at source (`~/GitHub/dixie`, uncommitted, 58/58 tests): sweep crash on sha-less `integrity_checked` events (written by the 2026-08-14 Acts acceptance); screening re-import regressing a `verified` stage to `acquired`. |
| — (not in task) | `seldon_events.jsonl` gained one `artifact_created` line (Seldon hook during Phase 1). |

## Files
**New:** `scripts/{run_profiles.yaml, harvest_kernel.py, kernel_list.yaml, manifest_kernel.py, pilot_audit_v03.py, quality_monitors.py}` · `tests/{test_schema_append_only.py, test_quality_monitors.py}` · `events/batch-006.jsonl`, `events/raw/kernel_v03/` · `corpus/kernel/` (63 files, gitignored) · `docs/research/2026-08-21_*` (10 files) · `CLAUDE.md`.
**Modified:** `kg/schema.yaml` (v0.3), `kg/extraction/{parser.py, schema_loader.py, output_schema.json, prompt_template.md}`, `kg/manifest.py`, `scripts/{run_bulk_extraction.py, run_baseline_gates.py}`, `dixie_evidence.yaml` (kernel document_dir; `quality_monitors` section), `.gitignore`, `README.md`, `docs/{schema_v0.1.md, design_decisions.md}` (DD-009..012), `corpus/{manifest.json, evidence/decisions.jsonl, staging/candidate_register.jsonl}`, tests ×5.

## Out of scope, left for follow-on
Concept dedup / Construct promotion / definition-conflict adjudication on the merged graph; the `cites`-endpoint refetch lane (now 1,209 dangling); the DD-012 currency harvester; `is_platform_operator` document signal to sharpen the grading-confusion metric; MR-based control limits for density.
