# RESULT: the prescription layer — 45 sourced actions, each bound to the rule outcome that verifies it

**Task:** `cc_tasks/2026-09-17_prescription_layer.md` (ResearchTask `7bc3e700`). I globbed `2026-09-17_prescription_layer_ADDENDUM*.md` before starting and again before §4. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher (`dispatch_launched` at 2026-09-17T20:05:48Z) from HEAD `e428e79`. The predecessor, `2026-09-17_measurement_tiers.md`, already had its RESULT on `0798ba6`, so the SEQUENCING line held.
**Framework layer served:** DN-005 §2.3 (prescription: action mapped to indicator, with effort, cost and value) and §4 item 3.
**Spend:** zero model calls. **Network:** none beyond `git push`. Every technique source is a document already in `corpus/`; nothing was fetched.
**Gate:** green, with every command run to its `EXIT=` line before this file was written.
- `make gate-full` equivalent — **the full tier**, `/opt/anaconda3/bin/python3 -m pytest tests/ assessment/ -q -rs`: **2341 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed**, `EXIT=0`, wall-clock 1388.93 s (`real 23m11.323s`). Expected skips: 3, and the three are the expected three.
- `seldon verify`: **All checks passed**, `EXIT=0`.
- `scripts/check_protected_prescriptions.sh`: **PROTECTED PATHS OK**, `EXIT=0`.
The log paths are in §6.

**In one paragraph.** The framework record now holds a prescription layer: **45 `Action` nodes and 45 `REMEDIATES` edges**, one per failing outcome of the 17 `harness_leg` indicators' current rules, projected into Neo4j under a sixth assessment label. Every action carries at least one technique source quoted verbatim from a document on disk (**110 citations over 16 distinct documents**), and a `verifies_by` that resolves to `rules.CURRENT` — the WCAG/CIS/Scorecard invariant, enforced from both ends by `tests/test_prescriptions.py`. Value is computed, never authored: `bodies_failing_now` is recomputed in the gate from the published matrices of the cycle of record and compared cell for cell. **Every effort and cost band is empty and every band source reads `estimate:pending`: 90 slots, tabled for the operator in §2.** The search that produced that number is in §0 — no document on disk assigns a band to any of these techniques, and this task did not invent one.

---

## 0. What the prior art already had, and what it did not

**The four shapes DN-005 §2.3 and the task file name, as they exist on disk.** The claim "no prior art found" requires the search that failed, so here is the search.

| shape | on disk? | what I used |
|---|---|---|
| **Lighthouse** | **yes** — `corpus/kernel/lighthouse-docs-overview.md` (doc_id `lighthouse-docs-overview`) | the invariant, in the document's own words: *"Each audit has a reference that explains why the audit is important, as well as how to fix it."* Cited as a technique source on `act:a10-serve-the-product-content-before-javascript-runs`. |
| **WCAG** (success criterion → sufficient techniques → common failures) | **no** | `grep -rli "wcag" corpus/kernel/ corpus/crosswalk/ corpus/bulk_md/` returns six schema.org pages and three AI-readiness reports, none of which is WCAG; no manifest entry is WCAG. Cited as DN-005 §2.3 names it, not as a document. |
| **CIS Benchmarks** | **no** | same grep for `"cis benchmark"`: no hit anywhere in the corpus, no manifest entry. |
| **OpenSSF Scorecard** | **no** | same grep for `"openssf"`/`"scorecard"`: the only hits are the substring `scorecard` inside three unrelated readiness reports. |
| **NIST SP 800-53** | **no** | same grep for `"800-53"`: no hit. `nist-ai-risk-management-framework-ai-rmf`, `nist-ai-rmf-playbook` and `nist-ai-100-3` are in the manifest; 800-53 is not. |

What the four share is the thing this layer implements and the tests enforce: **an action is bound to the check that would detect its absence, and the same check verifies its completion.** Here that is `Action.verifies_by` → a rule id in `rules.CURRENT`, and a `REMEDIATES` edge whose `outcome` names the rule branch the action closes.

**W3C DWBP is the shape's best on-disk instance, and the task file did not name it.** `corpus/kernel/w3c-dwbp-2017.md` gives every one of its 35 Best Practices an *Intended Outcome*, a *Possible Approach to Implementation* and a *How to Test* — which is WCAG's decomposition under different headings, for exactly this domain. 16 of its 35 BPs supply 40 of the 110 technique citations here — BP 1, 4, 5, 6, 7, 8, 9, 11, 12, 14, 17, 19, 22, 23, 25 and 27. Finding it is the one place this task's prior-art search paid better than the task file assumed.

**Nothing in the record or the skeleton already held an action, remediation or "how to fix" field.** I checked three ways: (a) every property key on every node of `framework/ai_readiness_framework.json` at HEAD — 45 distinct keys, none of them an action, remediation or fix; (b) `git show HEAD:framework/ai_readiness_framework.json | grep -c remediat` → 0 (the current record matches, of course, because `REMEDIATES` is what this task added); (c) the skeleton (`docs/crosswalk/usafacts_operationalization_skeleton.md`) has no remediation column. Two near-misses are worth naming rather than passing over:

- **The record already names the loop, in the deck.** `docs/crosswalk/deck_content_2026-09-01.md` §"Remediation loop": *"failed indicators on a product become corrective actions with re-test (the TEVV closure), and recurring failures across products become the improvement agenda fed back to framework authors."* That is this layer's purpose, written a fortnight before the layer. It was prose in a deck; it is now a query.
- **E7 is the indicator for having this loop, on the agency's side.** Skeleton row E7, "Corrective-action closure": *"Documented path from failed eval back into the data product … with re-test; mean-time-to-closure tracked"*. E7 measures whether a publisher runs a remediation loop; this layer is the loop's content for our own 17 checks. They are not the same object and neither supersedes the other.

**The effort/cost search, and why every band is pending.** DN-005 §2.3 says the cost and value part "is this project's contribution and must be sourced where a source exists and marked as estimate where none does". I searched for a source that states a level of effort or a cost for any of these techniques:

- every markdown source in `SOURCES` for `effort|cost|person-day|staff time|hours|expensive|no cost|licence fee|budget`;
- `corpus/bulk_md/`, `corpus/kernel/`, `corpus/crosswalk/` for `level of effort|person-day|staff hours|burden hours|implementation cost`.

Four documents answered and none of them assigns a band:

- **W3C DWBP BP 14** is the closest sentence in the corpus: *"Data publishers must balance the effort required to make the data available in many formats against the cost of doing so"*. It says the two exist. It does not say how large either is.
- **DWBP BP 23**: *"Creating an API is a little more involved than posting data for download."* An ordering between two of these actions, not a band for either.
- **`corpus/kernel/digital-gov-website-standards.md`**: *"We publish finalized standards on this site and set a pending time period based on the relative level of effort to comply."* The mechanism exists — but the three pending standards are the federal banner, the HTML page title and the meta page description, none of which is one of these 17 legs, and no period is stated.
- **`corpus/crosswalk/slsa-specification-v1-0.md`**: higher SLSA levels *"come at higher implementation costs"*. About F6, which is not a harness leg.

