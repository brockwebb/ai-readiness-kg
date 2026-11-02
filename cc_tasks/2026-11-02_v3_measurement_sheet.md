# CC Task: V3, the measurement sheet: every check rendered as a measurement specification from the record

**Date:** 2026-11-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** DN-019 (`docs/design/2026-11-02_DN-019_measurement_view_and_the_view_ladder.md`, verified PASS sha256 d2a9152f197b; lands on main in 9af5f624 ADDENDUM_03), DN-015, DN-016.
**Amended by:** none.
**Builds on:** 9af5f624 (one-pager builder and its imported checks), 32e394f1 (roll-up builder, `DESCENDS_FROM` edges).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer, at the implementer's rung.
**Fulfils:** its own ResearchTask.
**After:** 32e394f1
**Model:** author
**Spend:** est. 0.8M tokens, Claude Code session included. One role. The task ends by printing its own session usage.
**Parts:** A 0.15, B 0.65, C 0.20.
**Part map:** A fetches the two measurement-theory sources into the corpus; B is the V3 build product; C is the gate and RESULT.
**Network:** allowlist: www.iso.org, www.cs.umd.edu, doi.org, api.openalex.org

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Step 0

1. Confirm 32e394f1 `completed`, `projection_gate.status: green`, DN-019 present at `docs/design/` on main with a PASS verdict for its bytes; quote all three.
2. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.
3. Read DN-019 §3 (the field table) and §4 (the ladder). The field table is the column specification; nothing is added to it or renamed.

## Vocabulary and style

As the one-pager task. "TEVV" may appear at V3 only, spelled out on first use as "test, evaluation, verification and validation". Check codes may appear at V3 (this is the implementer's rung), once per row, beside the plain name.

## Part A: the two sources into the corpus

DN-019 cites ISO/IEC/IEEE 15939:2017 and Basili, Caldiera and Rombach (1994) unverified. Through the project's admission machinery (manifest entry, fetch, docling, biblio cache), admit what is publicly fetchable: the ISO catalogue page and abstract for 15939:2017 (the standard itself is paywalled; the manifest entry records that and admits the abstract page only), and the GQM chapter from the authors' public copy at the University of Maryland or an OpenAlex-resolved open version. A source that cannot be fetched publicly is declined in the manifest with the reason, per the corpus rule. Quote the manifest entries and the docling line counts. Then `seldon prior-art verify` DN-019 again; its verdict is unchanged (the receipts are the search, not the sources), and the RESULT says which citation is now backed by a corpus document and which remains abstract-only.

## Part B: the measurement sheet

`scripts/measurement_sheet_build.py`, patterned on `sixteen_checks_build.py` (checks imported). Outputs `reports/diagnostic/measurement_sheet/Readiness_Diagnostic_V3_Measurements.md`, `.docx`, `.pdf` (PDF from the Markdown by the script; Markdown sha256 beside the PDF in the build report). Portrait, Calibri, body 10pt, one check per page section with a heading `n. <plain name> (<code>)`, and under it a two-column table: DN-019 §3's "Field, as rendered" column verbatim as the row labels, the record property's value as the cell. A property that is empty or absent renders as "not specified", and the build report counts them per field and per check. The page header carries "V3 of the readiness diagnostic; V2 is the sixteen-check page, V1 the criteria roll-up" (DN-019 §4 rule). `rf_requirements` renders as one line per source: the source document's title from the biblio cache, then the quote in quotation marks. `rf_standards_urls` renders as the URLs. `collector_pin` renders beside the collector. The client row reads from `rf_rung_two_changes`: "standard user" when it is empty, otherwise "standard user; API user: " followed by the text.

- check: sixteen sections, in the brief's row order; quote the order.
- check: the count of "not specified" cells, by field and by check; quote the table. Zero is the expected value for `auto` checks; any non-zero count is listed in the RESULT as a record defect for a follow-up task, never filled by this build.
- check: font, colour, vocabulary and dash audits on all three files; quote. The digit audit is relaxed for this rung only in the `signal` and `rf_requirements` cells (they quote standards with numbers); every other cell is audited as the one-pager audits it.
- check: every `rf_requirements` source id resolves in the biblio cache; quote any that does not as a record defect.
- check: a grep of the Markdown for U+2014 and U+2013 returns zero lines; quote.

Register the three files as build products the way the one-pager was. Commit path-scoped, push.

## Part C: gate and RESULT

`make gate-task` if the record was touched (Part A's corpus admission touches it; so yes), `seldon verify`, protected-paths diff, all to `EXIT=0`. Then `cc_tasks/2026-11-02_v3_measurement_sheet_RESULT.md`: Step 0 quotes; Part A's manifest entries; Part B's five checks; the "not specified" table; premises this task got wrong; gate tier with wall-clocks; session usage against 0.8M. `seldon cc complete`, commit, push.

## Out of scope

The framework's levels in the record and the lineage figure (DN-019 §6 item 2; a task after this one). V0. Any edit to a check's text.
