# AR-002: squiddy's answer to items (2) and (5) of the worktree-admission filing: held bytes may live under a declared archive root, an absent held file is refused before a write, and the graph's ignore rules come from the kit

**Status:** proposed
**Author:** squiddy SQ-111's Claude Code session, 2026-11-05. This is the return (AD-036-R16) of the kit half of ai-readiness-kg's filing (`squiddy/cc_tasks/2026-11-03_consumer_filing_from_ai_readiness_kg_documents_admitted_in_a_dispatched_worktree_are_not_in_the_primary_after_merge.md`, AR-7; Issue `2b5a296d`), items (2) and (5), as SQ-109 measured them and SQ-111 built them. It follows AR-001, which carried the interim.
**Returns:** squiddy:SQ-111
**Repo:** ai-readiness-kg. L4: commit in ai-readiness-kg. No squiddy or seldon change.
**After:** c8fb9f62
**Governing:** squiddy DN-056 R-246 to R-250 (`/Users/brock/GitHub/squiddy/docs/design/2026-11-05_DN-056_held_bytes_live_under_a_declared_archive_root.md`); squiddy SQ-111's task file and RESULT; AR-001 and its RESULT. No new ruling here.
**Framework layer served (DN-005 §5 rule 1):** none (corpus plumbing under the validity layer).
**Model:** author
**Spend:** est. 0.25M tokens, Claude Code session included. Basis: one `squiddy init --check` and `--render` on one graph, one gate run, and one Issue line; AR-001 (two driver edits, a config edit and a verification pass) was estimated at 0.4M. Zero model calls.
**Parts:** A 0.50, B 0.30, C 0.20.
**Network:** none
**Exclusive:** no. It writes `graphs/ai-readiness/.gitignore` (and, under optional step 5, `graphs/ai-readiness/graph.yaml` and the configs `init --render` rewrites), and reads the rest.
**Touches:** graphs/ai-readiness/squiddy.pin, graphs/ai-readiness/.gitignore, graphs/ai-readiness/graph.yaml, graphs/ai-readiness/config.yaml, graphs/ai-readiness/.squiddy_init.json, graphs/ai-readiness/.env.example
**Premises:**
- premise: squiddy shipped the archive root and the held gate | check: `grep -q "def held_check" /Users/brock/GitHub/squiddy/squiddy/gates.py`
- premise: squiddy's init writes the graph ignore block | check: `test -f /Users/brock/GitHub/squiddy/squiddy/templates/graph.gitignore`
- premise: the kit graph's ignore file is the one SQ-019 wrote | check: `grep -q "intake/inbox/\*" graphs/ai-readiness/.gitignore`

Glob and read every sibling `*AR-002*ADDENDUM*.md`.