So: **0 sourced bands, 90 pending.** The band is left empty and the source says `estimate:pending` in words, because an empty cell reads as "no effort" and a guessed band reads as a measurement. §2 tables the 90 slots for the operator, who is the value input for them (`~/.claude/CLAUDE.md` §2 item 3).

---

## 1. The action table

45 rows: one action per failing outcome of the 17 `harness_leg` indicators' current rules. Generated from the record as written, so this is the record's own content. `technique sources` lists the doc_ids of the locators on the node; the full locator and the verbatim quote are on `Action.technique_source` and printed by `scripts/prescriptions.py`.

| indicator | leg | outcome | action id | technique sources (doc_id) | effort | cost | bodies failing now |
|---|---|---|---|---|---|---|---|
| A1 | `A1` | `no_structured_link` | `act:a1-serve-the-data-files-with-their-own-media-type` | w3c-dwbp-2017, schema-org-datadownload, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 12 |
| A1 | `A1` | `only_pdf` | `act:a1-publish-a-structured-distribution` | w3c-dwbp-2017, w3c-dwbp-2017, schema-org-dataset | `estimate:pending` | `estimate:pending` | 12 |
| A10 | `A10` | `client_rendered_shell` | `act:a10-serve-the-product-content-before-javascript-runs` | llmstxt-proposal, llmstxt-proposal, lighthouse-docs-overview | `estimate:pending` | `estimate:pending` | 1 |
| A10 | `A10` | `deep_link_error_status` | `act:a10-make-the-product-deep-link-resolve` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 1 |
| A10 | `A10` | `soft_404` | `act:a10-return-a-real-status-for-routes-that-do-not-exist` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 1 |
| A11 | `A11-declared` | `meta_robots_contradicts_robots_txt` | `act:a11-resolve-the-meta-robots-directive-that-contradicts-robots-txt` | google-robots-txt-intro, google-robots-txt-intro | `estimate:pending` | `estimate:pending` | 2 |
| A11 | `A11-declared` | `nothing_declared` | `act:a11-declare-a-crawler-policy-for-the-product-path` | google-robots-txt-intro, rfc-9309-robots-exclusion-protocol, openai-crawlers-bots | `estimate:pending` | `estimate:pending` | 2 |
| A11 | `A11-declared` | `robots_disallows_ai_crawlers` | `act:a11-permit-the-ai-crawlers-you-intend-to-serve-on-the-product-path` | rfc-9309-robots-exclusion-protocol, openai-crawlers-bots | `estimate:pending` | `estimate:pending` | 2 |
| A12 | `A12` | `declared_permits_enforced_refuses` | `act:a12-align-the-edge-with-the-declaration` | openai-crawlers-bots, rfc-9309-robots-exclusion-protocol, google-robots-txt-intro | `estimate:pending` | `estimate:pending` | 4 |
| A12 | `A12` | `nothing_declared_for_this_client` | `act:a12-publish-a-robots-txt-group-an-identified-client-matches` | rfc-9309-robots-exclusion-protocol, rfc-9309-robots-exclusion-protocol | `estimate:pending` | `estimate:pending` | 4 |
| A12 | `A12` | `robots_itself_refused` | `act:a12-serve-robots-txt-to-every-client` | rfc-9309-robots-exclusion-protocol, google-robots-txt-intro | `estimate:pending` | `estimate:pending` | 4 |
| A2 | `A2` | `no_api_description` | `act:a2-expose-an-api-and-publish-its-description` | w3c-dwbp-2017, w3c-dwbp-2017, openapi-specification-core, schema-org-webapi | `estimate:pending` | `estimate:pending` | 13 |
| A2 | `A2` | `served_but_not_an_api_description` | `act:a2-serve-a-parseable-api-description-at-the-documented-path` | openapi-specification-core, openapi-specification-core, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 13 |
| A3 | `A3` | `below_bulk_floor` | `act:a3-publish-the-complete-file-not-a-sample` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 7 |
| A3 | `A3` | `filtered_query_not_whole_product` | `act:a3-add-a-whole-product-download-beside-the-query-builder` | w3c-dwbp-2017, schema-org-dataset | `estimate:pending` | `estimate:pending` | 7 |
| A3 | `A3` | `no_whole_product_download` | `act:a3-link-a-bulk-download-from-the-product-page` | w3c-dwbp-2017, dcat-us-1-1-schema | `estimate:pending` | `estimate:pending` | 7 |
| A4 | `A4` | `no_robots_txt` | `act:a4-serve-a-robots-txt-that-names-ai-crawlers` | rfc-9309-robots-exclusion-protocol, google-robots-txt-intro, openai-crawlers-bots | `estimate:pending` | `estimate:pending` | 1 |
| A4 | `A4` | `robots_disallows_ai_crawlers` | `act:a4-allow-the-data-paths-for-named-ai-crawlers` | rfc-9309-robots-exclusion-protocol, openai-crawlers-bots, google-robots-txt-intro | `estimate:pending` | `estimate:pending` | 1 |
| A5 | `A5` | `discovery_file_omits_product` | `act:a5-list-the-product-url-in-the-sitemap` | sitemaps-protocol, sitemaps-protocol, llmstxt-proposal | `estimate:pending` | `estimate:pending` | 10 |
| A5 | `A5` | `no_discovery_file` | `act:a5-publish-a-sitemap-and-point-robots-txt-at-it` | sitemaps-protocol, sitemaps-protocol, llmstxt-proposal | `estimate:pending` | `estimate:pending` | 10 |
| A6 | `A6` | `markup_without_dataset_type` | `act:a6-type-the-product-page-as-a-dataset` | schema-org-dataset, w3c-dwbp-2017, w3c-json-ld-1-1-core | `estimate:pending` | `estimate:pending` | 11 |
| A6 | `A6` | `no_structured_markup` | `act:a6-embed-json-ld-on-the-product-page` | w3c-dwbp-2017, w3c-json-ld-1-1-core, schema-org-dataset | `estimate:pending` | `estimate:pending` | 11 |
| A6 | `A6` | `shapes_violation` | `act:a6-make-the-dataset-markup-conform-to-the-profile` | dcat-us-3-dataset-schema, dcat-us-1-1-schema, schema-org-dataset | `estimate:pending` | `estimate:pending` | 11 |
| A8 | `A8` | `last_modified_header_only` | `act:a8-declare-the-product-vintage-in-the-markup` | schema-org-dataset, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 11 |
| A8 | `A8` | `latest_vintage_pointer_unresolved` | `act:a8-make-the-latest-pointer-resolve` | w3c-dwbp-2017, w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 11 |
| A8 | `A8` | `no_declared_date` | `act:a8-publish-a-release-date-for-the-product` | w3c-dwbp-2017, dcat-us-3-dataset-schema, schema-org-dataset | `estimate:pending` | `estimate:pending` | 11 |
| A8 | `A8` | `no_latest_vintage_pointer` | `act:a8-serve-a-stable-latest-url-on-the-product-host` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 11 |
| A9 | `A9` | `machine_path_answers_html` | `act:a9-return-a-machine-format-at-the-machine-path` | w3c-dwbp-2017, llmstxt-proposal, llmstxt-proposal | `estimate:pending` | `estimate:pending` | 13 |
| A9 | `A9` | `no_machine_first_path` | `act:a9-publish-a-machine-first-entry-point` | llmstxt-proposal, llmstxt-proposal, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 13 |
| B3 | `B3` | `methodology_pdf_only` | `act:b3-publish-the-methodology-in-structured-text` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 10 |
| B3 | `B3` | `methodology_requires_js` | `act:b3-serve-the-methodology-without-javascript` | llmstxt-proposal, llmstxt-proposal | `estimate:pending` | `estimate:pending` | 10 |
| B3 | `B3` | `no_methodology_link` | `act:b3-link-the-methodology-from-the-product-page` | w3c-dwbp-2017, dcat-us-3-dataset-schema | `estimate:pending` | `estimate:pending` | 10 |
| B3 | `B3` | `no_structured_text_methodology` | `act:b3-publish-a-methodology-document-reachable-from-the-product` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 10 |
| D1 | `D1` | `licence_is_free_text` | `act:d1-state-the-licence-as-an-identifier` | schema-org-dataset, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 13 |
| D1 | `D1` | `no_licence` | `act:d1-publish-a-machine-readable-licence` | w3c-dwbp-2017, schema-org-dataset | `estimate:pending` | `estimate:pending` | 13 |
| D4 | `D4` | `catalog_schema_violation` | `act:d4-make-the-catalog-conform-to-dcat-us` | dcat-us-1-1-schema, dcat-us-1-1-schema, dcat-us-3-dataset-schema | `estimate:pending` | `estimate:pending` | 11 |
| D4 | `D4` | `no_catalog` | `act:d4-publish-a-data-json-inventory` | dcat-us-1-1-schema, dcat-us-1-1-schema | `estimate:pending` | `estimate:pending` | 11 |
| D4 | `D4` | `product_absent_from_catalog` | `act:d4-add-the-product-to-the-public-data-inventory` | dcat-us-1-1-schema, schema-org-datacatalog | `estimate:pending` | `estimate:pending` | 11 |
| E5 | `E5` | `control_verdict_not_as_expected` | `act:e5-investigate-the-control-verdict-that-moved` | internal:scan-params, internal:scan-params | `estimate:pending` | `estimate:pending` | 0 |
| E5 | `E5` | `controls_ran_after_surfaces` | `act:e5-order-the-controls-before-the-surfaces` | internal:scan-params, internal:scan-params | `estimate:pending` | `estimate:pending` | 0 |
| E5 | `E5` | `zero_controls_fired` | `act:e5-fire-every-declared-control-before-the-first-host` | internal:scan-params, internal:scan-params | `estimate:pending` | `estimate:pending` | 0 |
| F4 | `F4` | `changelog_entries_lack_revision_class` | `act:f4-carry-a-revision-class-on-every-changelog-entry` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 13 |
| F4 | `F4` | `changelog_not_machine_readable` | `act:f4-serve-the-changelog-in-a-machine-readable-format` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 13 |
| F4 | `F4` | `no_changelog` | `act:f4-publish-a-version-history-endpoint` | w3c-dwbp-2017, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 13 |
| G1-D | `G1-D` | `no_error_measure_field` | `act:g1d-publish-the-error-measure-as-a-structured-field` | schema-org-dataset, w3c-dwbp-2017 | `estimate:pending` | `estimate:pending` | 0 |

