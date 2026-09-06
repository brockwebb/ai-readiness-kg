# CC Task — Harness scaffold: evidence-first collectors, versioned rules, control fixtures, smoke run

**Date:** 2026-09-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-06_freeze_and_framework_graph_RESULT.md`)
**Fulfils:** ResearchTask `harness-scaffold` (`09745466`). Blocks `scan-targets` (`22fb59b2`) by the chain recorded in DataFile `framework_task_chain_2026-09-06`.
**Premise (from `6b742c1e` RESULT):** 20 AUTO legs carry a `MeasurementSpec`; 15 have a pinned open-source collector, 5 are `none_known` with stated reasons (C4-auto, E5, F2, F3, G3). Schema v0.4.0 has `Observation` and `Finding` in the parser-invisible `assessment_layer`, with `OBSERVED_ON`, `SUPPORTS`, `RULED_BY`. 17 product surfaces are admitted under epoch `g1sfc-2026-09-03`. `measurement_status`: 2 measured, 46 specified, 0 harness_built.
**Spend:** zero model calls on the AUTO tier — this is a design property of the harness, asserted by a test (no client library for any model provider is importable from `assessment/harness/scan/`). Network: outbound HTTP to public federal/statistical sites only, identified UA, rate-limited (§2.4).
**Zero edits to:** `framework/ai_readiness_framework.json` indicator content (adding `rule_id` values and `measurement_status` transitions is permitted — they are this task's output), the G1 harness and fixtures, `assessment/cq/*.yaml`, the vocabulary log.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-06_harness_scaffold_ADDENDUM*.md` before starting.** Read `docs/crosswalk/assessment_protocol.md` §6b.5 and the DD-051 schema block before writing any code.

---

## 0. Prior art (record in DD-052)
- **Observation / Finding split**: OSCAL assessment-results (observations are facts, findings are judgements over them); Lighthouse's `artifacts` (gathered once) vs `audits` (computed from artifacts, re-runnable without re-gathering). This is §6b.5 made concrete: raw facts stored, warnings by versioned rule, history re-scorable without re-measurement.
- **Metric → tests → evidence**: F-UJI (Devaraju & Huber 2021) — each metric has named tests, each test records the evidence it saw.
- **Whole-surface capture, no truncation; every constant a swept-able parameter** (Khan 2026, Wintermute `wm-20260906-075432-d860df`: one unswept truncation constant was worth 14 points).
- **Positive controls in every cycle**: the instrument's own E5 — a cycle with zero fired controls is INVALID (DD-019 decoy discipline).
- **Crawler manners**: RFC 9309 (the scanner obeys the file it measures), identified UA, per-host rate limit.

## 1. Package layout
`assessment/harness/scan/` with: `collectors/` (one module per collector: `http`, `robots`, `sitemap`, `structured_data`, `dcat`, `lighthouse`, `fuji`), `rules/` (one module per rule id), `params.yaml`, `run.py`, `rederive.py`, `fixtures/` (§4). `scan/__init__.py` exports `collect(spec, target) -> list[Observation]` and `judge(rule_id, observations) -> Finding`.

## 2. Observations — evidence first

### 2.1 Record
Every collector call yields one or more `Observation` records: `{obs_id, spec_code, leg, target_doc_id, target_url, captured_at (UTC), collector, collector_version, params_hash, request {method, url, headers_sent, ua}, response {status, headers, body_sha256, body_path, bytes, elapsed_ms}, parsed (JSON, collector-specific), error_class (None | dns | timeout | http_4xx | http_5xx | robots_disallowed | parse_error)}`. **Whole body retained**, content-addressed under `corpus/evidence/scan/<sha256[:2]>/<sha256>` — no truncation anywhere; a test asserts the stored bytes hash to `body_sha256`.

### 2.2 Events and graph
`observation_recorded` events in a new shard; loader projects `:Observation` nodes with `OBSERVED_ON` → the product-surface `:Document`. Labelled Cypher only (the lint from `230b282f` applies).

### 2.3 Constants
Every timeout, byte cap (none by default — cap is `null` and must be set explicitly to exist), UA string, rate, crawl depth, retry count, and list (AI-crawler UA list for A4/A11, the format allowlist for A1, the DCAT/schema.org shapes for A6) lives in `params.yaml`, versioned, and its hash stamps every Observation. Nothing numeric is hard-coded in a collector; a test greps for integer literals in `collectors/` outside a small allowlist (HTTP status codes).

### 2.4 Manners
UA `ai-readiness-kg-scanner/0.1 (+<repo url>)`. Before fetching any page on a host, fetch and parse its robots.txt; `/robots.txt`, `/sitemap*.xml`, `/llms.txt`, `/data.json` and `/.well-known/*` are always fetched (they are the object of measurement); any other path is fetched only if allowed for this UA, and a disallow is itself an Observation with `error_class: robots_disallowed`. One request per second per host; exponential backoff on 429/503; no forms, no logins, no query-string fuzzing. Record the manners parameters in `params.yaml` like everything else.

## 3. Rules — versioned, pure, re-derivable
- One module per rule: `RULE-<code>-v1` for each of the 15 legs with a collector plus **E5** (§4 turns its `none_known` into the harness's own control cycle). Signature `judge(observations: list[Observation], params) -> Finding`. No I/O, no network, no clock.
- `Finding`: `{finding_id, rule_id, rule_version, spec_code, leg, target_doc_id, verdict ∈ {pass, fail, not_applicable, error}, evidence: [obs_id], reason (one sentence naming the deciding observation field), params_hash}`. `not_applicable` is a real verdict (a CSV surface has no JSON-LD to check); `error` means the collector could not observe, never that the product failed.
- Events `finding_derived`; loader projects `:Finding` with `SUPPORTS` (Observation→Finding) and `RULED_BY` (Finding→a `:Rule` node carrying id, version, and the rule's docstring).
- **Re-derivation gate:** `rederive.py` deletes every Finding, re-runs every rule from stored Observations, and the result must be byte-identical (ids derived deterministically from rule id + version + sorted obs ids + params hash). A test does this on the fixture set and on the smoke-run output.
- Write `rule_id` back into each `MeasurementSpec` in `framework/ai_readiness_framework.json` and set `measurement_status: harness_built` for the 16 legs. Re-render the skeleton (the round-trip test must still pass — status is not a rendered cell; confirm).

## 4. Control fixtures — E5 by construction
`fixtures/` holds two local static sites served by a test-only `http.server` on localhost: `passes_all/` (robots allowing everything, sitemap, llms.txt, valid `data.json`, a page with valid schema.org `Dataset` JSON-LD, CSV and JSON downloads, a license line, machine-readable release date) and `fails_all/` (PDF-only, no robots, no sitemap, soft-404 shell, no markup, no license). Every rule must return `pass` on the first and `fail` on the second; a rule that returns anything else on either fixture is a failed positive control and the cycle is INVALID (the run exits non-zero before touching a real host). This is the E5 collector: `RULE-E5-v1` reads the control Findings of the current cycle and fails the cycle if either fixture produced a non-expected verdict. Update E5's `MeasurementSpec` from `none_known` to this.

## 5. F-UJI
Pin the `fuji` package (or run its container) for the three overlapping legs (A2 → FsF-A1-03D, A6 → FsF-F4-01M/FsF-I1-01M, D1 → FsF-R1.1-01M). Its output is stored as an Observation with `collector: fuji`; our rule reads the named metric's test results from it. If F-UJI cannot run against a surface (it wants a PID or landing page it can't resolve), that is `error_class: parse_error` with the message retained, not a `fail`.

## 6. Smoke run
Run the full cycle — control fixtures first (§4 gate), then the 17 admitted surfaces. For each (surface, leg) exactly one Finding. Report a matrix: surfaces × legs with verdict class. Expect many `not_applicable` (API rows and CSVs) — that is correct behaviour; a leg that is `error` on every surface is a collector defect, and the RESULT says so. **No verdict from the smoke run is registered as an instrument Result** — this is a harness test, not a measurement; `measurement_status` stays `harness_built`, not `measured`. Register only harness-level counts: `scan_smoke_surfaces`, `scan_smoke_findings`, `scan_smoke_error_legs`, `scan_control_fired`.

## 7. Progress page
Re-run `scripts/framework_progress.py`; `docs/progress/index.html` shows the 16 legs at `harness_built`. Register the updated fractions.

## 8. Reporting
RESULT: `cc_tasks/2026-09-06_harness_scaffold_RESULT.md`. Lead with the control gate and the re-derivation gate, then the surfaces × legs matrix, then any collector that errored everywhere. State every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on the protected files, round-trip test green. `seldon cc complete`; move `09745466` to completed with this RESULT as evidence; commit, push.

**SEQUENCING:** §1 → §2 → §3 → §4 (fixtures and the E5 gate) → §5 → §6 (controls first, hard stop on control failure) → §7 → §8.
