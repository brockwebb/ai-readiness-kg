# KG construction methodology — ai-readiness-kg

**Status:** v1, 2026-08-27. Describes the pipeline as it exists after tasks d2756bd1 (spend guard), cd8449de (overnight burn), ea7dd3bd (pilot finish), and the design of `2026-08-27_chunked_pilot.md`. Numbers cite their task or verdict file; the graph is authoritative where they disagree.
**Purpose of the graph:** the validity layer under the FSS AI-readiness survey — definitions, constructs, instruments, and the crosswalk survey item → construct → definition → primary source. Every assertion citable by a stranger. That purpose sizes the graph: the crosswalk is hundreds of curated edges hanging on validated Instrument/Definition nodes, not thousands of bulk-extracted relations.

## 1. Three things that are not the same

- **Admission** — a document enters the corpus. Path: inbox → register → `manifest_add` event; since the Stage-0 rewire `manifest.json` is projected from the dixie evidence ledger. Provenance survives as `primary_url + content_hash`. Rejections are quarantined with a reason, never deleted. Admission is rule-based (AUTH-2 etc.); an "off-construct" flag is a signal for the operator, not a verdict.
- **Request** — a document is asked for extraction under a named profile and model epoch (`extraction_request` event, task 00968603, in progress). Derived `extraction_state` includes `stale` when the profile or model behind an extraction is superseded.
- **Extraction** — a model run under a sha-pinned profile (`scripts/run_profiles.yaml`) and a pinned model (`kg/extraction/model_config.yaml`). Model identity is a gate: a response reporting a different model is discarded and the run STOPs. A model change is a new instrument; items from different epochs are never pooled.

Conflating these produced two of this month's incidents (extractions counted against the wrong epoch; triage adds assumed to be extracted).

## 2. Write barriers

- **No grounding span, no write.** Every node and edge carries a verbatim span validated at parse (NFKC, de-hyphenation, whitespace collapse, case-sensitive, not fuzzy). Misses are quarantined at birth. The `grounding_zero_ungrounded` gate is absolute zero. Since v0.3.4, Instrument attributes carry per-attribute spans; uncovered attributes are nulled, not guessed.
- **Schema whitelist.** `kg/schema.yaml` is the only type catalogue; unknown edge types route to `proposed_relationships` staging with a `diversion_reason` (closed list, ADDENDUM-06).
- **Harness owns provenance.** Model-emitted ids, timestamps, model names are stripped and re-stamped.
- **Gate before wire.** No repair or restoration touches the projection until its acceptance gate passes on a held-out sample (restoration v2: 100-item class gate ≥ 0.90). The a2d3fb42 class was REVERSED at 0.78 and stays unprojected.

## 3. Pilot gate before bulk

No prompt, profile, model, or unit-of-extraction change reaches bulk without a five-document pilot judged by the probe protocol against pre-registered thresholds:

- Fabrication share of atomic facts **F_upper < 0.10** per stratum (Wilson 95%).
- Item-level faithful **≥ 0.70**.
- Precondition: **pooled ≥ 20 admitted items per stratum**; strata are judged and unlocked independently (ADDENDUM-05 §2).

Thresholds were ported from fss-policy-kg realized values and are operator decisions written before data. They have not moved and do not move. A failed gate triggers investigation and a new pre-registered pilot, never retuning.

## 4. Probe protocol (measurement instrument, versioned)

Decompose each admitted item into atomic facts; two raters (primary `claude-opus-4-8`, secondary `claude-sonnet-5`, neither the extractor) judge entailment against the grounding; Dawid-Skene aggregation; batch size 10 (κ 0.915 batch-vs-single, task 68426971); self-consistency κ 0.957. Rater agreement on tonight's Instrument judge 1.00 / 0.97. Two protocol defects found 2026-08-27 and to be versioned before reuse: (a) the decomposer redistributes coordinated phrases so that every content word is in-span but the fact is scored non-entailed (14/34 Instrument non-entailments); (b) resume logic re-decomposed already-labeled items (fixed, 156a91c).

## 5. Spend guard (DD-022)

