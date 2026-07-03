# Pilot Extraction — Audit Summary (schema §9 inputs)

**Task:** cc_tasks/2026-07-03_pilot_extraction_run_v5.md  
**Model:** claude-fable-5 (subscription OAuth via `claude -p`; no API key)  
**Date:** 2026-07-03  
**Outcome:** 5/5 documents extracted → validated. No STOP, no model substitution, no gate breach. Facts only; no schema-patch recommendations (operator's audit).

Events in the sharded log (`events/batch-002.jsonl`): 357 node_asserted, 519 edge_asserted, 5 build_metrics, 5 model_call, 10 doc_state (extracted→validated ×5). Every extracted item carries §4 provenance (model_id from the response envelope, schema_version, extraction_event_id, timestamp). Acquired PDFs stay gitignored; only short verbatim grounding spans (required for provenance) appear below.

## Per-document metrics

| # | doc_id | est.tok | concepts | conc/1k | defs | claims | nodes | edges | quar | quar% | prop_rel | cost |
|---|--------|--------:|---------:|--------:|-----:|-------:|------:|------:|-----:|------:|---------:|-----:|
| 1 | lawrence-data-readiness-levels-2017 | 8520 | 30 | 3.5211 | 11 | 20 | 64 | 101 | 0 | 0.0 | 11 | $2.46 |
| 2 | fcsm-25-03 | 2577 | 28 | 10.8653 | 3 | 18 | 57 | 87 | 0 | 0.0 | 8 | $2.16 |
| 3 | datahub-mlmu-25 | 2853 | 32 | 11.2163 | 1 | 14 | 53 | 77 | 0 | 0.0 | 7 | $2.08 |
| 4 | aidrin-hiniduma-2024 | 16891 | 41 | 2.4273 | 9 | 16 | 94 | 132 | 7 | 3.0 | 40 | $3.98 |
| 5 | cisco-ai-readiness-index-2025 | 9748 | 36 | 3.6931 | 11 | 31 | 89 | 122 | 0 | 0.0 | 25 | $3.52 |
| — | **TOTAL** | — | **167** | — | **35** | **99** | **357** | **519** | **7** | — | **91** | **$14.51** |

**Gates:** quarantine-rate STOP threshold 10% — max observed 3.0% (AIDRIN); no STOP. Concept-density flag < 2.0/1k — none flagged (min 2.43, AIDRIN). No thin layer.

## Quarantine specimens (7 total)


**aidrin-hiniduma-2024** (7):
- [claims] grounding_span not found in source text
  - span: "Despite the availability of various tools and frameworks that tackle different pieces of the AI readiness evaluation, no single system evaluates all the aspects using quantitative metrics and visualizations."
- [claims] grounding_span not found in source text
  - span: "Notably, for the evaluation of privacy alone, the MIDRC datasets required around 106.36 seconds for result generation on one attribute (‘sex’)."
- [edge] unresolved endpoint id (missing or quarantined node)
  - span: "Despite the availability of various tools and frameworks that tackle different pieces of the AI readiness evaluation, no single system evaluates all the aspects using quantitative metrics and visualizations."
- [edge] unresolved endpoint id (missing or quarantined node)
  - span: "Notably, for the evaluation of privacy alone, the MIDRC datasets required around 106.36 seconds for result generation on one attribute (‘sex’)."
- [edge] unresolved endpoint id (missing or quarantined node)
  - span: "Despite the availability of various tools and frameworks that tackle different pieces of the AI readiness evaluation, no single system evaluates all the aspects using quantitative metrics and visualizations."
- [edge] unresolved endpoint id (missing or quarantined node)
  - span: "Notably, for the evaluation of privacy alone, the MIDRC datasets required around 106.36 seconds for result generation on one attribute (‘sex’)."
- [cites] grounding_span not found in source text
  - span: "Another metric, the Imbalance Degree (ID), proposed by Ortigosa-Hernández et al. [40], extends the measurement of class imbalance by considering specific characteristics of the class distribution."

## proposed_relationships — full inventory (91 total)

Source: {'model': 91} (all model-supplied — the model routed unexpressible relationships to this block rather than forcing illegal edges; zero auto-routed unknown/invalid-pair edges, so the edge whitelist held).

Suggested edge-name frequency (candidate schema-expressiveness signal):

- `measures_concept` ×14
- `uses_measure` ×12
- `has_component` ×9
- `measures` ×9
- `has_category` ×7
- `sub_level_of` ×4
- `categorizes` ×4
- `subtype_of` ×4
- `evaluates` ×3
- `precedes` ×2
- `part_of` ×2
- `extends` ×2
- `operationalizes` ×2
- `supports_standard` ×2
- `evolves_from` ×2
- `builds_on` ×1
- `exemplifies` ×1
- `administers` ×1
- `defined_in` ×1
- `participates_in` ×1
- `develops` ×1
- `assesses` ×1
- `based_on_framework` ×1
- `integrated_into` ×1
- `mapped_to` ×1
- `adapted_from_prior_metric` ×1
- `decomposes` ×1
- `risk_to` ×1

Full list (doc | suggested_edge | from → to | grounding span):

- lawrence-data-readiness-levels-2017 | `has_component` | fw-drl → c-band-a | "The initial proposal is that data readiness should be split into three bands. Each band being represented by a letter, A, B and C." | note: The framework comprises the three bands; no Framework→Concept composition edge exists in the schema.
- lawrence-data-readiness-levels-2017 | `has_component` | fw-drl → c-band-b | "The initial proposal is that data readiness should be split into three bands. Each band being represented by a letter, A, B and C." | note: The framework comprises the three bands; no Framework→Concept composition edge exists in the schema.
- lawrence-data-readiness-levels-2017 | `has_component` | fw-drl → c-band-c | "The initial proposal is that data readiness should be split into three bands. Each band being represented by a letter, A, B and C." | note: The framework comprises the three bands; no Framework→Concept composition edge exists in the schema.
- lawrence-data-readiness-levels-2017 | `precedes` | c-band-c → c-band-b | "These bands reflect stages of data readiness which would each likely have some sub-levels, so the best data would be A1 and the worst data might be C4." | note: Bands form an ordered progression from C (worst) through B to A (best); the schema has no ordering edge between Concepts.
- lawrence-data-readiness-levels-2017 | `precedes` | c-band-b → c-band-a | "Thirdly, awareness of the transition from Band B to Band A (data moving to its context) would have made us realize that the question may well evolve and be more responsive to that outcome." | note: Explicit transition from Band B to Band A; no ordering edge between Concepts in the schema.
- lawrence-data-readiness-levels-2017 | `sub_level_of` | c-hearsay-data → c-band-c | "The lowest sub-level of Band C (let’s label it as C4) would represent a belief that the data may exist, but its existence isn’t even verified." | note: C4/hearsay data is the lowest sub-level of Band C; no Concept→Concept containment edge in the schema.
- lawrence-data-readiness-levels-2017 | `sub_level_of` | c-level-c1 → c-band-c | "For data to arrive at C1, then it would have all these considerations dealt with." | note: C1 is the top sub-level of Band C; no Concept→Concept containment edge in the schema.
- lawrence-data-readiness-levels-2017 | `sub_level_of` | c-level-b1 → c-band-b | "By the end of Band B, when data is B1, a broad idea of limitations in the data should be present in the expert’s mind." | note: B1 is the top sub-level of Band B; no Concept→Concept containment edge in the schema.
- lawrence-data-readiness-levels-2017 | `sub_level_of` | c-level-a1 → c-band-a | "Once data has been considered alongside a task and any remedial steps have been taken, then the data is in A1 condition." | note: A1 is the top sub-level of Band A; no Concept→Concept containment edge in the schema.
- lawrence-data-readiness-levels-2017 | `part_of` | c-exploratory-data-analysis → c-band-b | "Tukey’s approach of “Exploratory Data Analysis” also fits within Band B." | note: EDA is situated within Band B; no Concept→Concept part-of edge in the schema.
- lawrence-data-readiness-levels-2017 | `part_of` | c-data-munging → c-band-c | "Some parts of Band C are sometimes referred to as “data munging” or “data wrangling”, but those aren’t the only components of this band" | note: Data munging/wrangling constitutes part of Band C; no Concept→Concept part-of edge in the schema.
- fcsm-25-03 | `extends` | fcsm-25-03 → fw-fcsm-dq | "AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality"
- fcsm-25-03 | `builds_on` | co-ai-ready-data → co-open-data-principles | "Creating AI-ready data builds on established open-data principles."
- fcsm-25-03 | `extends` | co-machine-understandable → co-machine-readable | "Today’s AI era demands federal agencies go further – from machine-readable to machine-understandable data."
- fcsm-25-03 | `operationalizes` | inst-baseline-assessment → co-ai-performance | "This provides a baseline of AI performance with the status quo."
- fcsm-25-03 | `measures` | m-source-accuracy → co-ai-performance | "perform test queries on a range of AI chatbots (e.g., asking for recent unemployment rates, population statistics, etc.) and observe the sources and accuracy of responses"
- fcsm-25-03 | `measures` | m-mcp-outcomes → co-integration-protocols | "measure whether this leads to more relevant and accurate answers or reduced developer time"
- fcsm-25-03 | `evaluates` | fw-fcsm-dq → co-variable-level-metadata | "The FCSM framework provides three domains to evaluate these metadata improvements: Utility, Objectivity, and Integrity."
- fcsm-25-03 | `exemplifies` | fw-commerce-ai-ready → co-ai-ready-data | "The Department of Commerce’s recent “AI-ready data” initiative exemplifies this approach."
- datahub-mlmu-25 | `evaluates` | None → None | "An AI-readiness evaluation that measures how effectively an LLM interacts with Commerce statistical data assets" | note: Instrument→Concept evaluation target; operationalizes/measures require a Construct, which extraction cannot emit.
- datahub-mlmu-25 | `evaluates` | None → None | "The evaluation should also assess how well federal statistical data assets are structured to support effective LLM interaction" | note: The evaluation has a second target: the structural AI-readiness of the data assets themselves.
- datahub-mlmu-25 | `administers` | None → None | "prototype an open-source and publicly accessible tool that can automate and apply the AI-readiness evaluation" | note: Instrument→Instrument: the tool automates and applies the evaluation; no allowed edge type covers this.
- datahub-mlmu-25 | `defined_in` | None → None | "Open government data assets are defined in statute (44 USC 3502(20)) and in M-25-05." | note: Concept whose authoritative definition lives in external documents (also M-25-05); the definition text itself is not quoted in this document, so no Definition node could be emitted.
- datahub-mlmu-25 | `participates_in` | None → None | "The Bureau of Economic Analysis, the Census Bureau, the National Center for Science and Engineering Statistics, and other federal statistical agencies have played a major role in this project." | note: Schema has no Organization or Project node types.
- datahub-mlmu-25 | `develops` | None → None | "aims to assess and improve the AI compatibility of federal statistical data by developing AI-readiness criteria and prototyping tools" | note: Project→Concept; schema has no Project node type.
- datahub-mlmu-25 | `assesses` | None → None | "They are also assessing the use of emerging standards like the Model Context Protocol to increase system interoperability." | note: Organization→Standard; schema has no Organization node type.
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-completeness | "AIDRIN quantifies this by measuring the proportion of missing values within each feature of the dataset."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-outlier-iqr | "Hence, AIDRIN uses IQR to assess the proportion of outliers in each feature of the dataset."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-duplicate-score | "AIDRIN uses this method to examine the number of identical items present in datasets."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-mm-risk | "AIDRIN uses this approach for assessing and managing re-identification risks, emphasizing a more detailed analysis of dataset information to improve privacy protection."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-pearson | "AIDRIN utilizes the Pearson correlation coefficient to gauge the strength and direction of numerical feature correlations."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-theils-u | "On the other hand, for the assessment of categorical feature correlations, AIDRIN uses Theil’s U."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-representation-rate | "In the context of AIDRIN, the representation rate and statistical rate emerge as effective metrics for measuring group fairness."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-statistical-rate | "In the context of AIDRIN, the representation rate and statistical rate emerge as effective metrics for measuring group fairness."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-tsd | "To tackle this limitation, we introduce the Target Standard Deviation (TSD) metric."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-fair-score | "The function calculates a FAIR compliance score by assessing the fulfillment of checks against the total possible checks, presenting the results in a pie chart as illustrated in the pie chart in Figure 6."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-imbalance-degree | "AIDRIN uses the ID as the chosen metric to measure class imbalance."
- aidrin-hiniduma-2024 | `uses_measure` | inst-aidrin → m-shapley | "AIDRIN uses Shapley values [33] as a method to measure feature importance"
- aidrin-hiniduma-2024 | `measures_concept` | m-completeness → c-completeness | "In this study, we use the completeness metric proposed by Blake et al. [9] to assess this dimension of readiness."
- aidrin-hiniduma-2024 | `measures_concept` | m-outlier-iqr → c-outliers | "Hence, AIDRIN uses IQR to assess the proportion of outliers in each feature of the dataset."
- aidrin-hiniduma-2024 | `measures_concept` | m-duplicate-score → c-duplication | "By comparing the number of unique items to the total number of items, it generates a single score indicating the level of duplication throughout the dataset."
- aidrin-hiniduma-2024 | `measures_concept` | m-mm-risk → c-reid-risk | "The authors propose the “MM risk score”, which uses the Markov model to quantify re-identification risks."
- aidrin-hiniduma-2024 | `measures_concept` | m-pearson → c-feature-correlations | "AIDRIN utilizes the Pearson correlation coefficient to gauge the strength and direction of numerical feature correlations."
- aidrin-hiniduma-2024 | `measures_concept` | m-theils-u → c-feature-correlations | "On the other hand, for the assessment of categorical feature correlations, AIDRIN uses Theil’s U."
- aidrin-hiniduma-2024 | `measures_concept` | m-representation-rate → c-group-fairness | "The representation rate assesses the distributions of different sensitive attributes in the dataset."
- aidrin-hiniduma-2024 | `measures_concept` | m-statistical-rate → c-group-fairness | "The statistical rate, on the other hand, evaluates fairness through conditional probabilities, ensuring that the target representations do not discriminate certain groups based on sensitive attributes."
- aidrin-hiniduma-2024 | `measures_concept` | m-tsd → c-fairness | "This metric goes beyond binary groups by considering the average differences across all possible subgroups for a given target."
- aidrin-hiniduma-2024 | `measures_concept` | m-fair-score → c-fair-compliance | "The overall FAIR compliance score is presented as a percentage, reflecting the proportion of fulfilled checks out of the total possible checks."
- aidrin-hiniduma-2024 | `measures_concept` | m-imbalance-degree → c-class-imbalance | "AIDRIN uses the ID as the chosen metric to measure class imbalance."
- aidrin-hiniduma-2024 | `measures_concept` | m-imbalance-ratio → c-class-imbalance | "This metric provides a numerical representation of the disparity between the majority class instances and minority class instances in a dataset."
- aidrin-hiniduma-2024 | `measures_concept` | m-lrid → c-class-imbalance | "It uses the likelihood ratio (LR) test, offering a fine measurement of imbalance by comparing the existing class distribution to a balanced distribution."
- aidrin-hiniduma-2024 | `measures_concept` | m-shapley → c-feature-importance | "Shapley values provide a means to quantify the impact of each feature on a model’s predictions."
- aidrin-hiniduma-2024 | `based_on_framework` | inst-aidrin → fw-readiness-categories | "Based on the definition of AI readiness of data described above, we designed AIDRIN as a comprehensive framework to provide data assessment metrics."
- aidrin-hiniduma-2024 | `supports_standard` | inst-aidrin → std-dcat | "AIDRIN currently supports the assessment of FAIR compliance of metadata using two metadata standards: DCAT [3] and Datacite [2]."
- aidrin-hiniduma-2024 | `supports_standard` | inst-aidrin → std-datacite | "Similarly, AIDRIN supports corresponding FAIR elements in the DataCite standard."
- aidrin-hiniduma-2024 | `integrated_into` | inst-aidrin → fw-appfl | "We have successfully integrated data readiness assessment into the APPFL framework, which is available publicly [44]."
- aidrin-hiniduma-2024 | `mapped_to` | std-dcat → c-fair-compliance | "In Table 2, we show the DCAT elements divided into each subcategory under the FAIR principles [23]."
- aidrin-hiniduma-2024 | `adapted_from_prior_metric` | m-tsd → c-group-fairness | "Poulain et al. [42] introduced this concept, where their metric evaluates algorithmic fairness across different sensitive groups by computing the standard deviation of the groups’ true positive rates."
- aidrin-hiniduma-2024 | `decomposes` | fw-readiness-categories → c-data-readiness | "In our effort to design a comprehensive framework and metrics for AI readiness, we propose seven categories of evaluation and several metrics in each category."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-governance | "Given below are the categories of data readiness for AI."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-understandability | "Given below are the categories of data readiness for AI."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-structural-quality | "Given below are the categories of data readiness for AI."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-value | "Given below are the categories of data readiness for AI."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-fairness | "Given below are the categories of data readiness for AI."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-data-quality | "Given below are the categories of data readiness for AI."
- aidrin-hiniduma-2024 | `has_category` | fw-readiness-categories → c-model-specific | "Given below are the categories of data readiness for AI."
- cisco-ai-readiness-index-2025 | `operationalizes` | instr-cisco-ai-readiness-index → concept-ai-readiness | "The Cisco AI Readiness Index assesses organizations against six pillars of readiness—Strategy, Infrastructure, Data, Governance, Talent, and Culture—measured across 49 indicators."
- cisco-ai-readiness-index-2025 | `measures` | measure-overall-readiness-score → concept-ai-readiness | "Pillar scores were then combined to calculate an overall AI readiness score for each organization."
- cisco-ai-readiness-index-2025 | `measures` | measure-strategy-pillar-score → concept-strategy-pillar | "The pillar weightings are as follows: Strategy (15%); Infrastructure (25%); Data (20%); Governance (15%); Talent (15%); and Culture (10%)."
- cisco-ai-readiness-index-2025 | `measures` | measure-infrastructure-pillar-score → concept-infrastructure-pillar | "The pillar weightings are as follows: Strategy (15%); Infrastructure (25%); Data (20%); Governance (15%); Talent (15%); and Culture (10%)."
- cisco-ai-readiness-index-2025 | `measures` | measure-data-pillar-score → concept-data-pillar | "The pillar weightings are as follows: Strategy (15%); Infrastructure (25%); Data (20%); Governance (15%); Talent (15%); and Culture (10%)."
- cisco-ai-readiness-index-2025 | `measures` | measure-governance-pillar-score → concept-governance-pillar | "The pillar weightings are as follows: Strategy (15%); Infrastructure (25%); Data (20%); Governance (15%); Talent (15%); and Culture (10%)."
- cisco-ai-readiness-index-2025 | `measures` | measure-talent-pillar-score → concept-talent-pillar | "The pillar weightings are as follows: Strategy (15%); Infrastructure (25%); Data (20%); Governance (15%); Talent (15%); and Culture (10%)."
- cisco-ai-readiness-index-2025 | `measures` | measure-culture-pillar-score → concept-culture-pillar | "The pillar weightings are as follows: Strategy (15%); Infrastructure (25%); Data (20%); Governance (15%); Talent (15%); and Culture (10%)."
- cisco-ai-readiness-index-2025 | `evolves_from` | concept-ai-infrastructure-debt → concept-technical-debt | "The report also introduces a new concept — AI Infrastructure Debt — the modern evolution of technical and digital debt that held back prior transformation efforts."
- cisco-ai-readiness-index-2025 | `evolves_from` | concept-ai-infrastructure-debt → concept-digital-debt | "The report also introduces a new concept — AI Infrastructure Debt — the modern evolution of technical and digital debt that held back prior transformation efforts."
- cisco-ai-readiness-index-2025 | `risk_to` | concept-ai-infrastructure-debt → concept-ai-value | "AI Infrastructure Debt is a real risk to value"
- cisco-ai-readiness-index-2025 | `categorizes` | framework-readiness-levels → concept-pacesetters | "Based on their readiness scores, organizations are categorized into four levels:"
- cisco-ai-readiness-index-2025 | `categorizes` | framework-readiness-levels → concept-chasers | "Based on their readiness scores, organizations are categorized into four levels:"
- cisco-ai-readiness-index-2025 | `categorizes` | framework-readiness-levels → concept-followers | "Based on their readiness scores, organizations are categorized into four levels:"
- cisco-ai-readiness-index-2025 | `categorizes` | framework-readiness-levels → concept-laggards | "Based on their readiness scores, organizations are categorized into four levels:"
- cisco-ai-readiness-index-2025 | `has_component` | framework-six-pillars → concept-strategy-pillar | "The Index measures AI readiness of companies across six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture."
- cisco-ai-readiness-index-2025 | `has_component` | framework-six-pillars → concept-infrastructure-pillar | "The Index measures AI readiness of companies across six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture."
- cisco-ai-readiness-index-2025 | `has_component` | framework-six-pillars → concept-data-pillar | "The Index measures AI readiness of companies across six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture."
- cisco-ai-readiness-index-2025 | `has_component` | framework-six-pillars → concept-governance-pillar | "The Index measures AI readiness of companies across six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture."
- cisco-ai-readiness-index-2025 | `has_component` | framework-six-pillars → concept-talent-pillar | "The Index measures AI readiness of companies across six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture."
- cisco-ai-readiness-index-2025 | `has_component` | framework-six-pillars → concept-culture-pillar | "The Index measures AI readiness of companies across six pillars: Strategy, Infrastructure, Data, Governance, Talent, and Culture."
- cisco-ai-readiness-index-2025 | `subtype_of` | concept-autonomous-software-engineering → concept-agentic-ai | "Top Agentic AI use cases"
- cisco-ai-readiness-index-2025 | `subtype_of` | concept-productivity-agents → concept-agentic-ai | "Top Agentic AI use cases"
- cisco-ai-readiness-index-2025 | `subtype_of` | concept-industrial-robotics-agents → concept-agentic-ai | "Top Agentic AI use cases"
- cisco-ai-readiness-index-2025 | `subtype_of` | concept-simulated-humans-agents → concept-agentic-ai | "Top Agentic AI use cases"

## Protocol friction (observed facts)

- **AIDRIN's 7 quarantines (3.0%) = 3 root grounding misses + 4 cascade.** Two `claims` and one `cites` span were lightly paraphrased by the model, so they did not string-match the source verbatim (whitespace/OCR tolerance does not cover a reword). Four edges were then quarantined as `unresolved endpoint id` because they referenced the two quarantined claim nodes. The other four documents had zero quarantines.
- **All 91 proposed_relationships are model-supplied**, none auto-routed — the model did not emit unknown edge types or illegal endpoint pairs that the parser had to reject. The most frequent proposed names cluster around Instrument/Measure/Construct wiring and cross-framework relations (see frequency list).
- **The model does not emit `document_id`** (harness-owned; injected by the pipeline per the v3 provenance-ownership contract). No harness-owned field leaked into an event.
- **Concept density is high on short federal docs** (FCSM 10.9/1k, MLMU 11.2/1k) and lower on the long AIDRIN paper (2.4/1k) — expected; density is per estimated token.

## Per-call usage & spend accounting

| doc_id | input_tok | output_tok | cache_read | cache_create | dur_s | cost |
|--------|----------:|-----------:|-----------:|-------------:|------:|-----:|
| lawrence-data-readiness-levels-2017 | 11636 | 35353 | 18392 | 27694 | 321 | $2.46 |
| fcsm-25-03 | 11486 | 33862 | 15077 | 17076 | 304 | $2.16 |
| datahub-mlmu-25 | 11486 | 33359 | 18401 | 13958 | 314 | $2.08 |
| aidrin-hiniduma-2024 | 11486 | 54509 | 18401 | 55961 | 468 | $3.98 |
| cisco-ai-readiness-index-2025 | 11486 | 53984 | 18401 | 34367 | 472 | $3.52 |

- Preflight (identity smoke): ~$0.31.  v5 run total (preflight + 5 docs): **$14.51**.
- Prior pilot spend (v2 discarded doc-1 + smoke; v3/v4 never ran): **$3.20**.
- **Cumulative pilot spend (v2 + v5): $17.71.**
