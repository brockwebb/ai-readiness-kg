# RESULT — F5 stops saying "not measured" about legs that were measured

**Task:** `cc_tasks/2026-09-11_f5_membership_through_fallback.md`. No addenda exist; globbed
before starting and again before §3, both times empty.
**Date:** 2026-09-11 UTC
**Spend:** zero model calls. **Network: none** — every figure is drawn from registered Results
and stored payloads. Nothing under `state/` or `corpus/evidence/` changed, asserted by the
protected-paths check: no cycle was run and no payload was judged.

---

## 1. A correction to my own previous RESULT, at the top because it changes what this fixed

**The L0 report embeds `figures/scan_2026-09-09_rj1/cycle_over_cycle.svg` — the RE-JUDGED cycle
3, not the measured one.** `docs/reports/sections/60_movement.md` line 8 references the Figure
artifact `cycle_over_cycle_2026-09-09_rj1`, which resolves to that path, and the built markdown
and the PDF both carry it. The `l0_figures` task chose it deliberately; it is not a fallback and
not a miss.

`cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §8 item 6 says *"Nothing the L0 report
embeds is affected — it carries `figures/scan_2026-09-09/cycle_over_cycle.svg`, the measured
cycle, with 0 blank rows."* **That is wrong.** The report embeds the `_rj1` figure, which carried
**eleven** rows reading "not measured in this cycle" about legs that were measured. The defect
reached the published PDF, and the sentence that said it had not was written by the same session
that found the defect — which is how a finding gets under-reported: by checking the artifact
whose name is nearest rather than the one the document actually references.

Decision 4 asks this RESULT to state which F5 the PDF embeds "so the revision task starts from a
fact". The fact is the one above, and it upgrades the revision from cosmetic to required: the
PDF on disk still shows the eleven rows, because decision 4 forbids rebuilding it here. §6 is
how that is pinned rather than left to be noticed.

## 2. The gate — §3

| clause | result |
|---|---|
| `__contains__` ≡ `__getitem__` over every recorded name | **PASS** — 1,566 names, both directions |
| Blank-row set ≡ legs absent from the payload, every re-judged F5 | **PASS** — cycle 2 `_rj3` = `{A1, A3}`, every other drawable F5 empty |
| §1's stop: a blank neither the fallback nor the payload explains | **did not fire** — 0 unexplained, before or after |
| Numeral audit, 0 unresolved, over every re-rendered figure | **PASS** — 52 figures, 0 findings |
| Measured-cycle figures move nothing | **PASS** — new code and the code at `HEAD` produce byte-identical output for every measured cycle; the committed files were separately stale, §5 |
| Graph page carries 0 "not measured" rows for judged legs | **PASS** — 11 → 0 |
| Socket counter 0 | **PASS** — no collector ran; 0 changes under `state/` and `corpus/evidence/` |
| `make gate-task` | **PASS** — 1,886 passed, 17 skipped, 13 xfailed, 356 s; then 16 of 16 payloads byte-identical, 6.1 s |
| `make gate-full` | **PASS** — 1,905 passed, 17 skipped, 13 xfailed, 1,302 s, detached and polled to EXIT |
| `seldon verify` | **PASS** — all checks passed |
| Protected paths | **PASS** — `scripts/check_protected_f5.sh` |

## 3. §1 decision 1 — the type, not the call site

`figures.Reads` is a `dict` subclass. `__getitem__` resolves a missing name through the
evidence-bound fallback; `in` was `dict.__contains__` and knew nothing about it. So under
"register only what moved", a leg whose pass rate had not moved had no Result under the re-judged
cycle's name, `if rate_key not in R` said absent, and the row was drawn blank.

`__contains__` is now defined as exactly "`__getitem__` would return rather than raise", and
`__getitem__`'s own three membership tests were switched to `super().__contains__` — otherwise the
two recurse forever, which is the one trap in writing this. `get()` is overridden for the same
reason: `dict.get` reaches the C-level lookup and never calls `__getitem__`, so it was the same
hole with a different name.

**One asymmetry survives and is pinned rather than papered over.** A name that is missing and NOT
licensed reads as absent through `in` and raises `UnlicensedFallback` through `[]`. A caller who
branches on `in` can therefore still silence an unlicensed name — `__contains__` cannot fix that
from where it sits. What catches it is decision 2's test, which licenses a blank row only by the
PAYLOAD, so a blank produced by an unlicensed name fails as the unexplained blankness it is.

## 4. §1 decision 2 — blank rows before and after, per figure

One "not measured in this cycle" is drawn per (leg, series), so a leg blank on one series and
drawn on the other counts once for each.

| figure | before | after | what remains |
|---|---|---|---|
| `scan_2026-09-07b_rj3/cycle_over_cycle` | 12 | **2** | A1 and A3 on the cycle-1 series |
| `scan_2026-09-09_rj1/cycle_over_cycle` — **the one the report embeds** | 11 | **0** | |
| `scan_2026-09-09_rj2/cycle_over_cycle` | 21 | **0** | |
| `scan_2026-09-10_rj1/cycle_over_cycle` | 11 | **0** | |
| `scan_2026-09-10_rj2/cycle_over_cycle` | 11 | **0** | |
| `scan_2026-09-07b/cycle_over_cycle` (measured) | 0 | 0 | |
| every other figure of every cycle | 0 | 0 | |
| **total over 52 figures** | **66** | **2** | |
| `docs/progress/index.html` | 11 | **0** | |

**The two that remain are the sentence's real case.** Cycle 2 re-judged is drawn against cycle 1
re-judged, and cycle 1 never collected the `link_probe` leg — it entered with harness-v3 — so
`scan_2026-09-07_rj2`'s payload carries no A1 and no A3 Finding at all. Those two rows say
"not measured in this cycle" about a cycle that did not measure them, which is DD-055 exactly.

**§1's stop did not fire.** Every blank row, before the fix and after it, is explained either by
the fallback (a leg judged whose rate did not move) or by the payload (a leg with no Finding).
There is no third source of blankness.

## 5. §2 decision 3 — what re-rendering found, which was not what decision 3 expected

52 figures re-rendered across ten cycle directories; **16 files changed**, and they split cleanly
into two causes that have nothing to do with each other:

* **5 `cycle_over_cycle` files** — the fix. These are the only files whose TEXT changed.
* **11 files that gained `xmlns` and nothing else** — 4 in `scan_2026-09-07`, 5 in
  `scan_2026-09-07b`, 2 in `scan_2026-09-07b_rj1`. **Zero text nodes differ in any of them.**

The second cause is a day old and is not this task's: `cc_tasks/2026-09-10_harness_small.md`
decision 3 added `xmlns="http://www.w3.org/2000/svg"` to the SVG root because typst refuses a
figure without it ("missing root node"), and the figures of cycles 1 and 2 were never re-rendered
after it. Thirty-seven bytes of root attribute, and any of those eleven would have failed the PDF
build had the report referenced one.

**Decision 3's byte-identity clause asks two questions and only one of them was answerable as
written.** "The fix must move nothing where nothing was wrong" is true and was measured directly:
the renderer at `HEAD` and the renderer with `__contains__` produce **byte-identical output for
every measured cycle and for `scan_2026-09-07b_rj1`**. "The committed file matches what the
renderer produces" was FALSE for eleven files before this task touched anything. The first
question cannot be asked again once this is committed, because `HEAD` moves; the second is a
standing property, so it is now a test —
`test_every_committed_figure_is_what_the_renderer_produces_today`, with a companion asserting
every committed figure carries `xmlns`. That is the gate that would have caught the eleven a day
earlier.

**Two cycles cannot have an F5 at all, each for its own reason, and both are the machinery
refusing rather than guessing.** Decision 3 lists nine re-judged cycles; seven have figures.

| cycle | figures on disk | F5 |
|---|---|---|
| `scan_2026-09-07_rj1` | **0** | `UnlicensedFallback` — its figure-input Results (`…_wilson_lo_…`) were never registered under its name and no comparison record licenses a fallback. It predates the comparison-record convention, and this is why it has never had a figure. F1 and F3 refuse for the same reason. |
| `scan_2026-09-07b_rj2` | **0** | `UnconfiguredComparison` — no predecessor declared; F1 and F3 also refuse, as above |
| `scan_2026-09-07_rj2` | 5 | `UnconfiguredComparison` — nothing precedes the first cycle, which is correct and deliberate |
| the other six | 2 to 6 | drawn and audited |

Nothing was rendered for the two with no figures: there is nothing to RE-render, and drawing a
partial set for a superseded payload would add artifacts nobody asked for. Each is recorded in
`tests/test_f5_membership.py` with its reason as a marker, so a cycle that silently acquires an
F5 later fails the table rather than passing unnoticed.

## 6. §2 decision 4 — the PDF is one rebuild behind, and it is pinned

Re-rendering the figure the report embeds put the committed PDF out of step with it, and
`tests/test_report_pdf.py::test_the_pdf_carries_exactly_the_markdowns_numbers` found it
immediately — correctly. That gate subtracts the figure's numerals **read from disk**, so it is
also a staleness detector for the PDF against its own figures, and what it detected is true.

Decision 4 says `docs/reports/` is not rebuilt. Obeying it is what makes the PDF stale, so this
is not the task failing its gate — it is the task doing what it was told and the gate reporting
the consequence. Pinned the way this repo pins an immutable artifact's known defect
(`tests/test_invariants.py`): a **strict xfail** with the reason on its face, and beside it
`test_the_pdf_is_behind_by_exactly_the_figure_rows`, which asserts the shortfall is

```
{'0': 7, '33': 3, '32': 2, '24': 1, '35': 1, '34': 1, '2': 1}
```

and that the PDF carries **no** numeral the markdown lacks. The xfail says "this still fails";
the second says "by this much, and by nothing else", so any other drift in either direction is a
failure rather than an excuse. Rebuilding the PDF clears both at once — the xfail turns XPASS
(strict, so it fails) and the shortfall assertion fails with an empty multiset. Both say: delete
this pin.

## 7. §2 decision 5 — the comment beside the pin

One line above `ABSENCE_UNDER_PARTIAL_BLINDNESS["scan_2026-09-07"] = 1`, saying it is permanent
and why: the verdict is on leg A3, cycle 1 never collected the `link_probe` leg `RULE-A3-v6`
reads, so A3 is not re-judged for cycle 1 and a re-judgement cannot clear a verdict it is unable
to make. No pinned VALUE changed, and the protected-paths check proves it by parsing the `HEAD`
and working versions and comparing the tables entry by entry.

## 8. Every premise this task got wrong

1. **Decision 4's parenthesis is wrong and it was my error it inherited** (§1). The report
   embeds `_rj1`, not the measured cycle, so the published PDF did carry the defect. The
   revision is required, not cosmetic.
2. **Decision 3's byte-identity clause could not hold as written** (§5). Eleven committed
   figures were already stale for a reason one day older than this task. The question it meant
   to ask — does this change move a figure — is answered exactly and separately, and the
   question it literally asked is now a standing test.
3. **Decision 3's nine cycles are not nine figure sets** (§5). Two have no figures and cannot
   get a full set, one of them because the hard error installed by
   `2026-09-10_l0_figures_and_leg_rate_names.md` decision 1 is doing its job.
4. **`__contains__` cannot close the class on its own** (§3). The unlicensed case still reads as
   absent through `in`. Decision 1's "no caller can hit it again" is true for the licensed case
   and not for the unlicensed one; decision 2's payload test is what covers the rest.
5. **`scripts/register_scan_figures.py::_resolve_read` is a THIRD implementation of the fallback
   rule**, and it carries a hardcoded list of three cycles — `scan_2026-09-09_rj1`,
   `scan_2026-09-10_rj1`, `scan_2026-09-07b_rj2`. It is not run by this task, so nothing here
   depends on it, but any task that registers a Figure artifact for `_rj2` or `_rj3` will find it
   resolving those names to themselves and the `CONTAINS` edges failing, which is how 93 of them
   failed on its first run.

## 9. Verification

```
logs/f5_rerender.log       52 figures re-rendered, 16 changed, numeral audit 0 findings   EXIT=0
logs/f5_page.log           docs/progress/index.html, scan_2026-09-10_rj2, 0 blank rows    EXIT=0
logs/f5_gate_task_first.log  the same gate BEFORE the PDF pin: 1 failed, 1885 passed —
                           the stale-PDF failure, in full, as it was found          362 s  EXIT=2
