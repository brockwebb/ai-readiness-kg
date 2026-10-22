# CC Task: DN-018 lands in the record: one FCSM 20-04 Accessibility concern per check, and the sixteen-check one-pager becomes a build product that renders the concern column

**Date:** 2026-10-21
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** `docs/design/2026-10-21_DN-018_si_readiness_is_fcsm_accessibility_for_a_machine_user.md` (DN-018; verified PASS sha256 bc31ad94892e, committed 4faa1d26), DN-016, DN-015.
**Amended by:** none.
**Builds on:** task b6c65bfe and its RESULT (the sixteen MeasurementSpecs with their `rf_*` plain-language fields, `scripts/apply_instrument_fields.py`, `scripts/diagnostic_package_build.py`); task b694c14a and its RESULT (`scripts/readiness_brief_build.py`: the font, colour, vocabulary, digit and dash checks, and the four-state grid). The hand-built one-pager the operator presented on 2026-10-16 (`Readiness_Diagnostic_16_Checks.docx`, built in a chat sandbox, never committed) is the shape being reproduced; its spec is written out in Part B so nothing depends on that file.
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer: each check is tied to the published quality dimension it operationalizes, and the one-pager is a view of that tie.
**Fulfils:** its own ResearchTask. **Hand-dispatched** by the operator (DN-006 decision 10; `dispatch.enabled` is false and `.seldon/DISPATCH_STOP` is present); not launched by the dispatcher. This task does not change `dispatch.enabled`.
**After:** none
**Model:** author
**Spend:** est. 0.9M tokens, Claude Code session included. The session writes (role `author`); no second model role is used. The task ends by printing its own session usage so estimate and actual can be compared.
**Parts:** A 0.40, B 0.45, C 0.15.
**Part map:** A is the record write-back and projection; B is the one-pager build product; C is the gate and RESULT.
**Network:** none beyond git push.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Step 0

1. `seldon cc register cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md` if the Desktop session's registration did not land (check `seldon task list` for this file's stem first; a second registration is a defect to report, not a step to take). Quote the id.
2. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.
3. Verify and quote: b6c65bfe and b694c14a `completed`; `get_overview` reports `projection_gate.status: green`; the sixteen MeasurementSpecs with `instrument_state` set exist with the codes A1, A2, A3, A4, A5, A6, A8, A9, A10, A11, A12, A13, B3, D1, D4, F4. A seventeenth, or a missing one, stops the task before any write.
4. Read DN-018 in full. The section 4 table is the data for Part A; the section 2 verbatim definition and the section 3 concern wording are the data for the concern nodes. Nothing in this task paraphrases either.

## Vocabulary and style (every rendered word)

As the brief task: *readiness diagnostic*, *check*, *public client*; pass, partial, fail, *not measured*. "Scan", "probe", "crawl", "audit", "ports" and "unmeasurable" appear nowhere. No em dashes or en dashes used as dashes. The word "accessibility" in rendered text appears only as "accessibility in the FCSM data-quality sense" on its first use (DN-018 §2.1); the Section 508 sense is never implied. Plain words; a cell that needs a glossary entry is rewritten instead.

## Part A: the concern nodes and edges in the record

Through `scripts/framework_writeback.py::save` only (single-writer rule), in one write-back:

1. Four `FcsmConcern` nodes, ids `fcsm_20_04_accessibility_c1` to `c4`, each with: `dimension: Accessibility`, `domain: Utility`, `framework: FCSM 20-04`, `text` verbatim from DN-018 §3's table (the crosswalk's Mapping A wording), `source: Webb 2026, doi:10.5281/zenodo.18772590, v2`, `rmf_equivalent: none`. One further property on each, `definition_segment: fcsm_20_04#s389`, naming the fss-policy-kg segment the dimension's definition comes from.
2. One `serves_fcsm_concern` edge from each of the sixteen MeasurementSpecs to its primary concern, with `role: primary`; and one more, `role: also`, where DN-018 §4 lists a second concern (A1, A2, A3, A6, A9, A13, D4). Twenty-three edges in all. The edge table is read from DN-018 §4 by a parser over the Markdown table, not typed into the script; the script fails if the parsed table has other than sixteen rows.
3. `counts` gains `fcsm_concern_nodes` and `serves_fcsm_concern_edges`.

Then `python scripts/load_framework_graph.py`, then `python -m pytest tests/test_framework_projection_roundtrip.py`. A write-back without a green roundtrip is not finished (DD-057).

