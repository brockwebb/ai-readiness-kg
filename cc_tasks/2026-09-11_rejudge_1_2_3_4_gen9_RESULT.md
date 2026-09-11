# RESULT — third re-judgement: cycles 1 to 4 under generation 9

**Task:** `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md`. No addenda exist; globbed before starting
and again before §3, both times empty.
**Date:** 2026-09-11 UTC
**Spend:** zero model calls. **Network: none** — four re-judgements of stored Observations, plus
the eight control fixtures on loopback. Every new payload records `requests_total: 0` and
`requests_per_host: {}`, asserted per payload.

---

## 1. §1's stop describes three cycles of the four, and the decision is mine

**The measurement first, because the decision follows from it.** Legs whose verdict differs from
the payload each new one supersedes:

| new cycle | supersedes | moved legs | §1's literal condition |
|---|---|---|---|
| `scan_2026-09-07_rj2` | `scan_2026-09-07_rj1` | A5 ×3, A6 ×1, A8 ×1, B3 ×1, G1-D ×1 | **does not hold** |
| `scan_2026-09-07b_rj3` | `scan_2026-09-07b_rj2` | A3 ×2 | holds |
| `scan_2026-09-09_rj2` | `scan_2026-09-09_rj1` | A3 ×1 | holds |
| `scan_2026-09-10_rj2` | `scan_2026-09-10_rj1` | A3 ×10 | holds |

**Cycle 1 cannot satisfy it, and that is knowable from the payload before a Finding is judged.**
`scan_2026-09-07_rj1` carries no `harness_version` — harness-v4, where a robots disallow was
SCOPE — and was judged under `RULE-A5-v1`, `RULE-A8-v3`, `RULE-A12-v1` and `RULE-B3-v2`.
Decision 1 admits cycle 1 *because* it never received harness-v5. So "only A3 and B3 may move"
and "cycle 1 is in, because it is two generations behind" are the same task file asking for two
things at once.

**What I enforced instead, for all four.** A verdict may move only where the instrument moved,
and the instrument is on the payloads: a rule version that differs between the two Findings, or
an error class on the Finding's own evidence whose KIND differs between the two harness versions.
Every move must land on `error` and be named by one of those. Where the predecessor is a
generation-8 payload — cycles 2, 3 and 4 — that permitted set comes out as **exactly `{A3, B3}`**,
which is §1's condition reached rather than typed, and a third leg moving there is still a hard
stop because nothing could have moved it. For cycle 1 the permitted set is eight legs
(`A11-declared`, `A12`, `A5`, `A6`, `A8`, `B3`, `D1`, `G1-D`) and the five that moved are inside
it. `strict_subset_holds` is recorded per cycle on `state/rejudgement_diff_2026-09-11.json` and
asserted per cycle in the test, so which cycles satisfied the literal form is a fact on disk and
not a sentence here.

**Nothing is unexplained.** All 20 verdict moves across the four cycles are `fail → error`. Not
one is `→ pass`, asserted separately: generation 9 turns an unprovable `fail` into a disclosure,
and a rule that started crediting something would be a different change wearing this one's name.

**Prior art, and it is this repo's.** `cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §3 met the
same conflict and recorded the same resolution — *"a verdict move is accounted for when it lands
on `error` and something names it — a class that changed kind, or a rule version that changed"*.
This is that condition, with the tighter subset held wherever it is meaningful.

**What would make this wrong.** If cycle 1's moves included a leg whose rule did not change and
whose evidence carried no class that changed kind, that would be a rule answering differently for
no declared reason and the task should have stopped. It does not: A6 and G1-D moved on unchanged
rules, and both cite `robots_disallowed` on EIA's flagship — the class harness-v5 redefined. The
operator may override this reading; the payloads and the diff record are on disk either way.

## 2. The gate — §3

