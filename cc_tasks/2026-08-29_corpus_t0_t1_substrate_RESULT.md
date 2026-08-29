# RESULT — 2026-08-29_corpus_t0_t1_substrate (with ADDENDUM-01, ADDENDUM-02)

**Date:** 2026-08-29. **Zero `model_stub` spend** — no run declared, none needed. Every layer
here is metadata API, local parsing, or local embedding. Docling and sentence-transformers
run locally; neither touches the extraction choke point.

**Close criteria per ADDENDUM-02 §1:** T1 complete, T0 at whatever coverage exists at close.
**T1 is complete. T0 is at 29/178 with 149 documents in a retryable state and one command to
finish them.**

---

## §-0.5 (ADDENDUM-01) — the gate. Cleared, and the addendum's premise was wrong

`kg.manifest verify`: **4 problems → clean.** Committed separately as `00acd06`.

The addendum instructs: "the `manifest_add` event is the truth about what was admitted; the
file on disk is the drifted party **until proven otherwise**." The dixie ledger proves
otherwise for all four, so the presumption is rebutted on evidence, not overridden.

| doc_id | event | dixie | disk | what the ledger says |
|---|---|---|---|---|
| `advancing-american-ai-act-ndaa-fy2023-div-g` | `9e5d37dfa7d1` | `b0d6bd47384d` | `b0d6bd47384d` | wrong extent (whole NDAA) → standalone `BILLS-117s1353rs` |
| `ai-in-government-act-of-2020` | `32285d91badb` | `b5bb3a22ac12` | `b5bb3a22ac12` | wrong extent → standalone `BILLS-116hr2575pcs` |
| `fcsm-19-01-transparent-reporting-...` | `0a1cfc211362` | `b646efbbd55a` | `b646efbbd55a` | corrupt PDF (`PdfReadError: no 'endstream' marker @811018`) → clean NCES copy |
| `information-quality-act-...-sec-515` | `07fc5aa02373` | `6d69b226950c` | `6d69b226950c` | over-extent (whole P.L. 106-554) → operator-supplied §515 excerpt |

Every one is a **deliberate, operator-authorized July 2026 re-acquisition**, recorded at the
time with `superseded_sha256`, a reason, and the superseded original preserved in
`corpus/quarantine/`. **Nothing drifted. No re-fetch was performed or needed** — the ledger
already answers what a re-fetch would ask, and one of the four (the §515 excerpt) is an
operator-supplied file that no URL serves.

**The addendum's decision tree has no cell for this**, because the fault is not in either
party it names. It is a **ledger-sync gap** at the seam CLAUDE.md describes: `manifest.json`
projects from the dixie ledger and carried the corrected hash; `kg.manifest.verify` replays
the KG event log, which never received a supersession event. Two layers diverged and nothing
reconciled them.

Fixed per the addendum's own rule — never rewrite the original event, append a supersession.
New `kg.manifest.content_update` writes a `content_update` event that `_load_entries` replays
over the admission entry. Four guards, each mutation-proven: unknown `doc_id` refused; `reason`
confined to a closed list; `superseded_content_hash` must equal the entry's **current** hash
(blind chaining is how a supersession silently adopts whatever is on disk); unchanged bytes
refused. A retired hash no longer blocks a later admission, so a quarantined original can be
re-admitted under its own doc_id.

**Deviation:** the addendum's reason vocabulary (`source_revised`,
`source_unavailable_disk_adopted`) fits none of these. Added `extent_corrected` and
`corrupt_source_replaced`, which is what the dixie records actually say.

## ADDENDUM-01 §2 — acquisitions

- **W3C PROV-DM + PROV-O admitted** (`w3c-prov-dm-data-model`, `w3c-prov-o-ontology`),
  resolving the crosswalk's D3 gap. Confirms 3d86f16d's finding: the corpus had no provenance
  vocabulary; the previous pointer matched the letters "prov" inside a Census standard's code.
- **Commerce guidance: still blocked.** The manual-download lane was checked at dispatch —
  `corpus/inbox/` was empty. Left `acquisition_blocked`; A1/B1 remain gaps. It is row 3 of the
  operator pickup list.

---

## §0 — T0 bibliographic harvest

**Coverage 29/178 resolved · 149 retryable · 0 partial-findings.**

