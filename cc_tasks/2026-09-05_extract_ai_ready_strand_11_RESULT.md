# RESULT: the AI-ready-data-product strand extracted; CQ-02 answered; the gap classes cleared

**Task:** `cc_tasks/2026-09-05_extract_ai_ready_strand_11.md` §0–§5. **No addenda** — globbed before starting, none exist. **Date:** 2026-09-05 UTC. **Spend: 10,988,869 tokens settled** against a declared ceiling of 11,771,414, Claude Max OAuth throughout. **Task file committed before execution** (`26da35f`), per the dispatch protocol.

**The headline, stated before the accounting.** CQ-02 — *how does the corpus define "AI-ready data"* — moved **`partial` → `yes` in both views**, and it moved for the right reason: the corpus now holds two definitions in the sense the framework means, from different documents, comparable to each other and contrastable with the training-data sense it already had. That is what the cohort was extracted to do and it is the only CQ whose verdict changed.

**The second finding is negative and is reported with equal weight.** `flip` did not move: **0.307692 before, 0.307692 after**, the same eight CQs. Eleven documents, 1,447 new document-anchored edges, 795 new Concepts — and the duplicate-collapse statistic is identical to four decimal places. Extraction does not fix entity resolution; it feeds it. `concept_dup_node_share` went **up**, 0.408 → 0.413.

---

## §0. Decisions recorded — DD-043

Appended to `docs/design_decisions.md` as **DD-043**, three parts. Committed at `cf1a48a`, before the extraction ran.

### §0.1 The cohort is 11, and the UK pair is one publication

The task said the two UK documents' §3a sentences are identical and asked for confirmation by hash or diff before cutting one. **They are not identical, and the discrepancy is instructive:** `uk-ai-ready-data-action-plan-2026` yields 5 `data_product_consumption` sentences and `uk-building-ai-ready-datasets-2026` yields 4. The extra one is a sentence-splitting artifact — the markdown renders a bullet list that the PDF's line breaks fuse into the preceding sentence.

Content hashes differ (`d0f18941…` vs `7787378048…`) because the substrates differ, so the determination had to be made on text. Measured:

| direction | sentences ≥ 12 words | with a majority 5-gram match in the other | share |
|---|---:|---:|---:|
| PDF → markdown | 383 | 369 | **96.3 %** |
| markdown → PDF | 389 | 377 | **96.9 %** |

8-gram shingle containment is 0.792 / 0.817, Jaccard 0.672 — lower than the sentence figure precisely because PDF line-break and hyphenation artifacts break shingles that the sentence comparison survives. Every residual sentence is chrome: on the PDF side the dot-leader table of contents, the copyright page and `alt.formats@dsit.gov.uk`; on the markdown side the GOV.UK cookie banner, the "Is this page useful?" widget and the site footer. Two substantive differences are house style (`&` vs `and`) and one markdown table the PDF loses to page layout.

**Determination: the same DSIT publication acquired twice.** The markdown is kept — it preserves the four-pillar lifecycle **table**, and it passes the DD-030 extent gate on its own terms (77,492 visible characters against a 2,000 floor; link density **0.000** against a 0.25 ceiling), so it is the document and not a landing page. `uk-building-ai-ready-datasets-2026` is deferred with reason `duplicate_of:uk-ai-ready-data-action-plan-2026`, an append-only correction to its earlier `no consumer` deferral.

**Cohort = 11.** Not asserted from the task's list: `run_strand_extraction.cohort()` recomputes the §3a rule (≥ 3 `data_product_consumption` sentences) from the registered harvest, subtracts anything a live `duplicate_of:` deferral cuts, and intersects with the queue. The eleven it returns are the eleven the task names. A hardcoded list would have made the task file rather than the evidence the authority for membership, and would have kept the UK duplicate — a list does not know about a deferral.

### §0.2 Eval fixtures are excluded by rule — Issue `2e226acb` closed

The 22 members of `g1dp-2026-09-02` (1), `g1srp-2026-09-03` (4) and `g1sfc-2026-09-03` (17) are what G1 **scores**: a Census API JSON slice, an NCHS Data Brief, a StatCan cube, a BLS news release. They were landing in `never_queued` — *"admitted to the corpus; no extraction_request was ever emitted for it"* — which is true and is the wrong explanation. It reads as an oversight the corpus owes work on, and it was the sole reason that class could not reach zero.