**How the outcomes were enumerated, and why they cannot drift.** A rule module has no named outcomes — its `fail` branches carry free-text reason strings. So each outcome is anchored by a **verbatim fragment of its own branch's reason string**, stored on the `REMEDIATES` edge as `reason_fragment` and checked as a substring of the current rule module's source before anything is written (`tag_prescriptions.validate` step 2, `tests/test_prescriptions.py::test_every_outcome_names_a_branch_that_is_still_in_its_rule`). A rule version that rewords a branch fails the gate rather than leaving a prescription bound to a sentence nothing produces. The fragments are short and sit inside one source line, because a rule's reason strings are f-strings wrapped across lines and a fragment spanning the wrap is verbatim nowhere.

**Coverage, by construction.** 45 (leg, outcome) pairs from the 17 modules; 45 actions; the test asserts set equality both ways, so an uncovered outcome and an action on a non-outcome are both failures. `A11-declared` maps to indicator `A11`; every other leg is its own indicator code, including `G1-D`, which is an indicator (DD-036) and not a qualifier.

---

## 2. Counts, and the pending slots for the operator

| | |
|---|---|
| `Action` nodes | **45** |
| `REMEDIATES` edges | **45** (one per action; `(from, type, to)` unique) |
| harness legs covered | **17 of 17** |
| failing rule outcomes covered | **45 of 45** |
| technique-source citations | **110** |
| distinct source documents cited | **16** (15 corpus documents + `assessment/harness/scan/params.yaml` for E5) |
| **bands with a source** | **0** |
| **bands `estimate:pending`** | **90** (45 effort + 45 cost) |
| actions not addressed to a publisher | **3** (all E5) |
| `counts.actions` (framework, DD-054) | **42** |
| `counts.actions_on_candidate_indicators` (A12) | **3** |

Actions per leg: A1 2, A2 2, A3 3, A4 2, A5 2, A6 3, A8 4, A9 2, A10 3, A11-declared 3, A12 3, B3 4, D1 2, D4 3, E5 3, F4 3, G1-D 1.

### The 90 `estimate:pending` slots — the operator's table

Every row has both bands empty. `effort_band` ∈ {hours, days, weeks, quarter}; `cost_band` ∈ {none, tooling, staff_time, procurement}. Ordered by `bodies_failing_now` descending, which is the order in which filling them changes what the framework can say. Re-derivable at any time with `scripts/prescriptions.py --pending`.

