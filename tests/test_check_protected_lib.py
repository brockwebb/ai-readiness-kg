"""`scripts/check_protected_lib.sh`: the one exclusion every protected-paths check shares.

`cc_tasks/2026-09-18_registration_commits.md` decision 3. Real git and the real `/bin/sh`,
because fourteen of the checks run under `#!/bin/sh` and the helper is a shell function that
interposes on git's own listing output: a fake of either would prove nothing about it.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LIB = REPO / "scripts" / "check_protected_lib.sh"
SOURCE_LINE = '. "$(dirname "$0")/check_protected_lib.sh"'


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout


def _sh(cwd: Path, script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["/bin/sh", "-c", f". {LIB}\n{script}"], cwd=cwd,
                          capture_output=True, text=True)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A checkout as a dispatched session sees it after a Desktop registration beside it."""
    for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"],
                 ["config", "user.name", "t"]):
        _git(tmp_path, *args)
    (tmp_path / "cc_tasks").mkdir()
    (tmp_path / "cc_tasks" / "old_RESULT.md").write_text("done\n", encoding="utf-8")
    (tmp_path / "seldon_events.jsonl").write_text('{"a": 1}\n', encoding="utf-8")
    (tmp_path / "work.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    # Written by other actors: a registered task file, an addendum, a store append.
    (tmp_path / "cc_tasks" / "registered.md").write_text("# t\n", encoding="utf-8")
    (tmp_path / "cc_tasks" / "registered_ADDENDUM_01.md").write_text("# a\n", encoding="utf-8")
    with (tmp_path / "seldon_events.jsonl").open("a", encoding="utf-8") as f:
        f.write('{"b": 2}\n')
    # Written by the session: a modified file and a new one.
    (tmp_path / "work.py").write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "new.py").write_text("y = 1\n", encoding="utf-8")
    return tmp_path


def test_foreign_paths_leave_every_listing_form(tree):
    out = _sh(tree, "git diff --name-only HEAD; echo --; git ls-files --others "
                    "--exclude-standard; echo --; git status --porcelain").stdout
    diff, others, porcelain = out.split("--\n")
    assert diff.split() == ["work.py"]
    assert others.split() == ["new.py"]
    assert porcelain.splitlines() == [" M work.py", "?? new.py"]


def test_a_modified_tracked_task_file_is_still_a_violation(tree):
    """Task files are immutable once written; no other actor edits one."""
    (tree / "cc_tasks" / "old_RESULT.md").write_text("rewritten\n", encoding="utf-8")
    out = _sh(tree, "git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md'; "
                    "git status --porcelain -- cc_tasks/").stdout.splitlines()
    assert out == ["cc_tasks/old_RESULT.md", " M cc_tasks/old_RESULT.md"]


def test_the_store_content_diff_is_untouched(tree):
    """Every check's append-only test reads the store's content diff, never its name."""
    out = _sh(tree, "git diff HEAD -- seldon_events.jsonl").stdout
    assert '+{"b": 2}' in out


def test_gits_exit_status_is_returned_and_other_commands_pass_through(tree):
    assert _sh(tree, "git status --porcelain --no-such-flag").returncode != 0
    assert _sh(tree, "git rev-parse --is-inside-work-tree").stdout.strip() == "true"


def test_every_protected_paths_check_sources_the_helper_on_line_two():
    checks = sorted((REPO / "scripts").glob("check_protected_*.sh"))
    checks = [c for c in checks if c != LIB]
    assert len(checks) >= 35
    missing = [c.name for c in checks
               if c.read_text(encoding="utf-8").splitlines()[1] != SOURCE_LINE]
    assert not missing, f"checks not sourcing the shared exclusion on line 2: {missing}"
