# RESULT — Acquisition round 2 (SEO/AI-O/GEO cluster, reference-driven expansion, evaluated cuts)

**Task:** `cc_tasks/2026-08-30_acquisition_round2.md` · **Date:** 2026-08-30 · **Model spend: ZERO.**
Metadata APIs (OpenAlex keyed, Crossref, arXiv, IETF datatracker), direct HTTP retrieval,
deterministic parsing, code and tests. No `model_stub` call was made or attempted.

**Headline:** corpus **178 → 194 included** (16 admitted). **24 candidates cut**, every one with a
standing-rule clause. Reference lists rose from **2 documents to 57** by parsing the documents'
own bibliographies, which took the coupling ranking from "no candidate reaches the bar" to two
above it — one of which the corpus already held under a different identifier, and only because
that parse existed was the duplicate visible at all.

---

## 0. Discrepancy reported, not reconciled: a concurrent session owns the chunked pilot

This session was asked to execute **both** `2026-08-27_chunked_pilot_ADDENDUM-04` and this task.
On starting, Arm A3 was **already in flight** — `pilot_v039_arm_a3_haiku`, pid 42603, started
12:27Z, not this session's. Session `ai-readiness-kg-03` confirmed on request that A3 is **its**
work end to end, and that ADDENDUM-**05** and **06** exist and modify -04's closure; this
session had globbed only four addenda because -05 and -06 postdate its dispatch.

**Nothing in this RESULT touches the pilot.** No shard, profile, template, raw dir, metrics dir
or judge run was read or written. The one shared file is the append-only, `flock`-protected
`state/spend_ledger.jsonl`, and this task declared no run on it because it spent nothing.

A3's outcome is recorded here only because it bears on this task, and it is **that session's
reported number, not one this session measured**: A3 came in **UNDER-EXTRACTION** (25.34
admitted/chunk, ratio 0.5603 against the 0.60 floor), which selects ADDENDUM-04 §2.4's FAIL
branch, so the ADDENDUM-06 held-out confirmation does not run. Had it run, it would have
drawn a stratified sample keyed on the manifest — and this task changed the manifest under it.
**That collision did not occur, but it is real:** any future held-out draw needs a pinned
manifest snapshot, because acquisition is now a live process. Recorded for whoever revives it.

---

## 1. Feeding the coupling engine — reference parsing from the Docling output

### Prior art (searched before building)

Reference-string parsing is a named, solved problem: **ParsCit** (Councill et al., LREC 2008),
**GROBID** (Lopez, ECDL 2009), AnyStyle, and Crossref's `query.bibliographic` reconciler. The
mature tools are ML sequence labellers over PDF layout. GROBID is deliberately absent from this
environment's provider ladder (`kg.biblio.biblio_method` says so in the data, not only in prose),
and a labeller is a model call, which §6 puts out of scope.

What was built is therefore **not a cheap approximation of ParsCit** — it is the sub-problem the
field treats as trivial and which is exactly recoverable without a labeller: **identifiers**. A
DOI is a regular language (ANSI/NISO Z39.84; Crossref's recommended match
`10.\d{4,9}/[-._;()/:A-Za-z0-9]+`, Crossref blog 2015-08-11, adopted verbatim), and so is an
arXiv id. Titles and years are returned as **explicitly flagged guesses** and **no ranking reads
them** — the field's answer for those is a sequence labeller and this module does not pretend
otherwise.

### `kg/refparse.py` — new, deterministic, 22 tests

Evidence class **`bibliographic_derived`**, `derivation: docling_refparse`, with the source
markdown's sha256 and the section's byte offsets on every record (`state/refparse/*.json`, one
per document). **Never pooled with `bibliographic`.** The two fail differently — a third-party
index can be wrong about a document; our regex can be wrong about a page — and the candidates
file carries both counts separately on every row.

### Measured, over all 194 admitted documents

| | |
|---|---|
| documents parsed | **194** |
| with a reference section | **57** (was **2** with an index-supplied reference list) |
| reference entries split | **2,158** |
| DOIs recovered | **336** |
| arXiv ids recovered | **177** |
| entries with no identifier | **1,663** (77%) |
| documents contributing ≥1 identifier | **41** |

