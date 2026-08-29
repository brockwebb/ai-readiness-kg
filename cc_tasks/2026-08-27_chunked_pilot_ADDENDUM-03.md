# ADDENDUM-03 to 2026-08-27_chunked_pilot.md — v0.3.7 build (§2) and pilot scope correction (§3)

**Date:** 2026-08-29. Operator go for the cheaper burn path. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-27_chunked_pilot_ADDENDUM*.md` (there are now three including this one) and the parent task file. Run `seldon cc complete cc_tasks/2026-08-27_chunked_pilot.md` only at the end of §3, not before.
**Result:** append to `cc_tasks/2026-08-27_chunked_pilot_RESULT.md`. Discrepancies reported, never silently reconciled.

## 0. What this addendum decides

ADDENDUM-01 §1 is closed: the chunked arm PASSES the Instrument gate. The extractor is not broken. The only live objection to chunked extraction is **cost** (65,637 tokens/chunk settled; ~8.4M projected for five documents against 3.93M whole-doc). ADDENDUM-01 §2 (the v0.3.7 emission contract) is the cost fix and is **design only** — no code exists. This addendum builds it, then runs the two arms.

Two corrections to ADDENDUM-01 as written, both pre-registered here before any data:

**(a) §3 gates the Instrument stratum only.** DD-026 fixes the minimum n at 35 for `F_upper < 0.10` at one fact per edge. The five pilot documents produced 11–20 semantic edges in the chunked arm. Running the semantic stratum on the same five documents can only produce a second GATE UNREACHABLE, and would be spend that buys an uninformative FAIL — the exact thing DD-026 forbids at registration. Semantic edges are already closed to demand-pull by DD-024, so nothing downstream waits on this verdict. Report the semantic count; do not judge it.

**(b) ADDENDUM-01 §2.5 is superseded by DD-023 ERRATUM 2.** The corpus has already been re-converted with Docling under task 204bc046, and the erratum established that re-conversion does **not** repair the `span_partial` class it was prescribed for — both converters extract the identical truncated token from the same bytes. Use the Docling output that already exists (`state/corpus_index.db` / T1 artefacts); do not re-convert, and do not carry any expectation that quarantine rate falls because of the converter. Pre-registered attribution stands: any quarantine improvement measured in §3 credits the anchor contract.

## 1. §2 — build the v0.3.7 emission contract (ZERO model spend)

Implement ADDENDUM-01 §2 items 1–4 as code plus tests. No `model_stub` call anywhere in this section; a step that would need one is out of scope and stops.

1. **Anchor contract.** Model emits per item `name`, `type`, `anchor` (shortest unique substring in the chunk, ≤ 10 tokens). Harness locates the anchor deterministically against the chunk source (NFKC + de-hyphenation + whitespace collapse, case-sensitive, exact — reuse `kg/extraction/grounding.py`, do not fork its normalization). Ambiguous or absent → quarantine `anchor_not_located`. The grounding span written to the graph is derived **by the harness from the source text** as the containing sentence, never from the model's typing. Instrument attributes use the same mechanism per attribute. Locate-at-birth guarantee unchanged.
2. **Salience, not exhaustiveness.** Drop the exhaustive-inventory instruction from the prompt. Extract schema-typable items the chunk asserts something about. One gleaning pass permitted (names only). Recall is not gate-measured.
3. **Closed lists enforced at parse.** Promote the report-side `diversion_reason` normalization into `parser.py` against the ADDENDUM-06 list; raw value preserved on the shard. Tests for an out-of-list value.
4. **Type reconciliation at merge.** Cross-chunk typing conflicts resolve at the deterministic merge step: instrument evidence wins; else majority; else `type_conflict`, excluded from strata pooling. Mechanical, logged per entity.
5. **Profile.** Register `v0_3_7` in `scripts/run_profiles.yaml`, sha-pinned, with the chunker profile it depends on. The whole-document profile stays on disk for the comparison record and is not deleted.
6. **Tests, positive-control discipline (methodology §7.5).** For each of 1–4, a seeded known-bad must fire the guard, and a mutation check must confirm the test measures the guard rather than something adjacent — the M2 failure mode from task 204bc046 (a retention test that was really measuring a date parse) is the specific thing to avoid. Report the mutation matrix.

**Exit §1:** full suite green, mutation matrix reported, committed and pushed. **STOP and report before §2 below.**

## 2. Dry run — ceilings before spend

`scripts/run_bulk_extraction.py --dry-run` over the five pilot documents under `--profile v0_3_7`. Report: chunk count per document, projected output tokens per chunk under the anchor contract (~1–2K expected), projected total per arm. Declare the per-run ceiling from that projection on `state/spend_ledger.jsonl` via `--ceiling-tokens`; an undeclared run is refused at the choke point (DD-022). Run `python -m kg.spend release-orphans` (dry-run, then `--commit`) first so a stale hold does not distort the band.

**Exit §2:** ceilings declared and reported. **STOP and report before §3.**

## 3. §3 — two extractor arms (the only model spend in this task)

Same five documents, same chunker, same judge, same pre-registered Instrument thresholds (`F_upper < 0.10`, `faithful ≥ 0.70`). Arms run sequentially, cheapest first, each against its own declared ceiling.

- **Arm A: `claude-haiku-4-5`.** If A clears the Instrument gate, extraction economics stop being a constraint.
- **Arm B: `claude-sonnet-5`.** Run only if A's admitted yield or faithfulness falls short. If A passes, B is not run and that is reported as a decision, not an omission.
- Opus 5 is not an arm.

Report per arm: admitted yield, F with Wilson interval, faithful, settled cost per document, quarantine rate by reason (with `span_partial` and `anchor_not_located` broken out separately — the erratum split those causes and the report must keep them split), and semantic edge count **unjudged** per §0(a).

**Exit §3:** verdict appended to `docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md`; RESULT written; `seldon cc complete cc_tasks/2026-08-27_chunked_pilot.md`; commit and push.

## 4. Sequencing and caps

§1 → (report, suite green) → §2 → (report, ceilings declared) → §3. Hard stop between sections; each section's spend reported against its ceiling before the next begins. §1 and §2 are zero and near-zero spend and carry no cap risk. If the weekly cap forces a choice inside §3, Arm A alone is the deliverable and Arm B defers.

## 5. Out of scope

Bulk extraction of the corpus (a separate decision that follows the §3 verdict, ordered by `state/t2_priority.json`); re-conversion of any document; the semantic stratum judge; T0 bibliographic work; Lane 2/3/4.
