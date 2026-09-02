# CC Task — Build the clean FSS AI Data Readiness specification document

**Date:** 2026-06-23
**Type:** Author a clean, team-facing deliverable from existing lab-note content
**Project dir:** `/Users/brock/GitHub/brock_projects/ai-readiness-fss`
**Supersedes:** `2026-06-23_assemble_spec_package_with_glossary.md` (cancelled — glossary overreach)

---

## The problem with the current state

`fss_ai_readiness_assessment.md` is a good raw collection but it is a LAB NOTE, not a deliverable: notes inside notes, sidetracks, design-process commentary, too much information, squished tables. It is unusable as a team-facing package in current form. DO NOT DESTROY IT — it is valuable history. Build a NEW file. Preserve the lab note as-is.

## What to build

ONE clean academic document. Output path:
`/Users/brock/GitHub/brock_projects/ai-readiness-fss/FSS_AI_Data_Readiness_Specification.md`

Think business plan, not treatise: state the job, do it, stop. No preaching, no War and Peace. If no one will read it, it failed.

---

## Formatting rules (strict)

- **Plain academic style. NO bold anywhere. No highlights. No emoji. No fat title block.** Bold/highlight in a document is chart junk — banned.
- Section headers only, clean, mapping to Word Heading 1 / Heading 2 / Heading 3. The document title is plain text (a Heading 1), not a styled banner.
- Prose is concise. Where justification helps, a SHORT bulleted list — not paragraphs.
- Question tables: one question per row, with a second column holding a plain-language tooltip/explanation of that question. Keep cell content tight. (Brock will handle final page layout / landscape orientation for wide tables — do not over-engineer spacing, just don't cram.)
- No design-process commentary in the body (no "core vs frontier firewall," no "as_of_date," no "PMT," no covariate machinery). That apparatus stays in the lab note. The clean doc describes WHAT each instrument does and WHY, at the level a federal review team reads.

---

## Required structure

### 1. Introduction (Heading 1, short)
Our task: construct a method to help the Federal Statistical System assess AI data readiness. One short paragraph. State the OMB-context reason briefly. State plainly: a shared definition is the precondition for meaningful measurement.

### 2. What AI data readiness means (Heading 1, short)
- One-to-two sentence working definition (the content-side core: data prepared so AI systems, particularly LLMs, can correctly access, interpret, and use it).
- One line of provenance: adopted and extended from federal sources (BEA RFS / America's DataHub MLMU-25, FCSM 25-03, OPEN Government Data Act).
- One sentence noting any important forward interpretation (access/discoverability as an emerging dimension the current standards do not yet fully cover).
- Pointer: "The full definition appears in the Glossary."
Keep this section SHORT. The long form lives in the glossary.

### 3. Approach: three evidence streams (Heading 1, short)
Frame as ONE assessment package drawing on three complementary evidence sources — NOT two surveys plus a separate tool. Integrated. Short paragraph or short bulleted list:
- Agency-level response — high-level landscape from the top; answered once by the right person (CDO / Statistical Official / CAIO).
- Practitioner survey — the statisticians, mathematical statisticians, data scientists actively working (or trying to work) with the data and tools; lived experience.
- Machine diagnostic — a script that assesses current public-facing web posture for machine usability of public data, and serves as a guide to where resources are needed to improve machine access to public endpoints.
- One line: the three streams cross-check each other (e.g., what a practitioner reports vs. what the diagnostic finds).
- One line noting the agency/practitioner split is deliberate: the agency response alone could mask ground-level problems, so the practitioner stream reaches the people doing the work directly.

### 4. Agency-level response (Heading 1)
Short bulleted rationale (2-4 bullets: what this stream is for, why answered once, why evidence-eliciting). Then the question table (Question | Explanation). Use the R1–R7 items from the lab note. Convert any design-jargon in the "response field" into plain-language explanation in the tooltip column.

### 5. Practitioner survey (Heading 1)
Short bulleted rationale. Then question table (Question | Explanation) from the lab note's P1–P9. Plain-language tooltips.

### 6. Machine diagnostic (Heading 1)
Short bulleted rationale (what it probes, why machine-tested not self-reported, that it's a guide to where resources are needed). Then a clean table of what is checked, grouped by the four plain-language questions: can a machine FIND the data, GET it, UNDERSTAND it, RELY on it. Plain-language explanation per check. Keep the emerging-standards items (llms.txt, MCP/WebMCP) as a short note that these are forward-looking and not counted against an agency — one sentence, no as_of_date machinery.

### 7. Appendix A — Design principles (Heading 1)
The existing design-principles list from the lab note, lightly cleaned. Reference material — do not preach it in the body.

### 8. Appendix B — Glossary (Heading 1)
SHORT. Major communicated terms ONLY — e.g. AI, machine learning, AI data readiness, machine-readable, and at most a few others that genuinely need it. NOT the full 43-term vocabulary. NOT terms like "discoverability" (explain those in the question tooltips instead).
- The AI data readiness entry carries the FULL definition (content-side core + the forward/access interpretation, clearly marked as forward-looking), pulled from the `AI-ready data` record in the vocabulary artifact.
- Pull big-term definitions FROM the vocabulary artifact; do not hand-author. Condense faithfully, no drift.

### 9. References (Heading 1)
APA citation list. SOURCE: the vocabulary artifact already references every document used to build the definitions — build the reference list from the provenance/citations carried in the vocab records that this document actually uses (the glossary terms + the definition sources). If a pre-built APA list is found easily in icsp_notebook, use it; if not, generate from the vocab provenance. Do NOT go spelunking through icsp_notebook docs hunting for a file — the vocab provenance is sufficient and self-contained. Bound the effort; if references are partial, note which and move on.

---

## Inputs
1. `/Users/brock/GitHub/brock_projects/ai-readiness-fss/fss_ai_readiness_assessment.md` (lab note — all instrument content; restructure FROM it, preserve it).
2. `/Users/brock/Documents/GitHub/icsp_notebook/corpus/vocab/fss_ai_vocabulary.json` (definition source for the AI-data-readiness glossary entry + big-term definitions + reference provenance).

## Constraints
- No drift: definitions trace to the vocab artifact. Don't invent meanings.
- Lean: the surveys people fill out stay tight. Definition/glossary/references are reference layers, not body bloat.
- Render OPTIONAL and LAST: Brock does not need docx now. Markdown is the deliverable. If everything else is done, a markdown->docx conversion may be appended, but never block on it.

## Done criteria
- New clean file at the output path; lab note untouched.
- Follows the 9-part structure; plain formatting; zero bold; Word-mappable headings.
- Question tables have a plain-language explanation column.
- Glossary is short (major terms only) and carries the full AI-data-readiness definition.
- References built from vocab provenance; partial-ness noted if any.
- Append `## DONE` to THIS task file: sections produced, glossary terms included, references status, render y/n.

---

## DONE (2026-06-24)

New clean deliverable created: `FSS_AI_Data_Readiness_Specification.md`. Lab note (`fss_ai_readiness_assessment.md`) left untouched.

Sections produced (all 9, plain academic style, zero bold, Word-mappable headings — title + sections at Heading 1, machine-diagnostic groups at Heading 2):
1. Introduction (OMB context; shared definition as precondition for measurement)
2. What AI data readiness means (short; provenance one-liner; forward-interpretation one-liner; pointer to glossary)
3. Approach: three evidence streams (integrated package framing; cross-check + agency/practitioner-split lines)
4. Agency-level response (R1–R7 as Question | Explanation; response-field jargon converted to plain tooltips)
5. Practitioner survey (P1–P9 as Question | Explanation)
6. Machine diagnostic (four plain-language groups: FIND / GET / UNDERSTAND / RELY, each a Check | What it means table; one-sentence forward-standards note for llms.txt and MCP/WebMCP, not counted against agencies)
7. Appendix A — Design principles (10-item list, debolded, lightly cleaned)
8. Appendix B — Glossary (short)
9. References (APA)

Glossary terms included (major terms only; pulled/condensed from the vocabulary artifact, no drift): AI (artificial intelligence); machine learning; machine-readable and machine-understandable; provenance; AI data readiness (carries the full definition — content-side core plus the forward/access interpretation, marked forward-looking, from the `AI-ready data` record). Lower-level terms such as discoverability/retrievability are explained in the question tooltips, not the glossary, per spec.

References status: built from the vocab provenance for the sources this document uses (AI def, ML def, AI-readiness sources, provenance sources, OMB mandate). PARTIAL where noted — NIST SP 800-218A and SP 800-55v1 are carried in the vocab only as document identifiers (no separate title/year), so those two entries are cited by identifier + DOI and flagged partial in the References lead note. No spelunking through icsp_notebook performed; vocab provenance was sufficient.

Render: NO (markdown is the deliverable; render is optional and not produced, per task).
