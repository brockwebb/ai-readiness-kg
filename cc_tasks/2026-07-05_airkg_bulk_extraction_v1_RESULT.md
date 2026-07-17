# RESULT — ai-readiness-kg Bulk Extraction v1

**Task:** `cc_tasks/2026-07-05_airkg_bulk_extraction_v1.md`
**Started:** 2026-07-05
**Status:** Stages 0–4 built and armed; burn windows in progress (per-day sections
appended below by the runner); Stage 5 runs after the burn completes.

---

## Stage 0 — Manifest collision fix ✅ (preferred path: rewired)

`kg.manifest rebuild` now projects `corpus/manifest.json` FROM the Dixie evidence
decisions log (`corpus/evidence/decisions.jsonl`) — the ledger is truth, the JSON is
its projection. `add()` still validates + appends `manifest_add` admission events but
no longer auto-clobbers the projection.

**Verification (live):** ran the old command twice — v2 ledger survives (97 entries,
counts preserved: 71 included / 8 excluded / 18 pending_refetch), second rebuild
byte-identical (sha `0314057a…` both times; `generated_at` is the deterministic
last-event timestamp, not wall-clock). Missing dixie package/config → loud
ManifestError naming the ledger and this task. Tests: 73/73 green in this repo
(rebuild tests rewritten against the ledger), 23/23 in dixie.
Commits: ai-readiness `68ecd2c`, dixie `deterministic projections`.

## Stage 1 — Cisco recombination + v1 freeze ✅ (with a finding)

**Finding:** the manifested `cisco-ai-readiness-assessment-instrument.pdf` (25 pages)
IS already the recombined compound — verified **page-identical, 25/25**, against the 6
components in Cisco pillar order (strategy → infrastructure → data → governance →
talent → culture; order confirmed from page content, not guessed). A prior session
merged them and left the fragments behind. Creating a second merged PDF would have
minted a content duplicate — instead the compound's provenance was COMPLETED in the
ledger: `provenance_completion` note event carrying all 6 component sha256s +
pillar mapping + `acquisition_channel: manual_page_capture`; components archived
(moved, never deleted) to `corpus/components/cisco-assessment/`; the 6 fragment
entries decided `excluded` with superseded-by rationale.

**Freeze:** `corpus_epoch_declared` epoch=v1 event `0ba4e3f764e64cb8ba1a7155fd6eee3f`
with 71 member_doc_ids — emitted BEFORE any extraction. `min_verified_included: 71`
set in `dixie_evidence.yaml`. All 71 included docs stamped `added_in: v1` in the
manifest projection. The 18 refetch items remain manifested as `pending_refetch` with
worklist metadata. Baseline = **71** (cisco compound already inside).

## Stage 2 — Pre-registered thresholds (fss realized values) ✅

Ported into `dixie_evidence.yaml` `baseline_gate.post_extraction_checks`, sources
cited per check, **flagged for operator review**:

| check | v1 threshold | fss realized value + source artifact |
|---|---|---|
| grounding_zero_ungrounded | **eq 0 (absolute — doctrine override)** | 0 ungrounded admitted / 6,237 extraction events (`kg/e3_full_drain_report.md` §1); 6,481/6,481 grounded in live graph (`kg_intrinsic_quality_report.md` §4) |
| quarantine_rate (run) | lte 0.0152 | 123 failed / 8,078 eligible segments (`e3_full_drain_report.md` §2–3) |
| edge_endpoint_validation | eq 0 | 0 out-of-vocab forces, 0 missing source provenance (`kg_intrinsic_quality_report.md` §2, §4) |
| orphan_rate | lte 0.0034 | 22/6,481 segmentless obligations (`kg_intrinsic_quality_report.md` §2) |
| projection_drift | eq 0 (definitional) | `drift_check.py` clean |
| empty_extraction_rate | lte 0.1196 | 11/92 zero-obligation docs (`kg_intrinsic_quality_report.md` §1) |

