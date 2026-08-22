# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`~/GitHub/CLAUDE.md` (engineering standards) and `~/.claude/CLAUDE.md` (operating doctrine) govern this repo; this file adds project context only.

## What this is

A knowledge graph that is the **validity layer** under the FSS AI-readiness survey: which definitions of *AI readiness* / *AI-ready data* exist, which constructs the literature proposes, which instruments operationalize them, and the crosswalk survey item → construct → definition → primary source. Every assertion must be citable by a stranger.

Status (2026-08): corpus epoch **v1 frozen at 71 docs, 71/71 extracted**, bulk-v1 closed out. Gate results in `docs/research/2026-08-14_bulk_v1_closeout_gate_report.md`; three gates (`quarantine_rate`, `edge_endpoint_validation`, `orphan_rate`) FAIL as *recorded findings* — a failed pre-registered gate triggers investigation, never retuning.

## Commands

```bash
python -m pytest tests/ -v                       # full suite (stdlib + pyyaml; anthropic NOT required)
python -m pytest tests/test_extraction_parser.py -v
python -m pytest tests/test_manifest.py -k duplicate -v

python -m kg.manifest add <file> --doc-id ... --title ... --authors ... \
    --pub-date ... --source-type ... --url ... --rationale ... [--discovered-via ...]
python -m kg.manifest rebuild                    # regenerate corpus/manifest.json (projects from dixie ledger)
python -m kg.manifest verify

python scripts/run_bulk_extraction.py --dry-run  # runner; --profile v1|kernel_v03 (scripts/run_profiles.yaml), --only DOC_ID, --max-docs, --retry-failed, --fleet, --shard
python scripts/build_projection.py               # reset-and-replay events → Neo4j (db: seldon-ai-readiness-kg)
python scripts/run_baseline_gates.py [--profiles v1,kernel_v03 --report PATH]  # pre-registered checks
```

Extraction and projection need the anaconda python (`/opt/anaconda3/bin/python3`) for `dixie`, `pypdf`, `neo4j`, and the `claude` CLI on PATH; the launchd wrapper `scripts/jobs/airkg_extraction_burn.sh` shows the exact environment. Neo4j creds come from `NEO4J_USER`/`NEO4J_PASS` (fallback: `~/.wintermute/.env`). **Never set `ANTHROPIC_API_KEY`** — the model gate refuses it (DD-007); all model calls go through `claude -p` under Max OAuth.


## Architecture — the invariants you must not break

**1. Event log is the source of truth; everything else is a disposable projection.**
`events/batch-NNN.jsonl` (sharded by ingest batch, DD-008) is append-only. `kg/eventlog.py` stamps every event with `event_id`, UTC `timestamp`, `schema_version`. Never edit or delete an event line; correct via a new event (e.g. `extraction_superseded`, `edge_endpoint_alias` in batch-005). `corpus/manifest.json` and the Neo4j graph are rebuilt by replay. Shard usage so far: 001 = manifest_add ×71, 002 = pilot extraction, 003 = curated_promotion, 004 = bulk-v1 extraction (assertions + `model_call`/`build_metrics`/STOP/skip events), 005 = closeout overlays. Raw model responses are persisted beside events at `events/raw/bulk_v1/<doc_id>.<sha12>.<prompt_epoch>.<model_id>.json` — non-negotiable provenance.

**2. Manifest is the only gate into the corpus (DD-003).**
A document is corpus only after a `manifest_add` event (`kg/manifest.py`: validates provenance, sha256-hashes, rejects duplicates *before* writing). Harvester finds in `corpus/staging/` are inert. Since the Stage-0 rewire, `manifest.json` is projected from the **dixie evidence ledger** (`dixie_evidence.yaml`, `corpus/evidence/`), not from `manifest_add` events — the event stream remains the extraction-admission gate, the ledger is the corpus ledger. Corpus binaries (`corpus/bulk/`, `bulk_md/`, `pilot/`, `cisco/`) are gitignored; provenance survives via `primary_url + content_hash`. Bad acquisitions are moved to `corpus/quarantine/` with a `.reason.txt` — never deleted.

