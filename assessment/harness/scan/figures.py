#!/usr/bin/env python3
"""One scan cycle as five figures. **Zero model spend. No network. No CDN.**

Task `cc_tasks/2026-09-07_eda_and_charts.md` §2. Every number printed here comes from the
Seldon Result registry by name or from `state/scan_matrix_2026-09-07.json`; the module carries
no constant of its own (layout lives in `figures.yaml`, and `tests/test_scan_figures.py`
extends the collectors' integer-literal lint to this file). Codes and names — not numbers —
come from the framework of record, because F3 lists indicator codes and no registered Result
holds a code.

**Every text node that contains a digit carries `data-src`**, naming where the digit came
from: `result:<name>` (one per numeral, in order), `matrix:<path>`, `axis`, or `label`. That
attribute is what makes §4's gate mechanical rather than hopeful — the test resolves each one
and fails with the numeral and the figure named. A figure that prints a number nobody can
trace is a chart with a footnote leading nowhere, which is the defect this task exists to fix:
the scan-run RESULT quoted fifteen Wilson intervals that existed nowhere in the registry.

**Prior art the encodings implement.**
- Cleveland & McGill (1984, *JASA* 79:531) and Cleveland (1985): position along a common
  scale beats length, so F1 is a dot-and-interval plot and not a bar chart. Bars would also
  assert a zero baseline as a claim, and eight legs sitting at 0/23 is the claim under
  caution.
- Bertin (1967/1983, *Semiology of Graphics*), the reorderable matrix — **not reordered**
  here: reordering rows by pass count is a ranking of agencies, which the operator forbade.
  Rows in roster order, columns grouped by criterion.
- Gigerenzer & Hoffrage (1995, *Psychol. Rev.* 102:684): a natural frequency beside every
  rate, never a bare percentage.
- Wilson (1927); Brown, Cai & DasGupta (2001); Newcombe (1998) for the intervals; Hanley &
  Lippman-Hand (1983) rule of three as the reader's check on a zero.
- Tufte (1983) small multiples for F4's three snapshots. Three points, and no trend line
  through them.

    /opt/anaconda3/bin/python3 assessment/harness/scan/figures.py [--dry-run]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import yaml

SCAN = Path(__file__).resolve().parent
REPO = SCAN.parents[2]
CONFIG = SCAN / "figures.yaml"
sys.path.insert(0, "/Users/brock/GitHub/seldon")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(SCAN.parent))

import cycle_results                                                   # noqa: E402
from scan import load_params                                           # noqa: E402

FIGURES = ("per_leg_pass_rate", "agencies_by_legs_matrix", "gap_map_by_criterion",
           "progress_over_snapshots", "cycle_over_cycle", "tier_c_reference_hosts")


def config(cycle: str | None = None) -> dict:
    """Layout from `figures.yaml`; WHICH CYCLE from `params.cycle.name`.

    Read at call time, never cached — the repo convention, so a test can point it at a tmp
    file. The cycle-dependent keys are derived rather than stored: `figures.yaml` used to
    carry `cycle`, `cycle_suffix`, `out_dir` and `matrix_json`, which made it a second
    definition of which cycle is being drawn, and a renderer that reads a stale one draws the
    previous cycle's numbers under this cycle's heading without erroring.
    """
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    cyc = cycle or load_params()["cycle"]["name"]
    suffix = cycle_results.cycle_suffix(cyc)
    cfg.update({"cycle": cyc, "cycle_suffix": suffix,
                "out_dir": f"assessment/harness/scan/figures/{cyc}",
                "matrix_json": f"state/scan_matrix_{suffix}.json"})
    # Which cycle F5 compares AGAINST is a fact about the cycle being drawn, not a global.
    # A re-judged cycle is drawn against the cycle it derives from — same evidence, old rules
    # against new — and the default `compare_to` DID silently draw one against cycle 1.
    #
    # `None` when the cycle has no entry, and `None` is the answer, not a missing one: the
    # default is gone (`figures.yaml`, and `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md`
    # decision 5). It is resolved to a refusal in `cycle_over_cycle` rather than here, because
    # five of the six figures need no predecessor and a cycle that legitimately has none — the
    # first one — must still be able to draw them.
    cfg["compare_to"] = (cfg.get("compare_to_by_cycle") or {}).get(cyc)
    return cfg


def rname(base: str, cfg: dict) -> str:
    """The Result name this cycle registered `base` under. One resolver, shared with the
    registrars (`scripts/cycle_results.name_for`), so a figure can never look up a name no
    registrar ever bound — which is what the first cycle's bare names would do here."""
    return cycle_results.name_for(base, cfg["cycle"])


def slug(leg: str) -> str:
    """`A11-declared` -> `a11_declared`; the convention the per-leg Result names use."""
    return leg.replace("-", "_").lower()


