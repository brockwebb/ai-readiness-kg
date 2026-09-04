# CC Task: G1 calibration — independent-model rating of the blind sheet, agreement on real labels, disagreement escalation list, findings memo §4 update, provenance backfill (conditional)

**Date:** 2026-09-03
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-03_g1_calibration_rating_agreement_ADDENDUM*.md` files.**
**SEQUENCING:** after `cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings_RESULT.md` (exists). Do not commit biblio-cron files (Seldon task `989daaad`). The instrument stays frozen: no file under `assessment/harness/` or `assessment/config/` changes.
**Spend:** step 1 is the only model-calling step: one declared DD-022 run, **ceiling 2,500,000 tokens**, `claude -p` under Max OAuth only, model **`claude-fable-5-1`** selected with `--model`. Under the daily band (55M). Everything else is zero spend.

## Context

The v2 reviewer (Opus, CC) judged 232 flagged records; its agreement with an independent rater is unmeasured (`…_g1_freeze_…_RESULT.md` §1). **Desktop decision 2026-09-03:** the independent rater is a different model with no context beyond the sheet — not the operator, whose role is the ambiguity escalation only. This is the two-rater κ design (Cohen 1968 quadratic weights; the repo's own `tevv_stability.py` precedent on never reporting κ alone). The blind sheet, key, and agreement script exist (`assessment/results/g1_calibration_sheet_2026-09-03.{md,csv}`, `.g1_calibration_key_2026-09-03.json`, `scripts/g1_calibration_agreement.py`).

**Pre-registered consequence rule (no threshold):** the reviewer's genuine-loss counts are never reported alone. From this task on they are reported as a **range bounded by the scorer's count and the rater-implied count**, with κ_w and its interval stating how wide the disagreement is. Low κ widens the range; it triggers no redesign. Landis & Koch is not applied. The only escalation is a disagreement list (step 3).

## Step 1 — Rating run (model spend)

- `scripts/g1_calibration_rate.py`: one call per sample record through the same `model_stub` choke point as the consumer runs (hermetic empty temp cwd, no repo access, identity gate: a response reporting a model other than `claude-fable-5-1` stops the run — invariant 5). Each call's prompt is exactly: the sheet's labelling-instruction paragraph, the verbatim D2 level scale and D9 families as printed on the sheet, and **one** record block (prompt-as-seen, response, estimate label/value, family and published forms, mode, compression level). Nothing else — no other records, no scorer/reviewer/surface/model information. Response format requested: one line `LEVEL: <L0|L1|L2|L3|L4|U>` then `NOTE: <free text>`. Temperature/sampling as the CLI default; no retries on a parseable answer; one retry on an unparseable answer, recorded.
- Run id `g1_calibration_fable_2026-09-03`, `--ceiling-tokens 2500000`. Raw request + response persisted per record under `assessment/evidence/g1/calibration/<sample_id>.<model_id>.json` **before** the filled sheet is written.
- Output: `assessment/results/g1_calibration_sheet_2026-09-03_filled_fable.md` (the sheet with the LEVEL and NOTE lines filled from the responses; rater id `claude-fable-5-1`), a DataFile with content hash. If `--model claude-fable-5-1` is not selectable under Max OAuth, **stop here**, report the exact CLI error, and register nothing further from steps 2–4; do not substitute another model (an Opus rater is the reviewer's own model and is not independent), and do not use the API key (DD-007).

## Step 2 — Agreement on real labels (zero spend)

`scripts/g1_calibration_agreement.py` on the filled sheet + key, unmodified script. Register as Results (`g1_cal_fable_` prefix, `computed_from` the filled-sheet DataFile, `generated_by` the agreement Script `8eca971e`):
- rater-vs-scorer: quadratic-weighted κ over L0–L4 with 95 % bootstrap interval, raw agreement, the six-category unweighted κ including U, n rated, n U;
- rater-vs-reviewer on the review queue via the pre-registered implied-verdict rule: κ, interval, raw agreement, positive specific agreement on `parser_miss`;
- the confusion tables as DataFiles;
- **the range**: scorer genuine-loss count, reviewer count, rater-implied count (rater level < L3 ⇒ genuine; ≥ L3 ⇒ parser miss; U counted separately), for the pooled Opus grid extrapolated by stratum weights from the 60 (state the extrapolation and its assumption of stratum-homogeneity plainly; register the three numbers and the stratum weights).
Also register the stratum-level agreement table (per scorer level × reviewer verdict: n, raw agreement) so the reader can see where disagreement lives.

## Step 3 — Escalation list (zero spend)

`assessment/results/g1_calibration_disagreements_2026-09-03.md`: every sample record where **rater and reviewer differ by ≥ 2 levels** (mapping reviewer verdict to a level via the key's scorer level and the implied-verdict rule) or where either gave U. Per record: sample id, record id, passage, response, family, scorer level, reviewer verdict + note, rater level + note. No CC commentary, no proposed resolution. This is the only artifact the operator is asked to look at, and only if he chooses. Register as a DataFile; link the ResearchTask `85851bcd` (rename its description by a new task if the tool cannot rename: "Rater agreement computed 2026-09-03; operator escalation list at …; operator review optional") and close `85851bcd` by `seldon task close` **only if** its wording permits (its description says the operator labels; the operator did not). If it does not permit, leave it `proposed` and create the replacement task `completed` with the correct description; report which.

## Step 4 — Findings memo §4 and DD-037 (zero spend)

- `docs/research/2026-09-03_g1_eval_findings.md` §4: replace the "uncalibrated" paragraph with: rater identity and independence conditions; κ_w [interval] rater-vs-scorer; κ [interval] rater-vs-reviewer; the genuine-loss **range** (three tokens) replacing every place the memo cites a reviewer count alone (grep the memo for `genuine` and fix each); the escalation list's count and path. Every number a `{{result:}}` token; `g1_resolve_results.py --check` must resolve 100 %. Register the edit by a new DesignNote version per the project's convention for updated memos (if the convention is "append a dated section", do that instead of replacing; report which).
- Append **DD-037** to `docs/design_decisions.md`: independent-model rater design; the no-threshold consequence rule (range, not verdict); disagreement-list escalation as the operator's only role; the independence conditions (different model, hermetic cwd, single record per call, no aggregate results in context); why the operator does not label (touchpoint list, closed).

## Step 5 — Provenance backfill (conditional, zero spend)

If Seldon task `0bc41cfc` has landed a `seldon result backfill-provenance` (check the seldon repo's CLI), run it for the 515 `g1_v2_pooled_opus_*` Results against DataFile `0bc7bcdb` and report the edge count. If it has not landed, **skip** and say so; do not hand-write 515 events.

## Step 6 — Close

`seldon verify` (cron files expected dirty; say so), `seldon cc complete`, RESULT with the discrepancy section, suite counts, `kg.spend status` for the run, commit, push.

## Discrepancies to report, not reconcile
- If the identity gate stops the run (a response reports another model), report the count reached and register nothing from the partial sheet.
- If more than 6 of 60 rater answers are unparseable after one retry, report the raw responses and do not extrapolate the range; register κ on the parseable subset with n stated.
- If the agreement script fails on a real-label edge case its synthetic tests did not cover, report the case and the traceback; do not patch the script in this task.

## Not in this task
Any change to parser, scorer, prompts, or fixtures. Any threshold on κ. Any edit to a registered Result, RESULT, DD, or the v2 memo sections other than §4. Operator labeling. Rating by any model other than `claude-fable-5-1`.
