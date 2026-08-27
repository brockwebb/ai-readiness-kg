# ADDENDUM-03 to `2026-08-26_overnight_burn.md` (Seldon cd8449de)

**Date:** 2026-08-27 ~08:40 ET
**Scope:** adds a model arm to Lane 1″ (ADDENDUM-02). Everything else in ADDENDUM-02 stands. If Lane 1″ has already started under 4.8 when this is read, run the Fable arm as a second pass on the same 5 docs; do not discard the 4.8 arm.

## Two arms, same docs, same prompt v0.3.5, same protocol

- Arm A: `claude-opus-4-8`, effort high (current pin).
- Arm B: `claude-fable-5`, effort high. **Precondition for the arm:** 3 trivial probe calls (`claude -p`, no document, "reply with your model id") return `claude-fable-5` in the envelope 3/3. Any other id ⇒ arm B skipped, logged `fable_reroute`, and the July continuity reason stands. The model-identity gate applies per call in the arm exactly as it does for A.
- Run ids `pilot_v035b_opus48`, `pilot_v035b_fable5`; ceilings 4M each. Reuse the 3 existing 4.8 extractions for arm A as ADDENDUM-02 says; arm B extracts all 5.
- Judge both arms; raters unchanged (Opus 4.8 + Sonnet 5). A rater judging its own arm's output is a known bias direction; report per-rater agreement per arm so it's visible, and note that Sonnet 5 is the same-model rater for neither arm.

## Pre-registered selection rule (recorded before any arm B call)

1. An arm passes iff it meets the ADDENDUM-02 threshold (F_upper < 0.10 per stratum, item-level faithful ≥ 0.70).
2. Both pass ⇒ the bulk model for Lanes 2/3 is the arm with the lower pooled F point estimate **only if** its F_upper is also lower and the difference in item-level faithful ≥ 0.05; otherwise **A** (continuity with the 134-doc corpus; a model change is a new epoch and the probe stratifies by epoch, so don't create one on a tie).
3. Exactly one passes ⇒ that arm.
4. Neither ⇒ Lanes 2/3 closed; both verdicts written.
5. Cost per document per arm is reported from the ledger (settled tokens ÷ docs) and is **informational** — it does not enter the rule.

Whichever arm is selected is written to `model_config.yaml` `model_id` with a comment citing this addendum and the verdict path; the model-identity gate then pins it for the bulk lanes.

Verdict: `docs/research/2026-08-27_pilot_reextract_v035b_verdict.md` with both arms side by side.
