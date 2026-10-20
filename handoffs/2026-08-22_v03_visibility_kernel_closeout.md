# Handoff — 2026-08-22 — schema v0.3 + machine-visibility kernel landed

**Session:** 2026-08-21 21:05 → 2026-08-22 ~02:40 UTC, Claude Code (Fable 5) as orchestrator, two parallel subagents (schema, harvest).
**Commits pushed:** `ai-readiness-kg@10e3d07` (110 files), `dixie@07a4359` (2 bug fixes). Working trees clean.
**Authoritative record:** `cc_tasks/2026-08-21_v03_visibility_kernel_RESULT.md` + sub-RESULTs `docs/research/2026-08-21_v03_*`. This handoff is the 2-minute version.

## Where the repo stands now

- **Graph = 134 documents, two epochs.** `v1` (71, schema v0.2, frozen) + `kernel-v03` (63, schema v0.3). Neo4j `seldon-ai-readiness-kg`: 9,018 nodes / 12,224 rels; new labels Practice 305, Tool 82, Platform 85.
- **Schema v0.3** is live and append-only-verified (`tests/test_schema_append_only.py`). `Claim.evidence_grade` required from v0.3; 568/568 kernel Claims graded. v1 Claims carry no grade by design (DD-010) — not a quarantine condition.
- **Gates** (`docs/research/2026-08-21_v03_kernel_gate_report.md`): grounding 0 · drift 0 · kernel-alone quarantine 0.0109 PASS · union quarantine 0.0237 / orphan 0.0877 / edge_endpoint **1209** are recorded findings, not retuned.
- **Monitors** (`scripts/quality_monitors.py`, config in `dixie_evidence.yaml: quality_monitors`): Shewhart limits from the v0.2 corpus; all five verified by mutation test. Run `--profiles kernel_v03` after any new extraction.
- **Runner/gates are profile-driven.** `scripts/run_profiles.yaml`: `v1` (default, unchanged behavior) and `kernel_v03`. A new epoch = a new profile block, not a code edit.
- **`controls.yaml`** restored to pre-task state (`extract: off`, 10/day). Re-widen per task, restore on exit — AUTH-3 pattern.
- **Tests:** 117 passing (`python -m pytest tests/ -q`).
- **Convention change:** commit and push at the end of every task/burn, shards and raw dirs included. CLAUDE.md line 71. No "operator commits" exception.

## What to read first next session
1. `CLAUDE.md` (new this session — invariants, commands, profiles).
2. `cc_tasks/2026-08-21_v03_visibility_kernel_RESULT.md` — especially the discrepancy table.
3. `docs/research/2026-08-21_v03_pilot_audit.md` — the evidence-grade behavior and the 21 proposed-relationship names.

## Open items (none blocking)

- **4 pre-existing `kg.manifest verify` hash mismatches** (fcsm-19-01, the two Acts, §515): v1 re-acquisitions were ledgered in dixie but never re-manifested in `kg.manifest`. Needs a supersession `manifest_add` per doc (same path OECD took in batch-005). Small, cheap, untouched here.
- **1,209 dangling `cites` endpoints** (was 747). Same class as `corpus/staging/refetch_candidates.jsonl` (721). The refetch lane is the fix; DD-012's harvester is the durable one.
- **24 kernel docs have `as_of: null`** with `as_of_source` explaining why. DD-012 says never fabricate; a currency harvest should try page-level dates again.
- **Akamai Bot Manager docs** — SAML-gated, `fetch_failed`. Needs an operator-side capture or drop.
- **Grading-confusion metric conflates "platform-official" with harvest clause b.** The DAP guide (federal, GSA-operated platform) shows why. Proposed: an `is_platform_operator` document signal. Not started.
- **Density control limit is wide** (SD-based, heavy-tailed). Moving-range or log-scale chart is the standard refinement.
- **Two docs between 0.10 and 0.15 quarantine** (`chen-2025-geo…` 0.1245, `anthropic-crawler-support-article` 0.1158) — findings in batch-006 (`bulk_doc_quarantine_high`); not re-run, per task.

## Next on the critical path (task says "separate task, after this kernel lands")
1. Concept dedup across the two epochs (the rename-of-old-science question in DD-009 — AIO vs crawlability/structured data — is now answerable but not yet asked).
2. Construct promotion + definition-conflict adjudication on the merged graph (the graph's first question).
3. Operator batch review of `corpus/staging/proposed_relationships/` for the kernel docs (21 names in pilot, more in bulk; none hit the ≥3×/≥2-doc patch rule).
4. Serving layer / FastMCP verbs / HF deploy (explicitly out of scope this task).

## Standing decisions made this session (logged, override if wrong)
- Pilot slot 4 → digital.gov DAP guide (no SME Visibility Diagnostic file existed).
- Bulk ran in `BURN_QUARANTINE_STOP_MODE=systemic` so isolated 0.10–0.15 breaches are findings, matching the task's flag-not-rerun rule.
- Phase 2's "excluded" marks on already-held Census standards were rewritten to `manifested/already_manifested` before the dixie sweep (they would otherwise have dropped three v1 docs from the corpus).
- Stale test `test_extract_json_tolerates_fences` updated to the documented `ModelInvocationError` behavior; no production change.
- Cost recorded as UNKNOWN (all calls unpriced by the control plane); CLI envelope estimate $86.43 is a lower bound.
