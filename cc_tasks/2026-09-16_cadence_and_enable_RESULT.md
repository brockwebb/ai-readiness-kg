# RESULT — cadence: cycle 5 is created by a schedule, and the dispatcher is on

**Task:** `cc_tasks/2026-09-16_cadence_and_enable.md`, implementing DN-006 decision 8, decision
10, DD-060 and DN-005 §4 item 1 second half.
**Addenda:** none exist. Globbed at dispatch and again before §5
(`logs/cadence_due_instants.log`), both times empty. The base task was executed as written.
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M.
**Date:** 2026-09-16 UTC.
**Spend: zero model calls.** **Network: none** — no host was contacted, no `ANTHROPIC_API_KEY`
was ever set, the `claude` in every test is a shell script, and the one `claude -p` the
dispatcher can issue was never reached because nothing was ever eligible. The only remote
operations are the three `git push`es.

## THE GATE: PASS

| clause (§5) | result | log |
|---|---|---|
| Seldon suite green on the merged commit | **PASS — 1,878 passed, 137.16 s** on `61cad01` | `seldon/logs/cadence_seldon_suite_final3.log` |
| `make gate-fast` here, detached and polled | **PASS — 2,214 passed, 17 skipped, 25 deselected, 12 xfailed, 409.90 s (6:49)** | `logs/cadence_gate_fast.log` |
| no payload is touched, so `gate-task` is not owed | **correct** — no rule module, no engine, no stored payload; `assessment/`, `state/`, `events/`, `corpus/`, `kg/` all unchanged, asserted by the protected-paths diff | `logs/cadence_protected.log` |
| the full suite, before pushing (`CLAUDE.md` suite tiers) | **PASS — 2,239 passed, 17 skipped, 12 xfailed, 1,327.75 s (22:07)** | `logs/cadence_gate_full.log` |
| `seldon verify` | **PASS — all checks passed** | `logs/cadence_verify.log` |
| protected paths | **PASS** | `logs/cadence_protected.log` |
| §3's observed scheduled pass, with the byte comparison | **PASS — launchd-fired 2026-09-16T03:41:16Z, `rc=0`, event log byte-identical** | `logs/cadence_scheduled_pass.log` |
| `launchctl list` shows the job | **PASS** — `-	0	com.brock.airkg-dispatch` | `logs/cadence_install.log` |

Every log carries its own `EXIT=`, and all of them were written before this file was.

**A green fast tier is not reported as a green suite** (`CLAUDE.md`): both wall-clocks are
above, 6:49 for the fast tier and 22:07 for the whole one.

## 1. Both repos' commits

| repo | commit | what |
|---|---|---|
| `seldon` | `4c34861` | `feat: dispatch.cadence — a schedule that produces a task` (on `feat/dispatch-cadence`) |
| `seldon` | **`04dc1ac`** | `Merge feat/dispatch-cadence` → `main`, pushed |
| `seldon` | **`72d5aa1`** | `fix: a pass with nothing eligible writes no event, as decision 7 says` → `main`, pushed. §5 (a) |
| `seldon` | **`61cad01`** | `fix: a released lease reports free, not a dead holder` → `main`, pushed. §5 (c) |
| `ai-readiness-kg` | see §7 | the template, the cadence config, the enable, the plist install, the wrapper's credentials, the test, the addendum and this RESULT |

`pip install -e .` re-run here after the merge; `seldon.core.cadence` and
`seldon.commands.dispatch` both resolve to `/Users/brock/GitHub/seldon/…`. Nothing is left on a
branch.

## 2. The template, as shipped

`cc_tasks/templates/scan_cycle.md`, 149 lines, and it is a **real task file** rather than a stub
somebody has to finish: the three dispatch headers, the design-note citations, the immutability
line, the addendum glob, a numbered §1–§5, a hard-stop gate and a named RESULT path.

