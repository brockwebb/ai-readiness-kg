# DN-009: the deck is rejected; the brief becomes an evidence map, a one-page summary, a brief, and a report

**Date:** 2026-10-02
**Status:** operator decisions 2026-10-02, recorded by the Desktop session
**Supersedes:** DN-008 §1.2 (the chaptered deck as destination)

## 1. What happened

DN-008 set the destination as one chaptered deck. Five CC tasks built it (`92421acb`, `bffd0ed2`, `97b58374`, `3afb7840`, `d7631a51`; about 23M tokens): a 77-slide brief, a 219-slide appendix, a ten-slide authored case with the paper in the notes, and three gates that check every numeral, quotation and criterion label against the pack. The operator read it on 2026-10-02 and could not extract a story from it. His verdict stands: the deck is the record paginated, the notes carry a paper the slides fragment, and there is no picture of what was built relative to USAFacts or of what the tests found.

Causes, in order: the deck executed DN-008 literally instead of questioning the medium; the authoring discipline (no sentence not in a pack file) optimized for traceability and forbade synthesis; no one opened the output as a reader. The gates were right to exist and were insufficient: nothing checked whether a person could follow it.

The pack (`docs/brief/`, 61 generated files plus the demo capture) is unaffected and remains the fact base. `docs/deck/` is retained until the report exists and is then removed. The three gates transfer to the paper pattern.

## 2. Decisions

1. **Destination.** Four documents, in this order of production: (a) an evidence map; (b) a one-page executive summary (one figure, one table, a handful of sentences, one ask); (c) a brief of four to six pages that carries the operator's full argument; (d) the long report in sections on the paper pattern, with an information map. The summary and brief are drafted only after the evidence map exists. The operator dictates the summary's contents; Desktop does not author it before that.

2. **Evidence map first.** Every claim the summary or brief will make is written down as a claim with its evidence before any prose is drafted: established by prior art (cited), established by the record (finding, result or document id with locator), needs measurement, or unsupported. The map lives at `docs/evidence/claims.yaml`, is generated or validated by script, and is the input to the information map of the report. It is also the shape the claims take when they are later ingested into the graph as artifacts with evidence edges; that ingestion is a follow-on, not this.

3. **No ROI language.** Page H's position holds: equal weights, no weighting asserted, every rank rests on one leg. The summary says "the cheapest actions and the bound on what each moves under equal weights," and says in one clause why nothing stronger is claimed. Value, impact and ROI wording requires a weighting the project has not adopted; adopting one is a design decision with its own note.

4. **Terminology.** The operator reports an executive order of 2026-09-29 renaming AI to SI in federal usage. If confirmed by citation, the summary and brief use the EO's term once with the citation and a footnote that the record says AI throughout. The record, rules, pack and generated artifacts are not renamed.

5. **The public-client claim.** The harness ran as an unauthenticated public client; sentences about public access say that the harness ran, not the operator. "Blocked" is used only for findings that are access denials (status codes, robots.txt disallows, bot walls), counted on the cycle of record; absence from a catalog is not blocked.

6. **The boundary of what was measured.** The summary states the partition of unmeasured indicators by what blocks them: doable from outside with open tooling, needs agency cooperation, needs money, needs a standard that does not exist. Anything in the first class is measured before the summary is drafted.

7. **Reader gate, standing.** Every output task from here (figure, summary, brief, report section) ends with a fresh-context read: a subagent that has not seen the work reads the output as a federal executive would and writes back the story in five sentences and the one action it would take. If it cannot, the task fails before the output reaches the operator. The RESULT quotes the five sentences.

8. **Prior art before claims.** Each claim in the map is searched first in the corpus (264 admitted documents, through the MCP) and then on the web. The summary cites nothing from memory. Where the point is already established (FAIR, generative engine optimization, the Evidence Act's data.json requirement, Longpre et al. on crawler consent), the summary says so and positions the work as applying it, not inventing it.

## 3. Tasks created in this session

Three CC tasks, serial: evidence queries against the record; prior-art search for the claim set; figures (USAFacts-to-framework relation, high-level architecture, pass/fail table). Ids and order are in the handoff. Each produces part of the evidence map; the summary is drafted in the next thread after all three close.

## 4. Open defect that bit again

`21af86f8` (a Desktop-written design note has no commit path and stalls the dispatcher) applies to this note. The operator commits it by hand before the first task can launch.
