# CC Task — KG diagnostic as code, and the competency-question coverage/conciseness harness

**Date:** 2026-09-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session
**Spend:** zero model spend. CC authors CQs itself; no `claude -p`.
**Prior art:** competency questions as the KG coverage test (Grüninger & Fox 1995; still the standard method, e.g. KG-EmpiRE 2023, Q²Forge K-CAP 2025). The duplicate-union measurement is the *conciseness* dimension of Zaveri et al. 2016 (Semantic Web 7:63–93) — redundancy of entities — not an invented metric. Paulheim 2016 for refinement/evaluation framing.

**Immutable once written. Changes require a new task file or an `_ADDENDUM-NN.md` sibling.**

---

## 0. The defect this task first documents

On 2026-09-04 the Desktop session ran four diagnostic Cypher queries against `seldon-ai-readiness-kg` **in chat, through `neo4j-mcp`**, and drew conclusions from them. Nothing consequential lives only in chat; this was a Desktop authorship error. The figures below are therefore **premises to verify, not facts**:

- 8,662 Concept; 1,122 exact-lowercase-name duplicate groups covering 3,479 nodes; `AI readiness` as 14 nodes / 44 in-edges
- Concept degree: median 1; 4,246 at degree 1; 617 isolated; 398 at ≥5; max 26
- 25,227 domain edges (non-Artifact); top: `Document-MENTIONS->Concept` 6,715, `Document-ASSERTS->Claim` 4,459, `Claim-ABOUT->Concept` 4,152
- Cross-document integration: `Document-CITES->Document` 28, `Claim-CONFLICTS_WITH->Claim` 3, `Definition-CONFLICTS_WITH` 1
- 4,509 Claims, 50 with no `ASSERTS` source; 211 Documents, 0 without extractions, median 30 extractions/doc
- Every Concept carries `doc_id`, `prov_*`, `grounding_span`; 8,129 carry `aliases`

### 0.1 Reproduce as code
`scripts/kg_diagnostic.py`: the same queries, parameterised by database, emitting JSON. Register the script; register every figure as a Result with `--name kg_diag_<metric>` and `--script-name kg_diagnostic` and `--data-name` the graph snapshot (register a DataFile `kg_snapshot_<date>` = a `neo4j-admin dump` or, if that is heavier than warranted, the event-log/Result of `MATCH (n) RETURN count(n)` plus label counts written to `state/kg_snapshot_<date>.json`, `snapshot: true`). Report every figure that differs from the chat premise.

### 0.2 Record the error
Append a DesignNote (DD-next) in `docs/design_decisions.md`: diagnostic-in-chat is the defect; `scripts/kg_diagnostic.py` is the mechanism that replaces it; rule going forward: any graph figure quoted in a handoff, memo, or decision must resolve to a `kg_diag_*` or CQ-harness Result by name.

## 1. The measurement: competency-question harness

### 1.1 Purpose
Decide, with a pre-registered rule, whether the absence of entity resolution blocks the KG's intended uses, before spending anything on entity resolution or on probe design that assumes the KG answers questions it cannot.

### 1.2 CQ set — authored BEFORE any query runs, committed first
`assessment/cq/cq_set_v1.yaml`. Derive from the framework's own constructs: read `docs/crosswalk/assessment_protocol.md` (constructs, orientation-first rule, discovery stack, frontier candidates), the G1 instrument docs, and the Instrument/Framework/Standard/Measure label populations. Minimum 24 CQs, at least 3 in each category:

| category | example shape |
|---|---|
| construct definition | "How do documents in the corpus define *uncertainty legibility* (or its nearest terms)?" |
| measure lookup | "Which Measures operationalise construct X, and in which Instruments?" |
| instrument coverage | "Which of the framework's constructs are measured by no Instrument in the corpus?" |
| claim evidence | "What Claims support Practice P, and from which Documents?" |
| conflict detection | "Where do two Documents make conflicting Claims about X?" |
| provenance traceback | "For Claim C, return the grounding span, source sha, and extraction event." |
| discovery stack | "Which Platforms consume which Standards of the established discovery stack (RFC 9309, sitemaps, RFC 8615, schema.org Dataset, DCAT)?" |
| frontier candidate | "What does the corpus assert about MCP / llms.txt as discovery mechanisms, with dates?" |

