# RESULT: re-pin squiddy from `933153d2` to `b16ebb05`

**Date executed:** 2026-11-02
**Task:** `cc_tasks/2026-10-28_repin_squiddy_to_b16ebb05_after_sq021s_rebase.md`
**Branch:** `worktree-eager-kindling-rainbow` (CC worktree; not merged/pushed/completed here — dispatcher does that).
**Recall used:** none (the eight recall hits are all re-judgement/burn RESULTs about the L0 scan; none touch the squiddy pin or kit sync, so none changed the approach).

## 0. Outcome

Done and committed on this branch. `graphs/ai-readiness/squiddy.pin` now pins
`b16ebb059106f144557b8805dbb0ad48e38eb283` (squiddy `squiddy/` package tree
`331126da25101d580fc646ea5c4e06613ba9b300`), replacing `933153d2…` (tree `21996226`). The gate
(`make gate-fast`, the correct tier — see §5) and `seldon verify` both ran to EXIT. Both exit
non-zero, and **neither non-zero exit is caused by the pin change**: every gate failure is a
gitignored corpus binary/rendering absent from this fresh CC worktree, and the one `seldon verify`
warning is a pre-existing blocked-task hygiene note about an unrelated task. The pin change touches
only `graphs/ai-readiness/squiddy.pin`; nothing it touches failed. Per step 3 I report and do not
patch.

## 1. Step 1 — confirm the current pin and the tag (with one premise correction)

