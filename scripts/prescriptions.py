#!/usr/bin/env python3
"""The prescription layer as a query. **Zero spend, no network, reads only.**

`cc_tasks/2026-09-17_prescription_layer.md` decision 4, under DN-005 §2.3: *this layer is what
makes "you need this, here is what you do, here is the effort, here is the cost, here is the
value" a query rather than a slide.* So it is a script, and what a slide would show is its
output.

    scripts/prescriptions.py --body NCHS      one body on the cycle of record
    scripts/prescriptions.py --all            every action, ranked by bodies failing now
    scripts/prescriptions.py --pending        the bands no source on disk supports, as a table

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
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RECORD = REPO / "framework" / "ai_readiness_framework.json"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
PENDING = "estimate:pending"


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


def snapshot_cycle() -> str:
    import yaml
    return yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))["snapshot_cycle"]


def matrices(cycle: str) -> list:
    suffix = cycle.replace("scan_", "")
    out = []
    for kind in ("tierA", "product"):
        path = REPO / "docs" / "reports" / f"scan_matrix_{kind}_{suffix}.json"
        m = json.loads(path.read_text(encoding="utf-8"))
        m["_kind"], m["_path"] = kind, str(path.relative_to(REPO))
        out.append(m)
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
    """What to print for one band. `pending` is printed as `pending`, never as a blank cell:
    an empty cell reads as zero effort, and the whole point is that nobody has said."""
    if a[f"{which}_source"] == PENDING:
        return "pending"
    return f"{a[f'{which}_band']} ({a[f'{which}_source']})"


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
    acts = actions(g)
    mine = fails.get(name, {})
    print(f"# {name} — prescriptions from cycle {cycle}")
    print(f"#   {len(mine)} failing leg(s) of the {sum(len(m['legs']) for m in matrices(cycle))}"
          f" judged; {len(all_bodies)} bodies on this cycle")
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
    return 0


def print_all(g: dict, cycle: str, width: int) -> int:
    acts = actions(g)
    total = len(bodies(cycle))
    print(f"# every action, ranked by bodies failing now — cycle {cycle}, {total} bodies")
    print(f"# {len(acts)} actions over {len({a['leg'] for a in acts})} legs\n")
    head = f"{'bodies':>6}  {'leg':<13}  {'outcome':<36}  {'effort':<8}  {'cost':<8}  action"
    print(head)
    print("-" * len(head))
    for a in acts:
        n = a["value"]["bodies_failing_now"]
        pub = "" if a["applies_to_publisher"] else "  [not a publisher action]"
        print(f"{n:>6}  {a['leg']:<13}  {a['outcome']:<36}  "
              f"{band(a, 'effort'):<8}  {band(a, 'cost'):<8}  {a['title']}{pub}")
    return 0


def print_pending(g: dict, width: int) -> int:
    acts = actions(g)
    rows = [(a["id"], a["leg"], a["outcome"]) for a in acts
            if a["effort_source"] == PENDING or a["cost_source"] == PENDING]
    print(f"# {sum(1 for a in acts for b in ('effort', 'cost') if a[f'{b}_source'] == PENDING)}"
          f" band(s) on {len(rows)} action(s) have no source on disk.")
    print("# The band is left EMPTY rather than guessed; the operator is the value input.\n")
    print(f"{'action':<62}  {'leg':<13}  effort  cost")
    print("-" * 96)
    for aid, leg, _ in rows:
        a = next(x for x in acts if x["id"] == aid)
        print(f"{aid:<62}  {leg:<13}  {band(a, 'effort'):<6}  {band(a, 'cost')}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g1 = ap.add_mutually_exclusive_group(required=True)
    g1.add_argument("--body", metavar="NAME", help="one body on the cycle of record")
    g1.add_argument("--all", action="store_true", help="every action, ranked by value")
    g1.add_argument("--pending", action="store_true", help="the bands with no source on disk")
    ap.add_argument("--width", type=int, default=96)
    a = ap.parse_args(argv)
    g, cycle = load_record(), snapshot_cycle()
    if a.body:
        return print_body(a.body, g, cycle, a.width)
    if a.all:
        return print_all(g, cycle, a.width)
    return print_pending(g, a.width)


if __name__ == "__main__":
    raise SystemExit(main())