The mechanism is a rule, not 22 hand-emitted deferrals:

* `fixture_epochs:` in `dixie_evidence.yaml` names the epochs — the file CLAUDE.md already designates for operator decisions that code reads and never edits;
* `kg.queue.fixture_epochs()` reads it, `kg.queue.fixture_documents()` expands it against the epoch declarations in the dixie ledger;
* `kg.queue.deferrals()` overlays a synthetic `eval_fixture` deferral, so every surface reading the queue's single derivation — `status`, `worklist()`, the gap diagnostic's `excluded_by_design` class — inherits the exclusion without knowing fixtures exist.

Two properties make it a rule rather than a default. `kg.queue.request()` **refuses** a fixture document and names the epoch that refused it. And the overlay is applied **last**, so a stray `extraction_request` event cannot revive a fixture the way it legitimately revives a human deferral — the revive-on-request rule exists so a person can change their mind about one document, and a fixture exclusion is not a judgment about a document, it is what the document is.

Seven tests in `tests/test_fixture_epoch_exclusion.py`, all written before the code and failing first (`AttributeError: module 'kg.queue' has no attribute 'fixture_epochs'`). Two assert against the **live** config so the tagged set cannot drift from the epochs that exist, and one is a mutation guard: retagging the config must move which document is excluded, which a hardcoded list would not do. A fourth fixture epoch is now one line of YAML.

**Issue `2e226acb` is `resolved`.** Both halves are answered: the 22 now have Document nodes (`kg_diag_gap_manifest_documents_without_a_document_node_2026-09-05` = 0, against 22 when the issue was filed — the g1eval replay created them), and the question the issue explicitly left open, *whether these 22 should become Document nodes*, is answered — they stay as nodes and are never queued.

### §0.3 The remaining deferrals stay deferred

Four `data_product_consumption` documents with fewer than three hits (`data-unchained-gasper-sequeda-ai-readiness-2026` 2, `radhakrishnan-2024-knowing-when-to-ask-data-commons` 1, `sequeda-missing-layer-semantics-kg-2025` 1, and the UK duplicate) and the rest of the 55 remain deferred under DD-024/DD-041. **41 documents still carry reason `no consumer`.** Not a reversal, and not quietly widened.

---

## §1. The ceiling, from the measured rate (DD-042)

| | |
|---|---:|
| chunks, under the pipeline's own chunker | **225** |
| rate Result | `g1eval_extraction_tokens_productive` = 31,299,448 |
| over | 688 chunks |
| **measured rate** | **45,493.38 tokens/chunk** |
| headroom | × 1.15 |
| **ceiling declared** | **11,771,414** |
| the same work priced at the `extraction_chunk` floor | 4,500,000 (**2.6× too low**) |
| §1's stop threshold | 20,000,000 — not reached, no stop |

**Discrepancy with the task file, reported not reconciled.** §1 names the rate as `g1eval_extraction_tokens_productive / 688` and then writes the literal **45,521**. The division gives **45,493.38**: 45,521 × 688 = 31,318,448, which is 19,000 tokens above the registered figure. The derivation was followed rather than the literal, because DD-042's whole point is that the ceiling is computed from the measurement and not from a number carried by hand. The difference is 0.06 % — 7,000 tokens on this ceiling — and changes nothing, which is exactly why it is worth recording: a literal that agrees to four significant figures is the kind that survives unchecked.

Registered: **`strand_extraction_tokens_declared` = 11,771,414**.

---

## §2. Extraction

**221 model calls in the completing pass, 0 failures, 225 chunks ingested → 2,427 nodes, 2,546 edges, 898 mentions, 525 diverted, 27 semantic edges refused.** Profile `bulk_v038`, prompt v0.3.8, model `claude-opus-5`, wave dispatch confirmed: `chunked_pilot.phase_extract` calls `dispatch_waves` at line 513 and there is no other path.

### Spend, read off the ledger

