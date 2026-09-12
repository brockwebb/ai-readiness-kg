# RESULT — A1, A8, B3 and D4 get their sources: every check the report quotes is now cited

**Task:** `cc_tasks/2026-09-12_a1_a8_b3_d4_sources.md`. No addendum exists; globbed before starting
and again before §3, both times empty.
**Date:** 2026-09-12 UTC. **Spend:** zero model calls.
**Network: NONE.** Not "one acquisition" — zero. Decision 4's acquisition was not taken, because
its own condition was not met (§3). No HTTP request of any kind was issued in this session; the
only socket opened was the local Neo4j bolt connection. `corpus/` is byte-identical to HEAD, which
is how that claim is checkable (`scripts/check_protected_a1a8b3d4.sh`).
**Gate (§3): PASS.** Every command in §7 ran to `EXIT=0` before this file was written.

---

## 1. The twelve-leg table, after

| leg | indicator | → construct | → definitions | → **source documents** | spec | rules |
|---|---|---|---|---|---|---|
| A4 | `A4` | 1 | 29 | 6 | 1 | 1 |
| A5 | `A5` | 1 | 29 | 2 | 1 | 2 |
| A10 | `A10` | 1 | 39 | 2 | 1 | 3 |
| A11-declared | `A11` | 1 | 13 | 2 | 1 | 2 |
| A12 | `A12` | 1 | 13 | 2 | 1 | 1 |
| G1-D | `G1-D` | 1 | 364 | 40 | 1 | 1 |
| A3 | `A3` | 1 | 52 | 3 | 1 | 4 |
| **A1** | `A1` | 1 | **51** (was 0) | **3** (was 0) | 1 | 4 |
| A6 | `A6` | 1 | 152 | 4 | 1 | 2 |
| **A8** | `A8` | 1 | **46** (was 0) | **3** (was 0) | 1 | 4 |
| **B3** | `B3` | 1 | **37** (was 0) | **3** (was 0) | 1 | 2 |
| **D4** | `D4` | 1 | **50** (was 0) | **3** (was 0) | 1 | 2 |

All twelve reach at least one source; the four this task cited reach three each. **`legs_without_
source` is now empty** — the appendix has no "no admitted source" row left to print. The definition
counts went 0 → 37..51 for the four, because the chain continues through the documents to the
`Definition` nodes already extracted from them.

## 2. The gate — §3, clause by clause

| clause | result |
|---|---|
| Traceability test green over twelve legs with the stated floors | **PASS** — `tests/test_report_traceability.py`, 47 cases. `RT.LEGS` is twelve and is READ from the sections, not typed |
| Every appendix row's doc_id in the manifest | **PASS** — `doc_ids_not_in_manifest: []`; the fragment writer refuses otherwise |
| A1, A8, D4 ≥ 1 source each | **PASS** — three each (§1) |
| B3 ≥ 1 **or** a named allowance with the reading recorded | **PASS on the first branch** — three sources (§4). The allowance mechanism exists and is EMPTY: `ALLOW_ZERO_SOURCES = {}` |
| Write-back events carry deltas with 0 removals | **PASS** — two events, `edges_removed: {}` and `nodes_removed: {}` on both (§5) |
| Projection round-trip green | **PASS** — `tests/test_framework_projection_roundtrip.py`, 7 passed; loader reports `evidenced_by_missing_document: 0` |
| Tag-coverage lint and PDF numeral-multiset gate green | **PASS** — `bare_numerals_in_prose: []`, `missing_fragments: []`, `gate: PASS`, `test_report_pdf` 2 passed |
| `test_report_text_and_figures_agree_per_leg` green | **PASS** |
| Embedded F5 unchanged | **PASS** — `assessment/harness/scan/figures/` byte-identical to HEAD (protected whole) |
| Socket counter shows at most the one acquisition host | **PASS, vacuously and better** — zero non-loopback sockets. No host was contacted, no federal host in the frame included |
| `make gate-task` | **PASS** — 1,975 passed, 17 skipped, 19 deselected, 12 xfailed, 360.7 s; then 16 of 16 payloads re-derive, 5.9 s |
| `make guards` | **PASS** — 25 passed, 15.7 s |
| `make gate-full` | **PASS** — 1,994 passed, 17 skipped, 12 xfailed, 1,245.1 s, detached and polled to EXIT |
| `seldon verify` | **PASS** — all checks passed |
| Protected paths | **PASS** — `scripts/check_protected_a1a8b3d4.sh` |

