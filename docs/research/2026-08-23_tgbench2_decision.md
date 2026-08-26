# TrustGraph benchmark v2 — decision (task 2026-08-23_trustgraph_benchmark_v2, Seldon 36a5c0e1)

Model held constant: both extractors ran `claude-opus-4-8` through the Claude Code CLI (ours: `model_stub`; theirs: the fork's `claude-cli-completion` backend). 5 pilot documents.

## Measurements
| | TrustGraph (OntoRAG flow) | Ours (v0.3.2 pipeline, coverage gate ON) |
|---|---|---|
| items (schema-typed) | 1,613 | 157 admitted (+511 quarantined `span_partial`) |
| facts generated / judged | 3,290 / 103 (seeded sample, budget-cut) | 475 / **0 — unjudged: ceiling consumed** |
| extraction tokens | 6,738,175 (168 calls, 123 min) | 575,106 (5 calls, ~33 min) |
| **F (fabrication, Wilson 95%)** | **0.126 [0.075, 0.204]** vs their own evidence chunks | 0.079 [0.063, 0.099] — **probe-measured (2026-08-22), cited as context, not re-measured on this run** |
| capture-defect rate (judged sample) | 0.03 (span classes barely arise: their "span" is a whole chunk) | 52% of failures at probe (span discipline is our gate, not theirs) |
| evidence discipline | chunk-level; **chunk verbatim-vs-source rate 0.915** | verbatim span, mechanically verified, coverage-enforced |
| **R (their coverage of our admitted items)** | **52/157 = 0.331** (vs admitted+quarantined: 52/668 = 0.078) | — |
| per-family F (TG) | Claim 0.000 [0, 0.242] · node 0.078 [0.031, 0.185] · **edge 0.225 [0.123, 0.375]** | — |

## Verdict — pre-registered rule applied: **harvest-components**
Adopt-evaluate required F_tg_upper < F_ours_point AND C_tg < C_ours AND R ≥ 0.7. Two grounds fail independently:
1. **R = 0.33 < 0.7.** TG produces ~10× the typed items but they are different items — chunk-local paraphrases and structural fragments that rarely match our extractions (type + similarity ≥ 0.8).
2. **F_tg_upper = 0.204 > F_ours_point = 0.079**, judged against their own chunks — an easier evidentiary bar than our spans. Their edges fabricate at 0.225 — the same structure-inferred-relation failure our probe flagged in `edge:semantic`.

Caveats, recorded not hidden: our-side fact-level F on THIS run went unjudged (the 8M ceiling was consumed at 8.11M — TG extraction alone took 6.74M; overshoot 1.3% from the budget guard's 30-s poll); F_ours is the probe's measurement of the same extractor family on overlapping documents. The comparison basis for R shrank because our coverage gate (2026-08-23) quarantines pointer-span items; R against admitted+quarantined is 0.08 — fails the bar either way.

## Harvested components (adoptable, recorded)
1. **Ontology-constrained extraction pays**: their domain/range validator dropped 253 over-proposed relations at extraction time — the same class our parser routes to `proposed_relationships`. Our SHACL gate (b6900da4) covers this post-hoc; an extraction-time ontology check is worth a follow-on.
2. **Chunk-anchored provenance is cheap but weak**: chunk verbatim rate 0.91 yet F still 0.126 — evidence-locality without entailment discipline does not buy faithfulness. Keeps DD-015's span-coverage direction validated.
3. **Their config-service ontology format** loses union domains/ranges and alignments (14+4+1+12 enumerated) — count-fidelity checks are blind to expressiveness loss; recorded for any future interop.
4. Backend contract (`LlmService`) is clean; the claude-cli backend (fork `9aef0ef0`) is reusable for any future TG evaluation. Upstream-offer decision left to the operator (public contribution under his name).
