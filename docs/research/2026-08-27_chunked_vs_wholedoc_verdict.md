# Chunked vs whole-document extraction — pre-registered verdict

Task `cc_tasks/2026-08-27_chunked_pilot.md`. Same five documents, same model (`claude-opus-5`, effort unchanged), same schema, same rules — `kg/extraction/chunked_template.md` is `prompt_template.md` v0.3.5 with the framing swapped, sha-pinned in the `chunked_v035` profile. **The unit of extraction is the only variable.**

Thresholds are the task's, unchanged and not re-read from any result: F_upper < 0.1, item-faithful >= 0.7, precondition pooled >= 20 per stratum.

**Gate reachability.** Under the aggregator's Wilson 95% interval, `F_upper < 0.1` is attainable only at **>= 35 facts**: below that, a PERFECT result (0 fabrications) still yields an upper bound above the threshold. This is arithmetic from the task's own F_STOP and the aggregator's own interval method, not a new threshold. A stratum whose facts are 1:1 with its items (`semantic_edge` — one fact per edge) and which sits below that count cannot pass however good the extraction is, and is recorded as GATE UNREACHABLE rather than judged: ADDENDUM-01 §1 forbids judging a sub-minimum sample, and paying for a foregone FAIL is the case it forbids.

Both arms were judged through ONE protocol at one set of versions — decompose 1.1.0, probe_judge 1.1.0, span_checks 1.0.0 — so the comparison is like-for-like. The whole-document arm's banked numbers in `2026-08-27_pilot_instrument_verdict.md` were produced under decompose 1.0.0 / probe_judge 1.0.0 and are NOT comparable to the rows below; they are superseded for comparison purposes, not retracted.

## Caveat — the chunked arm is a 44/128 partial (ADDENDUM-01 §1)

The chunked arm was stopped by the operator at 44 of 128 chunks. It covers **2 of the 5 pilot documents** (`data-readiness-for-ai-a-360-degree-survey` 30/30, `aidrin-hiniduma-2024` 14/18); `fcsm-23-02`, `from-accuracy-to-readiness` and `mitre-ai-maturity-model` have **no chunked extraction at all**. The whole-document arm spans all five. **The two arms therefore do not run on the same document mix**, and the per-document mixes are reported with every count below. Remaining chunks were not extracted by decision, not by failure: the cost question the arm existed to answer was settled at 65,637 settled/chunk (DD-023), and the faithfulness question is answerable from banked material.

## Verdict

| arm | stratum | admitted | facts in F-denominator | F [Wilson 95%] | item-faithful | precondition | pre-registered |
|---|---|---|---|---|---|---|---|
| chunked | Instrument | 92 | 80 | 0.0000 [0.0000, 0.0458] | 30/30 = 1.000 | Y | PASS |
| chunked | semantic_edge | 20 | — | — | — | — | GATE UNREACHABLE: 20 facts (1 per edge); a perfect result (0 fabrications) gives F_upper > 0.1; >= 35 facts needed |
| wholedoc | Instrument | 24 | 75 | 0.0000 [0.0000, 0.0487] | 22/24 = 0.917 | Y | PASS |
| wholedoc | semantic_edge | 21 | — | — | — | — | GATE UNREACHABLE: 21 facts (1 per edge); a perfect result (0 fabrications) gives F_upper > 0.1; >= 35 facts needed |

### What was counted, and what was judged

`admitted` above is the FULL admitted set of each arm. Where fewer items were judged, the cap is a spend bound declared before any label was bought, not a threshold: a smaller sample widens the Wilson interval, which makes PASS harder and never easier.

| arm | stratum | admitted | judged | doc mix (judged) |
|---|---|---|---|---|
| chunked | Instrument | 92 | 30 | {'aidrin-hiniduma-2024': 3, 'data-readiness-for-ai-a-360-degree-survey': 27} |
| chunked | semantic_edge | 20 | 0 | — |
| wholedoc | Instrument | 24 | 24 | {'aidrin-hiniduma-2024': 10, 'data-readiness-for-ai-a-360-degree-survey': 5, 'fcsm-23-02-a-framework-for-data-quality-case-studies': 7, 'from-accuracy-to-readiness-metrics-and-benchmarks-for-human': 1, 'mitre-ai-maturity-model': 1} |
| wholedoc | semantic_edge | 21 | 0 | — |

