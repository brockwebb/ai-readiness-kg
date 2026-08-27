# CC Task — Preemptive shared spend guard (DD-019 §5 defect)

**Date:** 2026-08-26
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Zero model spend. Code, tests, and ledger plumbing only. The only "model calls" in this task are the test stub. Blocks every burn task in the queue (restoration v2, stratum re-extraction, triage-batch extraction); nothing dispatches to a model until this lands.
**Before starting:** glob and read every `cc_tasks/2026-08-26_preemptive_spend_guard_ADDENDUM*.md`. Immutable file; changes arrive as addenda.
**Result:** `cc_tasks/2026-08-26_preemptive_spend_guard_RESULT.md` citing the Seldon task id. Record a `design_decisions.md` entry DD-022 (append-only) with the realized design and the mutation-test evidence. Discrepancies between this task's premises and live code are reported in the RESULT, never silently reconciled.

## Defect being fixed (from the ledger, not memory)

- `2026-08-23_batched_repair_resume` (a2d3fb42): 12M ceiling implemented as process-local state; two shard workers spent 22.03M. Registered result `ee4e8554`.
- `2026-08-23_trustgraph_benchmark_v2` (36a5c0e1): 8M ceiling checked after the call returned; consumed 8.11M (poll lag).
- DD-019 §5 states the requirement: ceiling enforced against a **shared counter**, not process-local state. DD-017 says `repair_relocate.py` "now enforces via the control plane" — verify what that actually does and report; if it is another process-local counter, it is in scope for replacement.

Both defects have the same shape: the check is *reactive* (after spend is known) and *local* (per process). The fix is *preemptive* (reserve before dispatch) and *shared* (one ledger, cross-process atomic).

## Prior art the design follows (no first-principles invention)

Reserve-then-settle admission control — the two-phase pattern used by quota systems and database connection/credit pools: a caller reserves an *estimated* cost before the operation, the operation runs only if the reservation was granted, and the reservation is replaced by the actual cost on completion. Cross-process atomicity on one machine via advisory file locking (`fcntl.flock`, exclusive) around the read-modify-append; this is the standard single-host mechanism and is sufficient because fleet workers run on one machine (`BURN_MAX_FLEET_WORKERS`). Per-call cost estimate = the conservative of a declared floor and a running mean of settled calls in the same run (the DD-019 measurements: ~36K/call cleanup-class, ~111K/call pilot-era single calls).

## Design (binding)

### 1. Ledger: `state/spend_ledger.jsonl` — append-only, flock-guarded

Records (all stamped `ts` UTC, `pid`, `host`):

- `declare` — `{run_id, ceiling_tokens, declared_by (task id), call_class}`; a run's ceiling exists on the ledger before its first reservation or the reserve call refuses with `undeclared_run`.
- `reserve` — `{run_id, reservation_id, estimate_tokens}`
- `settle` — `{run_id, reservation_id, actual_tokens, model_call_event_id}`; replaces the reservation's estimate with actual in every subsequent computation.
- `release` — `{run_id, reservation_id, reason}`; for a reserved call that never dispatched (exception before the CLI ran).
- `refuse` — `{run_id, estimate_tokens, committed_tokens, ceiling_tokens, scope: run|daily}`; written on every refusal.

`committed(run_id) = Σ settle.actual + Σ outstanding reserve.estimate` (outstanding = reserved, neither settled nor released). `committed(day)` is the same sum over all runs with `ts` in the UTC day.

Ledger is truth for spend admission. `model_call` events in the graph shards remain provenance for the calls themselves; the two are reconciled, not merged (§4).

### 2. API: `kg/spend.py`

```
class SpendLedger:
    def declare(run_id, ceiling_tokens, declared_by, call_class) -> None
    def reserve(run_id, estimate_tokens=None) -> Reservation | Refusal
    def settle(reservation, actual_tokens, model_call_event_id) -> None
    def release(reservation, reason) -> None
    def committed(run_id) -> int ; def committed_today() -> int
    def status(run_id=None) -> dict   # ceiling, committed, outstanding, remaining, refusals
```

- `reserve` with `estimate_tokens=None` computes the estimate: `max(call_class_floor, mean(actual of last N settled calls in this run))`, N=10, floors from `controls.yaml` (§3). Refuse iff `committed(run) + estimate > ceiling(run)` **or** `committed(day) + estimate > daily_tokens`. Refusal is a returned object, not an exception; the caller must treat it as a clean stop (exit 0, same contract as the STOP file and cap exhaustion in `run_bulk_extraction.py`).
- All five operations take the exclusive flock for the duration of read → compute → append. No reads outside the lock decide anything.
- Estimate floors and the daily cap are read at call time from `controls.yaml`, never cached across calls (config-first dials).

