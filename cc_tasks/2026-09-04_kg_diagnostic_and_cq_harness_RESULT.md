# RESULT: KG diagnostic as code, and the competency-question coverage/conciseness harness

**Task:** `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md` (no addenda: globbed `…_ADDENDUM*.md`, none exist). **Date:** 2026-09-04 UTC. **Spend: zero model calls** — the CQs were authored by this session, the queries are Cypher, and no `claude -p` ran. **Task file committed before execution:** `8890b57`.

**The decision, first: `flip` = 0.269, which fires the middle branch of the pre-registered rule — entity resolution is scheduled as a task, and does not block probe design.** It is not close to the P0 threshold (0.30) and not close to the deferral threshold (0.10); it sits between them, and the category breakdown says exactly where the cost falls.

## 0. The diagnostic, and what re-deriving it found

### 0.1 As code

`scripts/kg_diagnostic.py` (Script `ca49df59`) → `state/kg_snapshot_2026-09-04.json` (DataFile `af95a178`, snapshot per AD-027) → **52 Results** named `kg_diag_*`.

**Nineteen of the twenty chat figures reproduce exactly**: Concept 8,662; 1,122 duplicate groups over 3,479 nodes; `AI readiness` 14 nodes / 44 in-edges; Concept degree median 1, 4,246 at degree 1, 617 isolated, 398 at ≥5, max 26; 25,227 domain edges; CITES 28; Claim CONFLICTS_WITH 3; Definition CONFLICTS_WITH 1; 4,509 Claims with 50 unasserted; 211 Documents, median 30 extractions; 8,129 Concepts with aliases.

**One figure was wrong, and it matters more than the nineteen that were right.**

| premise | measured | |
|---|---|---|
| 211 Documents, **0 without extractions** | **72 of 211 have no extraction edges at all** | DIFFERS |

A third of the corpus is admitted and unextracted — `bandi-2025-metadata-ai-ready`, `cao-2024-multimodal-long-form-summarization`, `census-acs-general-handbook-2020`, `cloudflare-pay-per-crawl` and 68 others. This changes what an unanswerable CQ means: a question can fail because its source was never read, not because entities are duplicated. Registered as `kg_diag_documents_without_extractions` (72) and `kg_diag_documents_extracted` (139).

**Three further first-run differences were defects in my new script, not in the old numbers**, and both root causes are recorded in the script where they happened:

- `concept_degree_*` grouped by `n.name` instead of by node. In a graph with 1,122 duplicate-name groups that silently merges duplicates — it reported max degree 66 where the truth is 26.
- `document_extractions_median` aggregated with no `WITH d` grouping at all, returning 13,757 (the total) as a median.
- `domain_edges_total` was a **definitional** difference, not a bug: 22,141 counts edges whose *both* endpoints carry a KG label; 25,227 counts edges with *no Artifact endpoint*, which is what the premise's "non-Artifact" wording means. Both are now registered, separately named, so a future reader cannot quote one believing it is the other.

### 0.2 The error recorded

**DD-040** appended (DesignNote `1ebcf3b2`): diagnostic-in-chat is the defect; the script, the snapshot and the `kg_diag_*` Results are the mechanism; and the rule — **any graph figure quoted in a handoff, memo, decision or task file must resolve by name to a `kg_diag_*` or `cq_v1_*` Result.** The DD makes the argument the re-derivation actually supports: the chat numbers were *right*, and that is the point — they were right by nobody's verification, and the one that was wrong was wrong in the direction that would have misled the work that followed.

## 1. The CQ measurement

### 1.2 The set, pre-registered

`assessment/cq/cq_set_v1.yaml` (DataFile `2e17d1ba`): **26 CQs, 8 categories, minimum 3 per category** (construct definition 4, measure lookup 3, instrument coverage 3, claim evidence 3, conflict detection 3, provenance traceback 3, discovery stack 3, frontier candidate 4).

**Pre-run commit SHA: `369d717`** — the CQ file was committed alone, before the harness existed and before any CQ query ran. Every pass criterion was written without having seen a single answer, and **no criterion was revised afterwards**; CQ-15 fails and is recorded as a failure (§1.4 below).

