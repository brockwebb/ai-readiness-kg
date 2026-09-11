# CC Task — L0 report, cycle-4 revision: the snapshot moves to `scan_2026-09-10_rj2`

**Date:** 2026-09-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-11_f5_membership_through_fallback_RESULT.md` §1, §6, §8 item 5, §10 items 1, 2; and `2026-09-10_thread_close_harness_v5_rejudge_dispatched.md` §5.4.
**Fulfils:** its own ResearchTask (`seldon cc register`). This is the last task before the report is published. It is a correctness fix before it is a refresh: the PDF on disk embeds an F5 with eleven "not measured" rows about legs that were measured, and is pinned as one rebuild behind (`tests/test_report_pdf.py`).
**Spend:** zero model calls. **Network: none.** Everything the report quotes is a registered Result or a figure on disk.

**Decisions taken here (operator overrides later):**
1. **Cycle 4 re-judged (`scan_2026-09-10_rj2`) is the report's snapshot; cycle 3 re-judged (`scan_2026-09-09_rj2`) is the predecessor in the movement section.** Every `{{result}}` tag that named a cycle-3 name moves to the cycle-4 name where the cycle-4 name is registered, and to the cycle-4 fallback target where the comparison record licenses it; a tag that resolves to neither is a hard error, never a hand-typed number. The Figure artifacts embedded are the `_rj2` figures.
2. **There is one implementation of the fallback rule.** `scripts/register_scan_figures.py::_resolve_read` and its hardcoded three-cycle list are deleted; Figure registration resolves reads through `figures.Reads`. A test asserts no module other than `figures.py` implements suffix stripping. Figure artifacts for `scan_2026-09-10_rj2` and `scan_2026-09-09_rj2` are registered with their `CONTAINS` edges, and a test asserts every edge resolves.
3. **Content changes are the four the thread-close handoff named and nothing else.** (a) Cycle 4 as snapshot, with the matrix's last row no longer "planned". (b) The refusal column and one sentence: three of sixteen bodies refuse an identified client, six consecutive cycles (the registered Result carries the number; the prose carries the tag). (c) NOAA 3 of 5 AI-ready components and ESIP 9 of 58 checklist items, into the "what the matrix cannot see" section, as tags. (d) The four flagships that came live in cycle 4, as a tag on the declared count. The scope fence of 2026-09-09 stands: no new section, no new indicator, ≤ 7 pages, every numeral a tag.
4. **The A3 movement is written as what it is.** The movement section states that five declared flagships left A3's denominator under generation 9 because the harness had been counting products whose download it was forbidden to look for as products without one, and that the instrument's claim got weaker as a result. One paragraph, tags for 19 → 14 and the upper bound.
5. **Traceability, measured and reported, not gated.** For each of the six tier-0 legs and A3, the RESULT states whether the graph links the rule's indicator node to a construct, definition or source node (the survey item → construct → definition → source crosswalk that CLAUDE.md calls the validity layer), by Cypher, with counts. If the answer is "no edge" for any leg, the RESULT says so and the report is not changed for it; that is the next task's decision.
6. **The pin in `tests/test_report_pdf.py` is deleted** as its own text instructs, in the same commit as the rebuild.

**Zero edits to:** rule modules, harness runtime, stored payloads, prior Results, prior RESULTs, cycle evidence, targets, registration records, invariant pins, figures (they are read, not re-rendered), report prose beyond decision 3 and 4.

**Immutable once written. Glob `2026-09-11_l0_report_cycle4_revision_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decision 2. The single fallback implementation and the Figure artifacts. Stop if any `CONTAINS` edge for `_rj2` fails to resolve.
## 2. Decisions 1, 3, 4, 5, 6. Retag, the four content changes, the movement paragraph, the Cypher, the build through `make report-pdf`, the pin removed.
## 3. Gate (the one gate of this task)
Every `{{result}}` and `{{figure}}` tag resolves, 0 hand-typed numerals (the tag-coverage test); PDF numeral-multiset gate green with the pin deleted and no replacement pin; `test_report_text_and_figures_agree_per_leg` green; the embedded F5 carries 0 "not measured" rows; page count ≤ 7; `_resolve_read` absent and the single-implementation test green; Figure artifacts registered with resolving `CONTAINS` edges; every committed figure is what the renderer produces today; socket counter 0; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes no PDF and no Figure artifacts: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-11_l0_report_cycle4_revision_RESULT.md`: every tag that moved, from what to what; the four content changes with their tags; the decision-5 traceability table; page count; every premise wrong. `seldon cc complete`, commit, push. Final message states the PDF path, the page count, the decision-5 table in one line per leg, and whether the push succeeded.

**SEQUENCING:** §1 (stop on an unresolving edge) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
