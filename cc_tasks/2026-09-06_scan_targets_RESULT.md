# RESULT — Week chain applied; every rule reviewed against its spec; the scan target list built

**Task:** `cc_tasks/2026-09-06_scan_targets.md` (no addenda; globbed, none exist)
**Date:** 2026-09-06 · **Executed by:** Claude Code
**Spend:** §2 only. **515,478 tokens settled** against the task's 800,000 stop — 98,568 on the 3-rule calibration and 416,910 on the remaining 13. The DD-042 ceiling was computed from the **measured** rate (32,856 tok/rule) rather than the `judge` call-class floor (36,000), and registered as `rule_review_tokens_declared` = 491,000 before a single reservation was taken. §1, §3, §4 and §5 spent nothing.
**Prerequisite:** the seldon build ships `precedes` (AD-029) — `seldon task chain` and `seldon task precede` both present. Not a stop condition.

---

## 1. The rule review — 0 of 16 rules conform to their MeasurementSpec

The harness RESULT named this the open question: *"Every rule is at `v1` and none has been reviewed against its `MeasurementSpec` by anyone but its author."* One Opus call per rule, hermetic cwd, given the spec's `signal` / `evidence_kind` / `prior_art`, the indicator's skeleton row, the rule source, and the two fixtures' expected verdicts. **The smoke-run verdicts were withheld** (rubric v1.3.0 §2 anti-anchoring): a reviewer told "A2 failed on 15 of 15" reasons backward from the outcome, and a rule that fails everything looks broken whether or not it is.

**13 `deviates`, 3 `spec_underspecified`, 0 `conforms`.**

| leg | verdict | conf | the clause the code did not implement | disposition |
|:--|:--|--:|:--|:--|
| A1 | deviates | 0.72 | *extract every download link; for each, HEAD and read Content-Type and file extension* | **`RULE-A1-v2`** |
| A2 | deviates | 0.88 | *record auth scheme, declared rate limits, and whether the description is machine-readable* | **`RULE-A2-v2`** |
| A3 | deviates | 0.85 | *classify links as bulk (whole-product archive or full dataset file) vs filtered query* | **`RULE-A3-v2`** |
| A6 | deviates | 0.90 | *validate the DCAT graph against DCAT-AP SHACL shapes* | **`RULE-A6-v2`** |
| A8 | deviates | 0.88 | *test whether a latest-vintage pointer resolves* | **`RULE-A8-v2`** |
| A10 | deviates | 0.85 | *compare status codes and pre-JS HTML; a soft-404 is HTTP 200 with an error shell* | **`RULE-A10-v2`** |
| A11-declared | deviates | 0.78 | *the DECLARED layer only: robots.txt **and meta-robots directives*** | **`RULE-A11-declared-v2`** |
| B3 | deviates | 0.72 | *and whether it is retrievable without JS* | **`RULE-B3-v2`** |
| D1 | deviates | 0.88 | *read the licence from schema.org/DCAT markup, **an HTTP Link header, and the API's terms endpoint*** | **`RULE-D1-v2`** |
| D4 | deviates | 0.76 | *validate against the POD v1.1 schema* | **`RULE-D4-v2`** |
| E5 | deviates | 0.60 | *both control fixtures are scanned **before any real host*** | **`RULE-E5-v2`** |
| F4 | deviates | 0.90 | *test whether it is machine-readable **and carries a revision class per entry*** | **`RULE-F4-v2`** |
| G1-D | deviates | 0.62 | *error measures present as STRUCTURED FIELDS … rather than as footnotes* | **NOT CONFIRMED** — see §1.2 |
| A4 | spec_underspecified | 0.72 | the signal never settles the verdict when **no robots.txt is served** | `decision` on the spec; no code change |
| A5 | spec_underspecified | 0.72 | the signal never settles what a served **llms.txt** contributes | `decision` on the spec; no code change |
| A9 | spec_underspecified | 0.68 | the signal never settles what counts as a **served** machine-first entry point | `decision` on the spec; no code change |

**1.1 The shape is one habit, not sixteen bugs.** In twelve of thirteen `deviates` the rule implements the **first clause** of a multi-clause `signal` and stops. A6's `collector_pin` literally reads `extruct + pyshacl` and the rule never ran SHACL. D4's spec says *validate against the POD v1.1 schema* and no branch consumed a validation result — the schema-derived counts were interpolated into the pass message only. **This is invisible from inside a control gate**, because the fixture was built to the same cheap clause by the same author in the same sitting. A shared misreading passes a control unanimously. That is the precise sense in which a green control gate is necessary and not sufficient, and it is why this had to be a separate instrument rather than another fixture.

