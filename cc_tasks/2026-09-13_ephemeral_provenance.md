# CC Task — four published Results name a provenance file the repository deliberately does not hold

**Date:** 2026-09-13
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-12_publish_l0_RESULT.md` §5 and §9 item 2.
**Implements:** DN-002 decision 3 (Result states are real; a tagged Result that cannot be re-derived is a stop); under DD-001.
**Fulfils:** its own ResearchTask (`seldon cc register`). Independent of Pages; runs while the host is being enabled. Does not touch `docs/`.
**Spend:** zero model calls. **Network: none.**

**Why this task exists.** Four published Results are `COMPUTED_FROM` a DataFile whose registered path, `state/scan_matrix_2026-09-10.json`, nothing writes and nothing holds. The absence is a decision of record (the judgement of record for cycle 4 is `_rj2`; the measured cycle was never reported, and the figure suite skips on exactly that absence). The published `results_tagged.json` says so under `provenance_paths_absent`. A stranger following the chain reaches a dead path; the re-derivation script reaches the value only because it knows to run the generator into a temporary tree. That knowledge has to be in the graph, not in a script.

**Decisions taken here (operator overrides later):**
1. **The DataFile stays; it is marked ephemeral, with its derivation on the node.** The matrix was computed and the four Results were computed from it; re-pointing them at the payload would rewrite what happened. The DataFile node gains `materialized: false`, `derivable_from` (the cycle payload path the repository does hold) and a `GENERATED_BY` edge to `scan_report`, through the registry's own update path with an event. No Result is edited; edges and node properties change, values and states do not.
2. **The stranger test becomes a suite test.** For every DataFile any `published` Result is `COMPUTED_FROM`: the path exists in the repository, or the node is `materialized: false` and `scripts/rederive_tagged_results.py` can derive it from `derivable_from` in a temporary tree and reproduce the dependent values. Both branches asserted; a DataFile in neither is red.
3. **`provenance_paths_absent` becomes `provenance_paths_ephemeral`** in `results_tagged.json`, each entry carrying `derivable_from` and the generator. The site builder reads the node, never a hardcoded path. The file is rebuilt; `docs/index.html` is not otherwise touched.
4. **The re-derivation script reads the temporary-tree rule from the node** rather than carrying a special case for `scan_report`: any generator whose DataFile is `materialized: false` writes into a temporary tree. The special case is deleted and the test in decision 2 exercises the general path.

**Zero edits to:** rule modules, harness, payloads, prior Results' values and states, prior RESULTs, figures, section prose, the skeleton, the record, `corpus/`, `docs/` beyond `data/results_tagged.json`.

**Immutable once written. Glob `2026-09-13_ephemeral_provenance_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Decisions 1, 4. Stop if the registry has no update path for a DataFile node's properties without a new node; the RESULT says what it would need.
## 2. Decisions 2, 3.
## 3. Gate (the one gate of this task)
Decision 2's test green over every DataFile a published Result depends on; the four Results re-derive and reproduce through the general path; `provenance_paths_absent` empty and `provenance_paths_ephemeral` carries one entry with its derivation; every change to the DataFile on an event; no Result value or state changed (asserted by query before and after); `make gate-task`; `make gate-full` detached, logged, polled; `seldon verify`; protected paths.
**Failure writes nothing: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-13_ephemeral_provenance_RESULT.md`: the node before and after; the general-path re-derivation log; every premise wrong. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (stop on no update path) → §2 → glob addenda → §3 (detached, logged, polled) → §4 → push.