logs/f5_gate_task.log      make gate-task — 1,886 passed, 17 skipped, 13 xfailed, 356 s; then 16 of 16 payloads byte-identical, 6.1 s                                  EXIT=0
logs/f5_full.log           make gate-full — 1,905 passed, 17 skipped, 13 xfailed, 1,302 s, detached and polled to EXIT                                  EXIT=0
logs/f5_verify.log         seldon verify — all checks passed                               EXIT=0
logs/f5_protected.log      scripts/check_protected_f5.sh — PASS                            EXIT=0

changed    assessment/harness/scan/figures.py  (__contains__, get, and the comment at
           the F5 blank branch)
           16 SVG files: 5 cycle_over_cycle (the fix), 11 xmlns-only (§5)
           docs/progress/index.html, tests/test_invariants.py (a comment, no value),
           tests/test_report_pdf.py (the pin and its companion)
new        tests/test_f5_membership.py (40 cases), scripts/check_protected_f5.sh
untouched  every rule module, the harness runtime, every stored payload and matrix,
           every registration record, figures.yaml, docs/reports/
```

## 10. What the next task needs

1. **Rebuild the PDF** — the cycle-4 report revision, which was already next. It clears the pin
   in `tests/test_report_pdf.py` (both halves at once) and replaces the eleven blank rows in the
   published document. This is now a correctness fix to the report, not a refresh.
2. **`_resolve_read`'s hardcoded cycle list** (§8 item 5), before any task registers a Figure
   artifact for a `_rj2` or `_rj3` cycle.
3. **`scan_2026-09-07_rj1` and `scan_2026-09-07b_rj2` have no figures and cannot get a full set**
   without registering their figure inputs. That is a decision about whether a superseded
   re-judgement deserves figures at all, and nothing needs it today.
4. **The `xmlns` class of staleness is now gated** for figures. Nothing checks the same property
   for any other build product.
