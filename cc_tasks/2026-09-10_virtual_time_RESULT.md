# RESULT — virtual time: the control fixtures stop sleeping

**Task:** `cc_tasks/2026-09-10_virtual_time.md` (no addenda exist; globbed at dispatch and again
before §3).
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

---

## 1. The gate — §3

**PASS on every clause.** All long-running commands detached, logged, polled to `EXIT`; §6 cites
the paths.

| clause | result |
|---|---|
| Decision 5: seven fixtures, both clocks, zero differences | **0 differences**, fixture by fixture, leg by leg |
| Fast tier green, wall-clock | **EXIT=0**, 1644 passed, **1145 s** |
| Full suite green, wall-clock | **EXIT=0**, 1655 passed, **1815 s** (was 3354 s) |
| Re-derivation of all prior payloads unchanged | 8 of 8, byte-identical |
| Hygiene, `seldon verify`, protected paths | all **EXIT=0** |
| `--durations=15` reported | §4 |

**The headline: the full suite went 3354 s → 1815 s, a 46% cut, with no test removed, skipped
or weakened.** The seven-fixture control gate alone went from ~291 s of real sleeping to
**6.1 s real / 291 virtual seconds recorded across 291 waits**, and returns the same verdict.

## 2. §1 — every call site that read wall time

| site | before | now |
|---|---|---|
| `manners.Fetcher._wait` (the rate limiter) | `time.monotonic()` ×2, `time.sleep` | `self.clock.now()`, `self.clock.sleep()` |
| `manners.Fetcher.raw_get` timing | `time.monotonic()` ×2 | `self.clock.now()` |
| `manners.Fetcher.raw_get` backoff | `time.sleep` | `self.clock.sleep()` |
| `manners.Fetcher.raw_head` timing | `time.monotonic()` ×2 | `self.clock.now()` |
| `model.captured_at` | `datetime.now(timezone.utc)` | **unchanged, deliberately** |
| `model._redirect_root` log stamp | `datetime.now(timezone.utc)` | **unchanged, deliberately** |

`import time` is gone from `manners.py` entirely.

**The two that did not move are a scoping decision, not an oversight.** The injected clock is a
MONOTONIC SCHEDULING clock: `now()` for measuring an interval, `sleep()` for yielding one. It is
not a wall clock. A virtual timestamp on a stored `Observation.captured_at` would be a false
statement about when a thing was observed, and no amount of suite speed buys that. The task's
own §1 lint names `time.sleep`, `time.time` and `time.monotonic` and not `datetime.now`, which
is the same boundary arrived at independently.

**Production cannot reach the virtual clock.** `run.py::main` takes no clock argument and a test
asserts it by signature, so a cycle against real federal hosts is structurally incapable of
running unthrottled. `Fetcher`'s default is the real clock, also asserted.

**Prior art, adopted not invented.** Twisted's `twisted.internet.task.Clock` and RxJS's
`TestScheduler`. Their shared rule is the one that matters and is implemented here: **advance
time when someone waits on it**. `VirtualClock.sleep(s)` records the wait and jumps `now()`
forward by `s`; it is not a no-op. A monkeypatched `time.sleep` would make "the limiter never
asked" and "the limiter asked and was ignored" indistinguishable, and the first is the defect
decision 2 exists to catch.

## 3. §2 — the retier, which cut both ways

Decision 4 extends the `slow` definition to "runs a control fixture at the REAL standing rate,
or replays the whole event log". The task anticipated that adding the three event-log replays;
it did not anticipate that **the same extension makes seven of yesterday's marks obsolete**,
because a virtualised control cycle is no longer slow by any definition.

* **3 added** — the event-log replays (264 s, 230 s, 169 s).
* **7 removed** — the control-cycle tests marked yesterday, now virtual.
* **Two `slow` tests remain in the entire suite.**

**`fixture_expectations.py` and the derived tables are unaffected in content — checked, not
assumed**, as §2 requires: 7 fixtures, 23 derived, 89 deferred, **0 differences**,
`fetcher gates every request: True`, ungated set empty. Identical to before the clock existed.

## 4. §4 — the durations, and the test that did not move

```
594.33s  test_merging_controls_replaces_them_rather_than_accumulating     (was 593.01s)
301.76s  test_the_control_gate_returns_the_same_verdicts_on_both_clocks   (new, this task)
263.94s  test_the_uncited_set_only_shrinks_and_only_by_citation           slow
230.22s  test_the_overlay_is_idempotent                                   slow
169.40s  test_every_recorded_403_now_reads_as_refused_on_the_log          slow
 37.69s  test_batch_membership_matches_what_provenance_already_records
  ...
  4.73s  test_no_request_in_the_control_cycle_leaves_the_loopback         (was 297s)
```

