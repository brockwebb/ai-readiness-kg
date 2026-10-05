# DCAT-003: DCAT-US 3.0 FAQ for the operator's meeting, answered from both graphs, every claim cited and checked

**Implements:** `docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`, DN-011-R5.
**Due:** Wednesday 2026-10-07, for the Thursday 2026-10-08 meeting.
**Starts after:** DCAT-001 (icsp_notebook) and DCAT-002 (this repository) are merged. Check both on main first; if
either is missing, stop and report.
**Read first:** DN-011; both delivery reports; this repository's `CLAUDE.md`. Glob and read sibling
`*DCAT-003*ADDENDUM*.md`.
**Model spend:** one answer call and one independent validator call per question, about 15 questions. This is small;
estimate it before the run and report estimate and actual.
**Network:** none beyond the model CLI and git push. Answers come from the two graphs (fss-policy-kg and
ai-readiness-kg MCP or their query code), never from the web or model memory.

## The audience and the use

The operator briefs OMB: a 101 on DCAT-US 3.0 and next steps. The complaint in play is that 3.0 does not deliver
findability and fitness-for-use assessment for statistical uses, possibly because the Mandatory elements leave out
what FCSM advocated, and the FCSM people who worked on it have left. He needs answers he can say out loud and hand
over, each backed by the authoritative document.

## Questions

1. What is DCAT-US 3.0, and how does it relate to W3C DCAT 3?
2. Who developed it, and what was FCSM's role (the FAIRness Project)?
3. What does policy require of agencies, and by when (M-25-05, the Evidence Act's inventory requirements)?
4. Which elements are Mandatory, Recommended and Optional, and what did v1.1 require that 3.0 does not?
5. What did FCSM and the FAIRness Project recommend for findability and for assessing fitness for use?
6. Which of those recommendations reached the Mandatory or Recommended tiers, and which did not?
7. What changed between the public working draft and the published schema?
8. How does 3.0 represent data quality, and how does that map to the FCSM Framework for Data Quality (FCSM 20-04)?
9. Can 3.0 carry what statistical users need: series, dimensions, units, uncertainty (margins of error, CVs),
   methodology and revisions?
10. Where do the documents disagree with each other: the schema pages, the Implementation Guide, the M-25-05
    crosswalk, M-25-05 itself, and secondary accounts? Example: the language code is ISO 639-1 per the corrected
    schema page, but BCP 47 in other accounts.
11. How does DCAT-US 3.0 relate to AI readiness of statistical data (FCSM 25-03; the AI-readiness framework's
    indicators)?
12. What did the EU do for statistical data (StatDCAT-AP), and does the US have an equivalent?
13. What options exist for next steps? Examples: a statistical application profile; raising requirement levels
    through guidance; conformance checking. State what each source supports. Do not recommend beyond the sources.
14. What questions can the current sources not answer? List each, with the document that would answer it if one is
    known.

## Steps

1. **Evidence per question.**
   - Query both graphs (definitions, obligations, segments, sections, the framework records).
   - Save every hit with its locator (document id, section or segment id, verbatim text) to
     `reports/dcat_us_3_faq/evidence/Q<n>.json`.
   - Run the queries by script, and commit the script.
2. **Answers.**
   - One call per question writes a summary answer of three sentences or fewer, using only that question's evidence
     file.
   - Each claim carries its locator.
   - Where the evidence does not support an answer, the answer says what is not known and stops.
3. **Check.**
   - A separate validator call per question sees only the evidence and the answer, and marks each claim supported or
     not.
   - An unsupported claim is cut, never reworded to fit.
   - Report claims cut per question.
4. **Build by code** into `reports/dcat_us_3_faq/`, never gitignored:
   - `FAQ.md` and `FAQ.pdf`: each question, the summary answer, and its sources as short citations (title, issuer,
     date, section, URL).
   - `ATTACHMENT_evidence.md` and `ATTACHMENT_evidence.pdf`: per question, the verbatim passages with locators, and the
     table for Q4 and Q6 (element, v1.1 status, 3.0 level, recommended by FCSM or the FAIRness Project with source).
   - Plain language, the exact word, no task codes or pipeline vocabulary in either file.
5. **Close.**
   - Suite green, commit, push, `seldon cc complete`.
   - Delivery report: questions answered, questions with gaps, claims cut, spend.
   - End by printing this session's token usage.
