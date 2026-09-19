#!/usr/bin/env python3
"""The scoring model as a query. **Zero spend, no network, reads only, publishes nothing.**

`cc_tasks/2026-09-18_scoring_model.md`, under DN-005 §2.1 (b) and §4 item 5: *there is no
quantitative score and no qualitative rubric.* This is the quantitative half, as a query over
two sources and no third — the framework of record (`framework/ai_readiness_framework.json`)
and the published matrices of the cycle of record (`docs/reports/publication.yaml:
snapshot_cycle`). No number is authored; every score re-derives from the cells printed beside
it. It reads Neo4j for nothing, for the reason `scripts/prescriptions.py` gives.

    scripts/score.py                  the body grid: additive score with coverage, gating view
    scripts/score.py --body NCHS      one body: its cells, its score, its prescription join
    scripts/score.py --top 10         actions ranked by what they would raise, cheapest first
    scripts/score.py --sensitivity    rank changes under the prior cycle and each criterion dropped
    scripts/score.py --json           everything above, machine-readable
    scripts/score.py --explain        the model, step by step (docs/design/scoring_model.md)
    scripts/score.py --check          exit 1 unless docs/design/scoring_model.md is --explain

**Prior art.** The OECD/JRC *Handbook on Constructing Composite Indicators: Methodology and
User Guide* (OECD, 2008) — not on disk; cited by reference. Its ten steps are the outline of
`--explain`, and its two rules govern here: equal weights where no theoretical or empirical
basis for others exists, and every step documented so the composite can be re-derived. Beside
it: the Open Data Barometer and ODIN (per-element grids beside the total, equal weights),
WCAG conformance levels (a gating shape rather than an additive one) and OpenSSF Scorecard
(additive, with published per-check weights). None of these is a document in `corpus/`.

**The model, in one paragraph.** The scored legs are the Tier M `harness_leg` indicators' legs
(read from the record's `measurement_basis`, so a new rule enters by being tagged) that the
cycle of record's matrices judge, minus the candidate legs (DD-054: reported, never counted).
A body's score at a leg is its pass share over its judged rows; `error`, `not_applicable` and
any other verdict are out of the denominator and counted separately. Indicator = mean of its
legs; construct = mean of its measured indicators; criterion = mean of its measured
constructs; body = mean of the criteria with at least one measured construct. Every score is
printed with its coverage — measured of total at its level — or it is not printed.

**The second half** (`cc_tasks/2026-09-18_scoring_levels.md`). Beside the hierarchical score, a
FLAT one: every judged leg weighs 1/n. Neither scheme has a basis over the other, so both are
printed with the rank under each. Beside both, the READINESS LEVEL: a cumulative ladder over the
scored criteria in the framework's own order, TRL's shape (JRC, *AI Watch: Revisiting
Technology Readiness Levels*, §3 and Appendix A — on disk): a body holds level k when every
scored leg of every criterion up to the k-th passes outright, and a level is never an average.
The level names are the record's criterion names and the rubric sentence for each level is
generated from the record and the prescription layer; nothing in either is hand-written.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import prescriptions as P  # noqa: E402  the record, the cycle, the matrices: one reader of each

DOC = REPO / "docs" / "design" / "scoring_model.md"
REPORTS = REPO / "docs" / "reports"
TASK = "cc_tasks/2026-09-18_scoring_model.md"
TASK_LEVELS = "cc_tasks/2026-09-18_scoring_levels.md"

#: Decision 2. Printed on every output of this script, verbatim; a test asserts it.
COVERAGE_SENTENCE = ("Scores cover only what the harness measures; "
                     "Tier O and D indicators are not scored.")

#: The verdicts that enter a denominator. Everything else is excluded and counted by name.
JUDGED = ("pass", "fail")

#: The basis value that makes an indicator's leg a candidate for scoring (decision 1).
HARNESS_BASIS = "harness_leg"


# ------------------------------------------------------------------ inputs

def snapshot_cycle() -> str:
    return P.snapshot_cycle()


def matrices(cycle: str) -> list:
    """Both published matrices of a cycle, or a stop naming the missing file."""
    suffix = cycle.replace("scan_", "")
    for kind in ("tierA", "product"):
        path = REPORTS / f"scan_matrix_{kind}_{suffix}.json"
        if not path.exists():
            raise SystemExit(f"FATAL: {path.relative_to(REPO)} does not exist; cycle {cycle!r} "
                             f"has no published matrix to score")
    return P.matrices(cycle)


def _rows(m: dict) -> list:
    # Product rows are DECLARED flagship surfaces only; an undeclared row is neither a fail nor
    # an omission (the product matrix's own note), so it is not a row of the body.
    return [r for r in m["rows"] if m["_kind"] != "product" or r.get("declared")]


def bodies_on(cycle: str) -> list:
    return P.bodies(cycle)


def cells(cycle: str) -> dict:
    """`{body: {leg: {verdict: n}}}` over both matrices of the cycle."""
    out: dict = {}
    for m in matrices(cycle):
        for r in _rows(m):
            for leg in m["legs"]:
                v = r["verdicts"].get(leg)
                if v is None:
                    continue
                c = out.setdefault(r["agency"], {}).setdefault(leg, {})
                c[v] = c.get(v, 0) + 1
    return out


def cycle_legs(cycle: str) -> tuple:
    legs, withdrawn = [], {}
    for m in matrices(cycle):
        legs += [l for l in m["legs"] if l not in legs]
        for w in m.get("legs_withdrawn", []):
            withdrawn[w["leg"]] = w
    return tuple(legs), withdrawn


def prior_cycle(cycle: str) -> str | None:
    """The newest cycle with a published tier-A matrix that sorts before the cycle of record
    and is not a re-judgement of the same measurement. `None` if there is none."""
    base = cycle.replace("scan_", "").split("_rj")[0]
    names = sorted(p.name[len("scan_matrix_tierA_"):-len(".json")]
                   for p in REPORTS.glob("scan_matrix_tierA_*.json"))
    older = [n for n in names if n.split("_rj")[0] < base]
    return f"scan_{older[-1]}" if older else None


# ------------------------------------------------------------------ the structure

def structure(g: dict, cycle: str) -> list:
    """One row per `harness_leg` indicator leg: where it sits in the framework, and whether it
    is scored on this cycle and, if not, why. Legs come from `rules.CURRENT`, and the leg's
    indicator from its rule id (`rules.parse_rule_id`), never from a table kept here."""
    from scan import rules
    nodes = {n["id"]: n for n in g["nodes"]}
    parent: dict = {}
    for e in g["edges"]:
        if e["type"] == "DECOMPOSES_INTO":
            parent.setdefault(e["to"], []).append(e["from"])
    harness = {n["properties"]["code"]: n["id"] for n in g["nodes"]
               if "AssessmentIndicator" in n["labels"]
               and n["properties"].get("measurement_basis") == HARNESS_BASIS}
    by_code: dict = {}
    for leg, rule_id in rules.CURRENT.items():
        by_code.setdefault(rules.parse_rule_id(rule_id)["indicator_code"], []).append(leg)
    legs_on, withdrawn = cycle_legs(cycle)
    publisher = {}
    for a in P.actions(g):
        publisher.setdefault(a["leg"], set()).add(a["applies_to_publisher"])
    out = []
    for code, ind in sorted(harness.items()):
        if code not in by_code:
            raise SystemExit(f"FATAL: {ind} is tagged {HARNESS_BASIS} but no rule in "
                             f"rules.CURRENT measures {code}")
        cons = parent.get(ind, [])
        if len(cons) != 1:
            raise SystemExit(f"FATAL: {ind} decomposes from {len(cons)} constructs; the "
                             f"hierarchy needs exactly one")
        crits = parent.get(cons[0], [])
        if len(crits) != 1:
            raise SystemExit(f"FATAL: {cons[0]} decomposes from {len(crits)} criteria")
        crit = nodes[crits[0]]["properties"]["code"]
        for leg in by_code[code]:
            if leg in rules.CANDIDATE_LEGS:
                scored, why = False, ("candidate rule (DD-054): its Findings are reported and "
                                      "enter no framework numerator")
            elif leg in withdrawn:
                w = withdrawn[leg]
                scored, why = False, (f"withdrawn by {w['decision']}, effective "
                                      f"{w['effective']}; not a leg of the cycle of record")
            elif leg not in legs_on:
                if publisher.get(leg) == {False}:
                    why = ("not a leg of any published matrix: it judges this instrument's own "
                           "controls, not a publisher (its actions carry "
                           "applies_to_publisher: false)")
                else:
                    why = "not a leg of any published matrix of the cycle of record"
                scored = False
            else:
                scored, why = True, ""
            out.append({"leg": leg, "indicator_id": ind, "code": code,
                        "construct_id": cons[0],
                        "construct": nodes[cons[0]]["properties"].get("name", cons[0]),
                        "criterion": crit, "scored": scored, "reason": why})
    return out


def framework_totals(g: dict) -> dict:
    """The denominators, on the record's own DD-054 split: counts of what the FRAMEWORK holds
    exclude candidate indicators and their constructs (`counts_basis` on the record), so a
    coverage line here agrees with `counts` there. The candidate set is the single writer's."""
    from framework_writeback import _candidate_ids
    cand = _candidate_ids(g)
    adopted = [n for n in g["nodes"] if n["id"] not in cand]
    crits = sorted(n["properties"]["code"] for n in adopted
                   if "AssessmentCriterion" in n["labels"])
    return {
        "indicators": sum("AssessmentIndicator" in n["labels"] for n in adopted),
        "constructs": sum("AssessmentConstruct" in n["labels"] for n in adopted),
        "criteria": crits,
        "harness_leg_indicators": sum(
            "AssessmentIndicator" in n["labels"]
            and n["properties"].get("measurement_basis") == HARNESS_BASIS for n in adopted),
        "candidate_indicators": sum("AssessmentIndicator" in n["labels"]
                                    for n in g["nodes"] if n["id"] in cand),
    }


