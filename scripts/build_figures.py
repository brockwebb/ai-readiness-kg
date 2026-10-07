#!/usr/bin/env python3
"""The three figures the summary needs, generated from the record. **Zero spend, no network.**

`cc_tasks/2026-10-02_summary_figures.md`, under DN-009 decisions 1 and 7: the operator's finding
on the deck was that nothing in it showed what was built relative to USAFacts or what the tests
found. These are the three pictures that do. They are views of the framework (DN-005), so no
indicator, rule, verdict or document is created or changed here.

    scripts/build_figures.py           write every file under docs/figures/
    scripts/build_figures.py --check   re-render into memory; exit 1 on any drift (SVG, caption,
                                       CSV and ledger by bytes; PNG by decoded pixels, because
                                       PNG encoders are not byte-stable)

**Sources, and only these** (the same two-sources rule as `scripts/score.py`): the framework
record (`framework/ai_readiness_framework.json`) and the published matrices of the cycle of
record (`docs/reports/publication.yaml: snapshot_cycle`), read through `scripts/score.py`; the
cycle's event shard for its Finding count; the corpus manifest for the admitted count; the rule
registry; the crosswalk skeleton for USAFacts' criterion names; the frame's target DataFile for
body names; and `docs/evidence/claims.yaml`, whose table Q2 gives the access-denial counts and
whose ids the captions cite. Neo4j is not read: every count here is a framework or cycle fact,
and the record answers framework questions even when the graph holds the same nodes.

**Figures.** 1, USAFacts to framework (`fig1_usafacts_to_framework`); 2, the system at a glance
(`fig2_system_at_a_glance`); 3, the pass/fail table (`fig3_pass_fail_table`, plus a CSV of the
same cells). Each ships as SVG, PNG at the layout's dpi, and a `.caption.md`.

**Numbers.** No numeral is typed onto a figure. Every number a figure prints goes through
`Ledger.n(value, source)`, which records it in `docs/figures/numbers.json` under the figure;
`tests/test_figures.py` reads every text element of every figure and fails on a numeral that
figure's ledger does not hold. Layout, sizes and colours come from `docs/figures/layout.yaml`.

**Renderer.** matplotlib (3.8, the anaconda install). The in-repo prior art was weighed:
`scripts/build_brief_deck.py --render-diagrams` draws Mermaid with `mmdc`, which cannot draw a
proportional bar or a colour-scaled table; `assessment/harness/scan/figures.py` hand-writes SVG
for one cycle's charts, which gives no PNG without a second rasteriser. matplotlib draws all
three figures with one tool, writes SVG and PNG from the same drawing, and its SVG is
byte-stable once `svg.hashsalt` and the date metadata are fixed. From `figures.py` this script
keeps its rule that rows are never reordered by score: figure 3's rows are in roster order.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import yaml  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

OUT = REPO / "docs" / "figures"
LAYOUT = OUT / "layout.yaml"
LEDGER = OUT / "numbers.json"
CLAIMS = REPO / "docs" / "evidence" / "claims.yaml"
RECORD = REPO / "framework" / "ai_readiness_framework.json"
SKELETON = REPO / "docs" / "crosswalk" / "usafacts_operationalization_skeleton.md"
MANIFEST = REPO / "corpus" / "manifest.json"
FRAME = REPO / "assessment" / "harness" / "scan" / "frames" / "fss16.yaml"
TASK = "cc_tasks/2026-10-02_summary_figures.md"
GENERATOR = "scripts/build_figures.py"

FIG1 = "fig1_usafacts_to_framework"
FIG2 = "fig2_system_at_a_glance"
FIG3 = "fig3_pass_fail_table"
FIGURES = (FIG1, FIG2, FIG3)

#: The criteria USAFacts named. Skeleton **Frame:** line: "USAFacts' four criteria (accessible,
#: understandable, accurate, open) as the top-level structure". The names are PARSED from that
#: line (`usafacts_names`) and checked against the record's names for these codes.
USAFACTS_CRITERIA = ("A", "B", "C", "D")

#: The measurement states of figure 1, in bar order. Every framework indicator is in exactly one.
STATES = ("measured_cycle", "rule_not_cycle", "measured_eval", "specified")
STATE_LABELS = {
    "measured_cycle": "measured on the cycle of record",
    "rule_not_cycle": "rule built, not judged on the cycle",
    "measured_eval": "measured outside the scan (evaluation)",
    "specified": "specified only",
}

#: The record's `measurement_status` value that means "no rule, no measurement" (CL-049's term).
SPECIFIED = "specified"


# ------------------------------------------------------------------------------ inputs

def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def layout() -> dict:
    return yaml.safe_load(LAYOUT.read_text(encoding="utf-8"))


def code_key(code: str) -> tuple:
    m = re.match(r"([A-Z])(\d+)(.*)", code)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (code, 0, "")


def usafacts_names() -> list:
    """USAFacts' four criterion names, parsed from the skeleton's **Frame:** line."""
    for line in SKELETON.read_text(encoding="utf-8").splitlines():
        m = re.search(r"USAFacts' four criteria \(([^)]*)\)", line)
        if line.startswith("**Frame:**") and m:
            names = [x.strip() for x in m.group(1).split(",")]
            if len(names) != len(USAFACTS_CRITERIA):
                raise SystemExit(f"FATAL: the skeleton's Frame line names {len(names)} USAFacts "
                                 f"criteria, not {len(USAFACTS_CRITERIA)}: {names}")
            return names
    raise SystemExit(f"FATAL: {SKELETON.relative_to(REPO)} has no **Frame:** line naming "
                     "USAFacts' four criteria; figure 1's left column has no source")


def body_names() -> dict:
    """`{body code: display name}` from the frame's target DataFile (the 72-row frame the cycle
    measured). The display name is the agency name up to its first comma, so a unit named
    "<office>, <parent>" shows its office; the code is printed beside it."""
    frame = yaml.safe_load(FRAME.read_text(encoding="utf-8"))
    path = REPO / "state" / f"{frame['targets']}.json"
    if not path.is_file():
        raise SystemExit(f"FATAL: {path.relative_to(REPO)} (the frame's target DataFile) is "
                         "missing; figure 3 cannot name its bodies")
    out = {}
    for r in load_json(path)["rows"]:
        out.setdefault(r["agency"], r["agency_name"].strip())
    return out


def admitted_documents() -> int:
    """Manifest entries whose screening decision is `included`: CL-044's count, by its rule."""
    entries = load_json(MANIFEST)["entries"]
    return sum(1 for v in entries.values() if v["screening"]["decision"] == "included")


