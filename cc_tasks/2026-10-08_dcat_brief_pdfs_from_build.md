# CC Task: the DCAT brief's build renders ROWS.pdf and DEMO.pdf, replacing the hand-built copies; "Optional" is glossed in code-built text; every reader-facing report ships a PDF from its own build

**Date:** 2026-10-08
**Project:** ai-readiness-kg
**Authored by:** Desktop session. The operator reads PDFs, not Markdown. On 2026-10-08 a Desktop session converted `reports/dcat_us_3_brief/ROWS.md` and `DEMO.md` by hand (pandoc + wkhtmltopdf, from `397373a0`) and committed them with a footer saying so. Nothing regenerates them, which is the staleness class of 34ccb843. DCAT-005's fresh reader read "Optional" as "carried" (its RESULT §4), and the gloss belongs in the code-built lines, not in a model sentence.
**Implements:** the operator's stated reading format; 34ccb843 (no committed build product without a generator), for this report.
**Framework layer served (DN-005 §5 rule 1):** none (hygiene; a view's format).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** zero model calls. Code, two renders, the fast gate.
**Network:** none beyond git push.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions
1. **The build renders both.** `scripts/dcat_brief_build.py` renders `ROWS.pdf` from `ROWS.md` and `DEMO.pdf` from `DEMO.md` through its own `render_pdf` (pandoc + typst), landscape for ROWS if its table overflows portrait, and overwrites the hand-built copies. No script writes `DEMO.md` today; the build renders it when present and says so in `build_report.json`. A test asserts that after a build each PDF exists, is newer than its Markdown, and that every `##` heading of the Markdown appears in the PDF's text.
2. **"Optional" glossed once, in code-built text only.** The first code-built use of "Optional" in BRIEF.md and in ROWS.md reads "Optional (agencies may leave it out)", and outcome B's definition says the same. No model-written or validated sentence changes. Rebuild BRIEF.pdf; `scripts/dcat_faq_lint.py` stays at 0; report the body word count against the 900 cap.
3. **A standing convention in `CLAUDE.md`** under "Conventions specific to this repo": every reader-facing report under `reports/` ships a PDF rendered by the same script that writes its Markdown; Markdown is the source, the PDF is what the operator reads; a task whose deliverable is a report lists the PDF in its write set and its RESULT names the PDF path.

**Write set:** `scripts/dcat_brief_build.py`, `reports/dcat_us_3_brief/{BRIEF,ROWS}.md` (code-built lines only), `{BRIEF,ROWS,DEMO}.pdf`, `build_report.json`, `tests/test_dcat_brief.py`, `CLAUDE.md` (the one convention), the RESULT. Byte-identical: `answers.json`, `evidence/`, `run/`, `brief_config.yaml`, `docs/evidence/claims.yaml`, `reports/dcat_us_3_faq/`, every rule and matrix.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-08_dcat_brief_pdfs_from_build_RESULT.md`, under 25 lines: the three PDF paths with page counts, the gloss lines changed, the body word count, the gate lines. `seldon cc complete`, commit, push.

**SEQUENCING:** render path → test → gloss → rebuild → lint → CLAUDE.md → gate → RESULT → push.
