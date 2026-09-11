# CC Task — L0 draft made self-consistent: figures drawn from cycle 3 re-judged; leg-rate names family-prefixed; the six misbound Results superseded

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-10_rejudge_2_3_4_RESULT.md` §1, §7 item 2, §9 items 1 and 2.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs after `2026-09-10_rejudge_2_3_4.md` (COMPLETED on the graph). Blocks the operator's read of the L0 PDF.
**Spend:** zero model calls. **Network: none.** A test asserts the socket counter is zero for the whole task.

**Why this task exists.** The rebuilt PDF's prose quotes cycle 3 re-judged (A1 n=15, upper95 0.203883) while its figures still draw cycle 3 as measured (n=16, 0.1936), because decision 5 of the previous task could not run under its decision 2. A report whose text and figures disagree on the same leg is not a read that ships. Separately, six Results carry Tier C values under host-family names because `build_l0_matrices.leg_results` emits one name for three families.

**Decisions taken here (operator overrides later):**
1. **Figures resolve a re-judged cycle's unchanged numerals through the cycle it was measured in.** `figures.py`, given `--cycle scan_2026-09-09_rj1`, looks up `<name>_2026-09-09_rj1` first; if absent, it falls back to `<name>_2026-09-09` **only if** `state/rejudgement_registration_2026-09-10.json` or `state/l0_rejudged_registration_2026-09-10.json` lists that name as compared-and-unchanged. A name that is neither registered under the `_rj` suffix nor listed as unchanged is a hard error, never a silent fallback. The fallback is evidence-bound: it reads the comparison record, not a naming convention. Decision 2 of the previous task stands: nothing unchanged is registered.
2. **`build_l0_matrices.leg_results` emits family-prefixed names**: `scan_l0_host_leg_rate_<leg>_<stat>_<cycle>`, `scan_l0_product_leg_rate_<leg>_<stat>_<cycle>`, `scan_l0_tierc_leg_rate_<leg>_<stat>_<cycle>`. A test asserts no two families emit the same name for any cycle. The unprefixed `scan_leg_rate_<leg>_<stat>_<cycle>` names already registered are not touched (AD-028); they remain the host-family originals they always were, and report tags that point at an unchanged one stay. New emission from this task forward uses the prefixed names only; the cycle-4 report revision will register under them.
3. **The six misbound Results are superseded, not corrected.** For each of `a4`, `a5`, `a10`, `a11_declared`, `a12`, `g1_d`: register `scan_l0_tierc_leg_rate_<leg>_upper95_2026-09-09_rj1` at the value the RESULT §1 table says it should be, with a description that names the misbound Result it supersedes and states the cause (Tier C value registered under a host-family name). This is a first registration of Tier C for cycle 3, not a duplicate. If the Result state machine has a state for superseded or retracted, walk the six to it; if it does not, the supersession pointer in the new description and the pin in `tests/test_rejudgement_2_3_4.py` are the record, and the RESULT says which of the two happened. `test_no_report_tag_quotes_a_misbound_result` is extended to figure inputs.
4. **The registrar takes the FIRST emitter per name** (already fixed in the previous task) and now refuses to register any unprefixed `scan_leg_rate_*` name at all, so the collision cannot recur under a different caller.
5. **Figures and the graph page are rendered from `scan_2026-09-09_rj1`** under decision 1, and cycle 4 enters the graph page from `scan_2026-09-10_rj1`. The PDF is rebuilt through `make report-pdf`. No prose changes except a `{{result}}` tag re-pointed where decision 2 or 3 makes the prefixed name the correct one.

**Zero edits to:** rule modules, harness, stored payloads, prior Results, prior RESULTs, cycle evidence, targets, report prose beyond a tag re-point.

**Immutable once written. Glob `2026-09-10_l0_figures_and_leg_rate_names_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 2, 3, 4 (registry). Write the prefix, the collision test, the refusal, the six supersessions. Stop if any of the six values in RESULT §1 does not reproduce from `build_l0_matrices` on `state/scan_2026-09-09_rj1.json` to six decimals; the number in the RESULT is a claim, and this step is where it gets checked.
## 2. Decisions 1, 5 (figures). Write the evidence-bound fallback with a test that feeds it a name missing from both the `_rj` registry and the unchanged list and asserts a hard error. Render figures and graph page. Rebuild the PDF.
## 3. Gate (the one gate of this task)
Every figure numeral resolves through a registered Result or an evidence-bound fallback, 0 hard errors; a new test `test_report_text_and_figures_agree_per_leg` asserts that for every leg quoted in both prose and a figure, the two resolve to the same Result value (this is the clause that makes the PDF a read that ships); the family-collision test; the unprefixed-name refusal test; the six supersessions present with correct values and pointers; `test_no_report_tag_quotes_a_misbound_result` green over prose and figures; PDF numeral-multiset gate; socket counter 0; `make gate-task` (registry changed); `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes no Results and no PDF: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names_RESULT.md`: which figures changed and by what values, leg by leg; every fallback the figures took, by name, with the unchanged-list line that licensed each; the six supersessions; whether the Result state machine had a superseded state; every premise wrong. `seldon cc complete`, commit, push. Final message states the PDF path and whether the push succeeded.

**SEQUENCING:** §1 (stop on a value that does not reproduce) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
