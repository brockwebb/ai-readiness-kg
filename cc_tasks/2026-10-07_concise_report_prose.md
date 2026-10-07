# CC Task: the concise report, written as prose by a model from the frozen evidence map, every claim checked against it, under a prose gate

**Date:** 2026-10-07
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from DN-013 §3 (R5, R6), which amends DN-009 d1: the destination keeps the evidence map and this report, and drops the one-page summary and the four-to-six page brief as Desktop deliverables. The operator writes the summary himself from this report; nothing here drafts one.
**Implements:** DN-013-R5, DN-013-R6; DN-009 d2 (claims before prose).
**Framework layer served (DN-005 §5 rule 1):** §2.1 and §2.2; the report is a view of the framework and its measurement, and says so.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** 2026-10-07_seed_known_locations_verify
**Spend:** est. 2.5M tokens (Opus). One writing call and one checking call per section (about six sections), one transitions pass, the controls, one revision round, two fresh-reader calls.
**Network:** none beyond the model CLI and git push.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why this task exists
The deck and the brief pack were assembled under the rule that no sentence may appear that is not in a record file, and read as assertion, qualifier, assertion, qualifier, with nothing carrying one thought into the next. The operator rejected them on 2026-10-02. This report is written, then checked. The check is what keeps it true; the writing is what makes it readable.

## Decisions

1. **Inputs, and a stop condition.** Read `docs/evidence/FROZEN.md`. Run `scripts/build_evidence_map.py --check`; it must pass and every claim in `docs/evidence/claims.yaml` must cite the composite FROZEN.md names. If either fails, stop and report. The report may use: the claims file, DN-005 §1 and §2, the L0 report's methods sections, the scan catalog RESULT and the audit's limits. No number enters from anywhere but a claim.

2. **The argument, in this order.** (a) What the framework is for: whether the public, and the tools the public now uses, can reach, understand and use the data they paid for. (b) What was measured, on which 16 bodies, when, and how, under one named composite. (c) What was found, ordered by the strength of the evidence, not by a story chosen in advance; existence against discoverability (DN-013-R1) is the expected centre if the claims bear it out. (d) What the instrument cannot say: errors, candidate and frontier legs, hosts that refused this client, each as a finding about access where it is one. (e) What an agency can do, from the prescriptions and their sources, and what the framework measures next. Three to five pages, or what the argument needs; there is no page cap.

3. **Writing.** One call per section, given that section's claims with their evidence lines and the previous section's last paragraph. The register is technical and readable: each paragraph one thought, stated in its topic sentence; known information before new information in each sentence (Gopen and Swan, "The Science of Scientific Writing", American Scientist, 1990); a connective wherever the logic turns. Every sentence that states a fact ends with a marker `[c:<claim id>]`, stripped at build. Numbers appear only as their claims state them. One pass over the whole report then rewrites the joins between sections and adds no fact.

4. **The claim check.** A separate call per section sees only the section and its claims and labels every sentence `supported` (with claim ids), `unsupported`, or `no factual content`. Before it runs on the report, a control: one known-false sentence planted in each section; if the checker misses any, stop and report (the DCAT-003 ADDENDUM 01 item 5 precedent). An unsupported sentence is cut; if cutting it breaks the argument, it stays marked `[unsupported]` in the draft and is listed in the RESULT. It is never reworded to fit. Separately, code checks that every digit string in a sentence equals a value in the claims that sentence cites.

5. **The prose gate (DN-013-R6), by code, before the fresh reader.**
   - No U+2014, and no U+2013 used as a dash.
   - No word on the operator's list. DN-013-R6 cites "the operator's banned list", and no such file exists in this repository. Create `docs/style/operator_banned_words.yaml` with exactly these entries and their source line ("operator, stated preferences, recorded 2026-10-07"): `load-bearing` and `load bearing`; `hallucinate` and its forms (the operator's term is `confabulate`); `delve`; `testament`. Also flag any citation of Gartner. Wire `scripts/dcat_faq_lint.py` to read it, so the DCAT briefs get the same list.
   - The pattern DN-013-R6 names, measured this way: for adjacent sentences in a section, flag the pair when the second has at most 8 words, the first is at least twice its length, and the second either has no finite verb or opens with a qualifier (`Not`, `Only`, `Never`, `No`, `Just`, `Or`, `That is`). Use spaCy's tagger for finite verbs if it installs; otherwise name the tagger used. A section with more than two flagged pairs fails and goes back to its writer once.
   - Reported, not gated: sentence-length standard deviation and clauses per sentence per section; adjacent-sentence content-lemma overlap and connective rate, after Coh-Metrix (Graesser, McNamara, Louwerse and Cai, 2004) and TAACO (Crossley, Kyle and McNamara, 2016), naming the connective list used.
   - Repetition: every content 3-gram that occurs twice or more in the report, and every content lemma used more than five times in one section, listed as warnings. The list goes back to the writers with the gate failures in the one revision round; what survives is reported, not silenced.

6. **The fresh reader.** A subagent with no project context reads the built report alone and answers: what was measured, on whom; the main finding, in one sentence; one thing an agency could do, and the evidence for it. Its answers are compared with the claims; a section that produced a wrong answer goes back once. Both rounds are recorded verbatim.

7. **Build** into `reports/concise/`: `REPORT.md`, `REPORT.pdf`, `claims_trace.json` (each sentence with its claim ids and check label), `prose_gate.json`, `fresh_reader.json`, `run/` (every prompt and response). Plain language: no task codes, no repository paths, no pipeline vocabulary in REPORT.md (run `scripts/dcat_faq_lint.py` on it).

**Write set:** `reports/concise/`, `scripts/concise_report_*.py`, `docs/style/operator_banned_words.yaml`, `scripts/dcat_faq_lint.py` (reading the list only), tests for the gate measures, the RESULT. Byte-identical: `docs/evidence/claims.yaml`, `FROZEN.md`, every rule, matrix and stored payload, `scripts/score.py`, every report under `docs/reports/`.

**Immutable once written.**

## Gate and report
The gate tier `CLAUDE.md` prescribes for a task that touches no rule or scoring code, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-07_concise_report_prose_RESULT.md`, under 60 lines: page count; per section, sentences written, cut and marked unsupported; the control's catches; the prose gate per section, both rounds; the repetition warnings that survived; the fresh reader's answers, both rounds; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** FROZEN and --check → banned list → outline from claims → sections → joins → control → claim check → digit check → prose gate → one revision round → fresh reader → build → lint → gate → RESULT → push.
