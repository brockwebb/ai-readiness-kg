# ADDENDUM 04 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-16. **Status:** AMENDS decision 8 and decision 2's c7 gate; CLOSES ADDENDUM_03
§4. Does not supersede anything.
Written by the implementing task (`cc_tasks/2026-09-16_dispatcher_commits_its_record.md`),
from ADDENDUM_03 §4: every completed dispatch left `seldon_events.jsonl` modified by a
`dispatch_finished` line only the dispatcher wrote, and the cadence gates creation on a clean
tree, so that line could block cycle 5 on 2026-10-05.

Decisions 1, 3 to 7, 9 and 10 stand as ADDENDUM_01 to ADDENDUM_03 left them.

---

## 1. The dispatcher commits every line it writes to a tracked store, in the pass that wrote it

**Rule.** A line the dispatcher appends to the tracked event store is committed by the
dispatcher in the same pass. The commit is pathspec-limited to the store and is made **only when
every appended line carries `actor: dispatcher`** and the working copy begins with HEAD's bytes.
The commit message names each event type and task id. **The test is the tree, not the event:**
after a pass, `git status --porcelain -- seldon_events.jsonl` is empty unless a session is in
flight.

**Prior art.** None of this is new, and none of it is ours:

* Pathspec-limited commit is `git commit -- <paths>`, which git documents as `--only`: it
  commits those paths' working-tree contents and ignores whatever else is staged
  (git-commit(1), "--only"). `D.commit_paths` has always used it; ADDENDUM_02 §1 adopted it for
  the cadence.
* A bot that commits the state files it writes is the ordinary CI pattern, for example GitHub
  Actions jobs that commit generated files under a bot identity. The two guards here are the
  ones that pattern uses: commit only the paths the bot owns, and do not commit into a checkout
  another writer is working in.
* The actor check is the append-only log's own contract (the store is append-only;
  `seldon.core.events.append_event`) applied as a precondition. It is not a new mechanism.

**Where each line is written, and who commits it.**

| line | written | lease held by this pass? | committed by |
|---|---|---|---|
| `artifact_created` (Desktop registration) | before any pass | — | the registration commit (ADDENDUM_03 §2); unchanged |
| claim transitions + `dispatch_launched` | before launch | yes | **this pass, before the launch** (new), so the session opens on a clean, pushed tree |
| `dispatch_finished` (+ `blocked` transition) | after the session exits | yes | **this pass, after the finish** (new). This closes ADDENDUM_03 §4 |
| `dispatch_refused{claim_failed}` | in the pass | yes | **this pass** (new) |
| `cadence_created` | in the pass | yes | the cadence commit (ADDENDUM_02 §1); unchanged |
| `dispatch_refused{lease_held}` | while another process holds the lease | **no** | the session in flight, or the finish pass (below) |
| `dispatch_observed_stop` | before the lease; the world is stopped | **no** | the first pass under the lease after the STOP file is removed |
| `dispatch_refused{api_key_present}` | before the lease (DD-007: touches nothing) | **no** | the first pass under the lease once the key is gone; the launchd wrapper unsets it, so only a hand-run pass reaches this |

**A pass never commits without the lease.** A held lease is the only way a pass knows no
dispatched session is working in the checkout, and a `git commit` beside a working session is
DD-019's batch-identity class (and an `index.lock` collision). So the three lines written
without the lease are left where they are, and **every pass that takes the lease with no
dispatcher claim in flight commits any dispatcher-only leftovers first, before it reads the
tree.** The same sweep covers a pass that died between its append and its commit, and it covers
the dispatcher process that launched the implementing session: that process was still running
the earlier code, so its own `dispatch_finished` for that session is committed by the next pass.

**What it refuses, and says so on stdout.** An appended line with any other actor means a
session or an operator wrote to the store and did not commit. That is their finding, and c7
surfaces it; the dispatcher does not commit it under its own message. The same applies to a
working copy that does not begin with HEAD's bytes, which means the store was edited in place.

## 2. The dispatcher pushes what it commits, and retries a failed push

A local `main` ahead of origin by dispatcher commits satisfies the clean-tree gate while the
record on GitHub disagrees with the record on the machine. So:

* **Push follows commit in the same pass.** It also follows the pre-launch commit, so a
  dispatched session starts level with origin.
* **A failed push is not a refusal and writes no event.** It is printed on stdout
  (`push FAILED (…; retried next pass)`), which the wrapper's log carries.
* **The retry has no state of its own.** Every pass under the lease with no claim in flight
  pushes whenever `git rev-list --count @{u}..HEAD` is non-zero, so "retry" means "still ahead".
  git records when the branch became ahead, so the log records nothing.
* `GIT_TERMINAL_PROMPT=0`: a launchd pass has no terminal, and a credential prompt would hang
  the pass until the next pass collided with its lease.
* A branch with no upstream is reported and is not an error.

**This widens the dispatcher's outward-facing surface by one verb, `git push`, to the
project's own configured remote.** The task's `**Network:**` header declares it. The operator's
doctrine makes commit-and-push the machine's job, never the operator's. A consequence to know:
a pass pushes *everything* the configured branch is ahead by, including any unpushed commits
the operator made by hand on `main`.

## 3. The cadence's clean-tree gate, re-read

After §1 and §2, a tree can be dirty at a cadence tick in only three ways:

1. **A session in flight.** Correct to wait. The claim is reported as `claim_in_flight`, and a
   held lease means the pass never reaches the cadence at all.
2. **A Desktop-authored file not yet committed.** ADDENDUM_03 §2's commit runs before the
   cadence in the same pass, so this is never the dirt that blocks a tick.
3. **The operator's own uncommitted work.** Correct to wait.

**The reason is now printed with its evidence**, and the row carries it as `blocked_evidence`:

```
cadence scan_cycle 2026-10 is due and NOT created (dirty_tree): <path>, <path> (+N more)
cadence scan_cycle 2026-10 is due and NOT created (claim_in_flight): <task8> by <holder>
cadence scan_cycle 2026-10 is due and NOT created (wrong_branch): on <branch>, configured main
```

This way October's first pass can be read from `logs/airkg_dispatch.log` alone.
`tests/test_dispatch_config.py` asserts these three strings against this project's own cadence
entry at 2026-10-05T00:30Z. It also asserts the ordering in `_pass`: own lines, then registered
files, then the cadence.

## 4. ADDENDUM_03 §4 is closed

The residue it recorded, a lone `dispatch_finished` blocking the schedule, no longer arises.
The Seldon test `test_a_pass_after_a_finished_dispatch_creates_the_due_cadence_instance` covers
it end to end: a dispatch finishes, and the next pass at the October instant creates the instance
instead of reporting `dirty_tree`.