Each CQ record: `id`, `question`, `category`, `cypher_raw`, `cypher_collapsed` (see 1.3), `expected_shape` (columns, cardinality range), `pass_criterion` (pre-registered: e.g. "≥1 row whose grounding span, on reading, addresses the question"), `judge_notes` (empty until run). **Commit the file before the first run; the RESULT cites the commit SHA.** A CQ edited after its first run is a new `id` with `supersedes`.

### 1.3 Two views, same question
- `raw`: the graph as it is.
- `collapsed`: a query-time canonical key `k = toLower(trim(name))`, with a second level using the `aliases` property (if `aliases` of node A contains name of node B, same group). Implement the collapse once, as a Cypher fragment or a Python post-join, and reuse it; do not write per-CQ collapse logic.

### 1.4 Metrics per CQ (all pre-registered here)
- `answerable_raw`, `answerable_collapsed` ∈ {yes, partial, no}. Judged by CC reading the returned grounding spans against the pass criterion; record the judged rows and the reason. This is an LLM judge and is labelled as such in the report.
- `rows_raw`, `rows_collapsed`.
- `dup_groups_unioned`: number of collapse groups of size >1 that the collapsed answer depends on. This is the Zaveri conciseness cost for that CQ.
- `provenance_complete`: fraction of answer rows traceable to a Document with `prov_source_sha256`.
- `misleading_raw`: yes if the raw answer is non-empty but would mislead a reader who did not know duplicates exist (e.g. returns 3 of 14 `AI readiness` nodes' edges).

### 1.5 Aggregates and the decision rule (pre-registered; do not adjust after seeing data)
- `A_raw`, `A_collapsed`: fraction of CQs answerable (yes) in each view.
- `flip`: fraction of CQs that are `no`/`partial`/`misleading` in raw and `yes` in collapsed.
- `C`: total `dup_groups_unioned` across the set.
- **Rule:** `flip ≥ 0.30` → entity resolution is P0, blocks probe design. `flip < 0.10` → ER deferred; note as a known limitation. Otherwise → ER scheduled as a task with the sift-kg three-layer pattern as the design, not blocking probe design. The RESULT states which branch fired and the CQ ids that drove it.
- Report category-level `flip` too; if one category carries all the flips, say so.

### 1.6 Harness
`assessment/cq/run_cq.py`: loads the YAML, runs both views, writes `assessment/results/cq_v1_<date>.jsonl` (one row per CQ per view) and a markdown report `docs/research/<date>_cq_coverage_v1.md` with the aggregates and the rule outcome. Every aggregate and every per-CQ metric registered as a named Result (`cq_v1_<metric>`, `cq_v1_<cqid>_<metric>`), script and data registered. Rerunnable after any future dedup pass; a rerun is a new dated results file and new Results, never an overwrite.

### 1.7 Judge contamination guard
The CQ author and the judge are the same session. Mitigate: pass criteria are written before queries are run (1.2), and `judge_notes` cite the grounding spans read. Do not revise a pass criterion to make a CQ pass; record the failure.

## 2. Also register as findings, no fix
- 50 Claims with no `ASSERTS` source (Issue artifact, links to a sample of 5 by artifact id).
- Whether `key` on Concept is document-scoped or intended as canonical (read the extraction code; report).

## 3. Integration
Tests for the collapse fragment (a fixture with known duplicate groups yields known group counts) and for the harness's Result registration. `tests/` and `assessment/` green. `seldon verify` clean. `cc complete`; commit and push with the CQ file's pre-run commit SHA in the RESULT.

## 4. RESULT must report
Diagnostic figures vs chat premises, every difference. CQ file pre-run SHA. The per-CQ table (raw/collapsed answerability, rows, dup groups, provenance, misleading). Aggregates, `flip`, `C`, which branch of the rule fired and the driving CQ ids. Category-level flips. Findings from §2. Every premise contradicted.

## 5. Out of scope
Entity resolution itself. Probe design. Any change to extraction. The G1 instrument.
