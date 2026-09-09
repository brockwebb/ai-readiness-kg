# AI readiness of the federal statistical system: host-level findings

**Draft. {{result:fss_agencies_tier_a:value}} recognized bodies and three reference
hosts, one cycle, one client identity.**
Written from `cc_tasks/2026-09-09_report_draft.md` against the graph as it stood on
2026-09-09. Every number below is a registered Result quoted by name; nothing is typed into
the prose.

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
{{result:fss_scan_surfaces_2026-09:value}} declared surfaces across
{{result:fss_scan_netlocs_2026-09:value}} netlocs. Netlocs exceed bodies because each reference
host declares a machine entry point on its own hostname. Every surface is declared, by the
roster or by the operator, and no rule selects one. Three selection rules were built for this
frame and all three failed; the record of why is in the design decisions.

## The client, and what it did

One identified client, one request per second per host, `robots.txt` obeyed, no forms, no
logins, no query-string fuzzing. The user agent names the project and links to its source. The
scanner has never retried a host under another identity, because a refusal is itself a
measurement and a disguise would destroy it.

The cycle issued {{result:scan_requests_total_2026-09-09:value}} requests across
{{result:fss_scan_netlocs_contacted_2026-09-09:value}} netlocs, which is more netlocs than the
target list names. The excess is not an accident and is discussed under what the matrix cannot
see. It produced {{result:scan_observations_2026-09-09:value}} observations and
{{result:scan_findings_2026-09-09:value}} findings, and every finding re-derives byte for byte
from its stored observations.

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
