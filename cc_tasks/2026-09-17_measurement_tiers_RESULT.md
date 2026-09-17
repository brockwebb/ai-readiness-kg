# RESULT: every indicator carries a measurement tier or a reason, and the tool map's verdicts come from the record

**Task:** `cc_tasks/2026-09-17_measurement_tiers.md` (ResearchTask `f6370ad6`). I globbed `2026-09-17_measurement_tiers_ADDENDUM*.md` before starting and again before §4. Neither glob found an addendum.
**Session:** launched headless by the standing dispatcher (`dispatch_launched` at 2026-09-17T15:40:26Z) from HEAD `52af6c7`. The predecessor, `2026-09-17_dispatcher_notifies.md`, already had its RESULT and its `dispatch_finished` record (`bc80869`), so the SEQUENCING line held.
**Framework layer served:** DN-005 §2.2 (measurement capability tiered three ways).
**Spend:** zero model calls. **Network:** none beyond `git push`.
**Gate:** green, with every command run to its `EXIT=` line before this file was written.
- `make gate-full` (the full tier, `-rs`): **2311 passed, 3 skipped, 12 xfailed, 0 deselected**, `EXIT=0`, wall-clock 1479.64 s.
- `seldon verify`: all checks passed, `EXIT=0`.
- `scripts/check_protected_measurement_tiers.sh`: `PROTECTED PATHS OK`, `EXIT=0`.
The log paths are in §6.

**In one paragraph.** All 49 indicators now carry either a tier or a recorded reason for having none. 29 carry `measurement_tier`, `measurement_basis` and `tier_source`: **27 M, 1 O, 1 D**. **20 carry `tier_unassigned_reason` and no tier**, because none of decision 2's rules reached them. Each reason names the tier its evidence points at, as a candidate for the next task. The tool map's §2 verdict is now derived from those fields, and the C-class rows no longer claim a page fetch would measure a benchmark. The product matrix no longer says G1-D was withdrawn from it. G1-D's existing `measurement_tier: product` moved to `measurement_level`, because it named a surface level, not a tier (§5 premise 3).

## 0. What prior art already had

- **A tier field under another name exists, and it is a different axis.** Every node carries the skeleton's `tier` (`public` / `agency_instrumented` / `paid`, skeleton `docs/crosswalk/usafacts_operationalization_skeleton.md` §6b.1, the schema's `Measure.tier` enum). §6b.1 defines it by **whose cooperation or funding observing the property needs**. It was assigned by a default ("All AUTO indicators default here"), which is exactly what this task forbids for a tier. I kept it and did not reuse it as M/O/D. F6 shows why the two differ: it is `tier: paid` (the publisher pays to sign releases) and `measurement_tier: O` (anyone can verify the attestations with open tooling). DN-005 ADDENDUM_01 §1 records this.
- **A basis field under another name exists too.** Every node also carries the skeleton's `type` (`AUTO`, `DOC`, `EVAL` and combinations). It is close to `measurement_basis` but not the same: `DOC` mixes things the agency must *answer* with things it must *expose*, and that split is the D/M boundary. I cite `type` in the reasons and do not derive the basis from it.
- **`measurement_tier` already existed on one node, with a different meaning.** `ind:G1-D` carried `measurement_tier: product` (DD-066 §6), meaning the surface level at which the construct can be measured. DD-066 §6 says the tiering task "may rename the field, but it does not remove this one". The value and its source text moved verbatim to `measurement_level` / `measurement_level_source`. The two readers of that key moved with them: `build_l0_site.INDICATOR_LABELS` and `tests/test_publication.py`. The published appendix's seven G1-D rows now say `measurement_level: product`.
- **`withdrawn_from` already existed on G1-D** (`withdrawn_from: host-level`, with its source). Decision 5 allowed "`withdrawn_from: L0-host`" on the record. The record already said it in the instrument's own term, so I wrote nothing new there.
- **The "Screaming Frog investigation" is not a document.** No file in `docs/`, `cc_tasks/` or `corpus/` records one. The only record is ResearchTask `43108db6` in `seldon_events.jsonl` (created 2026-09-09T01:37:13Z): "No Screaming Frog; open stack already covers its functions". It names the open tools that replace it: the Common Crawl index API, the Wayback CDX API and Google Dataset Search presence. There is also one line in a gitignored handoff (`handoffs/2026-09-10_thread_close_harness_v5_rejudge_dispatched.md` §3 row 11). I cite the ResearchTask. A stranger can read that; the handoff is not tracked.
- **The G1 instrument's definition** is DD-036 §2. G1-D is the deterministic `g1_declared` probe. G1-O is the v2 evaluation: a pinned consumer restates the captured surface, and the family preservation rate is scored. That makes G1-O the judged reading, not G1-D (§5 premise 4).
- **The June harness's probes** (`assessment/harness/probes/`: `d1_stable_urls`, `d3_schema`, `d3_provenance`, …) are this project's own code and are not rules in `rules.CURRENT`. Rule 1 does not reach them. The unassigned reasons for A7, B1, D3 and G4 name them as candidates.
- **The framework writer's contract** is `scripts/framework_writeback.py::save`. It refuses any drop of a node, edge or `counts` key, puts the delta on the event, and treats an identical write as a no-op. The write went through it: event `a711f730a1474bbfbf0f05bf2e95577a` on `events/batch-033_framework.jsonl`, 49 nodes changed, no node, edge or `counts` key added or dropped, framework sha256 `23f79076…93b6bd`. A second run returned `unchanged: true`. `scripts/build_framework_graph.py --dry-run` over the new record is still a byte-for-byte no-op (`nodes_changed: 0`, `unchanged: true`).

