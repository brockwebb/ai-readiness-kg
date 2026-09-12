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

<!-- include: rules_by_leg -->

**Requests issued, per netloc.**

<!-- include: requests_per_netloc -->

**Sources per check.**

<!-- include: sources_per_check -->

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