| clause | result |
|---|---|
| Four new payloads, each naming itself, Findings only, no Observation | **PASS** |
| Moved-leg set ⊆ `{A3, B3}` with counts | **PASS on cycles 2, 3, 4** (A3 ×2, ×1, ×10); cycle 1 moves five legs, all inside what the instrument could have moved — §1 |
| Both invariant readings 0 on all four, asserted not xfailed | **PASS** — 85 passed, 12 xfailed |
| Byte-identical re-derivation of all **16** stored payloads under their own harness and rule versions | **PASS** — 16 of 16, 5.8 s |
| Every registered Result carries a supersession pointer | **PASS** — 575 checked in the graph |
| No registered Result repeats a value its own fallback already held | **PASS** |
| Comparison records present for three families | **PASS** — and each is in `figures.UNCHANGED_RECORDS` |
| Figures and graph page resolve for all four cycles, 0 `UnlicensedFallback` | **PASS** — and every numeral in every one of them resolves, through the published-figure gate |
| F5 raises on an unconfigured cycle | **PASS** — `UnconfiguredComparison`, and `figures.yaml` has no global `compare_to` |
| Socket counter 0 | **PASS** — `requests_total: 0`, `requests_per_host: {}` on all four |
| `make guards` | **PASS** — 25 passed, 16 s |
| `make gate-task` | **PASS** — 1,846 passed, 17 skipped, 12 xfailed, 346 s; then 16 of 16 payloads byte-identical, 5.9 s |
| `make gate-full` | **PASS** — 1,865 passed, 17 skipped, 12 xfailed, 1,209 s, detached and polled to EXIT |
| `seldon verify` | **PASS** — all checks passed |
| Protected paths, `docs/reports/` untouched | **PASS** — `scripts/check_protected_gen9.sh`, §8 item 5 for the one allowance |

## 3. §1 — the four diffs

A Finding's id derives from its rule, version, evidence and params hash, so a re-judgement mints
new ids for everything; the diff is keyed on `(surface, leg)` — the surface and the question.

| | verdict moves | transitions | moved by a newer RULE | moved by the CLASS | rule versions that moved |
|---|---|---|---|---|---|
| `_rj1` → `scan_2026-09-07_rj2` | 7 | 7 fail→error | 3 | 4 | A5 v1→v2, A8 v3→v4, A12 v1→v2, B3 v2→v3 |
| `_rj2` → `scan_2026-09-07b_rj3` | 2 | 2 fail→error | 2 | 0 | A3 v5→v6, B3 v2→v3 |
| `_rj1` → `scan_2026-09-09_rj2` | 1 | 1 fail→error | 1 | 0 | A3 v5→v6, B3 v2→v3 |
| `_rj1` → `scan_2026-09-10_rj2` | 10 | 10 fail→error | 10 | 0 | A3 v5→v6, B3 v2→v3 |

### The A3 verdicts generation 9 moved, with the blind candidate named

| cycle | surface | blind of 25 | class | first blind candidate |
|---|---|---|---|---|
| 2 | `scan-ers-flagship-1-ag-and-food-statistics-charting` | 1 | `connection_reset` | `https://www.ers.usda.gov/data-products?topic=food-choices-health` |
| 2 | `scan-nchs-flagship-1-data-briefs` | 1 | `timeout` | `https://www.cdc.gov/nchs/products/series/series13.htm` |
| 3 | `home:www.eia.gov` | 22 | `http_5xx` | `https://www.eia.gov/` |
| 4 | `home:www.eia.gov` | 21 | `http_5xx` | `https://www.eia.gov/` |
| 4 | `home:www.irs.gov` | 3 | `refused` | `https://sa.www4.irs.gov/ola` |
| 4 | `home:www.nass.usda.gov` | 1 | `robots_disallowed` | `https://quickstats.nass.usda.gov/` |
| 4 | `scan-nass-flagship-1-data-statistics` | 1 | `robots_disallowed` | `https://quickstats.nass.usda.gov/` |
| 4 | `scan-nass-flagship-2-livestock-county-estimates` | 1 | `robots_disallowed` | `https://quickstats.nass.usda.gov/` |
| 4 | `scan-nass-machine` | 1 | `robots_disallowed` | `https://quickstats.nass.usda.gov/` |
| 4 | `scan-nchs-flagship-1-data-briefs` | 1 | `http_5xx` | `https://tools.cdc.gov/medialibrary/index.aspx` |
| 4 | `scan-nchs-machine` | 1 | `http_5xx` | `https://tools.cdc.gov/medialibrary/index.aspx` |
| 4 | `scan-soi-flagship-1-individual-tax-statistics` | 3 | `refused` | `https://sa.www4.irs.gov/ola` |
| 4 | `scan-soi-flagship-2-business-tax-statistics` | 3 | `refused` | `https://sa.www4.irs.gov/ola` |