def load_results(prefixes=("scan_", "framework_")) -> dict:
    """`{name: value}` for every Result whose name starts with one of `prefixes`.

    Labelled Cypher, read-only. The registry is the source; this module never computes a
    statistic — `scan/stats.py` did that once, and its output was registered before any figure
    was drawn (task §1, and the SEQUENCING line is why).
    """
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            rows = s.run("MATCH (r:Result) WHERE any(p IN $pfx WHERE r.name STARTS WITH p) "
                         "RETURN r.name AS name, r.value AS value", pfx=list(prefixes))
            return {r["name"]: r["value"] for r in rows}
    finally:
        driver.close()


def matrix(cfg: dict | None = None) -> dict:
    return json.loads((REPO / (cfg or config())["matrix_json"]).read_text(encoding="utf-8"))


def tier_c_matrix(cfg: dict | None = None) -> dict:
    """The Tier C matrix, written beside the Tier A one by `scripts/scan_report.py`. Separate
    files because they are separate populations and must never share a denominator."""
    cfg = cfg or config()
    p = REPO / "state" / f"scan_matrix_tierc_{cfg['cycle_suffix']}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"rows": [], "legs": []}


def framework() -> dict:
    return json.loads((REPO / config()["framework_json"]).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- SVG primitives

def fmt(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}"


def as_count(value) -> str:
    """A registered Result value is a float; a count is written as one."""
    return str(int(round(value)))


def text(x, y, body: str, cls: str, src: str, anchor: str = "start", extra: str = "") -> str:
    return (f'<text class="{cls}" x="{x:g}" y="{y:g}" text-anchor="{anchor}" '
            f'data-src="{html.escape(src)}"{extra}>{html.escape(body)}</text>')


#: DataFile artifact names, by the config key that points at the file. The figure records
#: which of them it read, so provenance covers the figures that print no registered number at
#: all — F2's data is entirely in the matrix, and it would otherwise have no edge to anything.
DATA_NAMES = {"framework_json": "ai_readiness_framework"}


def data_name(key: str, cfg: dict) -> str:
    """The DataFile artifact name behind a config key. `matrix_json` is per cycle, so it is
    derived from the cycle rather than listed — the figure and the registrar must name the
    same artifact, and a hand-kept second copy of that name is how they stop doing so."""
    if key == "matrix_json":
        return f"scan_matrix_{cfg['cycle_suffix']}"
    return DATA_NAMES[key]


def svg(width, height, label: str, body: list, reads=(), files=(), cfg=None) -> str:
    """`data-reads` names every Result the figure LOOKED UP, printed or not. F1's control
    marks are the case that matters: their fill is decided by
    `scan_<leg>_control_fired_2026-09-07`, which never appears as a numeral, so a provenance
    list built from the printed numbers alone would miss fifteen Results the figure depends
    on. `scripts/register_scan_figures.py` reads this attribute back to build the edges, so
    the dependency list cannot go stale — it is derived from the run that drew the figure."""
    attr = f' data-reads="{html.escape(" ".join(sorted(reads)))}"' if reads else ""
    attr += (f' data-files="{html.escape(" ".join(data_name(k, cfg) for k in files))}"'
             if files else "")
    # `xmlns` makes each figure a STANDALONE SVG document and not only an inline fragment
    # (`cc_tasks/2026-09-10_harness_small.md` decision 3). Without it typst refused every one
    # with "missing root node", and the PDF build carried a step that namespaced a copy —
    # every consumer outside the HTML page had to repair the file before reading it. The
    # attribute is valid on inline SVG too, so the graph page is unaffected.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width:g} {height:g}" width="100%" role="img" '
            f'aria-label="{html.escape(label)}"{attr}>{"".join(body)}</svg>')


#: The comparison records a re-judgement leaves behind: for each `_rj` cycle, which Result names
#: were compared against the original and found UNCHANGED. `cc_tasks/2026-09-10_rejudge_2_3_4.md`
#: decision 2 forbids re-registering those, so they exist only under the source cycle's name —
#: and a figure of the re-judged cycle still has to draw them.
UNCHANGED_RECORDS = ("state/rejudgement_registration_2026-09-10.json",
                     "state/l0_rejudged_registration_2026-09-10.json",
                     "state/figure_inputs_registration_2026-09-10.json",
                     # Generation 9 (`cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md` decision 3),
                     # one record per family for the same reason the harness-v5 pass wrote three:
                     # a family nobody compared has no evidence, and no evidence is no fallback.
                     "state/rejudgement_registration_2026-09-11.json",
                     "state/l0_rejudged_registration_2026-09-11.json",
                     "state/figure_inputs_registration_2026-09-11.json")


