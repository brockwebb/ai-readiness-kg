#!/usr/bin/env python3
"""Agreement on the real calibration labels, the genuine-loss RANGE, and their Results
(task 2026-09-03_g1_calibration_rating_agreement, step 2). **Zero model calls.**

`scripts/g1_calibration_agreement.py` is imported and run UNMODIFIED on the filled sheet and
the key; this script adds only what the task asks be registered beside it:

* **the range.** The reviewer's genuine-loss count is never reported alone from here on
  (DD-037's consequence rule). The range is bounded by the SCORER's count — every record in
  the review queue, i.e. the scorer treating every sub-L3/unparseable record as a loss — and
  the RATER-implied count, extrapolated from the 60 sampled records to the pooled Opus grid
  by stratum weights. The reviewer's count sits inside it. No threshold is applied to kappa;
  a low kappa widens the range and triggers nothing.
* **the extrapolation, stated plainly.** Per queue stratum h (scorer level x reviewer
  verdict), p_h = (sampled records the rater put below L3) / (sampled records in h with a
  parseable, non-U level); the implied count is sum_h N_h * p_h over the POOLED grid's
  stratum populations N_h. **The assumption is stratum-homogeneity**: that the rater's
  genuine share inside a stratum is the same in the pooled grid as in the sample. The sample
  mixes pooled-Opus and control-arm records, so the assumption also spans the two grids.
  Both the weights N_h and the rates p_h are registered, so the arithmetic is reproducible
  and the assumption is inspectable rather than buried.
* **the stratum-level agreement table**, so a reader can see where the disagreement lives
  rather than only how large it is.

    /opt/anaconda3/bin/python3 scripts/register_g1_calibration_results.py \
        --sheet assessment/results/g1_calibration_sheet_2026-09-03_filled_fable.md \
        --key assessment/results/.g1_calibration_key_2026-09-03.json [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import g1_calibration_agreement as agree  # noqa: E402

TASK = "cc_tasks/2026-09-03_g1_calibration_rating_agreement.md"
RESULTS = REPO / "assessment" / "results"
POOLED = RESULTS / "g1_v2_pooled_opus_reviewed.json"
PREFIX = "g1_cal_fable"
SCRIPT_NAME = "g1_calibration_agreement"          # Seldon Script 8eca971e


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def pooled_strata() -> dict:
    """(scorer level, reviewer verdict) -> population in the POOLED Opus grid. The sample was
    drawn from pooled + control; the extrapolation target is pooled alone, so the weights are
    recomputed here from the pooled file rather than taken from the sheet's stratum table."""
    doc = json.loads(POOLED.read_text(encoding="utf-8"))
    sizes: dict = {}
    for rec in doc["records"]:
        lv = "unparseable" if rec["outcome"] == "unparseable" else f"L{rec['level']}"
        vd = "not_in_queue" if "review_note" not in rec else ("genuine" if rec["genuine_loss"] else "parser_miss")
        sizes[(lv, vd)] = sizes.get((lv, vd), 0) + 1
    return sizes


def reviewer_counts() -> dict:
    doc = json.loads(POOLED.read_text(encoding="utf-8"))
    rv = doc["review"]
    return {"queue": rv["queue"], "genuine": rv["genuine_losses"], "parser_misses": rv["parser_misses"]}


def stratum_table(sheet: dict, key: dict) -> dict:
    """Per stratum: n sampled, n rated, and raw agreement of the rater with the scorer (exact
    level) and with the reviewer (the implied-verdict rule). U answers are counted, never
    folded into either agreement."""
    rows: dict = {}
    for sid, e in key["key"].items():
        lv, vd = e["scorer_level"], e["reviewer_verdict"]
        r = rows.setdefault((lv, vd), {"n_sampled": 0, "n_rated": 0, "n_U": 0,
                                       "scorer_agree": 0, "reviewer_n": 0, "reviewer_agree": 0,
                                       "rater_below_L3": 0, "rater_L3plus": 0})
        r["n_sampled"] += 1
        lab = (sheet.get(sid) or {}).get("level")
        if lab is None:
            continue
        r["n_rated"] += 1
        if lab == agree.UNCLASSIFIABLE:
            r["n_U"] += 1
            continue
        if lab == lv:
            r["scorer_agree"] += 1
        if agree.ORDINAL[lab] < agree.ORDINAL["L3"]:
            r["rater_below_L3"] += 1
        else:
            r["rater_L3plus"] += 1
        if vd != "not_in_queue":
            r["reviewer_n"] += 1
            if agree.implied_verdict(lab, lv) == vd:
                r["reviewer_agree"] += 1
    out = {}
    for (lv, vd), r in sorted(rows.items(), key=lambda kv: (agree.LEVELS.index(kv[0][0])
                                                           if kv[0][0] in agree.ORDINAL else 5, kv[0][1])):
        scored = r["rater_below_L3"] + r["rater_L3plus"]
        out[f"{lv}|{vd}"] = dict(
            r,
            raw_agreement_with_scorer=(round(r["scorer_agree"] / r["n_rated"], 6) if r["n_rated"] else None),
            raw_agreement_with_reviewer=(round(r["reviewer_agree"] / r["reviewer_n"], 6) if r["reviewer_n"] else None),
            rater_genuine_rate=(round(r["rater_below_L3"] / scored, 6) if scored else None))
    return out


