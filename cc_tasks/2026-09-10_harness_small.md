# CC Task — harness small: clock through merge_controls, a cheap agreement check, xmlns at source

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-10_virtual_time_RESULT.md` §7 and `2026-09-10_report_pdf_RESULT.md` §8.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs before `2026-09-10_scan_frame_v5.md`.
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

**Decisions taken here (operator overrides later):**
1. `merge_controls` takes a `clock` parameter, real by default, threaded to the control cycles it runs. `run.py::main` still takes no clock and the signature test still asserts it.
2. The both-clocks agreement check stays in the per-task gate (it is what makes every virtual test meaningful) but its real-clock side runs at a short test interval (`manners.standing_interval` overridden to 0.05 s for that test only, stated in the test's docstring). Verdict agreement is a property of the rules, not of the rate; the one-fixture `slow` test is what asserts the real standing rate and it is unchanged.
3. `figures.py` emits `xmlns="http://www.w3.org/2000/svg"` on the root element at source. The registered Figure artifacts re-hash; the report build's namespaced-copy step is removed since the source is now a standalone document. The HTML graph page is checked to still render (inline SVG with xmlns is valid).
4. The suffix-list lint and every other source-scanning check in the repo strip comments and string literals before matching, as `2026-09-10_virtual_time_RESULT.md` §5 item 6 prescribes for the class. One shared helper; each check uses it; a test plants the needle in a comment, a docstring and a string literal and asserts no match, then plants it in code and asserts a match.

**Zero edits to:** shipped rule modules, registered Result values, prior RESULTs, cycle evidence, report prose, targets v4.

**Immutable once written. Glob `2026-09-10_harness_small_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 to 4.
## 2. `make report-pdf` still passes its numeral gate with the namespaced-copy step removed.
## 3. Gate (the one gate of this task)
Both-clocks agreement, 7 fixtures, 0 differences, with the agreement test's wall-clock reported; fast tier green with wall-clock; full suite green with wall-clock and `--durations=10`; 8 payloads byte-identical; hygiene, `seldon verify`, protected paths. Expected: `test_merging_controls...` no longer in the top ten.
**Failure: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-10_harness_small_RESULT.md`. Register `suite_fast_seconds_2026-09-10b`, `suite_full_seconds_2026-09-10b`. Every premise wrong. `seldon cc complete`, commit, push. Final message states whether the RESULT exists and the push succeeded.

**SEQUENCING:** §1 → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
