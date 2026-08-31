# Extract-worthiness rubric — ground-truth annotation for the yield floor

**Task:** `cc_tasks/2026-08-30_ground_truth_yield_floor.md` §1.
**Status:** IMMUTABLE for that task once sha-pinned. A defect found mid-task is reported and
the task stops; it is not patched in flight, because patching a rubric after seeing annotations
measures the patch (task §5).
**Standing:** the pilot's §3 closure recorded that the yield floor's target — 45.23 admitted
items per chunk, from the unvalidated chunked v0.3.5 arm — is a tripwire and not a validity
criterion. This rubric exists so that a floor can be derived from measured value instead.

**This rubric is derived, not invented.** Every rule below cites the source it comes from, in
the priority order the task fixes: schema first, consumers second, published annotation
guidelines third. Where they conflict, the schema wins.

---

## 0. The question an annotator answers

For one chunk of one primary-source document, and **for the chunk text alone**:

> Which items in this passage is the document *asserting something about*, such that a
> downstream consumer could query them and get an answer the document actually supports?

Not "what nouns appear here." Not "what is this passage about, loosely." The unit of judgment
is an **item** — a candidate node with a type from §1 and a name taken from the document.

---

## 1. Source 1 — the schema (highest priority)

`kg/schema.yaml`, schema_version 0.3.4. An item is extract-worthy **only if** it is typable as
one of:

`Definition`, `Concept`, `Instrument`, `Measure`, `Claim`, `Standard`, `Framework`,
`Practice`, `Tool`, `Platform`.

Two exclusions from the catalogue, both from the schema itself:

- **`Construct` is never annotated.** A Construct is a Concept promoted to measurability by an
  explicit operator decision, not an extraction decision (schema §6; stated in the extraction
  templates).
- **`Document` is never annotated as an item.** It is the container.

### 1.1 The assertion test (the seed rule)

Seed text, verbatim from `kg/extraction/prompt_template_v0_3_8.md` and `_v0_3_9.md`:

> **Salience, not exhaustiveness.** Extract the schema-typable items this chunk **asserts
> something about** — the ones a reader would say the passage is *about*. Do not inventory
> every noun. An exhaustive list is not wanted and is not measured: completeness of recall is
> not gated, so do not spend output on it.

Operationalized for annotation: an item is extract-worthy iff the chunk asserts, about that
item, at least one of —

