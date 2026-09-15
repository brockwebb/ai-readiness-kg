# DN-006 — Design note: the standing dispatcher

**Date:** 2026-09-15. Desktop design note for ResearchTask `6ee71737`, DN-005 §4 item 1. Under DD-001, DD-004, DD-007, DD-019, DD-022, DD-060, DD-065 and the L4 autonomy model (operator touchpoints are a closed list: spend above the standing band, external sends, value inputs, incident notification).

**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M. January's numbers must be January's; a cycle that waits for a human to paste a line is a cycle whose date is set by the human's attention. The dispatcher is the mechanism by which cycle 5 and every later cycle run from a schedule and publish to the log under their own gate (DN-003). Nothing here advances a view or a publication.

---

## 1. The condition

Between 2026-08-31 and 2026-09-01, auto-registered gap tasks, an addendum whose gate had opened, and zero-spend housekeeping all sat in `proposed` until a person relayed a dispatch line into Claude Code (`6ee71737`). The same shape recurs in every thread close since: the handoff ends with one or two dispatch lines and the work waits for the next session. The system decides into `proposed` and then waits for a message bus. That is a latency defect, not a decision defect: nothing about *which* task to run is missing, only the act of starting it.

## 2. Prior art, read before designing

* **Schedulers with a claim step.** Airflow's scheduler moves a task instance to `queued` then `running` and bounds concurrency with pools and `max_active_runs`; the claim is a database row transition, not a message. Kubernetes' Job controller and the `coordination.k8s.io/Lease` object separate *who holds the right to act* (holder identity, acquire time, renew time, duration) from *what is acted on*. GitHub Actions `concurrency` groups serialize jobs by a key. The shape common to all three: a compare-and-set claim before launch, a bounded concurrency parameter, and a lease with an identified holder.
* **Advisory locks and liveness.** Burrows, *The Chubby lock service* (OSDI 2006): locks are advisory, leases expire, and a holder that stops renewing loses the lease rather than blocking forever. Locally, DD-022's spend ledger is `flock`-guarded and its orphan reap (`controls.yaml spend.orphan_reservation_age_seconds`) qualifies a reservation by **PID liveness, never by age alone**. That rule is adopted unchanged for the dispatcher's lease.
* **Kill switches already in this repo.** The burn's STOP file halts a run until an operator removes it; `controls.yaml` is the on/off panel (DD-004); cap exhaustion is a clean exit 0. The dispatcher reuses both idioms rather than adding a third.
* **The batch-identity class.** DD-019 recorded the ceiling being enforced per shard so two workers spent 22.0M against a 12M ceiling. Two runners on one queue is that defect at runner grain. It is why concurrency starts at one and why the lease is a hard single-instance guard, not a hint.
* **Event-sourced decisions.** DD-065: every judgement the project asserts is on the log. A dispatch is an assertion that a task was eligible under named criteria at a named time; it goes on the log with the criteria vector, so a stranger can replay why anything ran.

## 3. Decisions

**1. Home and shape.** The dispatcher is a `seldon dispatch` command group in the Seldon repo, configured per project by a `dispatch:` block in that project's `seldon.yaml`. It polls the Seldon graph (registered ResearchTasks with a `source_file`), not a separate queue: the graph already is the queue. Subcommands: `once` (one evaluation pass, at most one launch, exit), `status` (the live criteria vector for every candidate, launches in flight, lease holder), `lease reap` (operator-only; refuses while the holder PID is alive). There is no long-lived daemon: launchd is the loop, `once` is the pass, which is the pattern `scripts/jobs/biblio_resume_job.py` already runs under.

**2. A task is eligible only when every criterion below evaluates true, and each evaluation is recorded as a value, not a boolean summary.**

| # | criterion | read from |
|---|---|---|
| c1 | task is a registered ResearchTask in `proposed` or `accepted` with a `source_file` that exists and is git-tracked | graph, filesystem, git |
| c2 | every `precedes` predecessor is in `completed`, `verified`, `superseded` or `withdrawn`; a predecessor in `blocked` or `rejected` makes the successor ineligible | graph |
| c3 | no sibling `<stem>_ADDENDUM*.md` carries the supersession marker | filesystem |
| c4 | the task file's `**Spend:**` header declares `zero` or a token ceiling at or below the standing band | task file, `controls.yaml#spend.daily_tokens` via a reference in `seldon.yaml`, never a copied number |
| c5 | the task file's `**Network:**` header declares `none`, or the task was created by the cadence rule in decision 8 | task file |
| c6 | no task is `in_progress` under a dispatcher claim, and no dispatcher-launched process is alive (PID liveness); concurrency is one | graph, lease file |
| c7 | the working tree is clean and on the configured branch | git |
| c8 | `dispatch.enabled` is true in `seldon.yaml` and no STOP file exists; both read on every pass, never cached | `seldon.yaml`, filesystem |

A task whose file has no `**Spend:**` and `**Network:**` headers is **not a candidate**. The dispatcher takes only tasks authored under this convention; the 24 tasks open at this writing stay operator-dispatched until re-authored. Opt-in, so nothing already queued changes behaviour when the job is installed.

