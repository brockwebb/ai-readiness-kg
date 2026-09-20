# RESULT — Seldon hygiene: a superseded artifact is a decision, a template can be rendered by hand, and a task names its predecessors in a header the dispatcher can read

**Date:** 2026-09-20
**Task:** `cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after.md` (`65e5da0e`) and its
`_ADDENDUM_01.md` (AMENDS; adds decision 6 and this §4a). Both were globbed and read before §1
and again before §3; neither carries a supersession marker.
**Executed by:** dispatched CC session, launched by the standing dispatcher at
2026-09-20T10:18:29Z (`fee6956`, `dispatch_launched 65e5da0e`).
**Spend:** zero model calls, as declared. **Network:** none beyond `git push` to both repos.

**Outcome: every decision landed, both repos are green, and one premise of ADDENDUM_01 was
wrong in a way that re-scopes decision 6 without cancelling either half of it (§4a, §5.3).**

---

## §0 — the grep that gates decision 3

§0.3 of the task file: *"Step 1 of §1 is a repo-wide `grep -rn -i sequencing seldon/` in the
Seldon repo. If a reader exists in a file not listed above, stop, write nothing, and report
it."*

```
$ cd /Users/brock/GitHub/seldon && grep -rn -i sequencing seldon/
(no output; 0 lines)
```

**Zero hits in the package.** Repo-wide, every hit is prose: `README.md:33` (topological sort
in a paragraph about decomposition), five `cc_tasks/*.md` SEQUENCING lines, and the copies of
those task files embedded in `seldon_events.jsonl` as `governed_sync` section text. No reader
exists in `seldon/`, in any file, listed or not.

The premise of decision 3 therefore holds, and it is stronger than DN-007's wording: DN-007
says SEQUENCING lines are "read into `precedes` edges inconsistently"; they are not read at
all. Every `precedes` edge in the ai-readiness-kg graph was written by a Desktop session
calling `seldon_task_chain` by hand.

---

## §1 — both repos' commits

### Seldon (`/Users/brock/GitHub/seldon`)

| commit | what |
|---|---|
| `33f70c6` | `feat:` decisions 1–4 and ADDENDUM_01 decision 6, on `feat/seldon-hygiene` |
| `7bcdfb2` | `Merge feat/seldon-hygiene` into `main` |
| `1e5e275` | `issue:` `issues/2026-09-18_cadence_render_on_request.md` marked resolved by decision 2 |

Pushed: `d509423..7bcdfb2` then `1e5e275`. Working tree clean.

Files: `seldon/core/staleness.py`, `seldon/commands/verify.py`, `seldon/commands/status.py`,
`seldon/commands/session.py`, `seldon/commands/go.py` (D1); `seldon/commands/cadence.py` (new),
`seldon/core/cadence.py`, `seldon/cli.py` (D2); `seldon/core/dispatch.py`,
`seldon/commands/cc.py`, `seldon/mcp_server.py` (D3, D4, D6);
`seldon/commands/dispatch.py` (D6); `docs/design/2026-09-15_standing_dispatcher.md`; four new
test modules and two amended ones.

**Decision 1.** `decided_not_drifted(artifact, resolve)` in `seldon/core/staleness.py`, with
`partition_stale`, `resolver_for_session` and a `StaleVerdict` that carries the reason an
undecided artifact stays undecided. `check_stale_artifacts`, `seldon status`,
`get_briefing_data` and `seldon go`'s renderer all read it, so the count means one thing in all
four. A `superseded_by` that resolves to nothing, to more than one artifact, or to a successor
that is itself undecided-stale is **not** a decision and stays in the warning set with the
reason on its line; chains are followed with a visited set and a cycle is undecided. Three
counts are reported and only the first warns. The Result state machine is unchanged, and
`test_the_result_state_machine_is_unchanged` asserts it.

**Decision 2.** `seldon cadence list | check | render`. The stdout render is byte-identical to
what `_create_instance` writes for the same entry and instant
(`test_render_to_stdout_is_what_the_pass_would_have_written`). A hand render writes
`cadence_rendered`, never `cadence_created`. A template declares extra placeholders on a
`<!-- seldon:vars target, network_hosts -->` line in its first ten; all three refusals name the
variable. See §5.6 and §5.7 for two things the decision did not specify.

