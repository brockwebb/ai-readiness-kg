#!/usr/bin/env python3
"""Write the instrument specification's verdicts into the framework of record. **Zero spend.**

`cc_tasks/2026-10-15_instrument_specification_audit.md` Part C, under DN-015. From each entry in
`assessment/instrument/RULE-*.yaml`, through the ONE writer (`framework_writeback.save`, never a
hand edit):

* `instrument_state` (and `instrument_entry`, the entry's path) on the rule's MeasurementSpec
  node, `spec:<leg>`: `specified`, `project_defined`, `invalid` or `retired` (DN-015 §3);
* `plain_name` on the indicator, rewritten from the entry's `claims.pass` so the name states only
  what a pass asserts (at most `plain_name_max_words`, config); an entry with `plain_name: null`
  leaves the indicator's name as it is;
* `fix_line` on the Action an entry's `fix_line_check` rewrote, checked against the entry's
  expected behavior.

`framework/summary_grid_vocab.yaml` holds the authored strings `apply_grid_plain_names.py`
applies; this script refuses to write unless that file already carries the same plain names and
fix lines, so re-running the older script can never revert this one. It adds and changes; it
removes nothing, so `save` writes without `--force`. A projection MUST follow
(`scripts/load_framework_graph.py`), or a Cypher answer over the framework labels is stale (DD-057).

    /opt/anaconda3/bin/python3 scripts/apply_instrument_state.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import framework_writeback as fw  # noqa: E402
import instrument as INS  # noqa: E402

SCRIPT = "scripts/apply_instrument_state.py"
TASK = INS.TASK
VOCAB = REPO / "framework" / "summary_grid_vocab.yaml"


def wanted(entries: list) -> dict:
    """What the record should carry, from the entries."""
    specs, names, fixes = {}, {}, {}
    for e in entries:
        specs[f"spec:{e['leg']}"] = {"instrument_state": e["state"], "instrument_entry": e["_path"]}
        if e.get("plain_name"):
            names[e["indicator"]] = e["plain_name"]
        flc = e.get("fix_line_check") or {}
        if flc.get("verdict") == "rewritten":
            fixes[flc["action"]] = flc["new_fix_line"]
    return {"specs": specs, "plain_names": names, "fix_lines": fixes}


def vocab_drift(w: dict, vocab: dict) -> list:
    """Every name or fix line the grid vocabulary disagrees with, for a grid code it carries."""
    out = []
    for ind, name in w["plain_names"].items():
        code = ind.split(":", 1)[1]
        if code in vocab["plain_names"] and vocab["plain_names"][code] != name:
            out.append(f"plain_names.{code}: vocab {vocab['plain_names'][code]!r} != entry {name!r}")
    for act, line in w["fix_lines"].items():
        if vocab["fix_lines"].get(act) != line:
            out.append(f"fix_lines.{act}: vocab {vocab['fix_lines'].get(act)!r} != entry {line!r}")
    return out


def apply(g: dict, w: dict) -> dict:
    seen = set()
    changed = {"specs": [], "plain_names": [], "fix_lines": []}
    for n in g["nodes"]:
        p, nid = n["properties"], n["id"]
        if nid in w["specs"]:
            seen.add(nid)
            p.update(w["specs"][nid])
            changed["specs"].append(nid)
        if nid in w["plain_names"]:
            seen.add(nid)
            p["plain_name"] = w["plain_names"][nid]
            changed["plain_names"].append(nid)
        if nid in w["fix_lines"]:
            seen.add(nid)
            p["fix_line"] = w["fix_lines"][nid]
            changed["fix_lines"].append(nid)
    every = set(w["specs"]) | set(w["plain_names"]) | set(w["fix_lines"])
    changed["unmatched"] = sorted(every - seen)
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    cfg = INS.load_config()
    entries = INS.load_entries()
    problems = INS.check(cfg, entries)
    if problems:
        raise SystemExit("FATAL: the entries do not pass `instrument.py check`; nothing written:\n  "
                         + "\n  ".join(problems))
    w = wanted(entries)
    drift = vocab_drift(w, yaml.safe_load(VOCAB.read_text(encoding="utf-8")))
    if drift:
        raise SystemExit("FATAL: framework/summary_grid_vocab.yaml disagrees with the entries; update it "
                         "first so apply_grid_plain_names.py cannot revert this write:\n  " + "\n  ".join(drift))
    g = fw.load()
    if g is None:
        raise SystemExit("FATAL: framework record not found")
    rep = apply(g, w)
    if rep["unmatched"]:
        raise SystemExit(f"FATAL: entries name nodes the record does not hold: {rep['unmatched']}; nothing written")
    states = {k: v["instrument_state"] for k, v in w["specs"].items()}
    ev = fw.save(g, script=SCRIPT, task=TASK,
                 changes={"applied": "instrument_state / plain_name / fix_line from the instrument entries (DN-015)",
                          "instrument_state": states, "plain_names": w["plain_names"], "fix_lines": w["fix_lines"]},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({**{k: len(v) for k, v in rep.items() if k != "unmatched"}, "written": ev["written"],
                      "unchanged": ev.get("unchanged", False), "event_id": ev.get("event_id"),
                      "framework_sha256": ev["framework_sha256"], "delta": ev["delta_summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
