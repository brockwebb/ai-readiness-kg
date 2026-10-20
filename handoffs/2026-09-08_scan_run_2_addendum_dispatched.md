# Handoff — 2026-09-08 (early) — scan-run-2 ran and published but did not finish; ADDENDUM-01 dispatched

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-08_scan_run_2_addendum_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. State (verified from disk and graph)

- Operator reported "task done". **No RESULT file; `00d95985` still `proposed`.** The cycle itself ran as `scan_2026-09-07b` (UTC date had not rolled): controls pass (65), 40 surfaces, 404 Findings, 1,428 Observations, 1,469 requests total, published to the log and projected (Findings 1,822; Observations 5,297; Rules 31; `refused` 317). Only `scan_evidence_uncited_real_host_bodies` was registered. No matrix DataFile, no cycle Results, no figures, no page.
- Cycle-2 verdicts (from the payload, unregistered): A4 21/1/4, A11-declared 22/1/3, A10 17/6/3, G1-D 5/17/4, A12 9/3/1/1, A3 4/18/4 (rule v4), A1 0/22/4 (rule v3), A5 3/19/4, B3 4/19/3; zeros hold on A1, A2, A6, A8, A9, D1, D4, F4. `applicable_n` is now per leg (22 or 23): two ERS surfaces errored on some legs.
- Payload defects: `task` field cites the cycle-1 task file; 20 `dns` observations (all ERS) and 1 `unknown` carry no error text.

## 2. Dispatched

`cc_tasks/2026-09-07_scan_run_2_ADDENDUM-01.md`: resume at §3 on the state as it stands, gate output written to the RESULT before anything else, fix the two payload defects (code plus overlay, never an edit), then §4/§5/§6 with suffix `_2026-09-07b`, cross-cycle attribution paragraph, `cc complete`. **Hosts are not re-run.**

## 3. Chain state

```
6b9124bc scan-harness-v3 [completed]
  → 00d95985 scan-run-2 [proposed, cycle published, paperwork unfinished]  ← ADDENDUM-01 dispatched
  → 2517cda8 report-draft [proposed] → 37476f34 er_research_resumes [proposed]
seldon: 814e95d7 [proposed, no cc_task yet]
```

## 4. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Read CLAUDE.md, then execute cc_tasks/2026-09-07_scan_run_2.md together with cc_tasks/2026-09-07_scan_run_2_ADDENDUM-01.md; the addendum supersedes the base task from §3 onward and says where to resume. Only that task. Do not re-run any federal host.

## 5. What the next OODA should verify first

RESULT exists and opens with the §3 gate output; re-derivation byte-identical for `scan_2026-09-07b` and the four prior payloads; `00d95985` completed; per-leg Results suffixed `_2026-09-07b` with per-leg `applicable_n`; `scan_matrix_2026-09-07b` DataFile; five figures with `CONTAINS` edges; page regenerated; the `task`-field overlay and the error-text fix in place with tests; the 22 `conversion_gap_withdrawn` overlays and the retention DD confirmed; cross-cycle paragraph attributes A4/A11/A10/G1-D/A12 shifts and names what it cannot tell apart. Then author `report-draft` (`2517cda8`) from two cycles. A12 promotion and allowlisting contact remain the operator's inputs.
