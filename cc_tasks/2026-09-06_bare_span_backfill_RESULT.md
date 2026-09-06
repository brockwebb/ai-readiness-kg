# RESULT: 1,773 bare spans backfilled to 78 — and the control still fails, for the opposite reason

**Task:** `cc_tasks/2026-09-06_bare_span_backfill.md` §1–§6. **No addenda** — globbed before starting, none exist. **Date:** 2026-09-06 UTC. **Spend: 63,945 tokens settled** (two terms) against a **150,000 settled stop**. **Task file committed before execution** (`6f7bdfd`).

## The two control verdicts, and the MITRE span before and after

| term | before backfill | **after backfill** |
|---|---|---|
| `air:concept/accessibility` | `same_sense` (0.72) | **`same_sense` (0.70)** — §4 gate **FAILS** |
| `air:concept/ai-ready` | `distinct_senses` (0.78) | **`distinct_senses` (0.76)** — regression control **passes** |

**`mitre-ai-maturity-model::d-accessibility`, verbatim:**

> **before:** `Accessibility`

> **after:** `Maturing the Data Pillar Maturing the Data Pillar from the initial awareness to Level 2 includes researching and considering data-related activities such as governance, accessibility, sharing/access controls, architecture, and security, as well as identifying iInitial data. By Level 3, the entity should have a defined process for governance , and auditing compliance for to data standards.`

**The gate fails, and the failure has inverted.** Before, the judge could not see the organisational-maturity arm at all and said so. Now it reads that span and reaches a *substantive* conclusion — that MITRE's "governance, accessibility, sharing/access controls" as **data-pillar activities** is:

> *"the same data property viewed from the organisation's maturing angle rather than a separate organisational capability"*

**That contradicts the ER gold label.** The gold rater called P089/P090 `different` — *"Node A's bare 'Accessibility' in an AI maturity model context is an organizational-capability dimension"* — a judgment formed from the **document title**, because the span was empty. With the span supplied, the text does not obviously support that reading: MITRE lists accessibility among *data* activities, not among organisational capabilities.

**Which reading is right is not settled here, and more model calls will not settle it.** The disagreement is now between two readings of the same visible evidence rather than between a reading and an absence — which is a strictly better place to be, and is the honest outcome of supplying the evidence. Per §4 the overlays are **not reverted**: they are correct on their own terms. `ai-ready` holding at `distinct_senses` confirms the backfill did not degrade a term that already worked.

## §1. The census — measured before touching anything

| | |
|---|---:|
| named nodes examined | 13,977 |
| **bare spans** (`span` == `name`) | **1,773** |
| bare share | 12.69 % |
| documents contributing | 138 |

| label | bare | of | share |
|---|---:|---:|---:|
| Concept | 1,566 | 11,432 | 13.70 % |
| Standard | 81 | 943 | 8.59 % |
| Framework | 77 | 506 | **15.22 %** |
| Platform | 24 | 332 | 7.23 % |
| Tool | 13 | 262 | 4.96 % |
| Instrument | 12 | 502 | 2.39 % |

**The premise's 1,561 is the `Concept` count alone** (1,566 measured here); across all six labels that carry a `name` it is **1,773**. `Claim`, `Definition`, `Measure` and `Practice` carry no `name` at all, so "span equals name" is undefined for them and they are reported as not-applicable rather than as a clean zero.

**The concentration is the useful part.** `mitre-ai-maturity-model` — the document at the centre of the §2.3 control failure — is **41 of 50 named nodes bare (82 %)**, and `ai-real-toolkit-ai-readiness-assessment-guide` is 46 of 63 (73 %).

### What `location` turned out to encode

**A model-authored heading path, in free text.** `prompt_template_v0_3_8.md` requires a `location` on every node and edge and **never defines its format**, so the model writes what it likes: `Stages of the journey > Readiness`, `Introduction`, `title/intro`, `DIME PROJECT banner`. Distribution over the 1,773 bare-span nodes: 1,328 single heading, 277 positional, 96 numeric, 48 heading path, 24 prose.

It is not an offset and not a stable section id. §2 therefore uses it **only to disambiguate** between candidate matches of the name, and a `location` matching nothing can never lose a match a plain phrase search would have found — asserted by a test.

## §2. The backfill

| | |
|---|---:|
| **backfilled** | **1,695** (95.6 %) |
| unlocatable | 32 |
| name absent after widening | 36 |
| still thin after widening | 10 |
| **remaining bare** | **78** |
| **bare share after** | **0.56 %**, from 12.69 % |

Block kinds: 1,560 paragraph, 87 list item, 32 heading extended into the block below, 16 table row.

**One defect found by running it, and it is instructive.** The first pass produced only 542 backfills and **1,190 `name_absent`** — because my window truncated from the block's *start*, so any mention past 400 characters was cut out of its own span. That is not KWIC at all: Luhn's construction is keyword **in** context, a window **centred** on the mention. Corrected, with a test that fails on the old behaviour, and `name_absent` fell 1,190 → 36. The failure was concentrated in PDF-derived text, where a "paragraph" can be a whole page.

**Provenance is intact.** All 1,695 are `grounding_relocated` overlays — PROV-O `prov:wasRevisionOf`, the bare span retained on the log — and a labelled count confirms **`prov_extraction_event_id` is present and unchanged on all 1,695**. No extraction event was rewritten.

