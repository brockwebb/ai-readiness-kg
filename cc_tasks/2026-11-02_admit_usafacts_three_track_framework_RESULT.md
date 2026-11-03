# RESULT: admit USAFacts' three-track AI-ready data framework (August 2026 deck and overview)

**Task:** `cc_tasks/2026-11-02_admit_usafacts_three_track_framework.md` (+ `ADDENDUM_01`)
**Executed:** 2026-11-03 (UTC) in the dispatched worktree `cheeky-cooking-dolphin`.
**Recall used:** none — the design was derived from the repo's own code and live graph (the admission
scripts `admit_measurement_theory_sources.py` / `admit_noaa_naos.py`, `kg/manifest.py`,
`dixie.evidence`, `scripts/build_evidence_map.py`, and the live `seldon-ai-readiness-kg` graph), not
from the recalled RESULTs. The recall hits (NOAA/ESIP, DCAT, USAFacts-note) confirmed context but did
not change the approach.

---

## 1. The two doc_ids and the Part B hit list (first, as ordered)

Admitted, both `included` + `integrity: verified`:

| doc_id | canonical corpus file | sha256 | source_type | grounding_surface |
|---|---|---|---|---|
| `usafacts-ai-ready-framework-deck-2026-08` | `corpus/crosswalk/usafacts-ai-ready-framework-deck-2026-08.pdf` | `9cbe6ae3…bfbb0b` | practitioner | slides |
| `usafacts-ai-ready-framework-overview-2026` | `corpus/crosswalk/usafacts-ai-ready-framework-overview-2026.pdf` | `e47c5bc6…7d7876fc` | practitioner | document |

**Part B — strings in `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md`** (docling,
765 lines / 11,444 chars; normalization = `kg/extraction/grounding.py` NFKC + de-hyphenate-at-linebreak
+ whitespace-collapse, case-sensitive). **9 of 12 HIT, 3 MISS** (`logs/usafacts_partb.log` reproduces
this via `kg.extraction.grounding.is_grounded`):

| string | result | where |
|---|---|---|
| "Three tracks, three levels within each track" | **HIT** | — |
| "Modeled on SLSA" | **HIT** | — |
| "Agentic Access" | **HIT** | — |
| "Agentic Context" | **HIT** | — |
| "Agentic Evaluation" | **HIT** | — |
| "Open by default" | **HIT** | — |
| "Discoverable" | **HIT** | — |
| "Clearly licensed" | **HIT** | — |
| "Integrated quality assurance programs across agencies and industry" | **HIT** | L461 |
| "Data is published in machine-readable files" | **MISS** | present as `machine -readable` (L441) |
| "Context is machine-readable and citable in an answer" | **MISS** | present as `machine - readable` (L453) |
| "05 AI-ready data" | **MISS** | present as `05 AI - ready data` (L287); also once OCR-mangled `05 Al-ready data` (L247) |

**The 3 misses are the hyphen-across-break quirk the task anticipated, in both converters.** The
slide lays the compounds "machine-readable" and "AI-ready" across a soft break; **docling** renders a
*spaced* hyphen (`machine -readable`, `machine - readable`, `AI - ready`), and **pypdf** (the second
converter, `logs/usafacts_partb.log`) wraps the hyphen to the next line (`…machine` ⏎ `-readable…`).
The grounding normalizer joins only *hyphen-then-linebreak* (`-\s*\n`), so neither a spaced hyphen nor
a leading-hyphen wrap matches the un-spaced compound. **Neither converter recovers the three as the
task phrased them** — the text is present in both, only the inline hyphen is mangled. The markdown was
**not** hand-edited (task instruction). The grounding-findable verbatim forms, for DN-020 to quote, are:
`Data is published in machine -readable files` (L441), `Context is machine - readable and citable in
an answer` (L453), `05 AI - ready data` (L287) — all three confirmed HIT (`logs/usafacts_partb.log`).

pandoc/trafilatura were not run: per the `document-ingest` skill they are HTML converters, and the deck
is a PDF; the "second converter" for a PDF is pypdf, which is reported above.

---

## 2. Part A — admission (`included` 289 → 291)

