# RESULT: the brief pack cites Seldon code at a pinned commit

**Task:** `cc_tasks/2026-10-10_brief_pack_cites_seldon_at_a_pinned_commit.md` (ResearchTask `5778a325`). No addendum exists (glob `2026-10-10_brief_pack_cites_seldon_at_a_pinned_commit_ADDENDUM*.md`: no match).
**Outcome:** done. `make gate-full` green (3206 passed, 4 skipped, 41 xfailed, 0 deselected, EXIT=0). The Seldon-shift check passed. No harness model call; no network beyond `git push`.

## 1. Premises

1. **Daily-run failure: confirmed, but the drift went the other way.** `logs/daily_suite/2026-10-10T083004Z.log` does end `1 failed, 3202 passed, 4 skipped, 41 xfailed`, `EXIT=2`, and the failure is `test_full_pack_regenerates_byte_for_byte_and_nothing_else_is_there`, `E_architecture.md drifted`. The task says the committed page cites `:834` and a regeneration gives `:788`. That is reversed. `git show HEAD:docs/brief/E_architecture.md` cites `seldon/seldon/core/dispatch.py:788` (written by `9720d796`, 2026-10-09 11:26). A regeneration on 10-10 gave `:834`. In the pytest diff, `-` is the regenerated text and `+` is the file on disk, which is likely why it was misread.
2. **Cause: confirmed for the mechanism. The commit named is wrong.** `sym()` called `line_of()` on `SELDON_REPO / "seldon/core/dispatch.py"`, an absolute path into Seldon's working tree, so the line was whatever that working tree held at render time. The line was not moved by the PA-001 or HOOK-001 merges. It was moved by Seldon `977d3f2` (SEL-005, 2026-10-09 16:37, "the standing dispatcher for seldon"), the only commit in `a11e041..2c76c65` that touches `seldon/core/dispatch.py`. `def candidacy` is at 788 in `977d3f2^` and at 834 in `977d3f2` and every later commit through `2c76c65`.
3. **Dispatcher tests skip under `LIVE_MODEL_CALLS`: confirmed.** The 10-10 log and this run both show `SKIPPED [1] tests/test_dispatch_config.py:275` and `:341` with "calls a real model; set LIVE_MODEL_CALLS=1 to run (seldon AD-036-R9 …)". I did not touch them.
4. **HOOK-001's pre-commit hook: confirmed.** `seldon verify` reports `Commit hook installed (.githooks)`. The commit for this task goes through it; see §5.
5. **Not stated in the task, found while reading:** `pyproject.toml` already pins `seldon` for a different purpose. It is the dependency this repository *imports* (bumped to `a11e041` and then `3500b54` on 10-09). I kept the citation pin separate on purpose (§3).

## 2. Every cross-repository citation the pack makes

I searched `SELDON_REPO`, `/Users/`, `Path.home`, `parents[2]`, `icsp` and `wintermute` in `scripts/build_brief_pack.py`, and searched backticked `seldon/…`, `../…` and `/Users…` spans across `docs/brief/`. Seldon is the only other repository the pack reads, and it reads one file:

