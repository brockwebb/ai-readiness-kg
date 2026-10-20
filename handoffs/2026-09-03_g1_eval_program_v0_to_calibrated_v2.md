# Handoff — G1 EVAL program: prior art → v0 → v1 → v2 → independent calibration → freeze

**Date:** 2026-09-03 (thread ran 2026-09-02 evening → 2026-09-03; last CC run stamps 2026-09-04 UTC)
**Project:** ai-readiness-kg
**Supersedes:** `handoffs/2026-09-02_post_burn_reconciliation_and_g1_prior_art.md` (which itself superseded the 09-01/02 handoff). Known defect: `seldon go` may serve an older handoff as "latest" (Seldon task `f951ed84`); trust the newest file on disk.
**Rule for the next session:** verify against the graph and the RESULT files before trusting anything below. This is prose compression of six RESULTs.

## 1. State in one paragraph

G1 (uncertainty legibility) has a measured, frozen, two-leg instrument. **G1-D** (declared) is the unchanged `g1_declared` field-pattern probe. **G1-O** (observed) is an EVAL: family preservation rate (L3+ share of qualifier families) under restatement with the source in context, pinned consumer `claude-opus-5`, prompt epoch `g1-v2-2026-09-03`, `parser_version g1-parse-v2`, `scorer_version g1-score-v2`. Frozen for the January pilot (DD-036). The headline result: **the two legs dissociate** — coded `_E/_M` API tables score PASS on G1-D and lose most on G1-O; compression drives loss (0.843 → 0.563 → 0.278 across none/short/tight) more than consumer strength; the form-shift mechanism appears only under compression. The instrument's binary grain (L3+ vs below) is robust to an independent rater; its sub-L3 level partition is not (DD-038). All numbers are registered Results; the findings memo resolves 214/214 tokens. **Nothing is pending from the operator** except, optionally, four escalated disagreement records and where the deck draft goes.

## 2. Artifacts (canonical locations)

| what | path / id |
|---|---|
| prior-art memo (17 sources, 162 queries + F7) | `docs/research/2026-09-02_g1_eval_prior_art.md`; erratum `…_ERRATUM-01.md`; F7 addendum `…_F7_addendum.md` |
| findings memo **v1.2** (internal; not for distribution) | `docs/research/2026-09-03_g1_eval_findings.md` (DesignNote `92795fa0`; v1.1 `c9a81161`, v1.0 `6760baaf` retained) |
| design decisions | DD-033 (level scale, parse+unparseable, no product threshold), DD-034 (parser versioning, sealed holdout), DD-035 (product test, families, binding, covariates), DD-036 (freeze, two-leg G1, freeze-is-last-act), DD-037 (independent-model rater, range not verdict), DD-038 (binary is score, levels descriptive) |
| skeleton | `docs/crosswalk/usafacts_operationalization_skeleton.md` **v0.2.8** (G1 row two legs; carries `{{result:}}` tokens — residue task `a74433f8` reverts to name-only) |
| protocol | `docs/crosswalk/assessment_protocol.md` §9 (G1-D/G1-O as two vectors; families as denominator) |
| harness (frozen) | `assessment/harness/probes/g1_declared.py`, `g1_preservation.py`, `_g1_parse.py`; `harness/consumers.py`; `assessment/config/g1_prompts.toml`, `g1_consumer.toml`, `g1_pilot.toml` |
| fixtures | `assessment/tests/fixtures/g1/` (v1 prose) and `…/g1/v2/` (product surfaces; `declared_leg.json` join) |
| evidence | `assessment/evidence/g1/{,holdout/,v2/{dev,holdout,control}/,calibration/}` — raw responses, reusable for any re-score |
| results files | `assessment/results/g1_v1_*`, `g1_v2_*`, `g1_calibration_*` |
| deck draft | `docs/crosswalk/framework_deck_2026-09-03_draft.pptx` (DataFile `c3e98de7`, `proposed`; one new slide 14; the 09-01 deck untouched). **Distribution is the operator's call.** |
| resolver (workaround) | `scripts/g1_resolve_results.py` — matches Result name in `units` property; retire when Seldon task `0bc41cfc` lands |
| RESULTs, in order | `cc_tasks/2026-09-02_g1_eval_probe_family_v0_RESULT.md` → `2026-09-03_g1_eval_v1_parser_fullgrid_errata_RESULT.md` → `2026-09-03_g1_eval_v2_product_surfaces_compression_RESULT.md` → `2026-09-03_g1_freeze_calibration_redefinition_findings_RESULT.md` → `2026-09-03_g1_calibration_rating_agreement_RESULT.md` → `2026-09-03_g1_memo_v1_2_level_caveat_RESULT.md` |

## 3. Key numbers (Result names; verify in graph, do not copy from here)

