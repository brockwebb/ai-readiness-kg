<!--
Chunked extraction prompt (task 2026-08-27_chunked_pilot §3, profile `chunked_v035`).
DERIVED FROM kg/extraction/prompt_template.md v0.3.5 BY SUBSTITUTION, NOT REWRITING: every
rule below — the first grounding rule, character-exact spans, the Instrument positive
criterion and per-attribute spans, the semantic-edge span rule, evidence_grade, the edge
whitelist — is that file's text unchanged. Only the framing changed, because only the UNIT
changed: the model sees one chunk instead of the whole document. That is the pilot's single
variable; anything else edited here invalidates the comparison.
Rendering substitutes {{schema_version}}, {{document_id}}, {{chunk_id}}, {{document_text}}.
prompt_version: 0.3.5-chunk
-->
# Chunk extraction — ai-readiness-kg schema {{schema_version}}

You extract a knowledge graph from ONE CHUNK of a primary-source document. Output **strict
JSON** only — no prose, no markdown fences. Every node and every edge you emit MUST carry a
`grounding_span`: a quote copied from the chunk text below that supports it.

**Extract only what THIS CHUNK asserts.** The chunk is a contiguous passage of a larger
document; a `[section: ...]` breadcrumb line and the previous chunk's last paragraph may
precede it as context. Do not extract from the breadcrumb — it is navigation, not document
text, and a span quoting it will be rejected. Do not carry in anything you know about the
rest of the document.

**Entities mentioned but not asserted about are mention-only stubs.** If the chunk names
something but says nothing about it that a span can carry, do NOT emit a typed node. Emit it
in `mentions` as `{"name": "<surface form>", "grounding_span": "<exact quote>"}`. Stubs are
resolved against typed nodes elsewhere in the document by the harness; a stub is never a
typed node and never an edge endpoint.

**A relation whose endpoints are not BOTH in this chunk is diverted, not guessed.** Put it in
`proposed_relationships` with `"diversion_reason": "cross_chunk"` and whatever span you have.
Cross-chunk relations are a known open problem and are out of scope for this run — diverting
them is the correct behavior, not a failure.

Do NOT emit `document_id`, `model_id`, `schema_version`, `extraction_event_id`, or any
timestamp/event id — the harness owns those and injects them. Emit only the content you
extract.

## Emission order (produce these keys in this order)

1. `extract_plan` — a one-line `chunk_summary` and a `concept_inventory` (an exhaustive list
   of the substantive ideas THIS CHUNK uses). Plan before you extract.
2. `concepts` — the exhaustive Concept layer, extracted first-class. Be thorough: thin concept
   coverage is a known failure mode.
3. `definitions` — verbatim definitions the document gives for a term.
4. `claims` — falsifiable assertions the document makes.
5. `instruments` and `measures` — assessments/indices/benchmarks and their individual items.
6. `standards` and `frameworks` — technical specs and conceptual structures the document names.
7. `practices`, `tools`, `platforms` — normative recommendations for machine consumers, the
   software that runs measures, and the machine consumers (search engines, crawlers, LLM
   retrieval systems, bot controls) the document targets or describes. Emit only when the
   document actually contains them; most policy/academic documents will have none.
8. `edges` — relationships **among the nodes above**, using only the allowed edge types below.
9. `cites` — citations from this document to other documents (`from_id` is this document).
10. `mentions` — the mention-only stubs described above.
11. `proposed_relationships` — any relationship the schema below CANNOT express, each with a
   `grounding_span` and a `suggested_edge` name. These are staged for human review, never
   written directly. Use this instead of forcing a relationship into the wrong edge type.

## Node types and their properties

- **Concept**: name, aliases, description
- **Definition**: term, verbatim_text, normative_status (statute/policy/standard/academic/industry), as_of_date
- **Claim**: claim_text, claim_type (empirical/normative/speculative), **evidence_grade (REQUIRED,
  see below)**
- **Instrument**: name, owner, year, method, **grounding_spans (REQUIRED map, see below)**
- **Measure**: text, response_type, tier (optional: public/agency_instrumented/paid — see below)
- **Standard**: name, version, steward, as_of_date
- **Framework**: name, owner, year
- **Practice**: text, as_of_date, scope — a normative recommendation the source makes about how
  to publish, structure, expose, or maintain data or content for machine consumers. `scope` is
  the asset class it is about, exactly one of: `dataset`, `api`, `bulk_file`, `tool`, `content`,
  `advisory`, `site`, `any`. Any other value is rejected.
- **Tool**: name, steward, license, url, as_of_date — software that implements one or more
  Measures (e.g. Lighthouse, Scrapy, pySHACL, LinkChecker, GoAccess, Spectral, extruct, the GSA
  Site Scanning engine, DAP).
- **Platform**: name, operator, as_of_date — a machine consumer whose behavior is targeted or
  described (Google Search, Bing, a named crawler, an LLM vendor's retrieval system,
  Cloudflare/Akamai bot controls).

### Instrument attributes — per-attribute spans, no background knowledge (v0.3.4)

**You must NOT complete any attribute from background or world knowledge.** This rule exists
because a prior run fabricated Instrument `method` values ("fielded every 2 years",
"household health survey") that the document never stated. For every Instrument:

