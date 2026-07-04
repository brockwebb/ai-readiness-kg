# CC Task — Schema v0.2 + Promotion + Model Pin (v2: re-baseline dropped)

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Supersedes:** cc_tasks/2026-07-03_schema_v02_promotion_rebaseline.md (3d1ccbec — Part 4 re-baseline cut by operator: bulk's own per-doc gates provide identical protection at doc 1. Parts 1–3 carry forward verbatim; if 3d1ccbec was partially executed, complete the equivalent parts here without redoing finished work.)

## Part 1 — Schema v0.2 (append-only)

Exactly these edges added to schema.yaml + doc (bump to v0.2, changelog cites pilot audit). Strict index-pairing metadata. external_alignment annotations:

| Edge | Legal pairs | external_alignment |
|---|---|---|
| `uses_measure` | Instrument→Measure | https://www.w3.org/ns/sosa/ (madeBySensor/implements pattern) |
| `measures` | Measure→Concept; Instrument→Concept | http://www.w3.org/ns/sosa/observes |
| `has_component` | Framework→Concept; Concept→Concept | http://purl.obolibrary.org/obo/BFO_0000051 (part-whole ONLY) |
| `subtype_of` | Concept→Concept | http://www.w3.org/2000/01/rdf-schema#subClassOf (is-a ONLY) |
| `precedes` | Concept→Concept | http://purl.obolibrary.org/obo/BFO_0000063 |

No other edges, no new node types (Organization/Project rejected in audit — changelog note). Parser/loader/tests updated.

## Part 2 — Promote the 91 staged items (curated events, no re-extraction)

Mapping: uses_measure → uses_measure; {measures, measures_concept, evaluates, assesses, operationalizes} → measures; {has_component, has_category, categorizes, sub_level_of, part_of, decomposes} → has_component; subtype_of → subtype_of; precedes → precedes. Everything else stays staged untouched.

Each mapped item re-enters through the parser gate (pairing + grounding re-validation) and is written as a curated_promotion event: original staged id, mapping applied, span, §4 provenance. None-endpoint or gate-failing items stay staged with reason. Report promoted/remaining counts by edge.

## Part 3 — Prompt hardening + model pin

- Prompt: grounding_span must be character-exact from source, no paraphrase. Template version bumped, stamped per §4.
- model_config.yaml → **claude-opus-4-8**. Identity gate pins Opus: any other envelope model_id → discard unparsed, STOP.

## Acceptance

v0.2 committed, tests pass; promotion report; prompt + model config committed. Zero API keys. `seldon cc complete cc_tasks/2026-07-03_schema_v02_promotion_v2.md`; `seldon verify` clean.

## Out of scope

Any extraction call. Bulk. Ingested transitions. Long-tail staged items.
