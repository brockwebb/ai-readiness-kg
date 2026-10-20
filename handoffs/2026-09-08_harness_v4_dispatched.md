# Handoff — 2026-09-08 — scan-run-2 complete and verified; scan-harness-v4 dispatched

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-08_harness_v4_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. Verified (labelled Cypher, 2026-09-08)

- `00d95985` scan-run-2 **completed**. 211 live Results suffixed `_2026-09-07b`; `scan_a10_pass_2026-09-07b` = 17, `scan_a4_pass_2026-09-07b` = 21 (cycle 1: 16 and 19), `scan_requests_total_2026-09-07b` = 1469, `scan_rederived_findings_2026-09-07b` = 469, uncited bodies 418 → 417. DataFiles `scan_2026-09-07b`, `scan_matrix_2026-09-07b`. 9 live Figures (4 cycle-1 + 5 cycle-2), 399 edges. 31 Rules all with `MEASURES`. 359 observations reclassified (93 + 266). Framework 16/1/32 unchanged.
- Cycle-2 finding: almost every movement is `www.census.gov` serving `robots.txt` again (404 → 200; A4, A11-declared, A12, A5 move together); A1/A3 rule change moved no surface; ERS DNS transient makes `applicable_n` per leg (22 or 23).
- The substantive instrument defect: `RULE-A10-v2` scored `pass` on an unobserved (connection-reset) invalid-route probe; cycle-2 A10 17/23 contains at least one non-evidence pass. A8 followed an off-host pointer (2 requests to govdelivery, robots obeyed, no verdict rested on it).

## 2. Where the priority chain stands (operator asked)

Priority shift of 2026-09-06: harness → scan → collect → EDA/charts → report; ER after. **Everything before the report is done:** harness-scaffold `09745466`, scan-targets `22fb59b2`, scan-run `e3e38014`, projection repair `8ed10f14`, eda-and-charts `c1ede3d9`/`3be54ec9`, hygiene `7b5c0c30`, harness-v3 `6b9124bc`, scan-run-2 `00d95985`: all completed. The earlier outstanding items are also closed: extraction-gap diagnostic `0efa167e` completed 2026-09-04; the Seldon defect sweep completed per the 2026-09-06 overview. Open in this repo: `report-draft` `2517cda8` (placeholder, not due this week), `er_research_resumes` `37476f34` and the five ER-debt tasks (parked behind it by the priority shift), G1 EVAL v3 backlog (frozen instrument), and older design tasks (dispatcher `6ee71737`, chunker `1bd304b1`, DD-022 guard `9a627af8`, chunked-pilot writeup `f1da94c6`, essay `3b89a2f6`). Seldon repo: 11 open, two new this week (`814e95d7`, `066e5b69`), no cc_task written for either.

## 3. Dispatched

`f5f8d1c3` scan-harness-v4: blind-probe rule (`_common.unobserved` per probe, lint on gen ≥ 4), `RULE-A10-v3`, fixture `invalid_route_unobserved`, one same-host policy for every dereferencing collector, `RULE-A8-v3`, and **re-judging both real cycles from stored observations under v4 (`_rj1` cycles, no network)** so the report quotes corrected A10 numbers without re-contacting hosts.

## 4. Chain state

```
00d95985 scan-run-2 [completed]
  → f5f8d1c3 scan-harness-v4 [proposed]  ← dispatched (no federal hosts)
  → 2517cda8 report-draft [proposed] → 37476f34 er_research_resumes [proposed]
seldon: 814e95d7, 066e5b69 [proposed, no cc_task yet]
```

## 5. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-08_scan_harness_v4.md and only that task. Glob and read all sibling 2026-09-08_scan_harness_v4_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task. Do not contact any federal host.

## 6. What the next OODA should verify first

Five fixtures pass with `invalid_route_unobserved` producing A10 `error`; all five prior payloads byte-identical; zero non-fixture requests in the suite; `_rj1` Results for both cycles with the A10 delta stated per surface; A8 delta; cycle-1 re-judge skips A1/A3 (no `link_probe`) with a reason; F5 marks re-judged points; hygiene green. Then author `report-draft` from cycles 1, 2 and the `_rj1` re-judgments, quoting only registered Results. Operator inputs still open: A12 promotion (DD-054 §5), allowlisting contact with BLS/BTS/SSA, retention policy for the 417 contact-record bodies (DD-058 leaves it open).