Reserve-then-settle at the single choke point (`model_stub.invoke`); flock ledger `state/spend_ledger.jsonl`; per-run ceiling declared by the runner (`--ceiling-tokens`, required — undeclared runs are refused); daily band `controls.yaml spend.daily_tokens` (standing 55M). Two scopes, both refuse cleanly; refusals are ledger events. A ceiling is derived from the ledger's per-class running mean and a dry run, never from memory or a prior model's cost. Raising the band is operator touchpoint #1 and is scoped to a task, reverted at its close.

## 6. Findings that shape the method (2026-08-27)

**6.1 Whole-document extraction was an untested design rule and it is wrong.** Schema §5 specified one call per document. Under Opus 5 that produced 108–158K-token outputs on 3/4 pilot docs, forced a per-layer fallback (three resumed turns re-paying the document), and doubled per-doc cost (single-pass 399–426K; fallback 866K–1,331K; extraction-only mean 785K/doc, `pilot_finish` RESULT). The literature predicted the quality effect: extraction yield falls as chunk size grows (Edge et al. 2024, ~2× entities at 600 vs 2400 tokens) and LLM relation extraction degrades with relation count because output formatting dilutes attention (Gajo et al. 2026). Structure-aware chunking outperforms fixed-size for both entities and relations (ChemRxiv 10.26434/chemrxiv.10001546). The standard is section-bounded, paragraph-integral chunks, real-tokenizer cap, ~100-token overlap, breadcrumb context, chunk-local extraction with post-hoc entity resolution (Neo4j LLM Graph Builder; docling-graph). This project's own predecessor (Wintermute) extracted at chunk level. The chunked arm is `2026-08-27_chunked_pilot.md`.

**6.2 Bulk semantic-edge extraction does not clear the gate and is unlikely to.** Semantic stratum: 0.607 entailed under v0.3.5 (needs 0.85 for the evidence-set path); **live kernel-era edges 0.61, 23/35 non-entailed are fabrication.** Two prompt revisions and a model change did not move it. Endpoint co-occurrence near a predicate cue predicts faithfulness at 0.51–0.67 — the distant-supervision false positive (Mintz 2009; Riedel 2010): co-occurrence is not assertion. Cross-chunk relations remain an open research problem (CrossAug 2026). Disposition, same as Wintermute G4: `has_component`/`subtype_of`-class edges are **demand-pull** — adjudicated one at a time with the grounding span captured at adjudication. Live edges from the kernel epoch carry a `faithfulness_epoch` flag and are not cited as validated. The chunked pilot may revise this if its semantic stratum clears the gate; that is the pre-registered test, not an expectation.

**6.3 Instrument stratum fails on attribute quoting, not admission — CONFIRMED, and the failure was the instrument's own.** v0.3.5 fixed admission (pooled 24 ≥ 20). F_upper 0.158, item-faithful 0.292 over 89 facts; 26/34 non-entailments are `method` spans truncated — 14 a probe-protocol artifact (§4a), 13 the model quoting a fragment cut mid-noun-phrase. Both were fixed in both arms before the chunked comparison was judged. **Result (2026-08-29, ADDENDUM-01 §1): on the same banked extraction, with no re-extraction, the same two raters and the same thresholds, the whole-document arm re-measures F_upper 0.0487 / item-faithful 0.917 and the chunked arm 0.0458 / 1.000 — both PASS.** The diagnosis was right, and the FAIL was never a property of the extraction: it was how the probe cut the spans it judged. The verdict had already propagated into DD-023 as measurement (3) before the error was found (DD-023 ERRATUM). Standing consequence: §7.6.

**6.4 Restoration is repair on a layer that measured 0.61.** Restoration v2 spent ~30M of one day's band. Stage 2 completed 2026-08-28T01:14Z (5,554 judged, 4,021 accepted) and its class gate passed at 0.90 (n=130, threshold ≥ 0.90). Relocation and re-judge remain stopped and do not proceed until the graph's edge layer has a passing extraction unit; wiring the passed class is a separate task. Fix-on-contact without a stop condition is how a cleanup becomes a campaign.

