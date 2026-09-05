# ADDENDUM-02 to `2026-09-04_extract_g1eval_17_and_rerun.md`

**Date:** 2026-09-04
**Authored by:** Desktop session
**Status:** AMENDS ADDENDUM-01. Adds one zero-spend step after §3 (CQ rerun), before §4.
**Immutable once written.**

---

## §3a. Term-in-context harvest from the 23 unextracted documents (zero model spend)

From `state/extraction_gap_2026-09-04.json`, take the 23 documents that matched CQ-02's terms (`ai ready`, `ai-ready`, plus `ai readiness`). Using the converted markdown substrate where it exists and pypdf otherwise (as the gap diagnostic did), extract every sentence containing any of those terms, with document id and page/section locator. Write `assessment/results/ai_ready_term_contexts_2026-09-04.jsonl` and register it as a DataFile (`snapshot: true`).

Then classify each sentence into exactly one sense, by reading, and record the sentence ids per class:
- `adoption` — readiness of an organization, person, sector, or nation to adopt or use AI
- `training_data` — data prepared as input to model training (cleaning, labelling, sharding, feature engineering)
- `data_product_consumption` — a published data product's fitness to be discovered and correctly processed by an AI system at inference time (the framework's sense)
- `other` — anything else, with a one-line reason

Register the counts as Results `cq_02_unextracted_sense_<class>` (Script = the harvest script, DataFile = the JSONL). Report the table and, for every `data_product_consumption` hit, the sentence verbatim and its source.

Do not extract any of the 23. If `data_product_consumption` > 0, list the documents; the decision to extract them is Desktop's and will be a separate task with its own ceiling computed from the measured rate.