| action | leg | bodies failing now | effort_band | cost_band |
|---|---|---|---|---|
| `act:a2-expose-an-api-and-publish-its-description` | `A2` | 13 | | |
| `act:a2-serve-a-parseable-api-description-at-the-documented-path` | `A2` | 13 | | |
| `act:a9-publish-a-machine-first-entry-point` | `A9` | 13 | | |
| `act:a9-return-a-machine-format-at-the-machine-path` | `A9` | 13 | | |
| `act:d1-publish-a-machine-readable-licence` | `D1` | 13 | | |
| `act:d1-state-the-licence-as-an-identifier` | `D1` | 13 | | |
| `act:f4-carry-a-revision-class-on-every-changelog-entry` | `F4` | 13 | | |
| `act:f4-publish-a-version-history-endpoint` | `F4` | 13 | | |
| `act:f4-serve-the-changelog-in-a-machine-readable-format` | `F4` | 13 | | |
| `act:a1-publish-a-structured-distribution` | `A1` | 12 | | |
| `act:a1-serve-the-data-files-with-their-own-media-type` | `A1` | 12 | | |
| `act:a6-embed-json-ld-on-the-product-page` | `A6` | 11 | | |
| `act:a6-make-the-dataset-markup-conform-to-the-profile` | `A6` | 11 | | |
| `act:a6-type-the-product-page-as-a-dataset` | `A6` | 11 | | |
| `act:a8-declare-the-product-vintage-in-the-markup` | `A8` | 11 | | |
| `act:a8-make-the-latest-pointer-resolve` | `A8` | 11 | | |
| `act:a8-publish-a-release-date-for-the-product` | `A8` | 11 | | |
| `act:a8-serve-a-stable-latest-url-on-the-product-host` | `A8` | 11 | | |
| `act:d4-add-the-product-to-the-public-data-inventory` | `D4` | 11 | | |
| `act:d4-make-the-catalog-conform-to-dcat-us` | `D4` | 11 | | |
| `act:d4-publish-a-data-json-inventory` | `D4` | 11 | | |
| `act:a5-list-the-product-url-in-the-sitemap` | `A5` | 10 | | |
| `act:a5-publish-a-sitemap-and-point-robots-txt-at-it` | `A5` | 10 | | |
| `act:b3-link-the-methodology-from-the-product-page` | `B3` | 10 | | |
| `act:b3-publish-a-methodology-document-reachable-from-the-product` | `B3` | 10 | | |
| `act:b3-publish-the-methodology-in-structured-text` | `B3` | 10 | | |
| `act:b3-serve-the-methodology-without-javascript` | `B3` | 10 | | |
| `act:a3-add-a-whole-product-download-beside-the-query-builder` | `A3` | 7 | | |
| `act:a3-link-a-bulk-download-from-the-product-page` | `A3` | 7 | | |
| `act:a3-publish-the-complete-file-not-a-sample` | `A3` | 7 | | |
| `act:a12-align-the-edge-with-the-declaration` | `A12` | 4 | | |
| `act:a12-publish-a-robots-txt-group-an-identified-client-matches` | `A12` | 4 | | |
| `act:a12-serve-robots-txt-to-every-client` | `A12` | 4 | | |
| `act:a11-declare-a-crawler-policy-for-the-product-path` | `A11-declared` | 2 | | |
| `act:a11-permit-the-ai-crawlers-you-intend-to-serve-on-the-product-path` | `A11-declared` | 2 | | |
| `act:a11-resolve-the-meta-robots-directive-that-contradicts-robots-txt` | `A11-declared` | 2 | | |
| `act:a10-make-the-product-deep-link-resolve` | `A10` | 1 | | |
| `act:a10-return-a-real-status-for-routes-that-do-not-exist` | `A10` | 1 | | |
| `act:a10-serve-the-product-content-before-javascript-runs` | `A10` | 1 | | |
| `act:a4-allow-the-data-paths-for-named-ai-crawlers` | `A4` | 1 | | |
| `act:a4-serve-a-robots-txt-that-names-ai-crawlers` | `A4` | 1 | | |
| `act:e5-fire-every-declared-control-before-the-first-host` | `E5` | 0 | | |
| `act:e5-investigate-the-control-verdict-that-moved` | `E5` | 0 | | |
| `act:e5-order-the-controls-before-the-surfaces` | `E5` | 0 | | |
| `act:g1d-publish-the-error-measure-as-a-structured-field` | `G1-D` | 0 | | |

### What `value` holds, and the one thing it over-states

`value` is computed by `tag_prescriptions.value_of` and recomputed independently in the gate. It is flat by construction so `load_framework_graph.flatten` can promote every sub-key to `value_<name>` in Neo4j (Neo4j has no map property type), and `tests/test_prescriptions.py::test_value_is_flat_so_the_projection_can_promote_every_sub_key` holds it flat.

- **`bodies_failing_now`** — bodies on the cycle of record (`scan_2026-09-10_rj2`, declared at `docs/reports/publication.yaml:snapshot_cycle`) whose verdict on the verifying rule's leg is `fail`, over `scan_matrix_tierA_2026-09-10_rj2.json` (legs A4, A5, A10, A11-declared, A12) and `scan_matrix_product_2026-09-10_rj2.json` (A1, A2, A3, A6, A8, A9, B3, D1, D4, F4), 16 bodies. A body fails a leg when any of its rows on that matrix carries `fail`; tier C reference hosts enter no Tier A denominator (DD-059) and are not read.
- **It is a per-LEG count, and that is an upper bound for a single action on a multi-outcome leg.** The matrices carry verdicts, not reasons, so the per-outcome split is not derivable from them; the stored cycle payload (`state/scan_2026-09-10_rj2.json`) is a summary and does not carry the Finding reason strings either. Rather than let a reader over-read the number, every action on a leg with more than one failing outcome carries `value.bodies_failing_now_caveat` saying so in words, and the single-outcome leg (G1-D) carries none. Asserted both ways by `test_a_leg_with_more_than_one_failing_outcome_says_the_count_is_an_upper_bound`.
- **`bodies_failing_now` is 0 for E5 and G1-D, with a source rather than a blank.** Neither leg is on either matrix of the cycle of record — E5's rule judges this instrument's own cycle, and G1-D was withdrawn from the host level by DD-066 and is not among the product matrix's ten legs. The source says exactly that.
- **`constructs_served`** — read from the `DECOMPOSES_INTO` edges that reach the indicator, with the edges named as the source. (The task file said "via the indicator's `MEASURES` edge"; see §4 premise 1.)
- **`downstream_indicators`** — 3 entries over the whole layer, each quoted from the record and checked against it: **A4 → A11** (`ind:A11.indicator`: *"A4 upgraded from declared-policy check to three-layer comparison"*), **A4 → A12** (`spec:A12.signal`: *"A robots.txt that DISALLOWS the path is not incoherence — it is A4's measurement, and this indicator is `not_applicable` there."*), **A11 → A12** (`ind:A12.candidate_rationale`: *"The public-observable leg of A11's enforced layer."*). The scan that found them was a token sweep of every string property of every node for an indicator code other than its own; it returned seven hits, of which three are presuppositions among these legs. The fourth in range — `ind:G1-D.tier_note` naming G1-O — says which leg the G1 instrument judges, not that G1-O presupposes G1-D, so it is not a downstream edge. Every other leg carries the explicit sentence that the scan found nothing, never a silent empty list.

