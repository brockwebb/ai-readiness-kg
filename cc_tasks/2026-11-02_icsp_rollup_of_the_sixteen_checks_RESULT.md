# RESULT: the ICSP roll-up of the sixteen checks

**Task:** `cc_tasks/2026-11-02_icsp_rollup_of_the_sixteen_checks.md`
**Date executed:** 2026-11-02
**Outcome:** COMPLETE. Parts A, B and C carried out. Gate-task green (EXIT=0); protected-paths
clean (EXIT=0); `seldon verify` EXIT=1 on one pre-existing warning unrelated to this task.
Committed on this branch (three commits, see §Commits); `seldon dispatch part-complete` run from
here. The dispatcher rebases/merges and completes the task.

**Recall used:** `blank:2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager`. Its
`RESULT_02` documented the record-write-back cascade (a record edit drifts
`mcp/airkg_tools.py::FRAMEWORK_LABELS`, `docs/data/*`, `docs/evidence/claims.yaml` and the
`docs/brief/*` pages, all of which must be regenerated) and the build-product registration
convention (commit the files with a `build_report.json`, no Seldon Artifact nodes). Both shaped
Part A's projection work and Part C directly. The other recall hits (scoring model, adopter path,
USAFacts note) were read for context and did not change the approach.

---

## Step 0

1. **9af5f624 `completed` and projection gate green.** `run_cypher` over the one-pager's
   ResearchTask: `{labels: [Artifact, ResearchTask], state: "completed", title: "fcsm concern
   edges and sixteen checks one pager"}`. `get_overview().projection_gate.status` = `"green"`
   (nodes_compared 236 at Step 0; 243 after Part A).
2. **Served model = `seldon models resolve author`.** `seldon models resolve author` →
   `claude-opus-4-8`; this Claude Code session runs Opus 4.8. Match; no `model_substituted` stop.
3. **Read the Implements documents.** Read in depth: the operationalization brief
   (`docs/crosswalk/usafacts_operationalization_brief.md`, the "Shape of the instrument" bullets
   that are the extension-group text), the delta table (`docs/brief/B_usafacts_delta.md`, which
   records A–D kept and E/F/G added — F = "release engineering … added"), the skeleton
   (letter→group map), and the USAFacts guide docling copy (criterion statements). DN-016
   (vocabulary; two kinds of user) and DN-018 (FCSM concern edges) are applied through the
   imported one-pager code (`sixteen_checks_build`); DN-014's three tiers appear in the brief.

---

## Part A: the lineage in the record

Authored through the single writer by `scripts/add_aiready_lineage.py` (new, patterned on
`apply_fcsm_concerns.py`). The guide's docling copy and the brief are gitignored, so the verbatim
text is embedded in the script as literals with provenance, the same way `apply_fcsm_concerns`
embeds DN-018's constants. `framework_writeback` event `5ec3407ebc8b4949aa90d2d0554a982e`.

**Check 1 — nodes, edges, roundtrip.**
- **7 nodes added, 16 edges added, 0 removed, 0 changed.** Event delta: `nodes_added
  {AiReadyCriterion: 4, ExtensionGroup: 3}`, `edges_added {DESCENDS_FROM: 16}`, `nodes_removed
  {}`, `edges_removed {}`, `nodes_changed 0`; counts gained `aiready_criterion_nodes: 4`,
  `extension_group_nodes: 3`, `descends_from_edges: 16`.
- **Roundtrip `tests/test_framework_projection_roundtrip.py`: 10 passed, 0 skipped, 0 xfailed, 0
  deselected** (`logs/roundtrip.log`, after `scripts/load_framework_graph.py` projected 243 nodes
  / 501 edges, `logs/load_framework.log`). Also green inside the full gate (part of the 3432).
- `scripts/load_framework_graph.py` gained the two labels (`AiReadyCriterion`, `ExtensionGroup`)
  and the edge type (`DESCENDS_FROM`); `build_framework_graph.py --dry-run` remains a byte-for-byte
  no-op (`written=False unchanged=True`, empty delta).

**Check 2 — the per-criterion Cypher split.** From the record's DESCENDS_FROM edges:
**Accessible 12, Understandable 1, Accurate 0, Open 2, Release engineering 1 = 16.**
**Premise error:** the task's Part A check states "13 Accessible". The sixteen instrument legs
carry **twelve** Accessible checks (A1, A2, A3, A4, A5, A6, A8, A9, A10, A11-declared, A12, A13 —
there is no A7 among them); 13 Accessible would total 17, which contradicts "the sixteen specs"
everywhere else in the task. Reported, not retuned.

