# RESULT: rematerialize worktree admissions in the primary, and file why they went missing

**Task:** `cc_tasks/2026-11-03_rematerialize_worktree_admissions_in_primary.md` (c1662a22)
**Executed:** 2026-11-03, dispatched headless session in worktree `elegant-knitting-pond`.
**Outcome:** Part A — **3 of 4** documents restored into the primary; ISO stopped at re-fetch (HTTP 403), manifest untouched, both hashes recorded. Part B — Issue `2b5a296d` filed. Gate green after worktree corpus seeding; `seldon verify` returns 1 on one pre-existing unrelated warning; protected-paths diff empty.

**Recall used:** none. (The eight recall hits are prior admission/projection RESULTs; the task file, the two admission scripts, and the `airkg-worktree-gate-seeding` memory were sufficient. None of the listed hits changed the approach.)

---

## §1 — Part A quotes first (step 4 and step 5)

### Step 4 — listings in the primary (`/Users/brock/GitHub/ai-readiness-kg`)

`ls corpus/crosswalk | grep usafacts`:
```
usafacts-ai-ready-data-guide.pdf
usafacts-ai-ready-framework-deck-2026-08.pdf        <- restored (this task)
usafacts-ai-ready-framework-overview-2026.pdf       <- restored (this task)
usafacts-fde-standards-detailed.pdf
usafacts-fde-standards-quick-reference.pdf
```

ISO and GQM canonical paths:
```
corpus/crosswalk/basili-caldiera-rombach-1994-gqm.md   -> present, 19726 bytes (restored, this task)
corpus/crosswalk/iso-iec-ieee-15939-2017.md            -> ABSENT (ISO stopped on 403; see step 3)
```

`ls state/docling_md | grep -i -E 'iso-iec|basili|usafacts'` (`.md` only):
```
basili-caldiera-rombach-1994-gqm.md                 <- restored
usafacts-ai-ready-data-guide.md
usafacts-ai-ready-framework-deck-2026-08.md         <- restored
usafacts-ai-ready-framework-overview-2026.md        <- restored
usafacts-fde-standards-detailed.md
usafacts-fde-standards-quick-reference.md
```
**6 `.md`, not the expected 7.** The one missing is `iso-iec-ieee-15939-2017.md`, because ISO's canonical source could not be restored (403, step 3). Each restored `.md` has its `.meta.json` beside it.

### Step 5 — grounding spot-check in the primary's deck markdown
`state/docling_md/usafacts-ai-ready-framework-deck-2026-08.md` (11,444 chars), via `kg.extraction.grounding.is_grounded`:
```
HIT  | Three tracks, three levels within each track
HIT  | Modeled on SLSA
MISS | Crawlable data
HIT  | Lineage/change notes
HIT  | Published methodology documentation
HIT  | Provenance and update cadence
HIT  | Clearly licensed
```
6 of 7 HIT. **`Crawlable data` MISS** is a property of the deck/docling render, not a restoration defect: the deck PDF is byte-identical to admission (sha256 `9cbe6ae3…`), and docling of it reads `agents can crawl` / `crawl, walk, run` (lines 427, 437, 443) but not the literal string `Crawlable data`. Reported, not reconciled: DN-020's quote of `Crawlable data` is not verbatim-present in this deck's markdown.

---

## §2 — Part A execution record

Primary checkout confirmed: `echo $SELDON_PRIMARY_CHECKOUT` → `/Users/brock/GitHub/ai-readiness-kg`; the `check` passes (`ok`).

**USAFacts deck & overview (step 2a).** Copied from `corpus/staging/inbox/` to the primary's canonical crosswalk paths; sha256 verified equal to the manifest:
| doc_id | dest | sha256 | result |
|---|---|---|---|
| usafacts-ai-ready-framework-deck-2026-08 | corpus/crosswalk/…deck-2026-08.pdf | `9cbe6ae32203…bfbb0b` | OK |
| usafacts-ai-ready-framework-overview-2026 | corpus/crosswalk/…overview-2026.pdf | `e47c5bc63d3c…7d7876fc` | OK |