**The first two premises hold only once squiddy's dispatcher has merged SQ-111 to squiddy's `main`.** Until then this task is not runnable and registration refuses it (AD-038-R5, `premise_false`), which is the intended order. SQ-111 therefore committed this file unregistered; it is registered after the merge (SQ-111's RESULT carries the line).

## What changed in the kit (squiddy SQ-111, DN-056)

| your filing's item | what the kit does now | rule |
|---|---|---|
| (2) an ignored output lost when a worktree is removed, with the manifest still saying `acquired` | **An absent held file is a named refusal before every write.** `gates drift --when before` (the admission's stage 5, check-before) and `python -m squiddy.gates held --graph G [--mutate]` check every in-graph entry's `local_path` and `text_path`. An absent one prints `held-absent: <id> <field> <path>` and the gate exits 1. An absent fetch cache that acquire can fetch again (`acquisition: auto` with a `direct_download_url`) is listed as dropped, not refused. Measured read-only on 2026-11-05: your kit graph `graphs/ai-readiness` has 472 held references, 0 absent, so the gate passes on it today. | R-249 |
| (2) the kit and the consumer disagreed about the inbox | **`squiddy init` writes the graph's `.gitignore` from one template**, as a marked block (`# >>> squiddy-generated graph ignore rules (DN-056 R-250) >>>` ... `# <<<`). Lines outside the block are yours and are kept. `init --render` adds the block to a graph rendered before it; `init --check` reports it `missing` or `drifted`. The template ignores the inbox's bytes (`intake/inbox/*`, keeping `.gitkeep`), as your rules already did, and the kit repository's own rules now agree. | R-250 |
| (5) archive in iCloud `~/Documents`, symlinked in | **Declare an archive root instead of symlinking.** In `graphs/ai-readiness/graph.yaml`: `archive: {root: ~/Documents/kg-archive/ai-readiness}` (or `${SOME_VAR}/ai-readiness`), then `squiddy init --render`. A file under it is recorded as `archive:<relative path>`, never as this machine's path. Under a root, acquire writes fetched bytes to `<root>/oa/`, attached texts go to `<root>/texts/`, and an inbox may be declared `{source: inbox, dir: archive:inbox}`. The root must be outside the repository (your graph's own `archive/` directory, which holds the DN-049 export, is inside it and would be refused). | R-246, R-247 |
| (5) an evicted iCloud file was silent | **Eviction is its own state.** On this machine macOS evicts by leaving a dataless file (`SF_DATALESS`; 194,140 of the first 200,002 files under `~/Documents` on 2026-11-05), not a `.icloud` placeholder. The kit never reads an evicted file to check it (a read downloads it), so it is never a byte revision; the gate names it on every run, and refuses it only where the graph declares `manifest: {held_evicted: refuse}`. | R-248 |
| (5) a symlinked `texts/` recorded the target's absolute path; a directory link in the inbox was not walked; a link named `texts` was committed | Fixed: a path written through a link is recorded as the link's own graph-relative path; the inbox walks a directory link (a cycle ends); the template's patterns carry no trailing slash where a link may stand (`texts`, `work`). | R-247, R-250 |

**What did not change:** no recorded path was rewritten. Moving existing held files into an archive is a migration, its own task with a checkpoint plan, and none is proposed here. Your `kg.manifest` corpus (the dixie lanes `corpus/crosswalk`, `corpus/measurement_theory`, `state/docling_md`) is not the kit graph's held bytes, so the kit's gate does not see it.

## Which of AR-001's interim steps you may drop

| AR-001 interim step | now |
|---|---|
| 1. every gitignored output in the primary when the task ends (links or `$SELDON_PRIMARY_CHECKOUT`) | **Keep for your `kg.manifest` lanes.** For the kit graph's own admissions the kit now refuses a lost held file before the next write, so a loss can no longer be silent; the links remain how a worktree admission reads the primary's bytes at all. |
| 2. each admission RESULT lists the bytes in the primary and runs `kg.manifest verify` there | **Keep for `kg.manifest`.** For the kit graph, cite `python -m squiddy.gates held --graph graphs/ai-readiness` run in the primary instead of listing files by hand. |
| 3. no RESULT says a new document is in the MCP corpus layer | **Keep.** That is SQ-112's, not this task's. |
| 4. move no held bytes into `~/Documents` behind symlinks | **Drop the symlink plan; a declared archive root replaces it** (Part B, optional, and only for new held files). |

## Part A: take the kit's ignore block

0. Re-pin first. `graphs/ai-readiness/squiddy.pin` binds squiddy `b16ebb05` (tree `331126da`), which predates SQ-111, and stage 0 runs the pinned kit. Re-pin to the squiddy `main` commit that carries SQ-111 and has a kit pass recorded on main (`squiddy/kit/ledger/passes.jsonl`), by the procedure of your `cc_tasks/2026-10-28_repin_squiddy_to_b16ebb05_after_sq021s_rebase.md` (the pin's comment block says what moved and why). If no pass is recorded for such a commit yet, stop and say so; do not pin an untested kit.
1. In ai-readiness-kg, Claude Code window, run: `squiddy init graphs/ai-readiness --check`. Expect one new finding, `missing .gitignore` (no kit block), beside whatever it reported before this task; record the whole output.
2. Run `squiddy init graphs/ai-readiness --render`. It appends the kit block and keeps your lines. Read the diff of `graphs/ai-readiness/.gitignore`: your `texts/` and `work/` lines become redundant beside the block's `texts` and `work`; remove them or keep them, and say which.
3. Run `git check-ignore -v graphs/ai-readiness/intake/inbox/x.pdf graphs/ai-readiness/texts` and record that both are ignored, and that `graphs/ai-readiness/intake/inbox/.gitkeep` is not.

## Part B: the gate, in the primary

4. Run `python -m squiddy.gates held --graph graphs/ai-readiness --mutate --json <your evidence dir>/held.json` in the primary checkout. Expect `0 absent` and the positive control `FIRED`. If anything is absent, name it in the RESULT and restore it; do not retire an entry to pass the gate.
5. Optional, and only if the operator wants new hand-acquired files outside the repository now: add `archive: {root: ~/Documents/kg-archive/ai-readiness}` to `graphs/ai-readiness/graph.yaml`, create that directory, `init --render`, and declare a second inbox `{source: inbox, dir: archive:inbox}`. Existing entries keep their paths.

## Part C: the record

6. Add a line under Issue `2b5a296d` naming this return, squiddy SQ-111 and DN-056, and that items (2, kit half) and (5) are answered. Item (2)'s loss itself stays with seldon's filing (`seldon/cc_tasks/2026-11-04_consumer_filing_from_squiddy_a_merged_worktrees_removal_discards_gitignored_outputs_the_primary_does_not_hold.md`).

## Not to do

- No edit to squiddy or seldon. No `squiddy build` on `graphs/ai-readiness`; that is its own task under R-211.
- No migration of existing held files into an archive.
- Do not point the archive root inside the repository.
