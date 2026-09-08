#!/usr/bin/env python3
"""Register a cycle's figures and link each to every Result it prints. **Zero spend.**

Task `cc_tasks/2026-09-07_eda_and_charts.md` §2, carried to cycle 2 by
`cc_tasks/2026-09-07_scan_run_2.md` §5. The link set is not typed in: it is read back
out of the SVG's own `data-src` attributes, so a figure that stops printing a Result loses the
edge on the next run, and one that starts printing a new one gains it. A hand-maintained list
of "what this figure shows" is a list that goes stale silently.

The domain's own vocabulary, adopted rather than extended: `Figure -[:CONTAINS]-> Result` is
declared in `seldon/domain/research.yaml` for exactly this ("contains: from Figure to
Result"), and `Figure -[:GENERATED_BY]-> Script` for the generator. The domain declares no
`Figure -> DataFile` edge at all, so the two DataFiles a figure reads go on its `data_source`
property, which the schema defines as "Which DataFiles/Results this figure renders". F2 prints
no registered number — its whole content is the matrix — and without `data_source` it would be
the one figure with no provenance of any kind.

    /opt/anaconda3/bin/python3 scripts/register_scan_figures.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path



REPO = Path(__file__).resolve().parents[1]
SCAN = REPO / "assessment" / "harness" / "scan"
TASK = "cc_tasks/2026-09-07_scan_run_2.md"
CONFIG = SCAN / "figures.yaml"
sys.path.insert(0, str(REPO / "assessment" / "harness"))

_READS = re.compile(r'data-reads="([^"]*)"')
_FILES = re.compile(r'data-files="([^"]*)"')

CAPTIONS = {
    "per_leg_pass_rate":
        "F1. Pass rate per leg with its Wilson 95 % score interval and its denominator "
        "(pass + fail on admitted, observable surfaces; `error` excluded). Dot-and-interval "
        "rather than bars: Cleveland & McGill (1984) for position over length, and because a "
        "bar asserts a zero baseline as a claim while eight legs sitting at 0/23 is the claim "
        "under caution. A filled square marks a leg whose control fixtures fired in this same "
        "cycle, which is what separates a real zero from a dead rule. Legs are grouped by "
        "criterion and sorted only within one: they measure different constructs and are not "
        "comparable across.",
    "agencies_by_legs_matrix":
        "F2. All 14 roster agencies by 15 legs, one cell per Finding. Bertin's reorderable "
        "matrix, deliberately NOT reordered — sorting rows by pass count would be a ranking of "
        "agencies. Two control rows at the top are the instrument's ceiling and floor; StatCan "
        "is marked with a cross (every leg returned `error`, TCP reset); the four agencies "
        "with no admitted surface get one row each in their own fill, because dropping them "
        "would make the instrument's blind spot invisible.",
    "gap_map_by_criterion":
        "F3. Where the instrument is, by criterion: specified / harness_built / measured, with "
        "the count in each segment and every indicator code beside its bar. A12 is shown "
        "separately as a candidate and is in no count (DD-054). This is a coverage view and "
        "says nothing about pass rates — an indicator can be measured and failing.",
    "progress_over_snapshots":
        "F4. The same 48 indicators at three snapshots, each read from the commit named on the "
        "row. Three points is what exists and there is no line through them: two intervals of "
        "a few hours are not a rate of progress, and a line would say they were.",
    "cycle_over_cycle":
        "F5. Both cycles' pass rate per leg, side by side, each with its own `k/n` and Wilson "
        "95 % interval. A1 and A3 are marked **rule changed (v2\u2192v3, v3\u2192v4): not "
        "comparable** \u2014 a difference on those rows is the instrument moving, not the "
        "host. No line, no delta, no arrow: a difference between two points is not a trend, "
        "and two cycles hours apart on federal publication schedules are not a rate of "
        "change. A leg with no applicable denominator in a cycle is left blank rather than "
        "plotted at zero (DD-055: not measured is a reason, not a zero).",
}


def figures(cycle: str | None = None) -> dict:
    """The rendered SVGs of one cycle. The out_dir comes from `figures.config()`, which
    derives it from `params.cycle.name` — one definition of which cycle, shared with the
    renderer that wrote the files."""
    from scan import figures as _figs
    cfg = _figs.config(cycle)
    out = {}
    for path in sorted((REPO / cfg["out_dir"]).glob("*.svg")):
        body = path.read_text(encoding="utf-8")
        reads = _READS.search(body)
        files = _FILES.search(body)
        out[path.stem] = {"path": str(path.relative_to(REPO)),
                          "reads": sorted(reads.group(1).split()) if reads else [],
                          "files": sorted(files.group(1).split()) if files else []}
    return out


def run(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, cwd=REPO)


def existing(name: str) -> str | None:
    """The live, non-superseded Figure with this name, or None.

    `seldon artifact create` does NOT enforce name uniqueness on a Figure (only Result names
    are unique per graph, AD-028), so a second run of this script minted four twins on
    2026-09-07 and every link then failed with "Multiple artifacts with name=…". The guard is
    here rather than in the CLI because the CLI's rule is the CLI's to change; what this
    script owes is not to create what it can find.

    The reader itself now lives in `scripts/seldon_artifacts.py`, because two other registrars
    needed the same question answered and answered it with a check that could not work
    (`cc_tasks/2026-09-07_scan_run_2.md` §1.4). This name is kept as the local vocabulary.
    """
    from seldon_artifacts import live_artifact
    return live_artifact(name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="register a cycle other than params.cycle.name")
    a = ap.parse_args(argv)
    from scan import figures as _figs
    suffix = _figs.config(a.cycle)["cycle_suffix"]
    figs = figures(a.cycle)
    if not figs:
        raise SystemExit("FATAL: no SVGs found; run assessment/harness/scan/figures.py first")
    if a.dry_run:
        print(json.dumps({k: {"path": v["path"], "reads": len(v["reads"]),
                              "files": v["files"]} for k, v in figs.items()}, indent=1))
        return 0
    made, linked, failed, reused = 0, 0, [], 0
    for name, f in figs.items():
        node = f"{name}_{suffix}"
        fid = existing(node)
        if fid:
            reused += 1
            run(["seldon", "artifact", "update", fid, "--actor", "cc",
                 "-p", f"path={f['path']}", "-p", f"caption={CAPTIONS[name]}",
                 "-p", f"data_source={', '.join(f['files']) or 'the Result registry only'}"])
        else:
            fid = None
        r = None if fid else run(["seldon", "artifact", "create", "Figure", "--actor", "cc",
                 "-p", f"name={node}", "-p", f"path={f['path']}",
                 "-p", f"caption={CAPTIONS[name]}",
                 "-p", f"data_source={', '.join(f['files']) or 'the Result registry only'}",
                 "-p", f"description={CAPTIONS[name]} Generated by "
                       f"assessment/harness/scan/figures.py. Task {TASK}."])
        if r is not None and r.returncode:
            failed.append((name, r.stderr.strip()[-200:]))
            continue
        if r is not None:
            made += 1
            fid = existing(node)
        edges = [("CONTAINS", n) for n in f["reads"]]
        edges += [("GENERATED_BY", "scan_figures")]
        for rel, target in edges:
            lr = run(["seldon", "link", "create", "--from-id", fid,
                      "--rel", rel, "--to-name", target, "--actor", "cc"])
            if lr.returncode:
                failed.append((f"{name} -{rel}-> {target}", lr.stderr.strip()[-160:]))
            else:
                linked += 1
    for n, e in failed:
        print("FAILED:", n, e)
    print(f"figures created {made}, reused {reused}, links {linked}, failed {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
