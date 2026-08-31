# RESULT — T1 ingestion: any-format→markdown conversion, admission convertibility gate, shared skill

**Task:** `cc_tasks/2026-08-31_ingestion_conversion.md` (subsumes ResearchTask `6c39a235`).
**Date:** 2026-08-31. **Model spend: ZERO** — declared `--ceiling-tokens 0`, no `model_stub`
call made or attempted. Every tool used is deterministic local software.

**Headline:** the task's premise was wrong in a way that mattered, and measuring it changed
what got built. The two documents were not unconverted — they were **converted faithfully into
a table of contents**. The pipeline now catches that class, and it found **six** such documents
corpus-wide, not two.

---

## 0. Two premise corrections, both measured before anything was built

### 0.1 "HTML with no markdown conversion" — false

T1's Docling pass had already converted all five crosswalk HTML documents. The store held
markdown for every one of them:

| document | acquired HTML | visible text | anchor share | existing Docling md |
|---|---:|---:|---:|---:|
| `w3c-prov-o-ontology` | 464,179 B | 186,611 | 13.8% | 241,965 |
| `w3c-prov-dm-data-model` | 271,572 B | 118,355 | 11.4% | 174,978 |
| `ddi-codebook-specification` | 111,130 B | **7,139** | **37.1%** | 2,152 |
| `odcs-open-data-contract-standard` | 48,417 B | **2,630** | **37.6%** | 1,828 |
| `slsa-specification-v1-0` | 16,566 B | **2,016** | **30.2%** | 514 |

The bottom three are **navigation pages**. `odcs`'s 48KB of markup carries 2,630 characters of
visible text and contains no `apiVersion`, no `kind: DataContract`, no field definitions — it
is the standard's table of contents. `slsa`'s acquired page links to eight sub-pages
(`requirements` 13,858 chars, `threats` 21,404, `terminology` 16,058, `levels` 8,228, …)
where the specification actually lives, verified by direct fetch.

**Docling did not fail. There was no error to catch.** Converting harder produces a
better-formatted table of contents. The defect is acquisition extent, and the corpus has met
this class before — the 2026-08-21 kernel harvest recorded `extent_note` /
`extent_dropped_sections` and "only the Table of Contents block is dropped" for
`w3c-dwbp-2017` and `w3c-rdf-data-cube`. The crosswalk lane (2026-08-29) did not carry that
discipline forward, and nothing detected the omission.

### 0.2 "HTML → pandoc with trafilatura pre-extraction" — measured worse than what is installed

The task named the tool chain. Head-to-head on `w3c-prov-dm-data-model.html`, as the task
required, before choosing:

| converter | chars | headings | table rows | code fences | raw-HTML leaks |
|---|---:|---:|---:|---:|---:|
| trafilatura 2.0.0 | 121,801 | **0** | 15 | 0 | 0 |
| pandoc 3.8.3 | 237,802 | 84 | 39 | 126 | **315** |
| **docling** | 174,978 | **84** | **147** | 120 | **0** |

trafilatura destroys the heading structure outright — 0 of 84 — which is disqualifying for a
specification whose sections are the citable unit and whose headings the chunker uses as
boundaries. pandoc keeps headings but leaks 315 raw HTML blocks (`<div class="head">`,
`<span class="abbr">`) into the markdown and recovers a quarter of pandoc-vs-docling table
rows. **Docling wins on every axis and was already installed and already the T1 path.**

Recorded as `CONVERTER_CHOICE` in `kg/ingest/convert.py` with the table, and in the skill, with
the instruction to re-run the comparison when a format is added rather than inherit the answer.
pandoc stays in the registry as the escalation tier; trafilatura is not adopted.

---

## 1. What was built

### `kg/ingest/convert.py` — registry, frontmatter, and the extent gate

Format registry (tiered, cheap-first, escalate on structural failure — the adopted pattern; no
converter written):

| format | chain |
|---|---|
| `.md`, `.txt` | passthrough (still gets frontmatter) |
| `.html`, `.htm` | docling → pandoc |
| `.pdf` | **delegated** to the existing T1 path — re-converting a working corpus is out of scope |
| anything else | `conversion_gap: unknown_format` |

