# FSS AI Data Readiness — Internal Survey (the un-probeable layer)

**Date:** 2026-06-23
**Status:** working draft (~95% — role-routing taxonomy flagged for validation)
**Relationship to the diagnostic:** This survey covers ONLY what the machine probe physically cannot reach. It is the complement to `benchmark_rubric.md`, not a parallel instrument. Every item here must justify why a probe can't answer it. If a probe can test it, it belongs in the probe, not here.

---

## Design principles (inherited from the diagnostic, applied to the survey layer)

1. **Un-probeable only.** Scope = internal facts no HTTP request can observe: governance, ownership, workforce, legal comprehension, internal process. Anything about public data exposure (catalogs, APIs, metadata, formats, discoverability) is PROBED, deleted from here. This subtraction alone removes ~half the inherited 40-item instrument.

2. **Evidence-eliciting, not agreement-rating.** Replace "rate 1–5 whether X is true" with "name/link the artifact that proves X, or mark none." A request for a specific document cannot be inflated the way a Likert agreement score can. This is the anti-PMT discipline at the survey layer.

3. **Behavioral anchors where rating is unavoidable.** Some constructs are genuinely perceptual. Where a scale is used, anchor it to observable behavior, never to bare gradients ("sufficient," "easily," "readily" — all banned: they invite guessing and inflation).

4. **Symptom inversion / unreadiness.** Some items ask about blockers EXPERIENCED, not capabilities POSSESSED. People report pain honestly and inflate competence. Symptom items also cross-check the positive items.

5. **Practitioner-direct, not agency-aggregated.** Collected from the people touching the data, NOT one sanitized response laundered up the management chain (the iceberg problem). No "The agency..." framing — that is the executive-voice tell.

6. **Contradiction is signal.** Where a survey answer contradicts a probe result for the same asset, that gap is information (blind spot in the people OR hole in the automated view). Design items so this cross-check is possible.

---

## What was DELETED from the inherited 40 (and why)

| Inherited section | Disposition |
|---|---|
| I — Data Inventory & Accessibility | PROBED. Catalog presence, discoverability, access-without-coordination are all machine-testable. Delete. |
| II — Data Quality | MOSTLY PROBED. Completeness/accuracy/timeliness of public assets are testable against the data. Internal "process for correcting issues" survives (process, not state). |
| III — Data Standardization | PROBED. Formats, machine-readability, common identifiers, integration — all testable. Delete. |
| IV — Governance & Stewardship | SURVIVES. Ownership, responsibility definition — internal org facts. Reframe to evidence-eliciting. |
| V — Privacy/Security/Legal | SPLIT. Access controls = probeable. Staff legal *comprehension* and internal risk-assessment *process* = survive. |
| VI — Technical Infrastructure | MOSTLY PROBED. API access testable. Compute capacity / pipeline automation = internal, survive as thin items. |
| VII — Workforce Readiness | SURVIVES ENTIRELY. Literacy, expertise, training, leadership — all internal, none probeable. |
| VIII — "AI Readiness" | RENAME (category error — the whole instrument is AI readiness). Use-case identification survives as POINTER (not scored). Outcome measurement = internal process, survives. |

---

## The rewritten instrument

### Routing (FLAGGED — first-principles default, needs validation against real FSS org structure)

Three tracks. **This taxonomy is my best guess, not ground truth — validate who actually exists and who can answer what before fielding.**
- **PRACTITIONER** — data stewards, methodologists, engineers who touch the assets. Gets the ground-truth + symptom items.
- **GOVERNANCE** — CDO / Statistical Official / data-governance leads. Gets ownership/policy items.
- **CAIO/STRATEGY** — Chief AI Officer / strategy. Gets mandate/prioritization items, scoped to what they actually control.

Discipline: each item routes to the role that can answer it from DIRECT knowledge. An item answerable only by inference is mis-routed.

---

### Section A — Governance & Stewardship (GOVERNANCE track; evidence-eliciting)

