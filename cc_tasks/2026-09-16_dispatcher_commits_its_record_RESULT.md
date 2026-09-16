# RESULT — the dispatcher commits and pushes its own record

**Task:** `cc_tasks/2026-09-16_dispatcher_commits_its_record.md`
**Date:** 2026-09-16
**ResearchTask:** `c609b1e1-b294-4a75-931a-6e314ab1669b`
**Addenda:** none. Globbed twice (before §1 and before §4); `cc_tasks/2026-09-16_dispatcher_commits_its_record_ADDENDUM*.md` matched nothing both times.
**Gate:** green. Seldon suite on the merged commit, `make gate-fast`, `make gate-full`, `seldon verify` and the protected-paths diff all reached `EXIT=0` before this file was created.

---

## 0. Where this session stopped, and where the one before it did

This is the **second** session on this task. The first was launched by the standing dispatcher at
`2026-09-16T14:34:23Z` and is the first task ever launched by it under decision 3 of
`cc_tasks/2026-09-16_dispatch_idempotence.md`. It ran 624.431s, exited 0, and **wrote no RESULT**,
so the finish was recorded `ok: false` and the task was walked `in_progress -> blocked`
(`dispatch_finished` `804e0b27`, `artifact_state_changed` `0a235e61`).

Its own log says exactly how it died, and the sentence is worth keeping:

```
$ tail -2 logs/dispatch/2026-09-16_dispatcher_commits_its_record.log
I'll be notified when the Seldon suite finishes. Next step after that is merging and pushing
Seldon, then running this repo's gates.
EXIT=0
```

It backgrounded the Seldon suite and **ended its turn to wait for a notification that a headless
`claude -p` process never receives** — there is no next turn to be notified into, so the process
exited 0 with the work half done. `CLAUDE.md`'s long-running-commands rule already says "Do not
end the turn while a required command is still running"; what it does not say is that for a
dispatched session this is not a delay but a *termination*. §7 carries that forward.

What that session left on disk was complete and sound, and this session verified it line by line
rather than trusting it: the Seldon implementation and its 14 tests, this repo's cadence-reasons
test, the `CLAUDE.md` sentence, ADDENDUM_04 and the protected-paths check. Nothing of it was
rewritten. What this session did is what the first one never reached: run the gate for real,
merge and push Seldon, and write this file.

---

## 1. Both repos' commits

| repo | commit | what |
|---|---|---|
| seldon | `e593148` | `feat: the dispatcher commits and pushes the lines it writes` |
| seldon | `f459c98` | `Merge feat/dispatch-own-record: the dispatcher commits and pushes its own record` (pushed; `main...origin/main` level, branch deleted) |
| ai-readiness-kg | this commit | `tests/test_dispatch_config.py`, one sentence of `CLAUDE.md`, `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_04.md`, `scripts/check_protected_dispatcher_commits_its_record.sh`, this RESULT |

Seldon write set: `seldon/commands/dispatch.py` (+117), `seldon/core/dispatch.py` (+78),
`tests/test_dispatch_own_record.py` (new, 480 lines, 14 tests),
`tests/test_dispatch_launch.py` and `tests/test_cadence_pass.py` (two assertions each re-pointed:
they read a commit off `HEAD`, and the dispatcher's own record commits now follow the ones they
meant in the same pass, so they look their commit up by message instead).

## 2. The per-event table, as decision 1 requires it

For each line the dispatcher writes: who commits it, and whether this task changed that.

| line | lease held when written? | committed by | changed here? |
|---|---|---|---|
| `artifact_created` (Desktop registration) | — | the registration commit, ADDENDUM_03 §2 | no — already left the tree clean |
| claim transitions + `dispatch_launched` | yes | **this pass, before the launch** | **yes** — the session now opens on a clean, pushed tree |
| `dispatch_finished` (+ `blocked` transition) | yes | **this pass, after the finish, on both branches** | **yes** — this is ADDENDUM_03 §4, closed |
| `dispatch_refused{claim_failed}` | yes | **this pass** | **yes** |
| `cadence_created` | yes | the cadence commit, ADDENDUM_02 §1 | no — already left the tree clean |
| `dispatch_refused{lease_held}` | **no** | the session in flight, or the next pass's leftover sweep | no, by design |
| `dispatch_observed_stop` | **no** | the first pass under the lease after the STOP file goes | no, by design |
| `dispatch_refused{api_key_present}` | **no** | the first pass under the lease once the key is gone | no, by design |

The three written without the lease are never committed where they are written: a held lease is
the only way a pass knows no dispatched session is working in the checkout, and a `git commit`
beside a working session is DD-019's batch-identity class plus an `index.lock` collision. Every
pass that takes the lease with no claim in flight sweeps dispatcher-only leftovers first, which
also recovers from a pass that died between its append and its commit.

Two guards, both asserted: the commit is pathspec-limited to the store (`D.commit_paths`, git's
documented `--only`), and it is made only when every appended line carries `actor: dispatcher`
and the working copy begins with HEAD's bytes (`D.own_appended_lines`). A line a session or the
operator wrote is *their* finding, surfaced by c7 as a dirty tree — never laundered under a
dispatcher message.

