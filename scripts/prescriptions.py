#!/usr/bin/env python3
"""The prescription layer as a query. **Zero spend, no network, reads only.**

`cc_tasks/2026-09-17_prescription_layer.md` decision 4, under DN-005 §2.3: *this layer is what
makes "you need this, here is what you do, here is the effort, here is the cost, here is the
value" a query rather than a slide.* So it is a script, and what a slide would show is its
output.

    scripts/prescriptions.py --body NCHS      one body on the cycle of record
    scripts/prescriptions.py --all            every action, ranked by bodies failing now
    scripts/prescriptions.py --bands          every band with the class it comes from

**The bands are notional and the output says so once, not forty-five times.** Every effort and
cost band in this layer is a relative estimate assigned by technique class
(`cc_tasks/2026-09-17_notional_bands.md`, DN-005 ADDENDUM_03), so a `(notional)` marker goes on
the header line and the adjustment instruction — `band_note`, carried verbatim on every action —
is printed ONCE per invocation. Repeating either beside every band would train a reader to skim
the one sentence that says what the number is not.

Two sources and no third: the framework of record (`Action` nodes and `REMEDIATES` edges, as
`scripts/tag_prescriptions.py` wrote them) and the published matrices of the cycle of record
(`docs/reports/publication.yaml:snapshot_cycle`). It reads Neo4j for nothing — the record is
the source of truth and the projection is a projection, so a query that needs the database up
to answer would be asking the wrong thing.

**A body's failing legs come from the matrices, not from the actions.** The matrix says which
bodies fail which leg; the record says which actions close which outcome of that leg's rule.
Where a leg's rule has more than one failing outcome, every action on the leg is printed with
the outcome it closes, because the matrix carries verdicts and not reasons and nothing here
may guess which branch fired.

**Spot cycles** (`cc_tasks/2026-09-19_spot_scan.md` decision 3). A body may have been measured
again, alone, after the snapshot — a spot cycle, run when a publisher asks to see its fixes.
`latest_for(body)` names the newest measurement of a body, whichever cycle that is, and
`since_snapshot(body)` diffs it against the snapshot leg by leg. `--body` lists a body's
failures from its LATEST measurement; `bodies_failing_now` is a frame quantity and stays the
snapshot's, because a spot of one body says nothing about how many others fail a leg.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import spot  # noqa: E402  the one definition of what a spot cycle is

RECORD = REPO / "framework" / "ai_readiness_framework.json"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
#: Where the published matrices are read. A module global read at call time, so the spot scan's
#: loopback gate can point every view at a throwaway tree (`cc_tasks/2026-09-19_spot_scan.md`
#: decision 5). `scripts/score.py` reads matrices through here too.
REPORTS = REPO / "docs" / "reports"

#: Printed after the header line of every mode, never beside a band.
NOTIONAL = "(notional)"


def load_record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def actions(g: dict) -> list:
    """Every Action with the indicator it remediates, sorted by value then by id."""
    edges = {e["from"]: e for e in g["edges"] if e["type"] == "REMEDIATES"}
    out = []
    for n in g["nodes"]:
        if "Action" not in n["labels"]:
            continue
        p = dict(n["properties"])
        p["id"] = n["id"]
        p["indicator_id"] = edges[n["id"]]["to"]
        out.append(p)
    out.sort(key=lambda a: (-a["value"]["bodies_failing_now"], a["leg"], a["id"]))
    return out


def use_run(frame_dir) -> None:
    """Point this module's readers at an adopter's frame directory (`out/<frame>/`) instead of
    this project's published tree. `cc_tasks/2026-09-19_adopter_path.md` decision 4.

    The two module globals every reader here goes through are all that move: the matrices
    are `out/<frame>/reports/`, and the cycle of record is that directory's own
    `publication.yaml`, which `scripts/render_run_report.py` writes after each run of the
    frame. The framework record, and so every action and band, stays this repository's. Called
    by `score.py --run`, `render_run_report.py` and the MCP server's `--run`, each in a process
    or a module copy of its own.
    """
    global REPORTS, PUBLICATION
    from scan import adopt
    where = adopt.layout(Path(frame_dir).resolve().parent, Path(frame_dir).resolve().name)
    REPORTS, PUBLICATION = where["reports"], where["publication"]


def snapshot_cycle() -> str:
    import yaml
    cycle = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))["snapshot_cycle"]
    spot.refuse_as_snapshot(cycle)
    return cycle


def _shown(path: Path) -> str:
    """Repo-relative where it can be; the absolute path for a throwaway tree outside it."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def matrices(cycle: str) -> list:
    suffix = cycle.replace("scan_", "")
    out = []
    for kind in ("tierA", "product"):
        path = REPORTS / f"scan_matrix_{kind}_{suffix}.json"
        m = json.loads(path.read_text(encoding="utf-8"))
        m["_kind"], m["_path"] = kind, _shown(path)
        out.append(m)
    return out


