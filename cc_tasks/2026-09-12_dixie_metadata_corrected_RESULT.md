# RESULT — dixie gains a correction event, its handler, and `acquired_at` from the ledger

**Task:** `cc_tasks/2026-09-12_dixie_metadata_corrected.md`. No addendum exists; globbed before
starting and again before §3, both times empty.
**Date:** 2026-09-12 UTC. **Spend:** zero model calls. **Network: NONE** — no host of any kind was
contacted; the only sockets opened were the local Neo4j bolt connection (`seldon verify`).
**Outcome: the gate passed, with one of its clauses corrected against the ledger — see §1.**

---

## 1. The one clause of the gate that does not hold as written, and why it is a premise defect

Decision 3: *"After the change, `build_manifest` over the existing ledger yields **0 null
`acquired_at`**"*, and §3's gate repeats it.

**It yields 93 null out of 377, and every one of those 93 is correct.** They are
`screening_imported` candidates the corpus never acquired:

| the 93 | |
|---|---|
| lifecycle stage | `cataloged`, all 93 |
| `identity.canonical_path` | `None`, all 93 |
| `file_observed` events in the ledger | **none**, for any of them |
| screening decision | `excluded` 64, `pending_refetch` 29 |
| `acquisition.method` after the change | `unknown`, all 93 |

There is no attestation to read a timestamp from, and writing one would be the thing dixie's own
doctrine forbids in as many words: *"Unknown provenance is recorded as unknown. Fields may be
null; they may not be guessed."* (`README.md`). The manifest's TOTALITY axis exists precisely so
a never-acquired candidate stays in the ledger rather than vanishing; an acquisition date on it
would assert the opposite of what the ledger holds.

**The invariant that is right, and that the change delivers:** *an entry the ledger attests a
file for carries the time it was attested.* That held for **0 of 284** such entries before and
holds for **284 of 284** after.

This is reported, not reconciled, and the threshold was not moved to make a number pass: the
clause rests on a factual premise ("all 377 have a `file_observed`") that the ledger contradicts.
Nothing was retuned — the fill writes where there is an attestation and nowhere else.

## 2. What changed in dixie

Commit `eeac6c4` on `main`, `/Users/brock/GitHub/dixie`.

**Decision 1 — the event type.** `metadata_corrected` in `eventlog.EVENT_TYPES`, payload
`{doc_id, fields, provenance}`. `fields` keys are `<section>.<field>` with section in
`CORRECTABLE_FIELD_PREFIXES = ("identity", "acquisition")`; anything else is refused **at
append** by `_validate_metadata_corrected`, through a new per-type `_PAYLOAD_VALIDATORS` hook.
Append-time and not replay-time because the log is append-only: an event the projection will
reject cannot be retracted, only shadowed.

Two deviations from the decision as written, both forced by the data:

* **The before-values are not in the payload.** The decision lists them as a payload field
  *"captured by the handler"*, which cannot both be true. The handler captures them onto the
  entry (§2, decision 2); the event carries only what the operator asserts.
* **A correction value may be a flat list, not only a scalar.** `identity.authors_or_org` is a
  list on **370 of 377** manifest entries, and the FCSM document's own recommended citation names
  six people. A scalar-only rule would have forced a type change on the field rather than
  correcting it. Mappings stay refused — `identity.signals` is written by the connector that
  measured it, and a correction able to replace it wholesale is a merge conflict, not a citation
  fix.

**Decision 2 — the handler and the no-handler test.** `ManifestProjection._on_metadata_corrected`
overlays the fields, appends `{ts, provenance, fields: {dotted: {before, after}}}` to
`entry["extra"]["metadata_corrections"]`, re-indexes (so a corrected `source_url` resolves), and
**raises** on a doc_id the projection does not hold and on a leaf the entry does not have.

The decision's literal test — *"an event type in `EVENT_TYPES` with no `_on_` handler fails the
suite"* — **fails today on a type that is correct**: `note` is a free-form annotation and has no
projection effect by construction. So the guard is stated as a partition rather than a
prohibition: `manifest.INERT_EVENT_TYPES` declares the types that are deliberately inert, and
`tests/test_projection_handlers.py` holds `EVENT_TYPES == handlers ∪ INERT_EVENT_TYPES`. The hole
is also closed in the code, not only in the test: **`apply()` now raises** for a type that is
neither handled nor declared inert, where it used to `return` silently.