Its body is cycle 4's shape (`cc_tasks/2026-09-10_scan_run_4.md` and its RESULT are the source):
pre-flight `refuse_clobber` and the control gate as a hard stop; one pass over the bound target
list, detached and polled; the gate — byte-identical re-derivation, Tier C legs in the set, no
duplicate Finding identities, **no verdict resting on an unobserved probe** (the clause that
stopped cycle 4), the manners replay with the per-site request count, hygiene and append-only,
`make gate-task`, `seldon verify`, protected paths; publish to the log under DN-003 as
generation 1; the three matrices; the L0 Results registered in `proposed` through
`scripts/cycle_results.py`; the page and figures.

**Six decisions stand for every instance**, and the one the task asked for is decision 4, in the
template's own words so a reader of cycle 5's task file does not have to go to DN-004 to find
out what it will not do:

> **This task does not move the published report's snapshot, the site's published Results, or
> the abstract.** A new measured cycle is on the log and in the matrices the moment it lands;
> promoting it to the published snapshot is a DN-004 decision […] until DN-005 §4 items 2 and 3
> exist.

It runs the instrument as `params.yaml` binds it on the day — the five host-level legs after
DD-066 (`A4`, `A5`, `A10`, `A11-declared`, `A12`), with `G1-D` withdrawn from `home`/
`well_known` by `params.tier0.legs_withdrawn` — and **changes no rule**: if the gate shows the
instrument is wrong, the instance writes nothing and reports, and the fix is the next task's.

`tests/test_cadence_template.py` (16) asserts the shipped file against the shipped config: it
renders with no placeholder left, the rendered instance is a **candidate on all three headers**,
`D.evaluate` — the same function `seldon dispatch status` prints — reports it **eligible with
`ok c5` by its cadence declaration**, c4 reads zero spend under the band, the five leg names in
the template are the five `params.tier0.legs` binds today, and the RESULT path it names is the
one the dispatcher's finish check looks for.

## 3. The observed scheduled pass, and the byte comparison

Fired by launchd, not by hand — the log line is the wrapper's own, written 2 m 48 s after the
previous fire at the 300 s interval:

```
=== 2026-09-16T03:41:16Z | airkg-dispatch fire
nothing eligible (26 open, 2 candidate(s))
  c55e40b7 dirty_tree: c1,c2,c7  cc_tasks/2026-09-16_publication_guards.md
  fe16dfb1 dirty_tree: c1,c7  cc_tasks/2026-09-16_cadence_and_enable.md
=== rc=0

=== launchctl list ===
-	0	com.brock.airkg-dispatch

=== event log, before and after ===
8b54bdd2b02550a934c280a1fe7b1ebc07d721a8acdb574d8a0662a142ddfbc8  seldon_events.jsonl
8b54bdd2b02550a934c280a1fe7b1ebc07d721a8acdb574d8a0662a142ddfbc8  seldon_events.jsonl
```

**Byte-identical: yes.** Nothing was eligible because the working tree was dirty with this
task's own edits — which is c7 doing exactly what it is for, and what decision 10 states as a
rule. The plist is a **symlink**, not a copy:

```
lrwxr-xr-x  1 brock  staff  79 ... /Users/brock/Library/LaunchAgents/com.brock.airkg-dispatch.plist
  -> /Users/brock/GitHub/ai-readiness-kg/scripts/jobs/com.brock.airkg-dispatch.plist
```

Loaded with `launchctl bootstrap gui/502` (macOS 26.5.2), exit 0.

## 4. The next three due instants, as the implementation computes them

```
now                : 2026-09-16T03:41:33Z
current period     : 2026-09
start_period       : 2026-10
due now            : False (before_start: True)
instance on disk   : None
next due #1        : 2026-10-05T00:00:00Z = Monday 05 October 2026
next due #2        : 2026-11-02T00:00:00Z = Monday 02 November 2026
next due #3        : 2026-12-07T00:00:00Z = Monday 07 December 2026
```

