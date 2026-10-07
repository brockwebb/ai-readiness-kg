#!/usr/bin/env python3
"""Two runs of one commit report the same outcome for EVERY node id, not just the same totals.

`cc_tasks/2026-10-07_parallel_hosts_and_fast_gate.md` decision 5's gate: the suite under
pytest-xdist and the suite in one process, on one commit, compared node by node from their
JUnit XML (`--junitxml`). Equal totals can hide a test that passes in one run and fails in the
other while a second does the reverse; equal per-node outcomes cannot.

A node id is `classname::name`, less the `@<group>` suffix xdist's `--dist loadgroup` appends
to a grouped test's name (it names the worker queue, not the test). The outcome is `failed`
(a `<failure>` or `<error>`), `xfailed` (`<skipped type="pytest.xfail">`), `skipped` (any other
`<skipped>`) or `passed`.

    /opt/anaconda3/bin/python3 scripts/compare_junit_outcomes.py A.xml B.xml

Exit 0 when every node id is in both runs with one outcome; 1 otherwise, listing each one.
"""
from __future__ import annotations

import collections
import re
import sys
import xml.etree.ElementTree as ET

_GROUP_SUFFIX = re.compile(r"@[A-Za-z0-9_.+-]+$")


def outcomes(path: str) -> dict:
    out: dict = {}
    for case in ET.parse(path).iter("testcase"):
        node = f"{case.get('classname')}::{_GROUP_SUFFIX.sub('', case.get('name') or '')}"
        if case.find("failure") is not None or case.find("error") is not None:
            kind = "failed"
        elif (sk := case.find("skipped")) is not None:
            kind = "xfailed" if sk.get("type") == "pytest.xfail" else "skipped"
        else:
            kind = "passed"
        if node in out:
            raise SystemExit(f"REFUSING: {path} reports {node} twice")
        out[node] = kind
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        raise SystemExit("usage: compare_junit_outcomes.py A.xml B.xml")
    a, b = (outcomes(p) for p in argv)
    for name, run in zip(argv, (a, b)):
        counts = collections.Counter(run.values())
        print(f"{name}: {len(run)} node ids; " + ", ".join(
            f"{counts.get(k, 0)} {k}" for k in ("passed", "failed", "skipped", "xfailed")))
    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    differ = sorted(n for n in set(a) & set(b) if a[n] != b[n])
    for n in only_a:
        print(f"ONLY IN {argv[0]}: {n} ({a[n]})")
    for n in only_b:
        print(f"ONLY IN {argv[1]}: {n} ({b[n]})")
    for n in differ:
        print(f"DIFFERS: {n}: {a[n]} vs {b[n]}")
    same = not (only_a or only_b or differ)
    print(f"{'SAME' if same else 'DIFFERENT'}: {len(set(a) & set(b))} common node ids, "
          f"{len(differ)} differ, {len(only_a)} + {len(only_b)} in one run only")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
