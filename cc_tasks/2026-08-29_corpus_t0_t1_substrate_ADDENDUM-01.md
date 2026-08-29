# ADDENDUM-01 to 2026-08-29_corpus_t0_t1_substrate.md — pre-flight hash reconciliation, two acquisition additions

**Date:** 2026-08-29. Trigger: 3d86f16d RESULT. Runs as §-0.5, before §0. Task file immutable; this amends.

## -0.5 Resolve the 4 pre-existing `hash_mismatch` entries before building any index

T0 keys metadata and T1 keys chunks/embeddings to `content_hash`. Building either on a corpus with 4 unresolved mismatches indexes ambiguous bytes. Resolution is derivable from the architecture, not an operator call (decision logged here; operator overrides by addendum): **the manifest_add event is the truth about what was admitted; the file on disk is the drifted party until proven otherwise.**

Per mismatched doc:
1. Pull the dixie evidence-ledger record (acquisition integrity layer) for the admission — it holds the verified acquisition hash. Three-way compare: event hash, dixie hash, disk hash.
2. `disk ≠ event = dixie`: disk drifted. Re-fetch from `primary_url`; if the fetch matches the event hash, restore those bytes. If the fetch matches today's disk (source silently revised), keep disk and append a supersession event (`content_update`, reason `source_revised`, old and new hashes) — never rewrite the original event.
3. `event ≠ dixie`: the admission event itself recorded wrong — append a correction event citing the dixie record; report loudly, since that's an admission-pipeline defect, not drift.
4. `primary_url` dead: keep disk bytes, append `content_update` with reason `source_unavailable_disk_adopted`, flag the doc `provenance_degraded`.
Report the three-way table for all 4 in the RESULT. No silent re-hashing anywhere. T0/T1 proceed only when `kg.manifest verify` is clean or every residual mismatch carries an explanatory event.

## §2 additions

- **W3C PROV-DM + PROV-O** join the acquisition queue (3d86f16d found D3's "PROV-aligned standards nodes" was a false lexical match; the actual provenance vocabulary is not in the corpus).
- **Commerce GenerativeAI-Open-Data guidance**: Cloudflare-blocked (3d86f16d, `acquisition_blocked`). Manual-download lane: if the operator has placed the PDF in the inbox by dispatch time, admit it normally and resolve the A1/B1 gaps; if not, leave blocked and note.

## Recorded, not in scope here

Seldon domain-config defect from 3d86f16d (no `Documentation` artifact type; `DesignNote` cannot link `ResearchTask`, provenance carried only as a property invisible to edge queries) — belongs to the seldon repo, not this project; queued as a seldon-repo task.
