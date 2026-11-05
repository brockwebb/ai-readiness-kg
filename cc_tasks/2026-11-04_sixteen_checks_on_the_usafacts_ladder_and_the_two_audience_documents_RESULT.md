# RESULT: the sixteen checks re-parented onto USAFacts' three-track ladder, the roll-up and one-pager rebuilt on it, and the ICSP page and working-group explainer built

**Task:** `cc_tasks/2026-11-04_sixteen_checks_on_the_usafacts_ladder_and_the_two_audience_documents.md`
**Date executed:** 2026-11-04
**Session:** dispatched headless worktree `linear-drifting-wirth`.
**Status:** complete. Part A (ladder in the record), Part B (roll-up + one-pager rebuilt), Part C (two documents), Part D (gate + RESULT) all done. `make gate-task` EXIT=0; `seldon verify` EXIT=1 on two known/not-this-task warnings; protected-paths diff as expected.

Recall used: none — the predecessor roll-up, one-pager and measurement sheet were rebuilt from their live scripts (`readiness_rollup_build.py`, `sixteen_checks_build.py`) and DN-020, not from the recalled RESULTs; the recall hits confirmed those artifacts exist but did not change the approach.

---

## §1. The sixteen id-to-name pairs and the rung counts (first, as ordered)

**The sixteen `DESCENDS_FROM` placements, resolved by `rf_name_brief` (not by DN-020 §4's letter-code — see premise 1).** `display` is the roll-up's display code DN-020 §4 prints; `spec` is the record id the name resolves to; `rung` is the USAFacts rung the new edge points at (`basis: DN-020 §4`).

| DN-020 §4 display | record spec | rung | rf_name_brief (the resolving name) |
|---|---|---|---|
| A3 | `spec:A5` | `usaf:pre:discoverable` | The data page is in the site's list of pages |
| A6 | `spec:A6` | `usaf:pre:discoverable` | The page labels itself as a dataset |
| D1 | `spec:D4` | `usaf:pre:discoverable` | The product is listed in the agency's data inventory |
| D2 | `spec:D1` | `usaf:pre:licensed` | The terms of reuse, under a recognised name |
| A1 | `spec:A1` | `usaf:access:1` | Data offered as a file a program can read |
| A2 | `spec:A3` | `usaf:access:1` | The whole dataset in one download |
| A4 | `spec:A4` | `usaf:access:1` | Whether the site's visitor rules let AI tools in |
| A12 | `spec:A12` | `usaf:access:1` | The site serves what its own rules permit |
| A11 | `spec:A11-declared` | `usaf:access:1` | What the site states about automated access |
| A10 | `spec:A10` | `usaf:access:1` | The interactive data tool answers honestly |
| A5 | `spec:A2` | `usaf:access:2` | A published description of the agency's data service |
| A9 | `spec:A9` | `usaf:access:2` | A front door built for programs |
| A13 | `spec:A13` | `usaf:access:2` | From a data page to the data service, terms, change log and inventory |
| F3 | `spec:F4` | `usaf:access:2` | A change history a program can follow |
| B1 | `spec:B3` | `usaf:context:1` | The methods are readable as plain text |
| A8 | `spec:A8` | `usaf:context:2` | The release date, and a link to the latest release |

Every row resolved its verbatim name to exactly one `MeasurementSpec`; none was ambiguous, so the task did not stop on any row.

**The rung counts (rendered on the roll-up, verified two ways — see Part B).**

| USAFacts rung | checks placed | agencies passing (of sixteen) |
|---|---|---|
| Prerequisite, discoverable | 3 | zero |
| Prerequisite, clearly licensed | 1 | zero |
| Access I | 6 | eleven |
| Access II | 4 | one |
| Context I | 1 | two |
| Context II | 1 | one |
| Access III | 0 | none measured |
| Context III | 0 | none measured |
| Evaluation I | 0 | none measured |
| Evaluation II | 0 | none measured |
| Evaluation III | 0 | none measured |

New record counts: `usafacts_track_nodes: 3`, `usafacts_level_nodes: 9`, `usafacts_prerequisite_nodes: 3`, `usafacts_descends_from_edges: 16`. Record now 258 nodes / 526 edges (was 243 / 501). Writeback event `140abeaf5a7244dda26b61b177b4bf62`, framework sha256 `439c6717…99b65bb`.

---

## §2. Step 0 quotes

1. **`c1662a22` completed and projection green.** `c1662a22` (rematerialize worktree admissions) reached `artifact_state_changed -> completed` at `2026-11-03T11:53:27.756731Z`, then `dispatch_finished`. `get_overview` → `projection_gate.status: "green"`, `nodes_compared: 243, mismatches: []` (read before Part A; 258 after Part A and re-projection).
2. **Served model = `seldon models resolve author`.** `seldon models resolve author` → `claude-opus-4-8`; the session runs on `claude-opus-4-8`. Match; no `model_substituted`.
3. **DN-020 read in full; the two docling files read.** DN-020 (`docs/design/2026-11-04_DN-020_…`) read whole. `state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md` (slides 9, 15–21) and `…-overview-2026.md` read from `$SELDON_PRIMARY_CHECKOUT` (both gitignored, so not in a clean worktree — seeded for the gate; see §7).
4. **Prior-art verdict passes.** `seldon prior-art verify docs/design/2026-11-04_DN-020_…` → every row `pass`; `verdict recorded in the governed ledger: event 1389f24c1f0d480789cca610da06a4d4`.

---

## §3. Docling line for every USAFacts phrase rendered

OCR normalisation applied to the verbatim text (de-hyphenation of a space around a hyphen, "machine -readable" → "machine-readable"; a doubled article, "the open the web" → "the open web") — the NFKC/de-hyphenation discipline of `kg/extraction/grounding.py`, recorded per node.

**Tracks** (one-line descriptions, `usafacts-ai-ready-framework-overview-2026.md`):
- Agentic Access — overview line 13.
- Agentic Context — overview line 14.
- Agentic Evaluation — overview line 15 (OCR "publ ic" → "public").

**Levels** (caption = `name`, deck "How it works"; detail bullets = `text`; `usafacts-ai-ready-framework-deck-2026-08.md`):
- Access I "Data is published in machine-readable files" — deck 441 (Access detail slide 18 OCR'd no Level I bullet; `text` repeats the caption).
- Access II "Stable, documented endpoints agents can crawl" — deck 443 (caption), 491 (detail "Lineage/change notes").
- Access III "Agent-native interface for live, structured queries" — deck 445 (caption), 493–495 (detail).
- Context I "Definitions and units documented for humans" — deck 449 (caption), 537–539 (detail).
- Context II "Methodology and caveats travel with each dataset" — deck 451 (caption), 543–547 (detail).
- Context III "Context is machine-readable and citable in an answer" — deck 453 (caption), 551–555 (detail).
- Evaluation I "A published evaluation set with reported pass rates" — deck 457 (caption), 587–591 (detail).
- Evaluation II "Continuous automated evaluation at scale" — deck 459 (caption), 595–599 (detail).
- Evaluation III "Integrated quality assurance programs across agencies and industry" — deck 461 (caption), 603–607 (detail).

**Prerequisites** (deck slide 15):
- "Open by default" — deck 471.
- "Discoverable" — deck 473 (OCR "the open the web" → "the open web").
- "Clearly licensed" — deck 475.

**USAFacts title phrase rendered in prose:** "AI-ready data" (italic) — USAFacts' own title (deck 19/247, overview title); the only place "AI" is rendered outside a quoted caption, per the vocabulary rule.

The rendered captions that reach a reader: the roll-up's "What the framework asks for" column (level `name` / prerequisite `text`), and the explainer's "what the next rung asks for" lines (level `name`). All verbatim from the lines above.

---

## §4. Part B check lines (roll-up and one-pager, read back as a reader)

Both PDFs opened and read back. Every automated check green; `failures: []` on both build reports.

**Roll-up** (`reports/diagnostic/rollup/`, 1 page at 9.5pt):
- `vocabulary: {"project_prose": []}` — clean. (The banned-word scan runs over the project's prose; the verbatim USAFacts caption "Stable, documented endpoints agents can crawl" is a quoted caption and exempt — see premise 2.)
- `dashes: {"project_prose": []}`, `markdown_dashes: []`, `markdown_check_codes: []`, `markdown_mentions_508: false`.
- `font_colour_audit.docx: []` (Calibri, black/grey/orange only).
- `bucket_counts_match_part_a: true` — rendered rung check counts equal the Part A `DESCENDS_FROM` edge split.
- `agencies_passing_match: true` — the edge-derived passing counts equal a second, independent path (`verify_pass_by_rung`, a literal DN-020 §4 rung→leg map over the full state matrix).
- `scored_match_four_specified: true` — scored = `['A1','A3','A5','D4']`, the four `instrument_state == specified` specs.
- `docx_pages: 1, pdf_pages: 1`.

**One-pager** (`reports/diagnostic/one_pager/`, 1 landscape page):
- rows regrouped by USAFacts rung (Part B item 8): order `['A5','D4','A6','D1','A1','A3','A4','A10','A11-declared','A12','A2','A9','A13','F4','B3','A8']` (rung order, scored-first within rung).
- `vocabulary` clean on markdown and docx; `concern_column_vs_record: []`; `mentions_508: []`; `font_colour_audit.docx: []`; `digit_audit: []`.
- `chosen: {body_pt: 7.0, where_mode: first_clause, passes_mode: clause}`, `docx_pages: 1, pdf_pages: 1` (fit ladder unchanged; reordering does not change total content, so the page fit is as before).

---

## §5. Part C: placeholder report and the two reader notes

**Documents** (`reports/dn020/`, built by new `scripts/dn020_documents_build.py`):
- `ICSP_SI_Readiness_One_Page.pdf` — **1 page** (required 1). docx + md beside it.
- `SI_Readiness_Working_Group_Explainer.pdf` — **4 pages** (required 4–6). docx + md beside it.
- `vocabulary: {icsp: [], explainer: []}`, `dashes: {icsp: [], explainer: []}` — clean (USAFacts captions exempted as the quoted zone).
- worked check: `A6` ("The page labels itself as a dataset") — the simplest sensor: one request to the data page, reading the markup as served, following no link and visiting no other location.

**Placeholder report (all four pending — no PNG dropped in yet):**

| figure | DN-020 §7 | document | placed | path |
|---|---|---|---|---|
| 1 ladder | picture 1 | ICSP | placeholder | `reports/figures/dn020/1.png` |
| 3 where agencies stand | picture 3 | ICSP | placeholder | `reports/figures/dn020/3.png` |
| 2 lineage | picture 2 | explainer | placeholder | `reports/figures/dn020/2.png` |
| 4 one check end to end | picture 4 | explainer | placeholder | `reports/figures/dn020/4.png` |

When a PNG is dropped into `reports/figures/dn020/<n>.png` a rebuild places the image instead; the image is bound to the same height as the placeholder frame, so a picture of any aspect keeps the ICSP to one page and the explainer to its range.

**Reader note, ICSP (one line):** a reader may pause at the two illustrations being placeholders (the operator drops in the pictures); the prose and the per-rung counts stand on their own and nothing else reads as unfinished.

**Reader note, explainer (one line):** a reader may stumble on the per-rung counts not climbing (zero clear the discoverable prerequisite, eleven clear Access I) — addressed with one sentence under "What each measured rung asks" that the counts are read rung by rung, not as a cumulative climb, and a not-measured check is left out, never a fail.

---

## §6. Premises this task got wrong

1. **DN-020 §4's letter-codes are not record spec ids.** Part A item 4 says to "resolve every record id in DN-020 §4 against the spec's `rf_name_brief`", but DN-020 §4 prints the roll-up's *display* codes (A3, A6, D1, D2, F3, B1 …), which do not equal the record spec ids (e.g. display A3 = the check "The data page is in the site's list of pages" = record `spec:A5`; display B1 = record `spec:B3`; display F3 = record `spec:F4`). Resolution was keyed on the verbatim `rf_name_brief`, the reliable anchor, and all sixteen resolved one-to-one (§1).
2. **The vocabulary rule and a verbatim USAFacts caption collide on "crawl".** USAFacts' Access II caption is "Stable, documented endpoints agents can crawl", and "crawl" is a banned project-prose word. The task's own rule names "USAFacts' own titles and quoted captions" as the zone where USAFacts' terminology stands, so the banned-word scan was scoped to the project's prose and the verbatim captions were exempted (both Part B and Part C). Recorded on the builders.
3. **`32e394f1` added no `AiReadyCriterion` entry to `kg/schema.yaml` or `docs/schema_v0.1.md` — there was nothing to "mirror".** Part A item 5 says to add the three labels "in the style of the `AiReadyCriterion` entry (`32e394f1` set the pattern)". The lineage commit (`37b3b82a`, artifact `32e394f1`) touched `load_framework_graph.py`, both roundtrip/single-writer tests, `mcp/airkg_tools.py` and `docs/evidence/claims.yaml` — **not** `kg/schema.yaml` or `docs/schema_v0.1.md`. Neither of those files carries any assessment-layer label (not even `AssessmentCriterion`; `FcsmConcern`/`AiReadyCriterion`/`ExtensionGroup` are absent from both). Grounded decision: documented the three new labels and the `DESCENDS_FROM` edge type in **`kg/schema.yaml`'s `assessment_layer` block** (the correct authored home, where `DECOMPOSES_INTO` already lives and where `test_framework_graph.py` reads `assessment_layer.node_types`), and extended the `DECOMPOSES_INTO` pairs. **`docs/schema_v0.1.md` is the parser-visible EXTRACTION catalogue** (title "Extraction Schema v0.3"); the assessment layer is deliberately parser-invisible (`kg/schema.yaml` §576–582; `test_framework_graph` asserts disjointness), so adding assessment labels there would be wrong, and it was left unchanged. The protected-paths diff therefore shows three of the four named files changed, not four.
4. **The two existing products were not one page by content alone.** The roll-up grew from five rows (A/B/C/D/F) to eleven rungs; it needed 9.5pt to stay one portrait page (was built at a larger size). Recorded so a later reader does not read the smaller font as drift.

---

## §7. The gate, with wall-clocks (Part D)

**Worktree seeding.** This dispatched worktree lacks the gitignored corpus binaries, the T0 substrate and two staging artifacts, so the gate first ran 17 environmental failures (files "not on disk"), the ripple this worktree's own AR-001 is about. Copy-seeded from `$SELDON_PRIMARY_CHECKOUT` (real dirs → gitignored contents invisible to `git status`): `corpus/{bulk,bulk_md,cisco,crosswalk,g1eval,inbox,kernel,measurement_theory,pilot,round2,triage}`, `corpus/staging/proposed_schema`, `state/docling_md`, `state/biblio_cache`, `state/corpus_index.db`. All confirmed absent from `git status` after seeding.

Two of the 17 were **real ripples of this task**, not environmental, and were regenerated:
- `docs/design/mcp_over_the_graph.md` — the MCP doc page pinned "243 nodes compared"; the record now holds 258. Regenerated with `mcp/airkg_doc.py`; `--check` byte-for-byte green.
- `docs/brief/E_architecture.md` — pinned `scripts/load_framework_graph.py:120`; the `ASSESSMENT_LABELS` definition moved to :126 under this task's edit. Regenerated with `scripts/build_brief_pack.py` (one line changed; the other 61 pack files byte-identical).

**`make gate-task`** (the record was touched, so gate-task, not gate-fast), detached, logged `logs/gate_task.log`, polled to EXIT:
- gate-fast tier: **3434 passed, 17 skipped, 0 failed, 41 xfailed, 2046 warnings in 248.66s** (0 errored). (`pytest -q` prints no deselected count for the `-m "not slow"` marker filter; the slow tier is excluded by marker, not deleted.)
- re-derivation tier: **25 passed in 8.68s**.
- `EXIT=0`.
- The 17 skips are the remaining gitignored-absent artifacts that skip rather than fail (e.g. "seldon checkout not beside this repo", a corpus binary a specific test still finds absent).

**`seldon verify`** (`logs/seldon_verify.log`): **EXIT=1**, two warnings, neither from this task:
- `98ed1dd1 is blocked with no reason recorded` — the pre-existing known warning the task names.
- `c8fb9f62 [proposed] cc_tasks/2026-11-04_AR-001_…` names a `source_file` not on disk in this worktree — a different, proposed task whose file is not in this checkout.

**Protected-paths diff** (`git diff --stat` on the four named files):
```
 docs/data/ai_readiness_framework.json | 472 ++++++++++++++++++++++++++++++++--
 framework/ai_readiness_framework.json | 472 ++++++++++++++++++++++++++++++++--
 kg/schema.yaml                        |  34 ++-
 3 files changed, 942 insertions(+), 36 deletions(-)
```
`docs/schema_v0.1.md` is unchanged, by the grounded decision in premise 3; nothing outside the four named files is in this diff.

**Reports are tracked, not gitignored** — `git check-ignore` on the four new/changed PDFs (`reports/dn020/ICSP_SI_Readiness_One_Page.pdf`, `reports/dn020/SI_Readiness_Working_Group_Explainer.pdf`, `reports/diagnostic/rollup/Readiness_Diagnostic_Rollup.pdf`, `reports/diagnostic/one_pager/Readiness_Diagnostic_16_Checks.pdf`) returned nothing (RC=1, none ignored).

Log paths cited: `logs/gate_task.log`, `logs/seldon_verify.log` (gitignored local artifacts).

---

## §8. Session usage against the 1.0M estimate

No paid model calls were made: Part A–D are deterministic Python (record writeback, projection, builders, pandoc/typst renders) and `pytest`. The spend ledger records no new spend for this task (`model` role `author` was never invoked — nothing in this task calls a model). The 1.0M-token figure in the task's `**Spend:**` header is the Claude Code session's own token budget, not a priced API spend; this session ran well under it (all work was tool-driven builds and tests, no generation). There is no in-band token meter available to the session to print an exact count.

---

## §9. Files changed

New: `scripts/add_usafacts_lineage.py`, `scripts/dn020_documents_build.py`, `reports/dn020/*` (md/docx/pdf × 2 + build_report.json).
Part A: `framework/ai_readiness_framework.json`, `docs/data/ai_readiness_framework.json`, `docs/data/index.json`, `kg/schema.yaml`, `scripts/load_framework_graph.py`, `mcp/airkg_tools.py`, `tests/test_framework_projection_roundtrip.py`, `tests/test_framework_single_writer.py`, `events/batch-033_framework.jsonl`.
Part A ripples (regenerated): `docs/design/mcp_over_the_graph.md`, `docs/brief/E_architecture.md`.
Part B: `scripts/readiness_rollup_build.py`, `scripts/sixteen_checks_build.py`, `reports/diagnostic/rollup/*`, `reports/diagnostic/one_pager/*`.