def unchanged_names() -> set:
    """Every `_rj` Result name a comparison record lists as compared-and-unchanged.

    Read from the records, never inferred from the naming convention. That is the whole point of
    `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 1: a fallback licensed by a
    pattern would resolve ANY missing name to the previous cycle, which is how a figure comes to
    draw one cycle's number under another cycle's label. A fallback licensed by evidence
    resolves only what something checked and recorded as equal.
    """
    out: set = set()
    for rel in UNCHANGED_RECORDS:
        p = REPO / rel
        if not p.is_file():
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        if "unchanged" in doc and isinstance(doc["unchanged"], list):
            out |= set(doc["unchanged"])
        for v in doc.values():
            if isinstance(v, dict) and isinstance(v.get("unchanged_names"), list):
                out |= set(v["unchanged_names"])
    return out


class UnlicensedFallback(KeyError):
    """A figure asked for a name that is neither registered nor recorded as unchanged."""


class UnconfiguredComparison(KeyError):
    """F5 was asked to draw a cycle whose predecessor nobody declared.

    Raised rather than defaulted. Which cycle a comparison is AGAINST is a claim about the past —
    same frame or not, same rules or not — and `figures.yaml` is where a person makes it. The
    global default that used to answer here drew `scan_2026-09-09_rj1` against cycle 1, a figure
    with 22 rows reading "not measured in this cycle" and a heading that said otherwise
    (`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names_RESULT.md` §4).
    """


class Reads(dict):
    """A `{name: value}` view that remembers which names were asked for. The alternative is a
    hand-kept list of each figure's inputs, which is a list that goes stale silently.

    **Evidence-bound fallback** (decision 1). Drawing a re-judged cycle, a name registered only
    under the source cycle resolves there — but only when a comparison record lists it as
    compared-and-unchanged. Anything else is `UnlicensedFallback`, raised rather than guessed,
    and every fallback taken is recorded in `fell_back` so the RESULT can name each one and the
    line that licensed it.
    """

    def __init__(self, source: dict, cycle: str | None = None):
        super().__init__(source)
        self.seen = set()
        self.cycle = cycle
        self.fell_back: dict = {}
        # Loaded whatever cycle is drawn: the comparison cycle may be a
        # re-judgement even when the drawn one is not.
        self._licensed = unchanged_names()

    def __getitem__(self, key):
        self.seen.add(key)
        if key in self:
            return super().__getitem__(key)
        # Keyed on the NAME, not on the cycle being drawn. `cycle_over_cycle` reads the
        # COMPARISON cycle's names too, and cycle 4's comparison is cycle 3 re-judged — so a
        # fallback scoped to the drawn cycle answers for half the figure and raises on the
        # other half. The licence is unchanged and is still the comparison record: a name that
        # nothing recorded as compared-and-unchanged is a hard error whatever cycle asked for it.
        older = _source_name(key)
        if older is not None:
            if key in self._licensed and older in self:
                self.fell_back[key] = older
                return super().__getitem__(older)
            raise UnlicensedFallback(
                f"{key!r} is not registered, and "
                + (f"{older!r} exists but no comparison record lists {key!r} as "
                   f"compared-and-unchanged"
                   if older in self else f"{older!r} does not exist either")
                + ". A figure may not resolve a missing name by convention; see "
                  "`cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 1.")
        return super().__getitem__(key)


def _source_name(name: str) -> str | None:
    """`scan_a3_pass_2026-09-09_rj1` -> `scan_a3_pass_2026-09-09`, or `None` when the name does
    not carry a re-judgement suffix at all."""
    m = re.match(r"^(.*)_rj\d+$", name or "")
    return m.group(1) if m else None


def _suffix(cycle: str) -> str:
    return cycle.removeprefix("scan_") if cycle else ""


def _rj_source(cycle: str) -> str | None:
    """`scan_2026-09-09_rj1` -> `scan_2026-09-09`. `None` for a cycle that is not a
    re-judgement, which is every cycle that measured something."""
    m = re.match(r"^(.*)_rj\d+$", cycle or "")
    return m.group(1) if m else None


def criterion_of(leg: str) -> str:
    """`A11-declared` -> `A`. The framework's own code shape: a criterion letter then digits."""
    return leg[:1]


# ---------------------------------------------------------------- F1

