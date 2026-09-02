# Prior art for the G1 EVAL tier — uncertainty preservation under AI restatement

**Task:** `cc_tasks/2026-09-02_g1_eval_prior_art.md`. **Date:** 2026-09-02. **Model calls:** zero (OpenAlex, arXiv, Semantic Scholar, Europe PMC and web search only).
**Query log (machine-readable):** `docs/research/2026-09-02_g1_eval_prior_art_query_log.json` (run 2, authoritative), `…_query_log_run1_fulltext.json` (run 1, kept because its failure shaped run 2), `…_query_log_f6.json` (run 3). The reproducing script is `scripts/g1_prior_art_search.py`. Web-search hits are logged in §5 by hand because those sources are not indexed by the scholarly APIs.

## 1. The question and the answer

The handoff of 2026-09-02 recorded the claim "uncertainty preservation has no known named prior art", and the Desktop two-query pass already falsified its strong form (clinical NLP has a named benchmark; science communication has a taxonomy). The residual claim this task tests is narrower:

> Does a named metric or benchmark exist for whether an LLM preserves **numeric** uncertainty — margin of error, confidence interval, standard error, coefficient of variation, differential-privacy noise parameters — when it restates a statistical estimate?

**Answer: no, not as a named instrument.** After 162 logged scholarly-API queries across six families, two citation walks, 26 named-work resolutions and 11 web searches (§5), nothing found measures whether a machine restatement of a point estimate keeps the uncertainty statement that was published with it. The evidence for that "no" is the query log itself: every family returned on-topic neighbours (§2), which shows the phrasing was reaching the literature, and none of those neighbours is the thing.

What *does* exist decomposes the problem almost completely. The G1 EVAL design is therefore an assembly of five settled pieces plus one genuinely open piece, not a first-principles design:

| piece | settled by | status |
|---|---|---|
| unit of analysis: proposition / atomic claim, not document | FActScore (Min 2023); Du 2026 uses 9,184 proposition-level annotations | **settled** |
| preservation as an ordinal level, not a binary; adjacent-level confusion as a named finding | Du 2026 (five levels); van der Bles 2019 (forms of expression) | **settled** |
| failure taxonomy: certainty assertion / omission / decontextualization / overgeneralization | Du 2026; Lee 2026; Peters & Chin-Yee 2025 | **settled** |
| direct vs indirect assessment (ask about the cue vs. summarize and check) | Du 2026 | **settled** |
| what counts as "the uncertainty" on the producer side: MOE at 90 %, CI, SE, CV, reliability bands, suppression | ACS handbook 2020; ONS methodology page; StatCan Quality Guidelines 6e; Manski 2015; Mazzi et al. 2021 | **settled** |
| the numeric-uncertainty preservation instrument itself (levels for numeric forms, scoring a restated interval, DP parameters, vintage) | — | **open: this is G1's contribution** |

## 2. Findings table

Every row was staged through the standing acquisition path (§4). "Unit" is the unit of analysis; "transfer" is one line on what it fixes for G1 (numeric uncertainty attached to a point estimate).

### 2.1 Uncertainty preservation under restatement (the construct itself)

| citation | measures | unit | metric | failure taxonomy | transfer to G1 |
|---|---|---|---|---|---|
| **Du, Lu, Qu 2026.** *Possible or Definite? A Benchmark for Evaluating Diagnostic Uncertainty Preservation in Clinical Text.* arXiv:2606.18471. **Admitted** (`du-2026-possible-or-definite`). | Whether an LLM summary/revision keeps the diagnostic uncertainty level of each proposition | proposition (9,184 annotations over 1,200 documents) | preservation rate at the annotated level; five-level ordinal scale; adjacent-level confusion | certainty assertion (cue removed, claim rewritten as definite); omission of the uncertainty-bearing proposition | The measurement design transfers whole: annotate the uncertainty carrier per proposition, score preservation ordinally, assess indirectly through a restatement task. Its cues are verbal (possible/probable/definite); G1's are numeric. |
| **Peters & Chin-Yee 2025.** *Generalization bias in large language model summarization of scientific research.* R. Soc. Open Sci. 12:241776. **Admitted** (`peters-2025-generalization-bias-llm-summarization`). | Whether LLM summaries widen the scope of a scientific claim beyond the source | summary–source pair (4,900 summaries, 10 models) | overgeneralization rate; OR 4.85 vs human summaries | overgeneralization: quantifiers, qualifiers, tense and population limits dropped | The scope-qualifier analogue of dropping an MOE; supplies a coding instrument for "qualifier dropped" and the finding that *accuracy prompting does not fix it* and *newer models are worse*. |
| **Lee, Park, Lee, Seo 2026.** *When Summaries Distort Decisions: Information Fidelity in LLM-Compressed Financial Analysis.* arXiv:2606.29251. **Admitted** (`lee-2026-when-summaries-distort-decisions`). | Whether compression changes the decision the source supports | source–compression pair | decision-flip under compression | **decontextualization** (evidence retained, caveats/qualifiers separated); model dependency | The only work found that names, generally, the failure "the number survives, the caveat does not". A decision-relevant definition of fidelity that G1 can adopt instead of a string-match. |
| Ansari 2026. *The Slop Paradox.* arXiv:2606.17791. Staged, **not admitted** (`ambiguous_contribution`, round-2 single-author precedent). | Hedging language lost under LLM rewriting of 450 radiology reports | report | hedging-collapse rate (43.7 % under EHR summarization) | hedging collapse; entity erosion | A measured erosion *rate* for verbal uncertainty under a realistic rewriting task; the construct name is carried by Du 2026. |
| Yang et al. 2025 *UNCLE* (arXiv:2505.16922); Yang et al. 2024 *LoGU* (arXiv:2410.14309). Staged, **not admitted** (`R1_out_of_scope`). | Whether a model expresses **its own** uncertainty in long-form answers | atomic claim | selective uncertainty-expression metrics | uncertainty suppression; uncertainty misalignment | A different construct (model epistemic state, not source-stated uncertainty). Recorded so the two are not conflated; the two failure names are usable vocabulary. |

### 2.2 Numeric fidelity of generated text (the nearest metric family)

