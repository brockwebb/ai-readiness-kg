# CC Task — Overnight burn 2026-08-26 → 27: stratum re-extraction, triage-batch extraction, restoration v2, resumable repair

**Date:** 2026-08-26 (dispatch ~22:15 ET; window closes 05:00 ET 2026-08-27)
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Model spend, unattended. Operator ceiling arrives in the execute line as `CEILING=<tokens>`. Everything else in this file is automatic: every lane has a pre-registered gate; a gate FAIL stops that lane and the driver moves to the next lane. No operator contact at any point. If a genuine ambiguity blocks a lane, that lane STOPs with a logged reason and the driver continues.
**Before starting:** glob and read every `cc_tasks/2026-08-26_overnight_burn_ADDENDUM*.md`. Immutable file.
**Result:** `cc_tasks/2026-08-26_overnight_burn_RESULT.md` written by CC when it hands off to the detached driver (state: `running`, with what was verified live), and `docs/research/2026-08-27_overnight_burn_SUMMARY.md` written by the driver at exit (ledger totals per lane, gate verdicts, counts). Seldon task id on both. Discrepancies reported, never reconciled.

## Why this is safe to run unattended (the lessons, as mechanisms — each cited to the ledger)

| Failure we already paid for | Mechanism tonight | Source |
|---|---|---|
| 22.0M spent against a 12M ceiling; 8.11M against 8M | `kg/spend.py` reserve-then-settle guard at the stub, shared ledger, `--ceiling-tokens` required | DD-022, d2756bd1 |
| 36K–111K/call overhead on single-item cleanup calls | batch 25–50 per call, one headless session per document, batches as `--resume` turns; cache-read ratio checked on first 3 calls, STOP the lane if reads aren't dominant | DD-019 §1–4 |
| Cheap model returns related-but-not-entailing passages; restoration class reversed at 0.78 | two-stage per attribute: propose → independent entailment check gates *each* event; class-level acceptance sample; **gate before wire** — nothing projects until the class passes | DD-017, a2d3fb42 RESULT |
| Instrument `method` fabricated from world knowledge (F 0.25/0.17); semantic edges from headings (F 0.26) | corrected prompt: per-attribute spans on Instrument, null unless covered, cited-only instruments are `mentions` Concepts; semantic edge span must contain both endpoints + predicate | 2026-08-22_probe_decision.md §reextract_required |
| Bulk before the pilot proved the prompt | 3-doc pilot judged by the fact protocol before any stratum burn; threshold pre-registered below | DD-013, DD-015, schema §5 pilot gate |
| Array parse loss, id-echo mismatch, malformed-row kill | 2% planted decoys per batch, rolling acceptance window; batch split-and-retry once; salvage valid rows | DD-019 §6 |
| Garbage discovered only after the burn | **running positive control**: after the first 8 documents of any extraction lane, decompose + judge a 60-fact sample from that lane's fresh output; F_upper > 0.10 → STOP the lane | DD-015 decision rule, applied mid-run |
| Span locates but doesn't cover; paraphrase admitted as quote | `extraction_gates.enforce_span_coverage: true` already on; parser quarantines `span_partial`; grounding gate absolute zero | DD-017 |
| Model narrates around JSON with repo cwd | hermetic `claude -p` from empty temp cwd (unchanged) | CLAUDE.md |
| Rate-limit / session-cap errors mistaken for failures | CLI rate-limit or overload error → release reservation, sleep 10 min, retry; after 6 consecutive, STOP the lane with `rate_limited`, not `failed` | new tonight |
| Uncommitted shards after a burn | driver commits + pushes at the end of every lane and at exit | CLAUDE.md §commit rule |

## Ceilings (all declared on the ledger via `declare`)