**GQM (step 2b).** Re-fetched through `scripts/fetch_allowlisted.py` (allowlist `www.iso.org, www.cs.umd.edu` from the dispatcher) into `corpus/measurement_theory/gqm.pdf`. Re-fetched capture sha256 `afcfc464b299…0083f` = the recorded capture sha256 (byte-identical). The canonical markdown was reproduced exactly as the 2026-11-02 admission produced it — the admission header reconstructed with the **original** `retrieved_at` (`2026-11-02T16:03:06.239336+00:00`) and capture sha256, then `admit_measurement_theory_sources.docling_markdown` over the capture (188 docling lines, 19381 chars) — giving `md_sha256 = f8db1b69d78f…c79dee`, **equal to the manifest**. Written to `corpus/crosswalk/basili-caldiera-rombach-1994-gqm.md` (read-back sha256 matches).

**ISO (step 2b) — STOPPED, manifest untouched.** `www.iso.org/standard/71197.html` returned **HTTP 403** to the allowlisted client today (it was 200 on 2026-11-02). Per the task ("if a re-fetch returns different bytes … do not overwrite the manifest: record both hashes and stop"):
- recorded capture sha256 (2026-11-02): `d155ffb5cfab…dddef`
- today: HTTP 403, response-body sha256 `838d4fca71e3…025c27` (5597 bytes)

The manifest was not overwritten and no file was written. ISO remains an `included`+`verified` manifest entry with no on-disk bytes in the primary — a live instance of the defect Part B files.