| provider / state | n | meaning |
|---|---:|---|
| `doi` (OpenAlex + Crossref) | 10 | resolved from a DOI in, or derived from, the primary URL |
| `arxiv_then_title` | 9 | arXiv id, title-guarded |
| `crossref_title_search` | 8 | OpenAlex unavailable; Crossref served it |
| `title_search` (OpenAlex) | 2 | |
| **resolved** | **29** | by provider: OpenAlex 21, Crossref 8 |
| `harvest_error` | **149** | **retryable — asserts nothing.** OpenAlex daily quota |
| `bibliographic_partial` | **0** | a finding; none currently justified |

Reference lists: **100 referenced DOIs from 2 documents.** Corpus-internal citation edges: 2.
Coupling pairs: 0.

### Three defects found in my own harvest, all fixed, one retracted number

**1. A transient failure was written down as a finding — the number is retracted.** The first
implementation returned `None` from `get()` on HTTP 429 and the caller recorded
`bibliographic_partial`. **159 documents were labelled "has no bibliographic record" on the
strength of a rate limit.** That figure is withdrawn. `bibliographic_partial` is now writable
by exactly one function requiring every provider to have answered cleanly; anything else is
`harvest_error`. Enforced by test, including a test that reads the source to assert there is
still only one write path. Residue check on the cache: **0 mislabelled records**. Generalized
as methodology §7.11.

**2. The fallback was written but unreachable.** `get()` raised on provider failure, so a
document aborted before it ever reached Crossref — a resolution ladder whose lower rungs
cannot be reached is not a ladder. Provider failure now degrades to the next rung and is
recorded per document.

**3. A wrapper record impersonated the work.** The FAIR principles paper matched
**"Faculty Opinions recommendation of** The FAIR Guiding Principles…" — `cited_by` 3 against
the real paper's thousands — because the manifest title sits wholly inside the recommendation's
title. This is the fabrication mode DD-024 recorded for distant supervision, arriving in the
bibliographic layer. Fixed with a wrapper blocklist and a length-ratio bound (containment now
requires ≥ 0.8); both mutation-proven against tests that hold the year constant so only the
guard under test can reject (methodology §7.9 — the first version of that test passed with
both guards deleted).

Two further guard corrections, from observed misses rather than a wish for a higher hit rate:
the manifest's `pub_year` is sometimes an **access date** (`2019-11-11` for a 2016 paper), so
an exact title match is no longer vetoed by a year; and manifest titles carry editorial
suffixes ("(Hiniduma et al., 2024)") that guaranteed false mismatches. Deterministic URL→DOI
derivations were added for the two publishers present (`nature.com/articles/sdata201618` →
`10.1038/sdata.2016.18`; `aclanthology.org/X` → `10.18653/v1/X`) — mechanical rearrangements
of characters already in the URL, which fail loudly as a 404 rather than resolving to another
work.

### GROBID (task §0.2) — not run, not substituted

No server on `:8070` and it needs a Java runtime this task has no mandate to install
(ADDENDUM-02 §4 confirms that call). DOI-less PDFs therefore fall to title search, and
`biblio_method` is recorded per document as `resolution` + `metadata_source`.
**Yield number that would justify GROBID-via-Docker as a future task:** of 145 documents with
no DOI/arXiv/ACL identifier in their URL, title search resolved **10** (6.9%). If a future
harvest needs the other 135, header/reference parsing is the remaining lever.

### Finishing T0 — ADDENDUM-02 §1

```
python -m kg.biblio coverage    # resolved / retryable / partial, per provider
python -m kg.biblio resume      # finishes the harvest, then recomputes everything derived
```

`resume` is idempotent, touches only retryable states, degrades across the provider ladder,
and surfaces a daily quota as a retryable error rather than a multi-hour sleep (OpenAlex
answered `Retry-After: 38913` ≈ 10.8 h; anything over 90 s is treated as a quota, not a blip).
On completion it **recomputes the §2.2 ranking and the §2.3 ordering automatically**, which is
the only thing that makes publishing a provisional number safe.

---

## §1 — T1 structural index. Complete.

| | |
|---|---:|
| documents converted | **178 / 178**, 0 failed |
| chunks | **5,164** |
| FTS5 rows | 5,164 |
| embeddings | 5,164 (`all-MiniLM-L6-v2`, dim 384, L2-normalised) |
| converter | docling 89 · passthrough (already markdown) 85 · **pypdf_fallback 4** |
| fidelity | layout_aware 174 · **degraded 4** (213 chunks) |

