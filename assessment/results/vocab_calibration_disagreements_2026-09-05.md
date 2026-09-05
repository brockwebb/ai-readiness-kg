# Vocabulary linking — rater disagreements, opus vs fable

**Task:** `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §2.2. **Rubric:** v1.3.0. **n compared:** 100. **Cohen's kappa:** 0.979214 (gate 0.6, PASS). **Disagreements:** 1.

Informational. These are records for the operator, not a queue of approvals: the kappa gate above is what decides whether the band's links are written.


## `W3C Data Catalog Vocabulary Version 3` (Standard) -> `Data Catalog Vocabulary (DCAT)`

- **opus:** different (0.72) — The node's span "of the W3C Data Catalog Vocabulary Version 3, known as the DCAT-US 3.0." denotes a specific version/profile instance (DCAT-US 3.0), whereas the term's note "equivalent structures represented in [W3C](https://www.w3.org/)'s [Data Catalog Vocabulary (DCAT) format](https://www.w3.org/TR/vocab-dcat/)" denotes the version-agnostic DCAT vocabulary, making the node a narrower species rather than the term itself.
- **fable:** same (0.9) — The node span "of the W3C Data Catalog Vocabulary Version 3, known as the DCAT-US 3.0." names the W3C DCAT standard (its version 3 revision, which the document then profiles as DCAT-US), and the term's scope note "equivalent structures represented in [W3C](https://www.w3.org/)'s [Data Catalog Vocabulary (DCAT) format](https://www.w3.org/TR/vocab-dcat/)" covers that same W3C standard; a version is an edition of the standard, not a distinct species of it, so both denote the W3C DCAT vocabulary.
- document `m-25-05-phase-2-implementation-of-the-evidence-act-open-gove`, node `m-25-05-phase-2-implementation-of-the-evidence-act-open-gove::s_dcat_w3c`, term `air:standard/data-catalog-vocabulary-dcat`
