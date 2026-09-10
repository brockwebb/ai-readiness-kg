# CC Task — virtual time: the control fixtures stop sleeping

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-09_guards_earn_their_keep_RESULT.md` (gate PASS, `fba8efb9` completed, `suite_fast_seconds_2026-09-09 = 1029`, `suite_full_seconds_2026-09-09 = 3354`). That RESULT's §4 durations table is this task's premise: ten tests are 91% of the suite and each is a loopback control cycle waiting on the standing 1 req/s limiter.
**Fulfils:** its own ResearchTask (`seldon cc register`). Part of `520ec74b` (cycle-4 maintenance). Cycle 4 is not this task; it waits on the operator's flagship declarations.
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

**Decisions taken here (operator overrides later):**
1. **The clock is injected, not patched.** The rate limiter, the fetcher's timeouts, and anything else in `assessment/harness/scan/` that sleeps or reads wall time take a `clock` object (`now()`, `sleep(s)`) with the real clock as the default. Production code paths never see the virtual one; `run.py::main` does not accept a clock argument at all. Prior art: virtual-time scheduling as in Twisted `task.Clock` and RxJS `TestScheduler`; the pattern is "advance time when someone waits on it," not "make sleep a no-op." Monkeypatching `time.sleep` globally is refused because it hides whether the limiter asked to wait at all.
2. **The limiter's behaviour is asserted, not skipped.** Under the virtual clock, a control cycle records every wait the limiter scheduled; a test asserts that consecutive requests to one netloc were spaced at least the standing interval apart in virtual time. That is the property the real-clock sleep was implicitly guaranteeing, made explicit.
3. **Exactly one real-clock control cycle survives**, in the `slow` tier, over one fixture, asserting real wall-clock spacing at the standing rate. Everything else runs virtual.
4. **The `slow` marker's definition is extended** in `pyproject.toml` to: "runs a control fixture at the real standing rate, or replays the whole event log." The three event-log replays named in the prior RESULT §4 join the tier. No merely-slow test is marked for being slow.
5. **Virtual and real must agree.** The seven-fixture control gate's verdicts under the virtual clock equal the verdicts under the real clock, fixture by fixture, leg by leg. Any difference is a stop and a finding (it would mean a rule reads wall time).

**Zero edits to:** shipped rule modules, registered Result values, prior RESULTs, cycle evidence, the report, targets v4, `run.py::main`'s interface.

**Immutable once written. Glob `2026-09-10_virtual_time_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Inject
Decision 1. List in the RESULT every call site that read wall time or slept before this task, and what each takes now. A source-level test asserts no bare `time.sleep` or `time.time`/`monotonic` remains under `assessment/harness/scan/` outside the real-clock implementation (assemble the needle from parts; the last three source checks matched their own test files).

## 2. Retier
Decisions 2 to 4. `fixture_expectations.py` and the derived tables are unaffected in content; say so after checking rather than assuming.

## 3. Gate (the one gate of this task)
Decision 5's agreement check, all seven fixtures, both clocks, zero differences. Fast tier green with wall-clock; full suite green under the long-running protocol with wall-clock; byte-identical re-derivation of all prior payloads unchanged; hygiene, `seldon verify`, protected paths. Report `--durations=15` from the full run.
**Failure: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-10_virtual_time_RESULT.md`, written after EXIT=0 logs exist. Register `suite_fast_seconds_2026-09-10`, `suite_full_seconds_2026-09-10`, `suite_fast_share_of_full_2026-09-10`. State whether `test_merging_controls_replaces_them_rather_than_accumulating` is still twice the cost of a single control cycle under the virtual clock; if it is, name what it is spending the time on, one sentence, no fix. Every premise this task got wrong. `seldon cc complete`, commit, push. Final message states whether the RESULT exists and the push succeeded.

**SEQUENCING:** §1 → §2 → glob addenda → §3 (hard stop; detached, logged, polled) → §4 → push.
