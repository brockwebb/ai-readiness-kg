# RESULT: the dispatcher tells the operator when a task finishes; four small provenance defects close with it

**Task:** `cc_tasks/2026-09-17_dispatcher_notifies.md` (ResearchTask `2881767c`). No addenda existed at start or before §3; `cc_tasks/2026-09-17_dispatcher_notifies_ADDENDUM*.md` matched nothing both times.
**Executed:** 2026-09-17, headless session launched by the standing dispatcher (`dispatch_launched` `af6811bc`, 14:45:09Z).
**Spend:** zero model calls. **Network:** `git push` to both repos' own remotes only.
**Gate:** green, and every command below ran to its `EXIT=` line before this file was written. Seldon suite: 1969 passed, 0 skipped, `EXIT=0`. Here, `make gate-fast`: 2274 passed, 3 skipped, 25 deselected, 12 xfailed, `EXIT=0`. `make gate-full`: 2299 passed, 3 skipped, 12 xfailed, 0 deselected, `EXIT=0`. `seldon verify` and the protected-paths check both reached `EXIT=0`. Table in §5.

---

## 0. The notifier contract as implemented, and the `seldon.yaml` line

**Where.** `seldon/commands/dispatch.py::_notify`, called from `_pass` once per finished task:

* **ok branch:** after `dispatch_finished` is appended.
* **not-ok branch:** after `dispatch_finished` and after `_block` has walked the task to `blocked`.

In both branches it runs before `_record_and_push`, so a `dispatch_notify_failed` event ships in the same commit. There is one notification per finish, never one per record.

**Config** (`seldon/core/dispatch.py::load_dispatch_config`):
* **`dispatch.notify`:** optional. When present it must be a non-empty string; anything else raises `DispatchConfigError` at load.
* **`dispatch.notify_timeout_s`:** optional. It must be a positive number and a bool is refused. The default is `NOTIFY_TIMEOUT_S_DEFAULT = 30`.
* **Absent `notify`:** no child is run and no event is written.

**How the command runs.**
* It runs as `/bin/sh -c <notify>` with cwd at the project root, stdin closed, stdout and stderr captured, and `start_new_session=True` so it has its own process group.
* The pass waits at most `notify_timeout_s`, then kills the whole group with `os.killpg`.
* The outcome reaches the child only through the environment and is never substituted into the command text. A task name is data, and the way git hooks and systemd units hand context to a command is the environment.

| variable | value |
|---|---|
| `SELDON_NOTIFY_TASK_ID` | full artifact id |
| `SELDON_NOTIFY_TASK_NAME` | the ResearchTask's `name`, falling back to the file stem |
| `SELDON_NOTIFY_OK` | `true` / `false` (the `ok` of `dispatch_finished`) |
| `SELDON_NOTIFY_OUTCOME` | `ok` / `blocked`. Added beyond the task's six, so a template needs no shell conditional (§4 premise 6) |
| `SELDON_NOTIFY_RESULT_PATH` | `cc_tasks/<stem>_RESULT.md`, repo-relative |
| `SELDON_NOTIFY_LOG_PATH` | `logs/dispatch/<stem>.log`, repo-relative |
| `SELDON_NOTIFY_WALL_SECONDS` | the session's wall clock, as recorded on `dispatch_finished` |

**Failure handling.**
* **What counts as a failure:** a nonzero exit (which covers a missing binary: `sh` returns 127), a timeout, or any exception while spawning.
* **What a failure writes:** exactly one `dispatch_notify_failed` event, actor `dispatcher`, with payload `{task_id, command, reason: nonzero_exit|timeout|error, exit_code|timeout_s|error, output_tail}`.
* **What a failure never touches:** the finish record, the task's state or the pass's exit code. `_notify` never raises.
* **A successful notification** writes no event. The finish it reports is already on the log, so it only prints `notify: sent (<id8> ok|blocked)` to the wrapper log.

**The line in this repo's `seldon.yaml`** (dispatch block, after `log_dir`, with its reasons in the comment above it):

