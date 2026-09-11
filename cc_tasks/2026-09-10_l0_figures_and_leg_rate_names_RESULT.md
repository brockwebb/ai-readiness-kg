# RESULT — L0 draft made self-consistent: figures from cycle 3 re-judged, leg-rate names family-prefixed, the six superseded

**Task:** `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md`. No addenda exist; globbed
before starting and again before §3, both times empty.
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network: none** — every payload this task read records
`requests_total: 0` and nothing was fetched.

---

## 1. The gate — §3

**PASS on every clause.**

| clause | result |
|---|---|
| Every figure numeral resolves, 0 hard errors | **PASS** — 6 figures × 2 cycles, **0 unresolved** |
| `test_report_text_and_figures_agree_per_leg` | **PASS** — 3 cases, and §5 says what "agree" can and cannot mean |
| Family-collision test | **PASS** — no two families emit one name, for any leg |
| Unprefixed-name refusal | **PASS** — refused at `cycle_results.check_names`, the choke point every registrar passes |
| The six supersessions present, correct values and pointers | **PASS** — 6 registered, 0 failed |
| `test_no_report_tag_quotes_a_misbound_result` over prose **and figures** | **PASS** |
| PDF numeral-multiset gate | **PASS** — 2 passed |
| Socket counter 0 | **PASS** — 0 on both re-judged payloads |
| `make gate-task` (the registry changed) | **PASS** — 340 s, 12 of 12 payloads re-derive |
| Full suite | **PASS** — 1,754 passed, 17 skipped, 4 xfailed, 1,265 s |
| `seldon verify` | **PASS** |
| Protected paths | **PASS** — rule modules, harness collectors, stored payloads, prior RESULTs, cycle evidence and targets unchanged; report prose changed by one line, the figure tag |

**§1's stop condition passed before anything was written.** All six values in
`2026-09-10_rejudge_2_3_4_RESULT.md` §1 reproduce from `build_l0_matrices` on
`state/scan_2026-09-09_rj1.json` to six decimals — both columns, the Tier C value that was bound
and the host value that should have been.

## 2. The cause was narrower than the task states, and the fix is wider

The task says six Results carry Tier C values "because `build_l0_matrices.leg_results` emits one
name for three families". **The shipped builder does not.** It emits
`scan_leg_rate_<leg>_upper95` from two families, host and product, and their legs are
**disjoint** — tier 0 is `A4, A5, A10, A11-declared, A12, G1-D`, `PRODUCT_LEGS` is
`A1, A2, A3, A6, A8, A9, B3, D1, D4, F4`. Tier C was never asked for the stat at all. The name
was unambiguous by **coincidence**, and `scripts/register_l0_rejudged.py` — mine, one task ago —
asked the third family for it and the coincidence ran out.

That makes the fix more important rather than less: a scheme that is correct only while two
lists stay disjoint is a scheme waiting for a third caller, and the third caller had already
arrived. Decision 2 is implemented as written.

## 3. §1 — the registry

**Decision 2: family-prefixed emission.** `leg_results` takes a `family` and emits
`scan_l0_<family>_leg_rate_<leg>_upper95`. `with_upper95=True` without a family now **raises** —
that exact call is what produced the six. Tier C emits its bound too, which it could not safely
do before. The unprefixed names already registered are untouched.

**Decision 4: refusal at the choke point.** `cycle_results.check_names` refuses any
`scan_leg_rate_*` name before a batch is registered, so no caller can mint another one — not the
emitter, which is one caller, but the point every registrar in the repo passes through.

**Decision 3: the six superseded.** Registered at the **Tier C** values, which is the only
reading that does not repeat the defect:

| superseded | value | successor |
|---|---|---|
| `scan_leg_rate_a4_upper95_2026-09-09_rj1` | 1.0 | `scan_l0_tierc_leg_rate_a4_upper95_2026-09-09_rj1` |
| `scan_leg_rate_a5_upper95_2026-09-09_rj1` | 0.561497 | `scan_l0_tierc_leg_rate_a5_upper95_2026-09-09_rj1` |
| `scan_leg_rate_a10_upper95_2026-09-09_rj1` | 1.0 | `scan_l0_tierc_leg_rate_a10_upper95_2026-09-09_rj1` |
| `scan_leg_rate_a11_declared_upper95_2026-09-09_rj1` | 1.0 | `scan_l0_tierc_leg_rate_a11_declared_upper95_2026-09-09_rj1` |
| `scan_leg_rate_a12_upper95_2026-09-09_rj1` | 1.0 | `scan_l0_tierc_leg_rate_a12_upper95_2026-09-09_rj1` |
| `scan_leg_rate_g1_d_upper95_2026-09-09_rj1` | 0.561497 | `scan_l0_tierc_leg_rate_g1_d_upper95_2026-09-09_rj1` |

