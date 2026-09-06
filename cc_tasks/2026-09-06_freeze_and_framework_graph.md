# CC Task — Freeze the KG; the assessment framework becomes a graph; register the week's chain

**Date:** 2026-09-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session (priority pivot: instrument first, ER research resumes after)
**Follows:** `1a561df4` (completed). Zero model spend in this task.
**Premise:**
- `docs/crosswalk/usafacts_operationalization_skeleton.md` v0.2.9 is the framework of record: 45 indicators across A (11), B (6), C (5), D (4), E (9), F (6), G (6); each typed AUTO/DOC/EVAL; tiered `public` / `agency_instrumented` / `paid` (schema v0.3 `Measure.tier`); 25 evidenced, 20 gaps. G1 is a two-leg indicator frozen at v2 (DD-036). `docs/crosswalk/assessment_protocol.md` governs where the two differ.
- `assessment/harness/` holds the G1 reference implementation (`g1_declared.py`, `g1_preservation.py`, fixtures, 17 admitted product surfaces under epoch `g1sfc-2026-09-03`).
- KG state after `1a561df4`: vocabulary epoch 1; ER population precision 0.9945 (DD-045 PASS); bare spans 78 of 13,977; 991 `grounding_thin`; Issue `e21b9ab3` open.
- `kg/schema.yaml` has no label for the assessment layer; the KG's `Framework` label is taken (506 extracted nodes) and `Construct` means construct arm. Assessment-layer labels must not collide.
**Zero edits to:** `assessment/cq/*.yaml`, the G1 harness and fixtures, the vocabulary log, the skeleton's indicator *content* (the JSON is derived from it in this task, not the reverse — that flips in §2.4 only after the round-trip proves equal).

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-06_freeze_and_framework_graph_ADDENDUM*.md` before starting.** Read `assessment_protocol.md` in full before §2.

---

## 0. Prior art (record in DD-050)
- **NIST OSCAL** (Open Security Controls Assessment Language): catalog → profile → assessment-plan → assessment-results, with `observation`, `evidence`, `finding` as first-class objects. The layering here is OSCAL's; the schema is not.
- **F-UJI** (Devaraju & Huber 2021, *Patterns* 2(10)): metric definitions as YAML with `metric_identifier`, `metric_tests`, and per-test `evidence`; automated assessment against a landing page.
- **FAIR maturity indicators** (Wilkinson et al. 2019, *Scientific Data* 6:174): each indicator as a machine-readable test with a defined pass condition.
- **Progress at every level with partial completion** is a coverage model, not a maturity ladder: per-level completion = evidenced-and-measured indicators over indicators in scope for the tier. Reported as fractions with counts, never as a single composite (protocol §3 and the G1 no-composite rule extend to the framework).

## 1. Freeze — DD-049
Append DD-049:
1. **KG good-enough ruling.** Epoch 1 vocabulary plus the `1a561df4` span backfill is the instrument's validity layer for the September–January cycle. Consumers: this framework graph, the memo/deck, the papers.
2. **`accessibility` ruling.** The gold labels P089/P090 were formed on a bare span; with the span supplied, MITRE's "accessibility" is a data-pillar activity, and the judge's `same_sense` is the reading the text supports. Gold pairs rated on a bare span are re-rated in the regold; the 2026-09-05 labels stand as the record of that sheet. Stratum E's 0.889 is recorded as largely an artifact of Issue `e21b9ab3`.
3. **Scheduled ER debt**, each registered as a `proposed` ResearchTask with description and a `blocks` edge to a placeholder task `er_research_resumes` (state proposed): full Phase B homograph pass on backfilled spans (212 terms); token-set aliases + epoch-1 term dedupe (`rdf` ×3, `sdmx` ×2) with a control drawn from a classified miss list; stratum-D band lowering to 0.70 through the judge; the regold draw (allocation `er_regold_allocation_2026-09-06b`, seed 20260906); Issue `e21b9ab3` disposition (78 remaining + 991 thin + extractor rule).
4. Tag the repo `kg-freeze-2026-09-06` after the rest of this task lands.

## 2. The framework as a graph

### 2.1 Schema epoch v0.4 — assessment layer (through the schema's own §6 review process; record as DD-051)
New labels, prefixed to avoid collision: `AssessmentCriterion` (A–G), `AssessmentConstruct` (the 45 rows' construct column), `AssessmentIndicator` (the 45), `MeasurementSpec` (how an indicator is obtained: one per indicator leg), `Observation` (a raw fact captured against a product, evidence-first), `Finding` (a versioned-rule verdict over Observations). Edges: `DECOMPOSES_INTO` (Criterion→Construct→Indicator), `EVIDENCED_BY` (Indicator→Document, the doc_ids in the Evidence cells, with the DD-024 grounding span where one was captured), `MEASURED_BY` (Indicator→MeasurementSpec), `OBSERVED_ON` (Observation→product surface Document), `SUPPORTS` (Observation→Finding), `RULED_BY` (Finding→a versioned rule id). Fold CQ-27's gap in here: `OPERATIONALIZED_BY: Framework→Instrument` so Issue `2a2b6461` closes under the same epoch. Properties on `AssessmentIndicator`: `code` (A1…G6, G1-D/G1-O as two indicator nodes under one construct), `type` (AUTO/DOC/EVAL, multi-valued where the skeleton says so), `tier`, `status`, `measurement_status ∈ {specified, harness_built, measured}`, `frontier` flag with `as_of` where the skeleton dates it.

### 2.2 Source of truth: `framework/ai_readiness_framework.json`
Plain node/edge JSON (a `nodes` array and an `edges` array, each with `id`, labels, properties; JSON-LD `@context` optional and not required). Populate from the skeleton v0.2.9 **mechanically** — parse the seven tables; every cell becomes a property; every `doc_id` in an Evidence cell becomes an `EVIDENCED_BY` edge **only if it exists in `corpus/manifest.json`**, else a `gap` marker with the cell's stated reason. Internal references ("internal: DD-019", "methodology §3") become `EVIDENCED_BY_INTERNAL` with the artifact path. Nothing is invented; a cell that can't be parsed is listed in the RESULT, not guessed.

### 2.3 Round trip, gated
`scripts/render_framework.py` renders the JSON back to the skeleton's seven tables. Gate: the rendered tables equal v0.2.9's tables cell-for-cell after whitespace normalisation, **or** every diff is listed with the reason (a cell the parser can't represent). Zero unexplained diffs or the JSON is not adopted. Load the JSON into Neo4j under the v0.4 labels; a labelled count test proves 45 indicators (46 nodes with the G1 split), 7 criteria, and that every `EVIDENCED_BY` target exists.

### 2.4 Flip the source of truth
On a passing §2.3: DD-050 records that `framework/ai_readiness_framework.json` is the framework of record and the skeleton's §2–§5d tables are a rendered projection; the skeleton header gets a one-line note saying so with the render command. The skeleton's prose sections (§1, §1b, §6–§10) stay authored markdown.

## 3. MeasurementSpec for every `public`-tier AUTO indicator
For each (A1, A2, A3, A4, A5, A6, A8, A9, A10, A11-declared leg, C4-auto leg, D1, D4, E5, F2, F3, F4, G1-D, G3): a `MeasurementSpec` node with `signal` (what is observed, e.g. "HTTP GET /robots.txt; parse; Allow/Disallow for the product path per UA in the AI-crawler list"), `collector` (an open-source tool or library, named and pinned: `httpx`, `scrapy`, `extruct`, `protego`, `ultimate-sitemap-parser`, the Project Open Data `data.json` validator, `pyshacl` + DCAT-AP shapes, Lighthouse, **F-UJI** where the indicator overlaps a FAIR metric — name the F-UJI metric id), `evidence_kind` (raw capture retained: response body hash, headers, timestamp, UA), `rule_id` (a placeholder `RULE-<code>-v0` — rules are written in the harness task, not here), `prior_art` (doc_id or citation). No collector is installed or run here. Where no open-source collector exists, say so and mark `collector: none_known`; that is the only allowed use of the Screaming Frog fallback later, and it is recorded, not assumed. DOC and EVAL indicators get a `MeasurementSpec` with `mode: checklist` or `mode: harness` and a pointer (G1-O points at `g1_preservation.py`, instrument frozen); no further design.

## 4. Progress model and the first chart
`scripts/framework_progress.py`: for each level (criterion, construct, tier, whole) compute counts and fractions of indicators at each `measurement_status`, evidenced vs gap, and by type — the coverage model from §0, fractions with counts, no composite. Emit `docs/progress/framework_progress_2026-09-06.json` (snapshot DataFile) and one static HTML page `docs/progress/index.html` (matplotlib PNGs or inline SVG, no server, no JS framework) showing: indicators by criterion × measurement_status; evidenced/gap by criterion; public-tier AUTO indicators with a named collector vs `none_known`. Onboard the page as a webdesktop service YAML per `ONBOARDING.md` (static, `readiness.home` or the name that convention gives). Register the fractions as Results.

## 5. Register the week's chain (Seldon-native plan)
Create these ResearchTasks, `proposed`, with `blocks` edges in this order, so `seldon go` shows the path:
1. `harness-scaffold` — evidence-first collector framework for the §3 specs; versioned rules (§6b.5: observed facts stored raw, warnings by rule); smoke-run against the 17 admitted product surfaces; F-UJI wired for its subset. Blocks 2.
2. `scan-targets` — target list: the 17 surfaces plus one flagship product page and catalog endpoint per principal statistical agency; registered as a snapshot DataFile with selection criteria stated. Blocks 3.
3. `scan-run` — parallel CC dispatch, one worker per agency, shared evidence schema, no shared mutable state; Observations written as events. Blocks 4.
4. `eda-and-charts` — per-indicator pass rates with Wilson intervals, evidence links, G1-D first; progress page updated; positive-progress and gap charts. Blocks 5.
5. `report-draft` — not due this week; placeholder.
Also register `er_research_resumes` (from §1.3) blocked by 5.

## 6. Reporting
RESULT: `cc_tasks/2026-09-06_freeze_and_framework_graph_RESULT.md`. Lead with the round-trip gate outcome and any unexplained diffs, then the indicator/evidence counts loaded, then the §3 table of collectors including every `none_known`, then the progress fractions. State every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on the protected files. Tag `kg-freeze-2026-09-06`. `seldon cc complete`, commit, push.

**SEQUENCING:** §1.1–1.3 → §2.1 → §2.2 → §2.3 (gate) → §2.4 → §3 → §4 → §5 → §1.4 tag → §6. §5 runs regardless of the §2.3 outcome; if §2.3 fails, the JSON is kept as a draft and the RESULT says the skeleton remains the record.
