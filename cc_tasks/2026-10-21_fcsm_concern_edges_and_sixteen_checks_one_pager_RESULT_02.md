# RESULT_02: `cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md` (task 9af5f624) — resume to completion

**Date:** 2026-11-02
**Session:** dispatcher-launched headless Claude Code session, worktree `.claude/worktrees/wobbly-wiggling-canyon` (branch `worktree-wobbly-wiggling-canyon`), served model `claude-opus-4-8`.
**Outcome:** COMPLETE. Parts A, B and C carried out per ADDENDUM_02 (resume from the orphaned worktree). Gate green (EXIT=0), protected-paths clean (EXIT=0), `seldon verify` EXIT=1 on two pre-existing warnings unrelated to this task (§Gate). Committed on this branch; `seldon dispatch part-complete` run from here. The dispatcher rebases/merges and completes the task.

This file is the completion record. The earlier `..._RESULT.md` is the record of the first (hand-dispatched, 2026-10-22) session that STOPPED at Step 0 item 2 as `model_substituted` (served `claude-opus-5-5`); it is preserved, not overwritten (§14 "new files get new names").

## Step 0

1. **Model (base item 2).** `seldon models resolve author` = `claude-opus-4-8`; this session's served model = `claude-opus-4-8` (environment). Match — no `model_substituted`. The dispatcher launched the lock's id, as DN-006 decision 10 requires.
2. **Predecessors (base item 3).** `seldon task show`: b6c65bfe `completed`, b694c14a `completed`.
3. **The sixteen specs.** Cypher over the projection: exactly 16 MeasurementSpecs carry `instrument_state`, codes {A1,A2,A3,A4,A5,A6,A8,A9,A10,A11,A12,A13,B3,D1,D4,F4}. No seventeenth, none missing. Four are `specified` (A1, A3, A5, D4) — the Scored checks.
4. **DN-018 read in full.** §3 (Mapping A, four concerns, all `RMF equivalent = none`) and §4 (sixteen checks → primary/also concern) are the data for Parts A and B; nothing is paraphrased.
5. **Projection gate (base item 3, replaced by ADDENDUM_02 3a).** Was red for the reason ADDENDUM_02 names: the shared Neo4j held the orphaned 4 concerns + 23 edges while main's record had neither, so `test_node_and_edge_counts_match_the_json_exactly@neo4j` failed. This task is the fix, so a green gate was not a precondition.

## Dispatcher (ADDENDUM_01 items 1–5)

Done on 2026-10-21 by the earlier session (commits c1091b58, f74c3bb7, 2e6edb18) per the first `..._RESULT.md` §2; not repeated. Item 5's claim is re-made by this dispatcher launch. `dispatch.enabled` is true; this session did not change it.

## ADDENDUM_02: resume from the orphaned worktree

**3a. Orphaned worktree.** `.claude/worktrees/gleaming-munching-kahan`, branch `worktree-gleaming-munching-kahan`, head `a327c8c9`. It carries Part A's authored files (`scripts/apply_fcsm_concerns.py`, `tests/test_fcsm_concerns.py`, the `load_framework_graph.py`/roundtrip-test edits) and Part B's mid-edit `scripts/sixteen_checks_build.py` — all **uncommitted** in that worktree (the squiddy commits on its branch are unrelated noise, DN-018 commits were never made). So "cherry-pick/merge" was not literally possible; the faithful equivalent was to bring the authored files over verbatim and run the deterministic Part A script once on this branch. Premise of ADDENDUM_02 3a corrected: "the commits that add apply_fcsm_concerns.py" do not exist — the work was never committed.

**3b. Part A brought to this branch (done once, not re-authored).** `apply_fcsm_concerns.py`, `test_fcsm_concerns.py`, the `load_framework_graph.py` FcsmConcern/SERVES_FCSM_CONCERN branch, and the roundtrip-test edits were copied verbatim from the orphaned worktree (diffs confirmed to be FcsmConcern-only additions). `apply_fcsm_concerns.py` ran once (`written: true`, event `8f1c4f7dc8744072ad89e78260e0170e`, framework_sha256 `f7eddfa62ed2…`), then `load_framework_graph.py`, then the roundtrip test. Roundtrip **green on this branch: 10 passed, 0 skipped, 0 xfailed, 0 deselected** (incl. `test_node_and_edge_counts_match_the_json_exactly` and `test_every_serves_fcsm_concern_edge_reached_the_graph_with_its_role`). Commit 6c1de654.

**3c. Record delta matches ADDENDUM-free DN-018 §4.** 4 concern nodes, 16 `primary` edges, 7 `also` edges (23 total). Confirmed on the write-back event and the projection (Part A checks below).

## Part A — the four checks

