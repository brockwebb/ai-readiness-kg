# RESULT — eda-and-charts

**Task:** `cc_tasks/2026-09-07_eda_and_charts.md`
**Date:** 2026-09-07
**Predecessor:** `cc_tasks/2026-09-07_framework_projection_repair.md` — gate **PASS** (7/7), so this task ran. Its `Rule -[:MEASURES]-> AssessmentIndicator` edge is what makes §4's re-derivation check expressible at all.
**Spend:** zero model calls, zero network. The only processes launched were `pytest`, `seldon`, the two registration scripts, the figure generator and `curl` against `localhost`.

---

## 1. The gate (§4) — PASS

`tests/test_scan_figures.py`: **17 passed**, inside `python -m pytest tests/`.

| check | result |
|---|---|
| `wilson()` vs the closed form at (0,23), (16,23), (19,23), (23,23) | 4 passed, `< 1e-9` |
| `wilson()` vs the 2-dp table in `2026-09-07_scan_run_RESULT.md` §4 | 6 pairs, exact |
| one Wilson implementation in the harness (`Z == rollup._WILSON_Z`, no arithmetic in `stats.py`) | pass |
| the registered intervals equal the ones `scan_matrix_2026-09-07.json` holds, all 15 legs | pass |
| integer-literal lint on `figures.py` and `stats.py` | pass, 0 offenders |
| **every numeral in every figure resolves to an artifact** | pass, 0 unresolved |
| the gate itself catches a number from nowhere | 5 mutations, 5 caught |
| the figures print what the task asked (all legs, all agencies, control rows, candidate row, three snapshots, no trend line) | pass |
| no figure reaches the network (`http`, `<script>`, `<image>`, `xlink:href`, `@import`) | pass |
| **per-leg counts re-derive from the graph** through `Rule-[:MEASURES]->AssessmentIndicator` | 15 legs × 4 verdicts, 0 mismatches |

