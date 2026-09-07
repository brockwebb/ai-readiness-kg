# CC Task — Apply the week chain; review every rule against its spec; build the scan target list

**Date:** 2026-09-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on `2026-09-06_harness_scaffold_RESULT.md` and seldon `2026-09-06_task_precedes_relationship_RESULT.md`)
**Fulfils:** ResearchTask `scan-targets` (`22fb59b2`). Requires the seldon build that ships `precedes` (AD-029, domain 0.3) — check `seldon --version` / `seldon task chain --help` before §1; if absent, STOP and report.
**Premise (from the harness RESULT):** 16 rules at `v1`, none reviewed against its `MeasurementSpec` by anyone but its author; 15 indicators `harness_built`; 4 specs `none_known` (C4-auto, F2, F3, G3); F-UJI deferred with `fuji.available: false`; `www.bls.gov` 403 on 60/60 requests and `www.census.gov` on 26/62 under the identified UA while their robots.txt permits the paths; `seldon verify` reports 117 illegal `Precedence` endpoints rendered as `? [missing] → ? [missing]`, pre-existing.
**Spend:** §2 only — one Opus call per rule (16) at the `judge` floor; calibrate on 3, declare the ceiling (DD-042); **stop above 800k settled**. No Fable pass: this is a conformance review, not a rating, and its output is a diff, not a label. §1, §3, §4 zero.
**Zero edits to:** rule *verdicts* in stored Findings (rules are versioned; a fix is `v2`, never an edit to `v1`), the smoke-run evidence, `assessment/cq/*.yaml`, the G1 harness, the vocabulary log, indicator content in the JSON other than the one `candidate` addition in §4.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling. Glob and read all siblings `2026-09-06_scan_targets_ADDENDUM*.md` before starting.**

---

## 1. Chain migration and verify (zero spend)
1. `seldon task chain 09745466 22fb59b2 e3e38014 c1ede3d9 2517cda8 --reason "week chain, DataFile framework_task_chain_2026-09-06"`.
2. `seldon task precede 2517cda8 37476f34 --reason "ER research resumes after the report draft"`; then each of the five DD-049 §3 debt tasks `precedes 37476f34` (read their ids from the graph, not from memory).
3. `seldon task update 09745466 --state completed` if the harness RESULT did not already move it (check first).
4. `seldon verify` under the new build. If the 117 `Precedence` issue persists, find what the 117 endpoints are (labelled query on the edge type the check reads) and report: real orphaned edges from an earlier experiment, or a check reading a relationship this repo never wrote. Fix only if it is data in this repo; if it is the check, register a seldon ResearchTask naming it.
5. Confirm `seldon go` now shows **Next ready** = `scan-targets` and the chain, and paste that block into the RESULT.

## 2. Rule review — conformance to spec, not correctness of verdicts (spends)
For each of the 16 `v1` rules, one Opus call, hermetic cwd, given: the `MeasurementSpec` node's `signal`, `evidence_kind`, `prior_art`; the indicator's skeleton row (construct, definition, AUTO/DOC/EVAL, tier); the rule module source; the two control fixtures' expected verdicts. Asked for: `conforms | deviates | spec_underspecified`, and for `deviates` the specific clause the rule fails to implement or implements beyond the spec, and for `spec_underspecified` the decision the rule had to make that the spec does not settle. **Withhold** the smoke-run verdicts (anti-anchoring: a reviewer who sees "A2 fails on 15/15" reasons backward from the outcome).
- `conforms` → nothing.
- `deviates` → write `v2` (new module, `v1` untouched), extend the fixtures if the deviation needs a case the fixtures don't exercise, re-run the control gate and the re-derivation gate; the smoke-run Findings under `v1` stay on the log and are **not** re-derived under `v2` — re-derivation is per rule version by construction.
- `spec_underspecified` → write the decision the rule made into the `MeasurementSpec` as a `decision` property with the rule version that made it, so the spec and the rule agree and the gap is closed in the framework of record, not in code. Re-render; round-trip test must pass.
Register `rule_review_conforms`, `rule_review_deviates`, `rule_review_underspecified`, and per-rule Results `rule_review_<code>` with the verdict as a string value. Record the review protocol as DD-053.

