# CC Task — Homograph split by construct arm, DD-045, and the ER gold sample

**Date:** 2026-09-05
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-05_vocabulary_and_entity_linking_RESULT.md`)
**Follows:** `27b360f4` (completed). Does not modify anything that task froze.
**Premise (verified against the live graph 2026-09-05, Desktop):**
- `air:concept/ai-readiness` has 28 `RESOLVES_TO` members spanning three `Document.construct_arm` values: org_maturity 12 nodes/11 docs, publication_actionability 9/7, training_data_readiness 7/4. `air:concept/ai-ready-data`: 8/4 pub + 3/3 training. `air:concept/ai-ready`: 4/4 pub, 2/2 org, 1/1 training. The canonical view merges the three senses that CQ-02 (`2026-09-04_kg_diagnostic_and_cq_harness`, §3a) established as distinct.
- 289 active Terms have members in ≥2 arms (259 in two, 30 in three), 1,666 nodes. Most are legitimately shared; the readiness family is not.
- Every Document carries `construct_arm` (163 pub / 53 org / 17 training = 233; no NULL). The key is complete.
- Graph holds 6,440 `RESOLVES_TO` edges (RESULT §1.4 reports 6,408): the 32 extra are 30 `Claim` + 2 `Practice` nodes, so RESULT §1.3's "not one Practice carries a `name`" is false and the loader's nameless-node fix (§1.4 defect 1) was label-gated, not property-gated. `unresolved: true` nodes: 7,619 (RESULT: 7,569). Register both discrepancies (§4).
**Spend:** Phase A zero. Phase B spends; ceiling from a measured calibration batch (DD-042); **stop above 10M**. Claude Max OAuth only; Fable for the κ rating as in Phase B of the prior task. Any `ANTHROPIC_API_KEY` in the environment is a STOP.
**Zero edits to:** `assessment/cq/cq_set_v1.yaml`, `cq_set_v2.yaml`, `kg/schema.yaml`, the memo, the deck. CQ-27's schema gap (Issue `2a2b6461`) is a separate task.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-05_homograph_split_and_er_gold_sample_ADDENDUM*.md` before starting.**

---

## 0. Why, and the prior art (goes into DD-045 with the acceptance ruling in §3)

Exact-name linking treats a surface form as one meaning. It is not: "AI-ready" is a homonym in this corpus (CQ-02: 17% framework sense, 41% training-data, 22% adoption/maturity). Thesaurus practice has handled this since the card catalogue with **homograph qualifiers** — `Mercury (planet)` / `Mercury (metal)` — standardised in **ISO 25964-1:2011 §6.2.2** (qualifiers) and expressible in SKOS as separate `skos:Concept`s with distinct `skos:scopeNote`s. The qualifier here is the document's construct arm, which this project already assigns by rule (`scripts/construct_arm_backfill.yaml`) and which CQ-02 used as its sense marker.

The licence to key sense on the document is **one sense per discourse** — Gale, Church & Yarowsky (1992), "One sense per discourse", *HLT '92*: a polysemous word overwhelmingly keeps one sense within a document (98% in their measurement). Arm is coarser than document, in the safe direction: it can under-split, never over-split within a document.