**Decision 3.** `**After:**`, parsed in `seldon/core/dispatch.py` beside the other header
grammars and resolved in `seldon/commands/cc.py::register_task_file` — so the CLI, the MCP tool
and the cadence all take one path. Resolution happens **before** `create_artifact`, so a
refusal writes nothing. Edges go through `add_chain`, asserted statically by
`test_the_edges_go_through_the_shared_writer`.

**Decision 4.** `sequencing_lint` warns — never refuses — when a task has no `After` header and
its SEQUENCING line states an ordering or names another task file.

**Decision 6a.** `_commits_its_append` decorates the ten MCP write tools the addendum names;
`commit_journal_append` commits the store path-scoped, and defers on a held lease, a wrong
branch, an untracked store, or a project with no `dispatch:` block. `COMMITTABLE_ACTORS` is now
`("dispatcher", "desktop")`; a `cc` line still refuses.

**Decision 6b.** `dispatch_stuck`, `dispatch.stuck_after_passes` (default 3, validated at config
load), `.seldon/dispatch_stuck.json` for the streak, `advance_stuck` for the re-arm rule as a
pure function, and the refusal line now naming the dirty paths.

### ai-readiness-kg (this repo)

`CLAUDE.md` (decision 5: the paragraph, and the replaced sentence), `seldon.yaml`
(`stuck_after_passes: 3` with its comment), `scripts/check_protected_seldon_hygiene.sh` (new —
see §5.5), `seldon_events.jsonl`, this RESULT.

---

## §2 — `seldon verify` and `seldon go --brief`, before and after

"Before" was taken against Seldon at `main@d509423` in a throwaway git worktree
(`/tmp/seldon_before`, since removed), so the two runs differ in exactly the code this task
wrote. Logs: `logs/stale_before.log`, `logs/stale_after.log`.

| | `seldon verify` — Stale artifacts | exit | `seldon go --brief` |
|---|---|---|---|
| **before** | `⚠ 36 stale: scan_findings_2026-09-10_rj2, scan_l0_a10_pass_2026-09-10_rj2, scan_l0_a10_applicable_n_2026-09-10_rj2` | **1** (1 warning) | `**Stale Artifacts:** 41` |
| **after** | `✓ None stale; 5 withdrawn by decision (scan_l0_g1_d_pass_2026-09-10_rj2, …); 36 superseded by decision (scan_findings_2026-09-10_rj2, …)` | **0** (all checks passed) | `**Stale Artifacts:** 0` / `**Decided, not drifted:** 5 withdrawn, 36 superseded` |

**The expected after-state held exactly: stale 0, withdrawn by decision 5, superseded by
decision 36, `seldon verify` EXIT=0.** Nothing was edited to make the numbers match; the 41
artifacts are as they were and `build_projection.py` was not run.

All 36 resolved on the first attempt — every one names a `*_rj4` successor in state
`published`, and none fell into the dangling, ambiguous or cyclic cases.

The before row also records something §0.1 did not: **`verify` and `go` already disagreed**,
36 against 41, because the DD-066 withdrawal exemption lived in `check_stale_artifacts` alone.
That is the "four renderers, four filters" condition decision 1 names, observed live rather
than argued.

---

## §3 — `seldon cadence render` on `cc_tasks/templates/spot_scan.md`, and the delegation verdict

Log: `logs/spot_render.log`, `logs/delegation_check.log`.

**As the template stands, it refuses:**

```
$ python -m seldon cadence render --template cc_tasks/templates/spot_scan.md \
    --period bea --cycle-name spot_bea_2026-09-20 \
    --var target=BEA --var network_hosts=apps.bea.gov
Error: --var 'network_hosts', 'target' are not declared by this template; it declares nothing.
Declare it on a `<!-- seldon:vars ... -->` line in the template's first 10 lines, or drop the --var
```

That is the designed refusal, not a defect: the five fields are closed so a typo in a template
fails at render instead of shipping `{typo}` in a task body, and an open `--var` would reopen
the same hole from the caller's side.

**Verdict: `scripts/render_spot_scan.py` CAN delegate its substitution, byte-identically, and
two things stand between it and doing so.**

With one line added to a copy of the template —
`<!-- seldon:vars target, network_hosts -->` — and the values the script derives
(`target='BEA'`, `period='bea'`, `cycle_name='spot_bea_2026-09-20'`,
`instance_stem='2026-09-20_spot_scan_bea'`, `network_hosts='www.bea.gov, 127.0.0.1'`), the two
renders are **identical apart from one line**:

