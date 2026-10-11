## What the products offer a machine

Everything above measures a host. This section measures products, and for the first time it
covers the whole frame. Every one of the {{result:fss_agencies_tier_a:value}} bodies now has a
flagship product declared for it —
{{result:scan_l0_declared_flagship_agencies_2026-10-07_composite_d:value}} agencies across
{{result:scan_l0_declared_flagship_surfaces_2026-10-07_composite_d:value}} declared surfaces — and
{{result:fss_agencies_pending_operator_declaration_2026-09-10:value}} bodies carry a host row
and nothing else.

{{result:fss_flagships_declared_2026-09-10:value}} of those flagships were declared for this
cycle, for the bodies that had none when the previous one ran, and each was verified
robots-first before it entered the frame.
{{result:fss_flagships_refused_at_declaration_2026-09-10:value}} of them were answered with a
refusal by the same hosts that refuse this client at every other door. They enter marked as
refused rather than dropped: restricting the instrument to the agencies that permit it would
make the frame a function of who answers. The rest came live in this cycle and are measured
below.

<!-- include: matrix_product -->

Across the {{result:scan_l0_declared_flagship_surfaces_2026-10-07_composite_d:value}} declared
surfaces, the checks that ask for a body's API, its terms, its changelog and its inventory now read
every location recorded for the body: the places its own pages declare, and the places this
repository, the model that wrote the seed table, catalog.data.gov and api.data.gov name for it,
each verified by one request on 2026-10-11. They reach `fail` only when every recorded location
was read and every one of those sources was searched, and say `error`, naming what was not read,
everywhere else. A machine-readable licence (`D1`) has a verdict now and the verdict is `fail`,
on {{result:scan_l0_product_d1_fail_2026-10-07_composite_d:value}} surfaces, with no pass: where
the body's API terms page is recorded it was read whole, and it states its licence in free text
rather than as a recognised identifier; where no source records a terms page, the product page
carries no licence field either. {{result:scan_l0_product_d1_error_2026-10-07_composite_d:value}}
more could not be observed, or a source was not searched for them. A documented API with its auth
model and its rate limits (`A2`) fails on
{{result:scan_l0_product_a2_fail_2026-10-07_composite_d:value}} surfaces: where an API is recorded
and served, what it serves at its base is not a description of the API, and where no source
records an API for the body there is none to describe. On
{{result:scan_l0_product_a2_error_2026-10-07_composite_d:value}} more the recorded API base refused
this client, by `robots.txt` or by status, and the check says `error`. Whether a machine starting
from the product page can reach the API, the terms, the changelog and the inventory at all is a
separate question, asked by a candidate check that enters no rate here and is reported apart
(`docs/research/2026-10-11_seeded_delta.md`).

The other three checks that had no verdict before the recollection have some, because the search
reaches the places the indicator names. Structured data rather than a document is served on
{{result:scan_l0_product_a1_pass_2026-10-07_composite_d:value}} of the
{{result:scan_l0_product_a1_applicable_n_2026-10-07_composite_d:value}} surfaces on which the question could be
answered; on {{result:scan_l0_product_a1_error_2026-10-07_composite_d:value}} more the product page links more of
its own site than the scanner's request bound probed, and the links it did not reach may hold
the data file. A machine-first entry point, a frontier check that enters no score, answers on
{{result:scan_l0_product_a9_pass_2026-10-07_composite_d:value}} surfaces and is absent on
{{result:scan_l0_product_a9_fail_2026-10-07_composite_d:value}} whose API base is recorded. No
surface has a machine-readable changelog: on
{{result:scan_l0_product_f4_fail_2026-10-07_composite_d:value}} surfaces the search was complete,
and either the changelog recorded for the body is a page for a person rather than a feed, or no
source records one at all; on {{result:scan_l0_product_f4_error_2026-10-07_composite_d:value}}
more a recorded location could not be read or a source was not searched. Each `error` names what
was not searched.

