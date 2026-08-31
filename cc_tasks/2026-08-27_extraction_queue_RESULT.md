# RESULT — 2026-08-27_extraction_queue

**Zero model spend**, declared as a ledger fact (`extraction_queue`, ceiling **0**,
`call_class: cleanup`, per ADDENDUM-01 §6). Any model call under this run would have been a
defect, not an overage; none was made.

**The three sentences are now true from one command.** `python -m kg queue status`:

```
pinned profile: v1   included: 194   manifest_add events: 194   reconciles: YES
document                          type       state            under          prio
---------------------------------------------------------------------------------
bandi-2025-metadata-ai-ready      academic   queued           —                10
ccsa-2026-ai-ready-official-stat… intergove… queued           —                10
croissant-akhtar-2024-paper       academic   queued           —                10
data-unchained-gasper-sequeda-ai… practitio… queued           —                10
… 190 more (use --limit)
---------------------------------------------------------------------------------
queued=34  stale=63  extracted=67  skipped_oversize=3  not_requested=27   total=194
```

ADDENDUM-01 read first and **committed before execution** (`fe8d0e7`) so the record shows which
instructions the run was against. On conflict it won; §1 (DD renumber) and §2 (derive, don't
trust) both bound real decisions below.

---

## Deliverables

| | |
|---|---|
| schema v0.3.5 append + append-only test | `kg/schema.yaml` `event_types` — the file's first event-type block |
| `extraction_request` / `extraction_withdrawn` | `kg/queue.py`, emitted to `events/batch-022.jsonl` |
| projection `extraction_state`, `extracted_under` | Neo4j `Document` properties + SQLite `extraction_queue` table |
| worklist derivation; `--docs` emits events | `scripts/run_bulk_extraction.py` |
| `kg queue` CLI | status / add / add-epoch / withdraw / next / explain / backfill |
| backfill events | 34 emitted; **134 refused, and the refusal was correct** — see below |
| DD | **DD-027** (base file said DD-023, occupied; ADDENDUM-01 §1) |
| tests | 440 → **453**; queue mutations **11/11** killed |

## The state of the corpus, derived live

Every number here is read at run time. ADDENDUM-01 §2 forbids hardcoded totals because the base
file's "currently 168" was stale within three days, and a test that pins a total fails for the
wrong reason the next time acquisition lands.

| state | n | composition (by corpus epoch) |
|---|---|---|
| `queued` | **34** | triage-2026-08-24 (all 34) |
| `stale` | **63** | kernel-v03 (all 63) |
| `extracted` | **67** | v1 |
| `skipped_oversize` | **3** | v1 |
| `not_requested` | **27** | acquisition-round2 16, no epoch 10, v1 1 |
| **total** | **194** | reconciles with 194 `manifest_add` doc_ids |

**Reconciliation: 194 = 194, exactly.** The raw `manifest_add` event count is 195; one is a
duplicate add for the same doc_id, so distinct ids are 194. Reported rather than reconciled —
`kg.manifest` is supposed to reject duplicates before writing, so that event is worth a look by
whoever owns admission. It does not affect any count here, which uses distinct ids.

## Discrepancies against the base prose — reported, not reconciled

### 1. "All 134 kernel-epoch docs" is two epochs, not one

Derived from the **dixie evidence ledger** (`corpus/evidence/decisions.jsonl`), which is where
`corpus_epoch_declared` lives:

| epoch | members | with an extraction |
|---|---|---|
| `v1` | 71 | 70 |
| `kernel-v03` | **63** | 63 |
| `triage-2026-08-24` | **34** | 0 |
| `acquisition-round2-2026-08-30` | 16 | 0 |

**71 + 63 = 134.** The base file's count is right and its label is wrong: those are all
documents extracted under a pre-v0.3.x profile, not kernel-epoch documents. Emitting all 134
under `profile: kernel_v03` as the base says would have mislabelled 71 v1 documents and
projected them `stale` against a profile they were never extracted under. The backfill requests
each epoch under **its own** profile.

The **34** is exactly right.

### 2. The cohorts are not derivable from `events/` at all

ADDENDUM-01 §2 says to derive the backfill counts "from the ledger". `manifest_add` events
carry **no `corpus_epoch`** — 195 of 195 have none — and the only `corpus_epoch_declared` events
on the event shards are for `crosswalk-2026-08-29`. Epochs are declared in the dixie evidence
ledger, which `run_bulk_extraction.corpus_members` already reads. `kg.queue.corpus_epochs`
reads the same source, so there is one definition and not two.

### 3. §1's precondition refuses §6's backfill — and the precondition should win

