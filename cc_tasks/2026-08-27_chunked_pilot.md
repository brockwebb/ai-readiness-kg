# Chunked-extraction pilot — same 5 docs, same model, same gate; unit of extraction is the only variable

**Date:** 2026-08-27 (evening ET)
**Lineage:** follows `2026-08-27_pilot_finish.md` (ea7dd3bd, both strata FAIL under whole-document extraction). Whole-document arm is banked on `batch-013_reextract_v035b` + tonight's judge verdicts; this task adds the chunked arm and the comparison.
**Prior art (required block — see methodology §7):**
- External: Edge et al. 2024 (GraphRAG): ~2× entity references at 600-token chunks vs 2400; 100-token overlap. Gajo et al. 2026 (arXiv 2604.08752): LLM RE degrades with relation count; formatting dilutes attention. Hierarchical/structure-aware chunking outperforms fixed-size for entity *and* relation extraction (ChemRxiv 10.26434/chemrxiv.10001546, Jan 2026). Section-bounded, whole-paragraph chunking rules (TechRAG, arXiv 2606.01613 §5.3). docling-graph chunking (real tokenizer, schema-aware content budget). Neo4j LLM Graph Builder: chunk-local extraction, HAS_ENTITY provenance, post-hoc entity merge. Cross-chunk relations are an open problem (CrossAug, arXiv 2605.28004) — not solved here, diverted by design.
- Internal: Wintermute G4 kill (2026-08-16), "relationship extraction fails at 2× entity rate; descoped to Tier-2 demand-pull"; Wintermute chunk-level extractor (locate in step 1); DD-022 spend guard; locate-at-birth grounding filter.

## Preamble (standard)

Glob and read all `_ADDENDUM*.md` siblings first. Run `seldon cc complete cc_tasks/2026-08-27_chunked_pilot.md` before writing the RESULT. Report discrepancies between task premises and live state; never reconcile silently. Estimate spend from the ledger's per-class running mean before declaring any ceiling; a dry run that counts chunks and prompt tokens is required before the ceiling is written.

## 0. Band protection — first action

Lane 4 (pid 70576/70596, `restoration_v2_resume`) is sleeping to 00:05Z and will proceed stage 2 → gate → relocation → re-judge when it wakes. Relocation has no measured unit cost and could take most of the 08-28 band. **Write the STOP file the driver honors (path per `scripts/overnight_burn.py`) now**, before 00:05Z. Stage 2 resumes later from its last judgment (resume mode is proven) by a separate task after this pilot's verdict. Record the stage-2 judgment count at stop in the RESULT. This is a priority decision (pilot work gates new extraction; relocation is cleanup on a graph whose edge layer measured 0.61), logged here; operator overrides by addendum.

## 1. Locate and assess the existing chunker (zero spend)

Search `/Users/brock/GitHub/wintermute` and `~/.wintermute/` for the extraction chunker. Report: unit (page / section / fixed tokens), overlap, tokenizer, whether it preserves heading hierarchy. Reuse it **only if** it is structure-aware (section-bounded, paragraph-integral, real tokenizer). If it is page-level or fixed-character, do not reuse the unit; reuse any harness plumbing that helps and write the chunker below. Either way, cite what you found in the RESULT — this is the internal-precedent record.

## 2. Chunker (`kg/extraction/chunker.py`, deterministic, tested)

Input: the corpus markdown (`corpus/bulk_md/<doc_id>.md`). Rules, in priority order:
1. Section-bounded: a chunk never crosses a markdown heading boundary at the level that produces sections (H1–H3; pick the level per doc by the heuristic "≥ 3 headings at that level", record the choice).
2. Paragraph-integral: only whole paragraphs are packed; never split a paragraph or a table.
3. Cap ≤ 1,500 tokens by the real tokenizer (the one `model_stub` reports; fall back to `tiktoken cl100k_base` and say so). Oversize single paragraphs/tables are their own chunk, flagged `oversize`.
4. Overlap: repeat the last paragraph of the previous chunk (bounded ≤ 100 tokens; if the last paragraph exceeds that, repeat its final sentences to ≤ 100 tokens).
5. Breadcrumb header prepended to the model input, not stored in the span: `doc_title > H1 > H2 > …`.
6. Each chunk gets a stable id `<doc_id>#c<NNNN>` and byte offsets into the source markdown; extraction events record `chunk_id`; grounding spans are validated against the *chunk* text and re-validated against the full document (locate-at-birth, unchanged).

