# RESULT: every effort and cost band carries a notional relative value, tagged by technique class, and the layer stops waiting

**Task:** `cc_tasks/2026-09-17_notional_bands.md`. I globbed `2026-09-17_notional_bands_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher from HEAD `5556235`. The predecessor, `2026-09-17_unassigned_indicators.md`, already had its RESULT on `e1c9c7b`, so the SEQUENCING line held; `2026-09-17_mcp_over_the_graph.md` has not run, so no prescriptions tool has yet printed a pending band.
**Framework layer served:** DN-005 §2.3, prescription.
**Spend:** zero model calls. **Network:** none beyond `git push`.
**Gate:** green, with every command run to its `EXIT=` line before this file was written.
- `make gate-full` — **the full tier**, `/opt/anaconda3/bin/python3 -m pytest tests/ assessment/ -q -rs`: **2353 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed**, `EXIT=0`, wall-clock 1439.11 s. Expected skips: 3, and the three are the expected three.
- `seldon verify`: **All checks passed**, `EXIT=0`.
- `scripts/check_protected_notional_bands.sh`: **PROTECTED PATHS OK**, `EXIT=0`.
- framework projection round-trip (DD-057): `EXIT=0`, `actions_in_graph: 45`, `harness_leg_indicators_without_an_action: []`.
The log paths are in §4.

**In one paragraph.** The 90 empty bands are filled. Every `Action` now carries a `technique_class` — one of five, defined once in DN-005 ADDENDUM_03 — and the class fixes both bands through one table, so no band is authored per action. **45 classes, 90 bands, 0 of them empty and 0 of them `estimate:pending`**: 17 actions `edit_existing` (hours / none), 14 `publish_new_file` (days / staff_time), 10 `change_server_behaviour` (weeks / staff_time), 1 `expose_api` (quarter / procurement), 3 `harness_side` (hours / none). Each band source reads `notional:technique_class:<class>, task 2026-09-17_notional_bands`, each node carries the adjustment instruction verbatim in `band_note`, and `scripts/prescriptions.py` prints that sentence once per invocation with a `(notional)` marker on the header line rather than beside 45 rows. The literal `estimate:pending` appears nowhere in the record, the catalogue or the two scripts, and a test asserts its absence. Ten of the 45 classes were not obvious on the description's face; each carries its own `technique_class_reason` on the node, and §0 tables all 45 so a reader can dispute one.

---

## 0. The class table — all 45 rows

Generated from the record as written, so this is the record's own content and not a restatement of the tagger's table. The last column is `technique_class_reason` as it stands on the node; `—` is a row whose class is obvious from the action's description and carries no reason.

| leg | outcome | action | class | effort | cost | why this class, where it is not obvious |
|---|---|---|---|---|---|---|
| `A1` | `no_structured_link` | `a1-serve-the-data-files-with-their-own-media-type` | `change_server_behaviour` | weeks | staff_time | the rule classifies on the RESPONSE content type, so the act is the web server or CDN media-type configuration; linking the file without it does not move the verdict |
| `A1` | `only_pdf` | `a1-publish-a-structured-distribution` | `publish_new_file` | days | staff_time | — |
| `A10` | `client_rendered_shell` | `a10-serve-the-product-content-before-javascript-runs` | `change_server_behaviour` | weeks | staff_time | — |
| `A10` | `deep_link_error_status` | `a10-make-the-product-deep-link-resolve` | `change_server_behaviour` | weeks | staff_time | — |
| `A10` | `soft_404` | `a10-return-a-real-status-for-routes-that-do-not-exist` | `change_server_behaviour` | weeks | staff_time | — |
| `A11-declared` | `meta_robots_contradicts_robots_txt` | `a11-resolve-the-meta-robots-directive-that-contradicts-robots-txt` | `edit_existing` | hours | none | — |
| `A11-declared` | `nothing_declared` | `a11-declare-a-crawler-policy-for-the-product-path` | `publish_new_file` | days | staff_time | no robots.txt is served, so this is the same act as A4's `no_robots_txt` action on the same host: a file published where none exists |
| `A11-declared` | `robots_disallows_ai_crawlers` | `a11-permit-the-ai-crawlers-you-intend-to-serve-on-the-product-path` | `edit_existing` | hours | none | — |
| `A12` | `declared_permits_enforced_refuses` | `a12-align-the-edge-with-the-declaration` | `change_server_behaviour` | weeks | staff_time | — |
| `A12` | `nothing_declared_for_this_client` | `a12-publish-a-robots-txt-group-an-identified-client-matches` | `edit_existing` | hours | none | the act named is adding a group to robots.txt. Where the file is absent outright, the publishing act is already carried by A4's and A11's `publish_new_file` actions on the same host, so classing this one `publish_new_file` would count that work twice |
| `A12` | `robots_itself_refused` | `a12-serve-robots-txt-to-every-client` | `change_server_behaviour` | weeks | staff_time | the file exists and the EDGE refuses it, so the act is a bot-management exemption rather than an edit to the file |
| `A2` | `no_api_description` | `a2-expose-an-api-and-publish-its-description` | `expose_api` | quarter | procurement | — |
| `A2` | `served_but_not_an_api_description` | `a2-serve-a-parseable-api-description-at-the-documented-path` | `publish_new_file` | days | staff_time | not `expose_api`: a document is already served at the probed API path, so what is missing is the description file and not the API |
| `A3` | `below_bulk_floor` | `a3-publish-the-complete-file-not-a-sample` | `publish_new_file` | days | staff_time | — |
| `A3` | `filtered_query_not_whole_product` | `a3-add-a-whole-product-download-beside-the-query-builder` | `publish_new_file` | days | staff_time | — |
| `A3` | `no_whole_product_download` | `a3-link-a-bulk-download-from-the-product-page` | `publish_new_file` | days | staff_time | — |
| `A4` | `no_robots_txt` | `a4-serve-a-robots-txt-that-names-ai-crawlers` | `publish_new_file` | days | staff_time | no robots.txt is served at all, so the act is publishing a file the host does not have, not editing a directive in one it does |
| `A4` | `robots_disallows_ai_crawlers` | `a4-allow-the-data-paths-for-named-ai-crawlers` | `edit_existing` | hours | none | — |
| `A5` | `discovery_file_omits_product` | `a5-list-the-product-url-in-the-sitemap` | `edit_existing` | hours | none | — |
| `A5` | `no_discovery_file` | `a5-publish-a-sitemap-and-point-robots-txt-at-it` | `publish_new_file` | days | staff_time | — |
| `A6` | `markup_without_dataset_type` | `a6-type-the-product-page-as-a-dataset` | `edit_existing` | hours | none | — |
| `A6` | `no_structured_markup` | `a6-embed-json-ld-on-the-product-page` | `edit_existing` | hours | none | a JSON-LD block is markup added to a page the host already serves: no new file, and no change to how the server answers |
| `A6` | `shapes_violation` | `a6-make-the-dataset-markup-conform-to-the-profile` | `edit_existing` | hours | none | — |
| `A8` | `last_modified_header_only` | `a8-declare-the-product-vintage-in-the-markup` | `edit_existing` | hours | none | — |
| `A8` | `latest_vintage_pointer_unresolved` | `a8-make-the-latest-pointer-resolve` | `change_server_behaviour` | weeks | staff_time | — |
| `A8` | `no_declared_date` | `a8-publish-a-release-date-for-the-product` | `edit_existing` | hours | none | — |
| `A8` | `no_latest_vintage_pointer` | `a8-serve-a-stable-latest-url-on-the-product-host` | `change_server_behaviour` | weeks | staff_time | a URL that always resolves to the latest release is a route the server maintains across releases, not a file published once |
| `A9` | `machine_path_answers_html` | `a9-return-a-machine-format-at-the-machine-path` | `change_server_behaviour` | weeks | staff_time | — |
| `A9` | `no_machine_first_path` | `a9-publish-a-machine-first-entry-point` | `publish_new_file` | days | staff_time | — |
| `B3` | `methodology_pdf_only` | `b3-publish-the-methodology-in-structured-text` | `publish_new_file` | days | staff_time | — |
| `B3` | `methodology_requires_js` | `b3-serve-the-methodology-without-javascript` | `change_server_behaviour` | weeks | staff_time | the document is already served and the failure is that its content needs JavaScript to appear; the first route the action names is server-rendering it |
| `B3` | `no_methodology_link` | `b3-link-the-methodology-from-the-product-page` | `edit_existing` | hours | none | — |
| `B3` | `no_structured_text_methodology` | `b3-publish-a-methodology-document-reachable-from-the-product` | `publish_new_file` | days | staff_time | — |
| `D1` | `licence_is_free_text` | `d1-state-the-licence-as-an-identifier` | `edit_existing` | hours | none | — |
| `D1` | `no_licence` | `d1-publish-a-machine-readable-licence` | `edit_existing` | hours | none | the licence is a value written into markup and a catalogue record the host already serves, not a file of its own |
| `D4` | `catalog_schema_violation` | `d4-make-the-catalog-conform-to-dcat-us` | `edit_existing` | hours | none | — |
| `D4` | `no_catalog` | `d4-publish-a-data-json-inventory` | `publish_new_file` | days | staff_time | — |
| `D4` | `product_absent_from_catalog` | `d4-add-the-product-to-the-public-data-inventory` | `edit_existing` | hours | none | — |
| `E5` | `control_verdict_not_as_expected` | `e5-investigate-the-control-verdict-that-moved` | `harness_side` | hours | none | — |
| `E5` | `controls_ran_after_surfaces` | `e5-order-the-controls-before-the-surfaces` | `harness_side` | hours | none | — |
| `E5` | `zero_controls_fired` | `e5-fire-every-declared-control-before-the-first-host` | `harness_side` | hours | none | — |
| `F4` | `changelog_entries_lack_revision_class` | `f4-carry-a-revision-class-on-every-changelog-entry` | `edit_existing` | hours | none | — |
| `F4` | `changelog_not_machine_readable` | `f4-serve-the-changelog-in-a-machine-readable-format` | `publish_new_file` | days | staff_time | — |
| `F4` | `no_changelog` | `f4-publish-a-version-history-endpoint` | `publish_new_file` | days | staff_time | — |
| `G1-D` | `no_error_measure_field` | `g1d-publish-the-error-measure-as-a-structured-field` | `edit_existing` | hours | none | — |

**How a class was chosen.** From the action's own `description` and the kinds of its technique sources, in that order. The four publisher-facing classes separate on one question — *what does the host have to change?* A value inside something it already serves (`edit_existing`); a file it does not serve yet (`publish_new_file`); how it answers a request rather than what it holds (`change_server_behaviour`); or an interface that does not exist (`expose_api`). `harness_side` is the fifth because E5's rule judges this instrument's own cycle and its actor is the operator of the harness, which the record already said in `applies_to_publisher: false`.

**No sixth class was added.** Decision 1 forbids one unless a second action needs it, and no second action did. The three rows that came closest are the ones whose reasons say so: A12's `nothing_declared_for_this_client` (a robots.txt that may be absent *or* present-and-unmatched), B3's `methodology_requires_js` (server-render *or* publish a copy) and A2's `served_but_not_an_api_description` (a description file where the API already answers). Each was resolved to an existing class with the reason on the node.

## 1. Counts

| class | actions | `effort_band` | `cost_band` |
|---|---|---|---|
| `edit_existing` | **17** | hours | none |
| `publish_new_file` | **14** | days | staff_time |
| `change_server_behaviour` | **10** | weeks | staff_time |
| `expose_api` | **1** | quarter | procurement |
| `harness_side` | **3** | hours | none |
| **total** | **45** | | |

| | |
|---|---|
| bands filled | **90** of 90 (45 effort + 45 cost) |
| bands empty | **0** |
| bands whose source is `estimate:pending` | **0** (the literal appears nowhere) |
| bands whose source is a document locator | **0** — no document on disk states one; the failed search stands in `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §0 |
| bands whose source is a `notional:` marker naming its class | **90** |
| actions carrying `band_note` verbatim | **45** (1 distinct sentence) |
| actions carrying `technique_class_reason` | **10** |

