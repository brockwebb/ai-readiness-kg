# SI readiness of federal statistical data: an executive summary

Prepared 13 October 2026.

SI readiness is how well an SI system, working on its own, can find an agency's data, understand it, and use it correctly. It has many parts, so each is measured on its own, and each can sit at a different level. The field moves fast, so this work holds to the fundamentals that limit what SI systems can do with federal data today. A fuller definition, covering how the data was made, where it came from, its date, and its terms of use, is in the appendix.

## Why it matters

SI readiness is wide: it runs across how data is published, how the web is used, which metadata standards apply, what policy requires, and how SI systems behave, and no one person holds all of it. People increasingly reach official statistics through SI systems, so when those systems cannot find or understand federal data, the public is left with stale or second-hand numbers. We meet an SI problem with SI: these systems helped build the work, and they are how the public now reaches the data.

## What we built

This is a decision support system, not a site checker, and it works in three parts. It measures what a machine actually meets on an agency's site, rather than what the agency says about itself, and that measurement is the way in, not the point. It maps each result onto a readiness framework, built on the four qualities USAFacts set out, that data be accessible, understandable, accurate and open, with three more added, and puts every result on one standard scale, so agencies can be set side by side. It then says what to do, ordered by effort and by how much each fix would open up: the cheap, high-value fixes first, the larger ones planned, and the high-effort, low-value ones, and the merely temporary ones, set aside. How much a fix is worth is a rated judgment under a stated rubric, not a measurement.

## Who can use it, and why the advice can be trusted

An executive, someone working anywhere in the data's life, a site administrator or a data producer can all ask it questions, get answers pitched at their own level, and see where their part fits the whole, so no one needs to be expert in every field it touches. The advice rests on a knowledge graph of the research, standards and policy, which an SI system reads to give answers with their sources attached, rather than off the cuff. When a source is overtaken, the graph keeps it as history but stops it shaping advice, so the work can also explain why an approach was tried and dropped.

## Measured in three tiers, by who can run them

The checks fall into three tiers by who can run them: a public tier that anyone can run with free, open tools; a tier that needs an agency to turn something on, often free to do; and a tier that needs paid tools. The public tier matters most, because it is what any SI system, and any member of the public, faces, not only the largest commercial crawlers. Each tier connects to the framework, so an agency can see how far the public tier alone carries it, and what turning a setting on, or buying a tool, would add.

## What we found

All 16 federal statistical agencies are now on this measurement. The results below come from the public tier, and three stand out, each with a free action that would move it. A plain, identified machine client is frequently refused before it can read anything. Much of what such a client looks for is not served at all. And resources that agencies do publish often cannot be reached by a machine that starts at the data page, because nothing links to them.

## One caution

Any single score can be gamed, so we design around what the public can actually reach: readiness is judged where real users and their tools meet the data.


```{=typst}
#pagebreak()
```

## The results, and the free actions that move them

| What we looked at | What the machine met | A free action that moves it |
| --- | --- | --- |
| Reaching the data at all | 341 of 1,055 checks met an access denial, a 401, 403 or 429 reply, a robots rule, or a reset connection, and 177 passed. | Serve a plain, identified, robots-respecting client the pages it asks for. |
| Finding what is published | 415 of the 1,055 checks found nothing served where a machine looks for it. | Publish the missing piece, such as a machine-readable licence. |
| Reaching resources that do exist | Of 29 agency-and-object pairs where the object exists, a data interface, its terms, a change history or a data inventory, a machine that starts at the data page cannot reach 15; counted per page, 54 of 88 cannot be reached. | Link the object from the data page, or place it at the standard address a published standard defines. |
| One publisher in focus: the Census Bureau | 18 of 39 published rows fail, and two of the fixes the record names, a machine-readable licence and a revision class on every changelog entry, sit in a notional effort band of hours and carry no cost. | Publish a machine-readable licence, and carry a revision class on every changelog entry. |

Effort and cost are relative, notional estimates by type of fix, not a calendar or a budget.

```{=typst}
#pagebreak()
```

## The fuller definition

SI readiness is how well a system that finds, reads and uses data on its own can reach an agency's data, understand it, and use it correctly, judged where real users and the tools they now use meet the data. It has several parts, each measured on its own and each able to sit at a different level. The first is discovery: the data, and the ways into it, can be found without anyone being told where they are. The second is access: a plain, identified machine client is served. The third is interpretation: the data is machine-readable and machine-understandable, with contextual metadata in standard formats. The fourth is fitness for use: how the data was made, where it came from, its date, and its terms of use are stated. The framework keeps the four qualities USAFacts set out, that data be accessible, understandable, accurate and open, and adds three more.

The definition draws on the U.S. Department of Commerce guidance (machine-readable and machine-understandable, with contextual metadata in standard formats), NOAA NAO 216-128 and the World Bank (discoverable, and the ways in), the UN Statistical Commission (how the data was made, and its date), and USAFacts (the four qualities).

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

Measured across all 16 federal statistical agencies in September and October 2026. Every figure above traces to a registered result; the detailed report and the knowledge graph hold the evidence behind each one.