## 1. The table: all 49 indicators

The task file asked for 44 rows. The record holds 49 indicator nodes (§5 premise 1). This table is generated from the record as written, so it is the record's own text.

| code | status | tier | basis | rule | source (definition quote where the source is the definition) |
|---|---|---|---|---|---|
| A1 | measured | M | harness_leg | rule 1 | rules.CURRENT['A1'] = RULE-A1-v4 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A1` |
| A10 | measured | M | harness_leg | rule 1 | rules.CURRENT['A10'] = RULE-A10-v3 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A10` |
| A11 | measured | M | harness_leg | rule 1 | rules.CURRENT['A11-declared'] = RULE-A11-declared-v2 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A11-declared` |
| A12 | specified | M | harness_leg | rule 1 | rules.CURRENT['A12'] = RULE-A12-v3 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A12` |
| A2 | measured | M | harness_leg | rule 1 | rules.CURRENT['A2'] = RULE-A2-v3 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A2` |
| A3 | measured | M | harness_leg | rule 1 | rules.CURRENT['A3'] = RULE-A3-v6 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A3` |
| A4 | measured | M | harness_leg | rule 1 | rules.CURRENT['A4'] = RULE-A4-v1 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A4` |
| A5 | measured | M | harness_leg | rule 1 | rules.CURRENT['A5'] = RULE-A5-v2 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A5` |
| A6 | measured | M | harness_leg | rule 1 | rules.CURRENT['A6'] = RULE-A6-v2 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A6` |
| A7 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| A8 | measured | M | harness_leg | rule 1 | rules.CURRENT['A8'] = RULE-A8-v4 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A8` |
| A9 | measured | M | harness_leg | rule 1 | rules.CURRENT['A9'] = RULE-A9-v1 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A9` |
| B1 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| B2 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| B3 | measured | M | harness_leg | rule 1 | rules.CURRENT['B3'] = RULE-B3-v3 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:B3` |
| B4 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| B5 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| B6 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| C1 | specified | M | evaluation | rule 5 | definition of `ind:C1` in framework/ai_readiness_framework.json: "Benchmark question set per product; answer accuracy of a retrieval-paired model vs published values" |
| C2 | specified | M | evaluation | rule 5 | definition of `ind:C2` in framework/ai_readiness_framework.json: "Entailment-judged: do model statements about the product entail from product text?" |
| C3 | specified | M | evaluation | rule 5 | definition of `ind:C3` in framework/ai_readiness_framework.json: "does retrieval return the vintage asked for?" |
| C4 | specified | M | evaluation | rule 5 | definition of `ind:C4` in framework/ai_readiness_framework.json: "Generative engines citing the product cite the authoritative page (not aggregators)" |
| C5 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| D1 | measured | M | harness_leg | rule 1 | rules.CURRENT['D1'] = RULE-D1-v3 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:D1` |
| D2 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| D3 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| D4 | measured | M | harness_leg | rule 1 | rules.CURRENT['D4'] = RULE-D4-v2 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:D4` |
| E1 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| E2 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| E3 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| E4 | specified | D | declaration | rule 2 | docs/design/scan_tool_map.md §2 at commit 52af6c7 (verdict `not web-observable`), confirmed against the definition: a held-out set is by construction not published, so whether a rotation exists is a fact only the agency holds; definition of `ind:E4`: "Public eval sets have a held-out rotation" |
| E5 | harness_built | M | harness_leg | rule 1 | rules.CURRENT['E5'] = RULE-E5-v2 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:E5` |
| E6 | specified | M | evaluation | rule 5 | definition of `ind:E6` in framework/ai_readiness_framework.json: "Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model" |
| E7 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| E8 | specified | M | evaluation | rule 5 | definition of `ind:E8` in framework/ai_readiness_framework.json: "Versioned golden question/answer sets re-run on schedule against the product surface" |
| E9 | specified | M | evaluation | rule 5 | definition of `ind:E9` in framework/ai_readiness_framework.json: "Standing adversarial bank: vintage traps, confusable series, unit traps, DP-noise misreads, suppression probes" |
| F1 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| F2 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| F3 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| F4 | measured | M | harness_leg | rule 1 | rules.CURRENT['F4'] = RULE-F4-v3 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:F4` |
| F5 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| F6 | specified | O | open_tool | rule 3 | corpus/crosswalk/slsa-specification-v1-0.md (doc_id `slsa-specification-v1-0`), page 'Distributing provenance': "SLSA requires the distribution and verification of provenance metadata in the form of SLSA attestations"; FAQ 'How does SLSA relate to in-toto?': the specification recommends in-toto attestations (https://github.com/in-toto/attestation) as the vehicle to express provenance; definition of `ind:F6`: "Signed releases / provenance attestations" |
| G1-D | measured | M | harness_leg | rule 1 | rules.CURRENT['G1-D'] = RULE-G1-D-v1 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:G1-D` |
| G1-O | measured | M | judged_reading | rule 5 | DD-036 §2 (docs/design_decisions.md): G1-O is the v2 EVAL; spec `spec:G1-O` names its collector; instrument: the G1 instrument: DD-036 (docs/design_decisions.md), assessment/harness/probes/g1_preservation.py, frozen at v2; definition of `ind:G1-O`: "when the pinned consumer restates that same captured surface" |
| G2 | specified | M | evaluation | rule 5 | definition of `ind:G2` in framework/ai_readiness_framework.json: "EVAL: vintage disambiguation (ties C3)" |
| G3 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| G4 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| G5 | specified | — | — | no rule reaches it | unassigned, reason in §2 |
| G6 | specified | M | judged_reading | rule 4 | docs/design/scan_tool_map.md §2 at commit 52af6c7 (verdict `content-evaluation`), confirmed against the definition; instrument: the G1 instrument: DD-036 (docs/design_decisions.md), assessment/harness/probes/g1_preservation.py, frozen at v2; definition of `ind:G6`: "The consumer-side test: an AI system asked to compare values across a break must surface the break" |

**Notes carried on the nodes (`tier_note`).**

- **A11.** The rule measures the DECLARED layer only (leg `A11-declared`). The enforced and observed layers need edge or WAF logs and crawler request logs, which spec `spec:A11-declared` places at `agency_instrumented`.
- **A12.** A CANDIDATE indicator (DD-054): its rule runs and enters no framework numerator until the operator adopts it.
- **C1.** No such instrument exists yet.
- **C2.** The definition names the probe protocol, 're-aimed', as the instrument; it has not been re-aimed at a data product.
- **C3.** No such instrument exists yet.
- **C4.** No such instrument exists yet; spec `spec:C4-auto` records `collector: none_known` for the URL-resolution half.
- **E5.** The rule judges this instrument's own cycle (its control fixtures), not a publisher's; `not_measured_reason` on this node says why that is not `measured`.
- **E6.** The failures it localizes are an evaluation's outputs (retrieval and model stages), so it presupposes the C1 to C3 evaluations. No such instrument exists yet.
- **E8.** No such instrument exists yet.
- **E9.** No such instrument exists yet.
- **F6.** Verifying a published attestation against the artifact is the open-tool act. The skeleton's `tier: paid` is the PUBLISHER's cost of signing, a different axis. Rule 3 is read with decision 1's source list, which names 'a tool's documentation on disk'; the tool map §3 and the open-tool record name no tool for F6.
- **G1-D.** A deterministic structured-field rule (`RULE-G1-D-v1`, the frozen `g1_declared` probe, DD-066 §7), not a judged reading: G1-O is the leg the G1 instrument judges. Measured on product surfaces only (`measurement_level`).
- **G1-O.** Reached by rule 5, and its basis is `judged_reading` rather than `evaluation` because the instrument exists: it is the one rule 4 cites.
- **G2.** docs/design/scan_tool_map.md §2 at commit 52af6c7 said `content-evaluation`; rule 4's confirmation fails because the reading the definition asks for is C3's evaluation, not the G1 instrument, so rule 5 reaches it. The declared half (revision status machine-readable per value) is a structured-field test no rule makes yet. No such instrument exists yet.
- **G6.** The consumer-side half is a G1-style preservation test (does the restatement keep the qualifier); the declared half, the versioned epoch carried as metadata, is a structured-field test no rule makes yet.

## 2. Counts

| tier | n | | basis | n |
|---|---|---|---|---|
| M | 27 | | harness_leg | 17 |
| O | 1 | | judged_reading | 2 |
| D | 1 | | evaluation | 8 |
| unassigned | 20 | | open_tool | 1 |
| **total** | **49** | | declaration | 1 |

- **Sources that are `estimate`: 0.** Every assignment rests on a locator into `rules.CURRENT`, the tool map at `52af6c7`, a document on disk, DD-036, or a verbatim quote from the indicator's definition. `scripts/tag_measurement_tiers.py` checks each quote as a substring of the definition before writing. I considered an estimate-sourced O for A7 (via the Wayback CDX API) and for B1 and B2 (via `extruct`). Each would have rested on this session's reasoning about reach, not on a source that names the tool for that spec, so I recorded them as candidates.
- **Decision 4's Cypher, run live after projection** (`logs/measurement_tiers_cypher.log`):
  - `D declaration 1 [E4]`
  - `M evaluation 8 [C1 C2 C3 C4 E6 E8 E9 G2]`
  - `M harness_leg 17 [A1 A10 A11 A12 A2 A3 A4 A5 A6 A8 A9 B3 D1 D4 E5 F4 G1-D]`
  - `M judged_reading 2 [G1-O G6]`
  - `O open_tool 1 [F6]`
  - `— — 20 [A7 B1 B2 B4 B5 B6 C5 D2 D3 E1 E2 E3 E7 F1 F2 F3 F5 G3 G4 G5]`
  - G1-D: `{'t': 'M', 'l': 'product', 'w': 'host-level', 'old_gone': True}`.
  `tests/test_measurement_tiers.py` asserts the same distribution as a literal against the record and against the graph.

**How the rules were read.** These readings are logged here, and the operator can override them.

1. **Rule 2's "confirmed against the definition" also applies to rule 4.** Both rules key on a tool-map verdict, and every one of those verdicts was a keyword match (`scripts/scan_tool_map.py` at `52af6c7` matched "document", "policy", "process" and similar words). Decision 3 retires the keyword match. Using its output unchecked in rule 4 would have turned a keyword default into a tier. The check failed for E7, G3 and G5, and for G2, which fell through to rule 5.
2. **Rule 3's source list includes decision 1's "a tool's documentation on disk".** That source kind only makes sense for an O assignment. Under this reading F6 is reached: `corpus/crosswalk/slsa-specification-v1-0.md` requires "the distribution and verification of provenance metadata" and names in-toto attestations as the vehicle.
3. **Rule 5 reaches an indicator when its value is the output of running the named evaluation**, not whenever its text contains the word "eval". This is why E1, E2 and E3 are unassigned (§5 premise 5). E6, E8 and E9 are reached. G1-O is reached, but its basis is `judged_reading`, because its instrument exists and it is the one rule 4 cites.
4. **A12 and E5 are M/harness_leg by rule 1, applied mechanically, and each node's note says what that does not mean.** A12 is a CANDIDATE (DD-054) and enters no numerator. E5's rule judges this instrument's own cycle, not a publisher's. A11's rule covers the declared layer only.

**The 20 unassigned indicators, with the reason each node carries.**

| code | reason (`tier_unassigned_reason`) |
|---|---|
| A7 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; no rule in rules.CURRENT serves it and no on-disk source names an open tool for it. Candidates: M through the June harness's assessment/harness/probes/d1_stable_urls.py (resolves a distribution URL; not a rule in rules.CURRENT), or O through the Wayback CDX API that ResearchTask 43108db6 names for robots.txt history, which would reach URL persistence across time. |
| B1 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; no rule serves it. Candidates: M through assessment/harness/probes/d3_schema.py (a `describedBy` data dictionary), or O through `extruct` reading schema.org `variableMeasured`; the tool map §3 names `extruct` for A6 only. |
| B2 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; no rule serves it. Candidate: O through `extruct` over schema.org `DefinedTerm` (the evidence cell cites `schema-org-definedterm`); the tool map §3 names `extruct` for A6 only, and 'versioned' is not a DefinedTerm property. |
| B4 | docs/design/scan_tool_map.md §2 at commit 52af6c7 said `not web-observable`, and the definition does not confirm it: 'published as metadata, not prose' is a property of a served surface, so rule 2 does not reach it and no other rule does. Candidate: M, the structured-field test G1-D already makes for the error-measure subset. |
| B5 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; the definition ('Same concept ⇒ same identifier across products/vintages') needs two products or vintages compared, and no rule, collector or on-disk tool does that. Candidate tier undetermined. |
| B6 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; presence is fetchable, but 'plain-language' and 'current' need a judged reading and no rule reaches it. Candidate: M, judged_reading. |
| C5 | The definition ('Product scored against published AI-data-readiness metrics') names published metrics, not a benchmark, an eval set, entailment or what a generative engine does, so rule 5 does not reach it; the tool map verdict was the keyword default. Candidate: O through AIDRIN (`aidrin-hiniduma-2024`, `aidrin-2-0-a-framework-to-assess-data-readiness-for-ai`), but neither paper's text on disk says where the tool is obtained, so rule 3 cannot cite it. |
| D2 | docs/design/scan_tool_map.md §2 at commit 52af6c7 said `not web-observable`, and the definition does not confirm it: terms of use are published text. The tool map §3 response-header row names D2 as a consumer with 'no library needed', which is a harness path and not an open tool. Candidate: M, a terms or header leg, or a judged reading of the terms. |
| D3 | docs/design/scan_tool_map.md §2 at commit 52af6c7 said `not web-observable`, and the definition does not confirm it: 'Source lineage published' is a served surface. Candidate: M; assessment/harness/probes/d3_provenance.py reads source and date signals, which is less than lineage. |
| E1 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; the definition names an eval set, but its value is how results are REPORTED, not the output of running an evaluation, so rule 5 does not reach it. Candidate: D, or a judged reading of a published report. |
| E2 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; the definition names an eval, but its value is whether thresholds are published and pre-registered, not the output of running one, so rule 5 does not reach it. Candidate: D (pre-registration is verifiable only against the agency's own timestamps). |
| E3 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; 'Eval sets and rubrics carry versions' is a practice of whoever runs the evaluation, not the output of running one, so rule 5 does not reach it. Candidate: D. |
| E7 | docs/design/scan_tool_map.md §2 at commit 52af6c7 said `content-evaluation` (the keyword was 'document'), and the definition does not confirm it: 'mean-time-to-closure tracked' is an agency process, not a reading of a served surface, and its value is not an evaluation's output. Candidate: D. |
| F1 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; 'pass a published expectation suite ... before going live' happens before publication, on the agency's side. Candidate: D; the suite's publication alone would be observable. |
| F2 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; spec `spec:F2` records `collector: none_known`. Candidate: O through `oasdiff` (an open-source OpenAPI breaking-change detector), which would reach 'compatibility checked mechanically'; no on-disk source names it, so it is the next tool-map row rather than a citation. |
| F3 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; spec `spec:F3` records `collector: none_known`. Candidate: O through a web archive's CDX index (ResearchTask 43108db6 names the Wayback CDX API), which would supply the prior vintage's endpoints. |
| F5 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; 'Canary/staging surface ... AI-consumer regression run before promotion' is on the agency's side of publication. Candidate: D. |
| G3 | docs/design/scan_tool_map.md §2 at commit 52af6c7 said `content-evaluation`, and the definition does not confirm it: stable series IDs and machine-readable crosswalks are structured properties, not a judged reading. Spec `spec:G3` records `collector: none_known`. Candidate tier undetermined. |
| G4 | docs/design/scan_tool_map.md §2 at commit 52af6c7 gave the keyword default (`scan-observable`, "`http` + `structured_data` would serve it"), which is not a derivation; 'carried as structured metadata' is observable, but no rule serves it; assessment/harness/probes/d3_provenance.py reads the issuing-authority half (publisher, bureauCode) and nothing reads the statutory mandate. Candidate: M. |
| G5 | docs/design/scan_tool_map.md §2 at commit 52af6c7 said `content-evaluation` (the keyword was 'document'), and the definition does not confirm it: 'documented machine-readably with unique identifiers' is a structured-field test, not a judged reading. Candidate: M, harness_leg. |

By the candidate each reason names, the 20 fall roughly into these groups. This is a map for the next task, not an assignment:

- **D (agency-side):** E1, E2, E3, E7, F1, F5.
- **M (a structured-field or harness leg not yet built):** B4, D3, G4, G5, and D2 (a terms or header leg).
- **O (an open tool not yet cited on disk):** B2, C5, F2, F3, and A7 or B1 (both also have an M candidate).
- **M, judged reading:** B6.
- **Undetermined:** B5, G3.

## 3. The tool map's C-class rows, before and after

Before (`docs/design/scan_tool_map.md` at `52af6c7`):

```
| C1 | Benchmark question set per product; answer accuracy of a r | **scan-observable** | `http` + `structured_data` would serve it |
| C2 | Entailment-judged: do model statements about the product e | **scan-observable** | `http` + `structured_data` would serve it |
| C3 | Version/vintage disambiguation: does retrieval return the  | **scan-observable** | `http` + `structured_data` would serve it |
| C4 | Generative engines citing the product cite the authoritati | **scan-observable** | `http` + `structured_data` would serve it |
| C5 | Product scored against published AI-data-readiness metrics | **scan-observable** | `http` + `structured_data` would serve it |
```

After (regenerated by `scripts/scan_tool_map.py` from the record):

```
| C1 | Benchmark question set per product; answer accuracy of a r | M | **content-evaluation** | an evaluation this project would build; source: definition of `ind:C1` in framework/ai_readiness_framework.json: "Benchmark question set per product; answer accuracy of a retrieval-paired model vs published values" |
| C2 | Entailment-judged: do model statements about the product e | M | **content-evaluation** | an evaluation this project would build; source: definition of `ind:C2` in framework/ai_readiness_framework.json: "Entailment-judged: do model statements about the product entail from product text?" |
| C3 | Version/vintage disambiguation: does retrieval return the  | M | **content-evaluation** | an evaluation this project would build; source: definition of `ind:C3` in framework/ai_readiness_framework.json: "does retrieval return the vintage asked for?" |
| C4 | Generative engines citing the product cite the authoritati | M | **content-evaluation** | an evaluation this project would build; source: definition of `ind:C4` in framework/ai_readiness_framework.json: "Generative engines citing the product cite the authoritative page (not aggregators)" |
| C5 | Product scored against published AI-data-readiness metrics | — | **unassigned** | no tier assigned: The definition ('Product scored against published AI-data-readiness metrics') names published metrics, not a benchmark, an eval set, entailment or what a generative engine does, so rule 5 does not reach it; the tool map verdict was the keyword default. Candidate: O through AIDRIN (`aidrin-hiniduma-2024`, `aidrin-2-0-a-framework-to-assess-data-readiness-for-ai`), but neither paper's text on disk says where the tool is obtained, so rule 3 cannot cite it. |
```

Changes to `scripts/scan_tool_map.py`:

- The keyword classifier is removed. `verdict_for` reads `measurement_basis`, and `VERDICT_BY_BASIS` is the only mapping.
- A `scan-observable` row names the collector entry point and the `MeasurementSpec` clause it reaches. A12 is the only harness-leg row in §2: "`http.fetch`, `robots.fetch` (via `RULE-A12-v3`) reaches the spec clause 'Per host: GET /robots.txt and parse it; then GET the product path under the identified UA'". Otherwise the row says `no collector reaches this yet`, as it does for F6.
- §2 gains a tier column.
- A new §4 lists all 49 indicators with tier, basis, rule and source. That is the indicator-listing view decision 4 asked to show the tier column. The report's source appendix lists *checks*, all of them M by construction, so a tier column there would carry no information, and the report and its PDF were not rebuilt.
- `tests/test_scan_frame.py::test_the_tool_map_regenerates_byte_identically` still guards the file.
- `tests/test_measurement_tiers.py` asserts three things:
  - each §2 verdict equals the one its basis implies;
  - a `scan-observable` row names a reach or says there is none;
  - no row uses the old default as its own reason.

## 4. The header move (decision 5)

Before this task, `build_l0_matrices.compute` built one header dict and every matrix used it. The published `docs/reports/scan_matrix_product_2026-09-10_rj2.json` therefore said `legs_withdrawn: [G1-D]`, which is the opposite of the record: G1-D is measured on product surfaces and has 104 product-tier passes on the log (DD-066 §2).

- `compute` now also returns `product_head`, which is the host header minus `legs_withdrawn`, with the key order otherwise unchanged. `write_matrices` writes the product matrix from it.
- The host matrices (tier A and tier C) keep the header. It is true there: the withdrawal is from `home` and `well_known` surfaces.
- I rebuilt the six matrix files and five fragments into a temporary tree and compared them with the published ones. Only `scan_matrix_product_2026-09-10_rj2.json` differed, and only that file was copied: 9 lines removed, none added.
- `tests/test_publication.py::test_every_published_matrix_is_what_its_cycle_computes_now` now expects no withdrawal on the product matrix.
- `tests/test_measurement_tiers.py::test_the_product_matrix_does_not_carry_the_host_level_withdrawal` asserts the move itself.
- On the record, G1-D's node already carried `withdrawn_from: host-level` and now carries `measurement_level: product` beside `measurement_tier: M`. That entry is where a stranger would look for the fact.

## 5. Premises this task file got wrong

1. **"44 indicators".** The record holds **49** `AssessmentIndicator` nodes: 48 adopted plus A12 as a candidate. `counts.indicators` is 48 under DD-054's candidate exclusion. There was no count of 44 anywhere, so the RESULT table has 49 rows.
2. **"12 have a spec, a rule and sources, and the harness measures the L0 six plus A1, A3, A8, B3, D4 and G1-D".** `rules.CURRENT` holds 17 legs, which serve 17 indicators:
   - A1, A2, A3, A4, A5, A6, A8, A9, A10, A11 (declared leg), B3, D1, D4, F4 and G1-D, all `measured`;
   - E5, `harness_built`;
   - A12, a candidate.
   G1-O is also `measured`, by the G1 instrument. The record has **16** `measured` indicators and 22 `MeasurementSpec` nodes. The "12" is the report's source-appendix checks (`report_traceability.LEGS`), not the framework's measured set. "The 12 measured indicators resolve this way and nothing else" therefore could not hold: rule 1 reaches 17.
3. **`measurement_tier` was treated as a new field.** G1-D already carried it with the value `product` (DD-066 §6), and two readers depended on that key: the site's appendix labels and a publication test. Writing M/O/D over it would have silently changed a published label's meaning, so the value moved to `measurement_level` (§0).
4. **"M, basis `harness_leg` (or `judged_reading` for G1-D)".** G1-D is the deterministic structured-field rule `RULE-G1-D-v1` (DD-066 §7), so it is `harness_leg`. The judged reading is G1-O (DD-036 §2), which the task file did not mention and which rule 1 does not reach, because it has no rule in `rules.CURRENT`.
5. **"C1 to C5, E2, E3, E8, E9 on their face" name an evaluation.**
   - C5's definition names "published AI-data-readiness metrics", not a benchmark, an eval set, entailment or a generative engine's behaviour.
   - E2's value is whether thresholds are published and pre-registered.
   - E3's value is whether eval sets carry versions.
   Neither E2 nor E3 is the output of running an evaluation. All three are unassigned, with reasons. C1 to C4, E8 and E9 are reached as the task file expected. E6 and G2 are reached as well.
6. **"The tool map's `not web-observable` verdict (A12, B4, D2, D3, E4) … Sound."** That verdict came from the same keyword classifier: "policy", "process" and "organisation" matched. Checked against the definitions it holds only for E4.
   - A12 is measured by a harness rule.
   - B4 ("published as metadata"), D2 (published terms) and D3 ("Source lineage published") describe served surfaces.
   Likewise, `content-evaluation` holds for G6 only. E7, G3 and G5 matched on "document" and similar words, and G2's reading is C3's evaluation.
7. **"The Screaming Frog investigation (find it; cite its path)".** There is no investigation document. The decision not to use Screaming Frog is ResearchTask `43108db6`, cited in §0.
8. **"The header belongs on the L0 host matrix or in the framework record's G1-D entry as `withdrawn_from: L0-host`".** The record entry already existed as `withdrawn_from: host-level` (the instrument's term, read by `scripts/withdrawn_legs.py`), so nothing was written there. The host matrices already carried the header, and they keep it.
9. **Decision 6: "`docs/` byte-identical except the tool map and any report page that prints the tier column".** Writing the record makes the site's published copy stale by construction. `tests/test_publication.py` asserts that every published copy equals its source by sha256. So these also moved, each by its own generator (`scripts/build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest`):
   - `docs/data/ai_readiness_framework.json`;
   - `docs/data/index.json` (digests and build stamp only);
   - `docs/data/sources_per_check.json` (G1-D's label key only).
   `scripts/check_protected_measurement_tiers.sh` asserts each of these line by line.
10. **Not a premise of the task file: a defect the narrow build exposed.** `--only data_manifest` wrote `index.json` with digests computed from citation text dated **today**, but it did not write the citation files. The manifest then recorded digests and a `built_at` date that no published citation file had, and five standing tests failed. The citation files now travel with the manifest in `_ONLY["data_manifest"]`. `tests/test_publication.py::test_the_manifest_digest_of_each_citation_file_is_the_file_published` was written first and failed before the fix. As a result, `CITATION.cff`, `.zenodo.json` and their `docs/data/` copies moved on their date line only (2026-09-16 → 2026-09-17), because the published data did change today. `--only sources_per_check` was added to the builder's declared list for the appendix payload.
11. **Two historical scripts still name the old key, and I left them as records.**
    - `scripts/check_protected_derived_counts.sh` line 172 checks `measurement_tier == product` on the published appendix. It is that task's own protected-paths check, and it would now fail if re-run.
    - `scripts/tag_g1d_product_tier.py` would write `measurement_tier: product` back if re-run. `tests/test_measurement_tiers.py` would then fail, both on an illegal tier value and on the tagger no-op check, so the suite guards it.
    Neither script is called by anything.

**The next task under DN-005 §4 item 3** is the prescription schema for the Tier M checks, authored from §1. Its natural scope is the 17 `harness_leg` rows, the ones with cold data behind them. The 20 unassigned rows are a separate, smaller task: each reason already names its candidate and the source it lacks.

## 6. Gate

**Tier:** `make gate-full` (the whole suite, `-rs`, detached and polled). This is not the fast tier. The task touched no rule module, the registry or the re-derivation engine, so `gate-task`'s re-derivation adds nothing beyond the full run, which includes it.

| check | result | log |
|---|---|---|
| `make gate-full` | **2311 passed, 3 skipped, 12 xfailed, 0 deselected**, 248 warnings, 1479.64 s, `EXIT=0` | `logs/suite.log` |
| skips | `tests/test_dispatch_config.py:333` (interactive_only: this is a dispatched session); `tests/test_scan_harness.py:281` (E5 judges the cycle's controls, not a surface); `assessment/tests/test_g1_preservation.py:337` (no dev proposition publishes SE and CI together) | `logs/suite.log` |
| `seldon verify` | all checks passed (34833 events readable; replay skipped as expensive, per its own default), `EXIT=0` | `logs/measurement_tiers_seldon_verify.log` |
| protected paths | `PROTECTED PATHS OK`, `EXIT=0` (`scripts/check_protected_measurement_tiers.sh`) | `logs/measurement_tiers_protected.log` |
| framework projection | `scripts/load_framework_graph.py`, `EXIT=0`; the round-trip gate is green inside the suite | `logs/measurement_tiers_projection.log` |
| tier Cypher | §2 | `logs/measurement_tiers_cypher.log` |
| site payloads | `build_l0_site.py --only sources_per_check --only framework_copy --only data_manifest`, `EXIT=0` (final run; the first two exposed premise 10) | `logs/measurement_tiers_site_3.log` |

**Write set as committed:**
- the record: `framework/ai_readiness_framework.json`, written through `framework_writeback.save`, plus event `a711f730…` on `events/batch-033_framework.jsonl`;
- code: `scripts/tag_measurement_tiers.py` (new), `scripts/scan_tool_map.py`, `scripts/build_l0_matrices.py`, `scripts/build_l0_site.py`;
- checks: `scripts/check_protected_measurement_tiers.sh` (new);
- tests: `tests/test_measurement_tiers.py` (new), `tests/test_publication.py`;
- the DN-005 addendum: `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal_ADDENDUM_01.md` (new);
- regenerated and published files: `docs/design/scan_tool_map.md`, `docs/reports/scan_matrix_product_2026-09-10_rj2.json`, `docs/data/{ai_readiness_framework.json,index.json,sources_per_check.json,CITATION.cff,zenodo.json}`, `CITATION.cff`, `.zenodo.json`;
- `seldon_events.jsonl`, from `seldon cc complete`;
- this RESULT.

Nothing under `state/`, `corpus/`, `kg/` or `assessment/` moved. No cycle ran, no Result was registered, and the report and its PDF were not rebuilt.
