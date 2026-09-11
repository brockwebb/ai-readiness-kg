# RESULT — absence claims under a scope limitation

**Task:** `cc_tasks/2026-09-11_absence_claims_under_scope_limitation.md`. No addenda exist;
globbed before starting and again before §3, both times empty.
**Date:** 2026-09-11 UTC
**Spend:** zero model calls. **Network: loopback only** — every observation's host is
`127.0.0.1`, asserted; no cycle was re-judged.

---

## 1. The gate — §3

**PASS on every clause.** The full suite is green for the first time since the fixture task
stopped: **1,789 passed, 0 failed, 17 skipped, 12 xfailed.**

| clause | result |
|---|---|
| Eight-fixture control gate under `CURRENT`, `unknown` = 0, expectation file unchanged | **PASS** |
| Both-clocks agreement over eight fixtures, 0 differences | **PASS** — 30 s |
| Fixture replay RED under v5/v2, GREEN under v6/v3; A1 still `pass` | **PASS** |
| `CLAIM` resolves for every `CURRENT` leg | **PASS** — 17 of 17 |
| Lint green | **PASS** — and §2 is what it found |
| Second invariant reading pinned per payload | **PASS** — counts in §4 |
| Byte-identical re-derivation of all stored payloads | **PASS** — 12 of 12 |
| The seven tests the fixture task left red | **GREEN**, none edited for the fixture count |
| Socket counter loopback only | **PASS** |
| `make guards` | **PASS** — 25, the fixture now among them |
| `make gate-task` | **PASS** — 352 s |
| `make gate-full` | **PASS** — 1,200 s, EXIT=0 |
| `seldon verify` | **PASS** |
| Protected paths | **PASS** — stored payloads, prior RESULTs, cycle evidence, targets, `docs/reports/`, the eight fixtures, `params.e5_control.expected_verdicts` and `errors.CLASSES` all unchanged; **no shipped rule module edited** |

**The rules moved to meet the expectation, not the other way round.** The fixture's
`expected_verdicts` entry — `A3: error`, `B3: error` — was derived before the fixture ever ran
and is byte-identical to what the previous task registered. A test asserts that and asserts the
verdicts now match it.

## 2. §1 — the lint, and no ninth instance

`CLAIM` is `existence` or `absence` for all 17 `CURRENT` legs. The classification is read from
what each rule's `fail` branches ASSERT, not from the leg name:

| claim | legs |
|---|---|
| `existence` | A1, A4, A6, A9, A10, A11-declared, A12, D1, E5, F4 |
| `absence` | A2, A3, A5, A8, B3, D4, G1-D |

Of the absence rules, **four dereference beyond the surface page**: A3, A5, A8, B3. The lint
asks whether each routes its absence claim through a blind guard.

**No ninth instance. §1's stop did not fire, and the reason is worth the space.** The task
expected the dereferencing absence rules to be `{A3, A8, B3}` and named a fifth as a stop
condition. There is a fourth — **A5** — and it is not a defect: `rule_a5_v2.py` already does
exactly what this task generalises, and said so before there was a helper:

> *"From here the verdict is about ABSENCE, and absence is only provable over probes that
> answered. One blind candidate is enough to make it unprovable: it might have been the sitemap,
> or the sitemap that covers the product."*

**A8-v4 is compliant too**, in its own words — *"A pointer that might have resolved was never
looked at, so 'none resolves' is not established"* — with both blind branches returning `error`
and its `fail` branches reachable only when nothing was blind.

So the lint's predicate is **"routes through a blind guard"**, not "calls the new helper":
`absence_verdict` or `unobserved_error`. A lint demanding the new name would have reported two
correct rules as defective and stopped this task for nothing. A test pins the four so a fifth
appearing is the stop §1 intended.

## 3. §1 and §2 — the helper, the declaration, the two rules

