# G1 EVAL prior art — family F7 addendum (DP noise parameters, vintage, rounding)

**Task:** `cc_tasks/2026-09-02_g1_eval_probe_family_v0.md`, step 0 (gated). **Date:** 2026-09-02/03 UTC. **Model calls:** zero. Extends `docs/research/2026-09-02_g1_eval_prior_art.md` (the memo); the run-1/2/3 logs are untouched.

**Query logs (machine-readable, new files):**
- `docs/research/2026-09-02_g1_eval_prior_art_query_log_f7.json` — the F7 run: 24 entries, 18 ok (6 OpenAlex title/abstract, 6 Semantic Scholar, 6 named lookups), 6 arXiv legs errored (HTTP 429).
- `…_query_log_f7_attempt1_arxiv429.json` — first attempt, kept: 24 entries, 19 ok; the one arXiv leg that returned (phrasing 5, 37 hits) is reviewed below.
- `…_query_log_f7_arxiv_retry.json`, `…_query_log_f7_arxiv_retry2.json` — arXiv-only retries after 2- and 15-minute back-offs: 12 entries each, 6 ok (OpenAlex), all 6 arXiv legs 429 (one read timeout). arXiv's API refused this host for the whole window; the F6 run (2026-09-02 21:27 UTC) had reached arXiv for the same topics, so the arXiv leg of F7 is **incomplete and recorded as errors, not zeros**.

Reproducing command: `scripts/g1_prior_art_search.py --families F7_dp_vintage_rounding --named-set f7 --skip-citations` (the script gained the F7 family, an F7 named set, `--named-set`, `--task`, and strips `?`/`:` from `title.search` values, which cost two titles in run 2).

## 1. Why F7

The memo's evidence that DP noise parameters and vintage/as-of dates are uncharted rested on family F6 (12 queries). F7 widens that with the vocabulary of the neighbouring fields — disclosure-avoidance user guidance, temporal-validity / stale-answer benchmarks, rounding-precision preservation — so a falsifier phrased in *their* words would be reached.

**Pre-registered falsifier (memo §3):** a work that annotates uncertainty carriers on statistical estimates and scores machine restatements against them. Hits that do not meet that description are neighbours and are recorded as such.

## 2. Results by phrasing

| # | phrasing | OpenAlex t/a | S2 | arXiv | nearest hits (all neighbours) |
|---|---|---|---|---|---|
| 1 | disclosure avoidance noise user guidance large language model | 0 | 50 | 429 | S2 top hits are LLM security/privacy papers (DP-FedLoRA, Whisper Leak); nothing on restating DP-protected statistics |
| 2 | differential privacy communicating noisy statistics data users | 1 | 561 | 429 | **Making Differential Privacy Work for Census Data Users** (HDSR 2023); **"Having Confidence in My Confidence Intervals": How Data Users Engage with Privacy-Protected Wikipedia Data** (2025); *Communicating the Privacy-Utility Trade-off* (2024) — all about human data users reading DP outputs, none about machine restatement |
| 3 | temporal validity statistics answer large language model release date | 0 | 19 | 429 | *Right Knowledge, Wrong Answer: parametric temporal conflict* (2026); *Time Present and Time Past* (2026); *Scaling Point-in-Time Language Models* (NBER 2026); *Mitigating Temporal Misalignment by Discarding Outdated Facts* (2023) — currency of the answer, not preservation of the as-of date |
| 4 | outdated statistic stale answer official data vintage | 0 | 7 | 429 | off-topic (BRFSS prevalence, Flint data story) |
| 5 | data release version temporal misalignment retrieval augmented | 0 | 107 | 37 (attempt 1) | **HoH: A Dynamic Benchmark for Evaluating the Impact of Outdated Information on RAG** (2025); *PAT-Questions* (2024); *Chronocept* (2025); *LiveVectorLake* (2025) — whether RAG surfaces current vs outdated facts |
| 6 | number rounding precision preservation summarization | 2 | 66 | 429 | off-topic (clinical, surgical) |

**Named lookups (OpenAlex `title.search`, abstracts read):**

