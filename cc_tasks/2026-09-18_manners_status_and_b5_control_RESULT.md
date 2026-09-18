# RESULT — robots.txt status per RFC 9309, a two-product control for B5, and D4's membership question closed

**Task:** `cc_tasks/2026-09-18_manners_status_and_b5_control.md` (no addenda; globbed before §1 and again before §3).
**Date:** 2026-09-18. **Spend:** zero model calls. **Network:** none beyond `git push`; every fixture on loopback.
**Framework layer served:** §2.2 Tier M, instrument integrity ahead of cycle 5.

**Gate, in one line.** Full suite **2581 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`. `make gate-task` fast tier **2556 passed, 3 skipped, 12 xfailed, 25 deselected**; re-derivation **22 passed, 0 skipped, 0 xfailed, 25 deselected**, `EXIT=0`. Slow control tier run first: **25 passed, 0 skipped, 0 xfailed, 2571 deselected**, `EXIT=0`. `seldon verify`: all checks passed. Protected paths: OK. The table and log paths are in §4.

**In one paragraph.**
- **Decision 1.** `Fetcher._robots_for` now reads the status before the body, per RFC 9309 §2.3.1. A 5xx, or a network failure on the read, now disallows everything on that netloc for the cycle. Until now both meant "allow everything". Each read writes one line to `Fetcher.robots_log`, and the cycle payload carries that log as `robots_log`.
- **Decision 3.** Two body fixtures, `body_two_products` and `body_two_products_split`, give B5 a control that fires. Their tables were pre-registered from the rule source before either fixture ran, and all 11 fixtures returned their tables on the first run.
- **Decision 4.** D4's substring membership test contradicts the DCAT-US text. The replacement is **`RULE-D4-v3`**, not `-v2`, because `RULE-D4-v2` already existed. The test itself lives in the collector, since no rule can compute membership.
- **Record and views.** The record moved through the single writer in three derived events, and a projection followed. No stored Finding re-derives differently.

---

## 0. Decision 1: the status table as implemented

### The RFC, as admitted

The source is `corpus/kernel/rfc-9309-robots-exclusion-protocol.md` (doc_id `rfc-9309-robots-exclusion-protocol`), §2.3.1. The two clauses the task names:

> **2.3.1.3. "Unavailable" Status** — "Unavailable" means the crawler tries to fetch the robots.txt file and the server responds with status codes indicating that the resource in question is unavailable. For example, in the context of HTTP, such status codes are in the 400-499 range. If a server status code indicates that the robots.txt file is unavailable to the crawler, then the crawler MAY access any resources on the server.

> **2.3.1.4. "Unreachable" Status** — If the robots.txt file is unreachable due to server or network errors, this means the robots.txt file is undefined and the crawler MUST assume complete disallow. For example, in the context of HTTP, server errors are identified by status codes in the 500-599 range. If the robots.txt file is undefined for a reasonably long period of time (for example, 30 days), crawlers MAY assume that the robots.txt file is unavailable as defined in Section 2.3.1.3 or continue to use a cached copy.

The table also rests on two neighbouring clauses:
- §2.3.1.1: "the crawler MUST follow the parseable rules".
- §2.3.1.2: "If there are more than five consecutive redirects, crawlers MAY assume that the robots.txt file is unavailable."

### The table

The table is `manners.robots_access(status, error_class)`. It is a pure function, and each branch carries its clause.

| response to `GET /robots.txt` | `robots_status` | decision | clause | what the fetcher does |
|---|---|---|---|---|
| 2xx | `successful` | `rules` | 2.3.1.1 | parses the body with `protego` and obeys it. An empty body allows everything. |
| 3xx | — | — | 2.3.1.2 | the client follows it under `manners.follow_redirects` / `max_redirects: 5`, and this table is applied to the **final** response. |
| more than 5 redirects (`redirect_loop`), or a final 3xx the client could not follow | `unavailable` | `allow_all` | 2.3.1.2 | allows everything. |
| 4xx, including 401, 403 and 429 | `unavailable` | `allow_all` | 2.3.1.3 | allows everything. The body is not read. |
| 5xx, after the existing `backoff_on_status` retries of 503 | `unreachable` | `disallow_all` | 2.3.1.4 | refuses every fetch to the netloc for the cycle. |
| timeout, reset, DNS failure, or any other transport error (classified by `errors.classify_exception`) | `unreachable` | `disallow_all` | 2.3.1.4 ("network errors") | same as 5xx. |

**How an unreachable netloc is refused**
- `allowed()` returns False **before** the measurement carve-out (`always_fetch_paths`) is consulted. The carve-out exists so that a robots *rule* cannot hide the object of measurement. An unreachable robots.txt has no rules, and the RFC's instruction is about the server.
- `/robots.txt` itself stays fetchable. It is the bootstrap, and it is what A4 measures.
- `_gate` raises `RobotsDisallowed` with the message `<url> (robots_status: unreachable; RFC 9309 §2.3.1.4 complete disallow)`.
- The collector records the fetch as `robots_disallowed`. That class is BLIND under harness 5, so every rule returns `error` over it and never `fail` (DD-052 §6). `tests/test_manners_robots_status.py::test_an_unreachable_host_returns_error_never_fail` asserts this.

**The manners log line.** The fetcher appends one line to `Fetcher.robots_log` for each netloc it reads. The line holds `netloc`, `url`, `status`, `final_url`, `error_class`, `robots_status`, `decision`, `rfc9309` and `read_at`. `run.main` writes the list to the cycle payload as `robots_log`, so gate clause 4 of `cc_tasks/templates/scan_cycle.md` can replay each decision from the cycle's own record.

**What a cycle will see differently.**
- SAMHSA answered `/data.json` with a 5xx on the cycle of record (`2026-09-18_dcat_field_rules_RESULT.md` §1). If its robots.txt answers 5xx on cycle 5, every other fetch to that netloc becomes `error`, where before they were requests.
- On the control set, `resets_connection` now records `robots_disallowed` beside `connection_reset`. Its robots read is reset, so the netloc is unreachable, and nothing else is requested. Every verdict on it is still `error`, as its table says.

**Tests.** `tests/test_manners_robots_status.py` has 21 tests, all red before the change and green after. They drive a real `httpx.Client` over `httpx.MockTransport` on a virtual clock and cover:
- every row of the table;
- a 503 retried under the backoff and then served;
- a redirect to another host and a redirect to a 5xx;
- a redirect loop;
- one read and one log line per netloc.

---

## 1. Decision 3: the B5 control rows and their derivation

**Fixtures.** Both are in `fixtures/server.py:MODES` and serve `passes_all`'s tree plus an overlay. They are the only fixtures that declare `products`.

| fixture | `products` | overlaid files | what differs |
|---|---|---|---|
| `body_two_products` | `/index.html`, `/second.html` | `second.html`, `data.json`, `sitemap.xml`, `MANIFEST.json` | `second.html` is `passes_all/index.html` with a second product's name in `<title>`, `<h1>` and the `Dataset` name. Its `DefinedTerm` is byte-identical: "Occupied housing unit", `HU-OCC`, in `http://HOSTPORT/glossary.json`. `data.json` adds a record for the second product, and `sitemap.xml` lists it. |
| `body_two_products_split` | the same | its own `second.html`, then `body_two_products/` (overlays are now a search list) | one attribute of one page: `second.html` codes the concept `OCC-2`. |