Checked against a calendar once, here, and against a hand-written table of first Mondays in
`seldon/tests/test_cadence.py` — including 2027-02-01 and 2027-03-01, the months that begin on a
Monday, where an implementation that always added a week would put the cycle on the 8th.

**Cycle 5 is `scan_2026-10-05`, period `2026-10`, due 2026-10-05T00:00Z.** Its instance will be
`cc_tasks/2026-10-05_scan_cycle_2026-10.md` and its RESULT
`cc_tasks/2026-10-05_scan_cycle_2026-10_RESULT.md`.

## 5. Every premise the task file got wrong

**(a) Decision 6's "nothing is created by this task, because nothing is due" was false when it
was written, and it is the most consequential thing this task found.**

September 2026's first Monday was the **7th**. The job was installed on the **16th**. The
current period was due, and the instance glob found no cadence instance on disk — correctly,
because September's cycle was **cycle 4, hand-dispatched on 2026-09-10 as `scan_2026-09-10`**,
which is not a cadence instance and never will be. The first pass to find a clean tree would
have created and launched **a second September cycle**: two measurements of one month, which for
a dated measurement is the least affordable error available.

`catchup=False` does not cover it — back-fill protection is about *earlier* periods, and the
offending one is the *current* one. The fix is `start_period`, the first period a schedule may
serve, required rather than defaulted; **prior art is Airflow's `start_date`**, which exists for
this exact condition. `start_period: "2026-10"` is what makes decision 6's sentence true, and
now for a reason the code enforces rather than a reason the author believed. DN-006
ADDENDUM_02 §3.

**(b) Decision 8 requires the dispatcher to COMMIT, and neither the note nor the task says so.**
Decision 2's c1 wants a git-tracked task file and c7 wants a clean tree. A rendered,
uncommitted instance fails both — permanently, and *for every other task in the queue*, because
c7 is a fact about the checkout. The cadence would have created January's cycle and then wedged
the dispatcher until a person came and committed it, which is the exact latency the mechanism
exists to remove. The commit is pathspec-limited, gated on a clean tree it owns, and pushes
nothing. ADDENDUM_02 §1.

**(c) Decision 1's five entry keys and four template placeholders are seven and five.**
`cycle_name_format` keeps the string `scan_` out of a shared library (`~/GitHub/CLAUDE.md` §2);
`start_period` is (a). `{instance_stem}` is the fifth placeholder and it is load-bearing: the
finish check reads `cc_tasks/<stem>_RESULT.md`, so a template naming its RESULT
`{cadence_name}_{period}` — which reads naturally — would produce a cycle that ran, wrote its
RESULT, and was marked **`blocked` on a filename**, every month, silently. ADDENDUM_02 §2.

**(d) "The RESULT quotes the pass log and the byte-identical event log" was not reachable as
shipped.** `_pass` emitted one `dispatch_refused` per blocked candidate, **directly beneath a
comment quoting decision 7's "a pass in which nothing is eligible writes no event"**. The branch
had never executed — the dispatcher shipped disabled, so the prior task's dry pass returned at
`dispatch is disabled`. Every reason reachable there is a *standing condition*, re-evaluated
every five minutes; and because `seldon_events.jsonl` is tracked, writing to it keeps the tree
dirty, which keeps `dirty_tree` true, which writes again. Two candidates × 12 passes an hour,
for as long as a session works. Fixed in `72d5aa1`; the reasons are now named on stdout, where
the wrapper's log carries them, and `status` still computes every one on demand.

**(e) §3 assumed a scheduled pass would work. It did not.** The first one fired on time
(03:36:15Z) and died on `neo4j.exceptions.AuthError`: **a launchd job inherits almost no
environment**, so the NEO4J_* variables a hand-run `seldon dispatch` picks up from the shell are
simply absent. The wrapper now falls back to `~/.wintermute/.env` — this repo's own convention
(`CLAUDE.md`; the parse is copied from `scripts/build_projection.py::_neo4j_creds`) — and
**refuses with exit 3** when no credential is found, rather than running a pass that cannot read
the queue. The first attempt at that fix was *also* wrong and silently so: `tr -d` deletes every
quote character in a value rather than the surrounding pair, and this password contains one, so
the pass authenticated with a password one character short — `AuthError` again,
indistinguishable from a wrong password and from no password at all. Both halves are tested.

