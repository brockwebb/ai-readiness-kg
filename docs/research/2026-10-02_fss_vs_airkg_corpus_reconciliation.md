# This corpus against the FSS policy graph: reconciliation and a definitional-lookup audit

**Task:** `cc_tasks/2026-10-02_commerce_guidance_admission.md` decisions 5 and 6, with ADDENDUM-01.
**Produced by:** `scripts/fss_airkg_reconciliation.py --phase reconcile` and `--phase audit`, zero model
calls, no network. Machine-readable rows: `docs/research/2026-10-02_fss_vs_airkg_corpus_reconciliation.csv`
(one row per FSS document) and `state/fss_vs_airkg_reconciliation_2026-10-02.json`,
`state/definition_lookup_audit_2026-10-02.json`. Screen calls: `scripts/fss_screen_2026-10-02.yaml`.

**What was read.** The FSS policy graph is the Neo4j database `fss-policy-kg` on this machine, the
projection of the `~/GitHub/icsp_notebook` repository (the task calls it `fss-policy-kg`; the
directory is `icsp_notebook`, its package `fss_policy_kg`). It was read in READ sessions only. The
hosted `fsskg` MCP server was not used, because the task declares `Network: none`; the local database
is the graph that server serves a copy of, and the two were not compared. This graph is
`seldon-ai-readiness-kg` after the Commerce admission's projection, and its corpus is
`corpus/manifest.json`.

## 1. Documents

Each of the 112 FSS `Document` nodes was matched to this manifest by primary URL (the FSS node's
`source_url`, the FSS ledger's `source_url` and `direct_download_url`, normalised for scheme, `www.` and a
trailing slash), then by the sha256 of the FSS repository's stored file against this manifest's
`identity.sha256`, then by normalised title (lower case, parentheticals and punctuation removed).

| | n |
|---|---:|
| FSS documents | 112 |
| matched to this manifest | 35 |
| by primary URL / content hash / normalised title | 30 / 3 / 2 |
| matched to an `included` entry here | 33 |
| matched to a `pending_refetch` entry here | 2 (`m_25_21`, `m_25_22`) |
| FSS-only | 77 |
| this corpus's `included` documents no FSS document matches | 233 of 265 |

Two FSS documents, `cipsea_2018` and `evidence_act_2018`, match the same entry here
(`foundations-for-evidence-based-policymaking-act-of-2018-evid`): CIPSEA 2018 is Title III of the
Evidence Act and the FSS graph holds it as a separate document at the same URL.

**The two `pending_refetch` matches are this task's own case again.** M-25-21 and M-25-22 are held by
the FSS graph as files and by this ledger as owed refetches; each could be fulfilled from the FSS copy
the way `generative-ai-and-open-data-guidelines-and-best-practices-de` was. Not done: decision 5 admits
nothing beyond decision 2.

## 2. The FSS-only documents, screened

Under rules R1 to R5 of `cc_tasks/2026-08-24_source_triage.md` (decision log
`docs/research/2026-08-24_triage_decision_log.md`). Each call cites the FSS graph's own text layer:
counts of segments containing `machine-readable`, `metadata`, `open data` and `dissemination` per
document, plus the segment quoted where the call turns on one.

| screen | n |
|---|---:|
| `include_candidate` | **6** |
| `excluded_by_rule` | 1 |
| `off_topic` | 70 |

**Candidates, for the operator** (none admitted):

| FSS id | title | clause | ground |
|---|---|---|---|
| `pra_1995_uslm` | Paperwork Reduction Act, 44 U.S.C. ch. 35 (codified, current) | R1 | carries the OPEN Government Data Act's definitions: `s43` defines "machine-readable", `s45` "open Government data asset"; `s231` requires every public data asset be machine-readable |
| `m_19_18` | M-19-18, Federal Data Strategy | R1 | data as a strategic asset; machine-readable and metadata practice |
| `omb_circular_a130` | OMB Circular A-130 (2016) | R1 | open-data and dissemination policy (`s16`); the FSS graph holds a partial extent, 28 segments |
| `spd_4` | SPD 4, Release and Dissemination of Statistical Products | R1 | dissemination of statistical products, 26 dissemination segments |
| `eo_14363` | EO 14363, Launching the Genesis Mission | R1 | federal data and model assets for AI "including digitization, standardization, metadata, and provenance tracking" (`s34`) |
| `acdeb_final_report_2022` | ACDEB Year 2 Report | R1 | metadata (18 segments) and discoverability (4) of federal data for evidence building |

Four of the six are R1 calls made under its own "err inclusive" instruction (A-130, SPD 4, EO 14363,
ACDEB); `pra_1995_uslm` and M-19-18 meet it on their subject.