- Emit a `grounding_spans` map: `{"owner": "<exact quote>", "year": "<exact quote>",
  "method": "<exact quote>"}` — one CHARACTER-EXACT document quote per attribute you fill.
  Each quote must **contain the attribute's value verbatim**. `method` in particular must be
  copied from a document sentence that states how the instrument works — if the document
  only names the instrument, `method` is null. No covering quote ⇒ set that attribute null.
  (`name` is covered by the node's own `grounding_span`, as for every node.)
- **Positive criterion — when TO emit an Instrument (v0.3.5).** Emit an Instrument node
  whenever the document *specifies, applies, evaluates, or documents* the instrument —
  that is, the document's own text carries at least one attribute-bearing description
  (its method, owner, year, inputs, or outputs) that a span can cover. A **surveyed**
  instrument in a survey/review paper meets this criterion: the survey documents it —
  emit it as an Instrument with whatever attributes the survey's text covers. The paper's
  OWN instrument always meets it (e.g. AIDRIN in the AIDRIN paper is an Instrument node,
  never a mere Concept).
- An instrument the document merely **names without any attribute-bearing text** — e.g.
  named once in a related-work sentence ("unlike DQAF, we…") — is NOT an Instrument node:
  emit it as a Concept and connect it with `mentions`.
- This criterion decides the *node type*; the per-attribute span rule above decides the
  *attributes*. An Instrument that meets the criterion but whose `method` has no covering
  quote gets `method: null` — it is still an Instrument.

### Semantic edges — the span must state the relation (v0.3.4)

For the edge types `has_component`, `subtype_of`, `consumes`, `extends`, `implements`:
the edge's `grounding_span` must be a quote that contains **both endpoints' names (or their
unambiguous in-sentence referents) AND the relation predicate** — a sentence that actually
states the relationship. Page structure is not a relation: a heading, a list nesting, a
table row, or a navigation grouping never grounds a semantic edge. If you infer a
relationship from headings or list structure, put it in `proposed_relationships` with the
structural evidence as its span — never emit it as an edge.

### `evidence_grade` — REQUIRED on every Claim

Every Claim MUST carry `evidence_grade`, exactly one of these values (descending strength). A
Claim without it, or with any other value, is rejected.

- `peer_reviewed_experiment` — a published, peer-reviewed experimental result.
- `platform_official` — the platform operator's own documentation or statement about its own
  behavior (ONLY when the source IS that operator; a third party reporting what Google says is
  not `platform_official`).
- `measured_practitioner` — a practitioner result with a disclosed method and data.
- `practitioner_assertion` — a practitioner statement with no disclosed method.
- `inference` — reasoned from other evidence rather than observed.

### `Measure.tier` — optional

Emit `tier` on a Measure only when the source states or implies who can run it: `public`
(runnable by anyone from outside), `agency_instrumented` (needs agency-side analytics, scripts,
or logs), or `paid` (commercial product). Omit it otherwise; any other value is rejected.

Do NOT emit Construct nodes: a Construct is a Concept promoted to measurability by an explicit
operator decision, not an extraction decision. Emit the underlying Concept instead.

Every node object also needs: `id` (unique within this output), `grounding_span`, `location`.

## Allowed edge types (type-validity is enforced; anything else is rejected)

`defines` (Document→Definition), `mentions` (Document→Concept), `asserts` (Document→Claim),
`about` (Claim→Concept), `operationalizes` (Instrument→Construct),
`measures` (Measure→Construct, Measure→Concept, Instrument→Concept),
`grounds` (Construct→Definition), `extends` (Definition→Definition, Framework→Framework),
`conflicts_with` (Definition↔Definition, Claim↔Claim), `cites` (Document→Document),
`builds_on` (Standard/Framework→Standard/Framework), `implements` (Standard→Concept),
`uses_measure` (Instrument→Measure), `has_component` (Framework→Concept or Concept→Concept;
part-whole only, never is-a), `subtype_of` (Concept→Concept; is-a only, never part-whole),
`precedes` (Concept→Concept),
`recommends` (Document→Practice; the source makes this recommendation),
`supported_by` (Practice→Claim; the claim whose evidence backs the practice),
`implemented_by` (Measure→Tool; the software that runs the measure),
`consumes` (Platform→Standard; the platform reads/honors this spec),
`applies_to` (Practice→Concept or Measure→Concept; the asset class or concept it targets — asset
classes such as Dataset, Distribution, DataService, DataCatalog, WebApplication, Report,
DefinedTerm are Concepts),
`targets` (Practice→Platform; the machine consumer the practice is aimed at),
`supersedes` (Document→Document; this document replaces an earlier version).

Endpoint types are enforced exactly as listed: an allowed edge type between the wrong node
types is not written. Put it in `proposed_relationships` instead.

Each edge object: `type`, `from_id`, `to_id`, `grounding_span`, `location`. The document node's
id is `{{document_id}}`.

Every node object also needs: `id` (unique within this chunk), `grounding_span`, `location`.

## Output keys

`extract_plan` (a one-line `chunk_summary` is enough here), `concepts`, `definitions`,
`claims`, `instruments`, `measures`, `standards`, `frameworks`, `practices`, `tools`,
`platforms`, `edges`, `cites`, `mentions`, `proposed_relationships`.

## The chunk

Document id: `{{document_id}}`
Chunk id: `{{chunk_id}}`

```
{{document_text}}
```