def range_block(strata_rows: dict, weights: dict, reviewer: dict) -> dict:
    """The genuine-loss range on the pooled Opus grid: scorer bound, reviewer count, and the
    rater-implied count extrapolated by stratum weights. Queue strata only — a record the
    scorer put at L3+ was never a candidate loss."""
    per = {}
    implied_genuine = 0.0
    implied_U = 0.0
    covered = 0
    uncovered = []
    for (lv, vd), n_pop in sorted(weights.items()):
        if vd == "not_in_queue":
            continue
        covered += n_pop
        row = strata_rows.get(f"{lv}|{vd}")
        p = (row or {}).get("rater_genuine_rate")
        u_rate = (round(row["n_U"] / row["n_rated"], 6) if row and row["n_rated"] else None)
        if p is None:
            uncovered.append(f"{lv}|{vd}")
        else:
            implied_genuine += n_pop * p
            implied_U += n_pop * (u_rate or 0.0)
        per[f"{lv}|{vd}"] = {"pooled_population": n_pop, "sampled": (row or {}).get("n_sampled"),
                             "rated": (row or {}).get("n_rated"), "rater_genuine_rate": p,
                             "rater_U_rate": u_rate,
                             "implied_genuine": (round(n_pop * p, 3) if p is not None else None)}
    return {
        "grid": "pooled Opus (dev + holdout), pinned consumer claude-opus-5",
        "queue_population": covered,
        "scorer_genuine_losses": reviewer["queue"],
        "reviewer_genuine_losses": reviewer["genuine"],
        "rater_implied_genuine_losses": round(implied_genuine),
        "rater_implied_genuine_losses_exact": round(implied_genuine, 3),
        "rater_implied_U": round(implied_U, 3),
        "strata": per,
        "strata_without_a_rate": uncovered,
        "extrapolation": ("sum over queue strata of (pooled population) x (share of the stratum's "
                          "rated sample the rater put below L3, U excluded). ASSUMES stratum "
                          "homogeneity: that the rater's genuine share within a stratum is the same "
                          "in the pooled grid as in the 60-record sample, which mixes pooled-Opus "
                          "and control-arm records."),
        "consequence_rule": ("DD-037: the reviewer's count is never reported alone; it is reported "
                             "inside the range bounded by the scorer's count and the rater-implied "
                             "count, with kappa stating how wide the disagreement is. No threshold."),
    }


def build(sheet_path: Path, key_path: Path, bootstrap: int, seed: int) -> dict:
    sheet = agree.read_sheet(sheet_path)
    key = json.loads(key_path.read_text(encoding="utf-8"))
    report = agree.analyse(sheet, key, bootstrap, seed)
    rows = stratum_table(sheet, key)
    weights = pooled_strata()
    report["stratum_agreement"] = rows
    report["range"] = range_block(rows, weights, reviewer_counts())
    report["pooled_stratum_weights"] = {f"{lv}|{vd}": n for (lv, vd), n in sorted(weights.items())}
    report["n_U"] = sum(1 for sid in key["key"] if (sheet.get(sid) or {}).get("level") == agree.UNCLASSIFIABLE)
    report["task"] = TASK
    report["rater"] = "claude-fable-5-1"
    report["filled_sheet"] = str(sheet_path.relative_to(REPO))
    return report


