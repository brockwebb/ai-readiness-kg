# CC Task: G1 instrument freeze at v2 — reviewer calibration sample (blind), two-leg G1 redefinition in the skeleton, findings memo from registered Results, deck slide draft, DD-036

**Date:** 2026-09-03
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-03_g1_freeze_calibration_redefinition_findings_ADDENDUM*.md` files.**
**SEQUENCING:** after `cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression_RESULT.md` (exists). Do not commit biblio-cron files (Seldon task `989daaad`).
**Spend:** zero model calls. Every number in every deliverable resolves to a registered `g1_v1_*` / `g1_v2_*` Result via `{{result:...}}`; no literal that is not also a Result.

## Context and decision

v2 (`…_v2_product_surfaces_compression_RESULT.md`) is the pilot instrument. **Desktop decision 2026-09-03: the G1 EVAL instrument is frozen at (`g1-parse-v2`, `g1-score-v2`, prompt epoch `g1-v2-2026-09-03`, consumer `claude-opus-5`) for the January pilot.** v3 items are a registered backlog (ResearchTask `73f0aa5d`), not queued work. Rationale recorded here and in DD-036: the remaining parser misses bias the loss rate upward, i.e. against the finding, so the finding's direction survives them; further scorer work changes magnitudes, not conclusions, and magnitudes are what the calibration run is for.

The finding this task carries into the instrument: the declared leg and the observed leg dissociate. The surfaces the declared probe scores PASS (coded `_E`/`_M` API tables) are where restatement loses uncertainty most (H3 supported; §6.5 join); compression drives loss more than consumer strength (E4 supported; C1 underpowered); the form-shift mechanism appears only under compression (E6). G1 as defined in the skeleton ("MOEs/CVs as structured fields, not footnotes") is the declared leg only and would score those API tables at the top. It must become a two-leg indicator.

Three things are not citable yet and this task makes them so or says why not: the reviewer's genuine-loss counts (an uncalibrated LLM judge), the G1 scoring rule (single-leg), and the findings (in a RESULT, not a document).

## Step 1 — Reviewer calibration sample (blind sheet for the operator)

The v2 reviewer (CC, criterion recorded per file) disagreed with the scorer on 54 of 232 flagged pooled records. Its agreement with a human is unmeasured. Produce the sample; the operator labels; a follow-up computes agreement. Nothing here is decided by CC.

- `scripts/g1_calibration_sample.py`: from the pooled Opus v2 reviewed file plus the control file, draw a **stratified random sample of 60 records** with a fixed seed recorded in the file: strata = scorer level {L0, L1, L2, L3, L4, unparseable} × reviewer verdict {genuine, parser_miss, not_in_queue}, proportional allocation with a floor of 3 per non-empty stratum; the seed and the stratum table are the first block of the sheet.
- Sheet: `assessment/results/g1_calibration_sheet_2026-09-03.md` (and `.csv`). Per record: sample id, the **passage** (the exact text the consumer saw), the **response** verbatim, the estimate label and value, the qualifier family and its published forms, mode and compression level. **Nothing else** — no scorer level, no reviewer judgment, no failure class, no surface type, no model id. The key mapping sample id → record id lives in a separate gitignored file `assessment/results/.g1_calibration_key_2026-09-03.json` that the sheet does not reference.
- Labeling instructions at the top of the sheet, one paragraph, the D2 level definitions verbatim from DD-033 plus D9 families from DD-035, and one question per record: "Which level (L0–L4) did the response achieve for this family, or U if the qualifier is stated in a form you cannot classify?" and a free-text note.
- `scripts/g1_calibration_agreement.py`: reads the filled sheet + key, computes Cohen's κ (weighted, quadratic, on the ordinal levels) between operator and scorer, and between operator and reviewer, with 95 % bootstrap intervals; also raw agreement and a confusion table. Test it on a synthetic filled sheet. It is not run on real labels in this task.
- Register the sheet, key path (path only), and both scripts as Seldon artifacts; a ResearchTask "Operator labels G1 calibration sheet; then run g1_calibration_agreement" in state `proposed`, depends_on the sheet.

## Step 2 — Two-leg G1 in the skeleton and protocol

Rewrite the G1 row of `docs/crosswalk/usafacts_operationalization_skeleton.md` and the G1 note. New content (mechanical from what follows; no new design):

- **G1 has two legs, scored as a vector, no composite** (protocol §3 / June decision: no composite until intended use is decided).
  - **G1-D (declared):** the existing `g1_declared` probe — uncertainty fields present as structured fields beside estimates. AUTO, public tier. Unchanged.
  - **G1-O (observed):** the v2 EVAL — family preservation rate (L3+ share of scored families) at indirect `none`, with the unparseable share and the `short`/`tight` rates reported beside; pinned consumer, prompt epoch, parser and scorer versions stamped; per surface. EVAL, `paid` tier (standing harness). **No PASS/PARTIAL/FAIL at product level in v0.2.x**: the rate and its Wilson interval are the score until the January calibration run sets a boundary.
- **Dissociation statement** in the G1 note, one sentence, with the two Results that show it (`g1_v2_pooled_opus_…table_coded…` loss vs `…prose_labeled…`; the §6.5 join file). Structured fields are necessary for G1-D and are not sufficient for G1-O.
- **Compression is a reported condition, not a scored one**, until intended use says which condition the consumer of the assessment cares about.
- Skeleton §5d G1 Evidence cell: the v2 DD-035 and DD-036 references, the 17 + 4 + 17 admissions by doc_id groups (memo, g1srp, g1sfc), the three pilot RESULT files. Version bump.
- `docs/crosswalk/assessment_protocol.md` §9: replace the eval-family paragraph with G1-D / G1-O as two vectors; one sentence that G1-O's denominator is families (D9). Keep it to the length of what it replaces.

## Step 3 — Findings memo

`docs/research/2026-09-03_g1_eval_findings.md` (new; registered as a DesignNote; internal — not for distribution until the operator says so). Structure, and nothing outside it:

1. Question and construct (three sentences; cite the memo and DD-033/034/035).
2. Instrument at freeze: fixtures (surface types, counts per split), prompts, consumer, parser/scorer versions, gate results (v1 fresh, v2), spend per run. A table.
3. Findings, each a pre-registered statement with its verdict and the Result tokens: E3 (v1, not supported), E4, E5, E6, H3 supported; H4, H5, C1 underpowered with counts; the declared→observed join table (§6.5) reproduced from its file. Every number a `{{result:}}` token.
4. What the reviewer counts are and are not (Step 1's status: LLM judge, agreement unmeasured, sample issued).
5. Limits: single consumer at scale; handbook stratum thin in holdout; suppressed cells unmeasured; footnote-distance range; the freeze amendment (§9.1) stated plainly; parser miss rate as an upward bias on loss.
6. What changes in the instrument (Step 2) and what does not.
No recommendations section. No adjectives about the findings.

## Step 4 — Deck slide draft (draft only; not sent)

`framework_deck_2026-09-01.pptx`: read `/mnt/skills/public/pptx/SKILL.md` first. Add **one** slide after the current G1 slide, titled with the dissociation statement, carrying the §6.5 join as a small table (surface type, declared leg, observed loss at `none`) and the E4 three-rate line. Numbers from Results via the deck's resolver as slide 15 uses. Save as `framework_deck_2026-09-03_draft.pptx`; the 09-01 deck is not modified. Register as a Seldon artifact in state `proposed`. The operator decides whether it goes anywhere.

## Step 5 — DD-036 and close

Append DD-036 to `docs/design_decisions.md`: instrument frozen at v2 for the pilot and why; two-leg G1 with no composite; reviewer-calibration protocol (blind sheet, stratification, κ); freeze-is-last-act rule; v3 backlog reference `73f0aa5d`. `seldon verify` (cron files expected dirty; say so), `seldon cc complete`, RESULT with the discrepancy section, suite counts, commit, push.

## Discrepancies to report, not reconcile
- If the deck resolver cannot reach a `g1_v2_*` Result by name (Result names are in descriptions, not a `name` property — see how slide 15 resolves and follow it), report the lookup path used.
- If the pooled reviewed file lacks a stratum needed for the sample floor, report the empty stratum and the allocation actually used.
- If any skeleton text outside the G1 row needs to change to stay consistent, report the sentence and leave it.

## Not in this task
Any model call. Any parser or scorer change (frozen). Running the agreement script on real labels. Product-level thresholds. Sending or publishing anything. Editing any RESULT, DD, memo, or registered Result.