### E5 and A12, marked rather than omitted

- **E5's three actions carry `applies_to_publisher: false`** and an `applies_to_note` naming the actor as the operator of the harness. E5's rule judges this instrument's own cycle, not a publisher's surface. They are in the layer on the same footing as the rest because the instrument is measured by its own instrument, which is what E5 is for. One of them — `act:e5-investigate-the-control-verdict-that-moved` — is the only action here whose execution is forbidden to change the check, which is the point of a pre-registered control.
- **A12's three actions carry `applies_to_publisher: true`** and a note recording DD-054. The task file anticipated A12 might need `false`; it does not. A12's subject is the publisher's host, exactly as for every other A-criterion leg (`rules.measures('RULE-A12-v3') == 'host'`, and a host is the publisher's). What is provisional about A12 is the **indicator**, not who acts on it: its Findings are reported and enter no framework numerator until the operator adopts it. The counts split follows the same logic — `actions_on_candidate_indicators: 3` — because a prescription inherits the standing of the check it is bound to.


---

## 3. The query the layer exists to make

`scripts/prescriptions.py` reads the framework record and the published matrices of the cycle of record. It reads Neo4j for nothing: the record is the source of truth and the projection is a projection, so a query that needed the database up to answer would be asking the wrong thing.

### `scripts/prescriptions.py --all` — every action, ranked by bodies failing now

```
# every action, ranked by bodies failing now — cycle scan_2026-09-10_rj2, 16 bodies
# 45 actions over 17 legs

bodies  leg            outcome                               effort    cost      action
---------------------------------------------------------------------------------------
    13  A2             no_api_description                    pending   pending   Expose the product through an API and publish the API's description
    13  A2             served_but_not_an_api_description     pending   pending   Serve a parseable OpenAPI description where the API is documented
    13  A9             no_machine_first_path                 pending   pending   Publish a machine-first entry point for the product
    13  A9             machine_path_answers_html             pending   pending   Return a machine format at the paths advertised for machines
    13  D1             no_licence                            pending   pending   Publish a machine-readable licence for the product
    13  D1             licence_is_free_text                  pending   pending   State the licence as an identifier, not as a sentence
    13  F4             changelog_entries_lack_revision_class  pending   pending   Carry a revision class on every changelog entry
    13  F4             no_changelog                          pending   pending   Publish a version history for the product
    13  F4             changelog_not_machine_readable        pending   pending   Serve the changelog in a machine-readable format as well as a page
    12  A1             only_pdf                              pending   pending   Publish the product as a structured download beside the PDF
    12  A1             no_structured_link                    pending   pending   Link a data file from the product page and serve it with its own media type
    11  A6             no_structured_markup                  pending   pending   Embed JSON-LD describing the product on the product page
    11  A6             shapes_violation                      pending   pending   Make the Dataset markup conform to the profile it declares
    11  A6             markup_without_dataset_type           pending   pending   Type the product page's existing markup as a Dataset
    11  A8             last_modified_header_only             pending   pending   Declare the product's vintage in the markup, not only in a file header
    11  A8             latest_vintage_pointer_unresolved     pending   pending   Make the latest-vintage pointer resolve
    11  A8             no_declared_date                      pending   pending   Publish a release date for the product
    11  A8             no_latest_vintage_pointer             pending   pending   Serve a stable 'latest' URL for the product on its own host
    11  D4             product_absent_from_catalog           pending   pending   Add the product to the public data inventory already published
    11  D4             catalog_schema_violation              pending   pending   Make the public data catalog conform to the DCAT-US schema
    11  D4             no_catalog                            pending   pending   Publish a data.json inventory on the host
    10  A5             discovery_file_omits_product          pending   pending   List the product URL in the discovery file that is already served
    10  A5             no_discovery_file                     pending   pending   Publish a sitemap and point robots.txt at it
    10  B3             no_methodology_link                   pending   pending   Link the methodology from the product page
    10  B3             no_structured_text_methodology        pending   pending   Publish a methodology document reachable from the product surface
    10  B3             methodology_pdf_only                  pending   pending   Publish the methodology in structured text beside the PDF
    10  B3             methodology_requires_js               pending   pending   Serve the methodology document without requiring JavaScript
     7  A3             filtered_query_not_whole_product      pending   pending   Add a whole-product download beside the query builder
     7  A3             no_whole_product_download             pending   pending   Link a bulk download of the product from the product page
     7  A3             below_bulk_floor                      pending   pending   Publish the complete product, not a sample extract
     4  A12            declared_permits_enforced_refuses     pending   pending   Align the edge or bot manager with what robots.txt declares
     4  A12            nothing_declared_for_this_client      pending   pending   Publish a robots.txt group that an identified machine client matches
     4  A12            robots_itself_refused                 pending   pending   Serve /robots.txt to every client, including ones the edge does not recognise
     2  A11-declared   nothing_declared                      pending   pending   Declare a crawler policy for the product path
     2  A11-declared   robots_disallows_ai_crawlers          pending   pending   Permit, in robots.txt, the AI crawlers the product is meant to reach
     2  A11-declared   meta_robots_contradicts_robots_txt    pending   pending   Resolve the meta-robots directive that contradicts robots.txt
     1  A10            deep_link_error_status                pending   pending   Make the product's own deep link resolve
     1  A10            soft_404                              pending   pending   Return a real HTTP status for routes that do not exist
     1  A10            client_rendered_shell                 pending   pending   Serve the product's content in the first response, before JavaScript runs
     1  A4             robots_disallows_ai_crawlers          pending   pending   Allow the product's data paths for the AI crawlers you intend to serve
     1  A4             no_robots_txt                         pending   pending   Serve a robots.txt and state the policy for AI crawlers in it
     0  E5             zero_controls_fired                   pending   pending   Fire every declared control fixture before the cycle contacts a host  [not a publisher action]
     0  E5             control_verdict_not_as_expected       pending   pending   Investigate a control verdict that moved, and never retune the expectation  [not a publisher action]
     0  E5             controls_ran_after_surfaces           pending   pending   Order the control fixtures ahead of every real host in the cycle  [not a publisher action]
     0  G1-D           no_error_measure_field                pending   pending   Publish the error measure as a structured field beside the estimate
```

The ranking is the January third slide without a slide: the nine worst-served actions each fail 13 of 16 bodies, and every one of them is a product-surface basic — an API and its description, a machine-first entry point, a machine-readable licence, a version history. The three bodies at the bottom of the failing-leg distribution (BLS, BTS, ORES) fail exactly one leg each, and for all three it is A12: their robots.txt permits an identified client that their edge then refuses.