```yaml
  notify: >-
    osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "Seldon"'
    -e 'end run' "$SELDON_NOTIFY_TASK_NAME — $SELDON_NOTIFY_OUTCOME"
  notify_timeout_s: 30
```

The body is passed to AppleScript as `argv`, so a quote in a task name stays data and is not parsed as AppleScript. The title is `Seldon` and the body is the task name plus `ok` or `blocked`.

**Swapping to a phone push** is an example, not the default: the dispatcher's own network stays local. The comment in `seldon.yaml` gives it as one line:

```yaml
  notify: curl -fsS -d "$SELDON_NOTIFY_TASK_NAME: $SELDON_NOTIFY_OUTCOME" https://ntfy.sh/<topic>
```

**Tests** (`seldon/tests/test_dispatch_notify.py`, 15 cases, all run against the stub CC):
* **Environment:** all seven variables reach the child. The task name is set to differ from the stem so the test can tell them apart.
* **Ordering:** `dispatch_finished` is already on the log when the notifier runs. On the blocked path, the last event before the notifier is the walk to `blocked`.
* **Once per finish:** exactly one call on each path.
* **Failures:** a nonzero exit, a missing binary and a `sleep 30` under a 1 s timeout each produce one `dispatch_notify_failed`, with the task still `completed` and `dispatch_finished.ok` still true.
* **No key:** no `notify` key means no event.
* **Config refusals:** four bad `notify` values and four bad `notify_timeout_s` values are refused at load.
* **Default:** the timeout defaults to 30.

## 1. Commits

**Seldon** (`/Users/brock/GitHub/seldon`, `main`, pushed):

| commit | what |
|---|---|
| `19dd4d5` | fix: the dispatcher notifies on finish; issue commands name their actor; Desktop registration hashes the spec |
| `1f67389` | Merge `fix/dispatcher-notifies` |
| `9859205` | fix: one notify and one record commit per finish branch (§4 premise 9) |
| `42dbd47` | Merge `fix/notify-per-branch`. **The code this repo's gate ran against.** |

Files changed:
* `seldon/commands/dispatch.py`, `seldon/core/dispatch.py`, `seldon/commands/issue.py`, `seldon/config.py`, `seldon/mcp_server.py`, `tests/conftest.py`.
* New: `tests/test_dispatch_notify.py`, `tests/test_cli_actor.py`, `tests/test_cc_register_hash.py`.

**The tests were written first and seen failing** before any code changed. That was a foreground run whose output was not saved to a file: 18 failed across `test_dispatch_notify.py` and `test_cc_register_hash.py`, and `test_cli_actor.py` failed at collection on `ImportError: cannot import name 'resolve_cli_actor'`. The failures were for the reasons the tests name:
* `EVENT_NOTIFY_FAILED` did not exist, and `load_dispatch_config` accepted a bad `notify` without error.
* The hash test read `assert None == 'd0f1150d…'`, and `cc complete` printed `no registered file_hash`.

**ai-readiness-kg** (this repo): the commit that carries this RESULT. It contains:
* **`seldon.yaml`:** the notify block (decision 1).
* **`scripts/jobs/airkg_dispatch.sh`:** `LOG="${AIRKG_DISPATCH_LOG:-$REPO/logs/airkg_dispatch.log}"`, with `LOG_DIR` derived from it and the rotation glob keyed on its basename (decision 4).
* **`tests/test_dispatch_config.py`:** `_bare_env_run(home, log)` passes `AIRKG_DISPATCH_LOG`. The credential-refusal fixture now writes to `tmp_path` and asserts that the live log gained no credential refusal. The three tests that run a real pass pass `LIVE_LOG` explicitly, because they read the live log back by design.
* **`scripts/check_protected_dispatcher_notifies.sh`:** this task's protected-paths check.
* **`seldon_events.jsonl`:** this task's lines, plus the dispatcher's one `lease_held` refusal `774d5b41` (15:00:49Z). The dispatcher leaves that refusal uncommitted by design while a session holds the lease.