| work | resolved | classification |
|---|---|---|
| FreshQA — Vu et al. 2023, arXiv:2310.03214 (FreshLLMs) | yes (Findings ACL 2024 + arXiv) | *temporal knowledge*: dynamic QA on fast-changing facts and false premises; scores whether the answer is current. Not a falsifier; does not supply a vintage-preservation metric. Not admitted. |
| TimeQA — Chen, Wang, Wang 2021, arXiv:2108.06314 | yes | *temporal reasoning*: time-sensitive QA over WikiData facts; accuracy of the time-conditioned answer. Not a falsifier; not admitted. |
| RealTime QA — Kasai et al. 2022, arXiv:2207.13332 | yes | weekly live QA; finding that GPT-3 "tends to return outdated answers when retrieved documents do not provide sufficient information". Currency, not as-of carriage. Not a falsifier; not admitted. |
| Cummings, Kaptchuk, Redmiles 2021, "I need a better description" (CCS; JPC 2023) | yes | user expectations of DP descriptions (n = 2,424); how DP is communicated sets expectations. Human reception of DP, no restatement instrument. Not a falsifier; not admitted. |
| Census Bureau, *Disclosure Avoidance for the 2020 Census: An Introduction* (Nov 2021) | not in OpenAlex; resolved on census.gov (`www2.census.gov/library/publications/decennial/2020/2020-census-disclosure-avoidance-handbook.pdf`) | the current DAS user handbook: publishes global rho 2.56 / epsilon 17.14 / delta 10⁻¹⁰ (people), rho 0.07 / epsilon 2.47 (units), per-geography rho allocations, and user-facing accuracy bounds. **Fetched and admitted** as `census-2020-disclosure-avoidance-handbook-2021` (batch-026, epoch `g1dp-2026-09-02`, rationale "G1 DP_NOISE fixture source"). It is a producer document, not a falsifier. |
| Abowd et al. 2022, *The 2020 Census DAS TopDown Algorithm* (HDSR) | yes | mechanism paper; no restatement instrument. Not admitted (the handbook carries the parameters). |

Companion brief C2020BR-04 (*How the TopDown Algorithm Works*, Mar 2023) was read: qualitative, no parameter values beyond the handbook's; not staged (`R1_no_marginal_contribution`).

## 3. Gate outcome

**No F7 hit meets the falsifier for any qualifier class.** The nearest objects are, for DP, human-reception studies of DP outputs (Cummings 2021; the 2023 HDSR data-users paper; the 2025 Wikipedia confidence-interval study) and, for vintage, temporal-knowledge benchmarks (FreshQA, TimeQA, RealTime QA, HoH, PAT-Questions) that measure whether an answer is *current* — none scores whether a restatement *carries the as-of date the source states*. That distinction is the finding: "temporal knowledge" is a currency criterion on the answer; G1's VINTAGE class is a carriage criterion on the restatement. Rounding-precision preservation returned nothing on-topic in any source.

Design steps for every class proceed. The DP class is built from the admitted handbook, not from an invented example.

**Search limit, stated.** The arXiv leg of F7 is missing (HTTP 429 on 18 of 19 attempts across three runs spanning ~40 minutes; one leg returned in attempt 1). If the falsifier exists under F7's vocabulary only on arXiv, this log shows exactly which six boolean queries have not yet been answered; they can be re-run with the reproducing command when the limiter clears.

## 4. Corpus-wide check for the other thin classes (recorded here because the same step found it)

The task's step 3 assumes `statcan-quality-guidelines-6th-edition` supplies CV bands, reliability flags and suppression rules with worked estimates. The 49-page text held in `corpus/g1eval` (pypdf, 153,213 chars) names "coefficient of variation, margin of error or confidence interval" as accuracy measures and "suppress" only as a process step; it carries **no** 16.6 % / 33.3 % band, no letter flag, and no suppressed cell. A full-text scan of every `manifest_add` document with a local file (207 of 211 pre-F7; 4 files absent locally) for reliability-flag / suppression / CV-band vocabulary found only the ACS handbook and the ONS page (both CV vocabulary, no flags or suppression). Consequences: RELIABILITY_FLAG is built from the ACS handbook's own verbal verdicts; SUPPRESSION is empty; a Seldon ResearchTask records the acquisition gap (task RESULT §3).