**Projection proof (§1.4): PASS.** `--phase rebuild` built a second database from sources and
diffed every table: counts identical across all seven. The db holds no state its sources do not.

**Degraded documents proceed at full speed** (ADDENDUM-02 §3): the 4 pypdf-fallback documents
have complete chunks, FTS and embeddings, and the `fidelity` flag rides on **every chunk row**
so any downstream derivation inherits it without a join.

### §1.1 fidelity diff — and it contradicts the premise it was run to confirm

The check was meant to confirm that re-converting removes the dropped-character damage DD-023
names. **It does not.** Positive control on the named instance, both converters on the same
bytes:

```
pypdf   : ['Heterogeneous Euclidean-Overlap Metri']
docling : ['Heterogeneous Euclidean-Overlap Metri']
verdict : converter_was_not_the_cause
```

The missing `c` is in the **PDF's own text layer**. No converter choice repairs it. Filed as
**DD-023 ERRATUM 2**: re-conversion does not fix the `span_partial` class it was prescribed
for, and the v0.3.7 pilot should not expect a quarantine-rate improvement from this change.
Docling still earns its place on separate grounds — 4–24% more extracted text on the sample
(169,576 vs 163,016 chars on the 360-degree survey; 127,424 vs 102,301 on MITRE) from
recovering tables, headings and reading order. That is a real gain in retrievable structure;
it is not the gain DD-023 claimed. Generalized as methodology §7.8.

The general word-level heuristic in the same script found only 5 candidate repairs across 5
documents, all plural/suffix variants (`conference`→`conferences`) rather than the damage
class — reported as too weak to be evidence, which is why the named-instance control is what
the conclusion rests on.

### Artifacts

- `state/corpus_index.db` — declared a rebuildable projection, proof above
- `state/docling_md/` — converted markdown + per-doc meta (`converted_by`, `fidelity`, source sha256)
- `docs/corpus/manifest_table.md` — 178 rows, T0/T1/T2 flags. **T2 is empty corpus-wide by
  design**: extraction waits on v0.3.7 (DD-023) and this task is forbidden from it.

---

## §2 — Acquisition round 2

**§2.1 operator literature list: not supplied at dispatch.** Skipped and noted, per the task's
own instruction.

**§2.2 coupling expansion: computed, and honestly unusable.** `docs/corpus/acquisition_candidates.md`,
labelled **PROVISIONAL — T0 coverage 29/178**. No candidate reaches the ≥ 3 corpus-citer bar;
the highest observed is **1**. Reference lists exist for **2 of 178** documents, so this is a
statement about coverage, not about the literature. **The bar was not lowered to manufacture a
list**, and nothing was auto-admitted. `kg.biblio resume` regenerates the file whenever
coverage advances.

**§2.3 `t2_priority`: computed, split by what coverage affects.** `state/t2_priority.json`.
Crosswalk demand is **coverage-independent and already final** (ADDENDUM-02 §1 requires it now
regardless); T0 centrality is not, and each row records whether its centrality was measurable.

| rank | doc_id | crosswalk demand | T0 centrality | T0 state |
|---|---|---:|---:|---|
| 1 | `odcs-open-data-contract-standard` | 3 | 0 | retryable |
| 2 | `fcsm-23-02-a-framework-for-data-quality-case-studies` | 2 | 0 | retryable |
| 3 | `nist-ai-risk-management-framework-ai-rmf` | 2 | 0 | resolved |
| 4 | `usafacts-ai-ready-data-guide` | 2 | 0 | retryable |
| 5 | `w3c-dcat-3` | 2 | 0 | retryable |
| 6 | `data-readiness-for-ai-a-360-degree-survey` | 1 | 1 | resolved |
| 7 | `wilkinson-2016-fair-guiding-principles` | 1 | 1 | resolved |
| 8–10 | `aggarwal-2024-geo…`, `aidrin-2-0…`, `aidrin-hiniduma-2024` | 1 | 0 | mixed |

**`docs/corpus/operator_pickup.md`** (ADDENDUM-02 §2) — projected, not hand-written, 5 rows:
the Commerce block plus the 4 `fidelity: degraded` documents, ordered by `t2_priority` with
the provisional label on its face. The projection **deduplicates by (doc, state)**: the
append-only event log legitimately holds the Commerce block twice because the admission pass
ran twice, and a projection must collapse that.

---