| Result | value |
|---|---:|
| `strand_extraction_tokens_declared` | 11,771,414 |
| `strand_extraction_tokens_productive` | **10,988,869** (93.3 % of ceiling) |
| `strand_extraction_tokens_wasted` | **0** |
| `strand_extraction_tokens_unsettled` | 87,620 (estimate; see below) |

227 reservations, 225 settles, every settle `outcome_class: success`, **no chunk settled twice**. Wasted is zero and that is the number §2 asked for even if zero — the comparable figure for the g1eval run was 15,073,098, 32.5 % of it, before the `dispatch_waves` fix. This is the first run to go through bounded waves end to end and it discarded nothing.

**The two unsettled reservations are an operator action and are reported as one.** The run was started at 2 workers, measured at ≈ 4.7 hours, and restarted at 6 workers after 4 chunks — `chunked_pilot` skips already-extracted chunks, so the restart resumed at chunk 5. Two calls (`bandi-2025-metadata-ai-ready#c0005`, `#c0006`) were killed about a minute in; their partial output was billed and discarded, and both chunks were re-extracted cleanly in the second pass. A killed call never settles, so no measured token count exists for them; 87,620 is the guard's reservation for the two and is the honest upper bound. It is registered under its own name rather than folded into `_wasted`, because a Result carries one measured number and this one is an estimate.

**DD-042's first out-of-sample test, and it held.** Measured 10,988,869 / 225 = **48,839 tokens/chunk** against 45,493 predicted from a different cohort — 7.4 % high, entirely absorbed by the 15 % headroom, finishing at 93.3 % of ceiling. Had this run been priced at the call-class floor it would have stopped at a document boundary about 41 % of the way through.

### Per-document

| document | chunks | edges | Concept | Claim | Definition | tokens |
|---|---:|---:|---:|---:|---:|---:|
| bandi-2025-metadata-ai-ready | 10 | 96 | 76 | 54 | 5 | 510,832 |
| ccsa-2026-ai-ready-official-statistics | 17 | 218 | 97 | 64 | 4 | 974,335 |
| doc-rfi-ai-open-gov-data-2024 | 29 | 111 | 84 | 25 | 2 | 1,198,119 |
| doe-data-cards-standardized-metadata-2026 | 38 | 109 | 69 | 32 | 25 | 1,826,102 |
| odi-ai-ready-national-data-library-2025 | 5 | 33 | 24 | 13 | 0 | 226,201 |
| odi-framework-for-ai-ready-data-2025 | 32 | 154 | 69 | 76 | 5 | 1,605,128 |
| uk-ai-ready-data-action-plan-2026 | 26 | **317** | 144 | 146 | 22 | 1,248,507 |
| unsc-2026-stoyanovich-open-data-responsible-reuse | 2 | 33 | 17 | 12 | 0 | 107,355 |
| usdc-mcp-federal-open-data-pilot-2026 | 45 | 192 | 124 | 64 | 10 | 2,313,723 |
| worldbank-blog-open-data-to-ai-ready-2025 | 14 | 83 | 34 | 30 | 4 | 595,600 |
| worldbank-fostering-ai-readiness-official-statistics | 7 | 101 | 57 | 47 | 2 | 382,967 |
| **total** | **225** | **1,447** | **795** | **563** | **79** | **10,988,869** |

Every one of the eleven contributes edges; none is a silent no-op. Chunk count and yield are only loosely related — `doe-data-cards` needed 38 chunks for 109 edges while `uk-ai-ready-data-action-plan` got 317 from 26.

### Gap diagnostic reread — all three required checks pass

`state/extraction_gap_2026-09-05.json`, 19 Results at `--suffix _2026-09-05`.

| check | required | measured |
|---|---|---|
| `run_ok_no_edges` | 0 | **0** ✓ |
| `never_queued` | 0 (fixtures now excluded) | **0** ✓ |
| `documents_with_edges` | 156 + 11 = 167 | **167** ✓ |

| class | 09-04b | 09-05 |
|---|---:|---:|
| never_queued | 22 | **0** |
| queued_not_run | 0 | 0 |
| run_failed | 0 | 0 |
| run_ok_no_edges | 0 | 0 |
| excluded_by_design | 55 | **66** |
| source_missing | 0 | 0 |
| **gap total** | **77** | **66** |