## 3. Decision 4 — M-13-13 was NOT acquired, and the reason is on the document's face

Decision 4 permits exactly one acquisition, **and only if `dcat-us-1-1-schema` on reading does not
itself state the Public Data Listing requirement.** It does state it, in three places read this
session from `corpus/kernel/dcat-us-1-1-schema.md`:

* the Introduction: *"guidance to support the use of the Project Open Data metadata to list agency
  datasets and application programming interfaces (APIs) as hosted at agency.gov/data"*;
* What to Document: *"The catalog file for each agency should list all of the agency's datasets
  that can be made public, regardless of whether they are distributed by a file download or a Web
  API"*;
* Catalog Fields: *"These fields describe the entire Public Data Listing catalog file."*

So the condition fails and **the memorandum is not acquired.** The corpus-first search then did
better than the substitution the task contemplated: it already holds the **statute** and the
**current** OMB guidance, both of which post-date and outrank a 2013 memorandum for this check —

* `foundations-for-evidence-based-policymaking-act-of-2018-evid` — Title II, the OPEN Government
  Data Act, enacting 44 U.S.C. 3511;
* `m-25-05-phase-2-implementation-of-the-evidence-act-open-gove` — the Phase 2 Evidence Act
  guidance, which is what actually tells an agency to post `data.json`.

Both were already admitted, integrity-verified, with `:Document` nodes carrying 24 and 13 extracted
definitions. **Nothing had to be fetched for any of the four legs.**

## 4. The citations, verified from the documents rather than from their titles

Every string below was read out of the file in this session — `corpus/kernel/*.md` by grep,
`corpus/bulk/*.pdf` and `corpus/kernel/omb-m-23-22-*.pdf` through `pypdf`. The locators are in the
skeleton's Evidence cells and render into the appendix.

**A1 — structured data, not PDF-only.** Indicator: *"Product available as structured data
(CSV/JSON/parquet), not PDF-only."*

* `w3c-dwbp-2017` — **BP 12, Use machine-readable standardized data formats**: *"Make data available
  in a machine-readable, standardized data format that is well suited to its intended or potential
  use"*, implemented as *"CSV, XML, HDF5, JSON and RDF serialization syntaxes"*, and **How to Test**:
  *"Check if the data format conforms to a known machine-readable data format specification"* — which
  is A1's check, stated by the standard as a test. Plus **BP 14, Provide data in multiple formats**,
  the not-PDF-only half.
* `foundations-for-evidence-based-policymaking-act-of-2018-evid` — 44 U.S.C. 3502(18), the statutory
  definition: machine-readable is *"data in a format that can be easily processed by a computer
  without human intervention while ensuring no semantic meaning is lost"*; 3502(20) requires an open
  Government data asset to be machine-readable and available in an open format.
* `m-25-05-…` — Section 5, *"i. Machine-Readable. Agencies must make each of their public data assets
  machine-readable"*, with the worked example that tabular data *"should not provide this data as a
  scanned image or image-based PDF document, but rather should provide that public data asset in an
  appropriate format (e.g., in a character-delimited format such as a CSV file)"*. That sentence is
  A1's indicator in federal policy prose.

**A8 — release date machine-readable, latest-vintage pointer resolvable.**

* `w3c-dwbp-2017` — **BP 7, Provide a version indicator**: *"Assign and indicate a version number or
  date for each dataset"*; intended outcome *"Humans and software agents will easily be able to
  determine which version of a dataset they are working with"*; and the implementation note that is
  exactly the vintage-pointer half: *"the URI used to request the latest version of the data should
  not change as the versions change"*. Plus **BP 21, Provide data up to date**: *"Make data available
  in an up-to-date manner, and make the update frequency explicit."*
* `dcat-us-1-1-schema` — the **modified** field, Required *"Yes, always"*: *"Most recent date on which
  the dataset was changed, updated or modified"*, ISO 8601; and **accrualPeriodicity**, the publishing
  frequency as an ISO 8601 repeating duration.
