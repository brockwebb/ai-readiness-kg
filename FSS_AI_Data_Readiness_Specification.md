# FSS AI Data Readiness Specification

A method for assessing whether a Federal Statistical System agency's public data is ready to be found, retrieved, and correctly used by AI systems.

# 1. Introduction

Our task is to construct a method that helps the Federal Statistical System (FSS) assess the AI data readiness of the public data its agencies already publish. The motivation is the federal push to expand AI use across government (OMB M-25-21): before agencies can responsibly accelerate AI use of federal statistics, the data those systems consume has to be in a state a machine can actually use. A shared definition is the precondition for meaningful measurement — if reviewers do not agree on what AI data readiness means, any score against it is arbitrary. This specification therefore states the definition first, then builds the assessment to match it.

# 2. What AI data readiness means

Data is AI-ready when it is prepared so that AI systems, particularly large language models, can correctly access, interpret, and use it — its meaning, provenance, and quality signals travel with the data, not just the raw values.

This definition is adopted and extended from federal sources: America's DataHub Request for Solutions Topic MLMU-25, FCSM 25-03 (AI-Ready Federal Statistical Data), FCSM 20-04 (A Framework for Data Quality), and the OPEN Government Data Act.

One dimension runs ahead of current standards: whether an AI system can discover and retrieve the data in the first place — via emerging mechanisms such as llms.txt and the Model Context Protocol — is an access question the present federal guidance does not yet fully cover, and it is treated here as forward-looking rather than as a settled requirement.

The full definition appears in the Glossary (Appendix B).

# 3. Approach: three evidence streams

The assessment is one integrated package that draws on three complementary sources of evidence, not three separate products:

- Agency-level response: the high-level landscape from the top, answered once by the person whose job is to know it (the Chief Data Officer, Statistical Official, or Chief AI Officer).
- Practitioner survey: the lived experience of the statisticians, mathematical statisticians, and data scientists actively working — or trying to work — with the data and tools.
- Machine diagnostic: a script that assesses an agency's current public-facing web posture for machine usability of its public data, and points to where resources are needed to improve machine access to public endpoints.

The three streams cross-check each other; for example, what a practitioner reports about a dataset can be compared against what the diagnostic actually finds for that same dataset.

The split between the agency response and the practitioner survey is deliberate. An agency-level answer alone can mask ground-level problems, so the practitioner stream reaches the people doing the work directly rather than relying on a single summary from the top.

# 4. Agency-level response

What this stream is for:

- Capturing organization-level facts that no automated probe can observe: policies, governance, and where the agency intends to use AI.
- Answered once, by the accountable official, because these are their domain and a single authoritative answer is enough.
- Evidence-eliciting rather than self-rating: each item asks for a document, link, or concrete description, not a score.

| Question | Explanation |
|---|---|
| For your agency's major public data assets, is there a named individual or role accountable for each? | Whether each major public dataset has a specific owner. A stewardship register answers this; "no central register" or "handled informally" is also a valid answer. |
| Are data-governance responsibilities documented? | Whether the rules for managing data are written down in a policy or charter, rather than only understood informally. |
| Is there a documented policy governing AI use of agency data? | Whether the agency has its own written policy for how AI may use its data, versus relying only on government-wide guidance or having none yet. |
| When a data-quality defect is found in a public asset, is there a defined process to correct and republish it? | When an error is found in a published dataset, whether there is a defined way to fix and re-release it, or whether it is handled case by case. |
| Is there a documented process for assessing AI-related privacy or disclosure risk before deploying an AI use case? | Whether the agency checks for privacy or disclosure risk before turning on an AI use of its data, and whether that check is written down. |
| Has the agency identified priority AI use cases for statistical production? | Whether the agency has named where it intends to use AI in producing statistics. The agency's annual AI use case inventory is a place this can point to. |
| For identified use cases, is there a way to measure whether deployment improved the outcome? | For each intended AI use, whether there is a way to tell if it actually helped, rather than deploying without measuring the result. |

# 5. Practitioner survey

What this stream is for:

- Capturing lived experience that an automated probe cannot see and an executive summary cannot honestly report: barriers, friction, and what breaks in practice.
- Kept short, with bands and brief free-text answers, so the busy practitioners whose input matters most will actually finish it.
- Routed to the people in the relevant data areas who handle the data and tools day to day.