## Yield and cost

| doc | chunks | chunk tokens (med/max) | chunked settled | whole-doc settled |
|---|---|---|---|---|
| data-readiness-for-ai-a-360-degree-survey | 30 | 1477/1498 | 2,021,101 | 1,330,683 |
| aidrin-hiniduma-2024 | 18 | 1045/1498 | 795,582 | 903,365 |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 27 | 1368/1500 | 0 | 426,215 |
| from-accuracy-to-readiness-metrics-and-benchmarks-for-human | 18 | 684/1498 | 0 | 866,717 |
| mitre-ai-maturity-model | 35 | 570/1663 | 0 | 398,880 |
| **total** | 128 | | 2,816,683 | 3,925,860 |

Chunked extraction run `pilot_chunked_v035` settled 2,851,499 against a declared ceiling of 13,000,000; judge run `chunked_pilot_judge` settled 2,023,212 of 2,000,000.

## Diversion and resolution (chunked arm)

Diverted relations: 281 total, of which **47 `cross_chunk`** (16.7% of diversions)

```json
{
 "unstated": 94,
 "structural_inference": 20,
 "cross_chunk": 47,
 "other:schema_cannot_express": 12,
 "other": 108
}
```

Deterministic cross-chunk resolution (§4 — exact normalized surface form + recorded alias, no LLM-proposed merges):

```json
{
 "data-readiness-for-ai-a-360-degree-survey": {
  "node_events": 519,
  "surface_forms": 425,
  "merged_events": 140,
  "merge_rate": 0.2697,
  "stubs": 283,
  "stubs_resolved": 57,
  "stubs_unmerged": 226,
  "edge_events": 922
 },
 "aidrin-hiniduma-2024": {
  "node_events": 227,
  "surface_forms": 196,
  "merged_events": 79,
  "merge_rate": 0.348,
  "stubs": 94,
  "stubs_resolved": 10,
  "stubs_unmerged": 84,
  "edge_events": 322
 },
 "fcsm-23-02-a-framework-for-data-quality-case-studies": {
  "node_events": 0,
  "surface_forms": 0,
  "merged_events": 0,
  "merge_rate": 0.0,
  "stubs": 0,
  "stubs_resolved": 0,
  "stubs_unmerged": 0,
  "edge_events": 0
 },
 "from-accuracy-to-readiness-metrics-and-benchmarks-for-human": {
  "node_events": 0,
  "surface_forms": 0,
  "merged_events": 0,
  "merge_rate": 0.0,
  "stubs": 0,
  "stubs_resolved": 0,
  "stubs_unmerged": 0,
  "edge_events": 0
 },
 "mitre-ai-maturity-model": {
  "node_events": 0,
  "surface_forms": 0,
  "merged_events": 0,
  "merge_rate": 0.0,
  "stubs": 0,
  "stubs_resolved": 0,
  "stubs_unmerged": 0,
  "edge_events": 0
 }
}
```

## Mid-noun-phrase span check (span_checks 1.0.0)

Recorded, never subtracted from a denominator — excluding a class from a pre-registered metric would move the threshold by other means.

| arm | facts checked | on a mid-noun-phrase span |
|---|---|---|
| chunked | 80 | 9 |
| wholedoc | 75 | 12 |

## Per-rater agreement

`chunked`:
```json
{
 "claude-opus-4-8": {
  "n": 80,
  "agreement_with_map": 1.0,
  "type": "prov:SoftwareAgent"
 },
 "claude-sonnet-5": {
  "n": 80,
  "agreement_with_map": 1.0,
  "type": "prov:SoftwareAgent"
 }
}
```

`wholedoc`:
```json
{
 "claude-opus-4-8": {
  "n": 75,
  "agreement_with_map": 1.0,
  "type": "prov:SoftwareAgent"
 },
 "claude-sonnet-5": {
  "n": 75,
  "agreement_with_map": 0.9466666666666667,
  "type": "prov:SoftwareAgent"
 }
}
```

## Consequence

Strata meeting the pre-registered gate: **['chunked:Instrument', 'wholedoc:Instrument']**.
Lane 2/3 eligibility is recorded here and nowhere acted on: this task launches neither (§6).
