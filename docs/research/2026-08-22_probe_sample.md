# Probe sample (task 2026-08-22_faithfulness_probe, Phase 1)

Seed `20260822`. Population 20,973 live grounded nodes+edges minus the 200 TEVV items (no overlap, so the samples pool). Strata = node type × epoch, edges by the TEVV families × epoch; proportional allocation, floor 15; strata with population < 15 merged into `other:<epoch>`: none. Windows: ±400 chars of normalized document text around the span (evidence for subject_dropped/fabrication adjudication, not the span). Span not found in document text for 1 items (window null).

| stratum | population | sampled |
|---|---|---|
| Claim:kernel-v03 | 518 | 15 |
| Claim:v1 | 920 | 18 |
| Concept:kernel-v03 | 1,870 | 30 |
| Concept:v1 | 2,817 | 29 |
| Definition:kernel-v03 | 418 | 15 |
| Definition:v1 | 478 | 15 |
| Framework:kernel-v03 | 47 | 15 |
| Framework:v1 | 198 | 15 |
| Instrument:kernel-v03 | 26 | 15 |
| Instrument:v1 | 124 | 15 |
| Measure:kernel-v03 | 166 | 15 |
| Measure:v1 | 352 | 15 |
| Platform:kernel-v03 | 88 | 15 |
| Practice:kernel-v03 | 326 | 15 |
| Standard:kernel-v03 | 274 | 15 |
| Standard:v1 | 146 | 15 |
| Tool:kernel-v03 | 90 | 15 |
| edge:document_structural:kernel-v03 | 4,197 | 30 |
| edge:document_structural:v1 | 5,044 | 30 |
| edge:semantic:kernel-v03 | 1,194 | 23 |
| edge:semantic:v1 | 1,680 | 30 |
