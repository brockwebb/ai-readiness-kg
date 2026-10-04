# ADDENDUM-01 to `2026-10-02_commerce_guidance_admission.md`: same document, two pipelines, one descriptive comparison

**Date:** 2026-10-02 **Status:** AMENDS the base task. Does not supersede it. Read before any step.
**Origin:** the operator's observation of 2026-10-02 that one document extracted by two pipelines is an interesting state-fidelity-validity case. Estimated spend unchanged in order of magnitude; no extra model call except the reader gate.

## Added decisions

9. **Why re-extraction is not optional, one sentence in the RESULT.** The FSS nodes carry another schema and another harness's provenance, so they cannot enter this event log; the document is extracted here under the pinned model, prompt epoch and schema, and both graphs then hold the same text.

10. **Fix the comparison BEFORE querying either graph, and write it into the RESULT's first section.** Ground truth is the document's own glossary appendix: the count N of defined terms it lists (taken from the extracted text of `doc_genai_open_data_2025`, by script, with the term list written to `docs/research/2026-10-02_commerce_guidance_glossary_terms.csv`). Metric, per graph: the number of those N terms that have a Definition node, with the glossary entry as the grounding span (this graph) or with `source_doc = doc_genai_open_data_2025` and verbatim text matching the glossary entry after NFKC and whitespace folding (the FSS graph). Also report, for this graph, how many glossary spans were quarantined at parse and why. No threshold, no pass line, no winner: the two graphs have different schemas, models and prompts, so the difference is a description of two pipelines and is never attributed to one cause.

11. **Reuse the repository's own cross-system method.** `cc_tasks/2026-09-*_trustgraph_benchmark_v2*` (Results `6cc5680a`, `f425fcce`) already compared another extractor on coverage and fabrication share. Read it, use its matching rule where it applies, and say where it does not; do not invent a second matching rule. Search prior art on evaluating extraction against a gold glossary or gold span set (corpus first, then the web) and cite what is found.

12. **Scope the claim.** One document, one pass each. The RESULT states in one sentence that this is an illustration of divergence between pipelines on one document and not an estimate of either pipeline's fidelity, and says what sample would be needed for an estimate. Do not use the phrase "state fidelity validity" as a conclusion; name only the observation (a glossary entry present as text in one graph and as a Definition in the other, or absent from the Definition layer in both).

13. **Write set additions:** `docs/research/2026-10-02_commerce_guidance_glossary_terms.csv`, `docs/research/2026-10-02_commerce_guidance_two_pipelines.md` (the table of N terms by graph, the divergent terms listed with both graphs' ids, the method and its limits). The reader gate (base decision 8) also reads this file.
