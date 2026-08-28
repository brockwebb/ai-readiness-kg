# ADDENDUM-01 to 2026-08-27_chunked_pilot.md — pause disposition, banked-material judge, v0.3.7 emission contract

**Date:** 2026-08-27, after operator full stop at 44/128 chunks. Task file immutable; this amends. **Nothing in this addendum runs until the operator says go.** Weekly cap is the binding constraint; every step below carries its own ceiling and the cheap steps come first.

## 0. Immediately on go (near-zero spend)

1. Commit and push the staged work (RESULT pause record, `scripts/chunked_pilot.py`, batch-016 shard, chunk raws, ledger/Seldon events). It is real state; resume-safety requires it on the remote.
2. Do **not** resume extraction of the remaining 84 chunks. The cost question is answered (65,637/chunk settled, ~8.4M projected vs 3.93M whole-doc); finishing the arm buys no information the judge can't get from banked material.

## 1. Judge the banked 44 chunks (the pre-registered question, ~1–2M ceiling from per-class mean)

The pilot exists to answer one question: does chunk-local extraction move faithfulness? 530 admitted nodes / 841 edges across 34 ingested chunks is enough to test the Instrument stratum if pooled ≥ 20 (count first; report the number before judging). Same raters, same thresholds, both attribute-quoting fixes applied. Semantic stratum: count pooled admitted semantic edges; if < 20 (likely — 11 over 10 chunks, `has_component` at zero from type instability), record PRECONDITION NOT MET with the counts and do not judge a sub-minimum sample. Verdict appended to `docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md` with an explicit caveat: chunked arm judged on a 44/128 partial, doc mix reported.

## 2. v0.3.7 emission contract (design + code + tests, zero model spend until its pilot)

The cost pathology is the contract, not the unit. Changes, each cited to tonight's evidence:

1. **Anchors, not quotes.** Model emits per item: `name`, `type`, `anchor` = shortest unique substring in the chunk (≤ 10 tokens). Harness locates the anchor deterministically (exact match after NFKC/whitespace normalization; ambiguous or missing → quarantine `anchor_not_located`), then derives the grounding span itself as the containing sentence from the source text. Locate-at-birth guarantee unchanged; the span in the graph comes from the *document*, not the model's typing. Kills the 33–46K outputs and most `span_partial` quarantines in one move. Instrument attributes: same anchor mechanism per attribute.
2. **Salience, not exhaustiveness.** Drop the exhaustive-inventory instruction. Extract items the schema can type that the chunk *asserts something about*. Recall is not gate-measured; we do not pay for it. One gleaning pass ("list any schema-typable items you missed, names only") is permitted, cheap by construction.
3. **Closed lists enforced at parse.** `diversion_reason` outside the ADDENDUM-06 list is normalized at parse (raw preserved on the shard) — promote CC's report-side normalization into the parser with tests. A model cannot be bound by an instruction; it can be bound by a parser.
4. **Type reconciliation at merge, not per chunk.** Typing conflicts across chunks (metric as Concept vs Instrument) resolve at the deterministic-merge step: if any chunk grounds instrument evidence, Instrument wins; otherwise majority; unresolved → `type_conflict` flag, excluded from strata pooling. Rule is mechanical and logged per entity.
5. **Source fidelity before extraction.** Re-convert the five pilot docs with Docling (or MinerU) replacing the pypdf-damaged markdown; diff a sample to confirm the class of damage (dropped characters at line breaks) is gone. A validity pipeline running against corrupted source text quarantines faithful output — measured tonight at scale.

## 3. v0.3.7 pilot, two extractor arms (on go, after §2 suite green; pre-registered)

Same 5 docs (re-converted), same chunker, same judge, same thresholds. Two arms:
- **Arm A: `claude-haiku-4-5` extractor.** The gate is the validity instrument; the extractor's job is recall of judgeable candidates. If Haiku's admitted output clears F_upper < 0.10 / faithful ≥ 0.70, extraction economics stop being a constraint permanently (~60–100× unit-cost reduction).
- **Arm B: `claude-sonnet-5` extractor.** Fallback if A's admitted yield or faithfulness is short.
Opus 5 is not an arm; tonight's data prices it out unless both cheap arms fail the gate. Ceilings from dry-run chunk counts × expected anchor-contract output (~1–2K/chunk); expected total per arm well under 1M. Report per-arm: admitted yield, F, faithful, per-doc settled cost, quarantine rate by reason.

## 4. Sequencing and caps

§0 → §1 → (report) → §2 → (report, suite green) → §3. Hard stop between numbered sections; each section's spend reported against its ceiling before the next starts. If the weekly cap forces a choice, §1 outranks everything — it closes the pre-registered question; §2–§3 are the redesign and keep.

## 5. Recorded, not acted on

- Lane 4: stage 2 complete (5,554 judged, 4,021 accepted), class gate PASS at 0.90 (n=130, threshold ≥ 0.90, pre-registered — passes). Relocation/re-judge remain stopped; wiring the passed class is a separate task after the graph's extraction epoch settles.
- The whole-doc arm's exhaustive-verbatim contract is retired for any future run; profile stays on disk for the comparison record.
