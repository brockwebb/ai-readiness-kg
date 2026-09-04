#!/usr/bin/env python3
"""Draw the blind reviewer-calibration sample for G1 EVAL v2 (task
2026-09-03_g1_freeze_calibration_redefinition_findings, step 1). **Zero model calls.**

Why this exists. The v2 genuine-loss counts come from an LLM reviewer (`review.reviewer`
= "CC") whose agreement with the operator has never been measured; every number that rests
on them is uncalibrated until it is. Prior art for the measurement is standard and is
adopted rather than re-derived. This repo has measured agreement before —
`scripts/tevv_stability.py` (Cohen's kappa on item presence, with the kappa-paradox remedy of
Cicchetti & Feinstein 1990) and the Results named `kappa` under tasks `de7ae80b` / `68426971`
— and `scripts/g1_calibration_agreement.py` follows it. From the literature: Cohen (1960)
kappa, Cohen (1968) weighted kappa with Fleiss & Cohen (1973) for the quadratic weights on an
ordinal scale, Efron & Tibshirani (1993) for the percentile bootstrap, and Han et al.,
"Judge's Verdict" (arXiv:2510.09738; Wintermute `harvest-arxiv-e2a16615`) for measuring an LLM
judge by its agreement with human labels rather than by its own confidence.

The stratification is not decoration: 372 of the 778 records are L4 and 178 are the reviewer's
genuine losses, so a simple random sample of 60 would spend most of its labels on the cell
nobody disputes and leave the disputed cells at single digits.

What this script does. It reads the reviewed pooled-Opus v2 results file and the control-arm
file, strata-samples records, and writes a sheet the operator can label WITHOUT seeing what
the scorer or the reviewer decided:

  strata   = scorer level {L0, L1, L2, L3, L4, unparseable} x reviewer verdict
             {genuine, parser_miss, not_in_queue}
  n        = 60, proportional allocation with a floor of 3 per NON-EMPTY stratum
             (largest-remainder on the residual after the floor; capped at stratum size)
  seed     = fixed, printed as the first block of the sheet

The sheet carries only: sample id, the exact prompt text the consumer saw, the response
verbatim, the estimate's label and value, the qualifier family and the forms the source
published, the elicitation mode and the compression level. It does NOT carry the scorer's
level, the reviewer's verdict, the failure class, the surface type or the model id. The
mapping sample id -> record lives in a separate gitignored key file that the sheet never
references.

    /opt/anaconda3/bin/python3 scripts/g1_calibration_sample.py [--n 60] [--seed 20260903] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "scripts"))

from run_g1_v2 import load_all_fixtures  # noqa: E402

TASK = "cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md"
RESULTS = REPO / "assessment" / "results"
SOURCES = (("pooled_opus", RESULTS / "g1_v2_pooled_opus_reviewed.json"),
           ("control", RESULTS / "g1_v2_control_reviewed.json"))
SHEET_MD = RESULTS / "g1_calibration_sheet_2026-09-03.md"
SHEET_CSV = RESULTS / "g1_calibration_sheet_2026-09-03.csv"
KEY = RESULTS / ".g1_calibration_key_2026-09-03.json"

LEVELS = ("L0", "L1", "L2", "L3", "L4", "unparseable")
VERDICTS = ("genuine", "parser_miss", "not_in_queue")

# Verbatim from DD-033 decision 1 (the D2 level scale) — quoted, not paraphrased, because the
# labeler must apply the same definitions the scorer was given.
D2_VERBATIM = (
    "L4 preserved_exact (class, value within published rounding, confidence level and binding "
    "all restated); L3 preserved_transformed (numeric and correct under a legitimate "
    "transformation — MOE↔bounds, ±↔interval, percent↔fraction, precision that rounds back to "
    "the source's, and, in v0, a right value with the confidence level omitted); L2 "
    "degraded_verbal (verbal band, no number); L1 omitted; L0 corrupted (magnitude outside "
    "published rounding with `widened`/`narrowed` recorded, wrong level, wrong binding, "
    "fabricated qualifier, suppressed or flagged-unreliable estimate restated as usable)."
)
# Verbatim from DD-035 decision 1 (D9 families).
D9_VERBATIM = (
    "{SE, MOE, CI} = `interval`, {CV} = `relative`, {RELIABILITY_FLAG, SUPPRESSION} = "
    "`reliability`, {DP_NOISE} = `dp`, {VINTAGE} = `vintage` … The record unit is "
    "(proposition, family, mode[, compression]); the family level is the best level any "
    "published form achieved."
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def level_key(rec: dict) -> str:
    return "unparseable" if rec["outcome"] == "unparseable" else f"L{rec['level']}"


def verdict_key(rec: dict) -> str:
    """The reviewer's verdict. Only records in the review queue (L0/L1/L2/unparseable) carry a
    `review_note`; everything else was never put to the reviewer and is `not_in_queue`."""
    if "review_note" not in rec:
        return "not_in_queue"
    return "genuine" if rec.get("genuine_loss") else "parser_miss"


def allocate(sizes: dict, n: int, floor: int) -> dict:
    """Proportional allocation with a floor per non-empty stratum.

    Floor first (capped at the stratum's size), then the residual by largest remainder on the
    population shares, never exceeding a stratum's size. Raises if the population cannot fill
    the request — silence here would produce a short sheet nobody notices (standard 4).
    """
    live = {k: v for k, v in sizes.items() if v > 0}
    total = sum(live.values())
    if total < n:
        raise SystemExit(f"FATAL: population {total} < requested sample {n}")
    alloc = {k: min(floor, v) for k, v in live.items()}
    residual = n - sum(alloc.values())
    if residual < 0:
        raise SystemExit(f"FATAL: floor {floor} x {len(live)} non-empty strata exceeds n={n}")
    shares = {k: residual * v / total for k, v in live.items()}
    whole = {k: int(s) for k, s in shares.items()}
    for k, w in whole.items():
        take = min(w, live[k] - alloc[k])
        alloc[k] += take
    left = n - sum(alloc.values())
    order = sorted(live, key=lambda k: (-(shares[k] - whole[k]), -live[k], k))
    i = 0
    while left > 0:
        if i >= len(order) * 3:
            raise SystemExit("FATAL: cannot place the residual without exceeding a stratum size")
        k = order[i % len(order)]
        if alloc[k] < live[k]:
            alloc[k] += 1
            left -= 1
        i += 1
    return alloc


def load_population() -> list:
    pop = []
    for split, path in SOURCES:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for i, rec in enumerate(doc["records"]):
            pop.append({"split": split, "file": str(path.relative_to(REPO)), "index": i, "record": rec})
    return pop


def published_forms(prop, family: str, fam_of: dict) -> str:
    """The forms the SOURCE published for this family, with their printed values — the ground
    truth the labeler needs. Never the model's output, never a scorer verdict."""
    out = []
    for q in prop.qualifiers:
        cls = q.cls.value if hasattr(q.cls, "value") else str(q.cls)
        if fam_of.get(cls) != family:
            continue
        f = dict(q.fields)
        bits = [f"{cls}"]
        if f.get("text") is not None:
            bits.append(f"= {f['text']}")
        elif f.get("value") is not None:
            bits.append(f"= {f['value']}")
        extra = {k: v for k, v in f.items() if k not in ("text", "value")}
        if extra:
            bits.append("(" + ", ".join(f"{k}={v}" for k, v in sorted(extra.items())) + ")")
        out.append(" ".join(bits))
    return "; ".join(out) if out else "(none recorded on the proposition)"


def build_rows(sample: list, props: dict, fam_of: dict) -> list:
    rows = []
    for sid, item in sample:
        rec = item["record"]
        ev = json.loads((REPO / rec["evidence_path"]).read_text(encoding="utf-8"))
        prop = props[rec["target"]]
        rows.append({
            "sample_id": sid,
            "mode": rec["mode"],
            "compression_level": rec.get("compression_level") or "(n/a — direct mode)",
            "estimate_label": prop.estimate.get("label", ""),
            "estimate_value": prop.estimate.get("text", ""),
            "qualifier_family": rec["family"],
            "published_forms": published_forms(prop, rec["family"], fam_of),
            "prompt_shown": ev["prompt"],
            "response": ev["response_text"],
        })
    return rows


def sheet_markdown(rows: list, header: dict) -> str:
    n = len(rows)
    L = []
    L.append("# G1 EVAL v2 — reviewer calibration sheet (blind)\n")
    L.append(f"**Drawn:** {header['drawn_at']} · **Task:** `{TASK}` · **Zero model calls.**\n")
    L.append("## Draw\n")
    L.append(f"- **Seed:** `{header['seed']}` (Python `random.Random(seed)`, stratum draws in the "
             f"stratum order printed below, then one final shuffle to assign sample ids).")
    L.append(f"- **Population:** {header['population']} family records — "
             f"`assessment/results/g1_v2_pooled_opus_reviewed.json` ({header['by_split']['pooled_opus']}) "
             f"and `assessment/results/g1_v2_control_reviewed.json` ({header['by_split']['control']}).")
    L.append(f"- **Sample:** {n}, stratified by scorer level × reviewer verdict, proportional "
             f"allocation with a floor of {header['floor']} per non-empty stratum "
             f"(largest remainder on the residual, capped at stratum size).")
    L.append(f"- **Structurally empty strata (no allocation):** {header['empty_note']}\n")
    L.append("| stratum (level × verdict) | population | allocated |")
    L.append("|---|---:|---:|")
    for k, size in header["strata"]:
        L.append(f"| {k[0]} × {k[1]} | {size} | {header['alloc'].get(k, 0)} |")
    L.append(f"| **total** | **{header['population']}** | **{n}** |\n")
    L.append("## What to do\n")
    L.append("For each record below you see exactly what the consumer saw (the prompt), exactly what "
             "it answered (the response), and what the source published for one qualifier family "
             "attached to one estimate. Read the response in full and decide which preservation level "
             "that response achieved **for that family and that estimate** — not for the response as a "
             "whole, and not for any other number in it. Write the level on the answer line, and a "
             "short note if the record is not clean (a form you had to convert, a value bound to the "
             "wrong row, a qualifier stated about something else). Write **U** if the qualifier is "
             "stated in a form you cannot classify at all. Nothing here tells you what the scorer or "
             "the reviewer decided; that is the point, so please do not go looking before you finish.\n")
    L.append("**The level scale (D2, verbatim from DD-033):** " + D2_VERBATIM + "\n")
    L.append("**Qualifier families (D9, verbatim from DD-035):** " + D9_VERBATIM + "\n")
    L.append("**Question, once per record:** which level (L0–L4) did the response achieve for this "
             "family, or U if the qualifier is stated in a form you cannot classify?\n")
    L.append("---\n")
    for r in rows:
        L.append(f"## {r['sample_id']}\n")
        L.append(f"- **Estimate:** {r['estimate_label']} — **{r['estimate_value']}**")
        L.append(f"- **Qualifier family:** `{r['qualifier_family']}` · **published forms:** {r['published_forms']}")
        L.append(f"- **Mode:** {r['mode']} · **Compression:** {r['compression_level']}\n")
        L.append("**Prompt shown to the consumer:**\n")
        L.append("```text")
        L.append(r["prompt_shown"].rstrip())
        L.append("```\n")
        L.append("**Response:**\n")
        L.append("```text")
        L.append(r["response"].rstrip())
        L.append("```\n")
        L.append(f"**{r['sample_id']} — Level (L0 / L1 / L2 / L3 / L4 / U):** ______\n")
        L.append(f"**{r['sample_id']} — Note:** ______\n")
        L.append("---\n")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--floor", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="print the strata and the allocation, write nothing")
    a = ap.parse_args(argv)

    props, _, _ = load_all_fixtures()
    with (REPO / "assessment" / "config" / "harness.toml").open("rb") as fh:
        import tomllib
        fam = tomllib.load(fh)["g1"]["families"]
    fam_of = {cls: family for family, classes in fam.items() for cls in classes}

    pop = load_population()
    strata = {}
    for item in pop:
        strata.setdefault((level_key(item["record"]), verdict_key(item["record"])), []).append(item)
    sizes = {k: len(v) for k, v in strata.items()}
    ordered = sorted(sizes.items(), key=lambda kv: (LEVELS.index(kv[0][0]), VERDICTS.index(kv[0][1])))
    alloc = allocate(sizes, a.n, a.floor)

    empty = [f"{lv} × {vd}" for lv in LEVELS for vd in VERDICTS if (lv, vd) not in sizes]
    if a.dry_run:
        for k, size in ordered:
            print(f"{k[0]:12s} {k[1]:13s} pop {size:4d}  alloc {alloc.get(k, 0):3d}")
        print("empty strata:", ", ".join(empty) or "none")
        print("total", sum(alloc.values()))
        return 0

    rng = random.Random(a.seed)
    drawn = []
    for k, _size in ordered:
        pool = sorted(strata[k], key=lambda it: (it["split"], it["index"]))
        drawn.extend(rng.sample(pool, alloc[k]))
    rng.shuffle(drawn)
    sample = [(f"C{i + 1:03d}", item) for i, item in enumerate(drawn)]

    rows = build_rows(sample, props, fam_of)
    header = {
        "drawn_at": _now(), "seed": a.seed, "floor": a.floor,
        "population": len(pop),
        "by_split": {s: sum(1 for x in pop if x["split"] == s) for s, _ in SOURCES},
        "strata": ordered, "alloc": alloc,
        "empty_note": (", ".join(empty) + " — the review queue is by construction the records at "
                       "L0/L1/L2 or unparseable, so no L3/L4 record carries a reviewer verdict and no "
                       "queued record is `not_in_queue`") if empty else "none",
    }
    SHEET_MD.write_text(sheet_markdown(rows, header), encoding="utf-8")
    with SHEET_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) + ["level", "note"])
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, level="", note=""))

    key = {"task": TASK, "drawn_at": header["drawn_at"], "seed": a.seed, "floor": a.floor,
           "n": a.n, "population": len(pop),
           "sources": {s: str(p.relative_to(REPO)) for s, p in SOURCES},
           "strata": [{"level": k[0], "verdict": k[1], "population": size, "allocated": alloc.get(k, 0)}
                      for k, size in ordered],
           "sheet_md": str(SHEET_MD.relative_to(REPO)), "sheet_csv": str(SHEET_CSV.relative_to(REPO)),
           "key": {sid: {"file": item["file"], "index": item["index"], "split": item["split"],
                         "target": item["record"]["target"], "family": item["record"]["family"],
                         "mode": item["record"]["mode"],
                         "compression_level": item["record"].get("compression_level"),
                         "scorer_level": level_key(item["record"]),
                         "reviewer_verdict": verdict_key(item["record"]),
                         "evidence_path": item["record"]["evidence_path"]}
                   for sid, item in sample}}
    KEY.write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"sample {len(rows)} of {len(pop)} records over {len(ordered)} non-empty strata "
          f"(seed {a.seed}, floor {a.floor}) -> {SHEET_MD.relative_to(REPO)}, "
          f"{SHEET_CSV.relative_to(REPO)}, key {KEY.relative_to(REPO)} (gitignored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
