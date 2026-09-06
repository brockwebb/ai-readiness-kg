#!/usr/bin/env python3
"""Fill the gold sheet from the rater's labels, measure test-retest, and find the escalations.
**Zero model spend.**

Task `cc_tasks/2026-09-05_er_gold_fable_labels_and_score.md` §2-§4. Three phases, each of
which reads an artifact on disk and writes another; no phase recomputes a number another one
already produced.

    --fill         write the rater's verdict and reason into the sheet's own blanks
    --retest       raw agreement and Cohen's kappa between the main and retest passes
    --escalations  the §4 set, computed by re-scoring with each `uncertain` pair flipped
    --register     per-stratum precision/recall with Wilson intervals, and the above

**§4's escalation rule is deliberately narrow, and the narrowness is the point.** An
`uncertain` is excluded from the rates by the sheet's own rule, so most of them cost nothing
to leave alone. A pair reaches the operator ONLY when flipping that single verdict would move
a DD-045 §3 threshold verdict — precision across 0.95 or recall across 0.80 on the point
estimate. That is computed by actually re-scoring with the flip, not by an estimate of
influence: the operator's judgment is a narrow-band sensor and a queue of "might matter" is
exactly the theater the operating doctrine forbids.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import score_er_gold as sg  # noqa: E402
from vocab_calibration import kappa  # noqa: E402  (one kappa implementation, not two)

TASK = "cc_tasks/2026-09-05_er_gold_fable_labels_and_score.md"
SHEET = REPO / "docs" / "research" / "2026-09-05_er_gold_sample.md"
KEY = REPO / "state" / "er_gold_key.json"
RESULTS = REPO / "assessment" / "results"
ESCALATIONS = REPO / "docs" / "research" / "2026-09-05_er_gold_escalations.md"
SUMMARY = RESULTS / "er_gold_analysis_2026-09-05.json"

RATER = "claude-fable-5-1"


def labels(pass_name: str) -> dict:
    p = RESULTS / f"er_gold_labels_2026-09-05_{pass_name}.jsonl"
    if not p.is_file():
        return {}
    return {json.loads(l)["pair_id"]: json.loads(l)
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def fill_sheet(main: dict) -> int:
    """Write the verdict and reason into the sheet's own blanks. The sheet stays the
    operator-facing record — §3 — so the rater's reason goes in `note` where a person's would."""
    text = SHEET.read_text(encoding="utf-8")
    n = 0
    for pid, rec in sorted(main.items()):
        v = rec.get("verdict")
        if not v:
            continue
        text = text.replace(
            f"**{pid} — verdict (same / different / uncertain):** ______",
            f"**{pid} — verdict (same / different / uncertain):** {v}")
        note = (rec.get("reason") or "").replace("\n", " ")
        text = text.replace(f"**{pid} — note:** ______",
                            f"**{pid} — note:** [{RATER}, confidence {rec.get('confidence')}] {note}")
        n += 1
    header = (
        f"# Entity-resolution gold sample — 100 pairs, LABELLED\n\n"
        f"**Labelled by `{RATER}`** — an independent model rater that took no part in any "
        f"pipeline decision on these pairs: the vocabulary seed, the alias-first links, the "
        f"clerical-band judgments and the homograph scores were all `claude-opus-5` or "
        f"deterministic code. One pair per call, hermetic empty cwd, no repo access, and the "
        f"pair block below is all the rater saw — no cosine, no vocabulary term, no stratum, "
        f"no pipeline decision. Raw exchanges under `assessment/evidence/er_gold/`. "
        f"**Limitation, stated where the numbers are:** a same-family rater bounds "
        f"correctness RELATIVE TO THAT RATER, not to ground truth (DD-045 addendum-01). "
        f"Task `{TASK}`. {n} of 100 pairs answered.\n")
    text = re.sub(r"^# Entity-resolution gold sample — 100 pairs for the operator\n",
                  header, text, count=1, flags=re.M)
    SHEET.write_text(text, encoding="utf-8")
    return n


def retest(main: dict, re_: dict) -> dict:
    shared = sorted(set(main) & set(re_))
    pairs = [(main[p]["verdict"], re_[p]["verdict"]) for p in shared]
    st = kappa(pairs)
    st["disagreements"] = [
        {"pair_id": p, "main": main[p]["verdict"], "retest": re_[p]["verdict"],
         "main_confidence": main[p].get("confidence"), "retest_confidence": re_[p].get("confidence")}
        for p in shared if main[p]["verdict"] != re_[p]["verdict"]]
    return st


def escalations(pairs: list, base: dict) -> list:
    """§4: an `uncertain` pair escalates only if flipping it alone moves a threshold verdict."""
    out = []
    for i, p in enumerate(pairs):
        if p.get("gold") is not None:
            continue                    # only uncertain/unfilled rows can flip
        for flip in ("same", "different"):
            trial = [dict(x) for x in pairs]
            trial[i]["gold"] = flip
            r = sg.score(trial)
            if (r["passes_precision"] != base["passes_precision"]
                    or r["passes_recall"] != base["passes_recall"]):
                out.append({"pair_id": p["pair_id"], "stratum": p["stratum"],
                            "system_match": p["system_match"], "flip_to": flip,
                            "base": {"precision": base["precision"], "recall": base["recall"],
                                     "passes_precision": base["passes_precision"],
                                     "passes_recall": base["passes_recall"]},
                            "flipped": {"precision": r["precision"], "recall": r["recall"],
                                        "passes_precision": r["passes_precision"],
                                        "passes_recall": r["passes_recall"]}})
                break
    return out


def register(rows: list) -> int:
    ok = 0
    for name, value, note in rows:
        if value is None:
            print("SKIPPED (no value):", name)
            continue
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{note} Derivation: scripts/er_gold_finalize.py "
                                             f"-> {SUMMARY.name} ({TASK}).",
                            "--script-name", "er_gold_finalize",
                            "--data-name", "er_gold_analysis_2026-09-05"],
                           capture_output=True, text=True, cwd=REPO)
        ok += 1 if r.returncode == 0 else 0
        if r.returncode:
            print("FAILED:", name, r.stderr.strip()[-200:])
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f in ("fill", "retest", "escalations", "register", "all"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args(argv)
    do = lambda f: getattr(a, f) or a.all  # noqa: E731

    main_labels, retest_labels = labels("main"), labels("retest")
    out: dict = {"task": TASK, "rater": RATER,
                 "labelled_main": len(main_labels), "labelled_retest": len(retest_labels),
                 "verdict_counts": dict(collections.Counter(
                     r["verdict"] for r in main_labels.values()))}

    if do("fill"):
        out["sheet_filled"] = fill_sheet(main_labels)
        print(f"filled {out['sheet_filled']} verdicts into the sheet")

    if do("retest") and retest_labels:
        out["retest"] = retest(main_labels, retest_labels)
        print(json.dumps({k: v for k, v in out["retest"].items() if k != "confusion"}, indent=1))

    scored = sg.score(sg.load(SHEET, KEY)) if do("escalations") or do("register") else None
    if scored:
        out["scores"] = scored
    if do("escalations") and scored:
        pairs = sg.load(SHEET, KEY)
        esc = escalations(pairs, scored)
        out["escalations"] = esc
        L = [f"# ER gold — escalations to the operator\n",
             f"**Task:** `{TASK}` §4. **Rule:** a pair reaches you ONLY if `{RATER}` answered "
             f"`uncertain` AND flipping that single verdict would move a DD-045 §3 threshold "
             f"verdict (precision across 0.95, or recall across 0.80, on the point estimate). "
             f"Every other `uncertain` is excluded from the rates by the sheet's own rule and "
             f"costs nothing to leave alone.\n",
             f"**Measured:** {scored['pairs_uncertain_or_unfilled']} uncertain or unfilled "
             f"pair(s); **{len(esc)}** meet the escalation rule.\n"]
        if not esc:
            L.append("## None.\n\nNo single `uncertain` verdict can move either threshold. "
                     "There is nothing here that needs your judgment.\n")
        for e in esc:
            L.append(f"\n## {e['pair_id']} (stratum {e['stratum']}, pipeline says "
                     f"{'match' if e['system_match'] else 'no match'})\n")
            L.append(f"- base: precision {e['base']['precision']}, recall {e['base']['recall']}")
            L.append(f"- flipped to `{e['flip_to']}`: precision {e['flipped']['precision']}, "
                     f"recall {e['flipped']['recall']}")
            L.append(f"- read the pair in `docs/research/2026-09-05_er_gold_sample.md`\n")
        ESCALATIONS.write_text("\n".join(L) + "\n", encoding="utf-8")
        print(f"escalations: {len(esc)} -> {ESCALATIONS.relative_to(REPO)}")

    SUMMARY.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    if do("register") and scored:
        rows = []
        for h, c in sorted(scored["by_stratum"].items()):
            what = {"A": "exact-name auto-links", "B": "clerical band accepted",
                    "C": "clerical band rejected", "D": "near-miss below the 0.80 floor",
                    "E": "cross-arm pairs in terms the homograph pass KEPT"}[h]
            if c["precision"] is not None:
                rows.append((f"er_gold_precision_stratum_{h}", c["precision"],
                             f"Pairwise precision in gold stratum {h} ({what}): {c['tp']} true "
                             f"of {c['tp'] + c['fp']} pairs the pipeline matched. Wilson 95% CI "
                             f"{c['precision_ci']} on the stratum's own {c['n']} scored pairs "
                             f"(unweighted — the weight applies to the population estimate, "
                             f"not to a within-stratum rate)."))
            if c["recall"] is not None:
                rows.append((f"er_gold_recall_stratum_{h}", c["recall"],
                             f"Pairwise recall in gold stratum {h} ({what}): {c['tp']} of "
                             f"{c['tp'] + c['fn']} pairs the rater called `same`. Wilson 95% CI "
                             f"{c['recall_ci']}."))
        if out.get("retest"):
            rt = out["retest"]
            rows += [("er_gold_retest_agreement", rt["observed_agreement"],
                      f"Raw test-retest agreement of `{RATER}` on {rt['n']} pairs re-rated in a "
                      f"fresh hermetic session (seeded draw, 6 per stratum). Reported, not "
                      f"gated: it is the RELIABILITY bound on the gold labels, and no accuracy "
                      f"figure derived from them can be trusted beyond it."),
                     ("er_gold_retest_kappa", rt["kappa"],
                      f"Cohen's kappa for the same test-retest, chance agreement "
                      f"{rt['chance_agreement']}. {len(rt['disagreements'])} pair(s) changed "
                      f"verdict between passes.")]
        rows.append(("er_gold_escalations", len(out.get("escalations", [])),
                     "Pairs meeting the §4 escalation rule: rater said `uncertain` AND flipping "
                     "that one verdict would move a DD-045 §3 threshold verdict."))
        print(f"registered {register(rows)}/{len(rows)} Results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
