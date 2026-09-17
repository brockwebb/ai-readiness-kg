# CC Task: the figure gate reads the cycle of record from where the report reads it; a guard that cannot run says so on the record

**Date:** 2026-09-17
**Project:** ai-readiness-kg (this repo only)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_long_running_rule_matches_harness_RESULT.md` §2 Findings A and B.
**Implements:** the reported-first rule in `CLAUDE.md` (a figure is built from a matrix that exists; a gate that skips is not a gate) and DN-005 §5 rule 1 (Tier M is the cycle of record, measured, and its figures are gated).
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M. The current cycle of record's figures are ungated today.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher. This is the first launch by a dispatcher pass running the session-identity fix (`2026-09-16_session_id_names_the_process_RESULT.md` §0 item 3), so its RESULT §0 is that fix's live observation.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

## 0. The defect, stated once

`assessment/harness/scan/params.yaml:125` says `cycle.name: scan_2026-09-10`. The disk holds `state/scan_matrix_2026-09-10_rj1.json`, `_rj2.json` and the per-tier `_rj2` matrices; there is no base `scan_matrix_2026-09-10.json`. `tests/test_scan_figures.py` (five tests, 14 cases) and `tests/test_scan_run_2.py:534` resolve the cycle from `params.yaml` and skip with "has not been reported". The report and the site cite the re-judged matrix. So the tests answer a question about a file that will never exist, and 15 skips per run stand in for a gate on the cycle of record.

**Decisions taken here (operator overrides later):**

1. **One resolver for "the cycle of record".** Find where the report build and the site count read which matrix is the cycle of record (`scripts/build_report.py`, `scripts/build_projection.py` or the cycle-of-record declaration, whichever holds it). The figure and denominator tests resolve the cycle through that same function. `params.yaml`'s `cycle.name` remains what the harness runs; the tests no longer read it for "reported". A skip remains only when no cycle has been reported at all, with that as its reason.
2. **The gate must actually gate.** After decision 1 the 15 tests run against the `_rj2` matrices. If any fails, that is a finding about the figures of record, not a reason to re-skip: fix the figure or the matrix reference, and the RESULT quotes the failure and the fix. If they pass, the RESULT quotes the 15 as passed with the matrix path each one resolved to.
3. **`tests/test_dispatch_config.py:333` declares its condition.** The quiet-checkout assertion is marked `interactive_only`, with a skip reason that names the marker and the reason the state cannot be quiet inside a dispatched session. Its configuration-invariant half, if it has one, is split into a test that runs everywhere. A skip by design, on the record, is not the same defect as a skip by accident.
4. **Prior art before any of this.** Read `cc_tasks/2026-09-10_harness_v5_blind.md` and its RESULT for why skip-with-reason was introduced, and whatever DD covers the cycle-of-record declaration. If the intended resolver already exists and the tests simply bypass it, say so and use it.

**Write set:** `tests/test_scan_figures.py`, `tests/test_scan_run_2.py`, `tests/test_dispatch_config.py`, the shared resolver's module only if the tests need an import it does not expose, `seldon_events.jsonl` by this task's transitions, the RESULT. `params.yaml` unchanged. `docs/` byte-identical. No matrix, figure or report is rebuilt.

**Immutable once written. Glob `2026-09-17_figure_gate_reads_cycle_of_record_ADDENDUM*.md` before starting and again before §3.**

---

## 1. RESULT §0 first: quote this session's `SELDON_SESSION_ID`, the `dispatch_launched` event with its `child_session_id`, and one of this session's own `cc`-actor events, all from the store. This evidence exists only in this window.
## 2. Decisions 4, 1, 2, 3 in that order.
## 3. Gate
`make gate-full` (`-rs`), detached with `nohup bash -c '<cmd>; echo EXIT=$?' > log 2>&1 &` and polled inside this turn with the bounded loop `CLAUDE.md` now gives; `seldon verify`; protected paths. Expected skip count after this task: 3 (the parametrisation by design, the data condition, and the declared interactive-only guard). A count above 3 needs each extra reason quoted. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-17_figure_gate_reads_cycle_of_record_RESULT.md`: §0 the session-identity observation; §1 the resolver found and how the tests now call it; §2 the 15 formerly skipped tests with outcome and resolved matrix path each; §3 the interactive-only split; §4 every premise this task file got wrong; §5 the gate table with passed, skipped, xfailed, deselected, wall clock and log path, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
