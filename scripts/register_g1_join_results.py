#!/usr/bin/env python3
"""Register the declared→observed join per surface file as Seldon Results (task
2026-09-03_g1_freeze_calibration_redefinition_findings, step 3). **Zero model calls.**

The join is the first place the A11 triad's declared and observed legs meet on ONE captured
surface file: `scripts/g1_declared_surfaces.py` scored every surface (`declared_leg.json`), and
every observed family record carries the `source_doc_id` of the file its passage was cut from.
It was reported as a table in §6.5 of the v2 RESULT but never registered, so the findings memo
could not cite it without literals. It is registered here, recomputed from the two files:

    g1_v2_join_<doc_id>_families | _scored | _lost | _loss_rate   (loss = level < 3, i.e. not L3+)
    g1_v2_join_<doc_id>_declared_score                            (0 FAIL, 1 PARTIAL, 2 PASS)
    g1_v2_surface_<surface_type>_none_{scored,lost,loss_rate}     (the same join by surface type)

The declared leg's verdict is a word; it is registered as the harness's own numeric score
(`records.Score`: FAIL 0, PARTIAL 1, PASS 2) so the join travels as numbers, with the word in
the description.

    /opt/anaconda3/bin/python3 scripts/register_g1_join_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POOLED = REPO / "assessment" / "results" / "g1_v2_pooled_opus_reviewed.json"
DECLARED = REPO / "assessment" / "tests" / "fixtures" / "g1" / "v2" / "declared_leg.json"
TASK = "cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md"
DATA_NAMES = "g1_v2_pooled_opus_reviewed"


def slug(doc_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", doc_id.lower()).strip("_")


def rows() -> list:
    declared = json.loads(DECLARED.read_text(encoding="utf-8"))["surfaces"]
    pooled = json.loads(POOLED.read_text(encoding="utf-8"))
    per: dict = {}
    for rec in pooled["records"]:
        did = rec["observations"].get("source_doc_id")
        if did not in declared:
            continue
        b = per.setdefault(did, {"families": 0, "scored": 0, "lost": 0})
        b["families"] += 1
        if rec["outcome"] != "unparseable":
            b["scored"] += 1
            if rec["level"] < 3:
                b["lost"] += 1
    out = []
    for did, b in sorted(per.items()):
        d = declared[did]
        s = slug(did)
        where = (f"declared leg {d['score_name']} ({d['score']}) on surface_type {d['surface_type']}; "
                 f"observed leg from {POOLED.relative_to(REPO)} records with "
                 f"observations.source_doc_id == {did}")
        out.append((f"g1_v2_join_{s}_families", b["families"], f"{where}: family records"))
        out.append((f"g1_v2_join_{s}_scored", b["scored"], f"{where}: scored family records (unparseable excluded)"))
        out.append((f"g1_v2_join_{s}_lost", b["lost"], f"{where}: scored families below L3"))
        out.append((f"g1_v2_join_{s}_loss_rate", round(b["lost"] / b["scored"], 6) if b["scored"] else 0.0,
                    f"{where}: share of scored families below L3"))
        out.append((f"g1_v2_join_{s}_declared_score", d["score"],
                    f"{where}: the declared leg's own score (0 FAIL, 1 PARTIAL, 2 PASS) — "
                    f"evidence: {d['evidence'][:180]}"))
    return out


def surface_rows() -> list:
    """The same join aggregated by surface_type at indirect compression `none` — the view the
    deck slide draws. Registered because the per-compression cells hold the preservation rate
    and its counts but not the loss rate, and a slide must not compute one from the other.
    `prose_labeled` has no captured product surface and so no declared-leg score."""
    pooled = json.loads(POOLED.read_text(encoding="utf-8"))
    per: dict = {}
    for rec in pooled["records"]:
        if rec["mode"] != "indirect" or (rec.get("compression_level") or "none") != "none":
            continue
        b = per.setdefault(rec["surface_type"], {"scored": 0, "lost": 0})
        if rec["outcome"] == "unparseable":
            continue
        b["scored"] += 1
        if rec["level"] < 3:
            b["lost"] += 1
    out = []
    for st, b in sorted(per.items()):
        where = (f"pooled pinned-consumer family records with surface_type {st} at indirect "
                 f"compression none, from {POOLED.relative_to(REPO)}")
        out.append((f"g1_v2_surface_{st}_none_scored", b["scored"], f"{where}: scored families"))
        out.append((f"g1_v2_surface_{st}_none_lost", b["lost"], f"{where}: scored families below L3"))
        out.append((f"g1_v2_surface_{st}_none_loss_rate",
                    round(b["lost"] / b["scored"], 6) if b["scored"] else 0.0,
                    f"{where}: share of scored families below L3"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    data = rows() + surface_rows()
    if a.dry_run:
        for name, value, note in data:
            print(f"{name}\t{value}\t{note[:110]}")
        print(len(data), "Results")
        return 0
    ok = 0
    data = data[a.skip:]
    for name, value, note in data:
        cmd = ["seldon", "result", "register", "--value", str(value), "--units", name,
               "--description", (f"G1 EVAL v2 declared→observed join (A11 legs 1 and 3 on one captured surface "
                                 f"file), pinned consumer claude-opus-5, parser g1-parse-v2, scorer g1-score-v2; "
                                 f"registered by scripts/register_g1_join_results.py for {TASK}. {note}"),
               "--script-name", "rescore_g1_v2", "--data-name", DATA_NAMES]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-200:])
    print(f"registered {ok}/{len(data)} join Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
