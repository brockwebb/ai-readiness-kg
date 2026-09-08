# CC Task: eda-and-charts: the week's progress and gap views, every number re-derived from the graph

**Date:** 2026-09-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-07_scan_run_RESULT.md`)
**Fulfils:** ResearchTask `eda-and-charts` (`c1ede3d9`); predecessor `scan-run` (`e3e38014`) completed 2026-09-07T11:38Z.
**Spend:** zero model calls (the existing test asserts it). **Network: none.** This task scans nothing and fetches nothing; it reads the graph, the framework JSON, the fixtures, and git history.
**Zero edits to:** any rule module, `params.yaml`, the target list, the G1 harness, `assessment/cq/*.yaml`, indicator content in the framework JSON. The only framework write permitted is the projection in §0, which changes no cell.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-07_eda_and_charts_ADDENDUM*.md` before starting.**

---

## Premises, verified against the graph 2026-09-07 before this file was written

- Cycle `scan_2026-09-07`, `params_hash 4a1350802619…`: 437 Findings in the graph = 390 product (67 pass / 278 fail / 45 error) + 14 A12 host (8/4/1 na/1 error) + 33 control. Matches the RESULT and `scan_findings` (404 = 390 + 14; the RESULT's §6.4 calls the 404 "product-surface Findings", which is wrong: the single `not_applicable` is A12 on EIA, a host Finding; product-surface `not_applicable` is 0).
- 102 Results carry the cycle string; per-leg pass rates carry Wilson bounds in their description text only, not as separate numeric Results.
- **The graph's `AssessmentIndicator` projection is stale.** Graph: 2 `measured`, 46 `specified`, no `A12` node, no `harness_built`. Framework JSON: 16 `measured`, 32 `specified`, 1 `harness_built` (E5), plus A12 `specified`/candidate (49 nodes). The RESULT's "16 of 48 measured" is true of the file and false of the graph, because `scan-run` moved status in the JSON and never re-projected. The freeze task projected once on 2026-09-06 and nothing since. This is Desktop's premise defect: the scan-run task file demanded "graph is the source of truth" and never named the projection step.
- Two Results the scan-run task §4 demanded were not registered and the RESULT does not say so: `scan_rederived_findings` for this cycle (graph still holds the smoke cycle's 286 under the bare name; this cycle's 437 is unregistered) and `scan_params_hash`. The second was Desktop's defect: a hash is not a numeric value and cannot be a Result; the hash already rides on every Result description. Drop it. Register the first under the dated name.

## 0. Projection parity, before any chart (precondition, not the gate)

1. Re-run the framework-to-graph projection recorded in `cc_tasks/2026-09-06_freeze_and_framework_graph_RESULT.md`. Do not reconstruct it; use the script that RESULT names.
2. Assert with labelled Cypher: `AssessmentIndicator` count and per-status counts equal the JSON's (`measured` 16, `specified` 32 + A12, `harness_built` 1); A12 present and marked candidate.
3. Add a test that fails when the JSON and the graph disagree on any indicator's `measurement_status`, and wire it into whatever the round-trip gate runs under, so the next status move cannot leave the graph behind. Append **DD-056** to `docs/design_decisions.md`: the framework JSON is the record (DD-050), the graph is its projection, and any write that moves `measurement_status` re-projects in the same step; the parity test is the enforcement. In the same DD, record the naming rule the RESULT §7.4 asked for: every cycle- or date-scoped Result name carries `_YYYY-MM-DD`; bare cycle names are retired after this task.

## 1. What the page already has, audited

`docs/progress/index.html` (served at `readiness.home`) gained the agencies × legs matrix and a per-leg pass-rate chart in `scan-run`. Do not redraw them from memory. For each existing figure: re-derive every plotted number from the graph (Findings by `params_hash` and `indicator_code`), compare to the registered Result, and record the check in the RESULT. Then make these changes only where the audit or the items below require them:

- **Per-leg pass rates:** the datum at 0/23 is the interval, not the point. If the chart is a bar with an error bar, replace it with a dot-and-interval plot (Cleveland, *The Elements of Graphing Data*, 1985; dot plots over bars for estimates with uncertainty). Print `pass/n` and the Wilson bounds (Brown, Cai, DasGupta 2001, *Statistical Science* 16(2), already the project's interval) beside each leg. Print the `error` count per leg in a muted column so the excluded-from-denominator surfaces are visible on the same row. Legs sorted by rate; state on the figure that legs are not comparable to each other and that there is no composite.
- **Matrix:** add the two control fixtures as reference rows above the agencies, visibly marked as fixtures. Those rows are "floors from the fixtures": the instrument's demonstrated ability to return all-pass and all-fail. Add four rows for BLS, BTS, NCES, ORES marked `no admitted surface` in a fill distinct from `error`, so the hole named in RESULT §5 is on the chart and not only in prose. Colour scale for verdicts: Okabe-Ito palette (Okabe & Ito 2008, colourblind-safe); do not encode a verdict by hue alone, keep the glyph.

## 2. New views

Inline SVG, no CDN, every fraction printed with numerator and denominator, every source Result named in a `<title>` or caption.

- **2a. Gap map by criterion.** Seven criteria (A..G). For each: indicators by `measurement_status` (`measured`, `harness_built`, `specified`), stacked horizontal counts, A12 drawn separately as candidate and excluded from the 48. Source: the graph after §0. Register per-criterion measured counts as Results: `framework_measured_<criterion>_2026-09-07`, and the totals `framework_measured_2026-09-07` (16), `framework_specified_2026-09-07`, `framework_harness_built_2026-09-07`.
- **2b. Positive-progress view.** A burn-up of `measured` indicators against the 48 total by date (Anderson, *Kanban*, 2010, ch. 12 for the form; it is a cumulative count, nothing more). Derive the series from the git history of `framework/ai_readiness_framework.json`: for each commit that changed any `measurement_status`, the count of `measured` at that commit and its author date. Expect two points this week (2 on 2026-09-06, 16 on 2026-09-07); draw them, do not interpolate, and the chart grows as the week does. If the history technique cannot recover a point, say so on the chart; do not backfill from memory.
- **2c. Instrument coverage.** One small figure: 14 hosts by observation outcome for this cycle (product surface admitted and observed: 9; admitted, every leg error: STATCAN; no admitted surface: 4). Source: `scan_agencies_unobservable`, `scan_agencies_with_no_admitted_surface`, `scan_targets_hosts`. This is the figure a reader of the pass rates needs first.

## 3. Register

- `scan_rederived_findings_2026-09-07` = 437 (from the RESULT's gate line; re-derive by re-running the gate, not by copying).
- The Results in §2a. Every one carries `cycle: scan_2026-09-07` where cycle-scoped, the `params_hash`, and a description that states its denominator.
- Link each new chart's data to the Results it draws, by whatever edge the freeze task used for the existing charts; do not invent an edge type.

## 4. Gate (one)

**Page-to-graph parity.** A check script re-derives, from labelled Cypher alone, every number printed on `docs/progress/index.html` (pass, fail, error, n, rate, both Wilson bounds per leg; per-criterion counts; host outcome counts; burn-up points from git) and asserts each equals both the rendered value and the registered Result. Any mismatch: **write nothing to the page, register nothing, report.** The check runs in `pytest` so `seldon verify` before commit catches drift.

## 5. Report

RESULT: `cc_tasks/2026-09-07_eda_and_charts_RESULT.md`. Lead with the §0 parity result and the §4 gate, then the audit of the two existing figures (what changed and why), then the three new views with their numbers, then every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on protected files. `seldon cc complete`; move `c1ede3d9` to completed with this RESULT as evidence; commit, push.

**SEQUENCING:** §0 (hard stop on parity failure) → §1 → §2 → §3 → §4 → §5.
