# ADDENDUM 03 to `cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md`: land DN-019 and the verdict ledger as the first commit

**Date:** 2026-11-02
**Status:** AMENDS the base task, ADDENDUM_01 and ADDENDUM_02. Not a supersession.
**Authored by:** Desktop session.

## Why

DN-019 (the measurement view and the view ladder) was written and its prior-art verdict recorded (PASS, sha256 d2a9152f197b, event 1b9ddeb0) on 2026-11-02, but the commit gate requires `state/prior_art_verdicts.jsonl` staged beside the note and `seldon_commit_governed` refuses that path (defect 9c5c7d62). Left untracked in `docs/design/`, the note would make the dispatcher refuse every task, so Desktop staged it at `handoffs/2026-11-02_staged_DN-019_measurement_view_and_the_view_ladder.md` and committed it there. That location is a holding slot, not where the note lives.

## Step 0, new item before ADDENDUM_02's 3a

0. `git mv handoffs/2026-11-02_staged_DN-019_measurement_view_and_the_view_ladder.md docs/design/2026-11-02_DN-019_measurement_view_and_the_view_ladder.md`. Run `seldon prior-art verify docs/design/2026-11-02_DN-019_measurement_view_and_the_view_ladder.md` (the bytes are unchanged, so the verdict is PASS again; quote the sha256). Stage the note and `state/prior_art_verdicts.jsonl` together and commit as `design: DN-019 measurement view and the view ladder (moved from handoffs staging)`. Quote the sha. If the ledger carries other uncommitted lines (the lease-held lines from 2026-10-21 onward), they go in the same commit; quote the line count.

Everything else in the base task and ADDENDUM_01 and ADDENDUM_02 stands.