def per_leg_pass_rate(mx: dict, R: dict, cfg: dict) -> str:
    """Dot at the pass rate, Wilson 95 % interval through it, `k/n` and the bounds printed,
    legs grouped by criterion and sorted by rate WITHIN a criterion only.

    Sorting inside a criterion is a reading aid; sorting across criteria would invite the
    cross-leg comparison the caption forbids. The control mark is the point of the figure as
    much as the dots: eight legs sit at zero, and a zero has two readings — the products do
    not have the property, or the rule cannot say `pass` at all. A filled mark says the rule
    returned `pass` on the passing fixture and `fail` on the failing one in this same cycle.
    """
    f = cfg["f1"]
    ax = cfg["rate_axis"]
    col = cfg["colours"]
    dec = ax["tick_decimals"]
    legs = mx["legs"]
    groups = []
    for crit in cfg["criteria"]:
        members = [l for l in legs if criterion_of(l) == crit]
        if not members:
            continue
        members.sort(key=lambda l: -R[rname(f"scan_{slug(l)}_pass_rate", cfg)])
        groups.append((crit, members))

    left, plot = f["label_w"], f["plot_w"]
    height = (f["top"] + f["bottom"] + len(legs) * f["row_h"]
              + len(groups) * f["group_gap"])
    body = [f'<rect x="0" y="0" width="{cfg["canvas"]["width"]:g}" height="{height:g}" '
            f'fill="none"/>']
    y = f["top"]
    for crit, members in groups:
        body.append(text(0, y - f["group_label_dy"], f"criterion {crit}", "grp", "label"))
        for leg in members:
            n = f"scan_{slug(leg)}"
            rate = R[rname(f"{n}_pass_rate", cfg)]
            lo = R[f"{n}_wilson_lo_{cfg['cycle_suffix']}"]
            hi = R[f"{n}_wilson_hi_{cfg['cycle_suffix']}"]
            cy = y + f["row_h"] / 2
            body.append(text(0, cy + f["text_dy"], leg, "lbl", "label"))
            fired = R[f"{n}_control_fired_{cfg['cycle_suffix']}"]
            side = f["control_size"]
            body.append(
                f'<rect x="{left - side - f["control_gap"]:g}" y="{cy - side / 2:g}" '
                f'width="{side:g}" height="{side:g}" rx="1" '
                f'fill="{col["control"] if fired else col["empty"]}">'
                f'<title>{html.escape(leg)}: control fixtures '
                f'{"fired" if fired else "DID NOT FIRE"} in this cycle</title></rect>')
            body.append(f'<line x1="{left:g}" x2="{left + plot:g}" y1="{cy:g}" y2="{cy:g}" '
                        f'stroke="{col["axis"]}" stroke-width="{cfg["canvas"]["stroke"]:g}"/>')
            body.append(
                f'<line x1="{left + plot * lo:g}" x2="{left + plot * hi:g}" y1="{cy:g}" '
                f'y2="{cy:g}" stroke="{col["interval"]}" '
                f'stroke-width="{f["interval_w"]:g}" stroke-linecap="round"/>')
            body.append(
                f'<circle cx="{left + plot * rate:g}" cy="{cy:g}" r="{f["dot_r"]:g}" '
                f'fill="{col["pass"]}"/>')
            npass, napp = rname(f"{n}_pass", cfg), rname(f"{n}_applicable_n", cfg)
            body.append(text(left + plot + f["frac_dx"], cy + f["text_dy"],
                             f'{as_count(R[npass])}/{as_count(R[napp])}',
                             "num", f"result:{npass} result:{napp}"))
            body.append(text(
                left + plot + f["ci_dx"], cy + f["text_dy"],
                f'[{fmt(lo, dec)}, {fmt(hi, dec)}]', "num",
                f'result:{n}_wilson_lo_{cfg["cycle_suffix"]} '
                f'result:{n}_wilson_hi_{cfg["cycle_suffix"]}'))
            y += f["row_h"]
        y += f["group_gap"]
    base = y - f["group_gap"]
    body.append(f'<line x1="{left:g}" x2="{left + plot:g}" y1="{base:g}" y2="{base:g}" '
                f'stroke="{col["axis"]}" stroke-width="{cfg["canvas"]["stroke"]:g}"/>')
    for t in ax["ticks"]:
        x = left + plot * t
        body.append(f'<line x1="{x:g}" x2="{x:g}" y1="{base:g}" '
                    f'y2="{base + f["tick_len"]:g}" stroke="{col["axis"]}" '
                    f'stroke-width="{cfg["canvas"]["stroke"]:g}"/>')
        body.append(text(x, base + f["tick_label_dy"], fmt(t, dec), "num", "axis", "middle"))
    return svg(cfg["canvas"]["width"], height,
               "Pass rate per leg with its Wilson 95 percent interval and denominator", body,
               getattr(R, "seen", ()), ("matrix_json",), cfg)


# ---------------------------------------------------------------- F2

