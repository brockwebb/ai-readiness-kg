# RESULT: executive summary from DN-014 (v2)

**Served model:** author `claude-opus-4-8` (effort high; `seldon models resolve author`, session served-model = `claude-opus-4-8`); checker `claude-sonnet-5-5` (role `critic`), reader `claude-fable-5-1` (role `judge`) — three families, no model substitution on any of the 9 calls. Run spend 373,837 tokens (ceiling 3,000,000; est 2.5M).

**Step 0.** Task was `in_progress`, but the state change and `dispatch_launched` are both stamped 2026-10-14T02:37:11Z — this session's own dispatch, not a prior run — so the guard did not fire. Proceeded.

**Step 1 — discoverability headline (checked).** `RULE-A13-v1` measures, per object (API, API terms, changelog, inventory), whether a machine starting at the product page reaches an object shown to exist, by a link or at a documented convention location. Each per-object branch has a published definition: link reachability — RFC 8288 (web linking), schema.org WebAPI and the DCAT-US / Project Open Data schema (a dataset record links its service and distributions); API convention `/.well-known/api-catalog` — RFC 9727 §2-§3; inventory `/data.json` at the host root — OMB M-13-13 + Project Open Data (M-25-05 §4a iii). **No branch is invented.** The *composite* "discoverability from the product page" (candidate A13, enters no score) is project-invented and no single source defines it. Decision: the summary uses the grounded per-object form only (15 of 29 agency-and-object pairs where the object exists are unreachable; 54 of 88 per page — CL-118), never as a score; the composite is recorded as project-invented (Step 2). Counts sit in the page-2 table, not page-1 sentences.

**Step 2 — vocabulary.** Added `air:concept/si-readiness` (short + full definition from DN-014 §1, sources by corpus id: Commerce GAI guidance, NOAA NAO 216-128, World Bank, UN Statistical Commission, USAFacts FDE) and `air:concept/discoverability-from-the-product-page` (project-invented, sources RFC 9727 / DCAT-US / schema.org WebAPI) to `ontology/vocabulary_proposals_epoch2.yaml`. State reached: **proposed** (operator promotion cadence; the TTL was not edited, and nothing in the pipeline reads this file).

**Step 3 — capability table (each DN-014 §3 capability → artifact).**
| Capability | Artifact | State |
|---|---|---|
| Measure what a machine meets | `assessment/harness/scan/` + `rules/rule_*.py` (25 rules) | real |
| Map to the framework (7 criteria) | `framework/ai_readiness_framework.json` (7 criteria, 48+2 indicators) | real |
| One standard scale, comparison | `docs/design/scoring_model.md` (hierarchical equal weights); 13 ranked (CL-050/052) | real |
| Prescriptions by effort | 64 Action nodes, notional `effort_band`/`cost_band` (`get_prescriptions`); score-delta bounds (`score.py`) | real |
| Prescriptions by value (1-5 rating) | `docs/design/2026-10-02_DN-010…` rubric | **planned** (not yet rated) |
| Three tiers by who can run them | framework `measurement_tier` M/O/D (`get_overview`) + requirements layer (`tag_requirements.py`, `get_requirements`) | real |
| Queryable KG, cited answers | MCP server (`docs/design/mcp_over_the_graph.md`; every answer carries locators) | real |
| Superseded kept as history, out of advice | append-only `events/*.jsonl` (DD-008) + claims `status` excluded from advice | real |
| Serves several roles at their depth | MCP answers at overview→indicator→evidence→document granularity | real; role-tailored dashboard **planned** (DN-014 §5) |

**Step 4 — Fable rounds (role `judge`; editorial, not a measurement).**
- R1: q1 **yes to all four**; flagged SI undefined, and repeated points (fast-moving, "meets", worth-is-a-judgment).
- R2: q1 **yes to all four**; caught a build artifact (raw page-break code) in the reader's text, plus residual repetition.
- R3 (final): q1 **"Yes to all four … None of the four depends on page 2; page 2 only adds the numbers."** The checker (one `critic` call) caught all 3 planted controls and, after I tightened four over-reaching sentences to hug their claims, passed every result sentence; a GLOSSARY in the check prompt maps the summary's plain words to the claims' forbidden vocabulary (cycle→measurement, finding→check, body→agency) so faithful paraphrase is not mislabelled.

**Step 5 — build.** `reports/summary/SUMMARY.md` + `SUMMARY.pdf` (rendered by `scripts/summary_build.py`, the Markdown's writer). Body **2 pages exactly** (`build_report.json` `body_pages: 2`); appendix 1 page (total 3). No figure (DN-014 §5 "at most one" permits zero; the page-2 table carries the quantitative content).

**Gate.**
- body page count = **2** (pypdf, body-only render).
- text check (`scripts/summary_text_check.py`, word list `reports/summary/text_check.yaml`) + lint: **0 findings** — zero process words, zero indicator codes, zero "AI" outside titles, zero em/en dashes.
- unsupported-sentence check: **passed** (`unsupported_check_passed: true`, 8 result sentences supported, 0 stray digits); all **3 planted controls caught** (`controls_caught: true`).
- Fable R3 (last): the 30-second bullets can be said from page 1 alone (quoted above).
- `make gate-task`: **EXIT=0** — gate-fast `3352 passed, 5 skipped, 41 xfailed` (0 deselected reported), 285.64s; re-derivation `25 passed`, 9.48s (`logs/gate_task.log`).
- `seldon verify`: **All checks passed, EXIT=0** (`logs/seldon_verify.log`).
- protected-paths diff (`git diff HEAD` on framework record, `rules/`, `params.yaml`, `events/`, prior `*_RESULT.md`, harness): **empty, EXIT=0**.

**Premises found wrong / amended.**
1. DN-014 §3/§7 say prescriptions are "ranked by effort and **impact**", but DN-010 §2.6 bans "impact"/"return" anywhere (they imply a weighting the score lacks). Honored DN-010: the summary says "value"/"how much each fix would open up" and carries DN-010's one-line label that worth is a rated judgment, not a measurement.
2. The task treats the concise pipeline's checks as if a model also wrote the prose; here the **author writes** (Opus 4.8), so only the control + unsupported checks and Fable's reading run, and a GLOSSARY was needed because the text rules forbid the claims' own words.
3. The headline "15 of 29" is correct only as agency-and-object **pairs where the object exists** (not "resources"); the checker forced that precision.

Logs: `logs/gate_task.log`, `logs/seldon_verify.log`, `logs/summary_check*.log`, `logs/summary_read*.log`; run record `reports/summary/run/verify.json`.
