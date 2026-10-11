# ADDENDUM 01 to `2026-10-07_seed_known_locations_verify.md` (part 2): the write set admits the two collection changes part 1 proved necessary, and the freeze covers the stored KG answers

**Date:** 2026-10-10
**Authored by:** Desktop session, from part 1's RESULT §5 (`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability_RESULT.md`) and the 2026-10-10 gate logs. Written before part 2 was read by any session. Read with the base task; where they differ, this addendum governs. Nothing else in the base task changes, launch procedure included.

## Why

Part 1 measured three things the base task did not know:

1. **Decision 3 cannot run inside the base write set.** The base task holds every collector byte-identical, but nothing fetches `/.well-known/api-catalog`, and `run.targets` gives candidate legs only to `well_known` rows (part 1 RESULT §5.1). As written, part 2 would either break its own write set or freeze a composite with A13 uncollected.
2. **D1 is `error` by construction on large terms pages.** `runner.py` keeps 20,000 characters of a terms page; census.gov's is 302,319 bytes. A truncated read is a partial search, so Census ×4 and EIA ×3 D1 legs can never reach pass or fail (part 1 RESULT §1, §5.2). Freezing that composite would cite a verdict the collector made impossible.
3. **`tests/test_kg_questions.py:115` skips: "corpus epoch moved under the stored answers".** It skipped in part 1's gate and in task `422251c1`'s full gate, and did not skip in the 10-10 daily run, so part 1's publication of `_composite_c` moved the record under the stored answers. A freeze that leaves a check skipping on stale answers is not frozen.

## Decisions (amend the base task)

A. **Write set, collection, narrowly.** `run.py` and `runner.py` may change for exactly two things; every other line stays byte-identical, and the protected-paths script names these two files with a diff the RESULT quotes whole.
   - **A13 collection:** for each roster host and each verified API host, fetch `/.well-known/api-catalog`, read any `Link: rel="api-catalog"` header on the product page response already recorded in `scan_2026-10-06_recollect` (no re-fetch of product pages, per base decision 4), and fetch `/data.json` at the host root. Robots-first, the standing manners layer. The candidate legs reach `ind:A13` rows through `run.targets`, not only through `well_known` rows.
   - **D1 terms read:** the terms-page body is stored whole as visible text, up to a declared ceiling set in `params.yaml` and recorded on the cycle manifest (choose it from the largest terms page the seed table names, with headroom; quote the number and how you chose it). A page over the ceiling is `error` naming the ceiling, never a judgement on a prefix. Existing payloads stay byte-identical: the change applies to this cycle's collection only.
   - Each change gets a test that is red on the pre-change collector and green after, shown in the RESULT.

B. **The freeze includes the stored KG answers.** Regenerate the answers `tests/test_kg_questions.py` reads against `_composite_d`, by the script that owns them (name it), so the `:115` skip clears. The gate must show that test run, not skip. If regeneration changes an answer's substance, list each change in the RESULT; do not edit a question to make an answer fit.

C. **Not in scope, stated so it is not mistaken for an omission:** the A3 "body sniffs as HTML" check (link records are HEADs, there is no body; part 1 §5.2), and `adopt.py` declaring locations for adopter frames (part 1 §5.3). Both stay open.

D. **Commits.** Seldon's commit gate (HOOK-001) is a tracked pre-commit hook here. If it refuses a commit, quote its output whole and stop. Commit this addendum with the base task's first commit.

## Spend

The base estimate was 2M tokens. With A and B, read it as 3M, and as 2 to 4x low like every estimate in this queue.

## RESULT additions

Add to the base RESULT: the A13 fetch count per host and the A13 verdict counts per body; the D1 ceiling and the before/after D1 counts for Census and EIA; the KG-answer regeneration and its changes; the two collector diffs.