**3. No grounding span, no write.**
Every node and edge carries a verbatim `grounding_span` validated by `kg/extraction/grounding.py` (NFKC + de-hyphenation + whitespace collapse; case-sensitive; not fuzzy). Misses are quarantined at parse in `parser.py`, never admitted. The `grounding_zero_ungrounded` gate is absolute zero, not a rate.

**4. `kg/schema.yaml` is the single type catalogue.**
Transcribed from `docs/schema_v0.1.md` (the doc is authoritative; currently v0.2). Parser edge whitelist = `edge_types` keys; unknown edge types are auto-routed to `proposed_relationships` (staged to `corpus/staging/proposed_relationships/<doc>.jsonl` for operator batch review — §6 of the schema doc). Schema changes go through that review, never silent edits. `build_projection.py` only emits rel types from this whitelist (never interpolates payload text into Cypher).

**5. Harness owns provenance.** `pipeline.py` strips any `document_id`/`model_id`/`schema_version`/`timestamp`/`extraction_event_id` the model emits and re-stamps them. Model identity is pinned in `kg/extraction/model_config.yaml` (currently `claude-opus-4-8`, `effort: high`); a response reporting a different model is discarded and the run STOPs.

**Document state machine** (`kg/extraction/state.py`): `discovered → manifest_added → extracted → validated → ingested`; extraction on a doc without `manifest_add` is a hard error.

**Extraction runtime quirk:** `model_stub.py` runs `claude -p` from a hermetic empty temp cwd so the model loads no project CLAUDE.md — with repo cwd it narrates around the JSON and breaks parsing (root-caused 2026-07-09). Keep it that way.

## Operational controls

- `controls.yaml` — `forage`/`extract` on-off and daily budgets; the *entire* interface for Wintermute's circuit-breaker panel (DD-004). Budget caps are bound in the runner, not negotiated.
- `dixie_evidence.yaml` — corpus integrity floors, identity-admission gate, and the **pre-registered** `baseline_gate` thresholds (ported from fss-policy-kg realized values, with sources cited per check). Thresholds are operator decisions; code reads them, never adjusts them.
- Runner env knobs: `BURN_ORDER=size_desc`, `BURN_QUARANTINE_STOP_MODE=per_doc|systemic`, `BURN_MAX_FLEET_WORKERS`. A STOP file halts the run until the operator removes it; cap exhaustion is a clean exit 0.

## Where to read first

- `docs/design_decisions.md` — DD-001..DD-008 (append-only, dated).
- `docs/schema_v0.1.md` — node/edge types, provenance (§4), extraction protocol (§5), state machine (§7).
- `cc_tasks/*_RESULT.md` — execution records; the newest (`2026-08-14_bulk_v1_closeout_RESULT.md`) is the current state of play. `cc_tasks/` is intentionally tracked; `handoffs/` is not.
- Seldon is active (`seldon.yaml`, `seldon_events.jsonl`); Neo4j database `seldon-ai-readiness-kg` holds both the KG labels and Seldon's artifact graph under disjoint labels — `build_projection.py` deletes only KG-schema labels.

## Conventions specific to this repo

- Module path globals (`_EVENTS_DIR`, `_METRICS_DIR`, `_REVIEW_DIR`, `_SCHEMA_PATH`) are read at call time so `tests/conftest.py` can monkeypatch them onto `tmp_path`; don't inline them into function bodies.
- Tests use the *real* `kg/schema.yaml` for type validity but a tmp schema for the eventlog version stamp (`ext_iso` fixture).
- Discrepancies between a task's stated premise and live state are reported in the RESULT file, never silently reconciled.
- **Commit and push at the end of every task and every burn**, per `~/GitHub/CLAUDE.md` §10. Event shards, raw model responses, sub-RESULTs, and the RESULT file are committed together with the code that produced them. There is no "operator commits" exception; a prior line here said burn runs leave shards uncommitted, and that contradicted the constitution (retracted 2026-08-21).
