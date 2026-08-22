<!--
Versioned faithfulness-judge prompt (task 2026-08-22_kernel_tevv, Phase 3; DD-013).
This file IS the prompt — loaded and rendered, never pasted inline into code.
Rendering substitutes {{item_kind}}, {{item_type}}, {{item_json}}, {{grounding_span}}.
judge_version: 1.0.0
-->
# Faithfulness judgment — one extracted item against its grounding span

You are checking whether ONE item extracted from a document is supported by the verbatim
passage that was cited as its evidence. You see only the item and the passage — not the
document. Output **strict JSON** only, no prose, no markdown fence:

{"entailed": true|false, "reason": "<one sentence>"}

Decision rule — answer `true` only if a careful reader of the passage alone would accept the
item as stated:
- A **node** (concept, definition, claim, practice, measure, standard, framework, instrument,
  tool, platform) is entailed if the passage names or clearly describes it and every factual
  attribute shown in the item (e.g. a definition's wording, a claim's assertion, a tool's
  steward) is supported by the passage. Paraphrase is fine; added facts are not.
- An **edge** (`from -[type]-> to`) is entailed if the passage supports that the relationship
  of that type holds between those two things. The endpoint identifiers are slugs; judge the
  relationship, not the slug spelling.
- A `grounding_span` that merely mentions the item's topic without supporting the stated
  content is **not** entailment.
- If the passage is too short or too generic to support the item, answer `false`.

Item kind: {{item_kind}}
Item type: {{item_type}}
Item:
{{item_json}}

Grounding span (verbatim from the source document):
"""
{{grounding_span}}
"""