**Decision 3's wording is ambiguous and §7 item 1 records the reading.** It says to register the
Tier C name "at the value the RESULT §1 table says it should be", and that table's *should be*
column holds the **host** value. A host value under a Tier C name is the same defect one column
over, so the Tier C name carries the Tier C number — the one that was misfiled and now has
somewhere correct to live. The host values are unchanged from cycle 3 and stay unregistered
under decision 2 of the previous task.

**There is no superseded state to walk them to.** Seldon's `Result` type in
`seldon/domain/research.yaml` has a `properties` block and **no `states` block** — checked, not
assumed. So decision 3's second branch applies: the record is the successor's description plus
the pin in `tests/test_rejudgement_2_3_4.py`, and that pin now covers figure inputs as well as
prose.

## 4. §2 — the figures

**Decision 1: the fallback is bound to evidence, not to a pattern.** `figures.Reads` resolves a
missing `_rj` name through the source cycle **only** when a comparison record lists it as
compared-and-unchanged; anything else raises `UnlicensedFallback`. A test feeds it a name in
neither place and asserts the hard error. Three records license it —
`rejudgement_registration`, `l0_rejudged_registration`, and `figure_inputs_registration`, the
last written by this task for a family nobody had compared.

**Every fallback taken, by figure** (`state/figure_fallbacks_2026-09-10.json` has each name and
the record line that licensed it):

| cycle | figure | fallbacks |
|---|---|---|
| `scan_2026-09-09_rj1` | per_leg_pass_rate | 68 |
| | gap_map_by_criterion | 21 |
| | cycle_over_cycle | 4 |
| `scan_2026-09-10_rj1` | cycle_over_cycle | 4 |

**`data-src` now names the Result the number came from**, not the one asked for. Rewritten at
the end of `build()` for every name that fell back — otherwise the figure cites a Result nobody
registered, which is exactly what the figure gate reported and which would make the provenance
attribute a statement about the lookup rather than about the evidence. The `CONTAINS` edges
follow the same resolution: **221 links, 0 failed**, where the first attempt failed 93.

### Which figures changed, and by what

Five of six differ from cycle 3 as measured; `progress_over_snapshots` is byte-identical.

**F1 `per_leg_pass_rate`**, 11 of 35 numerals moved, every one a denominator shrinking as a
robots-disallowed surface left it: `6/35 → 6/33`, `6/36 → 6/34`, `0/36 → 0/34`, `5/35 → 5/34`,
and the intervals that ride on them (`[0.08, 0.33] → [0.09, 0.34]`). **Every interval got wider
or stayed put.** That is the correction's direction throughout: fewer surfaces claimed as
measured, less certainty claimed about them.