- v1 handbook prose, holdout fresh: preservation 0.919 [0.825, 0.965]; pooled 0.969; 0 L2 in 196 (E3 not supported).
- v2 pooled Opus indirect by compression: `g1_v2_pooled_opus_compression_indirect_{none,short,tight}_preservation_rate` = 0.843 / 0.563 / 0.278 (E4 supported, disjoint intervals).
- v2 H3: `g1_v2_pooled_opus_table_coded_*` vs `…prose_labeled_*` — coded tables lose more (supported). Join: `assessment/tests/fixtures/g1/v2/declared_leg.json` and `g1_v2_join_*` Results.
- Control arm (Haiku 4.5, holdout only): ≈ Opus at `tight`; C1 underpowered.
- Calibration (rater `claude-fable-5-1`, 60 blind records): `g1_cal_fable_scorer_kappa_w` 0.392 [0.205, 0.614]; `g1_cal_fable_reviewer_kappa` 0.421 [0.206, 0.665]; `g1_cal_fable_preserved_exact_agreed` 18/18; `g1_cal_fable_parser_miss_reviewer_agreed` 14/14; genuine-loss range on the 232-record queue: rater 173 — reviewer 178 — scorer 232.
- Spend across the program: v0 185k (guard-refused at 200k ceiling), v1 3.59M, v2 6.59M, calibration 1.95M; all under the 55M daily band; every call `claude -p` Max OAuth.

## 4. Open graph items

**ai-readiness-kg**
- `73f0aa5d` v3 backlog (not queued): 25 holdout-motivated parser misses; suppressed-cell propositions (`estimate: null`, `fabricated_estimate`); H5 needs varied footnote distances; freeze-is-last-act; C1 wording/code rule; month-without-year vintage class; implied-verdict rule's `unparseable` defect.
- `a74433f8` hygiene residue: E3 caveat (v1 scorer, different sentence); skeleton token revert. Fold into the next G1 task.
- `989daaad` biblio cron leaves tracked files dirty; cron must commit its own writes. Every `seldon verify` this thread reported it.
- `85851bcd` stale ("operator labels") — leave `proposed` until Seldon has a `withdrawn` state; superseded in substance by `529133e4` (completed).
- Pre-existing, untouched: methodology document `docs/research/kg_construction_methodology.md` (outstanding Desktop deliverable); dedup design blocked on Lanes 2/4; A10/A11 gated on SEO SME publication; January pilot plan.

**seldon** (authored here when wanted; dispatched in the seldon directory)
- `0bc41cfc` Result registry contract: `--name` property; fail on unknown `--data-name` (515 G1 Results lack `computed_from`); `--allow-proposed` resolver mode; DataFile provenance edges. **Highest-leverage debt** — every project runs on the workaround resolver.
- `698d1d86` ontology: `corrects`, Issue→Result.
- `a3ba67a3` task lifecycle: `withdrawn/superseded` state; `seldon task close` CLI parity with the MCP tool.
- `f951ed84` stale handoff picker.

## 5. Decisions made this thread (operator can override any)

1. G1-O is a **product test**, not a consumer test; one weaker consumer as a control arm, never a factor.
2. Qualifier **families** (SE/MOE/CI at a level = one `interval` family; CV/RSE `relative`; flags/suppression `reliability`) are the scored unit.
3. **No product-level threshold** before the January calibration run; no rounding tolerance knob — rounding and compression are recorded covariates.
4. **Independent-model rater**, not the operator: operator's role is the ambiguity escalation only (four records at `assessment/results/g1_calibration_disagreements_2026-09-03.md`; five more are rule artifacts).
5. κ never gates; it widens a **range**. Landis & Koch not applied.
6. **Binary is the score**; levels are descriptive; any level claim needs a level-agreement estimate at its own grain.
7. Instrument **frozen at v2**; v3 is backlog.
8. Ansari 2026 stays cut.

## 6. Process defects this thread — Desktop's, recorded so they don't repeat

- v0 readiness gate was circular (parser tested on restatements its author wrote). Fix adopted: readiness only on sealed model output that does not exist until the parser is frozen.
- v0 ceiling set without reading the ledger (200k vs 34k/call floor). Fix: plan grids from `controls.yaml call_class_floors`.
- v1 holdout seal leaked through shared passages ("skip existing evidence"). Fix: split by passage.
- v2 freeze tagged before the prior-evidence re-score finished. Fix: **freeze commit is the last act** of the step (DD-036).
- Desktop invoked an operator "value input" touchpoint for labeling that the closed touchpoint list does not contain. Corrected: a second independent model rates; operator sees only escalations.
- Task-file premise errors CC caught rather than reconciled (correct behaviour): no deck resolver existed; no pptx skill on the machine; no `seldon task close` CLI; `0bc41cfc` lives in the seldon graph, not this one.

## 7. Next session

Start with `seldon go --brief` on this project and confirm §4 states. Then, in order of leverage: (a) author the **Seldon registry CC task** (`0bc41cfc` + `698d1d86` + `a3ba67a3` as one task; needs a short design pass on `name` uniqueness and the `--allow-proposed` render form against `seldon/paper/build.py`); (b) the **methodology document**; (c) G1 sleeps until January — when it wakes, the first task folds `a74433f8` and reads `73f0aa5d`.
