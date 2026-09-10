# RESULT — report PDF: the L0 report as a readable PDF, from the pipeline

**Task:** `cc_tasks/2026-09-10_report_pdf.md` (no addenda exist; globbed at dispatch and again
before §3).
**Date:** 2026-09-10 UTC
**Spend:** zero model calls. **Network: none.** No host contacted.

---

## 1. The gate — §3

**PASS on every clause.**

| clause | result |
|---|---|
| PDF text layer carries exactly the markdown's numbers | **0 differences**, multiset, both directions |
| Fast tier green | **EXIT=0**, 1646 passed, 1144 s |
| `seldon verify` | **EXIT=0**, all checks passed |
| Protected paths | **EXIT=0**, prose changes confined to decisions 4 and 5 |

**PDF: `docs/reports/2026-09_fss_ai_readiness_L0.pdf` — 11 pages, A4 portrait, 245 KB, all 5
fonts embedded, zero `{{` tokens, every matrix row present.**

## 2. Toolchain, pinned

| tool | version | role |
|---|---|---|
| pandoc | 3.8.3 | converter |
| typst | 0.14.2 | PDF engine |

No LaTeX is installed on this machine; typst is what exists, and decision 1 forbids installing
a toolchain to do this. Typst also renders SVG natively, which is what makes decision 3's "no
figure is redrawn" achievable. Both versions are pinned in `scripts/build_report_pdf.py` and in
the `report-pdf` Makefile target, so the next revision is one command:

```
make report-pdf      # rebuilds the markdown, converts, then runs the numeral gate
```

The markdown is rebuilt **first**, every cycle, so no number can enter the PDF that did not
resolve from the graph.

## 3. Three things the conversion exposed

**The figure would not parse.** `figures.py` writes SVG for INLINE embedding in an HTML page,
so its root element carries no `xmlns` and typst refuses it outright: "failed to parse SVG
(missing root node)". Decision 3 forbids redrawing, so the build writes a **namespaced copy**
under `docs/reports/generated/`. The registered Figure artifact and the graph page are
untouched and not one path element changes. Adding the namespace that makes the same bytes a
standalone document is not redrawing a figure.

**`flipped=true` was silently ignored, and landscape turned out to be unnecessary.** pandoc's
typst template exposes `papersize` and no `flipped`, so the variable did nothing and the first
build came out portrait with `NAHM-SAPHIS` and `SAMH-SACBHS` hyphenated mid-name. The cause of
the ugliness was hyphenation, not width. Setting `#set text(hyphenate: false)` fits the whole
matrix on one portrait page at 10 pt with every agency name whole, so decision 2's landscape
allowance is not used and the type never went below 9 pt. Landscape was tried and measured
first: it worked, and cost three extra pages of wide-set prose.

**Two layout sources injected numbers that exist in no source.** A generated table of contents
(page numbers) and pandoc's `Figure 1:` caption numbering. The TOC was **dropped** rather than
exempted: §3's gate is worth more than a contents page on an 11-page document, and carving an
exemption for generated page numbers is how a gate stops meaning anything. Page numbers and
generated figure numbering are stripped as layout, which is what §3's "stripped of layout"
says, and the strip is **bounded** — the test asserts it removes no more lines than there are
pages, so it cannot quietly swallow a table cell.

## 4. Decision 5: the pending count stays at 7, and the premise was wrong

Decision 5 says: "If the report currently says 7 pending, correct it to the count in the
shortlist (8) with the registered Result." **I did not, because 8 would be false about the
cycle this report describes.** Measured from the target list:

| | count | who |
|---|---|---|
| pending in cycle 3 | **7** | BLS, BTS, DRSMSU, NAHMSAPHIS, NCES, ORES, SAMHSACBHS |
| with a flagship in cycle 3 | 9 | BEA, BJS, CENSUS, EIA, ERS, NASS, NCHS, **NCSES**, SOI |
| named in `fss_flagship_declarations.md` | **8** | the 7 pending, **plus NCSES** |

The declarations file names 8 because it also declares a flagship for **NCSES**, which was not
pending — it had one (the Annual Business Survey) and the file declares a different one
(Science and Engineering Indicators). So 8 = 7 pending + 1 replacement, and the report's
`fss_agencies_pending_operator_declaration_2026-09 = 7` is correct as it stands. **No Result
was re-registered and no number changed.**

What decision 5's first half asks for is done: the file is referenced by name in the
future-research section, applied to no number, with a sentence saying it postdates the cycle
and changes nothing here.

## 5. Decision 4: the self row

The matrix's last row now reads `this report | - | - | - | - | - | - | planned host: GitHub
Pages under this repository; to be measured on publication`, and the prose that said the row
was absent says what it is instead. It carries no verdicts and is not scored.

It is appended to the RENDERED table in the section file, **not** to
`docs/reports/generated/matrix_tierA.md`, which is a measurement artifact whose every row
carries the Finding identities it summarises. A row for a host nobody has measured does not
belong in a file that the re-derivation gate walks back to the graph.

## 6. Premises this task got wrong

1. **Decision 5's "correct it to the count in the shortlist (8)".** §4. The two counts measure
   different things and the report's is right.
2. **Decision 2's landscape.** Offered as the fix for a matrix that will not fit; the matrix
   fits portrait once hyphenation stops breaking agency names. Reported because "we used
   landscape as permitted" would have hidden that the diagnosis was wrong.
3. **Decision 1's "or the repo's existing report pipeline if it already produces PDF".** It
   does not; `scripts/build_l0_report.py` produces markdown only. Named for completeness.

### Mine

4. **I set `-V flipped=true` and did not check that the template reads it.** It does not, and
   pandoc reports nothing for an unused variable. I only noticed because `pdfinfo` said
   595 x 842 when I had asked for the reverse — which is the reason to read the artifact's own
   properties rather than trust that the flag took.
5. **A walrus typo aborted an edit script mid-way** (`assert s3 := ...`), so a fix I believed
   applied had not been. Caught immediately because the next run reported the identical
   failure, unchanged.

## 7. Verification

```
logs/gate_fast.log    1646 passed, 2 skipped, 11 deselected     1144 s   EXIT=0
logs/verify.log       seldon verify — All checks passed                  EXIT=0
logs/protected.log    protected-paths diff                               EXIT=0
                        report prose   only 20_matrix.md (+1, the self row)
                                       and 70_future.md (decisions 4 and 5)
                        state/         no change
                        rule modules   no change
                        prior RESULTs  no change
                        cycle evidence no change
                        events/        no change

pdfinfo               11 pages, 595.276 x 841.89 pts (A4)
pdffonts              5 fonts, all embedded (emb=yes)
numeral gate          multiset equality, markdown vs PDF text layer, 0 differences
                      (tests/test_report_pdf.py, 2 passed)
```

Build intermediates (`*.build.md`, the namespaced SVG copy) are gitignored: `make report-pdf`
regenerates both, and committing a second copy of the report is how two copies drift. The PDF
is the product and is committed.

## 8. What the next task needs

1. **`figures.py` writes SVG that is not a standalone document.** Every consumer outside the
   HTML page has to namespace it first. Emitting the `xmlns` at source would cost one string
   and is a change to a registered Figure artifact, which is why this task did not make it.
2. **The report has no host.** The self row is a promise until GitHub Pages is serving it, at
   which point the row becomes measurable and the instrument can be turned on its own output.
3. **Cycle 4** waits on `docs/design/fss_flagship_declarations.md`, now committed, and is not
   this task's to run.