Three of the five classes here are not `robots_disallowed`. That is worth noticing: the family
this task closes is not "pages robots forbade", it is **any candidate the collector did not read**
— a reset, a timeout, a 5xx, a refusal to an identified client. Four of the ten cycle-4 moves are
a `robots_disallowed` on one URL, `https://quickstats.nass.usda.gov/`, seen from four surfaces.

**The single B3 move is cycle 1's, and generation 9 did not make it.**
`scan-eia-flagship-1-open-data` reads `error` because the whole methodology surface was
`robots_disallowed` — the harness-v5 correction. `RULE-B3-v2` carries the identical guard
(`rule_b3_v2.py:24` and `rule_b3_v3.py:36` are the same line) and would have returned the same
verdict under harness-v5; v3's new branch never fires here, because there was no partially
observed candidate set — there was no observation at all. **Generation 9 moved nothing on cycle
1.**

**And cycle 1's one absence-under-partial-blindness verdict is not cleared by this; it is not
re-judged.** It is on leg A3, and cycle 1 never collected the `link_probe` leg `RULE-A3-v6` reads
— that leg entered with harness-v3. So A3 registers nothing for cycle 1, with the reason on the
payload, and `ABSENCE_UNDER_PARTIAL_BLINDNESS["scan_2026-09-07"] = 1` stays pinned and always
will. Not measured is a reason, not a zero (DD-055). What cycle 1's re-judgement delivers is the
harness-v5 and generation-7/8 catch-up ResearchTask `016149c3` asked for, which is worth having
and is not what this task is named after.

## 4. §2 decision 3 — what was registered, and what "unchanged" had to mean

| cycle | family | candidates | registered | unchanged | global, already bound |
|---|---|---|---|---|---|
| `scan_2026-09-07_rj2` | scan | 101 | **101** | 0 | — |
| | figure inputs | 70 | **10** | 51 | 9 |
| | L0 | 132 | declined | — | — |
| `scan_2026-09-07b_rj3` | scan | 115 | **31** | 84 | — |
| | figure inputs | 76 | **13** | 54 | 9 |
| | L0 | 132 | declined | — | — |
| `scan_2026-09-09_rj2` | scan | 141 | **30** | 111 | — |
| | figure inputs | 76 | **12** | 55 | 9 |
| | L0 | 132 | **37** | 95 | — |
| `scan_2026-09-10_rj2` | scan | 142 | **142** | 0 | — |
| | figure inputs | 76 | **67** | 0 | 9 |
| | L0 | 132 | **132** | 0 | — |

**575 registered, 0 failed, 395 compared and left alone.** Every new Result's description names
the Result it supersedes and that Result's value; **no old Result was touched** (AD-028). The
records are `state/rejudgement_registration_2026-09-11.json`,
`state/figure_inputs_registration_2026-09-11.json` and
`state/l0_rejudged_registration_2026-09-11.json`, all three read by `figures.unchanged_names()`.

**"Unchanged" is compared against the fallback target, not against the payload superseded.** A
figure of a re-judged cycle resolves a missing name by stripping ONE `_rjN` suffix
(`figures.Reads.__getitem__`): `scan_a3_pass_2026-09-09_rj2` falls back to
`scan_a3_pass_2026-09-09`, the measured cycle, never to `_rj1`. So a value equal to the previous
judgement's but different from the measured cycle's still has to be registered — otherwise the
figure quietly draws a number superseded twice, under the new cycle's heading. That is the
misbound-six defect reached from the other side, and it is why **cycle 3's L0 family registers 37
numbers of which not one moved under generation 9**: 21 are identical to their `_rj1` values, 16
are names `_rj1` never bound at all (the family-prefixed leg rates postdate it), and 0 differ from
`_rj1`. Two tests hold the pair of rules: every name a record calls unchanged resolves through the
fallback to a Result holding that value, and no registered name repeats the value its own fallback
already had.

**Cycle 1 registers all 101 scan names, and that is DD-056 rather than an exception.** The first
cycle bound BARE names (`scan_a3_pass`, no suffix), so `scan_a3_pass_2026-09-07` does not exist
and no fallback is possible in either direction. Cycle 4 registers everything for the opposite
reason: its gate stopped before §4, so `scan_2026-09-10` bound nothing at all.

