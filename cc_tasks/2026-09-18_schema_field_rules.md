# CC Task: three schema.org and robots structured-field rules, pre-registered before cycle 5

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-17_unassigned_indicators_RESULT.md` §0 and from `2026-09-18_dcat_field_rules.md`, whose decisions 1 to 4 apply here unchanged.
**Implements:** the same harness discipline and DN-005 §2.1/§2.2; the last three `structured_field` rows become `harness_leg` ahead of cycle 5.
**Framework layer served (DN-005 §5 rule 1):** §2.2.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. No host is contacted.

---

## 0. The three rows

B2 (schema.org `DefinedTerm` with `termCode`, `inDefinedTermSet`, `description`; via `structured_data.fetch`), B5 (`DefinedTerm.termCode` within `inDefinedTermSet`, compared across products within one cycle; the cross-vintage half waits for a second cycle and is recorded as unmeasured, per the node's `tier_note`), D2 (`Content-Signal` directive in robots.txt, categories `ai-train` and `ai-input`, via `robots.fetch`). B1's schema.org half (`variableMeasured`) joins B1's rule from the DCAT task if that task shipped first; otherwise B1 is written here whole and the DCAT task's RESULT is read for what it did. Field locators are on the nodes.

**Decisions taken here (operator overrides later):** decisions 1 to 4 of `2026-09-18_dcat_field_rules.md`, plus:

5. **B5 is the first rule that compares two collected surfaces.** Its subject is the body (host level), its evidence is the set of `DefinedTerm` codes across the body's products on one cycle, its failing outcomes are `no_term_codes`, `codes_not_shared_across_products`, `codes_without_set`. The cross-vintage clause is declared `unmeasured_until: second cycle with term codes` on the rule and in the record; not silently dropped.
6. **D2's rule reads a directive, not a policy.** `Content-Signal` present with a category the corpus document names → pass on the declared half; absent → `no_content_signal`; present with an unknown category → `unknown_category`. Enforcement is A12's business and is not re-measured here.

**Write set:** three (or four) rule modules, registry, `rules.CURRENT`; fixtures and tests; the record through the writer (basis moves, new actions and edges); the taggers; regenerated tool map and site payloads; `scripts/check_protected_sd_rules.sh` (new); `seldon_events.jsonl`; the RESULT. `state/`, `corpus/`, `docs/reports/` byte-identical.

**Immutable once written. Glob `2026-09-18_schema_field_rules_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Read the nodes, A6's rule as the `structured_data` precedent, A4's as the `robots` precedent, and the cited corpus sections.
## 2. Decisions. Tests first.
## 3. Gate
`make gate-full` (`-rs`) plus `make gate-task`, `seldon verify`, protected paths, projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_schema_field_rules_RESULT.md`: same sections as the DCAT task's, plus §1a the state of the record after both tasks: `harness_leg` count, remaining `structured_field` count (expected 0), and the sentence that cycle 5 on 2026-10-05 is the first judgement of all seven. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_dcat_field_rules.md`.