**(f) A released lease looked like a dead holder.** The first `seldon go` after enabling
reported `**Lease:** dispatcher:HexagonMBP.local:66065 (holder GONE — seldon dispatch lease
reap)`. The guard was working; the *record* was stale — `Lease.__exit__` dropped the flock and
left the body naming the finished pass's holder. That is a false alarm after every ordinary
pass, twelve times an hour, and an operator trained to reap on sight will eventually reap a live
one. Fixed in `61cad01`: exit records the release and keeps the file (the flock needs a stable
inode), `reap` distinguishes `not_held` from `no_lease_file`, and a genuinely killed holder
still reaps. It now reads `**Lease:** free (last released 2026-09-16T04:01:23Z)`.

**(g) One premise that held exactly, and it is the one that mattered.** Decision 8's load-bearing
clause — *"lets it flow through decisions 2 to 5 like any other task"* — needed no amendment.
`c5`'s second limb ("or the task was created by the cadence rule") was written into the matcher
when the dispatcher shipped, before anything could produce such a task, and the first rendered
instance passes it with **no change to the criterion**. A cadence instance is evaluated by the
same nine criteria, claimed by the same compare-and-set and finished by the same check as a
hand-written task.

**(h) The shape behind (d), (e) and (f) is worth naming.** All three were unreachable while
`dispatch.enabled` was `false`. A mechanism that ships disabled has no observations behind it,
only reasoning — and four defects across this build and the one before it (the truncated first
dirty path, the refusal-per-pass, the launchd environment, the stale lease) were each found by
running the thing once and reading the output, none by review. A dry pass could not have reached
three of them, because a dry pass runs in a shell.

## 6. What `seldon go` now says (decision 5)

```
## Dispatcher

**Enabled:** True
**Lease:** free (last released 2026-09-16T04:01:23.791829Z)
**Last dispatch per task:** *(the dispatcher has launched nothing)*

**Cadence `scan_cycle`:** period 2026-09, due 2026-09-07T00:00:00Z → not due (before start_period 2026-10)
  Next: 2026-10-05T00:00:00Z, 2026-11-02T00:00:00Z, 2026-12-07T00:00:00Z
```

Plus, when there is anything to say: the STOP file, the last `dispatch_finished` per task with
exit code and RESULT-present, and **every task the dispatcher moved to `blocked` with its log
path**. That is **operator touchpoint 4** — incident notification, informational, never an
approval step. A blocked launch is seen the next time a Desktop thread opens, with the log
beside it, and nothing else notifies anyone.

It is read from the **event log and disk, never the graph**: `seldon go` degrades gracefully
when Neo4j is down, and a brief that lost the dispatcher's state exactly when the machine was
unhealthy would be missing at the only moment it was wanted.

## 7. What was built

**Seldon** (`04dc1ac`, `72d5aa1`, `61cad01`):

* `seldon/core/cadence.py` — the closed rule vocabulary refusing at config load, the calendar,
  `start_period`, the instance-file guard, the brace-safe render (not `str.format`: a task file
  is markdown full of JSON, Cypher and shell), and the comment-preserving `last_instance`
  write-back.
* `seldon/core/dispatch.py` — `cadence` validated in `load_dispatch_config`; `stage` and
  `commit_paths`, pathspec-limited, skipping an ignored path rather than failing on it; the
  lease's recorded release.
* `seldon/commands/dispatch.py` — the cadence pass *before* candidacy, gated on a clean tree,
  the configured branch and no claim in flight; `cadence_created`; a failed registration removes
  the file it rendered; `_utcnow` as one clock seam; `status` reporting the cadence rows.
