# DN-005 ADDENDUM_01 — how the three measurement tiers are read, and the basis field beside them

**Date:** 2026-09-17. **Written by:** `cc_tasks/2026-09-17_measurement_tiers.md` (decision 2, last paragraph), executing DN-005 §4 item 2. **Amends:** DN-005 §2.2. It adds a reading and a field and repeals nothing. The operator can overrule the reading, which is a naming decision and not a value one.

---

## 1. The reading

DN-005 §2.2 names three tiers. Every indicator node in `framework/ai_readiness_framework.json` now carries them as `measurement_tier`, with the meanings below.

- **M: measured by this project's instruments.** This covers the harness legs in `rules.CURRENT`. It also covers instruments this project builds and runs under the same discipline even where they are not yet built. The G1 judged reading (DD-036) is the precedent: it is this project's instrument and it runs under harness discipline. A benchmark or entailment evaluation the project would build is M for the same reason, and its node says the instrument does not exist yet.
- **O: measurable with open tools this project runs but does not own.** The tool must be named, and a source on disk must say it reaches the indicator.
- **D: declared. Only the agency can say.** This is the survey's honest scope (DN-005 §2.5).

§2.2's gloss of D also names "paid tools". This reading does not use that clause to place an indicator. The skeleton's `tier` field (`public` / `agency_instrumented` / `paid`, skeleton §6b) already records what observing or producing a property costs, so it is kept as a separate axis. For example, F6 is `tier: paid` because signing releases costs the publisher money. It is `measurement_tier: O` because the attestations can be verified with open tooling.

## 2. The basis field

The three-way split stays three-way. A second field, `measurement_basis`, records the kind of act that measures the indicator:

| basis | tier | what it is |
|---|---|---|
| `harness_leg` | M | a rule in `rules.CURRENT` serves the indicator |
| `judged_reading` | M | the G1-style second instrument: a pinned consumer reads the captured surface and its restatement is scored |
| `evaluation` | M | a benchmark, eval set or entailment run the project would build |
| `open_tool` | O | a named open tool, cited |
| `declaration` | D | only the agency can say |

Each assignment carries `tier_source` (the locator the assignment rests on), `tier_rule` (which of the task's decision-2 rules reached it) and, where needed, `tier_note`. An indicator that no rule reaches carries `tier_unassigned_reason` and no tier. A tier is not defaulted.

**The verdict axis is not the tier axis.** The tool map's verdict (`scan-observable`, `content-evaluation`, `not web-observable`) answers *by what kind of act*. The tier answers *who could measure it*. Since this addendum, `scripts/scan_tool_map.py` derives the verdict from the basis:

- `harness_leg` and `open_tool` become `scan-observable`;
- `judged_reading` and `evaluation` become `content-evaluation`;
- `declaration` becomes `not web-observable`;
- no basis becomes `unassigned`.

## 3. The name `measurement_tier` was already in use, and moved

`ind:G1-D` carried `measurement_tier: product` (DD-066 §6). That value names the **surface level** at which the construct can be measured (product rather than host). It does not say who can measure it. DD-066 §6 anticipated this task: the tiering task "may rename the field, but it does not remove this one".

The value and its source text moved verbatim to `measurement_level` and `measurement_level_source`. `measurement_tier` on G1-D is now `M`. The published source appendix (`docs/data/sources_per_check.json`) labels its G1-D rows with `measurement_level` for the same reason, because `scripts/build_l0_site.py::INDICATOR_LABELS` reads that key.

## 4. Where the numbers are

The per-indicator table, the counts per tier and per basis, and the list of indicators no rule reached, with the reason for each, are in `cc_tasks/2026-09-17_measurement_tiers_RESULT.md` §1 and §2. They are also on the record's nodes. `docs/design/scan_tool_map.md` §4 prints them, and `tests/test_measurement_tiers.py` holds the distribution as a literal, for the record and for the graph.
