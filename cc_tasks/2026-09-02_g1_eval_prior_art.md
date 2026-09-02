# CC Task: Prior-art search for the G1 EVAL tier — uncertainty preservation under AI restatement

**Date:** 2026-09-02
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-02_g1_eval_prior_art_ADDENDUM*.md` files.**

## Context

Hop 4 / the EVAL tier for group C and G1 has no implementation anywhere. The standing rule is search before design. The handoff of 2026-09-02 recorded "uncertainty-preservation has no known named prior art" as a claim requiring the failed search. A two-query Desktop pass on 2026-09-02 already falsified the strong form of that claim:

- **Named prior art for the construct exists in clinical NLP:** "Possible or Definite? A Benchmark for Evaluating Diagnostic Uncertainty Preservation in Clinical Text" (arXiv:2606.18471, June 2026) — 1,200 documents, 9,184 proposition-level uncertainty annotations on a five-level scale; indirect assessment via summarization and revision; finding that baseline LLMs preserve the original uncertainty level under half the time, dominant failure mode "certainty assertion" (uncertainty cue removed, claim rewritten as definite), second mode omission of the uncertainty-bearing proposition. This is epistemic/hedging uncertainty, not numeric uncertainty, but the measurement design (proposition-level annotation, ordinal preservation levels, named failure taxonomy, direct vs indirect assessment) transfers.
- **Science-communication prior art** for what "preserving numeric uncertainty" means: van der Bles et al. 2019, "Communicating uncertainty about facts, numbers and science," Royal Society Open Science 6:181870 — taxonomy of what uncertainty is expressed about (facts, numbers, science), forms of expression (numeric range, verbal qualifier, visual), and evidence on how each form is received.
- **Not found in two queries:** any benchmark or metric for whether LLMs preserve *numeric* uncertainty (MOE, CI, CV, standard error, DP noise parameters) when restating statistical estimates. That is the residual "no prior art" claim; this task performs the search that either finds it or records the failure.

## Steps

### 1. Systematic search, logged

Use the OpenAlex client and auth already in the repo (see `cc_tasks/2026-08-29_openalex_auth_and_eligibility_RESULT.md`), arXiv, and Semantic Scholar. Log every query string, source, date, and hit count in the memo. Minimum query families, each run in at least two phrasings:

1. numeric uncertainty preservation / margin of error / confidence interval / standard error + LLM summarization / restatement / paraphrase / RAG
2. quantitative claim fidelity / numeric hallucination / number faithfulness in summarization (known families to place: FActScore-style atomic-fact decomposition; SummaC / QAGS / FEQA / AlignScore; RAGAS faithfulness; Vectara HHEM)
3. hedging / epistemic uncertainty preservation in summarization (follow citations forward and backward from arXiv:2606.18471)
4. uncertainty communication for statistics — van der Bles 2019 forward citations; official-statistics guidance on communicating sampling error (Census ACS MOE guidance, ONS, Statistics Canada quality guidelines)
5. AI answer engines / LLM search citing official statistics — any audit of whether MOEs or vintages survive (Pew, Reuters Institute, NIST GenAI, or academic)

### 2. Memo

Write `docs/research/2026-09-02_g1_eval_prior_art.md`:

- **Findings table:** for each candidate, citation, what it measures, unit of analysis, metric, failure taxonomy if any, and one line on transferability to G1 (numeric uncertainty attached to a point estimate).
- **The residual claim, stated precisely:** after these searches, does a named metric/benchmark for numeric-uncertainty preservation exist? Yes with citation, or no with the query log as evidence.
- **Design constraints for the Desktop session that follows:** what the found prior art fixes (annotation unit, preservation levels, failure classes, direct vs indirect assessment) versus what remains open for the G1 probe family. Do not design the probes.

### 3. Corpus

Route every document you would cite through the standing acquisition path: stage under `corpus/staging/` with provenance, apply the 2026-08-24 triage rules (`AUTH-2` and the R-clauses as recorded in `cc_tasks/2026-08-24_source_triage_RESULT.md` and its decision log) and admit by rule where they apply; list the rest as staged-not-admitted with the clause that stopped them. Do not extract; extraction on these is a separate demand-pull decision.

## Constraints

Zero model calls (search APIs and fetches only). Do not touch the burn state, ledger, or event log beyond `manifest_add` events produced by rule-based admission. Do not edit the crosswalk skeleton or the assessment protocol.

## Completion

RESULT at `cc_tasks/2026-09-02_g1_eval_prior_art_RESULT.md` with the query log summary, counts (found / staged / admitted / excluded-by-clause), and the memo path. `seldon cc complete`; commit and push.
