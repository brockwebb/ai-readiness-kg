# Phase 0 sub-RESULT — source-list intake, schema v0.3.3, construct_arm backfill

Task: `cc_tasks/2026-08-24_source_triage.md` (Seldon 7456614d) + ADDENDUM-01 + ADDENDUM-02.
Run: 2026-08-26/27 (UTC). Zero model calls.

## Input-1 drop file (ADDENDUM-02 delivery)

- Path: `docs/research/2026-08-24_sme_source_list.tsv`
- sha256: `e735faaea6ce3ce0a31e060f62c10bb78343e1f1f5b14ea84fbc7b0ce081e978`
- Size: 98,531 bytes
- Provenance (per ADDENDUM-02): `source: desktop_transcription_from_chat_2026-08-24` — a
  Desktop transcription of the 2026-08-24 chat paste, NOT the operator's original export.
  Weight for the list itself: `signal_not_verdict`, same as the row-level vetting weight.
- Parsed with a quote-aware TSV reader (`csv.reader(..., delimiter='\t')`) per the
  ADDENDUM-02 hazard note; all 73 lines (header + data) parse to exactly 8 fields.

### Discrepancies (recorded, not reconciled)

1. **Row count: 72 data rows, not the 65 ADDENDUM-02 expects** (1 inserted CES row + 64
   transcribed). The file's last row IS the expected tail row (Tiger et al. 2024, arXiv
   2409.03805), and row 1 IS the inserted CES-WP-26-25 row, so the file is a superset of
   the Desktop reading, not a truncation: 7 more rows than the Desktop count. All 72 rows
   are triaged; the count mismatch is logged here per ADDENDUM-02 ("report the actual
   count; any mismatch is a discrepancy to log, not reconcile").
2. **max.gov decks: 9, not the task's 10** — rows 7–15 (2026-C2.1 Webb, C2.2 Hoppe,
   C2.4 Belyaeva, C2.5 VanWart, 2026 FCSM AI-Ready Data WG Kopp, 2024-D1.1 Harper,
   D1.2 Christensen, D1.3 Haase, D1.4 Iwugo). Matches the ADDENDUM-01 premise-check
   expectation of 9. The operator download list reports the actual 9.
3. **Video/podcast: 2 YouTube rows (44 Presley/Data Unchained, 45 Sequeda) plus 2
   lakefs.io/ai-ready-data-summit session rows (33, 34) with no direct media URL** —
   matches ADDENDUM-01's reading ("2 YouTube, 1 vlog" in the task does not match; actual
   counts used). lakefs rows are routed per ADDENDUM-01 (fetch_failed unless a transcript
   or slides are fetchable from the summit page; result in the Phase 1/2 sub-RESULT).

## Schema v0.3.3 (append-only)

- `kg/schema.yaml` → `schema_version: "0.3.3"`; Document gains `construct_arm`
  (enum `publication_actionability` / `training_data_readiness` / `org_maturity`) and
  `grounding_surface` (enum `document` / `transcript` / `slides`, default `document`),
  both `span_entailable: false`. Changelog entries in `kg/schema.yaml` and
  `docs/schema_v0.1.md` (§2 Document row updated).
- Append-only test extended: `tests/test_schema_append_only.py` freezes both new enums
  (v0.3.3 section). `kg/manifest.py` accepts the two fields as validated optional
  keywords on `add()` (tests in `tests/test_manifest.py`); `scripts/build_projection.py`
  projects them from `manifest_add` payloads (null-safe) and whitelists `construct_arm`
  in `ANNOTATABLE_DOCUMENT_PROPERTIES`.

## construct_arm backfill (existing 134 included documents)

- Rule file: `scripts/construct_arm_backfill.yaml` (rule_version 2026-08-24.1);
  runner: `scripts/annotate_construct_arm.py`; events: `events/batch-014.jsonl`
  (`document_annotation` ×134, one per included doc, idempotent re-run contract as
  `annotate_platform_operator.py`).
- Split: kernel-v03 (63) → `publication_actionability` by epoch default, zero overrides
  after title review; v1 (71) → per-document assignment listed in the rule file:
  17 `publication_actionability`, 5 `training_data_readiness`, 49 `org_maturity`.
- Full per-doc decision table: `docs/research/2026-08-24_triage_backfill_report.md`.
- Coverage validated mechanically before any event was written: included = v1 ∪ kernel
  exactly (134 = 71 + 63, no overlap, no stragglers).
