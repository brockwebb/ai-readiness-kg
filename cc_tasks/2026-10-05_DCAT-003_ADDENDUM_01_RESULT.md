# RESULT: DCAT-003 ADDENDUM 01: the FAQ made shippable: live pages admitted as dated versions, Q9, Q12 and Q13 re-run under a controlled responsiveness check, Q14 built by code, and a lint that fails the build

**Task:** `cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md`, amending `cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md` (commit 1a5e6cc). **Implements** DN-011-R5. **Ran to the end.** The operator hand-dispatched it in a Claude Code session on 2026-10-05 UTC, 18:40Z to about 23:00Z, while `dispatch.enabled: true` (§7, item 1).

## 1. Delivery report

### 1.1 Live-page tier differences (first, as step 8 asks)

**There are none.** The DCAT-US 3.0 Dataset page as served on 2026-10-05 (sha256 `3b5cbb2d…`) gives every one of its 62 per-property sections the same requirement level as the 2026-09-15 capture:
- Mandatory: contactPoint, description, identifier and title;
- publisher: Recommended.

The FAQ says so in one sentence, computed from the table. The attachment's table now carries a fifth column, "as served 5 Oct 2026".

**What did change is the Overview,** in the rewrite its changelog dates "September 2026". Against the 2026-08-21 capture the FAQ's earlier answers quote:
- **Tables removed:** the "Breaking changes", "Fields replaced or removed" and "Structural changes" tables are gone from "Changes from v1.1".
- **Q10 is affected.** Its second sentence ("The Overview disagrees with itself on accrualPeriodicity…") quotes the structural-changes row (live coverage 0.0) and a glossary entry (0.062). The FAQ now says after it: "Quoted from the Overview as captured 21 August 2026; the page as served 5 October 2026 does not contain this text."
- **The glossary half is uncertain.** The site loads its glossary through `glossary.js` from a separate resource, and the raw HTML carries none of it. So the live page's glossary may still carry the "plain English … cause validation failures" sentence. The fetch cannot say. The attachment's preface says the glossary is loaded separately.
- **If asked "what is it now":** the structural-changes table that preferred plain-language codes is no longer on the page.

### 1.2 Sentences cut per re-run question

| Q | kept | cut, unsupported | cut, non-responsive | "not found" kept | "not found" cut |
|---|---|---|---|---|---|
| 9 | 3 | 0 | 0 | 3 | 1: "any DCAT-US 3.0 field for units of measure". The absence passages hold QualityMeasurement's `unitMeasure` (A53). |
| 12 | 2 | 0 | 1: "the schema was developed collaboratively by the Federal Chief Data Officers Council, the Federal Committee on Statistical Methodology, and the Data.gov team". Supported, but "background not asked by the statistical-equivalent question". | 3 | 0 |
| 13 | 3 | 0 | 0 | 4 | 0 |

