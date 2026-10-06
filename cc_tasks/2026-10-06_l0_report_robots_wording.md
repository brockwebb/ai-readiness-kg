# CC Task: the L0 report says three hosts grant robots access; every read got a 403. Reword to the findings (audit C-02)

**Date:** 2026-10-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/audit/2026-10-04_full_audit.md` finding C-02 (`docs/audit/2026-10-04_full_audit_findings.csv` row 2). A wording defect on a shown surface, and the one the reader gate said casts doubt on every other sentence.
**Implements:** DN-012 (closure of C-02); DN-001 (every report sentence cites a finding); DN-004 (report snapshot policy).
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement, since the report is evidence under it.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1M tokens (Opus). One generator edit, a rebuild, the suite. No model call.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **The facts, from the log.** `www.bls.gov`, `www.bts.gov` and `www.ssa.gov` answered HTTP 403 to `/robots.txt` on every read of every cycle 2026-09-06 to 09-10 (BLS 22 reads, BTS 10, SSA 10). Their A4 cells are `error` ("robots.txt could not be observed: refused"); their A12 Findings say the declared layer is not observable. No grant was ever observed. Re-derive these counts from `events/*.jsonl` and print them in the RESULT.

2. **Reword at the generator**, not by hand, lines 143-148, 173-174 and 187-190 of `docs/reports/2026-09_fss_ai_readiness_L0.md` and any other sentence the grep in decision 4 finds. The sentences say what the findings say: the host refused `/robots.txt` itself; the declared layer could not be observed; under RFC 9309 §2.3.1.3 an unavailable robots file permits crawling, so the harness's client was permitted to proceed and the host then refused the pages it requested. The coherence claim ("each publishes a robots.txt that grants access") is dropped. Cite RFC 9309 with its section; retrieve it, do not recall it (the corpus may already hold it; check the manifest first).

3. **Snapshot policy.** The report is a dated snapshot under DN-004. Regenerate it as a corrected snapshot with the correction noted in its change line, the prior snapshot kept; do not rewrite history.

4. **Grep the pack and the site** for the same claim in other words ("grants access", "permissive robots", "obeys the robots.txt those hosts publish") and fix each at its generator. List every hit and its fix in the RESULT.

5. **A test.** For every body whose A4 cell is `error` on the cycle of record, no shown surface contains a sentence asserting that body publishes a robots.txt. Generated from the matrix, so a future cycle that observes a grant lifts the restriction by itself.

**Write set:** the report generator, the regenerated report snapshot (PDF and markdown), affected brief-pack and site generators and their outputs, `tests/`, the RESULT. Byte-identical: every rule, collector and matrix.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-06_l0_report_robots_wording_RESULT.md`, under 40 lines: the re-derived 403 counts; every sentence changed, before and after; the RFC citation and how it was retrieved; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** re-derive counts → retrieve RFC 9309 → generator edits → grep and fix → test → rebuild → gate → RESULT → push.
