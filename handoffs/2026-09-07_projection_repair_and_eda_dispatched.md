# Handoff — 2026-09-07 (afternoon) — scan-run OODA done; projection repair + eda-and-charts dispatched

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-07_projection_repair_and_eda_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. What this OODA verified (labelled Cypher, 2026-09-07 after 11:38Z)

- `scan-run` `e3e38014` **completed** (cc_task `df4ce826`); seldon `4ab0bd16` / `1ad92c2b` (precedence labels) **completed** 09:51Z; both dispatch lines from the previous handoff are closed.
- Registry matches the RESULT: 149 Results, per-leg counts and rates as in RESULT §4; A12 8/4/1/1; `scan_findings` 404, `scan_observations` 2018, `scan_surfaces` 40. Graph: 3,717 Observations, 1,353 Findings, 29 Rules. DataFile `scan_matrix_2026-09-07` `f2e33667`.
- Framework of record (`framework/ai_readiness_framework.json`): 49 indicators, 16 measured / 1 harness_built (E5) / 32 specified incl. candidate A12. RESULT §8 holds against the JSON.

## 2. Premises found wrong (beyond RESULT §7)

- **Neo4j framework layer is stale.** Graph shows 48 `AssessmentIndicator`, 46 specified / 2 measured, no A12; neither the 02:16Z rule-review write-back nor the 11:03Z scan-run write-back reached it. Root cause unknown (repair task §1). Until repaired, Cypher verification of framework state verifies a two-write-backs-old projection.
- Every `Rule.version` = `v1` regardless of `rule_id`; no `Rule→AssessmentIndicator` edge exists, so evidence cannot be traversed to the framework (operator's "progress at every level" requirement unmet in the graph).
- Previous handoff said "every measurement_status is harness_built except G1"; the registry shows 15 harness_built / 31 specified at 02:16Z. Progress vocabulary is specified → harness_built → measured.
- 22 open `Conversion gap ... on scan-*` ResearchTasks were emitted at scan-surface admission (02:06Z); false premise (landing pages are observation targets, not corpus). Withdrawal delegated to the repair task §4.
- Wilson intervals quoted in RESULT §4 are not registered Results (DD-040 gap); registered by eda §1.
- Cycle-level bare Result names will collide on cycle 2 (RESULT §7.4); convention recorded as a DD by repair task §5.

## 3. Chain state

```
09745466 harness-scaffold [completed] → 22fb59b2 scan-targets [completed] → e3e38014 scan-run [completed]
  → 8ed10f14 framework-projection-repair [proposed]  ← dispatched, runs FIRST
  → 3be54ec9 eda-and-charts cc_task [proposed] fulfils c1ede3d9 eda-and-charts [proposed]  ← dispatched, runs SECOND
  → 2517cda8 report-draft [proposed]
  → 37476f34 er_research_resumes [proposed]
```

## 4. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task files first, then read CLAUDE.md and execute cc_tasks/2026-09-07_framework_projection_repair.md, then cc_tasks/2026-09-07_eda_and_charts.md, in that order and only those tasks; stop after the first if its gate fails. For each, glob and read all sibling <filename>_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task.

## 5. What the next OODA should verify first

Repair task: §1 root cause is a file:line, not a guess; round-trip test green and in `tests/`; `MATCH (r:Rule)-[:MEASURES]->(:AssessmentIndicator)` = 29; status distribution 16/1/32 by Cypher; 22 tasks `withdrawn` (not completed, not superseded); new DDs numbered from the file, not invented.
EDA task: 30 Wilson Results registered; the four SVGs contain no numeral that does not resolve to a Result; F2 shows 14 agencies; F4 has three points and no trend line; page served through webdesktop (curl check in RESULT); error-class breakdown absent.
Then the next task is the second scan cycle's `v3` list: `ERROR_CLASSES` gains a reset/refused member (§6.2), shared per-surface link probe for A1/A3 (§6.3), a refusing-host control fixture for A12 (§6.5), `purpose: scan_surface` skip in the admission gate (repair task §4), cycle-suffixed names.

Standing operator inputs still open (his, not the machine's): promote A12 or not (DD-054 §5); contact BLS/BTS/SSA for allowlisting.