## 3. The tree state after a finished dispatch — and the live proof of both decisions

The check is the tree, not the event. In the Seldon suite,
`test_a_finished_dispatch_leaves_the_event_store_clean` asserts
`git status --porcelain -- seldon_events.jsonl` is empty after a completed dispatch, and
`test_a_pass_after_a_finished_dispatch_creates_the_due_cadence_instance` carries it to the point:
a dispatch finishes in September, and the first pass at `2026-10-05T00:30Z` **creates** cycle 5
instead of reporting `dirty_tree`.

The same thing then happened in production, unprompted, and it is the best evidence in this file:

```
$ git log --oneline -2 -- seldon_events.jsonl
32e2de5 record: artifact_state_changed, artifact_updated, dispatch_launched, dispatch_finished
        c609b1e1 — 6 line(s) written by the standing dispatcher
69ad180 register: cc_tasks/2026-09-16_dispatcher_commits_its_record.md — registered task file
        committed by the standing dispatcher
$ git branch -r --contains 32e2de5
  origin/HEAD -> origin/main
  origin/main
$ git status --porcelain -- seldon_events.jsonl      # empty
```

`32e2de5` was written at 14:49:49 EDT, five minutes after the first session's finish at
14:44:47Z, by a **later** launchd pass — because the process that launched that session was still
running the code from before this change, exactly as ADDENDUM_04 §1 predicted. So the six lines it
left are the leftover sweep's first live customer, and
`test_a_line_left_by_an_earlier_pass_is_committed_by_the_next` is the test of it. That the commit
is on `origin/main` is decision 2 working in production: the dispatcher pushed what it committed,
with nobody asking.

## 4. The status output from inside the session — and the premise it fails

§3 of the task says this session "was launched by the dispatcher under a held lease" and asks for
`seldon dispatch status --json` showing a lease holder and a task in flight. **That is not this
session's state, and the RESULT does not pretend otherwise.** This session was hand-dispatched by
the operator after the first one died; the lease is free and the claim is gone:

```json
{"enabled": true, "branch": "main", "tree_dirty": true, "tree_dirty_count": 4,
 "lease": {"holder": null, "pid": null, "task": null,
           "last_holder": "dispatcher:HexagonMBP.local:88835",
           "acquired_at": "2026-09-16T15:25:07.411089Z",
           "released_at": "2026-09-16T15:25:07.903870Z"},
 "claim_in_flight": null, "candidates": 0, "eligible": []}
```

The task `c609b1e1` is not in `open_tasks` at all, because it is `blocked` — the first session's
finish put it there.

The concurrency §3 wanted to probe was nevertheless exercised, and more honestly than a
hand-held lease would have: **the launchd dispatcher fired every five minutes for the whole
~50 minutes of the gate** and interfered with nothing, because the tree was dirty (c7 false, so
no launch) and the store was clean (nothing for the record commit to do):

```
$ tail -6 logs/airkg_dispatch.log
=== 2026-09-16T15:50:16Z | airkg-dispatch fire
nothing eligible (24 open, 0 candidate(s))
=== rc=0
=== 2026-09-16T15:55:18Z | airkg-dispatch fire
nothing eligible (24 open, 0 candidate(s))
=== rc=0
```

`make gate-full` was therefore green **beside a live dispatcher**, not beside a held lease. What
that demonstrates is the thing worth demonstrating: a pass is a no-op against a session's dirty
checkout.

## 5. Every premise the task file got wrong

1. **"this session was launched by the dispatcher under a held lease" (§3).** False for the
   session that wrote this file, and unrecoverable for the one it was true of — that session
   never captured the status before it died. Desktop's defect, in the ordinary sense that a task
   file cannot know it will be run twice; but the deeper one is that §3 asked for evidence
   obtainable *only* from inside a dispatched session and gave no instruction for the case where
   that session fails. Evidence that exists in exactly one window needs capturing first, not last.
2. **"Not hand-dispatched" (SEQUENCING), and `CLAUDE.md`'s rule that the operator does not
   hand-dispatch while `dispatch.enabled` is true.** Both were overridden by the operator, who
   launched this session by hand. That is his to do — gates bind the machine, not the operator —
   and the DD-019 hazard the rule guards did not materialise: the dispatcher's concurrent passes
   are logged above and touched nothing. Recorded because the rule is machine-read and the
   exception is not.
3. **"§1 (merged before §2)".** The first session wrote §2's files into the tree before §1 was
   merged. This session restored the order — Seldon suite green, merged, pushed, *then* this
   repo's gate — so the sequencing constraint holds for the work as shipped, but it was violated
   in the interim and the tree carried §2 uncommitted for about an hour.
4. **"**Fulfils:** its own ResearchTask".** It did not, on the first attempt: the task is in
   `blocked`, not `in_progress`, so the completion in §6 is walked from `blocked`.