- **Pin was `933153d2`** ✓. `graphs/ai-readiness/squiddy.pin` read `SQUIDDY_COMMIT=933153d2cb6acff437d5c16da3a2fd77c4147a98` before the edit (tree `219962268aa3…`, matching the file's own KIT PASS note). Not "already something else", so no stop.
- **Tag — premise refined, not a stop.** The task says the tag "names a tag resolving to it [933153d2]". Live:
  - `git -C /Users/brock/GitHub/squiddy tag -l 'sq021-gen1-*'` → `sq021-gen1-3d41fffa`
  - that tag resolves to `3d41fffabe9f9632f0917f8929649d38b5ed4285`, **not** `933153d2`.
  - `git -C /Users/brock/GitHub/squiddy merge-base --is-ancestor 933153d2 3d41fffa` → **933153d2 IS an ancestor of the tag.**
  So the superseded generation `933153d2` is kept reachable *through* the tag (as its ancestor), which is exactly the reason the pin's own comment and the task Why give for the tag's existence ("reachable only through the tag … which squiddy keeps for exactly this reason"). `3d41fff` is the SQ-021-branch commit that *recorded the pass* for `933153d2`; the tag points at it. The premise's wording ("resolving to it") is loose but its intent — the tag preserves `933153d2` — holds. Not a stop condition; recorded here per the "report discrepancies, never silently reconcile" rule.

## 2. Step 2 — set the pin, verify the synced kit, record the pass line

**Pin set.** `graphs/ai-readiness/squiddy.pin` → `SQUIDDY_COMMIT=b16ebb059106f144557b8805dbb0ad48e38eb283`, `SQUIDDY_VERSION=0.8.0` unchanged. The comment block was rewritten end-to-end (announced) because the old body described a *worktree-branch* pin (pass on branch `3d41fff`, "to be moved to the merge commit once SQ-021 lands") that the move makes false; the new body records the move, the tree change `21996226 → 331126da`, and the main-recorded pass. Diff: 21 insertions, 14 deletions, one file.

**Live verification of `b16ebb05` (read-only, against `/Users/brock/GitHub/squiddy`):**
- `b16ebb05` exists and is **on squiddy `main`** (`git branch --contains b16ebb05` lists `* main`).
- `git rev-parse b16ebb05:squiddy` = `331126da25101d580fc646ea5c4e06613ba9b300` — the `squiddy/` package tree the pin binds; matches `b16ebb05`'s own commit message ("tree 331126da").
- `b16ebb05`'s parent `bc345c0` carries the **same** `squiddy/` tree `331126da`; `b16ebb05` adds only the kit-pass ledger line. So the pinned kit code = `bc345c0`'s = `b16ebb05`'s.

**The synced kit's `kit/ledger/passes.jsonl` last line (step 2 deliverable).** Read at the pinned
commit with `git -C /Users/brock/GitHub/squiddy show b16ebb05:kit/ledger/passes.jsonl | tail -1`
(25 lines at that commit). Its last line is a `kit_suite_pass`:
- `"commit": "bc345c09f37069262d3b6200a57f7825ab46c049"`
- `"package_tree": "331126da25101d580fc646ea5c4e06613ba9b300"` (= the pinned tree)
- three clean-clone runs, seeds `2891785936, 2229681695, 1838392823`, each **2,355 passed, 3 skipped, 0 xfailed, 22 deselected, 0 failed, 0 errors**
- `"passed": true`, `run_id` `kit_record_pass_20261027T170137_12a3ad46`, recorded `2026-10-27T17:01:37Z`.

**It is a main line (R-237).** `bc345c0` (the pass's subject) is an ancestor of squiddy `main`
(`git merge-base --is-ancestor bc345c0 main` succeeds), and the pass line itself is present at the
main commit `b16ebb05`. Contrast the superseded pin: `933153d2`'s pass (2,232 passed) was recorded
on the SQ-021 branch `3d41fff`, not on main — which is the whole reason for the re-pin (DN-052 R-237
item 3).

**On "sync the way this repository syncs its kit" — grounded decision.** ai-readiness-kg keeps **no
local copy of the kit or its `passes.jsonl`**; the kit the graph builds against is the shared
checkout at `/Users/brock/GitHub/squiddy` (imported on the anaconda python's `sys.path`;
`scripts/jobs/airkg_extraction_burn.sh`). The two prior re-pins in this repo
(`6b200af0`, `401c2a6d`, both "SQ-021 Part D") changed **only** `graphs/ai-readiness/squiddy.pin`
and nothing else — there is no file-copy sync step in this repo. The only operational "sync" is
making the installed squiddy match the pin, i.e. `git -C /Users/brock/GitHub/squiddy checkout b16ebb05`.
**I deliberately did NOT run that**, because: (a) `/Users/brock/GitHub/squiddy` is a shared checkout
currently on `main` with many active worktrees — checking it out to `b16ebb05` would leave it in
detached HEAD and risk clobbering concurrent squiddy sessions, a side effect on a resource outside
this isolated worktree; and (b) this task runs no graph build, so the installed-kit HEAD does not
affect the task's gate. Instead I verified the pin target read-only (above), which is the
"synced kit" verification the deliverable asks for. For the record, the shared checkout's current
`main` HEAD (`d5a0e5cf`) carries `squiddy/` tree `ea7dac59…`, which has moved past the pinned tree
`331126da`; a future graph *build* against this pin will need `git -C /Users/brock/GitHub/squiddy
checkout b16ebb05` (or any commit carrying tree `331126da`) so `governed/check_pin.py`'s
`kit_matches` holds — done by the session that builds, not by this pin-only task.

## 3. Premises the task file got right / wrong

- Right: pin was `933153d2`; `b16ebb05` is the merged main tip carrying the SQ-021 work with a
  pass on main; `sq021-gen1-*` tag exists and preserves the superseded generation.
- Refined (§1): the tag resolves to `3d41fffa`, with `933153d2` as its ancestor — not a tag that
  literally resolves to `933153d2`. Intent preserved; no stop.
- Right: "the same work" — note the `squiddy/` **tree differs** across the re-pin
  (`21996226 → 331126da`); "same work" means the rebased/merged SQ-021 content, not a byte-identical
  tree. Expected and within scope (re-pin to the merged tip).

## 4. Steps 3 & 4

- Step 3: suite + `seldon verify` run — see §5. No patching (forbidden by the task and out of scope).
- Step 4: commit on this branch only. **Not** pushed/merged, and `seldon cc complete` **not** run —
  the dispatcher owns rebase/merge/complete for a worktree session. `seldon dispatch part-complete`
  run from here (Parts: A 1.0).

## 5. Gate, verify, protected-paths (logs cited; EXIT lines reached)

**Gate tier = `make gate-fast`.** Write set is `graphs/ai-readiness/squiddy.pin` + this RESULT; it
touches nothing under `assessment/harness/scan/rules/`, `collectors/`, `runner.py`, `run.py`,
`manners.py`, `rederive.py`, `scripts/score.py`, or the framework record — so `gate-fast` is the
task's gate (CLAUDE.md "Suite tiers").

**`make gate-fast`** — `logs/gate-fast.log`, ran to `EXIT=2`. Final summary line verbatim:

> `18 failed, 3382 passed, 50 skipped, 41 xfailed, 1686 warnings, 1 error in 247.65s (0:04:07)`

(Command: `pytest tests/ assessment/ -n auto --dist loadgroup -q -rs -m "not slow"`. Under `-q` with
xdist pytest printed no `collected/deselected` line; `-m "not slow"` deselects the slow tier that
`gate-fast` intentionally excludes, so the deselected count is not in the log. 41 xfailed, 50
skipped are printed as above.)

**Every one of the 18 failures + 1 error is a gitignored corpus binary/rendering absent from this
fresh worktree** (the dispatch note's "Gitignored files are not in this worktree unless linked").
Representative root causes from `logs/gate-fast.log`:
- setup error `test_full_pack_regenerates_…`: `FATAL: corpus/crosswalk/usafacts-ai-ready-data-guide.pdf … is not on disk; the corpus binaries are gitignored`.
- `test_every_technique_source_document_is_a_file_this_repository_holds`, requirements-table tests, `test_graph_free_pages_regenerate_byte_for_byte`, `test_claims_file_regenerates_byte_for_byte`, etc.: `… is not on disk` / `FileNotFoundError` on `corpus/pilot/*.pdf`, `corpus/kernel/*.md`, `corpus/crosswalk/*`, `corpus/bulk/*.pdf`.

Proof these are not the pin change: (1) the write set is one line in `squiddy.pin`; (2)
`grep -rln "squiddy\|squiddy.pin\|SQUIDDY_COMMIT" tests/ assessment/` hits only
`test_sq022b_slots.py`, `test_sq022_corpus_layer.py`, `test_replay_selection.py`, **none of which
are in the failure list and none of which read the pin's commit value**; (3) `corpus/` here holds
3,901 tracked files but the gitignored binaries (`corpus/bulk/`, `pilot/`, `kernel/`, `crosswalk/`
PDFs/renderings) are absent by `.gitignore` design — the identical failures occur on clean HEAD in a
bare worktree because the missing files are independent of the pin's content.

**`seldon verify`** — `logs/seldon-verify.log`, ran to `EXIT=1` with **1 warning**. The only
non-pass item:

> `⚠ Blocks and waits — 1 finding(s): 98ed1dd1 is blocked with no reason recorded`

This is a pre-existing hygiene warning about unrelated task `98ed1dd1` (a `--reason` was never
recorded on its blocked state); the pin change neither created nor touches it. All other checks ✓,
including `✓ File hashes — All 2 tracked files in sync`, `✓ Event log — 50783 events readable`, and
`✓ Pass ledger — no pass_ledger declared; skipping (squiddy DN-052 R-237)`.

**Protected-paths diff** (this worktree; `git status --porcelain` + `git diff --stat`):

> ` M graphs/ai-readiness/squiddy.pin`
> `1 file changed, 21 insertions(+), 14 deletions(-)`

Exactly the declared write set (plus this RESULT, added at commit; `logs/` is gitignored). No stored
payload, event shard, rule module, matrix, report, or framework record moved.

## 6. Where the numbers can be re-read

- `logs/gate-fast.log` — full `make gate-fast` run, summary line and every traceback, `EXIT=2`.
- `logs/seldon-verify.log` — full `seldon verify`, the one warning, `EXIT=1`.
- `graphs/ai-readiness/squiddy.pin` — the new pin and its provenance comment.
- squiddy `kit/ledger/passes.jsonl` @ `b16ebb05` (read via `git -C /Users/brock/GitHub/squiddy show b16ebb05:kit/ledger/passes.jsonl`) — the recorded pass line quoted in §2.