**How the control cycle runs them** (`run.run_controls`)
- A fixture that declares `products` is scanned once per product, as `control:<fixture>/<path>`, with the fixture legs and one `Fetcher`.
- The body legs are then judged over those surfaces by `run.judge_bodies`, the same function a cycle uses.
- `CONTROL_LEGS` itself did not change. The fixture's declaration admits the body leg, not the leg list.
- `rules.body_groups` admits a control surface only when it is a body member (`rules.control_body_member`: `control:<fixture>/<path>`). One-product controls still never group.
- The E5 observation gains `products`. Its `verdicts` join a leg's verdicts across products as `a/b` when they disagree. On every fixture they agree.

**The rows**, written in `params.yaml:e5_control` before either fixture ran, with the derivation beside them, by the method used for the D2 rows:

| fixture | default | B5 | derivation |
|---|---|---|---|
| `body_two_products` | `pass` | `pass` | Default `pass`: both surfaces serve `passes_all`'s bytes with nothing blinded, so `fixture_expectations` derives no row. Each product has its own catalog record and sitemap entry, so every per-surface leg (including A5, D4 and the four DCAT field legs) reads on each product what it reads on `passes_all`. B5 `pass`: both pages carry a coded `DefinedTerm` with a set, and the one concept is coded on two products with one identifier. That is `RULE-B5-v1`'s last branch. |
| `body_two_products_split` | `pass` | `fail` | Same default. B2 reads each term's completeness, and `OCC-2` is as complete as `HU-OCC`. B5 reaches its central fail branch: "codes not shared across products". |