`corpus/manifest.json` `counts_by_decision.included`: **289 before → 291 after** (`logs/usafacts_admit_live.log`;
quoted live: `{"included": 291, "excluded": 73, "pending_refetch": 42, "pending_review": 1}`). Manifest
`entries` 405 → 407. Both new entries are `screening.decision = included`, `integrity.status =
verified`, on-disk sha256 == manifest sha256, canonical path under `corpus/crosswalk/`. The integrity
gate passed on both: magic_bytes (pdf/pdf), size_sanity (3,701,919 / 370,754 bytes vs floor 7,000),
content_smoke (24 pages / 1 page, extractable text present).

The two manifest entries are quoted **in full** in `logs/usafacts_manifest_entries.txt`. Identity
headlines:

- **deck** — title "AI-Ready Government Data: A Framework for Trust in the Age of AI (August 2026)";
  authors `["USAFacts","Ben Gitis","Pieter van Noordennen"]`; pub_year 2026; doc_type practitioner;
  source_url `urn:usafacts:ai-ready-data-framework:2026-08-roundtable:slide-deck`;
  acquisition `{method: operator_inbox, acquired_by: operator}`.
- **overview** — title "Overview of USAFacts Project on AI-Ready Government Data"; authors
  `["USAFacts"]`; pub_year 2026; doc_type practitioner; source_url
  `urn:usafacts:ai-ready-data-framework:2026-08-roundtable:overview`;
  acquisition `{method: operator_inbox, acquired_by: operator}`.

**`acquired_at` (inbox file mtime), quoted:** deck `2026-11-02T17:50:10.999093+00:00`, overview
`2026-11-02T17:50:15.004385+00:00` (the operator's original file times, carried into the dixie
`screening_imported` `notes`). The manifest's `acquisition.acquired_at` instead records the ledger's
first file-observation timestamp (`2026-11-03T04:43:28Z`), because `_on_file_observed` fills a null
`acquired_at` from the sweep event time; the operator's mtime is preserved in the notes, as above.

**Inbox emptied (step 2).** After the live run the originals were moved to
`corpus/staging/inbox/usafacts_2026-11-02/` (gitignored). `ls corpus/staging/inbox/` →
`usafacts_2026-11-02`. (`corpus/inbox/` is empty and untracked; the ADDENDUM path correction was
honored — the PDFs came from `corpus/staging/inbox/`, not `corpus/inbox/`.) Because gitignored binaries
are not in a dispatched worktree, the two PDFs and the corpus/state document dirs were **copy-seeded**
from `$SELDON_PRIMARY_CHECKOUT` (rsync `-a`, no `--delete`); the primary checkout's own inbox is
outside this worktree's reach and still holds the originals (operator housekeeping, not this task).

**Part A step 4 — the `supersedes` relation: recorded as absent of any honored mechanism; NOT invented**
(exactly as the task directs). `kg/schema.yaml` *declares* a `supersedes` edge (Document→Document,
`dcterms:replaces`), and a comment says `document_annotation` events populate it. But the projection's
`annotation_update` (`scripts/build_projection.py`) whitelists only the scalar properties
`is_platform_operator` and `construct_arm` (`ANNOTATABLE_DOCUMENT_PROPERTIES`); a `document_annotation`
with `property: supersedes` is silently dropped, and **zero** such events exist anywhere in the log.
The manifest's only supersession primitives are `content_update` (byte replacement of one doc) and
`version_of` (dated versions of one URL) — neither is a cross-document successor edge. The only path
that *would* create the edge is an `edge_asserted` from extraction carrying a grounding span, which
this corpus-admission task does not perform. So no relation was written; **DN-020 carries the
supersession (deck ⊃ `usafacts-ai-ready-data-guide`) in prose and the record**, as the task provides.

---

## 3. Premises the task / addendum got wrong (named, with the grounded correction)