```
identical once created_at is normalised: True
diff lines: 5
--- render_spot_scan.py
+++ seldon cadence render
@@ -3 +3 @@
-**Date:** 2026-09-20T12:00:00Z
+**Date:** 2026-09-20T10:48:11.092369Z
```

The only delta is `{created_at}`: `render_spot_scan.py` formats it `%Y-%m-%dT%H:%M:%SZ`, while
the command uses microsecond ISO — which is what `_create_instance` has always written, so the
command matches the *dispatcher* byte for byte and the script is the one that differs.

The two blockers:

1. **The declaration line is a template edit, and `cc_tasks/templates/` is outside this task's
   write set.** The one-line diff is stated here so the next task is one edit and one call.
2. **The derivation does not move.** `target`, `period`, `cycle_name` and `network_hosts` come
   from `run.canonical_bodies`, `spot.slug`, `spot.spot_name` and the netlocs of the body's rows
   on `params.cycle.targets` — the frame, which Seldon cannot know. The task file said as much
   and it is right. What delegating removes is the script's own `_SPOT_FIELDS` regex and its
   direct call into `C.render`; what it keeps is every line that reads the frame.

`seldon cadence list` on this repo prints the honest thing for `dispatch.cadence: []`:

```
dispatch.cadence is empty: no schedule is configured.
A template can still be rendered on request: seldon cadence render --template <path> --period <P> --cycle-name <N>
```

---

## §4 — an `After` registration end to end, on a throwaway task in a scratch store

Scratch Neo4j database `afterdemo44869` and a temp project; both destroyed at the end (the
database drop is confirmed in the log below — `tests/testdb.py::drop_database` refused the
non-`seldon-test-p*` name, so it was dropped explicitly and `SHOW DATABASES` confirms no
`afterdemo*` remains). Log: `logs/after_demo.log`.

```
[1] predecessor registered: 5c4055d3  cc_tasks/2026-09-18_predecessor.md

[2] **After:** 2026-09-18_predecessor  (a stem ref)                      exit=0
    Registered: successor
      id: 5a80de77...
      state: proposed
      after: 5c4055d3 (1 precedes edge(s) written)
    precedes edges: [('5c4055d3', '5a80de77')]

[3] **After:** 5c4055d3  (an id prefix), on a second successor           exit=0
    precedes edges: [('5c4055d3', '5a80de77'), ('5c4055d3', '351f6797')]

[4] **After:** 2026-09-18_never_existed  (unresolvable)                  exit=1
    ERROR: after_unresolved: After ref '2026-09-18_never_existed' names no registered
    ResearchTask. Grammar: `**After:** none`, or `**After:** <ref>[, <ref> ...]` where each ref
    is a cc_tasks file stem (with or without `.md`) or an artifact id prefix of 8 or more hex
    characters. Nothing was written.
      Fix: name a registered task, or drop the **After:** header.
    tasks in graph: 3 (unchanged); precedes edges: 2 (unchanged)

[5] re-registering [2] is idempotent                                     exit=0
    precedes edges: 2 (unchanged)

[6] no **After:**, SEQUENCING states an ordering                         exit=0
    Warning: this task's SEQUENCING line states an ordering nothing reads. It names
    2026-09-18_predecessor. A dispatcher reads `precedes` edges only; SEQUENCING is prose.
    Declare it in an `**After:**` header (…) and `cc register` writes the edge.
    tasks in graph: 4 — the lint did not refuse
```

The MCP path is the same function and is covered by
`tests/test_after_header.py::test_the_mcp_tool_takes_the_same_path` and
`::test_the_mcp_tool_refuses_an_unresolvable_ref`.

---

## §4a — ADDENDUM_01 step 0: what actually made the tree dirty

`git log --stat a705522^..HEAD -- seldon_events.jsonl cc_tasks/`, with the commit instants in
UTC:

