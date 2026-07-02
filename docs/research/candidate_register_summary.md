# Candidate Register — Discovery Scan Summary

**Date:** 2026-07-02  
**Register:** `corpus/staging/candidate_register.jsonl` (gitignored, local only)

**Total unique candidates:** 89

Discovery only — no manifest entries, no events, no inclusion judgment (operator's next session).


## Counts by source_type

- **federal**: 33
- **academic**: 26
- **industry**: 19
- **standard**: 11

## Counts by discovered_via

- **research-synthesis**: 56
- **fss-policy-kg-manifest**: 33
- **wintermute-scan**: 1

Merged across >1 source: 1
  - NIST AI Risk Management Framework (AI RMF) — ['research-synthesis', 'fss-policy-kg-manifest']

## source_type classification rule

- **federal** — US federal government (NIST, GSA, GAO, Census, FCSM, OMB memos, EOs, US statutes, DOC, BEA).
- **academic** — peer-reviewed journals, arXiv, PubMed/PMC, ACM/Nature.
- **industry** — companies, consultancies, vendors, nonprofits (Cisco, IBM, Deloitte, McKinsey, Arm, Oxford Insights, Alice Labs, Prosci, Pearson, WEF, MITRE, DiMe, AI-REAL, Code for America).
- **standard** — intergovernmental / standards bodies (OECD, UNESCO, ITU, UN Statistics, UNECE, PARIS21, UNDP, IADB, EU JRC).

*Ambiguity:* the schema's four-value `source_type` has no clean slot for intergovernmental bodies; they are mapped to **standard**. Operator should confirm this convention.

## needs_source (Wintermute hits with no external citable URL — title only)

Six Wintermute `Document` hits were internal `claude_ai_chat` logs (discovery signal only, not citable primary sources per DD-002):
- A Simple AI Governance Process for Company ABC (claude_ai_chat)
- AI Adoption Geographic Disparities (claude_ai_chat)
- Brock Webb's AI adoption at Census Bureau (claude_ai_chat)
- Teaching AI governance through NotebookLM resources (claude_ai_chat)
- Thoughtful AI Adoption: Start Simple, Automate Gradually (claude_ai_chat)
- Website optimization for AI readiness and data discovery (claude_ai_chat)

Register candidates with a null primary_url (4): New Absorb Software Report: AI Ambition in L&D Outpacing Readiness, MIT NANDA report: 95% of enterprise AI pilots fail to deliver P&L impact, M-25-21: Accelerating Federal Use of AI through Innovation, Governance, and Public Trust, M-25-22: Driving Efficient Acquisition of Artificial Intelligence in Government

## Anomalies / flags for triage

- **AI-REAL Toolkit: AI Readiness Assessment Guide** — PDF; dco.org domain — verify liveness.
- **AI Data Readiness Checklist (Digital Government Hub)** — http (not https) in source.
- **Why AI Projects Fail: The 63% Human Factor Problem** — Blog; low provenance — 63% human-factor claim.
- **MIT NANDA report: 95% of enterprise AI pilots fail to deliver P&L impact** — Cited via SkillPanel aggregator only — primary URL not in synthesis; needs source.
- **AI Governance, Ethics and Leadership (substack) — Harvey Lab Legal AI Benchmark post** — Substack blog; low provenance — triage.
- **Webb: NIST x FCSM Crosswalk (Data Quality <-> AI Trustworthiness)** — Author work; Zenodo landing only — needs exact DOI.
- **M-25-21: Accelerating Federal Use of AI through Innovation, Governance, and Public Trust** — OMB memoranda landing page only in fss manifest — no stable PDF; needs source URL.
- **M-25-22: Driving Efficient Acquisition of Artificial Intelligence in Government** — OMB memoranda landing page only in fss manifest — no stable PDF; needs source URL.

General notes:
- The synthesis document itself is excluded from the register (internally generated discovery input, no citable provenance).
- Wintermute intake graph holds no AI-readiness *literature* — only personal chats + misc web articles; source B contributed 1 low-provenance candidate.
- fss-manifest entries are candidates for deliberate re-ingestion here (DD-001 acceptable redundancy); several OMB memos give only a landing-page URL (no stable PDF in that manifest).
- arXiv `2601.*`/`2603.*`/`2604.*`/`2605.*` IDs reflect 2026 submissions as recorded in the synthesis.
