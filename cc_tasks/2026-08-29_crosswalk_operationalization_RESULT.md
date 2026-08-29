# RESULT — 2026-08-29_crosswalk_operationalization

**Date:** 2026-08-29. **Zero kg-pipeline model spend** — nothing in this task called `model_stub`;
the spend ledger has no run declared for it and none was needed. Admission was rule-based; the
brief is my own generation. Acquisition used `curl` and two web searches, neither of which touches
the extraction choke point.

**Deliverables:** `docs/crosswalk/usafacts_operationalization_skeleton.md` (v0.1 → **v0.2**) and
`docs/crosswalk/usafacts_operationalization_brief.md` (**new**).

## Preamble compliance

- `_ADDENDUM*.md` siblings of this task: **none exist** (globbed `cc_tasks/2026-08-29_crosswalk_operationalization_ADDENDUM*.md`).
- `seldon cc complete` run **before** this RESULT was written: task `3d86f16d`, state `proposed → completed`.
- Discrepancies are reported below and were **not** silently reconciled.

---

## Discrepancies (reported, not reconciled)

1. **Most of the §9 acquisition queue was already admitted.** The task frames §0 as an acquisition
   pass over ~14 items. Checked against `corpus/manifest.json` first, as §9 itself instructs: **10 of
   them were already `included` / `verified`** — FCSM.25.03 (`fcsm-25-03`), GEO
   (`aggarwal-2024-geo-generative-engine-optimization`), Croissant (both the MLCommons spec and the
   Akhtar 2024 paper), NIST AI RMF **and** the GenAI profile (`nist-generative-ai-profile-ai-600-1`,
   plus the Playbook and an existing `webb-fcsm-nist-crosswalk`), SDMX (two entries), DCAT (W3C plus
   three DCAT-US), FAIR (`wilkinson-2016-fair-guiding-principles`), llms.txt, schema.org (seven
   nodes), and MITRE. §0's real work was the residue, not the queue.
2. **Indicator count: 45, not 44.** Groups A(9, including A9 from §1b) B(6) C(5) D(4) E(9) F(6)
   G(6). The task's "44 indicators" matches the count **excluding A9**, which §1b added after the
   original tables — so the two numbers are reconcilable and I have used 45 throughout, noting which
   is which.
3. **Seven indicator groups, not six.** The task's §4 asks for "six indicator groups". There are
   seven letter-groups in the skeleton (A–G). The brief describes all seven; I did not merge two to
   hit the number.
4. **Seldon has no `Documentation` artifact type.** §5 asks to register both documents as
   `Documentation`. The valid types are `AgentRole, ArchitecturalDecision, AuditFinding, AuditRun,
   BuildRun, Citation, DataFile, DesignNote, Figure, GeneratedFile, Issue, LabNotebookEntry,
   OntologyTerm, PaperSection, PipelineRun, ResearchTask, Result, SRS_Requirement, Script, Table,
   Workflow`. Registered as **`DesignNote`** (`note_type: pattern_proposal`), the closest fit.
5. **A `DesignNote` cannot be linked to a `ResearchTask` in the Seldon schema.** §5 asks for the
   artifacts to be "linked to this task". `DesignNote` can only originate `references_ontology →
   OntologyTerm` and `informs → ArchitecturalDecision`; there is no relationship to a
   `ResearchTask`. Rather than edit the Seldon domain schema — a cross-project change well outside
   this task — the task file is carried on each artifact's **`provenance`** property. The link is
   recorded in property form; it is not a graph edge, and a query for edges will not find it.
6. **`kg.manifest verify` reports 4 pre-existing `hash_mismatch` entries**, none of them from this
   task: `fcsm-19-01-...`, `ai-in-government-act-of-2020`, `advancing-american-ai-act-ndaa-fy2023-div-g`,
   `information-quality-act-...`. All four trace to `manifest_add` events dated **2026-07-04** whose
   recorded `content_hash` differs from the file now on disk; the *projected* manifest and the disk
   agree, so the divergence is event-log vs disk. The files were evidently re-acquired later without
   a superseding event. **Not fixed here** — which hash is authoritative is an operator call, and
   the eight documents this task admitted are all clean.
7. **The `ddialliance.org/Specification` path 404s.** The skeleton's §9 names "DDI" generically; the
   live primary is the product page `https://ddialliance.org/ddi-codebook`, which is what was
   admitted. Recorded on the manifest entry.

---

## §0 — Acquisitions (admission only; no extraction)

