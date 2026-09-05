#!/usr/bin/env python3
"""Register the CQ coverage measurement as Seldon Results (task
2026-09-04_kg_diagnostic_and_cq_harness §1.6). **Zero model spend.**

Every aggregate (`cq_v1_<metric>`) and every per-CQ metric (`cq_v1_<cqid>_<metric>`), each
`computed_from` the dated results DataFile and `generated_by` the Script `run_cq`. A rerun
after a dedup pass — or after new extraction — is a NEW dated file and NEW Results, never an
overwrite (§1.6). The date rides on the DataFile name; the Result name carries a `--suffix`
under the **DD-041** rerun convention (`cq_v1_A_raw_2026-09-04b`), so the un-suffixed names
stay bound to the first run they were measured on and a reader quoting either knows which.

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
          "collapse_shrink", "distinct_entities_raw", "distinct_entities_collapsed",
          # third view (task 2026-09-05_vocabulary_and_entity_linking §4)
          "rows_canonical", "distinct_entities_canonical", "canonical_shrink",
          "dup_groups_canonical")


def rows(date: str, suffix: str = "", version: str = "v1") -> list:
    """`version` names the CQ SET, and rides on every Result name. v2 exists (task
    2026-09-05_vocabulary_and_entity_linking §4) and it changed two questions and added one,
    so pooling its verdicts under `cq_v1_*` would put two instruments' answers under one name
    — the same error the `rubric_version` discipline prevents for the judge."""
    v = version
    recs = [json.loads(l) for l in
            (REPO / "assessment" / "results" / f"cq_{v}_{date}.jsonl").read_text().splitlines() if l.strip()]
    agg = json.loads((REPO / "assessment" / "results" / f"cq_{v}_{date}_aggregates.json").read_text())
    out = []
    out.append((f"cq_{v}_n_cqs", agg["n_cqs"], f"competency questions in set {v}"))
    out.append((f"cq_{v}_A_raw", agg["A_raw"],
                f"fraction of CQs answerable (yes) against the graph AS IT IS. {JUDGED}"))
    out.append((f"cq_{v}_A_collapsed", agg["A_collapsed"],
                f"fraction answerable under the query-time canonical-key + alias collapse. {JUDGED}"))
    out.append((f"cq_{v}_flip", agg["flip"],
                f"fraction of CQs that are no/partial/misleading raw and yes collapsed — the "
                f"pre-registered decision statistic (§1.5). {JUDGED}"))
    out.append((f"cq_{v}_C_dup_groups_unioned_total", agg["C_dup_groups_unioned_total"],
                "total collapse groups of size > 1 the collapsed answers depend on: the Zaveri "
                "et al. 2016 conciseness cost of the whole CQ set. Counted, not judged"))
    out.append((f"cq_{v}_misleading_raw_count", agg["misleading_raw_count"],
                "raw answers non-empty but collapsing by >= 30% of rows — a reader who did not "
                "know duplicates exist would misread them. Counted, not judged"))
    # The third view's aggregates. Registered only when the run computed them, so a rerun of
    # an older set does not emit a row of nulls under a name that reads like a measurement.
    for key, note in (
            ("A_canonical", "fraction answerable in the CANONICAL view — grouped by the "
                            "controlled-vocabulary term each entity RESOLVES_TO. " + JUDGED),
            ("flip_canonical", "flip computed raw -> canonical: §4's acceptance statistic. "
                               + JUDGED),
            ("C_dup_groups_canonical_total", "collapse groups of size > 1 the CANONICAL "
                                             "answers depend on. Counted, not judged")):
        if agg.get(key) is not None:
            out.append((f"cq_{v}_{key}", agg[key], note))
    for cat, c in sorted(agg["by_category"].items()):
        out.append((f"cq_{v}_flip_{cat}", c["flip"],
                    f"flip within the {cat} category ({c['flips']} of {c['n']}). {JUDGED}"))
        out.append((f"cq_{v}_n_{cat}", c["n"], f"CQs in the {cat} category"))
    for r in recs:
        for m in PER_CQ:
            val = r.get(m)          # NOT `v` — that is the set version and shadowing it here
            if val is None:         # renamed every per-CQ Result to `cq_None_*` once already
                continue
            out.append((f"cq_{v}_{r['id'].replace('-', '_')}_{m}", val,
                        f"{r['id']} ({r['category']}) {m}"))
    # One place, so no emitter above can forget it and silently overwrite a prior run's Result.
    return [(name + suffix, value, note) for name, value, note in out]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default="2026-09-04")
    ap.add_argument("--data-name", default=None)
    ap.add_argument("--version", default="v1", help="CQ set version: v1 or v2")
    ap.add_argument("--suffix", default="",
                    help="rerun suffix appended to every Result name, e.g. _2026-09-04b (DD-041)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    data_name = a.data_name or f"cq_{a.version}_{a.date}_results"
    base = (f"Competency-question coverage of the ai-readiness KG, set v1, run {a.date}. "
            f"Method: Grüninger & Fox (1995) competency questions; the duplicate-union cost is "
            f"the conciseness dimension of Zaveri et al. (2016). CQ set pre-registered and "
            f"committed before any query ran. Derivation: assessment/cq/run_cq.py -> "
            f"assessment/results/cq_{a.version}_{a.date}.jsonl ({TASK})")
    data = rows(a.date, a.suffix, a.version)
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
