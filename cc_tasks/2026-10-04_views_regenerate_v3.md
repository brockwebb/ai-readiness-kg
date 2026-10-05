# CC Task: regenerate the manifest views, v3, applying the measured patch, the reader's rewordings, and one false sentence on page H

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-10-04_views_regenerate_v2_RESULT.md` (task `acfb372d`, stopped at decision 4 on one unexpected diff line). That run measured everything: the regenerated tree with the module mark `xfail(run=False, strict=True, …)` gives the full suite **2910 passed, 0 failed, 37 xfailed**; the one unexpected line, `E_architecture.md:74`, is a symbol locator that moved when `141534d1` relocated `build_projection.build()`; and the reader gate found three wording defects in the regenerated pack. The patch is saved at `logs/views_regenerate_v2_regenerated.patch`. This task applies it with the wording fixed at the generator, and nothing is measured a third time that v2 already measured.
**Implements:** DN-009 decisions 2, 3 and 7; closes tracking record `9f2026e3`.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-04_views_regenerate_v2.md`
**Spend:** est. 2M tokens (Opus). One patch, three generator edits, three generators, the suite; no model call outside the reader gate.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Apply the v2 patch's generator part** to `scripts/build_brief_pack.py`, then make the three wording changes below in the same generator, then run `build_brief_pack.py`, `build_l0_site.py` and `build_evidence_map.py`. No hand edit of any generated file.

2. **Page B, the held-out sentence.** v2's proposed line says A12 is "held out of every framework count", and two sentences earlier the same page tallies "0 verbatim, 27 restated, 22 n/a", which sums to 49 and includes A12. Make the page consistent at the generator: either compute that tally over the 48 and say so, or keep 49 and say the held-out rule applies to the rule and score counts, naming them. Give "5 carry a departure quote" its base ("5 of the 48" or "of the 49", whichever the generator computes). State in the RESULT which you did and why.

3. **Page H, the weighting sentence.** Replace "because no basis for other weights exists" with "because this project has no basis for other weights". Beside the `CL-083` reference, quote the Handbook under 15 words with its page, taken from `claims.yaml` `CL-083`'s evidence entry; if that entry carries no page, cite the section and say so.

4. **Page H, the single-leg sentence.** "each body's rank rests on a single leg" is false on H's own table, which shows 4 of 13 ranked bodies resting on one pass. Compute the count at the generator and print it: how many of the ranked bodies rest on one pass, and which. The design notes (DN-009 d3, DN-010) that repeat the "single leg" phrasing are not in this write set; list the lines in the RESULT for a wording task.

5. **The deck's guards, retired, not run.** `tests/test_brief_deck.py`: `pytestmark = pytest.mark.xfail(run=False, strict=True, reason="DN-009: deck rejected 2026-10-02; pinned at the 264-document corpus until removed")`. Nothing under `docs/deck/` is touched.

6. **Expected diff**, and nothing else: `B:16` and whatever lines decision 2 moves on B, `C:17`, `C:23`, `E:74` (the locator), `H:71` and the single-leg line, `numbers.json` (24 → 23, the new 48, and any count decisions 2 and 4 add), `docs/data/corpus_manifest.json`, `docs/data/index.json`, the L0 site outputs the generator owns, and `claims.yaml`'s `q5_numbers_that_differ_from_the_pack` emptying. Any other line stops the task before commit; the RESULT names it with its cause, as v2 did.

7. **Pass criterion:** full suite at 0 failed, deck module xfailed and not run, `seldon verify` green, protected paths green.

8. **Reader gate (DN-009 d7).** A fresh subagent reads only regenerated pages B and H and writes three sentences on whether any sentence on either page is contradicted by the same page or by its own table. If it finds one, the task stops before commit and reports it.

**Write set:** `scripts/build_brief_pack.py`, `docs/brief/` (generated files only), `docs/data/corpus_manifest.json`, `docs/data/index.json`, the L0 site outputs, `docs/evidence/claims.yaml` (generator output only), `tests/test_brief_deck.py` (the module mark only), the protected-paths script, the RESULT. Byte-identical: `docs/deck/`, `docs/catalog/`, `docs/figures/`, `docs/design/`, `framework/`, `corpus/`, `events/`.

**Immutable once written.**

## Gate and report
Full suite, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-04_views_regenerate_v3_RESULT.md`, under 50 lines: the diff by file; the three wording changes before and after; the single-leg count and which bodies; the design-note lines still saying "single leg"; the gate counts; the reader gate's three sentences; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** patch → three generator edits → regenerate → diff against decision 6 → module mark → full suite to 0 failed → reader gate → RESULT → push.