# ------------------------------------------------------------------ the model

def _mean(xs: list) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def score_body(body_cells: dict, struct: list, criteria: list, drop: tuple = (),
               totals: dict | None = None) -> dict:
    """Decision 3: equal weights, hierarchical, additive. Pure; the tests drive it with a
    synthetic body."""
    scored = [l for l in struct if l["scored"] and l["criterion"] not in drop]
    excluded: Counter = Counter()
    legs, inds, cons, crits = {}, {}, {}, {}
    for l in scored:
        c = body_cells.get(l["leg"], {})
        judged = sum(c.get(v, 0) for v in JUDGED)
        for v, n in c.items():
            if v not in JUDGED:
                excluded[v] += n
        legs[l["leg"]] = {"pass": c.get("pass", 0), "judged": judged,
                          "score": c.get("pass", 0) / judged if judged else None}
        inds.setdefault(l["indicator_id"], []).append(legs[l["leg"]]["score"])
    ind_of = {l["indicator_id"]: l for l in scored}
    indicators = {i: {"score": _mean(v)} for i, v in inds.items()}
    for i, v in indicators.items():
        cons.setdefault(ind_of[i]["construct_id"], []).append(v["score"])
    con_of = {l["construct_id"]: l for l in scored}
    constructs = {c: {"score": _mean(v), "name": con_of[c]["construct"]}
                  for c, v in cons.items()}
    for c, v in constructs.items():
        crits.setdefault(con_of[c]["criterion"], []).append(v["score"])
    criteria_out = {k: {"score": _mean(crits.get(k, []))} for k in criteria}
    body = _mean([criteria_out[k]["score"] for k in criteria if k not in drop])
    t = totals or {}
    measured_ind = sum(v["score"] is not None for v in indicators.values())
    coverage = {
        "legs": {"measured": sum(v["score"] is not None for v in legs.values()),
                 "total": len(scored)},
        "indicators": {"measured": measured_ind,
                       "total": t.get("indicators", len({l["indicator_id"] for l in struct}))},
        "constructs": {"measured": sum(v["score"] is not None for v in constructs.values()),
                       "total": t.get("constructs", len({l["construct_id"] for l in struct}))},
        "criteria": {"measured": sum(criteria_out[k]["score"] is not None for k in criteria
                                     if k not in drop),
                     "total": len([k for k in criteria if k not in drop])},
    }
    # Levels decision 1: the flat scheme, every judged leg at 1/n. Same legs, same cells, same
    # exclusions; only the aggregation differs.
    flat = _mean([v["score"] for v in legs.values()])
    return {"score": body, "flat": flat, "legs": legs, "indicators": indicators,
            "constructs": constructs, "criteria": criteria_out, "excluded": dict(excluded),
            "coverage": coverage}


