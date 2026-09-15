# ADDENDUM 01 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-15. **Amends, does not supersede.** Written by the implementing task
(`cc_tasks/2026-09-15_standing_dispatcher.md`), whose §6 requires that any DN-006 decision the
build showed to be wrong be corrected here rather than silently deviated from. Three
corrections; decisions 1, 2, 6, 7, 9 and 10 stand unchanged.

## 1. Decision 3's marker survey found a partial convention, not none

Decision 3 says: derive from the existing addenda whether a prior convention was in use; if one
is found, adopt it and correct this note; if none, `**Status:** SUPERSEDED` within the first ten
lines **is** the convention.

**Neither branch is quite right, and the survey is why.** Over the 34 `cc_tasks/*_ADDENDUM*.md`
files in `ai-readiness-kg`:

* a bolded `**Status:**` field in the first ten lines is an established habit — **5 of 34** —
  with an upper-case verb vocabulary: `AMENDS` in four, `SUPERSEDED` in one;
* but only **1 of 34** has ever expressed base-task supersession, and it spells it
  `**Status of base task: SUPERSEDED — DO NOT EXECUTE.**`
  (`2026-09-01_harness_reconciliation_ADDENDUM-01.md`, whose base task is `481b6994`, genuinely
  `superseded` on the graph);
* eleven files use `**Supersedes:**` or `Supersedes ADDENDUM-0N`, but every one of those
  supersedes a **prior addendum or a clause**, never the base task. Different relation, and a
  matcher that read them as base-task supersession would make eleven executable tasks
  undispatchable.

One instance in 34 is not a convention, so **decision 3's marker is what gets written from here
on** and `CLAUDE.md` says so. But the matcher accepts the one historical spelling as well,
because the alternative is a dispatcher that reads the single genuinely superseded task in the
repository as executable — which is the one outcome c3 exists to prevent. The regex is
case-sensitive on `SUPERSEDED`: four of the five Status lines say "Does not supersede it", and
a case-insensitive match reads the sentence that says the opposite as a supersession.

The marker must also be **searched for within** the line rather than anchored to its start:
every real Status line in that repository sits after a `**Date:** ...` on the same line, so an
anchored pattern reads none of them.

## 2. Decision 4's claim is two transitions from `proposed`, not one

Decision 4: "The pass transitions the chosen task to `in_progress` with `claimed_by = ...`".
Decision 2's c1 admits a task in `proposed` **or** `accepted`.

`proposed -> in_progress` is not an edge on the ResearchTask state machine
(`seldon/domain/research.yaml`: `proposed: [accepted, rejected, superseded, withdrawn]`;
`accepted: [in_progress, ...]`). From `proposed` the claim is therefore
`proposed -> accepted -> in_progress`, with the claim marker on the second hop, where the
machine puts it. That is the same shape `walk_to_completed` already uses for the close path, so
it is the codebase's existing answer to "walk a task to a state several transitions away" and
not a new mechanism.

The compare-and-set property decision 4 depends on is unchanged: `transition_task` validates
every precondition before its first write, so a failed first hop leaves the graph untouched and
a failed second leaves the task `accepted`, which is an open state the next pass re-evaluates.
**A failed transition launches nothing** either way.

## 3. Decision 5's permission mode could not be derived from this repository

Decision 5: "Whatever non-interactive permission mode the CLI needs to execute tools headlessly
is derived from how this repo already runs `claude -p` unattended."

**It cannot be derived from there, and the reason is itself the finding.** This repository's one
unattended `claude -p` is `kg/extraction/model_stub.py`, and it runs
`--allowed-tools ""` — an empty allowlist, no tools at all — from a hermetic empty cwd so the
model loads no project context. That is the deliberate opposite of what a dispatched session
needs, and it is evidence that **this repository has never run a tool-executing headless
session**. There was nothing to derive.

The value comes from the CLI's own interface instead: `claude --permission-mode` takes
`acceptEdits | auto | bypassPermissions | manual | dontAsk | plan` (claude 2.1.272), and
`bypassPermissions` is the one that does not prompt. A headless session in any prompting mode
blocks forever on its first tool call, having consumed a claim and produced nothing. It is
recorded in `seldon.yaml` with that reasoning beside it, as decision 5 requires, and not only
in the plist.

## 4. One thing decision 2 did not anticipate, reported rather than corrected

Decision 2's closing paragraph says "the 24 tasks open at this writing stay operator-dispatched
until re-authored". The count was right; the mechanism is not the one the note pictures.
**23 of the 24 carry no `source_file` at all** — they were created with `seldon task create`
from a Desktop thread, not registered from a task file — so they are not candidates because
there is no file to read headers from, not because the file lacks headers. The opt-in works
exactly as intended; the diagnostic differs, and `status` reports `no_source_file` rather than
`no_header:...` so a reader is not sent looking for headers in a file that does not exist.

## 5. What this addendum does not change

Decisions 1 (home and shape), 2's criteria table itself, 6 (the lease and its PID-gated reap),
7 (the four event types and the silent empty pass), 9 (FIFO) and 10 (no hand-dispatch while
enabled) are implemented as written. Decision 8 (cadence) is untouched and remains the next
task. The ninth criterion the implementing task's own ADDENDUM_01 adds — the
`**Framework layer served` header — is recorded there and in the build; it extends decision 2's
table by one row and does not renumber it.
