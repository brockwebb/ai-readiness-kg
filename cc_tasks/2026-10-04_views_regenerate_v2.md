# CC Task: regenerate the manifest views and apply the two pack corrections, v2, with the rejected deck's guards retired as a module

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-10-04_views_regenerate_RESULT.md` (task `7da41858`, stopped at decision 2). That run established: regenerating the pack at all, with or without the two edits, turns the deck's 1 red guard into 12, because the deck renderer quotes pack sentences verbatim and its narrative gate checks numerals against pack pages; the unapplied generator edit is saved at `logs/views_regenerate_generator.patch`; and the diff it produced held only the expected lines. The operator's standing decision (DN-009) rejected the deck, so its guards are retired here as a module and the deck files are left untouched until the summary replaces them. This is the base task's decisions 1 and 3 to 7 unchanged, with decision 2 replaced.
**Implements:** DN-009 decisions 2 and 3; closes tracking record `9f2026e3`.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-04_node_key_fusion_audit.md`
**Spend:** est. 2M tokens (Opus). Generators, one patch, diffs; no model call outside the reader gate.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Regenerate the pack and the site, by their generators only** (base decision 1). Apply `logs/views_regenerate_generator.patch` to `scripts/build_brief_pack.py` first; it carries base decisions 3 and 4 exactly as that RESULT proposed them, including the 23-of-48 sentence for `B_usafacts_delta.md:16` and the page H replacement citing `CL-083`. `docs/brief/appendix/rules.md` keeps its 24, which counts rules and is correct.

2. **Retire the deck's guards as a module.** Mark the whole of `tests/test_brief_deck.py` with `pytestmark = pytest.mark.xfail(strict=True, reason="DN-009: deck rejected 2026-10-02; pinned at the 264-document corpus until removed")`. Do not regenerate, edit or delete anything under `docs/deck/`; its narrative files still say 24 and 264, and the RESULT lists those lines so the removal task has them. If any other test imports the deck renderer or its narrative gate as a dependency of a pack guard, stop and report; do not unpick the renderer.

3. **`claims.yaml` ripple.** `test_evidence_map.py::test_claims_file_regenerates_byte_for_byte` fails after the pack moves because `q5_numbers_that_differ_from_the_pack` loses its `pack: '24' / script: 23` row. Run `scripts/build_evidence_map.py` and ship the regenerated `claims.yaml`; the RESULT shows that diff in full. That is the generator doing its job, not a hand edit.

4. **Diff discipline** (base decision 5). Expected changes are the ones the v1 RESULT enumerated: `B:16`, `C:17` (94 → 95), `C:23` (264 → 265), `H:71`, `numbers.json` (24 → 23 and the new 48), `docs/data/corpus_manifest.json`, `docs/data/index.json`, and the `claims.yaml` row above. Any other change stops the task before commit.

5. **Pass criterion.** `make gate-fast` and the full suite at **0 failed**, with the deck module reporting as xfailed, not failed.

6. **Reader gate (DN-009 d7).** A fresh subagent reads only the regenerated page H and `B_usafacts_delta.md` and writes three sentences on what changed and whether anything reads as a claim the record does not make.

**Write set:** `scripts/build_brief_pack.py`, `docs/brief/` (generated files only), `docs/data/corpus_manifest.json`, `docs/data/index.json`, the L0 site outputs the generator owns, `docs/evidence/claims.yaml` (generator output only), `tests/test_brief_deck.py` (the module mark only), the protected-paths script for this task, the RESULT. Byte-identical: `docs/deck/`, `docs/catalog/`, `docs/figures/`, `framework/`, `corpus/`, `events/`.

**Immutable once written.**

## Gate and report
`make gate-fast`, the full suite, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-04_views_regenerate_v2_RESULT.md`, under 50 lines: the diff summary by file; the `claims.yaml` diff; the deck lines still carrying 24 and 264; the gate counts; the reader gate's three sentences; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** apply patch → regenerate pack, site, evidence map → diff → module mark → gate to 0 failed → reader gate → RESULT → push.
