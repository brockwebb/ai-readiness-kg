# CC Task — Extraction queue: admitted → prioritized → extracted, one status surface

**Date:** 2026-08-27
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Zero model spend. Events, projection, CLI, tests. Runs in parallel with cd8449de's lanes; touches no shard those lanes write. Coordinate on `kg/extraction/state.py` and `scripts/run_bulk_extraction.py` by reading them fresh at start and reporting any in-flight edits by the burn driver rather than overwriting.
**Before starting:** glob and read every `cc_tasks/2026-08-27_extraction_queue_ADDENDUM*.md`. Immutable file.
**Result:** `cc_tasks/2026-08-27_extraction_queue_RESULT.md`; DD-023 appended to `docs/design_decisions.md`. Discrepancies reported, never reconciled.

## What this is for

The operator wants three sentences to be true at any moment, from one command, from the ledger:
1. what is in the manifest, what is out, and why;
2. for every admitted document, whether it has been extracted, under which prompt version and model, or why not;
3. what will be extracted next, in what order, and "extract these" as an operator sentence.

Two of the three stages already exist as event types (`kg.manifest` include/exclude with reason; extraction events per document). The third — a deliberate, prioritized *extraction request* separate from admission — does not. Curation pipelines that work at scale (Wikidata's proposal→review→ingest, UniProt's triage→curate) separate "accepted into the corpus" from "worked on now"; that separation is what lets resources be spent by priority instead of by arrival order. Admission ≠ extraction.

## Design (binding)

### 1. Event: `extraction_request` (append-only, new type in `kg/schema.yaml` — schema v0.3.5 append)

```
{type: extraction_request, document_id, priority: int (1 = first), requested_by, reason,
 profile: <run_profiles key>, superseding: bool, ts}
```
- Preconditions enforced at emit: document is manifest-included; profile exists and is sha-pinned. Emitting for a non-included document is a refusal with the reason, not an event.
- A later request for the same document replaces priority/profile (latest wins in projection). `superseding: true` means "re-extract even though an extraction under an older profile exists"; default false.
- `extraction_withdrawn {document_id, reason}` cancels a request.

### 2. Projection: `Document.extraction_state` (derived, never stored as truth)

Computed from events in the projection layer and exposed on the Neo4j `Document` node and in the SQLite bundle:

`not_requested | queued | extracting | extracted | stale | failed | skipped_oversize | excluded`

- `extracted` iff an extraction event exists under the *current* pinned profile for the document's construct arm.
- `stale` iff an extraction exists only under a profile that has since been superseded for that arm (e.g., kernel-v03 items in the two `reextract_required` strata once `reextract_v035` is current). Staleness is per-stratum where supersession is stratum-scoped (the burn task's `superseded_strata`); the document-level state is `stale` if any stratum is.
- `failed` carries the last failure status (`parse_failed_truncated`, `quarantined_systemic`, `rate_limited`, …) and count.
- `extracting` = an outstanding spend reservation exists for the document (read from `state/spend_ledger.jsonl`), so the status surface never claims a document is idle while a call is in flight.

Also projected: `Document.extracted_under {profile, model_id, ts, event_id}` list, all runs.

### 3. Worklist derivation replaces hand-built lists

`scripts/run_bulk_extraction.py` (and the burn driver's Lane 2/3 worklists) derive the worklist as: manifest-included ∧ (`queued` ∨ (`stale` ∧ superseding request)) ∧ not `skipped_oversize`, ordered by `priority` asc, then `BURN_ORDER`. `--docs a,b,c` remains as an explicit override and emits `extraction_request` events (priority 0, `requested_by: cli`) so the ledger shows why those ran. No worklist may be built from an ad-hoc list that isn't on the ledger.

### 4. CLI: `python -m kg queue …`

- `kg queue status [--arm X] [--state S]` — table: document_id, title, arm, manifest reason (short), extraction_state, extracted_under (latest), priority, size. Totals per state. This is the answer to "what the fuck are we doing"; make it fit a terminal.
- `kg queue add <doc_id…> --priority N --reason "…" [--profile P] [--superseding]` — emits requests.
- `kg queue add-epoch <manifest epoch> --priority N --reason "…"` — e.g., `triage-2026-08-24`.
- `kg queue withdraw <doc_id> --reason`.
- `kg queue next [--n 5] [--arm X]` — what would run next, with the estimated token cost from the ledger's per-class running mean × doc count (informational).
- `kg queue explain <doc_id>` — every manifest and extraction event for the doc, in order, with reasons.

### 5. Inbox admission stays as is, with one addition

The drain path (`inbox → candidate register → kg.manifest.add → sweep`) is unchanged. On `kg.manifest.add` success, **no** extraction request is emitted automatically — admission is not a request. The drain prints the `kg queue add` command for the new ids so the operator's next sentence is ready.

### 6. Backfill (events, so it's auditable)

- All 134 kernel-epoch docs: `extraction_request {priority: 50, requested_by: backfill, reason: "kernel epoch; extracted under kernel-v03", profile: kernel_v03}` so they project as `extracted` or `stale` correctly. No new spend.
- The 34 `triage-2026-08-24` docs: `priority: 10, reason: "triage batch; awaiting reextract_v035 pilot pass"`, profile `reextract_v035`. They project `queued`; the burn's Lane 3 worklist derives from this.
- Documents in the two `reextract_required` strata: projected `stale` automatically once `reextract_v035` is current for the arm; no request needed until the pilot passes — the burn driver emits `superseding` requests on PASS.

### 7. Tests

- Request for a non-included doc refuses.
- State machine: not_requested → queued → extracting (planted reservation) → extracted; profile supersession flips extracted → stale; withdraw → not_requested.
- Worklist derivation ignores anything not on the ledger; `--docs` emits request events.
- `kg queue status` totals reconcile with the manifest included count (currently 168) and with Neo4j `Document` counts.

## Out of scope

Model-assisted admission triage (an Opus "read on drop" that writes descriptive metadata) — a separate proposal; the operator's instinct to gate submissions is right, but the gate is the recorded admission decision, and a model's read of a submission is `signal_not_verdict` input to it, not the gate. Dedup. Any change to prompts, gates, or thresholds.

## Deliverables

- [ ] schema v0.3.5 append + append-only test; `extraction_request` / `extraction_withdrawn` events
- [ ] projection: `extraction_state`, `extracted_under`; Neo4j + SQLite
- [ ] worklist derivation in `run_bulk_extraction.py`; `--docs` emits events
- [ ] `kg queue` CLI (status/add/add-epoch/withdraw/next/explain)
- [ ] backfill events (134 + 34)
- [ ] tests; suite green; DD-023; commit; push; `seldon cc complete`; RESULT with the `kg queue status` totals pasted
