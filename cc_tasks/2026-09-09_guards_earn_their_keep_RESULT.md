# RESULT — guards earn their keep: incident replays, no self-licensing, suite tiers

**Task:** `cc_tasks/2026-09-09_guards_earn_their_keep.md` (no addenda exist; globbed at dispatch
and again before §3).
**Date:** 2026-09-09 UTC
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

---

## 1. The gate — §3

**PASS on every clause.** All long-running commands were run detached, logged, and polled to
`EXIT`; §6 cites the paths.

| clause | result |
|---|---|
| Fast tier green, wall-clock reported | **EXIT=0**, 1635 passed, 14 deselected, **1029 s** |
| Full suite green under the long-running protocol, wall-clock reported | **EXIT=0**, 1649 passed, 2 skipped, **3354 s** |
| Every guard listed with its replay test and red/green evidence | 4 guards, §2 |
| Self-licensing lint fails on a planted driver, passes after removal | both asserted |
| Redirect-log hygiene fails on a planted line, passes after the sweep | both asserted |
| `seldon verify` | **EXIT=0**, all checks passed |
| Protected paths | **EXIT=0**, every fence intact |

## 2. The four guards, each against its own incident

Decision 1. Every one is a pair: **red** against the pre-guard code path or a faithful stub,
**green** against what ships. `tests/test_guards_replay_their_incidents.py`, 10 tests.

| guard | incident | red against | green |
|---|---|---|---|
| blind-probe lint | `RULE-A5-v2` shipped without a guard (`2026-09-09_manners_closeout_RESULT.md` §0) | a stub rule using only `only_errors` | every shipped generation-4+ rule |
| fetcher gate (robots-first) | the two apex sitemap GETs (`2026-09-09_report_draft_RESULT.md` §3) | the shipped fetcher with `_gate` neutralised, on `sitemap_on_sibling` | sibling receives `/robots.txt` first |
| evidence-store guard | 29 + 18 driver writes, **and the guard's own wrong condition** (`..._manners_closeout_RESULT.md` §5 item 8 and §4 item 3) | a content-addressed writer with no licence check | redirected, logged, and a repointed root honoured |
| AST gate detector | both wrong predecessors (`2026-09-09_closeout_and_manners_RESULT.md` §5 item 9) | text search fooled by `robots.py`'s comment; joined parse fooled by real un-newlined segments | correct on both |

**No guard is unreplayed.** The task asks for any that are to be listed as such; there are none.

**The evidence-guard replay carries three cases, not two**, because that guard failed in both
directions. A pre-guard write lands in the committed store; an unlicensed write is redirected
and logged; **a write whose root was deliberately repointed is honoured**. The third is the one
the first implementation got wrong, and a replay with only the first two would have passed
against it.

## 3. What decision 3 found: 1,891 redirects, none of them real

The redirect log was non-empty at gate time, which is exactly what decision 3 exists to
surface. It held **1,891 entries, and not one was aimed at the committed store.** Every one was
a legitimate pytest write to a `tmp_path` root, redirected by the evidence guard's pre-fix
condition.

That is the measure of the defect reported one task ago as `..._manners_closeout_RESULT.md` §4
item 3: the guard was firing on 1,891 correct writes and zero incorrect ones. It was reported
then as "one failure in 1639"; the true blast radius was three orders of magnitude larger and
invisible because the redirect was silent by design.

Swept through a new `--clear-redirects` mode on `scripts/quarantine_fixture_evidence.py`, which
summarises the log into `reason.txt` — count, span, writers, and how many were aimed at the
committed store — **before** truncating. Clearing it silently would have deleted the only
record of who wrote litter, which is the finding.

## 4. Decision 4: the split, measured, then made to work

**Implemented as literally specified, the split saved 18%.** `slow` on the older
re-derivations, everything else fast: **2762 s** fast against **3373 s** full. The per-task gate
was still 46 minutes, which is not the gate decision 4 is written around.

`--durations=25`, folded into the full run that had to happen anyway, said why:

```
593s  test_merging_controls_replaces_them_rather_than_accumulating
298s  test_findings_re_derive_byte_identically_from_stored_observations
297s  test_no_request_in_the_control_cycle_leaves_the_loopback        <- the only one marked
297s  test_the_cycles_own_validity_verdict_is_on_the_record
296s  test_the_re_derivation_gate_covers_the_control_findings_too
296s  test_the_control_gate_passes_on_all_four_fixtures
296s  test_the_control_gate_passes_on_all_five_fixtures
284s  test_the_uncited_set_only_shrinks_and_only_by_citation
229s  test_the_overlay_is_idempotent
169s  test_every_recorded_403_now_reads_as_refused_on_the_log
```

