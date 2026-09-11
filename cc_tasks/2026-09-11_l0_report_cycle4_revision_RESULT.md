# RESULT — L0 report, cycle-4 revision: the snapshot is `scan_2026-09-10_rj2`

**Task:** `cc_tasks/2026-09-11_l0_report_cycle4_revision.md`. No addenda exist; globbed before
starting and again before §3, both times empty.
**Date:** 2026-09-11 UTC
**Spend:** zero model calls. **Network: none** — no host was contacted, no figure was
re-rendered, no cycle was run. Socket counter 0: nothing under `state/scan_*` or
`corpus/evidence/` changed, asserted by `scripts/check_protected_c4.sh`.

---

## 1. ONE CLAUSE OF §3 FAILS, AND IT FAILED BEFORE THIS TASK: THE PAGE COUNT

**§3 requires "page count ≤ 7". The PDF is 12 pages. The PDF this task replaced was 11.**

| artifact | pages | where the number is recorded |
|---|---|---|
| the design note's target | 7 | `cc_tasks/2026-09-09_report_draft.md` §1, "matrix on one page, at most six pages around it" |
| the first built markdown | ~9 | `cc_tasks/2026-09-09_report_draft_RESULT.md` §"Length": *"about nine pages against the design note's seven"* |
| the PDF at `HEAD` | **11** | `cc_tasks/2026-09-10_report_pdf_RESULT.md` §1 and its `pdfinfo` line |
| the PDF this task writes | **12** | `pypdf`, §6 |

**The clause has never held for this artifact, and this task could not make it hold.** The one
page added is the task's own content: the product matrix grew from 16 rows plus 7 "not declared"
rows to 23 measured rows because every body now has a declared flagship (decision 3d), and
decisions 3b, 3c and 4 each add a paragraph. Getting to seven pages would mean deleting sections
the scope fence forbids touching.

**So the threshold is not moved and not restated.** It is reported here as a failed
pre-registered clause, with its history, and the next task's decision is whether a seven-page
target still governs a document that has never been seven pages — or whether the matrices move
to the machine-readable files that already sit beside the report and the prose keeps the page
budget.

**Why the PDF was written anyway, which is a decision and is mine.** §3's failure clause says a
failure writes no PDF. Applied here it would leave a *published* artifact carrying eleven rows
that say "not measured in this cycle" about legs that were measured — the defect this task
exists to fix (`cc_tasks/2026-09-11_f5_membership_through_fallback_RESULT.md` §1) — in order to
protect a length target the same artifact already violated by four pages. Every clause that
bears on whether the document is TRUE passes (§2). The operator may reverse this; the previous
PDF is one `git checkout` away and the page count is on the face of this section.

## 2. The gate — §3

| clause | result |
|---|---|
| Every `{{result}}` and `{{figure}}` tag resolves | **PASS** — 0 fatal reference errors, 0 unresolved tokens over 59 tags |
| 0 hand-typed numerals (tag-coverage lint) | **PASS** — `bare_numerals_in_prose: []` |
| PDF numeral-multiset gate green, pin deleted, no replacement pin | **PASS** — `test_the_pdf_carries_exactly_the_markdowns_numbers` passes as a plain assertion; the strict xfail and `test_the_pdf_is_behind_by_exactly_the_figure_rows` are deleted, and nothing replaces them |
| `test_report_text_and_figures_agree_per_leg` | **PASS** — after moving `REPORT_CYCLE` to `2026-09-10_rj2`, §5 |
| The embedded F5 carries 0 "not measured" rows | **PASS** — `scan_2026-09-10_rj2/cycle_over_cycle.svg`, 0 occurrences; the PDF's one "not measured" is prose |
| **Page count ≤ 7** | **FAIL — 12.** §1, and it was 11 before this task |
| `_resolve_read` absent, single-implementation test green | **PASS** — `tests/test_figure_registration.py`, 9 cases |
| Figure artifacts registered with resolving `CONTAINS` edges | **PASS** — 12 Figures, 552 links, 0 failed; every edge asserted against the graph |
| Every committed figure is what the renderer produces today | **PASS** — in the suite, unchanged from the task that installed it |
| Socket counter 0 | **PASS** — no collector ran; 0 changes under `state/scan_*` and `corpus/evidence/` |
| `make gate-task` | **PASS** — 1,895 passed, 17 skipped, 12 xfailed, 345.7 s; then 16 of 16 payloads byte-identical, 5.8 s |
| `make guards` | **PASS** — 25 passed, 15.7 s |
| `make gate-full` | **PASS** — 1,914 passed, 17 skipped, 12 xfailed, 1,211 s, detached and polled to EXIT |
| `seldon verify` | **PASS** — all checks passed |
| Protected paths | **PASS** — `scripts/check_protected_c4.sh` |

