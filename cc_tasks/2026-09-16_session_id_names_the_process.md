# CC Task: an event's session_id names the process that wrote it, not a file nobody closed

**Date:** 2026-09-16
**Project:** ai-readiness-kg (all code lands in `/Users/brock/GitHub/seldon`; the Issue disposition and RESULT land here)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips_RESULT.md` §4 and Issues `5c6f694a` (session_id smear) and `7af77cb8` (`seldon issue create` not atomic).
**Implements:** the provenance invariant of this repo (every event says who wrote it and when) applied to Seldon's own log, and DN-006 decision 7 (dispatch events are attributable).
**Framework layer served (DN-005 §5 rule 1):** none. Provenance hygiene of the tracking system itself.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push` to both repos' own remotes.

---

## 0. The defect, stated once

`seldon/config.py:86 start_session` writes `.seldon/current_session.json` and returns the existing id if the file exists. Only `seldon briefing` starts one and only `seldon closeout` ends one; `seldon handoff`, the command Desktop sessions actually close with (AD-030-R9), does not. This repo's file has held `87ea77ee` since 2026-08-22. Every writer (`cc.py`, `dispatch.py`, `result.py`, `issue.py`, `link.py`, `verify.py`, `governed.py`, `task.py`) stamps it. 34,137 of 34,777 events carry it, across actors `human`, `cc` and `dispatcher`. The field is present on every event and identifies nothing.

Prior art, read before designing (the shape below is taken from it): a session or trace identity is generated at the root process and propagated to children through the environment, never recovered from a mutable file on disk (W3C Trace Context `traceparent`; OpenTelemetry context propagation). Where a file must stand in for a live process, its authority is bounded by age and holder identity, not assumed (Chubby, Burrows OSDI 2006, already cited by `seldon/core/dispatch.py`; conventional lockfile staleness). Claude Code already sets `CLAUDE_CODE_SESSION_ID` in every Bash call of a session, which is the root id for interactive and headless CC sessions alike.

**Decisions taken here (operator overrides later):**

1. **Resolution order for `get_current_session`.** (a) `SELDON_SESSION_ID` if set in the environment. (b) `CLAUDE_CODE_SESSION_ID` if set. (c) the seldon-mcp server's own id, generated once per server process and held in memory, for calls arriving over MCP. (d) `.seldon/current_session.json` only if its `started_at` is within 24 hours; the constant is declared in one place with this task cited beside it. (e) otherwise a fresh id, written to the file. Case (d)'s bound is the Chubby-style rule: a claim of a live session older than a working day is not evidence of one.
2. **The dispatcher propagates, and records, the child's id.** `_run` sets `SELDON_SESSION_ID` to a fresh id for the child, and `dispatch_launched` and `dispatch_finished` carry it as `child_session_id`. The dispatcher's own events keep the dispatcher process's id. A reader can then join a task's `cc`-actor events to the launch that produced them.
3. **`seldon handoff` ends the session file**, exactly as `closeout` does. A Desktop session that closes by the documented command leaves no live session behind.
4. **`seldon issue create` validates every link before its first append** (Issue `7af77cb8`). A refused link writes nothing. A test asserts the store is byte-identical after a create that fails link validation.
5. **The log is not rewritten.** The 34,137 stamped events stay as they are (append-only). This RESULT records the boundary: the last event carrying `87ea77ee` and the first carrying a process-derived id, by event id and timestamp, so a reader knows where `session_id` starts meaning something. Issues `5c6f694a` and `7af77cb8` are moved to `resolved` with a note citing this RESULT; no new Issue is opened for the historical smear because the boundary line is its disposition.

**Write set:** `seldon/config.py`, `seldon/commands/dispatch.py`, `seldon/commands/session.py` (handoff), `seldon/commands/issue.py`, the MCP server's session init, and tests for decisions 1 to 4 in the Seldon repo; `seldon_events.jsonl` here by this task's transitions and the two Issue state changes; the RESULT. Nothing else. `docs/` byte-identical.

**Immutable once written. Glob `2026-09-16_session_id_names_the_process_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Seldon repo: decisions 1 to 4 with tests, written first and seen failing. Seldon suite green with zero skips (the fixture now fails instead; quote the counts). Merged, pushed.
## 2. This repo: decision 5's boundary line and the two Issue transitions. Confirm from the store that this session's own `cc`-actor events carry the id the dispatcher put in `SELDON_SESSION_ID` and that `dispatch_launched` for this task carries the same value as `child_session_id`. That is this task's live observation and it exists only in this session's window; capture it before §3.
## 3. Gate
`make gate-fast` (no stored payload touched, no push from this repo until it is green), `seldon verify`, protected paths. Detached with `nohup bash -c '<cmd>; echo EXIT=$?' > log 2>&1 &`, polled inside this turn with a bounded `grep -q '^EXIT='` loop. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-16_session_id_names_the_process_RESULT.md`: §0 the live observation from §2; §1 both repos' commits and the resolution order as implemented; §2 the boundary line; §3 the Issue transitions; §4 every premise this task file got wrong; §5 the gate table with passed, skipped, xfailed, deselected, wall clock and log path per row, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (merged before §2) → §2 → glob addenda → §3 → §4 → push both repos.
