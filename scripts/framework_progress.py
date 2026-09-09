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
    """The framework's indicators. **Candidates are excluded** (DD-054): a candidate is not the
    framework, so it is not in any fraction's numerator OR denominator. Counting one in the
    denominator would make the instrument look less complete for having noticed something;
    counting it in the numerator would adopt it by arithmetic."""
    return [n["properties"] for n in g["nodes"] if "AssessmentIndicator" in n["labels"]
            and n["properties"].get("status") != "candidate"]


def candidates(g: dict) -> list:
    return [n["properties"] for n in g["nodes"] if "AssessmentIndicator" in n["labels"]
            and n["properties"].get("status") == "candidate"]


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


def candidate_banner(s: dict) -> str:
    """Candidates, said out loud rather than left out. A page that simply omitted them would
    be accurate and would hide the one thing a reader most needs to know about them: that they
    exist, and that nobody has adopted them."""
    c = s.get("candidates") or {}
    if not c.get("n"):
        return ""
    codes = ", ".join(html.escape(x) for x in c["codes"])
    return (f'<p class="note"><b>{c["n"]} candidate indicator'
            f'{"s" if c["n"] != 1 else ""} ({codes}) — proposed, not adopted.</b> '
            f'{html.escape(c["note"])}</p>')


#: The four cycle figures. They used to be drawn here, from the matrix file, by two functions
#: that carried their own geometry and their own numbers. They are now generated by
#: `assessment/harness/scan/figures.py` and gated by `tests/test_scan_figures.py`, which
#: resolves every numeral in every figure to a registered Result, a matrix count or a declared
#: axis tick. This page inlines the finished SVG: one artifact, one generator, one gate. The
#: figure files ARE the artifacts (Seldon `Figure` nodes carry their paths), so a page and a
#: paper cannot drift into showing two different pictures of one cycle.
FIGURES_YAML = REPO / "assessment" / "harness" / "scan" / "figures.yaml"


def _figures_module():
    """`assessment/harness/scan/figures.py`, imported for its config and figure NAMES.

    The page used to enumerate the four figure names itself. It no longer does: `FIGURES` and
    the out_dir are the generator's, and a fifth figure that the generator draws but the page
    does not list is a figure nobody sees — which is a silent omission, the worst kind.
    """
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures
    return figures