| citation | measures | unit | metric | failure taxonomy | transfer to G1 |
|---|---|---|---|---|---|
| **Zhao, Cohen, Webber 2020.** *Reducing Quantity Hallucinations in Abstractive Summarization.* Findings of EMNLP. **Admitted** (`zhao-2020-reducing-quantity-hallucinations`). | Whether quantity entities in a summary are supported by the source | quantity entity (dates, numbers, sums) | support/unsupported per entity; ROUGE precision after re-ranking | quantity hallucination | Origin of the construct name and the entity class; verification unit for any number in a restatement. |
| **Cao, Raman, Dervovic, Tan 2024.** *Characterizing Multimodal Long-form Summarization: A Case Study on Financial Reports.* arXiv:2404.06162. **Admitted** (`cao-2024-multimodal-long-form-summarization-financial-reports`). | Numeric use in LLM summaries of number-heavy documents | number in summary | numeric-use characterization framework | explicit taxonomy of numeric hallucination | The taxonomy of ways an LLM gets a number wrong; G1 adds the ways it gets the number *right and the qualifier wrong*. |
| **Zhou, You, Yuan 2026.** *LOOMSUM: Table-Grounded Faithfulness.* arXiv:2609.00241. **Admitted** (`zhou-2026-loomsum-table-grounded-faithfulness`). | Whether summary claims are grounded in table numbers and correctly linked to narrative | claim | TGF = Numeric Grounding + Analysis Support + **Relation Consistency** | supported quantity paired with the wrong interpretation | Nearest existing metric to "is this number attached to the right qualifier"; its Relation Consistency component is the shape of a G1 score. |
| **Venktesh, Anand, Anand, Setty 2024.** *QuanTemp.* SIGIR. **Admitted** (`venktesh-2024-quantemp-numerical-claims`). | Veracity of natural numerical claims | claim | macro-F1 over fine-grained labels | claim taxonomy: temporal, statistical, comparison, **interval** | Supplies the claim-type axis; an MOE-bearing estimate is an interval-class claim. QuanTemp++ (2025) staged, not admitted, same construct. |
| **Min et al. 2023.** *FActScore.* EMNLP. **Admitted** (`min-2023-factscore`). | Factual precision of long-form generation | atomic fact | fraction of atomic facts supported | — | Fixes the atomic-fact unit that Du 2026 and LOOMSUM inherit. |
| SummaC, QAGS, FEQA, AlignScore, RAGAS, Vectara HHEM, FaithBench. Staged, **not admitted** (`R1_method_not_construct` / `R1_no_marginal_contribution`). | Summary/answer factual consistency | sentence / statement / span | NLI, QA-based, alignment, classifier scores | FaithBench: benign / questionable / unwanted | Number-blind and qualifier-blind: a restatement that keeps "12.3 %" and drops "± 1.8" scores as consistent under all of them. That is the measured gap. |
| Solatorio 2025. *Proof-Carrying Numbers.* arXiv:2509.06902. Staged, **not admitted** (`R1_method_not_construct`). | Renderer-side verification of numeric spans | numeric span | verified / unverified under a declared policy | — | The *tolerance-with-qualifiers* policy class is the one enforcement design that treats a number and its qualifier as one claim; a mechanism, not an instrument. |
| Upadhyay et al. 2025 *SporTabSet* (arXiv:2510.18173). Staged, **not admitted**. | Numerical fidelity in long tabular summarization | entity/statistic | accuracy, numerical fidelity | hallucination, omission, role confusion | Failure classes already carried by Cao 2024 and LOOMSUM. |

### 2.3 What "the uncertainty" is on the producer side (official statistics and science communication)

| citation | measures / defines | unit | metric | transfer to G1 |
|---|---|---|---|---|
| **van der Bles et al. 2019.** *Communicating uncertainty about facts, numbers and science.* R. Soc. Open Sci. 6:181870. **Admitted** (`van-der-bles-2019-communicating-uncertainty`). | Taxonomy: what uncertainty is *about* (facts, numbers, science), its *form* (numeric range, verbal qualifier, visual), and its reception | expression | — | Defines the preservation levels: a numeric range restated as a verbal qualifier is a level change, not a pass. |
| **Manski 2015.** *Communicating Uncertainty in Official Economic Statistics.* J. Econ. Lit. 53(3). **Admitted** (`manski-2015-…`, NBER w20098 copy). | Transitory, permanent and conceptual uncertainty in published estimates; the case against point estimates presented as exact | estimate | — | Fixes the uncertainty *classes* a probe can ask a consumer to preserve; the definitional anchor for the whole tier. |
| **Mazzi, Mitchell, Carausu 2021.** *Measuring and Communicating the Uncertainty in Official Economic Statistics.* J. Off. Stat. 37(2). **Admitted**. | Survey of NSO practice: data vs sampling uncertainty, revision-based intervals, density presentations | agency practice | — | The field's own survey of constructs; the producer-side counterpart to §2.1. |
| **U.S. Census Bureau 2020.** *Understanding and Using ACS Data: What All Data Users Need to Know.* **Admitted** (`census-acs-general-handbook-2020`). | MOE at the 90 % level as the published accuracy measure; how to carry and combine MOEs | estimate | — | The producer rule a G1 probe checks: an ACS estimate restated without its MOE has lost a *required* attribute of the product. |
| **ONS (UK).** *Uncertainty and how we measure it for our surveys.* **Admitted** (`ons-uncertainty-and-how-we-measure-it`). | Standard error, confidence interval, coefficient of variation, statistical significance | estimate | — | Second producer-side definition; names CV alongside CI. |
| **Statistics Canada 2019.** *Quality Guidelines, 6th ed.* (12-539-X). **Admitted** (`statcan-quality-guidelines-6th-edition`). | CV as the published accuracy measure; reliability bands; suppression rules | estimate | — | Gives G1 a CV-class qualifier and a *suppression* class (an estimate the producer would not publish at all). |
| van der Bles et al. 2020 (PNAS); Kerr et al. 2023 (R. Soc. Open Sci.). Staged, **not admitted** (`R1_no_marginal_contribution`). | Effect of communicating uncertainty on trust: numeric ranges barely reduce trust, verbal qualifiers reduce it more | respondent | trust deltas | Reception evidence for the 2019 taxonomy; not a construct. |
| Bakker 2023, *Should we include margins of error in public opinion polls?* EJPR. **Excluded**, not fetched (Wiley paywall). | Reader response to MOE reporting | respondent | — | Same lineage as above. |