Config comments state the expectation: the heterogeneous corpus may fail the
edge/orphan/empty gates — a failed gate triggers investigation, never retuning.
fss-policy-kg was read-only throughout.

## Stage 3 — Budget diversion ✅ (switch/epoch record)

**Declared (federation.yaml epoch 4, sha `e5951e82…`, event appended):** job
`airkg-extraction-burn` → extraction circuit; priority class `deadline`; diversion
rationale in the config comment. Extraction band read live: **400,000 daily /
2,000,000 weekly** — diverted intact, not re-typed.

**Switches flipped OFF (exact list):**
- Panel: `wm-power off extraction` → circuit OFF; bootouts its 4 declared jobs
  (knowledge-graph-extract, process-books, book-extraction-burn, book-recovery-burn).
- launchd-disabled individually (18): load-extracted, revert-extract-backend,
  drain-inbox, ingest-anthropic, ingest-cli-sessions, ingest-mech-interp,
  ingest-tda-tooling, watch-claude-inbox, stage-harvest-corpus, harvest-arxiv,
  harvest-chain-references, harvest-citation-expand, harvest-count-validation,
  harvest-federal-register, harvest-manifest-integrity, harvest-pubmed,
  harvest-saturation-check, search-papers.
- **NOT touched:** federation-reconcile, Arnold (com.arnold.*), watchdog/OODA/
  self-healer/mcp-server/backups, enrichment + digest cycles, dedup guard state.

**Admission-policy note (recorded reasoning):** ai-readiness-kg stays OBSERVE — an
`enforce` policy would be blocked by the very circuit switch that silences Wintermute
(one shared circuit). The runner therefore BINDS the declared caps itself via
`declared_caps()` + panel usage before every document, and meters every call through
`gate()` + `record_usage()` project-tagged. Same primitives, no new plane machinery.

**Pause verified:** manual fire of `knowledge_graph_extract.sh` →
`SKIPPED: circuit-off`, rc=0 — the switch-off reason, not an error.
**Dry admission check:** `gate('extraction', project='ai-readiness-kg',
class='deadline')` → `(True, observe:ai-readiness-kg)`; lease free.

**Window note:** Wintermute's extract cron burned 412,676 tokens of the 2026-07-05
daily window this morning before the switch-off — today's diverted band is already
exhausted (day_left=0, week_left=758,883). First burn window: next day-roll
(2026-07-06, which is also the ISO-week roll → full band). Cap-tripping is normal
operation.

## Stage 4 — Extraction burn (armed; progress appended below)

Runner: `scripts/run_bulk_extraction.py` + wrapper `scripts/jobs/airkg_extraction_burn.sh`
+ `com.wintermute.airkg-extraction-burn.plist` (hourly). Per document: declared-cap
check → project-tagged gate → `claude -p` (model pinned `claude-opus-4-8`, Max OAuth
only, substitution gate STOPs the run) → **raw response persisted to
`events/raw/bulk_v1/<doc_id>.<sha12>.<prompt_epoch>.<model_id>.json` before parsing**
→ parse with grounding (ungrounded items quarantined, never admitted) → assertion
events to `events/batch-004.jsonl` with provenance stamps {model_id, prompt_version,
schema_version 0.2, **corpus_epoch v1, source_sha256**} → `record_usage` with actual
envelope tokens. Resume = batch-004 build_metrics replay. Oversize docs
(>250k chars) are DEFERRED with an event, never truncated (grounding integrity).
STOP discipline: per-doc quarantine >10% or model substitution → STOP file
(`events/bulk_v1_STOP.json`); runner refuses to fire until the operator removes it.

## Stage 5 — Machinery built + shakedown (final gate report runs post-burn)

**What was built (the S1 finding made good):** this repo had ZERO projection code —
the KG existed only as events. Now:
- `scripts/build_projection.py` — minimal reset-and-replay events→Neo4j projection
  into **`seldon-ai-readiness-kg`** (the hive's declared KG database per
  seldon.yaml/federation registry; Seldon's :Artifact graph coexists untouched under
  disjoint labels — deletes are scoped to the 9 schema labels only). Rel types come
  exclusively from the schema.yaml edge whitelist (no payload text ever reaches
  Cypher composition).