**First run: no mismatch.** Every fixture returned its pre-registered table (`tests/test_b5_control.py`, and inside the full suite). Recorded B5 reasons:
- `pass`: "all 1 concept(s) coded on two or more of the body's products carry one identifier (`termCode` within `inDefinedTermSet`); not measured: the cross-vintage half …"
- `fail`: "codes not shared across products: 1 of 1 concept(s) coded on two or more of the body's products carry different identifiers; first: 'occupied housing unit' as HU-OCC in http://127.0.0.1:<port>/glossary.json, OCC-2 in …"

A controls payload built from one run re-derives byte-identically (`test_the_control_b5_findings_re_derive_byte_identically`).

---

## 2. Decision 4: D4's membership, answered with its quote

**The question** (`2026-09-18_dcat_field_rules_RESULT.md` §1). D4 decides membership with `product_url in json.dumps(record)`: the product URL as a substring anywhere in a record. By that test, census.gov's home surface "owns" 1,635 of its 1,805 records.

**The sentence it rests on.** DCAT-US v1.1, `corpus/kernel/dcat-us-1-1-schema.md` (doc_id `dcat-us-1-1-schema`), field `landingPage`:

> This field is not intended for an agency's homepage (e.g. www.agency.gov), but rather if a dataset has a human-friendly hub or landing page that users can be directed to for all resources tied to the dataset.

**Answer: the current behaviour contradicts the quote.** The substring test makes an agency home page the product of every record whose URLs begin with it. The document says a home page is not what a dataset's page field names.

**The rule the quote supports.** A record is the product's when a field DCAT-US defines as a URL *of the dataset* **equals** the product URL. The fields are in `params.d4_catalog.membership_fields`, each with its DCAT-US definition beside it:

| field | DCAT-US definition |
|---|---|
| `identifier` | "It is highly recommended that a URI (preferably an HTTP URL) be used to provide a globally unique identifier." |
| `landingPage` | the sentence above |
| `distribution.accessURL` | "the URL for an indirect means of accessing the data" |
| `distribution.downloadURL` | "the direct download URL" |

- **Equality** follows RFC 3986 §6.2.2.1 (scheme and host case) and §6.2.3 (default port, empty path) and goes no further. `http` and `https` stay distinct. The default ports come from `params.d4_catalog.default_ports`, RFC 9110 §4.2.1 / §4.2.2. RFC 3986 and RFC 9110 are not in the corpus; they are cited as the canonical standards (doctrine search order 4).
- **Not counted:** `describedBy`, `references` and free text. These are URLs *about* the dataset.

**Where it lives, and why the version is `v3`**
- `collectors/dcat.product_records` implements the test. `fetch_catalog` records a `membership` block (`test`, `fields`, `records`) beside the old `contains_product`, which `-v1` and `-v2` keep reading.
- `RULE-D4-v3` (generation 13) reads `membership`. Every other branch and every prescription fragment is `-v2`'s, which `tests/test_d4_membership.py::test_v3_keeps_every_prescription_fragment_of_v2` checks.
- A stored catalog Observation has no `membership` block, so `-v3` over it is `error`, never `fail`.
- `v2clauses.dcat_record_fields` uses the same function, so the four DCAT field legs follow D4. Their pre-registration's subject was "the product's catalog record, using D4's own membership test". No stored Observation carries a field block (every one predates it), so no Finding of theirs moves.

**What it moves on the retained catalogs of the cycle of record.** This is **unpublished**, like that RESULT's §1. It comes from `scripts/exercise_dcat_field_rules.py`'s new `d4_membership` section (`logs/dcat_exercise_membership.log`, `EXIT=0`). Of the 10 surfaces with a served, parseable catalog, the two tests disagree on exactly two, and both are host-level `home` surfaces:

| surface | catalog records | substring test | DCAT-US field test |
|---|---|---|---|
| `home:www.census.gov` (`https://www.census.gov/`) | 1,805 | 1,635 | **0** |
| `home:www.bea.gov` (`https://www.bea.gov/`) | 26 | 14 | **0** |
| `flagship:www.federalreserve.gov/econres/scfindex.htm` | 167 | 1 | 1 |
| the other 7 | — | 0 | 0 |

- **G4's exercised distribution** moves from 3 pass / 35 fail / 8 error to **1 / 37 / 8**. The two passes that were "readings of a host's catalog through D4's lens" are gone. The script's pinned `EXPECTED_DISTRIBUTION` moved with a comment saying why.
- **B1, B4 and D3** do not move: 38 fail / 8 error each.
- **Every product surface** agrees under both tests. The contradiction was confined to the case the quote names.