### 2.4 Machine consumers restating published statistics (audits)

| citation | measures | unit | metric | failure taxonomy | transfer to G1 |
|---|---|---|---|---|---|
| **EBU / BBC 2025.** *News Integrity in AI Assistants.* **Admitted** (`ebu-bbc-2025-news-integrity-ai-assistants`). | Journalist-scored answers from four assistants, 18 countries, >3,000 responses | answer | significant-issue rate: 45 % overall; 31 % sourcing; 20 % major accuracy | accuracy, sourcing, opinion/fact, context | The largest audit instrument for machine restatement of published content; **has no uncertainty criterion**. G1 is that missing criterion. |
| **Radhakrishnan et al. 2024.** *Knowing When to Ask* (DataGemma). arXiv:2409.13741. **Admitted** (`radhakrishnan-2024-knowing-when-to-ask-data-commons`). | Accuracy of LLM answers to numerical/statistical questions grounded in Data Commons (UN, CDC, census bureaus) | answer | statistical-fact accuracy under RIG / RAG | — | The measured-practice document for machine consumers restating official statistics; evaluates the *number*, not its uncertainty or vintage. |
| **Suleymanli et al. 2025.** *Are LLMs ready to help non-expert users to make charts of official statistics data?* arXiv:2510.01197. **Admitted**. | LLMs over Statistics Netherlands open data | task | three dimensions: retrieval & pre-processing, code quality, visual representation | locating the right table dominates failures | Adjacent instrument on NSO data; its retrieval finding matches Suzgun 2026's. |
| UNECE HLG-MOS 2025, *Generative AI for Official Statistics* chapter. **Fetch failed** (unece.org 403 to every scripted fetch; `needs_source`). | NSO experience: GenAI "frequently provides dangerously reasonable but incorrect figures"; ONS StatsChat paused; StatCan IntelliStatCan | — | — | Producer testimony that the failure is live; the quote is from the web-search snippet, not from a held copy, and is cited as such. |
| Suzgun et al. 2026, *Evaluating Commercial AI Chatbots as News Intermediaries.* arXiv:2605.22785. Staged, **not admitted** (`R1_no_marginal_contribution`). | 2,100 same-day BBC questions, six chatbots, 14 days | question | free-response accuracy 11–17 pts below multiple-choice; >70 % of errors retrieval-driven | Anglophone retrieval bias; false-premise collapse | Audit evidence; instrument adds nothing beyond EBU/BBC and the held DeepTRACE. |
| Held already (R5): `liu-2023-evaluating-verifiability-generative-search`, `venkit-2025-deeptrace`, `zhang-2026-citation-selection-absorption`, `datacommons-docs-landing`. | citation recall/precision; deep-research reliability | — | — | Citation-level constructs; none scores uncertainty. |

## 3. The residual claim, stated precisely

**Claim.** As of 2026-09-02 there is no named benchmark, metric or annotation scheme whose object is the preservation of a *numeric* uncertainty statement (MOE, CI, SE, CV, DP noise parameters, reliability flag, vintage) when an LLM or AI answer engine restates a statistical estimate.

**Evidence.** The three query-log files (§5 and appendix): 162 scholarly-API queries, of which 158 returned (4 errored and are recorded as errors, not zeros); per-family results in §2 show every family reached its neighbouring literature. Family F1 (numeric uncertainty + restatement) returned **zero** on-topic works in all three sources after the run-2 phrasing fix; F6 (CV, DP parameters, vintage) returned zero on-topic works. The closest objects found are Du 2026 (verbal cues, clinical), LOOMSUM's Relation Consistency (number-to-narrative linking, no uncertainty), QuanTemp's interval claim class (veracity, not preservation), and Lee 2026's decontextualization (caveats generally, no metric).

**What would falsify it.** A work that annotates uncertainty carriers on statistical estimates and scores restatements against them. The searches that would have found it are F1 phrasings 1–4 and F6 phrasings 1–2 on OpenAlex title/abstract and arXiv abstract fields; if such a work exists under vocabulary those phrasings miss, the log shows exactly which vocabulary was tried.

**Search limits, stated.** Semantic Scholar rate-limited two queries (429 after five spaced retries); OpenAlex's `title.search` rejected two titles containing `?` (400); both recorded. OpenAlex full-text search (run 1) was discarded as a ranking instrument after it placed a 1987 AHP paper first for "numeric uncertainty preservation LLM summarization"; run 2 restricted to title/abstract. Forward citations of Du 2026 number 2 (both unrelated agent papers); forward citations of van der Bles 2019 number 447 (OpenAlex) / 374 (S2), filtered by "large language model", "numeric uncertainty communication" and "official statistics" with no LLM-restatement work among the top hits.

## 4. Design constraints for the Desktop session that follows

Fixed by the found prior art (adopt, cite, do not re-derive):

1. **Unit of analysis is the proposition / atomic claim** carrying one estimate and its qualifier(s) (FActScore; Du 2026). Not the document, not the number alone.
2. **Preservation is ordinal.** Du 2026's five verbal levels do not transfer, but the *structure* does: a numeric interval restated as a verbal qualifier ("about", "roughly") is a level change; a qualifier dropped is another; a qualifier fabricated is a third. van der Bles 2019's form-of-expression axis (numeric range / verbal qualifier / visual / none) is the ready-made level scale for numeric forms.
3. **Failure classes are named:** certainty assertion and omission (Du 2026), decontextualization (Lee 2026), overgeneralization (Peters & Chin-Yee 2025), quantity hallucination (Zhao 2020) with Cao 2024's numeric sub-taxonomy. G1 should map its observed failures onto these before adding any new name.
4. **Assess indirectly** (a restatement task, then score) as well as directly (ask for the uncertainty) — Du 2026 found the indirect route is where preservation fails.
5. **The producer rules define the ground truth,** not the probe author: ACS MOE at 90 % and combination rules; ONS SE/CI/CV; StatCan CV bands and suppression. A restatement that keeps an estimate the producer would have suppressed is its own failure class (source: StatCan 6e).
6. **Existing faithfulness metrics are number- and qualifier-blind** (§2.2); do not use SummaC/AlignScore/RAGAS-style scores as the G1 metric. LOOMSUM's Relation Consistency is the nearest shape.
7. **Accuracy prompting does not fix qualifier loss and newer models are not better** (Peters & Chin-Yee 2025) — a pre-registered expectation, not a hypothesis to discover.
8. **Retrieval, not reasoning, drives most restatement errors** (Suzgun 2026; Suleymanli 2025). A G1 probe must separate "found the wrong table/vintage" from "found the right estimate and dropped its MOE".

