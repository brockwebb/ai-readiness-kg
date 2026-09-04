#!/usr/bin/env python3
"""Register the CQ coverage measurement as Seldon Results (task
2026-09-04_kg_diagnostic_and_cq_harness §1.6). **Zero model spend.**

Every aggregate (`cq_v1_<metric>`) and every per-CQ metric (`cq_v1_<cqid>_<metric>`), each
`computed_from` the dated results DataFile and `generated_by` the Script `run_cq`. A rerun
after a dedup pass is a NEW dated file and NEW Results — never an overwrite (§1.6), which is
why the date is in the name of the data file and not in the Result name.

**Every answerability-derived Result says in its description that the verdict is an LLM
judge's.** `A_raw`, `A_collapsed` and `flip` all rest on that judgement; the row counts,
duplicate-group counts and provenance fractions do not.

    /opt/anaconda3/bin/python3 assessment/cq/register_cq_results.py --date 2026-09-04 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TASK = "cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md"

JUDGED = ("Verdict by an LLM judge (the session that authored the CQ set read the returned "
          "grounding spans against pass criteria written before any query ran, §1.7)")

#: per-CQ numeric metrics worth a Result of their own
PER_CQ = ("rows_raw", "rows_collapsed", "dup_groups_unioned", "provenance_complete",
          "collapse_shrink", "distinct_entities_raw", "distinct_entities_collapsed")


def rows(date: str) -> list:
    recs = [json.loads(l) for l in
            (REPO / "assessment" / "results" / f"cq_v1_{date}.jsonl").read_text().splitlines() if l.strip()]
    agg = json.loads((REPO / "assessment" / "results" / f"cq_v1_{date}_aggregates.json").read_text())
    out = []
    out.append(("cq_v1_n_cqs", agg["n_cqs"], "competency questions in set v1"))
    out.append(("cq_v1_A_raw", agg["A_raw"],
                f"fraction of CQs answerable (yes) against the graph AS IT IS. {JUDGED}"))
    out.append(("cq_v1_A_collapsed", agg["A_collapsed"],
                f"fraction answerable under the query-time canonical-key + alias collapse. {JUDGED}"))
    out.append(("cq_v1_flip", agg["flip"],
                f"fraction of CQs that are no/partial/misleading raw and yes collapsed — the "
                f"pre-registered decision statistic (§1.5). {JUDGED}"))
    out.append(("cq_v1_C_dup_groups_unioned_total", agg["C_dup_groups_unioned_total"],
                "total collapse groups of size > 1 the collapsed answers depend on: the Zaveri "
                "et al. 2016 conciseness cost of the whole CQ set. Counted, not judged"))
    out.append(("cq_v1_misleading_raw_count", agg["misleading_raw_count"],
                "raw answers non-empty but collapsing by >= 30% of rows — a reader who did not "
                "know duplicates exist would misread them. Counted, not judged"))
    for cat, c in sorted(agg["by_category"].items()):
        out.append((f"cq_v1_flip_{cat}", c["flip"],
                    f"flip within the {cat} category ({c['flips']} of {c['n']}). {JUDGED}"))
        out.append((f"cq_v1_n_{cat}", c["n"], f"CQs in the {cat} category"))
    for r in recs:
        for m in PER_CQ:
            v = r.get(m)
            if v is None:
                continue
            out.append((f"cq_v1_{r['id'].replace('-', '_')}_{m}", v,
                        f"{r['id']} ({r['category']}) {m}"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default="2026-09-04")
    ap.add_argument("--data-name", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    data_name = a.data_name or f"cq_v1_{a.date}_results"
    base = (f"Competency-question coverage of the ai-readiness KG, set v1, run {a.date}. "
            f"Method: Grüninger & Fox (1995) competency questions; the duplicate-union cost is "
            f"the conciseness dimension of Zaveri et al. (2016). CQ set pre-registered and "
            f"committed before any query ran. Derivation: assessment/cq/run_cq.py -> "
            f"assessment/results/cq_v1_{a.date}.jsonl ({TASK})")
    data = rows(a.date)
    if a.dry_run:
        for name, value, note in data:
            print(f"{name}\t{value}\t{note[:90]}")
        print(len(data), "Results")
        return 0
    ok = 0
    data = data[a.skip:]
    for name, value, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{base}: {note}",
                            "--script-name", "run_cq", "--data-name", data_name],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} CQ Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
