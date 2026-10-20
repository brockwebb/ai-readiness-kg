# Handoff — 2026-09-07 — scan-run dispatched; instrument week, day 2

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-07_scan_run_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol for the thread itself: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)". "Task done" from the operator means run the loop; the operator does not need to say OODA.

---

## 1. Where we are

**Priority (operator, 2026-09-06):** KG frozen as good-enough (`kg-freeze-2026-09-06`, DD-049); instrument first. Week goal: scan, collect, EDA and charts showing progress; written report later. ER research resumes after `report-draft` (`er_research_resumes` `37476f34`, six predecessors).

**Framework of record:** `framework/ai_readiness_framework.json` (DD-050); skeleton §2–§5d tables are a rendered projection with a cell-for-cell round-trip gate. 7 criteria, 47 constructs, 48 indicators (G1 split), plus one **candidate** A12 (declared-vs-enforced machine access, DD-054) in its own rendered table — promotion is the operator's call, and the DD states what promotion would require.

**Harness:** `assessment/harness/scan/` — Observation/Finding split, whole bodies content-addressed and committed, every constant in `params.yaml` hashed onto every record, rules pure and versioned (`REGISTRY` + `CURRENT`), re-derivation byte-identical per rule version, two control fixtures as the E5 gate, integer-literal lint (fired on its own author twice). All 16 v1 rules reviewed against spec: 0 conform — a single habit (first clause only) invisible to controls built by the same author. 12 `v2` rules; A4/A5/A9 closed by `decision` on the spec; G1-D review was a false positive caused by my protocol (rule shown without collector — DD-053 §5). F-UJI is a server, not a package; deferred (`fuji.available: false`).

**Targets:** 13 principal statistical agencies (SPD-1, read from fss-policy-kg) + StatCan comparator. 41 surfaces (26 admitted docs under epoch `scan-2026-09` + 14 well-known sets); 3 hosts (BLS, BTS, SSA/ORES) refuse the identified compliant UA on every probe; only 2 of 14 hosts serve `/data.json`; Census serves no robots.txt; NCES listing is JS-only. **Nothing has been measured yet** — every `measurement_status` is `harness_built` except G1 (`measured`, DD-036).

## 2. Chain state (from `seldon go`, 2026-09-06 late)

```
09745466 harness-scaffold [completed] → 22fb59b2 scan-targets [completed]
  → e3e38014 scan-run [proposed]  ← NEXT READY (cc_task df4ce826 registered, dispatched below)
  → c1ede3d9 eda-and-charts [proposed]
  → 2517cda8 report-draft [proposed]
  → 37476f34 er_research_resumes [proposed]  (also waits on 43edd2cc / 26214693 / f9c5d054 / d9c26f0c / 4e132d0e)
```

Seldon side: `precedes` shipped (AD-029, domain 0.3). `seldon verify` in this repo shows one issue — the Precedence check reads `(:Concept)-[:PRECEDES]->(:Concept)` KG edges by name; fix is seldon `1ad92c2b` / cc_task `4ab0bd16`, dispatched below.

## 3. Open dispatch lines

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-07_scan_run.md and only that task. Glob and read all sibling 2026-09-07_scan_run_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task.

In `/Users/brock/GitHub/seldon` (independent, run in parallel):

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-07_precedence_artifact_labels.md and only that task. Glob and read all sibling 2026-09-07_precedence_artifact_labels_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task.

## 4. What the next OODA should verify first

When `scan-run` reports:
1. Control gate and both re-derivation gates (this cycle; and the v1 smoke cycle still byte-identical under v1 — history untouched).
2. `measured` moved only for indicators meeting DD-055 (a non-error Finding on an admitted observable surface); A12 still `candidate`; no composite, no agency ranking registered.
3. Per-leg pass rates carry Wilson intervals and state the observable-surface denominator; 3 unobservable agencies reported, not dropped.
4. The RESULT's list of "things a surface did that no fixture anticipated" — those are `v3` candidates and the input to the next task.
Then author `eda-and-charts` (`c1ede3d9`): per-leg pass rates with intervals, agencies × legs matrix, gap map by criterion, positive-progress view (harness_built → measured over the week), floors from the fixtures, all fractions with counts. Operator wants charts by end of week; prose report is `report-draft`, not this week.

Standing operator inputs still open: promote A12 or not (needs a second compliant client identity to be honest — see DD-054 §5); whether to contact BLS/BTS/SSA for scanner allowlisting (public, under his name — his call, not the machine's).
