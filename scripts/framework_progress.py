#!/usr/bin/env python3
"""The framework's coverage model and its static progress page. **Zero model spend.**

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §4. **A coverage model, not a
maturity ladder** (DD-050): per-level completion is evidenced-and-measured indicators over
indicators in scope, **reported as fractions with counts and never as a single composite.**
That is protocol §3's no-composite rule and DD-036's two-leg rule carried up from the
indicator to the framework — a composite embeds a weighting only a stated purpose can justify,
and no purpose has been stated.

Renders inline SVG, not matplotlib PNGs: the page is then one self-contained file with no
build artifact, no server and no JS.

    /opt/anaconda3/bin/python3 scripts/framework_progress.py
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
JSON_PATH = REPO / "framework" / "ai_readiness_framework.json"
OUT_JSON = REPO / "docs" / "progress" / "framework_progress_2026-09-06.json"
OUT_HTML = REPO / "docs" / "progress" / "index.html"

STATUSES = ("specified", "harness_built", "measured")
#: Colour-blind-safe, and each hue used once so the legend is the only thing to read.
COLOURS = {"specified": "#94a3b8", "harness_built": "#3b82f6", "measured": "#059669",
           "evidenced": "#059669", "gap": "#d97706",
           "collector": "#3b82f6", "none_known": "#d97706"}


def indicators(g: dict) -> list:
    return [n["properties"] for n in g["nodes"] if "AssessmentIndicator" in n["labels"]]


def specs(g: dict) -> dict:
    return {n["properties"]["leg"]: n["properties"] for n in g["nodes"]
            if "MeasurementSpec" in n["labels"]}


def frac(num: int, den: int) -> dict:
    """Every fraction carries its counts. A bare ratio is how a coverage model turns into a
    score nobody can audit."""
    return {"n": num, "of": den, "fraction": round(num / den, 4) if den else None}


def summarise(inds: list) -> dict:
    def block(rows: list) -> dict:
        return {
            "indicators": len(rows),
            "by_measurement_status": {s: frac(sum(1 for r in rows
                                                  if r.get("measurement_status") == s), len(rows))
                                      for s in STATUSES},
            "evidenced": frac(sum(1 for r in rows if not r.get("gap")), len(rows)),
            "gap": frac(sum(1 for r in rows if r.get("gap")), len(rows)),
            "by_type": dict(collections.Counter(r["type"] for r in rows)),
        }

    out = {"whole": block(inds), "by_criterion": {}, "by_tier": {}, "by_construct": {}}
    for c in sorted({r["criterion_code"] for r in inds}):
        out["by_criterion"][c] = block([r for r in inds if r["criterion_code"] == c])
    for t in sorted({r["tier"] for r in inds}):
        out["by_tier"][t] = block([r for r in inds if r["tier"] == t])
    for con in sorted({r["construct"] for r in inds}):
        out["by_construct"][con] = block([r for r in inds if r["construct"] == con])
    return out


# ---------------------------------------------------------------- inline SVG
def bars(title: str, rows: list, keys: list, width: int = 640) -> str:
    """Stacked horizontal bars. `rows` is [(label, {key: count})]."""
    row_h, pad, left = 26, 8, 132
    height = len(rows) * row_h + 44
    total_max = max((sum(d.values()) for _, d in rows), default=1) or 1
    scale = (width - left - 70) / total_max
    out = [f'<figure><figcaption>{html.escape(title)}</figcaption>',
           f'<svg viewBox="0 0 {width} {height}" role="img" '
           f'aria-label="{html.escape(title)}" width="100%">']
    for i, (label, d) in enumerate(rows):
        y = i * row_h + 6
        out.append(f'<text x="{left - 8}" y="{y + 14}" text-anchor="end" '
                   f'class="lbl">{html.escape(str(label))}</text>')
        x = left
        for k in keys:
            v = d.get(k, 0)
            if not v:
                continue
            w = max(v * scale, 2)
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{row_h - 8}" '
                       f'fill="{COLOURS.get(k, "#64748b")}"><title>{html.escape(str(label))} — '
                       f'{html.escape(k)}: {v}</title></rect>')
            if w > 18:
                out.append(f'<text x="{x + w / 2:.1f}" y="{y + 13}" text-anchor="middle" '
                           f'class="inbar">{v}</text>')
            x += w
        out.append(f'<text x="{x + 6:.1f}" y="{y + 13}" class="tot">{sum(d.values())}</text>')
    out.append("</svg>")
    out.append('<p class="legend">' + " ".join(
        f'<span><i style="background:{COLOURS.get(k, "#64748b")}"></i>{html.escape(k)}</span>'
        for k in keys) + "</p></figure>")
    return "\n".join(out)


def page(g: dict, s: dict, sp: dict) -> str:
    inds = indicators(g)
    by_crit = [(f"{c} · {g_name(g, c)}",
                {k: s["by_criterion"][c]["by_measurement_status"][k]["n"] for k in STATUSES})
               for c in sorted(s["by_criterion"])]
    ev_gap = [(f"{c} · {g_name(g, c)}",
               {"evidenced": s["by_criterion"][c]["evidenced"]["n"],
                "gap": s["by_criterion"][c]["gap"]["n"]})
              for c in sorted(s["by_criterion"])]
    auto = [p for p in sp.values() if p.get("mode") == "auto"]
    coll = [("public-tier AUTO legs",
             {"collector": sum(1 for p in auto if p["collector"] != "none_known"),
              "none_known": sum(1 for p in auto if p["collector"] == "none_known")})]
    w = s["whole"]
    rows = "".join(
        f"<tr><td>{html.escape(p['code'])}</td><td>{html.escape(p['construct'][:60])}</td>"
        f"<td>{html.escape(p['type'])}</td><td><code>{html.escape(p['tier'])}</code></td>"
        f"<td class='{'gap' if p.get('gap') else 'ok'}'>"
        f"{'gap' if p.get('gap') else 'evidenced'}</td>"
        f"<td>{html.escape(p.get('measurement_status', ''))}</td></tr>"
        for p in sorted(inds, key=lambda x: (x['criterion_code'], x['code'])))
    return f"""<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI-readiness framework — progress</title>