def agencies_by_legs_matrix(mx: dict, R: dict, cfg: dict) -> str:
    """Every agency on the roster, including the four that contributed no surface and the one
    that refused every probe. Bertin's matrix, deliberately not reordered.

    The two control rows sit at the top because they are the instrument's ceiling and floor:
    without them a column of `fail` is ambiguous between a finding and a broken rule.
    """
    f = cfg["f2"]
    col = cfg["colours"]
    legs = mx["legs"]
    cell, gap = f["cell"], f["gap"]
    by_agency = {}
    for r in mx["rows"]:
        if r["surface_kind"] == "well_known":
            continue
        by_agency.setdefault(r["agency"], []).append(r)
    no_surface = set(mx["agencies_without_surfaces"])
    unobservable = set(mx["agencies_wholly_unobservable"])

    rows = [("control", "control · passes_all", {l: "pass" for l in legs}),
            ("control", "control · fails_all", {l: "fail" for l in legs})]
    for agency in mx["agencies"]:
        if agency in no_surface:
            rows.append(("no_surface", f"{agency} · no admitted surface", {}))
            continue
        for r in by_agency.get(agency, []):
            mark = " ✕" if agency in unobservable else ""
            rows.append(("surface", f"{agency} · {r['surface_kind']}{mark}", r["verdicts"]))

    width = cfg["canvas"]["width"]
    height = f["head_h"] + len(rows) * (cell + gap) + f["bottom"]
    body = []
    for i, leg in enumerate(legs):
        x = f["label_w"] + i * (cell + gap) + cell / 2
        y = f["head_h"] - f["header_dy"]
        body.append(f'<text class="lbl" x="{x:g}" y="{y:g}" text-anchor="start" '
                    f'data-src="label" transform="rotate({f["label_rotate"]:g} {x:g} {y:g})">'
                    f'{html.escape(leg)}</text>')
    for j, (kind, label, verdicts) in enumerate(rows):
        y = f["head_h"] + j * (cell + gap)
        body.append(text(0, y + cell - f["text_dy"], label,
                         "lbl unob" if "✕" in label else "lbl", "label"))
        for i, leg in enumerate(legs):
            x = f["label_w"] + i * (cell + gap)
            if kind == "no_surface":
                fill, title = col["no_surface"], "no admitted surface for this agency"
            else:
                v = verdicts.get(leg, "")
                fill = col.get(v, col["empty"])
                title = v or "no finding"
            body.append(f'<rect x="{x:g}" y="{y:g}" width="{cell:g}" height="{cell:g}" '
                        f'rx="{f["cell_radius"]:g}" fill="{fill}">'
                        f'<title>{html.escape(label)} · {html.escape(leg)} · '
                        f'{html.escape(title)}</title></rect>')
    return svg(width, height, "Agencies by legs, one cell per finding", body,
               getattr(R, "seen", ()), ("matrix_json",), cfg)


# ---------------------------------------------------------------- F3

def gap_map_by_criterion(fw: dict, R: dict, cfg: dict) -> str:
    """Where the instrument is, per criterion: specified / harness_built / measured, with the
    count in each segment and the indicator codes beside the bar. It says nothing about pass
    rates — a measured indicator can be measured and failing."""
    f = cfg["f3"]
    col = cfg["colours"]
    suffix = cfg["cycle_suffix"]
    inds = [n["properties"] for n in fw["nodes"]
            if "AssessmentIndicator" in n["labels"]]
    adopted = [p for p in inds if p.get("status") != "candidate"]
    cands = [p for p in inds if p.get("status") == "candidate"]

    rows = []
    for crit in cfg["criteria"]:
        counts = {st: R[f"framework_{crit}_{st}_{suffix}"] for st in cfg["statuses"]}
        codes = sorted(p["code"] for p in adopted if p["criterion_code"] == crit)
        rows.append((crit, counts, codes))
    total = max(sum(c.values()) for _, c, _ in rows)

    height = f["top"] + len(rows) * f["row_h"] + f["bottom"] + f["row_h"]
    body = []
    y = f["top"]
    for crit, counts, codes in rows:
        body.append(text(0, y + f["label_dy"], f"criterion {crit}", "lbl", "label"))
        x = f["label_w"]
        for st in cfg["statuses"]:
            n = counts[st]
            w = f["bar_w"] * n / total
            if n:
                body.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" '
                            f'height="{f["bar_h"]:g}" fill="{col[st]}">'
                            f'<title>{html.escape(crit)} · {html.escape(st)}</title></rect>')
                body.append(text(x + w / 2, y + f["seg_text_dy"], as_count(n), "inbar",
                                 f"result:framework_{crit}_{st}_{suffix}", "middle"))
            x += w
        body.append(text(f["label_w"] + f["bar_w"] + f["code_gap"], y + f["label_dy"],
                         " ".join(codes), "codes", "label"))
        y += f["row_h"]
    body.append(text(0, y + f["label_dy"], "candidate (not counted)", "lbl", "label"))
    body.append(f'<rect x="{f["label_w"]:g}" y="{y:g}" '
                f'width="{f["bar_w"] / total:g}" height="{f["bar_h"]:g}" '
                f'fill="{col["candidate"]}"><title>candidate, DD-054</title></rect>')
    body.append(text(f["label_w"] + f["bar_w"] + f["code_gap"], y + f["label_dy"],
                     " ".join(sorted(p["code"] for p in cands)), "codes", "label"))
    return svg(cfg["canvas"]["width"], height,
               "Indicators by criterion and measurement status", body,
               getattr(R, "seen", ()), ("framework_json",), cfg)


# ---------------------------------------------------------------- F4

