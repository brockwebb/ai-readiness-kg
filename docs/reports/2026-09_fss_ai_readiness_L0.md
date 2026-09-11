# AI readiness of the federal statistical system: host-level findings

**Draft. 16 recognized bodies and three reference
hosts, one cycle, one client identity.**
Written from `cc_tasks/2026-09-09_report_draft.md` and revised to the cycle of 2026-09-10
under `cc_tasks/2026-09-11_l0_report_cycle4_revision.md`. The snapshot is cycle
`scan_2026-09-10`, the first over the complete frame, re-judged as `scan_2026-09-10_rj2`:
the same stored observations under the rules current when this was written. Every number
below is a registered Result quoted by name; nothing is typed into the prose.

## What was measured, and over what

The frame is the recognized agencies and units of the federal statistical system:
16 bodies. They are taken from the Interagency Council on
Statistical Policy's own charter, which enumerates its membership under an explicit flag legend
rather than in prose. Recognition is a legal status conferred under CIPSEA 2018 (44 U.S.C.
3561, 3562), so the roster is a parse of an authoritative list and not a judgement about who
counts. The charter and the Council's public About page disagree about
1 body, the Social Security Administration's
research office. The charter marks it recognized and the About page does not, and the charter
was named the authority before either document was read.

Three further hosts appear in the measurement and in none of its rates: data.gov, NIST and GSA.
These are reference hosts. A federal catalog and two data portals are the nearest available
control for what a machine-facing government site looks like when someone has tried. They are
judged on the host-level checks only and enter no agency denominator, because placing a catalog
beside a statistical agency above that level compares two different kinds of thing.

Counting surfaces rather than bodies, the target list carries
72 declared surfaces across
22 netlocs. Netlocs exceed bodies because each reference
host declares a machine entry point on its own hostname. Every surface is declared, by the
roster or by the operator, and no rule selects one. Three selection rules were built for this
frame and all three failed; the record of why is in the design decisions.

## The client, and what it did

One identified client, one request per second per host, `robots.txt` obeyed, no forms, no
logins, no query-string fuzzing. The user agent names the project and links to its source. The
scanner has never retried a host under another identity, because a refusal is itself a
measurement and a disguise would destroy it.

The cycle issued 2684 requests across
35 netlocs, which is more netlocs than the
target list names. The excess is not an accident and is discussed under what the matrix cannot
see. It produced 2718 observations and
739 findings, and every finding re-derives byte for
byte from its stored observations. The requests and the observations are the measured cycle's
and carry its name; the findings are the re-judgement's, over those same observations, because
a re-judgement opens no socket.

## The six checks

Each asks something a machine would need before it could use a body's statistics without a
person in the loop.

**A4** asks whether the host serves a `robots.txt` and whether it permits an identified,
compliant client to read the page in question. A site with no such file has not refused; it has
said nothing, and a client has to guess.

**A5** asks whether the host offers a way to discover what it publishes, through a sitemap it
declares itself or one of the newer machine-directed files. Discovery is the difference between
a catalogue and a maze.

**A10** asks whether a deep link behaves. A page that answers a nonsense URL with a cheerful
page and a success status tells a machine that everything exists, which is worse than an honest
absence.

**A11-declared** asks whether the host declares a machine layer anywhere in its own markup: an
API, a bulk endpoint, a data catalogue.

**A12** asks whether what the host declares and what it enforces agree, comparing the
permission stated in `robots.txt` against the answer a compliant client actually receives on
the same path. It is a candidate check, adopted by nobody, and it enters no fraction here.

**G1-D** asks whether published figures carry the fields that make them interpretable: a
measure of uncertainty, a suppression flag, a reliability marker. An estimate without them can
be read by a machine and cannot be used responsibly by one.

## The matrix

One row per body, one column per check, one cell per verdict. `pass` and `fail` are
measurements. `error` means this scanner could not observe the surface, which is a fact about
the scanner and its reception, never a fact about the product. The last column counts how many
of the probes issued against the body's own page the host answered with a refusal status.

The five surface-judged checks are read from each body's home page, and the coherence check
from its well-known set. Which surface a cell was measured on is recorded on every row of the
machine-readable copy beside this one. It matters: a `robots.txt` that permits the front door
can disallow a particular product, so a flagship page and a home page need not receive the same
answer. This cycle found that disagreement on
17 cells across
8 bodies, and a single
combined cell would have had to pick one without saying which.

