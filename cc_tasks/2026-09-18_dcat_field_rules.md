# CC Task: four DCAT-US structured-field rules, pre-registered before cycle 5

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-17_unassigned_indicators_RESULT.md` §0 (the `structured_field` rows and the field and collector each names) and §5 item "the seven structured_field rows".
**Implements:** the harness discipline in `CLAUDE.md` and DN-005 §2.1/§2.2: a rule is written, versioned and registered before the cycle that first judges it (E2's own standard), and a `structured_field` indicator becomes `harness_leg` only when a rule in `rules.CURRENT` serves it.
**Framework layer served (DN-005 §5 rule 1):** §2.2, moving four rows from `structured_field` to `harness_leg` ahead of cycle 5 (2026-10-05).
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. No host is contacted; the rules are exercised against retained evidence from the cycle of record and against fixtures.

---

## 0. The four rows, and the collector they share

B4 (`hasQualityMeasurement`, `versionNotes` / `previousVersion`, DCAT-US 3), D3 (`wasGeneratedBy` / `qualifiedAttribution`, DCAT-US 3; `prov:wasGeneratedBy` / `prov:wasDerivedFrom`, DCAT 3), G4 (`bureauCode`, `programCode`, DCAT-US 1.1), and B1's DCAT half (`describedBy`, DCAT-US 1.1). All four read what `dcat.fetch_catalog` already retains. The field locators are on each node as `tier_field` and `tier_collector` with their corpus citations; read them off the record, not from this file.

**Decisions taken here (operator overrides later):**

1. **One rule per indicator, versioned `v1`, in the existing rule-module shape**, with named failing outcomes whose reason strings are stable one-line fragments (the prescription layer anchors on them). Each rule's `measures()` names its subject level (host catalog vs product record), following D4's precedent since it reads the same catalog.
2. **Pre-registered, not run.** The rules enter `rules.CURRENT` and the registry; the basis on each node moves to `harness_leg` through the framework writer with `tier_source` citing the rule id; **no cycle is run and no matrix is rebuilt.** Cycle 5 judges them first. A rule that cannot be exercised on the retained catalogs of the cycle of record (because the field is absent everywhere) still ships, with that fact in the RESULT, because absence is the verdict the rule exists to record.
3. **Each rule is exercised three ways before registration**: a fixture catalog that passes, one per failing outcome, and the retained catalogs of the cycle of record with the verdict distribution reported (not published). Determinism: two runs over the same bytes give the same Finding ids.
4. **Prescriptions follow automatically.** `tag_prescriptions.validate` requires every `harness_leg` indicator to have an action per failing outcome, so this task writes those actions with technique sources from the same DCAT documents the fields cite, classed by the existing five classes. The join is on the basis; nothing hand-kept.
5. **E1 and E3 take the Desktop's naming decision in the same record write:** basis `judged_reading`, tier M, `tier_note` "no instrument exists; the reading is of a published report, not a served surface" and, for E3, "observability is one-sided: a fail is visible, a pass needs the agency's records". No fourth tier. `tier_source` cites `2026-09-17_unassigned_indicators_RESULT.md` §0 and this task.
6. **The stale `ind:D3.gap` cell is corrected** through the writer: the two PROV documents are admitted (`w3c-prov-o-ontology`, `w3c-prov-dm-data-model`, both `included` in the manifest). One line, cited.

**Write set:** four rule modules under `assessment/harness/scan/rules/`, the registry, `rules.CURRENT`; fixtures and tests; `framework/ai_readiness_framework.json` through the writer (basis moves, E1/E3, D3's cell, the new actions and edges); `scripts/tag_prescriptions.py` (new outcomes), `scripts/tag_measurement_tiers.py`; the regenerated tool map and site payloads; `scripts/check_protected_dcat_rules.sh` (new); `seldon_events.jsonl`; the RESULT. `state/`, `corpus/`, `docs/reports/` byte-identical.

**Immutable once written. Glob `2026-09-18_dcat_field_rules_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Read the four nodes, D4's rule as the precedent, the DCAT documents at the cited sections, and `CLAUDE.md`'s rule-versioning and registry rules.
## 2. Decisions 1 to 6. Tests first.
## 3. Gate
`make gate-full` (`-rs`) plus `make gate-task` for the rule modules, `seldon verify`, protected paths, projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_dcat_field_rules_RESULT.md`: §0 the four rules with outcomes and the fixture results; §1 the verdict distribution over the retained catalogs of the cycle of record, marked unpublished; §2 the record write (basis moves, E1/E3, D3, actions added) with event ids; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_scoring_model.md`.
