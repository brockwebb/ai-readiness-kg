# Desktop session close — 2026-08-30

**Verified against `seldon_task_list` and the live graph before writing (AD-007). Open tasks: 3 (plus superseded noise). Everything else below is committed state, not memory.**

## Where the project stands

**Pilot §3 CLOSED — UNDER-EXTRACTION, FAIL branch, parent 64661f7a completed at 0cdd3aa.**
Three arms, one variable each, on the same 44 chunks (paired design):

| arm | profile | yield ratio (floor 0.60 vs 45.23) | faithfulness | $/item |
|---|---|---|---|---|
| A | v0_3_7 anchor contract | 0.347 | F=0, PASS | $0.0052 |
| A2 | +FIRST GROUNDING RULE | 0.537 | F_upper 0.0243, PASS | $0.0029 |
| A3 | +character-exact | 0.560 | PASS | $0.0034 |

- A2 and A3 proposed the identical 1,766 items — the rules move admission only; isolation measured, not assumed.
- A3 falsified its pre-registration informatively: "copy exactly" → longer anchors → over-budget +73 (now the binding constraint), non-unique −40% (pre-registered as unreachable — reasoning error recorded). A3 also regressed cites (+32) and Instrument recall (0.905→0.888). **A2 may be the better production profile.**
- The floor's target (45.23, from unvalidated v0.3.5) is the suspect. Per recorded closure: **no further arm, Arm B included, before ground-truth re-derivation.** Arm B ceiling declared, 0 committed, blocked.
- Cost question is closed: 7× cheaper than baseline at F=0.

**IN FLIGHT: ground-truth re-derivation (35094dc4, `cc_tasks/2026-08-30_ground_truth_yield_floor.md`).** Opus-5 double-annotation of 5 comparator chunks under a derived, sha-pinned rubric (schema → crosswalk consumers → SciERC/ACE/TAC-KBP, all verified and cited). Re-derives floor = 0.60 × measured ground-truth yield; scores A, A2, A3 AND v0.3.5 against it; picks the production profile by measurement. Reported discrepancy (accepted): comparator spans only 2 docs, so sample is 3+2 not 1×5. Only operator touchpoint: inter-pass Jaccard < 0.5 → stop and report (incident-class). **Next session: read its RESULT first.**

**Decision tree after re-derivation:**
- A profile clears the re-derived floor → write the **bulk task**. Hard requirements already recorded in the closure: burn-time acceptance sampling (ADDENDUM-06 §3, Dodge–Romig/SPRT, batch quarantine rules pre-registered); extract/defer cut per doc (crosswalk demand ≥1 or nonzero centrality; rest = `admitted, not extracted, reason: no consumer` on the manifest); ordering by `state/t2_priority.json`; stratified corpus confirmation (ADDENDUM-06 §1) inherited by the bulk task.
- No profile clears → one design cycle on the anchor budget (the A3 falsification scoped it: 10-token limit vs verbatim discipline are in tension). New pilot task, not an addendum.

## Completed this session (all pushed)

- **OpenAlex auth + eligibility** (e858b1e8, completed): root cause was retired auth model (key required since 2026-02-13), not quota. Key wired from `~/.wintermute/.env` `OPENALEX_API_KEY`. T0 complete: 40/46 eligible resolved, 0 retryable, 132 measured-ineligible (predictions converted to measurements, ~2,900 credits). Nightly biblio launchd job live and now meaningful.
- **Acquisition round 2** (61cc65ff, completed): manifest at **194 included** (commit 750a2b6). Reference parsing from Docling output (`bibliographic_derived` class), SEO/AI-O/GEO cluster searched, every candidate decided admit-or-cut with reasons on the manifest. Phantom-ledger scare retracted after field-level verification (0 dup url/sha/title); positive-control detector added.
- **Pilot arms A2, A3 + closure** (above).
- **`source_type` vs `doc_type` erratum**: `source_type` is what you pass in (admission API), `doc_type` is what you read back (projection). Both names live; task authors beware.

## Open tasks (graph-verified)

1. **35094dc4 ground truth yield floor** — RUNNING. Everything blocks on it.
2. **f1da94c6 publication writeup** — gated on re-derivation verdict. Foils file at `docs/research/writeup_foils.md` (Karpathy lint = coherence-not-correspondence — corrected claim, do not overstate; OKF; shared thesis: quality operations without quality measurement). New material this session: the A3 falsification (budget-vs-verbatim tension), the floor-miscalibration arc, TAC-KBP provenance rule independently re-derived by repo's v0.3.4 (prior-art-not-consulted, §7.5 exhibit).
3. **00968603 extraction queue** — open since 08-27, unbuilt. Blocking defect: its header reserves DD-023, now occupied (log runs past DD-026). Needs ADDENDUM renumbering to next free DD + standard preamble before dispatch. Zero spend. Needed before bulk (worklists must be ledger-derived).

Superseded-state tasks in the graph (7, from pre-08-27 sessions) are noise; ignore.

## Standing rules re-affirmed this session

- Dispatches live in cc_task files/addenda on disk, never chat-only (relapsed, corrected mid-session).
- CC terminal reports are NOT pasted to Desktop; Desktop reads RESULTs + graph. Paste only uncommitted alarms.
- Guard-test-measures-neighbour: SIX instances now. Root cause: hand-authored fixtures too clean / tests reading files instead of driving code. Mutation matrix catches it every time (backstop working; cost = one rework cycle). Accepted-risk posture; fixture rule: real corpus lines, tests drive the production entry point.
- Weekly cap was binding at session start; pilot spend settled well under ceilings (A3: 1.92M + 1.06M judge; annotation: ≤0.8M declared).

## Blocked / parked

- **Arm B**: blocked by closure until re-derivation. Ceiling declared, 0 committed.
- **Bulk extraction**: blocked on re-derivation verdict + extraction-queue build.
- **OKF serving-layer projection**: parking lot, gated on serving-layer milestone (v0.2 trust fields ← evidence_class/instrument-version/adjudication).
- **Karpathy-wiki-style compiled surface**: same parking-lot item — good output format, rejected ingestion method.
- **seldon repo**: documentation_artifact_type task dispatchable anytime (other repo).
- **webdesktop biblio cron**: live on the other machine, now unblocked by the API key fix.