def cycle_findings(cycle: str) -> int:
    """`finding_derived` events of the cycle in its shard: CL-051's count, by its rule.

    A COMPOSITE cycle of record (`scan.composite`) has no shard of its own: its count is the
    Findings its payload selects, each of which must be on its part's shard under its part's
    cycle (`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` decision 4)."""
    payload_file = REPO / "state" / f"{cycle}.json"
    if payload_file.is_file():
        from scan import composite
        p = load_json(payload_file)
        if composite.is_composite(p):
            on_log: set = set()
            for part, _legs in composite.parts(p):
                shard = REPO / "events" / f"cycle-{part}.jsonl"
                for line in shard.read_text(encoding="utf-8").splitlines():
                    if '"finding_derived"' in line:
                        e = json.loads(line)
                        if e.get("cycle") == part:
                            on_log.add(e["finding_id"])
            ids = [f["finding_id"] for f in p["findings_detail"]]
            missing = [i for i in ids if i not in on_log]
            if missing or len(set(ids)) != len(ids):
                raise SystemExit(f"FATAL: {len(missing)} of the composite's Findings are on no "
                                 f"part's shard, or one is listed twice")
            return len(ids)
    shard = REPO / "events" / f"cycle-{cycle}.jsonl"
    if not shard.is_file():
        raise SystemExit(f"FATAL: {shard.relative_to(REPO)} is missing; the cycle of record "
                         "has no event shard to count its Findings from")
    ids = set()
    for line in shard.read_text(encoding="utf-8").splitlines():
        if '"finding_derived"' not in line:
            continue
        e = json.loads(line)
        if e.get("event_type") == "finding_derived" and e.get("cycle") == cycle:
            if e["finding_id"] in ids:
                raise SystemExit(f"FATAL: {e['finding_id']} derived twice in {shard.name}")
            ids.add(e["finding_id"])
    return len(ids)


def claims() -> dict:
    return yaml.safe_load(CLAIMS.read_text(encoding="utf-8"))


def denials(cl: dict) -> dict:
    """`{body: (access_denial, findings)}` from the evidence map's table Q2."""
    return {r["body"]: (r["access_denial"], r["findings"])
            for r in cl["tables"]["q2_findings_by_body"]}


def criterion_of(record: dict) -> dict:
    """`{indicator id: criterion code}` by walking DECOMPOSES_INTO criterion → construct →
    indicator. Exactly one parent at each level, or the record is not the shape the figure
    draws."""
    nodes = {n["id"]: n for n in record["nodes"]}
    parent: dict = {}
    for e in record["edges"]:
        if e["type"] == "DECOMPOSES_INTO":
            parent.setdefault(e["to"], []).append(e["from"])
    out = {}
    for n in record["nodes"]:
        if "AssessmentIndicator" not in n["labels"]:
            continue
        cons = parent.get(n["id"], [])
        if len(cons) != 1:
            raise SystemExit(f"FATAL: {n['id']} decomposes from {len(cons)} constructs")
        crits = parent.get(cons[0], [])
        if len(crits) != 1:
            raise SystemExit(f"FATAL: {cons[0]} decomposes from {len(crits)} criteria")
        out[n["id"]] = nodes[crits[0]]["properties"]["code"]
    return out


