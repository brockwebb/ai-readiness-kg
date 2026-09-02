# CC Task — Assemble the complete FSS AI Data Readiness specification package

**Date:** 2026-06-23
**Type:** Assemble + audit (consolidate existing content into the complete team-facing spec; dogfood the glossary from the verified vocabulary)
**Project dir:** `/Users/brock/GitHub/brock_projects/ai-readiness-fss`
**Target file:** `fss_ai_readiness_assessment.md` (rewrite in place — this becomes THE deliverable)

---

## Purpose

The current `fss_ai_readiness_assessment.md` is missing two constituents that make it a complete specification rather than a partial draft. This task adds them and reorders to the intended structure. The deliverable is a single self-contained document a review team uses to evaluate whether this is the right instrument: it must state what the task is, why we're doing it, why the two-instrument design, the instruments themselves, and the reference material (definition + glossary) that makes the terms unambiguous.

**Core principle being enforced — this is real dogfooding:** the FSS asked for definitions *because people don't understand the terms.* A spec that uses AI terms without defining them reproduces the exact comprehension gap the definitions were meant to close. We built a knowledge-graph-derived vocabulary; this task makes the document USE it. Glossary entries come FROM the verified vocabulary artifact, never hand-written, never paraphrased into drift.

---

## Inputs (read both)

1. **Target/source content:** `/Users/brock/GitHub/brock_projects/ai-readiness-fss/fss_ai_readiness_assessment.md` (current draft — all instrument content is correct, keep it; restructure and add around it).
2. **Vocabulary artifact (DIFFERENT repo):** `/Users/brock/Documents/GitHub/icsp_notebook/corpus/vocab/fss_ai_vocabulary.json` — 43 terms, verified, provenance-bearing. Source of the glossary AND the AI-ready data definition. The flagship record `AI-ready data` carries the Part A (grounded, content-side) definition + Part B (dated access-axis `forward_interpretation`, `author_framing`) + provenance (BEA RFS `bea_rfs_mlmu25`, FCSM 25-03, OPEN Government Data Act, Lawrence DRL ancestor). Pull definition text and provenance verbatim from this record.

---

## Required output structure (reorder to this)

1. **Title + one-line purpose.**
2. **Task & purpose** — what this is (a specification for an FSS AI data readiness assessment), who it's for (the review team), what we're asking them to evaluate (is this the right instrument and the right questions).
3. **Why we're doing it** — brief: OMB mandate context; the deeper reason measurement needs a shared definition (if we can't agree on what AI readiness *means*, measurement is meaningless — state this explicitly, it is the load-bearing justification for including the definition).
4. **The adopted definition (with provenance)** — THIS IS NEW, pull from the `AI-ready data` vocab record:
   - Part A — the grounded, content-side definition (the adoptable core). State it.
   - Part B — the access-axis extension, clearly marked as dated forward interpretation (`author_framing`, 2026-06), not a ratified standard.
   - Provenance line — name the federal sources (BEA RFS, FCSM 25-03, OPEN Government Data Act) so the definition reads as *adopted from federal sources and extended*, not coined. This provenance is what makes the measurement authoritative; do not drop it.
   - One sentence connecting definition→instrument: the machine diagnostic measures Part A (content-side, established) as the core and reports Part B (access-side, emerging) on a separate frontier track — so the instrument's structure directly mirrors the definition.
5. **Justification of the two-instrument design** — the existing Preface content (machine vs. survey, route-to-lowest-burden-knower, cross-checks as payload, scope boundary, join key). Keep substantially as-is.
6. **Part 1 — Machine diagnostic** (keep as-is).
7. **Part 2 — Agency roll-up survey** (keep as-is).
8. **Part 3 — Practitioner survey** (keep as-is).
9. **Appendix A — Glossary** — NEW (see audit below).
10. **Appendix B — Design principles** (keep existing list).
11. **Open items (internal)** (keep).

---

## The glossary audit (the dogfooding constraint — do this rigorously)

**Rule: the glossary contains ONLY terms that actually appear in Part 1, 2, or 3 of this document. Nothing aspirational, nothing from the broader vocabulary that isn't used here. Closed loop both directions.**

