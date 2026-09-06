# RESULT: both write gates failed, nothing reached the vocabulary log — and one defect explains both

**Task:** `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md` §1–§6. **No addenda** — globbed before starting, none exist. **Date:** 2026-09-06 UTC. **Spend: 345,550 tokens settled** against a 9,000,000 stop; the paid pass was stopped early, deliberately, and §2 explains why. **Task file committed before execution** (`bd2600e`).

## Both controls, as §6 requires

| gate | outcome | |
|---|---|---|
| **§1.2 alias positive** | **FAILED** | 0 of 6 stratum-D gold pairs joined (needed ≥ 5) |
| §1.2 alias negative | **passed** | 0 violations over 33 stratum-C/D `different` pairs |
| **§2.3 homograph positive** | **FAILED** | `air:concept/ai-ready` → `distinct_senses` (0.78) ✓, **`air:concept/accessibility` → `same_sense` (0.72)** ✗ |

**Nothing was written to the vocabulary log.** No aliases, no splits, no epoch 2, no DCAT-US split, no Turtle re-export. §2.4 and §2.5 are therefore no-ops and the canonical CQ view is unchanged; epoch 1 stands.

**One defect explains the §2.3 failure and a quarter of the population, and it is the Issue §4 asked for.** `air:concept/accessibility`'s organisational-maturity arm holds **one node whose grounding span is the bare word**. The judge said so itself:

> *"Both evidenced arms denote obtainability of the data itself … while the organisa[tional]…"* — it could only compare the two arms that carried evidence.

The gold sample had independently measured that exact term as a **live false merge** (P089, P090). So the term is a homograph, a judge with evidence would likely have said so — `ai-ready`, whose arms do carry spans, was called correctly and for the right reason — and the split failed because the corpus does not carry the sentence.

## §1. Phase A — surface-form aliases (zero model spend)

139 aliases proposed, **none written**. Counterfactually they would have moved auto-links 6,518 → **6,583** (+65) and the residue 7,459 → 7,417.

| generator | proposed | | refusal | count |
|---|---:|---|---|---:|
| `schwartz_hearst` | 103 | | label theft | 305 |
| `generic_suffix_strip` | 15 | | label block | 62 |
| `version_strip` | 14 | | ambiguous target | 12 |
| `technical_specifications_variant` | 5 | | | |
| `determiner_strip` | 2 | | | |

**The negative control is clean — 0 of 33** — which is the half that matters most under DD-045 §3: a false merge is the expensive error and the generators proposed none.

**The positive control is 0 of 6, and the reason is not that the generators are weak.** Four of the six produce **no candidate form at all** from §1.1's rule set, because they are not the kind of variation §1.1 describes:

| pair | node A | gold term | blocker |
|---|---|---|---|
| P065 | `Agency inventory of AI use cases` | `ai-use-case-inventory` | **word reordering** |
| P075 | `Governance of data` | `data-governance` | **reordering with a preposition** |
| P073 | `subject protection` | `human-subject-protection` | **truncation** (prefix dropped) |
| P068 | `robots.txt exclusion protocol` | `robot-txt` | **multi-token domain suffix** (`exclusion protocol`) |
| P067 | `Resource Description Framework (RDF)` | `standard/rdf-resource-description-framework` | **duplicate terms** |
| P076 | `SDMx 2.0 Technical Specifications` | `standard/sdmx-technical-standard` | **duplicate terms** |

**P067 and P076 are the interesting pair, because the generators work and the vocabulary is what blocks them.** Schwartz–Hearst mines `(Resource Description Framework, RDF)` correctly from both the node name and the term label. But `rdf` is already claimed by **two** terms (`air:concept/rdf`, `air:standard/rdf`) while the gold counterpart sits in a **third** (`air:standard/rdf-resource-description-framework`); `sdmx` is claimed by `air:sdmx` while the counterpart sits in `air:standard/sdmx-technical-standard`. The label-theft guard correctly refuses to alias across them. **Epoch 1 contains duplicate terms for one thing, and joining these pairs needs a term-level merge** — explicitly out of scope in `0b8ea847` §7 and not authorised here.

So §1.1's five generators cover a variation class the gold sample's misses largely are not. That is a finding about the generator list, not about the idea: the prior art is right and the rule set was drawn too narrow.

### §1.2's third requirement — the unlabelled-Cypher lint

Added: `tests/test_cypher_unlabelled_lint.py` reads every Cypher string in `kg/` and `build_projection.py` and fails on any node pattern binding by property with no label and no `labels(...)` guard. It has a mutation test that must fail on the exact string that shipped twice.

