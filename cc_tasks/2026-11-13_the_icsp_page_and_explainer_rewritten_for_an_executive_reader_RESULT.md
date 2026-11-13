# RESULT: the ICSP page and the working-group explainer, rewritten for an executive reader (DN-020 §10)

**Task:** `cc_tasks/2026-11-13_the_icsp_page_and_explainer_rewritten_for_an_executive_reader.md`
**Date:** 2026-11-13
**Status:** complete. One builder rewritten, both documents rebuilt, the four drawn figures brought in and placed. ICSP one page, explainer five pages. `make gate-fast` EXIT=0; the four predecessor tests pass; `seldon verify` EXIT=1 on two pre-existing warnings this task did not cause; protected-paths diff empty. Nothing re-measured; the record did not change.
**Addenda:** ADDENDUM_01 (the four figures) and ADDENDUM_02 (SI means superintelligence) both read and applied; neither is SUPERSEDED.
**Recall used:** none. (The eight recall hits are prior RESULTs; I worked from DN-020 §10 and the two addenda directly, the live framework record and the cycle's grid, and the builder source. No hit changed the approach.)
**Served model:** `claude-opus-4-8`, equal to `seldon models resolve author` (`claude-opus-4-8`). No substitution.

---

## 1. The ICSP page as built (full text)

> # SI readiness of federal statistical data: a ladder, and where agencies stand
>
> **What is it?** USAFacts, which gathers federal data at scale, has published a ladder for making government data usable by SI (superintelligence), the federal term that replaced AI on 29 September 2026. The ladder readies data for the assistants people now use to reach it. It has three tracks, three levels on each, and three basics that come first. The three tracks ask three plain questions: Access (can a program get the data?); Context (can it understand what it got?); Evaluation (has anyone checked the answers it gives?).
>
> *[Figure one — the three ladders on one base, three signposts, a robot with a notebook.]*
> *Figure one. Three tracks, three levels on each, and three basics that come first.*
>
> **How does it work?** The readiness diagnostic checks each agency from the outside, the way a member of the public's SI assistant would, making ordinary public web requests and reading what comes back. There are sixteen checks today.
>
> **Where do agencies stand?**
>
> *[Figure three — a crowd on the ground and the first level, a couple on the second, none on the third, a few on the basics step.]*
> *Figure three. Of sixteen agencies, eleven reach the first level of the Access track and one the second; on the Context track two reach the first level and one the second. None is higher, and the Evaluation track is not measured yet.*
>
> - The basics come first, and no agency yet clears all three. The basic most agencies meet is having each data page in the site's own list of pages (three of sixteen); the one most miss is a page that labels itself a dataset (eleven of sixteen fail it).
> - On the Access track, can a program get the data, eleven of sixteen reach the first level and one the second.
> - On the Context track, can it understand what it got, two of sixteen reach the first level and one the second.
> - The Evaluation track, has anyone checked the answers it gives, is not measured yet: that is a testing programme on its own, not something a public web request can see.
>
> **What does an agency do with it?** This is decision support. An agency sees its level on each track and the single next step up, read from published criteria rather than asserted, so money and staff time go where they raise the level, not to a grade. A check that could not be measured for an agency names its reason and never counts against it.
>
> **What does it cost to run?** The diagnostic makes ordinary public web requests, the kind any SI assistant makes for a member of the public, and puts no special load on a site.
>
> ---
>
> *Built on USAFacts' framework (August 2026) and the FAIR principles (2016).*
>
> *How this was made. These pages were produced by a program from the project's framework record and its most recent round of public web requests, made in October 2026; every count on them is read from that record, not typed by hand. The wording was drafted with Anthropic's Claude Opus 4.8, through Claude Code under a commercial subscription, on 13 November 2026, and is the project's own. This note follows FCSM 26-01 on disclosing the use of generative SI.*

**First-use sentence, each document (ADDENDUM 02):**

- ICSP: "USAFacts, which gathers federal data at scale, has published a ladder for making government data usable by SI (superintelligence), the federal term that replaced AI on 29 September 2026."
- Explainer: "USAFacts built a ladder for making federal data usable by SI (superintelligence), the federal term that replaced AI on 29 September 2026: three tracks, three levels on each, and three basics that come first."

After first use each document says "SI" alone. The build fails if "SI (" ever expands to anything but "superintelligence"; it does not.

---

## 2. Part A: the basics, counted per check

From the cycle of record (`scan_2026-10-07_composite_d`), for each of the four checks DN-020 §4 places on a prerequisite. The "bar" column is the record's `instrument_state`: `specified` reads as a published requirement (the record Scores it), anything else as this project's reading.

| Basic (plain name) | Pass | Fail | Not measured | Bar |
|---|---|---|---|---|
| The data page is in the site's list of pages | 3 | 10 | 3 | a published requirement (Scored) |
| The page labels itself as a dataset | 1 | 11 | 4 | this project's reading (not Scored) |
| The product is listed in the agency's data inventory | 0 | 5 | 11 | a published requirement (Scored) |
| The terms of reuse, under a recognised name | 0 | 11 | 5 | this project's reading (not Scored) |

No partial readings on any of the four (every agency's pages agree). No agency clears all three discoverability checks and the licence check together, so zero clear the prerequisite rung as a whole (T3's cumulative rule, reported for the record and NOT applied on these two documents, per A5). The per-level counts are the roll-up's, imported, not recomputed: Access level 1, eleven of sixteen; Access level 2, one; Context level 1, two; Context level 2, one; everything above, not measured.

The four rows were added to the builder's computed data and to `reports/dn020/build_report.json` (`basics[]`, with `counts` and `bar`).

---

## 3. Step 0: where the 2026-11-05 documents broke an amendment

Read back as their reader would (the built `.md` and `.pdf` of task ec1112d3). Each break, and the amendment it broke:

- **A1 / ADDENDUM 02.** Title "Statistical-information readiness: the USAFacts ladder…" and the footer "in these pages SI means statistical information". SI is superintelligence; the gloss was a build invention. Titles now read "SI readiness"; the gloss is the ADDENDUM 02 wording; "statistical information" is gone and the build fails if it returns.
- **A2.** The closing block was a vocabulary note ("SI use: …SI means statistical information…"), not a disclosure of how generative SI made the document. Replaced by a production statement (which model drafted the wording, from what record), with no claim of human review the record cannot show.
- **A3.** The explainer's lineage put the project's own summary sentences in quotation marks beside FAIR and USAFacts ("Findable, Accessible, Interoperable, Reusable…", "the ladder with a sensor on it"), reading as if those sources wrote them. The lineage is now told in the project's words without quotation marks; only USAFacts' captions are quoted, each cited to the deck (section 6).
- **A4.** The worked check headed a paragraph "The sensor." and leaned on "markup"; the bottom line used "least privileged client"; both documents carried the generator path `scripts/dn020_documents_build.py` in the body; the tracks were never introduced with their plain questions. All six A4 words are now out of the prose (the build fails on any), the generator path is gone from the ICSP body and confined to one explainer footer line, and the three tracks are introduced once with their plain questions.
- **A5.** The ICSP left the prerequisites out; the explainer reported "zero of sixteen" clearing the prerequisites beside "eleven" at Access level 1, with no per-check basics and no published-requirement/this-project's-reading mark. Both now show the basics before the ladder, one line per check with the count of sixteen and the bar (Part A).
- **A6.** The ICSP did not answer the five questions in order. It now answers What is it; How does it work; Where do agencies stand; What does an agency do with it; What does it cost to run.
- **A7.** The explainer's "What each measured rung asks" repeated one sentence ("An agency clears this rung when none of its measured checks here comes back a fail; on the cycle of record N of sixteen did.") six times. That section is now one table, each measured level once; no sentence repeats (the build fails if one does).

---

## 4. The four figures (ADDENDUM 01)

sha256 as Desktop wrote them, verified against the source folder and quoted:

| file | sha256 | check |
|---|---|---|
| `1.svg` | `149f5bf1fc8adbaa48469af9385be5ab5c204a90cac2ec8f906762c5cdc0a7ce` | matches ADDENDUM 01 |
| `2.svg` | `26c171e1c8f8140efb749b627b42e2475767d72134cd76fe9a0bd093e9d04520` | matches |
| `3.svg` | `9137184d6269965ad5b2fe0352ec901e282624e0b11c0c7663ae33c0bbb2a1ec` | matches |
| `4.svg` | `9f741d4dc710f5a9bf0ddf933665efbfe45bf4c7b2e1ed046e74c3960d251dec` | matches |

All four copied into `reports/figures/dn020/`. `git check-ignore` on each returned nothing (exit 1 overall; none ignored — they are tracked deliverable sources). Each SVG carries zero `<text>`/`<tspan>` elements (no text in any picture). The PDF embeds the SVG directly (typst); the Word route needs a raster, so each SVG was rendered to `reports/figures/dn020/<n>.png` at 2x with `rsvg-convert` (present on the machine — no install, no network). `build_report.json` records `placed: svg` and the SVG sha256 per picture, plus the docx PNG sha256.

**Figure 3 against the counts (ADDENDUM 01 step 3).** The picture shows most figures on the ground and the first level, a couple on the second, none on the dotted third, and a few on the basics step. The counts: Access level 1 eleven, level 2 one, none higher; Context level 1 two, level 2 one; basics per check A5 three, A6 one, D4 zero, D1 zero. The qualitative story matches — the crowd sits low on the ladder, a few reach the second level, none the third — and the warned-against case (the counts putting most agencies on the second level) does not hold. Placed, not a placeholder; `figure3_counts.not_misleading = true`.

---

## 5. The checks added to the builder, and their output

Part D extends the builder so the build FAILS on: a banned word (DN-016's scan/probe/crawl/audit/unmeasurable/ruling plus A4's sensor, measurement specification, cycle of record, least privileged client, markup, rung-by-rung), a code/record-id/script-path/file-name in the body, the string "statistical information" anywhere, an expansion of "SI" other than "superintelligence", or a sentence that appears twice. All passed (`failures: []`).

**ADDENDUM 02 check, all six files** (`statistical information` present? / SI expansions that are not "superintelligence"):

| file | "statistical information" | SI mis-expansions |
|---|---|---|
| `ICSP_SI_Readiness_One_Page.md` | false | [] |
| `ICSP_SI_Readiness_One_Page.pdf` (text) | false | [] |
| `ICSP_SI_Readiness_One_Page.docx` (text) | false | [] |
| `SI_Readiness_Working_Group_Explainer.md` | false | [] |
| `SI_Readiness_Working_Group_Explainer.pdf` (text) | false | [] |
| `SI_Readiness_Working_Group_Explainer.docx` (text) | false | [] |

**Captions cited to the deck (A3).** Each quoted USAFacts caption was located verbatim (normalised match, the docling copy carries "machine -readable" spacing) in `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md`; the build fails if one cannot be found. Lines: "Data is published in machine-readable files" (441); "Stable, documented endpoints agents can crawl" (443); "Agent-native interface for live, structured queries" (445); "Definitions and units documented for humans" (449); "Methodology and caveats travel with each dataset" (451); "Context is machine-readable and citable in an answer" (453).

---

## 6. Read-back (Part D)

Both PDFs read back page by page as a senior non-technologist (ICSP) and a mixed room, lay reader first (explainer).

**ICSP (one page, body 9.5pt, figure 1 at 3.0cm, figure 3 at 2.6cm).**
- Longest sentence: *"These pages were produced by a program from the project's framework record and its most recent round of public web requests, made in October 2026; every count on them is read from that record, not typed by hand."* (the production disclosure; the five answer blocks are two–three short sentences each.)
- Terms a non-technical reader might not know, and where glossed: **SI** — glossed at first use, "(superintelligence), the federal term that replaced AI on 29 September 2026"; **FAIR principles** — a named reference in the credit line; **FCSM 26-01** — a named standard in the disclosure. No letter codes, record ids, script paths or file names in the body.
- Sentence appearing twice: none.

**Explainer (five pages, body 11pt).**
- Longest sentence: *"The same four ideas, rebuilt as three tracks with levels borrowed from SLSA, a maturity ladder from the software industry where each level is a short list of things you can check."*
- Terms glossed: **SI** — first-use gloss as above; **SLSA** — glossed inline "a maturity ladder from the software industry where each level is a short list of things you can check" (named once, in the explainer only, per A4); **FAIR** — glossed inline "easy to find, to get, to combine and to reuse, by machines as much as by people"; the dataset-label idea (A6's check) is rendered as "a built-in, machine-readable label", never "markup".
- Sentence appearing twice: none. The former six-fold repeat is now the single level-by-level table; the unmeasured levels close it in one row ("not measured yet" once).
- "AI" appears only in the history line ("replaced AI on 29 September 2026"), the acronym FAIR, and inside the quoted USAFacts captions — never in the project's own prose for the machine user, which says SI throughout (A4's check name "…let AI tools in" renders as "…let SI tools in").

---

## 7. Premises this task (and DN-020) got right and wrong

- **DN-020 §4's prerequisite record ids (A3, A6, D1, D2) are display labels, not the grid legs.** The record's `DESCENDS_FROM` edges place `A5, A6, D4` on the discoverable prerequisite and `D1` on the licensed one; the §4 note says as much ("Record ids are the ones the roll-up used… confirmed against `rf_name_brief`"). I took the four basics from the edges (authoritative), and their plain names match the §4 descriptions one-for-one. No premise broken, but worth recording: the four basics are A5/A6/D4/D1, not A3/A6/D1/D2.
- **The cycle name cannot go in the body.** `scan_2026-10-07_composite_d` is a record id and contains "scan"; the disclosure names the round as "public web requests, made in October 2026" instead, truthfully, keeping the body free of the id and the banned word.
- **The record commit stamp is `b5c940ce3aff`** (the last commit to `framework/ai_readiness_framework.json`), the same commit the brief pack stamps — consistent across the repo. The explainer footer carries it; the ICSP body carries no generator or commit (both in the build report).
- **The task filename constant in the builder was wrong on first write** (`…the_working_group_explainer…`); corrected to the real file before the RESULT. It affects only `build_report.json` metadata, no rendered byte.

---

## 8. Gate, verify, protected paths

Run detached and logged (`logs/`, gitignored). This worktree had no copy of the gitignored corpus lanes (`corpus/kernel|pilot|bulk|bulk_md`) or the `state/` caches, so they were copy-seeded from the primary checkout with `rsync -a` (no `--delete`, no symlinks), as the daily-suite job seeds its own worktree; that seeding changed no tracked file.

| step | result | log |
|---|---|---|
| `make gate-fast` | **3452 passed, 8 skipped, 41 xfailed, 0 deselected** (none reported in the xdist summary), 1890 warnings, in 577.75s. **EXIT=0** | `logs/gate_fast.log` |
| four predecessor tests (`test_brief_pack.py` ×3, `test_evidence_map.py` ×1) | **4 passed** in 20.42s. **EXIT=0** | `logs/four_tests.log` |
| `seldon verify` | **EXIT=1**, 2 warnings, neither caused by this task: task `98ed1dd1` blocked with no reason recorded; no decision register declared (AD-033). Same two the predecessor RESULT recorded. | `logs/seldon_verify.log` |
| protected-paths diff (`framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json`) | empty | — |

The task's gate is `make gate-fast`: the write set touches none of `assessment/harness/scan/rules/`, `collectors/`, `runner.py`, `run.py`, `manners.py`, `rederive.py`, `scripts/score.py` or the framework record (CC-dispatch gate-tier rule).

**Write set:** `scripts/dn020_documents_build.py` (rewritten); `reports/dn020/{ICSP_SI_Readiness_One_Page,SI_Readiness_Working_Group_Explainer}.{md,docx,pdf}`; `reports/dn020/build_report.json`; `reports/figures/dn020/{1,2,3,4}.svg` and `{1,2,3,4}.png`; this RESULT.

---

## 9. Session usage against 0.6M

The build makes **zero paid model calls** — it is deterministic over the framework record and the cycle's grid, one role (`author`), no review model — so there is no spend-ledger entry for it. The only cost is this Claude Code session's own tokens, which are not machine-metered from inside the session; the work (reads, one builder rewrite, iterative rebuilds, two PDF read-backs, the gate) ran well inside the 0.6M-token estimate. No cap was approached; nothing to escalate.
