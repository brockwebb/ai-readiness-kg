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

**Controls.** Six local fixture servers are scanned in every cycle alongside the real hosts.
One passes every check and one fails every check. One refuses an identified client and one
resets the connection. One answers normally but kills the invalid-route probe, and one answers
every GET while resetting every HEAD. Their expected verdicts are derived from what each
collector dispatches, not written by hand: a hand-written expectation was wrong once.

**Rules that judged this cycle.**

<!-- include: rules_by_leg -->

**Requests issued, per netloc.**

<!-- include: requests_per_netloc -->

**Files beside this report.** `scan_matrix_tierA_2026-09-09.csv` and `.json`, the host-level
matrix; `scan_matrix_tierC_2026-09-09.*`, the reference hosts; `scan_matrix_product_2026-09-09.*`,
the partial product matrix. Every row carries its Finding identities.

**Provenance.** Cycle `scan_2026-09-09`, parameter hash
`7ee55f512e8473e6d74ab8c0d089d694078baa8548b60f2b5f22fed66728d6a6`. The event log is the source
of truth; the graph and the matrices are projections of it and are rebuilt by replay. Design
decisions DD-059 (the frame and the tier separation), DD-060 (one client identity) and DD-061
(control tables derived from collector dispatch) govern what this report may say.

<!-- lint: numerals-enforced -->