| Question | Explanation |
|---|---|
| Do you have access to the AI tools you need to do your work? | Whether the person has the AI tools their work requires; if not, what specifically is missing. |
| Do you have the training to use AI tools effectively in your work? | Whether the person has been trained to use AI tools well, not just given access to them. |
| Does your unit have people who can independently evaluate an AI or machine-learning tool's methodology, not just use it? | Whether the unit has anyone who can judge how a tool actually works, not only operate it. Zero is a valid and informative answer. |
| What is the single biggest barrier to getting AI-assisted work done? | The main thing stopping AI-assisted work. If the answer is approval delays or "other," the specific blocking step must be named so the barrier is actionable. |
| When you need to know whether a dataset can be shared or exposed a certain way, how long does it take to get an authoritative answer? | How long it takes to get a definitive answer, which is a proxy for how clear the rules and decision paths are. |
| Is there an AI-use policy for agency data that you have actually seen? | Whether the person has personally seen such a policy. Compared against the agency's answer, this reveals policies that exist on paper but not in practice. |
| The last time you needed to know what a field or variable in a public asset means, how long did it take and where did you look? | How easy it is, in practice, to find out what a data field means. |
| The last time someone tried to consume an agency dataset programmatically, what broke? | A concrete account of what failed when someone tried to use a dataset by machine. Compared against the machine diagnostic's findings for the same data. |
| What is the single biggest thing that slows you down when preparing or using agency data? | The one biggest day-to-day obstacle, in the person's own words, not pre-categorized. |

# 6. Machine diagnostic

What this stream is for:

- Probing an agency's public data presence directly and recording the actual response as evidence, so results are checkable without re-running the test.
- Machine-tested rather than self-reported, which makes it objective, reproducible by anyone with a browser and basic scripting, and impossible to inflate.
- Serving as a guide to where resources are needed to improve machine access, not as a grade.

The checks are organized around four plain-language questions.

## Can a machine find the data?

| Check | What it means |
|---|---|
| Access rules permit automated agents and point to a site map | The site's machine-access file allows automated tools and tells them where the index of content is. |
| A current site map is present and readable | A machine-readable list of the site's pages exists, parses correctly, and is up to date. |
| A structured data catalog resolves and validates | A standard public catalog of the agency's datasets exists and is valid, so a machine can list what is available. |
| Web addresses are stable and meaningful | Dataset links are durable and not hidden behind one-time sessions or scripted page loads. |

## Can a machine get the data?

| Check | What it means |
|---|---|
| The data is reachable by machine, without a human step | The dataset can be retrieved through an interface or bulk download, with no manual or scripted-browser step required. |
| The data is offered in machine-usable formats | Formats such as JSON, CSV, or Parquet are available, not only human-oriented HTML or PDF. |
| There are no anti-machine barriers on public data | No login wall, puzzle challenge, or scripted-page requirement blocks access to data that is meant to be public. |
| The whole dataset is available in bulk | The complete dataset can be obtained at once, not only a page at a time through a viewer. |

## Can a machine understand the data?

| Check | What it means |
|---|---|
| Field definitions are provided as data | The meaning of each field is available in a machine-readable form, not buried in a prose document. |
| A metadata standard is present and valid | The dataset carries standard, valid descriptive information so a machine can interpret it consistently. |
| Provenance is machine-readable | The source, method, version, and date of the data travel with it in a form a machine can read. |
| Codes and categories are documented and retrievable | The meaning of coded values and categories can be looked up by machine. |
| Units and data types are declared | The dataset states what its numbers measure and how each field is typed. |
| Access level is described | Where a public catalog points to a restricted dataset, a machine can learn that it is restricted and why. |

## Can a machine rely on the data?

| Check | What it means |
|---|---|
| Versioning is machine-readable | A version or last-modified signal is available so a machine knows which release it has. |
| Update cadence is declared and honored | The dataset states how often it is updated and follows that schedule. |
| An integrity signal is present | A checksum, signature, or canonical-source indicator lets a machine confirm the data is intact and authentic. |
| The license is machine-readable | The terms of use are stated in a form a machine can read. |

Two emerging access standards — llms.txt and the Model Context Protocol (MCP/WebMCP) — are also checked and reported separately as forward-looking signals; their absence is not counted against an agency.

# 7. Appendix A — Design principles

