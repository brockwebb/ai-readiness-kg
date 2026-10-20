# Handoff — 2026-09-07 (evening) — repair + eda verified; hygiene and harness-v3 dispatched

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-07_hygiene_and_harness_v3_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. Verified this OODA (labelled Cypher, 2026-09-07 afternoon)

- `8ed10f14` framework-projection-repair, `3be54ec9` eda-and-charts cc_task, `c1ede3d9` eda-and-charts: all **completed**.
- Framework layer live: 16 measured / 1 harness_built / 32 specified; `MEASURES` = 29 = Rule count; `Rule.version` v1/v2/v3; 22 scan conversion-gap tasks `withdrawn`; DD-056 (cycle-suffixed names), DD-057 (projection contract) recorded.
- Registry: 30 Wilson bounds (0/23 hi = 0.143117, closed form 0.14311), 15 `control_fired` all 1, 21 per-criterion counts summing to 48, three snapshots (2/0/46 → 2/15/31 → 16/1/31), `scan_agencies_total_2026-09-07` = 14.
- Figures: 4 live + 4 superseded (eda §7.7); 120 `CONTAINS` + 4 `GENERATED_BY`. Page served at `readiness.home` (static webdesktop service, 200 / 113,145 bytes per RESULT; not re-curled by Desktop).
- Week goal met on the charts: F1 dot-and-interval per leg, F2 14-agency matrix, F3 gap map by criterion, F4 three snapshots.

## 2. Premises the RESULTs corrected (mine)

- Repair §2 named one map property to flatten; there were three. `EVIDENCED_BY` was 0 not 17. 29 Rule nodes ≠ 33 registry versions (4 crashed-generation `v2`s have no node).
- Eda §1 asked for a second Wilson implementation; the repo had one (`rollup.py::wilson_interval`); `stats.py` delegates. F3 needs indicator codes from the JSON as a third read source (labels only). Axis ticks are a third numeral class (declared in `figures.yaml`).
- `scan_agencies_total` had to be suffixed per DD-056, which I cited and then contradicted.

## 3. Defects carried forward (all in the two dispatched tasks unless noted)

- `RULE_VERSION = "v1"` constant on every Finding; input to `finding_id` → `finding_identity: 2` as a param (harness-v3 §1.1).
- 120 control Findings on batch-029 with no Observations on the log → annotate `evidence_unretained`, never delete (hygiene §1).
- `pytest assessment/` writes 47 fixture blobs into `corpus/evidence/scan/` per run; some already committed → tmp root + quarantine (hygiene §2).
- Framework JSON `counts` stale; A12 internal-ref key shape differs → normalize by write-back with event (hygiene §3).
- ECONNRESET filed as `dns`; A1/A3 double-HEAD; no refusing-host or reset fixture; no `purpose: scan_surface` admission escape; no suffix enforcement (harness-v3 §1.2–1.6).
- Seldon: `artifact create` allows duplicate Figure names; `superseded_by` restricted to ResearchTask; no Figure→DataFile edge → seldon task `814e95d7` (not dispatched; write its cc_task when a seldon session is open).

## 4. Chain state

```
e3e38014 scan-run [completed] → c1ede3d9 eda-and-charts [completed]
  → 7b5c0c30 scan-hygiene [proposed]      ← dispatched, runs FIRST
  → 6b9124bc scan-harness-v3 [proposed]   ← dispatched, runs SECOND
  → (next: scan-run cycle 2 against real hosts; then report-draft 2517cda8; then er_research_resumes 37476f34)
seldon: 814e95d7 Figure name uniqueness / superseded_by / Figure→DataFile [proposed, no cc_task yet]
```

## 5. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task files first, then read CLAUDE.md and execute cc_tasks/2026-09-07_scan_hygiene.md, then cc_tasks/2026-09-07_scan_harness_v3.md, in that order and only those tasks; stop after the first if its gate fails. For each, glob and read all sibling <filename>_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task.

## 6. What the next OODA should verify first

Hygiene: `MATCH (f:Finding) WHERE NOT (:Observation)-[:SUPPORTS]->(f) AND coalesce(f.evidence_unretained,false)=false` = 0 and annotated = 120; `git status --porcelain corpus/` empty after the full suite; quarantine count registered; round-trip gate still 7/7; JSON `counts` = 48/49.
Harness-v3: all three prior cycles byte-identical under their own params with `finding_identity: 2` in `params.yaml`; four fixtures, `unknown` error class = 0; fixture request log shows one HEAD per link; StatCan reclassification is an overlay event, not an edited line; `CURRENT` lists A1-v3, A3-v4 and the rest unchanged.
Then author cycle 2 (`scan-run-2026-09-xx`): same targets file, cycle-suffixed names only, expect the 4 invisible agencies to stay invisible unless the operator has decided on allowlisting contact or a second client identity (DD-054 §5). Those two remain his inputs; do not decide them.
