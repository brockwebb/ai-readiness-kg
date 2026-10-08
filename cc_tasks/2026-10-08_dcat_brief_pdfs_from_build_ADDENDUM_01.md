# ADDENDUM 01 to `2026-10-08_dcat_brief_pdfs_from_build.md`: the brief's build adopts the operator-reviewed structure of 8 October

**Date:** 2026-10-08. Desktop session, from the operator's review of BRIEF.pdf (DCAT-005 build). Amends the base task; nothing in it is superseded.

The operator rejected three things in the built brief: the opening methods paragraph ("one model wrote each sentence, two others checked it"), the letter codes A to E that a reader has to decode across the table, and the absence of a bottom line. A hand-edited version answering all three is committed as `reports/dcat_us_3_brief/BRIEF_v2_2026-10-08.md` and `.pdf` (2 pages). It reuses only validated sentences and code-built facts from the DCAT-005 build, plus two operator-directed paragraphs (the proposed next step, and the AI-use statement in the form of FCSM 26-01, "Communicating Generative AI Use in Federal Statistical Products", September 2026).

## Amendments
1. **The build writes v2's structure.** `dcat_brief_build.py` produces BRIEF.md in the order and wording of `BRIEF_v2_2026-10-08.md`: title as a question; byline; a bold bottom line computed by code from the table (count of needs asked, and per level: Mandatory, Recommended, Optional, dropped, not confirmed); sections 1 to 6; the AI-use statement; sources. No methods paragraph at the top.
2. **No letter codes in the brief.** The Result column prints plain labels (Optional only; Optional, form not checked; Recommended; Dropped; Different form; combinations), with a five-line legend under the table. The letters A to E and the R7 verdicts move to ROWS.md, which keeps them for traceability.
3. **The AI-use statement** follows FCSM 26-01's five elements (meaningful contribution; how used; tools with version and dates; human oversight; where to find more) and sits at the end, never at the top. Its model list is generated from the run records (`run/`), not typed.
4. **The proposed next step and the "checking is automated" paragraph** are carried verbatim from v2 as operator-authored text, outside the validator, and marked as such in `build_report.json`.
5. **Gate addition:** the built BRIEF.md must equal `BRIEF_v2_2026-10-08.md` in section order, table rows and bottom-line counts; wording may differ only where a validated sentence was re-checked. Report any difference.