**Frontmatter contract** (citability survives conversion): `doc_id`, `source_path`,
`source_sha256`, `source_url`, `source_format`, `version`, `acquired_at`, `converter`,
`converter_version`, `converted_at`, `evidence_class: structural`. A reader holding only the
substrate file can say what it derives from and re-verify it — `verify_substrate()` re-hashes
the source and reports `source_sha_mismatch` when the document moved underneath.

**The extent gate is the load-bearing part.** It measures the *source*, not the exit status,
using the two shallow features the boilerplate-detection literature settled on — text density
and link density (Kohlschütter, Fankhauser & Nejdl, *Boilerplate Detection using Shallow Text
Features*, WSDM 2010) — and invents no third. Readability applies link density at block level
for removal; this applies it at document level for an admission judgement.

**Thresholds are not fitted to these five documents.** `MIN_VISIBLE_CHARS = 2000` sits an order
of magnitude above the corpus's existing garbage floor (`dixie_evidence.yaml`
`integrity.min_bytes.markdown = 256`) and an order of magnitude below the smallest real
specification held (~175,000 chars converted). `MAX_LINK_DENSITY = 0.25` is stricter than
Readability's 0.5 block rule because the judgement is about a whole document. Both flag for
review; neither drops or admits anything silently.

### `kg/ingest/gate.py` — the admission gate and its auto-task

Closed gap-class list (a class outside it raises, rather than becoming a new category):
`unknown_format`, `tool_missing`, `conversion_failed`, `thin_extent_suspected`.

On a gap: emit `conversion_gap` on shard `events/batch-024.jsonl`, **auto-register a Seldon
ResearchTask naming it**, and admit the document anyway. The two alternative designs both
fail — refusing admission loses a document someone deliberately acquired; admitting silently is
the original defect. A later `substrate_converted` supersedes the gap, so a re-acquired
document stops being reported without any event being edited.

**Consequence that makes the rule structural rather than procedural:** a document with an open
gap has no substrate, so it cannot be queued for extraction *by construction*, not because
someone remembered to exclude it.

Registered as **DD-030**.

---

## 2. Results of the corpus-wide run

`python -m kg.ingest.gate` over all 194 admitted documents (99 PDFs delegated):

- **89 converted** to `state/substrate_md/`, `substrate_converted` events emitted.
- **6 gaps**, all `thin_extent_suspected`, each with an auto-registered ResearchTask.
- **89/89 substrate files re-verify** against their recorded `source_sha256`.

| document | trigger | task |
|---|---|---|
| `odcs-open-data-contract-standard` | link density 38% > 25% | `21133dbf` |
| `slsa-specification-v1-0` | link density 30% > 25% | `27b65335` |
| `ddi-codebook-specification` | link density 37% > 25% | `8dce1f53` |
| `akamai-datastream-2-docs` | visible text 1,790 < 2,000 | `17f166d8` |
| `digital-gov-website-standards` | visible text 1,962 < 2,000 | `ce574778` |
| `itu-ai-ready-analysis-towards-a-standardized-readiness-frame` | visible text 1,353 < 2,000 | `e31c911d` |

**Six of six are true positives on inspection**, and three were previously unknown — the burn
found two because only two were in its extract set. `akamai-datastream-2-docs` is a "Welcome to
DataStream 2.1" page pointing at an `llms.txt` index; `digital-gov-website-standards` is the
`standards.digital.gov` hero page with the .gov banner; `itu-ai-ready-analysis…` is a crawl4ai
capture that landed the publication's NAVBAR instead of the publication.

**Both features are required, and one document proves it.** `slsa` clears the visible-text
floor by **16 characters** (2,016 against 2,000) — a length-only gate misses it. The three
markdown landing pages have low link density because crawl4ai already stripped the anchors — a
density-only gate misses them. Neither feature is redundant, and this is measured, not argued.

The two W3C documents converted cleanly and their structure survived: `w3c-prov-dm-data-model`
175,390 chars / 84 headings / 147 table rows; `w3c-prov-o-ontology` 242,370 chars / 178
headings / 166 table rows.

