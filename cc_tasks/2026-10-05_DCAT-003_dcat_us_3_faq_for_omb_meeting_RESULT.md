# RESULT: DCAT-003: DCAT-US 3.0 FAQ built from both graphs, 14 questions answered, every kept sentence checked against its cited text

**Task:** `cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md` (no addendum exists). **Implements** DN-011-R5. **Ran to the end.** The operator hand-dispatched it in a Claude Code session on 2026-10-05 UTC, 13:21Z to 14:50Z, with `dispatch.enabled: true` (§7, item 1).

**Prerequisites checked on main first.**
- DCAT-001 is merged in `icsp_notebook`: v7.17 at `71a34b6`, its addendum v7.18 at `35c8caf`, both with delivery reports.
- DCAT-002 and its ADDENDUM_01 are committed here (`688451fb`, `a6d937d8`).

## 1. Delivery report

**Shipped**, all under `reports/dcat_us_3_faq/`:
- `FAQ.md` and `FAQ.pdf` (11 pages);
- `ATTACHMENT_evidence.md` and `ATTACHMENT_evidence.pdf` (landscape, 33 pages, including the element table for Q4 and Q6);
- `answers.json`, every kept and cut item with its verdict;
- `evidence/` (one file per question, the absence-check files, the element table and the catalog records);
- `run/` (the checkpoint and every raw prompt and response);
- `faq_config.yaml`.

**Questions answered: 14 of 14.** Each has at least one kept sentence. Q1 to Q13 keep three sentences each; Q14 keeps one, followed by the code-built list in §2.

**Questions with gaps: 13 of 14.** Every question except Q1 carries "Not found" items, 31 in all. Each item survived two checks: the check against its question's passages, and the absence check (§2).

**Claims cut, by question (final units):**

| Q | sentences kept | sentences cut | "not found" kept | "not found" cut | reasons for the cuts |
|---|---|---|---|---|---|
| 1 | 3 | 0 | 0 | 0 | |
| 2 | 3 | 0 | 2 | 0 | |
| 3 | 3 | 0 | 3 | 0 | |
| 4 | 3 | 0 | 2 | 1 | absence check failed: the Quality and Governance page does list per-property levels for other classes, e.g. a `data-service` property row |
| 5 | 3 | 0 | 2 | 0 | |
| 6 | 3 | 0 | 3 | 0 | |
| 7 | 3 | 0 | 2 | 0 | |
| 8 | 3 | 0 | 3 | 0 | |
| 9 | 3 | 0 | 3 | 0 | |
| 10 | 3 | 0 | 3 | 0 | |
| 11 | 3 | 0 | 3 | 0 | |
| 12 | 3 | 0 | 3 | 0 | |
| 13 | 3 | 0 | 1 | 2 | absence check failed twice: "This metadata will not be required until further guidance on the implementation of Title III of the Evidence Act is publ[ished]", and "Data.gov verifies only that catalog submissions include the DCAT-US v3.0 mandatory properties…" |
| 14 | 1 | 2 | 1 | 1 | both sentences flagged `boundary_imprecision`: "The biggest gap…" is a ranking no passage makes, and the second places the `publisher` difference between draft and published pages, where the passage places it between the two published captures. The "not found" item was cut by the absence check |
| **all** | **40** | **2** | **31** | **4** | 0 cut before the check (no sentence cited an id missing from its file) |

The first pass of Q3, Q5, Q6, Q10 and Q14 was superseded when the evidence was corrected (§3). Its cuts are in the checkpoint and do not count above. They were: Q5, one sentence cut because the quoted support was not located under whitespace-only matching; Q14, one sentence flagged.

**Spend.**

| | tokens |
|---|---|
| Estimate before the run: 28 calls, ceiling 2,700,000 (about 60K per call × 28 × 1.5; nothing measured yet) | 2,700,000 ceiling |
| Pilot, measured on Q1 | 53,561 per call → 1,499,708 projected for 28 calls |
| Re-projection after the absence check was added (42 calls) | 2,249,562 against a ceiling raised to 3,600,000 |
| **Actual, settled** (`kg.spend status`, run `dcat_us_3_faq_2026-10-05`) | **3,314,787** |
| … final units: 14 answer, 14 check, 13 absence | 2,605,238 (63,542 per call) |
| … one check retried after an unparseable response | 52,973 |
| … superseded: the first-template Q1 answer, and the first pass of Q3, Q5, Q6, Q10 and Q14 (answer and check) | 656,576 |
| Released unmeasured: the Q1 check I killed when I stopped the first run | 54,195 reserved, consumption unknown |

- The ceiling is the run's own declaration, raised from 2.7M to 3.6M with the derivation in `faq_config.yaml`.
- The day closed at 29,449,774 of the 55,000,000 daily cap.

## 2. Method, and the prior art it follows

