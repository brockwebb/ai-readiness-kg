# RESULT — `cc_tasks/2026-09-18_registration_commits.md`

**Date:** 2026-09-18. **Executed by:** the dispatched Claude Code session (headless).
**Addenda:** none. `cc_tasks/2026-09-18_registration_commits_ADDENDUM*.md` was globbed before
§1 and again before §3; both globs matched nothing.
**Outcome:** every step ran to completion. Seldon `d9ad7d3` (merged as `ba484cc`, pushed);
this repo `ced3e16` plus the commit carrying this RESULT. Gate green: `gate-fast` as the task gate, then `gate-full` before the push (§4).

---

## 0. The registration event, with `source_commit`

`artifact_created` for a ResearchTask now always carries `properties.source_commit`:

```json
{
  "event_id": "…", "event_type": "artifact_created", "timestamp": "…Z",
  "session_id": "…", "actor": "desktop", "authority": "accepted",
  "payload": {
    "artifact_id": "<uuid, minted before the commit so the commit message can name it>",
    "artifact_type": "ResearchTask",
    "properties": {
      "description": "…", "name": "…", "source_file": "cc_tasks/<file>.md",
      "file_hash": "<sha256 of the spec>", "hash_scope": "spec",
      "source_commit": "<full 40-char sha of the path-scoped commit> | null"
    },
    "from_state": null, "to_state": "proposed"
  }
}
```

* **Untracked file:** `git add -- <file>`, then `git commit -q -m "register: <file> — task
  <id8> (<name>) committed by its registration" -- <file>`; `source_commit` is `HEAD` after
  it. The node gets the same property.
* **Tracked or staged file:** left alone; `source_commit: null`.
* **Commit refused** (hook, `index.lock`): registration succeeds, `source_commit: null`, a
  warning names the git error, and the file is **unstaged again** (`git rm --cached`) so the
  dispatcher's fallback sweep still sees it as untracked. If it stayed staged, the sweep
  (keyed on `git ls-files`) would read it as tracked and nobody would ever commit it.
* The event line is written **after** the commit it names, so the event store is never in the
  registration commit (decision 1: only that path is staged).

## 1. Commits

**Seldon** (`/Users/brock/GitHub/seldon`, branch `feat/registration-commits`, merged `--no-ff`
to `main`, pushed; `main...origin/main` level after push):

| sha | what |
|---|---|
| `d9ad7d3` | `feat: registration commits the untracked task file it registers, path-scoped` |
| `ba484cc` | merge commit |

Files: `seldon/commands/cc.py` (`_commit_registered_file`, called from `register_task_file`),
`seldon/core/artifacts.py` (`create_artifact(..., artifact_id=None)`), `seldon/mcp_server.py`
(prints `source_commit`), `seldon/commands/dispatch.py` (`_commit_registration_records`),
`seldon/core/dispatch.py` (`appended_events`, factored out of `own_appended_lines`, whose
behaviour is unchanged), `tests/test_cc_register_commits.py` (new, 6 tests),
`tests/test_cc_register_hash.py` (sequence updated), `tests/test_dispatch_launch.py` (+2 tests).

Tests written first and seen red: the 6 in `test_cc_register_commits.py` failed before the
implementation (`6 failed`); `test_the_record_of_a_self_committing_registration_is_committed_by_the_next_pass`
failed at `assert len(shas) == 1` before the sweep change. They cover the three cases the task
names (untracked gets committed and `source_commit` set; tracked left alone; failing commit
leaves registration intact), plus staged-left-alone, nothing else in the tree swept up
(untracked, modified and **staged** session work all survive the registration commit), the CLI
path, and the sweep: it commits the record, and it does not commit while a claim is in flight.

**Seldon suite:** `1994 passed in 220.51s`, 0 skipped, 0 xfailed, 0 deselected, `EXIT=0`
(`/Users/brock/GitHub/seldon/logs/2026-09-18_registration_commits_suite2.log`). The first run
(`…_suite.log`) had `3 failed, 1991 passed`, all three in `test_cc_register_hash.py`. Its
helper committed the file the way the dispatcher did, and now there was nothing left to commit.
The helper now asserts that registration made the commit and that the bytes are unchanged.

**This repo:** `ced3e16` `feat: one shared protected-paths exclusion; DN-006 ADDENDUM_06`,
then the commit carrying this RESULT and `seldon_events.jsonl`.

