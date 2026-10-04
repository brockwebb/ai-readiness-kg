# CC Task: a cross-document conflict pass over the definitions of AI readiness, every pair recorded

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-10-02_kg_research_questions_RESULT.md` (task 48c74933), Q3 graded `cannot_answer`. The operator's question was whether the literature's definitions of AI readiness and AI-ready data conflict. The graph cannot say: `CONFLICTS_WITH` holds 7 edges, all inside single documents, none touching the Q1 definition set, and the RESULT notes that an empty answer is not agreement (the CQ-15 failure of 2026-09-04, unchanged). This task runs the cross-document pass the RESULT names and records every pair, so an absence of a conflict edge becomes a recorded "compared, no conflict" instead of silence.
**Implements:** DN-009 decisions 2 and 8; closes the Q3 candidate task of the 48c74933 RESULT.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-02_commerce_guidance_admission.md`
**Spend:** est. 6M tokens (Opus). Pair judgments are the cost; the pair list, matrices and tests are script work.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **The set.** The Q1 definition set as `scripts/run_kg_questions.py` produces it AFTER the Commerce admission task has re-run it (expect 17 or more definitions across 11 or more documents; use whatever the script yields and report the count). Do not recompute the set by another query.

2. **Prior art first.** Read the repository's own precedent for a conflict overlay before designing one: the fss-policy-kg adjudicator overlay shape (`get_conflicts`, the `conflict_kind` and adjudicator fields; read its schema and one worked example in that repository, do not modify it) and this repository's single-document conflict edges (`CONFLICTS_WITH` in `kg/schema.yaml`; the 7 existing edges and the extraction run that wrote them). Search the corpus and then the web for a named method for comparing definitions of a construct across sources (definition analysis, concept analysis, Walker and Avant style attribute listing, conceptual-analysis methods in the information-systems literature) and cite what is found in the README; adopt a named method if one fits and say where it does not.

3. **Every pair, one record.** For each unordered pair of definitions from DIFFERENT documents, write one row to `docs/evidence/definition_pairs.csv` with: both definition keys, both document ids, both verbatim spans (each under 15 words quoted, the rest by locator), `outcome` (closed set: `conflict`, `differs_no_conflict`, `consistent`, `not_comparable`), and, when the outcome is `conflict` or `differs_no_conflict`, `kind` (closed set, from the 48c74933 RESULT: `scope`, `necessary_condition`, `object_of_readiness`) and a one-sentence reason that cites only words present in the two spans. `not_comparable` requires the reason (for example: one defines a human capability, one defines a property of data). Pairs from the same document are skipped and counted.

4. **Edges only where the gate allows.** For `conflict` outcomes, write `CONFLICTS_WITH` through the standing event-writing path and the grounding gate (DD-008, absolute zero ungrounded), with both spans as grounding and the `kind` and a `source: cross_document_pass` property; never hand-write events. An edge that fails grounding goes to quarantine with the reason, and its row in the CSV keeps its outcome with a `quarantined` flag. `differs_no_conflict` and `consistent` produce no edge; they live in the CSV, and the projection is not changed for them.

5. **Adjudication is not done by this task.** Every judged row carries `adjudicated: false`. A control: include at least 6 pairs the operator or a prior artifact has already characterised (for example the NOAA order and the scientific-AI data-readiness paper, whose differences the 48c74933 reader gate described) as positive controls, plus 4 self-pairs of a definition with a verbatim paraphrase made by script (not by the model) as negative controls. The pass criterion for the controls is stated in the RESULT before the controls run: positive controls must not come back `consistent`; negative controls must come back `consistent`. Report the control outcome whether it passes or fails; if the negative controls fail, the judgments are not usable and the RESULT says so first.

6. **Matrices and the summary table.** Generate from the CSV: a pair-outcome matrix by document pair, counts by `outcome` and by `kind`, and a ranked list of the definitions with the most `conflict` or `differs_no_conflict` rows. Order is by count only; no weighting. Do not write prose that interprets what the conflicts mean for the framework.

7. **Reader gate (DN-009 d7).** A fresh subagent given only the README and the three generated tables writes five sentences on where the literature's definitions of AI readiness conflict, where they merely differ, and the one disagreement it would want settled first. Quote in the RESULT.

**Write set:** `docs/evidence/definition_pairs.csv`, `docs/evidence/definition_pairs.md` (README, matrices, counts, controls), `scripts/run_definition_pairs.py` (builds the pair list deterministically, calls the model per pair under a declared ceiling of 5000000 tokens, writes the CSV; `--check` re-verifies the pair list and control outcomes without a model call), `tests/test_definition_pairs.py` (pair list complete and unordered-unique; same-document pairs excluded and counted; closed vocabularies; every `conflict` row has a `kind` and two spans; controls recorded), `events/` (the next shard, via the harness only), the RESULT. Byte-identical: everything else, including `kg/schema.yaml`, `docs/brief/`, `docs/deck/`, `framework/`, and the FSS repository. No schema change, no new node label, no new edge type, no extraction of any document.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, `tests/test_definition_pairs.py`, the protected-paths diff. RESULT `cc_tasks/2026-10-04_definition_conflict_pass_RESULT.md`, under 60 lines: the set size and pair count; counts by outcome and kind; the controls first (declared criterion, then outcome); how many edges written and how many quarantined, with reasons; the prior art found and the method adopted; the reader gate's five sentences; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** read precedent and prior art → pair list → controls and declared criterion → run pairs → edges through the harness → matrices → tests → reader gate → gate → RESULT → push.
