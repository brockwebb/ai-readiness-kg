# RESULT — A3 and A10 get their sources: every published check is now citable

**Task:** `cc_tasks/2026-09-11_a3_a10_sources.md`. No addenda exist; globbed before starting and
again before §3, both times empty.
**Date:** 2026-09-11 UTC
**Spend:** zero model calls. **Network: NONE.** Not "acquisition only" — none. All three sources
were already in the corpus, admitted and integrity-verified on 2026-08-21; nothing was fetched.
Nothing under `state/` or `corpus/` changed, asserted by `scripts/check_protected_a3a10.sh`.

---

## 1. The seven-leg table, after

| leg | indicator | → construct | → definitions | → **source documents** | spec | rules |
|---|---|---|---|---|---|---|
| A4 | `A4` | 1 | 29 | **6** | 1 | 1 |
| A5 | `A5` | 1 | 29 | **2** | 1 | 2 |
| A10 | `A10` | 1 | 39 | **2** (was 0) | 1 | 3 |
| A11-declared | `A11` | 1 | 13 | **2** | 1 | 2 |
| A12 | `A12` | 1 | 13 | **2** | 1 | 1 |
| G1-D | `G1-D` | 1 | 364 | **40** | 1 | 1 |
| A3 | `A3` | 1 | 52 | **3** (was 0) | 1 | 4 |

All seven legs reach at least one source; A3 and A10 reach at least two. The definition counts
for A3 and A10 went 0 → 52 and 0 → 39, because the chain continues through the documents to the
`Definition` nodes already extracted from them.

## 2. The gate — §3

| clause | result |
|---|---|
| All seven legs reach ≥ 1 source document; A3 and A10 ≥ 2 | **PASS** — §1, and `tests/test_report_traceability.py` asserts it, 28 cases |
| Every admitted `Document` carries URL, retrieval date and hash | **PASS on URL and hash; the retrieval date is a finding, not a pass** — §6. No document was admitted here, so the clause bites on the three already in the corpus: all three carry `primary_url` and `sha256`; none carries `acquisition.acquired_at`, which is `null` for everything `scripts/harvest_kernel.py` admitted. `integrity.checked_at` (2026-08-21) is the nearest thing and is not the same claim |
| `EVIDENCED_BY` edges follow the existing shape | **PASS** — `{"properties": {"doc_id": …}}`, the shape `build_framework_graph` emits; no new property invented, and the locator goes where A12's already goes (§4) |
| Socket counter shows only the acquisition hosts | **PASS, vacuously and better** — zero sockets. No host of any kind was contacted |
| PDF rebuilt? | **No** — decision 4's condition is not met (§5). The numeral gate and page count are therefore not this task's to report; the committed PDF is untouched and its gates still pass inside the suite |
| `make gate-task` | **PASS** — 1,923 passed, 17 skipped, 12 xfailed, 353.3 s; then 16 of 16 payloads byte-identical, 5.7 s |
| `make guards` | **PASS** — 25 passed, 15.6 s |
| `make gate-full` | **PASS** — 1,942 passed, 17 skipped, 12 xfailed, 1,212.7 s, detached and polled to EXIT |
| `seldon verify` | **PASS** — all checks passed |
| Protected paths | **PASS** — `scripts/check_protected_a3a10.sh` |

## 3. §1 — the admission path exists, and it had already been walked for all three

Decision 1 asks CC to find the path and stop if admission would need bypassing it. The path is
DD-003's and is written down in `kg/manifest.py` itself:

1. the file under `corpus/`; 2. `python -m kg.manifest add …`, which validates provenance,
hashes, refuses duplicates and appends a `manifest_add` event; 3. the Dixie sweep
(`dixie-evidence verify --config dixie_evidence.yaml`) to ledger it; 4. `python -m kg.manifest
rebuild` to refresh `corpus/manifest.json` from the ledger; 5. a projection, which turns the
`manifest_add` event into the `:Document` node.

**No step of it had to be run, because the corpus already held every source this task needed.**
That is the doctrine's first search order — existing corpus before the open web — and it
answered:

| source | doc_id | in corpus since | integrity |
|---|---|---|---|
| W3C, *Data on the Web Best Practices* (Rec. 31 Jan 2017) | `w3c-dwbp-2017` | 2026-08-21, `harvest_kernel.py` | verified, sha256 `9f41e8ea…`, `https://www.w3.org/TR/dwbp/` |
| Wilkinson et al. (2016), *The FAIR Guiding Principles* | `wilkinson-2016-fair-guiding-principles` | 2026-08-21 | verified, sha256 `cdddd9f4…`, `https://www.nature.com/articles/sdata201618` |
| DCAT-US Schema v1.1 (Project Open Data Metadata Schema) | `dcat-us-1-1-schema` | 2026-08-21 | verified, sha256 `2a0f079d…`, `https://resources.data.gov/resources/dcat-us/` |

All three already had `:Document` nodes in the graph, each already carrying extracted
`Definition` nodes (14, 25 and 13). What was missing was never the documents — it was five
edges.

## 4. §2 decisions 2 and 3 — the citations, verified from the documents rather than typed

**The best-practice numbers are read out of the file, as decision 2 requires.** Every string
below was grepped from `corpus/kernel/w3c-dwbp-2017.md` or extracted from the FAIR PDF in this
session.

**A3 — bulk access.** Indicator: *"Full-product bulk download exists and is linked from product
page."*

* `w3c-dwbp-2017` — **Best Practice 17, Provide bulk download**: *"Enable consumers to retrieve
  the full dataset with a single request."* Exact match to the indicator.
* `wilkinson-2016-fair-guiding-principles` — **A1**: *"(meta)data are retrievable by their
  identifier using a standardized communications protocol"*, with **A1.1**: *"the protocol is
  open, free, and universally implementable."*
* `dcat-us-1-1-schema` — **distribution → downloadURL**: *"This must be the **direct** download
  URL"*, expressly distinguished from `accessURL`, *"an indirect means of accessing the data …
  This should not be a direct download URL."* This is the federal anchor decision 3 asked for:
  the schema's own page names *"the [Implementation Guidance] available as a part of Project
  Open Data [which] describes Agency requirements … as per the Open Data Policy"*, i.e. M-13-13.

**A10 — deep links and honest absence.** Indicator: stable directly-requestable deep links;
invalid routes return a true 404/410, not an HTTP-200 shell.

* `w3c-dwbp-2017` — **BP 9, Use persistent URIs as identifiers of datasets**: *"Developers may
  build URIs into their code and so it is important that those URIs persist and that they
  dereference to the same resource over time"* — the deep-link half. And **BP 27, Preserve
  identifiers**: *"If dereferencing a URI leads to the infamous 404 response code (Not Found),
  the user will not know whether the lack of availability is permanent or temporary"* — which is
  precisely the property a soft-404 destroys, stated by the standard.
* `wilkinson-2016-fair-guiding-principles` — **F1**: *"(meta)data are assigned a globally unique
  and persistent identifier"*; **A2**: *"metadata are accessible, even when the data are no
  longer available."*

**BP 10 was rejected after reading it.** "Use persistent URIs as identifiers *within* datasets"
is about reusing other people's URIs, not about a tool's own deep links. It is the obvious
number to cite from the title alone and it is the wrong one; BP 9 and BP 27 are the right pair.
That is the whole reason decision 2 says CC verifies the numbers from the document.

**Where the locator is recorded, and why there.** Decision 2 says to follow the existing shape.
The existing shape is `A12`'s cell: `` `rfc-9309-robots-exclusion-protocol` (the declared
layer's semantics); `cloudflare-ai-crawl-control-manage-crawlers` (the enforcing layer this
indicator detects from outside) `` — the locator is prose in the skeleton's Evidence cell, which
the builder carries verbatim onto the indicator as `evidence_raw`. `EVIDENCED_BY` edges carry no
properties but `doc_id`, across all 124 of them. So the BP numbers went in the cell, and no new
property was invented.

**Decision 3's fourth source was not acquired, and that is a decision.** OMB M-13-13 itself is
not in the corpus and neither is the 5-star page. A3 already reaches three sources including the
federal one, and DCAT-US *is* the Project Open Data metadata schema M-13-13 mandates and cites
its implementation guidance on its face — the policy lineage decision 3 asked for, one hop, with
the hop inside an admitted document. Acquiring the memorandum would add a fourth citation to the
only leg that already has three, at the cost of a manifest add, a Dixie sweep and a projection.
If the operator wants the memorandum named directly, it is one admission and a one-line cell
edit, and the gate would not move.