Effort bands over the 45 actions: **hours 20, days 14, weeks 10, quarter 1**. Cost bands: **none 20, staff_time 24, procurement 1**.

**`cost_band: tooling` is reached by no class**, so three of its four legal values are used. The value stays in `COST_BANDS` and in `kg/schema.yaml` rather than being dropped, because an enumeration member removed for being unused is how the later action that needs it comes to be mis-banded. The task file's band table has no row for it; this is a fact about the table, reported rather than repaired.

**Live Cypher after projection** (`logs/notional_cypher.log`), which is valid because `tests/test_framework_projection_roundtrip.py` is green (DD-057):

```
edit_existing            hours    none         17
publish_new_file         days     staff_time   14
change_server_behaviour  weeks    staff_time   10
harness_side             hours    none         3
expose_api               quarter  procurement  1
actions with an empty or unmarked band: 0
distinct band_note on the graph: 1
actions whose band source still says pending: 0
```

## 2. `scripts/prescriptions.py --all`, with the note

Re-readable at `logs/notional_all.log`. The `(notional)` marker is on the header line, the note is at the end, and neither appears beside a band.

```
# every action, ranked by bodies failing now — cycle scan_2026-09-10_rj2, 16 bodies
# 45 actions over 17 legs
# effort and cost are relative bands (notional) — the note is at the end

bodies  leg            outcome                               effort    cost        action
-----------------------------------------------------------------------------------------
    13  A2             no_api_description                    quarter   procurement  Expose the product through an API and publish the API's description
    13  A2             served_but_not_an_api_description     days      staff_time  Serve a parseable OpenAPI description where the API is documented
    13  A9             no_machine_first_path                 days      staff_time  Publish a machine-first entry point for the product
    13  A9             machine_path_answers_html             weeks     staff_time  Return a machine format at the paths advertised for machines
    13  D1             no_licence                            hours     none        Publish a machine-readable licence for the product
    13  D1             licence_is_free_text                  hours     none        State the licence as an identifier, not as a sentence
    13  F4             changelog_entries_lack_revision_class  hours     none        Carry a revision class on every changelog entry
    13  F4             no_changelog                          days      staff_time  Publish a version history for the product
    13  F4             changelog_not_machine_readable        days      staff_time  Serve the changelog in a machine-readable format as well as a page
    12  A1             only_pdf                              days      staff_time  Publish the product as a structured download beside the PDF
    12  A1             no_structured_link                    weeks     staff_time  Link a data file from the product page and serve it with its own media type
    11  A6             no_structured_markup                  hours     none        Embed JSON-LD describing the product on the product page
    11  A6             shapes_violation                      hours     none        Make the Dataset markup conform to the profile it declares
    11  A6             markup_without_dataset_type           hours     none        Type the product page's existing markup as a Dataset
    11  A8             last_modified_header_only             hours     none        Declare the product's vintage in the markup, not only in a file header
    11  A8             latest_vintage_pointer_unresolved     weeks     staff_time  Make the latest-vintage pointer resolve
    11  A8             no_declared_date                      hours     none        Publish a release date for the product
    11  A8             no_latest_vintage_pointer             weeks     staff_time  Serve a stable 'latest' URL for the product on its own host
    11  D4             product_absent_from_catalog           hours     none        Add the product to the public data inventory already published
    11  D4             catalog_schema_violation              hours     none        Make the public data catalog conform to the DCAT-US schema
    11  D4             no_catalog                            days      staff_time  Publish a data.json inventory on the host
    10  A5             discovery_file_omits_product          hours     none        List the product URL in the discovery file that is already served
    10  A5             no_discovery_file                     days      staff_time  Publish a sitemap and point robots.txt at it
    10  B3             no_methodology_link                   hours     none        Link the methodology from the product page
    10  B3             no_structured_text_methodology        days      staff_time  Publish a methodology document reachable from the product surface
    10  B3             methodology_pdf_only                  days      staff_time  Publish the methodology in structured text beside the PDF
    10  B3             methodology_requires_js               weeks     staff_time  Serve the methodology document without requiring JavaScript
     7  A3             filtered_query_not_whole_product      days      staff_time  Add a whole-product download beside the query builder
     7  A3             no_whole_product_download             days      staff_time  Link a bulk download of the product from the product page
     7  A3             below_bulk_floor                      days      staff_time  Publish the complete product, not a sample extract
     4  A12            declared_permits_enforced_refuses     weeks     staff_time  Align the edge or bot manager with what robots.txt declares
     4  A12            nothing_declared_for_this_client      hours     none        Publish a robots.txt group that an identified machine client matches
     4  A12            robots_itself_refused                 weeks     staff_time  Serve /robots.txt to every client, including ones the edge does not recognise
     2  A11-declared   nothing_declared                      days      staff_time  Declare a crawler policy for the product path
     2  A11-declared   robots_disallows_ai_crawlers          hours     none        Permit, in robots.txt, the AI crawlers the product is meant to reach
     2  A11-declared   meta_robots_contradicts_robots_txt    hours     none        Resolve the meta-robots directive that contradicts robots.txt
     1  A10            deep_link_error_status                weeks     staff_time  Make the product's own deep link resolve
     1  A10            soft_404                              weeks     staff_time  Return a real HTTP status for routes that do not exist
     1  A10            client_rendered_shell                 weeks     staff_time  Serve the product's content in the first response, before JavaScript runs
     1  A4             robots_disallows_ai_crawlers          hours     none        Allow the product's data paths for the AI crawlers you intend to serve
     1  A4             no_robots_txt                         days      staff_time  Serve a robots.txt and state the policy for AI crawlers in it
     0  E5             zero_controls_fired                   hours     none        Fire every declared control fixture before the cycle contacts a host  [not a publisher action]
     0  E5             control_verdict_not_as_expected       hours     none        Investigate a control verdict that moved, and never retune the expectation  [not a publisher action]
     0  E5             controls_ran_after_surfaces           hours     none        Order the control fixtures ahead of every real host in the cycle  [not a publisher action]
     0  G1-D           no_error_measure_field                hours     none        Publish the error measure as a structured field beside the estimate

------------------------------------------------------------------------------------------------
Notional relative estimate for a typical federal statistical publisher. Adjust for your
platform, staffing, skills and procurement path; the band orders actions against each other, it
does not predict your calendar or budget.
```

