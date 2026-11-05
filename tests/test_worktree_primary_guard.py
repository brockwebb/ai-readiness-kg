"""AR-001 Part B: an admission driver refuses to write a gitignored output the primary won't hold.

Task `cc_tasks/2026-11-04_AR-001_worktree_admissions_answered_by_squiddy_link_the_corpus_dirs_write_to_the_primary_and_verify_there.md`;
squiddy SQ-109; Issue `2b5a296d`. The loss: a dispatched session writes `corpus/crosswalk/<id>.pdf`
(gitignored) into its worktree, the merge carries the tracked `manifest.json` but not the bytes, and
`git worktree remove` discards them — leaving the primary asserting `included`+`verified` for a
document whose bytes are gone.

The guard (`scripts/worktree_primary.py::assert_outputs_in_primary`) is a preflight: before any write,
each output's symlinks are resolved and the write is refused by name unless it is durable in the
primary checkout — inside `$SELDON_PRIMARY_CHECKOUT` and, when the driver runs in a worktree, not
still inside that worktree (which `dispatch.worktree_links` escapes by symlinking the corpus lane
into the primary).

These tests build a REAL git worktree and exercise the guard against the exact loss condition. The
static test then proves both admission drivers call the guard before their first write; the
subprocess test (anaconda-only, skipped otherwise) runs an actual driver and asserts it refuses.
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from worktree_primary import assert_outputs_in_primary, OutputNotInPrimary  # noqa: E402

DRIVERS = ("admit_measurement_theory_sources.py", "admit_usafacts_three_track.py")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def worktree(tmp_path: Path):
    """A real primary git repo with a `corpus/crosswalk/` directory, and a git worktree of it under
    the primary's `.claude/worktrees/` — the CLI's own layout, where the worktree nests inside the
    primary and so a worktree-local path is still 'inside the primary' by prefix."""
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q")
    _git(primary, "config", "user.email", "t@t")
    _git(primary, "config", "user.name", "t")
    (primary / "corpus" / "crosswalk").mkdir(parents=True)
    (primary / ".gitignore").write_text("corpus/crosswalk/\n.claude/worktrees/\n")
    (primary / "README").write_text("x")
    _git(primary, "add", "-A")
    _git(primary, "commit", "-q", "-m", "init")
    wt = primary / ".claude" / "worktrees" / "w"
    wt.parent.mkdir(parents=True)
    _git(primary, "worktree", "add", "-q", "--detach", str(wt), "HEAD")
    return primary, wt


def test_guard_refuses_worktree_local_output(worktree, monkeypatch):
    """No link: the output resolves inside the worktree, so it would be discarded at merge."""
    primary, wt = worktree
    monkeypatch.setenv("SELDON_PRIMARY_CHECKOUT", str(primary))
    (wt / "corpus" / "crosswalk").mkdir(parents=True)  # a real dir in the worktree, not a link
    out = wt / "corpus" / "crosswalk" / "doc.pdf"
    with pytest.raises(OutputNotInPrimary) as e:
        assert_outputs_in_primary(wt, [out])
    msg = str(e.value)
    assert "doc.pdf" in msg and "worktree" in msg and "2b5a296d" in msg


def test_guard_passes_through_link(worktree, monkeypatch):
    """A linked corpus lane: the worktree path resolves into the primary, so the write is durable."""
    primary, wt = worktree
    monkeypatch.setenv("SELDON_PRIMARY_CHECKOUT", str(primary))
    (wt / "corpus").mkdir(parents=True, exist_ok=True)
    (wt / "corpus" / "crosswalk").symlink_to(primary / "corpus" / "crosswalk")
    out = wt / "corpus" / "crosswalk" / "doc.pdf"
    returned = assert_outputs_in_primary(wt, [out])
    assert returned == primary.resolve()
    assert Path(os.path.realpath(out)) == (primary / "corpus" / "crosswalk" / "doc.pdf").resolve()


def test_guard_passes_direct_primary_run(worktree, monkeypatch):
    """Run by hand in the primary (no worktree, env unset): outputs are already durable."""
    primary, _ = worktree
    monkeypatch.delenv("SELDON_PRIMARY_CHECKOUT", raising=False)
    out = primary / "corpus" / "crosswalk" / "doc.pdf"
    assert assert_outputs_in_primary(primary, [out]) == primary.resolve()


def test_guard_refuses_output_outside_declared_primary(worktree, tmp_path, monkeypatch):
    """The output is not under the declared primary at all (e.g. a stray absolute path)."""
    primary, wt = worktree
    other = tmp_path / "elsewhere"
    other.mkdir()
    monkeypatch.setenv("SELDON_PRIMARY_CHECKOUT", str(primary))
    out = other / "doc.pdf"
    with pytest.raises(OutputNotInPrimary) as e:
        assert_outputs_in_primary(wt, [out])
    assert "not inside the primary checkout" in str(e.value)


# ---------------------------------------------------------------- static wiring
def _first_lineno(source: str, predicate) -> int | None:
    tree = ast.parse(source)
    hits = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and predicate(n)]
    return min(hits) if hits else None


def _is_guard_call(node: ast.Call) -> bool:
    f = node.func
    return (isinstance(f, ast.Name) and f.id == "assert_outputs_in_primary") or (
        isinstance(f, ast.Attribute) and f.attr == "assert_outputs_in_primary")


def _is_write_call(node: ast.Call) -> bool:
    f = node.func
    if isinstance(f, ast.Attribute):
        if f.attr in ("write_bytes", "write_text"):
            return True
        if f.attr in ("copy2", "copy", "copyfile"):  # shutil.copy2 etc.
            return True
        # manifest.add(...) / manifest.rebuild(...)
        if isinstance(f.value, ast.Name) and f.value.id == "manifest" and f.attr in ("add", "rebuild"):
            return True
    return False


@pytest.mark.parametrize("driver", DRIVERS)
def test_driver_imports_and_calls_guard_before_writing(driver):
    source = (REPO / "scripts" / driver).read_text()
    assert "assert_outputs_in_primary" in source, f"{driver} does not reference the AR-001 guard"
    assert "worktree_primary" in source, f"{driver} does not import from worktree_primary"
    guard_line = _first_lineno(source, _is_guard_call)
    write_line = _first_lineno(source, _is_write_call)
    assert guard_line is not None, f"{driver} never calls assert_outputs_in_primary"
    assert write_line is not None, f"{driver} has no write call to guard (test premise wrong)"
    assert guard_line < write_line, (
        f"{driver}: the guard at line {guard_line} must run before the first write at line "
        f"{write_line}; a guard after a write cannot stop a lost admission")


# ---------------------------------------------------------- the real driver refuses (anaconda only)
def _anaconda_can_import(driver_module: str) -> bool:
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); sys.path.insert(0, '.'); "
        f"import {driver_module}"
    )
    r = subprocess.run([sys.executable, "-c", probe], cwd=REPO, capture_output=True, text=True)
    return r.returncode == 0


@pytest.mark.parametrize("driver_module", [d[:-3] for d in DRIVERS])
def test_real_driver_refuses_when_output_not_in_primary(driver_module, tmp_path):
    """Run the actual driver; with $SELDON_PRIMARY_CHECKOUT pointed at an empty tree the driver's
    outputs are not durable there, so the guard refuses before any write. Skipped unless the driver's
    heavy deps (docling/dixie) import under this interpreter — gate-fast deliberately excludes them."""
    if not _anaconda_can_import(driver_module):
        pytest.skip("driver deps (docling/dixie) not importable under this interpreter")
    empty_primary = tmp_path / "empty_primary"
    empty_primary.mkdir()
    env = {**os.environ, "SELDON_PRIMARY_CHECKOUT": str(empty_primary)}
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / f"{driver_module}.py"), "--dry-run"],
        cwd=REPO, env=env, capture_output=True, text=True)
    assert r.returncode != 0, f"driver did not refuse; stdout={r.stdout[-400:]} stderr={r.stderr[-400:]}"
    assert "AR-001" in (r.stdout + r.stderr) or "primary checkout" in (r.stdout + r.stderr), (
        f"driver exited nonzero but not for the guard: {r.stderr[-600:]}")
