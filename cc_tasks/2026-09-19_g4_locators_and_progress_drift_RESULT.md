# RESULT — G4's two sources get a locator, and `docs/progress/` is compared to the record it is a view of

**Task:** `cc_tasks/2026-09-19_g4_locators_and_progress_drift.md`. **No addendum exists**; globbed
before starting and again before §3, both times empty (`ls cc_tasks/2026-09-19_g4_locators_and_
progress_drift_ADDENDUM*.md` → no match).
**Date:** 2026-09-20 UTC. **Spend:** zero model calls — no `claude -p`, no `model_stub.invoke`,
nothing on `state/spend_ledger.jsonl`. **Network: NONE.** No HTTP request was issued; the only
sockets opened were the local Neo4j bolt connection (projection, report build) and `git push`.
`corpus/` is byte-identical to HEAD, which is how that claim is checkable (§7).
**Gate: PASS.** Every command in §7 ran to `EXIT=0` and its output was on disk before this file
was created. No placeholder appears below.

**The outcome in one line.** Both documents are **decision 2 outcome (b)**: each supports the
*statistical-versus-administrative provenance* clause of G4 with a pinpoint quote, and neither
supports the *issuing authority* or *statutory mandate* clauses — those say `general support; no
pinpoint` in the cell, with the search recorded here. Six verbatim spans were written and all six
ground through `kg/extraction/grounding.py`, from a test.

---

## 0. The reading, per document

