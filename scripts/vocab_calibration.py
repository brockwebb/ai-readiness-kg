#!/usr/bin/env python3
"""Cohen's kappa between the two raters of the §2 clerical band. **Zero model spend.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §2.2. The reviewer under test is
`claude-opus-5` — this repo's own CC session's model — whose agreement with anyone is
otherwise unmeasured. The second rater is a different model with no repo context, one pair per
call, which is the independence design DD-037 records for the G1 calibration and the reason
that design is reused verbatim rather than re-invented.

**Cohen (1960), "A coefficient of agreement for nominal scales", *Educational and
Psychological Measurement* 20(1):37-46.** kappa = (Po - Pe) / (1 - Pe): observed agreement
discounted by the agreement two raters would reach by chance given their own marginals. Raw
percent agreement is not reported alone, because on a band where one verdict dominates it can
be high while the raters agree about nothing.

**The gate is pre-registered and is a stop, not a warning:** kappa < 0.60 -> write nothing,
report, stop. 0.60 is Landis & Koch's (1977) lower bound for "substantial" agreement; it is
the task's number and is not adjusted here after seeing the result.

    /opt/anaconda3/bin/python3 scripts/vocab_calibration.py [--a opus --b fable]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"
RESULTS = REPO / "assessment" / "results"
GATE = 0.60
CLASSES = ("same", "different", "uncertain")


def load(label: str) -> dict:
    p = RESULTS / f"vocab_link_decisions_2026-09-05_{label}.jsonl"
    if not p.is_file():
        raise SystemExit(f"FATAL: {p.relative_to(REPO)} missing")
    return {json.loads(l)["pair_id"]: json.loads(l)
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def kappa(pairs: list) -> dict:
    """pairs: [(verdict_a, verdict_b)]. Returns Po, Pe, kappa and the confusion matrix."""
    n = len(pairs)
    if not n:
        return {"n": 0, "kappa": None}
    agree = sum(1 for a, b in pairs if a == b)
    po = agree / n
    ma = collections.Counter(a for a, _ in pairs)
    mb = collections.Counter(b for _, b in pairs)
    pe = sum((ma[c] / n) * (mb[c] / n) for c in set(ma) | set(mb))
    k = (po - pe) / (1 - pe) if pe < 1 else None
    conf = {a: {b: 0 for b in CLASSES} for a in CLASSES}
    for a, b in pairs:
        conf.setdefault(a, {}).setdefault(b, 0)
        conf[a][b] += 1
    return {"n": n, "observed_agreement": round(po, 6), "chance_agreement": round(pe, 6),
            "kappa": round(k, 6) if k is not None else None,
            "marginals_a": dict(ma), "marginals_b": dict(mb), "confusion": conf}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", default="opus", help="the reviewer under test")
    ap.add_argument("--b", default="fable", help="the independent rater")
    ap.add_argument("--out", default=str(RESULTS / "vocab_calibration_2026-09-05.json"))
    a = ap.parse_args(argv)

    A, B = load(a.a), load(a.b)
    shared = sorted(set(A) & set(B))
    pairs = [(A[p]["verdict"], B[p]["verdict"]) for p in shared]
    stats = kappa(pairs)
    stats.update({"task": TASK, "reviewer": a.a, "independent_rater": a.b,
                  "gate": GATE, "rubric_version": A[shared[0]]["rubric_version"] if shared else None,
                  "passes_gate": bool(stats.get("kappa") is not None and stats["kappa"] >= GATE)})

    # Disagreements, written for the operator as records — informational, never an approval
    # step (§2.2, and the operating doctrine's narrow-band rule).
    dis = [p for p in shared if A[p]["verdict"] != B[p]["verdict"]]
    lines = [f"# Vocabulary linking — rater disagreements, {a.a} vs {a.b}\n",
             f"**Task:** `{TASK}` §2.2. **Rubric:** {stats['rubric_version']}. "
             f"**n compared:** {stats['n']}. **Cohen's kappa:** {stats['kappa']} "
             f"(gate {GATE}, {'PASS' if stats['passes_gate'] else 'FAIL'}). "
             f"**Disagreements:** {len(dis)}.\n",
             "Informational. These are records for the operator, not a queue of approvals: "
             "the kappa gate above is what decides whether the band's links are written.\n"]
    for p in dis:
        ra, rb = A[p], B[p]
        lines += [f"\n## `{ra['name']}` ({ra['label']}) -> `{ra['term_label']}`\n",
                  f"- **{a.a}:** {ra['verdict']} ({ra['confidence']}) — {ra['reason']}",
                  f"- **{a.b}:** {rb['verdict']} ({rb['confidence']}) — {rb['reason']}",
                  f"- document `{ra['doc_id']}`, node `{ra['node_key']}`, term `{ra['term_id']}`"]
    (RESULTS / "vocab_calibration_disagreements_2026-09-05.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    Path(a.out).write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=1))
    return 0 if stats["passes_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
