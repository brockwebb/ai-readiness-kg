# CC Task — the published report cites its sources: a generated per-check source appendix

**Date:** 2026-09-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-11_a3_a10_sources_RESULT.md` §5 and §10 items 4, 5; closes the decision that task left open.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs after `2026-09-11_framework_single_writer.md`. Last content change before publish.
**Spend:** zero model calls. **Network: none.**

**Why this task exists.** Every check in the report is now citable through the graph and no reader of the PDF can follow it. "Citable by a stranger" means a stranger holding the PDF, not one holding Cypher access. A public instrument that describes itself as grounded in standards and cites none of them invites exactly the objection it should be immune to.

**On the scope fence.** The 2026-09-09 fence forbids new sections and new indicators. This appendix is generated from the graph by the report builder, row for row from `report_traceability.measure()`; nothing in it is authored. It adds no claim; it shows where the existing claims come from. That is the fence's purpose served, not breached, and it is recorded here as a judgement.

**Decisions taken here (operator overrides later):**
1. **Appendix "Sources per check", generated.** One row per check the report carries (the six tier-0 legs and A3, and any product leg the prose names): the check, its indicator, each source as a citation, and the locator (best-practice number, principle) read from the indicator's evidence cell. The builder emits it as a generated fragment like the matrices; the report's section files do not gain hand-written rows.
2. **Citation strings come from `corpus/manifest.json` metadata** (author or issuing body, title, year, `primary_url`). A document missing a field renders with what it has and the RESULT lists which fields are missing for which doc_id; nothing is typed to fill a gap.
3. **Numerals in the generated appendix are not hand-typed** and the tag-coverage lint scopes generated fragments out, the way it must already for the matrices. The PDF numeral-multiset gate still runs over the whole document.
4. **A10's `status: stub`.** Read the status vocabulary where the framework defines it; if `stub` means "no admitted source", A10 no longer qualifies and the status moves through `framework_writeback.py` with an event; if it means something the internal draft still governs, it stays and the RESULT says why. Reported, not gated.
5. **Page budget.** The ~7-page target governs prose. The RESULT reports prose pages and total pages separately, prose meaning everything outside the matrices and appendices. If prose alone exceeds 7, nothing is cut here; the number goes to the operator, because a cut is taste.
6. **OMB M-13-13 is not acquired.** DCAT-US is the schema the memorandum mandates and cites its guidance on its face; one hop inside an admitted document is the lineage, and A3 has three sources.

**Zero edits to:** rule modules, harness, payloads, prior Results, prior RESULTs, figures, the skeleton and the record beyond decision 4, report section prose (a `{{fragment}}`-style include for the appendix is the only change to a section file).

**Immutable once written. Glob `2026-09-11_report_sources_appendix_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 2, 3. The generated fragment, the citation rendering, the lint scope. Stop if any row's doc_id is absent from the manifest.
## 2. Decisions 4, 5. Status; page counts. Rebuild through `make report-pdf`.
## 3. Gate (the one gate of this task)
Appendix present in markdown and PDF; every check the report carries has ≥ 1 row and every row's doc_id is in the manifest; A3 and A10 rows carry their locators; tag-coverage lint green with generated fragments scoped; PDF numeral-multiset gate green; `test_report_text_and_figures_agree_per_leg` green; embedded F5 unchanged; prose and total page counts reported; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes no PDF: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-11_report_sources_appendix_RESULT.md`: the appendix as rendered; missing metadata by doc_id; A10's status outcome; prose and total pages; every premise wrong. `seldon cc complete`, commit, push. Final message states the PDF path, prose and total page counts, and whether the push succeeded.

**SEQUENCING:** §1 (stop on a doc_id outside the manifest) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
