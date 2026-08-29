# Corpus T0/T1 substrate — bibliographic layer, structural index, acquisition round 2

**Date:** 2026-08-29. **Dispatch after task 3d86f16d closes** (both write the manifest; serialize).
**Decision context:** hybrid tier architecture (T0 bibliographic / T1 structural / T2 gated extraction / T3 adjudication). T2/T3 are already decided (DD-023/024); this task builds T0/T1. **Zero `model_stub` spend** — every layer here is API metadata, local parsing, or local embedding. Any step that would need a model call is out of scope and stops.

**Prior art (required block, DD-025):**
- External: LazyGraphRAG (Microsoft 2024) — deferred LLM extraction over cheap index, ~0.1% GraphRAG indexing cost; validates extract-on-demand. OpenAlex (Priem et al. 2022, arXiv:2205.01833), Crossref, Semantic Scholar APIs — free structured metadata + citation graphs. GROBID (Lopez 2009) — PDF header/reference parsing. Bibliographic coupling (Kessler 1963) and co-citation (Small 1973) — connection structure from citation behavior, no extraction. Docling (IBM) — layout-aware parse to structured document.
- Internal: Wintermute tier design (page-level acquisition + retrieval; G4 verdict — embeddings+FTS as system of record); DD-023/024 (gated T2/T3); chunker + stable chunk ids (commit 2a43eca); "symlinks never copies" — all stores below are rebuildable projections, never sources of truth.

## Epistemic classes (binding on every write)

Every record carries `evidence_class`: `bibliographic` (third-party asserted: OpenAlex/Crossref/S2/GROBID output, citation edges), `structural` (deterministic derivation: chunks, offsets, FTS, embeddings), `extracted_gated` (T2, absent from this task), `adjudicated` (T3, absent). Bibliographic and structural records NEVER appear in validated strata, are never pooled with gated items, and are excluded from any faithfulness reporting by construction. Author keywords and topic assignments are retrieval features, not graph claims.

## 0. T0 — bibliographic harvest (all admitted docs)

1. For every manifest doc with a DOI: pull OpenAlex work record (title, abstract, authorships, venue, topics/concepts, referenced_works, cited_by_count). Fall back Crossref → Semantic Scholar; record which source served each field.
2. Docs without DOI: GROBID header + reference extraction from the PDF; attempt DOI resolution from parsed metadata; unresolved stay `bibliographic_partial`.
3. Citation edges: `cites` edges between corpus members (both endpoints admitted), `evidence_class: bibliographic`, `metadata_source` recorded. Compute co-citation and bibliographic-coupling scores among corpus members; store as edge weights, clearly non-semantic.
4. Rate limits respected (OpenAlex polite pool with mailto); all responses cached raw to `state/biblio_cache/` so the harvest is replayable without re-fetching.

## 1. T1 — structural index (all admitted docs)

1. Re-convert corpus with Docling (this also executes ADDENDUM-01 §2.5's source-fidelity fix for the whole corpus, not just the pilot five). Sample-diff 5 docs against pypdf output; confirm the dropped-character damage class is gone; report.
2. Run the existing chunker over the Docling output: chunk table (chunk_id, doc_id, byte offsets, breadcrumb, token count) persisted.
3. FTS index (SQLite FTS5) + embeddings (local sentence-transformers; record model name + version as instrument metadata) over chunks.
4. Store: single SQLite file `state/corpus_index.db`, declared a **rebuildable projection** (events + sources are truth); a `rebuild_index` entrypoint proves it by rebuilding from scratch and diffing counts.
5. Manifest table export: projection of the manifest to `docs/corpus/manifest_table.md` (doc_id, title, year, venue, DOI, admission date, tier coverage T0/T1/T2 flags) — the reviewable artifact the operator asked for.

## 2. Acquisition round 2 (admission only; extraction forbidden)

1. Sources: the team's literature list (operator supplies file path or paste at dispatch — if absent, skip and note); AIO/GEO cluster (Aggarwal et al. GEO already queued in 3d86f16d; add its citing/cited works from T0 expansion below).
2. T0-driven candidate expansion: from the harvested reference lists, rank non-corpus works cited by ≥ 3 corpus members (bibliographic coupling to the corpus). Emit `docs/corpus/acquisition_candidates.md`: candidate, rank score, which corpus docs cite it, open-access status, fetchable vs `manual_download_needed`. **Do not auto-admit** — candidates are a reviewed list; the operator's admission rules (AUTH-2 class) still gate entry. Fetch + admit only open-access items the rules pass; everything else lands on the manual list.
3. Prioritization output: for every admitted doc, `t2_priority` = crosswalk demand (evidence cells naming it or its topic) first, T0 centrality (corpus-internal citations) second. This ordering, not anyone's intuition, feeds the eventual v0.3.7 bulk decision.

## 3. Close

RESULT with: T0 coverage table (docs fully/partially harvested), fidelity sample diff, index counts + rebuild proof, candidate list sizes, top-10 t2_priority docs with scores. Register `manifest_table.md` and `acquisition_candidates.md` as Seldon artifacts. `seldon cc complete`, commit, push.

## Non-goals

Any `model_stub` call; T2 extraction; keyword/concept promotion into validated strata; Postgres (SQLite suffices at 200-doc scale — revisit only on measured need); Wintermute integration (this substrate is project-local; cross-project is a Wintermute decision, not a side effect).
