# CC Task: the cadence is off; a cycle is something a person asks for

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the operator's ruling of 2026-09-18: the harness is a utility anyone can run, not an instrument that runs itself monthly; an initial set on the 16 bodies is the goal, and a rescan is requested, not scheduled.
**Implements:** DN-006 decision 8 amended: a schedule may produce a task, and this project has no schedule. DD-060's "monthly, first Monday" is superseded for this project by this ruling; the template stays so a cycle can be rendered on request.
**Framework layer served (DN-005 §5 rule 1):** none. Dispatch path.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

**Decisions taken here (operator overrides later):**

1. **`seldon.yaml` `dispatch.cadence` becomes an empty list.** The `scan_cycle` entry, its rule, `start_period` and `last_instance` are removed; the comment block above `cadence:` is replaced by four lines saying the schedule was turned off on 2026-09-18 by operator ruling, that the template at `cc_tasks/templates/scan_cycle.md` is rendered on request, and how (`seldon cadence render scan_cycle` if that command exists in the Seldon repo; otherwise the RESULT names the one-line equivalent and the Seldon Issue that asks for the command). `dispatch.enabled` stays `true`.
2. **The template's "Authored by" paragraph loses the sentence that a cycle dated by human attention is the defect**, since on-request is now the design. One sentence replaces it: a cycle runs when the operator asks for one, and its date is the day it was rendered.
3. **`tests/test_cadence_pass.py` and `tests/test_dispatch_config.py` assert the new state**: an empty cadence list is valid, nothing renders on the first Monday, and the template still renders on request with the three headers.
4. **DD-060 is not edited.** A DN-006 addendum (next free number) records the supersession for this project and cites the ruling. Documents are history.

**Write set:** `seldon.yaml`, `cc_tasks/templates/scan_cycle.md` (one sentence), the two test files, the DN-006 addendum, `seldon_events.jsonl`, the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-18_cadence_off_ADDENDUM*.md` before starting and again before §2.**

---

## 1. Decisions 1 to 4.
## 2. Gate
`make gate-fast` (`-rs`), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Failure ships nothing.
## 3. Report
RESULT `cc_tasks/2026-09-18_cadence_off_RESULT.md`: §0 the config diff; §1 how a cycle is rendered on request, as one command; §2 every premise this task file got wrong; §3 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → glob addenda → §2 → §3 → push.
