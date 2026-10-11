# AI readiness of the federal statistical system: host-level findings

**Version.** Snapshot cycle `scan_2026-10-07_composite_d` · version `2026-10-07_composite_d` · released `2026-10-11`; the commit this build was read from is recorded in `data/index.json` beside it. This document is a VIEW of data published beside it: the matrices as JSON and CSV, the per-check source appendix, and every Result quoted below with its value, its state and the artifact that generated it. The site index links all of them. **Licence.** The report and the data it is a view of are `CC-BY-4.0` (`LICENSE-DATA`); the code that produced them is `MIT` (`LICENSE`). Documents under corpus/ are third-party works, retained as evidence under their own terms: neither licence in this repository applies to them. **Standing.** No later judgement of this cycle's evidence is on the event log: the snapshot is the current judgement of record.

**Draft. 16 recognized bodies and three reference
hosts, one cycle for the host checks and two more for the product checks, one client
identity.**
Written from `cc_tasks/2026-09-09_report_draft.md`, revised to the cycle of 2026-09-10
under `cc_tasks/2026-09-11_l0_report_cycle4_revision.md`, re-snapshotted under
`cc_tasks/2026-09-19_resnapshot_rj4.md`, again under
`cc_tasks/2026-10-06_absence_verdicts_rules.md`, and onto a recollection under
`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md`, re-judged under
`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md`, and measured again over
every seeded location under `cc_tasks/2026-10-07_seed_known_locations_verify.md`. The snapshot is
a declared composite, `scan_2026-10-07_composite_d`, of three cycles. The host checks, and every
product check not listed next, are cycle `scan_2026-09-10`, the first over the complete frame, as
re-judged in `scan_2026-09-10_rj5`. Three product checks, `A1`, `A3` and `B3`, are cycle
`scan_2026-10-06_recollect`, measured on 2026-10-06 over the places each body's own pages declare
and re-judged on 2026-10-10 in `scan_2026-10-06_recollect_rj1`. The checks that ask for a body's
API, its terms, its changelog and its inventory, `A2`, `D1`, `F4`, `D4`, `B1`, `B4`, `D3` and
`G4`, with the frontier check `A9`, are cycle `scan_2026-10-07_seeded`, measured on 2026-10-11
over every location recorded for the body: the places its own pages declare, and the places this
repository, the model that wrote the seed table, catalog.data.gov and api.data.gov name for it,
each verified by one request. Every rule makes an absence a `fail` only over a
complete search, and says `error`, naming what was not searched, everywhere else. Every number
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

The first cycle issued 2684 requests across
35 netlocs, which is more netlocs than the
target list names. The excess is not an accident and is discussed under what the matrix cannot
see. It produced 2718 observations. The recollection
issued 2074 requests under the same client
and produced 6512 observations, and the seeded
cycle issued 1078 and produced
1205. The snapshot
holds 1055 findings, and every finding re-derives
byte for byte from its stored observations. The requests and the observations are each measured
cycle's and carry its name; the findings are each judgement's, and the composite selects them
by check without judging anything again.

## The five checks

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

## The matrix

One row per body, one column per check, one cell per verdict. `pass` and `fail` are
measurements. `error` means this scanner could not observe the surface, which is a fact about
the scanner and its reception, never a fact about the product. The last column counts how many
of the probes issued against the body's own page the host answered with a refusal status.

The four surface-judged checks are read from each body's home page, and the coherence check
from its well-known set. Which surface a cell was measured on is recorded on every row of the
machine-readable copy beside this one. It matters: a `robots.txt` that permits the front door
can disallow a particular product, so a flagship page and a home page need not receive the same
answer. This cycle found that disagreement on
12 cells across
6 bodies, and a single
combined cell would have had to pick one without saying which.