## ADDENDUM-02 §4 — defect fixes folded in

- **Log-bomb guard.** Converter exception text is truncated to 2,000 chars for the shared log;
  the raw message goes to `state/convert_errors/<doc_id>.err.txt`. Docling's `ConversionError`
  embeds the entire PDF page dictionary — one failure wrote ~230,000 lines and killed the
  process, so an unbounded exception message is a denial of service on your own run. Test:
  a 500KB seeded exception truncates and the raw text survives. Mutation-proven.
- **GROBID:** not installed; yield number recorded above.
- **`bibliographic_partial` residue:** 0. Single write path, enforced by test.

Suite **241 → 254** (+13).

---

## Discrepancies (reported, not reconciled)

1. §-0.5's decision tree does not cover the case that actually occurred (above).
2. The addendum's `content_update` reason vocabulary fits none of the four cases; two reasons
   added.
3. §1.1's premise is contradicted by its own measurement (DD-023 ERRATUM 2).
4. §0.2's GROBID step could not run.
5. §2.1's input was not supplied.
6. §2.2 is computable but not decision-grade at current coverage.
7. The task's `evidence_class` vocabulary is carried on every T0/T1 record
   (`bibliographic` / `structural`) and on every chunk. No record from this task is eligible
   for a validated stratum, and none is pooled with gated items.

## Not done

T2 extraction (forbidden here, waits on v0.3.7); Postgres (SQLite at 178 docs / 5,164 chunks
is not close to a measured need); Wintermute integration (a Wintermute decision, not a side
effect of this task); the remaining 149 T0 documents — one command, no session context.

---

# ADDENDUM-02 compliance audit (2026-08-29, after the first close)

Re-read ADDENDUM-02 clause by clause against what actually shipped. The file was byte-identical
to the version acted on, so this is an audit of my own delivery, not a response to a change.
**Four requirements were under-delivered on the first pass.** All four are now closed; each is
listed with what was missing rather than folded silently into the prose above.

| clause | what shipped first time | gap | now |
|---|---|---|---|
| §1 coverage table | resolved / retryable / partial, per provider | **`blocked` was missing** — a blocked *acquisition* was folded in with an unresolved *lookup*, two different failures reading as one number | `coverage()` reports `blocked` + `blocked_docs`, plus `retryable_by_provider` naming which provider holds each retryable doc up |
| §2 one projection | `--phase table` and `--phase pickup`, run separately | addendum says pickup is "regenerated by the same projection that builds `manifest_table.md`"; two half-runs publish disagreeing views | `--phase project` runs both; `table`/`pickup` remain for deliberately running half |
| §3 per-doc re-index | degraded docs got full T1 treatment and the flag propagated | **the re-acquisition path did not exist**: "re-convert + re-index *that document only*, marking its prior derivations stale" was unimplemented | `--phase reindex --doc-id X --reason ...`, with a `stale_derivations` table recording each superseded chunk and the content hash it was derived from |
| §4 `biblio_method` | `resolution` + `metadata_source` served the purpose | not emitted under that name, so the distinction lived only in this RESULT | `biblio_method(rec)` on every `t2_priority` row: `doi@crossref`, `unresolved:provider_unavailable`, `unresolved:no_record_at_source` |

**Verified rather than asserted:**

- `--phase reindex` run against a real degraded document (`webb-fcsm-nist-crosswalk`): 84 prior
  chunks marked stale with the hash they were derived from, 84 new chunks written, corpus total
  unchanged at 5,164 — **only that document was touched**, which is the whole point of the clause.
- `python -m kg.biblio resume --limit 6` run **while the OpenAlex quota is still exhausted** —
  the hostile case. It completed, did not hang on a 10.8-hour `Retry-After`, and recomputed the
  derived rankings. A second `recompute` produced byte-identical coverage: **idempotent**.
- Mutation-proven: dropping `blocked` from the coverage table fails a test; collapsing
  `provider_unavailable` into `no_record_at_source` fails a test. Both are the distinctions
  §7.10/§7.11 exist to protect, so a test that does not fail when they are erased is not a test.

Suite **254 → 259** (+5 compliance tests).

**Unchanged by this audit:** every number in the sections above — T1 completeness, T0 coverage
29/178, the DD-023 ERRATUM 2 fidelity finding, and the §2 rankings. The gaps were in the
mechanisms the addendum required for *finishing later*, not in what was measured.
