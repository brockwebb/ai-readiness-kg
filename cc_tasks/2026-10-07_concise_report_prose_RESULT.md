# RESULT: the concise report, written by a model from the frozen claims, every sentence checked, under the prose gate

**Task:** `cc_tasks/2026-10-07_concise_report_prose.md` (no addenda exist). **Ran to the end.** **Layer:** DN-005 §2.1 and §2.2. **Deliverable:** `reports/concise/` holds `REPORT.md`, `REPORT.pdf` (**5 pages**), `claims_trace.json`, `prose_gate.json`, `fresh_reader.json`, `build_report.json`, `report_config.yaml` (sections, claims per section, plants, gate and grading rules, fixed before the first call) and `run/` (checkpoint plus 34 raw prompt and response files). Code: `scripts/concise_report_{gate,run,build}.py`, `docs/style/operator_banned_words.yaml`, and `scripts/dcat_faq_lint.py`, which now reads that list (rules `banned_word` and `flagged_source`; no old rule removed; the DCAT files still give 0 findings). Tests: `tests/test_concise_report_{gate,run,shipped}.py`, 30 tests, including the §15 SIGKILL resume.

**Spend:** 34 calls, **1,662,808 tokens**, all `done`; the ledger run `concise_report_2026-10-11` (ceiling 3,500,000) settled the same total with 0 refusals. Writer `claude-opus-5-5` (6 writes, 6 revisions, 2 joins). Checker `claude-fable-5-1` (6 controls, 12 checks). Fresh reader `claude-sonnet-5-5` (2 reads). The pilot measured 46,372 tokens per call and projected 1,854,880 for the expected 40 calls. The task's estimate was 2.5M. The session's own context is unmetered and not counted.

## 1. Inputs (decision 1)
`build_evidence_map.py --check`: no drift. `claims.yaml` `cycle_of_record` is `scan_2026-10-07_composite_d`, the composite FROZEN.md names, and no claim's text names another cycle (`load_claims` checks both before any call). Claims used: section 1, 7; section 2, 6; section 3, 16; section 4, 7; section 5, 9; section 6, 24. Excluded, with reasons in the config: CL-083 (status `unsupported`), CL-084 (the order's term governs the operator's summary, DN-009 d4), and CL-099 to CL-114 (the DCAT brief's table).

## 2. Control, check and cuts (decision 4)
**Control: 6 of 6 plants caught**, each labelled `unsupported` for the right reason (for example "CL-035 states 177 pass, not 512").

| § | r1 written / cut (checker, digit) | r2 written / cut (checker, digit) | kept |
|---|---|---|---|
| 1 | 16 / 2 (0, 2) | 13 / 0 | 13 |
| 2 | 12 / 1 (1, 0) | 12 / 0 | 12 |
| 3 | 13 / 2 (1, 1) | 11 / 1 (1, 0) | 10 |
| 4 | 13 / 0 | 14 / 0 | 14 |
| 5 | 18 / 3 (3, 0) | 19 / 4 (1, 3) | 15 |
| 6 | 21 / 1 (1, 0) | 21 / 0 | 21 |

**0 sentences are marked `[unsupported]`:** every unsupported sentence was cut, and none was reworded. Round 1's digit cuts are numbers the writer took from evidence quotes rather than claim text (14,000 domains, 42%). Round 2's three digit cuts in §5 are cross-references ("as section 4 explained"), which the literal rule reads as numbers. §5 still reads as an argument without them, so nothing was kept marked.

## 3. Prose gate (decision 5): spaCy `en_core_web_sm` 3.8.0 (spaCy 3.8.14)
Flagged "statement, short clarification" pairs: **0 in every section in both rounds**. No dash and no banned word anywhere, so every section passed both rounds. All six went back once anyway, because each had a cut or a repetition warning. Reported measures, round 1 → round 2: the sentence-length SD ranges from 6.65–11.07 to 6.06–11.81, and finite verbs per sentence from 2.36–3.38 to 2.67–3.54. Adjacent content-lemma Jaccard ranges from 0.083–0.101 to 0.054–0.090. The share of sentences holding a connective goes from 0.818–1.0 to 0.923–1.0, measured with "concise_report connectives v1, after TAACO's categories". Per-section figures are in `prose_gate.json`.

