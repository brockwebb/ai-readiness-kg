# Machine Benchmark Rubric — FSS AI Data Readiness
*The load-bearing instrument. Test the machine by being the machine.*

## Premise
Public-facing AI data readiness is **directly testable** — point an agent at what an agency exposes and score what comes back. No self-report. The only way to score well is to actually be machine-consumable. This is the part absent from the existing literature (NOAA/ESIP, Virginia, NIH all measure fitness-for-training, not machine-as-consumer).

## Framing: diagnostic that scores (decided)
This is a **diagnostic in purpose, a measurement in mechanism.** It emits an objective score and those scores aggregate into a system-wide readiness picture. It is NOT a self-rated scorecard, and the distinction is mechanical, not cosmetic: the score comes from probing what an AI agent actually encounters, so there is no self-assessment layer to inflate. "No one can hide" follows from the measure being reality-based, not from surveillance.

The thing that keeps aggregation *just* (rather than punitive) is the scope boundary (protected data never enters the frame at all) plus the covariate/peer-cohort layer. Aggregation without fairness stratification would convert "diagnostic" into "scorecard with teeth" — so the fairness layer is load-bearing, not ornamental.

## Scoring model
- Per-probe: **pass / partial / fail** (2 / 1 / 0). Avoid finer scales — they invite interpretation theater.
- Each probe is **independently reproducible** by anyone with a browser + Python.
- Agency score = sum within dimension, reported **per-dimension**; dimension vectors aggregate to a system picture, read **within peer cohort** (see covariate schema), never as a naked cross-agency ranking.
- **Every probe emits evidence** (the actual HTTP response / artifact retrieved), so a score is auditable, not asserted.

## Two scoring tracks: core vs. frontier (the access-axis firewall)
The adopted definition (`icsp_notebook` task `51fe4574`, flagship term **AI-ready data** in `fss_ai_vocabulary.json`) splits cleanly:
- **Part A** — the grounded, content-side definition: *readiness of data a consuming system can already reach.* Machine-understandability, provenance, methodology, quality preserved and programmatically queryable. Grounded in established mechanisms (OPEN Government Data Act, Project Open Data, FCSM 25-03 AI-friendly APIs/metadata, FCSM 20-04 data quality). **This is the CORE score.**
- **Part B** — `forward_interpretation`, typed `author_framing`, dated `2026-06`, explicitly *not* a ratified standard: the **discoverability/retrievability (access) axis** the current corpus does not yet cover, named concretely as the emerging mechanisms `llms.txt`, `MCP`, `WebMCP`. **This is the FRONTIER track.**

The firewall is therefore **not** "D1/D2 = frontier." It is **established mechanism = core** (across all four dimensions) **vs. emerging-standard access mechanism = frontier** (exactly the three Part B names). The bulk of D1 (robots/sitemap/DCAT catalog/stable URLs), D2 (programmatic access, content negotiation, bulk, no anti-machine barriers), D3, and D4 are all established → core. Only `llms.txt`, `MCP`, `WebMCP` are bracketed off. The diagnostic MUST honor this or it contaminates the graded core with a standard that postdates the policy corpus.

### Frontier maturity tiers (llms.txt is NOT WebMCP)
The frontier track is not flat — partial forward-lean is informative signal, so "has llms.txt but not WebMCP" must be distinguishable from "has neither":
- **`frontier_near`** — `llms.txt`. A low-effort, already-circulating convention achievable **today**. Failing it reads as "hasn't bothered," not "ahead of the standard." `as_of_date: 2024-09` (convention first circulated).
- **`frontier_deep`** — `MCP` / `WebMCP`. WebMCP was standardized only ~2026-Q1, roughly three months before this assessment. Presence is visionary; absence is explicitly **NOT** core unreadiness — the standard barely existed when the policy corpus was written. `as_of_date: 2026-01` (WebMCP standardization).

Each frontier probe carries its `as_of_date` in the emitted record so the dating convention lives in the data, not just this prose. Presence is an asset (carrot); absence is never scored as core unreadiness (no stick). This is the document-level analog of the grounded-vs-author_framing discipline: the core score is grounded; the frontier track is explicitly dated forward interpretation. Never blur them into one composite.

## Scope boundary (the measurement universe)
**The measurement universe is public and public-mandated data assets ONLY.** Protected data (Title 13 microdata, Title 26, CIPSEA-restricted, PII) is OUT OF SCOPE — not flagged, not stratified, not scored. The instrument measures one thing: is data that is *already public or mandated-public* exposed in AI-ready ways? It has NOTHING to do with access to protected data. Nobody is being asked to expose protected data; the question is whether the data an agency *already publishes* is published so a machine can actually use it.

This preempts the "you're penalizing us for protecting data" attack entirely — protected data never enters the frame, so there is nothing to argue about. Cleaner and more defensible than stratifying legal constraint: there are no low scores on protected data because protected data is not measured.

**Design-history note:** an earlier draft ran a "can't-vs-hasn't gate" that classified each target as LAWFULLY NON-EXPOSED (Title 13/26/CIPSEA/PII) vs. EXPOSABLE and scored only the exposable set. That was the wrong register — it brought protected data into the frame just to exclude it, inviting exactly the argument the scope boundary forecloses. The gate is retired. The only surviving fragment is restriction-discoverability, narrowed and folded into D3 (see below): if a public catalog *points at* a restricted dataset, a machine should be able to learn *that it is restricted and why* — an interpretability property of the public catalog, not a top-level gate.

