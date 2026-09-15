# CC Task — the abstract says six host-level checks; the report now has five

**Date:** 2026-09-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-15_g1d_leaves_l0_RESULT.md` §9 item 1.
**Implements:** DD-066. `publication.yaml`'s abstract feeds `CITATION.cff`, `zenodo.json` and the site index; every consumer is asserted by `tests/test_publication.py`.
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene: a published summary must not disagree with the report it summarizes.
**Fulfils:** its own ResearchTask (`seldon cc register`).
**Spend:** zero model calls. **Network:** none.

**Decisions taken here (operator overrides later):**
1. The abstract's count of host-level checks changes from six to five: four rated (A4, A5, A10, A11) and A12 as candidate, which is how the report counts them. If the abstract enumerates the checks by name, G1-D leaves the list; if it states a rate that included G1-D, the sentence is re-sourced from the report's current registered Results and the RESULT quotes the before and after.
2. Every derived copy (`CITATION.cff`, `zenodo.json`, the site index and any other consumer `tests/test_publication.py` asserts) regenerates through the existing writer, never by hand.
3. Nothing else in `publication.yaml` moves.

**Zero edits to:** anything outside `publication.yaml` and the files its consumers regenerate.

**Immutable once written. Glob `2026-09-15_abstract_five_checks_ADDENDUM*.md` before starting and again before §2.**

---

## 1. The edit and the regeneration.
## 2. Gate
`tests/test_publication.py` green; site `--check` green; `make gate-fast` detached, logged, polled; `seldon verify`; protected paths. Failure ships nothing: report and stop.
## 3. Report
RESULT `cc_tasks/2026-09-15_abstract_five_checks_RESULT.md`: the abstract sentence before and after; the regenerated files by path; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → glob addenda → §2 (detached, logged, polled) → §3 → push. Runs now, before `cc_tasks/2026-09-15_standing_dispatcher.md`.