# ------------------------------------------------------------------ spot cycles (decision 3)

def published_cycles() -> dict:
    """`{"full": [...], "spot": [...]}`: every cycle with a published host-level matrix, split
    by what it measured. A spot is known by its matrix header (`scope: spot`) or its name, the
    two `scan.spot` reads; a frame cycle is everything else. Sorted by the day measured, then
    name."""
    out: dict = {"full": [], "spot": []}
    for path in sorted(REPORTS.glob("scan_matrix_tierA_*.json")):
        suffix = path.name[len("scan_matrix_tierA_"):-len(".json")]
        head = json.loads(path.read_text(encoding="utf-8"))
        # The cycle is the FILE's, as `matrices` addresses it; the header is read only for
        # `scope`, so a header whose `cycle` field disagrees with its file cannot move a view.
        cycle = suffix if suffix.startswith(spot.SPOT_PREFIX) else f"scan_{suffix}"
        out["spot" if spot.is_spot(cycle, head) else "full"].append(cycle)
    for k in out:
        out[k].sort(key=lambda c: (spot.measured_on(c) or "", c))
    return out


def spot_info(cycle: str) -> dict:
    """One spot cycle as a view lists it: its bodies, its day, its matrices."""
    mats = matrices(cycle)
    head = mats[0]
    return {"cycle": cycle, "measured_on": spot.measured_on(cycle),
            "bodies": list(head.get("spot_targets") or bodies(cycle)),
            "matrices": [m["_path"] for m in mats]}


def latest_for(body: str) -> str:
    """The newest measurement of `body`: the snapshot, or a spot cycle whose matrices hold the
    body and whose day is not before the snapshot's measurement.

    Ordered by the day the EVIDENCE was collected (`spot.measured_on`), never by a cycle's
    generation: the snapshot `scan_2026-09-10_rj4` is a 2026-09-19 judgement of 2026-09-10
    bytes, and a spot of 2026-09-15 saw the body later than it did. A spot on the snapshot's
    own day wins the tie, because a spot is only ever requested after a snapshot exists.
    """
    snap = snapshot_cycle()
    best = (spot.measured_on(snap) or "", 0, snap)
    for c in published_cycles()["spot"]:
        if body in bodies(c):
            best = max(best, (spot.measured_on(c) or "", 1, c))
    return best[2]


def leg_states(cycle: str, body: str) -> dict:
    """`{leg: state}` for one body on one cycle, over both matrices: `fail` if any of its rows
    fails the leg, `pass` if every judged row passes, otherwise the verdicts it does carry,
    joined (`error`, `not_applicable`, `error/pass`) — so a leg the harness could not see is
    never reported as fixed or as broken."""
    seen: dict = {}
    for m in matrices(cycle):
        for r in m["rows"]:
            if r["agency"] != body or (m["_kind"] == "product" and not r.get("declared")):
                continue
            for leg in m["legs"]:
                v = r["verdicts"].get(leg)
                if v is not None:
                    seen.setdefault(leg, set()).add(v)
    out = {}
    for leg, vs in seen.items():
        out[leg] = ("fail" if "fail" in vs else "pass" if vs == {"pass"}
                    else "/".join(sorted(vs)))
    return out


