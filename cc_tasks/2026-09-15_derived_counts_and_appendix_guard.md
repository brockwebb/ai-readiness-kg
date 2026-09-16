# CC Task — published counts derive from the matrix they label; the source appendix is compared to the graph it came from

**Date:** 2026-09-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-15_abstract_five_checks_RESULT.md` §5 items 1, 2 and 4.
**Implements:** DD-066 and DN-004's guard shape (a published artifact is compared to the graph it was derived from, or it drifts).
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene: two published pages say six about a five-column matrix, and one published payload sat a rule version behind the graph for two days with every gate green.
**Fulfils:** its own ResearchTask (`seldon cc register`).
**Spend:** zero model calls. **Network:** none.

**Decisions taken here (operator overrides later):**
1. **Matrix labels derive `len(legs)` from the matrix JSON they describe.** `scripts/build_l0_site.py:96` (`MATRICES`) stops carrying a typed count; the label is rendered from the matrix file's `legs` array through the same numeral map `scripts/check_protected_abstract_five_checks.sh` uses, and that map moves into one importable place so the abstract check and the builder read one function. `docs/index.html` and `docs/llms.txt` regenerate through the writer. The unreachable branch at `build_l0_site.py:531` derives the same way, so the next self-scan gap does not ship a wrong number. The comment at `scripts/report_traceability.py:42` is replaced by one that states the list's length is asserted by a test, and a test asserts `len(_NAMED_IN_CODE)` against the enumerated set rather than a prose count.
2. **A guard compares `docs/data/sources_per_check.json` to the graph.** For every indicator row, `rules` equals the count of `(:Rule)-[:MEASURES]->(:AssessmentIndicator {code})`, and the source and definition counts equal what the builder would compute from the graph now. It joins `tests/test_publication.py` beside `test_the_published_result_values_and_states_match_the_graph`, and site `--check` runs it. The "when did `RULE-A12-v3` reach the graph" question is answered as far as the graph allows and no further: `Rule` nodes carry no `created_at`, so the graph cannot say (Desktop query 2026-09-15, all three A12 rules return `created: None`). The RESULT states that, and the guard is aimed at the drift class, not at the unrecoverable incident. If the projection can stamp `created_at` on `Rule` at write time without touching the ontology master, do it and say so; if it needs an ontology change, record that as a proposed ResearchTask and stop there.
3. **Every payload under `docs/data/` is inventoried once for graph comparability.** The RESULT carries a table: payload, what it is derived from, whether a test compares it to that source today. No new guards beyond decision 2 are written from the table; the table is what the next hygiene task is authored from.
4. **The G1-D row in `sources_per_check.json` stays and is labelled.** The sources exist and the construct stands (DD-066 §1); the row gains `measurement_tier: product` and `withdrawn_from: host-level` read from the framework record's indicator node, never typed. The published appendix then advertises a product-tier check, which is what G1-D is.
5. **The abstract keeps its typed count.** It is gated against the matrix and reads as a sentence; a pointer would not. Recorded as a decision so §5 item 3 is closed, not forgotten.

**Zero edits to:** rule modules, `assessment/`, `state/`, `events/`, `corpus/`, `controls.yaml`, the report source, the PDF, the matrices, `publication.yaml`.

**Immutable once written. Glob `2026-09-15_derived_counts_and_appendix_guard_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Decision 1: the derivation, the shared numeral map, the regeneration; the diff on `docs/index.html` and `docs/llms.txt` is exactly the four labels.
## 2. Decision 2: the guard, red first against the stale `rules: 2` reconstructed from git (`05455cd`), then green; the `created_at` answer.
## 3. Decisions 3 and 4: the inventory table; the labelled row through the writer.
## 4. Gate
`tests/test_publication.py` green including the new guard; site `--check` green and idempotent; `make gate-fast` detached, logged, polled; `seldon verify`; protected paths. Failure ships nothing: report and stop.
## 5. Report
RESULT `cc_tasks/2026-09-15_derived_counts_and_appendix_guard_RESULT.md`: the four labels before and after; the guard's red run; the inventory table; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → §3 → glob addenda → §4 (detached, logged, polled) → §5 → push. Hand-dispatched: `dispatch.enabled` is false.
