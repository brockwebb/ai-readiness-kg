# RESULT: a headless session has no next turn; every gate it starts is polled to completion inside the turn

**Task:** `cc_tasks/2026-09-16_headless_session_polls_to_completion.md` (no addenda: the glob matched nothing before §1 or before §4)
**Date:** 2026-09-16
**Outcome:** complete. Every section ran to the end, and every gate row below has `EXIT=0` in its log.

## 0. How this session handled its own headlessness

The dispatcher launched this session (`logs/dispatch/2026-09-16_headless_session_polls_to_completion.log`, first line `=== 2026-09-16T16:15:32.640232Z | dispatch | claude -p 'Read CLAUDE.md, then execute ...`). The environment showed `CLAUDE_CODE_ENTRYPOINT=sdk-cli` and `CLAUDE_CODE_SESSION_ATTENDED=0`, and `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` was unset. So this session ran under the old prompt without the guard, and its Bash tool still offered `run_in_background`. It never used that mode.

Every command that could run for more than two minutes was started as `nohup bash -c '<cmd>; echo EXIT=$?' > <log> 2>&1 &`. It was then waited on inside this turn by a single foreground Bash call running a bounded loop: `until grep -q '^EXIT=' <log> || [ $n -ge N ]; do sleep 5; ...; done`.

| command | log | wait calls | loop iterations (5 s each) |
|---|---|---|---|
| Seldon full suite | `/Users/brock/GitHub/seldon/logs/seldon_suite_headless.log` | 1 | 40 |
| `make gate-fast` and `seldon verify` (started together, waited on together) | `logs/headless_gate_fast.log`, `logs/headless_seldon_verify.log` | 1 | 94 |
| Neo4j-tier spot check | `logs/headless_neo4j_tier.log` | 1 | 1 |
| protected paths | `logs/headless_protected.log` | 0 (finished in under 1 s; read directly) | none |

The first wait attempt was `sleep 180; tail -5 <log>`, which is the form the task prescribes. The harness blocked it before it ran (see §4, premise 1).

## 1. Prior-art outcome (decision 3): the guard exists

- `claude --help` (CLI 2.1.273) has no flag that disables background tasks. `--bg/--background` does the opposite: it backgrounds the whole session.
- `strings` on `/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe` turned up `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`, alongside `CLAUDE_AUTO_BACKGROUND_TASKS`, `CLAUDE_CODE_AUTO_BACKGROUND_TIMEOUT_MS` and `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`.
- Documentation, `https://code.claude.com/docs/en/env-vars.md` line 237: "`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` — Set to `1` to disable all background task functionality, including the `run_in_background` parameter on Bash and subagent tools, auto-backgrounding, and the Ctrl+B shortcut." `https://code.claude.com/docs/en/interactive-mode.md` line 312 says the same. The summarizing WebFetch reported the variable as absent, and a `curl | grep` of the raw page showed that was wrong. The raw page is the citation.

The `claude -p` call is not in `scripts/jobs/airkg_dispatch.sh`. It is built in `seldon/commands/dispatch.py::_launch_cmd` and run by `_run`, so the guard is set in `_run`. `HEADLESS_ENV = {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}` is written over the child's environment after the API-key strip, so an inherited `0` cannot turn background tasks back on.

## 2. Commits

- **Seldon** (`origin/main`): `466ceab` feat: a dispatched session is told it is headless and has background tasks disabled; merged as `c0b232c` from `feat/headless-launch-clause`. Files: `seldon/commands/dispatch.py` (`HEADLESS_CLAUSE`, `DISPATCH_LINE`, `HEADLESS_ENV`, `_run`) and `tests/test_dispatch.py`. One existing test was updated to expect the clause; two tests were added: the clause is in the prompt verbatim and appears once, and the child sees `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` with no API key. The tests were written first and failed with `ImportError` before the code existed.
- **ai-readiness-kg:** the commit that carries this RESULT. Files: `CLAUDE.md` (a **Headless sessions** paragraph under "Long-running commands"), `tests/test_dispatch_config.py::test_claude_md_headless_rule_is_the_launch_prompts_clause_byte_for_byte`, `seldon_events.jsonl` and this RESULT.

## 3. The two clause texts, side by side

