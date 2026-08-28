<!--
Versioned atomic-fact judge prompt (task 2026-08-22_faithfulness_probe, Phases 3-4; DD-015/16).
Rendering substitutes {{facts_json}} (a list; batch of 1..N in randomized order).
probe_judge_version: 1.1.0
1.1.0 (2026-08-27, task 2026-08-27_chunked_pilot §5): the span presented for a fact about an
  attribute that carries its own `grounding_spans` entry is THAT span, not the node's own.
  See scripts/probe_judge.py::span_for. The prompt text below is unchanged.
-->
# Atomic-fact faithfulness judgment

For each fact below, decide whether the **grounding span alone** entails the fact. The
`window` (document text around the span) is evidence for ONE purpose only: distinguishing a
fact that the document supports but the span omits (`subject_dropped` / `span_truncated`)
from a fact the document does not support at all (`fabrication`). Never label a fact
`entailed` on the strength of the window.

Labels: `entailed` | `not_entailed`.
When `not_entailed`, assign exactly one class:
- `doc_level_attribute` — the fact is a document-level attribute (a date, an operator inferable
  from the name, a harvest-time field) a span would not normally carry.
- `span_truncated` — the span is a cut fragment of the item's own text; the fact lies in the
  cut portion (the window shows the rest).
- `subject_dropped` — the span carries the predicate/values; the subject or agent comes from
  surrounding context (the window supports it).
- `filled_attribute` — a description/steward/owner/scale/version-type value that the span does
  not support and the window does not clearly supply.
- `fabrication` — the fact contradicts the span, or asserts content absent from the span AND
  absent from the window.
- `grade_misassigned` — an evidence-grade/classification fact inconsistent with the document.
When `entailed`, class is null.
Confidence: 0..1, your probability that the label is right.

Output **strict JSON** only — no prose, no fence:
{"judgments": [{"fact_id": "...", "label": "entailed|not_entailed", "class": "<class>|null", "confidence": 0.0}, ...]}
Every input fact_id must appear exactly once.

Facts:
{{facts_json}}
