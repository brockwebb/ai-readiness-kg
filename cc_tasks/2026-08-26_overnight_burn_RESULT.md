# RESULT — Overnight burn 2026-08-26 → 27 (state: **running**)

**Task:** `cc_tasks/2026-08-26_overnight_burn.md` (Seldon ResearchTask **cd8449de**). No addenda existed at start (glob → empty).
**Written:** 2026-08-27 ~03:35 UTC (23:35 ET), at CC handoff to the detached driver per the task's exit rule. The driver's `docs/research/2026-08-27_overnight_burn_SUMMARY.md` at exit covers Lane 4's completion; this RESULT states what was verified live.

## CEILING — the execute line carried an unfilled placeholder (discrepancy, decided on grounding)

The execute line read `CEILING=<your token number>` — a literal template placeholder, not a number. Decision (logged, operator overrides by addendum): **CEILING = 55,000,000**, the standing declared band (control plane `declared_caps("extraction")`: daily 55M), with `controls.yaml spend.daily_tokens` **untouched** — the task's own text makes the daily cap "the real global" and gives CEILING band-changing effect only when it *exceeds* 55M, so the conservative grounded reading of an unfilled placeholder is *no band change*. Under the declared cap → run, per standing doctrine. All lane ceilings below are declared on `state/spend_ledger.jsonl` (DD-022); the daily band is the true bound.

## Verified live at handoff

| item | state |
|---|---|
| Lane 0 (zero spend) | **done, committed** — prompt v0.3.4 (`kg/extraction/prompt_template.md`: Instrument per-attribute `grounding_spans`, no-background-knowledge rule, cited-only→Concept, semantic-edge span rule); schema **v0.3.4** append-only (+tests); parser nulls uncovered Instrument owner/year/method at parse and routes structural semantic edges to `proposed_relationships` (6 new unit tests); profile `reextract_v034` pins the template sha (apply_profile refuses drift); projection: stratum-scoped `superseded_strata` + gate-before-wire `restoration_class_accepted` overlay; `model_stub` rate-limit release (`ModelRateLimitError`); `batch_repair --kinds/--exclude-types`. Suite **190 green** at launch. |
| Driver | **running detached** (pid 25659, `logs/overnight_burn_2026-08-26.log`; status `state/overnight_burn_status.json`; STOP file honored; wall-stop 08:45 UTC = 04:45 ET; per-lane commit+push; rate-limit backoff 600 s ×6 → `rate_limited`). |
| Lane 1 pilot | **completed — verdict FAIL, on disk** (`docs/research/2026-08-26_pilot_reextract_v034_verdict.md`). Pilot docs (top Instrument counts from the live projection): `data-readiness-for-ai-a-360-degree-survey`, `aidrin-hiniduma-2024`, `fcsm-23-02-a-framework-for-data-quality-case-studies`. Zero admitted items in both strata → pre-registered rule fires without reaching the F-threshold arithmetic. |
| Lanes 2 & 3 | **skipped by the pre-registered rule** (both depend on Lane 1 PASS). No stratum supersession events were written; the triage epoch remains unextracted. |
| Lane 4 | **running** (independent of Lane 1 by design): restoration v2 stage 1 (Haiku propose, batch 40, session-resume, decoys, cache check) → stage 2 (Sonnet entailment, batch 10, blind) → 100-sample acceptance gate ≥ 0.90 before any projection; then relocation resume (`batch_repair --kinds relocate --exclude-types Instrument --redo-unrepairable`, shards 0/2, 1/2) and the 50-item re-judge of prior `model_assisted_batch` relocations. Worklist measured live: **7,908 open attributes over 132 docs** (the task's 2,545 deferred + the reversed v1 class + remaining nulls, minus Instrument — scope arithmetic discrepancy, reported not reconciled). |

## Lane 1 FAIL — what it is and is not (full diagnosis in the verdict doc)

Not a fabrication measurement: the corrected prompt **over-corrected**. (1) First-party instruments were demoted to Concepts under the cited-only rule — a survey OF instruments yielded 0 Instrument nodes; (2) span-coverage-on-`name` quarantined 38 nodes in one doc, collapsing 100 edges on unresolved endpoints; (3) the aidrin response (67K output tokens) came back with no parseable envelope layers — likely mid-JSON truncation — and the lane counted it as zero (counting defect recorded). Top-3 patterns + re-run trigger (prompt v0.3.5 through the same pilot gate) are in the verdict. Per the task: a finding for the morning, **no prompt tweak tonight**.

## Incidents during handoff (reported)

1. **First driver launch (02:47Z) aborted at 02:56Z**: Lane 1 called the parser on raw model output without the pipeline's provenance-ownership step (`document_id` injection) → `ValueError`. Fixed (`extract_doc` now applies `_apply_provenance_ownership`, per-doc ValueError hardened); driver relaunched 03:0xZ. Cost: one settled pilot extraction (~130K tokens) plus one killed in-flight Haiku reservation left outstanding on `restoration_v2_s1` (≤36K, conservative direction). Both visible on the ledger; history preserved in the status file under `driver_run1`.
2. **Lane 3 Phase-0 retag scope**: only the manifested DOC RFI notice (`doc-rfi-ai-open-gov-data-2024`) carries a `construct_arm` to supersede; the regulations.gov comments index was excluded (`R3_listing_page`, 7456614d) and has no manifest entry or arm. The driver emits the RFI retag when Lane 3 runs; since Lane 3 was skipped, **no retag event exists yet** — it rides the Lane 3 re-run.

## Spend at handoff (ledger, DD-022 first production night)

`pilot_instr_sem` (3M ceiling): two pilot rounds ≈ 0.8M settled, 0 refusals. Reserve-before-dispatch worked exactly as designed on its first unattended night; per-run totals, reconcile exit codes, and Lane 4 totals land in the SUMMARY via `python -m kg.spend status`.

## Deliverables checklist

- [x] Lane 0 code + tests + schema v0.3.4 + profile pin
- [x] Driver scripts (`overnight_burn.py`, `overnight_burn_2026-08-26.sh`, `restoration_v2.py`, entailment template); status file; wall-clock stop; rate-limit backoff; per-lane commit
- [x] Lane 1 verdict on disk (FAIL, with diagnosis and re-run trigger)
- [x] RESULT (this file, state running) + `seldon cc complete`
- [ ] SUMMARY — written by the driver at exit (Lane 4 totals, gate verdicts, reconcile codes)
