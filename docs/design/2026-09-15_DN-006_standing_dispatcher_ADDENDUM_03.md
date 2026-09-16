# ADDENDUM 03 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-16. **Status:** AMENDS decision 7 and decision 2. Does not supersede either.
Written by the implementing task (`cc_tasks/2026-09-16_dispatch_idempotence.md`), from the
failure `cc_tasks/2026-09-16_publication_guards_RESULT.md` §0 reported: the first session the
dispatcher ever launched could not have a green suite, because the lease its own dispatcher
held made every five-minute pass write a `dispatch_refused` event and a standing test asserted
that a pass writes none.

Two corrections and one addition. Decisions 1, 3, 4, 5, 6, 8, 9 and 10 stand as ADDENDUM_01 and
ADDENDUM_02 left them.

---

## 1. Decision 7's sentence is about assertions, and it needs the rule that decides which
   conditions are assertions

Decision 7 says: *"A pass in which nothing is eligible writes **no** event: the log records
assertions, and 'nothing to do' is not one."* ADDENDUM_02 §4 applied it to the refusal branch
and removed the per-pass events there. What neither says is **why `stop_file` keeps an event
and `dirty_tree` does not**, and without that the next reason added to the list is decided by
taste.

The rule, stated once here and implemented in `seldon/commands/dispatch.py`:

> **A standing condition earns an event when, and only when, its beginning is recorded nowhere
> else a reader can reach. The event marks the beginning, never the observation.**

That is not a new principle; it is the one the STOP-file branch was already following, written
down. Applied to every reason decision 7 names:

| reason | what it is | the record of its beginning | event |
|---|---|---|---|
| `lease_held` | standing, for the length of a dispatched session | `.seldon/dispatch.lock` — **gitignored runtime state, overwritten by the next acquisition**; and a pass that acquires the lease and launches nothing leaves no `dispatch_launched` either | **one per acquisition**, keyed on `(holder, acquired_at)` |
| `stop_file` | standing, until an operator removes it | `.seldon/DISPATCH_STOP` — **gitignored runtime state**, and its mtime is the only trace | **one per appearance**, keyed on mtime (unchanged) |
| `dirty_tree` | standing, for as long as a session works | **git**, exactly and by path | none |
| `disabled` | standing, until `seldon.yaml` is edited | **git** — `seldon.yaml` is tracked and the commit that flipped the key is the record | none |
| `above_band` | a property of a tracked task file's `**Spend:**` header | **git** | none |
| `network_undeclared` | a property of a tracked task file's `**Network:**` header | **git** | none |
| `api_key_present` | an occurrence: an environment this pass found itself in, gone by the next | nothing | one per pass |
| `claim_failed` | an occurrence: a compare-and-set that lost | nothing | one per pass |

The two occurrences at the bottom are why the rule is phrased about *beginnings* rather than
about *silence*: `api_key_present` is not a standing condition at all, and suppressing it would
hide a DD-007 refusal.

**What changed in the code:** the `lease_held` branch gained the suppression its `stop_file`
neighbour three lines above already had, and the refusal payload gained `acquired_at` so the
suppression has an identity to key on. The holder alone will not do —
`dispatcher:<host>:<pid>` recycles, and a suppression keyed on it would swallow a genuinely new
collision taken by a reused PID.

## 2. Decision 2's c1 and c7 cannot both be true for a task nobody committed, so the dispatcher
   commits it

Decision 2 asks c1 for a **git-tracked** task file and c7 for a **clean tree**. A Desktop
session that registers a task satisfies neither, and it cannot: `seldon cc register` leaves an
untracked file *and* appends the `artifact_created` line that records the registration to
`seldon_events.jsonl`, which this project tracks. The registered task is therefore permanently
ineligible, and so is **every other task in the queue**, because c7 is a fact about the
checkout rather than about the task being evaluated.

This is ADDENDUM_02 §1's finding — *"a rendered, uncommitted file fails both, permanently, and
for every other task in the queue"* — one step earlier in the life of a task. ADDENDUM_02 drew
the conclusion for files the **cadence** renders. The same conclusion follows for files a
**Desktop session registers**, from the same two criteria, and it was not drawn: the cadence
was the only writer anybody had in mind.

**So the dispatcher commits a registered task file, before candidacy, under the cadence's own
three properties** (ADDENDUM_02 §1): pathspec-limited, refusing a checkout it does not own,
pushing nothing.

* **What is committed:** the task file, any untracked `<stem>_ADDENDUM*.md` beside it, and the
  event store. The addenda because they are c3's evidence — a dispatcher that committed a base
  task and left its supersession notice untracked would hand a session a task the notice
  forbids. The event store because the modified line **is the record of the registration being
  committed**, which is the ordering ADDENDUM_02 §1 already states ("the commit carries its own
  record on the log"); committing the file alone leaves c7 false on a line describing the file
  just committed, and the mechanism would not free a single task.
* **What is not:** anything else untracked or modified stays c7's business.
* **When it does nothing:** a dispatcher claim in flight, a branch that is not the configured
  one, or `--dry-run`.
* **No new event type.** The commit is recorded by git and the registration by
  `artifact_created`; a third record of one fact is what §1 of this addendum spent its effort
  removing. The pass names the commit on stdout, which is what the launchd wrapper's log
  carries.

A pass that frees a task may then launch it, in that same pass. That is deliberate and it is
decision 8's shape — *"lets it flow through decisions 2 to 5 like any other task"* — applied to
a Desktop-authored file rather than a rendered one.

## 3. Decision 7's test is an idempotence test, because emptiness is not reachable in the only
   environment the dispatcher has

The project-side test that failed asserted that **one** pass leaves the event log
byte-identical. A dispatched session always has a lease held by the process that launched it,
so under §1 that session's first pass writes one line and the assertion is false for a reason
that is correct behaviour.

The invariant that holds in every state the dispatcher can be in is **idempotence**:

> Two passes in succession, with nothing changed between them, leave the event log
> byte-identical after the second.

It holds with a task in flight, with a STOP file present, with a dirty tree, when disabled and
when nothing is eligible — so it runs in the only environment the dispatcher has and **never
skips**. A test that skipped whenever a task was in flight would never run at all.

The single-pass emptiness claim is kept, narrowed to the state it is true in — nothing
eligible, nothing in flight, clean tree — as its own test, which states its precondition and
skips when the checkout is not in it. The two together are decision 7 as amended.

## 4. What is still wrong, and is not fixed here

**The dispatcher's own finish event leaves the tree dirty, and nothing commits it.**
`dispatch_finished` is appended to the tracked event store *after* the dispatched session has
committed and pushed its work, so every completed dispatch leaves `seldon_events.jsonl`
modified by exactly the lines the dispatcher wrote. Two consequences, and they differ:

* **For candidacy it self-clears**, because the next registration makes the task file untracked
  too and §2's commit takes both paths in one commit.
* **For the cadence it does not.** `_cadence` gates creation on a clean tree, so a lone
  uncommitted `dispatch_finished` line blocks the schedule — and the first period it can block
  is **October 2026, cycle 5**, which is the thing DN-006 exists to deliver.

It is recorded rather than fixed because `cc_tasks/2026-09-16_dispatch_idempotence.md`
decision 3 draws its write set at "anything else untracked or modified stays c7's business",
and widening it inside the same task is how a boundary stops meaning anything. The next task is
authored from this paragraph.
