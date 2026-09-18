# RESULT: the requirements layer is on the record — 13 tools, 19 preconditions, 37 `REQUIRES` edges — and `get_requirements` answers an indicator, a body and the whole map

**Task:** `cc_tasks/2026-09-18_requirements_layer.md`. I globbed `2026-09-18_requirements_layer_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher from HEAD `76467ac`. The predecessor named on the SEQUENCING line, `2026-09-18_rejudge_seven_legs.md`, has its RESULT on `0ab3afb`, so the order held.
**Framework layer served:** DN-005 §2.2 and §2.4 — the expert-system edge, indicator → test → requirement.
**Spend:** zero model calls. **Network:** none beyond `git push`; nothing was fetched.
**Gate:** green, every command run to its `EXIT=` line before this file was written (§4).
- **full tier** (`make gate-full`'s command, `/opt/anaconda3/bin/python3 -m pytest tests/ assessment/ -q -rs`, detached and polled): **2652 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed**, 1499.66 s, `EXIT=0`. The three skips are the expected three.
- `seldon verify`: **All checks passed**, `EXIT=0`.
- `scripts/check_protected_requirements.sh`: **PROTECTED PATHS OK**, `EXIT=0`.
- framework projection round-trip (DD-057): **9 passed**, `EXIT=0`, including the new `test_every_requires_edge_reached_the_graph_with_its_properties`.

**In one paragraph.** Every indicator the harness cannot measure alone now points at what would close it. The tests this project cannot run are recorded as the tools, accounts, records, evaluation sets, second measurements and grants they need, with a cost for each tool and a `who_provides` for everything. Every edge cites a corpus sentence, a record field or a frozen tool-map row, and the suite opens each citation to check it is where it says. `get_requirements` on the MCP turns that into the query the operator's ruling asks for. For **BLS** on the cycle of record it says: *"The publisher admits the identified client (publisher_grant; provided by publisher) would unlock 14"*. That is all fourteen of BLS's error cells on one line, followed by the 33 tests no body is measured on, grouped under the benchmark set, account or tool that would unlock each. The tool map §3 is now generated from the record. Two decisions in the task file could not stand as written, and §3 gives both. The node label is `AssessmentTool`, because `Tool` is a KG label with 262 extracted nodes that the framework loader would have deleted. There is a sixth precondition kind, `publisher_grant`, because the two largest classes of blind cell need a grant that none of the five kinds describes.

---

## 0. Counts, the `notional:` count, and the indicators with no requirement

Read from the record as written (`scripts/tag_requirements.py --check`) and confirmed by live Cypher after projection (`logs/requirements_cypher.log`). The Cypher is valid because the round-trip gate is green.

**Nodes: 32.**

| label | kind | n | cost band (tools) | who provides |
|---|---|---|---|---|
| `AssessmentTool` | `open_source` | 8 | tooling | this_project |
| `AssessmentTool` | `hosted_free` | 2 | none | this_project |
| `AssessmentTool` | `hosted_paid` | 1 | procurement | this_project |
| `AssessmentTool` | `platform_account` | 2 | none | publisher |
| `AssessmentTool` | `agency_internal` | 0 | — | — |
| `Precondition` | `agency_records` | 8 | — | publisher |
| `Precondition` | `benchmark_set` | 6 | — | this_project |
| `Precondition` | `second_cycle` | 2 | — | this_project |
| `Precondition` | `site_owner_account` | 2 | — | publisher |
| `Precondition` | `publisher_grant` | 1 | — | publisher |
| `Precondition` | `page_script` | 0 | — | — |

**Edges: 37 `REQUIRES`**, all from framework indicators (`requires: 37`, `requires_on_candidate_indicators: 0`). By `closes`: **tier 27, unmeasured_half 4, coverage 6**. By `source_kind`: **record 21, corpus 10, tool_map 6**. Every edge carries a source. The suite opens all 37, the 9 tool documents and the 6 error-class citations (`test_every_edge_cites_and_every_citation_opens`, `test_every_tool_doc_source_opens_or_says_why_it_is_not_on_disk`). A negative control proves the checker refuses a citation that does not open.

**`notional:` costs: 13 of 13.** Every tool's `cost_source` is `notional:tool_kind:<kind>, task 2026-09-18_requirements_layer`. None is a document locator, because no document on disk states what running any of these tools costs a publisher. `cost_band: tooling` reaches 8 tools, the first use of the value since `2026-09-17_notional_bands_RESULT.md` §1 recorded that no action class reached it. Preconditions carry no band (decision 1).

**Four tools have no document on disk** and carry `doc_source: none_on_disk` with a `doc_source_note`: `tool:ultimate-sitemap-parser` (already a harness dependency as `usp`), `tool:openapi-spec-validator`, `tool:prance` and `tool:catalog-data-gov-ckan-api`. The tool-map row at `76467ac` is the source that names each one.

**Error classes.** `pre:publisher-admits-the-identified-client` unlocks `refused` and `robots_disallowed`. `pre:second-scan-cycle` unlocks `dns`, `timeout`, `connection_reset` and `http_5xx`. The BLIND classes of `scan.errors.CLASSES` that nothing unlocks are `parse_error`, `redirect_loop`, `collector_unavailable` and `unknown`. For each of these, what fixes it is the publisher's response or this project's code, so no grant or tool applies (`UNMAPPED_ERROR_CLASSES`). The suite holds both lists to the harness's own map.

**Indicators in scope with at least one requirement: 27.** A2, A5, A6, A7, A11, B5, C1, C2, C3, C4, C5, D4, E1, E2, E3, E4, E6, E7, E8, E9, F1, F2, F3, F5, F6, G2 and G6.

**Indicators in scope with none, and why.** The reason is on the node as `requirement_none_reason`, or for an unassigned row it is the unchanged `tier_unassigned_reason`.

| code | why no requirement |
|---|---|
| B1 | The unmeasured half is whether the dictionary or the listed variables are "comprehensive", a judgement about their contents that no admitted document defines a test for. What is missing is an instrument, not a tool, an account or anything the body holds. |
| B2 | The "versioned" clause has no field in any admitted document. What is missing is a standard. |
| B4 | The suppression-rules clause has no field in any admitted document. What is missing is a standard. |
| D3 | Whether the lineage runs from collection through processing is readable by walking `wasDerivedFrom` on the catalog records the rule already fetches. That needs a rule this project would write, not a requirement of the body's. |
| G4 | The statutory-mandate and statistical-versus-administrative clauses have no field in any admitted document. What is missing is a standard. |
| G1-O | Measured. The G1 instrument exists and judged it (DD-036), so nothing stands between it and a verdict. |
| B6 | Unassigned, reason unchanged. It names "a different instrument" (readability, freshness), not a tool or grant. |
| G3 | Unassigned, reason unchanged. It names an SDMX collector this project would build. |
| G5 | Unassigned, reason unchanged. No admitted document names the field. |

Harness legs with no recorded unmeasured half (A1, A3, A4, A8, A9, A10, A12, B3, D1, D2, E5, F4, G1-D) are out of scope, and `get_requirements` says for each *"measured by this harness with RULE-…; no tool, account or record stands between it and a verdict"*. Four harness legs (A2, A5, A6, D4) carry `coverage` edges only, from the tool map §3 rows. See §3 premise 5.

## 1. The full requirement table

One row per `REQUIRES` edge, generated from the record (`logs/requirements_table.md`). Rows that share an indicator and a route are needed together. Two routes are alternatives. A precondition's cost is `—`.

| indicator | closes | route | clause | requirement | kind | cost | who provides | source |
|---|---|---|---|---|---|---|---|---|
| A11 | unmeasured_half | agency_logs | enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs) | `pre:edge-and-crawler-request-logs` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:A11` field `tier_note`: "The enforced and observed layers need edge or WAF logs and crawler request logs" |
| A11 | unmeasured_half | cloudflare_zone | enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs) | `pre:cloudflare-zone-account` | site_owner_account | — | publisher | corpus/kernel/cloudflare-ai-crawl-control-manage-crawlers.md (doc_id `cloudflare-ai-crawl-control-manage-crawlers`), 'Manage AI crawlers': "Log in to the [Cloudflare dashboard ↗](https://dash.cloudflare.com/), and select your account and domain." |
| A11 | unmeasured_half | cloudflare_zone | enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs) | `tool:cloudflare-ai-crawl-control` | platform_account | none | publisher | corpus/kernel/cloudflare-ai-crawl-control.md (doc_id `cloudflare-ai-crawl-control`), overview: "**Monitor robots.txt compliance** - Track which crawlers follow your directives and create enforcement rules" |
| A2 | coverage | openapi_spec_validator | Documented public API | `tool:openapi-spec-validator` | open_source | tooling | this_project | docs/design/scan_tool_map.md §3 at commit 76467ac, row 'OpenAPI / AsyncAPI detection and validation': "`openapi-spec-validator`, `prance`" |
| A2 | coverage | prance | Documented public API | `tool:prance` | open_source | tooling | this_project | docs/design/scan_tool_map.md §3 at commit 76467ac, row 'OpenAPI / AsyncAPI detection and validation': "`openapi-spec-validator`, `prance`" |
| A5 | coverage | bounded_crawl | sitemap covers data products | `tool:scrapy` | open_source | tooling | this_project | docs/design/scan_tool_map.md §3 at commit 76467ac, row 'Sitemap crawl and URL inventory': "`ultimate-sitemap-parser`, or `scrapy` for a bounded crawl" |
| A5 | coverage | sitemap_walk | sitemap covers data products | `tool:ultimate-sitemap-parser` | open_source | tooling | this_project | docs/design/scan_tool_map.md §3 at commit 76467ac, row 'Sitemap crawl and URL inventory': "`ultimate-sitemap-parser`, or `scrapy` for a bounded crawl" |
| A6 | coverage | extruct_at_scale | markup valid on product pages | `tool:extruct` | open_source | tooling | this_project | docs/design/scan_tool_map.md §3 at commit 76467ac, row 'schema.org `Dataset` extraction at scale': "`extruct` (already a dependency) driven over a URL inventory rather than one page" |
| A7 | tier | wayback_cdx | Persistent URLs/DOIs for products and vintages | `tool:wayback-cdx-server` | hosted_free | none | this_project | corpus/tools/wayback-cdx-server/README.md (doc_id `wayback-cdx-server-api-readme`), 'Filtering': "Results may be filtered by timestamp using **from=** and **to=** params" |
| B5 | unmeasured_half | second_cycle | across products/vintages | `pre:second-scan-cycle` | second_cycle | — | this_project | framework/ai_readiness_framework.json node `spec:B5` field `note`: "The cross-vintage half is unmeasured until a second cycle with term codes." |
| C1 | tier | benchmark | Benchmark question set per product | `pre:product-question-benchmark` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:C1` field `indicator`: "Benchmark question set per product" |
| C2 | tier | probe_protocol | Entailment-judged: do model statements about the product entail from product text? | `pre:entailment-probe-set` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:C2` field `tier_note`: "The definition names the probe protocol, 're-aimed', as the instrument; it has not been re-aimed at a data product." |
| C3 | tier | benchmark | does retrieval return the vintage asked for? | `pre:vintage-disambiguation-set` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:C3` field `indicator`: "Version/vintage disambiguation: does retrieval return the vintage asked for?" |
| C4 | tier | bing_ai_performance | Generative engines citing the product cite the authoritative page (not aggregators) | `pre:bing-webmaster-tools-verified-site` | site_owner_account | — | publisher | corpus/kernel/bing-ai-performance-public-preview-2026.md (doc_id `bing-ai-performance-public-preview-2026`), 'Extending Search Insights to AI Answers': "Bing Webmaster Tools has long helped website owners understand indexing, crawl health, and search performance." |
| C4 | tier | bing_ai_performance | Generative engines citing the product cite the authoritative page (not aggregators) | `tool:bing-webmaster-tools-ai-performance` | platform_account | none | publisher | corpus/kernel/bing-ai-performance-public-preview-2026.md (doc_id `bing-ai-performance-public-preview-2026`), introduction: "For the first time, you can understand how often your content is cited in generative answers, with clear visibility into which URLs are referenced" |
| C4 | tier | engine_queries | Generative engines citing the product cite the authoritative page (not aggregators) | `pre:generative-engine-query-set` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `spec:C4-auto` field `note`: "The AUTO leg needs a generative engine's citations as input, which is the EVAL half of the indicator." |
| C4 | tier | engine_queries | Generative engines citing the product cite the authoritative page (not aggregators) | `tool:perplexity-ai` | hosted_paid | procurement | this_project | corpus/kernel/aggarwal-2024-geo-generative-engine-optimization.pdf (doc_id `aggarwal-2024-geo-generative-engine-optimization`), section 3.1: "Perplexity.ai, which is a commercially deployed generative engine" |
| C5 | tier | aidrin | Product scored against published AI-data-readiness metrics | `tool:aidrin` | open_source | tooling | this_project | corpus/pilot/aidrin-hiniduma-2024.pdf (doc_id `aidrin-hiniduma-2024`), the paper's tool section: "Users can install the AIDRIN PyPI package via the command line and use it for data readiness assessment" |
| D4 | coverage | federal_catalog | data.gov/agency inventory current | `tool:catalog-data-gov-ckan-api` | hosted_free | none | this_project | docs/design/scan_tool_map.md §3 at commit 76467ac, row 'Federal DCAT catalog presence': "`catalog.data.gov`'s CKAN action endpoints answered HTTP 404 on 2026-09-08" |
| E1 | tier | agency_report | reported separately from fit-for-use evals (EVAL set) | `pre:published-conformance-and-evaluation-report` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:E1` field `tier_note`: "the reading is of a published report, not a served surface" |
| E2 | tier | agency_records | pre-registered before results | `pre:threshold-preregistration-records` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:E2` field `tier_source`: "the agency's own timestamps are the only record of that order" |
| E3 | tier | agency_records | results never pooled across versions | `pre:evaluation-set-version-records` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:E3` field `tier_note`: "a pass needs the agency's records" |
| E4 | tier | agency_records | Public eval sets have a held-out rotation | `pre:held-out-rotation-records` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:E4` field `tier_source`: "whether a rotation exists is a fact only the agency holds" |
| E6 | tier | benchmark | Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model | `pre:product-question-benchmark` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:E6` field `tier_note`: "it presupposes the C1 to C3 evaluations" |
| E6 | tier | benchmark | Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model | `pre:vintage-disambiguation-set` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:E6` field `tier_note`: "it presupposes the C1 to C3 evaluations" |
| E7 | tier | agency_records | mean-time-to-closure tracked | `pre:eval-failure-closure-records` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:E7` field `tier_source`: "mean time to closure is measured over the agency's own ticket history" |
| E8 | tier | benchmark | Versioned golden question/answer sets re-run on schedule against the product surface | `pre:product-question-benchmark` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:E8` field `indicator`: "Versioned golden question/answer sets re-run on schedule against the product surface" |
| E8 | tier | benchmark | baseline deltas alarmed | `pre:second-evaluation-run` | second_cycle | — | this_project | framework/ai_readiness_framework.json node `ind:E8` field `indicator`: "baseline deltas alarmed" |
| E9 | tier | benchmark | Standing adversarial bank: vintage traps, confusable series, unit traps, DP-noise misreads, suppression probes | `pre:adversarial-bank` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:E9` field `indicator`: "Reported as break modes, not just pass rates" |
| F1 | tier | agency_records | before going live | `pre:release-validation-records` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:F1` field `tier_source`: "happened on the agency's side of publication and leaves nothing on the served surface" |
| F2 | tier | oasdiff_two_releases | API/schema changes are versioned | `pre:second-scan-cycle` | second_cycle | — | this_project | framework/ai_readiness_framework.json node `spec:F2` field `note`: "Becomes collectible once the scan runs twice." |
| F2 | tier | oasdiff_two_releases | compatibility checked mechanically | `tool:oasdiff` | open_source | tooling | this_project | corpus/tools/oasdiff/README.md (doc_id `oasdiff-readme`), opening description: "Command-line tool to compare and detect breaking changes in OpenAPI specs." |
| F3 | tier | wayback_cdx | endpoints survive a new vintage | `tool:wayback-cdx-server` | hosted_free | none | this_project | corpus/tools/wayback-cdx-server/README.md (doc_id `wayback-cdx-server-api-readme`), 'Url Match Scope': "**matchType=prefix** will return results for all results under the path" |
| F5 | tier | agency_records | AI-consumer regression run before promotion | `pre:staging-regression-records` | agency_records | — | publisher | framework/ai_readiness_framework.json node `ind:F5` field `tier_source`: "only the agency can say that it ran" |
| F6 | tier | slsa_verifier | Signed releases / provenance attestations | `tool:slsa-verifier` | open_source | tooling | this_project | corpus/crosswalk/slsa-specification-v1-0.md (doc_id `slsa-specification-v1-0`), 'Consumer': "Client-side verification tooling can be either standalone, such as [slsa-verifier](https://github.com/slsa-framework/slsa-verifier), or built into the package ecosystem client." |
| G2 | tier | benchmark | EVAL: vintage disambiguation (ties C3) | `pre:vintage-disambiguation-set` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:G2` field `tier_note`: "the reading the definition asks for is C3's evaluation" |
| G6 | tier | break_cases | an AI system asked to compare values across a break must surface the break | `pre:series-break-cases` | benchmark_set | — | this_project | framework/ai_readiness_framework.json node `ind:G6` field `tier_note`: "The consumer-side half is a G1-style preservation test" |

