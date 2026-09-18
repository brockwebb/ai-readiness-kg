# RESULT: four schema.org and robots field rules pre-registered before cycle 5; B2, B5 and D2 are `harness_leg`, B1 reads both halves, and no `structured_field` row remains

**Task:** `cc_tasks/2026-09-18_schema_field_rules.md`. I globbed `2026-09-18_schema_field_rules_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher from HEAD `d49a001`. It ran after `2026-09-18_dcat_field_rules.md` (commit `0827806`), as the SEQUENCING line requires.
**Framework layer served:** DN-005 §2.2.
**Spend:** zero model calls. **Network:** none beyond `git push`. No host was contacted. The rules were exercised on fixtures and on evidence already retained under `state/` and `corpus/evidence/scan/`.
**Gate:** green. Every command in §4 ran to its `EXIT=` line before this file was written.
- `make gate-full`: **2522 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`, 1392.98 s.
- `make gate-task`: fast tier **2497 passed, 3 skipped, 12 xfailed, 25 deselected**, 487.47 s. Re-derivation: **22 passed, 0 skipped, 0 xfailed, 25 deselected**. `EXIT=0`.
- `seldon verify`: all checks passed, `EXIT=0`.
- `scripts/check_protected_sd_rules.sh`: `PROTECTED PATHS OK`, `EXIT=0`.

**In one paragraph.** Generation 12 adds four modules: `RULE-B1-v2`, `RULE-B2-v1`, `RULE-B5-v1` and `RULE-D2-v1`. All four are in `rules.CURRENT` and the registry.
- `RULE-B1-v1` remains in `REGISTRY` and was not edited.
- B1-v2, B2 and B5 read the markup that A6 already extracts. Every stored A6 Observation keeps `parsed.raw`, so these rules needed no new collector.
- D2 reads a `Content-Signal` block. The runner parses that block from A4's robots.txt body at collection time.
- B5 is the first rule judged per **body** rather than per surface (`SCOPE = "body"`). `rules.body_groups` builds its group, and both `run.judge_bodies` and `rederive.py` use that one function.

Nine failing outcomes each have a fixture and an action. On the retained evidence of the cycle of record the rules judge deterministically, and none of them passes on any body (§1, unpublished).

The record moved through the single writer in four events. B2, B5 and D2 are now `harness_leg` / `harness_built`, and B1 is on v2. **The record carries 24 `harness_leg` rows and 0 `structured_field` rows.**

No cycle was run and no matrix, figure or report was rebuilt. Nothing under `state/`, `corpus/` or `docs/reports/` changed.

## 0. The four rules

