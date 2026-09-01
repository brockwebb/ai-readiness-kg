# RESULT — Extent remediation: re-acquire the six thin-extent documents

**Task:** `cc_tasks/2026-08-31_extent_remediation.md`. No ADDENDUM siblings existed at
dispatch or at close. **Date:** 2026-08-31.
**Model spend: ZERO** — run declared at `--ceiling-tokens 0`, so the DD-022 guard refuses a
model call at the `model_stub.invoke` choke point rather than trusting the runner not to make
one. No `claude -p` invocation was made or attempted.

**Headline:** five of six documents re-acquired and clearing the DD-030 gate; open conversion
gaps **6 → 1**. The sixth is cut-with-reason. Along the way the remediation itself moved batch
identity for the fourth time, which is what finally retired the derivation approach: the burn
plan is now a fact on the append-only log.

---

## 0. Reconciliation before closing anything (the task's precondition)

| task file | live graph | document |
|---|---|---|
| `21133dbf` | `21133dbf` ✓ | odcs-open-data-contract-standard |
| `27b65335` | `27b65335` ✓ | slsa-specification-v1-0 |
| `8dce1f53` | `8dce1f53` ✓ | ddi-codebook-specification |
| `17f166d8` | `17f166d8` ✓ | akamai-datastream-2-docs |
| **`ce774778`** | **`ce574778`** ✗ | digital-gov-website-standards |
| `e31c911d` | `e31c911d` ✓ | itu-ai-ready-analysis… |

`ce774778` does not exist — a digit transposition of `ce574778`, which the task file itself
anticipated ("verify exact id from graph"). Nothing was closed against the wrong id. Eight
further gap tasks appear in the graph and are **not** part of this set: they are the
fixture-doc_id artifacts from the ingestion task's own incident, already superseded there.

## 1. Acquisition

Rule applied: canonical fullest source, native markdown/text over rendered HTML over
PDF-of-HTML. Every source was verified live rather than inherited from the task's direction,
per its own instruction.

| document | source | sections | visible chars |
|---|---|---:|---|
| odcs-open-data-contract-standard | GitHub `bitol-io/open-data-contract-standard` **@v3.1.0**, `docs/*.md` | 12 | 2,630 → **76,744** |
| slsa-specification-v1-0 | GitHub `slsa-framework/slsa` **@v1.0.0**, `docs/spec/v1.0/*.md` | 16 | 2,016 → **131,684** |
| ddi-codebook-specification | GitHub `ddialliance/ddi-codebook-docs`, `documentation/src/**.rst` via pandoc | 15 | 7,139 → **34,851** |
| akamai-datastream-2-docs | the site's own `llms.txt` index + its `.md` suffix convention | 48 | 1,790 → **321,628** |
| digital-gov-website-standards | `standards.digital.gov/sitemap.xml`, each page via docling | 11 | 1,962 → **31,358** |
| itu-ai-ready-analysis… | **not acquired — cut with reason** | — | 1,353 (unchanged) |

Four of five needed no converter at all: the publishers keep the canonical text in markdown,
which is the whole point of preferring native source. DDI's reStructuredText goes through
pandoc; digital-gov's HTML through docling — the DD-030 registry's own tool, reused rather
than reimplemented (Section 7, and the ingestion RESULT already measured docling ahead of
pandoc and trafilatura on exactly this kind of page).

**Substrate shape: merged single file per doc_id**, decided once and recorded in
`scripts/extent_remediation.yaml`. The task fixes `doc_id`, and a doc_id is one entry with one
canonical path; per-subpage substrate would need new doc_ids and would split `crosswalk_demand`
across entries the crosswalk does not name. DD-023 makes the chunk the extraction unit and the
chunker is heading-aware, so sections written as H1s chunk exactly where per-page substrate
would have. Citation survives because every section carries its own source URL in-band.

### 1.1 The akamai extent decision, measured before deciding

The llms.txt index enumerates 136 pages / **4,826,195 chars**. Acquiring all of it would have
produced the largest document in the corpus by a wide margin — roughly 1,000 chunks — at
**zero crosswalk demand**. The split:

