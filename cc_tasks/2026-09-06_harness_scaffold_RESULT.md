# RESULT — Harness scaffold: evidence-first collectors, versioned rules, control fixtures, smoke run

**Task:** `cc_tasks/2026-09-06_harness_scaffold.md` (no addenda; globbed, none exist)
**Date:** 2026-09-06 · **Executed by:** Claude Code
**Model spend:** **zero.** The AUTO tier makes no model call, and that is asserted rather than intended — `test_the_auto_tier_cannot_call_a_model` walks every module under `assessment/harness/scan/` and fails on an import of any model provider's client library.
**Network:** outbound HTTP only, to the five public statistical hosts the 17 admitted surfaces live on, under the identified UA `ai-readiness-kg-scanner/0.1`, one request per second per host, robots.txt honoured (§2.4).

---

## 1. The control gate — it fired, and it earned its keep on the first run

```
CONTROL GATE: PASS — both control fixtures fired and every rule returned its expected verdict
```

Two local static sites are served on localhost and scanned **before any real host is touched**: `passes_all/` must draw `pass` from every rule, `fails_all/` must draw `fail` from every rule, and a cycle in which either did otherwise exits non-zero before a single federal server sees a request. 31 control Findings — 15 `pass` on `passes_all`, 15 `fail` on `fails_all`, no exceptions, plus `RULE-E5-v1`'s own verdict on the cycle. This is DD-019's decoy discipline turned on the instrument itself, and it is why E5's `MeasurementSpec` moved from `collector: none_known` to `collector: control_fixtures`: *a cycle with zero fired controls is INVALID* stopped being an aspiration and became an exit code.

**It caught three real rule defects on its first run**, each of which would have produced a plausible and wrong verdict against federal surfaces with nothing to flag it:

| rule | what it accepted | why that is wrong |
|---|---|---|
| A8 | a bare HTTP `Last-Modified` response header | a byte-level artefact of the file's mtime, not a *published* release or modification date; every static file on earth has one |
| A9 | the `fails_all` soft-404 HTML shell | a machine-first entry point is a **machine format**; an HTML body disqualifies it whatever the status code, and a soft-404 host answers every probe with HTTP 200 |
| B3 | the product page as its own methodology document | "links to a methodology document" is not satisfied by a page linking to itself; the check has to find a *different* document |

All three now pass the control and were re-run against the real surfaces.

## 2. The re-derivation gate

```
RE-DERIVATION GATE: PASS   "identical": true
missing_after_rederive: []   unexpected_after_rederive: []   field_mismatches: []
```

`rederive.py` deletes every Finding, re-runs all 16 rules from the stored Observations alone, and the output must come back byte-identical. It does — **286 of 286**, the 255 surface Findings and all 31 control Findings.

That number started at 255, and the gap is the more useful half of this section. **A gate is only as wide as the evidence it kept.** The first version looked airtight and was checking only the *surface* Findings, because the control run discarded its Observations — so the Findings that license the entire cycle were the only ones in the system that could not be re-derived. Retaining the fixture Observations brought them in and immediately exposed a second bug: E5 judges the **cycle**, not a surface, so grouping its evidence per fixture re-derived two E5 Findings where the cycle recorded one. Both fixed, both tested. The lesson generalises past E5: *ask what a passing gate did not look at.* That works because a Finding's id is **derived, never assigned** — `sha256(rule_id | rule_version | sorted obs_ids | params_hash)` — so an id from a counter or a clock cannot make the gate vacuous. This is the OSCAL / Lighthouse observation-vs-finding split (DD-052 §1) delivering its actual payoff: **a rule can be corrected in a year and the whole history re-scored without re-measuring a single surface**, which matters because by then the surfaces will have changed and the old measurement can never be repeated.

The gate also refuses to re-derive across a `params_hash` mismatch. It has to: a params change moves every derived id, so re-deriving old evidence under new constants would silently produce ids that disagree with the stored ones. That guard was added after a params change did exactly that mid-task.

## 3. What was built

`assessment/harness/scan/` — 1,829 lines of Python, 134 lines of `params.yaml`, 47 tests.

