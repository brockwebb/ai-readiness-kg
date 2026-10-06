# Full-project audit: holes, weaknesses, and what it takes to operationalize

**Task:** `cc_tasks/2026-10-04_full_audit.md` (ResearchTask `2d9d2309`). **Run:** 2026-10-06 UTC, a Claude Code session under `claude-opus-5-5`, not the `claude-fable-5-1` the task asks for (see RESULT, premise wrong 1). **Scope:** this repository's own evidence, methods and code. It compares against nothing outside the repository and names no other group's work. It builds nothing and fixes nothing.

## 1. Protocol (written before the inventory was read)

### 1.1 Method sources, and whether each was retrieved or recalled

| source | what it supplies here | locator | status |
|---|---|---|---|
| Adversarial-review rubric v1.3.0 | the grounding rule (every finding cites a verbatim span or is marked speculative; absence claims are always speculative); anti-anchoring (a RESULT's own claim is evidence about the pipeline, never about the truth); overstatement as a defect; "not rewarded for volume" | `~/.claude/skills/adversarial-review/rubric/baseline.md`, sha256 `4e6f51c2…f77`, header "**Version:** v1.3.0", "ACTIVE since 2026-08-13" | retrieved |
| the same rubric's `code` overlay | nothing: it is marked "STUB … MUST NOT be used to produce recorded verdicts" | `overlays/code.md` | retrieved; **not used to emit verdicts** (§1.4) |
| `seldon audit` | the starting inventory | none: `seldon` 0.1.0 has no `audit` command ("No such command 'audit'"); the nearest, `com.arnold.seldon-audit`, runs `arnold/scripts/seldon/close_landed_tasks.py --audit`, bound to arnold's own `seldon.yaml` | **substituted** by `seldon status`, `seldon verify` and `seldon dispatch status` on this repo (§2.1) |
| Wohlin, Runeson, Höst, Ohlsson, Regnell, Wesslén, *Experimentation in Software Engineering*, Springer 2012 | the four validity classes: construct, internal, external, conclusion | DOI 10.1007/978-3-642-29044-2 (Semantic Scholar CorpusId 9558494) | **metadata retrieved, class definitions recalled**: the book's text sits behind Springer's login (303 to `idp.springer.com`). The four class names are confirmed by secondary search results; the working definitions below are the standard ones, recalled |
| ACM Artifact Review and Badging, Version 1.1, 2020-08-24 | the badge criteria: Available, Functional, Reusable, Results Reproduced | `https://www.acm.org/publications/policies/artifact-review-and-badging-current` returned HTTP 403; the definitions were retrieved verbatim as reproduced, with that attribution and version, at `https://sigir.org/general-information/acm-sigir-artifact-badging/` | **retrieved, via a page that reproduces them** |
| State Fidelity Validity (SFV), the project author's paper in progress | does the stored state match what the pipeline claims it did; threat codes T1 to T5 | `~/GitHub/brock_projects/sfv-paper/paper/glossary.md` (definition), `sections/04_sfv_framework.md` (T1 to T5 table), at `ac28c39` (2026-09-01) | retrieved |

### 1.2 Tags every finding carries

**Validity class (Wohlin, recalled definitions):**
- **construct:** the measure does not measure what the claim says it measures (a count that counts the wrong thing, an indicator whose rule tests something else);
- **internal:** the pipeline's own stages could have produced the result by a route other than the one claimed (a fused node, a stale projection, an unrun step);
- **external:** the result does not carry beyond the cases it was measured on (one cycle, one leg, 16 agencies, this machine);
- **conclusion:** the inference drawn exceeds what the data licenses (a rank from one leg, a rate from n too small to separate, a negative with no positive control).

**ACM badge criterion (retrieved, v1.1):** *Available* ("permanently available for retrieval"); *Functional* ("documented, consistent, complete, exercisable, and include appropriate evidence of verification and validation"); *Reusable* ("very carefully documented and well-structured to the extent that reuse and repurposing are facilitated"); *Reproduced* ("obtained in a subsequent study by a person or team other than the authors, using, in part, artifacts provided by the author").

**SFV threat (retrieved):** T1 semantic drift; T2 false state injection (an asserted step or result that never happened); T3 compression distortion; T4 supersession failure (a superseded value persists in use); T5 state discontinuity. A finding takes an SFV code when the stored state and the claim about it disagree.

A finding carries one primary tag, and secondaries where they apply.

### 1.3 Severity, a declared 3-point scale

| code | meaning | test |
|---|---|---|
| **S1** | blocks showing | a skeptical reader of the shown material would find it and be right, and the material would be withdrawn or corrected publicly |
| **S2** | must fix before a second cycle | the first cycle's statements survive, but a second cycle built on the same machinery would inherit the defect or could not be compared to the first |
| **S3** | note | real, located, and does not change any shown statement or the next cycle |

**Priority class: "vibe".** A thing that looks built and has no test, no control, no locator or no event. These are ranked first within their severity.

### 1.4 Rules on the auditor

1. **No finding without a locator.** That means a file and line, a node id, or an event id. A finding's evidence is a verbatim span where the claim is about text. An absence claim says so and is marked *absence*, as the rubric's §3 marks it speculative.
2. **Anti-anchoring (rubric §2).** A RESULT's statement is a claim to check, not a premise. A finding that rests only on a RESULT's self-report says so.
3. **Not rewarded for volume (rubric §1).** No style opinions. No finding manufactured to fill a class.
4. **The rubric's verdict records are not emitted.** The surface here is code and documents, and the rubric's `code` overlay is an uncalibrated stub that forbids recorded verdicts. Findings use this audit's own table (§5), not `schema/verdict.json`.
5. **The known list is verified, not re-found (task decision 3).** A confirmation is recorded as open, closed or changed, and is not counted as a finding.
6. **Blind controls (task decision 6).** Three defects are planted by `scripts/plant_audit_controls.py` into a scratch copy of the tracked tree before the inventory is read. Their locations are drawn at random and written to a sealed manifest outside the copy. The readers (subagents) audit the copy and are not told that plants exist. The session that wrote the script knows the three *kinds*, from the task file, but not where they were placed until the manifest is opened after the findings are frozen. The plants are never committed.
7. **Reader gate (DN-009 d7).** A fresh subagent sees only the ranked findings table.

## 2. Inventory

### 2.1 Starting inventory (the `seldon audit` substitute)

| command | result | log |
|---|---|---|
| `seldon status` | 37,170 events; 8,410 nodes, 18,578 relationships; 38 open ResearchTasks (1 accepted, 37 proposed); "No stale artifacts." | `logs/2026-10-06_full_audit_seldon_status.log` |
| `seldon dispatch status` | enabled, tree clean, 38 open, 0 candidates: 37 `NOT A CANDIDATE (no_source_file)`, this task `NOT A CANDIDATE (framework_layer_names_no_layer)` | `logs/2026-10-06_full_audit_dispatch_status.log` |
| `seldon verify` (before any read) | "All checks passed.", EXIT=0 | `logs/2026-10-06_full_audit_verify_pre.log` |

### 2.2 How the inventory was read

The tracked tree at `a5b5134f` was copied by `git archive` into a scratch directory, the three controls were planted in it (§6), and six fresh readers each audited one slice of the copy under one brief (the rubric's grounding and anti-anchoring rules, the §1.2 tags, the §1.3 scale), with the live graph read-only. The session then merged, re-graded against §1.3 and re-checked the S1 findings itself (§4.3). The readers' own read records are Appendix A.

| slice | task decision 2 inventory it covered |
|---|---|
| A | the 15 RESULTs dated 2026-10-02 to 2026-10-04 and their task files, with their "premises wrong" sections; `docs/design/` from DN-005 (DN-005 to DN-011 and addenda, `scoring_model.md`); `docs/design_decisions.md` |
| B | `docs/evidence/claims.yaml`, `definition_pairs.md`, `kg_questions.yaml`/`.md`; `docs/catalog/`; `docs/figures/`; their generators |
| C | `framework/ai_readiness_framework.json`; `assessment/harness/scan/rules/`, `targets.yaml`, `params.yaml`, `manners.py`; `scripts/score.py` (the task's `score.py`; there is none under `assessment/`); `docs/design/scoring_model.md`; the cycle-of-record matrices |
| D | `kg/schema.yaml`, `docs/schema_v0.1.md`, `scripts/build_projection.py`, `kg/eventlog.py`, `kg/extraction/grounding.py`, `parser.py`, `pipeline.py`; `docs/research/2026-10-04_node_key_fusion_audit.md` |
| E | `tests/` (124 files, 1,876 test functions), statically by `ast`; `conftest.py`; the `Makefile` gate targets |
| F | operationalization, from `docs/adopt/run_on_your_site.md`; the modular-roster record `712755f8`; the dispatcher defects |
| R2 | the clean re-run of two controls (§6): `claims.yaml` locators and figure captions only |

**Not read, across slices** (each reader's own list is in Appendix A):
- `logs/` (gitignored, so absent from a clone and from the copy): no RESULT's suite, verify or protected-path count could be re-read (finding A-18).
- `events/raw/` model responses; the PNG figures and the `.pptx` deck files.
- Ten current rule modules were judged from their cycle-of-record reason strings, not line by line (slice C).
- `publish.py` beyond line 120 and `rederive.py` beyond line 80, except by grep (slice C).
- The test suite was not run by any reader. The session ran `make gate-fast` (§9 of the RESULT).

## 3. The known list, verified (task decision 3; confirmations, not findings)

| item | status | evidence | locator |
|---|---|---|---|
| K1: CL-054, 16 indicators with no EVIDENCED_BY edge | **open** | Still 16 in the claim, in the record and in the live graph (projection_gate green), the same set: A2, A7, B5, B6, C2, C3, D1, D2, E3, E5, E6, E7, F3, F5, G2, G3. E5 has EVIDENCED_BY_INTERNAL only. Two of them, A2 and D1, are marked measurement_status measured. Record has 149 EVIDENCED_BY edges (graph 149), 2 from candidate A12, which is why record counts.evidenced_by = 147. CL-054's evidence lists only the 9 located indicators; neither the 16 nor the 84 cited documents are enumerated as evidence entries. kg_questions Q5 items_with_no_document = 16, which agrees. | docs/evidence/claims.yaml:2352 (CL-054); framework/ai_readiness_framework.json EVIDENCED_BY edges |
| K2: 26 Definitions with no asserting event (NOAA among them) | **changed** | Still 26, but the statement is wrong as worded: 26 of 2,550 Definitions (was 26 of 1,975) lack an incoming DEFINES edge; all 26 have an asserting node_asserted event on the log (replay Definition count 2,550 = graph). 25 carry prov_extraction_event_id (opus-4-8/0.2.0 or opus-5/0.3.8: aggarwal d_keyword_stuffing; ai-watch d-famt, d-hamt, d-trl2, d-trl4..d-trl8; arm d-differential-privacy, d-federated-learning, d-fine-tuning, d-security-by-design, d-smpc; beyond-model d_iar; cao d_dens, d_num, d_words; croissant d-fileobject; data-readiness-360 d_class_separability, d_readability, d_term_importance, def-class-separability, def-discrimination-in-data; statcan d_sample). Only NOAA nao216-ai-ready-data lacks an extraction event id: it was curated by scripts/assert_noaa_definition.py into batch-043 (event 6f0c77bed2ad489ca808830420c3a27b) and the projection does not stamp that event id nor write a DEFINES edge. kg_questions.md still says 1 Q1 row incomplete for this reason. | Neo4j: MATCH (d:Definition) WHERE NOT ()-[:DEFINES]->(d); events/batch-043.jsonl:1 (event 6f0c77bed2ad489ca808830420c3a27b); cc_tasks/2026-10-02_kg_research_questions_RESULT.md §2 Q1; docs/evidence/kg_questions.md:19-22 |
| K3: no construct layer, so comparative questions are partial or cannot_answer | **changed** | By grade: answered 1 (Q3), partial 4 (Q1, Q2, Q4, Q5), cannot_answer 0. Comparative questions: Q2 (share/differ by construct) partial, with 0 Construct nodes, 0 GROUNDS edges and 0 Definition-Concept edges; Q5 (item to construct to definition crosswalk) partial, with 0 construct-to-Definition edges; Q4 (what each instrument operationalises) partial, with 0 OPERATIONALIZES edges. Q3 (do definitions conflict) is now answered, from 5 cross_document_pass CONFLICTS_WITH edges written by run_definition_pairs (158 pairs judged, single rater, not adjudicated). So the construct-layer gap still holds for Q2, Q4 and Q5, but Q3 no longer fits the known statement. See B-05 on Q3's controls and B-12 on Q5's hardcoded grade. | docs/evidence/kg_questions.yaml (Q1 to Q5) |
| K4 | **closed** | A12 is the only node with status 'candidate' (ind:A12 plus con:A12-access-policy-coherence). Recomputing every counts key from nodes/edges reproduces all 18 stored values exactly: indicators 48 and constructs 47 exclude A12; evidenced_by 147 of 149 and evidenced_by_internal 17 of 20 exclude A12's 2 and 3 edges; actions 60 + actions_on_candidate_indicators 3 = 63 REMEDIATES; requires_on_candidate_indicators 0 (A12 has no REQUIRES edge); indicators_measured 16 excludes A12 (its measurement_status is 'specified'). score.py drops A12 via rules.CANDIDATE_LEGS (structure reason 'candidate rule (DD-054)'); legs_on_cycle total 23 = 24 harness legs minus A12. A12 IS counted, by the stated basis, in rules_built 24 (RULE-A12-v3 is in rules.CURRENT) and in the report's 'five host-level checks' (the report labels it a candidate, L0 report :76-78). One surface counts it against the record: docs/deck/brief_narrative.md:4 '49 indicators written as tests' (49 = 48 + A12) where every figure says 48. Nothing found that holds A12 out where the counts say it is in. | framework/ai_readiness_framework.json:5-24 (counts), :8668 (counts_basis); scripts/score.py:176-178; docs/deck/brief_narrative.md:4 |
| K5 | **closed** | The three unranked bodies are BLS, BTS and ORES (SSA). Every product cell is error ('every fetch failed: refused') and tier-A A4/A5/A10/A11-declared are error; refused_identified_client 33 of 35, 32 of 33 and 32 of 33 probes on the host surface; their robots.txt itself answered 403 on every read 2026-09-06..09-10. score.py prints them '- 0 (unobservable at 1)' with 0/21 legs. The polite-client boundary is stated where a hostile reader of the report sees it: :42-45 ('One identified client, one request per second per host, `robots.txt` obeyed, no forms, no logins, no query-string fuzzing ... never retried a host under another identity'), :176-177 ('this instrument did not find those sites wanting, it was not allowed to look'), :310-312 ('no reader should infer that their absence from a numerator means anything about their products'), and the Manners paragraph :442-444. Caveat (new, filed as C-02 and C-11): the same section says the client 'obeys the `robots.txt` those same hosts publish' although none of the three ever served one to it, and the manners paragraph omits the always-fetch carve-out and the unhonoured Crawl-delay. | docs/reports/scan_matrix_tierA_2026-09-10_rj4.json (rows BLS, BTS, ORES); docs/reports/2026-09_fss_ai_readiness_L0.md:42-45, :170-177, :310-312, :442-444 |
| K6 | **open** | Still open, 3 files: (1) node_key_fusion_audit.md:66 'The two external sources are cited as recalled, not retrieved' (RDF 1.1 Concepts §3.4 / Semantics §5.2 and GraphRAG, Edge et al. 2024, arXiv 2404.16130); (2) scoring_model.md:7 says the OECD/JRC Handbook, the Open Data Barometer, ODIN, WCAG and OpenSSF Scorecard are each 'cited by reference', and :120 says the same of Berners-Lee's five-star scheme (2010) and WCAG conformance levels (the Handbook has since been fetched for CL-083 but scoring_model.md, a generated page, still says 'by reference'); (3) DN-005 ADDENDUM_03:17 says Kahneman & Tversky 1979, Flyvbjerg 2006 and Cohn 2005 are 'named by reference', not on disk; DN-007:10 repeats the first two. Closed since the RESULTs: definition_pairs.md:51 and commerce_guidance_two_pipelines.md:55 now say retrieved, with entries in docs/evidence/method_sources.bib. docs/evidence/claims.yaml:3358 only reports that scoring_model.md says 'cited by reference'. No hits in README.md or reports/ (the reports/dcat_us_3_faq/run/raw model outputs were excluded). | docs/research/2026-10-04_node_key_fusion_audit.md:66; docs/design/scoring_model.md:7 and :120; docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_03.md:17 |
| K7: node-key fusion and its effect on cited counts | **open** | Still fusing: the node write is unchanged last-wins on (label, <doc>::<id>), no fix task exists in cc_tasks (only the audit and its RESULT), and no test asserts within-document non-fusion (only the cross-document test_mutation_same_item_id_across_docs_no_longer_fuses). Effect not carried: kg_questions.md was regenerated at epoch 281 docs / 2,550 Definitions after the audit and still states 'Q1 19 definitions from 11 documents' and 'Q4 29 Instrument nodes' with no fusion caveat (grep -i fus/overwrit returns nothing in kg_questions.md/.yaml or definition_pairs.md), though the audit, recomputed at HEAD, still gives Q1 20 and Q4 31 under either fix. Numbers at HEAD (audit's own code, rendered to scratch): 2,780 fused (label,key) groups of 29,322 (audit said 2,396 of 26,035), 2,638 lossy, 5,269 distinct spans lost (was 4,511), 3,146 collisions (was 2,703); Definition 208 fused / 173 collisions / 281 spans lost; Definitions 2,550 -> 2,826 under chunk-qualified keys; Instruments 506 -> 673; Commerce glossary 48 (38 under first-wins). The audit's control that replay counts equal Neo4j still holds at HEAD for all ten labels and Document (281). The growth and the stale --check are filed as D-02. | scripts/build_projection.py:811 (MERGE (n:{label} {key}) SET n += $props); docs/research/2026-10-04_node_key_fusion_audit.md; docs/evidence/kg_questions.md:19,115 |
| K8 | **open** | 13 of 16 bodies ranked. Concentration: all 13 ranks move when one leg's verdicts are reversed: DRSMSU 1->4 (G4, 1 pass of 1), EIA 2->4 (A10, 1 of 1), CENSUS 5->9 and NCES 5->9 (A10, 1 of 1); BEA 3->1, NCSES 3->1, SAMHSACBHS 7->1, NASS 8->2, SOI 8->2, BJS 10->2, ERS 10->2, NAHMSAPHIS 10->2, NCHS 13->2 (F4, 0 pass). Mean /rank shift/: prior cycle scan_2026-09-09 2.417 (8 of 12 moved, legs measured differ for all 13 bodies, e.g. DRSMSU 4/21 vs 21/21), flat 0.308 (4 of 13), drop A 3.385 (12 of 13), drop B 0.308 (2 of 13), drop D 0.000, drop F 0.000, drop G 1.000 (10 of 13). F4 and G4 each weigh 1/5 of a hierarchical score. Scores are compressed: 12 of 13 lie in 0.040-0.133. The docs state the fragility (H_limits.md, brief_narrative.md:59-62, G_census_dogfood.md:12); no doc found stating a rank more firmly than the sensitivity. New beyond the known item (C-05): DRSMSU's D4 and G4 passes cite one Observation, so the leg-level probe understates its fragility (both reversed: rank 9). | scripts/score.py --sensitivity (cycle scan_2026-09-10_rj4); docs/brief/H_limits.md:69-86 |
| K9 | **closed** | No hit puts value, impact or ROI into the score or a rank. The ROI/return/impact/benefit/value/worth hits are: the DN-009/DN-010 prohibitions themselves; docs/catalog value_rating columns, each carrying the DN-010 label 'enters no score, rank or bound'; the rubric in docs/catalog/README.md:72-86; and data words ('value' in a field sense, 'return a 404'). tests/test_scan_catalog.py::test_no_score_rank_or_bound_module_reads_a_value_column walks the import closure of score.py, prescriptions.py and build_evidence_map.py and forbids value_rating/value_basis/docs/catalog. value_rating has 0 occurrences in framework/ai_readiness_framework.json and kg/schema.yaml. One residue, which is not score-entering: DN-005 §2.3 (line 37, 'here is the value'; line 39, 'effort/cost/benefit fields') still describes value as part of the prescription layer. The bound that orders the prescription join (scoring_model.md §9) is the equal-weight score change, which DN-009 d3 allows. | docs/design/2026-10-02_DN-010_value_effort_matrix_decision_support.md:13,18; docs/catalog/README.md:3; tests/test_scan_catalog.py:344-392 |
| K10 | **open** | Lines still carrying the stale numbers: brief_narrative.md:4 ('24 of them with a current rule' and 'a corpus of 264 admitted documents'), :12 ('The corpus is 264 documents'; the same line still carries 'the OECD/JRC Handbook's' scoring default, per the v2 RESULT), :28 ('24 indicators have a current rule'), :34 ('264 documents admitted'), :38 ('federal (94 admitted)'); brief_deck_content.md:75 (quotes 'Of 49 indicator nodes, 24 have a current rule'). Correct and left alone: brief_deck_content.md:498 (24 current rules) and brief_narrative.md:66 (24 specified only). The .pptx files were not inspected. Nothing outside docs/deck builds from or links to the deck except its own generator scripts/build_brief_deck.py, scripts/build_framework_deck.py, the protected-path scripts, and tests/test_brief_deck.py, which is retired whole (line 46: pytestmark xfail(run=False, strict=True, reason='DN-009: deck rejected ... pinned at the 264-document corpus until removed')). No docs/ page or site file links to brief_deck.pptx. Removal is still pending under DN-009 §1 ('retained until the report exists'). | docs/deck/brief_narrative.md:4,12,28,34,38; docs/deck/brief_deck_content.md:75 |
| K11 (fa40072e): dispatcher header-parse defect and declared_tokens defect | **open** | Both defects are still in the code; dispatch.py was last changed by commit 33f70c6 (2026-09-20), before the task was filed on 2026-10-02. Called the installed functions directly: spend_tokens('est. 4 to 7M tokens') = 4, spend_tokens('est. 2 to 4M tokens') = 2, spend_tokens('7M tokens') = 7000000, so the c4 band check is vacuous for any 'A to BM' header. parse_headers on a file whose Supersedes line quotes **Network:** inline before the real header returned Network = 'inline under cadence nightly and so on.' and parse_network classed it 'cadence' with no error, so the real **Network:** none line was never read. The header regex has no line-start anchor and search() takes the first match. Part (3) of the task (registration does not run parse_network) also holds: grep for parse_network/candidacy/spend_tokens in seldon/commands/cc.py and mcp_server.py found nothing. Side note: the brief calls 1267b87d the 'header-parse defect', but fa40072e carries both the header-parse and the declared_tokens defects; 1267b87d is a different defect (see next row). | /Users/brock/GitHub/seldon/seldon/core/dispatch.py:75-81 (_header_re), :338-344 (_header_value), :91 (_TOKENS_RE), :357-372 (spend_tokens); ResearchTask fa40072e-358c-42d2-88b9-a512032772f0 (seldon_events.jsonl line 37018, state proposed in graph) |
| K11 (1267b87d): seldon_cc_register does not commit the task file it registers | **changed** | The core claim no longer matches the code. Seldon commit d9ad7d3 (2026-09-18, 'registration commits the untracked task file it registers, path-scoped') makes register_task_file, which the MCP tool also calls (mcp_server.py:1100), run `git add -- <file>` and `git commit -- <file>` for an untracked file, and recent ai-readiness-kg history shows registrations committing their own file (e.g. 16de7e24 'register: cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01... committed by its registration'). What still holds: it commits exactly the one registered path, so a sibling *_ADDENDUM*.md that is not itself registered stays untracked and still dirties the tree for c7, and there is no refusal of a file modified relative to HEAD. The task's description (filed 2026-10-04) describes the pre-2026-09-18 behaviour, or a case where the commit failed and the file was unstaged again (cc.py:649-652). | /Users/brock/GitHub/seldon/seldon/commands/cc.py:621-654 (_commit_registered_file), :1077 (register_task_file), mcp_server.py:1100; ResearchTask 1267b87d-fb19-4289-b586-5e24a720f8d2 (seldon_events.jsonl line 37047, state proposed in graph) |
| K11 note: `seldon dispatch status` reports 37 of 38 open tasks as no_source_file, and cc_tasks/2026-10-04_full_audit.md as framework_layer_names_no_layer | **open** | Matches the graph: open ResearchTasks are 36 proposed + 1 accepted with source_file null and 1 proposed with a source_file (38 total, 37 with no file). no_source_file is the code's answer for any ResearchTask created without a file, such as Desktop-filed backlog items like 712755f8, fa40072e and 1267b87d, so the status listing is mostly backlog, not dispatch failures. The full audit's header value 'all layers; the audit is cross-cutting and says so.' does not match _LAYER_VALUE_RE (§2.1-2.5, Tier M/O/D, none), so the refusal is the grammar working as written, not a parse defect; but the task's line 8 says 'Launched by the dispatcher', and the audit copy's log has no dispatch_launched for 2d9d2309 (logged as finding F-21). I did not run `seldon dispatch status` myself (it may write events); the 37/38 figure comes from the brief and the graph count agrees with it. | /Users/brock/GitHub/seldon/seldon/core/dispatch.py:903-905 (no_source_file), :85 (_LAYER_VALUE_RE), :433-436; cc_tasks/2026-10-04_full_audit.md:7; ResearchTask 2d9d2309-28cd-4c68-80c2-f1408c181e39 |

## 4. Findings

**66 findings**, after the four plant detections were removed (§6) and nine duplicate findings from overlapping slices were merged into the finding they duplicate (column `also` of the CSV). By severity: **S1 7, S2 28, S3 31**. By primary validity class: construct 20, internal 29, external 4, conclusion 13. Vibe class: 12 (listed first within their severity).

| | construct | internal | external | conclusion |
|---|---|---|---|---|
| S1 | 5 | 1 | 0 | 1 |
| S2 | 5 | 12 | 3 | 8 |
| S3 | 10 | 16 | 1 | 4 |

### 4.1 Ranked table

Full rows, with the verbatim evidence span, the check each reader ran and what closes each, are in `docs/audit/2026-10-04_full_audit_findings.csv`.

| # | id | sev | vibe | tags | locator | finding | closes by |
|---|---|---|---|---|---|---|---|
| 1 | C-01 | S1 |  | construct/conclusion/internal; ACM functional; SFV T3 | `assessment/harness/scan/params.yaml:704` (fnd_e5011a474f72fcb754b8c3d9) | A1/A3 fails judge only the first 25 links of 48-244 | task |
| 2 | C-02 | S1 |  | conclusion/construct; SFV T2 | `docs/reports/2026-09_fss_ai_readiness_L0.md:187` (fnd ids of A12 for BLS/BTS/ORES in docs/reports/scan_matrix_tierA_2026-09-10_rj4.json) | Report says BLS/BTS/SSA publish permissive robots.txt; scanner never read one | wording |
| 3 | C-04 | S1 |  | construct/external | `assessment/harness/scan/rules/rule_d4_v3.py:86` (ind:D4) | D4 and four DCAT legs read only the scanned host's data.json | task |
| 4 | C-06 | S1 |  | construct/internal; SFV T4 | `assessment/harness/scan/rules/rule_a9.py:1` (ind:A9) | Frontier indicator A9 enters every body's score | task |
| 5 | C-07 | S1 |  | internal/conclusion; ACM reproduced; SFV T5 | `framework/ai_readiness_framework.json:18` (ind:G4) | Record says 16 measured; cycle of record scores 21 of 48 | task |
| 6 | C-13 | S1 |  | construct/conclusion | `assessment/harness/scan/targets.yaml:96` | Parent-department host files scored and ranked as the unit's | ruling |
| 7 | C-14 | S1 |  | construct/conclusion | `assessment/harness/scan/rules/rule_a2_v3.py:59` (fnd_b9e93605be55aeffa1b2633f) | Census ACS fails 'documented public API'; prescribed to build one | task |
| 8 | A-07 | S2 | vibe | internal | `docs/design_decisions.md:421` | DD-029 acceptance sampling not run on Commerce or DCAT extractions | task |
| 9 | A-10 | S2 | vibe | internal; SFV T2 | `docs/design_decisions.md:686` | DD-040 'every graph figure is a registered Result' is not enforced | task |
| 10 | D-01 | S2 | vibe | internal/construct; ACM reproduced; SFV T2 | `scripts/build_projection.py:557` (w3c-dcat-3::c1) | Edges written onto both label-twins: 301 spurious edges, 75 schema-illegal ASSERTS | task |
| 11 | D-02 | S2 | vibe | internal/conclusion; ACM reproduced; SFV T4 | `docs/research/2026-10-04_node_key_fusion_audit.md:26` | Fusion grew after the audit; the audit's own --check drifts at HEAD | task |
| 12 | D-03 | S2 | vibe | internal/construct; ACM functional; SFV T2 | `docs/design_decisions.md:225` | DD-024's faithfulness_epoch flag on legacy semantic edges does not exist | task |
| 13 | E-04 | S2 | vibe | external; ACM reproduced | `.github/secret_scanning.yml` | No CI: every green suite is one machine's run | task |
| 14 | E-05 | S2 | vibe | internal/construct; ACM functional | `tests/test_mcp_server.py:225` | Projection gate has no seeded-stale test; 'stale' branch never exercised | task |
| 15 | E-07 | S2 | vibe | internal/conclusion; ACM functional | `scripts/run_baseline_gates.py:145` | grounding_zero_ungrounded gate untested and passes vacuously at zero checked | task |
| 16 | A-03 | S2 |  | conclusion; SFV T4 | `docs/figures/fig3_pass_fail_table.caption.md:4` | Single-leg claim corrected on page H only; caption, page G, DN-009 still say it | wording |
| 17 | A-04 | S2 |  | conclusion; SFV T4 | `docs/brief/D_demo_runbook.md:103` | Unsupported 'OECD/JRC default' wording survives in score.py and pack page D | wording |
| 18 | A-05 | S2 |  | conclusion/construct | `docs/evidence/kg_questions.md:94` | Q3 graded 'answered' on five unadjudicated single-model judgments | task |
| 19 | A-09 | S2 |  | internal; ACM reusable; SFV T5 | `scripts/run_definition_pairs.py:92` | Spend and event provenance name the wrong task file | task |
| 20 | A-14 | S2 |  | conclusion | `docs/design/2026-10-02_DN-009_deck_rejected_evidence_map_first.md:27` | Eight open-tooling indicators have no measurement task before the summary | task |
| 21 | B-04 | S2 |  | construct/conclusion; SFV T4 | `docs/evidence/claims.yaml:830` (CL-032) | G5 classed no_standard although the catalog names an existing standard | ruling |
| 22 | B-05 | S2 |  | conclusion/construct | `docs/evidence/definition_pairs.md:62` | No positive control can show the judge detects a conflict | task |
| 23 | C-03 | S2 |  | construct/conclusion; SFV T1 | `assessment/harness/scan/rules/rule_a12_v3.py:98` (spec:A12) | A12 fail covers three states; spec defines incoherence as one | task |
| 24 | C-05 | S2 |  | conclusion/internal; SFV T3 | `scripts/score.py:390` (obs_5039cd5646be4ca314a8528d) | Rank-1 rests on one observation feeding two legs; probe says one | task |
| 25 | C-08 | S2 |  | conclusion/internal; SFV T4 | `assessment/harness/scan/rules/__init__.py:128` (fnd_d83f3a2fdd15edd4c2f06f22) | Generation 11-12 rules called pre-registered; judged on stored 2026-09-10 data | wording |
| 26 | C-09 | S2 |  | construct/conclusion | `docs/reports/scan_matrix_tierA_2026-09-10_rj4.json:5` (fnd_2b6bb1732e02a90e488b9639) | A10 judged on home pages; three ranks rest on it | task |
| 27 | C-10 | S2 |  | construct; SFV T1 | `framework/ai_readiness_framework.json:4659` (spec:D2) | D2 verdict is one robots.txt directive, scored as the indicator | ruling |
| 28 | C-11 | S2 |  | external/construct | `docs/reports/2026-09_fss_ai_readiness_L0.md:442` | 'Disallowed paths not fetched' contradicted by carve-out and Crawl-Delay | wording |
| 29 | C-12 | S2 |  | conclusion; SFV T4 | `docs/design/scoring_model.md:59` | Scoring page's stated implicit weights are stale; --check cannot see it | task |
| 30 | D-04 | S2 |  | internal/construct; ACM reproduced; SFV T4 | `scripts/build_projection.py:783` (events/batch-001.jsonl:99 (content_update, scan-eia-flagship-1-open-data)) | Projection ignores content_update: 18 Documents show superseded hashes | task |
| 31 | E-01 | S2 |  | internal/external; ACM functional; SFV T2 | `tests/test_framework_projection_roundtrip.py:59` | Neo4j tier skips, never fails; Seldon-side fail-not-skip rule not adopted here | task |
| 32 | E-02 | S2 |  | internal; ACM functional | `tests/test_figure_registration.py:162` | Broad except around code under test turns its bugs into skips | task |
| 33 | E-03 | S2 |  | external/internal; ACM reproduced | `CLAUDE.md:18` | Suite cannot collect on a machine with only the declared dependencies | task |
| 34 | E-06 | S2 |  | construct/internal; ACM functional; SFV T3 | `mcp/airkg_tools.py:489` | MCP projection gate compares nodes only, never edges | task |
| 35 | E-09 | S2 |  | internal/external; ACM functional | `tests/test_dispatch_config.py:298` | A test runs the real dispatcher and may write live seldon_events.jsonl | task |
| 36 | A-12 | S3 | vibe | internal | `docs/design_decisions.md:231` | Registration-time refusals in DD-025/026/028 have no implementation | task |
| 37 | A-18 | S3 | vibe | internal; ACM reproduced | `cc_tasks/2026-10-04_definition_pairs_last7_RESULT.md:25` | Every gate result in the RESULTs is self-reported; logs are not in the tree | task |
| 38 | B-12 | S3 | vibe | internal | `scripts/run_kg_questions.py:444` (Q5) | Q5 grade is hardcoded, not computed from the counts | task |
| 39 | C-15 | S3 | vibe | construct | `assessment/harness/scan/params.yaml:938` (spec:F4) | F4 pass threshold 0.5 has no citation or measured basis | task |
| 40 | A-13 | S3 |  | internal | `docs/design_decisions.md:717` | DD-042 ceiling guard never built; two runs under-declared | task |
| 41 | A-15 | S3 |  | internal; SFV T4 | `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md:23` | The standing map DN-005 still claims layers and a cadence that do not exist | wording |
| 42 | A-17 | S3 |  | conclusion | `seldon.yaml:57` | Promised measured basis for the poll interval never produced | task |
| 43 | A-19 | S3 |  | internal; SFV T4 | `docs/design_decisions.md:1078` | DD-060 cadence clause superseded elsewhere; design_decisions.md not annotated | wording |
| 44 | B-06 | S3 |  | internal; ACM functional | `docs/evidence/definition_pairs.csv:3` (pair 3d3926872aaaa128) | Judge parser accepts malformed answers; reasons carry model self-corrections | task |
| 45 | B-07 | S3 |  | construct | `docs/evidence/claims.yaml:1390` (CL-039) | Access-denial counts include findings dominated by server errors | ruling |
| 46 | B-08 | S3 |  | internal | `docs/evidence/claims.yaml:2231` (fnd_0443dfeb74d4b73499629f78) | Host-level B5 finding counted twice and labelled with wrong surfaces | wording |
| 47 | B-09 | S3 |  | construct | `scripts/build_figures.py:480` | Figure 2 labels all 280 documents literature; 25 are scan captures | wording |
| 48 | B-10 | S3 |  | construct | `docs/figures/fig2_system_at_a_glance.caption.md:4` | Figure 2's 1,009 findings include 27 on non-statistical comparators | wording |
| 49 | B-11 | S3 |  | conclusion | `docs/evidence/claims.yaml:3234` (CL-082) | CL-082's universal wording contradicts its own evidence notes | wording |
| 50 | B-13 | S3 |  | internal; ACM functional | `tests/test_evidence_map.py:114` | Evidence-resolution test never resolves indicator or requirement locators | task |
| 51 | B-14 | S3 |  | internal | `docs/catalog/rollups/rollups.md:52` | Set-cover tie-break described wrongly in the rollup | wording |
| 52 | D-05 | S3 |  | construct; SFV T1 | `docs/evidence/kg_questions.md:5` (Document scan-eia-flagship-1-open-data) | Graph corpus (281) disagrees with the corpus ledger (280 included) | ruling |
| 53 | D-06 | S3 |  | construct; ACM functional | `kg/extraction/grounding.py:39` | Grounding accepts NFKC-altered numbers, one-character and mid-word spans | task |
| 54 | D-07 | S3 |  | internal | `kg/extraction/pipeline.py:37` | Provenance stripping is envelope-only; item keys reach SET n += props | task |
| 55 | D-08 | S3 |  | construct; ACM reusable; SFV T1 | `kg/schema.yaml:2` | Schema source of truth is circular, and the doc lags 0.4.0 | wording |
| 56 | D-09 | S3 |  | construct | `scripts/assert_noaa_definition.py:123` (nao-216-128-artificial-intelligence-in-noaa::nao216-ai-ready-data (event 6f0c77bed2ad489ca808830420c3a27b)) | Curated NOAA Definition bypasses the span-coverage gate it would fail | wording |
| 57 | D-10 | S3 |  | internal | `kg/eventlog.py:108` | Event append flushes but never fsyncs, contrary to §15 | task |
| 58 | E-10 | S3 |  | construct | `Makefile:31` | `make guards` omits most of the repo's incident-replay guard tests | task |
| 59 | E-11 | S3 |  | internal; ACM reproduced; SFV T4 | `tests/test_scan_harness_v4.py:58` | Re-derivation set is hand-kept; one stored payload still missing | task |
| 60 | E-13 | S3 |  | construct | `tests/test_cq_collapse.py:120` | Tautological asserts compare a value with itself | task |
| 61 | E-14 | S3 |  | conclusion/construct | `tests/test_prescriptions.py:99` | Loop-only asserts over record collections with no non-emptiness check | task |
| 62 | E-15 | S3 |  | conclusion/internal; SFV T4 | `tests/test_kg_questions.py:115` | Regeneration check skips exactly when stored answers become stale | ruling |
| 63 | E-16 | S3 |  | external; ACM reproduced | `tests/test_scan_harness_v4.py:184` | Re-derivation gate needs git history; fails outside a clone | task |
| 64 | E-17 | S3 |  | internal; SFV T4 | `tests/test_brief_deck.py:46` | 23 tests are never executed but counted as xfailed | wording |
| 65 | E-18 | S3 |  | internal | `scripts/batch_repair.py:253` | batch_repair continues past a model substitution instead of stopping | task |
| 66 | F-21 | S3 |  | internal; SFV T2 | `cc_tasks/2026-10-04_full_audit.md:8` (2d9d2309-28cd-4c68-80c2-f1408c181e39) | Audit task says the dispatcher launched it, but its header is refused | wording |

### 4.2 The top ten in full

**1. C-01 (S1; construct/conclusion/internal; ACM functional; SFV T3). A1/A3 fails judge only the first 25 links of 48-244.** `assessment/harness/scan/params.yaml:704` (fnd_e5011a474f72fcb754b8c3d9)
- *Skeptic:* Every product surface on the source cycle carried 48 to 244 on-host links (Census ACS 115, Fed SCF 224, SAMHSA NSDUH 244) and links.probe stops at 25 in document order (mostly navigation) with no record of the rest (collectors/links.py:73 `break`), so A3's absence claim 'no whole-product download linked from the product page (25 link(s) probed)' and A1's 'no probed link serves a structured content type (25 link(s) observed)' are asserted over a truncated candidate set the absence guard cannot see; the project's own sources_per_check.json cites JSON from the Census Data API for ACS while A1 fails that surface.
- *Closes it (task):* Probe every on-host link (or rank candidates by data-likeness before the cap) and record unprobed candidates so an A3/A1 absence over a truncated set returns error, then re-judge; until then state the cap and the per-surface link totals beside every A1/A3 fail.
- *Checked:* Counted parsed.links per page observation in state/scan_2026-09-10.json against non-off-host link probes per surface: every product surface with links had probed=25 of 38-244 on-host links; read links.py:40-110 and rule_a3_v6/rule_a1_v4.

**2. C-02 (S1; conclusion/construct; SFV T2). Report says BLS/BTS/SSA publish permissive robots.txt; scanner never read one.** `docs/reports/2026-09_fss_ai_readiness_L0.md:187` (fnd ids of A12 for BLS/BTS/ORES in docs/reports/scan_matrix_tierA_2026-09-10_rj4.json)
- *Skeptic:* The L0 report says each of the three refusing bodies 'publishes a `robots.txt` that grants access' (lines 187-188) and that the client 'obeys the `robots.txt` those same hosts publish' (line 173), but every robots.txt read of www.bls.gov, www.bts.gov and www.ssa.gov on every cycle 2026-09-06..09-10 returned HTTP 403 (BLS 22 reads, BTS 10, SSA 10), their A4 cells are `error` ('robots.txt could not be observed: refused'), and their own A12 Findings say 'the declared layer is not observable'; no grant was ever observed.
- *Closes it (wording):* Reword lines 143-148, 173-174 and 187-190 to what the Findings say (the host refused /robots.txt itself; under RFC 9309 §2.3.1.3 an unavailable file permits access) or drop the claim.
- *Checked:* Grepped all events/*.jsonl for observation_recorded on https://{www.bls.gov,www.bts.gov,www.ssa.gov}/robots.txt and tallied status by date (all 403); read the rj4 A4 and A12 finding_derived reasons for the three bodies.

**3. C-04 (S1; construct/external). D4 and four DCAT legs read only the scanned host's data.json.** `assessment/harness/scan/rules/rule_d4_v3.py:86` (ind:D4)
- *Skeptic:* ind:D4 reads 'enumerable from a public inventory (data.gov/agency inventory current)' but spec:D4 and RULE-D4-v3 fetch only <host>/data.json, so 28 rows fail 'no public data.json catalog served on this host' (ERS/NASS/APHIS on usda.gov subdomains, NCES, BJS, NCHS, SOI...) and are prescribed 'Publish a data.json inventory on the host', while the project's own params note that data.gov reads each DEPARTMENT's data.json (params.yaml:296-297); DRSMSU passes only because the Board's catalog shares its host, and B1, B4, D3 and G4 inherit the same host-coincidence through CONSUMES = ("D4",), so 5 of 21 scored legs turn on it.
- *Closes it (task):* Resolve each body's departmental inventory (and catalog.data.gov) before D4 judges absence, or narrow the indicator and prescription text to 'on this host' and state it in the report.
- *Checked:* Read spec:D4 signal, ind:D4 text, rule_d4_v3.py, _dcat_fields.read and the D4/G4 Action nodes; tallied rj4 D4 reasons (28 no-catalog fails).
- *Re-graded S2 → S1:* a shown prescription ('Publish a data.json inventory on the host') contradicts the indicator's own text ('data.gov/agency inventory current') for bodies whose department inventory data.gov reads

**4. C-06 (S1; construct/internal; SFV T4). Frontier indicator A9 enters every body's score.** `assessment/harness/scan/rules/rule_a9.py:1` (ind:A9)
- *Skeptic:* The protocol says frontier mechanisms 'never enter the core score' and 'absence is not a deficiency' (docs/crosswalk/assessment_protocol.md:66-72), spec:A9's decision says 'A9 is FRONTIER (as_of 2026-01) and is reported, never scored', and ind:A9 carries frontier: true, yet score.py scores A9 as one of criterion A's ten legs for every body (all fail), so every published score is lowered by it (CENSUS 0.080 vs 0.089 without A9, EIA 0.133 vs 0.160) and SAMHSACBHS's flat rank moves 7 to 5.
- *Closes it (task):* Exclude indicators with frontier: true in score.structure (as candidates are) and regenerate scoring_model.md and every quoted score, or record a ruling that retires the firewall.
- *Checked:* Read score.structure (selects on measurement_basis only), ind:A9/spec:A9 properties; recomputed all bodies with A9 unscored via score.score_body.
- *Re-graded S2 → S1:* every published score includes a frontier: true indicator that DD (design_decisions.md:537-539) says is kept out of the core score 'unchanged'; score.py --json structure has A9 scored: True

**5. C-07 (S1; internal/conclusion; ACM reproduced; SFV T5). Record says 16 measured; cycle of record scores 21 of 48.** `framework/ai_readiness_framework.json:18` (ind:G4)
- *Skeptic:* The record keeps B1, B2, B4, B5, D2, D3 and G4 at measurement_status 'harness_built' and G1-D at 'measured', but the cycle of record judges and scores the seven (G4 decides the rank-1 body) and withdraws G1-D (DD-066), so the site's progress page prints '16/48 measured' (docs/progress/index.html:55-56) while fig1 and the brief print '21 of 48 indicators measured'; two public numbers for one quantity, and measured_by on every 'measured' node still points at scan_2026-09-07.
- *Closes it (task):* Run the measured write-back against scan_2026-09-10_rj4 through framework_writeback.save, project, and rebuild the progress page; or define the two quantities with different names on both surfaces.
- *Checked:* Recomputed every counts value from nodes/edges (all 18 match the stored block), then compared node measurement_status with score.py --json coverage (21 indicators scored) and the rj4 matrix legs.
- *Re-graded S2 → S1:* two public numbers for one quantity: docs/progress/index.html:55 '16/48 measured' vs docs/brief/G_census_dogfood.md:10 '21 of 48 … measured'

**6. C-13 (S1; construct/conclusion). Parent-department host files scored and ranked as the unit's.** `assessment/harness/scan/targets.yaml:96`
- *Skeptic:* The roster itself says NCHS's robots.txt, /data.json and /.well-known/ answer for CDC and a finding against them is not a finding about the statistical agency, yet NCHS's A4, A5, A11-declared, D2 and the five data.json legs are read from www.cdc.gov and NCHS is ranked 13 of 13 (the same holds for SOI on irs.gov, ORES on ssa.gov, DRSMSU on federalreserve.gov), and neither the L0 report nor docs/brief/H_limits.md says so.
- *Closes it (ruling):* Mark parent-host cells on the matrices and exclude them from unit scores and ranks, or state the limitation beside every rank.
- *Checked:* Read targets.yaml:89-99 and the rj4 matrices; grepped the L0 report, H_limits.md and scoring_model.md for parent/cdc.gov/shared host (no caveat found).
- *Re-graded S2 → S1:* a shown rank (NCHS 13 of 13) rests on cells the roster itself (targets.yaml:93-96) says are 'not a finding about the statistical agency', undisclosed in the L0 report

**7. C-14 (S1; construct/conclusion). Census ACS fails 'documented public API'; prescribed to build one.** `assessment/harness/scan/rules/rule_a2_v3.py:59` (fnd_b9e93605be55aeffa1b2633f)
- *Skeptic:* spec:A2 says GET 'the documented API base', but the collector probes only three guessed paths on the scanned host (www.census.gov/openapi.json, /swagger.json, /api/openapi.json, all 404), so the ACS flagship fails A2 (CLAIM_BY_LEG 'no documented API') and docs/brief/G_census_dogfood.md:125 prescribes 'Expose the product through an API and publish the API's description', while this repo's own docs/data/sources_per_check.json:237 cites the Census Data API endpoint for ACS 5-year.
- *Closes it (task):* Follow the agency's documented API base (declared per body, or discovered from the page/data.json) before A2 judges absence, and withdraw the A2 prescription for bodies with a documented API.
- *Checked:* Listed A2 observation URLs/statuses for Census surfaces in state/scan_2026-09-10.json; read spec:A2, rule_a2_v3.py, CLAIM_BY_LEG and the A2 Action nodes; grepped docs for api.census.gov. *Session:* Session check: finding fnd_b9e93605be55aeffa1b2633f reason 'no OpenAPI/JSON API description served at any probed path'; the API exists (sources_per_check.json:237 cites api.census.gov), whether it serves an OpenAPI description was not checked (no network).

**8. A-07 (S2, vibe; internal). DD-029 acceptance sampling not run on Commerce or DCAT extractions.** `docs/design_decisions.md:421`
- *Skeptic:* About 4,400 nodes from 14 documents (Commerce, the nine DCAT-US 3.0 documents, the four A01 documents) were projected with no faithfulness sample, even though DD-029 says a batch projects only on an SPRT accept; these documents back the OMB FAQ.
- *Closes it (task):* Run the standing probe/SPRT over the Commerce, dcat_us_3 and dcat_us_3_a01 runs, or record in a DD why one-off cohorts are exempt.
- *Checked:* grep -i 'sprt/faithful/judge/accept' scripts/run_dcat_extraction.py scripts/run_commerce_extraction.py returned nothing; grep -i 'SPRT/DD-029/faithful' over the 2026-10-02..05 RESULTs returned nothing; scripts/build_projection.py:371-391 projects every batch unless a bulk_batch_quarantined event names it.

**9. A-10 (S2, vibe; internal; SFV T2). DD-040 'every graph figure is a registered Result' is not enforced.** `docs/design_decisions.md:686`
- *Skeptic:* October RESULTs and task files quote graph counts that resolve to no kg_diag_/cq_ Result, and one set (4,070 spans, 1,966 keys, 815 Claim, 184 Definition) did not reproduce, which is the exact defect DD-040 exists to stop.
- *Closes it (task):* Register a dated kg_diag snapshot whenever a RESULT quotes graph counts, and add a check that flags graph numerals in new RESULTs with no matching Result.
- *Checked:* grep of seldon_events.jsonl for kg_diag_ Result names: the newest snapshots are 2026-09-04b and 2026-09-05; no Result carries 2959, 34878 or 43032; the node_key_fusion_audit_RESULT §7 premise 3 records that the Commerce RESULT's figures came from an uncommitted query and do not reproduce.

**10. D-01 (S2, vibe; internal/construct; ACM reproduced; SFV T2). Edges written onto both label-twins: 301 spurious edges, 75 schema-illegal ASSERTS.** `scripts/build_projection.py:557` (w3c-dcat-3::c1)
- *Skeptic:* The graph says w3c-dcat-3 ASSERTS the Concept 'quality assessment service'; no extraction asserted that, the unlabelled MERGE copied a Claim's edge onto a Concept sharing its key, and the lint test allowlists the exact line on the false premise that endpoint types are unknowable (12,292 edge events carry from_type/to_type; the chunked writer drops them at scripts/chunked_pilot.py:721).
- *Closes it (task):* Carry from_type/to_type on every edge event (or resolve them from the same chunk's node events), MERGE endpoints by label, check the schema endpoint pair at projection, remove the ALLOW entry in tests/test_cypher_unlabelled_lint.py:35, and add a test with a Claim+Concept twin key.
- *Checked:* Offline replay of the audit copy's log mirroring build(): unique edges per type plus label-twin multiplicity reproduce live Neo4j exactly (ABOUT 6,901+157=7,058, ASSERTS 7,598+75=7,673, MENTIONS 9,905+43=9,948, MEASURES +12, APPLIES_TO +8, RECOMMENDS +4, SUPPORTED_BY +1, TARGETS +1); Cypher over the 87 twin keys returns the same 301; MATCH (:Document)-[:ASSERTS]->(:Concept) returns 75 against schema pairs [[Document, Claim]].

### 4.3 What the session re-checked itself, and the re-grades

The session re-read the locator of every S1 and of D-01, D-02, D-03/E-08 and F-09 on the live checkout (equal to HEAD), and queried the graph:
- C-01: `params.yaml:704` `max_links_probed: 25` and `collectors/links.py` `break` at the cap.
- C-02: `L0.md:187-188` "each publishes a `robots.txt` that grants access"; BLS A12 Finding `fnd_43cf49086ef11fa38f0e03d6`: "the host answered HTTP 403 to /robots.txt itself"; A4 `fnd_3b4e02825d5c7cddaa8e67f6`: "robots.txt could not be observed: refused". The same report, lines 145-149, defines an incoherent host as one that publishes a granting `robots.txt` and says the fourth "publishes no `robots.txt` at all" (C-03).
- C-06: `ind:A9` has `frontier: true`; `score.py --json` structure has A9 `scored: True`; `design_decisions.md:537-539` carries the firewall forward "unchanged"; `docs/crosswalk/assessment_protocol.md:66` "never enter the core score".
- C-07: `docs/progress/index.html:55` "16/48" measured; `docs/brief/G_census_dogfood.md:10` "21 of 48 framework indicators … are measured"; record status counts measured 16, harness_built 8, specified 25.
- C-13: `targets.yaml:93-96`: "a finding against them is not a finding about the statistical agency"; no disclosure in the L0 report (grep for parent/department).
- C-14: Finding `fnd_b9e93605be55aeffa1b2633f`, "no OpenAPI/JSON API description served at any probed path"; `docs/data/sources_per_check.json:237` cites `api.census.gov`. Whether that API serves an OpenAPI description was not checked (no network).
- D-01: Cypher, `(:Document)-[:ASSERTS]->(:Concept)` = 75 edges over 12 documents; `kg/schema.yaml:304-307` allows only `[Document, Claim]`.
- D-02: `scripts/audit_node_key_fusion.py --check` at HEAD: "DRIFT … (generated block)", EXIT=1 (`logs/2026-10-06_full_audit_fusion_check.log`).
- D-03/E-08: Cypher, 1,335 HAS_COMPONENT/SUBTYPE_OF/IMPLEMENTS/CONSUMES/EXTENDS edges, 0 with `faithfulness_epoch`.
- F-09: `adopt.py:155-196` stamps every row with the home netloc and `check_identity` (`:220-249`) reads `r["host"]`; whether a later fetch layer blocks an off-host flagship was not shown.

Four readers' S2s were re-graded S1 under the §1.3 test, because each makes a statement in shown material false. The reason is on each row (`regrade_reason`): C-04, C-06, C-07 and C-13. No grade was lowered.

## 5. Operationalization: what a stranger needs to run this on one site

**19 items**, in the order a stranger following `docs/adopt/run_on_your_site.md` would hit them: S2 10, S3 9. Each locates its dependency. The modular-roster record `712755f8` (a ResearchTask with no task file) was read: it covers none of these items directly, and overlaps F-08 (adopter identity in the tracked params) and F-09 (the identity guard). E-03 (the suite does not collect with only the declared dependencies) and E-04 (no CI) are in §4 and bear on this list too.

| # | id | sev | ACM | locator | where it breaks | closes by |
|---|---|---|---|---|---|---|
| 1 | F-01 | S2 | available | `README.md` | README never points a stranger to the adopter runbook: A stranger who lands on the README finds a KG description and `pytest`, with no mention that the repo can scan their site or where docs/adopt/run_on_your_site.md is; the Layout block omits assessment/, mcp/ and framework/, where the scan harness, the MCP server and the framework live. | wording: Add a 'Run it on your site' section to README.md linking docs/adopt/run_on_your_site.md and list assessment/, mcp/, framework/ in Layout. |
| 2 | F-02 | S2 | available | `README.md:50` | README says the corpus is committed; a clone lacks it: The corpus binaries are gitignored (.gitignore:34-67, 106), so a clone holds 65 of the 1,371 corpus/ file paths that corpus/manifest.json names; the README's 'committed' is false and a stranger cannot re-run anything that reads the documents. | wording: Correct README line 50 to say the binaries are local-only and how to re-acquire them (see F-17). |
| 3 | F-03 | S3 | available | `docs/adopt/run_on_your_site.md:18` | The clone step has never been run by the gate: Block 1 is marked not-run-by-gate and the gate substitutes a local copy, so nothing on record shows the URL resolves to a public repo holding this commit; the same URL is the contact in the scanner's User-Agent. | task: Run the clone and install from a machine with no access to the author's accounts and record the log, or state in the runbook that the URL was checked and when. |
| 4 | F-04 | S2 | reproduced | `docs/adopt/run_on_your_site.md:20` | Install line is unpinned though the page lists tested versions: The page says 'Versions are the ones the gate ran under' (httpx 0.28.1, rdflib 7.6.0, pyshacl 0.40.1 ...) but the install command pins nothing and there is no requirements file or lock, so a stranger installs whatever is current and may run a different instrument (parsers feed verdicts) with no warning. | task: Ship a pinned requirements file (or pyproject extra with ==/~= pins) and make step 1 install from it; have the gate install from that file into a fresh venv. |
| 5 | F-05 | S2 | reusable | `pyproject.toml:10` | pyproject declares one runtime dependency; the scan alone needs nine: pyproject declares only pyyaml (plus optional fastmcp/neo4j), while the scan path imports bs4, extruct, httpx, jsonschema, protego, pyshacl, rdflib, usp, yaml, and the repo as a whole imports seldon (75 sites), dixie (65), docling, pypdf, tiktoken, nltk, numpy, pandas, crowdkit, matplotlib, pptx, PIL, sentence_transformers, requests and two modules that do not resolve here (control_plane, harvester); there is no [build-system] and setuptools' flat-layout discovery finds 11 top-level packages, so `pip install .` would not install a working tool. | task: Declare the scan dependencies as a pinned extra (e.g. `[project.optional-dependencies] scan`), declare or vendor seldon/dixie for the paths that need them, and add a [build-system] with explicit packages. |
| 6 | F-07 | S3 | reusable | `Makefile:18` | Every make target defaults to the author's interpreter path: The runbook exports PY in one shell; a stranger who runs `make scan-now` from a new terminal, or any other target (gate-*, guards, report-pdf, project), gets /opt/anaconda3/bin/python3, which does not exist off this machine. | task: Default PY to `python3` (or $(shell command -v python3)) and fail with a message naming PY when it lacks the scan packages. |
| 7 | F-08 | S3 | reusable | `docs/adopt/run_on_your_site.md:50` | Adopter identity and schedule require editing the tracked params.yaml: Step 2 (and step 6's `schedule:`) edit the committed assessment/harness/scan/params.yaml in place, leaving a dirty tree and a .orig file; every upstream params change then conflicts on pull, and this repo's own test test_the_schedule_key_moves_no_hash_and_the_identity_does (asserting the committed params hash) fails in the adopter's checkout. | ruling: Read the scanner identity and schedule from an untracked per-adopter file or the frame (with params_hash covering it), so params.yaml stays the shared instrument. |
| 8 | F-09 | S2 | functional | `assessment/harness/scan/adopt.py:231` | Identity guard bypassed by a loopback home with an external flagship: check_identity tests each row's `host`, but compile_rows stamps every row with the HOME's netloc, so a frame whose home is 127.0.0.1 and whose flagship is https://www.example.gov/... passes the guard and the scan reaches the external host as ai-readiness-kg-scanner, contradicting the runbook's 'run.py refuses to reach any non-loopback host under this project's identity'; load_frame also does not require flagships to share the home's host. | task: Check identity against the netloc of every URL the frame will fetch (each row's url, not the body's host), add the mixed frame as a refusal case in tests/test_adopter_path.py, and decide whether off-host flagships are allowed. |
| 9 | F-10 | S3 | reusable | `assessment/harness/scan/params.yaml:402` | Adopter scans still write this project's name into target logs: The adopter guard's stated reason is that a scan under this project's identity 'puts this project's name and contact in the target's logs' (adopt.py:224-226), yet every A10 probe of every flagship requests <flagship>/__ai-readiness-kg-probe-404__, so an adopter's scan still names this project in the target's access log, under the adopter's User-Agent. | task: Derive the probe suffix from the configured product token, or a neutral string, and record it in params_hash as now. |
| 10 | F-11 | S2 | functional | `assessment/harness/scan/run.py:509` | Scan loop has no checkpoint, resume, ETA or ceiling: run_cycle loops over every surface at 1 request/s and writes the payload once at the end, so a kill, crash or laptop sleep loses the whole run; there is no per-surface persistence, no resume by skip, no ETA, no wall-clock ceiling, which is the ~/GitHub/CLAUDE.md §15 rule for networked loops over two minutes; the runbook gate took 676.7 s for four loopback surfaces, and the project's 2026-09-07 cycle took 46 minutes (params.yaml:724). | task: Persist each surface's observations and findings to a JSONL checkpoint keyed by (cycle, doc_id, leg, params_hash) as it completes, skip completed keys on re-run, print done/total/ETA, and add the SIGKILL-and-resume test §15 item 8 requires. |
| 11 | F-12 | S3 | functional | `tests/test_adopter_path.py:208` | Twice-daily schedules are accepted, then every second run fails: install_schedule accepts any five-field cron (the test even uses '0 */12 * * *'), but the scheduled job is `make scan-now` with no rerun letter, and run.py refuses a second run of a frame on the same UTC day (run.py:688), so every second firing exits non-zero into scheduled.log; the day is UTC while cron fires in local time; no scheduled job has ever been run end to end by the gate, which runs only the on_demand branch. | task: Either refuse schedules that can fire more than once per UTC day, or have the scheduled job pick the next rerun letter; add a test that runs the installed job twice. |
| 12 | F-13 | S2 | functional | `assessment/harness/scan/publish.py:570` | Optional Neo4j step needs Seldon, though the runbook says Seldon is unused: The runbook says 'Neo4j is optional, and Seldon is not used.' and step 7 needs only NEO4J_USER/NEO4J_PASS, but `make project` runs build_projection.py, whose scan layer calls publish.project, which imports seldon.config, a package that is not on the declared dependency list and exists here only as an editable install from /Users/brock/GitHub/seldon (publish.py:28 hard-codes that path), so step 7 fails with ModuleNotFoundError on a stranger's machine. | task: Give publish.project the same driver/creds helper build_projection uses (no Seldon), or document and declare Seldon as step 7's dependency. |
| 13 | F-14 | S3 | functional | `scripts/build_projection.py:53` | Step 7 needs a Neo4j database the runbook never says to create: build_projection and the MCP guard bind to seldon.yaml's `seldon-ai-readiness-kg`, and `neo4j`, the one database a fresh install has, is refused as protected; the runbook does not say to create the database or to rename the default, and Neo4j Community Edition holds a single standard database (from Neo4j's documentation as recalled; not fetched in this offline audit), so a stranger's first `make project` fails. | wording: State in step 7 which edition is needed and the exact setup (CREATE DATABASE, or Community's default-database setting), or make the database name configurable from an untracked file. |
| 14 | F-15 | S3 | reusable | `scripts/build_projection.py:271` | Neo4j credentials fall back to another project's dotfile, by two different routes: build_projection falls back to ~/.wintermute/.env (another system's secrets file) when NEO4J_USER is unset, while the scan layer inside the same `make project` takes credentials through Seldon's resolver, which defaults to neo4j/password; a stranger gets two credential paths in one command and neither is documented beyond 'needs NEO4J_USER and NEO4J_PASS'. | task: One credential resolver for the whole projection, reading env (or a repo-local .env) and failing loud naming the variable, per ~/GitHub/CLAUDE.md §4. |
| 15 | F-16 | S3 | reusable | `mcp/airkg_tools.py:54` | Author-machine paths are hard-coded across code, config and job files: 46 `sys.path.insert(0, "/Users/brock/GitHub/seldon")` lines in 37 code files (including airkg_tools.py on runbook step 5 and publish.py on step 7); .mcp.json names /opt/anaconda3/bin/python3 and /Users/brock/GitHub/ai-readiness-kg; seldon.yaml:14 points the ontology at /Users/brock/GitHub/seldon/ontology; scripts/jobs/com.brock.airkg-dispatch.plist and airkg_dispatch.sh hard-code /Users/brock, /opt/anaconda3 and ~/.wintermute/.env; docstrings throughout give /opt/anaconda3/bin/python3 as the way to run. Harmless where the path is absent only because the import is lazy; each is a place a stranger's run depends on this machine. | task: Replace the sys.path inserts with a declared dependency, and generate .mcp.json and the plist from the checkout path. |
| 16 | F-17 | S2 | available | `.gitignore:32` | No tool re-acquires the gitignored corpus from the manifest: The stated reproduction path for the gitignored corpus is 're-fetch + re-hash', but no script walks corpus/manifest.json to re-fetch and verify each document, and the one fetch helper (scripts/fetch_allowlisted.py) refuses to run unless the dispatcher's SELDON_NETWORK_ALLOWLIST is set, so a stranger has no supported route from a clone to the documents behind the KG. | task: Ship a `restore-corpus` command that re-fetches every admitted entry by primary_url, checks sha256, and reports mismatches and unacquirable entries as rows. |
| 17 | F-18 | S2 | reproduced | `kg/extraction/model_stub.py:50` | KG extraction can only be re-run under a Claude Max OAuth login: The validity layer's extraction refuses API keys and runs only through the `claude` CLI under a subscription OAuth login (model_config.yaml provider claude_max_oauth), with dixie, pypdf and tiktoken undeclared and the corpus absent (F-02); a stranger with an API key, or another provider, cannot re-derive a single edge, so 'every assertion citable by a stranger' is checkable only against stored raw responses, never re-run. | ruling: Document the extraction re-run path with its requirements, and decide whether an API-key provider is an allowed alternative for reproduction (it is a different billing path, not a different model). |
| 18 | F-19 | S3 | reproduced | `CLAUDE.md:52` | CLAUDE.md names a superseded extraction model pin: CLAUDE.md says the extraction model is pinned to claude-opus-4-8, but kg/extraction/model_config.yaml:14 sets `model_id: claude-opus-5` under an operator decision of 2026-08-27 that its own comment says 'Supersedes the 2026-07-03 claude-opus-4-8 pin'; a stranger setting up the model gate from CLAUDE.md gets the wrong model and the run STOPs. | wording: Change the CLAUDE.md line to point at model_config.yaml without copying the value. |
| 19 | F-20 | S2 | reproduced | `tests/test_adopter_path.py:510` | The 'stranger' gate is the author's machine, interpreter and home directory: The runbook gate prepends /opt/anaconda3/bin, so `command -v python3` resolves to the author's interpreter, which also has seldon, dixie, neo4j and fastmcp; it runs on the same macOS host with the same HOME (~/.wintermute/.env); and its 'clone' is `git ls-files -co`, which includes untracked files, so the runbook's 'That is what a clone of the pushed commit holds.' is not true; no run on a fresh environment, another OS or a real non-loopback site is on record. The AST requirements check (test lines 407-436) partly covers dependencies for scan+render only. | task: Run the runbook in a clean container or VM from a real clone into a fresh venv built only from the declared requirements, and record that log as the adopter evidence. |


## 6. Controls on the auditor (task decision 6)

`scripts/plant_audit_controls.py` copied HEAD (`a5b5134f`) by `git archive`, planted one defect of each kind at a location drawn by `secrets`, and verified by git object hash that the copy differed from HEAD in exactly the three planted files. It wrote the manifest outside the copy. The manifests were opened only after the merged findings were frozen (sha256 `f1db3871…aede8` of the merged set, unchanged afterwards). Both copies were then removed by the script's `remove` mode, which checked that the plants were still as written and that the checkout's three paths equal HEAD (`logs/2026-10-06_full_audit_remove_controls.log`, both EXIT=0). Nothing planted was ever in the checkout.

| run | plant | where it was placed | caught? | blind? |
|---|---|---|---|---|
| 1 | test with no assertion | `tests/test_extraction_schema_pairs.py:155`, `test_extraction_schema_pairs_payload_round_trip_is_stable` | **yes**: E-12 (by an `ast` scan for test functions with no assertion) | **yes**. Reader E did not open the task file. |
| 1 | claim with a wrong locator | `docs/evidence/claims.yaml:2057`, CL-046, `#ind:A12` re-pointed to `#ind:E3` | yes: B-02 | **no**. Reader B diffed `claims.yaml` against `git show HEAD:` in the live checkout before its checks, against its brief, and says so in its read record. It reports that the generators' `--check` then flagged the same drift. |
| 1 | caption number off by one | `docs/figures/fig1_usafacts_to_framework.caption.md:4`, "3 added" made "4 added" | yes: A-01 and B-01 | **no**. Reader A had read the task file and so knew plants existed. Reader B was contaminated as above. |
| 2 | claim with a wrong locator | `docs/evidence/claims.yaml:214`, CL-004, `#ind:B2` re-pointed to `#ind:F2` | **yes**: R2-01 (a script resolving each locator's node id against the entry's id, note and claim text) | **yes** |
| 2 | caption number off by one | `docs/figures/fig1_usafacts_to_framework.caption.md:4`, "48 indicators" made "49" | **yes**: R2-02 (number-by-number comparison with `numbers.json`, the SVG text and the record, then `build_figures.py --check`) | **yes** |
| 2 | test with no assertion | `tests/test_cli_outcome_classes.py:221` | not measured: tests were outside R2's scope | n/a |

**Why run 2 exists.** Run 1's locator and caption detections were contaminated, so they measure nothing about the audit. Run 2 used a fresh copy and a fresh random draw. It deleted `cc_tasks/`, `docs/design/` and `docs/research/` from that copy, so the reader could not learn controls existed, and it barred the reader from the live checkout and from git. R2 reported exactly two defects, both plants, so it had no false positives.

**What the controls show, and what they do not.**
- Each of the three kinds was caught blind once.
- That is n = 1 per kind, so no detection rate is claimed.
- Run 2's scope (claims and captions) was chosen by plant *kind*, which the session knew from the task file, though not by location. A reader of the whole tree has a weaker prior than R2 had.
- Both caption plants are also caught mechanically by the existing `scripts/build_figures.py --check`. So that defect class already has a machine guard, and the audit's catch is not the only one.

## 7. Reader gate (DN-009 decision 7)

A fresh subagent was given only the ranked findings table (§4.1's rows: rank, id, severity, vibe, validity, locator, title, skeptic sentence) and told to read nothing else. Its answer, verbatim:

> 1. The scanner fails agencies for things it never fully looked for: it checks only the first 25 of 48 to 244 links, only the scanned host's data.json, and three guessed API paths. So Census ACS is told to build an API that the project's own sources file cites, and 28 rows are told to publish an inventory that data.gov reads at the department level.
>
> 2. The L0 report says BLS, BTS and SSA publish a robots.txt that grants access, but every one of the 42 reads of those files returned 403. A report that claims to have observed something its own logs show it never saw makes me doubt every other sentence in it.
>
> 3. The scores break the project's own published rules: frontier indicator A9, which the protocol says "never enters the core score", lowers every body's score and moves ranks. Rules called "pre-registered" were written after the data they judge was already on disk, and those verdicts decide rank 1.
>
> 4. Rank 1 rests on a single fetch of federalreserve.gov/data.json that feeds five legs. NCHS, SOI, ORES and DRSMSU are scored on their parent department's host files. Yet the robustness probe treats the legs as independent and says DRSMSU would only drop to rank 4, when losing that one observation drops it to 9.
>
> 5. The checks that are supposed to catch all this cannot fail. The Neo4j gate counts as green whenever it is skipped, the zero-ungrounded gate passes having checked nothing, and nothing ever runs outside the operator's machine (no CI). Every gate log is gitignored, and the site prints "16/48 measured" while the brief prints "21 of 48", so I could not check any "green" myself.
>
> First: Fix the absence verdicts in finding 1 (C-01, C-04, C-14) so that a fail must record and cover the full search scope, or else say `not_observed`. These are the errors that send specific, wrong instructions to named agencies under the project's name, and every score, rank and prescription built on those legs inherits them.

Its five numbered points each run to two sentences, so it gave ten sentences where five were asked for. They are quoted as given. Every point traces to a row in the table: points 1 and 2 to C-01, C-04, C-14 and C-02; point 3 to C-06 and C-08; point 4 to C-05 and C-13; point 5 to E-01, E-07, E-04, A-18 and C-07. It invents nothing beyond the table.

## 8. Limits

1. **Model.** The session and all eight subagents ran under `claude-opus-5-5`, not the `claude-fable-5-1` the task names, so the task's own condition for a by-hand re-run under Fable holds. The audit, its CSV and the RESULT are immutable once written, so a Fable re-run must write new files.
2. **One instrument tier.** Every reader shares the session's model tier. The rubric's own scope limit applies (§3.1): this design catches errors that come from bad evidence, not errors the model makes systematically. One reader per slice, so no inter-reader agreement was measured, and none is claimed (rubric §9).
3. **No network.** Nothing outside the repository and the local graph was checked. So it is not known whether `api.census.gov` serves an OpenAPI description (C-14), and F-14's Neo4j Community claim is recalled.
4. **Gate logs.** The gate logs behind every RESULT are gitignored and were not re-read (A-18), so the audit could not check any RESULT's suite counts.
5. **Severity is the session's call.** The re-grades in §4.3 are the session's application of §1.3. Four S2s were raised to S1, and none was lowered. The reader's grade is kept beside each one in the CSV.
6. **Contamination.** Reader B read outside its copy (§6), and reader A had read the task file. Their non-control findings stand on their own checks, but their control detections are void.
7. **The rubric's verdict records were not produced.** The code overlay is a stub (§1.4).
8. **The definitions of the Wohlin validity classes are recalled** (§1.1).

## Appendix A. The readers' read records

Each reader's record of what it read in full, read in part, and did not read, as written. Scratch paths are elided as `<scratch>`.

### Reader A

```
SLICE A: files read (repo-relative, audit copy)

cc_tasks: task files and RESULTs dated 2026-10-02 to 2026-10-04 (all read in full)
full  cc_tasks/2026-10-02_commerce_guidance_admission.md
full  cc_tasks/2026-10-02_commerce_guidance_admission_ADDENDUM-01.md
full  cc_tasks/2026-10-02_commerce_guidance_admission_RESULT.md
full  cc_tasks/2026-10-02_evidence_map_prior_art.md
full  cc_tasks/2026-10-02_evidence_map_prior_art_v2.md
full  cc_tasks/2026-10-02_evidence_map_prior_art_v2_RESULT.md
full  cc_tasks/2026-10-02_evidence_map_record.md
full  cc_tasks/2026-10-02_evidence_map_record_RESULT.md
full  cc_tasks/2026-10-02_kg_research_questions.md
full  cc_tasks/2026-10-02_kg_research_questions_ADDENDUM-01.md
full  cc_tasks/2026-10-02_kg_research_questions_RESULT.md
full  cc_tasks/2026-10-02_scan_catalog.md
full  cc_tasks/2026-10-02_scan_catalog_ADDENDUM-01.md
full  cc_tasks/2026-10-02_scan_catalog_RESULT.md
full  cc_tasks/2026-10-02_summary_figures.md
full  cc_tasks/2026-10-02_summary_figures_RESULT.md
full  cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4.md
full  cc_tasks/2026-10-04_DCAT-002_dcat_us_3_intake_and_g4_RESULT.md
full  cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_base_standard_and_fairness_record.md
full  cc_tasks/2026-10-04_DCAT-002_ADDENDUM_01_RESULT.md
full  cc_tasks/2026-10-04_definition_conflict_pass.md
full  cc_tasks/2026-10-04_definition_conflict_pass_RESULT.md
full  cc_tasks/2026-10-04_definition_pairs_completion.md
full  cc_tasks/2026-10-04_definition_pairs_completion_RESULT.md
full  cc_tasks/2026-10-04_definition_pairs_last7.md
full  cc_tasks/2026-10-04_definition_pairs_last7_RESULT.md
full  cc_tasks/2026-10-04_node_key_fusion_audit.md
full  cc_tasks/2026-10-04_node_key_fusion_audit_RESULT.md
full  cc_tasks/2026-10-04_views_regenerate.md
full  cc_tasks/2026-10-04_views_regenerate_RESULT.md
full  cc_tasks/2026-10-04_views_regenerate_v2.md
full  cc_tasks/2026-10-04_views_regenerate_v2_RESULT.md
full  cc_tasks/2026-10-04_views_regenerate_v3.md
full  cc_tasks/2026-10-04_views_regenerate_v3_RESULT.md
full  cc_tasks/2026-10-04_full_audit.md  (context only)

docs/design (DN-005 on) and design_decisions
full  docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md
full  docs/design/2026-09-15_DN-005_..._ADDENDUM_01.md, _ADDENDUM_02.md, _ADDENDUM_03.md
full  docs/design/2026-09-15_DN-006_standing_dispatcher.md
full  docs/design/2026-09-15_DN-006_..._ADDENDUM_01.md through _ADDENDUM_07.md
full  docs/design/2026-09-19_DN-007_operator_rulings_and_state.md
full  docs/design/2026-09-22_DN-008_operator_rulings_and_brief_destination.md
full  docs/design/2026-10-02_DN-009_deck_rejected_evidence_map_first.md
full  docs/design/2026-10-02_DN-010_value_effort_matrix_decision_support.md
full  docs/design/2026-10-04_DN-011_dcat_us_3_intake.md
full  docs/design/scoring_model.md
full  docs/design_decisions.md (DD-001 to DD-068, all 1284 lines)

Verification reads (partial)
partial events/batch-001.jsonl (lines 108-127, manifest_add sequence)
partial events/batch-023.jsonl (line 58680; events after 2026-10-04 aggregated by type/task; DCAT node_asserted keys)
partial events/batch-033_framework.jsonl (event 6522fdfe...; task field counts)
partial events/batch-044_xdoc_conflict_held.jsonl (line count only)
partial events/cycle-scan_2026-09-10_rj4.jsonl (aggregated: 1009 finding_derived; G4 verdicts 37/8/1)
partial state/spend_ledger.jsonl (aggregated declare/reserve/settle/release/refuse for the 6 runs in slice)
partial seldon_events.jsonl (grep: kg_diag_ Result names, 9a627af8, e56cd2fb, ResearchTask creations since 2026-10-01)
partial docs/evidence/claims.yaml (CL-046..CL-054, CL-083 region 3350-3362)
partial docs/evidence/kg_questions.yaml (header, Q3 lines 681-720) and kg_questions.md (header, Q3)
partial docs/evidence/definition_pairs.csv (aggregated all 158 rows)
partial docs/figures/fig1 and fig3 .caption.md (full), numbers.json (lines 1-20)
partial docs/brief/H_limits.md:69-71, G_census_dogfood.md:12-14, D_demo_runbook.md:103 (grep)
partial docs/research/2026-10-04_node_key_fusion_audit.md:60-70; 2026-10-02_commerce_guidance_two_pipelines.md:50-60
partial docs/catalog/README.md, actions.md, rollups/rollups.md (grep for value/impact hits)
partial docs/deck/brief_narrative.md, brief_deck_content.md (grep for 24/264/94)
partial corpus/manifest.json (counts_by_decision, included ids)
partial controls.yaml (spend block), seldon.yaml (lines 54-130)
partial kg/spend.py (declare/reserve 305-360)
partial scripts/run_definition_pairs.py (TASK, controls, criterion: grep), run_dcat_extraction.py and run_commerce_extraction.py (grep), build_framework_graph.py (TASK), build_projection.py (360-400), run_kg_questions.py (epoch, 125-145), score.py (grep OECD), build_figures.py (grep)
partial assessment/harness/scan/manners.py (165-260), params.yaml (145-153)
partial tests/test_scan_catalog.py (grep, static value test), tests/test_brief_deck.py (line 46)
partial ~/GitHub/seldon/seldon/commands/cc.py (register_task_file, grep; read-only, outside the audit copy, to check registration enforcement)
Live graph (read-only, run_cypher, gate green): Document count 281; label counts; DCAT doc node and Definition counts.

NOT read
- logs/*: gitignored, absent from the audit copy; gate counts in every RESULT could not be checked (finding A-18). Live-checkout logs were not opened, per the preamble.
- docs/research/2026-10-02_fss_vs_airkg_corpus_reconciliation.md/.csv, commerce glossary CSV, two_pipelines.md (only partially read): the reconciliation counts (35/77/6) and the 48/49 were not re-derived.
- docs/catalog/*.csv, scan_catalog.md in full: catalog row counts (71/64) and set cover were not re-derived (another slice covers the catalog).
- docs/figures PNG/SVG, docs/deck/*.pptx: not opened.
- The FSS graph and icsp_notebook: not queried; the Commerce hash and FSS counts are self-reported.
- events/raw/definition_pairs/*: individual prompts and responses not read; spend totals were checked on the ledger instead.
- 2026-10-05 DCAT-003 task files: outside the date range; skimmed only through the ResearchTask list.
```

### Reader B

```
Slice B reader: files read (all paths repo-relative, read in the audit copy)

docs/evidence/claims.yaml                         full (parsed whole by script, all 86 claims and 4 tables; claim texts, evidence and numbers printed for CL-001..CL-086; every locator resolved by script)
docs/evidence/README.md                           full
docs/evidence/definition_pairs.md                 partial (lines 1-120: set, method, controls, edges, table 1 head; the rest of table 1 not read)
docs/evidence/definition_pairs.csv                full (parsed by script: every column tallied, reasons scanned)
docs/evidence/kg_questions.yaml                   full (parsed by script: grades, reasons, counts, structure, Q3 rows)
docs/evidence/kg_questions.md                     partial (lines 1-60 and the Q3 section; the rest is a rendering of the yaml, checked by --check)
docs/catalog/README.md                            full
docs/catalog/scan_catalog.csv                     full (parsed by script; rows B6, G5 read whole)
docs/catalog/actions.csv                          full (parsed by script)
docs/catalog/actions.md                           partial (lines 1-40)
docs/catalog/enablers.csv                         parsed for row count only; enablers table read via README generated block
docs/catalog/rollups/set_cover.csv, set_cover_uncovered.csv, quick_wins.csv   full
docs/catalog/rollups/rollups.md                   partial (lines with numerals, ~60 lines)
docs/figures/fig1_usafacts_to_framework.caption.md, fig2_system_at_a_glance.caption.md, fig3_pass_fail_table.caption.md   full
docs/figures/layout.yaml                          full
docs/figures/numbers.json                         full (parsed, every entry printed)
docs/figures/fig3_pass_fail_table.csv             full
docs/figures/fig1/fig2/fig3 *.svg                 text content only (the <!-- text --> comments matplotlib writes per text element); glyph paths not read
scripts/build_evidence_map.py                     full
scripts/build_figures.py                          partial (lines 1-130, 200-320, 740-780; caption templates seen by grep around 640-680)
scripts/build_scan_catalog.py                     partial (main 995-1026, set_cover 660-689, line 816)
scripts/run_kg_questions.py                       partial (lines 1-500 and 555-596; render_md body not read)
scripts/run_definition_pairs.py                   partial (prompt/regexes 200-232, load_q1, parse_answer/reason_check 340-380, load_state, main 1096-1211)
scripts/build_brief_pack.py                       grep only (writes, git_out, Sources.record_commit)
tests/test_evidence_map.py                        partial (lines 95-136 and test names)
tests/test_figures.py, tests/test_definition_pairs.py   grep only (test names, parse_answer cases)
framework/ai_readiness_framework.json             parsed by script (nodes, edges, counts, indicator properties for A1, B1, B5, D2, D3, E5, G1-D, G1-O, G3)
corpus/manifest.json                              parsed by script (included entries, provenance_sources)
events/cycle-scan_2026-09-10_rj4.jsonl            lines at every finding locator (by script); lines 334, 418, 807 read
events/batch-*.jsonl                              lines at every document locator (by script)
events/raw/definition_pairs/judgments.jsonl and <unit>.a*.json   the 9 malformed-answer units

Commands run (cwd = audit copy, read-only; logs in scratchpad/B_logs/):
  build_evidence_map.py --check   -> DRIFT, EXIT=1 (only line 2057, CL-046 locator; in-memory render diffed)
  build_figures.py --check        -> DRIFT, EXIT=1 (only fig1 caption; SVG, PNG pixels, CSV, numbers.json re-render identically)
  build_scan_catalog.py --check   -> no drift in 17 files, EXIT=0
  run_kg_questions.py --check     -> no drift, EXIT=0 (epoch unchanged)
  run_definition_pairs.py --check -> 158 pairs, controls positive/negative pass, drift [], EXIT=0
  build_evidence_map.py needs git; the audit copy has no .git, so GIT_DIR pointed at the live repo's .git (read-only, GIT_OPTIONAL_LOCKS=0).
  Neo4j read-only via mcp__ai-readiness-kg__run_cypher (projection_gate green).

Disclosure: before the checks, I diffed claims.yaml and the fig1 caption against `git show HEAD:` in the live checkout (a read outside the audit copy, against the brief) and so saw the two planted differences (B-01, B-02) before the generators' --check reported the same two drifts. Treat those two as found by --check with the control contaminated, not as blind detections. I did not open scripts/plant_audit_controls.py or docs/audit/.

Not read, and why:
  docs/evidence/mcp_health_2026-10-02.md, method_sources.bib, sources.bib   outside the four named evidence files; bib keys not cross-checked
  docs/catalog/catalog_inputs.yaml, front_door.csv, enablers.md, scan_catalog.md (body), rollups/{criterion_by_who,matrix_actions,matrix_scans,staffing_by_cost,unlockers}.csv   covered by build_scan_catalog --check (no drift); not independently recounted beyond the README counts block and quick-win cells
  docs/figures/*.png   binary; covered by --check pixel comparison
  Prior-art quotes (CL-078..CL-086) against corpus text: corpus binaries and bulk_md are not in the audit copy and search_text covers definitions only, so quote fidelity is NOT verified; web citations are not fetched (network not allowed).
```

### Reader C

```
Slice C read log (paths repo-relative, audit copy at HEAD)

IN SLICE, READ
framework/ai_readiness_framework.json  full (parsed programmatically: every node/edge, counts, counts_basis, all properties of indicators, specs, actions; head of file by eye)
scripts/score.py  full
scripts/framework_writeback.py  partial (recount, apply_counts, check, _candidate_ids, lines 1-188; grep for writes)
docs/design/scoring_model.md  partial (lines 59, 79-82; whole page verified by `score.py --check`)
docs/reports/publication.yaml  full
docs/reports/scan_matrix_tierA_2026-09-10_rj4.json  full (parsed)
docs/reports/scan_matrix_product_2026-09-10_rj4.json  full (parsed)
assessment/harness/scan/rules/__init__.py  full
assessment/harness/scan/rules/rule_a1_v4.py  full
assessment/harness/scan/rules/rule_a2_v3.py  full
assessment/harness/scan/rules/rule_a3_v6.py  full
assessment/harness/scan/rules/rule_a4.py  full
assessment/harness/scan/rules/rule_a5_v2.py  full
assessment/harness/scan/rules/rule_a6_v2.py  full
assessment/harness/scan/rules/rule_a9.py  full
assessment/harness/scan/rules/rule_a10_v3.py  full
assessment/harness/scan/rules/rule_a12_v3.py  full (judge) / docstring partial
assessment/harness/scan/rules/rule_b1_v2.py  partial (lines 1-60)
assessment/harness/scan/rules/rule_d1_v3.py  full
assessment/harness/scan/rules/rule_d4_v3.py  full
assessment/harness/scan/rules/rule_f4_v3.py  full
assessment/harness/scan/rules/rule_g4.py  full
assessment/harness/scan/rules/_dcat_fields.py  full
assessment/harness/scan/targets.yaml  full
assessment/harness/scan/manners.py  full
assessment/harness/scan/params.yaml  partial (lines 1-175, 270-330, 355-460, 455-700, 700-960 by grep/section; every numeric scalar key listed)
assessment/harness/scan/stats.py  full
assessment/harness/scan/rederive.py  partial (lines 1-80, grep of reread/control paths)
assessment/harness/scan/reread.py  partial (lines 1-80, grep)
assessment/harness/scan/publish.py  partial (lines 1-120, grep for seldon/neo4j)
assessment/harness/scan/fixture_expectations.py  partial (lines 1-120)
assessment/harness/scan/fixtures/server.py  partial (MODES table by grep)
assessment/harness/scan/collectors/links.py  partial (lines 40-110)

IN SLICE, NOT READ (and why)
assessment/harness/scan/rules/ superseded versions (rule_a1.py, _v2, _v3; rule_a2.py, _v2; rule_a3.py.._v5; rule_a5.py; rule_a6.py; rule_a8.py.._v3; rule_a10.py, _v2; rule_a11_declared.py; rule_a12.py, _v2; rule_b1.py; rule_b3.py, _v2; rule_d1.py, _v2; rule_d4.py, _v2; rule_e5.py; rule_f4.py, _v2): not CURRENT, judge no cell of the cycle of record; only their line counts and the registry entries were checked.
assessment/harness/scan/rules/rule_a8_v4.py, rule_a11_declared_v2.py, rule_b2.py, rule_b3_v3.py, rule_b4.py, rule_b5.py, rule_d2.py, rule_d3.py, rule_e5_v2.py, rule_g1d.py: CURRENT but not read line by line; judged through their rj4 reason strings (tallied per leg from events/cycle-scan_2026-09-10_rj4.jsonl), their MeasurementSpec signals and the e5_control expected_verdicts table. Construct checks on these are therefore from verdict reasons, not from code.
assessment/harness/scan/rules/_common.py, _schema_terms.py: not read; behaviour inferred from callers.
assessment/harness/scan/publish.py lines 120-874, rederive.py lines 80-496: not read beyond grep; time spent on the cycle-of-record verdicts instead.
tests/: not read (brief: grep only). Grepped for every CURRENT rule id and module name; 6 current rules (A2-v3, A6-v2, A9-v1, A11-declared-v2, D1-v3, F4-v3) are named in no test file, but every CURRENT leg is covered by the passes_all/fails_all control fixtures in params.e5_control.expected_verdicts, which the rj4 control_gate recorded as fired; so no "no positive/negative fixture" finding was filed.

OUTSIDE SLICE, READ FOR CHECKS
docs/reports/2026-09_fss_ai_readiness_L0.md  partial (lines 38-48, 56, 74-80, 140-150, 168-196, 306-314, 388-400, 438-450; greps)
docs/brief/G_census_dogfood.md  partial (lines 6-14, 39-58, 115-125)
docs/brief/H_limits.md  partial (lines 69-86)
docs/deck/brief_narrative.md  partial (lines 4, 19-22, 58-62)
docs/deck/brief_deck_content.md  partial (greps)
docs/progress/index.html  partial (lines 50-60)
docs/figures/numbers.json  partial (fig1, fig2 blocks)
docs/figures/fig1_usafacts_to_framework.svg  partial (line 366)
docs/figures/fig3_pass_fail_table.csv  partial (header + 2 rows)
docs/crosswalk/assessment_protocol.md  partial (lines 60-75)
docs/design_decisions.md  partial (lines 530-540; greps)
docs/design/2026-09-22_DN-008_operator_rulings_and_brief_destination.md, docs/design/2026-09-19_DN-007_operator_rulings_and_state.md  partial (greps)
docs/data/sources_per_check.json  partial (lines 234-258 by grep)
state/scan_2026-09-10.json  partial (parsed: requests_per_host, observations_detail for A2/link probes/page links)
state/scan_2026-09-10_rj4.json  partial (parsed: rules, control_gate, observations_reread)
state/scan_targets_fss_2026-09_v5.json  partial (grep parent_department)
events/cycle-scan_2026-09-10_rj4.jsonl  partial (parsed: finding_derived reasons per leg; DRSMSU D4/G4; BLS/BTS/ORES A4/A12)
events/batch-029.jsonl and events/*.jsonl  partial (observation_recorded for robots.txt of BLS/BTS/SSA/statcan/catalog.data.gov, statcan /llms.txt, obs_5039cd5646be4ca314a8528d)
corpus/evidence/scan/32/32e1fef18221e126e30843bdb2828a98114e9d62deb6e0bc69d422d1d2e3f743 (StatCan robots.txt)  full
corpus/evidence/scan/8c/8c5ed3bd234a802efe10349b17749c514dd58315d5b7c1a8197cd589af93517d (catalog.data.gov robots.txt)  partial (lines 1-3)
scripts/prescriptions.py, scripts/tag_prescriptions.py, assessment/harness/scan/spot.py  partial (grep for writes/network, to confirm score.py is read-only before running it)

COMMANDS RUN (read-only, cwd = audit copy)
scripts/score.py; scripts/score.py --sensitivity; scripts/score.py --json; scripts/score.py --check (exit 0, "is the generated page"); ad-hoc Python recomputation of counts, weights, A9-excluded scores and DRSMSU joint reversal via score.score_body; protego parse of retained robots.txt bodies. Neo4j not queried (the record and the matrices are the sources of truth for this slice).
```

### Reader D

```
Slice D reader log (paths repo-relative, audit copy at HEAD a5b5134f)

ASSIGNED FILES
kg/schema.yaml — partial: lines 1-70 (header, changelog, schema_version 0.4.0), 300-335 (asserts..operationalized_by); node_types and edge_types parsed in full by script (keys and pairs).
docs/schema_v0.1.md — full (140 lines; long changelog lines read truncated at 400 chars).
scripts/build_projection.py — full (1,048 lines).
kg/eventlog.py — full.
kg/extraction/grounding.py — full.
kg/extraction/parser.py — full.
kg/extraction/pipeline.py — full.
docs/research/2026-10-04_node_key_fusion_audit.md — partial: lines 1-200 (prose, G1-G7, start of G8) and 380-413 (end of G9); the middle of the G8/G9 generated tables skimmed via the CSV instead.
cc_tasks/2026-10-04_node_key_fusion_audit_RESULT.md — full.
events/ — shape only: file listing and sizes (63 shards + raw/), event-type tally over all shards by script, stamp/duplicate-id check by script; single lines read: batch-001.jsonl:84, :99; batch-003.jsonl:1; batch-004.jsonl:1349 (prefix); batch-043.jsonl:1. No shard read whole.

OTHER FILES READ TO CHECK CLAIMS
kg/extraction/state.py — partial (assert_item, lines 81-92).
scripts/chunked_pilot.py — partial (lines 640-730, ingest path).
scripts/run_definition_pairs.py — partial (lines 740-790, cross-document edge writer).
scripts/assert_noaa_definition.py — full.
scripts/audit_node_key_fusion.py — partial (lines 1-30 docstring grep, 95-250, 328-346, 617-643); executed --check read-only and its functions imported into scratch scripts.
scripts/run_kg_questions.py — partial (lines 150-230).
tests/test_extraction_grounding.py — full.
tests/test_cypher_unlabelled_lint.py — partial (lines 1-80).
tests/test_build_projection.py — partial (lines 1-80); test names listed.
tests/test_build_projection_filters.py — partial (lines 40-52); test names listed.
tests/test_extraction_pipeline.py, tests/test_extraction_parser.py — test names only (grep def test_).
tests/test_node_key_fusion_audit.py — partial (grep of test names and --check lines).
cc_tasks/2026-10-02_kg_research_questions_RESULT.md — partial (lines 1-60).
cc_tasks/2026-10-04_full_audit.md — line 21 only (known list).
docs/evidence/kg_questions.md — partial (lines 1-30; grep for 19/29/fusion).
docs/design_decisions.md — partial (DD-024 lines 219-232).
docs/research/kg_construction_methodology.md — line 43 only (grep).
dixie_evidence.yaml — grep for enforce_span_coverage only.
corpus/manifest.json — parsed by script (screening.decision counts and doc ids).
docs/research/2026-10-04_node_key_fusion_audit.csv — parsed by script (keys and classes).
reports/dcat_us_3_faq/evidence/Q12.json — partial (lines 540-560, 775-810) and evidence-kind tally by script; other evidence files only key-scanned by script.

LIVE GRAPH (read-only Cypher via MCP): label counts, rel counts by type, unlabelled nodes, ASSERTS endpoint labels, label-twin duplicated edges, Definitions without DEFINES, grounding_thin count, semantic-edge property keys, cross-document CONFLICTS_WITH spans, 8 Document content hashes, scan-eia-flagship-1-open-data.

SCRATCH SCRIPTS (findings/ directory, mine): D_replay.py (+ D_replay_out.json), D_spans.py, D_semantic.py, D_twins.py, D_scan_keys.py, D_fusion_block_now.md (audit render at HEAD), D_content_update.json, D_write.py.

IN SLICE, NOT READ
events/ shard contents beyond the lines above — brief says shape only; all content checks were by script.
events/raw/ — not read (provenance blobs; outside the counts checked).
kg/extraction/model_stub.py, model_config.yaml — not in the assigned list; the "different model => STOP" half of the provenance invariant was therefore not checked.
kg/manifest.py — only grepped (empty/required checks); the manifest gate belongs to the corpus slice.
corpus text (bulk_md etc.) — gitignored, absent from the audit copy; so NFKC acceptance could be demonstrated but not counted on real spans, and curated_promotion spans were not re-grounded.
```

### Reader E

```
E_read.txt — slice E (the test suite as evidence). Static analysis only; the suite was NOT run and pytest collection was NOT run.

== COUNTS (tests/ only; test FUNCTIONS by AST, before parametrisation expansion) ==
test files: 124 (tests/test_*.py), 35,495 lines incl. conftest; test functions: 1,876
no assertion of any kind (no assert / pytest.raises|warns|fail / self.assert* / asserting helper in file, conftest, tests/support or imported test modules): 3
  tests/test_extraction_model_stub.py:49 test_guard_passes_without_credentials (does-not-raise test)
  tests/test_extraction_schema_pairs.py:155 test_extraction_schema_pairs_payload_round_trip_is_stable (bare `reread == payload`, E-12)
  tests/test_leg_rate_names.py:87 test_a_prefixed_name_is_accepted (does-not-raise test)
every assertion inside a loop/if (no unconditional assertion): 169; of these 36 loop over a literal, 36 have a non-emptiness/count assert on the iterable elsewhere in the file, 96 have none (heuristic; many are module constants and safe; data-record ones e.g. test_prescriptions `acts` x14, test_requirements inds/reqs, test_kg_questions doc['questions'] x4, test_definition_pairs shipped_rows, test_evidence_map on_disk)
tautological: self-equal asserts 3 (test_cq_collapse.py:120, test_rule_a12_v3.py:380 real; test_brief_pack.py:67 is two render calls, legitimate); assert-on-constant 0; only-`is not None` 1 (test_mcp_server.py:117, acceptable: refusal returns a message); assert all(...) over a generator 55 sites (vacuous on empty; not individually triaged)

== SKIP / XFAIL INVENTORY: 98 static sites + 1 named skipif alias (test_dispatch_config.py:326 interactive_only) + 2 parametrised strict-xfail generators (test_invariants.py:161 UNDER_V5, 3 cycles; :312 absence, 5 cycles) ==
by condition: build_artifact_or_git_history_absent 38, neo4j 35, live_state_or_design 10, gitignored_binary 8, optional_import 4, seldon_checkout 3
Neo4j: 35 sites; 27 are a broad `except Exception` -> pytest.skip (any error, not only unreachable, becomes a skip; E-01/E-02). Static propagation through fixtures: ~123 test functions in 29 files depend on Neo4j and skip without it.
hard-coded /Users/brock/GitHub/seldon: 25 test files; ~64 test functions reach it (heuristic). Without that checkout most degrade to the Neo4j skip with a misleading reason; test_cadence_template.py imports it at module level (collection error, E-03).
git history: ~37 test functions use git log/show (re-derivation, prior_params); in a tree without .git the re-derivation tests FAIL (test_scan_harness_v4.py:182) while test_invariants.py:108 SKIPS (E-16).
gitignored corpus binaries/substrate: 8 sites — test_commerce_guidance_admission.py:91, test_dcat_faq.py:36, test_dcat_us_3_intake.py:155,169, test_g4_locators_and_progress_drift.py:180, test_scan_catalog.py:417,427, test_v037_contract.py:444. A stranger's clone silently tests less here.
optional imports: pypdf (test_report_pdf.py:96, test_snapshot_successor.py:165), rdflib+pyshacl (test_shacl_gate.py:13-14: whole module, 9 tests). None of these is declared in pyproject.toml.
module xfail(run=False): test_brief_deck.py:46, 23 tests never executed (E-17). Strict xfails that DO run and pin known defects: 8 parametrised cases in test_invariants.py, each paired with an exact-count test.
live-state / design skips (10): test_brief_deck.py:46; test_brief_pack.py:103 (mmdc absent); test_bulk_v038.py:1321 (no batch-stamped events); test_dispatch_config.py:373 (dispatcher not quiet); test_framework_single_writer.py:477 (commit bb660f9 unreadable, i.e. shallow clone); test_kg_questions.py:115 (epoch moved, E-15); test_publication.py:586; test_report_traceability.py:158 (ALLOW_ZERO_SOURCES); test_resnapshot_rj4.py:151 (cycle of record moved); test_scan_harness.py:283 (E5 by design).
skips that guard a named incident: test_framework_projection_roundtrip.py:59 (DD-057 stale-projection incident 2026-09-07), test_standing_guards.py:294 graph half (DN-003 decision 6), test_snapshot_successor.py:74/82/164/358 (DN-004), test_guards_replay_their_incidents.py:439 (cycle-4 payload; committed, so it does not fire in a clone), test_dispatch_config.py:268/334/373 (DN-006 decision 7).
markers: pyproject declares live_plan and slow. Only test_bulk_v038.py:1302 is live_plan and no Makefile target deselects it. slow: test_adopter_path.py:494, test_scan_run_2.py:197/240/307, test_virtual_time.py:144, test_scan_harness_v4.py:716, plus every re-derivation case outside RECENT_CYCLES. gate-fast = -m 'not slow' over tests/ and assessment/; gate-task = gate-fast + -k re_derives in test_scan_harness_v4.py (runs all 23 PRIOR_CYCLES); guards = 4 files (E-10); gate-full = detached full run of tests/ and assessment/.

== GUARDS vs SEEDED-DEFECT (MUTATION) TESTS ==
single-writer (framework_writeback): YES — test_framework_single_writer.py:138 planted writer shapes, :248 the incident itself, :465 two historical writers (skips in a shallow clone).
projection round-trip (DD-057): NO seeded-stale test for test_framework_projection_roundtrip.py or MCP projection_gate (E-05); MCP gate ignores edges (E-06).
grounding (parse time, invariant 3): YES — test_extraction_parser.py:74,125,135,171,180 and test_extraction_grounding.py:31,55. grounding_zero_ungrounded gate (run_baseline_gates.check_grounding): NO, only monkeypatched (E-07).
spend guard (DD-022): YES — test_spend_guard.py:82,164,192,231 (22M incident replay),350 (mutation).
model gate ANTHROPIC_API_KEY (DD-007): YES — test_extraction_model_stub.py:37,42. Model substitution: YES at invoke (test_extraction_model_stub.py:162); NO at any driver (E-18).
harness owns provenance: YES — test_extraction_pipeline.py:107,189.
event-log write guard (conftest): YES — test_extraction_queue.py:292. seldon_events.jsonl: not guarded (E-09).
fetch allowlist: YES — test_fetch_allowlisted.py:88,140.
dispatch header rules (Spend/Network/Framework layer served, network_undeclared, SUPERSEDED marker): enforced in the Seldon repo; this suite only checks CLAUDE.md carries the words (test_dispatch_config.py:117) and that a refusal-class name list exists (:394). The Seldon repo was not in the audit copy, so not checked.
'era purity': no guard by that name anywhere in the audit copy (grep -rIl -i 'era.purity|era_purity|epoch_purity' empty). The closest documented guard, the kernel-epoch `faithfulness_epoch` flag, has no implementation at all (E-08).
standing guards (DN-003/DN-004): YES — test_standing_guards.py:195,219,232 red-by-subtraction replays against the committed log.

== TESTS THAT READ LIVE STATE (machine-dependent, not just committed-tree dependent) ==
Neo4j graph: ~123 functions / 29 files (see above). Live dispatcher/seldon CLI: test_dispatch_config.py:256 (/opt/anaconda3/bin/seldon), :270, :336 (E-09). Committed-but-mutable record (events/, state/, framework JSON, docs/): ~76 functions read the real event log by heuristic (tests/test_standing_guards.py, test_rejudgements_on_the_log.py, test_scan_run_2.py, test_resnapshot_rj4.py, test_bulk_v038.py:1303 ...) — these depend on the committed tree, so they are reproducible from a clone, but they test the record, not the code.

== FILES READ ==
full: findings/PREAMBLE.md
full: tests/conftest.py (221 lines)
full: Makefile
full: tests/test_framework_projection_roundtrip.py
full: tests/support/prior_params.py; partial: tests/support/sourcescan.py (lines 1-100 = whole file)
full (machine-read): every tests/test_*.py (124 files), parsed with Python ast by E_work/scan.py, cond.py, loops.py, guardne.py, live.py, exc.py: test defs, asserts, skip/xfail/importorskip calls and decorators, broad excepts, top-level imports, loop iterables
partial: pyproject.toml (1-40, whole file)
partial: tests/test_extraction_model_stub.py 30-60, 66-76, 120-163; tests/test_extraction_schema_pairs.py 140-162; tests/test_leg_rate_names.py 70-91
partial: tests/test_scan_harness_v4.py 54-130, 145-186, 235-265, 660-760; tests/test_scan_harness_v3.py 210-235; tests/test_scan_run_2.py 265-280; tests/test_score.py 210-230; tests/test_report_figures_agree.py 29-95
partial: tests/test_requirements.py, test_prescriptions.py, test_scan_catalog.py, test_kg_questions.py, test_score.py, test_definition_pairs.py, test_evidence_map.py, test_measurement_tiers.py, test_framework_graph.py — fixtures only (AST)
partial: tests/test_kg_questions.py 1-30, 95-120 (whole file effectively); tests/test_resnapshot_rj4.py 140-160; tests/test_dispatch_config.py 20-35, 115-135, 170-385; tests/test_bulk_v038.py 1310-1330
partial: tests/test_standing_guards.py 150-300; tests/test_invariants.py 95-112, 161-191, 312-335; tests/test_mcp_server.py 110-125, 215-235, 585-600; tests/test_projection_at_burn_close.py 105-135
partial: tests/test_brief_pack.py 54-70; tests/test_cq_collapse.py 110-125; tests/test_rule_a12_v3.py 360-400; tests/test_figure_registration.py 155-165; tests/test_scan_figures.py 115-126; tests/test_shacl_gate.py 1-30; tests/test_cadence_template.py 30-50; tests/test_framework_single_writer.py 150-170; tests/test_node_key_fusion_audit.py 110-125; tests/test_fixture_epoch_exclusion.py 1-40; tests/test_tevv_gates.py (grep); tests/test_extraction_parser.py (grep of test names)
partial: cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips.md 1-60 (whole decision block); cc_tasks/2026-09-14_standing_guards_RESULT.md 280-290
partial: mcp/airkg_tools.py 450-505; assessment/harness/scan/figures.py 100-130; scripts/register_scan_figures.py 149-175; scripts/run_baseline_gates.py 39-50, 105-160; scripts/batch_repair.py 1-30, 245-262, 305-315; scripts/overnight_burn.py 362-378; scripts/run_bulk_extraction.py 460-475; kg/extraction/model_stub.py 385-425; scripts/admit_dcat_us_3.py 50-62; scripts/build_projection.py (imports)
partial: docs/design_decisions.md:225 and docs/research/kg_construction_methodology.md:43 (the faithfulness_epoch sentences); docs/adopt/run_on_your_site.md (grep of dependency lines); .zenodo.json; .github/secret_scanning.yml (full); CITATION.cff (grep)
data checks: events/batch-012.jsonl (all lines, model ids counted); state/scan_2026-09-07_controls.json, state/scan_2026-09-07b_controls.json, state/self_l0_self_2026-09-13.json (key counts); state/ listing
graph (read-only Cypher via MCP): count of relationships with faithfulness_epoch (0); semantic edge types, keys and prov_method counts

== NOT READ, AND WHY ==
assessment/tests/ (24 files, 316 test defs): outside slice E's stated scope (tests/), though gate-fast and gate-full run them; not analysed.
Bodies of most of the 124 test files beyond the AST pass: each test's assertion semantics were not hand-checked; only flagged tests and fixtures were read.
The Seldon repository (/Users/brock/GitHub/seldon), where the dispatch header rules and the fail-not-skip Neo4j fixture live: not in the audit copy.
The 55 `assert all(...)` sites and most of the 96 unguarded loop tests: counted, not triaged one by one.
```

### Reader F

```
Slice F (operationalization) — read log. Paths repo-relative to the audit copy unless absolute.

READ IN FULL
full    findings/PREAMBLE.md
full    docs/adopt/run_on_your_site.md (173 lines)
full    tests/test_adopter_path.py (543 lines)
full    assessment/harness/scan/adopt.py (307 lines)
full    assessment/harness/scan/run.py (880 lines)
full    scripts/install_schedule.py (192 lines)
full    pyproject.toml
full    Makefile
full    .gitignore
full    README.md (66 lines)
full    assessment/harness/scan/collectors/lighthouse.py
full    .mcp.json

READ IN PART
partial assessment/harness/scan/manners.py: lines 1-140 (robots_access, Fetcher init, rate limiter, start of _robots_for)
partial assessment/harness/scan/publish.py: lines 20-60 (header, sys.path), 221-240 (_log_index), 558-610 (project()), 831-874 (main); function map by grep
partial assessment/harness/scan/rederive.py: grep map of functions/args, lines 450-477 context
partial assessment/harness/scan/params.yaml: lines 128-160 (manners), 395-410 (a10), 715-735 (link probe), 961-973 (schedule)
partial assessment/harness/scan/frames/fss16.yaml: lines 1-40 (whole file content shown)
partial assessment/harness/scan/runner.py, collectors/*, rules/*, model.py, spot.py, __init__.py, figures.py: import/grep scans only (AST import closure, hard-coded path grep); rule_a10*.py grep for renderer/error handling
partial scripts/render_run_report.py, scripts/score.py, scripts/prescriptions.py: import/sys.path grep only
partial scripts/build_projection.py: lines 260-295 (_neo4j_creds, _database), 940-1000 (project_assessment), grep for seldon/NEO4J/database
partial scripts/seldon_artifacts.py: lines 30-45
partial scripts/fetch_allowlisted.py: lines 1-80, grep for paths/UA
partial scripts/jobs/*: grep for /Users/brock, /opt/anaconda3, wintermute
partial scripts/build_*targets*.py: grep only (for the 712755f8 overlap check)
partial mcp/airkg_tools.py: lines 40-60, 1310-1340, import grep
partial mcp/airkg_server.py, mcp/airkg_doc.py, mcp/airkg_guard.py: grep for hard-coded paths/database
partial seldon.yaml: lines 1-80, grep rest
partial controls.yaml: grep for machine-local values only
partial CLAUDE.md: already in context (project instructions); lines 18 and 52 checked against code
partial kg/extraction/model_config.yaml: lines 1-25
partial kg/extraction/model_stub.py: grep for forbidden env (lines 2-50)
partial corpus/manifest.json: parsed programmatically (entry shape; counted corpus/ path strings and their presence)
partial cc_tasks/2026-10-04_full_audit.md: lines 1-14 (headers)
partial cc_tasks/2026-09-19_adopter_path.md and _RESULT.md: grep for fresh/clone/stranger/venv
partial seldon_events.jsonl: grep for 712755f8, fa40072e, 1267b87d, full_audit, dispatch_launched
partial tests/*.py, assessment/tests/*.py: grep only (seldon/dixie imports, /Users/brock and /opt/anaconda3 paths, gitignored input paths)
partial docs/design/2026-09-22_DN-008_operator_rulings_and_brief_destination.md: line 12 (checkpoint scope)

OUTSIDE THE AUDIT COPY (read-only)
partial /Users/brock/GitHub/seldon/seldon/core/dispatch.py: lines 75-91, 320-445, 880-945 (K11); functions spend_tokens/parse_headers/parse_network called on literal strings
partial /Users/brock/GitHub/seldon/seldon/config.py: lines 70-103 (credential resolver, driver)
partial /Users/brock/GitHub/seldon/seldon/commands/cc.py: lines 621-654, 1077-1165 (grep within)
partial /Users/brock/GitHub/seldon git log / git show --stat d9ad7d3 (read-only)
ls only /Users/brock/GitHub/ai-readiness-kg: checked which gitignored paths exist (.env, .seldon, handoffs, corpus/bulk, corpus/bulk_md, corpus/kernel, corpus/pilot, state/corpus_index.db, state/evidence_staging present; .venv, .claude, out absent). .env contents NOT read.
partial /Users/brock/GitHub/ai-readiness-kg/logs/adopt_runbook.log: first 3 header lines only (start/finish times, 676.7 s, exit 0). This goes past the brief's "ls only" for the live checkout; disclosed here; nothing else in it was read.
graph   live Neo4j (read-only Cypher): states of 712755f8, fa40072e, 1267b87d; count of open ResearchTasks by source_file null

PROBES RUN (read-only, scratch dir f_probe/)
- AST import scan of every .py; transitive import closure from nine adopter entry points
- compile() of assessment/harness/scan, scripts, mcp, kg under python3.10 and 3.11: 0 syntax errors (so the runbook's "Python 3.12" is not a hard floor; no finding)
- setuptools FlatLayoutPackageFinder.find on the copy (11 top-level packages)
- adopt.load_frame/compile_rows/check_identity on a scratch mixed-host frame (F-09); no network
- seldon dispatch parsers on literal strings (K11)

NOT READ, AND WHY
- assessment/harness/scan/manners.py lines 140-408: the robots and rate-limit logic is slice-adjacent; I checked only what an adopter depends on (identity, rate, timeouts)
- collectors/*.py bodies other than lighthouse.py: checked for third-party imports and external binaries only; collector correctness is another slice
- scripts/score.py, render_run_report.py, rederive.py bodies: the gate runs them in step 5 and its log reports exit 0; I checked their dependencies, not their logic
- the rest of mcp/airkg_tools.py and airkg_server.py: MCP verb logic is another slice
- scripts/build_projection.py except the parts named: projection correctness is another slice
- scripts/jobs/ in full: grep was enough to show the hard-coded paths; these are the author's own jobs, not on the adopter path
- the live logs/adopt_runbook.log beyond its header: outside the brief's live-checkout permission
- `seldon dispatch status`: not run, because it may append events; the graph count was used instead
- the GitHub clone URL: not checkable offline (F-03 is marked self-report only)

MODULAR-ROSTER RECORD 712755f8 (ResearchTask, proposed; seldon_events.jsonl line 37048)
Description: make the scan roster fully modular (population statement, cohort tiers hardcoded in build_*_targets.py, self-targets in a per-site config shape; "a new site is one file dropped in a directory"; any host; 18F domain-scan / pa11y-ci / Lighthouse CI / HTTP Observatory as the pattern; after the summary ships).
Overlap with my items: it covers NONE of F-01..F-21 directly. It concerns how THIS project's own frame (fss16, target DataFile, tiers in build scripts) is assembled. The adopter path already has the "one file per site" shape it asks for (a declared frame, adopt.py), so it is partly done for adopters already. The nearest overlaps: F-08 (identity and schedule live in the shared params.yaml, not in the per-site file 712755f8 envisions; a modular roster that carried per-site identity/schedule would close F-08), and F-09 (if each site file named its hosts, the identity guard could check every host the file names). Dependency packaging, hard-coded paths, checkpointing, Seldon/Neo4j setup and corpus re-acquisition are not in its scope.
```

### Reader R2

```
R2 audit: files read (all inside audit_copy_r2, read-only; no git, network, Neo4j or model calls)

Read in full or parsed by script:
- docs/evidence/claims.yaml (all 86 claims, the evidence entries, the numbers lists, and tables q1/q2/q5)
- framework/ai_readiness_framework.json (nodes, edges, counts, counts_basis)
- docs/figures/fig1_usafacts_to_framework.caption.md, fig2_system_at_a_glance.caption.md, fig3_pass_fail_table.caption.md
- docs/figures/numbers.json, docs/figures/layout.yaml, docs/figures/fig3_pass_fail_table.csv
- docs/figures/fig1/fig2/fig3 .svg (text comments only; the glyphs are drawn as paths)
- corpus/manifest.json (screening.decision counts)
- scripts/build_evidence_map.py (all of it)
- scripts/build_figures.py (docstring, compute, Ledger, captions, CSV, render, main)
- mcp/airkg_tools.py (get_requirements, _requirement_view, _edge_view, _no_requirement_reason)
- scripts/report_traceability.py (the locators() function and the module-level statements; not imported, because it puts a path outside R2 on sys.path)
- scripts/build_brief_pack.py (imports, git_out, graph_or_none, the module-level statements)
- scripts/score.py, scripts/prescriptions.py, scripts/framework_writeback.py (import lines only)
- assessment/harness/scan/rules/__init__.py (CURRENT; the module was imported to read the registry)

Run:
- scripts/build_figures.py --check (python -B, MPLCONFIGDIR in the scratchpad). Output: "DRIFT: fig1_usafacts_to_framework.caption.md: bytes differ", EXIT=1. An md5 snapshot of every R2 file before and after the run shows no change.
- An in-memory render through build_figures.render(), to diff the regenerated files. Only the fig1 caption differs.
- NOT run: scripts/build_evidence_map.py --check. It connects to Neo4j (graph_or_none(required=True)) and calls git (framework_start, Sources.record_commit), and the brief forbids both.

Side effect, disclosed: an early `import scan.rules` without -B created assessment/harness/scan/__pycache__ and assessment/harness/scan/rules/__pycache__ in R2 (born 22:30:42). I removed both directories at once; they did not exist before. No source file was touched.
```