### 1.3 One collapse, not twenty-six

`assessment/cq/collapse.py`: canonical key `toLower(trim(text))`, then an `aliases` level unioned transitively (union-find) from an index built once per run over the 6,037 names that carry aliases. **§1.3 permits "a Cypher fragment or a Python post-join" and forbids per-CQ collapse logic**, so each CQ declares `collapse_on` — the column whose duplicates are unioned — and there is no `cypher_collapsed` field. A second hand-written query per question would have been exactly the per-CQ logic the task rules out; reported here as the deliberate reading of the schema.

### 1.4 Results

`assessment/results/cq_v1_2026-09-04.jsonl` (DataFile `1425ffc4`), aggregates JSON, report `docs/research/2026-09-04_cq_coverage_v1.md`, Script `run_cq` (`6355e83d`), **199 Results** named `cq_v1_*`.

| | value |
|---|---|
| `A_raw` | **0.808** (21 of 26 answerable) |
| `A_collapsed` | **0.769** (20 of 26) |
| **`flip`** | **0.269** (7 of 26): CQ-05, CQ-06, CQ-10, CQ-20, CQ-22, CQ-23, CQ-24 |
| `C` (duplicate groups unioned, whole set) | **98** |
| raw answers flagged misleading | 8 |

**Category-level flip, which is the finding underneath the number:**

| category | n | flips | flip |
|---|---:|---:|---:|
| discovery_stack | 3 | 2 | **0.667** |
| measure_lookup | 3 | 2 | **0.667** |
| frontier_candidate | 4 | 2 | **0.500** |
| instrument_coverage | 3 | 1 | 0.333 |
| claim_evidence · conflict_detection · construct_definition · provenance_traceback | 3/3/4/3 | 0 | **0.000** |

**Every flip is an enumeration question and no flip is an evidence question.** "Which standards does X consume", "which measures operationalise Y", "how many instruments are there" break on duplicates; "what does the corpus claim about X", "trace this claim to its source", "how is X defined" do not. Duplication costs the KG its ability to *count and enumerate*, not its ability to *retrieve and ground*. That is a sharper statement than the aggregate, and it is why the middle branch is the right one: probe design consumes evidence, and the enumeration questions can be fixed by a dedup pass scheduled on its own.

**`A_collapsed` is LOWER than `A_raw`, which was not anticipated.** Two CQs (CQ-13 interoperability claims, CQ-21 robots.txt) got *worse* under collapse: their questions ask for a list of items about one entity, and collapsing on that entity merges the list into a single row. That is a harness defect in my choice of `collapse_on` for those two, not a graph finding, and it is recorded rather than repaired — repairing it after seeing the answers is precisely the contamination §1.7 guards against. A v2 set should collapse list-type questions on the listed item, never on the shared subject.

**Two failures, recorded as failures.** CQ-15 (conflicting definitions) returns one pair that does **not** disagree — two fragments of the same Census household definition from the same document — so by its own pre-registered criterion it fails, and the corpus's real competing definitions of "AI readiness" (CQ-02, CQ-03) are not captured by `CONFLICTS_WITH`. CQ-14 is `partial` because all three conflict pairs are **intra-document** while the question asks where two *documents* conflict: the graph holds no cross-document conflict at all.

**Three answers worth quoting because they are negative and load-bearing.** CQ-08: nine of ten framework constructs (uncertainty, provenance, license, revision, discoverability, machine-readable, semantic consistency, authority, disclosure) are measured by **zero** Instruments in the corpus; only timeliness has 2. CQ-09: **no Instrument measures an uncertainty-related concept** — the graph independently supporting the skeleton's claim that G1 is the sharpest gap. CQ-10: the corpus describes **285** distinct instruments, not the 354 nodes labelled Instrument.

### 1.7 Judge contamination

The CQ author and the judge are the same session, and the report says so in its own header rather than a footnote. Mitigations as specified: criteria written and committed at `369d717` before any query; every `judge_reason` cites the grounding spans read; no criterion revised. Every Result derived from answerability (`cq_v1_A_raw`, `cq_v1_A_collapsed`, `cq_v1_flip`, the per-category flips) carries "Verdict by an LLM judge" in its description. Row counts, duplicate-group counts and provenance fractions are counted, not judged, and say so.

