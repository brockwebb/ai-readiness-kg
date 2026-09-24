# RESULT: narrative v4, last three claims closed, page B subsection placed, 48 and 49 reconciled

**Task:** `cc_tasks/2026-09-24_brief_narrative_v4.md` (no addenda). **Status:** complete, and every gate in §5 ran to its EXIT line. Launch base: `f26d889`. Pack commit: `e769047` (decisions 1 and 2, committed alone). Work commit: `0eadcf4`.

## 1. Reconciliation (decision 2): counts confirmed from the record by script
The record has 49 `AssessmentIndicator` nodes. `counts.indicators` = 48 and `counts.candidate_indicators` = 1, so 48 + 1 = 49. The one node held out under DD-054 (`_candidate_ids`, status `candidate`) is **A12**. **F6**'s status is the string "`paid`-tier candidate". DD-054 does not hold F6 out: it counts among the 48, and it is not the source of the gap. The task's paragraph read as if two nodes accounted for the one-node difference. Page H now opens its "Measurement tiers" section with this sentence, as emitted:
> The record holds 49 indicator nodes, and its `counts.indicators` is 48: `counts.candidate_indicators` is 1, `A12`, whose record `status` is `candidate` and whose promotion is an operator decision (DD-054: the framework does not adopt what the instrument found about itself without the operator). The measurement-tier table shows both denominators; the status table and the list of indicators not marked measured count the framework's. `F6`'s status reads "`paid`-tier candidate", but DD-054 does not hold it out, and it is counted in the framework.

The DD-054 clause is quoted from the record's `counts_basis`, not retyped. The three counts are on `numbers.json` under H. The new test `test_page_h_reconciles_48_and_49_in_the_records_own_counts` re-derives the counts from the record. Decision 1: `### What the guide says of itself` now comes after the "Of 49" paragraph. Only `B_usafacts_delta.md`, `H_limits.md` and `numbers.json` moved (`--check`: 61 files, 0 drifted).

## 2. C and E wording as landed
Page G's requirements table does not support "reference material", and it does not support the old "benchmark sets" alone either. The C rows are mostly `benchmark_set` rows provided by `this_project` (C1 to C4), plus accounts and tools for C4 and C5. The E rows are `benchmark_set` rows (E6, E8, E9) and `agency_records` rows provided by `publisher` (E1, E2, E3, E4, E7). Landed: "Two criteria, C accurate and E the TEVV loop, are largely unmeasured: the requirements table says what would unlock them, and it is benchmark sets this project has not built and agency records the publisher holds [G]."

## 3. Corrections (deviations from the task's exact text, each needed to pass a gate or for accuracy)
1. **Bullet 3 opening.** The task's "Criteria C accurate and E the TEVV loop are…" fails the label gate, which reads E's label as "TEVV loop are largely unmeasured". It now opens "Two criteria, C accurate and E the TEVV loop, are…". The label gate is outside the write set, so the gate was not changed.
2. **Bullet 3 ending.** "reference material" was replaced by the table's wording, as §2 describes.
3. **Bullet 1 last clause.** "the record's 49th is a candidate" became "the record's 49th indicator node, A12, is a candidate whose promotion is an operator decision", following page H's sentence. Blind spot: `prose_numerals` does not scan ordinals such as "49th", so this numeral was checked by hand against page H (49 is on its ledger), not by the gate.
4. **Abstract:** landed verbatim as the task gave it.

Nothing was struck. Both narrative gates (numerals and quotations, labels) return `[]`. The narrative diff against `d2b2d5b` plus decision 3, in the wording that landed, prints no lines.

**Claims to check (not edited):** "48 indicators in the framework record": the record holds 49 nodes and *counts* 48, so "the record counts 48" would be more exact.

## 4. Premises wrong
(1) Page H has no "coverage section". The sentence went at the top of "Measurement tiers", the section whose tables sum to 48 and 49. (2) The paid-tier candidate, F6, is inside the 48 (§1). (3) "Reference material" is not the table's wording (§2). (4) `tests/test_brief_deck.py` was not touched, and §1 of the protected check now enforces that.

## 5. Gate (logs under `logs/`, not shipped). All ran after `0eadcf4`.
- `make gate-fast` (fast tier, not the full suite): **2801 passed, 3 skipped, 27 deselected, 12 xfailed**, 667.01 s, EXIT=0 (`logs/narr4_gate_fast.log`).
- `seldon verify`: All checks passed, EXIT=0 (`logs/narr4_seldon_verify.log`).
- `check_protected_brief_pack.sh`: 61 files checked, 0 drifted, PROTECTED PATHS OK, EXIT=0 (`logs/narr4_protected_pack.log`).
- `check_protected_brief_deck.sh` (base `f26d889`): 77 and 219 slides re-rendered identical, no narrative diff, PROTECTED PATHS OK, EXIT=0 (`logs/narr4_protected_deck.log`). The appendix moved only by its cover stamp.

## 6. Spend
Measured session total up to this RESULT: **2,479,957 tokens** over 29 model turns on `claude-opus-5-5`. Of these, 2,368,816 were cache reads and 16,776 were output. That is inside the 2 to 4M estimate. There were no model calls and no projection.
