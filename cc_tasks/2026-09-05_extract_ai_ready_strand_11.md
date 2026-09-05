# CC Task — Extract the AI-ready-data-product strand (11 documents); fixtures excluded by rule; CQ v1 rerun

**Date:** 2026-09-05
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Premise (registered):** `cq_02_unextracted_sense_data_product_consumption` = 68 sentences in 15 documents (RESULT-02 of `2026-09-04_extract_g1eval_17_and_rerun`, §3a).
**Spend:** model spend, bounded, ceiling computed in §1 from the measured rate. **Claude Max OAuth only; any path reading `ANTHROPIC_API_KEY` is a stop condition.**

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. Decisions recorded (Desktop; append as one dated DD entry)

1. **Cohort = documents with ≥3 `data_product_consumption` sentences in §3a**, which is this strand's own peer literature: `worldbank-blog-open-data-to-ai-ready-2025`, `usdc-mcp-federal-open-data-pilot-2026`, `ccsa-2026-ai-ready-official-statistics`, `doc-rfi-ai-open-gov-data-2024`, `worldbank-fostering-ai-readiness-official-statistics`, `odi-framework-for-ai-ready-data-2025`, `bandi-2025-metadata-ai-ready`, `odi-ai-ready-national-data-library-2025`, `doe-data-cards-standardized-metadata-2026`, `unsc-2026-stoyanovich-open-data-responsible-reuse`, and **one** of `uk-ai-ready-data-action-plan-2026` / `uk-building-ai-ready-datasets-2026` — the §3a sentences are identical across the two, so first confirm by content hash or diff that they are the same text; keep the markdown substrate, cut the other with reason `duplicate_of:<id>` (an existing `excluded_by_design` reason class). If they differ materially, keep both and say so. Cohort is therefore 11, or 12 if they differ.
2. **The 22 fixture-epoch documents (`g1sfc-2026-09-03`, `g1srp-2026-09-03`, `g1dp-2026-09-02`) are eval fixtures, not literature.** Rule: any epoch tagged as a fixture epoch in the manifest is `excluded_by_design` with reason `eval_fixture`, and the gap diagnostic classifies it so. Closes Issue `2e226acb`. Their Document nodes stay (they are what G1 scores), but they are never queued.
3. **The 12 remaining `data_product_consumption` documents with <3 hits and everything else in the 55 stay deferred** under DD-024. Not a reversal.

## 1. Ceiling from the measured rate (DD-042, by hand until `9a627af8` lands)

From `state/extraction_gap_2026-09-04b.json` take the cohort's per-document chunk counts under the pipeline's current chunking (recompute if the file carries only estimates). Ceiling = `chunks × 45,521` (the g1eval measured productive rate, `g1eval_extraction_tokens_productive / 688`) × 1.15 headroom. Register the ceiling as a Result `strand_extraction_tokens_declared` before reserving. Report `chunks`, the rate used, and the ceiling. If the ceiling exceeds 20M tokens, stop and report; that is outside the number Desktop priced this at and the discrepancy is the finding.

## 2. Extract

Same path as the g1eval run (`run_g1eval_extraction` pattern, profile `bulk_v038` unless moved). Wave dispatch is now the only dispatch (`dispatch_waves`); confirm the run goes through it. Reserve-then-settle; stop at a document boundary if settled crosses the ceiling. Register `strand_extraction_tokens_productive` and `_wasted` on completion; wasted must be reported even if zero.

Projection replay. Rerun `scripts/extraction_gap_diagnostic.py` → `state/extraction_gap_2026-09-05.json`, `register_gap_results.py --suffix 2026-09-05`. Required: `run_ok_no_edges` = 0, `never_queued` = 0 (fixtures now excluded), `documents_with_edges` = 156 + cohort size.

## 3. Diagnostic and CQ v1 rerun, same set

`scripts/kg_diagnostic.py` → `kg_snapshot_2026-09-05`, Results `kg_diag_*_2026-09-05`. Delta table as in RESULT-02 §2.

`assessment/cq/run_cq.py` on `cq_set_v1.yaml` **unchanged at `369d717`** (assert the diff is empty), `--suffix 2026-09-05`. Report the four aggregates, `flip`, category flips, and the per-CQ table against the 2026-09-04b run. The §1.5 rule is evaluated and the branch reported. No harness repair, no criterion edits; judge caveat stands.

Special attention to CQ-02: with this cohort in, does the collapsed view now return a definition in the `data_product_consumption` sense? Quote the spans. This is the question the whole cohort was extracted to answer.

## 4. Issue: the CQ-09 gap claim

Register an Issue: the first harness RESULT quoted CQ-09's empty answer as graph support for "G1 is the sharpest gap"; RESULT-02 §3.3 withdrew that support (Comunikos, GRADE). The claim survives only re-scoped to *no AI-readiness assessment instrument measures uncertainty legibility*. Link the Issue to `cq_v1_cq09_*` Results (`annotates`) and record, in the Issue text, the v2 competency question that would test the re-scoped claim: Instruments that MEASURES an uncertainty-related Concept **and** whose parent Framework is an AI-readiness assessment (by normative status or by `ABOUT` an AI-readiness Concept). Do not edit the memo or deck; if v2 answers it, that is an erratum then.

## 5. Integration

`tests/` and `assessment/` green; `seldon verify` clean; Script/DataFile/Result registration; DD entry for §0; Issue `2e226acb` closed with the rule cited; `cc complete`; commit and push with the ledger delta.

## 6. RESULT must report

Cohort size and the duplicate determination; chunk count, rate, ceiling, productive, wasted; gap diagnostic reread; diagnostic delta; CQ before/after and the rule branch; the CQ-02 spans; the Issue id; premises contradicted.

## 7. Out of scope

Entity resolution (`93a628e8`) — next task, authored after this RESULT. CQ set v2. The 44 remaining deferrals. `609cb10b`.
