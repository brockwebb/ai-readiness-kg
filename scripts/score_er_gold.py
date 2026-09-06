#!/usr/bin/env python3
"""Score the operator's filled ER gold sheet against the ER-standard metrics. **Zero spend.**

Task `cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md` §5, under the acceptance rule
recorded as **DD-045 §3**. Written BEFORE the sheet exists, and tested on a synthetic sheet
with known answers, so the scorer cannot be shaped by the answers it will score.

**Why these metrics and not `flip`.** The prior task's acceptance criterion was
`flip(raw -> canonical) < 0.10`, and it was unsatisfiable by construction: `flip` fires on
`misleading_raw`, which is computed from how much the RAW view shrinks, and the raw view is
one node per document per mention because DD-020 requires it. Entity resolution that keeps
per-document nodes can only ever raise it. The record-linkage literature has the right
instrument and has had it for a while — **Menestrina, Whang & Garcia-Molina (2010),
"Evaluating entity resolution results", PVLDB 3(1):208-219**, and the pairwise / B-cubed /
cluster-F1 family in **Christen (2012), *Data Matching*, ch. 7**: pairwise precision and
recall against a human-labelled gold sample, plus a cluster-level measure, because pairwise
alone rewards a system that splits everything.

**Asymmetric thresholds, and the asymmetry is the grounding** (DD-045 §3, operator-declared):
precision >= 0.95, recall >= 0.80. A FALSE MERGE silently corrupts every enumeration CQ — the
merged entity is no longer countable as two — while a MISSED merge surfaces as a duplicate
somebody can see and count. The two errors are not equally expensive, so the thresholds are
not equal.

**Stratified estimation.** The sheet is drawn 20 per stratum from strata of very different
population sizes, so an unweighted pooled rate would be an estimate of nothing. Each stratum
carries weight `w_h = N_h / n_h` and the population estimate is the weighted ratio. The
interval uses Wilson (1927) on the EFFECTIVE sample size — `n_eff = (sum w_h m_h)^2 /
sum (w_h^2 m_h)`, the standard design-effect correction — rather than on the raw count, which
would report a confidence the design does not support.

    /opt/anaconda3/bin/python3 scripts/score_er_gold.py \
        --sheet docs/research/2026-09-05_er_gold_sample.md \
        --key state/er_gold_key.json [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md"

SHEET = REPO / "docs" / "research" / "2026-09-05_er_gold_sample.md"
KEY = REPO / "state" / "er_gold_key.json"
OUT = REPO / "assessment" / "results" / "er_gold_scores_2026-09-05.json"

#: DD-045 §3, operator-declared 2026-09-05. Not adjusted here after seeing a result.
PRECISION_FLOOR = 0.95
RECALL_FLOOR = 0.80

VERDICTS = ("same", "different", "uncertain")

_PAIR_RE = re.compile(r"^\*\*(?P<pid>P\d{3})\s*—\s*verdict\s*\(same\s*/\s*different\s*/\s*"
                      r"uncertain\):\*\*\s*(?P<v>\S*)", re.M | re.I)
_NOTE_RE = re.compile(r"^\*\*(?P<pid>P\d{3})\s*—\s*note:\*\*\s*(?P<n>.*)$", re.M | re.I)


class SheetError(ValueError):
    """The sheet is not in the shape this scorer was written against — fail loud rather than
    score a sheet whose verdicts were silently dropped (standard 4)."""


def parse_sheet(text: str) -> dict:
    """{pair_id: {'verdict': …, 'note': …}}. An unfilled blank parses as None, not as a
    verdict: an unanswered pair must not be counted as agreement with anything."""
    out: dict = {}
    for m in _PAIR_RE.finditer(text):
        raw = (m.group("v") or "").strip().strip("_*").lower()
        out[m.group("pid")] = {"verdict": raw if raw in VERDICTS else None, "note": ""}
    if not out:
        raise SheetError("no '**Pnnn — verdict (same / different / uncertain):**' lines found")
    for m in _NOTE_RE.finditer(text):
        if m.group("pid") in out:
            out[m.group("pid")]["note"] = " ".join((m.group("n") or "").split())[:400]
    return out


def wilson(k: int, n: float, z: float = 1.959963985) -> tuple:
    """Wilson (1927) score interval. `n` may be an EFFECTIVE sample size (a float) — that is
    the whole reason this is not a normal-approximation interval, which goes out of [0,1] and
    degenerates at k = n, exactly where a precision figure is expected to sit."""
    if n <= 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / d
    return (round(max(0.0, centre - half), 6), round(min(1.0, centre + half), 6))


def score(pairs: list) -> dict:
    """pairs: [{pair_id, stratum, system_match: bool, gold: 'same'|'different'|None, weight}]

    `system_match` is what the pipeline decided (these two nodes resolve to one term);
    `gold` is what the operator read. Uncertain and unfilled rows are EXCLUDED from the rates
    and reported as a count — scoring them either way would put the operator's hesitation on
    one side of a threshold.
    """
    usable = [p for p in pairs if p.get("gold") in ("same", "different")]
    by_stratum: dict = collections.defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "n": 0})
    for p in usable:
        c = by_stratum[p["stratum"]]
        c["n"] += 1
        if p["system_match"] and p["gold"] == "same":
            c["tp"] += 1
        elif p["system_match"] and p["gold"] == "different":
            c["fp"] += 1
        elif (not p["system_match"]) and p["gold"] == "same":
            c["fn"] += 1
        else:
            c["tn"] += 1

    weights = {p["stratum"]: p["weight"] for p in pairs}
    strata = {}
    for h, c in sorted(by_stratum.items()):
        prec = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else None
        rec = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else None
        strata[h] = {**c, "weight": weights.get(h),
                     "precision": None if prec is None else round(prec, 6),
                     "recall": None if rec is None else round(rec, 6),
                     "precision_ci": wilson(c["tp"], c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else (None, None),
                     "recall_ci": wilson(c["tp"], c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else (None, None)}

    def weighted(num_key: str, den_keys: tuple) -> dict:
        num = sum(weights.get(h, 1.0) * c[num_key] for h, c in by_stratum.items())
        den = sum(weights.get(h, 1.0) * sum(c[k] for k in den_keys) for h, c in by_stratum.items())
        if den <= 0:
            return {"value": None, "ci": (None, None), "n_eff": 0.0}
        # Effective sample size: (sum w m)^2 / sum (w^2 m) over the rows entering the ratio.
        m = {h: sum(c[k] for k in den_keys) for h, c in by_stratum.items()}
        sw = sum(weights.get(h, 1.0) * m[h] for h in m)
        sw2 = sum((weights.get(h, 1.0) ** 2) * m[h] for h in m)
        n_eff = (sw * sw / sw2) if sw2 else 0.0
        p = num / den
        return {"value": round(p, 6), "ci": wilson(p * n_eff, n_eff), "n_eff": round(n_eff, 3)}

    prec = weighted("tp", ("tp", "fp"))
    rec = weighted("tp", ("tp", "fn"))

    # Cluster F1 over the SAMPLED nodes only, which is what a pair sample can support.
    # Menestrina et al. count a cluster correct only when it matches exactly; the transitive
    # closure of the gold `same` pairs gives the gold clusters, and of the system matches the
    # system clusters. Reported, never a gate: 100 pairs induce very small clusters.
    def clusters(edge_pred) -> set:
        parent: dict = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        nodes = set()
        for p in usable:
            nodes.add(p["node_a"])
            nodes.add(p["node_b"])
            find(p["node_a"]), find(p["node_b"])
        for p in usable:
            if edge_pred(p):
                ra, rb = find(p["node_a"]), find(p["node_b"])
                if ra != rb:
                    parent[rb] = ra
        groups: dict = collections.defaultdict(set)
        for n in nodes:
            groups[find(n)].add(n)
        return {frozenset(v) for v in groups.values()}

    gold_c = clusters(lambda p: p["gold"] == "same")
    sys_c = clusters(lambda p: p["system_match"])
    inter = len(gold_c & sys_c)
    cp = inter / len(sys_c) if sys_c else None
    cr = inter / len(gold_c) if gold_c else None
    cf1 = (2 * cp * cr / (cp + cr)) if (cp and cr) else 0.0

    return {
        "pairs_on_sheet": len(pairs),
        "pairs_scored": len(usable),
        "pairs_uncertain_or_unfilled": len(pairs) - len(usable),
        "by_stratum": strata,
        "precision": prec["value"], "precision_ci": prec["ci"], "precision_n_eff": prec["n_eff"],
        "recall": rec["value"], "recall_ci": rec["ci"], "recall_n_eff": rec["n_eff"],
        "cluster_precision": None if cp is None else round(cp, 6),
        "cluster_recall": None if cr is None else round(cr, 6),
        "cluster_f1": round(cf1, 6),
        "thresholds": {"precision_floor": PRECISION_FLOOR, "recall_floor": RECALL_FLOOR},
        "passes_precision": bool(prec["value"] is not None and prec["value"] >= PRECISION_FLOOR),
        "passes_recall": bool(rec["value"] is not None and rec["value"] >= RECALL_FLOOR),
    }


def load(sheet_path: Path, key_path: Path) -> list:
    key = json.loads(key_path.read_text(encoding="utf-8"))
    filled = parse_sheet(sheet_path.read_text(encoding="utf-8"))
    weights = key["stratum_weights"]
    missing = [p for p in key["pairs"] if p["pair_id"] not in filled]
    if missing:
        raise SheetError(f"{len(missing)} pair(s) on the key are absent from the sheet: "
                         f"{[p['pair_id'] for p in missing][:5]}")
    return [{**p, "gold": filled[p["pair_id"]]["verdict"],
             "note": filled[p["pair_id"]]["note"],
             "weight": weights[p["stratum"]]} for p in key["pairs"]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", default=str(SHEET))
    ap.add_argument("--key", default=str(KEY))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    pairs = load(Path(a.sheet), Path(a.key))
    res = score(pairs)
    res["task"] = TASK
    res["verdict"] = ("PASS" if (res["passes_precision"] and res["passes_recall"]) else "FAIL")
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "by_stratum"}, indent=1))
    if a.dry_run:
        return 0
    if res["pairs_scored"] == 0:
        raise SystemExit("FATAL: no pair carries a verdict; the sheet is unfilled. Nothing "
                         "registered — an unfilled sheet must never register a rate.")
    rows = [
        ("er_gold_precision", res["precision"],
         f"Pairwise PRECISION of the entity-linking pipeline against a human-labelled gold "
         f"sample, stratum-weighted to population (Menestrina, Whang & Garcia-Molina 2010; "
         f"Christen 2012 ch. 7). Wilson 95% CI {res['precision_ci']} on an effective sample "
         f"size of {res['precision_n_eff']}. DD-045 §3 floor {PRECISION_FLOOR}: "
         f"{'PASS' if res['passes_precision'] else 'FAIL'}."),
        ("er_gold_recall", res["recall"],
         f"Pairwise RECALL against the same sample, stratum-weighted. Wilson 95% CI "
         f"{res['recall_ci']} on an effective sample size of {res['recall_n_eff']}. DD-045 §3 "
         f"floor {RECALL_FLOOR} — lower than precision on purpose: a false merge silently "
         f"corrupts every enumeration CQ, a missed merge surfaces as a countable duplicate. "
         f"{'PASS' if res['passes_recall'] else 'FAIL'}."),
        ("er_gold_cluster_f1", res["cluster_f1"],
         "Cluster-level F1 over the sampled nodes: exact-match clusters from the transitive "
         "closure of the gold `same` pairs against the same closure of the pipeline's "
         "matches. Reported, never a gate — 100 pairs induce very small clusters."),
        ("er_gold_verdict", 1.0 if res["verdict"] == "PASS" else 0.0,
         f"1 when both DD-045 §3 thresholds are met, 0 otherwise. Measured: precision "
         f"{res['precision']} (floor {PRECISION_FLOOR}), recall {res['recall']} (floor "
         f"{RECALL_FLOOR}), on {res['pairs_scored']} scored pairs with "
         f"{res['pairs_uncertain_or_unfilled']} uncertain or unfilled and excluded."),
    ]
    ok = 0
    for name, value, note in rows:
        if value is None:
            print("SKIPPED (no value):", name)
            continue
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{note} Derivation: scripts/score_er_gold.py "
                                             f"-> {Path(a.out).name} ({TASK} §5).",
                            "--script-name", "score_er_gold",
                            "--data-name", "er_gold_scores_2026-09-05"],
                           capture_output=True, text=True, cwd=REPO)
        ok += 1 if r.returncode == 0 else 0
        if r.returncode:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(rows)} gold Results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