```
fee6956  2026-09-20T10:18:29Z  record: artifact_state_changed, artifact_updated,
                               dispatch_launched 65e5da0e — 4 line(s) by the standing dispatcher
                                 seldon_events.jsonl | 4 ++++
4d455da  2026-09-20T10:16:33Z  docs: DN-007 — operator rulings 2026-09-16..09-19 and project state
0568b6d  2026-09-20T10:13:44Z  desktop: 93d28c6e, precedes 65e5da0e->dcf47bc6, ADDENDUM_01
                                 ...cadence_after_ADDENDUM_01.md | 28 ++++++++++
6c6295b  2026-09-20T09:58:17Z  register: record of cc_tasks/2026-09-19_g4_locators_and_progress
                               _drift.md (dcf47bc6) — registration line by the standing dispatcher
                                 seldon_events.jsonl | 2 ++
6f94d0f  2026-09-20T09:56:25Z  register: cc_tasks/2026-09-19_g4_locators_and_progress_drift.md
                               — task dcf47bc6 committed by its registration
                                 .../2026-09-19_g4_locators_and_progress_drift.md | 47 ++++++
a705522  2026-09-20T03:00:41Z  register: record of cc_tasks/2026-09-19_seldon_hygiene_superseded
                               _cadence_after.md (65e5da0e) — registration line
                                 seldon_events.jsonl | 2 ++
```

And the c7 code, from the pass that made the first refusal (`logs/airkg_dispatch.log`, lines
2963–2968):

```
=== 2026-09-20T03:00:39Z | airkg-dispatch fire
record: seldon_events.jsonl NOT committed: not dispatcher-only (also written by desktop)
register: record of cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after.md (65e5da0e)
          committed as a705522
nothing eligible (26 open, 1 candidate(s))
  65e5da0e dirty_tree: c7  cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after.md
push: pushed 2 commit(s)
```

**The dirt was NOT the desktop event lines.** The two lines the addendum names — `93d28c6e`
(`seldon_task_create`, 02:59:48Z) and `65e5da0e`'s registration (03:00:10Z) — are exactly the
two insertions in `a705522`, committed at **03:00:41Z**, in the same pass that refused. They
were swept because `_commit_registration_records` commits the store with a **pathspec on the
file**, not a filter on the lines; only `_record_own_lines`, which runs first and does filter by
actor, refused them. The same happened to the `seldon_task_chain` line (`link_created`,
09:56:28Z), committed by `6c6295b` at 09:58:17Z.

So from 03:00:41Z the store was clean, and the dirt across all ~84 refusing passes was **one
untracked file**: `cc_tasks/2026-09-19_g4_locators_and_progress_drift.md`, the second task file
of the same Desktop authoring turn, written and left unregistered until it was registered at
09:56:25Z — at which point registration committed it (`6f94d0f`) and the queue moved.

**Decision 6 is re-scoped, and neither half is cancelled:**

* **6b is the decision that covers the actual cause.** An unregistered task file writes no
  event, so no commit mechanism could ever have swept it; the only instrument that reaches it
  is an alarm on the refusal itself. Implemented as specified.
* **6a closes a real, neighbouring gap, not this one.** A desktop append is committed today
  only by accident — when a registration record happens to be pending in the same pass. A
  `seldon_task_update`, `seldon_task_close` or `seldon_issue_create` on its own leaves a line
  that `_record_own_lines` refuses by name and nothing else touches, and that line is c7 false
  for the whole queue for as long as it sits there. Implemented as specified, and the sweep
  rule is widened from `dispatcher-only` to `dispatcher or desktop, no cc` so a deferred line
  is picked up by the next pass rather than refused again.

Pass log of a scratch checkout showing both, from
`tests/test_dispatch_stuck_and_journal.py` (14 tests, all passing):

* **6a's commit** — `test_an_mcp_write_tool_commits_its_own_append`: after
  `seldon_task_create`, `git status --porcelain` is empty and `git log -1` reads
  `desktop: artifact_created <id> — 1 line(s) written by the seldon_task_create MCP tool`.
  `test_an_mcp_write_tool_defers_while_a_lease_is_held` asserts the deferral.
  `test_a_pass_commits_an_uncommitted_desktop_line_and_dispatches` asserts the other half: a
  store left dirty by a desktop line is committed by the next pass and the task **launches in
  that same pass**. `test_an_uncommitted_cc_line_still_refuses` asserts the DD-019 guard is
  intact, with the message now reading `written by cc, which is not one of dispatcher, desktop`.
