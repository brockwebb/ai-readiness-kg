#!/usr/bin/env python3
"""Reviewer pass for the G1 genuine-loss count (task 2026-09-03 step 6).

For every record in a results file at L0 / L1 / L2 (or unparseable), print the proposition,
the qualifier the source states, the scorer's reading, and the raw response, so a reviewer
can say whether the qualifier was in fact dropped, shifted or corrupted (`genuine`) or
whether the scorer misread a response that carried it (`parser`). The judgments are written
back into a NEW results file (the input is never edited) as `genuine_loss` per record, with
`reviewer` and `criterion` recorded once at the top.

    python3 scripts/g1_review_losses.py --in RESULTS.json --list            # print the queue
    python3 scripts/g1_review_losses.py --in RESULTS.json --out NEW.json --judgments J.json

J.json: {"<target>|<qualifier_class>|<mode>": {"genuine_loss": true|false, "note": "..."}}.
A record at L3/L4 is never a loss; a record left unjudged stays null and is reported as such.

Criterion (recorded on the file): a loss is genuine when the raw response, read in full,
does not state the qualifier's class and value (or, for VINTAGE, the as-of date; for a flag,
the producer's outcome word) for that estimate — whatever form it uses. A response that
states it in a form the parser could not read is a parser miss, not a loss.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

CRITERION = ("genuine when the raw response, read in full, does not state the qualifier's class and "
             "value (VINTAGE: the as-of date; flags: the producer's outcome word) for that estimate in any "
             "form; a response that states it in a form the parser could not read is a parser miss")


def key(r: dict) -> str:
    return f"{r['target']}|{r['qualifier_class']}|{r['mode']}|{r['observations'].get('qualifier_source', {}).get('parameter', '')}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--judgments", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--reviewer", default="CC")
    a = ap.parse_args(argv)
    report = json.loads(Path(a.inp).read_text(encoding="utf-8"))
    queue = [r for r in report["records"] if r["outcome"] == "unparseable" or (r["level"] is not None and r["level"] <= 2)]
    if a.list:
        for r in queue:
            print(f"\n=== {key(r)}  [{r['outcome']}/{r.get('level_label')}/{r.get('failure_class')}]")
            print(f"source qualifier: {r['observations'].get('qualifier_source')}")
            print(f"scorer: {r['evidence']}")
            print(f"evidence: {r['evidence_path']}")
            text = json.loads(Path(r["evidence_path"]).read_text(encoding="utf-8"))["response_text"]
            print("--- response ---")
            print(text)
        print(f"\n{len(queue)} record(s) to review of {len(report['records'])}")
        return 0
    if not a.out or not a.judgments:
        ap.error("--out and --judgments are required unless --list")
    judg = json.loads(Path(a.judgments).read_text(encoding="utf-8"))
    n_gen = n_parser = n_unjudged = 0
    for r in report["records"]:
        if r["outcome"] != "unparseable" and (r["level"] is None or r["level"] >= 3):
            r["genuine_loss"] = False
            continue
        j = judg.get(key(r))
        if j is None:
            r["genuine_loss"] = None
            n_unjudged += 1
            continue
        r["genuine_loss"] = bool(j["genuine_loss"])
        r["review_note"] = j.get("note", "")
        if r["genuine_loss"]:
            n_gen += 1
        else:
            n_parser += 1
    report["review"] = {"reviewer": a.reviewer, "criterion": CRITERION, "reviewed_at": datetime.now(timezone.utc).isoformat(),
                        "queue": len(queue), "genuine_losses": n_gen, "parser_misses": n_parser, "unjudged": n_unjudged}
    Path(a.out).write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"reviewed {len(queue)}: genuine {n_gen}, parser misses {n_parser}, unjudged {n_unjudged} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
