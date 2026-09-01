# RESULT — Stub the FSS Machine Diagnostic into the crosswalk (conceptual level only)

**Task:** `cc_tasks/2026-09-01_machine_diagnostic_stub.md` · **Date:** 2026-09-01
**Spend:** zero model tokens. File edits and registration only; no extraction, no model call.
**Scope held:** 2 indicator rows, 1 design-stance item, 1 G1 sentence, 2 §9 entries, 1 version
note. Nothing else. Diff is **7 insertions, 2 modified lines** in one file.

## 1. Edits made

All in `docs/crosswalk/usafacts_operationalization_skeleton.md`, all verbatim from the task.

| step | location | change |
|---|---|---|
| 1 | §2 Criterion A table | rows **A10** (application/data-tool machine surface) and **A11** (declared/enforced/observed crawler access) appended after A8 |
| 2 | §6b | item **5** — observed facts vs versioned warning rules |
| 3 | §5d | one sentence appended to the G1 paragraph, naming A11 as G1's measurement template |
| 4 | §9 | two gap entries — the deferred rule-catalog crosswalk, and the A10 evidence gap |
| 5 | Status line | `v0.2.1 2026-09-01: …` version note |

Rows A1–A9 untouched; no renumbering. The internal draft is **not** manifest-admitted and no
`manifest_add` event was written — it appears only as the class-(c)-style inline reference the
task specifies, in the two new Evidence cells and in the §9 deferral.

## 2. Discrepancies between task premises and live state

Recorded, not reconciled.

**2.1 "Do not renumber or edit existing rows A1–A9" — A9 is not in the §2 table.**
A1–A8 are in §2. **A9 lives in §1b** as its own one-row "Added indicator" table (M2M agent
surface), added when the design-stance section was written. So the ID space *is* contiguous
(A9 → A10 → A11) and no renumbering was needed, but the §2 table now reads **A1–A8, A10, A11**
and a reader looking only at §2 will see A9 missing. Left as-is deliberately: the IDs are
load-bearing across this task's own edits — A11 is cited in the §5d sentence and A10–A11 in the
§9 entry — and renumbering to close the visual gap would have been a silent reconciliation of
three cross-references. Flagged so a future pass can decide whether §1b's row should move into
§2 (a formatting question, not a content one).

**2.2 The §2 table header is `Evidence (doc_id)`, not `Evidence`.**
The task's specimen table used `| Evidence |`; §1b uses that, §2 uses `| Evidence (doc_id) |`.
The task also said formatting must match the existing table exactly, so the live §2 header
governs. The new rows carry a non-doc_id value in that column (the internal draft), which is
what the admission decision requires and what A1's existing cell already does with its
`**gap** — named source … is acquisition_blocked` text. No header change made.

**2.3 The burn is *pausing*, not paused.**
The task says "the burn (paused; leave paused)". Measured at 11:53Z:

- `events/bulk_v038_STOP.json` exists, written **11:49:24Z** — operator halt, ADDENDUM-03,
  reason "burn running hot; pause at the batch seam to evaluate quality".
- `run_chunked_bulk.py --phase burn` (pid 9108) is **alive**, and the spend ledger shows two
  `reserve` records under `bulk_v038_b015` at **11:50:39Z and 11:50:41Z** — *after* the STOP
  file was written.

This is correct, designed behaviour, not a defect: the operator halt is checked **between
batches**, which is the seam where the previous batch is judged and recorded and the next has
not declared a ceiling. The burn will stop when b015 completes. The premise was simply written
in the ~4 minutes between the STOP file landing and the seam being reached. **Nothing in this
task touched the burn, its files, the event log, or `corpus/manifest.json`.**

## 3. `seldon verify` — it was crashing, and the cause was mine

The completion checklist's `seldon verify` did not run. It aborted with:

```
IsADirectoryError: [Errno 21] Is a directory: '…/state/refparse'
```

`check_file_hashes` reads `path` on **every** artifact and calls `read_bytes()` on it, with no
state filter and no directory guard. The offending artifact is `refparse-derived-references`
(`f7b38a38`), which **I registered on 2026-08-30** under
`cc_tasks/2026-08-30_acquisition_round2.md` with `path=state/refparse` — a *directory* of 194
derived JSON files, hashed with a directory digest. A `DataFile` cannot be a directory, and
nothing caught it because that task's checklist did not include `seldon verify`; it has been
broken for two days.

**Fix:** cleared `path` (the check skips a falsy path) and moved the directory onto a
`store_dir` property the hash check does not read. `content_hash` keeps the directory digest,
so the provenance record survives intact — what changed is that the store is no longer claiming
to be a file. The reason is recorded on the artifact's `note`.

`seldon verify` now completes:

```
✗ File hashes         3 modified: schema.yaml, manifest.json, manifest.json
✓ Ontology  ✓ Glossary  ✓ References  ✓ Stale artifacts  ✓ Blocking tasks  ✓ Unregistered files
1 issue.
```

**The remaining issue is pre-existing and was not fixed, deliberately.** The three are
`kg-schema-v0.1` (registered 2026-07-04 against schema v0.1; the schema is now v0.3.x),
`corpus-manifest` (2026-07-04) and `corpus-manifest-round2` (2026-08-30, mine). All three are
**snapshot** artifacts: they record a file as it stood at a moment. `seldon verify --fix` would
rewrite their stored hashes to today's bytes, which is exactly what a snapshot must not do — it
would erase the record that round 2's manifest differed from today's. A file-hash check is a
drift instrument, and applying it to a deliberate snapshot reports drift that is the point of
the artifact. Out of scope for this task either way; flagged for whoever owns the artifact
schema.

## 4. Verification

- Diff: 1 file, +7 lines, 2 lines modified (Status line, G1 paragraph). Reviewed line by line.
- Every insertion anchored on a string asserted unique before replacement, so no edit could
  land twice or in the wrong section.
- `corpus/manifest.json`, `events/`, and the burn: untouched (`git status` clean for all).
- `C4`, referenced in the §9 deferral entry, exists (§4 Criterion C, citation quality) —
  checked rather than assumed.
- `seldon verify`: runs; 1 pre-existing issue, characterised above.

## 5. Files

**Changed:** `docs/crosswalk/usafacts_operationalization_skeleton.md`.
**New:** this file; `cc_tasks/2026-09-01_machine_diagnostic_stub.md` (the task, committed with
its result per the task's own instruction).
**Seldon:** artifact `f7b38a38` repaired (path → store_dir); no artifact created; no
`manifest_add`; no event appended.
