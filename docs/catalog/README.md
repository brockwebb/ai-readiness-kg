# The scan catalog

**Value is a rated judgment under a stated rubric (v1), not a measurement. It enters no score, no rank and no bound** (DN-010 §2.1; DN-009 decision 3 still governs the score). The value columns live only in this directory, and `tests/test_scan_catalog.py` asserts statically that no scoring, ranking or bound code path reads them.

Every scan the framework could run, who can run it, how, what it would cost in two separate bands, and which one agency-side action would unlock the most. Task `cc_tasks/2026-10-02_scan_catalog.md` with its ADDENDUM-01, under DN-009 decisions 2, 6 and 8, and DN-010.

**Nothing in the tables is hand-authored.** `scripts/build_scan_catalog.py` builds every table from three sources:

1. **The framework record** (`framework/ai_readiness_framework.json`): its indicators, criteria, measurement specs, the requirements layer (`AssessmentTool` and `Precondition` nodes, `REQUIRES` edges) and the prescription layer (`Action` nodes, `REMEDIATES` edges, notional bands).
2. **The evidence map** (`docs/evidence/claims.yaml`): the Q1 class of what blocks each unmeasured indicator (CL-001 to CL-033), and the Q6 bound on what each Census action can move under equal weights (CL-055 to CL-077). These are read, never recomputed.
3. **The declared inputs** (`docs/catalog/catalog_inputs.yaml`): what the record does not carry. That covers the value ratings under rubric v1, the cheap-pass judgements, the enabler leads and their vendor quotes, tool licences and URLs, the methods found by search for indicators the record leaves without one, and the front-door vendor signatures. Every entry carries its source.

It also reads the stored observations of the cycle of record (`state/scan_2026-09-10.json`, the source of the re-judged `scan_2026-09-10_rj4`) for the front door.

```
/opt/anaconda3/bin/python3 scripts/build_scan_catalog.py           # write everything
/opt/anaconda3/bin/python3 scripts/build_scan_catalog.py --check   # regenerate in memory; exit 1 on any byte of drift
```

## Files

| file | what it is |
|---|---|
| `scan_catalog.csv`, `scan_catalog.md` | one row per (indicator, scan method); several `REQUIRES` routes give several rows, because routes are alternatives |
| `actions.csv`, `actions.md` | one row per `Action` in the record, plus one named row (`llms.txt`) the record has no Action for |
| `enablers.csv`, `enablers.md` | the agency-side enabler leads (decision 4), each with its status and the indicators it would serve |
| `front_door.csv` | per body: did a stored response header or challenge page name a CDN or bot-management vendor |
| `rollups/unlockers.csv` | each tool, enabler or requirement set, with the unmeasured indicators it would unlock |
| `rollups/set_cover.csv` | the greedy set cover over the currently unmeasured framework indicators, in order |
| `rollups/criterion_by_who.csv` | framework criterion by who-can-run, counted in rows |
| `rollups/staffing_by_cost.csv` | staffing band by cost band, counted in rows |
| `rollups/matrix_scans.csv`, `rollups/matrix_actions.csv` | the DN-010 effort-by-value grids, each cell with its row ids |
| `rollups/*.md` | the same rollups as Markdown, in `rollups/rollups.md` |

## Closed vocabularies

**`who_can_run`** (decision 2), defined by the act each one needs:

- `public_outside_in`: an unauthenticated client can run it within robots.txt and the harness manners (DD-060), with the identity and request rate the cycle of record used (`ai-readiness-kg-scanner/0.2`, 1 request per second per host). Buying a hosted tool does not change the class, because no one at the agency acts.
- `agency_enabled`: the agency installs, verifies or turns on something that then produces data, such as a verified webmaster-console site, an analytics tag, a CDN dashboard grant or a log export.
- `agency_records`: the agency must supply records only it holds.
- `needs_standard`: no standard or reference set exists to test against. The project or the field would have to author it first.

`blocked` is not a value. It is reserved for access denials on the cycle of record (DN-009 decision 5).

**Precedence when one route needs several things:** `agency_records` > `agency_enabled` > `needs_standard` > `public_outside_in`. Requirements on one route are needed together, so the hardest one decides.

**`method_kind`** (decision 3):

