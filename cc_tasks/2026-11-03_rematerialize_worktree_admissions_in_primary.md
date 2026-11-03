# CC Task: put the four documents admitted in worktrees on 11-02 and 11-03 back into the primary checkout, and file why they went missing

**Date:** 2026-11-03
**Project:** ai-readiness-kg
**Authored by:** Desktop session (OODA on 5ae6744f).
**Implements:** DD-003 (an `included, verified` manifest entry has its bytes on disk), DD-030 (admission requires convertibility).
**Amended by:** none.
**Builds on:** `cc_tasks/2026-11-02_admit_usafacts_three_track_framework_RESULT.md`, `cc_tasks/2026-11-02_v3_measurement_sheet_RESULT.md` §2, `scripts/admit_usafacts_three_track.py`, `scripts/admit_measurement_theory_sources.py`.
**Framework layer served (DN-005 §5 rule 1):** none; corpus integrity, so DN-020's prior-art verify can read the USAFacts deck.
**Fulfils:** its own ResearchTask.
**Model:** author
**Spend:** est. 0.2M tokens, Claude Code session included. No model calls through model_stub. The task ends by printing its own session usage.
**Parts:** A 0.55, B 0.45.
**Part map:** A restores the files into the primary; B files the structural cause.
**Network:** allowlist: www.iso.org, www.cs.umd.edu

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Why

Four documents were admitted by dispatched sessions running in worktrees: `iso-iec-ieee-15939-2017` and `basili-caldiera-rombach-1994-gqm` (829a5010, 2026-11-02), `usafacts-ai-ready-framework-deck-2026-08` and `usafacts-ai-ready-framework-overview-2026` (5ae6744f, 2026-11-03). Their manifest entries and events merged to main. Their gitignored outputs did not: on 2026-11-03T10:4xZ the primary checkout has no `corpus/crosswalk/usafacts-ai-ready-framework-*.pdf`, no `corpus/*/` file for the ISO or GQM sources, and none of the four under `state/docling_md/` (388 files; quoted by Desktop with `ls state/docling_md | grep -i -E 'iso-iec|basili|usafacts'`, which returned only the three older USAFacts documents). The worktrees were removed at merge, taking the files with them. The operator's two original PDFs survive in the primary at `corpus/staging/inbox/` (sha256 `9cbe6ae3…bfbb0b` deck, `e47c5bc6…7d7876fc` overview). ISO and GQM were fetched by `scripts/fetch_allowlisted.py` and can be fetched again.

This session also runs in a worktree. Every output in Part A is written to the **primary checkout** at `$SELDON_PRIMARY_CHECKOUT` (the path the admission task copy-seeded from), not to the worktree, or it is lost the same way.

## Part A: restore into the primary

1. Quote `echo $SELDON_PRIMARY_CHECKOUT` and confirm it is `/Users/brock/GitHub/ai-readiness-kg`.
2. For each of the four doc_ids, read the canonical path and sha256 from `corpus/manifest.json` (the field the integrity gate uses; quote it) and write the file there in the primary:
   - USAFacts deck and overview: copy from `$SELDON_PRIMARY_CHECKOUT/corpus/staging/inbox/` (filenames as the operator gave them); verify sha256 equals the manifest's.
   - ISO 15939 and GQM: re-run the fetch through `scripts/fetch_allowlisted.py` exactly as `scripts/admit_measurement_theory_sources.py` does, with output into the primary's canonical path; verify sha256 equals the manifest's. If a re-fetch returns different bytes (the ISO catalogue page can change), do not overwrite the manifest: record both hashes in the RESULT and stop on that document.
3. Convert each restored file to `$SELDON_PRIMARY_CHECKOUT/state/docling_md/<doc_id>.md` (and its `.meta.json`) with the canonical converter the admission used (`t1_build_index --phase convert`, per the 219786c5 commit message), pointed at the primary. Quote line counts.
4. Quote from the primary: `ls corpus/crosswalk | grep usafacts`, the ISO and GQM canonical paths, and `ls state/docling_md | grep -i -E 'iso-iec|basili|usafacts'` (expected 7 `.md`).
5. Grounding spot-check in the primary's deck markdown, via `kg.extraction.grounding.is_grounded`: "Three tracks, three levels within each track", "Modeled on SLSA", "Crawlable data", "Lineage/change notes", "Published methodology documentation", "Provenance and update cadence", "Clearly licensed". Quote hit or miss for each (DN-020 quotes these).
6. `git status --porcelain` in the primary: expected no change (all four outputs are gitignored). Quote it.

- check: `sh -c "test -n \"$SELDON_PRIMARY_CHECKOUT\" && echo ok"` prints `ok`.

## Part B: file the cause

Open one Issue (`seldon issue create`), importance high, urgency medium, titled "admissions in dispatched worktrees lose their gitignored corpus outputs at merge". Body: the four doc_ids, the evidence above, the fact that `seldon verify` and the gate stayed green while the primary lacked the files (quote what in verify or `kg/manifest.py` integrity checks the on-disk file, and why it did not fire in the primary, by file:line), and the two candidate fixes for a design note to choose between: (a) admission drivers write gitignored outputs to `$SELDON_PRIMARY_CHECKOUT`, as this task does by hand; (b) the dispatcher copies declared gitignored outputs back to the primary before it removes a worktree. Do not implement either.

## Gate and RESULT

Write set in the worktree: logs, Issue events, `seldon_events.jsonl`. Write set in the primary: gitignored corpus and docling files only. Gate: `make gate-fast`, detached and logged; quote passed, skipped, xfailed and deselected. Then `seldon verify` (quote EXIT) and the protected-paths diff on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json` (expected empty).

RESULT at `cc_tasks/2026-11-03_rematerialize_worktree_admissions_in_primary_RESULT.md`: §1 the Part A step 4 and step 5 quotes first; log paths in §6. Then `seldon cc complete`, commit, push.
