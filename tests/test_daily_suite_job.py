"""The daily full-suite job runs on `main` in its own worktree, and a red run stops dispatch.

`cc_tasks/2026-10-07_parallel_hosts_and_fast_gate.md` decision 6 (DN-013-R4). The incident it
answers: the recollection's first full-suite run died at 35% with no EXIT line at
2026-10-07T02:17:51Z, when a Desktop session committed in the same checkout (DN-013 ADDENDUM 01
A2). A gate must not run in a tree another process commits to.

The wrapper is copied into a scratch repository, the way `tests/test_dispatch_config.py` runs
the dispatch wrapper, so nothing here touches this checkout, its `.seldon/` or the graph: the
scratch `Makefile`'s `suite` target stands in for the suite and records where it ran, and a
fake `seldon` records the Issue it was asked to open.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WRAPPER = REPO / "scripts" / "jobs" / "airkg_daily_suite.sh"
PLIST = REPO / "scripts" / "jobs" / "com.brock.airkg-daily-suite.plist"
MARK = "airkg-daily-suite: main is red"

HELPER = REPO / "scripts" / "jobs" / "daily_suite_issues.py"

MAKEFILE = """suite:
\tpwd > "$(RAN_IN)"
\ttest -f data/seed.txt && test ! -L data/seed.txt && echo seeded >> "$(RAN_IN)"
\tcat "$(FAILED_LINES)"
\techo "3 passed in 0.01s"
\texit $$(cat "$(RC_FILE)")
"""

#: A stand-in for `seldon`: records every call, and answers `issue list` from a JSON file the
#: test writes (`[]` when it wrote none), as `seldon issue list --json` does.
FAKE_SELDON = """#!/bin/bash
echo "$@" >> "{calls}"
if [ "$1 $2" = "issue list" ]; then
  if [ -f "{issues}" ]; then cat "{issues}"; else echo "[]"; fi
