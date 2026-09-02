# FSS AI Data Readiness Assessment
*A specification for a three-part instrument — machine diagnostic + agency roll-up survey + practitioner survey. Circulated for team review: is this the right instrument, asking the right questions, before anything is fielded?*

---

## 1. Task & purpose

**What this is.** A specification for an instrument that assesses whether a Federal Statistical System (FSS) agency's public data is *AI-ready* — usable by an AI system, not just present on a website. The instrument has three parts: a machine diagnostic that probes public endpoints directly, an agency roll-up survey answered once by the accountable official, and a practitioner survey answered by the people who actually work the data.

**Who it's for.** The review team. This document is the thing you evaluate — not data we collected, but the design we propose to collect it with.

**What we're asking you to evaluate.** Two questions, before a single agency is probed:
1. Is this the **right instrument** — does the machine/survey split, the routing, and the cross-check design produce trustworthy evidence rather than self-flattering noise?
2. Are these the **right questions** — does the machine diagnostic probe what "AI-ready" actually requires, and do the surveys ask only what a machine genuinely cannot?

Everything below — the definition, the design justification, the instruments, and the reference glossary — exists so you can answer those two questions without having to reconstruct our assumptions.

---

## 2. Why we're doing it

**The mandate context.** OMB M-25-21 (*Accelerating Federal Use of AI through Innovation, Governance, and Public Trust*, Apr. 2025) pushes agencies to identify and deploy AI use cases and to inventory and govern them. For the FSS specifically, that raises a prior question the policy does not answer: is the public data agencies *already publish* in a state an AI system can actually find, retrieve, and use correctly? You cannot accelerate AI use of federal statistics on top of data a machine cannot consume.

**The deeper reason — measurement needs a shared definition.** This is load-bearing, so it is stated plainly: **if we cannot agree on what "AI readiness" means, measuring it is meaningless.** A score is only as defensible as the definition behind it. The FSS asked for definitions in the first place *because people do not share the terms* — "AI-ready," "machine-readable," "interpretable" are used to mean different things by different readers. An assessment that scores agencies against an unstated or private definition reproduces exactly that confusion at the moment it matters most. So this specification adopts a definition first (§4), traces it to federal sources, and builds the instrument to mirror it.

---

## 3. The adopted definition (with provenance)

The instrument measures against an explicit, sourced definition of *AI-ready data*. It is adopted from federal sources and extended — not coined here.

### Part A — the grounded, content-side definition (the adoptable core)

> Data is **AI-ready** when it is **machine-understandable — not merely machine-readable**: its context, provenance, methodology, and quality signals are preserved and programmatically queryable, sufficient for an AI system (particularly a large language model) to analyze and answer questions about the asset *without loss of statistical integrity*.

The federal project definition this rests on, verbatim:

> "For the purposes of this project, 'AI-readiness' refers to the extent to which a data asset is prepared for effective analysis and querying by AI systems, particularly LLMs. This includes data quality, access, formatting, and metadata. AI-ready data enable LLMs to generate meaningful insights from both structured (e.g., tabular) and unstructured (e.g., reports) formats by facilitating accurate interpretation and contextual understanding."

**Scope boundary of Part A:** this content-side definition assumes a consuming system can *already reach* the data asset. It addresses the readiness of data that is already accessible — whether a model can *find and retrieve* it in the first place is treated separately (Part B), and deliberately so, to keep the established core uncontaminated by interpretation.

### Part B — the access-axis extension (dated forward interpretation, NOT a ratified standard)

> *Forward interpretation — ahead of documented policy (author framing, dated 2026-06; not an established standard).* The federal and FCSM/Commerce definitions above assume access is already established. In practice, access and machine-retrievability must be deliberately configured — via emerging mechanisms such as **llms.txt**, the **Model Context Protocol (MCP)**, and **WebMCP** (the last standardized only around 2026, i.e. *after* the FCSM/Commerce literature was written; written policy lags the technology here). A complete AI-data-readiness picture therefore treats **discoverability and retrievability as a prior axis** the current standards do not yet cover: data a model cannot find or reach is not AI-ready in any operational sense, however machine-understandable it would be once reached. This is the *machine-as-first-class-user* position — offered as a bounded, forward-looking seed, not a mandate, and kept separate from Part A so the definition's authority is not diluted by interpretation.