**Every document that contributes nothing to the graph now cites a reason** — 41 `no consumer`, 22 `eval_fixture`, 1 `duplicate_of:`, 1 `extent_unremediable` (the ITU cut), 1 `conversion_gap`. That is the first time the gap has been fully explained since the diagnostic was written.

---

## §3. Diagnostic and CQ v1 rerun

### §3.1 Structural delta

`state/kg_snapshot_2026-09-05.json`, 52 Results at `--suffix _2026-09-05`.

| metric | 09-04b | 09-05 | Δ |
|---|---:|---:|---:|
| nodes_total | 32,204 | 34,753 | +2,549 |
| concept_total | 10,637 | 11,432 | +795 |
| claim_total | 6,213 | 6,776 | +563 |
| document_total | 233 | 233 | 0 |
| **documents_extracted** | **156** | **167** | **+11** |
| documents_without_extractions | 77 | 66 | −11 |
| document_extractions_median | 34 | 41 | +7 |
| concept_dup_groups | 1,387 | 1,486 | +99 |
| concept_dup_nodes | 4,343 | 4,722 | +379 |
| **concept_dup_node_share** | **0.408292** | **0.413051** | **+0.004759** |
| ai_readiness_nodes | 14 | 21 | +7 |
| ai_readiness_in_edges | 44 | 66 | +22 |
| concept_degree_0 | 761 | 869 | +108 |
| concept_degree_1 | 5,249 | 5,661 | +412 |
| concept_degree_ge5 | 484 | 502 | +18 |
| concept_degree_median | 1 | 1 | 0 |
| concept_degree_max | 26 | 26 | 0 |
| domain_edges_total | 32,096 | 34,388 | +2,292 |
| domain_edges_both_kg_labels | 27,785 | 29,865 | +2,080 |
| edges_total | 39,738 | 42,640 | +2,902 |
| document_cites_document | 35 | 36 | +1 |
| claim_conflicts_claim | 5 | 5 | 0 |
| definition_conflicts | 2 | 2 | 0 |
| claims_without_asserts_source | 55 | 55 | 0 |
| concept_with_doc_id / grounding_span | 10,637 | 11,432 | +795 |
| document_with_content_hash | 233 | 233 | 0 |
| document_with_prov_source_sha256 | 0 | 0 | 0 |

By label: Concept +795, Claim +563, Practice +260, Standard +130, Definition +79, Measure +77, Framework +53, Platform +29, Instrument +19, Tool +17.

**`concept_with_grounding_span` equals `concept_total` exactly, as it has every run — invariant 3 holds through 795 new nodes.** `claims_without_asserts_source` did not grow, so the strand added no orphan claims. `concept_degree_0` grew by 108 against +795 concepts: **13.6 % of the new concepts attach to nothing**, slightly better than the standing 7.2 % base rate would predict but still the largest single quality cost of the run.

### §3.2 CQ v1 aggregates

`assessment/cq/cq_set_v1.yaml` **unchanged at `369d717`** — `git diff --quiet 369d717 -- assessment/cq/cq_set_v1.yaml` returns clean. No criterion edited, no harness repaired.

| aggregate | 09-04b | 09-05 |
|---|---:|---:|
| `A_raw` | 0.884615 | **0.923077** |
| `A_collapsed` | 0.846154 | **0.884615** |
| `flip` | 0.307692 | **0.307692** |
| `C` (dup groups unioned) | 121 | 125 |
| `misleading_raw_count` | 9 | 9 |

**Rule branch (pre-registered §1.5): `flip` = 0.308 ≥ 0.30 → entity resolution is P0 and blocks probe design.** Same branch as the previous run, reached by the same eight CQs — `CQ-05, CQ-06, CQ-09, CQ-10, CQ-20, CQ-22, CQ-23, CQ-24`. The flip set did not gain or lose a member.

This is the useful part of a negative result. The previous run crossed the threshold **on** the extraction (CQ-09 joined the flip set because the corpus acquired instruments that could then be duplicated). This run added a comparable volume of material — 795 concepts against the g1eval run's 1,975 — and moved the statistic by **zero**. `flip` is not tracking corpus growth; it is tracking a structural property of the graph that only entity resolution changes. The branch stands on its own evidence rather than on a single question's luck.

