# CC Task — Whole-graph repair: span coverage, relocation, attribute nulling

**Date:** 2026-08-23
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Max OAuth only; `ANTHROPIC_API_KEY` unset or abort.
**Execution model:** Multi-agent permitted; relocation calls are embarrassingly parallel. Sub-RESULTs under `docs/research/2026-08-23_repair_*`; orchestrator assembles `cc_tasks/2026-08-23_whole_graph_repair_RESULT.md` citing the Seldon task id.
**Immutable file; discrepancies reported, never reconciled. Operator contact: none. Every fork has a rule; unlisted forks get a grounded decision logged in standing decisions.**

## Context

Probe (Seldon `68426971`, RESULT 2026-08-22) measured on n=935 atomic facts: 14% scoring defects, 52% capture defects (span truncated / subject dropped), 21% filled attributes, F=0.079 fabrication. Repair disposition per class was pre-registered in the probe task and is not re-decided here. This task generalizes the probe's Phase 7 repairs from the 400 probe items to all items in both epochs, excluding the three `reextract_required` strata (Instrument v1, Instrument kernel-v03, edge:semantic:kernel-v03), which are handled by the re-extraction task, not repaired here.

## Pre-registered success measure (before data)

A seeded-random sample of 150 repaired items (stratified by repair type: relocated-deterministic, relocated-model, attribute-nulled), decomposed and judged under the probe's fact-level protocol (same judges, batch size 10 per the probe's κ), must reach strict fact-level entailment ≥ 0.85 pooled. Below that, the repair method that missed is reported per-type; no threshold change, no silent retry.

## Phase 1 — Detection sweep (zero model spend)

Mechanical, whole graph, both epochs, excluding `reextract_required` strata:
- **Span-partial:** span text is not a covering match of item `verbatim_text`/`text`/`claim_text`/`name`/`term` under NFKC normalization. Emit worklist `repair_span_partial.jsonl`.
- **Unsupported attribute:** `span_entailable: true` attribute value absent from span under normalized substring match. Worklist `repair_filled_attr.jsonl`.
- Report counts by type, epoch, document; compare against probe-projected rates (52% and 21% of failed facts) and flag divergence > 2× either way as a finding.

## Phase 2 — Deterministic relocation (zero model spend)

Exact / NFKC-normalized substring search of item text in full document text. Hit → `grounding_relocated` overlay event (old span, new span, method `deterministic`). Miss → forward to Phase 3.

## Phase 3 — Model-assisted relocation (model spend; cleanup-class model per model_config / DD-006)

One directed call per item: given item text and full document text, return the minimal contiguous passage supporting it, or NONE. Verify the returned passage is a verbatim substring of the document (reject and retry once on failure; then NONE). Passage found → `grounding_relocated` overlay (method `model_assisted`, call id stamped). NONE → item gets `span_unrepairable` annotation event; counted, left intact. Rate-measure the first 20 calls, project total, proceed regardless (this class is bounded by Phase 1 counts).

## Phase 4 — Attribute nulling (zero model spend)

For every worklist entry from Phase 1 not resolved by a relocation that now covers the attribute: `attribute_nulled` overlay, `reason: unsupported_by_span`. Attributes the probe showed the document supports elsewhere are still nulled; re-grounding them is re-extraction's job, not repair's (rule from the probe's disposition table: may be null, may not be guessed).

## Phase 5 — Enforcement flip

Set `extraction_gates.enforce_span_coverage: true` for **future extraction runs only** (config gate, not retroactive quarantine). Add a regression test that a partial span is quarantined at extraction time and that historical items with `grounding_relocated`/`span_unrepairable` overlays are not quarantined by projection.

## Phase 6 — Projection, gates, success measure

Rebuild projection (overlays last); grounding gate must remain 0 (STOP otherwise). Run the 150-item re-judge per the pre-registered measure. Update the six monitors' baselines only if the RESULT records the before/after pair (version the instrument).

## Phase 7 — Close

DD-017: whole-graph repair record (counts, methods, ceiling of deterministic relocation, the success-measure outcome). Seldon results registered: relocated counts by method, nulled count, unrepairable count, post-repair fact entailment. Tests green; controls restored if touched; **commit and push**.

## Out of scope

Re-extraction of the three flagged strata; dedup; new harvest; judging beyond the 150-item measure; threshold changes; editing this file.