| piece | what it is |
|---|---|
| `model.py` | `Observation` and `Finding`. Ids derived by sha256 of what was observed / what was judged. Whole response bodies stored content-addressed under `corpus/evidence/scan/<sha[:2]>/<sha>` — **no truncation anywhere**, and `manners.max_body_bytes` is `null` so a cap must be written down to exist. Closed sets `ERROR_CLASSES` and `VERDICTS` reject an unknown value at construction. |
| `manners.py` | `Fetcher`: 1 req/s per host, exponential backoff on 429/503, robots gate, and the stated `always_fetch_paths` carve-out. |
| `collectors/` | 6 modules — `http`, `robots`, `sitemap`, `structured_data`, `dcat`, `lighthouse`. They observe and never judge. |
| `rules/` | 16 rules at `v1`, one module each, pure: no I/O, no network, no clock. Asserted by AST walk, not by convention. |
| `params.yaml` | every timeout, rate, UA, depth, retry, path list and format list. `params_hash` rides on every Observation and every Finding. |
| `fixtures/` | `passes_all/`, `fails_all/`, and a test-only `FixtureServer` with `HOSTPORT` substitution. |
| `run.py` / `rederive.py` / `publish.py` | the cycle, the re-derivation gate, and the event-log writer + projector (`SCAN_BATCH = 29`, labelled Cypher only). |

## 4. The smoke run — 17 surfaces × 15 legs

Controls first, then the 17 product surfaces admitted under epoch `g1sfc-2026-09-03`, their URLs read from `corpus/manifest.json` and never typed here. 515 Observations, 255 Findings, exactly one per (surface, leg).

`P` pass · `.` fail · `—` not_applicable · `E` error

| surface | A1 | A2 | A3 | A4 | A5 | A6 | A8 | A9 | A10 | A11-d | B3 | D1 | D4 | F4 | G1-D |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `bls-employment-situation-2026-05-news-release-archive` | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E |
| `bls-employment-situation-2026-08-news-release` | E | E | E | E | E | E | E | E | E | E | E | E | E | E | E |
| `census-api-acs5-2023-b19013-counties-colorado` | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| `census-api-acs5-2023-b19013-counties-idaho` | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| `census-api-dec2020-dhc-p1-counties-colorado` | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| `census-quickfacts-denver-county-colorado` | E | . | E | P | . | E | E | . | E | P | E | E | . | . | E |
| `census-quickfacts-denver-county-colorado-csv` | E | . | E | P | . | E | E | . | E | P | E | E | . | . | E |
| `nchs-data-brief-500-dental-visits-adults-65-2022` | . | . | . | P | . | — | . | . | P | P | . | . | . | . | . |
| `nchs-data-brief-515-high-total-cholesterol-2021-2023` | . | . | . | P | . | — | . | . | P | P | . | . | . | . | . |
| `nchs-data-brief-530-perinatal-mortality-2022-2023` | . | . | . | P | . | — | . | . | P | P | . | . | . | . | . |
| `statcan-13-10-0096-01-cchs-2022-provinces-percent-ci-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | P |
| `statcan-13-10-0096-01-cube-metadata-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | . |
| `statcan-13-10-0113-01-cchs-2021-2022-quebec-health-regions-percent-ci-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | P |
| `statcan-13-10-0113-01-cube-metadata-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | . |
| `statcan-14-10-0287-01-cube-metadata-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | . |
| `statcan-14-10-0287-01-lfs-2025-12-provinces-estimate-se-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | P |
| `statcan-14-10-0287-01-lfs-2026-07-provinces-estimate-se-csv` | P | . | . | P | . | — | . | . | . | P | . | . | . | . | P |