* `seldon/commands/cc.py` — `register_task_file` factored out of `cc register`, so the cadence
  registers through the *same lines*, every gate included.
* `seldon/commands/go.py` — the Dispatcher section.
* `seldon/core/sync.py` — the four `dispatch_*` types and `cadence_created` registered as
  audit-only. They shipped unlisted, so every replay warned five times per dispatch, which is
  precisely what that set exists to prevent.
* `docs/design/2026-09-16_cadence.md` — the Seldon-side record.
* `tests/test_cadence.py` (63), `tests/test_cadence_pass.py` (12, Neo4j), plus 7 in
  `test_go.py` and 4 in `test_dispatch.py`.

**This repo:**

* `cc_tasks/templates/scan_cycle.md` — §2 above.
* `seldon.yaml` — `dispatch.enabled: true`, and the `cadence:` block with every key carrying the
  reason for its value.
* `scripts/jobs/com.brock.airkg-dispatch.plist` — the install comment corrected to the symlink,
  with the reason (a copy is a third file holding one interval, and the wrapper's drift check
  can only see two of them).
* `scripts/jobs/airkg_dispatch.sh` — the Neo4j credential fallback and its loud refusal.
* `tests/test_cadence_template.py` (16) and 3 new tests in `tests/test_dispatch_config.py`
  (26 there in total),
  whose `enabled is False` assertion is **inverted rather than deleted**: a dispatcher silently
  switched off is the same defect as one silently switched on, and the test is where a reader
  finds out which is true today.
* `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_02.md` — five corrections, two
  defects found by enabling, one confirmation.
* `scripts/check_protected_cadence_and_enable.sh`.

## 8. Logs

```
logs/cadence_install.log            symlink + launchctl bootstrap + list      EXIT=0
logs/cadence_scheduled_pass.log     the launchd-fired pass + byte comparison  rc=0  IDENTICAL
logs/airkg_dispatch.log             the wrapper's own log (gitignored)        rc=0
logs/cadence_due_instants.log       §4, and the second addendum glob          EXIT=0
logs/cadence_go_section.log         the `seldon go` Dispatcher section        EXIT=0
logs/cadence_gate_fast.log          make gate-fast, detached, polled          EXIT=0  2,214 / 409.90 s
logs/cadence_gate_full.log          the whole suite, before the push          EXIT=0  2,239 / 1,327.75 s
logs/cadence_verify.log             seldon verify — all checks passed         EXIT=0
logs/cadence_protected.log          protected paths                           EXIT=0  PASS
seldon/logs/cadence_seldon_suite_final3.log   the Seldon suite on 61cad01     EXIT=0  1,878 / 137.16 s
```

## 9. Open, for the next OODA

1. **The dispatcher's first self-launch is `cc_tasks/2026-09-16_publication_guards.md`**, on the
   first pass after this task's commit leaves the tree clean and `seldon cc complete` satisfies
   c2. It is `ineligible on c1,c2,c7` as this is written; c1 and c7 close with the commit, c2
   with the completion. **Nothing in this task launched it**, per decision 4.
2. **`poll_interval_s: 300` still has no measured basis.** DN-006 §5 makes dispatch latency
   measurable after a week of `dispatch_launched` events. There are still zero.
3. **Cycle 5 will be the first task a machine both wrote and ran**, on 2026-10-05. The template
   says its instance must report *"every premise this template got wrong"* — a template rendered
   unattended every month is exactly the artifact whose stale premises nobody notices, and that
   sentence is its only maintenance channel. The first instance's RESULT is the one to read
   closely.
4. **The cadence has one entry and one project.** `seldon dispatch` is written to be adopted by
   any project with a `dispatch:` block and the cadence by any with a template; the first real
   second one will be the first test of whether the doc's "adopting it in another project" is as
   short as it claims.
5. **Twenty-two open tasks still carry no `source_file`** and can never be dispatched. Unchanged
   by this task, and still nobody has asked whether all twenty-two deserve a task file.
