# CC Task: evidence map, part 2, prior art for every claim the summary will make

**Date:** 2026-10-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session, under DN-009 decision 8 (prior art before claims; corpus first, web second; nothing cited from memory). Runs after `2026-10-02_evidence_map_record.md`. This task adds `prior_art` entries to `docs/evidence/claims.yaml` and authors no summary text.
**Implements:** DN-009 decisions 2 and 8.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-02_evidence_map_record.md`
**Spend:** est. 4 to 7M tokens (Opus). Web fetches are the cost; keep each to the page that carries the citation.
**Network:** WebSearch and WebFetch for the literature in decision 2 only; `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **The claim set to ground.** Each is a position the operator intends the summary to take. For each: search the corpus first (the 264 admitted documents, through the `ai-readiness-kg` MCP `search_text` and the manifest), then the web. Record the result as a `prior_art` claim with `evidence` entries of kind `document` (corpus doc id and locator) or `citation` (author, year, title, venue, URL, the sentence that establishes the point, under 15 words quoted). Status `prior_art` only when a source establishes the point; otherwise `unsupported` with the searches that failed listed in `note`.
   - **PA1.** Structured metadata on a page does not by itself make data usable by machines; discovery, access, interpretation and fitness for use are each required. Expected: FAIR (Wilkinson et al. 2016, Scientific Data) and its machine-actionability principle; Juran's fitness for use; OMB information quality guidance. Check whether any of these is already in the corpus.
   - **PA2.** A federal agency's flagship data product must be listed in its data.json. Expected: OPEN Government Data Act (Evidence Act Title II, 2019), OMB M-13-13 and Project Open Data schema, DCAT-US. Confirm the obligation's exact wording and cite it; if the fss-policy-kg holds it, cite that graph's document id as well.
   - **PA3.** Optimizing published content for machine readers has a named discipline, descended from search engine optimization. Expected: Aggarwal et al. 2023, "GEO: Generative Engine Optimization"; the llms.txt proposal (2024). Find primary sources.
   - **PA4.** Publishers increasingly restrict AI crawlers, and the public's access through AI tools depends on those restrictions. Expected: Longpre et al. 2024, "Consent in Crisis"; any measured federal-site crawler policy data. Search for a federal-specific source; record its absence if none.
   - **PA5.** External, outside-in measurement of an organization's published surface, tied to prescribed actions, is an existing pattern. Expected: web accessibility audits (WCAG conformance tooling), security posture rating services, the Federal Data Strategy maturity assessment, and any outside-in open-data index (Open Data Barometer, Global Open Data Index). The claim the summary needs is the narrow one: which of these ties each result to an action with an effort estimate, and which do not.
   - **PA6.** Equal weighting with no asserted weights is the defensible default for a composite indicator when no basis for weights exists. Expected: OECD/JRC Handbook on Constructing Composite Indicators (2008), already cited on page H; confirm the corpus holds it and the locator.
   - **PA7.** The reported executive order of 2026-09-29 renaming AI to SI in federal usage. Search for it. If found, record the citation (Federal Register or whitehouse.gov) and the operative wording; if not found, status `unsupported` with the searches listed. The summary's use of the term depends on this row (DN-009 d4).
   - **PA8.** The Department of Commerce definition of AI-ready data, verbatim with citation, and the project's own definition with its record locator, side by side, so the summary can state the delta without characterizing either. Do not evaluate the definitions; record them.
   - **PA9.** Data buried in aggregated spreadsheets is not machine-usable even when published. Expected: the tidy data literature (Wickham 2014, J. Stat. Software), and any data.gov or Federal Data Strategy guidance on machine-readable formats. One source suffices.

2. **No evaluation, no synthesis.** This task records what exists. Sentences such as "this project applies X" are the summary's to write later.

3. **Reader gate (DN-009 d7).** A fresh subagent reads `claims.yaml` only and writes five sentences on which of the summary's positions are already established in the literature and which are not. Quote in the RESULT.

**Write set:** `docs/evidence/claims.yaml` (append `prior_art` and `unsupported` entries only; `record` entries byte-identical), `docs/evidence/sources.bib` (new, one entry per citation), `tests/test_evidence_map.py` (every `citation` entry has a resolvable URL recorded at search time and a bib key), the RESULT. Byte-identical: everything else. No projection; no model call outside the reader gate.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, `tests/test_evidence_map.py`. RESULT `cc_tasks/2026-10-02_evidence_map_prior_art_RESULT.md`, under 60 lines: PA1 to PA9 each with status and the one citation that establishes it, or the searches that failed; which were found in the corpus versus the web; the reader gate's five sentences; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** corpus searches for all nine → web searches for the gaps → bib → tests → reader gate → gate → RESULT → push.