**Q13 now covers each named option (rule 2):**
- **A statistical application profile:** a sentence (StatDCAT-AP as the EU's extension) and a "not found" item (no US profile exists or is planned).
- **Raising requirement levels through guidance:** a sentence (the Implementation Guide says the tiger team elevated outstanding recommendations to OMB and the CDO Council "for potential incorporation into future updates") and a "not found" item (that levels can be raised through guidance).
- **Conformance checking:** a sentence (the Overview as served 2026-10-05: a valid JSON Schema 2020-12, with data.gov's online validator).

**Rule 1 (draft statements):** Q9 and Q12 now say "the 2025 Candidate Recommendation says…". Each also carries a "not found" item that the published schema carries it.

**Not used:** Q3's M-25-05 one-year schema-update rule is not repeated in Q13. The three-sentence limit went to one sentence per option.

**No sentence of Q1 to Q8, Q10 or Q11 was re-asked.** Their v1 units are found by the v1 template hashes, and `--assemble` reproduces them identically: this was checked against the 1a5e6cc answers before any call.

### 1.3 Spend

| | tokens |
|---|---|
| Estimate before any call (`faq_config.yaml` `rerun`): 3 answers at 65,000, 3 checks at 90,000, 1 control at 65,000 | 530,000 |
| Declared ceiling, run `dcat_us_3_faq_addendum01_2026-10-05` (1.5 × the estimate) | 800,000 |
| Pilot: the r2 control call, measured; projected for the 6 further calls | 55,239; 331,434 |
| **Actual, settled** (`kg.spend status`) | **625,274** |
| … control r1 (failed, §3) | 53,890 |
| … control r2 (passed) | 55,239 |
| … Q9 answer + check | 57,715 + 179,555 |
| … Q12 answer + check | 52,413 + 75,754 |
| … Q13 answer + check | 53,916 + 96,792 |

**Calls:**
- **Answer and check calls:** 3 answer and 3 validator calls, the task's limit.
- **Controls:** 2 control calls, under "plus the controls in item 5".
- **Retries:** none, because `rerun.max_attempts` is 1.
- **Absence check:** folded into the one validator call (§2), so the "three validator calls" limit held. That is why Q9's check is the largest: 179,555 tokens, with up to 80,000 characters of absence passages beside the question's own.
- **The day:** 30,075,048 of the 55,000,000 daily band was committed when this run settled.

## 2. What was built, step by step

1. **Q14 by code** (`dcat_faq_build.gap_rows`, `gaps_section`; `built_by_code: true`, no call).
   - **Part A:** a table of 28 rows, deduplicated from 33 kept "not found" items. Four groups are declared in `faq_config.yaml` `gap_groups`, each with its reason:
     - the sequencing plan's recommendations, 5 and 6;
     - why draft levels are not the published ones, 6 and 7;
     - dimension vocabulary in the published schema, 9 and 12 (three items);
     - a US statistical profile, 12 and 13.
   - **Document column:** the sequencing plan answers four items (both Q5 items, and Q6's "what the plan recommended" and "whether the newly Recommended elements came from an earlier recommendation"). Every other row reads "None known", because no catalog record names a document for it.
   - **Part B:** the two documents not used, with title, issuer and date read from each catalog record, and the addendum's own reason sentence.
   - **Removed:** the model's prose paragraph and the per-question re-listing.
   - **Stale config fails loud:** a config entry that matches no kept item, or several, stops the build.
2. **"Not found in the sources:"** with bare clauses (`bare()`, which strips only "The sources do not state|show|…").
3. **Em dashes.** None remain in either file or either PDF (checked on extracted PDF text).
   - **Titles** use the issuer's punctuation, set as `same_document` overrides with the source of each:
     - M-25-05 from its SUBJECT line (`m_25_05#s3`–`s4`): "…Act of 2018: Open Government Data Access and Management Guidance";
     - FCSM 25-03 from its title page: "AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality".
   - **Q7** gets the one deterministic substitution (pair to commas), recorded in `build_report.json`.
   - **Quoted source text** shows U+2014 as a spaced hyphen, and the preface says so.
   - **Two PDF findings:**
     - pandoc's `smart` extension turned a quoted `---|---` table rule into an em dash, so it is now off;
     - typst also prints a literal `---` as an em dash, so a run of hyphens in quoted page text (a converted table rule) is shown as one hyphen.
4. **Currency.**
   - **Admission:** both live pages were fetched through `scripts/fetch_allowlisted.py` (resources.data.gov only, §8) and admitted by `scripts/admit_dcat_us_3_live_2026_10_05.py` as `dcat-us-3-dataset-schema-2026-10-05` and `dcat-us-3-overview-2026-10-05`, in epoch `dcat-us-3-live-2026-10-05`. They are converted and projected, and not extracted, because `extract: off` and no spend was declared for it.
   - **Version notes:** the build adds a parenthetical after each sentence that needs one, eight in all, listed in `build_report.json`:
     - after a sentence that states a requirement level and names no date (Q7 S2, Q8 S1, Q11 S3): each named element's level in all three page versions;
     - after a sentence that quotes a superseded capture: whether the page as served on 2026-10-05 still carries the text, by word 5-gram coverage.
   - **Coverage thresholds** (`PRESENT_AT` 0.75, `ABSENT_AT` 0.25) sit in a gap measured on the shipped passages: 0.818 to 1.0 where the text survives with different markup, and 0.0 or 0.062 where it is gone. No passage fell between.
   - **Q11's publisher clause** now reads, after it: "Level by version, publisher: Mandatory on the Dataset page captured 21 August 2026, Recommended on the 15 September 2026 capture and as served 5 October 2026."
5. **Re-run of Q9, Q12 and Q13** under v2 templates (`ANSWER_TEMPLATE_V2`, `CHECK_TEMPLATE_V2`). Both are derived from v1, and v1 is unchanged and still hashes to DCAT-003's units (a test asserts it).
   - **Answer rules added:**
     - a draft statement says it is a draft and whether the published schema carries it;
     - a stated tier names its version;
     - no em dash;
     - each sentence answers the question;
     - each named option gets a sentence or a "not found" item.
   - **The check** asks the responsiveness question per sentence, and a "no" is cut.
   - **The absence check** is folded into the same call: the "not known" items are read against the question's passages and against passages found by their own words (ids `A…`, `evidence/Q<n>_absence_v2.json`, beside the v1 absence files rather than over them).
   - **Q13's evidence** is widened as asked. It now holds M-25-05's "within one year" sentence, the Implementation Guide's schema-change and "recommendations that reached sufficient consensus" passages, and the FAIRness Project's post-release governance.
6. **Q11's framework citation:** "The presenter's own draft AI-readiness framework for federal statistical publishers (unpublished; the indicator's text is quoted in the attachment). Indicator G4." The build checks the quoted text against the record's current `ind:G4` text and would cut the sentence on a mismatch. It matches.
7. **The lint** (`scripts/dcat_faq_lint.py`) runs on both texts before either file is written. It carries the defect report and its date in its docstring.
   - **Positive control:** it fails FAQ.md at 1a5e6cc with 39 findings (em_dash, repository_path, file_extension, pipeline_word) and passes on both rebuilt files. Both are tests.
   - **Legal by rule:** a markdown link whose target is a URL counts as the URL. Otherwise the Overview's own "[jsonschema/README.md](https://github.com/…)" in a quote would trip the extension rule.

**Prior art.**
- **Dated versions:** RFC 7089 (Memento) and ISO 28500 (WARC), DD-068.
- **Responsiveness:** SAFE's relevance step (Wei et al. 2024, *Long-form factuality in large language models*) and RAGAS answer relevance (Es et al. 2023).
- **Attribution, as before:** AIS (Rashkin et al. 2021), FActScore (Min et al. 2023), ALCE (Gao et al. 2023).
- **Controls:** methodology §7.5 and §7.6.
- **Checkpoint plan (§15).** The plan was in `faq_config.yaml` `rerun` before the first call:
  - unit: one call;
  - key: sha1(kind | question | input hash | model | template hash);
  - checkpoint: `reports/dcat_us_3_faq/run/checkpoint.jsonl`, appended and fsynced, with raws under `run/raw/`;
  - resume: re-run `--rerun`;
  - pilot: the control call;
  - ceilings: 800,000 tokens and 7,200 s;
  - failures: rows, with no retry, so a failed call stops the run.

## 3. The positive control failed once, and what changed

**The first control (r1, check template `8efb45bc…`, unit `0973f64820b65388`) failed:**
- The validator passed the planted StatDCAT-AP agent-roles sentence and judged it responsive ("supports a future extension…").
- The run stopped as designed (`logs/2026-10-05_DCAT-003a_faq_rerun.log`, EXIT=3). No v2 verdict was used, and no question was asked.

**Diagnosis:**
- r1 asked "does this sentence bear on what the question asks". A sentence about StatDCAT-AP shares a field ("application profile", "extension") with Q13's first option.
- The field's fix is relevance to the question's subject, as SAFE's relevance step judges it and as RAGAS answer relevance penalises a topical answer that does not address the question.
- **r2** (`3d13e214…`) asks the validator to name the subject the question asks about. It counts a sentence responsive only if it says something the question asks for about that subject, or about a named option as applied to it.

**r2 has no example fitted to the plant.** To guard against fitting, its control added a held-out plant: a true background sentence about what DCAT-US 3.0 is, which does not answer "options for next steps".

**r2's control passed on all three** (unit `dcfdd8601dc80360`, `control/control_result.json`):
- the plant cut non-responsive;
- the held-out cut non-responsive;
- the responsive sentence kept.

The r1 failure stays in the checkpoint and `run/raw/`, and the revision history is in `dcat_faq_run.py` beside `RESPONSIVE`.

**This was in scope as the instrument loop, not a moved threshold.** The addendum gates the validator's verdicts on the control ("must cut the first and keep the second before its verdicts are used"). Fixing the instrument and re-running the control is that loop. No finding's threshold moved, and nothing judged under r1 was kept.

## 4. Check by query

- **Projection:** `scripts/build_projection.py`, EXIT=0, `evidenced_by_missing_document` 0, 282 documents (`logs/2026-10-05_DCAT-003a_projection.log`). The framework round-trip test is inside the full suite.
- **Element table:** asserted by `test_the_live_column_is_read_from_the_2026_10_05_page`.
  - The new column's Mandatory set is exactly the four.
  - Every row's evidence text still quotes four versions.
  - The frozen Q4, Q6, Q7 and Q10 evidence files reproduce byte for byte from the five-version table (checked: 0 mismatches over 73, 73, 22 and 22 rows).
- **Corpus:** 278 → 280 admitted. `kg.manifest verify`: clean, EXIT=0.

## 5. Ripple, by generator, none by hand (`logs/2026-10-05_DCAT-003a_regenerate.log`, each rc=0)

- **Generators run:** `build_l0_report.py`, `build_brief_pack.py`, `build_l0_site.py`, `build_evidence_map.py`, `build_figures.py`, `build_report_pdf.py`, `build_scan_catalog.py`, `mcp/airkg_doc.py`, `run_kg_questions.py`, `run_definition_pairs.py --render`. That is DCAT-002 ADDENDUM 01's list, each confirmed zero-spend first.
- **What moved:**
  - the corpus count;
  - the KG-questions epoch (the stale-epoch skip in `test_kg_questions.py:115` is gone);
  - `docs/brief/C_provenance.md`, `docs/data/`, `docs/evidence/` and `fig2`.
- **What did not move:** the L0 report markdown and PDF.
- **Checks:** `run_definition_pairs.py --check` gives 158 pairs, both controls pass, drift `[]`.
- **The fast tier before the ripple failed 7 drift guards** (`logs/2026-10-05_DCAT-003a_gate_fast.log`), all from the corpus count, and the regeneration cleared them.

## 6. Gate (logs under `logs/`, gitignored)

- **Full suite** (`logs/2026-10-05_DCAT-003a_gate_full_suite.log`): **2985 passed, 0 failed, 3 skipped, 0 deselected, 37 xfailed, EXIT=0**, 2379.78 s. The three skips:
  - `test_dispatch_config.py:373`: dirty tree and the STOP file, expected mid-task;
  - `test_scan_harness.py:283` and `test_g1_preservation.py:337`: both standing.
- **`seldon verify`** (`logs/2026-10-05_DCAT-003a_verify.log`): all checks passed, EXIT=0.
- **Protected paths** (`scripts/check_protected_dcat_003a.sh`, `logs/2026-10-05_DCAT-003a_protected.log`): PASS, EXIT=0, re-run after the suite.
- **New and changed tests:**
  - `tests/test_dcat_faq.py`, 44 passed (21 → 44). They cover:
    - the v1 template hashes;
    - the v2 rules;
    - responsiveness parsing and cutting;
    - absence ids;
    - lint rules and its control;
    - Q14's table;
    - version naming;
    - the live column;
    - the shipped files.
  - `tests/test_manifest.py`, 41 passed, of which 8 are new (DD-068). The 8 new ones fail against HEAD's `kg/manifest.py` and pass on the change (checked).
- **Paid runs:**
  - `logs/2026-10-05_DCAT-003a_faq_rerun.log` (r1 control FAIL, EXIT=3);
  - `_faq_rerun2.log` (EXIT=0).
- **After the suite started,** the build was re-run once to de-duplicate an entry in `build_report.json`. FAQ.md was byte-identical and the PDFs were re-rendered.

## 7. Premises wrong, and findings outside the task

1. **Dispatch.**
   - The addendum is not dispatchable: `**Model spend:**`, not `**Spend:**`, and no `**Framework layer served` header. Its `**Network:**` is prose, not `allowlist: …`.
   - It was hand-dispatched while `dispatch.enabled: true`. I touched `.seldon/DISPATCH_STOP` at 18:40:12Z (the dispatcher logged `dispatch_observed_stop`) and removed it at close.
   - The network allowlist I used was `resources.data.gov`, the only host step 4 names.
2. **"Fetch … as a new dated version" had no path through the gate.** `manifest.add` refuses a second document with a held URL, and DCAT-002 had recorded "no policy for holding several versions of one URL". DD-068 is that policy, kept narrow:
   - `version_of` plus `retrieved_at`;
   - one lineage per URL;
   - the content-hash dedupe never waived.
3. **The addendum budgets "three validator calls", but DCAT-003's method makes two validator calls per question** (check and absence check). Folding the absence check into the one call kept the budget. The opening note no longer says "checked twice", which would be untrue for the re-run questions. It says what holds for all questions.
4. **Step 4's "every sentence in FAQ.md that states a tier names the version" could not be met by rewording** the non-re-run sentences (cut, never reword). It is met by computed notes and a test, `test_every_tier_sentence_in_the_faq_names_a_version_or_carries_a_note`.
5. **The Overview rewrite (§1.1) touches more than tiers.** Q10's accrualPeriodicity sentence is the one passage the live page no longer carries. Every other passage the answers quote from a superseded capture is still on the page (coverage ≥ 0.818).
6. **The rejected "units of measure" item (Q9)** shows the folded absence check working: the same search found QualityMeasurement's `unitMeasure`. That field measures a quality metric's unit, not the data's. The FAQ simply carries no units item now. The distinction DCAT-003's Q9 drew ("as distinct from the Optional unitMeasure on QualityMeasurement") was lost with the re-run.
7. **Progress denominator** (cosmetic, carried from DCAT-003 §7 item 8): it still counts superseded units in the checkpoint ("60/37").
8. **The graph's view of the Implementation Guide's issuer** (DCAT-003 §7 item 6) is unchanged here and still open.

## 8. Fetch log, whole (`logs/2026-10-05_DCAT-003a_fetch.jsonl`, 3 lines: time UTC, event, status, bytes, sha256[:12], URL)
```
18:41:27 request 200 22 212cf4d230aa https://resources.data.gov/robots.txt
18:41:28 request 200 106817 3b5cbb2dc8af https://resources.data.gov/standards/catalog/dcat-us-3/dataset/
18:41:28 request 200 47227 f95692f885a4 https://resources.data.gov/resources/dcat-us3/
```