1. **"source_url: none" is infeasible for an *included* document, and the Cisco inbox pages are not a
   precedent for one.** The task modeled the admission on the Cisco inbox precedent and specified
   `source_url: none`. But `build_evidence_map.q3_claims` fails hard unless **every** included doc has
   a `manifest_add` event (it uses the first such date in the corpus-growth claim), and `kg.manifest.add`
   requires a non-empty, **unique** `primary_url`. All 289 prior included docs carry an http(s) URL; the
   six Cisco `source_url: None` pages are **`excluded`**, not included, so they are no precedent. These
   two are the first genuinely unpublished *included* documents. **Grounded resolution (RFC 8141):** each
   `primary_url` is a URN — a persistent, location-independent identifier, honestly non-dereferenceable —
   and the roundtable event page is recorded as `discovered_via`, exactly as the operator directed (not
   as source_url). This is an internal, reversible, under-cap decision: decided and logged, not escalated.
   `manifest.add` was therefore called (it wrote the two `manifest_add` events to `events/batch-001.jsonl`),
   contrary to my first pass which skipped it; that first pass was reverted before the corrected run.
2. **ADDENDUM premise 2 — "projection expected +2 → 292" — holds *because* of the correction above, not
   by the admission alone.** `build_projection.py` sources `Document` nodes from `manifest_add` events
   (not from the dixie-projected manifest), so without the `manifest.add` call the 91-minute run would
   have been a no-op (290). With the URN + `manifest.add` correction, the projection genuinely added the
   two nodes: **290 → 292** (confirmed live; §6).
3. **The worktree is unseeded.** A fresh dispatched worktree lacks gitignored corpus binaries, `state/`
   caches, and `corpus/staging/` subtrees. The first `gate-fast` failed one test
   (`test_noaa_esip_crosswalk.py:192`) purely because `corpus/staging/proposed_schema/` had not been
   seeded; after seeding the staging tree from the primary the gate is green (§6). Unrelated to this task.
4. **The docling conversion is delegated, not reimplemented in the admit script.** The task's step 1 says
   the script docling-converts; instead the script does admission only and the docling markdown is
   produced by the project's canonical converter `scripts/t1_build_index.py --phase convert` (DD-023 keeps
   the docling→pypdf fallback and fidelity labelling in one place — adopt-before-create). That run reports
   `95 converted, 194 cached, 2 failed` (`logs/usafacts_docling_convert.log`): the 2 failures are the
   **pre-existing** measurement-theory docs `basili-caldiera-rombach-1994-gqm` and `iso-iec-ieee-15939-2017`,
   whose `.md` canonical files are absent in **both** this worktree and the primary checkout — a prior-task
   corpus-binary gap, not this task's concern. Both USAFacts docs converted cleanly (deck 11,444 chars;
   overview 2,713 chars).

---

## 4. Ripple: the admission moved the published corpus count 289 → 291

Admitting two included documents moves every generated view that cites the count; the `gate-fast` drift
guards catch it. Regenerated **by generator, none by hand** (`logs/usafacts_regen.log`, `EXIT=0` for all
seven: `build_evidence_map`, `build_l0_report`, `build_brief_pack`, `build_figures`, `build_scan_catalog`,
`build_l0_site`, `build_report_pdf`). Tracked files changed (full list; `git diff --stat`):

- `docs/evidence/claims.yaml` — CL-044 "holds **291** admitted documents now" (was 289); the
  `framework_record_commit` pin stayed stable at `37b3b82ae3de` (V3's fix on main; this task does not
  touch the record).
- `docs/data/corpus_manifest.json`, `docs/data/index.json` — count-bearing data copies.
- `docs/brief/C_provenance.md` — provenance count.
- `docs/figures/fig2_system_at_a_glance.{png,svg}`, `docs/figures/numbers.json` — the "system at a glance"
  figure's corpus count.
- plus the admission artifacts: `corpus/manifest.json` (+2 entries), `corpus/evidence/decisions.jsonl`
  (+7 lines: 2 screening_imported, 2 file_observed, 2 integrity_checked, 1 corpus_epoch_declared),
  `events/batch-001.jsonl` (+2 manifest_add events), and the new `scripts/admit_usafacts_three_track.py`.

The L0 report/site/scan-catalog did **not** change: the raw included count is not embedded in their prose,
and the two docs are not yet cited by any check (DN-020 wires that). The diff is a pure count refresh —
no verdict, score, or check-text change.

