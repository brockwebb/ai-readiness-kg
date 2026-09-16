# CC Task — publication guards: every generated consumer is compared to the declaration it came from

**Date:** 2026-09-16
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-15_derived_counts_and_appendix_guard_RESULT.md` §3 (the inventory table and its four items).
**Implements:** DN-004's guard shape, generalized: a published file is compared to its source by a standing test, not by a task gate somebody runs.
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene.
**Fulfils:** its own ResearchTask (`seldon cc register`). Intended as the standing dispatcher's first automated launch (cadence task decision 4).
**Spend:** zero model calls. **Network:** none.

**Decisions taken here (operator overrides later):**
1. **The abstract's count enters the suite.** `scripts/check_protected_abstract_five_checks.sh`'s comparison of the abstract to the tier-A matrix's `legs` length becomes a test in `tests/test_publication.py`, through `scripts/numerals.word`, so it runs on every gate and not only when a task invokes the script. The script stays; it now calls the same function the test does.
2. **`publication.yaml` → consumer, field by field.** For `CITATION.cff`, `.zenodo.json` and their `docs/data/` copies: title, abstract, version, authors and date-released are compared back to the declaration, the way the licence identifiers already are. One parametrized test, one row per field per consumer.
3. **The published matrices join the inventory.** `docs/reports/scan_matrix_*.{json,csv}` listed in `docs/data/index.json` `matrices`: each JSON's `legs`, `legs_withdrawn` and row count are compared to the CSV beside it, and each is compared to what `build_l0_matrices.compute` produces for its cycle from the log now (the DN-004 comparison, run at test time rather than only at build time). A mismatch is a failing test with the differing cells named.
4. **`docs/data/index.json`'s `generated` and `matrices` lists are compared to the files on disk**: every listed path exists and every published file under `docs/data/` and `docs/reports/scan_matrix_*` is listed. A file published and unlisted, or listed and absent, fails.
5. **Row counts in labels stay typed.** "The 16 Tier A bodies" and "the three federal reference hosts" are frame counts fixed by DD-026 and DD-030, not derived quantities; a test asserts them against the frame file so a frame change fails loudly, and nothing else changes.

**Zero edits to:** rule modules, `assessment/`, `state/`, `events/`, `corpus/`, `controls.yaml`, `framework/`, the report source, the PDF, the matrices, `publication.yaml`, `CLAUDE.md`. This task writes tests and one shared function; it regenerates nothing.

**Immutable once written. Glob `2026-09-16_publication_guards_ADDENDUM*.md` before starting and again before §2.**

---

## 1. Decisions 1 to 5, each test red against a deliberately broken fixture before it is green against the tree (the standing shape: a guard replays what it is built for).
## 2. Gate
`tests/test_publication.py` green; `make gate-fast` detached, logged, polled (no payload is touched; say so); `seldon verify`; protected paths asserting nothing under `docs/` changed. Failure ships nothing: report and stop.
## 3. Report
RESULT `cc_tasks/2026-09-16_publication_guards_RESULT.md`: the test count before and after; each guard's red run; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → glob addenda → §2 (detached, logged, polled) → §3 → push. Dispatched by the standing dispatcher after `cc_tasks/2026-09-16_cadence_and_enable.md` completes; not hand-dispatched.
