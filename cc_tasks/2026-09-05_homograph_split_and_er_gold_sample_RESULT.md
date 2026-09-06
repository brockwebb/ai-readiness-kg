# RESULT: the positive control failed, nothing was split, and the diagnosis is worth more than the split

**Task:** `cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md` §0–§6. **No addenda** — globbed before starting, none exist. **Date:** 2026-09-05 UTC. **Spend: ZERO model calls.** Phase B was never reached. **Task file committed before execution** (`4f50ec7`).

**Lead, as §6 requires.**

> **The §1.3 positive control FAILED. `air:concept/ai-ready` — known homographic from CQ-02's own sense harvest — landed in `auto_keep`. Per §1.3 nothing was written to the vocabulary log, Phase B was not run, and 0 terms were split.**

The control did exactly what a control is for. And the *reason* it failed is the substantive finding: **the thresholds were transplanted from a different comparison and do not transfer.** The 0.80 floor was pre-registered in DD-044 for *node name + span* against *term label + scope note* — text against its own definition. Here it is applied to *one document's sentence* against *another document's sentence*, which measures topical spread between documents at least as much as sense. **Only 12 of 289 cross-arm terms reach 0.80 at all.**

The negative control agrees and is blunter: of the ten highest-membership cross-arm `Standard` terms, **five auto-split** — JSON-LD, ISO 8601, DataCite, VoID, Croissant-RAI — and `Schema.org` (33 members) fell in the band at cross-arm mean 0.383. A method that would split JSON-LD is not ready to split anything.

**A second finding, unrelated and concrete:** both spend-free discrepancies this task was asked to register have **one** cause, and it is not the one the premise supposed — a Cypher pattern without a label, binding 82 twin nodes.

---

## §0. Prior art — DD-046

Recorded with citations: homograph qualifiers are thesaurus practice since the card catalogue (`Mercury (planet)` / `Mercury (metal)`), standardised at **ISO 25964-1:2011 §6.2.2** and expressible in SKOS as separate `skos:Concept`s with distinct scope notes. The licence to key sense on the document is **Gale, Church & Yarowsky (1992), "One sense per discourse", *HLT '92*** — 98 % of the time a polysemous word keeps one sense within a document. An arm is coarser than a document, which errs safely: it can under-split, never over-split within one.

## §1. Phase A — homograph detection (zero model spend)

### §1.1–1.2 Scores and the three-way split

| | |
|---|---:|
| active terms | 1,946 |
| **cross-arm terms** (members in ≥ 2 arms) | **289** |
| **cross-arm nodes** | **1,660** |
| terms in 2 arms / 3 arms | 259 / 30 |
| auto-split (cross < 0.80 **and** `s` < −0.10) | **71** |
| auto-keep (cross ≥ 0.80 **or** `s` ≥ 0) | **79** |
| **clerical band** (`homograph_candidate_terms`) | **139** |
| §1.2 band stop threshold | 150 — **not exceeded** |
| scored on cross-arm mean alone (no arm has 2 members) | **82** (28 %) |

Thresholds were **not** tuned after seeing the distribution, and the band was **not** narrowed. Members are read per `(term, node label)`, not per key — see §4.

**The cross-arm mean distribution is the whole story.** Buckets of 0.05, over 289 terms:

```
0.25 15 | 0.30 14 | 0.35 26 | 0.40 33 | 0.45 36 | 0.50 37 | 0.55 31
0.60 32 | 0.65 19 | 0.70  8 | 0.75 10 | 0.80  3 | 0.85  3 | 0.90 4 | 0.95 2 | 1.00 1
```

The population is centred near **0.50**. The prior task's band — the interval this 0.80 was pre-registered for — was `[0.80, 1.0)` on a *name-to-definition* comparison. Here that interval holds 12 terms out of 289. **The `cross ≥ 0.80` limb of auto-keep is nearly dead**, so 67 of the 79 auto-keeps arrive on the `s ≥ 0` limb alone — and **61 of those 67 have an arm holding fewer than three members**, where a within-arm mean is noise.

### §1.3 Positive control — FAILED (the gate)

| term | arms (nodes) | cross | within | `s` | class |
|---|---|---:|---:|---:|---|
| `air:concept/ai-readiness` | org 12, pub 9, train 7 | 0.6491 | 0.6667 | −0.0176 | band ✓ |
| `air:concept/ai-ready-data` | pub 8, train 3 | 0.6144 | 0.6441 | −0.0297 | band ✓ |
| **`air:concept/ai-ready`** | **org 2, pub 4, train 1** | **0.5564** | **0.4522** | **+0.1043** | **auto_keep ✗** |

`ai-ready`'s members are *less* similar to each other **within** an arm than **across** arms — with 2 and 4 members per arm and a third arm of 1, the within estimate is noise, and the single-node arm contributes to `cross` while contributing nothing to `within`. `s` goes positive, the auto-keep limb fires, and a term whose homography CQ-02 measured directly is classified as one sense.

