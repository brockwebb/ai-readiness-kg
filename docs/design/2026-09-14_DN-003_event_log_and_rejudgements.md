# DN-003 — Design note: what the event log is for, and re-judgements on it

**Date:** 2026-09-14. Desktop design note; not a task. Under DD-001 (stranger rule), DD-019, DD-055. Raised by `2026-09-13_self_cycle_promote_RESULT.md` §9 item 1 and `2026-09-13_rule_a12_v3_RESULT.md` §9 item 1.

## The question

Seventeen re-judged payloads, including the judgement of record for the published report (`scan_2026-09-10_rj2`), live in `state/` and nowhere on the append-only log. The graph's Findings for cycle 4 are the measured judgement its own gate refused. Is the log the record of Observations only, with judgements a derived view, or the record of every judgement the project has asserted?

## Decision

1. **The log records every judgement the project asserts, and every Observation.** A judgement of record that is not on the log fails DD-001: a stranger replaying the log gets a different instrument than the one that published. Re-judgements are judgements; they go on the log.
2. **A re-judgement creates no evidence and republishes none.** Its `finding_derived` events cite the source cycle's `obs_id`s, which `publish.write_events` already permits. No Observation is republished, no body is promoted. The re-judged cycle carries `source_cycle`, `supersedes` (the payload it re-judged), `generation` and its `params_hash`, `base_params_hash` and overlay where one exists, so replay recovers exactly what the payload did.
3. **Supersession is on the graph.** A re-judged cycle's Findings link `SUPERSEDES` to the predecessor cycle's Findings on the same (site, leg), one to one. A Finding with no successor is current. The published report's Results point at the current judgement for its snapshot and the projection can say so by query, not by convention.
4. **One shard per published cycle**, named from the cycle (`events/cycle-<name>.jsonl`), replacing the table in `publish.CYCLE_BATCH` and the fallback to a shared shard. Cycles already on shared shards are not moved; the append-only log does not get rewritten. The census counts per cycle either way.
5. **Publication order is generation order.** The seventeen are published oldest generation first so the log's sequence is the sequence in which the project asserted them. A re-judgement is never published before its source cycle's Observations are.
6. **From now on a re-judgement task publishes its payloads as its last step**, before its RESULT. A re-judged payload in `state/` and not on the log is a gate failure for that task.

## What this changes for the standing cadence

Cycle 5's own gate publishes both its measurement and, when a gate refuses the measured judgement, the re-judgement it commissions. The graph is never a generation behind the instrument.