- `scripts/run_baseline_gates.py` — computes the six pre-registered checks from
  events + the projection; writes `docs/research/bulk_v1_gate_report.md`. No
  retuning path exists.

**First projection build (2026-07-05):** 357 nodes + 588 edges (519 pilot assertions
+ 69 curated promotions — exactly the declared baseline numbers) + 71 Documents.

**Shakedown gate run against PILOT-era data** (machinery verification — the v1 gate
report regenerates after the burn):

| check | value | threshold | verdict |
|---|---|---|---|
| min_verified_included | 71 | 71 | PASS |
| grounding_zero_ungrounded | 0 (0 v1 items yet) | 0 | PASS |
| quarantine_rate | 0.0 | 0.0152 | PASS |
| edge_endpoint_validation | **67** | 0 | **FAIL — finding** |
| orphan_rate | **0.0483** | 0.0034 | **FAIL — finding** |
| projection_drift | 0 | 0 | PASS |
| empty_extraction_rate | 0.0 | 0.1196 | PASS |

**The two failures are pilot-data findings, recorded not retuned:** the 67 edge
violations are dominated by pilot `cites` edges whose targets are UNMANIFESTED cited
works (external references — i.e. refetch-candidate surface, plus at least one
id-mismatch: `doc-fcsm-framework-for-data-quality` vs the held `fcsm-20-04`). The
orphan rate is pilot nodes with no surviving edges. Both match the pre-registration
comment's prediction that a heterogeneous corpus fails edge/orphan gates — they
trigger investigation post-burn.

**To produce the final Stage-5 report after the burn completes:**
`python3 scripts/build_projection.py && python3 scripts/run_baseline_gates.py`

---

<!-- Per-window progress sections are appended below by the runner. -->

### Burn progress — 2026-07-06 01:57 EDT

- advancing-american-ai-act-ndaa-fy2023-div-g: deferred oversize (5,560,088 chars)
- ai-data-readiness-checklist-digital-government-hub: 48 nodes, 64 edges, quarantined 0 (rate 0.000), 55,727 tokens
- ai-governance-ethics-and-leadership-substack-harvey-lab-lega: 48 nodes, 72 edges, quarantined 0 (rate 0.000), 69,025 tokens
- ai-in-government-act-of-2020: deferred oversize (6,687,124 chars)
- ai-readiness-building-the-bridge-from-higher-education-to-wo: 86 nodes, 138 edges, quarantined 2 (rate 0.009), 172,551 tokens
- ai-readiness-for-official-data-and-statistics-un-statistical: 44 nodes, 65 edges, quarantined 10 (rate 0.084), 64,124 tokens
- ai-readiness-in-healthcare-through-storytelling-xai: 58 nodes, 40 edges, quarantined 0 (rate 0.000), 95,054 tokens
- cap exhausted after 5 docs this window
- window total: 5 docs extracted; 5/71 complete; tokens left in band: 0

### Burn progress — 2026-07-07 02:35 EDT

- advancing-american-ai-act-ndaa-fy2023-div-g: deferred oversize (5,560,088 chars)
- ai-in-government-act-of-2020: deferred oversize (6,687,124 chars)
- ai-real-toolkit-ai-readiness-assessment-guide: 129 nodes, 185 edges, quarantined 0 (rate 0.000), 248,246 tokens
- ai-watch-revisiting-technology-readiness-levels-for-relevant: deferred oversize (329,578 chars)
- aidrin-2-0-a-framework-to-assess-data-readiness-for-ai: 66 nodes, 70 edges, quarantined 0 (rate 0.000), 76,825 tokens
- aidrin-hiniduma-2024: 93 nodes, 147 edges, quarantined 20 (rate 0.077), 127,268 tokens
- cap exhausted after 3 docs this window
- window total: 3 docs extracted; 8/71 complete; tokens left in band: 0

