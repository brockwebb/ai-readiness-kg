# CC Task: the report is re-snapshotted onto `scan_2026-09-10_rj4`; the guard follows the chain; the two ingested READMEs get their Document nodes

**Date:** 2026-09-19
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-18_rejudge_seven_legs_RESULT.md` §3 and "Open" items 1 to 4, and `2026-09-18_requirements_layer_RESULT.md` §3 premise 7 and "Open" item 1.
**Implements:** DN-004 (the snapshot moves when a published number would change; it would: three tagged Results and 161 product cells), DD-056 (Results are registered per cycle and published by promotion), DD-003 (the corpus gate is the manifest and its events).
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M, the published state of the 16 bodies catches up with the instrument.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`.

---

**Decisions taken here (operator overrides later):**

1. **`publication.yaml:snapshot_cycle` → `scan_2026-09-10_rj4`.** The report, its fragments, the PDF and the site's published Results rebuild from it through their own generators. The three tagged Results move (`scan_findings` 739 → 1009, `scan_l0_product_legs` 10 → 17, `scan_l0_product_legs_at_zero` 5 → 11); every other published number is asserted unchanged, and the diff of the published payloads is in the RESULT line by line. The 168 `proposed` L0 Results of `_rj4` are promoted per DD-056's rule; the `_rj2` ones they succeed are marked superseded.
2. **Prescriptions are re-tagged from the new snapshot.** `tag_prescriptions` recomputes `bodies_failing_now` (D2 enters at 13, B2/B4/B5/D3 at 12, B1/G4 at 11); the record moves through the writer with the cycle as source.
3. **The successor guard follows `SUPERSEDES` to the newest judgement**, not one hop, and reports the chain it walked. Against the new snapshot it must report `moved: 0`; a test pins that the old one-hop behaviour would have missed `_rj4`.
4. **Every view that prints a rank prints the concentration sentence with it.** `score.py` gains, per body, the single leg whose flip would change its rank most (the "on one pass" sentence: DRSMSU is first on G4's single pass); the design page's step 10 says why. The MCP's `get_body` carries the same field.
5. **The 22 `_rj3` G1-D Findings that are `current` without being today's instrument get a `finding_withdrawn` overlay** on the log citing DD-066, so `current` means what it says. No Finding is deleted.
6. **`manifest_add` events are emitted for `oasdiff-readme` and `wayback-cdx-server-api-readme`**, from their ledger entries, so the projection holds their `Document` nodes; the MCP's manifest fallback stays as the guard for any future gap and its test now also asserts the fallback is not needed for these two.

**Write set:** `docs/reports/publication.yaml`, the report and its generated fragments, the PDF, `docs/data/*` and the manifest through `build_l0_site.py`, `results_tagged.json` and the Results ledger (promotions), `framework/ai_readiness_framework.json` through the writer (decision 2), `scripts/snapshot_successor.py` and `scripts/score.py` and `mcp/` (decisions 3, 4), the shard (decision 5 overlay, append), the corpus events (decision 6), the projection, tests for 3 to 6, `scripts/check_protected_resnapshot.sh` (new), `seldon_events.jsonl`, the RESULT. No Observation, no Finding, no matrix content changes.

**Immutable once written. Glob `2026-09-19_resnapshot_rj4_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 3 to 6 first (they are what the re-snapshot is checked with), tests first.
## 2. Decisions 1 and 2; the published-payload diff captured before and after.
## 3. Gate
`make gate-full` (`-rs`), `seldon verify`, protected paths, projection round-trip, the successor guard on the new snapshot. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-19_resnapshot_rj4_RESULT.md`: §0 the published-number diff; §1 the promotions; §2 the guard's walked chain; §3 the concentration sentence for each of the 13 scored bodies; §4 every premise this task file got wrong; §5 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
