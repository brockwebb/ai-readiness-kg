# RESULT — STOPPED AT §1: `kg/manifest.py` has no metadata-update verb, and a `manifest_update` event would not reach the manifest anyway

**Task:** `cc_tasks/2026-09-12_cited_documents_metadata.md`. No addendum exists; globbed before starting
and again before the gate, both times empty.
**Date:** 2026-09-12 UTC. **Spend:** zero model calls. **Network: NONE** — no host of any kind was
contacted; the only sockets opened were the local Neo4j bolt connection.
**Outcome: the §1 stop condition fired. No manifest change, no PDF, no report rebuild.**

---

## 1. The block, on top

Decision 3: *"**Manifest edits go through `kg/manifest.py`**, appending a `manifest_update` event per
entry with before/after; **if the module has no update verb, §1 stops** and the RESULT says what the
verb would need."*

**The module has no update verb.** `kg/manifest.py` knows exactly three event types —

| constant | value | what it writes |
|---|---|---|
| `_MANIFEST_ADD` | `manifest_add` | the admission payload |
| `_CONTENT_UPDATE` | `content_update` | `content_hash`, `local_path` only |
| `_PURPOSE_DECLARED` | `manifest_purpose_declared` | `purpose` |

— and **none of them writes `identity.*` or `acquisition.acquired_at`.** `grep` over the module for
`authors_or_org`, `pub_year`, `acquired_at` returns no write site; the only occurrences are a
`source_url` read in the convertibility gate and an `acquisition` passthrough in `add()`.

