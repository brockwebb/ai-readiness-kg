# Live demonstration sheet: eight questions for the two graphs

Prepared 7 October 2026. Each question was run once against the live servers from Claude Code: fss-policy-kg (federal statistical policy, through the claude.ai connector) and ai-readiness-kg (the AI-readiness framework and its corpus, through its local server), with the projection check green. The tool call is the one to repeat in the room; the answer is two sentences written from what the call returned; the locators are what to show. The full returned rows are in `demo/runs_fss.json` and `demo/runs_airkg.json`. If the room has no network, read the answer and show the locator from those files.

## 1. What does OMB require of the metadata agencies send to Data.gov? (fss-policy-kg)

- **Call:** `fss_policy_kg_search_text(phrase="DCAT-US", limit=10)` (120 hits).
- **Answer:** The Implementation Guide states, as an obligation, that OMB requires metadata submitted to Data.gov to conform to the DCAT-US v3.0 schema. It also recommends agencies be aware that a submission that conforms to the schema does not, by itself, guarantee compliance with M-25-05's metadata requirements.
- **Locators:** Obligation `3ad0b08443e74e6fb4c9191d0e957c5d` and Obligation `c9d8dc5eb8fd4e4abd69ee44e712e7e9`, both in `dcat_us_3_implementation_guide`.

## 2. By when must agencies have their inventories in DCAT-US 3.0? (fss-policy-kg)

- **Call:** `fss_policy_kg_search_text(phrase="September 30, 2026", limit=8)` (8 hits).
- **Answer:** M-25-05's action table carries the date September 30, 2026 in six rows, and the Implementation Guide says Title II of the Evidence Act and M-25-05 direct each agency to keep a comprehensive data inventory and submit its metadata. The date is September 30, 2026.
- **Locators:** Segments `m_25_05#s468` (and `#s479`, `#s487`, `#s493`, `#s501`, `#s508`); `dcat_us_3_implementation_guide#s70`.

## 3. Is the framework's issuing-authority indicator current to DCAT-US 3.0, and what did it find? (ai-readiness-kg)

- **Call:** `get_indicator(code="G4")`.
- **Answer:** Indicator G4 reads issuing authority from `publisher`, which DCAT-US 3.0 defines as Recommended, or from `bureauCode` and `programCode`, which v1.1 requires of federal datasets and 3.0 neither defines nor rejects. On the cycle of record it measured 8 products as fail and 15 as error, and none as pass.
- **Locators:** `framework/ai_readiness_framework.json#ind:G4`; rule `RULE-G4-v2`; cycle `scan_2026-10-06_composite_b`.

## 4. What do the documents say "fitness for use" means? (ai-readiness-kg)

- **Call:** `search_text(q="fitness for use", limit=8)` (6 hits).
- **Answer:** FCSM 19-01 defines data quality from the user's side as the data's fitness for use for the user's own needs, and FCSM 25-03 says FCSM built its Framework for Data Quality to help analysts and the public assess fitness for use. The W3C Data on the Web Best Practices gives the same definition for a specific application or use case.
- **Locators:** Definitions `fcsm-19-01-transparent-reporting-for-integrated-data-quality::d_data_quality`, `fcsm-25-03::def-fcsm-framework`, `w3c-dwbp-2017::def-data-quality`.

## 5. What does the collection hold from DDI-CDI, the cross-domain statistical model added today? (ai-readiness-kg)

- **Call:** `get_document(doc_id="ddi-cdi-1-0-specification")`.
- **Answer:** The DDI-CDI 1.0 Specification Overview (DDI Alliance, January 2025) is in the collection with its content hash, and the graph holds 79 definitions, 227 claims, 56 standards and 388 concepts drawn from it. No framework indicator cites it yet.
- **Locators:** Document `ddi-cdi-1-0-specification`, sha256 `8c67ef2ed84a…`; `evidences_indicators` is empty.

## 6. Who issued the DCAT-US 3.0 Implementation Guide, and when? (both graphs)

- **Calls:** `fss_policy_kg_get_document(doc_id="dcat_us_3_implementation_guide")`; `get_document(doc_id="dcat-us-3-implementation-guide")`.
- **Answer:** fss-policy-kg records the Federal CDO Council as issuer with a baseline date of 21 August 2026, while ai-readiness-kg dates the same PDF 9 September 2026 (version 1.1). Both are right about different things: the cover says August 21, 2026 and the version history says 1.1, September 9, 2026, which is the disagreement the FAQ's attachment records.
- **Locators:** fss `dcat_us_3_implementation_guide` (171 obligations, 1,299 segments); ai-readiness-kg Document `dcat-us-3-implementation-guide`, sha256 `26e4c3baecb2…` in both.

## 7. Does federal policy, or the readiness record, say how margins of error should be published? (both graphs)

- **Calls:** `fss_policy_kg_search_text(phrase="margin of error", limit=10)`; `search_text(q="margin of error", limit=8)`.
- **Answer:** fss-policy-kg has two passing mentions and no obligation: FCSM 25-02 notes smaller geographies have higher margins of error. ai-readiness-kg has the American Community Survey handbook's definition and one framework action, G1-D, to publish the error measure as a structured field beside the estimate.
- **Locators:** fss `fcsm_25_02#s173`; ai-readiness-kg `census-acs-general-handbook-2020::d_margin_of_error`, `framework/ai_readiness_framework.json#act:g1d-publish-the-error-measure-as-a-structured-field`.

## 8. What did the FAIRness Project's sequencing plan recommend? (both graphs)

- **Calls:** `fss_policy_kg_search_text(phrase="sequencing plan", limit=10)`; `search_text(q="sequencing plan", limit=8)`.
- **Answer:** The graphs do not hold this. fss-policy-kg holds only the plan's citation in the Implementation Guide and the wiki's one-line description of it, and ai-readiness-kg's search finds no hit; the plan went to OMB and was not published.
- **Locators:** fss `dcat_us_3_implementation_guide#s91`, `fairness_project_wiki_overview#s5`; ai-readiness-kg `search_text` returned 0 hits.

Questions the graphs could not answer: 8 (the sequencing plan's content). Question 7's answer is a partial one: neither graph holds a federal requirement to publish margins of error in catalog metadata.