## 3. Target list (zero spend)
### 3.1 Selection criteria — stated before any URL is chosen
Population: the U.S. principal statistical agencies (the OMB Statistical Policy list; read it from the corpus if admitted, else cite the Statistical Programs of the U.S. Government edition used) plus the Census Bureau's own flagship products already in scope, plus the two non-U.S. comparators the admitted set already contains (StatCan; add one more only if the corpus already admits a document from it). For each agency, three surface kinds:
- **flagship product landing page** — the page a human would call the product (e.g., the Employment Situation release page, ACS data page);
- **machine entry point** — the documented API root, bulk-download index, or `data.json` catalog for that product or the agency;
- **agency-level well-known set** — `/robots.txt`, `/sitemap*.xml`, `/llms.txt`, `/data.json`, `/.well-known/` (always fetched; this is a synthetic surface per host, not a document).
One flagship per agency minimum; two where the agency has an obviously distinct second flagship (e.g., BLS CPI alongside Employment Situation; Census ACS alongside Decennial). Do not choose products because they look good or bad for the instrument; choose by the agency's own "principal products" or "featured data" listing, and cite where each came from.
### 3.2 Admission
Every landing page and machine entry point is admitted into `corpus/manifest.json` under a new epoch `scan-2026-09` with `source_type: product_surface`, `construct_arm: publication_actionability`, `primary_url`, and `content_hash` of the first capture — the same admission pattern as `g1sfc-2026-09-03`. `OBSERVED_ON` requires a `:Document`; a target that is not admitted cannot be scanned. Register the target list as snapshot DataFile `scan_targets_2026-09` with columns: agency, surface kind, url, selection source (the listing it came from), admitted doc_id.
### 3.3 Observability pre-flight — manners, not evasion
Before the full scan, one probe per host: robots.txt, then a single HEAD and GET of the flagship page under the identified UA. Record the outcome per host as an Observation (`host_preflight`). A host that answers 401/403/429 to an identified compliant client is **unobservable**; it stays on the target list, its surfaces will produce `error` Findings, and it is reported as such. **No UA spoofing, no proxying, no retry storms.** Where the agency documents a machine access route (API key, bulk mirror, data.gov catalog entry), record it as the machine entry point — that *is* the observation the instrument wants. Register `scan_targets_hosts`, `scan_targets_hosts_unobservable`, `scan_targets_surfaces`.

## 4. Candidate indicator — declared vs enforced machine access
Add to `framework/ai_readiness_framework.json` one `AssessmentIndicator` with `status: candidate`, under criterion A, construct "Access policy coherence": *an identified, robots-compliant machine client that robots.txt permits is served (not refused by a WAF or bot-manager)*. Type AUTO, tier `public`, `MeasurementSpec` = the §3.3 pre-flight (`collector: http` + `robots`, rule `RULE-A12-v0` placeholder). `EVIDENCED_BY_INTERNAL` → the harness RESULT §5 and DD-052 §6a; `EVIDENCED_BY` → any admitted document on robots.txt semantics (RFC 9309 if admitted; else record the gap). Render; the round-trip test must pass with the candidate row appearing in a **separate "Candidate indicators" table**, not in the A table — candidates are not the framework until the operator promotes them, and the renderer must make that visible. DD-054 records why it is a candidate: it is the public-observable leg of what A11 assumed needed edge logs, it was found by the harness rather than the literature, and promotion is an operator decision because the framework goes out under his name.

## 5. Progress page
Re-run `framework_progress.py`; candidates appear as their own status class, not counted in any fraction's denominator. Register the fractions.

## 6. Reporting
RESULT: `cc_tasks/2026-09-06_scan_targets_RESULT.md`. Lead with the rule review table (16 rows, verdict, what changed), then the `seldon go` block, then the target list summary (agencies, surfaces, unobservable hosts), then the 117 disposition. State every premise this task got wrong. `python -m pytest tests/ assessment/`, `seldon verify`, control and re-derivation gates green, round-trip green, `git diff` empty on the protected files. `seldon cc complete`; move `22fb59b2` to completed with this RESULT as evidence; commit, push.

**SEQUENCING:** §1 → §2 → §3.1 → §3.2 → §3.3 → §4 → §5 → §6. §3 does not wait on §2's fixes landing; §2's `v2` rules are what `scan-run` will use.
