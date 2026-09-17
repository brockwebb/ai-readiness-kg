# CC Task: the prescription layer, schema and first sourced actions for the 17 harness-leg indicators

**Date:** 2026-09-17
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md` §2.3 and §4 item 3, and `cc_tasks/2026-09-17_measurement_tiers_RESULT.md` §1 (the 17 `harness_leg` rows) and §2.
**Implements:** DN-005 §2.3: an `Action` node type, `REMEDIATES` edges to indicators, effort/cost/value fields with provenance, a source or an explicit estimate marker on each. Under DN-001 and DD-001.
**Framework layer served (DN-005 §5 rule 1):** §2.3, prescription. "The instrument measures; it does not yet say what to do."
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. Every technique source is a document already in `corpus/` or a standard already cited by the framework record; nothing is fetched.

---

## 0. Prior art, and what this project adds

DN-005 §2.3 names the shapes to read before designing: WCAG (success criterion → sufficient techniques → common failures), CIS Benchmarks (each recommendation carries description, rationale, impact, audit procedure, remediation, default, references), OpenSSF Scorecard (check → risk → remediation). Add Lighthouse audits (each audit ships a "how to fix" reference) and NIST SP 800-53's control → assessment procedure pairing. The common shape: **an action is bound to the check that would detect its absence, and the same check verifies its completion.** None of them carries effort, cost or value. That is this project's contribution and it is the part that must be sourced or marked, never guessed.

The framework record already holds the check side: 17 indicators with a rule in `rules.CURRENT`, each rule's failing outcomes enumerated in its module, and the cycle of record (`docs/reports/publication.yaml:snapshot_cycle`) recording which of 16 bodies fail which leg. The value of an action is therefore cold data: the count of bodies its completion would move from fail to pass on the leg that verifies it. Nothing about value needs an opinion.

**Decisions taken here (operator overrides later):**

1. **`Action` is a node in the framework record, written through `framework_writeback.save`, projected like every other node.** Fields:
   - `id` (`act:<slug>`), `title` (imperative, one line), `description` (what to do, in terms a web or data team can execute),
   - `technique_source[]`: locators into documents on disk or standards the record already cites (RFC 9309 for robots, the sitemaps.org protocol, schema.org `Dataset`, DCAT-US, OpenAPI, the `.well-known` registrations, and so on). At least one per action, quoted or located per DN-001.
   - `effort_band` ∈ {hours, days, weeks, quarter} and `cost_band` ∈ {none, tooling, staff_time, procurement}, each with `effort_source` / `cost_source`: a locator (a vendor's or standard's own implementation guidance, a published case) or the literal `estimate:pending` when no source on disk supports a band. **An `estimate:pending` band is left empty; this task does not fill it with a guess.** The RESULT lists every pending slot for the operator, who is the value input for those bands.
   - `value` is computed, not authored: `bodies_failing_now` (from the cycle-of-record matrix, per leg), `constructs_served[]` (via the indicator's `MEASURES` edge), `downstream_indicators[]` (indicators whose spec presupposes this one, where the record says so). All three carry the matrix path or edge as source.
   - `verifies_by`: the rule id whose outcome flips when the action is done. **No action without a verifying rule.** That is the WCAG/CIS invariant and it is what makes the layer a query.
2. **`REMEDIATES` edges from Action to Indicator**, with `outcome` naming the failing outcome of the rule the action addresses (a rule with three failing outcomes may need three actions or one action with three outcomes; the edge says which). Every one of the 17 `harness_leg` indicators gets at least one action per failing outcome its rule can return. A12 (candidate) and E5 (judges this instrument's own cycle) get their actions marked `applies_to: publisher` false where that is the case, not omitted.
3. **The schema is in the record's schema file and the projection**, with a Cypher test asserting: every `harness_leg` indicator has ≥1 `REMEDIATES` in-edge; every Action has ≥1 `technique_source` and a `verifies_by` that resolves to a rule in `rules.CURRENT`; every band is a legal value or `estimate:pending`; `value.bodies_failing_now` equals the matrix's fail count for that leg on the cycle of record.
4. **One query is the deliverable view, and it is written as a script, not a slide.** `scripts/prescriptions.py --body <name>` prints, for one body on the cycle of record: each failing leg, the action(s) that remediate it, technique source, effort and cost bands (or `pending`), and how many other bodies share the failure. `--all` prints the actions ranked by `bodies_failing_now`. The RESULT includes the `--all` output and one `--body` output. This is the query DN-005 §2.3 says the layer exists to make.
5. **Nothing is measured and no report is rebuilt.** The site's published framework copy will move by sha256, exactly as in the predecessor; the same three `build_l0_site.py --only` payloads are regenerated and the protected-paths check names them. `state/`, `corpus/`, `assessment/` byte-identical.
6. **The 20 unassigned indicators and the O/D rows get no actions here.** Prescriptions for indicators without cold data would be sourced techniques with no `bodies_failing_now`, which is a different and smaller task, authored after this one from §1.

**Write set:** `framework/ai_readiness_framework.json` through its writer and the event it emits; the schema file the record validates against; `scripts/build_framework_graph.py` / the projection only for the new node and edge type; `scripts/prescriptions.py` (new); `scripts/tag_prescriptions.py` or equivalent writer driver (new); `tests/test_prescriptions.py` (new); `scripts/check_protected_prescriptions.sh` (new); the three site payloads; `seldon_events.jsonl` by this task's transitions; the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-17_prescription_layer_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Prior art: read DN-005 §2.3, the four shapes named above as they exist on disk or in the record's citations (cite what is on disk; do not fetch), each of the 17 rule modules for its failing outcomes, and the cycle-of-record matrix for fail counts per leg. If an action, remediation or "how to fix" field already exists in the record or the skeleton under another name, use it and say so.
## 2. Decisions 1 and 2, indicator by indicator: the action table (indicator, outcome, action id, technique source, effort band + source, cost band + source, bodies failing now).
## 3. Decisions 3, 4, 5.
## 4. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths, the projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing: report and stop.
## 5. Report
RESULT `cc_tasks/2026-09-17_prescription_layer_RESULT.md`: §0 what prior art already had; §1 the action table; §2 counts (actions, edges, sourced bands, pending bands) and **the list of `estimate:pending` slots as one table for the operator**; §3 the `--all` and one `--body` output; §4 every premise this task file got wrong; §5 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → §3 → glob addenda → §4 → §5 → push.