| rule | reads (`CONSUMES`) | subject (`MEASURES` / `SCOPE`) | passes when | failing outcomes → stable fragment | recorded as unmeasured |
|---|---|---|---|---|---|
| `RULE-B1-v2` | D4, A6 | product / surface | **either** half passes: every catalog record for the product links `describedBy` (v1's reading, same sentences), **or** a schema.org `Dataset` on the page lists `variableMeasured` | v1's `no_product_record`, `no_data_dictionary`; new `no_variable_measured` → "no \`variableMeasured\`". A fail carries both halves' fragments, so both actions apply | the contents of the dictionary or variable list, and whether they are "comprehensive" |
| `RULE-B2-v1` | A6 | product / surface | at least one `DefinedTerm` is reachable from a `Dataset`, and every such term carries `termCode`, `inDefinedTermSet` and `description` | `no_defined_terms` → "no schema.org \`DefinedTerm\` in the product page's markup"; `terms_not_linked` → "the terms are not linked from the "; `terms_incomplete` → "lack a \`termCode\`, an \`inDefinedTermSet\` or a " | "versioned": no admitted document names a version property |
| `RULE-B5-v1` | A6 (every product surface of the body) | **host / body**; target `host:<netloc>` | every concept (a term's name, case-folded) coded on ≥2 products carries one (`inDefinedTermSet`, `termCode`) | `no_term_codes` → "no term codes: none of the body's "; `codes_without_set` → "codes without a set: "; `codes_not_shared_across_products` → "codes not shared across products: " | cross-vintage half, `UNMEASURED_UNTIL = "second cycle with term codes"`, on the module and in `ind:B5.tier_note` |
| `RULE-D2-v1` | A4 | product path / surface | a `Content-Signal` that applies to the product path declares **both** `ai-train` and `ai-input` (yes or no) and names only defined categories and values | `no_content_signal` → "declares no Content-Signal for "; `unknown_category` → "a category or value the Content Signals Policy does not define" | the prose terms of use (still a judged reading), and enforcement (A12's question) |

Every rule declares `CLAIM = "absence"`, and every rule calls `_common.unobserved_error` on each probe it scores on.

**How the rules handle blind or unread evidence:**
- **B1-v2** returns `error` when a half that has not passed is blind or unread, because the absence claim covers both surfaces.
- **B5** has two cases. When every product surface is blind, it returns `error`. When some surfaces are blind and none carries codes, it takes the `_common.absence_verdict` route, which also returns `error` and records `blind_candidates`.
- **D2** returns `error` on an A4 Observation that has no `content_signal` block. That applies to every stored cycle.

**How the rules are grounded:**
- The schema.org terms are quoted from `schema-org-definedterm` and `schema-org-dataset`.
- The Content-Signal grammar, including path-scoped directives, comes from the examples in `cloudflare-content-signals-policy`.
- D2's requirement that both uses be declared comes from that document's clause (c): "If the website operator does not include a content signal for a corresponding use, the website operator neither grants nor restricts permission".
- `_schema_terms.py` reads JSON-LD, microdata and expanded RDFa. It treats a property as schema.org only when the name is bare or carries a schema.org prefix, and it follows `@id` references.

**Fixture results** (`tests/test_schema_field_rules.py`, 30 tests, all passing inside the gate):
- **Pass fixtures:** one per rule. They include B2 over expanded RDFa, B5 matching names regardless of case and spacing, D2 with a path-scoped directive, and B1 passing on either half.
- **One fixture per failing outcome:** nine in all. Each fixture's reason contains its `tag_prescriptions.OUTCOMES` fragment, and the test asserts that the fixture set equals the outcome set.
- **B1-v2 edge cases:**
  - It passes on the catalog when the page is blind.
  - It returns `error` when the unpassed half is blind.
  - On a non-HTML surface it takes the catalog half's verdict.
- **B5 edge cases:**
  - A single product, or products that share no concept, give `not_applicable`.
  - "No codes" with one blind surface gives `error`.
  - `body_groups` takes the product surfaces of one host only. It excludes `home:`, the well-known row, control fixtures and other legs.
- **B5 through the runner:** a B5 Finding made by `run.judge_bodies` re-derives byte-identically through `rederive.rederive`.
- **D2 edge cases:**
  - The parser reproduces the policy page's own examples.
  - An Observation stored before the block existed gives `error`.
  - One undeclared use gives `fail`.
- **Determinism:** two runs over the same bytes give the same Finding ids for every fixture.
- **The real control page:** `passes_all`'s actual `index.html`, run through `extruct`, passes B1 and B2. Its robots.txt, and the three fixture robots.txt files carrying the new line, pass D2.

**Control fixtures.** The expectations were derived from the rule source and written into `params.yaml:e5_control` before the controls ran (the comment is there).
- **B1 and B2** take every fixture's default verdict.
- **D2** departs from the default exactly where A4 does. That gives two new rows: `refuses_identified_client: D2: pass` (its declared layer is served with the signal) and `robots_404_html: D2: fail`.
- **B5** is in no control row: no fixture is a body with two products (see §3 premise 4).

The slow control tier ran green before the gate (`logs/sd_controls.log`: **25 passed, 0 skipped, 0 xfailed, 2512 deselected**, `EXIT=0`) and again inside `gate-full`.

## 1. Retained evidence of the cycle of record: **UNPUBLISHED**

**What was run.** `scripts/exercise_schema_field_rules.py` (log `logs/sd_exercise.log`, `EXIT=0`).
- The cycle of record is `scan_2026-09-10_rj2`. Its Observations are `scan_2026-09-10`'s.
- The script read the 46 tier-A, non-well-known surfaces.
- It attached D4's `dcat_fields` block and A4's `content_signal` block offline, from the stored bodies. That is exactly what `runner.collect_leg` now does at collection time.
- It judged every rule twice. Missing robots bodies: 0. Missing catalog bodies: 0. Deterministic: `true`.

**What was not done.** Nothing here entered a matrix, a figure, a Result or the report.

| leg | subject | pass | fail | not_applicable | error | fail outcomes |
|---|---|---|---|---|---|---|
| B1 (v2) | 46 surfaces | 0 | 37 | 0 | 9 | `no_product_record` 34, `no_data_dictionary` 3, `no_variable_measured` 37 (on the same fails, one reason carries both halves) |
| B2 | 46 surfaces | 0 | 38 | 0 | 8 | `no_defined_terms` 38 |
| D2 | 46 surfaces | 0 | 40 | 0 | 6 | `no_content_signal` 40 |
| B5 | 16 bodies | 0 | 12 | 0 | 4 | `no_term_codes` 12 |

**Absence everywhere, measured.** The rule ships anyway under decision 2 of the DCAT task.
- **`DefinedTerm`:** not one retained product page carries one.
- **`variableMeasured`:** not one carries it either. The only schema.org `Dataset` on the frame is the Federal Reserve SCF page, and it carries neither.
- **`Content-Signal`:** not one host's robots.txt carries the directive.
- **B5's four errors:**
  - BLS, BTS and ORES: every product surface is `refused`.
  - EIA: one of its two product surfaces is `robots_disallowed`. With nothing found on the other, the scope limitation owes `error`.
- **B5 targets.** B5's targets are exactly the frame's 16 `host:<netloc>` rows, so every body Finding lands on an existing matrix row. `body_findings_without_a_row` would be empty.

## 2. The record write

Every change went through `framework_writeback.save`. The four events are all on `events/batch-033_framework.jsonl`, and every one names this task.

| event | time (UTC) | script | delta | framework sha256 |
|---|---|---|---|---|
| `4fe65ce3d528453e98c553e6c2e60222` | 06:14:48 | `build_measurement_specs.py --add-missing --refresh B1` | +3 `MeasurementSpec` (`spec:B2`, `spec:B5`, `spec:D2`), +3 `MEASURED_BY`; `spec:B1`'s authored fields refreshed to both halves, with its `rule_id` kept; measurement_specs 26→29 | `fc1b941b…52dbec` |
| `1fe93c5fc5344cafb337c835bdc92956` | 06:14:48 | `framework_writeback_rules.py` | `spec:B1` → `RULE-B1-v2`; `spec:B2/B5/D2` → `RULE-*-v1`; B2, B5, D2 `specified` → `harness_built`; rules_built 21→24 | `32e3c8da…86a07c` |
| `f73abae40b044e9494e55dd3327ced0a` | 06:14:54 | `tag_measurement_tiers` | B2, B5, D2 `structured_field` → `harness_leg` (rule 1, `tier_source` cites the rule id, `tier_field`/`tier_collector` leave the node); B1's `tier_source` cites `RULE-B1-v2` and its `tier_note` describes both halves | `af3bb42d…599649` |
| `3c3301de6a224b51b1bcc5ab4ab87426` | 06:14:55 | `tag_prescriptions` | +9 `Action`, +9 `REMEDIATES`. B1's two generation-11 actions now `verifies_by: RULE-B1-v2`, and their per-leg caveat counts 3 outcomes. Actions 51→60 (63 `Action` nodes including the 3 on the candidate A12) | `680aa4e9…cb1746` |

**Actions added** (all `authored_by` this task):

| class | actions |
|---|---|
| `edit_existing` (7) | `b1-list-the-variables-measured-in-the-page-markup`; `b2-publish-concept-definitions-as-defined-terms`; `b2-link-defined-terms-from-the-variables`; `b2-give-each-defined-term-a-code-set-and-definition`; `b5-name-the-set-each-term-code-belongs-to`; `d2-declare-ai-training-and-input-terms-in-robots-txt`; `d2-use-only-the-defined-content-signal-categories` |
| `publish_new_file` (2) | `b5-code-the-bodys-concepts-in-one-term-set` and `b5-use-one-identifier-per-concept`. Each carries a `technique_class_reason`: the act is a term set the body does not yet publish |

Every technique source is a verbatim quote, checked by the tagger, from one of four documents:
- `schema-org-dataset`
- `schema-org-definedterm`
- `cloudflare-content-signals-policy`
- `w3c-dwbp-2017`, Best Practice 15: "referring to codes and terms from standards helps to avoid ambiguity and clashes between similar elements or values."

### 1a. The state of the record after both tasks

- **`harness_leg`: 24.** It was 17 before the DCAT task, 21 after it, and is 24 now.
- **`structured_field`: 0** (expected 0). The seven rows the unassigned-indicators task named (B1, B2, B4, B5, D2, D3, G4) are all `harness_leg`.
- **Tiers:** 36 M / 5 O / 5 D, with 3 unassigned (B6, G3, G5). These are unchanged, because B2, B5 and D2 were already tier M.
- **`measurement_status`:** 16 measured, 8 harness_built, 25 specified.
- **Live Cypher after projection** (`projection_gate: green`) agrees row for row: `M harness_leg 24 [… B1 B2 B5 D2 …]`, `M judged_reading 4`, `M evaluation 8`, `O open_tool 5`, `D declaration 5`, `null 3 [G3 G5 B6]`.
  - The projection is `logs/sd_projection.log`, `EXIT=0`, `harness_leg_indicators_without_an_action: []`.

**Cycle 5 on 2026-10-05 is the first judgement of all seven structured-field rules:** `RULE-B1-v2`, `RULE-B2-v1`, `RULE-B4-v1`, `RULE-B5-v1`, `RULE-D2-v1`, `RULE-D3-v1` and `RULE-G4-v1`.

**Idempotence.** Every writer is a no-op over the new record: `build_framework_graph`, `tag_prescriptions`, `framework_writeback_rules` and `build_measurement_specs --add-missing --refresh B1`. The protected-paths script asserts all four.

**Regenerated views.**
- `docs/design/scan_tool_map.md`: `specified` 28 → 25. `structured_data` now serves B1, B2 and B5, `robots` serves D2, and `v2clauses` serves A4 and D2.
- `docs/design/scoring_model.md`: 23 adopted harness legs, 14 scored on the cycle of record. B2, B5 and D2 are "not a leg of any published matrix".
- `docs/design/mcp_over_the_graph.md`.
- `docs/data/ai_readiness_framework.json` and `docs/data/index.json`, via `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest` (log `logs/sd_site.log`, `EXIT=0`). `sources_per_check.json` did not change.

## 3. Premises the task file got wrong

1. **"Its subject is the body … its evidence is the set of `DefinedTerm` codes across the body's products on one cycle."**
   - **What was missing.** The harness had no place where a rule could see more than one surface. `run_surface` and both `rederive` loops group by `(surface, leg)`.
   - **What was added:**
     - `rules.scope` and `SCOPE = "body"` on the module.
     - `rules.BODY_LEGS`.
     - `rules.body_groups`. It is pure. It groups by the host of the observed product surfaces and excludes controls and the `home:`/`host:` rows (`params.b5_consistency`).
     - `run.judge_bodies`, which runs after every surface of a cycle is collected and records each verdict on the body's well-known row.
     - Body passes in `rederive.rederive` and `rederive.rejudge`, which skip body rules in their per-surface loops.
   - **What the regrouping would otherwise have broken.** Without the skip, re-derivation would have minted one extra B5 Finding for every product surface.
   - **The decision behind "body".** The body is read as its host. On the frame, every tier-A body has exactly one host and one `host:<netloc>` row (`state/scan_targets_fss_2026-09_v5.json`), so the two coincide. A body whose products sat on two hosts would be judged once per host, and the target says which.
2. **"The last three `structured_field` rows", read as needing only rule modules.**
   - **D2 needs a collector.** `protego` ignores `Content-Signal`. I added `v2clauses.content_signals`, the runner attaches it to A4's Observation, and there is a `params.content_signal` block.
   - **All three need specs.** B2, B5 and D2 each needed a `MeasurementSpec`, because a leg without one is never judged. That is the same gap the DCAT task found (its premise 2).
   - **`spec:B1` needed an edit.** It described the DCAT half only. `build_measurement_specs.py` gained `--refresh LEG`, which rewrites a spec's authored fields and keeps its written-back `rule_id` and `decision`. It refuses to run without `--add-missing`.
3. **Decision 6: "present with a category the corpus document names → pass".**
   - **The literal reading was too loose.** It would pass `Content-Signal: search=yes`, which says nothing about the two uses the indicator names.
   - **What the rule requires instead.** Both `ai-train` and `ai-input` must be declared, on the policy's own clause (c) quoted in §0. A directive that addresses neither use, or only one, fails as `no_content_signal`.
   - **The outcome set did not change.** The two outcomes are exactly the two the decision names. An operator who wants "any named category" instead can have it as a `v2`.
4. **The DCAT precedent assumes every framework leg is judged in the control cycle. B5 cannot be.**
   - Each control fixture is served on its own port, so none is a body with two products, and `CONTROL_LEGS` excludes body legs.
   - B5's fixtures therefore live in `tests/test_schema_field_rules.py`, including a run→re-derive round trip.
   - This is a real gap in E5's coverage for one leg. A two-product control fixture would close it, and it is named as open work below.
5. **"`RULE-B1-v2` … joins B1's rule" leaves the combining rule unstated.**
   - **The decision.** Either half passes the leg. The two are vocabularies for one property (DCAT-US for the catalog, schema.org for the page), and the indicator asks whether the metadata reaches a consumer, not in which vocabulary.
   - **The stricter alternative.** Requiring both halves would fail a body for publishing in only one format, and no admitted document asks for that.
6. **Files the write set omits, each forced by the moves above:**
   - `run.py`, `rederive.py`, `runner.py`, `v2clauses.py`, `params.yaml`, and `rules/_schema_terms.py`.
   - Four fixture files: `passes_all/index.html`, and the robots.txt of `passes_all`, `refuses_identified_client`, `robots_forbids_product` and `sitemap_on_sibling`. Without them the passing controls could not pass the new legs.
   - `scripts/exercise_dcat_field_rules.py`. It judged by `CURRENT`, which silently turned B1 into v2 (46 errors). It now pins the generation-11 ids, so it still reproduces the DCAT RESULT §1.
   - Nine tests whose literals moved, each with its reason beside the new value:
     - `test_scan_harness`: 23 legs.
     - `test_scan_harness_v3`: `SHARED_LEGS` gains A4 and A6.
     - `test_invariants`: B5 joins A12 as a declared host subject, citing decision 5.
     - `test_rule_a12_v3`: four more `unobserved_error` callers, and D2's `robots_404_html` row.
     - `test_dcat_field_rules`: B1 is `CURRENT` at v2, and the page is fetched once.
     - `test_measurement_tiers`, `test_prescriptions`, `test_mcp_server`, `test_framework_projection_roundtrip` and `test_framework_single_writer`: counts.
7. **§0: "Field locators are on the nodes".** As the DCAT task found, `tier_field`/`tier_collector` leave a node when it becomes `harness_leg`. The locators now live in three places: the rule module docstrings, the spec `signal`s, and the `tier_note`s.

**Open, for the next task, not done here:**
- a two-product control fixture for B5;
- D4's substring membership question, left open by the DCAT RESULT §1.

## 4. Gate

**Tier:** `make gate-full`, the full suite, detached and polled to `EXIT=`. `make gate-task` was run as well, because rule modules, the registry and the re-derivation engine all changed.

| check | result | log |
|---|---|---|
| `make gate-full` | **2522 passed, 3 skipped, 12 xfailed, 0 deselected**, 251 warnings, 1392.98 s, `EXIT=0` | `logs/suite.log` |
| skips (3, as expected) | `tests/test_dispatch_config.py:333` (interactive_only, dispatched session); `tests/test_scan_harness.py:283` (E5 judges the cycle, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | `logs/suite.log` |
| `make gate-task` | fast: **2497 passed, 3 skipped, 12 xfailed, 25 deselected**, 487.47 s; re-derivation: **22 passed, 0 skipped, 0 xfailed, 25 deselected**, 8.81 s; `EXIT=0` | `logs/sd_gate_task.log` |
| slow tier, run first | **25 passed, 0 skipped, 0 xfailed, 2512 deselected**, 907.35 s, `EXIT=0` | `logs/sd_controls.log` |
| `seldon verify` | all checks passed (replay skipped as expensive, its default), `EXIT=0` | `logs/sd_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` | `logs/sd_protected.log` |
| projection | `load_framework_graph.py` `EXIT=0`; the round-trip gate is green inside the suite; live Cypher agrees (§1a) | `logs/sd_projection.log` |
| retained evidence (§1) | `EXIT=0`, deterministic, 0 bodies missing | `logs/sd_exercise.log` |

**Two earlier fast-tier probes on the same tree failed 24 tests** (`logs/sd_fast_probe.log`, `logs/sd_fast_probe2.log`). Every failure was a literal this task moves (§3 premise 6), or one of the DCAT tests that assumed B1's CURRENT rule was v1. No gate or threshold was moved. `params.yaml:e5_control` gained two derived D2 rows and the comment deriving them.

**Write set as committed:**
- **Rules:** the four rule modules, `_schema_terms.py` and `rules/__init__.py` (V12, `scope`, `BODY_LEGS`, `body_groups`).
- **Harness:** `collectors/v2clauses.py`, `runner.py`, `run.py`, `rederive.py` and `params.yaml`.
- **Fixtures:** the five fixture files.
- **Record:** the record and its four events.
- **`scripts/`:** `tag_prescriptions.py`, `tag_measurement_tiers.py`, `build_measurement_specs.py`, `exercise_schema_field_rules.py`, `exercise_dcat_field_rules.py` and `check_protected_sd_rules.sh`.
- **Tests:** `tests/test_schema_field_rules.py` plus the moved literals.
- **Regenerated views:** `docs/design/{scan_tool_map,scoring_model,mcp_over_the_graph}.md` and `docs/data/{ai_readiness_framework,index}.json`.
- `seldon_events.jsonl`.
- This RESULT.