| Agency | A4 | A5 | A10 | A11-declared | A12 | Refused of probed |
|---|---|---|---|---|---|---|
| BEA | pass | fail | pass | pass | pass | 1 of 135 |
| BJS | pass | fail | pass | pass | pass | 0 of 156 |
| BLS | error | error | error | error | fail | 40 of 46 |
| BTS | error | error | error | error | fail | 37 of 44 |
| CENSUS | pass | pass | pass | pass | pass | 7 of 171 |
| DRSMSU | fail | fail | pass | fail | fail | 0 of 270 |
| EIA | pass | pass | pass | pass | pass | 3 of 161 |
| ERS | pass | fail | pass | pass | pass | 1 of 117 |
| NAHMSAPHIS | pass | fail | pass | pass | pass | 1 of 205 |
| NASS | pass | fail | pass | pass | pass | 1 of 199 |
| NCES | pass | fail | pass | pass | pass | 1 of 86 |
| NCHS | pass | fail | fail | fail | pass | 2 of 46 |
| NCSES | pass | pass | pass | pass | pass | 0 of 100 |
| ORES | error | error | error | error | fail | 36 of 38 |
| SAMHSACBHS | pass | fail | pass | pass | pass | 3 of 931 |
| SOI | pass | fail | pass | pass | pass | 0 of 164 |
| *this report* | \- | \- | \- | \- | \- | no host yet; the instrument is turned on this report when it is published |

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
16. None of the incoherent verdicts is
the case the check is named for. That case is a declared layer that admits this client over an
enforced layer that refuses it, and no body was observed in it. Three of the four are the Bureau
of Labor Statistics, the Bureau of Transportation Statistics and the Social Security
Administration's research office. Their hosts refused the request for `/robots.txt` itself, so
their declared layer could not be observed at all. The next section takes them up. The fourth,
the Federal Reserve Board's Microeconomic Surveys Unit, serves no `robots.txt` and so declares
nothing for the enforced layer to agree or disagree with.

<!-- lint: numerals-exempt -->

**Uncertainty fields.** This column has been withdrawn. **G1-D** asks whether a published figure carries, beside it and in machine-readable form, the fields that make it interpretable — a measure of uncertainty, a suppression flag, a reliability marker. The construct stands; the level was wrong. A body's home page carries no estimate, so the check could not hold the property it measures there: across every body, every reference host and every cycle it returned 126 `fail` and 28 `error` on host-level surfaces and **not one** `pass`, while the same rule returned 104 `pass` on product surfaces in the same runs. A check that never passes on one kind of surface and passes 104 times on another is measuring which surface it was pointed at, not the publisher. It is withdrawn from the host-level instrument effective cycle 5 (this params_hash forward) (`DD-066`); the cycles that measured it keep every observation and every verdict on the append-only log, unchanged and un-re-judged, because it was not mis-scored — it was asked of the wrong surface. Where the property does live is a data product, and that is the January G1 pilot's instrument, not this one's.

<!-- lint: numerals-enforced -->

### The reference hosts

| Agency | A4 | A5 | A10 | A11-declared | A12 | Refused of probed |
|---|---|---|---|---|---|---|
| GSA | pass | fail | pass | pass | pass | 0 of 11 |
| NIST | pass | fail | pass | pass | pass | 0 of 11 |
| data.gov | pass | fail | pass | pass | pass | 0 of 12 |

All 3 reference hosts serve `robots.txt`, declare
a machine layer, answer deep links honestly and are coherent between declaration and
enforcement. All three fail discovery. They appear here for contrast and in no rate above.

## Three bodies will not serve a compliant machine

3 bodies of
16 decline to answer a client that identifies itself, says where to complain about
it, asks for no more than one page per second, and reads `robots.txt` first. They are the
Bureau of Labor Statistics, the Bureau of Transportation Statistics and the Social Security
Administration's research office. Each returns a refusal status on effectively every request,
`/robots.txt` included, so what these hosts declare to a machine has never been read. Their rows
above read `error` throughout, which is the correct
reading: this instrument did not find those sites wanting, it was not allowed to look.

The behaviour is neither a transient nor a sampling accident. It has now been recorded in
6 separate measurements,
taken on four different days under two different user-agent strings. The count survives a change in how this project names errors: the earliest
filed the refusal under a general client-error class, because the closed set of names had no
member for a refusal until later. The number of bodies refusing has not moved, standing at
3 on the first look and the same on
the most recent.

Two things follow, and only two. First, the coherence check fails on all three, and not
because a declaration and a behaviour were seen to disagree: no declaration was seen. Every read
of `/robots.txt` on these hosts, in every cycle, was answered with HTTP `403`, so the declared
layer is not observable. RFC 9309 §2.3.1.3 calls a `robots.txt` answered with a status in the
`400`–`499` range unavailable, and provides that then "the crawler MAY access any resources on
the server". The scanner was therefore permitted to go on, and the hosts refused the pages it
asked for as they had refused the file. A client meeting them cannot learn the policy it is
held to, because the one place the protocol puts that policy is refused as well. Second, no rate in
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

