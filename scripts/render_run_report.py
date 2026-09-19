#!/usr/bin/env python3
"""An adopter run, rendered: its matrices and its report, as files. **Zero spend, no network,
no Neo4j.**

`cc_tasks/2026-09-19_adopter_path.md` decision 4. `run.py --frame` leaves a payload in
`out/<frame>/state/`; this turns it into what a publisher reads:

    out/<frame>/reports/scan_matrix_{tierA,tierC,product}_<suffix>.{json,csv}
    out/<frame>/reports/publication.yaml      the frame's cycle of record (its newest run)
    out/<frame>/report/<cycle>.md             per body: every verdict with its reason, the
                                              prescriptions ranked for it, what the harness
                                              could not see and what would let it, and the
                                              sentence its rank rests on

**Nothing here is a second implementation.** The matrices are `build_l0_matrices.compute` and
`write_matrices`, the functions that build this project's published matrices, pointed at the
run's directory. Every section of the report is an MCP verb (`get_body`, `get_prescriptions`,
`get_requirements`) called on a `Tools` pointed at the same directory, so the report and the
server can never disagree about a body: they are one answer. Neo4j is not read — `Tools` in run
mode reads a Finding's reason and its bytes from the run's payload — so the report is the same
with the graph up or down.

The run is re-read under the parameters it was measured under (`adopt.params_of_run`): the
committed `params.yaml` plus the payload's recorded overlay, refused unless the two hash to what
the run's Observations carry.

    python scripts/render_run_report.py --frame frames/my_site.yaml [--out out] [--cycle C]
    python scripts/render_run_report.py --run out/my-site [--cycle C]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "mcp"))

TASK = "cc_tasks/2026-09-19_adopter_path.md"


def frame_root(a) -> Path:
    from scan import adopt
    if a.run:
        return Path(a.run).resolve()
    frame = adopt.load_frame(Path(a.frame))
    if frame["kind"] != adopt.DECLARED:
        raise SystemExit(f"REFUSING: {a.frame} is this project's frame; its report is "
                         f"docs/reports/, built by scripts/build_l0_report.py")
    return adopt.frame_dir(Path(a.out).resolve(), frame["frame"])


def build_matrices(where: dict, cycle: str, payload: dict, params: dict) -> dict:
    """The run's three matrices, into its own `reports/`, by the builder of record."""
    import build_l0_matrices as M
    prev = M.STATE
    M.STATE = where["state"]
    try:
        c = M.compute(cycle, params)
        written = M.write_matrices(c, out_dir=where["reports"], fragments=False)
    finally:
        M.STATE = prev
    return {"compute": c, "files": [f for pair in written["files"] for f in pair]}


def update_publication(where: dict, cycle: str, payload: dict) -> str:
    """The frame's cycle of record: its newest FRAME run, by the day measured and then by name.

    A spot run never becomes it (`scan.spot`, decision 2 of the spot task holds here too); a
    spot rendered before any frame run has nothing to be read beside and is refused.
    """
    import yaml
    from scan import spot
    pub = where["publication"]
    have = (yaml.safe_load(pub.read_text(encoding="utf-8")) or {}).get("snapshot_cycle") \
        if pub.is_file() else None
    if spot.is_spot(cycle, payload):
        if not have:
            raise SystemExit(f"REFUSING: {cycle} is a spot run and this frame has no rendered "
                             f"frame run to read it beside. Run the frame first "
                             f"(make scan-now FRAME=...), then the spot.")
        return have
    key = lambda c: (spot.measured_on(c) or "", c)  # noqa: E731
    best = cycle if not have or key(cycle) >= key(have) else have
    pub.parent.mkdir(parents=True, exist_ok=True)
    pub.write_text(
        "# The cycle of record of this frame: its newest frame run. Written by\n"
        f"# scripts/render_run_report.py ({TASK} decision 4); read by score.py --run and by the\n"
        "# MCP server's --run, in place of this project's docs/reports/publication.yaml.\n"
        + yaml.safe_dump({"snapshot_cycle": best}, sort_keys=False), encoding="utf-8")
    return best


def _cell(v) -> str:
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")


