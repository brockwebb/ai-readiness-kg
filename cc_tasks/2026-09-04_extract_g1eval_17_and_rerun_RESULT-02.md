# RESULT-02: Diagnostic and CQ rerun after the g1eval extraction

**Task:** `cc_tasks/2026-09-04_extract_g1eval_17_and_rerun.md` §2–§5, resumed under **ADDENDUM-01** (AMENDS, resume at §2) and **ADDENDUM-02** (adds §3a). Both globbed and read before starting; both committed before execution (`d547066`, `982a646`). **Date:** 2026-09-04/05 UTC. **Spend: zero model calls in this leg** — the extraction is §1 of the first RESULT and is not repeated here.

**Two things happened that the task did not anticipate, and they are the first two sections for that reason.**

1. **The 17 extracted cleanly and still had no edges.** The gap diagnostic came back `run_ok_no_edges` = **17**, the class §1.4 says must stay zero. The extraction was not at fault: the projection was, in a way that had been latent since documents began being admitted after their extraction shard. Two loader defects, both fixed, both with a regression test written first.
2. **The pre-registered §1.5 rule fired a different branch.** `flip` moved 0.269 → **0.308**, over the 0.30 threshold: **entity resolution is P0 and blocks probe design**, where the first run put it in the middle branch. The branch is reported here and the decision is Desktop's.

## 0. Resume verification (ADDENDUM-01 §0)

No `extraction_request` was re-emitted, nothing was re-extracted, and the spend ledger was read and never written. `kg.queue.project()` reports all 17 `extracted` at full chunk coverage. The three spend figures ADDENDUM-01 §1 asks for are registered as Results: `g1eval_extraction_tokens_declared` 13,280,000, `g1eval_extraction_tokens_productive` 31,299,448, `g1eval_extraction_tokens_wasted` 15,073,098 — Script `run_g1eval_extraction`, DataFile `spend_ledger_2026-09-04_g1eval`.

## 1. The projection lost every document-anchored edge

### 1.1 What was wrong

`scripts/build_projection.py` merges an edge endpoint with `MERGE (a {key: $from_id})` and a document with `MERGE (d:Document {id: $id})` — **two different patterns for the same node**, so whichever runs first decides whether the document ends up labelled. Shards replay in batch order. The 17 were extracted into the *open* bulk shard `batch-023` while their `manifest_add` sits in `batch-025` (admitted 2026-09-02), so every `ASSERTS`/`MENTIONS`/`DEFINES`/`CITES` edge reached the `MERGE` before anything carried that key, created an **unlabelled twin**, and left the real `Document` node at degree zero:

```
key='min-2023-factscore', labels=[]          degree 293
key='min-2023-factscore', labels=[Document]  degree 0
```

This is not a defect of this extraction. It fires for **any** document whose extraction lands in a lower-numbered shard than its admission, and it is silent: the ingest reports its 7,643 edges, the replay reports its counts, and only a query for edges *from the Document node* shows the loss.

**Fix:** merge the `Document` skeletons from the pre-pass that already computes `document_ids`, before the event loop. Commit `1977a89`; regression test `test_a_document_manifested_after_its_extraction_still_owns_its_edges` fails on the old ordering with `assert 2 < 1`.

### 1.2 The second defect, found by the first fix

With the skeletons in place, `min-2023-factscore`'s Document node picked up its 290 edges **and the twin from the previous replay still had 296** — Cypher's `MERGE` binds *every* node matching `{key: ...}`, so both got the edge. The reset was deleting only KG-**labelled** nodes, so every unlabelled endpoint the projection creates had survived every replay since the projection was written: 4,332 key-scoped endpoints, the 17 twins, and **1,201 degree-zero nodes carrying only an `id`** — the endpoint shape of an older keying scheme, still sitting in a graph whose whole contract is that it is a disposable replay of the log. `nodes_total` counted them.

**Fix:** the reset also clears unlabelled nodes; everything it deletes is recreated by the replay if the log still asserts it, and Seldon's own artifacts all carry labels. Commit `e5d6d33`, regression test written first. After the third replay: **0 degree-zero unlabelled nodes**, and `documents_with_edges` = 156, up from 139 by exactly the 17.

### 1.3 §1.4's condition, met

`state/extraction_gap_2026-09-04b.json` (DataFile, snapshot) → 19 Results `kg_diag_gap_*_2026-09-04b`, registered by the new `scripts/register_gap_results.py` — written because the first run's 16 gap Results came from an ad-hoc command with no reproducible path, which is the DD-040 defect in miniature.

| class | before | after |
|---|---:|---:|
| `never_queued` | 17 | **22** |
| `run_ok_no_edges` | 0 | **0** |
| `queued_not_run` · `run_failed` · `source_missing` | 0 | 0 |
| `excluded_by_design` | 55 | 55 |
| **gap documents** | 72 (of 211 nodes) | **77** (of 233 nodes) |

**`run_ok_no_edges` reads 0 and the `g1eval` epoch is out of `never_queued` entirely.** The condition is met, but *not* in the form the task predicted: `never_queued` reads **22, not 0**, and nothing about the 17 explains it. The 22 are the fixture-epoch documents of Issue `2e226acb` — `g1sfc-2026-09-03` (17 product surfaces), `g1srp-2026-09-03` (4 producer rules), `g1dp-2026-09-02` (1 handbook). They had no `Document` node when that Issue was written, because the graph predated their admission; the replay gave them one, so `manifest_documents_without_a_document_node` is now **0** and they appear in the gap classification instead. **The Issue's premise has moved and its question has not**: whether an eval fixture should be a Document node at all is still open, and is still out of scope (§7).

## 2. Diagnostic delta (task §2)

