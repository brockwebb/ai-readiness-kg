# Handoff — 2026-09-08 — harness-v4 verified; frame reset to the full FSS; scan-frame-fss dispatched

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-08_scan_frame_fss_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. Verified (labelled Cypher, 2026-09-08)

- `f5f8d1c3` scan-harness-v4 **completed**. Findings 2,578 (756 re-judged), 33 Rules all with `MEASURES`, MeasurementSpec A10 → `RULE-A10-v3`, A8 → `RULE-A8-v3`; 281 `_rj1` Results. Re-judged A10: cycle 1 16/23 → **13/20**, cycle 2 17/23 → **13/19**; seven passes across the two cycles rested on connections never observed, three surfaces blind since cycle 1. A8 moved nothing (every surface fails its first clause). Seven payloads byte-identical. One pre-existing red test (`test_the_uncited_set_only_shrinks_and_only_by_citation`, 578 vs 418, stale pre-cycle tracked set) carried into the frame task §0.
- v4 defects found by its own gate: `resets_connection` was non-deterministic (EINVAL at connect; fixture fixed, classifier untouched); E5 `collector_pin` frozen at two fixtures; two readers assumed params and cycle name move together; the re-judgement's control gate wrote 54 fixture blobs into the committed store (caught by the hygiene gate; swept; sweep's attribution line was itself wrong and corrected by append).

## 2. Frame decision (operator, this session)

Tier A = the 16 OMB-recognized statistical agencies and units (13 principal + 3 units), every one. Tier B = departments of the other designated Statistical Officials, machine entry point and robots only, reported separately. No external comparators: NIST, GSA, data.gov, StatCan are not the same kind of thing; data.gov enters as a catalog-presence collector, not a row. Unit of analysis is the surface; no agency score. Tier 0 headline: A4, A5 (sitemap / llms.txt / well-known as separate counts), A10, A11-declared, A12 (beside), G1-D. Surface selection becomes a pre-registered rule (machine entry point + first 3 products in the agency's own listing order). UA gains a contact URL. Monthly cadence from cycle 3, scheduler installed only after cycle 3 validates the frame.

## 3. Chain state

```
f5f8d1c3 scan-harness-v4 [completed]
  → 4f1370b2 scan-frame-fss [proposed]  ← dispatched (roster fetch, listing fetches, pre-flight only; no scan)
  → (cycle 3 over the full frame, with A3-v5/A1-v4 blind-links fix and its fixture)
  → 2517cda8 report-draft [proposed] → 37476f34 er_research_resumes [proposed]
seldon: 814e95d7, 066e5b69 [proposed, no cc_task yet]
```

## 4. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-08_scan_frame_fss.md and only that task. Glob and read all sibling 2026-09-08_scan_frame_fss_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task. Contact only the hosts the task names, for the fetches it names; run no scan cycle.

## 5. What the next OODA should verify first

Suite fully green (the §0 red test fixed, with the method stated); `fss_roster_2026-09` DataFile with retained source body and Tier A = 16 by parse; `scan_targets_fss_2026-09` with listing digest and position on every entry and zero conversion-gap tasks; pre-flight Results for every host with the refusing and unreachable lists; `docs/design/scan_tool_map.md` regenerating byte-identically, with the `specified`-indicator verdict table; two DDs appended. Then author cycle 3: harness-v5 (A3-v5 / A1-v4 blind-links `error`, fixture that resets links only; uncited census reader) folded in as pre-flight, full Tier A + Tier B run, cycle-suffixed, F1 to F5 plus a Tier A / Tier B split, and the report-draft after it. Operator inputs open: A12 promotion; allowlisting contact; retention policy for contact-record bodies.
