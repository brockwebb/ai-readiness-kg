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

![Pass rate per check, previous judgement beside this one]({{figure:cycle_over_cycle_2026-10-07_composite_d:path}})

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
was answered over {{result:scan_l0_product_a3_applicable_n_2026-09-10_rj1:value}} declared
flagship surfaces. The fourth correction cut that sharply: on some surfaces the scanner was
forbidden to look, and on the others the page's links ran past the request bound before the
download could be reached, and both kinds had been counted as products that offer none. The
recollection ranks a page's links by how much each looks like data before the bound applies, and
the question is now answered over
{{result:scan_l0_product_a3_applicable_n_2026-10-07_composite_d:value}}. The upper bound of the
ninety-five percent interval on the rate went from
{{result:scan_l0_product_leg_rate_a3_upper95_2026-09-10_rj1:value}} under the first
re-judgement to {{result:scan_l0_product_leg_rate_a3_upper95_2026-10-07_composite_d:value}} now.
A larger denominator is a stronger claim only because the search behind it reached further, and
an instrument that stops scoring what it did not look at has to earn every surface it adds back.
