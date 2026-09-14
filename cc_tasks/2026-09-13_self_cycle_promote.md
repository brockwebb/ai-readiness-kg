# CC Task — the self cycle joins the record: promoted, on the event log, in PRIOR_CYCLES; and the licence reaches every published face

**Date:** 2026-09-13
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-13_self_row_RESULT.md` §7, §10 items 1, 4, and `2026-09-13_ephemeral_provenance_RESULT.md` §9 items 1, 3.
**Implements:** DN-002 decisions 2 and 5; under DD-001 and DD-055 (a body a Finding cites is retained or the Finding says it is not).
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs before `2026-09-13_rule_a12_v3.md`, so the self cycle is a prior cycle when generation 10 re-judges.
**Spend:** zero model calls. **Network: none.** The payload and its staged bodies are on disk.

**Two concerns, one deliberate exception to one-gate-per-task, stated.** The licence on `docs/llms.txt` and on the report's title block is two lines and a test, deferred by three consecutive RESULTs because each task's widening excluded it. A change that small carried forward three times is a process defect; it rides here, does not touch any verdict input in a way any leg reads (A5 reads the authority root's `llms.txt`, which is 404), and is asserted separately in the gate.

**Decisions taken here (operator overrides later):**
1. **`publish.py --from state/self_2026-09-13.json --project`**, in the only order it permits: promote the 34 staged bodies into `corpus/evidence/scan/` content-addressed, then `write_events`, then re-project the scan layer. Every `body_in_committed_store: false` on the self row flips to true on regeneration of `state/self_l0_self_2026-09-13.json` and the index; no verdict, reason, URL or status changes, asserted by diff.
2. **`self_2026-09-13` enters `PRIOR_CYCLES`** with its Finding count (6), so the retention census, the invariant readings and every re-judgement see it as a stored payload. The re-derivation under base-from-git + overlay keeps passing.
3. **The licence on every published face.** `docs/llms.txt` gains a licence section generated from `publication.yaml`; the report's generated version block gains one line (`Licence: report and data CC BY 4.0; code MIT`) so the PDF a reader meets first states it; `make report-pdf` rebuilt, numeral-multiset gate and bare-numeral lint green, page counts unmoved or re-registered. A test asserts both faces carry both SPDX ids, extending A5's consumer set to five.
4. **`docs/robots.txt` and `docs/sitemap.xml` untouched**; the self row's measured inputs other than `llms.txt` are byte-identical before and after, asserted.

**Zero edits to:** rule modules, harness runtime, manners, prior payloads, prior Results' values and states, prior RESULTs, figures, section prose, the skeleton, the record, `corpus/` beyond the promotion under decision 1, `docs/robots.txt`, `docs/sitemap.xml`.

**Immutable once written. Glob `2026-09-13_self_cycle_promote_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 2. Stop if promotion would write any body whose digest already exists under a different path, or if `write_events` would emit an event for a Finding not in the payload.
## 2. Decisions 3, 4.
## 3. Gate (the one gate of this task, plus the stated exception's own clause)
34 bodies promoted, content-addressed, digests matching the payload; events written for 6 Findings and 13 Observations; scan layer re-projected and the 6 `self_l0_*` Results' provenance resolves into `corpus/`; `PRIOR_CYCLES` carries the self cycle; retention census shows 0 unretained on it; both invariant readings 0; self payload re-derives byte-identically; row regenerated with `body_in_committed_store: true` on every read and no other field changed; licence test green on all five faces; PDF gates green; `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes nothing into `corpus/` or the log: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-13_self_cycle_promote_RESULT.md`: promotion and event counts; the row diff (expected: only `body_in_committed_store`); the licence faces; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (stop on a digest collision or a stray event) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