Notes on the edges where a clause stays open, all carried on the edge's `note`:
- **A7:** the DOI half has no requirement, because no resolver's documentation is on disk.
- **F3:** series identifiers and geography codes live in response bodies, which the CDX index does not carry.
- **G2 and G6:** each has a declared half that needs a rule, not a requirement.
- **C4, Bing route:** it counts the owner's own citations on Microsoft's AI surfaces only. Whether an aggregator was cited *instead* needs the engine route.

## 2. `get_requirements` — one indicator, one body

Full answers: `logs/requirements_get_C4.json` and `logs/requirements_get_BLS.json`. Every locator in both, and in the whole-map answer, resolves (`test_every_locator_in_a_requirements_answer_resolves`; `test_every_locator_in_every_tool_answer_resolves` in `tests/test_mcp_server.py` now covers all three shapes).

### `get_requirements(indicator="C4")`, locators elided except on the first requirement

```
indicator: C4   measurement_tier: M   measurement_basis: evaluation
routes_mean: requirements on one route are needed together; two routes are alternative ways to run the test

route bing_ai_performance — which of the product's pages AI answers cite, and how often   (closes: tier)
  tool:bing-webmaster-tools-ai-performance   platform_account   cost none   provided by publisher
    source: corpus/kernel/bing-ai-performance-public-preview-2026.md (doc_id `bing-ai-performance-public-preview-2026`),
            introduction: "For the first time, you can understand how often your content is cited in generative
            answers, with clear visibility into which URLs are referenced"
    locators: record tool:bing-webmaster-tools-ai-performance; document bing-ai-performance-public-preview-2026
              ('Page-level citation activity'); record_edge ind:C4-[REQUIRES]->tool:…; record ind:C4;
              document bing-ai-performance-public-preview-2026 ('introduction')
  pre:bing-webmaster-tools-verified-site     site_owner_account   —            provided by publisher
    source: … 'Extending Search Insights to AI Answers': "Bing Webmaster Tools has long helped website owners
            understand indexing, crawl health, and search performance."

route engine_queries — whether a generative engine's answer about the product cites the agency page or an aggregator
  tool:perplexity-ai                         hosted_paid          cost procurement   provided by this_project
    source: corpus/kernel/aggarwal-2024-geo-generative-engine-optimization.pdf (doc_id `aggarwal-2024-geo-…`),
            section 3.1: "Perplexity.ai, which is a commercially deployed generative engine"
  pre:generative-engine-query-set            benchmark_set        —            provided by this_project
    source: framework/ai_readiness_framework.json node `spec:C4-auto` field `note`: "The AUTO leg needs a
            generative engine's citations as input, which is the EVAL half of the indicator."

band_note: Notional relative cost by tool kind. It orders requirements against each other; it does not price a
licence, an account or anyone's time, and an agency adjusts it for its own platform, staffing and procurement path.
```

