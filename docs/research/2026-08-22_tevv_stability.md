# TEVV Phase 2 — Test-retest stability (task 2026-08-22_kernel_tevv)

Retest run 2026-08-22 13:03–13:45 UTC, serial, `scripts/tevv_retest.py`. Each document re-extracted under its ORIGINAL model (`claude-opus-4-8`), prompt-template version and schema version, read from its events (v1 docs → prompt 0.2.0 / schema 0.2 via `scripts/tevv_pins/`, sha-verified against git `69ebfdc`; kernel docs → 0.3.0 / 0.3, `10e3d07`). All retest events in `events/batch-008_tevv_retest.jsonl` (`purpose: tevv_retest`; excluded from replay, projection, gates, monitors); raw responses in `events/raw/tevv_retest/`; per-doc metrics and proposed_relationships in `tevv_retest/` subdirs (originals untouched).

## Rate
First doc alone: `census-…-f2` 31,884 chars → **381 s, 98,718 tokens**. Projected remaining seven ≈ 45–60 min; actual 8-doc total ≈ 42 min, **834,313 tokens**; cost UNKNOWN (unpriced by the control plane).

| doc | epoch | prompt / schema | chars | wall | tokens | result |
|---|---|---|---|---|---|---|
| `census-bureau-statistical-quality-standards-standard-f2-prov` | v1 | 0.2.0 / 0.2 | 31,884 | 381.2 s | 98,718 | 83n/105e/0q |
| `ai-data-readiness-checklist-digital-government-hub` | v1 | 0.2.0 / 0.2 | 1,560 | 255.8 s | 112,790 | 48n/66e/0q |
| `undp-artificial-intelligence-readiness-assessment-aira` | v1 | 0.2.0 / 0.2 | 17,542 | 104.9 s | 118,342 | 21n/37e/0q |
| `beyond-model-readiness-institutional-readiness-for-ai-deploy` | v1 | 0.2.0 / 0.2 | 45,027 | 454.1 s | 110,378 | 50n/71e/57q |
| `lighthouse-docs-overview` | kernel-v03 | 0.3.0 / 0.3 | 9,622 | 208.8 s | 65,335 | 37n/50e/0q |
| `dcat-us-3-dataset-schema` | kernel-v03 | 0.3.0 / 0.3 | 86,663 | 349.6 s | 138,893 | 68n/95e/0q |
| `jacobsen-2020-fair-principles-interpretations` | kernel-v03 | 0.3.0 / 0.3 | 65,886 | 406.7 s | 124,652 | 97n/102e/8q |
| `gsa-site-scanning-engine-readme` | kernel-v03 | 0.3.0 / 0.3 | 7,363 | 240.5 s | 65,205 | 28n/34e/0q |

Note `beyond-model-readiness` retest: 57 quarantined (orig 0) — the retest emitted edges to ids it never asserted (`unresolved endpoint`), the same per-run variance the kernel bulk showed.

## Metrics (pre-registered identity: type + NFKC-normalized primary text; edge = type + endpoint identities; spans NFKC/whitespace-normalized)

| doc | nodes orig/retest/both | κ nodes | PA nodes | edges orig/retest/both | κ edges | PA edges | span Jaccard |
|---|---|---|---|---|---|---|---|
| `census-bureau-statistical-quality-standards-standard-f2-prov` | 51/83/28 | -0.44 | 0.42 | 64/105/26 | -0.56 | 0.31 | 0.31 |
| `ai-data-readiness-checklist-digital-government-hub` | 48/48/38 | -0.21 | 0.79 | 64/66/36 | -0.45 | 0.55 | 0.29 |
| `undp-artificial-intelligence-readiness-assessment-aira` | 18/21/14 | -0.26 | 0.72 | 32/37/20 | -0.40 | 0.58 | 0.55 |
| `beyond-model-readiness-institutional-readiness-for-ai-deploy` | 44/50/24 | -0.48 | 0.51 | 67/71/22 | -0.68 | 0.32 | 0.07 |
| `lighthouse-docs-overview` | 38/37/12 | -0.68 | 0.32 | 53/50/12 | -0.77 | 0.23 | 0.29 |
| `dcat-us-3-dataset-schema` | 67/68/32 | -0.53 | 0.47 | 103/95/33 | -0.66 | 0.33 | 0.35 |
| `jacobsen-2020-fair-principles-interpretations` | 108/97/43 | -0.57 | 0.42 | 162/102/45 | -0.54 | 0.34 | 0.14 |
| `gsa-site-scanning-engine-readme` | 42/28/12 | -0.56 | 0.34 | 56/34/14 | -0.55 | 0.31 | 0.29 |

**Pooled:** κ all items **-0.590** (nodes -0.520, edges -0.639); positive agreement all items **0.409** (nodes 0.479, edges 0.358); mean span Jaccard **0.285**.

| node type | orig | retest | both | κ pooled | positive agreement |
|---|---|---|---|---|---|
| Claim | 63 | 60 | 17 | -0.72 | 0.28 |
| Concept | 219 | 250 | 121 | -0.47 | 0.52 |
| Definition | 42 | 29 | 17 | -0.43 | 0.48 |
| Framework | 12 | 9 | 5 | -0.47 | 0.48 |
| Instrument | 5 | 4 | 1 | -0.75 | 0.22 |
| Measure | 12 | 15 | 11 | -0.11 | 0.81 |
| Platform | 2 | 4 | 2 | 0.00 | 0.67 |
| Practice | 16 | 22 | 3 | -0.79 | 0.16 |
| Standard | 30 | 22 | 16 | -0.30 | 0.62 |
| Tool | 15 | 17 | 10 | -0.36 | 0.62 |

## Reading
1. **Every pre-registered stability gate fails** (κ ≥ 0.61 pooled and per type; Jaccard ≥ 0.70). Findings; thresholds unchanged.
2. **The κ values are an artefact of the statistic on this structure** — the kappa paradox (Cicchetti & Feinstein 1990; Feinstein & Cicchetti 1990): with the union as universe there is no both-absent cell, expected agreement is inflated, and κ is negative even where half the items match (Concept: 121 shared of 219/250 → PA 0.52, κ −0.47). Positive specific agreement (Dice) is the literature's remedy and is reported beside κ. A follow-on should replace κ with PA (or compute κ over a fixed candidate universe) by the pre-registration process — not in this task.
3. **The paradox-free number is still low.** PA 0.41 pooled: under exact normalized-text identity, fewer than half the items recur across two runs of the same model/prompt/document. Short, list-like sources are the most stable (checklist 0.79, UNDP 0.72); long prose and technical references are the least (Lighthouse 0.32, GSA README 0.34, Jacobsen 0.42). The model re-describes rather than re-names: "AI readiness assessment" vs "AI-readiness assessment framework" count as different Concepts. Part of the instability is therefore naming variance, not content variance — a canonicalized identity (token-set or embedding match) would raise PA; that is the concept-dedup task already queued, and it is exactly why dedup is on the critical path.
4. **Least stable types:** Practice (PA 0.16), Claim (0.28), Instrument (0.22), Framework (0.48). Most stable: Measure (0.81), Platform (0.67), Tool (0.63), Concept (0.52). Practices and Claims are free-text sentences, so exact-text identity is harshest on them; Measures and Tools have canonical names.
5. **Span Jaccard 0.28:** grounding spans are chosen freely per run; the same item is usually grounded in a different (valid) quote. Span identity is not a good stability measure for this protocol; item identity is.
6. Per Phase 5's rule (any per-type κ < 0.61), a per-type stability monitor is added with a mutation-test positive control.