def gating(s: dict, struct: list) -> dict:
    """Decision 4, WCAG's shape beside the additive one: how many legs pass outright, and the
    first construct (framework order) whose measured score is zero."""
    order = []
    for l in struct:
        if l["construct_id"] not in order:
            order.append(l["construct_id"])
    name = {l["construct_id"]: l["construct"] for l in struct}
    zero = [name[c] for c in order if c in s["constructs"]
            and s["constructs"][c]["score"] == 0]
    return {"legs_passed_outright": sum(v["score"] == 1 for v in s["legs"].values()),
            "legs_judged": sum(v["score"] is not None for v in s["legs"].values()),
            "zero_constructs": zero, "first_zero_construct": zero[0] if zero else None}


# ------------------------------------------------------------------ the ladder (levels decision 3)

#: What a leg is, for one body, on the ladder. `clear`: judged rows and every one passed, or
#: every row `not_applicable` (WCAG's reading: a requirement with nothing to apply to is
#: satisfied); `fail`: at least one row failed; `unobservable`: no fail, and an `error` (or any
#: verdict outside pass / fail / not_applicable) or no row at all. A fail is an observation and
#: decides; an error is an absence of one and can only cap.
LEG_STATES = ("clear", "fail", "unobservable")


def leg_state(c: dict) -> str:
    if c.get("fail", 0):
        return "fail"
    if not c or any(n and v not in ("pass", "not_applicable") for v, n in c.items()):
        return "unobservable"
    return "clear"


def ladder_order(struct: list, criteria: list) -> list:
    """The scored criteria in the framework's own order (the record's criterion codes, which
    `framework_totals` sorts). The ladder authors no order of its own."""
    scored = {l["criterion"] for l in struct if l["scored"]}
    return [k for k in criteria if k in scored]


def ladder(body_cells: dict, struct: list, order: list) -> dict:
    """A body is at level k when every scored leg of the first k criteria in `order` is
    `clear`. The walk stops at the first criterion that is not: a `fail` there places the body
    one level below it; no fail but an unobservable leg places it one level below as well, and
    says the next level could not be observed, so it is never rounded up."""
    per = {}
    for k in order:
        states = [leg_state(body_cells.get(l["leg"], {})) for l in struct
                  if l["scored"] and l["criterion"] == k]
        per[k] = {"legs": len(states), **{s: states.count(s) for s in LEG_STATES}}
    level, unobs = len(order), None
    for i, k in enumerate(order, start=1):
        if per[k]["clear"] == per[k]["legs"]:
            continue
        level, unobs = i - 1, (None if per[k]["fail"] else i)
        break
    return {"level": level, "unobservable_at": unobs, "per_criterion": per,
            "label": f"{level}" + (f" (unobservable at {unobs})" if unobs else "")}


def rubric(struct: list, order: list, names: dict, acts: list, efforts: tuple) -> list:
    """Levels decision 4. One entry per level, its sentence generated from the record: which
    legs a body must hold outright, and the cheapest action per leg (prescription layer) that
    closes the gap for a body one level down."""
    by_leg: dict = {}
    for a in sorted(acts, key=lambda a: (efforts.index(a["effort_band"]), a["title"])):
        by_leg.setdefault(a["leg"], []).append(a)
    out = [{"level": 0, "criterion": None, "name": "no scored criterion clear", "legs": [],
            "sentence": (f"Level 0: every body holds it. A body stays here while any scored leg "
                         f"of criterion {order[0]} fails; one whose criterion {order[0]} "
                         f"legs show no fail but an error or no row is reported as "
                         f"'0 (unobservable at 1)'.") if order else "Level 0 only."}]
    for i, k in enumerate(order, start=1):
        legs = [l["leg"] for l in struct if l["scored"] and l["criterion"] == k]
        below = ", ".join(order[:i - 1])
        n_act = sum(len(by_leg.get(l, [])) for l in legs)
        cheapest = "; ".join(
            f"{l}: \u201c{by_leg[l][0]['title']}\u201d ({by_leg[l][0]['effort_band']})"
            if l in by_leg else f"{l}: no publisher action on record" for l in legs)
        out.append({
            "level": i, "criterion": k, "name": names[k], "legs": legs,
            "sentence": (f"Level {i}, {names[k]} (criterion {k}): a body holds it when "
                         + (f"it holds level {i - 1} (criteri{'a' if i > 2 else 'on'} "
                            f"{below}) and " if i > 1 else "")
                         + (f"all {len(legs)} scored legs of criterion {k} "
                            f"({', '.join(legs)}) pass" if len(legs) != 1 else
                            f"the one scored leg of criterion {k} ({legs[0]}) passes")
                         + f" outright with no error row; a body at level {i - 1} closes the "
                           f"gap through the "
                           f"{n_act} publisher action{'s' if n_act != 1 else ''} on "
                           f"{'those legs' if len(legs) != 1 else 'that leg'}, the cheapest "
                           f"per leg being {cheapest}.")})
    return out


def flip_delta(body_cells: dict, leg: str, struct: list, criteria: list) -> float:
    """Decision 5: the score change if every `fail` row of this body on this leg passed."""
    before = score_body(body_cells, struct, criteria)["score"]
    flipped = {k: dict(v) for k, v in body_cells.items()}
    c = flipped.get(leg, {})
    c["pass"] = c.get("pass", 0) + c.pop("fail", 0)
    flipped[leg] = c
    after = score_body(flipped, struct, criteria)["score"]
    return (after or 0.0) - (before or 0.0)


def ranks(scores: dict) -> dict:
    """Standard competition ranking ("1224"), higher score first; unscored bodies unranked."""
    s = {k: v for k, v in scores.items() if v is not None}
    return {k: 1 + sum(1 for w in s.values() if w > v) for k, v in s.items()}


