# Desktop session close — 2026-08-27

**Project:** ai-readiness-kg. Graph state is authoritative; this is lossy prose. Open with `seldon_go`, then `kg queue status` once 00968603 lands, then `python -m kg.spend status`.

## What changed since the 2026-08-25 handoff (all on the ledger)

- **Task hygiene:** 7 CC tasks that had RESULT files but sat at `proposed` (CC never ran `seldon cc complete`) were closed 08-26 with dated notes. Systemic since 08-21; the "run `seldon cc complete` before RESULT" line now belongs in every dispatch preamble.
- **7456614d source triage — complete.** Input list reconstructed from the 08-24 chat (`docs/research/2026-08-24_sme_source_list.tsv`, 72 rows, provenance `desktop_transcription_from_chat`, ADDENDUM-02). 34 manifest adds → **168 included**. 9 max.gov decks `awaiting_operator_drop`, 10 `access_blocked` (6 regulations.gov letters, SSRN, Wiley×2, World Scientific), CES-WP-26-25 flagged off-construct → exclude. Schema v0.3.3 (`construct_arm`, `grounding_surface`). RFI + comments index mis-tagged `org_maturity` by my R3 placement; retag to `publication_actionability` rides Lane 3 Phase 0.
- **d2756bd1 spend guard — complete.** `kg/spend.py`, reserve-then-settle, flock ledger `state/spend_ledger.jsonl`, wired at `model_stub.invoke`; local counters deleted from 4 callers; `--ceiling-tokens` required; DD-022. `controls.yaml spend.daily_tokens = 55M` (standing band). Two production refusals so far, both correct.
- **cd8449de overnight burn — running, 6 addenda.** Prompt v0.3.4 → v0.3.5 (Instrument positive criterion, node-span rule, truncation→status + per-layer fallback). Schema v0.3.4 (Instrument per-attribute `grounding_spans`). **Model pinned `claude-opus-5`** (ADDENDUM-04; verified in platform docs 08-27 — Desktop's product knowledge was stale, Opus 5 shipped 07-24). Opus 5 truncates single-pass at 108–158K output on 3/4 docs; per-layer fallback is now the normal path; ~977K/doc.
- **00968603 extraction queue — registered, not yet reported.** `extraction_request` event, derived `extraction_state` (incl. `stale`), `kg queue status|add|add-epoch|withdraw|next|explain`, ledger-derived worklists, backfill 134+34.

## Pilot state (the gate on all new extraction)

- Instrument stratum: pooled 24 ≥ 20 under Opus 5 + v0.3.5; judge queued behind the 00:05Z band roll. PASS ⇒ Lane 2 Instrument-only supersession.
- Semantic stratum: v0.3.5 over-suppresses (38 kernel edges → 0 on the test doc; 89 locatable diverted candidates, 52 single-span). §3b entailment judge (≤2M) decides; ≥ 0.85 ⇒ v0.3.6 = evidence-set grounding + diversion-as-exception + `diversion_reason` (ADDENDUM-05/06) ⇒ edges-only resumed-session pilot ⇒ Lanes 2 (both strata) and 3 (34 docs). Lane 3 does not run on an Instrument-only pass (rework cost).
- Thresholds never moved: F_upper < 0.10 per stratum, item faithful ≥ 0.70; precondition pooled ≥ 20 per stratum.

## Lane 4 (restoration v2 + relocation)

Stage 2 ~4,400/5,554 at close; then 100-item class gate ≥ 0.90 (gate before wire); relocation resume + 50-item re-judge wait for the 00:05Z roll (band priority to pilot work). Wall stop 2026-08-28T03:30Z. SUMMARY: `docs/research/2026-08-27_overnight_burn_SUMMARY.md` at driver exit, all lanes from the ledger.

## Defects owned by Desktop this session (for the methodology doc)

1. Unmeasured estimates in addenda: "65 rows" (was 72); 4M pilot ceiling (needed ~9M at Opus 5 cost). Estimate before declaring, from the ledger.
2. Per-doc conjunction precondition confused "document contains nothing" with "prompt produced nothing"; fixed to pooled per-stratum.
3. Clock-time wall stops written for a night that had ended; use absolute UTC.
4. Stale model knowledge; verify product facts in docs before pinning.
5. "No prompt revision tonight" rule was for an unattended operator; distinguish guess (forbidden) from measured revision (allowed).

## Open, in order

1. Read SUMMARY + verdicts; on both-strata PASS confirm Lanes 2/3 ran or dispatch them; on FAIL, the verdict's top-3 is the next design input.
2. `daily_tokens` stays 55M — nothing raised it. No restore needed.
3. **Methodology document** (`docs/research/kg_construction_methodology.md`) — still the Desktop deliverable. Describe the pipeline as it exists after cd8449de and 00968603: admission (inbox→register→manifest event) ≠ request (`extraction_request`) ≠ extraction (profile + model epoch); pilot gate before bulk; probe protocol; quarantine as write barrier; gate-before-wire repair; spend guard; the five defects above as process rules.
4. Dedup design (blocked on Lanes 2 and 4): deterministic pre-dedup → LLM-proposed merges w/ confidence → adjudication events; sift-kg three-layer as prior art.
5. Deferred, not dropped: TrustGraph extraction-time validation port; model-assisted admission triage ("read on drop" → document card, `signal_not_verdict`); max.gov decks and blocked PDFs when operator has them.
6. Wintermute `hub.home` static launchpad — untouched this session.

## Dispatch preamble (standard, add to every CC task)

Glob and read all `_ADDENDUM*.md` siblings first. Run `seldon cc complete <task file>` before writing the RESULT. Report discrepancies between task premises and live state; never reconcile silently. Estimate spend from the ledger's per-class running mean before declaring any ceiling.
