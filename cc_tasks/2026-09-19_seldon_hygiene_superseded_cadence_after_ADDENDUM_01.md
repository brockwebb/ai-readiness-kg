# ADDENDUM 01 to `2026-09-19_seldon_hygiene_superseded_cadence_after.md`: a Desktop graph write must not silently stop the queue

**Date:** 2026-09-20
**Status:** AMENDS (adds decision 6 and RESULT §4a; supersedes nothing)
**Authored by:** Desktop session, from `logs/airkg_dispatch.log`, 2026-09-20T03:00:39Z to 09:58:15Z.

## What happened, from the log

`65e5da0e` was registered at 03:00:10Z. The 03:00:39Z pass printed:

```
record: seldon_events.jsonl NOT committed: not dispatcher-only (also written by desktop)
register: record of cc_tasks/2026-09-19_seldon_hygiene_superseded_cadence_after.md (65e5da0e) committed as a705522
  65e5da0e dirty_tree: c7  ...
```

and then 84 consecutive passes over seven hours printed `65e5da0e dirty_tree: c7`, exit 0, no event, no notification. Two Desktop actions made the tree dirty, and both are ordinary: (1) `seldon_task_create` (93d28c6e, 02:59:48Z) and later `seldon_task_chain` appended desktop-actor events to `seldon_events.jsonl`, which the registration commit of `2026-09-18_registration_commits` is scoped not to include; (2) the second task file of the same authoring turn sat written and unregistered in `cc_tasks/` until 09:56Z. The operator cleared it by hand with one commit on 2026-09-20. **Step 0 of this addendum's work is `git log --stat a705522^..HEAD -- seldon_events.jsonl cc_tasks/` and the dispatcher's c7 code, quoted in RESULT §4a: if the dirt was something else, say what, and decision 6 is re-scoped to the real cause.**

Prior art: a queue that can stop needs a staleness alarm that is separate from its failure alarm (the dead man's switch; Nagios freshness checks; Prometheus `absent()` and "for:" durations). A healthy exit code on a pass that has refused the same candidate 84 times is the case those exist for. Committing a journal write with the action that caused it is what `2026-09-18_registration_commits` already decided for registration; this extends it to the other Desktop writes.

## Decision 6 (two parts, both in the Seldon repo)

a. **Every MCP write tool that appends to the event store commits its own append, path-scoped, the way registration does**: `seldon_task_create`, `seldon_task_update`, `seldon_task_close`, `seldon_task_withdraw`, `seldon_task_supersede`, `seldon_task_chain`, `seldon_task_precede`/`unprecede`, `seldon_issue_create`/`update`. If a dispatched session holds the lease the commit is deferred to the next pass, which commits desktop-actor events it finds (the rule `not dispatcher-only` becomes `dispatcher or desktop, no cc`). A `cc`-actor uncommitted event still refuses, as now: that is the DD-019 class and the guard stays.
b. **A candidate refused on the same criterion for N consecutive passes raises the notifier once**, with the criterion and the dirty paths in the body, and writes one `dispatch_stuck` event; it re-arms when the criterion changes or clears. N comes from `seldon.yaml` (`dispatch.stuck_after_passes`), default 3, which at `poll_interval_s: 300` is fifteen minutes; stated as a starting value with no measured basis, like `poll_interval_s`. The refusal line in the pass log names the dirty paths (`git status --short`, first ten), not only the task file.

Tests: a store with an uncommitted desktop `artifact_created` is dispatched after one pass; with an uncommitted `cc` event it is refused; three identical refusals produce exactly one notification and one event, a fourth produces none, a cleared-then-recurring refusal produces a second.

**Write set additions:** the MCP server module, `seldon/core/dispatch.py`, `seldon/commands/dispatch.py`, tests; here, `seldon.yaml` (the one new key with its comment). **RESULT §4a:** step 0's quotes, and the pass log of a scratch checkout showing a)'s commit and b)'s single notification.
