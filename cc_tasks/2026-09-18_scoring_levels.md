# CC Task: the scoring model's second half: a flat view beside the hierarchical one, the A12 criterion applied, and readiness levels as a cumulative ladder

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-18_scoring_model_RESULT.md` Findings 1 to 3, §4 premise 9, and its "Next" list.
**Implements:** DN-005 §2.1(b) in full: the quantitative score (built), the qualitative rubric and the level definitions (this task), and §4 item 5's "the level definitions with it".
**Framework layer served (DN-005 §5 rule 1):** §2.1(b), scoring.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

## 0. What the first scoring task showed, and the prior art for what it did not build

Hierarchical equal weights give a criterion-A leg 1/40 of a body's score and B3 or F4 1/4; F is zero for every body; three bodies score nothing because the harness cannot reach them. None of that is a bug in the model; all of it is a property of one aggregation choice made without a basis, and the Handbook's own remedy is to show the alternative and the divergence rather than pick.

Prior art for the qualitative half, and two of the three are on disk: the JRC *AI Watch: Revisiting Technology Readiness Levels* document is in the manifest (TRL as an ordered, cumulative, gated ladder with a stated test per level); W3C DWBP (on disk) cites the Open Data Barometer and the five-star open data deployment scheme (Berners-Lee, 2010: on the web with an open licence → structured → non-proprietary → URIs → linked), which is a cumulative ladder over exactly the kind of properties this instrument measures; WCAG conformance levels (by reference) are the same shape. A level is earned by passing everything below it, and it is never an average.

**Decisions taken here (operator overrides later):**

1. **A flat view beside the hierarchical one.** `score.py` prints, for every body, both the hierarchical score (unchanged) and a flat score in which every scored leg has equal weight (1/n over legs judged). The grid shows both columns and the rank under each; the sensitivity table gains a row for the flat scheme. The design page's step 6 says: two equal-weight schemes, no basis to prefer either, both shown; a stated priority from the working group or an empirical relation between a leg and use of the data is what would settle it.
2. **A12's promotion criterion is read and applied, not ruled on.** Read DD-054 and `ind:A12.candidate_promotion`. If the criterion is stated in terms the record can evaluate (cycles run, stability of verdict, controls firing), evaluate it against the log and the matrices and print the evaluation. If it is met, promote A12 through the record's writer with the evaluation as the source, and the scored-leg count moves from 14 to 15 in every view. If it is not met, or the criterion is stated as an operator judgment, do nothing to the record and say which.
3. **Readiness levels as a cumulative ladder over legs, derived from the framework's own structure, not authored.** Levels are built by criterion order as the framework already orders them (A discoverability and access, then B semantics, then D terms, then F stability): a body is at level k when every scored leg of every criterion up to k passes outright (the gating view's "outright" count, per criterion). Level 0 is nothing outright; the top level is every scored criterion clear. Level names are the criterion titles from the record, not invented labels. A body with an `error` on a leg of criterion k cannot be placed at k or above and is reported as `≤ k-1 (unobservable at k)`; never rounded up. The ladder is printed beside the two scores.
4. **The qualitative rubric is the ladder plus the per-criterion sentence.** For each level, one sentence generated from the record: which legs a body must pass outright to hold it and which actions (from the prescription layer) close the gap for a body one level down. That sentence is the rubric; nothing is hand-written.
5. **Nothing is published.** The design page and `--explain` grow; no report page, no site payload, no score on the site. A test asserts every level assignment is re-derivable from the printed outright counts, and that no body is placed above a criterion where it has an `error`.

**Write set:** `scripts/score.py`, `tests/test_score.py`, `docs/design/scoring_model.md` (regenerated), the record through the writer only under decision 2, `scripts/check_protected_score.sh` (extended), `seldon_events.jsonl`, the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-18_scoring_levels_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Prior art on disk: the JRC TRL document and DWBP's five-star reference, cited at their sections; DD-054 and A12's promotion field.
## 2. Decisions 1 to 4. Tests first.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_scoring_levels_RESULT.md`: §0 the prior art as found; §1 the 16-body grid with both scores, both ranks and the level; §2 the A12 evaluation and what it did; §3 the ladder definition as generated and the rubric sentences; §4 every premise this task file got wrong; §5 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_manners_status_and_b5_control.md`.
