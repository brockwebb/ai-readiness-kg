# RESULT — the correction verb, the backfill, and the tests that follow it

**Task:** `cc_tasks/2026-09-12_cited_documents_metadata_2.md`. No addendum exists; globbed before
starting and again before §3, both times empty.
**Date:** 2026-09-12 UTC. **Spend:** zero model calls. **Network: NONE** — no host of any kind was
contacted; the only sockets opened were the local Neo4j bolt connection.
**Outcome: the gate passed, with two of its clauses corrected against the ledger — see §1.**

Runs after `2026-09-12_dixie_metadata_corrected.md` (dixie `eeac6c4`, this repo `99e8198`), whose
gate passed. `e6765ba6` is **closed** (§5).

---

## 1. The two clauses that do not hold as written

Both inherit the premise defect named in the preceding task's RESULT §1, and both are reported
rather than reconciled. No threshold was moved.

**Decision 3, "`acquired_at` is filled for all 377", and §3's "0 null `acquired_at` across
377".** The true figures: **284 filled, 93 correctly null.** The 93 are candidates the corpus
never acquired — lifecycle stage `cataloged`, no `canonical_path`, and **no `file_observed` event
of any kind** in the ledger (`excluded` 64, `pending_refetch` 29). There is no attestation to
read a time from, and inventing one is what dixie's doctrine forbids in as many words: *"Fields
may be null; they may not be guessed."*

**Decision 4's test, "forbids null `acquired_at` on every entry".** The testable invariant is *on
every entry the ledger attests a file for*. `tests/test_manifest_acquisition.py` asserts it in
both directions, so the loosening cannot hide a real gap:

| test | holds |
|---|---|
| every acquired entry carries an acquisition time | 284 of 284 |
| an entry with no file is **null rather than guessed** | 93 of 93 |
| an acquisition time never stands beside `method: unknown` | 0 violations |
| a document acquired from 2026-09-12 names its channel (not `unknown`, not the `attested_by_file_observed` fallback) | 0 violations |

**Decision 3's "the count filled by `file_observed` versus `inbox_ingested`": 284 and 0.** The
ledger contains **zero `inbox_ingested` events**. Its 1,336 events at HEAD were
`screening_imported` 599, `integrity_checked` 327, `file_observed` 320, `quarantined` 43,
`screening_decided` 28, `corpus_epoch_declared` 13, `note` 4, `duplicate_group_found` 2.

## 2. Decision 1 — the entry point

`kg/manifest.py::metadata_update(doc_id, *, provenance, **sections)`, CLI verb
`python -m kg.manifest metadata-update`. It appends `metadata_corrected` to the **Dixie evidence
ledger** through `dixie.evidence.eventlog.EventLog.append`, never to `events/batch-*.jsonl`.

**One deviation from the signature as written.** The decision says `**fields` with dotted keys;
`identity.pub_year` is not a Python identifier, so fields are passed **by section** —
`metadata_update(doc_id, provenance=..., identity={"pub_year": "2022"})`. The CLI keeps the
dotted form the event itself uses: `--set identity.pub_year=2022`, repeatable.

Every refusal is checked **before anything is written**, because the ledger is append-only and an
event the projection will reject cannot be retracted, only shadowed: a `doc_id` not in the ledger
projection, a section outside `identity`/`acquisition`, a leaf the entry does not have, an empty
correction, an empty `provenance`. Sixteen tests in `tests/test_manifest_acquisition.py` hold
them, and they run against the real ledger precisely because each raises before an append.

Values stay **strings**: `pub_year` is a string on 363 of 377 entries and `authors_or_org` a list
on 370, so `_parse_set` splits on commas by default and `--scalar` turns that off for a title
that contains one. A verb that silently retyped a field would make the corrected entry differ in
shape from every other.

**§1's stop condition did not fire: the consumer sees the dixie change.** `dixie` is an editable
install whose `.pth` puts `/Users/brock/GitHub/dixie/src` on `sys.path`, so
`metadata_corrected in EVENT_TYPES` is `True` from this repo with nothing to bump. The dry run
(one correction against a **copy** of the real ledger, the original untouched) showed the event,
the projected entry carrying `{"before": "n.d.", "after": "2022"}`, and the citation going from
one missing field to none.

