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
{{result:scan_l0_home_flagship_disagreement_cells_2026-09-09:value}} cells across
{{result:scan_l0_home_flagship_disagreement_bodies_2026-09-09:value}} bodies, and a single
combined cell would have had to pick one without saying which.

<!-- include: matrix_tierA -->

### Reading it by column

**Serving `robots.txt`.** {{result:scan_l0_a4_pass_2026-09-09:value}} bodies of
{{result:scan_l0_a4_applicable_n_2026-09-09:value}} observable ones serve a `robots.txt` that
permits this client to read the page. The single failure serves no such file at all: not a
refusal, an absence, and a machine meeting it has to assume rather than read.
{{result:scan_l0_a4_error_2026-09-09:value}} bodies could not be observed on this check, and
the same {{result:scan_l0_a4_error_2026-09-09:value}} recur in every column below.

**Discovery.** {{result:scan_l0_a5_pass_2026-09-09:value}} of
{{result:scan_l0_a5_applicable_n_2026-09-09:value}} offer a discoverable index of what they
publish; {{result:scan_l0_a5_fail_2026-09-09:value}} do not. Discovery is the weakest
host-level result by a wide margin, and the consequence is direct: a machine that cannot
enumerate what a site publishes cannot tell what it has missed. Every sitemap any host
declared was followed, including ones declared on a neighbouring hostname, so none of these
failures is an artefact of the scanner declining to look.

**Deep links.** {{result:scan_l0_a10_pass_2026-09-09:value}} of
{{result:scan_l0_a10_applicable_n_2026-09-09:value}} answer a deliberately invalid URL
honestly. This is the best result on the page and it deserves less credit than it looks: it
measures the absence of a specific pathology rather than the presence of a capability.

**Declared machine layer.** {{result:scan_l0_a11_declared_pass_2026-09-09:value}} of
{{result:scan_l0_a11_declared_applicable_n_2026-09-09:value}} declare somewhere in their own
markup that a machine reader is expected. Declaring is not providing, and this check does not
follow the declaration to see whether anything answers at the other end.

**Declared against enforced.** The candidate check finds
{{result:scan_l0_a12_pass_2026-09-09:value}} bodies coherent and
{{result:scan_l0_a12_fail_2026-09-09:value}} incoherent, of
{{result:scan_l0_a12_applicable_n_2026-09-09:value}}. An incoherent host publishes a
`robots.txt` granting access and then declines to serve the client that obeys it. Three of them
are the bodies discussed in the next section, and the fourth publishes no `robots.txt` at
all.

**Uncertainty fields.** {{result:scan_l0_g1_d_pass_2026-09-09:value}} bodies of
{{result:scan_l0_g1_d_applicable_n_2026-09-09:value}} expose the fields that make an estimate
interpretable at the host level. The upper bound of the ninety-five percent interval on that
rate is {{result:scan_leg_rate_g1_d_upper95_2026-09-09:value}} at this denominator, which is
the honest way to say that a zero here is not proof of universal absence. It is measured on
the body's own front page and not on a data product, which flatters nobody and is a limit of
the host-level view rather than a finding about statistical practice.

### The reference hosts

<!-- include: matrix_tierC -->

All {{result:scan_a12_tierC_pass_2026-09-09:value}} reference hosts serve `robots.txt`, declare
a machine layer, answer deep links honestly and are coherent between declaration and
enforcement. All three fail discovery. All three also fail the uncertainty check, which for a
catalogue is the expected and uninteresting answer: it carries no estimates, so it has no
uncertainty fields to expose. They appear here for contrast and in no rate above.
