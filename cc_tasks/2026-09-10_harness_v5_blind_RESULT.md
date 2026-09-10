# RESULT — harness-v5: forbidden to look is blind; scope is not

**Task:** `cc_tasks/2026-09-10_harness_v5_blind.md`. No addenda exist; globbed at dispatch and
again before §3, both times empty.
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

---

## 1. The gate — §3

**PASS on every clause.**

| clause | result |
|---|---|
| Seven-fixture control gate under `CURRENT` (harness-v5, A12-v2), `unknown` = 0 | **PASS** — 17 checks, 8 s |
| Both-clocks agreement, 0 differences | **PASS** — 27 s |
| Byte-identical re-derivation of all nine payloads **under their own harness versions** | **PASS** — 9 of 9 |
| The invariant test: history pinned under v4, 0 under v5 | **PASS** — 33 passed, 4 strict xfails |
| A10 replay: RED under v4 / GREEN under v5 | **PASS** |
| Fast tier | **PASS** — 1,707 passed, 314 s |
| Full suite | **PASS** — 1,719 passed, 17 skipped, 4 xfailed, 1,174 s |
| `seldon verify` | **PASS** |
| Protected paths | **PASS** — no prior payload, RESULT, evidence, report or target touched; no shipped rule module edited; `params.yaml` gained exactly `harness_version: 5` |

**The suite is green for the first time since cycle 4's gate stopped**, and the three failures
that stop was leaving behind are gone: the cycle-shaped test folded into the invariant, and the
figure gate now skips with a reason instead of erroring on a cycle nobody reported.

## 2. §1 decision 1 — the three kinds

`OBSERVED` / `BLIND` / `SCOPE`, named in `errors.py` and nowhere else. The full statement is
**DD-064**; the short version is that harness-v4 drew the line at *declared versus absent* and
the line belongs at *inside the product versus outside it*.

| class | v4 | v5 |
|---|---|---|
| `robots_disallowed` | SCOPE | **BLIND** |
| `off_host`, `sitemap_off_site` | SCOPE | SCOPE |
| `refused`, `dns`, `timeout`, `connection_reset`, `http_5xx`, `parse_error`, `collector_unavailable`, `unknown` | BLIND | BLIND |
| `redirect_loop` | — | **BLIND** (new, decision 4) |
| `None`, `http_4xx` | OBSERVED | OBSERVED |

`NOT_FETCHED` is retired as a class name and survives as the `requested` attribute
(`NOT_REQUESTED` derives it). Four readers moved: `tests/test_scan_run_4.py`,
`tests/test_manners_robots_first.py`, `tests/test_scan_run_2.py`,
`scripts/register_manners_results.py`. **No rule reads `errors.CLASSES` any more** —
`_common.unobserved` asks `errors.is_blind(cls, harness)` and `scan_report` asks `note_for` and
`kind_of`.

## 3. §1 decision 2 — re-derivation did NOT bind the harness version, and now does

**It had to be fixed first, exactly as the task anticipated.** Re-derivation bound the *rule*
version per Finding — `wanted = {f["rule_id"] …}`, judged through `REGISTRY` — but every rule
version, v1 to v7, calls the same `_common.unobserved`, which read a module-level tuple computed
at import. One constant cannot be v4 for one payload and v5 for the next, so changing the class
table would have re-scored nine stored payloads under a reading that did not exist when they
were measured.

The fix is three lines and no payload edited:

* `params.yaml` binds `harness_version: 5`;
* a params set that binds none IS a v4 set (`errors.HARNESS_DEFAULT`), which is what every
  stored payload's recovered params look like;
* `rederive` recovers each payload's own params **from git by hash**, so the version follows the
  payload rather than the clock.

`run.py` and `rederive.py` now stamp `harness_version` on the payloads they write, so the next
cycle's version is on its face rather than inferred from what params.yaml said later.

**9 of 9 re-derive byte-identically**, including cycle 4 at 852 Findings.

## 4. §1 decision 3 — A12 reads the refusal, and says so on its own face

`RULE-A12-v2`. v1's branch logic, with the two `error` conditions restated: v1 asked *is the
status None*, v2 asks *did a response arrive*. A 403 to `/robots.txt` is an observation of
enforcement and yields a verdict; a DNS failure or a reset yields `error`.

**The mechanism that keeps decision 5 exemption-free is `MEASURES = "host"`** — a declaration on
the module, inherited by leg so `RULE-A12-v1` carries it too (the subject belongs to the
indicator, not to the rule version). Three readers use it: the invariant test, the blind-guard
lint in `test_scan_harness_v4.py`, and its replay in the guards suite. A future host-level rule
declares the same thing and needs no edit anywhere else. A test asserts A12 is the only leg that
declares it, so the declaration cannot quietly become a list.

## 5. §1 decision 4 — the A10 incident, replayed

`test_a10_returned_pass_from_two_probes_that_were_never_issued` reads cycle 4's actual Finding
off the payload: `pass`, `RULE-A10-v3`, both cited Observations `robots_disallowed`. RED under
v4 (`is_blind(…, 4)` is False for every one of them), GREEN under v5 (True for every one).
**The rule module is untouched** — one entry in `errors.CLASSES` moved, and a defect that
appeared in seven disguises across A1, A3, A6, A8, A10, B3 and G1-D was one wrong answer to one
question asked in one place.

`redirect_loop` joined the closed set and `TooManyRedirects` maps to it. That renamed three
stored observations, which were corrected **by overlay, never by edit**: the
`recorded_error` pass now stands at 96 (93 from harness-v3 plus these 3), all Census A10 probes.