`state/kg_snapshot_2026-09-04b.json` (DataFile, snapshot) → **52 Results** named `kg_diag_<metric>_2026-09-04b`, the DD-041 rerun convention. The un-suffixed names stay bound to the pre-extraction run.

**Every scalar figure, before and after:**

| figure | before | after | delta |
|---|---:|---:|---:|
| nodes, all labels | 27,231 | 32,204 | +4,973 |
| Concept | 8,662 | 10,637 | +1,975 |
| Claim | 4,509 | 6,213 | +1,704 |
| Document | 211 | 233 | +22 |
| duplicate-name Concept groups | 1,122 | 1,387 | +265 |
| Concept nodes inside a duplicate group | 3,479 | 4,343 | +864 |
| share of Concepts duplicated | 0.401639 | 0.408292 | +0.0067 |
| nodes named `AI readiness` | 14 | 14 | +0 |
| in-edges on them | 44 | 44 | +0 |
| Concept degree, median | 1 | 1 | +0 |
| Concept degree, max | 26 | 26 | +0 |
| Concepts at degree 1 | 4,246 | 5,249 | +1,003 |
| isolated Concepts | 617 | 761 | +144 |
| Concepts at degree >= 5 | 398 | 484 | +86 |
| domain edges (no Artifact endpoint) | 25,227 | 32,096 | +6,869 |
| domain edges (both endpoints KG-labelled) | 22,141 | 27,785 | +5,644 |
| edges, all | 32,335 | 39,738 | +7,403 |
| Document CITES Document | 28 | 35 | +7 |
| Claim CONFLICTS_WITH Claim | 3 | 5 | +2 |
| Definition CONFLICTS_WITH | 1 | 2 | +1 |
| Claims with no ASSERTS source | 50 | 55 | +5 |
| Documents with no extraction edges | 72 | 77 | +5 |
| extractions per Document, median | 30 | 34 | +4 |
| Concepts carrying doc_id | 8,662 | 10,637 | +1,975 |
| Concepts carrying a grounding span | 8,662 | 10,637 | +1,975 |
| Concepts carrying aliases | 8,129 | 10,104 | +1,975 |
| Documents carrying content_hash | 211 | 233 | +22 |
| Documents carrying prov_source_sha256 | 0 | 0 | +0 |
| Documents with extraction edges | 139 | 156 | +17 |

**Node labels:**

| label | before | after | delta |
|---|---:|---:|---:|
| Concept | 8,662 | 10,637 | +1,975 |
| Claim | 4,509 | 6,213 | +1,704 |
| Definition | 1,567 | 1,895 | +328 |
| Measure | 1,173 | 1,352 | +179 |
| Practice | 973 | 1,087 | +114 |
| Standard | 801 | 813 | +12 |
| Instrument | 354 | 483 | +129 |
| Framework | 410 | 453 | +43 |
| Platform | 212 | 303 | +91 |
| Tool | 183 | 245 | +62 |
| Document | 211 | 233 | +22 |

**Reading the delta.** The corpus grew by 1,975 Concepts and 1,704 Claims from 17 documents — roughly a fifth of the Concept count from a fourteenth of the corpus, because the uncertainty literature is dense in exactly the vocabulary the schema captures. Three figures are worth separating from the growth:

- **`Document` +22 is not this extraction.** It is the fixture epochs acquiring nodes at the replay (§1.3). The 17 already had Document nodes.
- **`documents_without_extractions` went 72 → 77**, which reads backwards until the composition is written out: −17 (extracted) +22 (fixtures that had no node to be counted against before).
- **Duplication got worse in absolute terms and barely moved in proportion**: duplicate groups 1,122 → 1,387, duplicated share 0.402 → 0.408. New documents bring new duplicates at about the rate the graph already had, which is what DD-020 predicts — the loader keys `<doc_id>::<item_id>` and cross-document identity is dedup's job, still not run.
- **`AI readiness` is unmoved at 14 nodes / 44 in-edges**, and `concept_degree_max` at 26. The 17 are uncertainty-and-summarisation prior art; they say nothing about AI readiness as a term, which is exactly what the §3a harvest independently confirms about where that term lives.

## 3. CQ v1 rerun — same set, no edits (task §3)

**The set is byte-identical to commit `369d717`** (`git diff 369d717 -- assessment/cq/cq_set_v1.yaml` is empty; sha256 `a253cede…`). No question, no Cypher and **no pass criterion was touched**, before or after seeing an answer. New dated artifacts throughout: `assessment/results/cq_v1_2026-09-04b.jsonl` (DataFile, snapshot), the aggregates JSON, the report `docs/research/2026-09-04b_cq_coverage_v1.md`, and **200 Results** named `cq_v1_*_2026-09-04b` — the suffix added to `register_cq_results.py` this session, because its Result names carried no date and a rerun would have overwritten the first run's registered measurement, which §1.6 forbids.

### 3.1 The four aggregates and the rule

| aggregate | before | after |
|---|---:|---:|
| `A_raw` | 0.808 (21/26) | **0.885 (23/26)** |
| `A_collapsed` | 0.769 (20/26) | **0.846 (22/26)** |
| **`flip`** | **0.269** (7/26) | **0.308** (8/26) |
| `C` (duplicate groups unioned) | 98 | **121** |
| raw answers flagged misleading | 8 | 9 |

**Pre-registered rule (§1.5, unchanged): `flip ≥ 0.30` → entity resolution is P0 and blocks probe design; `flip < 0.10` → deferred; otherwise scheduled but not blocking.**