def concentration(bodies: dict, struct: list, criteria: list) -> dict:
    """`cc_tasks/2026-09-19_resnapshot_rj4.md` decision 4: for each ranked body, the ONE leg
    whose verdicts, reversed, would move its rank furthest, and the sentence that says so.

    The Handbook's step 7 reads robustness by excluding or re-weighting one component at a time
    (OECD/JRC 2008; `sensitivity` above does it per criterion). This is the same probe one level
    down and one body at a time, because a rank is quoted about ONE body. On
    `scan_2026-09-10_rj4` DRSMSU is first on a single G4 pass: G4 is criterion G's only harness
    leg, so under the hierarchical scheme that one verdict is a fifth of the score. A rank that
    rests on one verdict is the rank a reader quotes, and the reader should be told.

    **Reversal**, not deletion: the body's `pass` and `fail` rows on the leg swap, every other
    body stays as it is, and the body is re-ranked against them. That asks the question in both
    directions at once (a rank resting on a pass drops, a rank held down by a fail rises) and
    it never changes the denominator, which a deletion would: a move that is only a change of
    what was measured is not the same finding (decision 2 of the scoring task). Ties go to the
    leg first in the framework's order, so the choice is deterministic and re-derivable.
    """
    scores = {b: v["score"] for b, v in bodies.items()}
    base = ranks(scores)
    order = [l["leg"] for l in struct if l["scored"]]
    out = {}
    for b, v in bodies.items():
        if base.get(b) is None:
            out[b] = None
            continue
        best = None
        for leg in order:
            x = v["legs"].get(leg) or {}
            if not x.get("judged"):
                continue
            cells = {k: dict(c) for k, c in v["cells"].items()}
            c = cells.get(leg, {})
            c["pass"], c["fail"] = c.get("fail", 0), c.get("pass", 0)
            cells[leg] = c
            after = ranks({**scores, b: score_body(cells, struct, criteria)["score"]})[b]
            if best is None or abs(after - base[b]) > abs(best["rank_if_reversed"] - base[b]):
                best = {"leg": leg, "pass": x["pass"], "judged": x["judged"],
                        "rank": base[b], "rank_if_reversed": after}
        best["of"] = len(base)
        best["sentence"] = concentration_sentence(b, best)
        out[b] = best
    return out


def concentration_sentence(body: str, c: dict) -> str:
    """The one sentence every rank is printed with. Every number in it is a field beside it."""
    head = f"{body} ranks {c['rank']} of {c['of']} (hierarchical)"
    move = c["rank_if_reversed"] - c["rank"]
    counts = (f"{c['pass']} pass of {c['judged']} judged row"
              f"{'' if c['judged'] == 1 else 's'} on {c['leg']}")
    if move == 0:
        return (f"{head}; no single leg's verdicts, reversed, would change it (the nearest is "
                f"{c['leg']}).")
    if move > 0:
        what = "on one pass" if c["pass"] == 1 else f"most on {c['leg']}"
        return (f"{head}, and it rests {what}: {counts}; were that leg's verdicts reversed it "
                f"would rank {c['rank_if_reversed']}.")
    return (f"{head}, and the leg that would move it most is {c['leg']}: {counts}; were that "
            f"leg's verdicts reversed it would rank {c['rank_if_reversed']}.")


# ------------------------------------------------------------------ the query

def effort_order() -> tuple:
    from tag_prescriptions import EFFORT_BANDS  # the one declaration of the band order
    return EFFORT_BANDS


def criterion_names(g: dict) -> dict:
    return {n["properties"]["code"]: n["properties"]["name"] for n in g["nodes"]
            if "AssessmentCriterion" in n["labels"]}


def compute(cycle: str | None = None, prior: str | None = None) -> dict:
    g = P.load_record()
    cycle = cycle or snapshot_cycle()
    tot = framework_totals(g)
    struct = structure(g, cycle)
    crit = tot["criteria"]
    all_cells = cells(cycle)
    names = bodies_on(cycle)
    efforts = effort_order()
    scored_legs = {l["leg"] for l in struct if l["scored"]}
    acts = [a for a in P.actions(g) if a["applies_to_publisher"] and a["leg"] in scored_legs]
    order = ladder_order(struct, crit)

    bodies = {}
    for b in names:
        bc = all_cells.get(b, {})
        s = score_body(bc, struct, crit, totals=tot)
        s["cells"] = bc
        s["gating"] = gating(s, struct)
        s["ladder"] = ladder(bc, struct, order)
        pres = []
        for a in acts:
            if bc.get(a["leg"], {}).get("fail", 0):
                pres.append({"action": a["id"], "title": a["title"], "leg": a["leg"],
                             "outcome": a["outcome"], "effort": a["effort_band"],
                             "cost": a["cost_band"],
                             "delta": flip_delta(bc, a["leg"], struct, crit)})
        pres.sort(key=lambda p: (efforts.index(p["effort"]), -p["delta"], p["leg"], p["action"]))
        s["prescriptions"] = pres
        bodies[b] = s
    base_rank = ranks({b: v["score"] for b, v in bodies.items()})
    flat_rank = ranks({b: v["flat"] for b, v in bodies.items()})
    for b in bodies:
        bodies[b]["rank"] = base_rank.get(b)
        bodies[b]["flat_rank"] = flat_rank.get(b)
    for b, c in concentration(bodies, struct, crit).items():
        bodies[b]["concentration"] = c

    overall = []
    n_scored = sum(v["score"] is not None for v in bodies.values())
    for a in acts:
        ds = [p["delta"] for v in bodies.values() for p in v["prescriptions"]
              if p["action"] == a["id"]]
        if ds:
            overall.append({"action": a["id"], "title": a["title"], "leg": a["leg"],
                            "outcome": a["outcome"], "effort": a["effort_band"],
                            "cost": a["cost_band"], "bodies_raised": len(ds),
                            "mean_score_raise": sum(ds) / n_scored})
    overall.sort(key=lambda p: (efforts.index(p["effort"]), -p["mean_score_raise"],
                                p["leg"], p["action"]))

    candidate_legs = {l["leg"] for l in struct if "DD-054" in l["reason"]}
    measured_legs = {l for v in bodies.values() for l, x in v["legs"].items()
                     if x["score"] is not None}
    measured_inds = {l["indicator_id"] for l in struct if l["leg"] in measured_legs}
    coverage = {
        "bodies": {"measured": n_scored, "total": len(names)},
        "legs_on_cycle": {"measured": len(scored_legs),
                          "total": len([l for l in struct if l["leg"] not in candidate_legs])},
        "indicators": {"measured": len(measured_inds), "total": tot["indicators"]},
        "harness_leg_indicators": {"measured": len(measured_inds),
                                   "total": tot["harness_leg_indicators"]},
        "criteria": {"measured": len({l["criterion"] for l in struct
                                      if l["leg"] in measured_legs}),
                     "total": len(crit)},
    }
    return {"cycle": {"name": cycle, "n_bodies": len(names),
                      "matrices": [m["_path"] for m in matrices(cycle)]},
            "framework": tot, "structure": struct, "coverage": coverage,
            "bodies": bodies, "overall": overall,
            "candidates": [{"id": n["id"], "promotion": n["properties"].get(
                "candidate_promotion", "(no promotion field on the record)")}
                for n in g["nodes"] if n["properties"].get("status") == "candidate"
                and "AssessmentIndicator" in n["labels"]],
            "ladder": {"order": order,
                       "levels": rubric(struct, order, criterion_names(g), acts, efforts)},
            "sensitivity": sensitivity(struct, crit, bodies, prior or prior_cycle(cycle)),
            "coverage_sentence": COVERAGE_SENTENCE}


