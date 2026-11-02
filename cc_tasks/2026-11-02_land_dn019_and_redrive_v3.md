# CC Task: land DN-019 in docs/design with its verdict ledger, then put V3 back on the queue

**Date:** 2026-11-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** 9af5f624 ADDENDUM_03 (missed: committed after that task had launched and read its addenda).
**Amended by:** none.
**Builds on:** none.
**Framework layer served (DN-005 §5 rule 1):** none; repository hygiene so a design note sits where the gate expects it.
**Fulfils:** its own ResearchTask.
**After:** none
**Model:** author
**Spend:** est. 0.15M tokens, Claude Code session included. The task ends by printing its own session usage.
**Parts:** A 0.70, B 0.30.
**Part map:** A lands the note; B redrives V3 if it stopped.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Part A

1. `git mv handoffs/2026-11-02_staged_DN-019_measurement_view_and_the_view_ladder.md docs/design/2026-11-02_DN-019_measurement_view_and_the_view_ladder.md`.
2. `seldon prior-art verify docs/design/2026-11-02_DN-019_measurement_view_and_the_view_ladder.md`; expected PASS with sha256 d2a9152f197b (bytes unchanged). Quote the line. A FAIL stops the task and the RESULT quotes the problems.
3. Stage the note and `state/prior_art_verdicts.jsonl` together; if `seldon_events.jsonl` or the ledger carry other uncommitted lines (Desktop's verdict events of 2026-11-02 that the tools could not commit), they go in the same commit. Commit as `design: DN-019 measurement view and the view ladder (moved from handoffs staging)`. Quote the sha and the line counts committed from each ledger.
4. `seldon verify`; quote EXIT.

- check: `git status --porcelain` is empty after the commit; quote.
- check: `ls docs/design/*DN-019*` exists and `ls handoffs/*DN-019*` does not; quote.

## Part B

If 829a5010 (`cc_tasks/2026-11-02_v3_measurement_sheet.md`) is `blocked` on its Step 0 item 1 (DN-019 absent), `seldon dispatch redrive 829a5010` and quote the transition. If it is still `in_progress`, leave it; if `completed`, nothing to do. Quote the state found.

RESULT at `cc_tasks/2026-11-02_land_dn019_and_redrive_v3_RESULT.md` with every quote above, then `seldon cc complete`, commit, push.
