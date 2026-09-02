# CC Task: web-surface target enumeration and barrier intermittency

**Created:** 2026-09-01
**Repo:** ai-readiness-fss (not Seldon-managed as of this date; this
file is the task record).
**Motivation:** The Census run scored D2 at 21/24 while the site's
flagship product, QuickFacts, refuses automated clients at the edge
(measured 2026-09-01 in census-web-concept-inventory task D0: 2,874 of
4,374 Common Crawl index records for /quickfacts/fact/table/ are HTTP
403; home-machine probes refused 5 of 8). The harness could not see
this because `enumerate_targets.py` reads data.json only, and for
Census every one of its 1,798 distributions is on api.census.gov. Web
product surfaces are outside the measurement universe. Separately,
`d2_no_barriers` evaluates one fetch, and the refusals are
intermittent, so its result on such a surface is a coin flip.

## Change 1: second enumeration source, sitemap-derived web surfaces

1. Add a `sitemap` enumeration source alongside `data.json`, config
   driven (agencies.toml gains an optional `sitemap_url`; harness.toml
   gains sampling tunables). Parse the sitemap index and children
   (reuse the parsing approach from
   census-web-concept-inventory/src/pipelines/01_sitemap_universe.py;
   adopt, do not reinvent, but the harness stays zero-dependency, so
   port to stdlib xml.etree rather than importing).
2. Stratified sample per child sitemap (section), size from config,
   seeded and recorded, so the probe count stays polite and
   reproducible. Each target carries `source = "sitemap"` and its
   section.
3. Web-surface targets run D1 stable_urls, D2 no_barriers, D2
   content_negotiation, D3 metadata_standard (extend it to read
   in-page JSON-LD schema.org Dataset/DataCatalog, which is how
   QuickFacts self-describes), and D4 license (from JSON-LD license
   field when present). Record which probes apply per source in the
   probe base class; do not force distribution-only probes onto HTML
   pages.
4. Rollup: report web-surface results as their own vector alongside
   the catalog-distribution vector, never summed into one D2 number,
   because they measure different surfaces and the whole point is that
   they can diverge. Firewall this structurally in rollup.py the same
   way frontier is firewalled.

## Change 2: catalog completeness signal (D1, evidence only)

For agencies with both sources, emit an evidence-only field: fraction
of sampled web-surface pages carrying in-page Dataset markup that are
not referenced by any data.json distribution. This is not a scored
probe (the rubric scores presence, not completeness, and changing that
is a rubric decision, not a code change); it is emitted so a reviewer
can see catalog fragmentation with a denominator.

## Change 3: barrier intermittency

`d2_no_barriers` fetches n times (config, default 3) at the politeness
delay and records status per attempt. Score: FAIL if any attempt is
401/403 or shows barrier markers; evidence carries the refusal
fraction. Rationale in the docstring: an intermittent refusal is still
a barrier to a machine, and one fetch cannot distinguish always from
sometimes.

## Verification

Tests for the new enumerator from a sitemap fixture; tests for
multi-fetch scoring from fixtures with mixed statuses; a live Census
run capped at a small sample showing the web-surface D2 vector diverge
from the catalog-distribution D2 vector. Record the run in results/.

## What NOT to do

- No third-party dependencies (harness invariant).
- No self-attested inputs. No composite across surfaces.
- No em dashes; the word "clever" is banned.
- Commit and push on completion; write a task log beside this file.