{{result:scan_l0_product_legs_at_zero_2026-10-07_composite_d:value}} of the
{{result:scan_l0_product_legs_2026-10-07_composite_d:value}} product checks were measured and return not a
single pass: variable-level metadata, concept definitions linked from the variables,
data-quality attributes published as metadata rather than prose, terms that address model
training and retrieval, published source lineage, an entry in a public inventory, the issuing
authority recorded in that entry, a machine-readable changelog, a documented API and a
machine-readable licence. The last check at zero is
asked of the body rather than of a surface: whether the same concept carries the same identifier
across a body's products, and no body answers it yes. Four of these read the product's own record
in a public inventory, and that record was found for no declared product. On
{{result:scan_l0_product_d4_fail_2026-10-07_composite_d:value}} surfaces every inventory recorded
for the body was read, its own host's, its department's and its data.gov organization's, and none
names the product. On {{result:scan_l0_product_d4_error_2026-10-07_composite_d:value}} more an inventory could not be read,
because the department's or the body's own host refused this client or failed to answer, and
the `error` names which. So the issuing authority and its programme, recorded as structured
metadata in the product's catalogue record, are present on
{{result:scan_l0_product_g4_pass_2026-10-07_composite_d:value}} of the
{{result:scan_l0_product_g4_applicable_n_2026-10-07_composite_d:value}} surfaces whose search
was complete. The one product the earlier judgement found in an inventory, the
Survey of Consumer Finances, is still in the Board's catalogue; its record now carries its
landing page as an object instead of a URL, so no field the check reads names the product.

The other checks are not at zero. A bulk download of the whole product is linked from
{{result:scan_l0_product_a3_pass_2026-10-07_composite_d:value}} of
{{result:scan_l0_product_a3_applicable_n_2026-10-07_composite_d:value}} surfaces on which the question
could be answered. On {{result:scan_l0_product_a3_error_2026-10-07_composite_d:value}} more it could not,
because the links the scanner did not probe may hold the download. With structured data above,
these are the pass rates on this page a reader would notice, and in both the denominator is why
they should not be noticed for long. {{result:scan_l0_product_b3_pass_2026-10-07_composite_d:value}} of
{{result:scan_l0_product_b3_applicable_n_2026-10-07_composite_d:value}} serve their substantive content
without requiring a browser to execute code. Structured markup describing the data and a
resolvable pointer to the current vintage are present on
{{result:scan_l0_product_a6_pass_2026-10-07_composite_d:value}} of
{{result:scan_l0_product_a6_applicable_n_2026-10-07_composite_d:value}} and
{{result:scan_l0_product_a8_pass_2026-10-07_composite_d:value}} of
{{result:scan_l0_product_a8_applicable_n_2026-10-07_composite_d:value}} surfaces.

A low count at this denominator is not proof of universal absence, and the report will not let
it be read as one. Structured markup describing the data is present on
{{result:scan_l0_product_a6_pass_2026-10-07_composite_d:value}} of
{{result:scan_l0_product_a6_applicable_n_2026-10-07_composite_d:value}} surfaces. The upper bound of the
ninety-five percent score interval on that rate is
{{result:scan_l0_product_leg_rate_a6_upper95_2026-10-07_composite_d:value}}, and that bound is the number
a reader should carry rather than the count. Every check at zero has its own registered bound
beside it, for the same reason. The bound quoted here is the score interval, computed once and
registered rather than worked out in a sentence. The correct statement is that the true rate is
unlikely to exceed that bound, not that it is what the count shows.

The interval is still wide, and the declaration list is no longer what makes it so. It is wide
because one product is one surface, and the frame holds
{{result:scan_l0_product_a6_applicable_n_2026-10-07_composite_d:value}} observable surfaces on this
check. {{result:scan_l0_product_a6_error_2026-10-07_composite_d:value}} more answered with something
this scanner could not read. A denominator that small is what a report on a system this size
gets, and saying so is cheaper than pretending the bound is tighter.
