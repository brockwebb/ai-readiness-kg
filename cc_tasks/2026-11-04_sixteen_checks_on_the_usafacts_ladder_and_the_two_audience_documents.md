# CC Task: the sixteen checks re-parented onto USAFacts' three-track ladder, the roll-up and one-pager rebuilt on it, and the ICSP page and working-group explainer built with picture placeholders

**Date:** 2026-11-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** DN-020 (sections 1, 3, 4, 6, 7 and 8 are the specification; nothing here restates them from memory), DN-019 (view ladder; measurement specification fields), DN-016 (vocabulary), DN-015 (four states), FCSM 26-01 (the "SI use" statement at the end of each document).
**Amended by:** none.
**Builds on:** 32e394f1 (`scripts/readiness_rollup_build.py`, the `AiReadyCriterion` and `ExtensionGroup` nodes and the sixteen `DESCENDS_FROM` edges), 9af5f624 (`scripts/sixteen_checks_build.py`, `RB.check_rows`), 829a5010 (`scripts/measurement_sheet_build.py`, the per-check fields), b694c14a (`readiness_brief_build.py`: font, colour, vocabulary, dash and digit checks, reused as-is).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer: each check's lineage up to the rung of the framework it operationalizes, rendered for two audiences.
**Fulfils:** its own ResearchTask.
**After:** c1662a22
**Model:** author
**Spend:** est. 1.0M tokens, Claude Code session included. One role (`author`), no review model. The task ends by printing its own session usage.
**Parts:** A 0.25, B 0.20, C 0.40, D 0.15.
**Part map:** A is the ladder in the record; B rebuilds the two existing products on it; C builds the two new documents; D is the gate and RESULT.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

DN-020 §0: the base document is now USAFacts' August 2026 framework (three tracks, three levels each, three prerequisites, modeled on SLSA), and the sixteen measured checks are placed on its rungs. The roll-up of 2026-11-02 sorts them under the predecessor's four criteria plus a "release engineering" bucket that DN-020 §4 dissolves. The ICSP needs one page and the working group needs a short explainer, both lay reader first (DN-020 §6). Nothing is re-measured: the cycle of record, the readings and the four states are untouched (DN-020 §5). This task edits the framework record's lineage layer only.

## Step 0

1. Confirm c1662a22 `completed` and `get_overview` reports `projection_gate.status: green`; quote both. Red stops the task.
2. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.
3. Read DN-020 in full, then `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md` (slides 9, 15 to 21) and `state/docling_md/usafacts-ai-ready-framework-overview-2026.md`. Every USAFacts phrase rendered on a page is quoted from one of these two files with its docling line; nothing is paraphrased from memory.
4. Confirm DN-020's prior-art verdict passes for its current bytes (`seldon prior-art verify`, read-only); quote the line.

## Vocabulary and style (every rendered word)

As the roll-up and one-pager tasks, plus DN-020 T6: *readiness diagnostic*, *check*, *rung*, *track*, *prerequisite*; pass, partial, fail, *not measured*; SI for government material, AI only inside USAFacts' own titles and quoted captions. No "scan", "probe", "crawl", "audit", "unmeasurable", "ruling". No check code anywhere a reader sees (record ids live in the build report only). No em or en dash as a dash. Calibri, white page, black and grey text, orange accent only (the b694c14a checks enforce this; wire them in). Digits as b694c14a renders them.

## Part A: the ladder in the record

The record (`framework/ai_readiness_framework.json`) gains the three-track framework as lineage nodes beside the existing `AiReadyCriterion` and `ExtensionGroup` nodes. New labels and nodes (ids fixed here so DN-020 §4 and later views can name them):

