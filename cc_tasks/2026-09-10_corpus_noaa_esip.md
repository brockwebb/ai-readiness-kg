# CC Task — corpus: NOAA's AI-ready data definition and the ESIP checklist enter the crosswalk

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session. Operator supplied the two NOAA sources.
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs after `2026-09-10_scan_run_4.md`. Independent of the scan; touches corpus and crosswalk only.
**Spend:** zero model calls. **Network:** the three source fetches below and nothing else. `www.noaa.gov` is not on the scan roster and is not scanned; it is fetched once per document as a source, robots-first through the fetcher; if the fetcher is refused (the identified client was blocked from Desktop; plain `curl` was not), record the refusal as an Observation on the Document and use the operator-supplied copies from the Desktop session (the operator will place them at `corpus/inbox/`). Never fetch with a non-identified UA.

**Sources:**
- NAO 216-128, *Artificial Intelligence in NOAA*, signed and effective 2026-04-16. https://www.noaa.gov/sites/default/files/2026-04/NAO_216-128.pdf. Scanned image PDF; OCR required; the definition text is in §3.01.
- NAO 201-118, *Software Governance and Public Release Policy*, 2024-11. https://www.noaa.gov/sites/default/files/2024-11/NAO_201-118-Software_Governance_and_Public_Release_Policy.pdf. Text PDF.
- ESIP Data Readiness Cluster, *Checklist to Examine AI-readiness for Open Environmental Datasets*, Christensen et al., ESIP, 2021, v1.0.1 (Figshare). Search the corpus first; admit only if absent; record the exact citation as found, not as written here.

**Decisions taken here (operator overrides later):**
1. Both NAOs are admitted as Documents, authority NOAA, `in_force` (216-128 has no supersession; 201-118 per its own §8), with the OCR text stored beside the image PDF and marked as OCR with the engine and confidence.
2. NAO 216-128 §3.01 becomes a Definition node, term "AI-Ready Data", verbatim, five components split as sub-properties: discoverable; machine-readable and machine-understandable; sufficient quality; documentation; access methods. §4.05 and §5.02.d become Obligations (force `obligation`) with their verbatim text.
3. A crosswalk DataFile `crosswalk_noaa_ai_ready_2026-09-10` maps each component to the framework indicators that measure it, with `measured: full | partial | none` and the indicator ids: discoverable → A4, A5, A11; machine-readable/understandable → A1, A2, A6, A8, D1; access methods → A9, B3, F4; documentation → partial (license, vintage); quality → none. A test re-derives the file from the graph.
4. The ESIP checklist, if admitted, is crosswalked the same way, item by item, in `crosswalk_esip_ai_readiness_<date>`.
5. No report prose changes. A note in `docs/design/2026-09-08_l0_product_shape.md` §"What the matrix cannot see" records that the cycle-4 revision cites the NOAA definition and states the three-of-five coverage.

**Zero edits to:** shipped rule modules, registered Results, prior RESULTs, cycle evidence, report prose and PDF, targets.

**Immutable once written. Glob `2026-09-10_corpus_noaa_esip_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Admit (decisions 1, 2; ESIP search then admit if absent).
## 2. Crosswalk (decisions 3, 4, 5).
## 3. Gate (the one gate of this task)
Both crosswalk files re-derive from the graph byte-identically; the Definition node's verbatim matches the OCR text span it cites; `corpus admit` manifest verify clean; fast tier; `seldon verify`; protected paths.
**Failure: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-10_corpus_noaa_esip_RESULT.md`: whether the fetcher was refused by noaa.gov and what was recorded; whether ESIP was already in the corpus; the two crosswalks as tables; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
