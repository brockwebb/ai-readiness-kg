<!--
Restoration v2 — stage-2 independent entailment check (task 2026-08-26_overnight_burn Lane 4).
Judges stage-1 passage proposals BLIND to stage-1's reasoning: only the attribute, the
proposed value, and the verbatim passage are shown. The fix for the v1 acceptance failure
(0.78 < 0.90): a related-but-not-entailing passage must be rejected here.
restoration_entailment_version: 1.0
-->
# Entailment judgment — attribute restoration proposals

For each task below: does the PASSAGE (a verbatim quote from a source document) **entail**
that the item's ATTRIBUTE has the given VALUE? Entail means a careful reader of the passage
alone would agree the attribute holds that value — not merely that the passage is related,
mentions the same topic, or is consistent with the value.

Output **strict JSON only** — a single array, no prose, no markdown fences:
`[{"id": "<task id>", "verdict": "entailed" | "not_entailed"}]`

Rules:
- `entailed` ONLY when the passage itself states or directly implies the value. Topical
  overlap, shared vocabulary, or plausibility is `not_entailed`.
- A passage that supports a DIFFERENT value for the attribute is `not_entailed`.
- For list values, every element must be supported; one unsupported element ⇒ `not_entailed`.
- When uncertain, answer `not_entailed`.

## Tasks

{{items_json}}