### Provenance

The definition is **adopted from federal sources and extended**, which is what makes a score against it authoritative rather than arbitrary:

- **America's DataHub / NSDS Request for Solutions — Topic MLMU-25**, *"Measuring Large Language Model Understanding of Federal Statistical Data"* (footnote 2) — the source of the project definition. [ATT-1_Topic_MLMU-25.pdf](https://www.americasdatahub.org/wp-content/uploads/2025/06/ATT-1_Topic_MLMU-25.pdf)
- **FCSM 25-03**, *AI-Ready Federal Statistical Data* — establishes that creating AI-ready data "builds on established open-data principles," that federal statistics used in AI interactions must meet the data-quality dimensions of the Framework (accessibility, timeliness, accuracy), and that metadata enrichment exposed through AI-friendly APIs improves how LLMs discover and interpret data.
- **FCSM 20-04**, *A Framework for Data Quality* — anchors the data-quality dimensions that must be balanced and preserved.
- **OPEN Government Data Act** (Title II, P.L. 115-435) — the open-data / machine-readability foundation FCSM 25-03 builds the AI-ready extension on top of.
- *Conceptual ancestor (academic, not federal policy):* Lawrence, **Data Readiness Levels** (2017, arXiv:1705.02245) — the source of the use-case-conditional logic (readiness is relative to the intended use). Cited as an ancestor only.

This definition **builds on FAIR** (Findable, Accessible, Interoperable, Reusable) and **does not supersede it**.

### Definition → instrument (one line)

The two-track structure of the instrument mirrors the two parts of the definition exactly: **the machine diagnostic measures Part A (content-side, established) as the scored core, and reports Part B (access-side, emerging) on a separate, unscored frontier track** — so presence of frontier mechanisms is forward-looking credit, never a penalty for their absence.

---

## 4. Justification of the two-instrument design

AI data readiness has two kinds of evidence, and forcing them into one tool produces bad data.

**What a machine can test, we test directly.** Whether an agency's public data is discoverable, retrievable, and interpretable by an AI agent is observable — point an agent at the public endpoints and see what comes back. We do not ask agencies to rate themselves on this; we measure it. Objective, reproducible by anyone with a browser and Python, un-inflatable.

**What a machine cannot reach, we ask about — and we route each question to whoever can answer it at the lowest burden.** Two short surveys, not one long one:
- **Agency roll-up** — answered ONCE by the person whose job is to know (CDO / Statistical Official / CAIO). Org-level facts: policies, governance, use-case identification. All "produce the artifact," never "rate yourselves."
- **Practitioner survey** — answered by the people who actually touch the data. Lived experience a probe can't see and an executive can't honestly report: barriers, blockers, friction.

Splitting by respondent is a **data-quality** decision, not a convenience. A long survey selects *against* the busy practitioner whose answer you most need — length manufactures nonresponse bias. Keep each instrument short enough to finish in one sitting.

