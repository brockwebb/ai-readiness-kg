# RESULT: AR-001 — link the corpus dirs, make the drivers refuse a lost write, verify in the primary

**Task:** `cc_tasks/2026-11-04_AR-001_worktree_admissions_answered_by_squiddy_link_the_corpus_dirs_write_to_the_primary_and_verify_there.md`
**Executed:** 2026-11-04, dispatched headless session in worktree `scalable-wobbling-cascade`.
**Outcome:** Parts A, B, C delivered, with two premise corrections that changed the shape of Part A.
Part B (the driver guard) is complete and green (9 new tests pass). Part A (dispatch.worktree_links)
is added but **narrowed** from the task's broad set, and needed a companion change to `kg.manifest.add`
to work at all. The per-task gate (`make gate-fast`) is **RED on 4 failures, all pre-existing
brief-pack / evidence-map regeneration drift** that my changes do not touch and that the AR-001
crosswalk link merely *exposed*; no failure is attributable to this task's code. `seldon verify`
returns 1 on the same pre-existing `98ed1dd1` warning the prior task left as-is; protected-paths diff
is empty.

**Recall used:** `2026-11-03_rematerialize_worktree_admissions_in_primary_RESULT` (its §3 named the two
candidate fixes — drivers write to the primary, or the dispatcher copies back — and documented the
seeding practice, `$SELDON_PRIMARY_CHECKOUT`, and that `kg.manifest verify` is unwired on the real
corpus; this shaped Part B and the gate approach), `issue-2b5a296d` (the Issue this return annotates,
Part C). The other six hits were context and did not change the approach.

---

## §1 — Premises the task file got wrong (the two that mattered)

**P1 — "link the gitignored lanes" is NOT transparent to the admission code.** `kg.manifest.add`
(`kg/manifest.py:390,394`) resolves symlinks (`Path(filepath).resolve()`) before checking the file is
under `corpus/` (`_CORPUS_DIR.resolve()` = the *worktree's* corpus). A file written through a
dispatcher-symlinked lane resolves out to `<primary>/corpus/…`, which is **not** under the worktree's
corpus, so `manifest.add` raises `file is not under corpus/`. This breaks (a) the existing test
`test_scan_harness_v3.py::test_a_scan_surface_is_not_gapped_for_being_thin`, which writes a fixture
into a symlinked `corpus/scan`, and (b) — by the identical code path — **the admission drivers Part A
exists to support**. Both of the task's two interim routes (link, or write directly under
`$SELDON_PRIMARY_CHECKOUT`) hit this, because the local check is anchored on the worktree's corpus.
**Correction:** `kg.manifest.add` was made primary-aware — a resolved path under
`$SELDON_PRIMARY_CHECKOUT/corpus` is accepted as a known corpus tree, and the stored `local_path`
stays corpus-root-relative and portable. When `$SELDON_PRIMARY_CHECKOUT` is unset (every
non-dispatched run, and every existing test) the branch is inert and the strict check is unchanged
(`tests/test_manifest.py::test_reject_file_not_under_corpus` still red-refuses).

**P2 — the lane set must NOT be "every corpus lane the seeding copies."** A lane is safe to symlink
only if the gate never *writes* into it: a symlinked lane IS the primary's directory, so a test (or
driver) that writes there mutates the primary, and (per P1) a write through a linked lane escapes to
the primary's corpus. `corpus/scan` is written by the scan-harness tests; `corpus/staging` holds
tracked files. Linking the broad set made the first gate run fail on exactly these (see §4). **The set
is narrowed** to the lanes that are (a) the drivers' write target / read source and (b) read-only to
the gate: `corpus/crosswalk`, `corpus/measurement_theory`, `state/docling_md` (plus `.env`). The
copy-seed can stop for *these three*; the rest still rely on the session seed.

A smaller note the task premised: the task's own instruction 3 ("a RESULT never says a newly admitted
document is in the MCP corpus layer") did not apply — this task admits nothing.

---

## §2 — What was done