---

## 3. Premises the task file got wrong

1. **"`rules/__init__.py` (`CONTROL_LEGS`)".**
   - `CONTROL_LEGS` is in `run.py:118`.
   - Decision 3 needed `run.run_controls` to scan a fixture's products and judge body legs over them. `rules/__init__.py` moved anyway, for `body_groups`: a two-product control is a body, and `body_groups` excluded every `control:` surface. `CONTROL_LEGS` is unchanged, and `test_b5_alone_is_judged_per_body` still holds.
2. **"write the rule … as `RULE-D4-v2`".** `RULE-D4-v2` has been shipped since the 2026-09-06 conformance review (POD v1.1 validation). The new version is `RULE-D4-v3`.
3. **"write the rule the quote supports", read as a rule-only change.**
   - Membership is decided in the **collector** (`dcat.fetch_catalog` → `contains_product`). A rule is pure and has no body to test, so no rule could implement the quote.
   - The write set gained `collectors/dcat.py`, `collectors/v2clauses.py` (the field legs follow D4) and `params.d4_catalog` (two keys).
4. **"record `robots_status: unavailable` on the Observation".**
   - The fetcher builds no Observation; the collectors do, and editing every collector was outside the write set.
   - As implemented, the decision is carried in three places:
     - the refused fetch's class (`robots_disallowed`);
     - the refusal message, for collectors that record it (`… robots_status: unreachable; RFC 9309 §2.3.1.4 …`);
     - the payload's `robots_log` line for the netloc, joined by netloc.
   - An `unavailable` netloc produces no refusal, and its line in `robots_log` is the record.
   - The name `robots_status` already exists on A4's Observation as the integer HTTP status, so the string form lives only in `robots_log`.
5. **Decision 3's write set omitted the record.**
   - `spec:E5.collector_pin` is derived from `fixtures.server.MODES`, so adding two fixtures moves the framework of record. It moved through `framework_writeback_rules.py` and was projected.
   - Decision 4 moved `spec:D4.rule_id`, three `Action.verifies_by` and three `REMEDIATES.rule_id` (`tag_prescriptions`), and `ind:D4.tier_source` (`tag_measurement_tiers`).
   - Four derived views followed: the site copy and `index.json`, `scan_tool_map.md`, and `mcp_over_the_graph.md`.
   - On the MCP page, `current_rules` went from 17 to 16. `RULE-D4-v3` has no `:Rule` node until a cycle judges under it, and `-v2` is no longer current. That is the true graph state, not a defect.
6. **"`state/`, `corpus/`, `docs/reports/` byte-identical".** `corpus/` moved on one file, **by this session's own defect**, and it is reported rather than hidden.
   - **The litter.** `tests/test_b5_control.py` first ran its control cycle in a **module-scoped** fixture. That fixture is set up before `conftest.py`'s function-scoped evidence redirect, so fixture bodies went to the evidence guard's redirect. The session's own exploratory `run_controls` calls from stdin did the same. Together: 2,190 redirects.
   - **The fix.** The fixture now sets its own tmp evidence root. The redirect log stayed at 0 across the whole gate.
   - **The clearance.** The log was cleared the only way DD-063 decision 3 allows: `scripts/quarantine_fixture_evidence.py --clear-redirects --wrote-by "<this task …>"` (`logs/manners_sweep.log`). That appends one clearance record to the tracked `corpus/quarantine/evidence_scan_fixture/reason.txt`.
   - **Nothing else moved.** Zero committed-store blobs were quarantined or removed. `check_protected_manners.sh` asserts that the file only grew, by one clearance naming this task.
7. **Decision 2, "Prior payloads are not re-derived on this change. Collection code is not judgement code."** That holds for decision 1. Decision 4 turned out to need a judgement change (a new rule version), and it keeps the same property differently: `-v2` stays in `REGISTRY`, no stored Finding is under `-v3`, and `make gate-task`'s byte-identical re-derivation passed.
8. **The B5 control Finding's target is not a `control:` id.** `RULE-B5-v1.target_of` names the body's well-known row, `host:<netloc>`. For a fixture that is `host:127.0.0.1:<port>`, while every other control Finding carries `control:…`.
   - **What is unaffected.** It sits in `control_findings_detail`, E5 checks it by leg, and it re-derives.
   - **The risk.** A reader that classifies Findings by the `host:` prefix, such as `withdrawn_legs.census` over the graph, could count it as a host Finding.
   - **What would fix it.** A `control:` target needs a new B5 version, because `-v1` is pre-registered and may not be edited. It is listed as open below, not done here.

