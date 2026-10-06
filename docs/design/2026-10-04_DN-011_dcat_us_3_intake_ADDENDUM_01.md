# DN-011 ADDENDUM 01: the plain-language brief, and the pre-registered rule for judging what FCSM asked for

**Date:** 2026-10-06. Desktop session, at the operator's direction. Amends DN-011; R1 to R5 stand. Implemented by
DCAT-004.

## Context

DCAT-003 and its addendum produced the FAQ and the evidence attachment: correct, cited, and too detailed for the
person who asked the question. The operator wants a one-to-two page 101 for a reader who is not technical, with a
yes-or-no answer on whether DCAT-US 3.0 delivers findability and fitness-for-use assessment for statistical uses, and
a judgement on what FCSM asked for. That judgement has more than one honest outcome, and the operator named them
before any of them was looked for. They are written here so the task finds whichever holds rather than the one the
colleague expects.

## Decisions

- **DN-011-R6. The outcome rule for each statistical need, pre-registered.** A statistical need is one of: series,
  dimensions, units of measure, uncertainty (margins of error, coefficients of variation, confidence intervals),
  methodology and provenance, revisions and versions, quality dimensions (FCSM 20-04), restricted-access terms. For
  each need the task records, with locators, the answer to three questions:
  1. **Did FCSM or the FAIRness Project publicly ask for it?** Evidence: the project wiki, the B3.3 slides, the CDOC
     Data Sharing report, FCSM 19-01, 20-04, 23-02, 25-03. The sequencing plan is not public; a need it may have
     asked for is recorded as *not knowable from the public record*, never as asked or not asked.
  2. **Where did it land in 3.0?** Mandatory, Recommended, Optional, dropped, or absent, read from the Dataset page
     as served 2026-10-05 and the working draft; and whether the Implementation Guide or the Overview says it was
     deferred to a later version.
  3. **What does the literature say is the right way to carry it?** StatDCAT-AP, SDMX, DDI, the W3C Data Cube and
     DQV, DWBP, the FAIR principles and their interpretations, ISO/IEC 25012 as already crosswalked in S-015. The
     answer is one of: the literature carries it this way and 3.0 matches; the literature carries it and 3.0 does
     not; the literature carries it differently from what FCSM asked for, with the difference named; the literature
     does not carry it at the catalog layer (it belongs in the data or in documentation, not in metadata).

  From those three answers each need falls into exactly one of five outcomes, decided by the rule and not by the
  writer: **(A) asked and included at Mandatory or Recommended; (B) asked and left Optional, deferred, or dropped;
  (C) not asked, and the literature says it is needed, the void; (D) asked, and the literature says what was asked
  is not the best way to carry it; (E) undeterminable from the public record.** The brief's section on FCSM is a
  table of needs by outcome, and the prose says nothing a row does not support.

- **DN-011-R7. The yes-or-no.** "Does 3.0 deliver findability and fitness-for-use assessment for statistical
  uses?" is answered separately for findability and for fitness-for-use, each as yes, no, or partly, with the one
  sentence of grounds and the rows of the R6 table it rests on. The answer is computed from the table (fitness-for-use
  is *no* if every quality and uncertainty need is in B, C or E; *partly* if at least one is in A), so that a later
  schema change moves the answer by moving the rows.

- **DN-011-R8. The plain-language bar.** The brief is for a reader who is not technical. Every term of art is
  defined in the sentence that first uses it or not used; no acronym appears before its expansion; the lint from
  DCAT-003 ADDENDUM 01 item 7 applies; and a readability score is measured and reported against a declared target
  (Flesch-Kincaid grade 10 or lower on the brief's body, which is the federal plain-language practice and not a
  threshold chosen here). A fresh reader with no project context is given the brief alone and answers three
  questions: what DCAT-US 3.0 is, whether it delivers for statistics, and what FCSM asked for that it does not
  carry. A wrong answer to any of the three sends the section back, once.

- **DN-011-R9. The live demonstration.** Both graphs answer from Claude Desktop in real time through their MCP
  servers (verified 2026-10-06: `fss-policy-kg` and `ai-readiness-kg` both answered a search from this session).
  The task writes a demonstration sheet of eight questions a listener might ask, each run once against the graphs
  with the answer and its locators saved, so that the live demonstration has a known-good set and a fallback if the
  room has no network.

## Prior art

- **External.** Federal plain language guidelines (plainlanguage.gov; the Plain Writing Act of 2010); the
  Flesch-Kincaid grade as the readability measure federal agencies report. For the comparison standard,
  StatDCAT-AP 1.0.1 section 4 (the statistical extension's own gap analysis against DCAT-AP), the SDMX 3.0
  information model, DDI, W3C Data Cube and DQV, and W3C DWBP, all already admitted to this corpus.
- **Internal precedent.** S-015 Part A (the readiness crosswalk adopted W3C's DQV Annex C verbatim rather than
  re-deriving it; the same move applies here to StatDCAT-AP's gap table); DCAT-003 and ADDENDUM 01 (the
  evidence-answer-validator pipeline, the responsiveness check, the lint); DN-009 d7 (the fresh-reader gate). The
  five-outcome rule has no precedent in these repositories; it is new and says so.
