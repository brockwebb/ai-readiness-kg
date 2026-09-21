# RESULT: 2026-09-21_g4_resourcing_reissue

Resumed from the SIGTERMed session: its work was already committed as `4040bb5` (kept, not redone). Operator amendments applied: **decision 9 (checkpoint docs, DN-008, CLAUDE.md paragraph, audit) SKIPPED entirely, so no ResearchTasks come from it.**

## 0. Where each part stands
- **Part B (release date from the record):** done in `4040bb5`; `tests/test_g4_resourcing_reissue.py` guards it (two builds a day apart byte-identical and equal to the committed tree). Restored-date diff: `logs/g4r_partB_restore.diff`. Pages status: `logs/g4r_pages.json`.
- **Part A (G4 re-sourcing):** done in `4040bb5`. DCAT-AP 3.0.0 r5r admitted (fetch log `logs/2026-09-21_g4_resourcing_reissue_fetch.jsonl`), +7 evidenced_by edges (141 -> 148; edges 389 -> 396), zero drops, no `--force`. Issues filed this session (states `open`): (1) statutory-mandate clause has no defining source and RULE-G4-v1 measures the authority clause alone (`rule_g4.py` docstring says so); (2) the AI-ranker trust-signal clause is the framework's own inference and the statistical-versus-administrative clause has no DCAT-US class. Indicator text, tier and rule not edited. Issue ids are on the event log (`seldon issue list`).
- **Part C (grounding punctuation count):** `scripts/measure_grounding_punctuation.py`, read-only, 45.5 s measured, so no checkpoint machinery (§15 scope is >2 min or paid/networked). Output `logs/grounding_punctuation.json`.

## 1. Part C numbers (population: `events/raw/bulk_v1`, re-parsed by the live parser; 65 docs parsed, 7 skipped because no source binary is on disk)
| measure | value |
|---|---|
| grounding-miss quarantines (parser reason "grounding_span not found in source text") | 141 |
| flip to grounded under the fold | 4 (2.84%) |
| flips by single class | single_quote 2, double_quote 2 |
| flips by rendering | pypdf 4 |
| inverse control (500 grounded spans re-tested) | 0 lost |

All four flips sampled and inspected (only 4): three are genuine curly/straight quote differences; one is a source spacing quirk (`firms ' AI`) that grounds once a quote is folded. No false accept seen. Fold classes as decision 7; `normalize` untouched. Rate and denominator only, no recommendation. Results registered (proposed): `grounding_miss_population`, `grounding_punct_flips`, `grounding_punct_inverse_control_lost`; script Artifact link not made (no Script artifact exists), script named in each description.

## 2. Premises the task got wrong
- The task expected the fold to matter across the extraction gate; over bulk-v1 it moves 4 of 141 misses.
- Part A's rebuild ran against a graph whose KG layer was stale/partial after the interrupted session (published appendix showed `definitions: 0`); a full `build_projection.py` and a second report/PDF/site rebuild were needed. `docs/design/mcp_over_the_graph.md` is generated from the record's counts and had to be regenerated (`mcp/airkg_doc.py`); the guard allows that one path.
- The first `make gate-fast` here had 15 failures, all downstream of the un-rebuilt published views/stale projection plus my new guard not sourcing `check_protected_lib.sh`; each fixed at its cause.

## 3. Gate (tier: full, `make gate-full`, includes the slow tier)
| gate | result | log |
|---|---|---|
| suite | 2775 passed, 3 skipped, 12 xfailed, 0 deselected, 2171.56 s, EXIT=0 | `logs/suite.log` |
| first fast tier (before fixes, for the record) | 15 failed, 2733 passed, 3 skipped, 27 deselected, 12 xfailed, 583 s | `logs/g4r_gate_fast.log` |
| seldon verify | All checks passed, exit 0 | `logs/g4r_seldon_verify.log` |
| protected paths | PROTECTED PATHS OK (`scripts/check_protected_g4_resourcing_reissue.sh`) | `logs/g4r_protected.log` |
| full projection | EXIT=0 | `logs/g4r_full_projection.log` |