**Branch that fired: `flip` = 0.308 ≥ 0.30 → ER is P0 and BLOCKS probe design.** The first run fired the middle branch at 0.269. The threshold was crossed by **one CQ**: the flip set gained `CQ-09` and lost nothing (`CQ-05, CQ-06, CQ-09, CQ-10, CQ-20, CQ-22, CQ-23, CQ-24`). That is worth stating plainly rather than dressing up — the rule is a bright line, the statistic moved 0.038, and a rule that binds only when it is convenient is not a rule. It is also worth stating that **the extraction is what moved it**: CQ-09 flipped because the corpus now has instruments measuring uncertainty to be duplicated in the first place.

**Category flip, before → after:**

| category | n | before | after |
|---|---:|---:|---:|
| instrument_coverage | 3 | 0.333 | **0.667** |
| discovery_stack | 3 | 0.667 | 0.667 |
| measure_lookup | 3 | 0.667 | 0.667 |
| frontier_candidate | 4 | 0.500 | 0.500 |
| claim_evidence · conflict_detection · construct_definition · provenance_traceback | 3/3/4/3 | 0.000 | 0.000 |

The first run's finding holds and sharpened: **every flip is an enumeration question and no flip is an evidence question.** The only category that moved is `instrument_coverage`, and it moved because the corpus can now enumerate uncertainty instruments — badly.

### 3.2 Per-CQ, both views

| CQ | category | raw before→after | collapsed before→after | rows raw | rows coll | dup |
|---|---|---|---|---:|---:|---:|
| CQ-01 | construct_definition | **partial→yes** | **partial→yes** | 3→36 | 3→36 | 0→0 |
| CQ-02 | construct_definition | partial | partial | 3→3 | 3→3 | 0→0 |
| CQ-03 | construct_definition | yes | yes | 12→12 | 12→12 | 0→0 |
| CQ-04 | construct_definition | yes | yes | 4→4 | 4→4 | 0→0 |
| CQ-05 | measure_lookup | yes | yes | 5→5 | 2→2 | 1→1 |
| CQ-06 | measure_lookup | yes | yes | 18→18 | 8→8 | 3→3 |
| CQ-07 | measure_lookup | yes | yes | 46→46 | 33→33 | 7→7 |
| CQ-08 | instrument_coverage | yes | yes | 10→10 | 10→10 | 0→0 |
| CQ-09 | instrument_coverage | yes | yes | 0→10 | 0→5 | 0→1 |
| CQ-10 | instrument_coverage | partial | yes | 354→483 | 285→362 | 42→64 |
| CQ-11 | claim_evidence | yes | yes | 3→3 | 3→3 | 0→0 |
| CQ-12 | claim_evidence | yes | yes | 84→100 | 82→98 | 2→2 |
| CQ-13 | claim_evidence | yes | partial | 5→5 | 1→1 | 1→1 |
| CQ-14 | conflict_detection | partial | partial | 3→5 | 3→5 | 0→0 |
| CQ-15 | conflict_detection | **no→yes** | **no→yes** | 1→2 | 1→2 | 0→0 |
| CQ-16 | conflict_detection | yes | yes | 12→12 | 12→12 | 0→0 |
| CQ-17 | provenance_traceback | yes | yes | 25→25 | 25→25 | 0→0 |
| CQ-18 | provenance_traceback | yes | yes | 121→121 | 115→115 | 5→5 |
| CQ-19 | provenance_traceback | yes | yes | 50→50 | 47→47 | 3→3 |
| CQ-20 | discovery_stack | yes | yes | 58→58 | 31→31 | 8→8 |
| CQ-21 | discovery_stack | yes | partial | 37→37 | 8→8 | 3→3 |
| CQ-22 | discovery_stack | yes | yes | 92→93 | 33→33 | 17→17 |
| CQ-23 | frontier_candidate | yes | yes | 7→7 | 4→4 | 1→1 |
| CQ-24 | frontier_candidate | yes | yes | 13→13 | 6→6 | 1→1 |
| CQ-25 | frontier_candidate | yes | yes | 8→8 | 6→6 | 2→2 |
| CQ-26 | frontier_candidate | yes | yes | 26→28 | 24→26 | 2→2 |

### 3.3 The three verdicts that changed, with their spans

**CQ-01 (how the corpus defines uncertainty) `partial` → `yes`, 3 rows → 36.** The criterion asks for a span that states what uncertainty *means for a data product*, not a sentence containing the word. `census-acs-general-handbook-2020`: *"The margin of error is the measure of the magnitude of sampling error provided with all published ACS estimates."* `du-2026-possible-or-definite` adds an operational definition over cue-target pairs. Both documents are from this extraction.

**CQ-09 (which Instruments measure uncertainty-related concepts) — empty → 10 rows, and this is the substantive one.** It passed before under the clause that an agreed-empty answer is itself the finding; the first RESULT quoted it as "the graph independently supporting the skeleton's claim that G1 is the sharpest gap." **That support is now withdrawn by measurement.** `mazzi-2021`: *"Comunikos is designed to evaluate alternative ways of measuring and communicating data uncertainty specifically in contexts relevant to official economic statistics"*, owner **Eurostat**. `van-der-bles-2019`: GRADE, *"a system designed to communicate indirect uncertainty."* The consequence runs through **CQ-08**, whose answer — the framework constructs measured by zero Instruments — was ten terms including `uncertainty` and is now six: **provenance, license, revision, discoverability, machine-readable, semantic consistency.** `uncertainty` is off that list.

**CQ-15 (conflicting Definitions of the same term) `no` → `yes`.** This was a recorded failure: the single pair was two fragments of one Census household definition that did not disagree. A second pair now comes from `census-acs-general-handbook-2020` and does: *"The universe in the 2000 Census was 'specified renter-occupied housing units,' which excluded one-family houses on 10 acres or more, whereas the universe in the ACS is 'renter-occupied housing units,' thus, comparisons cannot be made between these two data sets."* Two incompatible definitions of the same universe, with the source itself saying they are not comparable. The criterion asks for a definition pair whose spans disagree about the same term and does **not** require two documents — CQ-14 is the one that does, and it stays `partial` because every conflict pair in the graph still has `doc_a == doc_b`. **The pass rests entirely on the new pair; the original one still fails.**