- `built_rule`: already in the harness, with the rule id.
- `tool_open_source`: an open-source program this project runs.
- `tool_commercial`: a vendor's hosted service or console.
- `roll_your_own`: a collector or reading this project would write, against a named protocol, API or method, with the locator of its specification.
- `none_known`: no method found. The `failed_searches` column lists the searches that failed.

A hosted free API (the Wayback CDX server, the CKAN action API) is `roll_your_own` over that API. The project writes the client; nothing is installed or bought.

**`row_source`**: `record` (the row is the record's own spec, route or recorded reason), `catalog_search` (the record names no method and the catalog's search found one; the source is on the row) or `proposed_link` (an enabler lead from decision 4 that would need a new requirement node).

**`q1_class`** is CL-001's partition of unmeasured indicators, read from `claims.yaml`: `open_tooling`, `funding`, `no_standard`, `agency_cooperation` or `not_blocked`. A measured indicator reads `measured`. The candidate `A12` reads `TBD`, because CL-001 partitions framework indicators only (DD-054).

**`cheap_pass`**: `yes`, `no` or `TBD`. It asks whether the pass condition can be met without serving a reader (decision 8, DN-010 §2.7).

**`evidence_grade`**: `established`, `plausible` or `unevidenced`. It grades whether a source shows that the artifact matters to a machine consumer, which is the claim behind the value rating.

