# TrustGraph benchmark — Phase 2 ontology (task `2026-08-23_trustgraph_benchmark`)

**Date:** 2026-08-23. **Status:** deterministic half DONE; workbench load NOT RUN (nothing deployed, see `2026-08-23_tgbench_phase1_blocker.md`).

## Generator

`benchmarks/trustgraph/schema_to_owl.py` reads `kg/schema.yaml` (v0.3.2) and writes `benchmarks/trustgraph/airkg_schema.ttl`. Namespace `https://brockwebb.github.io/ai-readiness-kg/schema#`. Environment: `/opt/anaconda3/bin/python3` (3.x), **rdflib 7.6.0** and **pyshacl 0.40.1**, both installed into the anaconda python on 2026-08-23 (neither was present; `pip install rdflib pyshacl`).

Mapping: node type → `owl:Class` (`rdfs:comment` = `what`); each distinct property name → one `owl:DatatypeProperty`, `rdfs:domain` = declaring class or `owl:unionOf` the declaring classes, `rdfs:range xsd:string` except `is_platform_operator` → `xsd:boolean`; enum values noted as `rdfs:comment` on the property; edge type → `owl:ObjectProperty` (`rdfs:comment` = `meaning`), domain/range = union of the from-/to-types in the authoritative `pairs` list, `symmetric: true` → `owl:SymmetricProperty`, `external_alignment` → `rdfs:seeAlso` when it is an http(s) URI (all 11 are).

## Counts and fidelity check (re-parse of the emitted Turtle with rdflib)

| quantity | schema.yaml | airkg_schema.ttl |
|---|---|---|
| node types / named `owl:Class` | 12 | 12 |
| edge types / `owl:ObjectProperty` | 23 | 23 |
| distinct property names / `owl:DatatypeProperty` | 33 | 33 |
| triples | — | 439 |

The script asserts the first three equalities on every run and exits non-zero on mismatch; `tests/test_shacl_gate.py::test_owl_class_and_property_counts_match_schema` repeats the check in the suite.

## Recorded limitation

OWL domain/range cannot express the schema's strict index-pairing: `extends` is Definition→Definition **or** Framework→Framework, never Definition→Framework, but `rdfs:domain (Definition ∪ Framework)` / `rdfs:range (Definition ∪ Framework)` admits the cross product. The OWL is therefore a *looser* statement of the schema than the parser enforces. The exact pairs are stated in SHACL (`airkg_shapes.ttl`, Phase 6), which is the artifact that should gate anything. Had the workbench load run, the round-trip diff would be on class/property counts only and would not have detected this — the fidelity check, as specified, is blind to pair semantics; recorded so a future run does not over-read a clean diff.

## Not run

"Load via their ontology workbench/API. Fidelity check: round-trip export and diff class/property counts." — requires the Phase 1 deployment. Trigger to run it: same as the benchmark re-run trigger in DD-018.