| section | pages | chars |
|---|---:|---:|
| `/reference/` | 58 | 4,243,618 |
| `/docs/` (Guides) | 48 | 348,341 |
| `/recipes/` | 20 | 209,018 |
| `/changelog/` | 10 | 8,978 |

Acquired the **Guides only**. "Within reason" is the task's phrase and this is the reason:
`/reference/` is 88% of the bulk and all of it request/response endpoint schemas, which
contribute no definition, construct or instrument to a KG about AI-readiness. Taking it would
also have contradicted a live scope decision made two hours earlier, when three ~200-chunk
documents were deferred `below_burn_scope` on precisely this cost-per-demand ground
(ADDENDUM-02 §2).

### 1.2 ITU — cut with reason, and the search that failed

The publication is served only through ITU's JavaScript e-publications reader. The page
carries no PDF or download link. Probed and 404: `api/static/<slug>/en/` ×
{`content.json`, `toc.json`, `index.html`, `document.pdf`, `main.pdf`, bare}, plus
`api/publication/<slug>{,/en}` and `api/epub/<slug>/en`; and a link extraction over the page
HTML for any `pdf`/`download` href found only language variants of the same landing page. The
static API is real — it serves the cover image — but exposes no content path.

Recorded as an `extent_unremediable` event carrying the list of what was searched, because
"unreachable" is a claim that needs its failed search attached. The document carries zero
crosswalk demand, and the task's own instruction governs: *"cut-with-reason is the correct
outcome, not heroics."*

## 2. Gate verdicts and verification

`python -m kg.ingest.gate --doc <id>`:

```
OK    odcs-open-data-contract-standard        passthrough
OK    slsa-specification-v1-0                 passthrough
OK    ddi-codebook-specification              passthrough
OK    akamai-datastream-2-docs                passthrough
OK    digital-gov-website-standards           passthrough
GAP   itu-…  thin_extent_suspected — visible text 1,353 < 2,000   task=e31c911d
```

**5/6 clear; the sixth fails correctly** — it was not remediated, and a gate that passed it
would be broken. `verify_substrate()` returns `ok: True` for all five re-acquired documents
against their recorded `source_sha256`. Open gaps corpus-wide: **6 → 1**.

Both ledgers agree on all six canonical paths (dixie projection vs event-log replay), which is
the check that matters after a re-acquisition touches both.

## 3. Three defects found and fixed

### 3.1 `content_update` wrote to the wrong shard, and it broke replay

The crosswalk lane's admissions live on `batch-017` (DD-008 shards by ingest batch), but
`content_update` hardcoded `_MANIFEST_BATCH = 1`. `replay()` orders by shard number, so the
supersession arrived **before** the admission it superseded and `_load_entries()` raised
`content_update for 'odcs-…' which has no manifest_add event` — on every call, for every
caller, after the first crosswalk document was superseded.

Latent since DD-008: no document outside shard 1 had ever been superseded. **Shard order is
not causal order.** Supersessions are now collected during replay and applied after it, so
placement cannot matter; the guard still raises for a genuinely orphaned supersession, which
is what it was actually for. Supersessions also now land on the admission's own shard, so a
reader following one document is not sent to two.

The already-written odcs event was left exactly where it is (invariant 1) and now replays
correctly.

### 3.2 Batch identity moved a fourth time — and this one ends the argument

Making five unreadable captures readable put them into `document_chunk_counts()`, which
`resume_plan` filters identity by. `bulk_v038_b001` came to mean **`odcs`**, the plan grew to
14 batches, and every id shifted — while the burn was running with 2,504 events stamped with
the old meaning. The running process held its plan in memory, so nothing was corrupted; a
restart would have quarantined the wrong events.

Four failures, one shape:

| # | identity derived from | what moved it |
|---|---|---|
| 1 | remaining chunk counts | finishing batch 1 renamed it (caught mid-dispatch) |
| 2 | `queue.worklist()` | a fully-extracted document dropped out |
| 3 | `queue.live_requests()` | deferring six documents for scope |
| 4 | `d in counts` (readability) | **this task**, making five captures readable |