**How "every numeral is sourced" is enforced.** The task said to walk the SVG text nodes and match each numeral to a registered Result or a matrix count. Walking alone cannot distinguish `19` the pass count from `19` the y-coordinate that happened to be printed, so the generator declares the provenance instead: **every text node that contains a digit carries `data-src`**, and the test resolves it — `result:<name>` (one source per numeral, matched in order), `matrix:<count>`, `axis` (a tick from the declared scale in `figures.yaml`), or `label` (in which case every whitespace token carrying a digit must be in the framework's own code vocabulary). An unresolvable numeral fails with the numeral and the figure named.

That is a third allowed class the task did not name — the axis scale — and it is declared rather than assumed: `figures.yaml::rate_axis.ticks` is the only place ticks exist, the gate checks the rendered ticks against exactly that list, and the lint forbids the generator from carrying one of its own.

**The gate was watched failing.** `test_the_gate_catches_a_number_from_nowhere` appends five mutations to a real figure — a numeral that disagrees with its Result, a numeral with no `data-src`, a citation of an unregistered Result, an axis tick outside the declared scale, and a label token outside the vocabulary — and asserts each is reported. Without it, four figures that printed nothing would pass §4 perfectly.

**The re-derivation check (§4 last bullet), adapted.** Findings carry `params_hash`, not `cycle`; the cycle is identified by `4a1350802619…` and control targets are excluded by prefix:

```cypher
MATCH (f:Finding)-[:RULED_BY]->(:Rule)-[:MEASURES]->(:AssessmentIndicator {code: $code})
WHERE f.params_hash = $ph AND NOT f.target_doc_id STARTS WITH 'control:'
RETURN f.verdict, count(*)
```

`$code` comes from `rules.parse_rule_id(CURRENT[leg])`, not from string surgery on the leg name — `A11-declared` measures `A11`, and the derivation the repair task tested is the one used here.

---

## 2. What was registered before anything was drawn (§1)

`scripts/register_figure_results.py` — **76 Results**, idempotent at value, refusing at drift (AD-028):

| what | n | names |
|---|---:|---|
| Wilson bounds, 15 legs | 30 | `scan_<leg>_wilson_lo_2026-09-07`, `_hi_` |
| control fired, 15 legs | 15 | `scan_<leg>_control_fired_2026-09-07` |
| framework snapshots at three commits | 9 | `framework_indicators_<status>_{2026-09-06, after_review, 2026-09-07}` |
| per criterion × status | 21 | `framework_<A..G>_<status>_2026-09-07` |
| roster denominator | 1 | `scan_agencies_total_2026-09-07` |

Two of those five groups are not in the task's §1 list and are here because a figure needs them:

- **`scan_<leg>_control_fired_2026-09-07`.** F1's control mark was specified as a mark, which means the figure would have printed a fact from `state/scan_2026-09-07.json` that no artifact held. Registering it makes the mark checkable by the same gate as the dots. All 15 are 1: every leg's `CURRENT` rule returned `pass` on `passes_all` and `fail` on `fails_all` in this cycle.
- **`framework_indicators_{measured,specified}_after_review`.** F4's middle snapshot had exactly one of its three numbers registered (`..._harness_built_after_review` = 15). Two bars of a three-bar stack cannot come from prose.

**The interval registration cross-checks itself.** Before writing, the script recomputes each interval with `scan/stats.py` and refuses if it disagrees with the `ci95_low`/`ci95_high` already in `scan_matrix_2026-09-07.json`. It did not fire; the two agree to the sixth decimal, which is the evidence that there is one implementation and not two.

**`scan_agencies_total` was registered as `scan_agencies_total_2026-09-07`.** The task named it bare and then said "cycle-suffixed names only". DD-056, which the task cites, settles it: every Result a cycle registers carries its cycle. Named here because it is a deviation from the literal instruction.

**Prior art, adopted rather than re-derived.** `assessment/harness/scan/stats.py::wilson` is a **delegate** to `harness/rollup.py::wilson_interval` — the Wilson interval this repo already had, already pinned to the burn-close arithmetic by `assessment/tests/test_rollup.py`, and already the arithmetic that wrote the matrix file. Writing a second one would have been a second thing to be wrong, with a silent failure mode: two figures disagreeing in the third decimal and no way to say which is the instrument. A test asserts `stats.Z == rollup._WILSON_Z` and that `stats.py` contains no arithmetic of its own.

---

## 3. The four figures (§2)

Directory `assessment/harness/scan/figures/scan_2026-09-07/`. Generator `assessment/harness/scan/figures.py`; all geometry in `assessment/harness/scan/figures.yaml`; system fonts; inline SVG; no external resource of any kind.

| figure | file | prints (Results) | reads (Results) | data |
|---|---|---:|---:|---|
| **F1** `per_leg_pass_rate` | `per_leg_pass_rate.svg` | 60 | 90 | `scan_matrix_2026-09-07` |
| **F2** `agencies_by_legs_matrix` | `agencies_by_legs_matrix.svg` | 0 | 0 | `scan_matrix_2026-09-07` |
| **F3** `gap_map_by_criterion` | `gap_map_by_criterion.svg` | 13 | 21 | `ai_readiness_framework` |
| **F4** `progress_over_snapshots` | `progress_over_snapshots.svg` | 8 | 9 | the registry only |

*prints* = numerals rendered; *reads* = Results looked up, printed or not. The difference is not bookkeeping: F1's fifteen control marks are **decided** by `scan_<leg>_control_fired_2026-09-07` and never printed, so a provenance list built from the visible numbers would have missed fifteen dependencies. The generator records what it looked up (`data-reads` on the SVG root, written by a recording dict, so the list cannot go stale) and `scripts/register_scan_figures.py` reads it back to build the edges.

**Artifacts and edges.** Four `Figure` artifacts, `<name>_2026-09-07`, each with `caption` and `data_source`; **124 links** — 120 `Figure -[:CONTAINS]-> Result` and 4 `Figure -[:GENERATED_BY]-> Script (scan_figures)`. `CONTAINS` and `GENERATED_BY` are the domain's own declared endpoints for a Figure (`seldon/domain/research.yaml`); `COMPUTED_FROM` was tried first and correctly refused — a Figure cannot originate it. The domain declares **no** `Figure -> DataFile` edge at all, so the DataFiles a figure reads go on its `data_source` property, which the schema defines for exactly that. F2 is why this matters: it prints no registered number, its whole content is the matrix, and without `data_source` it would be the one figure with no provenance of any kind.

**Encoding choices and the prior art behind them** (also in the page footer):
- **F1 is a dot-and-interval plot, not bars** — Cleveland & McGill (1984, *JASA* 79:531); Cleveland (1985). Position along a common scale beats length, and a bar asserts a zero baseline as a claim, which is exactly the claim under caution when eight legs sit at 0/23. The interval is drawn through the dot, `k/n` and `[lo, hi]` are printed beside it (Gigerenzer & Hoffrage 1995: a natural frequency beside every rate), and legs are grouped by criterion and sorted **only within** a criterion — sorting across would invite the cross-leg comparison the caption forbids.
- **F2 is Bertin's matrix (1967/1983) deliberately NOT reordered.** Rows in roster order, columns grouped by criterion. Reordering rows by pass count is a ranking of agencies.
- **F4 has no trend line**, asserted by a test (`"<line" not in f4`). Three points, two of them hours apart; a line would say they were a rate.
- **Zero counts**: the page footnotes Hanley & Lippman-Hand (1983) rule of three — 3/23 = 0.13 against the Wilson 0.14 printed on the figure — as the reader's sanity check, not as the number quoted.

---

## 4. Page and service (§3)

`scripts/framework_progress.py` now **inlines the generated SVGs** rather than drawing its own. `matrix_svg()` and `rate_bars()` are gone: they carried their own geometry and their own numbers, and nothing gated either. The page reads the files from disk rather than re-rendering, because the SVG on disk is the one the gate checked — rendering a second copy at page time would put an ungated figure in front of a reader.

Footer carries the §0 citations and, verbatim, the non-claims paragraph from `2026-09-07_scan_run_RESULT.md` §9, plus the four exclusions the task listed (no error-class breakdown — `error_class` misfiles ECONNRESET as `dns`, scan-run §6.2; no agency composite; no ranking; no cross-leg comparison; A12 in no fraction).

**The page was already a webdesktop service** — `/Users/brock/GitHub/webdesktop/services/readiness.yaml`, a **static** service (`static_root: ~/GitHub/ai-readiness-kg/docs/progress`), onboarded by `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §4. No YAML change, no regenerate, no `install-units.sh`, no Caddy reload: nothing about the service definition changed, only the bytes it serves. Confirmed live:

```
$ curl -s -o /dev/null -w '%{http_code} %{size_download}' -H 'Host: readiness.home' http://localhost/
200 113145
```
— the same 113,145 bytes as `docs/progress/index.html`, containing all four figures and the footer. Nothing generated was hand-edited; the Caddyfile was not touched.

---

## 5. What the figures show that the scan-run RESULT prose did not

Observations only. No inference, no recommendation, no composite, no ranking.

**5.1 A4 and A11-declared are not merely equal in count — they are the same column.** The RESULT table shows both at 19/4/3. F2 shows the nineteen are the **same nineteen surfaces** and the four failures are the same four. Two indicators with different constructs (crawler access declared, AI-crawler policy declared) produced an identical verdict vector across every observable surface in this cycle. A table of counts cannot show that; a matrix cannot hide it.

**5.2 A3 and B3 are equal in count and are NOT the same surfaces.** Both are 4/23 in the table. Three of the four coincide; the fourth differs (A3 also passes an NCHS flagship page, B3 an NCSES one). The identical row in the RESULT's §4 table is a coincidence of arithmetic, and reading it as "the same products" would have been wrong.

**5.3 The eight zeros are uniform, not concentrated.** A1, A2, A6, A8, A9, D1, D4 and F4 have **no pass on any surface of any agency** — the columns in F2 are solid, with no lighter patch anywhere. The prose said "eight of fifteen legs are at zero"; what the matrix adds is that the zero is not one or two agencies dragging a mean down, because there is no mean and there is nothing to drag.

**5.4 The failures on the passing legs sit in a few agencies, and the two legs fail in different places.** A4/A11-declared fail on four surfaces (three Census, one EIA). A10 fails on seven, and the seven are not those four: NCHS ×3, EIA ×2, ERS ×1, NCSES ×1. Where the instrument sees a failure on a leg that mostly passes, it is not the same surface twice.

**5.5 G1-D passes only on flagship pages, never on a machine entry point** — three passes, all flagship, none of the seven observable machine surfaces. A5 is the mirror: two passes, one flagship and one machine, both NCSES. Neither fact is in the counts.

**5.6 Two whole criteria have nothing measured.** F3: criterion **C** (5 indicators) and criterion **E** (9) are at zero measured — 14 of 48 indicators sit in criteria the harness has not touched at all, against criterion A where 10 of 11 are measured. The scan-run RESULT reported 16 measured of 48 as one fraction; where those 16 are is a different shape.

**5.7 `harness_built` is a transient, and it takes three snapshots to see it.** F4: 0 → **15** → 1. The status existed in bulk for roughly nine hours between the rule review and the scan run. Read from either end alone it looks like a rounding error; read across the three it is the whole middle of the week.

**5.8 Every control mark on F1 is filled.** All fifteen rules returned `pass` on the passing fixture and `fail` on the failing one in this same cycle. This is the fact that makes 5.3 readable as a measurement rather than as fifteen dead rules, and it is why the mark is on the figure and not in a footnote.

---

## 6. Verification

| check | result |
|---|---|
| `python -m pytest tests/ assessment/` | **1,482 passed, 2 skipped** (was 1,465 + 2; +17 = `tests/test_scan_figures.py`) |
| `tests/test_scan_figures.py` | **17 passed** |
| `seldon verify` | **All checks passed** — 25,747 events readable, relationship types canonical, precedence acyclic |
| `git diff` on protected paths | **empty** — `framework/ai_readiness_framework.json`, every `rules/rule_*.py`, `params.yaml`, `targets.yaml`, `assessment/cq/*.yaml`, `events/`, every prior `*_RESULT.md`, the G1 harness (`assessment/harness/run.py`, `rollup.py`, `probes/`), and this task's own file |
| `curl -H 'Host: readiness.home' localhost` | 200, 113,145 bytes, four figures present |

---

## 7. Premises this task got wrong

**7.1 There is already a Wilson implementation in this repo, and §1 asked for a second.** `harness/rollup.py::wilson_interval` computed the G1 intervals, is pinned by `assessment/tests/test_rollup.py`, and wrote the `ci95` fields in `scan_matrix_2026-09-07.json` that §1's own cross-check compares against. `scan/stats.py` is therefore a delegate. Following §1 literally would have produced the exact defect the harness recorded against duplicated guards (`_common.served`, four modules, one crash).

**7.2 §2's "reads only the Result registry and the `scan_matrix` DataFile" is contradicted by §2's own F3.** F3 requires the indicator **codes** listed beside each bar, and no registered Result holds a code. The generator reads `framework/ai_readiness_framework.json` as a third source for names only — never for a number — and the `data-src="label"` class in the gate is what keeps that honest: a label may carry a digit only if the token is in the framework's own code vocabulary.

**7.3 §4's numeral rule needs a third class, and the axis is it.** A rate axis with no tick labels is not a common scale, and Cleveland's own argument for F1's encoding depends on there being one. The ticks are declared in `figures.yaml`, checked against the rendered figure, and are the only numerals in any figure that are neither a Result nor a matrix count.

**7.4 `scan_agencies_total` cannot be registered under the name §1 gives it.** §1 names it bare and then says "cycle-suffixed names only". Registered as `scan_agencies_total_2026-09-07` on DD-056, which §1 cites two lines earlier.

**7.5 F4's middle snapshot had one of its three numbers.** §1 asked for the 2026-09-06 snapshot and the per-criterion 2026-09-07 counts, and left the 2026-09-07 02:54Z snapshot with only `framework_indicators_harness_built_after_review` registered. Two more were registered under the same `_after_review` suffix rather than inventing a second naming for one snapshot.

**7.6 The task's snapshot times are the write-back times, not the commit times.** §2 F4 says "2026-09-07 02:16Z" and "11:03Z"; the commits whose bytes the counts were actually read from are `72cdec6` at **02:54:35Z** and `52ec048` at **11:38:29Z**. The figure carries the commit time and the short hash, because that is what a reader can re-read.

**7.7 A `Figure` cannot originate `COMPUTED_FROM`, and `seldon artifact create` does not enforce a unique Figure name.** The first registration run created four Figures and had all 124 links refused (`'Figure' cannot originate a 'computed_from' relationship`); the second, before the guard existed, minted four twins and then failed differently (`Multiple artifacts with name=…`). The four orphans are **not deleted** — an artifact event is never removed — but marked `state=superseded` with `superseded_by_artifact_id` pointing at the live node and a description saying why. `superseded_by` could not be used as an edge: the domain restricts it to `ResearchTask` sources. `register_scan_figures.py` now looks up the live Figure by name before creating one, and refuses outright if it finds more than one. My defect, not the task's.

**7.8 `pytest assessment/` still writes control-fixture evidence blobs into `corpus/evidence/scan/`** — 47 of them per run, content-addressed on a payload containing the fixture server's ephemeral port, so the names differ every time and the set grows without bound. Cleaned with `git clean -fd` scoped to that path, as in the repair task's RESULT §7.8. Still unfixed, still belonging to whoever next touches the fixture harness.

---

## 8. What these figures do not claim

Everything in `2026-09-07_scan_run_RESULT.md` §9, unchanged and quoted verbatim in the page footer. The figures add no claim to that cycle; they make its numbers traceable and its shape visible. Specifically:

- **No composite and no ranking.** F2's rows are in roster order and nothing on any figure sums across legs. §5's observations are about columns and about which surfaces sit in a column — never about how many legs a surface or an agency passed, because that number is a score and this instrument has not earned one.
- **F3 is coverage, not quality.** An indicator at `measured` can be measured and failing on every surface; eight of them are.
- **F4's three points are three points.** Two of the intervals are hours; there is no rate here and no line drawn as if there were.
- **A12 appears in no fraction on any figure.** It is drawn in F3 as its own row, labelled "candidate (not counted)", which is DD-054 rendered rather than remembered.
