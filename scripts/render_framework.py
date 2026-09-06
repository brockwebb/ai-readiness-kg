#!/usr/bin/env python3
"""Render the framework JSON back to the skeleton's seven tables, and gate on equality.
**Zero model spend.**

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §2.3. The gate is the whole point: a
source of truth that cannot reproduce the document it replaces is not a source of truth. The
rendered tables must equal v0.2.9's **cell for cell** after whitespace normalisation, or every
diff must be listed with the reason it exists. **Zero unexplained diffs or the JSON is not
adopted.**

    /opt/anaconda3/bin/python3 scripts/render_framework.py --check
    /opt/anaconda3/bin/python3 scripts/render_framework.py --write   # rewrite the tables in place
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
SKELETON = REPO / "docs" / "crosswalk" / "usafacts_operationalization_skeleton.md"
JSON_PATH = REPO / "framework" / "ai_readiness_framework.json"
REPORT = REPO / "state" / "framework_roundtrip_2026-09-06.json"

_WS = re.compile(r"\s+")


def norm(s: str) -> str:
    return _WS.sub(" ", (s or "").strip())


def rows_from_json(g: dict) -> list:
    """Indicator rows in document order, with G1's two legs folded back into ONE row.

    The split is the only structural change `build_framework_graph` makes (DD-036's two-leg
    rule), so the render has to undo it exactly — which is the round trip's sharpest test.
    """
    inds = [n for n in g["nodes"] if "AssessmentIndicator" in n["labels"]]
    out, g1_legs = [], {}
    for n in inds:
        p = n["properties"]
        if p.get("g1_leg_of"):
            g1_legs[p["code"]] = p
            continue
        out.append(p)
    if g1_legs:
        d, o = g1_legs.get("G1-D"), g1_legs.get("G1-O")
        merged = dict(d)
        merged["code"] = "G1"
        merged["indicator"] = f"{d['indicator']} {o['indicator']}"
        merged["type"] = "G1-D: AUTO · G1-O: EVAL"
        merged["tier_raw"] = "G1-D `public` · G1-O `paid`"
        out.append(merged)
    order = {c: i for i, c in enumerate("ABCDEFG")}
    return sorted(out, key=lambda p: (order[p["criterion_code"]],
                                      int(re.sub(r"\D", "", p["code"]) or 0)))


def render_row(p: dict) -> str:
    """The Tier cell is rendered from `tier_raw`, verbatim. Rendering the ENUM and re-wrapping
    it in backticks is how the first round trip failed: A11's cell carries prose and a second
    backticked token, and `enum -> f"`{enum}`"` cannot reproduce it."""
    return (f"| {p['code']} | {p['construct']} | {p['indicator']} | {p['type']} | "
            f"{p['evidence_raw']} | {p.get('tier_raw', p['tier'])} | {p['status']} |")


def skeleton_rows(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*([A-G]\d{1,2})\s*\|", line)
        if m:
            out[m.group(1)] = line
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)

    g = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    text = SKELETON.read_text(encoding="utf-8")
    original = skeleton_rows(text)
    rendered = {p["code"]: render_row(p) for p in rows_from_json(g)}

    diffs, explained = [], []
    for code in sorted(set(original) | set(rendered)):
        o, r = original.get(code), rendered.get(code)
        if o is None or r is None:
            diffs.append({"code": code, "reason": "present in only one side",
                          "skeleton": o, "rendered": r})
            continue
        oc = [norm(c) for c in o.strip().strip("|").split("|")]
        rc = [norm(c) for c in r.strip().strip("|").split("|")]
        if oc == rc:
            continue
        bad = [(i, x, y) for i, (x, y) in enumerate(zip(oc, rc)) if x != y]
        entry = {"code": code, "cells": [{"index": i, "skeleton": x[:200], "rendered": y[:200]}
                                         for i, x, y in bad]}
        # The ONE representable-difference class, stated in advance: G1's row is two indicator
        # nodes folded back into one cell, so its Type and Tier cells are reconstructed from
        # the two legs rather than copied. Any other diff is unexplained.
        if code == "G1" and all(i in (3, 5) for i, _, _ in bad):
            entry["reason"] = ("G1 is stored as two indicator nodes (DD-036's two-leg rule) "
                               "and folded back into one row; the Type and Tier cells are "
                               "reconstructed from the legs, not copied.")
            explained.append(entry)
        else:
            diffs.append(entry)

    report = {"task": TASK, "indicator_rows_in_skeleton": len(original),
              "indicator_rows_rendered": len(rendered),
              "unexplained_diffs": diffs, "explained_diffs": explained,
              "gate_passed": not diffs}
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "explained_diffs"},
                     indent=1, ensure_ascii=False)[:3000])
    print(f"\nexplained diffs: {len(explained)}  unexplained: {len(diffs)}  "
          f"GATE {'PASS' if not diffs else 'FAIL'}")

    if a.write and not diffs:
        for code, line in rendered.items():
            if code in original and code != "G1":
                text = text.replace(original[code], line)
        SKELETON.write_text(text, encoding="utf-8")
        print("skeleton tables rewritten from the JSON")
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
