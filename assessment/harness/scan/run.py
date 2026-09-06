#!/usr/bin/env python3
"""One scan cycle: controls first (hard stop), then targets. **Zero model calls.**

Task §4 and §6. The control fixtures run BEFORE any real host is touched, and a control that
does not produce its expected verdict aborts the cycle non-zero — DD-019's decoy discipline,
and the instrument's own E5 made operational: *a cycle with zero fired controls is INVALID.*

    /opt/anaconda3/bin/python3 assessment/harness/scan/run.py --controls-only
    /opt/anaconda3/bin/python3 assessment/harness/scan/run.py --smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(REPO))

from scan import load_params                                   # noqa: E402
from scan.model import Observation, params_hash                # noqa: E402
from scan.rules import BY_LEG, judge as judge_rule             # noqa: E402
from scan.runner import collect_leg                            # noqa: E402

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
OUT = REPO / "state" / "scan_smoke_2026-09-06.json"
#: Legs the control fixtures are built to exercise. E5 judges the cycle, not a surface.
CONTROL_LEGS = [l for l in BY_LEG if l != "E5"]


def specs() -> dict:
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    return {n["properties"]["leg"]: n["properties"] for n in g["nodes"]
            if "MeasurementSpec" in n["labels"]}


def run_surface(sp: dict, target: dict, params: dict, legs: list, fetcher=None) -> tuple:
    obs, findings = [], []
    for leg in legs:
        spec = sp.get(leg)
        if spec is None:
            continue
        try:
            o = collect_leg(spec, target, params, fetcher)
        except Exception as exc:                              # a collector defect, recorded
            o = [Observation.make(leg, leg, target["doc_id"], target["url"], "runner", "0.1.0",
                                  params, {"method": "GET", "url": target["url"]},
                                  {"status": None, "headers": {}, "body_sha256": None,
                                   "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                   "error": f"{type(exc).__name__}: {exc}"},
                                  error_class="collector_unavailable")]
        obs += o
        findings.append(judge_rule(BY_LEG[leg], o, params))
    return obs, findings


def run_controls(params: dict) -> tuple:
    """§4's gate. Returns (control_findings, e5_finding, control_observations, ok)."""
    from scan.fixtures.server import FixtureServer
    from scan.manners import Fetcher
    sp = specs()
    all_findings, control_obs, fixture_obs = [], [], []
    for fixture, expected in params["e5_control"]["expected_verdicts"].items():
        with FixtureServer(fixture) as base:
            target = {"doc_id": f"control:{fixture}", "url": f"{base}/index.html"}
            obs, findings = run_surface(sp, target, params, CONTROL_LEGS, Fetcher(params))
        # Retained, not discarded. The re-derivation gate can only check a Finding whose
        # evidence it still holds, and the control Findings are the ones whose determinism
        # matters most — they are what licenses the cycle.
        fixture_obs += obs
        all_findings += findings
        unexpected = [f"{f.leg}={f.verdict}" for f in findings if f.verdict != expected]
        control_obs.append(Observation.make(
            "E5", "E5", f"control:{fixture}", f"fixture://{fixture}", "control_fixture",
            "0.1.0", params, {"method": "FIXTURE", "url": f"fixture://{fixture}"},
            {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 0},
            parsed={"fixture": fixture, "expected": expected,
                    "verdicts": {f.leg: f.verdict for f in findings},
                    "unexpected": unexpected}))
    e5 = judge_rule("RULE-E5-v1", control_obs, params)
    return all_findings, e5, control_obs + fixture_obs, e5.verdict == "pass"


def surfaces() -> list:
    """The 17 product surfaces admitted under epoch g1sfc-2026-09-03, with their primary URLs
    read from the manifest — never a URL typed here."""
    sys.path.insert(0, str(REPO))
    from kg import queue
    members = queue.corpus_epochs().get("g1sfc-2026-09-03") or []
    entries = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"]
    out = []
    for d in sorted(members):
        e = entries.get(d) or {}
        url = ((e.get("identity") or {}).get("source_url") or "")
        if url:
            out.append({"doc_id": d, "url": url})
    return out


