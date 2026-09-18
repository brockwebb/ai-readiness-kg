# RESULT: four DCAT-US field rules pre-registered before cycle 5; B1, B4, D3 and G4 are `harness_leg`, E1 and E3 are M `judged_reading`, D3's gap cell is corrected

**Task:** `cc_tasks/2026-09-18_dcat_field_rules.md`. I globbed `2026-09-18_dcat_field_rules_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher (ResearchTask `f30ea93d`) from HEAD `4808f05`.
**Framework layer served:** DN-005 §2.2. Four rows move from `structured_field` to `harness_leg` ahead of cycle 5 (2026-10-05).
**Spend:** zero model calls. **Network:** none beyond `git push`. No host was contacted. The rules were exercised on fixtures and on catalog bodies already retained under `corpus/evidence/scan/`.
**Gate:** green. Every command below ran to its `EXIT=` line before this file was written.
- `make gate-full` (the full tier, `-rs`): **2486 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`, 1368.91 s.
- `make gate-task` (fast tier plus re-derivation of every stored payload): fast tier **2461 passed, 3 skipped, 12 xfailed, 25 deselected**, 481.03 s. `-k re_derives` gave **22 passed, 0 skipped, 0 xfailed, 25 deselected**, 7.98 s. `EXIT=0`.
- `seldon verify`: all checks passed, `EXIT=0`.
- `scripts/check_protected_dcat_rules.sh`: `PROTECTED PATHS OK`, `EXIT=0`.

