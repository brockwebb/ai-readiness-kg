# CC Task — CLAUDE.md states the goal by citing DN-005; one stale task closed on the graph

**Date:** 2026-09-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session, first action after `handoffs/2026-09-15_thread_close_l0_shipped_rejudgements_on_log.md` ADDENDUM.
**Implements:** DN-005 §6 (`docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md`).
**Framework layer served (DN-005 §5 rule 1):** none. This is a hygiene task: the bootloader must point at the standing map, and the graph must not carry a task that a completed successor already fulfilled.
**Fulfils:** its own ResearchTask (`seldon cc register`).
**Spend:** zero model calls. **Network:** none.

**Decisions taken here (operator overrides later):**
1. **`CLAUDE.md` "What this is" opens with the goal, not the KG.** Insert, as the first paragraph of that section, a statement of purpose that names the AI-readiness framework as the goal (DN-005 §1, quoted or paraphrased in one sentence), names the KG as its validity layer and L0 as its most basic level, and cites `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md` by path. Existing paragraphs stay verbatim after it. Nothing else in `CLAUDE.md` moves.
2. **`CLAUDE.md` "Where to read first" gains DN-005 as its first bullet.** One line, path and the phrase "the standing map every task cites".
3. **`eaa47eb3` is superseded by `95911824`.** `cc_tasks/2026-09-12_cited_documents_metadata.md` stopped at §1; `cc_tasks/2026-09-12_cited_documents_metadata_2.md` completed the work (graph: `95911824` completed 2026-09-13T02:30:24Z). Use the Seldon CLI's task supersede command with the reason "stopped at §1; work completed by 2026-09-12_cited_documents_metadata_2.md (95911824)" and `95911824` as the superseding artifact. The Desktop attempted this through `seldon_task_supersede` twice on 2026-09-15 and the MCP call timed out both times without writing; verify by Cypher before and after that the state moved from `proposed` to `superseded` and that a `superseded_by` edge to `95911824` exists.

**Zero edits to:** anything other than `CLAUDE.md` and the graph event for decision 3. No code, no tests, no docs beyond the two `CLAUDE.md` insertions.

**Immutable once written. Glob `2026-09-15_claude_md_cites_dn005_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decision 3 first (graph), with the before and after Cypher output captured for the RESULT.
## 2. Decisions 1 and 2 (`CLAUDE.md`).
## 3. Gate
`make gate-fast` detached, logged, polled (a `CLAUDE.md` edit touches no payload, so `gate-task` is not owed; say so in the RESULT); `seldon verify`; protected paths. The gate for decision 3 is the after-Cypher showing `superseded` with the edge.
## 4. Report
RESULT `cc_tasks/2026-09-15_claude_md_cites_dn005_RESULT.md`: the inserted paragraph as written; the before/after Cypher for `eaa47eb3`; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push. Runs only after `cc_tasks/2026-09-14_standing_guards.md` has pushed; it edits the same `CLAUDE.md` that task may touch.