Which cross-arm terms are homographs is decided the way the prior task decided links — Fellegi–Sunter three-way split on a deterministic score (the prior task's own embedding space), Opus on the clerical band, Fable-rated κ gate — with one addition: **a positive control.** The readiness family is known to be homographic. If the method does not flag it, the method fails, and the split is not written.

For acceptance the correct instrument is the record-linkage literature's, not the CQ harness: pairwise precision/recall and cluster-level measures against a gold sample — **Menestrina, Whang & Garcia-Molina (2010), "Evaluating entity resolution results", PVLDB 3(1)**; the pairwise/B-cubed/cluster-F1 family in Christen (2012) *Data Matching*, ch. 7. The RESULT's own §4.1 finding is why: `flip` fires on raw-view shrinkage, which entity resolution can only increase.

## 1. Phase A — homograph detection (zero model spend)

### 1.1 Deterministic score
For each of the 289 cross-arm Terms: embed each member node's `grounding_span` with the repo's existing `all-MiniLM-L6-v2` (the space `link_vocabulary` used; no other model). Compute mean pairwise cosine **within** each arm's members and mean pairwise cosine **across** arms. Score `s = cross_arm_mean − within_arm_mean` (negative = arms diverge). Terms with fewer than 2 members in any arm get `within` from the arms that have ≥2; a term with no arm having ≥2 members is scored on cross-arm mean alone and reported separately.

### 1.2 Thresholds — pre-registered here, not tuned after
- **Auto-split** (homograph): cross-arm mean < 0.80 **and** `s` < −0.10.
- **Auto-keep** (one sense): cross-arm mean ≥ 0.80 **or** `s` ≥ 0.
- **Clerical band**: everything else. Register `homograph_candidate_terms` — the unit count for Phase B's ceiling.
The 0.80 is the prior task's pre-registered lower threshold in the same embedding space; do not move it. If the 0.80 / −0.10 pair produces a band larger than 150 terms, STOP and report the distribution — do not narrow the band.

### 1.3 Positive control (gate)
`air:concept/ai-readiness`, `air:concept/ai-ready-data`, `air:concept/ai-ready` must land in **auto-split or band**. If any lands in auto-keep, register `homograph_positive_control_failed = 1`, write nothing to the vocabulary log, and stop after §4. Negative control: pick the 10 highest-`nodes` cross-arm Standards (DCAT, robots.txt, schema.org …) — expected auto-keep; report if not, but do not gate on them.

## 2. Phase B — clerical band (spends)

### 2.1 Calibration and ceiling (DD-042)
Prompt: one term per call; the term's prefLabel and scope note; **up to 3 grounding spans per arm quoted verbatim with the arm named**; verdict `same_sense | distinct_senses | uncertain`, confidence, one-sentence reason; **cosine and `s` withheld** (anti-anchoring, rubric v1.3.0 §2 — the band was selected by the score). Calibrate on 10 band terms at the `judge` floor, measure tokens/term, ceiling = band × rate × 1.15, declared before the band run. Fable rates a stratified sample of min(50, band) decisions independently, one term per call, hermetic cwd. **κ ≥ 0.60 or nothing is written.** Register `homograph_calibration_kappa`, `homograph_link_decisions_*`, `homograph_tokens_declared/settled`.

### 2.2 Writing the split (append-only, epoch 2)
For every auto-split term and every band term judged `distinct_senses` with confidence ≥ 0.80: append `term_deprecated` for the parent and `term_added` for one qualified child per arm — `term_id` `air:<label>/<slug>--<arm>`, prefLabel `<label> (<arm human name>)`, scope note = the arm's most-cited span, `skos:broader` → a new unqualified umbrella term only if one already existed as a curated S1/S2 term (never invent umbrellas for graph-derived terms). Then `vocabulary_epoch` 2, folding in the **DCAT-US split** already proposed in `ontology/vocabulary_proposals_epoch2.yaml` (remove `DCAT-US` from `air:dcat`'s aliases; `air:standard/dcat-us` stands). Re-export the Turtle. `RESOLVES_TO` for split members is recomputed by the loader from `(normalized name, construct_arm)` — the loader gains the arm as a second key **only for qualified terms**; unqualified terms resolve exactly as before. Test: a fixture term with two arms resolves each member to its own child; an unqualified term's resolution is byte-identical before and after.

### 2.3 Loader fix carried from the prior RESULT
Gate `unresolved: true` on `name IS NULL`, not on label. Test with a named `Claim` fixture. Register the per-label counts after the rebuild (§4).

### 2.4 Rerun the canonical view
`cq_set_v2.yaml` unchanged. Rerun all three views; register every CQ Result with the next dated suffix per DD-041. Report `flip_canonical` for the record but **it is not an acceptance criterion** (§3). Report per-CQ canonical row counts before/after the split; enumeration CQs touching the readiness family should change, nothing else should.