**The deeper finding, which the task's decision 3 does not anticipate: a `manifest_update` event
appended to the kg event log would be inert.** `kg.manifest.rebuild()` regenerates
`corpus/manifest.json` **wholly from the Dixie evidence ledger** (`corpus/evidence/decisions.jsonl`)
via `dixie.evidence.manifest.build_manifest` — its own docstring says *"Regenerate corpus/manifest.json
(v2) FROM THE DIXIE EVIDENCE DECISIONS LOG … this file is its projection."* The kg event log is the
extraction-admission gate; the ledger is the corpus ledger (this repo's CLAUDE.md invariant 2 says so).
So a kg-side metadata event would be written, would be replayed by `_load_entries()` into a *different*
entry shape, and would then be **overwritten on the very next `rebuild`** the task's own decision 3
calls for. The metadata would vanish between step one and step two.

Per the task's failure branch — *"Failure writes no manifest change and no PDF: report and stop"* —
nothing was written. `corpus/` is byte-identical to HEAD and `python -m kg.manifest verify` reports
*"clean: all local files present and unchanged"*.

## 2. What the verb would need

The verb spans **two repositories**, which is why it is not a one-line addition and why stopping was
right.

**In `dixie` (`/Users/brock/GitHub/dixie/src/dixie/evidence/`) — the ledger that owns the fields:**

1. **A new event type**, e.g. `metadata_corrected`, added to `eventlog.EVENT_TYPES`. The nine that
   exist are `corpus_epoch_declared`, `screening_imported`, `screening_decided`, `integrity_checked`,
   `duplicate_group_found`, `note`, `inbox_ingested`, `file_observed`, `quarantined` — **there is no
   correction event.** Identity reaches an entry only through `screening_imported`'s `normalized`
   block, i.e. only at import.
2. **A `_on_metadata_corrected` handler on `ManifestProjection`.** The projection dispatches by
   `getattr(self, f"_on_{event['event_type']}", None)`, so an event with no handler is silently
   ignored — a correction event without the handler would append and do nothing, which is worse than
   refusing. The handler overlays `identity.*` / `acquisition.*` and records the provenance note
   decision 1 requires (the page or line the value was read from).
3. **One line for `acquired_at`, which is a projection bug rather than missing data.**
   `_on_inbox_ingested` already does `entry["acquisition"]["acquired_at"] = ts`. The
   `screening_imported` path — how all 377 entries arrived — never sets it, so the blank template value
   `{"method": "unknown", "acquired_at": None, …}` survives. **`_on_file_observed` has the timestamp in
   hand** (it is the handler's `ts` parameter) and writes `canonical_path` and `sha256` from the same
   event; it is exactly the attestation "this file was on disk at this time".

**In this repo (`kg/manifest.py`) — the sanctioned entry point:**

4. `metadata_update(doc_id, *, provenance, **fields)` that validates the doc_id is admitted, refuses a
   field the document does not state (decision 1: *a value that is not on the document is not typed*),
   and appends the event to **the Dixie ledger** through `dixie.evidence.eventlog.EventLog.append`
   (signature `append(event_type: str, payload: dict) -> str`), **not** to `events/batch-*.jsonl`.
   Then `rebuild()`, then the projection.

**Sequencing the next task must not get wrong:** decision 2 wants a manifest test that *"forbids null
`acquired_at` on every entry from now on"*. **No such test exists today** (`grep acquired_at tests/`
returns only conversion-metadata fixtures in `test_ingest_convert.py`), and adding it before the
backfill would fail on **377 of 377** entries. The test follows the backfill; it cannot precede it.

## 3. The scope the verb has to cover, measured

Measured from `corpus/manifest.json` against the appendix on disk, and cross-checked independently
against the graph (both say 59 documents / 73 rows).

**The appendix cites 59 distinct documents, and all 59 are missing at least one required field** —
because `acquired_at` is null for every one of them. Splitting that:

| gap | count | detail |
|---|---|---|
| `acquired_at` null | **59 of 59** cited (**377 of 377** manifest-wide) | the projection never sets it on the `screening_imported` path (§2.3) |
| citation fields missing | **10 of 59** | the ten below |

The ten with a missing citation field — the same ten
`2026-09-11_report_sources_appendix_RESULT.md` §3 found, so that premise holds:

| doc_id | missing |
|---|---|
| `anthropic-crawler-support-article` | `pub_year` |
| `bing-webmaster-guidelines` | `pub_year` |
| `cloudflare-ai-crawl-control-manage-crawlers` | `pub_year` |
| `openai-crawlers-bots` | `pub_year` |
| `perplexity-crawlers` | `pub_year` |
| `rfc-9309-robots-exclusion-protocol` | `pub_year` |
| `schema-org-dataset` | `pub_year` |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | `authors_or_org`, `pub_year` |
| `foundations-for-evidence-based-policymaking-act-of-2018-evid` | `authors_or_org`, `pub_year` |
| `m-25-05-phase-2-implementation-of-the-evidence-act-open-gove` | `authors_or_org`, `pub_year` |

**The values are on the documents — the blocker is purely the write path.** Spot-checked this session
by reading page 1 of the two federal documents the report leans on for three checks (nothing was
recorded):

* `foundations-…-evid` — page 1 line 1: *"132 STAT. 5529 PUBLIC LAW 115–435—JAN. 14, 2019"*, then
  *"Public Law 115–435 / 115th Congress"*. Year **2019**; issuing body **115th Congress**.
* `m-25-05-…` — page 1: *"EXECUTIVE OFFICE OF THE PRESIDENT / OFFICE OF MANAGEMENT AND BUDGET"*,
  *"January 15, 2025"*, *"M-25-05"*, *"FROM: Shalanda Young"*. Year **2025**; issuing body **OMB**.

**`acquired_at` is recoverable for the corpus, and mostly to a real timestamp rather than
`unrecoverable`.** Per-document timestamps are in the ledger now — sampled:

| doc_id | `file_observed` | `integrity_checked` |
|---|---|---|
| `w3c-dwbp-2017` | 2026-08-21T21:49:15.787812Z | 2026-08-21T21:49:15.788132Z |
| `bing-webmaster-guidelines` | 2026-08-21T21:49:15.627907Z | 2026-08-21T21:49:15.628056Z |
| `foundations-…-evid` | 2026-07-05T08:05:43.364667Z | 2026-07-05T08:05:43.371420Z |

## 4. Every premise the task file got wrong

1. **Decision 3's "`kg/manifest.py` … appending a `manifest_update` event"** — no such verb, and the
   event log it names is not where the manifest's metadata lives. The edit has to reach the Dixie
   ledger or it does not survive `rebuild` (§1, §2).
2. **"Ten cited documents render in the appendix as title + URL"** — ten are missing a *citation*
   field, which is right; but **59** are missing something, because `acquired_at` is null on every
   cited document (§3).
3. **"`acquisition.acquired_at` is null for every kernel-harvested document"** — it is null for **every
   entry in the manifest, all 377**, whatever the acquisition method, including the `bulk_fetch` and
   `doc_pattern_pdf` federal documents. The cause is not the harvester; it is that the projection sets
   the field on only one of its handlers (§2.3).
4. **Decision 2's "recovered from the harvest logs (`scripts/harvest_kernel.py` output, Dixie ledger,
   git history of the corpus file)"** — of those three sources, **one exists**. No harvest log files are
   on disk (`logs/*harvest*` matches nothing); git history of a corpus file is unavailable because
   `corpus/bulk/` and `corpus/kernel/` are gitignored (`.gitignore:40`, `:43`). The Dixie ledger is the
   source, and it is sufficient (§3).
