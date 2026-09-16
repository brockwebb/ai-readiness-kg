# CC Task: a headless session has no next turn; every gate it starts is polled to completion inside the turn

**Date:** 2026-09-16
**Project:** ai-readiness-kg (the launch prompt and its test land in `/Users/brock/GitHub/seldon`; the `CLAUDE.md` clause and its test land here)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_dispatcher_commits_its_record_RESULT.md` §0 and §7.2, and the dispatch log `logs/dispatch/2026-09-16_dispatcher_commits_its_record.log`.
**Implements:** DN-006 decision 2 (a dispatched session is launched by the dispatcher and must produce its RESULT) and the long-running-commands rule in `CLAUDE.md` (operator-ordered 2026-09-09), extended to the case that rule did not foresee.
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene of the dispatch path; cycle 5 on 2026-10-05 is the first dispatched gate-running task that depends on it.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push` to both repos' own remotes.

**HEADLESS NOTICE, read before any step.** This session is running under `claude -p`. There is no next turn. Ending the turn ends the process, and every child you started and did not wait for is orphaned with its work undone (POSIX `wait(1)`; CI runners kill unwaited background jobs at step exit for the same reason). Do not use Claude Code's background-task mode for any command in this task, and never write or rely on "I'll be notified when it finishes." Every command that can run longer than two minutes is started with `nohup ... > logs/<name>.log 2>&1; echo EXIT=$? >> logs/<name>.log &`, then polled in this turn with repeated `sleep 240; tail -5 logs/<name>.log` tool calls until the log carries its `EXIT=` line. Only then continue. The first session on `c609b1e1` died exactly this way at `2026-09-16T14:44:47Z` after 624 s with no RESULT; this task exists so that no dispatched session dies that way again, and its own session is the first one at risk.

---

## 0. The defect, stated once

`logs/dispatch/2026-09-16_dispatcher_commits_its_record.log` is three lines: the launch line, the sentence `I'll be notified when the Seldon suite finishes. Next step after that is merging and pushing Seldon, then running this repo's gates.`, and `EXIT=0`. The session backgrounded the Seldon suite through Claude Code's background-task mode, which delivers its completion as a message on the *next* turn, and ended the turn to receive it. Under `claude -p` the model's turn end is the process end. The dispatcher recorded `result_present: false`, `ok: false`, and walked the task to `blocked` (`dispatch_finished` `804e0b27`, `artifact_state_changed` `0a235e61`), which is the design catching the failure correctly. The failure should not have needed catching.

`CLAUDE.md`'s long-running-commands section already says "Do not end the turn while a required command is still running. Poll." It says it for an interactive session, where ending the turn early is a delay. For a dispatched session it is a termination, and nothing in the prompt the dispatcher hands the session says so.

**Decisions taken here (operator overrides later):**

1. **The dispatcher's launch prompt carries the headless clause.** The prompt the dispatcher passes to `claude -p` (`seldon/commands/dispatch.py`, the string that begins `Read CLAUDE.md, then execute cc_tasks/<file>.md ...`) gains one sentence after the addendum sentence: `This session is headless: there is no next turn and ending it ends the process. Poll every detached command to its EXIT line inside this turn; never use background-task mode or wait to be notified.` The clause is part of the launch, not of the task file, because it is true of every dispatched session and false of every interactive one. A test in the Seldon suite asserts the launched prompt contains the clause verbatim.
2. **`CLAUDE.md`'s long-running-commands section gains a `Headless sessions` paragraph** stating the same rule in the same words, with the 2026-09-16 log line as the incident it was built for, so an interactive reader sees why the dispatched prompt says what it says. `tests/test_dispatch_config.py` (or a sibling in the same file) asserts the paragraph is present and that its rule sentence matches the launch prompt's clause byte for byte, so the two cannot drift apart.
3. **A mechanical guard is searched for before it is designed.** Before writing decision 1, spend at most fifteen minutes on prior art: does Claude Code expose a setting, flag or environment variable that disables background-task mode for a `claude -p` invocation? Search the Claude Code documentation and `claude --help`. If one exists, the dispatcher's wrapper (`scripts/jobs/` or the launch call itself, whichever holds the `claude -p` line) sets it, and the RESULT cites the documentation. If the search fails, the RESULT says so in words with the queries run, and the prompt clause stands alone. A guard that exists is not re-invented in prose.
4. **The live proof is the next dispatched task, not this one.** This session was launched under the old prompt, so its own log cannot show the clause working. `cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips.md` succeeds this task on the graph and is the first task launched under the new prompt; its RESULT §0 quotes its own dispatch log and `dispatch_finished` event as the observation for this task. This RESULT says that plainly and claims nothing it did not observe (RESULT §5.1 of the predecessor: evidence that exists in exactly one window is captured in that window, not promised).

**Write set, derived from the decisions:** `seldon/commands/dispatch.py` (one sentence in the prompt string) and its test in the Seldon repo; the wrapper line only if decision 3 finds a guard; `CLAUDE.md` (one paragraph under "Long-running commands") and the assertion in `tests/test_dispatch_config.py` here; `seldon_events.jsonl` by this task's state transitions; the RESULT. Nothing else. The protected-paths check asserts `docs/` byte-identical.

**Immutable once written. Glob `2026-09-16_headless_session_polls_to_completion_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Prior-art search (decision 3): fifteen minutes, bounded, cited or recorded as failed.
## 2. Seldon repo: decision 1's sentence in the launch prompt, its test, the wrapper setting if §1 found one. Seldon suite green with `NEO4J_USERNAME` and `NEO4J_PASSWORD` exported explicitly (the fixture skips silently without them; `dispatcher_commits_its_record_RESULT` §5.5). The RESULT quotes passed AND skipped counts; a run that skips the Neo4j tier is not a green run. Merged, pushed.
## 3. This repo: decision 2's paragraph and the byte-equality assertion.
## 4. Gate
`make gate-fast` (no stored payload is touched), `seldon verify`, protected paths. All detached, logged, polled to `EXIT=0` inside this turn per the HEADLESS NOTICE. Failure ships nothing: report and stop.
## 5. Report
RESULT `cc_tasks/2026-09-16_headless_session_polls_to_completion_RESULT.md`: §0 what this session did about its own headlessness (which commands were polled, how many polls, the log paths); §1 the prior-art outcome; §2 both repos' commits; §3 the two clause texts side by side; §4 every premise this task file got wrong; §5 the gate table with passed, skipped, wall clock and log path per row; §6 the sentence that the live proof belongs to the successor. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 (merged before §3) → §3 → glob addenda → §4 (detached, logged, polled inside the turn) → §5 → push both repos. Precedes `2026-09-16_neo4j_fixture_fails_not_skips.md` on the graph; the dispatcher will not launch that task until this one is `completed`.
