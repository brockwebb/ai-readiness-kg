# DN-014 ADDENDUM 01: page two is one grid; plain names; the publisher row goes

**Date:** 2026-10-14
**Amends:** `docs/design/2026-10-12_DN-014_executive_summary_brief.md` (DN-014). Where this addendum and DN-014 differ, this addendum governs. Everything in DN-014 not named here stands.
**Decided by:** the operator, Desktop session of 2026-10-14, after reading the v2 summary (`reports/summary/SUMMARY.pdf`, task 14d163b7).

## 1. What the v2 showed

DN-014 §5 and §6 moved every count to a page-two results table. The author built that table as written. The operator's reading: the table needs inside knowledge to read, carries counts no reader can place, singles out one publisher, and the prose around it is conversational where it should be direct. The brief's wording caused this, not the author.

## 2. Page two

Page two is one grid and nothing else. No other table, no figure, no counts.

- Rows: the 16 federal statistical agencies, by name, in alphabetical order. The row label carries the agency's data-page count when it is more than one ("Bureau of Labor Statistics, 3 pages").
- Columns: the public-tier checks (the record's tier M, display name "public tier"), each under a plain-language name of at most six words. Checks that record what an agency declares rather than what a machine met are excluded from this grid.
- Cells: one of three marks. **Pass**: every one of the agency's data pages passes the check. **Fail**: every page fails it. **Partial**: at least one page passes and at least one fails. A single-page agency can only pass or fail. The three-state form follows accessibility conformance reporting (the VPAT format: supports, partially supports, does not support).
- Under each column, one line: the fix for that check. Derived from the record's one action per failing outcome; where a check has more than one failing outcome, the line names the fix for the most frequent one across the 16 agencies, and the footnote says so.
- Colors: pass blue, fail red, partial a hatched or lighter mark; a legend; never color alone (a glyph in every cell).
- Footnote, three sentences at most: the pass/fail/partial rule, the most-frequent-outcome rule, and the cycle date.

The old four-row table, the Census row, and every per-check count leave the document. They remain in the detailed report.

## 3. Plain names in the record, not in the prose

The record carries no plain-language name for any check or tier; that is why a table built from it reads as code. The record gains, through its write-back path and never by hand edit:

- `display_name` on each measurement tier: public tier; agency-enabled tier; paid-tool tier.
- `plain_name` on each public-tier check (rule), at most six words, stating what a machine met, not the rule's mechanism.
- `fix_line` on each action, one sentence, imperative, no codes.

The summary's text check adds the tier letters (M, O, D) and every rule and indicator code to its forbidden list. The reader's questions gain a fifth: name every term on either page that a CIO new to SI would not already know. A term named in two rounds is replaced, not explained.

## 4. Prose

Page one loses its opening definition paragraph and the pointer to a fuller definition; the appendix definition and its source paragraph go. Each section is at most three sentences. Register: a technical research summary, direct, with one plain sentence of motivation where it earns its place. The 30-second bullets of DN-014 §4 still govern what page one must let a reader say.

## 5. Second artifact: the USAFacts note

A separate two- or three-paragraph narrative, `reports/summary/USAFACTS_NOTE.md`, derived from the record: which of the framework's criteria came from USAFacts' four qualities (accessible, understandable, accurate, open); which three criteria were added, and the sources each one rests on; which USAFacts standards became checks a machine can run; and the result, that measurements now map onto their framework. No graph vocabulary (no nodes, edges, counts of either). Cites USAFacts' detailed user guide by title.

## 6. Parked (future tasks, not scheduled)

- A waffle chart per criterion (one square per check per agency, pass blue, fail red) showing how much of each criterion the 16 agencies meet. Before it is drawn: the framework has no ordered readiness levels; criteria sit side by side. Depth would need a decision to order them, which changes the framework, not the chart.
- An interactive explorer over the grid: click a cell, see which pages failed which checks and the fix for each. The grid is its top level.

## Prior art

### External

The grid's three-state cell (pass / partial / fail) follows accessibility conformance reporting: a VPAT/ACR scores each criterion supports / partially supports / does not support. The waffle chart (square pie) and isotype pictograms are the prior art for the parked item in §6. Both are published external practice, not research held in the squiddy library; the library searches below return only off-topic rows (web-agent accessibility trees, data-pipeline conformance, LLM evaluation scales), so each is recorded as a failed search, exactly as DN-014's external search was.

- library receipt: query "accessibility conformance report three-state scale supports partially supports does not support VPAT" | release library_graph_20261012_sq013_01_2026-10-12.json sha256:0989759c402ca41472806bdf9ab47529ba2eb5a6b25d0e75c1a6e29e650d4275 | rows lesson:2026-02-22_arXiv_2504_21024#p15:361:1330-1663, lesson:2026-02-22_arXiv_2504_21024#p17:398:1368-1450, lesson:2026-02-22_arXiv_2504_21024#p4:95:2139-2478, lesson:2026-08-25_arXiv_2512_03541#p12:127:1084-1133, lesson:2026-08-25_arXiv_2512_03541#p27:327:0-98, lesson:2026-08-25_arXiv_2512_03541#p5:38:140-354
- library receipt: query "waffle chart square pie isotype pictogram part-to-whole proportion visualization" | release library_graph_20261012_sq013_01_2026-10-12.json sha256:0989759c402ca41472806bdf9ab47529ba2eb5a6b25d0e75c1a6e29e650d4275 | rows lesson:2026-02-22_arXiv_2505_24876#p45:889:417-814, lesson:2026-02-22_arXiv_2505_24876#p45:893:1166-1330, lesson:2026-02-22_arXiv_2505_24876#p45:892:1001-1164, lesson:2026-02-22_arXiv_2505_02484#p202:2764:160-309

### Internal

The addendum follows DN-010 (decision support; "value", not "impact") and DN-013 (the concise report), and its changes to page two build on the v2 summary (task 14d163b7), whose capability table and Fable rounds stand. DN-010 and DN-013 are under `docs/design/` and resolve; the v2 RESULT lives under `cc_tasks/`, which is outside the prior-art internal roots (`prior_art.internal.default_include` in seldon.yaml), so its search reaches nothing and is recorded as such.

- internal receipt: query "DN-010" | repo ai-readiness-kg@e25d7af310ad9e9a1bdc07a3dafd441cb485f392 | hits docs/design/2026-10-02_DN-010_value_effort_matrix_decision_support.md:1
- internal receipt: query "DN-013 concise report" | repo ai-readiness-kg@580fbdd9976cfc4e70085dd1f355c27828f8ce39 | hits docs/design/2026-10-06_DN-013_parallelism_known_endpoints_and_prose.md:29
- internal receipt: query "executive_summary_from_brief_v2_RESULT" | repo ai-readiness-kg@d067e6960d8666adb0dcfca6f8837602deb81866 | hits none