Section-split strategy, recorded per document so a bad parse is diagnosable from the record
rather than by re-running: `markdown_list` 41, `paragraph` 11, `numbered` 5.

The 77% no-identifier rate is **not** a parse failure and is not reported as one: gray and
government literature cites by URL and title, and there is no DOI in the text to find. The
ranking consumes identifiers, so an entry without one costs recall and asserts nothing false.

Richest documents: `data-readiness-for-ai-a-360-degree-survey` (150 entries, 55 DOI + 13 arXiv),
`scihorizon-qin-2025` (104 / 37 / 5), `webb-2026-state-fidelity-validity` (47 / 31 / 12),
`elnaffar-2026-agent-ready-websites` (49 / 24 / 6).

### Three defects the live corpus produced, each now a test with a positive control

Each is a **false-coupling** defect — a wrong candidate — not merely a lost one, which is why
each is guarded rather than tolerated:

1. **Docling escapes markdown metacharacters.** A TACL DOI arrives as `10.1162/tacl\_a\_00471`;
   the backslash is outside the DOI charset, so an unescaped match stops at `10.1162/tacl`.
   Three documents citing three *different* TACL articles collapsed onto the bare journal prefix
   and it **reached the top of the ranking as a 3-citer candidate** before the guard existed.
2. **A DOI cut at a line break is a prefix of a real one.** `https: //doi.org/10.18653/v1/` →
   `10.18653/v1`. Admitted, it resolves to nothing or to the wrong work. Dropped, with the
   trailing-slash rule and a mutation check proving the syntactic `fullmatch` alone would admit it.
3. **A truncation that looks completely valid.** `10.18653/v1/2023. emnlp-main.153` leaves
   `10.18653/v1/2023`, which passes every syntactic check and collided into a phantom 2-citer.
   Only the *same bibliography's* full form reveals it. **A general de-space repair was
   considered and rejected**: joining across a space also glues genuine sentence continuations
   (`10.1145/3168389. Springer`), trading a visible miss for an invisible wrong answer. The
   prefix rule can only decline an identifier, never invent one.

Also fixed: `## Appendix B. References` and RFC-style `Normative References` headings were
invisible to the first pattern, costing four documents' reference lists.

### Coupling re-run over the enlarged set

`kg.biblio.coupling_candidates` now unions both evidence classes, keeping the counts separate,
and covers arXiv ids as well as DOIs. `docs/corpus/acquisition_candidates.md` is regenerated with
the required columns (candidate, score, citing docs, OA status, fetchable vs
`manual_download_needed`) plus a **disposition** column, so the file is a decision record rather
than a queue.

| | round 1 | round 2 |
|---|---|---|
| documents with a reference list | 2 | **57** |
| distinct non-corpus works cited | 100 DOIs | **525** works (DOI + arXiv) |
| **at or above the ≥3 bar** | **0** | **2** |
| near-miss at 2 citers | 0 | **20** |
| 1-citer tail | 100 | **503** |

**The bar was not moved.** It was unreachable at 2 documents of reference coverage and is
reachable at 57 — which is a statement about coverage, exactly as the round-1 file said.

---

## 2. SEO / AI-O / GEO cluster

Searched: arXiv API (`generative engine optimization`, `answer engine optimization`, AI-search
visibility, `llms.txt`, AI crawlers, agentic web), OpenAlex (keyed), Crossref, IETF datatracker,
and direct probes of the gray-literature hosts this cluster lives on.

**The operator's read was right and the gap is larger than "under-represented":** the corpus held
three GEO papers (Aggarwal 2023, Chen 2025, Wu 2025) and four audits, and **nothing at all** from
the 2026 wave — one arXiv query alone returns thirty 2026 GEO papers. It also held **no AEO work**
under that name.

Bounding this was the actual problem, not finding it. §3 says the default is cut and
"ever-expanding graphs are trash". The rule applied is **R1 as written** — primary subject is
machine consumption of published content — with one discriminator taken from the graph's own
purpose: **admit works carrying a definition, a survey of the field's constructs, or a
measurement instrument; cut works that optimize or attack one technique.** The graph is a
validity layer, not a toolbox. That is R1 plus R2's method/framework distinction, not a new rubric.