## 5. Decision 4 — the report carries no per-check source list, so it was not touched

Searched: no section and no appendix lists sources per check. The appendix's per-leg table is
*"Rules that judged this cycle"* — rule versions, not citations — and the *"The six checks"*
section describes each check in prose without citing anything. Decision 4's condition is
therefore not met: **the report is not touched, the PDF is not rebuilt, and the citation lives
in the graph.** `docs/reports/` is protected whole by this task's protected-paths check.

## 6. §2 decision 5 — the traceability script is now a test

`tests/test_report_traceability.py`, 28 cases. Every leg ≥ 1 construct, ≥ 1 `MeasurementSpec`,
≥ 1 `Rule`, ≥ 1 source document; A3 and A10 ≥ 2 sources and ≥ 1 reachable definition; and every
`EVIDENCED_BY` edge in the graph points at a doc_id `corpus/manifest.json` holds, which is the
"citable by a stranger" invariant asserted from the graph side.

**The measurement is the script's, not a copy.** `report_traceability.measure(session)` is now
the one implementation and both the CLI and the test call it — because the two reversed arrows
below are exactly the kind of defect a second copy of a query preserves.

**Both Cypher directions are pinned, each asserted in both directions:**

* `DECOMPOSES_INTO` runs construct → indicator (97 edges); indicator → construct must be 0.
* `DEFINES` runs document → definition (1,949); definition → document must be 0.
* `EVIDENCED_BY` runs indicator → document (129); the reverse must be 0.

Written backwards, the first two each reported *every leg reaching nothing* — a clean, plausible
table of zeros. A test that only counted edges would have passed against the reversed query and
called the graph empty.

## 7. THE THING THIS TASK ALMOST BROKE, and the guard that now exists

**`scripts/build_framework_graph.py` regenerates the framework of record from the skeleton, and
the record has been written back to ever since.** Running it — the obvious way to turn a new
evidence cell into edges — produced a diff of **90 insertions and 843 deletions**:

* **22 `MEASURED_BY` edges deleted**, every indicator's link to its `MeasurementSpec`;
* **3 of A12's `EVIDENCED_BY_INTERNAL` refs deleted**;
* **A12's construct moved out of criterion G back into A**, undoing its DD-054 candidate
  adoption;
* `measurement_specs`, `rules_built`, `specs_with_recorded_decision`, `candidate_indicators`
  and `indicators_measured` dropped from `counts` entirely.

It is not a bug — regenerating is what that script is for. The trap is that the skeleton is the
source of the AUTHORED cells and *not* of the whole record, and nothing said so at the point of
use. Caught by diffing the regenerated file against `HEAD` before doing anything with it;
reverted with `git checkout`.

**The fix is `scripts/framework_writeback_evidence.py`**, which carries one named indicator's
evidence cell across and touches nothing else, through `scripts/framework_writeback.py` — the
one helper that recounts, writes, and appends a `framework_writeback` event carrying the sha256
of the bytes written (`ff796299…`, `events/batch-033_framework.jsonl`). It parses the cell with
`build_framework_graph.evidence_edges` against `corpus/manifest.json`, so the rule that *a
doc_id becomes an edge only if the manifest holds it* is the same code in both paths, and it
refuses the whole write-back if a cell names a document the corpus has not admitted.

