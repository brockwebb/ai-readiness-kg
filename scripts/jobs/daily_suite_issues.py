"""The daily suite job's Issues: one per failing test set, updated while it stays red, closed on green.

`cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md` decision 6. Until it, every red
run opened a fresh nameless `merge_blocked` Issue (`24deefb3`, `b2828020`, `a82451c1` on three
consecutive days for two different failures), `seldon go` printed `None` for each, and nothing
closed them when main went green.

The rules:

* **Named.** An Issue this job opens is named `daily suite red: <failing node ids>`, read from the
  `FAILED`/`ERROR` lines of the run's log (the `suite` target reports them with `-rfE`).
* **Updated, not reopened.** A red run whose name matches an open `merge_blocked` Issue appends the
  run to that Issue's description instead of opening another. A different failing set is a
  different finding and gets its own Issue.
* **Closed on green.** The first green run resolves every open `merge_blocked` Issue this job
  opened (named as above, or, for the ones opened before names existed, described
  `Daily full suite on ...`) with the green log's path in the resolution notes.

Called by `scripts/jobs/airkg_daily_suite.sh`, which owns the STOP file; this owns only Issues.
Drives the `seldon issue` CLI (`$AIRKG_SELDON` in a test), so a test can stand a fake in for it.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

NAME_PREFIX = "daily suite red: "
#: How the job's Issues were described before they had names; the green run closes those too.
LEGACY_DESCRIPTION_PREFIX = "Daily full suite on "
_FAILED_LINE = re.compile(r"^(?:FAILED|ERROR) (\S+)")


def failing_tests(log_text: str) -> list[str]:
    """Sorted, unique node ids from pytest's `-rfE` summary lines. A line's ` - message` tail
    is dropped; a parametrized id carries no spaces, so the first token is the whole id."""
    return sorted({m.group(1) for ln in log_text.splitlines()
                   if (m := _FAILED_LINE.match(ln))})


def issue_name(tests: list[str], rc: str) -> str:
    """One name per failing set. A run that died before naming a test is its own finding."""
    if tests:
        return NAME_PREFIX + ", ".join(tests)
    return f"{NAME_PREFIX}no failing test named (EXIT={rc or 'none'})"


def is_job_issue(issue: dict) -> bool:
    return (issue.get("issue_type") == "merge_blocked"
            and ((issue.get("name") or "").startswith(NAME_PREFIX)
                 or (issue.get("description") or "").startswith(LEGACY_DESCRIPTION_PREFIX)))


def plan_red(open_issues: list[dict], name: str) -> dict:
    """`{"action": "update", "issue": <the open Issue of this name>}` or `{"action": "create"}`."""
    for issue in open_issues:
        if is_job_issue(issue) and issue.get("name") == name:
            return {"action": "update", "issue": issue}
    return {"action": "create"}


def plan_green(open_issues: list[dict]) -> list[dict]:
    return [i for i in open_issues if is_job_issue(i)]


def _seldon(seldon: str, repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([seldon, *args], cwd=repo, capture_output=True, text=True)


def _open_issues(seldon: str, repo: str) -> list[dict] | None:
    """The open `merge_blocked` Issues, or None when the list could not be read. None is said
    out loud by the caller; it is never read as "there are none"."""
    r = _seldon(seldon, repo, "issue", "list", "--open", "--type", "merge_blocked", "--json")
    if r.returncode != 0:
        print(f"WARNING: seldon issue list exited {r.returncode}: {r.stderr.strip()[:300]}")
        return None
    try:
        rows = json.loads(r.stdout or "null")
    except json.JSONDecodeError:
        print(f"WARNING: seldon issue list printed no JSON: {r.stdout.strip()[:300]!r}")
        return None
    if not isinstance(rows, list):
        print(f"WARNING: seldon issue list printed {type(rows).__name__}, not a list")
        return None
    return rows


def red(a) -> int:
    with open(a.log, encoding="utf-8", errors="replace") as fh:
        tests = failing_tests(fh.read())
    name = issue_name(tests, a.rc)
    run = (f"{a.stamp} {a.branch}@{a.sha[:12]} (EXIT={a.rc or 'none'}, "
           f"{a.summary or 'no summary line'}). Log: {a.log}.")
    issues = _open_issues(a.seldon, a.repo)
    plan = plan_red(issues or [], name)
    if issues is None:
        print("WARNING: open Issues unreadable; opening a new one rather than recording nothing")
    if plan["action"] == "update":
        issue = plan["issue"]
        r = _seldon(a.seldon, a.repo, "issue", "update", issue["artifact_id"], "--description",
                    f"{issue.get('description', '')} Red again: {run}")
        print(f"red again on the open Issue {issue['artifact_id'][:8]} ({name})")
    else:
        r = _seldon(a.seldon, a.repo, "issue", "create", "--name", name, "--description",
                    f"Daily full suite on {a.branch} is red: {run} Dispatch is stopped by "
                    f"{a.stop} until main is green.",
                    "--type", "merge_blocked", "--importance", "high", "--urgency", "high",
                    "--detection", "build_failure", "--target", "structure")
    print(r.stdout, end="")
    if r.returncode != 0:
        print(f"WARNING: seldon issue {plan['action']} exited {r.returncode}: "
              f"{r.stderr.strip()[:300]}")
        return 1
    return 0


def green(a) -> int:
    issues = _open_issues(a.seldon, a.repo)
    if issues is None:
        print("WARNING: open Issues unreadable; none closed this run")
        return 1
    failed = 0
    for issue in plan_green(issues):
        r = _seldon(a.seldon, a.repo, "issue", "update", issue["artifact_id"], "--state",
                    "resolved", "--resolution-notes",
                    f"main green at {a.branch}@{a.sha[:12]} ({a.stamp}). Log: {a.log}")
        print(f"closed {issue['artifact_id'][:8]} ({issue.get('name') or 'unnamed'})"
              if r.returncode == 0 else
              f"WARNING: could not close {issue['artifact_id'][:8]}: {r.stderr.strip()[:300]}")
        failed += r.returncode != 0
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("outcome", choices=("red", "green"))
    for flag in ("--seldon", "--repo", "--log", "--sha", "--stamp", "--branch"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--rc", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--stop", default="")
    a = ap.parse_args(argv)
    return red(a) if a.outcome == "red" else green(a)


if __name__ == "__main__":
    sys.exit(main())