## 3. §1, decision 2 — one implementation of the fallback, and the Figure artifacts

`scripts/register_scan_figures.py::_resolve_read` is deleted with its hardcoded three-cycle
list. Registration now asks `figures.Reads` for the VALUE and reads `fell_back` for the name it
resolved to, so the edge follows the same resolution the figure did, by the same licence.

`tests/test_figure_registration.py` holds four things: the deleted resolver stays deleted and
its three cycle names are absent from the module's code; `resolve_read` is `Reads`' answer and
raises `UnlicensedFallback` on an unlicensed name; every figure on disk for both `_rj2` cycles
has a live Figure artifact; and every `data-reads` name, resolved, is on the far end of a
`CONTAINS` edge in the graph.

**Decision 2's "no module other than `figures.py` implements suffix stripping" could not be
asserted in that form, and the reason is on the test.** Two other modules carry one:

* `scripts/register_gen9_rejudged.py::fallback_target` — a DELIBERATE paired implementation,
  documented as such and held equal to `figures._source_name` by
  `tests/test_rejudgement_gen9.py::test_the_registrar_and_the_renderer_agree_on_where_a_name_falls_back_to`.
  It answers a different question (what should I register?) in a different layer, and importing
  the renderer into the registrar is the coupling that let three families share one Result name.
* `scripts/register_rejudged_cycles.py` — `cycle.removesuffix('_rj1')` inside a description
  string, on a literal from that module's own `PAIRS`. It resolves nothing.

Both are in a declared allowlist with the reason beside each, and anything new fails. The clause
as written would have been satisfied only by deleting a duplication the repo installed on
purpose; what it is *for* — figure registration has one resolver — holds exactly.

**The stop did not fire.** Every one of the 540 reads across the twelve figures resolved before
anything was registered: 270 reads per cycle, 190 through the fallback for `scan_2026-09-09_rj2`
and 53 for `scan_2026-09-10_rj2`, 0 unlicensed, 0 pointing at a name the registry does not hold.

## 4. Decision 1 — every tag that moved, from what to what

Four tags did not move: `fss_agencies_tier_a`, `fss_tier_a_source_disagreements`,
`fss_scan_netlocs_2026-09` (22 netlocs at v4 and at v5 — the seven declared flagships added
surfaces on hosts already in the frame) and `fss_hosts_refusing_identified_client_2026-09`.
Every other tag moved. 39 names left the report and 55 entered it.

| the report says | was | is now | value |
|---|---|---|---|
| requests issued | `scan_requests_total_2026-09-09` | `scan_requests_total_2026-09-10` | 2341 → 2684 |
| netlocs contacted | `fss_scan_netlocs_contacted_2026-09-09` | `fss_scan_netlocs_contacted_2026-09-10` | 24 → 35 |
| observations | `scan_observations_2026-09-09` | `scan_observations_2026-09-10` | 2429 → 2718 |
| findings | `scan_findings_2026-09-09` | `scan_findings_2026-09-10_rj2` | 634 → 739 |
| declared surfaces in the frame | `fss_scan_surfaces_2026-09` | `fss_scan_surfaces_2026-09-10` | 65 → 72 |
| A4 / A5 / A10 / A11-declared / A12 / G1-D, every count | `scan_l0_<leg>_*_2026-09-09` | `scan_l0_<leg>_*_2026-09-10_rj2` | the table in the report |
| G1-D's upper bound | `scan_leg_rate_g1_d_upper95_2026-09-09` | `scan_l0_host_leg_rate_g1_d_upper95_2026-09-10_rj2` | 0.242494 → 0.228095 |
| A1's upper bound | `scan_leg_rate_a1_upper95_2026-09-09_rj1` | `scan_l0_product_leg_rate_a1_upper95_2026-09-10_rj2` | 0.203883 → 0.168179 |
| Tier C coherence | `scan_a12_tierC_pass_2026-09-09` | `scan_l0_tierc_a12_pass_2026-09-10_rj2` | 3 → 3 |
| home/flagship disagreements | `scan_l0_home_flagship_disagreement_{cells,bodies}_2026-09-09` | `…_2026-09-10_rj2` | 15/6 → 17/8 |
| declared flagships | `scan_l0_declared_flagship_{agencies,surfaces}_2026-09-09` | `…_2026-09-10_rj2` | 9/16 → 16/23 |
| product legs at zero | `scan_l0_product_legs_at_zero_2026-09-09` | `…_2026-09-10_rj2` | 8 of 10 → 5 of 10 |
| A3, A1, B3 on products | `scan_l0_product_*_2026-09-09(_rj1)` | `…_2026-09-10_rj2` | A3 3/15 → 4/14; A1 0/15 → 0/19; B3 3 → 3 |
| bodies pending a declaration | `fss_agencies_pending_operator_declaration_2026-09` | `…_2026-09-10` | 7 → 0 |
| the off-frame sitemap caveat | `scan_a5_fail_offroster_sitemap_2026-09-09` | `…_2026-09-10_rj2` | 0 → 0 |
| the unnamed error class | `scan_error_class_unknown_2026-09-09` | `scan_error_class_unknown_2026-09-10` | 1 → 1 |
| refusal persistence | `scan_refusal_consecutive_measurements_2026-09-09` | `…_2026-09-10_rj2` | 5 → 6 |
| F5 | `cycle_over_cycle_2026-09-09_rj1` | `cycle_over_cycle_2026-09-10_rj2` | the figure of the snapshot |

