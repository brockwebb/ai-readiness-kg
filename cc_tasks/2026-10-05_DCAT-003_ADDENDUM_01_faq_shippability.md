# DCAT-003 ADDENDUM 01: make the FAQ shippable to OMB

**Implements:** `docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`, DN-011-R5 (as DCAT-003 does).
**Amends:** `cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md` (completed, commit 1a5e6cc).
**Due:** Wednesday 2026-10-07. The meeting is Thursday 2026-10-08 and the files go out under the operator's name.
**Read first:** DCAT-003 and its delivery report; `reports/dcat_us_3_faq/FAQ.md`; this repository's `CLAUDE.md`.
**Model spend:** at most three answer calls and three validator calls (Q9, Q12, Q13), plus the controls in item 5.
Estimate before the run; report estimate and actual.
**Network:** one item only, item 4: re-fetch the live DCAT-US 3.0 schema pages through the admission path. Nothing
else from the web; no answer text from model memory.

## Why

A Desktop review of FAQ.md at 1a5e6cc found defects the build did not catch. The first breaks a requirement DCAT-003
step 4 stated: "no task codes or pipeline vocabulary in either file".

1. **Pipeline vocabulary in Q14.** The section headed "Documents known to exist that were not available for this
   briefing" prints raw manifest notes. They include `kg/assess.py`, `docs/runbook_document_admission.md`,
   `corpus/layers.yaml`, `CLAUDE.md`, "basis (a)", "PRIOR NOTE, PRESERVED", "Cataloged by kg/catalog.py" and "no
   in-corpus reference points at it".
2. **Q14 does not answer its question.** It was asked to list each gap with the document that would answer it. It
   instead re-copies every per-question "Not found" list in full and does not map any gap to a document. Its prose
   answer repeats Q3.
3. **Repetition.** "The sources do not state" opens about 45 lines.
4. **Em dashes** appear in generated text: the M-25-05 title as rendered, and Q7's prose ("Optional — geographic
   bounding box, next and prev —"). The operator's standing rule is no em dashes in his output.
5. **Currency of tier claims.** Publisher's tier moved: Mandatory on the 2026-08-21 page, Recommended on the
   2026-09-15 Internet Archive capture. Q11 states "publisher, which DCAT-US 3.0 defines as Recommended" with no
   date. Nothing establishes what the live page says on 2026-10-05.
6. **Q13 is thin and partly non-responsive.** Q13 is the "next steps" question, and next steps are half the meeting.
   - It is silent on "raising requirement levels through guidance". Yet Q3's evidence already holds M-25-05's rule
     that agencies update within one year of a schema change.
   - Its StatDCAT-AP sentence (future agent roles) is entailed by its passage but does not answer the question. The
     validator checks entailment, not responsiveness: H-009's faithfulness-versus-coverage split, recurring here.
7. **Draft-era statements read as current.** Q9 and Q12 cite the 2025 Candidate Recommendation's RDF Data Cube
   language next to statements about the published schema. They give no signal that nothing shows the published 3.0
   carries it.
8. **Unpublished source.** Q11 cites "AI-readiness framework for federal statistical publishers, indicator G4" with
   no URL.

## Steps

1. **Q14 rebuilt by code, not by a model call.**
   - **Part A, a gap table.** One row per distinct gap, deduplicated across questions. Columns:
     - the gap in plain words;
     - the questions it affects;
     - the document that would answer it, where one is known, else "none known".
   - Known mappings:
     - The FAIRness Project sequencing plan (provided to OMB, no public copy) answers the Q5 and Q6 gaps on what
       FCSM and the project recommended.
     - Map any other gap only where a catalog record names a document for it.
   - **Part B, documents not used, one plain sentence each:** title, issuer, date, and why it was not used.
     - **Sequencing plan:** "Provided to OMB and not published; a public request for it (DOI-DO/dcat-us issue #214,
       2024-07-15) is open and unanswered."
     - **NGAC April 2024 briefing:** "Public; not reviewed for this briefing." It is public, so "not available" is
       false.
   - Drop the prose paragraph that repeats Q3.
   - Drop the full per-question re-listing, because the table replaces it.
2. **"Not found" phrasing.** Each block's header becomes "Not found in the sources:" and the items are bare clauses
   with no repeated lead-in. This is a template change in the build; it does not touch answer text.
3. **Em dashes.** Remove every U+2014 from both files.
   - In titles, use the issuer's own punctuation. For M-25-05 that is a colon before "Open Government Data Access and
     Management Guidance".
   - In generated answer text, the fix is a re-run (step 5) for Q9, Q12 and Q13. Q7's dash is the one case where a
     deterministic substitution (U+2014 to a colon or comma) is acceptable, because it changes no claim. Record it in
     the delivery report.
4. **Currency.**
   - Fetch the live DCAT-US 3.0 Dataset page and Overview through the document-admission path, as a new dated
     version. A changed page is re-assessable and costs one document.
   - Re-read the requirement level of every Dataset element and rebuild the Q4/Q6 table with a fifth column:
     2026-10-05.
   - Every sentence in FAQ.md that states a tier names the version it reads.
   - Q11's publisher clause is the known case. If the 2026-10-05 page differs from the 2026-09-15 capture on any
     element, report the elements first in the delivery report: the operator may be asked "what is it now".
5. **Re-run Q9, Q12, Q13**, with evidence widened as below and two answer-prompt rules.
   - **Rule 1:** a statement from a draft or Candidate Recommendation says so, and says whether the published schema
     carries it.
   - **Rule 2:** for Q13, each of the three named options (a statistical application profile; raising requirement
     levels through guidance; conformance checking) gets either a sourced sentence or a "Not found" item.
   - **Q13 evidence:** query both graphs for M-25-05's schema-update and inventory-update language, the
     Implementation Guide's governance and versioning passages, and the FAIRness project's post-release governance.
   - **Validator:** add a second question per sentence, "does this sentence answer the question asked?", and cut a
     "no" as an unsupported claim is cut.
   - **Positive control first:** plant one entailed but non-responsive sentence (the current StatDCAT-AP
     agent-roles sentence is the natural plant) and one responsive sentence. The validator must cut the first and
     keep the second before its verdicts are used (methodology 7.6).
6. **Q11's framework citation.** Cite it in plain words as the presenter's own draft framework, unpublished, with
   the indicator text quoted in the attachment.
   - Assumption: the operator wants it shown.
   - If the build cannot quote the indicator text from the graph, cut the sentence instead.
7. **A gate, from this defect.** Add a build-time lint over FAQ.md and ATTACHMENT_evidence.md that fails the build
   on any of:
   - U+2014;
   - a repository path or file extension (`kg/`, `docs/`, `corpus/`, `.py`, `.yaml`, `.md` outside a URL);
   - `CLAUDE.md`, `PRIOR NOTE`, `basis (`, `manifest`, `cataloged`, `assessed mechanically`;
   - a task code (`\b[A-Z]{1,4}-\d{3}\b` outside a citation title, so M-25-05 and FCSM 20-04 stay legal).

   Carry the defect report and date with the rule. Positive control: the lint fails on FAQ.md at 1a5e6cc and passes
   on the rebuilt file.
8. **Close.**
   - Rebuild both PDFs. Suite green. Commit, push, `seldon cc complete`.
   - Delivery report:
     - live-page tier differences first;
     - sentences cut per re-run question, split into unsupported and non-responsive;
     - spend.
   - End by printing this session's token usage.