`scripts/manifest_crosswalk.py`, modelled on `scripts/manifest_triage.py`. Path: fetch →
`corpus/staging/inbox/crosswalk_2026-08-29/` → verify content → `corpus/crosswalk/` → dixie
`screening_imported` → `kg.manifest.add` → sweep → `corpus_epoch_declared` → `manifest.rebuild()`.
`dixie_evidence.yaml` `document_dirs` gained `crosswalk` (the same way `kernel` and `triage` were
added by their own tasks).

**No `extraction_request` events were written for any of these** — extraction waits on v0.3.7
(task §0, explicit; DD-023).

### Admitted — 8

| doc_id | title | src type | sha256 | primary_url |
|---|---|---|---|---|
| `usafacts-ai-ready-data-guide` | AI-Ready Data — The USAFacts Guide (6 pp) | practitioner | `02ceecd47c8f` | media.usafacts.org/…AIReadinessForGovernment.pdf |
| `usafacts-fde-standards-detailed` | Standards for Excellent Data Products, Detailed User Guide (31 pp) | practitioner | `98a092ac6f19` | media.usafacts.org/…Detailed-User-Guide-… |
| `usafacts-fde-standards-quick-reference` | Data Product Grading Rubric, Quick Reference | practitioner | `f0bfaf7e80d8` | media.usafacts.org/…Quick-Reference-… |
| `ddi-codebook-specification` | DDI-Codebook (DDI-C) | standard | `97fa0a19fad7` | ddialliance.org/ddi-codebook |
| `odcs-open-data-contract-standard` | Open Data Contract Standard | standard | `8a140f031b7b` | bitol-io.github.io/open-data-contract-standard/latest/ |
| `slsa-specification-v1-0` | SLSA Specification v1.0 | standard | `94a6630c0ec4` | slsa.dev/spec/v1.0/ |
| `sainz-2023-llm-data-contamination` | NLP Evaluation in trouble (Findings EMNLP 2023) | academic | `54ec9661a921` | aclanthology.org/2023.findings-emnlp.722/ |
| `webb-2026-state-fidelity-validity` | State Fidelity Validity for Reproducible AI Systems | academic | `849d45f705fa` | doi.org/10.5281/zenodo.22111334 |

Every artifact was opened and its first pages read before admission — the two `usafacts-fde-*`
files, the DDI page and the ODCS page were confirmed to be the documents claimed, not landing pages
or redirects. Sweep: `{'observed': 8, 'checked': 8, 'quarantined': 0}`.

**Contamination-source selection rationale (§0 requires it recorded).** Five candidates were scored
by citation count via OpenAlex on 2026-08-29: Sainz et al. 2023 **62**; Deng et al. 2024 (NAACL)
28; "Benchmark Data Contamination … A Survey" 7; "A Survey on Data Contamination for LLMs" 7;
Magar & Schwartz 2022 (ACL) 2. Sainz leads by 2.2×. **Deviation recorded:** the task says "survey"
and Sainz et al. is a *position paper*. I took the most-cited work rather than the most-cited work
literally called a survey, because the indicator it grounds (E4, contamination policy) is a policy
claim the position paper states directly, and the alternative was a 7-citation paper over a
62-citation one. If the word "survey" was load-bearing, this is the line to reverse.

### Blocked — 1 (recorded as an `acquisition_blocked` event in `events/batch-017.jsonl`)

| doc_id | reason |
|---|---|
| `commerce-generative-ai-open-data-guidelines` | **HTTP 403 from every client tried on 2026-08-29**: `curl` with a browser User-Agent, the `commerce.gov/sites/default/files` PDF path, `data.commerce.gov`, and `WebFetch`. The 5,801-byte body is a Cloudflare interstitial ("Just a moment… Enable JavaScript and cookies to continue"), not the document. `resources.data.gov` has no copy (404). This is bot protection, not a paywall or a withdrawal. |

**No secondary source was substituted for it** (task §0). The manifest already holds
`generative-ai-and-open-data-guidelines-and-best-practices-de` at `pending_refetch` / `quarantined`
for the same URL; this run did not alter that entry. The two cells that named it (A1, B1) are
recorded as **gaps**, not resolved to a stand-in — which is why A1 is a gap despite the criterion
being well-covered elsewhere in the literature.

---

## §1 — Evidence-cell resolution

