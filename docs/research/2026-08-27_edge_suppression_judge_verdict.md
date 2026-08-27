# Edge-suppression judge (ADDENDUM-05 §3b): suppression is correct — no v0.3.6

Candidates judged: 89 of 89 locatable (§3a); evidence sets presented as grounding. Raters claude-opus-4-8 + claude-sonnet-5, Dawid-Skene crowd-kit DawidSkene(n_iter=100); run `edge_suppression_judge` settled 1,323,023 (ceiling 2M).

**Fact-level entailed: 54/89 = 0.607** (pre-registered pass ≥ 0.85). Per class: {'suppressed:evidence_set': '19/37', 'suppressed:single_span': '35/52'}

Per-rater agreement:
```json
{
 "claude-opus-4-8": {
  "n": 89,
  "agreement_with_map": 0.9775280898876404,
  "type": "prov:SoftwareAgent"
 },
 "claude-sonnet-5": {
  "n": 89,
  "agreement_with_map": 0.9550561797752809,
  "type": "prov:SoftwareAgent"
 }
}
```

## Consequences and diagnosis (task `2026-08-27_pilot_finish` §3; verdict above is the script's, unedited)

**Pre-registered read, applied.** 0.607 < 0.85 ⇒ the diverted relations are mostly *not*
faithful, v0.3.5's diversion rule is doing its job, **no v0.3.6 is authored** and §4 is
skipped. ADDENDUM-06's premise — that the 52 `single_span` candidates are relations the rule
should have admitted — does not survive measurement: they are 35/52 = 0.673 entailed, well
under the bar. Thresholds were not moved.

**§3a's mechanical proxy is weak, and that is the methodological finding.** "Both endpoint
surface forms plus a predicate cue inside one sentence" predicted faithfulness at 0.67, and
inside a ≤ 3-sentence, ≤ 800-char evidence set at 19/37 = 0.51. Co-occurrence of the two
endpoint strings near a cue word is not evidence that the sentence *asserts that relation* —
the classic distant-supervision false-positive, and the reason DocRED-style corpora label
evidence sentences by hand rather than by co-occurrence. A future triage that wants to
predict admissibility needs a relation-stating test, not a proximity test.

**The unfaithfulness is not a v0.3.5 artifact — it is in the graph too.** Split by population:

| population | entailed |
|---|---|
| `p2_live_kernel_era` (semantic edges live in the projection) | 40/66 = 0.61 |
| `p1_proposed_v035b` (diverted by the opus-5 pilot) | 14/23 = 0.61 |

Identical rates. The kernel-era edges *already written to the graph* for these 5 docs are, in
the locatable subset, no more faithful than the ones v0.3.5 refused to write. Of the 35
not-entailed, 23 are `fabrication` (the relation contradicts the evidence or is absent from
it), 11 `span_truncated`, 1 `subject_dropped`. **This is a graph-quality finding about live
`has_component`/`subtype_of` edges, not only a prompt finding**, and it is recorded here for
whatever addresses the semantic-edge layer next. It is out of this task's scope to act on.

By edge type: `has_component` 50/80 = 0.62, `subtype_of` 4/9 = 0.44. By document, entailment
ranges 0.20 (`data-readiness-for-ai-a-360-degree-survey`, n=5) to 0.82
(`from-accuracy-to-readiness…`, n=11); `mitre-ai-maturity-model` — the doc that supplied 18 of
the 21 pilot semantic edges — sits at 19/35 = 0.54.

**Semantic stratum: closed**, per §3b's own rule. With the Instrument stratum also FAIL
(`2026-08-27_pilot_instrument_verdict.md`), Lanes 2 and 3 have no passing stratum and no
passing profile.