## 3. Decision 2 — the backfill, per doc_id

Six corrections written, each read off the document on disk this session. `scripts/backfill_
citation_metadata.py` carries the values and the full provenance strings; the ledger event carries
them verbatim.

| doc_id | field → value | read from |
|---|---|---|
| `rfc-9309-robots-exclusion-protocol` | `pub_year` → `2022` | md line 13 `September 2022`; line 43 `Copyright (c) 2022 IETF Trust` |
| `schema-org-dataset` | `pub_year` → `2026` | md line 1009, page footer `• Schema.org • V30.0 \| 2026-03-19` |
| `cloudflare-ai-crawl-control-manage-crawlers` | `pub_year` → `2026` | md line 6, the docs page's own last-updated stamp `Jul 28, 2026` |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | `pub_year` → `2023`; `authors_or_org` → `Mirel LB; Singpurwalla D; Hoppe T; Liliedahl E; Schmitt R; Weber J` | PDF page 1, the document's own **Recommended citation** |
| `foundations-…-evid` | `pub_year` → `2019`; `authors_or_org` → `115th Congress` | PDF page 1 lines 1–3, `132 STAT. 5529 PUBLIC LAW 115–435—JAN. 14, 2019` / `Public Law 115–435` / `115th Congress` |
| `m-25-05-…` | `pub_year` → `2025`; `authors_or_org` → `Office of Management and Budget` | PDF page 1, `EXECUTIVE OFFICE OF THE PRESIDENT / OFFICE OF MANAGEMENT AND BUDGET`, `January 15, 2025`, `M-25-05` |

Both federal documents were **re-read from page 1 of the PDF this session** rather than taken
from the prior RESULT's quotation of them; both matched.

**FCSM 23-02 takes its named authors, not its issuing body.** Decision 2 says the issuing body
counts as author for federal documents, which unblocks the two that name none. This one names six
people in its own recommended citation — the document's own instruction on how to cite it is the
stronger grounding, so it is used and the committee is not substituted for it.

**Four cited documents keep `n.d.`, because the document does not state the field.** Each was
searched exhaustively for a four-digit year; the two short ones were also read end to end.

| doc_id | what was searched, what was found |
|---|---|
| `anthropic-crawler-support-article` | 33 lines, read in full: no date, no copyright line, no revision stamp |
| `perplexity-crawlers` | 62 lines, read in full: none |
| `bing-webmaster-guidelines` | 184 lines: the only year is a forward-looking API retirement notice (`August 31, 2026`), which dates an event the page announces, not the page |
| `openai-crawlers-bots` | 490 lines: none; the page offers an RSS feed *"for updates to this page"* and states no date of its own |

The harvest timestamp is **not** used for these. It records when we fetched the page, which is a
different claim wearing the same field name. This is not a to-do list: no future task can supply
the value without re-acquiring the document from a publisher that states it.

## 4. Decision 3 — rebuild, projection; and the manifest diff

`python -m kg.manifest rebuild` → 377 entries. `python -m kg.manifest verify` → *"clean: all local
files present and unchanged"* (it re-hashes every entry, which is how the corpus **bytes** are
asserted: the document binaries are gitignored, so no diff could speak for them).

Fields that moved in `corpus/manifest.json` against HEAD, and **nothing else did** — the diff
script exits non-zero if an unexpected field moves:

```
acquisition.acquired_at     284 entries      (284 by file_observed, 0 by inbox_ingested)
acquisition.method           26 entries      (the entries whose import record named no channel)
identity.pub_year             6 entries      (the six corrections)
identity.authors_or_org       3 entries
extra.metadata_corrections    6 entries      (the before/after + provenance note)
unexpected fields moved:   NONE
```

`scripts/build_projection.py` ran to `EXIT=0` — all three layers, framework 126 nodes / 280 edges,
`evidenced_by_missing_document: 0`. It reads `manifest_add` events from the kg event log, not
`corpus/manifest.json`, so it is a no-op with respect to this task's change; it was run because
decision 3 calls for it, and it confirms the graph still replays clean.

