# CC Task — report PDF: the L0 report as a readable PDF, from the pipeline

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session. The operator will read the report as a PDF and not as markdown.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs after `fb2c3172` (virtual time) has pushed; independent of cycle 4.
**Spend:** zero model calls. **Network: none.** Contact no host.

**Decisions taken here (operator overrides later):**
1. **The PDF is a build product, not a hand edit.** `docs/reports/2026-09_fss_ai_readiness_L0.md` is rendered through the existing build (every `{{result:...}}` resolved) to `docs/reports/2026-09_fss_ai_readiness_L0.pdf`. No number is typed. Tooling: pandoc with a PDF engine already on the machine (typst or LaTeX, whichever is installed; say which and pin it in the build), or the repo's existing report pipeline if it already produces PDF. Do not install a new toolchain to do this; report if none is present and stop.
2. **The matrix renders as a table that fits one page** in landscape if needed: 16 rows, six checks, the refusal column, one cell per surface note. If the table cannot fit a page at a readable size, split by tier rather than shrink the type below 9 pt.
3. **The movement figure (F5) is embedded** from the figure file the graph page already builds; no figure is redrawn.
4. **The last matrix row** reads: planned host GitHub Pages under this repository; to be measured on publication. It is not scored.
5. **The 8 flagship declarations** in `docs/design/fss_flagship_declarations.md` are referenced in the future-research section by that file's name and are not applied to any number: the report is cycle 3 and cycle 3 had 9 declared flagships. If the report currently says 7 pending, correct it to the count in the shortlist (8) with the registered Result, or register the count if none exists; say which.

**Zero edits to:** report prose beyond decisions 4 and 5, registered Result values, shipped rule modules, prior RESULTs, cycle evidence.

**Immutable once written. Glob `2026-09-10_report_pdf_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Build
Decisions 1 to 5. The build command lives in the Makefile (or the repo's equivalent) as `report-pdf`, so the next revision is one command.

## 2. Check the rendering
Open the PDF's text layer and confirm: zero unresolved `{{` tokens; every matrix cell present; the figure present; page count reported; fonts embedded.

## 3. Gate (the one gate of this task)
The PDF's text layer, stripped of layout, contains exactly the same numbers as the built markdown (a script diffs the multiset of numerals between the two; zero differences). Fast tier green; `seldon verify`; protected paths.
**Failure: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-10_report_pdf_RESULT.md`: gate first, page count, toolchain pinned, the flagship-pending count decision 5 landed on. `seldon cc complete`, commit, push. Final message states the PDF path, whether the RESULT exists, and whether the push succeeded.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