### Burn progress — 2026-07-08 00:26 EDT

- advancing-american-ai-act-ndaa-fy2023-div-g: deferred oversize (5,560,088 chars)
- ai-in-government-act-of-2020: deferred oversize (6,687,124 chars)
- ai-watch-revisiting-technology-readiness-levels-for-relevant: 87 nodes, 80 edges, quarantined 2 (rate 0.012), 312,762 tokens
- arm-ai-readiness-index: deferred oversize (250,746 chars)
- artificial-intelligence-domain-ai-readiness-and-firm-product: 62 nodes, 91 edges, quarantined 14 (rate 0.084), 150,738 tokens
- cap exhausted after 2 docs this window
- window total: 2 docs extracted; 10/71 complete; tokens left in band: 0

### Burn progress — 2026-07-08 17:53 EDT

- cisco-ai-readiness-index-2025: 123 nodes, 157 edges, quarantined 11 (rate 0.038), 127,168 tokens
- arm-ai-readiness-index: deferred oversize (250,746 chars)
- m-19-23-phase-1-implementation-of-the-evidence-act: 66 nodes, 106 edges, quarantined 0 (rate 0.000), 162,786 tokens
- nist-ai-rmf-playbook: deferred oversize (339,509 chars)
- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- window total: 2 docs extracted; 12/71 complete; tokens left in band: 1,246,546

### Burn progress — 2026-07-08 21:06 EDT

- arm-ai-readiness-index: deferred oversize (250,746 chars)
- nist-ai-rmf-playbook: deferred oversize (339,509 chars)
- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- nist-ai-risk-management-framework-ai-rmf: 102 nodes, 133 edges, quarantined 12 (rate 0.049), 159,538 tokens
- gao-ai-accountability-framework-ariga-testimony: 57 nodes, 67 edges, quarantined 18 (rate 0.127), 83,727 tokens
- STOP: gao-ai-accountability-framework-ariga-testimony quarantine rate 0.127 > 0.1
- window total: 2 docs extracted; 14/71 complete; tokens left in band: 1,003,281

### Burn progress — 2026-07-08 21:56 EDT

- arm-ai-readiness-index: deferred oversize (250,746 chars)
- nist-ai-rmf-playbook: deferred oversize (339,509 chars)
- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- fcsm-19-01-transparent-reporting-for-integrated-data-quality: text extraction failed (Unable to find 'endstream' marker for obj starting at 811018.)
- from-school-ai-readiness-to-student-ai-literacy: 70 nodes, 110 edges, quarantined 1 (rate 0.005), 190,707 tokens
- mitre-ai-maturity-model: 93 nodes, 145 edges, quarantined 29 (rate 0.109), 166,220 tokens
- STOP: mitre-ai-maturity-model quarantine rate 0.109 > 0.1
- window total: 2 docs extracted; 16/71 complete; tokens left in band: 646,354

### Burn progress — 2026-07-09 04:06 EDT

- arm-ai-readiness-index: 159 nodes, 90 edges, quarantined 4 (rate 0.016), 254,184 tokens
- window total: 1 docs extracted; 17/71 complete; tokens left in band: 1,745,816

### Burn progress — 2026-07-09 05:12 EDT

- nist-ai-rmf-playbook: 134 nodes, 64 edges, quarantined 2 (rate 0.010), 313,126 tokens
- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- fcsm-19-01-transparent-reporting-for-integrated-data-quality: text extraction failed (Unable to find 'endstream' marker for obj starting at 811018.)
- window total: 1 docs extracted; 18/71 complete; tokens left in band: 1,432,690

### Burn progress — 2026-07-09 07:59 EDT

- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- nist-generative-ai-profile-ai-600-1: 88 nodes, 130 edges, quarantined 3 (rate 0.014), 211,571 tokens
- technology-readiness-levels-for-machine-learning-systems-mlt: 79 nodes, 100 edges, quarantined 1 (rate 0.006), 172,440 tokens
- fcsm-20-04-a-framework-for-data-quality: deferred oversize (269,719 chars)
- why-ai-readiness-is-an-organizational-learning-problem-not-a: 68 nodes, 114 edges, quarantined 0 (rate 0.000), 95,235 tokens
- from-accuracy-to-readiness-metrics-and-benchmarks-for-human: 86 nodes, 115 edges, quarantined 3 (rate 0.015), 118,221 tokens
- data-readiness-for-ai-a-360-degree-survey: 102 nodes, 63 edges, quarantined 3 (rate 0.018), 182,991 tokens
- bangladesh-s-ai-readiness-perspectives: 79 nodes, 119 edges, quarantined 7 (rate 0.034), 445,945 tokens
- window total: 6 docs extracted; 24/71 complete; tokens left in band: 206,287

### Burn progress — 2026-07-09 12:52 EDT

- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- fcsm-20-04-a-framework-for-data-quality: deferred oversize (269,719 chars)
- fcsm-23-02-a-framework-for-data-quality-case-studies: invocation failed (attempt 1/2): model response contains no JSON object
- cisco-ai-readiness-assessment-instrument: invocation failed (attempt 1/2): model response contains no JSON object
- technology-readiness-levels-for-ai-ml-trl4ml: 61 nodes, 87 edges, quarantined 12 (rate 0.075), 91,131 tokens
- m-24-10-advancing-governance-innovation-and-risk-management: 67 nodes, 98 edges, quarantined 2 (rate 0.012), 144,392 tokens
- data-readiness-for-scientific-ai-at-scale: 86 nodes, 102 edges, quarantined 0 (rate 0.000), 103,241 tokens
- winning-the-race-america-s-ai-action-plan: invocation failed (attempt 1/2): model response contains no JSON object
- m-24-18-advancing-the-responsible-acquisition-of-ai-in-gover: 83 nodes, 110 edges, quarantined 1 (rate 0.005), 162,651 tokens
- m-25-05-phase-2-implementation-of-the-evidence-act-open-gove: 67 nodes, 88 edges, quarantined 0 (rate 0.000), 137,451 tokens
- executive-order-14110-safe-secure-and-trustworthy-developmen: 81 nodes, 93 edges, quarantined 8 (rate 0.044), 182,450 tokens
- statistical-policy-working-paper-46-data-quality-assessment: 75 nodes, 100 edges, quarantined 0 (rate 0.000), 118,352 tokens
- unesco-ai-readiness-assessment-methodology-ram: 32 nodes, 49 edges, quarantined 0 (rate 0.000), 58,568 tokens
- advancing-american-ai-act-ndaa-fy2023-div-g: 54 nodes, 84 edges, quarantined 6 (rate 0.042), 111,748 tokens
- introducing-the-oecd-ai-capability-indicators: deferred oversize (287,110 chars)
- nist-ai-100-3-the-language-of-trustworthy-ai-an-in-depth-glo: invocation failed (attempt 1/2): model response contains no JSON object
- foundations-for-evidence-based-policymaking-act-of-2018-evid: 72 nodes, 74 edges, quarantined 21 (rate 0.126), 156,696 tokens
- building-an-ai-ready-public-workforce: deferred oversize (266,932 chars)
- m-26-04-increasing-public-trust-in-ai-through-unbiased-ai-pr: 44 nodes, 76 edges, quarantined 8 (rate 0.062), 79,496 tokens
- beyond-model-readiness-institutional-readiness-for-ai-deploy: 44 nodes, 67 edges, quarantined 21 (rate 0.159), 95,443 tokens
- fcsm-25-03: 59 nodes, 90 edges, quarantined 11 (rate 0.069), 77,577 tokens
- cisco-ai-readiness-index-methodology: 35 nodes, 54 edges, quarantined 0 (rate 0.000), 57,055 tokens
- ai-in-government-act-of-2020: 36 nodes, 51 edges, quarantined 1 (rate 0.011), 60,952 tokens
- datahub-mlmu-25: invocation failed (attempt 1/2): model response contains no JSON object
- executive-order-14319-preventing-woke-ai-in-the-federal-gove: 29 nodes, 42 edges, quarantined 7 (rate 0.090), 60,627 tokens
- executive-order-13859-maintaining-american-leadership-in-ai: invocation failed (attempt 1/2): model response contains no JSON object
- executive-order-13960-promoting-the-use-of-trustworthy-ai-in: 43 nodes, 50 edges, quarantined 8 (rate 0.079), 83,146 tokens
- executive-order-14179-removing-barriers-to-american-leadersh: invocation failed (attempt 1/2): model response JSON unparseable: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
- webb-fcsm-nist-crosswalk: 92 nodes, 99 edges, quarantined 9 (rate 0.045), 159,982 tokens
- rethinking-technological-readiness-in-the-era-of-ai-uncertai: 65 nodes, 71 edges, quarantined 42 (rate 0.236), 124,782 tokens
- gsa-ai-guide-for-government-ai-capability-maturity-model-ai: 107 nodes, 156 edges, quarantined 0 (rate 0.000), 174,375 tokens
- lawrence-data-readiness-levels-2017: 37 nodes, 56 edges, quarantined 0 (rate 0.000), 83,926 tokens
- making-agentic-ai-work-for-government-a-readiness-framework: invocation failed (attempt 1/2): model response contains no JSON object
- why-ai-projects-fail-the-63-human-factor-problem: 86 nodes, 120 edges, quarantined 2 (rate 0.010), 150,754 tokens
- organizational-ai-readiness-prosci-adkar: 47 nodes, 48 edges, quarantined 0 (rate 0.000), 103,650 tokens
- six-areas-for-assessing-ai-readiness-in-government: invocation failed (attempt 1/2): model response contains no JSON object
- government-ai-readiness-index-2025: 58 nodes, 81 edges, quarantined 0 (rate 0.000), 96,781 tokens
- census-bureau-statistical-quality-standards-standard-f1-rele: 51 nodes, 76 edges, quarantined 8 (rate 0.059), 96,546 tokens
- census-bureau-statistical-quality-standards-standard-d3-prod: 54 nodes, 79 edges, quarantined 6 (rate 0.043), 96,977 tokens
- census-bureau-statistical-quality-standards-standard-f2-prov: 51 nodes, 64 edges, quarantined 0 (rate 0.000), 82,196 tokens
- government-ai-landscape-assessment-code-for-america: 74 nodes, 93 edges, quarantined 0 (rate 0.000), 86,086 tokens
- health-ai-readiness-assessment-dime: 76 nodes, 90 edges, quarantined 0 (rate 0.000), 81,784 tokens
- undp-artificial-intelligence-readiness-assessment-aira: 18 nodes, 32 edges, quarantined 0 (rate 0.000), 62,623 tokens
- the-nation-s-data-at-risk-first-annual-report-on-the-federal: 13 nodes, 17 edges, quarantined 0 (rate 0.000), 61,417 tokens
- the-oecd-ai-index: 21 nodes, 31 edges, quarantined 0 (rate 0.000), 53,025 tokens
- itu-ai-ready-analysis-towards-a-standardized-readiness-frame: 0 nodes, 0 edges, quarantined 0 (rate 0.000), 42,665 tokens
- window total: 33 docs extracted; 57/71 complete; tokens left in band: 4,867,742

