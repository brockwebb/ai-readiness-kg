# CC Task — TrustGraph benchmark v2: custom Claude-CLI backend, model held constant on Claude

**Date:** 2026-08-23
**Repo:** /Users/brock/GitHub/ai-readiness-kg (work under `benchmarks/trustgraph/`; fork clone at `/Users/brock/GitHub/trustgraph-fork`)
**Mode:** Max OAuth via the Claude Code CLI only. `ANTHROPIC_API_KEY` unset everywhere including TrustGraph config — abort any path that requires a provider API key. No Google, no OpenAI, no Ollama in this design.
**Supersedes the execution plan of `2026-08-23_trustgraph_benchmark.md` (Seldon b6900da4, closed not-evaluable).** The question under test, the decision rule, and the class definitions from that task are unchanged and are incorporated by reference. DD-018's re-run trigger is satisfied by this design: TrustGraph is Apache-2.0, its model backends are swappable service components, and a custom backend invoking the Claude Code CLI is an intended extension mechanism, not a workaround.
**Immutable file. Operator contact: none. Sub-RESULTs under `docs/research/2026-08-23_tgbench2_*`; final `cc_tasks/2026-08-23_trustgraph_benchmark_v2_RESULT.md`.**

## Design change from v1

Both extractors call the **same pinned Claude model through the same Claude Code CLI invocation path** (the repo's model_stub conventions). Architecture is the only varied factor; model, auth, and client are constant. TrustGraph's side gets this via a custom text-completion backend service written against their component contract.

## Token ceiling and friction accounting

- **Ceiling: 8M tokens total** across both sides. TrustGraph's chunking controls its call count; that is data. Record per document and per side: calls made, tokens in/out, cache-read ratio, wall-clock. If TrustGraph's side alone projects past 5M after the first document, stop its extraction at the documents completed and run the comparison on the completed subset (minimum 2 documents; below that, verdict `not_evaluable_cost`, with the measured burn as the finding).
- The v1 friction rule stands: deployment or integration exceeding its time-box is a finding, not a failure.

## Phase 1 — Deploy + backend (time-boxed: 2h deploy, 3h backend, hard stops)

1. Clone TrustGraph (github.com/trustgraph-ai/trustgraph) to `/Users/brock/GitHub/trustgraph-fork`; record commit sha. Deploy the minimal Docker profile (no vLLM, no OCR, no vendor LLM containers).
2. Implement `claude-cli-completion`: a service satisfying their text-completion component contract (subscribe request topic, publish response), which executes the pinned model via the Claude Code CLI in non-interactive mode, tools disabled, stable cwd, prompt passed through unmodified, response returned verbatim. Concurrency 1–2; simple retry-once on transient CLI failure (the 2026-08-22 auto-update incident class). Unit test with a stub CLI on PATH.
3. Wire TrustGraph's flow to this backend; smoke-test with one paragraph end-to-end. Time-box exceeded at either step → write RESULT with the blocker and the friction numbers; skip to Phase 5.

## Phase 2 — Ontology + extract

As v1 Phases 2–3: load the schema-derived OWL (generator already exists from v1: `benchmarks/trustgraph/` schema→OWL script); run their ontology-driven flow on the 5 pilot documents through the claude-cli backend. Our side: re-run our extractor on the same 5 documents with the same pinned model into a `purpose: benchmark` shard. Neither output enters the graph. Both sides log the friction metrics above.

## Phase 3 — Normalize + judge

As v1 Phases 4–5, unchanged: map both outputs to the probe fact schema (their evidence chunks stand as span-equivalents; measure their verbatim-substring rate as its own metric); judge under the probe protocol with PROV-O attribution and Dawid-Skene using the probe's confusion-matrix priors; compute F, capture-defect rate, filled-attribute rate, coverage R per side.

## Phase 4 — Verdict

Apply the v1 pre-registered decision rule verbatim (adopt-evaluate / harvest-components thresholds unchanged). Write `docs/research/2026-08-23_tgbench2_decision.md`. DD-021 records the outcome and explicitly supersedes DD-018's not-evaluable status.

## Phase 5 — Close

Seldon results (F/C/R both sides, calls and tokens per document per side, backend implementation time); teardown containers; fork left in place with the backend committed to the fork only; tests green in our repo; **commit and push** ai-readiness-kg.

## Out of scope

Platform migration; Context Core export (parked, trigger unchanged); touching the live graph; extending past 5 documents; upstreaming the backend to TrustGraph (note in RESULT if it is worth offering; that is the operator's call since it is a public contribution under his name).