- check: `framework_writeback` event on disk carries the delta: 4 nodes, 23 edges, 2 counts keys added, 0 removed; quote it.
- check: Cypher over the projection returns 16 MeasurementSpecs each with exactly one `role: primary` edge, and 7 with a `role: also` edge; quote both counts and the query.
- check: `scripts/build_framework_graph.py` over the committed record is a byte-for-byte no-op; quote the diff length (0).
- check: the roundtrip test's passed, skipped, xfailed and deselected counts; quote them.

## Part B: the sixteen-check one-pager as a build product

A new script `scripts/sixteen_checks_build.py`, patterned on `scripts/readiness_brief_build.py` (reuse its checks by import, do not copy them), writing `reports/diagnostic/one_pager/Readiness_Diagnostic_16_Checks.md`, `.docx` and `.pdf`. The PDF is rendered by this script from the Markdown it wrote, and the build report records the Markdown's sha256 beside the PDF path (the `render_report` pattern, task d3de4348). Every cell is a graph query; the script exits non-zero on a missing field.

The page, in order:

1. **Title:** "Readiness diagnostic: the sixteen checks".
2. **Intro, two sentences:** what "Scored" means (a check whose pass line rests on a published source; the four scored checks are read from `instrument_state = specified` and from the scoring model, never typed); and that "not measured" always carries a reason and never counts as a fail.
3. **The table**, sixteen rows in the order A1, A2, A3, A4, A5, A6, A8, A9, A10, A11, A12, A13, B3, D1, D4, F4, six columns:
   - **#**: the row number 1 to 16 (the code is not shown; the brief's numbering is kept so the operator's working group sees the same numbers as on 2026-10-16: quote the brief's row order from `READINESS_BRIEF.md` and use it; if it differs from the order above, the brief's order wins and the RESULT says so).
   - **Check**: `rf_name_brief`.
   - **What we look at**: `rf_where_we_look`, cut to one sentence if longer.
   - **It passes when**: `rf_pass`, one sentence.
   - **Why it matters**: `rf_why_short`.
   - **Quality concern**: the primary `FcsmConcern`'s short label (C1 "find and obtain", C2 "understand", C3 "usable format", C4 "metadata"), with the also-concern in parentheses where present. Column header carries a footnote mark; the footnote is one line: "The concern each check serves in the FCSM Framework for Data Quality (FCSM 20-04), Accessibility dimension, after Webb 2026."
   - Scored rows carry an orange "Scored" tag in the Check cell. No other colour.
4. **Two kinds of user**, two short lines below the table, text from the brief's page one (query the brief's source, do not retype): the standard user (no key) and the API user (free registered key, a person completes an email step).

Layout: one landscape page, Calibri, 10pt body (9.5pt only if 10pt overflows, and the RESULT says which), white background, black or grey text, orange for the Scored tag only. No page two. If the content cannot fit at 9.5pt, the "What we look at" column is shortened by rule (first clause only) before any other change, and the RESULT records the rule used.

Build-product registration: register the three files with `seldon cc register`'s sibling for products or `seldon artifact create` as the project's existing build products are registered (read how `reports/diagnostic/brief/` was registered in b694c14a's RESULT and do the same), so the one-pager is a graph artifact with `generated_by` the script. Commit path-scoped, push.

- check: `.docx` page count is 1 and `.pdf` page count is 1; quote both.
- check: the build's font, colour, vocabulary, digit and dash checks pass on all three files; quote them.
- check: a grep of the Markdown for each banned word, for U+2014 and U+2013, and for "508" returns zero lines; quote it.
- check: the four rows tagged Scored are exactly the four `instrument_state = specified` specs; quote the ids.
- check: the Quality concern column, read back from the `.md`, equals the primary edges in the projection for all sixteen rows; quote the comparison.
- check: the build report lists the Markdown sha256 beside the PDF path; quote the line.

## Part C: gate and RESULT

The write set touches the framework record, so the gate is `make gate-task` (detached, logged, polled), then `seldon verify`, then the protected-paths diff. No RESULT until all three logs carry `EXIT=0`. Then `cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager_RESULT.md`: Step 0 quotes; Part A's four checks; Part B's six checks; premises this task file got wrong, if any; the gate tier run with both wall-clocks; the log paths; the session's own usage against the 0.9M estimate. `seldon cc complete`, commit, push.

## Out of scope

Changing `dispatch.enabled` or removing `.seldon/DISPATCH_STOP` (operator housekeeping, named in the handoff). The executive summary v4 (98ed1dd1, blocked on Fable quota). The Semrush trial (DN-017, operator by hand). Any edit to a MeasurementSpec's existing `rf_*` text.