### Burn progress — 2026-07-09 13:16 EDT

- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- fcsm-20-04-a-framework-for-data-quality: deferred oversize (269,719 chars)
- fcsm-23-02-a-framework-for-data-quality-case-studies: invocation failed (attempt 2/2): model response contains no JSON object
- cisco-ai-readiness-assessment-instrument: 90 nodes, 136 edges, quarantined 36 (rate 0.137), 98,006 tokens
- winning-the-race-america-s-ai-action-plan: invocation failed (attempt 2/2): model response contains no JSON object
- introducing-the-oecd-ai-capability-indicators: deferred oversize (287,110 chars)
- nist-ai-100-3-the-language-of-trustworthy-ai-an-in-depth-glo: invocation failed (attempt 2/2): model response contains no JSON object
- building-an-ai-ready-public-workforce: deferred oversize (266,932 chars)
- datahub-mlmu-25: 43 nodes, 58 edges, quarantined 0 (rate 0.000), 70,361 tokens
- executive-order-13859-maintaining-american-leadership-in-ai: 33 nodes, 44 edges, quarantined 6 (rate 0.072), 69,933 tokens
- executive-order-14179-removing-barriers-to-american-leadersh: invocation failed (attempt 2/2): model response contains no JSON object
- making-agentic-ai-work-for-government-a-readiness-framework: invocation failed (attempt 2/2): model response contains no JSON object
- six-areas-for-assessing-ai-readiness-in-government: invocation failed (attempt 2/2): model response contains no JSON object
- window total: 3 docs extracted; 60/71 complete; tokens left in band: 4,629,442