**45 indicators: 25 resolve to at least one admitted `doc_id`, 20 are gaps.** Prose pointers are
gone from the skeleton; every cell is now a `doc_id` or the word gap. **No gap cell was filled with
a new claim** (task §1) — including cases where I could see a plausible substitute, e.g. A1, whose
named source is the blocked Commerce guidance.

Three of the skeleton's own pointers did **not** resolve and are now explicit gaps:

| skeleton pointer | outcome |
|---|---|
| D3 "PROV-aligned standards nodes" | **gap** — no PROV-O or W3C PROV document is admitted. The nearest hit, `census-bureau-statistical-quality-standards-standard-f2-prov`, matched only on the letters "prov" in its standard code and is not a provenance-vocabulary spec. |
| G1 "DP documentation" | **gap** — no differential-privacy or disclosure-avoidance document is admitted. G1 keeps `fcsm-23-02` for the quality-dimension half. |
| F1 "data-contract / expectation-suite literature" | partially resolved to `odcs-open-data-contract-standard`; no expectation-suite (Great Expectations / dbt class) source is admitted. |

The full per-indicator resolution is the right-hand column of the tier log below, and the skeleton
itself is the authoritative copy.

---

## §2 — Tier log (rule applied per indicator)

Tier vocabulary is the schema's existing `Measure.tier` enum, per skeleton §6b.1.
**Distribution: `public` 17 · `agency_instrumented` 21 · `paid` 7.**

Three assignments are not a bare read of the type column and carry their reasoning, as §2 permits:

- **A2, B3, F2, G3** (`AUTO/DOC` → `public`): §6b.2's machine-first rule — where a public machine
  test exists it replaces practitioner self-report, so the AUTO half governs.
- **C4** (`EVAL/AUTO` → `public`): the AUTO half (which page a generative engine cites) runs
  against the public surface with no agency cooperation.
- **F6** (`AUTO` → `paid`): the type column says AUTO, but §6b.1 names *attestation infrastructure*
  explicitly as `paid`. The funded-capability rule governs the type rule. The skeleton had already
  hand-marked F6 a `paid` candidate; this is the rule that confirms it.
- **E8** (`AUTO/EVAL` → `paid`): scheduled re-runs against a baseline are monitoring, named `paid`.
- **G1, G2, G6** (`DOC+EVAL` → `agency_instrumented`): the DOC half gates — the EVAL half cannot
  run until the structured fields exist. Their EVAL halves are `paid` work once it does.

