# RESULT: a controlled vocabulary resolved at write time — and a failed acceptance test that indicts the gate

**Task:** `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §0–§5. **No addenda** — globbed before starting, none exist. **Date:** 2026-09-05 UTC. **Spend: 7,370,861 tokens settled** across three declared runs, Claude Max OAuth throughout. **Task file committed before execution** (`f967eed`).

**The headline is a failure, and it is the useful result.** §4 pre-registered two acceptance criteria. Both failed, neither narrowly. But the diagnosis is not that the vocabulary underperformed — it is that **`flip` cannot measure what it was adopted to trigger.** `flip` fires on `misleading_raw`, which is computed from how much the *raw* view shrinks; the raw view is one node per document per mention **because DD-020 requires it**. No entity resolution that respects DD-020 can ever move `flip`. The gate adopted in `2026-09-04_kg_diagnostic_and_cq_harness` §1.5 and the invariant in DD-020 contradict each other, and this task is where that surfaced. The rule stands as written — a failed pre-registered gate triggers investigation, never retuning.

**The second finding is smaller and sharper:** adding one edge type changed a byte-identical query's answer. CQ-21 went from 37 rows to 51 the moment `RESOLVES_TO` existed, because it traverses an untyped relationship.

---

## §0. Prior art, and why vocabulary-first — DD-044

Recorded as **DD-044** with every citation the task lists: Cutter (1876), LCSH, ISO 25964-1:2011 and W3C SKOS (2009) for the vocabulary; **Fellegi & Sunter (1969)**, *JASA* 64(328):1183–1210 for the three-way threshold split; Franklin, Halevy & Maier (2005) and Madhavan et al. (2007) for pay-as-you-go promotion; Cohen (1960) and Landis & Koch (1977) for the agreement statistic and its 0.60 boundary; sift-kg as implementation precedent, not origin. Both historical bottlenecks — the cataloguer and the clerk — were *judgment*, which is now affordable.

The evidence for vocabulary-first over a dedup pass is this project's own: **the 2026-09-05 strand extraction added 795 Concepts and moved `flip` by exactly zero.** A batch pass over a "complete" corpus is stale the next time anything is extracted. `93a628e8` is superseded with `superseded_by` pointing at this task.

## §1. Phase A — seed and deterministic layer (zero model spend)

### §1.1 Where the vocabulary lives: NOT Seldon's ontology module

Decided by reading `seldon/commands/ontology.py`, not by assumption. Two blockers:

1. **`ONTOLOGY_MASTER_DB = "seldon-ontology"` is a module-level constant in `seldon/config.py` with no override.** Every write path — `_ensure_master_db`, `_ensure_master_indexes`, `_get_or_create_master_meta`, `_increment_epoch`, `_read_master_state` — names it directly. The task's `ai-readiness-vocabulary` option cannot exist without editing Seldon.
2. **`_do_sync` pulls `MATCH (a:Artifact:OntologyTerm) RETURN a` with no namespace filter.** Every master term lands in every project's replica. A 1,946-term domain thesaurus would be pushed into every other project — exactly what §1.1 forbids.

A third, smaller gap: `OntologyTerm` carries `term_id/name/definition/category/namespace/citations/extra` with no first-class `altLabel`, `broader`, `narrower` or `scopeNote`, so a thesaurus would have to hide its structure in an `extra` JSON blob and could not be indexed on aliases.

**Choice: project-owned `:Term` nodes** with the same append-only event shapes AD-017 uses — `term_added`, `term_alias_added`, `term_deprecated`, `vocabulary_epoch` — on shard `batch-026`. Exported as **SKOS Turtle**: `ontology/ai_readiness_vocabulary.ttl`, 3,485 concepts, **29,715 triples**. Seldon ResearchTask **`af389420`** records exactly what would have to change to fold it in later.

`Term` and `RESOLVES_TO` are deliberately **absent from `kg/schema.yaml`**: that file is the parser's whitelist, and a model must never be able to assert a vocabulary term or a resolution edge.

### §1.2 The seed — 1,946 terms, every one sourced

| source | terms | aliases |
|---|---:|---:|
| S1 framework constructs + indicator groups (`usafacts_operationalization_skeleton.md` table, `assessment_protocol.md` §7) | 51 | 47 |
| S2 discovery stack + dated frontier candidates | 12 | 23 |
| S3 search-optimisation lineage | 4 | 5 |
| S4 KG name groups, per node label | 1,879 | 997 |
| S5 model-asserted `aliases` property | — | 1,868 |
| **total (active)** | **1,946** | **2,940** |

**S3, dated and sourced as §1.2.3 requires, with the scope notes saying what each optimises *for*:**

| term | first use | origin | optimises for |
|---|---|---|---|
| **SEO** | 1997, John Audette (Multimedia Marketing Group) — attribution *contested*; Bruce Clay, Bob Heyman, Leland Harden credited around the same date | industry | position in a ranked list of destinations |
| **AEO** | 2023-05-26 (nogood.io) | industry, no academic paper | being the cited source of a single returned answer |
| **GEO** | **arXiv:2311.09735, 2023-11-16**, Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan & Deshpande; KDD 2024 | **academic** | share of a synthesised answer composed from many sources |
| **AIO** | 2024–2025, after Google AI Overviews launched 2024-05-14 | industry, **no consensus definition as of 2026** | ambiguous — three live senses, recorded as ambiguous rather than resolved |

GEO is the only member of the lineage with an academic origin; it models a generative engine as retrieval plus synthesis. AIO's scope note records all three senses (absorbable-by-an-LLM, Google-AI-Overview-specific, and using-AI-in-your-own-workflow) because an assessment that uses the term must say which it means.

**The S5 guard, and the case it exists for.** The extractor's `aliases` list is not always an alias list: it asserts `AI-ready data → high-quality data`, an equivalence between two things this corpus must keep apart — §3a of the previous task exists because that phrase is a homonym. A model-asserted alias is refused when its normalised form is already the **preferred label of a different term**. **749 aliases refused** on that rule.

**A defect made and corrected inside this session, visible because the log is append-only.** The first seed emitted 1,606 terms *before* `term_added` carried `node_labels`, making every graph-derived term label-agnostic and visible to every blocking scope — the cross-label merge §1.3 exists to refuse. The log cannot be edited, so all 1,539 are **deprecated in place**, each naming its label-scoped replacement, and the epoch note carries an append-only correction. A regression test (`test_no_active_graph_derived_term_is_visible_to_every_blocking_scope`) asserts against the live vocabulary so it cannot recur. The SKOS export carries all 3,485 terms with `owl:deprecated` on the retired ones; 1,946 are active.

**`normalize` is stronger than `collapse.canonical_key`, deliberately and in one direction.** NFKC → casefold → punctuation-to-space → whitespace collapse → conservative per-word plural fold. It is **not** a stemmer: Porter (1980) takes `readiness` to `readi` and would collapse `AI readiness` into `AI ready`, which §3a established are different senses. The plural fold carries a **stated closed exception list** (`alias`, `bias`, `analysis`, `readiness`, …) rather than a suffix heuristic, because an over-fold is a silently wrong merge and an under-fold is a candidate the band still catches. `canonical_key` was not touched — it is the instrument the registered `flip` series is bound to.

### §1.3 Deterministic linking

| | |
|---|---:|
| linkable nodes (labels with a `name` some CQ collapses on) | **13,977** |
| auto-linked at the upper threshold | **6,518** (46.6 %) |
| candidate band, cosine ∈ [0.80, 1.0) | **137** |
| auto-rejected below 0.80 | **7,322** |

Blocking is on the KG label. Embeddings are `all-MiniLM-L6-v2`, L2-normalised — **the model this repo already uses** (`scripts/t1_build_index.py`, 5,164 corpus chunks), so there is one embedding space in the repo; `bge-large` is also cached here and would have shifted the whole cosine distribution, making the pre-registered 0.80 mean something different.

Cosine distribution over the 7,459 unlinked nodes (0.1-wide buckets): 0.3→504, 0.4→1,613, **0.5→2,286**, 0.6→1,877, 0.7→782, 0.8→270, 0.9→59. The mass sits at 0.5, well below the threshold, which is why the band is small.

**`Measure` and `Practice` are excluded, for a measured reason.** **Not one** of the 1,429 `Measure` nodes or the 1,347 `Practice` nodes carries a `name` property at all — they are keyed by `id` and carry only `grounding_span` and provenance. Including them would have grouped 2,776 nodes on a property that does not exist and reported a confident zero.

### §1.4 The loader resolves at write time

`build_projection.py` projects `Term` nodes from the vocabulary log, hoists one alias index per label, and on node creation writes `RESOLVES_TO` on a hit or `unresolved: true` on a miss. **Deterministic links are recomputed; judged links are replayed from their events** — the derivation must not be stored, or the log disagrees with itself the moment the vocabulary changes.

**Two defects found by running it, both fixed with tests written first:**

1. **`unresolved: true` was set on nameless nodes.** `Claim` (6,776), `Definition` (1,974), `Measure` (1,429), `Practice` (1,347) carry no `name` and can never resolve; flagging 11,526 of them made the residue read almost three times its real size.
2. **292 nodes carried two `RESOLVES_TO` edges.** A node is asserted once per chunk that mentions it and the extractor's spelling drifts between assertions — `scientifc integrity` and `scientific integrity` on one key. Resolving per assertion wrote both edges: the ambiguity `vocab.resolve` refuses at the term level, reappearing at the node level. Resolutions are now accumulated and written once after the pass; **283** nodes are refused as ambiguous across their own assertions, and the pass makes ~14,000 round-trips instead of 30,144.

Final: **6,408 resolved + 7,569 unresolved = 13,977**, exactly the linkable count.

## §2. Phase B — the clerical band

### §2.1 Calibration and ceiling

50 stratified pairs on `claude-opus-5` (declared 2,100,000, priced at the `judge` floor because no measured rate for this prompt existed — which is what a floor is *for*). Measured **30,765.9 tokens/pair**.

**Ceiling = 137 × 30,765.9 × 1.15 = `vocab_linking_tokens_declared` 4,847,174**, against §2.1's 25M stop threshold. Notably the floor-priced figure for the same work is 4,932,000 — **within 2 % of the measurement**, the first case in this repo where floor and measured rate nearly agree, because a judge call is small and uniform where an extraction call is neither.

### §2.2 Decisions, and the κ gate

The prompt is derived from the **adversarial-review baseline rubric v1.3.0**; every decision record stamps `rubric_version` and the project-local overlay `entity-linking`. Three rubric rules do real work: **§2 anti-anchoring — the cosine is withheld from the prompt entirely**, because the band was *selected* by cosine and showing the judge the selector invites ratification (the rubric's own calibrated failure is `cos=0.917` driven by shared boilerplate); §3 grounding — both spans quoted verbatim; §1 role — a clean `different` is a real answer.

| verdict | n |
|---|---:|
| different | **87** |
| same | 48 |
| uncertain | 2 |
| **accepted** (`same`, confidence ≥ 0.80) | **45** |

The judge earned it. It refuses pairs that merely share a grounding span — *"manual rewrites" → "annotation"*, cosine 0.806: *"Both node and term share the identical span … but with"* different denotations; *"numeric values" → "GPT-4"*, cosine 0.929, rejected at confidence 0.98.

**Cohen's κ = 0.979** (`vocab_calibration_kappa`), observed agreement 0.99, chance 0.519, over 100 stratified decisions rated independently by `claude-fable-5-1` — different model, hermetic empty cwd so no repo context, one pair per call so it cannot infer a distribution. **Gate 0.60: PASSED**, so the links were written.

**The caveat is on the Result's face and belongs here too:** two models of one family answering an identical prompt one pair at a time will agree about *prompt determinacy* as much as about truth. This κ bounds rater idiosyncrasy; it does not establish correctness. The single disagreement is a genuinely arguable version-vs-standard question (`W3C Data Catalog Vocabulary Version 3` → `Data Catalog Vocabulary (DCAT)`: Opus `different` at 0.72, "a narrower species"; Fable `same` at 0.90, "a version is an edition of the standard").

### Spend

| run | ceiling | settled |
|---|---:|---:|
| `vocab_link_opus_2026-09-05` (calibration, 50) | 2,100,000 | 1,538,297 |
| `vocab_link_opus_band_2026-09-05` (remaining 87) | 4,847,174 | 2,680,832 |
| `vocab_link_fable_2026-09-05` (κ sample, 100) | 3,541,540 | 3,151,732 |
| **total** | | **7,370,861** |

All 137 pairs decided exactly once, 0 duplicates, 0 unparsed answers. Measured 30,796 tokens/pair against 30,766 predicted from the calibration batch — **0.1 % out**.

**One operational failure, reported because it cost a run.** The band run crashed with `Exec format error: 'claude'`. Cause: `/opt/homebrew/bin/claude` was installed at 14:08 mid-session as a broken symlink to `claude.exe`, and my own `export PATH="/opt/homebrew/bin:…"` shadowed the working CLI. My mistake — the prepend was unnecessary; the strand extraction earlier had used the default PATH. Fixed by removing it. No tokens were lost (evidence-on-disk resume).

## §3. Residue and epoch 2

| | |
|---|---:|
| `vocab_residue_unresolved` | **7,414** |
| unresolved name groups | 7,403, of which **7,440 surface forms are singletons** |
| `vocab_e2_proposed` (recurring in ≥ 3 documents) | **1** |

Written to `ontology/vocabulary_proposals_epoch2.yaml`, **not promoted** — §3 is explicit that promotion is a scheduled cadence.

**One proposal, and the reason the number is one is structural rather than disappointing.** The epoch-1 seed already promoted every name recurring across two or more nodes, so a name can only survive into the residue at three documents if it is **ambiguous**. It is: `DCAT-US` is claimed both by the curated `air:dcat` (which lists it as an alias) and by the graph-derived `air:standard/dcat-us`, and the corpus treats DCAT-US as a standard in its own right across `datahub-mlmu-25`, `dcat-us-3-dataset-schema` and `doe-data-cards-standardized-metadata-2026`. **The curated alias is wrong and epoch 2 should split them** — the residue mechanism found a defect in the seed, which is exactly what it is for.

## §4. Acceptance — three views, v1 and v2

### §4.1 v1 unchanged at `369d717` (`git diff` empty), three views

| aggregate | 2026-09-05 (2 views) | 2026-09-05c (3 views) |
|---|---:|---:|
| `A_raw` | 0.923077 | 0.923077 |
| `A_collapsed` | 0.884615 | 0.884615 |
| **`A_canonical`** | — | **0.884615** |
| `flip` (raw→collapsed) | 0.307692 | 0.307692 |
| **`flip_canonical`** (raw→canonical) | — | **0.307692** |
| `C` collapsed / canonical | 125 | 125 / 125 |

**ACCEPTANCE: FAILED, both criteria.**

| criterion | required | measured |
|---|---|---|
| `flip(raw→canonical)` | < 0.10 | **0.307692** |
| every enumeration CQ `yes` in canonical | all 13 | **CQ-21 is `partial`** |

**Why, and it is not that the vocabulary underperformed.** `flip` = canonical `yes` **and** (raw `no`/`partial` **or** `misleading_raw`). `misleading_raw` is computed from how much the **raw** view shrinks — and the raw view is one node per document per mention *because DD-020 requires it*. Canonicalising cannot lower it. **A statistic that can only be moved by deleting per-document nodes was adopted as the trigger for entity resolution, and cannot be satisfied by any entity resolution that respects DD-020.** The §1.5 gate and DD-020 contradict each other. The rule stands as pre-registered; naming which of the two moves is the next task's job, not this one's.

CQ-21's `partial` is the known harness defect, repaired in v2.

**What the canonical view is actually worth, since `flip` does not show it.** It is *narrower* than the collapsed view on several questions — CQ-10 **383** canonical groups against 377 collapsed, CQ-06 9 against 8, CQ-13 3 against 2, CQ-18 118 against 115 — and that is the honest direction: the collapsed view unions on the extractor's own **unvetted** `aliases` property, while the canonical view unions only what a term claims and refuses every ambiguity. Where the collapsed view looked better, it was over-merging. It is narrower where the vocabulary did real work: CQ-22 32 against 35, CQ-24 5 against 6, CQ-20 30 against 31.

### §4.2 The v1 contamination — one edge type changed a byte-identical query

**CQ-21 went from 37 raw rows to 51.** Its query traverses `OPTIONAL MATCH (s)-[r]-(other)` — untyped — so the 19 `RESOLVES_TO` edges the vocabulary added to those Standard nodes are returned as things the corpus says about robots.txt. They are infrastructure. Row breakdown: `RESOLVES_TO` 19, `CONSUMES` 16, `BUILDS_ON` 9, `IMPLEMENTS` 4, null 3.

v1 is left contaminated and reported that way — repairing it would break the frozen series. v2 excludes the type. **The lesson is general: a new edge type changes every untyped traversal in the graph**, and this repo has at least one.

### §4.3 v2 — two harness repairs and CQ-27

`assessment/cq/cq_set_v2.yaml`, 27 questions. **24 are byte-identical to v1** (verified programmatically); three changed:

* **CQ-13** `collapse_on: concept → claim`. The question asks for a list of *claims*; collapsing on the shared subject grouped 11 distinct interoperability claims into 2. Collapsed goes 2 → **11**, matching raw. `partial → yes`.
* **CQ-21** `collapse_on: standard → other_text`, **and** the untyped traversal now excludes `RESOLVES_TO`. Raw back to 37, collapsed 8 → **32**. `partial → yes`.
* **CQ-27** NEW — the re-scoped G1 question from Issue `cfe9eaf7`.

| aggregate | v1 (09-05c) | v2 |
|---|---:|---:|
| n | 26 | 27 |
| `A_raw` | 0.923077 | 0.888889 |
| `A_collapsed` | 0.884615 | **0.925926** |
| `A_canonical` | 0.884615 | **0.925926** |
| `flip` | 0.307692 | **0.296296** |
| `misleading_raw_count` | 9 | **7** |
| rule branch | ER is P0 and blocks probe design | **ER scheduled, not blocking** |

**The two harness repairs alone moved `flip` below the 0.30 threshold** — 0.308 → 0.296 — which changes the §1.5 branch. That is worth stating flatly rather than claiming as a win: **a decision rule that a collapse-column fix can flip is measuring the harness at least as much as the graph.** It reinforces §4.1's finding rather than softening it.

v2 acceptance also fails: `flip_canonical` 0.296296, and CQ-27 is `no`.

### §4.4 CQ-27 — the question could not be asked, and that is the finding

**CQ-27 returns 0 rows, and is scored `no`, not `yes`, by the criterion written before it ran.** That criterion says an empty answer is informative *only if both legs are live*:

* **Leg 1 is live** — 11 `Instrument-[:MEASURES]->Concept` rows on uncertainty terms (`Cohen's Kappa → inter-rater reliability`, `benchmark → diagnostic uncertainty`, `Multi-Signal Uncertainty Classification and Ranking Prompt → uncertainty level`).
* **Leg 2 is dead by construction.** 55 Frameworks match the readiness/maturity name test, 0 by `ABOUT` edge — and **there are ZERO relationships of ANY type between a `Framework` node and an `Instrument` node anywhere in the graph**, across 506 Frameworks and 502 Instruments.