## 2. Findings registered, not fixed

**Issue `25ca65aa` — 50 Claims with no `ASSERTS` source.** All 50 carry a `doc_id`, and **40 of the 50 are fully isolated** (no edge of any kind), which the task's premise did not mention. Five named by id: `cl-adas-62`, `cl-adopt-accelerate`, `cl-adoption`, `cl-ai-infra-layer`, `cl-architecture-holds`. Whether the extraction emitted no edge or the projection dropped it is **not** determined here. The ontology has no `Issue → Claim` relationship (`annotates`/`disputes` are `Issue → Result` only, AD-028), so the sample ids are a property, as the ERRATUM precedent did.

**Issue `325a09a8` — `Concept.key` is document-scoped by design, and answering that was the point.** Format `<doc_id>::<item_id>` (`scripts/build_projection.py:335`); 8,662 Concepts carry 8,662 **distinct** keys; **zero** keys are shared across more than one `doc_id`. The design comment at `build_projection.py:328–332` states the intent and the reason: *"600 of 6,988 item ids recur across documents; keying nodes by bare item id FUSED them… Cross-document identity is dedup's job, never the loader's"* (DD-020). So the 1,122 duplicate groups are **not a loader defect** — they are the loader behaving as specified, with the dedup pass that was meant to follow never having run. That also settles why the collapse has to canonicalise display text at query time: no property in the graph is a canonical key.

## 3. Integration

| check | value |
|---|---|
| root `tests/` | **752 passed** (was 729; +23 in `tests/test_cq_collapse.py`) |
| `assessment/` | **471 passed, 1 skipped** (unchanged) |
| `seldon verify` | **All checks passed** |
| artifacts | 52 `kg_diag_*` + 199 `cq_v1_*` Results; Scripts `kg_diagnostic`, `run_cq`; DataFiles for the snapshot, the CQ set and the run; DesignNote DD-040; Issues `25ca65aa`, `325a09a8` |

The collapse tests use fixtures whose answer is obvious by inspection, and include a regression for the bug described in §4.2 below.

## 4. Premises contradicted by live state

1. **"211 Documents, 0 without extractions" is wrong: 72 have none** (§0.1). The single material error in the chat figures, and the one that changes how an unanswerable CQ should be read.
2. **`prov_source_sha256` does not exist on Document.** §1.4 defines `provenance_complete` against it; **0** Documents carry it and **211** carry `content_hash` (the property does exist on Concept, where 8,541 of 8,662 carry it). The metric uses `content_hash`; the substitution is in the harness docstring and here.
3. **My own `dup_groups_unioned` implementation did not match the pre-registered definition,** and I changed the implementation, not the definition. §1.4 says "collapse groups of size >1"; the first version counted distinct member *strings*, which reads **zero** for the commonest case in this graph — fourteen nodes named `AI readiness` are one string and fourteen rows. Corrected before judging, and the corrected figure is C = 98 against the buggy 9; `misleading_raw` moved to row-level shrink for the same reason, matching §1.4's own example. Both are pinned by tests.
4. **The CQ record schema's `cypher_collapsed` field is incompatible with §1.3's own prohibition** (§1.3 above). Resolved in favour of the post-join §1.3 explicitly permits; the field is absent and `collapse_on` replaces it.
5. **`A_collapsed` < `A_raw`.** The collapse is not free: two CQs got worse under it, because `collapse_on` was the shared subject of a list question. A harness defect, recorded and not repaired post hoc.
6. **The task's example figure "3 of 14 `AI readiness` nodes' edges" is about nodes, not strings** — noted because it is the sentence that told me my first metric implementation was wrong.
7. **`seldon artifact create Issue` requires `urgency`,** which the task's §2 did not mention; both Issues carry `importance` and `urgency`.

## 5. Out of scope, untouched

Entity resolution itself; probe design; any change to extraction; the G1 instrument. The decision this task exists to make is recorded, not acted on: **ER is scheduled, not blocking.**
