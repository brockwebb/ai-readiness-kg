# RESULT — 2026-08-30_ground_truth_yield_floor

**Re-derived floor: `5.16` admitted NODE items per chunk. All four arms meet it.**
**Production candidate: `v0_3_8` (Arm A2), selected on measurement.**

The pilot's §3 closure recorded 45.23/chunk as a tripwire from an unvalidated arm and mandated
this re-derivation before any further extraction arm. Done. Rubric written and sha-pinned before
any annotation; sample drawn, seeded and committed before any model call; **480,162 of 800,000
declared, 0 refusals, $3.98 over 12 calls.**

---

## The finding that reframes the whole floor saga: the target was 63% edges

| the comparator, over its own 44 chunks | per chunk |
|---|---|
| admitted **nodes** | **16.95** |
| admitted **edges** | **28.27** |
| **combined — the pilot's 45.23** | **45.23** |

**The rubric annotates items. It does not annotate relations at all.** So a yield floor stated
in nodes+edges is not commensurable with any ground truth a rubric of this kind can produce.
Three arms were designed against a target whose **majority component (62.5%) was never
comparable to the thing that would validate it.**

Restated on the node basis, the old target was **10.17/chunk**, not 27.14. Every figure below
is on the node basis, and I caught this only when the first scoring run produced numbers that
did not reconcile — it is recorded as a unit error in my own scorer, not as a discovery.

## Ground truth

| chunk | ground-truth items |
|---|---|
| `aidrin-hiniduma-2024#c0003` | **0** |
| `aidrin-hiniduma-2024#c0018` | **0** |
| `data-readiness…#c0012` | 14 |
| `data-readiness…#c0021` | 28 |
| `data-readiness…#c0024` | 1 |

**mean 8.60 · median 1 · range 0–28 · stdev 12.2.** `n = 5`, and the spread is reported instead
of a tighter-looking summary because the mean is not a stable quantity at this n.

**Re-derived floor = 0.60 × 8.60 = `5.16` node items/chunk** (old floor 27.14 combined-basis,
10.17 node-basis).

The two zeros are correct, not failures. `aidrin#c0003` is a keywords block plus an ACM
reference-format citation; `aidrin#c0018` is a pure references list; `#c0024` is one closing
sentence then a bibliography. **Both annotators independently returned nothing on all three** —
negative rules N6 (incidental proper nouns) and N7 (boilerplate) firing exactly as written.

## Inter-pass agreement: 0.942, no stop

| chunk | checklist | consumer | agreed | Jaccard |
|---|---|---|---|---|
| aidrin c0003 | 0 | 0 | 0 | 1.000 (empty–empty) |
| aidrin c0018 | 0 | 0 | 0 | 1.000 (empty–empty) |
| dr c0012 | 14 | 14 | 14 | 0.933 |
| dr c0021 | 27 | 24 | 25 | 0.893 |
| dr c0024 | 1 | 1 | 1 | 1.000 |

**Informative mean 0.9421** over the 3 chunks where either pass proposed anything; §3.4's stop
threshold is 0.50. Adjudication admitted 3 of 5 singletons on a cited rule; **0 unresolvable.**

### A defect in my own agreement metric, fixed before it fired falsely

My first implementation scored `Jaccard(∅, ∅)` as **0.0**. With three near-empty chunks in the
draw that would have dragged the mean to 0.59 and, on a slightly different sample, **fired
§3.4's incident stop on a rubric that was working perfectly.** Jaccard of two empty sets is 1 by
convention — two annotators who both find nothing in a bibliography agree completely. Empty–empty
chunks are also uninformative about whether the rubric is specified finely enough, so they are
excluded from the mean the threshold reads and reported separately.

**Recorded honestly: this was changed after seeing the per-pass counts and before seeing any
agreement value.** It cannot rescue a failing rubric — a mutation confirms the stop still fires
when the informative chunks disagree — but the sequencing is stated because it was a threshold's
measurement changing mid-task.

## All four arms against the re-derived floor

| arm | nodes/chunk (distinct) | raw nodes/chunk | recall | precision proxy | × floor | × ground truth |
|---|---|---|---|---|---|---|
| **v0.3.5 chunked** | 8.0 | 12.0 | **0.628** | **0.550** | 1.55 | 0.93 |
| Arm A (`v0_3_7`) | 7.6 | 9.6 | 0.419 | 0.500 | 1.47 | 0.88 |
| **Arm A2 (`v0_3_8`)** | **9.0** | 12.6 | **0.605** | 0.511 | **1.74** | 1.05 |
| Arm A3 (`v0_3_9`) | 8.6 | 11.8 | 0.558 | 0.465 | 1.67 | 1.00 |

**Every arm meets the re-derived floor**, by 1.47× to 1.74×.

### §4.3 — was v0.3.5's 45.23 over-extraction? On nodes, essentially no

**v0.3.5 sits at 0.93× ground truth on nodes.** It is not the wild over-extractor the floor saga
assumed. Its apparent supremacy is **edge volume**: 28.27 edges/chunk against 16.95 nodes.
`aidrin#c0018` is the clean demonstration — a pure references block where v0.3.5 emitted **0
nodes and 21 edges**, against a ground truth of 0 items. Those are `cites` edges, and a
bibliography does contain citations, so this is not fabrication; it is a component the rubric
cannot see and the floor silently counted.