The substrate read is `state/docling_md/<doc_id>.md`, the layout-aware Docling conversion of the
admitted PDF (`converted_by: docling`, `fidelity: layout_aware`, `source_sha256` matching
`corpus/bulk/<doc_id>.pdf`). **Premise correction:** the task says "the converted substrate on
disk under `corpus/`". There is none under `corpus/` for either document — `kg.ingest.gate
.substrate_path` returns `None` for both, because DD-030 delegates PDFs to the reader rather than
converting them, so `run_bulk_extraction.doc_text` reads these two through `pypdf`. The two
renderings on disk are `state/docling_md/` and pypdf-of-the-PDF, both gitignored projections of
the same sha256-verified bytes. §0.3 below is what they do to a quote.

### 0.1 `statistical-policy-working-paper-46-data-quality-assessment` — outcome (b)

*Statistical Policy Working Paper 46: Data Quality Assessment Tool for Administrative Data*
(Iwig, Berning, Marck, Prell; FCSM, February 2013). A 43-question instrument a statistical agency
and a program agency work through together before, during and after acquiring an administrative
data extract.

**Supported: the statistical-versus-administrative provenance clause.** Introduction, opening
paragraph — the distinction G4's third clause names, stated as the document's premise:

> "Unlike survey data, which are collected for statistical purposes, administrative data are
> collected as part of a program agency's routine operations."

**Adjacent, and cited as such:** the INSTITUTIONAL ENVIRONMENT dimension definition (Initial
Acquisition phase, repeated in the Repeated Acquisition phase and in Appendix A's compendium):

> "Institutional Environment refers to the credibility of the administrative agency for producing
> high quality and reliable administrative data."

That is the issuing agency's identity treated as a **quality dimension to be assessed**, not as a
field to be carried — which is the distinction the cell states, because G4 is about metadata
carried on the product.

**Not supported: issuing authority and statutory mandate.** `general support; no pinpoint`. What
was searched, over the whole 168,922-character substrate, case-insensitively:

| term | hits | what they are |
|---|---|---|
| `authorit` | 0 | — |
| `statut` | 0 | — |
| `legislat` | 3 | Q24 and its two repeats: *"legislative changes"* as a cause of program-population change over time |
| `authoriz` | 1 | the example MOU answer: PII access *"permitted only to authorized persons"* |
| `mandat` | 2 | Q27: *"what percentage of those mandated are not compliant"* — program compliance, not a collection mandate |
| `legal` | 2 | Q8 and its compendium row: *"Describe any legal, regulatory or administrative restrictions on access to the data file extract"* — restrictions on sharing, not authority to hold |
| `law`, `regulat`, `collected under`, `Title 13`, `legal basis`, `provenance`, `source of the data` | 0 | — |
| `metadata` | 5 | Q30 and its repeats: *"other metadata … such as record counts, range of values, and frequencies of responses"* |

And structurally: **Appendix B — Data Dictionary Template**, the document's own specification of
what metadata travels with the file, carries four file-level fields (`File Name`, `File Date`,
`Description`, `File Format`) and ten column-level fields (`Field Name`, `Description`, `Type`,
`Req.`, `Len`, `Format`, `Units`, `Valid Values`, `Definitions`, `Notes`). **No authority field,
no mandate field, no provenance-class field.** None of the 43 questions asks under what authority
or statutory mandate the data are held. The `EVIDENCED_BY` edge stands — the document is genuine
support for the provenance clause — so no Issue was filed; decision 2's Issue is for outcome (c),
and this is (b).

### 0.2 `fcsm-19-01-transparent-reporting-for-integrated-data-quality` — outcome (b)

*Transparent Reporting for Integrated Data Quality: Practices of Seven Federal Statistical
Agencies* (FCSM 19-01, 2019). Seven case studies plus a user survey, on how agencies document the
quality of integrated data.

**Supported: provenance carried as metadata.** §3(c), VetPop2016, **Table 3.3** (*Data quality
dimensions evaluated when constructing USVETS, VetPop and other NCVAS data*), **dimension 4,
Traceability** — a named quality dimension whose assessment criterion is a metadata criterion:

> Definition — "The extent to which data are well documented, verifiable, and easily attributed to
> a source."
> Assessment criteria — "Clarity of the description of the source of a data element in
> documentation including metadata information."

**Supported: the survey-versus-administrative distinction the clause rests on.** §1 Introduction,
*Types of Data*:

> "Government program agencies create administrative data as part of their daily operations."

**Statutory mandate — recorded as one agency's practice, nowhere prescribed.** §5, SESTAT, under
the recurring case-study heading *The statistical product and its data sources*:

> "NSF has a continuing mandate most recently expressed in the America COMPETES Reauthorization
> Act of 2010"

This is the report *observing* that NCSES's product documentation states its statutory mandate. It
is not a reporting element the report asks agencies to carry, so the cell says exactly that rather
than citing it as a requirement.

**Not supported: issuing authority as carried metadata.** `general support; no pinpoint`. The
report's quality framework is eight dimensions — *relevance, accuracy, reliability, timeliness,
punctuality, consistency, comparability, access* (Executive Summary; §1 *Dimensions of Data
Quality*) — and none of them is authority or provenance-class. What was searched over the whole
439,613-character substrate:

| term | hits | what they are |
|---|---|---|
| `authorit`, `authoritative`, `issuing`, `provenance`, `Title 13` | 0 | — |
| `statut` | 0 | — (the word "statutory" does not occur) |
| `mandat` | 3 | the SESTAT passage above, its lead-in, and *"mandated by the U.S. Congress"* for two NCSES publications — all §5, all descriptive |
| `official` | 4 | *"official veteran population projection"*, *"the Nation's official vital statistics"* — product descriptions, not metadata fields |
| `legal` | 1 | the Brackstone taxonomy of administrative data: *"legal registration of certain events"* |
| `CIPSEA` | 1 | §4(b), the FoodAPS restricted-use pledge |

The closest thing to a prescription is §1's *"When disseminating a statistical product based on
integrated data, agencies inform users about the sources of data, how the sources were integrated,
and the possible implications for data quality"* and Appendix 3's item **B5**, *"Detail with which
the {Agency} explained the purpose for which the source information was collected initially"* —
both about **documentation for human users**, neither about a structured field, and both already
covered by the provenance quote. Nothing was invented to fill the two unsupported clauses.

**The final clause of the indicator** — *"the trust signal AI rankers need to prefer authoritative
sources over aggregators"* — is the framework's own inference. Neither 2013 nor 2019 document was
written about AI rankers, and no locator was sought for it (task decision 2).

### 0.3 The grounding test, and the one span that grounds in one rendering only

`tests/test_g4_locators_and_progress_drift.py::test_every_quoted_span_in_g4s_locator_is_verbatim
_from_that_document`. The quotes are **read out of the framework of record**, not typed into the
test; a sibling test asserts the record's `evidence_raw` is the skeleton cell that authors it, so
the test guards the published string.

| span | `docling_md` | `pypdf` |
|---|---|---|
| "Unlike survey data, which are collected for statistical purposes, administrative data are collected as part of a program agency's routine operations." | **True** | False |
| "Institutional Environment refers to the credibility of the administrative agency for producing high quality and reliable administrative data." | True | True |
| "The extent to which data are well documented, verifiable, and easily attributed to a source." | True | True |
| "Clarity of the description of the source of a data element in documentation including metadata information." | True | True |
| "Government program agencies create administrative data as part of their daily operations." | True | True |
| "NSF has a continuing mandate most recently expressed in the America COMPETES Reauthorization Act of 2010" | True | True |

**The one False is a character, and it is worth recording.** The PDF sets `agency’s` with U+2019;
Docling normalises it to U+0027 and `grounding.normalize` does not, because NFKC does not map the
right single quotation mark to an apostrophe. Both renderings come from the same sha256-verified
bytes, so the span is in the document either way. The test therefore requires a span to ground in
**a** rendering that is on disk and names the per-rendering result in its failure message. The
alternative — requiring every rendering — would have forced this citation to stop mid-sentence at
"as part of a program" to dodge one punctuation mark, which is a worse citation, not a safer one.
A document with no rendering on disk skips, naming the rebuild command; both are gitignored.

Two other quotes the reading rejected for the same class of reason are worth naming so the next
task does not re-derive them: SPWP-46's *"Administrative data were gathered for a particular
purpose-running a program-and can have qualities…"* (Docling renders the em dashes as hyphens) and
anything drawn from Appendix A's compendium table, whose cells Docling repeats five times per row.

---

## 1. The appendix's two G4 rows, before and after

`docs/reports/generated/sources_per_check.md`, lines 78–79, Locator column.

**Before** (both rows, verbatim):

```
| G4 | G4 · Authority metadata | Prell M; … *FCSM 19-01: Transparent Reporting for Integrated Data Quality*. 2019. <…>. | `fcsm-19-01-transparent-reporting-for-integrated-data-quality` |  |
| G4 | G4 · Authority metadata | Iwig W; … *Statistical Policy Working Paper 46: Data Quality Assessment Tool for Administrative Data*. 2013. <…>. | `statistical-policy-working-paper-46-data-quality-assessment` |  |
```

Two empty Locator cells — a citation with no page number, which is what DN-001's "citable by a
stranger" floor forbids.

**After**, Locator column only:

* `fcsm-19-01-…` — "§3(c), VetPop2016, Table 3.3, dimension 4 Traceability, which is the
  provenance-carried-as-metadata clause: "The extent to which data are well documented, verifiable,
  and easily attributed to a source.", assessed as "Clarity of the description of the source of a
  data element in documentation including metadata information."; and §1 Introduction, Types of
  Data, for the survey-versus-administrative distinction the clause rests on: "Government program
  agencies create administrative data as part of their daily operations."; statutory mandate:
  recorded as one agency's practice and nowhere prescribed, §5 SESTAT: "NSF has a continuing
  mandate most recently expressed in the America COMPETES Reauthorization Act of 2010"; issuing
  authority: general support; no pinpoint — the report's eight quality dimensions do not include
  one, and the searches are in cc_tasks/2026-09-19_g4_locators_and_progress_drift_RESULT.md §0"
* `statistical-policy-working-paper-46-…` — "Introduction, opening paragraph, which supports the
  statistical-versus-administrative provenance clause and that clause only: "Unlike survey data,
  which are collected for statistical purposes, administrative data are collected as part of a
  program agency's routine operations."; and the INSTITUTIONAL ENVIRONMENT dimension definition,
  Initial Acquisition phase, which makes the identity of the issuing agency a quality dimension to
  be assessed rather than a field to be carried: "Institutional Environment refers to the
  credibility of the administrative agency for producing high quality and reliable administrative
  data."; issuing authority and statutory mandate: general support; no pinpoint — the Tool asks 43
  questions and none of them asks under what authority or mandate the data are held, and its Data
  Dictionary Template carries File Name, Description, File Date and File Format and no authority
  field"

**Where the appendix reads it from** (decision 3's conditional): exactly where the task said —
`report_traceability.locators()` parses the balanced parenthetical after each backticked slug in
the indicator's `evidence_raw`, and `evidence_raw` is the skeleton cell. No second source exists,
so no edit went anywhere else. The locators reach the built markdown
(`docs/reports/2026-09_fss_ai_readiness_L0.md`, appendix table) and the PDF, and
`docs/data/sources_per_check.json` through `build_l0_site.py`.

---

## 2. The single-writer path, its delta, and the projection

`scripts/build_framework_graph.py` (dry-run first, then for real), which hands the merged record
to `framework_writeback.save`. **`--force` was not used.**

```
"delta": {"nodes_added": {}, "nodes_removed": {}, "nodes_changed": 1,
          "edges_added": {}, "edges_removed": {}, "edges_changed": 0,
          "counts_keys_dropped": [], "counts_moved": {}},
