# AI readiness of the federal statistical system: host-level findings

**Draft. {{result:fss_agencies_tier_a:value}} recognized bodies and three reference
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
{{result:fss_agencies_tier_a:value}} bodies. They are taken from the Interagency Council on
Statistical Policy's own charter, which enumerates its membership under an explicit flag legend
rather than in prose. Recognition is a legal status conferred under CIPSEA 2018 (44 U.S.C.
3561, 3562), so the roster is a parse of an authoritative list and not a judgement about who
counts. The charter and the Council's public About page disagree about
{{result:fss_tier_a_source_disagreements:value}} body, the Social Security Administration's
research office. The charter marks it recognized and the About page does not, and the charter
was named the authority before either document was read.

Three further hosts appear in the measurement and in none of its rates: data.gov, NIST and GSA.
These are reference hosts. A federal catalog and two data portals are the nearest available
control for what a machine-facing government site looks like when someone has tried. They are
judged on the host-level checks only and enter no agency denominator, because placing a catalog
beside a statistical agency above that level compares two different kinds of thing.

Counting surfaces rather than bodies, the target list carries
{{result:fss_scan_surfaces_2026-09-10:value}} declared surfaces across
{{result:fss_scan_netlocs_2026-09:value}} netlocs. Netlocs exceed bodies because each reference
host declares a machine entry point on its own hostname. Every surface is declared, by the
roster or by the operator, and no rule selects one. Three selection rules were built for this
frame and all three failed; the record of why is in the design decisions.

## The client, and what it did

One identified client, one request per second per host, `robots.txt` obeyed, no forms, no
logins, no query-string fuzzing. The user agent names the project and links to its source. The
scanner has never retried a host under another identity, because a refusal is itself a
measurement and a disguise would destroy it.

The first cycle issued {{result:scan_requests_total_2026-09-10:value}} requests across
{{result:fss_scan_netlocs_contacted_2026-09-10:value}} netlocs, which is more netlocs than the
target list names. The excess is not an accident and is discussed under what the matrix cannot
see. It produced {{result:scan_observations_2026-09-10:value}} observations. The recollection
issued {{result:scan_requests_total_2026-10-06_recollect:value}} requests under the same client
and produced {{result:scan_observations_2026-10-06_recollect:value}} observations, and the seeded
cycle issued {{result:scan_requests_total_2026-10-07_seeded:value}} and produced
{{result:scan_observations_2026-10-07_seeded:value}}. The snapshot
holds {{result:scan_findings_2026-10-07_composite_d:value}} findings, and every finding re-derives
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