`--bands` (the mode that was `--pending`) prints the same 45 actions with the class each band comes from; `logs/notional_bands.log` holds it.

## 3. Premises this task file got wrong

1. **Decision 5 names the addendum `…_ADDENDUM_02.md`.** DN-005 ADDENDUM_02 already exists — written earlier the same day by `cc_tasks/2026-09-17_unassigned_indicators.md`, the task immediately before this one in the same chain, for the sixth `measurement_basis`. The addendum written here is **ADDENDUM_03**. Nothing was overwritten; `~/GitHub/CLAUDE.md` §11 forbids it, and the task file's own "Immutable once written" would have been violated by a session that took the number literally.
2. **The write set omits `kg/schema.yaml`.** Architecture invariant 4 makes it the single type catalogue. Its `Action` entry stated in prose that the bands "are EMPTY where no source on disk supports a band, and the corresponding `_source` then reads `estimate:pending`" — false after decision 3 — and two properties now exist on 45 nodes (`technique_class`, `band_note`) that the catalogue did not list. A catalogue that describes a record it no longer matches is worse than one that is silent, so the `Action` entry moved: the prose, the property list, and a `technique_class` enumeration beside the two band enumerations. `scripts/check_protected_notional_bands.sh` §4 asserts that **nothing else in the file moved**, by parsing both revisions and comparing them with the `Action` entry removed.
3. **Decision 3 names one test to replace.** Five moved, because four others also encoded the empty band: `test_every_band_is_a_legal_value_or_an_explicit_pending` and `test_the_pending_slots_are_counted_and_reported` on the record, and `test_cypher_the_bands_are_pending_and_the_value_is_promoted` and the last assertion of `test_cypher_the_prescription_query_the_layer_exists_to_make` on the graph. Six tests are new. No test was weakened: the count of notional bands is still a literal (90), the class distribution is a new literal, and the band table is restated in the test file rather than imported from the tagger, so moving a band in `NOTIONAL_BANDS` fails a test instead of validating itself.
4. **Decision 4 governs the body output and `--all`, and says nothing about the third mode.** `--pending` existed to table the pending bands and its name became false the moment they were filled. It is renamed **`--bands`** — same question, *where does this band come from*, now that they are filled — and `--pending` is kept as an accepted alias that prints one line to stderr saying so, because `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §2 cites `--pending` as the re-derivation command and a cited command that stops working is a broken citation in an immutable file.
5. **Decision 2's "the RESULT says which class was chosen and why in one line" reads as a rare case.** Ten of 45 needed one. The reason is written on the node as `technique_class_reason` and not only here, so the row a reader disputes carries its own argument; §0 prints the node's text.
6. **The task file did not anticipate that the write-back event would be stamped with the wrong task.** `scripts/tag_prescriptions.py` had one `TASK` constant serving two purposes: `authored_by` on every node and the `task` field of the `framework_writeback` event. The actions were authored by `2026-09-17_prescription_layer.md` and the bands by this task, so the two were split: `TASK` still goes on the nodes as `authored_by`, and a new `WRITEBACK_TASK` goes on the event. Without the split the event would have claimed the prescription-layer task made a change it never made.
7. **"The site's framework copy and manifest move as before" — half of it did.** `docs/data/ai_readiness_framework.json` and `docs/data/index.json` moved; `CITATION.cff`, `.zenodo.json` and their `docs/data/` copies did not, because their only movable line is a build date and the build is same-day. The build was run with all three `--only` flags anyway, so the absence is a fact about the payloads and not about what was rebuilt.
8. **The supersession the task file declares cannot be written where it points.** `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §2 still tables 90 pending slots and asks the operator to fill them; RESULT files are execution records and are not edited. The supersession is recorded in DN-005 ADDENDUM_03 §1, which names that section explicitly, and here.

