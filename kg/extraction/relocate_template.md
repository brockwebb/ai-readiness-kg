<!--
Versioned span-relocation prompt (task 2026-08-23_whole_graph_repair Phase 3; DD-017).
Cleanup-class model (DD-006). Rendering substitutes {{item_type}}, {{item_text}}, {{document_text}}.
relocate_version: 1.0.0
-->
# Find the minimal verbatim passage supporting an extracted item

Below is an extracted {{item_type}} and the text of the document it came from. Return the
**shortest contiguous passage, copied verbatim from the document**, that fully supports the
item text — every clause of it. Do not paraphrase, do not stitch fragments, do not add words.
If no single contiguous passage supports the whole item, answer NONE.

Output strict JSON only, no prose, no fence: {"passage": "<verbatim passage>"} or {"passage": "NONE"}

Item text:
{{item_text}}

Document text:
{{document_text}}