**The ledger only grew: 1,336 lines at HEAD → 1,342, all 1,336 byte-identical and in order**,
asserted by `scripts/check_protected_cited_metadata.sh` rather than claimed.

## 5. Decisions 4 and 5 — the tests, the report, the open task

**The tests follow the backfill, as the sequencing requires.** 19 new tests, all in the suite:

* `tests/test_manifest_acquisition.py` (16) — the four acquisition invariants of §1 against the
  real `corpus/manifest.json`, plus `metadata_update`'s refusals and the CLI `--set` parser.
* `tests/test_report_sources_appendix.py` (+3) — every cited doc_id renders `authors_or_org`,
  `title`, `pub_year` and `source_url`, **or** is in `CITATION_FIELD_NOT_STATED` with the field it
  is exempted for. Two further tests keep that list honest: it must equal the backfill script's
  `NOT_STATED` (one list, two places, neither free to drift), and **no exemption may survive the
  document gaining the field** — a stale exemption hides a real value.

**The appendix, before and after:**

| | HEAD | now |
|---|---|---|
| rows | 73 | 73 |
| distinct doc_ids | 59 | 59 |
| rows whose citation text changed | — | **12**, across the 6 corrected documents |
| cited docs missing ≥1 citation field | **10** | **4** |

The 4 are exactly the four of §3 that state no date. No row was added or removed; no doc_id
entered or left the appendix.

**Report rebuilt through `make report-pdf`** (which rebuilds the markdown first, so the appendix
is regenerated from the graph and the corrected manifest). Prose untouched — the only section
file in the diff is none; `docs/reports/sections/` is byte-identical to HEAD.

**Page counts did not move, so nothing was registered.** The rebuilt PDF measures
`{"total": 14, "prose": 6}`, identical to the registered `l0_report_pages_total_2026-09-11 = 14`
and `l0_report_pages_prose_2026-09-11 = 6`. Decision 5 says *"only if they moved"*, and they did
not. `scripts/register_report_page_counts.py` gained a `--epoch` flag so a future rebuild that
does move them can register under its own date; the hardcoded `EPOCH` it replaced was a standard-2
violation that would have forced an edit to register a second cycle.

**`e6765ba6` is closed.** `seldon task close e6765ba6` → `proposed → accepted → in_progress →
completed`. Its description is precisely this work — *"Recover timestamps … where it does not,
record the date as unrecoverable … never a back-filled guess. A manifest test forbids a null
`acquired_at` from now on."* — and this task did it, including the "never a back-filled guess"
clause, which is why the 93 stay null.

## 6. Every premise the task file got wrong

1. **Decision 3's "filled for all 377"** and §3's **"0 null across 377"** — 284 and 93 (§1).
2. **Decision 4's "forbids null `acquired_at` on every entry"** — the invariant is over acquired
   entries; asserted in both directions so nothing is hidden (§1).
3. **Decision 1's `metadata_update(doc_id, *, provenance, **fields)` with dotted keys** — a dotted
   key is not a Python identifier; fields are passed by section, and the CLI keeps the dotted form
   (§2).
4. **Decision 2's "Issuing body counts as author for federal … documents"** reads as a mandate but
   is a fallback. FCSM 23-02 names six authors in its own recommended citation and gets them (§3).
5. **§3's "tag-coverage lint"** — **no such gate exists in this repo.** `grep` over `scripts/`,
   `tests/` and the `Makefile` for `tag_coverage` / `tag-coverage` / "tag coverage" returns
   nothing. The two report lints that do exist both ran green: the **numeral-multiset gate**
   (`tests/test_report_pdf.py`, 2 passed) and the **bare-numeral lint** inside
   `build_l0_report.build`, which refuses to write the markdown when it fires.
6. **The prior RESULT's §4 item 6, "there is no supersede verb"** — true of `seldon cc`, and it
   led the task to hedge on how `e6765ba6` could be closed. **`seldon task` has `close`,
   `supersede` and `withdraw`.** The verb was in a different namespace, not absent.