Procedure:
1. **Extract** every AI/technical term used in the machine diagnostic and the two surveys. Candidate list (verify against actual text, add any missed): machine-readable, machine-understandable, content negotiation, metadata standard (DCAT, schema.org, ISO 19115), provenance, structured catalog (data.json), schema, semantic clarity, bulk availability, programmatic access, API, llms.txt, MCP, WebMCP, AI-ready data, AI readiness, discoverability, retrievability, interpretability.
2. **Match** each extracted term to its record in `fss_ai_vocabulary.json`. Pull the definition (and short provenance tag) FROM the JSON, verbatim or faithfully condensed — do NOT author new definitions.
3. **Flag gaps both ways:**
   - Term used in the instrument but ABSENT from the vocabulary JSON → list under "GLOSSARY GAPS — terms in the instrument with no vocabulary record." Do NOT invent a definition. This is useful signal (vocabulary needs the term, or the instrument should drop it).
   - Do not include vocabulary terms that aren't used in the instrument.
4. Render the matched terms as Appendix A, alphabetical, each: **term — definition (condensed from vocab) — source tag.** Keep definitions tight; this is a reference glossary, not the full vocab record.

---

## Constraints

- **No drift.** Glossary definitions trace to the vocab JSON which traces to verified primaries. Do not paraphrase into new meaning. If condensing, preserve the grounded sense.
- **No fabrication.** A term with no vocab record is flagged, never invented.
- **Keep the instrument lean.** The definition + glossary are reference layers (front-matter definition, appendix glossary). The survey sections people fill out stay exactly as lean as they are now. Lean to use, complete to reference.
- **Render is OPTIONAL and LAST.** Brock does not need the docx now. If everything else is done, a markdown→docx render (`pandoc` or docx skill) may be appended as a final step, but do not block on it and do not let it gate the content assembly.

## Done criteria
- Document follows the 11-part structure above.
- Definition with Part A / Part B / provenance present and traced to the `AI-ready data` vocab record.
- Glossary contains exactly the AI terms used in the instrument, defined from the vocab JSON, alphabetical, with source tags.
- Any instrument term missing from the vocabulary is flagged under GLOSSARY GAPS, not invented.
- Append a `## DONE` block to THIS task file listing: terms glossed, terms flagged as gaps (if any), and whether render was produced.

---

## DONE (2026-06-24)

**Outcome:** `fss_ai_readiness_assessment.md` rewritten in place to the 11-part structure. New: §3 adopted definition (Part A / Part B / provenance, traced to the `AI-ready data` vocab record) and Appendix A glossary + GLOSSARY GAPS. Parts 1–3, design principles, and open items preserved verbatim.

**Glossary audit (closed loop against `fss_ai_vocabulary.json`, 43 terms):**

Terms glossed (have a vocab record, used in Parts 1–3; condensed from vocab, source-tagged, alphabetical):
1. AI (artificial intelligence) — NIST SP 800-218A
2. AI readiness / AI-ready data — America's DataHub RFS MLMU-25 (fn. 2), ext. FCSM 25-03 / 20-04
3. AI use case inventory — OMB M-25-21
4. Machine learning (ML) — NIST SP 800-55v1
5. Provenance — CNSSI 4009-2015; CIPSEA 2018

Terms flagged as GAPS (used in instrument, no vocab record — none invented): machine-readable/machine-understandable; discoverability; retrievability; interpretability (data sense — false-friend flag: vocab's `interpretability` is a surface form of *explainability*/model output, a different sense); content negotiation; structured catalog/`data.json`; metadata standard (DCAT, schema.org, ISO 19115); machine-readable schema; semantic clarity; bulk availability; programmatic access/API; llms.txt; MCP/WebMCP; plus lower-level infra terms (robots.txt, sitemap.xml, versioning, integrity signal/checksum, machine-readable license).

**Dogfooding finding (registered in Appendix A and Open items):** the vocabulary covers AI governance/literacy terms, not the data-access/engineering vocabulary the machine diagnostic runs on. ~5 matched vs ~13 gaps. Recommendation: extend the vocabulary with an FCSM-25-03-sourced data-readiness tier, or document the scope boundary.

**Render:** produced. `pandoc` markdown→docx succeeded; `fss_ai_readiness_assessment.docx` refreshed (22.6 KB).