**One premise the task file got right that is worth naming, because a gate could have made it false.** Decision 6 says nothing else moves. Nothing else did: no node was added or dropped, no edge was touched, no `counts` key moved, and the 45 changed nodes changed only in the four band fields plus the two new properties. The protected-paths check asserts each of those separately rather than by diff size.

## 4. Gate

**Tier:** `make gate-full` — the whole suite, detached and polled to its `EXIT=` line inside this turn, per `CLAUDE.md`. Not the fast tier. The task touched no rule module, no registry entry and no re-derivation engine, so `gate-task` adds nothing the full run does not already include.

| check | result | log |
|---|---|---|
| `make gate-full` | **2353 passed, 3 skipped, 12 xfailed, 0 deselected**, 0 failed, 248 warnings, 1439.11 s, `EXIT=0` | `logs/suite.log` |
| skips (3, the expected 3) | `tests/test_dispatch_config.py:333` (interactive_only: this is a dispatched session, which holds its own claim and dirties the tree); `tests/test_scan_harness.py:281` (E5 judges the cycle's controls, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | `logs/suite.log` |
| `seldon verify` | all checks passed (34865 events readable; replay skipped as expensive, per its own default), `EXIT=0` | `logs/notional_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` | `logs/notional_protected.log` |
| framework projection | `scripts/load_framework_graph.py`, `EXIT=0`, `actions_in_graph: 45`, `harness_leg_indicators_without_an_action: []` | `logs/notional_projection.log` |
| projection round-trip (DD-057) | `tests/test_framework_projection_roundtrip.py` + `tests/test_prescriptions.py`: 43 passed, `EXIT=0` — run against the live graph, so the Cypher in §1 is valid | `logs/notional_roundtrip.log` |
| band Cypher | §1 | `logs/notional_cypher.log` |
| site payloads | `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest`, `EXIT=0` | `logs/notional_site.log` |
| tagger | `--check` validates the table against the rules, the sources, the classes and the record; the generator over the new record is still a byte-for-byte no-op | inside `logs/notional_protected.log` §7 |

The suite ran once and passed once; no gate was moved, no threshold retuned, and no test deleted.

**The record**, written through `framework_writeback.save`, the single writer:

| event | time | nodes changed | framework sha256 |
|---|---|---|---|
| `fa3d9baf4b834f4cb5312df0d7106199` | 2026-09-17T22:32:27Z | 45 | `f32b2b08…e95427` |

On `events/batch-033_framework.jsonl`, appending exactly one line. `nodes_added {}`, `nodes_removed {}`, `edges_changed 0`, `counts_moved {}`.

**Write set as committed:**
- the record: `framework/ai_readiness_framework.json`, plus the event above;
- code: `scripts/tag_prescriptions.py` (the classes, the band table, `BAND_NOTE`, the class gate in `validate`, the split of `TASK` and `WRITEBACK_TASK`), `scripts/prescriptions.py` (`--bands`, the header marker, the note printed once);
- the catalogue: `kg/schema.yaml` (§3 premise 2);
- checks: `scripts/check_protected_notional_bands.sh` (new);
- tests: `tests/test_prescriptions.py` (five tests replaced, six added);
- the DN-005 addendum: `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_03.md` (new);
- published: `docs/data/ai_readiness_framework.json`, `docs/data/index.json`;
- `seldon_events.jsonl`;
- this RESULT.

Nothing under `state/`, `corpus/`, `assessment/`, `docs/reports/`, `docs/research/` or `docs/crosswalk/` moved. No cycle ran, no Result was registered, no matrix, figure or report was rebuilt, and no action, rule or edge was added.

## 5. What the next task starts from

1. **`cc_tasks/2026-09-17_mcp_over_the_graph.md` is now unblocked on its stated condition** — no prescriptions tool can print a pending band, because none exists. What it will print instead is a word with a `(notional)` marker and one sentence of context, and the MCP tool has to carry that sentence out with the number or it hands a consumer an unqualified estimate. That is the one thing to check in its RESULT.
2. **The bands are refined by evidence, never by further estimation** (ADDENDUM_03 §6). A publisher who closes one of these actions and records what it took converts a notional band into a sourced one, and the test in place already admits a document locator beside the marker without a change. Nothing else should move a band.
3. **`cost_band: tooling` is unreached.** Whether that means the value is wrong or the classes are incomplete is answerable only when an action needs it; it is recorded here so the next reader of the cost bands does not silently conclude there are three.
