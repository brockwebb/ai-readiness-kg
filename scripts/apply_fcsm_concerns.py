#!/usr/bin/env python3
"""Write the FCSM 20-04 Accessibility concern layer into the framework record. **Zero spend.**

`cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md` Part A, implementing
DN-018. The validity layer (DN-005 section 2.1): each of the sixteen instrument MeasurementSpecs
is tied to the FCSM 20-04 Accessibility concern it operationalizes, so the dictionary, brief and
one-pager render the tie rather than restate it.

**Nothing here is typed from the ruling's prose.** The four concern nodes' text and the
twenty-three edges are PARSED from DN-018's own markdown tables — section 3 (the crosswalk's
Mapping A, four concerns) for the nodes, section 4 (check -> primary/also concern, sixteen rows)
for the edges. The script fails loudly if either table has the wrong shape, so a later edit to
the ruling that changes a row cannot pass silently.

Through `scripts/framework_writeback.py::save` only (the single-writer rule,
`tests/test_framework_single_writer.py`): this module builds nodes and edges in memory and hands
them to `save`, which recounts, refuses any drop without `--force --reason`, and puts the delta
on the `framework_writeback` event. A re-run upserts by identity and so writes the same bytes
(`save` reports `unchanged`). A write-back is not finished until a projection follows it
(DD-057): run `scripts/load_framework_graph.py` and `tests/test_framework_projection_roundtrip.py`.

    /opt/anaconda3/bin/python3 scripts/apply_fcsm_concerns.py [--dry-run] [--force --reason TEXT]
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

import framework_writeback as fw  # noqa: E402

SCRIPT = "scripts/apply_fcsm_concerns.py"
TASK = "cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md"
DN018 = REPO / "docs" / "design" / "2026-10-21_DN-018_si_readiness_is_fcsm_accessibility_for_a_machine_user.md"

#: Fixed by DN-018 section 2: the dimension, its domain, the framework it is published in, the
#: citation for the crosswalk the four concerns come from, and the fss-policy-kg segment that
#: holds the dimension's verbatim definition. Not thresholds — identity of the source.
DIMENSION, DOMAIN, FRAMEWORK = "Accessibility", "Utility", "FCSM 20-04"
SOURCE = "Webb 2026, doi:10.5281/zenodo.18772590, v2"
DEFINITION_SEGMENT = "fcsm_20_04#s389"

#: The sixteen instrument legs, in the matrix/leg convention, used only to validate that the
#: section-4 table names exactly these checks. A11's spec id carries the `-declared` suffix.
EXPECTED_CHECKS = {"A1", "A2", "A3", "A4", "A5", "A6", "A8", "A9", "A10", "A11", "A12", "A13",
                   "B3", "D1", "D4", "F4"}


def _table_rows(text: str, header_contains: str, first_cell: re.Pattern) -> list[list[str]]:
    """Every data row of the first markdown table whose header line contains `header_contains`.

    A data row is a `| ... |` line whose first cell matches `first_cell`; the header and the
    `|---|` separator are skipped, and parsing stops at the first non-table line after the header.
    Each row is returned as its list of stripped cell strings (outer pipes removed)."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.lstrip().startswith("|")
                  and header_contains in l), None)
    if start is None:
        raise SystemExit(f"FATAL: DN-018 has no table whose header contains {header_contains!r}")
    rows = []
    for l in lines[start + 1:]:
        s = l.strip()
        if not s.startswith("|"):
            break
        cells = [c.strip() for c in s.strip("|").split("|")]
        if first_cell.match(cells[0]):
            rows.append(cells)
    return rows


def concern_id(code: str) -> str:
    """`C1` -> `fcsm_20_04_accessibility_c1`. The ids the task fixes (Part A item 1)."""
    return f"fcsm_20_04_accessibility_c{code[1:]}"


def parse_concerns() -> list[dict]:
    """The four FcsmConcern nodes from DN-018 section 3's Mapping A table, text verbatim."""
    rows = _table_rows(DN018.read_text(encoding="utf-8"),
                       "FCSM 20-04 Accessibility concern", re.compile(r"^C\d$"))
    if len(rows) != 4:
        raise SystemExit(f"FATAL: DN-018 section 3 has {len(rows)} concern rows, expected 4")
    nodes = []
    for code, text, rmf in ((r[0], r[1], r[2]) for r in rows):
        if rmf != "none":
            raise SystemExit(f"FATAL: concern {code} RMF equivalent is {rmf!r}, expected 'none'")
        nodes.append({"id": concern_id(code), "labels": ["FcsmConcern"], "properties": {
            "dimension": DIMENSION, "domain": DOMAIN, "framework": FRAMEWORK,
            "text": text, "source": SOURCE, "rmf_equivalent": rmf,
            "definition_segment": DEFINITION_SEGMENT}})
    return nodes


