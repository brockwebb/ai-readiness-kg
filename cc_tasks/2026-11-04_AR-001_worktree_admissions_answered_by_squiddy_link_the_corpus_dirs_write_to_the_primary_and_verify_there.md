# AR-001: squiddy's answer to the worktree-admission filing: link the gitignored corpus directories into every worktree, check each admission's bytes in the primary, and read the MCP corpus layer as lagging the manifest

**Status:** proposed
**Author:** squiddy SQ-109's Claude Code session, 2026-11-04. This is the return (AD-036-R16) of ai-readiness-kg's filing to squiddy, `squiddy/cc_tasks/2026-11-03_consumer_filing_from_ai_readiness_kg_documents_admitted_in_a_dispatched_worktree_are_not_in_the_primary_after_merge.md` (AR-7; Issue `2b5a296d`), measured at squiddy HEAD `6c77b136` by SQ-109.
**Returns:** squiddy:SQ-109
**Repo:** ai-readiness-kg. L4: commit in ai-readiness-kg. No squiddy or seldon change.
**After:** ec1112d3
**Governing:** squiddy SQ-109 (`/Users/brock/GitHub/squiddy/cc_tasks/2026-11-04_SQ-109_ai_readiness_kg_filing_worktree_admissions_absent_from_the_primary_measured_owned_and_returned.md` and its RESULT); seldon `dispatch.worktree_links` (`seldon/core/dispatch.py` `PARALLEL_DEFAULTS`, `seldon/core/worktree.py` `link`); squiddy DN-049 R-208, R-211. No new ruling.
**Framework layer served (DN-005 §5 rule 1):** none (corpus plumbing under the validity layer).
**Model:** author
**Spend:** est. 0.4M tokens, Claude Code session included. Basis: one config edit, two driver edits with their tests, and one verification pass over four documents; SQ-109 (measuring the same five items) used about 0.2M. Zero model calls.
**Parts:** A 0.40, B 0.40, C 0.20.
**Network:** none
**Exclusive:** yes. Part A changes the dispatcher configuration every later task of this repository runs under.
**Premises:**
- premise: squiddy filed the task this returns | check: `test -f /Users/brock/GitHub/squiddy/cc_tasks/2026-11-04_SQ-109_ai_readiness_kg_filing_worktree_admissions_absent_from_the_primary_measured_owned_and_returned.md`
- premise: the dispatcher links named paths into a worktree | check: `grep -q '"worktree_links"' /Users/brock/GitHub/seldon/seldon/core/dispatch.py`
- premise: the two admission drivers exist | check: `sh -c 'ls scripts/admit_measurement_theory_sources.py scripts/admit_usafacts_three_track.py'`

Glob and read every sibling `*AR-001*ADDENDUM*.md`.

## What squiddy measured, per item of your filing