def render(where: dict, cycle: str, payload: dict, tools) -> str:
    """The report, as markdown, from the verbs."""
    from scan import spot
    frame = payload.get("frame") or {}
    lines = [f"# {frame.get('name', where['root'].name)}: {cycle}", "",
             f"Rendered by `scripts/render_run_report.py` from `{_shown(where['state'])}/"
             f"{cycle}.json` ({TASK}). Every section below is an answer of the MCP server "
             f"(`mcp/airkg_server.py --run {_shown(where['root'])}`), so the report and the "
             f"server cannot disagree. Neo4j was not read.", "",
             "## The run", "",
             "| | |", "|---|---|",
             f"| measured on | {spot.measured_on(cycle)} |",
             f"| scope | {payload.get('scope')}"
             + (f" ({', '.join(payload.get('spot_targets') or [])})" if payload.get(
                 'spot_targets') else "") + " |",
             f"| frame file | `{frame.get('path')}` (sha256 `{str(frame.get('sha256'))[:12]}…`) |",
             f"| control gate | {payload.get('control_verdict')}: "
             f"{_cell(payload.get('control_reason'))} |",
             f"| surfaces / findings / observations | {payload.get('surfaces')} / "
             f"{payload.get('findings')} / {payload.get('observations')} |",
             f"| verdicts | {_cell(json.dumps(payload.get('verdict_counts')))} |",
             f"| requests per host | {_cell(json.dumps(payload.get('requests_per_host')))} |",
             f"| params_hash | `{str(payload.get('params_hash'))[:12]}…` (base "
             f"`{str(payload.get('base_params_hash'))[:12]}…` plus the cycle overlay) |",
             f"| cycle of record of this frame | {tools.cycle} |", ""]
    bodies = (payload.get("spot_targets") if spot.is_spot(cycle, payload)
              else tools._presc().bodies(cycle))
    for body in bodies:
        b = tools.get_body(body)
        if "error" in b:
            lines += [f"## {body}", "", f"Not on the cycle of record: {b['error']}", ""]
            continue
        lm = b["latest_measurement"]
        lines += [f"## {body}", "", b["summary"], ""]
        if lm["latest_is_spot"]:
            lines += [lm["sentence"], ""]
        lines += ["### Every judged leg", "",
                  "| leg | verdict | surface | why |", "|---|---|---|---|"]
        for c in sorted(b["legs"], key=lambda c: (c["verdict"] != "fail", c["leg"],
                                                  str(c["surface"]))):
            lines.append(f"| {c['leg']} | {c['verdict']} | `{_cell(c['surface'])}` | "
                         f"{_cell(c.get('reason'))} |")
        pr = tools.get_prescriptions(body=body)
        lines += ["", "### What to fix first", "",
                  f"Ranked by `{pr['ranked_by']}`, over the legs {body} fails "
                  f"({', '.join(pr['failing_legs']) or 'none'}). {pr['band_note']}", ""]
        if pr["actions"]:
            lines += ["| action | leg | effort | cost | failing on |", "|---|---|---|---|---|"]
            for a in pr["actions"]:
                lines.append(f"| **{_cell(a['title'])}** (`{a['id']}`) | {a['leg']} | "
                             f"{_cell(a['effort'])} | {_cell(a['cost'])} | "
                             f"{_cell(', '.join(a['failing_on'] or []))} |")
        else:
            lines.append(f"No action applies: {body} fails no leg an action remediates.")
        rq = tools.get_requirements(body=body)
        lines += ["", "### What the harness could not see, and what would let it", "",
                  rq["summary"] + ".", ""]
        for r in rq["by_requirement"]:
            lines.append(f"- {r['line']}")
        lines.append("")
    lines += ["## Files", "",
              f"- payload: `{_shown(where['state'])}/{cycle}.json` (every Observation and "
              f"Finding; re-derivable with `assessment/harness/scan/rederive.py --from`)",
              f"- retained response bodies: `{payload.get('evidence_root')}/`",
              f"- matrices: `{_shown(where['reports'])}/scan_matrix_*`",
              f"- cycle of record: `{_shown(where['publication'])}`", ""]
    return "\n".join(lines)


def _shown(path: Path) -> str:
    try:
        return str(Path(path).relative_to(REPO))
    except ValueError:
        return str(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--frame", metavar="FILE", help="the frame file the run measured")
    g.add_argument("--run", metavar="DIR", help="the frame's directory, out/<frame>/")
    ap.add_argument("--out", default="out", metavar="DIR",
                    help="the --out the run was given (default ./out)")
    ap.add_argument("--cycle", default=None, help="a run other than the frame's LATEST")
    a = ap.parse_args(argv)

    from scan import adopt, load_params
    root = frame_root(a)
    where = adopt.layout(root.parent, root.name)
    if a.cycle:
        cycle = a.cycle
    elif where["latest"].is_file():
        cycle = where["latest"].read_text(encoding="utf-8").strip()
    else:
        raise SystemExit(f"REFUSING: {where['latest']} does not exist; this frame has no run "
                         f"yet (make scan-now FRAME=...)")
    src = where["state"] / f"{cycle}.json"
    if not src.is_file():
        raise SystemExit(f"REFUSING: {src} does not exist")
    payload = json.loads(src.read_text(encoding="utf-8"))
    if not payload.get("frame"):
        raise SystemExit(f"REFUSING: {src} is not an adopter run (no `frame` on the payload)")
    params = adopt.params_of_run(payload, load_params())

    built = build_matrices(where, cycle, payload, params)
    of_record = update_publication(where, cycle, payload)

    import airkg_tools as T
    tools = T.Tools(graph=None, run=root)
    text = render(where, cycle, payload, tools)
    out = where["report"] / f"{cycle}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(json.dumps({"cycle": cycle, "cycle_of_record": of_record,
                      "matrices": [_shown(f) for f in built["files"]],
                      "report": _shown(out)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
