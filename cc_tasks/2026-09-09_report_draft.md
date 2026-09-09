# CC Task — report-draft: the L0 product, first draft

**Date:** 2026-09-09
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-08_a8_v4_blind_pointer_and_fixture_table_RESULT.md` and `2026-09-08_scan_run_3b_RESULT.md` (both gates PASS, both tasks `completed` on the graph, cycle `scan_2026-09-09` registered).
**Governing design:** `docs/design/2026-09-08_l0_product_shape.md`. Read it first. It fixes the shape; this task fixes the content sources.
**Fulfils:** its own ResearchTask (`seldon cc register`); supersedes the placeholder `2517cda8`.
**Spend:** zero model calls. **Network: none.** No federal host is contacted. Every figure and every number comes from the graph as it stands.

**Fence:** this task collects nothing, re-runs nothing, judges nothing. It projects the record into a document. Any question that needs a new request, a new rule, or a re-judgement is written down as future research and left there.

**Zero edits to:** shipped rule modules, any registered Result value, the targets DataFile, events beyond this task's own registrations, `params.yaml`, any prior cc_task or RESULT.

**Immutable once written. Glob `2026-09-09_report_draft_ADDENDUM*.md` before starting and again before §3.**

---

## 0. Housekeeping (CLI, first)
1. `seldon task supersede d261be8b --by 3b47290e` with reason "blocked at §1.4 on A8-v3 blind pointer; fulfilled by scan-run-3b". `seldon task supersede 2517cda8 --by <this task's id>`.
2. Register the two figures scan-run-3b left in prose: `fss_scan_netlocs_2026-09 = 22` (description: distinct netlocs on `scan_targets_fss_2026-09` v2; the roster stays 19 hosts, agency-level) and `fss_scan_netlocs_contacted_2026-09-09 = 24` (the 22 plus two apex `robots.txt`, per scan-run-3b RESULT §2). If targets v2 was never registered as a DataFile version, register it now with `derived_from` v1 and scan-run-3b named; if it was, say where.
3. Register A12 per tier from existing cycle-3 Findings, new names, no re-judgement: `scan_a12_tierA_pass_2026-09-09 = 11`, `_fail = 4`, `_error = 1`, `scan_a12_tierC_pass_2026-09-09 = 3`. Each Result's description names the pooled `scan_a12_pass_2026-09-09 = 14` it decomposes.
4. For every A5 `fail` in cycle 3, record on the Result description (or one aggregate Result `scan_a5_fail_offroster_sitemap_2026-09-09 = N`) how many fails are hosts whose `robots.txt` declares a sitemap off the roster that the scanner did not follow. That number is a caveat the report must carry; if it is zero, the report says zero.

## 1. Build the matrices (data, not prose)
1. `scan_matrix_tierA_2026-09-09`: 16 agencies × the six `params.tier0.legs` + one column `refused_identified_client`. Rendered from Findings by the existing `scan_report.matrix()` (tier-corrected in scan-run-3b §8). Emit CSV and JSON beside the report, each row carrying the Finding identities it summarises.
2. `scan_matrix_tierC_2026-09-09`: the three reference hosts, same legs, separate file, never in a Tier A denominator (DD-059).
3. `scan_matrix_product_2026-09-09`: declared flagship surfaces only, product-level legs (A1, A2, A3, A6, A8, A9, B3, D1, D4, F4). Agencies without a declared flagship appear as rows marked `not declared`, not as fails and not omitted. Label the file and the report section PARTIAL with the count of declared agencies as a registered Result.
4. One movement figure: leg rates cycle 2 → cycle 3 with rule changes and the frame change marked (F5 already does this; reuse, do not redraw).

## 2. Draft the report
`docs/reports/2026-09_fss_ai_readiness_L0.md`, through the build pipeline so every number is `{{result:NAME:value}}`. Sections and length per the design note (matrix on one page, at most six pages around it). Specifically:
- **Frame:** who the 16 are, the OMB list cited, the 3 reference hosts and why they are outside the denominator, the client identity (DD-060), one request budget line.
- **Host-level matrix** (primary). One paragraph per leg, plain words, no rule versions in the body (versions go in the appendix).
- **Refusals:** BLS, BTS, SSA, five consecutive measurements, two UA strings, three days; stated as a finding about accessibility with the count registered. No speculation on why.
- **Product-level matrix** (secondary, PARTIAL). Seven legs at zero across the declared surfaces; the Hanley and Lippman-Hand rule of three stated at the actual n per leg, upper 95% bound registered as a Result per leg (`scan_leg_rate_<leg>_upper95_2026-09-09`), not computed in prose.
- **What the matrix cannot see:** rendered pages, machine use (EVAL), hosts that refused us, the 7 undeclared flagships, the A5 off-roster caveat from §0.4, the one `error_class_unknown`.
- **Movement since cycle 2:** the instrument moved (four rules, one frame); a reader comparing rates across cycles compares two instruments over two populations. One figure.
- **Future research,** one sentence each, evidence in hand named: refusal by identity (`ae58c74e`), third-party observed access (`43108db6`), same-site contact bound (cycle 4), product-level completion after flagship declarations.
- **Method appendix:** rules by version per leg, fixtures, request count per netloc, graph access path, DD-060, DD-061.
- **Last row:** the report's own host, scored on the six host-level legs by hand-reading (no scan), marked `self-assessed`. If it cannot be scored yet because the report has no host, the row says so.

Banned in the body: em dashes, "load-bearing", "hallucinate" (use "confabulate"), a number typed as digits outside a `{{result}}` tag, the same phrase twice.

## 3. Gate (the one gate of this task)
The build resolves every `{{result:...}}` tag (zero unresolved), and a lint over the built body finds **zero bare numerals in prose** outside tags, tables, and the appendix (years and section numbers exempt; declare the exemption regex in the lint). Every matrix CSV row re-derives from the graph by Cypher (extend the `test_scan_figures` re-derivation to the three matrix files). Hygiene green; `seldon verify` green.
**Failure writes no report file to `docs/reports/`: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-09_report_draft_RESULT.md`: gate first; the list of registered Results this task created; the A5 off-roster count; page count of the built report; every premise this task got wrong. `seldon cc complete`, commit, push. **Do not publish anywhere beyond the repo.** The operator reads the draft; nothing goes out under his name from this task.

**SEQUENCING:** §0 → §1 → §2 → glob addenda → §3 (hard stop) → §4 → push.
