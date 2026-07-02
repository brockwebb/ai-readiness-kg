# CC Task: Manifest module (the corpus gate)

**Date:** 2026-07-02
**Project:** ai-readiness-kg
**Project root:** /Users/brock/GitHub/ai-readiness-kg
**Status:** proposed
**Immutable once written. Changes require a new task file.**

---

## Objective

Implement the manifest: the single gate through which any document becomes corpus (DD-003). A CLI-driven `add` operation that validates provenance, hashes content, dedups, emits a `manifest_add` event via the existing eventlog, and updates `corpus/manifest.json`.

## Context (read first)

- `docs/schema_v0.1.md` §2 (Document node), §7 (state machine)
- `docs/design_decisions.md` DD-002, DD-003, DD-008
- `kg/eventlog.py` — use it; do not reimplement event writing
- Reference for manifest discipline (read-only, no imports): `/Users/brock/GitHub/icsp_notebook/kg/manifest_ingest.py`

## Design

`corpus/manifest.json` is a projection rebuilt from `manifest_add` events — the event log is the source of truth. Structure: `{"schema_version": "0.1", "documents": [ ... ]}` sorted by doc_id.

Manifest entry fields (all required unless noted):
- `doc_id` — slug, lowercase, hyphenated, unique (e.g. `fcsm-25-03`)
- `title`, `authors` (list), `pub_date` (ISO or year)
- `source_type` — one of: federal / academic / industry / standard
- `primary_url` — the citable primary source. Never an internal system.
- `local_path` — path under `corpus/` to the stored copy
- `content_hash` — sha256 of the file at local_path, computed at add time
- `inclusion_rationale` — one or two sentences, free text
- `discovered_via` — optional; capture provenance (e.g. `manual`, `harvester:arxiv-rss`, `wintermute-scan`). Discovery attribution only; provenance authority stays with primary_url (DD-002).
- `status` — `active` (only value in v0)

## Steps

1. `kg/manifest.py`:
   - `add(filepath, **fields) -> str` — validates required fields, computes sha256, rejects on: duplicate doc_id, duplicate content_hash, duplicate normalized primary_url, file not under corpus/, missing fields. On pass: emits `manifest_add` event (`event_type: manifest_add`, full entry as payload) via `eventlog.append`, rebuilds manifest.json from replay. Returns doc_id.
   - `rebuild() -> dict` — replays event log, filters `manifest_add`, writes and returns manifest.json. Idempotent.
   - `verify() -> list[dict]` — re-hashes every local_path, returns mismatches/missing files. Empty list = clean.
   - CLI: `python -m kg.manifest add <file> --doc-id ... --title ... --authors ... --pub-date ... --source-type ... --url ... --rationale ... [--discovered-via ...]`, plus `rebuild` and `verify` subcommands. argparse, stdlib only.

2. `tests/test_manifest.py` — tmp-path based: successful add (event written, manifest.json updated, hash correct); each rejection path; rebuild idempotence; verify catches a tampered file.

3. Run full test suite. Green required.

4. Commit: `manifest: corpus gate with event-sourced projection (DD-003)`. Push.

## This task does NOT

- Ingest any real document or create any real manifest entry.
- Write harvester, staging-intake, extraction, or MCP code.
- Add any dependency beyond stdlib.
- Modify eventlog.py, schema.yaml, or the docs.

## Verification checklist

- [ ] manifest.json rebuilt purely from event replay (delete it, run rebuild, identical)
- [ ] All five rejection paths tested
- [ ] `verify` catches hash tamper
- [ ] pytest green, pushed
- [ ] No cross-repo imports
