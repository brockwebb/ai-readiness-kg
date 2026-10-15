# SI readiness of federal statistical data: an executive summary

Prepared 15 October 2026.

SI readiness is how well an SI system, one that finds, reads and uses data on its own, can reach an agency's data, understand it, and use it correctly. People increasingly reach official statistics through such systems, so when those systems cannot find or understand federal data, the public is left with stale or second-hand numbers. SI readiness runs across data publishing, web practice, metadata standards and policy at once and moves fast, so no one person holds all of it, and we meet an SI problem with SI.

## What we built

This is a decision support system, not a site checker: it measures what a machine actually meets on an agency's site, rather than what the agency says about itself. It maps each result onto a readiness framework, built on the four qualities the data nonprofit USAFacts set out (that data be accessible, understandable, accurate and open) with three more added, and puts every result on one standard scale so agencies can be set side by side. It then says what to fix first for the best value, the cheap high-value fixes before the larger ones, where how much a fix is worth is a rated judgment under a stated rubric, not a measurement.

## Who can use it, and why its advice can be trusted

An executive, a site administrator, a data producer or anyone working in the data's life can ask it questions and get answers at their own level, so no one need be expert in every field it touches. The advice rests on a connected store of the research, standards and policy, which the system reads to give answers with their sources attached. When newer evidence replaces a source, the store keeps the old one as history but stops it shaping advice.

## Measured in three tiers, by who can run them

The checks fall into three tiers by who can run them: a public tier anyone can run with free, open tools; an agency-enabled tier that needs an agency to turn something on; and a paid-tool tier. The public tier matters most, because it is what any such system, and any member of the public, meets, not only the largest commercial crawlers. The grid on the next page runs the public tier across every agency, and three findings stand out below.

## What we found

This measurement covers all 16 federal statistical agencies. A plain, identified machine client is frequently refused before it can read anything, and much of what it looks for is not served at all. Resources that agencies do publish often cannot be reached by a machine that starts at the data page.

## One caution

Any single score can be gamed, so we design around what the public can actually reach: readiness is judged where real users and their tools meet the data.


```{=typst}
#pagebreak(weak: true)
#page(flipped: true, margin: (x: 1.1cm, y: 1.0cm))[
#align(center)[#text(size: 12pt, weight: "bold")[The public tier, agency by agency]]
#v(4pt)
#set text(size: 6pt)
#table(
  columns: (4.5cm,) + (1fr,)*13,
  align: (left + horizon,) + (center + horizon,)*13,
  stroke: 0.3pt + rgb("#bbbbbb"),
  inset: 2.1pt,
  table.header([*Agency*], [*Data offered in a machine format*], [*A documented machine interface*], [*A full dataset download*], [*Crawlers allowed to reach the data*], [*The data is listed for discovery*], [*Structured markup describes the data*], [*A machine readable release date*], [*A machine first entry point*], [*Data tools answer a machine*], [*Methodology in reachable structured text*], [*A machine readable licence*], [*Listed in a public inventory*], [*A machine readable change history*]),
  [Bureau of Economic Analysis (2 pages)], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Bureau of Justice Statistics (2 pages)], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Bureau of Labor Statistics], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Bureau of the Census (2 pages)], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Bureau of Transportation Statistics], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Division of Research and Statistics, Microeconomic Surveys Unit], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Economic Research Service (2 pages)], [#text(fill: rgb("#c77d0a"))[◐]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#c77d0a"))[◐]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Energy Information Administration], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [National Agricultural Statistics Service (2 pages)], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [National Animal Health Monitoring System, Animal and Plant Health Inspection Service], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [National Center for Education Statistics], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [National Center for Health Statistics (2 pages)], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#c77d0a"))[◐]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [National Center for Science and Engineering Statistics], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Office of Research, Evaluation, and Statistics], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Statistics of Income (2 pages)], [#text(fill: rgb("#c77d0a"))[◐]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#c77d0a"))[◐]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]],
  [Substance Abuse and Mental Health Services Administration, Center for Behavioral Health Statistics and Quality], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#1b5e9c"))[●]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]], [#text(fill: rgb("#b22222"))[○]]
)
#v(6pt)
#text(size: 7pt)[*The fix under each check.*]
#v(2pt)
#set text(size: 6.2pt)
#grid(columns: (1fr, 1fr), gutter: 9pt, row-gutter: 2.4pt,
  [*Data offered in a machine format.* Link a data file from the product page and serve it with its own media type.],
  [*A documented machine interface.* Expose the product through a machine interface and publish its description.],
  [*A full dataset download.* Link a bulk download of the product from the product page.],
  [*Crawlers allowed to reach the data.* Serve a robots.txt that permits the data paths for the crawlers you want to allow.],
  [*The data is listed for discovery.* List the product address in the discovery file that is already served.],
  [*Structured markup describes the data.* Type the product page's existing markup as a dataset.],
  [*A machine readable release date.* Publish a release date for the product.],
  [*A machine first entry point.* Publish a machine-first entry point for the product.],
  [*Data tools answer a machine.* Return a real status for routes that do not exist.],
  [*Methodology in reachable structured text.* Link the methodology from the product page.],
  [*A machine readable licence.* Publish a machine-readable licence for the product.],
  [*Listed in a public inventory.* Add the product to the public data inventory already published.],
  [*A machine readable change history.* Publish a version history for the product.],
)
#v(6pt)
#text(size: 6.3pt)[*Key.* #text(fill: rgb("#1b5e9c"))[●] pass: every data page meets the check; #text(fill: rgb("#c77d0a"))[◐] partial: some data pages meet the check, some do not; #text(fill: rgb("#b22222"))[○] fail: no data page meets the check.]
#v(3pt)
#text(size: 6pt, style: "italic")[A check is pass where every one of an agency's data pages meets it, fail where none do, and partial where some do and some do not; a page that returned an access denial, an unconfirmable absence or a server error is counted as not meeting the check, and an agency with one data page can only pass or fail. The fix under a check is the action for the failing outcome the most agencies hit on that check across this measurement. Measured across all sixteen federal statistical agencies in October 2026.]
]
```