**This retroactively explains the entire saga.** The arms were short of 45.23 mostly because they
emit far fewer edges, not because they miss items — Arm A2 emits 382 edges to v0.3.5's 1,244 on
the 44 chunks. A floor built on a combined count made an edge-volume gap look like an
extraction-quality gap, and three arms were designed to close it.

### §4.2 — A2 vs A3 head to head

| | Arm A2 | Arm A3 | winner |
|---|---|---|---|
| recall vs ground truth | **0.605** | 0.558 | **A2** |
| precision proxy | **0.511** | 0.465 | **A2** |
| Instrument containment recall (44 ch) | **0.905** | 0.888 | **A2** |
| $ per admitted item | **$0.00291** | $0.00335 | **A2** |
| `cites` layer defects (44 ch) | **5** | 37 | **A2** |
| admitted/chunk (44 ch) | 24.30 | **25.34** | A3 |
| faithfulness | 0.986 | **1.000** | A3 (1 item) |

**A2 wins five of seven, including both ground-truth measures.** A3's only material advantage is
1.04× admitted items, which the ground truth now shows is not a quality signal — A3's extra
items are less often justified (precision 0.465 vs 0.511).

**Production candidate: `v0_3_8`.** Selected by measurement, not recency — which the task
required precisely because A3 was the later arm.

## Verdict and limitations

**`v0_3_8` (Arm A2) is the production candidate at a re-derived floor of 5.16 node items per
chunk**, which it exceeds by 1.74×.

The limitations are large enough to state as part of the verdict, not beneath it:

1. **The ground truth is model-defined.** A stronger model (`claude-opus-5`) annotating under a
   rubric, in a different task posture from extraction, is not a human gold standard. It is a
   better-instrumented judgment than the 45.23 it replaces, which was no judgment at all.
2. **n = 5, and effectively n = 2.** Three chunks are references/boilerplate with ground truth
   0, 0, 1, so the arm comparison rests on **two informative chunks** (42 of the 43 ground-truth
   items). The floor's mean (8.60) is dominated by chunk-type composition, not by extraction
   difficulty.
3. **The sample is unrepresentative of its own comparator, measurably.** v0.3.5 admits 12.0
   nodes/chunk on these 5 against 16.95 across all 44 — the draw is 29% below the comparator's
   own average because it is reference-heavy. A sound floor needs **stratification by chunk
   type** (prose / table / references / front matter), which 5 chunks cannot supply.
4. **The floor cannot speak to relations at all.** Nothing here validates edge extraction, which
   is 63% of the old target and the whole of the arms' remaining gap.
5. **Corpus generalization is still owed.** These are 5 chunks from 2 documents of the pilot's
   5. The ADDENDUM-06 stratified held-out confirmation — 30 chunks, three document classes,
   documents no arm has touched — remains unrun and is inherited by the bulk task.

**Carried forward unchanged: the bulk task may not be written without burn-time acceptance
sampling** (ADDENDUM-06 §3; Dodge–Romig, Wald SPRT). A floor derived from 5 chunks licenses
starting a burn even less than a 44-chunk qualification did.

## Discrepancies reported, not reconciled

1. **§2 asks for one chunk per document across the pilot's five documents. The 44-chunk
   comparator set spans only two of them.** A five-document quota is not constructible, and
   drawing outside the comparator would make §4.3 (score v0.3.5 on the same chunks) impossible.
   Allocation is proportional to comparator coverage — 3 data-readiness, 2 aidrin — and the
   committed sample file carries the note.
2. **The rubric was to be compiled from `docs/crosswalk/` evidence cells.** Those cells are
   currently 25 resolved / 20 gaps and **nothing has been extracted into the graph yet** (the
   skeleton says so explicitly). The consumer rules are therefore derived from what the cells
   *declare they need*, not from observed query traffic. Stated in rubric §2.

## Prior art, and one convergence worth recording

Rubric §3 adapts three published guideline sets, each verified against its source rather than
recalled: **SciERC** (Luan et al. 2018) most-specific spans; **ACE 2005** SPC/GEN entity class,
where we *exclude* on genericity rather than tag it (divergence recorded); **TAC KBP** slot-fill
justification and no-outside-knowledge rules.

**TAC KBP's provenance rule — the span "must include some mention of the subject and object
entities and some text supporting the slot/predicate that connects them" — is independently this
repo's v0.3.4 semantic-edge rule** (`parser.py::_semantic_span_violation`), which was derived
from probe failures in August. The repo re-derived a published NIST guideline at full cost. That
is the §7.5 failure the standing doctrine names, found in our own history.

## Tests and mutations

Suite **436 → 440**. Ground-truth mutations **13/13 killed**; four survived a first pass:

| mutation | note |
|---|---|
| M85 draw not restricted to the comparator set | SURVIVED — sample tests read the committed **file**, not the draw |
| M86 sample seed ignored (draw re-rollable) | SURVIVED — same cause |
| M88 empty–empty scored as total disagreement | SURVIVED — test asserted only the informative mean |
| M91 floor kept the old 45.23 target | SURVIVED — nothing drove `phase_score`'s floor arithmetic |

**M85/M86 are the sixth instance in this project of a test measuring an artifact instead of the
generator that produced it.** Fixed by driving `phase_sample` against stubbed shards.

**A second bug caught by an impossible value:** Arm A3 scored `precision 1.091`. Containment
matching is many-to-one in both directions, and I had divided *ground-truth items matched* by
*arm item count*. Recall and precision now use separate numerators — ground-truth items found,
and arm items justified.
