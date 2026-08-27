# RESULT — Preemptive shared spend guard (DD-019 §5 defect)

**Task:** `cc_tasks/2026-08-26_preemptive_spend_guard.md` (Seldon ResearchTask **d2756bd1**). No addenda existed at start (glob `cc_tasks/2026-08-26_preemptive_spend_guard_ADDENDUM*.md` → empty).
**Run:** 2026-08-26/27 UTC. **Model calls: zero** — the only "model" in this task is the test stub (`CountingStub`), which asserts it was never invoked on refusal.
**Design decision:** DD-022 appended (append-only) with the realized design and mutation evidence.

## Deliverables checklist — all landed

- [x] `kg/spend.py` (SpendLedger: declare/reserve/settle/release/committed/committed_today/status/reconcile; flock held for every read → compute → append) + `state/spend_ledger.jsonl` (tracked; opened with a `ledger_open` header record, `ledger_schema: 1`)
- [x] `controls.yaml` `spend:` block; `schema_version` bumped `"0.1"` → `"0.2"` append-only
- [x] Guard wired at the choke point; local counters **deleted** from the callers; `--ceiling-tokens` required (no default) on every dispatching script
- [x] `python -m kg.spend status|reconcile` (reconcile exits non-zero on mismatch and appends `reconcile_mismatch`)
- [x] `tests/test_spend_guard.py` — 8 tests, all green; disabled-guard failure proof recorded below
- [x] DD-022 appended; full suite **183 passed**; committed + pushed; `seldon cc complete`

## The choke point (task §5: "find the exact function; report the file:line")

`kg/extraction/model_stub.py::invoke` — the DD-007 API-key gate is the `guard_no_api_key()` call at `kg/extraction/model_stub.py:224`; the spend guard sits immediately after it: reserve at `model_stub.py:232`, refusal raised as `SpendRefusalStop` at `model_stub.py:234`, before any `subprocess.run`. Settlement paths:

- envelope parsed → settle at the measured sum of `inputTokens + outputTokens + cacheCreationInputTokens + cacheReadInputTokens`;
- CLI never ran (`OSError` — the auto-update window) → `release` (capacity restored);
- dispatched but unmeasurable (timeout / non-zero exit / unparseable envelope / usage fields absent) → settle **at the estimate**, flagged `settled_as_estimate` (+`usage_fields_missing` where applicable) — conservative; the task's "do not estimate" rule is honored in that no token count is ever derived from content (the old `cp.estimate_tokens` fallback is not used by the ledger).
- `invoke`'s return meta now carries `spend_run_id` / `spend_reservation_id`; `kg/extraction/pipeline.py` stamps both onto each `model_call` event.

**Settle-record discrepancy vs task §1, reported:** the spec's `settle.model_call_event_id` cannot be non-null at the choke point — `kg/eventlog.append` mints the event id *after* the stub has already settled, and no `model_call` event exists at all for the repair-class scripts. The field exists and is nullable; the correlation pointer is inverted (the `model_call` event carries `run_id` + `spend_reservation_id`), and reconcile joins by run as §4 specifies. Nothing is lost; the single-choke-point property (no caller can forget to settle) is kept, which is the stronger guarantee.

## DD-017 verification (task: "verify what that actually does and report")

`scripts/repair_relocate.py` "enforces via the control plane" = `rbe.tokens_left() <= 0` at (old) line 175 → `run_bulk_extraction.tokens_left()` (`scripts/run_bulk_extraction.py:185`) = control-plane **daily/weekly band** remaining, from usage booked *after* each call. So: shared file, but **reactive** (poll-lag, the 8.11M shape), and **no per-run ceiling at all** — in scope per the task's "if it is another process-local counter" clause read against the defect's actual shape (reactive + no reservation). Replaced with the ledger guard; the band itself survives *inside* the guard as the ledger's daily scope, and `tokens_left()` remains only as printed telemetry (`run_bulk_extraction.py:306,449`), never an admission decision.

## Local counters removed (task §5)

| script | before | after |
|---|---|---|
| `scripts/batch_repair.py` | `TOKEN_CEILING = 12_000_000` module constant + `tokens_spent` process-local sum (the 22.03M defect) | deleted; `--ceiling-tokens`/`--run-id` declare on the ledger (call_class `cleanup`); `SpendRefusalStop` → clean stop **exit 0** (exit 3 stays reserved for diagnostic halts); reported `tokens` = shared `committed(run)`; reconcile before the summary |
| `scripts/repair_relocate.py` | `rbe.tokens_left() <= 0` poll + local `tokens` sum | deleted; phase 3 requires `--ceiling-tokens` (phase 2 is zero-spend); declare `cleanup`; refusal → clean stop; reconcile at end |
| `scripts/run_bulk_extraction.py` | `tokens_left() <= 0` loop gate (reactive) | gate removed; `--ceiling-tokens` **required**, `--run-id` optional; fleet coordinator forwards both so all shard workers draw one shared run (idempotent re-declare); refusal → clean stop; reconcile appended to burn progress before the RESULT write |
| `scripts/tgbench_ours.py` | no ceiling at all (the 8M was checked post-hoc task-side; consumed 8.11M) | `--ceiling-tokens` required; declare `extraction`; refusal → clean stop; reconcile at end |

