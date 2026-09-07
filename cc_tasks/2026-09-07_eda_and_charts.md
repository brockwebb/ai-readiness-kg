# CC Task — eda-and-charts: the 2026-09-07 cycle as four figures, every number a registered Result

**Date:** 2026-09-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-07_scan_run_RESULT.md`; every count below was re-read from the Result registry by Cypher on 2026-09-07, not from the RESULT prose)
**Fulfils:** ResearchTask `eda-and-charts` (`c1ede3d9`). Predecessor `scan-run` (`e3e38014`) completed 11:38Z. **Runs after `cc_tasks/2026-09-07_framework_projection_repair.md`** and reads the graph that task repairs; if that task's RESULT reports its gate failed, stop here and report.
**Spend:** zero model calls. No network.

**Premise (verified):** 149 Results exist for the cycle and the framework snapshots, all `proposed`, all named; per leg for 15 legs: `scan_<leg>_pass`, `_fail`, `_error`, `_not_applicable`, `_applicable_n` (= 23 on every leg), `_pass_rate`; cycle: `scan_surfaces` 40, `scan_findings` 404, `scan_observations` 2018, `scan_control_findings_2026-09-07` 33, `scan_surfaces_unobservable` 3, `scan_agencies_unobservable` 1, `scan_agencies_with_no_admitted_surface` 4, `scan_hosts_refusing_or_unreachable` 5; A12 candidate counts `scan_a12_pass` 8 / `_fail` 4 / `_not_applicable` 1 / `_error` 1; framework snapshots `framework_indicators_measured_2026-09-07` 16, `_harness_built_2026-09-07` 1, `_specified_2026-09-07` 31, `framework_indicators_harness_built_after_review` 15 (02:16Z). DataFile `scan_matrix_2026-09-07` (`f2e33667`) holds the 26 × 15 verdict matrix. **Not registered:** any Wilson bound (the RESULT quotes 15 intervals from nowhere in the registry), the 2026-09-06 snapshot counts, per-criterion status counts. `error_class` on the log misfiles ECONNRESET as `dns` (RESULT §6.2), so no figure in this task breaks errors out by class.

**Operator constraints in force (not re-decided here):** no composite score; no ranking of agencies; legs are not comparable across legs and no figure may imply they are; every fraction printed with its count; unobservable and un-admitted agencies shown, never dropped; all rendering static, inline SVG, no CDN; the page is served through webdesktop or not at all.

**Zero edits to:** any rule module, `params.yaml`, the target list, events, the G1 harness, `assessment/cq/*.yaml`, `framework/ai_readiness_framework.json`, any prior cc_task or RESULT.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-07_eda_and_charts_ADDENDUM*.md` before starting.**

---

## 0. Grounding (prior art the figures are built on; cite in the RESULT and the page footer)
- Intervals: Wilson (1927, JASA 22:209); Brown, Cai and DasGupta (2001, Statist. Sci. 16:101) and Newcombe (1998, Stat. Med. 17:857) both recommend Wilson over Wald at small n and at 0 or n successes. Already this harness's convention; this task makes the bounds registered Results instead of prose.
- Zero counts: Hanley and Lippman-Hand (1983, JAMA 249:1743), the rule of three: with 0 events in n, the 95% upper bound is about 3/n (3/23 = 0.13, against Wilson 0.14). Print the Wilson bound; footnote the rule of three as the reader's sanity check.
- Encoding: Cleveland and McGill (1984, JASA 79:531) and Cleveland (1985, *The Elements of Graphing Data*): position along a common scale beats length; use dot-and-interval plots, not bars, for the rates. Bars also assert a zero baseline as a claim, which for eight legs at 0/23 is the very point under caution (RESULT §9).
- Matrix: Bertin (1967/1983, *Semiology of Graphics*), the reorderable matrix. **Not reordered by pass count here**: reordering rows by score is a ranking of agencies, which is forbidden. Rows grouped by agency in a fixed order; columns grouped by criterion.
- Fractions: Gigerenzer and Hoffrage (1995, Psychol. Rev. 102:684): natural frequencies (`4/23`) beside every rate, never a bare percentage.
- Small multiples for the progress view: Tufte (1983, *The Visual Display of Quantitative Information*).

## 1. Register what the figures need, before drawing anything
- `scan_<leg>_wilson_lo_2026-09-07` and `scan_<leg>_wilson_hi_2026-09-07` for the 15 legs (30 Results), z = 1.959964, computed by **one** function `assessment/harness/scan/stats.py::wilson(k, n, z)` with a unit test against the closed form for (0, 23), (16, 23), (19, 23), (23, 23) and against the 2-dp values in the scan-run RESULT §4 table. Description states `k/n`, the observable-surface denominator, the cycle and `params_hash`.
- `framework_indicators_measured_2026-09-06`, `_harness_built_2026-09-06`, `_specified_2026-09-06` from `git show <kg-freeze-2026-09-06 commit>:framework/ai_readiness_framework.json` (expected 2 / 0 / 46, but register what the file says; the 09-06 projection still in Neo4j before the repair task showed 46 / 2).
- Per criterion, for the 2026-09-07 snapshot: `framework_<crit>_measured_2026-09-07`, `_harness_built_`, `_specified_` for the 7 criteria (21 Results), A12 excluded from every count (candidate).
- `scan_agencies_total` = 14 (13 SPD-1 principal agencies + StatCan), with the roster as provenance, so the "4 of 14 invisible" fraction has a registered denominator.
Cycle-suffixed names only (repair task §5 convention).

## 2. Four figures, as SVG files, each a Seldon `Figure` artifact linked to every Result it prints
Directory `assessment/harness/scan/figures/scan_2026-09-07/`. Generator `assessment/harness/scan/figures.py` reads **only** the Result registry by name and the `scan_matrix_2026-09-07` DataFile; the existing integer-literal lint is extended to this module so it cannot carry a number of its own. Fonts system default; no external resource of any kind.

**F1 `per_leg_pass_rate`** — dot at `pass_rate`, horizontal Wilson interval, `k/n` printed at each dot, legs grouped by criterion (A, B, D, F, G) and within a criterion sorted by rate; axis title states the denominator (`observable admitted surfaces, n = 23; 3 StatCan surfaces excluded as error`). A small mark per leg shows the control verdict (`passes_all` → pass, `fails_all` → fail) so a 0/23 leg is visibly a live rule and not a dead one: that is what "floors from the fixtures" means here. Caption: legs measure different constructs, no composite, one cycle, one client identity.

**F2 `agencies_by_legs_matrix`** — all **14** agencies, not 26 surfaces alone: surface rows grouped under their agency (fixed roster order), the 3 StatCan rows as `error` (TCP reset, unobservable), and one row each for BLS, BTS, ORES (`no admitted surface: host refused the identified client at listing`) and NCES (`no admitted surface: listing JS-only`) in a distinct fill. Two control rows at the top (`passes_all`, `fails_all`) as the instrument's ceiling and floor. Columns grouped by criterion. Four verdict fills plus the two "not observable" fills; a legend that names them. Nothing sorted by count.

**F3 `gap_map_by_criterion`** — 7 criteria × status (`specified` / `harness_built` / `measured`) as stacked horizontal counts with the count printed in each segment and the indicator codes listed beside the bar (48 codes total; A12 listed separately as candidate). This is the "where the gaps are" view the operator asked for; it says nothing about pass rates.

**F4 `progress_over_snapshots`** — three snapshots (2026-09-06 freeze; 2026-09-07 02:16Z after rule review; 2026-09-07 11:03Z after scan-run), each a stacked status count out of 48, x labelled with the datetime and the commit short-hash the snapshot was read from. Three points is what exists; do not draw a trend line through them.

Excluded on purpose, stated in the page: error-class breakdown (§6.2 misclassification), agency composites, agency rankings, cross-leg comparison language, A12 in any fraction.

## 3. Page and service
Re-run `framework_progress.py`: replace the per-leg bar chart from scan-run §8 with F1, replace the 26-row matrix with F2, add F3 and F4, inline SVG. Footer carries the §0 citations and the non-claims from scan-run RESULT §9 verbatim. Confirm the page is a webdesktop service per `/Users/brock/GitHub/webdesktop/ONBOARDING.md` (service YAML → regenerate → install-units → caddy reload; `curl -H 'Host: <sub>.home' localhost`); if it is not yet onboarded, onboard it there and cite the YAML path in the RESULT. Never hand-edit generated output or the live Caddyfile.

## 4. Gate (the one gate of this task)
`tests/test_scan_figures.py`:
- `wilson()` matches the closed form at the four (k, n) pairs above to 1e-9 and the RESULT's 2-dp table;
- the literal lint passes on `figures.py`;
- every numeric string rendered into any of the four SVGs (walk the generated text nodes) equals a registered Result by name and value, or is a count printed from `scan_matrix_2026-09-07`; unmatched numerals fail the test with the numeral and the figure named;
- re-derivation: for each of the 15 legs, `MATCH (f:Finding)-[:RULED_BY]->(r:Rule)-[:MEASURES]->(i:AssessmentIndicator {code: $code}) WHERE f.cycle = 'scan_2026-09-07' RETURN f.verdict, count(*)` (adapt property names to the projection; labelled Cypher on `seldon-ai-readiness-kg`) equals the registered `scan_<leg>_{pass,fail,error,not_applicable}` counts.
**Failure writes no figures and no page: report the diff and stop.**

## 5. Report
RESULT: `cc_tasks/2026-09-07_eda_and_charts_RESULT.md`. Lead with the §4 gate output, then the four figures by path with the Result names each one prints, then **what the figures show that the scan-run RESULT prose did not** (EDA observations, no inference, no recommendation), then every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on protected paths. `seldon cc complete`; move `c1ede3d9` to completed with this RESULT as evidence; commit, push.

**SEQUENCING:** repair task complete and green → §1 → §2 → §4 (hard stop) → §3 → §5. (§4 before §3 on purpose: the page is rendered only from figures that passed.)
