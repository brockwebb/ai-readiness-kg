# Handoff — 2026-09-08 (evening) — frame task stopped at §2; selection rule replaced by ADDENDUM-02; Tier C (ADDENDUM-01) not yet run

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-08_scan_frame_fss_addendum2_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. State (disk and graph, 2026-09-08 evening)

- `4f1370b2` scan-frame-fss **proposed**, no RESULT. Done: §0 (assumed; verify the red test), §1 roster (Tier A 16 by parse, Tier B 14, `fss_agencies_tier_a` = 16, one disagreement resolved by charter authority: ORES). Not done: §2 registration, §3 pre-flight, §4 tool map, §5 DDs, §6, §7, and all of ADDENDUM-01 (Tier C).
- §2 as I wrote it produced a worse frame than the hand list (12 flagships vs 26, 10 of 16 agencies without a machine entry point, substring matches such as `api` in "Capital Markets"). Replaced by ADDENDUM-02: machine entry point derived from each department's `/data.json` (OPEN Government Data Act inventory, DCAT-US); flagships **declared** (cycle-1's 26 stand; shortlist from `data.json` by `modified` for the three units and thin agencies, operator picks); Tier B and Tier C `data.json` presence and host probes only.

## 2. Operator input now open

Flagship declaration for the three units (Fed MSU, SAMHSA CBHSQ, APHIS NAHMS) and any Tier A agency with fewer than two cycle-1 flagships: pick from `docs/design/fss_flagship_shortlist.md` once the task writes it. Tier-0 measurement does not wait on this. Still open from before: A12 promotion; allowlisting contact; retention policy for contact-record bodies.

## 3. Chain state

```
f5f8d1c3 scan-harness-v4 [completed]
  → 4f1370b2 scan-frame-fss [proposed; §0-§1 done; ADDENDUM-01 + ADDENDUM-02 dispatched]
  → cycle 3 (harness-v5 blind-links fix as pre-flight; full Tier A/B/C run)
  → 2517cda8 report-draft → 37476f34 er_research_resumes
seldon: 814e95d7, 066e5b69 [proposed, no cc_task yet]
```

## 4. Open dispatch line

In `/Users/brock/GitHub/ai-readiness-kg`:

> Read CLAUDE.md, then execute cc_tasks/2026-09-08_scan_frame_fss.md together with its ADDENDUM-01 and ADDENDUM-02 siblings; ADDENDUM-02 replaces §2 and says where to resume, ADDENDUM-01 adds Tier C. Only that task. Contact only the hosts the task and addenda name, for the fetches they name; run no scan cycle.

## 5. What the next OODA should verify first

RESULT exists and opens with what the disk showed; `scan_targets_fss_2026-09` registered with `data.json` digests, every Tier A row sourced from an operator declaration or an inventory record, no substring-matched anchors; `fss_agencies_with_api_distribution_in_edi`, `fss_departments_publishing_data_json`, `fss_flagships_declared`, `fss_flagships_pending` registered; pre-flight Results for every Tier A, B and C host; `docs/design/scan_tool_map.md` regenerating byte-identically with the `specified`-indicator verdict table and a `/data.json` collector row; `fss_flagship_shortlist.md` written; two DDs appended; suite green including the previously red test. Then cycle 3.