**F5 `cycle_over_cycle`** was drawing the wrong comparison entirely and is the sharper find. Its
predecessor is configured per cycle, and `scan_2026-09-09_rj1` had no entry — so it fell through
to the global default and drew **cycle 1** beside cycle 3 re-judged, with 22 of its rows reading
"not measured in this cycle". The per-cycle override exists to prevent exactly that and did not
prevent it for a name it had never seen. Both re-judged cycles now have entries: cycle 3
re-judged against cycle 2 (the comparison the report's movement section makes), cycle 4 against
cycle 3 re-judged, like for like.

**Decision 5 needed a figure tag re-pointed, not only a `{{result}}` one.** The report embeds
`{{figure:cycle_over_cycle_2026-09-09:path}}`; leaving it there would have kept prose quoting the
re-judgement beside a figure of the measurement, which is the defect this task exists to close.
It now reads `cycle_over_cycle_2026-09-09_rj1`. That is the one line of prose this task changed.

**The graph page** draws cycle 4 from `scan_2026-09-10_rj1`. `framework_progress.py` could only
draw `params.cycle.name`, and `state/scan_matrix_2026-09-10.json` does not exist and never will —
cycle 4's gate stopped before it was reported. It takes a `--cycle` now, the same shape its
sibling scripts have.

## 5. What "text and figures agree" can mean, and what it cannot

`test_report_text_and_figures_agree_per_leg` does **not** assert that prose and figure print the
same number for a leg, because for A1 they correctly print different ones: the prose quotes the
L0 **product** family (the declared flagship surfaces, n=15) and F1 plots the **cycle** family
(every Tier A product surface, n=34). Different populations of one leg, under different names,
which is what `leg_results` exists to keep apart. Forcing them equal would be the error one
layer down from the one being fixed.

What the test asserts instead: every embedded figure is drawn from the cycle the prose quotes;
every name either side reads resolves to a registered Result or a licensed fallback; and no
metric appears as `…_2026-09-09` in a figure while its `…_2026-09-09_rj1` is quoted in the
prose. That last clause is the shape the PDF actually shipped with.

## 6. Verification

```
logs/lf2_agree.log      22 passed — agreement, names, misbound, PDF      2 s   EXIT=0
logs/lf2_gate_task.log  fast tier + 12 of 12 payloads re-derive        340 s   EXIT=0
logs/lf2_full.log       1754 passed, 17 skipped, 4 xfailed            1265 s   EXIT=0
logs/lf2_verify.log     seldon verify — All checks passed                     EXIT=0
logs/lf2_protected.log  protected paths — one line of prose, the figure tag   EXIT=0
logs/l0_audit.log       6 figures × 2 cycles, 0 unresolved numerals
logs/l0_rebuild.log     figures 221 links 0 failed; page EXIT=0; report gate PASS
logs/l0_pdf.log         make report-pdf, numeral gate 2 passed                EXIT=0

registered  6 supersessions (Tier C leg rates, cycle 3 re-judged)
            67 + 12 figure inputs (cycle 4 first registration; cycle 3 what moved)
            55 + 0 compared and left unchanged, recorded for the fallback
new tests   tests/test_leg_rate_names.py (6), tests/test_report_figures_agree.py (3)
PDF         docs/reports/2026-09_fss_ai_readiness_L0.pdf
```

## 7. Every premise this task got wrong

1. **Decision 3's "the value the RESULT §1 table says it should be"** is ambiguous: that
   table's *should be* column is the host value, and the name being registered is the Tier C
   one. Read as Tier-C-name-gets-Tier-C-value (§3).
2. **The collision was not in the shipped builder** (§2). It was in the caller I wrote one task
   ago. The task file attributes it one layer too low.
3. **Decision 5 says "no prose changes except a `{{result}}` tag"**, but the embedded figure is
   a `{{figure}}` tag and had to move too, or text and figures cannot agree — which is §3's own
   gate clause. One line.
4. **Decision 1's fallback had to key on the NAME, not on the cycle being drawn.**
   `cycle_over_cycle` reads the comparison cycle's names, and cycle 4's comparison is cycle 3
   re-judged, so a fallback scoped to the drawn cycle answered half the figure and raised on the
   other half. The licence is unchanged: the comparison record, or a hard error.
5. **A third family had never been compared.** Decision 1 presumes the unchanged lists exist for
   everything a figure reads; the figure-input family (`scan_<leg>_wilson_lo/_hi`,
   `scan_<leg>_control_fired`, 76 names per cycle) had no comparison record at all, because
   `register_figure_results.py` owns it and nothing had run it for a re-judged cycle. Compared
   and recorded here: 21 moved for cycle 3, all 76 new for cycle 4.
6. **`F5` had no predecessor configured for a re-judged cycle** and silently drew cycle 1 (§4).

## 8. What the next task needs

1. **The operator's read.** The PDF is now self-consistent: prose, figures and the graph page
   all speak for cycle 3 re-judged, and cycle 4 is on the page. This is the read that was
   blocked.
2. **Cycle 1 still carries six product verdicts on unobserved evidence** and was excluded from
   the re-judgement on a premise that turned out false
   (`2026-09-10_rejudge_2_3_4_RESULT.md` §7 item 4). One command.
3. **The control fixtures still do not forbid an in-product probe.** Four cycles of this defect
   were found by reading payloads, never by the gate that should have caught it first.
4. **The six misbound names remain in the registry**, superseded by pointer because no state
   machine exists to retract them. If Seldon gains a `superseded` state for `Result`, they are
   the first six to walk.
