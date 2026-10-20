# Handoff — 2026-09-08 (thread close) — frame settled at 16 + 3; scan-run-3 dispatched; next thread picks up its RESULT

**Resume line for the next Desktop thread (copy exactly):**

> `seldon go --brief /Users/brock/GitHub/ai-readiness-kg/handoffs/2026-09-08_thread_close_scan_run_3_dispatched.md` — read the handoff, verify its premises against the graph before trusting them, then act on its final section.

Protocol: `CLAUDE.md` §"Desktop session protocol (operator-ordered, 2026-09-07)".

---

## 1. Where the work stands (verified, 2026-09-08 evening)

Priority chain since 2026-09-06: harness → scan → collect → EDA/charts → report; ER after. **Every step before the report is complete** and verified in the graph: harness-scaffold, scan-targets, scan-run (cycle 1), projection repair, eda-and-charts, hygiene, harness-v3, scan-run-2, harness-v4 (re-judged both cycles), scan-frame-fss. Frame task `4f1370b2` completed: gate PASS, 1,592 tests green, `seldon verify` clean.

**The frame (DD-059):** 16 OMB-recognized statistical agencies and units (Tier A) plus three tier-0 reference hosts data.gov, NIST, GSA (Tier C). 19 hosts, 65 surfaces, all declared (24 carried from cycle 1 by host), none derived. No Tier B, StatCan out. **Client identity (DD-060):** one UA `0.2` with contact URL; refusals are findings; monthly cadence after cycle 3, no scheduler yet.

**Pre-flight over the 19:** all reachable; 15 serve `robots.txt` (Fed 404s it; BLS, BTS, SSA 403 it); those three have refused the identified client on four measurements; EIA home 503 twice.

**Two cycles plus re-judgement on the log:** cycle 1 (2026-09-07), cycle 2 (`2026-09-07b`), both re-judged under v4 (`_rj1`). Eight of 15 legs are 0/n on every observable surface in every cycle, controls proving the rules fire. Almost every cycle-1 → cycle-2 movement was Census serving `robots.txt` again. Corrected A10 (blind probes → `error`): 13/20 and 13/19.

## 2. What this thread got wrong, so the next one does not

- Desktop turned the operator's hand-picked surface list into a derivation problem (home-page scraping → `/data.json` → CISA registry → data.gov API → 26 departments). Three addenda, three CC stops, one operator intervention. **Rule:** when a hand list exists and the measurement does not depend on the selection rule, the hand list is the frame. Value inputs (what counts as a flagship) are the operator's; do not derive them.
- Desktop dispatched on a stale snapshot twice (ADDENDUM-01 to scan-run-2 duplicated work CC had already done; "run in progress" read of the frame task was wrong). **Rule:** read the disk and graph timestamps before writing an addendum; a RESULT is the only proof of completion, and a task that stops must still write one.
- Two named-source findings worth a sentence in the report, not a workaround: the government publishes no machine-readable department → inventory map, and catalog.data.gov's CKAN API answers 404 to an identified client.

## 3. Dispatched, awaiting RESULT in the next thread

`d261be8b` **scan-run-3**: declares `params.tier0.legs`, adds the blind-links rules (`A1-v4`, `A3-v5`) with fixture `resets_links_only` (six fixtures), runs the first cycle over all 19 hosts (Tier C on tier-0 legs only, 7 thin agencies on home and probes), registers cycle-suffixed Results incl. per-host request counts, F1 to F6 with a Tier C block, `cc complete`, push.

## 4. Chain state

```
4f1370b2 scan-frame-fss [completed]
  → d261be8b scan-run-3 [proposed]  ← dispatched
  → 2517cda8 report-draft [proposed] → 37476f34 er_research_resumes [proposed]
seldon: 814e95d7, 066e5b69 [proposed, no cc_task yet]
```

## 5. Open dispatch line (already given to the operator; re-issue only if CC has not started)

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-08_scan_run_3.md and only that task. Glob and read all sibling 2026-09-08_scan_run_3_ADDENDUM*.md files before starting and again before §2; an addendum can amend or SUPERSEDE the base task. Contact only the 19 hosts in scan_targets_fss_2026-09.

## 6. What the next OODA does

1. Read `cc_tasks/2026-09-08_scan_run_3_RESULT.md`; if absent, check `d261be8b` state and `state/scan_<date>.json` before assuming anything.
2. Verify: six-fixture control gate; byte-identical re-derivation for all eight payloads; zero Tier C Findings outside `tier0.legs`; Results suffixed with the cycle; Tier A and Tier C matrices; F6 present; page regenerated; `cc complete`; pushed.
3. Then author **report-draft** (`2517cda8`) from cycles 1, 2, 2-rj1, 3: quoting only registered Results by name; structure = frame and instrument, tier-0 headline (Tier A), the eight zero legs with controls, refusal consistency, Tier C block, what moved and why, non-claims, what the instrument cannot see. It goes out under the operator's name, so the draft is category 2: he reads it before it leaves the repo.
4. Operator inputs still open, do not decide them: the 7 flagship declarations (`docs/design/fss_flagship_shortlist.md`); A12 promotion (DD-054 §5); allowlisting contact with BLS/BTS/SSA; retention policy for the 417 contact-record bodies (DD-058).
