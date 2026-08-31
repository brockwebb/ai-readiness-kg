# CC Task — Ground-truth yield re-derivation (mandated by pilot §3 FAIL-branch closure)

**Date:** 2026-08-30. **Repo:** /Users/brock/GitHub/ai-readiness-kg
**Standing:** Pilot §3 closed UNDER-EXTRACTION (A3 0.560 < 0.60). The floor's target (45.23/chunk, from the unvalidated v0.3.5 arm) is the suspect. This task re-derives the yield floor from measured ground truth. No further extraction arm, including Arm B, runs before this completes — recorded in the closure.
**Before starting:** glob and read any `_ADDENDUM*.md` siblings of this file; read the pilot RESULT §3 closure and `docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md`.
**Result:** `cc_tasks/2026-08-30_ground_truth_yield_floor_RESULT.md`; `seldon cc complete` this file at the end; commit, push.
**Spend:** annotation + adjudication only. Declare a ceiling of 800,000 tokens on the ledger before any model call; expected well under.

## 1. Rubric — derived, not invented, and NOT an operator input

Compile the extract-worthiness rubric from three sources, in priority order, each cited in the rubric document:

1. **The schema.** An item is extract-worthy iff it is typable under the domain config's node types AND the chunk asserts a property, definition, measurement, or relation about it — not merely mentions it. The existing salience instruction in the v0.3.8/v0.3.9 templates is the seed text.
2. **The consumers.** Crosswalk evidence cells (docs/crosswalk/) define what the graph must supply: instruments and their attributes (owner, year, method), measures, definitions, and claims with a subject and a stake. Items no consumer class could query are not extract-worthy (headings, boilerplate, incidental proper nouns, section labels).
3. **Prior art.** Adapt decision rules from scientific-IE annotation guidelines — SciERC (Luan et al. 2018), ACE/ERE entity guidelines, TAC KBP slot-filling. Cite what each adopted rule comes from. Where our schema diverges, the schema wins.

Write the rubric to `docs/research/ground_truth_rubric.md` BEFORE any annotation, sha-pin it, and treat it as immutable for this task. Include explicit negative rules (what is NOT extract-worthy) with examples drawn from the pilot set-difference sample already in the RESULT (heading inventory, mid-word fragments, bare concept nouns).

## 2. Sample

The 5 chunks mandated by the closure: seeded deterministic draw (seed recorded) from the pilot's five documents' chunks within the 44-chunk comparator set, one chunk per document. These documents were untouched by acquisition round 2 (recorded in the RESULT erratum), so no manifest pinning is needed.

## 3. Annotation protocol — model-annotated, double, blind

1. Annotator model: the strongest model available to the harness (Sonnet-class or better; record which). NOT Haiku — the annotator must outclass the production extractor.
2. Two independent passes per chunk under two prompt framings: (a) rubric-as-checklist exhaustive read; (b) consumer-simulation ("what would a crosswalk evidence query need from this chunk"). Neither framing sees any arm's output. Annotation is of the chunk text only.
3. Reconciliation, deterministic: items agreed by both passes (containment-key match) → ground truth. Items in exactly one pass → re-scored once against the rubric's explicit rules by a third pass that sees only the item, the chunk, and the rubric; admitted iff a cited rubric rule applies, else excluded. Unresolvable → excluded and counted, reported as annotation uncertainty, never silently dropped.
4. Report inter-pass agreement. If agreement (Jaccard on containment keys) < 0.5, STOP and report — the rubric is underspecified and patching it mid-task would be measuring the patch. That stop is an incident-class report, the one path that reaches the operator.

## 4. Re-derivation and re-judging

1. Ground-truth yield per chunk = admitted ground-truth items / chunk. Re-derived floor = 0.60 × mean ground-truth yield, stated with its n=5 uncertainty (report the per-chunk spread; no fake precision).
2. Score ALL THREE arms (A, A2, A3) against ground truth on those 5 chunks: recall (containment key), precision proxy (arm items matching ground truth / arm admitted), and yield ratio vs the re-derived floor. The comparison MUST include A2 vs A3 head-to-head — A3 admitted more items but fewer Instruments, regressed cites, and costs more per item; the closure requires profile selection by measurement, not recency.
3. Also score v0.3.5 chunked against ground truth on the same chunks: if its 45.23 was over-extraction, quantify it — that number retroactively explains the entire floor saga and goes in the writeup.
4. Verdict: which profile (v0_3_8 or v0_3_9) is the production candidate, at what re-derived floor, with the limitation paragraph (model-defined ground truth; stronger annotator, different task posture; n=5 chunks from pilot documents only — corpus generalization still owed to the ADDENDUM-06 stratified confirmation, which the bulk task inherits).

## 5. Out of scope

Any new extraction arm; template edits; Arm B; bulk extraction; rubric changes after sha-pin (a rubric defect found mid-task = report and stop, new task re-derives); operator involvement absent §3.4's stop condition.