Everything else is unchanged, including the two CQs (CQ-13, CQ-21) whose collapsed view is *worse* than raw because `collapse_on` names the shared subject of a list question. That is a harness defect recorded in the first RESULT and **deliberately not repaired**, because repairing a harness after seeing its answers is the contamination §1.7 exists to prevent.

### 3.4 Judge caveat

Unchanged and load-bearing: **the session that authored the CQ set is the session that judged it.** Mitigations as pre-registered — criteria written and committed at `369d717` before any query ran, no criterion revised in either run, every verdict citing the grounding spans it was read against (they are in `judge_reason` on every row of the JSONL and in the report). Every Result derived from answerability carries "Verdict by an LLM judge" in its description; row counts, duplicate-group counts and provenance fractions are counted, not judged, and say so.

**This is the before/after. The interpretation — in particular whether it justifies reviving the 55 DD-024 deferrals — is Desktop's, and is not drawn here.**

## 3a. What "AI-ready" actually means in the 23 unextracted documents (ADDENDUM-02)

`scripts/harvest_ai_ready_contexts.py` (Script) → `assessment/results/ai_ready_term_contexts_2026-09-04.jsonl` (DataFile, snapshot) → 5 Results `cq_02_unextracted_sense_*`. Population: the rows of the **pre-extraction** gap file, which is the set the addendum names. Terms: CQ-02's own `ai ready` / `ai-ready` plus `ai readiness`, matched across a hyphen, a space or a PDF line break. **411 sentences in exactly 23 documents** — the addendum's number, reproduced from a different direction. Zero model spend: file reads, a regex, and reading.

| sense | sentences | documents |
|---|---:|---:|
| `data_product_consumption` | 68 | 15 |
| `training_data` | 169 | 11 |
| `adoption` | 92 | 7 |
| `other` | 82 | 18 |
| **total** | **411** | **23** |

Documents carrying at least one `data_product_consumption` sentence:
- `worldbank-blog-open-data-to-ai-ready-2025` — 10
- `usdc-mcp-federal-open-data-pilot-2026` — 8
- `ccsa-2026-ai-ready-official-statistics` — 6
- `doc-rfi-ai-open-gov-data-2024` — 6
- `worldbank-fostering-ai-readiness-official-statistics` — 6
- `odi-framework-for-ai-ready-data-2025` — 5
- `uk-ai-ready-data-action-plan-2026` — 5
- `bandi-2025-metadata-ai-ready` — 4
- `odi-ai-ready-national-data-library-2025` — 4
- `uk-building-ai-ready-datasets-2026` — 4
- `doe-data-cards-standardized-metadata-2026` — 3
- `unsc-2026-stoyanovich-open-data-responsible-reuse` — 3
- `data-unchained-gasper-sequeda-ai-readiness-2026` — 2
- `radhakrishnan-2024-knowing-when-to-ask-data-commons` — 1
- `sequeda-missing-layer-semantics-kg-2025` — 1

**The phrase is a homonym, and the counts are the evidence.** Only **68 of 411 sentences (17%)** carry the framework's sense — a published data product's fitness to be discovered and correctly processed by an AI system at inference. The plurality, 169, is *training data*: cleaning, labelling, feature engineering, "technical optimisation for machine learning." Another 92 are *organizational adoption*, which the ODI framework explicitly disclaims for itself — *"our approach does not extend to evaluating organisational or institutional AI-readiness"* — while PARIS21's SPEEDometer is entirely that sense, scoring an NSO 10–50.

**So "23 documents mention CQ-02's terms" was never the right question,** and the first RESULT was right to say the count "is not a claim that extracting them would have changed any verdict." Extracting all 23 would add far more evidence about preparing training data and about national AI-adoption maturity than about the construct this KG is the validity layer for.

**`data_product_consumption` > 0, so the addendum's condition is met and the documents are listed.** Where the sense concentrates is itself the finding: the World Bank blog (10 of 11 sentences), the USDC MCP pilot (8 of 10), the Commerce RFI (6 of 7), the CCSA and World Bank official-statistics papers (6 each) — the official-statistics and machine-access strand, not the AI-readiness-framework strand. **The decision to extract any of them is Desktop's**, with a ceiling computed from the measured rate per DD-042, not from the call-class floor.

### Every `data_product_consumption` sentence, verbatim

**`worldbank-blog-open-data-to-ai-ready-2025`** (10)

