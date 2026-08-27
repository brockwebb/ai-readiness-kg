# Pilot re-extract v0.3.5 — verdict: FAIL:harness_or_prompt

Precondition not met: items > 0 in BOTH strata for >= 2/3 docs (got 1/3). Judge not run (ADDENDUM-01).

| doc | instruments | semantic edges | span_lacks_name precheck | emission |
|---|---|---|---|---|
| `data-readiness-for-ai-a-360-degree-survey` | 2 | 5 | 1 | per_layer |
| `aidrin-hiniduma-2024` | 6 | 0 | 12 | single_pass |
| `fcsm-23-02-a-framework-for-data-quality-case-studies` | 1 | 0 | 4 | single_pass |

## Diagnosis (from the raws, zero spend — judge correctly not run)

**What v0.3.5 fixed, measured against last night's v0.3.4 run on the same docs:**

- **Instrument over-demotion: fixed.** 0 → 9 Instrument nodes across the three docs
  (aidrin 0 → 6 — the paper's own instrument is back; fcsm 0 → 1; survey 0 → 2).
- **Name-in-span: fixed.** `span_lacks_name` precheck 38 (one doc alone) → 1 / 12 / 4.
- **Truncation fallback: fired and worked.** The 360-survey came back truncated again and
  the per-layer fallback produced a usable merged extraction (`emission: per_layer`);
  aidrin ran clean single-pass this time.

**Why the precondition still failed (semantic edges = 0 in 2/3 docs):**

- aidrin: the model emitted **0** semantic edges and self-routed **8** candidate relations
  to `proposed_relationships` — the v0.3.4/5 heading-inference rule operating as designed.
- fcsm-23-02: **1** semantic edge emitted; the v0.3.4 span rule routed it (span lacked an
  endpoint name).
- The pilot docs were selected by **Instrument count**; instrument-heavy methods/case-study
  papers plausibly contain few sentences that *state* has_component/subtype_of/consumes
  relations. The ADDENDUM-01 precondition requires both strata **per doc** (a conjunction),
  which such docs may be structurally unable to meet even under a perfect prompt.

### Top-3 patterns (per the FAIL-report structure)

1. **Precondition design, not prompt failure, is the leading explanation for this FAIL**:
   the per-doc conjunction penalizes docs that legitimately lack semantic-relation
   sentences. A follow-on could (a) select pilot docs per stratum (instrument-heavy for
   Instrument, ontology/spec-heavy for semantic edges), or (b) apply the >0 precondition
   per stratum across the pooled 3-doc sample. **Threshold and protocol unchanged tonight**
   — ADDENDUM-01 permits no second revision; this is for the morning.
2. **Endpoint-resolution attrition remains high** (67 / 56 edges dead on unresolved
   endpoints in the two single-pass docs): edges referencing nodes that the coverage gate
   quarantined. Downstream of node admission, not the semantic-edge rule.
3. **Self-routing works**: the model now places structure-inferred relations in
   `proposed_relationships` (8 + 6 staged for review) instead of asserting them — the
   fabrication vector the probe flagged (F 0.26) is being diverted, not emitted. The
   staged sets are reviewable evidence for pattern 1.

Per ADDENDUM-01: Lanes 2/3 stay closed; no v0.3.6 (one grounded revision only). The v0.3.5
instrument-side gains are real and measured; the semantic-edge stratum needs either a
stratum-matched pilot or a pooled precondition — an operator decision, not a tonight tweak.
