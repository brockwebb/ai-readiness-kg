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

<!-- include: parent_host -->

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

<!-- include: rules_by_leg -->

**Requests issued, per netloc.** Summed over the two collections the snapshot rests on: the
first cycle, which measured every check, and the recollection, which measured the twelve checks
listed in the frame section.

<!-- include: requests_per_netloc -->

**Sources per check.**

<!-- include: sources_per_check -->

**Files beside this report.** `scan_matrix_tierA_2026-10-06_composite_c.csv` and `.json`, the
host-level matrix; `scan_matrix_tierC_2026-10-06_composite_c.*`, the reference hosts;
`scan_matrix_product_2026-10-06_composite_c.*`, the product matrix. Every row carries its Finding
identities, and each JSON file names the two cycles under `composed_of`.

**Provenance.** A declared composite, `scan_2026-10-06_composite_c`
(`state/scan_2026-10-06_composite_c.json`, `composed_of`). The host checks and every product
check but twelve are cycle `scan_2026-09-10`, parameter hash
`4e0a92ba19ab769bb98b3a4a0c68640fbe465a04eaaec4aa6f2f0f41dc75c0df`, judged as
`scan_2026-09-10_rj5`: the same stored observations under the rules current on 2026-10-06. The
twelve (`A1`, `A2`, `A3`, `A9`, `B1`, `B3`, `B4`, `D1`, `D3`, `D4`, `F4`, `G4`) are cycle
`scan_2026-10-06_recollect`, parameter hash
`2e56a8815bc22a2708f153978a8231ccfa1647027f85f27c5979beecfa1b50e9`, collected on 2026-10-06 over
the API, terms, changelog and inventory locations each body declares (`targets.yaml`
`declared_locations`, every entry citing the page it was read from), and judged as
`scan_2026-10-06_recollect_rj1` on 2026-10-10, parameter hash
`bcea2d92c74e53f8d9e364c7eee0ab143675ddba6574553c1473197d18d926aa`, under generation 15 of the
rules, which corrects three false passes on `A2`, `D1` and `A3`. The parameters moved between
the collection and the judgement only in blocks the twelve legs' rules do not read (the
`existence` and `discoverability` blocks, and the discoverability candidate's entry under the
link probe), so no other verdict moved. Every superseded judgement stays registered under its
own name. The event log is the source of
truth; the graph and the matrices are projections of it and are rebuilt by replay. Design
decisions DD-059 (the frame and the tier separation), DD-060 (one client identity), DD-061
(control tables derived from collector dispatch) and DD-064 (forbidden to look is blindness,
outside the product is scope) govern what this report may say.

<!-- lint: numerals-enforced -->