---

## 5. Projection (ADDENDUM premise 2): `seldon-ai-readiness-kg` Document nodes 290 → 292

`scripts/build_projection.py` ran detached/logged/polled to `EXIT=0` in **5,376.9s (~90 min)**
(`logs/usafacts_projection.log`; `scan_layer` 2,239.5s / 41.7% was the long phase, `framework_layer`
10.9s). Document nodes **290 (before) → 292 (after)**, both queried live against `seldon-ai-readiness-kg`;
the projection's own summary prints `"n:Document": 292`. Both new docs are present as Document nodes.
This is `build_projection.py`'s database (`seldon-ai-readiness-kg`), not the MCP corpus layer
(`ai-readiness`): per ADDENDUM premise 2 the MCP layer is fed by squiddy from `graphs/ai-readiness/ledger`,
**not** touched here, so **the two documents are not yet in the squiddy ledger and the MCP corpus verbs
will not see them until that ledger is updated — a separate task.**

---

## 6. Gate, verify, protected paths (logs under `logs/`, gitignored)

- **`make gate-fast`: green** — `logs/usafacts_gate_fast_2.log`, `EXIT=0`: **3443 passed, 8 skipped,
  41 xfailed, 0 failed, 0 deselected**, 246.13s. The write set touches nothing under
  `assessment/harness/scan/rules/`, `collectors/`, `runner.py`, `run.py`, `manners.py`, `rederive.py`,
  `scripts/score.py` or the framework record, so `gate-fast` is the correct tier (also what the task
  specifies). The 8 skips are all standing/environmental, none hiding a failure:
  `test_kg_questions:115` (stored corpus epoch moved under the admission — a skip, not a failure);
  `test_dispatch_stuck_isolation` ×3 (seldon checkout not beside this repo); `test_dispatch_config`
  ×2 (live-model, never run unasked); `test_g1_preservation:337`; `test_scan_harness:290` (E5).
  The first run (`logs/usafacts_gate_fast.log`) had 1 failure, `test_noaa_esip_crosswalk.py:192`,
  from the unseeded `corpus/staging/proposed_schema/`; seeding the staging tree fixed it (§3.3).
- **`seldon verify`: EXIT=1, 1 warning, 0 failed checks** — `logs/usafacts_seldon_verify.log`. The one
  warning is **pre-existing and about another task**: "`98ed1dd1` is blocked with no reason recorded"
  (the V3 RESULT noted the same). Every integrity check passes: event log **50,863 events readable**,
  prior art 6 notes each passing, relationship types canonical, precedence 76 edges acyclic, all 221 task
  source files resolve on disk, tracked dirs `cc_tasks/`+`handoffs/`. This task introduced no new finding.
- **Protected paths: pass (empty diff).** `git diff HEAD` on `framework/ai_readiness_framework.json`,
  `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json` is byte-empty — the
  record and schema are untouched.

**Logs cited:** `logs/usafacts_admit_dryrun.log`, `logs/usafacts_admit_live.log`,
`logs/usafacts_manifest_entries.txt`, `logs/usafacts_docling_convert.log`, `logs/usafacts_partb.log`,
`logs/usafacts_regen.log`, `logs/usafacts_gate_fast.log`, `logs/usafacts_gate_fast_2.log`,
`logs/usafacts_seldon_verify.log`, `logs/usafacts_projection.log`,
`logs/projection_20261103T045501Z.log`.

---

## 7. Session usage and spend

**Zero model calls.** Every step — the admit script, docling conversion (`t1_build_index`), the dixie
sweep, `kg.manifest.add`, the seven view generators, `build_projection.py`, `make gate-fast`,
`seldon verify` — is non-model; nothing went through `model_stub.invoke` / `claude -p`, so **zero tokens
were reserved or settled against the daily cap** (`state/spend_ledger.jsonl` unchanged). The `**Spend:**
est. 0.3M tokens` was this Claude Code session's own (unmetered) context budget. No network (the task
declared `Network: none`; `fetch_allowlisted.py` was not invoked — the bytes came from the operator inbox).