### Burn progress — 2026-07-09 15:13 EDT

- fcsm-19-01-transparent-reporting-for-integrated-data-quality: text extraction failed (Unable to find 'endstream' marker for obj starting at 811018.)
- fcsm-23-02-a-framework-for-data-quality-case-studies: invocation failed (attempt 3/2): model response contains no JSON object
- introducing-the-oecd-ai-capability-indicators: invocation failed (attempt 1/2): model response contains no JSON object
- nist-ai-100-3-the-language-of-trustworthy-ai-an-in-depth-glo: 30 nodes, 33 edges, quarantined 0 (rate 0.000), 65,153 tokens
- window total: 1 docs extracted; 61/71 complete; tokens left in band: 34,564,289

### Burn progress — 2026-07-09 15:13 EDT

- building-an-ai-ready-public-workforce: invocation failed (attempt 1/2): model response contains no JSON object
- making-agentic-ai-work-for-government-a-readiness-framework: invocation failed (attempt 3/2): model response contains no JSON object
- six-areas-for-assessing-ai-readiness-in-government: 37 nodes, 54 edges, quarantined 0 (rate 0.000), 100,115 tokens
- window total: 1 docs extracted; 62/71 complete; tokens left in band: 34,464,174

### Burn progress — 2026-07-09 15:21 EDT

- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- fcsm-20-04-a-framework-for-data-quality: invocation failed (attempt 2/2): model response contains no JSON object
- introducing-the-oecd-ai-capability-indicators: invocation failed (attempt 2/2): model response contains no JSON object
- building-an-ai-ready-public-workforce: 48 nodes, 49 edges, quarantined 0 (rate 0.000), 311,271 tokens
- window total: 1 docs extracted; 63/71 complete; tokens left in band: 34,152,903

### Burn progress — 2026-07-16 21:41 EDT

- information-quality-act-data-quality-act-sec-515-of-p-l-106: deferred oversize (2,117,624 chars)
- fcsm-19-01-transparent-reporting-for-integrated-data-quality: text extraction failed (Unable to find 'endstream' marker for obj starting at 811018.)
- fcsm-20-04-a-framework-for-data-quality: 140 nodes, 150 edges, quarantined 16 (rate 0.052), 265,652 tokens
- fcsm-23-02-a-framework-for-data-quality-case-studies: 176 nodes, 278 edges, quarantined 2 (rate 0.004), 183,019 tokens
- winning-the-race-america-s-ai-action-plan: 113 nodes, 181 edges, quarantined 1 (rate 0.003), 127,010 tokens
- introducing-the-oecd-ai-capability-indicators: 99 nodes, 137 edges, quarantined 7 (rate 0.029), 338,165 tokens
- executive-order-14179-removing-barriers-to-american-leadersh: 35 nodes, 64 edges, quarantined 1 (rate 0.010), 50,818 tokens
- making-agentic-ai-work-for-government-a-readiness-framework: 26 nodes, 48 edges, quarantined 0 (rate 0.000), 116,200 tokens
- window total: 6 docs extracted; 69/71 complete; tokens left in band: 29,542,428