| # | Tier | Rule applied (§6b) | Evidence resolution |
|---|---|---|---|
| A1 | `public` | AUTO on public surface | **gap** — named source (Commerce GenAI-Open-Data guidance) is `acquisition_blocked`, batch-017 |
| A2 | `public` | AUTO/DOC; §6b.2 machine-first — the AUTO half is a public machine test and replaces self-report | **gap** |
| A3 | `public` | AUTO on public surface | **gap** |
| A4 | `public` | AUTO on public surface | `rfc-9309-robots-exclusion-protocol`; `google-robots-txt-intro`; `openai-crawlers-bots`; `ant... |
| A5 | `public` | AUTO on public surface | `llmstxt-proposal`; `sitemaps-protocol` |
| A6 | `public` | AUTO on public surface | `schema-org-dataset`; `w3c-dcat-3`; `mlcommons-croissant-spec`; `croissant-akhtar-2024-paper` |
| A7 | `agency_instrumented` | DOC requiring agency artifacts | **gap** |
| A8 | `public` | AUTO on public surface | **gap** |
| A9 | `public` | AUTO on public surface | `wilkinson-2016-fair-guiding-principles`; internal existence proof: fss-policy-kg (MCP server) |
| B1 | `agency_instrumented` | DOC requiring agency artifacts | `fcsm-25-03` |
| B2 | `agency_instrumented` | DOC requiring agency artifacts | `schema-org-definedterm`; `w3c-dcat-3`; internal: this KG's Definition layer |
| B3 | `public` | AUTO/DOC; §6b.2 machine-first | **gap** |
| B4 | `agency_instrumented` | DOC requiring agency artifacts | `fcsm-23-02-a-framework-for-data-quality-case-studies`; `fcsm-20-04-a-framework-for-data-qual... |
| B5 | `agency_instrumented` | DOC requiring agency artifacts | **gap** |
| B6 | `agency_instrumented` | DOC requiring agency artifacts | **gap** |
| C1 | `paid` | EVAL — standing eval harness, named `paid` in §6b.1 | `from-accuracy-to-readiness-metrics-and-benchmarks-for-human` |
| C2 | `paid` | EVAL — standing eval harness | internal: probe protocol, `2026-08-27_chunked_vs_wholedoc_verdict.md` |
| C3 | `paid` | EVAL — standing eval harness | **gap** |
| C4 | `public` | EVAL/AUTO; the AUTO half runs against the public surface | `aggarwal-2024-geo-generative-engine-optimization`; `chen-2025-geo-how-to-dominate-ai-search` |
| C5 | `agency_instrumented` | DOC requiring agency artifacts | `aidrin-hiniduma-2024`; `data-readiness-for-ai-a-360-degree-survey`; `aidrin-2-0-a-framework-... |
| D1 | `public` | AUTO on public surface | **gap** |
| D2 | `agency_instrumented` | DOC requiring agency artifacts | **gap** |
| D3 | `agency_instrumented` | DOC requiring agency artifacts | **gap** — no PROV-O/W3C-PROV document is admitted; the skeleton's "PROV-aligned standards nod... |
| D4 | `public` | AUTO on public surface | **gap** |
| E1 | `agency_instrumented` | DOC requiring agency artifacts | `nist-ai-risk-management-framework-ai-rmf`; internal: this instrument's A/B/D vs C split |
| E2 | `agency_instrumented` | DOC requiring agency artifacts | internal: methodology §3; `nist-ai-rmf-playbook` |
| E3 | `agency_instrumented` | DOC requiring agency artifacts | internal: methodology §4 and §7.6 (instrument-version citation rule) |
| E4 | `agency_instrumented` | DOC requiring agency artifacts | `sainz-2023-llm-data-contamination` |
| E5 | `public` | AUTO on public surface | internal: DD-019 decoy discipline; methodology §7.5 |
| E6 | `paid` | EVAL — standing eval harness | **gap** |
| E7 | `agency_instrumented` | DOC requiring agency artifacts | **gap** |
| E8 | `paid` | AUTO/EVAL — scheduled re-runs are monitoring, named `paid` in §6b.1 | `webb-2026-state-fidelity-validity` |
| E9 | `paid` | EVAL — standing adversarial bank is a funded capability | `nist-generative-ai-profile-ai-600-1`; `nist-ai-risk-management-framework-ai-rmf` |
| F1 | `agency_instrumented` | DOC requiring agency artifacts | `odcs-open-data-contract-standard` |
| F2 | `public` | AUTO/DOC; §6b.2 machine-first | `odcs-open-data-contract-standard` |
| F3 | `public` | AUTO on public surface | **gap** |
| F4 | `public` | AUTO on public surface | `usafacts-ai-ready-data-guide` |
| F5 | `agency_instrumented` | DOC requiring agency artifacts | **gap** |
| F6 | `paid` | AUTO by type, but §6b.1 names attestation infrastructure as `paid`; the funded-capability rule governs | `slsa-specification-v1-0` |
| G1 | `agency_instrumented` | DOC+EVAL; the DOC half gates (EVAL half is `paid`) | `fcsm-23-02-a-framework-for-data-quality-case-studies`; DP documentation **gap** |
| G2 | `agency_instrumented` | DOC+EVAL; the DOC half gates | **gap** |
| G3 | `public` | AUTO/DOC; §6b.2 machine-first | **gap** |
| G4 | `agency_instrumented` | DOC requiring agency artifacts | `statistical-policy-working-paper-46-data-quality-assessment`; `fcsm-19-01-transparent-report... |
| G5 | `agency_instrumented` | DOC requiring agency artifacts | `usafacts-ai-ready-data-guide` |
| G6 | `agency_instrumented` | DOC+EVAL; the DOC half gates | `sdmx-3-0-section-1-framework`; `sdmx-standards-overview`; `odcs-open-data-contract-standard` |

---

## §3 — References

Added as skeleton §10 and as the brief's closing section, in three visually distinct classes:
**(a)** 36 admitted corpus documents, each with `doc_id` + sha256; **(b)** external sources not
admitted — the blocked Commerce guidance, and the two Databricks tools which §9 queues as
*evaluations, not adoptions* and which are cited as evidence nowhere; **(c)** internal artifacts —
tasks, verdicts, DDs, and the SFV DOI. Identifier order DOI > arXiv > stable URL is respected
throughout.

## §4 — The brief