**3. The supersession marker is machine-readable or it does not exist.** An addendum supersedes its base task by carrying, in its first ten lines, the line `**Status:** SUPERSEDED`. The implementing task derives from the existing addenda whether any prior convention was in use; if one is found, it is adopted and this line is corrected by an addendum to this note; if none, this is the convention and `CLAUDE.md`'s CC dispatch protocol says so.

**4. Claim before launch, and the claim is the compare-and-set.** The pass transitions the chosen task to `in_progress` with `claimed_by = dispatcher:<host>:<pid>` and `claimed_at`, then launches. A transition that fails launches nothing. The claim marker already exists on the state machine (`seldon_task_update`); the dispatcher writes it and nothing else reads it as a lock. At finish the dispatcher records exit code, wall clock, whether `<stem>_RESULT.md` exists, and whether the graph shows the task `completed` (the CC session runs `seldon cc complete` itself, per protocol). Exit non-zero, or no RESULT, or no completion in the graph: the task moves to `blocked` with the log path on the event. **The dispatcher never retries.** A retry is a decision, and it belongs to the next OODA, which reads the log.

**5. Launch is `claude -p` from the project root, detached, logged.** The prompt is exactly the CC dispatch line `CLAUDE.md` prescribes. Working directory is the project root so `CLAUDE.md` loads: the inverse of `model_stub.py`'s hermetic cwd, which exists to keep a JSON-only call from narrating; here narration is the point. Output goes to `logs/dispatch/<stem>.log` with `EXIT=$?` appended. Max OAuth only; `ANTHROPIC_API_KEY` in the environment is a refusal (DD-007). Whatever non-interactive permission mode the CLI needs to execute tools headlessly is derived from how this repo already runs `claude -p` unattended, and the flag with its reason is recorded in `seldon.yaml`, never only in the plist.

**6. One instance, by lease.** `fcntl.flock` on `<project>/.seldon/dispatch.lock`; the file holds holder `host:pid`, `acquired_at`, `heartbeat_at`, and the task in flight. A second `once` that cannot take the flock exits 0 and writes a `dispatch_refused` event with reason `lease_held`. `seldon dispatch lease reap` is the only release path other than process exit, and it refuses while the holder PID is alive. No age-based auto-reap, for the reason DD-022 gives.

**7. Events, on Seldon's own log.** `dispatch_launched` (task id, criteria vector with values, claim marker, log path), `dispatch_finished` (exit code, wall clock, RESULT present, graph state observed), `dispatch_refused` (task id or null, reason: `lease_held`, `stop_file`, `disabled`, `dirty_tree`, `above_band`, `network_undeclared`), and `dispatch_observed_stop` once per STOP-file appearance. A pass in which nothing is eligible writes **no** event: the log records assertions, and "nothing to do" is not one. `status` computes the same vector live for the operator's eye.

**8. Cadence produces a task; it does not bypass the queue.** `seldon.yaml dispatch.cadence` lists named schedules, each with a calendar rule, a template under `cc_tasks/templates/`, and the name of the last instance created. When a schedule is due and no instance for that period exists, the pass renders the template (cycle name substituted, `**Network:** hosts, under cadence <name>` in the header), registers it, and lets it flow through decisions 2 to 5 like any other task. This is how cycle 5 runs on the first Monday UTC monthly (DD-060), and it is the second implementing task, not the first.

**9. Priority is FIFO by `created_at` among eligible tasks.** The Desktop orders work with `precedes` edges and with nothing else. A priority field would be a value nobody measured.

**10. While `dispatch.enabled` is true, the operator does not hand-dispatch.** The dispatcher cannot see a session it did not launch except through c7. A hand-dispatched session and a dispatched one in the same checkout is the batch-identity class in the one place the design cannot guard, so the guard is the rule.

## 4. What this does not solve, stated so nobody thinks it did

The gap named in `6ee71737` has two halves. This note closes **dispatch latency**: a registered task with a clean gate no longer waits for a person. It does not close **post-completion decision latency**: reading a RESULT, naming its wrong premises and authoring the next task is still the Desktop OODA, run when a Desktop thread opens. That half is a decision-making problem and is not designed here.

## 5. Parameters and their basis

| parameter | value | basis |
|---|---|---|
| poll interval | 300 s (launchd `StartInterval`) | **no measured basis.** A pass is a local graph read at zero spend. After one week of `dispatch_launched` events, dispatch latency (registration `created_at` to launch) is measurable and the interval is set from it; until then this is a declared starting value and says so in `seldon.yaml` |
| concurrency | 1 | DD-019 defect; the file-ownership model that would license 2 is undesigned and untested |
| standing band | reference to `controls.yaml#spend.daily_tokens` | the same number the spend guard enforces; a second copy would drift |
| lease reap | operator-only, PID-liveness gated, never by age | DD-022 orphan-reap rule |
| retries | 0 | a retry loop on a CC task is unbounded spend with no gate |

## 6. Where this note is cited

`cc_tasks/2026-09-15_standing_dispatcher.md` (implements decisions 1 to 7, 9, 10), the cadence task that follows it (decision 8), `CLAUDE.md`'s CC dispatch protocol (decision 3's marker and decision 10's rule), and `6ee71737`, which this note and its implementing task supersede.