7. **Decision 3's "`rebuild`, then the projection"** — `build_projection.py` does not read
   `corpus/manifest.json`, so it cannot carry a manifest correction into the graph. It was run
   anyway and is clean; the appendix gets the corrected identity from the manifest directly (§4).
8. **The task's count of "the ten citation gaps"** is right, and so is the prior RESULT's
   73 rows / 59 distinct documents — both re-counted here from the fragment on disk (§5).

## 7. Verification

Everything below ran to completion before this file was written; every log is on disk.

```
logs/citation_backfill.log          scripts/backfill_citation_metadata.py — 6 events
                                    appended, 4 not corrected with reasons        EXIT=0
logs/citation_rebuild.log           kg.manifest rebuild — 377 entries             EXIT=0
logs/citation_manifest_verify.log   kg.manifest verify — "clean: all local files
                                    present and unchanged" (re-hashes every entry) EXIT=0
logs/citation_manifest_diff.log     manifest diff vs HEAD; the five fields of §4,
                                    "unexpected fields moved: NONE"               EXIT=0
logs/citation_projection.log        scripts/build_projection.py — all three layers,
                                    evidenced_by_missing_document 0               EXIT=0
logs/citation_report_pdf.log        make report-pdf — wrote the md and the PDF
                                    (593,048 B), pages {"total":14,"prose":6},
                                    tests/test_report_pdf.py 2 passed             EXIT=0
logs/citation_gate_task.log         make gate-task — fast tier 1994 passed,
                                    17 skipped, 19 deselected, 12 xfailed, 378.8 s;
                                    re-derivation 16 passed, 6.7 s                EXIT=0
logs/suite.log                      make gate-full — 2013 passed, 17 skipped,
                                    12 xfailed, 1315.87 s, detached and polled    EXIT=0
logs/citation_verify.log            seldon verify — all checks passed             EXIT=0
logs/citation_protected.log         the zero-edits list + the append-only ledger
                                    check: "ledger: 1336 lines at HEAD, 1342 now,
                                    all 1336 unchanged"; PASS                     EXIT=0
```

`gate-full` grew from 1,994 to 2,013 passing: the 19 tests decision 4 adds. The preceding task's
`gate-full` (also green, 1,994) is preserved at `logs/suite_task1.log`.

changed: `kg/manifest.py`, `scripts/register_report_page_counts.py`,
`tests/test_report_sources_appendix.py`, `corpus/evidence/decisions.jsonl` (+6 lines, append
only), `corpus/manifest.json`, `docs/reports/2026-09_fss_ai_readiness_L0.md` and `.pdf`,
`docs/reports/generated/sources_per_check.md`, `seldon_events.jsonl`.
new: `scripts/backfill_citation_metadata.py`, `scripts/check_protected_cited_metadata.sh`,
`tests/test_manifest_acquisition.py`, this RESULT.
untouched: corpus document bytes and hashes (re-hashed clean), `events/` entire,
`framework/ai_readiness_framework.json`, `assessment/harness/`, `state/`, every rule module,
every payload, every figure, the skeleton, `docs/reports/sections/` entire, every prior Result
and prior RESULT.

## 8. What the next task needs

1. **`2026-09-12_publish_l0.md` was not started**, per the dispatch. DN-002 decision 4 made
   cited-document metadata a condition of publication; that condition now holds for 55 of the 59
   cited documents, and the remaining 4 render without a year because no year exists to render —
   a fact the appendix's own gate now records rather than tolerates. Its §1 stop (Result state
   transitions) is still untested and unknown.
2. **`ai-readiness-kg` does not declare dixie as a dependency.** No `requirements.txt`;
   `pyproject.toml` does not name it. The dependency is ambient — it works because someone ran
   `pip install -e` once — and `pip show dixie` still reports `0.1.2` against a tree at `0.3.0`.
   Carried forward unchanged from the preceding RESULT §4; no task so far has been allowed to
   touch it.
3. **26 entries now carry `attested_by_file_observed`.** That is honest for the pre-2026-09-12
   corpus and a defect for anything admitted after: the test forbids it on new admissions, so the
   next connector change that drops the channel will fail the gate rather than pass silently.