def compute() -> dict:
    """Every number the three figures print, from the sources named in the module docstring."""
    import score as S
    from framework_writeback import _candidate_ids
    from scan import rules as R

    record = load_json(RECORD)
    r = S.compute()
    cycle = r["cycle"]["name"]
    cand = _candidate_ids(record)
    crit_of = criterion_of(record)
    names = S.criterion_names(record)

    # Indicators with a current rule: the rule id parses to the indicator's code.
    rule_codes = {R.parse_rule_id(rid)["indicator_code"] for rid in R.CURRENT.values()}
    # `cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md` decision 3 (audit C-07): the
    # figure's "measured" is the RECORD's, so it is the number the progress page and the brief
    # print, under the same name. Measured on the cycle of record: `measured_by.cycle` names it
    # (the write-back re-derives every scan-measured node against that cycle, DD-069). Measured
    # outside the scan: `measured` with no scan cycle behind it (G1-O, DD-036). score.py's own
    # coverage is "scored", a different quantity under a different name.

    crit_rows = []
    for code in r["framework"]["criteria"]:
        inds = sorted((n for n in record["nodes"] if "AssessmentIndicator" in n["labels"]
                       and n["id"] not in cand and crit_of[n["id"]] == code),
                      key=lambda n: code_key(n["properties"]["code"]))
        states = {s: [] for s in STATES}
        for n in inds:
            p = n["properties"]
            measured = p.get("measurement_status") == "measured"
            if measured and (p.get("measured_by") or {}).get("cycle") == cycle:
                s = "measured_cycle"
            elif measured and not p.get("measured_by"):
                s = "measured_eval"
            elif measured:
                raise SystemExit(f"FATAL: {n['id']} is `measured` by "
                                 f"{p['measured_by'].get('cycle')!r}, not by the cycle of "
                                 f"record {cycle!r}; run the measured write-back against it "
                                 "(scripts/framework_writeback_measured.py --cycle)")
            elif p["code"] in rule_codes:
                s = "rule_not_cycle"
            elif p.get("measurement_status") == SPECIFIED:
                s = "specified"
            else:
                raise SystemExit(f"FATAL: {n['id']} has no rule, is not judged on the cycle and "
                                 f"its measurement_status is {p.get('measurement_status')!r}; "
                                 "figure 1 has no state for it")
            states[s].append(p["code"])
        crit_rows.append({
            "code": code, "name": names[code], "kept": code in USAFACTS_CRITERIA,
            "indicators": len(inds),
            "rule": sum(1 for n in inds if n["properties"]["code"] in rule_codes),
            "states": states,
        })
    total = sum(c["indicators"] for c in crit_rows)
    measured_n = sum(len(c["states"][k]) for c in crit_rows
                     for k in ("measured_cycle", "measured_eval"))
    if measured_n != record["counts"]["indicators_measured"]:
        raise SystemExit(f"FATAL: figure 1 counts {measured_n} measured indicators and the "
                         f"record's counts.indicators_measured is "
                         f"{record['counts']['indicators_measured']}; one name, one value")
    if total != r["framework"]["indicators"] or total != record["counts"]["indicators"]:
        raise SystemExit(f"FATAL: figure 1 counts {total} framework indicators; score.py says "
                         f"{r['framework']['indicators']} and the record's counts say "
                         f"{record['counts']['indicators']}")

    uf = usafacts_names()
    for code, nm in zip(USAFACTS_CRITERIA, uf):
        if names[code].lower() != nm.lower():
            raise SystemExit(f"FATAL: the skeleton names USAFacts criterion {code} {nm!r}; the "
                             f"record names it {names[code]!r}")

    cl = claims()
    den = denials(cl)
    bn = body_names()
    from build_brief_pack import DOGFOOD_BODY
    rows = []
    for b in sorted(r["bodies"]):
        v = r["bodies"][b]
        cells = {}
        for code in r["framework"]["criteria"]:
            legs = [l["leg"] for l in r["structure"] if l["scored"] and l["criterion"] == code]
            judged = [v["legs"][leg] for leg in legs if v["legs"].get(leg, {}).get("judged")]
            cells[code] = None if not judged else {
                # A leg passes when every judged row on it passes (score.py's gating reading:
                # `legs_passed_outright`).
                "passed": sum(1 for x in judged if x["pass"] == x["judged"]),
                "judged": len(judged),
            }
        c = v.get("concentration")
        if b not in bn:
            raise SystemExit(f"FATAL: body {b} is on the cycle but not in the frame DataFile")
        if v["score"] is None and b not in den:
            raise SystemExit(f"FATAL: {b} is unranked and the evidence map's table Q2 has no "
                             "row for it, so the figure cannot say why")
        rows.append({
            "body": b, "name": bn[b], "cells": cells, "score": v["score"],
            "rank": v["rank"], "of": c["of"] if c else None,
            "leg": c["leg"] if c else None,
            "rank_if_reversed": c["rank_if_reversed"] if c else None,
            "denials": den.get(b), "highlight": b == DOGFOOD_BODY,
        })

    return {
        "cycle": cycle,
        "usafacts": uf,
        "criteria": crit_rows,
        "framework_indicators": total,
        "rule_indicators": sum(c["rule"] for c in crit_rows),
        "measured_cycle": sum(len(c["states"]["measured_cycle"]) for c in crit_rows),
        "measured": measured_n,
        "specified": sum(len(c["states"]["specified"]) for c in crit_rows),
        "documents": admitted_documents(),
        "rules": len(set(R.CURRENT.values())),
        "bodies": r["cycle"]["n_bodies"],
        "ranked": r["coverage"]["bodies"]["measured"],
        "findings": cycle_findings(cycle),
        "rows": rows,
        "claim_ids": {c["id"] for c in cl["claims"]},
    }


