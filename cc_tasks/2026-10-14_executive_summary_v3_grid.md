# CC Task: executive summary v3: page two is the agency grid, every name is plain, the prose is direct

**Date:** 2026-10-14
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** `docs/design/2026-10-12_DN-014_executive_summary_brief.md` (DN-014), DN-010, DN-001.
**Amended by:** DN-014 ADDENDUM 01 (dated 2026-10-14, beside DN-014); where it and DN-014 differ, the addendum governs. It is untracked and unverified at registration; Step 0 verifies it before anything else, and the task stops if that fails.
**Builds on:** task 14d163b7 (v2) and its RESULT: the discoverability decision, the vocabulary entries, the capability table, the build script and the checks all stand. This task changes page two, the names, and the prose. It does not redo Steps 1 to 3 of v2.
**Framework layer served (DN-005 §5 rule 1):** §2.1, the summary as a view of the framework.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Model:** author
**Spend:** est. 2M tokens. The session writes (role `author`); Fable reads (role `judge`), at most three rounds; the checker (role `critic`) runs the planted and unsupported checks.
**Parts:** A 0.25, B 0.35, C 0.25, D 0.15.
**Part map:** A is the record's plain names; B is the grid; C is the prose and the reading rounds; D is the build and the gate.
**Network:** none.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Step 0

If this task is `in_progress` from an earlier dispatch (a `dispatch_launched` stamp older than this session's), stop. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.

Then the addendum, before any other step: its `## Prior art` section is prose. Run `seldon prior-art search` for each entry (library and internal), replace the prose entries with the receipts, run `seldon prior-art verify` on the file, and commit it path-scoped through the hooks. If the verdict is not PASS, stop and report the verdict; nothing below runs on an unverified note (AD-036-R4). Record the verdict and the commit in the RESULT.

## Part A: plain names in the record (ADDENDUM §3)

Through `scripts/framework_writeback.py` (never a hand edit of `framework/ai_readiness_framework.json`): `display_name` on the three measurement tiers; `plain_name` (at most six words, what a machine met) on every tier-M rule that the grid will show; `fix_line` (one imperative sentence, no codes) on every action those rules' failing outcomes map to. Rules that record a declaration are marked `declared: true` and excluded from the grid. The projection gate must be green after the write-back.

- check: `get_overview` reports `projection_gate.status: green`; quote it.
- check: every grid column has a `plain_name` and every column's fix a `fix_line`; a script lists any missing and exits non-zero if one is.

## Part B: the grid

`scripts/summary_grid.py` reads the cycle of record's product matrix and tier-A matrix, applies ADDENDUM §2 exactly (pass / fail / partial; single-page agencies pass or fail only; declared checks excluded; most-frequent failing outcome chooses the fix line), and writes `reports/summary/grid.json` with, per cell, the agency, the check, the state, and the locators of the matrix cells it was computed from. The build renders the grid from that file: 16 named rows alphabetical, page count in the label where more than one, plain-name column heads, a glyph in every cell plus color (pass blue, fail red, partial lighter), the fix line under each column, the legend, the three-sentence footnote. Landscape page if it needs one.

- check: a round-trip test recomputes ten random cells from the matrices by hand and matches `grid.json`.
- check: every grid cell carries at least one locator, and `seldon verify` accepts them.
- check: no digit appears on page two outside the row labels' page counts and the footnote's date.

## Part C: the prose (ADDENDUM §4)

Rewrite page one in `reports/summary/summary_source.yaml`: drop the opening definition paragraph and the pointer to the appendix; drop the appendix definition and its source paragraph (the source list stays); at most three sentences per section; direct register. Fable reads as in v2 with the fifth question added: name every term a CIO new to SI would not know; a term named in two rounds is replaced. The planted-sentence and unsupported-sentence checks run as before.

- check: the text check word list gains the tier letters and every rule and indicator code; it returns zero findings on both pages; quote its output.
- judgment: Fable's last round says the 30-second bullets can be said from page one alone and names no unknown term. Quote it.

## Part D: build and gate

`reports/summary/SUMMARY.md` and `SUMMARY.pdf` rebuilt by the writing script. Body: page one prose, page two grid, exactly two pages; sources after. Keep the v2 output as `reports/summary/v2/` for the record.

- check: pypdf body page count is 2; quote.
- check: `make gate-task` (passed, skipped, xfailed, deselected, wall clock), `seldon verify`, protected-paths diff empty.

## RESULT

Under 40 lines: served model; the plain-name counts written; the grid's state counts (how many pass, fail, partial cells, and how many agencies have more than one page); which checks were excluded as declared; Fable's rounds one line each; page count; text check; gates; premises found wrong. Then `seldon cc complete`, commit, push. The operator reads `reports/summary/SUMMARY.pdf`.
