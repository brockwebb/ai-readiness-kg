# FSS AI Data Readiness — Probe Harness

*Test the machine by being the machine.* Point probes at what a federal statistical
agency publicly exposes and score what comes back. No self-report; every score is
backed by the raw artifact it was read from.

## What this is
A zero-runtime-dependency Python harness that measures **public-facing AI data
readiness**: can a machine *find*, *retrieve*, *interpret*, and *rely on* the data
an agency already publishes? It implements the rubric in `benchmark_rubric.md` and
feeds the peer-cohort layer in `covariate_clustering_schema.md`.

It is **reproducible by anyone with a browser + Python** — public endpoints only,
no auth, no API keys, no third-party packages. That reproducibility is the design's
source of authority: anyone can re-run it and see the same publicly-observable facts.

## Design invariants (do not violate)
- **No PMT (performative metric theater).** No self-attested field is ever a scored
  input. If a human types it, it is not a benchmark input.
- **Pass/partial/fail only (2/1/0).** No maturity stars, no graded tiers on the score.
- **Evidence-emitting.** Every probe writes the raw response to disk beside the
  score; a reviewer verifies any score from emitted evidence without re-running.
- **Scope boundary.** The measurement universe is *public and public-mandated data
  assets only*. Protected data (Title 13/26, CIPSEA, PII) is out of scope — never
  flagged, never scored. See `benchmark_rubric.md` → Scope boundary.

## The core-vs-frontier firewall (traceability)
The core-vs-frontier split traces to **icsp_notebook task `51fe4574`**, flagship
term *"AI-ready data"* in `corpus/vocab/fss_ai_vocabulary.json`:

| Definition part | Meaning | Harness mapping |
|---|---|---|
| **Part A** (grounded, content-side) | readiness of data a consuming system can *already reach* | `core` track → core composite |
| **Part B** (`forward_interpretation`, dated 2026-06, *not* a standard) | the access axis: `llms.txt`, `MCP`, `WebMCP` | `frontier_near` / `frontier_deep` tracks, **never** in the core composite |

The firewall is **established mechanism = core** (across all four dimensions) vs.
**emerging-standard access mechanism = frontier**. It is enforced structurally in
`harness/rollup.py`: frontier results are partitioned out before the composite is
summed, so no code path can fold a frontier score into the headline.

- `frontier_near` = `llms.txt` (as_of 2024-09) — achievable today; absence is "hasn't bothered."
- `frontier_deep` = `MCP`/`WebMCP` (as_of 2026-01) — visionary; absence is **not** core unreadiness.

## Dimensions & probes (one module per probe, `harness/probes/`)
- **D1 Discovery (core):** `d1_robots`, `d1_sitemap`, `d1_catalog`, `d1_stable_urls`
- **D2 Retrieval (core):** `d2_programmatic`, `d2_content_negotiation`, `d2_bulk`, `d2_no_barriers`
- **D3 Interpretability (core):** `d3_metadata_standard`, `d3_provenance`, `d3_schema` (also covers semantic-clarity + units/types — all need the retrievable schema), `d3_access_tier`
- **D4 Trust/freshness (core):** `d4_versioning`, `d4_cadence`, `d4_license`, `d4_integrity`
- **Frontier (Part B):** `frontier_llms_txt` (near), `frontier_mcp` (deep)

Each probe separates `fetch` (network I/O) from `evaluate` (pure scoring of a
fetched artifact) so scoring is testable from fixtures without the network.

## Usage
```bash
# list configured agencies
python -m harness.run --list

# run against specific agencies, politely capped
python -m harness.run --agency census --agency bea --max-datasets 3 --max-dists-per-dataset 1

# run all configured agencies
python -m harness.run
```
Outputs per agency to `results/`:
- `<agency>_records.json` — every probe result `{probe_id, target, dimension, track,
  score, as_of_date, evidence, timestamp, evidence_path}`
- `<agency>_rollup.json` — core dimension vectors, core composite, the two frontier
  tracks (separate), and enumeration metadata.

Raw evidence is written to `evidence/<agency>/`. Both `results/` and `evidence/`
are gitignored (regenerable).

## Configuration (`config/`, no hardcoded tunables — Engineering Standards §2)
- `harness.toml` — HTTP behavior (user agent, timeout, retries, politeness delay,
  body cap), evidence location + per-file cap, and the track dating convention.
- `agencies.toml` — agency catalog roots the enumerator starts from. An agency with
  no machine-readable catalog is itself a **D1 finding** (recorded, not an error).

## Target enumeration
`harness/enumerate_targets.py` parses a Project Open Data / DCAT `data.json` into
candidate public data-asset endpoints (each distribution's `downloadURL`/`accessURL`).
No machine-readable catalog → recorded as a D1 finding; the harness keeps going.

## Out of scope (deliberately)
- **M-25-21 AI use-case inventories.** Self-reported and inflation-prone — a
  **pointer, never a scored metric**. No score is computed from inventory contents.
  See `notes/inventory_as_pointer_constraint.md`.
- **Clustering / peer cohorts.** The rollup *feeds* the covariate layer; clustering
  is a later, post-data task (see `covariate_clustering_schema.md` sequencing).

## Tests
```bash
python -m pytest tests/ -v
```
Pure logic (records, rollup firewall, config, enumeration, evidence, every probe's
`evaluate`) is covered; network I/O is exercised by the live end-to-end run.
