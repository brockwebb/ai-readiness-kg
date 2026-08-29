# ADDENDUM-02 to 2026-08-27_chunked_pilot.md — orphaned-reservation release path

**Date:** 2026-08-28. Trigger: §0 report — 1,326,274 tokens held across four runs by reserve-before-dispatch holds from calls killed mid-flight (largest: `pilot_chunked_v035`, 1,113,669 of its 13M ceiling). Reconciliation is honest (`ok: true`; holds err conservative) but dead holds distort any reused ceiling. Zero model spend; code + tests only. Runs before ADDENDUM-01 §3; independent of §1.

## Spec: `python -m kg.spend release-orphans`

1. **Orphan definition (all three required):** reservation event with no matching settle/release; reservation age > 10 minutes; owning PID recorded on the reservation is not alive (or PID absent). Age alone never qualifies — a live long call is not an orphan.
2. **Action:** append `reservation_released` ledger event carrying the original reservation id, run_id, amount, reason `orphan_pid_dead`, and the PID liveness evidence. Ledger stays append-only; no mutation of prior events. Capacity math treats released reservations as returned to the run ceiling and daily band.
3. **Dry-run default:** `release-orphans` lists candidates and exits; `--commit` required to write. Output table: run_id, reservation id, age, amount, PID, liveness.
4. **Reconcile compatibility:** `kg.spend status` and reconcile must account for `reservation_released` (committed − settled − released = outstanding). `ok: true` invariant preserved.
5. **Tests, positive-control discipline (methodology §7.5 — no monitor trusted until a seeded known-bad fires it):**
   - Seeded orphan (dead PID, aged) → listed in dry-run, released with `--commit`, capacity returns.
   - Live reservation (own PID) → never listed, never released.
   - Aged reservation with live PID → never released.
   - Mutation check: disable the PID-liveness test → the live-reservation test must fail.
6. **First real run:** dry-run, paste table into RESULT, then `--commit`. Expected: the four known orphans released (~1.33M returned). Report new outstanding per run (should be 0 across all four unless a hold is genuinely mid-flight at run time).

## Exit
Suite green; ledger shows the releases; `kg.spend status` outstanding column zeroed for the four runs; RESULT appended to this task's RESULT file; commit and push. `seldon cc complete` covered by the parent task's closure.
