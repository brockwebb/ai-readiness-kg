# CC Task: every effort and cost band is filled with a notional relative value, tagged as notional, and the layer stops waiting

**Date:** 2026-09-17
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the operator's ruling of 2026-09-17: the bands are notional starting points, relative not absolute, to be adjusted by each agency for its own skills, staffing and platform; they are not a value input and they do not gate anything. Supersedes the pending-slot table in `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §2 as an ask.
**Implements:** DN-005 §2.3 ("sourced where a source exists and marked as estimate where none does") with the estimate marker now carrying a value instead of a blank.
**Framework layer served (DN-005 §5 rule 1):** §2.3, prescription.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

## 0. The ruling and its prior art

The 90 empty bands were left empty because no document on disk states a level of effort for any technique. That was right for the source field and wrong for the band: an empty band reads as "no answer", when the honest answer is "a notional relative estimate, adjust for your shop." The literature on why absolute effort figures are not worth the operator's time is settled and the task cites it once, in the DN-005 addendum, not per node: the planning fallacy (Kahneman and Tversky, 1979, "Intuitive prediction: biases and corrective procedures"), reference-class forecasting as the corrective (Flyvbjerg, 2006, "From Nobel Prize to project management"), and relative sizing as the practice teams actually use (story points; Cohn, *Agile Estimating and Planning*, 2005). None of these is on disk; cite by reference and say so. The corpus sentences that acknowledge effort without sizing it (DWBP BP 14 and 23, digital.gov's pending-period mechanism) are cited as the reason a source field cannot be filled.

**Decisions taken here (operator overrides later, and has said it will not be asked to):**

1. **Bands are assigned by technique class, and every action carries its class.** `technique_class` ∈ {`edit_existing`, `publish_new_file`, `change_server_behaviour`, `expose_api`, `harness_side`} with a one-line definition each in the addendum. Classes are assigned from the action's `description` and its `technique_source` kinds, and the RESULT tables the mapping so a reader can dispute a row.
2. **The notional bands per class**, relative within this layer, not absolute:

   | class | effort_band | cost_band |
   |---|---|---|
   | `edit_existing` (a field, a directive, an identifier added to something already served) | hours | none |
   | `publish_new_file` (a sitemap, `data.json`, `llms.txt`, a changelog feed, a structured methodology, a bulk download) | days | staff_time |
   | `change_server_behaviour` (content negotiation, real 404s, server-side render, edge or bot-manager alignment) | weeks | staff_time |
   | `expose_api` (an HTTP API and its OpenAPI description where none exists) | quarter | procurement |
   | `harness_side` (E5, this instrument's own controls) | hours | none |

   Where an action does not fit a class on its face, the RESULT says which class was chosen and why in one line; it does not add a sixth class without a second action needing it.
3. **The source field says what the band is.** `effort_source` and `cost_source` become `notional:technique_class:<class>, task 2026-09-17_notional_bands`. The value `estimate:pending` no longer appears anywhere; `test_no_band_was_filled_from_a_source_that_does_not_state_one` is replaced by a test that every band is a legal value and every source is either a document locator or a `notional:` marker, and that no `notional:` marker is missing its class.
4. **Every action carries the adjustment instruction as a field, once, verbatim:** `band_note: "Notional relative estimate for a typical federal statistical publisher. Adjust for your platform, staffing, skills and procurement path; the band orders actions against each other, it does not predict your calendar or budget."` `scripts/prescriptions.py` prints it once per body output and once in `--all`, not per action, and prints bands as their words with `(notional)` after the header line.
5. **The DN-005 addendum (`…_ADDENDUM_02.md`) records the ruling, the classes, the bands and the three references**, and the sentence that these bands are refined by evidence from agencies that act on them, not by further estimation.
6. **Nothing else moves.** No new actions, no rule, no matrix, no report. The site's framework copy and manifest move as before.

**Write set:** `framework/ai_readiness_framework.json` through `framework_writeback.save`; `scripts/tag_prescriptions.py` (the class mapping and band fill); `scripts/prescriptions.py` (the note and the `(notional)` marker); `tests/test_prescriptions.py`; the addendum; the site payloads; `scripts/check_protected_notional_bands.sh` (new); `seldon_events.jsonl`; the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-17_notional_bands_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1 to 4: the 45-row class table, then the fill through the writer.
## 2. Decision 5.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths, projection round-trip. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-17_notional_bands_RESULT.md`: §0 the class table (action, class, one-line reason where not obvious); §1 counts per class and per band; §2 the `--all` output with the note; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-17_unassigned_indicators.md` (both write the record) and before `2026-09-17_mcp_over_the_graph.md`, so the MCP's prescriptions tool never prints a pending band.