def sensitivity(struct: list, crit: list, bodies: dict, prior: str | None) -> dict:
    """Decision 6, the Handbook's step 7 without a distributional claim: the rank of every body
    under each alternative, and the Handbook's summary statistic, the mean absolute shift in
    rank, over the bodies ranked under both."""
    base = {b: v["rank"] for b, v in bodies.items()}
    variants = {}
    if prior:
        pc = cells(prior)
        # The STRUCTURE is the cycle of record's, so the variant moves the data and not the
        # model: a leg the prior cycle judged and the cycle of record does not (a withdrawn
        # leg) is not scored, and a leg the prior cycle lacks is simply unmeasured there.
        ps = {b: score_body(pc.get(b, {}), struct, crit) for b in bodies}
        variants[f"prior cycle ({prior})"] = {b: v["score"] for b, v in ps.items()}
        # Denominator first (decision 2): a rank that moved because the body was measured on
        # fewer legs is not the same finding as one that moved on the same legs.
        prior_legs = {b: v["coverage"]["legs"]["measured"] for b, v in ps.items()}
    # Levels decision 1: the flat scheme is an alternative weighting of the same cells.
    variants["flat (equal leg weights)"] = {b: v["flat"] for b, v in bodies.items()}
    measured = sorted({l["criterion"] for l in struct if l["scored"]})
    for k in measured:
        variants[f"drop criterion {k}"] = {
            b: score_body(v["cells"], struct, crit, drop=(k,))["score"]
            for b, v in bodies.items()}
    out = {"prior_cycle": prior, "variants": {}}
    if prior:
        out["prior_cycle_coverage_changed"] = {
            b: {"prior": prior_legs[b], "cycle_of_record": v["coverage"]["legs"]["measured"],
                "total": v["coverage"]["legs"]["total"]}
            for b, v in bodies.items() if prior_legs[b] != v["coverage"]["legs"]["measured"]}
    for name, sc in variants.items():
        r = ranks(sc)
        both = [b for b in base if base[b] is not None and b in r]
        out["variants"][name] = {
            "scores": sc, "ranks": r,
            "mean_abs_rank_shift": (sum(abs(r[b] - base[b]) for b in both) / len(both)
                                    if both else None),
            "bodies_moved": sum(r[b] != base[b] for b in both),
            "bodies_compared": len(both)}
    return out


# ------------------------------------------------------------------ printing

def _f(x) -> str:
    return "  —  " if x is None else f"{x:.3f}"


def _cov(c: dict) -> str:
    return f"{c['measured']}/{c['total']}"


def header(r: dict) -> list:
    c = r["coverage"]
    return [f"# scoring model — cycle {r['cycle']['name']}, {r['cycle']['n_bodies']} bodies",
            f"# {COVERAGE_SENTENCE}",
            f"# coverage: bodies scored {_cov(c['bodies'])}; legs scored "
            f"{_cov(c['legs_on_cycle'])} adopted harness legs; indicators measured "
            f"{_cov(c['indicators'])} in the framework ({_cov(c['harness_leg_indicators'])} "
            f"harness_leg); criteria measured {_cov(c['criteria'])}",
            "# two equal-weight schemes, no basis to prefer either: hierarchical (leg to "
            "criterion, OECD/JRC 2008 default) and flat (1/n per judged leg); readiness level "
            "is a cumulative ladder, never an average; `scripts/score.py --explain` for every step"]


def print_grid(r: dict) -> None:
    print("\n".join(header(r)) + "\n")
    crit = [k for k in r["framework"]["criteria"]
            if any(v["criteria"][k]["score"] is not None for v in r["bodies"].values())]
    order_l = r["ladder"]["order"]
    head = (f"{'rank':>4}  {'body':<11} {'score':>6}  {'flat':>6} {'frank':>5}  "
            f"{'level':<22}" + "  ".join(f"{k:>5}" for k in crit)
            + f"  {'legs':>6} {'ind':>6} {'con':>6} {'crit':>5} {'err':>4}  "
              f"{'outright':>8}  {'clear/legs by criterion':<24}  first construct with zero "
              f"passes")
    print(head)
    print("-" * len(head))
    order = sorted(r["bodies"].items(),
                   key=lambda kv: (kv[1]["rank"] is None, kv[1]["rank"] or 0, kv[0]))
    for b, v in order:
        cv, gt = v["coverage"], v["gating"]
        lad = v["ladder"]
        per = " ".join(f"{k}{lad['per_criterion'][k]['clear']}/{lad['per_criterion'][k]['legs']}"
                       for k in order_l)
        print(f"{v['rank'] or '-':>4}  {b:<11} {_f(v['score']):>6}  {_f(v['flat']):>6} "
              f"{v['flat_rank'] or '-':>5}  {lad['label']:<22}"
              + "  ".join(f"{_f(v['criteria'][k]['score']):>5}" for k in crit)
              + f"  {_cov(cv['legs']):>6} {_cov(cv['indicators']):>6} "
                f"{_cov(cv['constructs']):>6} {_cov(cv['criteria']):>5} "
                f"{sum(v['excluded'].values()):>4}  "
                f"{gt['legs_passed_outright']:>3}/{gt['legs_judged']:<4}  {per:<24}  "
                f"{gt['first_zero_construct'] or '(none)'}"
                + (f"  [+{len(gt['zero_constructs']) - 1} more]"
                   if len(gt['zero_constructs']) > 1 else ""))
    print("\nscore/rank: hierarchical; flat/frank: every judged leg at 1/n. level: the "
          "ladder over criteria " + " < ".join(order_l) + " (`--explain`); 'unobservable at k' "
          "means no leg of the k-th failed but one errored or had no row, so the body is placed "
          "below k and never rounded up. legs/ind/con/crit: measured of total at that level for "
          "the body; err: rows excluded from every denominator (error, not_applicable); "
          "outright: legs whose every judged row passed, of legs judged; clear/legs: legs that "
          "passed outright with no error row, per criterion — the counts the level is read "
          "from.")
    print_concentration(r)


