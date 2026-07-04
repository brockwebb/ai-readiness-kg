# Pilot proposed_relationships — Promotion Report (schema v0.2)

**Task:** cc_tasks/2026-07-03_schema_v02_promotion_rebaseline.md (Part 2)  
**Date:** 2026-07-03  
**Result:** 69 promoted to curated_promotion events (batch 3), 22 remain staged (of 91 total). No re-extraction — curated events only.

## Promoted by canonical edge

- `has_component`: 27
- `measures`: 25
- `uses_measure`: 11
- `subtype_of`: 4
- `precedes`: 2

## Remaining staged — by reason

- not in mapping (long-tail; stays staged): 17
- None/empty endpoint: 3
- illegal pair Framework->Concept for 'measures': 1
- grounding miss / no span: 1

## Remaining staged — by original proposed name

- `evaluates`: 3
- `extends`: 2
- `supports_standard`: 2
- `evolves_from`: 2
- `builds_on`: 1
- `exemplifies`: 1
- `administers`: 1
- `defined_in`: 1
- `participates_in`: 1
- `develops`: 1
- `assesses`: 1
- `uses_measure`: 1
- `based_on_framework`: 1
- `integrated_into`: 1
- `mapped_to`: 1
- `adapted_from_prior_metric`: 1
- `risk_to`: 1

## Promoted items (doc | original → canonical | pair | from → to)

- lawrence-data-readiness-levels-2017 | `has_component` → `has_component` | Framework->Concept | fw-drl → c-band-a
- lawrence-data-readiness-levels-2017 | `has_component` → `has_component` | Framework->Concept | fw-drl → c-band-b
- lawrence-data-readiness-levels-2017 | `has_component` → `has_component` | Framework->Concept | fw-drl → c-band-c
- lawrence-data-readiness-levels-2017 | `precedes` → `precedes` | Concept->Concept | c-band-c → c-band-b
- lawrence-data-readiness-levels-2017 | `precedes` → `precedes` | Concept->Concept | c-band-b → c-band-a
- lawrence-data-readiness-levels-2017 | `sub_level_of` → `has_component` | Concept->Concept | c-hearsay-data → c-band-c
- lawrence-data-readiness-levels-2017 | `sub_level_of` → `has_component` | Concept->Concept | c-level-c1 → c-band-c
- lawrence-data-readiness-levels-2017 | `sub_level_of` → `has_component` | Concept->Concept | c-level-b1 → c-band-b
- lawrence-data-readiness-levels-2017 | `sub_level_of` → `has_component` | Concept->Concept | c-level-a1 → c-band-a
- lawrence-data-readiness-levels-2017 | `part_of` → `has_component` | Concept->Concept | c-exploratory-data-analysis → c-band-b
- lawrence-data-readiness-levels-2017 | `part_of` → `has_component` | Concept->Concept | c-data-munging → c-band-c
- fcsm-25-03 | `operationalizes` → `measures` | Instrument->Concept | inst-baseline-assessment → co-ai-performance
- fcsm-25-03 | `measures` → `measures` | Measure->Concept | m-source-accuracy → co-ai-performance
- fcsm-25-03 | `measures` → `measures` | Measure->Concept | m-mcp-outcomes → co-integration-protocols
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-completeness
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-outlier-iqr
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-mm-risk
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-pearson
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-theils-u
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-representation-rate
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-statistical-rate
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-tsd
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-fair-score
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-imbalance-degree
- aidrin-hiniduma-2024 | `uses_measure` → `uses_measure` | Instrument->Measure | inst-aidrin → m-shapley
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-completeness → c-completeness
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-outlier-iqr → c-outliers
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-duplicate-score → c-duplication
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-mm-risk → c-reid-risk
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-pearson → c-feature-correlations
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-theils-u → c-feature-correlations
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-representation-rate → c-group-fairness
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-statistical-rate → c-group-fairness
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-tsd → c-fairness
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-fair-score → c-fair-compliance
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-imbalance-degree → c-class-imbalance
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-imbalance-ratio → c-class-imbalance
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-lrid → c-class-imbalance
- aidrin-hiniduma-2024 | `measures_concept` → `measures` | Measure->Concept | m-shapley → c-feature-importance
- aidrin-hiniduma-2024 | `decomposes` → `has_component` | Framework->Concept | fw-readiness-categories → c-data-readiness
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-governance
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-understandability
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-structural-quality
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-value
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-fairness
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-data-quality
- aidrin-hiniduma-2024 | `has_category` → `has_component` | Framework->Concept | fw-readiness-categories → c-model-specific
- cisco-ai-readiness-index-2025 | `operationalizes` → `measures` | Instrument->Concept | instr-cisco-ai-readiness-index → concept-ai-readiness
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-overall-readiness-score → concept-ai-readiness
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-strategy-pillar-score → concept-strategy-pillar
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-infrastructure-pillar-score → concept-infrastructure-pillar
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-data-pillar-score → concept-data-pillar
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-governance-pillar-score → concept-governance-pillar
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-talent-pillar-score → concept-talent-pillar
- cisco-ai-readiness-index-2025 | `measures` → `measures` | Measure->Concept | measure-culture-pillar-score → concept-culture-pillar
- cisco-ai-readiness-index-2025 | `categorizes` → `has_component` | Framework->Concept | framework-readiness-levels → concept-pacesetters
- cisco-ai-readiness-index-2025 | `categorizes` → `has_component` | Framework->Concept | framework-readiness-levels → concept-chasers
- cisco-ai-readiness-index-2025 | `categorizes` → `has_component` | Framework->Concept | framework-readiness-levels → concept-followers
- cisco-ai-readiness-index-2025 | `categorizes` → `has_component` | Framework->Concept | framework-readiness-levels → concept-laggards
- cisco-ai-readiness-index-2025 | `has_component` → `has_component` | Framework->Concept | framework-six-pillars → concept-strategy-pillar
- cisco-ai-readiness-index-2025 | `has_component` → `has_component` | Framework->Concept | framework-six-pillars → concept-infrastructure-pillar
- cisco-ai-readiness-index-2025 | `has_component` → `has_component` | Framework->Concept | framework-six-pillars → concept-data-pillar
- cisco-ai-readiness-index-2025 | `has_component` → `has_component` | Framework->Concept | framework-six-pillars → concept-governance-pillar
- cisco-ai-readiness-index-2025 | `has_component` → `has_component` | Framework->Concept | framework-six-pillars → concept-talent-pillar
- cisco-ai-readiness-index-2025 | `has_component` → `has_component` | Framework->Concept | framework-six-pillars → concept-culture-pillar
- cisco-ai-readiness-index-2025 | `subtype_of` → `subtype_of` | Concept->Concept | concept-autonomous-software-engineering → concept-agentic-ai
- cisco-ai-readiness-index-2025 | `subtype_of` → `subtype_of` | Concept->Concept | concept-productivity-agents → concept-agentic-ai
- cisco-ai-readiness-index-2025 | `subtype_of` → `subtype_of` | Concept->Concept | concept-industrial-robotics-agents → concept-agentic-ai
- cisco-ai-readiness-index-2025 | `subtype_of` → `subtype_of` | Concept->Concept | concept-simulated-humans-agents → concept-agentic-ai