**Decision 4, observed live.** `logs/airkg_dispatch.log` held 19 fixture-written `no Neo4j credentials` refusals before this task. It still held 19 after `gate-fast` and `gate-full`, each of which ran that fixture once. The existing lines are left in place, as decided. They are listed in §4 premise 3.

## 2. The hand-fired notification, and the first automatic one

The configured `notify` string was read from `seldon.yaml` and run once by hand from this session as `/bin/sh -c "$CMD"`, with every `SELDON_NOTIFY_*` set:
* `TASK_ID=2881767c-…`, `TASK_NAME="dispatcher notifies (hand-fired test)"`, `OK=true`, `OUTCOME=ok`, and this task's RESULT and log paths.

**It fired at 2026-09-17T14:54:38Z, and `osascript` exited 0.** Exit 0 means macOS accepted the AppleScript `display notification` call. This headless session cannot see the screen. Whether a banner actually appeared depends on the notification permission macOS grants the calling process, and the operator is the only one who can confirm that.

**The first automatic notification belongs to the successor, not to this task.** The dispatcher process that launched this session (`dispatcher:HexagonMBP.local:54245`) loaded Seldon before `_notify` existed, so its `dispatch_finished` for this task runs no notifier. The next launchd pass is a fresh process running `42dbd47` (the installed `seldon` is an editable install of the Seldon checkout). So the first notification the dispatcher sends on its own is for the next task it dispatches.

## 3. The actor and hash fixes, and this task's own transitions

**Actor (decision 2).**
* **The resolver:** `seldon.config.resolve_cli_actor()` returns `cc` when `CLAUDECODE` is set and not `"0"`, or when `CLAUDE_CODE_SESSION_ID` is non-empty. Otherwise it returns `human`. Both variables are set by Claude Code in every shell it spawns (code.claude.com/docs/en/env-vars), and this session's environment has `CLAUDECODE=1`.
* **Where it is used:** `issue create` and `issue update` now stamp it on all four of their writes: create, the `affects` links, the property update and the transition.
* **Live check:** from this session, `resolve_cli_actor()` printed `cc`.
* **Isolation:** the suite's autouse fixture now also clears `CLAUDECODE`, so a suite run from inside a CC session and one run from a terminal stamp the same actor.
* **Tests:** `tests/test_cli_actor.py` covers the resolver in 7 cases and the two CLI commands end to end, under `CLAUDECODE=1` and under neither variable.
* **Prior events** are not rewritten, as decided.

**Hash (decision 3).**
* **The fix:** `seldon_cc_register` (the MCP tool) now registers through `seldon.commands.cc.register_task_file`. That is the same code path `seldon cc register` and the cadence use, and it records the spec-scoped `file_hash` and `hash_scope`. The MCP tool's own git guard still runs first and returns text; having passed it, the library call is told `allow_untracked=True`.
* **The test sequence** (`tests/test_cc_register_hash.py`) is the dispatcher's own: register the file untracked through the MCP tool, commit it with `D.commit_paths`, then run `cc complete`.
  * The commit leaves the bytes unchanged (asserted).
  * The node carries `file_hash == _spec_hash(file)`, `hash_scope` set to spec, and `created_by: desktop`.
  * `cc complete` after a Findings append succeeds with no "no registered file_hash" warning.
  * `cc complete` after a spec edit exits 1 with "SPEC has been modified since registration".

**This task's own record does not show a hash check that ran, and cannot** (§4 premise 4). `2881767c` was registered at 14:40:51Z (`artifact_created` `fcdd780a`, actor `desktop`) by the MCP server's pre-fix code, so its node has no `file_hash`, and `seldon cc complete` below prints the legacy warning. Two facts show the spec was not edited:
* `git diff --quiet HEAD -- cc_tasks/2026-09-17_dispatcher_notifies.md` is clean.
* The protected-paths check asserts the file is unmodified. It was last committed by the dispatcher's registration commit `9d23f7f`.

This task's transitions so far:

