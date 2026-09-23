<!-- authored by cc_tasks/2026-09-22_brief_deck_assembly.md, packaged by cc_tasks/2026-09-23_brief_deck_packaging.md, from the brief pack at commit ed2b3c20558887cca90f3dbd4a461f035a579d0b (docs/brief/, scripts/build_brief_pack.py); framework record at commit 9ffcffddbf8f (framework/ai_readiness_framework.json, generated_from docs/crosswalk/usafacts_operationalization_skeleton.md); cycle of record scan_2026-09-10_rj4. Rendered by scripts/build_brief_deck.py into two files, docs/deck/brief_deck.pptx (sections outside the Appendix chapter) and docs/deck/brief_appendix.pptx (the Appendix chapter and the appendix generated from the pack, which is not in this file). -->
# The brief deck: authored slides

Every line starting `> ` is a quotation the renderer finds in the slide's `source:` files or refuses to build. Every `@` line is pack content copied onto the slide by the renderer. Every other numeral must be on `docs/brief/numbers.json` under a `source:` page.

---

## Slide 1 — Cover

layout: cover
source: docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md
> An AI-readiness framework for federal statistical publishers: a way to rate and score, quantitatively and qualitatively, whether the public and the tools the public now uses can reach, understand and use the data they paid for.
Brock Webb
@stamp

---

## Slide 2 — A · What it is and why

chapter: A
source: docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md
- DN-005 §1, transcribed; chapter A has no pack file.

---

## Slide 3 — The goal, unchanged since the project began

source: docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md
> **An AI-readiness framework for federal statistical publishers: a way to rate and score, quantitatively and qualitatively, whether the public and the tools the public now uses can reach, understand and use the data they paid for.** Everything else in this repository is a level of it, a measurement of it, a view of it, or a demonstration of it.

> - **L0** is the most basic level (host-level: crawler policy present, discovery files, deep links, declared versus enforced access). It is one step, and the one with cold, re-derivable data behind it today.
> - **The L0 report** (`docs/reports/2026-09_fss_ai_readiness_L0.pdf`) is evidence under the framework. It is not the product and it is not a publication in the release sense; nobody has been told it exists.
> - **The site** (`brockwebb.github.io/ai-readiness-kg`) is a demonstration of what an AI-ready site looks like, data-first, with its own scorecard visible. That is the whole of its purpose.
> - **The January ICSP briefing** is a view of the framework at whatever state it is in then: professionally, FSS sites are not AI ready, the public who paid for the data is underserved, here is who, here is what to do. Slides with visuals from matrices that already exist.
> - **Open source** exists to protect the work from being hidden or gatekept, not to publish it. Provenance is git, the append-only log with timestamps and hashes, and CC BY 4.0. No DOI is needed for that and none is being minted.

---

## Slide 4 — What you are looking at

source: INDEX.md
@provenance

> Every file under `docs/brief/` is written by `scripts/build_brief_pack.py` (`cc_tasks/2026-09-22_brief_material_pack_v2.md`) and by nothing else. `--check` re-renders the pack and compares it byte for byte. The numbers each page states in prose are on `numbers.json`, with the source of each.

---

## Slide 5 — B · Delta against the USAFacts framework

chapter: B
source: B_usafacts_delta.md, B_usafacts_delta.csv
- Pack files: `B_usafacts_delta.md`, `B_usafacts_delta.csv`

---

## Slide 6 — How the delta is derived

source: B_usafacts_delta.md
> The framework record has no `origin` field, so no mark on this page is read off the record directly. Each mark is derived by three rules, and each rule cites the skeleton line it rests on:
> 1. Criteria A to D are USAFacts' four and are kept as the top-level structure (`docs/crosswalk/usafacts_operationalization_skeleton.md:9`).
> 2. Criteria E, F and G are additions. The section of the skeleton each one comes from is the section whose tables carry its indicator codes, and that section's heading says why it was added (table below).
> 3. Within A to D, USAFacts named criteria and gave no indicator-level tests (`docs/crosswalk/usafacts_operationalization_skeleton.md:15`), so every indicator is an operationalization and is marked `added (operationalizes <criterion>)`.

> USAFacts names four criteria and argues for pairing LLMs with retrieval and holding results to accuracy evaluations. It does not give an agency a test.

---

## Slide 7 — What the marks say, and what the verbatim test found