| Agency | Surface | A1 | A2 | A3 | A6 | A8 | A9 | B3 | D1 | D4 | F4 | B1 | B2 | B4 | B5 | D2 | D3 | G4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BEA | bea-flagship-1-interactive-data | error | error | error | fail | fail | error | pass | error | error | fail | error | fail | error | fail | fail | error | error |
| BEA | bea-flagship-2-news-releases | error | error | error | fail | fail | error | pass | error | error | fail | error | fail | error | fail | fail | error | error |
| BJS | bjs-flagship-1-data-by-topic | error | fail | error | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| BJS | bjs-flagship-2-death-in-custody-reporting-act | error | fail | error | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| BLS | flagship:www.bls.gov/cpi/ | error | error | error | error | error | error | error | error | error | error | error | error | error | error | error | error | error |
| BTS | flagship:www.bts.gov/topics/national-transportation-statistics | error | error | error | error | error | pass | error | error | error | error | error | error | error | error | error | error | error |
| CENSUS | census-flagship-1-surveys-programs | error | fail | error | fail | fail | pass | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| CENSUS | census-flagship-2-american-community-survey-acs | error | fail | error | fail | fail | pass | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| DRSMSU | flagship:www.federalreserve.gov/econres/scfindex.htm | pass | fail | pass | pass | pass | error | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| EIA | eia-flagship-1-open-data | error | error | error | error | error | error | error | fail | fail | fail | error | error | fail | error | fail | fail | fail |
| ERS | ers-flagship-1-ag-and-food-statistics-charting-the-essentials | pass | error | error | fail | fail | error | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| ERS | ers-flagship-2-agricultural-baseline-database | error | error | pass | fail | fail | error | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| NAHMSAPHIS | flagship:www.aphis.usda.gov/aphis/ourfocus/animalhealth/monitoring-and-surveillance/nahms | error | fail | pass | fail | fail | error | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| NASS | nass-flagship-1-data-statistics | error | error | error | fail | fail | error | fail | error | error | error | error | fail | error | fail | fail | error | error |
| NASS | nass-flagship-2-livestock-county-estimates | error | error | error | fail | fail | error | fail | error | error | error | error | fail | error | fail | fail | error | error |
| NCES | flagship:nces.ed.gov/programs/digest/ | error | fail | error | fail | fail | fail | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| NCHS | nchs-flagship-1-data-briefs | error | fail | error | fail | fail | pass | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| NCHS | nchs-flagship-2-early-releases-of-selected-estimates-from-the-nhis | error | fail | pass | fail | fail | pass | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| NCSES | ncses-flagship-1-annual-business-survey-2024-data-year-2023 | pass | fail | pass | fail | fail | error | pass | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| ORES | flagship:www.ssa.gov/policy/docs/statcomps/supplement/ | error | error | error | error | error | error | error | error | error | error | error | error | error | error | error | error | error |
| SAMHSACBHS | flagship:www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health | error | fail | error | fail | fail | error | fail | fail | error | fail | error | fail | error | fail | fail | error | error |
| SOI | soi-flagship-1-individual-tax-statistics | error | fail | error | fail | fail | error | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |
| SOI | soi-flagship-2-business-tax-statistics | pass | fail | pass | fail | fail | error | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail | fail |

Across the 23 declared
surfaces, the checks that ask for a body's API, its terms, its changelog and its inventory now read
every location recorded for the body: the places its own pages declare, and the places this
repository, the model that wrote the seed table, catalog.data.gov and api.data.gov name for it,
each verified by one request on 2026-10-11. They reach `fail` only when every recorded location
was read and every one of those sources was searched, and say `error`, naming what was not read,
everywhere else. A machine-readable licence (`D1`) has a verdict now and the verdict is `fail`,
on 16 surfaces, with no pass: where
the body's API terms page is recorded it was read whole, and it states its licence in free text
rather than as a recognised identifier; where no source records a terms page, the product page
carries no licence field either. 7
more could not be observed, or a source was not searched for them. A documented API with its auth
model and its rate limits (`A2`) fails on
13 of the
13 surfaces on which the
question could be answered: where an API is recorded
and served, what it serves at its base is not a description of the API, and where no source
records an API for the body there is none to describe. On
10 more the recorded API base refused
this client, by `robots.txt` or by status, and the check says `error`. Whether a machine starting
from the product page can reach the API, the terms, the changelog and the inventory at all is a
separate question, asked by a candidate check that enters no rate here and is reported apart
(`docs/research/2026-10-11_seeded_delta.md`).

