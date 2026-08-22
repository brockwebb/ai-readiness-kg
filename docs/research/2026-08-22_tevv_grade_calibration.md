# TEVV Phase 4 — evidence_grade calibration (task 2026-08-22_kernel_tevv)

Zero spend. `scripts/tevv_grade_calibration.py` → `corpus/staging/metrics/tevv_grade_calibration.json`. Population: **568 live kernel-v03 Claims** (all graded; 0 missing). Ground truth: `Document.is_platform_operator` (134 annotations, Phase 0) and `source_type`.

## platform_official vs is_platform_operator
| | is_platform_operator = true | false |
|---|---|---|
| graded platform_official | TP 177 | FP 36 |
| graded otherwise | FN 57 | TN 298 |

**Precision 0.831** (pre-registered gate ≥ 0.90 → **FAIL, finding**; Phase STOP floor 0.70 → not triggered, so the gate IS written). Recall 0.756 (not gated).

False positives by document: `sdmx-3-0-section-1-framework` 12, `w3c-rdf-data-cube` 10, `census-api-user-guide` 7, `spectral-readme` 3, `schema-org-webapi` 1, `schema-org-definedterm` 1, `schema-org-dataset` 1, `scrapy-docs-landing` 1. Reading: the model grades a *standards steward's* own documentation of its own standard (SDMX on SDMX, W3C on Data Cube, Census on its API, Stoplight on Spectral) as `platform_official`. DD-010 defines the grade as the **platform operator's** documentation of the platform's behaviour; these sources are official but not platforms. 29 of 36 FPs are that one confusion. The remaining 7 (schema.org ×3, Scrapy, Spectral) are the same shape (steward ≠ platform).

**Recommended follow-on (prompt, not threshold):** in `prompt_template.md` v0.3.1, define `platform_official` as "the operator of a *machine consumer* (search engine, crawler, CDN/bot control, LLM retrieval) documenting its own system's behaviour" and route steward-documenting-its-own-spec to `practitioner_assertion`/`measured_practitioner` per method disclosure, or add a `standard_official` grade by the schema's append-only process. Either is a separate task; thresholds stay.

## peer_reviewed_experiment vs source_type ∈ {academic}
| | academic | not academic |
|---|---|---|
| graded peer_reviewed_experiment | TP 32 | FP 0 |
| graded otherwise | FN 109 | TN 427 |

**Precision 1.000** (gate ≥ 0.90 → **PASS**). Recall 0.227: most Claims in academic papers are (correctly) graded `inference` or `practitioner_assertion` — a paper's discussion is not its experiment. Discrepancy: the task names `source_type in {academic, preprint}`; the schema enum has no `preprint` (arXiv papers are `academic`), so truth = `academic` only.

## Distribution of the other grades by document signal
{
 "platform_official": {
  "industry|po=True": 134,
  "federal|po=True": 15,
  "standard|po=False": 25,
  "standard|po=True": 28,
  "industry|po=False": 4,
  "federal|po=False": 7
 },
 "practitioner_assertion": {
  "industry|po=True": 14,
  "standard|po=False": 88,
  "federal|po=True": 18,
  "standard|po=True": 14,
  "industry|po=False": 30,
  "academic|po=False": 19,
  "federal|po=False": 10
 },
 "inference": {
  "standard|po=False": 17,
  "academic|po=False": 24,
  "industry|po=True": 3,
  "federal|po=True": 2,
  "federal|po=False": 3
 },
 "peer_reviewed_experiment": {
  "academic|po=False": 32
 },
 "measured_practitioner": {
  "standard|po=False": 7,
  "standard|po=True": 2,
  "industry|po=True": 4,
  "academic|po=False": 66,
  "federal|po=False": 2
 }
}
