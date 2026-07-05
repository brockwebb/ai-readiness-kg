# CC Task — ai-readiness-kg Bulk Extraction v1 (baseline corpus, diverted budget)

**Created:** 2026-07-05
**Mode:** Claude Code, dev Mac (`/Users/brock/...`)
**Type:** Build + extraction burn. Serialized stages; extraction does not fire until
Stages 0–3 are verified DONE.
**Writes:** ai-readiness-kg repo (manifest artifacts, corpus/cisco merge, config,
events, extraction outputs), `~/.wintermute/` (federation.yaml + panel changes per
Stage 3 only), RESULT file. fss-policy-kg is READ-ONLY (threshold port only).
**Immutability:** This file is immutable once written. Addendum files only.
**Status:** approved for execution

---

## Operator decisions this task implements

1. **Baseline freezes on what we have.** v1 corpus = the 71 verified-included docs
   plus the recombined cisco document if it passes integrity. Refetch-worklist items
   (18) STAY in the manifest with acquisition status — they are carried evidence
   candidates, not forgotten. Every future addition gets tagged with the corpus
   version it entered under (`added_in: v1 | v1.1 | ...`). Continuous build is the
   design center.
2. **Cisco fragments are one document.** They are manually printed pages of a single
   survey instrument (per-page components titled by topic: infrastructure,
   governance, etc.). Recombine into ONE compound document; manifest it as one
   evidence item.
3. **Budget diversion.** Wintermute ingest/extraction cycles PAUSE; their daily token
   band is redeclared against this project's extraction. The control plane's Stage-6
   primitives (project-tagged admission, declared caps, switches) execute this — no
   new plane machinery.
4. **Raw-response retention is a harness invariant** (S1 finding). Every model
   response persisted alongside events. This run is the engine's future parity
   baseline; retention is non-negotiable.

## Stage 0 — Manifest collision fix (GATES EVERYTHING)

`kg.manifest rebuild` (v1-era machinery) writes to the path now occupied by the v2
evidence ledger. Close the landmine:
- Preferred: rewire `kg.manifest` so the Dixie decisions log is truth and the
  manifest is its projection — rebuild regenerates FROM the decisions log,
  byte-stable on unchanged input (verify: rebuild twice, diff empty, v2 content
  preserved).
- Fallback if rewiring exceeds ~a session's effort: hard-deprecate the rebuild path —
  loud error naming the Dixie ledger and this task file. No silent no-op.
- Verify whichever path: run the old command; prove the v2 ledger survives.

## Stage 1 — Cisco recombination + manifest v1 freeze

- Merge the 6 cisco per-page components into one PDF, ordered by the instrument's
  own structure (component titles/page evidence — verify order from content, don't
  guess). Run the merged artifact through Dixie integrity (magic bytes, text-extract
  smoke, sha256). Manifest entry: ONE document; acquisition_channel:
  manual_page_capture; provenance lists all 6 component hashes; components archived
  in place (moved to a `corpus/components/` dir, never deleted), marked superseded_by
  the merged hash.
- If the merge fails integrity or page order is genuinely ambiguous: quarantine with
  reason, cisco doc joins the refetch worklist, baseline proceeds at 71. STOP is not
  required for this — record and continue.
- Freeze baseline: `min_verified_included = 71` in the Dixie config instance;
  corpus epoch `v1` declared as an event; every included doc stamped `added_in: v1`;
  the 18 refetch items remain manifested as `pending_refetch` with their worklist
  metadata. Emit the corpus-epoch event BEFORE extraction begins so provenance can
  cite it.

## Stage 2 — Threshold pre-registration (fss port)

- READ fss-policy-kg's realized health-check values (grounding rate, edge/
  relationship validation, orphan rate, and the other two checks at TO_BE_SET —
  discoverable in its repo/run artifacts; read-only).
- Write them into the ai-readiness gate config as the pre-registered v1 thresholds,
  with one doctrine override: grounding is ZERO-UNGROUNDED absolute, not a rate
  threshold. Record in the RESULT the exact fss values ported and their source
  artifacts, flagged for operator review. Expectation stated in config comments: the
  heterogeneous corpus may fail edge/orphan gates — a failed gate triggers
  investigation, never retuning to pass.

## Stage 3 — Budget diversion via the control plane

In `~/.wintermute/`:
- Flip Wintermute's ingest + extraction cycle switches OFF (identify the exact
  switches from panel/config; list them in RESULT). Molly harvest cycles included.
  Reconcile/federation cron and Arnold are NOT touched.
- Redeclare in `federation.yaml` (new config epoch, event emitted): project
  `ai-readiness-kg` extraction job with daily cap equal to the band Wintermute
  extraction held (read the current declared value; do not hardcode from memory),
  priority class appropriate for an operator-directed run.
- Extraction runner (Stage 4) must submit to admission (project-tagged) and take the
  global burn lease per heavy-loop convention. Verify with a dry admission check
  before any real burn.
- Verify the pause: confirm the next scheduled Wintermute cycle no-ops with the
  switch-off reason, not an error.

## Stage 4 — Extraction burn

- Corpus: exactly the v1 baseline set (71 or 72). Model: current extraction model per
  standing config (Max OAuth only — no API keys exist and none may be created).
- Per-document loop with STOP-per-doc discipline: extraction → grounding
  verification (verbatim spans, zero-ungrounded or the item is rejected/quarantined,
  never admitted) → events appended → RAW MODEL RESPONSE persisted (path convention:
  alongside events, keyed by doc sha256 + prompt epoch + model_id). Chunk-resumable:
  an interrupted run resumes without re-burning completed docs.
- Every extracted item stamps: model_id, prompt epoch, schema epoch (v0.2), corpus
  epoch (v1), source doc sha256.
- Budget behavior: when the daily cap trips, the run no-ops cleanly and resumes next
  window — cap-tripping is normal operation, not failure. Expect this to take
  multiple days at the diverted band; report per-day progress in the RESULT as
  appended sections.

## Stage 5 — Post-run gates + report (no promotion beyond gates)

- Run the pre-registered health checks from Stage 2 against the built graph
  (projection per existing ai-readiness machinery; if no projection builder exists
  yet in this repo — the S1 finding — build the minimal events→Neo4j projection
  needed to run the checks, into `seldon-ai-readiness-kg`'s KG database per repo
  convention, NOT the Seldon project DB; state clearly in RESULT what was built).
- Report per-gate: pass/fail against pre-registered values. FAILED GATES DO NOT
  BLOCK THE RESULT — they are the finding. No retuning, no re-runs to pass.
- Final numbers: docs processed, items extracted, grounding stats (must show zero
  admitted ungrounded), per-gate outcomes, total tokens burned vs declared cap,
  raw-response archive size and location.

## Hard stops
- Stage 0 gates all burns. No extraction before Stages 0–3 verified.
- Zero ungrounded admitted, ever. Rejected items are recorded rejections, not
  silent drops.
- No writes to fss-policy-kg. No new API keys. No Wintermute re-enable — Wintermute
  cycles stay OFF until the operator flips them back.
- No threshold retuning after seeing data. Pre-registered values stand for v1.
- Manifest truthfulness absolute: cisco merge provenance complete or quarantined.
- Do not touch the federation dedup guard state (ON/OFF stays as operator left it).

## Done =
`cc_tasks/2026-07-05_airkg_bulk_extraction_v1_RESULT.md` in ai-readiness-kg:
per-stage evidence, Stage-3 switch/epoch record, per-day burn progress, Stage-5 gate
report, raw-response archive manifest. Operator gates: promotion/publication of the
graph, Wintermute cycle re-enable, refetch campaign scheduling.