The other three checks that had no verdict before the recollection have some, because the search
reaches the places the indicator names. Structured data rather than a document is served on
4 of the
4 surfaces on which the question could be
answered; on 19 more the product page links more of
its own site than the scanner's request bound probed, and the links it did not reach may hold
the data file. A machine-first entry point, a frontier check that enters no score, answers on
5 surfaces and is absent on
3 whose API base is recorded. No
surface has a machine-readable changelog: on
18 surfaces the search was complete,
and either the changelog recorded for the body is a page for a person rather than a feed, or no
source records one at all; on 5
more a recorded location could not be read or a source was not searched. Each `error` names what
was not searched.

11 of the
17 product checks were measured and return not a
single pass: variable-level metadata, concept definitions linked from the variables,
data-quality attributes published as metadata rather than prose, terms that address model
training and retrieval, published source lineage, an entry in a public inventory, the issuing
authority recorded in that entry, a machine-readable changelog, a documented API and a
machine-readable licence. The last check at zero is
asked of the body rather than of a surface: whether the same concept carries the same identifier
across a body's products, and no body answers it yes. Four of these read the product's own record
in a public inventory, and that record was found for no declared product. On
7 surfaces every inventory recorded
for the body was read, its own host's, its department's and its data.gov organization's, and none
names the product. On 16 more an inventory could not be read,
because the department's or the body's own host refused this client or failed to answer, and
the `error` names which. So the issuing authority and its programme, recorded as structured
metadata in the product's catalogue record, are present on
0 of the
7 surfaces whose search
was complete. The one product the earlier judgement found in an inventory, the
Survey of Consumer Finances, is still in the Board's catalogue; its record now carries its
landing page as an object instead of a URL, so no field the check reads names the product.

The other checks are not at zero. A bulk download of the whole product is linked from
6 of
6 surfaces on which the question
could be answered. On 17 more it could not,
because the links the scanner did not probe may hold the download. With structured data above,
these are the pass rates on this page a reader would notice, and in both the denominator is why
they should not be noticed for long. 3 of
19 serve their substantive content
without requiring a browser to execute code. Structured markup describing the data and a
resolvable pointer to the current vintage are present on
1 of
19 and
1 of
19 surfaces.

A low count at this denominator is not proof of universal absence, and the report will not let
it be read as one. Structured markup describing the data is present on
1 of
19 surfaces. The upper bound of the
ninety-five percent score interval on that rate is
0.246387, and that bound is the number
a reader should carry rather than the count. Every check at zero has its own registered bound
beside it, for the same reason. The bound quoted here is the score interval, computed once and
registered rather than worked out in a sentence. The correct statement is that the true rate is
unlikely to exceed that bound, not that it is what the count shows.

The interval is still wide, and the declaration list is no longer what makes it so. It is wide
because one product is one surface, and the frame holds
19 observable surfaces on this
check. 4 more answered with something
this scanner could not read. A denominator that small is what a report on a system this size
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

This time the evidence and the rules moved together, on the checks that ask for a body's API,
its terms, its changelog and its inventory. The figure below draws the snapshot beside the
judgement it replaces, `scan_2026-10-06_composite_c`, the composite published on 2026-10-10.
Eight checks are marked as a rule change (`A2`, `B1`, `B4`, `D1`, `D3`, `D4`, `F4` and `G4`):
each now reads only the locations recorded for the body, and says `fail` only when every one of
them was read and every named source was searched. On those eight and on `A9` the evidence is
new too: cycle `scan_2026-10-07_seeded`, collected on 2026-10-11 over every location seeded for
the body and verified by one request each. On every other check both points are the same
findings. A check with no applicable denominator on a side has no point there, because every
product surface is `error` on it.

![Pass rate per check, previous judgement beside this one](assessment/harness/scan/figures/scan_2026-10-07_composite_d/cycle_over_cycle.svg)

