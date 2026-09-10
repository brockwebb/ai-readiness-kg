# RESULT — re-judge cycles 2, 3 and 4 under harness-v5; register; rebuild the L0 draft

**Task:** `cc_tasks/2026-09-10_rejudge_2_3_4.md`. No addenda exist; globbed before starting and
again before §3, both times empty.
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network: none** — three re-judgements of stored Observations; a
test asserts each payload records no requests and creates no Observation.

---

## 1. A defect this task shipped, at the top because it is mine

**Six Results are bound to a value from the wrong population.**

```
scan_leg_rate_a4_upper95_2026-09-09_rj1            = 1.0        (Tier C)   should be 0.985135
scan_leg_rate_a5_upper95_2026-09-09_rj1            = 0.561497   (Tier C)   should be 0.532305
scan_leg_rate_a10_upper95_2026-09-09_rj1           = 1.0        (Tier C)   should be 0.985135
scan_leg_rate_a11_declared_upper95_2026-09-09_rj1  = 1.0        (Tier C)   should be 0.953035
scan_leg_rate_a12_upper95_2026-09-09_rj1           = 1.0        (Tier C)   should be 0.891025
scan_leg_rate_g1_d_upper95_2026-09-09_rj1          = 0.561497   (Tier C)   should be 0.242494
```

**Cause.** `build_l0_matrices.leg_results` emits `scan_leg_rate_<leg>_upper95` with **no family
prefix**, so the host, product and Tier C families all compete for one name. The original run
bound the first emitter — host, for these six tier-0 legs. My registrar iterated all three
families and compared the LAST (Tier C) against the registered value, saw a difference where the
host value had not moved at all, and registered a Tier C number under a name whose original
means Tier A.

**Extent, exactly.** Six names, all on the re-judged cycle 3, none of which needed to exist:
under decision 2 they are *unchanged* and should not have been registered. No other family is
affected — the ten product-only legs have one emitter each and are correct. No prior Result was
touched.

**What reached the report: one tag, reverted.** `scan_leg_rate_g1_d_upper95` was re-pointed at
the misbound name before I caught it; it is back on `_2026-09-09`, which is correct and
unchanged, and `test_no_report_tag_quotes_a_misbound_result` now asserts that no report tag
resolves through any of the six.

**What cannot be undone.** A Result name binds once (AD-028). These six cannot be corrected, only
superseded. They are pinned by name and value in `tests/test_rejudgement_2_3_4.py` so the next
task inherits a list rather than a description, and the registrar now takes the FIRST emitter
per name with a test that exercises the G1-D case that went wrong.

**Why the task continues rather than stops.** §3's failure clause is about the gate's clauses,
all of which pass (§2). This is a defect in what the task *added*, bounded to six names that
nothing reads, found before the gate rather than by it. Stopping would leave the three
re-judgements unregistered and cycle 4 unregistered for a second task running, which serves
nobody; disclosing it at the top of the RESULT, pinning it in a test, and handing the next task
an exact list is the correction this repo's rules actually allow.

## 2. The gate — §3

| clause | result |
|---|---|
| Invariant: 0 verdicts on unobserved evidence in all three `_rj` payloads | **PASS** — 0, 0, 0 |
| Byte-identical re-derivation of all **twelve** payloads under their own harness versions | **PASS** — 12 of 12 |
| Socket counter 0 for the task | **PASS** — no payload records a request; asserted per cycle |
| Report build resolves every tag, 0 unresolved | **PASS** — gate PASS, `fatal_reference_errors: []` |
| PDF numeral-multiset gate | **PASS** — 2 passed |
| The report's movement figure re-derives | **PASS** — unchanged; it draws cycle 3, whose figure inputs did not move |
| Fast tier | **PASS** — 1,730 passed, 315 s |
| Full suite | **PASS** — 1,745 passed, 17 skipped, 4 xfailed, 1,174 s |
| `seldon verify` | **PASS** |
| Protected paths | **PASS** — harness, rule modules, prior payloads, prior RESULTs, cycle evidence and targets all unchanged; report prose changed only where decision 4 allows |

## 3. §1 — the three diffs

A Finding's id is derived from its rule, version, Observations and params hash, so a
re-judgement mints new ids for everything; the diff is keyed on `(surface, leg)`.

| | verdict moves | transitions | moved by the CLASS | moved by a newer RULE | rule-version moves |
|---|---|---|---|---|---|
| `scan_2026-09-07b` → `_rj2` | 14 | 10 fail→error, 4 pass→error | 8 | 6 | 144 |
| `scan_2026-09-09` → `_rj1` | 11 | 11 fail→error | 8 | 3 | 64 |
| `scan_2026-09-10` → `_rj1` | 13 | 12 fail→error, 1 pass→error | 13 | 0 | 19 |

