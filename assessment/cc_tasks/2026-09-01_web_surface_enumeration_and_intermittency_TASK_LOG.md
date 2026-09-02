# Task log: web-surface target enumeration and barrier intermittency

**Spec:** `cc_tasks/2026-09-01_web_surface_enumeration_and_intermittency.md`
**Executed:** 2026-09-02 (UTC), repo `ai-readiness-fss`
**Status:** all three changes implemented, 156 tests passing (was 86), live
Census run recorded.

This repo is not Seldon-managed, so this file is the task record. `results/` is
gitignored (regenerable), so the run's headline numbers are transcribed here.

---

## What changed

| Area | File | Change |
|---|---|---|
| Enumeration source 2 | `harness/enumerate_sitemap.py` (new, 352 lines) | Walks the declared sitemap, seeded stratified sample per section |
| In-page metadata | `harness/jsonld.py` (new, 221 lines) | schema.org Dataset/DataCatalog extraction, normalized to DCAT field names |
| Probe applicability | `harness/probes/base.py` | `sources` declared per probe, `_Probe` shared base, `MetadataProbe.evaluate_page` |
| Intermittency | `harness/probes/d2_no_barriers.py` | n fetches, refusal fraction, per-attempt statuses |
| Surface firewall | `harness/rollup.py`, `harness/records.py` | `ProbeResult.source`, partition before summing |
| Orchestration | `harness/run.py` | Second source wired in, completeness signal, CLI caps |
| Gzip | `harness/fetch.py` | Decompress gzipped bodies, flag the transformation |
| Config | `config/harness.toml`, `config/agencies.toml` | `[sitemap]`, `[probes.d2_no_barriers]`, `sitemap_url` |

Tests added: `test_enumerate_sitemap.py` (19), `test_jsonld.py` (17),
`test_barrier_intermittency.py` (11), plus additions to `test_rollup.py` (4),
`test_runner.py` (9), `test_config.py` (6), `test_fetch.py` (3). Fixtures: three
sitemap XML documents, three HTML pages with different JSON-LD shapes.

Zero-dependency invariant held: `xml.etree`, `html.parser`, `json`, `random`,
`gzip`, `zlib`, `tomllib`. Nothing is imported from
`census-web-concept-inventory`; the sitemap parsing is a port, and the port is
cited in the module docstring.

---

## Change 1: second enumeration source

`enumerate_sitemap.py` ports `census-web-concept-inventory`
`src/pipelines/01_sitemap_universe.py` to stdlib. Three disciplines came with the
port and are pinned by tests:

1. **Follow robots.txt, record drift.** The configured `sitemap_url` is the
   recorded expectation, not the instruction. robots.txt is followed; a
   difference is reported as `sitemap_url_drift`. The directive match is
   case-insensitive, which matters: census.gov emits `SITEMAP:` uppercase.
2. **A failed child sitemap is recorded, never fatal.** Status, section and
   reason are captured and the walk continues.
3. **Counts reconcile.** Unique plus duplicates must equal parsed, or the sample
   is suppressed and the note says why.

Sampling is stratified by section and seeded. Each section draws from its own
stream keyed by `f"{seed}:{section}"`, so a section that disappears between runs
does not shift the pages drawn for every other section. Pools are sorted before
sampling, so the draw does not depend on the order the sitemap happened to list
URLs. A test pins this specific property.

**Probe applicability** is declared, not assumed. Each probe carries
`sources`; the runner asks. `d2_bulk` and `d2_programmatic` stay
catalog-only, because "is the whole dataset retrievable in bulk" is a question
about a catalog distribution and asking it of a product page would manufacture a
score out of a category error. `d1_stable_urls`, `d2_no_barriers`,
`d2_content_negotiation`, `d3_metadata_standard` and `d4_license` declare both.

**Rollup firewall.** `ProbeResult` gained a `source` field, and `rollup_agency`
partitions on it before any summing, structurally identical to how frontier is
firewalled. The web-surface result is called `vector_total`, not a composite,
because it runs a different probe set over a different denominator and is not
comparable to the catalog composite by construction.

## Change 2: catalog completeness signal

Emitted at `enumeration.web_surface.catalog_completeness`, carrying
`evidence_only: true`, `scored: false`, the named denominator, its value, the
count absent from the catalog, up to ten examples, and the fraction.

The fraction is `null` when the denominator is zero rather than `0.0`. A zero
denominator means completeness was not measurable from the sample, and a `0.0`
there would read as a clean result. This is the case that actually occurred on
Census (below), so the distinction is load-bearing, not defensive.

URL matching for the signal ignores scheme, case and trailing slash, which errs
toward judging a page present in the catalog. The signal is therefore
conservative about claiming fragmentation.

## Change 3: barrier intermittency

`d2_no_barriers` now fetches n times (config `[probes.d2_no_barriers] attempts`,
default 3) at the politeness delay and scores every attempt. Any refusal
(401/403 or barrier markers) fails the probe; the evidence carries
`refusal_fraction` and the ordered per-attempt statuses, so "refused once in
five" and "refused five in five" score the same and read differently.

No PARTIAL: a barrier that appears on some attempts is not half a barrier, it is
a barrier plus uncertainty about when.

**Defect found and fixed while rewriting the file.** The previous version had a
PARTIAL branch for a JS-render dependency that could never be reached, because
`"enable javascript"` is itself in `BARRIER_MARKERS` and the FAIL check on those
markers ran first. It was removed rather than left as a score the probe cannot
produce, and the docstring now states the actual behavior. No test covered that
branch, which is how it survived.

---

## Live Census run

```
python3 -m harness.run --agency census --max-datasets 2 \
    --max-dists-per-dataset 1 --sitemap-sample-size 2
```
2026-09-02, 2 min 48 s wall, roughly 105 requests at the 1.0 s politeness delay.