The figure draws no line and no arrow between the two points. A difference between two
measurements is not a direction of travel, and two collections days or weeks apart on federal
publication schedules are not a rate of change. A check with no applicable denominator in a
cycle is left blank rather than plotted at zero, because not measured is a reason and not a
zero.

The judgements before this one moved the rule that reads the evidence, and each time in the same
direction. A verdict about a product used to be allowed to rest on a probe the collector never
made: a connection closed mid-request, a page a `robots.txt` forbade. Three successive
corrections turned each of those into `error`. The fourth went further. An absence is a `fail`
only over a search that reached everything the check names: every link on the product page, the
agency's documented API, its department's inventory and data.gov's. Wherever the search stopped
short, at the scanner's own request bound or at a location nobody declared, the verdict is
`error`, and the `error` says which places were not searched. The recollection is the other half
of that correction. The places were declared, each read off a page the body or data.gov
publishes, and searched; a check now says `fail` where the whole declared search found nothing,
and still says `error` where a host refused to be searched. The seeded cycle completes that
search: it adds the locations that sources other than the body's own pages name for it (this
repository, the model that wrote the seed table, catalog.data.gov and api.data.gov), verifies
each by one request, and records which sources were searched for which object, so a `fail` now
stands on a search a stranger can repeat source by source.

**The bulk-download check shows both halves.** Under the first re-judgement of the first cycle it
was answered over 19 declared
flagship surfaces. The fourth correction cut that sharply: on some surfaces the scanner was
forbidden to look, and on the others the page's links ran past the request bound before the
download could be reached, and both kinds had been counted as products that offer none. The
recollection ranks a page's links by how much each looks like data before the bound applies, and
the question is now answered over
6. The upper bound of the
ninety-five percent interval on the rate went from
0.433343 under the first
re-judgement to 1 now.
A larger denominator is a stronger claim only because the search behind it reached further, and
an instrument that stops scoring what it did not look at has to earn every surface it adds back.

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

**Cells read from a parent organization's host.** Some statistical units publish on a host
whose root belongs to an organization above them, so that host's `robots.txt`, `/data.json` and
well-known files answer for that organization, and a verdict on them is not a finding about the
unit. The machine-readable matrices keep those cells, with their verdicts and Findings, and mark
them `parent_host` in each row's `marks`. The per-check rates in this report still count them,
because those rates describe hosts and surfaces. The project's scores and ranks, which this
report does not print, leave them out. The bodies, the cells and the roster's reason for each,
generated from the roster:

| Body | Host | Whose host | Cells marked `parent_host` on this cycle | Why the roster says so |
|---|---|---|---|---|
| DRSMSU | `www.federalreserve.gov` | Board of Governors of the Federal Reserve System | A4, A5, A11-declared, A12, D4, B1, B4, D2, D3, G4 | the frame's home surface for the body is `https://www.federalreserve.gov/econres/rsmecs-staff.htm`, a section of `www.federalreserve.gov` rather than its root |
| NAHMSAPHIS | `www.aphis.usda.gov` | Department of Agriculture | A4, A5, A11-declared, A12, D4, B1, B4, D2, D3, G4 | the frame's home surface for the body is `https://www.aphis.usda.gov/aphis/ourfocus/animalhealth/monitoring-and-surveillance/nahms`, a section of `www.aphis.usda.gov` rather than its root |
| NCHS | `www.cdc.gov` | Centers for Disease Control and Prevention | A4, A5, A11-declared, A12, D4 (2), B1 (2), B4 (2), D2 (2), D3 (2), G4 (2) | the cycle-1 roster row carries `host_shared_with: Centers for Disease Control and Prevention` (assessment/harness/scan/targets.yaml); the frame's home surface for the body is `https://www.cdc.gov/nchs/index.htm`, a section of `www.cdc.gov` rather than its root |
| ORES | `www.ssa.gov` | Social Security Administration | A4, A5, A11-declared, A12, D4, B1, B4, D2, D3, G4 | the .gov registry attributes `ssa.gov` to Social Security Administration, the roster's parent department, with no suborganization, and `www.ssa.gov` is that domain itself (state/fss_department_domains_2026-09.json) |
| SAMHSACBHS | `www.samhsa.gov` | Substance Abuse and Mental Health Services Administration | A4, A5, A11-declared, A12, D4, B1, B4, D2, D3, G4 | the frame's home surface for the body is `https://www.samhsa.gov/about-us/who-we-are/offices-centers/cbhsq`, a section of `www.samhsa.gov` rather than its root |
| SOI | `www.irs.gov` | Internal Revenue Service | A4, A5, A11-declared, A12, D4 (2), B1 (2), B4 (2), D2 (2), D3 (2), G4 (2) | the frame's home surface for the body is `https://www.irs.gov/statistics/soi-tax-stats-statistics-of-income`, a section of `www.irs.gov` rather than its root |