| event | time (Z) | type | actor | |
|---|---|---|---|---|
| `fcdd780a` | 14:40:51 | `artifact_created` | desktop | registration, no `file_hash` |
| `cbc665c3` | 14:40:57 | `link_created` | desktop | |
| `2cf0d525` | 14:45:08 | `artifact_state_changed` | dispatcher | proposed → accepted |
| `cd1a0a53` | 14:45:09 | `artifact_updated` | dispatcher | claim marker |
| `eb3d1f6a` | 14:45:09 | `artifact_state_changed` | dispatcher | accepted → in_progress |
| `af6811bc` | 14:45:09 | `dispatch_launched` | dispatcher | |

The completion events written by `seldon cc complete` are listed in §3a, which was added after the command ran.

### 3a. `seldon cc complete`, run after the gate (exit 0)

| event | time (Z) | type | actor | |
|---|---|---|---|---|
| `aca3d9ec` | 15:34:39 | `artifact_updated` | **cc** | `completed_at` |
| `0d8a82da` | 15:34:39 | `artifact_state_changed` | **cc** | in_progress → completed |

As premise 4 predicts, the command printed `WARNING: Task has no registered file_hash. Skipping immutability check.` for this task. **No hash check ran on this task's own record.** The check that runs is shown only by `tests/test_cc_register_hash.py`, until the first Desktop registration made after the MCP server restarts.

## 4. Premises this task file got wrong

1. **Decision 3 named the wrong code path.** The file says "`seldon cc register` records the file's hash whether or not the file is git-tracked", and its write set names `seldon/commands/cc.py`. But `register_task_file`, which is `cc register`'s code, already hashed untracked files; `allow_untracked` never skipped the hash there. The unhashed path was `seldon/mcp_server.py::seldon_cc_register`, the Desktop's MCP tool, which carried its own copy of registration without the hash. The fix is in `mcp_server.py`, a file outside the named write set. Rather than add a hash line to the copy, the copy was replaced with a call to the single code path.
2. **"Whatever `cc complete` uses to stamp `cc`" does not exist.** `cc complete` hard-codes the literal `actor="cc"`; there is no resolver to reuse. `resolve_cli_actor()` was written instead, from Claude Code's documented environment variables. `cc complete` keeps its literal, because its name already fixes its caller.
3. **The stray `REFUSING` line at 02:04:06Z was not "the last of its kind".** `logs/airkg_dispatch.log` holds **19** fixture-written `no Neo4j credentials` refusals, and all 19 name a `pytest-of-brock` temporary `.env`. Their timestamps (Z):
   * 2026-09-16: 03:43:18, 03:50:40, 04:27:47, 04:36:54, 04:38:54, 11:17:33, 11:17:43, 11:23:46, 11:30:56, 15:15:44, 15:16:06, 15:30:21, 15:37:44, 16:23:07, 16:45:38.
   * 2026-09-17: 02:04:06, 02:44:23, 11:04:22, 11:08:35.

   **The last of its kind is 2026-09-17T11:08:35Z.** The count was still 19 after this task's two gate runs.
4. **§3 asks for "a hash check that ran" on this task's own transitions, and this task cannot supply one** (§3). This task was registered by the pre-fix code.
   * **Wider effect:** the Desktop's MCP server is a long-lived process, so it keeps running the pre-fix `seldon_cc_register` until Claude Desktop (or its Seldon MCP server) is restarted. Until then, Desktop registrations still record no `file_hash`.
   * **So:** the first live hash check belongs to the first task registered after that restart.
   * **Same class as decision 5:** that is the same kind of fact the task recorded about the dispatcher. The dispatcher side needs no restart, because each launchd pass is a new process.
5. **The write set omitted files the decisions require.**
   * `seldon/core/dispatch.py`: config validation and the event name.
   * `seldon/config.py`: the resolver.
   * `seldon/mcp_server.py`: premise 1.
   * `tests/conftest.py`: environment isolation.
   * `scripts/check_protected_dispatcher_notifies.sh` here: each task in this series ships its own check.
