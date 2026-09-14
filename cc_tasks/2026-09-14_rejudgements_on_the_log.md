# CC Task — the seventeen re-judgements go on the log, in generation order, with supersession on the graph

**Date:** 2026-09-14
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-13_self_cycle_promote_RESULT.md` §6, §9 item 1 and `2026-09-13_rule_a12_v3_RESULT.md` §9 item 1.
**Implements:** DN-003 decisions 1 to 6 (`docs/design/2026-09-14_DN-003_event_log_and_rejudgements.md`); under DD-001, DD-019, DD-055.
**Fulfils:** its own ResearchTask (`seldon cc register`). Precedes the standing-cadence work; cycle 5 must not run against a log a generation behind the instrument.
**Spend:** zero model calls. **Network: none.** Every payload is on disk; the log only grows.

**Decisions taken here (operator overrides later):**
1. **`publish.py` learns the re-judgement shape** (harness runtime, edited under DN-003): a payload with `source_cycle` publishes `finding_derived` events only, citing the source cycle's `obs_id`s, with the cycle-level fields DN-003 decision 2 names; it refuses if any cited `obs_id` is not on the log, refuses to promote evidence, and refuses a payload whose `supersedes` is not itself on the log. One shard per cycle named from the cycle (decision 4); the `CYCLE_BATCH` table is deleted; cycles already on shared shards stay where they are and a test asserts no shard shrinks.
2. **Publication in generation order** (decision 5): the seventeen, oldest first, each `--project`ed after write. The order is derived from each payload's `supersedes` chain and generation, not typed; a test asserts every payload's predecessor precedes it on the log.
3. **`SUPERSEDES` edges** (decision 3): projection links each re-judged Finding to its predecessor on the same (site, leg), one to one; a test asserts the count of `SUPERSEDES` equals the count of re-judged Findings whose predecessor exists, and that for the report's snapshot every Result's Finding is current (no successor) at the time of this task. The `rejudgement_diff` records already on disk are the source of the pairing; the projection does not recompute verdict diffs.
4. **The census learns cycle kinds**: measured, self, re-judged. `findings_evidence_unretained` and the orphan count are reported per kind; a re-judged Finding whose cited `obs_id` resolves is not an orphan. The 120 annotated orphans from the 2026-09-06 scaffold stay 120.
5. **The published tree**: `docs/data/index.json` regenerates because the framework copy's digest may not move but the event-log digest does if the site publishes one; the report, PDF, matrices, `robots.txt`, `llms.txt` untouched; the sitemap moves only in `lastmod` if the site rebuilds at all, asserted.

**Zero edits to:** rule modules, manners, stored payloads, prior Results' values and states, prior RESULTs, figures, section prose, the skeleton, the record, `corpus/`, existing shards' content, `docs/` beyond decision 5.

**Immutable once written. Glob `2026-09-14_rejudgements_on_the_log_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decision 1. The shape, the refusals, the shard rule. Stop if any re-judged payload cites an `obs_id` absent from the log: that is a payload whose source cycle was never published, and it is named before anything is written.
## 2. Decisions 2, 3, 4, 5.
## 3. Gate (the one gate of this task)
Seventeen re-judged cycles on the log in generation order with 0 orphan Findings among them; `SUPERSEDES` count equals the paired count; the report snapshot's tagged Findings current; every shard append-only (byte-prefix check on every pre-existing shard); projection round-trip green; 22 of 22 payloads re-derive byte-identically; both invariant readings 0 across the whole projection; no Result registered or moved (count before and after); `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes no event: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-14_rejudgements_on_the_log_RESULT.md`: per cycle, events written and shard; the `SUPERSEDES` counts; the census per kind before and after; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (stop on an unpublished source) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
