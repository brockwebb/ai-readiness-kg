# Crosswalk operationalization + brief — evidence verification, acquisitions, citations, writeup

**Date:** 2026-08-29. **Deliverable:** the Monday-reviewable brief plus a fully evidence-linked crosswalk.
**Inputs:** `docs/crosswalk/usafacts_operationalization_skeleton.md` (44 indicators, §1b–§9), `docs/research/kg_construction_methodology.md`, DD-023–DD-026.
**Not a pilot** — no gates registered, no extraction, no judging. `prior_art` obligations here take the form of the citation discipline in §3/§4.

## Preamble (standard)

Glob and read all `_ADDENDUM*.md` siblings of any task you touch. `seldon cc complete cc_tasks/2026-08-29_crosswalk_operationalization.md` before writing the RESULT. Report discrepancies; never reconcile silently. **Zero kg-pipeline model spend:** nothing in this task calls `model_stub`. Admission is rule-based; writing is your own generation.

## 0. Acquisitions (admission only — extraction explicitly forbidden)

For each §9 queue item: check the manifest first (some may be admitted); if absent, fetch the primary source, admit through the normal pipeline (inbox → register → `manifest_add`), recording `primary_url + content_hash + access_date`. Items: FCSM.25.03; Commerce GenerativeAI-Open-Data guidance (Jan 2025); USAFacts AIReadinessForGovernment PDF; USAFacts/Partnership Federal Data Excellence standards; Aggarwal et al. GEO (KDD 2024); MLCommons Croissant spec; NIST AI RMF + GenAI profile; SDMX break-in-series guidance; DDI; DCAT; FAIR (Wilkinson et al. 2016); ODCS spec; one benchmark-contamination survey (pick the most-cited; record the selection rationale); SFV paper (Zenodo 10.5281/zenodo.22111334). Paywalled or unfetchable → record as `acquisition_blocked` with reason; do not substitute a secondary source silently. **No `extraction_request` events for any of these** — extraction waits on v0.3.7.

## 1. Evidence-cell verification (mechanical)

For every cell in the skeleton marked `*corpus: ...*` or "pending admission": resolve to a manifest doc_id or demote to `gap`. Replace prose pointers with `doc_id` references. Report a table: indicator → cell claim → doc_id | gap. Do not fill any `gap` cell with new claims — gaps are demand-pull targets, not homework.

## 2. Tier assignment (mechanical, per §6b rules)

Add a `Tier` column to every indicator table: `public` / `agency_instrumented` / `paid`, assigned by the §6b rules (AUTO on public surface → `public`; DOC requiring agency artifacts → `agency_instrumented`; funded capability → `paid`). Log the rule applied per indicator in the RESULT; ambiguous assignments get one line of reasoning, not a question to the operator.

## 3. References section (applies to skeleton and brief)

Author-date style, one flat list per document, every entry carrying the strongest identifier available in this order: DOI > arXiv ID > stable URL + access date. Internal sources cite task ids and verdict filenames. Three source classes, visually distinguished: (a) admitted corpus documents (doc_id + content_hash), (b) external sources pending admission (URL + access date), (c) internal artifacts (tasks, verdicts, DDs, the SFV DOI). Every claim in both documents must be traceable to exactly one of these classes.

## 4. The brief — `docs/crosswalk/usafacts_operationalization_brief.md`

2–4 pages, audience: USAFacts team + FCSM-adjacent colleagues. Structure: purpose; machine-first stance (§1b); instrument shape (six indicator groups, counts, one exemplar row each — do not reproduce the tables); the 11 feedback items as one paragraph each at most; the novel contribution stated once (consumer-side EVALs: does the AI preserve uncertainty, surface breaks, restate faithfully — producer-surface audits exist, consumer-behavior audits do not); pilot plan and tier sequencing; January milestone.

**Citation and plagiarism rules, binding:**
1. Paraphrase by default. Direct quotes only where exact wording matters, ≤ 25 words, quotation marks, cited to page/section. Never quote the USAFacts guide beyond short attributed phrases.
2. Every non-obvious factual claim carries an inline author-date citation resolving to §3's list. A claim you cannot source gets deleted or explicitly marked as this instrument's position.
3. Characterize criticized sources fairly: before finalizing, re-read each passage of the USAFacts guide that a feedback item targets and confirm the critique responds to what the text says, not a paraphrase of it. The brief goes to its authors.
4. No reproduction of tables, figures, or framework structure from any source; describe and cite.
5. Self-check pass before commit: diff the draft against the admitted source texts for ≥ 8-word unattributed overlaps (mechanical n-gram check is fine); report the check and its result in the RESULT.
6. Numbers from this project cite their verdict file or Result id; pre-erratum numbers (F_upper 0.158 / 0.292) may only appear as the erratum narrative, never as findings (methodology 6.3, rule 7.6).

## 5. Registration and close

Register skeleton and brief as Seldon artifacts (Documentation), linked to this task. Update the skeleton's status line to v0.2 with date. `seldon cc complete`, RESULT with: admission table (§0), evidence-resolution table (§1), tier log (§2), plagiarism-check output (§4.5), commit and push.

## Non-goals (parked, separate tasks)

v0.3.7 contract + extractor arms (ADDENDUM-01 §2–§3); DD-024 instrument-version citation check on the §3b semantic verdicts (rule 7.6); Lane 4 relocation; Lane 2/3 anything; scoring rubric and weights (post-review, operator value input).