Tests: heading boundary respected; paragraph never split; cap enforced; overlap ≤ 100; offsets round-trip; a doc with no headings falls back to paragraph packing with a recorded `no_structure` flag.

## 3. Extraction profile `chunked_v035`

Same prompt v0.3.5 rules, restated for a chunk: extract only what is asserted in this chunk; entities mentioned but not asserted about are emitted as mention-only stubs (name + span) for resolution, not as typed nodes; a relation whose endpoints are not both in this chunk is diverted with `diversion_reason: cross_chunk`. Instrument per-attribute grounding spans unchanged. Output per chunk is small — there is no truncation path; if a chunk response exceeds `truncation_suspect_tokens`, STOP the run, that is a defect not a status. Model `claude-opus-5`, effort unchanged — the model is held constant so the unit is the only variable. Profile sha-pinned; `apply_profile` refuses drift.

## 4. Cross-chunk entity resolution (deterministic only)

Merge stubs and nodes within a document by exact normalized surface form (NFKC, case-fold, whitespace collapse) and recorded alias. Report merge rate and the count of unmerged stubs per doc. No LLM-proposed merges in this task — that is the sift-kg three-layer design and it is a separate pilot. Unmerged stubs stay as `Mention` nodes with provenance, not typed entities.

## 5. Run — pre-registered

- Docs: the same five (`data-readiness-for-ai-a-360-degree-survey`, `aidrin-hiniduma-2024`, `fcsm-23-02-a-framework-for-data-quality-case-studies`, `from-accuracy-to-readiness-metrics-and-benchmarks-for-human`, `mitre-ai-maturity-model`).
- Run id `pilot_chunked_v035`. Ceiling from the dry run: chunk count × (chunk tokens + prompt overhead + expected output from the per-class mean) + judge, with the arithmetic in the RESULT. Expectation from the banked single-pass docs: ≤ ~400K/doc; if the dry run says otherwise, report before running.
- Judge: identical probe protocol, identical raters (opus-4-8 primary, sonnet-5 secondary), identical thresholds: **F_upper < 0.10 per stratum, item faithful ≥ 0.70; precondition pooled ≥ 20 per stratum.** Thresholds do not move. Apply the decomposer coordination fix and the mid-noun-phrase truncation check identified in `pilot_finish` **to both arms' facts** before judging, so the comparison is like-for-like; record both fixes as versioned probe-protocol changes.
- Report, per arm and per stratum: admitted items, F (Wilson 95%), item-faithful, per-doc settled tokens, diversion histogram (chunked arm: `cross_chunk` share separately), merge rate. Verdict: `docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md`.
- Register every headline number as a Result artifact with `generated_by` → the verdict script and `computed_from` → the shards. The graph currently carries 39 Results with incomplete provenance; add zero more.

## 6. Not in scope

Chunk-size sweep; LLM-proposed merges; any bulk extraction; any prompt revision. On PASS of either stratum, record Lane 2/3 eligibility under `chunked_v035` and stop. Lane 4 stage-2 resume is a separate task.

## 7. Exit

Verdict on disk; Results registered with provenance; chunker + tests + profile committed; STOP file state and Lane 4 judgment count recorded; RESULT with the ledger table and the ceiling arithmetic; commit and push shards, raws, verdict, code. Register `docs/research/kg_construction_methodology.md` and `docs/research/2026-08-27_lab_note_unit_of_extraction.md` as Seldon artifacts (`seldon artifact create`, types Documentation and LabNotebookEntry respectively) if not already registered; do not edit them.
