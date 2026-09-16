# ADDENDUM 02 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-16. **Status:** AMENDS decision 8. Does not supersede it. Written by the
implementing task (`cc_tasks/2026-09-16_cadence_and_enable.md`), whose §6 requires that any
decision the build showed to be incomplete be corrected here rather than silently deviated
from. Five corrections, two defects found by enabling, and one confirmation; decisions 1 to 7, 9 and 10 stand as ADDENDUM_01
left them, and the substance of decision 8 — *a schedule produces a task; it does not bypass
the queue* — is implemented exactly as written.

---

## 1. Decision 8 requires the dispatcher to COMMIT, and does not say so

Decision 8: "the pass renders the template, registers it, and lets it flow through decisions 2
to 5 like any other task."

Decision 2's **c1 requires the task file to be git-tracked**; **c7 requires a clean working
tree**. A rendered, uncommitted file fails both. It fails them *permanently* and it fails them
*for every other task in the queue*, because c7 is a fact about the checkout and not about the
task being evaluated: the cadence would create January's cycle and then wedge the dispatcher
until a person came and committed the file — which is the exact latency the whole mechanism
exists to remove, reintroduced by the one part of it that was supposed to end the need for a
person.

So **the cadence commits what it created**, and the commit is *entailed by* decision 8 rather
than added to it. Three properties keep that safe, and they are not optional:

* **Pathspec-limited.** `git add -- <paths>` and `git commit -- <paths>`, never `-A`. The
  commit contains the instance file, the event-store line and the one-line `last_instance`
  edit. A tree dirty for some other reason keeps its other changes.
* **It refuses a checkout it does not own.** Creation is gated on a clean tree, the configured
  branch and no claim in flight — the same shape as c6 and c7, for the same reason. Writing a
  file and a commit into a checkout something else is editing is DD-019's batch-identity class
  in the one place this design can still reach it.
* **Nothing is pushed.** A push is outward-facing. The dispatched session pushes its own work
  at the end of its task, as `CLAUDE.md` §10 already requires.

The sequence inside a creation is ordered and the order is load-bearing: **stage before
register** (`register_task_file` refuses a file git cannot recover, and the index is what makes
it recoverable), **event before commit** (so the commit carries its own record on the log), and
**remove on any failure** (a rendered file that is not in the graph is both a task nothing will
run and a file the next pass reads as "this period is already served").

## 2. A cadence entry needs fields decision 8 does not name, and the template a fifth placeholder

Decision 8 describes an entry as "a calendar rule, a template under `cc_tasks/templates/`, and
the name of the last instance created". The implementing task's decision 1 lists five keys
(`name`, `rule`, `template`, `instances_dir`, `last_instance`). **Seven are needed** —
`cycle_name_format` here, and `start_period` in §3.

**`cycle_name_format`** is the sixth. Rendering `{cycle_name}` means producing
`scan_2026-10-05`, and the string `scan_` is this project's naming convention — the one every
payload path, Result suffix and `refuse_clobber` key follows — not Seldon's. Compiling it into
`seldon/core/cadence.py` would put a project's convention in a shared library and would violate
`~/GitHub/CLAUDE.md` §2 in the same breath. It is a config key with its reason beside it.

**`{instance_stem}`** is a fifth template placeholder beyond the four the task names
(`{cycle_name}`, `{period}`, `{cadence_name}`, `{created_at}`), and it is not decoration. The
dispatcher's finish check looks for `cc_tasks/<stem>_RESULT.md`, where `<stem>` is the instance
file's own stem. A template that named its RESULT any other way — `{cadence_name}_{period}`,
say, which reads naturally and is wrong — would produce a cycle that ran correctly, wrote its
RESULT, and was marked **`blocked` on a filename**, every month, silently. The placeholder
exists so the template can name the file the machine will look for.

## 3. Decision 8 has no start boundary, and installing the schedule mid-month needed one

The implementing task's decision 6 states: *"`dispatch.cadence[0].last_instance` is empty at
ship; nothing is created by this task, because nothing is due."*

**The second clause was false when it was written.** The schedule is monthly on the first
Monday UTC; September 2026's first Monday was the **7th**; the job was installed on the
**16th**. The current period was due, and the instance glob correctly found no *cadence
instance* on disk — because September's cycle was cycle 4, hand-dispatched on 2026-09-10 as
`scan_2026-09-10`, which is not a cadence instance and never will be. The first pass to find a
clean tree would have created and launched **a second September cycle**: two measurements of one
month, the thing a dated measurement may least afford.

`catchup=False` does not cover it. Back-fill protection is about *earlier* periods; the
offending period here is the *current* one, the one the schedule was switched on inside.

So a cadence entry declares **`start_period`** — the first period it may serve — and it is
required rather than defaulted. The obvious default, "the period the config was written in",
would depend on a file's mtime, and a schedule whose start nobody can read off the config is a
schedule nobody can check. **Prior art: Airflow's `start_date`**, which exists for this exact
condition and for no other; it was found by asking what a mature scheduler does about a DAG
enabled mid-interval, which is the question decision 8 did not ask.

`start_period: "2026-10"` is what makes decision 6's sentence true. Cycle 5's period is October
2026 and its due instant is 2026-10-05T00:00Z, exactly as decision 6 states — and now for a
reason the code enforces rather than a reason the author believed.

## 4. Decision 7's sentence and decision 7's code disagreed, in the path nothing had run

Decision 7: *"A pass in which nothing is eligible writes **no** event: the log records
assertions, and 'nothing to do' is not one."*