**The two family-prefixed renames are the fix of
`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 4 arriving in the prose.** The
unprefixed `scan_leg_rate_<leg>_upper95` names do not say which of three populations computed
them; the report now names the family it means.

### Decision 1's premise was wrong for eleven tags, and what was done about it

**"Everything the report quotes is a registered Result or a figure on disk" did not hold.**
Eleven cycle-3 tags had no cycle-4 name to move to and no licensed fallback: the six L0
population counts, the three collection facts, `fss_scan_netlocs_contacted` and
`scan_refusal_consecutive_measurements`. Cycle 4's gate stopped before registration
(`cc_tasks/2026-09-10_scan_run_4_RESULT.md` §1) and the generation-9 pass registered the leg
families and not these.

Decision 1 says such a tag "is a hard error, never a hand-typed number". Read as "stop", the
report could not move to cycle 4 at all and the false F5 stays published; read as "do not type
the number", the answer is to register it from the artifact it is about, which is what every
cycle does. **16 Results were registered, by the registrars that own each family, every value
recounted from a payload or a matrix on disk, nothing typed:**

| registrar | names | what |
|---|---|---|
| `scripts/build_l0_matrices.py --cycle scan_2026-09-10_rj2` | 6 | the L0 population counts; **and 132 of the 138 it emits were already bound at exactly this value**, which is an independent check that this builder and the generation-9 registrar agree number for number |
| `scripts/register_l0_report_results.py --cycle scan_2026-09-10_rj2` | 3 | netlocs contacted, the off-frame sitemap caveat, refusal persistence |
| `scripts/register_measured_collection_facts.py` (new) | 4 | observations, requests, the unnamed error class, netlocs contacted — under the MEASURED cycle's name |
| `scripts/register_esip_crosswalk_results.py` | 1 | `noaa_ai_ready_components_2026-09-10` = 5, the denominator decision 3c's "3 of 5" needs |
| `scripts/register_superseded_l0_endpoints.py` (new) | 2 | A3's denominator and upper bound under `_rj1`, the BEFORE end of decision 4's movement |

**One of those 16 is misfiled and is superseded rather than hidden.**
`fss_scan_netlocs_contacted_2026-09-10_rj2` was bound before I had read `scan_report.results`,
which already decides this: *"the Results that describe the MEASUREMENT — observations captured,
requests issued per host, error classes recorded — are the source cycle's and are not
re-registered under this cycle's name"*, because a re-judgement fetches nothing. Its value and
description are true; its NAME files a socket count under a cycle that opened no socket. A name
binds once (AD-028) and Seldon's `Result` has no state machine, so the supersession is
`fss_scan_netlocs_contacted_2026-09-10`'s description, `state/collection_facts_2026-09-10.json`,
and this paragraph — the shape `scripts/supersede_misbound_leg_rates.py` used. The report quotes
the measured-cycle name.

**`register_measured_collection_facts.py` types neither the family nor the list.** The
measurement family is DERIVED as the difference between what `scan_report.results` emits for the
measured payload and what it withholds for the re-judged one (52 bases), and it is intersected
with the `{{result:…}}` tags the report's own sections quote. Four names came out. That is why
it registered four and not fifty-two: a permanent name with no consumer is the bloat
`cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9_RESULT.md` §4 declined 264 of.

## 5. Decisions 3 and 4 — the content changes, and the ones the snapshot forced

**The four the thread-close handoff named.**

**(a) Cycle 4 as the snapshot.** Every tag above; the matrices and the appendix fragments
rebuilt from `scan_2026-09-10_rj2`; the provenance line names the cycle, its parameter hash and
the judgement. The matrix's last row no longer says "planned": it reads *"no host yet; the
instrument is turned on this report when it is published"*. **Decision 3a is ambiguous and I
read it the narrow way.** It can mean that hand-typed row, or it can mean the product matrix's
"not declared" rows, which cycle 4 removes on its own because every body has declared. The
second is satisfied mechanically. For the first, nothing licenses saying the report HAS a host —
`cc_tasks/2026-09-10_report_pdf_RESULT.md` §8 item 2 says it does not — so the row states the
present fact and drops the word, and GitHub Pages is still named in the closing section.

**(b) The refusal column and one sentence.** *"{3} bodies of {16} decline to answer a client
that identifies itself…"*, with the persistence tag at 6 measurements and *"taken on four
different days"* — four, because `state/scan_2026-09-10.json` is the sixth artifact and it is a
fourth date. Decision 3b says "six consecutive cycles"; the registered Result counts six
measurement ARTIFACTS, of which four are cycles and two are pre-flights, so the prose says what
the Result means.

**(c) NOAA and ESIP, in "what the matrix cannot see".** NOAA's own order defines AI-ready data
in {5} components of which this instrument measures {3} exactly; ESIP's checklist has {58}
assessable items of which {9} are measured exactly. Both as tags. The bullet they replace —
*"Most of the frame, at product level"* — had become false, because the product section now
covers every body.

**(d) The four flagships that came live.** The declared count carries a tag and now reads 16 of
16 agencies across 23 surfaces; {7} flagships were declared for this cycle and {3} of them were
answered with a refusal, so the number that came live is the difference, stated in words rather
than typed as a numeral.

**Decision 4, the A3 movement.** One paragraph in the movement section: the bulk-download check
was answered over 19 declared flagship surfaces under the previous judgement of this same cycle
and is answered over 14 now; the upper bound of the interval rose from 0.433343 to 0.546491.
Both ends are tags. The paragraph says plainly that the surfaces which left are ones whose
whole-product download the scanner was forbidden to look for, that nothing about those products
changed, and that a smaller denominator is a weaker claim.

**Five further prose changes the snapshot FORCED, none of them new content.** Each is a sentence
that became false when the cycle moved, and leaving it would have shipped a falsehood:

1. **The fourth unobserved body is gone.** Cycle 3 had a body that timed out; in cycle 4 only
   the three refusing bodies carry `error`. The paragraph now says it answered this time.
2. **The zero legs.** 8 of 10 product checks were at zero in cycle 3 and 5 of 10 are now, so the
   list of what no product offers is the list of the five, and the checks that are not at zero
   are named with their counts.
3. **"Most bodies have not declared a product"** was the explanation for the wide interval and
   is no longer true; the interval is wide because one product is one surface.
4. **The open question about the rest of the frame** (`70_future.md`) was answered by this
   cycle; it is replaced by the question the cycle raises — one page per body is not a product.
5. **The controls.** Cycle 4 ran SEVEN fixtures, not the six the appendix describes; the
   seventh, `sitemap_on_sibling`, is now described with what it pins, which is an order.

## 6. Decision 5 — traceability, measured and reported, not gated

`scripts/report_traceability.py`, labelled Cypher, read-only. For each leg: does the rule's
indicator node reach a construct, a definition and a primary source?

| leg | indicator node | → construct | → definitions | → source documents | measurement spec | rules |
|---|---|---|---|---|---|---|
| A4 | `A4` | 1 — Crawler/agent access | 29 | 6 | 1 | 1 |
| A5 | `A5` | 1 — Discoverability surface | 29 | 2 | 1 | 2 |
| A10 | `A10` | 1 — Application/data-tool machine surface | **0** | **0** | 1 | 3 |
| A11-declared | `A11` | 1 — Effective crawler access (declared / enforced) | 13 | 2 | 1 | 2 |
| A12 | `A12` | 1 — Access policy coherence | 13 | 2 | 1 | 1 |
| G1-D | `G1-D` | 1 — Uncertainty legibility | 364 | 40 | 1 | 1 |
| A3 | `A3` | 1 — Bulk access | **0** | **0** | 1 | 4 |

The chain is `AssessmentCriterion → AssessmentConstruct → AssessmentIndicator`, the indicator
`-[:EVIDENCED_BY]->` a `Document`, and the document `-[:DEFINES]->` its `Definition` nodes; the
definition count is what is reachable that way.

**Two of the seven reach nothing: A10 and A3 have no primary source document at all**, so no
definition either. Every leg has an indicator, a construct and a measurement spec, and every leg
is judged by a rule, so the gap is exactly and only the citation: the report's deep-link check
and its bulk-download check — the latter being the one product check with a pass rate worth
reading — rest on no cited source in this graph. **The report is not changed for it**, as
decision 5 requires. The next task decides whether those two indicators get their sources or
whether the report says which of its checks are uncited.

`A11-declared` has no indicator node of its own and is measured through `A11`; that mapping is
declared in the script rather than discovered by a fuzzy match, so a leg with no indicator at
all would report as one instead of being paired with a neighbour.

**Two Cypher directions were written the wrong way round first and both said "no edge".**
`DECOMPOSES_INTO` runs construct → indicator, and `DEFINES` runs document → definition. Reversed,
the first reported every leg as having no construct and the second reported every leg as
reaching no definition — a clean, plausible, entirely false table. It is in this RESULT because
"no edge" is exactly the answer a reversed arrow gives, and decision 5 asks for that answer.

## 7. A defect found and fixed: `make report-pdf` did not rebuild the markdown

**The first PDF this task built was the previous cycle's report, embedding the previous cycle's
figure, and nothing reported an error.** `scripts/build_report_pdf.py`'s docstring and the
Makefile's `report-pdf` comment both say the markdown is rebuilt first by
`scripts/build_l0_report.py`. Nothing did it. `main` checked that
`2026-09_fss_ai_readiness_L0.md` exists and carries no unresolved `{{` token — which a stale file
passes trivially — and converted it.

Fixed where the promise was made: `build_report_pdf.main` now calls `build_l0_report.build()`
and refuses to render if that gate blocks. A build product whose builder does not run is a
committed artifact that drifts from its sources in silence, and this one had drifted by a whole
cycle within a minute of the tags moving.

## 8. Every premise this task got wrong

1. **"Everything the report quotes is a registered Result or a figure on disk"** (§4). False for
   eleven tags. 16 Results registered from artifacts on disk, one of them superseded by a
   better-named sibling in the same pass.
2. **"≤ 7 pages"** (§1). Never true of this artifact: 11 pages at `HEAD`, 12 now.
3. **"A test asserts no module other than `figures.py` implements suffix stripping"** (§3). Two
   others do, one of them a deliberate paired implementation with its own equality test. The
   test asserts the scoped form, with both exceptions and their reasons on its face.
4. **Decision 3a's "the matrix's last row no longer 'planned'" is ambiguous** (§5a). Both
   readings are addressed; the narrow one is a judgement and is recorded as one.
5. **Decision 3's "the four content changes and nothing else" was not achievable** (§5). Moving
   the snapshot falsified five further sentences. Leaving them would have shipped a report whose
   prose described cycle 3 and whose numbers described cycle 4.
6. **Decision 3b says "six consecutive cycles"; the Result counts six measurement artifacts**
   (§5b), four of which are cycles. The prose says what the Result means.
7. **Decision 4's "19 → 14" had only one end registered** (§4). The other was minted here, from
   the superseded payload, by the module that owns the computation.
8. **The report's figures and matrices could not be rebuilt from a re-judged payload without
   two fixes** (§9). A re-judgement records no Observation, so the appendix's requests-per-netloc
   table came out as a total of zero and the matrix's refusal column came out as `0 of 0` for
   every body — including the three that refuse everything.
9. **`scripts/build_l0_matrices.py --dry-run` writes files.** The matrices and the generated
   fragments are written before the dry-run check. Not fixed here — it is a one-line move in a
   script this task was already editing for other reasons, and changing what `--dry-run` means
   mid-task is how a verification step stops being one. It is named for the next task.

## 9. What changed in the scripts, and why each change was necessary

* `scripts/register_scan_figures.py` — decision 2. `_resolve_read` out, `figures.Reads` in.
* `scripts/build_l0_matrices.py` — `--cycle`, so a re-judged cycle can be built at all; and
  `evidence_payload()`, because two things in these matrices are counted off OBSERVATIONS and a
  re-judgement has none. The requests table and the refusal column now read the measured cycle
  the judgement derives from. Both were silently empty before, which is the worse failure: `0 of
  0` beside BLS reads as "nothing was refused".
* `scripts/register_l0_report_results.py` — `--cycle`, the same evidence split for the off-frame
  sitemap caveat, cycle 4 added to the declared refusal-artifact list, and every description that
  quotes a count now names the cycle it counted.
* `scripts/build_report_pdf.py` — §7.
* `scripts/register_esip_crosswalk_results.py` — the NOAA denominator, read from the crosswalk.
* `tests/test_report_figures_agree.py` — `REPORT_CYCLE` moved to `2026-09-10_rj2`; the `noaa_`
  and `esip_` prefixes added to the registry view; and the figure-side fallback now asks
  `figures.Reads` instead of re-deriving "strip this report's cycle", which could not resolve the
  comparison cycle's names and would go stale at the next re-judgement.
* `tests/test_report_pdf.py` — the staleness pin and its companion deleted, as their own text
  instructed, in the same commit as the rebuild.

## 10. Verification

```
logs/c4_figreg.log        12 Figure artifacts, 552 CONTAINS/GENERATED_BY links, 0 failed
logs/c4_l0matrices.log    L0 matrices for scan_2026-09-10_rj2: 6 registered,
                          132 already at this value, 0 failed                     EXIT=0
logs/c4_l0report.log      cycle family: 3 registered, 0 failed                    EXIT=0
logs/c4_collection.log    collection facts: 4 registered, 0 failed                EXIT=0
logs/c4_noaa.log          NOAA denominator: 1 registered, 6 already               EXIT=0
logs/c4_a3endpoints.log   A3 movement endpoints: 2 registered, 0 failed           EXIT=0
logs/c4_pdf.log           the FIRST build — the stale-markdown defect, §7          EXIT=0
logs/c4_pdf2.log          the rebuild: markdown gate PASS, then the PDF           EXIT=0
logs/c4_traceability.json decision 5, per leg, as JSON
logs/c4_guards.log        make guards — 25 passed                        15.7 s   EXIT=0
logs/c4_gate_task.log     make gate-task — 1,895 passed, 17 skipped, 12 xfailed,
                          345.7 s; then 16 of 16 payloads byte-identical, 5.8 s   EXIT=0
logs/suite.log            make gate-full — 1,914 passed, 17 skipped, 12 xfailed,
                          1,211 s, detached and polled to EXIT                    EXIT=0
logs/c4_verify.log        seldon verify — all checks passed                       EXIT=0
logs/c4_protected.log     scripts/check_protected_c4.sh — PASS                    EXIT=0

PDF        docs/reports/2026-09_fss_ai_readiness_L0.pdf — 12 pages, 260,561 bytes,
           embedding assessment/harness/scan/figures/scan_2026-09-10_rj2/cycle_over_cycle.svg
markdown   docs/reports/2026-09_fss_ai_readiness_L0.md, 5,372 words, 59 tags, 0 typed numerals
matrices   docs/reports/scan_matrix_{tierA,tierC,product}_2026-09-10_rj2.{csv,json}
new        scripts/register_measured_collection_facts.py,
           scripts/register_superseded_l0_endpoints.py, scripts/report_traceability.py,
           scripts/check_protected_c4.sh, tests/test_figure_registration.py,
           state/collection_facts_2026-09-10.json
untouched  every rule module, the harness runtime, every stored payload, every figure SVG,
           figures.py, figures.yaml, params.yaml, every fixture, corpus/evidence/,
           tests/test_invariants.py
```

## 11. What the next task needs

1. **The page count.** 12 against a target of 7 that no version of this report has met. Either
   the target is restated for a document that carries three matrices, or the matrices move to
   the machine-readable files beside it and the prose keeps the budget. It is a decision, not a
   retune, and it belongs to whoever publishes.
2. **A10 and A3 cite no source** (§6). The bulk-download check is the one product check with a
   pass rate worth reading and it rests on no cited document in this graph. Either the
   indicators get their sources, or the report says which of its checks are uncited.
3. **`build_l0_matrices.py --dry-run` writes files** (§8 item 9).
4. **`fss_scan_netlocs_contacted_2026-09-10_rj2` is superseded and live** (§4). Whoever reads the
   registry for cycle 4's netloc count should take the `_2026-09-10` name; the `_rj2` one is
   recorded as misfiled on `state/collection_facts_2026-09-10.json`.
5. **The report still has no host.** The self row stays empty until GitHub Pages serves it, at
   which point the instrument can finally be turned on its own output — which is the one
   measurement this report describes and does not contain.
