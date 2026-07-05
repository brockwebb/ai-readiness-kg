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

<!-- Per-window progress sections are appended below by the runner. -->
