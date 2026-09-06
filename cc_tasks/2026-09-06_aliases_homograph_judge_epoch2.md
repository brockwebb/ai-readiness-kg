# CC Task — Surface-form aliases, judged homograph pass on the diagnosed class, epoch 2

**Date:** 2026-09-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-05_er_gold_fable_labels_and_score_RESULT.md`)
**Follows:** `3e56d806` (completed), `0b8ea847` (completed — its Phase A scores and DD-046 are inputs here).
**Premise (verified against the live graph, Desktop 2026-09-06):**
- Gold stratum E precision 0.889 [0.672, 0.969]; both false merges are `air:concept/accessibility` (`{org 1, pub 29, train 1}`, auto_keep, `s` = +0.089). Stratum D recall 0.000 (6 of 20 near-misses are true matches, all surface-form variants). Strata B/C: 39/40 clerical-band decisions correct.
- Homograph pass (0b8ea847 §1.2): 71 auto-split / 79 auto-keep / 139 band; 61 of the 79 auto-keeps have an arm with < 3 members. 82 terms have no arm with ≥ 2 members.
- 1,561 of 11,432 `Concept` nodes carry `grounding_span` == `name` (case/whitespace-insensitive). Register as Issue in §4; do not fix here.
- DD-045 §3 verdict PASS on point estimates, n_eff 21; the sample cannot certify the 0.95 floor. DD-045 addendum-01 in force.
**Spend:** Phase A zero. Phase B judges ~200 terms on Opus (`judge` floor), Fable κ on 50: expect ~6.3M at the measured ~31.3k/unit; ceiling from a 10-term calibration (DD-042); **stop above 9M.** The run will cross a band rollover: resume from evidence on disk, never re-judge a term that has a decision record. Claude Max OAuth only; `ANTHROPIC_API_KEY` in the environment is a STOP.
**Zero edits to:** `assessment/cq/cq_set_v1.yaml`, `cq_set_v2.yaml`, `kg/schema.yaml`, `state/er_gold_key.json`, the 100-pair sheet, the memo, the deck. Do not move any threshold registered in 0b8ea847 §1.2 or DD-045 §3.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-06_aliases_homograph_judge_epoch2_ADDENDUM*.md` before starting.**

---

## 0. Prior art (record in DD-047 with the rulings in §5)

- **Acronym/expansion pairs:** Schwartz & Hearst (2003), "A simple algorithm for identifying abbreviation definitions in biomedical text", *PSB 2003* — the parenthetical-pattern algorithm; still the baseline. Applied to node names and grounding spans.
- **Surface-form normalisation in record linkage:** Christen (2012) *Data Matching* ch. 3 (standardisation before comparison): determiner strip, version-token strip, generic-suffix strip.
- **Two-literature homonymy:** the FCSM Data Quality Framework dimensions (accuracy, accessibility, timeliness, interoperability, …) and maturity-model capability dimensions (MITRE AI Maturity Model, and kin) share labels with different referents — a capability of an organisation vs a property of a data product. FAIR (Wilkinson et al. 2016) adds a third referent for `accessibility`/`interoperability`. Qualifiers per ISO 25964-1 §6.2.2, as DD-046.
- **Allocation for the regold:** Neyman (1934), optimal allocation proportional to N_h·S_h; standard survey-sampling practice (Cochran 1977 §5.5).

## 1. Phase A — surface-form aliases (zero model spend)

### 1.1 Generators, each a named derivation
Run over every linkable node's `name` and `grounding_span` and every active term's prefLabel/aliases:
- `schwartz_hearst`: `Long Form (SF)` and `SF (Long Form)` → both forms become aliases of whichever term either form already resolves to.
- `determiner_strip`: leading `the|a|an`.
- `version_strip`: trailing version token (`\s+v?\d+(\.\d+)*$`), e.g. `SDMX 2.0` → `SDMX`.
- `generic_suffix_strip`: trailing `standard|specification(s)|protocol|framework|guideline(s)|principle(s)` **only when the stripped form already matches an existing term or alias exactly** — never create a term from a bare stripped form.
- `technical_specifications_variant`: `Technical Specifications` ↔ `Technical Standards` treated as one generic suffix under the same guard.
Each generated alias carries `derivation: <generator>` and `evidence: <node id>`. Apply the label-theft check from `27b360f4` §1.2 unchanged: an alias that already belongs to a different term is refused and counted.

### 1.2 Controls (gate for Phase A)
- **Positive:** the six stratum-D true matches (`P0xx` ids in `state/er_gold_key.json` with gold `same` and stratum D) must resolve to a shared term after relink. If fewer than 5 of 6 do, register `alias_positive_control_failed = 1` and do not write Phase A to the vocabulary log.
- **Negative:** the 19 stratum-C gold-`different` pairs and the 14 stratum-D gold-`different` pairs must **not** resolve to a shared term. Any violation is a hard stop for Phase A.
- **Property-gated, labelled Cypher only.** Add the lint from DD-046's twin-node finding: a test that greps `kg/` write paths for `MATCH (n {` and fails on any unlabelled node pattern.