def result_rows(r: dict) -> list:
    """(name, value, note) for every number the task asks be registered."""
    out = []
    ovs, six = r["operator_vs_scorer_ordinal"], r["operator_vs_scorer_six_category"]
    ovr = r["operator_vs_reviewer_queue"]

    def add(name, value, note):
        if value is not None:
            out.append((f"{PREFIX}_{name}", value, note))

    add("n_rated", r["labelled"], "sheet records with a parseable rater level (of 60 drawn)")
    add("n_unlabelled", len(r["unlabelled"]) + len(r["missing_from_sheet"]),
        "sheet records with no parseable rater level after one retry")
    add("n_U", r["n_U"], "rater answers of U — the qualifier is stated in a form the rater could not classify")

    add("scorer_kappa_w", ovs["kappa"], "rater vs scorer, Cohen's quadratic-weighted kappa over L0-L4 "
        "(Cohen 1968; Fleiss & Cohen 1973), records where both sides are ordinal")
    add("scorer_kappa_w_ci_lower", ovs["bootstrap95"]["lower"], "percentile bootstrap 2.5th (Efron & Tibshirani 1993)")
    add("scorer_kappa_w_ci_upper", ovs["bootstrap95"]["upper"], "percentile bootstrap 97.5th")
    add("scorer_raw_agreement", ovs["raw_agreement"], "rater vs scorer, exact level match, same records")
    add("scorer_n", ovs["n"], "records in the rater-vs-scorer ordinal comparison")
    add("scorer_kappa_six_category", six["kappa"], "rater vs scorer, UNWEIGHTED kappa over L0-L4 plus one "
        "unparseable/U category (that category has no ordinal position, so it is not weighted)")
    add("scorer_kappa_six_ci_lower", six["bootstrap95"]["lower"], "percentile bootstrap 2.5th")
    add("scorer_kappa_six_ci_upper", six["bootstrap95"]["upper"], "percentile bootstrap 97.5th")
    add("scorer_six_raw_agreement", six["raw_agreement"], "rater vs scorer, six-category exact match")
    add("scorer_six_n", six["n"], "records in the six-category comparison")

    add("reviewer_kappa", ovr["kappa"], "rater vs reviewer on the review queue, unweighted kappa over the "
        "binary {genuine, parser_miss}; the rater's verdict is DERIVED by the pre-registered implied-verdict "
        "rule (a rater level above the scorer's implies parser_miss; equal or below implies genuine)")
    add("reviewer_kappa_ci_lower", ovr["bootstrap95"]["lower"], "percentile bootstrap 2.5th")
    add("reviewer_kappa_ci_upper", ovr["bootstrap95"]["upper"], "percentile bootstrap 97.5th")
    add("reviewer_raw_agreement", ovr["raw_agreement"], "rater vs reviewer, queue records, verdict match")
    add("reviewer_n", ovr["n"], "queue records in the rater-vs-reviewer comparison")
    add("reviewer_positive_agreement_parser_miss", ovr.get("positive_agreement_parser_miss"),
        "positive specific agreement (Dice) on the minority call, the kappa-paradox companion this repo "
        "already uses (scripts/tevv_stability.py; Cicchetti & Feinstein 1990)")
    add("reviewer_excluded_U", ovr.get("excluded_operator_U"),
        "queue records excluded from the verdict comparison because the rater answered U")

    rng = r["range"]
    add("range_scorer_genuine_losses", rng["scorer_genuine_losses"],
        "RANGE upper bound: the scorer's own count — every pooled-grid record it put below L3 or called "
        "unparseable, i.e. the whole review queue")
    add("range_reviewer_genuine_losses", rng["reviewer_genuine_losses"],
        "RANGE middle: the LLM reviewer's genuine-loss count on the pooled grid (never to be reported alone, DD-037)")
    add("range_rater_implied_genuine_losses", rng["rater_implied_genuine_losses"],
        "RANGE other bound: the independent rater's implied count, extrapolated from the 60-record sample to the "
        "pooled grid by stratum weights — " + rng["extrapolation"])
    add("range_rater_implied_U", rng["rater_implied_U"],
        "pooled-grid records the extrapolation implies the rater would call U (reported separately, never folded "
        "into the genuine count)")
    add("range_queue_population", rng["queue_population"], "pooled-grid records in the review queue (the range's denominator)")
    for k, cell in rng["strata"].items():
        add(f"range_weight_{k.replace('|', '_')}", cell["pooled_population"],
            f"stratum weight: pooled-grid population of scorer level x reviewer verdict {k}")
        if cell["rater_genuine_rate"] is not None:
            add(f"range_rate_{k.replace('|', '_')}", cell["rater_genuine_rate"],
                f"share of the {k} sample the rater put below L3 (U excluded); n rated {cell['rated']} of {cell['sampled']} sampled")
    for k, cell in r["stratum_agreement"].items():
        if cell["raw_agreement_with_scorer"] is not None:
            add(f"stratum_agreement_{k.replace('|', '_')}", cell["raw_agreement_with_scorer"],
                f"raw agreement of the rater with the SCORER's exact level inside stratum {k} (n rated {cell['n_rated']})")
            add(f"stratum_n_{k.replace('|', '_')}", cell["n_rated"],
                f"records rated inside stratum {k} (of {cell['n_sampled']} sampled)")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", default=str(RESULTS / "g1_calibration_sheet_2026-09-03_filled_fable.md"))
    ap.add_argument("--key", default=str(RESULTS / ".g1_calibration_key_2026-09-03.json"))
    ap.add_argument("--out", default=str(RESULTS / "g1_calibration_agreement_2026-09-03.json"))
    ap.add_argument("--data-name", default="g1_calibration_sheet_2026-09-03_filled_fable",
                    help="DataFile the Results are computed_from (the filled sheet)")
    ap.add_argument("--bootstrap", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)

    report = build(Path(a.sheet), Path(a.key), a.bootstrap, a.seed)
    Path(a.out).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(agree.render(report))
    rng = report["range"]
    print(f"\ngenuine-loss range on the pooled Opus grid: rater-implied {rng['rater_implied_genuine_losses']} "
          f"— reviewer {rng['reviewer_genuine_losses']} — scorer {rng['scorer_genuine_losses']} "
          f"(queue {rng['queue_population']}; implied U {rng['rater_implied_U']})")
    print(f"report -> {Path(a.out).relative_to(REPO)}")

    # the confusion tables and the stratum table as their own files (registered as DataFiles)
    conf_path = RESULTS / "g1_calibration_confusion_2026-09-03.json"
    conf_path.write_text(json.dumps({
        "task": TASK, "written_at": _now(), "rater": report["rater"],
        "filled_sheet": report["filled_sheet"],
        "rater_vs_scorer_ordinal": {"categories": report["operator_vs_scorer_ordinal"]["categories"],
                                    "confusion": report["operator_vs_scorer_ordinal"]["confusion"]},
        "rater_vs_scorer_six_category": {"categories": report["operator_vs_scorer_six_category"]["categories"],
                                         "confusion": report["operator_vs_scorer_six_category"]["confusion"]},
        "rater_vs_reviewer_queue": {"categories": report["operator_vs_reviewer_queue"]["categories"],
                                    "confusion": report["operator_vs_reviewer_queue"]["confusion"]},
        "reading": "keys are 'rater|other'; the rater's verdict in the queue table is the implied-verdict rule",
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    strat_path = RESULTS / "g1_calibration_stratum_agreement_2026-09-03.json"
    strat_path.write_text(json.dumps({"task": TASK, "written_at": _now(), "rater": report["rater"],
                                      "strata": report["stratum_agreement"],
                                      "pooled_stratum_weights": report["pooled_stratum_weights"],
                                      "range": report["range"]},
                                     indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"confusion tables -> {conf_path.relative_to(REPO)}; stratum table -> {strat_path.relative_to(REPO)}")

    rows = result_rows(report)
    if a.dry_run:
        for name, value, note in rows:
            print(f"{name}\t{value}\t{note[:100]}")
        print(len(rows), "Results")
        return 0
    ok = 0
    rows = rows[a.skip:]
    for name, value, note in rows:
        cmd = ["seldon", "result", "register", "--value", str(value), "--units", name,
               "--description", (f"G1 calibration, independent rater {report['rater']} on the blind sheet "
                                 f"(60 records, seed 20260903), scorer g1-score-v2 / reviewer CC; registered by "
                                 f"scripts/register_g1_calibration_results.py for {TASK}; derivation: "
                                 f"scripts/g1_calibration_agreement.py -> {Path(a.out).relative_to(REPO)}: {note}"),
               "--script-name", SCRIPT_NAME, "--data-name", a.data_name]
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
        if p.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, p.stderr.strip()[-200:])
    print(f"registered {ok}/{len(rows)} calibration Results")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