| leg | pass | fail | n/a | error | | leg | pass | fail | n/a | error |
|:--|--:|--:|--:|--:|--|:--|--:|--:|--:|--:|
| A1 | 7 | 6 | 0 | 4 | | A10 | 3 | 10 | 0 | 4 |
| A2 | 0 | 15 | 0 | 2 | | A11-declared | 12 | 3 | 0 | 2 |
| A3 | 0 | 13 | 0 | 4 | | B3 | 0 | 13 | 0 | 4 |
| A4 | 12 | 3 | 0 | 2 | | D1 | 0 | 13 | 0 | 4 |
| A5 | 0 | 15 | 0 | 2 | | D4 | 0 | 15 | 0 | 2 |
| A6 | 0 | 3 | 10 | 4 | | F4 | 0 | 15 | 0 | 2 |
| A8 | 0 | 13 | 0 | 4 | | G1-D | 4 | 9 | 0 | 4 |
| A9 | 0 | 15 | 0 | 2 | | **all 255** | **38** | **161** | **10** | **46** |

**No collector errored on every surface.** `legs_erroring_on_every_surface: []` — the condition §6 defines as a collector defect did not occur. The 46 errors are the transposed shape: **two surfaces** on which *every* leg errored, which is the host's refusal, not our defect. That distinction is now two separate Results (`scan_smoke_error_legs` = 0, `scan_smoke_unobservable_surfaces` = 2) because collapsing them would let one hide the other.

**Reading the pass column.** A4 and A11-declared pass on 12 surfaces because robots.txt does not disallow the AI-crawler UAs; A1 passes on the 7 StatCan CSVs because a CSV *is* the structured format A1 asks for; A10 passes on 3 NCHS briefs whose valid/invalid route pair is distinguishable; G1-D passes on the 4 StatCan tables that carry a standard-error or confidence-interval **field**. Everything else fails, and the fail reasons are uniform and legible — no OpenAPI description (A2), no whole-product download link (A3), no sitemap or `llms.txt` or well-known file (A5), no declared release date (A8), no machine-first entry point (A9), no methodology link (B3), no licence field (D1), no `data.json` catalog (D4), no changelog endpoint (F4).

**These are not measurements of these agencies.** See §9.

## 5. The defect only real surfaces could expose: a refused scanner is not a failed product

`www.bls.gov` answered **HTTP 403 to all 60 requests**. `www.census.gov` answered 403 to 26 of 62. The first smoke run scored both BLS surfaces `fail` on all fifteen legs and the two Census QuickFacts surfaces `fail` on eight each — **46 verdicts asserting that federal statistical agencies lack properties nobody was ever permitted to look for.** The control fixtures could not catch this: they answer every request.

§3 is explicit that `error` means the collector could not observe and never that the product failed, and the guard was reading `error_class` alone. `http_4xx` covers **both** 404 (*the path is not served* — a real observation of absence, and most of what the harness is for) and 401/403/407/429 (*the host declined this client* — no observation at all). The class cannot carry the distinction, so the status now does: `manners.unobservable_statuses` is a parameter, not a protocol constant, and `only_errors` takes `params` to read it. It fires only when **every** observation for a leg is a non-observation — `www.census.gov` returned 26 403s alongside 10 200s and 26 404s, and treating that whole surface as unobservable would throw away real evidence.

Recorded as DD-052 §6a, with two tests (`test_a_host_that_refuses_every_request_is_an_error_not_a_fail`, `test_a_404_is_still_a_real_observation_of_absence`) that fail on the old code. `verdict_counts` moved `{pass 38, fail 207, n/a 10, error 0}` → `{pass 38, fail 161, n/a 10, error 46}`.

**Erratum.** `scan_smoke_findings` was registered before this fix, and its *description* quotes the superseded verdict map. Its **value (255) is unaffected** — the count of findings did not change, only how 46 of them are classified. The corrected breakdown is registered as four separate Results (`scan_smoke_pass_findings`, `_fail_findings`, `_error_findings`, `_not_applicable`) so the figures resolve individually rather than through prose, per DD-040.

## 6. Every premise this task got wrong

