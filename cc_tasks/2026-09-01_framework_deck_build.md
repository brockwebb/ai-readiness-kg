# CC Task: Build the framework deck (plain-text pptx) from deck_content_2026-09-01.md

**Date:** 2026-09-01
**Authored by:** Desktop session
**Immutable once written. Before starting: glob and read all sibling `2026-09-01_framework_deck_build_ADDENDUM*.md` files.**

## Objective

Build a plain-text PowerPoint from `docs/crosswalk/deck_content_2026-09-01.md`. Working deck the operator will edit — not a polished deliverable. No template, no theme, no images, no charts.

## Source

`docs/crosswalk/deck_content_2026-09-01.md` is the single source. One `## Slide N` section = one slide. The `**bold lead**` line after a slide header is the slide title; remaining content is body. Content is authoritative — do not rewrite, summarize, or "improve" wording. If a slide's body overflows, reduce font size for that slide (floor 14pt); if still overflowing, split into "N" and "N (cont.)" and note the split in the RESULT.

## Build

- python-pptx, default 16:9 blank layout. Title + body text frame per slide. Black text, white background, default font.
- Nested bullets in the source map to indent levels. Numbered lists stay numbered.
- Slide 1 uses a title-slide layout (title + subtitle).
- Output: `docs/crosswalk/framework_deck_2026-09-01.pptx`.
- Use the anaconda python if python-pptx is not in the default env; `pip install python-pptx` into the anaconda env is permitted if absent.

## Constraints

- Zero model calls, zero spend. Deterministic transform only.
- Do not edit the content file. Discrepancies (malformed section, ambiguous nesting) go in the RESULT.
- Do not touch the burn, ledger, or manifest.

## Completion

- Open-check: verify the pptx loads (python-pptx round-trip read; count slides == source sections).
- Write `cc_tasks/2026-09-01_framework_deck_build_RESULT.md` (slide count, overflow handling, any splits).
- Run `seldon cc complete cc_tasks/2026-09-01_framework_deck_build.md`.
- Commit and push (task, RESULT, pptx, and content file if it was uncommitted).
