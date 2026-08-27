# Finish the pilot — both strata to a verdict, tonight

**Date:** 2026-08-27 (evening ET)
**Lineage:** continues `2026-08-26_overnight_burn.md` ADDENDUM-05 §2–§3 and ADDENDUM-06 (Seldon cd8449de, already closed in the graph at the 03:35Z RESULT — hence a new task file, not a seventh addendum; the protocol is theirs, unchanged).
**Operator decision (touchpoint #1, spend above band):** the pilot does not wait for the 00:05Z roll. Daily band raised for the duration of this task. Thresholds do not move.

## Preamble (standard)

Glob and read all `_ADDENDUM*.md` siblings of `2026-08-26_overnight_burn.md` first (there are six). Run `seldon cc complete cc_tasks/2026-08-27_pilot_finish.md` before writing the RESULT. Report discrepancies between task premises and live state in the RESULT; never reconcile silently. Estimate spend from the ledger's per-class running mean (`python -m kg.spend status`, settled totals ÷ calls per run) before declaring any ceiling; write the arithmetic in the RESULT.

## 0. Live-state premises (verify each; report any that are false)

- Daily band: `controls.yaml spend.daily_tokens = 55,000,000`; ledger shows `over_daily` refusals at 18:53Z for both `restoration_v2_resume` (pid 70596) and `pilot_v035b_opus5` (pid 91558).
- Lane 4 (pid 70596) is in `daily_band_sleep` until 2026-08-28T00:05Z per `state/overnight_burn_status.json`. Leave it alone; it wakes itself.
- The pilot process (pid 91558) took its refusal at 18:53:08Z; its post-refusal state is unrecorded. Check `ps`; if it is still alive and sleeping, kill it — this task relaunches the pilot explicitly.
- `pilot_v035b_opus5` was re-declared at 9M per ADDENDUM-05 §0 (the 18:52Z calls prove it was dispatching past 4M). Confirm on the ledger.
- Banked: 4 pilot extractions on `batch-013_reextract_v035b`; ADDENDUM-05 §3a triage counts on disk (`docs/research/2026-08-27_edge_suppression_triage.md`: 89 locatable, 52 `single_span`). Doc 5 (`mitre-ai-maturity-model`) status: the handoff claims Instruments pooled 24 (implying doc 5 ran); the v035b verdict and status file say 23 from 4 docs. Resolve from the event shard, not from either document. If doc 5 is not on the shard, extract it.

## 1. Band raise (the one config edit this task makes)

Set `controls.yaml spend.daily_tokens: 75000000`. Commit with message `spend: daily_tokens 55M→75M for pilot finish (operator decision 2026-08-27, task 2026-08-27_pilot_finish)`. Verify `python -m kg.spend status` reports the new daily ceiling. If `kg/spend.py` caches the value at process start rather than reading it per reserve, note that in the RESULT — it means the raise only reaches processes started after the edit, which is fine for this task since the pilot is relaunched, but it is a property the operator should know.

Sizing (write your own from the ledger; this is the authoring estimate): ~20M of new headroom over the 54.98M committed. Remaining pilot work: doc 5 ≤1M if needed + Instrument judge (decompose + 2 raters, per ADDENDUM-02 protocol) + §3b ≤2M + §3d ≤9M ceiling. The Lane 4 stage-2 remainder (~1,150 judgments at ~5.7K ≈ 6.6M + 100-item gate) will also fit if Lane 4 wakes before the roll — it doesn't; it sleeps to 00:05Z, so today's raise is pilot-only in practice.

**Revert at task close:** after the §3d verdict is on disk (or the stratum is closed at §3b), set `daily_tokens` back to `55000000` and commit. The raise is scoped to this task, not a new standing band. If the operator wants the standing band changed, that is a separate decision.

## 2. Execute ADDENDUM-05 §2 — Instrument stratum

Ensure doc 5 is extracted (§0). Run the Instrument judge exactly as pre-registered (ADDENDUM-02 protocol; F_upper < 0.10, item faithful ≥ 0.70; precondition pooled ≥ 20 already met). Verdict to `docs/research/2026-08-27_pilot_instrument_verdict.md`. Instrument PASS ⇒ record `superseded_strata: [Instrument]` eligibility for Lane 2. **Do not launch Lane 2.** See §5.

## 3. Execute ADDENDUM-05 §3b — semantic-edge entailment judge

Run id `edge_suppression_judge`, ceiling ≤ 2M (declare from the per-class mean × candidate count; cap 120 candidates, random, seed recorded). Judge the `single_span` + `evidence_set` candidates from §3a with the located evidence set as grounding. Pre-registered read: fact-level entailed ≥ 0.85 pooled ⇒ over-suppression confirmed, proceed to §4; below ⇒ close the semantic stratum with the number, skip §4, go to §5. Verdict to `docs/research/2026-08-27_edge_suppression_judge_verdict.md`.

## 4. On §3b PASS only — ADDENDUM-05 §3c + ADDENDUM-06, then §3d

Author v0.3.6 exactly as ADDENDUM-05 §3c amended by ADDENDUM-06 (evidence-set grounding; diversion-as-exception with the two worked examples and one counter-example; `diversion_reason` closed list on `proposed_relationships`; parser joint-coverage + 800-char distance validation; profile `reextract_v036` sha-pinned; the three named unit tests plus a `diversion_reason` schema test). Suite green before any spend.

Then §3d: run id `pilot_v036_edges`, ceiling 9M, `--resume` each pilot doc's Opus 5 session for an edges-only turn; full re-extraction on resume failure. Pooled precondition ≥ 20 admitted semantic edges; judge as pre-registered; F_upper < 0.10, item faithful ≥ 0.70. Verdict to `docs/research/2026-08-27_pilot_v036_edges_verdict.md`, carrying the ADDENDUM-06 informational counts (diversion histogram per doc; fraction of §3a `single_span` candidates now admitted).

If the resumed-session path is not implemented in the harness, say so in the RESULT and fall back to full re-extraction under `reextract_v036` — at ~977K/doc that is ~5M and inside the 9M ceiling. Do not build session-resume tonight to save tokens; the operator has declared the headroom.

## 5. Lanes 2 and 3 — NOT launched by this task (deviation from ADDENDUM-05 §5, stated)

ADDENDUM-05 §5 launches Lanes 2/3 detached on PASS. This task overrides that clause. Reason: at the measured ~977K/doc, Lane 2 is ~134 × ~1M ≈ 130M+ and Lane 3 another ~34M — a multi-day spend at any band, and the operator has an open question on whether the per-doc unit cost (full verbatim-span emission, single-call whole-document, per-layer fallback) is the thing to fix before bulk. That is a separate decision with its own task. Record Lane 2/3 eligibility (which strata passed, which profile) in the RESULT and stop.

## 6. Exit

- Verdicts on disk per §2, §3 (and §4 if reached).
- `daily_tokens` reverted to 55M and committed (§1).
- `seldon cc complete cc_tasks/2026-08-27_pilot_finish.md`, then RESULT `cc_tasks/2026-08-27_pilot_finish_RESULT.md` with: per-run ledger table (`python -m kg.spend status`), the ceiling arithmetic you actually used, every §0 premise marked true/false, Lane 2/3 eligibility, and the per-doc settled cost for any extraction this task ran (the corpus-mean question needs these numbers).
- Commit and push everything: shards, raw responses, verdicts, RESULT, code.
