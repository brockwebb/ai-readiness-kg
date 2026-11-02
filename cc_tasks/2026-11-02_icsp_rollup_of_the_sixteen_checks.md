# CC Task: the ICSP-level roll-up: the sixteen checks placed under the AI-ready criteria they descend from, as a build product

**Date:** 2026-11-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** DN-018 (checks tied to FCSM 20-04 Accessibility concerns), DN-014 (decision support, three tiers), DN-016 (vocabulary; two kinds of user), the USAFacts operationalization brief (`docs/crosswalk/usafacts_operationalization_brief.md`) and its delta table (`docs/brief/B_usafacts_delta.md`).
**Amended by:** none.
**Builds on:** 9af5f624 (one-pager builder `scripts/sixteen_checks_build.py`, `SERVES_FCSM_CONCERN` edges, `RB.check_rows`); b694c14a (`readiness_brief_build.py`: the cycle-of-record grid, font/colour/vocabulary/dash/digit checks).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer: the lineage from each check up to the criterion it operationalizes, rendered at the level an ICSP member reads.
**Fulfils:** its own ResearchTask.
**After:** 9af5f624
**Model:** author
**Spend:** est. 0.7M tokens, Claude Code session included. One role (`author`); no review model. The task ends by printing its own session usage.
**Parts:** A 0.25, B 0.60, C 0.15.
**Part map:** A is the lineage data in the record; B is the roll-up build product; C is the gate and RESULT.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

The sixteen-check table is the implementer's level. ICSP members asked for one level up: the buckets, why each matters, and the line from each bucket back to the AI-ready data framework they already know (USAFacts 2026), which the operator operationalized and extended. The operator's instruction for the text: plain, no restating, every sentence counts; nothing conversational.

## Step 0

1. Confirm 9af5f624 `completed` and `get_overview` reports `projection_gate.status: green`; quote both. Red stops the task.
2. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.
3. Read this file's four Implements documents. The delta table is the source of record for what was kept, changed and added against USAFacts; nothing here restates it from memory.

## Vocabulary and style (every rendered word)

As the brief and one-pager tasks: *readiness diagnostic*, *check*, *standard user*, *API user*; pass, partial, fail, *not measured*. No "scan", "probe", "crawl", "audit", "ports", "unmeasurable". No em or en dash used as a dash. No check code (A1, F4) anywhere on the page: plain names only. The word "accessibility" appears only as "accessible" (the USAFacts criterion name) or "accessibility in the FCSM data-quality sense"; Section 508 is never implied. Every sentence on the page is a query over the record or a verbatim quotation with its source; the builder types no prose of its own beyond column headers and the two-sentence intro fixed in Part B.

## Part A: the lineage in the record

Each MeasurementSpec already carries `indicator_code` (A1..A13, B3, D1, D4, F4); the code's letter is its USAFacts group per the skeleton (`docs/crosswalk/usafacts_operationalization_skeleton.md`): A Accessible, B Understandable, C Accurate, D Open, and the extension groups E, F, G the project added. If the record does not already carry a node per group with the criterion's verbatim description, add through `scripts/framework_writeback.py::save`:

1. Four `AiReadyCriterion` nodes (accessible, understandable, accurate, open), each with `source: USAFacts 2026 (usafacts-ai-ready-data-guide)` and `text` verbatim from the corpus copy (`state/docling_md/usafacts-ai-ready-data-guide.md`): the guide's own one-sentence statement of the criterion, with the docling line range quoted in the build report. Where the guide gives no one-sentence statement, the first sentence under the criterion heading, and the RESULT says so.
2. Three `ExtensionGroup` nodes (E TEVV loop, F Release engineering, G Statistical-system constructs) with `text` from the operationalization brief's "Shape of the instrument" bullets, verbatim.
3. One `DESCENDS_FROM` edge from each of the sixteen specs to its criterion or extension group, by code letter. Sixteen edges.

