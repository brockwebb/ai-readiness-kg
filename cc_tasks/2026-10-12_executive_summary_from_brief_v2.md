# CC Task (v2): a two-page executive summary written from DN-014, by Opus 4.8 with Fable as the reader, every capability claim pointing to something that exists

**Date:** 2026-10-12
**Project:** ai-readiness-kg
**Authored by:** Desktop session, resuming `handoffs/2026-10-12_executive_summary_brief_dn014_stop_held.md`.
**Supersedes:** task 78971e58 (`cc_tasks/2026-10-12_executive_summary_from_brief.md`). Two premises in it were wrong: it read the brief from the workbench copy and planned to copy it in as its first commit, while the accepted brief is DN-014 in this repo; and it ran the session on `primary` (Opus 5.5), while DN-014 §9 names Opus 4.8 as author. Steps 1 to 5, the rules and the gate are carried over unchanged in substance.
**Implements:** DN-014 (the brief), DN-010 (decision support), DN-013-R5 and R6 (the concise report, as amended by DN-014), DN-001 (evidence floor).
**Framework layer served (DN-005 §5 rule 1):** §2.1, the summary as a view of the framework.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Model:** author
**Spend:** est. 2.5M tokens. Read it as 2 to 4x low. The session writes (role `author`, Opus 4.8 at effort high, seldon AD-035 ADDENDUM 02); Fable reads through the harness model call (role `judge`), at most three reading rounds.
**Network:** allowlist: www.rfc-editor.org, www.w3.org, resources.data.gov, project-open-data.cio.gov, llmstxt.org, www.sitemaps.org, schema.org

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Step 0

If this task is `in_progress`, stop. Confirm the session's served model is the `author` role's pin from seldon's lock (`seldon models resolve author`); a mismatch stops the task as `model_substituted` and writes nothing.

## Inputs, in order of authority

1. `docs/design/2026-10-12_DN-014_executive_summary_brief.md`, committed. Its words on purpose, definition, shape and cuts govern. Where anything below seems to conflict with it, DN-014 wins and the RESULT says so. The workbench copy is history, not input.
2. The frozen evidence: `docs/evidence/claims.yaml` and `docs/evidence/FROZEN.md` (`_composite_d`).
3. Prior art for authoring: Seldon's paper pipeline (`seldon/seldon/paper/`: `context`, `qc`, `glossary_check`, `copyedit`, `build`), used for the SFV paper and the two books. Use it where it fits a two-page document and say what you used; do not build a new authoring pipeline.

## Steps

1. **The discoverability headline, checked before anything is written about it.** Quote what `RULE-A13-v1` (`assessment/harness/scan/rules/rule_a13.py`) measures. For each of its branches, find a published definition (corpus first, including the admitted RFC 9727, DCAT and Project Open Data documents; then the allowlisted standards hosts: RFC 8288 web linking, DCAT `dcat:accessService`, schema.org `WebAPI`, sitemaps.org, the llms.txt proposal) or record it as project-invented. Decide the sentence the summary may use: one that claims no more than the rule measured. If a branch is invented and no published definition replaces it, the summary does not use the headline; record a vocabulary proposal in `ontology/vocabulary_proposals_epoch2.yaml` and stop there on that point.
2. **The definition enters the vocabulary.** Add "SI readiness" (short definition as in DN-014 §1, fuller definition as in its appendix line) to `ontology/vocabulary_proposals_epoch2.yaml` with each source it draws on, cited by corpus document id. Do not edit `ai_readiness_vocabulary.ttl` directly; follow how proposals become entries in this repo and say which state it reached.
3. **Every capability claim points to something real.** For each capability in DN-014 §3 (measure, map, standard scale and comparison, prescriptions ranked by effort and impact, the three measurement tiers, the queryable knowledge graph with cited answers, superseded evidence kept as history and kept out of advice, serving several roles), name the artifact that implements it: a design note, an MCP tool, a file, a test. A capability with no artifact is written as planned, or cut. The table goes in the RESULT.
4. **Write.** You write. The reader is Fable via the harness model call (role `judge`), in a fresh context, given only DN-014 and the draft. Fable answers four things each round: can the 30-second bullets in DN-014 §4 be said from page 1 alone; what on page 1 a CIO new to SI would not understand; what is said twice; what detail could be cut without loss. At most three rounds. Fable's rounds are editorial review, not a measurement, and are reported as such. If the harness refuses the reader call (`judge_uncalibrated` or any other named refusal), stop and report; do not route the read through another role. The planted-sentence check and the unsupported-sentence check from the concise report pipeline still run, as checks, not as content.
5. **Build.** `reports/summary/SUMMARY.md` and `SUMMARY.pdf`, the PDF rendered by the script that writes the Markdown (repo convention, `cc_tasks/2026-10-08_dcat_brief_pdfs_from_build.md` decision 3). Page 1 is the whole message. Page 2 is one summary table of results and at most one figure. Appendix pages after that: the fuller definition with sources, and the source list. The old `reports/concise/` stays as it is.

## Rules for the text

SI everywhere, never AI, except inside a published document's exact title. No process words (cycle, claim, leg, composite, harness, verdict, gate, pipeline). No indicator codes in the text. No counts in page-1 sentences except the 16 agencies; counts belong in the page-2 table. No section about how the summary was written. No em dashes. A point is made once.

## Gate

- check: pypdf page count of the body (pages 1 and 2) is exactly 2; quote the count.
- check: the text check, from a word list committed with it, returns zero process words, zero indicator codes, zero "AI" outside published titles, zero em dashes; quote its output.
- check: the unsupported-sentence check passes and every planted sentence is caught; every number traces to a claim or registered Result.
- judgment: Fable's last round says the 30-second bullets can be said from page 1 alone (a reader's judgment; no program decides it). Quote its answer.
- check: `make gate-task` (quote passed, skipped, xfailed, deselected, wall clock), `seldon verify`, the protected-paths diff.

## RESULT

Under 40 lines: served model and effort from the receipt; the discoverability decision and its sources; the definition's vocabulary state; the capability table; Fable's rounds in one line each; page counts; the text check; gates; premises found wrong. Then open nothing and write nothing else: the operator reads `reports/summary/SUMMARY.pdf`. `seldon cc complete`, commit, push.