**The installed Seldon is the checkout** (`seldon.__file__` →
`/Users/brock/GitHub/seldon/seldon/__init__.py`), so the CLI and the next dispatcher pass run
the new code as soon as they start. **An MCP server process the Desktop already had running
keeps the old code until it restarts.** Until then, a Desktop registration behaves as before,
and the dispatcher's sweep is its fallback.

## 2. The helper, and the checks that source it

`scripts/check_protected_lib.sh` (new; POSIX sh, because 14 of the checks are `#!/bin/sh`)
defines a shell function `git` that runs `command git` and filters the three name-listing forms
the checks use:

| form | dropped |
|---|---|
| `git diff --name-only …` | `seldon_events.jsonl` |
| `git ls-files --others|-o …` | `seldon_events.jsonl`, `cc_tasks/<name>.md` (top level) |
| `git status --porcelain …` | any `seldon_events.jsonl` line; `?? cc_tasks/<name>.md` |

All other git calls pass through, and git's exit status is returned. **Not excluded:** a modified
*tracked* `cc_tasks/*.md` (the "prior RESULT changed" guards keep working) and the store's
content diff (the append-only guards keep working). `tests/test_check_protected_lib.py` (new,
5 tests) runs the helper under `/bin/sh` against a real git tree and asserts statically that every
check sources it on line 2.

