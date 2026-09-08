#!/usr/bin/env python3
"""Register everything the four figures need to print. **Zero model spend. No network.**

Task `cc_tasks/2026-09-07_eda_and_charts.md` §1. The scan-run RESULT quoted fifteen Wilson
intervals that exist nowhere in the Result registry, and the progress page drew three
snapshots of which only one was registered. A figure printing a number the registry does not
hold is a chart with a footnote nobody can follow; §4's gate forbids it, and this script is
what makes the gate satisfiable.

Idempotent in the only sense AD-028 allows: a name already bound AT THE SAME VALUE is this
script re-running; at a different value it is drift and stays an error.

    /opt/anaconda3/bin/python3 scripts/register_figure_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                 # noqa: E402
from scan import load_params                                         # noqa: E402
from seldon_artifacts import live_artifact                           # noqa: E402
from scan.stats import Z, wilson                                     # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_run_2.md"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"


#: Which cycle's figures these Results feed is read from `params.cycle.name`, never typed —
#: the same single-source rule `scripts/scan_report.py` follows, and for the same reason: a
#: second copy of the cycle name is a second definition of "which cycle", and the stale copy
#: is the one that reports last week's numbers under this week's heading.
def paths(cycle: str) -> dict:
    suffix = cycle_results.cycle_suffix(cycle)
    return {"cycle": cycle, "suffix": suffix,
            "matrix": REPO / "state" / f"scan_matrix_{suffix}.json",
            "payload": REPO / "state" / f"{cycle}.json",
            "matrix_name": f"scan_matrix_{suffix}",
            "payload_name": cycle}

#: The three framework snapshots F4 draws, each read from a COMMIT rather than from a
#: remembered number. `git show <commit>:<path>` is the provenance; the short hash goes on the
#: figure's x axis so a reader can re-read the same bytes.
#: (name suffix, commit, why). The middle one keeps the `_after_review` suffix already bound
#: for its `harness_built` count rather than inventing a second naming for one snapshot.
SNAPSHOTS = [("2026-09-06", "51d2526", "the KG freeze, before any harness existed"),
             ("after_review", "72cdec6", "after the 16-rule conformance review of 2026-09-06"),
             ("2026-09-07", "52ec048", "after the scan-run write-back")]

STATUSES = ("measured", "harness_built", "specified")
CRITERIA = ("A", "B", "C", "D", "E", "F", "G")


def slug(leg: str) -> str:
    """`A11-declared` -> `a11_declared`. The convention the per-leg Results already use."""
    return leg.replace("-", "_").lower()


def snapshot_counts(commit: str) -> dict:
    """Indicator status counts in the framework of record AS OF a commit, candidates excluded
    (DD-054). Reads the file out of git, never a number out of a RESULT."""
    out = subprocess.run(["git", "show", f"{commit}:framework/ai_readiness_framework.json"],
                         capture_output=True, text=True, cwd=REPO)
    if out.returncode:
        raise SystemExit(f"FATAL: cannot read framework JSON at {commit}: {out.stderr.strip()}")
    g = json.loads(out.stdout)
    inds = [n["properties"] for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"] and n["properties"].get("status") != "candidate"]
    counts = collections.Counter(p.get("measurement_status") for p in inds)
    return {"total": len(inds), **{s: counts[s] for s in STATUSES}}


def rows(cycle: str) -> list:
    """(name, value, script, data, description). Nothing here is typed in from prose."""
    P = paths(cycle)
    SUFFIX, CYCLE, MATRIX = P["suffix"], P["cycle"], P["matrix"]
    mx = json.loads(MATRIX.read_text(encoding="utf-8"))
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    out = []

    # ---- the fifteen intervals the scan-run RESULT quoted and never registered ----
    for leg in mx["legs"]:
        pl = mx["per_leg"][leg]
        k, n = pl["pass"], pl["applicable_n"]
        lo, hi = wilson(k, n, Z)
        # The matrix was written by the same arithmetic; if these disagree, one of them is a
        # second implementation and the whole point of scan/stats.py has been lost.
        if (lo, hi) != (pl["ci95_low"], pl["ci95_high"]):
            raise SystemExit(f"FATAL: {leg} interval disagrees with {MATRIX.name}: "
                             f"computed {(lo, hi)}, stored {(pl['ci95_low'], pl['ci95_high'])}")
        note = (f"Wilson 95 % score interval {{}} bound for {leg}: {k}/{n} pass on the "
                f"observable-surface denominator ({pl['denominator']}), z = {Z}, cycle "
                f"{CYCLE}, params_hash {mx['params_hash'][:12]}…. Wilson (1927), recommended "
                f"over Wald at small n and at 0 or n successes by Brown, Cai & DasGupta (2001) "
                f"and Newcombe (1998).")
        out.append((f"scan_{slug(leg)}_wilson_lo_{SUFFIX}", lo, "scan_stats",
                    P["matrix_name"], note.format("LOWER")))
        out.append((f"scan_{slug(leg)}_wilson_hi_{SUFFIX}", hi, "scan_stats",
                    P["matrix_name"], note.format("UPPER")))

    # ---- did each leg's rule actually fire on the fixtures? ----
    # F1 shows eight legs at 0/23, and a rate of zero has two readings: the products do not
    # have the property, or the rule is dead. The controls separate them, and separating them
    # is only visible on the figure if the answer is a registered number rather than a
    # sentence in a RESULT. `passes_all` must produce `pass` and `fails_all` must produce
    # `fail`; anything else is 0 and the cycle would have been invalid (DD-019).
    cyc = json.loads(P["payload"].read_text(encoding="utf-8"))
    ctrl = collections.defaultdict(dict)
    for f in cyc["control_findings_detail"]:
        ctrl[f["leg"]][f["target_doc_id"]] = f["verdict"]
    # A RE-JUDGED cycle publishes no control Findings — publishing them would mean publishing
    # the fixture Observations behind them, and a re-judgement creates no Observation — so the
    # gate it stands on is recorded on the payload instead (`scan/rederive.control_gate_record`,
    # `cc_tasks/2026-09-08_scan_harness_v4.md` §1.5). Same verdicts, same fixtures, same
    # pre-registered table; a different place on the payload. Read it rather than registering
    # fifteen zeros, which would say every rule is dead.
    gate = cyc.get("control_gate") or {}
    if not ctrl and gate.get("verdicts"):
        for leg, per_fixture in gate["verdicts"].items():
            ctrl[leg].update(per_fixture)
    where = (f"the control gate recorded on cycle {CYCLE} ({gate.get('rule')}: "
             f"{gate.get('verdict')})" if gate.get("verdicts") and cyc.get("cycle_kind")
             == "rejudged" else f"cycle {CYCLE}")
    for leg in mx["legs"]:
        got = ctrl.get(leg, {})
        fired = int(got.get("control:passes_all") == "pass"
                    and got.get("control:fails_all") == "fail")
        out.append((f"scan_{slug(leg)}_control_fired_{SUFFIX}", fired, "scan_run",
                    P["payload_name"],
                    f"1 when {leg}'s CURRENT rule returned `pass` on the `passes_all` fixture "
                    f"AND `fail` on the `fails_all` fixture in {where}, else 0. This is "
                    f"the ceiling-and-floor check that tells a 0/23 rate apart from a rule "
                    f"that cannot return `pass` at all; a cycle with no fired control is "
                    f"invalid (DD-019). Observed: passes_all -> "
                    f"{got.get('control:passes_all')}, fails_all -> "
                    f"{got.get('control:fails_all')}."))

    # ---- the three snapshots F4 draws, each read from its commit ----
    for date, commit, why in SNAPSHOTS:
        c = snapshot_counts(commit)
        for st in STATUSES:
            out.append((f"framework_indicators_{st}_{date}", c[st], "framework_progress",
                        "ai_readiness_framework",
                        f"Indicators at `{st}` of {c['total']} in the framework of record at "
                        f"`git show {commit}:framework/ai_readiness_framework.json` ({why}). "
                        f"Candidates excluded from the count (DD-054)."))

    # ---- per criterion, the 2026-09-07 snapshot: the gap map's own numbers ----
    inds = [n["properties"] for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"] and n["properties"].get("status") != "candidate"]
    per = collections.Counter((p["criterion_code"], p["measurement_status"]) for p in inds)
    tot = collections.Counter(p["criterion_code"] for p in inds)
    for crit in CRITERIA:
        for st in STATUSES:
            out.append((f"framework_{crit}_{st}_{SUFFIX}", per[(crit, st)], "framework_progress",
                        "ai_readiness_framework",
                        f"Indicators of criterion {crit} at `{st}`, of {tot[crit]} in that "
                        f"criterion, as of the {SUFFIX} scan-run write-back. A12 excluded "
                        f"(candidate, DD-054); this is a coverage count and says nothing "
                        f"about pass rates."))

    # ---- the denominator under "4 of 14 agencies contributed no surface" ----
    out.append((f"scan_agencies_total_{SUFFIX}", len(mx["agencies"]), "build_scan_targets",
                "scan_targets_2026-09",
                "Agencies on the target roster: the 13 U.S. principal statistical agencies "
                "enumerated by OMB Statistical Policy Directive No. 1 (79 FR 71610, segments "
                "s22-s39) plus the StatCan comparator. This is the denominator under "
                "`scan_agencies_with_no_admitted_surface` and `scan_agencies_unobservable`, "
                "which had none registered."))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="which cycle's figures to register inputs for "
                         "(default: params.cycle.name)")
    a = ap.parse_args(argv)
    data = rows(a.cycle or load_params()["cycle"]["name"])
    if a.dry_run:
        for n, v, sc, dn, note in data:
            print(f"{n}\t{v}\t{sc}\t{dn}")
        print(len(data), "Results")
        return 0
    # The cycle payload is a DataFile like any other and every cycle writes a new one, so it is
    # ensured here for the reason `cycle_results.ensure_data_file` exists: `seldon result
    # register` resolves every reference BEFORE writing an event (AD-028), so a missing
    # artifact refuses the batch — correctly, and at the wrong moment to find out.
    P = paths(a.cycle or load_params()["cycle"]["name"])
    cycle_results.ensure_data_file(
        P["payload_name"], f"state/{P['cycle']}.json",
        f"The {P['cycle']} scan cycle's payload: every Observation with its stored body "
        f"digest, every Finding with its evidence, the control-fixture records and the "
        f"cycle summary. Written by assessment/harness/scan/run.py; the evidence a Finding "
        f"cites is in corpus/evidence/scan/ and was promoted on publication. Task {TASK}.")
    # UUIDs, not names: `--script-name` and `--data-name` resolve over superseded artifacts
    # too, so a name that was ever duplicated stays unresolvable (see scripts/seldon_artifacts).
    ids = {}
    for _n, _v, sc, dn, _note in data:
        for nm in (sc, dn):
            if nm not in ids:
                ids[nm] = live_artifact(nm)
                if not ids[nm]:
                    raise SystemExit(f"FATAL: no live artifact named {nm!r}; "
                                     f"nothing was registered")
    ok, already, failed = 0, [], []
    for n, v, sc, dn, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description", f"{note} ({TASK})",
                            "--script-id", ids[sc], "--data-ids", ids[dn]],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        elif "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
            already.append(n)
        else:
            failed.append(n)
            print("FAILED:", n, r.stderr.strip()[-240:])
    print(f"registered {ok}, already at this value {len(already)}, failed {len(failed)} "
          f"(of {len(data)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
