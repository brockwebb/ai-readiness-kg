# CC Task: the brief deck packaged as brief plus appendix; B packed to the floor; wide diagrams turned upright

**Date:** 2026-09-23
**Project:** ai-readiness-kg
**Authored by:** Desktop session, for ResearchTask `5f1bf9f0`, from the OODA over `cc_tasks/2026-09-22_brief_deck_assembly_RESULT.md` (`92421acb`). Four mechanical corrections to a deck that exists and passes its gates; nothing here changes what the deck says.
**Implements:** DN-005 (view of the framework) and DN-008 ruling 2 (one chaptered deck, roughly 100 slides, mostly appendix). The assembled deck is 293 slides, 218 of them appendix; this task packages it so the ruling's shape holds without trimming a slide.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure: the brief's view.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 2 to 4M tokens. The last deck task was estimated at 3 to 6M and measured 9.99M (97.1 percent cache reads); that pair is recorded for `bb46ddb5`. The RESULT ends with the measured session total and names the model.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line inside this turn. Targeted reads only.

## What exists (read first)
`scripts/build_brief_deck.py`, `docs/deck/brief_deck_content.md`, `tests/test_brief_deck.py`, `scripts/check_protected_brief_deck.sh`, `cc_tasks/2026-09-22_brief_deck_assembly_RESULT.md` §1 (counts), §3 (diagrams), §5 premise 5 (the protected check diffs against HEAD, so commit order matters). `scripts/build_brief_pack.py` owns the Mermaid sources on `docs/brief/E_architecture.md`.

## Decisions

1. **Two outputs from one content file.** `build_brief_deck.py` writes `docs/deck/brief_deck.pptx` (cover, chapters A to H, and one closing slide that names the appendix file and its slide count by `@stamp`) and `docs/deck/brief_appendix.pptx` (the generated appendix: indicator sheets, rule groups, corpus summary, each preceded by its own cover). The single 293-slide file is not kept. `--check` covers both. `tests/test_brief_deck.py` asserts brief plus appendix slide counts equal the counts the old single file had, less nothing, plus the two new cover and closing slides.

2. **Chapter B packs to the floor.** The 2026-09-22 task said one skeleton §8 item per slide; that was an override with no basis, and it made B 22 slides. Remove it: consecutive `> ` quotations in a section flow onto one slide until the 14pt floor splits them, the same rule every other section follows. Expected B after: 12 to 16. State the count.

3. **Diagrams (c) and (d) are drawn upright.** The RESULT says they render at about 10:1 and 15:1 and read small on 16:9. In `build_brief_pack.py`, set `direction TB` (or the equivalent for the diagram type) on those two Mermaid sources only, regenerate the pack, `--check`, then `--render-diagrams`. If upright still exceeds the slide, split the diagram at a named boundary across two slides and say where. The "how to read it" text is unchanged. Only `E_architecture.md`, the two PNGs and their sha sidecars may change under `docs/brief/` and `docs/deck/diagrams/`; the pack's protected check must pass.

4. **61 versus 62.** `cc_tasks/2026-09-22_brief_material_pack_v2_RESULT.md`, `docs/brief/INDEX.md` and DN-008 §2 say the pack is 62 files; the deck RESULT says `--check` covered 61. Name the file that accounts for the difference and which count the deck's slide 2 should carry. If the 62 is wrong, say so in the RESULT and leave DN-008 alone (it is a dated note); the next design note corrects it.

**Write set:** `scripts/build_brief_deck.py`, `docs/deck/**`, `tests/test_brief_deck.py`, `scripts/build_brief_pack.py` (decision 3 only), `docs/brief/E_architecture.md` and `numbers.json` if a diagram count changes (via the generator only), `scripts/check_protected_brief_deck.sh` (updated for two outputs), the RESULT. Byte-identical: `framework/`, `state/`, `events/`, `docs/reports/`, `docs/data/`, `docs/crosswalk/`, `assessment/`, `corpus/`, `mcp/`, every other file under `docs/brief/`. No projection, no model call.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, `scripts/check_protected_brief_pack.sh`, `scripts/check_protected_brief_deck.sh`. Commit the pack change (decision 3) alone first, gated alone, as the last task did. RESULT `cc_tasks/2026-09-23_brief_deck_packaging_RESULT.md`, under 40 lines: slide counts per chapter and per output; the diagram outcome; the 61/62 answer; premises wrong; measured session tokens with the model named. `seldon cc complete`, commit, push.

**SEQUENCING:** 3 (pack first, committed alone) → 2 → 1 → 4 → tests → gate → RESULT → push.
