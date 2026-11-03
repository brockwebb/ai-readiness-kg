# ADDENDUM 01 to 2026-11-02_admit_usafacts_three_track_framework.md

**Date:** 2026-11-02 (23:15 local)
**Authored by:** Desktop session.
**Why:** the task file named `corpus/inbox/`, which git does not ignore, so the untracked PDFs held the task at the dispatcher's clean-tree gate (c7, pass of 2026-11-03T04:06Z). The files now sit where the Cisco precedent put them. Two premises corrected from `4e27e7bf`'s RESULT.

## Path corrections (replace throughout the task)

- `corpus/inbox/USAFacts AI-Ready Data Slide Deck.pdf` → `corpus/staging/inbox/USAFacts AI-Ready Data Slide Deck.pdf`
- `corpus/inbox/Overview of USAFacts AI-Ready Data Project.pdf` → `corpus/staging/inbox/Overview of USAFacts AI-Ready Data Project.pdf`
- sha256 values unchanged; verify them at the new paths.
- Part A step 2: after the live run, move the originals to `corpus/staging/inbox/usafacts_2026-11-02/` (same gitignored tree). Quote `ls corpus/staging/inbox/`. An empty `corpus/inbox/` directory may remain; it is not tracked and may be left.

## Premise corrections

- Part A step 3: the `included` count is whatever `corpus/manifest.json` shows at run time; quote before and after, expected +2. The project database (`seldon-ai-readiness-kg`) held 290 `Document` nodes after `4e27e7bf`'s projection run.
- Part B, projection paragraph: `4e27e7bf` answered the question. Database `ai-readiness` (the MCP corpus layer) is fed by squiddy from `graphs/ai-readiness/ledger`, not from `corpus/manifest.json`; `scripts/build_projection.py` feeds `seldon-ai-readiness-kg`. So: run `scripts/build_projection.py` (detached, logged, polled; it took 91 minutes last run) and quote the `Document` count in `seldon-ai-readiness-kg` before and after, expected +2. Do not run squiddy's projection. Record in the RESULT §1 that the two documents are not yet in the squiddy ledger, so the MCP corpus verbs will not see them until that ledger is updated; that is a separate task.
