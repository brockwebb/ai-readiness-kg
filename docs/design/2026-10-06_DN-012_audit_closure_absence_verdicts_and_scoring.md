# DN-012 — Design note: closing the audit's S1 findings. Absence verdicts, the frontier firewall, parent-host cells, and the rescan

**Date:** 2026-10-06. Desktop design note from `docs/audit/2026-10-04_full_audit.md` (task `2d9d2309`, RESULT at `cc_tasks/2026-10-04_full_audit_RESULT.md`): 66 findings, 7 S1. The reader gate's first fix is the absence verdicts. This note records the rulings the S1 closures need, so that each closing task implements a decision rather than making one. The audit itself was run under `claude-opus-5-5` because the hand-dispatch line carried no model; the Fable pass is the second cycle, after these closures (decision 6).

Under DN-005 §1 (the framework is the goal), DN-005 §5 (every task names its layer), DN-009 d3 (no weighting asserted), DD-001 (every assertion citable by a stranger).

---

## 1. Decisions

**d1. An absence verdict is never reached over a partial search.** A rule that would say `fail` on "nothing found" says `error` instead, naming what was not searched, whenever the candidate set was truncated (C-01: `link_probe.max_links_probed` cut 48 to 244 on-host links to 25), whenever the search never reached the place the indicator text names (C-04: ind:D4 says "data.gov/agency inventory" and RULE-D4-v3 reads only `<host>/data.json`), or whenever a documented location was declared and not followed (C-14: spec:A2 says "the documented API base" and the collector guessed three paths). `error` carries the unsearched remainder in its reason. This is the general form of the standing `unobserved_error` guard: blind is blind whether the cause is a refused fetch or a cap. Scope: every rule in `REGISTRY` that can say `fail` on absence, not only the three the audit named; the closing task lists them.

**d2. The candidate set for a product page is every on-host link, ranked, with the remainder recorded.** The cap stays as a request bound, because manners bound requests. What changes: candidates are ordered by data-likeness before the cap (archive and data extensions, `download` and `data` in the path or anchor text, `Content-Type` hints from the href) so navigation chrome stops consuming the budget, and every candidate past the cap is written as an Observation with `fetched: false` and `error_class: unprobed_over_cap`. A rule sees the unprobed count and applies d1.

**d3. Declared locations per body.** `targets.yaml` gains two optional per-body fields: `api_base` (the agency's documented API host and description path, read from the agency's own developer page and cited on the row) and `inventory_urls` (the data.json URLs data.gov harvests for the body: its own host's, its department's, and the `catalog.data.gov` organization page). A1/A2/A3 read `api_base`; D4 and the five legs that consume it read every `inventory_urls` entry before judging. Those hosts enter the roster for those legs only; this is not a sweep (operator scope ruling 2026-09-08), it is following the indicator text to where it points. Absence of a declaration is `error` under d1, never `fail`.

**d4. Frontier indicators leave the score. This is a defect fix, not a new ruling.** `design_decisions.md:537-539` and spec:A9 already say frontier mechanisms never enter a core score; `score.py` scored A9 for every body (C-06). `score.structure` excludes `frontier: true` the way it excludes candidates. Every quoted score regenerates. The firewall is not retired.

**d5. Parent-host cells do not score the unit.** Where the roster records `host_shared_with` (NCHS on cdc.gov) or the host is a department's (SOI on irs.gov, ORES on ssa.gov, DRSMSU on federalreserve.gov), cells read from that host (robots.txt, `/data.json`, `/.well-known/`, A4, A5, A11-declared, D2 and the data.json legs) are kept on the matrix, marked `parent_host`, and excluded from the unit's score and rank. Grounds: the roster already says such a finding "is not a finding about the statistical agency"; a rank built on cells the project disowns is not a rank. The alternative (score them and state the limitation beside every rank) leaves NCHS at 13 of 13 on CDC's files. The report and `docs/brief/H_limits.md` say which bodies lost which cells. Operator value call: this is the one ruling in this note that is a choice rather than a defect; it is made here and the operator overrides by editing this decision.

**d6. The rescan is operator-dispatched.** Fixing the rules under d1 to d3 re-judges the cycle of record into `error` where it was `fail`; that is an honest record of what the cycle did not look at. Collecting the missing observations needs new fetches on all 16 bodies. Under the standing rule (rescans are ad hoc, never automatic), the recollection task is written and registered but launched by the operator, not the dispatcher. The second-cycle audit, under `claude-fable-5-1` with the model on the launch line and on every subagent, follows the recollection.

**d7. Two public numbers for one quantity end (C-07).** The measured write-back runs against `scan_2026-09-10_rj4`; `measured_by` points at the cycle of record; the progress page and the brief print one count or two named quantities, never one name with two values.

## 2. What this note does not decide

Weighting (DN-009 d3 holds). The S2 and S3 findings, which the closing tasks list but do not take on. Whether `max_links_probed` should rise; d2 makes the cap honest, the manners layer sets its value.

## 3. Tasks authored under this note

`2026-10-06_absence_verdicts_rules.md` (d1 to d3, no network), `2026-10-06_absence_verdicts_recollection.md` (d3, d6, network, operator-launched), `2026-10-06_scoring_frontier_parent_host_counts.md` (d4, d5, d7), `2026-10-06_l0_report_robots_wording.md` (C-02), `2026-10-06_install_closure.md` (F-05).