1. **Event delta.** `framework_writeback` event `8f1c4f7d…` on `events/batch-033_framework.jsonl` carries `delta_summary`: nodes_added {FcsmConcern: 4}, edges_added {SERVES_FCSM_CONCERN: 23}, nodes_removed {}, edges_removed {}, counts_keys_dropped [], counts_moved {fcsm_concern_nodes: null→4, serves_fcsm_concern_edges: null→23}. **4 nodes, 23 edges, 2 counts keys added, 0 removed.**
2. **Cypher over the projection.** `MATCH (m:MeasurementSpec)-[r:SERVES_FCSM_CONCERN {role:'primary'}]->()` with `m.instrument_state IS NOT NULL`: **16 specs, each exactly one primary edge** (min=max=1). `role:'also'`: **7 specs, 7 also edges.**
3. **`build_framework_graph.py` no-op.** `--dry-run` over the committed record: `written=False, unchanged=True`, empty delta — byte-for-byte no-op; the record was written only through the single writer.
4. **Roundtrip test.** `tests/test_framework_projection_roundtrip.py`: **10 passed, 0 skipped, 0 xfailed, 0 deselected.**

## Part B — the six checks

Build converged at **body 7.0pt, where→first clause, passes→first clause** (fit ladder; see "premises" for why 9.5pt could not fit). `scripts/sixteen_checks_build.py` wrote `reports/diagnostic/one_pager/{Readiness_Diagnostic_16_Checks.md,.docx,.pdf}` + `build_report.json`. All checks from `build_report.json` (failures: []):