- **Evidence by script, before any model call** (`scripts/dcat_faq_evidence.py`).
  - **Retrieval:** lexical retrieval over the question's named documents in both graphs:
    - fss-policy-kg: `Segment.text` and `Obligation.verbatim_span`;
    - ai-readiness-kg: node `grounding_span`, and for admitted web pages the converted page text the extraction read;
    - the framework record, for Q11.
  - **Ranking:** passages are ranked by the number of distinct question terms they contain, and duplicates are dropped.
  - **Caps:** at most 60 retrieved passages, 60,000 characters and 10 passages per document. Every evidence file records `matched` and `dropped_by_cap`.
  - **Computed table:** Q4, Q6 and Q7 get the element table, read by code from four texts:
    - the Dataset page captures of 2026-09-15 and 2026-08-21;
    - the FAIRness draft's 49 Dataset properties;
    - the v1.1 schema's Dataset fields.

    Each cell quotes the line it was read from.
- **Answer, check and absence check** (`scripts/dcat_faq_run.py`).
  - **Answer:** one call per question on `claude-opus-5`. The answer has at most 3 sentences of at most 35 words, each citing passage ids, plus "not known" statements.
  - **Check:** one call per question on `claude-opus-4-8`, a different model from the writer. The prompt is an overlay (`faq-claim-attribution`) of the adversarial-review baseline rubric v1.3.0: role, anti-anchoring, the verbatim grounding rule and the closed defect classes. Every verdict is stamped `rubric_version: v1.3.0`.
  - **What is kept is decided by code.** A sentence is kept only on `pass` with a `support_span` that `kg/extraction/grounding.is_grounded` finds in a passage the sentence cites. Everything else is cut and recorded, never reworded.
  - **Absence check:** one call per question with any "not known" statement left. Each statement is read against passages found by its own content words: stemmed, with the top 3 per document across the question's documents. It is kept only on `pass`.
  - **Question 14** is answered from the "not found" items kept on Q1 to Q13, plus the catalog records of documents known to exist and not held.
- **Build** (`scripts/dcat_faq_build.py`).
  - Kept text is printed verbatim. A test asserts every kept sentence appears verbatim and no cut sentence appears.
  - Citations are one per document, merging documents held in both graphs (`same_document` in the config, each pair with its ground).
  - PDFs are made by pandoc with the typst engine, the toolchain `build_report_pdf.py` pins.
  - For Q14 the FAQ prints the full "not found" list by question under the kept sentence, and quotes the two catalog records. This was assembled by code from checked material; the model wrote none of it.
- **Prior art.** The method follows established work:
  - attribution as AIS defines it (Rashkin et al. 2021, *Measuring Attribution in Natural Language Generation Models*);
  - per-claim support checking (FActScore, Min et al. 2023);
  - citation precision as in ALCE (Gao et al. 2023);
  - checkpoint and resume as in `scripts/run_definition_pairs.py` (`~/GitHub/CLAUDE.md` §15).

  Departures: the absence check, which these do not need because they score only positive claims, and cut-not-repair, which is the task's rule where RARR repairs.

## 3. Defects found during the run, and what each changed

Each was found by a test or by reading the output, and fixed before the shipped outcome.

1. **`_json_payload` read a JSON array of objects as its first object.**
   - Effect: every check would have failed to parse.
   - Caught by `test_a_flag_without_a_closed_class_is_malformed` before any paid call. It now takes whichever bracket opens first.
2. **The first pilot answer ran 60 to 80 words a sentence.**
   - I stopped the run after that one call and added a 35-word limit. "Each answer is short" (DN-011-R5) means the operator says it aloud.
   - Cost: the superseded answer (54,195) and the in-flight check I killed (54,195 reserved, released unmeasured).
3. **Catalog records misled.**
   - fss-policy-kg's "not admitted" records for the M-25-05 crosswalk, the B3.3 slides and the DSWG report went to the model as evidence. That produced a Q14 sentence saying the crosswalk "was assessed and not admitted", which is false for the collection: ai-readiness-kg admitted it.
   - Fix: records whose document either graph holds (matched by URL or title) are now excluded. Two remain, the sequencing plan and the NGAC slides.
4. **"Not known" statements were checked only against their question's capped passages.**
   - Q10's first pass kept "The sources do not state what M-25-05 itself requires for any metadata element". `m_25_05#s105` reads "This schema includes the following metadata elements, consistent with the requirements of the Act". This is the failure an uncapped absence search exists for.
   - Fix: the absence check added in §2. In the final run it cut 4 statements.
   - `metadata element` was also added to Q3's and Q10's terms.
5. **The span check used whitespace-only matching.**
   - Switched to `grounding.is_grounded`, the repo's one verbatim rule. The decision runs after the calls, so no paid unit changed.
6. **Citations.**
   - The same document was cited once per section and once per graph; M-25-05 appeared four times with two dates.
   - Markdown anchors broke typst, and table rows cited one of their four sources.
   - The element table overprinted its last rows: pandoc wraps a table in a typst figure that does not break across pages.
   - All are fixed in the builder.

