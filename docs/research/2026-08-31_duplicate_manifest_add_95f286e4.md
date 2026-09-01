# Duplicate `manifest_add` — ResearchTask 95f286e4

**Date:** 2026-08-31. **Spend:** zero model tokens.
**Verdict:** the guard did not fail. It was bypassed, deliberately, for a reason that no
longer applies. The missing guard was at the **log** level, and it now exists.

## The reported symptom

195 raw `manifest_add` events, 194 distinct doc_ids (`2026-08-27_extraction_queue_RESULT`,
reconciliation section). The task framed this as "`kg.manifest` is supposed to reject
duplicate adds before writing; one got through."

## What actually happened

The duplicate is `introducing-the-oecd-ai-capability-indicators`:

| | event | shard | content_hash | local_path |
|---|---|---|---|---|
| 2026-07-04 | `712a7c38…` | `batch-001` | `7e740330…` | `corpus/bulk_md/…md` (crawl4ai capture of `component-5.html`) |
| 2026-08-14 | `d2ad0f8c…` | `batch-005` | `798d84db…` | `corpus/bulk/…pdf` (full 56-page report) |

The second event is **an operator-cleared extent correction**, and it says so on its face:

> "Full 56-page OECD report (PDF). **Supersedes** the crawl4ai markdown capture of
> `component-5.html`, which was one component of the report, not the whole report, despite
> being larger in characters (287,110 md vs 142,364 pdf) because the web capture carried site
> boilerplate. Operator Clearance 2, `cc_tasks/2026-08-14_bulk_v1_closeout.md`."

Its `acquisition.verification.supersedes_sha256` names `7e740330…` — exactly the first
event's hash. The superseded file was quarantined, never deleted. CLEARANCE 2 in the closeout
task authorised precisely this.

### Why it did not go through `add()`

It could not have. `add()`'s duplicate-`doc_id` check has been in place since before either
event, it reads `_load_entries()`, and `_load_entries()` replays the log — I read the version
of `kg/manifest.py` in force on 2026-08-14 (`94fd280`) and the check is byte-identical in
intent to today's. Both shards are untagged, so `replay()` sees both. A call to `add()` on
2026-08-14 would have raised `duplicate doc_id`. The event was written straight to the shard.

**And that was the least-bad option available.** `content_update` — the sanctioned
supersession event, whose reason codes include `extent_corrected` — did not exist until
**2026-08-29** (commit `00acd06`), fifteen days later. On 2026-08-14 the alternatives were:
edit the admission event (forbidden, invariant 1), leave the corpus holding one component of a
report as if it were the report, or append a second `manifest_add`. The third preserves the
append-only log and lands the correct state, because `_load_entries()` replays in shard order
and the later entry wins.

So the premise "one got through the guard" is wrong in a way that matters: nothing got past a
check. A writer went around a check because the vocabulary it needed did not exist yet. Those
call for different fixes, and only the second one is real.

## No data defect — confirmed, not assumed

- The entry in force is `corpus/bulk/…pdf`, hash `798d84db…` — the corrected document.
- `queue.manifest_added_ids()` accumulates into a **set**, so `reconciles: YES` at 194 was
  never wrong; the distinct-id basis is used everywhere counts are reported.
- The one latent hazard is real but not triggered: shard order is not causal order, so a
  future add for the same doc landing on a *lower*-numbered shard would silently win. The
  guard below closes that by refusing to let a second add exist at all.

## The guard that was missing

`kg.manifest.duplicate_adds()` — a log-level invariant `add()`'s per-call check cannot
express. It reports every doc_id carrying more than one `manifest_add`, and classifies each as
**explained** (the later event declares what it supersedes, by `supersedes_sha256` or in its
rationale) or **unexplained**, which is a corrupt log.

Tests, all mutation-verified rather than asserted:

| test | mutation that must break it | fired? |
|---|---|---|
| `test_reject_duplicate_doc_id` (pre-existing) | remove the `doc_id` comparison in `add()` | ✅ fails |
| `test_mutation_the_doc_id_check_is_what_rejects_a_duplicate_doc_id` | — it *is* the control: blinds the doc_id field and asserts the add then lands | ✅ |
| `test_duplicate_adds_finds_a_bypassed_duplicate_and_calls_it_unexplained` | blind the audit (`len(evs) < 99`) | ✅ fails |
| `test_duplicate_adds_recognises_a_declared_supersession` | same | ✅ fails |
| `test_live_log_carries_only_the_known_explained_duplicate` | same | ✅ fails |

The pre-existing `test_reject_duplicate_doc_id` was already built correctly — different file
*and* different URL, so only the doc_id check can fire — but nothing in it **proved** that. A
naive version reusing the same file trips the `content_hash` check first and passes while
measuring the wrong guard, which is this repo's recurring M2 failure mode. The added mutation
pins which check does the work.

`test_live_log_carries_only_the_known_explained_duplicate` runs against the **real** event
log, allowlists exactly this one pair by event id, and additionally asserts that its
`supersedes_sha256` still equals the earlier event's `content_hash` — so the allowlist vouches
for a specific, internally consistent pair rather than for a doc_id. A second duplicate, or
this one losing its supersession claim, fails the suite.

## Does the duplicate need an annotation? Yes — and not a `content_update`

Appended `document_annotation` `2b1556ed…` on `events/batch-024.jsonl`,
`property: admission_supersession`, carrying both event ids, both hashes,
`reason: extent_corrected`, and the CLEARANCE 2 authority.

**Not a `content_update`**, for a reason worth recording: that event asserts a hash change
against the entry's *current* hash, and the current hash is already the corrected PDF's.
Emitting one retroactively would misstate the sequence, and `content_update` would refuse it
anyway ("bytes are unchanged"). The annotation records the relationship without touching the
entry.

Verified safe: `admission_supersession` is not in
`build_projection.ANNOTATABLE_DOCUMENT_PROPERTIES`, so `annotation_update()` returns `None`
for it — it stays on the log and can never become a Cypher property name. The manifest entry
is byte-identical after the append. No event was edited.

## What changes going forward

A re-acquisition at corrected extent is a `content_update(reason="extent_corrected")`, not a
second `manifest_add`. That is now enforced by a test against the live log rather than by
anyone remembering. Suite: **589 passed**.

This is the same defect class as DD-030, one layer up: there, an acquisition captured a
document's table of contents and nothing noticed; here, an acquisition captured one component
of a report and the correction had nowhere to go. Both were extent problems that the pipeline
had no vocabulary for at the time.
