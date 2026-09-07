#!/usr/bin/env python3
"""Register the rule-review and scan-target figures. **Zero model spend.**

Task `cc_tasks/2026-09-06_scan_targets.md` §2 (per-rule Results), §3.3 (host counts) and §5
(progress fractions). Idempotent: a name already taken AT THE SAME VALUE is this script
re-running; at a different value it is drift and stays an error (AD-028).

    /opt/anaconda3/bin/python3 scripts/register_review_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-06_scan_targets.md"
REVIEW = REPO / "assessment" / "results" / "rule_review_2026-09-06.jsonl"
TARGETS = REPO / "state" / "scan_targets_2026-09.json"
PREFLIGHT = REPO / "state" / "scan_preflight_2026-09.json"
PROG = REPO / "docs" / "progress" / "framework_progress_2026-09-06.json"

#: Verdicts are strings and a Result value is numeric, so each per-rule Result carries the
#: verdict as an ORDINAL and names it in the description. A bare 0/1/2 nobody can decode is
#: worse than no Result, which is why the mapping is stated on every row.
ORDINAL = {"conforms": 0, "spec_underspecified": 1, "deviates": 2}


def rows() -> list:
    rv = [json.loads(l) for l in REVIEW.read_text(encoding="utf-8").splitlines() if l.strip()]
    counts = collections.Counter(r["verdict"] for r in rv)
    tg = json.loads(TARGETS.read_text(encoding="utf-8"))
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    pr = json.loads(PROG.read_text(encoding="utf-8"))
    w = pr["whole"]
    out = [
        ("rule_review_conforms", counts["conforms"], "review",
         "Rules whose code implements their MeasurementSpec's signal as written. ZERO of 16 "
         "— the harness RESULT predicted this would be the open question and it was."),
        ("rule_review_deviates", counts["deviates"], "review",
         "Rules that fail to implement a clause of their signal, or implement something the "
         "signal does not authorise, with the clause and the code line both quoted. Twelve "
         "were confirmed by hand against the collector and got a v2 module; one (G1-D) did "
         "NOT survive verification — its clause is satisfied in runner.py, which the reviewer "
         "was not shown."),
        ("rule_review_underspecified", counts["spec_underspecified"], "review",
         "Rules that had to settle something the signal does not (A4, A5, A9). No code "
         "change: the decision is written into the MeasurementSpec as a `decision` property, "
         "so the gap closes in the framework of record rather than in a Python module."),
        ("rule_review_deviations_confirmed", 12, "review",
         "Deviations that survived verification against the collector and the runner before "
         "any v2 was written. A model finding is a finding to verify, not a verdict to obey."),
        ("rule_v2_modules_written", 12, "review",
         "New rule modules at v2. NOT ONE v1 line was edited: a stored Finding must re-derive "
         "under the rule that made it, so rules/__init__ carries REGISTRY (every version ever "
         "shipped) beside CURRENT (what a new cycle judges with)."),
        ("scan_targets_hosts", pf["hosts"], "targets",
         "Hosts pre-flighted: the 13 U.S. principal statistical agencies enumerated by OMB "
         "Statistical Policy Directive No. 1 (spd_1, segments s22-s39, read from the "
         "fss-policy-kg corpus) plus the StatCan comparator already admitted here."),
        ("scan_targets_hosts_unobservable", pf["hosts_unobservable"], "targets",
         f"Hosts that answered 401/403/429 to an identified, rate-limited, robots-obeying "
         f"client on EVERY probe: {', '.join(pf['hosts_unobservable_ids'])}. Their own "
         f"robots.txt permits the paths. They stay on the target list and their surfaces will "
         f"produce `error` Findings; this is the observation A12 was raised to name."),
        ("scan_targets_surfaces", tg["surfaces"], "targets",
         f"Surfaces on the target list: {tg['by_kind']['flagship']} flagship product pages, "
         f"{tg['by_kind']['machine']} machine entry points, {tg['by_kind']['well_known']} "
         f"agency-level well-known sets (synthetic, one per host, not documents)."),
        ("scan_targets_admitted", 26, "targets",
         "Surfaces admitted to corpus/manifest.json under epoch scan-2026-09. OBSERVED_ON "
         "requires a :Document, so an unadmitted target cannot be scanned. One EIA surface is "
         "NOT admitted: eia.gov/robots.txt disallows it for this UA and the scanner obeys the "
         "file it measures."),
        ("scan_targets_listings_unreadable", len(pf["listings_unreadable"]), "targets",
         f"Agencies whose own data listing could not be read: "
         f"{', '.join(pf['listings_unreadable'])}. Three are refusals; NCES's data-tools page "
         f"returns HTTP 200 and three links, because it is client-rendered. Each contributes "
         f"only its well-known set; no flagship was substituted from elsewhere."),
        ("framework_candidate_indicators", (pr.get("candidates") or {}).get("n", 0), "progress",
         "Indicators at status=candidate: proposed, NOT adopted, excluded from every "
         "numerator and every denominator, rendered in their own table (DD-054)."),
        ("framework_specs_with_recorded_decision", 3, "progress",
         "MeasurementSpecs carrying an explicit `decision` property naming what the rule had "
         "to settle that the signal does not (A4, A5, A9)."),
        ("framework_indicators_harness_built_after_review",
         w["by_measurement_status"]["harness_built"]["n"], "progress",
         f"Indicators at harness_built of {w['indicators']}, after the review. Unchanged by "
         f"the review, and that is correct: a v2 rule is still a harness, not a measurement."),
    ]
    for r in sorted(rv, key=lambda r: r["leg"]):
        out.append((f"rule_review_{r['leg'].replace('-', '_').lower()}",
                    ORDINAL[r["verdict"]], "review",
                    f"{r['rule_id']} reviewed against its MeasurementSpec: "
                    f"**{r['verdict']}** (ordinal 0=conforms, 1=spec_underspecified, "
                    f"2=deviates; confidence {r.get('confidence')}). "
                    f"{(r.get('finding') or '')[:400]}"))
    return out


SCRIPT = {"review": "rule_review", "targets": "build_scan_targets",
          "progress": "framework_progress"}
DATA = {"review": "rule_review_2026-09-06", "targets": "scan_targets_2026-09",
        "progress": "framework_progress_2026-09-06"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for n, v, s, note in data:
            print(f"{n}\t{v}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    ok, already, failed = 0, [], []
    for n, v, s, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(v), "--name", n,
                            "--units", n, "--description", f"{note} ({TASK})",
                            "--script-name", SCRIPT[s], "--data-name", DATA[s]],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        elif "unique per project graph" in r.stderr and f"value={float(v)}" in r.stderr:
            already.append(n)
        else:
            failed.append(n)
            print("FAILED:", n, r.stderr.strip()[-200:])
    print(f"registered {ok}, already at this value {len(already)}, failed {len(failed)} "
          f"(of {len(data)})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