**It is a schema gap, not an extraction gap.** No edge type in `kg/schema.yaml` has domain `Framework` and range `Instrument`: `operationalizes` is Instrument→Construct, `measures` is Measure|Instrument→Construct|Concept, `uses_measure` is Instrument→Measure, `has_component` is Framework|Concept→Concept, `extends` and `builds_on` stay within their own kinds. The parser's whitelist would reject such an edge even if the model asserted one.

**The re-scoped G1 claim from Issue `cfe9eaf7` therefore remains UNTESTED** — and now for a named, measured reason rather than an absent question. Registered as Issue **`2a2b6461`** (high/medium), linked `ANNOTATES` to all ten `cq_v2_CQ_27_*` Results. Closing it needs a schema change, which invariant 4 routes through the schema doc's §6 review and never a silent edit.

## §5. Integration

| check | result |
|---|---|
| `python -m pytest tests/` | **832 passed** (768 + 64 new) |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** (24,387 events readable) |
| `cq_set_v1.yaml` vs `369d717` | **diff empty** |
| v2 questions differing from v1 | **exactly CQ-13, CQ-21** (+ new CQ-27) |

**Registered.** 7 Scripts (`seed_vocabulary`, `link_vocabulary`, `link_judge`, `vocab_calibration`, `vocab_residue`, `export_vocabulary_skos`, `register_vocab_results`); 7 DataFiles, all `snapshot: true`; **640 Results** — 16 `vocab_*`, 307 `cq_v1_*_2026-09-05c`, 317 `cq_v2_*_2026-09-05`; DD-044; Issue `2a2b6461`; ResearchTask `93a628e8` **superseded** with `superseded_by` → this task; seldon ResearchTask `af389420` for the §1.1 follow-up.