def since_snapshot(body: str) -> dict:
    """The body on the snapshot and on its latest measurement, leg by leg.

    `passed_since_snapshot`: failed on the snapshot, passes now. `still_failing`: fails on
    both. `failing_since_snapshot`: fails now and did not then. `other_changes`: a leg whose
    state moved in any other way, with both states — typically a leg one cycle could not see.
    A leg judged on only one of the two is listed under `judged_on_one_only`, never as a change.
    """
    snap, latest = snapshot_cycle(), latest_for(body)
    a, b = leg_states(snap, body), leg_states(latest, body)
    common = sorted(set(a) & set(b))
    passed = [l for l in common if a[l] == "fail" and b[l] == "pass"]
    still = [l for l in common if a[l] == "fail" and b[l] == "fail"]
    newly = [l for l in common if a[l] != "fail" and b[l] == "fail"]
    other = [{"leg": l, "snapshot": a[l], "latest": b[l]} for l in common
             if a[l] != b[l] and l not in passed + newly]
    one = sorted(set(a) ^ set(b))
    if latest == snap:
        sentence = (f"{body}'s latest measurement is the snapshot {snap}; no spot cycle has "
                    f"measured it since.")
    else:
        sentence = (f"{body} measured again by spot cycle {latest} on "
                    f"{spot.measured_on(latest)} (snapshot {snap}, measured "
                    f"{spot.measured_on(snap)}). passed since the snapshot: "
                    f"{', '.join(passed) or 'none'}; still failing: {', '.join(still) or 'none'}"
                    + (f"; failing since the snapshot: {', '.join(newly)}" if newly else "")
                    + ".")
    return {"body": body, "snapshot": snap, "snapshot_measured_on": spot.measured_on(snap),
            "latest": latest, "latest_measured_on": spot.measured_on(latest),
            "latest_is_spot": latest != snap,
            "passed_since_snapshot": passed, "still_failing": still,
            "failing_since_snapshot": newly, "other_changes": other,
            "judged_on_one_only": one, "latest_verdicts": b, "sentence": sentence}


def on_cycle(acts: list, cycle: str) -> list:
    """`acts` with `value.bodies_failing_now` as it would read on `cycle`, re-ranked.

    The record's value is computed from the SNAPSHOT's matrices when `tag_prescriptions.py`
    writes it, so printing it under another cycle's name would print the snapshot's ranking
    with the wrong cycle in the header. For any other cycle it is recomputed here from that
    cycle's matrices by the record's own definition: per leg, the bodies with at least one row
    carrying `fail` (`tag_prescriptions.matrix_fail_bodies`). The record is never written.
    `cc_tasks/2026-09-18_rejudge_seven_legs.md` decision 4.
    """
    if cycle == snapshot_cycle():
        return acts
    per_leg: dict = {}
    for body, legs in failing(cycle).items():
        for leg in legs:
            per_leg[leg] = per_leg.get(leg, 0) + 1
    out = []
    for a in acts:
        b = dict(a, value=dict(a["value"], bodies_failing_now=per_leg.get(a["leg"], 0)))
        out.append(b)
    out.sort(key=lambda a: (-a["value"]["bodies_failing_now"], a["leg"], a["id"]))
    return out


def failing(cycle: str) -> dict:
    """`{body: {leg: [row labels that failed it]}}` over both matrices of the cycle."""
    out: dict = {}
    for m in matrices(cycle):
        rows = [r for r in m["rows"] if m["_kind"] != "product" or r.get("declared")]
        for r in rows:
            label = r.get("host_surface") or r.get("surface") or r["agency"]
            for leg in m["legs"]:
                if r["verdicts"].get(leg) == "fail":
                    out.setdefault(r["agency"], {}).setdefault(leg, []).append(label)
    return out


