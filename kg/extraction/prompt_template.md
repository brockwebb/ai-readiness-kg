<!--
Versioned extraction prompt template (schema_v0.1.md §5, whole-document protocol).
This file IS the prompt — it is loaded and rendered, never pasted inline into code strings.
Rendering substitutes {{schema_version}}, {{document_id}}, and {{document_text}}.
prompt_version: 0.1.0
-->
# Whole-document extraction — ai-readiness-kg schema {{schema_version}}

You extract a knowledge graph from ONE primary-source document, in a single pass. Output
**strict JSON** only — no prose, no markdown fences. Every node and every edge you emit MUST
carry a `grounding_span`: a **verbatim quote** copied from the document that supports it. If
you cannot quote the document for an item, do not emit it. No grounding span, no write.

Do NOT emit `document_id`, `model_id`, `schema_version`, `extraction_event_id`, or any
timestamp/event id — the harness owns those and injects them. Emit only the content you
extract: the extract plan, nodes, edges, and proposed_relationships below.

## Emission order (produce these keys in this order)

1. `extract_plan` — a `section_map` (list of `{heading, location}`) and a `concept_inventory`
   (an exhaustive list of the substantive ideas the document uses). Plan before you extract.
2. `concepts` — the exhaustive Concept layer, extracted first-class. Be thorough: thin concept
   coverage is a known failure mode.
3. `definitions` — verbatim definitions the document gives for a term.
4. `claims` — falsifiable assertions the document makes.
5. `instruments` and `measures` — assessments/indices/benchmarks and their individual items.
6. `standards` and `frameworks` — technical specs and conceptual structures the document names.
7. `edges` — relationships **among the nodes above**, using only the allowed edge types below.
8. `cites` — citations from this document to other documents (`from_id` is this document).
9. `proposed_relationships` — any relationship the schema below CANNOT express, each with a
   `grounding_span` and a `suggested_edge` name. These are staged for human review, never
   written directly. Use this instead of forcing a relationship into the wrong edge type.

## Node types and their properties

- **Concept**: name, aliases, description
- **Definition**: term, verbatim_text, normative_status (statute/policy/standard/academic/industry), as_of_date
- **Claim**: claim_text, claim_type (empirical/normative/speculative)
- **Instrument**: name, owner, year, method
- **Measure**: text, response_type
- **Standard**: name, version, steward, as_of_date
- **Framework**: name, owner, year

Do NOT emit Construct nodes: a Construct is a Concept promoted to measurability by an explicit
operator decision, not an extraction decision. Emit the underlying Concept instead.

Every node object also needs: `id` (unique within this output), `grounding_span`, `location`.

## Allowed edge types (type-validity is enforced; anything else is rejected)

`defines` (Document→Definition), `mentions` (Document→Concept), `asserts` (Document→Claim),
`about` (Claim→Concept), `operationalizes` (Instrument→Construct), `measures` (Measure→Construct),
`grounds` (Construct→Definition), `extends` (Definition→Definition, Framework→Framework),
`conflicts_with` (Definition↔Definition, Claim↔Claim), `cites` (Document→Document),
`builds_on` (Standard/Framework→Standard/Framework), `implements` (Standard→Concept).

Each edge object: `type`, `from_id`, `to_id`, `grounding_span`, `location`. The document node's
id is `{{document_id}}`.

## The document

Document id: `{{document_id}}`

```
{{document_text}}
```
