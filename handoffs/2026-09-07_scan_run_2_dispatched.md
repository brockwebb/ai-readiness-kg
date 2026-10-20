# Handoff — 2026-09-07 (night) — hygiene + harness-v3 verified; scan-run-2 dispatched

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-07_scan_run_2_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. Verified this OODA (labelled Cypher, 2026-09-07 evening)

- `7b5c0c30` scan-hygiene and `6b9124bc` scan-harness-v3 **completed**, gates green.
- Findings: 0 unsupported-and-unannotated, 120 `evidence_unretained`. Observations: 93 `error_reclassified` (92 dns→connection_reset, 1 dns→unknown); classes now http_4xx 1458 / connection_reset 92 / http_5xx 44 / robots_disallowed 15 / collector_unavailable 3 / unknown 1 / dns 0.
- Results `scan_control_findings_evidence_unretained_2026-09-06` = 120, `scan_evidence_fixture_blobs_quarantined` = 260. MeasurementSpec A1 → `RULE-A1-v3`, A3 → `RULE-A3-v4`. Framework 16/1/32 unchanged. 29 Rule nodes (the two new rules get nodes on their first Finding; not a defect).
- `finding_identity: 2` in params; all three prior cycles (286/33/437) plus the second controls payload (33) re-derive byte-identically.

## 2. Premises the RESULTs corrected (mine)

- Hygiene: the litter came from `tests/test_scan_harness.py` (24 blobs/run), not `assessment/`; a blanket "no fixture-host blob" rule would have stranded 8 cited control bodies (narrowed to uncited); `counts` had not drifted (candidate-excluded by DD-054); four writers existed, not zero; no `framework_writeback` event had ever existed (the task installed the convention it described as established).
- Harness-v3: 93 misfiled observations across four targets plus a Census redirect case, not three surfaces; the pre-registered fixture table was wrong for A11-declared (declared layer served → verdict, not error) and CC derived the right one before running; the "zero edits to the JSON" line collided with the spec-rule test, resolved by the two-line `rule_id` write-back with event.
- CC's own: `run.py --controls-only` clobbered a registered payload (recovered; `refuse_clobber` added); real runs outside pytest still litter the store.

## 3. Decisions taken in scan-run-2 (operator overrides if wrong)

- One error convention on the log: the 266 `http_4xx`-on-403 observations overlaid to `refused`.
- Evidence promotion on publish (staging root per run); the 418 tracked uncited real-host bodies retained as the record of host contact, registered, excluded from integrity checks (DD to be appended by the task).
- 22 stale `conversion_gap` events annotated, not closed.

## 4. Chain state

```
e3e38014 scan-run [completed] → c1ede3d9 eda-and-charts [completed]
  → 7b5c0c30 scan-hygiene [completed] → 6b9124bc scan-harness-v3 [completed]
  → 00d95985 scan-run-2 [proposed]   ← dispatched (touches federal hosts; ~559 fewer requests than cycle 1)
  → 2517cda8 report-draft [proposed] → 37476f34 er_research_resumes [proposed]
seldon: 814e95d7 Figure name uniqueness / superseded_by / Figure→DataFile [proposed, no cc_task yet]
```

## 5. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-07_scan_run_2.md and only that task. Glob and read all sibling 2026-09-07_scan_run_2_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task.

## 6. What the next OODA should verify first

Control gate over four fixtures with `unknown` = 0; re-derivation byte-identical for cycle 2 and all four prior payloads; `git status corpus/` shows only promoted cited bodies; request counts per host below cycle 1 and one HEAD per link; `error_class = 'refused'` covers the 266 and no `http_4xx` remains on a 403; every new Result name ends in the cycle; F5 marks A1/A3 as rule-changed; no status moved unless the RESULT says why; A12 still candidate; 4 agencies still without an admitted surface unless the operator decided on allowlisting or a second client identity (DD-054 §5), which remain his inputs.
Then: author `report-draft` (`2517cda8`) from two cycles, or a `v4` harness task if cycle 2 surfaces something no fixture anticipated. Also open: a seldon-repo cc_task for `814e95d7`.