**6.5 The emission contract, not the unit, is the cost driver.** Interim, 44/128 chunks (2026-08-27 pause): chunked extraction under the exhaustive-verbatim contract settled 65,637/chunk — ~2.1× the whole-document arm projected — with 33–46K-token outputs against 1,500-token chunks and 75.5% of emissions quarantined (`span_partial`, much of it pypdf source damage). Cheap production pipelines (Neo4j Graph Builder, GraphRAG) emit name/type/tuple with provenance as a chunk pointer, on mini-class models, unvalidated. The gate here measures faithfulness of admitted items and does not require model-typed quotes: v0.3.7 replaces quotes with shortest-unique anchors located deterministically by the harness, replaces exhaustiveness with salience plus one gleaning pass, enforces closed lists at parse, reconciles entity types at merge, and re-converts source text with a layout-aware parser. The extractor model becomes an empirical question the judge answers (`chunked_pilot` ADDENDUM-01 §3).

**6.6 The semantic stratum's gate was unreachable, not failed.** Both arms landed at 20–21 admitted semantic edges. `probe_decompose` emits one fact per edge, so n_facts = n_items, and Wilson-95 puts `F_upper < 0.10` out of reach below n = 35: a perfect zero-fabrication result returns 0.1611 at n = 20. The pre-registered precondition (≥ 20) was inconsistent with the pre-registered threshold, so the stratum could only ever FAIL. Recorded, not judged; the general rule is DD-026.

## 7. Process rules (each is a logged defect from this month)

**7.6 A gate verdict may not enter a design decision until its instrument has been positive-controlled.** §7.5 requires a seeded known-bad before a monitor is trusted. The judge is a monitor. The 2026-08-27 Instrument FAIL (F_upper 0.158 / item-faithful 0.292) was an artifact of the probe's span selection, stood for two days, and was cited as measurement (3) of DD-023 before the fixed probe re-measured the same banked extraction at F_upper 0.0487 / 0.917 PASS. Cost of the miss: a withdrawn measurement inside a live decision. The rule: a verdict cited in a decision names the instrument version that produced it and the positive control that was run against that version.

**7.7 A dry run is a read.** `probe_decompose --dry-run` wrote the deterministic half of the fact set, which marked every item done and permanently suppressed the model half of the run it was estimating for. The estimate poisoned its own subject, and the first judge call of ADDENDUM-01 §1 was paid on a fact set missing every free-text proposition. Any `--dry-run`/`--estimate` path must leave zero state behind, and must be tested for it.

**7.8 A converter change is not a fidelity fix until the damage is shown to be the converter's.** DD-023 attributed the chunked pilot's 75.5% `span_partial` quarantine rate to pypdf source damage and prescribed re-conversion with a layout-aware parser. Measured 2026-08-29 on the named instance: Docling and pypdf extract the **identical** truncated token `Heterogeneous Euclidean-Overlap Metri` from the same bytes. The missing character is in the PDF's own text layer, so re-conversion cannot repair that class. Docling still earns its place — it recovers layout, tables and headings that pypdf flattens, and on the 5-document sample it yields 4–24% more text — but the quarantine-rate remedy attributed to it does not follow. Before naming a component as the cause of a defect, run both candidates on the same bytes.

**7.9 A guard test must fail when its own guard is removed.** The first version of the wrapper-record test used a mismatched year, so the year check rejected the candidate and the test passed with the wrapper blocklist AND the length-ratio bound both deleted. It was measuring the year check. Every guard test holds all other conditions satisfied so only the guard under test can produce the rejection, and the mutation run is what proves it.

**7.10 Availability states never halt lanes; only validity gates halt work.** (ADDENDUM-02 to `2026-08-29_corpus_t0_t1_substrate`, binding.) A provider quota, an unavailable parser, a Cloudflare block and a degraded conversion are **availability** facts: they are recorded as retryable states, the lane proceeds on what exists, and derived numbers ship labelled with their coverage and are recomputed automatically when the state clears. A failed pre-registered gate is a **validity** fact and stops the lane. Conflating the two is how a rate limit became a permanent statement about 159 documents (§7.11).

**7.11 A transient failure may never be written down as a finding.** The T0 harvest recorded HTTP 429 as `bibliographic_partial` — "this document has no bibliographic record" — for 159 documents. The number was retracted. `bibliographic_partial` is a claim about the world and is now writable by exactly one code path that requires every provider to have answered cleanly; anything else is `harvest_error`, which asserts nothing and is retryable. Enforced by test, and the single-write-path rule is itself asserted by a test that reads the source.


