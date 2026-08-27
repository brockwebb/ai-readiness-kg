# ADDENDUM-02 to `2026-08-24_source_triage.md` (Seldon 7456614d)

**Date:** 2026-08-26
**Supersedes the "operator drops the file" clause of ADDENDUM-01.** The operator no longer has the original export. Desktop wrote `docs/research/2026-08-24_sme_source_list.tsv` from the 2026-08-24 Desktop chat transcript (turn where the list was pasted). All other ADDENDUM-01 clauses stand.

## Provenance of the drop file (record this in the Phase 0 sub-RESULT)

- `source: desktop_transcription_from_chat_2026-08-24` — not the operator's original file. Treat as `signal_not_verdict` for the *list itself*, same as the vetting weight already assigned to its rows.
- Transformations applied by Desktop, and only these: HTML entities de-escaped (`&amp;` → `&`); the CES-WP-26-25 bare link from above the table inserted as row 1 with `Industry=Government`, `Author/Organization=Census Bureau (CES-WP-26-25)`, `Year=2026`, empty Summary/Tags. No other edits — original typos, stray spaces, and trailing tabs preserved.
- Known TSV hazard: the SAS Institute row's Summary cell contains an embedded blank line inside a double-quoted cell (as in the original paste). Parse with a quote-aware TSV reader (`csv.reader(..., delimiter='\t')`), not `line.split('\t')`.
- Row count Desktop expects: **65 data rows** (1 inserted + 64 transcribed). Report the actual count; any mismatch is a discrepancy to log, not reconcile.
- The chat retrieval tool marked the source turn as possibly truncated at its end. The last transcribed row is Tiger et al. 2024 (arXiv 2409.03805). If Phase 1 fetches reveal the FSS group later supplies rows beyond that, they enter via a new addendum, not by editing this file.