Result: **five edges added, zero removed, 126 nodes unchanged**, `evidenced_by` 122 → 127,
`gaps` 19 → 18 (A3's gap marker is gone because A3 no longer has a gap), every other count
identical.

What makes this safe rather than merely careful is a test that already existed:
`tests/test_framework_graph.py::test_the_round_trip_reproduces_every_row_cell_for_cell` (DD-050)
requires the JSON to render back to the skeleton cell for cell. A write-back that carried the
cell inexactly fails there. It passes.

Then `scripts/load_framework_graph.py` projected the layer (DD-057), reporting
`evidenced_by_missing_document: 0`, and `tests/test_framework_projection_roundtrip.py` is green
— which is what makes the Cypher in §1 a valid reading of the record rather than of a stale
projection.

## 8. Every premise this task got wrong

1. **"Network: acquisition only"** (§3). Zero network. Three of the four named sources were
   already in the corpus, integrity-verified, with `:Document` nodes and extracted definitions.
   The task's prior-art section did the hard part — naming the right documents — and then
   assumed they would have to be fetched.
2. **"Documents enter through the repo's existing admission path"** implies documents must
   enter. None did. The missing thing was five edges, and the path for an edge is the skeleton
   plus a write-back plus a projection, which is a different path with a different hazard (§7).
3. **Decision 2's "recorded on the edge or the Document"** (§4). Neither: `EVIDENCED_BY` edges
   carry only `doc_id`, and the Document is the source, not the citation. The locator lives in
   the skeleton's Evidence cell, which is where A12 already keeps one.
4. **Decision 3 names OMB M-13-13 as the federal anchor** (§4). It is not in the corpus;
   `dcat-us-1-1-schema` is, and is the schema M-13-13 mandates. Recorded as a decision, not a
   substitution made quietly.
5. **The gate's "every admitted Document carries URL, retrieval date and hash"** (§2). No
   document was admitted, and the three relied on carry no retrieval date at all —
   `acquisition.acquired_at` is `null` for every document `harvest_kernel.py` admitted. The
   clause cannot be met by the corpus as it stands.
6. **Decision 5's "the seven-leg table as its expected shape"** could not be pinned as a table
   of values. G1-D reaches 40 sources and 364 definitions and A4 reaches 6; pinning those
   numbers would fail the next time anything is cited anywhere. What is pinned is the SHAPE —
   minimum counts per leg and the arrow directions — which is what the decision is for.

## 9. Verification

```
logs/a3a10_writeback.log      framework write-back: 5 edges added, 0 removed,
                              sha256 ff796299…, event in batch-033_framework    EXIT=0
logs/a3a10_loadframework.log  framework projection, evidenced_by_missing_document: 0,
                              EVIDENCED_BY 129, MEASURED_BY 22, MEASURES 37     EXIT=0
logs/a3a10_guards.log         make guards — 25 passed                 15.6 s    EXIT=0
logs/a3a10_gate_task.log      make gate-task — 1,923 passed, 17 skipped, 12 xfailed,
                              353.3 s; then 16 of 16 payloads byte-identical    EXIT=0
logs/suite.log                make gate-full — 1,942 passed, 17 skipped, 12 xfailed,
                              1,212.7 s, detached and polled to EXIT            EXIT=0
logs/a3a10_verify.log         seldon verify — all checks passed                 EXIT=0
logs/a3a10_protected.log      scripts/check_protected_a3a10.sh — PASS           EXIT=0

changed    docs/crosswalk/usafacts_operationalization_skeleton.md  (the A3 and A10
           Evidence cells, and nothing else in the table)
           framework/ai_readiness_framework.json  (+5 edges, 2 nodes' evidence_raw/gap)
           scripts/report_traceability.py  (measure() extracted, so the test calls it)
new        scripts/framework_writeback_evidence.py, scripts/check_protected_a3a10.sh,
           tests/test_report_traceability.py
untouched  every rule module, the harness runtime, every stored payload, every figure,
           corpus/ entire, state/ entire, docs/reports/ entire, tests/test_invariants.py
```

## 10. What the next task needs

1. **`acquisition.acquired_at` is null for every kernel-harvested document** (§8 item 5). A
   corpus whose provenance has no retrieval date cannot answer "as of when" for any citation in
   the report. The harvest log may still hold the timestamps; if it does not, the honest fix is
   to record that the date is unrecoverable rather than to back-fill a guess.
2. **`build_framework_graph.py` can silently destroy the record** (§7). It has no guard: no
   warning that the file it overwrites carries write-backs, and no check that its output is a
   superset of what it replaces. One refusal — "output drops N edges present in the current
   file; pass `--force`" — would have turned a 30-minute catch into an error message.
3. **OMB M-13-13 itself, if the operator wants the memorandum cited directly** (§4). One
   manifest add, the Dixie sweep, a projection, one cell.
4. **A10's indicator is still `status: stub`** and its cell still names an operator-held
   internal draft as admission-gated. It now has two admitted standards-grade sources, so
   whether `stub` is still the right status is a framework judgement, and this task had no
   decision covering it.
5. **The report cites nothing** (§5). Every check is citable through the graph and no reader of
   the PDF can follow it. Whether the published report grows a per-check source list is the
   decision decision 4 deliberately left open.
