#!/usr/bin/env python3
"""The executive-summary grid: page two of the summary, as data. **Zero spend, no network.**

`cc_tasks/2026-10-14_executive_summary_v3_grid.md` Part B, under DN-014 ADDENDUM 01 §2. Reads
the cycle of record's product matrix and tier-A matrix (and the cycle's findings, for the one
thing a matrix does not carry: the reason a cell failed), the framework of record (plain names,
the declared flag, the fix line of each action), and writes `reports/summary/grid.json`.

**The grid is the PUBLIC tier.** Columns are the public-tier checks (`tier == public`) that the
cycle's matrices judge, minus the checks that record a declaration (`declared: true`) and minus
candidate checks (DD-054: the framework does not adopt what the instrument found about itself).
Page one says the results come from the public tier; this is that tier, agency by agency.

**A cell is one of three states** (ADDENDUM §2, after accessibility conformance reporting's
supports / partially supports / does not support):

* **pass**  — every one of the agency's data pages passes the check;
* **fail**  — no page passes it;
* **partial** — at least one page passes and at least one does not.

A page passes iff its verdict is `pass`; a `fail` or an `error` (an access denial, an absence the
machine could not even confirm, a server error) is a page that did not meet the check. A single
page can only pass or fail.

**The fix under a column** is the record's action for the failing outcome the most agencies hit
on that check across the cycle. The matrix carries verdicts, not reasons, so the outcome of a
failing cell is read by matching each action's verbatim reason fragment (the REMEDIATES edge's
`reason_fragment`) against the finding's reason. Ties break toward the outcome that names the
absence of the thing (publishing it is the more basic fix), then the lexically smaller outcome.
Where no cell of the check carries verdict `fail` (every non-pass was an access error), the
column names the fix for the check's absence outcome.

    /opt/anaconda3/bin/python3 scripts/summary_grid.py
    /opt/anaconda3/bin/python3 scripts/summary_grid.py --check    # Part A/B presence gate only
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

GENERATOR = "scripts/summary_grid.py"
TASK = "cc_tasks/2026-10-14_executive_summary_v3_grid.md"
RECORD = REPO / "framework" / "ai_readiness_framework.json"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
REPORTS = REPO / "docs" / "reports"
STATE = REPO / "state"
FRAME = REPO / "state" / "scan_targets_fss_2026-09_v5.json"
OUT = REPO / "reports" / "summary" / "grid.json"

#: The tier-A matrix is per host (one row per agency); the product matrix is per data page
#: (one row per declared surface). A tier-A leg's cell is the host verdict; a product leg's cell
#: rolls up the agency's pages.
TIERA_LEGS_SOURCE = "tierA"
PRODUCT_LEGS_SOURCE = "product"


# ---------------------------------------------------------------------------------- inputs

def load_cycle() -> str:
    pub = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))
    return pub["snapshot_cycle"]


def matrix_rel(kind: str, cycle: str) -> str:
    # the matrix filename carries the cycle WITHOUT its `scan_` prefix
    stem = cycle[len("scan_"):] if cycle.startswith("scan_") else cycle
    return f"docs/reports/scan_matrix_{kind}_{stem}.json"


def matrix_path(kind: str, cycle: str) -> Path:
    return REPO / matrix_rel(kind, cycle)


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def agency_names() -> dict:
    t = load_json(FRAME)
    return {d["agency"]: d["agency_name"] for d in t["agency_detail"]}


def record_views(g: dict) -> dict:
    """What the grid needs from the record: per indicator code its plain_name, tier, status and
    declared flag; per leg the list of (outcome, action_id, reason_fragment, fix_line); the tier
    display names."""
    inds, rem = {}, defaultdict(list)
    acts = {n["id"]: n["properties"] for n in g["nodes"] if "Action" in n["labels"]}
    for n in g["nodes"]:
        if "AssessmentIndicator" in n["labels"]:
            p = n["properties"]
            inds[p["code"]] = {"plain_name": p.get("plain_name"), "tier": p.get("tier"),
                               "status": p.get("status"), "declared": bool(p.get("declared")),
                               "construct": p.get("construct"), "id": n["id"]}
    for e in g["edges"]:
        if e["type"] == "REMEDIATES":
            p = e["properties"]
            a = acts.get(e["from"], {})
            rem[p["leg"]].append({"outcome": p["outcome"], "action_id": e["from"],
                                  "reason_fragment": p.get("reason_fragment") or "",
                                  "fix_line": a.get("fix_line")})
    tiers = {k: v["display_name"] for k, v in (g.get("measurement_tiers") or {}).items()}
    return {"indicators": inds, "remediates": rem, "tier_display_names": tiers}


# ------------------------------------------------------------------------------- columns

def select_columns(matrices: dict, inds: dict) -> list[str]:
    """Public-tier, non-declared, non-candidate legs the matrices judge, in code order."""
    legs = []
    for kind, m in matrices.items():
        for leg in m["legs"]:
            code = leg.replace("-declared", "")
            ind = inds.get(code)
            if ind is None:
                continue
            if ind["tier"] != "public" or ind["declared"] or ind["status"] == "candidate":
                continue
            if leg not in legs:
                legs.append(leg)

    def key(leg: str):
        c = leg[0]
        n = "".join(ch for ch in leg[1:] if ch.isdigit())
        return (c, int(n) if n else 0)

    return sorted(legs, key=key)


def leg_source(leg: str, matrices: dict) -> str:
    for kind, m in matrices.items():
        if leg in m["legs"]:
            return kind
    raise KeyError(leg)


# -------------------------------------------------------------------------- cell state

def _passes(verdict: str) -> bool:
    return verdict == "pass"


def agency_cells(agency: str, leg: str, kind: str, matrices: dict) -> list[dict]:
    """Every (page/host) cell for an agency on a leg, with its verdict, surface, finding id, and
    a matrix locator."""
    m = matrices[kind]
    path = matrix_rel(kind, m["cycle"])
    out = []
    for r in m["rows"]:
        if r["agency"] != agency:
            continue
        v = r["verdicts"].get(leg)
        if v is None:
            continue
        surface = r.get("surface") or r.get("host_surface") or r.get("candidate_surface") or ""
        out.append({"surface": surface, "verdict": v,
                    "finding_id": r.get("finding_ids", {}).get(leg),
                    "locator": {"kind": "matrix", "path": path,
                                "cell": f"{agency}/{leg}", "surface": surface, "verdict": v}})
    return out


def roll_up(cells: list[dict]) -> str:
    passed = sum(1 for c in cells if _passes(c["verdict"]))
    total = len(cells)
    if total == 0:
        return "none"
    if passed == total:
        return "pass"
    if passed == 0:
        return "fail"
    return "partial"


# ---------------------------------------------------------------- fix line per column

def choose_outcome(leg: str, matrices: dict, kind: str, findings: dict, rem: list[dict]) -> dict:
    """The failing outcome the most agencies hit on this leg, computed over the matrix's `fail`
    cells by matching each action's reason fragment against the finding's reason. Returns the
    chosen remediation row and the ranking; falls back to the absence outcome when no cell fails
    on content."""
    frags = [(r["outcome"], r["reason_fragment"]) for r in rem if r["reason_fragment"]]
    by_outcome = defaultdict(set)
    m = matrices[kind]
    for r in m["rows"]:
        v = r["verdicts"].get(leg)
        if v != "fail":
            continue
        fid = r.get("finding_ids", {}).get(leg)
        reason = (findings.get(fid) or {}).get("reason") or ""
        hits = [o for o, fr in frags if fr and fr in reason]
        if hits:
            by_outcome[hits[0]].add(r["agency"])
    ranking = sorted(((o, sorted(a)) for o, a in by_outcome.items()),
                     key=lambda kv: (-len(kv[1]), 0 if kv[0].startswith("no_") else 1, kv[0]))
    if ranking:
        chosen = ranking[0][0]
        basis = {"rule": "most_agencies", "agencies": len(ranking[0][1])}
    else:
        nos = sorted(r["outcome"] for r in rem if r["outcome"].startswith("no_"))
        chosen = nos[0] if nos else sorted(r["outcome"] for r in rem)[0]
        basis = {"rule": "absence_fallback",
                 "why": "no matrix cell for this check carries verdict fail; every non-pass was "
                        "an access error, so the column names the fix for publishing the object"}
    row = next(r for r in rem if r["outcome"] == chosen)
    return {"outcome": chosen, "action_id": row["action_id"], "fix_line": row["fix_line"],
            "basis": basis, "ranking": [{"outcome": o, "agencies": len(a)} for o, a in ranking]}


# ---------------------------------------------------------------------------------- build

def build(out_path: Path = OUT) -> dict:
    cycle = load_cycle()
    matrices = {PRODUCT_LEGS_SOURCE: load_json(matrix_path("product", cycle)),
                TIERA_LEGS_SOURCE: load_json(matrix_path("tierA", cycle))}
    g = load_json(RECORD)
    rv = record_views(g)
    inds, rem_all = rv["indicators"], rv["remediates"]
    findings = {f["finding_id"]: f for f in load_json(STATE / f"{cycle}.json")["findings_detail"]}
    names = agency_names()

    bodies = list(dict.fromkeys(r["agency"] for m in matrices.values() for r in m["rows"]))
    bodies = sorted(bodies, key=lambda b: names.get(b, b).lower())

    columns_legs = select_columns(matrices, inds)
    sources = {leg: leg_source(leg, matrices) for leg in columns_legs}

    # page count per agency = number of product surfaces (data pages) it carries
    page_count = defaultdict(int)
    for r in matrices[PRODUCT_LEGS_SOURCE]["rows"]:
        page_count[r["agency"]] += 1

    missing_plain = [leg for leg in columns_legs
                     if not (inds[leg.replace("-declared", "")].get("plain_name"))]

    columns = []
    for leg in columns_legs:
        code = leg.replace("-declared", "")
        ch = choose_outcome(leg, matrices, sources[leg], findings, rem_all[leg])
        columns.append({"leg": leg, "code": code,
                        "plain_name": inds[code]["plain_name"],
                        "construct": inds[code]["construct"],
                        "source_matrix": sources[leg],
                        "fix_line": ch["fix_line"], "fix_outcome": ch["outcome"],
                        "fix_basis": ch["basis"], "fix_ranking": ch["ranking"]})

    missing_fix = [c["leg"] for c in columns if not c["fix_line"]]

    rows = []
    state_counts = {"pass": 0, "fail": 0, "partial": 0, "none": 0}
    for b in bodies:
        cells = {}
        for leg in columns_legs:
            cl = agency_cells(b, leg, sources[leg], matrices)
            state = roll_up(cl)
            state_counts[state] = state_counts.get(state, 0) + 1
            cells[leg] = {"agency": b, "check": leg, "state": state,
                          "pages": [{"surface": c["surface"], "verdict": c["verdict"],
                                     "finding_id": c["finding_id"]} for c in cl],
                          "locators": [c["locator"] for c in cl]}
        rows.append({"agency": b, "display_name": names.get(b, b),
                     "page_count": page_count.get(b, 0), "cells": cells})

    multi_page = sorted(b for b in bodies if page_count.get(b, 0) > 1)
    footnote = (
        "A check is pass where every one of an agency's data pages meets it, fail where none do, "
        "and partial where some do and some do not; a page that returned an access denial, an "
        "unconfirmable absence or a server error is counted as not meeting the check, and an "
        "agency with one data page can only pass or fail. "
        "The fix under a check is the action for the failing outcome the most agencies hit on "
        "that check across this measurement. "
        f"Measured across all sixteen federal statistical agencies in {cycle_date(cycle)}."
    )
    grid = {
        "generated_by": GENERATOR, "task": TASK, "cycle": cycle,
        "tier": "public", "tier_display_name": rv["tier_display_names"].get("public", "public tier"),
        "matrices": {k: matrix_rel(k, cycle) for k in matrices},
        "excluded": {
            "declared": sorted({leg for m in matrices.values() for leg in m["legs"]
                                if inds.get(leg.replace("-declared", ""), {}).get("declared")}),
            "candidate": sorted({leg for m in matrices.values() for leg in m["legs"]
                                 if inds.get(leg.replace("-declared", ""), {}).get("status") == "candidate"}),
            "non_public": sorted({leg for m in matrices.values() for leg in m["legs"]
                                  if inds.get(leg.replace("-declared", ""), {}).get("tier")
                                  not in (None, "public")}),
        },
        "columns": columns, "rows": rows,
        "state_counts": state_counts, "multi_page_agencies": multi_page,
        "legend": {"pass": "every data page meets the check",
                   "partial": "some data pages meet the check, some do not",
                   "fail": "no data page meets the check"},
        "footnote": footnote,
        "presence_gate": {"missing_plain_name": missing_plain, "missing_fix_line": missing_fix},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(grid, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return grid


def cycle_date(cycle: str) -> str:
    """'October 2026' from a cycle id like scan_2026-10-07_composite_d."""
    import re
    m = re.search(r"(\d{4})-(\d{2})-\d{2}", cycle)
    if not m:
        return cycle
    months = ["January", "February", "March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December"]
    return f"{months[int(m.group(2)) - 1]} {m.group(1)}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true",
                    help="write the grid, then fail if any column lacks a plain_name or fix_line")
    a = ap.parse_args(argv)
    grid = build(Path(a.out))
    pg = grid["presence_gate"]
    print(json.dumps({"cycle": grid["cycle"], "columns": len(grid["columns"]),
                      "rows": len(grid["rows"]), "state_counts": grid["state_counts"],
                      "multi_page_agencies": grid["multi_page_agencies"],
                      "excluded": grid["excluded"], "presence_gate": pg}, indent=1))
    if a.check and (pg["missing_plain_name"] or pg["missing_fix_line"]):
        print(f"FATAL: missing plain_name {pg['missing_plain_name']} or "
              f"fix_line {pg['missing_fix_line']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