### 3. Config: `controls.yaml` (append, keep `schema_version` bump append-only)

```
spend:
  daily_tokens: <set from the standing Max daily band; if no declared band exists, use 30_000_000 and record the choice in the RESULT as an operator-visible default>
  call_class_floors:
    cleanup: 36000        # DD-019 measurement, Haiku one-item
    extraction: 111000    # 2026-08-21 pilot-era floor
    judge: 36000
```

Per-run ceilings are **not** in `controls.yaml` — they are declared on the ledger by the runner from the task file's stated ceiling (`declare`), so the ceiling and the spend that hit it are in one auditable place.

### 4. Reconciliation

`python -m kg.spend reconcile --run-id R`: Σ `settle.actual` for R vs Σ token counts on `model_call` events tagged with R across shards. Mismatch → non-zero exit and a `reconcile_mismatch` record on the ledger. Runs automatically at the end of every burn script (before the RESULT is written).

### 5. Wiring — one choke point, then remove the local counters

- The guard lives adjacent to the DD-007 API-key gate in `kg/extraction/model_stub.py` (find the exact function; report the file:line in the RESULT). Every CLI invocation passes through `reserve` → call → `settle` (or `release` on exception). A caller that has not declared a run gets `undeclared_run` refusal — there is no unmetered path.
- `scripts/batch_repair.py`, `scripts/repair_relocate.py`, `scripts/run_bulk_extraction.py`, and the TrustGraph backend under `benchmarks/trustgraph/` if it dispatches through the stub: replace every process-local token counter / ceiling with ledger calls. **Delete the local counters** — two mechanisms is how the 22M happened. Each script declares its run at start from a `--ceiling-tokens` argument (required; no default) and a `--run-id` (default: task slug + UTC timestamp).
- Token counts come from the CLI envelope the stub already parses for `model_call` events; if the envelope lacks a field the stub currently records as tokens, report it, do not estimate.

### 6. Mutation tests — the guard is not verified until each seeded fault fires it

`tests/test_spend_guard.py`, all against a stub model that **asserts it was never invoked** on refusal:

1. **Seeded near-ceiling refuses before dispatch.** Ledger seeded at `ceiling − (floor − 1)`; one `reserve` → `Refusal(scope=run)`; stub call count 0; a `refuse` record exists.
2. **Concurrent workers cannot oversubscribe.** `multiprocessing` with 8 processes each attempting 50 reservations against a ceiling that admits exactly 100 floor-sized calls; assert granted reservations == 100, Σ granted estimates ≤ ceiling, ledger has no interleaved/corrupt lines.
3. **Overshoot on settle closes the door.** Reserve at estimate E, settle at actual 3E pushing committed past ceiling; next `reserve` refuses.
4. **Daily cap is independent of run ceiling.** Two runs, each under its own ceiling, whose sum crosses `daily_tokens`; the second run's reserve refuses with `scope=daily`.
5. **Undeclared run refuses.** `reserve` on an unknown `run_id` → refusal, stub count 0.
6. **Release restores capacity.** Reserve to the ceiling, release one, reserve again succeeds.
7. **Reconcile detects a planted mismatch.** Write a `model_call` event with tokens ≠ its ledger settle; reconcile exits non-zero and appends `reconcile_mismatch`.
8. **Regression replay of the 22M incident shape.** Two "workers" each declaring the same run with ceiling 12M and dispatching floor-sized calls in a loop until refused; assert total settled ≤ 12M + one floor (the at-most-one-in-flight overshoot bound), not 22M.

Every test must fail when the corresponding guard line is commented out (prove it once: run the suite with the reserve check disabled, record the failing test names in the RESULT, restore).

## Out of scope

- Cross-machine ledgers, token buckets with refill, cost-in-dollars, provider-side spend APIs. Not this task.
- Any change to existing burn worklists, shards, or event content.
- Retro-ingesting past spend into the ledger. The ledger starts empty; history stays in `model_call` events and the RESULT files.

## Deliverables checklist

- [ ] `kg/spend.py` + `state/spend_ledger.jsonl` (created empty, tracked; `.gitkeep`-style header record `ledger_open` with schema version)
- [ ] `controls.yaml` `spend:` block
- [ ] guard wired in `model_stub.py`; local counters removed from the four callers; `--ceiling-tokens` required
- [ ] `python -m kg.spend status|reconcile`
- [ ] `tests/test_spend_guard.py`, 8 tests, plus the disabled-guard failure proof
- [ ] DD-022 appended
- [ ] full suite green, commit, push, `seldon cc complete`, RESULT
