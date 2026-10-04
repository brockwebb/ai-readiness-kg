# RESULT: 2026-10-04_views_regenerate_v2 — STOPPED at decision 4 (one unexpected diff line); decision 2's mark as written cannot meet decision 5; nothing applied

**Stopped at:** decision 4, "Any other change stops the task before commit". Regeneration also moved `docs/brief/E_architecture.md:74`. Decision 2's stop clause did not fire: no test besides `test_brief_deck.py` imports the deck renderer. Everything was measured on the regenerated tree, then reverted. Ships: this RESULT and `scripts/check_protected_views_regenerate_v2.sh`. Kept unapplied under `logs/`: `views_regenerate_v2_regenerated.patch` (the generator patch plus every regenerated file) and `views_regenerate_v2_deck_mark_runfalse.patch`.

## Diff summary by file (regenerated tree, generators only: `build_brief_pack.py`, `build_l0_site.py`, `build_evidence_map.py`)
- Expected, as v1 enumerated: `B:16`, `C:17` (federal 94 → 95), `C:23` (all 264 → 265), `H:71`, `numbers.json` (24 → 23, plus the new `48`, "indicators not held out as candidates"), `docs/data/corpus_manifest.json`, `docs/data/index.json`.
- **Unexpected:** `E_architecture.md:74`, `build_projection.py: KG labels` changes from `scripts/build_projection.py:468` to `:587`. It is a symbol locator (`sym(..., "build")`, `build_brief_pack.py:867`). Commit `141534d1` (2026-10-04 17:01, definition pairs completion) moved `build()` after the v1 run (`2803051b`, 14:53). The pack at HEAD is already stale on this line, so `test_brief_pack` cannot go green without it.
- `docs/evidence/claims.yaml`: the one expected change. Its full diff:
  ```
  -  q5_numbers_that_differ_from_the_pack:
  -  - number: indicators with a current rule
  -    pack: '24'
  -    pack_source: 'B_usafacts_delta.md: indicators with a current rule in rules.CURRENT'
  -    script: 23
  +  q5_numbers_that_differ_from_the_pack: []
  ```

## Decision 2 as written fails decision 5
The dictated line `pytestmark = pytest.mark.xfail(strict=True, reason=…)` applied: **13 failed, 12 xfailed** (`logs/views_regenerate_v2_deck_probe.log`). 13 deck tests do not read the pack, for example the framework-deck refactor test and the gates that refuse a typed number. They pass, so strict mode reports them as `XPASS(strict)` failures. Adding `run=False` (the module is retired, so not run) gives **25 xfailed, 0 failed**.

## Gate
- **Full suite, regenerated tree + `run=False` mark** (`logs/views_regenerate_v2_suite_regenerated.log`): **2910 passed, 0 failed, 3 skipped, 0 deselected, 37 xfailed (12 baseline + 25 deck), EXIT=0**, 2409 s. All 5 regenerate-and-compare guards pass.
- **gate-fast, reverted tree = HEAD** (`logs/views_regenerate_v2_gate_fast_reverted.log`): **5 failed, 2903 passed, 3 skipped, 27 deselected, 12 xfailed, EXIT=2**, 715 s. These are the baseline 5 (`test_brief_deck`, `test_brief_pack` ×2, `test_g4_resourcing_reissue`, `test_publication`).
- `seldon verify` (`logs/views_regenerate_v2_verify.log`): All checks passed, EXIT=0. Protected paths (`logs/views_regenerate_v2_protected.log`): PASS, EXIT=0.

## Deck lines still carrying 24, 264 or 94 (left untouched, for the removal task)
`docs/deck/brief_narrative.md:4` (24 with a current rule; corpus of 264), `:12` (corpus is 264; "scoring default is the OECD/JRC Handbook's"), `:28` (24 indicators have a current rule), `:34` (264 documents admitted), `:38` (federal 94 admitted); `docs/deck/brief_deck_content.md:75` (quotes B: 24). The 24s at `brief_deck_content.md:498` (rules) and `brief_narrative.md:66` (specified only) are correct.

## Reader gate (fresh subagent; read only regenerated H, B and their diff; run on the unshipped tree)
"On B, the line about indicator counts now says 48 of the 49 indicator nodes are the framework's, with `A12` a held-out candidate under DD-054, and the rule count drops from "24" to "23 of the 48"; on H, the equal-weights sentence no longer credits the choice to an OECD/JRC Handbook default but says "because no basis for other weights exists" and adds a Handbook paraphrase (via `CL-083`). Several changed claims outrun the page: "held out of every framework count" is contradicted two sentences earlier on B by "0 are verbatim, 27 restated and 22 n/a", which sums to 49 and counts A12, "5 carry a departure quote" leaves its base unstated, and on H "no basis for other weights exists" is unqualified, and the Handbook sentence cites only an internal claims id with no page or quotation. Rewording is needed: on B, recompute that tally over 48 or say it covers all 49 and write "5 of the 49/48"; on H, say "this project has no basis for other weights" and quote the Handbook verbatim with its page beside `CL-083`." (Trimmed for length. The reader also flagged H's unchanged "each body's rank rests on a single leg": its table shows only 4 of 13 bodies resting on one pass.)

## Premises wrong
1. Decision 4's expected-diff list was v1's diff carried forward. `141534d1` landed between the two runs and moved a locator the pack prints.
2. Decision 2's `strict=True` module mark assumed every deck test fails after regeneration. 13 of 25 pass.
3. Decision 5's "deck module reporting as xfailed" is reachable only with `run=False` (or per-test marks), not with the dictated line.

## For v3 (grounded in this run's measurements)
Apply `logs/views_regenerate_v2_regenerated.patch`, or the generator part and rerun the three generators. Add `E:74` to the expected diff. Mark the module `xfail(run=False, strict=True, …)`. Decide whether page B's held-out wording and `B:16`'s "5 carry" are reworded per the reader before shipping, since the patch's "held out of every framework count" is false on its own page.

**Tokens and model:** claude-opus-5-5 under Max OAuth. One subagent call (reader gate, about 65k tokens). No other model calls. Well under the 2M estimate.