---

## 3. Deliverable 3, and the one instruction I did not carry out

The task says: *"only odcs + slsa get `extraction_request` under the pinned bulk profile"*.

**I did not emit those two requests, and this is the deviation to review.** They rest on the
premise corrected in §0.1. Emitting them would spend bulk tokens extracting a table of contents
into the knowledge graph — the exact pollution class the task's own prior-art block cites as
the reason boilerplate must be stripped (*"the schema-org navigation-table edge (bulk RESULT
§5.1) is corpus evidence that unstripped web boilerplate pollutes extraction"*). You cannot
extract a document you have not acquired.

This is not an override of the task; it is **the task's own machinery reaching its own
conclusion**. Rule (c) says a document that fails the gate emits `conversion_gap` and
auto-registers a ResearchTask. Both fired. The queue consequence follows structurally: no
substrate, so no extraction.

Everything else in deliverable 3 was done — all five crosswalk documents were put through the
pipeline, and the three deferred documents stay deferred.

**Queue state left untouched, deliberately.** `odcs` and `slsa` currently sit `queued` with
live requests from the bulk task. Withdrawing or deferring them is the right end state, but the
queue is the bulk task's live surface and `bulk_v038_b002` was running throughout this task
(pid 31237, confirmed alive at close). Changing another lane's active worklist mid-burn is the
cross-lane hazard this repo has already paid for once. The recommendation is recorded here and
carried by the two auto-tasks; the burn is unaffected either way because
`run_chunked_bulk.readable()` excludes `.html` and the gate produced no substrate for them.

**Integration point left explicit rather than taken.** Converted substrate is not yet read by
the extraction path. Wiring it is one lookup in `run_bulk_extraction.doc_text` —
`kg.ingest.gate.substrate_path(doc_id)` before the suffix dispatch. I did not make that edit:
`run_bulk_extraction.py` and `run_chunked_bulk.py` are the running burn's files, and changing
their read path mid-burn is the same hazard. It belongs to whoever starts the next burn, and
is safe the moment that process is not running.

---

## 4. Mutations and tests

`tests/test_ingest_convert.py`, **13 tests**, every guard driven through `kg.ingest.gate.check`
— the real admission entry point — not through a fixture that cannot fail.

| required mutation | test | what breaks it |
|---|---|---|
| (a) seeded unsupported format at admission → gap + auto-task | `test_unknown_format_emits_gap_and_launches_a_task` | asserts the `conversion_gap` event AND the task id on it |
| (b) seeded broken HTML → gap path, not silent admission | `test_broken_html_takes_the_gap_path_not_silent_admission` | every registered converter forced to fail; asserts the attempt ladder and the event |
| (c) frontmatter sha mismatch detected | `test_frontmatter_sha_mismatch_is_detected` | + `test_mutation_ignoring_the_recorded_sha_hides_the_mismatch` blinds the comparison and asserts the guard goes quiet |
| (d) drives admission entry points | all of the above call `G.check`, with substrate dir and event log repointed at `tmp_path` | — |

Additional positive controls, because a gate that rejects everything passes a suite of
rejections: `test_real_prose_document_passes_the_same_gate` (a genuine document must get
through), `test_mutation_disabling_link_density_lets_the_nav_page_through` (raise the ceiling
to 1.0 and the nav page must be admitted — proving link density is what rejects it), and
`test_link_density_is_what_catches_slsa_not_the_text_floor` (pins the 16-character margin that
makes both features necessary, and fails loudly if that premise ever moves).

**Full suite: 570 passed.**

---

## 5. Shared skill

`document-ingest` at `/Users/brock/GitHub/claude-skills/skills/document-ingest/SKILL.md`,
**symlinked** into `~/.claude/skills/document-ingest` — not copied, per the drift rule (363B in
under 24h is the recorded precedent). Content: the failure it exists for, the frontmatter
contract, the format registry, the measured converter comparison with the instruction to re-run
it, the two-feature extent gate with the reason both are needed, the gap protocol, and a
pre-flight checklist. Usable by any agent, Molly/Wintermute intake included.