## 6. §2 decisions 5 and 6

**The invariant is a test now** — `tests/test_invariants.py`, parametrised over all nine
payloads, three readings each:

| payload | own harness | under v5 (product) | under v5 (all rules) |
|---|---|---|---|
| `scan_smoke_2026-09-06`, `scan_controls_2026-09-06`, `scan_2026-09-07_controls` | 0 | 0 | 0 |
| `scan_2026-09-07` | 0 | **6** | **9** |
| `scan_2026-09-07b` | 0 | **6** | **9** |
| `scan_2026-09-07_rj1`, `scan_2026-09-07b_rj1` | 0 | 0 | 0 |
| `scan_2026-09-09` | 0 | **6** | **9** |
| `scan_2026-09-10` | 0 | **11** | **14** |

The v5 column's non-zero rows are strict `xfail`s with their counts asserted separately, so the
history is pinned rather than hidden and a re-judgement cannot move it silently.

**The figure gate skips with a reason** when `params.cycle.name` has no matrix — both in
`matrix()` and in the `figures` fixture, because a fixture that raises reports 8 collection
errors rather than 8 skips. A gate that cannot tell "the figures are wrong" from "there are no
figures yet" trains its reader to ignore it.

The failing test CC left in `test_scan_run_4.py` is removed from there, with a note in its place
saying what replaced it and why a cycle-shaped test could only ever catch the instance in front
of it.

## 7. Every premise this task got wrong

1. **"Historical counts (9, 9, 14)" is one of three answers, not the answer.** Those are the
   counts *across all rules* under v5's reading, of the three most recent payloads. Scoped to
   product verdicts they are 6, 6 and 11 — the difference is A12's three per cycle, whose
   subject is the refusal. And **`scan_2026-09-07` carries the same 6 and was not in the task's
   list at all**: `scan_run_4`'s RESULT looked at three payloads, this looks at nine. All three
   counts are pinned.
2. **§1 expected control-table rows to move and none did.** The derivation reports **23 derived,
   89 deferred, 0 differences** under harness-v5. The reason is a gap rather than a reassurance:
   **no control fixture forbids an in-product probe in its robots.txt**, so the seven-fixture set
   never exercises the class that moved. The gate that would have caught cycle 4's A10 defect
   before it shipped does not exist yet, and §8 item 1 is that fixture.
3. **Decision 2 asked whether re-derivation binds the harness version per payload.** It did not,
   and the RESULT was asked to say whether it had to be fixed first: **it did** (§3).
4. **A12-v2 had to be in two lists.** `CURRENT` is built from the generations and then updated
   from `CANDIDATE_RULES`, so a new version of a candidate rule that appears only in its
   generation is silently overwritten by the old one. Found by the registry reporting
   `CURRENT["A12"] == "RULE-A12-v1"` after V8 shipped.
5. **Shipping a rule has two follow-ups this task had to run**, neither named in the task file:
   the framework write-back (`framework_writeback_rules.py`, then `load_framework_graph.py`, per
   CLAUDE.md's standing rule) and `scan_tool_map.py`. Both had tests that failed until they were
   run, which is the system working.

## 8. Verification

```
logs/hv5_agree.log      both clocks, 7 fixtures, 0 differences       27 s   EXIT=0
logs/hv5_control.log    control gate + derived tables, 17 checks      8 s   EXIT=0
logs/hv5_rederive.log   9 of 9 payloads byte-identical                4 s   EXIT=0
logs/hv5_invariant.log  33 passed, 4 xfailed (the pinned history)    17 s   EXIT=0
logs/hv5_fast.log       1707 passed, 17 skipped, 4 xfailed          314 s   EXIT=0
logs/hv5_full.log       1719 passed, 17 skipped, 4 xfailed         1174 s   EXIT=0
logs/hv5_verify.log     seldon verify — All checks passed                   EXIT=0
logs/hv5_protected.log  protected-paths diff                                EXIT=0
                          prior payloads          no change
                          prior RESULTs           no change
                          cycle evidence          no change
                          report prose and PDF    no change
                          targets                 no change
                          shipped rule modules    none edited; rule_a12_v2.py is new
                          params.yaml             harness_version: 5, and nothing else
                          events                  +4 / -0 (3 overlays, 1 framework)

control tables   23 derived, 89 deferred, 0 differences — no row moved (§7 item 2)
new tests        tests/test_invariants.py (37 cases), 2 guard replays, 1 registry audit
DD-064           written: the three kinds, and harness versioning as the answer to
                 "how does a judgement-layer fix coexist with a bind-once record"
```

## 9. What the next task needs

1. **A control fixture whose robots.txt forbids an in-product probe.** The seven-fixture set has
   no such mode, which is why 0 rows moved and why cycle 4's A10 defect reached a federal host
   before anything noticed. It is the one gate that would have caught this class at the source.
2. **`2026-09-10_rejudge_2_3_4.md` is next** and now has what it needs: four payloads carrying
   6, 6, 6 and 11 product verdicts that rest on nothing, pinned so the re-judgement can be
   checked against them, and a harness version that lets a v5 re-judgement coexist with the v4
   originals rather than overwriting their meaning.
3. **`rule_a3_v4`'s blind-handling gap is still a pinned exemption** in the lint, by content
   hash. Harness-v5 does not close it: the module never consults a guard at all, and the fix is
   a new version, not an edit.