Category table, unchanged in every cell:

| category | n | flips | flip | driving |
|---|---:|---:|---:|---|
| construct_definition | 4 | 0 | 0.0 | — |
| measure_lookup | 3 | 2 | 0.667 | CQ-05, CQ-06 |
| instrument_coverage | 3 | 2 | 0.667 | CQ-09, CQ-10 |
| claim_evidence | 3 | 0 | 0.0 | — |
| conflict_detection | 3 | 0 | 0.0 | — |
| provenance_traceback | 3 | 0 | 0.0 | — |
| discovery_stack | 3 | 2 | 0.667 | CQ-20, CQ-22 |
| frontier_candidate | 4 | 2 | 0.5 | CQ-23, CQ-24 |

### §3.3 Per-CQ, both views

| CQ | category | raw | collapsed | rows raw | rows collapsed |
|---|---|---|---|---:|---:|
| CQ-01 | construct_definition | yes | yes | 36→36 | 36→36 |
| **CQ-02** | construct_definition | **partial→yes** | **partial→yes** | **3→7** | **3→7** |
| CQ-03 | construct_definition | yes | yes | 12→14 | 12→14 |
| CQ-04 | construct_definition | yes | yes | 4→4 | 4→4 |
| CQ-05 | measure_lookup | yes | yes | 5→5 | 2→2 |
| CQ-06 | measure_lookup | yes | yes | 18→18 | 8→8 |
| CQ-07 | measure_lookup | yes | yes | 46→46 | 33→33 |
| CQ-08 | instrument_coverage | yes | yes | 10→10 | 10→10 |
| CQ-09 | instrument_coverage | yes | yes | 10→10 | 5→5 |
| CQ-10 | instrument_coverage | partial | yes | 483→502 | 362→377 |
| CQ-11 | claim_evidence | yes | yes | 3→5 | 3→5 |
| CQ-12 | claim_evidence | yes | yes | 100→112 | 98→110 |
| CQ-13 | claim_evidence | yes | partial | 5→11 | 1→2 |
| CQ-14 | conflict_detection | partial | partial | 5→5 | 5→5 |
| CQ-15 | conflict_detection | yes | yes | 2→2 | 2→2 |
| CQ-16 | conflict_detection | yes | yes | 12→14 | 12→14 |
| CQ-17 | provenance_traceback | yes | yes | 25→25 | 25→25 |
| CQ-18 | provenance_traceback | yes | yes | 121→121 | 115→115 |
| CQ-19 | provenance_traceback | yes | yes | 50→50 | 47→47 |
| CQ-20 | discovery_stack | yes | yes | 58→58 | 31→31 |
| CQ-21 | discovery_stack | yes | partial | 37→37 | 8→8 |
| CQ-22 | discovery_stack | yes | yes | 93→111 | 33→35 |
| CQ-23 | frontier_candidate | yes | yes | 7→20 | 4→7 |
| CQ-24 | frontier_candidate | yes | yes | 13→13 | 6→6 |
| CQ-25 | frontier_candidate | yes | yes | 8→8 | 6→6 |
| CQ-26 | frontier_candidate | yes | yes | 28→31 | 26→29 |

**CQ-02 is the only verdict that changed.** Ten CQs returned identical row counts *and* identical rows and duplicate groups; their verdicts are carried with that stated in the judge reason, rather than re-asserted as if re-derived.

**Judging discipline.** All 26 were judged by reading returned grounding spans against the criteria pre-registered at `369d717`. No criterion was revised. Two known defects were deliberately left unrepaired so the before/after is not contaminated: **CQ-13**'s collapse groups on the shared subject Concept rather than the listed Claim (11 claims → 2 groups), and **CQ-21**'s equivalent. **CQ-14** is held at `partial` although its criterion is literally met — manski-2015's *"The estimates of GDP and GDI are accurate"* against *"realtime research has shown that this assumption is false"* genuinely disagree — because the *question* asks where two **documents** conflict and all five pairs remain intra-document. The strand produced no cross-document conflict. The criterion is not rewritten to make that pass.