```{=typst}
#pagebreak()
```

## Sources

1. Standards for Excellent Data Products: Detailed User Guide (Federal Data Excellence). USAFacts, Partnership for Public Service, 2026. <https://media.usafacts.org/m/260cbbd653fb33ec/original/Detailed-User-Guide-Federal-Data-Excellence-Standards.pdf>
2. Generative Artificial Intelligence and Open Data: Guidelines and Best Practices. U.S. Department of Commerce Data Governance Board, AI and Open Government Data Assets Working Group, 2025. <https://www.commerce.gov/news/blog/2025/01/generative-artificial-intelligence-and-open-data-guidelines-and-best-practices>
3. NAO 216-128: Artificial Intelligence in NOAA. National Oceanic and Atmospheric Administration, 2026. <https://www.noaa.gov/sites/default/files/2026-04/NAO_216-128.pdf>
4. AI-Readiness for Official Data and Statistics (UN Statistical Commission side event). UN Statistics Division, 2026. <https://unstats.un.org/UNSDWebsite/statcom/session_57/side-events/Friday_Seminar_2026_AI_Readable_Data_Concept_Note.pdf>
5. From open data to AI-ready data: Building the foundations for responsible AI. World Bank, 2025. <https://blogs.worldbank.org/en/opendata/from-open-data-to-ai-ready-data--building-the-foundations-for-re>
6. RFC 9727: api-catalog: A Well-Known URI and Link Relation to Help Discovery of APIs. K. Smith (IETF), 2025. <https://www.rfc-editor.org/rfc/rfc9727.txt>
7. DCAT-US Schema v1.1 (Project Open Data Metadata Schema) - resources.data.gov. U.S. General Services Administration / Data.gov, 2026. <https://resources.data.gov/resources/dcat-us/>
8. schema.org: WebAPI. Schema.org Community Group, n.d. <https://schema.org/WebAPI>
9. RFC 8288: Web Linking. M. Nottingham, 2017. <https://www.rfc-editor.org/rfc/rfc8288>

Measured across all 16 federal statistical agencies in September and October 2026. Every mark in the grid traces to a cell of the published matrices for the cycle of record; the detailed report and the knowledge graph hold the evidence behind each one.