### `scripts/prescriptions.py --body EIA` — one body on the cycle of record

EIA fails 5 of the 15 legs judged on this cycle, which makes it short enough to print whole. `--body NCHS` (12 failing legs) and `--body BJS` (11) have the same shape at greater length.

```
# EIA — prescriptions from cycle scan_2026-09-10_rj2
#   5 failing leg(s) of the 15 judged; 16 bodies on this cycle

================================================================================================
A2  (ind:A2)   failing on: scan-eia-flagship-1-open-data
   13 of 16 bodies fail this leg (12 others share it)

   [no_api_description] Expose the product through an API and publish the API's description
      No OpenAPI or JSON API description was served at any probed path. Expose the product
      through a documented HTTP API and publish a machine-readable description of it; where the
      product already sits on a data platform, enabling the platform's own API is the cheaper
      route than building one.
      effort: pending    cost: pending
      verified by: RULE-A2-v3
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 23
      'Possible Approach to Implementation': "If you use a data management platform, such as
      CKAN, you may be able to enable an existing API."
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 25
      'Possible Approach to Implementation': "A typical API reference provides a comprehensive
      list of the calls the API can handle, describing the purpose of each one"
      technique: corpus/kernel/openapi-specification-core.md (doc_id `openapi-specification-
      core`), section 2 'Introduction': "The OpenAPI Specification (OAS) defines a standard,
      language-agnostic interface to HTTP APIs which allows both humans and computers to
      discover and understand the capabilities of the service without access to source code,
      documentation, or through network traffic inspection."
      technique: corpus/kernel/schema-org-webapi.md (doc_id `schema-org-webapi`), property
      `documentation`: "Further documentation describing the Web API in more detail."

   [served_but_not_an_api_description] Serve a parseable OpenAPI description where the API is documented
      A document is served at a probed API path but does not parse as an API description; a JSON
      content type alone is not a description. Publish an OpenAPI Description document (YAML or
      JSON) at that path, so a client can discover the operations without reading prose.
      effort: pending    cost: pending
      verified by: RULE-A2-v3
      technique: corpus/kernel/openapi-specification-core.md (doc_id `openapi-specification-
      core`), section 2 'Introduction': "The OpenAPI Specification (OAS) defines a standard,
      language-agnostic interface to HTTP APIs which allows both humans and computers to
      discover and understand the capabilities of the service without access to source code,
      documentation, or through network traffic inspection."
      technique: corpus/kernel/openapi-specification-core.md (doc_id `openapi-specification-
      core`), section 2 'Introduction': "An OpenAPI Description (OAD) can then be used by
      documentation generation tools to display the API"
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 25
      'Possible Approach to Implementation': "A typical API reference provides a comprehensive
      list of the calls the API can handle, describing the purpose of each one"

================================================================================================
A9  (ind:A9)   failing on: scan-eia-flagship-1-open-data
   13 of 16 bodies fail this leg (12 others share it)

   [no_machine_first_path] Publish a machine-first entry point for the product
      None of the probed machine-first paths is served, so a machine client's only entry is the
      human page. Publish an entry point built for machines — an `/llms.txt` at the site root,
      an API root, or a data endpoint — and link it from the product page.
      effort: pending    cost: pending
      verified by: RULE-A9-v1
      technique: corpus/kernel/llmstxt-proposal.md (doc_id `llmstxt-proposal`), 'Proposal': "We
      propose adding a `/llms.txt` markdown file to websites to provide LLM-friendly content."
      technique: corpus/kernel/llmstxt-proposal.md (doc_id `llmstxt-proposal`), 'Proposal':
      "These links can be provided as HTML `<link>` elements, or as an HTTP `Link:` response
      header."
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 23
      'Possible Approach to Implementation': "If you use a data management platform, such as
      CKAN, you may be able to enable an existing API."

   [machine_path_answers_html] Return a machine format at the paths advertised for machines
      A probed machine-first path answers with HTML rather than a machine format: the route
      exists and returns the human page. Serve the machine representation at that path, or
      honour the request's `Accept` header and return the machine format when it is asked for.
      effort: pending    cost: pending
      verified by: RULE-A9-v1
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 19
      'Possible Approach to Implementation': "A possible approach to implementation is to
      configure the Web server to deal with content negotiation of the requested resource."
      technique: corpus/kernel/llmstxt-proposal.md (doc_id `llmstxt-proposal`), 'Proposal':
      "pages with information that agents might need provide a clean markdown version of those
      pages at the same URL as the original page"
      technique: corpus/kernel/llmstxt-proposal.md (doc_id `llmstxt-proposal`), 'Proposal':
      "These links can be provided as HTML `<link>` elements, or as an HTTP `Link:` response
      header."

================================================================================================
D1  (ind:D1)   failing on: scan-eia-flagship-1-open-data
   13 of 16 bodies fail this leg (12 others share it)

   [no_licence] Publish a machine-readable licence for the product
      No licence appears in the product page's markup, in an HTTP `Link` header, or at a probed
      terms endpoint, so a consumer has to assume the worst or guess. Publish the licence as a
      machine-readable value on the product's markup and in its catalogue record.
      effort: pending    cost: pending
      verified by: RULE-D1-v3
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 4
      'Possible Approach to Implementation': "Data license information can be available via a
      link to, or embedded copy of, a human-readable license agreement."
      technique: corpus/kernel/schema-org-dataset.md (doc_id `schema-org-dataset`), 'Dataset'
      example, the `license` field: ""license": [ "http://spdx.org/licenses/CC0-1.0",
      "https://creativecommons.org/publicdomain/zero/1.0" ]"

   [licence_is_free_text] State the licence as an identifier, not as a sentence
      A licence statement is present and its value is free text, so a machine can see that terms
      exist but not what they permit. State the licence as a recognised identifier — an SPDX id
      or the licence's canonical URL — in the markup's `license` property.
      effort: pending    cost: pending
      verified by: RULE-D1-v3
      technique: corpus/kernel/schema-org-dataset.md (doc_id `schema-org-dataset`), 'Dataset'
      example, the `license` field: ""license": [ "http://spdx.org/licenses/CC0-1.0",
      "https://creativecommons.org/publicdomain/zero/1.0" ]"
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 4
      'Possible Approach to Implementation': "Data license information can be available via a
      link to, or embedded copy of, a human-readable license agreement."

================================================================================================
F4  (ind:F4)   failing on: scan-eia-flagship-1-open-data
   13 of 16 bodies fail this leg (12 others share it)

   [changelog_entries_lack_revision_class] Carry a revision class on every changelog entry
      A machine-readable changelog is served and too few of its entries carry a revision class,
      so a consumer can see that something changed but not whether it was a correction, a
      scheduled revision or a new release. Put a class on every entry — an Atom `<category
      term=...>`, or a `type`/`change_type` field in JSON.
      effort: pending    cost: pending
      verified by: RULE-F4-v3
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 8
      'Possible Approach to Implementation': "Provide a list of published versions and a
      description for each version that explains how it differs from the previous version."
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 7
      'Possible Approach to Implementation': "Include a unique version number or date as part of
      the metadata for the dataset."

   [no_changelog] Publish a version history for the product
      No changelog or release-notes endpoint is served, so a consumer holding an older vintage
      cannot learn what changed. Publish a list of released versions with, for each, what
      differs from the previous one; a single dedicated URL that returns the complete history is
      enough.
      effort: pending    cost: pending
      verified by: RULE-F4-v3
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 8
      'Possible Approach to Implementation': "Provide a list of published versions and a
      description for each version that explains how it differs from the previous version."
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 8
      'Possible Approach to Implementation': "An API can expose a version history with a single
      dedicated URL that retrieves the latest version of the complete history."

   [changelog_not_machine_readable] Serve the changelog in a machine-readable format as well as a page
      A changelog page is served and not in a machine-readable content type, so the history is
      readable only by a person. Publish the same history as JSON, Atom or RSS at its own URL
      and keep the human page beside it.
      effort: pending    cost: pending
      verified by: RULE-F4-v3
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 8
      'Possible Approach to Implementation': "An API can expose a version history with a single
      dedicated URL that retrieves the latest version of the complete history."
      technique: corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 12
      'Possible Approach to Implementation': "Make data available in a machine-readable
      standardized data format that is easily parseable including but not limited to CSV, XML,
      HDF5, JSON and RDF serialization syntaxes"

================================================================================================
D4  (ind:D4)   failing on: scan-eia-flagship-1-open-data
   11 of 16 bodies fail this leg (10 others share it)

   [product_absent_from_catalog] Add the product to the public data inventory already published
      A catalog is served on the host and the product is not in it, so the product is invisible
      to every consumer that starts from the inventory. Add the product's record to the catalog
      file; the inventory is meant to list all of the agency's public data assets, whether they
      are downloads or APIs.
      effort: pending    cost: pending
      verified by: RULE-D4-v2
      technique: corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), 'What to
      Document - Datasets and Web APIs': "The catalog file for each agency should list all of
      the agency’s datasets that can be made public, regardless of whether they are distributed
      by a file download or a Web API."
      technique: corpus/kernel/schema-org-datacatalog.md (doc_id `schema-org-datacatalog`),
      property `dataset`: "A dataset contained in this catalog."

   [catalog_schema_violation] Make the public data catalog conform to the DCAT-US schema
      The product appears in the host's catalog and the catalog violates the schema, so a
      consumer that validates before reading rejects the whole file. Fix the fields the
      validator names; field names are case-sensitive and a near-miss is a miss.
      effort: pending    cost: pending
      verified by: RULE-D4-v2
      technique: corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), 'Metadata
      File Format - JSON': "The Project Open Data schema is case sensitive."
      technique: corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), 'Metadata
      File Format - JSON': "When a record has an **accessURL** or **downloadURL** , they should
      be contained as objects within a **distribution**."
      technique: corpus/kernel/dcat-us-3-dataset-schema.md (doc_id `dcat-us-3-dataset-schema`),
      'DCAT-US 3.0: Dataset': "Information about a dataset, including identifiers, contacts,
      coverage, distributions, and related resources."

   [no_catalog] Publish a data.json inventory on the host
      No public `data.json` catalog is served on this host, so there is no machine-readable
      inventory of what the agency publishes. Publish one at `/data.json` and let its own URL be
      its identifier.
      effort: pending    cost: pending
      verified by: RULE-D4-v2
      technique: corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), 'What to
      Document - Datasets and Web APIs': "The catalog file for each agency should list all of
      the agency’s datasets that can be made public, regardless of whether they are distributed
      by a file download or a Web API."
      technique: corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), 'Catalog'
      fields, Metadata Catalog ID: "This should be the URL of the data.json file itself"
```