| Agency | A4 | A5 | A10 | A11-declared | A12 | G1-D | Refused of probed |
|---|---|---|---|---|---|---|---|
| BEA | pass | fail | pass | pass | pass | fail | 0 of 59 |
| BJS | pass | fail | pass | pass | pass | fail | 0 of 59 |
| BLS | error | error | error | error | fail | error | 33 of 35 |
| BTS | error | error | error | error | fail | error | 32 of 33 |
| CENSUS | pass | pass | pass | pass | pass | fail | 4 of 59 |
| DRSMSU | fail | fail | pass | fail | fail | fail | 0 of 67 |
| EIA | pass | pass | pass | pass | pass | fail | 1 of 64 |
| ERS | pass | fail | pass | pass | pass | fail | 0 of 60 |
| NAHMSAPHIS | pass | fail | pass | pass | pass | fail | 0 of 58 |
| NASS | pass | fail | pass | pass | pass | fail | 0 of 66 |
| NCES | pass | fail | pass | pass | pass | fail | 0 of 63 |
| NCHS | pass | fail | fail | fail | pass | fail | 0 of 34 |
| NCSES | pass | pass | pass | pass | pass | fail | 0 of 65 |
| ORES | error | error | error | error | fail | error | 32 of 33 |
| SAMHSACBHS | pass | fail | pass | pass | pass | fail | 0 of 62 |
| SOI | pass | fail | pass | pass | pass | fail | 3 of 59 |
| *this report* | \- | \- | \- | \- | \- | \- | no host yet; the instrument is turned on this report when it is published |

### Reading it by column

**Serving `robots.txt`.** 12 bodies of
13 observable ones serve a `robots.txt` that
permits this client to read the page. The single failure serves no such file at all: not a
refusal, an absence, and a machine meeting it has to assume rather than read.
3 bodies could not be observed on this check, and
the same 3 recur in every column below.

**Discovery.** 3 of
13 offer a discoverable index of what they
publish; 10 do not. Discovery is the weakest
host-level result by a wide margin, and the consequence is direct: a machine that cannot
enumerate what a site publishes cannot tell what it has missed. Every sitemap any host
declared was followed, including ones declared on a neighbouring hostname, so none of these
failures is an artefact of the scanner declining to look.

**Deep links.** 12 of
13 answer a deliberately invalid URL
honestly. This is the best result on the page and it deserves less credit than it looks: it
measures the absence of a specific pathology rather than the presence of a capability.

**Declared machine layer.** 11 of
13 declare somewhere in their own
markup that a machine reader is expected. Declaring is not providing, and this check does not
follow the declaration to see whether anything answers at the other end.

**Declared against enforced.** The candidate check finds
12 bodies coherent and
4 incoherent, of
16. An incoherent host publishes a
`robots.txt` granting access and then declines to serve the client that obeys it. Three of them
are the bodies discussed in the next section, and the fourth publishes no `robots.txt` at
all.

**Uncertainty fields.** 0 bodies of
13 expose the fields that make an estimate
interpretable at the host level. The upper bound of the ninety-five percent interval on that
rate is 0.228095 at this denominator, which is
the honest way to say that a zero here is not proof of universal absence. It is measured on
the body's own front page and not on a data product, which flatters nobody and is a limit of
the host-level view rather than a finding about statistical practice.

### The reference hosts

| Agency | A4 | A5 | A10 | A11-declared | A12 | G1-D | Refused of probed |
|---|---|---|---|---|---|---|---|
| GSA | pass | fail | pass | pass | pass | fail | 0 of 11 |
| NIST | pass | fail | pass | pass | pass | fail | 0 of 11 |
| data.gov | pass | fail | pass | pass | pass | fail | 0 of 12 |

All 3 reference hosts serve `robots.txt`, declare
a machine layer, answer deep links honestly and are coherent between declaration and
enforcement. All three fail discovery. All three also fail the uncertainty check, which for a
catalogue is the expected and uninteresting answer: it carries no estimates, so it has no
uncertainty fields to expose. They appear here for contrast and in no rate above.

## Three bodies will not serve a compliant machine

3 bodies of
16 decline to answer a client that identifies itself, says where to complain about
it, asks for no more than one page per second, and obeys the `robots.txt` those same hosts
publish. They are the Bureau of Labor Statistics, the Bureau of Transportation Statistics and
the Social Security Administration's research office. Each returns a refusal status on
effectively every request. Their rows above read `error` throughout, which is the correct
reading: this instrument did not find those sites wanting, it was not allowed to look.

