# CC Task: the seven new rules are published as a re-judgement of the cycle of record; no host is contacted

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the operator's ruling of 2026-09-18 (run everything we can on what we have; no rescan now), `cc_tasks/2026-09-18_schema_field_rules_RESULT.md` §1 and `2026-09-18_dcat_field_rules_RESULT.md` §1 (the offline exercise of the seven rules on retained evidence, deterministic, unpublished).
**Implements:** DN-003 (every judgement goes on the append-only log, in generation order), DN-004 (a re-judgement is published beside its measurement; the report's snapshot moves only when a published number would change, and that is the Desktop's decision, stated here not acted on), DD-041 (byte-identical re-derivation).
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M: 23 legs measured on the 16 bodies instead of 16.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. Every Observation judged here was made on 2026-09-10; none is made now.

---

## 0. What exists and what this publishes

`scan_2026-09-10` holds the Observations. Its re-judgements `_rj1` and `_rj2` (the cycle of record) and `_rj3` exist. `scripts/exercise_dcat_field_rules.py` and `scripts/exercise_schema_field_rules.py` judged `RULE-B1-v2`, `B2-v1`, `B4-v1`, `B5-v1`, `D2-v1`, `D3-v1`, `G4-v1` over those Observations, attaching the `dcat_fields` and `content_signal` blocks offline exactly as the runner now does at collection; the verdicts were `fail` or `error` everywhere and identical on two runs. Those Findings are on no shard and in no matrix.

**Decisions taken here (operator overrides later):**

1. **One re-judgement, the next `_rj` number, over the whole current registry**, so every leg is judged by `rules.CURRENT` as of this task, not only the seven. Where a leg's rule has not changed since `_rj2`, the Finding ids must be byte-identical to `_rj2`'s; a test asserts it, and a difference is a gate failure, not a finding. If `RULE-D4-v2` exists by the time this runs (`2026-09-18_manners_status_and_b5_control.md`), D4 is re-judged under it and the RESULT says which D4 verdicts moved and why.
2. **Published through `publish.py`, projected, matrices written**, as the cycle template's §4 does: Findings to the shard as the next generation, `scan_matrix_tierA/tierC/product_<cycle>_rjN` under `docs/reports/`, L0 Results for the seven new legs registered `proposed` with cycle-suffixed names (DD-056). The E5 control gate runs first, offline, and is a hard stop.
3. **The snapshot is not moved.** `publication.yaml:snapshot_cycle` stays `_rj2`. The snapshot-successor guard (DN-004 decision 3) runs and its output goes in the RESULT. The RESULT states in one sentence whether a re-snapshot looks owed: it will, since seven legs are new and every scored view reads the snapshot. The decision is the Desktop's next turn.
4. **The scoring, prescription and MCP views are run against the new re-judgement with `--cycle`**, and the outputs are quoted in the RESULT beside the `_rj2` outputs, so the Desktop can see what moving the snapshot would change before it does.

**Write set:** the shard (append), `docs/reports/scan_matrix_*_<cycle>_rjN.json`, the L0 Results (append, `proposed`), `state/<cycle>_rjN.json`, the projection, `scripts/check_protected_rejudge.sh` (new), `seldon_events.jsonl`, the RESULT. `publication.yaml`, the report, the PDF, the site's published Results, `framework/`, prior payloads: byte-identical.

**Immutable once written. Glob `2026-09-18_rejudge_seven_legs_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Pre-flight: `refuse_clobber`; `run.py --controls-only` (hard stop).
## 2. Decisions 1 to 4.
## 3. Gate
`make gate-task` (re-derivation of this and every prior payload, non-optional), `make gate-full` (`-rs`), `seldon verify`, protected paths, the snapshot-successor guard. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure publishes nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_rejudge_seven_legs_RESULT.md`: §0 the control gate; §1 the seven legs' verdict distribution over the 16 bodies as published; §2 the unchanged-leg identity check; §3 the guard's output and the one-sentence re-snapshot statement; §4 the scoring grid and top prescriptions under `_rj2` and under the new re-judgement, side by side; §5 every premise this task file got wrong; §6 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (hard stop) → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_scoring_levels.md`.
