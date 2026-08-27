# ADDENDUM-05 to `2026-08-26_overnight_burn.md` (Seldon cd8449de)

**Date:** 2026-08-27 ~13:50 ET
**Scope:** pilot ceiling correction; per-stratum decoupling of consequences; semantic-edge diagnosis and, if warranted, prompt v0.3.6 (evidence-set grounding); band priority. Thresholds unchanged. ADDENDUM-02 §Lane 4 unchanged except the priority clause below.

## 0. Own the arithmetic

The 4M pilot ceiling was derived from 4.8-era per-call cost. Measured Opus 5 cost with per-layer fallback is ~977K/doc. Re-declare `pilot_v035b_opus5` at **9M** (5 docs + Instrument judge + margin). The refusal at 3.91M is retained on the ledger as a correct guard event; the 4 banked extractions are reused, not re-run.

## 1. Band priority for today (UTC 08-27 remainder, then the 00:05Z roll)

Lane 4 finishes stage 2 and runs the 100-item acceptance gate (small). **Relocation resume and the 50-item re-judge wait for the 00:05Z roll** — they are cleanup on old extractions; the pilot work below gates new extraction and gets today's remaining band first. Implement as: Lane 4 driver checks `kg.spend status` before starting relocation; if `committed_today + 5M > daily_tokens`, sleep to 00:05Z.

## 2. Instrument stratum — judge now, verdict stands alone

Extract doc 5 under the re-declared ceiling. Instrument precondition is met (23 pooled ≥ 20); run the Instrument judge exactly as pre-registered. **Per-stratum verdicts are independent from here**: Instrument PASS unlocks Lane 2 for the Instrument stratum only (`superseded_strata: [Instrument]`); the semantic stratum's kernel-era edges are *not* superseded by a prompt that admits ~zero of them. Lane 3 (34 new docs) does **not** start on an Instrument-only pass — running new documents under a prompt with a diagnosed edge defect means re-extracting all 34 later at ~1M each. Lane 3 waits for both strata.

## 3. Semantic stratum — measure the suppression before touching the prompt (zero spend, then ≤ 2M)

**3a. Mechanical triage of staged candidates (zero spend).** For every `proposed_relationships` entry from the 5 pilot docs (and, for the same docs, every kernel-era semantic edge in the projection): locate the two endpoint surface forms (name or recorded alias) and a predicate cue (verb/noun phrase matching the edge type's cue list — write the cue list per edge type into `kg/extraction/edge_cues.yaml`, sha-pinned) in the document text. Classify:
- `single_span`: endpoints + cue within one sentence (the v0.3.5 rule should have admitted it — model over-diverted);
- `evidence_set`: endpoints + cue within ≤ 3 sentences and ≤ 800 chars, not one sentence;
- `unlocatable`: some element not found within 800 chars (correct diversion or inference).
Report the three counts per doc and pooled, for both populations. If `single_span + evidence_set` pooled < 20, the semantic stratum's problem is not the span rule; write that finding, close the stratum for today, no v0.3.6.

**3b. Entailment judge on the locatable candidates (≤ 2M, run id `edge_suppression_judge`).** Judge all `single_span` + `evidence_set` candidates (cap 120, random) with the probe protocol, presenting the located evidence set as the grounding. Pre-registered read: **fact-level entailed ≥ 0.85 pooled** ⇒ the suppression is over-suppression and v0.3.6 is justified; below ⇒ the diverted candidates are mostly unfaithful, v0.3.5's rule is doing its job, close the stratum for today with the number.

**3c. v0.3.6 (only on 3b PASS; zero spend to author).** Semantic edges ground on an *evidence set*: 1–3 verbatim spans, each ≤ 400 chars, jointly covering both endpoint surface forms and a predicate cue, all within 800 chars of each other in document order. Prompt states it as the rule with one example; `output_schema.json` allows `grounding_spans: [..]` on edges; parser validates joint coverage and the distance bound, quarantines otherwise, and routes heading/list inference to `proposed_relationships` exactly as now. Instrument rules untouched. Profile `reextract_v036`, sha-pinned. Unit tests: two-sentence relation admitted; > 800-char separation quarantined; single-endpoint span quarantined.

**3d. Semantic pilot under v0.3.6.** Same 5 docs. First attempt: `--resume` each pilot doc's Opus 5 session for an **edges-only turn** under the v0.3.6 rule (document is the cached prefix; output is one layer). If a session cannot be resumed, full re-extraction of that doc. Run id `pilot_v036_edges`, ceiling 9M. Pooled precondition ≥ 20 admitted semantic edges; judge as pre-registered; **F_upper < 0.10, item faithful ≥ 0.70** unchanged. PASS ⇒ semantic stratum unlocked: Lane 2 superseding scope adds `semantic`, and Lane 3 starts under the profile that passed both strata (`reextract_v036`, which carries the v0.3.5 Instrument rules). Note the Instrument verdict from §2 carries over: v0.3.6 changes no Instrument text; record the sha diff as evidence.

## 4. Why the "no v0.3.6 today" clause is set aside

That clause forbade a second *guess*. §3 is a measurement (3a, 3b) with a prior-art mechanism (evidence-sentence grounding, DocRED) that only becomes a prompt change after the numbers say so. Thresholds do not move at any step.

## 5. Exit for CC

Instrument verdict on disk; 3a counts on disk; 3b verdict on disk; on PASS, v0.3.6 authored, 3d verdict on disk, and Lanes 2/3 launched detached under the passing profile with wall stop `2026-08-28T03:30:00Z`. RESULT dated section; SUMMARY at driver exit covers everything from the ledger.