The behaviour is neither a transient nor a sampling accident. It has now been recorded in
6 separate measurements,
taken on four different days under two different user-agent strings. The count survives a change in how this project names errors: the earliest
filed the refusal under a general client-error class, because the closed set of names had no
member for a refusal until later. The number of bodies refusing has not moved, standing at
3 on the first look and the same on
the most recent.

Two things follow, and only two. First, the coherence check fails on all three: each publishes
a `robots.txt` that grants access and then refuses the client that honours it. Whatever the
intent, the machine-readable statement and the machine-observable behaviour disagree, and a
client has no way to discover which one is real except by being turned away. Second, no rate in
this report describes them, and none can. They are in the frame, they are counted in the
denominator of nothing, and the space they occupy in the matrix is the shape of what is not
known.

What does not follow is any account of why. This scanner sees a status code. Bot management, a
content delivery configuration, a deliberate policy and an unnoticed default all look identical
from outside, and the only honest thing to report is the behaviour and its persistence.
Distinguishing them needs either the operator's own logs or a request made from a different
vantage point, and both are named as future research rather than guessed at here.

In the previous cycle a fourth body could not be observed either, for an unrelated reason: its
host timed out or closed the connection on most probes. It answered this time, and the three
refusing bodies are now the whole of the unobserved column — which is why the `error` counts in
the matrix are lower here than a reader of the last cycle would expect, and why they still are
not zero.

## What the products offer a machine

Everything above measures a host. This section measures products, and for the first time it
covers the whole frame. Every one of the 16 bodies now has a
flagship product declared for it —
16 agencies across
23 declared surfaces — and
0 bodies carry a host row
and nothing else.

7 of those flagships were declared for this
cycle, for the bodies that had none when the previous one ran, and each was verified
robots-first before it entered the frame.
3 of them were answered with a
refusal by the same hosts that refuse this client at every other door. They enter marked as
refused rather than dropped: restricting the instrument to the agencies that permit it would
make the frame a function of who answers. The rest came live in this cycle and are measured
below.

| Agency | Surface | A1 | A2 | A3 | A6 | A8 | A9 | B3 | D1 | D4 | F4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BEA | bea-flagship-1-interactive-data | fail | fail | pass | fail | fail | fail | pass | fail | fail | fail |
| BEA | bea-flagship-2-news-releases | fail | fail | pass | fail | fail | fail | pass | fail | fail | fail |
| BJS | bjs-flagship-1-data-by-topic | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| BJS | bjs-flagship-2-death-in-custody-reporting-act | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| BLS | flagship:www.bls.gov/cpi/ | error | error | error | error | error | error | error | error | error | error |
| BTS | flagship:www.bts.gov/topics/national-transportation-statistics | error | error | error | error | error | error | error | error | error | error |
| CENSUS | census-flagship-1-surveys-programs | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| CENSUS | census-flagship-2-american-community-survey-acs | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| DRSMSU | flagship:www.federalreserve.gov/econres/scfindex.htm | fail | fail | fail | pass | pass | fail | fail | fail | pass | fail |
| EIA | eia-flagship-1-open-data | error | fail | error | error | error | fail | error | fail | fail | fail |
| ERS | ers-flagship-1-ag-and-food-statistics-charting-the-essentials | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| ERS | ers-flagship-2-agricultural-baseline-database | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| NAHMSAPHIS | flagship:www.aphis.usda.gov/aphis/ourfocus/animalhealth/monitoring-and-surveillance/nahms | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| NASS | nass-flagship-1-data-statistics | fail | fail | error | fail | fail | fail | fail | fail | fail | fail |
| NASS | nass-flagship-2-livestock-county-estimates | fail | fail | error | fail | fail | fail | fail | fail | fail | fail |
| NCES | flagship:nces.ed.gov/programs/digest/ | fail | fail | pass | fail | fail | fail | fail | fail | fail | fail |
| NCHS | nchs-flagship-1-data-briefs | fail | fail | error | fail | fail | fail | fail | fail | fail | fail |
| NCHS | nchs-flagship-2-early-releases-of-selected-estimates-from-the-nhis | fail | fail | pass | fail | fail | fail | fail | fail | fail | fail |
| NCSES | ncses-flagship-1-annual-business-survey-2024-data-year-2023 | fail | fail | fail | fail | fail | fail | pass | fail | fail | fail |
| ORES | flagship:www.ssa.gov/policy/docs/statcomps/supplement/ | error | error | error | error | error | error | error | error | error | error |
| SAMHSACBHS | flagship:www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health | fail | fail | fail | fail | fail | fail | fail | fail | error | fail |
| SOI | soi-flagship-1-individual-tax-statistics | fail | fail | error | fail | fail | fail | fail | fail | fail | fail |
| SOI | soi-flagship-2-business-tax-statistics | fail | fail | error | fail | fail | fail | fail | fail | fail | fail |