**Politeness check.** census.gov `robots.txt` declares `Crawl-delay` only for
Googlebot (15), Yahoo! Slurp (3) and bingbot (3). The `User-agent: *` group the
harness matches declares no `Crawl-delay` and no `Disallow` on `/quickfacts/`,
so the 1.0 s delay is inside what the site declares for this client. The
`usasearch` block disallows `/quickfacts/`, but that group does not apply here.

### Both vectors, side by side

| | catalog distributions | web surface (26 pages, 13 sections) |
|---|---|---|
| D1 | 10/10 | 52/52 |
| D2 | **14/16** | **78/104** |
| D3 | 12/16 | 0/52 |
| D4 | 8/16 | 0/52 |
| total | 44/58 core composite | 130/260 vector total |

The D2 divergence the spec asked for is present: 87.5 percent on catalog
distributions against 75.0 percent on the web surface. Within D2 it is entirely
`d2_content_negotiation`: PASS on 2 of 2 catalog distributions, PARTIAL on 26 of
26 pages (`mediaType=''`, `content-type='text/html'` under a machine-favoring
Accept). `d2_no_barriers` passed on all 26 sampled pages, refusal fraction 0.00.

D3 and D4 diverge harder than D2: 75 percent and 50 percent on the catalog, zero
on the web surface, because not one sampled page carries schema.org
Dataset/DataCatalog JSON-LD.

### The premise correction that matters

The spec says QuickFacts "self-describes" with in-page JSON-LD schema.org
Dataset/DataCatalog. Checked live on 2026-09-02: it does not. The one
`application/ld+json` block on
`https://www.census.gov/quickfacts/fact/table/US/PST045217` contains
`Organization` and `FAQPage` nodes. No `Dataset`, no `DataCatalog`. Three other
census.gov pages sampled by hand (`/data/datasets.html`, a library publication,
a tables page) carry no JSON-LD at all, and none of the 26 sampled pages did
either.

The reader was still built as specified, because reading in-page JSON-LD is the
right mechanism for a web surface and a fixture proves it scores a
Dataset-marked page correctly. The finding is that Census does not use it. The
consequence is stronger than the spec anticipated, not weaker: the web-surface
D3 vector is 0/52 and `catalog_completeness.fraction_absent_from_catalog` is
`null` on a denominator of 0, meaning catalog fragmentation is **not measurable**
on this surface because there is no in-page dataset markup to measure it with.

Recorded per the repo convention that a discrepancy between a task's stated
premise and live state is reported, never silently reconciled.

### The refusal is upstream of the measurement

The QuickFacts section could not be enumerated at all: its child sitemap
`https://www.census.gov/quickfacts/fact/sitemap/US/PST045217` returned **HTTP
403** to the harness, on 5 consecutive manual probes and again during the run.
It is recorded as a child failure, the walk continued, and 13 of 14 sections
parsed.

The consequence is worth stating plainly: **the barrier hides the surface that
has the barrier.** The sampled universe is 42,190 URLs rather than the 53,943
that `census-web-concept-inventory` enumerated on 2026-09-01. The missing
section is QuickFacts, which the prior art counted at 11,763 URLs. So the web-surface D2 vector
above understates the problem, because the worst surface is the one the
enumerator was refused access to. The prior-art non-QuickFacts denominator was
42,180 on 2026-09-01 against 42,190 here on 2026-09-02, a 10 URL day-over-day
change, which cross-validates the port against the original.

### Targeted live observation, folded into no vector

`d2_no_barriers` run directly against the QuickFacts page form the unenumerable
section would have contributed:

| when | client | statuses | refusal fraction |
|---|---|---|---|
| 2026-09-02 ~00:05Z | curl, harness UA | 403, 200, 403, 403, 403 | 0.80 |
| 2026-09-02 ~00:55Z | harness `HttpFetcher` | 403 | 1.00 |
| 2026-09-02 ~00:56Z | harness `HttpFetcher` | 403 x5 | 1.00 |

The mixed outcome is real: a 200 was observed. It also did not recur in the
harness runs, so a second explanation cannot be ruled out from this evidence:
curl and `urllib` differ in default request headers, and the edge may be keying
on header fingerprint rather than, or as well as, varying over time. Either way
the probe's behavior is the same and correct: it records what it got on each
attempt with a fraction, where one fetch would have reported a single verdict
with no indication that the next fetch might differ.

This observation was run deliberately outside the sampled run and is not part of
any vector.

---

## What was not done, and why

- **Web-surface results are not scored into any composite.** By design
  (Change 1.4). There is no single Census number in this output and there should
  not be one.
- **Catalog completeness stayed evidence-only.** Scoring it is a rubric change,
  not a code change (spec, Change 2).
- **The QuickFacts section was not worked around.** No alternate UA, no retry
  loop to get past the 403, no injecting known QuickFacts URLs into the sample.
  The harness is the machine and reports what the machine gets; manufacturing
  access would destroy the finding.
- **`politeness_delay_seconds` was left at 1.0.** It is inside what census.gov
  declares for this client. Changing a global tunable to suit one run is not
  this task's call.

## Follow-ups worth a task, not taken here

1. The web surface has no schema.org markup at all. Whether the rubric should
   treat in-page markup as the D3 anchor for web surfaces, or whether "no markup
   on any product page" deserves its own reported finding, is a rubric decision.
2. A section that refuses the enumerator is currently a `child_failure` line. It
   arguably belongs in the D1 vector as a discovery finding, which is also a
   rubric decision.
3. Only Census has a recorded `sitemap_url`. BLS and BEA will pick theirs up
   from robots.txt on the next full run, unverified until then.