"written": true, "unchanged": false, "event_id": "9abeabc3790d4b67bead5968f7e09ad4"
```

One node changed (`ind:G4`), **zero nodes removed, zero edges removed, zero `counts` keys
dropped**. The event on `events/batch-033_framework.jsonl` carries the before/after of
`evidence_raw` as its whole node delta — quoted in full in `logs/g4_protected.log`, and asserted
by check 4 of `scripts/check_protected_g4_locators.sh`.

`scripts/load_framework_graph.py`: `evidenced_by_missing_document: 0`; `EVIDENCED_BY` 143,
`MEASURED_BY` 29, `MEASURES` 49, `REMEDIATES` 63, `REQUIRES` 37, `DECOMPOSES_INTO` 97;
`measurement_status` 16 measured / 8 harness_built / 25 specified. Unchanged from before, as it
must be: a locator is not a measurement.

`tests/test_framework_projection_roundtrip.py` + `test_framework_single_writer.py` +
`test_framework_graph.py`: **43 passed, 0 skipped**, 4.68 s. The round trip
(`test_the_round_trip_reproduces_every_row_cell_for_cell`) is what proves the skeleton cell and
the record are one string, and it is green with the new cell in place. Neo4j was up for the whole
session, so the round-trip gate did not skip and Cypher verification of framework state is valid
(DD-057).

---

## 3. The drift guard, its negative control, and the one generator fix

**Red first.** `tests/test_g4_locators_and_progress_drift.py` before the cell was written:
**5 failed, 6 passed** (`logs/g4_tests_red.log`). The five were the locator half —

```
AssertionError: statistical-policy-working-paper-46-data-quality-assessment is cited on G4 with
no locator: the appendix would print a source with no place in it.
AssertionError: fcsm-19-01-transparent-reporting-for-integrated-data-quality is cited on G4 with
no locator: …
AssertionError: …-46-… carries no quoted span; the outcome-(c) case is the test above
AssertionError: fcsm-19-01-… carries no quoted span; …
AssertionError: the appendix's G4 row for …-46-… does not carry the cell's locator
```

— and the six that passed were the drift half plus the two structural locator tests. After the
cell, the projection and the report rebuild: **11 passed**, 3.64 s.

**The guard.** Decision 4, as the standard generated-file-is-up-to-date gate (`go generate` then
`git diff --exit-code`; Bazel `diff_test`; `make -q`): regenerate both files with
`framework_progress.main(["--cycle", PUB["snapshot_cycle"]])` into `tmp_path` and byte-compare
with the committed copies. The cycle is **read from `docs/reports/publication.yaml`**
(`scan_2026-09-10_rj4`), never typed. Three tests: the two byte comparisons (parametrized per
file), a two-run determinism check, and the negative control. All in the fast tier — the whole
file runs in 3.64 s.

**The generator needed no determinism fix.** It stamps no wall clock: the page's "Generated" date
comes from the record's `generated_at`, not from `now`, and two runs into two scratch directories
are byte-identical (`test_the_generator_is_deterministic_across_two_runs`). The committed page was
already current, so `docs/progress/` is **byte-identical to HEAD** and appears in check 1 of the
protected-paths script rather than in its allow-list.

**The one fix the generator did need** was a status line that could fail a run it had already
completed:

```diff
-    print(f"-> {OUT_JSON.resolve().relative_to(REPO)}  {OUT_HTML.resolve().relative_to(REPO)}",
-          file=sys.stderr)
+    print(f"-> {_say(OUT_JSON)}  {_say(OUT_HTML)}", file=sys.stderr)
```

with `_say()` falling back to the absolute path when `relative_to` raises. `Path.relative_to`
**raises** on a path outside the tree, so writing the page anywhere but `docs/progress/` crashed
after both files were on disk — which is exactly what happened the first time the guard pointed
the generator at a pytest `tmp_path` (`ValueError: '…/pytest-4366/progress0/framework_progress_
2026-09-06.json' is not in the subpath of '/Users/brock/GitHub/ai-readiness-kg'`). The fix is in
the generator, per decision 4, not excused in the test.

