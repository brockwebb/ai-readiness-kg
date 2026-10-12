# CC Task: the projection rebuild is measured, then batched, so admitting a document no longer costs 90 minutes

**Date:** 2026-10-12
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the 2026-10-11 projection logs.
**Implements:** no design note; a performance defect in `scripts/build_projection.py`. The standing rule applies: a mechanism named for a measured number is a hypothesis until this task confirms it.
**Framework layer served (DN-005 §5 rule 1):** none directly: the projection every view and query reads. No verdict, record, claim or score may change; the graph after the change must be the graph before it.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1.2M tokens (Opus). Read it as 2 to 4x low. No harness model call. Several full projections (about 90 min each before the fix), run detached.
**Network:** none beyond git push

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Measured premises (verify before acting; report any that is wrong)

- `logs/2026-10-11_standards_projection.log`: the `kg_replay` phase replays 171,349 events at roughly 35 events per second (2,289 in the first 60 s, 69,190 by 1,423 s), with a burst where 15,000 events took under 5 s (25,000 to 40,000). The whole projection took about 89 minutes in part 2 (5,366 s) and dominated task `b3a2df60`'s 8,159 s.
- Every corpus admission, cycle publication and framework write-back runs this full rebuild.
- Desktop's hypothesis, unconfirmed: replay writes one Neo4j transaction per event (or per small group), so time is transaction overhead, not work; the fast burst is a run of events that write nothing. Neo4j's own guidance is to batch writes, many rows per transaction via `UNWIND`, rather than a transaction per row. Confirm or refute it from the code and a profile before changing anything.

## Decisions

1. **Measure first.** Profile one full projection: time per phase, transactions per phase, events per transaction, and the share of `kg_replay` time spent in driver round trips versus server work. Record the event types in the fast burst and why they are fast. The RESULT states the measured cause; if it is not transaction overhead, stop after this step and report, changing nothing.
2. **If the cause is per-event transactions: batch the replay.** Group consecutive events into transactions of a size you choose and justify from a short sweep (for example 500, 2,000, 10,000 rows), using `UNWIND` with parameters. Ordering semantics must hold: an event that depends on an earlier one in the same batch must see it, or the batch boundary must fall between them. Say how you guarantee that.
3. **Equivalence is the gate, not speed.** Build a canonical export of the projected graph (every node with labels and properties, every relationship with type, endpoints and properties, sorted, with volatile fields such as write timestamps named and excluded) and hash it. The batched projection's hash must equal the current projection's hash, on the current corpus. Any difference fails the task, whatever the speed.
4. **Full rebuild stays the only path.** No incremental or checkpointed projection in this task. If batched full replay still exceeds 10 minutes end to end, report the phase that dominates and stop; an incremental design is its own task with its own equivalence proof.
5. **Progress logging stays.** The existing progress lines (`phase … elapsed …`) keep their format; tests that read them stay green.

**Write set:** `scripts/build_projection.py` and modules it owns, a canonical-export script, tests, the RESULT. Byte-identical: every event file, the corpus, rules, collectors, `manners.py`, `score.py`, claims, views, `reports/`, `docs/evidence/FROZEN.md`.

## Gate

The equivalence hash, before and after, quoted whole. A test that a small fixture corpus projects to the same canonical hash batched and unbatched. Wall clock of one full projection before and after, from the progress log. `make gate-task`, quoting passed, skipped, xfailed, deselected and wall clock. `seldon verify`. The protected-paths diff.

## RESULT

Under 50 lines: the profile and the measured cause; the batch size sweep; the equivalence hashes; wall clock before and after per phase; premises wrong; logs. `seldon cc complete`, commit, push.
