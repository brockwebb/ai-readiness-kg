# RESULT: 2026-09-21_g4_narrowed — STOPPED at decision 2 (write-back refused); nothing applied

**Stopped at:** decision 2/3, `build_framework_graph.py` → `framework_writeback.save`. Suite, `seldon verify`, protected-paths diff, projection, report/site rebuild and Issue closure were **not run**. No framework record, event, test or Issue was changed.

## What happened
I edited G4's skeleton row (patch preserved, unapplied: `logs/g4_narrowed_skeleton_edit.patch`), then ran `build_framework_graph.py`. `save` refused, as decision 2 anticipated as a possibility:

`REFUSED ... Would drop: 3 edge(s) {'EVIDENCED_BY': 3}: ind:G4->doc:statistical-policy-working-paper-46-data-quality-assessment, ind:G4->doc:fcsm-19-01-transparent-reporting-for-integrated-data-quality, ind:G4->doc:dcat-ap-3-0-0-r5r-vocabulary. Nothing was written.`

Decision 2 says: if `save` refuses, stop and report, do not use `--force`. I stopped. The skeleton edit was reverted so the tree stays consistent with the record (`git status` clean except the writer-owned `seldon_events.jsonl`).

## Decision taken on the grounding (for the next task)
- `rule_g4.py` (docstring and `UNMEASURED`): "Two of the definition's three clauses are NOT measured ... the statutory mandate and the statistical-versus-administrative provenance"; the rule tests `bureauCode` and `programCode` only. So clause 3 (provenance) is removed and both FCSM documents plus WP-46 leave the cell (WP-46 supported only that clause, and its Institutional Environment quote is a quality dimension, not a field). DCAT-AP goes (it existed for the statutory-mandate clause).
- Kept: `dcat-us-1-1-schema`, `dcat-us-3-dataset-schema` (publisher only), `dcat-us-3-overview`, `w3c-dcat-3`, `w3c-prov-o-ontology`, `schema-org-dataset`, each with its place and quote.
- New text: "The issuing authority of a data product is carried as machine-readable metadata on the product, in the fields DCAT-US defines (`publisher`, `bureauCode`, `programCode`)".

## Next step needed
The task's expected negative delta (-3 EVIDENCED_BY) is exactly what `save` refuses without `--force --reason`, and the task forbids `--force`. A follow-up task must either authorize `--force --reason "G4 narrowed by operator ruling 2026-09-21"` for this one delta, or add a sanctioned narrowing path to `save`. Then apply the patch and continue from decision 2.

## Premises this file got wrong
- Decision 2 treats the negative delta as sanctioned; the single writer has no path for it short of `--force`, which decision 2 forbids.
- The task named `tests/` edits (decision 5) and Issue closure (decision 4) after a step that cannot complete, so both are pending, not done.

## Gate
| gate | result |
|---|---|
| suite / gate-fast / gate-full | not run (stopped at §2) |
| seldon verify | not run |
| protected paths | not run (`scripts/check_protected_g4_narrowed.sh` not written) |