**Sourced on line 2** (`. "$(dirname "$0")/check_protected_lib.sh"`, before each script's `cd`)
**by all 35:** `a1a8b3d4`, `a3a10`, `abstract_five_checks`, `c4`, `cadence_and_enable`,
`cited_metadata`, `claude_md_dn005`, `dcat_rules`, `derived_counts`, `dispatch_idempotence`,
`dispatcher_commits_its_record`, `dispatcher_notifies`, `ephemeral_provenance`, `f5`,
`g1d_leaves_l0`, `gen9`, `mcp`, `measurement_tiers`, `network_allowlist`, `notional_bands`,
`prescriptions`, `publication_guards`, `publish_l0`, `rejudgements`, `rule_a12_v3`, `score`,
`sd_rules`, `self_cycle_promote`, `self_row`, `single_writer`, `sources_appendix`,
`standing_dispatcher`, `standing_guards`, `tool_docs`, `unassigned_tiers`
(`scripts/check_protected_<name>.sh`). Each gained exactly one line and lost none (numstat
`1 0` on all 35, asserted in the protected-paths log).

**`scripts/check_protected_score.sh` in the live checkout, after `ced3e16`**, with a foreign
untracked `cc_tasks/2026-09-18_zz_foreign_registration_probe.md` present (standing in for a
Desktop registration whose commit failed) and a `dispatch_refused` line the dispatcher appended
to `seldon_events.jsonl` at `2026-09-18T10:32:07Z` while this session held the tree:

```
   design page: generated, and names no body
PROTECTED PATHS OK
EXIT=0
```
(`logs/2026-09-18_registration_commits_score_check_live.log`.) The counterfactual, run in the
same state with the source line removed (`logs/2026-09-18_registration_commits_score_check_counterfactual.log`):
`FAIL moved outside the write set: cc_tasks/2026-09-18_zz_foreign_registration_probe.md`,
`EXIT=1`. This is the scoring session's failure, reproduced. The probe file was then deleted.

**DN-006 ADDENDUM_06** (`docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_06.md`;
01–05 existed) covers decisions 1 to 4. Its §2 gives the git semantics: `git commit -- <path>`
is `--only` mode, which commits that path's working-tree content and leaves every other index
entry as it was (git-commit(1)). The one contention is `index.lock`, and registration is the
side that loses it.

## 3. Premises this task file got wrong

1. **"DN-006 decision 3 (the dispatcher commits Desktop-registered files)."** DN-006's decision 3
   is the supersession marker. The dispatcher's commit is DN-006 ADDENDUM_03 §2, implemented as
   `cc_tasks/2026-09-16_dispatch_idempotence.md` decision 3. ADDENDUM_06 cites it correctly.
2. **The write set left out the dispatcher, and the change needs it.** ADDENDUM_03 §2's sweep
   committed the task file *and the event store together*, because the registration's
   `artifact_created` line in the tracked store keeps c7 false for the whole queue. With the
   file committed at registration, the sweep (keyed on an untracked file) never fires. The line
   then stays dirty until a dispatched session happens to commit the store, and with nothing
   dispatchable, none will. That is ADDENDUM_03 §2's wedge again. So
   `seldon/commands/dispatch.py` and `seldon/core/dispatch.py` changed. The sweep now also
   commits the store when an uncommitted appended line is a ResearchTask `artifact_created` with
   a `source_commit`. It uses the same gates as the old sweep (no claim in flight, configured
   branch) plus one more: the store must be append-only against HEAD. Also outside the declared
   write set: `seldon/core/artifacts.py`, `seldon/mcp_server.py`,
   `tests/test_cc_register_hash.py`, `tests/test_dispatch_launch.py`, and
   `tests/test_check_protected_lib.py` here (constitution §5: every feature has tests).
3. **"Records the commit sha on the registration event."** The event can name the commit only if
   the commit exists first. So the commit comes first, and the event, written after it, is not in
   it. The commit message names the task id, so the id is minted before `create_artifact`,
   which now accepts one.
4. **"`cc_tasks/*.md` … never protected paths."** Taken literally, this would also blind the
   guards that fail on a *modified* prior RESULT or task file (`gen9`, `f5`, `g1d_leaves_l0`,
   `rejudgements`, and the `prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md')`
   lines). No actor other than the session writes those, since task files are immutable once
   written. So the exclusion covers **untracked** `cc_tasks/*.md` only: what registration and
   addenda actually produce.
5. **"One shared exclusion … not eight copies" / "no other line moves."** There are 35 checks,
   not eight, and they list the tree three different ways. The only way to share one exclusion
   and move no other line was to interpose on `git` itself. The helper's header says so.
6. **"`seldon cc register` runs `git add`."** The CLI still refuses an untracked file unless
   `--allow-untracked` is passed. That guard is unchanged and was not in scope. The Desktop
   registers through the `seldon_cc_register` MCP tool with `allow_untracked=True`. Both reach
   the same `register_task_file` and commit the same way.
7. **"If the commit fails … the dispatcher's pass commits it later as before."** This is true only
   if the failed commit leaves the file untracked, not staged. The code implements that, and a
   test asserts it.
8. **"The scoring session's live check re-run … must be green."** On a clean checkout the
   check passes with or without this change, so a green run proves nothing. The run was made
   meaningful with a foreign untracked task file in the tree, and the same state without the
   helper was shown red (§2).

## 4. Gate

**Tier: `make gate-fast`** (`-rs`). No rule module, registry or re-derivation engine changed,
so `gate-task` adds nothing.

| gate | result | log |
|---|---|---|
| Seldon full suite | `1994 passed`, 0 skipped, 0 xfailed, 0 deselected, `EXIT=0`, 220.51 s | `/Users/brock/GitHub/seldon/logs/2026-09-18_registration_commits_suite2.log` |
| `make gate-fast` | `2502 passed, 3 skipped, 25 deselected, 12 xfailed`, `EXIT=0`, 500.41 s | `logs/2026-09-18_registration_commits_gate_fast.log` |
| `make gate-full` (pre-push, CLAUDE.md) | `2527 passed, 3 skipped, 0 deselected, 12 xfailed`, `EXIT=0`, 1469.26 s | `logs/2026-09-18_registration_commits_gate_full_suite.log` (copy of `logs/suite.log`) |
| `seldon verify` | `All checks passed.`, `EXIT=0` (142 task source files resolve; 34933 events readable) | `logs/2026-09-18_registration_commits_verify.log` |
| protected paths (this task's write set) | `protected paths: PASS`, `EXIT=0` | `logs/2026-09-18_registration_commits_protected.log` |
| `check_protected_score.sh`, live | `PROTECTED PATHS OK`, `EXIT=0` | `logs/2026-09-18_registration_commits_score_check_live.log` |

The three skips, the same three in both tiers: `tests/test_dispatch_config.py:333` (interactive only;
`SELDON_SESSION_ID` is set in a dispatched session), `tests/test_scan_harness.py:283` (E5
judges controls, not a surface), `assessment/tests/test_g1_preservation.py:337` (no dev
proposition publishes SE and CI together). All three were pre-existing and are unrelated to
this task.

The protected-paths run was a logged inline check, not a new `scripts/check_protected_*.sh`,
because the write set named none. It asserted: every moved path is in the write set (the 35
checks, ADDENDUM_06, the test, `seldon_events.jsonl`, this RESULT); `docs/` is otherwise
byte-identical; each check changed by exactly `+1 −0`; and `seldon_events.jsonl` is
append-only. `logs/` is gitignored, so these logs stay on this machine.

The wall-clocks: `gate-fast` 500.41 s and `gate-full` 1469.26 s. The task named `gate-fast`. `gate-full` also ran because `CLAUDE.md` requires it before every push.
