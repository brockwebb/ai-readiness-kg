<!--
Versioned atomic-decomposition prompt (task 2026-08-22_faithfulness_probe, Phase 2; DD-015).
Prior art: FActScore (Min et al. 2023) atomic facts; RAGAS statement decomposition (Es et al. 2023).
Rendering substitutes {{items_json}}.
decompose_version: 1.0.0
-->
# Atomic decomposition of extracted free-text fields

For each input item, split the given free-text field into its **independent atomic
propositions** — the smallest statements that could each be true or false on their own.
Keep the original wording where possible; resolve pronouns using the item's own fields only;
do not add information; do not merge two facts into one. Aim for 1–4 propositions per field;
a short name or a single-clause sentence is ONE proposition.

Output **strict JSON** only — no prose, no fence — of the form:
{"facts": [{"item_id": "<id>", "attribute": "<field>", "fact_text": "<proposition>"}, ...]}

Every input item must appear at least once in the output.

Input items:
{{items_json}}