def progress_over_snapshots(R: dict, cfg: dict) -> str:
    """Three snapshots of the same 48 indicators, each read from a commit. Three points is
    what exists; there is no line through them, because two intervals of a few hours are not
    a rate of progress and drawing them as one would say they were."""
    f = cfg["f4"]
    col = cfg["colours"]
    snaps = cfg["snapshots"]
    totals = []
    for sn in snaps:
        totals.append(sum(R[f"framework_indicators_{st}_{sn['suffix']}"]
                          for st in cfg["statuses"]))
    total = max(totals)
    height = f["top"] + len(snaps) * f["row_h"] + f["bottom"]
    body = []
    y = f["top"]
    for sn in snaps:
        body.append(text(0, y + f["label_dy"], sn["label"], "lbl", "label"))
        body.append(text(0, y + f["sub_dy"], f'{sn["commit"]} · {sn["note"]}', "sub", "label"))
        x = f["label_w"]
        for st in cfg["statuses"]:
            n = R[f"framework_indicators_{st}_{sn['suffix']}"]
            w = f["bar_w"] * n / total
            if n:
                body.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" '
                            f'height="{f["bar_h"]:g}" fill="{col[st]}">'
                            f'<title>{html.escape(sn["label"])} · {html.escape(st)}</title>'
                            f'</rect>')
                body.append(text(x + w / 2, y + f["seg_text_dy"], as_count(n), "inbar",
                                 f"result:framework_indicators_{st}_{sn['suffix']}", "middle"))
            x += w
        y += f["row_h"]
    return svg(cfg["canvas"]["width"], height,
               "Indicator measurement status at the framework snapshots", body,
               getattr(R, "seen", ()), (), cfg)


# ---------------------------------------------------------------- F5

def cycle_over_cycle(mx: dict, R: dict, cfg: dict) -> str:
    """Both cycles' pass rates per leg, side by side, with `k/n` and the interval on each —
    and A1 and A3 marked **rule changed, not comparable**.

    The mark is the point of the figure. Two dots at different heights invite exactly one
    reading, "the host changed", and for A1 and A3 that reading is wrong: `RULE-A1-v2` became
    `RULE-A1-v3` and `RULE-A3-v3` became `RULE-A3-v4` between the cycles, so a difference
    there is the instrument moving under a fixed subject. Drawing the pair and leaving the
    reader to remember which rules moved is the failure mode; the legs that moved are read
    from `figures.yaml` and printed on the row.

    No line, no delta number, no arrow. A difference between two points is not a trend, and
    two cycles hours apart on federal publication schedules is not a rate of change. Where a
    leg has no interval in one cycle — no applicable denominator — that cycle's row is left
    blank rather than plotted at zero: DD-055 again, not measured is not a zero.

    Prior art, as F1: Cleveland & McGill (1984) position on a common scale; Gigerenzer &
    Hoffrage (1995) natural frequency beside every rate; Wilson (1927) for the intervals.
    """
    f, ax, col = cfg["f5"], cfg["rate_axis"], cfg["colours"]
    cmp_ = cfg["compare_to"]
    if not cmp_:
        raise UnconfiguredComparison(
            f"no predecessor is declared for cycle {cfg['cycle']!r}, so F5 cannot be drawn. Add "
            f"a `compare_to_by_cycle` entry to figures.yaml naming the cycle this one is "
            f"compared against, its suffix, its label and the legs whose rule moved between "
            f"them — or, if it genuinely has no predecessor, draw the other figures with "
            f"`--only` and leave this one out. There is no default: a default predecessor is an "
            f"assertion about the past that nobody made.")
    dec = ax["tick_decimals"]
    legs = mx["legs"]
    left, plot = f["label_w"], f["plot_w"]
    height = f["top"] + f["bottom"] + len(legs) * f["row_h"]
    body = [f'<rect x="0" y="0" width="{cfg["canvas"]["width"]:g}" height="{height:g}" '
            f'fill="none"/>']
    #: (suffix, colours, label). The PRIOR cycle first so the current one draws on top.
    series = [(cmp_["suffix"], col["prior"], col["prior_interval"], cmp_["label"]),
              (cfg["cycle_suffix"], col["pass"], col["interval"],
               f"cycle 2 · {cfg['cycle_suffix']}")]
    y = f["top"]
    # The one sentence a reader of a re-judged pair cannot do without: the second point is the
    # SAME evidence under a different rule. Without it the figure reads as two measurements.
    if cmp_.get("note"):
        body.append(text(0, f["group_label_dy"], cmp_["note"], "sub", "label"))
    for leg in legs:
        n = f"scan_{slug(leg)}"
        changed = cmp_["rule_changed"].get(leg)
        body.append(text(0, y + f["text_dy"] + f["cycle_dy"], leg,
                         "lbl warn" if changed else "lbl", "label"))
        if changed:
            body.append(text(0, y + f["text_dy"] + 2 * f["cycle_dy"],
                             f"rule changed ({changed}): not comparable", "sub", "label"))
        for i, (suffix, dot, bar, label) in enumerate(series):
            cy = y + f["cycle_dy"] * (i + 1)
            body.append(f'<line x1="{left:g}" x2="{left + plot:g}" y1="{cy:g}" y2="{cy:g}" '
                        f'stroke="{col["axis"]}" '
                        f'stroke-width="{cfg["canvas"]["stroke"]:g}"/>')
            rate_key = cycle_results.name_for(f"{n}_pass_rate",
                                              f"scan_{suffix}")
            if rate_key not in R:
                # A leg with no registered rate in that cycle: it had no applicable
                # denominator, or the cycle did not judge it. Left blank on purpose.
                body.append(text(left, cy + f["text_dy"], "not measured in this cycle",
                                 "sub", "label"))
                continue
            rate = R[rate_key]
            lo, hi = R[f"{n}_wilson_lo_{suffix}"], R[f"{n}_wilson_hi_{suffix}"]
            body.append(
                f'<line x1="{left + plot * lo:g}" x2="{left + plot * hi:g}" y1="{cy:g}" '
                f'y2="{cy:g}" stroke="{bar}" stroke-width="{f["interval_w"]:g}" '
                f'stroke-linecap="round"/>')
            body.append(f'<circle cx="{left + plot * rate:g}" cy="{cy:g}" '
                        f'r="{f["dot_r"]:g}" fill="{dot}">'
                        f'<title>{html.escape(label)} · {html.escape(leg)}</title></circle>')
            kp = cycle_results.name_for(f"{n}_pass", f"scan_{suffix}")
            kn = cycle_results.name_for(f"{n}_applicable_n", f"scan_{suffix}")
            body.append(text(left + plot + f["frac_dx"], cy + f["text_dy"],
                             f'{as_count(R[kp])}/{as_count(R[kn])}', "num",
                             f"result:{kp} result:{kn}"))
            body.append(text(left + plot + f["note_dx"], cy + f["text_dy"],
                             f'[{fmt(lo, dec)}, {fmt(hi, dec)}]', "num",
                             f"result:{n}_wilson_lo_{suffix} "
                             f"result:{n}_wilson_hi_{suffix}"))
        y += f["row_h"]
    base = y
    body.append(f'<line x1="{left:g}" x2="{left + plot:g}" y1="{base:g}" y2="{base:g}" '
                f'stroke="{col["axis"]}" stroke-width="{cfg["canvas"]["stroke"]:g}"/>')
    for t in ax["ticks"]:
        x = left + plot * t
        body.append(f'<line x1="{x:g}" x2="{x:g}" y1="{base:g}" '
                    f'y2="{base + f["tick_len"]:g}" stroke="{col["axis"]}" '
                    f'stroke-width="{cfg["canvas"]["stroke"]:g}"/>')
        body.append(text(x, base + f["tick_label_dy"], fmt(t, dec), "num", "axis", "middle"))
    return svg(cfg["canvas"]["width"], height,
               "Pass rate per leg in both cycles, with the legs whose rule changed marked",
               body, getattr(R, "seen", ()), ("matrix_json",), cfg)