**The L0 families are declined for cycles 1 and 2, with the reason on the record.** `scan_l0_*`
has never existed for either — 116 names under cycle 3 measured and 21 under its `_rj1` are the
whole of that family in the registry — the report has never quoted them, and no figure reads
them. A name binds once, so 264 permanent names with no consumer is exactly the registry bloat
"register only what moved" exists to prevent. The payload is the durable artifact; any later task
that wants those numbers computes them from it in one command.

## 5. §2 decision 4 — both readings pin at zero on all four, asserted

| payload | first reading (wholly blind) | second reading (absence over a partly blind set) |
|---|---|---|
| `scan_2026-09-07_rj2` | 0 | 0 |
| `scan_2026-09-07b_rj3` | 0 | **0**, where the payload it supersedes carries 2 |
| `scan_2026-09-09_rj2` | 0 | **0**, where the payload it supersedes carries 1 |
| `scan_2026-09-10_rj2` | 0 | **0**, where the payload it supersedes carries 10 |

`tests/test_invariants.py`: **85 passed, 12 xfailed**. The four new rows are plain assertions, not
xfails. The eight historical pins are untouched, value for value, and the protected-paths check
proves it by parsing both the `HEAD` and the working version and comparing the tables entry by
entry rather than eyeballing a diff.

## 6. §2 decision 5 — the predecessors, and the default that is gone

`figures.yaml` no longer carries a global `compare_to`. `figures.config()` resolves the per-cycle
entry or `None`, and `figures.cycle_over_cycle` raises `UnconfiguredComparison` — a new exception
with the incident in its docstring — rather than drawing a comparison nobody declared.

| cycle drawn | F5 predecessor | rule changed |
|---|---|---|
| `scan_2026-09-07_rj2` | **none** — F5 is not drawn; it is the first cycle | — |
| `scan_2026-09-07b_rj3` | `scan_2026-09-07_rj2` | `{}` |
| `scan_2026-09-09_rj2` | `scan_2026-09-07b_rj3` | `{}` |
| `scan_2026-09-10_rj2` | `scan_2026-09-09_rj2` | `{}` |

Every `rule_changed` is empty, and that is the statement rather than an omission: all four are
judged under one `CURRENT` and one harness version, so no row on any of these figures carries an
instrument change and every difference is the hosts and the frame.

**One entry is added that is not new information.** `scan_2026-09-07b` — cycle 2 as measured — had
been taking the global default, so it is now written down explicitly. Deleting the default then
changes no figure that already exists, and the only F5 ever drawn from the default is the one that
now names its predecessor.

Figures rendered for all four cycles (five for cycle 1, six for the rest) and the graph page
rendered for all four, **0 `UnlicensedFallback`**. The page is left showing `scan_2026-09-10_rj2`.
`docs/reports/` is untouched and the report is not rebuilt.

## 7. What this moves in the numbers the report will quote

The cycle-4 revision rebuilds the report from `scan_2026-09-10_rj2`. Four L0 product-family
numbers move against `_rj1`, all on A3, and they are the only L0 numbers generation 9 moves
anywhere:

| | `_rj1` | `_rj2` |
|---|---|---|
| `scan_l0_product_a3_fail` | 15 | **10** |
| `scan_l0_product_a3_error` | 4 | **9** |
| `scan_l0_product_a3_applicable_n` | 19 | **14** |
| `scan_l0_product_leg_rate_a3_upper95` | 0.433343 | **0.546491** |

Five declared flagships leave the A3 denominator. **The direction is the same as last time and
worth saying plainly: the instrument's claim gets WEAKER.** A smaller denominator and a higher
upper bound is what honesty costs here — the harness had been counting surfaces whose
whole-product download it was never allowed to look for as products that do not offer one.

Cycle 3's L0 numbers do not move at all: its one A3 move is on `home:www.eia.gov`, a host surface,
and the L0 product family counts declared flagship surfaces.

## 8. Every premise this task got wrong, and one defect it found and did not fix

1. **§1's stop and decision 1 contradict each other** (§1). The task admits cycle 1 *because* it
   never received harness-v5, then forbids any leg but A3 and B3 from moving. Both cannot hold,
   and which one is wrong is decidable from the payload before any Finding is judged.
2. **Generation 9 moves nothing on cycle 1** (§3). Cycle 1 never collected the `link_probe` leg
   `RULE-A3-v6` reads, so A3 is not judged there at all, and its one B3 move is the harness-v5
   correction `RULE-B3-v2` would have made too. Cycle 1 belongs in this task, but for ResearchTask
   `016149c3`'s reason and not for this task's.
