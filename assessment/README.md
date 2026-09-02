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
- **D1 Discovery (core):** `d1_robots`, `d1_robots_directives` (per page), `d1_sitemap`, `d1_catalog`, `d1_stable_urls`
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

# cap the second (web-surface) source, or skip it entirely
python -m harness.run --agency census --sitemap-sample-size 2 --max-sitemap-sections 3
python -m harness.run --agency census --no-sitemap

# run all configured agencies
python -m harness.run
```
Outputs per agency to `results/`:
- `<agency>_records.json` — every probe result `{probe_id, target, dimension, track,
  score, as_of_date, evidence, timestamp, evidence_path}`
- `<agency>_rollup.json` — core dimension vectors, core composite, the web-surface
  vector (separate), the two frontier tracks (separate), and enumeration metadata
  for both sources.

Raw evidence is written to `evidence/<agency>/`. Both `results/` and `evidence/`
are gitignored (regenerable).

## Configuration (`config/`, no hardcoded tunables — Engineering Standards §2)
- `harness.toml` — HTTP behavior (user agent, timeout, retries, politeness delay,
  body cap), evidence location + per-file cap, the track dating convention, the
  web-surface sampling tunables (`[sitemap]` size, section cap, seed), and the
  barrier probe's attempt count (`[probes.d2_no_barriers]`).
- `agencies.toml` — agency catalog roots the enumerator starts from, plus an
  optional `sitemap_url` recording the expected sitemap index. An agency with no
  machine-readable catalog is itself a **D1 finding** (recorded, not an error).
  robots.txt is what the harness actually follows for the sitemap; a difference
  from the recorded value is reported as drift.

## Target enumeration: two sources, never summed
**Source 1, the catalog.** `harness/enumerate_targets.py` parses a Project Open Data
/ DCAT `data.json` into candidate public data-asset endpoints (each distribution's
`downloadURL`/`accessURL`). No machine-readable catalog → recorded as a D1 finding;
the harness keeps going.

**Source 2, the web surface.** `harness/enumerate_sitemap.py` walks the sitemap the
agency's robots.txt declares and takes a seeded, stratified sample of the agency's
own product pages (one child sitemap = one section). It exists because source 1 is
not the whole surface: every one of Census's 1,798 catalog distributions sits on
api.census.gov, so its web products were outside the measurement universe entirely
and a product that refuses machines at the edge was invisible no matter how many
distributions the harness probed.

The two are **reported as separate vectors and never summed** (`harness/rollup.py`,
partitioned on `ProbeResult.source` before any addition, the same way frontier is
firewalled). They measure different surfaces, the whole point is that they can
diverge, and a single averaged number would erase the finding. Probes declare which
sources they apply to (`sources` on the probe class), so a distribution-only
question such as bulk availability is never forced onto an HTML page.

On a web surface the D3/D4 metadata probes read the page's own **in-page JSON-LD**
(schema.org `Dataset` / `DataCatalog`), normalized by `harness/jsonld.py` to the
same DCAT field names the catalog side uses, so one scoring rule covers both.

An evidence-only **catalog completeness** signal is emitted alongside: the fraction
of sampled pages carrying in-page `Dataset` markup that no `data.json` distribution
references, with its denominator. It is deliberately not scored, because the rubric scores
catalog presence, not completeness, and changing that is a rubric decision.

## Observed facts beside the score
Every record carries `observations`: structured facts kept apart from the score
and from any warning, so a threshold can change and history can be re-scored.
Warnings carry a `rule_id` and `rule_version`. Field names follow the SEO Machine
Diagnostic data dictionary where one exists. Added 2026-09-02 for the four
D0-r2 probe-design defects (`cc_tasks/2026-09-02_probe_depth_d0r2.md`):

- **Page-level robots directives** (`d1_robots_directives`, web surface only):
  `robots_meta` (meta name -> directives, including bot-specific names) and
  `x_robots_tag`. A `noindex` / `nofollow` / `none` (config) on a page scores
  PARTIAL with the directive as evidence; robots.txt eligibility (`d1_robots`)
  is unchanged.
- **The declared sitemap** (`d1_sitemap`): the probe follows the `Sitemap:`
  robots.txt declares and falls back to `/sitemap.xml` (`sitemap_source:
  fixed_path_fallback`). When the two differ, both are read and the fixed path
  is reported as `sitemap_divergence`. Non-stale condition: newest `lastmod`
  older than `[probes.d1_sitemap] stale_after_days` (default 365) scores
  PARTIAL (`sitemap_lastmod`, `sitemap_stale_warning`). No `lastmod` at all is
  recorded null and not scored stale (rubric v1.1, D1 sitemap no-`lastmod`
  clause: `lastmod` is optional in the protocol; absence is an unscored
  D4-class observation).
- **Catalog coverage of the sitemap universe** (`d1_catalog`):
  `catalog_sitemap_coverage`, the fraction of every sitemap-declared URL that
  the catalog references as a distribution or landing page, with numerator,
  denominator and per-section counts. The fraction is evidence only (threshold
  deferred to the January pilot, rubric v1.1 open item). A section with zero
  catalog references scores PARTIAL (`catalog_coverage_warning`, rule
  `catalog_zero_coverage` v1, rubric v1.1 Decision 1).
- **Crawler-access triad** (`d2_no_barriers` record, both surfaces):
  `effective_crawler_access` with `declared` (robots.txt per token,
  `[probes.crawler_access] declared_user_agents`, zero requests),
  `observed_public` (what the harness's own requests received, reusing the
  barrier attempts) and `enforced` (null unless an agency's
  `enforced_observations_file` supplies edge observations; no vendor reader).
  `crawler_policy_mismatch_warning` fires when robots.txt allows a client the
  edge refused. `observe_user_agents` (default empty) lists extra identities
  the harness may send; presenting a third-party crawler token is an operator
  decision per run.

## Barrier intermittency
`d2_no_barriers` fetches each target n times (`[probes.d2_no_barriers] attempts`,
default 3) at the politeness delay and scores every attempt. Any refusal fails the
probe and the evidence carries the refusal fraction and per-attempt statuses. One
fetch cannot distinguish "always refuses" from "refuses four times in five", and an
intermittent refusal is still a barrier to a machine that fetches once.

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