**The negative control** (`logs/g4_negative_control.log`), one count edited by hand in a scratch
copy of the page, and the message the guard prints:

```
hand edit: whole.indicators 48 -> 49 in a scratch copy

docs/progress/framework_progress_2026-09-06.json is not what the generator produces today.
  first differing line 3
    committed:     "indicators": 49,
    regenerated:   "indicators": 48,
  regenerate with: /opt/anaconda3/bin/python3 scripts/framework_progress.py --cycle scan_2026-09-10_rj4
```

and the HTML half, one label edited:

```
docs/progress/index.html is not what the generator produces today.
  first differing line 48
    committed:   7 criteria. Generated 1999-01-01 2026-09-06
    regenerated: 7 criteria. Generated 2026-09-06
  regenerate with: /opt/anaconda3/bin/python3 scripts/framework_progress.py --cycle scan_2026-09-10_rj4
```

The control is a standing test (`test_the_drift_guard_reports_the_drift_it_was_built_for`), not
just this paragraph, so the message shape is pinned. It is **not** in `make guards`: that target
is a fixed four-file list and the task did not ask for it to grow; the control runs in the fast
tier with the rest of the file.

---

## 4. ResearchTask `34ccb843` — read, not closed

`34ccb843-a412-4457-9529-e4d6dcf4b609`, state `proposed`: *"Staleness gate for every committed
build product, not just figures… render every build product (figures, docs/progress page, built
report markdown, PDF, scan_tool_map output) to a temp dir and byte- or numeral-compare to the
committed file."* Its five named products:

