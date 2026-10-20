# Handoff — 2026-08-29 Desktop session close

**Discipline reminder to next session: this is narrative compression. Verify against the graph (`seldon_go`, project_dir /Users/brock/GitHub/ai-readiness-kg), `kg.spend status`, and the RESULT files before acting on anything below.**

## What this session changed

1. **Pilot resolution (task ea7dd3bd → chunked_pilot 64661f7a §1):** both extraction units PASS the Instrument gate; the two-day FAIL was the probe (span-cutting defects, fixed, mutation-verified). ERRATUM 1 filed. Semantic stratum GATE UNREACHABLE at n=20/21 → DD-026 (preconditions must be arithmetically satisfiable); DD-024 trigger amended ≥20→≥35 in place.
2. **DD-023 now rests on cost alone.** ERRATUM 2: pypdf-damage story split into genuine PDF text-layer loss (better copy needed → pickup list) vs model mid-noun-phrase quoting (anchor contract fixes). Pre-registered expectation: v0.3.7 quarantine improvement credits the anchor contract, not Docling.
3. **Crosswalk (docs/crosswalk/):** skeleton v0.2 — 45 indicators, 7 groups, tiers assigned (public 17 / agency_instrumented 21 / paid 7), evidence cells resolved to doc_ids (25) or honest gaps (20). Brief written, plagiarism-checked (seeded control fires). Four critiques softened by fair-characterization pass — the delivered-feedback items now read: ACCURATE lacks closure+attribution (not "open-loop"); uncertainty framed only as privacy safeguard (not "absent"). Do not use the old phrasings with USAFacts.
4. **T0/T1 substrate (task 204bc046 + ADDENDA 01/02):** T1 complete — 178 docs, 5,164 chunks, FTS+embeddings, SQLite projection with rebuild proof. T0 at 29/178 (OpenAlex daily quota); `python -m kg.biblio resume` is idempotent, proven under exhausted quota, auto-recomputes rankings. Hash mismatches: ledger-sync defect fixed (content_update event type), verify clean. Per-doc reindex path exists (`--phase reindex --doc-id X`), staleness derivation-keyed.
5. **Process rules added:** methodology §7.10 (availability is a queue, validity is a gate), §7.8 (both candidates on same bytes before naming a cause), 7.6/7.7 (CC's, from the erratum). DD-025 prior-art gate operative — both new pilots carry the block.
6. **Seldon defect queued cross-repo:** seldon/cc_tasks/2026-08-29_documentation_artifact_type.md (Documentation type + produced_by→ResearchTask edge; migration of 2 mis-typed artifacts).

## Owner queues

**Operator:**
- Drop manually-fetched files in `corpus/inbox/` (Commerce PDF is the known one; `docs/corpus/operator_pickup.md` is the projected queue, ordered by t2_priority). If a file replaces a degraded/wrong-extent doc, say so at next dispatch or name the file with the existing doc slug; ambiguous matches get reported, not guessed.
- Review pass on crosswalk skeleton + brief (§7.1) — gates scoring rubric/weights (operator value input, deliberately parked).

**Machine, scheduled:** nightly `kg.biblio resume` + projection refresh (micro-task 2026-08-29_biblio_cron.md — dispatch anytime; zero model spend).

**Dispatchable now, zero/near-zero model spend:**
- seldon Documentation-type task (other repo, no contention).
- DD-024 instrument-version citation check on §3b semantic verdicts (rule 7.6; shard re-read).
- ADDENDUM-01 §2 of chunked_pilot: v0.3.7 contract + chunker profile + tests (code only; the §3 extractor arms are the only model spend and wait on quota comfort).

**Parked pending operator:** v0.3.7 §3 arms (Haiku/Sonnet, ceilings from dry run); Lane 4 relocation (stopped by design); Lane 2/3 (no eligibility yet under a cost-viable profile); scoring rubric.

## Spend context at close
Weekly Max cap is the binding constraint (operator-managed). Daily band 55M standing; all recent tasks zero model spend except pilot judges (~2M). Orphan-reservation release path exists (`kg.spend release-orphans`, dry-run default).
