# RESULT — TrustGraph extraction benchmark (task `2026-08-23_trustgraph_benchmark`, Seldon b6900da4)

**Date:** 2026-08-23. **Repo:** ai-readiness-kg. **Model calls made:** 0. **`ANTHROPIC_API_KEY` set:** never. **Containers deployed:** 0.

## Phase table

| phase | status | record |
|---|---|---|
| 1 Deploy | **STOPPED — precondition blocker** (no live Google credential; task rule forbids substitution) | `docs/research/2026-08-23_tgbench_phase1_blocker.md` |
| 2 Ontology | **PARTIAL** — OWL generated + fidelity-checked; workbench load not run (nothing deployed) | `docs/research/2026-08-23_tgbench_ontology.md` |
| 3 Extract | NOT RUN (needs model) | — |
| 4 Normalize | NOT RUN (no Phase 3 output) | — |
| 5 Judge | NOT RUN; `2026-08-23_tgbench_decision.md` not written | — |
| 6 SHACL gate candidate | **DONE** — shapes, Neo4j-free RDF export, gate script behind `enabled: false`, mutation positive control, 9 tests | `docs/research/2026-08-23_tgbench_shacl_report.md` |
| 7 Close | **DONE minus teardown** (nothing to tear down); DD-018 appended; 2 Seldon results registered; commit left to the orchestrator | `docs/design_decisions.md` DD-018 |

## Decision rule verdict

**Not evaluable.** F_tg, C_tg, R do not exist. F_ours / C_ours from the probe are unchanged and uncompared. Neither Adopt-evaluate nor Harvest-components was reached by the rule; the 2026-08-22 chat-level rejection of TrustGraph stands **untested, not confirmed** (DD-018). Harvest-components is nevertheless partially realized because Phase 6 is unconditional: the SHACL piece is in.

## Numbers

| quantity | value |
|---|---|
| SHACL violations, current projection export | **2,127** (Seldon result b6c489e1) |
| … outside known classes | **0** (Seldon result badaa580) |
| known class `dangling_cites_endpoint_untyped` | 1,200 (1,178 distinct never-manifested targets) |
| known class `required_property_predates_schema` | 927 (Claims under schema 0.1/0.2 without `evidence_grade`) |
| export: documents / nodes / edges / triples | 134 / 9,018 / 12,224 / 112,423 |
| overlays applied: superseded dropped / aliased endpoints / annotations / relocated / nulled | 236 / 15 / 134 / 1,344 / 79 (relocated was 23 before the concurrent repair task's `batch-011` landed mid-run; violation counts invariant, see report) |
| OWL: classes / object props / datatype props | 12 / 23 / 33 (= schema 12 / 23 / 33) |
| SHACL: node shapes / pair legs / forbidden-edge legs / enums / required | 12 / 32 / 247 / 6 / 1 |
| deployment friction (containers, RAM, time-to-first-query) | not measured |
| tests | 156 passed (147 + 9 new), both `/opt/anaconda3/bin/python3` and default `python3` |

## Mutation-test record (positive control)

`scripts/run_shacl_gate.py --force --no-export --mutate` seeded one `defines` edge Concept→Concept (`…/advancing-american-ai-act-ndaa-fy2023-div-g/c-agency-inventory` → `…/c-ai`) into the in-memory copy of the export. Result: 2,128 violations, 2,127 known, **1 UNKNOWN** (`ConceptShape/defines`, `sh:MaxCountConstraintComponent`), `gate_fired: true`, exit 0 ("positive control OK"). Exit 3 is reserved for a control that fails to fire. Baseline without mutation: 0 unknown, not fired. Repeated on a synthetic 5-node graph in `tests/test_shacl_gate.py::test_mutation_positive_control_fires_gate`, plus wrong-target-class, enum, and post-0.3-missing-grade variants, all UNKNOWN as they must be.

## Discrepancies vs the task text

1. **Credential premise false.** "The existing Google AI Studio credentials" do not exist: revoked 2026-08-13 (S21 Part 1), documented in `~/.wintermute/.env` and the spend-incident decision. Live check found the *revoked* key still inherited in this process env (sha256 prefix `3ee221ca4626` = recorded revoked fingerprint) — a stale-env finding, not a credential; remedy is restarting the `claude` session.
2. **"~1,209 dangling cites"** in the task brief vs **1,200** here: the brief's figure is the Neo4j-view count, where bare-id MERGE and alias overlays shift it; the RDF export uses doc-scoped IRIs. Also recorded: Neo4j's projection fuses 600 same-id items across documents (`c_ai` etc.); not acted on (live graph out of scope).
3. **`gitignore nothing` honored.** `git check-ignore` returns nothing for `benchmarks/trustgraph/*`, `scripts/run_shacl_gate.py`, `tests/test_shacl_gate.py`; `.gitignore` untouched. `projection.ttl` is 8.2 MB and intended to be committed (artifacts are the point, per the task header).
4. **DD numbering.** DD-017 is reserved by the concurrent whole-graph-repair task (not yet written); this task appended DD-018 as instructed.
5. **Dependencies added** to the anaconda python only: rdflib 7.6.0, pyshacl 0.40.1. The stdlib-only test profile skips (not fails) `test_shacl_gate.py` if they are absent.
6. **Concurrent shard.** `events/batch-011.jsonl` (repair task) appeared during this run; re-validated with it: same 2,127 / 0. Not written by this task.
7. **Edge `grounding_span` not carried** in the RDF export (plain triples); irrelevant to type conformance, recorded in the report.

## Standing decisions

- DD-018: benchmark NOT EVALUATED; rejection of TrustGraph stands untested; exact re-run trigger = a new on-disk `GEMINI_API_KEY` with a declared spend cap and revocation path, then re-dispatch this task from Phase 1 reusing Phase 2/6 artifacts.
- `shacl_conformance` is a **candidate** gate: `dixie_evidence.yaml::shacl_gate.enabled: false`, threshold 0 unknown-class violations, two known classes matched by predicate. Enabling it and wiring it into `run_baseline_gates.py` is an operator decision.

## Files touched (all new except the two appends)

New: `benchmarks/trustgraph/{schema_to_owl.py, schema_to_shacl.py, export_projection_rdf.py, airkg_schema.ttl, airkg_shapes.ttl, projection.ttl}`, `scripts/run_shacl_gate.py`, `tests/test_shacl_gate.py`, `docs/research/2026-08-23_tgbench_{phase1_blocker,ontology,shacl_report}.md`, this file. Appended: `dixie_evidence.yaml` (`shacl_gate` section), `docs/design_decisions.md` (DD-018). Not touched: `events/`, `corpus/`, `kg/schema.yaml`, other `scripts/`, `.gitignore`, anything `2026-08-23_repair_*`. Not committed (orchestrator commits).

## Seldon

Results registered (state `proposed`): `b6c489e1-9e4c-4382-948c-643797bae4ed` = 2127 count (SHACL violations), `badaa580-2229-43da-b924-98543e4fe19d` = 0 count (unknown-class violations), both `--script-path scripts/run_shacl_gate.py`.
