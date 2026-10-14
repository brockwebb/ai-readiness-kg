# DN-014: Brief for the executive summary

**Date:** 2026-10-12
**Status:** accepted by the operator as the writer's input (2026-10-11 to 2026-10-12, Desktop thread); wording of the summary itself is the writer's, against this brief.
**Supersedes as writer input:** the purpose statements in DN-013-R5/R6 where they conflict (page budget, shape).
**Working copy history:** `/Users/brock/GitHub/workbench/2026-10-12_concise_report_brief/BRIEF.md` (drafts of 2026-10-12).

## 1. Definition: the first thing the summary says

**SI readiness** is how well an SI system, working on its own, can find an agency's data, understand it, and use it correctly.

Then, as plain sentences: SI readiness has many parts, so we measure each one separately, and each can be at a different level. The field moves fast; this work focuses on the fundamentals that limit SI systems' use of federal data today. The fuller definition (how the data was made, its source, date and terms of use) goes in the appendix.

*Basis, one footnote:* Department of Commerce's definition of data ready for SI (machine-readable and machine-understandable, with contextual metadata in standard formats), extended from the data file to the website that serves it; "discoverable" and "access methods" from NOAA NAO 216-128 and the World Bank; "provenance and vintage" from the UN Statistical Commission; the four facets from USAFacts (accessible, understandable, accurate, open). Published titles cited exactly as published. The definition enters the project vocabulary (`ontology/vocabulary_proposals_epoch2.yaml`) with these sources.

## 2. What we built, in one sentence

Not a scanning tool: a decision support system that measures a website's real state, maps every gap to a readiness framework, and gives cited, prescriptive guidance on what to fix first for the best return, explained at whatever level of technical depth the person asking needs.

## 3. Page 1 must say, plainly