`docs/crosswalk/usafacts_operationalization_brief.md`, **2,170 words of body prose** (~3.5 pages;
the reference apparatus is additional). Structure as specified: purpose; machine-first stance;
instrument shape (seven groups, counts, one exemplar row each, **tables not reproduced**); the 11
feedback items at one paragraph each; the novel contribution stated **once** (consumer-side EVALs —
producer-surface audits exist, consumer-behaviour audits do not); pilot plan and tier sequencing;
January milestone.

**§4.3 fair-characterization pass — done, and it changed the text.** I re-read every passage of the
guide that a feedback item targets before finalizing. Four critiques inherited from the skeleton
were too strong against what the document actually says, and were softened to the accurate claim:

| item | skeleton's framing | what the guide actually says | brief's framing |
|---|---|---|---|
| 5 (TEVV) | "Their ACCURATE criterion is **open-loop**" | It asks for internal review, automated validation, audit trails, **and** developer notification | "not open-loop"; the gap is the absent route from a failed eval back into the **data product**, plus thresholds, versioning, contamination policy |
| 2 (understandable) | "their current text **under-specifies** this" | It has a "Machine Understandable" criterion with dictionaries, taxonomies, ontologies, Data Cards, semantic labelling | "not a missing criterion"; what is missing is variable-level specification and a conformance test |
| 8 (uncertainty) | "**absent** from their guide" | It **does** address differential privacy and suppressed-data documentation — but under OPEN, as privacy protections | privacy safeguards ≠ uncertainty as structured fields; the distinction is stated rather than the absence asserted |
| 9 (machine-first) | implies the machine user is overlooked | The guide is machine-oriented throughout, incl. crawler-reachable documentation | "already machine-oriented in its intent"; the addition is derivation *order* plus agent-protocol surfaces |

Item 6 was **confirmed** rather than softened: the guide does say "standard schemas like NIEM and
Crossaint", NIEM is a justice/public-safety exchange standard, and "Crossaint" is Croissant. The
DCAT point is sharpened — the same section asks for improved centralized catalogs, and data.gov's
own profile is DCAT-US.

**§4.5 plagiarism self-check — `scripts/ngram_overlap_check.py` (new), 8-word shingles against all
8 admitted crosswalk source texts.**

```
usafacts_operationalization_brief.md:    2,170 words, 2,163 8-gram shingles
  NO unattributed 8-word overlap with any admitted source.  PASS
  QUOTED  [usafacts-ai-ready-data-guide] to find and correct potential abuse and misinformation
usafacts_operationalization_skeleton.md: 2,760 words, 2,753 8-gram shingles
  NO unattributed 8-word overlap with any admitted source.  PASS
total UNATTRIBUTED overlaps >= 8 words: 0
```

The check **found one real defect and it was fixed**: feedback item 11 originally reproduced the
guide's phrase "to find and correct potential abuse and misinformation" unattributed. It is now a
quoted, cited, 8-word quotation — inside the §4.1 limit of 25 words.

The check excludes reference entries and inline-code spans before comparing, on one principle: a
cited work's title and a `doc_id` are how this project *cites* a document and necessarily match any
source citing the same document. Stripping them aims the check at reproduced wording instead of the
citation apparatus. Both exclusions are commented in the script with that reasoning.

**Positive control (methodology §7.5 — no monitor is trusted until a seeded known-bad fires it).**
A paragraph lifted verbatim and unattributed from the guide's ACCESSIBLE bullets was appended to a
copy of the brief and the check re-run: **12 overlaps fired**. The check is load-bearing, not
decorative.

## §5 — Registration and close

- `DesignNote` `bd0c2848` — skeleton, `note_type: pattern_proposal`
- `DesignNote` `8caca908` — brief, `note_type: pattern_proposal`
- Both carry `provenance: cc_tasks/2026-08-29_crosswalk_operationalization.md` (see discrepancy 5:
  a graph edge to the task is not expressible for this artifact type).
- `seldon cc complete` → task `3d86f16d` state `completed`, run before this RESULT was written.
- Skeleton status line updated to **v0.2, 2026-08-29** with a "what changed" paragraph.

## Not done (task's own non-goals, unchanged)

v0.3.7 contract and extractor arms (ADDENDUM-01 §2–§3); the DD-024 instrument-version citation
check on the §3b semantic verdicts (rule 7.6); Lane 4 relocation; Lane 2/3; scoring rubric and
weights. **Nothing here was extracted into the graph** — these eight documents are corpus members
with document-level citations only. Span-level grounding for the crosswalk's cells waits on
v0.3.7, and the brief says so in its own "what this document does not claim" section rather than
implying the citations are span-verified.
