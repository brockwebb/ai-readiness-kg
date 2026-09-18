#!/usr/bin/env python3
"""What the report's snapshot cycle's SUCCESSOR says, and whether it moves a published number.

**Zero model spend. No network. Nothing is written outside a temporary directory.**

Task `cc_tasks/2026-09-14_standing_guards.md` decisions 2 and 3, implementing
`docs/design/2026-09-14_DN-004_report_snapshot_policy.md` decisions 2 and 3, under DN-003 and
DD-065.

The situation this exists for: `docs/reports/publication.yaml` names `scan_2026-09-10_rj2` as
the cycle the published report is a view of, and since 2026-09-14 the event log carries
`scan_2026-09-10_rj3`, a later judgement of the same evidence, with a `SUPERSEDES` edge from
every one of its 739 Findings to the snapshot's. DN-004 decision 1 says a successor that moves
no published number does not force a republication — otherwise every sentence-level rule
correction becomes a publication event, and the project learns to leave corrections
unpublished. Two things follow, and both are here:

* **decision 2** — when the report does not re-snapshot, it SAYS SO, from the graph. One
  generated line in the version block, and the same fields in `docs/data/results_tagged.json`.
  `supersession_line` is the sentence; `successor_info` is the query behind it.
* **decision 3** — the build REFUSES when the successor moves a published number. `moved` is
  that comparison: the successor's matrices are built into a temporary tree and compared, and
  every tagged Result carrying the snapshot's suffix is recomputed under the successor and
  compared by value.

**A number this comparison cannot answer for is a refusal, not a pass.** `uncovered` names
every tagged Result carrying the snapshot's cycle suffix that no recomputation here covers.
That closure is the whole reason the guard means anything: a comparison that silently skips
the Results it does not know how to recompute reports "nothing moved" about the subset it
happened to understand, which is the shape of a green gate that checks nothing.

    /opt/anaconda3/bin/python3 scripts/snapshot_successor.py [--snapshot CYCLE]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TASK = "cc_tasks/2026-09-14_standing_guards.md"
REPORTS = REPO / "docs" / "reports"
GENERATED = REPORTS / "generated"

#: The revision task a refusal points at. DN-004 decision 3: a refusal is the signal to
#: RE-SNAPSHOT, and re-snapshotting the report is a report-revision task under DN-002 — not
#: something the builder does on its own and not something a flag turns off.
REVISION_DOC = "docs/design/2026-09-12_DN-002_publishing_l0.md"

#: Row fields the comparison reads, per matrix kind. `finding_ids` is DELIBERATELY absent: a
#: re-judgement's Findings have different identities by construction — that is what makes it a
#: different judgement — so comparing them would report every successor as moving every cell
#: and the guard would be permanently red for the one reason that carries no information. The
#: identities are provenance; the verdicts and the counts are the published numbers.
_ROW_FIELDS = {
    "host": ("agency", "tier", "host_surface", "host_url", "candidate_surface",
             "refused_identified_client", "probes_on_host_surface"),
    "product": ("agency", "declared", "surface", "url"),
}
_ROW_KEY = {"host": "host_surface", "product": "surface"}


# --------------------------------------------------------------- decision 2: what the graph says

def successor_info(session, snapshot: str) -> dict:
    """The snapshot's successor generation, and how the two differ, in ONE query.

    `pairs` is the count of `SUPERSEDES` edges from the successor's Findings into the
    snapshot's; `verdict_moves` and `reason_only` split them by what actually changed. Both are
    read off the Finding properties the projection stores, never off a `rejudgement_diff`
    record in `state/` — a diff lists only what MOVED, so a pairing taken from one leaves every
    unchanged judgement looking current at two generations at once
    (`2026-09-14_rejudgements_on_the_log_RESULT.md` §3b).

    Returns `{}` when the snapshot has no successor, which is the ordinary state of a report
    published the same day it was measured, and is reported as such rather than as an error.
    """
    row = session.run(
        "MATCH (new:Finding)-[:SUPERSEDES]->(old:Finding {cycle: $snap}) "
        "RETURN new.cycle AS cycle, new.generation AS generation, "
        "       new.cycle_kind AS cycle_kind, count(*) AS pairs, "
        "       sum(CASE WHEN new.verdict <> old.verdict THEN 1 ELSE 0 END) AS verdict_moves, "
        "       sum(CASE WHEN new.verdict = old.verdict AND new.reason <> old.reason "
        "                THEN 1 ELSE 0 END) AS reason_only "
        "ORDER BY pairs DESC", snap=snapshot).data()
    if not row:
        return {}
    if len(row) > 1:
        # Two cycles claiming to supersede the same judgement is not a thing to average. One of
        # them is a publication defect and the build says so rather than picking the larger.
        raise SystemExit(
            f"FATAL: {snapshot} has {len(row)} successor cycles on the graph "
            f"({', '.join(sorted(r['cycle'] or '<unnamed>' for r in row))}); supersession is "
            f"one to one (DN-003 decision 3) and the report cannot name one of two")
    r = row[0]
    snap_n = session.run("MATCH (f:Finding {cycle: $c}) RETURN count(f) AS n",
                         c=snapshot).single()["n"]
    return {"snapshot": snapshot, "snapshot_findings": snap_n, "successor": r["cycle"],
            "successor_generation": r["generation"], "successor_kind": r["cycle_kind"],
            "superseded_findings": r["pairs"], "verdict_moves": r["verdict_moves"],
            "reason_only_changes": r["reason_only"]}


def supersession_line(info: dict) -> str:
    """The version block's one generated sentence about the snapshot's standing.

    DN-004 decision 2. Every numeral in it comes from `successor_info`; nothing is typed. The
    counts arrive wrapped by the caller in the same markers `build_l0_report` puts around every
    value the resolver substitutes, so the bare-numeral lint reads them as what they are — a
    number that came FROM the graph — and needs no new exemption.

    The decision reference is inside backticks for the same reason every identifier in the
    version block already is: it is an address a reader types, and `DN-004` alone would leave
    the lint staring at a bare `1` in "decision 1". The paragraph's own rule is that the
    numbers in it are addresses, not findings; the whole address goes in the ticks.
    """
    if not info:
        return ("**Standing.** No later judgement of this cycle's evidence is on the event "
                "log: the snapshot is the current judgement of record.")
    return (f"**Standing.** This snapshot has been superseded on the event log by "
            f"`{info['successor']}`, generation {_n(info['successor_generation'])} of this "
            f"cycle, which re-judged the same evidence: "
            f"{_n(info['superseded_findings'])} of this snapshot's "
            f"{_n(info['snapshot_findings'])} findings have a successor, "
            f"{_n(info['verdict_moves'])} of them move a verdict and "
            f"{_n(info['reason_only_changes'])} change only the sentence that explains one. "
            f"No number this report publishes differs under that successor, which is why the "
            f"report is not re-snapshotted on it (`DN-004 decision 1`); the build refuses if "
            f"that ever stops being true.")


#: Set by `build_l0_report` to its own value markers, so the generated counts above are masked
#: by the bare-numeral lint exactly as a resolved `{{result:...}}` value is. Left as a plain
#: passthrough here so the line is readable on its own and testable without the report builder.
_MARK = (lambda t: t)


def _n(value) -> str:
    return _MARK(str(value))


def set_value_marker(fn) -> None:
    global _MARK
    _MARK = fn


# ----------------------------------------------- decision 3: does the successor move a number

def _matrix_rows(kind: str, rows: list, legs: list) -> dict:
    out = {}
    for r in rows:
        key = r.get(_ROW_KEY[kind]) or f"{r['agency']}::not-declared"
        cells = {f"verdict:{l}": r["verdicts"].get(l) for l in legs}
        cells.update({f: r.get(f) for f in _ROW_FIELDS[kind]})
        out[key] = cells
    return out


def _cell_moves(snap_c: dict, succ_c: dict) -> list:
    """Every published matrix cell that differs, named by matrix, row and column."""
    import build_l0_matrices as M
    moves = []
    # The product columns are the UNION of the two cycles' own (`build_l0_matrices.product_legs`):
    # a successor that judged a leg the snapshot did not adds a column, and each of its cells is
    # a published number that would appear, which is a move. Reading `M.PRODUCT_LEGS` alone
    # compared only the columns both had and called a seven-column successor unchanged
    # (`cc_tasks/2026-09-18_rejudge_seven_legs.md`).
    plegs = list(dict.fromkeys(snap_c.get("product_legs", M.PRODUCT_LEGS)
                               + succ_c.get("product_legs", M.PRODUCT_LEGS)))
    for matrix, kind, legs in (("tierA", "host", snap_c["tier0"]),
                               ("tierC", "host", snap_c["tier0"]),
                               ("product", "product", plegs)):
        key = {"tierA": "tier_a", "tierC": "tier_c", "product": "product"}[matrix]
        a = _matrix_rows(kind, snap_c[key], legs)
        b = _matrix_rows(kind, succ_c[key], legs)
        for row in sorted(set(a) | set(b)):
            if row not in a or row not in b:
                moves.append({"what": "matrix row", "matrix": matrix, "row": row,
                              "snapshot": "present" if row in a else "absent",
                              "successor": "present" if row in b else "absent"})
                continue
            for col in sorted(set(a[row]) | set(b[row])):
                if a[row].get(col) != b[row].get(col):
                    moves.append({"what": "matrix cell", "matrix": matrix, "row": row,
                                  "column": col, "snapshot": a[row].get(col),
                                  "successor": b[row].get(col)})
    return moves


def _fragment_moves(snap_c: dict, succ_c: dict) -> list:
    """The three matrix fragments the report INCLUDES, byte-compared.

    These carry no cycle name and no Finding identity — they are the agency names and the
    verdicts, which is exactly the part of the matrix a reader of the report sees — so they are
    comparable as bytes and not only cell by cell. Both cycles are rendered into temporary
    trees; the published files are never read here and never written.
    """
    import build_l0_matrices as M
    moves = []
    tmp = Path(tempfile.mkdtemp(prefix="snapshot-successor-"))
    try:
        got = {}
        for label, c in (("snapshot", snap_c), ("successor", succ_c)):
            d = tmp / label
            w = M.write_matrices(c, out_dir=d, gen_dir=d / "generated")
            got[label] = {f.name: f.read_bytes() for f in w["fragments"]
                          if f.name.startswith("matrix_")}
        for name in sorted(set(got["snapshot"]) | set(got["successor"])):
            if got["snapshot"].get(name) != got["successor"].get(name):
                moves.append({"what": "rendered matrix fragment", "fragment": name,
                              "snapshot_bytes": len(got["snapshot"].get(name) or b""),
                              "successor_bytes": len(got["successor"].get(name) or b"")})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return moves


def extra_result_values(cycle: str, params: dict) -> dict:
    """The tagged Results carrying a cycle suffix that `build_l0_matrices` does not compute.

    Three, and each is recomputed by the function that REGISTERED it rather than re-derived
    here, so the comparison cannot disagree with the registrar about what the metric means.
    """
    import build_l0_matrices as M
    import register_l0_report_results as R
    p = M.payload(cycle)
    ev = M.evidence_payload(p)
    a5 = R.offroster_sitemap_fails(p, params, ev)
    return {
        # `scan_report.py` registers this off the payload's own count.
        "scan_findings": p["findings"],
        "scan_a5_fail_offroster_sitemap": len(a5["fails"]),
        # Cycle-independent by construction: it counts the measurement ARTIFACTS in state/ that
        # record all three bodies refusing, and a re-judgement adds none. Recomputed anyway
        # rather than assumed constant, because "this cannot move" is the assumption a guard is
        # for.
        "scan_refusal_consecutive_measurements": R.refusal_measurements()["measurements"],
    }


def result_values(cycle: str, params: dict | None = None) -> dict:
    """`base name -> value` for every Result of this cycle a tagged name can resolve to."""
    import build_l0_matrices as M
    from scan import load_params
    params = params or load_params()
    out = {b: v for b, v, _note in M.compute(cycle, params)["results"]}
    out.update(extra_result_values(cycle, params))
    return out


#: Result states a published report may quote. A `stale` Result is one the project has
#: WITHDRAWN — its value stands as measured and is no longer the current instrument's answer
#: (`scripts/withdraw_g1d_results.py`, DD-066) — and a report that went on quoting it would be
#: publishing a number its own instrument no longer produces. `superseded` and `rejected` are
#: the older two ways a name stops being quotable.
LIVE_RESULT_STATES = ("proposed", "verified", "published")


def tag_states(session, names) -> dict:
    """`name -> state` for every tagged Result name, from the graph."""
    rows = session.run(
        "MATCH (r:Result) WHERE r.name IN $n "
        "RETURN r.name AS name, collect(DISTINCT r.state) AS states", n=list(names)).data()
    return {r["name"]: r["states"] for r in rows}


def withdrawn_tags(session, names) -> list:
    """Tagged names whose Result is not in a state a report may quote.

    Excluded BY STATE and never by name (`2026-09-15_g1d_leaves_l0_ADDENDUM_01.md`): a list of
    withdrawn names in this module would be a second place to maintain the withdrawal, and it
    would go stale the first time a Result was withdrawn by a task that did not think to edit
    this file. The graph already knows.
    """
    states = tag_states(session, names)
    out = []
    for n in sorted(names):
        st = states.get(n)
        if st is None:
            continue                        # the resolver's own SI check reports a missing one
        if not any(x in LIVE_RESULT_STATES for x in st):
            out.append({"name": n, "states": sorted(st)})
    return out


def tagged_of_snapshot(snapshot: str) -> list:
    """The report's tagged Result names that carry the SNAPSHOT's cycle suffix.

    Read from the report's own `{{result:...}}` tags (`rederive_tagged_results.tagged_names`),
    so the set cannot disagree with the document it guards. A tagged name with any other suffix
    is a fact about a different cycle or about the frame, and a later judgement of THIS cycle
    cannot move it.
    """
    import cycle_results
    import rederive_tagged_results as rd
    suffix = "_" + cycle_results.cycle_suffix(snapshot)
    return [n for n in rd.tagged_names() if n.endswith(suffix)]


def moved(snapshot: str, successor: str, params: dict | None = None) -> dict:
    """Every published number that differs between the snapshot and its successor.

    Three comparisons, because the report publishes its numbers in three shapes: the registered
    Results it quotes by name, the matrix cells it ships as JSON and CSV, and the matrix tables
    it renders into its own prose.
    """
    import build_l0_matrices as M
    import cycle_results
    from scan import load_params
    params = params or load_params()
    snap_c, succ_c = M.compute(snapshot, params), M.compute(successor, params)

    snap_v = {b: v for b, v, _n in snap_c["results"]}
    succ_v = {b: v for b, v, _n in succ_c["results"]}
    snap_v.update(extra_result_values(snapshot, params))
    succ_v.update(extra_result_values(successor, params))

    suffix = "_" + cycle_results.cycle_suffix(snapshot)
    result_moves, covered, uncovered = [], [], []
    for name in tagged_of_snapshot(snapshot):
        base = name[: -len(suffix)]
        if base not in snap_v:
            uncovered.append(name)
            continue
        covered.append(name)
        if float(snap_v[base]) != float(succ_v.get(base, float("nan"))):
            result_moves.append({"what": "registered Result", "name": name, "base": base,
                                 "snapshot": snap_v[base], "successor": succ_v.get(base)})

    moves = result_moves + _cell_moves(snap_c, succ_c) + _fragment_moves(snap_c, succ_c)
    return {"snapshot": snapshot, "successor": successor,
            "tagged_results_on_this_cycle": len(covered) + len(uncovered),
            "recomputed_and_compared": len(covered), "uncovered": sorted(uncovered),
            "matrix_rows_compared": sum(len(snap_c[k]) for k in
                                        ("tier_a", "tier_c", "product")),
            "moves": moves, "moved": len(moves)}


def refusal_text(cmp_: dict) -> str:
    """What the build says when it refuses. It NAMES the numbers, because "something moved" is
    not actionable and the next step — a report revision under DN-002 — starts from which."""
    lines = [f"FATAL: the report's snapshot `{cmp_['snapshot']}` has a successor on the event "
             f"log, `{cmp_['successor']}`, and it MOVES {cmp_['moved']} published number(s). "
             f"No report and no PDF is written."]
    if cmp_["uncovered"]:
        lines.append(f"  {len(cmp_['uncovered'])} tagged Result(s) of this cycle could not be "
                     f"recomputed and so could not be compared: "
                     f"{', '.join(cmp_['uncovered'])}")
    for m in cmp_["moves"][:40]:
        lines.append("  " + json.dumps(m, sort_keys=True))
    if len(cmp_["moves"]) > 40:
        lines.append(f"  ... and {len(cmp_['moves']) - 40} more")
    lines.append(f"  This is the re-snapshot condition (DN-004 decision 3). The next step is a "
                 f"report-revision task under DN-002 ({REVISION_DOC}): move "
                 f"`snapshot_cycle` in docs/reports/publication.yaml to "
                 f"`{cmp_['successor']}`, rebuild the matrices and register that cycle's "
                 f"Results. It is not fixed by rebuilding.")
    return "\n".join(lines)


def refuse_if_moved(standing: dict) -> str | None:
    """The refusal text when this snapshot may not be published as it stands, else `None`.

    ONE function, called by both builders, because the report's markdown and the site's data
    file publish the same numbers and a condition that stops one and not the other would ship
    a `results_tagged.json` disagreeing with the report beside it.

    `uncovered` refuses as loudly as `moved` does. A tagged Result of this cycle that nothing
    here knows how to recompute is a number the comparison cannot speak for, and "no move
    detected among the ones I understood" is the shape of a gate that passes by not looking.
    """
    cmp_ = standing.get("comparison")
    if cmp_ and (cmp_["moved"] or cmp_["uncovered"]):
        return refusal_text(cmp_)
    return None


def check(snapshot: str) -> dict:
    """`successor_info` and `moved` together: what the build needs, in one call."""
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            info = successor_info(s, snapshot)
    finally:
        driver.close()
    if not info:
        return {"info": {}, "comparison": None}
    return {"info": info, "comparison": moved(snapshot, info["successor"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", default=None,
                    help="the cycle to check; defaults to publication.yaml's snapshot_cycle")
    a = ap.parse_args(argv)
    import yaml
    snapshot = a.snapshot or yaml.safe_load(
        (REPORTS / "publication.yaml").read_text(encoding="utf-8"))["snapshot_cycle"]
    out = check(snapshot)
    print(json.dumps(out, indent=1, default=str))
    print()
    print(supersession_line(out["info"]))
    if out["comparison"] and (out["comparison"]["moved"] or out["comparison"]["uncovered"]):
        print(); print(refusal_text(out["comparison"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