### Admitted — cluster literature (9)

| doc_id | why it is not one of the thirty |
|---|---|
| `martinez-2026-geo-critical-survey` | The field's terminological survey, 45 studies Nov 2023–Jul 2026. States outright that "terminology, metrics, and evidence standards remain heterogeneous" — that heterogeneity *is* this graph's subject for the GEO arm. |
| `zhang-2026-citation-selection-absorption` | Two-stage measurement framework (selection vs absorption) over 21,143 citations across three platforms. An instrument with a construct decomposition. |
| `schulte-2026-dont-measure-once` | A **reliability** claim about the cluster's instruments: AI-search visibility is stochastic, so a one-off observation is not an estimate. No other held document states it. |
| `watanabe-2026-aeo-referral-natural-experiment` | The only AEO-named measurement located, and it separates the intervention from platform growth — the confound practitioner AEO claims ignore. Closes the AEO half of the gap. |
| `elnaffar-2026-agent-ready-websites` | A readiness **framework** for machine consumption of a published surface, with named dimensions, and the explicit claim that SEO/GEO metrics do not assess agent-mediated interaction. |
| `liu-2023-evaluating-verifiability-generative-search` | Defines citation recall / citation precision — the constructs the held audits measure against. Two held documents cite it; admitting it closes a dangling definition. |
| `kumar-2024-manipulating-llms-product-visibility` | The strategic-text-sequence result both held GEO papers cite. The adversarial boundary of publication actionability. |
| `chu-2026-geo-flag` | Detection instrument + benchmark for whether a page has been GEO-optimized: the measurement counterpart to the row above. |
| `grossman-2026-how-genai-disrupts-search` | 11,500-query public benchmark over Google / AI Overviews / Gemini. Primary measurement of what the held commentary asserts without measuring. |
| `volpini-2026-structured-linked-data-memory-layer` | Controlled experiment on whether schema.org markup improves agentic retrieval. The corpus holds seven schema.org type pages as normative surfaces and had **no measurement** of whether publishing them changes machine consumption. |

### Admitted — normative specs and platform documentation (4)

| doc_id | why |
|---|---|
| `ietf-aipref-vocab-draft` | `draft-ietf-aipref-vocab-07`, WG-adopted. The IETF successor to ad-hoc robots.txt AI directives. The corpus held RFC 9309, Web Bot Auth and llms.txt but not the work that supersedes their AI-preference semantics. |
| `ietf-aipref-attach-draft` | `draft-ietf-aipref-attach-05`. Admitted with the vocabulary because the vocabulary alone does not say **where a publisher puts it**, and the crosswalk's question is what a publisher must do. |
| `rsl-1-0-specification` | Really Simple Licensing 1.0: machine-readable licensing with bindings to robots.txt, HTTP headers, HTML, RSS and media. The licensing surface AIPREF deliberately does not cover. |
| `cloudflare-pay-per-crawl` | Kernel clause (b), platform-official CDN documentation. The HTTP 402 machine-payable crawl mechanism — a distinct access surface from the held AI Crawl Control overview and Content Signals Policy. |

Gray-literature bar held: primary sources only. No commentary, no explainer-of-a-spec.

### Admitted — coupling near-miss, evaluated individually (2)

| doc_id | why |
|---|---|
| `holland-2018-dataset-nutrition-label` | A general, cross-domain diagnostic framework for pre-model data quality — R2's named include class. The dataset-label lineage the corpus carried for FAIR and Croissant but not for labels. |
| `gebru-2021-datasheets-for-datasets` | The canonical dataset-documentation standard. Held documents cite it as the reference for what metadata a dataset must carry, and the crosswalk had **no primary source** for that claim. |

---

## 3. Evaluation — 40 candidates, 40 decisions, nothing pending

`scripts/round2_list_2026-08-30.yaml` carries one entry per evaluated candidate with its verdict
and the standing-rule clause. **16 fetched and admitted, 24 cut.** Every cut is a manifest record
with its rationale verbatim (`corpus/manifest.json`, `excluded` 26 → 50), not a deletion.