* **6b's single notification** — `test_three_identical_refusals_produce_one_event_and_one
  _notification`: three passes over one untracked `stray.md` produce exactly one
  `dispatch_stuck` (`criterion: dirty_tree`, `passes: 3`, `dirty_paths: ["stray.md"]`) and one
  notifier line, `stuck dirty_tree 3 stray.md`. A fourth pass produces neither.
  `test_a_cleared_then_recurring_refusal_alarms_again` clears the condition and recreates it
  and gets a second of each. `test_the_refusal_line_names_the_dirty_paths` asserts the log line
  now reads `dirty: stray.md` rather than pointing at the task file, which is the line that was
  wrong 84 times.

---

## §5 — every premise this task file got wrong

**5.1 — §0.1's account of the two counts (imprecise, and the correction strengthens the
decision).** It says the 36 superseded artifacts "are what makes `seldon verify` warn … and
what `seldon go` prints as 'Stale Artifacts: 41'". Measured: `verify` warned at **36** and `go`
printed **41**, because the DD-066 withdrawal exemption lived in `check_stale_artifacts` and
nowhere else. One number, two surfaces, five apart — which is decision 1's own argument, and
the task file did not notice its evidence was already on the machine (§2).

**5.2 — decision 3's "cycle (nothing written)" test is not reachable at registration.** A
brand-new task has no incoming edges, so `precedes: pred → new` cannot close a cycle whatever
`pred` is. The reachable self-loop — a task naming its own stem — refuses earlier and
differently, as `after_unresolved`, because the file is not yet registered and so resolves to
nothing (`test_a_self_reference_is_unresolvable_and_writes_nothing`). The cycle guard is
inherited rather than re-implemented: the writer is `add_chain`, asserted statically by
`test_the_edges_go_through_the_shared_writer`, and its refusal is covered by
`tests/test_precedence.py`.

**5.3 — ADDENDUM_01's step-0 premise is wrong in the specific.** Its cause (1) — desktop event
lines the registration commit "is scoped not to include" — is not what kept the tree dirty:
those lines were committed at 03:00:41Z by the registration-record sweep, which is pathspec-
scoped to the file and does not filter by actor. Its cause (2), the unregistered task file, was
the whole of it, for all ~84 passes. Full evidence and the re-scoping in §4a. The addendum
anticipated this and said what to do; both halves of decision 6 are implemented as written.

**5.4 — the wrong-premise count is not zero on the Seldon side either.** DN-007's "read into
`precedes` edges inconsistently" is the premise §0.3 was written to test, and §0 shows it was
generous: nothing read them at all.

**5.5 — the write set omits the instrument §3 requires.** The task says "Here: `CLAUDE.md` …
`seldon_events.jsonl` … the RESULT. Nothing else", and the addendum adds `seldon.yaml`. But §3
requires a protected-paths diff and this repo has no generic one — every prior task ships its
own `scripts/check_protected_<slug>.sh`. `scripts/check_protected_seldon_hygiene.sh` is
therefore a fifth path, entailed by §3 and declared here rather than smuggled; it is in the
check's own allow-list and named in §6.

**5.6 — decision 2 does not say where the five fields come from for `--template <path>`.**
There is no entry, so no `rule` (hence no period) and no `cycle_name_format` (hence no cycle
name). `--period` and `--cycle-name` are therefore **required** with `--template` and refuse
rather than default: a dated measurement may not carry a date nobody chose. A third option,
`--out-dir`, was added so `cc_tasks` is not compiled into the source (`~/GitHub/CLAUDE.md` §2);
it defaults to the entry's `instances_dir`, else `cc_tasks`.

**5.7 — decision 2's two sentences about a second run only reconcile one way.** "`--write`
refuses to overwrite" and "`--register` … a second run warns instead of duplicating" are
compatible only if `--register` on an existing instance does not re-render. Implemented that
way: `--register` on an existing path renders nothing, writes **no** second `cadence_rendered`,
and registers the file that is there — which warns, creates no duplicate, and leaves the graph
unchanged (`test_register_creates_one_task_and_a_second_run_warns`).

**5.8 — decision 2 said the delegation verdict, not that the template blocks it.** The verdict
is yes-with-one-line; the line is a `cc_tasks/templates/` edit and therefore out of scope here
(§3).

**5.9 — two existing Seldon tests state claims decision 6b deliberately changes, and were
amended rather than deleted.**
`test_dispatch_launch.py::test_ten_passes_over_a_dirty_tree_leave_the_log_byte_identical` is now
`…write_one_line_and_then_nothing`: it asserts byte-identity for the passes *below* the
threshold, exactly one `dispatch_stuck` at it, and byte-identity for ten passes after. DN-006
decision 7 forbids a poll logging its own silence; a record that the queue has stopped is the
opposite fact, and the amendment is stated in the test's docstring with the incident behind it.
`test_dispatch_own_record.py::test_a_line_somebody_else_wrote_is_never_committed_by_the_dispatcher`
matched the literal string `not dispatcher-only`, which decision 6a changes; its claim is
unchanged and the assertion now reads `written by cc` / `not one of dispatcher, desktop`.

**5.10 — nothing in §2's "if the numbers differ" branch fired.** The expected after-state held
exactly. No artifact was edited.

---

## §6 — the gate

Every command was detached, logged and polled to its `EXIT=` line inside this turn.

| gate | result | wall clock | log |
|---|---|---|---|
| Seldon full suite, `python3 -m pytest tests/ -q -rs` | **2059 passed, 0 skipped, 0 xfailed, 0 deselected** — EXIT=0 | 227.79 s (`real 3m49.056s`) | `/Users/brock/GitHub/seldon/logs/seldon_suite2.log` |
| `make gate-fast` (this repo) | **2707 passed, 3 skipped, 27 deselected, 12 xfailed** — EXIT=0 | 649.17 s (`real 10m54.140s`) | `logs/gate_fast.log` |
| `seldon verify` (this repo) | **All checks passed** — EXIT=0 | — | `logs/verify_gate.log` |
| `sh scripts/check_protected_seldon_hygiene.sh` | **PASS** — EXIT=0, 15/15 point-of-the-task assertions ok | — | `logs/protected.log` |
| the same check, re-run after `seldon cc complete` and before the commit | **PASS** — EXIT=0 | — | `logs/protected_final.log` |

**The Neo4j tier ran and was not excused.** `SELDON_TESTS_ALLOW_NEO4J_SKIP` was never set; the
Seldon suite reports zero skips, which under `tests/conftest.py`'s fail-not-skip gate is the
positive evidence that the tier executed.

The three skips in `gate-fast` are named in the log and none is this task's:

```
SKIPPED [1] tests/test_dispatch_config.py:333: interactive_only: SELDON_SESSION_ID is set, so
  this is a dispatched session, which holds its own task's claim and dirties the tree for its
  whole life; the quiet checkout this test asserts cannot exist inside one.