1. **The problem.** SI readiness is complex and moving fast. It spans data publishing, web practice, metadata standards, policy and SI behavior; no one person holds all of it. People increasingly get statistics through SI systems; if those systems cannot find or understand official data, people get stale or second-hand numbers. We use SI to solve this: SI helped build the machinery, and SI is how people use it.
2. **What it is.** A decision support system with three parts:
   - **Measure** what a machine actually experiences on an agency's website, not what the agency says about itself. The scan is the entry point, not the product.
   - **Map** each result to the readiness framework (USAFacts' four criteria as the backbone, plus three added areas) on one standard scale, so agencies can be compared.
   - **Prescribe** actions ranked by effort and impact: low-effort, high-impact first; plan the strategic ones; skip high-effort, low-return ones and problems that are temporary.
3. **Anyone can ask it.** An executive, an implementer anywhere in the data lifecycle, a site administrator or a data producer can ask questions and get explanations grounded in the science, at their own level of detail, and see where their piece fits in the whole. No one needs to be an expert in every field involved.
4. **Why the advice can be trusted.** It is grounded in a knowledge graph of the research, standards and policy, which an SI system queries to give cited answers: not made-up advice. When evidence is superseded, the graph keeps it as history but stops it from shaping advice, so it can also explain why an idea was tried and dropped.
5. **Measured in three tiers, by who can run them.**
   - **Tier 1, public:** checks anyone can run with free, open tools. These matter most: they are what any SI system or member of the public experiences, not only large commercial crawlers.
   - **Tier 2, agency cooperation:** checks that need the agency to run something or turn something on, often free tools or configuration, that unlock more of the system's value.
   - **Tier 3, paid tools.**
   Each tier connects to the framework, so an agency can see the highest score reachable with public checks alone, and what configuration or paid tools would add.
6. **What it found.** The few results that matter, each with one example, and the free actions that would move them.
7. **One caution.** A standard score can be gamed (Goodhart's law). Designing around what the public can actually reach is the guard: readiness is judged where real users meet the data, increasingly through SI systems. The system evolves with the science.

## 4. The 30-second version

- SI readiness is complex, fast-moving, and beyond any one expert; we use SI to solve it.
- We built a decision support system: it measures a website's real state, maps it to a standard framework, and tells you what to fix first for the best return.
- Anyone, from an executive to a site administrator, can ask it questions and get cited explanations at their own level.
- We ran the public tier on all 16 federal statistical agencies. [Headline result held until checked.]

## 5. Shape

Two pages. Page 1 carries everything above. Page 2: one summary table, at most one figure. Detail in attachments, later including an interactive dashboard of the data and the framework (its own design session). No section on how it was written; a short SI-use disclosure is added in a later pass.

## 6. Cut

Commerce's definition beyond the footnote. Process words (cycle, claim, leg, composite, harness, verdict, gate, pipeline). Any point made twice. Hedges. Indicator codes. Counts in page-1 sentences except the 16 agencies (counts go in the page-2 table).

## 7. Held until checked

- **The discoverability headline** ("15 of 29"): part of `RULE-A13-v1` has no cited source; stated only in the form that survives a check against published definitions.
- **Every capability in §3** (including the three tiers and the cost, effort and impact data) must point to something that exists: a design note, a tool, a file. A capability not yet built is stated as planned, or cut.

## 8. Context for later, not for page 1

Content delivery networks and bot defences that block by default will increasingly turn away legitimate SI users; the networks are evolving toward handling machine traffic. Material for the long report or the dashboard, not the summary.

## 9. Authoring

Opus 4.8 writes; Fable 5.1 reads as the reviewer in a fresh context. The operator's standing rule: he can name any model for a role; defaults are the most recent models unless there is a reason otherwise. Opus 4.8 is chosen for authoring on the operator's experience writing the two books with it.

## Prior art

Added at commit time by seldon MODEL-003 (task `019844b9`, 2026-10-14), so the note passes the AD-036 gate. It records
what this brief builds on. It changes nothing above.

### External

The library holds no writing-guidance literature for executive summaries; the rows returned are off-topic (UI traces,
ontology construction). This is a failed search, recorded as one:

- library receipt: query "executive summary for policy readers bottom line up front plain language" | release library_graph_20261012_sq013_01_2026-10-12.json sha256:0989759c402ca41472806bdf9ab47529ba2eb5a6b25d0e75c1a6e29e650d4275 | rows lesson:2026-02-22_arXiv_2508_02621#p31:681:1660-1683, lesson:2026-02-22_arXiv_2508_02621#p37:795:49-172, lesson:2026-02-22_arXiv_2010_03768#p10:224:3386-3563, lesson:2026-02-22_arXiv_2404_16130#p22:314:1499-1530, lesson:2026-05-09_arXiv_2605_06161#p7:137:407-755, lesson:2026-05-09_arXiv_2605_06161#p4:74:385-474, lesson:2026-02-22_arXiv_2502_02533#p28:541:78-214, lesson:2026-02-22_arXiv_2502_02533#p28:555:1048-1142, lesson:2026-02-22_arXiv_2502_02533#p26:504:1921-2329, lesson:2026-04-12_arXiv_2403_05530#p117:1661:1155-1327, lesson:2026-04-12_arXiv_2403_05530#p122:1711:1043-1091, lesson:2026-04-12_arXiv_2403_05530#p56:879:2646-2880, lesson:2026-02-22_arXiv_2502_05453#p15:262:2217-2752, lesson:2026-02-22_arXiv_2601_01885#p13:434:2774-2829, lesson:2026-04-07_arXiv_2510_13143#p4:65:4223-4355, lesson:2026-06-16_arXiv_2603_15118#p21:292:846-1287, lesson:2026-06-16_arXiv_2603_15118#p3:33:4974-5073, lesson:2026-07-04_arXiv_2606_10209#p13:235:1745-2229, lesson:2026-07-04_arXiv_2606_10209#p5:80:3582-4400, lesson:2026-07-04_arXiv_2606_10209#p4:47:3000-3583, lesson:2026-02-22_arXiv_2503_20020#p6:92:1691-1952, lesson:2026-02-22_arXiv_2503_20020#p49:744:581-665, lesson:2026-02-22_arXiv_2503_20020#p49:752:1028-1228, lesson:2026-02-11_10_17016_feds_2025_044#p1:5:293-1103, lesson:2026-02-11_10_17016_feds_2025_044#p43:436:126-515, lesson:2026-02-11_10_17016_feds_2025_044#p44:442:285-738, lesson:2026-02-22_arXiv_2409_18313#p2:48:253-338, lesson:2026-02-22_arXiv_2409_18313#p4:94:96-156, lesson:2026-02-22_arXiv_2409_18313#p3:82:4083-4163, lesson:2026-02-22_arXiv_2503_18968#p10:212:2786-2906, lesson:2026-05-23_arXiv_2510_20345#p4:39:3582-3916, lesson:2026-05-23_arXiv_2510_20345#p3:27:1604-2085, lesson:2026-02-22_arXiv_2502_14282#p14:290:550-667, lesson:2026-02-22_arXiv_2502_14282#p4:106:179-205, lesson:2026-02-22_arXiv_2503_11664#p15:494:2170-2368, lesson:2026-02-22_arXiv_2503_11664#p15:472:0-278, lesson:2026-03-17_arXiv_2207_01206#p9:185:395-459, lesson:2026-04-13_arXiv_2510_00615#p26:637:1717-2132, lesson:2026-04-13_arXiv_2510_00615#p27:662:1438-1676, lesson:2026-04-13_arXiv_2510_00615#p28:682:1247-1485

### Internal

The brief supersedes DN-013-R5/R6 as writer input where they conflict, and follows DN-009 (the deck was rejected; the
evidence map comes first):

- internal receipt: query "DN-009" | repo ai-readiness-kg@a95ae2e1cf5c5bf2c30090a0f80740a093a3d4ed | hits docs/design_decisions.md:1292, docs/design/2026-10-02_DN-009_deck_rejected_evidence_map_first.md:1, docs/design/2026-10-06_DN-012_audit_closure_absence_verdicts_and_scoring.md:5, docs/design/2026-10-06_DN-012_audit_closure_absence_verdicts_and_scoring.md:27
- internal receipt: query "DN-013-R5" | repo ai-readiness-kg@a95ae2e1cf5c5bf2c30090a0f80740a093a3d4ed | hits docs/design/2026-10-06_DN-013_parallelism_known_endpoints_and_prose.md:29
