# RESULT: 2026-10-04_views_regenerate — STOPPED at decision 2 (deck entangled with the pack); nothing applied

**Stopped at:** decision 2's own stop clause ("If the deck's guard is entangled with a pack guard such that one cannot pass without the other, stop and report"). The gate (`gate-fast`, `seldon verify`, protected-paths state) was run on the **reverted** tree. The full suite was not run because `gate-fast` was already red with nothing to ship. The reader gate was not run because no regenerated page exists. No generated file, test or generator was committed. The unapplied generator edit is kept at `logs/views_regenerate_generator.patch`.

## What happened
1. I edited `scripts/build_brief_pack.py` (decisions 3 and 4), regenerated with `build_brief_pack.py` and `build_l0_site.py`, and reviewed the diff. It held only the expected lines: B:16, C:17 `federal 94→95`, C:23 `all 264→265`, H:71, `numbers.json` (24→23, plus a new `48`), `docs/data/corpus_manifest.json` (the copy of `corpus/manifest.json`: included 264→265, pending_refetch 43→42, the Commerce entry), and `docs/data/index.json` (build_commit, plus the manifest's sha256 and bytes).
2. With that diff, `test_brief_deck.py` went from 1 red test to **12**: 4 failed and 8 errored. The deck renderer refuses: `DeckError: slide 7: quote not found in ['B_usafacts_delta.md']: 'Of 49 indicator nodes, 24 have a current rule…'`, and its narrative gate refuses `numeral '264' is on no page of chapter(s) ['C', …]`, `numeral '94' … ['C']` and `numeral '24' … ['B']`. `test_evidence_map.py::test_claims_file_regenerates_byte_for_byte` also failed, because `claims.yaml` → `q5_numbers_that_differ_from_the_pack` is computed from the pack ledger and loses its `pack: '24' / script: 23` row.
3. **Control: decision 1 alone** (generator reverted, pack and site regenerated) gives the same 12 deck reds through the narrative gate's '264' and '94'. The entanglement therefore comes from regenerating the pack at all, not from my two edits. I reverted everything.

## The 24s (before → proposed after; none applied)
- `docs/brief/B_usafacts_delta.md:16` and `numbers.json` B entry `indicators with a current rule in rules.CURRENT`: 24 → 23. The sentence would read: "Of 49 indicator nodes, 48 are the framework's; `A12` is a candidate, reported and held out of every framework count (`DD-054`). 23 of the 48 have a current rule in the registry."
- `docs/brief/appendix/rules.md` "of which 24 are current" counts **rules** (`len(set(rules.CURRENT.values()))`). That is correct, so it stays 24.
- Outside the write set, still saying 24 indicators: `docs/deck/brief_narrative.md:4,28` and `docs/deck/brief_deck_content.md:75`. `docs/figures/fig1…caption.md:4` already says 23.

## Page H sentence (H_limits.md:71)
- Before: "Both scoring schemes weight equally, following the OECD/JRC Handbook default for when no basis exists for other weights (`docs/design/scoring_model.md`)."
- Proposed: "Both scoring schemes weight equally because no basis for other weights exists (`docs/design/scoring_model.md`). The OECD/JRC Handbook notes that equal weighting is itself a weighting, not the absence of one, and that it can disguise the absence of a statistical or empirical basis (`docs/evidence/claims.yaml`, `CL-083`)."

## Gate (reverted tree; logs local under `logs/`)
- `gate-fast` (`logs/views_regenerate_gate_fast.log`): **5 failed, 2892 passed, 3 skipped, 27 deselected, 12 xfailed, EXIT=1**, in 674 s. These are the same 5 guards the task names, so this is the baseline and unchanged by this session.
- `seldon verify` (`logs/views_regenerate_verify.log`): All checks passed, EXIT=0.
- Protected paths (`logs/views_regenerate_protected.log`): the tree is clean except `seldon_events.jsonl`, which holds one line appended by the dispatcher. Write set used: this RESULT only.
- Reader gate: not run, since nothing was regenerated.

## Premises the task got wrong
1. Decision 2 assumed only the deck's byte-for-byte test is pinned. The deck's narrative and quotation gates check the deck's numerals and quotes against the **live** pack, so any pack regeneration (even 264 → 265 alone) breaks 12 deck tests.
2. "Byte-identical: `docs/evidence/`" conflicts with decision 3. `claims.yaml` records the pack-vs-script disagreement, so correcting the pack necessarily changes it through `build_evidence_map.py`.
3. Decision 3 says "24 is `len(set(rules.CURRENT.values()))`". Page B's 24 is actually `built`, the count of indicator rows (including candidate A12) with a current rule. It equals the rule count only because each indicator has exactly one current rule.
4. Decision 4 says `scoring_model.md:7` claims the default. It does not: it cites the Handbook's ten steps. The unsupported phrase is in `scripts/score.py:602` (the grid header "OECD/JRC 2008 default"), which reaches the pack through the captured output in `D_demo_capture.json` and `D_demo_runbook.md`. It also appears in `score.py:21` (docstring) and in the deck at `brief_narrative.md:12,62` and `brief_deck_content.md:455`.

## For the next task (recommendation, grounded in DN-009 d2)
Take the deck out of the gate the way DN-009 intends: retire `test_brief_deck.py` as a module, or xfail every deck test whose input is the pack. Do not mark only the byte-for-byte test. Put `docs/evidence/claims.yaml` (regenerated by its generator) in the write set. Re-capture `D` only if `score.py:602` is reworded. Then apply `logs/views_regenerate_generator.patch` and rerun from decision 1.

**Tokens and model:** claude-opus-5-5, under Max OAuth. No model call was made outside this session, and session tokens were not metered here (well under the 2M estimate).