Base §1: *"profile exists and is sha-pinned."* Base §6: emit backfill requests under `v1` and
`kernel_v03`. **Neither of those profiles is sha-pinned** — they predate the convention; every
profile from `reextract_v034` onward has a `template_sha256`. So 134 of the 168 planned
backfill requests were refused at emit, with the reason.

**Resolved in favour of §1, on evidence that nothing is lost.** The projection does not need
those requests: `extracted` and `stale` derive from *extraction events*, not from requests. The
composition table above is exactly right without them — 67 + 63 + 3 + 1 = 134. What the guard
refused was a historical annotation; what it admitted was the 34 documents that are actual
future work, under `reextract_v035`, which is pinned. **The guard did its job and cost nothing.**

Re-running `kg queue backfill --commit` after `v1`/`kernel_v03` are pinned (or superseded)
would complete the annotation; it is not needed for any state this task delivers.

### 4. `extracting` was not derivable from the spend ledger as specified

Base §2 defines `extracting` as "an outstanding spend reservation exists for the document, read
from `state/spend_ledger.jsonl`". **Reservations are per-run and carried no document id**, so
the state was not derivable.

Smallest change that makes the spec real: `Ledger.reserve(..., doc_id=None)` records it as
**provenance only — it never touches capacity arithmetic** — and `model_stub.invoke` passes the
`doc_id` it already has. Reservations written before this contribute nothing to the state,
which is correct rather than guessed. This touches DD-022 territory additively; the tally is
unchanged and the full suite is green.

## Design points worth stating

**The pin is read, never held** (ADDENDUM-01 §4). `pinned_profile()` reads
`scripts/run_profiles.yaml`'s `default` at projection time. A test flips only that key and
asserts `extracted` → `stale` with no code change. This mattered concretely: the production
profile moved from `v1` through three v0.3.x arms while this task was open.

**An extraction's profile is resolved, never guessed.** Legacy events record only
`corpus_epoch`, and `reextract_v034`/`v035` share one, as do the four chunked arms. Where
`prompt_version` cannot disambiguate, the profile is reported unknown **and flagged
ambiguous** — a guessed profile silently decides `extracted` versus `stale`, which is the class
of quiet error this whole surface exists to prevent.

**`--docs` emits its own justification.** An operator override runs exactly the named documents
*and* emits an `extraction_request` per document (priority 0, `requested_by: cli`), so
`kg queue explain` can still answer why they ran. `--no-queue` is the escape hatch for a
projection defect and prints that nothing justifies its worklist.

**Erratum honoured (ADDENDUM-01 §5):** `source_type` is what you pass to the admission API,
`doc_type` is what you read back from the projection. Both are live; neither was renamed.
`kg.queue` reads `identity.doc_type` and says so in the docstring.

## Tests: 440 → 453. Queue mutations 11/11 killed

| mutation | result |
|---|---|
| M92 request no longer checks manifest inclusion | KILLED |
| M93 request accepts an unpinned profile | KILLED |
| M94 pin captured instead of read at projection time | KILLED |
| M95 withdrawal ignored | KILLED |
| M96 earliest request wins instead of latest | KILLED |
| M97 in-flight reservation no longer marks `extracting` | KILLED |
| M98 oversize no longer excluded at projection | KILLED *(retargeted)* |
| M99 worklist ignores priority order | KILLED |
| M100 ambiguous epoch guesses the first profile | KILLED |
| M101 reconciliation always reports agreement | KILLED |
| M102 backfill re-plans documents already requested | KILLED |

**M98 first exposed dead code, not a gap.** `worklist()` carried an explicit
`skipped_oversize` skip, but `project()` assigns that state before any queued/stale branch, so
the guard could not fire. Deleted with the reasoning recorded in place, and the mutation
retargeted at the exclusion that actually runs. Same resolution as `_MULTIWORD_ABBREV` and the
paragraph-break lookahead earlier in this project: when a mutation kills nothing, the first
question is whether the code can run at all.

No test hardcodes a corpus total; the reconciliation test builds both sides in a tmp ledger and
a control test proves the check can report a mismatch.

## What this unblocks

`cc_tasks/2026-08-30_bulk_extraction_v038.md` stopped at its own dispatch gate on 2026-08-30
because this RESULT did not exist and `kg/queue.py` was absent. Both now exist. That task's
Phase 0 can run: `kg queue status` reconciles (shown above), and its Phase 0.3 extract/defer cut
becomes `kg queue` deferral events over the live `t2_priority.json` rather than the read-only
preview recorded in its stop report.

**DD-027 is now taken by this task**, which is what that task's deliverables told it to verify
before claiming DD-028/DD-029.