## §6. Premises contradicted, and what a reader should not over-read

1. **`flip` cannot measure entity resolution under DD-020.** §4's acceptance criterion was unsatisfiable as written. This is the task's main result.
2. **The §1.5 branch is flippable by a collapse-column fix** — 0.308 → 0.296 from repairing two `collapse_on` values, with no change to the graph.
3. **The canonical view is sometimes *narrower* than the collapsed view.** The collapsed view was over-merging on unvetted model aliases; the task's framing implicitly expected canonical ⊆ collapsed.
4. **§1.2.4 says "the 1,486 exact-name Concept groups"; the vocabulary reads six labels, not one.** §4's own acceptance requires enumeration CQs over `Instrument`, `Standard` and `Platform`, which a Concept-only vocabulary cannot touch. Under `vocab.normalize` the Concept groups number **1,548**, not 1,486 — the stronger normaliser finds 62 more than the diagnostic's weaker key.
5. **κ = 0.979 is not evidence of correctness.** Two models of one family, one prompt, one pair per call.
6. **`Measure` and `Practice` have no `name` property at all** — 2,776 nodes that no name-based vocabulary can reach.
7. **A vocabulary defect was made and corrected inside this session** (label-agnostic terms), visible only because the log is append-only. 1,539 terms are deprecated in place rather than deleted.
8. **My own PATH prepend broke a run.** A broken `claude` binary appeared mid-session at `/opt/homebrew/bin`; I had shadowed the working one unnecessarily.

## §7. Out of scope, untouched

Term-level merges across the vocabulary; the 41 `no consumer` deferrals; the memo and the deck (Issue `cfe9eaf7` still decides those, and CQ-27 did not answer it); probe design; any retrieval index over raw text. Epoch 2 is proposed and not promoted.
