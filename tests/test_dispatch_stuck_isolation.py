"""The dispatcher never records a dirty tree it cannot name, and passes in isolated copies of the
stuck-streak file never count toward each other.

`cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md` decision 5. The quiet-state test
in `tests/test_dispatch_config.py` is `interactive_only` and `live_model`, so it runs neither in a
dispatched session nor in the daily job. These pin the two mechanisms behind its 2026-10-08 and
2026-10-09 failures without a graph, a real pass, the queue's state or the kind of session:

* the daily worktree is a DETACHED HEAD, c7 failed on its branch half with a clean tree, and the
  pass reported `dirty_tree` with no path (`dirty: (branch)` in the worktree's
  `logs/airkg_dispatch.log`);
* the suite's three real passes in four seconds shared the worktree's `.seldon/dispatch_stuck.json`,
  and the third crossed `stuck_after_passes: 3`.

Seldon is whichever `seldon` the session imported first, which in this suite is the one
`tests/model_lock.py` imports through `tests/conftest.py`, before this module is collected: the
installed checkout. To run these against another seldon (the pre-fix commit, for the red half of
decision 5), put that checkout first on `PYTHONPATH`; prepending it to `sys.path` here is too late.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SELDON_CHECKOUT = REPO.parent / "seldon"
pytestmark = pytest.mark.skipif(not SELDON_CHECKOUT.exists(),
                                reason="seldon checkout not beside this repo")

#: Spelled out rather than imported: on the pre-fix seldon the name does not exist, and the test
#: must fail on behaviour, not on an ImportError.
STUCK_STATE_ENV = "SELDON_DISPATCH_STUCK_STATE"

CFG = {"branch": "main", "lease_file": ".seldon/dispatch.lock", "stuck_after_passes": 3,
       "poll_interval_s": 300}


def _git(p: Path, *a):
    return subprocess.run(["git", *a], cwd=p, check=True, capture_output=True, text=True)


@pytest.fixture
def detached(tmp_path):
    """The daily worktree's shape: committed, clean, HEAD detached."""
    p = tmp_path / "repo"
    p.mkdir()
    _git(p, "init", "-q", "-b", "main")
    _git(p, "config", "user.email", "t@t")
    _git(p, "config", "user.name", "t")
    (p / "a.txt").write_text("a\n")
    _git(p, "add", "a.txt")
    _git(p, "commit", "-q", "-m", "a")
    _git(p, "checkout", "-q", "--detach")
    return p


@pytest.fixture
def no_side_effects(monkeypatch):
    """A stuck alarm emits an event and runs the notifier; record either instead of doing it."""
    from seldon.commands import dispatch as CMD
    seen = []
    monkeypatch.setattr(CMD, "_emit", lambda *a, **k: seen.append(("emit", a[2], a[3])))
    monkeypatch.setattr(CMD, "_run_notifier", lambda *a, **k: seen.append(("notify",)))
    return seen


def _row(tree: dict) -> dict:
    """One candidate, with c7 as `seldon.core.dispatch.evaluate` builds it."""
    c7 = {"branch": tree["branch"], "configured_branch": CFG["branch"], "dirty": tree["dirty"],
          "dirty_count": tree["dirty_count"], "dirty_paths": tree["dirty_paths"],
          "ok": tree["branch"] == CFG["branch"] and not tree["dirty"]
          and not tree.get("read_error")}
    if tree.get("read_error"):
        c7["read_error"] = tree["read_error"]
    return {"task_id": "t", "candidate": True, "criteria": {"c7": c7},
            "failed": [] if c7["ok"] else ["c7"], "name": "t", "source_file": "cc_tasks/t.md"}


def test_a_failed_git_read_records_no_dirty_tree_and_advances_no_streak(
        tmp_path, monkeypatch, no_side_effects):
    """Decision 3: a git call that fails is a failed read, under its own reason, and the pass
    that made it does not count. Pre-fix, `tree_state` ignored git's exit code: a directory git
    cannot read came back `dirty: False` with branch `""`, c7 reported `dirty_tree`, and the
    streak advanced to an alarm with `dirty_paths: []`."""
    from seldon.commands import dispatch as CMD
    from seldon.core import dispatch as D
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.setenv(STUCK_STATE_ENV, str(tmp_path / "streaks.json"))
    unreadable = tmp_path / "not_a_checkout"
    unreadable.mkdir()
    tree = D.tree_state(unreadable)
    row = _row(tree)
    assert D.first_refusal_reason(row) != "dirty_tree"
    for _ in range(CFG["stuck_after_passes"] + 1):
        CMD._stuck(unreadable, "s", CFG, [row], tree, None, False)
    assert not (tmp_path / "streaks.json").exists()
    assert not (unreadable / ".seldon").exists(), "a failed read advanced a streak"
    assert no_side_effects == [], no_side_effects


def test_a_detached_clean_checkout_never_reports_dirty_tree(
        detached, tmp_path, monkeypatch, no_side_effects):
    """The incident's own state. Whatever a pass on it asserts, it does not assert a dirty tree
    it cannot name: an alarm, if one is raised, names its criterion as the branch."""
    from seldon.commands import dispatch as CMD
    from seldon.core import dispatch as D
    monkeypatch.setenv(STUCK_STATE_ENV, str(tmp_path / "streaks.json"))
    tree = D.tree_state(detached)
    assert tree["dirty_paths"] == []
    assert D.first_refusal_reason(_row(tree)) == "wrong_branch"
    for _ in range(CFG["stuck_after_passes"]):
        CMD._stuck(detached, "s", CFG, [_row(tree)], tree, None, False)
    emitted = [e for e in no_side_effects if e[0] == "emit"]
    assert len(emitted) == 1
    assert emitted[0][2]["criterion"] == "wrong_branch"
    assert emitted[0][2]["dirty_paths"] == []


def test_passes_in_two_isolated_streak_copies_do_not_see_each_others_counts(
        detached, tmp_path, monkeypatch, no_side_effects):
    """Decision 4's isolation, as `tests/test_dispatch_config.py::_isolated_stuck_state` uses it:
    each test's passes read and write their own copy. Two tests, two passes each, interleaved —
    four passes in all, past the threshold of three — and neither copy reaches it. Pre-fix the
    override did not exist, all four passes landed in the checkout's one file, and the third
    alarmed: exactly the daily suite's 2026-10-09 failure."""
    from seldon.commands import dispatch as CMD
    from seldon.core import dispatch as D
    tree = D.tree_state(detached)
    rows = [_row(tree)]
    a, b = tmp_path / "a" / "dispatch_stuck.json", tmp_path / "b" / "dispatch_stuck.json"
    for copy in (a, b, a, b):
        monkeypatch.setenv(STUCK_STATE_ENV, str(copy))
        CMD._stuck(detached, "s", CFG, rows, tree, None, False)
    assert no_side_effects == [], "a pass counted another copy's passes toward the threshold"
    for copy in (a, b):
        monkeypatch.setenv(STUCK_STATE_ENV, str(copy))
        assert D.read_stuck_state(detached, CFG)["t"]["passes"] == 2
    assert not (detached / ".seldon").exists(), "a pass wrote the checkout's shared streak file"
