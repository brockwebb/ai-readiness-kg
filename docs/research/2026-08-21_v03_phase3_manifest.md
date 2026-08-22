# Phase 3 — Manifest adds (task 2026-08-21_v03_visibility_kernel)

Run: 2026-08-21. `scripts/manifest_kernel.py` (new). Zero model calls. Authorization: AUTH-2 (rule-based adds; rule in `docs/research/2026-08-21_kernel_inclusion_rule.md`).

## Counts
| outcome | n |
|---|---|
| manifest-added | **63** |
| skipped — already manifested (doc_id / sha256 / primary_url) | 0 at the gate (the 3 Census standards were screened out upstream in Phase 2 as `excluded_by_rule: already_manifested`, never reached the gate) |
| deferred | 5 — `akamai-bot-manager-bot-reports` (fetch_failed: SAML login), `census-quality-standard-{d3,f1,f2}` (already held since bulk v1), `sme-visibility-diagnostic-framework` (not in inbox) |

By clause: a=21, b=25, c=8, d=9, e=0. `extent_note` recorded on 5 (AUTH-4 / DD-011): `w3c-dcat-3` (§1–18 + A/B), `openapi-specification-core` (§1–6), `w3c-json-ld-1-1-core` (§1,2,3,8 — no steward primer exists), `w3c-dwbp-2017` and `w3c-rdf-data-cube` (whole Rec; note records only a ToC nav strip removed). `as_of` present on 39/63; 24 carry `as_of: null` with `as_of_source` stating why (no page date, no Last-Modified) — never fabricated.

## Path taken (designed path, no side door)
1. File moved `corpus/staging/inbox/kernel/` → `corpus/kernel/<doc_id>.{md,pdf}` (new document dir; added to `dixie_evidence.yaml: document_dirs` and `.gitignore` with the same rationale as `corpus/bulk/`).
2. Dixie ledger: `screening_imported` (source `kernel_list_2026-08-21`, decision `included`, rationale = clause matched + task item) → sweep: `file_observed` ×63, `integrity_checked` ×65, quarantined 0.
3. `kg.manifest.add` → `manifest_add` events in **`events/batch-006.jsonl`** (the kernel shard; `_MANIFEST_BATCH` overridden at call time, documented in the script) carrying `acquisition.{clause, as_of, as_of_source, test.urls_tried, verification.sha256, validation.chars, extent_note, excluded_sections}`.
4. `corpus_epoch_declared epoch=kernel-v03` with 63 members → runner profile `kernel_v03` sees `63 docs | todo 63` on dry-run.
5. `python -m kg.manifest rebuild` → `corpus/manifest.json` 162 entries (97 → 162; no pre-existing entry's decision/stage/integrity changed — verified by diff against HEAD).

## Defects found and fixed on the way (all recorded, none silent)
- **Latent dixie crash (pre-existing ledger data):** two `integrity_checked` events written by the 2026-08-14 Acts acceptance (`scripts/accept_two_acts.py`, ledger lines 438/440) carry no `sha256`; `Sweep._known` indexed on `p["sha256"]` and crashed — the sweep had not run since. Fixed in dixie (`sweep.py`: `p.get("sha256")`, comment cites this). Ledger untouched (append-only). The first `manifest_kernel.py` run therefore stopped after writing the 63 `manifest_add` + 63 `screening_imported` events; a `--finalize` mode was added to resume from the shard without re-adding.
- **Semantic collision in the candidate register:** Phase 2 wrote the three already-held Census standards with `status: excluded` (= excluded from the *harvest*), but dixie re-imports the register as corpus screening decisions and would have flipped the live v1 entries to `excluded`. Per the repo's own convention (bulk_acquisition_v2: every outcome updates the register line's status), the 68 session-written lines were updated before the sweep: 63 `staged → manifested` (decision_reason = manifest-added by rule, clause), 3 `excluded → manifested` (already_manifested), Akamai `needs_source` and SME `excluded` unchanged. Lines 1–91 byte-identical to HEAD.
- **dixie stage regression:** the register re-import re-stamped the 3 Census entries `verified → acquired` (`_on_screening_imported` set stage unconditionally). Fixed in dixie (`manifest.py`: only advance from `None/cataloged`). dixie tests 58/58. Rebuilt: zero pre-existing entries changed.

## Discrepancies vs task
- Task expected ≈45–55 candidates; 68 registered / 63 added (schema.org type pages count individually, per the task's own instruction).
- `kg.manifest verify` reports 4 pre-existing `hash_mismatch` entries (`fcsm-19-01`, the two Acts, §515): their batch-001 `manifest_add` hashes predate the v1 re-acquisitions, which were ledgered in dixie but not re-manifested in `kg.manifest`. Pre-existing (HEAD), not touched here; noted for the operator.