**Decision 3 — `acquired_at` from the ledger.** `_on_file_observed` sets
`acquisition.acquired_at = ts` when the field is null, and `acquisition.method =
FILE_OBSERVED_METHOD` (`"attested_by_file_observed"`) when the method is `unknown`. It fills a
null and never overwrites, so an earlier `inbox_ingested` keeps its own timestamp and
`manual_drop`.

This collided with one standing assertion — `tests/test_sweep.py` asserted
`method == "unknown"` on an unprovenanced drop, with the rationale *"provenance never
invented"*. The assertion was amended, not deleted, and the comment says why the new label
**sharpens** the signal instead of losing it: `unknown` used to conflate two different states,
and after the change it names only one of them.

| state | before | after |
|---|---|---|
| never acquired, nothing to explain | `unknown`, `acquired_at: None` | `unknown`, `acquired_at: None` |
| acquired, channel never recorded | `unknown`, `acquired_at: None` | `attested_by_file_observed`, timestamped |

**Decision 4 — the diff is pinned.** `test_the_fill_changes_nothing_but_the_two_acquisition_fields`
builds the projection twice from one fixture ledger — once as written, once with the acquisition
write neutralized by restoring each entry's `acquisition` block after every `_on_file_observed`
call — and asserts the changed-path set is exactly
`{acquisition.acquired_at, acquisition.method}`. No copy of the old handler body exists to go
stale. `scripts`-free; the same comparison is run against the **real** ledger in §3.

Version bumped `0.2.0 → 0.3.0`, matching this repo's own convention of a version per feature.

**Files:** `src/dixie/evidence/eventlog.py` (+64), `src/dixie/evidence/manifest.py` (+72/-2),
`pyproject.toml` (+1/-1), `tests/test_sweep.py` (+13/-2), and three new test files —
`tests/test_metadata_corrected.py` (172 lines), `tests/test_acquired_at_fill.py` (133),
`tests/test_projection_handlers.py` (40).

## 3. The gate

**dixie's own suite, in full: 90 passed, EXIT=0** (`logs/dixie_suite.log`). Every pre-existing
test is green; the one that moved is named in §2.

**Replay of this repo's actual ledger, read only** (`logs/dixie_replay_diff.log`,
`corpus/evidence/decisions.jsonl` opened for reading and never written — `git diff` on it is
empty):

```
entries: before=377 after=377
--- fields changed by the dixie change ---
  acquisition.acquired_at: 284 entries
  acquisition.method: 26 entries
null acquired_at: before=377 after=93
filled: 284   by attesting handler: file_observed 284, inbox_ingested 0
```

**No field outside `acquisition` moved on any of the 377 entries** — the script exits non-zero if
one does. `acquisition.method` moved on 26: the entries whose import record named no channel.
The other 258 fills kept the channel their import record already carried (`httpx-pdf` 63, `crwl`
49, `bulk_fetch` 40, `scripted_fetch` 37, `httpx-raw` 28, `crawl4ai_markdown` 18, `httpx-dom` 10,
`doc_pattern_pdf` 5, and six more in ones and twos).

**Consumer unchanged.** Nothing in `ai-readiness-kg` was edited by this task; `kg/`, `tests/`
and `scripts/` are absent from the commit (§6).

## 4. How `ai-readiness-kg` consumes dixie — decision 5

**Editable install, unpinned and undeclared.** `pip show dixie` reports
`Editable project location: /Users/brock/GitHub/dixie`, and
`/opt/anaconda3/lib/python3.12/site-packages/__editable__.dixie-0.1.2.pth` puts the working tree
itself on `sys.path`. Verified from the consumer:

```
consumer imports dixie from: /Users/brock/GitHub/dixie/src/dixie/__init__.py
metadata_corrected visible to consumer: True
handler present: True
```

**So the consumer must change nothing to pick this up** — it already has it, uncommitted changes
included. Two things about that are worth recording rather than assuming:

1. **`ai-readiness-kg` does not declare dixie as a dependency anywhere.** There is no
   `requirements.txt`, and `pyproject.toml` does not name it. The dependency is ambient: it works
   because someone ran `pip install -e` once. A fresh clone has no instruction that would install
   it, and `kg/manifest.rebuild` fails loud with the right message when it is missing — which is
   the only reason this has never bitten.
