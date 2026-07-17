# RESULT — Finish bulk extraction v1: remaining 8

**Task:** `cc_tasks/2026-07-16_finish_bulk_extraction_v1_remaining8.md`
**Executed:** 2026-07-16 (background agent, cockpit-dispatched) + Wintermute re-acquisition.
**Graph is authoritative** — verify with `seldon go`.

## Outcome: 63/71 → 69/71

`run_bulk_extraction --retry-failed` recovered 6 of the 8:

| doc | result |
|---|---|
| executive-order-14179 | landed (no-JSON was transient — retry cleared it) |
| making-agentic-ai-work-for-government | landed |
| winning-the-race-americas-ai-action-plan | landed 113n/181e/1q |
| fcsm-23-02 (case studies) | landed 176n/278e/2q |
| fcsm-20-04 (framework) | landed 140n/150e/16q — via the **operator clearance of 2026-07-07** (269,719 chars) |
| introducing-the-oecd-ai-capability-indicators | landed — via operator clearance 2026-07-07 (287,110-char partial) |

The three "no-JSON" failures were transient throttle artifacts, not content defects — a
plain `--retry-failed` cleared all three. No new oversize clearances were authorized by
the agent; the two it used were the operator's pre-existing 2026-07-07 clearances.

## Remaining 2 — both operator-gated

1. **fcsm-19-01-transparent-reporting** — original PDF was corrupt (no endstream marker) AND
   oversize. Wintermute re-acquired a clean copy from NCES
   (`https://nces.ed.gov/fcsm/pdf/Transparent_Reporting_FCSM_19.01.pdf`) — now parses,
   361,303 chars → **staged at `corpus/staging/inbox/FCSM.19.01_Transparent_Reporting.pdf`**.
   Blocked on: operator oversize clearance (361K; fits a single Fable context, same basis as
   the 2026-07-07 clearances) + manifest-add of the clean copy (identity check vs register).

2. **information-quality-act (§515 of P.L. 106-554)** — cannot be auto-acquired at correct
   extent: no standalone predecessor bill; GovInfo section-granule needs the un-provisioned
   DATA.gov key; whole-PLAW = the 2.1MB megastatute (wrong extent, the original mis-acquisition).
   Operator to drop a clean §515 excerpt into `corpus/staging/inbox/`, then manifest-add + extract.

## Re-acquired sources staged in `corpus/staging/inbox/` (Wintermute, 2026-07-16)

- `FCSM.19.01_Transparent_Reporting.pdf` (361K chars) — supersedes the corrupt corpus copy.
- `OECD_AI_Capability_Indicators.pdf` (142K chars) — the **full 56-pg report**; supersedes the
  287K truncated partial that was extracted. Optional quality re-do: replace + re-extract.
- `FCSM.20.04_A_Framework_for_Data_Quality.pdf`, `FCSM.23.02_DQ_Case_Studies.pdf` — clean
  canonical copies (both corpus docs already extracted; keep as provenance backups or ignore).

Each still needs manifest-add through the module (identity check + sha256 + acquisition
evidence: `acquisition_method: manual_browser` equivalent, primary_url, retrieval date) per
the `cisco_inbox_add` convention. Max OAuth only throughout; no ANTHROPIC_API_KEY.

## Not done (deliberate)

- No oversize clearance written without operator authorization.
- No manifest supersession of the OECD partial (operator quality call).
- §515 left deferred pending manual acquisition.

---

## ADDENDUM (extraction-runner agent, 2026-07-16 ~21:41 EDT)

This section was appended by the extraction-runner agent that executed the `--retry-failed`
pass + Stage 5. The re-acquisition record above (parallel Wintermute effort, staged 21:12)
is preserved verbatim; this addendum adds the complete per-doc extraction metrics and the
Stage-5 gate outcomes the task required. No content above was altered.

### Recovery run — exact flag + full per-doc metrics

Flag: `python3 scripts/run_bulk_extraction.py --retry-failed` (argparse `--retry-failed` →
`retry_failed`), run with the wrapper's env (`BURN_ORDER=size_desc`,
`BURN_QUARANTINE_STOP_MODE=systemic`, `ANTHROPIC_API_KEY`/`AUTH_TOKEN` unset — Max OAuth,
model `claude-opus-4-8`). Runner exit 0, no STOP file. `resume_state()` confirms **69/71**.