fi
"""


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture
def scratch(tmp_path):
    repo = tmp_path / "repo"
    (repo / "scripts" / "jobs").mkdir(parents=True)
    shutil.copy(WRAPPER, repo / "scripts" / "jobs" / WRAPPER.name)
    shutil.copy(HELPER, repo / "scripts" / "jobs" / HELPER.name)
    (repo / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    (repo / "seldon.yaml").write_text("dispatch:\n  stop_file: .seldon/DISPATCH_STOP\n",
                                      encoding="utf-8")
    (repo / "controls.yaml").write_text("jobs:\n  biblio_resume:\n    log_retention_days: 30\n",
                                        encoding="utf-8")
    (repo / ".gitignore").write_text("data/\nlogs/\n.seldon/\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "scratch")
    (repo / "data").mkdir()
    (repo / "data" / "seed.txt").write_text("an ignored input the suite reads\n")
    (repo / ".seldon").mkdir()
    fake = tmp_path / "fake_seldon_cli"
    calls = tmp_path / "seldon_calls"
    issues = tmp_path / "open_issues.json"
    fake.write_text(FAKE_SELDON.format(calls=calls, issues=issues), encoding="utf-8")
    fake.chmod(0o755)
    rc = tmp_path / "rc"
    failed_lines = tmp_path / "failed_lines"
    failed_lines.write_text("", encoding="utf-8")
    # The worktree under its OWN parent, as the installed job's is (~/.cache/airkg/), so a
    # sibling of the repository is not trivially a sibling of the worktree too.
    env = {**os.environ, "AIRKG_DAILY_WORKTREE": str(tmp_path / "cache" / "wt"),
           "AIRKG_DAILY_LOG_DIR": str(tmp_path / "logs"), "AIRKG_SELDON": str(fake),
           "RAN_IN": str(tmp_path / "ran_in"), "RC_FILE": str(rc),
           "FAILED_LINES": str(failed_lines),
           "NEO4J_USER": "unused", "NEO4J_PASS": "unused"}
    return {"repo": repo, "tmp": tmp_path, "env": env, "rc": rc, "calls": calls,
            "stop": repo / ".seldon" / "DISPATCH_STOP", "issues": issues,
            "failed_lines": failed_lines}


def _run(s, rc: int) -> subprocess.CompletedProcess:
    s["rc"].write_text(str(rc))
    return subprocess.run(["/bin/bash", str(s["repo"] / "scripts" / "jobs" / WRAPPER.name)],
                          env=s["env"], capture_output=True, text=True, timeout=120)


def test_green_runs_in_its_own_worktree_at_main_with_the_ignored_inputs_copied(scratch):
    done = _run(scratch, 0)
    assert done.returncode == 0, done.stderr
    ran_in = (scratch["tmp"] / "ran_in").read_text().split()
    wt = (scratch["tmp"] / "cache" / "wt").resolve()
    assert Path(ran_in[0]).resolve() == wt, "the suite ran outside the job's worktree"
    assert Path(ran_in[0]).resolve() != scratch["repo"].resolve()
    assert ran_in[1:] == ["seeded"], "the ignored input was not copied in as a file"
    assert _git(wt, "rev-parse", "HEAD") == _git(scratch["repo"], "rev-parse", "main")
    assert not scratch["stop"].exists()
    job = (scratch["tmp"] / "logs" / "job.log").read_text()
    assert "EXIT=0" in job and "3 passed" in job


def test_red_writes_the_stop_file_with_the_log_and_opens_an_issue(scratch):
    done = _run(scratch, 1)
    assert done.returncode == 0, "a red suite is a finding about main, not a job failure"
    stop = scratch["stop"].read_text().splitlines()
    assert stop[0] == MARK
    # make exits 2 when a recipe fails; the job records make's code, whatever it is.
    assert "EXIT=2" in stop[1] and "log=" in stop[1]
    log = Path(stop[1].split("log=", 1)[1])
    assert log.is_file() and "EXIT=2" in log.read_text()
    issue = scratch["calls"].read_text()
    assert "issue create" in issue and "--type merge_blocked" in issue and str(log) in issue


def test_a_sibling_checkout_is_linked_beside_the_worktree(scratch, tmp_path):
    """`tests/test_dispatch_config.py` reads `REPO/../seldon`; from the worktree, `../seldon`
    must resolve to the same checkout or two tests skip that the checkout runs."""
    (tmp_path / "seldon").mkdir()
    assert _run(scratch, 0).returncode == 0
    link = scratch["tmp"] / "cache" / "seldon"
    assert link.is_symlink() and link.resolve() == (tmp_path / "seldon").resolve()


def test_the_next_green_run_lifts_its_own_stop_and_moves_to_the_new_main(scratch):
    _run(scratch, 1)
    assert scratch["stop"].exists()
    (scratch["repo"] / "fix.txt").write_text("fixed\n")
    _git(scratch["repo"], "add", "fix.txt")
    _git(scratch["repo"], "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "fix")
    assert _run(scratch, 0).returncode == 0
    assert not scratch["stop"].exists()
    wt = scratch["tmp"] / "cache" / "wt"
    assert _git(wt, "rev-parse", "HEAD") == _git(scratch["repo"], "rev-parse", "main")


def test_a_stop_file_someone_else_wrote_is_never_lifted_or_overwritten(scratch):
    scratch["stop"].write_text("stopped by the operator: budget\n")
    _run(scratch, 0)
    assert scratch["stop"].read_text() == "stopped by the operator: budget\n"
    _run(scratch, 1)
    lines = scratch["stop"].read_text().splitlines()
    assert lines[0] == "stopped by the operator: budget" and "EXIT=2" in lines[1]
    _run(scratch, 0)
    assert scratch["stop"].read_text().startswith("stopped by the operator: budget")


def test_the_plist_runs_the_wrapper_daily_and_not_at_load():
    import plistlib
    with PLIST.open("rb") as fh:
        p = plistlib.load(fh)
    assert p["Label"] == "com.brock.airkg-daily-suite"
    assert p["ProgramArguments"][-1].endswith("scripts/jobs/airkg_daily_suite.sh")
    assert set(p["StartCalendarInterval"]) == {"Hour", "Minute"}
    assert p["RunAtLoad"] is False


# ---------------------------------------------------------------------------------------------
# cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md decisions 6 and 7
# ---------------------------------------------------------------------------------------------

FAILING = "tests/test_x.py::test_y"


def _calls(s) -> list[str]:
    return s["calls"].read_text().splitlines() if s["calls"].exists() else []


def _open(s, *issues):
    import json
    s["issues"].write_text(json.dumps(list(issues)), encoding="utf-8")


def test_a_red_run_opens_an_issue_named_for_its_failing_test(scratch):
    scratch["failed_lines"].write_text(f"FAILED {FAILING} - AssertionError: boom\n")
    assert _run(scratch, 1).returncode == 0
    creates = [c for c in _calls(scratch) if c.startswith("issue create")]
    assert len(creates) == 1, _calls(scratch)
    assert f"--name daily suite red: {FAILING} " in creates[0]
    assert "--type merge_blocked" in creates[0]


def test_red_again_on_the_same_test_updates_the_open_issue_instead_of_opening_another(scratch):
    scratch["failed_lines"].write_text(f"FAILED {FAILING} - AssertionError: boom\n")
    _open(scratch, {"artifact_id": "aaaaaaaa-1", "issue_type": "merge_blocked",
                    "name": f"daily suite red: {FAILING}", "description": "first red.",
                    "state": "open"})
    assert _run(scratch, 1).returncode == 0
    calls = _calls(scratch)
    assert not [c for c in calls if c.startswith("issue create")], calls
    updates = [c for c in calls if c.startswith("issue update aaaaaaaa-1 --description")]
    assert len(updates) == 1, calls
    assert updates[0].split("--description ", 1)[1].startswith("first red. Red again: ")


def test_red_on_a_different_test_opens_its_own_issue(scratch):
    scratch["failed_lines"].write_text("FAILED tests/test_other.py::test_z - boom\n")
    _open(scratch, {"artifact_id": "aaaaaaaa-1", "issue_type": "merge_blocked",
                    "name": f"daily suite red: {FAILING}", "description": "d", "state": "open"})
    _run(scratch, 1)
    assert [c for c in _calls(scratch) if c.startswith("issue create")]
    assert not [c for c in _calls(scratch) if c.startswith("issue update")]


def test_the_first_green_run_closes_the_jobs_open_issues_and_only_those(scratch):
    _open(scratch,
          {"artifact_id": "named-1", "issue_type": "merge_blocked",
           "name": f"daily suite red: {FAILING}", "description": "d", "state": "open"},
          # opened before Issues had names: 24deefb3 and b2828020 are these
          {"artifact_id": "legacy-2", "issue_type": "merge_blocked",
           "description": "Daily full suite on main@33d95583e233 is red (EXIT=2, ...)",
           "state": "open"},
          {"artifact_id": "worktree-3", "issue_type": "merge_blocked", "name": "merge failed",
           "description": "a worktree task the dispatcher could not merge", "state": "open"})
    assert _run(scratch, 0).returncode == 0
    closes = [c for c in _calls(scratch) if c.startswith("issue update")]
    assert sorted(c.split()[2] for c in closes) == ["legacy-2", "named-1"], closes
    for c in closes:
        assert "--state resolved" in c and "--resolution-notes main green at main@" in c
        assert str(scratch["tmp"] / "logs") in c, "the resolution does not name the green log"


def test_green_removes_only_the_jobs_lines_and_leaves_the_operators(scratch):
    """Decision 7, on the 2026-10-07 file's own shape: an operator line first, then one line per
    red run appended by the job. Green leaves the operator's line, and with it the stop."""
    scratch["stop"].write_text("stopped by Desktop: operator at 84% of weekly cap\n")
    _run(scratch, 1)
    _run(scratch, 1)
    assert len(scratch["stop"].read_text().splitlines()) == 3
    _run(scratch, 0)
    assert scratch["stop"].read_text() == "stopped by Desktop: operator at 84% of weekly cap\n"
    job = (scratch["tmp"] / "logs" / "job.log").read_text()
    assert "dispatch stays stopped until they are removed" in job


def test_green_never_deletes_an_operator_line_appended_to_the_jobs_own_file(scratch):
    _run(scratch, 1)
    with scratch["stop"].open("a") as fh:
        fh.write("operator: keep this stopped until the budget resets\n")
    _run(scratch, 0)
    assert scratch["stop"].read_text() == "operator: keep this stopped until the budget resets\n"


def test_the_issue_helper_reads_failing_ids_from_the_summary_lines():
    import importlib.util
    spec = importlib.util.spec_from_file_location("daily_suite_issues", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    log = ("FAILED tests/b.py::t[x-1] - AssertionError: a - b\n"
           "ERROR tests/a.py - ImportError\nSKIPPED [1] tests/c.py:3: why\n"
           "FAILED tests/b.py::t[x-1] - again\n")
    assert mod.failing_tests(log) == ["tests/a.py", "tests/b.py::t[x-1]"]
    assert mod.issue_name([], "none") == "daily suite red: no failing test named (EXIT=none)"