## Dimensions & probes

### D1 — Discovery (can a machine find the data?) — CORE
| Probe | Pass condition |
|---|---|
| robots.txt permits agents | Not blanket-blocking; declares sitemap |
| sitemap.xml | Present, parses, non-stale |
| Structured catalog | data.json (Project Open Data) / DCAT resolves & validates |
| Stable, semantic URLs | Resources addressable, not session/JS-gated |

*(`llms.txt` was previously listed here; it is an emerging access-axis standard → moved to the Frontier access track, `frontier_near`.)*

### D2 — Retrieval (can a machine get it?) — CORE
| Probe | Pass condition |
|---|---|
| Programmatic access | API or bulk download w/o human/JS interaction |
| Content negotiation | Honors Accept headers; offers machine formats (JSON/CSV/Parquet) not just HTML/PDF |
| No anti-machine barriers | No CAPTCHA / login wall / JS-render requirement on public data |
| Bulk availability | Whole dataset retrievable, not just paginated UI scraping |

*(`MCP / WebMCP endpoint` was previously listed here; it is an emerging access-axis standard → moved to the Frontier access track, `frontier_deep`.)*

### D3 — Interpretability (can a machine use it correctly?) — CORE
| Probe | Pass condition |
|---|---|
| Machine-readable schema | Column/field definitions retrievable as data, not prose PDF |
| Metadata standard | DCAT / schema.org / ISO 19115 etc. present & valid |
| Provenance | Source, collection method, version, date machine-readable |
| Semantic clarity | Codes/enums documented in retrievable form |
| Units & types declared | No guessing field meaning or measure |
| Access-tier metadata | Where a public catalog points at a restricted dataset, the restriction *and its reason* are machine-readable (the catalog tells a machine *that* it is restricted and *why*) — interpretability of the public catalog, not access to the protected data |

### D4 — Trust / freshness (can a machine rely on it?)
| Probe | Pass condition |
|---|---|
| Versioning | Version or last-modified machine-readable |
| Update cadence declared | Stated and honored |
| Integrity signal | Checksums / signing / canonical source declared |
| License machine-readable | Use rights expressed as data |

### Frontier access track (Part B — dated, reported-not-penalized)
The access/discoverability axis the adopted definition brackets as forward interpretation. Reported on its **own** track, NEVER folded into the core composite. Each probe emits its `as_of_date`. Tiers let partial forward-lean show:

| Probe | Tier | as_of_date | Pass condition |
|---|---|---|---|
| llms.txt present & valid | `frontier_near` | 2024-09 | Resolves at root, parses, points to real resources |
| MCP / WebMCP endpoint | `frontier_deep` | 2026-01 | Advertised, reachable, returns valid tool/resource schema |

"Has `llms.txt` but not WebMCP" (`frontier_near` pass, `frontier_deep` fail) is a distinct, informative state from "has neither" — partial forward-lean is signal, not noise. Presence is an asset; absence is never core unreadiness.

## Output
Per agency: core dimension vector `[D1, D2, D3, D4]` + core composite + the two frontier tracks (`frontier_near`, `frontier_deep`) reported **separately** + evidence bundle. No can't/hasn't classification — protected data is out of scope (see Scope boundary), so there is nothing to classify. Feeds the covariate/clustering layer for peer-relative interpretation.

## Deliberately excluded (anti-PMT)
- No maturity level / 1–5 stars / graded "tier" label on the score. Goodhart bait. (The `frontier_near`/`frontier_deep` labels are **not** maturity grades — they are temporal dating buckets marking *when a standard emerged*, attached to the dated frontier track, never to the core score.)
- No self-attested fields anywhere in the benchmark. If a human types it, it's not a benchmark.
- No aggregate composite score until intended-use is decided.

## Open items
- [x] Diagnostic vs. scorecard — RESOLVED: diagnostic in purpose, measurement in mechanism, scores aggregate within peer cohort. Anti-gaming comes from reality-based probing, fairness from the scope boundary + covariates.
- [x] Access-axis contamination — RESOLVED: core vs. frontier two-track split; llms.txt + MCP/WebMCP report on dated frontier track, not core score.
- [x] Scope boundary (was: can't-vs-hasn't gate) — RESOLVED (1A): measurement universe is public/public-mandated assets only; protected data out of scope, never measured. Can't-vs-hasn't gate retired; restriction-discoverability folded into D3 as machine-readable access-tier metadata.
- [x] Frontier maturity tiers + dating convention — RESOLVED (1B): `frontier_near` (llms.txt, as_of 2024-09) vs `frontier_deep` (MCP/WebMCP, as_of 2026-01); per-probe `as_of_date` in emitted record; "llms.txt but not WebMCP" is a distinct state.
- [ ] Probe implementation: Python harness, one module per probe, evidence capture. (CC task 2026-06-23 Stage 3)
- [ ] Target list per agency (what URLs/endpoints constitute "their data"). (CC task 2026-06-23 Stage 3 — enumeration)
