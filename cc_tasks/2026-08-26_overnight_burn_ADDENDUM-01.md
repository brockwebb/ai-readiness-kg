# ADDENDUM-01 to `2026-08-26_overnight_burn.md` (Seldon cd8449de)

**Date:** 2026-08-26 ~23:35 ET
**Supersedes:** the clause "A FAIL is a finding for the morning, not a prompt tweak tonight" in Lane 1. That clause assumed an absent operator. The operator is present; the verdict's diagnosis is mechanical; the gate is cheap. Prompt **v0.3.5** re-enters Lane 1 tonight. **The pass threshold does not move** (F_upper < 0.10 per stratum, item-level faithful ≥ 0.70). Lane 4 keeps running; nothing here touches it.

## Lane 0′ — v0.3.5 (zero spend)

Implements exactly the three patterns in `docs/research/2026-08-26_pilot_reextract_v034_verdict.md`. No other prompt changes.

1. **Positive Instrument criterion.** An Instrument node is emitted when the document *specifies, applies, evaluates, or documents* the instrument — i.e., the text itself carries at least one attribute-bearing description (method, owner, year, inputs, outputs) that a span can cover. A surveyed instrument in a survey paper meets this (the survey documents it). A named instrument with no attribute-bearing text in the document is a Concept with `mentions`. Two examples in the prompt: AIDRIN in `aidrin-hiniduma-2024` ⇒ Instrument; an instrument named once in a related-work sentence ⇒ Concept. Attribute nulling rule (v0.3.4) unchanged — the criterion decides *node type*, spans decide *attributes*.
2. **Node span ≠ attribute spans.** Restate, as the first grounding rule in the prompt: every node's own `grounding_span` must contain the node's `name` verbatim (or the exact surface form used, recorded as an alias); per-attribute `grounding_spans` are *in addition*, never a substitute. Add a parser-side precheck that reports the count of nodes whose span lacks the name before quarantine so the pilot verdict shows it as a number.
3. **Truncation is a status, never zero.** In `model_stub`/pipeline: an envelope that fails `_extract_json` with output tokens above `truncation_suspect_tokens` (config; set 40,000 from tonight's 67,057 observation) is recorded as `parse_failed_truncated` on the document, counted as `unusable` in every lane metric, and **retried once in per-layer emission mode**: same headless session, document already in the cached prefix (DD-019 §3), three resumed turns — (a) nodes except Instrument/Measure, (b) Instrument + Measure, (c) edges referencing the ids emitted in (a)/(b). Each turn is parsed and grounded independently; the three layers are merged into one extraction event with `emission_mode: per_layer`. Per-layer is fallback only; single-pass stays the default. Unit test: a stubbed truncated envelope triggers the fallback and the merged event carries all three layers.
4. Profile `reextract_v035`, sha-pinned; v0.3.4 profile retained as history. Suite green before Lane 1′.

## Lane 1′ — pilot re-run, same 3 docs, same protocol, new run id `pilot_v035`, ceiling 3M

- Precondition added to the verdict (not to the threshold): admitted items > 0 in **both** strata for ≥ 2 of the 3 docs. If not met, the verdict is `FAIL:harness_or_prompt`, the judge is not run (no spend on judging nothing), and the raws are diagnosed as before. If met, judge as pre-registered.
- Run alongside Lane 4 with `MAX_CONCURRENT_MODEL_CALLS=1` for this process (Lane 4 keeps its 2). Rate-limit backoff as specified.
- Verdict file: `docs/research/2026-08-26_pilot_reextract_v035_verdict.md`.

## On PASS

Launch Lanes 2 ∥ 3 as a second detached driver invocation (`--lanes 2,3`, profile `reextract_v035`, fleet 2, shared run ids as specified, same 04:45 ET stop, same running positive controls). Lane 4 continues untouched. The SUMMARY at exit covers all lanes from both invocations (read the ledger, not process state).

## On FAIL

Lanes 2/3 stay closed. Write the verdict with the same top-3 pattern structure. Stop; Lane 4 finishes the night. No v0.3.6 tonight — one revision on the diagnosed patterns is grounded; a second would be guessing.

## Ceiling

`CEILING` was blank in the execute line; CC correctly resolved to the standing 55M band. That stands for tonight. Lanes 2/3 declare 55M; the daily band is the global.

## Exit condition for CC (this addendum)

Lane 0′ green, Lane 1′ verdict on disk, and — on PASS — the second driver running detached with its first 3 calls' cache-read check logged. Then RESULT appended (not rewritten: add a dated section) and `seldon cc complete`.