**6.1 §5 assumed F-UJI is a pip install. It is not, and the name that looks like it is a different package.** `pip install fuji` resolves to an unrelated PyPI project by startechsheffield ("a small library made to make common tasks easier"). It installs cleanly, it imports, and it contains no FAIR assessment code — verified by installing it, importing it, reading it, and uninstalling it. The real F-UJI (`pangaea-data-publisher/fuji`, Devaraju & Huber 2021) is a **server** installed from GitHub source with its own `config/server.ini` and metadata catalogues; `fuji-server` is not on PyPI at all. Standing that up is a dependency this scaffold declined to take on. `params.yaml` therefore records `fuji.available: false`, keeps the three overlapping metric ids in `deferred_metrics` (A2 → `FsF-A1-03D`, A6 → `FsF-F4-01M` / `FsF-I1-01M`, D1 → `FsF-R1.1-01M`) so the next task need not re-derive them, and states the collision in the file so nobody installs the wrong package twice. **The three legs use their own collectors; the F-UJI cross-check is deferred, not done.**

**6.2 §3 and §7 say "the 16 legs" and "the 16 legs at `harness_built`". It is 16 rules but 15 indicators.** 16 legs have a `v1` rule; two of them, `G1-D` and `G1-O`, hang off the single indicator `G1`, which is already `measured` under DD-036. A real measurement outranks the fact that a harness now exists for it, so `G1` is **not demoted** to `harness_built`. 15 indicators moved (A1, A2, A3, A4, A5, A6, A8, A9, A10, A11, B3, D1, D4, E5, F4). The progress page shows 15, not 16.

**6.3 The premise line says 5 specs are `collector: none_known`. After §4 it is 4** — E5 left the list, because §4 makes the control fixtures its collector. C4-auto, F2, F3 and G3 remain, each for the reason DD-050 records.

**6.4 §6 predicted "many `not_applicable` (API rows and CSVs)". The first smoke run produced ZERO, and that was a defect, not a correction to the prediction.** `RULE-A6-v1` read a `content_type` key that the `structured_data` collector never set, so a surface with no HTML at all — nothing for embedded markup to be *in* — scored as a failure to have embedded markup. Fixed, the same run returns 10. The general form is worth keeping: **a harness that cannot say "not applicable" reports absence of the substrate as absence of the property**, and every such verdict is a false negative against the product. `G1-D` had the same shape from the other direction — it searched only `<th>` elements, so a StatCan CSV that declares its standard errors in the header **row** and has no HTML at all could never pass.

**6.5 The premise that a `fail` means the product failed.** See §5 — the smoke run's worst defect, and the one only the real surfaces could expose.

**6.5a Three more premises the task did not know it was making, all in §3 and §4.** (i) That E5's Finding was being recorded — it was not; it lived in `run.py`'s locals, and `rules_built: 16` against 15 projected `:Rule` nodes was the only symptom. (ii) That the re-derivation gate covered the cycle — it covered the surfaces; see §2. (iii) That the control fixtures produce comparable records across runs — the fixture server binds an **ephemeral port**, which leaks into every control `target_url` and hence into every derived control id, so a second control run yields records that are new rather than equal. That last one surfaced as `run.py --merge-controls` (added so re-validating controls need not re-scan seventeen federal hosts a third time in an afternoon) producing a payload that claimed 61 control Findings for one cycle. It replaces rather than unions now, and refuses across a `params_hash` change.

**6.6 §2.3's integer-literal lint found one on its own author.** `sitemap.py` carried `locs[:5]` — a silent cap on retained sample URLs. Not evidence truncation (the whole body is stored content-addressed either way), but a constant that could not be swept, versioned, or stamped on the evidence it shaped. Now `a5_discovery.sample_urls_retained`.

**6.7 `seldon verify` reports one issue that this task did not cause and does not fix.** `✗ Precedence — 117 illegal endpoints`, every one printed as `? [missing] → ? [missing]`. Confirmed pre-existing by stashing this task's entire working tree and re-running: identical 117. It is the Seldon-side counterpart of the finding already recorded against ResearchTask `505f4c61` — Seldon's research domain cannot express task-to-task ordering — and it is not actionable from this repo. Every other check is green.

## 7. Registration

**Results (15).** Harness-level counts only, per §6's instruction. **No verdict from the smoke run is registered as an instrument Result**, and `measurement_status` stays `harness_built`, never `measured`. Registering per-indicator pass rates here would publish a measurement of seventeen federal surfaces taken by a harness whose rules had not yet been reviewed, under the very names the instrument will later want.

