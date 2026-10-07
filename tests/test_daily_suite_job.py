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

MAKEFILE = """suite:
\tpwd > "$(RAN_IN)"
\ttest -f data/seed.txt && test ! -L data/seed.txt && echo seeded >> "$(RAN_IN)"
\techo "3 passed in 0.01s"
\texit $$(cat "$(RC_FILE)")
"""


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture
def scratch(tmp_path):
    repo = tmp_path / "repo"
    (repo / "scripts" / "jobs").mkdir(parents=True)
    shutil.copy(WRAPPER, repo / "scripts" / "jobs" / WRAPPER.name)
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
    fake = tmp_path / "seldon"
    calls = tmp_path / "seldon_calls"
    fake.write_text(f'#!/bin/bash\necho "$@" >> "{calls}"\n', encoding="utf-8")
    fake.chmod(0o755)
    rc = tmp_path / "rc"
    env = {**os.environ, "AIRKG_DAILY_WORKTREE": str(tmp_path / "wt"),
           "AIRKG_DAILY_LOG_DIR": str(tmp_path / "logs"), "AIRKG_SELDON": str(fake),
           "RAN_IN": str(tmp_path / "ran_in"), "RC_FILE": str(rc),
           "NEO4J_USER": "unused", "NEO4J_PASS": "unused"}
    return {"repo": repo, "tmp": tmp_path, "env": env, "rc": rc, "calls": calls,
            "stop": repo / ".seldon" / "DISPATCH_STOP"}


def _run(s, rc: int) -> subprocess.CompletedProcess:
    s["rc"].write_text(str(rc))
    return subprocess.run(["/bin/bash", str(s["repo"] / "scripts" / "jobs" / WRAPPER.name)],
                          env=s["env"], capture_output=True, text=True, timeout=120)


def test_green_runs_in_its_own_worktree_at_main_with_the_ignored_inputs_copied(scratch):
    done = _run(scratch, 0)
    assert done.returncode == 0, done.stderr
    ran_in = (scratch["tmp"] / "ran_in").read_text().split()
    wt = (scratch["tmp"] / "wt").resolve()
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


def test_the_next_green_run_lifts_its_own_stop_and_moves_to_the_new_main(scratch):
    _run(scratch, 1)
    assert scratch["stop"].exists()
    (scratch["repo"] / "fix.txt").write_text("fixed\n")
    _git(scratch["repo"], "add", "fix.txt")
    _git(scratch["repo"], "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "fix")
    assert _run(scratch, 0).returncode == 0
    assert not scratch["stop"].exists()
    wt = scratch["tmp"] / "wt"
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
