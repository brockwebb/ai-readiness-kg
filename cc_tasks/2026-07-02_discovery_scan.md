# CC Task: Discovery scan — build the candidate register

**Date:** 2026-07-02
**Project:** ai-readiness-kg
**Project root:** /Users/brock/GitHub/ai-readiness-kg
**Status:** proposed
**Immutable once written. Changes require a new task file.**

---

## Objective

Produce a unified candidate register of documents for manifest consideration, merged and deduplicated from three discovery sources. Output is a register, not manifest entries — nothing in this task touches the manifest or event log (DD-003).

## Discovery sources

**A. Research synthesis doc (parse):**
`docs/research/AI Readiness  A Comprehensive Literature Synthesis for Knowledge Graph Ingest.md`
Extract every cited source: title, primary URL (prefer arXiv/DOI/publisher over aggregators like Semantic Scholar), authors/year where given, source_type (federal / academic / industry / standard). The synthesis doc itself is NOT a candidate — it is internally generated discovery input with no citable provenance.

**B. Wintermute scan (Cypher, read-only):**
Neo4j at bolt://localhost:7687, database `wintermute-intake` (creds in ~/.wintermute or existing config; every statement prefixed `USE \`wintermute-intake\``).
1. Probe schema first: `CALL db.labels()` and inspect document/source-bearing node types before writing search queries. Do not guess property names.
2. Keyword search (case-insensitive CONTAINS) over titles/names/summaries for: "AI readiness", "AI-ready", "data readiness", "readiness level", "AIDRIN", "maturity model", "AI adoption", "data quality for AI", "AI governance".
3. For hits, capture title and any stored source URL. Wintermute is discovery attribution only (`discovered_via: wintermute-scan`); the register entry's primary_url must be the external source, never a Wintermute reference. Hits with no recoverable external URL: list in a `needs_source` section, title only.
4. READ ONLY. No writes to wintermute-intake under any circumstances.

**C. fss-policy-kg manifest cross-scan (read-only):**
Read the manifest at `/Users/brock/GitHub/icsp_notebook/ingest/` (locate the manifest file; do not modify anything in that repo). Flag documents plausibly relevant to AI readiness / AI-ready data / AI governance (e.g. M-25-21, FCSM data/AI publications, Evidence Act family). `discovered_via: fss-policy-kg-manifest`. These are candidates for deliberate re-ingestion here (DD-001 acceptable redundancy).

## Output

1. `corpus/staging/candidate_register.jsonl` — one JSON object per candidate:
   `{"title", "primary_url", "authors", "year", "source_type", "discovered_via", "notes", "dedup_key"}`
   dedup_key = normalized URL (strip scheme, www, trailing slash, tracking params) or normalized title if no URL. Merge duplicates across sources A/B/C; keep all discovered_via values as a list.
2. `docs/research/candidate_register_summary.md` — counts by source_type and discovered_via, the needs_source list, and any anomalies (dead-looking URLs, ambiguous entries). No prose padding.

## This task does NOT

- Add anything to the manifest or emit any event.
- Fetch/download candidate documents or verify URL liveness.
- Write to wintermute-intake or icsp_notebook.
- Judge inclusion. Triage is the operator's next Desktop session.

## Verification checklist

- [ ] Register is valid JSONL, dedup applied, discovered_via preserved as list on merged entries
- [ ] Zero writes outside ai-readiness-kg
- [ ] Synthesis doc itself absent from the register
- [ ] Summary counts match register line counts
- [ ] Commit register summary; staging/ is gitignored so the JSONL stays local — confirm it does not appear in git status
