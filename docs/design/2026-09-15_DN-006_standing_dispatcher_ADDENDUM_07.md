# ADDENDUM 07 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-18. **Status:** AMENDS decision 8 for this project. In this project it replaces
DD-060's cadence clause ("monthly, from cycle 3, first Monday UTC"). DD-060 is not edited.
Written by the implementing task (`cc_tasks/2026-09-18_cadence_off.md`), from the operator's
ruling of 2026-09-18: the harness is a utility anyone can run, not an instrument that runs itself
monthly. The goal is an initial set on the 16 bodies, and a rescan happens when someone asks for
one, not on a schedule.

Decisions 1 to 7, 9 and 10 stand as ADDENDUM_01 to ADDENDUM_06 left them.

---

## 1. Decision 8, as amended for this project

Decision 8's rule still holds: **a schedule produces a task; it does not bypass the queue.**
This project now has no schedule. `seldon.yaml` `dispatch.cadence` is `[]`. The `scan_cycle`
entry is removed, along with its `monthly_first_weekday` rule, its `start_period: "2026-10"` and
its empty `last_instance`. The mechanism in Seldon is unchanged, and an empty list is a valid
config (`validate_cadence`). `dispatch.enabled` stays `true`. Hand-written and requested tasks
still flow through decisions 2 to 5.

**What this cancels.** Cycle 5 was due to be created unattended at 2026-10-05T00:00Z, the first
October Monday. It will not be. The next cycle runs when the operator asks for one.

## 2. A cycle is rendered on request

The template `cc_tasks/templates/scan_cycle.md` stays, and a requested cycle is rendered from it.
Seldon has no command for that yet. The request for one is the Seldon issue
`issues/2026-09-18_cadence_render_on_request.md`, filed in the Seldon repo, which asks for
`seldon cadence render <name>`. Until it ships, the command is the one line in
`cc_tasks/2026-09-18_cadence_off_RESULT.md` §1. That line renders through the same
`seldon.core.cadence` functions a scheduled pass used, then stages the file, registers it and
commits it. A requested cycle's period is its UTC date, so two cycles requested in one month
cannot collide on the instance glob.

**c5 on a requested instance.** The rendered `**Network:**` header still reads
`hosts, under cadence scan_cycle`. Decision 2's c5 (as amended by ADDENDUM_05) admits that form by
its grammar and does not check that the named cadence is configured. A requested instance is
therefore eligible on the same terms a scheduled one was. This addendum rules that this is
intended, because the host set is the one `params.cycle.targets` binds, whoever renders the file.
The Seldon issue records the dependency. A c5 later tightened to "a configured cadence" would make
every requested cycle ineligible.

## 3. What is not changed

- **DD-060 is not edited.** Documents are history. Its identity and refusal rules stand whole, and
  only its cadence clause is replaced in this project, by this addendum.
- **The template's body is not rewritten.** Only the "Authored by" sentence changed. The old
  sentence called a human-dated cycle the defect. It now reads: "A cycle runs when the operator
  asks for one, and its date is the day it was rendered." The rest of the template's prose still
  describes the old schedule: "rendered by the standing dispatcher", "DD-060 (monthly, first Monday
  UTC)" and "January's numbers are January's only if the January cycle ran in January".
  `cc_tasks/2026-09-18_cadence_off_RESULT.md` §2 lists these for a follow-up task.

## Prior art

Airflow and cron make the same distinction between a scheduled run and a manually triggered one.
In Airflow, a DAG whose `schedule` is `None` runs only when triggered, and its tasks are the same
tasks a scheduled run executes. This addendum puts the scan cycle in that state: the template is
the DAG, and `schedule=None` is `cadence: []`.