**`_common.absence_verdict`** (decision 1). Three cases: the object was found among observed
candidates → the caller's existence verdict stands; none found and a candidate was BLIND →
`error`, naming the candidates; none found and nothing blind → the caller's `fail` is a real
measurement. It asks `errors.is_blind` through `unobserved`, so harness versioning still governs
— which is visible in the fixture, where A3 and B3 now move between harness-v4 and v5 exactly as
A10 does.

**Prior art, cited rather than reinvented.** The auditor's scope limitation: ISA 705 / AU-C 705
say that where sufficient appropriate evidence cannot be obtained on a material item the
response is a qualified opinion or a disclaimer, **never an adverse opinion on the item nobody
examined**. In knowledge representation it is the open-world assumption — negation as failure is
unsound over a set known to be incomplete. `error` is this harness's disclaimer, and DD-052 §6
is why it may not be `fail`.

**`RULE-A3-v6` and `RULE-B3-v3`** (decision 3), new files; v5 and v2 untouched in `REGISTRY`.
Each asks the helper ONCE, where `found` still means something — before the existence branch,
not per `fail` branch, because three branches are three chances to forget, which is how v5's gap
reads on review: *the guard was there; it never asked what the verdict claimed.*

**`blind_candidates`** joins `blind_links` and `blind_pointers` on `Finding`, omitted when unset
like both of them, because a rule that reaches a candidate by neither route had nowhere to put
the count. Re-derivation across all twelve payloads proves nothing moved.

## 4. §1 decision 4 — the counts, which are the finding

Per stored payload: `fail` verdicts from **absence**-claim rules that cite at least one blind
candidate. Evidence for a Findings-only payload is resolved through the cycle it derives from —
reading `observations_detail` alone reports 0 for all three `_rj` payloads, which is not a
measurement but the absence of one.

| payload | count | legs |
|---|---|---|
| `scan_smoke_2026-09-06` | 0 | |
| `scan_controls_2026-09-06` | 0 | |
| `scan_2026-09-07` | **1** | A3 ×1 |
| `scan_2026-09-07_controls` | 0 | |
| `scan_2026-09-07b` | **5** | A5 ×2, A3 ×3 |
| `scan_2026-09-07_rj1` | 0 | |
| `scan_2026-09-07b_rj1` | **5** | A5 ×2, A3 ×3 |
| `scan_2026-09-09` | **5** | A5 ×3, A3 ×2 |
| `scan_2026-09-10` | **9** | A3 ×9 |
| `scan_2026-09-07b_rj2` | **2** | A3 ×2 |
| `scan_2026-09-09_rj1` | **1** | A3 ×1 |
| `scan_2026-09-10_rj1` | **10** | A3 ×10 |

**The harness-v5 re-judgements did not clear this, and one of them made it larger.**
`scan_2026-09-10_rj1` carries **10** where the cycle it re-judged carries 9: under v5
`robots_disallowed` became BLIND, so more findings cite a blind candidate — and `RULE-A3-v5`
went on excluding them and answering anyway. That is the measurement decision 4 exists to
produce, and it says plainly that fixing the wholly-blind case left this one standing.

**A5's counts are v1's, not v2's.** The A5 findings in cycles 2 and 3 were made by
`RULE-A5-v1`, which predates the guard; `RULE-A5-v2` is the rule that fixed it and is the prior
art quoted in §2. Nothing here is a defect in the current A5.

All eight non-zero payloads are pinned as strict `xfail`s with their counts asserted
separately. **This task re-judged nothing.** Whether cycles 2 to 4 need a third re-judgement is
the next task's decision, and it now has the numbers to make it against.

## 5. Every premise this task got wrong

1. **Decision 2 cannot be satisfied as written.** "Every CURRENT rule module declares `CLAIM`"
   and "Zero edits to … shipped rule modules" are in the same task file and contradict each
   other: fifteen of the seventeen CURRENT modules are shipped with Findings recorded under
   them. Resolved the way `MEASURES` already resolves — the module wins where it speaks
   (`rule_a3_v6`, `rule_b3_v3` declare their own), and `CLAIM_BY_LEG` in `rules/__init__.py`
   answers for the rest. The table shrinks as modules turn over rather than going stale. **I
   edited all fifteen first and reverted them**; the zero-edits line is the harder constraint
   and it has a stated reason.