3. **"Register only what moved" does not say moved from what**, and only one answer keeps a figure
   correct (§4). Compared against the payload superseded, 37 of cycle 3's L0 names would have been
   called unchanged and the figure would have resolved them to the measured cycle's superseded
   values.
4. **Decision 5's raise cannot live in `config()`.** Five of the six figures need no predecessor,
   and `tests/test_scan_figures.py` calls `config()` before it knows whether a cycle is reported at
   all; a raise there turns "this cycle has no F5" into "this cycle has no figures". It belongs in
   `cycle_over_cycle`, where the missing fact is used.
5. **The zero-edits list says "harness", and decision 5 requires editing two files under
   `assessment/harness/scan/`** — `figures.py` and `figures.yaml`. Decision 5 is specific and the
   zero-edits line is general, so decision 5 wins, and the reading applied is that the harness
   RUNTIME is what may not move: collectors, `runner.py`, `run.py`, `publish.py`, `rederive.py`,
   `model.py`, `errors.py`, `manners.py`, `stats.py`, `frame.py`, the probes, the fetcher, the
   eight fixtures and `params.yaml`. `scripts/check_protected_gen9.sh` asserts every one of those
   is unchanged and then LISTS what did change rather than diffing it away.
6. **A defect this task found and did not fix: F5 says "not measured in this cycle" about legs
   that were measured.** `cycle_over_cycle` asks `if rate_key not in R` before reading it. `R` is a
   `figures.Reads`, whose evidence-bound fallback lives in `__getitem__`; `in` is
   `dict.__contains__` and never consults it. So under "register only what moved", a leg whose
   pass rate did not move has no Result under the re-judged cycle's name, the membership test says
   absent, and the row is drawn blank with the words DD-055 reserves for a leg nobody judged.

   | figure | blank rows | recoverable through the fallback | genuinely not judged |
   |---|---|---|---|
   | `scan_2026-09-07b_rj3` (this task) | 12 | 10 | 2 — A1 and A3, which cycle 1 never collected |
   | `scan_2026-09-09_rj2` (this task) | 21 | 21 | 0 |
   | `scan_2026-09-10_rj2` (this task) | 11 | 11 | 0 |
   | `scan_2026-09-09_rj1` (published 2026-09-10) | 11 | 11 | 0 |
   | `scan_2026-09-10_rj1` (published 2026-09-10) | 11 | 11 | 0 |

   It is pre-existing — the two `_rj1` figures carry it already — and §3's clause is "0
   `UnlicensedFallback`", which holds, because the fallback is not failing, it is not being asked.
   Not fixed here: the fix is one line, but an honest fix re-renders every re-judged figure and
   re-runs the numeral audit over them, which is a task with its own gate and not an edit
   smuggled into this one. Nothing the L0 report embeds is affected — it carries
   `figures/scan_2026-09-09/cycle_over_cycle.svg`, the measured cycle, with 0 blank rows. The
   graph page does show cycle 4 re-judged's F5 and therefore shows 11 of them.
7. **A Finding's prose contradicts itself on cycle 1's three A5 moves, and it cannot be fixed in
   place.** `_common.unobserved_error` prints the note belonging to the ERROR CLASS when what made
   the probe unobservable was the STATUS: on `https://www.census.gov/.well-known/ai-plugin.json`
   the class is `http_4xx` and the status is 403, which is in `manners.unobservable_statuses`, so
   the Finding reads *"was not observed (http_4xx): a client-error status that IS the
   measurement"* — right verdict, self-contradicting sentence. Not fixed: a Finding's `reason` is
   part of what the re-derivation gate compares, so changing the text breaks byte-identical
   re-derivation of every stored payload carrying one. It needs a new rule version.
8. **`state/scan_2026-09-07b_rj2.json` says `"cycle": "scan_2026-09-07b_rj1"`.** The file name and
   the field disagree, because `rederive.py --under-current` takes the suffix from a module
   constant and the previous task renamed the file with `--out`. A stored payload is immutable so
   it is not edited; `scripts/rejudge_gen9.py` passes the cycle name explicitly and a test asserts
   that each new payload names itself.
9. **The task file was untracked when the session started.** `seldon cc complete` refuses a task
   file git cannot recover, so it is committed with this work rather than by a separate
   registration commit.

