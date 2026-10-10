# CC Task: main goes green: the brief pack cites Seldon code at a pinned commit, so a Seldon commit can no longer redden this repository's main

**Date:** 2026-10-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the 2026-10-10 daily run (Issue `a82451c1`).
**Framework layer served (DN-005 §5 rule 1):** none directly: a view's reproducibility and the daily gate. No verdict, record, score or framework cell may change.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 0.6M tokens (Opus). Read it as 2 to 4x low. One generator change, one regeneration, `make gate-full` once, detached. No harness model call.
**Network:** none beyond git push

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Measured premises (verify before acting; report any that is wrong)

- `logs/daily_suite/2026-10-10T083004Z.log`, main@`015a4f1c`: `1 failed, 3202 passed, 4 skipped, 41 xfailed`. The failure is `tests/test_brief_pack.py::test_full_pack_regenerates_byte_for_byte_and_nothing_else_is_there` (line 74): `E_architecture.md drifted`. The committed page cites `...spatch.py:834`; a regeneration now yields `...spatch.py:788`.
- Cause, as Desktop reads it: the page cites a line in the Seldon checkout beside this repo, and Seldon changed under it. `seldon/.git/logs/HEAD` shows the PA-001 and HOOK-001 merges on 2026-10-09 evening. The pack's generator resolves that line from Seldon's working tree at render time, so every Seldon commit that moves the cited code reddens this repo's main the next morning. Confirm in `scripts/build_brief_pack.py` how the line is found, and list every other citation the pack makes into a repository other than this one.
- The 10-10 run no longer exercises the dispatcher defect that task `422251c1` targets: since HOOK-001 (Seldon AD-036-R9, "a test never spends unasked"), `tests/test_dispatch_config.py:275` and `:341` skip unless `LIVE_MODEL_CALLS=1`. That is `422251c1`'s business. Do not touch the dispatcher tests here.
- HOOK-001 installed Seldon's commit gate as a tracked pre-commit hook in this repository. Commits go through it; if it refuses one, report its output whole and stop.

## Decisions

1. **Cross-repository citations are pinned to a commit.** A page that cites another repository's `file:line` names the commit it read, in the form `seldon@<sha12>:path:line`, and the generator reads that file at that commit (`git -C <repo> show <sha>:<path>`), never from the working tree. Regeneration is then deterministic in this repository's own state, which is what the byte-for-byte guard asserts. Prior art: commit-pinned permalinks are the standard remedy for line citations that rot (GitHub Docs, "Creating a permanent link to a code snippet"); pinning inputs is the reproducible-builds rule that a build's output depends only on declared inputs (reproducible-builds.org, "Definitions").
2. **The pin lives in one place.** One constant or one small data file holds the Seldon commit the pack cites, and the generator's header comment names it. Moving the pin is an explicit act: a regeneration run with a new pin, committed as such. Set the initial pin to Seldon's current `main` and regenerate, so every cited line is re-resolved against code that exists today; report every line that moved and confirm each still points at the code the prose describes.
3. **The existing guards stay as written.** "Every cited file exists" and "every `file:line` is inside its file" are checked at the pinned commit. No assertion is relaxed.
4. **A missing pinned commit fails loudly.** If the Seldon checkout lacks the pinned sha (shallow clone, rewritten history), the generator and the test fail with a message naming the sha. They do not fall back to the working tree.

## Gate

`make gate-full`, detached and logged per CLAUDE.md. Green means EXIT=0 and 0 failed; quote passed, skipped, xfailed, deselected. Then make one throwaway commit in a scratch branch of the Seldon checkout that shifts the cited code by a line, re-run `tests/test_brief_pack.py` in this repo, show it still passes, and delete the scratch branch. `seldon verify` and the protected-paths diff as usual.

A failed gate writes nothing beyond the RESULT and reports.

## RESULT

§1 premises, each confirmed or wrong. §2 every cross-repository citation found. §3 the change and the pin. §4 lines that moved on re-pinning. §5 gate output, the Seldon-shift check, log paths. Then `seldon cc complete`, commit, push.
