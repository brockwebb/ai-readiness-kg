# Repair Phases 2–6 — relocation, nulling, enforcement, success measure (task 2026-08-23_whole_graph_repair)

## Phase 2 — deterministic relocation (zero spend)
1,321 of 5,277 span-partial items relocated by exact/NFKC substring (`grounding_relocated`, method `deterministic`, `events/batch-011.jsonl`). 3,956 forwarded. **Deterministic ceiling: 25%** — the remaining item texts are paraphrases of the source.

## Phase 3 — model-assisted relocation (Haiku 4.5, `cleanup_model_id`)
Rate on the first 20: mean 8–19 s/call, ≈36K tokens/call (CLI cached system prompt dominates; Haiku's own tokens are small) → projected 3,956 calls ≈ 9–10 h and ≈141M tokens, above the 55M/day declared cap; the script enforces the cap via the control plane (`tokens_left`, `record_usage`) and stops cleanly. Two shards ran from 13:50 to 14:47 UTC when the **operator stopped the run** ("burning a little hot") at ≈915 calls: **555 relocated (61%), 360 `span_unrepairable`**, ~52 transient invocation errors on one shard (retry on resume). Defect found and fixed on the rate run: the verifier wrongly required the passage to *contain* the paraphrased item text (0/20); the task criterion is verbatim-substring-of-document only, verified whitespace-insensitively (PDF artefacts) with the document's own slice stored. The 20 `span_unrepairable` events from the defective run were superseded by `--redo-unrepairable` (append-only; later `grounding_relocated` wins in projection). Remaining **3,041 items resumable**: `scripts/repair_relocate.py --phase 3 --redo-unrepairable --shard I/N`.

## Phase 4 — attribute nulling (zero spend)
5,270 `attribute_nulled` overlays (by attribute: aliases 850, description 3,056, owner 131, year 140, term 424, response_type 339, steward 226, version 38, operator 36, url 26, license 4); 60 resolved because the relocated span carries the value; **2,545 deferred** until relocation settles. Projection whitelist gained `term` (424 Definition nulls were logged but not projected until then — caught by comparing log vs projection counts; fixed, rebuilt).

## Phase 5 — enforcement flip
`dixie_evidence.yaml: extraction_gates.enforce_span_coverage: true` (future runs). Regression tests: a partial span is quarantined at extraction time under the live default; `grounding_relocated` / `span_unrepairable` / `attribute_nulled` events project (never filtered); parser tests for other gates isolated from coverage by fixture. Suite 159 passing.

## Phase 6 — projection, gates, success measure
Projection: overlays relocated 1,899 (1,321 + 555 + probe 23), nulled 5,349. Gates: **grounding 0**, drift 0; quarantine/edge_endpoint/orphan findings unchanged (0.0237 / 1,209 / 0.0877). Monitors: only `stability_per_type` fires (as before).

**Pre-registered success measure** — 150 repaired items (50 relocated-deterministic, 50 relocated-model, 50 attribute-nulled; seed 20260823; pools 1,318 / 553 / 2,839), decomposed to 216 facts (122 deterministic + 94 model-split), judged by Opus 4.8 + Sonnet 5 (batch 10, `run=repair_success`), Dawid-Skene:

| repair type | entailed / facts | precision | Wilson 95% |
|---|---|---|---|
| relocated_deterministic | 65/71 | 0.915 | [0.828, 0.961] |
| relocated_model | 70/78 | 0.897 | [0.810, 0.947] |
| attribute_nulled | 64/67 | 0.955 | [0.876, 0.985] |
| **pooled** | **199/216** | **0.921** | [0.878, 0.950] → **PASS (≥ 0.85)** |

Fabrication 0/216; residual classes filled_attribute 8, subject_dropped 6, span_truncated 3. Items faithful 135/150. Rater agreement with MAP: Opus 1.000, Sonnet 0.935. Monitor baselines not changed (the task allows it only with a before/after pair; the instrument is unchanged, so none recorded).

## Spend
35,295,862 tokens across relocation + success measure; **cost UNKNOWN** (unpriced; envelope estimate $39.80 lower bound). `controls.yaml` not touched (judge/relocation paths do not read it).
