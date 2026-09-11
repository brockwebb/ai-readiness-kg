# CC Task — F5 stops saying "not measured" about legs that were measured

**Date:** 2026-09-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §8 item 6 and §11 items 2, 4.
**Fulfils:** its own ResearchTask (`seldon cc register`). Precedes the cycle-4 report revision, which would otherwise embed an F5 with eleven blank rows carrying the words DD-055 reserves for a leg nobody judged.
**Spend:** zero model calls. **Network: none.** Renders from registered Results and stored payloads only.

**Why this task exists.** `cycle_over_cycle` asks `if rate_key not in R` before reading. `R` is a `figures.Reads` whose evidence-bound fallback lives in `__getitem__`; `in` is `dict.__contains__` and never consults it. Under "register only what moved" every unmoved leg is absent by name under the re-judged cycle, the membership test says absent, and the row is drawn blank as "not measured". The published graph page shows eleven such rows for cycle 4 re-judged. A leg that was judged and did not move is the opposite of not measured.

**Decisions taken here (operator overrides later):**
1. **`Reads.__contains__` is defined and is equivalent to `__getitem__` not raising**: registered under the cycle's name, or absent and licensed by an unchanged-record to fall back. A test asserts the equivalence over every name in every registration record. This closes the class at the type rather than at the one call site; no caller can hit it again.
2. **A blank F5 row is licensed only by the payload.** "Not measured in this cycle" may be drawn only when the leg has no Finding in the cycle's payload. A test asserts, for every re-judged cycle's F5, that the blank-row set equals the set of legs absent from that payload. Expected after the fix: `scan_2026-09-07b_rj3` exactly `{A1, A3}` (cycle 1 never collected `link_probe`); every other re-judged F5 zero.
3. **Every figure of every re-judged cycle is re-rendered and re-audited**: `scan_2026-09-07_rj1`, `scan_2026-09-07_rj2`, `scan_2026-09-07b_rj1`, `scan_2026-09-07b_rj2`, `scan_2026-09-07b_rj3`, `scan_2026-09-09_rj1`, `scan_2026-09-09_rj2`, `scan_2026-09-10_rj1`, `scan_2026-09-10_rj2`. The published-figure numeral gate runs over all of them; the graph page is re-rendered, still showing `scan_2026-09-10_rj2`. Measured-cycle figures are re-rendered too and a test asserts they are byte-identical to before: the fix must move nothing where nothing was wrong.
4. **`docs/reports/` is not rebuilt.** The RESULT states which F5 file the L0 PDF currently embeds (`figures/scan_2026-09-09/...` per the previous RESULT, which is the measured cycle, not `_rj1`; if so, say whether that was a fallback the `l0_figures` task chose or an unnoticed miss) so the revision task starts from a fact.
5. **A comment beside `ABSENCE_UNDER_PARTIAL_BLINDNESS["scan_2026-09-07"] = 1`** says it is permanent and why (cycle 1 never collected the leg `RULE-A3-v6` reads). One line; not a gate clause.

**Zero edits to:** rule modules, harness runtime (collectors, `runner.py`, `run.py`, `publish.py`, `rederive.py`, `model.py`, `errors.py`, `manners.py`, `stats.py`, `frame.py`, probes, fetcher, fixtures, `params.yaml`), stored payloads, prior Results, prior RESULTs, cycle evidence, targets, registration records, invariant pins, `docs/reports/`.

**Immutable once written. Glob `2026-09-11_f5_membership_through_fallback_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 2, 5. The `__contains__`, the two tests, the comment. Stop if decision 2's test finds a blank row that neither the fallback nor the payload explains: that is a third source of blankness and the RESULT names it first.
## 2. Decision 3, 4. Re-render, re-audit, re-render the page, byte-compare the measured-cycle figures, read the PDF's F5 reference.
## 3. Gate (the one gate of this task)
`__contains__` ≡ `__getitem__` over every recorded name; blank-row set ≡ legs absent from payload for every re-judged F5, with cycle 2 `_rj3` = `{A1, A3}` and all others empty; numeral audit 0 unresolved over every re-rendered figure; measured-cycle figures byte-identical; graph page carries 0 "not measured" rows for judged legs; socket counter 0; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes nothing: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-11_f5_membership_through_fallback_RESULT.md`: blank rows before and after per figure; which F5 file the L0 PDF embeds and why; every premise wrong. `seldon cc complete`, commit, push. Final message states the blank-row counts and whether the push succeeded.

**SEQUENCING:** §1 (stop on unexplained blankness) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
