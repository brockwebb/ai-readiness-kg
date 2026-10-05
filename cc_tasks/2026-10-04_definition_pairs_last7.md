# CC Task: judge the last 7 definition pairs

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-10-04_definition_pairs_completion_RESULT.md` (task `607b15a6`, coverage 151 of 158). The 1.2M ceiling held; its arithmetic left out the 405K control re-check, so 7 pairs are unjudged. This task judges them under the exact command that RESULT gives, so the audit reads 158 of 158.
**Implements:** DN-009 decision 2.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-04_views_regenerate_v3.md`
**Spend:** est. 1M tokens (Opus) for the session, plus a declared judge ceiling of 300,000 (7 × ~37K with headroom). Controls are NOT re-run: they passed under `definition_pairs_2026-10-04b` with the same `criteria_version` `60256b3a937929b5` this run uses, and nothing in the judge or criteria has changed since; the RESULT states that premise and the spend it saves.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. `scripts/run_definition_pairs.py --run --run-id definition_pairs_2026-10-04c --ceiling-tokens 300000`, same `criteria_version`. Judged pairs skip. If the criteria version has moved, stop and report; do not judge under a different version.
2. Regenerate `docs/evidence/definition_pairs.md` over 158. If any of the 7 is `conflict`, emit its edge through `--emit-edges` and the projection path `607b15a6` built; otherwise no projection run.
3. Reader gate (DN-009 d7): a fresh subagent given only the regenerated file writes three sentences on whether the 7 change the picture; the RESULT quotes them and says in one line what moved from the 151-pair reading.

**Write set:** `docs/evidence/definition_pairs.{csv,md}`, `events/raw/definition_pairs/`, `state/spend_ledger.jsonl`, `docs/evidence/kg_questions.{yaml,md}` only if an edge is projected, the RESULT. Byte-identical: everything else.

**Immutable once written.**

## Gate and report
Full suite (0 failed; v3 precedes), `seldon verify`, the protected-paths diff, `tests/test_definition_pairs.py`. RESULT `cc_tasks/2026-10-04_definition_pairs_last7_RESULT.md`, under 30 lines: the 7 outcomes; counts over 158; edges projected if any; the reader gate; premises wrong; judge tokens against the ceiling, session tokens and models. `seldon cc complete`, commit, push.