def parse_edges(spec_by_code: dict, concern_ids: set) -> list[dict]:
    """The twenty-three SERVES_FCSM_CONCERN edges from DN-018 section 4's table: one `primary`
    per check, one `also` where the table lists a second concern. Fails on any shape surprise."""
    rows = _table_rows(DN018.read_text(encoding="utf-8"),
                       "| Check | Name |", re.compile(r"^[A-G]\d{1,2}$"))
    if len(rows) != 16:
        raise SystemExit(f"FATAL: DN-018 section 4 has {len(rows)} check rows, expected 16")
    codes = {r[0] for r in rows}
    if codes != EXPECTED_CHECKS:
        raise SystemExit(f"FATAL: section 4 checks {sorted(codes)} != {sorted(EXPECTED_CHECKS)}")
    edges = []
    for code, _name, primary, also in ((r[0], r[1], r[2], r[3]) for r in rows):
        if code not in spec_by_code:
            raise SystemExit(f"FATAL: no instrument MeasurementSpec for check {code}")
        for role, concern in (("primary", primary), ("also", also)):
            if not concern:
                continue
            cid = concern_id(concern)
            if cid not in concern_ids:
                raise SystemExit(f"FATAL: {code} {role} concern {concern!r} is not one of the four")
            edges.append({"from": spec_by_code[code], "type": "SERVES_FCSM_CONCERN",
                          "to": cid, "properties": {"role": role}})
    n_primary = sum(1 for e in edges if e["properties"]["role"] == "primary")
    n_also = sum(1 for e in edges if e["properties"]["role"] == "also")
    if (n_primary, n_also, len(edges)) != (16, 7, 23):
        raise SystemExit(f"FATAL: edges are primary={n_primary} also={n_also} total={len(edges)}, "
                         "expected 16 / 7 / 23")
    return edges


def spec_by_code(g: dict) -> dict:
    """`{indicator_code: spec_id}` for the sixteen instrument specs (`instrument_state` set)."""
    out = {}
    for n in g["nodes"]:
        p = n["properties"]
        if "MeasurementSpec" in n["labels"] and p.get("instrument_state"):
            out[p["indicator_code"]] = n["id"]
    return out


def build(g: dict) -> dict:
    """Upsert the four nodes and twenty-three edges into `g` by identity, and set the two counts
    keys. Idempotent: a second call reproduces the same record (so `save` writes nothing)."""
    nodes = parse_concerns()
    concern_ids = {n["id"] for n in nodes}
    edges = parse_edges(spec_by_code(g), concern_ids)

    by_id = {n["id"]: i for i, n in enumerate(g["nodes"])}
    for node in nodes:
        if node["id"] in by_id:
            g["nodes"][by_id[node["id"]]] = node
        else:
            g["nodes"].append(node)
    eidx = {fw._edge_key(e): i for i, e in enumerate(g["edges"])}
    for e in edges:
        k = fw._edge_key(e)
        if k in eidx:
            g["edges"][eidx[k]] = e
        else:
            g["edges"].append(e)
    g.setdefault("counts", {})
    g["counts"]["fcsm_concern_nodes"] = len(nodes)
    g["counts"]["serves_fcsm_concern_edges"] = len(edges)
    return g


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    g = build(fw.load())
    ev = fw.save(g, script=SCRIPT, task=TASK,
                 changes={"implements": "DN-018", "concern_nodes": g["counts"]["fcsm_concern_nodes"],
                          "serves_fcsm_concern_edges": g["counts"]["serves_fcsm_concern_edges"]},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({"written": ev["written"], "unchanged": ev.get("unchanged", False),
                      "event_id": ev.get("event_id"), "framework_sha256": ev["framework_sha256"],
                      "delta": ev["delta_summary"], "counts_fcsm": {
                          "fcsm_concern_nodes": g["counts"]["fcsm_concern_nodes"],
                          "serves_fcsm_concern_edges": g["counts"]["serves_fcsm_concern_edges"]}},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
