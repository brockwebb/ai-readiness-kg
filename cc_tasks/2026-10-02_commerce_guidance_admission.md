# CC Task: admit Commerce's "Generative AI and Open Data" guidance into this corpus, and reconcile this corpus against the FSS policy graph

**Date:** 2026-10-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from a lookup the operator ordered on 2026-10-02. Facts established by that lookup: (1) the FSS policy graph (`fss-policy-kg`) holds Commerce's January 2025 guidance as document `doc_genai_open_data_2025`, and its glossary line sits in Segment `doc_genai_open_data_2025#s583`: "AI-ready data 80 : Data that is not just machine-readable, but machine-understandable; data that is enriched with contextual metadata and organized in interpretable standard formats for utilization by AI systems." (2) That graph's `get_definitions` returns zero rows for "AI-ready": the glossary entry was never promoted to a Definition node, so a definitional lookup misses a definition that a text search finds. (3) This corpus (`seldon-ai-readiness-kg`, projection gate green) answers a definitional lookup for "AI-ready data" with seven Definitions (NOAA NAO 216-128, the scientific-AI data-readiness paper, the UK AI-ready data action plan, a World Bank blog, and noise from a vendor document) and NONE from Commerce: the guidance is not in the manifest. Only the related RFI (`doc-rfi-ai-open-gov-data-2024`) is. The 2026-10-02 prior-art task (PA8, `CL-085`) recorded the Commerce half as unsupported because commerce.gov returned 403 to the harness; its premise was incomplete because the task text told it to check the FSS graph for PA2 and not for PA8. That omission is this author's.
**Implements:** DN-009 decision 8 (the corpus is searched first; a corpus that lacks the most relevant federal document is a defect in the corpus).
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-02_kg_research_questions.md`
**Spend:** est. 5M tokens (Opus). One document extracted through the standing runner with `--ceiling-tokens` declared at 3M; the rest is queries and a script.
**Network:** none beyond `git push`. Every byte of the document comes from the FSS repository's stored copy on this machine; commerce.gov is not contacted.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Locate the stored copy.** Find `doc_genai_open_data_2025`'s source file and ledger entry in the `fss-policy-kg` working copy next to this repo (its evidence ledger and `corpus/`). Record the path, the `primary_url`, the sha256 the ledger holds and the sha256 you compute; they must be equal or the task stops and reports. Read, do not modify, anything in that repo.

2. **Admit it through the manifest gate (DD-003).** `python -m kg.manifest add` with provenance from the FSS ledger: `--url` the document's primary URL, `--rationale` naming this task and DN-009 d8, `--discovered-via` `fss-policy-kg ledger`, and an `acquisition_method` / `acquired_by` of `local_copy_from_fss_policy_kg` and this task (the standing rule that acquisition goes through `fetch_allowlisted.py` exists to give one fetch log; a copy of a stored file has no fetch, and the RESULT says so in one sentence). New corpus epoch `commerce-guidance-2026-10-02`. The existing epochs are not touched.

3. **Extract it with the standing pipeline, once.** `scripts/run_bulk_extraction.py --only <doc_id> --ceiling-tokens 3000000` under the same profile the v038 burn used, headless, polled to its EXIT line. No retuning of anything. The grounding gate stays absolute zero.

4. **Test the point of it.** Query this graph for the glossary definition ("machine-understandable" and "AI-ready data" and "Commerce"). The task passes only if a Definition node exists whose grounding span is the glossary sentence, with `doc_id`, section or segment locator and span id. If the extraction did not produce it, say so and why (a quarantine row, a chunk that missed it, the footnote marker 80 breaking the span) and do not hand-write a Definition; the follow-on is a task.

5. **Reconcile the two corpora.** From the FSS graph (its MCP or Cypher, read-only) list every document it holds; match each against this manifest by `primary_url`, then content hash, then normalised title. Emit `docs/research/2026-10-02_fss_vs_airkg_corpus_reconciliation.md` and a CSV: documents in FSS and not here, each with title, source type and a screen under the existing triage rules (AUTH-2, `docs/research/2026-08-24_*` decision log) as `include_candidate`, `excluded_by_rule` (with the clause) or `off_topic`. Admit nothing beyond decision 2; the candidate list goes to the operator. Also list this-corpus-only documents in one line of counts.

6. **Definitional-lookup audit of both graphs.** For the five phrases "AI-ready data", "AI-readiness", "data readiness", "machine-readable", "fitness for use", run the definition-layer verb and a text search in each graph and tabulate hits by label (Definition versus Segment). Report where a definition appears in text and not in the Definition layer. This is a finding about the FSS graph (and, if any, about this one); fix neither.

7. **Ripple, handled by the generator.** Admission moves `264` to `265`. Run `scripts/build_evidence_map.py` and let it regenerate the record entries it owns; report the exact diff in the RESULT (expected: the corpus count in `CL-044` and any entry derived from it). Then update the prior-art entry `CL-085` (PA8): if decision 4 passed, status `prior_art`, evidence kind `document` with the corpus doc id and locator and the glossary sentence as quoted text, and the existing NOAA and BEA/FCSM entries kept as comparators, the note stating that the Commerce text is the Department's guidance glossary (its Working Group's document), not a Department-wide regulation. Re-run `scripts/run_kg_questions.py` (from `2026-10-02_kg_research_questions.md`), regenerate its stored answers, and quote in the RESULT the change in Q1 (definitions of AI readiness) and any change in Q2, Q3 and Q5.

8. **Reader gate (DN-009 d7).** A fresh subagent given only the reconciliation markdown and the new Q1 answers writes five sentences on what definitions of AI-ready data the federal documents give and where this corpus differs from the FSS graph. Quote in the RESULT.

**Write set:** `corpus/` (the admitted document per the existing layout, gitignored binaries stay ignored), `events/` (the next shard, per DD-008), `corpus/manifest.json` and the dixie ledger entry as the pipeline writes them, `docs/research/2026-10-02_fss_vs_airkg_corpus_reconciliation.md` and its CSV, `docs/evidence/claims.yaml` (only entries the generator owns, plus `CL-085`), `docs/evidence/kg_questions.yaml` and `.md`, `tests/` additions for the new entry, the RESULT. Byte-identical: everything else, including `docs/brief/`, `docs/deck/`, `framework/`, and every file in the FSS repository. No projection beyond what the standing pipeline does for one document.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff, `python -m kg.manifest verify`. RESULT `cc_tasks/2026-10-02_commerce_guidance_admission_RESULT.md`, under 70 lines: the stored copy's path and the two hashes; whether the Definition exists with its locator; the reconciliation counts and the candidate list's size; the audit table; the generator diff and the Q1 change; the reader gate's five sentences; tokens spent against the 3M ceiling; premises wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** locate and hash → admit → extract → definition test → reconcile → audit → generator and `CL-085` → rerun questions → reader gate → gate → RESULT → push.
