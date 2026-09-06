# RESULT: the round trip passes clean, the framework is a graph, and the KG is frozen

**Task:** `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §0–§6. **No addenda** — globbed before starting, none exist. **Date:** 2026-09-06 UTC. **Zero model spend.** **Task file committed before execution** (`71cfedf`). `assessment_protocol.md` read in full before §2, as required.

## §2.3 — the adoption gate: **PASS, zero diffs of any kind**

| | |
|---|---:|
| indicator rows in skeleton v0.2.9 | 47 |
| rows rendered from the JSON | 47 |
| **unexplained diffs** | **0** |
| explained diffs | **0** |

Every one of the 47 rows round-trips **cell for cell** after whitespace normalisation — including G1, which is stored as two indicator nodes (DD-036's two-leg rule) and folded back into one row with its Type and Tier cells reconstructed from the legs. I had pre-declared that reconstruction as the one representable-difference class; it turned out not to be needed, because the reconstruction is exact.

**One diff did occur on the first attempt and it is worth recording.** A11's Tier cell is `` `agency_instrumented` (observed leg requires edge logs; declared leg stays `public`) `` — prose containing a second backticked token. Storing the tier as an enum and rendering it as `` `{enum}` `` cannot reproduce that. Fixed by storing **two** fields: `tier`, the enum the schema declares and the progress model groups on, and `tier_raw`, the cell verbatim, which is what the renderer emits. A test pins it.

**So §2.4 fired:** `framework/ai_readiness_framework.json` is the framework of record (DD-050) and the skeleton's §2–§5d tables are a rendered projection. The skeleton header carries a one-line note with the render command; its prose sections stay authored markdown.

## §2.2 / §2.3 — what loaded

| | |
|---|---:|
| AssessmentCriterion | **7** |
| AssessmentConstruct | **47** |
| **AssessmentIndicator** | **48** (47 rows, G1 split into G1-D and G1-O) |
| MeasurementSpec | 21 |
| `EVIDENCED_BY` edges to admitted Documents | **122** |
| `EVIDENCED_BY_INTERNAL` | 17 |
| indicators reachable from a criterion | **48 of 48** |
| unparseable rows | **0** |
| Evidence doc_ids in a cell but not in the manifest | 6 |

The 6 unmatched candidates are not missing documents: they are backticked tokens my `doc_id` pattern picks up that are not doc_ids — `acquisition_blocked` (a status word), `2026-08-27_chunked_vs_wholedoc_verdict.md` and `g1_preservation.py` (repo paths), and three corpus **epoch** names (`g1sfc-2026-09-03`, `g1eval-2026-09-02`, `g1srp-2026-09-03`). All are listed in the JSON rather than guessed at, exactly as §2.2 requires.

## §1 — the freeze (DD-049)

1. **Good enough, and what the claim rests on.** Vocabulary epoch 1 plus the `1a561df4` backfill is the validity layer for the September–January cycle. Not a claim that ER is finished — DD-045's PASS came with n_eff 21 and a precision lower bound under the floor. A claim about *sequencing*: the consumers are the framework graph, the memo/deck and the papers, and none is blocked by the residue.
2. **The `accessibility` ruling.** P089/P090 were rated on a bare span; with the span supplied, MITRE lists accessibility among data-pillar activities and the judge's `same_sense` is the reading the text supports. **The 2026-09-05 labels stand as the record of that sheet** — a gold label records what a rater saw, and rewriting it would destroy the only evidence that the span mattered. Those pairs are re-rated in the regold. Stratum E's 0.889 is recorded as largely an artifact of Issue `e21b9ab3`.
3. **ER debt scheduled**, five `proposed` ResearchTasks plus the `er_research_resumes` gate (`37476f34`).
4. **Tagged `kg-freeze-2026-09-06`.**

## §2.1 — schema epoch v0.4.0 (DD-051)

Bumped 0.3.8 → **0.4.0** through the schema doc's own §6 process.

**The assessment layer is deliberately *outside* `node_types` / `edge_types`.** Those two keys **are** the parser's whitelist — `schema_loader.py` says so in its docstring — so a label placed there is one a *model* can assert from a source document. The assessment layer is the instrument, not a finding about the literature, and an extraction able to mint an `AssessmentIndicator` would let a source document rewrite the framework measuring it. It lives in a sibling `assessment_layer:` block with `parser_visible: false`, and a test asserts the two sets are disjoint. Same reasoning that kept `Term` and `RESOLVES_TO` out in DD-044 §4.

`Observation` and `Finding` are separate so that **a rule change re-derives findings without re-collecting evidence** — OSCAL's split, and the one piece borrowed structurally rather than as layering.

**`operationalized_by: Framework → Instrument` joins the parser whitelist and closes Issue `2a2b6461`.** Unlike the assessment labels this one *is* extractable — a document really can say a framework is operationalised by an instrument. Existing extractions are **not** re-run; per schema §6 the targeted re-run flagging is the next task's.

## §3 — MeasurementSpecs: 20 AUTO legs, 15 with a collector, **5 `none_known`**

| leg | collector (pinned) | F-UJI |
|---|---|---|
| A1 | `httpx>=0.27` | |
| A2 | `httpx>=0.27` | **FsF-A1-03D** |
| A3 | `scrapy>=2.11` | |
| A4 | `protego>=0.3` | |
| A5 | `ultimate-sitemap-parser>=1.0` | |
| A6 | `extruct>=0.17` + `pyshacl>=0.26` | **FsF-F4-01M, FsF-I1-01M** |
| A8 | `httpx` + `extruct` | |
| A9 | `httpx` (frontier, as_of 2026-01) | |
| A10 | `lighthouse-cli>=12` | |
| A11-declared | `protego` | |
| B3 | `httpx` | |
| **C4-auto** | **none_known** | |
| D1 | `extruct` + `httpx` | **FsF-R1.1-01M** |
| D4 | Project Open Data v1.1 validator | |
| **E5** | **none_known** | |
| **F2** | **none_known** | |
| **F3** | **none_known** | |
| F4 | `httpx` | |
| G1-D | `g1_declared` (frozen, DD-036) | |
| **G3** | **none_known** | |
| G1-O | `g1_preservation` (mode: harness) | |

**The five `none_known` each have a stated reason**, and that is the only thing licensing a commercial fallback later: **C4-auto** needs a generative engine's citations, which is the EVAL half of the indicator; **E5** is a property of the harness's own cycle, not an observation of an external surface; **F2** and **F3** need *two vintages*, so a single-point scan cannot observe them at all; **G3** has no admitted source.

**Only 3 of 20 legs overlap an F-UJI metric, and that is the expected result.** F-UJI measures *metadata* FAIRness; this instrument measures *machine-consumability of a published product surface*. The ids above were read off f-uji.net's methods page, not recalled. No collector was installed or run; every `rule_id` is a `RULE-<code>-v0` placeholder written by the harness task.

## §4 — the coverage model

| | |
|---|---:|
| indicators | 48 |
| **evidenced** | **29 / 48** (60.4 %) |
| gap | 19 / 48 (39.6 %) |
| **measured** | **2 / 48** (4.2 %) — G1-D and G1-O only |
| specified | 46 / 48 |
| harness_built | 0 |
| public tier | 19 · agency_instrumented 21 · paid 8 |

**No composite is computed or registered**, deliberately: protocol §3 and DD-036's two-leg rule carried up from the indicator to the framework. Every fraction carries its counts.

`docs/progress/index.html` — one self-contained file, **inline SVG, no JS, no server** — with three charts (indicators by criterion × measurement status; evidenced vs gap by criterion; AUTO legs with a collector vs `none_known`) and the full indicator table. Onboarded as a **static** webdesktop service (`readiness.home`), committed in that repo at `ff9fee3`; Caddy serves it — verified `HTTP 200` via a Host header.

> **One step left for you, because it needs sudo.** Run `! scripts/check-hosts.sh` in `~/GitHub/webdesktop` and paste the `sudo tee -a /etc/hosts` block it prints; `readiness.home` then resolves in a browser.

## §5 — the week's chain, and a Seldon limitation

Five ResearchTasks registered `proposed`: `harness-scaffold` (`09745466`) → `scan-targets` (`22fb59b2`) → `scan-run` (`e3e38014`) → `eda-and-charts` (`c1ede3d9`) → `report-draft` (`2517cda8`), then `er_research_resumes` (`37476f34`) with its five DD-049 §3 prerequisites.

**The `blocks` edges §5 asks for cannot exist.** Seldon's research domain does not model task ordering: `blocks` accepts `[Result, PaperSection, Figure]`, `depends_on` accepts `[Result, DataFile, Script]`, and the **only** `ResearchTask → ResearchTask` relationship in `seldon/domain/research.yaml` is `superseded_by`, which asserts replacement rather than order. So `seldon go` cannot show this path.

Recorded the ways that do work — a snapshot DataFile `framework_task_chain_2026-09-06` and the order restated in each task's own description — and registered **seldon ResearchTask `505f4c61`** for the missing relationship, naming what would close it (a cycle-checked `precedes` with both endpoint types `ResearchTask`). The workaround is exactly the drift a graph is supposed to prevent: not queryable, not validated, stale silently. It is a stopgap and is labelled one.

## §6 — premises this task got wrong

1. **"45 indicators … A (11), B (6), C (5), D (4), E (9), F (6), G (6)".** The breakdown is right and sums to **47**; "45" is stale in both the task and the skeleton's own header — A10 and A11 were added in v0.2.1 and the count was never updated. With the G1 split that is **48 nodes**, not the 46 §2.3's gate expected. The skeleton header now says so.
2. **"25 evidenced, 20 gaps"** is stale by the same two rows: measured **29 evidenced, 19 gaps**.
3. **§3's list of public-tier AUTO indicators is off by one in each direction.** **B3** (Methodology legibility, AUTO/DOC, `public`) is public-tier AUTO and is not in the list; **A11** is `agency_instrumented` overall, which the task half-acknowledges by naming its "declared leg". I specified the union — 20 legs — and flagged both.
4. **`blocks` edges between ResearchTasks are not expressible in Seldon.** §5.
5. **A version tripwire fired**, correctly: `test_schema_version_is_v03_line` pinned the 0.3 line. Updated to assert the 0.4 line and to stop duplicating the append-only invariant that `test_schema_append_only.py` already holds.
6. **My `doc_id` pattern over-matches.** Six backticked tokens in Evidence cells are epoch names, repo paths or a status word, not doc_ids. They are reported rather than silently dropped, which is what §2.2 asks — but a tighter pattern would report zero.

## §7 — verification

| check | result |
|---|---|
| `python -m pytest tests/` | **909 passed** (900 + 9 new) |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** |
| round-trip gate | **0 unexplained diffs across 47 rows** |
| `git diff` on `assessment/cq/*.yaml`, the G1 harness and fixtures, the vocabulary shard | **empty** |
| indicator *content* edits | **none** — the JSON is derived from the skeleton, and the flip is a header note plus a render command |
| tag | **`kg-freeze-2026-09-06`** |

**Registered.** 6 Scripts; 6 DataFiles (all `snapshot: true`); **22 Results**; **DD-049, DD-050, DD-051**; 11 ResearchTasks in this repo; 1 in seldon.

## §8 — what the next task picks up

`harness-scaffold` is unblocked and has everything it needs: 20 MeasurementSpecs with pinned collectors, five honestly-marked `none_known`, placeholder rule ids, the Observation/Finding split in the schema, and 17 admitted product surfaces to smoke-run against.

**Out of scope and untouched:** the CQ yaml files, the G1 harness and fixtures, the vocabulary log, `state/er_gold_key.json`, the 100-pair sheet, the memo and the deck, and every indicator's content.