- a **property** the schema lists for its type (an Instrument's `owner`/`year`/`method`; a
  Measure's `response_type`/`tier`; a Standard's `steward`/`version`; a Practice's `scope`);
- a **definition** (the document says what the term means);
- a **measurement** (the document reports what the item measures, or what was measured of it);
- a **relation** to another item in the same chunk, stated in the text.

A passage that merely **names** an item, with nothing a span can carry, yields a
**mention-only stub** — which is *not* extract-worthy as a typed item. This is the schema's own
mention/node distinction, not a threshold introduced here.

### 1.2 The name is the document's

The item's name is the **surface form the document uses**, verbatim, capitalization included.
An annotator's preferred or canonical name goes in aliases, never in the name field. This is
the FIRST GROUNDING RULE of `kg/extraction/prompt_template.md`, restored to the chunked
templates as `v0_3_8`; annotation is held to the same rule the extractor is held to, or the
comparison is unfair in the extractor's disfavour.

---

## 2. Source 2 — the consumers

`docs/crosswalk/usafacts_operationalization_skeleton.md` (v0.2) and its brief define the only
declared consumer of this graph: **an indicator evidence cell**. The skeleton's own contract:

> **Evidence** — corpus doc_ids grounding the indicator's claim to matter. Empty = registered
> gap … **No cell is filled without a doc_id.**

and, per DD-024 discipline recorded there, *every filled cell carries a doc_id + grounding span
captured at adjudication.*

### 2.1 The consumer test

An item is extract-worthy only if some indicator evidence cell could **cite it**. Concretely,
the 45 indicators across groups A–G query for:

| the consumer needs | the item type that supplies it |
|---|---|
| an assessment/index/benchmark and who runs it, when, how | `Instrument` + `owner`/`year`/`method` |
| a single scored item, and who can run it | `Measure` + `tier` |
| what a term means, and with what normative force | `Definition` + `normative_status` |
| a falsifiable statement with a subject and a stake, and how well evidenced | `Claim` + `evidence_grade` |
| a spec or conceptual structure an indicator aligns to | `Standard`, `Framework` |
| a normative recommendation about publishing data for machines | `Practice` + `scope` |
| software that runs a measure; a machine consumer targeted | `Tool`, `Platform` |

**If no row of that table could be answered from the item, the item is not extract-worthy** —
however real the noun phrase is.

### 2.2 The stake test for Claims

A `Claim` is extract-worthy only if it has **a subject and a stake**: it says something
falsifiable *about* a named thing, such that a reader could disagree. A restatement of the
passage's topic with no assertive content is not a Claim.

---

## 3. Source 3 — published annotation guidelines, adapted

Each rule names what it is adapted from. Where our schema diverges, the schema wins (task §1).

### 3.1 Mention ≠ entity assertion, and generic ≠ specific
**Adapted from ACE 2005 English Entities guidelines (LDC), entity class SPC / GEN / USP.**
ACE labels a noun phrase SPECIFIC when it refers to a precise member of a category and GENERIC
when it refers to any member; ACE-2005 adds NEG and USP for negatively-quantified and
underspecified referents.

**Adopted:** an item referred to only generically — a category noun standing for any member —
is **not** extract-worthy. `data quality` used as a topic word is GEN; `the Data Quality
Toolkit (DQT)` is SPC. **Divergence recorded:** we do not carry a specificity attribute; ACE
tags genericity, we *exclude* on it, because our consumer (§2) cannot cite a generic.

### 3.2 The most specific span, and the document's own words
**Adapted from SciERC (Luan et al. 2018, EMNLP), which annotates scientific abstracts with six
entity types — Task, Method, Metric, Material, Other-ScientificTerm, Generic — over
most-specific spans.**

**Adopted:** the annotated name is the most specific contiguous span the document uses for the
item. **Divergence recorded:** SciERC has a `Generic` *type* for non-specific mentions; we have
no such type, so those items are excluded under §3.1 rather than typed. Our type catalogue is
the schema's (§1), not SciERC's — the domains differ.

### 3.3 Justification, and no outside knowledge
**Adapted from TAC KBP slot-filling assessment guidelines (NIST, 2012–2015).** Two rules there,
both directly applicable:

> All fillers must be supported in the provided predicate justification strings or their
> surrounding context … If a filler cannot be justified solely by the justification strings or
> their surrounding context, it should not be labeled as correct, **even if you know it to be
> true because of an outside information source.**

> the provenance … must contain text that justifies the extracted relation, and it must include
> some mention of the subject and object entities and some text supporting the slot/predicate
> that connects them.

**Adopted, both.** An annotator must not credit an item, or an attribute of one, from world
knowledge — only from this chunk's text. And a relation is annotated only where the text
contains both endpoints and the predicate.

**Convergence worth recording:** the second rule is, independently, the repo's existing
v0.3.4 semantic-edge rule (`kg/extraction/parser.py::_semantic_span_violation`). The repo
re-derived a TAC KBP guideline from its own probe failures. That is prior art that was
available and was not consulted at the time.

---

## 4. Negative rules — what is NOT extract-worthy

Examples are **real**, taken from the set-difference sample already recorded in
`cc_tasks/2026-08-27_chunked_pilot_RESULT.md` (items the v0.3.5 arm proposed and later arms did
not). They are listed there with their source spans.

| # | Not extract-worthy | Real example | Rule |
|---|---|---|---|
| N1 | **Section headings and titles** — page structure is not an assertion | `Quantitative Assessment of Data Readiness for AI` (aidrin c0003) | §1.1 — a heading asserts nothing about the item |
| N2 | **Bare category nouns** used as topic words | `AI training` (dr c0001), `unbiased data` (dr c0002), `Quantitative variable` (dr c0009), `Relational database table` (dr c0006) | §3.1 GEN |
| N3 | **Table, figure and column labels** | `Bias Indicator` (dr c0006) | §1.1 + §2.1 — no consumer row |
| N4 | **Fragments** cut mid-word or mid-clause | `to binary-sensitive attributes, leaving non-binary attributes unad-` (aidrin c0011) | §1.2 — not a surface form the document uses for an item |
| N5 | **Topic restatements with no stake** | `biases or limitations in the data` (dr c0013) | §2.2 |
| N6 | **Incidental proper nouns** — an author, venue, affiliation or funder named in passing | citation author names in a references block | §2.1 — no consumer row |
| N7 | **Boilerplate** — copyright, licence lines, running heads, page numbers | — | §1.1 |
| N8 | **Items known from world knowledge but not asserted here** | an instrument's method the reader knows but the chunk does not state | §3.3 |
| N9 | **`Construct` nodes** | — | §1, operator decision not extraction |
| N10 | **Coreference-only mentions** — a pronoun or "the tool" with no independent surface form | — | §1.2 |

---

## 5. Positive rules — what IS extract-worthy

| # | Extract-worthy | Rule |
|---|---|---|
| P1 | A **named instrument** with at least one attribute-bearing sentence (its method, owner, year, inputs, or outputs) — including one merely *surveyed* by a review paper, where the survey's own text carries the attribute | §1.1, §2.1; matches the v0.3.5 Instrument positive criterion |
| P2 | A **measure or metric** the document describes as scored, computed or reported | §1.1, §2.1 |
| P3 | A **definition** the document gives for a term, in the document's words | §1.1, §2.1 |
| P4 | A **claim** with a subject and a stake, falsifiable from the passage | §2.2 |
| P5 | A **standard or framework** the document names *and* says something about | §1.1 |
| P6 | A **concept the document defines, decomposes, or asserts a property of** — not one it merely uses | §1.1 vs §3.1 |
| P7 | A **practice**: a normative recommendation about publishing/structuring data for machine consumers, with an asset scope | §1.1, §2.1 |
| P8 | A **tool or platform** named as implementing a measure or as a targeted machine consumer | §2.1 |

---

## 6. Annotation output contract

Per chunk, a list of items, each: `name` (document's surface form, verbatim), `type` (from §1),
`evidence` (the sentence or clause carrying the assertion, copied from the chunk), and
`rule` (the P-number from §5 that admits it). An item without a citable P-rule is not admitted.

**Uncertainty is recorded, never resolved silently.** An annotator unsure whether an item meets
§1.1 marks it `uncertain: true` with the reason; reconciliation (task §3.3) decides, and
unresolvable items are excluded *and counted* as annotation uncertainty.

---

## 7. Sources

- `kg/schema.yaml` (schema_version 0.3.4); `kg/extraction/prompt_template.md`;
  `kg/extraction/prompt_template_v0_3_8.md`; `kg/extraction/prompt_template_v0_3_9.md`
- `docs/crosswalk/usafacts_operationalization_skeleton.md` v0.2; `..._brief.md` v0.1
- Luan, Y., He, L., Ostendorf, M., Hajishirzi, H. (2018). *Multi-Task Identification of
  Entities, Relations, and Coreference for Scientific Knowledge Graph Construction.* EMNLP.
  https://aclanthology.org/D18-1360/
- Linguistic Data Consortium. *ACE (Automatic Content Extraction) English Annotation Guidelines
  for Entities*, v6.6.
  https://www.ldc.upenn.edu/sites/www.ldc.upenn.edu/files/english-entities-guidelines-v6.6.pdf
- Linguistic Data Consortium. *Rich ERE Annotation Guidelines Overview* v4.2.
  https://tac.nist.gov/2016/KBP/guidelines/summary_rich_ere_v4.2.pdf
- NIST. *TAC KBP Slot Filling Assessment Guidelines* v3.2 (2012) and *TAC KBP 2015 Assessment
  Guidelines* v1.0. https://tac.nist.gov/2012/KBP/task_guidelines/TAC_KBP_Assessment_Guidelines_V3.2.pdf
  · https://tac.nist.gov/2015/KBP/ColdStart/guidelines/TAC_KBP_2015_Assessment_Guidelines_V1.0.pdf
