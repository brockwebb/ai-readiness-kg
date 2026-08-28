<!--
Versioned atomic-decomposition prompt (task 2026-08-22_faithfulness_probe, Phase 2; DD-015).
Prior art: FActScore (Min et al. 2023) atomic facts; RAGAS statement decomposition (Es et al. 2023).
Rendering substitutes {{items_json}}.
decompose_version: 1.1.0
1.1.0 (2026-08-27, task 2026-08-27_chunked_pilot §5): coordination is not redistributed.
  Diagnosed in 2026-08-27_pilot_instrument_verdict.md — 14 of 27 `span_truncated` facts had
  every content word inside the span and failed only because this decomposer had rewritten a
  coordinated list into per-conjunct sentences the source never wrote.
-->
# Atomic decomposition of extracted free-text fields

For each input item, split the given free-text field into its **independent atomic
propositions** — the smallest statements that could each be true or false on their own.
Keep the original wording where possible; resolve pronouns using the item's own fields only;
do not add information; do not merge two facts into one. Aim for 1–4 propositions per field;
a short name or a single-clause sentence is ONE proposition.

**Do not redistribute a coordination.** When the field coordinates a list under one head —
"designed for data profiling, cleansing, and monitoring capabilities" — that list is ONE
proposition. Do NOT emit one proposition per conjunct with the head copied onto each ("is
designed for data monitoring capabilities"): that manufactures a sentence the source never
wrote, so no quote from the source can entail it. Split only where the source itself states
the predicate separately for each element.

Output **strict JSON** only — no prose, no fence — of the form:
{"facts": [{"item_id": "<id>", "attribute": "<field>", "fact_text": "<proposition>"}, ...]}

Every input item must appear at least once in the output.

Input items:
{{items_json}}
