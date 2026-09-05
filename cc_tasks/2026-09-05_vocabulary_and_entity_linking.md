# CC Task — Canonical vocabulary and entity linking (replaces the ER task `93a628e8`)

**Date:** 2026-09-05
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Supersedes:** `93a628e8` (supersede it with reason "reframed as vocabulary-first; see this task" and `--superseded-by` this task's id once registered)
**Premise (registered):** `cq_v1_flip_2026-09-05` = 0.308, same eight CQs two runs running; `kg_diag_concept_dup_groups_2026-09-05` = 1,486 covering 4,722 nodes (41.3% of Concepts). Extraction of 795 Concepts moved `flip` by zero: the statistic tracks graph structure, not corpus size.
**Spend:** Phase A zero model spend. Phase B spends, ceiling from a measured calibration batch (DD-042). **Claude Max OAuth only.** Fable for the calibration rating (a separate model; used exactly as G1's calibration design uses it).

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. Why vocabulary-first, and the prior art (record as one DD entry, citations included)

The graph keys every node per document (DD-020) and never resolves identity across documents. Fourteen, now twenty-one, nodes named "AI readiness" is the direct result, and the CQ harness shows the cost lands entirely on enumeration questions. The fix is not a one-time dedup. It is a **controlled vocabulary that every mention resolves against at write time**, evolved as the corpus grows.

This is old, and the old versions were right but underpowered:

- **Controlled vocabularies / thesauri** — a curated list of preferred terms with aliases, broader/narrower links, and scope notes, and every new document indexed against it. Cutter (1876) *Rules for a Dictionary Catalog*; Library of Congress Subject Headings; standardized as ISO 25964-1:2011 and the W3C SKOS Reference (2009). Bottleneck: the human cataloguer.
- **Probabilistic record linkage** — decide whether two records refer to the same thing from a match weight over agreement patterns, with an upper threshold (auto-link), a lower threshold (auto-reject), and a clerical-review band between. Fellegi & Sunter (1969), *JASA* 64(328):1183–1210, built for census work. Bottleneck: the clerical band.
- **Pay-as-you-go integration** — seed a rough vocabulary, resolve against it, promote what recurs, deprecate what doesn't; never wait for a complete ontology. Franklin, Halevy & Maier (2005) "From databases to dataspaces", *SIGMOD Record* 34(4); Madhavan et al. (2007) "Web-scale data integration: you can only afford to pay as you go", CIDR.
- The formal-ontology detour (OWL alignment, committee vocabularies) routed around those two bottlenecks with formalism because judgment was unaffordable. It is now affordable: the LLM is the cataloguer and the clerical reviewer, with an independent second reviewer (Fable) for calibration, exactly as G1 already does for rating.
- The immediate design is the sift-kg three-layer pattern (github.com/juanceresa/sift-kg: deterministic pre-dedup → LLM-proposed merges with confidence → reviewable YAML), which is the above restated. Cited as the implementation precedent, not the origin.

**Machinery already built that this task uses, in plain terms:**

- **Seldon master/replica ontology, AD-017** (a single master vocabulary database, `seldon-ontology`, with numbered epochs; each project holds a read-only copy that `seldon ontology sync` refreshes; terms are added, aliased, and deprecated by appended events and never deleted, so anything that cited an older epoch still resolves). Built for Seldon's own research-lifecycle terms. This task decides in §1.1 whether it can host a *domain* thesaurus too.
- **`resolve_exercises` alias-first resolution in arnold-training** (look up a name in an alias table before doing anything fuzzy; unmatched names are reported, not guessed). Same pattern, different domain; copy the shape.
- **The CQ harness** (`assessment/cq/run_cq.py`: 26 pre-registered questions run in two views with a written pass criterion each; §1.5 of `2026-09-04_kg_diagnostic_and_cq_harness.md` is the decision rule). This is the acceptance instrument.
- **The G1 calibration design** (`assessment/results/g1_calibration_*`: Opus decides, Fable independently rates a sample, Cohen's κ reported, disagreements escalated as records). Reused for merge decisions.
- **DD-042 spend rule** (a ceiling is computed from a measured rate for the profile, never from the guard's first-call floor).

## 1. Phase A — seed vocabulary and deterministic layer (zero model spend)

### 1.1 Where the vocabulary lives — decide by inspection, report the choice
Read `seldon/ontology/` and AD-017. If the ontology module can hold a second, project-owned vocabulary (its own master DB, e.g. `ai-readiness-vocabulary`, with the same epoch/alias/deprecation events) **without adding terms to Seldon's own 51-term master**, use it. If not, model `:Term` nodes in the project graph with the same event shapes (`term_added`, `term_alias_added`, `term_deprecated`, `vocabulary_epoch`) and register a seldon ResearchTask to fold it into the ontology module later. Either way the vocabulary exports as **SKOS Turtle** (`skos:prefLabel`, `skos:altLabel`, `skos:broader`, `skos:narrower`, `skos:scopeNote`, `dcterms:source`) to `ontology/ai_readiness_vocabulary.ttl`, so it is a standard artifact and not a private one.

### 1.2 Seed — the 80% list, sourced
Every seed term carries a `dcterms:source`. Sources, in order:
1. The framework's constructs and indicator groups (`docs/crosswalk/assessment_protocol.md`, `docs/crosswalk/usafacts_operationalization_skeleton.md`).
2. The discovery-stack standards already in the graph (robots/RFC 9309, sitemaps, RFC 8615 well-known, schema.org Dataset, DCAT, data.json, content negotiation, PIDs) and the frontier candidates (MCP, llms.txt).
3. The search-optimization lineage the operator wants provenance on: SEO → AEO → GEO → AIO, with dated first-use where the corpus or a web search gives one; scope notes must say what each term claims to optimize *for*. Zero model spend: web search is permitted for dates and canonical sources; cite them.
4. The 1,486 exact-name Concept groups (after NFKC normalization, casefold, punctuation strip, and singular/plural fold) — each group becomes a candidate term with the group's members as aliases and the most-cited grounding span as the draft scope note.
5. The `aliases` property already on 10,104 Concepts — fold into altLabels.
Register the seed as `vocabulary_epoch_1` with a count Result `vocab_e1_terms`, `vocab_e1_aliases`.

### 1.3 Deterministic linking (Fellegi–Sunter, zero spend)
- **Blocking**: same label (Concept↔Concept, Instrument↔Instrument, …) and normalized-name overlap or shared alias.
- **Upper threshold — auto-link**: normalized name identical, or name identical to an alias of exactly one term. Emit `RESOLVES_TO` edges from every such node to its term. Never delete or relabel per-document nodes (their provenance is the point).
- **Candidate band**: local embedding similarity (sentence-transformers, on-machine, zero API) between node name+span and term prefLabel+scopeNote, cosine in [0.80, upper). Register `vocab_candidate_pairs` — **this count is the unit count for Phase B's ceiling.**
- **Lower threshold — auto-reject**: below 0.80, no action; the node stays an open, unresolved node flagged `unresolved: true` (the residue).
- Tests: a fixture with known groups yields known link counts; a node with two equally plausible terms is *not* auto-linked.

### 1.4 Loader change — resolve at write time
`scripts/build_projection.py` (or the ingest path that creates KG nodes): on node creation, alias-first lookup against the current vocabulary epoch; hit → `RESOLVES_TO` edge written in the same event; miss → `unresolved: true`. Unresolved nodes are never guessed. Test with a synthetic chunk containing one known alias and one novel term.

## 2. Phase B — the clerical band (spends)

### 2.1 Calibration batch and ceiling
Take 50 candidate pairs (stratified across labels and similarity). Run the merge-decision prompt with Opus: inputs are both grounding spans, both names, the candidate term's scope note; output `same | different | uncertain`, confidence in [0,1], and a one-sentence reason quoting both spans. Measure tokens per pair on the ledger. Ceiling = measured rate × `vocab_candidate_pairs` × 1.15; register `vocab_linking_tokens_declared`. If the ceiling exceeds 25M tokens, stop and report with the number; do not run.

### 2.2 Decide, calibrate, then apply
- Run the band. Auto-accept `same` with confidence ≥ 0.80 → `RESOLVES_TO`. Everything else stays unresolved. No merges of terms into each other in this pass (term-level merges are a vocabulary-epoch change, §3).
- **Before writing any edge from this pass:** Fable independently rates a stratified sample of 100 decisions (same prompt). Report Cohen's κ. **Pre-registered gate: κ < 0.60 → write nothing, report, stop.** κ ≥ 0.60 → apply. Disagreements are written as records in `assessment/results/vocab_calibration_disagreements_<date>.md` for the operator, informational only.
- Register `vocab_linking_tokens_productive`, `_wasted`, decision counts by class, κ.

## 3. Residue and epoch 2
Unresolved nodes whose normalized name recurs in ≥3 documents become **proposed terms**; write them to `ontology/vocabulary_proposals_epoch2.yaml` with sources. Do not promote in this task; promotion is a scheduled cadence, not a per-item review. Register `vocab_residue_unresolved`, `vocab_e2_proposed`.

## 4. Acceptance — the harness, third view
- Add a `canonical` view to `run_cq.py`: queries traverse `RESOLVES_TO` to the term and aggregate there. Keep `raw` and `collapsed` unchanged.
- Fix the recorded harness defect: `collapse_on` for list questions (CQ-13, CQ-21) collapses on the listed item, not the shared subject. This edit is allowed now because the before/after series is closed at `2026-09-05`; record it as `cq_set_v2.yaml` with `supersedes` on the two changed CQs, plus the re-scoped G1 question from Issue `cfe9eaf7` as CQ-27.
- Rerun **v1 unchanged** (`369d717`) in all three views, then v2. **Pre-registered acceptance:** `flip` computed raw→canonical < 0.10 on v1, and every enumeration-category CQ (`measure_lookup`, `instrument_coverage`, `discovery_stack`, `frontier_candidate`) `yes` in the canonical view. Report per-CQ and the §1.5 branch on the canonical `flip`. Failing acceptance is a result, not a reason to loosen it.

## 5. Integration
Tests green (`tests/`, `assessment/`); `seldon verify` clean; Scripts, DataFiles (snapshots), Results by name; DD entry for §0 with every citation above; `93a628e8` superseded; `cc complete`; commit and push with the ledger delta and the `.ttl`.

## 6. RESULT must report
§1.1 choice and why; seed counts by source; deterministic link counts and candidate-band size; calibration rate and ceiling; decision counts, κ, gate outcome; residue and proposals; the three-view CQ tables for v1 and v2 and the acceptance verdict; premises contradicted.

## 7. Out of scope
Term-level merges across the vocabulary; the 41 deferrals; the memo and deck (Issue `cfe9eaf7` decides those on CQ-27's answer); probe design; any retrieval index over raw text.