def figure_svgs() -> dict:
    """`{name: (svg, caption)}` from the generated files, or `{}` if they have not been
    generated. Read from disk rather than re-rendered: the SVG on disk is what the gate
    checked, and rendering a second copy here would put an ungated figure on the page."""
    if not FIGURES_YAML.is_file():
        return {}
    figures = _figures_module()
    cfg = figures.config()
    sys.path.insert(0, str(REPO / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_register_scan_figures", REPO / "scripts" / "register_scan_figures.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = {}
    for name in figures.FIGURES:
        path = REPO / cfg["out_dir"] / f"{name}.svg"
        if path.is_file():
            out[name] = (path.read_text(encoding="utf-8"), mod.CAPTIONS[name])
    return out


#: One fill per class, matching `figures.yaml`. Only the legends read these.
LEGEND = {
    "per_leg_pass_rate": [("#059669", "pass rate"), ("#94a3b8", "Wilson 95 % interval"),
                          ("#0f172a", "control fixtures fired in this cycle")],
    "agencies_by_legs_matrix": [("#059669", "pass"), ("#d97706", "fail"),
                                ("#94a3b8", "not_applicable"), ("#64748b", "error"),
                                ("#c4b5fd", "no admitted surface"),
                                ("#e2e8f0", "no finding")],
    "gap_map_by_criterion": [("#059669", "measured"), ("#3b82f6", "harness_built"),
                             ("#94a3b8", "specified"), ("#a78bfa", "candidate, not counted")],
    "progress_over_snapshots": [("#059669", "measured"), ("#3b82f6", "harness_built"),
                                ("#94a3b8", "specified")],
    # F6 has no rate and no interval by construction, so its legend is verdicts alone.
    "tier_c_reference_hosts": [("#059669", "pass"), ("#d97706", "fail"),
                               ("#64748b", "error"), ("#94a3b8", "not_applicable"),
                               ("#e2e8f0", "leg not asked of this host")],
    "cycle_over_cycle": [("#94a3b8", "cycle 1 pass rate"), ("#059669", "cycle 2 pass rate"),
                         ("#e2e8f0", "cycle 1 Wilson 95 % interval"),
                         ("#94a3b8", "cycle 2 Wilson 95 % interval")],
}


def figure_block(name: str, body: str, caption: str) -> str:
    legend = " ".join(f'<span><i style="background:{c}"></i>{html.escape(t)}</span>'
                      for c, t in LEGEND[name])
    return (f'<figure id="{name}"><figcaption>{html.escape(caption)}</figcaption>'
            f'<div class="wrap">{body}</div><p class="legend">{legend}</p></figure>')

#: The page's footer. Two things belong here and nowhere else: the prior art the encodings
#: implement, and the sentence the cycle's own RESULT wrote about what it does not claim —
#: quoted verbatim, because a non-claim that gets paraphrased on the way to the reader is a
#: claim.
def matrix_for_page() -> dict:
    """The matrix of the cycle currently being drawn. One read, shared by the non-claims
    paragraph and anything else that needs the cycle's own numbers."""
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures as _figs
    cfg = _figs.config()
    return json.loads((REPO / cfg["matrix_json"]).read_text(encoding="utf-8"))


def _frame_clause() -> str:
    """What the frame IS, on the page rather than only in a design decision.

    A reader looking at a rate needs to know it is over 16 recognized statistical agencies and
    units, that 3 reference hosts sit beside them at tier 0 only and in no rate here, and that
    some agencies contribute a thin row because their products are not yet declared. Read from
    the targets DataFile, so it cannot drift from the frame the cycle actually measured.
    """
    src = REPO / "state" / "scan_targets_fss_2026-09.json"
    if not src.is_file():
        return ""
    d = json.loads(src.read_text(encoding="utf-8"))
    pending = d.get("agencies_pending_operator_declaration") or []
    return (f"The frame is {d.get('tier_a_agencies')} OMB-recognized statistical agencies and "
            f"units plus {d.get('tier_c_hosts')} reference hosts, on "
            f"{d.get('netloc_count')} netlocs; the reference hosts are judged on tier-0 legs "
            f"only and appear in no rate on this page (F6 shows them on their own). "
            f"{len(pending)} agencies carry a host row and its probes and nothing else, "
            f"because their products are not yet declared ({', '.join(pending)}) — a thin row "
            f"is a measurement, not a gap. ")


def _rule_changed_clause() -> str:
    """Which legs' rules moved between the two cycles F5 draws, read from the SAME declaration
    the figure reads.

    It was the literal "on A1 and A3 it did" — true for the cycle it was written for, and a
    false statement about every cycle after. `figures.yaml`'s `compare_to.rule_changed` is
    where the figure gets its marks; a page that restates them in prose is a second source of
    the same fact, and the stale one is always the prose.
    """
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures as _figs
    changed = (_figs.config()["compare_to"].get("rule_changed") or {})
    if not changed:
        return ("no leg's rule moved between these two, so every difference on F5 is the "
                "host.")
    named = ", ".join(f"{html.escape(leg)} ({html.escape(how)})"
                      for leg, how in sorted(changed.items()))
    return (f"on {named} it did, and a difference there is the instrument moving, not the "
            f"host.")


def rejudged_note() -> str:
    """Which of this page's rates have been superseded by a re-judgement, and under which rules.

    A re-judged cycle is its own cycle with its own Results and its own figures
    (`cc_tasks/2026-09-08_scan_harness_v4.md` §1.5), so nothing on this page silently changes
    when one is published — which is right, and is exactly why the page has to SAY so. A rate
    drawn here that a later re-judgement corrected is a number a reader would otherwise carry
    away as current.

    Empty when no re-judgement of the cycle being drawn exists, which is every cycle before
    this one.
    """
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures as _figs
    cfg = _figs.config()
    path = REPO / "state" / f"{cfg['cycle']}_rj1.json"
    if not path.is_file():
        return ""
    rj = json.loads(path.read_text(encoding="utf-8"))
    changed = rj.get("rules_changed_since_source") or {}
    moved = rj.get("verdicts_moved") or []
    by_leg = {}
    for m in moved:
        by_leg.setdefault(m["leg"], []).append(m)
    rules = "".join(
        f"<li><b>{html.escape(leg)}</b>: {html.escape(v['source'])} → "
        f"{html.escape(v['current'])} — {len(by_leg.get(leg, []))} verdict(s) moved</li>"
        for leg, v in sorted(changed.items()))
    not_judged = rj.get("legs_not_judged") or {}
    return (f"<h3>Rates on this page that have been re-judged</h3>"
            f"<p>The figures above are cycle <code>{html.escape(cfg['cycle'])}</code> "
            f"<b>as it was judged when it ran</b>. Its stored Observations have since been "
            f"re-judged under corrected rules as "
            f"<code>{html.escape(rj['cycle'])}</code> — the same evidence, nothing re-fetched, "
            f"no Observation created — and that cycle has its own Results and its own F1 and "
            f"F5. {len(moved)} verdict(s) moved in total. The rules that differ:</p>"
            f"<ul>{rules}</ul>"
            f"<p>{len(not_judged)} leg(s) were not re-judged at all and register nothing "
            f"there, each with its reason on the payload: "
            f"{html.escape(', '.join(sorted(not_judged)))}. Not measured is a reason, not a "
            f"zero (DD-055).</p>")


def non_claims() -> str:
    """What the page does NOT claim, with its numbers DERIVED from the cycle being shown.

    This was a fixed paragraph carrying cycle 1's literals — "n = 23 per leg", "eight legs at
    zero with an upper bound of 0.14". Cycle 2's denominator is **not** constant (two ERS
    surfaces went unobservable on a host-side DNS transient, so `applicable_n` is 22 on some
    legs and 23 on others), and a non-claim that quotes a stale number is a claim
    (`cc_tasks/2026-09-07_scan_run_2_ADDENDUM-01.md` defect 3). Derived, so it cannot go stale
    without the figures going stale with it.
    """
    mx = matrix_for_page()
    per = mx["per_leg"]
    ns = sorted({s["applicable_n"] for s in per.values()})
    n_txt = (f"n = {ns[0]} per leg" if len(ns) == 1 else
             f"n = {ns[0]}–{ns[-1]} depending on the leg, because a leg is denominated only "
             f"by the surfaces it could actually observe")
    zeros = [l for l, s in per.items() if s["applicable_n"] and s["pass"] == 0]
    hi = max((per[l]["ci95_high"] for l in zeros), default=0.0)
    surfaces = len([r for r in mx["rows"] if r["surface_kind"] != "well_known"])
    return (
        f"One cycle, one client identity, one day, {html.escape(n_txt)}. The rates here are a "
        f"measurement of these {surfaces} surfaces in cycle "
        f"{html.escape(mx['cycle'])}, selected by a rule stated before any product was "
        f"chosen, and they are not a score of any agency: there is no composite, no ranking, "
        f"and the legs are not comparable to each other. "
        f"{len(mx['agencies_without_surfaces'])} of {len(mx['agencies'])} agencies "
        f"contributed no surface at all, which is a property of the instrument as much as of "
        f"them. {_frame_clause()}"
        f"{len(zeros)} legs are at zero with an upper bound of {hi:.2f}, and a zero is "
        f"not evidence of absence at these denominators. Where a leg's rate moved between "
        f"cycles, F5 marks whether the RULE changed: {_rule_changed_clause()}")

CITATIONS = [
    ("Intervals", "Wilson, E. B. (1927). Probable inference, the law of succession, and "
                  "statistical inference. <i>JASA</i> 22:209. Brown, Cai &amp; DasGupta "
                  "(2001), <i>Statist. Sci.</i> 16:101, and Newcombe (1998), <i>Stat. Med.</i> "
                  "17:857, both recommend the score interval over Wald at small n and at 0 or "
                  "n successes."),
    ("Zero counts", "Hanley &amp; Lippman-Hand (1983), <i>JAMA</i> 249:1743 \u2014 the rule of "
                    "three: with 0 events in n, the 95 % upper bound is about 3/n. At these "
                    "denominators that is about 0.13\u20130.14, which is what the Wilson "
                    "bounds printed on F1 come to."),
    ("Encoding", "Cleveland &amp; McGill (1984), <i>JASA</i> 79:531, and Cleveland (1985), "
                 "<i>The Elements of Graphing Data</i>: position along a common scale beats "
                 "length. F1 is a dot-and-interval plot, not bars."),
    ("Matrix", "Bertin (1967/1983), <i>Semiology of Graphics</i>, the reorderable matrix \u2014 "
               "deliberately NOT reordered here: reordering rows by pass count is a ranking of "
               "agencies."),
    ("Fractions", "Gigerenzer &amp; Hoffrage (1995), <i>Psychol. Rev.</i> 102:684: natural "
                  "frequencies beside every rate, never a bare percentage."),
    ("Small multiples", "Tufte (1983), <i>The Visual Display of Quantitative Information</i>."),
]

EXCLUDED = [
    "any figure breaking errors out BY CLASS. The classes are now sound \u2014 "
    "<code>scan/errors.py</code> names every failure and the log carries one convention after "
    "the 266-observation overlay of <code>cc_tasks/2026-09-07_scan_run_2.md</code> \u00a71.2 "
    "\u2014 and the counts are registered as Results per cycle; what is excluded is a CHART of "
    "them, because an error class is a fact about the instrument and this page is about the "
    "products",
    "any agency composite, and any ranking of agencies",
    "any language comparing one leg to another: they measure different constructs",
    "the candidate indicator A12 in any fraction (DD-054)",
]

def _user_agent() -> str:
    """The one client identity, from `params.manners.user_agent` (DD-060)."""
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import load_params
    return str(load_params()["manners"]["user_agent"])


def requests_table() -> str:
    """What this scanner ASKED of each host in the current cycle, from the cycle payload.

    On the page, not only in a RESULT, because the manners claim the harness makes in public
    — RFC 9309 obeyed, identified UA, one request per second per host, no forms, no logins —
    is a claim about our conduct toward someone else's server, and a reader of a page that
    scores those servers is entitled to the load we put on them. Empty when the payload has
    no counts, which is every cycle before `manners.Fetcher` counted them.
    """
    import yaml as _yaml
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures as _figs
    cfg = _figs.config()
    path = REPO / "state" / f"{cfg['cycle']}.json"
    if not path.is_file():
        return ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    per_host = payload.get("requests_per_host") or {}
    if not per_host:
        return ""
    rows = "".join(f"<tr><td><code>{html.escape(h)}</code></td><td>{n}</td></tr>"
                   for h, n in sorted(per_host.items()))
    return (f"<h3>What this cycle asked of each host</h3>"
            f"<p>HTTP requests issued in cycle <code>{html.escape(cfg['cycle'])}</code>, "
            f"counted at the socket and including <code>robots.txt</code> fetches, 429/503 "
            f"retries and HEAD-refused GET fallbacks. Rate-limited to one request per second "
            # The UA is READ, not typed. DD-060 is that there is exactly one client
            # identity and `params.manners.user_agent` is where it lives; this page carried
            # `ai-readiness-kg-scanner/0.1` as a literal and went on printing it after the
            # identity moved to `0.2`, so the page made a false claim about how the
            # measurement below it was taken.
            f"per host under the identified user agent "
            f"<code>{html.escape(_user_agent())}</code>, with <code>robots.txt</code> obeyed "
            f"(RFC 9309). No forms, no logins, no query-string fuzzing. Total "
            f"{sum(per_host.values())} across {len(per_host)} hosts.</p>"
            f'<div class="wrap"><table><thead><tr><th>Host</th><th>Requests</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></div>")


def footer() -> str:
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures as _figs
    cfg = _figs.config()
    return ("<footer><h3>What this does not claim</h3><p>" + non_claims() + "</p>"
            + "<h3>Excluded on purpose</h3><ul>"
            + "".join(f"<li>{t}</li>" for t in EXCLUDED) + "</ul>"
            + rejudged_note()
            + requests_table()
            + "<h3>Prior art the figures implement</h3><ul>"
            + "".join(f"<li><b>{k}.</b> {v}</li>" for k, v in CITATIONS) + "</ul>"
            + "<p>Figures generated by <code>assessment/harness/scan/figures.py</code>, gated "
            + "by <code>tests/test_scan_figures.py</code>: every numeral resolves to a "
            + "registered Result, a count in <code>"
            + html.escape(cfg["matrix_json"]) + "</code>, or a declared axis tick. Static "
            + "SVG, inline, no external resource of any kind.</p></footer>")


def page(g: dict, s: dict, sp: dict) -> str:
    inds = indicators(g)
    figs = figure_svgs()
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
.unob {{ font-weight:700 }}
.grp {{ font-size:11px; fill:var(--fg); font-weight:600 }}
.num {{ font-size:11px; fill:var(--fg); font-variant-numeric:tabular-nums }}
.codes {{ font-size:10px; fill:var(--muted) }}
.sub {{ font-size:10px; fill:var(--muted) }}
figure svg {{ min-width:640px }}
footer {{ margin-top:3rem; padding-top:1.25rem; border-top:1px solid var(--line);
  color:var(--muted); font-size:.82rem }}
footer h3 {{ font-size:.9rem; color:var(--fg); margin:1.25rem 0 .4rem }}
footer ul {{ margin:.25rem 0; padding-left:1.1rem }}
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
{candidate_banner(s)}

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

<h2>{html.escape(cycle_heading())}</h2>
{''.join(figure_block(n, b, c) for n, (b, c) in figs.items())}

<p class="note"><strong>No composite, deliberately.</strong> Every number here is a fraction
with its counts. A single readiness score embeds a weighting that only a stated purpose can
justify, and no purpose has been stated — assessment protocol §3, and DD-036's two-leg rule
for G1 carried up from the indicator to the framework.</p>

<h2>Indicators</h2>
<div class="wrap"><table>
<thead><tr><th>Code</th><th>Construct</th><th>Type</th><th>Tier</th><th>Evidence</th>
<th>Measurement</th></tr></thead>
<tbody>{rows}</tbody></table></div>
{footer()}
"""


def cycle_heading() -> str:
    """"The <cycle> cycle" — from `params.cycle.name`, never typed. The page carried the
    literal `2026-09-07`, which would have headed cycle 2's figures with cycle 1's date."""
    sys.path.insert(0, str(REPO / "assessment" / "harness"))
    from scan import figures as _figs
    return f"The {_figs.config()['cycle_suffix']} cycle"


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
    # Candidates are their own status class, reported and NOT counted (DD-054). Reporting them
    # here rather than only in the skeleton means the page can say "1 candidate, not counted"
    # instead of leaving a reader to wonder why 48 indicators became 48 again.
    cands = candidates(g)
    s["candidates"] = {"n": len(cands),
                       "codes": [c["code"] for c in cands],
                       "counted_in_any_fraction": False,
                       "note": ("A candidate is proposed, not adopted. It is excluded from "
                                "every numerator AND every denominator; promotion is an "
                                "operator decision (DD-054).")}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(s, indent=1) + "\n", encoding="utf-8")
    OUT_HTML.write_text(page(g, s, sp), encoding="utf-8")
    print(json.dumps({"whole": s["whole"], "candidates": s["candidates"],
                      "measurement_specs": s["measurement_specs"],
                      "by_tier": {k: v["indicators"] for k, v in s["by_tier"].items()}},
                     indent=1))
    print(f"-> {OUT_JSON.resolve().relative_to(REPO)}  {OUT_HTML.resolve().relative_to(REPO)}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