- From open data to AI-ready data: Building the foundations for responsible AI in :L27 — “Amid rapid advances in artificial intelligence (AI), development data has now reached another pivotal juncture: the evolution to **AI-ready development data**—data that is readily discoverable, comprehensible, accessible, and usable by both humans *and *AI applications.”
- Why AI-ready data?:L55 — “In short, the data must be “AI-ready.” AI-ready data does not supplant earlier advancements, foundational concepts, or standards—such as the Fundamental Principles of Official Statistics, open data frameworks, or the FAIR (Findable, Accessible, Interoperable, and Reusable) principles—but rather it builds on them.”
- Why AI-ready data?:L55 — “By extending established foundations and standards, AI-ready data means that development data is continuously open, discoverable, and reusable, while ensuring that it is systematically organized and well-documented, to facilitate seamless use by both people *and* AI systems.”
- Why AI-ready data?:L55 — “Ensuring AI-readiness can thus shorten the distance between development data and decision-making for better policies and faster innovation, democratizing development insights.”
- The case for AI-ready data:L63 — “AI-ready development data can help overcome this information integrity problem.”
- What makes data “AI-ready?”:L73 — “**AI-ready development data** is systematically organized and thoroughly documented to ensure its meaning and context are clear not only for subject matter experts, but also for general users and AI systems.”
- What makes data “AI-ready?”:L73 — “Three core pillars define AI-ready development data: 1. **AI-Ready Data Systems:** The foundational infrastructure—encompassing discovery platforms, APIs, and technical standards—ensures that data is not only stored but also readily discoverable, interoperable, and accessible.”
- What makes data “AI-ready?”:L73 — “By leveraging these foundational elements, development data becomes an accessible asset to all stakeholders. **AI-ready data is positioned to enhance public access, enable advanced insights through AI, and facilitate more rapid and informed decision-making throughout society. **”
- Why is AI-readiness for development data unique?:L117 — “By making development data AI-ready and accessible to AI-powered solutions across both public and private sectors, we will increase its impact, promote more equitable sharing of benefits, and strengthen trust that data will be used responsibly.”
- A call-to-action:L123 — “The transition to AI-ready development data is both urgent and extensive.”

**`usdc-mcp-federal-open-data-pilot-2026`** (8)

- p.4 — “AI agents struggle to interact with federal data systems designed for people, hindering LLM use of federal data while also preventing agencies from effectively testing the AI readiness of their data. ● The risk .”
- p.4 — “MCP servers offer an approach for agencies to make existing APIs accessible, ensuring federal data remains authoritative as AI adoption accelerates and provides agencies with a mechanism for testing the effectiveness of AI-ready data enhancements.”
- p.4 — “While deployment and security challenges require careful planning, MCPs represent essential infrastructure for AI-ready federal data.”
- p.5 — “This need for AI-ready public data has been formally recognized in several recent federal initiatives.”
- p.5 — “In alignment, the Federal Committee on Statistical Methodology (FCSM) issued AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality 3 , which called on agencies to modernize data access to “support accurate and trusted generative AI results.” To achieve this, FCSM recommended agencies explore MCPs as one possible approach for improving machine understandability.”
- p.5 — “In responding to this call, we recognized not only an opportunity for the federal government to take a leading role in defining the technologies associated with AI-ready data, but to improve the use of federal data through agentic interactions with MCP servers.”
- p.9 — “Some data owners may argue that their data is not designed for LLM use and that investing in AI readiness and MCPs is unnecessary and would only encourage improper use.”
- p.29 — “41 This test was designed to assess our hypothesis that federal data is not yet in machine-readable, AI-ready formats.”

**`ccsa-2026-ai-ready-official-statistics`** (6)

- p.6 — “The document introduces a framework for AI -readiness in statistical products.”
- p.7 — “The document examines the AI readiness of official statistics, identiﬁes key risks and opportunities associated with generative AI, and clariﬁes the roles and responsibilities of four principal stakeholder groups.”
- p.14 — “Becoming AI -ready means aligning infrastructure and governance with widely accepted standards so data and metadata are truly machine-actionable and accessible, cultivating transparent data quality practices, and opening programmatic access to data and metadata in ways that are clear, predictable, and responsible.”
- p.15 — “Becoming AI-ready requires modernization across technology, data management and dissemination, governance, and partnerships anchored in machine -actionable metadata, robust quality control, open licensing, responsible AI -enabled access, skills development, and structured collaboration.”
- p.19 — “Create multidisciplinary teams that pair statisticians and subject-matter experts with engineers and product leads to design AI -ready data products, automate curation, and operate reliable dissemination workﬂows.”
- p.22 — “In partnership with NSOs, deﬁne practical criteria, metrics, and workﬂows for metadata quality assessment (e.g., completeness, conformity, consistency, accuracy, speciﬁcity), aligned to endorsed standards, and operationalize an “AI -ready metadata” accreditation to signal machine-readiness and promote continuous improvement. • R.45.”

**`doc-rfi-ai-open-gov-data-2024`** (6)

- p.1 — “To this end, we are pleased to issue this Request for Information (RFI) to seek valuable insights from industry experts, researchers, civil society organizations, and other members of the public on the development of AI-ready open data assets and data dissemination standards.”
- p.2 — “Knowing this, Commerce seeks to adhere to its strategic mission to ‘‘expand opportunity and discovery through data,’’ by disseminating public data in AI ready formats while ensuring no semantic meaning is lost.”
- p.2 — “Commerce seeks to further understand how it can make its data assets AI-ready.”
- p.2 — “What users should Commerce consider when disseminating our AI- ready data?”
- p.3 — “How can Commerce better understand the needs of users for its data and the return on its investment in making its data more AI-ready?”
- p.3 — “How can industry and academic stakeholders collaborate with the government to shape the design and dissemination of AI-ready open data?”

**`worldbank-fostering-ai-readiness-official-statistics`** (6)

- p.2 — “1 Fostering AI-Readiness and Responsible Redistribution of Official Statistics Room Document by the World Bank Introduction The Fundamental Principles of Official Statistics (FPOS) highlight the critical role of high-quality statistical information in promoting sustainable development, peace, security, and international cooperation.”
- p.2 — “AI applications currently possess limited capabilities, and the AI -readiness of data presents a significant challenge.”
- p.2 — “There exists potential for enhanced interaction between AI systems and databases, but this will require AI-ready data.”
- p.3 — “Modernize data curation practices to ensure that official data is AI -ready.”
- p.3 — “During its meeting on 10 October 2024, the Com mittee for the Coordination of Statistical Activities (CCSA) agreed to "jointly promote the adoption of a common set of metadata standards by official data producers and contribute to their implementation in a coordinated manner to foster AI -readiness of official data." 2.”
- p.3 — “Making official statistics AI-ready Many data users do not directly access the websites of data producers.”

