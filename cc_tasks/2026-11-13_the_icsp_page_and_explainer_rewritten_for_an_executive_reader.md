# CC Task: the ICSP page and the working-group explainer rewritten for an executive reader, per DN-020 section 10

**Date:** 2026-11-13
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** DN-020 section 10 (amendments A1 to A7 are the specification; read them, nothing here restates them from memory), DN-020 sections 4, 6 and 7, DN-016 (vocabulary), FCSM 26-01 (disclosure of generative SI use, at the end of a document).
**Amended by:** none.
**Builds on:** ec1112d3 (`scripts/dn020_documents_build.py`, the USAFacts nodes and the sixteen `DESCENDS_FROM` edges in the record), `scripts/readiness_rollup_build.py` (the per-level counts; import, do not recompute), `scripts/dcat_brief_build.py` (an FCSM 26-01 statement already written in this repository).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer, rendered for two audiences.
**Fulfils:** its own ResearchTask.
**After:** 2026-11-13_regenerate_the_brief_pack_and_claims_file_stale_since_the_ladder_landed
**Model:** author
**Spend:** est. 0.6M tokens, Claude Code session included. One role (`author`), no review model. The task ends by printing its own session usage.
**Parts:** A 0.15, B 0.40, C 0.30, D 0.15.
**Part map:** A is the per-check prerequisite counts; B is the ICSP page; C is the explainer; D is the gate and RESULT.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

The operator's two asks: map the diagnostic's checks clearly onto the categories and levels of a maturity model such as USAFacts', and replace technical, abbreviated language with text an executive can read. ec1112d3 did the mapping. Desktop read the two built documents back on 2026-11-13 and found them unfit for that reader; DN-020 section 10 lists what was wrong and what replaces it. Nothing is measured again and the record does not change: this task edits one builder and rebuilds two documents.

## Step 0

1. Confirm the predecessor task `completed` and the four tests it names pass on main; quote.
2. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.
3. Read DN-020 in full, section 10 twice. Read both built documents (`reports/dn020/*.md`) as their reader would and list, in the RESULT, each place they break an amendment.

## The reader, and the words

The ICSP reader is a senior executive who is not a technologist and has two minutes. The working-group reader is a mixed room: some technical, most not. Write for the less technical one in both.

- Short sentences. One idea each. A point is made once.
- A term of art is either replaced by plain words or glossed the first time and then used consistently. No letter codes, no record ids, no script paths, no file names in the body of either document. The generator and record commit go in the build report and, on the explainer only, in one small footer line.
- Words that stay out (A4): sensor, measurement specification, cycle of record, least privileged client, markup, rung-by-rung. The earlier vocabulary rules stand (no "scan", "probe", "crawl", "audit", "unmeasurable", "ruling"; USAFacts' captions are quoted as written and exempt). No em or en dash used as a dash. Calibri, white page, black and grey text, orange accent only.
- SI per A1. "AI" appears only inside USAFacts' own titles and quoted captions.
- Quotation marks only around words the cited source wrote (A3); every quoted USAFacts caption is taken from `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md` with its line in the build report.

## Part A: the basics, counted per check

From the cycle of record, for each of the four checks placed on a prerequisite (DN-020 section 4): how many of the sixteen agencies pass it, how many fail, how many were not measured, and whether the record marks its pass bar Scored (a published requirement) or not (this project's reading). Add this to the builder's computed data and to `build_report.json`. Quote the four rows in the RESULT. The per-level counts stay as the roll-up computes them.

## Part B: the ICSP page (one page)

`reports/dn020/ICSP_SI_Readiness_One_Page.pdf`, rebuilt. Title: "SI readiness of federal statistical data: a ladder, and where agencies stand". Five short blocks in A6's order, each with a plain bold lead-in question:

1. **What is it?** USAFacts, which gathers federal data at scale, published a ladder for making government data usable by SI systems. Three tracks (each introduced per A4 with its plain question), three levels on each, and three basics that come first. Picture 1.
2. **How does it work?** The readiness diagnostic checks each agency from the outside, the way a member of the public's SI assistant would, and places it on the ladder. Sixteen checks today.
3. **Where do agencies stand?** Picture 3 and at most four bullets: the basics (per A5: which basic most agencies meet, which most miss, in counts of sixteen), the Access track, the Context track, and Evaluation not yet measured, with the reason in a clause.
4. **What does an agency do with it?** A6's fourth answer: decision support. The agency sees its level on each track and the next step up, so money and staff time go where they raise the level.
5. **What does it cost to run?** A6's fifth answer, one sentence. Read the request counts from the cycle of record; if no per-agency figure can be stated truthfully, state none.

Credit line: built on USAFacts' framework (August 2026) and the FAIR principles (2016). Closing statement per A2, modelled on the statement in `scripts/dcat_brief_build.py`: facts of production only, and nothing about human review that the record cannot show.

## Part C: the explainer (four to six pages)

`reports/dn020/SI_Readiness_Working_Group_Explainer.pdf`, rebuilt, in this order:

1. The bottom line, as three bullets a person could say aloud.
2. The ladder: the three tracks with their plain questions, the three levels, the basics. Picture 1.
3. Where it comes from (picture 2): FAIR 2016, USAFacts' guide 2025, USAFacts' framework 2026, this diagnostic. One or two plain sentences each, in the project's words (A3). SLSA named once here (A4).
4. One check, start to finish (picture 4), in plain words: what we ask, where we look, what counts as a pass, what the four results mean. Keep the check ec1112d3 chose unless a plainer one exists; say which.
5. The basics, before the ladder: the Part A table in plain labels (check, what it asks, how many of sixteen pass, published requirement or this project's reading).
6. The ladder, level by level: one table per A7 (level, what USAFacts asks for, our checks in plain names, how many agencies pass every measured check, what the next level asks for). Rows for the unmeasured levels say "not measured yet" once.
7. What we kept and what we changed (DN-020 section 3), at most six plain lines.
8. Attachments line, then the closing statement per A2.

## Part D: read-back, gate and RESULT

Read both PDFs back page by page as the reader described above. For each document the RESULT states: the longest sentence (quote it), every term a non-technical reader would not know and where it is glossed, and any sentence that appears twice (expected none). Extend the builder's own checks so a banned word, a script path in the body, the string "statistical information" as a gloss of SI, or a repeated sentence fails the build.

`make gate-fast`, detached and logged; quote passed, skipped, xfailed and deselected. Then run the four tests the predecessor task names (they guard the generated views a build can make stale) and quote them green. `seldon verify`, quote EXIT. Protected-paths diff on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json`: expected empty.

RESULT at `cc_tasks/2026-11-13_the_icsp_page_and_explainer_rewritten_for_an_executive_reader_RESULT.md`: §1 the full text of the ICSP page as built, first; then the Part A rows, Step 0's list, the read-back, premises this task got wrong, the gate, session usage against 0.6M. Then `seldon cc complete`, commit, push.
