# Pilot re-extract v0.3.4 — verdict: FAIL (no items)

Docs ['data-readiness-for-ai-a-360-degree-survey', 'aidrin-hiniduma-2024', 'fcsm-23-02-a-framework-for-data-quality-case-studies']: the corrected prompt produced 0 Instrument items and 0 semantic edges. Over-correction is a finding for the morning, not a bulk go.

## Diagnosis (added post-verdict from the raw responses, zero spend)

The pre-registered rule fired on "zero items in both strata"; per the task, this is a
finding for the morning, **not a prompt tweak tonight**. What the raws actually show:

| doc | what happened |
|---|---|
| `aidrin-hiniduma-2024` | **Extraction unusable, not a judged zero**: 67,057 output tokens but no recoverable envelope layers (`_extract_json` found no layer lists — consistent with output truncation mid-JSON). The lane counted it as 0 items; pilot-integrity caveat. AIDRIN did not even appear as a Concept. |
| `data-readiness-for-ai-a-360-degree-survey` | Model emitted **0 Instruments for a survey OF instruments** — over-demotion under the new cited-only rule (surveyed instruments read as "cited-only" → Concepts). 22 semantic edges emitted; 2 routed by the v0.3.4 span rule, **100 edges dead on unresolved endpoints** because 72 nodes quarantined first (38 `span_partial` on `name`, 25 missing spans) — only 35/207 items admitted. |
| `fcsm-23-02-…-case-studies` | 1 Instrument emitted (SSDQ); quarantined: `grounding_span not found in source text` (non-verbatim span). 3 semantic edges emitted, none survived endpoint resolution. |

### Top-3 patterns for the morning

1. **Over-demotion of first-party instruments.** The "cited-only instruments are Concepts"
   rule needs a positive criterion (the document *specifies, applies, or documents* the
   instrument ⇒ Instrument node), stated with an example — AIDRIN in its own paper must be
   an Instrument.
2. **Span-coverage-on-`name` interaction.** Under prompt v0.3.4 the model spends its spans
   on attribute evidence and under-covers node `name`s; 38 `span_partial` on `name` in one
   doc collapsed the endpoint graph (100 edges unresolved). The prompt should restate that
   the node's own `grounding_span` must contain the node's name/text verbatim.
3. **Output-length ceiling on dense docs.** The aidrin response (67K output tokens, no
   parseable envelope) looks like mid-JSON truncation. Candidate fixes for a follow-on:
   per-layer emission calls, or a length guard that detects a truncated envelope and
   retries with a reduced scope — never silently counting a broken parse as zero items
   (the lane now reports it; the counting defect is recorded here).

Re-run trigger: a revised prompt (v0.3.5) addressing 1–2 re-enters through this same
pilot gate; Lanes 2/3 stay closed until it passes.