| where | text |
|---|---|
| `seldon/commands/dispatch.py::HEADLESS_CLAUSE` (the last sentence of `DISPATCH_LINE`) | This session is headless: there is no next turn and ending it ends the process. Poll every detached command to its EXIT line inside this turn; never use background-task mode or wait to be notified. |
| `CLAUDE.md`, the **Headless sessions** paragraph | This session is headless: there is no next turn and ending it ends the process. Poll every detached command to its EXIT line inside this turn; never use background-task mode or wait to be notified. |

The test takes the text between `asserts the two are byte-identical: ` and ` The dispatcher also launches` in the paragraph and checks that its UTF-8 bytes equal the constant's.

## 4. Premises the task file got wrong

1. **The prescribed wait, `sleep 240; tail -5 logs/<name>.log`, cannot run in this harness.** Claude Code blocked `sleep 180; tail ...` with "To wait for a condition, use Monitor with an until-loop ... To wait for a command you started, use run_in_background: true." Both alternatives it offers deliver the result on a later turn, which is the failure this task exists to prevent. The fix that worked is one foreground Bash call running a bounded `until grep -q '^EXIT=' ...; do sleep 5; done` loop with a tool timeout of at most 600 s. `CLAUDE.md`'s long-running-commands section gives the same `sleep 240; tail -5` form. It was outside this task's write set and is unchanged; the successor should correct it.
2. **The prescribed detach form, `nohup ... > log 2>&1; echo EXIT=$? >> log &`, does not detach.** In `a; b &` only `b` goes to the background, so the `nohup` command runs in the foreground and blocks the tool call. This session used `nohup bash -c '<cmd>; echo EXIT=$?' > log 2>&1 &`. `CLAUDE.md`'s instruction to "append `; echo EXIT=$? >> logs/<name>.log`" to `nohup <cmd> > ... &` can be read the same wrong way.
3. **Decision 3 put the `claude -p` line in "`scripts/jobs/` or the launch call itself".** The wrapper only runs `seldon dispatch once`, and the `claude -p` command is built in Seldon. The guard is therefore in Seldon, and the wrapper is unchanged.
4. **Decision 3 named `claude --help` as a place to search.** It does not document the variable. Only the env-vars documentation page and the binary do.
5. **"This session was launched under the old prompt"** is correct, and it also lacked the guard (§0). Nothing this session did can show whether the clause works.

## 5. Gate

| row | passed | skipped | other | wall clock | exit | log |
|---|---|---|---|---|---|---|
| Seldon full suite (`pytest tests/ -q -rs`, `NEO4J_USERNAME`/`NEO4J_PASSWORD` exported from `~/.wintermute/.env`; the log records that they were set, not their values) | 1909 | **0** | none | 203.42 s | `EXIT=0` | `/Users/brock/GitHub/seldon/logs/seldon_suite_headless.log` |
| `make gate-fast` (tier: fast; no stored payload touched) | 2257 | 18 | 25 deselected (`slow`), 12 xfailed | 473.49 s | `EXIT=0` | `logs/headless_gate_fast.log` |
| Neo4j-tier spot check, `tests/test_framework_projection_roundtrip.py -rs` | 7 | 0 | none | 0.82 s | `EXIT=0` | `logs/headless_neo4j_tier.log` |
| `seldon verify` | "All checks passed." | none | none | not logged separately; ran alongside gate-fast, and both finished within 480 s of launch | `EXIT=0` | `logs/headless_seldon_verify.log` |
| protected paths: `docs/` byte-identical to `HEAD`; working-tree write set | `docs/ unchanged`; only `CLAUDE.md` and `tests/test_dispatch_config.py` modified | none | none | under 1 s | `EXIT=0` | `logs/headless_protected.log` |

The Makefile's `gate-fast` does not pass `-rs`, so the reasons for its 18 skips are not in the log. The Neo4j roundtrip row shows that the Neo4j tier ran rather than skipped in this environment. The 18 skips are not attributed further here. This is the fast tier; the full suite was not run.

## 6. The live proof belongs to the successor

This session ran under the old prompt without the guard, so its own log cannot show the clause or the environment variable working. That observation belongs to `cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips.md`, the first task the dispatcher launches after this change. Its RESULT §0 should quote its own dispatch log line, which should contain the headless clause, and its `dispatch_finished` event. It should also say whether its Bash tool still offered `run_in_background`, which it should not if `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` took effect. This RESULT claims neither observation.