| build product | guard today | where |
|---|---|---|
| figures (`assessment/harness/scan/figures/**.svg`) | **yes — regenerate and byte-compare**, per cycle, every SVG | `tests/test_f5_membership.py::test_every_committed_figure_is_what_the_renderer_produces_today` |
| `docs/progress/` page (both files) | **yes — regenerate and byte-compare**, as of this task | `tests/test_g4_locators_and_progress_drift.py::test_the_committed_progress_page_is_what_the_generator_produces_today` |
| `scan_tool_map` output | **yes — regenerate and byte-compare** (`--check`) | `tests/test_requirements.py` and `tests/test_scan_frame.py::test_the_tool_map_regenerates_byte_identically` |
| the L0 PDF | **partial — numeral-compare against the markdown**, not a regeneration | `tests/test_report_pdf.py::test_the_pdf_carries_exactly_the_markdowns_numbers`, `…_resolved_every_reference_and_kept_every_matrix_row` |
| built report markdown (`docs/reports/2026-09_fss_ai_readiness_L0.md`) | **no regeneration guard.** It is tied to its fragments (a fragment must appear verbatim in it) and to the graph through the tagged Results, but nothing rebuilds it into a temp dir and compares | `tests/test_report_sources_appendix.py::test_the_built_markdown_carries_the_fragment_verbatim`; `tests/test_publication.py::test_the_published_results_are_the_ones_the_report_tags` |

Beyond the five, the `2026-09-16` publication guards cover `CITATION.cff`, `.zenodo.json`, their
`docs/data/` copies, the published matrices and `docs/data/index.json` — field-by-field or
recomputed-from-the-log rather than byte-compared. Two products in that family still have **no
regenerate-and-compare guard**: the markdown fragments under `docs/reports/generated/`
(`matrix_product.md`, `matrix_tierA.md`, `matrix_tierC.md`, `requests_per_netloc.md`,
`rules_by_leg.md`, `sources_per_check.md`, `withdrawn_legs.md`, and the `.build.md`) and the built
markdown above; `rules_by_leg.md` and `withdrawn_legs.md` are named in no test at all.

