# Pilot re-extract v0.3.5b (opus-5) — verdict: STOP:run_ceiling (operationally FAIL — Lanes 2/3 closed)

Task `cc_tasks/2026-08-26_overnight_burn.md` ADDENDUM-02 protocol under the ADDENDUM-04
model pin (`claude-opus-5`; preflight 3/3 returned `claude-opus-5`). Run
`pilot_v035b_opus5`, declared ceiling **4M**.

**What happened:** the DD-022 guard refused the 5th document's reservation at committed
3,907,767 + estimate 257,708 > 4,000,000 (`scope=run`, 1 refusal, zero overshoot). The
judge was never reached; the pooled precondition was never formally evaluated. The
machine does not raise its own declared ceiling — that decision returns to the operator
with the arithmetic below.

## Measured per-doc (4 of 5 extracted)

| doc | instruments | semantic edges | span_lacks_name | emission | output tokens |
|---|---|---|---|---|---|
| `data-readiness-for-ai-a-360-degree-survey` | 5 | 1 | 2 | per_layer | 157,768 |
| `aidrin-hiniduma-2024` | 10 | 0 | 0 | per_layer | 121,569 |
| `fcsm-23-02-…-case-studies` | 7 | 2 | 1 | single_pass | 108,028 |
| `from-accuracy-to-readiness-…` (38 prior sem. edges) | 1 | 0 | 1 | per_layer | 119,626 |
| `mitre-ai-maturity-model` (32 prior sem. edges) | — refused at ceiling — | | | | |

Pooled so far: **Instruments 23 (≥ 20 met with a doc to spare)** — the v0.3.5 positive
criterion holds under Opus 5. **Semantic edges 3 (needs ≥ 20)** — on present trajectory
the precondition would fail even with doc 5.

## Findings for the operator (each a number, not a guess)

1. **Ceiling arithmetic.** Opus 5 under prompt v0.3.5 costs ~977K settled/doc on these
   docs (3.91M / 4). The ADDENDUM-02 protocol (5 docs + decompose + 2×judge ≈ +1.5M)
   needs a ceiling around **7M**, not 4M (a 4.8-era number). Re-entry is a one-line
   ceiling re-declare; everything else is in place and 4 extractions are already on the
   tagged shard (`batch-013_reextract_v035b`) for reuse if the operator permits reuse.
2. **Semantic-edge scarcity survives stratum-matched docs.** The doc selected FOR its 38
   prior semantic edges admitted 0 (1 instrument, output truncated → per_layer). The
   v0.3.5 span rule (span must state the relation) plus endpoint-resolution attrition is
   suppressing nearly everything the old prompt asserted at F≈0.26 fabrication. Whether
   that is correct suppression or over-suppression is exactly what the judge would have
   measured — it needs the re-declared ceiling, or a review of the
   `proposed_relationships` staging (where the model now self-routes these).
3. **Opus 5 output truncation is real at 128K.** 3 of 4 docs came back with unparseable
   single-pass envelopes at 108–158K output tokens; the per-layer fallback recovered all
   three (it is now load-bearing, not an edge case). `truncation_suspect_tokens: 40000`
   stands; the per-doc output maxima are recorded above per ADDENDUM-04.

**Consequences:** Lanes 2/3 stay closed (no PASS). No prompt revision (none is indicated
by this data — the open question is judgment of the suppression, not another rule). No
ceiling raise from the machine. Lane 4 resume continues unaffected.