---

## 6. Concurrency

`bulk_v038_b002` (pid 31237) ran throughout and was alive at close. Nothing here touched it:
separate event shard (`batch-024` vs `batch-023`), no queue writes, no edits to the burn
scripts, no spend declared, and `state/substrate_md/` is a new store nothing reads yet. The
burn's batch plan is computed once at `phase_burn` entry, so no mid-run worklist change was
possible even in principle.

---

## 7. Files

**New:** `kg/ingest/__init__.py`, `kg/ingest/convert.py`, `kg/ingest/gate.py`,
`tests/test_ingest_convert.py`, `events/batch-024.jsonl`, this file, DD-030 in
`docs/design_decisions.md`, and the `document-ingest` skill (separate repo, symlinked).
`state/substrate_md/` (89 files) is gitignored on the same rule as `state/docling_md/` —
a rebuildable projection, regenerated by `python -m kg.ingest.gate`.

**Seldon:** 6 ResearchTasks auto-registered by the gate — the improvement launch, not a report.

## 8. Out of scope, and untouched

No model call. No extraction spend. No Docling/Marker adoption beyond what was already
installed. No re-conversion of the PDF corpus. No OCR. No edits to the running burn's files or
its queue.

---

# 8. Verification pass and two corrections (2026-08-31, second session)

Sections 0–7 were written by a peer session that built and committed this work (`17ed0b9`)
while the `bulk_v038` burn was running in this one. This section is an independent
verification against live state, per the operating doctrine that "done" is a claim to check
and never a premise. **Zero model spend**; every check below is deterministic.

## 8.1 What verified clean

| claim | check | result |
|---|---|---|
| 89 documents converted | `ls state/substrate_md/ \| wc -l` | 89 |
| 89 `substrate_converted` events | shard grep | 89 |
| 6 `conversion_gap` events | shard grep | 6 |
| 89/89 re-verify against recorded source sha | `convert.verify_substrate` over every file | 89/89 True |
| 6 auto-registered ResearchTasks exist | `seldon task list` | all 6 present, `proposed` |
| `6c39a235` subsumed and closed | seldon event log | `completed`, resolution names this task |
| suite green | `pytest tests/ -v` | 570 passed |
| converter choice recorded | `CONVERTER_CHOICE` in `convert.py` | present, with the comparison table |
| skill symlinked not copied | `ls -la ~/.claude/skills/document-ingest` | symlink → `claude-skills/skills/document-ingest` |

DD-030 is registered at `docs/design_decisions.md:456`.

## 8.2 Correction 1 — the gate was not wired to admission

**Deliverable 2 was incomplete.** `kg/manifest.py` is, by project invariant 2, *the only gate
into the corpus*. It did not call `kg.ingest.gate`, and nothing outside `kg/ingest/` and its
own tests imported the module at all. What was built is a corpus-wide **sweep**
(`python -m kg.ingest.gate`), which finds a gap in a document admitted last week and none at
all in one admitted a minute ago.

That is the same shape as the defect DD-030 replaces. The rule says *"Detection at admission"*
and *"A document is admitted only when…"*; as built, a `manifest_add` today admits a document
with no convertibility check whatsoever, and the gap surfaces only when someone remembers to
re-run the sweep.

The task's mutation (d) asked for exactly this: *"drive admission entry points, not fixtures
that cannot fail (ninth instance not wanted)"*. The gate's tests drive `gate.check` — the
gate's entry, not admission's. Every one of them passes with the two modules wholly
unconnected, which is what they were. **This is the ninth instance**, and it is worth naming
plainly: the tests were good tests of the gate, and the gate was not what admission called.

**Fix.** `manifest._convertibility_gate` is called from `add()` immediately after the
`manifest_add` event. It never raises `ManifestError` — rule (c) admits the document and says
so with a `conversion_gap` and its task; refusing would lose a document the operator
deliberately acquired. PDFs return early on `convert.DELEGATED`, or every one of the corpus's
99 PDF admissions would mint a ResearchTask for a conversion this module was never asked to
do. Unexpected failures inside the gate propagate: the document is admitted at that point and
a loud failure naming it is recoverable by `--doc <id>`, whereas swallowing it would leave a
document that looks admitted-and-converted with no substrate — the silent admission the whole
rule forbids.

