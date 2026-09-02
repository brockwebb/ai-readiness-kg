# Assessment protocol

The live, merged assessment design of this framework. It reconciles the June 2026
ai-readiness-fss work, now imported verbatim under `assessment/` as record, with the September
product-level instrument in `usafacts_operationalization_skeleton.md`. Where the two differ,
this file governs. The June documents are not edited; they are the record of how the design got
here, and this file is what the framework actually runs.

Status: v1, 2026-09-01, task `cc_tasks/2026-09-01_assessment_consolidation.md`.

## 1. Purpose and unit of analysis

The design is two-level, and the two levels were built in different months for different
reasons. The data product is the measurement unit: one product yields a scored profile, which
is a dimension vector plus the evidence behind each score plus a gap list. Products aggregate
to an agency-level dimension vector, and agency vectors are read within peer cohorts.

That reconciles the June design, which was agency-level from the start because its question was
about the federal statistical system, with the September pilot, which is product-level because
its question is whether a specific data product can be consumed by a machine. Neither replaces
the other. The product is where evidence is collected and where remediation happens; the agency
is where the picture becomes actionable for policy. An agency vector is never presented as a
naked cross-agency ranking, for the reason the June rubric gives: aggregation without fairness
stratification converts a diagnostic into a scorecard with teeth.

## 2. Orientation first

Discoverability and retrievability are the first-order construct. An agent arriving cold at an
agency's public surface must be able to establish what exists, what it means, how to obtain it,
and what may be done with it. Everything else in the instrument depends on that orientation
succeeding, because an interpretability property nobody can reach is not a property of a system
under measurement.

The established discovery stack is the core-scored mechanism set: the robots exclusion protocol
of RFC 9309, the sitemaps protocol, well-known URIs under RFC 8615, schema.org Dataset and
DataCatalog markup, DCAT and data.json catalogs, HTTP content negotiation, and persistent
identifiers. These are scored because they are what machines demonstrably use today, not
because they are old.

This replaces the June Part B framing, which named the access axis by its emerging mechanisms.
Naming an axis after three specific products dates the construct to the month it was written.
The rule that survives is the one underneath: every mechanism, established or emerging, is a
hypothesis about how machines actually orient themselves. The evidence that admits a mechanism
to the core set, or retires it from that set, is observed machine behavior, meaning crawler and
edge logs, D0-class probe results, and citation telemetry. Vintage and fashion are not
evidence in either direction. Under that rule llms.txt and MCP or WebMCP-class endpoints are
dated frontier candidates, admitted on evidence of agent use rather than on novelty, and equally
liable to retirement if the evidence does not arrive.

## 3. Scoring model

Carried from June unchanged. Each probe returns pass, partial, or fail, scored 2, 1, or 0.
Finer scales are refused deliberately because they invite interpretation theater without adding
resolution the evidence can support.

Scores are reported per dimension as a vector. There is no composite until an intended use is
decided, since a composite embeds a weighting that only a stated purpose can justify. Every
probe emits its evidence, meaning the actual response or artifact retrieved, so a score is
auditable rather than asserted. No self-attested input is ever a scored input; if a human types
it, it is not a benchmark result.

## 4. Core and frontier, with as_of dating

The firewall is not a split between dimensions. It is a split between established mechanisms,
which are core across all dimensions, and emerging access mechanisms, which report on a dated
frontier track and never enter the core score.

Applied to this framework, any A-group indicator that tests a post-corpus mechanism carries an
as_of date and reports on the frontier track, partitioned structurally before any aggregate is
computed. The June rubric's reason for this holds without modification: a standard that
postdates the policy corpus cannot be scored as core unreadiness, because the corpus that
defines readiness was written before the standard existed. Presence on the frontier track is an
asset; absence is not a deficiency. The as_of date travels in the emitted record rather than
living only in prose, so the dating survives contact with a spreadsheet.

## 5. Enumeration and scope

Two measurement universes exist per agency, the catalog surface and the web surface, and their
vectors are never summed. They answer different questions and a machine reaching one does not
thereby reach the other.

The measurement universe is public and public-mandated assets only. Protected data under Title
13, Title 26, CIPSEA restriction, or PII regimes is out of scope entirely: not flagged, not
stratified, not scored. This is stronger than excluding protected data after classifying it,
because classification would bring protected data into the frame in order to remove it, and
inviting that argument is the cost. The only surviving restriction concern is
restriction-discoverability, which asks whether a public catalog pointing at a restricted
dataset lets a machine learn that it is restricted and why. That is an interpretability
property of the public catalog, and it is scored as one.

## 6. Three evidence streams and their cross-checks

Three instruments carry three kinds of evidence. The machine diagnostic measures what a machine
can reach directly. The agency roll-up asks the person whose job is to know for organizational
facts, phrased as produce-the-artifact rather than rate-yourself. The practitioner survey asks
the people who touch the data about lived barriers a probe cannot see and an executive cannot
honestly report. The instruments are `assessment/fss_ai_readiness_assessment.md` and
`assessment/internal_survey_draft.md`.

Splitting by respondent is a data-quality decision rather than a convenience, because a long
survey selects against the busy practitioner whose answer matters most and manufactures
nonresponse bias by its length. Every response in all three streams carries the agency
identifier, and the data-area identifier where one exists. Without that join key the
cross-checks collapse into anecdote.

The cross-checks are the payload, and two contradictions are designed in rather than tolerated.
The roll-up reporting a documented AI-use policy against practitioners who have never seen one
is the phantom-policy signal, item R3 against item P6. A practitioner reporting what broke when
someone consumed an asset programmatically, against the retrieval probe's finding for that same
asset, is the lived-versus-measured gap, item P8 against the probe. The survey streams assess
organizational readiness, which is a separable module sitting beyond the product-centric
indicator groups rather than inside them.

## 7. Dimension naming

June's dimensions are referred to here as Discovery, Retrieval, Interpretability, and Trust,
spelled out, never as D1 through D4. The letter D is already load-bearing twice over: group D
means Open in the skeleton, and the D block means something else again in
census-web-concept-inventory. Reusing it a third time would produce exactly the kind of
collision that costs an afternoon to diagnose.

The mapping to indicator groups is: Discovery and Retrieval correspond to group A;
Interpretability corresponds to groups B and G; Trust corresponds to groups D and F. Groups C
and E, and indicator G1, have no June counterpart. They are the EVAL-tier measurement of June's
own Part A definition, which requires readiness without loss of statistical integrity. June
states that requirement and does not probe it, and the September groups are what probing it
looks like.

## 8. Peer-cohort layer

Dormant until scores aggregate across agencies. The schema is
`assessment/covariate_clustering_schema.md`, whose function is to define peer cohorts so
agencies are compared within group rather than against the whole system. Covariates contextualize
a score and never adjust or excuse it, which is the distinction that keeps stratification honest.

## 9. Reference implementation

`assessment/harness/` is the public and AUTO-tier reference implementation, and new AUTO
indicators are specified as probes against its conventions rather than described in prose. It
has been run against a live Census product, so its conventions are tested rather than proposed.

Its known probe-depth gaps are open items, found by the D0-r2 run in
census-web-concept-inventory and listed here so nobody rediscovers them. Meta-robots directives
are not read. The sitemap is read from a fixed path rather than the path robots.txt declares.
Catalog presence is scored where coverage is the property that matters. There is no
declared-versus-enforced-versus-observed triad. The FSS Machine Diagnostic specification, stubbed
into the skeleton as indicators A10 and A11, is what these probes grow toward, and closing these
four gaps is what growing toward it means concretely.