### The cut list, verbatim

| candidate | clause | reason |
|---|---|---|
| `kumar-2026-geo-at-scale` (arXiv 2606.20065) | `R1_no_marginal_contribution` | Brand-visibility measurement across engines. Its construct decomposition is contained in the citation selection/absorption framework and its reliability point in "Don't Measure Once". |
| `vishwakarma-2026-what-gets-cited` (arXiv 2605.25517) | `R1_method_not_construct` | A controlled two-document RAG testbed measuring which of two sources is cited first. A mechanism experiment over 18 content factors, not a definition or a field-level instrument. |
| `yu-2026-geo-structural-feature-engineering` (arXiv 2603.29979) | `R1_method_not_construct` | GEO-SFE is an optimization method for improving one's own citation rate. The graph's target is what AI-readiness IS and how it is measured, not the toolbox for raising a score. |
| `luettgenau-2025-beyond-seo-transformer` (arXiv 2507.03169) | `R2_domain_application` | A BART fine-tune on 1,905 travel-website content pairs. The exact class R2 names for exclusion. |
| `jacques-2026-authority-signals-health` (arXiv 2601.17109) | `R2_domain_application` | Authority-signal framework instantiated for health information seeking. The corpus already holds a health-domain AI-Overviews audit. |
| `wen-2026-geo-governance-position` (arXiv 2606.12439) | `ambiguous_contribution` | **Operator review.** Formalizes a general GEO pipeline, but its contribution is a governance position, and a position paper is argument rather than definition or measurement. |
| `borysenko-2026-ai-agent-http-signatures-docs` (arXiv 2604.02544) | `ambiguous_contribution` | **Operator review.** Measures how nine coding agents and six assistant services actually fetch a documentation portal, including llms.txt handling — genuinely R1-shaped measured practice. Cut because it is one author studying one live endpoint, so it does not generalize to a publisher's decision. |
| `a2a-protocol-specification` | `R1_out_of_scope` | Agent-to-agent transport and task delegation. Not a surface on which published data is exposed to machine consumers; the corpus holds MCP, WebMCP and NLWeb for the data-exposure side. |
| `ibm-2021-data-quality-toolkit` (arXiv 2108.05935) | `ambiguous_contribution` | **Operator review.** A general (non-domain) toolkit scoring data quality for ML, so instrument-shaped under R2; cut because its metrics are already represented by AIDRIN and AIDRIN 2.0. |
| `li-2021-cleanml` (arXiv 1904.09483) | `ambiguous_contribution` | **Operator review.** Evidence for the readiness-matters premise, but it measures a preprocessing intervention rather than defining or operationalizing a readiness construct. |
| `aif360-2018-ai-fairness-360` | `R4_off_construct` | A fairness-mitigation toolkit. Fairness is a property the held instruments reference; the toolkit defines no readiness construct. |
| `celis-2019-preprocessing-mitigate-bias` | `R2_domain_application` | A specific preprocessing method, stating no general readiness framework. |
| `cobbe-2021-training-verifiers-gsm8k` | `R4_off_construct` | LLM training and the GSM8K benchmark. Cited by a held contamination paper for its benchmark, not for data readiness. |
| `duddu-2021-shapr` | `R4_off_construct` | A membership-inference privacy metric — privacy risk of a trained model, not readiness of published data. |
| `nakano-2021-webgpt` | `R4_off_construct` | A model paper. Ancestor of the systems the GEO cluster audits, but it asserts nothing about how publishers make content machine-consumable. |
| `carlini-2022-privacy-onion-effect` | `R4_off_construct` | Training-data memorization. |
| `zheng-2025-deepresearcher` | `R4_off_construct` | An RL training method for research agents. The corpus holds DeepTRACE for auditing such agents' citation behaviour, which is the readiness-relevant half. |
| `ortigosa-2017-class-imbalance-extent` | `R4_off_construct` | An ML class-imbalance metric. AIDRIN cites it as a score input; the metric is not a readiness construct. Closed access besides. |
| `zhu-2018-lrid` | `R4_off_construct` | As above: an imbalance metric cited as a score input. |
| `jumper-2021-alphafold` | `R4_off_construct` | A scientific application, cited by two members as an AI-for-science exemplar. Exemplar citation is not a readiness claim. |
| `kaaniche-2020-is-entropy-enough-privacy` | `R4_off_construct` | A privacy-measurement note cited as a score input. Off-construct and closed access. |
| `blake-2010-data-quality-problem-complexity` | `R1_no_marginal_contribution` | A 2010 study of data quality vs classification performance; its finding is carried, with fifteen further years of evidence, by the held 360-degree survey. |
| `azzalini-2022-e-fair-db` | `R4_off_construct` | A functional-dependency method for finding bias in a database. Method, not construct. |
| `hatem-2023-hallucination-or-confabulation` | `R4_off_construct` | A terminology note on LLM error naming. Says nothing about data or publication readiness. |