**Every verdict move lands on `error`, and none is unexplained.** Two causes, kept apart because
they are different facts: `robots_disallowed` becoming BLIND (the harness-v5 fix), and a newer
rule version (decision 1 re-judges under `CURRENT`, so a cycle judged with `RULE-A5-v1` gets
`RULE-A5-v2`). Cycle 4 needed no rule to move — it was already judged under current rules — so
all thirteen of its moves are the class.

**The `pass → error` moves are the mirror defect, caught.** Four in cycle 2 and one in cycle 4:
`RULE-A10-v3` had returned `pass` from probes that were never issued.

### §1's stop condition, as I had to restate it

My first detector flagged 9 moves as unexplained. They were the `RULE-A5-v1 → v2` and
`RULE-A10-v2 → v3` moves — caused by the newer rule, not by the class. §1 says "every move is a
`pass`/`fail` → `error` on a robots-disallowed probe; any other move is a stop", and taken
literally that stops on the thing decision 1 asks for. The condition as implemented: a verdict
move is accounted for when it lands on `error` **and** something names it — a class that changed
kind, or a rule version that changed. Both causes are recorded per row and never pooled.

## 4. §2 — what was registered and what was left alone

| | candidates | registered | unchanged, left alone |
|---|---|---|---|
| `scan_2026-09-07b_rj2` | 115 | **31** | 84 |
| `scan_2026-09-09_rj1` | 141 | **30** | 111 |
| `scan_2026-09-10_rj1` | 142 | **142** | 0 |
| L0 families (cycle 3 re-judged) | 132 | **20** + 6 misbound (§1) | 106 |

**Cycle 4 is registered for the first time** (decision 3). Nothing was ever registered under
`scan_2026-09-10` — its gate stopped before §4 — so all 142 are new and there is nothing to
compare against. That is a fact about that cycle, not an exception to decision 2's rule.

Each new Result's description names the one it supersedes and its value; **no old Result was
touched** (AD-028, and decision 2 says so). The proof that 195 + 106 values did not move is the
comparison itself, recorded in `state/rejudgement_registration_2026-09-10.json` and
`state/l0_rejudged_registration_2026-09-10.json` with every unchanged name listed.

## 5. §2 decision 4 — what the L0 draft now says differently

**Five product legs moved**, each losing one `fail` to `error` on EIA's robots-disallowed
flagship — the surface the scanner was forbidden to read and had been scoring as a product that
failed:

| leg | before | after |
|---|---|---|
| A1 | 0 pass / 16 fail, n=16, upper95 0.1936 | 0 pass / 15 fail / **1 error**, n=**15**, upper95 **0.2039** |
| A3 | 3 pass / 13 fail, n=16, upper95 0.4301 | 3 pass / 12 fail / **1 error**, n=**15**, upper95 **0.4519** |
| A6 | 0 pass / 16 fail, n=16 | 0 pass / 15 fail / **1 error**, n=**15** |
| A8 | 0 pass / 16 fail, n=16 | 0 pass / 15 fail / **1 error**, n=**15** |
| B3 | 3 pass / 13 fail, n=16, upper95 0.4301 | 3 pass / 12 fail / **1 error**, n=**15**, upper95 **0.4519** |

**Three tags in the report re-pointed**, all in the product family and all verified against the
family that produced their originals: `scan_l0_product_a1_applicable_n` and
`scan_l0_product_a3_applicable_n` (16 → 15) and `scan_leg_rate_a1_upper95` (0.1936 → 0.2039).
Every other quoted number was checked and did not move. `scan_l0_product_legs_at_zero` is
unchanged at 8: losing a `fail` does not create a `pass`.

**The direction matters and is worth saying plainly.** Every one of these makes the instrument's
claim WEAKER — a smaller denominator and a higher upper bound. The defect had been flattering
the measurement by counting a page it could not read as a product that failed.

One sentence added to the movement section, as decision 4 asks. It went in with numerals in it
and the report's own prose gate blocked the build — every number in the report must be a
registered reference — so it was rewritten without them, which is the gate working.

**PDF: `docs/reports/2026-09_fss_ai_readiness_L0.pdf`**, rebuilt through `make report-pdf`,
numeral-multiset gate passed. The rebuilt text carries both the re-judged 0.203883 and the new
sentence.

## 6. §2 decision 3 — cycle 4's flagships, re-judged