It found **three latent instances** of the same defect — the `grounding_relocated`, `attribute_nulled` and `attribute_restored` overlay writes, all `MATCH (n {key: $key})`. **No overlay currently targets any of the 82 duplicate keys** (measured: 4,293 + 5,349 + 4,021 overlay events, zero collisions), so the defect is latent rather than active — but it is the same trap that cost two rebuilds, so all three are now guarded on the label set. One site is allowlisted with its reason: the edge-endpoint `MERGE (a {key: …})` cannot carry a label, because an endpoint may be a Document, any KG node, or a cited document never manifested.

## §2. Phase B — judged homograph pass (spends)

**Population: 212**, not the ~200 the task expected — 139 band + **73** auto_keep with an arm under three members. The premise's "61 of the 79 auto-keeps" is 61 of the **67** that reached auto-keep on the `s ≥ 0` limb; over all 79 auto-keeps the count is 73.

Calibration measured **31,393.5 tokens/term**, against the task's ~31.3k expectation.

### The gate fired in the calibration batch itself

Of the first 10 terms, 9 `same_sense` and 1 `uncertain` — and `air:concept/accessibility` was among them, returning **`same_sense`**. §2.3 makes that a stop: `homograph_judge_positive_control_failed = 1`, nothing written.

The second control was then judged specifically to complete §6's required report, and it **passes decisively**:

> `air:concept/ai-ready` → **`distinct_senses`, 0.78**: *"The organisational-maturity arm predicates the label of a person — 'When does a user become "AI-ready"?' — a state of human competence/calibration, whereas both other arms predicate it of a data artifact."*

That is the right answer for the right reason, on a term whose arms carry spans. **The judge works; the evidence does not.**

### Why the remaining 202 terms were not judged — a decision, stated

The §2.3 gate had fired, so no verdict from the remaining 202 could be written to the vocabulary log. Judging them would have cost **≈ 6.34M tokens for decisions that by rule cannot be applied**, and the compromising defect is measured to affect a quarter of that population: **54 of 212 terms have an arm with no usable span, and 45 have at most ONE evidenced arm**, where a cross-arm distinction cannot be drawn on evidence at all and rule 2 directs the judge to `uncertain`.

I stopped the paid pass after the second control. §2.3 says "nothing written"; it does not say "stop judging", so this is my call and not the task's. The distribution over all 212 would be genuinely useful to the next task, and if Desktop wants it, dispatching the same script with `--ceiling-tokens 7292711` completes it — the evidence-on-disk resume means the 11 already judged are not repaid. I judged the cost against a measurement I already knew was compromised for the class that constitutes the population, and against the fact that the Fable κ pass (§2.2) exists to gate a write that is no longer happening, so it was skipped too (a further ≈ 1.57M).

**Spend:** 313,935 (calibration, 10 terms) + 31,615 (second control) = **345,550 settled**. Declared ceilings 420,000 + 45,000.

**A reading of the spend rule I should flag.** §Spend says "expect ~6.3M … stop above 9M". At the measured rate the full Phase B would have settled ≈ 8.23M — under 9M — but the *sum of DD-042 ceilings* (420k + 7.29M + 1.81M) is **9.52M**, over it. The two readings disagree. I did not have to resolve it, because the gate fired first; if the full pass is dispatched later, that ambiguity needs settling.

## §2.4 / §2.5 — no-ops

Nothing written, so no epoch 2, no loader arm-keying change, no Turtle re-export, and `cq_set_v2.yaml` was rerun **not at all**: with the graph unchanged, a rerun would register a new dated set of Results identical to `2026-09-05`, which is exactly the kind of number DD-040 exists to prevent. The canonical view stands at the `cq_v2_*_2026-09-05` figures.

## §3. Regold allocation — registered, and it exposes an objective mismatch

`state/er_regold_allocation_2026-09-06.json`, registered as a `snapshot` DataFile with per-stratum Results. Computed **before epoch 2's numbers exist**; the draw belongs to the next task, seed 20260906.

| stratum | N | errors/scored | p | S | N·S | **n** |
|---|---:|---:|---:|---:|---:|---:|
| A exact-name auto-links | 16,624 | 0/19 | 0.500 | 0.500 | 8,312.0 | **188** |
| B band accepted | 45 | 0/20 | 0.500 | 0.500 | 22.5 | **1** |
| C band rejected | 74 | 1/20 | 0.050 | 0.218 | 16.1 | **0** |
| D near-miss | 431 | 6/20 | 0.300 | 0.458 | 197.5 | **4** |
| E cross-arm kept | 915 | 2/18 | 0.111 | 0.314 | 287.6 | **7** |
| F pairs this task changed | 0 | — | 0.500 | 0.500 | 0.0 | **0** |

