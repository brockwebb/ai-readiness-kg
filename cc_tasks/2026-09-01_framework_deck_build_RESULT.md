# RESULT — Framework deck build

**Task:** `cc_tasks/2026-09-01_framework_deck_build.md`. No `_ADDENDUM*.md` siblings existed at
dispatch or at close. **Output:** `docs/crosswalk/framework_deck_2026-09-01.pptx`.
**Spend: zero.** Deterministic transform, no model call. python-pptx 1.0.2 was already present
in the anaconda environment, so nothing was installed. The content file was not edited. The
burn, ledger and manifest were not touched.

**18 source sections in, 18 slides out. No splits were needed.**

## Build

`scripts/build_framework_deck.py` is the transform, written as a re-runnable script rather than
a one-off because the content file says a rebuild regenerates the deck. 16:9 at 13.333 x 7.5
inches, black text on the default white, no template or theme, no images or charts. Slide 1
uses the title layout with title and subtitle placeholders; slides 2 through 18 use the blank
layout with a title textbox at 28pt and a body textbox beneath it.

Nested list indentation maps to bullet levels. Numbered lists keep their numbers as literal
text so PowerPoint cannot renumber them against the author's intent. Inline `**emphasis**`
renders as real bold runs, which consumes the markers and changes no words.

## Font sizes, and the two exceptions worth naming

Bodies render at 18pt and step down toward the 14pt floor only when the fit model says they
must. Three slides moved: slide 6 to 17pt, slide 8 to 14pt, and nothing else.

| slide | pt | rendered lines |
|---|---:|---:|
| 6 The instrument | 17 | 11 |
| 8 Capability architecture (SV-1) | 14 | 19, of which 11 preformatted |
| all others | 18 | 2 to 12 |

**The fit model is an estimate, and it is held two lines back from the real budget.** Line
counts come from an average-character-width approximation; PowerPoint does the actual layout
with the actual font metrics. The first build sized slides 6 and 8 to a one-line margin, which
is inside the model's own error, so a slide could render overflowing while the arithmetic said
it fit. A two-line slack costs one point of font on three slides and removes that failure mode.
Every slide now clears the hard height budget by at least two lines and none is below the 14pt
floor.

**Preformatted blocks render at 12pt monospace, which is below the floor, and this is
measured rather than casual.** Slides 4, 8 and 14 are text renderings of diagrams and the
content file asks for monospace where the layout survives. The widest diagram line is 107
characters on slide 14. In Courier that line needs 12.48 inches at 14pt against a 12.33-inch
box, so it clips; at 12pt it needs 10.70 inches and fits. The 14pt floor governs the
overflow-reduction mechanism for body text, which is a height constraint. The diagram blocks
are bound by width instead, and reducing them is the only way to render the author's alignment
without altering the lines. Raising these to 14pt would clip slide 14's widest row.

## Discrepancy, reported not reconciled

**The stated title rule matches one slide.** The task says the `**bold lead**` line after a
slide header is the slide title. Only slide 1 has a standalone bold line; slides 2 through 18
have none, and their bold markup is inline emphasis inside bullets. The builder uses the bold
lead where one exists and the `## Slide N — Title` header text otherwise, which is the reading
that produces a titled deck. Had the rule been applied literally, seventeen slides would have
been untitled and their first bullet consumed as a title. Recorded rather than silently
generalized.

Slide 1's subtitle placeholder carries the tagline line and the subtitle sentence. The literal
`Subtitle: ` prefix is dropped because it is a directive to the builder rather than content;
the sentence after it is unchanged.

## Open-check

Round-tripped through python-pptx after writing:

- 18 slides in the file, equal to the 18 `## Slide N` sections in the source.
- Slide size 13.333 by 7.5 inches.
- No slide is empty of text.
- Slide 1 has two placeholders, title and subtitle, populated.
- Slide 8 carries 11 Courier New runs, so the diagram blocks kept their monospace.
- Font sizes present: 28 for titles, 18/17/14 for bodies, 12 for preformatted, and small sizes
  on blank spacer paragraphs.

## Not done

No theme, template, images, charts or speaker notes, per the task. The SVG diagram versions
the content file mentions are not embedded; slides 4, 8 and 14 remain text renderings, which is
what a later polished deck would replace.

---

## Addendum — v3 rebuild, 2026-09-01

The deck was rebuilt from v3 content by
`cc_tasks/2026-09-01_assessment_consolidation.md` step 6, which owns the rebuild when the deck
already exists. Same procedure, same script, same open-check.

18 sections in, 18 slides out, no splits. One font change: slide 9 moved from 18pt to 17pt to
absorb the new reference-implementation line. Slide 13 gained a line and stayed at 18pt. Slides
6 and 8 are unchanged at 17pt and 14pt. Open-check confirms 18 slides against 18 sections, slide
5 free of MCP/A2A and naming RFC 9309, and slide 9 naming `assessment/harness`.

This task's own Seldon record was completed at 14:48 and is not re-completed; the artifact it
produced is now regenerated from newer content.