Across the 23 declared
surfaces, 5 of the
10 product checks return not a single pass.
None of these is present on any declared flagship surface measured in this cycle: the product
offered as structured data rather than as a document, a documented API with its auth model and
its rate limits, a machine-first entry point an agent could address, a machine-readable
licence, or a changelog per release.

The others are not at zero and are close to it. A bulk download of the whole product is linked
from 4 of
14 surfaces, the only check on
this page with a pass rate a reader would notice.
3 of
19 serve their substantive content
without requiring a browser to execute code. Structured markup describing the data, a
resolvable pointer to the current vintage and an entry in a public inventory are present on
1 of
19,
1 of
19 and
1 of
19 surfaces, and the matrix above
shows all three on the same row.

A zero at this denominator is not proof of universal absence, and the report will not let it be
read as one. With 0 passes in
19 surfaces, the upper bound of
the ninety-five percent score interval is
0.168179, which is the number a
reader should carry rather than the zero. Hanley and Lippman-Hand give the same magnitude by
their rule of thumb for zero events. The bound quoted here is the score interval, computed once
and registered rather than worked out in a sentence. The correct statement is that the true
rate is unlikely to exceed that bound, not that it is nothing.

The interval is still wide, and the declaration list is no longer what makes it so. It is wide
because one product is one surface and the frame holds
19 observable ones on this check,
4 more having answered with something
this scanner could not read. A denominator that small is what a report of a system this size
gets, and saying so is cheaper than pretending the bound is tighter.

## What the matrix cannot see

**Pages as a browser renders them.** Every check here reads what the server sends. A site that
assembles its content in the reader's browser looks empty to this scanner, and to any client
that does not run code. That is a real finding about machine access and a poor description of
what a person sees.

**Whether any machine actually uses the data.** Nothing here observes use. Access and uptake
are different questions, and only the first is measured.

**Anything about the three bodies that refused.** Their cells are `error` and will stay that
way under this method. No rate in this report includes them, and no reader should infer that
their absence from a numerator means anything about their products.

**Most of what "AI-ready" is taken to mean.** The product section now covers every body in
the frame, so the limit is no longer who is measured but what a check on a public surface can
reach. Two published definitions say how much. NOAA's own order defines AI-ready data in
5 components, and this instrument measures
3 of them exactly —
discoverable, machine-readable and machine-understandable, and access methods. Documentation it
measures in part and quality not at all: the definition's word is *sufficient*, a judgement
about the data against a use, and no check here opens the data. ESIP's AI-ready checklist has
58 assessable items and
9 of them are measured exactly here, most of
those under data access. Neither gap is a hole in the framework, which names indicators
for both; it is the distance between reading a surface and reading a dataset.

**The scanner's own reach.** The cycle contacted more netlocs than the target list names,
which bounds what "the frame" means. Two bodies declare their sitemap on a neighbouring
hostname and the scanner followed the declaration, which is what the discovery check is for. A
closed contact list and a discovery check that reads what the host actually says cannot both
hold; this cycle took the second and is reporting the choice rather than having made it in
advance. One consequence is on the log: those requests went out without first reading the
neighbouring host's own `robots.txt`, which this scanner's manners require. That is a defect in
the collector rather than a finding about anyone, it is still open in this cycle, and it is
queued.

The same declarations could have been declined instead, so the count of discovery failures
attributable to a declaration the scanner refused to follow is registered at
0 for this cycle. That is zero, and it
is registered rather than omitted: a caveat that is absent and a caveat measured to be empty
read alike in prose and are not the same claim.

**One failure this instrument cannot yet name.** Exactly
1 observation in the cycle carries an error
class of `unknown`: the map of failures does not have a name for what happened. It is counted
and reported rather than folded into a neighbouring class, because an aggregate is only worth
having if nothing was quietly swept into it.

## What moved since the previous cycle, and what moved it

The frame moved and the instrument held still. The previous cycle is this one's predecessor
re-judged under the same rules, so no row on the figure below is marked as a rule change and
every difference on it is the hosts or the frame. What changed between them is the frame: the
bodies that had declared no product now have one, and the product page of this report is about
23 declared surfaces where the
previous one was about a minority of them.

