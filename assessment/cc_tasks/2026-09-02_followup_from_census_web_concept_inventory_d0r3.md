# Follow-up note: QuickFacts in-page Dataset markup

**From:** `census-web-concept-inventory`, task D0-r3, Seldon 844f5cb0
**Beside:** `cc_tasks/2026-09-01_web_surface_enumeration_and_intermittency_TASK_LOG.md`
**Written:** 2026-09-02. Left as a note, not committed here; this
repository's owner decides what to do with it.
**Evidence:** `data/processed/d0_r3_summary.json` in the sibling repo,
and `docs/tevv/D0_quickfacts_ai_discoverability.md` revision note.

## The short version

`jsonld.py` is not at fault. The reader was tested against the same
bodies with an independent extractor and agreed on every one.

The premise correction in the task log, that Census does not use in-page
schema.org Dataset markup, does not hold for the QuickFacts URLs the
sitemap actually lists, and the run that produced it could not have
observed them.

## What was compared

Four bodies of QuickFacts pages, read by two extractors that share no
code: a regex over script tags written for the check, and this
repository's own `harness/jsonld.py` at the commit whose hashes the
sibling records.

Every readable body carries exactly one `application/ld+json` block, and
that block is a JSON array of four nodes in this order:

    Organization, FAQPage, DataCatalog, Dataset

That holds for a body captured 2026-09-01, for a second body of the same
URL captured the same day by a different code path, and for a fresh
fetch of the same URL on 2026-09-02. The 2026-09-01 and 2026-09-02
bodies of that URL differ in 6 regions, none containing a script tag or
an `ld+json` block, so nothing about the markup moved between them.

`harness/jsonld.py` read `has_dataset_markup` true on every one, and
normalized a record with `title`, `description`, `publisher`,
`license` and `identifier`. It is working as designed.

## Why the run could not have seen these pages

From `results/census_rollup.json` in this repository:

- `enumeration.web_surface.child_failures` holds one entry: the
  QuickFacts sitemap child `.../quickfacts/fact/sitemap/US/PST045217`,
  HTTP 403.
- `sections_parsed` is 13 of 14, and `per_section_parsed` has no
  QuickFacts section.
- `universe_total` is 42,190, which is the site's URLs excluding that
  section.
- `pages_probed` is 26, two from each of the 13 parsed sections.

So `pages_with_dataset_markup: 0` is a count over 26 pages drawn from a
universe that structurally excluded the stratum whose markup is in
question. The number is correct; the generalization drawn from it is
not. The web-surface D3 vector of 0/52 is likewise a statement about the
13 sections that parsed, and should be labelled that way.

For scale: the excluded section is 11,763 URLs, 21.8% of the sibling
project's full sitemap universe of 53,943.

## The URL form differs

The hand-check in the task log used
`https://www.census.gov/quickfacts/fact/table/US/PST045217`.

Every one of the 11,763 QuickFacts URLs the sitemap lists carries the
`PST045225` vintage, not `PST045217`. `PST045217` is the vintage in the
sitemap child's own filename, which does not match the URLs inside it.
The hand-checked URL is not in the sitemap universe.

This was not resolved and is stated as open. The edge returns 403 for
that URL to a residential host on both a `requests` client and this
repository's own `HttpFetcher`, so no body of that form could be read.
Common Crawl retained status-200 captures of it, but all four retrieved
captures are the QuickFacts application shell, so they carry no markup
either way.

The most parsimonious reading of the bytes in hand is that the
hand-checked URL serves a variant emitting the chrome nodes without the
dataset nodes, since `Organization` and `FAQPage` are exactly the first
two of the four nodes in the array the listed form serves, in the same
order. That is a reading, not a measurement, and it is not asserted.

## Common Crawl captures of QuickFacts are shells

Worth knowing for evidence interpretation. The retained status-200
captures of QuickFacts pages are the application shell: roughly 18 KB,
zero `data-mnemonic` attributes, and no `ld+json` block at all, against
roughly 112 KB and 64 mnemonics for a rendered page. A capture count for
this stratum overstates what an archive consumer can read.

## Probe-design findings from the earlier annotation

Recorded in the sibling's D0-r2 as routed here and delivered now, since
no artifact was placed in this repository at the time. Each was produced
by running this repository's probes against captured evidence.

- `d2_no_barriers` scores a single fetch. The QuickFacts refusal is
  intermittent: 5 of 8 sampled pages refused on one probe each, and one
  URL returned 403 four times consecutively after serving 200 minutes
  earlier. `base.DistributionProbe` already declares `multi_attempt` and
  `evaluate_attempts`, which this probe does not use, so the fix is to
  opt in rather than to add a mechanism.
- `d1_sitemap` reads a fixed `/sitemap.xml` and ignores the `Sitemap`
  line robots.txt declares. For census.gov those are different
  documents. `/sitemap.xml` holds 5,408 entries whose `lastmod` values
  all fall between 2013 and 2015, of which 2,315 of 5,362 are still in
  the current universe and none are QuickFacts. It scores PASS. The
  declared sitemap index is what yields 53,943 current URLs. The
  rubric's stated non-stale condition is also not implemented in the
  probe.
- `d1_robots` reads robots.txt only. census.gov scores PASS while 77 of
  98 sampled QuickFacts pages carry a `nofollow` meta robots directive
  that no probe reads.
- `d1_catalog` scores catalog presence, not coverage.
  `census.gov/data.json` scores PASS with 1,798 datasets whose 1,798
  distribution URLs all resolve to `api.census.gov`, and which reference
  QuickFacts zero times by any spelling. A machine that trusts the
  catalog cannot reach a product that is 21.8% of the site's own sitemap
  universe.

## What the sibling project offers back

Its sitemap universe is the target enumeration this harness's enumerator
lacks. `data.json` for Census yields 1,798 `api.census.gov` endpoints and
no web surface at all, and the sitemap traversal here drops the one
section that carries in-page dataset markup. The 53,943-URL universe,
with per-section counts and a `PST045217` section of 11,763, is
available as a fixed enumeration.

## Politeness

5 requests to census.gov for this check, all at a 3 second delay with an
identifying User-Agent, single threaded, no header variation and no
third-party crawler token. 4 range requests to `data.commoncrawl.org`.