**Frontier checks.** The machine-first entry point check (A9) is a frontier mechanism, dated by
its indicator. It is on the product matrix with its verdicts and is marked `frontier`; a
frontier mechanism enters no score.

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
| A1 | RULE-A1-v5 |
| A10 | RULE-A10-v3 |
| A11-declared | RULE-A11-declared-v2 |
| A12 | RULE-A12-v3 |
| A13 | RULE-A13-v1 |
| A2 | RULE-A2-v6 |
| A3 | RULE-A3-v8 |
| A4 | RULE-A4-v1 |
| A5 | RULE-A5-v2 |
| A6 | RULE-A6-v2 |
| A8 | RULE-A8-v4 |
| A9 | RULE-A9-v2 |
| B1 | RULE-B1-v4 |
| B2 | RULE-B2-v1 |
| B3 | RULE-B3-v4 |
| B4 | RULE-B4-v3 |
| B5 | RULE-B5-v1 |
| D1 | RULE-D1-v6 |
| D2 | RULE-D2-v1 |
| D3 | RULE-D3-v3 |
| D4 | RULE-D4-v5 |
| F4 | RULE-F4-v5 |
| G1-D | RULE-G1-D-v1 |
| G4 | RULE-G4-v3 |

**Requests issued, per netloc.** Summed over the three collections the snapshot rests on: the
first cycle, which measured every check, the recollection, which measured twelve product checks,
and the seeded cycle, which measured ten of them again, as the frame section lists.

| Netloc | Requests |
|---|---|
| `api.bls.gov` | 1 |
| `api.census.gov` | 26 |
| `api.eia.gov` | 14 |
| `api.ers.usda.gov` | 1 |
| `api.ojp.gov` | 20 |
| `apps.bea.gov` | 39 |
| `bjs.ojp.gov` | 389 |
| `catalog.data.gov` | 107 |
| `data.bls.gov` | 2 |
| `data.bts.gov` | 11 |
| `data.cdc.gov` | 21 |
| `data.census.gov` | 11 |
| `data.gov` | 2 |
| `data.nist.gov` | 13 |
| `datatools.samhsa.gov` | 3 |
| `gis.cdc.gov` | 4 |
| `hhs.gov` | 12 |
| `ir.eia.gov` | 4 |
| `nces.ed.gov` | 270 |
| `ncses.nsf.gov` | 397 |
| `open.gsa.gov` | 13 |
| `quickstats.nass.usda.gov` | 3 |
| `sa.www4.irs.gov` | 17 |
| `samhsa.gov` | 3 |
| `tools.bea.gov` | 10 |
| `tools.cdc.gov` | 5 |
| `wonder.cdc.gov` | 4 |
| `www.aphis.usda.gov` | 255 |
| `www.bea.gov` | 434 |
| `www.bls.gov` | 165 |
| `www.bts.gov` | 155 |
| `www.cdc.gov` | 450 |
| `www.census.gov` | 519 |
| `www.commerce.gov` | 18 |
| `www.data.gov` | 15 |
| `www.dol.gov` | 6 |
| `www.ed.gov` | 6 |
| `www.eia.gov` | 321 |
| `www.energy.gov` | 8 |
| `www.ers.usda.gov` | 509 |
| `www.federalreserve.gov` | 257 |
| `www.gsa.gov` | 15 |
| `www.hhs.gov` | 10 |
| `www.irs.gov` | 370 |
| `www.justice.gov` | 8 |
| `www.nass.usda.gov` | 437 |
| `www.nist.gov` | 15 |
| `www.nsf.gov` | 8 |
| `www.samhsa.gov` | 259 |
| `www.ssa.gov` | 155 |
| `www.transportation.gov` | 3 |
| `www.treasury.gov` | 8 |
| `www.usda.gov` | 22 |
| `wwwn.cdc.gov` | 6 |
| **total** | **5836** |