def merge_controls(payload_path: Path, params: dict) -> int:
    """Re-run the controls and fold them into an existing payload. **No network, no re-scan.**

    The control fixtures are local and free; the seventeen surfaces are neither. When a change
    affects only what a cycle RECORDS about its controls — not what it measured, and not
    `params_hash` — re-scanning the real hosts would fetch every federal page a third time in
    an afternoon and, worse, would move the `obs_id` of every page that changed in between,
    orphaning findings that are already on the log. This is the same principle as the
    re-derivation gate, applied to the control half of a cycle.

    Refuses across a `params_hash` mismatch: merging control records derived under one
    parameter set into a cycle measured under another would produce a payload whose parts
    disagree about the constants that shaped them.
    """
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    ph = params_hash(params)
    if payload.get("params_hash") != ph:
        print(f"REFUSING: payload params_hash {payload.get('params_hash')!r} != current "
              f"{ph!r}; re-run the whole cycle", file=sys.stderr)
        return 2
    cf, e5, control_obs, ok = run_controls(params)
    print(f"CONTROL GATE: {e5.verdict.upper()} — {e5.reason}")
    if not ok:
        print("cycle INVALID", file=sys.stderr)
        return 2
    # REPLACE, never union. A control run is a whole cycle's worth of canaries, and the
    # fixture server binds an ephemeral port that leaks into every control `target_url` and
    # therefore into every derived control id — so a second control run produces 30 records
    # that are *new* rather than equal. Unioning them made one payload claim two control
    # cycles. The superseded records stay on the append-only log, where an earlier control run
    # belongs; the payload describes the controls this cycle currently stands on.
    payload["control_findings_detail"] = [f.to_dict() for f in cf] + [e5.to_dict()]
    payload["control_findings"] = len(cf) + 1
    payload["observations_detail"] = [
        o for o in payload.get("observations_detail", [])
        if not str(o.get("target_doc_id", "")).startswith("control:")
    ] + [o.to_dict() for o in control_obs]
    payload["control_verdict"], payload["control_reason"] = e5.verdict, e5.reason
    payload_path.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"control_findings": payload["control_findings"],
                      "observations_detail": len(payload["observations_detail"]),
                      "surfaces_rescanned": 0}, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--merge-controls", metavar="PAYLOAD", default=None,
                    help="re-run the control gate ALONE and merge its records into an "
                         "existing cycle payload, without re-measuring a single surface")
    a = ap.parse_args(argv)
    params = load_params()

    if a.merge_controls:
        return merge_controls(Path(a.merge_controls), params)

    cf, e5, control_obs, ok = run_controls(params)
    print(f"CONTROL GATE: {e5.verdict.upper()} — {e5.reason}")
    if not ok:
        print("cycle INVALID; no real host was touched", file=sys.stderr)
        return 2
    if a.controls_only:
        return 0

    sp, tgts = specs(), surfaces()
    if a.limit:
        tgts = tgts[:a.limit]
    from scan.manners import Fetcher
    fetcher = Fetcher(params)
    rows, all_obs, all_find = [], [], []
    for t in tgts:
        obs, findings = run_surface(sp, t, params, CONTROL_LEGS, fetcher)
        all_obs += obs
        all_find += findings
        rows.append({"doc_id": t["doc_id"], "url": t["url"],
                     "verdicts": {f.leg: f.verdict for f in findings}})
        print(f"  {t['doc_id'][:46]:46s} " +
              " ".join(f.verdict[0].upper() for f in findings))

    by_leg_err = {leg: sum(1 for r in rows if r["verdicts"].get(leg) == "error")
                  for leg in CONTROL_LEGS}
    summary = {
        "task": "cc_tasks/2026-09-06_harness_scaffold.md",
        "params_version": params["params_version"], "params_hash": params_hash(params),
        "control_verdict": e5.verdict, "control_reason": e5.reason,
        # +1 for E5's own Finding. The cycle's validity verdict is the single most important
        # record the cycle produces and it was NOT on the event log: `rules_built` said 16 and
        # the projected graph held 15 `:Rule` nodes, because RULE-E5-v1 never emitted one.
        # DD-019 says a cycle with zero fired controls is INVALID; the evidence that THIS
        # cycle was valid has to be as durable as the findings it validates.
        "control_findings": len(cf) + 1,
        "surfaces": len(rows), "legs": len(CONTROL_LEGS),
        "findings": len(all_find), "observations": len(all_obs),
        "verdict_counts": {v: sum(1 for f in all_find if f.verdict == v)
                           for v in ("pass", "fail", "not_applicable", "error")},
        "legs_erroring_on_every_surface": [l for l, n in by_leg_err.items()
                                           if rows and n == len(rows)],
        "matrix": rows,
        "control_findings_detail": [f.to_dict() for f in cf] + [e5.to_dict()],
        "findings_detail": [f.to_dict() for f in all_find],
        "observations_detail": [o.to_dict() for o in all_obs] + [o.to_dict() for o in control_obs],
    }
    OUT.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("matrix", "findings_detail", "observations_detail",
                                   "control_findings_detail")}, indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
