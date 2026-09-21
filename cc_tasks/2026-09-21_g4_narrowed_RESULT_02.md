# RESULT 02: 2026-09-21_g4_narrowed (as amended by ADDENDUM_01) — DONE

Supersedes nothing; `..._RESULT.md` (the stopped first run) stays. Session `c933d0a7-0377-46a6-8dd2-7f1e9fff849a`.

## G4 text
- **Before:** "Issuing authority, statutory mandate, and statistical-vs-administrative provenance carried as structured metadata — the trust signal AI rankers need to prefer authoritative sources over aggregators".
- **After:** "The issuing authority of a data product is carried as machine-readable metadata on the product, in the fields DCAT-US defines (`publisher`, `bureauCode`, `programCode`)". Patch: `logs/g4_narrowed_skeleton_edit.patch`, applied unmodified.
- **Clause 3 (provenance) removed.** `rule_g4.py` docstring: "Two of the definition's three clauses are NOT measured ... the statutory mandate and the statistical-versus-administrative provenance"; the rule tests `bureauCode` and `programCode` only (quoted in the first RESULT §Decision).

## Evidence cell
- **Before (9):** WP-46, FCSM 19-01, DCAT-US 1.1, DCAT-US 3 dataset, DCAT-US 3 overview, W3C DCAT 3, PROV-O, schema.org Dataset, DCAT-AP 3.0.0 r5r.
- **After (6):** the six DCAT-US / W3C / PROV-O / schema.org documents, each with its place and quote, unchanged. Dropped: WP-46, FCSM 19-01, DCAT-AP.
- DCAT-AP stays an admitted, manifest-listed document that no indicator now cites. The three documents remain in the corpus.

## Write-back
- Without `--force`: refusal named exactly the three edges (`ind:G4->` WP-46, FCSM 19-01, DCAT-AP; type `EVIDENCED_BY`), nothing else.
- With `--force --reason "G4 narrowed ... (ADDENDUM_01)"`: written, event `3b505e7762884481bf253132593a25a5` (`events/batch-033_framework.jsonl`). `counts.evidenced_by` 148 → 145.
- Projection: full `build_projection.py`, `logs/g4n_proj.log` EXIT=0 (about 65 min; the log is empty until the end). `tests/test_framework_projection_roundtrip.py`: 9 passed.
- `score.py` before vs after: byte-identical (`logs/g4n_score_before.txt`, `logs/g4n_score_after.txt`). Rule, tier, Findings, state/: untouched.
- Rebuilt: `mcp/airkg_doc.py`, L0 report, PDF (15 pages, 7 prose), site. Release date and version unchanged.

## Issues closed (state `resolved`, closing note verbatim from the task)
`c2295615-b3a7-49d2-8925-33f1a9396743` (statutory mandate has no defining source), `a33e8654-e523-4470-bfbe-18e670d2e16c` (AI-ranker clause is the framework's inference).

## Tests
`tests/test_g4_locators_and_progress_drift.py`: `G4_DOCS` 9 → 6. `tests/test_g4_resourcing_reissue.py`: the DCAT-AP-by-analogy and AI-ranker-inference tests replaced by `test_g4_is_narrowed_to_the_measured_claim`. Guard: `scripts/check_protected_g4_narrowed.sh`. Remaining quotes pass the grounding test.

## Gate
| gate | passed | skipped | xfailed | deselected | log |
|---|---|---|---|---|---|
| `make gate-fast` | 2741 | 3 | 12 | 27 | `logs/g4n_gate_fast.log` (EXIT=0, 578 s) |
| `make gate-full` | 2768 | 3 | 12 | 0 | `logs/suite.log` (EXIT=0, 2211 s) |
| `seldon verify` | all checks passed | | | | `logs/g4n_verify.log` EXIT=0 |
| protected paths | PROTECTED PATHS OK | | | | `logs/g4n_protected.log` EXIT=0 |

Skips: dispatch quiet-state (tree dirty, STOP file), E5 controls, no dev proposition with SE and CI.

## Premises wrong
- Task decision 2 forbade `--force` although `save` sanctions it for a recorded deletion (fixed by ADDENDUM_01).
- The addendum was untracked when dispatched; it was committed (`0635b56`) and then showed as deleted in the working tree after the dispatcher's commits (`97d466b`, `444afcf`); restored from HEAD.
- Desktop registered `cc_tasks/2026-09-21_g4_narrowed_apply.md` (`6beddf1c`), a superseding task for the same work, while this one was in flight. This work is done; that task should be marked complete or cancelled rather than dispatched, or it will find nothing to do.
- Projection took ~65 min, not the "short gate" the task implied.

## Spend
`npx ccusage@latest session --json`, session `c933d0a7-0377-46a6-8dd2-7f1e9fff849a` (`logs/g4n_ccusage.json`): 3,037,098 tokens total (input 80, output 11,893, cache creation 80,732, cache read 2,944,393), claude-sonnet-5, $1.03. Replaces the 2.5 to 4M estimate. Sampled before the final commit turn.