**The cross-checks are the point.** The three instruments share an agency (and data-area) key so they reconcile. Two contradictions are designed in, not accidental:
- Roll-up says "here is our AI-use policy" vs. practitioners who have never seen one → **phantom-policy signal** (how many believe they're governed by a thing that may not exist).
- Practitioner says "X broke when we hit the API" vs. the probe's retrieval finding for the same asset → **lived-vs-measured gap.**

**Scope:** public and public-mandated data only. Protected data (Title 13, Title 26, CIPSEA-restricted, PII) is out of scope entirely — never probed, never scored. The question is only whether what an agency *already publishes* is published so a machine can use it.

> **Non-negotiable for fielding:** every response in all three instruments carries the agency (and where possible data-area) identifier. Without the join key the cross-checks collapse and you're left with anecdotes. If collection routes through a generic survey tool, the key cannot be dropped.

---

## Part 1 — Machine diagnostic (what is probed)

Automated probes against an agency's public data presence. Each returns pass / partial / fail and saves the actual response as evidence. No self-report anywhere.

**Discovery — can a machine find the data?**
- `robots.txt` permits agents and declares a sitemap
- `sitemap.xml` present, parses, current
- Structured catalog (`data.json` / DCAT) resolves and validates
- Stable, semantic URLs (not session- or JS-gated)

**Retrieval — can a machine get it?**
- Programmatic access (API or bulk download, no human/JS step)
- Content negotiation (JSON/CSV/Parquet, not only HTML/PDF)
- No anti-machine barriers (no CAPTCHA / login wall / JS-render on public data)
- Bulk availability (whole dataset, not just paginated UI)

**Interpretability — can a machine use it correctly?**
- Machine-readable schema (field definitions as data, not prose PDF)
- Metadata standard present and valid (DCAT / schema.org / ISO 19115)
- Provenance machine-readable (source, method, version, date)
- Semantic clarity (codes/enums documented, retrievable)
- Units and types declared
- Access-tier metadata (where a public catalog points at a restricted dataset, a machine can learn *that* it's restricted and *why*)

**Trust / freshness — can a machine rely on it?**
- Versioning (version or last-modified machine-readable)
- Update cadence declared and honored
- Integrity signal (checksum / signing / canonical source)
- License machine-readable

**Frontier (reported separately, not scored against the core).** Emerging access standards that postdate current federal guidance. Presence is forward-looking credit; absence is **not** unreadiness.
- **llms.txt** (convention since ~2024) — resolves, parses, points to real resources
- **MCP / WebMCP** (standardized ~2026) — advertised, reachable, valid schema

*"Has llms.txt but not WebMCP" is a distinct, informative state from "has neither."*

**Output:** per-agency per-dimension core score, frontier signals reported separately, evidence file per probe so any result is checkable without re-running.

---

## Part 2 — Agency roll-up survey (answered once, by the right person)

Org-level facts. Evidence-eliciting only — produce the artifact, never self-rate. Low burden for the respondent because it's their domain.

| # | Question | Response field |
|---|---|---|
| R1 | For your agency's major public data assets, is there a named individual/role accountable for each? | Provide stewardship register, OR: no central register / informal / per-asset undocumented |
| R2 | Are data-governance responsibilities documented? | Link policy or charter, OR "none" |
| R3 | Is there a documented policy governing AI use of agency data? | Link it, OR: none / in draft / relies on agency-wide M-25-21 guidance only |
| R4 | When a data-quality defect is found in a public asset, is there a defined correct-and-republish process? | One-sentence path, OR "ad hoc / no defined process" |
| R5 | Is there a documented process for assessing AI-related privacy/disclosure risk before deploying an AI use case? | Link or describe, OR "none" |
| R6 | Has the agency identified priority AI use cases for statistical production? | List or link (cross-reference M-25-21 inventory) |
| R7 | For identified use cases, is there a way to measure whether deployment improved the outcome? | Describe the measure, OR "deployed without outcome measurement" |

*The M-25-21 inventory is used only to locate where AI is claimed — never as a readiness score. A thin inventory is a lead, not a verdict.*

---

## Part 3 — Practitioner survey (answered by people who do the work)

Lived experience, un-probeable, un-inflatable. Bands and short free-text — fast to complete. Route to data stewards, methodologists, engineers in the relevant data areas.

### Barriers (the core — "do you have what you need to do the job?")

| # | Question | Response field |
|---|---|---|
| P1 | Do you have access to the AI tools you need to do your work? | Yes / partly / no + (if not) one line: what's missing |
| P2 | Do you have the training to use AI tools effectively in your work? | Yes / partly / no |
| P3 | Does your unit have people who can independently evaluate an AI/ML tool's methodology (not just use it)? | Count or band: 0 / 1–2 / 3+ (zero is a valid answer) |
| P4 | What is the biggest barrier to getting AI-assisted work done? (check all that apply) | ☐ tools ☐ training ☐ skills ☐ access/permissions ☐ procurement ☐ approval/red tape ☐ other — **if red tape or other, name the specific step that blocks you** (required) |

### Friction & blockers (lived symptoms — cross-check the probe and the roll-up)

| # | Question | Response field |
|---|---|---|
| P5 | When you need to know whether a dataset can be shared/exposed a certain way, how long to get an authoritative answer? | Same day / days / weeks / no clear path |
| P6 | Is there an AI-use policy for agency data that you've actually seen? | Yes (seen it) / believe so (haven't seen it) / no / don't know — **[phantom-policy check vs. R3]** |
| P7 | Last time you needed to know what a field/variable in a public asset means, how long did it take and where did you look? | Duration + source |
| P8 | Last time someone tried to consume an agency dataset programmatically, what broke? | Free text — **[cross-check vs. retrieval probe]** |
| P9 | What is the single biggest thing that slows you down when preparing or using agency data? | Open — do not pre-code |

*Total: 7 roll-up + 9 practitioner = 16 survey items, plus the machine diagnostic. Under the burden ceiling; every item is either un-probeable, a designed cross-check, or both.*

---

## Appendix A — Glossary

Reference layer, not part of what anyone fills out. **Closed-loop rule:** this glossary contains *only* AI/technical terms that actually appear in Parts 1–3, and every definition is drawn from the verified FSS AI vocabulary (`fss_ai_vocabulary.json`, 43 terms, provenance-bearing) — condensed, never re-authored. Terms used in the instrument with no vocabulary record are flagged as gaps below rather than invented.

| Term | Definition (condensed from the vocabulary) | Source |
|---|---|---|
| **AI (artificial intelligence)** | A machine-based system that can, for a given set of human-defined objectives, make predictions, recommendations, or decisions influencing real or virtual environments. | NIST SP 800-218A (per 15 U.S.C. § 9401(3)) |
| **AI readiness / AI-ready data** | Data is AI-ready when it is machine-understandable, not merely machine-readable: its context, provenance, methodology, and quality signals are preserved and programmatically queryable, so an AI system (particularly an LLM) can analyze and answer questions about it without loss of statistical integrity. Federal framing: "the extent to which a data asset is prepared for effective analysis and querying by AI systems, particularly LLMs" — spanning data quality, access, formatting, and metadata. *(Full definition with provenance in §3.)* | America's DataHub RFS Topic MLMU-25 (fn. 2), extending FCSM 25-03 & FCSM 20-04 |
| **AI use case inventory** | An annual, public inventory of an agency's AI use cases, identifying high-impact use cases and describing associated risks and mitigations, required of federal agencies. | OMB M-25-21 |
| **Machine learning (ML)** | The development and use of computer systems that adapt and learn from data with the goal of improving accuracy. | NIST SP 800-55v1 |
| **Provenance** | The documented method of generation, transmission, and storage of information used to trace the origin of a piece of data — its chain of custody. In the FSS, CIPSEA includes provenance within required metadata (44 U.S.C. § 3561(19)). | CNSSI 4009-2015; CIPSEA 2018 |

### GLOSSARY GAPS — terms used in the instrument with no vocabulary record

These AI/technical terms appear in Parts 1–3 but have **no record** in `fss_ai_vocabulary.json`. No definitions are invented here. This is signal, not failure: it shows where the vocabulary needs to grow (or where a term is operational rather than policy vocabulary).

- **machine-readable / machine-understandable** — Part 1 (interpretability dimension). The distinction is *discussed inside* the `AI-ready data` record but neither is a standalone term.
- **discoverability** — Part 1 (Discovery dimension).
- **retrievability** — Part 1 (Retrieval dimension).
- **interpretability (data sense)** — Part 1 (Interpretability dimension). **False-friend flag:** the vocabulary's `interpretability` exists only as a surface form of *explainability* (the degree to which the reasons for a **model's output** can be represented to a human). The instrument's "interpretability" means whether a **data asset** can be correctly interpreted by a machine. Different concept — matching them would be drift, so it is treated as a gap.
- **content negotiation** — Part 1 (Retrieval).
- **structured catalog / `data.json`** — Part 1 (Discovery).
- **metadata standard (DCAT, schema.org, ISO 19115)** — Part 1 (Interpretability). The vocabulary covers `provenance` as a component of metadata, but not "metadata standard" or the named standards.
- **machine-readable schema** — Part 1 (Interpretability).
- **semantic clarity** — Part 1 (Interpretability).
- **bulk availability** — Part 1 (Retrieval).
- **programmatic access / API** — Part 1 (Retrieval); Part 3 (P8, "consume … programmatically").
- **llms.txt** — Part 1 (Frontier). Named in the `AI-ready data` forward-interpretation note (§3 Part B) but has no own record.
- **MCP / WebMCP** — Part 1 (Frontier). Same: named in the forward-interpretation note, no own record.
- *(lower-level web/infrastructure terms, also without records: `robots.txt`, `sitemap.xml`, versioning, integrity signal/checksum, machine-readable license.)*