**Part A — `seldon.yaml` `dispatch.worktree_links`** (narrowed, see §1 P2):
```
worktree_links: [.env, corpus/crosswalk, corpus/measurement_theory, state/docling_md]
```
Resolved value confirmed through seldon's own loader (`_load_parallel_config`): parses clean.
`seldon dispatch status` runs without a `DispatchConfigError`. Linking the three lanes via seldon's own
`worktree.link` produced live symlinks into the primary (`corpus/crosswalk` → 29 files visible through
the link), i.e. the gate reads the real bytes with no copy. The TRADE (Part A.3) is recorded in the
config comment: a session writes into the primary through a link before its merge, so a mid-admission
failure can leave content-addressed bytes the manifest does not name; they are inert until a presence
check lands (squiddy SQ-111 / the seldon answer, both filed).

**Companion — `kg/manifest.py`** (required by §1 P1): `add()` accepts a file whose resolved path is
under `$SELDON_PRIMARY_CHECKOUT/corpus` (a linked lane), and derives the portable `local_path` from the
primary's corpus in that case. Additive; the symlink-escape guard still refuses a path outside any
corpus.

**Part B — the driver guard** (`scripts/worktree_primary.py`, new): `assert_outputs_in_primary(repo,
outputs)` refuses, before any write, if an output's resolved path is not durable in the primary —
either not inside `$SELDON_PRIMARY_CHECKOUT` at all, or still inside this worktree (which the merge
discards). Called before the first side effect (before even `mkdir`) in both
`scripts/admit_measurement_theory_sources.py` and `scripts/admit_usafacts_three_track.py`.

**Part C — Issue `2b5a296d`**: a return line added via `seldon issue update`, naming the three owners
(seldon for the merge-removal loss; squiddy SQ-111 for its admission path + presence refusal;
ai-readiness-kg for the interim Parts A+B). **Left open** — the links are not "in force" until the
dispatcher merges and relaunches under the new config, and the crosswalk link exposes the pre-existing
drift in §3 that must be regenerated first.

---

## §3 — The gate is red on PRE-EXISTING drift, not this task (the blocking finding)

`make gate-fast`, seeded worktree + the three lanes linked: **4 failed, 3448 passed, 8 skipped, 41
xfailed, 0 deselected in 209.38s, EXIT=2** (`logs/gate_fast2.log`). All four failures are
regeneration-drift in generated products this task does not touch:

| test | file | drift |
|---|---|---|
| `test_graph_free_pages_regenerate_byte_for_byte` | `tests/test_brief_pack.py` | `docs/brief/B_usafacts_delta.md` |
| `test_full_pack_regenerates_byte_for_byte_and_nothing_else_is_there` | `tests/test_brief_pack.py` | same |
| `test_every_page_names_its_generator_record_commit_and_cycle` | `tests/test_brief_pack.py` | same pack |
| `test_claims_file_regenerates_byte_for_byte` | `tests/test_evidence_map.py` | `docs/evidence/claims.yaml` |

**Evidence it is pre-existing and unrelated to my changes:**
- `docs/brief/` is **clean/committed** (`git status --porcelain docs/brief/` empty). `git show
  HEAD:docs/brief/B_usafacts_delta.md` embeds `at commit 37b3b82ae3de`.
- The record's current last-touching commit is **`b5c940ce`** (`git log -1 -- framework/ai_readiness_framework.json`),
  and a fresh re-render (`build_brief_pack.render(None)`, run standalone) embeds `b5c940ce`.