6. **Six variables → seven.** `SELDON_NOTIFY_OUTCOME` (`ok`/`blocked`) was added. Without it, the configured one-line `osascript` body would need a shell conditional to turn `OK=true` into a word. The addition does not change the six.
7. **"Runs detached with a 30 s timeout" is two properties in tension.** It was implemented as its own process group with stdin closed, a bounded wait, and a group kill at the timeout. The pass does wait, for at most `notify_timeout_s`, because a failure must be recorded as `dispatch_notify_failed`, and a fully detached child's failure could not be. The wait happens while the lease is held and after the finish is recorded, so a hung notifier costs at most 30 s of one pass.
8. **"Integration tests on real data" for the osascript line.** No automated test drives `osascript`. A test that put a banner on the operator's screen on every suite run would be wrong. The automated tests use a recording notifier, and the real line was exercised once, by hand, in §2.
9. **My own intermediate defect.** The first Seldon merge (`1f67389`) called `_notify` and `_record_and_push` once, after the if/else. The behaviour was identical, but `scripts/check_protected_dispatcher_commits_its_record.sh`, the check from an earlier task, counts two `_record_and_push(` calls after the launch, so it began printing `NO  the finish is committed on both the ok and the blocked branch`. `9859205` restores one notify and one commit per branch. That older check now prints all `ok`, and the Seldon suite was re-run (1969 passed) before that merge was pushed. The earlier task's script was not edited.
10. **Tier.** The task names `make gate-fast`. `CLAUDE.md` requires `make gate-full` before every push, so both were run; §5 quotes both.

## 5. Gate

Seldon suite at `9859205` / `42dbd47`: the tier is the whole suite. Here: the tier named by the task is `make gate-fast`, and `make gate-full` was also run because a push follows. No stored payload was touched.

| gate | passed | skipped | xfailed | deselected | wall clock | exit | log |
|---|---|---|---|---|---|---|---|
| Seldon `pytest tests/ -q -rs` at `19dd4d5` | 1969 | 0 | 0 | 0 | 223.23 s | `EXIT=0` | `/Users/brock/GitHub/seldon/logs/2026-09-17_dispatcher_notifies_suite.log` |
| Seldon `pytest tests/ -q -rs` at `9859205` | 1969 | 0 | 0 | 0 | 218.70 s | `EXIT=0` | `/Users/brock/GitHub/seldon/logs/2026-09-17_dispatcher_notifies_suite_2.log` |
| `make gate-fast` (`-rs`, `-m "not slow"`) | 2274 | 3 | 12 | 25 | 476.41 s | `EXIT=0` | `logs/2026-09-17_dispatcher_notifies_gate_fast.log` |
| `make gate-full` (`tests/ assessment/`, `-rs`), started 15:07:57Z | 2299 | 3 | 12 | 0 | 1488.04 s | `EXIT=0` | `logs/suite.log`, copied to `logs/2026-09-17_dispatcher_notifies_suite_full.log` |
| `seldon verify` | all checks passed (event log 34826 events readable, 130 task source files resolve) | | | | under 1 min | `EXIT=0` | `logs/2026-09-17_dispatcher_notifies_verify.log` |
| protected paths (`scripts/check_protected_dispatcher_notifies.sh`) | PASS: `docs/` and every measurement tree clean; `seldon.yaml` gained only the notify block; every modified path in the write set (4 before the RESULT, 6 on the re-run after it and `cc complete`); 5 of 5 point-of-task checks `ok` | | | | under 5 s | `EXIT=0` both runs | `logs/2026-09-17_dispatcher_notifies_protected.log`, `logs/2026-09-17_dispatcher_notifies_protected_2.log` |

**The three skips**, identical in both tiers here, quoted from the logs. This is the expected count.
```
SKIPPED [1] tests/test_dispatch_config.py:333: interactive_only: SELDON_SESSION_ID is set, so this is a dispatched session, which holds its own task's claim and dirties the tree for its whole life; the quiet checkout this test asserts cannot exist inside one. Run it from an operator shell.
SKIPPED [1] tests/test_scan_harness.py:281: E5 judges the cycle's controls, not a surface
SKIPPED [1] assessment/tests/test_g1_preservation.py:337: no dev proposition publishes SE and CI together
```