- `established`: a source on file says a named consumer (a crawler operator, a search engine, the federal catalog's harvester) reads the artifact or obeys it.
- `plausible`: a standard or best-practice source prescribes it for machine use, but no source on file shows a consumer acting on it.
- `unevidenced`: no source on file supports the claim, or a measurement contradicts it.

**`value_basis`**: `evidence` (a cited source decides the rating), `rubric` (rated by rubric v1 with no outside evidence) or `TBD`.

## Value rubric v1

Written before any row was rated, as addendum decision 10 requires. DN-010 §2.3 defines value as how much a failing result keeps a reader or a machine from reaching, understanding or using the data (discovery, access, interpretation, fitness for use), and fixes the two ends. The middle three levels place the DN-010 stages in that order.

| level | a failing result... |
|---|---|
| **5** | leaves the data unreachable or unusable by a machine reader: refused, disallowed, served only as PDF, or invisible until JavaScript runs |
| **4** | leaves the data reachable only by a path a machine reader is unlikely to find or to use whole (no catalog or sitemap entry, no markup, no bulk file, no API, an identifier that breaks), or shows that a machine reader that does reach it misstates it |
| **3** | leaves the data reachable and parseable, while withholding what a machine reader needs to interpret it correctly: definitions, units, vintage, revision status, quality measures, licence |
| **2** | weakens trust, provenance or maintenance signals while reach and interpretation hold: lineage, changelogs, signed releases, issuing authority, the publisher's own evaluation process |
| **1** | is cosmetic: it withholds nothing a machine reader needs, or no consumer on file acts on the artifact |

**How it is applied.** A scan row carries the value of a failing result on its indicator. An action carries the value of the failure it remedies. When the failing outcome is milder than the indicator's worst case, the action gets its own rating and reason. One example: `no_robots_txt` leaves retrieval permitted under RFC 9309 §2.3.1.3. A harness-side action (`E5`) changes nothing the publisher serves, so its value is `TBD`. Measured evidence overrides the rubric's default, and the row says so: `llms.txt` is rated on the Ahrefs measurement, not on its proposal. `rated_by` names the rubric version and who applied it. `operator_override` is empty until the operator uses it.

**Prior art for the shape.** The two-axis arrangement of a value rating against a cost estimate is the cost-value approach to prioritizing requirements (Karlsson and Ryan, 1997, *IEEE Software* 14(5), pp. 67 to 74). That approach rates each candidate's value and cost and plots one against the other. It rated them by pairwise comparison (AHP), and this catalog uses ordinal bands instead, because DN-010 fixes five-point scales. The project already sorts issues on a two-by-two of importance against urgency (the Eisenhower grid in `~/GitHub/seldon/seldon/core/issue_utils.py::eisenhower_quadrant`). Here urgency is replaced by effort, and the scale is five by five. The composite-indicator literature is why value is kept out of the score. The OECD/JRC Handbook (2008, §1.6, p. 31) treats equal weighting as itself a weighting, one that "could also disguise the absence of a statistical or an empirical basis" (evidence map CL-083), so a value rating folded into the score would be an unstated weighting. A corpus search for a prioritization matrix found none. `prioriti` matched 9 admitted documents, none of them defining a value-effort grid. `Eisenhower`, `impact matrix` and `effort matrix` matched none. The Karlsson and Ryan citation was verified through a web search (one result page); the paper itself was not read.

## Effort: the band mapping

DN-010 §2.2 gives two 1-to-5 axes, `staffing_band` and `cost_band`. `effort_level` is the higher of the two when both are known; otherwise it is `TBD` and the row sits beside the grid. The record's notional bands are relative estimates by technique class (`cc_tasks/2026-09-17_notional_bands.md`; DN-005 ADDENDUM_02), so the mapping only preserves their order. It does not size them.

| record band | maps to | basis |
|---|---|---|
| effort `hours` | staffing 2 | `notional_record`. Level 1 is DN-010's "no staffing beyond running it", which an hours-long edit is not |
| effort `days` | staffing 3 | `notional_record` |
| effort `weeks` | staffing 4 | `notional_record` |
| effort `quarter` | staffing 5 | `notional_record` |
| cost `none` | cost 1 | `notional_record` |
| cost `staff_time` (action) or `tooling` (tool) | cost 2 | `notional_record`. The record ranks both above `none` and below `procurement` |
| cost `procurement` | `TBD` | the record's top band is open above, and no source sizes it |
| a built harness rule | staffing 1, cost 1 | DN-010 §2.2: "free and no staffing beyond running it is 1". The rule exists and the run is the harness's |

No other staffing value is filled. A tool's staffing has no band in the record, so it is `TBD`. Dollars and hours are out of scope (DN-010 §3).

## Cheap-pass exposure: prior art

DN-010 §2.7 asks whether a pass can be had without serving a reader. This is a named problem with an old literature. The corpus holds none of the classic statements: a search of the admitted documents for `Goodhart`, `Campbell`, `gaming` and `composite indicator` matched nothing. The OECD/JRC Handbook is not in the corpus either (see the RESULT's premises). These were read on the web:

- **Goodhart's law.** As Manheim and Garrabrant (2018, arXiv:1803.04585, n. 1) quote its original form, a statistical regularity "will tend to collapse once pressure is placed upon it for control purposes". Their taxonomy names four mechanisms: regressional, extremal, causal and adversarial. A cheap pass is the **adversarial** case: an agent who knows the metric satisfies the proxy, not the goal.
- **Campbell's law.** Campbell (1979, *Evaluation and Program Planning* 2(1), pp. 67 to 90): the more a quantitative indicator is used for decisions, "the more subject it will be to corruption pressures". The wording was checked on the Wikipedia article that cites the paper; the paper itself was not read.
- **In this corpus, applied to AI answers:** Kumar and Lakkaraju (2024, `kumar-2024-manipulating-llms-product-visibility`) show that a "strategic text sequence" added to a product page raises its chance of being an LLM's top recommendation. That is a cheap pass on any citation-based indicator (`C4`).

The column is therefore filled by **described case**: for each rule, a concrete artifact that passes without serving a reader, read from the rule module, the measurement spec or an Action's outcome. Where none was found, the value is `TBD`. `yes` does not mean a publisher would game the check. It means the check cannot tell a served reader from a satisfied proxy, which is the adversarial-Goodhart exposure the literature names.

## Agency-enabled instruments (decision 4)

Each candidate enabler is treated as a lead, never as a fact. The capability is quoted from the vendor's own documentation, in under 15 words, from the corpus where an admitted document holds it, and from the web otherwise (one page per claim). Each enabler also records its verification or install step and who must take it. The indicators it would serve are joined through the requirements layer where a node exists (`existing_node`). A link that would need a new node is `proposed_link`, and a link no source establishes is `unsupported`. The table is `enablers.csv`. It is summarised here by the generator:

<!-- BEGIN GENERATED: enablers -->

| enabler | status | who_can_run | existing_node | proposed_link | unsupported |
|---|---|---|---|---|---|
| enabler:akamai-datastream-2 | supported | agency_enabled |  | A11 |  |
| enabler:bing-webmaster-tools | supported | agency_enabled | C4 | A11 |  |
| enabler:cloudflare-ai-crawl-control | supported | agency_enabled | A11 | A12 |  |
| enabler:google-search-console | supported | agency_enabled |  | A5;A6;A11 | C4 |
| enabler:server-logs | supported | agency_records | A11 |  |  |
| enabler:sitemap-and-robots-submission | unsupported | agency_enabled |  |  |  |
| enabler:web-analytics | supported | agency_enabled |  | C4 |  |

<!-- END GENERATED: enablers -->

## What stood in front (decision 13)

From the stored observations of `scan_2026-09-10` only, with no new request. For each body, the table records whether a response header on the body's own hosts, or the body of a refusal page from them, **names** a CDN or bot-management vendor. The vendor tokens and the headers read are declared in `catalog_inputs.yaml: front_door`. A content-security-policy that lists a vendor's script origin names a supplier of scripts, not the front, so it is not read. `x-varnish` names cache software, not a vendor, so it is not counted. The observation ids are the locators.

No inference is made about why any finding was a denial. A body with no vendor-naming observation is `not_observed_in_record`, not "no CDN". The operator has stated that Census uses Cloudflare; the row for Census below is what the stored headers say, read independently of that statement.

<!-- BEGIN GENERATED: front_door -->

| body | tier | front_door_observed | named_by | n_observations_naming | observation_ids |
|---|---|---|---|---|---|
| BEA | A | azure | azure: header name `x-azure-ref` | 198 | obs_01adc97b1fb8f9c99d6f94fa;obs_01c90be1a139f5cfaf40e347;obs_02a39c9abdf8c5a5a572aeed;obs_031b5814bb7d9482a47567ba;obs_0327c880df8951bb2b3d51e6;(+193 more) |
| BJS | A | cloudflare | cloudflare: `server` value | 176 | obs_00a07551608ec0ea266ebc98;obs_017774acc379381d485d9f9f;obs_01eac353c305c394c4a9c062;obs_032a021bbe9a9e1284454e95;obs_032bdb927b16044e2ca91723;(+171 more) |
| BLS | A | akamai | akamai: HTTP 403 refusal page body, `server` value | 70 | obs_00085076091297770e4fb1ee;obs_038f2c58bbd39c8ec6aaa317;obs_06bee96e237c79ae57aa0112;obs_076c9e5194887d2bf66377ba;obs_094cdf8a1172ac321395de43;(+65 more) |
| BTS | A | akamai | akamai: `server` value | 68 | obs_0807b2cca14f15a942dcdf5a;obs_087fc330989367d515722747;obs_0aee5b32356af765d3725118;obs_0b64425dce842b994138e602;obs_0fd656b538b16c050334e101;(+63 more) |
| CENSUS | A | cloudflare | cloudflare: `server` value | 230 | obs_01ca9cb25c4ab33b069a9943;obs_029b69c5a9eb9017b6dc90e8;obs_02b8e2fa1be3cf5619aec89e;obs_0440a3a0808314704c0dfa8c;obs_074f94188abfb8602f747ffb;(+225 more) |
| DRSMSU | A | cloudflare | cloudflare: `server` value | 118 | obs_04310ceca2b21ab87eae30c2;obs_0572976aa03e728eea8e44c1;obs_0577b993ecaea1976944f61a;obs_078a3b4c0fb4e516f782bb1c;obs_15b3a144345e8baa56979595;(+113 more) |
| EIA | A | akamai | akamai: `server` value, header name `x-akamai-transformed` | 42 | obs_0a9a2d479283d781e4e266c1;obs_21028074d239d41023e5bc60;obs_242a7ab3528235903b68c963;obs_2d387fc17690b06c8dc7922a;obs_2ec389be0054e16b537aa20f;(+37 more) |
| ERS | A | not_observed_in_record |  | 0 |  |
| NAHMSAPHIS | A | akamai | akamai: header name `akamai-grn`, header name `x-akamai-transformed` | 118 | obs_0280717081213ba384b066b0;obs_03c0a8256c848170123af57c;obs_03c949952d8ee2bd51a8f476;obs_07478be774dcd0370512598c;obs_09d7938fc768efa7d0027bab;(+113 more) |
| NASS | A | azure | azure: header name `x-azure-ref` | 234 | obs_006f787210ce2ac1410c2753;obs_030044258cd9ba9db4c3bf6e;obs_06095cf5d60d45ac93b64b20;obs_076ccf7b3d582d7c2f5cf6f0;obs_0787d4ec887228502bc04986;(+229 more) |
| NCES | A | not_observed_in_record |  | 0 |  |
| NCHS | A | azure | azure: header name `x-azure-ref` | 208 | obs_01007c7acced719e3871ec06;obs_017b38bfb33a0cbc2b237b0a;obs_01bb208e95971255599b0745;obs_0232502670c7411a46e14a92;obs_02dab82de1d97f243d18f123;(+203 more) |
| NCSES | A | not_observed_in_record |  | 0 |  |
| ORES | A | not_observed_in_record |  | 0 |  |
| SAMHSACBHS | A | not_observed_in_record |  | 0 |  |
| SOI | A | akamai | akamai: header name `akamai-grn` | 168 | obs_00fb14c049c8db7cdb49aa56;obs_025f4ffae55f5cfa7d681464;obs_02c2a6b16276e39f9652ff48;obs_053d7ce926d06f2b8a649634;obs_0628bc3f2cfd4debc2e0e3c1;(+163 more) |
| data.gov | C | cloudfront | cloudfront: `via` value, `x-cache` value | 24 | obs_29c4203a508eff7a3be7fdcd;obs_2ba9a0b5fc6153bc7a9851af;obs_2c5033957bfb2cffd33c0523;obs_39c43c1ee2d2deba60a3c1e5;obs_3bc5740faa0e55d8118048d6;(+19 more) |
| GSA | C | cloudfront | cloudfront: `via` value, `x-cache` value | 24 | obs_16d61b6ba78f404faa04fbb4;obs_1ba08d494d49a91e557a4e53;obs_1ca8357215e79cbc9ea83522;obs_1d199499bc81b99d52b4fdaa;obs_253f1993f8c7f0febb8f48a0;(+19 more) |
| NIST | C | cloudflare | cloudflare: `server` value | 24 | obs_07cc908150871317d3320d87;obs_08c0dff5ce2db07aceb08339;obs_0c8416b00ba24ebf9e10b17e;obs_16b3f17d7bbf208f432d543a;obs_21f5dab225a1b2b3975432da;(+19 more) |

<!-- END GENERATED: front_door -->

## What the tables say

<!-- BEGIN GENERATED: summary -->

Of the 26 framework indicators the record does not mark measured, the easiest route on any row needs:

| easiest route | n | indicators |
|---|---|---|
| `public_outside_in` | 8 | A7, B6, C5, F2, F3, F6, G3, G5 |
| `needs_standard` | 9 | C1, C2, C3, C4, E6, E8, E9, G2, G6 |
| `agency_enabled` | 0 |  |
| `agency_records` | 7 | E1, E2, E3, E4, E7, F1, F5 |
| `no_route_to_obtain` | 2 | D1, E5 |

`no_route_to_obtain` means no row offers anything to obtain: the indicator has a built rule the record does not mark measured, and its unmeasured half has no known method (`none_known`) or nothing stands in its way but the definition of measured. It does not mean the indicator needs nothing.

No agency-side enabler unlocks more than 1 unmeasured framework indicator(s): `enabler:bing-webmaster-tools` reaches C4; `enabler:web-analytics` reaches C4. Counting indicators already measured, the widest reaches 3: `enabler:google-search-console` (A5;A6;A11). Those extra links deepen a measured indicator (its unmeasured half, or its coverage); they do not add one.

The actions quick-win cell (effort at most 2, value at least 4) holds 11 action(s), 10 of them `established` and 10 of them with `cheap_pass: yes`: `act:a11-permit-the-ai-crawlers-you-intend-to-serve-on-the-product-path`, `act:a11-resolve-the-meta-robots-directive-that-contradicts-robots-txt`, `act:a12-publish-a-robots-txt-group-an-identified-client-matches`, `act:a13-link-what-you-publish-from-the-product-page`, `act:a4-allow-the-data-paths-for-named-ai-crawlers`, `act:a5-list-the-product-url-in-the-sitemap`, `act:a6-embed-json-ld-on-the-product-page`, `act:a6-make-the-dataset-markup-conform-to-the-profile`, `act:a6-type-the-product-page-as-a-dataset`, `act:d4-add-the-product-to-the-public-data-inventory`, `act:d4-make-the-catalog-conform-to-dcat-us`. The scans quick-win cell holds 11 row(s), all of them `built_rule`: a built rule costs nothing more to run, so the scan grid says which built rules matter most, not what to build.

<!-- END GENERATED: summary -->

## Indicator codes

The framework record's own wording for each code, with its criterion.

<!-- BEGIN GENERATED: codes -->

Criteria, as the record names them: `A` ACCESSIBLE; `B` UNDERSTANDABLE; `C` ACCURATE; `D` OPEN; `E` TEVV loop; `F` release engineering; `G` FSS-derived constructs.

| code | criterion | status | indicator |
|---|---|---|---|
| A1 | A | measured | Product available as structured data (CSV/JSON/parquet), not PDF-only |
| A2 | A | measured | Documented public API; auth model; rate limits stated |
| A3 | A | measured | Full-product bulk download exists and is linked from product page |
| A4 | A | measured | robots.txt + AI-crawler policy permit retrieval; no soft-blocks on data paths |
| A5 | A | measured | llms.txt (or equivalent) present; sitemap covers data products |
| A6 | A | measured | schema.org/Dataset (or DCAT/Croissant) markup valid on product pages |
| A7 | A | specified | Persistent URLs/DOIs for products and vintages |
| A8 | A | measured | Release date machine-readable; latest-vintage pointer resolvable |
| A9 | A | measured | Product exposes a machine-first entry point (documented API plus MCP/A2A-class endpoint or equivalent agent protocol); human pages derivable from it |
| A10 | A | measured | Interactive data tools expose stable, directly-requestable deep links; meaningful states are not fragment-only or session-dependent; invalid routes return true 404/410, not HTTP-200 shell (soft-404); page-specific content present in raw HTML before JS execution |
| A11 | A | measured | A4 upgraded from declared-policy check to three-layer comparison: declared (robots.txt/meta directives) vs enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs). A mismatch between layers is itself the finding, not an error state |
| A12 | A | specified | An identified, robots-compliant machine client that robots.txt permits is served (not refused by a WAF or bot manager) (candidate, DD-054) |
| A13 | A | specified | A machine client starting from the product page reaches the body's API, its terms, its changelog and its inventory without being told where they are (candidate, DD-054) |
| B1 | B | measured | Comprehensive variable-level metadata (labels, definitions, units, universes) |
| B2 | B | measured | Concept/term definitions published, versioned, linked from variables |
| B3 | B | measured | Methodology docs in structured text (not PDF-only); summarizable by retrieval |
| B4 | B | measured | Data-quality attributes (error measures, suppression rules, revisions policy) published as metadata, not prose |
| B5 | B | measured | Same concept ⇒ same identifier across products/vintages |
| B6 | B | specified | Plain-language product summary present and current (the retrieval target) |
| C1 | C | specified | Benchmark question set per product; answer accuracy of a retrieval-paired model vs published values |
| C2 | C | specified | Entailment-judged: do model statements about the product entail from product text? (probe protocol, re-aimed) |
| C3 | C | specified | Version/vintage disambiguation: does retrieval return the vintage asked for? |
| C4 | C | specified | Generative engines citing the product cite the authoritative page (not aggregators) |
| C5 | C | specified | Product scored against published AI-data-readiness metrics |
| D1 | D | harness_built | Explicit machine-readable license/terms on product and API |
| D2 | D | measured | Terms address model training/retrieval use explicitly |
| D3 | D | measured | Source lineage published (collection → processing → product) |
| D4 | D | measured | Statutory products enumerable from a public inventory (data.gov/agency inventory current) |
| E1 | E | specified | Product spec conformance (AUTO/DOC set) reported separately from fit-for-use evals (EVAL set); a product cannot pass validation while failing verification |
| E2 | E | specified | Published pass/fail thresholds per eval, pre-registered before results; threshold changes are versioned events |
| E3 | E | specified | Eval sets and rubrics carry versions; results never pooled across versions |
| E4 | E | specified | Public eval sets have a held-out rotation; publication schedule assumes training-set leakage within one model generation |
| E5 | E | harness_built | Seeded known-bad items (canaries/decoys) in every continuous-eval cycle; a cycle with zero fired controls is INVALID, not passing |
| E6 | E | specified | Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model; each stage instrumented |
| E7 | E | specified | Documented path from failed eval back into the data product (metadata fix, vintage pointer, dictionary entry) with re-test; mean-time-to-closure tracked |
| E8 | E | specified | Versioned golden question/answer sets re-run on schedule against the product surface; baseline deltas alarmed; state fidelity across product versions measured, not assumed |
| E9 | E | specified | Standing adversarial bank: vintage traps, confusable series, unit traps, DP-noise misreads, suppression probes; plus surface red team — misparse and injection resistance of pages/markup/llms.txt. Reported as break modes, not just pass rates |
| F1 | F | specified | New releases pass a published expectation suite (schema validity, row/total sanity, identifier persistence) before going live |
| F2 | F | specified | API/schema changes are versioned; breaking changes announced with deprecation windows; compatibility checked mechanically |
| F3 | F | specified | Time-series identifiers, geography codes, and endpoints survive a new vintage or a crosswalk is published; tested per release |
| F4 | F | measured | Machine-readable changelog per release (what changed, why, revision class); webhooks/push for high-frequency products |
| F5 | F | specified | Canary/staging surface for major product changes; AI-consumer regression run before promotion |
| F6 | F | specified | Signed releases / provenance attestations so downstream copies are traceable to the authoritative artifact (SLSA-class, adapted) |
| G1-D | G | measured | **G1-D (declared)** — error measures (MOEs, CVs, DP noise parameters) present as structured fields beside the estimates on the product surface, not as footnotes (`assessment/harness/probes/g1_declared.py`); unchanged. |
| G1-O | G | measured | **G1-O (observed)** — the family preservation rate (the L3+ share of scored qualifier families, D9) when the pinned consumer restates that same captured surface at indirect compression `none`, reported per surface with the `unparseable` share and the `short` / `tight` rates beside it, every record stamped with consumer, prompt epoch, `parser_version` and `scorer_version` (`g1_preservation.py`). The two legs are reported as a vector and are never composited (protocol §3). **No product-level PASS/PARTIAL/FAIL in v0.2.x:** the rate and its Wilson interval are the score until the January calibration run sets a boundary. Compression is a reported condition, not a scored one, until intended use says which condition the consumer of the assessment cares about |
| G2 | G | specified | Revision status machine-readable per value (preliminary/revised/final/benchmark), with scheduled-revision dates; EVAL: vintage disambiguation (ties C3) |
| G3 | G | specified | Stable series IDs; machine-readable crosswalks when classifications or geographies change (industry codes, boundary revisions) |
| G4 | G | measured | The issuing authority of a data product is carried as machine-readable metadata on the product's catalog record: in `publisher`, the field DCAT-US 3.0 defines for it (Recommended), or in the agency codes DCAT-US 1.1 requires of federal datasets (`bureauCode`, `programCode`), which DCAT-US 3.0 does not define and does not reject |
| G5 | G | specified | Suppression and disclosure-avoidance documented machine-readably with unique identifiers (strengthens the guide's own bullet from prose to spec) |
| G6 | G | specified | Collection instrument/protocol carried as a versioned epoch on the series; changes annotated machine-readably with reason and inter-epoch crosswalk (SDMX break-in-series class metadata). The consumer-side test: an AI system asked to compare values across a break must surface the break |

<!-- END GENERATED: codes -->

## Counts

<!-- BEGIN GENERATED: counts -->

- Scan rows: 72, over 50 indicators (26 framework indicators are not measured).
- By who can run it: `public_outside_in` 42, `agency_enabled` 9, `agency_records` 8, `needs_standard` 13.
- By method kind: `built_rule` 27, `tool_open_source` 8, `tool_commercial` 10, `roll_your_own` 23, `none_known` 4.
- By row source: `record` 63, `catalog_search` 2, `proposed_link` 7.
- Action rows: 65 (64 from the record, 1 named).
- Greedy set cover: 22 steps cover 24 of 26 unmeasured framework indicators; for 2, no row offers anything to obtain.

<!-- END GENERATED: counts -->