* `omb-m-23-22-digital-first-public-experience` — **Indicate timeliness of content**: agencies
  *"should indicate when content on static, public-facing websites was created or last updated by
  including temporal information in line with content or by using 'Last Modified' in the HTTP header,
  in metadata tags, or in XML sitemaps"* — the machine-readable surface a scanner actually reads.

**B3 — methodology in structured text, served without script execution.** The rule is
`RULE-B3-v3`, whose parameter block is `b3_without_js` and whose candidates are the methodology
documents appended after the product page; it fails a candidate that is thin, PDF-only or
JavaScript-dependent. The cell cites both halves separately:

* `omb-m-23-22-digital-first-public-experience` — **Default to HTML**: agencies *"should default to
  creating and publishing content in an HTML format in lieu of publishing content in other electronic
  document formats that are designed for printing or preserving and protecting the content and layout
  of the document (e.g., PDF and DOCX formats)"*, and *"An agency should develop online content in a
  non-HTML format only if necessitated by a specific user need."* That is the structured-text,
  not-PDF-only half, in federal policy.
* `bing-webmaster-guidelines` — **Section 8, Allow Efficient Crawling and Rendering**, which lists
  *"Hiding critical content behind client-side rendering"* among the things to avoid and states
  *"Content that cannot be reliably rendered may not be indexed or selected for grounding results."*
  That is the served-without-script-execution half, and it is the only statement of it found in the
  corpus (§4a).
