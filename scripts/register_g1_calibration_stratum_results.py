#!/usr/bin/env python3
"""Register the per-stratum agreement COUNTS from the G1 calibration (task
2026-09-03_g1_memo_v1_2_level_caveat, step 1). **Zero model calls.**

`scripts/register_g1_calibration_results.py` registered each stratum's agreement RATE with the
scorer and its rated `n`. The memo now has to say "the rater matched the scorer's exact level on
0 of 5 L2 records" and "on all 18 preserved-exact records", and it may not write a literal — so
the numerators, the reviewer-side counts, and the two aggregates that carry the calibration's
grain finding are registered here, read from the stratum table the agreement run already wrote
rather than recomputed:

    g1_cal_fable_stratum_scorer_agreed_<level>_<verdict>       rated records where the rater's
                                                              exact level equals the scorer's
    g1_cal_fable_stratum_reviewer_n_<level>_<verdict>          queue records in the verdict
                                                              comparison for that stratum
    g1_cal_fable_stratum_reviewer_agreed_<level>_<verdict>     of those, verdicts that matched
    g1_cal_fable_stratum_reviewer_agreement_<level>_<verdict>  that as a rate (queue strata only)
    g1_cal_fable_preserved_exact_n / _agreed                   the L4 stratum, the grain the two
                                                              instruments agree on
    g1_cal_fable_parser_miss_reviewer_n / _agreed              the four parser-miss strata pooled

Nothing is recomputed and no existing Result is touched: the source is
`assessment/results/g1_calibration_stratum_agreement_2026-09-03.json`, itself produced by
`scripts/g1_calibration_agreement.py` (unmodified) through the step-2 registration script.

    /opt/anaconda3/bin/python3 scripts/register_g1_calibration_stratum_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "assessment" / "results" / "g1_calibration_stratum_agreement_2026-09-03.json"
TASK = "cc_tasks/2026-09-03_g1_memo_v1_2_level_caveat.md"
PREFIX = "g1_cal_fable"
BASE = ("G1 calibration, independent rater claude-fable-5-1 against the frozen scorer g1-score-v2 "
        "and the v2 LLM reviewer, on the 60-record blind sample (seed 20260903); registered by "
        f"scripts/register_g1_calibration_stratum_results.py for {TASK}; source: "
        "assessment/results/g1_calibration_stratum_agreement_2026-09-03.json")


def rows() -> list:
    strata = json.loads(SOURCE.read_text(encoding="utf-8"))["strata"]
    out = []
    pm_n = pm_agreed = 0
    for key, cell in strata.items():
        lv, vd = key.split("|")
        slug = f"{lv}_{vd}"
        out.append((f"{PREFIX}_stratum_scorer_agreed_{slug}", cell["scorer_agree"],
                    f"strata.{key}.scorer_agree: rated records in stratum {key} where the rater's exact "
                    f"level equals the scorer's (of {cell['n_rated']} rated, {cell['n_sampled']} sampled)"))
        out.append((f"{PREFIX}_stratum_reviewer_n_{slug}", cell["reviewer_n"],
                    f"strata.{key}.reviewer_n: records of stratum {key} in the rater-vs-reviewer verdict "
                    f"comparison (0 for a stratum the reviewer never judged)"))
        out.append((f"{PREFIX}_stratum_reviewer_agreed_{slug}", cell["reviewer_agree"],
                    f"strata.{key}.reviewer_agree: of those, verdicts that matched under the "
                    f"pre-registered implied-verdict rule"))
        if cell["raw_agreement_with_reviewer"] is not None:
            out.append((f"{PREFIX}_stratum_reviewer_agreement_{slug}", cell["raw_agreement_with_reviewer"],
                        f"strata.{key}.raw_agreement_with_reviewer: that as a rate"))
        if vd == "parser_miss":
            pm_n += cell["reviewer_n"]
            pm_agreed += cell["reviewer_agree"]
    l4 = strata["L4|not_in_queue"]
    out.append((f"{PREFIX}_preserved_exact_n", l4["n_rated"],
                "rated sample records the scorer put at L4 (preserved_exact)"))
    out.append((f"{PREFIX}_preserved_exact_agreed", l4["scorer_agree"],
                "of those, records the independent rater also put at L4 — the grain at which the two "
                "instruments agree completely"))
    out.append((f"{PREFIX}_parser_miss_reviewer_n", pm_n,
                "sampled queue records the reviewer called a parser miss (the four parser_miss strata pooled)"))
    out.append((f"{PREFIX}_parser_miss_reviewer_agreed", pm_agreed,
                "of those, records where the rater's implied verdict was also a parser miss"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for name, value, note in data:
            print(f"{name}\t{value}\t{note[:100]}")
        print(len(data), "Results")
        return 0
    ok = 0
    data = data[a.skip:]
    for name, value, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value), "--units", name,
                            "--description", f"{BASE}: {note}",
                            "--script-name", "g1_calibration_agreement",
                            "--data-name", "g1_calibration_stratum_agreement_2026-09-03"],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-200:])
    print(f"registered {ok}/{len(data)} stratum-count Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