### `get_requirements(body="BLS")`, the `line` of each requirement

```
14 error cell(s) for BLS on scan_2026-09-10_rj2; 4 unmeasured half/halves and 33 untested test(s) that no body is measured on
- The publisher admits the identified client (publisher_grant; provided by publisher) would unlock 14: A1 on flagship:www.bls.gov/cpi/, A10 on home:www.bls.gov, A11-declared on home:www.bls.gov, A2 on flagship:www.bls.gov/cpi/, A3 on flagship:www.bls.gov/cpi/, A4 on home:www.bls.gov, A5 on home:www.bls.gov, A6 on flagship:www.bls.gov/cpi/, A8 on flagship:www.bls.gov/cpi/, A9 on flagship:www.bls.gov/cpi/, B3 on flagship:www.bls.gov/cpi/, D1 on flagship:www.bls.gov/cpi/, D4 on flagship:www.bls.gov/cpi/, F4 on flagship:www.bls.gov/cpi/
- Per-product question benchmark (benchmark_set; provided by this_project) would unlock 3: C1 (indicator), E6 (indicator), E8 (indicator)
- Vintage disambiguation set (benchmark_set; provided by this_project) would unlock 3: C3 (indicator), E6 (indicator), G2 (indicator)
- A second scan cycle (second_cycle; provided by this_project) would unlock 2: B5 (unmeasured half), F2 (indicator)
- Wayback Machine CDX Server API (hosted_free; provided by this_project) would unlock 2: A7 (indicator), F3 (indicator)
- A verified site in Bing Webmaster Tools (site_owner_account; provided by publisher) would unlock 1: C4 (indicator)
- The publisher's Cloudflare zone (site_owner_account; provided by publisher) would unlock 1: A11 (unmeasured half)
- Edge/WAF and crawler request logs (agency_records; provided by publisher) would unlock 1: A11 (unmeasured half)
- … 24 further lines, one per requirement, each unlocking 1 (full answer in logs/requirements_get_BLS.json)
no_requirement: B1, B2, B4, D3, G4 (unmeasured halves with a reason); B6, G3, G5 (unassigned, reason unchanged)
```

