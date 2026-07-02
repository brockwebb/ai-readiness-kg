# CC Task: Scaffold ai-readiness-kg repository

**Date:** 2026-07-02
**Project:** ai-readiness-kg
**Project root:** /Users/brock/GitHub/ai-readiness-kg
**Status:** proposed
**Immutable once written. Changes require a new task file.**

---

## Objective

Scaffold the repository: directory structure, gitignore, README, versioned schema config, controls file, and a clean sharded event log module. Initialize git and publish as a public GitHub repo (brockwebb/ai-readiness-kg) after a secrets check and operator STOP.

## Context (read first)

- `docs/schema_v0.1.md` — the extraction schema. Source of truth for schema.yaml.
- `docs/design_decisions.md` — DD-001..DD-008. This task implements DD-003 (manifest gate skeleton), DD-004 (controls.yaml), DD-008 (sharded event log).
- Reference implementation: `/Users/brock/GitHub/icsp_notebook/kg/eventlog.py` — read for the proven append/replay pattern. Write a CLEAN version; do not copy tech debt. This repo must be self-contained (DD-001): no imports from, or references to, icsp_notebook or Wintermute in code or docs.

## Steps

1. Create directory structure (docs/, cc_tasks/, handoffs/ already exist):
```
kg/                  # pipeline code
kg/__init__.py
corpus/              # source documents (committed)
corpus/staging/      # harvester finds, pre-manifest (gitignored)
events/              # sharded JSONL event logs (committed)
tests/
```

2. `.gitignore` — seed from `/Users/brock/GitHub/icsp_notebook/.gitignore`, adapted. Must include at minimum: `.env`, `__pycache__/`, `.DS_Store`, `.pytest_cache/`, `corpus/staging/`, `*.bak-*`, `logs/`.

3. `controls.yaml` at repo root (DD-004), exactly:
```yaml
# Operational switches. External systems (Wintermute control panel)
# flip these by writing this file. This file is the entire interface.
schema_version: "0.1"
forage: off
extract: off
budgets:
  forage_daily_docs: 25
  extract_daily_docs: 10
```

4. `kg/schema.yaml` — transcribe node types, edge types, and universal provenance properties from `docs/schema_v0.1.md` sections 2–4 into YAML. Top keys: `schema_version: "0.1"`, `node_types:`, `edge_types:`, `provenance_required:`. Every node type lists its properties; every edge type lists `from`, `to`, `meaning`. No invention — transcription only. If anything in the doc is ambiguous, STOP and note it in the completion report rather than guessing.

5. `kg/eventlog.py` — clean sharded event log (DD-008):
   - Shards at `events/batch-{NNN}.jsonl`, NNN zero-padded 3 digits.
   - `append(event: dict, batch: int) -> str` — appends one JSON line, injects `event_id` (uuid4 hex), `timestamp` (UTC ISO), `schema_version` (read from kg/schema.yaml); returns event_id.
   - `replay() -> Iterator[dict]` — yields all events across all shards in batch order, then line order.
   - `current_batch() -> int` — highest existing batch number, or 0.
   - Append-only. No mutation or deletion functions. Stdlib only.

6. `tests/test_eventlog.py` — pytest, tmp_path based: append to two batches, replay returns all in order, event_id and timestamp injected, file contents are valid JSONL.

7. `README.md` — short: what the graph is (validity layer under the FSS AI readiness survey and definitions work), pattern lineage (manifest-gated corpus, event-sourced JSONL, verbatim-grounded extraction), pointer to docs/. No aspirational feature lists.

8. Run `python -m pytest tests/ -v`. All green required before proceeding.

9. `git init`, add all, initial commit: `scaffold: structure, schema v0.1 config, controls, sharded eventlog`.

10. **Secrets check:** verify no `.env`, no key material, nothing matching `ANTHROPIC_API_KEY|sk-` in tracked files (`git grep`).

11. **STOP — operator checkpoint.** Report secrets-check result and await explicit go before: `gh repo create brockwebb/ai-readiness-kg --public --source=. --push`.

## This task does NOT

- Write any extraction, manifest-ingest, harvester, model-client, or MCP server code.
- Create any events or manifest entries.
- Touch icsp_notebook, Wintermute, or ai-readiness-fss beyond the two read-only reference reads named above.
- Modify docs/schema_v0.1.md or docs/design_decisions.md.

## Verification checklist

- [ ] Directory structure matches step 1
- [ ] .gitignore covers the minimum set
- [ ] controls.yaml matches step 3 verbatim
- [ ] kg/schema.yaml is a faithful transcription (spot-check 3 node types, 3 edge types against the doc)
- [ ] pytest green
- [ ] No cross-repo imports or path references in code
- [ ] Secrets check clean
- [ ] STOP honored before public push
