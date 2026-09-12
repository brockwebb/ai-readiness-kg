# DN-001 — Design note: every check the published report quotes is cited, and the report shows the citation

**Date:** 2026-09-12. Desktop design note; not a task. First numbered design note in this repo; numbering starts here because Seldon AD-030-R9 requires a CC task to cite the decision it implements, and this decision had been made across three task files without one (`2026-09-11_a3_a10_sources`, `2026-09-11_report_sources_appendix`, `2026-09-12_a1_a8_b3_d4_sources`).

## Decision

1. **Citation floor.** Every check whose pass rate the L0 report quotes, by tag or in words, reaches at least one admitted source document in the framework graph (`AssessmentIndicator -[:EVIDENCED_BY]-> Document`, doc_id in `corpus/manifest.json`). The set of checks is read from the report's sections, not typed; `report_traceability` pins it.
2. **The reader can follow it.** The report carries a generated per-check source appendix, one row per (check, admitted source), citation rendered from the manifest, locator read from the indicator's evidence cell. Nothing in it is authored. It is not a new section under the 2026-09-09 scope fence: it adds no claim; it shows where the existing claims come from.
3. **An uncited check is printed as uncited.** A row reading "no admitted source" is a true statement and is publishable. One task closes the gap for the checks found uncited on 2026-09-11 (A1, A8, B3, D4); after it, the report publishes whatever the appendix says. A check that still has no admitted source is not a blocker; a false citation would be.
4. **Corpus before web** (DD-003's search order). Locators are verified from the document's text, never from its title; a best practice whose title fits and whose content does not is rejected on reading. Acquisition of a document not in the corpus goes through `kg/manifest.py add`, the Dixie sweep, `rebuild`, and the projection, with `acquisition.acquired_at` set.
5. **Edges enter through the single writer.** Evidence cells in the skeleton, carried by `framework_writeback_evidence.py` through `framework_writeback.save`, which refuses drops and logs the delta; no node or edge created by hand.

## Why

DD-001: the provenance chain must survive handing the repo to a stranger. A stranger holding the PDF does not hold Cypher access; "citable through the graph" is not "citable". The instrument describes itself as grounded in standards; a check with no source is the objection it should be immune to.

## Governs

`cc_tasks/2026-09-12_a1_a8_b3_d4_sources.md` and any later task that adds a check to the report or a source to a check.