1. **Page count.** `.docx` pages = 1, `.pdf` pages = 1.
2. **Font/colour/vocabulary/dash/digit checks.** `font_colour_audit.docx` [], `vocabulary.{markdown,docx}` [], `dashes.{markdown,docx}` [], `digit_audit` []. (Em/en dashes in the `rf_where_we_look` source are normalised to the house comma in the rendered cell only; the record's `rf_*` text is not edited — out of scope.)
3. **Explicit grep of the `.md`.** banned words {scan,probe,crawl,audit,ports,unmeasurable}: 0 lines; U+2014: 0; U+2013: 0; "508": 0 (`grep … ; rc=1` for each).
4. **Scored rows = the four `specified` specs.** `scored_legs` = [A1, A3, A5, D4].
5. **Quality concern column vs projection.** The `.md` concern column (primary short label) read back and mapped to codes equals the projection's `role:'primary'` edge for all 16 rows: **ALL 16 MATCH**.
6. **Build report pairs md sha256 with the PDF.** `products[].md_sha256 = b5ac4344fa15…` beside `Readiness_Diagnostic_16_Checks.pdf` (and `.docx`, `.md`).

**Row order (base task's "order above" was overridden by the brief's order, as the task directs).** The `#` column numbers the brief's order (criterion-grouped, scored-first): A1, A3, A5, A2, A4, A6, A8, A9, A10, A11, A12, A13, B3, D4, D1, F4. This differs from the task's A1,A2,A3,… order; the brief's order wins (`RB.check_rows`).

**Build-product registration.** As `reports/diagnostic/brief/` was (b694c14a): the three files are committed under `reports/diagnostic/one_pager/` with a `build_report.json` recording `generated_by` and per-product sha256. The brief did **not** create per-file Seldon Artifact nodes (`seldon artifact list` holds none for the brief); "the one-pager is a graph artifact" overstates the brief precedent, so this follows the brief's actual practice.

## Premises this task file got wrong

1. **Base Step 0 item 3 is unsatisfiable by a task that writes the record.** It required `projection_gate: green` before any write, but the gate was red precisely because the record/projection had diverged, and this task is the repair. ADDENDUM_02 already replaced it. **Backlog fix (one line):** the per-task projection-gate precondition should be checked after Part A's projection, not before it.
2. **ADDENDUM_02 3a: Part A's commits do not exist.** The orphaned session never committed; its work was uncommitted in the working tree, so the files were brought over and the deterministic script re-run, not cherry-picked.
3. **Part B fit premise (9.5pt).** The task expected 10pt (9.5pt on overflow, then "What we look at"→first clause) to fit one landscape page. It does not: four long prose columns (the uncut `rf_why_short` among them, 2,202 chars total) overflow at every size above ~7pt. The fit ladder (where→first clause, passes→first clause, font stepped down) converges at 7.0pt body, recorded in `build_report.json` and above.
4. **The record write-back cascades to the record's consumers.** Neither the base task nor ADDENDUM_02 named them. Adding FcsmConcern to the record drifted `mcp/airkg_tools.py::FRAMEWORK_LABELS` (projection gate read the concerns as MISSING → stale), `tests/test_framework_single_writer.py` (preserved-not-authored Counters), `docs/design/mcp_over_the_graph.md` (the MCP doc page), `docs/data/*` (the L0 published copy), `docs/evidence/claims.yaml` and the 61 `docs/brief/*` pages. All regenerated/updated here (commits 23e77470, 9c521393). The orphaned session died before reaching this cascade.
5. **`render_pdf` in the orphaned draft was broken.** pandoc's typst template overrides a `header-includes` `#set text(size:…)`, so the PDF never shrank; and the pipe table is wrapped in an unbreakable `#figure`, so it bumped whole off the first page. Fixed: size via the `fontsize` variable, `#show figure: set block(breakable: true)`, reduced table inset, proportional column widths in the markdown delimiter row (root-caused 2026-11-02).

## Worktree environment note (not committed)

A fresh CLI worktree does not carry the gitignored data stores, so 17 of the first gate run's 23 failures were "file not on disk", not defects. Linked read-only from `$SELDON_PRIMARY_CHECKOUT` for the gate to run: `corpus/{bulk,bulk_md,cisco,crosswalk,g1eval,kernel,pilot,round2,triage}`, `corpus/staging/{dcat_*,inbox,instrument_standards,metrics,proposed_relationships,proposed_schema,standards_2026-10-11,refetch_candidates.jsonl}`, `state/{docling_md,biblio_cache,convert_errors,substrate_md,logs,corpus_index.db,candidate_oa.json}`. `state/evidence_staging` was deliberately **not** linked (a symlinked staging root makes `git check-ignore` return "beyond a symbolic link", failing `test_scan_run_2.py`). All symlinks are removed before `seldon dispatch part-complete` so the tree the dispatcher sees is clean.

## Gate

Write set touches the framework record → gate is `make gate-task` (detached, logged, polled).

- **`make gate-task`** (`logs/gate_task_final.log`): fast tier **3443 passed, 8 skipped, 41 xfailed, 0 failed, 0 deselected** in 240.80s (4:00); re-derivation tier **25 passed** in 8.53s. **EXIT=0.**
- **`seldon verify`** (`logs/seldon_verify.log`): **EXIT=1 on two pre-existing warnings, neither introduced by this task** — (a) `98ed1dd1` (executive summary v4, explicitly out of scope, blocked on Fable quota) is blocked with no reason recorded; (b) `829a5010` (`cc_tasks/2026-11-02_v3_measurement_sheet.md`, another Desktop session's proposed task) names a source file not on disk. Both are other tasks' graph state; fixing them would be scope creep. Every check that concerns this task's write set passes (File hashes ✓, Stale artifacts ✓, Precedence 74 edges acyclic ✓, Relationship types ✓).
- **Protected paths** (`logs/protected_paths.log`): `build_framework_graph.py --dry-run` no-op (`unchanged=True`); `framework/ai_readiness_framework.json` delta vs merge-base 4c47be99 = +4 FcsmConcern nodes, +23 SERVES_FCSM_CONCERN edges, 0 removed, 0 existing-node property changes; `test_framework_single_writer.py` 20 passed. **EXIT=0.**

## Commits on this branch (4c47be99..HEAD)

- `6c1de654` feat: DN-018 Part A — concern layer in the record (+ loader/roundtrip wiring).
- `783beb5d` feat: DN-018 Part B — sixteen-check one-pager build product.
- `23e77470` fix: concern layer visible to the gate and the MCP view (FRAMEWORK_LABELS, single-writer test, MCP doc page, L0 published copy).
- `9c521393` chore: regenerate record-derived artifacts (claims.yaml, 61 brief pages). **Rebase note on this commit:** claims.yaml and the brief-pack headers pin the record's last-touching commit SHA; if the dispatcher rebases this branch (changing that SHA) rather than preserving the Part A commit, re-run `scripts/build_evidence_map.py` and `scripts/build_brief_pack.py` after the rebase.

## Session usage against the 0.9M estimate

The task estimated 0.9M tokens (author role, this session included). This headless session cannot read its own live token meter; the actual is in the session transcript. Qualitatively the work ran well over a single-pass estimate because the record write-back's consumer cascade and the Part B fit engineering were unplanned (premises 3–5). No second model role was used; no paid model call beyond this authoring session (Parts A and B are zero-spend deterministic scripts).

## Logs

`logs/gate_task_final.log` (gate), `logs/seldon_verify.log` (verify), `logs/protected_paths.log` (protected paths), `logs/sixteen_build.log` (Part B build), `logs/load_framework.log`/`reproject*.log` (projection), `logs/roundtrip.log` (Part A roundtrip). `logs/` is gitignored; these are local artifacts this RESULT quotes.
