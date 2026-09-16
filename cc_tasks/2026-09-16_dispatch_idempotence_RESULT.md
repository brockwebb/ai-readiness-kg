# RESULT — a dispatcher pass is idempotent, and it commits what was registered

**Task:** `cc_tasks/2026-09-16_dispatch_idempotence.md` (no addenda; globbed before starting and
again before §4, both times empty — `ls cc_tasks/2026-09-16_dispatch_idempotence_ADDENDUM*.md`
returned only the base file).
**Executed:** 2026-09-16 UTC. **Hand-dispatched**, and this is the last such case: the file that
describes decision 3 could not be committed by a mechanism that did not yet exist.
**Spend:** zero model calls. **Network:** none — no host was contacted; the only remote-shaped
access is Neo4j on localhost and two `git push` to GitHub, which §5 requires.
**Gate: GREEN.** Every number below is quoted from a log named in §7.

---

## 0. The headline

`make gate-full` here: **2276 passed, 18 skipped, 12 xfailed in 1385.57s (23:05)**, `EXIT=0`.

The previous task's gate was **red on exactly one test** and could not be anything else
(`cc_tasks/2026-09-16_publication_guards_RESULT.md` §0): a dispatched session's lease made every
five-minute pass write a `dispatch_refused` event, and a standing test asserted that a pass
writes none. Both halves are now fixed — the dispatcher writes one `lease_held` event per
**acquisition**, and the project-side test asserts **idempotence** rather than emptiness.

| | before (publication_guards) | after (this task) |
|---|---|---|
| `make gate-fast` | 1 failed, 2249 passed, 17 skipped, `EXIT=2` | **2251 passed, 18 skipped, 25 deselected, 12 xfailed in 418.04s**, `EXIT=0` |
| `make gate-full` | 1 failed, 2274 passed, 17 skipped, `EXIT=1` | **2276 passed, 18 skipped, 12 xfailed in 1385.57s**, `EXIT=0` |

The one extra skip is deliberate and is decision 2's narrowed single-pass test declining to run
outside the state it asserts (§3).

---

## 1. Both repos' commits