`homograph_positive_control_failed = 1` is registered. **Nothing was written to the vocabulary log. Phase B (§2.1, §2.2, §2.4) was not run and cost nothing.** Epoch 1 stands; the DCAT-US split proposed in `ontology/vocabulary_proposals_epoch2.yaml` remains proposed.

### §1.3 Negative control — also poor (reported, not a gate)

| class | cross | nodes | term |
|---|---:|---:|---|
| band | 0.383 | 33 | Schema.org |
| **auto_split** | 0.366 | 17 | JSON-LD |
| **auto_split** | 0.501 | 7 | ISO 8601 |
| **auto_split** | 0.382 | 6 | DataCite |
| auto_keep | 0.454 | 6 | PROV-O |
| auto_keep | 0.513 | 6 | RDF |
| **auto_split** | 0.380 | 6 | VoID |
| band | 0.563 | 5 | CSVW |
| **auto_split** | 0.389 | 4 | Croissant-RAI |
| band | 0.409 | 3 | NIST AI 600-1 |

Five of ten well-known single-sense standards auto-split. Two pass. Three land in the band. The score is not separating senses; it is separating documents.

**What would fix it, recorded in DD-046 and deliberately not done here:** a **same-arm null distribution** — score pairs drawn *within* one arm to learn what "same sense, different document" looks like in this embedding space, and set the floor from that rather than importing one. That is a calibration task with its own pre-registration, not a threshold nudged after seeing this result.

## §2. Phase B — not run

§1.3 is a stop and it stopped. No calibration batch, no ceiling declared, no band judged, no κ rating, no `term_deprecated`, no `term_added`, no epoch 2, no Turtle re-export, no CQ rerun. **Zero tokens.**

**§2.3 was executed**, because §4 explicitly requires the label counts "after the §2.3 rebuild" and a loader defect is not a vocabulary write. See §4.

**One reading I had to make.** §1.3 says "stop after §4"; the SEQUENCING line runs "§1 → §2 (stop at §1.3 on control failure) → §3 → §4 → §5 → §6"; and §5 provides explicitly for the case where "§2 wrote nothing … §5 draws from the pre-split state and says so in the sheet header." Those cannot all be literal at once. I read "stop at §1.3" as stopping the *split pipeline*, not the task — because §5's own clause is meaningless otherwise, because §5 is zero-spend, and because the gold sheet is what unblocks the DD-045 acceptance instrument whether or not a split happened. §3, §4, §5 and §6 were executed; the sheet header states the pre-split state.

## §3. DD-045 — acceptance for entity resolution

Appended, with the §0 citations. Four rulings:

1. **DD-020 stands, and `flip` cannot be an acceptance metric under it.** `flip` fires on `misleading_raw`, computed from raw-view shrinkage; the raw view is one node per document per mention because DD-020 requires it, so resolution that keeps per-document nodes can only leave that shrinkage alone or raise it. `27b360f4` §4's `flip < 0.10` is recorded as **failed and unsatisfiable by construction**. `flip` is retained as a **duplication-severity trigger** — it measures *need* — and is never again quoted as evidence resolution worked.
2. **No discriminating power at this n.** At 26–27 questions a proportion near 0.3 carries SE ≈ 0.09, and 0.30 sits inside one SE of both 0.308 (v1) and 0.296 (v2). The demonstration is empirical: two `collapse_on` repairs, **with no change to the graph**, moved `flip` across the boundary and flipped the branch.
3. **Acceptance is pairwise precision ≥ 0.95 and recall ≥ 0.80**, Wilson 95 % on the effective sample size, stratum-weighted to population; cluster F1 reported, never a gate. Menestrina, Whang & Garcia-Molina (2010) PVLDB 3(1); Christen (2012) ch. 7. **The asymmetry is the grounding:** a false merge silently corrupts every enumeration CQ because the entity stops being countable as two; a missed merge surfaces as a duplicate somebody can count.
4. **κ is reliability, not correctness.** DD-044's κ = 0.979 bounds rater idiosyncrasy and says nothing about whether either rater is right. **Gold is human-labelled.**

DD-045 does **not** retune §1.5's 0.30 and does not withdraw the branch it fired.

## §4. Discrepancies — one cause, and not the one the premise named

The task premise reads the two gaps as evidence that "RESULT §1.3's *not one Practice carries a `name`* is false and the loader's nameless-node fix was label-gated, not property-gated." **Both halves are wrong.** Measured: **zero** `Claim` and **zero** `Practice` nodes carry a `name`, and `_resolve_node` was already gated on the property (`if not (name and str(name).strip()): return`), not the label.

**The actual cause.** `_write_resolutions` matched `MATCH (n {key: $key})`, and DD-020's `<doc_id>::<item_id>` is **not unique across types**. The extractor asserts one item id under two types in one document **82 times**: **75 `Claim`+`Concept`, 7 `Platform`+`Practice`**. Every one took a spurious write.

