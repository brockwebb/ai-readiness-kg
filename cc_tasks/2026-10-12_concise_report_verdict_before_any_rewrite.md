# CC Task: a verdict on the concise report against what it was for, before any rewrite is spent

**Date:** 2026-10-12
**Project:** ai-readiness-kg
**Authored by:** Desktop session, at the operator's direction (2026-10-11 22:54): he will not read the report; an independent pass decides whether it does its job and what is wrong, and a rewrite is spent only after he sees this verdict.
**Implements:** DN-013-R5, DN-013-R6 (the concise report's purpose); DN-001 (evidence floor).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the report as a view of the framework.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Model:** judge
**Spend:** est. 0.6M tokens. Read it as 2 to 4x low. One reading pass by this session; no harness model call; no rewriting.
**Network:** allowlist: www.darpa.mil, www.rfc-editor.org, www.w3.org, resources.data.gov, project-open-data.cio.gov, llmstxt.org, www.sitemaps.org, schema.org

**HEADLESS NOTICE.** No next turn. This task writes a verdict and stops. It writes no report text and edits no view.

## What the report was for (the operator's words, recorded; verify against the sources named)

- DN-013-R5/R6 and the operator's 2026-10-06 ruling: a concise report, three to five pages, smooth prose; he distills his own summary from it.
- 2026-09-21 and 2026-10-02 (`/Users/brock/GitHub/ai-readiness-kg/docs/design/` notes of those dates; find them): it must show the delta against the USAFacts AI data readiness framework (what was kept, changed, added, implemented); what the tests are, what they show and why they matter; how to use the tool on a website; provenance to research and federal documents.
- 2026-10-11, verbatim in substance: it is an executive explainer, essentially the Heilmeier questions; a reader must be able to tell the USAFacts authors what was done with their framework; the main points should be sayable to an audience in 30 seconds as a few plain bullets; no restating a point three or four times, no detail that is not useful, no pipeline or process vocabulary, no throat-clearing.

## Decisions

1. **The Heilmeier questions from their source.** Fetch the Heilmeier Catechism from www.darpa.mil and use its questions verbatim as the checklist. For each: answered, partly, or not; where (section and page); and in how many words. A question the report does not answer is named, not excused.
2. **The USAFacts test.** Could a reader, from this report alone, tell the USAFacts authors what was kept, changed and added from their framework, and why? Quote the passage that does it, or say none does.
3. **The 30-second test.** Write the bullets a presenter could say in 30 seconds *from what the report actually says*. If they cannot be written from the report, that is the finding.
4. **Bloat and drift, counted.** List: points made more than once (with locations); passages a reader could delete without loss; process or pipeline vocabulary; hedges and stock phrases. Counts and locations, not rewrites.
5. **The discoverability claim, checked against prior art before anything else is said about it.**
   - Quote how the report states it, and quote what `RULE-A13-v1` (`assessment/harness/scan/rules/rule_a13.py`) actually measures.
   - Search the corpus first (`corpus/`, the vocabulary, the admitted RFC 9727 and the DCAT and POD documents), then the allowlisted standards hosts. The question is whether a published definition exists for "a machine client can discover an API, terms, changelog or inventory from a page", in RFC 8288 web linking, RFC 9727, DCAT `dcat:accessService` and `dcat:DataService`, Project Open Data, schema.org `WebAPI`, sitemaps.org, or the llms.txt proposal.
   - Report, for each branch of the rule: cited source, or none (project-invented).
   - Judge whether the report's wording claims more than the rule measures (for example "a machine cannot find it" against "not linked from the scanned product page"), with the Census rows of `docs/research/2026-10-11_seeded_delta.md` as the worked example.
   - If a definition is invented, recommend the cited definition that should replace it, or state that none exists, which makes ours a proposal needing its own design note and vocabulary entry. Do not write that note here.
6. **Questions for outside checking, only where needed.** List the claims whose truth depends on facts outside the frozen evidence and corpus. For each, one plain question the operator could paste into a search engine. Say whether any claim needs an adversarial check by a different model family and why; "none needed" is an acceptable answer, and the default.
7. **The verdict.** One of: ship as is; fix specific defects (list them, at most ten); or rewrite (say why a fix is not enough). Plus the cost-free next step, if there is one.

**Write set:** `reports/concise/VERDICT_2026-10-12.md`, the RESULT, fetch logs. Nothing else. Every view, claim, rule and record is byte-identical.

## Output shape

`VERDICT_2026-10-12.md`: the verdict and the 30-second bullets on the first page, under 400 words. Then, as appendices, the Heilmeier table, the USAFacts finding, the bloat counts, the discoverability check with its sources, the outside-check questions. Plain prose and tables; no process vocabulary.

## Gate

`make gate-fast` (nothing in the code changed, so it must be green as found). `seldon verify`. A protected-paths check that only the write set changed.

## RESULT

Under 30 lines: the verdict, the served model and effort from the receipt, sources fetched, premises wrong. `seldon cc complete`, commit, push. Then the operator reads `VERDICT_2026-10-12.md`; no rewrite task is authored until he has.
