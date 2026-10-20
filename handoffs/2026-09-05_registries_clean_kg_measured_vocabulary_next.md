# Handoff — 2026-09-05: registries clean, KG measured, vocabulary task authored

**From:** Desktop session 2026-09-03 → 2026-09-05
**Project:** ai-readiness-kg (plus seldon side-effects)
**Next session starts with:** `seldon go --brief` on this project, then the dispatch in §6.

---

## 1. Where the plan stands (plain)

Goal: an assessment framework for whether federal statistical data products are usable by AI, validated against literature held in this KG, then live probes against real agency sites and a write-up.

Critical path, fixed by a pre-registered rule: **vocabulary + entity linking → CQ v2 rerun → probe design → live probes.** Nothing else in the graph blocks.

## 2. State of the KG (all figures are registered Results, suffix `_2026-09-05`)

- 233 documents acquired; **167 extracted** (71 v1 + 68 August + 17 g1eval on 09-04 + 11 AI-ready-data strand on 09-05). Every non-contributing document cites a reason: 41 `no consumer` (DD-024 deferral), 22 `eval_fixture` (rule, DD-043), 1 duplicate, 1 unremediable, 1 conversion gap.
- 11,432 Concepts, 6,776 Claims, 1,895 Definitions; all carry grounding spans and provenance. **1,486 exact-name duplicate groups (41.3% of Concepts).** No cross-document identity was ever built (DD-020 deferred it).
- CQ harness (26 pre-registered questions, `cq_set_v1.yaml` frozen at `369d717`): evidence questions all pass; enumeration questions fail on duplication. `flip` = 0.308 two runs running; extraction of 795 Concepts moved it by zero. **Rule §1.5: entity resolution is P0 and blocks probe design.**
- CQ-02 answered: the corpus now holds two definitions of "AI-ready data" in the framework's sense (World Bank 2025, UK DSIT 2026), contrastable with the training-data sense. "AI-ready" is a homonym: 17% of uses in the unextracted set are ours; 41% training data; 22% adoption. Nearest binding definition is statutory: Evidence Act §3502 / M-25-05 "machine-readable" — *processed without human intervention while ensuring no semantic meaning is lost*. Framework definition = that standard applied to an AI consumer; G1 tests the semantic-loss clause, the discovery stack tests the no-human-intervention clause.
- Issue `cfe9eaf7`: "G1 is the sharpest gap" is unsupported as stated (Comunikos, GRADE measure uncertainty); survives re-scoped to *no AI-readiness instrument measures uncertainty legibility*, testable as CQ-27. Memo/deck untouched until CQ-27 answers.

## 3. What this stretch fixed (each with a test)

Result registry `name` migration (3,592 named, resolver shim over seldon's library); biblio cron commits its own writes; loader: unlabelled-twin defect and reset-never-cleared-phantoms (1,201 ghost nodes gone); `dispatch_waves` (a session-limit event no longer bills work it cannot use: 0 wasted vs 15M before); DD-042 (ceilings from measured rates; held out-of-sample at 93% of ceiling); DD-040/041 (no graph figure quoted without a named Result; reruns get dated suffixes); fixture epochs excluded by rule. Seldon: registry contract, terminal task states, ontology parser regression, per-process test DBs, git guard on registrar, grammar amendment, epoch compare-then-bump.

## 4. Lessons learned (for `docs/design_decisions.md`; CC appends with the next task)

1. **Open extraction without a seed vocabulary defers the cheapest step to the most expensive moment.** FSS seeded its 663 concepts first and linked as it read; this project keyed per document and never linked. Seed at ~80% from the subject area before the first extraction (pay-as-you-go: Franklin/Halevy/Maier 2005; Madhavan et al. 2007) and evolve it with the epoch/alias/deprecation machinery Seldon already has (AD-017).
2. **Go to the roots before the fancy middle.** Controlled vocabularies (Cutter 1876; ISO 25964; SKOS) and probabilistic record linkage (Fellegi & Sunter 1969) were right and underpowered on human judgment; the LLM removes that bottleneck. Formal-ontology committee work was a detour around it.
3. **A dry run that does not execute every validation the live path executes is not a dry run.** (migrate-names incident; fixed structurally.)
4. **An estimate that drives a decision is measured, not read off a floor.** (13.3M priced vs 31M spent; DD-042.)
5. **Diagnostics in chat are a defect.** Four chat queries were 19/20 right; the 20th (0 vs 72 unextracted) governed everything.
6. **Every task RESULT this week corrected at least one premise in its task file.** Handoffs and memory are lossy; query the graph before asserting.
7. **No new sibling files for a task while it is running**; CC globs addenda once at start.
8. **Dispatch lines go last in a message, alone.**

## 5. Open, not blocking

seldon: `3c42e9cd` closeout was in flight at last check (recoverability `42be368d`, small defects `0977c79a`, sync-all `c9fdef46`, placeholder regex `3376805b` — landed as `fa7d113`, `1581c3ec` correctly `blocked` on four unnamed-Result projects, `f6b32bbe` resolver options); `9a627af8` guard enforcement; four projects need `migrate-names` (icsp_notebook 346, TickBiteRisk 61, brock-projects 2, sas2graph 2). ai-readiness-kg: `609cb10b` admission emits no decision event; CQ-13/21 harness defect (fixed inside the vocabulary task as v2); four escalated G1 calibration disagreement records and the deck draft remain operator items; methodology document is a Desktop deliverable and should carry the definition in §2 and the lessons in §4.

## 6. Next dispatch (authored, registered `27b360f4`)

`cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` — SKOS-style seed vocabulary (framework constructs, discovery stack, SEO→AIO lineage, the 1,486 exact-name groups), Fellegi–Sunter deterministic layer at zero spend, Opus clerical band with a Fable-rated calibration gate (κ ≥ 0.60 or nothing is written), write-time resolution in the loader, residue → epoch-2 proposals, CQ v2 with a canonical view, pre-registered acceptance `flip` < 0.10. Ceiling from a measured 50-pair batch, stop above 25M.

In `/Users/brock/GitHub/ai-readiness-kg`:

> Commit the task file first, then read CLAUDE.md and execute cc_tasks/2026-09-05_vocabulary_and_entity_linking.md and only that task. Glob and read all sibling 2026-09-05_vocabulary_and_entity_linking_ADDENDUM*.md files before starting; an addendum can amend or SUPERSEDE the base task.

After its RESULT: OODA on the acceptance verdict; if it passes, author probe design (prior-art pass first: F-UJI, FAIR-Checker, DCAT validators, Lighthouse-style audit structure), then live probes.