## 4. Check by query

- **fss-policy-kg** was read from the local Neo4j database `fss-policy-kg`. It matches release v7.18: 116 documents; `w3c_dcat_3` 1,339 segments; `fairness_project_wiki_overview` 14.
- **ai-readiness-kg** was read from `seldon-ai-readiness-kg`, projected at 34,878 nodes by DCAT-002 ADDENDUM_01 with a green round-trip.
- Neither graph's MCP server was used. The task allows "their query code", and the local databases need no network.
- **Element-table invariants**, asserted by `tests/test_dcat_faq.py`:
  - the 2026-09-15 page has exactly four Mandatory elements (contactPoint, description, identifier, title);
  - `publisher` is Mandatory on 2026-08-21 and Recommended on 2026-09-15;
  - all 49 draft properties are read, `hasVersion` with no level stated;
  - v1.1 requires `bureauCode` "for United States Federal Government agencies".

## 5. Ship set and gate

- **Protected paths** (`scripts/check_protected_dcat_003.sh`): PASS, EXIT=0, run after the suite (`logs/2026-10-05_DCAT-003_protected.log`). The task changed nothing outside `reports/dcat_us_3_faq/`, its three scripts, its test, this check, the spend ledger and this RESULT.

## 6. Gate (logs under `logs/`, gitignored)

- **Full suite** (`make gate-full`, copied to `logs/2026-10-05_DCAT-003_gate_full_suite.log`): **2953 passed, 0 failed, 3 skipped, 0 deselected, 37 xfailed, EXIT=0**, 2382.97 s. The three skips:
  - `test_dispatch_config.py:373`: dirty tree and STOP file, expected mid-task;
  - `test_scan_harness.py:283` and `test_g1_preservation.py:337`: both standing.
- **`seldon verify`** (`logs/2026-10-05_DCAT-003_verify.log`): all checks passed, EXIT=0.
- **New tests:** `tests/test_dcat_faq.py`, 21 passed, 0 skipped. They cover:
  - element-table parsing;
  - the keep and cut rules;
  - the absence rule;
  - a SIGKILL mid-loop resume test that makes no repeated call and gives identical output (§15 item 8);
  - the shipped files: verbatim kept text, no cut text, no process vocabulary outside quotations, every cited passage quoted.
- **Paid run logs:**
  - `logs/2026-10-05_DCAT-003_faq_run.log` (first run, stopped at the template change);
  - `_faq_run2.log` (EXIT=0);
  - `_faq_run3.log` (EXIT=0, after the evidence fixes);
  - `_faq_progress.log` (36 progress lines).

## 7. Premises wrong, and findings outside the task

1. **Dispatch.**
   - The task file is not dispatchable: `**Model spend:**`, not `**Spend:**`, and no `**Framework layer served` header.
   - The operator hand-dispatched it while `dispatch.enabled: true`. I touched `.seldon/DISPATCH_STOP` at 13:21:40Z and removed it at close.
2. **"About 15 questions":** there are 14.
3. **Q10's example**, "BCP 47 in other accounts". The documents show the BCP 47 wording was the Overview page's own, corrected in May 2026 per its changelog. No passage either graph holds gives BCP 47 as current; the absence-checked item "what any secondary account says about the language code" stands. What the graphs do show is a live internal contradiction: the Overview's glossary says plain-English `accrualPeriodicity` values "cause validation failures", while its structural-changes table prefers them.
4. **Q5 and Q6 presuppose published FCSM or FAIRness recommendations.**
   - The project's findings and recommendations are in the sequencing plan, which went to OMB and was not published (B3.3 slide 6; both delivery reports).
   - Q6 therefore compares the published levels with the project's public draft, the "Draft specification for review" B3.3 slide 5 names as its Task 1. That is the only public statement of what the project proposed, element by element.
5. **The colleague's claim** that "the FCSM people who worked on it have left" is not in either graph and is not addressed.
6. **The two graphs disagree on the Implementation Guide's metadata.**
   - Issuer: ai-readiness-kg's ledger says GSA; fss-policy-kg says Federal CDO Council.
   - Date: 2026-09-09 versus 2026-08-21.
   - The PDF itself: cover "August 21, 2026", version history "1.1 Sept 9, 2026", Acknowledgments in the Federal CDO Council's voice. The FAQ cites it so.
   - Follow-on: correct ai-readiness-kg's authors field through its ledger, not by hand.
7. **The 2026-09-15 Dataset page does not list `inSeries`;** the 2026-08-21 capture lists it as Optional.
8. **Cosmetic:** the progress line's denominator counts only the current units, so with superseded units in the checkpoint it read "52/42". The checkpoint and `answers.json` are right.
9. **Retrieval is lexical and capped by design** (§2). The FAQ says so in its opening note and labels the gap lists "Not found". A "not found" item means two searches did not find it, not that no document says it.