**Excluded by rule:** `cipsea_2018_uslm`, R5 — the codified text of CIPSEA 2018, which this corpus holds
as Title III of the Evidence Act.

**Off topic** (70): agency enabling and confidentiality statutes (9), statistical classification and
survey SPDs (9), FCSM methodology working papers (10), OMB guidance on statistical administration,
privacy, quality and budget (16), other statutes (7), ICSP operations reports (5), Federal Register
notices (3) and the rest; each row's reason is in the screen file. Two borderline calls are named:
`naii_2020_15usc9401` and `ndaa_fy2019_s238g` define "artificial intelligence", not AI readiness, and R3's
"definitional statements" are readiness definitions.

## 3. Definitional-lookup audit

Five phrases, each looked up two ways in each graph: the **definition layer** (FSS: `Definition`
`term_surface` and `verbatim_text`, the layer `get_definitions` reads; here: `Definition` `term`,
`grounding_span`, `verbatim_text`) and the **text layer** (FSS: `Segment.text`, the layer
`search_text` reads; here: the grounding span of every node, since this graph keeps no segment nodes).
Matching is case-insensitive and tolerant of hyphen, space and doubled whitespace, because the FSS text
layer writes "AI  model" with two spaces and a literal search reports a statutory definition absent
for a space. A text-layer row "reads as a definition" when the phrase, optionally quoted and followed
by a footnote marker, is followed by `:`, `means`, `is defined as` or `refers to`; those rows are listed
in the state file so each call can be checked.

| phrase | FSS Definition (term / term or text) | FSS Segment (rows / docs) | FSS definitional text with no Definition of the phrase | here: Definition (term / term or text) | here: definitional span on a non-Definition node |
|---|---|---|---|---|---|
| AI-ready data | 0 / 0 | 15 / 3 | `doc_genai_open_data_2025#s583` | 6 / 10 | 1 (`uk-ai-ready-data-action-plan-2026::f_odi`, a Framework) |
| AI-readiness | 0 / 0 | 17 / 3 | `bea_rfs_mlmu25#s4`, `doc_genai_open_data_2025#s126` | 8 / 16 | 7 (Concept and Framework spans; none on inspection is a definition) |
| data readiness | 0 / 0 | 1 / 1 | — | 3 / 5 | 1 (`unsc-2026-stoyanovich-open-data-responsible-reuse::c_data_readiness`, a Concept; a slide bullet, not a definition) |
| machine-readable | 0 / 2 | 65 / 19 | `pra_1995_uslm#s43`, `cipsea_2018#s169`, `evidence_act_2018#s169`, `m_25_05#s61` | 7 / 18 | 0 |
| fitness for use | 0 / 0 | 19 / 10 | — | 0 / 6 | 0 |

**Findings about the FSS graph** (not fixed; this repository does not write it):

1. Its definition layer holds no definition of any of the five phrases. Two of them are defined in
   its text layer: "AI-ready data" by the Commerce glossary (`s583`), "AI-readiness" by BEA's
   `bea_rfs_mlmu25#s4` ("For the purposes of this project, 'AI-readiness' refers to the extent to which
   a data asset is prepared for …"), and "machine-readable" by the statute four times
   (44 U.S.C. 3502(18) as codified at `pra_1995_uslm#s43`, as enacted in the Evidence Act at
   `evidence_act_2018#s169` and `cipsea_2018#s169`, and as quoted by M-25-05 at `m_25_05#s61`). Its
   Definition layer does hold the neighbouring statutory term "open Government data asset"
   (`pra_1995_uslm#s45`), whose text contains "machine-readable" — one of the 2 in the table, the
   other being `iqa_guidelines_omb#s297`, "information dissemination product" — so the promotion
   step reached 44 U.S.C. 3502 and stopped one definition short. `doc_genai_open_data_2025#s126`
   is a false positive of the pattern (a list of topics), kept in the table because the rule is the
   rule.
2. The Commerce document has 778 segments and no Definition at all, though its appendix A1 is 49
   glossary entries; 43 of the 49 entries' openings are found in a segment
   (`docs/research/2026-10-02_commerce_guidance_two_pipelines.md`).

**About this graph.** For these five phrases the definition layer finds what the text layer finds:
no grounded span here reads as a definition of one of them while sitting on a node other than a
Definition. "Fitness for use" is defined in six Definitions' text but is no Definition's term.

## 4. Limits

The FSS side was read from the local database and the FSS repository's ledger; the hosted MCP copy
may differ. The title match is a normalisation, not a fuzzy match, so a document whose two ledgers
title it differently and whose URL and bytes both differ is reported FSS-only. The screen applies the
2026-08-24 rules as written to titles and to the FSS text layer, which for some documents (A-130, 28
segments) is a partial extent; a candidate is a candidate, never an admission.
