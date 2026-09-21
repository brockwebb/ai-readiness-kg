# CC Task: apply the G4 narrowing (the three-edge drop is authorized, by name)

**Date:** 2026-09-21
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-21_g4_narrowed_RESULT.md`. Supersedes `cc_tasks/2026-09-21_g4_narrowed.md` (`d4b1b275`), whose decision 2 forbade `--force` by rote; `save` already has the sanctioned path for a deliberate, recorded deletion (`--force --reason`). Desktop's error, not a gap in the writer. No change to `framework_writeback.py`.
**Implements:** operator ruling 2026-09-21: "narrow it and close it."
**Framework layer served (DN-005 §5 rule 1):** §2.1, the validity layer.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**After:** none
**Spend:** zero pipeline model calls; CC session floor 691K tokens measured on the stopped run (Sonnet, 11 calls), full run estimated 2.5 to 4M on Sonnet, more on Opus; unmeasured. **Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Wait on every detached command with ONE blocking bash call (`until grep -q EXIT= <log>; do sleep 20; done`, 10 minute timeout, repeated as needed). That satisfies "poll to the EXIT line"; never poll turn by turn. Read files with targeted `grep`/`sed` ranges, never whole large files.

---

## The specification

`cc_tasks/2026-09-21_g4_narrowed.md`, decisions 1, 3, 4, 5, its write set, gate and report sections, executed unchanged, with decision 2 replaced by this:

1. Apply `logs/g4_narrowed_skeleton_edit.patch` (the first run's edit, reviewed in its RESULT and accepted as written: new G4 text; clause 3 removed because `rule_g4.py` lists provenance under `UNMEASURED`; six documents kept, each with place and quote).
2. Run the write-back once WITHOUT `--force` and confirm the refusal names **exactly these three edges and nothing else**:
   - `ind:G4->doc:statistical-policy-working-paper-46-data-quality-assessment`
   - `ind:G4->doc:fcsm-19-01-transparent-reporting-for-integrated-data-quality`
   - `ind:G4->doc:dcat-ap-3-0-0-r5r-vocabulary`
3. Only then re-run with `--force --reason "G4 narrowed to the measured, sourced claim by operator ruling 2026-09-21; three EVIDENCED_BY edges removed by name (cc_tasks/2026-09-21_g4_narrowed_apply.md)"`. **If the refusal lists any other node, edge or `counts` key, stop and report; the authorization covers these three edges only.**
4. The three documents stay in the corpus and the manifest; only G4's edges to them go. DCAT-AP remains an admitted document that no indicator cites; say so in the RESULT and leave it.

**Filenames follow this task's slug:** RESULT `cc_tasks/2026-09-21_g4_narrowed_apply_RESULT.md` (under 40 lines), guard `scripts/check_protected_g4_narrowed_apply.sh`. The RESULT ends with this session's own token total (`npx ccusage@latest session --json`, matched by session id), so the estimate above is replaced by a measurement.

**Immutable once written.**

**SEQUENCING:** 1 → 2 → 3 → base task decisions 3, 4, 5 → gate → RESULT → `seldon cc complete` → push.
