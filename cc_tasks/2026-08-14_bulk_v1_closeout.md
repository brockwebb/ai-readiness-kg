# CC Task — AIRKG bulk-v1 closeout: fcsm-19-01, OECD supersession, id-mismatch fix

**Date:** 2026-08-14
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Max OAuth only. ANTHROPIC_API_KEY must remain unset — abort if any script path requires it.
**Operator clearances recorded in this task (granted 2026-08-14, Desktop session):**
- **CLEARANCE 1 — oversize:** `fcsm-19-01-transparent-reporting` at ~361,303 chars, cleared above MAX_DOC_CHARS (250,000). Same basis as the 2026-07-07/09 clearances (fits a single whole-doc context). Record as OVERSIZE_ALLOW entry with this task file as authorization reference.
- **CLEARANCE 2 — supersession:** replace the truncated 287,110-char partial of `introducing-the-oecd-ai-capability-indicators` with the staged full 56-page report and re-extract. Quality call ruled by operator.

## Scope (three items, in order)

### 1. fcsm-19-01 — manifest-add + extract

- Source staged: `corpus/staging/inbox/FCSM.19.01_Transparent_Reporting.pdf` (clean NCES copy; original corpus copy was corrupt — no endstream marker).
- Manifest-add through the manifest module per the `cisco_inbox_add` convention: identity check vs candidate register, sha256, acquisition evidence block (`primary_url: https://nces.ed.gov/fcsm/pdf/Transparent_Reporting_FCSM_19.01.pdf`, re-acquired by Wintermute 2026-07-16, retrieval evidence from that staging if recorded).
- Add OVERSIZE_ALLOW per Clearance 1, then extract via the standard runner (whole-doc protocol, same config as bulk v1 — no config changes).
- The corrupt prior corpus copy: supersede in manifest, never delete. Event-sourced.

### 2. OECD — supersede + re-extract

- Full report staged: `corpus/staging/inbox/OECD_AI_Capability_Indicators.pdf` (~142K chars — under limit, no clearance needed).
- Manifest supersession of the truncated partial per Clearance 2 (identity check, sha256, acquisition evidence). Prior extraction is superseded in events, not deleted; projection must show only the new extraction.
- Re-extract with standard runner, same config.

### 3. Edge id-mismatch fix + cites triage surface

- Decompose the 683 `edge_endpoint_validation` failures into (a) doc-id mismatches (e.g., `doc-fcsm-framework-for-data-quality` vs `fcsm-20-04`) and (b) `cites` targets that are unmanifested external works.
- Fix (a) only: event-sourced amendment or projection-time canonical-id mapping — whichever the repo's existing mechanism supports. No raw-event mutation. Document the mechanism chosen in RESULT.
- For (b): produce a register-style candidate list artifact (`corpus/staging/refetch_candidates.jsonl` or repo-conventional equivalent) with citing-doc provenance, sorted by citation count. **Do NOT manifest-add anything from it.** Corpus expansion is Desktop triage per DD rulings.

## Then

- Rebuild projection (`build_projection.py` → `seldon-ai-readiness-kg`).
- Re-run baseline gates (`run_baseline_gates.py`) — **thresholds frozen, zero retuning; fails are findings**. Expect edge_endpoint_validation to drop by the (a) subset and remain nonzero from (b); expect grounding_zero_ungrounded to hold at 0 — if it doesn't, STOP and report, do not proceed.
- Gate report as NEW dated artifact: `docs/research/2026-08-14_bulk_v1_closeout_gate_report.md`, with deltas vs the 2026-07-17 report.

## Out of scope

- §515 excerpt (operator manual acquisition, still pending — corpus stays 70/71 extracted... verify actual count, report it).
- FCSM 20.04 / 23.02 provenance-backup copies in inbox: leave untouched.
- Git commits: leave uncommitted per burn convention; operator commits.
- Any corpus expansion, any threshold change, any config change.

## Completion

`_RESULT.md` sidecar: per-doc extraction metrics, gate table with deltas, id-mismatch fix mechanism + count fixed, refetch-candidate list size, discrepancies vs figures quoted here (report live numbers, flag, never reconcile silently), token cost.