def bodies(cycle: str) -> list:
    seen = []
    for m in matrices(cycle):
        for r in m["rows"]:
            if m["_kind"] == "product" and not r.get("declared"):
                continue
            if r["agency"] not in seen:
                seen.append(r["agency"])
    return sorted(seen)


def band(a: dict, which: str) -> str:
    """One band, as its word. A band whose source is a document locator rather than the
    notional marker prints the locator with it, because that is the one a reader may rely on
    without adjusting it for their own shop."""
    value, src = a[f"{which}_band"], a[f"{which}_source"]
    return value if src.startswith("notional:") else f"{value} ({src})"


def band_note(acts: list) -> str:
    """The adjustment instruction, read off the record rather than restated here. Every action
    carries it verbatim; if two ever disagreed the query would be choosing between them
    silently, so it refuses instead."""
    notes = {a["band_note"] for a in acts}
    if len(notes) != 1:
        raise SystemExit(f"FATAL: {len(notes)} distinct band_note(s) on the record; "
                         f"every action carries the same one or the query cannot print it once")
    return notes.pop()


def print_band_note(acts: list, width: int) -> None:
    print(f"\n{'-' * width}")
    print(wrap(band_note(acts), width, ""))


def wrap(text: str, width: int, indent: str) -> str:
    import textwrap
    return "\n".join(textwrap.fill(text, width, initial_indent=indent,
                                   subsequent_indent=indent).splitlines())


def print_body(name: str, g: dict, cycle: str, width: int) -> int:
    fails = failing(cycle)
    all_bodies = bodies(cycle)
    if name not in all_bodies:
        print(f"'{name}' is not a body on cycle {cycle}. Bodies: {', '.join(all_bodies)}")
        return 2
    acts = on_cycle(actions(g), cycle)
    mine = fails.get(name, {})
    # Decision 3: on the cycle of record, a body's failures are its LATEST measurement's. The
    # ranking below still reads `bodies_failing_now` from `acts`, which is the snapshot's.
    latest = latest_for(name) if cycle == snapshot_cycle() else cycle
    if latest != cycle:
        mine = failing(latest).get(name, {})
    print(f"# {name} — prescriptions from cycle {cycle}")
    if latest != cycle:
        print(f"#   failing legs from {name}'s latest measurement, spot cycle {latest} "
              f"({spot.measured_on(latest)}); bodies failing now is the snapshot's")
        print(wrap(since_snapshot(name)["sentence"], width, "#   "))
    print(f"#   {len(mine)} failing leg(s) of the {sum(len(m['legs']) for m in matrices(cycle))}"
          f" judged; {len(all_bodies)} bodies on this cycle")
    print(f"#   effort and cost are relative bands {NOTIONAL} — the note is at the end")
    if not mine:
        print("\nNo leg on this cycle carries the verdict `fail` for this body.")
        return 0
    order = sorted(mine, key=lambda l: -next(
        a["value"]["bodies_failing_now"] for a in acts if a["leg"] == l))
    for leg in order:
        on_leg = [a for a in acts if a["leg"] == leg]
        shared = on_leg[0]["value"]["bodies_failing_now"]
        print(f"\n{'=' * width}\n{leg}  ({on_leg[0]['indicator_id']})"
              f"   failing on: {', '.join(sorted(set(mine[leg])))}")
        print(f"   {shared} of {len(all_bodies)} bodies fail this leg"
              f" ({shared - 1} other{'' if shared - 1 == 1 else 's'} share it)")
        for a in on_leg:
            print(f"\n   [{a['outcome']}] {a['title']}")
            print(wrap(a["description"], width, "      "))
            print(f"      effort: {band(a, 'effort')}    cost: {band(a, 'cost')}")
            print(f"      verified by: {a['verifies_by']}")
            for s in a["technique_source"]:
                print(wrap(f"technique: {s}", width, "      "))
    print_band_note(acts, width)
    return 0