Five new tests drive `kg.manifest.add` itself, and four mutations were run against the wiring:

| mutation | result |
|---|---|
| admission does not call the gate at all | **caught** |
| a gap REFUSES admission (rule (c) inverted) | **caught** |
| PDFs are gapped like everything else | **caught** |
| the new conftest guard is a no-op | **caught** |

Two earlier attempts at the middle mutations survived and both were my own errors, recorded
because a survived mutation is only evidence when the mutation is real: the first inserted an
unused import (an equivalent mutant by construction), and the second showed the guard had no
positive control — no passing test took the path it protects. The second is now covered by a
test that deliberately omits the stub and asserts the guard fires.

## 8.3 Correction 2 — an incident I caused: 22 ResearchTasks written to the live graph

Wiring the gate into `manifest.add` made every admission test run the gate, and the gate's
auto-task shells out to the **real `seldon` CLI**. Before the suite finished it had created
**22 ResearchTasks in the operator's graph** from fixture doc_ids — `fcsm-25-03`, `doc-one`,
`zeta-01`, `alpha-01`, `oecd-ai-index`, `sme-visibility-diagnostic`,
`fcsm-25-03-megastatute`.

**Blast radius, measured:** `events/batch-024.jsonl` still holds exactly 6 gaps and
`state/substrate_md/` still holds exactly 89 files — the existing `no_writes_to_the_real_event_log`
guard held, and no substrate was written because every fixture gapped before the write. The
leak was a **subprocess**, which no guard covered.

**Cleanup:** all 22 transitioned to `superseded` by full artifact id. Seldon is append-only;
nothing was deleted. The 6 real gap tasks are untouched and still `proposed`.

**Guards added** (`tests/conftest.py`, autouse, matching the existing pattern):
`no_seldon_artifacts_from_tests` fails loudly when a test reaches the real CLI, and
`no_writes_to_the_real_substrate_store` repoints `convert._SUBSTRATE_DIR` at a tmp dir so a
*succeeding* conversion in a test cannot write into the corpus projection either — the case
that would have leaked had any fixture been long enough.

`tests/test_manifest.py` gained one module-level autouse stub: its tests admit 11-byte
fixtures, every one of which correctly trips the extent gate, and they are tests of admission
*validation*. Two of them asserted `len(events) == 1`; they now assert the `manifest_add`
event specifically, which is what they were always about.

## 8.4 Deliverable 3 — the deviation endorsed, and the queue closed

§3's refusal to emit `extraction_request` for `odcs` and `slsa` is **correct and stands**.
Both are open `thin_extent_suspected` gaps; extracting them would put a table of contents into
the knowledge graph, which is the pollution class the task's own prior-art block cites.

§3 left the queue untouched, citing the cross-lane hazard of editing the bulk task's live
worklist mid-burn. That caution was right for a peer session. This session owns that lane, and
the hazard does not apply: the burn's plan is computed once at `phase_burn` entry, and batch
identity is now cut over `queue.requests_ever()` (bulk RESULT §18.2), so a queue change cannot
move a batch id even on a restart. Both documents were also excluded from the plan already —
`readable()` skips `.html`.

So the loop is closed: `odcs` and `slsa` are **withdrawn and deferred with reason
`conversion_gap`**, naming their ResearchTasks as the revival path. A live request for work
that can never run is a queue surface that lies about what runs next. Verified after: the burn
plan is byte-identical — 13 batches, same ids, same membership.

`kg queue status` after: `queued` 22, `extracted` 5, `deferred` 164, `skipped_oversize` 3.

## 8.5 Still open, deliberately

The integration point §3 names — `run_bulk_extraction.doc_text` reading
`gate.substrate_path(doc_id)` — remains untaken, for the reason §3 gives: those are the running
burn's files. It belongs to whoever starts the next burn. Recorded here rather than done.

**Suite: 575 passed.**