## 3. DD-045 — acceptance for entity resolution (append to `docs/design_decisions.md`)

Record, with the citations in §0:
1. DD-020 stands. `flip` (§1.5 of the 09-04 task) fires on raw-view shrinkage; resolution that keeps per-document nodes can only raise it. `flip` is retained as a **duplication-severity trigger** — it measures need — and is **not** an acceptance metric for resolution. The `flip < 0.10` criterion in `27b360f4` §4 is recorded as failed and as unsatisfiable by construction.
2. At n = 26–27 questions, `flip` has SE ≈ 0.09; 0.30 lies within one SE of both 0.308 (v1) and 0.296 (v2). The §1.5 branch has no discriminating power at this n; a harness repair crossing it demonstrated that. ER's blocking status is decided by canonical precision, not by `flip`.
3. ER acceptance is pre-registered on ER-standard metrics against a gold sample (§5 of this task): **pairwise precision ≥ 0.95, pairwise recall ≥ 0.80**, each with a Wilson 95% interval, stratum-weighted to population; cluster F1 reported. Asymmetry is the grounding: a false merge silently corrupts every enumeration CQ; a missed merge surfaces as a countable duplicate. Thresholds are operator-declared (Desktop, 2026-09-05); override lands as a new DD entry.
4. Rater agreement (κ) is reliability, not correctness. Gold is human-labelled.

## 4. Discrepancy registration (DD-040)
Register, with derivations: `vocab_resolved_by_label_<Label>` and `vocab_unresolved_by_label_<Label>` for every label after the §2.3 rebuild; `vocab_resolved_total` and `vocab_unresolved_total`; an ERRATUM-01 to the prior RESULT noting 6,408→6,440 and 7,569→7,619 and the named `Claim`/`Practice` nodes. Register `homograph_cross_arm_terms = 289` and `homograph_cross_arm_nodes = 1666` as the task premise.

## 5. Gold sample for the operator (zero model spend; the one operator touchpoint)

After §2 lands, draw **100 pairs, 20 per stratum**, seeded RNG (seed recorded):
- A. auto-linked exact-name pairs (two nodes, same term, cosine 1.0 on key)
- B. band-accepted pairs from the prior task (of the 45)
- C. band-rejected pairs from the prior task (of the 87)
- D. near-miss auto-rejected pairs, cosine ∈ [0.70, 0.80)
- E. cross-arm pairs from terms this task **kept** (auto-keep or judged `same_sense`)

Write `docs/research/2026-09-05_er_gold_sample.md`: one row per pair — pair id, stratum **hidden** (held in `state/er_gold_key.json`, not in the sheet), node A label + span + doc title + arm, node B likewise, blank `verdict` (`same | different | uncertain`) and `note`. **No cosine, no term name, no current decision on the sheet.** Write `scripts/score_er_gold.py` **before** the sheet exists: reads the filled sheet + key, computes pairwise precision/recall per stratum and population-weighted (weights = stratum population sizes, registered), Wilson intervals, cluster F1 on the induced clusters, compares to §3 thresholds, registers Results `er_gold_precision`, `er_gold_recall`, `er_gold_cluster_f1`, `er_gold_verdict`. Test the scorer on a synthetic filled sheet with known answers. The operator fills the sheet; scoring is the next dispatch, not this one.

## 6. Reporting
RESULT file: `cc_tasks/2026-09-05_homograph_split_and_er_gold_sample_RESULT.md`. Lead with the positive-control outcome and the number of terms split. State every premise this task got wrong. Tests: `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` on the two CQ yaml files and `kg/schema.yaml` must be empty. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 (stop at §1.3 on control failure) → §3 → §4 → §5 → §6. §5 depends on §2 having landed; if §2 wrote nothing, §5 draws from the pre-split state and says so in the sheet header.