## 9. ResearchTasks closed

Both were verified `proposed` before writing, not assumed.

```
016149c3  proposed → superseded   superseded_by 25bc8063 (this task)
          Cycle 1 IS re-judged here, as scan_2026-09-07_rj2 — and its premise is
          confirmed the other way round: cycle 1's gap is harness-v5 and
          generations 7 and 8, not generation 9, which moves nothing on it (§3).
24af5222  proposed → superseded   superseded_by 25bc8063 (this task)
          The global compare_to default is gone; an unconfigured cycle raises
          UnconfiguredComparison in cycle_over_cycle, with a test.
```

## 10. Verification

```
logs/g9_build.log        four re-judgements, eight-fixture control gate PASS          EXIT=0
logs/g9_register.log     575 Results registered, 0 failed, 395 left unchanged         EXIT=0
logs/g9_figures.log      figures for four cycles (five for cycle 1)                   EXIT=0
logs/g9_page.log         docs/progress/index.html for four cycles                     EXIT=0
logs/g9_guards.log       make guards — 25 passed                              16 s    EXIT=0
logs/g9_gate_task.log    make gate-task — 1,846 passed, 17 skipped, 12 xfailed, 346 s; then 16 of 16 payloads byte-identical, 5.9 s                               EXIT=0
logs/g9_gate_task_first.log  the same gate before the four figure-audit cases
                         were added: 1838 passed, 16 of 16 re-derive         356 s    EXIT=0
logs/g9_full.log         make gate-full — 1,865 passed, 17 skipped, 12 xfailed, 1,209 s, detached and polled to EXIT                               EXIT=0
logs/g9_verify.log       seldon verify — all checks passed                     1 s    EXIT=0
logs/g9_protected.log    scripts/check_protected_gen9.sh — PASS                       EXIT=0

payloads    state/scan_2026-09-07_rj2.json    352 Findings
            state/scan_2026-09-07b_rj3.json   404 Findings
            state/scan_2026-09-09_rj2.json    634 Findings
            state/scan_2026-09-10_rj2.json    739 Findings
            eight matrix files beside them
diff        state/rejudgement_diff_2026-09-11.json
records     state/rejudgement_registration_2026-09-11.json
            state/figure_inputs_registration_2026-09-11.json
            state/l0_rejudged_registration_2026-09-11.json
new code    scripts/rejudge_gen9.py, scripts/rejudgement_diff_gen9.py,
            scripts/register_gen9_rejudged.py, scripts/check_protected_gen9.sh
new tests   tests/test_rejudgement_gen9.py, 48 cases
figures     assessment/harness/scan/figures/scan_2026-09-07_rj2/   (5, no F5)
            assessment/harness/scan/figures/scan_2026-09-07b_rj3/  (6)
            assessment/harness/scan/figures/scan_2026-09-09_rj2/   (6)
            assessment/harness/scan/figures/scan_2026-09-10_rj2/   (6)
page        docs/progress/index.html, showing scan_2026-09-10_rj2
```

## 11. What the next task needs

1. **The cycle-4 report revision**, from `scan_2026-09-10_rj2`, which is registered and whose
   figures and matrices are on disk. Four L0 tags move, all A3 (§7); `docs/reports/` is untouched
   here, so the revision starts from exactly what the last one left.
2. **F5's membership test** (§8 item 6). One line, and then every re-judged figure has to be
   re-rendered and put back through the numeral audit — including the two the harness-v5 task
   published. It is the largest untrue thing in a published artifact this repo currently has.
3. **`_common.unobserved_error`'s message** (§8 item 7). It needs a rule version, because the text
   is inside the re-derivation comparison. Worth doing the next time any rule turns over.
4. **Cycle 1's A3 pin stays at 1 forever** and nothing will clear it. Whoever next reads
   `ABSENCE_UNDER_PARTIAL_BLINDNESS` should find that written beside it rather than try.
5. **The L0 families of cycles 1 and 2 are computable and deliberately unregistered**, with the
   reason on `state/l0_rejudged_registration_2026-09-11.json`. If a report ever compares cycles at
   the L0 level, that is where to start.
6. **`RECENT_CYCLES` now names `scan_2026-09-10_rj2`**, so the `_rj1` payloads' re-derivation moved
   to the slow tier. The full suite still runs them before every push, and `gate-task` runs all
   sixteen whatever their tier.
