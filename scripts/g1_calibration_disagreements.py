#!/usr/bin/env python3
"""The disagreement escalation list for the G1 calibration (task
2026-09-03_g1_calibration_rating_agreement, step 3). **Zero model calls.**

This is the only artifact the operator is asked to look at, and only if he chooses. It is
mechanical: every sampled record where the independent rater and the reviewer are far apart,
printed with everything needed to judge it and nothing else. No commentary, no proposed
resolution — a resolution written here would be the machine grading its own disagreement.

**Selection rule (pre-registered in the task):** a record is listed when the rater's level and
the reviewer's implied level differ by two or more levels, or when either side gave U.

**Mapping the reviewer's verdict to a level**, which the rule needs because the reviewer
answered a different question (genuine vs parser miss, not a level):

* `genuine` — the reviewer read the response and agreed the qualifier is not there, so the
  reviewer's level is the SCORER's level;
* `parser_miss` — the reviewer read the qualifier in a form the parser could not, so the
  record should have scored preserved: the reviewer's level is **L3**, the lowest preserved
  level (the inverse of the implied-verdict rule the agreement script applies);
* `not_in_queue` — the record was never put to the reviewer (the scorer put it at L3+), so
  the reviewer's level is the scorer's level, and the disagreement listed is really the rater
  against the scorer with no reviewer between them. Said here so nobody reads those rows as a
  reviewer's judgment.

`unparseable` is the scorer's own U and has no position on the level scale; it sorts below L0
for the distance, exactly as the agreement script's implied-verdict rule treats it.

    /opt/anaconda3/bin/python3 scripts/g1_calibration_disagreements.py [--distance 2]
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
OUT = RESULTS / "g1_calibration_disagreements_2026-09-03.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def reviewer_level(scorer_level: str, verdict: str) -> str:
    """See the module docstring. Returns a level name or `unparseable`."""
    return "L3" if verdict == "parser_miss" else scorer_level


def position(level: str) -> int:
    """Ordinal position; `unparseable` and `U` sit below L0 (they are not a level)."""
    return -1 if level in (agree.UNPARSEABLE, agree.UNCLASSIFIABLE) else agree.ORDINAL[level]


def load_sheet_blocks(sheet_path: Path) -> dict:
    """sample_id -> the record block as printed on the blind sheet (estimate, family,
    published forms, mode, compression, the prompt the consumer saw, its response)."""
    import g1_calibration_rate as rate
    text = sheet_path.read_text(encoding="utf-8")
    return {sid: block for sid, block in rate.record_blocks(text)}


def rows(sheet_labels: dict, key: dict, blocks: dict, evidence_dir: Path, distance: int) -> list:
    out = []
    for sid, e in key["key"].items():
        lab = (sheet_labels.get(sid) or {}).get("level")
        if lab is None:
            continue                      # never rated: not a disagreement, reported as unrated
        rl = reviewer_level(e["scorer_level"], e["reviewer_verdict"])
        gave_u = lab == agree.UNCLASSIFIABLE or rl == agree.UNPARSEABLE
        gap = abs(position(lab) - position(rl))
        if not (gave_u or gap >= distance):
            continue
        ev = evidence_dir / f"{sid}.{key.get('rater', 'claude-fable-5-1')}.json"
        rater_note = ""
        if ev.is_file():
            rater_note = json.loads(ev.read_text(encoding="utf-8")).get("note") or ""
        out.append({"sample_id": sid, "entry": e, "block": blocks.get(sid, ""),
                    "rater_level": lab, "rater_note": rater_note,
                    "reviewer_level": rl, "gap": gap, "gave_u": gave_u})
    out.sort(key=lambda r: (-r["gap"], r["sample_id"]))
    return out


def render(rows_: list, key: dict, n_rated: int, distance: int, reviewer_notes: dict) -> str:
    L = ["# G1 calibration — rater/reviewer disagreements\n",
         f"**Written:** {_now()} · **Task:** `{TASK}` · **Zero model calls.**\n",
         f"**Rater:** `claude-fable-5-1`, independent (one record per call, hermetic cwd, no repo "
         f"context, no scorer or reviewer information). **Reviewer:** the v2 LLM reviewer (Opus, CC). "
         f"**Scorer:** `g1-score-v2`.\n",
         f"**Selection:** of the {n_rated} rated sample records, the {len(rows_)} below are those where "
         f"the rater's level and the reviewer's implied level differ by {distance} or more levels, or "
         f"where either side gave U. The reviewer's verdict is mapped to a level as: `genuine` → the "
         f"scorer's level; `parser_miss` → L3 (the lowest preserved level); `not_in_queue` → the "
         f"scorer's level, with no reviewer judgment behind it (those rows are the rater against the "
         f"scorer). `unparseable` is the scorer's own U and sorts below L0.\n",
         "**Nothing in this file proposes a resolution.** It exists so the operator can look at the "
         "cases where the two instruments disagree, if he chooses to.\n",
         "| sample | scorer | reviewer verdict | reviewer level | rater | gap |",
         "|---|---|---|---|---|---:|"]
    for r in rows_:
        e = r["entry"]
        L.append(f"| {r['sample_id']} | {e['scorer_level']} | {e['reviewer_verdict']} | {r['reviewer_level']} "
                 f"| {r['rater_level']} | {'U' if r['gave_u'] else r['gap']} |")
    L.append("\n---\n")
    for r in rows_:
        e = r["entry"]
        note = reviewer_notes.get((e["file"], e["index"]), "")
        L.append(f"## {r['sample_id']}\n")
        L.append(f"- **Record:** `{e['target']}` · family `{e['family']}` · mode {e['mode']}"
                 f" · compression {e['compression_level'] or '(n/a — direct)'} · split {e['split']}"
                 f" · `{e['file']}` record {e['index']}")
        L.append(f"- **Evidence:** `{e['evidence_path']}`")
        L.append(f"- **Scorer level:** {e['scorer_level']}")
        L.append(f"- **Reviewer verdict:** {e['reviewer_verdict']}"
                 + (f" — {note}" if note else " — (no note: the record was never in the review queue)"))
        L.append(f"- **Rater level:** {r['rater_level']}" + (f" — {r['rater_note']}" if r['rater_note'] else ""))
        L.append(f"- **Gap:** {'U given' if r['gave_u'] else str(r['gap']) + ' levels'}\n")
        L.append(r["block"] + "\n")
        L.append("---\n")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", default=str(RESULTS / "g1_calibration_sheet_2026-09-03_filled_fable.md"))
    ap.add_argument("--blind-sheet", default=str(RESULTS / "g1_calibration_sheet_2026-09-03.md"))
    ap.add_argument("--key", default=str(RESULTS / ".g1_calibration_key_2026-09-03.json"))
    ap.add_argument("--evidence-dir", default=str(REPO / "assessment" / "evidence" / "g1" / "calibration"))
    ap.add_argument("--distance", type=int, default=2)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--register", action="store_true",
                    help="register the list's two counts as Results (the memo cites them as tokens)")
    a = ap.parse_args(argv)

    labels = agree.read_sheet(Path(a.sheet))
    key = json.loads(Path(a.key).read_text(encoding="utf-8"))
    blocks = load_sheet_blocks(Path(a.blind_sheet))
    # the reviewer's own note, from the results file the record came from
    notes: dict = {}
    for f in {e["file"] for e in key["key"].values()}:
        doc = json.loads((REPO / f).read_text(encoding="utf-8"))
        for i, rec in enumerate(doc["records"]):
            if "review_note" in rec:
                notes[(f, i)] = rec["review_note"]
    n_rated = sum(1 for sid in key["key"] if (labels.get(sid) or {}).get("level") is not None)
    listed = rows(labels, key, blocks, Path(a.evidence_dir), a.distance)
    Path(a.out).write_text(render(listed, key, n_rated, a.distance, notes), encoding="utf-8")
    gave_u = sum(1 for r in listed if r["gave_u"])
    print(f"{len(listed)} of {n_rated} rated records listed (gap >= {a.distance} levels or a U): "
          f"{gave_u} involve a U, {len(listed) - gave_u} are level gaps -> {Path(a.out).relative_to(REPO)}")
    if a.register:
        base = (f"G1 calibration escalation list, independent rater claude-fable-5-1 against the v2 LLM "
                f"reviewer; selection: a gap of {a.distance} or more levels after mapping the reviewer's "
                f"verdict to a level (genuine -> the scorer's level, parser_miss -> L3, not_in_queue -> the "
                f"scorer's level), or either side giving U; registered by "
                f"scripts/g1_calibration_disagreements.py for {TASK}: ")
        for name, value, note in (
            ("g1_cal_fable_disagreements_listed", len(listed),
             f"records listed of the {n_rated} rated ({Path(a.out).relative_to(REPO)})"),
            ("g1_cal_fable_disagreements_with_U", gave_u,
             "of those, records where either side gave U — every one is a record the scorer called "
             "unparseable, which has no level for the gap rule to compare"),
            ("g1_cal_fable_disagreements_level_gap", len(listed) - gave_u,
             f"of those, records separated by a gap of {a.distance} or more levels"),
        ):
            r = subprocess.run(["seldon", "result", "register", "--value", str(value), "--units", name,
                                "--description", base + note, "--script-name", "g1_calibration_agreement",
                                "--data-name", "g1_calibration_disagreements_2026-09-03"],
                               capture_output=True, text=True, cwd=REPO)
            print(("registered " if r.returncode == 0 else "FAILED ") + name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