| repo | commit | what |
|---|---|---|
| `seldon` | `8172296` | `feat: a dispatcher pass is idempotent, and it commits what was registered` — decisions 1 and 3, 30 tests in `tests/test_dispatch_launch.py` (21 before), 9 of them red first |
| `seldon` | `eea0aed` | `Merge feat/dispatch-idempotence: a pass is idempotent, and it commits what was registered` (`--no-ff`, the repo's pattern) |
| `ai-readiness-kg` | see §8 | decision 2's tests, DN-006 ADDENDUM_03, the protected-paths check, this RESULT |

**Seldon suite on the merged commit `eea0aed`: 1893 passed in 139.80s, `EXIT=0`.** It was run
three times — on the branch tip before the lint fix (1893 passed, 155.58s), on the final branch
code (1893 passed, 150.34s), and on the merge commit itself (above). All three green.

**"Reinstalled" needed no step and the RESULT says why rather than claiming one.** Seldon is an
**editable** install (`pip show seldon`: `Editable project location: /Users/brock/GitHub/seldon`),
so merging to `main` is what makes the code live. Verified rather than assumed:
`seldon.commands.dispatch.__file__` resolves to `/Users/brock/GitHub/seldon/seldon/commands/
dispatch.py`, and both new symbols (`_commit_registered`,
`_lease_acquisition_already_refused`) are importable from the installed package.

**Both pushes succeeded.** `seldon`: `61cad01..eea0aed main -> main`, exit 0. `ai-readiness-kg`:
§8.

---

## 2. Decision 1 — the per-reason refusal table, and the rule behind it

Decision 1 asks for `lease_held` to get the STOP file's treatment and for `dirty_tree`,
`disabled` and `above_band` to be **reviewed against the same rule**. Reviewing them turned up
the fact that the rule had never been written down: the STOP branch had the suppression and its
neighbour did not, and nothing said which of the two was right. So the rule is stated, in
DN-006 ADDENDUM_03 §1 and in the code:

> **A standing condition earns an event when, and only when, its beginning is recorded nowhere
> else a reader can reach. The event marks the beginning, never the observation.**

| reason | what it is | where its beginning is already recorded | event | changed here |
|---|---|---|---|---|
| `lease_held` | standing, for the length of a dispatched session | **nowhere** — `.seldon/dispatch.lock` is gitignored runtime state the next acquisition overwrites, and a pass that takes the lease without launching writes no `dispatch_launched` either | **one per acquisition**, keyed `(holder, acquired_at)` | **yes** — was one per pass |
| `stop_file` | standing, until an operator removes it | **nowhere** — `.seldon/DISPATCH_STOP` is gitignored; its mtime is the only trace | one per appearance, keyed on mtime | no (already correct; it is the model) |
| `dirty_tree` | standing, while a session works | **git**, exactly and by path | none | no |
| `disabled` | standing, until `seldon.yaml` is edited | **git** — the commit that flipped the key | none | no |
| `above_band` | a property of a tracked task file's `**Spend:**` header | **git** | none | no |
| `network_undeclared` | a property of a tracked task file's `**Network:**` header | **git** | none | no |
| `api_key_present` | an **occurrence**: an environment this pass was in, gone by the next | nothing | one per pass | no |
| `claim_failed` | an **occurrence**: a compare-and-set that lost | nothing | one per pass | no |

The two occurrences at the bottom are why the rule is about *beginnings* and not about
*silence*: suppressing `api_key_present` would hide a DD-007 refusal.

**`acquired_at` is new on the payload** and is load-bearing: `dispatcher:<host>:<pid>` recycles,
and a suppression keyed on the holder alone would swallow a genuinely new collision taken by a
reused PID.

**Verified in the checkout where the defect was observed**, not only in a fixture
(`logs/lease_held_once.log`): a lease was taken, the real launchd wrapper was run **six times**
under it, and the log grew by **one** line.

```
lease_held events before: 3   total lines: 34749
  pass 1: rc=0  lease_held events on the log now: 4
  pass 2..6: rc=0  lease_held events on the log now: 4   (unchanged)
six passes over one acquisition added: 1
```

The three pre-existing `lease_held` events are the defect's own record — 04:27:49Z, 04:36:55Z
and 04:38:55Z, **all naming one holder**, `dispatcher:HexagonMBP.local:71841`. They stay
(task decision 5); they are a true record of what the dispatcher did.

**A number in the source RESULT that this corrects:** `publication_guards_RESULT.md` §0 says
"Five of the seven uncommitted `seldon_events.jsonl` lines this session inherited are dispatcher
lines". That is right about *dispatcher lines*; the count of **`lease_held` refusals** on the log
is **three**, and three is the number this task's fix is measured against.

---

## 3. Decision 2 — the invariant is idempotence, and it never skips

`test_a_pass_in_a_launchd_shaped_environment_reaches_the_queue_and_writes_no_event` is replaced
by two tests plus one that pins the addendum.

**`test_two_passes_in_a_launchd_shaped_environment_leave_the_event_log_byte_identical`** — the
real wrapper under `env -i`, twice, sha256 compared after each pass. It skips only when Neo4j is
down, which is a fact about the machine. Before running it reads `seldon dispatch status --json`
(which writes no event) and **fails rather than skips** if anything is eligible: a pass that
would launch is not an idempotence experiment, and starting a CC session out of a test is not
something to do quietly.

**The two-pass byte comparison, in the real repo** (`logs/two_pass_bytes.log`):

```
events lines before :    34749
sha256 before       : 19d95f868a5855da22da12c3885de69bef91763b6f55234a986233ffec94c535
pass 1 rc=0
sha256 after pass 1 : 19d95f868a5855da22da12c3885de69bef91763b6f55234a986233ffec94c535
pass 2 rc=0
sha256 after pass 2 : 19d95f868a5855da22da12c3885de69bef91763b6f55234a986233ffec94c535
events lines        :    34749
```

Byte-identical across both, and in this state even the **first** pass wrote nothing, because
there was nothing to assert.

**On the Seldon side the same invariant is parametrized over every state the dispatcher can be
in**, so the project-side test asserts something already pinned where the code lives:

```
test_a_second_pass_under_a_standing_condition_leaves_the_event_log_byte_identical[nothing_eligible] PASSED
test_a_second_pass_under_a_standing_condition_leaves_the_event_log_byte_identical[lease_held]       PASSED
test_a_second_pass_under_a_standing_condition_leaves_the_event_log_byte_identical[stop_file]        PASSED
test_a_second_pass_under_a_standing_condition_leaves_the_event_log_byte_identical[dirty_tree]       PASSED
test_a_second_pass_under_a_standing_condition_leaves_the_event_log_byte_identical[disabled]         PASSED
```

**`test_a_single_pass_writes_no_event_when_there_is_nothing_to_assert`** keeps decision 7's
original claim, narrowed to the state it is true in, and states its precondition on the skip:

```
SKIPPED [1] tests/test_dispatch_config.py:313: not the quiet state this asserts: tree dirty (4 path(s))
```

That is the 18th skip in the gate counts, and it is honest: a working session's tree is dirty,
so this stronger claim is checkable between sessions and not during one.

---

## 4. Decision 3 — the committed-by-dispatcher tests

All seven passed; `logs/decision_tests.log` has the run.

```
test_the_dispatcher_commits_a_registered_task_file_nobody_committed          PASSED
test_an_untracked_addendum_beside_a_registered_task_is_committed_with_it     PASSED
test_the_dispatcher_commits_the_registration_record_with_the_file_it_records PASSED
test_the_dispatcher_commits_nothing_else_that_is_lying_in_the_checkout       PASSED
test_a_registered_file_that_is_already_tracked_is_not_committed_again        PASSED
test_the_dispatcher_does_not_commit_into_a_checkout_a_claim_is_in_flight_in  PASSED
test_the_commit_is_reported_on_stdout_where_the_wrapper_log_carries_it       PASSED
```

Together with decision 1's three and decision 2's five that is **17 named tests**, all red or
absent before the change; `tests/test_dispatch_launch.py` goes from 21 to 30.

**Two of them failed on my own premise first, and the failure is the interesting part.** I wrote
`test_the_dispatcher_commits_a_registered_task_file_nobody_committed` expecting to read the
task's criteria back off `status` after the pass. `StopIteration`: the task was not in the open
set any more, because **the same pass that freed it went on to launch it**. That is correct and
deliberate — the commit runs before candidacy for exactly this reason, which is decision 8's
shape applied to a Desktop-authored file — so the assertion was rewritten to read `c1.git_tracked
= true` and `c7.ok = true` off the `dispatch_launched` event's own criteria vector, which is
stronger than re-computing them.

---

## 5. Every premise the task file got wrong

**1. Decision 3's write-set boundary makes decision 3 incapable of freeing a single task.**
"Anything else untracked or modified stays c7's business" excludes the event store — but
`seldon cc register` leaves **two** things behind: the untracked task file **and** the
`artifact_created` line it appends to `seldon_events.jsonl`, which this project **tracks**.
Committing the file alone leaves c7 false on a line that describes the file just committed, and
the task stays ineligible forever. **The event store goes in the same commit**, which is the
ordering ADDENDUM_02 §1 already states for the cadence ("the commit carries its own record on
the log"). Recorded rather than silently done: this is the one place the implementation is wider
than the task's sentence, and it is wider because the sentence cannot be satisfied.

**1a. Corroboration from an unrelated direction, found at closeout.** `seldon cc complete`
refused this very task: *"refusing to register an untracked task file … git does not know this
path … 37 such stubs already exist in this project's graph. Fix: Run `git add <file>` first."*
Seldon's own close path had already concluded that an uncommitted task file is a defect and had
been saying so, in an error message, while decision 2's criteria quietly made it unfixable. The
dispatcher now does what that message tells a person to do.

**2. Decision 3 says "every ResearchTask in `proposed`". Implemented over `proposed` AND
`accepted`.** c1 admits both, so `proposed` alone would leave the identical wedge one state
later — a task that reaches `accepted` with an untracked file is as stuck as one in `proposed`,
and for the same two criteria.

**3. Decision 1's heading and its next sentence are two different rules.** "One event per lease
acquisition, none per pass" and "a pass that finds the lease held by a live holder … writes
nothing" cannot both be literal. Resolved to the heading — one per acquisition — because it is
the STOP file's treatment, which the same sentence names as the model, and because the
parenthetical's reason ("`dispatch_launched` already records it") does not hold for a pass that
acquires the lease and launches nothing. The rule that decides it is §2's table.

**4. "Zero edits to … `docs/`" and §2's "DN-006 ADDENDUM_03" contradict each other.** The
addendum lives in `docs/design/`. §2 is the later and more specific instruction, so exactly one
file under `docs/` moved and the protected-paths check asserts the rest of that tree is
byte-identical.

**5. Decision 4 did not anticipate that hand-dispatching under an ENABLED dispatcher needs the
task claimed first.** This task's own ResearchTask (`d958a425`) was `proposed` with an untracked
`source_file` — **the only candidate in a queue of 25** (`seldon dispatch status`: 24 others
report `no_source_file`). The moment decision 3 landed and the tree went clean, a launchd pass
would have committed the file, found it eligible, and launched a **second CC session for the
task already running in this one**. The session walked it `proposed → accepted → in_progress`
(`claimed_by: cc:hand-dispatch:last-under-DN-006-decision-10`) before touching any code, which
is both the truthful state and the guard. Any future hand dispatch must do the same, and DN-006
decision 10 exists so there are none.

**6. Decision 2's single-pass test is kept but does not run during a working session.** The
state it asserts needs a clean tree; a session that is working has a dirty one. It skips with
its reason on the skip line (§3). Not a defect, but the task's "kept … as its own test" reads as
though it would run alongside the other, and it does not.

**A premise that held exactly:** decision 4's "if this task is hand-dispatched … the lease is
free and the gate is green on its own terms". The lease was free the whole session
(`seldon dispatch status`: `lease: free (last released …)`), and the gate is green. **The next
dispatched task is the real test of decision 2**, because it is the first one that will run with
a lease held by its own launcher — and, since the queue's other 24 tasks carry no `source_file`,
it will be **the next task Desktop registers from a file**, whichever that turns out to be.

---

## 6. What is still wrong, and is not fixed here

**The dispatcher's own `dispatch_finished` leaves the tree dirty, and nothing commits it.** It is
appended to the tracked event store *after* the dispatched session has committed and pushed, so
every completed dispatch leaves `seldon_events.jsonl` modified by lines only the dispatcher
wrote. It is why this checkout was dirty when the session opened.

* **For candidacy it self-clears**: the next registration makes a task file untracked too, and
  §5.1's commit takes both paths together.
* **For the cadence it does not.** `_cadence` gates creation on a clean tree, so one uncommitted
  `dispatch_finished` line blocks the schedule — and the first period it can block is
  **October 2026, cycle 5**, which is the thing DN-006 exists to deliver.

Recorded rather than fixed because decision 3 draws its write set at "anything else untracked or
modified stays c7's business", and widening it inside the same task is how a boundary stops
meaning anything. DN-006 ADDENDUM_03 §4 states it; the next task is authored from that
paragraph.

**`CLAUDE.md` was not edited, and the task's conditional is why.** It licenses an edit only if
decision 3 makes a sentence in the CC dispatch protocol false. It does not: the protocol never
said who commits a registered task file.

---

## 7. Verification — every number, and where it can be re-read

| check | result | log |
|---|---|---|
| seldon suite, branch tip | **1893 passed in 155.58s**, `EXIT=0` | `~/GitHub/seldon/logs/seldon_suite.log` |
| seldon suite, final branch code | **1893 passed in 150.34s**, `EXIT=0` | `~/GitHub/seldon/logs/seldon_suite_final.log` |
| seldon suite, **merged commit `eea0aed`** | **1893 passed in 139.80s**, `EXIT=0` | `~/GitHub/seldon/logs/seldon_suite_merged.log` |
| `tests/test_dispatch_launch.py` alone | **30 passed in 17.37s** (21 before) | run inline; also inside all three suites |
| the 9 new tests, red first | **9 failed, 21 passed in 15.70s** | run inline before the fix |
| `make gate-fast` | **2251 passed, 18 skipped, 25 deselected, 12 xfailed in 418.04s**, `EXIT=0` | `logs/gate_fast.log` |
| `make gate-full` (pre-push) | **2276 passed, 18 skipped, 12 xfailed in 1385.57s (0:23:05)**, `EXIT=0` | `logs/suite.log` |
| `seldon verify` | **All checks passed**, `EXIT=0` — 34750 events readable, 122 task source files resolve, precedence acyclic (19 edges) | `logs/seldon_verify.log` |
| protected paths | **PASS**, `EXIT=0` | `logs/protected_paths.log` |
| two-pass byte comparison | sha256 unchanged across both passes | `logs/two_pass_bytes.log` |
| six passes, one acquisition | **+1 event** | `logs/lease_held_once.log` |
| decision-1/2/3 tests by name | 17 named, all PASSED | `logs/decision_tests.log` |

**Both tiers ran and both wall-clocks are reported**, as the tier rule requires: `gate-fast`
418.04s, `gate-full` 1385.57s. `gate-task` was not run and is not this task's gate — no rule
module, no registry, no re-derivation engine changed, and no stored payload was touched. (The
re-derivation tests run anyway inside `gate-full`, which is why it takes 23 minutes.)

**What the protected-paths check asserts** beyond the write set: `docs/` is byte-identical apart
from the addendum §2 requires; `state/`, `events/`, `assessment/`, `kg/`, `framework/`,
`corpus/`, `controls.yaml`, `dixie_evidence.yaml`, `publication.yaml`, `docs/design_decisions.md`
and `CLAUDE.md` are all empty; **5 modified paths, all inside the write set**; and the point of
the task rather than its file list — that every keyed acquisition on the live log has exactly one
event, that the installed suppression recognises the last refusal it wrote, that a *new*
acquisition by the same holder would still be refused, and that the registration commit is
pathspec-limited and gated on claim and branch.

Two bugs in that check, found by running it and fixed before it was trusted: `must_be_empty`
with an expansion that came back empty left `git status` with **no pathspec**, which lists the
whole tree and reports every path as a violation of a rule about `docs/`; and the
pathspec-limited check matched the characters `-A` inside the docstring that **forbids**
`git add -A`. A check that fails loudest when nothing is wrong is worse than no check.

`logs/` is gitignored; what ships is this file quoting it.

---

## 8. Files, and the push

**Seldon** (`8172296`, merged `eea0aed`, pushed `61cad01..eea0aed`):
`seldon/commands/dispatch.py` (+140/−11: `_last_payload`, `_lease_acquisition_already_refused`,
`_commit_registered`, the `lease_held` branch, the `_pass` ordering),
`tests/test_dispatch_launch.py` (21 → 30 tests; `_stub` gained a `stem` parameter).
Lint after the change is the pre-existing baseline — the one warning this task introduced (E128)
was fixed; the two that remain (E501:190, E127:453) are on `HEAD~`.

**This repo:** new — `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_03.md`,
`scripts/check_protected_dispatch_idempotence.sh`, this RESULT, and
`cc_tasks/2026-09-16_dispatch_idempotence.md` itself (untracked until now, which is the whole
point of decision 3). Changed — `tests/test_dispatch_config.py` (+134/−15: one test replaced by
three), `seldon_events.jsonl` (the dispatcher's `dispatch_finished` from the previous task,
Desktop's `artifact_created` for this one, this session's two state transitions, the one
`lease_held` refusal §2 measures, and the `cc complete` close).

**Not changed:** the whole of `docs/` apart from the addendum, `state/`, `events/`,
`assessment/`, `kg/`, `framework/`, `corpus/`, `controls.yaml`, `dixie_evidence.yaml`,
`publication.yaml`, `CLAUDE.md`, and every other `scripts/` file.