The **503-work 1-citer tail** is cut en bloc as `below_coupling_bar` and deliberately not
enumerated: one citer is one document's bibliography, not coupling. The identifiers survive in
`state/refparse/*.json`, so the tail regenerates if the bar or the coverage changes.

### Operator-review section (four `ambiguous_contribution` cuts)

Per §3, ambiguity was cut, not admitted, and listed rather than buried:
`wen-2026-geo-governance-position`, `borysenko-2026-ai-agent-http-signatures-docs`,
`ibm-2021-data-quality-toolkit`, `li-2021-cleanml`. All four are open-access and fetchable; each
has a defensible R1/R2 reading. The default was applied. **A `manifest_add` reverses any of them
in one command; no re-derivation is needed.**

### `manual_download_needed`

**Empty for round 2.** Every admitted candidate was open access and fetched. Five closed-access
works appear on the near-miss list (`10.1016/j.patrec.2017.08.002`, `10.1109/csci51800.2020.00249`,
`10.1145/1891879.1891881`, `10.1145/3552433`, `10.14445/22492615/ijptt-v9i1p402`) and are **cut on
their merits, not on their paywall** — no operator fetch is requested for any of them.
`docs/corpus/operator_pickup.md` is unchanged at 5 pre-existing rows.

---

## 4. Downstream — T0, T1, `t2_priority`

| step | before | after |
|---|---|---|
| manifest `included` | 178 | **194** |
| manifest `excluded` | 26 | **50** |
| T0 resolved / eligible | 40 / 46 | **52 / 58** |
| T1 Docling markdown | 178 | **194** (16 converted, 0 failed, 168 s) |
| T1 chunks / FTS / embeddings | — | **5,630 / 5,630 / 5,630** |
| `t2_priority` rows | 178 | **194** |

All 16 admits carry `crosswalk_demand = 0` and `t0_centrality = 0`, which is correct and not a
defect: they are named by no crosswalk cell and cited by no held document — they are new
acquisitions, and centrality is a lagging measure of them.

**No extraction was dispatched.** The bulk decision waits on the pilot's §3, per ADDENDUM-04.

### Four defects found and fixed downstream (each now a test)

1. **`t1_build_index.local_path` hardcoded the corpus document directories** — a literal tuple
   duplicating `dixie_evidence.yaml document_dirs`, in violation of the standing no-hardcoding
   rule. All 16 admits reported as `MISSING` with no diagnostic naming the cause. It now reads
   the config, and prefers the manifest's own `canonical_path` when dixie has verified one.
   Three tests, including a mutation check that fails if the list is re-hardcoded.
2. **`source_type: platform` is not in the doc_type enum.** The Cloudflare page was refused at the
   manifest gate; re-admitted as `industry`, the type every held platform-operator page carries.
3. **The IETF drafts were captured as the HTML *rendering* under a `.md` name.** The integrity
   gate's magic-bytes check correctly quarantined both. Refetched as the canonical Internet-Draft
   plain text and superseded through `manifest.content_update(reason="corrupt_source_replaced")`
   — the sanctioned path; **the admission events were not edited** (invariant 1).
4. **`kg.biblio` wrote its enrichment cache into `state/biblio_cache/`,** which `records()` globs
   for per-document T0 records; the sidecar was then read as a document with no `doc_id` and
   crashed `recompute`. Moved to `state/candidate_oa.json`.