# ---------------------------------------------------------------- F6

def tier_c_reference_hosts(mx: dict, R: dict, cfg: dict) -> str:
    """Tier C: reference hosts by tier-0 leg, verdict cells, **no rate and no interval**.

    A reference host is not a statistical agency. It is judged on `params.tier0.legs` only —
    properties of a host that publishes data — and it enters no Tier A denominator, so there is
    no `k/n` to print and nothing to draw an interval through (DD-059, ADDENDUM-01). Drawing a
    rate here would invite exactly the cross-tier comparison the frame decision forbids.

    Cells, not dots, for the same reason F2 uses cells: six surfaces by six legs is a matrix of
    judgements, not a distribution.
    """
    f, col = cfg["f6"], cfg["colours"]
    rows = sorted(mx["rows"], key=lambda r: (r["agency"], r["surface_kind"]))
    legs = mx["legs"]
    cell, gap = f["cell"], f["gap"]
    height = f["head_h"] + len(rows) * (cell + gap) + f["bottom"]
    body = []
    for i, leg in enumerate(legs):
        x = f["label_w"] + i * (cell + gap) + cell / 2
        y = f["head_h"] - f["header_dy"]
        body.append(f'<text class="lbl" x="{x:g}" y="{y:g}" text-anchor="start" '
                    f'data-src="label" transform="rotate({f["label_rotate"]:g} {x:g} {y:g})">'
                    f'{html.escape(leg)}</text>')
    for j, r in enumerate(rows):
        y = f["head_h"] + j * (cell + gap)
        body.append(text(0, y + cell - f["text_dy"],
                         f'{r["agency"]} · {r["surface_kind"]}', "lbl", "label"))
        for i, leg in enumerate(legs):
            x = f["label_w"] + i * (cell + gap)
            v = r["verdicts"].get(leg, "")
            body.append(f'<rect x="{x:g}" y="{y:g}" width="{cell:g}" height="{cell:g}" '
                        f'rx="{f["cell_radius"]:g}" fill="{col.get(v, col["empty"])}">'
                        f'<title>{html.escape(r["agency"])} · {html.escape(r["surface_kind"])}'
                        f' · {html.escape(leg)} · {html.escape(v or "not asked")}</title>'
                        f'</rect>')
    return svg(cfg["canvas"]["width"], height,
               "Tier C reference hosts by tier-0 leg, verdict cells, no rate", body,
               getattr(R, "seen", ()), (), cfg)