1. `UsafactsTrack` (3): `usaf:access` "Agentic Access", `usaf:context` "Agentic Context", `usaf:evaluation` "Agentic Evaluation". Properties: `name`, `text` (the track's one-line description from slide 16, verbatim), `source: USAFacts 2026-08 (usafacts-ai-ready-framework-deck-2026-08)`, `source_file`, `docling_lines`.
2. `UsafactsLevel` (9): `usaf:access:1` to `usaf:evaluation:3`. Properties: `track`, `level` (1, 2, 3), `name` (the deck's caption, verbatim, e.g. "Data is published in machine-readable files"), `text` (the bullet list for that level from slides 18 to 20, verbatim), `source`, `source_file`, `docling_lines`. Edge `usaf:<track>:<n>` `DECOMPOSES_INTO` from its track (the existing edge type; quote that the loader accepts it for these labels, or use `REQUIRES` from level n+1 to level n if the schema reads cumulative levels that way; say which and why in the RESULT).
3. `UsafactsPrerequisite` (3): `usaf:pre:open`, `usaf:pre:discoverable`, `usaf:pre:licensed`, with `name` and `text` verbatim from slide 15.
4. Sixteen new `DESCENDS_FROM` edges from the `spec:*` nodes to their rung per DN-020 §4, each with a property `basis: DN-020 §4`. The sixteen existing `DESCENDS_FROM` edges to `aiready:*` and `ext:*` stay and gain `lineage: predecessor`. Before writing, resolve every record id in DN-020 §4 against the spec's `rf_name_brief` and quote the sixteen pairs; a name that does not match its id stops the task on that row (DN-020 §4 says the task confirms them).
5. Schema: `kg/schema.yaml` and `docs/schema_v0.1.md` gain the three labels and their properties, in the style of the `AiReadyCriterion` entry (32e394f1 set the pattern; quote the lines it added and mirror them). `scripts/load_framework_graph.py` learns the three labels, and the roundtrip test `tests/test_framework_projection_roundtrip.py` is run and quoted green: compared, mismatches 0. Update the label list wherever the two prior label additions updated it (grep for `ExtensionGroup` across `scripts/`, `tests/`, `assessment/`, `mcp/`; quote every file touched). The MCP server's `get_overview` is restarted only by the operator; note in the RESULT that until then its gate reads stale, and why (Issue abe74ad2).
6. The three protected files change under this task by design; the protected-paths diff in Part D lists them and nothing else.

## Part B: the roll-up and one-pager rebuilt on the ladder

7. `scripts/readiness_rollup_build.py`: the bucket column becomes the USAFacts rung (prerequisite, discoverable; prerequisite, clearly licensed; Access I; Access II; Context I; Context II; and one row each for Access III, Context III and Evaluation I to III rendered "none measured"), ordered as DN-020 §4. The "What the framework asks for" column quotes the rung's caption from the record. The "Agencies passing every check in this bucket" column and its footnote keep their rule (DN-020 T3 is the same rule). Drop the "Release engineering (added)" row; the lineage sentence at the top names the August 2026 framework and the predecessor guide in one sentence each. Rebuild `reports/diagnostic/rollup/`.
8. `scripts/sixteen_checks_build.py`: the one-pager's grouping follows the same rungs; rebuild `reports/diagnostic/one_pager/`.
9. Both PDFs opened and read back by the author as a reader: the vocabulary checks pass; quote the check lines.

## Part C: the two documents

Built by a new `scripts/dn020_documents_build.py` that reads the record, the cycle of record and the roll-up's computed counts (import, do not recompute), renders Markdown, and produces docx and PDF the way the existing builders do. Pictures: four placeholder frames at the sizes below, each labelled with its DN-020 §7 number and caption; when `reports/figures/dn020/<n>.png` exists the builder places it instead. The build report (`build_report.json`) says for each of the four whether a picture or a placeholder was placed.

10. **ICSP page**, `reports/dn020/ICSP_SI_Readiness_One_Page.pdf`, one page, per DN-020 §6 item 1: what USAFacts built and why it is worth adopting (two sentences); the ladder picture (DN-020 §7 picture 1) with its caption; where the sixteen agencies stand (picture 3, one combined picture) with a caption that gives the count of agencies per rung on the Access track and the Context track, from the roll-up's counts; what an agency gets from the diagnostic (its rung on each track and the one check that lifts it to the next, two sentences); the Evaluation track empty, one sentence. No check names, no record ids, no numbers beyond agency counts. The "SI use" statement in a footer line.
11. **Working-group explainer**, `reports/dn020/SI_Readiness_Working_Group_Explainer.pdf`, four to six pages, per DN-020 §6 item 2, in this order: page 1 the bottom line (what the diagnostic is, what USAFacts' ladder is, where the group's agencies stand); one worked check end to end with picture 4 (choose the check with the simplest sensor, say which and why); the lineage with picture 2 and one short paragraph per step quoting DN-020 §2; the placement table of DN-020 §4 in plain labels; for each rung with a measured check, what passing looks like and what the next rung asks for, quoting the deck's captions; the "what we kept, what we changed" box from DN-020 §3 in at most six lines; the attachments line (measurement sheet, roll-up, one-pager, DN-019) and the "SI use" statement last.
12. Prose in both: smooth and lightly conversational, no stock phrasing, no point made twice, no letter codes a reader must decode; each page read back by the author as a reader before the gate, and the RESULT says in one line per document what a reader would stumble on, if anything.

## Part D: gate and RESULT

`make gate-task` (record touched), detached and logged, polled to EXIT; quote passed, skipped, xfailed and deselected. `seldon verify`, quote EXIT (the pre-existing 98ed1dd1 warning is known). Protected-paths diff on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json`: expected non-empty on exactly the Part A changes; quote the `--stat` and nothing else is listed. Reports are tracked, never gitignored; quote `git check-ignore` returning nothing for the four new PDFs.

RESULT at `cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents_RESULT.md`: §1 the sixteen id-to-name pairs and the rung counts first; Step 0 quotes; the docling line for every USAFacts phrase rendered; Part B's check lines; Part C's placeholder report and the two reader notes; premises this task got wrong; the gate with wall-clocks; session usage against 1.0M. Then `seldon cc complete`, commit, push.