Open for G1 (the contribution; not designed here):

- the level scale for **numeric** forms and how a restated interval is scored (exact, rounded, widened, narrowed, converted to a verbal band);
- treatment of **coefficient of variation, reliability flags and suppression**, which have no counterpart in any found benchmark;
- **differential-privacy noise parameters and vintage/as-of dates** — F6 found nothing; these are uncharted;
- whether the audit criterion belongs in an EBU/BBC-style instrument (per answer) or a Du-style benchmark (per proposition), or both.

## 5. Web-search log (family 5 and official guidance; not indexed by the scholarly APIs)

| date | query (WebSearch) | what it returned that mattered |
|---|---|---|
| 2026-09-02 | EBU BBC "News Integrity in AI Assistants" study 2025 findings errors sourcing | EBU/BBC report PDF (admitted); Suzgun et al. 2026 arXiv:2605.22785 (staged) |
| 2026-09-02 | audit AI answer engines ChatGPT Perplexity official statistics accuracy census margin of error study | vendor comparison pages only; no audit with an MOE criterion |
| 2026-09-02 | Census Bureau "Understanding and Using American Community Survey Data" margin of error guidance handbook | ACS general handbook 2020 (admitted) |
| 2026-09-02 | ONS "uncertainty and how we measure it" guidance … | ONS methodology page (admitted) |
| 2026-09-02 | Peters Chin-Yee 2025 "generalization bias" … | RSOS 241776 / arXiv:2504.00025 (admitted); surfaced Lee 2026 arXiv:2606.29251 |
| 2026-09-02 | Pew Research OR "Reuters Institute" generative AI search answers statistics accuracy … | Reuters Institute Gen AI & News 2025 (usage survey; excluded `R1_out_of_scope`); Pew AI-overview usage figures |
| 2026-09-02 | "When Summaries Distort Decisions" … | arXiv:2606.29251 (admitted) |
| 2026-09-02 | Statistics Canada Quality Guidelines communicating sampling variability coefficient of variation … | StatCan 12-539-X 6e (admitted); CV bands 16.6 % / 33.3 % |
| 2026-09-02 | LLM summaries drop confidence intervals margin of error statistical uncertainty stripped study benchmark | nothing on-topic (hits were about CIs *on* LLM benchmark scores, e.g. arXiv:2604.11581 — off-construct, not staged) |
| 2026-09-02 | statistical office evaluation chatbot official statistics answers accuracy ONS StatsChat OR "Statistics Canada" OR Eurostat LLM experiment | UNECE HLG-MOS GenAI chapter (fetch failed, 403); IMF StatGPT (already held) |
| 2026-09-02 | NIST GenAI evaluation OR "Data Commons" DataGemma numeric accuracy … | DataGemma paper arXiv:2409.13741 (admitted); NIST GenAI T2T pilot is human-vs-AI text discrimination, off-construct, not staged |

## 6. Corpus routing summary

17 admitted (`events/batch-025.jsonl`, epoch `g1eval-2026-09-02`, corpus 194 → 211 included), 16 staged-not-admitted (bytes in `corpus/staging/inbox/g1eval_2026-09-02/`, register status `excluded` with clause), 3 excluded without fetch, 1 fetch failed (`needs_source`). Per-document verdicts and clauses: `scripts/g1eval_list_2026-09-02.yaml`; run summary: `docs/research/2026-09-02_g1eval_manifest_summary.json`. No extraction was run on any of them.

## Appendix — scholarly-API query log (every query, source, UTC timestamp, hit count)

**run 1 (OpenAlex full-text `search=`, arXiv AND-of-tokens)** — `docs/research/2026-09-02_g1_eval_prior_art_query_log_run1_fulltext.json`: 62 queries, 61 ok, 1 errored (recorded).