| page | citation (before) | how it was produced |
|---|---|---|
| `E_architecture.md:81` | `` `seldon/seldon/core/dispatch.py:788` `` (box "standing dispatcher (seldon dispatch)") | `sym(SELDON_REPO/…/dispatch.py, "candidacy")`, read from the working tree |
| `INDEX.md:12` | `` `seldon/seldon/core/dispatch.py` `` (page E's source list, no line) | literal string in `page_e` |

No other page cites another repository. The fss-policy-kg, Wintermute and icsp checkouts are not referenced.

## 3. The change and the pin

- **Pin:** `SELDON_PIN = "2c76c65f562d1c584724e0daa436bf69357b6dc1"` in `scripts/build_brief_pack.py`. This is Seldon `main` on 2026-10-10, "models: lock bumped 2026-10-10". The constant is the only place the sha is named. Its comment cites both pieces of prior art (GitHub Docs permalinks; reproducible-builds.org "Definitions") and says why it is not the `pyproject.toml` pin: that pin names the code this repository imports, while this one names the code the brief describes, and the dispatcher runs from the Seldon checkout, not from the installed package. The module docstring says how to move it: edit `SELDON_PIN`, regenerate, and commit both together.
- **Generator:** `pinned_text(path, sha)` first checks `git -C SELDON_REPO cat-file -e <sha>^{commit}`. If the commit is missing it raises `SystemExit`, naming the sha and the checkout and suggesting a shallow clone or rewritten history as the cause. There is no fallback to the working tree (decision 4). It then returns `git show <sha>:<path>`. `SeldonFile(path)` wraps that so `line_of`/`sym` read it exactly as they read a local `Path`, and it renders as `seldon@<sha12>:<path>`. `page_e` uses `SeldonFile("seldon/core/dispatch.py")` for both the box and the source list. I added one sentence to page E's opening paragraph: "Code in the Seldon repository is read at the commit its citation names, not as it stands today."
- **Guards (decision 3), none relaxed:**
  - `test_every_cited_file_exists_and_every_line_is_inside_it` now matches `seldon@<sha12>:path[:line]` and checks existence and line range at the cited commit through `B.pinned_text`.
  - An unpinned `seldon/…` citation is now a failure, where before it would have read the working tree.
  - If the Seldon checkout is absent, the check still skips, as before.
  - PDFs are still checked for existence only.
- **New tests**, all red before the generator change:
  - `test_every_seldon_citation_names_the_pinned_commit`: every `seldon@` sha in the pack is `SELDON_PIN[:12]`.
  - `test_a_seldon_citation_is_read_at_the_pin_not_from_the_working_tree`: a scratch git repo with `def target` on line 3 at the commit and line 5 in the working tree must resolve to `:3`.
  - `test_a_pin_the_seldon_checkout_lacks_fails_naming_the_sha`: both `sym` and `pinned_text` raise `SystemExit` matching the missing sha.
- **Write set:** `scripts/build_brief_pack.py`, `tests/test_brief_pack.py`, `docs/brief/E_architecture.md`, `docs/brief/INDEX.md`, `scripts/check_protected_brief_pin.sh` (new), this RESULT, `seldon_events.jsonl`. `numbers.json` and the other 59 pack files are byte-identical.

## 4. Lines that moved on re-pinning

There is one cited line into Seldon, and it moved:

| box | before | after | at the pin |
|---|---|---|---|
| standing dispatcher (seldon dispatch) | `seldon/seldon/core/dispatch.py:788` | `seldon@2c76c65f562d:seldon/core/dispatch.py:834` | line 834 is `def candidacy(task_file: Path) -> dict:`, the dispatcher's candidacy test the box describes |

The INDEX source entry became `seldon@2c76c65f562d:seldon/core/dispatch.py`, with no line. No line inside this repository moved.

## 5. Gate output, Seldon-shift check, logs

| check | result | log |
|---|---|---|
| `make gate-full` (whole suite, `-n auto --dist loadgroup`) | `3206 passed, 4 skipped, 41 xfailed, 1697 warnings in 1296.51s (0:21:36)`, 0 failed, 0 deselected, `EXIT=0`. The 4 skips are `test_dispatch_config.py:275`, `:341` (LIVE_MODEL_CALLS), `test_scan_harness.py:290`, `test_g1_preservation.py:337`, the same four as the 10-10 daily run. 3206 = the daily run's 3202 passed + its 1 failure + 3 new tests. | `logs/suite.log` (the Makefile's own); the launcher wrapper is `logs/2026-10-10_brief_pin_gate_full.log` |
| `scripts/build_brief_pack.py --check` | `61 files checked, 0 drifted` | inside the protected log |
| Seldon-shift check: in `/Users/brock/GitHub/seldon`, `git switch -c scratch/brief-pin-shift`, inserted one comment line at the top of `seldon/core/dispatch.py` (`def candidacy` → line 835), committed `845768a`, then ran `tests/test_brief_pack.py` here | `31 passed in 11.63s`, `EXIT=0`. Afterwards I ran `git switch main` and `git branch -D scratch/brief-pin-shift` ("Deleted branch … (was 845768a)"). Seldon HEAD is back at `2c76c65f…`, `def candidacy` is back at 834, and the Seldon working tree is as I found it (` M state/prior_art_queries.jsonl`, `?? cc_tasks/2026-09-28_designnote_cites_citation.md`, both there before and not mine). The scratch commit was made with `-c core.hooksPath=/dev/null`: it was a throwaway on a branch I deleted, and running Seldon's commit gate on it would have written gate records for a commit that no longer exists. | `logs/2026-10-10_brief_pin_seldon_shift.log` |
| `seldon verify` | `All checks passed.`, `EXIT=0` | `logs/2026-10-10_brief_pin_seldon_verify.log` |
| protected paths (`scripts/check_protected_brief_pin.sh`) | `PROTECTED PATHS OK`, `EXIT=0` | `logs/2026-10-10_brief_pin_protected.log` |

`logs/` is gitignored; the paths are local to this checkout.

**What this does and does not close.** After this change a Seldon commit can no longer redden this repository's main through the brief pack. When the pin moves, it moves in a commit here, and that commit regenerates the pack. The pack still needs the Seldon checkout to contain `2c76c65f…`. If that history is rewritten, the build and the test stop and name the sha, which is decision 4's intended behaviour.