`scan_smoke_surfaces` (17), `scan_smoke_findings` (255), `scan_smoke_observations` (515), `scan_smoke_pass_findings` (38), `scan_smoke_fail_findings` (161), `scan_smoke_error_findings` (46), `scan_smoke_not_applicable` (10), `scan_smoke_error_legs` (0), `scan_smoke_unobservable_surfaces` (2), `scan_control_fired` (2), `scan_control_findings` (31), `scan_rederived_findings` (286), `scan_rules_built` (16), `framework_indicators_harness_built` (15), `framework_specs_collector_none_known_after_harness` (4).

`register_harness_results.py` is idempotent: a name already taken **at the same value** is the script re-running, and only a name taken at a *different* value is an error. Result names are unique per graph (AD-028), so without that distinction adding one row would read as fourteen failures.

**Scripts (4):** `scan_run`, `scan_rules`, `register_harness_results`, `framework_writeback_rules`. **DataFile (1):** `scan_smoke_2026-09-06`.

**Event log:** shard `events/batch-029.jsonl`, `observation_recorded` and `finding_derived`. Three evidence cycles now sit on it under different `params_hash` values (`018dea33…` and `86299688…` superseded, `045c17eb…` current) — append-only, so a superseded cycle stays as the record of what was observed under the constants of the day. The 22 MB content-addressed evidence store under `corpus/evidence/scan/` **is committed**, unlike the gitignored corpus binaries: those survive as `primary_url + content_hash` because they can be re-fetched, and a scanned web page cannot. A Finding that cites bytes the repo does not hold is not evidence.

**`framework_writeback_rules` exists because the first write-back was an ad-hoc command.** It set `rule_id` on 16 specs and moved 15 indicators correctly, and left `counts.collectors_none_known` at 5 after E5 had stopped being `none_known` — a derived summary drifting from the nodes it summarises, with nothing to notice. That is precisely the defect DD-040 records about numbers computed in chat. The script makes the write-back a re-runnable derivation, and two new tests hold it: `test_counts_agree_with_the_specs_they_summarise` (which fails on the old file) and `test_the_rule_write_back_is_idempotent`.

**DD-052** records §0's prior art and where the harness departs from it: the OSCAL/Lighthouse observation-finding split, F-UJI's metric → tests → evidence shape *and the pinning that could not be done*, Khan 2026's unswept-constant finding, DD-019 decoy discipline made into the control gate, and RFC 9309 manners with the one carve-out stated rather than assumed. §6a records the 403 defect.

## 8. Verification

| gate | result |
|---|---|
| `python -m pytest tests/ assessment/` | **1,434 passed, 2 skipped** (52 in `test_scan_harness.py`) |
| control gate | **PASS** — 31/31 control Findings as expected |
| re-derivation gate | **PASS** — `identical: true`, 286 of 286 |
| graph projection | 1,608 Observations, 916 Findings, 16 Rules, `observed_on_missing_document: 0` |
| round-trip gate (`render_framework.py --check`) | **PASS** — explained diffs 0, unexplained 0 |
| `seldon verify` | 1 issue, pre-existing and unrelated (§6.7); all other checks green |
| `git diff` on protected paths | **empty** — `assessment/cq/`, `kg/vocab.py`, the G1 harness and fixtures untouched |
| `framework/ai_readiness_framework.json` diff | 38 insertions / 37 deletions, confined to `rule_id` (×16), `measurement_status` (×15), E5's collector block, and the two derived `counts` entries — exactly what §3 permits |
| model spend | **zero**, asserted by test |

## 9. What this does not claim

The 17 surfaces were **not measured**. This was a harness test, run on real hosts because a harness that has only ever seen its own fixtures has not been tested, and the verdicts it produced are on the event log as evidence of the harness working — not as an assessment of BLS, Census, NCHS or StatCan. Every rule is at `v1` and none has been reviewed against its `MeasurementSpec` by anyone but its author. `measurement_status: harness_built` is the honest state and the next task's job is to earn `measured`.
