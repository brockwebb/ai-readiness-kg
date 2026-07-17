# Task — Finish bulk extraction v1: the last 8 docs (63/71 → 71/71)

**Opened:** 2026-07-16 (Wintermute cockpit dispatch)
**Predecessor:** `cc_tasks/2026-07-05_airkg_bulk_extraction_v1.md` (+ RESULT). The burn
reached **63/71** on 2026-07-09 and its window-driver stopped. No STOP file present —
the runner simply clean-no-op'd because the remaining 8 are all at the retry ceiling or
oversize-deferred, which a plain resume can't advance.
**Graph is authoritative** — verify counts with `seldon go` in this repo, not this prose.

## Remaining 8 (authoritative, via `run_bulk_extraction.resume_state()`)

| doc_id | source | fail_attempts | class |
|---|---|---|---|
| executive-order-14179-removing-barriers-to-american-leadersh | 184KB | 3 | no-JSON ceiling → **recoverable** |
| making-agentic-ai-work-for-government-a-readiness-framework | 91KB | 3 | no-JSON ceiling → **recoverable** |
| winning-the-race-america-s-ai-action-plan | 522KB | 3 | no-JSON ceiling → recoverable IF <250K chars, else oversize |
| oecd-ai-capability-indicators (introducing-…) | 287KB | 2 | borderline oversize |
| fcsm-23-02-a-framework-for-data-quality-case-studies | 782KB | 3 | oversize + no-JSON |
| fcsm-20-04-a-framework-for-data-quality | 1.11MB | 2 | oversize |
| fcsm-19-01-transparent-reporting-for-integrated-data-quality | 1.46MB | 3 | **PDF-parse fail** (no endstream marker) + oversize |
| information-quality-act-data-quality-act-sec-515-of-p-l-106 | 2.07MB | 0 | **mis-acquired megastatute** — runner flags "stays deferred" |

## Do now (autonomous — mechanical, no judgment)

1. `python3 scripts/run_bulk_extraction.py --retry_failed` (confirm exact flag from argparse).
   Re-opens the no-JSON-ceiling docs. Expect the two small ones (exec-order-14179,
   making-agentic-ai) + possibly winning-the-race to land. Grounding validator + the
   pre-registered `baseline_gate.post_extraction_checks` thresholds gate as normal —
   a failed gate triggers investigation, never retuning (per predecessor Stage 2).
2. Run **Stage 5** (post-run gates + report, `cc_tasks/2026-07-05…` §Stage 5) on
   whatever the retry lands. Report per-doc node/edge/quarantine like the burn log.

## DO NOT (operator judgment — escalate, do not decide autonomously)

- **Oversize clearances** (`bulk_doc_oversize_cleared`) are operator-authorized + ledgered.
  Do NOT clear/truncate `information-quality-act`, `fcsm-20-04`, `fcsm-23-02`, or
  `oecd-capability-indicators`. Report their extracted char-counts vs MAX_DOC_CHARS so the
  operator can decide: re-acquire a narrower primary source, chunk, or accept-deferred.
- **PDF re-acquisition**: `fcsm-19-01` fails text extraction (corrupt/complex PDF). Flag for
  re-fetch; do not attempt a lossy parse.
- `information-quality-act`: the runner already flags it as almost-certainly mis-acquired
  (2.1M chars = whole P.L. 106-554, not just §515). Recommend re-acquire the §515 excerpt;
  leave deferred until then.

## Done when

- `--retry_failed` run complete, recoverable docs extracted + gated, Stage 5 report written.
- A RESULT file lists: which of the 8 landed, and the per-doc disposition of the residual
  oversize/PDF docs (each: re-acquire | chunk | accept-deferred) for operator sign-off.
- No oversize clearance or truncation performed. Max OAuth only; no ANTHROPIC_API_KEY.