**Docling line ranges for each criterion `text`** (verbatim from
`state/docling_md/usafacts-ai-ready-data-guide.md`, the numbered statement heading under each
criterion name; all four have a one-sentence statement, so none fell back to a body sentence):
- **Accessible** — lines 37 (name `## ACCESSIBLE`), 39 (statement): "Data Must Be Machine-Readable
  and Easy to Access".
- **Understandable** — lines 54, 56: "Data Must Be Machine Understandable with Easily Retrievable,
  WellStructured Documentation and Metadata". *(The "WellStructured" with no space is a verbatim
  docling OCR artifact in the corpus copy; transcribed as-is per "text verbatim".)*
- **Accurate** — lines 72, 74: "Agencies Should Provide Clear Evaluation Benchmarks and Make Them
  Public".
- **Open** — lines 87, 89: "Data Must Be Unencumbered and Open to All Citizens".

Extension-group `text` is the construct-list sentence of each bullet in the brief's "Shape of the
instrument" (brief lines 37 E, 38 F, 39 G), verbatim, with the bold label, the `(n)` count and the
`*Exemplar*` sentence excluded (the first is not a sentence, the second a bare number, the third
names check codes the rendered page forbids).

---

## Part B: the roll-up as a build product

`scripts/readiness_rollup_build.py` (new; imports the checks from `sixteen_checks_build`), writing
`reports/diagnostic/rollup/Readiness_Diagnostic_Rollup.{md,docx,pdf}` and `build_report.json`.
Portrait, Calibri, 11pt body, PDF rendered from the Markdown. **Two pages** (the task permits two;
the Accessible row lists twelve check names). `build_report.json` `failures: []`.

The six checks, all from `reports/diagnostic/rollup/build_report.json`:
1. **Page counts.** docx **2 pages**, pdf **2 pages**.
2. **Font / colour / vocabulary / digit / dash audits on all three files.** `vocabulary
   {markdown: [], docx: [], pdf: []}`; `dashes {markdown: [], docx: [], pdf: []}`;
   `font_colour_audit {docx: []}`; `digit_audit []`. All clean.
3. **Markdown greps.** check-code pattern `\b[A-G][0-9]{1,2}\b`: `markdown_check_codes []`;
   U+2014/U+2013: `markdown_dashes []`; "508": `markdown_mentions_508 false`. Zero lines each.
4. **Bucket counts == Part A split.** Rendered `{Accessible: 12, Understandable: 1, Accurate: 0,
   Open: 2, Release engineering: 1}` == edge split `{Accessible: 12, Understandable: 1, Open: 2,
   Release engineering: 1}` (Accurate carries no edge and renders zero). `bucket_counts_match_part_a:
   true`.
5. **Agencies-passing, recomputed independently.** Rendered (from the record's DESCENDS_FROM
   grouping, four-state rule over the cycle of record): A=2, B=2, C=null(EVAL note), D=0, F=0.
   Second path (grouping the grid's legs by code letter, a full per-agency state matrix built
   independently): `{A: 2, B: 2, C: null, D: 0, F: 0}`. `agencies_passing_match: true`.
6. **Scored marks == the four `instrument_state == specified` specs.** `scored_rendered
   ["A1","A3","A5","D4"]` == `scored_record ["A1","A3","A5","D4"]`; `scored_match_four_specified:
   true`.

Accurate's "Agencies passing" cell reads **"no check yet; needs an evaluation harness"** (its
indicators are EVAL-typed in the record, guarded by `criterion_eval_typed`), not a number. The
footer is rendered verbatim as the task fixes it (see §Premises for the one inexact attribution).
Build products committed with their `build_report.json` (per-product sha256), the way the one-pager
/ brief were — no Seldon Artifact nodes (one-pager `RESULT_02`).

---

## Part C: gate, verify, protected paths

Gate tier is **`gate-task`** (the write set touches the framework record). All three detached,
logged, polled to their EXIT line.