def print_concentration(r: dict) -> None:
    """Decision 4 of `cc_tasks/2026-09-19_resnapshot_rj4.md`: wherever a rank is printed, the
    leg it rests on is printed with it, in rank order."""
    print("\nconcentration — the one leg whose verdicts, reversed, would move each rank most:")
    for b, v in sorted(r["bodies"].items(),
                       key=lambda kv: (kv[1]["rank"] is None, kv[1]["rank"] or 0, kv[0])):
        if v["concentration"]:
            print(f"   {v['concentration']['sentence']}")


def print_body(r: dict, name: str) -> int:
    if name not in r["bodies"]:
        print(f"'{name}' is not a body on cycle {r['cycle']['name']}. "
              f"Bodies: {', '.join(r['bodies'])}")
        return 2
    v = r["bodies"][name]
    print("\n".join(header(r)))
    cv = v["coverage"]
    print(f"\n{name}: score {_f(v['score'])} hierarchical, rank {v['rank'] or 'none'}; "
          f"{_f(v['flat'])} flat, rank {v['flat_rank'] or 'none'}; of "
          f"{r['coverage']['bodies']['measured']}; legs {_cov(cv['legs'])}, indicators "
          f"{_cov(cv['indicators'])}, constructs {_cov(cv['constructs'])}, criteria "
          f"{_cov(cv['criteria'])}; excluded rows {v['excluded'] or 'none'}")
    if v["concentration"]:
        print(v["concentration"]["sentence"])
    print()
    print(f"{'crit':<4}  {'construct':<58} {'leg':<13} {'pass/judged':>11} {'score':>6}")
    for l in r["structure"]:
        if not l["scored"]:
            continue
        x = v["legs"][l["leg"]]
        print(f"{l['criterion']:<4}  {l['construct'][:58]:<58} {l['leg']:<13} "
              f"{x['pass']:>5}/{x['judged']:<5} {_f(x['score']):>6}")
    print("\ncriteria: " + ", ".join(f"{k} {_f(c['score'])}"
                                     for k, c in v["criteria"].items()))
    gt = v["gating"]
    print(f"gating: {gt['legs_passed_outright']} of {gt['legs_judged']} judged legs passed "
          f"outright; constructs with zero passes: {', '.join(gt['zero_constructs']) or 'none'}")
    lad, order = v["ladder"], r["ladder"]["order"]
    print(f"\nreadiness level: {lad['label']} — "
          + "; ".join(f"{k}: {c['clear']} clear, {c['fail']} fail, {c['unobservable']} "
                      f"unobservable of {c['legs']}" for k, c in lad["per_criterion"].items()))
    nxt = lad["level"] + 1
    if nxt <= len(order):
        lv = r["ladder"]["levels"][nxt]
        gap = {l["leg"] for l in r["structure"] if l["scored"] and l["criterion"] == lv["criterion"]
               and leg_state(v["cells"].get(l["leg"], {})) != "clear"}
        print(f"to reach level {nxt} ({lv['name']}), these legs must clear: "
              f"{', '.join(sorted(gap))}" + ("; an unobservable leg clears only when the harness "
                                             "can see it" if lad["unobservable_at"] else ""))
    print("\nprescription join — actions on this body's failing legs, cheapest effort band "
          "first, then by the score each would add (bands notional):")
    print(f"{'effort':<8} {'cost':<11} {'delta':>6}  {'leg':<13} action")
    for p in v["prescriptions"]:
        print(f"{p['effort']:<8} {p['cost']:<11} {p['delta']:>+6.3f}  {p['leg']:<13} "
              f"{p['title']}")
    print("\ndelta: the body's score if every failing row on that leg passed. Actions on the "
          "same leg share it; the matrix carries verdicts, not outcomes, so it is an upper "
          "bound for any one action.")
    return 0


def print_top(r: dict, n: int) -> None:
    print("\n".join(header(r)))
    print(f"\ntop {n} actions: cheapest effort band first (bands are ordinal and are not "
          f"divided), then by the mean body-score raise over the "
          f"{r['coverage']['bodies']['measured']} scored bodies (bands notional):\n")
    print(f"{'effort':<8} {'cost':<11} {'raise':>6} {'bodies':>6}  {'leg':<13} action")
    for p in r["overall"][:n]:
        print(f"{p['effort']:<8} {p['cost']:<11} {p['mean_score_raise']:>+6.3f} "
              f"{p['bodies_raised']:>6}  {p['leg']:<13} {p['title']}")


def print_sensitivity(r: dict) -> None:
    print("\n".join(header(r)))
    s = r["sensitivity"]
    names = list(s["variants"])
    print("\nrank of each body under each alternative (baseline first); '-' = unscored\n")
    short = ["base"] + [n.replace("drop criterion ", "-").replace("prior cycle ", "prior")
                        .replace(" (equal leg weights)", "") for n in names]
    print(f"{'body':<11} " + " ".join(f"{h[:24]:>8}" for h in short))
    for b, v in sorted(r["bodies"].items(), key=lambda kv: (kv[1]["rank"] or 99, kv[0])):
        row = [v["rank"]] + [s["variants"][n]["ranks"].get(b) for n in names]
        print(f"{b:<11} " + " ".join(f"{x if x is not None else '-':>8}" for x in row))
    changed = s.get("prior_cycle_coverage_changed", {})
    if changed:
        print(f"\nlegs measured differ between the prior cycle and the cycle of record for "
              f"{len(changed)} bodies; their prior-cycle rank is not a like-for-like "
              f"comparison:")
        for b, c in changed.items():
            print(f"   {b:<11} prior {c['prior']}/{c['total']}  cycle of record "
                  f"{c['cycle_of_record']}/{c['total']}")
    print_concentration(r)
    print()
    for n in names:
        x = s["variants"][n]
        print(f"{n:<40} mean |rank shift| {_f(x['mean_abs_rank_shift'])}; "
              f"{x['bodies_moved']} of {x['bodies_compared']} bodies moved")