**TrustGraph backend under `benchmarks/trustgraph/`:** verified — nothing there dispatches through the stub (export/judge-sample/normalize scripts only; the `claude-cli-completion` backend lives in the trustgraph fork repo, out of scope). The stub-dispatching piece of that benchmark in this repo is `scripts/tgbench_ours.py`, wired above. Its `model_call` events go to the *tagged* shard (`batch-013_benchmark`), which `eventlog.replay()` excludes by design, so its reconcile takes the no-tagged-events path (note below).

**No unmetered path:** all other stub callers (`probe_judge`, `tevv_judge`, `probe_decompose`, `probe_repair`, `pilot_audit_v03`) now refuse with `undeclared_run` until a future task declares a run for them — intended (their tasks are complete; re-use requires a declaration).

## Config decisions recorded (operator-visible)

- **`spend.daily_tokens: 55_000_000`** — a standing declared band exists: the Wintermute control plane's `declared_caps("extraction")` (`~/.wintermute/scripts/lib/control_plane.py` panel) read 2026-08-27 = daily 55M / weekly 880M. The task's 30M fallback was therefore **not** used.
- Floors: `cleanup: 36000`, `extraction: 111000`, `judge: 36000` — the DD-019 measurements, as the task specifies.
- Estimate = `max(class floor, mean of last 10 measured settles in the run)`; settles flagged `settled_as_estimate` are excluded from the mean (they are estimates, not measurements).
- `cp.record_usage(...)` calls are **kept** in the runners: the control plane is the cross-project observability panel, not an admission counter; deleting it would blind Wintermute's breaker. Admission lives only in the ledger — one enforcement mechanism.
- Reconcile on a run with **zero** tagged `model_call` events writes a `reconcile_note` and passes: the repair-class scripts persist raw usage JSONs but have never emitted `model_call` events, and changing their event content is out of scope. Reported here as the reconcile boundary.

## Mutation-test evidence (task §6)

All 8 tests green (`tests/test_spend_guard.py`); each seeded fault proven to fire:

- **Reserve admission check disabled** (`if scope:` → `if False and scope:`): **6/8 FAILED** — `test_seeded_near_ceiling_refuses_before_dispatch`, `test_concurrent_workers_cannot_oversubscribe` (8 spawn processes × 50 attempts vs a 100-call ceiling: granted 400 ≠ 100), `test_overshoot_on_settle_closes_the_door`, `test_daily_cap_is_independent_of_run_ceiling`, `test_release_restores_capacity`, `test_regression_replay_of_the_22m_incident_shape` (two workers, one declared 12M run: settled ≤ 12M + one floor with the guard; breach without it).
- **Undeclared-run check disabled**: `test_undeclared_run_refuses` FAILED.
- **Reconcile equality forced true**: `test_reconcile_detects_planted_mismatch` FAILED.
- All three mutations restored (`grep` for markers = 0); suite re-run green (183).

Stub-invocation counts asserted 0 on every refusal path (tests 1 and 5 drive the real `model_stub.invoke` with a counting fake `subprocess.run`).

## Discrepancies vs task premises (reported, not silently reconciled)

1. `settle.model_call_event_id` nullable + inverted correlation pointer (above) — the event id does not exist at settle time.
2. DD-017's "enforces via the control plane" is a reactive daily-band poll with no run ceiling (above) — replaced, not merely wrapped.
3. The task's §6.2 wording "assert granted reservations == 100, Σ granted estimates ≤ ceiling" is implemented exactly; note the 8-process run also asserts the ledger parses line-for-line (no interleaved writes) — flock held across read-modify-append makes torn lines impossible on one host.
4. §6.8's workers use a bounded loop (600 attempts each) instead of `while True`: with the guard healthy the refusal ends the loop at ~334 total grants; unbounded, a disabled guard (the mutation proof) would loop forever instead of failing fast. Bound is far above the ceiling's admit count, so it never masks a real refusal.
5. `state/spend_ledger.jsonl` is tracked with only the `ledger_open` record, per "the ledger starts empty; history stays in `model_call` events and the RESULT files". Future run records will accrue in it and travel with commits (auditable spend beside the code that spent it).
6. The launchd wrapper `scripts/jobs/airkg_extraction_burn.sh` (completed bulk-v1 burn; not currently loaded in launchd) would now fail loud on argparse if re-fired bare — annotated in place; re-enabling it for a future burn requires that burn task's declared ceiling. No default was added anywhere.

## Files

`kg/spend.py` (new), `state/spend_ledger.jsonl` (new), `tests/test_spend_guard.py` (new, 8 tests), `controls.yaml` (+spend block, schema 0.2), `kg/extraction/model_stub.py` (guard at the choke point), `kg/extraction/pipeline.py` (model_call run tagging), `scripts/batch_repair.py`, `scripts/repair_relocate.py`, `scripts/run_bulk_extraction.py`, `scripts/tgbench_ours.py` (counters deleted, ledger wired), `scripts/jobs/airkg_extraction_burn.sh` (annotation), `tests/test_extraction_model_stub.py` (declared-run fixture; release-path assertion), `docs/design_decisions.md` (DD-022), `CLAUDE.md` (commands + controls doc).
