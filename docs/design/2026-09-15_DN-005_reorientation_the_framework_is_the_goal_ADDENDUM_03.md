# DN-005 ADDENDUM_03 — the effort and cost bands are notional, relative, and assigned by technique class

**Date:** 2026-09-17. **Written by:** `cc_tasks/2026-09-17_notional_bands.md` (decision 5), executing DN-005 §2.3. **Amends:** DN-005 §2.3's clause "sourced where a source exists and marked as estimate where none does" — the estimate marker now carries a value instead of a blank. It repeals nothing and it moves no gate. **Supersedes as an ask:** the 90-slot pending table in `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §2, which asked the operator to fill the bands one by one.

---

## 1. The ruling

The prescription layer shipped with 90 empty bands (45 effort, 45 cost) and the source field reading `estimate:pending`, because no document on disk states a level of effort or a cost for any of these techniques. The search that established that is in `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §0 and it stands: four documents acknowledge that effort and cost exist (W3C DWBP BP 14 and BP 23, `digital-gov-website-standards`'s pending-period mechanism, SLSA's "higher implementation costs") and not one of them sizes anything.

The operator's ruling of 2026-09-17: **the bands are notional starting points, relative and not absolute, to be adjusted by each agency for its own skills, staffing and platform. They are not a value input and they gate nothing.**

That is a decision about what kind of quantity a band is, and it changes what an empty cell means. An empty band reads as *no answer* — or worse, as *no effort*. The honest answer was never "nobody knows"; it was "a notional relative estimate, adjust for your shop." The band was empty because the wrong instrument was being demanded of it.

## 2. The prior art, cited once here rather than per node

None of the three is on disk; each is named by reference, and this addendum is the one place the layer cites them.

- **The planning fallacy.** Kahneman, D. and Tversky, A. (1979), "Intuitive prediction: biases and corrective procedures". Absolute duration and cost estimates made from the inside view are systematically optimistic, and more deliberation does not correct them. A per-action effort figure produced by this session would have been exactly that kind of estimate.
- **Reference-class forecasting as the corrective.** Flyvbjerg, B. (2006), "From Nobel Prize to project management: getting risks right". The correction is to forecast from the distribution of a *class* of comparable cases rather than from the particulars of the instance. That is what `technique_class` is: an action is banded as a member of its class, never on its own.
- **Relative sizing as the practice.** Cohn, M. (2005), *Agile Estimating and Planning*. Teams estimate reliably in relative units and unreliably in absolute ones; the useful output is an ordering, not a calendar. The bands here are ordinal — `hours < days < weeks < quarter` — and the note on every node says so.

Read together: **the band is worth producing as a relative class-level ordering and is not worth producing as an absolute per-action figure.** The layer now does the first and explicitly refuses the second.

## 3. The classes

Assigned from the action's own `description` and the kinds of its technique sources. Every `Action` node carries `technique_class`; where the class is not obvious on the description's face the node also carries `technique_class_reason`, and `cc_tasks/2026-09-17_notional_bands_RESULT.md` §0 tables all 45 rows so a reader can dispute one.

| class | what it is |
|---|---|
| `edit_existing` | a field, a directive or an identifier added to something the host already serves |
| `publish_new_file` | a file the host does not serve yet — a sitemap, a data.json, an llms.txt, a changelog feed, a structured methodology, a bulk download |
| `change_server_behaviour` | how the server answers rather than what it holds — content negotiation, real 404s, server-side rendering, edge or bot-manager alignment |
| `expose_api` | an HTTP API and its OpenAPI description where none exists |
| `harness_side` | this instrument's own controls (E5), acted on by the operator of the harness |

A sixth class is not added for one action. Where an action does not fit on its face, the class chosen is recorded with its reason on the node.

## 4. The bands

Relative within this layer. Not a calendar, not a budget, not a denominator in anything.

| class | `effort_band` | `cost_band` |
|---|---|---|
| `edit_existing` | hours | none |
| `publish_new_file` | days | staff_time |
| `change_server_behaviour` | weeks | staff_time |
| `expose_api` | quarter | procurement |
| `harness_side` | hours | none |

`cost_band` retains the legal value `tooling`, which no class in this layer reaches. The value stays in `kg/schema.yaml` and in `COST_BANDS` because dropping an unused enumeration member is how a later action that needs it comes to be mis-banded.

**The band is a function of the class and is never authored per action.** `scripts/tag_prescriptions.py::build` reads it out of `NOTIONAL_BANDS[cls]`, and `tests/test_prescriptions.py::test_every_action_carries_a_class_and_the_class_fixes_both_bands` asserts that two actions of one class can never carry different bands. That is the property that keeps the estimate relative rather than making it forty-five separate guesses wearing one table's clothes.

## 5. What the source field says now

`effort_source` and `cost_source` read `notional:technique_class:<class>, task 2026-09-17_notional_bands`. The literal `estimate:pending` appears nowhere in the record, the schema or the two scripts, and a test asserts its absence.

The rule this replaces — *no band was filled from a source that does not state one* — becomes: **every band is a legal value, and every band source is either a document locator or a `notional:` marker that names its class.** A marker without a class would be an estimate with no method, which is the thing the empty band was protecting against, so it is the one thing the new test refuses.

Every action also carries `band_note`, verbatim and identical on all 45:

> Notional relative estimate for a typical federal statistical publisher. Adjust for your platform, staffing, skills and procurement path; the band orders actions against each other, it does not predict your calendar or budget.

It is a property of the record and not only of this document, so a consumer that reads one node off the graph reads what the number is *not* without also finding its way here. `scripts/prescriptions.py` prints it once per invocation and puts a `(notional)` marker on the header line — once each, never beside every band, because a sentence repeated forty-five times is a sentence nobody reads.

## 6. How these bands are refined

**By evidence from agencies that act on them, never by further estimation.** A publisher who closes one of these actions and records what it took is a measurement; a later session that thinks harder about the same table is not. If such evidence arrives, its band stops being notional: the `_source` becomes the locator for that evidence, and the test in §5 already admits a locator beside the marker without a change.

Until then the bands do exactly one job — they order the 45 actions against each other — and they gate nothing, enter no numerator, and are not the operator's to ratify.