2. **The dereferencing absence rules are four, not three** (§2). A5 is the fourth and was
   already correct.
3. **`RULE-A3-v4` was never the problem** — it is not `CURRENT`. ResearchTask `969f73c6` was
   written on that premise and is superseded by this task with the correction on its face.
4. **`make()` had no home for the count.** `absence_verdict` knows about *candidates*, not links
   or pointers; the two existing fields are the special cases. Added `blind_candidates`.
5. **Two follow-ups this task had to run**, neither named in the task file and both standing
   repo procedure after shipping a rule: `framework_writeback_rules.py` + `load_framework_graph.py`
   (a spec's `rule_id` moved for two legs) and `scan_tool_map.py`. Both had tests that failed
   until they were run, which is the system working.

## 6. ResearchTasks closed

Both were `proposed`; a Desktop MCP supersede had timed out on 2026-09-11, and state was
verified before writing rather than assumed.

```
969f73c6  proposed → superseded   superseded_by 454867f8 (this task)
          "RULE-A3-v5 was already CURRENT and FAILS the fixture: the gap is not
           'rule_a3_v4 has no blind guard' but 'the guard does not ask what the
           verdict claims'."
a2981a12  proposed → superseded   superseded_by 7c6b2ba1 (the fixture task)
          "Delivered by the eighth control fixture, which fired on its first run."
```

## 7. Verification

```
logs/ac_claims.log      19 passed — helper, declarations, lint, replay      3 s   EXIT=0
logs/ac_agree.log       both clocks over eight fixtures, 0 differences     30 s   EXIT=0
logs/ac_rederive.log    12 of 12 payloads byte-identical                    6 s   EXIT=0
logs/ac_invariant.log   61 passed, 12 xfailed (4 first reading + 8 second) 37 s   EXIT=0
logs/ac_guards.log      25 passed — the fixture is in `make guards` now    16 s   EXIT=0
logs/ac2_gate_task.log  fast tier + all payloads re-derive                352 s   EXIT=0
logs/ac2_full.log       1789 passed, 17 skipped, 12 xfailed              1200 s   EXIT=0
logs/ac2_verify.log     seldon verify — All checks passed                        EXIT=0
logs/ac2_protected.log  protected paths — no shipped rule module edited          EXIT=0

new files    rules/rule_a3_v6.py, rules/rule_b3_v3.py, tests/test_absence_claims.py
changed      rules/_common.py (the helper), rules/__init__.py (generation 9,
             CLAIM_BY_LEG, claim_of), model.py (blind_candidates), Makefile
             (the fixture into guards), tests/test_invariants.py (second reading),
             tests/test_control_fixture_robots_forbids_product.py (the pin flipped
             to a replay, which is what the pin was for)
```

## 8. What the next task needs

1. **The decision decision 4 was measured for**: whether cycles 2, 3 and 4 are re-judged a third
   time under `RULE-A3-v6`/`RULE-B3-v3`. The counts are 1, 5, 5, 9 on the measured cycles and
   2, 1, 10 on the existing re-judgements; the eight non-zero payloads are pinned, so the
   decision shows up as a change to those pins either way.
2. **Cycle 1 has never been re-judged at all** and carries 1. It was excluded from the harness-v5
   re-judgement on a premise that turned out false
   (`2026-09-10_rejudge_2_3_4_RESULT.md` §7 item 4) and is still outstanding.
3. **A2, D4 and G1-D are absence rules that do not dereference today.** They are correct as they
   stand and would need the helper the moment any of them follows a link — worth a line in
   whichever task next touches one, because the lint only catches a rule that already
   dereferences.
4. **`CLAIM_BY_LEG` should empty itself.** Every entry is a leg whose current module is shipped;
   each next version declares `CLAIM` on itself and drops its row. A test asserts the table
   names only legs a cycle judges, so it cannot outlive them.