Then `python scripts/load_framework_graph.py`, roundtrip test green, `build_framework_graph.py` no-op.

- check: 7 nodes added, 16 edges added, roundtrip passed/skipped/xfailed/deselected counts; quote all.
- check: a Cypher count of specs per criterion equals 13 Accessible, 1 Understandable, 0 Accurate, 2 Open, 1 Release engineering (F); quote it. Any other split is a premise error to report.

## Part B: the roll-up as a build product

`scripts/readiness_rollup_build.py`, patterned on `sixteen_checks_build.py` (checks imported, not copied), writing `reports/diagnostic/rollup/Readiness_Diagnostic_Rollup.md`, `.docx` and `.pdf` (PDF rendered from the Markdown by the script; Markdown sha256 beside the PDF path in the build report). Portrait, Calibri, 11pt body, white, black or grey text, orange only for the word "Scored". Target one page; two is permitted and the RESULT says which.

The page, in order:

1. **Title:** "Readiness diagnostic: what it measures, at a glance".
2. **Intro, two sentences, fixed:** "The readiness diagnostic checks whether a program acting for a member of the public can get an agency's data and the documentation that goes with it. Its checks descend from the four criteria of the USAFacts guide to AI-ready data; the diagnostic measures the criteria that can be measured from outside and adds one check from release practice."
3. **The bucket table**, one row per criterion in USAFacts' order (Accessible, Understandable, Accurate, Open) and a fifth row for the one extension group that carries a check (Release engineering), columns:
   - **Criterion**: the node's name, with "(added)" on the extension row.
   - **What the framework asks for**: the node's verbatim `text`.
   - **Checks**: the count, then the plain names (`rf_name_brief`) of the checks in this bucket, Scored ones marked.
   - **Quality concern**: the distinct FCSM 20-04 concern short labels those checks serve (from the one-pager's `CONCERN_SHORT`), so the bucket's "why it matters" is FCSM's language, not the project's.
   - **Agencies passing every check in this bucket**: from the cycle of record the brief's grid uses (`RB`'s grid source), the count of the sixteen agencies with no fail in the bucket, written "n of sixteen"; "not measured" checks are excluded from the denominator for that agency and a footnote says so. Accurate reads "no check yet; needs an evaluation harness" from the brief's typing (`EVAL`), not typed by the builder.
4. **Footer, two lines:** "Checks descend from USAFacts (2026), *AI-ready data*; concerns from FCSM 20-04, Accessibility dimension, after Webb 2026." and "Standard user: no key. API user: a free key by open registration, a person completes an email step." (the latter from `preface_source.yaml` as the one-pager reads it).

- check: `.docx` and `.pdf` page counts; quote both.
- check: font, colour, vocabulary, digit and dash audits on all three files; quote.
- check: grep of the Markdown for every check code pattern `\b[A-G][0-9]{1,2}\b`, for U+2014 and U+2013, and for "508" returns zero lines; quote.
- check: the bucket counts in the rendered table equal Part A's Cypher split; quote the comparison.
- check: the "agencies passing" column recomputed independently from the cycle of record by a second code path (`RB` grid) equals the rendered numbers; quote.
- check: the Scored marks are exactly the four `instrument_state = specified` specs; quote.

Register the three files as build products the way the one-pager was registered (9af5f624's RESULT). Commit path-scoped, push.

## Part C: gate and RESULT

`make gate-task` (record touched), `seldon verify`, protected-paths diff, all to `EXIT=0`. Then `cc_tasks/2026-11-02_icsp_rollup_of_the_sixteen_checks_RESULT.md`: Step 0 quotes; Part A's two checks; Part B's six checks; the docling line ranges quoted for each criterion text; premises this task got wrong; the gate tier with wall-clocks; session usage against 0.7M. `seldon cc complete`, commit, push.

## Out of scope

Use-case or user-persona nodes (a Desktop design note first, after the 2026-11-03 meeting). Any change to the sixteen specs' text. A deck. Pictures.
