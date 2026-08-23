# CC Task — TrustGraph extraction benchmark: measure, don't argue

**Date:** 2026-08-23
**Repo:** /Users/brock/GitHub/ai-readiness-kg (benchmark work under `benchmarks/trustgraph/`, gitignore nothing; artifacts are the point)
**Mode:** No `ANTHROPIC_API_KEY` anywhere, including inside TrustGraph's config — abort any path that requires it. LLM for BOTH extractors is Gemini Flash via the existing Google AI Studio credentials, so extractor architecture is the only varied factor. If no Google credential is configured, STOP at Phase 1 and record the blocker; do not substitute another provider.
**Immutable file. Operator contact: none. Sub-RESULTs under `docs/research/2026-08-23_tgbench_*`; final `cc_tasks/2026-08-23_trustgraph_benchmark_RESULT.md`.**

## Question under test

Does TrustGraph's ontology-driven extraction (github.com/trustgraph-ai/trustgraph, Apache-2.0) produce lower fabrication and fewer capture defects than our extractor on our corpus, holding the model constant? Prior decision (chat, 2026-08-22) rejected TrustGraph on infrastructure-weight and missing-validity-machinery grounds without measurement. This task replaces that argument with data. New information motivating re-evaluation: the probe measured our extractor at F=0.079 with 52% capture defects; "ours is instrumented" is not evidence that ours is better at extraction.

## Pre-registered decision rule

Let F_tg and F_ours be fact-level fabrication (probe protocol) on the same 5 documents; C_tg, C_ours the capture-defect rates; R = TrustGraph's item coverage relative to our extraction (matched items / our items, matching by type + normalized-text similarity ≥ 0.8).

- **Adopt-evaluate:** F_tg upper CI < F_ours point estimate AND C_tg < C_ours AND R ≥ 0.7 → follow-on task to design integration of TrustGraph's extraction layer (their extractor, our event store, gates, and TEVV instrumentation) for the next corpus arm. Not a platform migration.
- **Harvest-components:** otherwise → record what measurably helped (ontology constraint, SHACL, prompt structure) as adoptable pieces; no integration task.
- **Either way:** Phase 6 (pySHACL gate candidate) runs regardless of the verdict.
- Deployment friction is data, not grounds to skip: if Phase 1 exceeds its time-box, that is the RESULT ("cost of machinery exceeds spike budget"), reported with where it stuck.

## Phase 1 — Deploy (time-boxed 2h wall-clock)

`npx @trustgraph/config` → Docker Compose deployment, local, Google AI Studio (Gemini Flash) as sole LLM, minimal profile (no vLLM, no OCR). Record: containers count, RAM footprint, time-to-first-successful-query. Hard stop at 2h of deployment debugging → write RESULT with the blocker and the friction finding; skip to Phase 6.

## Phase 2 — Ontology

Generate OWL/Turtle from `kg/schema.yaml` v0.3.2 (node types → classes with datatype properties; edge `pairs` → object properties with domain/range). Deterministic script, committed. Load via their ontology workbench/API. Fidelity check: round-trip export and diff class/property counts.

## Phase 3 — Extract

The 5 probe pilot documents (same texts, from `corpus/`). Run TrustGraph's ontology-driven flow. Export triples + their provenance/evidence records via their API. In parallel (cheap), re-run OUR extractor on the same 5 docs with Gemini Flash under the current prompt template into a `purpose: benchmark` shard, so both sides share model and documents. Neither output enters the graph.

## Phase 4 — Normalize

Map both outputs to the probe's fact schema: items → atomic facts; TrustGraph evidence chunks stand as their "span" equivalent (record verbatim-substring rate of their evidence vs source as its own metric — our span discipline is a constraint they don't impose, so measure it, don't assume it). Matching for R computed here.

## Phase 5 — Judge

Probe protocol exactly: same judge models, batch 10, randomized order, PROV-O attribution, Dawid-Skene with the probe's estimated confusion matrices as priors. Output per side: F with CI, capture-defect rate, filled-attribute rate, coverage R, plus per-type breakdown. Apply the decision rule; write `docs/research/2026-08-23_tgbench_decision.md`.

## Phase 6 — SHACL gate candidate (unconditional)

Generate SHACL shapes from schema.yaml (same script family as Phase 2); validate the current projection export with pySHACL; report violations by class. If violations are all known classes (dangling cites), propose it as gate `shacl_conformance` with a mutation-tested positive control (seed one bad-typed edge). Wire behind a config flag, off by default.

## Phase 7 — Close

DD-018: benchmark outcome, verdict, and the re-evaluation rationale (supersedes the chat-level rejection; decisions are revisable on measurement, and this DD records the revision mechanism working). Seldon results: F/C/R both sides, deployment friction numbers, SHACL violation count. Teardown containers; commit and push.

## Out of scope

Platform migration; Context Core export (parked with trigger per 2026-08-22 chat); touching the live graph; any Anthropic-keyed path; extending past the 5 documents.