**1.2 One model finding did not survive verification, and the cause is a flaw in the protocol the task specified.** Every `deviates` was checked by hand against the collector and the runner before any `v2` was written. G1-D's did not hold: the reviewer said nothing distinguishes a structured field from footnote prose, and the field-scoping is real — it lives in `runner.py`, which slices `<th>` cells, a CSV header row, or a JSON head before the rule ever sees a token. **§2 of the task listed *"the rule module source"* among the reviewer's inputs and did not list the collector, and a rule is half of a measurement.** A conformance review that sees only the rule will over-report deviation whenever a clause is satisfied upstream. Recorded as DD-053 §5; the next run of this instrument ships the collector path with the rule. G1-D's second point — `tokens` computed and then used only for `len()` in the fail message — is real, is cosmetic, and did not earn a version bump.

**1.3 `deviates` → a new module; not one `v1` line was edited.** `rules/__init__` now carries `REGISTRY` (every version ever shipped) beside `CURRENT` (what a new cycle judges with), and `rederive.py` re-judges each stored Finding under **its own** `rule_id`. Verified, not asserted: **all 286 Findings from the `v1` smoke cycle re-derive byte-identically under their own `v1` rules and their own `v1` params**, read from git rather than reconstructed. History was not re-scored. Three tests hold it, including one that fails if any `v1` module's bytes change.

