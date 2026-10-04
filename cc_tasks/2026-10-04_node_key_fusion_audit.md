# CC Task: node-key fusion audit, how many grounding spans the `<doc>::<local id>` key has overwritten, and what it does to the record

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-10-02_commerce_guidance_admission_RESULT.md` §7 premise 6 (task `381b8651`), found outside that task's scope: node keys `<doc>::<local id>` fuse items that different chunks of one document gave the same local id, so a later chunk's `node_asserted` overwrites an earlier chunk's grounding span. In the Commerce document 102 asserted Definitions became 89 nodes. Across the `bulk_v038` shard: 4,070 distinct spans overwritten on 1,966 keys in 64 documents (815 Claim, 184 Definition). DD-020 fixed only the cross-document form. The record the summary cites counts Definition and Claim nodes, so the size of this has to be known before those counts are quoted. This task measures; it changes nothing.
**Implements:** DN-009 decision 2 (every number the summary uses has a stated basis).
**Framework layer served (DN-005 §5 rule 1):** §2.3, extraction integrity (the executing session confirms the layer number against DN-005 §2 and reports a mismatch as a premise).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-04_definition_pairs_completion.md`
**Spend:** est. 3M tokens (Opus). Script over the event log; no model call outside the reader gate.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Quantify, over every shard `replay()` yields.** For each `node_asserted`, group by key. For keys asserted more than once, count distinct grounding spans after `grounding.normalize`. Emit one CSV row per overwritten span: key, label, document, shard and line of the surviving assertion, shard and line of each overwritten one, chunk ids, and both spans' first 80 characters. Totals by label, by shard (extraction run and model), and by document.

2. **Classify by script, no model.** Each overwritten span is `benign_duplicate` (identical to the survivor after normalisation), `same_term_lost_evidence` (same term or claim text, different sentence), or `collision` (different term or claim text under one id). Counts per class per label. A `collision` is a wrong node, not a lost span; list those in full.

3. **Impact on the record, stated and not fixed.** Which cited figures depend on node counts: the 1,975 Definitions and the counts in `docs/evidence/kg_questions.yaml` (Q1's 19, Q2's construct tallies), any `CL-` entry in `claims.yaml` that counts nodes or edges, and the Commerce two-pipelines 48/49. For each, say whether chunk-qualified keys would move it and by how much, bounded from the CSV. Change none of them.

4. **The fix, designed, not built.** One page in the audit file comparing (a) chunk-qualified keys `<doc>::<chunk>::<id>` with a later merge on identical normalised span, and (b) keeping `<doc>::<id>` and refusing a second assertion whose span differs, routing it to quarantine. State what each does to existing keys, to `[[links]]` from other nodes, to the projection, and to DD-020. Recommend one with the reasoning. The fix is its own task after the operator reads the audit.

5. **Reader gate (DN-009 d7).** A fresh subagent reads only the audit markdown and writes five sentences on how much of the graph's evidence this affects, which cited numbers it touches, and whether it would trust the current Definition count.

**Write set:** `docs/research/2026-10-04_node_key_fusion_audit.md` and `.csv`, `scripts/audit_node_key_fusion.py` (`--check` byte-for-byte), `tests/test_node_key_fusion_audit.py` (a fixture shard with one benign duplicate, one lost span and one collision, each counted in exactly its class), the RESULT. Byte-identical: everything else, including `events/`, `kg/`, `docs/evidence/`, `docs/brief/`, `framework/`.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the audit tests, the protected-paths diff. RESULT `cc_tasks/2026-10-04_node_key_fusion_audit_RESULT.md`, under 50 lines: totals by label and class; collisions, listed; the impact table from decision 3; the recommended fix in two sentences; the reader gate's five sentences; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** script over the log → classify → impact table → fix design → tests → reader gate → gate → RESULT → push.