5. **Decision 2's "a manifest test forbids null `acquired_at` … from now on"** presumes the backfill
   has happened. Added today it fails 377 of 377 (§2, sequencing).
6. **§4's "Close `e6765ba6` as superseded by this task via the CLI"** — **not done, deliberately, and
   not for lack of a verb.** `e6765ba6-cc6f-4de4-8fd8-f4345bd2b672` is `state: proposed` and its
   description is precisely the `acquired_at` work. This task did not do that work, so marking it
   superseded would record the open item as closed and lose it. It stays `proposed`. (Separately,
   `seldon cc` exposes only `register`, `complete`, `constrain`, `rederive-description` — there is no
   supersede verb, though `superseded` is a state other ResearchTasks hold.)
7. **The appendix's distinct-document count.** `2026-09-11_report_sources_appendix_RESULT.md` §2 says
   *"All 51 distinct doc_ids"* at 65 rows. Re-counted from the committed fragment at that revision:
   **61 rows carrying a doc_id, 55 distinct**. After `19fdc4d` it is **73 rows, 59 distinct**, the four
   added being `foundations-…-evid`, `m-25-05-…`, `omb-m-23-22-…`, `bing-webmaster-guidelines`. The 51
   was a miscount; it is reported here rather than silently reconciled, and the prior RESULT is not
   edited.

## 5. Verification

Everything below ran before this file was written; nothing in the repo was modified by any of it.

```
logs/metadata_manifest_verify.log  python -m kg.manifest verify — "clean: all local files
                                   present and unchanged" (re-hashes every entry)      EXIT=0
logs/metadata_verify.log           seldon verify — all checks passed                   EXIT=0
logs/suite.log                     make gate-full — 1,994 passed, 17 skipped,
                                   12 xfailed, 1,242.3 s, detached and polled to EXIT  EXIT=0
git status --porcelain             only the two untracked task files, DN-002 and
                                   seldon_events.jsonl; corpus/, corpus/manifest.json,
                                   the PDF and the appendix are untouched
```

The gate of §3 was **not reached** — §1's stop is upstream of it. `gate-full` and `seldon verify` are
reported because this RESULT is pushed and CLAUDE.md requires the full suite before a push; they attest
that the tree this commit adds a document to is the green tree of `19fdc4d`, not that the task's own
gate passed.

changed: nothing.
new: this RESULT.
untouched: `corpus/` entire (bytes and hashes), `corpus/manifest.json`, `corpus/evidence/`, the skeleton,
the record, `events/`, every rule module, the harness, every payload, every figure, every section file,
`docs/reports/` entire, every prior RESULT.

## 6. What the next task needs

1. **Author the dixie-side change first** (§2.1–2.3): the `metadata_corrected` event type, its
   projection handler, and the `acquired_at` fill on `_on_file_observed`. It is a different repo with
   its own suite; this repo's gate cannot cover it.
2. **Then the `kg/manifest.py` entry point** (§2.4), then backfill, then `rebuild`, then the projection,
   then the report rebuild, **then** the test that forbids null `acquired_at`.
3. **`2026-09-12_publish_l0.md` was not started.** It declares *"Runs after
   `2026-09-12_cited_documents_metadata.md`"*, and DN-002 decision 4 makes cited-document metadata a
   condition of publication. Its own §1 stop (Result state transitions) is untested and unknown.