**Judge caveat stands, and is on every answerability-derived Result.** `A_raw`, `A_collapsed` and `flip` rest on an LLM judge's verdicts — the same session that ran the queries read the spans. Row counts, duplicate-group counts and provenance fractions do not.

### §3.4 CQ-02 — the question the cohort was extracted to answer

**Yes. The collapsed view now returns a definition in the `data_product_consumption` sense, from two documents.** All seven rows, verbatim:

**In the framework's sense — a published data product's fitness to be found and correctly processed by an AI system:**

> `worldbank-blog-open-data-to-ai-ready-2025` — "AI-ready data means that development data is continuously open, discoverable, and reusable, while ensuring that it is systematically organized and well-documented, to facilitate seamless use by both people *and* AI systems"

> `uk-ai-ready-data-action-plan-2026` — "AI-ready datasets that are technically fit for modern AI capabilities, intelligible beyond their original operational purpose, and governed in ways that are lawful, ethical, and worthy of public trust"

> `uk-ai-ready-data-action-plan-2026` — "AI-ready datasets should therefore be maintained at multiple levels of granularity (called grains), with each representation governed and documented explicitly."

> `uk-ai-ready-data-action-plan-2026` — "As set out in the Open Data Institute (ODI) A framework for AI-ready data [footnote 4], a dataset may be considered AI-ready when it address these 4 components:"

**In the training-data sense, which the corpus already had:**

> `data-readiness-for-scientific-ai-at-scale` — "AI-ready data—cleaned, labeled, normalized, feature-engineered, and formatted for scalable training"

> `data-readiness-for-scientific-ai-at-scale` — "an AI-ready state—defined by sharded storage in binary formats such as HDF5, ADIOS [25], or TFRecords"

**Vendor boilerplate, retained because the query returns it and removing it would be curating the evidence:**

> `odcs-open-data-contract-standard` — "[BigQuery] is a fully managed, AI-ready data analytics platform that helps you maximize value from your data and is designed to be multi-engine, multi-format, and multi-cloud."

The criterion — *two or more distinct documents return a span that defines the term, so the definitions can be compared* — is met on both counts. Four documents define it, and the answer is now a **definition landscape rather than a single quote**: the two consumption-sense definitions are comparable to each other and *contrast* with the training-sense pair, which is precisely the homonym §3a of the previous task measured. `dup_groups_unioned` is 0 and collapse shrink is 0, so raw and collapsed agree; entity resolution is not doing any work here.

**Two caveats a reader needs.** First, **only 2 of the 11 documents in the cohort returned a CQ-02 row.** Nine documents that each mention the phrase in the consumption sense three or more times contain no span the extractor recognised as a *definition* of it — they use the term rather than define it. That is a real and slightly deflating finding about the strand: the sense is widespread and the definitions are rare. Second, the fourth UK span is a **pointer** ("as set out in the ODI framework … these 4 components") whose components are not in the span; it is counted as a defining row because the criterion asks for a span that defines the term and it does state the condition, but it is the weakest of the four.

### §3.5 What else the strand moved

**CQ-23 (MCP as a discovery mechanism) grew most: 7 → 20 raw rows, 4 → 7 distinct.** `usdc-mcp-federal-open-data-pilot-2026` and `worldbank-blog-open-data-to-ai-ready-2025` both assert it, both dated 2025, so the frontier candidate is now carried by four documents rather than two. **CQ-10** gained 15 distinct Instruments (362 → 377). **CQ-12** gained 12 claims about preparation cost. **CQ-13** more than doubled its raw interoperability claims (5 → 11) and still collapses to 2 — the sharpest single illustration in the run of extraction feeding a defect rather than fixing it.

---

## §4. Issue: the CQ-09 gap claim

Registered as Issue **`cfe9eaf7`** (`unsupported_claim`, importance high, urgency medium, detection `audit`, target `content`), with six `ANNOTATES` edges to the `cq_v1_CQ_09_*` Results on both sides of the change (`cq_v1_CQ_09_rows_raw` = 0, `cq_v1_CQ_09_rows_raw_2026-09-04b` = 10, and the collapsed and distinct-entity pairs).

