# ADDENDUM 01 to `2026-09-21_g4_narrowed.md`: the three-edge drop is authorized, by name

**Date:** 2026-09-21
**Status:** AMENDS decision 2 (its ban on `--force`). Everything else stands.
**Authored by:** Desktop session, from `cc_tasks/2026-09-21_g4_narrowed_RESULT.md`.
**Spend:** floor 691K tokens measured on the stopped run (Sonnet, 11 calls); full run estimated 2.5 to 4M, Sonnet, unmeasured.

## Why

`save` already has the sanctioned path for a deliberate, recorded deletion: `--force --reason`. Decision 2 forbade it by rote. Desktop's error, not a gap in the writer. No code change to `framework_writeback.py`.

## The amendment

1. Apply `logs/g4_narrowed_skeleton_edit.patch` (the first run's edit, reviewed in its RESULT and accepted as written: new G4 text, clause 3 removed because `rule_g4.py` lists it under `UNMEASURED`, six documents kept).
2. Run the write-back once WITHOUT `--force` and confirm the refusal names **exactly these three edges and nothing else**:
   - `ind:G4->doc:statistical-policy-working-paper-46-data-quality-assessment`
   - `ind:G4->doc:fcsm-19-01-transparent-reporting-for-integrated-data-quality`
   - `ind:G4->doc:dcat-ap-3-0-0-r5r-vocabulary`
3. Only then re-run with `--force --reason "G4 narrowed to the measured, sourced claim by operator ruling 2026-09-21; three EVIDENCED_BY edges removed by name (cc_tasks/2026-09-21_g4_narrowed_ADDENDUM_01.md)"`. **If the refusal lists any other node, edge or `counts` key, stop and report; the authorization covers these three edges only.**
4. The three documents stay in the corpus and the manifest; only G4's edges to them go. DCAT-AP remains an admitted document with no indicator citing it; say so in the RESULT and leave it.
5. Continue the base task from decision 3 (projection, round-trip, rebuild), then decisions 4 and 5, the gate, the report. Write the RESULT as `cc_tasks/2026-09-21_g4_narrowed_RESULT_02.md` (new files get new names; the first RESULT stays). It ends with this session's token total from `npx ccusage@latest session --json` for its own session id, so the Spend estimate above is replaced by a measurement.

**SEQUENCING:** 1 → 2 → 3 → base task decisions 3, 4, 5 → gate → RESULT_02 → `seldon cc complete` → push.