![Pass rate per check, previous cycle beside this one](assessment/harness/scan/figures/scan_2026-09-10_rj2/cycle_over_cycle.svg)

The figure draws no line and no arrow between the two points. A difference between two
measurements is not a direction of travel, and two cycles taken a day apart on federal
publication schedules are not a rate of change. A check with no applicable denominator in a
cycle is left blank rather than plotted at zero, because not measured is a reason and not a
zero.

Both cycles here are re-judgements. The measurements they rest on were taken on their own days
and are untouched; what has moved twice is the rule that reads them, and each time in the same
direction. A verdict about a product used to be allowed to rest on a probe the collector never
made — a connection closed mid-request, a page a `robots.txt` forbade — and three successive
corrections turned each of those into `error`. That is why the `error` counts in this report are
larger than a naive reading of an earlier cycle would suggest, and why they should be.

**The last of those corrections cost this report its strongest product number, and that is the
correction working.** Under the previous judgement of this same cycle, the bulk-download check
was answered over
19 declared flagship surfaces; it
is now answered over 14. The
surfaces that left are ones whose whole-product download the scanner was forbidden to look for,
and which had been counted as products that offer none. Nothing about those products changed
and nothing was re-fetched. The upper bound of the ninety-five percent interval on the rate rose
from 0.433343 to
0.546491: a smaller denominator is a
weaker claim, and an instrument that stops scoring what it was not allowed to see has to say
less, not more.

## What this cannot answer, and what would

**Why three bodies refuse an identified client.** A status code cannot distinguish a policy
from a default. Asking the operators, or reading their own access logs, is the only method that
separates them, and it is the highest-value open question in this report.

**Whether a third party sees what we see.** Every observation here comes from one vantage point
under one identity. A request from elsewhere, or under a common crawler's name, would establish
whether the refusals are about this client or about machines in general.

**What the products offer beyond one page each.** The declaration list is complete and this
cycle ran under it, so the open question is no longer coverage but depth: a flagship landing
page is one surface, and a body's data lives behind it. Whether these checks answer the same way
on a product's download, its API and its documentation pages is not known from a landing page,
and asking it needs a declared surface per product rather than per body.

**Whether the contact bound should be closed or open.** Following a sitemap declared on a
neighbouring host is either correct discovery or scope creep, and this cycle did it without
having decided. One resolution bounds such following to the frame and records an off-frame
declaration as an observation in its own right. The other states the bound as the frame plus
whatever the frame's own hosts declare.

## This report, measured by its own checks

The last row of the matrix is this report's own host, and it carries no verdicts. The report
has no host: it exists as a file in a repository, so it serves no `robots.txt`, declares no
machine layer and answers no deep links, and the intended home is GitHub Pages under this
repository. Scoring it now would mean inventing answers for a site that does not exist, so the
row stays empty until the instrument can be turned on this report's own output.

What the design calls for once it is published is on the record and is not vague. It wants a
machine-readable copy of the matrix beside the readable one, and both already exist as the
comma-separated and structured files accompanying this draft. It also wants a declared licence,
a catalogue entry, markup identifying the matrix as a dataset, and a `robots.txt` permitting an
identified client to read all of it. The instrument is meant to be turned on its own output.
Until it can be, this section says so rather than reporting a row nobody measured.

## Method appendix

<!-- lint: numerals-exempt -->

**Where the numbers live.** Every value in this report is a registered Result in the project's
artifact graph, quoted by name and resolved at build time. Nothing was typed. The build refuses
to write this file if a single reference fails to resolve, and a lint over the built text
refuses any numeral in prose that did not come through a reference. The matrices are rendered
from the cycle's own data rather than transcribed. Each cell in the machine-readable copies
names the Finding identity it came from, so any cell can be walked back to its observations,
and those to the retained response bodies.

**Client identity.** `ai-readiness-kg-scanner/0.2 (+https://github.com/brockwebb/ai-readiness-kg)`.
One identity, declared in parameters and read from there by everything that reports it. No host
was ever retried under another.

**Manners.** RFC 9309 obeyed: `robots.txt` read before fetching, disallowed paths not fetched
and recorded as a decision rather than as a failure. One request per second per host, one
worker, no forms, no logins, no query-string fuzzing. Retries only on 429 and 503.

