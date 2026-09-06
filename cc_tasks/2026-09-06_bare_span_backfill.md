# CC Task — Backfill bare grounding spans from the corpus; re-judge the two homograph controls

**Date:** 2026-09-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-06_aliases_homograph_judge_epoch2_RESULT.md`)
**Follows:** `230b282f` (completed, both write gates failed). Resolves Issue `e21b9ab3`'s cause; does not touch aliases, term merges, or the homograph population beyond two control terms.
**Premise (from the RESULT and the graph, 2026-09-06):**
- 1,561 of 11,432 `Concept` nodes (13.66%) have `grounding_span` == `name`. Invariant 3 ("no grounding span, no write") is satisfied by a bare span, so the floor was never enforced.
- `air:concept/accessibility`'s org_maturity arm is one node, `mitre-ai-maturity-model::d-accessibility`, bare span. Judge returned `same_sense` (0.72) for lack of evidence; the gold rater, given the document title, called it a false merge (P089, P090).
- `grounding_relocated` is an existing overlay event type with a labelled write path (fixed in 230b282f §1.2). Corpus text is manifested under `corpus/` (`manifest.json`); every KG node carries `doc_id` and `location`.
- Judge rate measured 31,393.5 tokens/term.
**Spend:** §1–§3 zero model spend. §4 judges exactly two terms: ceiling 90,000, **stop above 150,000**. Claude Max OAuth only; `ANTHROPIC_API_KEY` in the environment is a STOP. **Stop rule, resolving 230b282f §6.4:** the stop applies to *settled* tokens; DD-042 ceilings are declared budgets and their sum is not the stop.
**Zero edits to:** extraction outputs (`prov_extraction_event_id` chains stay intact — spans are relocated by overlay, never rewritten in place), both CQ yaml files, `kg/schema.yaml`, the vocabulary log, `state/er_gold_key.json`, the 100-pair sheet.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-06_bare_span_backfill_ADDENDUM*.md` before starting.**

---

## 0. Prior art (record in DD-048 with §5)
- **Keyword-in-context windows:** Luhn (1960), "Key word-in-context index for technical literature", *American Documentation* 11(4). The span is the mention plus its bounded context, not the mention.
- **Structural-unit segmentation for markdown/HTML corpora:** list item, heading, table cell, paragraph — the units the extractor evidently emitted bare. Segmentation on markdown block structure (CommonMark spec §4–5) is deterministic.
- **Provenance:** PROV-O `prov:wasRevisionOf` semantics — the relocated span is a revision of the bare one, with the bare one retained in the event log. This is what `grounding_relocated` already implements.

## 1. Measure before touching (zero spend)
Register, from a labelled property-gated query:
- `bare_span_nodes_by_label` — bare spans per label (Concept expected 1,561; report Standard, Instrument, Framework, Platform, Tool, Practice, Claim too).
- `bare_span_docs` — documents contributing bare spans, and the top 20 by count. Register the top-20 table as a snapshot DataFile.
- `bare_span_location_kinds` — the distribution of `location` values for bare-span nodes (offset? section id? heading path?). **Read the extractor's `location` semantics from the code, not from the RESULT's guess.** Report what `location` actually encodes; this decides §2's locator.

## 2. Backfill — deterministic, no model
For each bare-span node:
1. Load the manifested text for `doc_id` via `corpus/manifest.json` (never a URL fetch).
2. Locate the mention: by `location` if it resolves to a position; else the first case-insensitive whole-phrase match of `name`; if none, the first match of the name's stemmed token set within a single block. No match → leave bare, count as `bare_span_unlocatable`.
3. Span = the smallest markdown block containing the mention (list item, table row, paragraph, heading). If that block is the heading alone or is ≤ 6 non-name tokens, extend to the heading **plus the first sentence of the following block**. Hard bounds: **≥ 8 tokens total, ≤ 400 characters**; truncate at a sentence boundary when over.
4. Write one `grounding_relocated` overlay event per node: `{node key, label, old_span, new_span, locator: <how it was found>, block_kind, doc_id, char_range, derivation: "kwic_backfill_v1"}`. Labelled `MATCH`, as the lint now requires.
5. A node whose new span would be **identical to another node's span in the same document** is fine (two mentions in one block); a node whose new span does not contain its `name` (after stemming) is a defect — leave bare, count as `bare_span_name_absent`.

Register `bare_span_backfilled`, `bare_span_unlocatable`, `bare_span_name_absent`, `bare_span_remaining`, and `bare_span_share_after`. Rebuild the projection.

## 3. Invariant 3 gets a floor
Add to the loader/validator: a grounding span must contain ≥ 8 tokens **or** ≥ 3 tokens not in the node's `name`. Bare spans that survive §2 are flagged `grounding_thin: true` (an annotation, not a deletion — the extraction event stands). Test with fixtures for: bare heading, list item, table cell, and a legitimate short span (`"RDF 1.1"`, which must **not** be flagged when the name is `RDF`... it will be, at 2 tokens; record that as the known cost and keep the floor — thinness is what it measures).

## 4. Acceptance — the control that failed, re-run on evidence (spends)
Judge exactly two terms with the 230b282f §2.2 prompt, unchanged, on the backfilled spans, hermetic cwd:
- `air:concept/accessibility` — expected `distinct_senses`. The MITRE node's new span should now say what an "Accessibility" maturity dimension is.
- `air:concept/ai-ready` — expected `distinct_senses` again (regression: the backfill must not have degraded a term that already worked).
Register `homograph_control_accessibility_after_backfill` and `homograph_control_ai_ready_after_backfill` with verdict and confidence. **Gate: both `distinct_senses` → §5 records the backfill as accepted. Either fails → record it, do not revert the overlays (they are correct on their own terms), and state in the RESULT what the judge saw** — quote the MITRE node's new span verbatim.
No other term is judged. No split is written. Epoch 1 stands until the full Phase B is re-dispatched on the backfilled graph.

## 5. DD-048 — rulings
1. Bare spans are an extraction quality defect, remediated by deterministic KWIC backfill as overlays; extraction events are never rewritten.
2. Invariant 3 gains the §3 floor. Thin spans are annotated, never dropped.
3. **Regold allocation objective is domain (per-stratum) precision, not population precision.** Replace the Neyman table with Cochran §5.6 allocation, n_h ∝ S_h, using the same S_h and p = 0.5 rule from 230b282f §3, 200 pairs, six strata (A–F; F's N is whatever the next write task changes). Register it as `er_regold_allocation_2026-09-06b` (snapshot DataFile + per-stratum Results). The 230b282f table stays registered as the superseded population-objective design. **The draw is still not made here.**
4. Spend stop rule = settled tokens (this task's header).

## 6. Reporting
RESULT: `cc_tasks/2026-09-06_bare_span_backfill_RESULT.md`. Lead with the two control verdicts and the MITRE node's before/after span verbatim, then the backfill counts by label and the remaining bare share, then what `location` turned out to encode. State every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, `git diff` empty on the protected files, and a labelled count proving `prov_extraction_event_id` is unchanged on every backfilled node. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → rebuild → §3 → §4 → §5 → §6. §5.3 (regold allocation) runs regardless of §4's outcome.