**`odi-framework-for-ai-ready-data-2025`** (5)

- p.14 — “3) Surrounding infrastructure For a dataset to be AI-ready, it needs to be published within a surrounding infrastructure that is also AI-ready. a) Datasets should be accessible via a user-centric data portal – A suﬃciently user-centric AI data portal facilitates user engagement with datasets.”
- p.14 — “This empowers practitioners to assess and integrate massive, continuously updated datasets into AI systems, thereby maintaining a responsive and adequate infrastructure in rapidly-evolving analytic contexts. b) Datasets accessible via AI-ready APIs are best practice – Large, well-known AI datasets are easily accessible for data scientists and practitioners via their API infrastructure, enabling users to access and do …”
- p.14 — “However, a genuinely AI-ready data infrastructure should not solely depend on API access; it must also incorporate standardised protocols suited for AI practitioners' usage.”
- p.15 — “When discussing what makes an API AI-ready, interviewees claimed it should employ a RESTful architecture (which is particularly important if we don’t know the use cases of a dataset, given the architecture’s ﬂexibility), avoid pagination (which could artiﬁcially bottleneck their work), and facilitate the querying of subsets and splices of datasets (which is functional in AI contexts, where datasets are often vast).”
- p.15 — “Data spaces are increasingly recognised in academic and industry literature as critical to achieving AI-readiness.”

**`uk-ai-ready-data-action-plan-2026`** (5)

- Pillar 1: Technical optimisation:L132 — “This enables efficient similarity search and retrieval, making legislation, maps, and other complex documents truly AI-ready. - **Representation layers and modern data management**: AI-ready datasets should be managed across multiple representation layers, each optimised for specific technical and operational needs, employing bronze, silver, and gold categorisation as required to represent raw, cleaned, and curated d …”
- Pillar 1: Technical optimisation:L132 — “This combination ensures data is discoverable, accessible, and ready for AI, helping the public sector improve data quality and meet interoperability challenges with robust technical standards and automation. **Example**: I.AI was involved in the analysis of complex structured, semi structured and unstructured data —demonstrating the diversity of data types that must be managed for AI readiness.”
- Department for Work and Pensions (DWP):L534 — “DWP provided insights from their recent experience developing the Generative AI tools DWP ASK, an internal policy chatbot which used Retrieval Augmented Generation (RAG) and GAIL, a tool that assists learning designers to create new content. - **Frame AI readiness** primarily as a data foundation and governance challenge, rather than a modelling or tooling issue. - **Data consistency and machine actionable design:**  …”
- Faculty.AI:L615 — “To resolve the Content Store becomes a middle layer between the public source and AI consumers until the policies are published in a machine readable form - **Metadata**: While working with tabular datasets (outside Content Store), metadata is often minimal or missing, complicating AI readiness, department is building a layer to address the metadata management of structured datasets. - **Dual Interface Design**: Cont …”
- Appendix D - Examples from the UK and overseas:L626 — “Examples include: - **World Bank:** Leading the charge in making development data AI-ready [footnote 19] through comprehensive standards, MCP implementation, and international partnerships - **Singapore:** Singapore’s Model AI Governance Framework [footnote 20] and AI Verify testing toolkit consisting of 11 AI ethics principles provide readily implementable guidelines for private sector organisations addressing key e …”

**`bandi-2025-metadata-ai-ready`** (4)

- p.1 — “The resea rch concludes with a blueprint for metadata -driven AI -readiness, offering actionable recommendations for data leaders, architects, and AI practitioners seeking to transform their data landscapes. | KEYWORDS Metadata management, AI readiness, Data discoverability, Knowledge graphs, Semantic interoperability. | ARTICLE INFORMATION ACCEPTED: 20 May 2025 PUBLISHED: 10 June 2025 DOI: 10.32996/jcsts.2025.7.5.11 …”
- p.1 — “In this landscape, metadata —defined as structured information that describes, explains, locates, and otherwise makes it easier to retrieve and use information resources —has emerged as a critical but frequently overlooked foundation for AI readiness.”
- p.5 — “The Role of Metadata in Making Data AI-Ready: Enhancing Data Discoverability and Usability Page | 958 4.2 Knowledge Graphs for Relationship Modeling Knowledge graph architectures extend traditional metadata repo sitories by explicitly modeling relationships between data assets, business concepts, and organizational structures.”
- p.10 — “Conclusion This study has established metadata as a strategic asset fundamental to AI readiness rather than merely a technical requirement.”

**`odi-ai-ready-national-data-library-2025`** (4)

