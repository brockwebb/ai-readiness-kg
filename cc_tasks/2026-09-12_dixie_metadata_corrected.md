# CC Task — dixie: a metadata-correction event, its projection handler, and `acquired_at` from the ledger

**Date:** 2026-09-12
**Project:** ai-readiness-kg (work is in `/Users/brock/GitHub/dixie`; registered here because this repo's publication waits on it)
**Authored by:** Desktop session, OODA on `2026-09-12_cited_documents_metadata_RESULT.md` §1, §2, §6 item 1.
**Implements:** DN-002 decision 4 (`docs/design/2026-09-12_DN-002_publishing_l0.md`); under DD-001 and DD-003 (the ledger is the corpus ledger; the manifest is its projection).
**Fulfils:** its own ResearchTask (`seldon cc register`). Precedes `2026-09-12_cited_documents_metadata_2.md`.
**Spend:** zero model calls. **Network: none.**

**Why this task exists.** The manifest's identity and acquisition fields reach an entry only at `screening_imported`; there is no correction event, and a correction event without a handler would append and silently do nothing. `acquired_at` is null on all 377 entries because only `_on_inbox_ingested` sets it; `_on_file_observed` holds the same timestamp and writes `canonical_path` and `sha256` from it.

**Decisions taken here (operator overrides later):**
1. **New event type `metadata_corrected`** in `eventlog.EVENT_TYPES`, payload: `doc_id`, `fields` (dotted keys under `identity.*` or `acquisition.*` only), `provenance` (free text naming where on the document each value was read), and the before-values captured by the handler. Any other key path is refused at append.
2. **`ManifestProjection._on_metadata_corrected`** overlays the fields, records `before` per field on the entry's provenance note, and refuses (raises, does not ignore) a doc_id the projection does not hold. A test asserts that an event type in `EVENT_TYPES` with no `_on_` handler fails the suite, so the silent-ignore path cannot recur for any future type.
3. **`acquired_at` is set from the ledger, with its meaning stated.** `_on_file_observed` sets `acquisition.acquired_at` to the event's `ts` when the field is null, and sets `acquisition.method` to `attested_by_file_observed` when method is `unknown`. This is not a guess: it is the earliest ledger attestation that the bytes existed, and the label says so. An entry with an earlier `inbox_ingested` keeps that value. After the change, `build_manifest` over the existing ledger yields 0 null `acquired_at`; a test asserts it against a ledger fixture with both paths.
4. **Idempotent replay.** Rebuilding the projection from the unchanged ledger is byte-identical before and after this change except for the `acquisition` fields decision 3 fills; a test pins that diff.
5. **How `ai-readiness-kg` consumes dixie is reported, not assumed** (editable install, pinned tag, path): the RESULT states it and what the consumer must change to pick this up; the consumer is not changed here.

**Zero edits to:** ledger files, any consumer repo, existing event types' semantics.

**Immutable once written. Glob `2026-09-12_dixie_metadata_corrected_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 2. Event type, handler, the no-handler test.
## 2. Decisions 3, 4, 5.
## 3. Gate (the one gate of this task)
dixie's own suite green in full; the no-handler test; the two projection tests; replay of `ai-readiness-kg`'s actual ledger (`corpus/evidence/decisions.jsonl`, read only) through the new projection yields 0 null `acquired_at` and no other field changed, shown as a diff summary; consumer unchanged.
**Failure writes nothing in dixie: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-12_dixie_metadata_corrected_RESULT.md` in this repo: the dixie commit; the replay diff summary; how the consumer pins dixie; every premise wrong. `seldon cc complete` here, commit, push both repos.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