**Repetition warnings that survived round 2.** Over-used lemmas: §3 `scanner` 6; §4 `check` 6; §5 `indicator` 8; §6 `fix` 7 and `indicator` 7. There are 17 repeated content 3-grams, each occurring twice. Fourteen fall in §4 and §5, which both restate the Census catalog case (`variable level semantic`, `read absence establish`, …), and three fall in §1 and §4 (`discovery access interpretation`, …).

## 4. Fresh reader (decision 6), verbatim in `fresh_reader.json`
Round 1 (graded right on q1, q2 and q3; no section went back):
- **q1:** "…one composite measurement cycle (scan_2026-10-07_composite_d)… a single identified, credential-free public scanner client produced 1,055 findings on 16 federal statistical bodies (13 of them ranked)…"
- **q2:** "The scanner was denied access on 341 of its 1,055 findings and met 415 absences against only 177 passes…"
- **q3:** "…carry a revision class on every changelog entry… at most 0.25 (a ceiling, not a predicted gain)… hours effort band at no cost."

Round 2, on the same body (graded right on all three):
- **q2:** "…341 of 1,055 findings were denials… 415 absences… only 177 findings passed…"
- **q3:** "…publish a machine-readable licence stated as an identifier… at most 0.125…"

Every number in the answers matches its claim (CL-050, CL-035, CL-115, CL-117).

## 5. Premises wrong (the task's, then mine)
1. **The claims do not bear out DN-013-R1's expected centre.** No claim in `claims.yaml` states existence against discoverability. Its headline (15 of 29 body × object pairs) lives only in `docs/research/2026-10-11_seeded_delta.md`, and the claims file is byte-identical here. The report's centre is therefore what the claims do state: 341 denials, 415 absences and 177 passes of 1,055, with denials, the most direct observation, first. The next evidence-map task should add the discoverability claims.
2. **"No sentence that is not in a record file" is gone, but the claims' own process words came through.** A supported sentence in §6 reads "is to be measured before the summary is drafted" (CL-002 and others), and the no-rewording rule keeps it.
3. **Decision 4 names no mechanism for "cutting it breaks the argument".** I applied cut-always. The rule is literal: it cut three harmless cross-references.
4. **q3's grading rule was weaker than its question.** It accepts the bound and the effort band as "evidence". Both answers give those, and neither names the failing finding behind the fix. §6 states each fix's bound, not the failure it fixes.
5. **What the reader read is not byte-for-byte REPORT.md.** After both reads, the build changed only the code-built source list: em dashes in two titles became colons, a path parenthetical was dropped, and URLs went into angle brackets, all so the lint passes. It also added the code-built note "How this report was written". The six sections are byte-identical to what both rounds read; I checked this against the raw prompts.
6. **Writes outside the stated set, each needed:** `pyproject.toml` declares `spacy==3.8.14` and the `en_core_web_sm` wheel, because `test_adopter_path` fails on an undeclared import. I also added `scripts/check_protected_concise_report_prose.sh`.

## 6. Verification
`make gate-fast` (the write set touches no scan, rule, scoring or record code): 3314 passed, 4 skipped, 41 xfailed, 30 deselected, 176 s, `EXIT=0` (`logs/2026-10-11_concise_gate_fast.log`; the deselected count is from `logs/2026-10-11_concise_gate_collect.log`). This is the fast tier, not a full suite. `seldon verify`: all checks passed, `EXIT=0` (`logs/2026-10-11_concise_seldon_verify.log`). Protected paths: PASS, `EXIT=0` (`logs/2026-10-11_concise_protected.log`). The run log is `logs/2026-10-11_concise_report_run.log` (`EXIT=0`), and progress went to `logs/2026-10-11_concise_report_progress.log`. Lint on REPORT.md: 0 findings.
