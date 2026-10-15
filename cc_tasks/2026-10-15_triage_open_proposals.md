# CC Task: triage every open proposal: superseded ones close as history, dead ones withdraw, live ideas are marked future, and the status view says only what is moving

**Date:** 2026-10-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session, on the operator's direction of 2026-10-15 ("close out superseded; those are historical at this point").
**Implements:** DN-001 (evidence floor: a closure cites the thing that closed it); AD-030 as recorded in this project (task lifecycle; terminal states supersede and withdraw with reasons).
**Framework layer served (DN-005 §5 rule 1):** none (project bookkeeping).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** db464d5f
**Model:** primary
**Spend:** est. 900k tokens.
**Parts:** A 0.70, B 0.30.
**Part map:** A is the triage; B is the status line and the report.
**Network:** none.

**HEADLESS NOTICE.** No next turn.

## Step 0

If this task is `in_progress` from an earlier dispatch, stop. Otherwise set it `in_progress`.

## The population

Every ResearchTask in this project's graph in state `proposed` or `accepted` other than this task and db464d5f, whether or not it has a source file. Today that is 11 proposals, the oldest from 2026-09-16; some are `FUTURE` ideas by their own first word, some are Seldon defects filed here, some are superseded by work since done.

## The decision rule (apply it; do not ask)

For each task, in this order, with the evidence named in the reason:

1. **Supersede** when what it asked for has been done or decided elsewhere: a completed task whose RESULT covers it, an accepted ruling that settles it, code at HEAD that implements it, or a newer open task that restates it. `seldon task supersede <id> --superseded-by <artifact>` with the evidence in the reason. A Seldon defect filed here that was fixed in seldon (check seldon's graph and its RESULT files by absolute path, read-only) is superseded by that seldon task's id.
2. **Withdraw** when its premise no longer holds: the component is mothballed or gone, the file it names is gone, the ruling it relied on was reversed, or it duplicates another task closed under rule 1. `seldon task withdraw <id>` with the reason.
3. **Future** when it is still valid and still unscheduled: an idea, a parked enhancement, work gated on a trigger that has not fired. Rewrite its description to begin `FUTURE (not scheduled; trigger: <the condition>):` so every status view can filter it. Do not create new tasks for these.
4. **Active** when it is live work with a current reason to run and nothing is blocking it except attention. Expected to be rare; name each one in the RESULT with the reason it belongs on the critical path.
5. **Undecidable with evidence** goes to the RESULT as a question for the operator with the two readings. Cap: three. A fourth means the rule needs a better clause; say which.

A Seldon defect filed in this project that is still open in seldon and not filed there: file it there (`seldon task create --project /Users/brock/GitHub/seldon`, description copied, origin cited) and supersede the local one by the new seldon id. No code changes in seldon from this task.

## Part B: the status line

`seldon status` and `seldon go` in this project print, first, one line: `Moving: <n> in progress, <n> proposed with a source file; <n> future ideas; <n> closed this week.` Future ideas are excluded from the candidate count the dispatcher logs. If this needs a Seldon change rather than project config, file it as a seldon task and say so; do not patch seldon from here.

- check: `seldon_query` after the pass: zero tasks in `proposed` without either a source file or a `FUTURE` prefix, other than those the RESULT names as active.
- check: every supersede carries a `superseded_by` edge; every withdraw a `terminal_reason`; quote the counts.
- check: `seldon verify`.

## RESULT

Under 40 lines: a table, one row per task: id, first words, decision, evidence. Then the active list, the questions (at most three), and the status line as printed. `seldon cc complete`, commit, push.