**1.4 `spec_underspecified` → the decision goes in the framework, not in the code.** A4 decides that a missing robots.txt is a `fail` (the indicator asks whether a policy was *declared*, and a host that declared nothing did not declare permission — RFC 9309's "absence permits" answers the crawler's question, not A4's). A5 decides that a covering sitemap is the sole pass path. A9 decides that a non-HTML 2xx body with content is a served entry point, without parsing the descriptor. **All three rules already decided; the decision simply was not written down.** In every case both control fixtures land on their stated verdicts under either reading, so the difference is only visible on a real surface — a gap the controls structurally cannot see.

**1.5 The `v2` rules needed evidence nobody had collected.** A rule is pure and cannot go and look, so most of the work was in the collectors: `collectors/links.py` HEADs every same-host download link (A1, A3); `collectors/extent.py` computes the two shallow features of Kohlschütter, Fankhauser & Nejdl (WSDM 2010) — **DD-030's own corpus extent gate, reused rather than reinvented**, so a methodology page that would have been refused admission to the corpus cannot be scored as legible here (B3, A10); `collectors/v2clauses.py` parses OpenAPI auth and rate-limit declarations, runs pyshacl, dereferences latest-vintage pointers, reads meta-robots and RFC 8288 `Link` headers, validates POD v1.1, and classifies changelog entries.

Two validators are **stated minimal subsets**, and each rides its profile name on every Finding so a pass can never be misread as conformance: `shapes/dcat_ap_min.ttl` (`dcat_ap_min`) carries DCAT-AP's mandatory Dataset/Distribution properties, not the DCAT-AP distribution; `shapes/pod_v1_1_min.schema.json` (`pod_v1_1_min`) carries POD v1.1's required fields, not its controlled vocabularies. Vendoring a snapshot of either would create a silent fork and fetching it at scan time would make a measurement depend on a third party being up. **A related trap, closed:** a schema.org `@context` given as a string makes rdflib fetch `https://schema.org` — a "pure parse" that reaches the network, which would have made the control fixtures non-hermetic. It is now substituted for a local `@vocab`.

**1.6 The control fixtures were extended, and both gates are green under `v2`.**

```
CONTROL GATE: PASS — both control fixtures fired and every rule returned its expected verdict
RE-DERIVATION GATE: PASS — 31 of 31, identical: true          (v2 control cycle, new params)
RE-DERIVATION GATE: PASS — 286 of 286, identical: true        (v1 smoke cycle, v1 rules, v1 params)
```

`passes_all` gained a whole-product `.zip` above the bulk floor, an OpenAPI with `securitySchemes` and a declared rate limit, a resolving latest-vintage pointer, and ~2,500 visible characters of real prose on both the product and methodology pages; the fixture server learned `HEAD` (with `Content-Length`, per RFC 9110 §9.3.2 — A3 sizes candidates from it) and `application/zip`. Link probing is now same-host-only: the fixture links out to a licence URL, and without that the control cycle would have reached the real internet **before the gate that exists to run before any real host**.

## 2. `seldon go` — the chain

```
**Chains:** 1
- (branching — 11 tasks, 10 edges)
    - 09745466 [completed] → 22fb59b2 [proposed]     harness-scaffold → scan-targets
    - 22fb59b2 [proposed]  → e3e38014 [proposed]     scan-targets → scan-run
    - e3e38014 [proposed]  → c1ede3d9 [proposed]     scan-run → eda-and-charts
    - c1ede3d9 [proposed]  → 2517cda8 [proposed]     eda-and-charts → report-draft
    - 2517cda8 [proposed]  → 37476f34 [proposed]     report-draft → er_research_resumes
    - 43edd2cc / 26214693 / f9c5d054 / d9c26f0c / 4e132d0e → 37476f34   (the five DD-049 §3 ER debt items)
```

`scan-run` (`e3e38014`) is correctly **not** in `Next ready`; `er_research_resumes` waits on six predecessors. `09745466` was already `completed` — the harness RESULT moved it — so §1.3 was a no-op, checked first as the step says.

**§1.5's premise is wrong in a way worth stating.** It expects `seldon go` to show **Next ready = `scan-targets`**, singular. It shows `Next ready: 14`, of which `scan-targets` is one. The chain did exactly what it should; the graph simply holds thirteen other unchained `proposed` tasks, and "next ready" is a set, not a queue head. Nothing to fix.

## 3. The 117 `Precedence` endpoints — it is the check, and it is not this repo's data

```
✗ Precedence   117 illegal endpoints — readiness is unanswerable
   illegal endpoint: ? [missing] → ? [missing] — both ends must be a ResearchTask   ×117
```

**All 117 are `(:Concept)-[:PRECEDES]->(:Concept)`.** `precedes` is a **whitelisted edge type in this repo's own `kg/schema.yaml`** — `Concept → Concept`, aligned to `BFO_0000063` — extracted from source documents, and it predates AD-029. Examples: `'Readiness' → 'Piloting'`, `'Term generation and selection' → 'Definition identification and selection'`.

The cause is a **Cypher trap this repo has already recorded once**: `seldon/core/precedence.py:read_edges()` runs `MATCH (a)-[r:PRECEDES]->(b)` with **no label on either endpoint**, and this project's Neo4j database holds the KG and Seldon's artifact graph side by side under disjoint labels — which is the documented arrangement, stated in the project's own CLAUDE.md. The pattern binds every node. A `:Concept` carries no `artifact_id`, hence `? [missing] → ? [missing]`. Two graphs independently chose the same relationship name and the check reads the name without reading the label.

It is **not fixable from this repo**: the edges are correct data, and the remedy the check suggests (`seldon task unprecede`) cannot address them. Registered as seldon ResearchTask **`1ad92c2b`** with the fix (`MATCH (a:Artifact)-[r:PRECEDES]->(b:Artifact)`, endpoint labels still unfiltered *within* that so a genuinely dangling Artifact endpoint — the case the code's own docstring exists for — still surfaces) and a test that co-tenants a non-Artifact `PRECEDES` edge and asserts `verify` stays green. Every other `seldon verify` check is green.

## 4. The target list

**Population, fixed before any URL was chosen.** The 13 U.S. principal statistical agencies as enumerated by OMB **Statistical Policy Directive No. 1** (79 FR 71610, 2014-12-02), read from the **fss-policy-kg** corpus (`spd_1`, segments s22–s39) rather than from memory — each agency row carries its own segment id. No such document is admitted in this repo's corpus, so §3.1's fallback applies and the edition is cited. Plus StatCan, the one non-U.S. comparator the admitted corpus already contains; no second was added, because §3.1 permits one *"only if the corpus already admits a document from it"* and no other national statistical office does. **Recorded rather than silently resolved:** `sap_policy_m_23_04` §s33 counts **16** agencies and units recognized under 44 U.S.C. §§ 3561(11)/3562 — the three additional recognized *units* are out of scope because the task says principal statistical agencies.

**Selection, also fixed before any product was chosen** (§3.1: *"Do not choose products because they look good or bad for the instrument"*). Written into `targets.yaml`, then applied mechanically to the candidates harvested from each agency's own listing, **in the agency's own document order**: flagship = the first anchors that name a product (surviving the reject and section token lists, deeper than the listing itself); machine = the first anchor matching `machine_entry_tokens`, else `<host>/data.json` if served. Where that yields something the author would not have picked — EIA's *Open Data* landing becoming a flagship because *Browse data »* took the machine slot first — **the pick stands** and the row records the anchor text it came from.

| agency | dept | flagship | machine | robots | /data.json | listing | admitted |
|:--|:--|--:|--:|:-:|:-:|:--|--:|
| BEA | Commerce | 2 | 1 | 200 | 200 | read | 3 |
| BJS | Justice | 2 | 0 | 200 | 404 | read | 2 |
| BLS | Labor | 0 | 0 | **403** | **403** | refused | 0 |
| BTS | Transportation | 0 | 0 | **403** | **403** | refused | 0 |
| CENSUS | Commerce | 2 | 1 | **404** | 200 | read | 3 |
| EIA | Energy | 2 | 1 | 200 | 404 | read | 3 |
| ERS | Agriculture | 2 | 1 | 200 | 404 | read | 3 |
| NASS | Agriculture | 2 | 1 | 200 | 404 | read | 3 |
| NCES | Education | 0 | 0 | 200 | 404 | **no product links without JS** | 0 |
| NCHS | HHS | 2 | 1 | 200 | 404 | read | 3 |
| NCSES | NSF | 1 | 1 | 200 | 404 | read | 2 |
| ORES | SSA | 0 | 0 | **403** | **403** | refused | 0 |
| SOI | Treasury | 2 | 0 | 200 | 404 | read | 2 |
| STATCAN | (comparator) | 2 | 1 | 200 | 404 | read | 3 |
| **total** | | **19** | **8** | | | | **26 admitted / 27 attempted** |

Plus **14 agency-level well-known sets** — one synthetic surface per host, not a document, and therefore not admitted: there is nothing to admit. **41 surfaces in total.**

**4.1 Three of thirteen principal statistical agencies refuse an identified, compliant client.** `www.bls.gov`, `www.bts.gov` and `www.ssa.gov` answered 401/403 to `ai-readiness-kg-scanner/0.1` on **every** probe — robots.txt included — while their own robots.txt permits the paths. This is not evasion territory: **no UA spoofing, no proxying, no retry storms**, per §3.3. Their surfaces stay on the target list and will produce `error` Findings, because dropping a surface for having refused us would quietly restrict the instrument to the agencies that let us look, which is the worst possible sampling frame for an accessibility assessment. This finding is what §4's candidate indicator exists to name.

**4.2 Host identity is verified, not asserted.** `publisher.name` from a served `/data.json` where there is one (BEA, CENSUS), else the home page `<title>`. "bls.gov is the Bureau of Labor Statistics" rests on a stored capture. **Only 2 of 14 hosts serve a `/data.json` at all** — a striking figure for a set of agencies covered by the OPEN Government Data Act, and one D4 will measure properly rather than in passing. **The Census Bureau serves no robots.txt** (404).

**4.3 NCHS does not control its own host.** It is a section of `www.cdc.gov`, so its agency-level well-known set is CDC's. Recorded on the roster row, because a finding against `www.cdc.gov/robots.txt` is a finding about a parent department and not about the statistical agency.

**4.4 NCES's own data-tools listing is not readable without JavaScript** — HTTP 200, three links, all navigation. Not a refusal and not our failure to find it: discovery from the home page was tried and the home page is client-rendered too. NCES contributes only its well-known set, and **no flagship was substituted from elsewhere**, per the roster's own rule.

**4.5 One target is deliberately not admitted.** `https://www.eia.gov/survey/` — `eia.gov/robots.txt` disallows it for this UA and the scanner obeys the file it measures.

## 5. A12 — a candidate, not an indicator

*An identified, robots-compliant machine client that robots.txt permits is served (not refused by a WAF or bot manager).* Criterion A, construct **Access policy coherence**, AUTO, tier `public`, `RULE-A12-v0` placeholder, `EVIDENCED_BY` → `rfc-9309-robots-exclusion-protocol` and `cloudflare-ai-crawl-control-manage-crawlers` (**both already admitted** — no evidence gap to record), `EVIDENCED_BY_INTERNAL` → the harness RESULT §5, DD-052 §6a and this task's pre-flight.

It is the **public-observable leg of what A11 assumed needed edge logs**: A11 puts the enforced layer at `agency_instrumented` because a WAF is not visible from outside, which is true in general and false for the one case where robots.txt *permits* a path and the host *refuses* a compliant client asking for that same path. Where robots.txt disallows, A12 is `not_applicable` — that is A4's measurement, not a coherence failure.

**A11 is not edited.** Amending its tier in place would erase the finding: the record would read as though the framework had always known this leg was public, and the fact that the instrument discovered it *by being refused* would be gone.

**Candidates are separated in the rendering, not flagged in a column** (DD-054). `rows_from_json` excludes them; `render_candidate_table` emits *"Candidate indicators (not part of the framework)"* with a `Where it came from` column; and `skeleton_rows` truncates at that heading, because a candidate row looks exactly like a criterion row and would otherwise leak back in through the round trip it was kept out of. The progress page counts candidates in **no** numerator and **no** denominator, and says so in a banner rather than omitting them silently. Four tests hold all of this. Round-trip gate: **0 explained, 0 unexplained, PASS.**

## 6. Every premise this task got wrong

**6.1 §2 gave the reviewer the rule and not the collector.** The single most consequential error, because it inflates `deviates` — one of thirteen did not survive verification (§1.2). A rule is half of a measurement.

**6.2 §1.5 expects `Next ready` to *be* `scan-targets`.** It is one of 14 ready tasks (§2 above).

**6.3 §3.2 assumes admission is one step. It is two, and the first pass did only one.** `corpus/manifest.json` is the projection of the **dixie evidence ledger**, not of the event log (invariant 2). Twenty-six documents passed `kg.manifest.add` and **none appeared in the manifest**, because the `screening_imported` half was never written. Both halves are now written and the script is idempotent across them.

**6.4 `kg.manifest.add` gates provenance and duplication, not extent — and a zero-byte document went through it.** `https://www.eia.gov/beta/api/` is robots-disallowed; the fetcher correctly declined, and an **empty file was admitted**. The second EIA surface was refused only because it hashed to the *same* empty string — duplicate detection doing by accident what an extent check should have done on purpose. Corrected the only way the invariants allow: a `content_update` (`extent_corrected`) replacing the empty bytes with a record of the disallow, plus a guard that refuses an empty capture.

**6.5 Re-running the admitter re-captured live pages, and drift followed.** Six surfaces changed between two captures minutes apart, so the stored hash no longer matched the admission event; and the empty-capture guard *deleted the stored file* of a document that was already on the ledger, because a not-re-fetched document has `bytes: None`. Six `content_update` (`source_revised`) events record the drift honestly, and the admitter now never re-captures or deletes anything for a document already admitted. `python -m kg.manifest verify`: **clean**.

**6.6 §5 assumed the progress page would need no change to handle candidates.** It would have counted A12 in every denominator, making the instrument look *less* complete for having noticed something. Candidates are now excluded from both sides of every fraction and reported as their own class.

**6.6a §2.3's integer-literal lint refused five of this task's own constants** — `msgs[:10]`, `errors[:10]`, `low_text[:40]`, and two `round(x, 4)` — written into the new collectors before the test caught them. All five are now `params.reporting`. The lint has now fired on two consecutive tasks, both times on its own author, which is the strongest argument for it.

**6.7 The task's premise line says F-UJI is deferred with `fuji.available: false`.** Still true; nothing here changed it. A6-v2 and D4-v2 validate against **this repo's own stated minimal profiles**, not against F-UJI, and say so on every Finding.

## 7. Verification

| gate | result |
|---|---|
| `python -m pytest tests/ assessment/` | **1,439 passed, 2 skipped** (55 in `test_scan_harness.py`, 16 in `test_framework_graph.py`) |
| control gate (under `v2`) | **PASS** — 31/31 control Findings as expected |
| re-derivation gate, `v2` control cycle | **PASS** — 31 of 31, `identical: true` |
| re-derivation gate, `v1` smoke cycle under `v1` rules | **PASS** — 286 of 286, history not re-scored |
| round-trip gate (`render_framework.py --check`) | **PASS** — explained 0, unexplained 0 |
| `python -m kg.manifest verify` | **clean** — all local files present and unchanged |
| `seldon verify` | 1 issue, the `Precedence` check reading another graph's edges (§3); every other check green |
| `git diff` on protected paths | **empty** — `assessment/cq/`, `kg/vocab.py`, the G1 harness and its fixtures, `kg/vocab.py` untouched; every `v1` rule module byte-identical (asserted by test) |
| model spend | 515,478 settled of the 800,000 stop; ceiling 491,000 declared from the measured rate before reserving |

## 8. What this does not claim

**No surface was measured.** 26 documents were admitted and 41 surfaces are on the list; not one has been scanned under `v2`. That is `scan-run`'s job (`e3e38014`), which this task's chain now correctly gates behind it. The twelve `v2` rules have passed their control fixtures and nothing else, and `measurement_status` stays `harness_built` throughout — a `v2` rule is still a harness.

The review itself is **one rater, one pass, one rubric version**, and its single verified false positive (§1.2) is the honest error rate to quote: 1 of 13, on a protocol flaw now recorded and fixable. A12 is a **candidate**, and §5 of DD-054 states what would have to be true to promote it — evidence from a second compliant client identity, which the harness will not obtain by impersonating a browser, because that is the evasion §3.3 forbids. That asymmetry is a finding for the operator to weigh, not a gap for the machine to close.
