#!/usr/bin/env python3
"""Guard: an admission driver's gitignored outputs must land in the PRIMARY checkout.

AR-001 (`cc_tasks/2026-11-04_AR-001_worktree_admissions_answered_by_squiddy_link_the_corpus_dirs_write_to_the_primary_and_verify_there.md`;
squiddy SQ-109; Issue `2b5a296d`). A dispatched session runs in a git worktree the Claude Code
CLI creates under `.claude/worktrees/<name>`. Corpus outputs — `corpus/crosswalk/*`,
`state/docling_md/*`, the rest of the gitignored corpus lanes — are gitignored, so a merge does
not carry them and `git worktree remove` discards them. An admission that wrote its bytes into
the worktree's own `corpus/crosswalk/` therefore leaves `corpus/manifest.json` (tracked, merged)
asserting `included`+`verified` for a document whose bytes are gone from the primary. That is the
loss squiddy reproduced without the dispatcher and the primary had no presence check to catch.

The interim fix (AR-001 Part A) is `dispatch.worktree_links` in `seldon.yaml`: the dispatcher
symlinks the gitignored corpus lanes from the primary into each worktree before the session runs
(`seldon/core/worktree.py::link`), so a write to `corpus/crosswalk/x.pdf` in the worktree lands in
the primary THROUGH the symlink and survives the merge. This module is the driver's own refusal
for when that link is absent: before any write, `assert_outputs_in_primary` resolves each output's
symlinks and refuses by name if the output would land inside the worktree (and so be discarded at
merge) rather than in the primary. Fail loud and early (engineering standards §4), never write then
discover.

Pure stdlib so the gate-fast suite can exercise it without the anaconda deps the drivers need.
"""
from __future__ import annotations

import os
from pathlib import Path


class OutputNotInPrimary(SystemExit):
    """A planned admission output would not be durable in the primary checkout. A non-zero
    ``SystemExit`` so a driver's ``raise`` exits with the diagnostic and code 1."""


def primary_checkout(repo: Path) -> Path:
    """The durable checkout every gitignored output must reach.

    ``$SELDON_PRIMARY_CHECKOUT`` when a dispatched worktree session set it (the dispatcher exports
    the primary's absolute path to every launched session); otherwise ``repo`` itself, which is the
    primary when a driver is run by hand there.
    """
    env = os.environ.get("SELDON_PRIMARY_CHECKOUT")
    return Path(env).resolve() if env else Path(repo).resolve()


def assert_outputs_in_primary(repo: Path, outputs) -> Path:
    """Refuse unless every output, with its symlinks resolved, is durable in the primary checkout.

    ``repo`` is the checkout the driver is running in (``Path(__file__).resolve().parents[1]``).
    ``outputs`` is every path the driver is about to WRITE (its destination files), not the paths
    it reads.

    Durable means the resolved path is inside the primary checkout AND — when ``repo`` is a worktree
    distinct from the primary — is NOT still inside that worktree. The CLI's worktrees live under
    ``<primary>/.claude/worktrees/<name>``, so "inside the primary" is true of a worktree-local path
    too; the second condition is what separates a write that escaped into the primary through a
    linked corpus lane from one that stayed in the worktree and will be discarded at merge.

    Returns the resolved primary checkout path. Raises :class:`OutputNotInPrimary` naming the first
    output that is not durable, with the reason.
    """
    repo = Path(repo).resolve()
    primary = primary_checkout(repo)
    in_worktree = repo != primary
    for out in outputs:
        real = Path(os.path.realpath(out))
        inside_primary = real == primary or primary in real.parents
        inside_worktree = real == repo or repo in real.parents
        if not inside_primary:
            raise OutputNotInPrimary(
                f"FATAL: admission output {out} resolves to {real}, which is not inside the "
                f"primary checkout {primary} named by $SELDON_PRIMARY_CHECKOUT. Refusing to write "
                f"a corpus output the primary would not hold (AR-001, Issue 2b5a296d).")
        if in_worktree and inside_worktree:
            raise OutputNotInPrimary(
                f"FATAL: admission output {out} resolves to {real}, which is still inside this "
                f"worktree {repo}. The dispatcher's dispatch.worktree_links did not link its parent "
                f"corpus lane into the worktree, so this gitignored write would be discarded when "
                f"the merged worktree is removed (AR-001, Issue 2b5a296d). Add the lane to "
                f"dispatch.worktree_links in seldon.yaml, or write under $SELDON_PRIMARY_CHECKOUT.")
    return primary