| family | source | query | date (UTC) | hits |
|---|---|---|---|---|
| F1_numeric_uncertainty_preservation | openalex | `numeric uncertainty preservation large language model summarization` | 2026-09-02T21:15 | 14798 |
| F1_numeric_uncertainty_preservation | arxiv | `all:numeric AND all:uncertainty AND all:preservation AND all:large AND all:language AND all:…` | 2026-09-02T21:15 | 1 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `numeric uncertainty preservation large language model summarization` | 2026-09-02T21:15 | 919 |
| F1_numeric_uncertainty_preservation | openalex | `margin of error confidence interval LLM paraphrase restatement` | 2026-09-02T21:15 | 78 |
| F1_numeric_uncertainty_preservation | arxiv | `all:margin AND all:error AND all:confidence AND all:interval AND all:LLM AND all:paraphrase …` | 2026-09-02T21:15 | 0 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `margin of error confidence interval LLM paraphrase restatement` | 2026-09-02T21:15 | 0 |
| F1_numeric_uncertainty_preservation | openalex | `standard error statistical estimate language model summary fidelity` | 2026-09-02T21:15 | 35871 |
| F1_numeric_uncertainty_preservation | arxiv | `all:standard AND all:error AND all:statistical AND all:estimate AND all:language AND all:mod…` | 2026-09-02T21:15 | 0 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `standard error statistical estimate language model summary fidelity` | 2026-09-02T21:16 | 920 |
| F1_numeric_uncertainty_preservation | openalex | `uncertainty interval retrieval-augmented generation numeric answer` | 2026-09-02T21:16 | 4336 |
| F1_numeric_uncertainty_preservation | arxiv | `all:uncertainty AND all:interval AND all:retrieval-augmented AND all:generation AND all:nume…` | 2026-09-02T21:16 | 0 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `uncertainty interval retrieval-augmented generation numeric answer` | 2026-09-02T21:16 | 270 |
| F2_quantitative_claim_fidelity | openalex | `numeric hallucination summarization` | 2026-09-02T21:16 | 18028 |
| F2_quantitative_claim_fidelity | arxiv | `all:numeric AND all:hallucination AND all:summarization` | 2026-09-02T21:16 | 19 |
| F2_quantitative_claim_fidelity | semantic_scholar | `numeric hallucination summarization` | 2026-09-02T21:16 | 26909 |
| F2_quantitative_claim_fidelity | openalex | `number faithfulness abstractive summarization` | 2026-09-02T21:16 | 51260 |
| F2_quantitative_claim_fidelity | arxiv | `all:number AND all:faithfulness AND all:abstractive AND all:summarization` | 2026-09-02T21:16 | 5 |
| F2_quantitative_claim_fidelity | semantic_scholar | `number faithfulness abstractive summarization` | 2026-09-02T21:16 | 15610 |
| F2_quantitative_claim_fidelity | openalex | `quantitative claim fidelity language model` | 2026-09-02T21:16 | 44875 |
| F2_quantitative_claim_fidelity | arxiv | `all:quantitative AND all:claim AND all:fidelity AND all:language AND all:model` | 2026-09-02T21:16 | 0 |
| F2_quantitative_claim_fidelity | semantic_scholar | `quantitative claim fidelity language model` | 2026-09-02T21:16 | 962 |
| F2_quantitative_claim_fidelity | openalex | `numerical consistency factual summarization evaluation` | 2026-09-02T21:16 | 19335 |
| F2_quantitative_claim_fidelity | arxiv | `all:numerical AND all:consistency AND all:factual AND all:summarization AND all:evaluation` | 2026-09-02T21:16 | 3 |
| F2_quantitative_claim_fidelity | semantic_scholar | `numerical consistency factual summarization evaluation` | 2026-09-02T21:16 | 335 |
| F3_hedging_epistemic_preservation | openalex | `hedging preservation summarization language model` | 2026-09-02T21:16 | 5479 |
| F3_hedging_epistemic_preservation | arxiv | `all:hedging AND all:preservation AND all:summarization AND all:language AND all:model` | 2026-09-02T21:16 | 1 |
| F3_hedging_epistemic_preservation | semantic_scholar | `hedging preservation summarization language model` | 2026-09-02T21:16 | 174 |
| F3_hedging_epistemic_preservation | openalex | `epistemic uncertainty preservation clinical text LLM` | 2026-09-02T21:16 | 384 |
| F3_hedging_epistemic_preservation | arxiv | `all:epistemic AND all:uncertainty AND all:preservation AND all:clinical AND all:text AND all…` | 2026-09-02T21:16 | 0 |
| F3_hedging_epistemic_preservation | semantic_scholar | `epistemic uncertainty preservation clinical text LLM` | 2026-09-02T21:16 | 152 |
| F3_hedging_epistemic_preservation | openalex | `speculation cue certainty summarization evaluation` | 2026-09-02T21:17 | 2376 |
| F3_hedging_epistemic_preservation | arxiv | `all:speculation AND all:cue AND all:certainty AND all:summarization AND all:evaluation` | 2026-09-02T21:17 | 0 |
| F3_hedging_epistemic_preservation | semantic_scholar | `speculation cue certainty summarization evaluation` | 2026-09-02T21:17 | 6 |
| F4_uncertainty_communication_statistics | openalex | `communicating uncertainty statistics margin of error public` | 2026-09-02T21:17 | 25313 |
| F4_uncertainty_communication_statistics | arxiv | `all:communicating AND all:uncertainty AND all:statistics AND all:margin AND all:error AND al…` | 2026-09-02T21:17 | 0 |
| F4_uncertainty_communication_statistics | semantic_scholar | `communicating uncertainty statistics margin of error public` | 2026-09-02T21:17 | 24 |
| F4_uncertainty_communication_statistics | openalex | `sampling error communication official statistics guidance` | 2026-09-02T21:17 | 72115 |
| F4_uncertainty_communication_statistics | arxiv | `all:sampling AND all:error AND all:communication AND all:official AND all:statistics AND all…` | 2026-09-02T21:17 | 0 |
| F4_uncertainty_communication_statistics | semantic_scholar | `sampling error communication official statistics guidance` | 2026-09-02T21:17 | 2097 |
| F4_uncertainty_communication_statistics | openalex | `communicating statistical uncertainty numeric verbal formats` | 2026-09-02T21:17 | 10677 |
| F4_uncertainty_communication_statistics | arxiv | `all:communicating AND all:statistical AND all:uncertainty AND all:numeric AND all:verbal AND…` | 2026-09-02T21:17 | 0 |
| F4_uncertainty_communication_statistics | semantic_scholar | `communicating statistical uncertainty numeric verbal formats` | 2026-09-02T21:17 | 415 |
| F5_answer_engines_official_statistics | openalex | `generative search engine official statistics accuracy audit` | 2026-09-02T21:17 | 1445 |
| F5_answer_engines_official_statistics | arxiv | `all:generative AND all:search AND all:engine AND all:official AND all:statistics AND all:acc…` | 2026-09-02T21:17 | 0 |
| F5_answer_engines_official_statistics | semantic_scholar | `generative search engine official statistics accuracy audit` | 2026-09-02T21:17 | 14 |
| F5_answer_engines_official_statistics | openalex | `AI answer engine citing statistics accuracy margin of error` | 2026-09-02T21:17 | 1802 |
| F5_answer_engines_official_statistics | arxiv | `all:answer AND all:engine AND all:citing AND all:statistics AND all:accuracy AND all:margin …` | 2026-09-02T21:17 | 0 |
| F5_answer_engines_official_statistics | semantic_scholar | `AI answer engine citing statistics accuracy margin of error` | 2026-09-02T21:19 | error (s2 429: {"message": "Too Many Req…) |
| F5_answer_engines_official_statistics | openalex | `LLM chatbot statistical data accuracy evaluation official statistics` | 2026-09-02T21:19 | 2864 |
| F5_answer_engines_official_statistics | arxiv | `all:LLM AND all:chatbot AND all:statistical AND all:data AND all:accuracy AND all:evaluation…` | 2026-09-02T21:19 | 0 |
| F5_answer_engines_official_statistics | semantic_scholar | `LLM chatbot statistical data accuracy evaluation official statistics` | 2026-09-02T21:19 | 179 |
| CIT_forward_arxiv_2606_18471 | openalex | `cites:https://openalex.org/W7165197799` | 2026-09-02T21:19 | 0 |
| CIT_backward_arxiv_2606_18471 | openalex | `referenced_works of https://openalex.org/W7165197799` | 2026-09-02T21:19 | 0 |
| CIT_forward_arxiv_2606_18471 | semantic_scholar | `citations of arXiv:2606.18471` | 2026-09-02T21:19 | 2 |
| CIT_backward_arxiv_2606_18471 | semantic_scholar | `references of arXiv:2606.18471` | 2026-09-02T21:19 | 38 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219` | 2026-09-02T21:19 | 447 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219 search=large language model` | 2026-09-02T21:19 | 128 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219 search=numeric uncertainty communication` | 2026-09-02T21:19 | 113 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219 search=official statistics` | 2026-09-02T21:19 | 55 |
| CIT_backward_vanderbles_2019 | openalex | `referenced_works of https://openalex.org/W2943845219` | 2026-09-02T21:19 | 157 |
| CIT_forward_vanderbles_2019 | semantic_scholar | `citations of DOI:10.1098/rsos.181870` | 2026-09-02T21:19 | 374 |
| CIT_backward_vanderbles_2019 | semantic_scholar | `references of DOI:10.1098/rsos.181870` | 2026-09-02T21:20 | 200 |

**run 2 (OpenAlex `title_and_abstract.search`, arXiv boolean, named lookups, citation walks)** — `docs/research/2026-09-02_g1_eval_prior_art_query_log.json`: 88 queries, 86 ok, 2 errored (recorded).

| family | source | query | date (UTC) | hits |
|---|---|---|---|---|
| F1_numeric_uncertainty_preservation | openalex:title_abstract | `numeric uncertainty preservation large language model summarization` | 2026-09-02T21:22 | 0 |
| F1_numeric_uncertainty_preservation | arxiv | `abs:"uncertainty" AND abs:"preserv" AND (abs:summarization OR abs:paraphrase) AND (abs:LLM O…` | 2026-09-02T21:22 | 13 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `numeric uncertainty preservation large language model summarization` | 2026-09-02T21:22 | 919 |
| F1_numeric_uncertainty_preservation | openalex:title_abstract | `margin of error confidence interval LLM paraphrase restatement` | 2026-09-02T21:22 | 0 |
| F1_numeric_uncertainty_preservation | arxiv | `(abs:"margin of error" OR abs:"confidence interval") AND (abs:LLM OR abs:"language model") A…` | 2026-09-02T21:22 | 9 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `margin of error confidence interval LLM paraphrase restatement` | 2026-09-02T21:22 | 0 |
| F1_numeric_uncertainty_preservation | openalex:title_abstract | `standard error statistical estimate language model summary fidelity` | 2026-09-02T21:22 | 8 |
| F1_numeric_uncertainty_preservation | arxiv | `(abs:"standard error" OR abs:"sampling error") AND (abs:LLM OR abs:"large language model") A…` | 2026-09-02T21:22 | 1 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `standard error statistical estimate language model summary fidelity` | 2026-09-02T21:22 | 920 |
| F1_numeric_uncertainty_preservation | openalex:title_abstract | `uncertainty interval retrieval-augmented generation numeric answer` | 2026-09-02T21:22 | 0 |
| F1_numeric_uncertainty_preservation | arxiv | `abs:"retrieval-augmented" AND (abs:"confidence interval" OR abs:"uncertainty interval" OR ab…` | 2026-09-02T21:22 | 15 |
| F1_numeric_uncertainty_preservation | semantic_scholar | `uncertainty interval retrieval-augmented generation numeric answer` | 2026-09-02T21:22 | 270 |
| F2_quantitative_claim_fidelity | openalex:title_abstract | `numeric hallucination summarization` | 2026-09-02T21:22 | 50 |
| F2_quantitative_claim_fidelity | arxiv | `(abs:"numeric hallucination" OR abs:"numerical hallucination" OR abs:"quantity hallucination…` | 2026-09-02T21:22 | 16 |
| F2_quantitative_claim_fidelity | semantic_scholar | `numeric hallucination summarization` | 2026-09-02T21:22 | 26909 |
| F2_quantitative_claim_fidelity | openalex:title_abstract | `number faithfulness abstractive summarization` | 2026-09-02T21:22 | 36 |
| F2_quantitative_claim_fidelity | arxiv | `(abs:numer OR abs:quantit OR abs:number) AND abs:faithful AND abs:summarization` | 2026-09-02T21:22 | 29 |
| F2_quantitative_claim_fidelity | semantic_scholar | `number faithfulness abstractive summarization` | 2026-09-02T21:23 | 15610 |
| F2_quantitative_claim_fidelity | openalex:title_abstract | `quantitative claim fidelity language model` | 2026-09-02T21:23 | 41 |
| F2_quantitative_claim_fidelity | arxiv | `(abs:"numerical claim" OR abs:"quantitative claim" OR abs:"statistical claim") AND (abs:LLM …` | 2026-09-02T21:23 | 19 |
| F2_quantitative_claim_fidelity | semantic_scholar | `quantitative claim fidelity language model` | 2026-09-02T21:23 | 962 |
| F2_quantitative_claim_fidelity | openalex:title_abstract | `numerical consistency factual summarization evaluation` | 2026-09-02T21:23 | 13 |
| F2_quantitative_claim_fidelity | arxiv | `abs:"factual consistency" AND abs:summarization AND (abs:numer OR abs:number OR abs:quantit)` | 2026-09-02T21:23 | 9 |
| F2_quantitative_claim_fidelity | semantic_scholar | `numerical consistency factual summarization evaluation` | 2026-09-02T21:23 | 335 |
| F3_hedging_epistemic_preservation | openalex:title_abstract | `hedging preservation summarization language model` | 2026-09-02T21:23 | 0 |
| F3_hedging_epistemic_preservation | arxiv | `(abs:hedg OR abs:hedges) AND (abs:summar OR abs:generat) AND (abs:LLM OR abs:"language model")` | 2026-09-02T21:23 | 3 |
| F3_hedging_epistemic_preservation | semantic_scholar | `hedging preservation summarization language model` | 2026-09-02T21:23 | 174 |
| F3_hedging_epistemic_preservation | openalex:title_abstract | `epistemic uncertainty preservation clinical text LLM` | 2026-09-02T21:23 | 0 |
| F3_hedging_epistemic_preservation | arxiv | `(abs:"uncertainty preservation" OR abs:"preserve uncertainty" OR abs:"preserving uncertainty…` | 2026-09-02T21:23 | 33 |
| F3_hedging_epistemic_preservation | semantic_scholar | `epistemic uncertainty preservation clinical text LLM` | 2026-09-02T21:23 | 152 |
| F3_hedging_epistemic_preservation | openalex:title_abstract | `speculation cue certainty summarization evaluation` | 2026-09-02T21:23 | 0 |
| F3_hedging_epistemic_preservation | arxiv | `(abs:speculat OR abs:"epistemic stance" OR abs:overgeneraliz OR abs:overclaim) AND abs:summa…` | 2026-09-02T21:23 | 0 |
| F3_hedging_epistemic_preservation | semantic_scholar | `speculation cue certainty summarization evaluation` | 2026-09-02T21:23 | 6 |
| F4_uncertainty_communication_statistics | openalex:title_abstract | `communicating uncertainty statistics margin of error public` | 2026-09-02T21:23 | 13 |
| F4_uncertainty_communication_statistics | arxiv | `abs:"communicating uncertainty" AND (abs:statistic OR abs:"margin of error")` | 2026-09-02T21:23 | 3 |
| F4_uncertainty_communication_statistics | semantic_scholar | `communicating uncertainty statistics margin of error public` | 2026-09-02T21:23 | 24 |
| F4_uncertainty_communication_statistics | openalex:title_abstract | `sampling error communication official statistics guidance` | 2026-09-02T21:23 | 4 |
| F4_uncertainty_communication_statistics | arxiv | `abs:"official statistics" AND (abs:uncertainty OR abs:"sampling error") AND (abs:communicat …` | 2026-09-02T21:23 | 6 |
| F4_uncertainty_communication_statistics | semantic_scholar | `sampling error communication official statistics guidance` | 2026-09-02T21:23 | 2097 |
| F4_uncertainty_communication_statistics | openalex:title_abstract | `communicating statistical uncertainty numeric verbal formats` | 2026-09-02T21:24 | 2 |
| F4_uncertainty_communication_statistics | arxiv | `abs:uncertainty AND abs:communicat AND (abs:verbal OR abs:numeric OR abs:"margin of error") …` | 2026-09-02T21:24 | 0 |
| F4_uncertainty_communication_statistics | semantic_scholar | `communicating statistical uncertainty numeric verbal formats` | 2026-09-02T21:24 | 415 |
| F5_answer_engines_official_statistics | openalex:title_abstract | `generative search engine official statistics accuracy audit` | 2026-09-02T21:24 | 0 |
| F5_answer_engines_official_statistics | arxiv | `(abs:"generative search" OR abs:"answer engine" OR abs:"AI overview" OR abs:chatbot) AND (ab…` | 2026-09-02T21:24 | 1 |
| F5_answer_engines_official_statistics | semantic_scholar | `generative search engine official statistics accuracy audit` | 2026-09-02T21:24 | 14 |
| F5_answer_engines_official_statistics | openalex:title_abstract | `AI answer engine citing statistics accuracy margin of error` | 2026-09-02T21:24 | 0 |
| F5_answer_engines_official_statistics | arxiv | `(abs:"generative search" OR abs:"answer engine" OR abs:"AI assistant") AND abs:audit AND (ab…` | 2026-09-02T21:24 | 9 |
| F5_answer_engines_official_statistics | semantic_scholar | `AI answer engine citing statistics accuracy margin of error` | 2026-09-02T21:24 | 0 |
| F5_answer_engines_official_statistics | openalex:title_abstract | `LLM chatbot statistical data accuracy evaluation official statistics` | 2026-09-02T21:24 | 0 |
| F5_answer_engines_official_statistics | arxiv | `(abs:LLM OR abs:"language model") AND abs:"official statistics"` | 2026-09-02T21:24 | 6 |
| F5_answer_engines_official_statistics | semantic_scholar | `LLM chatbot statistical data accuracy evaluation official statistics` | 2026-09-02T21:24 | 179 |
| NAMED | openalex:title | `Generalization bias in large language model summarization of scientific research` | 2026-09-02T21:24 | 8 |
| NAMED | openalex:title | `Reducing Quantity Hallucinations in Abstractive Summarization` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `QuanTemp: A real-world open-domain benchmark for fact-checking numerical claims` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `Knowing When to Ask - Bridging Large Language Models and Data` | 2026-09-02T21:24 | 1 |
| NAMED | openalex:title | `UNCLE: Benchmarking Uncertainty Expressions in Long-Form Generation` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `LoGU: Long-form Generation with Uncertainty Expressions` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `The effects of communicating uncertainty on public trust in facts and numbers` | 2026-09-02T21:24 | 3 |
| NAMED | openalex:title | `The effects of communicating uncertainty around statistics, on public trust` | 2026-09-02T21:24 | 15 |
| NAMED | openalex:title | `Communicating Uncertainty in Official Economic Statistics: An Appraisal Fifty Years after Mo…` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `Measuring and Communicating the Uncertainty in Official Economic Statistics` | 2026-09-02T21:24 | 1 |
| NAMED | openalex:title | `Should we include margins of error in public opinion polls?` | 2026-09-02T21:24 | error (openalex 400: {"error":"Invalid q…) |
| NAMED | openalex:title | `The Slop Paradox: How Synthetic Standardization Erodes Clinical Uncertainty` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `LOOMSUM: Weaving Quantitative and Narrative Evidence for Faithful Long Text-Table Summarization` | 2026-09-02T21:24 | 0 |
| NAMED | openalex:title | `FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `SummaC: Re-Visiting NLI-based Models for Inconsistency Detection in Summarization` | 2026-09-02T21:24 | 3 |
| NAMED | openalex:title | `Asking and Answering Questions to Evaluate the Factual Consistency of Summaries` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `FEQA: A Question Answering Evaluation Framework for Faithfulness Assessment in Abstractive S…` | 2026-09-02T21:24 | 1 |
| NAMED | openalex:title | `AlignScore: Evaluating Factual Consistency with a Unified Alignment Function` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `RAGAS: Automated Evaluation of Retrieval Augmented Generation` | 2026-09-02T21:24 | 1 |
| NAMED | openalex:title | `FaithBench: A Diverse Hallucination Benchmark for Summarization by Modern LLMs` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `Understanding and Using American Community Survey Data: What All Data Users Need to Know` | 2026-09-02T21:24 | 0 |
| NAMED | openalex:title | `Are LLMs ready to help non-expert users to make charts of official statistics data?` | 2026-09-02T21:24 | error (openalex 400: {"error":"Invalid q…) |
| NAMED | openalex:title | `Moneyball with LLMs: Analyzing Tabular Summarization in Sports Narratives` | 2026-09-02T21:24 | 2 |
| NAMED | openalex:title | `Hedges in scientific writing large language models` | 2026-09-02T21:24 | 0 |
| NAMED | openalex:title | `Do large language models preserve hedges when summarizing scientific abstracts` | 2026-09-02T21:24 | 0 |
| NAMED | openalex:title | `Numerical reasoning faithfulness in data-to-text generation hallucination` | 2026-09-02T21:24 | 0 |
| CIT_forward_arxiv_2606_18471 | openalex | `cites:https://openalex.org/W7165197799` | 2026-09-02T21:24 | 0 |
| CIT_backward_arxiv_2606_18471 | openalex | `referenced_works of https://openalex.org/W7165197799` | 2026-09-02T21:24 | 0 |
| CIT_forward_arxiv_2606_18471 | semantic_scholar | `citations of arXiv:2606.18471` | 2026-09-02T21:24 | 2 |
| CIT_backward_arxiv_2606_18471 | semantic_scholar | `references of arXiv:2606.18471` | 2026-09-02T21:24 | 38 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219` | 2026-09-02T21:24 | 447 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219 search=large language model` | 2026-09-02T21:24 | 128 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219 search=numeric uncertainty communication` | 2026-09-02T21:24 | 113 |
| CIT_forward_vanderbles_2019 | openalex | `cites:https://openalex.org/W2943845219 search=official statistics` | 2026-09-02T21:24 | 55 |
| CIT_backward_vanderbles_2019 | openalex | `referenced_works of https://openalex.org/W2943845219` | 2026-09-02T21:24 | 157 |
| CIT_forward_vanderbles_2019 | semantic_scholar | `citations of DOI:10.1098/rsos.181870` | 2026-09-02T21:24 | 374 |
| CIT_backward_vanderbles_2019 | semantic_scholar | `references of DOI:10.1098/rsos.181870` | 2026-09-02T21:24 | 200 |

**run 3 (family F6, qualifier classes)** — `docs/research/2026-09-02_g1_eval_prior_art_query_log_f6.json`: 12 queries, 12 ok, 0 errored (recorded).

| family | source | query | date (UTC) | hits |
|---|---|---|---|---|
| F6_numeric_qualifier_preservation | openalex:title_abstract | `caveat qualifier preservation LLM summarization decontextualization` | 2026-09-02T21:27 | 0 |
| F6_numeric_qualifier_preservation | arxiv | `(abs:caveat OR abs:qualifier OR abs:decontextualiz) AND (abs:summar OR abs:compress) AND (ab…` | 2026-09-02T21:27 | 8 |
| F6_numeric_qualifier_preservation | semantic_scholar | `caveat qualifier preservation LLM summarization decontextualization` | 2026-09-02T21:27 | 1 |
| F6_numeric_qualifier_preservation | openalex:title_abstract | `coefficient of variation relative standard error LLM generated text statistics` | 2026-09-02T21:27 | 0 |
| F6_numeric_qualifier_preservation | arxiv | `(abs:"coefficient of variation" OR abs:"relative standard error") AND (abs:LLM OR abs:"langu…` | 2026-09-02T21:27 | 20 |
| F6_numeric_qualifier_preservation | semantic_scholar | `coefficient of variation relative standard error LLM generated text statistics` | 2026-09-02T21:27 | 0 |
| F6_numeric_qualifier_preservation | openalex:title_abstract | `differential privacy noise disclosure LLM answer official statistics` | 2026-09-02T21:27 | 0 |
| F6_numeric_qualifier_preservation | arxiv | `abs:"differential privacy" AND (abs:"official statistics" OR abs:census) AND (abs:LLM OR abs…` | 2026-09-02T21:27 | 0 |
| F6_numeric_qualifier_preservation | semantic_scholar | `differential privacy noise disclosure LLM answer official statistics` | 2026-09-02T21:27 | 6 |
| F6_numeric_qualifier_preservation | openalex:title_abstract | `data vintage release date stale statistics LLM answer` | 2026-09-02T21:27 | 0 |
| F6_numeric_qualifier_preservation | arxiv | `(abs:vintage OR abs:"as of" OR abs:stale OR abs:outdated) AND abs:statistic AND (abs:LLM OR …` | 2026-09-02T21:27 | 9 |
| F6_numeric_qualifier_preservation | semantic_scholar | `data vintage release date stale statistics LLM answer` | 2026-09-02T21:28 | 0 |

Total scholarly-API queries logged: 162.