## §3. Invariant 3's floor

A span must carry **≥ 8 tokens or ≥ 3 tokens outside the node's name**; one that does not is flagged `grounding_thin: true`. **991 nodes are flagged** after the backfill. It is an annotation, never a deletion — the extraction event stands and the node stays queryable.

Tested with fixtures for a bare heading, a list bullet, a table cell, a legitimate long span — and **`RDF 1.1` against the name `RDF`, which is flagged**. That is the floor's recorded cost, kept: thinness is exactly what it measures, and carving an exception for short standard names would make the floor unfalsifiable.

The floor is computed **after** overlays are applied, so a node the backfill just repaired is not flagged for the span it used to have — a second test pins that.

## §5. DD-048 — four rulings

1. Bare spans are an extraction quality defect, remediated by deterministic KWIC backfill as overlays; extraction events are never rewritten. Prior art: Luhn (1960), CommonMark §4–5, PROV-O `wasRevisionOf`.
2. Invariant 3 gains the §3 floor; thin spans are annotated, never dropped.
3. **The regold objective is domain (per-stratum) precision, not population precision.** DD-047 §4's Neyman table put 188 of 200 into the stratum with zero observed errors, because Neyman minimises the variance of the *whole-corpus* estimate and stratum A's N of 16,624 dominates it. Cochran (1977) §5.6 gives `n_h ∝ S_h`:

   | stratum | Neyman (superseded) | **Cochran §5.6** |
   |---|---:|---:|
   | A exact-name auto-links | 188 | **52** |
   | B band accepted | 1 | **45** (its entire population) |
   | C band rejected | 0 | **22** |
   | D near-miss | 4 | **48** |
   | E cross-arm kept | 7 | **33** |
   | F next task's changes | 0 | 0 |

   Registered as `er_regold_allocation_2026-09-06b`; the DD-047 table stays registered as the superseded design. **The draw is still not made**; seed 20260906.
4. **The spend stop rule is settled tokens**, resolving `230b282f` §6.4. DD-042 ceilings are declared budgets whose headroom exists so a run does not halt mid-pass; summing them against a spend stop would forbid runs that never spend the money.

## §6. Premises this task got wrong, and mistakes I made

1. **"1,561 of 11,432 `Concept` nodes"** understates the population: it is the Concept count alone. Across all six named labels it is **1,773**, and `Framework` has the highest share (15.2 %), not Concept.
2. **My KWIC window was not KWIC.** Truncating from the block start dropped the mention from its own span and cost 1,190 nodes on the first pass. Found by the §2.5 name check, fixed, tested.
3. **I picked shard 27 as "the next free one" and it was not free** — it already held 4 `manifest_add` events, so the 1,695 relocations sit beside them. Harmless (mixed event types per shard are normal here) and unfixable in the right direction, because the log is append-only and moving them would mean deleting them. Recorded rather than tidied.
4. **I left a `pgrep -f "[b]uild_projection"` wait loop matching its own command line**, so it never exited and I ran a 31-minute rebuild that predated the §3 patch and could not produce the final state. Killed and re-run on the final code; waits are now keyed on PID.
5. **`regold_allocation.py` raised `ValueError` on a relative `--out` after writing its JSON** — `relative_to` against an absolute REPO, the same defect class fixed in `extraction_gap_diagnostic.py` on 2026-09-04. Fixed with `.resolve()`.
6. **The first domain allocation summed to 201, not 200** — rounding can overshoot as easily as undershoot. A trim step was added before the top-up.
7. **The §4 gate failed**, and the task anticipated that outcome. What it did not anticipate is that the failure would *invert*: the judge now disagrees with the gold label on the evidence rather than for want of it.

## §7. Verification

| check | result |
|---|---|
| `python -m pytest tests/` | **900 passed** (878 + 22 new) |
| `python -m pytest assessment/` | **471 passed, 1 skipped** |
| `seldon verify` | **All checks passed** |
| `git diff` on both CQ yamls, `kg/schema.yaml`, `er_gold_key.json`, the 100-pair sheet, the vocabulary shard `batch-026` | **empty, all six** |
| `prov_extraction_event_id` on relocated nodes | **1,695 of 1,695 present**, labelled count |
| bare spans | 1,773 → **78** |

**Registered.** 3 Scripts; 6 DataFiles, all `snapshot: true`; **22 Results**; **DD-048**.

## §8. What this leaves

* **Issue `e21b9ab3`'s cause is remediated** — 95.6 % of bare spans now carry context — but the Issue itself should stay open until someone decides whether the remaining 78, the 991 thin spans, and the extractor behaviour that produced them are acceptable. This task did not close it.
* **The `accessibility` disagreement is now a human question**, and a small one: read the MITRE AI Maturity Model's data-pillar section and decide whether its "accessibility" is the data property or an organisational capability. That is one document and one paragraph, and it decides whether the ER gold label or the judge is wrong — which matters because stratum E's precision (0.889) rests on those two pairs.
* **The full Phase B homograph pass is now runnable on evidence.** 212 terms at ≈ 31.4k tokens each; the class that made it unreliable — an arm with no usable span — has shrunk from 54 terms to whatever survives among the 78.

**Out of scope and untouched:** aliases, term merges, the homograph population beyond the two control terms, CQ-27's schema gap (`2a2b6461`), the memo and the deck, epoch 2.