2. **`pip show dixie` reports 0.1.2, which is not the code being imported.** The dist-info was
   never refreshed after the 0.2.0 bump and will not be after 0.3.0 either. Anything that gates
   on the installed *version* rather than on an imported symbol will read a number two releases
   stale. Nothing in either repo does today.

Neither is fixed here — this task's zero-edits list forbids touching the consumer. Both belong in
the next task that is allowed to.

## 5. Every premise the task file got wrong

1. **Decision 3's "0 null `acquired_at`"** — 93 remain and correctly so (§1).
2. **Decision 3's "An entry with an earlier `inbox_ingested` keeps that value"** — true in the
   code and **vacuous on this ledger: it contains zero `inbox_ingested` events.** All 284 fills
   come from `file_observed`. (The counts the *next* task's decision 3 asks for — "filled by
   `file_observed` versus `inbox_ingested`" — are therefore 284 and 0.)
3. **Decision 2's no-handler test as literally specified** would fail on `note`, a type that
   correctly has no handler (§2).
4. **Decision 1's payload carrying "the before-values captured by the handler"** — those are two
   different places; the handler's capture lands on the entry (§2).
5. **Decision 1's "any other key path is refused at append"** did not anticipate that the field
   most in need of correction is multi-valued; the rule had to admit a flat list (§2).
6. **Decision 3 silently contradicts a standing assertion** in `tests/test_sweep.py` whose stated
   rationale is a doctrine line. Amended with the reasoning on the face of the test (§2).
7. **The task's framing "`acquired_at` is null on all 377 entries because only
   `_on_inbox_ingested` sets it"** is exactly right, and was re-verified rather than assumed.
8. **Decision 5 expected a pin to report** ("editable install, pinned tag, path"). It is the
   first of those, and the more useful finding is that there is no declaration at all (§4).

## 6. Verification

Everything below ran to completion before this file was written; every log is on disk.

```
logs/dixie_suite.log              dixie: python -m pytest tests/ -q
                                  90 passed in 0.34s                              EXIT=0
logs/dixie_replay_diff.log        read-only replay of corpus/evidence/decisions.jsonl
                                  through the new projection; diff summary in §3   EXIT=0
logs/suite.log                    make gate-full — 1994 passed, 17 skipped,
                                  12 xfailed, 1311.37s, detached and polled        EXIT=0
logs/dixie_metadata_verify.log    seldon verify — all checks passed                EXIT=0
logs/dixie_metadata_protected.log the zero-edits list, asserted on the staged set
                                  "PASS nothing outside this task's declared
                                   surface is staged or moved"                     EXIT=0
```

`gate-full` ran against the tree this commit publishes: the dixie change is live in it (editable
install), and the only `ai-readiness-kg` content in the commit is this RESULT and its task file.
The `kg/`, `tests/` and `scripts/` edits in the working tree belong to
`2026-09-12_cited_documents_metadata_2.md`, were written while this suite ran, and are
deliberately **not** staged here — the protected check refuses the commit if they are.

changed (dixie): `eventlog.py`, `manifest.py`, `pyproject.toml`, `tests/test_sweep.py`.
new (dixie): `tests/test_metadata_corrected.py`, `tests/test_acquired_at_fill.py`,
`tests/test_projection_handlers.py`.
new (here): this RESULT.
untouched: `corpus/` entire — bytes, hashes, `corpus/manifest.json` and
`corpus/evidence/decisions.jsonl` are byte-identical to HEAD; `events/`, `framework/`,
`assessment/`, `state/`, every prior RESULT, every section file, the skeleton, the record.

## 7. What the next task needs

`2026-09-12_cited_documents_metadata_2.md` runs next, and two of its clauses inherit §1:

* its decision 3, *"`acquired_at` is filled for all 377"*, and its §3 gate, *"0 null
  `acquired_at` across 377"* — the true figures are **284 filled, 93 correctly null**;
* its decision 4's test, *"forbids null `acquired_at` on every entry"* — the testable invariant
  is *on every entry the ledger attests a file for*, which is what
  `tests/test_manifest_acquisition.py` asserts.

Both are carried into that task's RESULT as premise defects rather than reconciled in silence.