| | RESULT counter | graph before | after fix |
|---|---:|---:|---:|
| `RESOLVES_TO` edges | 6,408 | 6,440 (**+32**) | **6,408** |
| `unresolved: true` | 7,569 | 7,619 (**+50**) | **7,569** |

**32 + 50 = 82**, exactly the shared-key count — the whole gap, accounted for. Same Cypher trap as the g1eval defect of 2026-09-04: a pattern without a label binds every node that matches it. Fixed by keying `_resolutions` on `(node key, kg label)` and interpolating the label (which comes from `kg_labels` and was already validated). Regression test written first. **ERRATUM-01 appended to the prior RESULT.**

Post-rebuild label counts, registered:

| label | resolved | unresolved |
|---|---:|---:|
| Concept | 5,246 | 6,186 |
| Standard | 477 | 466 |
| Platform | 242 | 90 |
| Framework | 212 | 294 |
| Instrument | 173 | 329 |
| Tool | 58 | 204 |
| Claim / Practice | **0** | **0** |
| **total** | **6,408** | **7,569** |

## §5. The gold sample — 100 pairs, blind, scorer written first

`scripts/score_er_gold.py` was written and **tested against a synthetic sheet with known answers before the sampler ran** — 12 tests, every number hand-computable. A scorer authored after its inputs are visible is a scorer shaped by them.

`docs/research/2026-09-05_er_gold_sample.md`, seed **20260905**, 20 per stratum:

| stratum | what it is | population | weight | pipeline says |
|---|---|---:|---:|---|
| A | exact-name auto-links | 16,624 | 831.2 | match |
| B | prior clerical band, accepted | 45 | 2.25 | match |
| C | prior clerical band, rejected | 74 | 3.70 | no match |
| D | near-miss, cosine ∈ [0.70, 0.80) | 431 | 21.55 | no match |
| E | cross-arm pairs in terms this task **kept** | 915 | 45.75 | match |

**Stratum C's population is 74, not the 87 `different` decisions**, because 13 of the 87 name a term with no other member to pair the node against — a band decision is `(node, term)` and the gold question is about two *nodes*.

**Stratum E is where the control failure will show up.** It draws cross-arm pairs from terms the homograph pass kept — including `air:concept/ai-ready`, which the control says is homographic. If the pipeline is over-merging senses, E is the stratum that measures it, and it now carries a weight of 45.75.

The sheet shows **no cosine, no vocabulary term, no stratum and no pipeline decision** (verified: the only matches for those strings are the task filename and the instruction paragraph). Those live in `state/er_gold_key.json` and join at scoring time. The header states plainly that §2 wrote nothing and the pairs are pre-split.

**Scoring is the next dispatch, not this one.** The operator fills the sheet; `score_er_gold.py` then registers `er_gold_precision`, `er_gold_recall`, `er_gold_cluster_f1`, `er_gold_verdict` against the DD-045 §3 thresholds. Run against the unfilled sheet it reports 0 scored pairs and registers nothing, by design.

## §6. Premises this task got wrong

1. **"The 32 extra are 30 `Claim` + 2 `Practice` nodes, so RESULT §1.3's 'not one Practice carries a name' is false and the fix was label-gated."** Wrong twice over. Zero `Claim`/`Practice` nodes carry a name; the fix was property-gated; the cause is an unlabelled Cypher pattern binding 82 twins. §4.
2. **`homograph_cross_arm_nodes` is 1,660, not 1,666.** The 6-node gap is those same twins: members are read per `(term, label)`.
3. **Stratum C's population is 74, not 87.**
4. **The pre-registered thresholds do not transfer**, which the task could not have known: 0.80 was calibrated on a name-to-definition comparison and only 12 of 289 terms reach it here.
5. **`s` is undefined for 82 of 289 terms** and noise-dominated for 61 of the 79 auto-keeps. §1.1's provision for small arms lets a term reach a verdict on two members.
6. **§1.3 ("stop after §4") and §5 ("if §2 wrote nothing …") cannot both be literal.** I executed §3–§6 and said so.

## §7. Verification

| check | result |
|---|---|
| `python -m pytest tests/` | **845 passed** (832 + 13 new) |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** |
| `git diff` on `cq_set_v1.yaml`, `cq_set_v2.yaml`, `kg/schema.yaml` | **empty, all three** |
| model spend | **zero** |

**Registered.** 4 Scripts (`homograph_split`, `build_er_gold_sample`, `score_er_gold`, `register_homograph_results`); 4 DataFiles, all `snapshot: true`; **27 Results**; **DD-045** and **DD-046**; ERRATUM-01 on the prior RESULT.

## §8. Out of scope, untouched

CQ-27's schema gap (Issue `2a2b6461`) — a separate task, as the header says. The memo and the deck. Epoch 2. The 41 `no consumer` deferrals. Scoring the gold sheet.
