# Pilot Extraction Run — Status: STOPPED at precondition (no OAuth credential)

**Task:** cc_tasks/2026-07-03_pilot_extraction_run.md
**Date:** 2026-07-03
**Outcome:** Precondition rider completed and committed. **Extraction run did NOT execute** —
stopped before document 1 on an unsatisfiable Claude Max OAuth precondition. No documents were
extracted; no extraction/validation events, metrics, or proposed_relationships were produced.

## Precondition rider — DONE (commit 3ca82ed)

Strict index-pairing replaced the set-membership endpoint gate:
- `kg/schema.yaml`: every edge type now carries explicit `pairs` (legal endpoint pairs).
- `kg/extraction/schema_loader.py`: `is_valid_endpoint` enforces strict index-pairing
  (`extends` is Definition→Definition / Framework→Framework only, not the cross product;
  `builds_on` is the {Standard,Framework} cross product; `conflicts_with` symmetric same-type).
- `kg/extraction/parser.py`: a whitelisted edge with an **illegal** endpoint pair (grounded +
  resolvable) now routes to `proposed_relationships` (`source: auto_routed_invalid_pair`),
  preserving the §9 expressiveness measurement — it is neither quarantined nor written.
- Tests updated/added; **59 tests pass**. `seldon verify` clean (schema.yaml tracked-hash updated).

## Why the run stopped (run protocol step 1)

Step 1 mandates `claude-fable-5` via **Claude Max OAuth**, and hard-fails if `ANTHROPIC_API_KEY`
is present. Precondition scan of this environment:

| Check | Result |
|---|---|
| `ANTHROPIC_API_KEY` present | **No** (correct — must be absent) |
| `ANTHROPIC_AUTH_TOKEN` present | No |
| OAuth profile at `~/.config/anthropic/` | Absent |
| `ant` CLI (mints/refreshes OAuth tokens) | Not installed |
| bare `anthropic.Anthropic()` resolves a credential | No (no api_key, no auth_token) |
| `anthropic` SDK | 0.76.0 (present, but predates `claude-fable-5` / `output_config.effort`) |
| 5 pilot PDFs under `corpus/pilot/` | Present |

There is **no sanctioned credential** to authenticate the Fable calls. The only Claude-related
env is Claude Code's own internal session (`CLAUDE_CODE_*`), which is not a programmatic SDK
credential and must not be repurposed. Introducing `ANTHROPIC_API_KEY` is forbidden (DD-007 and
task step 1). Therefore the run cannot proceed, and no extraction was attempted.

## Not done (blocked)

- `model_stub.invoke()` was **not** implemented against the real client. Writing an
  API-call path that cannot be executed or verified here would ship unverified code
  (verification-before-completion); it is deferred until a credential exists so the code can
  be run and checked against the live API in the same task.
- No extraction/validation events, per-doc metrics, proposed_relationships, or token accounting
  — those require a real run.
- `seldon cc complete` was **not** run: the task is not complete.

## Gates (unchanged, not adjustable) — carried forward for the real run

- Per-document STOP: grounding quarantine rate > 10% on any document → STOP after that doc.
- Concept density: report per doc; flag any doc below 2.0 concepts/1k tokens as a thin-layer candidate.
- One call per document; a failed API call may be retried once verbatim; a *bad* extraction is data.

## To unblock

1. Install the Anthropic CLI (`brew install anthropics/tap/ant`) and run `ant auth login`
   (interactive, operator-side) to create a Claude Max OAuth profile — **or** export a
   short-lived `ANTHROPIC_AUTH_TOKEN` (never `ANTHROPIC_API_KEY`).
2. Upgrade the `anthropic` SDK to a build that supports `claude-fable-5` + `output_config.effort`.
3. Re-dispatch: implement `model_stub.invoke()` (PDF text as the grounding source, §5 emission
   order, strict JSON), then run the 5 documents sequentially under the gates above.
