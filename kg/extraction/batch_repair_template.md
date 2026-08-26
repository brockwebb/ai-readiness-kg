<!--
Versioned batched repair prompt (task 2026-08-23_batched_repair_resume Phase 2; DD-019).
The DOCUMENT comes before the items so consecutive batches on the same document share a
cached prefix. Rendering substitutes {{document_id}}, {{document_text}}, {{items_json}}.
batch_repair_version: 1.0.0
-->
# Batched span relocation and attribute adjudication against ONE document

You will judge a batch of tasks against the single document below. Two task kinds:

- kind "relocate": given `item_text`, return the **shortest contiguous passage copied
  verbatim from the document** that fully supports it, or "NONE" if no contiguous passage
  supports the whole item. Never paraphrase, never stitch fragments, never add words.
- kind "attribute": given `attribute` and `value` (extracted from this document but not
  present in its original grounding span), decide whether THIS DOCUMENT supports the value.
  Supported -> verdict "supported" with the shortest verbatim passage showing it.
  Not supported (absent, contradicted, or only inferable from outside knowledge) ->
  verdict "stays_null".

Output **strict JSON only**, no prose, no fence — an array with EXACTLY one object per
input id, same ids:
[{"id": "...", "verdict": "passage|NONE|supported|stays_null", "passage": "<verbatim or null>"}, ...]
For "relocate": verdict is "passage" with the passage, or "NONE" with passage null.

Document id: {{document_id}}
Document text:
"""
{{document_text}}
"""

Tasks:
{{items_json}}
