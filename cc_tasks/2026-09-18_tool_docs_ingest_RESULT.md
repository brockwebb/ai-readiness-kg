# RESULT: both tool documents fetched and admitted; A7, F2 and F3 take tier O on a cited section of each

**Task:** `cc_tasks/2026-09-18_tool_docs_ingest.md`. I globbed `2026-09-18_tool_docs_ingest_ADDENDUM*.md` before starting and again before §3. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher from HEAD `8e74f7f`, with `SELDON_NETWORK_ALLOWLIST=raw.githubusercontent.com,github.com,archive.org`.
**Framework layer served:** DN-005 §2.2 (tier O requires the tool's documentation on disk).
**Spend:** zero model calls. **Network:** 12 requests, all through `scripts/fetch_allowlisted.py`, all to the three declared hosts, none refused (§0).
**Gate:** green, with every command run to its `EXIT=` line before this file was written.
- `make gate-full` (the full tier, `-rs`): **2458 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`, wall-clock 1378.35 s. The first full run failed; the section below says on what, and why nothing shipped from it.
- `seldon verify`: all checks passed, `EXIT=0`.
- `scripts/check_protected_tool_docs.sh`: `PROTECTED PATHS OK`, `EXIT=0`.
The log paths are in §5.

**In one paragraph.** Two documents were fetched and admitted as epoch `tool-docs-2026-09-18`: `oasdiff`'s README (`oasdiff-readme`, 7,722 B) and the Wayback CDX Server API README (`wayback-cdx-server-api-readme`, 18,292 B). Both passed the sweep as `included` and `verified`. The Internet Archive's own API page answered 404 and is logged, not admitted. For each of A7, F2 and F3, a section of the admitted document reaches the indicator's spec, so all three are now `measurement_tier: O`, basis `open_tool`, with the locator in `tier_source`, and `open_tool_candidate` is gone from the record. The totals moved from 34 M / 2 O / 5 D / 8 unassigned to **34 M / 5 O / 5 D / 5 unassigned**. Nothing was measured: no archive query, no diff run.

## 0. The fetch log, whole

`logs/2026-09-18_tool_docs_ingest_fetch.jsonl`, 12 lines, one per request the client sent. Every line is `event: request` and `method: GET`. The log has no `refused` or `error` lines.

| # | ts (UTC) | URL | status | bytes | sha256 | robots verdict |
|---|---|---|---|---|---|---|
| 1 | 03:55:58.972 | https://raw.githubusercontent.com/robots.txt | 404 | 14 | `d5558cd4…3512ed` | robots read (bootstrap) |
| 2 | 03:55:59.937 | https://raw.githubusercontent.com/oasdiff/oasdiff/main/README.md | 404 | 14 | `d5558cd4…3512ed` | allowed (no directives) |
| 3 | 03:56:00.305 | https://raw.githubusercontent.com/robots.txt | 404 | 14 | `d5558cd4…3512ed` | robots read (bootstrap; new process) |
| 4 | 03:56:01.451 | https://raw.githubusercontent.com/internetarchive/wayback/master/wayback-cdx-server/README.md | **200** | 18292 | `e17a0e1f43c4dd887adbb1473a7be452bbc12f823b64ea3fda2105c8d27ee7dd` | allowed (no directives) |
| 5 | 03:56:02.042 | https://archive.org/robots.txt | 200 | 238 | `83e00f46…6c6161` | robots read (bootstrap) |
| 6 | 03:56:02.978 | https://archive.org/developers/wayback-cdx-server.html | 404 | 146 | `55f7d9e9…87e3e0` | allowed by archive.org's robots.txt |
| 7 | 03:56:12.800 | https://raw.githubusercontent.com/robots.txt | 404 | 14 | `d5558cd4…3512ed` | robots read (bootstrap; new process) |
| 8 | 03:56:13.941 | https://raw.githubusercontent.com/oasdiff/oasdiff/HEAD/README.md | 404 | 14 | `d5558cd4…3512ed` | allowed (no directives) |
| 9 | 03:56:20.051 | https://github.com/robots.txt | 200 | 5317 | `2bae6090…b711d` | robots read (bootstrap) |
| 10 | 03:56:21.705 | https://github.com/oasdiff/oasdiff | 200 | 377167 | `f2de5108…73ee1` | allowed by github.com's robots.txt |
| 11 | 03:56:35.182 | https://raw.githubusercontent.com/robots.txt | 404 | 14 | `d5558cd4…3512ed` | robots read (bootstrap; new process) |
| 12 | 03:56:36.282 | https://raw.githubusercontent.com/oasdiff/oasdiff/main/docs/README.md | **200** | 7722 | `9ec7fc519ccca54867f545950bf1e2744223ea6a2bdd7b1ff860deeefe59cfbb` | allowed (no directives) |

**How the robots column is derived.** The helper logs each request, not the verdict drawn from it. The verdict follows from the code path. `Fetcher.raw_get` calls `_gate` before sending, and `_gate` raises `RobotsDisallowed` rather than return, so every non-robots request in the log is one the Fetcher allowed. On raw.githubusercontent.com, `/robots.txt` answers 404 with the body `404: Not Found`. The Fetcher does not check that status: it parses the body as robots text, which yields no directives, and so it allows everything. That matches RFC 9309 §2.3.1.3 ("unavailable", 4xx: the crawler may access any resources), but it gets there by accident rather than by rule; see §4 item 7.

**Rows 2, 8 and 10 are resolution, not retries.** Row 2 was the task's "raw URL for its default branch" with the branch *guessed* as `main`. Row 8 asked raw for `HEAD`, which the host resolves to the default branch; it also answered 404. So the README was not at the repository root. Row 10 fetched the landing page on `github.com`, which is on the allowlist. It was stored under `logs/tool_docs_resolve/`, outside the corpus, and is not admitted. The page gives `defaultBranch: "main"`, `currentOid: 322d7ae815e5fb80f415bd4e8ef16d4b30cd8bdf`, and a file tree whose only README is `docs/README.md` (GitHub renders that as the repository's README). Row 12 is that file. No URL was requested twice.

**The commit the raw fetch served.** The raw response does not name one: raw.githubusercontent.com returns no commit header, and the helper logs only `content_type`. The best available record is the landing page 15 s earlier, which put `main` at `322d7ae8…cd8bdf`. For the Wayback README, no commit was recorded: the only request to that repository was the raw fetch.

**Row 6: the Internet Archive's own API page.** The task allowed one attempt, "if one is served on `archive.org`". It is not served at that URL. The attempt is a logged fact, and no other URL was tried.

## 1. Ledger entries and epoch

Written by `scripts/admit_tool_docs.py` (new), which follows the path of `admit_esip_checklist.py`. Dry run first (`logs/tool_docs_admit_dryrun.log`, `EXIT=0`), then the live run (`logs/tool_docs_admit_live.log`, `EXIT=0`). The config change is `dixie_evidence.yaml` `document_dirs` += `tools`, with this task's citation, and nothing else in that file moved.

`corpus/evidence/decisions.jsonl` gained 9 lines, appended:

| event | subject | detail |
|---|---|---|
| `screening_imported` | `oasdiff-readme` | `source_id: tool_docs_2026-09-18`, `doc_type: industry`, `pub_year: n.d.`, `acquisition_method: scripted_fetch`, `acquired_by: scripts/fetch_allowlisted.py`, `expected_sha256: 9ec7fc51…`, `local_path: corpus/tools/oasdiff/README.md` |
| `screening_imported` | `wayback-cdx-server-api-readme` | same shape; `authors_or_org: Internet Archive`, `expected_sha256: e17a0e1f…`, `local_path: corpus/tools/wayback-cdx-server/README.md` |
| `file_observed` + `integrity_checked` | `corpus/tools/oasdiff/README.md` | `pass` |
| `file_observed` + `integrity_checked` | `corpus/tools/wayback-cdx-server/README.md` | `pass` |
| `file_observed` + `integrity_checked` | `corpus/noaa_esip/NAO_216-128.ocr.json` | `pass`, sha `acffd551…`; see §4 item 6 |
| `corpus_epoch_declared` | `tool-docs-2026-09-18` | members `oasdiff-readme`, `wayback-cdx-server-api-readme`; `task: cc_tasks/2026-09-18_tool_docs_ingest.md`; the note records the archive.org 404 |

`manifest.rebuild()` went from 377 to **379** entries (`included` 263). The two new entries are `included` and `verified`. The only existing entry that moved is `nao-216-128-artificial-intelligence-in-noaa`, and only its `extra.observed_files` / `integrity_by_file` for the OCR sidecar. The script and `scripts/check_protected_tool_docs.sh` §4 both assert this. No `manifest_add` event was written: these are reference documents for tiering, not extraction inputs, and the event stream is the extraction-admission gate (CLAUDE.md invariant 2).

## 2. The three rows

Each row was written by `scripts/tag_measurement_tiers.py` (`TABLE3`, rule text `cc_tasks/2026-09-18_tool_docs_ingest.md decision 2`) through `framework_writeback.save`. That is one `framework_writeback` event, `4a38c203cde545ba90a8dbf723193399`, on `events/batch-033_framework.jsonl`: 3 nodes changed, framework sha256 `0cbaa670…4606f55`, no node, edge or `counts` key added or dropped. The tagger checks every quote as a verbatim substring of the definition before it writes. A second run returns `unchanged: true`.

| code | tier / basis | the definition clause it reaches | locator (`tier_source`, abridged) | what the document does NOT reach (`tier_note`) |
|---|---|---|---|---|
| **A7** | O / open_tool | "Persistent URLs/DOIs for products and vintages" | `corpus/tools/wayback-cdx-server/README.md` (doc_id `wayback-cdx-server-api-readme`), 'Basic Usage': "the only required param for the CDX server is the **url** param", one row per capture with `urlkey, timestamp, original, mimetype, statuscode, digest, length`; 'Filtering': "**from=** and **to=**" and "**filter=**[!]*field*:*regex*", "often useful to filter by … *statuscode*" | The DOI half. A DOI's persistence belongs to its resolver, not the archive, so a rule built on this document records that clause as unmeasured unless it also reads the resolver. The predecessor's M candidate (`probes/d1_stable_urls.py`) stands beside this one. |
| **F2** | O / open_tool | "compatibility checked mechanically" | `corpus/tools/oasdiff/README.md` (doc_id `oasdiff-readme`): "Command-line tool to compare and detect breaking changes in OpenAPI specs"; "`breaking` — only the changes that break existing API clients"; 'API lifecycle': "Deprecate APIs and parameters", "Version bumps — report a breaking change released without a major version bump" | Only APIs that publish an OpenAPI description are reachable. The deprecation-window and version-bump detail is in the linked `DEPRECATION.md` and `VERSIONING.md`, which were not fetched. `spec:F2`'s two-release requirement still holds. |
| **F3** | O / open_tool | "endpoints survive a new vintage" | the same CDX README, 'Url Match Scope': "**matchType=prefix** will return results for all results under the path", with **from=**/**to=** and 'Collapsing' "Only show unique urls in a prefix query" (`collapse=urlkey&matchType=prefix`): the endpoints captured under a product's path in the prior vintage's date range | Series identifiers and geography codes live in response bodies, which the index locates (timestamp, URL, digest) but does not carry, so they are unmeasured from this document alone. The published-crosswalk alternative is a separate observation. `spec:F3`'s two-vintage requirement holds. |

All three notes add that no harness path runs the tool under this project's manners, evidence retention and re-derivation discipline. That is what keeps them O rather than M (DN-005 §2.2), the same distinction C5 carries. `open_tool_candidate` was removed from all three; `OPEN_TOOL_CANDIDATE` in the tagger is now empty, and `tests/test_measurement_tiers.py::test_the_shopping_list_sits_only_on_untiered_rows` still holds any future entry to an untiered row.

**Decision 3's regenerations:**
- the tool map (`docs/design/scan_tool_map.md`, `logs/tool_docs_tool_map.log`): exactly the six A7/F2/F3 rows moved, in §2 and §4;
- the site (`build_l0_site.py --only sources_per_check --only framework_copy --only corpus_copy --only data_manifest`, `logs/tool_docs_site.log`): the framework copy, the corpus manifest copy, `index.json` and the citation files moved, and `sources_per_check.json` did not;
- the framework projection (`scripts/load_framework_graph.py`, `logs/tool_docs_projection.log`);
- the MCP page (`mcp/airkg_doc.py`, `logs/tool_docs_mcp_doc.log`): only the distribution lines moved.

## 3. Tier counts

| tier | before | after | | basis | before | after |
|---|---|---|---|---|---|---|
| M | 34 | 34 | | harness_leg | 17 | 17 |
| O | 2 | **5** | | structured_field | 7 | 7 |
| D | 5 | 5 | | judged_reading | 2 | 2 |
| unassigned | 8 | **5** | | evaluation | 8 | 8 |
| **total** | **49** | **49** | | open_tool | 2 | **5** |
| | | | | declaration | 5 | 5 |

Live Cypher after projection (`logs/tool_docs_cypher.log`):
- `D declaration 5 [E2 E4 E7 F1 F5]`
- `M evaluation 8 [C1 C2 C3 C4 E6 E8 E9 G2]`
- `M harness_leg 17 [A1 A10 A11 A12 A2 A3 A4 A5 A6 A8 A9 B3 D1 D4 E5 F4 G1-D]`
- `M judged_reading 2 [G1-O G6]`
- `M structured_field 7 [B1 B2 B4 B5 D2 D3 G4]`
- `O open_tool 5 [A7 C5 F2 F3 F6]`
- `— — 5 [B6 E1 E3 G3 G5]`
- `open_tool_candidate: []`

Sources that are `estimate`: 0. `tests/test_measurement_tiers.py` checks both new `doc_id`s against the corpus manifest: each must be `included` at the path the source prints. It asserts the distribution as a literal, against the record and against the graph, and `tests/test_mcp_server.py` asserts it against the MCP server's overview.

## 4. Premises this task file got wrong

1. **"the project README at `github.com/oasdiff/oasdiff`, via the raw URL for its default branch".** The repository has no root README. Its README is `docs/README.md`, and the root path answered 404 on both `main` and `HEAD` (§0 rows 2, 8). The landing page settled the question, and it was fetched from a declared host through the same helper.
2. **"the Internet Archive's own API page if one is served on `archive.org`".** The page is not served at `archive.org/developers/wayback-cdx-server.html` (404, row 6). One document was admitted for the CDX API, and the failure is logged, as the task allowed.
3. **Decision 1's `doc_type: reference`.** `reference` is not a value of `Document.source_type` in `kg/schema.yaml` (`federal, academic, industry, standard, intergovernmental, practitioner`), and the type catalogue changes only through its review (invariant 4). The one tool README already in the ledger, `extruct-readme`, is `industry`. Both admissions follow that precedent, and the script's docstring says so.
4. **The write set omits `scripts/build_l0_site.py` and `docs/data/corpus_manifest.json`.** No `--only` flag wrote the site's copy of the corpus manifest: this is the first narrow site build to follow a corpus admission. `--only data_manifest` recorded the new manifest's digest over a copy that still held the old one, and `tests/test_publication.py::test_every_copy_still_equals_the_record_it_was_copied_from` failed on it. I confirmed that failure before fixing it. The fix inserts one `_ONLY` key, `corpus_copy`, and removes nothing; `scripts/check_protected_tool_docs.sh` §9 asserts that.
5. **The write set omits `tests/test_mcp_server.py` and `docs/design/mcp_over_the_graph.md`.** Both hold the tier distribution: a literal in `test_overview_counts_indicators_by_tier_and_basis_from_the_record`, and a page generated by running the tools. The first full-suite run failed on exactly these two (see §5). The literal was updated to 34/5/5/5, and the page was regenerated, moving only on its distribution lines.
6. **Unnamed by the task: the sweep re-observed `corpus/noaa_esip/NAO_216-128.ocr.json`.** The committed bytes (2,508 B, sha `acffd551…`) are not the bytes swept on 2026-09-10 (1,850 B, sha `c8895da0…`). The sidecar changed after that sweep and before or at commit `8ac6445`, and no sweep had run since. The designed path picked it up, and it passes integrity. It is recorded here and asserted in the protected-paths check rather than reconciled silently. Also outside the write set, the citation files (`CITATION.cff`, `.zenodo.json` and their `docs/data/` twins) moved on `date-released` / `publication_date` only, because the build ran on a new UTC day and `_ONLY["data_manifest"]` carries them.
7. **Not a premise, an observation for a later task.** `scan.manners.Fetcher._robots_for` parses a robots.txt body without checking the status. On raw.githubusercontent.com that meant parsing `404: Not Found` as robots text. The result, allow, is the one RFC 9309 §2.3.1.3 prescribes for 4xx, but a 5xx whose body happened to be empty would also yield allow, where the RFC prescribes complete disallow ("unreachable"). This task did not touch `assessment/`.

## 5. Gate

**Tier:** `make gate-full`, the whole suite with `-rs`, detached and polled to its `EXIT=` line inside this turn. It is not the fast tier. No rule module, registry entry or re-derivation engine moved, so `gate-task` adds nothing the full run does not already include.

| check | result | log |
|---|---|---|
| `make gate-full` (run 2, shipped) | **2458 passed, 3 skipped, 12 xfailed, 0 deselected**, 248 warnings, 1378.35 s, `EXIT=0` | `logs/tool_docs_suite.log` (copy of `logs/suite.log`) |
| skips (3, as the task expected) | `tests/test_dispatch_config.py:333` (interactive_only: dispatched session); `tests/test_scan_harness.py:281` (E5 judges the cycle's controls); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | same |
| `make gate-full` (run 1, not shipped) | 2 failed, 2456 passed, 3 skipped, 12 xfailed, 1376.80 s, `EXIT=1`, on the two MCP views of the distribution (§4 item 5) | `logs/tool_docs_suite_run1_failed.log` |
| `seldon verify` | all checks passed (34904 events readable; replay skipped by default as expensive), `EXIT=0` | `logs/tool_docs_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` (`scripts/check_protected_tool_docs.sh`: `state/`, `docs/reports/`, `docs/research/`, `kg/`, `assessment/` untouched; record moved only on A7/F2/F3 tier keys; manifest +2; copies byte-equal; append-only logs, +1 framework event, +9 ledger lines) | `logs/tool_docs_protected.log` |
| projection round-trip | `scripts/load_framework_graph.py` `EXIT=0`; `tests/test_framework_projection_roundtrip.py` green inside the suite | `logs/tool_docs_projection.log` |
| fetch | 12 requests, 0 refused, 0 errors | `logs/2026-09-18_tool_docs_ingest_fetch.jsonl` |
| admission | dry run then live, both `EXIT=0` | `logs/tool_docs_admit_dryrun.log`, `logs/tool_docs_admit_live.log` |
| tagger | `EXIT=0`; the second run is `unchanged: true` | `logs/tool_docs_tagger.log`, `logs/tool_docs_tagger_dryrun.log` |

The first run failed on views the task file did not name. Nothing shipped from it. The literal and the page were corrected, the affected modules re-run (160 passed), and then the whole suite was run again from scratch. Both runs are reported, because a pass reached by changing the work after a failure is only credible if the failure is on the record too.

**Write set as committed:**
- corpus: `corpus/tools/oasdiff/README.md`, `corpus/tools/wayback-cdx-server/README.md` (new), `dixie_evidence.yaml`, `corpus/evidence/decisions.jsonl` (append), `corpus/manifest.json` (rebuilt);
- the record: `framework/ai_readiness_framework.json`, plus the one event on `events/batch-033_framework.jsonl`;
- code: `scripts/admit_tool_docs.py` (new), `scripts/tag_measurement_tiers.py` (`TASK3`, `TABLE3`), `scripts/build_l0_site.py` (§4 item 4);
- checks and tests: `scripts/check_protected_tool_docs.sh` (new), `tests/test_measurement_tiers.py`, `tests/test_mcp_server.py`;
- regenerated: `docs/design/scan_tool_map.md`, `docs/design/mcp_over_the_graph.md`, `docs/data/ai_readiness_framework.json`, `docs/data/corpus_manifest.json`, `docs/data/index.json`, `docs/data/CITATION.cff`, `docs/data/zenodo.json`, `CITATION.cff`, `.zenodo.json`;
- `seldon_events.jsonl`, and this RESULT.

## 6. What the next task starts from

- **Five rows remain unassigned, and none is waiting on a document.** B6, E1 and E3 need an instrument that reads a published text or report. G3 needs an SDMX collector. G5 has no admitted document that names its field. The open-tool shopping list is empty.
- **The five O rows are the input to a harness decision.** A7 and F3 share one tool, the CDX API, and one act: a dated query over a URL or a prefix. A single collector wired under this project's manners would move both toward M. F2 needs two dated OpenAPI descriptions, which the scan does not yet retain.
- **`Fetcher._robots_for` ignores the robots.txt status** (§4 item 7). The fix is one check against RFC 9309 §2.3.1.3–4, but it lives in `assessment/harness/scan/manners.py`, which is under the re-derivation gate.