- substrate_md:L1 — “We have set out[ our vision for an AI ready NDL](https://theodi.org/news-and-events/consultation-responses/the-odis-input-to-the-ai-action-plan-an-ai-ready-national-data-library/) as a data institution that enables safe access to data and provides robust foundations for modern AI driven public services.”
- substrate_md:L1 — “This is because these are the critical dimensions that those designing the NDL need to consider if they are to succeed in making the NDL AI ready and of most value to UK science.”
- Technical Dimension:L24 — “Our conceptual blueprint shows the key enabling elements of the architecture of NDL that are essential for enabling its AI-readiness these are: * **Metadata & dataset documentation**, which describe datasets broadly according to various relevant metadata formats and standards (such as [Croissant](https://theodi.org/insights/projects/croissant/), mentioned earlier), and enacts a solid ground for achieving data interop …”
- Governance Dimension:L33 — “We know that a user-centric approach will be key to co-designing governance that enables the NDL to deliver data that is AI-ready.”

**`uk-building-ai-ready-datasets-2026`** (4)

- p.13 — “This enables efficient similarity search and retrieval, making legislation, maps, and other complex documents truly AI-ready. • Representation layers and modern data management: AI-ready datasets should be managed across multiple representation layers, each optimised for specific technical and operational needs, employing bronze, silver, and gold categorisation as required to represent raw, cleaned, and curated data  …”
- p.34 — “DWP provided insights from their recent experience developing the Generative AI tools DWP ASK, an internal policy chatbot which used Retrieval Augmented Generation (RAG) and GAIL, a tool that assists learning designers to create new content. • Frame AI readiness primarily as a data foundation and governance challenge, rather than a modelling or tooling issue. • Data consistency & machine actionable design: DWP emphas …”
- p.39 — “To resolve the Content Store becomes a middle layer between the public source and AI consumers until the policies are published in a machine-readable form • Metadata: While working with tabular datasets (outside Content Store), metadata is often minimal or missing, complicating AI readiness, department is building a layer to address the metadata management of structured datasets. • Dual Interface Design: Content stor …”
- p.40 — “Examples include: • World Bank: Leading the charge in making development data AI-ready19 through comprehensive standards, MCP implementation, and international partnerships • Singapore: Singapore's Model AI Governance Framework20 and AI Verify testing toolkit consisting of 11 AI ethics principles provide readily implementable guidelines for private sector organisations addressing key ethical and governance issues whe …”

**`doe-data-cards-standardized-metadata-2026`** (3)

- p.13 — “The data card is designed to facilitate FAIR and AI-Ready data goals.”
- p.28 — “We will continue to clarify that discoverability and FAIR properties, while foundational, do not alone guarantee AI ‑ readiness.”
- p.34 — “Shared Data Card Concept Primary ISO/IEC 11179 Reference Alignment Data specification metadata (data elements, domains, datatypes, value meanings) ISO/IEC 11179-31:2023 Relevant where the shared data card describes structured features, schemas, variables, datatypes, and missing value codes Concept systems and ontology-linked semantics ISO/IEC 11179-32:2023 Relevant to science domain schemas, task taxonomies, semantic …”

**`unsc-2026-stoyanovich-open-data-responsible-reuse`** (3)

- p.14 — “What comes next: Develop AI-ready metadata data: provenance, context, structure process: curation, processing, imputation result: interpretation, correctness, confidence”
- p.15 — “machine readable: in a standard AI- accessible format portable: embedded across workflows dynamic: continuously updated also…. incrementally computable, as a by- product of AI computation What comes next: Develop AI-ready metadata “nutritional labels” for AI systems”
- p.19 — “What comes next: Summary AI-ready metadata ✔ Data readiness ✔ Technical readiness ✔ Validation and feedback ● Ensures data is structured, versioned, and machine-readable; ● Preserves provenance, definitions, territorial scope, revision status, and uncertainty; ● Enables AI systems to retrieve the correct release and propagate updates.”

**`data-unchained-gasper-sequeda-ai-readiness-2026`** (2)

- Understanding AI Readiness Before Implementation with Tim Gasper and Juan Sequed:L17 — “It needs context about your business. uh it needs context about people like who who are you and what is your job and what do you do and you know what are your decisions and things like that uh and so this concept of AI readiness and AI ready data has become very much front and center it's it's something that service now is trying to solve it's something that a lot of companies are trying to solve and I think where a  …”
- Understanding AI Readiness Before Implementation with Tim Gasper and Juan Sequed:L17 — “So um so long story short AI ready data is having data that you actually have an understanding to you have meaning semantics and it aligns with a different context that you may have within the organization.”

**`radhakrishnan-2024-knowing-when-to-ask-data-commons`** (1)

- p.23 — “External Partners ● Thank you to our partners at the Statistics Division of the United Nations Department ofEconomic and Social A airs (UN DESA) who ensure that key global datasets are publiclyaccessible and AI ready.● Thank you to the Infosys team and non-pro t social enterprise, Digital Divide Data, fortheir work in evaluating results and supporting multiple iterations of the evaluationtools.”

**`sequeda-missing-layer-semantics-kg-2025`** (1)

- The Missing Layer: Why Semantics and Knowledge Graphs Are Essential for AI-Ready:L17 — “So for them AI ready data is every single column is connected to a particular concept or attribute in a knowledge graph.”

## 4. Doc fix (task §4)

`CLAUDE.md` line 11, done in `e401f16`: *"v1 frozen at 71 docs, 71/71 extracted"* → **"71 docs, 70 of 71 contributing edges to the graph"**, naming `itu-ai-ready-analysis-towards-a-standardized-readiness-frame` and its `extent_unremediable` cut (served only through ITU's JavaScript e-publications reader, no downloadable form), citing the gap-diagnostic RESULT §1. One sentence, as asked.

## 5. The concurrency defect, fixed (ADDENDUM-01 §2)

`chunked_pilot.phase_extract` now dispatches in **bounded waves** through a new `dispatch_waves(todo, workers, run_one, stop_after)`: the failure streak is tested **before each wave is submitted**, and every submitted future's outcome is collected. The old loop submitted all futures up front and called `f.cancel()` on the remainder, which cannot stop a future that has already started — so 286 calls ran, reserved, invoked the model and settled while the loop's `continue` skipped their exceptions.

`tests/test_chunked_pilot_waves.py`, 7 tests, no live burn:

| test | pins |
|---|---|
| `test_at_most_one_wave_is_billed_after_the_streak_trips` (1, 2, 8 workers) | at most `workers − 1` extra calls after the streak trips, against 385 under the old loop |
| `test_every_dispatched_failure_is_counted_not_skipped` | printed failure count == dispatched failures, i.e. == the `error_with_output` settle count |
| `test_a_clean_run_dispatches_everything` | waves do not truncate a healthy pass |
| `test_an_isolated_failure_does_not_stop_the_pass` | one bad chunk still does not discard paid-for work |
| `test_a_spend_refusal_propagates_rather_than_counting_as_a_failure` | `SpendRefusalStop` is a clean exit (DD-022), never a chunk failure |

The extraction primitives are untouched: this changes *when* calls are submitted, not what a call does, so the harness Phase A qualified is still the harness that runs.

## 6. Guard enforcement, registered not implemented (ADDENDUM-01 §3)

**ResearchTask `9a627af8`**: `declare()` refuses a ceiling below `measured_rate(profile) × planned_units` when the ledger holds a measured rate for the profile, and names the computed floor in the refusal. **DD-042** records the rule the task will enforce, with this run as its evidence: the floor is the guard's first-call reservation estimate and is not a price, the measured rate is 2.3× it, and pricing from the floor is what produced a ceiling that had to be superseded mid-run.

## 7. Integration (task §5)

| check | value |
|---|---|
| root `tests/` | **761 passed** (was 752; +3 projection/reset regressions, +7 wave tests, −1 rewritten control) |
| `assessment/` | **471 passed, 1 skipped** (unchanged) |
| `seldon verify` | **All checks passed** (21,575 events readable, ontology epoch 6, no stale artifacts) |
| Scripts registered | `run_g1eval_extraction`, `harvest_ai_ready_contexts`, `register_gap_results` |
| DataFiles registered | `kg_snapshot_2026-09-04b`, `extraction_gap_2026-09-04b`, `cq_v1_2026-09-04b_results`, `ai_ready_term_contexts_2026-09-04`, `spend_ledger_2026-09-04_g1eval` — all `snapshot: true` (AD-027) |
| Results registered | 52 `kg_diag_*_2026-09-04b`, 19 `kg_diag_gap_*_2026-09-04b`, 200 `cq_v1_*_2026-09-04b`, 3 `g1eval_extraction_tokens_*`, 5 `cq_02_unextracted_*` — **279** |
| DesignNotes | DD-042; DD-041 amended on its face |
| ResearchTask | `9a627af8` |

**One test was rewritten rather than fixed, and it is worth naming.** `test_the_shim_pattern_is_stricter_than_the_librarys` failed at the start of this leg — a positive control whose own docstring said *"if seldon ever tightens REFERENCE_PATTERN this test fails and the pre-filter can go."* It fired for exactly that reason: seldon `fa7d113` (2026-09-04) rebuilt `REFERENCE_PATTERN` on `unanchored_name_grammar()`, which is the upstream ResearchTask `3376805b` the shim itself registered. The control is inverted to pin the new agreement between the two grammars; the pre-filter is now redundant but **not removed**, because `resolve_text` substitutes and reports errors through it and retiring it is a rewrite of that function's error paths — resolver-migration work, not extraction work.

## 8. Premises contradicted by live state

1. **`run_ok_no_edges` did not "stay zero" — it went to 17, and the loader was the reason.** The first gap diagnostic's headline finding ("the loader is exonerated") was true of the documents it examined and false as a general statement about the loader: no gap document had extraction history *then*, so the class was empty for want of a test case. The 17 were that test case.
2. **`never_queued` reads 22, not 0.** The class emptied of the `g1eval` epoch and refilled with the 22 fixture-epoch documents, which acquired `Document` nodes at this replay. Issue `2e226acb`'s count `manifest_documents_without_a_document_node` is now **0** and its question is unanswered rather than resolved.
3. **The projection was never a clean rebuild.** 1,201 nodes from a superseded keying scheme had survived every replay because the reset only cleared labelled nodes. `nodes_total` counted them, so any figure quoted from it before today was high by that much.
4. **`CQ-09`'s empty answer — quoted in the first RESULT as the graph independently supporting the G1 gap claim — no longer holds.** Comunikos (Eurostat) and GRADE measure uncertainty concepts, and `uncertainty` has left CQ-08's zero-instrument list. The gap claim may still be right about *survey instruments for data products*; it is no longer supported by "the corpus contains no such instrument", because the corpus does.
5. **The pre-registered rule changed branch on a 0.038 move.** Reported as the rule requires, without adjusting the threshold and without arguing the number down.
6. **"23 documents mention CQ-02's terms" measured a homonym.** 17% of the hits carry the framework's sense; 41% are about training data and 22% about organizational adoption (§3a).
7. **The CQ registrar could not have registered a rerun.** Its Result names carried no date by an explicit choice recorded in its own docstring, so a rerun would have overwritten the first run's Results — the opposite of what §1.6 requires. Fixed with `--suffix` before anything was registered.
8. **The gap diagnostic had no registration script at all**; its first 16 Results came from an ad-hoc command. `scripts/register_gap_results.py` now exists.
9. **`scripts/extraction_gap_diagnostic.py` crashed on a relative `--out`** after writing its output — `relative_to` against an absolute repo root. A run that had done all its work reported as a traceback.
10. **`run_g1eval_extraction.cohort()` gated on the live worklist**, which a completed run empties, so every read-only phase failed the moment the extraction it reports on succeeded. Re-gated on queue state.

## 9. Out of scope, untouched

The 55 DD-024 deferrals — priced, discussed, not revived; that decision is Desktop's and §3 is the evidence it was waiting for. The 22 fixture-epoch documents (`2e226acb`) — their class changed and their question did not. Entity resolution (`93a628e8`) — the rule now says it is P0 and blocking, and this RESULT does not act on that. CQ set v2. The admission-does-not-enqueue question (`609cb10b`).
