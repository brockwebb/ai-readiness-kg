# CC Task: finish the definition conflict pass, project its edges, and retrieve the citations it recalled

**Date:** 2026-10-04
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-10-04_definition_conflict_pass_RESULT.md` (task `7ae11b56`). That run judged 130 of 158 pairs and stopped at its 5M ceiling (a per-call cost of 36,795 tokens, mostly the `claude -p` system prompt, against an estimate that assumed 6M for 162 calls); it wrote 5 `conflicts_with` edges to a held shard because `build_projection.resolve_endpoint` scopes both endpoints of an edge to the asserting document and cannot place a cross-document edge; and its method citations are recalled, not retrieved, because the base task's `**Network:** none` line was read as forbidding harness web calls. This task closes the three.
**Implements:** DN-009 decisions 2 and 8.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** `2026-10-04_views_regenerate.md`
**Spend:** est. 3M tokens (Opus) for the session, plus a declared judge ceiling of 1,200,000 for the 28 pairs (the RESULT's own arithmetic: 28 × 36,795 ≈ 1.03M, with headroom).
**Network:** none beyond `git push` from the shell. WebSearch and WebFetch harness tool calls ARE permitted, for decision 4 only; they are not shell egress and need no allowlist entry. Nothing else contacts the network.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **The 28 pairs.** `scripts/run_definition_pairs.py --run --run-id definition_pairs_2026-10-04b` with the ceiling above and the same `criteria_version` (`60256b3a937929b5`). Judged pairs skip. First re-run the 11 controls under the new run id and confirm the declared criterion still passes (positive: none `consistent`; negative: all `consistent`) before any of the 28 is judged. Then the table in `definition_pairs.md` is regenerated over 158 of 158.

2. **Cross-document edges, through the projection, no model call.** Teach `resolve_endpoint` to accept a fully qualified key (`<doc_id>::<local id>`) carried on `from_key` / `to_key` when, and only when, its prefix is a manifested `doc_id`; an unqualified id keeps today's scoping to the asserting document; a qualified key whose prefix is not in the manifest is refused with a logged reason, never a phantom node. Three controls, each a fixture that fails exactly one case. Then replay `events/batch-044_xdoc_conflict_held.jsonl` plus any new `conflict` rows from decision 1: every edge lands between two existing Definition nodes with `kind`, `source: cross_document_pass`, both spans and `adjudicated: false` on the edge. `projection_gate` must read `green` afterwards; `get_overview` and `seldon verify` are the check. If the shard cannot be replayed without a second schema change, stop and report what it would need.

3. **The unprojected OECD edge.** `batch-004:11185` is a `conflicts_with` event not in the projection, cause uninvestigated. Find the cause. Fix it in this task only if it is the decision 2 defect; otherwise record it as a finding with the event's full text.

4. **Retrieve what was recalled.** For each method citation the RESULT and `docs/research/2026-10-02_commerce_guidance_two_pipelines.md` label "recalled": Podsakoff, MacKenzie and Podsakoff 2016; MacKenzie, Podsakoff and Podsakoff 2011; Walker and Avant; Euzenat and Shvaiko; SemEval-2013 Task 9; SemEval-2020 Task 6 (DEFT); Manheim and Garrabrant 2018; Campbell 1979. Search, fetch the page that carries the citation, record author, year, title, venue, URL and one establishing sentence under 15 words, and add each to `docs/evidence/sources.bib`. Replace every "recalled, not retrieved" label with the locator. One that cannot be found stays labelled and its failed searches are listed.

5. **Not done here.** No adjudication of any pair. The 3 `quote_not_in_spans` rows and the 0.60-confidence gloss stay flagged. No change to any Definition node.

6. **Reader gate (DN-009 d7).** A fresh subagent given only the regenerated `definition_pairs.md` writes five sentences on where the definitions conflict, where they merely differ, and the one disagreement to settle first; the RESULT quotes them and states in one line what changed from the 130-pair reading.

**Write set:** `docs/evidence/definition_pairs.{csv,md}`, `docs/evidence/sources.bib`, `docs/research/2026-10-02_commerce_guidance_two_pipelines.md` (citation labels only), `kg/build_projection.py` (`resolve_endpoint` and its callers), `tests/test_definition_pairs.py`, `tests/test_build_projection.py` (the three controls), `events/raw/definition_pairs/`, `state/spend_ledger.jsonl`, the RESULT. Byte-identical: `kg/schema.yaml`, `docs/brief/`, `docs/deck/`, `docs/catalog/`, `framework/`, `corpus/`, and the FSS repository.

**Immutable once written.**

## Gate and report
`make gate-fast`, the full suite (0 failed, since the views task precedes this one), `seldon verify`, the protected-paths diff, the three projection controls. RESULT `cc_tasks/2026-10-04_definition_pairs_completion_RESULT.md`, under 60 lines: the controls re-run; counts by outcome and kind over 158; edges projected and the gate colour; the OECD edge's cause; citations retrieved versus still recalled; the reader gate's five sentences; premises wrong; judge tokens against the ceiling, session tokens and models. `seldon cc complete`, commit, push.

**SEQUENCING:** controls → 28 pairs → `resolve_endpoint` and its controls → replay → OECD edge → citations → regenerate → reader gate → gate → RESULT → push.
