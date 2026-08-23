# Probe decision (task 2026-08-22_faithfulness_probe, Phase 5) — pre-registered rule applied

Aggregation: crowd-kit DawidSkene(n_iter=100) over 1,870 fact-level labels on 935 atomic facts from 400 items; raters `claude-opus-4-8` (agreement with MAP 0.923) and `claude-sonnet-5` (0.985). Batch-vs-single κ = 0.915 (n=50) → batch size 10. Self-consistency (Opus, 94 facts re-judged in different batches): see RESULT. Full-document check applied to literal-attribute `fabrication` calls (judges saw a ±400-char window): 33 checked, 20 reclassified to `filled_attribute` (value present in the document).

## Class proportions, pooled (935 facts; Wilson 95%)
| class | n | share | CI |
|---|---|---|---|
| entailed | 401 | 0.429 | [0.398, 0.461] |
| span_truncated | 156 | 0.167 | [0.144, 0.192] |
| subject_dropped | 121 | 0.129 | [0.109, 0.152] |
| filled_attribute | 113 | 0.121 | [0.101, 0.143] |
| doc_level_attribute | 76 | 0.081 | [0.065, 0.101] |
| fabrication | 68 | 0.073 | [0.058, 0.091] |

Item roll-up (faithful iff every fact entailed or doc_level_attribute): **130/400 = 0.325**.

**F pooled = 0.0792 [0.0629, 0.0991]** over 859 facts (doc_level_attribute and grade_misassigned excluded).

## Per stratum and verdict
| stratum | facts | F denom | fabrication | F | Wilson 95% | verdict |
|---|---|---|---|---|---|---|
| Claim:kernel-v03 | 30 | 30 | 0 | 0.000 | [0.000, 0.114] | **repair_then_rejudge** |
| Claim:v1 | 31 | 31 | 0 | 0.000 | [0.000, 0.110] | **repair_then_rejudge** |
| Concept:kernel-v03 | 102 | 101 | 7 | 0.069 | [0.034, 0.136] | **repair_then_rejudge** |
| Concept:v1 | 98 | 97 | 4 | 0.041 | [0.016, 0.101] | **repair_then_rejudge** |
| Definition:kernel-v03 | 45 | 45 | 0 | 0.000 | [0.000, 0.079] | **repair_then_rejudge** |
| Definition:v1 | 44 | 44 | 0 | 0.000 | [0.000, 0.080] | **repair_then_rejudge** |
| Framework:kernel-v03 | 40 | 26 | 1 | 0.038 | [0.007, 0.189] | **repair_then_rejudge** |
| Framework:v1 | 44 | 32 | 1 | 0.031 | [0.006, 0.157] | **repair_then_rejudge** |
| Instrument:kernel-v03 | 77 | 67 | 17 | 0.254 | [0.165, 0.369] | **reextract_required** |
| Instrument:v1 | 76 | 70 | 12 | 0.171 | [0.101, 0.276] | **reextract_required** |
| Measure:kernel-v03 | 38 | 35 | 2 | 0.057 | [0.016, 0.186] | **repair_then_rejudge** |
| Measure:v1 | 39 | 39 | 6 | 0.154 | [0.072, 0.297] | **repair_then_rejudge** |
| Platform:kernel-v03 | 28 | 18 | 0 | 0.000 | [0.000, 0.176] | **repair_then_rejudge** |
| Practice:kernel-v03 | 25 | 25 | 1 | 0.040 | [0.007, 0.195] | **repair_then_rejudge** |
| Standard:kernel-v03 | 37 | 36 | 0 | 0.000 | [0.000, 0.096] | **repair_then_rejudge** |
| Standard:v1 | 33 | 29 | 2 | 0.069 | [0.019, 0.220] | **repair_then_rejudge** |
| Tool:kernel-v03 | 35 | 31 | 0 | 0.000 | [0.000, 0.110] | **repair_then_rejudge** |
| edge:document_structural:kernel-v03 | 30 | 23 | 3 | 0.130 | [0.045, 0.321] | **repair_then_rejudge** |
| edge:document_structural:v1 | 30 | 28 | 0 | 0.000 | [0.000, 0.121] | **repair_then_rejudge** |
| edge:semantic:kernel-v03 | 23 | 23 | 6 | 0.261 | [0.125, 0.465] | **reextract_required** |
| edge:semantic:v1 | 30 | 29 | 6 | 0.207 | [0.098, 0.384] | **repair_then_rejudge** |

**Overall: repair_path for other strata; reextract_required strata flagged.** No stratum reaches F_upper < 0.05, so none takes the repair-only branch; three strata have F_lower > 0.10 and are flagged `reextract_required`; all others proceed to repair with a post-repair re-judge (follow-on) deciding.

## `reextract_required` strata — corrected-prompt requirements (re-extraction is a separate task)
- **Instrument (v1 and kernel-v03):** fabrication concentrates in `method` (25 of 29) — the extractor describes how an instrument works from world knowledge ("fielded every 2 years", "household health survey", "uses SPARQL ASK queries") when the document only names it. Requirements: `method` (and `owner`, `year`) MUST be null unless a grounding span covers the value — per-attribute spans for Instrument; forbid completion from background knowledge explicitly; an Instrument that is merely *cited* by the document is a `mentions`-only Concept/Standard, not an Instrument node with attributes.
- **edge:semantic (kernel-v03):** `has_component` / `subtype_of` / `consumes` edges asserted from page structure (a schema.org "Properties from SoftwareApplication" heading, a "we are exploring experimental support" sentence) rather than from a sentence stating the relation. Requirements: a semantic edge's span must contain both endpoints' names (or unambiguous referents) and the relation predicate; heading- or list-structure inference is `proposed_relationships`, not an edge.

## Limits recorded
- Fabrication for free-text propositions is window-based (±400 chars); the document-level check is mechanical only for literal attributes (33 facts). Some `fabrication` on Instrument `method` may be document-supported elsewhere; the re-judge after repair (and the human hard-item set) is where that gets resolved. Thresholds and the rule are unchanged.
- The TEVV sidecar rater contributed **0** labels: the probe sample excludes the 200 TEVV items by design, so the 40 sidecar items have no facts here (reported as a discrepancy).
