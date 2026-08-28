# Lab note — 2026-08-27 — the unit of extraction was the defect, and it was a known one

**Type:** LabNotebookEntry. **Session:** Desktop, evening ET. **Tasks:** ea7dd3bd (pilot finish, closed FAIL/FAIL), `2026-08-27_chunked_pilot.md` (registered).

## What happened

The five-document pilot under prompt v0.3.5 and Claude Opus 5 failed both strata. Instrument: F_upper 0.158, item-faithful 0.292 (89 facts, 24 pooled). Semantic: 0.607 entailed on the diverted candidates and 0.61 on the live kernel-era edges; 23/35 non-entailed facts are fabrication. Task spend 2.24M; the week's extraction and repair spend is on the order of 60M tokens.

## What it means

1. The extraction unit was the root cause of the cost pathology. Schema §5's one-call-per-document rule forced 108–158K-token outputs, which overflowed Opus 5's 128K cap, which forced a three-turn fallback, which doubled per-doc cost (single-pass ~400K, fallback 866K–1,331K). Every rule written this week about truncation was a patch on that decision.
2. It was already known. GraphRAG (2024) measured yield falling with chunk size. Gajo et al. (April 2026) explained the mechanism. Wintermute extracts at chunk level. The pilot was designed without citing any of it. That is a process defect, owned by Desktop: no prior-art step existed, so none fired.
3. Chunking will not by itself fix the faithfulness number. Wintermute's chunk-level extraction was killed at G4 for scoring zero against the embeddings baseline — cheap, not valid. The chunked pilot is the test of whether structure-aware chunking with locate-at-birth grounding clears F_upper < 0.10; the literature gives reason to expect improvement and no guarantee.
4. Bulk semantic-relation extraction is, on present evidence, not a task this pipeline can validate. The same finding as Wintermute's "RE fails at 2× entity rate." Disposition: demand-pull adjudication; live edges flagged by epoch.

## Decisions logged (operator overrides by addendum)

- Lane 4 relocation and re-judge halted before they start (STOP file, first action of the chunked-pilot task). Stage 2 resumes later by explicit task.
- Chunked pilot: same docs, same model, same raters, same thresholds; unit = section-bounded paragraph packs ≤ 1,500 tokens, 100-token overlap, breadcrumb; cross-chunk edges diverted; deterministic entity merge only.
- Methodology v1 written (`kg_construction_methodology.md`); §7 rule 1 makes a `prior_art` block a registration requirement for any pilot.
- Lanes 2 and 3 do not run under any profile until a stratum passes under a chunked unit.

## Open questions the chunked pilot answers

- Does per-doc cost land at or below the single-pass figure with no fallback path? (Expected yes; measured by dry run before the ceiling is declared.)
- Does the Instrument stratum pass once the two attribute-quoting defects are fixed in both arms? (This isolates unit from probe-protocol effects.)
- Does chunk-local extraction move semantic faithfulness at all, or is 0.61 the model's ceiling on assertion vs co-occurrence for these documents?
- What fraction of relations are lost to `cross_chunk` diversion — i.e., what the demand-pull queue will look like?

## Not done tonight

Methodology doc §1 (admission ≠ request ≠ extraction) describes 00968603 as in progress; it has not landed. Dedup design blocked on the chunked verdict and Lane 4's gate. `hub.home` launchpad untouched.