1. Test reality, do not ask for self-reports. Anything a machine can observe is probed, not surveyed.
2. Diagnose to guide, not to grade. The instrument finds gaps and routes effort; it is a pretest, not a final mark.
3. Measure substance, not presence. Existence is not readiness, and volume is not value.
4. Survey only what cannot be probed. Every survey item must justify why a machine could not answer it.
5. Ask for evidence, not agreement. Request a document, link, or concrete experience rather than a rating.
6. Route each question to the lowest-burden knower. Organization-level facts go to one agency respondent; lived experience goes to practitioners. Keep both short, because length generates nonresponse bias.
7. Specificity defeats the safe non-answer. A bare "red tape" checkbox explains nothing, so the specific blocking step is required.
8. Treat contradictions as the payload. The cross-checks between streams are designed in and depend on every response carrying a shared agency identifier.
9. Assess public data only. Protected data is never in scope, so protecting it is never penalized.
10. Stay open and reproducible. Anyone can run the diagnostic and verify the result.

# 8. Appendix B — Glossary

AI (artificial intelligence). A machine-based system that can, for a given set of human-defined objectives, make predictions, recommendations, or decisions influencing real or virtual environments (NIST SP 800-218A, per 15 U.S.C. § 9401(3)).

Machine learning. The development and use of computer systems that adapt and learn from data with the goal of improving accuracy (NIST SP 800-55v1). Most of what is called AI today is machine learning.

Machine-readable and machine-understandable. Machine-readable means a machine can open and parse the data, such as a clean CSV file. Machine-understandable is a higher bar: enough context, documentation, provenance, and quality information travels with the data that a system can interpret it correctly. Machine-readable is necessary but not sufficient for AI data readiness.

Provenance. The documented method of generation, transmission, and storage of information used to trace the origin of a piece of data — its chain of custody. In the FSS, statute includes provenance within the metadata a data product must carry (CNSSI 4009-2015; CIPSEA 2018, 44 U.S.C. § 3561).

AI data readiness. Data is AI-ready when it is machine-understandable, not merely machine-readable: its context, provenance, methodology, and quality signals are preserved and programmatically queryable, sufficient for an AI system, particularly a large language model, to analyze and answer questions about the asset without loss of statistical integrity. In the words of the federal project definition, AI-readiness is "the extent to which a data asset is prepared for effective analysis and querying by AI systems, particularly LLMs," spanning data quality, access, formatting, and metadata. This content-side definition assumes a consuming system can already reach the data.

A forward interpretation, ahead of current documented policy and offered as forward-looking rather than as a ratified standard: the definition above assumes access is already established, but in practice access and machine-retrievability must be deliberately configured, through emerging mechanisms such as llms.txt, the Model Context Protocol (MCP), and WebMCP, the last standardized only around 2026 — after the federal literature was written. A complete picture therefore treats discoverability and retrievability as a prior axis the current standards do not yet cover: data a model cannot find or reach is not AI-ready in any operational sense, however understandable it would be once reached. (Adopted and extended from America's DataHub RFS Topic MLMU-25, building on FCSM 25-03, FCSM 20-04, the OPEN Government Data Act, and FAIR principles; conceptual ancestor: Lawrence's Data Readiness Levels, 2017.)

# 9. References

Compiled from the provenance carried in the FSS AI vocabulary artifact for the sources this document actually uses. Where a federal standard is carried in that artifact only by its document identifier, the entry is cited by identifier and is partial in title or date.

America's DataHub Consortium. (2025). Measuring large language model understanding of federal statistical data (Request for Solutions, Topic MLMU-25). https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf

Committee on National Security Systems. (2015). Committee on National Security Systems (CNSS) glossary (CNSSI No. 4009). https://www.cnss.gov/CNSS/issuances/Instructions.cfm

Confidential Information Protection and Statistical Efficiency Act of 2018, Pub. L. No. 115-435 (codified at 44 U.S.C. § 3561). https://www.govinfo.gov/app/details/PLAW-115publ435

Federal Committee on Statistical Methodology. (2020). A framework for data quality (FCSM 20-04). https://statspolicy.gov/FCSM/resources/statistical-policy-working-papers/

Federal Committee on Statistical Methodology. (2025). AI-ready federal statistical data (FCSM 25-03).

Lawrence, N. D. (2017). Data readiness levels (arXiv:1705.02245). arXiv. https://arxiv.org/abs/1705.02245

National Institute of Standards and Technology. (n.d.). NIST SP 800-218A. https://doi.org/10.6028/NIST.SP.800-218A

National Institute of Standards and Technology. (n.d.). NIST SP 800-55 Vol. 1. https://doi.org/10.6028/NIST.SP.800-55v1

Office of Management and Budget. (2025). Accelerating federal use of AI through innovation, governance, and public trust (OMB M-25-21). https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf

OPEN Government Data Act, Title II of the Foundations for Evidence-Based Policymaking Act of 2018, Pub. L. No. 115-435 (2019). https://www.govinfo.gov/app/details/PLAW-115publ435
