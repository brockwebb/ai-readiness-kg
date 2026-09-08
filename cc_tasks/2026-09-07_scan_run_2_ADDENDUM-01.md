# ADDENDUM-01 to `cc_tasks/2026-09-07_scan_run_2.md` — resume at §3; the cycle exists on disk and on the log, and nothing after it does

**Date:** 2026-09-07 (night)
**Authored by:** Desktop session, OODA on the state the run left behind. **No RESULT file exists for scan-run-2; the ResearchTask `00d95985` is still `proposed`; `seldon cc complete` was never called.** Whatever was said in chat is not on disk and does not count.

**What is on disk and in the graph (verified):**
- `state/scan_2026-09-07b.json` (6.6 MB, written 01:44Z) and `state/scan_2026-09-07b_controls.json`. Cycle name `scan_2026-09-07b`, `params_hash 8762d72c…`, `control_verdict: pass` (65 control Findings), 40 surfaces, 404 Findings, 1,428 Observations, 1,469 requests, `error_class_unknown: 1`.
- Published: graph holds 469 Findings under `8762d72c` (404 + 65), Observations 3,717 → 5,297, Rule nodes 29 → 31 (`RULE-A1-v3`, `RULE-A3-v4` minted), `refused` = 317 (§1.2 done). `state/evidence_staging/` is empty (§1.1 promotion ran or nothing remained).
- §1.4 done: `scan_evidence_uncited_real_host_bodies` registered. §1.5 done (name moved).
- **Not done:** §3 gate output anywhere on disk; §4 (zero cycle Results, no `scan_matrix_2026-09-07b` DataFile); §5 (no `figures/scan_2026-09-07b/`, page not regenerated); §6 (no RESULT); `cc complete`.
- Unknown: whether §1.3 (the 22 `conversion_gap_withdrawn` overlays) ran; whether the DD from §1.4 was appended; whether the §3 gate was run and failed. **Do not re-run the hosts to find out.** The cycle is a measurement that was taken; it is not retaken because the paperwork stopped.

**Defects visible in the payload before any gate ran:**
1. `payload.task = "cc_tasks/2026-09-07_scan_run.md"`, the cycle-1 task file. `run.py` carries the task path from somewhere other than the invocation. Fix so the payload names the task that ordered the run (a `--task` flag, as `framework_writeback_rules.py` now has), and **amend** the published record by an append-only overlay rather than editing the payload or the events.
2. `error_class_counts.dns = 20`, all on two ERS surfaces (`scan-ers-machine`, `scan-ers-flagship-2-…`), and the observation records carry **no error text** (the `response`/`parsed` fields are empty where cycle 1 persisted `f"{type(exc).__name__}: {exc}"`). If the new `errors.py` path dropped the exception text, that is a regression of the evidence the reclassification overlay depended on: fix it, and report whether the 20 ERS `dns` are genuine name-resolution failures (they may be: ERS was fully observable in cycle 1, so this is a host-side transient, and it is why some legs now have 4 errors and `applicable_n` 22 rather than 23). The single `unknown` (Census ACS, A10) likewise has no text to classify from.
3. Two ERS surfaces went `error` on 5 and 4 legs respectively and observable on the rest, so `applicable_n` is now **per leg** (22 or 23), not the constant 23 cycle 1 had. Every rate, interval and F1/F5 label must use the per-leg denominator; state it on the axis.

**What to do, in order (this addendum supersedes the base task's SEQUENCING from §3 onward):**
- **§3 gate**, exactly as written, on the state as it stands: controls (already `pass` in the payload; re-derive it, do not trust the field), byte-identical re-derivation for `scan_2026-09-07b` and the four prior payloads, hygiene test green. Write the gate output to the RESULT **first**, before anything else, so a second stop leaves evidence. If the gate fails, the RESULT says which clause and stops; nothing is registered.
- Confirm §1.3 and the §1.4 DD from disk (`grep conversion_gap_withdrawn events/`; tail of `docs/design_decisions.md`); do what is missing.
- Fix defect 1 (code + overlay) and defect 2 (code; overlay nothing without text to ground it) before §4, with tests.
- **§4, §5, §6** as written, cycle suffix `_2026-09-07b`. F5 marks A1/A3 rule-changed. Section 6's cross-cycle paragraph must cover at least: A4 19→21 (three Census surfaces that failed in cycle 1 now pass, same rule), A11-declared 19→22, A10 19→17, G1-D 3→5 including `scan-census-machine` (a machine entry point, which the eda RESULT §5.5 said never passed), A12 8→9, ERS transient. Attribute each to host change, instrument change (A1/A3 only), or denominator change (ERS), and say which you cannot tell apart. No inference beyond that.
- RESULT §"why this run stopped": state only what the disk and the log show, not a reconstruction of what was intended. Then `seldon cc complete`, commit, push.

**SEQUENCING (this addendum):** §3 → RESULT header with gate output → confirm §1.3/§1.4 → defects 1 and 2 → §4 → §5 → §6 → `cc complete`.
