# CC Task: the dispatcher tells the operator when a task finishes; four small provenance defects close with it

**Date:** 2026-09-17
**Project:** ai-readiness-kg (dispatcher code and its tests land in `/Users/brock/GitHub/seldon`; the `seldon.yaml` block, the wrapper fix and its test land here)
**Authored by:** Desktop session, from the operator's statement of 2026-09-17 ("the only thing I don't have are alerts that things are done"), `2026-09-16_session_id_names_the_process_RESULT.md` §4 premise 5, `2026-09-17_figure_gate_reads_cycle_of_record_RESULT.md` §0 (no `file_hash`) and §4 premise 7, and `2026-09-16_long_running_rule_matches_harness_RESULT.md` (the `REFUSING` line in `logs/airkg_dispatch.log` at 02:04:06Z written by a fixture).
**Implements:** DN-006 decision 7 (the dispatcher's record is complete and attributable) and DN-005 §5 rule 3 (the operator is brought in for value inputs; a finished task is one, and today nothing brings it).
**Framework layer served (DN-005 §5 rule 1):** none. Hygiene of the dispatch path.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push` to both repos' own remotes.

---

## 0. The defects, stated once

1. **No completion signal.** Five tasks ran unattended in the last 14 hours. The operator learned each had finished by asking the Desktop to query the graph. cron has `MAILTO`, systemd has `OnFailure=` and `OnSuccess=`, CI runners post a status: in every one the runner owns the notification and configuration names the channel. The dispatcher has none.
2. **`seldon issue create` and `issue update` hard-code `actor="human"`.** Two Issues filed and resolved by headless CC sessions are on the record as human acts.
3. **Desktop registration records no `file_hash`.** Every `seldon cc complete` on a Desktop-authored task prints "Task has no registered file_hash. Skipping immutability check." The "immutable once written" line in every task file is unenforced for exactly the files the Desktop writes, which is all of them.
4. **A fixture writes into the live dispatch log.** `tests/test_dispatch_config.py::test_the_wrapper_refuses_loudly…` runs `scripts/jobs/` with a scrubbed environment, and the wrapper resolves its log path from the repo, so the refusal lands in `logs/airkg_dispatch.log` beside real passes.

**Decisions taken here (operator overrides later):**

1. **`dispatch.notify` in `seldon.yaml`: a command template the dispatcher runs after `dispatch_finished` and after it walks a task to `blocked`.** The child gets `SELDON_NOTIFY_TASK_ID`, `SELDON_NOTIFY_TASK_NAME`, `SELDON_NOTIFY_OK` (`true`/`false`), `SELDON_NOTIFY_RESULT_PATH`, `SELDON_NOTIFY_LOG_PATH`, `SELDON_NOTIFY_WALL_SECONDS` in its environment. It runs detached with a 30 s timeout; a failing or missing notifier is one `dispatch_notify_failed` event and never blocks or alters the dispatch record. This repo's `seldon.yaml` sets it to a macOS `osascript -e 'display notification …'` line with title `Seldon` and the task name plus ok/blocked in the body. The template is a string so the operator can swap in a phone push (ntfy, Pushover) without touching Seldon; the RESULT shows the swap in one line as an example, not as a default, because the dispatcher's own network stays local.
2. **`issue create` and `issue update` take the actor from the same place `cc complete` does.** Whatever `cc complete` uses to stamp `cc`, these use; a terminal invocation with no session environment still resolves to `human`. Prior events are not rewritten.
3. **`seldon cc register` records the file's hash whether or not the file is git-tracked.** `allow_untracked` was a statement about git recoverability (the registration message says so); it was never a reason to skip hashing the bytes on disk. The immutability check at `cc complete` then runs for Desktop-authored files. The dispatcher's commit of the file (DN-006 residue, decision 3 of `2026-09-16_dispatch_idempotence`) does not change its bytes, so the hash still matches; a test asserts that sequence.
4. **The wrapper's log path comes from the environment** (`AIRKG_DISPATCH_LOG`, defaulting to the current path), and the test sets it to `tmp_path`. The stray `REFUSING` line from 02:04:06Z is left in the log as it is; the RESULT cites it as the last of its kind.
5. **The live observation of decision 1 is this session's own finish.** The dispatcher process that launched this session loaded the pre-fix code, so its `dispatch_finished` will run no notifier. The first notification the operator sees is for the *next* dispatched task. The RESULT says that; it does not claim a notification it cannot have produced. It does show the notifier firing under a stub dispatcher in the test, and it runs the configured `osascript` line once by hand from the session, with `SELDON_NOTIFY_*` set, so the operator's screen gets one notification during this task and the RESULT records the wall clock it fired.

**Write set:** `seldon/commands/dispatch.py`, `seldon/commands/issue.py`, `seldon/commands/cc.py`, their tests, in the Seldon repo; `seldon.yaml` (the `dispatch.notify` line), `scripts/jobs/` (the log-path line), `tests/test_dispatch_config.py` (the fixture's env), `seldon_events.jsonl` by this task's transitions, the RESULT, here. `docs/` byte-identical.

**Immutable once written. Glob `2026-09-17_dispatcher_notifies_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Seldon repo: decisions 1 to 3 with tests written first and seen failing. Seldon suite green, 0 skipped, counts quoted. Merged, pushed.
## 2. This repo: decisions 4 and 5; the one hand-fired notification, with its wall clock.
## 3. Gate
`make gate-fast` (`-rs`; no stored payload touched), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-17_dispatcher_notifies_RESULT.md`: §0 the notifier contract as implemented and the `seldon.yaml` line; §1 both repos' commits; §2 the hand-fired notification and the sentence that the first automatic one belongs to the successor; §3 the actor and hash fixes with the event ids of this task's own transitions showing actor `cc` and a hash check that ran; §4 every premise this task file got wrong; §5 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (merged before §2) → §2 → glob addenda → §3 → §4 → push both repos.
