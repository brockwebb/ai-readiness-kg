# CC Task: regenerate the manifest views the Commerce admission broke, and apply the two pack corrections the evidence map found

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session. Since the Commerce admission (`381b8651`) the suite is red on 5 regenerate-and-compare guards: `test_brief_deck`, `test_brief_pack` ×2, `test_g4_resourcing_reissue`, `test_publication`. Each embeds the corpus manifest, which moved 264 → 265. Three later tasks reported the same 5 and could not touch them, because `docs/brief/`, `docs/deck/` and `docs/data/` were protected. The operator's standing position (DN-009): the deck is rejected and goes away once the report exists; the pack is the fact base of the one-page summary. A fact base that disagrees with the evidence map it feeds is the failure DN-009 was written against, so the pack and the site are regenerated and the deck is not.
**Implements:** DN-009 decisions 2 and 3; closes tracking record `9f2026e3` (the 24 → 23 correction).
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 2M tokens (Opus). Generators and diffs; no model call outside the reader gate.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Regenerate the pack and the site, by their generators only.** `scripts/build_brief_pack.py`, `scripts/build_l0_site.py`, and whatever writes `docs/data/corpus_manifest.json` and `docs/data/index.json`. Widen the protected-paths check to exactly the files those generators own. No hand edit of any generated file.

2. **The deck is not regenerated.** DN-009 rejected it. Mark `test_brief_deck` `xfail(strict=True, reason="DN-009: deck rejected 2026-10-02, pinned at the 264-document corpus until removed")`. If the deck's guard is entangled with a pack guard such that one cannot pass without the other, stop and report; do not split the generator to get around it.

3. **24 → 23, at the generator.** The pack says 24 indicators have a current rule. 24 is `len(set(rules.CURRENT.values()))`, which counts rules, one of them on candidate A12; the evidence map (`CL-048`) and figure 1 say 23. Fix the count where it is computed, then regenerate. List every file the number appears in before and after.

4. **Page H wording, per `CL-083`.** `docs/brief/H_limits.md:71` and `scoring_model.md:7` say equal weighting follows the OECD/JRC default. The prior-art pass found the Handbook never says that; it says equal weighting is common, is itself a weighting, and can disguise the absence of a basis. Replace the sentence, at its generator, with the wording the evidence supports: equal weights were chosen because no basis for other weights exists, and the Handbook notes that choice is a weighting. Cite `CL-083`.

5. **Diff discipline.** Report the regeneration diff line by line. Expected changes: the document count (264 → 265 and its derivatives), the federal-document count on `C_provenance.md`, the 24 → 23 lines, the page H sentence, and dates. Any other change stops the task before commit, and the RESULT names it.

6. **Pass criterion.** `make gate-fast` and the full suite at **0 failed**. A red gate is a failed task, whatever else shipped.

7. **Reader gate (DN-009 d7).** A fresh subagent reads only the regenerated page H and `B_usafacts_delta.md` and writes three sentences on what changed and whether anything reads as a claim the record does not make.

**Write set:** the files decisions 1 to 4 name, `tests/test_brief_deck.py` (the xfail mark only), the protected-paths script for this task, the RESULT. Byte-identical: `docs/deck/`, `docs/evidence/`, `docs/catalog/`, `docs/figures/`, `framework/`, `corpus/`, `events/`.

**Immutable once written.**

## Gate and report
`make gate-fast`, the full suite, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-04_views_regenerate_RESULT.md`, under 50 lines: the diff summary by file; the before and after of every 24; the page H sentence before and after; the gate counts; the reader gate's three sentences; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** read the generators → fix the count and the sentence at source → regenerate → diff → xfail mark → gate to 0 failed → reader gate → RESULT → push.