# ------------------------------------------------------------------------------ the ledger

class Ledger:
    """Every number a figure prints, with its source. `n` returns the number as shown."""

    def __init__(self):
        self.rows: dict = {f: [] for f in FIGURES}
        self.fig = None

    def n(self, value, source: str, fmt: str | None = None) -> str:
        if isinstance(value, float):
            shown = format(value, fmt or ".3f")
        elif isinstance(value, int) and abs(value) >= 1000:
            shown = f"{value:,}"
        else:
            shown = str(value)
        entry = {"value": shown, "source": source}
        if entry not in self.rows[self.fig]:
            self.rows[self.fig].append(entry)
        return shown

    def text(self) -> str:
        return json.dumps(self.rows, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


# ------------------------------------------------------------------------------ drawing

def setup(L: dict) -> None:
    plt.rcParams.update({
        "font.family": L["render"]["font_family"],
        "svg.fonttype": "path",
        "svg.hashsalt": L["render"]["svg_hashsalt"],
        "figure.facecolor": L["palette"]["surface"],
        "savefig.facecolor": L["palette"]["surface"],
    })


def canvas(size: list, xlim: float, ylim: float, L: dict):
    fig = plt.figure(figsize=size)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, ylim)
    ax.axis("off")
    ax.set_facecolor(L["palette"]["surface"])
    return fig, ax


def box(ax, x, y, w, h, face, edge, lw=1.2, style="round,pad=0.02,rounding_size=0.08"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, facecolor=face,
                                edgecolor=edge, linewidth=lw))


def arrow(ax, x0, y0, x1, y1, color, lw=1.4):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14,
                                 color=color, linewidth=lw, shrinkA=0, shrinkB=0))


