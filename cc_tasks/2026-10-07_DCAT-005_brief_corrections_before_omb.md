# DCAT-005: four corrections to the DCAT-US 3.0 brief before it goes to OMB: the asked column read in full, R7 applied as written, the void stated as the rule's limit, and 3.0 cited from its published pages only

**Date:** 2026-10-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from a mid-run read of `reports/dcat_us_3_brief/` (BRIEF.md, brief_config.yaml, evidence/) at 14:10Z while DCAT-004 v2 (a591e8b3) was still running. Each defect below is quoted from those files; re-read them from the DCAT-004 v2 RESULT's final commit before acting, and drop any item the final brief already fixed (say so in the RESULT).
**Implements:** DN-011 ADDENDUM 01, R6 and R7 as written; DN-012 d1 (no absence verdict over a partial search).
**Framework layer served (DN-005 §5 rule 1):** §2.5, the declared layer against measured behaviour; the brief is a view.
**Fulfils:** its own ResearchTask. **Launched by the operator**, not the dispatcher: it must run before the queued tasks and the dispatcher takes eligible tasks in registration order. It carries no Spend or Network header on purpose (DN-006 decision 3).
**After:** 2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict
**Launch:** when the DCAT-004 v2 RESULT is committed: `touch .seldon/DISPATCH_STOP`, wait for the lease to clear, paste the dispatch line; the session removes the STOP at close and records both times. Estimated 1.5M tokens (Opus): about 12 reading calls for decision 1, the changed sections re-written and re-validated, one fresh-reader round. Network: none beyond the model CLI and `git push`.
**Due:** before the Thursday 2026-10-08 meeting.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## The defects
1. **"Not in the public record" was reached over a capped search.** Rows 1 (series), 6 (revisions and versions) and 8 (restricted-access terms) say the statistical side's public record does not ask for the need. The absence checks behind them matched 233, 213 and 207 passages and dropped 80, 68 and 57 by cap (`evidence/need_{1,6,8}_absence_r2.json`), and the items they showed mix the landed and literature documents with the asked ones. That is DN-012 d1's defect: an absence claim over a partial search.
2. **R7 was extended, not applied.** R7 as written: fitness-for-use is *no* if every quality and uncertainty need is in B, C or E, *partly* if at least one is in A. `brief_config.yaml` adds "a D row counts as not A" and decides "no if none is in A". Quality dimensions is D and uncertainty is open between A and B, so R7 as written decides neither *no* nor *partly*. The findability answer uses the same extension.
3. **"No need is in outcome C, the void" reads as a finding, and it is a property of the rule.** R6 question 1 records a need the unpublished sequencing plan may have asked for as not knowable, never as not asked. While the plan is unpublished, no need can be shown not asked, so C cannot be reached from the public record. An OMB reader will hear "there is no void", which is the opposite of what the record can say.
4. **The 2025 working draft is cited as 3.0.** Source [1] is the 2025 Candidate Recommendation Snapshot. Rows 4 (uncertainty) and 6 cite it for "3.0 does too", and row 4's landed column says "Not confirmed" while its literature column says 3.0 carries it: the row contradicts itself.

## Decisions
1. **Read the asked record in full for rows 1, 6 and 8.** Over the eight asked documents only (the scope in `brief_config.yaml` `scopes.asked`), select every passage matching the need's `asked` terms, with no cap, and read all of them across as many calls as the per-call budget needs. Each need ends `asked` (with the locator of the ask), or `not_found_in_full_read` (every matched passage read, none asks). Under R6 question 1 the second still maps to E, because the plan may have asked; the brief says the public documents were read in full and do not ask, and that the plan is the reason the letter is E. An `asked` need is re-placed under the outcome rule; report any letter that moves.
2. **Apply R7 as written.** Compute each answer by R7's two clauses only. When neither clause holds, the answer is "the rule does not decide", followed by the rows that leave it open and what each would need to become for the rule to decide. Do not add a clause; if the operator wants D counted, that is a DN-011 amendment, not this task. Recompute the fresh reader's pre-registered Q2 key from the new answers before the reader runs.
3. **State the void as the rule's limit.** Section 5 drops "No need is in outcome C, the void" and says, in plain words, that whether the statistical side left a need out cannot be shown from the public record while the plan that held its recommendations is unpublished, and names the rows it would apply to.
4. **Cite 3.0 from its published pages.** Every "3.0 carries", "3.0 does not", level and landed claim cites the published pages (the Dataset page as served 5 October 2026, the Overview, the Implementation Guide, the supporting-class pages). The 2025 Candidate Recommendation Snapshot is cited only as "the 2025 working draft", for draft-versus-final statements. Re-place row 4 from the published pages; if it is still open, say open.
5. **Two pages.** The body (excluding sources) at or under 900 words. Cut repetition first; keep every table row.
6. **Re-run the gates** on every changed section: the validator pass with its control, `scripts/dcat_faq_lint.py`, the readability measure, and the fresh reader once. Append superseding rows to `docs/evidence/claims.yaml` for every changed table row and both answers; never edit a prior row.

**Write set:** `reports/dcat_us_3_brief/` (BRIEF.md, BRIEF.pdf, ROWS.md, evidence/ new files only, run/, build_report.json), `brief_config.yaml` (a dated amendment block; prior lines untouched), `scripts/dcat_brief_*.py` and `scripts/dcat_faq_evidence.py` (uncapped mode), `docs/evidence/claims.yaml` (append), tests, the RESULT. Byte-identical: `reports/dcat_us_3_faq/`, every rule, matrix and stored payload, the framework record.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb_RESULT.md`, under 50 lines: per defect, fixed or already fixed by DCAT-004 v2; rows 1, 6, 8 with passages matched and read and the verdict; every letter that moved; the two answers as R7 decides them; word count; lint, readability and fresh-reader results; tokens and model. `seldon cc complete`, commit, push, remove the STOP.

**SEQUENCING:** read DCAT-004 v2 RESULT → triage defects → full read (rows 1, 6, 8) → re-place rows → R7 as written → section 5 → citations → trim → gates → claims append → build → RESULT → push → remove STOP.