# ---------------------------------------------------------------- build

def build(cfg: dict | None = None, R: dict | None = None, only: tuple | None = None) -> dict:
    """Every figure, or the named subset. `only` is a filter on WHICH are drawn and never on
    how one is drawn: a figure in the subset is byte-identical to the same figure in the whole
    set, so a partial build can never produce a different chart from a full one."""
    cfg = cfg or config()
    R = R if R is not None else load_results()
    mx, fw = matrix(cfg), framework()
    # One recorder per figure, so `data-reads` names that figure's inputs and not the union.
    draw = {"per_leg_pass_rate": lambda: per_leg_pass_rate(mx, Reads(R, cfg['cycle']), cfg),
            "agencies_by_legs_matrix": lambda: agencies_by_legs_matrix(mx, Reads(R, cfg['cycle']), cfg),
            "gap_map_by_criterion": lambda: gap_map_by_criterion(fw, Reads(R, cfg['cycle']), cfg),
            "progress_over_snapshots": lambda: progress_over_snapshots(Reads(R, cfg['cycle']), cfg),
            "cycle_over_cycle": lambda: cycle_over_cycle(mx, Reads(R, cfg['cycle']), cfg),
            "tier_c_reference_hosts": lambda: tier_c_reference_hosts(
                tier_c_matrix(cfg), Reads(R, cfg['cycle']), cfg)}
    assert tuple(draw) == FIGURES

    # **`data-src` names the Result the number CAME FROM.** Where a recorder resolved a name
    # through the evidence-bound fallback, the attribute is rewritten to the name it actually
    # read. Leaving the asked-for name there would make the figure cite a Result nobody
    # registered — which is what the figure gate reports, correctly, and which would make the
    # provenance attribute a statement about the lookup rather than about the evidence.
    # `cc_tasks/2026-09-10_l0_figures_and_leg_rate_names.md` decision 1.
    out = {}
    for name, fn in draw.items():
        if only is not None and name not in only:
            continue
        rec = Reads(R, cfg["cycle"])
        _recorders[name] = rec
        svg = _draw_with(draw, name, mx, fw, cfg, rec)
        for asked, read in rec.fell_back.items():
            svg = svg.replace(f"result:{asked}", f"result:{read}")
        out[name] = svg
    return out


#: The recorder each figure used on the last `build`, so a caller can ask which names fell back
#: and to what. Read by the RESULT's accounting and by `register_scan_figures.py`.
_recorders: dict = {}


def _draw_with(draw: dict, name: str, mx: dict, fw: dict, cfg: dict, rec) -> str:
    """One figure, drawn through a recorder the caller keeps. The `draw` table builds its own
    recorder per lambda, which is right for the general case and useless when the caller needs
    the fallback record — so the five call shapes are named once here rather than the table
    being rewritten into something that returns two things."""
    if name == "per_leg_pass_rate":
        return per_leg_pass_rate(mx, rec, cfg)
    if name == "agencies_by_legs_matrix":
        return agencies_by_legs_matrix(mx, rec, cfg)
    if name == "gap_map_by_criterion":
        return gap_map_by_criterion(fw, rec, cfg)
    if name == "progress_over_snapshots":
        return progress_over_snapshots(rec, cfg)
    if name == "cycle_over_cycle":
        return cycle_over_cycle(mx, rec, cfg)
    if name == "tier_c_reference_hosts":
        return tier_c_reference_hosts(tier_c_matrix(cfg), rec, cfg)
    raise KeyError(name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="render, do not write")
    ap.add_argument("--cycle", default=None, help="draw a cycle other than params.cycle.name")
    ap.add_argument("--only", action="append", default=None, metavar="FIGURE",
                    help="draw only these figures (repeatable). Used for a RE-JUDGED cycle, "
                         "which has per-leg rates and a cycle-over-cycle comparison and no "
                         "measurement of its own to draw the rest from.")
    a = ap.parse_args(argv)
    cfg = config(a.cycle)
    if a.only:
        unknown = [n for n in a.only if n not in FIGURES]
        if unknown:
            raise SystemExit(f"REFUSING: no figure named {unknown}; known: {list(FIGURES)}")
    figs = build(cfg, only=tuple(a.only) if a.only else None)
    dest = REPO / cfg["out_dir"]
    written = {}
    if not a.dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    for name, body in figs.items():
        path = dest / f"{name}.svg"
        if not a.dry_run:
            path.write_text(body + "\n", encoding="utf-8")
        written[name] = {"path": str(path.relative_to(REPO)), "bytes": len(body)}
    print(json.dumps(written, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