# ------------------------------------------------------------------ the design page

STEPS = [
    ("1. Theoretical framework",
     "The framework of record: criteria DECOMPOSES_INTO constructs DECOMPOSES_INTO "
     "indicators, read from the record's own edges.",
     "The Handbook's first step is a framework the indicators are selected under; this one "
     "exists as a graph object (DN-005 §2.1) and the model adds no structure to it."),
    ("2. Data selection",
     "The legs of the Tier M `harness_leg` indicators (read from `measurement_basis`) that the "
     "published matrices of the cycle of record judge. Candidate legs (DD-054), withdrawn legs "
     "and legs on no published matrix are structured and not scored; the table below names "
     "each with its reason.",
     "Only cold, re-derivable data enters (DN-005 §2.2 Tier M). Tier O and D indicators are "
     "not scored, and every output says so."),
    ("3. Imputation of missing data",
     "None. A leg with no judged row for a body is unmeasured for that body and leaves every "
     "mean it would have entered; `error`, `not_applicable` and any other verdict are out of "
     "the denominator and counted separately.",
     "An imputed verdict is a verdict the instrument did not reach. Case deletion at the "
     "lowest level, with the count printed, is the option the Handbook lists that asserts "
     "nothing the data does not."),
    ("4. Multivariate analysis",
     "Not performed.",
     "With 16 bodies and at most one to ten legs per criterion there is no sample on which a "
     "factor or correlation structure would be stable; the hierarchy is the framework's, not "
     "a derived one."),
    ("5. Normalisation",
     "A leg's score is its pass share over its judged rows (products or surfaces), already on "
     "[0, 1] and already comparable across legs.",
     "Every leg's verdict is binary and every share is a proportion, so no rescaling is "
     "needed and none is applied."),
    ("6. Weighting and aggregation",
     "Two equal-weight schemes, both shown, with the rank under each. Hierarchical: indicator "
     "= mean of its legs; construct = mean of its measured indicators; criterion = mean of its "
     "measured constructs; body = mean of the criteria with at least one measured construct. "
     "Flat: body = mean of its judged legs, each at 1/n. Beside both, a gating view in WCAG's "
     "shape (legs passed outright, and the first construct with zero passes) and the readiness "
     "level below.",
     "Equal weights at one level are implicit weights at the level below: hierarchically a "
     "criterion-A leg weighs 1/40 of a body with full coverage and B3 or F4 1/4; flat, every "
     "leg weighs the same and criterion A weighs ten legs' worth. There is no basis on disk "
     "to prefer either, so neither is chosen and both are printed. What would settle it is a "
     "stated priority from the working group, or an empirical relation between a leg and use "
     "of the data, recorded before the weight. The gating view and the ladder exist because "
     "an additive mean can hide a construct with nothing in it."),
    ("7. Uncertainty and sensitivity analysis",
     "Sensitivity, not an interval: every body is re-scored under the prior published cycle "
     "(with the cycle of record's structure, so only the data moves), under the flat scheme, "
     "and with each measured criterion dropped in turn; the rank changes and the mean absolute rank shift are "
     "reported.",
     "The mean absolute shift in rank is the Handbook's own summary statistic for this step. "
     "No distributional claim is made because the bodies are a census of the FSS, not a "
     "sample."),
    ("8. Back to the data",
     "Every score is printed with the cells it came from (`--body`), and every cell is a "
     "matrix cell that names its Finding.",
     "Decomposition is what lets a reader see which leg moves a body, and it is what the "
     "re-derivation test checks."),
    ("9. Links to other indicators",
     "The prescription join: for each body, each publisher action on a failing scored leg, "
     "with the score change if that leg's failing rows passed, ranked cheapest effort band "
     "first and then by that change.",
     "The link that matters to a publisher is to what they can do. Effort bands are ordinal "
     "(hours < days < weeks < quarter, `scripts/tag_prescriptions.py:EFFORT_BANDS`) and are "
     "not divided; the ranking is lexicographic for that reason."),
    ("10. Visualisation of the results",
     "Nothing is published. The query prints a grid, a body page, a ranked join and a "
     "sensitivity table to a terminal; this page documents the model and the ladder and names "
     "no body. Every view that prints a rank prints beside it the rank's concentration: the one "
     "leg whose verdicts, reversed, would move that body's rank furthest, with the rank it "
     "would then hold (`concentration` in `--json`; the MCP's `get_body` carries the same "
     "field).",
     "A score or a level on the site is a publication and is the operator's (decision 8 of "
     "the scoring task, decision 5 of the levels task). The concentration sentence is there "
     "because a rank can rest on a single verdict: with equal weights at each level, the only "
     "harness leg of a one-leg criterion carries that criterion's whole weight, and a rank a "
     "reader quotes should say when it is one pass deep (`cc_tasks/2026-09-19_resnapshot_rj4.md` "
     "decision 4). Reversal rather than deletion keeps the denominator fixed, so the move it "
     "reports is the verdict's and not a change of what was measured."),
]