1. **Prior art before any pilot.** A CC task that registers a pilot must carry a `prior_art` block with (a) external literature and (b) the internal-precedent search across Wintermute and Seldon decision logs. Missing block → refused at registration. "No prior art" is a claim requiring the search that failed. (Defect: whole-document unit, one week and ~60M tokens.)
2. **Estimate from the ledger before declaring.** Row counts, ceilings, per-doc costs come from a dry run or the ledger's running mean, never from a prior model's numbers. (Defects: "65 rows" vs 72; 4M ceiling vs ~9M needed; Lane 2 sized at 977K vs measured 785K.)
3. **Pooled-per-stratum preconditions.** "Document contains nothing" ≠ "prompt produced nothing." (Defect: per-doc conjunction precondition.)
4. **Absolute UTC for every wall stop and band roll.** (Defect: clock-time stops written for a night that had ended.)
5. **Verify product facts in platform docs before pinning a model.** Desktop product knowledge is stale by construction. (Defect: Opus 5 pin.)
6. **Guess vs measured revision.** A prompt change after a failed gate is forbidden when it is a guess and permitted when it follows a measurement with a pre-registered read. (Defect: "no revision tonight" rule misapplied.)
7. **`seldon cc complete` before RESULT; glob `_ADDENDUM*` before starting; report discrepancies, never reconcile.** (Defect: 7 tasks stuck at `proposed`; addenda missed.)
8. **Every Result artifact registered with `generated_by` and `computed_from` at creation.** (Defect: 39 Results with incomplete provenance, growing.)
9. **Work on a closed task is a new task.** Six addenda ran on cd8449de after its RESULT. (Defect: graph state diverged from work state.)
10. **Availability is a queue; validity is a gate.** Only faithfulness/acceptance gates may halt work. Missing, blocked, degraded, or partially-harvested sources are *states* (`acquisition_blocked`, `manual_download_needed`, `fidelity: degraded`, `harvest_error: retryable`) that (a) propagate on provenance so every downstream consumer sees them, (b) feed an operator pickup list ordered by `t2_priority`, and (c) never halt independent lanes. Degraded sources are indexed and extractable; their outputs inherit the flag; a clean copy arriving later appends a supersession event that marks exactly that document's derivations stale for re-processing. Holding a pipeline for a perfect copy is gate theater. (Origin: 2026-08-29 operator directive during T0/T1 build.)

## 8. References

Edge, D. et al. (2024). From Local to Global: A Graph RAG Approach to Query-Focused Summarization. arXiv:2404.16130.
Gajo, P., Rosati, D., Sajjad, H., Barrón-Cedeño, A. (2026). LLMs Underperform Graph-Based Parsers on Supervised Relation Extraction for Complex Graphs. arXiv:2604.08752.
Hierarchical vs fixed-size chunking for materials-science KG extraction (2026). ChemRxiv, doi:10.26434/chemrxiv.10001546.
TechRAG (2026). Evidence-Gated Multimodal Agentic RAG for Technical Literature Reasoning. arXiv:2606.01613, §5.3.
CrossAug (2026). Beyond Chunk-Local Extraction: Cross-Chunk Graph Augmentation for GraphRAG. arXiv:2605.28004.
Wadhwa, S., Amir, S., Wallace, B. (2023). Revisiting Relation Extraction in the Era of Large Language Models. ACL.
Mintz, M. et al. (2009). Distant supervision for relation extraction without labeled data. ACL. Riedel, S. et al. (2010). Modeling relations and their mentions without labeled text. ECML-PKDD.
Tan, Q. et al. (2022). Revisiting DocRED — addressing the false negative problem. EMNLP.
Neo4j LLM Knowledge Graph Builder — extraction pipeline documentation (chunking, HAS_ENTITY, post-hoc merge). docling-project/docling-graph — chunking-strategies.md.
Internal: DD-003, DD-007, DD-008, DD-019, DD-022; Wintermute G4 kill (2026-08-16); verdict files under `docs/research/2026-08-2[67]_*`.