BLS's 14 error cells carry the classes `refused` and `robots_disallowed`. Where one cell carries both, it is counted **once** under the grant (`test_a_cell_is_counted_once_under_a_requirement`). Across the 16 bodies on the cycle of record, eight have error cells: BLS 14, BTS 14, ORES 14, EIA 5, NASS 2, SOI 2, NCHS 1, SAMHSACBHS 1. Every one is unlocked by the grant, except the two `http_5xx` cells (NCHS, SAMHSACBHS), which fall under `pre:second-scan-cycle`.

## 3. Every premise this task file got wrong

1. **"Two node types … `Tool`".** `Tool` is a KG node type (`kg/schema.yaml`, "Software that implements one or more Measures"). The literature extraction holds **262** of them in the same database, including Search Console, Bing Webmaster Tools, extruct and slsa-verifier. `load_framework_graph.py` owns its labels by `DETACH DELETE` and rebuild, and `build_projection.py` owns the KG labels the same way, so a framework `Tool` would have deleted the literature's tools on the next framework load, and the next KG replay would have deleted the framework's. The label is **`AssessmentTool`**, following the schema's own precedent ("Labels are prefixed `Assessment*` because the KG's own `Framework` label is taken"). `Precondition` collides with nothing and keeps its name. Ids stay `tool:<slug>`. `test_the_kg_tool_label_is_never_reused` guards it, and `tests/test_framework_graph.py::test_assessment_labels_are_invisible_to_the_extraction_parser` would have failed on `Tool` anyway. After projection, the KG `Tool` count is still 262 and no node carries both labels.
2. **The five precondition kinds.** `refused` (the edge answered 401/403/429 to the identified client on a robots-permitted path) and `robots_disallowed` are, by far, the blind cells on the cycle of record. What would let the harness see them is the publisher admitting the identified client. That is not an account the harness logs into, a script, agency records, a set this project builds or a second cycle. A sixth kind, **`publisher_grant`**, was added. It meets the bar the notional-bands task set for a sixth class, which is two things needing it. **`page_script` has 0 nodes:** no definition in scope names a tag or a beacon. It stays in the enumeration for the same reason `tooling` stayed in `COST_BANDS`.
3. **"The `tier_note`s carrying 'unmeasured'".** Taken literally, the word is on B2, B4, B5 and G4 among the harness legs (and A7 and F3, which are tier O). Three more harness legs record an unmeasured half without the word: A11 ("need edge or WAF logs and crawler request logs"), and B1 and D3 ("not measured"). Scope took all seven (`UNMEASURED_HALF`, each with its verbatim words). A test fails if a note that says either phrase is ever missing from the list.
4. **Decision 2's judged-reading rule ("agency_records or page_script as the definition says")** holds for E1 and E3 (agency records). It does not hold for **G6**, whose definition names "an AI system asked to compare values across a break", which is a consumer-side test needing a set of documented breaks. G6 requires `pre:series-break-cases` (`benchmark_set`). **G1-O** is judged and measured, so it has no requirement and says so.
5. **"The tool map §3 gap table is the prose this graph write replaces."** Four of its five rows are now tools and edges. The fifth, *Response-header profile*, names no tool ("no library needed") and no indicator ("No indicator consumes them yet"). A `REQUIRES` edge needs an indicator at its tail, so the row is not carried. `DROPPED_TOOL_MAP_ROWS` in `scripts/tag_requirements.py` records it and why. The four carried rows reach **harness legs outside decision 2's scope** (A2, A5, A6, D4). They are carried as `closes: coverage`, which means the rule reads the clause on the one surface fetched and the tool would carry it across the site. `test_no_indicator_outside_scope_carries_a_requirement` allows exactly that and nothing else.
6. **`ind:F6.tier_note` says "the tool map §3 and the open-tool record name no tool for F6".** The SLSA specification on disk names one twice: `slsa-verifier`, as standalone client-side verification tooling. F6 requires it. The note is left as written (this task writes no tier). The tool's own `note` records the correction.
7. **"Every tool named is documented on disk or named by the tool map"** holds, but on disk is not the same as in the graph. The two tool READMEs admitted earlier today (`oasdiff-readme`, `wayback-cdx-server-api-readme`) are in `corpus/manifest.json` with no `manifest_add` event, so the KG projection holds **no `Document` node** for either. A `document` locator naming them could not resolve. The MCP resolver now falls back to the manifest (the corpus gate, DD-003). It resolves a doc_id by its manifest entry's canonical path **and sha256**, and says in the detail that the projection lacks the node. The projection itself is not repaired here. That is outside the write set, and it is the next task's decision: emit the events, or project Documents from the ledger.
8. **Decision 4 asks for "kind, cost and who provides" for every requirement, but decision 1 gives `who_provides` to preconditions only.** Tools gained it by kind (`WHO_RUNS_BY_KIND`: a tool this project installs or queries is `this_project`'s; a platform account's report is the `publisher`'s). This was a **second `framework_writeback` event**, so the shard gained two lines, not one. The protected-paths check asserts exactly two.
9. **Decision 2's generative-engine rule** reaches C4 only. C1 and C2 name "a model", which this project already calls under Max OAuth, so they carry no `hosted_paid` tool. Google Search Console was considered for C4 and rejected on its own documentation (`google-ai-features-and-your-website`: AI features "are included in the overall search traffic … within the 'Web' search type"). It does not separate AI citations from search, so it cannot read C4.
10. **Decision 2: "The three unassigned rows get whatever their reason names."** None of the three reasons names a tool, account or record. B6 names a different instrument, G3 an SDMX collector this project would build, and G5 a field that does not exist. All three get nothing, and their reasons are unchanged; the suite asserts they carry no `requirement_none_reason`.
11. **The write set** did not list five files that had to move, and none of them was optional. `scripts/framework_writeback.py` (`recount` is where a counts key is derived; four keys were added and `counts_basis` says what they count). `scripts/load_framework_graph.py` (the label and edge whitelists, and a loader branch for `REQUIRES`'s properties). And three existing tests that pin the shapes this task moved: nine MCP tools became ten, the preserved-node census of the single writer, and the projected labels of the round-trip gate. The MCP resolver gained two locator kinds: `record_edge`, and `git` (a text in a file *at a commit*, for the frozen tool-map rows).
12. **The tool-map citations cite a commit, not the file.** Decision 5 makes §3 a view of the record. A source pointing at the current §3 would therefore cite itself. Every `tool_map` source names `docs/design/scan_tool_map.md §3 at commit 76467ac` and is checked with `git show`. That follows the `TOOL_MAP_AT … 52af6c7` precedent in `tag_measurement_tiers.py`.

## 4. Gate

**Tier:** full, `make gate-full`'s command run directly so the log carries this task's name, detached and polled to `EXIT=`.

| check | result | log |
|---|---|---|
| tests first | `tests/test_requirements.py` written before the tagger: 16 failed, 11 errors, 5 passed (red); 34 passed after | (run inline) |
| tagger | `--check` validated; write-back 1: +13 `AssessmentTool`, +19 `Precondition`, +37 `REQUIRES`, 6 indicators changed; write-back 2: 13 tools gained `who_provides` | events `14bdb9e9…`, `1c629baf…` on `events/batch-033_framework.jsonl` |
| projection | `load_framework_graph.py` `EXIT=0`: 228 nodes, 389 edges, `tools_in_graph: 13`, `preconditions_in_graph: 19`, `requires_in_graph: 37` | `logs/requirements_projection.log` |
| live Cypher | the §0 counts; 0 tools with an unmarked cost; KG `Tool` nodes 262, untouched | `logs/requirements_cypher.log` |
| site payloads | `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest`, `EXIT=0`; `docs/data/ai_readiness_framework.json` and `index.json` moved, the CITATION and Zenodo files did not (same-day build date) | `logs/requirements_site.log` |
| generated views | `scan_tool_map.py --check`, `mcp/airkg_doc.py --check`: byte-identical; `build_framework_graph.py --dry-run`: `unchanged: true`, empty delta | `logs/requirements_protected.log` |
| `make gate-full` | **2652 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed**, 1499.66 s, `EXIT=0`; skips: `test_dispatch_config.py:333` (dispatched session), `test_scan_harness.py:283` (E5), `test_g1_preservation.py:337` | `logs/requirements_suite.log` |
| `seldon verify` | all checks passed (replay skipped as expensive, its default), `EXIT=0` | `logs/requirements_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` | `logs/requirements_protected.log` |
| projection round-trip | **9 passed, 0 skipped**, `EXIT=0` | `logs/requirements_roundtrip.log` |

**Open, for the next OODA:**
1. **The two tool READMEs have no `Document` node** (premise 7). Either emit their `manifest_add` events, or project Documents from the ledger. Until then, a `document` locator to them resolves through the manifest and says so.
2. **`publisher_grant` is the single largest lever on the cycle of record.** 51 of the 53 error cells, across the eight bodies with any (BLS, BTS and ORES are 14 each), are unlocked by one act of the publisher's. The other two are `http_5xx`, and a later cycle is what would unlock them. It is also A12's subject. A view that prints a body's standing should say this before it says anything about those cells.
3. **The benchmark sets are this project's to build**, and three of them (`product-question-benchmark`, `vintage-disambiguation-set`, `second-scan-cycle`) each unlock two or three indicators. That is the ranking `get_requirements()` with no argument prints, and it is the input a next build task would be authored from.