- `controls.yaml spend.daily_tokens` ← `CEILING` for tonight if `CEILING` > current 55M (logged as an operator-declared band change; restore is a follow-on decision, not automatic).
- Lane run ids and ceilings: `pilot_instr_sem` **3M**; every other lane declares `CEILING` (the daily cap is the real global; operator's instruction is to run to the limit).
- `MAX_CONCURRENT_MODEL_CALLS = 2` stands. Lanes that can share it do (fleet 2 workers, one shared run id).

## Lane 0 — Corrected extraction prompt + Instrument per-attribute spans (zero spend, first)

1. Bump `kg/extraction/prompt_template.md` to a new version implementing the two requirement blocks in `docs/research/2026-08-22_probe_decision.md` verbatim as rules (Instrument: `method`/`owner`/`year` null unless a covering span exists; per-attribute `grounding_spans` map on Instrument; cited-only instrument → Concept with `mentions`; semantic edges: span must contain both endpoint names/referents and the predicate; heading/list inference → `proposed_relationships`). Explicitly forbid completion from background knowledge, in the prompt.
2. Schema **v0.3.4** append-only: per-attribute span map on Instrument (`grounding_spans: {attr: span}`), parser validates each against the document with `grounding.covers`; missing span ⇒ attribute nulled at parse (not quarantine of the node). Extend the append-only test and `docs/schema_v0.1.md`.
3. Pin the new template sha in `scripts/run_profiles.yaml` as profile `reextract_v034`; the old profiles stay untouched.
4. Unit tests: parser nulls an Instrument `method` lacking a span; semantic edge without both endpoints in its span routes to `proposed_relationships`.

## Lane 1 — Pilot: 3 documents, Instrument + semantic-edge strata (ceiling 3M) — the gate for Lanes 2 and 3

- Pick 3 docs with the highest Instrument-item count across both epochs (from the projection; report ids). Re-extract under `reextract_v034` into a tagged shard `events/batch-013_reextract_v034.jsonl` (`purpose: reextract`; superseding events for the two strata only — other strata's items from these docs are NOT replaced).
- Judge: decompose Instrument items + semantic edges from the 3 docs via the probe protocol (`decompose_template`, `probe_judge_template`, two raters, batch 10, Dawid-Skene). **Pre-registered pass: F_upper < 0.10 for each of the two strata AND item-level faithful ≥ 0.70.** (Not 0.05: the probe decision rule's repair-only branch needed <0.05; the question tonight is whether the corrected prompt moved the strata out of `reextract_required` territory, i.e., below the F_lower > 0.10 trigger with margin.)
- PASS → Lanes 2 and 3 proceed. FAIL → both stratum lanes STOP; the driver skips to Lane 4 (which doesn't depend on the prompt) and the SUMMARY names the failing stratum and the top-3 fabrication patterns from the judge output. A FAIL is a finding for the morning, not a prompt tweak tonight.

## Lane 2 — Stratum re-extraction, both epochs (after Lane 1 PASS)

- Worklist: every manifested document that has ≥1 Instrument item or ≥1 semantic edge (`has_component`/`subtype_of`/`consumes`/`extends`/`implements`) in either epoch, minus the 3 pilot docs. Size-descending order (`BURN_ORDER=size_desc`), fleet 2, shared run id `reextract_v034_bulk`, ceiling `CEILING`.
- Only the two strata are superseded (`extraction_superseded` scoped by stratum — if the event type can't scope by stratum, add `superseded_strata: [...]` to the event and make the projection honor it; report).
- Running positive control after doc 8 (60-fact sample, both strata): F_upper > 0.10 → STOP lane.
- Quarantine gate: `BURN_QUARANTINE_STOP_MODE=systemic` with the pre-registered `quarantine_rate` ceiling from `dixie_evidence.yaml` — FAIL stops the lane.

## Lane 3 — Triage-batch extraction, 34 new documents (after Lane 1 PASS; runs concurrently with Lane 2 under the same fleet if the ledger has room, else after)

- Worklist: manifest epoch `triage-2026-08-24` (34 docs), full extraction under `reextract_v034` (the corrected prompt is the current prompt; there is no reason to extract new docs under a prompt known to fabricate). Run id `triage_extract`, ceiling `CEILING`.
- DD-011 stated-extent rule for anything > `MAX_DOC_CHARS`: skip to `refetch_candidates.jsonl` with `oversize_needs_clearance`; no truncation.
- Phase 0 retag before extraction: the DOC RFI notice and the regulations.gov comments index are tagged `construct_arm: org_maturity` by 7456614d's R3 placement; their subject is AI-ready open government data assets → `publication_actionability`. Emit superseding `document_annotation` events with rationale citing this task; report the two doc ids.
- Running positive control after doc 8, all strata pooled: F_upper > 0.10 → STOP lane.
- Grading-confusion monitor (DD-010/DD-014): fraction of `platform_official` Claims from non-operator docs reported in SUMMARY.

## Lane 4 — Restoration v2 + relocation re-judge + finish resumable repair (cleanup class, Haiku, independent of Lane 1)

- **Scope:** the 2,545 deferred `attribute_nulled` overlays and the reversed restoration class; the ~3,428 resumable relocation tasks; the recommended re-judge of `model_assisted_batch` relocations from a2d3fb42. Exclude the two `reextract_required` strata entirely (Lane 2 replaces them; repairing them is wasted spend).
- **Two-stage per attribute (the fix for the 0.78):** stage 1 (Haiku, batch 40, session-per-document `--resume`): propose a verbatim passage for the attribute. Stage 2 (Sonnet 5, batch 10 — the probe's second rater, DD-015): entailment judgment "does this passage entail this attribute value" per proposal, blind to stage 1's reasoning. Only `entailed` proposals become `attribute_restored` events; everything else stays null with the proposal logged as `restoration_rejected`.
- **Gate before wire:** restorations accumulate in `events/batch-014_restoration_v2.jsonl` unprojected. Class acceptance: random 100 accepted restorations, decomposed and judged by the full probe protocol (two raters, D-S); **≥ 0.90 fact-level entailment** (the same threshold that reversed v1). PASS → projection enabled for the class (one `restoration_class_accepted` event). FAIL → class stays unprojected; SUMMARY reports.
- **Relocation resume:** `scripts/batch_repair.py --shard I/2 --redo-unrepairable` under run id `repair_resume`, ceiling `CEILING`, decoys on, cache check on. The re-judge of prior `model_assisted_batch` relocations rides the same success-measure sample (50 items) and is reported as its own number.
- Cache-read ratio and decoy acceptance window are STOP conditions for this lane exactly as DD-019 specifies.

## Lane 5 — NOT tonight

Concept dedup stays blocked (needs Lanes 2 and 4 settled and its own prior-art design: deterministic pre-dedup → LLM-proposed merges with confidence → adjudication events). Extraction-time ontology validation port (TrustGraph harvest) is deferred: parser quarantine already prevents bad writes; the port is an efficiency gain, not a lessons-learned gap, and it is not worth a burn-night regression risk.

## Driver

`scripts/overnight_burn_2026-08-26.sh` + `scripts/overnight_burn.py`: lanes in the order 0 → 1 → (2 ∥ 3) → 4; launched detached (`nohup`/launchd wrapper pattern from `scripts/jobs/airkg_extraction_burn.sh`) so it outlives the CC session; per-lane status in `state/overnight_burn_status.json`; STOP file honored at any point; hard wall-clock stop at **04:45 ET** (finish in-flight batches, release outstanding reservations, reconcile, commit, push, write SUMMARY). CC's job ends when: Lane 0 tests are green, the driver is running detached, Lane 1 has completed and its verdict is on disk (so the RESULT can state whether the stratum lanes are go/no-go), and the RESULT is written. Do not wait for Lanes 2–4; the SUMMARY covers them.

## Deliverables

- [ ] Lane 0 code + tests + schema v0.3.4 + profile pin
- [ ] driver scripts; status file; wall-clock stop; rate-limit backoff; per-lane commit
- [ ] Lane 1 verdict on disk (`docs/research/2026-08-26_pilot_reextract_v034_verdict.md`)
- [ ] RESULT (state `running`) + `seldon cc complete`
- [ ] SUMMARY at driver exit with ledger totals per lane via `python -m kg.spend status`, reconcile exit codes, gate verdicts, counts written/quarantined/nulled/restored/relocated
