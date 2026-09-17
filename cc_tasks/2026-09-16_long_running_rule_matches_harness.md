# CC Task: the long-running-commands rule says what the harness allows, and the gate prints why it skipped

**Date:** 2026-09-16
**Project:** ai-readiness-kg (this repo only)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_headless_session_polls_to_completion_RESULT.md` §4 premises 1 and 2, and `cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips_RESULT.md` §6 premise 7 and §7 "The 18 skips".
**Implements:** the long-running-commands rule and the suite-tiers rule in `CLAUDE.md` (operator-ordered 2026-09-09). Both are corrected here, not weakened.
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene of the dispatch path.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

## 0. The defects, stated once

Two dispatched sessions in a row reported that `CLAUDE.md` prescribes commands the harness refuses:

- `sleep 240; tail -5 logs/<name>.log` is blocked by Claude Code, which suggests alternatives that deliver on a later turn. A headless session has no later turn. What worked in both sessions is one foreground Bash call running a bounded loop: `for i in $(seq 1 N); do grep -q '^EXIT=' <log> && break; sleep 15; done; tail -5 <log>`, with the tool timeout set at or below 600 s and the loop bound chosen so the call ends before it.
- `nohup <cmd> > log 2>&1 &` with the instruction to "append `; echo EXIT=$? >> log`" reads as `nohup <cmd> > log 2>&1; echo EXIT=$? >> log &`, which backgrounds only the `echo` and blocks the tool call on the command. The form that detaches and records the exit code is `nohup bash -c '<cmd>; echo EXIT=$?' > log 2>&1 &`.
- `make gate-fast`, `gate-task` and `gate-full` do not pass `-rs`, so the standing 18 skips have no reason on the record. Decision 3 of the predecessor says a gate row without a skip count is a placeholder; a skip count without reasons is the same placeholder one step later.
- The last two tasks pushed on `gate-fast` only, because their task files said so. `CLAUDE.md` says `gate-full` before every push. The task author was wrong; this task runs `gate-full` and it stands for those two pushes as well.

**Decisions taken here (operator overrides later):**

1. **`CLAUDE.md` "Long-running commands" shows the two forms that work**, replacing the `nohup` line and the `sleep 240; tail` line. The three rules under it and the `logs/` gitignore sentence are unchanged. The Headless-sessions paragraph is unchanged (its rule sentence is byte-pinned to the Seldon launch prompt by `tests/test_dispatch_config.py`; do not touch it).
2. **Every gate target in `Makefile` passes `-rs`.** Skip reasons go to the log the RESULT cites. Nothing else about the targets changes.
3. **The RESULT for this task attributes the 18 skips**: a table of reason string and count, from the `gate-full` log. If any reason is a missing credential or service that this machine has, that is a finding for the next task, not a fix here.

**Write set:** `CLAUDE.md` (the two command lines under "Long-running commands", nothing else), `Makefile` (the `-rs` flag on the gate targets), `seldon_events.jsonl` by this task's state transitions, the RESULT. `docs/` byte-identical.

**Immutable once written. Glob `2026-09-16_long_running_rule_matches_harness_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 and 2.
## 2. Decision 3's table, from the `gate-full` log.
## 3. Gate
`make gate-full` (detached with the corrected form, polled inside this turn to `EXIT=0`), `seldon verify`, protected paths. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-16_long_running_rule_matches_harness_RESULT.md`: §0 the exact detach and poll commands this session used, with poll counts; §1 the `CLAUDE.md` diff, quoted; §2 the skip-reason table; §3 every premise this task file got wrong; §4 the gate table with passed, skipped, xfailed, deselected, wall clock and log path per row, and the sentence that this `gate-full` also covers the two prior fast-tier pushes (`e379e7c`, `ebf5624`). `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