### 1.3 Write and register
`alias_added` events (epoch 2 candidates) → relink → register `alias_generated_<generator>`, `alias_refused_label_theft`, `vocab_auto_linked_after_aliases`, `vocab_residue_unresolved_after_aliases`, and the delta.

## 2. Phase B — judged homograph pass on the diagnosed class (spends)

### 2.1 Population
From 0b8ea847's registered Phase A output: all **band** terms (139) plus every **auto_keep** term with any arm holding < 3 members (61). Register `homograph_judge_population` (expected 200; report the exact number). Auto-split terms (71) are **not** judged and **not** split — the score that produced them is discredited (DD-046); they stay merged pending the regold.

### 2.2 Protocol
One term per call, Opus at the `judge` floor: prefLabel, scope note, **up to 3 grounding spans per arm quoted verbatim with the arm named and the document title**; verdict `same_sense | distinct_senses | uncertain`, confidence, one sentence quoting the deciding phrase per arm. **Cosine, `s`, and the 0b8ea847 class are withheld.** For a term whose only spans in an arm are bare (span == name), say so in the prompt as "no context available for this arm" rather than quoting the bare word. Calibrate on 10, declare the ceiling, run, resume across rollover. Fable rates 50 (stratified over band/auto_keep, seed 20260906) independently in hermetic cwd. **κ ≥ 0.60 or nothing is written.**

### 2.3 Controls (gate for Phase B)
- **Positive:** `air:concept/accessibility` and `air:concept/ai-ready` must come back `distinct_senses` (they are in the population by construction: both are auto_keep with a thin arm). Either `same_sense` → `homograph_judge_positive_control_failed = 1`, nothing written.
- **Negative (reported, not gated):** `JSON-LD`, `RDF`, `PROV-O`, `ISO 8601`, `DataCite` if in the population — expected `same_sense`.

### 2.4 Writing the split — epoch 2
For every `distinct_senses` with confidence ≥ 0.80: qualified children per arm exactly as `0b8ea847` §2.2 specifies (`air:<label>/<slug>--<arm>`, prefLabel `<label> (<arm human name>)`, scope note from the arm's most-cited span, umbrella only if a curated S1/S2 term already exists). A single-member arm still gets its own child — one node is one sense with evidence, and the judge saw the span. Fold in Phase A's aliases and the DCAT-US split from `ontology/vocabulary_proposals_epoch2.yaml`. `vocabulary_epoch` 2. Turtle re-export. Loader: `(normalized name, construct_arm)` as key **for qualified terms only**, tests as specified there.

### 2.5 Rerun the canonical view
`cq_set_v2.yaml` unchanged. Three views, next dated suffix per DD-041. Report per-CQ canonical row deltas; `flip_canonical` for the record only.

## 3. Regold allocation — pre-registered now, executed next task
From the five strata's gold outcomes, compute Neyman allocation for a **200-pair** regold: n_h ∝ N_h·S_h with S_h from each stratum's observed error proportion (use p = 0.5 for strata with zero observed errors, which is the conservative choice, not a bias toward A). Add stratum **F: pairs this task changed** — nodes whose resolution moved because of a new alias or a split — with N_F from §1.3/§2.4 and S_F at p = 0.5. Register the allocation table as `er_regold_allocation_2026-09-06` (a DataFile with `snapshot: true`) and the per-stratum n as Results. The next task samples from it with seed 20260906; the draw is not made here.

## 4. Issue — bare-span grounding
Create Issue: 1,561/11,432 Concept nodes (13.7%) have `grounding_span` identical to `name`; a span that is the bare term gives a judge, a rater, or a reader nothing to resolve on, and all three gold `uncertain`s were this class. Importance high, not blocking this task. Register `concept_bare_span_count` and `concept_bare_span_share`. Link the Issue to the gold-sample Result `er_gold_escalations`.

## 5. DD-047 — rulings
1. DD-045 §3 PASS stands as registered; the population criterion is met and probe design is not blocked by it.
2. Per-stratum defects (E precision, D recall) are acted on ahead of probe design because enumeration probes draw on the quality-dimension vocabulary where the false merges sit; this is sequencing, not a new gate.
3. The embedding-score homograph detector (0b8ea847 §1.2) is retired for classification; its output is used only to define the judged population. Any future detector is calibrated on its own null (DD-046) before it classifies anything.
4. The regold is the acceptance measurement for epoch 2; its allocation is fixed in §3 before epoch 2's numbers exist.

## 6. Reporting
RESULT: `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2_RESULT.md`. Lead with both controls' outcomes, then terms split / aliases added, then the canonical CQ deltas, then κ and spend. State every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on the protected files. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (stop on control failure; §2 still runs on the pre-alias membership if §1 wrote nothing, and says so) → §2 → §2.4 → §2.5 → §3 → §4 → §5 → §6. §3 and §4 run regardless of §1/§2 outcomes.