def fig1(d: dict, L: dict, led: Ledger):
    """USAFacts' four criteria → the framework's seven → each criterion's indicators by state."""
    led.fig = FIG1
    P, F = L["palette"], L["fig1"]
    rows = d["criteria"]
    rh = F["row_height"]
    top = F["size_in"][1] - 0.2
    fig, ax = canvas(F["size_in"], F["size_in"][0], F["size_in"][1], L)
    ux0, ux1 = F["usafacts_x"]
    cx0, cx1 = F["criterion_x"]
    bx0, bx1 = F["bar_x"]
    nx = F["numbers_x"]

    total = d["framework_indicators"]
    ax.text(0.2, top - 0.05,
            f"What was built on USAFacts' {led.n(len(d['usafacts']), 'USAFacts criteria named in the skeleton Frame line')} "
            f"criteria: {led.n(sum(c['kept'] for c in rows), 'criteria kept from USAFacts')} kept, "
            f"{led.n(sum(not c['kept'] for c in rows), 'criteria added')} added, "
            f"{led.n(d['measured'], 'framework indicators measured (record counts.indicators_measured)')} "
            f"of {led.n(total, 'framework indicators (record counts.indicators; candidate A12 excluded, DD-054)')} "
            f"indicators measured",
            fontsize=F["title_pt"], fontweight="bold", color=P["ink"], va="top")

    hy = top - 0.75
    ax.text(ux0, hy, "USAFacts' criteria", fontsize=F["header_pt"], fontweight="bold",
            color=P["ink_secondary"], va="bottom")
    ax.text(cx0, hy, "This framework's criteria", fontsize=F["header_pt"], fontweight="bold",
            color=P["ink_secondary"], va="bottom")
    ax.text(bx0, hy, "Each criterion's indicators, by measurement state",
            fontsize=F["header_pt"], fontweight="bold", color=P["ink_secondary"], va="bottom")
    for x, head in zip(nx, ("current\nrule", "measured\non cycle", "specified\nonly")):
        ax.text(x, hy, head, fontsize=F["small_pt"], fontweight="bold",
                color=P["ink_secondary"], ha="center", va="bottom", linespacing=1.0)

    scale = (bx1 - bx0) / max(c["indicators"] for c in rows)
    uf = {code: nm for code, nm in zip(USAFACTS_CRITERIA, d["usafacts"])}
    for i, c in enumerate(rows):
        y = top - 1.0 - (i + 1) * rh
        bh = rh * 0.68
        yc = y + bh / 2
        if c["kept"]:
            box(ax, ux0, y, ux1 - ux0, bh, P["neutral_fill"], P["kept"])
            ax.text((ux0 + ux1) / 2, yc, uf[c["code"]].capitalize(), fontsize=F["box_pt"],
                    color=P["ink"], ha="center", va="center")
            arrow(ax, ux1 + 0.05, yc, cx0 - 0.05, yc, P["kept"])
            ax.text((ux1 + cx0) / 2, yc + 0.07, "kept", fontsize=F["small_pt"],
                    color=P["ink_secondary"], ha="center", va="bottom")
            edge, face = P["kept"], P["neutral_fill"]
        else:
            ax.text(cx0 - 0.12, yc, "added", fontsize=F["small_pt"], fontweight="bold",
                    color=P["ink_secondary"], ha="right", va="center")
            edge, face = P["added"], P["surface"]
        box(ax, cx0, y, cx1 - cx0, bh, face, edge, lw=2.0 if not c["kept"] else 1.2)
        nm = display(c["name"])
        ax.text(cx0 + 0.12, yc, f"{c['code']}  {nm}", fontsize=F["box_pt"],
                fontweight="bold", color=P["ink"], va="center")
        ax.text(cx1 - 0.12, yc,
                f"{led.n(c['indicators'], 'indicators of criterion ' + c['code'])} indicators",
                fontsize=F["small_pt"], color=P["ink_secondary"], ha="right", va="center")
        x = bx0
        for s in STATES:
            n = len(c["states"][s])
            if not n:
                continue
            w = n * scale
            ax.add_patch(Rectangle((x, y), w - 0.03, bh, facecolor=P[s],
                                   edgecolor=P["rule_line"] if s == "specified" else P[s],
                                   linewidth=0.8))
            ink = "white" if s == "measured_cycle" else P["ink"]
            ax.text(x + (w - 0.03) / 2, yc,
                    led.n(n, f"criterion {c['code']} indicators {STATE_LABELS[s]}"),
                    fontsize=F["small_pt"], color=ink, ha="center", va="center",
                    fontweight="bold")
            x += w
        for xx, val, src in zip(nx, (c["rule"], len(c["states"]["measured_cycle"]),
                                     len(c["states"]["specified"])),
                                ("with a current rule", "judged on the cycle of record",
                                 "specified only (record measurement_status)")):
            ax.text(xx, yc, led.n(val, f"criterion {c['code']} indicators {src}"),
                    fontsize=F["box_pt"], color=P["ink"], ha="center", va="center")

    # Totals row.
    y = top - 1.0 - (len(rows) + 1) * rh + rh * 0.15
    ax.plot([bx0, nx[-1] + 0.45], [y + rh * 0.62, y + rh * 0.62], color=P["rule_line"], lw=1)
    ax.text(bx1, y + rh * 0.3, f"all {led.n(total, 'framework indicators (record counts.indicators; candidate A12 excluded, DD-054)')}",
            fontsize=F["box_pt"], fontweight="bold", color=P["ink"], ha="right", va="center")
    for xx, val, src in zip(nx, (d["rule_indicators"], d["measured_cycle"], d["specified"]),
                            ("framework indicators with a current rule",
                             "framework indicators measured on the cycle of record (record measured_by.cycle)",
                             "framework indicators specified only (record measurement_status)")):
        ax.text(xx, y + rh * 0.3, led.n(val, src), fontsize=F["box_pt"], fontweight="bold",
                color=P["ink"], ha="center", va="center")

    # Legend, two by two under the bars.
    for k, s in enumerate(STATES):
        lx = bx0 + (k % 2) * F["legend_col"]
        ly = F["legend_y"][k // 2]
        ax.add_patch(Rectangle((lx, ly), 0.22, 0.2, facecolor=P[s],
                               edgecolor=P["rule_line"] if s == "specified" else P[s]))
        ax.text(lx + 0.3, ly + 0.1, STATE_LABELS[s], fontsize=F["small_pt"],
                color=P["ink_secondary"], va="center")
    ax.text(ux0, F["legend_y"][-1] + 0.1, f"Cycle of record: {d['cycle']}", fontsize=F["small_pt"],
            color=P["ink_muted"], va="center")
    return fig


def fig2(d: dict, L: dict, led: Ledger):
    """The pipeline, left to right, one short label per box."""
    led.fig = FIG2
    P, F = L["palette"], L["fig2"]
    w, g, h = F["box_width"], F["box_gap"], F["box_height"]
    boxes = [
        ("Documents",
         f"{led.n(d['documents'], 'admitted corpus documents (manifest screening.decision included, CL-044)')} "
         "admitted\ndocuments: standards,\npolicy, research"),
        ("Framework",
         f"{led.n(d['framework_indicators'], 'framework indicators (record counts.indicators)')} indicators\n"
         f"grouped in\n{led.n(len(d['criteria']), 'criteria in the record')} criteria"),
        ("Rules",
         f"{led.n(d['rules'], 'current rules (len(set(rules.CURRENT.values())), CL-048)')} automated\n"
         "checks that turn\nindicators into tests"),
        ("Scan",
         f"public websites of\n{led.n(d['bodies'], 'statistical bodies on the cycle of record (CL-050)')} statistical\n"
         "agencies, visited\nwith no login"),
        ("Findings",
         f"{led.n(d['findings'], 'finding_derived events on the cycle of record (CL-051)')} findings\n"
         "recorded and frozen\nas one scan cycle"),
        ("Scores and fixes",
         f"{led.n(d['ranked'], 'bodies ranked on the cycle of record (CL-050)')} agencies scored;\n"
         "fixes ranked,\ncheapest first"),
        ("Ask the graph",
         "knowledge graph that\npeople and AI tools\ncan question (MCP)"),
    ]
    n = len(boxes)
    width = n * w + (n - 1) * g + 0.6
    fig, ax = canvas(F["size_in"], width, F["size_in"][1], L)
    ax.text(0.3, F["size_in"][1] - 0.25, "How the assessment works, end to end",
            fontsize=F["title_pt"], fontweight="bold", color=P["ink"], va="top")
    y = F["box_y"]
    groups = [("what to measure", 0, 2, P["kept"]), ("measuring", 3, 4, P["measured_cycle"]),
              ("using the results", 5, 6, P["added"])]
    for i, (title, body) in enumerate(boxes):
        x = 0.3 + i * (w + g)
        edge = next(c for _, a, b, c in groups if a <= i <= b)
        box(ax, x, y, w, h, P["neutral_fill"], edge, lw=1.6)
        ax.text(x + w / 2, y + h - 0.22, title, fontsize=F["box_title_pt"], fontweight="bold",
                color=P["ink"], ha="center", va="top")
        ax.text(x + w / 2, y + h - 0.6, body, fontsize=F["box_body_pt"], color=P["ink_secondary"],
                ha="center", va="top", linespacing=1.25)
        if i < n - 1:
            arrow(ax, x + w + 0.04, y + h / 2, x + w + g - 0.04, y + h / 2, P["ink_secondary"])
    for title, a, b, color in groups:
        x0 = 0.3 + a * (w + g)
        x1 = 0.3 + b * (w + g) + w
        ax.plot([x0, x1], [y - 0.22, y - 0.22], color=color, lw=3, solid_capstyle="butt")
        ax.text((x0 + x1) / 2, y - 0.35, title, fontsize=F["group_pt"], fontweight="bold",
                color=P["ink_secondary"], ha="center", va="top")
    return fig


def display(name: str) -> str:
    """A record criterion name as a label: ACCESSIBLE -> Accessible, release engineering ->
    Release engineering, TEVV loop unchanged."""
    return name.capitalize() if name.isupper() else name[0].upper() + name[1:]


def cell_text(c: dict | None) -> str:
    return "" if c is None else f"{c['passed']}/{c['judged']}"


def fig3(d: dict, L: dict, led: Ledger):
    """Bodies × criteria, measured legs passed over judged; score and the leg the rank rests on."""
    led.fig = FIG3
    P, F = L["palette"], L["fig3"]
    crits = d["criteria"]
    lw_, cw, sw, rh = F["label_width"], F["cell_width"], F["score_width"], F["row_height"]
    n = len(d["rows"])
    width = 0.3 + lw_ + len(crits) * cw + sw + 0.3
    height = F["height_in"]
    # The canvas is as wide as the table, so a data unit is an inch and point-sized text keeps
    # its proportion to the cells.
    fig, ax = canvas([width, height], width, height, L)
    cmap = LinearSegmentedColormap.from_list("ratio", P["ratio_ramp"])

    ax.text(0.3, height - 0.2,
            "What the scan found: measured checks passed, by agency and criterion",
            fontsize=F["title_pt"], fontweight="bold", color=P["ink"], va="top")
    ty = height - 1.25
    x0 = 0.3 + lw_
    ax.text(0.35, ty + 0.1, "agency", fontsize=F["header_pt"], fontweight="bold",
            color=P["ink_secondary"], va="bottom")
    for j, c in enumerate(crits):
        nm = display(c["name"])
        nm = textwrap.fill(nm, F["header_wrap"], break_long_words=False)
        ax.text(x0 + j * cw + cw / 2, ty + 0.1, f"{c['code']}\n{nm}", fontsize=F["header_pt"] - 1,
                fontweight="bold", color=P["kept"] if c["kept"] else P["added"],
                ha="center", va="bottom", linespacing=1.05)
    xs = [x0 + len(crits) * cw + o for o in F["score_cols"]]
    for x, head in zip(xs, ("score", "rank", "rank if ONE check\nflipped: check → rank")):
        ax.text(x, ty + 0.1, head, fontsize=F["header_pt"] - 1, fontweight="bold",
                color=P["ink_secondary"], va="bottom", linespacing=1.05)
    # A criterion no body has a judged leg on is shaded and says so, rather than reading as
    # sixteen blank cells a reader may take for an omission.
    for j, c in enumerate(crits):
        if all(r["cells"][c["code"]] is None for r in d["rows"]):
            cx = x0 + j * cw
            ax.add_patch(Rectangle((cx + 0.04, ty - n * rh), cw - 0.08, n * rh,
                                   facecolor=P["neutral_fill"], edgecolor="none", zorder=0.5))
            ax.text(cx + cw / 2, ty - n * rh / 2, "no check judged on this criterion",
                    rotation=90, fontsize=F["header_pt"], color=P["ink_muted"],
                    ha="center", va="center", zorder=1)

    for i, r in enumerate(d["rows"]):
        y = ty - (i + 1) * rh
        if r["highlight"]:
            ax.add_patch(Rectangle((0.3, y), width - 0.6, rh, facecolor=P["highlight"],
                                   edgecolor=P["highlight_edge"], linewidth=1.6, zorder=0.7))
        else:
            ax.plot([0.3, width - 0.3], [y, y], color=P["rule_line"], lw=0.6, zorder=0)
        ax.text(0.35, y + rh / 2, r["body"], fontsize=F["label_pt"], fontweight="bold",
                color=P["ink"], va="center")
        ax.text(F["name_x"], y + rh / 2, textwrap.fill(r["name"], F["name_wrap"]),
                fontsize=F["name_pt"], color=P["ink_secondary"], va="center", linespacing=1.0)
        for j, c in enumerate(crits):
            cell = r["cells"][c["code"]]
            cx = x0 + j * cw
            if cell is None:
                continue
            ratio = cell["passed"] / cell["judged"]
            ax.add_patch(Rectangle((cx + 0.04, y + 0.04), cw - 0.08, rh - 0.08,
                                   facecolor=cmap(ratio), edgecolor="none"))
            ink = "white" if ratio > P["ratio_dark_text_above"] else P["ink"]
            src = f"{r['body']} criterion {c['code']}"
            ax.text(cx + cw / 2, y + rh / 2,
                    f"{led.n(cell['passed'], src + ' legs passed outright')}/"
                    f"{led.n(cell['judged'], src + ' legs judged')}",
                    fontsize=F["cell_pt"], color=ink, ha="center", va="center", fontweight="bold")
        if r["score"] is not None:
            parts = (led.n(r["score"], r["body"] + " hierarchical score (score.py)"),
                     f"{led.n(r['rank'], r['body'] + ' hierarchical rank')} of "
                     f"{led.n(r['of'], 'bodies ranked')}",
                     f"{r['leg']} → "
                     f"{led.n(r['rank_if_reversed'], r['body'] + ' rank if the leg is reversed (score.py concentration)')}")
            for x, t in zip(xs, parts):
                ax.text(x, y + rh / 2, t, fontsize=F["label_pt"], color=P["ink"], va="center")
        else:
            den, tot = r["denials"]
            ax.text(xs[0], y + rh / 2,
                    f"not ranked: {led.n(den, r['body'] + ' access-denial findings (claims.yaml table Q2)')} "
                    f"of {led.n(tot, r['body'] + ' findings (claims.yaml table Q2)')} findings were access denials",
                    fontsize=F["label_pt"], color=P["ink_secondary"], va="center")

    # Scale.
    yb = ty - (n + 1) * rh - 0.15
    ax.text(0.35, yb + 0.12, "share of judged checks passed:", fontsize=F["foot_pt"],
            color=P["ink_secondary"], va="center")
    steps = len(P["ratio_ramp"])
    for k in range(steps):
        ax.add_patch(Rectangle((2.9 + k * 0.42, yb), 0.4, 0.24,
                               facecolor=cmap(k / (steps - 1)), edgecolor="none"))
    ax.text(2.85, yb + 0.12, led.n(0, "scale: lowest share"), fontsize=F["foot_pt"],
            color=P["ink_secondary"], ha="right", va="center")
    ax.text(2.9 + steps * 0.42 + 0.05, yb + 0.12, f"{led.n(1, 'scale: highest share')}    "
            "blank: nothing judged", fontsize=F["foot_pt"], color=P["ink_secondary"], va="center")

    ax.text(0.35, yb - 0.3,
            "Equal weights; no weighting is asserted. Every rank rests on one check: flip that "
            "one check's result and the rank moves to the last column's number.",
            fontsize=F["foot_pt"] + 1, fontweight="bold", color=P["ink"], va="top")
    foot = (
        "A cell is the criterion's checks (measured legs) passed / judged for that agency; a leg "
        "passes when every judged row on it passes. Criteria C and E have no leg the scan judges.\n"
        f"Score: hierarchical mean, leg → indicator → construct → criterion → agency, on a "
        f"{led.n(0, 'score scale: lowest')} to {led.n(1, 'score scale: highest')} scale. Rows in roster order, not by rank. Cycle of record {d['cycle']}; the Census "
        "Bureau row is highlighted.")
    ax.text(0.35, yb - 0.62, foot, fontsize=F["foot_pt"], color=P["ink_secondary"], va="top",
            linespacing=1.4)
    return fig


# ------------------------------------------------------------------------------ outputs

CAPTIONS = {
    FIG1: ("USAFacts' criteria and the framework built on them",
           "{kept} of USAFacts' four criteria are kept and {added} added, {n_ind} indicators "
           "in all, of which {rule} have a current rule and {measured} are measured, "
           "{measured_cycle} of them on the cycle of record; {specified} are specified only.",
           ["CL-047", "CL-046", "CL-048", "CL-049", "CL-050"],
           "The measured count is the record's `counts.indicators_measured` (DD-055), the "
           "number the progress page and the brief print under the same name; measured on the "
           "cycle of record is the record's `measured_by.cycle` (DD-069). `scripts/score.py` "
           "calls what it scores \"indicators scored\", a different quantity."),
    FIG2: ("The system at a glance",
           "Documents become a framework of indicators, the indicators become rules, the rules "
           "scan {bodies} statistical agencies' public websites as a visitor with no login, and "
           "the {findings} findings become scores, ranked fixes and a graph people can question.",
           ["CL-044", "CL-046", "CL-048", "CL-034", "CL-051", "CL-050", "CL-082"],
           "The MCP box rests on no claim id; the evidence map has no claim about the interface."),
    FIG3: ("The pass/fail table",
           "Across the {ranked} ranked agencies most measured checks fail, criteria C and E "
           "have nothing the scan judges, and every rank rests on one leg under equal weights; "
           "{unranked} agencies are unranked because the scan's requests were refused.",
           ["CL-050", "CL-053", "CL-036", "CL-037", "CL-041", "CL-083"],
           "CL-083 is `unsupported`: no source calls equal weights defensible, so the footnote "
           "says no weighting is asserted and claims nothing stronger."),
}


def caption(name: str, d: dict) -> str:
    title, sent, ids, note = CAPTIONS[name]
    vals = {
        "kept": sum(c["kept"] for c in d["criteria"]),
        "added": sum(not c["kept"] for c in d["criteria"]),
        "n_ind": d["framework_indicators"], "rule": d["rule_indicators"],
        "measured": d["measured"], "measured_cycle": d["measured_cycle"],
        "specified": d["specified"], "bodies": d["bodies"], "findings": f"{d['findings']:,}", "ranked": d["ranked"],
        "unranked": d["bodies"] - d["ranked"],
    }
    missing = [i for i in ids if i not in d["claim_ids"]]
    if missing:
        raise SystemExit(f"FATAL: caption of {name} cites {missing}, not in "
                         f"{CLAIMS.relative_to(REPO)}")
    return (f"<!-- generated by {GENERATOR} ({TASK}). Do not edit: re-run the generator. -->\n"
            f"# {title}\n\n"
            f"**What this shows.** {sent.format(**vals)}\n\n"
            f"**Evidence-map claims.** {', '.join(f'`{i}`' for i in ids)} "
            f"(`docs/evidence/claims.yaml`).\n\n"
            f"**Note.** {note}\n\n"
            f"Cycle of record `{d['cycle']}`.\n")


def table_csv(d: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    codes = [c["code"] for c in d["criteria"]]
    w.writerow(["body", "name", *codes, "hierarchical_score", "rank", "of",
                "rank_rests_on_leg", "rank_if_leg_reversed", "access_denials", "findings"])
    for r in d["rows"]:
        den = r["denials"] or ("", "")
        w.writerow([r["body"], r["name"], *[cell_text(r["cells"][c]) for c in codes],
                    "" if r["score"] is None else format(r["score"], ".3f"),
                    r["rank"] or "", r["of"] or "", r["leg"] or "",
                    r["rank_if_reversed"] or "",
                    den[0] if r["score"] is None else "", den[1] if r["score"] is None else ""])
    return buf.getvalue()


def svg_bytes(fig, name: str) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="svg", metadata={"Date": None, "Title": name})
    return buf.getvalue()


def png_bytes(fig, L: dict) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=L["render"]["dpi"], metadata={"Software": None})
    return buf.getvalue()