source: B_usafacts_delta.md
> An indicator whose record `status` is `candidate` is marked that way instead. No indicator in the record has a status of withdrawn or dropped.

> The `kept_verbatim_or_restated` column is measured against the admitted USAFacts documents (`usafacts-ai-ready-data-guide`, `usafacts-fde-standards-detailed`, `usafacts-fde-standards-quick-reference`): an indicator of criteria A to D is `verbatim (<doc_id>)` when its `construct`, else its `indicator`, string grounds verbatim in one of them under `kg/extraction/grounding.py` normalization, `restated` when neither grounds in any, and an indicator of criteria E, F and G is `n/a (added criterion)`; 0 are verbatim, 27 restated and 22 n/a.

> Of 49 indicator nodes, 24 have a current rule in the registry. 5 carry a departure quote, either from skeleton §8 (items that name the indicator's code) or from a record property that records a restatement or a withdrawal.

---

## Slide 8 — The criteria: four kept, three added

source: B_usafacts_delta.md
@table B_usafacts_delta.md | Criteria | cols=code,name,mark,§8 items

> A §8 item is linked to a criterion when it names the criterion or cites the skeleton section the criterion's indicators sit in.

---

## Slide 9 — Feedback to USAFacts, item by item

source: B_usafacts_delta.md
> 1. **Decomposition with receipts** — four criteria → ~30 indicators, each carrying literature provenance through the KG rather than assertion.

> 2. **"Understandable" needs the FCSM extension** — machine-understandable (semantics, definitions, variable-level metadata), not just parseable; their current text under-specifies this.

> 3. **The accuracy evaluations they call for, instantiated** — a runnable harness (retrieval-grounded QA + entailment judging) rather than a principle.

> 4. **A measurable visibility layer** — GEO/llms.txt/Dataset-markup checks make "AI-optimization" auditable instead of vibes.

> 5. **ACCURATE becomes a closed TEVV loop (§5b)** — verification/validation split, pre-registered thresholds, versioned instruments, contamination policy, positive controls, failure attribution, corrective-action closure. This is the operator's delivered feedback, now with an indicator set and NIST AI RMF framing behind it.

> 6. **Statistical-standards correction** — SDMX/DDI/DCAT where the guide says NIEM.

> 7. **Publication is a deploy (§5c)** — the CI/CD feedback operationalized: pre-release gates, contract stability, vintage regression, staged rollout, signed releases.

> 8. **Uncertainty legibility (§5d G1)** — in their guide, error and noise appear only as privacy safeguards (DP, suppression); no framework treats uncertainty as something the AI consumer must *preserve*. G1 supplies that: structured error measures (G1-D) plus an eval of whether AI restatements keep them (G1-O).

> 9. **Machine as first-class user (§1b)** — delivered feedback, grounded in FAIR rather than prediction: machine-actionability as primary design target, human surface derived; A9 makes it auditable.

> 10. **Protocol as contract (§5d G6)** — delivered feedback: measurement-protocol epochs with machine-readable breaks and reasons; SDMX + ODCS give it standards footing.

> 11. **Red teaming (§5b E9)** — delivered feedback: the framework tests what works; it must also enumerate how products break, with a standing adversarial bank.

---

## Slide 10 — Indicators: A ACCESSIBLE

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=A

---

## Slide 11 — Indicators: B UNDERSTANDABLE

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=B

---

## Slide 12 — Indicators: C ACCURATE

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=C

---

## Slide 13 — Indicators: D OPEN

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=D

---

## Slide 14 — Indicators: E TEVV loop (added)

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=E

---

## Slide 15 — Indicators: F release engineering (added)

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=F

---

## Slide 16 — Indicators: G FSS-derived constructs (added)

source: B_usafacts_delta.csv
@csv B_usafacts_delta.csv | cols=code,construct,measurement_tier,rule,mark,kept_verbatim_or_restated | where=criterion=G

---

## Slide 17 — C · Provenance

chapter: C
source: C_provenance.md, C_provenance.csv
- Pack files: `C_provenance.md`, `C_provenance.csv`

---

## Slide 18 — Coverage, stated first

source: C_provenance.md
> **Coverage, stated first.** 9 of 49 indicator evidence cells carry a pinpoint locator for at least one cited document. The test is `scripts/report_traceability.py::locators`, the same one the report's Locator column prints: a backticked doc id followed by a parenthetical. 27 of 147 `EVIDENCED_BY` edges point at a document the cell locates. 16 indicators have no `EVIDENCED_BY` edge at all. The rest cite their sources as general support, with no place inside the source.

> Indicators with a located cell: `A1`, `A3`, `A8`, `A10`, `A12`, `B3`, `D3`, `D4`, `G4`.

> No admitted document matches `Title 13`, `CIPSEA`, `SPD (Statistical Policy Directive)`. Those rows are absences in this corpus. They are not claims about the instruments. The statistical-policy corpus is a separate graph (fss-policy-kg), and this page does not reach into it.

---

## Slide 19 — Corpus documents per type: admitted and cited

source: C_provenance.md
@table C_provenance.md | Corpus documents per type

> Admitted means `screening.decision: included`. Cited means cited by at least one indicator's `EVIDENCED_BY` edge.

> It does not split statute from OMB guidance, or a W3C recommendation from other standards. That split is not in the manifest, and this page does not guess it.

---

## Slide 20 — The policy-instrument map

source: C_provenance.md
@table C_provenance.md | Federal policy instruments | cols=instrument,admitted documents,by edge,by text only

> `by edge` lists the indicators with an `EVIDENCED_BY` edge to a matched document. `by text only` lists the indicators whose evidence cell names the instrument but which have no such edge.

---

## Slide 21 — Per-indicator provenance

source: C_provenance.md, C_provenance.csv
> One row per `EVIDENCED_BY` edge, in `C_provenance.csv` as well. Internal references (`EVIDENCED_BY_INTERNAL`) are listed after the table.

- Each indicator's cited documents, with their locators where the cell has one, are on its appendix slide.

---

## Slide 22 — D · Using it: the offline demo

chapter: D
source: D_demo_runbook.md, D_demo_capture.json
- Pack files: `D_demo_runbook.md`, `D_demo_capture.json`

---

## Slide 23 — How the demo was run

source: D_demo_runbook.md
> Each command is copied from a file that already documents it. The source file and the exact source text are named under each step, and so is any substitution. Every command was executed once, by `scripts/build_brief_pack.py --capture-demo` at commit `d330014dbfe8`, and the lines it printed are pasted under it: the first lines, then the last lines when there were more. A command that failed is left in with its failure and a note.

> Failed steps: none.

---

## Slide 24 — Neo4j is up and the framework projection is current

source: D_demo_runbook.md, D_demo_capture.json
> Source: `CLAUDE.md`, which documents `python -m pytest tests/test_framework_projection_roundtrip.py`.
@capture neo4j

---

## Slide 25 — Orient: seldon go

source: D_demo_runbook.md, D_demo_capture.json
> Source: `CLAUDE.md`, which documents `seldon go --brief`.
@capture seldon_go

---

## Slide 26 — Open the report

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: the project's published report in place of an adopter run's; the PDF beside it is `docs/reports/2026-09_fss_ai_readiness_L0.pdf`.
@capture report

---

## Slide 27 — Score one body

source: D_demo_runbook.md, D_demo_capture.json
> Source: `scripts/score.py`, which documents `scripts/score.py --body NCHS`.
@capture score

---

## Slide 28 — MCP verb get_body, in-process

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: `run=` dropped (the project's published tree), MYSITE -> CENSUS.
@capture get_body

---

## Slide 29 — MCP verb get_prescriptions, in-process

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: the same template, verb `get_prescriptions(body="CENSUS")`, printing the failing legs and the first five actions.
@capture get_prescriptions

---

## Slide 30 — MCP verb get_requirements, in-process

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: the same template, verb `get_requirements(body="CENSUS")`.
@capture get_requirements

---

## Slide 31 — Start the MCP server (stdio)

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: stdin closed, so the stdio server sees end-of-input at once; in a demo the client (Claude Desktop) holds stdin open.
@capture mcp_server

---

## Slide 32 — Request a live spot scan of one body (render only)

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: BEA -> CENSUS; without `--write`, so no task file is created and no host is contacted.
@capture spot_render

---

## Slide 33 — A spot scan end to end against the loopback fixtures

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: this machine's interpreter; `-q`. Every URL is 127.0.0.1; no federal host.
@capture spot_loopback

---

## Slide 34 — How a second agency runs it: the adopter runbook, executed

source: D_demo_runbook.md, D_demo_capture.json
> Substitution: none; the test runs every bash block of the adopter page in a scratch copy of the tree against a loopback "site".
@capture second_agency

---

## Slide 35 — E · Architecture

chapter: E
source: E_architecture.md
> Four diagrams. Every box names the code it stands for, and the generator resolves each `file:line` against the code when it renders. A box whose code has moved stops the build, so no diagram here is drawn from memory.

---

## Slide 36 — Operational view: from an agency site to a published verdict

source: E_architecture.md
@diagram a
> **How to read it.** Left to right is one cycle. The fetcher is the only part that touches the network. It sends one declared identity, reads robots.txt before anything else on a host, and keeps every response body under its sha256. Rules never fetch: they read Observations and return a Finding. The Findings go to the append-only log, and the matrices, the report, the site and the MCP are read from the log or from what it projects. Dotted arrows are configuration, not data.

---

## Slide 37 — Systems view: processes, stores and the one owner of each layer

source: E_architecture.md
@diagram b
> **How to read it.** The two stores of record are the event log and the framework record. Neo4j is a projection of both and can be deleted and rebuilt. Each projected layer has exactly one writer. `build_projection.py` resets only the KG labels, `publish.py` owns Observation, Finding and Rule, and `load_framework_graph.py` owns the framework labels (`CLAUDE.md:70`). The framework record itself has one writer, `framework_writeback.save`. Seldon's artifact graph lives in the same database under disjoint labels. The dispatcher is in the Seldon repository and launches one session per registered task. The MCP server reads the record and the projection and writes nothing.

---

## Slide 38 — Data flow for one verdict: CENSUS, worked from the cycle of record

source: E_architecture.md
@diagram c
> **How to read it.** The URL was fetched once. The Observation carries the response body's digest, and the body sits under that digest in the evidence store. The rule read the Observation and produced the Finding, and the matrix cell names the Finding. A reader can re-hash the stored body and re-run the rule (`assessment/harness/scan/rederive.py`) without touching the network.

---

## Slide 39 — Judgement generations: re-judgement without re-fetch

source: E_architecture.md
@diagram d
> **How to read it.** A re-judgement runs the current rules over Observations already on the log and fetches nothing. Its Findings cite the source cycle's `obs_id`s and `SUPERSEDES` their predecessors one to one (`docs/design/2026-09-14_DN-003_event_log_and_rejudgements.md:12`). A Finding with no successor is current. The published report points at the current generation of its snapshot cycle, which is why the report can move to a new judgement without a new scan.

---

## Slide 40 — F · Results

chapter: F
source: F_results_pointer.md
> Pointers only. No number is re-typed here: each Result is named with its id, and its value is on the graph and in the report.

---

## Slide 41 — Where the results live

source: F_results_pointer.md
@table F_results_pointer.md | F. Where the results live

---

## Slide 42 — Headline Results, by name and id

source: F_results_pointer.md
> The headline Results are the ones the report's opening section quotes (`docs/reports/sections/10_frame.md`, 8 names), each looked up on the Seldon graph by name.
@table F_results_pointer.md | Headline Results

---

## Slide 43 — G · Census dogfood

chapter: G
source: G_census_dogfood.md
> No new fetch. This is the published cycle read back through `get_body`, `get_requirements` and `scripts/score.py`.

---

## Slide 44 — census.gov on the cycle of record

source: G_census_dogfood.md
> `get_body` summary: 34 failing of 39 judged on scan_2026-09-10_rj4; 16 bodies are on this cycle. CENSUS ranks 5 of 13 (hierarchical), and it rests on one pass: 1 pass of 1 judged row on A10; were that leg's verdicts reversed it would rank 9.

> Hierarchical score 0.080, rank 5 of 13. Flat score 0.190, rank 5. Both schemes use equal weights, and neither has a basis over the other, so both are printed. Coverage: 21 of 48 framework indicators and 5 of 7 criteria are measured. Tier O and D indicators are not scored.

---

## Slide 45 — The one-leg-criterion caveat

source: G_census_dogfood.md
> **The one-leg-criterion caveat.** The rank rests on a single leg: `A10` (1 pass of 1 judged). Were that verdict reversed, the body would rank 9.

> Cycle of record: `scan_2026-09-10_rj4`, 23 legs judged, 1,009 findings, report and site re-snapshotted on it. Every rank rests on a one-leg criterion (F4 for nine bodies; a single pass on G4 or A10 for four); both equal-weight views are shown and no weighting is asserted.

@table G_census_dogfood.md | Score

---

## Slide 46 — Every judged leg

source: G_census_dogfood.md
> One row per judged cell: its surface, verdict and reason, and the Finding and rule behind it. From `get_body` against the projection.
@table G_census_dogfood.md | Every judged leg | cols=leg,surface,verdict,reason,rule

---

## Slide 47 — What to do first: prescriptions, ranked

source: G_census_dogfood.md
> Actions on the body's failing legs are ordered cheapest effort band first, then by how much each would add to the score. The bands are notional (page H). `delta` is an upper bound: it assumes every failing row on that leg passes.
@table G_census_dogfood.md | What to do first | cols=effort,cost,delta,leg,title

---

## Slide 48 — H · Limits and roadmap

chapter: H
source: H_limits.md
> Only the open items the record and the graph already state. Nothing here is a new finding.

---

## Slide 49 — Measurement tiers and status

source: H_limits.md
@table H_limits.md | Measurement tiers

> Measurement status of the framework's indicators (record `measurement_status`):
@table H_limits.md | Measurement tiers | nth=2

---

## Slide 50 — Indicators the record does not mark measured, and why

source: H_limits.md
> Where it says `yes`, the record's `measurement_status` lags the cycle, which judges the leg anyway. That is a recorded discrepancy, and this page does not correct it.
@table H_limits.md | Indicators the record does not mark measured | cols=indicator,status,tier,reason (record),judged on the cycle of record

---

## Slide 51 — Evidence locators, and equal weights

source: H_limits.md
> 9 of 49 evidence cells carry a pinpoint locator (page C). ResearchTask `93d28c6e` holds the rest, and it is not scheduled.

> Both scoring schemes weight equally, following the OECD/JRC Handbook default for when no basis exists for other weights (`docs/design/scoring_model.md`). With equal weights and sparse passes, each body's rank rests on a single leg.

---

## Slide 52 — Every rank rests on one leg

source: H_limits.md
@table H_limits.md | Equal weights | cols=body,leg,sentence (score.py)

---

## Slide 53 — Roadmap items already on the graph

source: H_limits.md
- `bb46ddb5` (proposed):
> FUTURE (not scheduled, not a side quest now): session-spend estimation. Survey prior art first (ccusage and similar transcript meters; agent cost-prediction literature; reference-class forecasting for task estimates), then the smallest tooling: the dispatcher writes each session's measured token total to the dispatch log and onto the ResearchTask beside the task file's estimate; a report compares estimate to actual by task shape and model. Also here: `dispatch.model` default and an optional per-task `**Model:**` header (the dispatcher launches on the default model today; seldon.yaml has no model key). Seed data points, 2026-09-21: stopped G4 run 691K tokens on Sonnet, 11 calls, 59 s; Opus task sessions of 2026-09-19/20 averaged tens of millions each, 98.9 percent cache reads (ccusage).

- `8a9a89d7` (proposed):
> FUTURE (blocked on external information): NSDS bake-off. The National Secure Data Service has a pilot of AI-readiness tools that can be pointed at websites. When the operator knows what the tools are and how to access them: design paired tests against the same hosts and cycle this framework scanned, to get comparative baselines and to find what the commercial or NSDS tools capture that this harness cannot (and the reverse). Output: a comparison table for the brief's limits-and-roadmap chapter (MVP brief task 5f1bf9f0 does NOT wait on this), and a position on complementary use (NSDS or commercial tooling as an additional data source where budget allows). Requirements for each external test are recorded the way `get_requirements` already records tests this harness cannot run alone.

---

## Slide 54 — The appendix, in its own file

chapter: Close
- The indicator sheets, the rule groups and the corpus summary are in a second file, generated from the same pack:
@stamp appendix

---

## Slide 55 — Appendix cover

chapter: Appendix
layout: cover
The brief deck: appendix
@stamp

---

## Slide 56 — Appendix

chapter: Appendix
source: appendix/rules.md
> Every rule version ever shipped (`rules.REGISTRY`, 54 versions), of which 24 are current: the rule a new cycle judges with.

- One slide per indicator sheet, one per rule group, and one corpus summary follow, generated from the pack when the deck is built.