**Sources per check.**

One row per check and admitted source: the check as the report names it, the framework indicator it measures, the source as the corpus manifest records it, its document id in the manifest, and the locator inside the source as the indicator's evidence cell states it. Generated from the graph; nothing in this table is typed.

| Check | Indicator | Source | doc_id | Locator |
|-----|--------------|----------------------------------------------|-----------------|------------------|
| A4 | A4 · Crawler/agent access | no admitted source |  |  |
| A5 | A5 · Discoverability surface | no admitted source |  |  |
| A10 | A10 · Application/data-tool machine surface | no admitted source |  |  |
| A11-declared | A11 · Effective crawler access (declared / enforced / observed) | no admitted source |  |  |
| A12 | A12 · Access policy coherence | no admitted source |  |  |
| G1-D | G1-D · Uncertainty legibility (two legs, scored as a vector) | no admitted source |  |  |
| A3 | A3 · Bulk access | no admitted source |  |  |
| A1 | A1 · Machine-readable formats | no admitted source |  |  |
| A2 | A2 · Programmatic access | no admitted source |  |  |
| A6 | A6 · Structured markup | no admitted source |  |  |
| A8 | A8 · Timeliness of surface | no admitted source |  |  |
| A9 | A9 · M2M agent surface | no admitted source |  |  |
| B3 | B3 · Methodology legibility | no admitted source |  |  |
| D1 | D1 · License clarity | no admitted source |  |  |
| D4 | D4 · No dark data | no admitted source |  |  |
| F4 | F4 · Change legibility | no admitted source |  |  |
| G4 | G4 · Authority metadata | no admitted source |  |  |

**Files beside this report.** `scan_matrix_tierA_2026-10-07_composite_d.csv` and `.json`, the
host-level matrix; `scan_matrix_tierC_2026-10-07_composite_d.*`, the reference hosts;
`scan_matrix_product_2026-10-07_composite_d.*`, the product matrix. Every row carries its Finding
identities, and each JSON file names its parts under `composed_of` and `composed_of_parts`.

**Provenance.** A declared composite over a composite, `scan_2026-10-07_composite_d`
(`state/scan_2026-10-07_composite_d.json`, `composed_of`, scheme 2). The host checks and every
product check but thirteen are cycle `scan_2026-09-10`, parameter hash
`4e0a92ba19ab769bb98b3a4a0c68640fbe465a04eaaec4aa6f2f0f41dc75c0df`, judged as
`scan_2026-09-10_rj5`: the same stored observations under the rules current on 2026-10-06.
`A1`, `A3` and `B3` are cycle `scan_2026-10-06_recollect`, parameter hash
`2e56a8815bc22a2708f153978a8231ccfa1647027f85f27c5979beecfa1b50e9`, collected on 2026-10-06 over
the locations each body's own pages declare, and judged as `scan_2026-10-06_recollect_rj1` on
2026-10-10, parameter hash `bcea2d92c74e53f8d9e364c7eee0ab143675ddba6574553c1473197d18d926aa`,
under generation 15 of the rules. The ten others (`A2`, `D1`, `F4`, `D4`, `B1`, `B4`, `D3`, `G4`,
the frontier check `A9` and the discoverability candidate `A13`) are cycle
`scan_2026-10-07_seeded`, parameter hash
`5166e78c756f8d736df02c667fcc4c1748ecfef3fbebf1df5124054e1fc22412`, collected on 2026-10-11 under
generation 16 over every location recorded for the body (`targets.yaml` `declared_locations`
scheme 2: each location read from the body's page or seeded from a named source, with the status
of its one verifying request), each product page read from the recollection rather than fetched
again. The parameters moved between the recollection and the seeded cycle only in the cycle's
name, the existence and discoverability blocks the generation-16 rules read, and the ceiling on
how much of a terms page the licence check keeps. Every superseded judgement stays registered under its
own name. The event log is the source of
truth; the graph and the matrices are projections of it and are rebuilt by replay. Design
decisions DD-059 (the frame and the tier separation), DD-060 (one client identity), DD-061
(control tables derived from collector dispatch) and DD-064 (forbidden to look is blindness,
outside the product is scope) govern what this report may say.

<!-- lint: numerals-enforced -->