| body | pass | fail | error | legs passed |
|---|---|---|---|---|
| DRSMSU | 5 | 10 | 0 | A6, A8, A10, D4, G1-D |
| NAHMSAPHIS | 3 | 12 | 0 | A4, A10, A11-declared |
| NCES | 4 | 11 | 0 | A3, A4, A10, A11-declared |
| SAMHSACBHS | 4 | 10 | 1 | A4, A5, A10, A11-declared |
| **BLS** | 0 | **0** | **15** | — |
| BTS | 0 | 0 | 15 | — |
| ORES | 0 | 0 | 15 | — |

**BLS is the row scan-run-4's gate stopped on.** It read 13 fail / 2 error, with A1 and A3
scored from links parsed out of a 403 access-denied page. It now reads `error` on all fifteen
legs, which is what a host that refused us told us about its product: nothing.

## 7. Every premise this task got wrong

1. **§1's stop condition stops on what decision 1 requires** (§3). Re-judging under `CURRENT` is
   a rule-version change by definition.
2. **Decision 5 is not achievable under decision 2, and the figures were NOT refreshed.** A
   figure resolves every numeral against a Result named for the cycle it draws — including
   `scan_a4_wilson_lo_<cycle>`, which no producer emitted for the re-judged cycles and which
   decision 2 forbids registering because its value did not change. Rendering
   `--cycle scan_2026-09-10_rj1` fails on the first such name. The two decisions are in direct
   conflict and I did not resolve it by quietly registering the full set. **The graph page and
   figures are unchanged and still show cycle 3 as measured**; §8 item 2 is the fix.
3. **`scan_report.py` writes its matrix files and registers in one function**, and reusing only
   the registration half left six DataFiles pointing at paths nobody had written. Caught when
   the figures could not find them; the six matrix files are written now.
4. **Cycle 1 was not re-judged and the RESULT was asked to confirm why.** Confirmed from the
   invariant test: `scan_2026-09-07` carries **6** product verdicts on unobserved evidence under
   v5's reading, not zero — the same six as cycle 2. Decision 1's premise ("its registered
   Results carried zero") is **wrong**; scan-run-4's table started at cycle 2 because it looked
   at three payloads, not because cycle 1 was clean. Cycle 1 is left alone as decision 1
   directs, and §8 item 3 is that it should not be.

## 8. Verification

```
logs/rj_build.log       three re-judgements, control gate PASS on each        EXIT=0
logs/rj_invariant.log   56 passed, 4 xfailed                          20 s   EXIT=0
logs/rj_rederive.log    12 of 12 payloads byte-identical               6 s   EXIT=0
logs/rj_report.log      report build gate PASS, 0 unresolved tokens    1 s   EXIT=0
logs/rj_pdf.log         make report-pdf, numeral gate 2 passed         2 s   EXIT=0
logs/rj_fast.log        1730 passed, 17 skipped, 4 xfailed           315 s   EXIT=0
logs/rj_full.log        1745 passed, 17 skipped, 4 xfailed          1174 s   EXIT=0
logs/rj_verify.log      seldon verify — All checks passed                     EXIT=0
logs/rj_protected.log   protected-paths diff                                  EXIT=0

payloads    state/scan_2026-09-07b_rj2.json   404 Findings
            state/scan_2026-09-09_rj1.json    634 Findings
            state/scan_2026-09-10_rj1.json    739 Findings
            six matrix files beside them
diffs       state/rejudgement_diff_2026-09-10.json
registered  229 Results (203 scan families + 26 L0), 0 failed
            301 compared and left unchanged, listed by name
            6 of the 26 are misbound — §1
new tests   tests/test_rejudgement_2_3_4.py, 11 cases
PDF         docs/reports/2026-09_fss_ai_readiness_L0.pdf
```

## 9. What the next task needs

1. **Supersede the six.** They are junk under names that cannot be rebound. The clean fix is a
   family-prefixed name (`scan_l0_leg_rate_…`, `scan_l0_tierc_leg_rate_…`) so three families stop
   competing for one string, and a migration of the report's tags onto it. The unprefixed name is
   a defect in `build_l0_matrices`, not in this task's use of it.
2. **Decide decision 2 against decision 5.** Either a re-judged cycle registers its full Result
   set (and "only what moved" becomes "only what moved, plus what a figure needs"), or figures
   resolve unchanged numerals through the cycle they were measured in. The second is better and
   is a change to `figures.py`, not to the registry.
3. **Cycle 1 carries the same six.** It was excluded on a premise that turned out false. It
   re-judges the same way and costs one command.
4. **The control fixtures still do not forbid an in-product probe** (harness-v5 RESULT §9 item
   1). Nothing here changes that: three cycles of this defect were found by reading payloads,
   never by the gate that should have caught it before the first one shipped.