**In one paragraph.** Four first-version rules make up generation 11: `RULE-B1-v1` (B1's DCAT half), `RULE-B4-v1`, `RULE-D3-v1` and `RULE-G4-v1`. They are in `rules.CURRENT` and the registry. Each declares `CONSUMES = ("D4",)`, `CLAIM = "absence"` and `MEASURES = "product"`, and reads a new `dcat_fields` block that the collector puts on D4's catalog Observation. Every host is still asked for `/data.json` once per surface. Nine failing outcomes each got a fixture and an action. On the retained catalogs of the cycle of record the rules judge deterministically; the verdict distribution is unpublished (§1). The record moved through the single writer in five events. The four rows became `harness_leg` / `harness_built`, E1 and E3 took M `judged_reading`, D3's stale gap cell was corrected at its authored source, and four MeasurementSpecs and nine Actions were added. **No cycle was run, no matrix, figure or report was rebuilt, and nothing under `state/`, `corpus/` or `docs/reports/` moved.** The task's write set was too narrow in seven places (§3). Each widening is asserted by the protected-paths script.

## 0. The four rules

Shared shape (`assessment/harness/scan/rules/_dcat_fields.py`, pure):
- **Subject.** The product's catalog record, using D4's own membership test (`product_url in json.dumps(dataset)`).
- **Clauses.** Declared in `params.yaml:dcat_fields.clauses`. A rule passes only when every catalog record for the product satisfies every clause.
- **Unmeasured clauses.** Each module declares them in `UNMEASURED`, and every pass and fail verdict prints them.
- **Branches and verdicts:**

| branch | verdict |
|---|---|
| empty | `error` |
| all probes blind | `error` |
| no catalog, with a blind probe | `error` (`absence_verdict`, ISA 705 scope limitation) |
| no catalog served | `fail` |
| catalog stored before `dcat_fields` existed | `error` |
| catalog does not parse | `fail` |
| product not in catalog | `fail` |
| records | per clause |

| rule | field(s), cited on the module | failing outcomes → stable fragment | recorded as unmeasured |
|---|---|---|---|
| `RULE-B1-v1` | `describedBy` on the dataset or on a distribution (`dcat-us-1-1-schema`) | `no_product_record` → "no catalog record for the product"; `no_data_dictionary` → "lack a data dictionary (" | the dictionary's contents and "comprehensive"; the schema.org half belongs to `2026-09-18_schema_field_rules.md` |
| `RULE-B4-v1` | `hasQualityMeasurement`; `versionNotes` / `previousVersion` / `hasCurrentVersion` (`dcat-us-3-dataset-schema`) | `no_product_record`; `quality_measurement_absent` → "lack a quality measurement ("; `revision_metadata_absent` → "lack revision metadata (" | the suppression-rules clause |
| `RULE-D3-v1` | `wasGeneratedBy`, `wasDerivedFrom`, bare or `prov:` (`dcat-us-3-dataset-schema`, `w3c-dcat-3`, `w3c-prov-o-ontology`); `qualifiedAttribution` is reported, not required | `no_product_record`; `no_lineage_field` → "lack a lineage field (" | whether the lineage reaches from collection to product |
| `RULE-G4-v1` | `bureauCode` `^[0-9]{3}:[0-9]{2}$` **and** `programCode` `^[0-9]{3}:[0-9]{3}$`, the formats `dcat-us-1-1-schema` states | `no_product_record`; `authority_codes_absent` → "lack a valid \`bureauCode\` and \`programCode\`" | the statutory mandate; statistical-versus-administrative provenance |

**Fixture results** (`tests/test_dcat_field_rules.py`, 20 tests, all passing inside the gate):
- A record carrying every field passes all four rules.
- Every alternative field satisfies its clause: dataset-level `describedBy`; each of the three revision fields; each of the three other lineage keys.
- **One fixture per failing outcome, nine in all.** Each fails, and each reason contains that outcome's `tag_prescriptions.OUTCOMES` fragment. The test also asserts that the fixture set equals the outcome set.
- The three no-record states (no catalog, unparseable catalog, product absent) all reach `no_product_record`.
- B4 names both clauses when both are missing.
- G4 fails on a missing code and on a malformed one.
- A blind catalog gives `error`.
- **A D4 Observation without `dcat_fields` gives `error`, never `fail`.** Every stored cycle is in that state.
- **Determinism:** two runs over the same bytes give the same Finding ids, for every fixture and every leg.
- **One fetch serves five rules.** `run.run_surface` over a counting fetcher issues exactly one GET of `/data.json`. D4's Finding is byte-identical to D4 judged alone. The four field Findings cite that one Observation.

**Control fixtures.** The four legs are framework legs, so every control cycle now judges them.
- **Expectations** were derived from the rule source and written into `params.yaml:e5_control` as a comment before the fixtures ran. The legs take every fixture's default, with no new rows:
  - `passes_all`: `pass`. Its `data.json` now carries the fields.
  - `fails_all`: `fail` (404, no catalog).
  - `refuses_identified_client` and `resets_connection`: `error`.
  - The other five fixtures: `pass`.
- **Result.** The slow control tests ran green in `logs/dcat_controls.log`: 170 passed, 0 skipped, 12 xfailed, 0 deselected. They ran again inside `gate-full`.

## 1. Retained catalogs of the cycle of record: **UNPUBLISHED**

**What was run.** `scripts/exercise_dcat_field_rules.py` (log: `logs/dcat_exercise.log`).
- The cycle of record is `scan_2026-09-10_rj2`, and its Observations are `scan_2026-09-10`'s.
- The script took the 46 surfaces with a D4 Observation.
- For each served catalog it read the stored body and attached `v2clauses.dcat_record_fields` offline, which is exactly what `runner.collect_leg` now does at collection. It then judged each rule twice.
- Missing bodies: 0. Deterministic: `true`.

**What was not done.** Nothing here entered a matrix, figure, Result or report. Cycle 5 is the first judgement of record.

| leg | pass | fail | error | fail outcomes |
|---|---|---|---|---|
| B1 | 0 | 38 | 8 | `no_product_record` 35, `no_data_dictionary` 3 |
| B4 | 0 | 38 | 8 | `no_product_record` 35, `quality_measurement_absent` 3, `revision_metadata_absent` 3 |
| D3 | 0 | 38 | 8 | `no_product_record` 35, `no_lineage_field` 3 |
| G4 | 3 | 35 | 8 | `no_product_record` 35 |

**By body.** Nine of the 16 bodies answer `/data.json` with no catalog. Four are blind: BLS, BTS and ORES are `refused`, and SAMHSA returns 5xx. Three serve one:
- **federalreserve.gov:** 167 records. Its flagship `scfindex` has 1 product record.
- **bea.gov:** 26 records. The home surface matches 14.
- **census.gov:** 1,805 records. The home surface matches 1,635.

**What the served catalogs carry.**
- **Authority codes.** All three catalogs carry `bureauCode`, `programCode` and `publisher` on every record, well-formed. That is G4's three passes.
- **The other fields.** Not one record in any of the three carries `describedBy`, `hasQualityMeasurement`, any revision field, or any lineage field. That is decision 2's "absence everywhere", measured.

**A finding about the subject, not about the rules.** D4's membership test is a substring test. A host-level `home` surface therefore "owns" every record containing its URL: census.gov's home URL is inside 1,635 of its 1,805 records. So two of G4's three passes are readings of a host's catalog through D4's lens, not of one product's record. This follows D4, as decision 1 asked. Every verdict prints how many records it read, so it is visible rather than hidden. It is a candidate question for D4 itself, and this task leaves it open.

## 2. The record write

Every change went through `framework_writeback.save`. The five events are all on `events/batch-033_framework.jsonl`, and every one names this task.

| event | time (UTC) | script | delta | framework sha256 |
|---|---|---|---|---|
| `fd30abf394634eacb0a7943baf0efe17` | 05:07:43 | `build_framework_graph.py` | `ind:D3`: `gap` → null, `evidence_raw` cites the PROV documents; +2 `EVIDENCED_BY` (`doc:w3c-prov-dm-data-model`, `doc:w3c-prov-o-ontology`); gaps 14→13, evidenced_by 139→141 | `68690fd3…d1dcd5` |
| `90602170aca34d7bb8a84a7d3c31ca24` | 05:08:04 | `build_measurement_specs.py --add-missing` | +4 `MeasurementSpec` (`spec:B1`, `spec:B4`, `spec:D3`, `spec:G4`), +4 `MEASURED_BY`; measurement_specs 22→26 | `d5d1192c…62278f` |
| `fca217d493664d44af7ea35ac7344e6b` | 05:08:07 | `framework_writeback_rules.py` | each spec `rule_id` → `RULE-<code>-v1`; B1, B4, D3, G4 `specified` → `harness_built`; rules_built 17→21 | `4348c97d…460cb8` |
| `a515f61d202a4f07955d2036e3c24d7e` | 05:08:30 | `tag_measurement_tiers` | B1, B4, D3, G4 → rule 1, `harness_leg`, `tier_source` "rules.CURRENT['X'] = RULE-X-v1 …; measurement spec `spec:X`", with a note on what is unmeasured; E1, E3 → M, `judged_reading` (decision 5's notes verbatim, source cites the predecessor RESULT §0 and this task) | `c54df58e…97251d` |
| `a74af444265a4bf4bb6036bd0aad31a3` | 05:08:34 | `tag_prescriptions` | +9 `Action`, +9 `REMEDIATES`; actions 42→51 | `97a2c1db…238443` |

**Actions added** (all `authored_by` this task):
- **`edit_existing`:** `b1-link-the-data-dictionary-from-the-catalog-record`, `b4-publish-quality-measurements-as-metadata`, `b4-state-what-changed-from-the-previous-version`, `d3-name-the-generating-activity-in-the-catalog-record` and `g4-carry-bureau-and-program-codes-on-the-record`.
- **`publish_new_file`:** four `…-publish-the-products-record-with-…` actions, one per leg's `no_product_record`. Each carries a `technique_class_reason`; see §3 premise 7.
- **Sources.** Every technique source is a verbatim quote from `dcat-us-1-1-schema`, `dcat-us-3-dataset-schema` or `w3c-dwbp-2017`, checked by the tagger before any write.

**Totals.**

| | before | after |
|---|---|---|
| tier M / O / D | 34 / 5 / 5 | **36 / 5 / 5** |
| unassigned | 5 | **3** (B6, G3, G5) |
| `harness_leg` | 17 | **21** |
| `structured_field` | 7 | **3** (B2, B5, D2: the sibling task's) |
| `judged_reading` | 2 | **4** |
| measurement_status (measured / harness_built / specified) | 16 / 1 / 32 | **16 / 5 / 28** |

**Checks on the record after the writes.**
- **Live Cypher after projection** agrees row for row, with `projection_gate: green`:
  - `M harness_leg 21 [… B1 B4 D3 G4]`
  - `M judged_reading 4 [E1 E3 G1-O G6]`
  - `M structured_field 3 [B2 B5 D2]`
  - `— — 3 [B6 G3 G5]`
- **Projection.** `scripts/load_framework_graph.py`, log `logs/dcat_projection.log`, `EXIT=0`, `harness_leg_indicators_without_an_action: []`.
- **Idempotence.** Every writer is a no-op over the new record: `build_framework_graph --dry-run`, `tag_measurement_tiers --dry-run`, `framework_writeback_rules --dry-run`, `build_measurement_specs --add-missing --dry-run` and `tag_prescriptions --dry-run` all report unchanged. The protected script asserts three of them.

**Regenerated views.**
- `docs/design/scan_tool_map.md`
- `docs/design/scoring_model.md`: 20 adopted harness legs, 14 scored on the cycle of record; the four new legs are "not a leg of any published matrix".
- `docs/design/mcp_over_the_graph.md`
- `docs/data/ai_readiness_framework.json` and `docs/data/index.json`, via `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest` (log `logs/dcat_site.log`, `EXIT=0`). `sources_per_check.json` did not move.

## 3. Premises the task file got wrong

1. **"All four read what `dcat.fetch_catalog` already retains."**
   - **What is true.** The collector retains the bytes.
   - **What is false.** A rule is pure and cannot read a stored body, and nothing on the D4 Observation named a field. A rule written to the task's write set would have had nothing to judge.
   - **What was done.**
     - `v2clauses.dcat_record_fields` (collector layer) summarises the product's records as field profiles.
     - `runner.collect_leg` attaches that summary to D4's Observation and returns `[]` for the four legs.
     - The field lists, the two formats and the clauses went into `params.yaml:dcat_fields`, because constitution §2 puts them in config.
   - **Consequence.** Every Observation already on the log lacks the block, so the rules return `error` on stored cycles. That is why §1 re-reads the bodies offline.
2. **Writing only the rules would not have been enough.** The write set omits the MeasurementSpecs, and `run.run_surface` judges only legs that have a spec. Without the specs, cycle 5 would silently have judged none of the four.
   - I added the specs through `build_measurement_specs.py --add-missing`. This is a new path: the regeneration path resets written-back `rule_id`s and drops recorded `decision`s.
   - `framework_writeback_rules.py` then did what it always does: it pointed the specs at the rules and moved the four indicators `specified` → `harness_built`. The task file does not mention that status move.
3. **Decision 6: "corrected through the writer".** The gap cell is *authored* by the skeleton. Editing the record directly would break the invariant that `build_framework_graph.py` over HEAD is a no-op (`tests/test_framework_single_writer.py`). So the D3 row's Evidence cell was corrected in `docs/crosswalk/usafacts_operationalization_skeleton.md` and regenerated.
   - It is one cell. It quotes each PROV document and says the earlier text was stale.
   - Because the cell now names two admitted documents, the builder minted their `EVIDENCED_BY` edges. `gaps` went 14 → 13.
4. **D4 would have been fetched twice.** `run_surface` collected shared legs once and then collected every judged leg again. With D4 both judged and consumed, every host would have been asked for `/data.json` twice per surface.
   - `run.py` now reuses the shared collection for such a leg. The change is two re-indented lines under a new branch.
   - D4's Finding is unchanged. A test shows it is byte-identical to D4 judged alone.
5. **The passing control would have broken cycle 5.** `passes_all`'s `data.json` carried none of the fields. With the four legs in `FRAMEWORK_LEGS`, its pre-registered `pass` would have failed and E5 would have invalidated cycle 5.
   - The fixture now carries the fields, and D4 still validates.
   - Each fixture's expectation for the new legs is its existing default, derived and written down before the controls ran (§0).
6. **Other files the write set omits, each forced by the moved counts:**
   - `scripts/scan_tool_map.py`: a leg is now credited with the collectors of the legs it consumes. Otherwise the four rows would read "no collector reaches this yet" beside a rule that reads `dcat`.
   - Two generated pages: `scoring_model.md` and `mcp_over_the_graph.md`.
   - Seven tests whose literals move: the projection round-trip, single-writer, MCP, tiers, prescriptions, `test_rule_a12_v3` (the list of `unobserved_error` callers), and `test_scan_harness` / `_v3` (framework legs 16 → 20, `SHARED_LEGS` gains D4). Each new literal has its reason beside it.
   - `--task` on four writers, so the events name this task.
7. **Decision 4 assumes each failing outcome has one technique class.** `no_product_record` covers two acts: publishing a new `data.json`, or adding a record to one that exists. It is classed `publish_new_file`, the act most bodies on the cycle of record face (9 of 16 serve no catalog), and the node says so in `technique_class_reason`. Splitting it into two outcomes would have duplicated D4's `no_catalog` / `product_absent_from_catalog` pair on four more legs.
8. **§0: "the field locators are on each node as `tier_field` and `tier_collector`".** That was true before this task. Once a row is `harness_leg`, those keys leave the node, because `tests/test_measurement_tiers.py` holds them to the `structured_field` basis. The locators now live in three places: the rule module docstrings, the spec `signal`s, and the `tier_note`.

**Not a premise error, recorded anyway.** B1's basis is now `harness_leg` on the strength of its DCAT half alone. Its `tier_note` says the schema.org half is unread until `2026-09-18_schema_field_rules.md`, which writes a `RULE-B1-v2` rather than editing this module.

## 4. Gate

**Tier:** `make gate-full` was the full suite, detached and polled to `EXIT=`. `make gate-task` was run as well, because a rule module and the registry changed.

| check | result | log |
|---|---|---|
| `make gate-full` | **2486 passed, 3 skipped, 12 xfailed, 0 deselected**, 248 warnings, 1368.91 s, `EXIT=0` | `logs/suite.log` |
| skips (3, as expected) | `tests/test_dispatch_config.py:333` (interactive_only, dispatched session); `tests/test_scan_harness.py:282` (E5 judges the cycle, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | `logs/suite.log` |
| `make gate-task` | fast: **2461 passed, 3 skipped, 12 xfailed, 25 deselected**, 481.03 s; re-derivation: **22 passed, 0 skipped, 0 xfailed, 25 deselected**; `EXIT=0` | `logs/dcat_gate_task.log` |
| slow control tests, run first | 170 passed, 0 skipped, 12 xfailed, 0 deselected, `EXIT=0` | `logs/dcat_controls.log` |
| `seldon verify` | all checks passed (replay skipped as expensive, its default), `EXIT=0` | `logs/dcat_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` | `logs/dcat_protected.log` |
| projection | `load_framework_graph.py` `EXIT=0`; round-trip gate green inside the suite | `logs/dcat_projection.log` |
| retained catalogs (§1) | `EXIT=0`, deterministic, 0 bodies missing | `logs/dcat_exercise.log` |

**An earlier fast-tier probe on the same tree failed 20 tests** (`logs/dcat_fast_probe.log`). Every failure was a literal this task moves (§3 premise 6), or one of the two generated pages that had not yet been regenerated. No gate or threshold was moved. `params.yaml:e5_control` gained a comment and no expectation row.

**Write set as committed:**
- the four rule modules, `_dcat_fields.py` and `rules/__init__.py` (V11);
- `collectors/v2clauses.py`, `runner.py`, `run.py`, `params.yaml` and `fixtures/passes_all/data.json`;
- the skeleton's D3 cell;
- the record and its five events;
- `scripts/`: `tag_prescriptions.py`, `tag_measurement_tiers.py`, `build_framework_graph.py`, `build_measurement_specs.py`, `scan_tool_map.py`, `exercise_dcat_field_rules.py` and `check_protected_dcat_rules.sh`;
- `tests/test_dcat_field_rules.py` plus seven test literals;
- regenerated `docs/design/{scan_tool_map,scoring_model,mcp_over_the_graph}.md` and `docs/data/{ai_readiness_framework,index}.json`;
- `seldon_events.jsonl`;
- this RESULT.

**What the next task starts from.** `2026-09-18_schema_field_rules.md` runs next. Its B1 half should be a `RULE-B1-v2` that consumes both D4 and `structured_data`; `RULE-B1-v1` stays in `REGISTRY`. Cycle 5 on 2026-10-05 is the first judgement of all four rules here, and its collector attaches `dcat_fields` at collection time.