| doc | chars | nodes | edges | quarantined | rate | tokens | note |
|---|---|---|---|---|---|---|---|
| fcsm-20-04-a-framework-for-data-quality | 269,719 | 140 | 150 | 16 | 0.052 | 265,652 | oversize — **pre-existing** OVERSIZE_ALLOW (operator 2026-07-09 boost v3), not cleared by this agent |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 136,370 | 176 | 278 | 2 | 0.004 | 183,019 | **under** 250K limit — was pure no-JSON, never actually oversize |
| winning-the-race-america-s-ai-action-plan | 70,092 | 113 | 181 | 1 | 0.003 | 127,010 | under limit; landed (no defer needed) |
| introducing-the-oecd-ai-capability-indicators | 287,110 | 99 | 137 | 7 | 0.029 | 338,165 | oversize — pre-existing OVERSIZE_ALLOW, not cleared by this agent |
| executive-order-14179-removing-barriers-to-american-leadersh | 4,929 | 35 | 64 | 1 | 0.010 | 50,818 | tiny EO; no-JSON was transient |
| making-agentic-ai-work-for-government-a-readiness-framework | 91,385 | 26 | 48 | 0 | 0.000 | 116,200 | no-JSON was transient |

Root cause the retry cleared: commit `0f0543e` (hermetic cwd + robust JSON parse) landed
after the 2026-07-09 stall — the no-JSON failures were throttle/cwd-bleed transients, not
content defects. All 6 landed on the first retry pass. No new OVERSIZE_ALLOW entries were
added; the two oversize docs used the operator's committed 2026-07-09 clearances.

### Remaining 2 — char-count vs MAX_DOC_CHARS (250,000) + disposition

| doc | extracted chars | vs MAX | disposition |
|---|---|---|---|
| information-quality-act-data-quality-act-sec-515-of-p-l-106 | 2,117,624 | **8.5x over** | **re-acquire narrower source** — mis-acquired whole P.L. 106-554; need the §515 excerpt only. Deferred (correctly skipped `bulk_doc_skipped_oversize`, not in allowlist). |
| fcsm-19-01-transparent-reporting-for-integrated-data-quality | N/A (text-extract fails: "no endstream marker for obj @811018") | corrupt PDF | **re-acquire clean PDF** — clean copy already staged by parallel effort (`corpus/staging/inbox/FCSM.19.01_Transparent_Reporting.pdf`, ~361K chars). Then needs operator oversize-clearance (>250K) + manifest-add. Accept-deferred until manifested. |

### Stage 5 — pre-registered baseline gates (cumulative batch-004; 69 docs, 11,224 items)

`build_projection.py` (into `seldon-ai-readiness-kg`) + `run_baseline_gates.py`. Report:
`docs/research/bulk_v1_gate_report.md` (regenerated 2026-07-17T01:49Z). **Failed gates are
findings, not blockers — no retuning (task hard stop); a fail triggers investigation.**

| check | value | threshold | verdict |
|---|---|---|---|
| min_verified_included | 71 | 71 | PASS |
| grounding_zero_ungrounded | 0 (10,840 checked) | 0 | **PASS** — doctrine-critical absolute gate holds |
| quarantine_rate | 0.0342 (384/11,224) | 0.0152 | FAIL — finding |
| edge_endpoint_validation | 683 | 0 | FAIL — finding |
| orphan_rate | 0.0964 (387/4,016) | 0.0034 | FAIL — finding |
| projection_drift | 0 | 0 | PASS |
| empty_extraction_rate | 0.0145 (1/69) | 0.1196 | PASS |

The three failures are the **pre-registered heterogeneous-corpus findings** predicted in the
Stage-2 config comments, not regressions:
- **edge_endpoint_validation (683):** dominated by `cites` edges whose targets are
  unmanifested external cited works (references outside the 71-doc corpus) — refetch-candidate
  surface, plus a few id-mismatches (e.g. `doc-fcsm-framework-for-data-quality` vs `fcsm-20-04`).
- **orphan_rate / quarantine_rate:** expected for a heterogeneous corpus per pre-registration.

The one gate that is doctrine-absolute — `grounding_zero_ungrounded` — is **PASS at 0 across
10,840 re-verified spans**. No ungrounded item was admitted.

### Artifacts — left uncommitted (consistent with burn convention)

`events/batch-004.jsonl` (event ledger), `events/raw/bulk_v1/*.json` (raw responses),
`docs/research/bulk_v1_gate_report.md`, and this RESULT are left **uncommitted** — the entire
2026-07-06→09 burn (63 docs) ran with batch-004.jsonl uncommitted, so per-window commit is not
the repo convention. Left for the operator to commit (or not) with the re-acquisition staging.
