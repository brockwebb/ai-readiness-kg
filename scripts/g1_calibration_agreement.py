#!/usr/bin/env python3
"""Agreement between the operator's calibration labels, the frozen scorer, and the LLM reviewer
(task 2026-09-03_g1_freeze_calibration_redefinition_findings, step 1). **Zero model calls.**
Stdlib only.

This script is written and tested here; it is NOT run on real labels in that task, because
there are no operator labels yet. `scripts/g1_calibration_sample.py` issues the blind sheet;
the operator fills the `level` (L0–L4 or U) and `note` columns; then this runs.

**Prior art in this repo's own record, adopted.** `scripts/tevv_stability.py` already measures
agreement with Cohen's kappa (item-presence kappa over a union universe, Results `kappa` under
tasks `de7ae80b` and `68426971`), and its docstring carries the lesson this file needs: with
skewed marginals kappa is dominated by its chance term and can go sharply negative while raw
agreement is high (the kappa paradox, Cicchetti & Feinstein 1990; the TEVV run recorded
kappa = -0.5904 at PA = 0.4092). That statistic is binary presence over a set union and is not
reusable for an ordinal confusion table, so the coefficient is implemented here — but the
remedy is carried over: kappa never travels alone. Raw agreement, the full confusion table and,
for the binary comparison, positive specific agreement (Dice) are reported beside it, and the
sheet is stratified precisely because the population is 372 L4 records out of 778.

**Prior art from the literature, adopted rather than re-derived.** Chance-corrected agreement: Cohen (1960).
Ordinal disagreement weighted by squared distance: Cohen (1968) weighted kappa; with quadratic
weights the coefficient equals the intraclass correlation ICC(2,1) for two raters
(Fleiss & Cohen 1973), which is why quadratic weights are the standard choice on a level scale
and are what this task pre-registers. Interval by the percentile bootstrap over records
(Efron & Tibshirani 1993). Judging an LLM judge by agreement with human labels rather than by
its own confidence: Han et al., arXiv:2510.09738 (Wintermute `harvest-arxiv-e2a16615`).
Landis & Koch's (1977) verbal bands ("substantial", "almost perfect"), cited by
`tevv_stability.py`, are deliberately NOT applied here: no threshold on kappa is
pre-registered, and naming a band would be setting one by the back door. The kappa is reported
with its interval and its n, exactly as G1 asks of everyone else.

**Two comparisons, on two scales — stated here because they are not interchangeable.**

1. **Operator vs scorer**, on the ordinal level scale L0…L4, quadratic weights. `unparseable`
   (scorer) and `U` (operator) have no position on that scale, so the primary coefficient is
   computed on records where BOTH sides are ordinal, and a secondary UNWEIGHTED kappa over the
   six categories (L0…L4 plus one `unparseable`/`U` category) is reported beside it with its
   own n. Neither is silently substituted for the other.
2. **Operator vs reviewer**, on the reviewer's own binary {genuine, parser_miss}, over the
   review queue only (the records the reviewer actually judged: scorer level L0/L1/L2 or
   unparseable). The operator never sees that vocabulary, so their verdict is DERIVED, by the
   rule pre-registered here: the operator implies `parser_miss` when they read a higher level
   than the scorer recorded (they found the qualifier stated in a form the parser did not
   credit) and `genuine` when they agree with the scorer or go lower. An operator `U` on a
   queued record implies neither and is excluded, counted, and reported.

    /opt/anaconda3/bin/python3 scripts/g1_calibration_agreement.py \
        --sheet assessment/results/g1_calibration_sheet_2026-09-03.csv \
        --key assessment/results/.g1_calibration_key_2026-09-03.json \
        [--bootstrap 10000] [--seed 20260903] [--out PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEVELS = ("L0", "L1", "L2", "L3", "L4")
ORDINAL = {lv: i for i, lv in enumerate(LEVELS)}
UNPARSEABLE = "unparseable"          # the scorer's fourth outcome
UNCLASSIFIABLE = "U"                 # the operator's fourth answer
SIX = LEVELS + (UNPARSEABLE,)

_ANSWER_RE = re.compile(r"^\*\*(C\d{3}) — Level \(L0 / L1 / L2 / L3 / L4 / U\):\*\*\s*(.*?)\s*$", re.M)
_NOTE_RE = re.compile(r"^\*\*(C\d{3}) — Note:\*\*\s*(.*?)\s*$", re.M)


class SheetError(ValueError):
    """A filled sheet that cannot be read. Names the sample id (standard 4: fail loud)."""


# ---------------------------------------------------------------------------
# Reading the filled sheet
# ---------------------------------------------------------------------------

def _clean_label(raw: str, sid: str) -> str | None:
    """Normalise one operator answer. Blank / the unfilled rule is 'not labelled' (None);
    anything else must be a level or U, or the sheet is wrong and we say so."""
    v = (raw or "").strip().strip("_").strip()
    if not v:
        return None
    v = v.upper().replace("LEVEL", "").strip()
    if v in ORDINAL:
        return v
    if v in ("0", "1", "2", "3", "4"):
        return f"L{v}"
    if v in ("U", "UNCLASSIFIABLE", "UNPARSEABLE"):
        return UNCLASSIFIABLE
    raise SheetError(f"{sid}: unreadable level {raw!r} (expected L0–L4 or U)")


def read_sheet(path: Path) -> dict:
    """Filled sheet -> {sample_id: {'level': …, 'note': …}}. CSV or the markdown sheet."""
    text = path.read_text(encoding="utf-8")
    out: dict = {}
    if path.suffix.lower() == ".csv":
        for row in csv.DictReader(text.splitlines()):
            sid = (row.get("sample_id") or "").strip()
            if not sid:
                continue
            out[sid] = {"level": _clean_label(row.get("level", ""), sid),
                        "note": (row.get("note") or "").strip()}
        if not out:
            raise SheetError(f"{path}: no sample_id rows")
        return out
    for sid, raw in _ANSWER_RE.findall(text):
        out[sid] = {"level": _clean_label(raw, sid), "note": ""}
    for sid, note in _NOTE_RE.findall(text):
        if sid in out:
            out[sid]["note"] = note.strip().strip("_").strip()
    if not out:
        raise SheetError(f"{path}: no answer lines found")
    return out


# ---------------------------------------------------------------------------
# Kappa
# ---------------------------------------------------------------------------

def confusion(pairs: list, categories: tuple) -> dict:
    """{(a, b): count} over the given category set; every cell present."""
    table = {(a, b): 0 for a in categories for b in categories}
    for a, b in pairs:
        table[(a, b)] += 1
    return table


def kappa(pairs: list, categories: tuple, weights: str = "quadratic") -> float | None:
    """Cohen's kappa. `weights`: 'quadratic' (Cohen 1968 on the ordinal scale) or 'none'
    (Cohen 1960). Returns None when it is undefined — one rater used a single category and the
    expected disagreement is zero. Undefined is reported as undefined, never as 0.0 or 1.0."""
    n = len(pairs)
    if n == 0:
        return None
    idx = {c: i for i, c in enumerate(categories)}
    k = len(categories)
    if weights == "quadratic":
        if k < 2:
            return None
        w = [[((i - j) / (k - 1)) ** 2 for j in range(k)] for i in range(k)]
    elif weights == "none":
        w = [[0.0 if i == j else 1.0 for j in range(k)] for i in range(k)]
    else:
        raise ValueError(f"unknown weights {weights!r}")
    rows = [0] * k
    cols = [0] * k
    obs = 0.0
    for a, b in pairs:
        i, j = idx[a], idx[b]
        rows[i] += 1
        cols[j] += 1
        obs += w[i][j]
    obs /= n
    exp = sum(w[i][j] * rows[i] * cols[j] for i in range(k) for j in range(k)) / (n * n)
    if exp == 0:
        return None
    return 1.0 - obs / exp


def raw_agreement(pairs: list) -> float | None:
    if not pairs:
        return None
    return sum(1 for a, b in pairs if a == b) / len(pairs)


def positive_agreement(pairs: list, category: str) -> float | None:
    """Positive specific agreement (Dice) on one category: 2|A∩B| / (|A|+|B|). The kappa-paradox
    remedy this repo already uses (`scripts/tevv_stability.py`; Cicchetti & Feinstein 1990) —
    it says how well the two raters agree on the MINORITY call, which a skewed kappa hides."""
    a = sum(1 for x, _ in pairs if x == category)
    b = sum(1 for _, y in pairs if y == category)
    both = sum(1 for x, y in pairs if x == y == category)
    return (2 * both / (a + b)) if (a + b) else None


def bootstrap_ci(pairs: list, categories: tuple, weights: str, b: int, seed: int) -> dict:
    """Percentile bootstrap over records (Efron & Tibshirani 1993). Resamples in which kappa is
    undefined are counted and dropped — reported, so a wide interval built on few usable
    resamples cannot be mistaken for a tight one."""
    if not pairs:
        return {"lower": None, "upper": None, "b": 0, "undefined": 0}
    rng = random.Random(seed)
    n = len(pairs)
    ks, undefined = [], 0
    for _ in range(b):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        k = kappa(sample, categories, weights)
        if k is None:
            undefined += 1
        else:
            ks.append(k)
    if not ks:
        return {"lower": None, "upper": None, "b": b, "undefined": undefined}
    ks.sort()

    def pct(p):
        i = (len(ks) - 1) * p
        lo, hi = int(i), min(int(i) + 1, len(ks) - 1)
        return round(ks[lo] + (ks[hi] - ks[lo]) * (i - lo), 6)

    return {"lower": pct(0.025), "upper": pct(0.975), "b": b, "undefined": undefined}


# ---------------------------------------------------------------------------
# The two comparisons
# ---------------------------------------------------------------------------

def implied_verdict(operator_level: str, scorer_level: str) -> str | None:
    """The operator's implied reviewer verdict on a queued record (see the module docstring).
    Higher than the scorer -> the qualifier was there and the parser missed it. Equal or lower
    -> the loss is genuine. `U` implies nothing."""
    if operator_level == UNCLASSIFIABLE:
        return None
    op = ORDINAL[operator_level]
    sc = -1 if scorer_level == UNPARSEABLE else ORDINAL[scorer_level]
    return "parser_miss" if op > sc else "genuine"


def analyse(sheet: dict, key: dict, bootstrap: int, seed: int) -> dict:
    entries = key["key"]
    missing = [sid for sid in entries if sid not in sheet]
    unlabelled = [sid for sid in entries if sid in sheet and sheet[sid]["level"] is None]
    labelled = {sid: sheet[sid]["level"] for sid in entries
                if sid in sheet and sheet[sid]["level"] is not None}

    ordinal_pairs, six_pairs, verdict_pairs = [], [], []
    excluded_U_in_queue = 0
    for sid, op in labelled.items():
        e = entries[sid]
        sc = e["scorer_level"]
        six_pairs.append((op if op != UNCLASSIFIABLE else UNPARSEABLE, sc))
        if op != UNCLASSIFIABLE and sc != UNPARSEABLE:
            ordinal_pairs.append((op, sc))
        if e["reviewer_verdict"] != "not_in_queue":
            iv = implied_verdict(op, sc)
            if iv is None:
                excluded_U_in_queue += 1
            else:
                verdict_pairs.append((iv, e["reviewer_verdict"]))

    def block(pairs, categories, weights, label):
        return {
            "comparison": label, "n": len(pairs),
            "kappa": None if kappa(pairs, categories, weights) is None else round(kappa(pairs, categories, weights), 6),
            "weights": weights,
            "bootstrap95": bootstrap_ci(pairs, categories, weights, bootstrap, seed),
            "raw_agreement": None if raw_agreement(pairs) is None else round(raw_agreement(pairs), 6),
            "categories": list(categories),
            "confusion": {f"{a}|{b}": c for (a, b), c in sorted(confusion(pairs, categories).items())},
        }

    return {
        "task": "cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md",
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "sheet_n": len(entries), "labelled": len(labelled),
        "unlabelled": unlabelled, "missing_from_sheet": missing,
        "seed": seed, "bootstrap_resamples": bootstrap,
        "operator_vs_scorer_ordinal": block(ordinal_pairs, LEVELS, "quadratic",
                                            "operator vs scorer, L0–L4 only, quadratic weights"),
        "operator_vs_scorer_six_category": block(six_pairs, SIX, "none",
                                                 "operator vs scorer, L0–L4 + unparseable/U, unweighted"),
        "operator_vs_reviewer_queue": dict(block(verdict_pairs, ("genuine", "parser_miss"), "none",
                                                 "operator (implied) vs reviewer, review queue only"),
                                           excluded_operator_U=excluded_U_in_queue,
                                           positive_agreement_parser_miss=(
                                               None if positive_agreement(verdict_pairs, "parser_miss") is None
                                               else round(positive_agreement(verdict_pairs, "parser_miss"), 6))),
        "notes": ["Rows of a confusion table read 'operator|other'.",
                  "No kappa threshold is pre-registered; no verbal band is applied.",
                  "Read kappa beside the raw agreement and the confusion table: the level "
                  "distribution is skewed (L4 dominates the population), and a skewed marginal "
                  "drives kappa down independently of how the raters actually behaved."],
    }


def render(report: dict) -> str:
    L = [f"G1 reviewer calibration — {report['labelled']} of {report['sheet_n']} sheet records labelled"]
    if report["unlabelled"]:
        L.append(f"  unlabelled: {', '.join(report['unlabelled'])}")
    if report["missing_from_sheet"]:
        L.append(f"  missing from the sheet: {', '.join(report['missing_from_sheet'])}")
    for k in ("operator_vs_scorer_ordinal", "operator_vs_scorer_six_category", "operator_vs_reviewer_queue"):
        b = report[k]
        ci = b["bootstrap95"]
        interval = "—" if ci["lower"] is None else f"[{ci['lower']}, {ci['upper']}]"
        kv = "undefined" if b["kappa"] is None else f"{b['kappa']:.3f}"
        L.append(f"  {b['comparison']}: n={b['n']}, kappa={kv} {interval} "
                 f"({b['weights']} weights), raw agreement="
                 f"{'—' if b['raw_agreement'] is None else format(b['raw_agreement'], '.3f')}"
                 + (f", operator U excluded={b['excluded_operator_U']}" if "excluded_operator_U" in b else "")
                 + (f", positive agreement on parser_miss={b['positive_agreement_parser_miss']}"
                    if b.get("positive_agreement_parser_miss") is not None else ""))
        if ci["undefined"]:
            L.append(f"    bootstrap resamples with undefined kappa: {ci['undefined']} of {ci['b']}")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", required=True, help="the FILLED sheet (.csv or .md)")
    ap.add_argument("--key", required=True, help="the gitignored sample-id -> record key")
    ap.add_argument("--bootstrap", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--out", default=None, help="write the full report as JSON")
    a = ap.parse_args(argv)
    sheet = read_sheet(Path(a.sheet))
    key = json.loads(Path(a.key).read_text(encoding="utf-8"))
    report = analyse(sheet, key, a.bootstrap, a.seed)
    if not report["labelled"]:
        print("no labelled records: the sheet has not been filled in yet", file=sys.stderr)
        return 1
    print(render(report))
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