- **A1.** For your agency's major public data assets, is there a named individual or role accountable for each? → *Provide the stewardship register/document, or mark: "no central register," "informal/by-convention," or "per-asset, undocumented."*
- **A2.** Are data-governance responsibilities documented? → *Link the governing policy/charter, or mark none.*
- **A3.** Is there a documented policy governing AI use of agency data? → *Link it, or mark: "none," "in draft," "relies on agency-wide M-25-21 guidance only."*
- **A4.** When a data-quality defect is identified in a public asset, is there a defined process to correct it and re-publish? → *Describe the trigger→fix→republish path in one sentence, or mark "ad hoc / no defined process."* (Process, not state — un-probeable. The defect itself is probeable; the existence of a fix loop is not.)

### Section B — Legal & Privacy Readiness (GOVERNANCE + PRACTITIONER; comprehension/process, not controls)

- **B1.** (Practitioner) When you need to know whether a given dataset can be shared/exposed in a particular way, can you get an authoritative answer, and how long does it typically take? → *Free-text + duration band. SYMPTOM item — measures friction, not policy existence.*
- **B2.** (Governance) Is there a documented process for assessing AI-related privacy/disclosure risk before deploying an AI use case on agency data? → *Link/describe, or mark none.*
- **B3.** (Practitioner) Have you encountered cases where uncertainty about legal restrictions blocked or delayed a legitimate data use? → *Frequency band + one example. SYMPTOM.*

### Section C — Workforce (PRACTITIONER + GOVERNANCE; behavioral anchors, not self-flattery)

- **C1.** Does your unit have personnel who can independently evaluate an AI/ML tool's methodology (not just use it)? → *Count or band of such people, NOT a 1–5 confidence rating. Zero is a valid, informative answer.*
- **C2.** In the last 12 months, did staff complete AI/data-skill training that changed how work is done? → *Name the training + one concrete change, or mark "none / training existed but changed nothing."* (Behavioral anchor — "changed how work is done" is falsifiable; "we value training" is not.)
- **C3.** (Symptom) When an AI-assisted task needs methodological review, is the reviewer-to-work ratio sufficient that review is meaningful rather than rubber-stamp? → *Describe the bottleneck if one exists. SYMPTOM — surfaces automation-bias risk.*

### Section D — Internal AI Capability (CAIO/STRATEGY; pointer, not score)

- **D1.** Has the agency identified priority AI use cases for statistical production? → *List or link. Cross-reference the M-25-21 inventory.*
- **D2.** For identified use cases, is there a way to measure whether the deployment actually improved the outcome? → *Describe the measure, or mark "deployed without outcome measurement."*

> **HARD CONSTRAINT — inventory as pointer, never metric.** The M-25-21 use-case inventory is self-reported and inflation-prone. Use it to locate where AI is claimed, NOT to score readiness. A thin inventory is a lead (under-use OR under-reporting OR conservative scoping — indistinguishable from the inventory alone), never evidence of low readiness. Do not compute any score from inventory contents.

### Section E — Symptom battery (PRACTITIONER; the unreadiness inversion)

Direct blocker questions. People report pain honestly. These cross-check Sections A–D's positive framing.

- **E1.** Last time you needed to understand what a field/variable in a public asset means, how long did it take and where did you have to look? → *Duration + source. Tests lived interpretability vs. claimed metadata.*
- **E2.** Last time an external user (or you) tried to consume an agency dataset programmatically, what broke? → *Free-text. Cross-checks the probe's retrieval findings from the human side.*
- **E3.** What is the single biggest thing that slows you down when preparing or using agency data? → *Open. The highest-signal question in the instrument; resist the urge to pre-code it.*

---

## Open items
- [ ] **Role taxonomy validation** (the flagged 5%) — confirm PRACTITIONER/GOVERNANCE/CAIO tracks map to real FSS roles and that each item routes to someone with direct knowledge.
- [ ] Duration/frequency band definitions (standardize the response scales for B1, B3, C, E1).
- [ ] Decide collection mechanism that bypasses management-chain aggregation (practitioner-direct) — political/logistics question, not a wording question.
- [ ] Contradiction-mapping spec: how survey items pair to probe findings for the cross-check (E1↔D3 interpretability probes; E2↔D2 retrieval probes).
- [ ] Pilot cognitive test: do practitioners read these as answerable, or do any still trigger "I don't know"? (The original failure mode.)