<style>
:root {{ --fg:#0f172a; --muted:#64748b; --line:#e2e8f0; --bg:#ffffff; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fg:#e2e8f0; --muted:#94a3b8; --line:#334155; --bg:#0f172a; }} }}
* {{ box-sizing:border-box }}
body {{ margin:0; padding:2rem 1.25rem 4rem; background:var(--bg); color:var(--fg);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  max-width:900px; margin-inline:auto }}
h1 {{ font-size:1.5rem; margin:0 0 .25rem }}
.sub {{ color:var(--muted); margin:0 0 2rem }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:.75rem;
  margin-bottom:2rem }}
.card {{ border:1px solid var(--line); border-radius:10px; padding:.85rem 1rem }}
.card b {{ display:block; font-size:1.6rem; font-weight:600 }}
.card span {{ color:var(--muted); font-size:.82rem }}
figure {{ margin:0 0 2rem }}
figcaption {{ font-weight:600; margin-bottom:.5rem }}
.lbl {{ font-size:11px; fill:var(--muted) }}
.inbar {{ font-size:11px; fill:#fff; font-weight:600 }}
.tot {{ font-size:11px; fill:var(--muted) }}
.legend {{ margin:.35rem 0 0; font-size:.8rem; color:var(--muted) }}
.legend span {{ margin-right:1rem; white-space:nowrap }}
.legend i {{ display:inline-block; width:10px; height:10px; border-radius:2px;
  margin-right:.35rem; vertical-align:-1px }}
table {{ border-collapse:collapse; width:100%; font-size:.85rem }}
th,td {{ text-align:left; padding:.35rem .5rem; border-bottom:1px solid var(--line) }}
th {{ color:var(--muted); font-weight:600 }}
td.gap {{ color:#d97706 }} td.ok {{ color:#059669 }}
.note {{ color:var(--muted); font-size:.85rem; border-left:3px solid var(--line);
  padding-left:.85rem; margin:2rem 0 }}
.wrap {{ overflow-x:auto }}
</style>
<h1>AI-readiness framework — progress</h1>
<p class="sub">Coverage of the assessment instrument, {w['indicators']} indicators across
{len(s['by_criterion'])} criteria. Generated {html.escape(g.get('generated_at', '2026-09-06'))}
from <code>framework/ai_readiness_framework.json</code>.</p>

<div class="cards">
  <div class="card"><b>{w['evidenced']['n']}/{w['evidenced']['of']}</b>
    <span>indicators with corpus evidence</span></div>
  <div class="card"><b>{w['by_measurement_status']['measured']['n']}/{w['indicators']}</b>
    <span>measured</span></div>
  <div class="card"><b>{coll[0][1]['collector']}/{sum(coll[0][1].values())}</b>
    <span>AUTO legs with a named collector</span></div>
  <div class="card"><b>{s['by_tier'].get('public', {}).get('indicators', 0)}</b>
    <span>public-tier indicators</span></div>
</div>

{bars('Indicators by criterion × measurement status', by_crit, list(STATUSES))}
{bars('Evidenced vs gap, by criterion', ev_gap, ['evidenced', 'gap'])}
{bars('Public-tier AUTO legs: named collector vs none known', coll, ['collector', 'none_known'])}

<p class="note"><strong>No composite, deliberately.</strong> Every number here is a fraction
with its counts. A single readiness score embeds a weighting that only a stated purpose can
justify, and no purpose has been stated — assessment protocol §3, and DD-036's two-leg rule
for G1 carried up from the indicator to the framework.</p>

<h2>Indicators</h2>
<div class="wrap"><table>
<thead><tr><th>Code</th><th>Construct</th><th>Type</th><th>Tier</th><th>Evidence</th>
<th>Measurement</th></tr></thead>
<tbody>{rows}</tbody></table></div>
"""


def g_name(g: dict, code: str) -> str:
    for n in g["nodes"]:
        if "AssessmentCriterion" in n["labels"] and n["properties"]["code"] == code:
            return n["properties"]["name"]
    return code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=str(JSON_PATH))
    a = ap.parse_args(argv)
    g = json.loads(Path(a.json).read_text(encoding="utf-8"))
    inds = indicators(g)
    s = summarise(inds)
    sp = specs(g)
    auto = [p for p in sp.values() if p.get("mode") == "auto"]
    s["measurement_specs"] = {
        "total": len(sp),
        "auto_legs": len(auto),
        "with_named_collector": frac(sum(1 for p in auto if p["collector"] != "none_known"),
                                     len(auto)),
        "none_known": [p["leg"] for p in auto if p["collector"] == "none_known"],
        "with_fuji_metric": [p["leg"] for p in auto if p.get("fuji_metric")],
    }
    s["task"] = TASK
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(s, indent=1) + "\n", encoding="utf-8")
    OUT_HTML.write_text(page(g, s, sp), encoding="utf-8")
    print(json.dumps({"whole": s["whole"], "measurement_specs": s["measurement_specs"],
                      "by_tier": {k: v["indicators"] for k, v in s["by_tier"].items()}},
                     indent=1))
    print(f"-> {OUT_JSON.resolve().relative_to(REPO)}  {OUT_HTML.resolve().relative_to(REPO)}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