- So the committed packs are **stale**: commit `b5c940ce` ("re-parent the sixteen checks … rebuild
  roll-up + one-pager") updated the record but did **not** regenerate `B_usafacts_delta.md` or
  `docs/evidence/claims.yaml`. `37b3b82ae3de` is the *previous* record commit.
- My write set (`scripts/worktree_primary.py`, the two driver guard calls, `kg/manifest.py`,
  `seldon.yaml`, the two test files) touches none of: the framework record, `docs/brief/`,
  `docs/evidence/claims.yaml`, `scripts/build_brief_pack.py`, `scripts/build_evidence_map.py`. The
  re-render is byte-identical with or without my changes.

**Why it surfaced now:** these tests read corpus binaries (e.g. `corpus/crosswalk/usafacts-ai-ready-data-guide.pdf`).
In an unseeded worktree they error/skip on the missing file, which is how the drift slipped past
`b5c940ce`'s own gate. The AR-001 crosswalk link (and the session seed) finally provide those bytes, so
the tests run and catch the pre-existing drift. **This is correct behaviour exposing a real defect, not
a regression.**

**Not fixed here (one gate per task; out of AR-001's scope):** regenerating `B_usafacts_delta.md` and
`docs/evidence/claims.yaml` from the current record is the sanctioned fix (the tests say "re-run the
generator"), but it belongs to whoever owns the `b5c940ce` / DN-020 record change, needs the graph for
the full pack, and mixing a multi-file regeneration of another task's product into this diff would
muddy the record. **Recommended follow-up:** a regeneration task that re-runs `build_brief_pack.py` and
`build_evidence_map.py` over `HEAD` and commits the refreshed products; this is what unblocks the gate
for AR-001's merge.

---

## §4 — Part B written test-first; the broad-link diagnostic

Part B's tests were written and run RED before the drivers were wired (guard absent →
`test_driver_imports_and_calls_guard_before_writing` and the real-driver subprocess refusal failed),
then GREEN after wiring. Final: `tests/test_worktree_primary_guard.py` (8) +
`tests/test_manifest.py::test_accepts_file_reached_through_a_linked_lane` (1) all pass. The guard tests
build a REAL git worktree nested under the primary and exercise the exact loss condition (no link →
refuse by name; linked lane → resolves into the primary → pass; direct primary run → pass). The
real-driver subprocess test runs each admission driver under the anaconda interpreter with
`$SELDON_PRIMARY_CHECKOUT` pointed at an empty tree and asserts it refuses before any write (skips when
docling/dixie are unimportable, as in a pure gate-fast env).

The FIRST gate run used the task's broad link set (all gitignored corpus lanes): **7 failed**
(`logs/gate_fast.log`) — `corpus/scan` write (P1/P2), and `state/t2_priority.json` /
`corpus/staging/proposed_schema/…` absent because linking document lanes does not cover the gate's
long tail of gitignored content. Narrowing the set (§1 P2) + seeding the rest removed those 3
failures and the scan failure; the remaining 4 are the §3 pre-existing drift.

---

## §5 — Gate tier and boundaries

- **Tier: `make gate-fast`.** The write set touches nothing under `assessment/harness/scan/rules/`,
  `collectors/`, `runner.py`, `run.py`, `manners.py`, `rederive.py`, `scripts/score.py`, or the
  framework record, so gate-fast (not gate-task) is the correct per-task gate.
- Did NOT edit squiddy or seldon. Did NOT run `squiddy build` on `graphs/ai-readiness`. Did NOT
  rematerialize ISO 15939. Did NOT move any threshold. Did NOT regenerate the stale brief-pack /
  evidence-map (reported as §3 follow-up). Did NOT merge, push, or run `seldon cc complete`
  (dispatcher's job). Ran `seldon dispatch part-complete`.
- The manual lane symlinks and the ~917 MB session seed are local verification artifacts under
  gitignored paths; only the six source files are committed. The three lane symlinks show as untracked
  in plain `git status` (the `dir/` ignore patterns do not match a symlink-as-file); seldon's
  clean-tree check treats them as clean (`_clean_link` / `_ignored_as_directory`).

---

## §6 — Verification (logs on disk; `logs/` is gitignored)

- **`make gate-fast`** (seeded + 3 lanes linked): `logs/gate_fast2.log` — **4 failed, 3448 passed, 8
  skipped, 41 xfailed, 0 deselected in 209.38s, EXIT=2.** All 4 failures are §3 pre-existing drift; all
  9 new tests pass. The broad-link diagnostic run is `logs/gate_fast.log` (7 failed, 3435 passed, 17
  skipped, 41 xfailed).
- **`seldon verify`**: `logs/seldon_verify.log` — **EXIT=1**, sole finding the pre-existing warning
  `⚠ 98ed1dd1 is blocked with no reason recorded` (a different, pre-existing task; the same warning the
  2026-11-03 RESULT left as-is). Every substantive check ✓ (event log 50,914 events, precedence 78
  edges acyclic, 224 task source files resolve, prior-art 7 notes pass, commit hook installed, tracked
  dirs present). Replay skipped (expensive).
- **Protected-paths diff** on `framework/ai_readiness_framework.json`, `kg/schema.yaml`,
  `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json`: `git diff --stat HEAD --` **empty**
  (exit 0).
- **Focused**: `tests/test_worktree_primary_guard.py` + `tests/test_manifest.py` — **50 passed**.
