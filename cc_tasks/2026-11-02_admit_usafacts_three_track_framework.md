# CC Task: admit USAFacts' three-track AI-ready data framework (August 2026 deck and overview) from the operator's inbox

**Date:** 2026-11-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** DN-019 §5 and §6 item 2 (the framework's levels are read from a corpus copy, never asserted), DD-003 (manifest is the only gate), the inbox precedent `cc_tasks/2026-07-03_cisco_inbox_add_v2.md` and the pattern of `scripts/admit_noaa_naos.py`.
**Amended by:** none.
**Builds on:** `scripts/admit_measurement_theory_sources.py` (the newest admission driver; copy its structure).
**Framework layer served (DN-005 §5 rule 1):** none; corpus admission. The record is not touched by this task.
**Fulfils:** its own ResearchTask.
**After:** 2026-11-02_land_dn019_and_redrive_v3
**Model:** author
**Spend:** est. 0.3M tokens, Claude Code session included. No model calls through model_stub. The task ends by printing its own session usage.
**Parts:** A 0.60, B 0.40.
**Part map:** A admits the two documents; B verifies the text the record will depend on.
**Network:** none

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

Every readiness artifact in this repository descends from `usafacts-ai-ready-data-guide` (four criteria: Accessible, Understandable, Accurate, Open). USAFacts presented a successor at the Partnership for Public Service Federal Data Excellence roundtable on 2026-08-26: three tracks (Agentic Access, Agentic Context, Agentic Evaluation), three levels within each, modeled on SLSA (slsa.dev), with three prerequisites (open by default, discoverable, clearly licensed). It is not published on the web; the operator holds the deck and a one-page overview from the roundtable and placed both in `corpus/inbox/` on 2026-11-02. DN-019 §5 left the framework's levels unsettled because no corpus copy existed. This task creates the corpus copy. DN-020 (next Desktop note) re-parents the sixteen checks onto track × level and cites these two doc_ids; it cannot be written until they exist.

## Part A: admit

Inbox files, sha256 as the operator handed them over (verify, quote):

| file | sha256 | doc_id | doc_type | title |
|---|---|---|---|---|
| `corpus/inbox/USAFacts AI-Ready Data Slide Deck.pdf` | `9cbe6ae32203f9d015d486765d4b00202e1540c08a3f4a158a5780036abbfb0b` | `usafacts-ai-ready-framework-deck-2026-08` | practitioner | AI-Ready Government Data: A Framework for Trust in the Age of AI (August 2026) |
| `corpus/inbox/Overview of USAFacts AI-Ready Data Project.pdf` | `e47c5bc63d3c70a0ab47a9b029f699ca21d1ea396e3d6dccfd5700747d7876fc` | `usafacts-ai-ready-framework-overview-2026` | practitioner | Overview of USAFacts Project on AI-Ready Government Data |

Authors: USAFacts; the deck names Ben Gitis and Pieter van Noordennen. pub_year 2026. source_url: none (unpublished draft, distributed at the 2026-08-26 roundtable; cite the event page `https://ourpublicservice.org/events/framework-for-ai-ready-data-2026-federal-data-excellence-roundtable` as `discovered_via`, not as `source_url`). acquisition_method `operator_inbox`; acquired_by the operator; acquired_at the inbox file mtime, quoted. rationale: successor to `usafacts-ai-ready-data-guide`; the framework the readiness diagnostic re-parents onto (DN-019 §5).

1. Write `scripts/admit_usafacts_three_track.py` on the pattern of `admit_measurement_theory_sources.py`: copy each file to `corpus/crosswalk/<doc_id>.pdf`, docling-convert to `state/docling_md/<doc_id>.md`, `manifest_add` with the identity above, dixie `screening_imported`, sweep, `kg.manifest rebuild`. Dry run first (log), then live (log).
2. Leave the inbox originals in place until the live run passes; then move them to `corpus/staging/inbox/usafacts_2026-11-02/` (gitignored per the inbox convention) so the inbox is empty. Quote `ls corpus/inbox/`.
3. Quote the two manifest entries from `corpus/manifest.json` in full, and the `included` count before and after (expected +2 on the count the V3 RESULT left at 289, unless something moved it since; quote what you find).
4. Record a `document_annotation` (the `supersedes` relation the manifest supports, or the nearest one it does; quote which) from `usafacts-ai-ready-framework-deck-2026-08` to `usafacts-ai-ready-data-guide`. If no such relation exists in the manifest or event schema, say so in the RESULT and do not invent one; DN-020 will carry the supersession in prose and the record.

## Part B: verify the text the record will depend on

The docling markdown is what DN-020 and the re-parenting task will quote. Confirm these strings (de-hyphenated, whitespace-collapsed as `kg/extraction/grounding.py` does) are findable in `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md`; quote each hit's line or report a miss:

- "Three tracks, three levels within each track"
- "Modeled on SLSA"
- "Agentic Access", "Agentic Context", "Agentic Evaluation"
- "Open by default", "Discoverable", "Clearly licensed"
- the nine level captions of slide 16, e.g. "Data is published in machine-readable files", "Context is machine-readable and citable in an answer", "Integrated quality assurance programs across agencies and industry"
- "05 AI-ready data" (slide 9: the framework becomes a Federal Data Excellence standard)

pypdf extraction of the deck breaks hyphenated words across lines ("AI\n-\n Ready"); if docling does the same, record the docling line count and the miss list, and say whether a second converter (pandoc or trafilatura per the document-ingest skill) recovers them. Do not hand-edit the markdown.

Projection: run `python scripts/build_projection.py` only if the corpus layer is fed by it (4e27e7bf Part A step 5 answers this; if that task has not run, read `scripts/build_projection.py` and say). Detached, logged, polled. Quote the `Document` count in database `ai-readiness` before and after.

## Gate and RESULT

Write set: `scripts/admit_usafacts_three_track.py`, `corpus/manifest.json`, `events/`, `state/docling_md/`, `dixie_evidence`/ledger files, `corpus/crosswalk/` (gitignored binaries), logs. No framework record, no schema, no rules. Gate: `make gate-fast`, detached and logged; quote passed, skipped, xfailed and deselected. Corpus-count drift guards will fire for views that cite the count; regenerate by generator as the V3 RESULT §4 did, quote the logs, and list the regenerated files. Then `seldon verify` (quote EXIT) and the protected-paths diff on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json` (expected empty).

RESULT at `cc_tasks/2026-11-02_admit_usafacts_three_track_framework_RESULT.md`: §1 the two doc_ids and the Part B hit list first; then every quote above; log paths in §6. Then `seldon cc complete`, commit, push.