**The list of unguarded products is therefore not empty, and `34ccb843` stays open.** CC does not
close it, and on this reading Desktop should not either.

---

## 5. Nothing moved that could move a verdict

No rule module, no payload, no Observation and no Finding was touched — `assessment/` and `state/`
are byte-identical to HEAD (§7, check 1). `scripts/score.py` run before the first edit and again
after the last:

```
$ shasum -a 256 logs/g4_score_before.log logs/g4_score_after.log
785aba88276361d9cb80d3bf5b25c982d9bc583677a3b9ccff4b81b492bde87f  logs/g4_score_before.log
785aba88276361d9cb80d3bf5b25c982d9bc583677a3b9ccff4b81b492bde87f  logs/g4_score_after.log
$ diff logs/g4_score_before.log logs/g4_score_after.log   # no output
```

Byte-identical, digest included: every body's score, every rank, every coverage fraction and the
whole concentration block are unchanged. DRSMSU still ranks 1 of 13 on its single G4 pass; that
pass is a measurement of a catalog record and has nothing to do with what the two 2013 and 2019
documents say.

---

## 6. Every premise this task file got wrong

1. **"the converted substrate on disk under `corpus/`" (decision 1).** There is none under
   `corpus/` for either document. `kg.ingest.gate.substrate_path` returns `None` for both — DD-030
   converts HTML and passes PDFs through — so the two renderings are `state/docling_md/<doc_id>.md`
   (the T0/T1 Docling conversion) and pypdf-of-`corpus/bulk/<doc_id>.pdf`, which is what the
   extractor itself reads. Both are gitignored. §0.3 is the consequence: they disagree on one
   character and the test had to say which rendering it checked.
2. **"12 of 49 indicator nodes carry a locator and 37 do not" (§0.2, carried into ResearchTask
   `93d28c6e`).** Not reproducible by any place-and-quote test. Measured on HEAD's record:
   **7 of 49** cells carry a double-quoted span (A1, A3, A8, A10, B3, D3, D4); **8 of 49** carry a
   parenthetical attached to a doc slug — the thing `report_traceability.locators()` reads and the
   Locator column prints — adding A12, whose parenthetical is an internal reference and not a
   place in a document. The number 12 is reproducible only by *"the cell contains an opening
   parenthesis anywhere"*, which scores 13 codes (adding A9, A11, E3, G1-D, G1-O) and counts a
   tiering note and a fixture epoch as locators. After this task: **8** and **9**. So the
   unlocated population is 41 or 40, not 36; `93d28c6e`'s description should be amended when it is
   next touched.
3. **"49 indicator nodes" vs the record's `counts.indicators: 48`.** Both are right and they count
   different things: 49 nodes carry the `AssessmentIndicator` label, one of which (A12) has
   `status: candidate` and is excluded from every numerator and denominator by DD-054. The
   progress page prints 48 for that reason. Naming one number without the other is how the page
   came to look like it had lost an indicator.
4. **"`docs/progress/` … only if decision 4's determinism fix changes its bytes" (write set).** No
   determinism fix was needed and the bytes did not change; the page is byte-identical to HEAD.
   The fix the generator did need was to a status line, not to its output (§3).
5. **The write set stops at "docs/reports/ rebuilt products".** The rebuild does not stop there.
   `scripts/build_l0_site.py` is the last step of the chain the write set names, and it rewrote
   `CITATION.cff`, `.zenodo.json`, `docs/data/CITATION.cff`, `docs/data/zenodo.json`,
   `docs/data/index.json`, `docs/data/ai_readiness_framework.json`,
   `docs/data/sources_per_check.json`, `docs/index.html` and `docs/sitemap.xml` — digests of files
   that changed, plus `built_at`/`build_commit` and the `date-released`/`lastmod` stamps, which
   moved from 2026-09-19 to 2026-09-20 because the tree was rebuilt today. Each is in the
   protected script's allow-list with that reason, and nothing else moved.
6. **The write set does not name a protected-paths script.** Every task's check is new by
   construction; `scripts/check_protected_g4_locators.sh` is this one's, and §3 of the task
   requires it be run.
7. **"an Issue is filed proposing the `EVIDENCED_BY` edge be reviewed" (decision 2c).** Not
   triggered: both documents are outcome (b), so both edges stand on a quote. No Issue was filed
   and none is owed.
