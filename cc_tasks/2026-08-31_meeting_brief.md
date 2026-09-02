# CC Task — Meeting brief: what the AI-readiness KG holds and can answer, mapped to the operationalization skeleton

**Date:** 2026-08-31 (evening). **Repo:** /Users/brock/GitHub/ai-readiness-kg. **Immutable once written.**
**Before starting:** glob and read every `cc_tasks/2026-08-31_meeting_brief_ADDENDUM*.md`.
**Result:** `cc_tasks/2026-08-31_meeting_brief_RESULT.md` (short — the deliverable is the brief, not the RESULT); `seldon cc complete`; commit, push.
**Spend:** zero extraction/model-ledger spend. Read-only against the projection and ledgers. Do not touch the running burn's files, queue, or shards; if reading a shard the burn writes, read a snapshot copy.

**Deliverable:** `docs/crosswalk/meeting_brief_2026-09-01.md` — maximum two pages rendered, written for a federal audience discussing AI data readiness frameworks tomorrow morning. Prose, no bullet walls, no hype. Numbers only from the ledger/projection, each traceable; anything not derivable is omitted, not estimated.

## Content, in order

1. **What exists** (one paragraph): a knowledge graph over the federal AI-readiness gray literature and adjacent standards — documents admitted with recorded reasons, converted to a uniform substrate, extracted under a version-pinned profile, every batch quality-gated before entering. Sizes from live state: documents admitted / with substrate / extracted; nodes by type; chunks processed.
2. **Coverage against the operationalization** (the centerpiece): read `docs/crosswalk/usafacts_operationalization_skeleton.md`. For each indicator group A–G, report what the graph now holds that bears on it — source documents extracted, node counts by type touching that group's concepts (use concept/text search over the projection; be honest where the mapping is judgment). One compact table. Then the demand ledger: crosswalk demand covered by tonight's burn (~76%, exact from state), the +4 demand landing when b014/b015 complete (~85%), and what is deferred-with-reason (three long specifications at 6 demand, 159 zero-demand documents) with the one-sentence demand-pull explanation: any deferred content is one request event away, at chunk grain.
3. **The quality line** (one short paragraph, this is the differentiator): extraction quality is measured, not asserted — pre-registered faithfulness gate (fabrication upper bound < 0.10 at 95%, item-faithfulness ≥ 0.70) passed at qualification (report the actual Phase A numbers), and every production batch passes sequential acceptance sampling (Wald SPRT, parameters fixed before data) before its content enters the graph; rejected batches quarantine automatically. Report batches accepted so far and observed pooled F from batch records. One sentence on the two-layer DD-024 guard refusing relation types that lack a consumer. The Census-native framing is allowed one sentence: estimates ship with error measurement; this graph ships with the same discipline.
4. **G1 tie-in** (two or three sentences): the skeleton's flagship indicator is uncertainty legibility — MOEs/CVs as structured, machine-readable fields. Note that this project practices the indicator it proposes: every quality number above carries its interval or its n. Do not oversell; one observation, not a section.
5. **What this enables next** (three sentences max): instrument items grounded in extracted evidence; per-indicator evidence lookup; gap identification (indicator groups where the corpus itself is thin — name the thinnest one or two from the §2 table, since an honest gap strengthens the story).

## Constraints

- Every number checked against its source of record; no number from memory or from chat history. If the burn is mid-batch when run, report state as of a named timestamp.
- No claims about edges/relations beyond cites (DD-024 stands; do not imply semantic relation coverage).
- Style: short plain sentences; no em-dashes; no bold in prose; no "delve/leverage/robust"; "confabulation" not "hallucination". Numbers with intervals where they have them.
- If an indicator group maps to nothing in the graph, the table says so plainly. Empty cells are findings.