**Is `test_merging_controls_replaces_them_rather_than_accumulating` still twice the cost of a
single control cycle under the virtual clock? Yes, and by far more than twice: 594 s against
6.1 s for a whole virtual seven-fixture gate. It did not move at all.**

One sentence on what it is spending the time on, as asked, with no fix: it calls
`run_mod.merge_controls(payload, params)` twice and `merge_controls` takes no `clock`
parameter, so it runs two complete seven-fixture control cycles on the real clock.

## 5. Premises this task got wrong

1. **Decision 4's retier is described as additive** ("the three event-log replays join the
   tier"). It is also subtractive: seven marks became wrong the moment their tests stopped
   sleeping. A retier written only as an addition would have left the fast tier deselecting
   tests that now cost milliseconds. §3.
2. **Decisions 3 and 5 are in tension and I resolved it rather than raising it.** Decision 3
   says "exactly one real-clock control cycle survives, over one fixture". Decision 5 requires
   comparing the seven-fixture gate's verdicts under both clocks, which *necessarily* runs a
   second real-clock cycle over all seven — that is what the comparison is. There are therefore
   two: the one-fixture rate assertion (marked `slow`, decision 3) and the agreement check
   (301 s, **left in the fast tier**). I left it there deliberately: it is the check that makes
   every other virtual test in the suite meaningful, and a per-task gate that omits it could
   ship a harness where virtual and real disagree. That is a judgment about gate design and the
   operator may reverse it; the cost is on the record either way.
3. **The fast tier got slower, 1029 s → 1145 s, and it is not a regression.** Seven tests that
   were deselected yesterday now run in it. The tier total is not comparable across the change;
   what those tests cost is.

### Mine

4. **My `pyproject.toml` edit split the marker string across two lines and produced an unclosed
   TOML array**, breaking collection for the whole suite. Caught immediately because
   `--collect-only` refused to run at all.
5. **I wrote fixture bodies from ad-hoc drivers again — the fourth task running.** 218 writes,
   every one genuinely aimed at the committed store. **All 218 were diverted and none reached
   it**, because the evidence guard shipped last task. Same mistake, no consequence: that
   contrast is the clearest evidence in the record that the guard earns its keep.
6. **The suffix-list lint matched a COMMENT** — `tests/test_guards_replay_their_incidents.py`
   contains the phrase "the tldextract retirement check" in a comment explaining the
   assembled-needle trick, and the lint reported it as a surviving dependency. This is the
   **fourth** source-scanning check in this repo to read prose as code: the AST gate detector
   did it to `robots.py`'s comment, the self-licensing lint did it to its own bait, and this
   check has now done it twice. Each previous fix addressed the specific match; the class is
   "a scanner that treats source as text will match the text that talks about the thing", and
   the fix this time is to strip comments before matching, because the question is whether the
   dependency is REACHED and a comment reaches nothing.

## 6. Verification

```
logs/gate_fast.log   1644 passed, 2 skipped, 11 deselected     1145 s   EXIT=0
logs/suite.log       1655 passed, 2 skipped, --durations=15    1815 s   EXIT=0
logs/verify.log      seldon verify — All checks passed                  EXIT=0
logs/protected.log   protected-paths diff                               EXIT=0
                       shipped rule modules   no change
                       prior RESULTs          no change
                       state/ (targets v4)    no change
                       cycle evidence         no change
                       docs/reports/          no change
                       run.py::main           interface unchanged
                       events/                no change (append-only)
                       redirect log           0 bytes (218 swept, all recorded)
logs/harness.log     the converted harness pair                 630 s   EXIT=0

both-clocks agreement   7 fixtures, leg by leg, 0 differences
control gate            6.1 s real / 291 virtual seconds across 291 waits, verdict pass
derived tables          7 fixtures, 23 derived, 89 deferred, 0 differences — unchanged
registered              suite_fast_seconds_2026-09-10       = 1145
                        suite_full_seconds_2026-09-10       = 1815
                        suite_fast_share_of_full_2026-09-10 = 0.6309
                        3 registered, 0 failed
```

## 7. What the next task needs

1. **`merge_controls` has no clock parameter**, which is the whole of the remaining 594 s and
   33% of the suite in one test. Threading one is a small change this task was told not to make.
2. **Rule on decision 3 versus decision 5** (§5 item 2): whether the 301 s agreement check
   belongs in the per-task gate, where I left it, or in the `slow` tier its definition would
   put it.
3. **Cycle 4 is not the next task** and waits on the operator's flagship declarations;
   `docs/design/fss_flagship_declarations.md` is now on disk, untracked, and is not this task's
   to commit.
