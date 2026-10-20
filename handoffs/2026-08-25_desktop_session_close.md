# Handoff — Desktop session close, 2026-08-25

**Scope:** ai-readiness-kg (plus FSS deck deliverable). Graph is the source of truth; verify counts against the ledger, not this prose.

## State on close

- Graph: 134 docs, two epochs, schema v0.3.2, composite-key projection (DD-020, un-fused 600 cross-doc ids). Gates green, grounding 0. Post-repair: 4,293 spans relocated (validated ~0.9), 1,169 span_unrepairable, ~3,428 repair tasks resumable (`scripts/batch_repair.py --shard I/N --redo-unrepairable`).
- **Attribute restorations: entire class REVERSED** by pre-registered gate (0.780 < 0.90; batch-012). Restorations were never projected (gate-before-wire), so projected state stayed null throughout. Failure mode: cheap model returns related-but-not-entailing verbatim passages. See 2026-08-23_batched_repair_resume_RESULT.
- TrustGraph benchmark v2: verdict harvest-components (R=0.33, F_tg=0.126 vs ours 0.079, their edges 0.225). Deployed fine (17-min backend vs their LlmService contract) — infra-weight objection dead by measurement. Harvest: extraction-time ontology validation (killed 253 over-proposals live). Fork local; upstream-PR decision is Brock's (federal outside-activity policy check first).
- Probe verdicts standing: strata Instrument (both epochs) and edge:semantic:kernel-v03 = reextract_required under corrected prompts (requirements in 2026-08-22 probe decision doc).
- Known defect, unfixed: budget ceiling enforcement (22.03M vs 12M per-shard misread; then 8.11M vs 8M poll lag). DD-019 specifies shared counter; the preemptive, mutation-tested guard is NOT yet implemented. Nothing burns before it lands.

## Registered, ready to run

- **7456614d** `cc_tasks/2026-08-24_source_triage.md` — zero-spend triage of the FSS research group's source list + SEO/AIO-lineage gap harvest; construct_arm tagging (schema v0.3.3); rule-based manifest adds; operator download list for 10 max.gov decks → `corpus/staging/inbox/maxgov/`. CC needs the source list pasted with the execute line (it is not in CC's context). Off-construct flag to review after: Census CES-WP-26-25.

## Next tasks to author (priority order; none written yet)

1. **Preemptive budget guard** (small, first): shared spend counter checked before each dispatch; mutation test = seeded near-ceiling state must refuse dispatch. Blocks all burns until done.
2. **Restoration v2 + relocation re-judge**: two-stage per-attribute design (cheap model proposes passage → entailment check gates each event; class-level acceptance retained). Include recommended re-judge of `model_assisted_batch` relocations. Also finish the ~3,428 resumable repair tasks under the fixed guard.
3. **Extraction-time validation port** (TrustGraph harvest): schema validation inside the extraction loop (preventive), alongside the existing post-hoc SHACL gate (detective, flag-gated, mutation-tested, from tgbench v1).
4. **Stratum re-extraction** under corrected prompts (probe decision doc), piloted on 3 docs, judged by the fact protocol before the stratum burn. Batch rule binds (DD-019).
5. **Triage-batch extraction**, sized after 1 lands and 7456614d reports counts.
6. **Concept dedup** — still blocked behind 2 and 4 (merging on invalid members contaminates merges).
7. **Serving layer**: Neo4j verbs forked from icsp_notebook + manifest query verbs (get_manifest, get_document_provenance, search_corpus) + SQLite manifest projection as bundle artifact. Truth stays in the event log; DBs are views (chat decision 2026-08-24; Postgres rejected as system-of-record).

## Desktop-authored artifact owed (next session's first deliverable)

**KG construction methodology document**, versioned at Seldon ontology level, so graph #4 starts from `seldon init --type knowledge_graph`. Stages with entry/exit gates: competency questions as executable test queries → schema vs CQs → manifest/acquisition rules → pilot with pre-registered audit → bulk with rate gating + batch dispatch rule → TEVV (stability, faithfulness, calibration) as mandatory pre-bulk-signoff stage → refinement (repair, dedup, adjudication; gate-before-wire) → serving → currency. Literature to cite: Grüninger & Fox 1995; METHONTOLOGY; NeOn; LOT (Poveda-Villalón 2022); OOPS!; Noy & McGuinness 2001; Dong et al. 2014 Knowledge Vault; Weikum et al. 2021; Paulheim 2017; Zaveri 2016; Wikidata reference model; Min 2023 FActScore; Dawid & Skene 1979; Zheng 2023; SHACL. Standing rules to encode: no span no write; location ≠ entailment; gate before wire; monitors need seeded-fault proof; batch dispatch; ledger over memory; measure before argue (TrustGraph arc, DD-018→DD-021).

## Open for Brock (non-blocking)

- 60 hard items: `corpus/staging/metrics/probe_hard_items.md` (ORCID-keyed labels; follow-on ingests).
- Cross-family judge batches: `corpus/staging/metrics/probe_crossfamily_batches/` → paste to another vendor's model, responses to `inbox/probe_crossfamily/` with model name in header.
- max.gov downloads (list produced by 7456614d).
- TrustGraph upstream PR decision.
- **FSS graph has never had TEVV run on it.** Recommend the same probe protocol on fss-policy-kg before any high-stakes use; legal text is friendlier but unmeasured. Relevant if the deck's honesty slide draws questions.

## Delivered this session

Plain 6-slide demo deck (`fss_kg_demo_plain.pptx`) with demo run-plan in slide 6 notes (overview → conflicts → currency → definition crosswalk; screenshot fallback advised). Prior 9-slide styled deck also exists if ever wanted.
