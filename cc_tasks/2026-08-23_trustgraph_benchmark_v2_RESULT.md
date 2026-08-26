# RESULT — TrustGraph benchmark v2: custom Claude-CLI backend, model held constant

**Task:** `cc_tasks/2026-08-23_trustgraph_benchmark_v2.md` (immutable) · **Seldon:** `36a5c0e1` · supersedes the execution of `b6900da4` (DD-018 → DD-021)
**Executed:** 2026-08-25 → 2026-08-26. Max OAuth only; `ANTHROPIC_API_KEY` never set anywhere including containers. Fork: `/Users/brock/GitHub/trustgraph-fork` branch `claude-cli-backend` @ `9aef0ef0` (TG-side changes fork-only; no public fork created — upstream offer is the operator's call).
**Sub-RESULTs:** `docs/research/2026-08-23_tgbench2_{phase1_deploy, phase2_tg_side, ours_log, decision}.md`.

## Verdict — **harvest-components** (pre-registered rule; two independent failing grounds)
R = 0.33 < 0.7 and F_tg upper 0.204 > F_ours 0.079. Full table and harvested components in the decision doc. No integration task. DD-021 records the revision-mechanism outcome: the 2026-08-22 chat rejection is replaced by measurement — partially vindicated (validity machinery matters; theirs fabricates more against an easier bar), partially corrected (the "infrastructure-weight" objection died: 16.8-min deploy, 17-min backend, 34-min total implementation inside 5 h of time-boxes).

## Phase table
| phase | outcome |
|---|---|
| 1 deploy + backend | done — 19 containers, 4.4 GiB RAM, 78 s to first query; `LlmService` backend, 14/14 stub-CLI unit tests; smoke 1 call/7 s |
| 2 ontology + extract | done — ontology count-fidelity exact (12/23/33) with 31 enumerated expressiveness losses; 5/5 docs both sides; TG 6.74M tokens/168 calls, ours 0.58M/5 calls |
| 3 normalize + judge | done with a ceiling cut — R computed on all items; TG side judged 103 facts (both raters, Dawid-Skene); **our side unjudged (ceiling)** |
| 4 verdict | harvest-components |
| 5 close | Seldon ×4, containers torn down (0 running), fork left in place, committed + pushed |

## Ceiling accounting (binding 8M)
TG extraction 6,738,175 + ours 575,106 + judging 793,468 = **8,106,749 — consumed, 1.3% overshoot** (budget guard polls at 30 s; fired at 793K of its 650K line). Consequences honestly taken: our-side fact-level F unjudged on this run (probe value cited as context); TG judging n=103 of the 200-fact sample. Costs UNKNOWN (unpriced); envelope estimates are lower bounds.

## Friction findings (data, not failure)
- Two ~6 h orchestration stalls (the subagent's detached-timer pattern; the pipeline itself never stalled and burned zero tokens waiting). Fixed by forbidding detached waits; doc 5 ran fully synchronous.
- TrustGraph deploy friction ~35 min total (disk-full BookKeeper crash-loop with opaque errors; undocumented `tg_` token prefix; Loki-on-by-default log flood; Makefile-generated version files; templates/images version skew). All under the boxes; several are upstream-noteworthy (operator's call).
- Their API: triples query page-caps at 5000; named-graph filter returns `[]`; `list-children` unregistered at the gateway. Export switched to store dumps (both formats handled by the normalizer).

## Standing decisions
1. 200-fact seeded samples per side for judging (full fact sets would breach the ceiling); budget guard cut it further — recorded, CIs widened accordingly.
2. Verdict decided on R + F_tg without our-side re-judging: adopt-evaluate could not trigger regardless (R term), so no further spend was warranted at a consumed ceiling.
3. R reported against admitted-only (pre-registered base) AND admitted+quarantined (0.078) — our 2026-08-23 coverage gate shrank the admitted denominator; the verdict is unchanged on either base.
4. Their evidence chunks accepted as the span-equivalent per the task, with the chunk verbatim-vs-source rate (0.98) reported as its own metric.

## Commits
{COMMIT}
