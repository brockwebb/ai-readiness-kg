#!/usr/bin/env python3
"""Register the homograph pass, the loader-fix label counts, and the gold-sample design.
**Zero model spend.**

Task `cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md` §1, §4, §5. DD-040: every
quoted figure resolves to a named Result and the path that produced it re-runs. Each number
here is read back off an artifact on disk, never recomputed in this script.

    /opt/anaconda3/bin/python3 scripts/register_homograph_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md"

HOMO = REPO / "state" / "homograph_scores_2026-09-05.json"
LABELS = REPO / "state" / "vocab_label_counts_2026-09-05.json"
GOLDKEY = REPO / "state" / "er_gold_key.json"

SCRIPT = {"homograph": "homograph_split", "labels": "build_projection",
          "gold": "build_er_gold_sample"}
DATA = {"homograph": "homograph_scores_2026-09-05", "labels": "vocab_label_counts_2026-09-05",
        "gold": "er_gold_key_2026-09-05"}


def rows() -> list:
    h = json.loads(HOMO.read_text(encoding="utf-8"))
    lab = json.loads(LABELS.read_text(encoding="utf-8"))
    g = json.loads(GOLDKEY.read_text(encoding="utf-8"))
    c = h["counts"]
    out = [
        ("homograph_cross_arm_terms", h["cross_arm_terms"], "homograph",
         "Active vocabulary terms whose RESOLVES_TO members span two or more Document "
         "construct arms — the population the homograph pass scores. The task premise says "
         "289 and this measures 289."),
        ("homograph_cross_arm_nodes", h["cross_arm_nodes"], "homograph",
         "Member nodes behind those terms. The task premise says 1,666; this measures 1,660. "
         "The 6-node gap is the Claim/Practice twins: members are read per (term, node label) "
         "because DD-020's <doc_id>::<item_id> is not unique across types, so reading by key "
         "alone pulls a Claim into a Concept term's evidence."),
        ("homograph_auto_split_terms", c.get("auto_split", 0), "homograph",
         "Terms below both pre-registered thresholds (cross-arm mean < 0.80 AND s < -0.10). "
         "NOT WRITTEN: the §1.3 positive control failed, so no split reached the vocabulary."),
        ("homograph_auto_keep_terms", c.get("auto_keep", 0), "homograph",
         "Terms the thresholds kept as one sense (cross-arm mean >= 0.80 OR s >= 0). 12 of "
         "these clear the 0.80 limb; the other 67 reach auto-keep only on `s >= 0`, and 61 of "
         "those 67 have an arm holding fewer than three members, where `s` is noise."),
        ("homograph_candidate_terms", h["band_size"], "homograph",
         "The clerical band — the unit count the §2 ceiling would have been computed from. "
         "Below the §1.2 stop threshold of 150, so the band size was not itself a stop."),
        ("homograph_scored_on_cross_only", h["scored_on_cross_only"], "homograph",
         "Terms where no arm holds two members, so `within` is undefined and `s` cannot be "
         "computed; scored on the cross-arm mean alone, per §1.1. 82 of 289 — 28% of the "
         "population is scored on half the statistic."),
        ("homograph_positive_control_failed",
         0 if h["positive_control_passed"] else 1, "homograph",
         f"§1.3 GATE. 1 when any of the three known-homographic readiness terms lands in "
         f"auto-keep. Measured: {h['positive_control']}. `air:concept/ai-ready` reached "
         f"auto-keep on the `s >= 0` limb (cross 0.556, within 0.452, s +0.104) because its "
         f"arms hold 2, 4 and 1 members and a within-arm mean over two nodes is noise. The "
         f"gate did its job: the thresholds are wrong, so NOTHING was written to the "
         f"vocabulary log and Phase B was not run."),
        ("vocab_resolved_total", lab["resolved_total"], "labels",
         "Distinct nodes carrying a RESOLVES_TO edge after the §2.3 loader fix."),
        ("vocab_unresolved_total", lab["unresolved_total"], "labels",
         "Nodes carrying `unresolved: true` after the §2.3 loader fix."),
        ("er_gold_pairs", len(g["pairs"]), "gold",
         f"Pairs on the operator's blind gold sheet, {g['per_stratum']} from each of five "
         f"strata, seed {g['seed']}. The sheet shows no cosine, no term, no stratum and no "
         f"pipeline decision; those live in state/er_gold_key.json and join at scoring time."),
    ]
    for lbl, n in sorted(lab["resolved_by_label"].items()):
        out.append((f"vocab_resolved_by_label_{lbl}", n, "labels",
                    f"{lbl} nodes carrying a RESOLVES_TO edge after the §2.3 loader fix."))
    for lbl, n in sorted(lab["unresolved_by_label"].items()):
        out.append((f"vocab_unresolved_by_label_{lbl}", n, "labels",
                    f"{lbl} nodes carrying `unresolved: true` after the §2.3 loader fix."))
    for h_, n in sorted(g["stratum_population"].items()):
        out.append((f"er_gold_stratum_population_{h_}", n, "gold",
                    f"Population of gold stratum {h_} ({g['strata'][h_]}); the sampling weight "
                    f"is this over the {g['stratum_drawn'][h_]} drawn."))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for name, value, src, note in data:
            print(f"{name}\t{value}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    ok = 0
    for name, value, src, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{note} Derivation: scripts/{SCRIPT[src]}.py "
                                             f"({TASK}).",
                            "--script-name", SCRIPT[src], "--data-name", DATA[src]],
                           capture_output=True, text=True, cwd=REPO)
        ok += 1 if r.returncode == 0 else 0
        if r.returncode:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