**Verdicts.** `pass` and `fail` are measurements. `error` means the collector could not observe
and is excluded from every denominator; it is never a product failure. `n.a.` means there was
nothing of that kind to check. `not declared` means no product has been named.

**Intervals.** Wilson score intervals, computed by the project's own rollup module and
registered per check. Wilson (1927) for the interval. Brown, Cai and DasGupta (2001) and
Newcombe (1998) for why a score interval rather than a normal approximation at proportions near
zero or one. Hanley and Lippman-Hand (1983) for the rule of three at zero events.

**Controls.** Seven local fixture servers were scanned in this cycle alongside the real hosts.
One passes every check and one fails every check. One refuses an identified client and one
resets the connection. One answers normally but kills the invalid-route probe, and one answers
every GET while resetting every HEAD. The seventh declares its sitemap on a second hostname of
the same site, which is the case the discovery check meets on two real hosts; what it pins is an
order, that the sibling's own `robots.txt` is read before anything else is asked of it. Their
expected verdicts are derived from what each collector dispatches, not written by hand: a
hand-written expectation was wrong once.

**Rules that judged this cycle.**

| Check | Rule that judged this cycle |
|---|---|
| A1 | RULE-A1-v4 |
| A10 | RULE-A10-v3 |
| A11-declared | RULE-A11-declared-v2 |
| A12 | RULE-A12-v2 |
| A2 | RULE-A2-v3 |
| A3 | RULE-A3-v6 |
| A4 | RULE-A4-v1 |
| A5 | RULE-A5-v2 |
| A6 | RULE-A6-v2 |
| A8 | RULE-A8-v4 |
| A9 | RULE-A9-v1 |
| B3 | RULE-B3-v3 |
| D1 | RULE-D1-v3 |
| D4 | RULE-D4-v2 |
| F4 | RULE-F4-v3 |
| G1-D | RULE-G1-D-v1 |

**Requests issued, per netloc.**

| Netloc | Requests |
|---|---|
| `apps.bea.gov` | 21 |
| `bjs.ojp.gov` | 183 |
| `catalog.data.gov` | 13 |
| `data.bls.gov` | 1 |
| `data.census.gov` | 5 |
| `data.gov` | 2 |
| `data.nist.gov` | 13 |
| `gis.cdc.gov` | 2 |
| `ir.eia.gov` | 2 |
| `nces.ed.gov` | 128 |
| `ncses.nsf.gov` | 184 |
| `open.gsa.gov` | 13 |
| `quickstats.nass.usda.gov` | 1 |
| `sa.www4.irs.gov` | 13 |
| `samhsa.gov` | 3 |
| `tools.bea.gov` | 5 |
| `tools.cdc.gov` | 3 |
| `wonder.cdc.gov` | 2 |
| `www.aphis.usda.gov` | 121 |
| `www.bea.gov` | 207 |
| `www.bls.gov` | 73 |
| `www.bts.gov` | 71 |
| `www.cdc.gov` | 213 |
| `www.census.gov` | 241 |
| `www.data.gov` | 15 |
| `www.eia.gov` | 140 |
| `www.ers.usda.gov` | 243 |
| `www.federalreserve.gov` | 123 |
| `www.gsa.gov` | 15 |
| `www.irs.gov` | 172 |
| `www.nass.usda.gov` | 243 |
| `www.nist.gov` | 15 |
| `www.samhsa.gov` | 124 |
| `www.ssa.gov` | 71 |
| `wwwn.cdc.gov` | 3 |
| **total** | **2684** |

**Files beside this report.** `scan_matrix_tierA_2026-09-10_rj2.csv` and `.json`, the
host-level matrix; `scan_matrix_tierC_2026-09-10_rj2.*`, the reference hosts;
`scan_matrix_product_2026-09-10_rj2.*`, the product matrix. Every row carries its Finding
identities.

**Provenance.** Cycle `scan_2026-09-10`, parameter hash
`4e0a92ba19ab769bb98b3a4a0c68640fbe465a04eaaec4aa6f2f0f41dc75c0df`, judged as
`scan_2026-09-10_rj2`: the same stored observations under the rules current on 2026-09-11, with
every superseded judgement still registered under its own name. The event log is the source of
truth; the graph and the matrices are projections of it and are rebuilt by replay. Design
decisions DD-059 (the frame and the tier separation), DD-060 (one client identity), DD-061
(control tables derived from collector dispatch) and DD-064 (forbidden to look is blindness,
outside the product is scope) govern what this report may say.

<!-- lint: numerals-enforced -->
