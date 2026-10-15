# CC Task: the instrument specification: every public-tier check documented as a hypothesis with its expected behavior, its source, its test, and what its result does and does not claim

**Date:** 2026-10-15
**Project:** ai-readiness-kg
**Authored by:** Desktop session, on the operator's standard of 2026-10-15.
**Implements:** `docs/design/2026-10-12_DN-014_executive_summary_brief.md` (DN-014) as amended by DN-014 ADDENDUM 01; DN-001 (evidence floor); DN-005 (framework layers). This task writes DN-015 (the instrument specification) as its first part and commits it with receipts, then works under it.
**Framework layer served (DN-005 §5 rule 1):** §2.1, the measurement specification layer.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Model:** primary
**Spend:** est. 3M tokens. Opus 5.5 audits (role `primary`); Fable reads each check's entry (role `judge`); one round per check, a second only on a `no`.
**Parts:** A 0.15, B 0.55, C 0.15, D 0.15.
**Part map:** A is DN-015; B is the audit of the 18 checks; C is the record write-back; D is the verdict on page two.
**Network:** allowlist: www.rfc-editor.org, www.w3.org, schema.org, developers.google.com, resources.data.gov, project-open-data.cio.gov, www.sitemaps.org, llmstxt.org, datatracker.ietf.org

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## The operator's standard (verbatim intent; the rubric for every entry)

Every check is a hypothesis. For each one, in this order: (1) is it a valid question, that is, does the construct it measures matter to SI readiness, on published grounds; (2) what is the expected behavior, defined by the literature or a standard, not by this project; (3) what test is run, and why that test is the recognized way to measure that behavior; (4) the result, and what a pass or fail does and does not claim. A check with no published definition behind (2) is project-defined and is marked so. Nothing is asserted from a check whose entry is incomplete. "Correct", not "best known today".

## Step 0

If this task is `in_progress` from an earlier dispatch, stop. Confirm the served model equals `seldon models resolve primary`. The v3 grid stays as it is on disk and is not published anywhere; `reports/summary/SUMMARY.pdf` is not rebuilt by this task except as Part D says.

## Part A: DN-015, the instrument specification

Write `docs/design/2026-10-15_DN-015_instrument_specification.md`: the standard above as this project's rule for every check in the harness; the entry schema below; the states a check can hold (`specified`, `project_defined`, `invalid`, `retired`); the rule that page two of the summary shows only `specified` checks; and the four-state cell (pass, partial, fail, could not measure) with "could not measure" for any page that returned an access denial, an unconfirmable absence or a server error. Prior art as receipts (`seldon prior-art search`, then `verify`, PASS required before Part B): Messick's unified validity framework and construct validity; IEEE 829 test specification (purpose, pass criterion, basis per test); pre-registration of hypotheses and tests; survey codebooks. Commit the note path-scoped through the hooks.

Entry schema, one per check, in `assessment/instrument/<rule_id>.yaml` and rendered as one table in `reports/instrument/INSTRUMENT.md`:

- `question`: one sentence, the construct and why it matters to an SI client, with the corpus documents (by id) that establish it matters.
- `expected_behavior`: the behavior a ready publisher exhibits, with the standard or paper that defines it, cited by document id and section. If none exists, `source: none` and `state: project_defined`.
- `test`: what the harness actually does (client, request, what it reads, the decision rule), quoted from the rule's code, and why this is the recognized way to measure the behavior (the standard's own conformance clause, a published method, or the absence of one, stated).
- `claims`: what a pass asserts; what a fail asserts; what neither asserts. Written so that a reader who knows the agency cannot read the cell as a claim the test did not make (a fail on API advertisement is not a claim that no API exists).
- `confounds`: what else produces a fail (a firewall that refuses the client, a key wall, a server error) and how the harness distinguishes them, or that it does not.
- `state`: `specified` only when every field above has a published source where one is required.

## Part B: the audit, 18 checks

The 13 product-level public-tier checks on the v3 grid and the 5 site-level checks (including the two declarations, which get entries stating they are declarations). For each: fill the entry from the rule's code (`assessment/harness/scan/rules/`), the indicator it maps to and that indicator's evidence edges, the corpus, and the allowlisted standards hosts. Reuse the v2 RESULT's audit of the API discoverability rule (its branches, two of them project-invented) as the first entry. Where a branch of a rule has no published definition, the entry splits the rule: the published branches keep `specified`, the invented branch is `project_defined`, and the record carries both.

For the API advertisement check specifically, the entry must settle in writing: that a search engine can locate an API is not the behavior measured; that Google Dataset Search depends on schema.org Dataset and DCAT markup (cite Google's own documentation); that robots.txt is declared policy and a firewall refusal is enforcement, two different observations; and that the harness measures the data page, not API endpoints, so no cell says whether a script calling the API is refused.

Fable reads each entry with three questions: does the expected behavior come from the cited source and not from the writer; could a reader who knows the agency misread a fail as a claim the test did not make; is any term undefined. A `no` on the first sends the entry back once; a second `no` sets `state: invalid` with the reason.

- check: 18 entry files, each with every field; a script lists any missing field and exits non-zero if one is.
- check: every `expected_behavior.source` resolves to a corpus document id or a receipted standards URL; none to prose.
- judgment: Fable's reading per entry, one line each in the RESULT.

## Part C: the record

Through `scripts/framework_writeback.py`: `instrument_state` on each rule; `plain_name` rewritten from the entry's `claims` so the column name states only what a pass asserts, at most eight words; `fix_line` re-checked against the entry's expected behavior. Projection gate green.

## Part D: the verdict on page two

Write `reports/instrument/PAGE_TWO_VERDICT.md`: which checks are `specified` and may appear; which are `project_defined` or `invalid` and come off; how many of the 208 cells change state under the four-state rule (count the "could not measure" cells, and which agencies' rows they concentrate in). Do not rebuild `SUMMARY.pdf`. The rebuild is a follow-on task registered after the operator reads this verdict; the grid's credibility is his to judge.

- check: `seldon verify`; `make gate-task` (quote the counts); protected-paths diff empty except the authorized write-back.

## RESULT

Under 45 lines: DN-015's verdict and commit; a table of the 18 checks with their state and one phrase on why; Fable's lines; the "could not measure" counts; premises found wrong. `seldon cc complete`, commit, push. The operator reads `reports/instrument/INSTRUMENT.md` and `PAGE_TWO_VERDICT.md`.
