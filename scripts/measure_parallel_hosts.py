#!/usr/bin/env python3
"""Wall-clock of the scan, serial and per-host parallel: measured on the controls, projected
for a 16-body cycle. **No network beyond loopback; no model calls.**

`cc_tasks/2026-10-07_parallel_hosts_and_fast_gate.md` decision 4 (DN-013-R2).

MEASURED. The control gate (`run.run_controls`, every pre-registered fixture on its own
loopback server) at the STANDING rate on the real clock, once with `max_parallel_hosts: 1`
(the serial runner, exactly) and once with the default (one worker per fixture).

PROJECTED, and said so. A 16-body cycle from a stored payload's own record, by default the
recollection (`state/scan_2026-10-06_recollect.json`, its RESULT §4): its per-netloc request
counts (`requests_per_host`, counted at the socket by the Fetcher) and its observed span (first
to last surface `captured_at`, controls excluded).

* Serial lower bound: the request total at the standing rate. Not a strict bound (two requests
  to DIFFERENT hosts need no gap between them), but the serial runner rarely alternates hosts,
  and the observed span is printed beside it.
* Parallel lower bound: the largest single netloc at the standing rate. One host cannot be asked
  faster than that, however many workers there are.
* Parallel estimate: each surface netloc's worker ALSO makes the off-host requests its surfaces
  cause (a declared API host, a sibling), so its load is its own host plus a share of the
  others. Each off-host netloc's requests are shared among the surface netlocs in proportion to
  the observations they made of it, and the largest worker's load is costed at the payload's
  observed seconds per request (span / total), which carries response time and the backoffs.
  With more surface netlocs than `run.MAX_PARALLEL_HOSTS`, the bound is also total / ceiling.

    /opt/anaconda3/bin/python3 scripts/measure_parallel_hosts.py [--payload P] [--out J]
    /opt/anaconda3/bin/python3 scripts/measure_parallel_hosts.py --projection-only
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params, run                                   # noqa: E402

DEFAULT_PAYLOAD = REPO / "state" / "scan_2026-10-06_recollect.json"


def time_controls(params: dict, max_parallel_hosts) -> dict:
    """One control gate on the real clock. The evidence goes to a throwaway directory: this is
    not a cycle and holds no licence to the committed store."""
    from scan import model
    p = copy.deepcopy(params)
    p["manners"]["max_parallel_hosts"] = max_parallel_hosts
    with tempfile.TemporaryDirectory(prefix="measure_parallel_hosts_") as tmp:
        prev, model.EVIDENCE_ROOT = model.EVIDENCE_ROOT, Path(tmp)
        try:
            t0 = time.perf_counter()
            cf, e5, obs, ok = run.run_controls(p)
            seconds = time.perf_counter() - t0
        finally:
            model.EVIDENCE_ROOT = prev
    return {"max_parallel_hosts": max_parallel_hosts, "seconds": round(seconds, 2),
            "e5": e5.verdict, "control_findings": len(cf) + 1, "observations": len(obs),
            "fixtures": len(params["e5_control"]["expected_verdicts"]), "gate_passed": ok}


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def project(payload_path: Path, params: dict) -> dict:
    p = json.loads(payload_path.read_text(encoding="utf-8"))
    rph = p["requests_per_host"]
    total = sum(rph.values())
    rate = float(params["manners"]["requests_per_second_per_host"])
    obs = [o for o in p["observations_detail"]
           if not str(o.get("target_doc_id", "")).startswith("control:")]
    stamps = sorted(_iso(o["captured_at"]) for o in obs)
    span = (stamps[-1] - stamps[0]).total_seconds()
    surface_of = {r["doc_id"]: urllib.parse.urlsplit(r["url"]).netloc for r in p["matrix"]}
    surfaces = sorted(set(surface_of.values()))
    # Observations each surface netloc's worker made of each netloc, from the request URL.
    seen: dict = {}
    for o in obs:
        g = surface_of.get(o["target_doc_id"])
        h = urllib.parse.urlsplit((o.get("request") or {}).get("url") or "").netloc
        if g and h:
            seen.setdefault(h, {}).setdefault(g, 0)
            seen[h][g] += 1
    load = {g: 0.0 for g in surfaces}
    unattributed = 0
    for h, n in rph.items():
        share = seen.get(h)
        if h in load:
            load[h] += n
        elif share:
            tot = sum(share.values())
            for g, k in share.items():
                load[g] += n * k / tot
        else:
            unattributed += n
    per_request = span / total
    largest_worker = max(load.items(), key=lambda kv: kv[1])
    ceiling = run.MAX_PARALLEL_HOSTS
    estimate = max(largest_worker[1], total / min(ceiling, len(surfaces))) * per_request
    largest_host = max(rph.items(), key=lambda kv: kv[1])
    return {
        "payload": str(payload_path.relative_to(REPO)), "cycle": p.get("cycle"),
        "kind": "PROJECTION from a stored payload's request counts, not a measurement",
        "surfaces": p["surfaces"], "surface_netlocs": len(surfaces), "netlocs": len(rph),
        "requests_total": total, "rate_per_host": rate,
        "observed_serial_span_seconds": round(span, 1),
        "observed_seconds_per_request": round(per_request, 3),
        "serial_lower_bound_seconds": round(total / rate, 1),
        "largest_netloc": {"netloc": largest_host[0], "requests": largest_host[1]},
        "parallel_lower_bound_seconds": round(largest_host[1] / rate, 1),
        "largest_worker": {"surface_netloc": largest_worker[0],
                           "requests_attributed": round(largest_worker[1], 1)},
        "requests_unattributed": unattributed,
        "parallel_estimate_seconds": round(estimate, 1),
        "speedup_estimate": round(span / estimate, 1),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--payload", default=str(DEFAULT_PAYLOAD))
    ap.add_argument("--out", default=None, help="also write the result here as JSON")
    ap.add_argument("--projection-only", action="store_true",
                    help="skip the two real-clock control gates (several minutes)")
    a = ap.parse_args(argv)
    params = load_params()
    out: dict = {"measured_at": datetime.now().astimezone().isoformat()}
    if not a.projection_only:
        out["control_gate"] = {"serial": time_controls(params, 1),
                               "parallel": time_controls(params, None)}
        print(json.dumps(out["control_gate"], indent=1), flush=True)
    out["projection_16_body_cycle"] = project(Path(a.payload), params)
    print(json.dumps(out["projection_16_body_cycle"], indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    gate = out.get("control_gate")
    if gate and not (gate["serial"]["gate_passed"] and gate["parallel"]["gate_passed"]):
        print("a control gate FAILED; the timing is not of a valid gate", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
