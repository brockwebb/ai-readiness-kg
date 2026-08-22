# TEVV Phase 3 — Faithfulness judging (task 2026-08-22_kernel_tevv)

Judge: `claude-opus-4-8` (the pinned extractor), `kg/extraction/judge_template.md` **judge_version 1.0.0**, one item per `claude -p` call via `model_stub.invoke` (hermetic cwd, Max OAuth, substitution gate). 200 items (Phase 1 sample), 200 judged, 0 errors after resume. Raw envelopes: `events/raw/tevv_judge/`; judgments: `corpus/staging/metrics/tevv_faithfulness_judgments.jsonl`. Tokens 7,160,002; **cost UNKNOWN** (unpriced; envelope estimate $40.00 lower bound). Status: **`uncalibrated_pending_human`** — the 40-item human subset (`tevv_human_subset.jsonl`) has no labels yet; same-family judge (DD-013).

Incident: the Claude Code CLI auto-updated at 13:17 UTC and `claude` did not resolve for a few seconds; the judge's first pass and its immediate retry both died at item 59 (`FileNotFoundError: 'claude'`). Relaunched; resumed by item id; no item was judged twice.

## Precision (strict entailment by the grounding span alone)
**Pooled: 0.535** (gate ≥ 0.90 → **FAIL**). Stratum minimum 0.00 (gate ≥ 0.85 → **FAIL**).

| stratum | n | entailed | precision | vs 0.85 |
|---|---|---|---|---|
| Instrument | 10 | 0 | 0.00 | **FAIL** |
| Measure | 10 | 1 | 0.10 | **FAIL** |
| Standard | 10 | 3 | 0.30 | **FAIL** |
| Concept | 20 | 7 | 0.35 | **FAIL** |
| Claim:peer_reviewed_experiment | 10 | 4 | 0.40 | **FAIL** |
| Tool | 10 | 4 | 0.40 | **FAIL** |
| Platform | 10 | 5 | 0.50 | **FAIL** |
| edge:semantic | 20 | 11 | 0.55 | **FAIL** |
| Claim:inference | 10 | 6 | 0.60 | **FAIL** |
| Claim:ungraded | 10 | 6 | 0.60 | **FAIL** |
| Definition | 10 | 6 | 0.60 | **FAIL** |
| Framework | 10 | 6 | 0.60 | **FAIL** |
| Practice | 10 | 6 | 0.60 | **FAIL** |
| Claim:measured_practitioner | 10 | 7 | 0.70 | **FAIL** |
| Claim:practitioner_assertion | 10 | 8 | 0.80 | **FAIL** |
| Claim:platform_official | 10 | 9 | 0.90 | PASS |
| edge:document_structural | 20 | 18 | 0.90 | PASS |

## Why (93 rejections, tagged from the judge's reasons)
| failure mode | n |
|---|---|
| A: name grounded, attributes unsupported | 65 |
| B: truncated span | 17 |
| C: other / content mismatch | 11 |

- **A — span grounds the name, not the attributes.** The extractor quotes a phrase that locates the item ("data anonymization", "DDI", "Flesch") and then fills `description`, `owner`, `year`, `steward`, `version`, `response_type` from elsewhere in the document or from its own knowledge (RFC 3629's steward is the IETF — true, and absent from the span). Under the pre-registered rule (entailed by the grounding span) those are unsupported. Instrument 0/10, Standard 3/10, Measure 1/10 and Concept 7/20 are almost entirely this mode: the *span* is a pointer, the *item* is a record.
- **B — truncated spans.** Mid-sentence fragments ("Is the methodology internally", "does not show a") satisfy the string-match gate while omitting the predicate the Claim asserts. The grounding gate verifies that the quote *exists*, not that it *carries the assertion*.
- **Where it holds:** `Claim:platform_official` 0.90 and `edge:document_structural` 0.90 — short, self-contained statements quoted whole.

## What this measures and what it does not
The pre-registered statistic is strict by design ("validity floor no looser than the admission floor"): the grounding span is the only evidence a stranger can check, so an attribute not in the span is not citable. A lenient reading (name/core supported, attributes sourced elsewhere in the document) would score much higher, but it is a different claim — and it is exactly the claim the `grounding_span` property does **not** make. The finding stands: **"no grounding span, no write" guarantees provenance of location, not entailment of content.** Thresholds unchanged.

## Follow-on (recommended, separate task — no threshold or prompt change here)
1. Extraction prompt: attributes must be null unless covered by the span, or carry their own span (per-attribute grounding); spans must be sentence-complete (reject fragments ending mid-clause — a mechanical check the parser can add next to the string-match).
2. Judge: keep v1.0.0 as the strict instrument; add a second, labelled lenient mode only if the operator wants the "core supported" number reported beside it.
3. Human calibration: fill `tevv_human_subset.jsonl`; recompute judge–human agreement (Cohen's κ on 40) and re-stamp the status.
