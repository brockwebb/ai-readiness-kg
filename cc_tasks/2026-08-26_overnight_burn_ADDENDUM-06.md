# ADDENDUM-06 to `2026-08-26_overnight_burn.md` (Seldon cd8449de)

**Date:** 2026-08-27 ~15:05 ET
**Scope:** amends ADDENDUM-05 §3c only. Everything else stands.

## §3c addition — v0.3.6 fixes over-diversion, not just span form

§3a found 52 of 89 locatable diverted candidates are `single_span`: relations the v0.3.5 rule would admit, which the model routed to `proposed_relationships` anyway. Two rule changes were therefore needed, not one. On §3b PASS, v0.3.6 carries both:

1. **Evidence-set grounding** as ADDENDUM-05 §3c specifies (1–3 verbatim spans, ≤ 400 chars each, all within 800 chars, jointly covering both endpoint surface forms and a predicate cue).
2. **Diversion is the exception, not the default.** Prompt text: a relation goes to `proposed_relationships` *only* when no evidence set satisfying rule 1 exists in the document. If the model can quote the evidence, it must emit the edge with that evidence. Two worked examples in the prompt: (a) a single-sentence relation, emitted as an edge with one span; (b) a two-sentence relation with an alias, emitted as an edge with a two-span evidence set. One counter-example: a heading-implied relation, correctly diverted with the reason `structural_inference`.

`proposed_relationships` entries must now carry a `diversion_reason` from a closed list (`structural_inference | endpoint_not_located | predicate_not_located | distance_exceeded | other:<text>`) so §3a-style triage is a projection query next time, not a script.

## Verdict content for §3d

Report, alongside the pre-registered numbers: diversion count and reason histogram per doc, and the fraction of §3a `single_span` candidates that v0.3.6 admitted (the direct measure of whether defect 2 is fixed). Informational; the pass/fail rule is unchanged.
