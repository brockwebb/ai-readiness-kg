# Foil notes for writeup task f1da94c6 (chunked-pilot publication)

**Date:** 2026-08-30. Referenced by ResearchTask f1da94c6; read at dispatch. Corrections here supersede chat characterizations.

## Foil 1 — Karpathy LLM Wiki (gist, 2026-04-04) — CORRECTED

Do NOT claim the pattern has no quality mechanism. It has one: lint is a first-class operation (contradiction detection, stale claims, orphans, missing cross-references), and ecosystem extensions add provenance fields, confidence levels, and recency/authority-based contradiction resolution.

The accurate critique: **lint measures coherence, not correspondence.** All checks run the wiki against itself; none run it against sources with a denominator. No error rate, no threshold, no gate. "Every claim traces back to raw/" is design intent, never verified or reported as a rate. A lint-clean wiki can be consistently fabricated (community's own phrasing: a wiki can become consistent around one stale claim).

Pairing with our result: Arm A was the inverse — perfect correspondence (F=0.0000), poor completeness (0.347 yield). Coherence and correspondence dissociate in both directions; the wiki pattern instruments neither correspondence nor completeness. Our gate set instruments both (faithfulness gate + pre-registered yield floor).

## Foil 2 — OKF (Google, v0.1 2026-06-12, v0.2 2026-07-25)

Interchange format, deliberately quality-agnostic; own stated limits: markdown doesn't fix knowledge quality, no conflict detection/resolution. Enrichment-pipeline articles (e.g. Medium/Estari) add lint = 13 spec-conformance rules — format checks, zero content measurement — refreshed by unvalidated LLM extraction on every commit. v0.2 trust/provenance/freshness fields are a vocabulary for trust signals with no mechanism to earn them; our evidence_class/instrument-version/adjudication state can populate them honestly (serving-layer parking-lot item).

## Shared thesis

Agent-memory patterns ship quality *operations* (lint) without quality *measurement* (error rates against sources, pre-registered thresholds). The Census analogy: publishing estimates with no MOE. The pilot demonstrates what the measurement layer costs and catches, including a failure (silent under-extraction) invisible to every check both foils possess.

---

## Appended 2026-08-30, post re-derivation (35094dc4 RESULT). Verdict landed; f1da94c6 is ungated.

### New centerpiece candidate — the floor was 63% edges

The pre-registered yield floor (45.23/chunk, 0.60 ratio) was a combined node+edge count; the ground-truth rubric — like any item-annotation instrument — measures nodes only. The floor's majority component (62.5%) was never commensurable with the instrument that would validate it. Three arms were designed to close what was mostly an edge-volume gap, and the "wild over-extractor" comparator sits at 0.93× ground truth on nodes. This strengthens the shared thesis a full step: it is not enough to *have* quality measurement (this pipeline did — pre-registered, gated, the works); **the gate's unit must be commensurable with its validating instrument's unit**, or the measurement layer manufactures the very phantom defect it exists to prevent. Self-implicating, which is what makes it publishable rather than promotional. The Census analogy sharpens: an MOE computed on a different universe than the estimate. (DD-028 candidate; the bulk task 82c281ff appends it.)

### Pre-registration integrity exhibit — the Jaccard(∅,∅) change

The agreement metric's convention changed mid-task (0 → 1 for empty–empty, exclusion of uninformative chunks from the threshold mean), after per-pass counts were visible, before any agreement value was computed. Mathematically correct, mutation-checked (the stop still fires on informative disagreement), and honestly sequenced in the RESULT. Writeup framing: pre-registration does not eliminate mid-task instrument judgment; it forces the judgment to be *recorded with its sequencing* so readers can audit whether it could have rescued a failure. Pairs with DD-026 (a threshold whose precondition makes it unsatisfiable) as two species of the same genus: gate arithmetic diverging from gate intent.

### Impossible values as cheap bug detectors

Two scorer defects were caught only because outputs were impossible (precision 1.091; non-reconciling totals that exposed the unit error). Neither had a test. Small methodological point worth a paragraph: range/consistency invariants on metrics are near-free assertions and caught what 440 tests did not.

### Sixth instance — tests measuring artifacts, not generators

M85/M86: sample tests read the committed sample file instead of driving the draw. Sixth recorded instance of the class in this project; the mutation matrix caught it every time, at the cost of one rework cycle each. The writeup's methodology section should report the class, the count, and the standing fixture rule as an empirical finding about AI-authored test suites, not a confession.

### Already-noted, now with the exhibit complete

TAC-KBP provenance rule independently re-derived by this repo's v0.3.4 parser at full cost (§7.5 prior-art doctrine) — the re-derivation task then adopted the published rule by citation, closing the loop: same rule, once expensive, once free.