---

## 4. Every premise this task file got wrong

1. **"`constructs_served[]` (via the indicator's `MEASURES` edge)" — there is no such edge from an indicator.** `MEASURES` in this graph is `Rule -[:MEASURES]-> AssessmentIndicator`, minted by `assessment/harness/scan/publish.py::link_rules_to_indicators` as the bridge between the two projections. It points *at* the indicator and carries no construct. The construct reaches the indicator the other way, on `AssessmentConstruct -[:DECOMPOSES_INTO]-> AssessmentIndicator`, which is what `value.constructs_served` is read from and what its source names. Decision 1's intent is served; its edge name was wrong.

2. **"The schema is in the record's schema file" — the record has no schema file of its own.** The assessment layer's type catalogue is the `assessment_layer:` block of `kg/schema.yaml` (`source_of_truth: framework/ai_readiness_framework.json`, `parser_visible: false`), which is where `Action` and `REMEDIATES` went. I did **not** bump `assessment_layer.version` from `0.4.0`: the record's own `schema_epoch` is the same literal and is an `AUTHORED_TOP` field written by `scripts/build_framework_graph.py`, so moving one without the other would put two versions of one epoch on the record and its schema, and moving both would edit an authored field and take that generator out of its byte-for-byte no-op. The addition is append-only and is commented in place with that reasoning.

3. **"the same three `build_l0_site.py --only` payloads are regenerated" — it is two `--only` names, over six published files.** The predecessor's third name was `sources_per_check`, and it moved there only because that task renamed a property the appendix reads off the indicator node. This task renames nothing and adds no indicator property, so `data/sources_per_check.json` does not move. What moved is `framework_copy` (`docs/data/ai_readiness_framework.json`) and `data_manifest` (`docs/data/index.json`, plus the four citation files, which are rewritten with the same bytes because the build date has not rolled over). Verified by the protected-paths check, which allows the citation files and finds them unmoved.

4. **The write set omitted three files the gate cannot pass without.** Each is named in `scripts/check_protected_prescriptions.sh` with its reason:
   - **`scripts/framework_writeback.py`** — the single writer, and the place `cc_tasks/2026-09-07_scan_hygiene.md` §3 puts `counts` ("that lives in the shared helper, not in three scripts"). A layer of 45 nodes and 45 edges that no counter mentions is the DD-040 drift the module exists to prevent, so `recount` gained `actions` and `actions_on_candidate_indicators` and `COUNTS_BASIS` gained the sentence that says what they count. Nothing else in it moved; the refusal behaviour, the delta and the no-op path are untouched and their tests pass unchanged.
   - **`tests/test_framework_projection_roundtrip.py`** — the DD-057 gate that makes verifying framework state by Cypher valid at all. Its count query names its labels as a **literal**, so a node in the JSON under a label the query does not know is a mismatch, and the gate would have failed for the wrong reason. It learned `Action` and `a:Action`, and gained a test for the thing a plain `MERGE` would have got wrong twice — `REMEDIATES` is the only edge in this layer with properties, and two actions on one indicator would have collapsed into one relationship.
   - **`tests/test_framework_single_writer.py`** — asserts, as a literal, exactly what the skeleton generator does *not* author and `merge` therefore preserves. The prescription layer is in that set by construction: an action is written against a rule's failing outcomes and the skeleton predates every rule. The literal moved with it, which is also the evidence that `build_framework_graph.py` is still a no-op.