8. **Not wrong, worth stating.** Decision 3's fallback — "if the appendix builder reads the
   locator from somewhere other than the evidence cell" — did not fire. There is one path and it
   is the one the task named.

---

## 7. The gate

Tier named on every row. Every command detached, logged and polled to its `EXIT=` line inside this
turn, per the headless rule; nothing was backgrounded and left.

| gate | tier | result | wall clock | log |
|---|---|---|---|---|
| the new file, **red** (before the cell) | — | **5 failed, 6 passed**, 0 skipped, 0 xfailed, 0 deselected, `EXIT=1` — the intended red | 0.35 s | `logs/g4_tests_red.log` |
| the new file, green | fast | **11 passed**, 0 skipped, 0 xfailed, 0 deselected | 3.64 s | (re-run inside the tiers below) |
| framework round-trip + single-writer + graph | fast | **43 passed**, 0 skipped, 0 xfailed, 0 deselected | 4.68 s | — |
| `build_l0_report.py` | — | `gate: PASS`, `fatal_reference_errors: []`, `unresolved_tokens: []`, `bare_numerals_in_prose: []`, `EXIT=0` | — | `logs/g4_report_build.log` |
| `build_report_pdf.py` | — | 15 pages (7 prose), 649,602 bytes, `EXIT=0` | — | `logs/g4_pdf.log` |
| `build_l0_site.py` | — | `EXIT=0`, `snapshot_standing: no successor on the event log` | — | `logs/g4_site.log` |
| `make gate-fast` | **fast** | **2,718 passed, 3 skipped, 27 deselected, 12 xfailed**, `EXIT=0` | 690.10 s | `logs/g4_gate_fast.log` |
| `make gate-full` (`-rs`, detached) | **full** | **2,745 passed, 3 skipped, 0 deselected, 12 xfailed**, `EXIT=0` | 2,309.17 s | `logs/suite.log` |
| `seldon verify` | — | **All checks passed**, `EXIT=0`; 36,865 events readable, 35 precedence edges acyclic, 150 task source files resolve | — | `logs/g4_seldon_verify.log` |
| protected paths | — | **PROTECTED PATHS OK**, `EXIT=0` | — | `logs/g4_protected.log` |

`make gate-task` was **not** required and was not run: no rule module, no rule registry and no
re-derivation engine changed, and `assessment/` is byte-identical to HEAD. The three skips are the
standing ones (`test_dispatch_config` interactive-only, `test_scan_harness` E5, `test_g1
_preservation` SE-and-CI) — none is a Neo4j skip, because the database was up throughout.

**Protected paths, clause by clause** (`scripts/check_protected_g4_locators.sh`):

1. byte-identical: `kg/`, `assessment/`, `state/`, `corpus/`, **`docs/progress/`**,
   `docs/research/`, `docs/design/`, `docs/reports/scan_matrix_*`, `docs/reports/sections/`,
   `docs/reports/publication.yaml`, `docs/data/results_tagged.json`,
   `docs/data/corpus_manifest.json`, `mcp/`, `Makefile`, `controls.yaml`, `dixie_evidence.yaml`,
   `seldon.yaml` — **all clean**;
2. the skeleton moved in **exactly one line** (256 → 256 lines), and that line starts `| G4 |`;
3. `events/`: 61 tracked shards, no new shard, none rewritten, **exactly one appended** —
   `events/batch-033_framework.jsonl`, `{"framework_writeback": 1}`;
4. that event's delta has empty `nodes_removed`, `edges_removed` and `counts_keys_dropped`;
5. every path that moved is on the write-set list, and nothing else moved.

`logs/` is gitignored; what ships is this file and the tree it quotes.

---

## 8. What ships

`docs/crosswalk/usafacts_operationalization_skeleton.md` (G4's Evidence cell, one line),
`framework/ai_readiness_framework.json` (through `save`), `events/batch-033_framework.jsonl` (one
appended event), the rebuilt report products and the site files §6 item 5 lists,
`scripts/framework_progress.py` (the status-line fix), `scripts/check_protected_g4_locators.sh`
(new), `tests/test_g4_locators_and_progress_drift.py` (new, 11 tests), `seldon_events.jsonl` and
this RESULT.
