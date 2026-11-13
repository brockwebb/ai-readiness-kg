# ADDENDUM 01 to 2026-11-13_the_icsp_page_and_explainer_rewritten_for_an_executive_reader.md

**Date:** 2026-11-13 (11:10 local)
**Authored by:** Desktop session.
**Why:** the operator asked Desktop to make the four DN-020 section 7 pictures rather than run the image prompts himself. Desktop drew them as flat SVG illustrations (no text in any picture, palette as section 7) and checked each by eye. They sit outside the repository so they do not dirty the tree; this task brings them in.

## The four pictures

Source folder: `/Users/brock/GitHub/workbench/dn020_figures/` (outside every repository). sha256 as Desktop wrote them; verify and quote:

| file | sha256 | DN-020 section 7 |
|---|---|---|
| `1.svg` | `149f5bf1fc8adbaa48469af9385be5ab5c204a90cac2ec8f906762c5cdc0a7ce` | picture 1, the ladder |
| `2.svg` | `26c171e1c8f8140efb749b627b42e2475767d72134cd76fe9a0bd093e9d04520` | picture 2, the lineage |
| `3.svg` | `9137184d6269965ad5b2fe0352ec901e282624e0b11c0c7663ae33c0bbb2a1ec` | picture 3, where the agencies stand (with the basics step beside the ladder, per DN-020 A5) |
| `4.svg` | `9f741d4dc710f5a9bf0ddf933665efbfe45bf4c7b2e1ed046e74c3960d251dec` | picture 4, one check start to finish |

A sha256 mismatch stops this step; report it and build with placeholders.

## Steps (before Part B)

1. Copy the four files into `reports/figures/dn020/` in this task's working copy, same names. They are deliverable sources and are tracked; quote `git check-ignore` returning nothing for each.
2. Teach `scripts/dn020_documents_build.py` to place `reports/figures/dn020/<n>.svg` when it exists, before looking for `<n>.png`. The PDF route is typst, which embeds SVG directly; the docx route needs a raster, so render each SVG to `<n>.png` at 2x with whatever converter is already installed (`rsvg-convert`, `cairosvg`, or typst's own export). This task has no network: if no converter is present, the docx carries the placeholder and the RESULT says so. Do not install anything.
3. The picture must not contradict the counts. Picture 3 shows most figures on the ground and the first rung, a few on the second, none on the third, and a few on the basics step. Read the per-level and per-basic counts from Part A and the roll-up; if picture 3 misleads (for example, the counts put most agencies on the second level), say so in the RESULT and leave the placeholder for that one picture rather than shipping a misleading drawing.
4. `build_report.json` records, per picture, `placed: svg | png | placeholder` and the sha256 of what was placed.
5. Captions stay in the documents, never in the pictures (DN-020 section 7).

Everything else in the task stands. Commit the four SVGs, any rendered PNGs, and the builder change with the rest of the task's write set.