**Ten tests are 3055 s of 3370 s — 91% of the suite — and one carried the marker.** The
criterion was right; its application covered one test in ten.

Five more are marked now, and the distinction matters: `pyproject.toml` defines `slow` as "runs
the loopback control fixtures at the standing 1 req/s rate", and each of the five calls
`run_controls()` or `_fresh_control_cycle()`, **verified by call path rather than inferred from
duration**. Making a marker true of what it already claims to mark is applying the definition.
Re-marking merely-slow tests until the number looked right would have been moving a threshold.

**Result: fast tier 2762 s → 1029 s, a 63% cut, at 31% of the full suite. Nothing was removed
or weakened; the full suite is unchanged at 3354 s against 3373 s.**

**Three heavyweights were deliberately left unmarked** — `..._uncited_set_only_shrinks...`
(284 s), `..._overlay_is_idempotent` (229 s), `..._403_now_reads_as_refused...` (169 s). They
are event-log replays: slow for a reason the marker does not name. Marking them would buy about
eleven more minutes and would require extending the marker's definition, which is the
operator's call. Recommended in §5 with the costs attached.

## 5. Premises this task got wrong

1. **Decision 4's "`@pytest.mark.slow` on ... Lighthouse runs".** **No standalone Lighthouse
   test exists.** `collectors/lighthouse.py` runs only inside the control-cycle tests, which
   were already in scope. Nothing to mark; recorded rather than invented.
2. **Decision 4's premise that marking the old re-derivations and the control cycles separates
   a quick tier from a slow one.** False as specified: it separated 18%. §4.

### Mine

3. **I told the operator the suite had "roughly doubled to two hours" and built a finding on
   it.** It had not: 3357 s against 3338 s. I read pytest's progress percentage as linear in
   wall clock and then reasoned from that error to a "the rate limiter throttles loopback"
   conclusion with nothing behind it.
4. **I then did it again, in the other direction**, reporting the suite as apparently stalled
   for seven minutes. My tool calls run far faster than wall clock; the 90-second sampler I
   started to check for a hang had not yet returned, which proved less than 90 seconds had
   passed. Settled properly with a stack sample: the process was executing bytecode, not
   blocked on a syscall, and the "stall" was one 593-second test emitting nothing under `-q`.
   **Twice in one session I inferred a timing fact from something that was not measuring
   time.** The fix that stuck was a watcher that prints `STALLED` with a byte delta and CPU on
   a real five-minute interval.
5. **The self-licensing lint matched its own test file's string literal**, and its path
   handling raised on `tmp_path`. The third time in this lineage a source-scanning check has
   caught itself: the suffix-list retirement check needed the same assembled-needle trick, and
   I did not carry the lesson across. Both fixed by assembling the token from parts.

## 6. Verification

Every long-running command detached, logged, polled to `EXIT` (CLAUDE.md, "Long-running
commands"). `logs/` is gitignored; the RESULT quotes it.

```
logs/gate_fast.log     1635 passed, 2 skipped, 14 deselected   1029 s   EXIT=0
logs/suite.log         1649 passed, 2 skipped                  3354 s   EXIT=0
logs/verify.log        seldon verify — All checks passed                EXIT=0
logs/protected.log     protected-paths diff                             EXIT=0
                         shipped rule modules   no change
                         prior RESULTs          no change
                         state/ (targets v4)    no change
                         cycle evidence         no change
                         docs/reports/          no change
                         events/                no change (append-only)
                         redirect log           0 bytes

guards replay suite    10 passed  (tests/test_guards_replay_their_incidents.py)
registered             suite_fast_seconds_2026-09-09      = 1029
                       suite_full_seconds_2026-09-09      = 3354
                       suite_fast_share_of_full_2026-09-09 = 0.3068
                       3 registered, 0 failed
```

The registrar refuses any log that does not carry `EXIT=0`: a wall-clock from a failed run
measures how long a failure took, and registering it as the cost of a tier would be false.

## 7. What the next task needs

1. **Decide whether the three event-log replays join the `slow` tier.** 682 s between them,
   which would take the fast tier from 1029 s to roughly 350 s. It needs the marker's
   definition extended from "runs the loopback control fixtures" to include "replays the whole
   event log", and that is a decision, not an application. §4.
2. **`test_merging_controls_replaces_them_rather_than_accumulating` is 593 s on its own**, 18%
   of the suite in one test. Nothing here investigated why it is twice the cost of the other
   control cycles.
3. **`params.manners.same_host_only` is still queued** (DD-063 §5 item 2), untouched here as
   decision 5 directs.
4. **Cycle 4 is not the next task** and waits on the operator's flagship declarations.