The shipped `_pass` emitted one `dispatch_refused` per blocked candidate — **directly beneath a
comment quoting that sentence.** It had never executed: the dispatcher shipped disabled, so the
prior task's dry pass returned at `dispatch is disabled` and never reached the branch. Enabling
it was the first time the code ran, and the first enabled pass would have written two events
for two candidates blocked on a dirty tree, and two more five minutes later, for as long as a
session was working.

Every reason reachable from that branch — `dirty_tree`, `above_band`, `network_undeclared`,
`disabled`, `stop_file` — is a **standing condition**: re-evaluated every five minutes and
unchanged until somebody edits a file. Logging one per pass is logging silence. And it feeds
itself here, because `seldon_events.jsonl` is a **tracked** file: writing to it keeps the tree
dirty, which keeps `dirty_tree` true, which writes again.

The branch now writes nothing and names each blocked candidate and its reason on stdout, which
is what the launchd wrapper's log carries. **Nothing is lost**: every one of those reasons is a
live property of a task file or of the checkout, and `seldon dispatch status` computes all of
them on demand with their values. The refusals that still reach the log are the ones that are
*occurrences* rather than *states* — `lease_held`, `api_key_present`, `claim_failed` — each
emitted at its own site.

Two tests now hold the line: a candidate blocked by a dirty tree leaves the log byte-identical
and names itself on stdout, and ten consecutive passes over a dirty tree leave it byte-identical
too. The old suite had only the no-candidate case, which is how the defect survived a green
suite.

## 5. Decision 7's event types were never registered as audit-only, and a replay said so

Not a correction to the note's text — a defect in the build ADDENDUM_01 describes, found while
adding the fifth event type.

`seldon/core/sync.py` carries `_AUDIT_ONLY_EVENT_TYPES`: types that record that something
happened and project no graph state. An unlisted type falls through to a `logger.warning` on
every replay, and the set's own comment gives the reason it exists — nine unlisted records
"would otherwise emit nine WARNINGs on every single replay, which trains an operator to ignore
replay warnings, precisely the signal this set exists to keep meaningful."

`dispatch_launched`, `dispatch_finished`, `dispatch_refused` and `dispatch_observed_stop`
shipped unlisted. They are audit-only in exactly the sense that comment means: the state they
refer to is already projected, by the `artifact_state_changed` of the claim. All four are now
registered, with `cadence_created`.

## 6. Two defects enabling it found, which no reading would have

Both are in the dispatcher rather than the cadence, and both were **unreachable while
`dispatch.enabled` was `false`**. Shipping the mechanism switched off is what kept them
invisible; the first minute of it being on is what showed them.

**(a) A launchd job inherits almost no environment.** The first scheduled pass fired on time
(2026-09-16T03:36:15Z) and died on `neo4j.exceptions.AuthError`. The NEO4J_* variables a
hand-run `seldon dispatch` picks up from the shell are simply not present under launchd. The
wrapper now falls back to `~/.wintermute/.env`, which is this repo's own convention (CLAUDE.md,
and `scripts/build_projection.py::_neo4j_creds` is the parse it copies), and **refuses loudly
with exit 3** when no credential can be found rather than running a pass that cannot read the
queue.

The first attempt at that fix was also wrong, and silently: it used `tr -d` to strip quotes,
which deletes *every* quote character in the value rather than the surrounding pair. This
password contains one. The pass then authenticated with a password one character short —
`AuthError` again, indistinguishable from a wrong password and from no password at all. Both
halves are now tested, the second by lifting the wrapper's own parse block and running it
against a fixture value containing an apostrophe.

**(b) A released lease looked like a dead holder.** `Lease.__exit__` dropped the flock and left
the body naming the holder of the finished pass. The first `seldon go` after enabling therefore
reported `**Lease:** dispatcher:HexagonMBP.local:66065 (holder GONE — seldon dispatch lease
reap)` — a false alarm after every ordinary pass, twelve times an hour at a five-minute poll.
An operator trained to reap on sight will eventually reap a live one. Exit now records the
release and keeps the file (the flock needs a stable inode); `reap` reports `not_held`
distinctly from `no_lease_file`; a holder that was genuinely killed still reaps.

**The shape is worth naming.** A mechanism that ships disabled has no observations behind it,
only reasoning. Four defects across this build and the one before it — the truncated first
dirty path, the refusal-per-pass, and these two — were each found by running the thing once and
reading the output, and none of them by review. §4 of the standing dispatcher's own RESULT made
the same argument about its dry pass; this is the second instance, and the dry pass could not
have reached any of these, because a dry pass runs in a shell.

## 7. What decision 8 got right and this build confirms

The load-bearing clause — *"lets it flow through decisions 2 to 5 like any other task"* — held
without amendment, and it is what made the rest cheap. A cadence instance is evaluated by the
same nine criteria, claimed by the same compare-and-set, launched by the same command line and
finished by the same check as a hand-written task. `c5`'s second limb ("or the task was created
by the cadence rule in decision 8") was written into the matcher when the dispatcher shipped,
before anything could produce such a task, and the first rendered instance passed it with no
change to the criterion: the header reads `**Network:** hosts, under cadence scan_cycle`, which
is the licensed form, and a cycle that contacts federal hosts may not claim `none`.

The alternative shape — a scheduler that ran the cycle itself — would have needed its own copy
of every criterion, its own claim and its own log, and the copies would have drifted. Decision
8 is the reason this task added one capability (a file appearing on a calendar) instead of a
second dispatcher.