* `w3c-dwbp-2017` — **BP 5, Provide data provenance information** (intended outcome: *"software
  agents will be able to automatically process provenance information"*) and **BP 6, Provide data
  quality information** (*"Humans and software agents will be able to assess the quality and therefore
  suitability of a dataset for their application"*) — why a methodology statement has to be
  machine-processable rather than merely published.

**D4 — statutory products enumerable from a public inventory.**

* `foundations-for-evidence-based-policymaking-act-of-2018-evid` — 44 U.S.C. 3511(a)(1): each agency
  shall *"develop and maintain a comprehensive data inventory that accounts for all data assets
  created by, collected by, under the control or direction of, or maintained by the agency"*;
  (a)(3) updates *"not later than 90 days"* after creation or identification; (b) public data assets
  submitted *"for inclusion in the Federal data catalogue"*; (c)(1) that catalogue is *"a single
  public interface online as a point of entry"*. The indicator says *statutory* products; this is the
  statute.
* `m-25-05-…` — Section 4(a)(iii), Public Dissemination: agencies *"must submit their comprehensive
  data inventory to the Federal Data Catalog as a data asset"* and *"host it publicly on the agency's
  website at the address: www.[agency].gov/data.json"*, repeated at Section 5(b)(ii) with the
  OMB-approved metadata schema. This is the address a scanner checks.
* `dcat-us-1-1-schema` — that schema, quoted in §3.

### 4a. What was read and rejected, and why

The BP-10 discipline (`2026-09-11_a3_a10_sources_RESULT.md` §4) applied four more times:

1. **`schema-org-dataset` for A1 — rejected.** The task's prior-art list names it. Read: its
   `distribution` is *"A downloadable form of this dataset, at a specific location, in a specific
   format"* and `encodingFormat` is *"Media type typically expressed using a MIME format"*. That is
   vocabulary for DESCRIBING whatever form exists; it imposes no requirement that the product be
   offered as structured data rather than as a document. It is A6's markup source and it is not an A1
   requirement source.
2. **FAIR R1.2 for A8 — rejected.** The task names it. Read from the PDF: *"R1.2. (meta)data are
   associated with detailed provenance."* Provenance is not a release date and not a latest-vintage
   pointer. DWBP BP 7 says the thing FAIR does not.
3. **The four admitted crawler documents for B3 — read, and they do not say it.** The task
   anticipated this. `openai-crawlers-bots`, `anthropic-crawler-support-article`,
   `perplexity-crawlers` and `cloudflare-ai-crawl-control-manage-crawlers` were grepped for
   javascript / render / client-side / script: **anthropic and cloudflare return no hit at all;
   openai's only hits are transcription-API links and a user-agent table header; perplexity's is a
   table header.** None of the four states whether the crawler executes scripts. What closed B3 was
   `bing-webmaster-guidelines`, found by grepping the whole corpus for the claim rather than the
   document — one hit, and it is on point.
4. **M-23-22's "Default to static websites" for B3's JS half — read and NOT cited for it.** It says
   static architectures serve files *"rather than dynamically executing code to assemble content on a
   web request"* and *"do not execute server-side code"*. That is SERVER-side execution; B3 measures
   whether a browser must run client-side script. Citing it for that half would have been the BP-10
   error in a federal document. It is cited for the not-PDF-only half only, which it does state.
   Also read and not cited: `gsa-site-scanning-engine-readme` (the federal scanner uses *"Headless
   Chrome, powered by Puppeteer"* — it executes JS, so it is evidence against the claim, not for it);
   `google-crawling-indexing-overview` (a navigation page whose body is link text, no substantive
   statement); `google-ai-features-and-your-website` (no statement about script execution);
   `fcsm-25-03` (metadata and APIs, nothing on methodology-document form).

## 5. The write-backs, and the latent gap this task found in the write-back path

**Two `framework_writeback` events, both in `events/batch-033_framework.jsonl`, both with zero
removals.**

| # | event_id | what moved |
|---|---|---|
| 1 | `7241d044e8de49d08de451adbf7ab7fb` | 12 `EVIDENCED_BY` edges added, 0 removed, 4 nodes changed; `evidenced_by` 127 → 139, `gaps` 18 → 14; sha256 `ee83d21d…` |
| 2 | `946ad078bec2431ba752caf6e5292cde` | 0 nodes, 0 edges, 0 counts moved — the top-level `evidence_doc_ids_not_in_manifest` only; sha256 `b2d010e5…` |

**Why there are two, which is the finding.** After the first write-back,
`tests/test_framework_single_writer.py::test_regenerating_from_the_current_skeleton_over_head_is_a_no_op`
and its sibling went RED — the only two failures in the whole gate. Diffed: the record still carried
`{"indicator": "A1", "doc_id": "acquisition_blocked"}` under `evidence_doc_ids_not_in_manifest`, a
stale entry from A1's old gap text, which had the backticked slug `` `acquisition_blocked` `` in it.

That key is an **`AUTHORED_TOP`** key: `build_framework_graph.generate` derives it from the
skeleton's evidence cells and `merge` therefore takes it from the generator, never from the record.
`framework_writeback_evidence` carried the cell and left the diagnostic behind, so the record and its
own skeleton came apart — exactly what that no-op test exists to catch, and it caught it. **A3 and
A10 never exercised the path** because neither cell named an unadmitted slug; A1's did.

The fix is nine lines in `scripts/framework_writeback_evidence.py`: recompute the key from
`bfg.generate()` (the generator, not a second copy — the dedup in that list is GLOBAL across rows, so
a per-indicator patch would be right only while no slug is named twice) and put the before/after on
the event under `changes.__top_level__`. Both no-op tests are green after it, and
`render_framework.py --check` reports `explained diffs: 0 unexplained: 0 GATE PASS`.

`scripts/framework_writeback_evidence.py` also gained a `--task` flag. The event's `task` field was
hardcoded to the a3a10 task; every run after the first would have mis-attributed the write-back.

## 6. Decisions 2, 3, 5

**Decision 2 — the pin is twelve legs and is READ, not typed.** `report_traceability.LEGS` is now
`appendix_legs()`: the seven named in code (`_NAMED_IN_CODE`) plus whatever product legs the section
prose names by a `{{result:scan_l0_product_<leg>_...}}` tag. Today that is `A1, A6, A8, B3, D4`, so
twelve. The shape assertions are unchanged (≥ 1 construct, ≥ 1 spec, ≥ 1 rule, per leg) and now run
over all twelve. `MIN_SOURCES` is 2 for the six legs that have been cited deliberately (A3, A10, A1,
A8, B3, D4) and 1 for the rest. **`ALLOW_ZERO_SOURCES` is the named allowance and it is empty**, with
the reason written next to it: all four legs were cited, including B3, whose script-execution half the
task expected to have no standards-grade source. A leg added there in future has to carry a written
reason; the floor is not lowered.

The reason the list is read rather than typed is the defect itself: a seven-leg list let four checks
be published with a quoted rate and no source, and a list somebody must remember to extend is not a
pin. A leg added to the prose now lands in `LEGS` on the next run and fails
`test_the_report_measures_exactly_these_legs` until someone looks at it.

**Decision 3 — the report was rebuilt; no prose changed; page counts did not move.**
`make report-pdf` → `docs/reports/2026-09_fss_ai_readiness_L0.pdf`, 590,807 bytes, **14 pages total,
6 pages of prose** — identical to the registered `l0_report_pages_total_2026-09-11 = 14` and
`l0_report_pages_prose_2026-09-11 = 6`, verified against the graph. Decision 3 says re-register under
`_2026-09-12` names *only if they moved*; **they did not move, so nothing was registered.** The
appendix went from 65 rows across 12 checks (four of them "no admitted source") to **73 rows across
12 checks with no such row**. `docs/reports/sections/` is byte-identical to HEAD.

**Decision 5 — the metadata gaps are not this task's, and citing added three.** The appendix's
`missing_fields` now names ten doc_ids, up from seven: the newly cited
`foundations-for-evidence-based-policymaking-act-of-2018-evid` (author + year),
`m-25-05-phase-2-implementation-of-the-evidence-act-open-gove` (author + year) and
`bing-webmaster-guidelines` (year). Their manifest identity carries `(unspecified)` / `n.d.`, which
the generator omits rather than prints, so those rows render as title + URL. Both federal documents
still resolve for a stranger — govinfo `PLAW-115publ435` and the archived whitehouse.gov PDF. Nothing
was typed to fill a gap.

## 7. Verification

```
logs/a1a8b3d4_writeback_dryrun.log  dry run: 12 EVIDENCED_BY added, 0 removed,
                                    0 refused doc_ids, written: false             EXIT=0
logs/a1a8b3d4_writeback.log         write-back 1: 12 edges added, 0 removed,
                                    sha256 ee83d21d…, event 7241d044…             EXIT=0
logs/a1a8b3d4_writeback2.log        write-back 2: diagnostic key only, 0 nodes,
                                    0 edges, sha256 b2d010e5…, event 946ad078…    EXIT=0
logs/a1a8b3d4_loadframework.log     projection, evidenced_by_missing_document: 0,
                                    EVIDENCED_BY 141                              EXIT=0
logs/a1a8b3d4_loadframework2.log    projection after write-back 2, same counts    EXIT=0
logs/a1a8b3d4_report_pdf.log        make report-pdf — markdown gate PASS (bare numerals 0,
                                    missing fragments 0), 73 rows / 12 legs,
                                    legs_without_source [], doc_ids_not_in_manifest [],
                                    PDF 590,807 bytes, pages {total: 14, prose: 6},
                                    test_report_pdf 2 passed                      EXIT=0
logs/a1a8b3d4_guards.log            make guards — 25 passed, 15.7 s               EXIT=0
logs/a1a8b3d4_gate_task.log         make gate-task — 1,975 passed, 17 skipped, 19 deselected,
                                    12 xfailed, 360.7 s; then 16 of 16 payloads
                                    re-derive, 5.9 s                              EXIT=0
logs/suite.log                      make gate-full — 1,994 passed, 17 skipped, 12 xfailed,
                                    1,245.1 s, detached and polled to EXIT        EXIT=0
logs/a1a8b3d4_verify.log            seldon verify — all checks passed             EXIT=0
logs/a1a8b3d4_protected.log         scripts/check_protected_a1a8b3d4.sh — PASS    EXIT=0

tests/test_report_traceability.py       47 passed (against live Neo4j)
tests/test_report_sources_appendix.py   13 passed
tests/test_framework_single_writer.py   20 passed (2 were RED before §5's fix)
tests/test_framework_graph.py           14 passed, incl. the cell-for-cell round trip
tests/test_framework_projection_roundtrip.py  7 passed
tests/test_report_figures_agree.py::test_report_text_and_figures_agree_per_leg  passed
scripts/render_framework.py --check     explained 0, unexplained 0, GATE PASS
```

An earlier `make gate-task` was started before §5's fix and killed mid-run once the two single-writer
failures were diagnosed; it is not reported as a result. The numbers above are from the re-run after
the fix, on the tree that shipped.

changed: `docs/crosswalk/usafacts_operationalization_skeleton.md` (the four Evidence cells and
nothing else on the rows), `framework/ai_readiness_framework.json` (+12 edges, 4 nodes'
`evidence_raw`/`gap`, the stale diagnostic entry dropped), `events/batch-033_framework.jsonl` (+2),
`scripts/report_traceability.py` (LEGS read rather than typed), `scripts/framework_writeback_evidence.py`
(`--task`; the `AUTHORED_TOP` refresh), `tests/test_report_traceability.py`,
`tests/test_report_sources_appendix.py`, `docs/reports/2026-09_fss_ai_readiness_L0.md` and the PDF,
`docs/reports/generated/sources_per_check.md`.
new: `scripts/check_protected_a1a8b3d4.sh`, this RESULT.
untouched: `corpus/` entire, `state/` entire, every rule module, the harness runtime, every stored
payload, every figure, every section file, every prior RESULT, `tests/test_invariants.py`, A10's
evidence cell.

## 8. Every premise the task file got wrong

1. **"Network: none by default. Acquisition is permitted for exactly one document under decision 4"**
   — no acquisition happened, and the reason is decision 4's own condition (§3). The task treated
   "does DCAT-US state the requirement" as a live question; it states it three times in its first
   screen.
2. **"OMB M-13-13 is the mandate itself"** for D4. It is a 2013 memorandum, and the corpus already
   holds what superseded it for this check: the OPEN Government Data Act (44 U.S.C. 3511) and M-25-05,
   both admitted and extracted. The inventory mandate D4 measures is statutory, not memorandum-level.
3. **"`schema-org-dataset` (already admitted)" as an A1 candidate** — read and rejected (§4a.1). It
   describes a distribution's format; it does not require one.
4. **"FAIR R1.2 provenance" as an A8 candidate** — read and rejected (§4a.2). Provenance is not
   vintage.
5. **"B3 may have no standards-grade source"** — it has three. The half the task doubted, content
   served without script execution, is stated by `bing-webmaster-guidelines` §8. The task looked for
   it in the four AI-crawler documents, which was the wrong place: none of them mentions script
   execution at all (§4a.3). Searching the corpus for the CLAIM rather than for the expected DOCUMENT
   found it in one pass.
6. **"Zero edits to … the record beyond the four evidence cells"** could not be met exactly. The
   record also carries `evidence_doc_ids_not_in_manifest`, which the skeleton authors and the cell
   edit therefore moves; leaving it put the record out of step with its own skeleton and failed the
   no-op test (§5). The edit is a consequence of the four cells, not a fifth edit, and it is on the
   event.
7. **"`framework_writeback_evidence.py` … carries one named indicator's evidence cell across and
   touches nothing else"** (the premise inherited from the a3a10 RESULT). True for A3 and A10;
   incomplete in general, for the reason in §5. It is true now.
8. **Decision 2's "an explicit, named allowance of 0 for any leg it could not [cite]"** presumes at
   least one such leg. There is none. The allowance is implemented and empty, which is the honest
   state and not a missing feature.

## 9. What the next task needs

1. **Seven manifest entries still have no `pub_year` and three no author** (§6, decision 5), two of
   them federal documents now cited in the published PDF. The appendix renders them as title + URL.
   That is followable but it is not a citation a reviewer would accept; the fix is manifest metadata,
   not the generator.
2. **`acquisition.acquired_at` is still null for every document cited here.** The a3a10 RESULT §10
   raised it; this task cites three more documents that carry no retrieval date. A corpus whose
   provenance cannot answer "as of when" is the remaining gap in DD-001's chain.
3. **DN-001's citation floor is now met for every check the report publishes.** The next check added
   to the report's prose will fail `test_the_report_measures_exactly_these_legs` before it can be
   published uncited — which is the invariant, mechanised.
