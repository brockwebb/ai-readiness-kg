# CC Task: evidence map, part 1, what the record says about the claims the summary will make

**Date:** 2026-10-02
**Project:** ai-readiness-kg
**Authored by:** Desktop session, under DN-009 (the deck is rejected; evidence map before any summary prose). This task asks the record a fixed set of questions and writes the answers as claims with evidence. It authors no summary text.
**Implements:** DN-009 decisions 2, 5 and 6.
**Framework layer served (DN-005 §5 rule 1):** §2.4, exposure (the evidence base of the summary).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 2 to 4M tokens (Opus). Query by script, not by reading tables into context.
**Network:** none beyond `git push`.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Output.** `docs/evidence/claims.yaml`, new, plus `docs/evidence/README.md` (schema, one paragraph), plus `scripts/build_evidence_map.py` that regenerates every record-derived entry from the graph and the cycle of record, byte-stable under `--check`. Schema per claim: `id` (`CL-NNN`), `text` (one sentence, the claim as it would be made), `status` (`record` | `prior_art` | `needs_measurement` | `unsupported`), `evidence` (list of `{kind: finding|result|document|indicator|query, id, locator, note}`), `source_task`. This task writes the `record` and `needs_measurement` entries; the prior-art task adds `prior_art`; nothing is `unsupported` without a search that failed.

2. **The questions, each answered by a script against the record, each producing one or more claims:**
   - **Q1, the measurement boundary (DN-009 d6).** For every indicator page H lists as not measured (32 of 48, plus the 3 unassigned), classify from page G's requirements table and the indicator's own record what blocks it: `open_tooling` (doable from outside with public tooling and no agency action), `agency_cooperation` (needs something only the publisher can provide), `funding`, `no_standard` (the test needs a reference set or standard that does not exist). One row per indicator with the classification and the record text it rests on. If any row is `open_tooling`, the RESULT lists it first; those become tasks before the summary (DN-009 d6).
   - **Q2, access denial versus absence (DN-009 d5).** Across the cycle of record `scan_2026-09-10_rj4`, count findings by body whose reason is an access denial (HTTP 401/403/429, robots.txt disallow, bot-detection challenge, TLS or connection refusal) versus an absence (no record, no field, no file) versus other. State the harness's client configuration as the record has it (user agent, authentication none, from the harness config). Produce the table and a claim per body with a denial count greater than zero.
   - **Q3, corpus growth.** From the corpus manifest and the event log: documents admitted at project start versus now, and how many were added during the framework work, with dates. One claim.
   - **Q4, the Census catalog absence.** From the cycle: which Census legs fail for the reason that data.json holds no record for the probed product; the list of product URLs probed; the data.json record count. One claim, with finding ids.
   - **Q5, the headline numbers the summary will need**, each as a claim with its Result or query: indicators total and in the framework record (49 and 48, with the candidate named); criteria kept and added (4 and 3); indicators with a current rule (24); measured, harness built, specified only (16, 8, 24); bodies on the cycle and ranked (16, 13); legs judged and findings (23, 1,009); Census judged rows failing (34 of 39); Census rank and the leg it rests on; evidence coverage (9 of 49 cells located, 27 of 147 edges, 16 indicators with no edge, 82 of 264 documents cited). Each number is computed by the script, not copied from the pack; where the script's number differs from the pack's, the RESULT says so and the claim carries the script's.
   - **Q6, the ranked prescriptions for Census.** From page G's table: the actions in the hours band with no cost, each with its bound under equal weights. One claim per action, worded as a bound, never as value or ROI (DN-009 d3).

3. **Reader gate (DN-009 d7).** Before the RESULT, spawn a subagent with no prior context, give it only `docs/evidence/claims.yaml` and `README.md`, and ask it to write, as a federal executive, five sentences on what the record establishes and one action it would take. Quote its answer in the RESULT verbatim. If it cannot produce five supported sentences, the map is not done.

**Write set:** `docs/evidence/**` (new), `scripts/build_evidence_map.py`, `tests/test_evidence_map.py` (idempotence; every `record` claim's evidence ids resolve in the graph or cycle; every number in a claim's text equals the script's computed value), the RESULT. Byte-identical: everything else, `docs/brief/` and `docs/deck/` included. No projection, no model call outside the reader gate.

**Immutable once written.**

## Gate and report
`make gate-fast`, `seldon verify`, `tests/test_evidence_map.py`. RESULT `cc_tasks/2026-10-02_evidence_map_record_RESULT.md`, under 60 lines: the Q1 table summarized by class with any `open_tooling` rows listed in full; the Q2 table; the Q3 to Q6 claims by id; numbers that differed from the pack; the reader gate's five sentences; premises wrong; measured tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** schema and script → Q1 → Q2 → Q3 to Q6 → tests → reader gate → gate → RESULT → push.
