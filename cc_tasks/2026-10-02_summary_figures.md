# CC Task: the three figures the summary needs, generated from the record, each passed through a reader

**Date:** 2026-10-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session, under DN-009. The operator's finding on the deck was that nothing in it showed what was built relative to USAFacts or what the tests found. This task makes the three pictures that do, from the record, by script. Runs after `2026-10-02_evidence_map_prior_art.md`, so figure captions can cite the evidence map by claim id.
**Implements:** DN-009 decisions 1 and 7.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-02_evidence_map_prior_art.md`
**Spend:** est. 3 to 6M tokens (Opus). Iterating a figure means re-running a script and viewing the PNG with Read, not regenerating by prose.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Output.** `docs/figures/` (new): for each figure, an SVG and a PNG at 300 dpi, a `.caption.md` holding its title, a one-sentence "what this shows," and the evidence-map claim ids it rests on, and `scripts/build_figures.py` that generates all three from the graph and the cycle of record, byte-stable for the SVG under `--check` (PNG compared by rendered pixels, since encoders are not byte-stable). Prior art for the renderer: `scripts/build_brief_pack.py --render-diagrams` and `scripts/build_framework_deck.py`; reuse what fits, do not re-derive. Library choice is yours (matplotlib, graphviz, or Mermaid via `mmdc` if installed); say which and why in the RESULT.

2. **Figure 1, USAFacts to framework.** One picture that answers "what did you build relative to USAFacts?" Left: USAFacts' four criteria by name. Center: the framework's seven criteria, the four kept drawn as descended from USAFacts' and the three added drawn as added, each with its indicator count. Right, per criterion: how many indicators have a current rule, how many are measured on the cycle of record, how many are specified only. Every count from the graph. No prose on the figure beyond labels. A reader with no context should be able to say "they kept four, added three, and have measured about a third."

3. **Figure 2, the system at a glance.** One picture of the pipeline a non-engineer can follow in under a minute: corpus of documents → framework record (indicators) → rules → scan of a body's public surface by an unauthenticated client → findings on a frozen cycle → scores and ranked prescriptions → graph with MCP interface a person can question. Six or seven boxes, left to right, one short label each, counts only where they help (264 documents, 49 indicators, 16 bodies). Nothing about supersession, event logs, or internals; those are the report's. The existing Mermaid diagrams on page E are the wrong altitude for this and are not reused.

4. **Figure 3, the pass/fail table.** Bodies as rows, the seven criteria as columns, cells showing measured legs passed over judged, with a color scale on the ratio and an empty cell where nothing was judged; a final column with the hierarchical score and the leg each body's rank rests on, as page H states it. Census row highlighted. Footnote on the table itself: equal weights, no weighting asserted, every rank rests on one leg. Both a figure (PNG/SVG) and a CSV of the same cells.

5. **Reader gate (DN-009 d7), per figure.** For each figure, a fresh subagent is given the PNG and nothing else (no caption) and asked: what does this show, in two sentences, and what is the one number you would repeat? Its answer is quoted in the RESULT beside the caption's intended sentence. If the reader's reading and the caption's sentence disagree in substance, the figure is revised and re-read, up to three rounds; the RESULT shows each round. A figure that fails three rounds ships with the failure stated, not hidden.

**Write set:** `docs/figures/**` (new), `scripts/build_figures.py`, `tests/test_figures.py` (idempotence; every count on a figure equals the script's computed value; every claim id in a caption exists in `docs/evidence/claims.yaml`), the RESULT. Byte-identical: everything else, `docs/evidence/` included. No projection; no model call outside the reader gate.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, `tests/test_figures.py`. RESULT `cc_tasks/2026-10-02_summary_figures_RESULT.md`, under 60 lines: the three figures by path with their captions; the reader rounds per figure, verbatim; library choice; premises wrong; measured tokens and model. Send the three PNGs with the RESULT so the operator sees them without opening files. `seldon cc complete`, commit, push.

**SEQUENCING:** renderer → figure 1 → its reader rounds → figure 2 → reader → figure 3 → reader → tests → gate → RESULT → push.