## 4. Gate

**Tier:** the full suite (the `make gate-full` command, run to its own log), plus `make gate-task`, because a rule module, the registry and `body_groups` changed. The slow control tier ran first.

| check | result | log |
|---|---|---|
| slow control tier (`-m slow`), run first | **25 passed, 0 skipped, 0 xfailed, 2571 deselected**, 948.84 s, `EXIT=0` | `logs/manners_slow.log` |
| `make gate-task`, fast tier | **2556 passed, 3 skipped, 12 xfailed, 25 deselected**, 521.82 s | `logs/manners_gate_task.log` |
| `make gate-task`, re-derivation | **22 passed, 0 skipped, 0 xfailed, 25 deselected**, 10.07 s, `EXIT=0` (the line: `/opt/anaconda3/bin/python3 -m pytest tests/test_scan_harness_v4.py -q -rs -k re_derives` → `22 passed, 25 deselected in 10.07s`) | `logs/manners_gate_task.log` |
| full suite (`pytest tests/ assessment/ -q -rs`, the `gate-full` command) | **2581 passed, 3 skipped, 12 xfailed, 0 deselected**, 1481.72 s, `EXIT=0` | `logs/manners_full.log` |
| skips (3, as the task expected) | `tests/test_dispatch_config.py:333` (interactive_only, dispatched session); `tests/test_scan_harness.py:283` (E5 judges the cycle's controls, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | `logs/manners_full.log` |
| `seldon verify` | all checks passed; replay skipped as expensive (its default); `EXIT=0` | `logs/manners_seldon_verify.log` |
| protected paths (`scripts/check_protected_manners.sh`) | `record: 6 node(s) moved, all derived D4/E5 cells`; `params: two control tables, two D4 keys`; `PROTECTED PATHS OK`; `EXIT=0` | `logs/manners_protected.log` |
| evidence-guard redirect log at the gate | 0 lines | `corpus/quarantine/evidence_scan_fixture/unlicensed/redirects.jsonl` |
| framework projection | `load_framework_graph.py` `EXIT=0`, run after all three write-backs; `tests/test_framework_projection_roundtrip.py` green inside the suite, not skipped | `logs/manners_load_framework.log` |
| record write-backs | `framework_writeback_rules.py`, `tag_prescriptions.py`, `tag_measurement_tiers.py`, each `EXIT=0` | `logs/manners_wb_rules.log`, `logs/manners_wb_prescriptions.log`, `logs/manners_wb_tiers.log` |
| derived views | `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest`, `scan_tool_map.py` and `mcp/airkg_doc.py`, each `EXIT=0` | `logs/manners_site.log`, `logs/manners_tool_map.log`, `logs/manners_mcp_doc.log` |
| retained-catalog exercise (§2) | deterministic, 0 bodies missing, `EXIT=0` | `logs/dcat_exercise_membership.log` |

**The three record events** (`events/batch-033_framework.jsonl`, +3 lines, append-only):

| event | time (UTC) | script | delta | framework sha256 |
|---|---|---|---|---|
| `0bbed4431c454ee4af0b6ac7482446d9` | 11:25:03 | `framework_writeback_rules.py` | `spec:D4.rule_id` → `RULE-D4-v3`; `spec:E5.collector_pin` names the two body fixtures | `595acb08…af5933` |
| `94da35ed15c54e14af5eebb1b9cd069c` | 11:25:07 | `tag_prescriptions` | 3 D4 `Action.verifies_by` and 3 `REMEDIATES.rule_id` → `RULE-D4-v3` | `19097637…79710b` |
| `1785e5a5ad744f7583a99cb265079036` | 11:25:16 | `tag_measurement_tiers` | `ind:D4.tier_source` cites `RULE-D4-v3` | `de7b56e3…06f762` |

## Open, for the next task

- **A `control:` target for a body rule's control Finding** (premise 8). This needs `RULE-B5-v2` or a harness-level target override that a re-derivation reproduces.
- **429 on robots.txt.** It is read as the RFC reads it: 4xx, unavailable, allow all, after the existing backoff. Google's crawler documentation treats 429 as a server error. That document is not in the corpus, and admitting it and deciding is a separate question.
- **Cycle 5 (2026-10-05)** is the first cycle judged under `RULE-D4-v3` and under the status-keyed robots read. The first `robots_log` on a payload arrives with it.
