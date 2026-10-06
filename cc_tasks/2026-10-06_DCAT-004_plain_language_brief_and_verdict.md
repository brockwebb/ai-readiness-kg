# DCAT-004: the plain-language 101 brief on DCAT-US 3.0, the yes-or-no for statistical uses, what FCSM asked for by outcome, and the live demonstration sheet

**Date:** 2026-10-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session, at the operator's direction of 2026-10-06. DCAT-003 and its addendum produced the FAQ and the evidence attachment, correct and too detailed for the reader who asked. This task produces the short document for that reader and the judgement the colleague's complaint turns on, under a rule written before the judgement was made.
**Implements:** DN-011 ADDENDUM 01, R6 to R9. Reads DN-011 R2 to R5 and DCAT-003's delivery and addendum reports first.
**Framework layer served (DN-005 §5 rule 1):** §2.5, the declared layer against measured behaviour; the brief is a view, and says so.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** 2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability
**Due:** Wednesday 2026-10-07, 18:00 local, for the Thursday meeting.
**Spend:** est. 3M tokens (Opus). Answer and validator calls over about 12 units (eight brief sections, the R6 table rows pooled by need, the demonstration sheet), two fresh-reader calls, one readability pass. Estimate before the run; report estimate and actual.
**Network:** the model CLI; the document-admission path for the named list in decision 1 only; `git push`. No answer text from model memory or the web.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Corpus check, then at most four admissions.** The corpus already holds StatDCAT-AP 1.0.1, DCAT-AP 3, SDMX 3.0 section 1, the SDMX standards overview, the DDI Codebook specification, W3C Data Cube, DQV, DWBP, Wilkinson 2016 and Jacobsen 2020, FCSM 19-01, 20-04, 23-02 and 25-03, and the FAIRness Project record. Admit through `kg/assess.py` and the admission path, under DN-011-R4, only: SDMX 3.0 section 2 (the information model); DDI-CDI (the cross-domain integration specification); UNECE GSIM (the statistical information model); W3C Data on the Web Best Practices is already in. A document that cannot be fetched publicly is declined with the reason in the manifest, never a to-do. Extract what is admitted with the standing pipeline and run the DD-029 acceptance sample on the batch (audit A-07 applies to this cohort).

2. **Evidence per need (R6 question 1 to 3).** For each of the eight statistical needs R6 names, query both graphs by script (reuse `scripts/dcat_faq_evidence.py`; extend, do not fork) and save every hit with its locator to `reports/dcat_us_3_brief/evidence/need_<n>.json`:
   - what FCSM or the project publicly asked for (the wiki, B3.3, the CDOC report, the four FCSM papers);
   - where it sits in 3.0 (the Dataset page as served 2026-10-05, the 2026-09-15 capture, the working draft, the Implementation Guide and Overview on deferral);
   - how the literature carries it (StatDCAT-AP, SDMX, DDI, Data Cube, DQV, DWBP, FAIR, the S-015 crosswalk rows).
   Commit the script.

3. **The R6 table, by rule.** One answer call per need writes the three answers in one sentence each with locators; a validator call checks entailment and responsiveness (DCAT-003 ADDENDUM 01 item 5, with its positive control run first). The outcome letter (A to E) is assigned by code from the three validated answers, never by the model. Where the sequencing plan would be the only source of "asked", the row is E and the brief says the plan is not public. Report rows per outcome.

4. **The yes-or-no (R7)**, computed from the table by the stated rule, for findability and for fitness-for-use separately. The brief prints the answer, the one-sentence grounds, and the row ids.

5. **The brief**, built by code into `reports/dcat_us_3_brief/BRIEF.md` and `BRIEF.pdf`, one to two pages, in this order, each section an answer call over that section's evidence with the validator pass:
   1. What DCAT-US 3.0 is, in three sentences a reader with no background can follow (a catalog card for every dataset the government publishes; a US version of a world standard; what agencies must do by 30 September 2026).
   2. Who made it and what FCSM's part was.
   3. Does it deliver for statistics: the two answers from decision 4, with grounds.
   4. What FCSM asked for, by outcome: the R6 table rendered as plain rows (need, asked?, where it landed, what the literature says, outcome), with the five outcomes explained in one sentence each.
   5. The void and the mismatch (outcomes C and D), in plain words, each with the source that says so.
   6. What could happen next, as options the sources support (from FAQ Q13), no recommendation beyond the sources.
   7. What cannot be known from the public record (outcome E rows, and the sequencing plan's status).
   8. Where the detail is (the FAQ and attachment, one line).
   Sources as short citations at the end, the DCAT-003 citation form. The FAQ's answers are evidence for the brief and may be reused where their validator passed; nothing is copied unvalidated.

6. **Plain-language gate (R8).** Run `scripts/dcat_faq_lint.py` on BRIEF.md (fail on pipeline vocabulary, task codes, U+2014); measure Flesch-Kincaid grade on the body with a named implementation and report it against the target of 10; list every acronym with the line of its expansion. Then the fresh-reader gate: a subagent with no project context reads BRIEF.md alone and answers R8's three questions; the task records the answers verbatim and sends any section that produced a wrong answer back once. Report both rounds.

7. **The demonstration sheet (R9).** `reports/dcat_us_3_brief/DEMO.md`: eight questions a listener might ask (at least two per graph, at least two needing both), each with the MCP tool and arguments used, the answer in two sentences, and its locators. Run every one once against the live servers from the task; a question the graphs cannot answer is kept on the sheet with "the graphs do not hold this", because that is a demonstration too.

8. **Register the brief's claims** into `docs/evidence/claims.yaml` under DN-009 d2, one row per R6 table row and per yes-or-no answer, each with its evidence class and locators, so the long report inherits them.

**Write set:** `reports/dcat_us_3_brief/` (BRIEF.md, BRIEF.pdf, DEMO.md, evidence/, run/, build_report.json), `scripts/dcat_brief_*.py`, the extended evidence script, the manifest and extraction records for decision 1 only, `docs/evidence/claims.yaml` (append), the RESULT. Byte-identical: `reports/dcat_us_3_faq/`, every rule and matrix, the framework record.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-06_DCAT-004_plain_language_brief_and_verdict_RESULT.md`, under 60 lines: the two yes-or-no answers with grounds; rows per outcome A to E and the C and D rows in full; admissions made and declined; sentences cut per section, unsupported and non-responsive; readability score; the fresh reader's three answers, both rounds; demonstration questions the graphs could not answer; premises wrong; estimate and actual tokens, and the model. `seldon cc complete`, commit, push.

**SEQUENCING:** corpus check and admissions → acceptance sample → evidence per need → control → R6 table → yes-or-no → brief sections → lint and readability → fresh reader → demonstration sheet → claims register → gate → RESULT → push.