def explain(r: dict) -> str:
    c = r["coverage"]
    lines = [
        "# The scoring model",
        "",
        f"Generated by `scripts/score.py --explain` (`{TASK}`); do not edit by hand. "
        "`scripts/score.py --check` fails if this page is not what the script prints.",
        "",
        f"**{COVERAGE_SENTENCE}**",
        "",
        "Framework layer served: DN-005 §2.1 (b) and §4 item 5. Prior art: the OECD/JRC "
        "*Handbook on Constructing Composite Indicators: Methodology and User Guide* (OECD, "
        "2008), whose ten steps are the outline below; the Open Data Barometer and ODIN "
        "(per-element grids beside an equal-weight total); WCAG conformance levels (the gating "
        "shape); OpenSSF Scorecard (additive, published weights). None of them is a document "
        "in `corpus/`; each is cited by reference.",
        "",
        "Two sources and no third: `framework/ai_readiness_framework.json` and the published "
        "matrices of the cycle of record named by `docs/reports/publication.yaml:"
        "snapshot_cycle`. Scores are computed at query time and never stored.",
        "",
        "## Coverage on the cycle of record",
        "",
        f"Cycle `{r['cycle']['name']}`, {r['cycle']['n_bodies']} bodies, matrices "
        + ", ".join(f"`{p}`" for p in r["cycle"]["matrices"]) + ".",
        "",
        "| level | measured | total |",
        "|---|---|---|",
        f"| adopted harness legs scored (candidates excluded, DD-054) | "
        f"{c['legs_on_cycle']['measured']} | "
        f"{c['legs_on_cycle']['total']} |",
        f"| indicators measured, of the framework | {c['indicators']['measured']} | "
        f"{c['indicators']['total']} |",
        f"| indicators measured, of `harness_leg` | {c['harness_leg_indicators']['measured']} | "
        f"{c['harness_leg_indicators']['total']} |",
        f"| criteria with a measured construct | {c['criteria']['measured']} | "
        f"{c['criteria']['total']} |",
        f"| bodies scored | {c['bodies']['measured']} | {c['bodies']['total']} |",
        "",
        "## The steps, in the Handbook's order",
        "",
    ]
    for title, choice, why in STEPS:
        lines += [f"### {title}", "", f"**Choice.** {choice}", "", f"**Why.** {why}", ""]
    lines += ["## The legs, and whether each is scored", "",
              "| criterion | construct | indicator | leg | scored | reason |",
              "|---|---|---|---|---|---|"]
    for l in r["structure"]:
        lines.append(f"| {l['criterion']} | {l['construct']} | `{l['indicator_id']}` | "
                     f"`{l['leg']}` | {'yes' if l['scored'] else 'no'} | {l['reason'] or '—'} |")
    lad = r["ladder"]
    lines += ["", "## Readiness levels: a cumulative ladder", "",
              f"Generated from the record by `{TASK_LEVELS}` decisions 3 and 4; nothing below is "
              "hand-written. The levels are the scored criteria in the framework's own order, "
              "named by the record's criterion names.", "",
              "**Definition.** A body is at level *k* when every scored leg of every criterion "
              "up to the *k*-th passes outright: at least one judged row, every judged row "
              "`pass`, and no `error` row (a leg whose every row is `not_applicable` is clear, "
              "as WCAG reads a requirement with nothing to apply to). The walk stops at the first "
              "criterion that is not clear. A `fail` there places the body one level below it. "
              "No fail but an `error` or no row places it one level below as well and reports "
              "`k-1 (unobservable at k)`: the body demonstrably holds *k*-1 and level *k* was "
              "not observed, so it is never rounded up. A level is never an average; it re-derives "
              "from the per-criterion clear / fail / unobservable counts that every output "
              "prints beside it.", "",
              "**Prior art.** JRC, *AI Watch: Revisiting Technology Readiness Levels for "
              "Relevant AI Technologies* (in the corpus, `ai-watch-revisiting-technology-"
              "readiness-levels-for-relevant`): §3 gives each of nine ordered levels a title and "
              "a rubric question, Appendix A the rubric per level, §4.3 reads the levels as "
              "ordinal and progress as cumulative. The five-star open data deployment scheme "
              "(Berners-Lee, 2010) and WCAG conformance levels have the same shape and are cited "
              "by reference; W3C DWBP (in the corpus) names the \u201c5 Stars of Linked Data\u201d "
              "in Best Practice 10 without a reference entry.", "",
              "| level | name | criterion | legs that must pass outright at this level |",
              "|---|---|---|---|"]
    for lv in lad["levels"]:
        lines.append(f"| {lv['level']} | {lv['name']} | {lv['criterion'] or '—'} | "
                     f"{', '.join(f'`{x}`' for x in lv['legs']) or '—'} |")
    lines += ["", "### The rubric", "",
              "One sentence per level, from the record's legs and the prescription layer's "
              "actions (cheapest effort band per leg; bands notional).", ""]
    lines += [f"- {lv['sentence']}" for lv in lad["levels"]]
    lines += ["", "### Candidate indicators and the ladder", "",
              "A candidate leg (DD-054) enters no level, as it enters no score. The record's "
              "promotion field for each candidate, quoted:", ""]
    for n in r["candidates"]:
        lines.append(f"- `{n['id']}`: \u201c{n['promotion']}\u201d")
    lines += ["", "## Re-deriving a score", "",
              "`scripts/score.py --json` prints, for every body, the verdict counts per leg "
              "(`cells`) beside every score computed from them. `tests/test_score.py` "
              "recomputes each body's score, hierarchical and flat, from those cells with an "
              "implementation written independently of this script, scores a synthetic body "
              "against a hand computation, re-derives every level from the printed "
              "per-criterion counts, asserts that no body is placed at or above a criterion "
              "where it has an `error`, and asserts that no coverage line claims more measured "
              "than its total.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--body", metavar="NAME")
    g.add_argument("--top", type=int, metavar="N")
    g.add_argument("--sensitivity", action="store_true")
    g.add_argument("--json", action="store_true")
    g.add_argument("--explain", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--cycle", help="score a cycle other than the cycle of record")
    ap.add_argument("--prior", help="the prior cycle for the sensitivity view")
    a = ap.parse_args(argv)
    r = compute(a.cycle, a.prior)
    if a.json:
        print(json.dumps(r, indent=1, sort_keys=True))
    elif a.body:
        return print_body(r, a.body)
    elif a.top:
        print_top(r, a.top)
    elif a.sensitivity:
        print_sensitivity(r)
    elif a.explain:
        print(explain(r), end="")
    elif a.check:
        want = explain(r)
        have = DOC.read_text(encoding="utf-8") if DOC.exists() else None
        if have != want:
            print(f"FAIL {DOC.relative_to(REPO)} is not `scripts/score.py --explain`; "
                  f"regenerate it with: scripts/score.py --explain > {DOC.relative_to(REPO)}")
            return 1
        print(f"{DOC.relative_to(REPO)} is the generated page")
    else:
        print_grid(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