**Applying the pre-registered rule literally puts 188 of 200 pairs into the stratum with zero observed errors, and none into stratum C.** That is arithmetically correct — Neyman (1934) minimises the variance of the **population** estimate, which stratum A dominates — and close to useless for what this regold is for, which is per-stratum precision where defects were measured. Cochran (1977) §5.5 gives the alternative: allocation for **domain** estimates. **The rule is followed and registered as written, not retuned after seeing its output**, and the mismatch is recorded in DD-047 §4 so the next task chooses the objective deliberately.

Stratum F is 0 because both write gates failed and nothing changed any node's resolution.

## §4. Issue — bare grounding spans

Registered **`e21b9ab3`** (`missing_content`, high/medium), linked `ANNOTATES` to `er_gold_escalations`, `concept_bare_span_count`, `concept_bare_span_share` and `homograph_judge_positive_control_failed`.

**1,561 of 11,432 Concept nodes (13.66 %)** carry a `grounding_span` identical to their `name`. It is now measured as a direct cause of failure at three gates, not a cosmetic complaint: all three gold `uncertain` verdicts were this class; the §2.3 control failed on it; and within the judged population 54 of 212 terms have an evidence-free arm.

Likely cause, not investigated here: the extractor emits a span equal to the surface form when the mention is a bare list item, heading or table cell. **Invariant 3 ("no grounding span, no write") is satisfied by a bare span**, so this is a quality floor the invariant does not yet enforce.

## §5. DD-047 — four rulings

1. **The DD-045 §3 PASS stands** and probe design is not blocked by it; the n_eff-21 caveat stands with it.
2. **The per-stratum defects (E precision 0.889, D recall 0.000) are sequenced ahead of probe design** — enumeration probes read the quality-dimension vocabulary the E failures sit in. Sequencing, not a new gate.
3. **The embedding homograph detector is retired for classification**, used only to define a judged population. Any future detector is calibrated on its own null first.
4. **The regold is epoch 2's acceptance measurement**, allocation fixed before its numbers exist — with the objective mismatch above recorded.

## §6. Premises this task got wrong

1. **"61 of the 79 auto-keeps have an arm with < 3 members"** — 61 is of the 67 on the `s ≥ 0` limb; over all 79 it is **73**, and the population is **212**, not ~200.
2. **The §1.2 positive control was unreachable by the §1.1 generator list.** Four of the six target pairs yield no candidate form from any of the five named generators, and two are blocked by duplicate terms rather than by generation. The control was set at 5 of 6 against a rule set that could address at most 2.
3. **"1,561 of 11,432 Concept nodes carry `grounding_span` == `name`"** — verified exactly, 13.66 %.
4. **The `stop above 9M` rule is ambiguous** between expected settle (8.23M, under) and the sum of DD-042 ceilings (9.52M, over). Unresolved because the gate fired first.
5. **§2.2's "no context available for this arm"** was implemented as declaring the absence *and still naming the arm's document titles* — a title is not the bare word, and it is demonstrably the evidence the gold rater used to judge the MITRE node. Had I suppressed the title too, the control would have failed for a reason I introduced.
6. **The task expected §2.5 to produce canonical CQ deltas.** With nothing written there is nothing to compare, and registering an identical dated rerun would manufacture the kind of number DD-040 forbids.

## §7. Verification

| check | result |
|---|---|
| `python -m pytest tests/` | **878 passed** (845 + 33 new) |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** |
| `git diff` on `cq_set_v1.yaml`, `cq_set_v2.yaml`, `kg/schema.yaml`, `er_gold_key.json`, the 100-pair sheet | **empty, all five** |
| vocabulary log | **unchanged** — no alias, no split, no epoch 2 |

**Registered.** 5 Scripts; 4 DataFiles, all `snapshot: true`; **23 Results**; **DD-047**; Issue `e21b9ab3`.

## §8. What the next task inherits

* **Two write gates failed for two different reasons**, and neither is "the idea was wrong". The aliases need a wider generator class — reordering, truncation, multi-token domain suffixes — plus a term-level merge pass for the duplicate-term blockers. The homograph judge needs **spans**, which is Issue `e21b9ab3`.
* **Fixing the bare spans is upstream of both** and of the regold: it is the single defect that broke the §2.3 control, produced every gold `uncertain`, and leaves 45 of 212 terms with at most one evidenced arm.
* **The regold allocation is registered but its objective is arguably wrong** (DD-047 §4). Choosing between population and domain allocation is a decision, not a computation.

**Out of scope and untouched:** CQ-27's schema gap (Issue `2a2b6461`), the 41 `no consumer` deferrals, the memo and the deck, term-level merges, and every threshold in `0b8ea847` §1.2 and DD-045 §3.