def print_all(g: dict, cycle: str, width: int) -> int:
    acts = on_cycle(actions(g), cycle)
    total = len(bodies(cycle))
    print(f"# every action, ranked by bodies failing now — cycle {cycle}, {total} bodies")
    if cycle != snapshot_cycle():
        print(f"# not the cycle of record ({snapshot_cycle()}): bodies failing recomputed from "
              f"this cycle's matrices; the record's stored value is the snapshot's")
    print(f"# {len(acts)} actions over {len({a['leg'] for a in acts})} legs")
    print(f"# effort and cost are relative bands {NOTIONAL} — the note is at the end\n")
    head = f"{'bodies':>6}  {'leg':<13}  {'outcome':<36}  {'effort':<8}  {'cost':<10}  action"
    print(head)
    print("-" * len(head))
    for a in acts:
        n = a["value"]["bodies_failing_now"]
        pub = "" if a["applies_to_publisher"] else "  [not a publisher action]"
        print(f"{n:>6}  {a['leg']:<13}  {a['outcome']:<36}  "
              f"{band(a, 'effort'):<8}  {band(a, 'cost'):<10}  {a['title']}{pub}")
    print_band_note(acts, width)
    return 0


def print_bands(g: dict, width: int) -> int:
    """Every band with the class it comes from. This is the mode that was `--pending` while the
    bands were empty; it answers the same question — where does this band come from — now that
    they are filled, so the flag keeps its old name as an alias."""
    from collections import Counter
    acts = actions(g)
    n_notional = sum(1 for a in acts for b in ("effort", "cost")
                     if a[f"{b}_source"].startswith("notional:"))
    print(f"# {n_notional} of {2 * len(acts)} band(s) on {len(acts)} action(s) are notional "
          f"{NOTIONAL}: no document on disk states an effort or a cost for these techniques.")
    print("# The band comes from the action's technique class, not from a per-action estimate.")
    per_class = Counter(a["technique_class"] for a in acts)
    print("\n" + ", ".join(f"{c} {n}" for c, n in sorted(per_class.items())) + "\n")
    print(f"{'action':<62}  {'class':<24}  {'effort':<8}  cost")
    print("-" * 110)
    for a in acts:
        print(f"{a['id']:<62}  {a['technique_class']:<24}  "
              f"{band(a, 'effort'):<8}  {band(a, 'cost')}")
    print_band_note(acts, width)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g1 = ap.add_mutually_exclusive_group(required=True)
    g1.add_argument("--body", metavar="NAME", help="one body on the cycle of record")
    g1.add_argument("--all", action="store_true", help="every action, ranked by value")
    g1.add_argument("--bands", action="store_true",
                    help="every band with the class it comes from")
    g1.add_argument("--pending", action="store_true",
                    help="the former name of --bands, kept because "
                         "cc_tasks/2026-09-17_prescription_layer_RESULT.md cites it")
    ap.add_argument("--width", type=int, default=96)
    # `scripts/score.py --cycle`'s twin (`cc_tasks/2026-09-18_rejudge_seven_legs.md` decision
    # 4): what the prescriptions would say if the report's snapshot moved, read before it does.
    # The default stays the cycle of record, so every published answer is unchanged.
    ap.add_argument("--cycle", default=None,
                    help="a cycle with published matrices other than the cycle of record")
    a = ap.parse_args(argv)
    g, cycle = load_record(), (a.cycle or snapshot_cycle())
    if a.body:
        return print_body(a.body, g, cycle, a.width)
    if a.all:
        return print_all(g, cycle, a.width)
    if a.pending:
        print("# --pending is the former name of --bands; no band is pending since "
              "cc_tasks/2026-09-17_notional_bands.md.", file=sys.stderr)
    return print_bands(g, a.width)


if __name__ == "__main__":
    raise SystemExit(main())