- **`make gate-task`** (`logs/gate_task3.log`): **EXIT=0.** gate-fast **3432 passed, 0 failed, 19
  skipped, 41 xfailed, 0 deselected** in **258.23s (4:18)**; re-derivation (`-k re_derives`) **25
  passed** in **7.67s**.
  - The first gate run (`logs/gate_task.log`) was EXIT=2 with 11 failures. All were resolved and
    none was a defect in Part A/B: (a) eight were the record-write-back cascade — regenerated
    `docs/data/*` (L0), `docs/evidence/claims.yaml`, the `docs/brief/*` pages and the
    `docs/design/mcp_over_the_graph.md` page, and added the two labels to
    `mcp/airkg_tools.py::FRAMEWORK_LABELS`; (b) one (`test_a_scan_surface_is_not_gapped_for_being_thin`)
    was induced by a `corpus/scan` symlink I had added to supply gitignored corpus — removed, since
    the test writes into that directory; (c) two (`test_t2_priority_rows_carry_biblio_method`,
    `test_the_two_directives_are_recorded_and_grounded`) were worktree-environmental — gitignored
    substrate (`state/biblio_cache/`, `corpus/staging/proposed_schema/`) absent from a fresh
    worktree; they pass on main (the daily suite runs with full data) and passed here once linked.
- **`seldon verify`** (`logs/seldon_verify.log`): **EXIT=1 — one warning, pre-existing and not this
  task's.** "Blocks and waits: `98ed1dd1` is blocked with no reason recorded" (the executive-summary
  v4 task, flagged the same way by the one-pager's `RESULT_02`). Every check touching this task's
  write set passes: File hashes ✓, Stale artifacts ✓ (none stale), Relationship types ✓, Precedence
  74 edges acyclic ✓, Task source files all 218 resolve ✓, Event log 50795 events readable ✓.
- **Protected paths** (`logs/protected_paths.log`): **PASS (EXIT=0).**
  `build_framework_graph.py --dry-run` no-op (`unchanged=True`, empty delta); the framework record
  vs merge-base `73019bf7` is +182/-1 lines, the sole `-` line being a trailing comma gained by
  `serves_fcsm_concern_edges` when the three new counts keys follow it (no existing node, edge or
  value changed); the authoritative `framework_writeback` delta is additive-only (7 nodes, 16
  edges, 0 removed, 0 changed); `tests/test_framework_single_writer.py` 20 passed.

The daily full suite on **main** is red (`test_node_and_edge_counts_match_the_json_exactly@neo4j`,
a shared-Neo4j projection-staleness failure) and `.seldon/DISPATCH_STOP` is set, red since
2026-10-24 and independent of this task; this gate run reaches that test green because the record
was re-projected immediately before it.

### Premises this task got wrong
1. **Part A "13 Accessible".** Actual 12 (see §Part A Check 2). A premise error in the task file;
   the split is a recorded finding, 16 total.
2. **Footer line 2 attribution.** The task fixes the footer verbatim and says line two is "from
   `preface_source.yaml` as the one-pager reads it." It is not: the preface's `two_rungs_note`
   phrases the two rungs differently and mentions no "email step", and the one-pager's
   `two_user_lines()` derives different text. The task's fixed string was rendered as written (a
   task constant); the attribution is inexact. This footer is ICSP-facing text and should be read
   by the operator before the January briefing.
3. **The record-write-back cascade is unscoped by the task.** Editing the record drifts its
   consumers (L0 site, claims.yaml, brief pack, MCP labels/doc); regenerated here, as the one-pager
   did. The brief pack and `claims.yaml` pin the record's last-touching commit — see the rebase
   note on the brief-pack commit.

### Session usage
No model API calls were made: Part A, Part B and every regenerator are zero-spend (they read the
record, the grid and the cycle of record and render locally). The only tokens spent are this Claude
Code session's own, well under the **0.7M** cap the task declared.

## Commits
- `d0d5a40f` feat: Part A lineage + Part B build product + regenerated L0/claims/MCP-doc/labels.
- `4c4b162d` chore: regenerate the brief pack after the write-back (pins `d0d5a40f`).
- `aaf14215` chore: re-pin `claims.yaml` to the Part A record commit (it had been regenerated
  before the Part A commit existed).
  **Rebase note:** `claims.yaml` and the brief-pack headers pin the record's last-touching commit.
  If the dispatcher rebases this branch (changing that SHA) rather than preserving `d0d5a40f`,
  re-run `scripts/build_evidence_map.py` and `scripts/build_brief_pack.py` after the rebase and
  commit the result.

## Logs (gitignored; local artifacts this RESULT quotes)
`logs/gate_task3.log` (gate), `logs/seldon_verify.log` (verify), `logs/protected_paths.log`
(protected paths), `logs/rollup_build.log` (Part B build), `logs/regen_c1.log`/`logs/regen_brief.log`
(cascade regeneration), `logs/load_framework.log`/`logs/reproject*.log` (projection),
`logs/roundtrip.log` (Part A roundtrip), `logs/gate_task.log` (first gate run, 11 failures diagnosed
above).