**Conversion (step 3).** `scripts/t1_build_index.py --phase convert`, pointed at the primary, produced the `state/docling_md/` renders. Line/char counts and converter:
| doc_id | state/docling_md/*.md | converted_by | fidelity |
|---|---|---|---|
| usafacts-ai-ready-framework-deck-2026-08 | 764 lines, 11,444 chars | docling | layout_aware |
| usafacts-ai-ready-framework-overview-2026 | 16 lines, 2,713 chars | docling | layout_aware |
| basili-caldiera-rombach-1994-gqm | 189 lines, 19,725 chars | passthrough | layout_aware |
| iso-iec-ieee-15939-2017 | — | — (MISSING: source absent) | — |

The convert run reported `96 converted, 194 cached, 1 failed (622s)` — the `1 failed` is ISO (`[130] MISSING iso-iec-ieee-15939-2017`). **Observed, strengthening Part B:** the primary's docling cache was broadly incomplete — 96 renders (not just the 3 restored here) were missing from the primary and regenerated by this convert. The same worktree-merge loss that dropped these four has been dropping gitignored renders at scale.

**Step 6 — no tracked change from the restores.** `git status --porcelain` in the primary cannot be run from this worktree (Claude Code refuses git aimed at the primary). The intent — that every restored output is gitignored and produces no tracked change — is shown instead with `git check-ignore -v` against the shared ignore rules:
```
.gitignore:54  corpus/crosswalk/   -> …deck-2026-08.pdf, …overview-2026.pdf, …gqm.md, …iso…md
.gitignore:60  corpus/measurement_theory/ -> gqm.pdf
.gitignore:125 state/docling_md/   -> …deck…md, …gqm.md  (and the rest)
```
All restored paths are ignored; writing them into the primary leaves its tracked tree unchanged.

---

## §3 — Part B: the cause, filed

Issue **`2b5a296d-d8c3-492e-beb2-1de80fec1464`** created (`seldon issue create`, type `structural_flow`, importance **high**, urgency **medium**, detection `audit`, target `code`), titled *"admissions in dispatched worktrees lose their gitignored corpus outputs at merge"*. Body (full text in `logs/issue_body.txt`) records the four doc_ids, the evidence above, and:

**What integrity-checks the on-disk file, and why it did not fire in the primary.**
`kg.manifest.verify` (**`kg/manifest.py:645-668`**) re-hashes every manifest entry's `local_path`: it flags `missing` when `path.is_file()` is false (line 654) and `hash_mismatch` when `_sha256(path) != entry["content_hash"]` (lines 659-660). `scripts/check_protected_cited_metadata.sh:13` names it as the mechanism by which gitignored binaries' bytes are asserted. **But it is never run against the real corpus on any green path:**
- `make gate-fast` = `pytest tests/ assessment/ -m "not slow"` (`Makefile:33-34`). Its only suite caller, `tests/test_manifest.py:297-314`, exercises `verify()` against the **tmp `repo` fixture** (a synthetic corpus), never the real `corpus/`. It tests the logic, not the corpus state.
- `make gate-full` (daily) is the same collection; it adds no corpus re-hash.
- `seldon verify` checks the Seldon artifact graph, not corpus files.
- The admission-time dixie integrity checks (magic_bytes / size_sanity / content_smoke) run once in the worktree Sweep and are stored as a **snapshot** in `corpus/manifest.json`; nothing re-reads the on-disk file at gate time.

So after a worktree merge, `manifest.json` asserts `included`+`verified` for documents whose gitignored bytes are absent from the primary, and gate-fast, `seldon verify`, and the protected-paths diff all stay green. The assertion the design relies on is written but unwired.

**Two candidate fixes (NOT implemented, for a design note to choose between):**
(a) admission drivers write their gitignored outputs to `$SELDON_PRIMARY_CHECKOUT`, as this task did by hand; or
(b) the dispatcher copies a task's declared gitignored outputs back to the primary before it removes the worktree.

---

## §4 — premises the task file got right / corrections

- The task's premise (four docs' bytes absent from the primary; manifests/events merged) is **confirmed** exactly.
- The task framed the ISO risk as "a re-fetch returns different bytes." Reality was stronger: **403, no bytes at all.** Handled under the same stop-and-record rule.
- The task expected `7` `.md` in `state/docling_md`; actual is `6` because ISO was stopped. Not a defect — the direct consequence of the ISO 403.
- Undocumented in the task but found during execution: the primary's docling cache was missing ~96 renders, not 4. The convert step healed them; the Issue notes the scale.

## §5 — what this task did NOT do (boundaries honored)
Did not overwrite the ISO manifest entry or fabricate ISO bytes. Did not implement either candidate fix. Did not alter any other task's state (the `seldon verify` warning on `98ed1dd1` is pre-existing and left as-is). Did not touch the protected paths. Did not merge, push, or run `seldon cc complete` (dispatcher's job).

## §6 — verification (logs on disk; `logs/` is gitignored)

- **Gate tier: `make gate-fast`** (write set touches no scan/scoring/record code). Two runs:
  - First, unseeded worktree: `logs/gate_fast.log` — `16 failed, 3384 passed, 50 skipped, 41 xfailed, 1 error in 228.01s`, EXIT=1. **Every failure/error is a gitignored corpus binary absent from the fresh worktree** (e.g. `corpus/crosswalk/usafacts-ai-ready-data-guide.pdf`, `corpus/pilot/aidrin-hiniduma-2024.pdf`), not a defect in this task's changes — the `airkg-worktree-gate-seeding` condition.
  - After copy-seeding the worktree's gitignored `corpus/` and `state/` from the primary (additive, 2686 files / 973.9 MB, never overwriting a tracked file; `logs/seed_worktree.py`): `logs/gate_fast_seeded.log` — **`3443 passed, 8 skipped, 41 xfailed, 0 deselected, 0 failed in 232.54s`, EXIT=0.** The 8 skips are environment-only (`seldon checkout not beside this repo`, a dev-proposition skip), not corpus-missing.
- **`seldon verify`:** `logs/seldon_verify.log`, **EXIT=1**. Every substantive check is `✓` (event log 50882 events, precedence 76 edges acyclic, 222 task source files resolve, prior-art notes pass, commit hook installed, tracked dirs present). The sole finding is one pre-existing **warning**: `⚠ Blocks and waits — 98ed1dd1 is blocked with no reason recorded`. `98ed1dd1` is a different, pre-existing task (this task is `c1662a22`); not this task's to fix. Replay was skipped (expensive).
- **Protected-paths diff** on `framework/ai_readiness_framework.json`, `kg/schema.yaml`, `docs/schema_v0.1.md`, `docs/data/ai_readiness_framework.json`: `git diff --stat HEAD --` returned **empty** (exit 0), and `git status --porcelain --` on the four is empty. As expected.

Fetch log: `logs/2026-11-03_rematerialize_fetch.jsonl` (GQM 200 / ISO 403). Issue body: `logs/issue_body.txt`.
