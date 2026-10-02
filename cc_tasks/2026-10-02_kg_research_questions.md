# CC Task: ask the knowledge graph five research questions, and record where it answers and where it cannot

**Date:** 2026-10-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the operator's dictation of 2026-10-02. The operator wants the graph shown as a research and decision-support tool by questions a decision maker would ask of the literature review. This task treats each as a test with a pass or fail, not a demonstration: a question the graph cannot answer is a finding and goes in the RESULT as one.
**Implements:** DN-009 decisions 2 and 8 (the corpus is the first place a claim is searched).
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure (the validity layer's answers to the summary's questions; the executing session confirms the layer number against DN-005 §2 and reports a mismatch as a premise).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-02_evidence_map_prior_art_v2.md`
**Spend:** est. 4M tokens (Opus). Query by Cypher and the MCP verbs; do not read documents into context beyond the span a citation needs.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **First step: is the graph reachable.** Call the `ai-readiness-kg` MCP `get_overview` with a 60 second ceiling per call. On 2026-10-02 `get_cycle_of_record` returned nothing for four minutes in a Desktop session. If any verb hangs, run the same question through `seldon_query` or direct Cypher against `seldon-ai-readiness-kg`, state in the RESULT which route answered each question, and record the hang as a finding. Check `projection_gate` on every Cypher result; an answer about framework labels while it is not `green` is not the record.

2. **The five questions.** Each answered from the graph with citable locators, and each graded `answered`, `partial` or `cannot_answer`, with the reason.
   - **Q1.** What definitions of AI readiness and of AI-ready data exist in the corpus? List each with its source document id, locator and the verbatim span (under 15 words quoted, the rest by locator).
   - **Q2.** What do the definitions share, and where do they differ? Group by the constructs the graph holds. Do not characterise; report which constructs each definition names and which it omits.
   - **Q3.** Do any definitions conflict? Use the graph's conflict representation if one exists (the fss-policy-kg has `get_conflicts`; check whether this graph does). If none exists, say so, and state what a conflict edge would need.
   - **Q4.** What standard instruments or tests of AI readiness exist, and what does each operationalise? List instruments with their constructs and sources.
   - **Q5.** For the FSS AI-readiness survey, which items map to which constructs and definitions, and which constructs have no item? Report the crosswalk's coverage as counts with the uncovered list.

3. **Citation standard.** Every answer row carries a document id, a locator and the extraction's grounding span id. A row without all three is `partial`. Nothing is added from memory or from the web; this task does not search the web.

4. **AI, not SI.** The graph says AI throughout. Do not rename; do not translate. A one-line note in the RESULT records that any federal terminology change is applied at presentation and not in the record (DN-009 decision 4).

5. **Reader gate (DN-009 d7).** A fresh subagent given only the answers file reads it as a federal executive and writes five sentences on what the literature says about the definition of AI readiness and where it disagrees, and the one thing it would want settled first. The RESULT quotes them.

**Write set:** `docs/evidence/kg_questions.yaml` (new; one entry per question with grade, route, rows), `docs/evidence/kg_questions.md` (generated from it), `scripts/run_kg_questions.py` (reruns the queries, `--check` byte-for-byte against the stored answers while the corpus epoch is unchanged), `tests/test_kg_questions.py` (every row has the three citation fields; every grade is in the closed set; the script's output equals the stored file), the RESULT. Byte-identical: everything else. No projection, no extraction, no schema change, no web search, no model call outside the reader gate.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, `tests/test_kg_questions.py`. RESULT `cc_tasks/2026-10-02_kg_research_questions_RESULT.md`, under 50 lines: each question with grade, route and the count of rows; every `partial` and `cannot_answer` with its reason and what would close it, as candidate tasks (not registered by this session); the MCP reachability finding; the reader gate's five sentences; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** reachability check → Q1 → Q2 → Q3 → Q4 → Q5 → file, script and tests → reader gate → gate → RESULT → push.