Each fix made the derivation cleverer. The actual lesson is that a batch id is **stamped into
provenance** and is what a quarantine names — it is a fact, not a derived value, and facts
belong on the append-only log. The plan is now cut once and recorded as `burn_plan_cut`
(schema v0.3.8); later cuts **append** batches after the highest id and never renumber.

The 13-batch plan was reconstructed with the remediated documents excluded and **verified
against stamped provenance before being frozen** — b001–b004 match the ids on already-ingested
`chunk_metrics` events exactly. The two newly-readable *requested* documents appended as
`b014` (odcs, 45 chunks) and `b015` (slsa, 32 chunks), both already deferred, so they dispatch
nothing and cost nothing while holding stable ids for whenever they are wanted.

### 3.3 The live consistency check was looking at the wrong plan

`test_batch_membership_matches_what_provenance_already_records` compared provenance against
`batches()` — the raw cut — not against the plan the burn actually uses, and it checked only
`b001`. It caught this shift by luck, because the renumbering happened to reach b001. It now
checks **every** stamped batch id against `cut_plan`, so a shift is caught wherever it lands.

## 4. Tests

The task asked for the re-acquired documents as positive controls and the old captures kept as
fixtures. Both are now **vendored** into `tests/fixtures/extent/` rather than read from
`corpus/`:

* `test_link_density_is_what_catches_slsa_not_the_text_floor` used to read
  `corpus/crosswalk/slsa-specification-v1-0.html` behind a `pytest.skip`. **This task
  quarantined that file**, so the control silently stopped running at the exact moment its
  subject was replaced — the suite went from 578 passed to 577 passed + 1 skipped, which is
  the only reason it was noticed. `corpus/` is gitignored, so a live-file control can never be
  durable.
* `test_every_superseded_capture_still_fails_the_gate` — all three superseded captures must go
  on failing.
* `test_a_reacquired_specification_passes_the_same_gate` — real bytes from the ODCS v3.1.0
  markdown must pass, because a gate that rejects everything passes a suite of rejections.
* `test_the_two_features_split_the_superseded_captures_between_them` — pins that neither
  Kohlschütter feature is redundant, now with real documents on both sides: slsa clears the
  text floor by 16 characters and is caught by link density; digital-gov's hero page has low
  link density (crawl4ai stripped the anchors) and is caught only by the text floor.

Plus three tests for the frozen plan, including one that drives the exact change this task
made — a document becoming readable and sorting first — and asserts no existing id moves.

**Mutations: 9/9 caught** (5 across the manifest replay/shard and gate thresholds, 4 across
the frozen plan), each by the test that should catch it. One mutation was initially "caught"
by an unrelated bulk test rather than a relevant assertion; chasing that incidental failure is
what surfaced §3.2, so it is recorded rather than tidied away.

**Suite: 584 passed.**

## 5. Queue reconciliation — deferred, per the task's liveness gate

The task gates this item on no bulk process being alive. **A burn was alive throughout**
(`run_chunked_bulk.py --phase burn`, pid 54119, confirmed at open and at close), so the queue
was not touched here.

It is also already done: `odcs` and `slsa` were withdrawn and deferred with reason
`conversion_gap` at the close of the ingestion task, when no burn was running. Their state is
correct and needs no further change. What remains for the next burn start is the substrate
wiring in §6 — and, now that both documents have real substrate, a decision about whether to
revive their extraction requests (4 crosswalk demand between them). That is a scope decision,
not a mechanical one, and it belongs with whoever starts that burn.

## 6. Explicitly not done

Extraction requests; substrate wiring into `doc_text`; any edit to a running-burn file. All
three remain owned by the next burn start (ingestion RESULT §3), unchanged by this task.
Gate thresholds were not touched: six true positives remain the evidence that they sit right,
and moving them needs its own task with its own measurement.

## 7. Burn state at close (context, not this task's work)

`bulk_v038` continued throughout: b001–b004 all **accept** (b004 at the first increment, 0
fabrications / 55 facts), b005 correctly skipped as deferred. Nothing in this task touched the
burn's files, spend, or queue.
