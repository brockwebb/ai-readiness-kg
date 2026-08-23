# TrustGraph benchmark — Phase 6 SHACL conformance report (task `2026-08-23_trustgraph_benchmark`)

**Date:** 2026-08-23. **Status:** DONE (unconditional phase). Tooling: rdflib 7.6.0, pyshacl 0.40.1 under `/opt/anaconda3/bin/python3`; no model calls, no Neo4j, no docker.

## Artifacts

| file | role |
|---|---|
| `benchmarks/trustgraph/schema_to_shacl.py` → `airkg_shapes.ttl` | one `sh:NodeShape` per node type (12); per class, every edge type gets a property shape: legal pairs → `sh:class` (`sh:or` when several targets; 32 legs = 32 schema pairs), illegal → `sh:maxCount 0` (247 legs). Enum properties → `sh:in` (6); `required_properties` → `sh:minCount 1` (1: `Claim.evidence_grade`); `is_platform_operator` → `sh:datatype xsd:boolean`. 1,249 triples. The `maxCount 0` leg is what closes the shape set over the edge whitelist, the way the parser is closed; without it a bad-SOURCE edge would pass silently. |
| `benchmarks/trustgraph/export_projection_rdf.py` → `projection.ttl` | event log → RDF, no Neo4j. Imports `read_overlays`, `is_projectable`, `annotation_update`, `NULLABLE_ATTRIBUTES`, `_scalar_props` from `scripts/build_projection.py` so the two projections share one definition of "projectable". Applies: `extraction_superseded` (236 events dropped), `edge_endpoint_alias` (15 endpoints rewritten), `document_annotation` (134), `grounding_relocated` (23) and `attribute_nulled` (79) last, `NON_GRAPH_PURPOSES` (0 in untagged shards; `eventlog.replay()` already excludes tagged shards). |
| `scripts/run_shacl_gate.py` | the gate candidate: export → validate → classify → count unknown-class violations → compare to threshold; `--mutate` positive control; `--force` to evaluate while `enabled: false`. |
| `dixie_evidence.yaml::shacl_gate` | `enabled: false`, `shapes`, `known_violation_classes` (2), `threshold_unknown_violations: 0`. |
| `tests/test_shacl_gate.py` | 9 tests (generator counts vs schema; positive control, wrong-target, enum, post-0.3 missing grade on a tiny synthetic graph; committed config sanity). |

## Export counts (2026-08-23, replay of `events/batch-001..010` untagged)

documents 134 distinct (135 `manifest_add` events), nodes 9,018, edges 12,224, triples 109,794. By type: Concept 4,675 · Claim 1,495 · Definition 900 · Measure 523 · Standard 425 · Practice 336 · Framework 252 · Instrument 154 · Document 134 · Tool 100 · Platform 98 · Construct 0.

**IRI scheme departs from the Neo4j projection, deliberately.** Extracted item ids are doc-scoped — 600 of 6,988 distinct ids recur across documents (e.g. `c_ai`) — so a node IRI is `…/doc/<doc_id>/<item_id>`. `build_projection.py` MERGEs on bare `id` and therefore fuses same-id items from different documents into one Neo4j node. That fusion is an existing property of the Neo4j view, not of the event log; this export does not reproduce it. Recorded as a finding for the Neo4j projection, not acted on here (out of scope: touching the live graph).


**Snapshot note.** The concurrent `2026-08-23_whole_graph_repair` task appended `events/batch-011.jsonl` (1,321 `grounding_relocated` + 5 `span_unrepairable`) at 12:45–12:48Z, after the first export. Re-run with it present: overlays_relocated 23 → 1,344, triples 109,794 → 112,423, violations unchanged at 2,127 / 0 unknown — relocations change spans, not types, so the conformance result is invariant to that shard. The committed `projection.ttl` is the later export (includes batch-011 as of 1,326 lines); `span_unrepairable` is not a projected event type and is ignored by both projections.

## Validation result

**Conforms: NO.** Violations: **2,127** total, **0 outside the known classes.**

| shape / constraint / predicate | count | class | verdict |
|---|---|---|---|
| `DocumentShape/cites` · `sh:ClassConstraintComponent` · `airkg:cites` | 1,200 | `dangling_cites_endpoint_untyped` | KNOWN |
| `ClaimShape/evidence_grade` · `sh:MinCountConstraintComponent` · `airkg:evidence_grade` | 927 | `required_property_predates_schema` | KNOWN |

Examples (3 each):

- dangling cites — focus `doc/venkit-2025-deeptrace` → value `doc/reiter-2025-real-world-impact`; same focus → `doc/liu-2023-verifiability`; same focus → `doc/hopcroft-karp-1973`. 1,178 distinct never-manifested targets. This is the population the bulk-v1 closeout's `edge_endpoint_validation` gate records as a FAIL finding; the task text's "~1,209" is that gate's count on the Neo4j view, where id-merging and the 9 alias overlays shift the figure slightly (1,200 here, after 15 alias rewrites).
- pre-0.3 Claims without `evidence_grade` — `doc/aidrin-hiniduma-2024/cl-bias-discriminatory-outcomes`, `doc/ai-governance-ethics-and-leadership-substack-harvey-lab-lega/cl_win`, `doc/why-ai-readiness-is-an-organizational-learning-problem-not-a/cl_702010`. Profile of the log: Claims by (prov_schema_version, has grade) = (0.1, no) 99 · (0.2, no) 861 · (0.3, yes) 568; after supersession drops, 927 pre-0.3 Claims remain. Schema v0.3 made the attribute required *"on every Claim extracted under 0.3"* (DD-010); these predate it. The shape states the schema unconditionally; the exemption is a classifier predicate on `prov_schema_version ∈ {0.1, 0.2}`, so a **0.3** Claim without a grade is still UNKNOWN (`test_post_03_claim_without_grade_is_unknown`).

Known classes are matched by predicate (shape + constraint + a property of the focus or value node), never by count, so a drift inside a known shape still surfaces.

## Mutation test — positive control (run record)

```
$ /opt/anaconda3/bin/python3 scripts/run_shacl_gate.py --force --no-export --mutate
positive control seeded: {"edge": "defines",
  "from": ".../doc/advancing-american-ai-act-ndaa-fy2023-div-g/c-agency-inventory",
  "to":   ".../doc/advancing-american-ai-act-ndaa-fy2023-div-g/c-ai",
  "from_type": "Concept", "to_type": "Concept"}
violations_total 2128 · known 2127 · UNKNOWN 1 · gate_fired true
     1  ConceptShape/defines  MaxCountConstraintComponent  defines  -> UNKNOWN
positive control OK: gate fired on the seeded edge        (exit 0; exit 3 had it not fired)
```

The mutation is applied to the in-memory graph only; `projection.ttl` on disk is untouched. Baseline run without `--mutate`: unknown 0, `gate_fired false`, exit 0. With `enabled: false` and no `--force`: prints "disabled", exit 0 — the gate is wired and inert, as the task specified.

## Proposal

Promote `shacl_conformance` to a pre-registered gate once the operator sets `enabled: true` and `scripts/run_baseline_gates.py` calls it. Threshold `threshold_unknown_violations: 0` is the only tunable and is an operator decision. What it adds over the existing parser checks: the parser validates each extraction at write time against the schema *it was written under*; this gate validates the *replayed, overlaid* graph against the *current* schema, so schema bumps, overlay bugs, and cross-shard inconsistencies are visible after the fact. What it does not do: carry edge-level `grounding_span` (plain triples have no slot; reification was not needed for a type-conformance check) or reproduce Neo4j's id-merging.
