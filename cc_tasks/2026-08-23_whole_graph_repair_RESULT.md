# RESULT — Whole-graph repair: span coverage, relocation, attribute nulling

**Task:** `cc_tasks/2026-08-23_whole_graph_repair.md` (immutable) · **Seldon task:** `803b024f`
**Executed:** 2026-08-23 ≈ 12:30 → 16:00 UTC. Max OAuth only; `ANTHROPIC_API_KEY` unset. Model: Haiku 4.5 (cleanup class) for relocation; Opus 4.8 + Sonnet 5 for the success measure.
**Sub-RESULTs:** `docs/research/2026-08-23_repair_phase1_detect.md`, `…_repair_phases2-6.md`, `…_repair_gate_report.md`. Decision record: DD-017.

## Headline
**Pre-registered success measure PASSED: strict fact-level entailment 199/216 = 0.921 [0.878, 0.950] ≥ 0.85** on 150 repaired items (deterministic 0.915 · model-assisted 0.897 · nulled 0.955; fabrication 0/216). Repair reached 1,876 spans relocated and 5,270 attributes nulled before the operator stopped the model-assisted pass for spend; 3,041 relocations remain resumable. Grounding gate 0 throughout.

## Phase status
| phase | status |
|---|---|
| 1 Detection | done — 8,858 nodes; 5,277 span-partial; 7,875 unsupported attributes; filled share 2.9× probe → flagged finding (substring rule over-detects paraphrased free text) |
| 2 Deterministic relocation | done — 1,321 (ceiling 25%) |
| 3 Model-assisted relocation | **partial, operator-stopped** — 915 of 3,956 attempted: 555 relocated, 360 unrepairable; verifier defect found on the rate run and fixed; cap-enforced via control plane; resumable |
| 4 Attribute nulling | done for settled items — 5,270 nulled, 60 resolved by relocation, 2,545 deferred pending relocation |
| 5 Enforcement flip | done — `enforce_span_coverage: true` (future runs), regression tests, 159 tests green |
| 6 Projection / gates / measure | done — overlays applied last (relocated 1,899, nulled 5,349); grounding 0; success measure PASS |
| 7 Close | done — DD-017; 5 Seldon results; committed + pushed with the TrustGraph task |

## Counts
| | |
|---|---|
| relocated, deterministic | 1,321 |
| relocated, model_assisted | 555 (of 915 attempted; 61%) |
| span_unrepairable | 360 |
| relocation pending (not attempted) | 3,041 |
| attributes nulled | 5,270 (+79 probe) — description 3,056, aliases 850, term 424, response_type 339, steward 226, year 140, owner 131, version 38, operator 36, url 26, license 4 |
| nulling deferred | 2,545 |

## Spend
35,295,862 tokens (relocation + success measure). **Cost UNKNOWN** (unpriced; envelope estimate $39.80 lower bound). ≈36K tokens per relocation call, almost all the `claude -p` harness's cached system prompt — the structural cost of using the CLI for cleanup-class calls; recorded for the follow-on (an API-keyed path is forbidden by DD-007, so the alternative is batching several items per call).
`controls.yaml` untouched (sha `611d5dda…3684`; no path in this task reads it).

## Standing decisions
1. **Verifier criterion** = verbatim substring of the document (task text), not "contains the item text" — the first 20 calls used the stricter, wrong criterion; their `span_unrepairable` events were superseded via `--redo-unrepairable` (append-only).
2. **Whitespace-insensitive verification** with the document's own slice stored: PDF text has mid-word spaces/hyphens the model silently heals; the stored span must string-match the source under the grounding validator's normalization, and does.
3. **Context window for the model call**: full normalized document when ≤ 30K chars, else a 12K-char window around the best difflib sentence match — bounds tokens; recorded on each overlay (`context`).
4. **Cap enforcement** added to Phase 3 (the task said "proceed regardless"; the operating doctrine makes the declared cap the gate) — the run stops cleanly at the cap and resumes next window. In the event the operator stopped it earlier for spend.
5. **Deferred nulling** for items whose relocation has not run (span may still change) rather than nulling then un-nulling.
6. **`term` added to the projection's nullable whitelist** after the log/projection count mismatch (424) — log and projection must agree.
7. **Parser-test isolation**: the enforcement flip broke nine pre-existing parser tests whose fixtures are pointer spans; they are isolated by fixture and the two enforcement tests exercise the live default explicitly.
8. **Operator stop honored mid-Phase 3**; the success measure ran on what was repaired (pools 1,318 / 553 / 2,839 — well above the 150 needed).

## Discrepancies vs the task
| task said | live |
|---|---|
| Phase 3 "proceed regardless" | Cap-bounded by doctrine, then operator-stopped at ≈915 calls; 3,041 pending, resumable. |
| "Rate-measure the first 20 calls" | Done twice — the first 20 exposed the verifier defect (0/20) and were redone. |
| Probe-projected rates 52% / 21% | Mechanical sweep: 40% / 60% of detections — filled > 2× → finding (paraphrase vs substring). |
| "Update the six monitors' baselines only if …" | Not updated (instrument unchanged; no before/after pair recorded). |
| Seldon "relocated counts by method, nulled, unrepairable, post-repair entailment" | 5 registered; script links show "no" (scripts not registered as artifacts in this graph). |

## Commits
`ai-readiness-kg@7c88e87` → `origin/main` (joint commit for both 2026-08-23 tasks).
