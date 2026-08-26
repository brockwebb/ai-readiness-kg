# Resume Phase 1 — Projection composite keying (task 2026-08-23_batched_repair_resume, Seldon a2d3fb42)

Defect (from the 2026-08-23 benchmark RESULT): 600 of 6,988 item ids recur across documents and the loader, keying on bare item id, FUSED them into single nodes — cross-document contamination of exactly the kind DD-020 forbids the loader to create.

**Fix:** every non-Document node keys on the composite `doc_id::item_id` (`node_key`); edge endpoints resolve document-scope (manifested doc ids and aliases onto them) vs item-scope (`resolve_endpoint`); dangling doc-like ids never manifested stay scoped to the asserting document. Overlay updates (`grounding_relocated`, `attribute_nulled`) address nodes by the same key. Cross-document identity is dedup's job, never the loader's (DD-020).

**Mutation test first** (`tests/test_build_projection_filters.py`): the old keying provably fuses (same key for two docs' same-id items); the fixed keying yields two distinct keys; endpoint resolution covers document-scope, alias, item-scope and dangling cases. 161 tests green.

**Rebuild before → after:** Concept nodes 3,537 → **4,675** (+1,138 un-fused; consistent with 600 recurring ids each fused across ≥2 docs). Grounding gate **0** (no STOP), drift 0; quarantine 0.0237 and empty 0.0075 unchanged (event-scoped); `edge_endpoint_validation` 1,209 unchanged (event-level check); `orphan_rate` — see gate table (splitting fused nodes changes the orphan denominator; the delta is a keying artefact, not new extraction).

**Monitor baselines:** unchanged and NOT re-versioned — the six monitors read event-derived per-document metrics (`build_metrics`, assertions), none of which the keying touches; the before/after pair recorded here is the required log. **Other consumers checked:** gates (event-level), monitors (event-level), probe/repair scripts (already keyed `(doc_id, item_id)`), SHACL export (already doc-scoped IRIs — the benchmark task's export anticipated this fix). No shims.