def png_pixels(data: bytes):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"))


def render(d: dict | None = None) -> tuple:
    """`(files, figures)`: `{relative path: bytes}` for every output, and the live figures (the
    test reads their text elements)."""
    L = layout()
    setup(L)
    d = d or compute()
    led = Ledger()
    figs = {FIG1: fig1(d, L, led), FIG2: fig2(d, L, led), FIG3: fig3(d, L, led)}
    files = {}
    for name, fig in figs.items():
        files[f"{name}.svg"] = svg_bytes(fig, name)
        files[f"{name}.png"] = png_bytes(fig, L)
        files[f"{name}.caption.md"] = caption(name, d).encode("utf-8")
    files[f"{FIG3}.csv"] = table_csv(d).encode("utf-8")
    files["numbers.json"] = led.text().encode("utf-8")
    return files, figs, d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files, figs, _ = render()
    for f in figs.values():
        plt.close(f)
    if a.check:
        drift = []
        for name, data in files.items():
            p = OUT / name
            if not p.is_file():
                drift.append(f"{name}: missing")
            elif name.endswith(".png"):
                old, new = png_pixels(p.read_bytes()), png_pixels(data)
                if old.shape != new.shape or (old != new).any():
                    drift.append(f"{name}: pixels differ")
            elif p.read_bytes() != data:
                drift.append(f"{name}: bytes differ")
        if drift:
            print("DRIFT:\n  " + "\n  ".join(drift))
            return 1
        print(f"OK: {len(files)} files under docs/figures/ re-render identically")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (OUT / name).write_bytes(data)
    print(f"wrote {len(files)} files under docs/figures/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