5. **The Seldon suite's Neo4j gate was vacuous on this machine, and has been all along.** Not a
   premise of this task but a finding that invalidates a claim every recent RESULT in both repos
   has made. `tests/conftest.py` reads `NEO4J_USERNAME`/`NEO4J_PASSWORD`; this machine exports
   `NEO4J_USER`/`NEO4J_PASS`. With neither set the fixture **skips rather than fails**, so an
   ordinary shell runs `1177 passed, 730 skipped` and calls it green — with all 14 of this task's
   new tests among the skips. `seldon/config.py:73` already bridges the two names for production
   code; the test fixture does not. Worse, `seldon/.env` holds the right values but nothing loads
   it, and `set -a; . .env` **cannot** load it, because the password contains an apostrophe and
   the file is unquoted:

   ```
   $ sh -c 'set -a; . /Users/brock/GitHub/seldon/.env; set +a; echo "len=${#NEO4J_PASSWORD}"'
   /Users/brock/GitHub/seldon/.env: line 3: unexpected EOF while looking for matching `''
   len=0
   ```

   The real run below exported the names explicitly and got `1907 passed, 0 skipped`. **A skip
   count is a number a gate has to read.** This repo's own suite already learned the apostrophe
   lesson once, in `test_the_credential_parse_strips_one_surrounding_quote_pair_and_no_more`,
   about the launchd wrapper; Seldon's fixture has not. Fixing it is the next task's, not this
   one's — this task's write set does not include `tests/conftest.py`.

## 6. Verification — every number below is re-readable at the cited path

| gate | result | wall clock | log |
|---|---|---|---|
| Seldon suite, feature branch, Neo4j reachable | `1907 passed` `EXIT=0` | 189.36s | `../seldon/logs/own_record_suite_neo4j.log` |
| Seldon suite, **on the merged commit `f459c98`** | `1907 passed` `EXIT=0` | 193.30s | `../seldon/logs/own_record_merged.log` |
| Seldon suite, no credentials exported (**rejected**) | `1177 passed, 730 skipped` `EXIT=0` | 26.05s | `../seldon/logs/own_record_suite.log` |
| `make gate-fast` | `2256 passed, 18 skipped, 25 deselected, 12 xfailed` `EXIT=0` | 426.70s (0:07:06) | `logs/gate_fast_dcir.log` |
| `make gate-full` | `2281 passed, 18 skipped, 12 xfailed` `EXIT=0` | 1357.68s (0:22:37) | `logs/gate_full_dcir.log` |
| `seldon verify` | `All checks passed.` `EXIT=0` | — | `logs/verify_dcir.log` |
| protected paths | `PASS` `EXIT=0` | — | `logs/protected_dcir.log` |

The third row is in the table because it is the run that looked green and was not; §5.5 is what it
means.

`seldon verify` reports 34759 events readable, all 123 task source files resolving, no blocking
tasks, and the five artifacts withdrawn by DD-066 still correctly withdrawn rather than stale.

Protected paths, all green: `docs/` byte-identical apart from ADDENDUM_04; exactly one line of
`CLAUDE.md` moved and it is the dispatch-protocol sentence; every modified path inside the write
set; nothing under `state/`, `events/`, `assessment/`, `kg/`, `framework/`, `corpus/` or the
control files touched. Its last section reads the *installed* dispatcher and asserts the five
orderings that are the point of the task — the leftover sweep before the cadence, the launch lines
committed before the session runs, the finish committed on both branches, the push retried on the
nothing-eligible branch, and the record commit pathspec-limited and actor-gated.

This task ran **zero model calls**, as declared. Network: `git push` to both repos' own remotes,
which the decisions require of the dispatcher and the header declares.

## 7. What the next OODA should verify first

1. **Seldon's Neo4j fixture** (§5.5). Two lines — read `NEO4J_USER`/`NEO4J_PASS` as fallbacks, as
   `seldon/config.py` already does — and the skip-vs-fail rule should key on *any* credential
   being set, not on `NEO4J_PASSWORD` alone. Until then every "Seldon suite green" in either
   repo's RESULTs means "green over 730 skipped tests" unless the session exported those two
   names. Re-read the recent RESULTs against that before trusting their gate lines.
2. **The headless-session termination rule** (§0). `CLAUDE.md`'s long-running-commands section
   should say that a dispatched session ending its turn to await a notification *ends the
   process*; a dispatched session must block in the foreground. The dispatcher already caught
   this one correctly — `result_present: false` -> `ok: false` -> `blocked` — which is the
   design working, but the session should not need catching.
3. **Cycle 5, `2026-10-05T00:00:00Z`.** The thing all of this protects. `next_due` reads
   `["2026-10-05T00:00:00Z", "2026-11-02T00:00:00Z", "2026-12-07T00:00:00Z"]`, `before_start` is
   true for September, and a blocked tick now prints its evidence beside its reason, so the first
   October pass is readable from `logs/airkg_dispatch.log` alone. Verify against that log, not
   against this paragraph.
