# ADDENDUM 01 — `cc_tasks/2026-09-15_g1d_leaves_l0.md`

**Date:** 2026-09-15. **Amends decisions 4 and the SEQUENCING line; supersedes nothing else.** Operator direction 2026-09-15: the report is fixed now, before a meeting today, not at cycle 5. Leaving a column on a published matrix that the project has decided measures nothing is the hand-wave this task exists to remove.

**Amended SEQUENCING.** This task runs **first**, before `cc_tasks/2026-09-15_standing_dispatcher.md`. The base file's "runs after the dispatcher has pushed" is withdrawn.

**Amended decision 4 (the report changes now).** The report is a view; the snapshot stays `scan_2026-09-10_rj2` and no Observation, Finding or stored payload moves. What changes is which legs the view renders, and that is driven from the instrument's current leg set, not from the snapshot's params:

- `build_l0_matrices.compute` and `write_matrices` render the columns in `params.tier0.legs` **as of the build**, so the G1-D column leaves the three matrices, the fragments, the JSON and CSV. The machine-readable matrices keep their rj2 name and gain the withdrawn leg in their metadata (`legs_withdrawn: [G1-D]`, with the DD reference), so a reader of the CSV can see a column was removed and why.
- The "Uncertainty fields" paragraph under "Reading it by column" is replaced by the generated sentence from the base task's decision 4: measured at host level in cycles 1 to 4, withdrawn as not applicable to the surface, product-tier measurement is the January G1 pilot, citing DD-066. The A12 sentence "and the fourth publishes no robots.txt" and every other paragraph stay verbatim.
- The published Results that quote G1-D at host level (the `0 of 13` rate, its Wilson upper bound, and any G1-D count Result the report tags) move to `withdrawn` with the reason "host-level G1-D leg withdrawn, DD-066; the surface cannot carry the property", not deleted. Every other published Result keeps its value and state. The `{{result:...}}` tags for the withdrawn Results are removed from the report source along with the paragraph; a tag pointing at a withdrawn Result is a build refusal.
- The snapshot-successor comparison (DN-004 decision 3) is run after the change and must report 0 moved and 0 uncovered over the Results that remain tagged; the withdrawn Results are excluded from its tagged set **by state**, not by name, and a test asserts that a withdrawn Result still tagged in the source refuses the build.
- Page counts re-register if they move (`l0_report_pages_{total,prose}_2026-09-15` per DD-056 naming); the site's `results_tagged.json` regenerates; the PDF rebuilds. The supersession line (DN-004 decision 2) still renders and still equals the query.
- Decision 4's "cycle 5 re-snapshots with five columns" becomes: cycle 5 renders under the same leg set and needs no further change.

**Zero-edits clause adjusted accordingly:** the report source, the three matrices, the fragments, `results_tagged.json`, the PDF and the G1-D Results' states are inside this task's write set. Nothing else moves.

**Amended §3.** Decision 4 as amended; the comparison output and the withdrawn Results' before/after states in the RESULT.

**Amended §5 gate adds:** the report and PDF contain no `G1-D` column and no G1-D rate; `grep -c "G1-D"` over the built markdown equals the count of occurrences in the generated withdrawal sentence and the DD citation, and nothing else; the PDF numeral-multiset gate and bare-numeral lint green; site `--check` green.

**Amended §6.** The RESULT states the page counts before and after, the withdrawn Result ids, and the rendered withdrawal sentence, and ends with the path of the rebuilt matrix CSV for `scan_2026-09-10_rj2`, which the Desktop uses to remake the meeting slides.
