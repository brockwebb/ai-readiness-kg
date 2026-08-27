# Instrument-stratum verdict (ADDENDUM-05 §2): FAIL

Run `pilot_v035b_opus5` (re-declared 9M per §0): settled 5,517,758; cost/doc ~1,103,551 (informational). Model `claude-opus-5`, prompt v0.3.5; raters claude-opus-4-8 + claude-sonnet-5.
Per-doc admitted Instruments: {'data-readiness-for-ai-a-360-degree-survey': 5, 'aidrin-hiniduma-2024': 10, 'fcsm-23-02-a-framework-for-data-quality-case-studies': 7, 'from-accuracy-to-readiness-metrics-and-benchmarks-for-human': 1, 'mitre-ai-maturity-model': 1} (pooled 24 ≥ 20).
Facts judged: 78 in F-denominator; Dawid-Skene crowd-kit DawidSkene(n_iter=100).

| F | F_upper | pass(<0.1) | item-faithful | pass(≥0.7) |
|---|---|---|---|---|
| 0.07692307692307693 | 0.1578322988679013 | N | 0.2916666666666667 | N |

Per-rater agreement:
```json
{
 "claude-opus-4-8": {
  "n": 93,
  "agreement_with_map": 1.0,
  "type": "prov:SoftwareAgent"
 },
 "claude-sonnet-5": {
  "n": 89,
  "agreement_with_map": 0.9662921348314607,
  "type": "prov:SoftwareAgent"
 }
}
```

**Consequence (per §2):** Instrument stratum stays closed; Lanes 2/3 closed.

**Correction to the header line's cost/doc.** `settled ÷ 5` conflates extraction with this
run's decompose and judge calls. Measured extraction only, summed from the persisted raw
usage in `events/raw/reextract_v035b_pilot/`: 3,925,860 tokens for 5 docs = **785,172/doc**
(per-layer docs 866K–1,331K; single-pass docs 399K–426K). That is the number Lane 2/3 sizing
should use.

## Diagnosis (recorded finding; no threshold moved, no prompt written tonight)

Both pre-registered checks fail, and they fail for different reasons. Detail added after the
run by task `2026-08-27_pilot_finish`; the verdict above is the script's, unedited.

**What v0.3.5 fixed.** Instrument admission is no longer the binding problem: 24 Instruments
pooled across 5 docs (v0.3.4 admitted 1–7 per doc and failed the precondition outright). The
positive criterion and the name-in-span rule did their job.

**What now binds — the `method` attribute, not admission.** Non-entailed fact classes, pooled
over 89 facts (37 entailed):

| class | n | attribute |
|---|---|---|
| `span_truncated` | 27 | 26 × `method`, 1 × `owner` |
| `doc_level_attribute` | 11 | `year` (excluded from F by design) |
| `filled_attribute` | 6 | `owner` |
| `fabrication` | 6 | `method` |
| `subject_dropped` | 2 | `owner` |

Item-faithfulness is 7/24 because a single unfaithful `method` fact condemns the whole item,
and `method` is the attribute the model writes as a clause. So the ratio is a `method`-span
measurement, not a statement about the other Instrument attributes.

**Two distinguishable populations inside `span_truncated` (n = 27).** Content-word containment
of each fact against that attribute's own `grounding_spans["method"]` (mechanical, stopwords
dropped, ≥ 4 chars):

- **14** facts have *every* content word inside the span. Example: span `"…an open-source
  solution designed for data profiling, cleansing, and monitoring capabilities"`, fact
  `"is designed for data monitoring capabilities"` — the decomposer redistributed a
  coordination, and both raters called the redistributed form not span-entailed.
- **13** facts have at least one content word outside the span, usually because the model
  quoted a fragment that stops mid-noun-phrase. Example: span `"evaluate the completeness,
  timeliness, accuracy, and consistency of the state-reported commercial"` — cut before its
  head noun.

Rater agreement with the MAP estimate is 1.00 (opus-4-8) and 0.97 (sonnet-5), so both
populations are systematic, not label noise.

**Consequence for the next fix (not made here).** The first population is a *measurement*
question — whether a coordination redistributed by `probe_decompose` should count as
span-entailed — and it touches the probe protocol, which is pre-registered and frozen for
this exercise. The second is an *extraction* question: `grounding_spans["method"]` must be a
complete clause, not a mid-phrase cut. Fixing the second without ruling on the first would
move at most 13 of 27; neither is a threshold adjustment and neither is authorized by this
task. Both are recorded here as the input to whatever decides the Instrument stratum next.

**Label-set provenance.** The judge ran in two parts (a daily-band refusal at 18:53Z, relaunch
at 21:40Z under the raised band). 5 opus-4-8 labels from an intermediate fact set were
orphaned by that relaunch and are dropped by `probe_aggregate` with a warning (fix committed
in `156a91c`); opus-4-8 shows 93 labels over 89 facts because 4 facts carry a duplicate label
from before the interruption. Agreement 1.00 — no effect on the MAP estimate.