| item | squiddy's finding | owner |
|---|---|---|
| (1) your drivers on the `admit_noaa_naos.py` pattern | Context. The four documents went through `kg.manifest` (your dixie ledger), not through the kit: none of the four is in `graphs/ai-readiness/corpus/manifest.yaml` or its ledger. | yours |
| (2) gitignored outputs do not survive a worktree merge | **Reproduced without the dispatcher.** A scratch repository admitted one document through the kit's own path in a git worktree, merged, and ran `git worktree remove` with no `--force`. It exited 0 and deleted every ignored output. Under your graph's `.gitignore` (`intake/inbox/*`) that included the PDF, and the merged manifest still said `acquired`. No gate caught it. Your `kg.manifest verify` is unwired on the real corpus (your c1662a22 RESULT §3). The kit has no presence check either: an absent held file is not a move under SQ-107, and `drift` and `presence` compare records, not bytes. The dispatcher's `dispatch_finished` records for 829a5010 and 5ae6744f did name `corpus/crosswalk/` in `merge.discarded_ignored`, but among about sixty paths, mostly your seeded copies. | **seldon** for the loss (filed: seldon `cc_tasks/2026-11-04_consumer_filing_from_squiddy_a_merged_worktrees_removal_discards_gitignored_outputs_the_primary_does_not_hold.md`, commit `7b1e18ba`); **squiddy** for its own admission path and a presence refusal (SQ-111); **yours** for the interim (Parts A and B) |
| (3) ISO 15939 HTTP 403 | The kit now records this as `posture: refused` with the evidence, the observation date and `manual_acquisition: true` (SQ-020R, DN-055 R-240). The test is `tests/test_sq020r_posture.py::test_the_iso_403_is_recorded_refused_with_evidence_date_and_the_manual_flag`, and it passes at squiddy HEAD. Your entry was admitted by `kg.manifest`, so it carries none of this until it reaches the kit graph. | context |
| (4) the MCP corpus layer reads the ledger, not `corpus/manifest.json` | **The kit's design, not your wiring.** Your MCP corpus verbs read the kit graph's database (`mcp/airkg_guard.py` `corpus_database`), a replay of `graphs/ai-readiness/ledger`. Under DN-049 R-208 that graph takes your `kg.manifest` entries through its intake `{source: dixie, manifest: /Users/brock/GitHub/ai-readiness-kg/corpus/manifest.json}`, and only when its catalog node runs. R-211 then holds a new document for an extraction pilot. The kit's ledger was last written on 2026-10-24. The four documents are exactly the four `manifest.json` ids (of 407) the kit manifest (404) does not hold. **The kit never told you this anywhere you read**, which is squiddy's defect. | **squiddy** (SQ-112: the rule in `docs/KIT_BOUNDARY.md`, and `build status` counts the lag) |
| (5) documents archived in iCloud `~/Documents`, symlinked in | **The kit's, with a design note first (SQ-111, DN-056).** Measured today: a symlink to a file outside the checkout is read, hashed and stat-checked through the link, and an edited target counts as moved. But an evicted iCloud file looks absent and is silent. A text written through a symlinked `texts/` is recorded as the archive's absolute path. A directory symlink inside the inbox is not walked. A symlink named `texts` is not ignored by a `texts/` pattern, so it is committed. | **squiddy** (SQ-111) |

## Interim instruction for your admission drivers (until SQ-111 and the seldon answer land)

1. Every gitignored output an admission writes must be in the primary checkout when the task ends. Use one of two routes. The first is a path the dispatcher links (Part A). The second is a path under `$SELDON_PRIMARY_CHECKOUT` that the driver writes directly. Write nothing that the merge cannot carry into the worktree's own ignored directories.
2. Every admission RESULT shows each admitted id's `local_path` and docling render listed in the PRIMARY. It also shows `python -m kg.manifest verify` run against the primary's `corpus/manifest.json` for those ids.
3. A RESULT never says a newly admitted document is in the MCP corpus layer. It is not, until the kit graph catalogs it.
4. Move no held bytes into `~/Documents` behind symlinks yet (item 5).

## Part A: link the corpus directories

1. Add `dispatch.worktree_links` to `seldon.yaml`. List the gitignored directories your admission drivers write and your gate reads: at least `corpus/crosswalk`, `corpus/measurement_theory`, `state/docling_md`, and the other `corpus/` lanes your `airkg-worktree-gate-seeding` practice copies. Keep `.env`. `worktree.link` links a directory that exists in the primary and skips one that does not.
2. Run `seldon dispatch status` and confirm the links are in force. A path that no longer has to be seeded is the evidence the seeding copy can stop.
3. State the trade in the RESULT. A session writes into the primary through a link before its merge. So a task that fails leaves bytes the manifest does not name. They are content-addressed, and `kg.manifest verify` checks only named entries.

## Part B: the drivers

4. Change `scripts/admit_measurement_theory_sources.py` and `scripts/admit_usafacts_three_track.py`. Each one ends by checking that every output it wrote resolves inside `$SELDON_PRIMARY_CHECKOUT`, whether directly or through a link, and refuses by name if any does not. Write the test first: run the driver in a temporary git worktree with no link, and it must refuse.

## Part C: the record

5. Add a line under Issue `2b5a296d` naming this return and the three owners. Close the Issue only when Part A's links are in force and Part B's refusal is tested.

## Not to do

- No edit to squiddy or seldon. No `squiddy build` on `graphs/ai-readiness`; that is its own task under R-211.
- Do not rematerialize ISO 15939; it is a posture case.