**Dogfooding finding.** The vocabulary was built for AI **governance and literacy** terms (definitions, risk, FSS bridges); the machine diagnostic runs almost entirely on **data-access and data-engineering** vocabulary, which the vocabulary does not yet carry. The matched-to-gap ratio (5 matched, ~13 gaps) is itself a requirement: either (a) extend the vocabulary with a data-readiness tier sourced to FCSM 25-03 / DCAT / the OPEN Government Data Act, or (b) decide these are operational engineering terms outside the FSS policy vocabulary's scope and document that boundary. Recommendation: (a) — the instrument cannot be self-explaining to the FSS audience until its core data-readiness terms are defined from a verified source, which is the exact comprehension gap this whole effort exists to close.

---

## Appendix B — Design principles

1. **Test reality, don't ask for self-reports.** Anything a machine can observe is probed, not surveyed.
2. **Diagnose to guide, not to grade.** Finds gaps and routes effort. A pretest, not a final mark.
3. **Measure substance, not presence.** Existence isn't readiness; volume isn't value.
4. **Survey only the un-probeable.** Every survey item must justify why a machine couldn't answer it.
5. **Evidence over agreement.** Ask for a document, link, or concrete experience — not a 1–5 rating.
6. **Route to the lowest-burden knower.** Org facts → one roll-up respondent. Lived experience → practitioners. Length is a nonresponse-bias generator; keep both short.
7. **Specificity kills the safe non-answer.** "Red tape" as a bare checkbox explains nothing — force the specific blocking step.
8. **Contradictions are the payload.** Phantom-policy (P6 vs R3) and lived-vs-measured (P8 vs probe) are designed cross-checks; they require the join key.
9. **Public data only.** Protected data is never in frame, so "you're penalizing us for protecting data" is a non-issue by construction.
10. **Open, reproducible, un-gameable.** Anyone can run the probe and verify the numbers.

### Open items (internal — not team-facing)
- Practitioner survey role-routing (who in which data areas receives it) — needs validation against real FSS org roles.
- Probe target list beyond seeded agencies (Census/BLS/BEA) — broader FSS enumeration.
- False-negative audit before any scaled run or published scores: confirm a low result reflects agency state, not a harness limit (body-cap truncation and 403 cases already seen).
- Peer-cohort/fairness layer for cross-agency comparison (kept out of this team-facing doc deliberately).
- Cross-check reconciliation spec: how P6↔R3 and P8↔probe pair up in analysis.
- **Vocabulary gap (from this assembly's glossary audit):** the data-access/engineering terms the machine diagnostic relies on (machine-readable, content negotiation, DCAT, programmatic access, etc.) have no record in `fss_ai_vocabulary.json`. Extend the vocabulary with an FCSM-25-03-sourced data-readiness tier, or document the scope boundary. See Appendix A → GLOSSARY GAPS.