5. **Decision 2's "at least one action per failing outcome" resolved to exactly one, and that was not free.** `framework_writeback.delta` identifies an edge by `(from, type, to)`. Two `REMEDIATES` edges from one action to one indicator with different `outcome` values would collide in that dict and the delta of a later write-back would be wrong — silently. One action per outcome keeps edge identity unique and keeps `outcome` singular as decision 2 writes it. The alternative (one action, a list of outcomes on one edge) would have deviated from the decision's own wording. Both the JSON-level and graph-level uniqueness are asserted.

6. **Decision 3's "every band is a legal value or `estimate:pending`" reads against decision 1's "an `estimate:pending` band is left empty".** They are reconciled as: the **band** is a legal value or absent, and the **source** is a locator or the literal `estimate:pending`; a pending source with a non-null band, and a sourced band with an illegal value, both fail. `test_every_band_is_a_legal_value_or_an_explicit_pending`.

7. **A12 does not need `applies_to: publisher` false.** See §2. The task file grouped it with E5; only E5 qualifies.

8. **The premise the task file got right, and it is the load-bearing one.** "The value of an action is therefore cold data: the count of bodies its completion would move from fail to pass on the leg that verifies it. Nothing about value needs an opinion." That held — with the one qualification in §2 about the per-leg count being an upper bound on a multi-outcome leg, which the nodes now carry themselves.

---

## 5. The gate

| check | result | exit | wall-clock | log |
|---|---|---|---|---|
| **full suite** (`pytest tests/ assessment/ -q -rs`, the whole tier, not `gate-fast`) | **2341 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed** | 0 | 1388.93 s (`real 23m11.323s`) | `logs/suite_prescriptions.log` |
| `seldon verify` | All checks passed | 0 | — | `logs/verify_prescriptions.log` |
| `scripts/check_protected_prescriptions.sh` | PROTECTED PATHS OK | 0 | — | `logs/protected_prescriptions.log` |
| framework projection (`scripts/load_framework_graph.py`) | 171 nodes, 325 edges, `actions_in_graph: 45`, `harness_leg_indicators_without_an_action: []` | 0 | — | `logs/prescriptions_project.log` |
| site payloads (`build_l0_site.py --only framework_copy --only data_manifest`) | 6 paths written | 0 | — | `logs/prescriptions_site.log` |

**The three skips, named** (a gate row that omits the skip count is a placeholder):
- `tests/test_dispatch_config.py:333` — `interactive_only`: `SELDON_SESSION_ID` is set, so this is a dispatched session and the quiet checkout the test asserts cannot exist inside one.
- `tests/test_scan_harness.py:281` — E5 judges the cycle's controls, not a surface.
- `assessment/tests/test_g1_preservation.py:337` — no dev proposition publishes SE and CI together.

These are the three the task file expected. **The Neo4j-gated tests did not skip**: Neo4j was up, so `tests/test_framework_projection_roundtrip.py` and the four Cypher tests in `tests/test_prescriptions.py` ran and passed, which is what makes the Cypher verification of this layer valid rather than merely unfalsified (DD-057).

**The projection followed the write-back, before the gate ran.** `framework_writeback` event `7eeeecc109e64d49ae6026c9c00480f4` on `events/batch-033_framework.jsonl` (one appended line; the shard is 18 lines), framework sha256 `c6b1d3fd…fe7731`, delta `{nodes_added: {Action: 45}, edges_added: {REMEDIATES: 45}, nodes_changed: 0, edges_changed: 0, nodes_removed: {}, edges_removed: {}, counts_keys_dropped: []}`. A second run of the writer returned `unchanged: true`. `scripts/build_framework_graph.py --dry-run` over the new record is still a byte-for-byte no-op (`nodes_changed: 0`, `unchanged: true`), asserted inside the protected-paths check rather than only reported here.

## 6. Where to re-read every number in this file

```
logs/suite_prescriptions.log          the full suite, to its EXIT=0 line
logs/verify_prescriptions.log         seldon verify
logs/protected_prescriptions.log      the protected-paths diff
logs/prescriptions_project.log        scripts/load_framework_graph.py
logs/prescriptions_site.log           scripts/build_l0_site.py --only framework_copy --only data_manifest
logs/prescriptions_all.log            scripts/prescriptions.py --all        (quoted whole in §3)
logs/prescriptions_body_EIA.log       scripts/prescriptions.py --body EIA   (quoted whole in §3)
logs/prescriptions_pending.log        scripts/prescriptions.py --pending    (the §2 table's source)
```

`logs/` is gitignored, so these are local artifacts this session can point at; what ships is this file and the three commands that regenerate any of it:

```
/opt/anaconda3/bin/python3 scripts/tag_prescriptions.py --check     # validate the table
/opt/anaconda3/bin/python3 scripts/prescriptions.py --all           # the ranked view
bash scripts/check_protected_prescriptions.sh                       # the write set, against HEAD
```

## 7. What this does not do, and what the next task is owed

- **The 20 unassigned indicators and the O/D rows get no actions**, per decision 6. A prescription for an indicator with no cold data behind it is a sourced technique with no `bodies_failing_now` — a different and smaller task, and DN-005 §4 orders the levels before it.
- **The 90 pending bands are the layer's open half.** Until they are filled, the layer answers "what to do" and "how much of the system it moves" and does not answer "what it costs". That is the honest state and the tests pin it: `test_no_band_was_filled_from_a_source_that_does_not_state_one` asserts zero sourced bands, so a later task that fills one has to move a literal and say where the band came from.
- **Per-outcome attribution is not derivable from the published matrices.** A `bodies_failing_now` that was exact per action would need the stored Findings' reason strings joined to the outcome fragments. The fragments now exist on every `REMEDIATES` edge, which is what makes that join possible for whoever wants it; the matrices and the stored cycle payload do not carry the reasons.
- **Nothing was measured, re-judged or rebuilt.** No cycle ran, no host was contacted, no rule was edited, no Observation or Finding was minted. `state/`, `corpus/`, `assessment/`, `docs/reports/` and `docs/design/` are byte-identical to HEAD, asserted rather than asserted-about.