SKIPPED [1] tests/test_scan_harness.py:283: E5 judges the cycle's controls, not a surface
SKIPPED [1] assessment/tests/test_g1_preservation.py:337: no dev proposition publishes SE and
  CI together
```

`gate-task` was not run and is not this task's gate: no rule module, no rule registry and no
part of the re-derivation engine was touched — `assessment/` is asserted byte-identical by the
protected-paths check. `gate-full` is the pre-push run and is what `make gate-fast` plus the
Seldon suite above stand in for here; `logs/` is gitignored, so these logs are local and what
ships is this RESULT quoting them.

`seldon cc complete` walked `65e5da0e` `in_progress -> completed` (`logs/cc_complete.log`, EXIT=0) before the check's second run, so the check saw the final tree.

Earlier runs kept for the record: `logs/stale_before.log`, `logs/stale_after.log` (§2);
`logs/spot_render.log`, `logs/delegation_check.log` (§3); `logs/after_demo.log` (§4). The first
full Seldon run, `logs/seldon_suite.log`, is the one that surfaced §5.9's two tests
(`2 failed, 2057 passed`); it is quoted here rather than discarded because a green second run
that hides a red first is the defect this RESULT section exists to prevent.

---

## §7 — what the next OODA should verify first

1. **The alarm has never fired on the live queue.** `_stuck` returns early while a claim is in
   flight, and this session held one for its whole life, so no `dispatch_stuck` exists yet in
   `seldon_events.jsonl`. The first real test is the next time the queue wedges. Check
   `dispatch.stuck_after_passes: 3` against measured behaviour once there is any — it is
   declared with **no measured basis**, like `poll_interval_s`.
2. **`cc_tasks/templates/spot_scan.md` is one line from delegating** (§3). That line, and the
   corresponding simplification of `scripts/render_spot_scan.py`, is the obvious next task.
3. **No existing task file carries an `**After:**` header.** The header is optional and nothing
   queued changed behaviour; the SEQUENCING lint will now warn on the next registration of a
   task whose SEQUENCING states an ordering, which is the prompt to add one.
4. **The 41 stale artifacts are unchanged on the graph.** What changed is what four commands
   say about them. If a later task needs the raw count, `get_stale_artifacts` still returns all
   41 and `partition_stale` is what narrows it.