Two of the three admissions that stalled at `pending_refetch` did so for a **correct** reason
recorded at the time. Both were re-decided `included` by an appended `screening_decided` event
whose rationale names the content_update that fixed the artifact — the ledger reads forward, and
nothing was rewritten.

---

## 5. The finding worth keeping: the parse made a duplicate visible that identifiers could not

The coupling engine's new top rows are the interesting output, not the admissions.

**`10.18653/v1/2023.findings-emnlp.467` reached 3 citers and topped the ranking as a work to
acquire — hours after this same task admitted it** as `liu-2023-evaluating-verifiability-generative-search`.
Identifier matching cannot catch it: the corpus holds the **arXiv preprint** (2304.09848), the
candidate is the **EMNLP Findings DOI**, and OpenAlex models those as two different works with
two different DOIs. R5 dedupe by URL/DOI passes them both.

Fixed by giving `corpus_identifiers()` a normalized-title index (the same normalization the T0
harvester already uses) and having the candidate row carry **`held_title_match`** — it **marks**
the row rather than deleting it, because title matching is fallible and this repo has the scar:
the FAIR "Faculty Opinions recommendation of …" wrapper match. A flagged row is evidence a human
can overturn; a deleted row is not.

**`arXiv:2112.09332` (WebGPT) is now the top candidate at 4 citers and stays cut.** Crossing the
coupling bar is new evidence about *salience*, not about *construct fit*; the R4 cut names its
subject, and its subject did not change. Recorded explicitly because "cuts are terminal absent
new evidence" needs to say which evidence would reopen a cut — and this is not it.

**The reflexive effect is real and worth stating:** admitting 16 documents changed the ranking
that recommended them, because their bibliographies now feed it. Round 3's candidate list is
downstream of round 2's admissions. That is how coupling works, and it means the ranking is a
*generator* whose output must be re-evaluated each round — never a standing queue.

---

## 6. Files

**New:** `kg/refparse.py`, `tests/test_refparse.py` (22), `scripts/round2_list_2026-08-30.yaml`,
`events/batch-020.jsonl`, `docs/research/2026-08-30_round2_manifest_summary.json`, this file.
`state/refparse/*.json` (194) and `state/candidate_oa.json` are **gitignored**, on the same rule
as `state/biblio_cache/` and `state/docling_md/`: rebuildable projections (`python -m kg.refparse`
regenerates them), never sources of truth. The decisions they feed are tracked —
`corpus/manifest.json`, `events/batch-020.jsonl`, `docs/corpus/acquisition_candidates.md`.

**Changed:** `kg/biblio.py` (two evidence classes, arXiv coupling, OA enrichment, title dedupe,
decision-carrying candidates file), `scripts/harvest_triage.py` and `scripts/manifest_triage.py`
(`--list`/`--inbox`/`--register`/`--doc-dir`/`--batch`/`--epoch`/`--source-id`/`--task` —
**parameterized, not copied**: the paywall reclassification, the resume-on-sha rule, the
dedupe-by-doc_id/sha/url gate and the sweep-before-register ordering are exactly the invariants a
second copy would drift on), `scripts/t1_build_index.py` (config-driven document dirs),
`tests/test_t0_t1_substrate.py` (+3), `dixie_evidence.yaml` (`round2` document dir),
`.gitignore` (`corpus/round2/`), `docs/corpus/*` (regenerated).

**Seldon:** five `DataFile` artifacts registered with content hashes —
`acquisition-candidates-round2`, `corpus-manifest-round2`, `round2-candidate-list`,
`refparse-derived-references`, `round2-manifest-summary`.

**Tests: 421 passed** (`python -m pytest tests/ -v`), measured 2026-08-30 after this task's
25 new tests landed. The absolute count also moves with the concurrent pilot session's edits
to `tests/test_v037_arm.py`, so the number that belongs to this task is the 25, not the total.

## 7. Out of scope, and untouched

No model call. No extraction. No relevance summary written by a model. No change to the admission
rules — R1–R5 are applied as written and quoted where applied. No pilot shard, profile or template
touched.