The Issue records: the first harness RESULT quoted CQ-09's empty answer as the graph independently supporting *G1 is the sharpest gap*; RESULT-02 withdrew that support by measurement (Comunikos/Eurostat via `mazzi-2021`, GRADE via `van-der-bles-2019`), and `uncertainty` left CQ-08's zero-instrument list. **The claim is not falsified — it is unsupported as stated.** It survives re-scoped to *no AI-readiness assessment instrument measures uncertainty legibility*, and CQ v1 cannot test that, because no v1 question joins an Instrument to the kind of Framework that owns it.

**The v2 competency question, recorded in the Issue text as §4 requires:** return every Instrument that (a) `MEASURES` a Concept whose surface form matches the uncertainty term set CQ-08 already uses, **and** (b) whose parent Framework qualifies as an AI-readiness assessment — either by `normative_status` in the readiness/maturity family, or by carrying an `ABOUT` edge to a Concept in the AI-readiness cluster. An empty answer to *that* is the evidence the memo needs; an empty answer to CQ-09 was not.

Per §4, the memo and deck are **not** edited. If v2 answers the re-scoped question, that is an erratum then, on evidence.

---

## §5. Integration

| check | result |
|---|---|
| `python -m pytest tests/` | **768 passed** (761 + 7 new) |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** (11 checks, 21,593 events readable) |
| `cq_set_v1.yaml` diff vs `369d717` | **empty** |
| `git status --short` | clean at close |

**Artifacts registered.** 1 Script (`run_strand_extraction`, `7aa6665b`); 5 DataFiles, all `snapshot: true` (`strand_extraction_2026-09-05`, `extraction_gap_2026-09-05`, `kg_snapshot_2026-09-05`, `cq_v1_2026-09-05`, plus the aggregates carried by the CQ registrar); **275 Results** — 52 `kg_diag_*_2026-09-05`, 19 `kg_diag_gap_*_2026-09-05`, 200 `cq_v1_*_2026-09-05`, 4 `strand_extraction_tokens_*`; DD-043; Issue `cfe9eaf7` created; Issue `2e226acb` resolved.

---

## §6. Premises contradicted, and things worth flagging

1. **The task's rate literal 45,521 is not `g1eval_extraction_tokens_productive / 688`.** The division gives 45,493.38. Derivation followed, literal reported. §1.
2. **The two UK documents' §3a sentences are not identical** (5 vs 4), though the documents are. The extra hit is a sentence-splitting artifact. The conclusion the task drew from the premise is unaffected. §0.1.
3. **`flip` did not move**, which the task's framing ("the §1.5 rule is evaluated and the branch reported") allowed for but the shape of the previous run invited expecting. Eleven documents changed it by zero. §3.2.
4. **Only 2 of the 11 cohort documents return a CQ-02 definition row.** The cohort rule selected documents that *use* the term in the framework's sense; using it and defining it turn out to be very different populations. §3.4.
5. **Extraction made the duplicate problem measurably worse**: `concept_dup_node_share` 0.408 → 0.413, `concept_dup_groups` +99. Every extraction from here compounds the entity-resolution debt the §1.5 rule now calls P0.
6. **108 of the 795 new Concepts (13.6 %) have degree 0.** Not a regression against the base rate, and still the run's largest quality cost.
7. **Issue `830330b4`** — the spend-control defect RESULT-02 fixed with `dispatch_waves` — **is still `open`** in the graph. This run is its evidence (0 wasted tokens against 15,073,098 before), but closing it is a record change outside this task's scope. Flagged for whoever authors the next one.
8. **The run was restarted at higher concurrency mid-flight**, an operator action costing an estimated 87,620 tokens, taken because 2 workers paced at ≈ 4.7 hours against 6 workers' ≈ 2.1. Under the cap, so decided and logged rather than escalated. §2.

## §7. Out of scope, untouched

Entity resolution (`93a628e8`), CQ set v2, the 41 remaining `no consumer` deferrals, `609cb10b`. The memo and the deck. The CQ-13/CQ-21 harness defect. The resolver pre-filter.
