# RESULT: the brief's material pack, generated from the record (`c3ba7b11`)

**Task:** `cc_tasks/2026-09-22_brief_material_pack_v2.md`. The addendum glob `2026-09-22_brief_material_pack_v2_ADDENDUM*.md` matched no files. Launched by the dispatcher from HEAD `d330014`. **Spend:** zero model calls by any tool. **Network:** loopback only (the spot and adopter fixtures) plus `git push`. No federal host was contacted.

**Gate: green.**
- **Full suite** (`pytest tests/ assessment/ -q -rs`, a superset of the `gate-fast` the task names; CLAUDE.md requires the whole suite before a push): 2799 passed, 3 skipped, 12 xfailed, 0 deselected, 2351.15 s, `EXIT=0` (`logs/brief_gate_full.log`). The 3 skips are the standing three: `test_dispatch_config.py:333` (dispatched session), `test_scan_harness.py:283` (E5) and `test_g1_preservation.py:337`.
- **`tests/test_brief_pack.py`:** 24 passed, 0 skipped, run with Neo4j up.
- **`seldon verify`:** "All checks passed.", `EXIT=0` (`logs/brief_seldon_verify.log`).
- **Protected paths:** `scripts/check_protected_brief_pack.sh` printed `61 files checked, 0 drifted` and `PROTECTED PATHS OK`, `EXIT=0` (`logs/brief_protected.log`).
- **Demo capture:** `EXIT=0` (`logs/brief_capture_demo.log`).

## 1. INDEX (`docs/brief/INDEX.md`, generated)
`B_usafacts_delta.md`/`.csv` (B) · `C_provenance.md`/`.csv` (C) · `D_demo_runbook.md` with `D_demo_capture.json` (D) · `E_architecture.md` (E) · `F_results_pointer.md` (F) · `G_census_dogfood.md` (G) · `H_limits.md` (H) · `appendix/indicator_<CODE>.md` ×49 and `appendix/rules.md` · `numbers.json` (the ledger of prose numbers). There are 61 generated files. One script writes all of them, `scripts/build_brief_pack.py`. Its `--check` re-renders the pack and byte-compares it: `0 drifted`. `--capture-demo` is the one mode that runs commands, and it is the only writer of the capture file. The pages E, F, G, H and INDEX read the projection (Finding reasons, digests, SUPERSEDES chains, Results). With Neo4j down, their test skips with the reason and the graph-free pages are still compared.

## 2. Coverage, as measured
- **Evidence-cell locators:** 9 of 49 cells (A1, A3, A8, A10, A12, B3, D3, D4, G4) by `report_traceability.locators()`. The task expected "8 of 49 before G4"; this is 8 plus G4, which matches the G4 RESULT §6 item 2.
- **Edges and gaps:** 27 of 147 `EVIDENCED_BY` edges point at a document their cell locates. 16 indicators have no `EVIDENCED_BY` edge.
- **Cited documents:** 82 distinct documents, drawn from 264 admitted.
- **Federal instruments:** the Evidence Act (A1, D4), M-25-05 (A1, D4), M-23-22 (A8, B3) and DCAT-US (A3, A8, D4, G4) each have admitted documents. Title 13, CIPSEA and the SPDs have no admitted document in this corpus, and page C says so.
- **Delta:** 49 indicator nodes. 24 have a current rule. 5 carry a departure quote from skeleton §8 or a record field. The operator column (`kept_verbatim_or_restated`) is left empty, as decision 2 orders.

## 3. Demo commands and diagrams
**Commands.** All 11 steps exited 0, and none failed. The adopter runbook took 773 s and the spot loopback test took 28.81 s. Each step's source text is asserted verbatim in its source file.

**Diagrams.** All 4 Mermaid diagrams were validated by `mmdc` (the Mermaid CLI parser, installed at `/opt/homebrew/bin/mmdc`), one test each. Every box's `file:line` is resolved from the code at render time. The worked verdict is CENSUS `A10` (`fnd_2b6bb1732e02a90e488b9639`, `RULE-A10-v3`), the leg its rank rests on. Its SUPERSEDES chain runs rj4 → rj3 → rj2 → rj1 → generation 0.

## 4. Premises the task file got wrong
1. **Manifest `source_type`.** The manifest has no `source_type`. The field is `identity.doc_type` (federal, academic, industry, standard, intergovernmental, practitioner, platform), and it has no statute, OMB or W3C split. Page C prints `doc_type` and says so.
2. **The record's `generated_from`.** It is a path (the skeleton), not a commit. The headers carry the last commit that wrote the record, `9ffcffddbf8f`.
3. **`rules_built` and access tier.** Neither is an indicator field. `rules_built` is a `counts` total (24), and rule existence is derived per indicator from `rules.CURRENT`. The access tier is the record's `tier`.
4. **"Start Neo4j."** No file in the repository documents a start command; the DBMS runs under Neo4j Desktop. Runbook step `neo4j` is the projection round-trip test instead, and the page says why.
5. **The gate.** The task names `gate-fast`. The full suite ran, per CLAUDE.md's pre-push rule.
6. **The spend estimate.** It said 4M tokens. The measured total is in §5; most of the difference is cache reads.
7. **Found, not fixed.** The record's `measurement_status` lags the cycle of record. B1, B2, B4, B5, D2, D3 and G4 read `harness_built`, yet each is judged on `scan_2026-09-10_rj4`. Page H shows the lag in a column and does not correct the record, which is outside this write set. The generation-0 Finding in the A10 chain has no `cycle` property on the graph, and page E prints that verbatim.

## 5. Measured session tokens
The total is taken from this session's transcript (`46b14e7a…jsonl`), summing `message.usage` over 76 assistant messages deduplicated by message id, which is the ccusage method; ccusage itself is not installed. Model `claude-opus-5`. Input 152, output 79,008, cache creation 235,893, cache read 11,827,440: **12,142,493 tokens**. That was measured before this RESULT was written. The complete, commit and push calls come after it and are not counted.
