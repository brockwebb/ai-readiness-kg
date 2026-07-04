# CC Task — Schema v0.2, Staged Promotion, Opus Re-baseline

**Date:** 2026-07-03
**Project:** ai-readiness-kg (/Users/brock/GitHub/ai-readiness-kg)
**Session type:** CC execution
**Immutable once written. Changes require a new task file.**
**Authority:** docs/schema_v0.1.md + this task's §9 audit rulings (Desktop, 2026-07-03). Conflicts = STOP and report.

## Part 1 — Schema v0.2 (append-only evolution)

Add exactly these edge types to schema.yaml + the schema doc (bump to v0.2, changelog note citing the pilot audit). Strict index-pairing metadata required. Each edge carries an `external_alignment` annotation:

| Edge | Legal pairs | external_alignment |
|---|---|---|
| `uses_measure` | Instrument→Measure | https://www.w3.org/ns/sosa/ (madeBySensor/implements pattern) |
| `measures` | Measure→Concept; Instrument→Concept | http://www.w3.org/ns/sosa/observes |
| `has_component` | Framework→Concept; Concept→Concept | http://purl.obolibrary.org/obo/BFO_0000051 (has_part; part-whole ONLY, never is-a) |
| `subtype_of` | Concept→Concept | http://www.w3.org/2000/01/rdf-schema#subClassOf (is-a ONLY, never part-whole) |
| `precedes` | Concept→Concept | http://purl.obolibrary.org/obo/BFO_0000063 |

No other edges. No new node types (Organization/Project explicitly rejected in audit — record in changelog). Parser/loader/tests updated for the new pairs.

## Part 2 — Promote the 91 staged items (curated events, no re-extraction)

Mapping table (proposed name → canonical), applied to the staged proposed_relationships:

- uses_measure → `uses_measure`
- measures, measures_concept, evaluates, assesses, operationalizes → `measures`
- has_component, has_category, categorizes, sub_level_of, part_of, decomposes → `has_component`
- subtype_of → `subtype_of`
- precedes → `precedes`
- Everything else (extends, builds_on, evolves_from, exemplifies, supports_standard, integrated_into, mapped_to, based_on_framework, adapted_from_prior_metric, risk_to, defined_in, administers, develops, assesses-org, participates_in, and the MLMU None→None items) → **remains staged**, untouched.

Promotion mechanics: each mapped item re-enters through the parser gate (pairing check + grounding validation against source) and is written as a curated_promotion event carrying: original staged item id, mapping applied, original grounding span, §4 provenance. Items with None endpoints or failing the gate stay staged with a reason. Report promoted/remaining counts by edge.

## Part 3 — Prompt hardening (pre-bulk)

One addition to the prompt template: grounding_span must be character-exact from the source text — no paraphrase, no normalization. Bump prompt template version; version stamped in extraction events (§4).

## Part 4 — Opus 4.8 re-baseline (2 docs)

1. model_config.yaml → claude-opus-4-8. Model-identity gate now pins Opus (any other envelope model_id → discard unparsed, STOP).
2. Re-extract Lawrence DRL and FCSM 25-03 under the v0.2 schema + hardened prompt. Write to a **re-baseline namespace/event batch clearly separated from pilot events** — these do not replace the Fable pilot extractions and are not ingested; they are comparison data.
3. Deliver docs/research/opus_rebaseline_comparison.md: side-by-side per doc (Fable pilot vs Opus re-baseline) — concepts/1k, defs, claims, edges, quarantine%, proposed count + names, spend. Facts only; the bulk go/no-go is the operator's.

## Acceptance

1. v0.2 committed, tests pass; 91-item promotion report; prompt version bumped; re-baseline comparison committed.
2. Zero API keys; Opus via claude -p subscription path; quarantine gate (10%) applies to the 2 re-baseline docs.
3. `seldon cc complete cc_tasks/2026-07-03_schema_v02_promotion_rebaseline.md`; `seldon verify` clean.

## Out of scope

Bulk extraction (next task, gated on the re-baseline comparison). Ingested transitions. Long-tail staged items.
