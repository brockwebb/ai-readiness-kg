# CC Task — the framework record has one writer, and that writer refuses to drop what it did not author

**Date:** 2026-09-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-11_a3_a10_sources_RESULT.md` §7 and §10 item 2.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs before `2026-09-11_report_sources_appendix.md`, because that task reads the record this one protects.
**Spend:** zero model calls. **Network: none.**

**Why this task exists.** `scripts/build_framework_graph.py` regenerates `framework/ai_readiness_framework.json` from the skeleton. The skeleton is the source of the authored cells and not of the record: the record has since been written back to by spec registration, DD-054's adoption of A12 into G, and now evidence write-backs. Running the generator the obvious way produced a diff of 90 insertions and 843 deletions, deleting every `MEASURED_BY` edge and undoing DD-054. It was caught by a diff and a `git checkout`, which is a habit, not a guard. Any future task that edits a cell will reach for the same script.

**Prior art.** Generated-file-with-hand-edits is a solved problem in two ways: edits go in the source and regeneration is idempotent, or the generator is not the writer. This repo is event-sourced, so the second is the native shape: the ledger is the truth, the record is a projection, and every projection write goes through one helper that appends an event.

**Decisions taken here (operator overrides later):**
1. **`framework_writeback.py` is the only code that writes `framework/ai_readiness_framework.json`.** `build_framework_graph.py` produces its output in memory and hands it to the helper; a test asserts no other module opens the record for writing.
2. **The helper refuses a write that removes any node or edge present in the current file**, or drops any key from `counts`, unless invoked with `--force --reason "<text>"`, in which case the reason is on the `framework_writeback` event. The refusal message names what would be dropped and how many.
3. **Regenerating from the current skeleton over `HEAD` is a no-op**, asserted by a test: generate, merge through the helper, byte-compare. If it is not a no-op today, the RESULT says exactly which nodes or edges the skeleton does not carry (the write-backs), and the generator learns to preserve them by reading the current record for everything the skeleton does not author, rather than by the skeleton learning to carry them.
4. **The event carries the delta**, not only the sha256 of the bytes written: nodes and edges added, removed, changed, so a future replay from the ledger is possible. Existing events are not rewritten.

**Zero edits to:** the skeleton, the record's content (this task adds no node or edge), the projection loader, rule modules, harness, payloads, prior Results, `docs/reports/`.

**Immutable once written. Glob `2026-09-11_framework_single_writer_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 2, 4. The choke point, the refusal, the delta on the event.
## 2. Decision 3. The no-op test; if red, the generator preserves what it does not author. Stop if preserving requires the skeleton to change.
## 3. Gate (the one gate of this task)
Single-writer test; refusal test (a synthetic drop is refused without `--force`, accepted with `--force --reason` and the reason lands on the event); no-op regeneration test green; `test_the_round_trip_reproduces_every_row_cell_for_cell` green; projection round-trip green; record byte-identical to `HEAD` at the end of the task; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes nothing: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-11_framework_single_writer_RESULT.md`: what the skeleton does not author, by kind and count; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 (stop on a skeleton change) → glob addenda → §3 (detached, logged, polled) → §4 → push.
