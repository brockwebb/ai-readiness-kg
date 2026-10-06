#!/usr/bin/env python3
"""Move an indicator to `measurement_status: measured` when the cycle earned it. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_run.md` §0 and §5. `measured` has a definition and this script
is it, so the word cannot drift:

    a cycle with FIRED CONTROLS produced, for that indicator's AUTO leg, at least one
    `pass`/`fail`/`not_applicable` Finding on an **admitted, observable** surface under
    `CURRENT` rules, with the evidence bytes committed and the Finding re-derivable.

Four things that definition deliberately excludes, each of which would otherwise be a way to
claim a measurement nobody made:

* **`error` does not count.** `error` means the collector could not observe. A leg that
  errored on every surface has measured nothing, however many Findings it produced.
* **An unadmitted surface does not count.** No `:Document`, no `OBSERVED_ON`, nothing to trace.
* **A cycle whose controls did not fire does not count** — it is INVALID (DD-019), and an
  invalid cycle cannot promote anything.
* **A candidate indicator never moves.** A12 stays `candidate` whatever it observed (DD-054);
  `measured` is a claim about the framework, and the framework has not adopted it.

An indicator that does NOT meet the bar keeps `harness_built` and the reason is recorded on
the node, because "why is A2 not measured" is the first question a reader of the progress page
will have and the answer should not require re-deriving the cycle.

**`measured` follows the cycle of record** (`cc_tasks/2026-10-06_scoring_frontier_parent_host_
counts.md` decision 3, DN-012 d7, DD-069). A run re-derives every indicator with a current
scan leg against the cycle it is given, the already-`measured` ones included, so `measured_by`
on every scan-measured node names that cycle. One the cycle no longer earns returns to
`harness_built` with the reason, and the `measured_by` it held moves to `measured_previously`:
nothing about the earlier measurement is lost, and the record stops saying the instrument of
record measures what its cycle of record could not observe. Two refinements, each recorded in
DD-069: a body-scoped leg (`rules.BODY_LEGS`, B5) qualifies on its one Finding per body when
the body has an admitted product surface, because that Finding sits on the body's synthetic
well-known row by construction; and an indicator measured at product level (`measurement_level:
product`, G1-D under DD-066) is read from product surfaces only. G1-O, which no scan leg
measures (DD-036), is untouched, as DD-055 §6 says.

    /opt/anaconda3/bin/python3 scripts/framework_writeback_measured.py [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw                                    # noqa: E402
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.rules import BODY_LEGS, CANDIDATE_LEGS, CURRENT          # noqa: E402

#: Which cycle the write-back reads is `params.cycle.name`, never typed — the same single
#: source `run.py`, `publish.py`, `scan_report.py` and `figures.py` read. A promotion to
#: `measured` is a claim about THE FRAMEWORK made on the strength of one cycle's evidence
#: (DD-055 §6), so a stale cycle name here would promote an indicator on last week's numbers
#: and stamp this week's cycle onto the record of why.
SCRIPT = "scripts/framework_writeback_measured.py"
#: The task that WROTE this script and its definition of `measured`. `--task` names the task
#: that ORDERED a given run, and that is what lands on the record — a promotion's
#: `recorded_by` should answer "who decided this indicator is measured", not "who wrote the
#: script that can decide it".
TASK = "cc_tasks/2026-09-07_scan_run.md"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
COUNTS_AS_MEASURED = ("pass", "fail", "not_applicable")
#: The surface kinds a host-level withdrawal (DD-066) takes a leg off, read from the same place
#: the instrument reads it (`params.tier0.legs_withdrawn`); a `measurement_level: product`
#: indicator is measured on every other kind.
HOST_LEVEL_KINDS_KEY = ("tier0", "legs_withdrawn")


def cycle_name(override: str | None = None) -> str:
    return override or load_params()["cycle"]["name"]


def host_level_kinds(params: dict | None = None) -> set:
    params = params or load_params()
    out = set()
    for w in (params.get(HOST_LEVEL_KINDS_KEY[0]) or {}).get(HOST_LEVEL_KINDS_KEY[1]) or []:
        out |= set(w.get("from_surfaces") or [])
    return out


def evidence(payload: dict, product_only: frozenset = frozenset(),
             host_kinds: set | None = None) -> dict:
    """Per leg: what this cycle actually produced on admitted surfaces.

    A body-scoped leg's Finding is on the body's well-known row (`rules.scope` = body), so it is
    read there, for the bodies with at least one admitted surface. A leg in `product_only` is
    read off host-level surface kinds. `unadmitted_qualifying` counts what the same leg produced
    on surfaces NOT admitted, so a reason can say a qualifying Finding exists and why it does
    not count (DD-055 exclusion 2), instead of reporting the leg as blind."""
    host_kinds = host_level_kinds() if host_kinds is None else host_kinds
    rows = [r for r in payload["matrix"]
            if r["surface_kind"] != "well_known" and r.get("admitted")]
    admitted_bodies = {r["agency"] for r in rows}
    body_rows = [r for r in payload["matrix"]
                 if r["surface_kind"] == "well_known" and r["agency"] in admitted_bodies]
    unadmitted = [r for r in payload["matrix"]
                  if r["surface_kind"] != "well_known" and not r.get("admitted")]
    out = {}
    for leg in CURRENT:
        src = body_rows if leg in BODY_LEGS else rows
        if leg in product_only:
            src = [r for r in src if r["surface_kind"] not in host_kinds]
        v = [r["verdicts"][leg] for r in src if leg in r["verdicts"]]
        c = collections.Counter(v)
        out[leg] = {"counts": {k: c[k] for k in ("pass", "fail", "not_applicable", "error")},
                    "qualifying": sum(c[k] for k in COUNTS_AS_MEASURED),
                    "surfaces": len(v),
                    "unadmitted_qualifying": sum(
                        1 for r in unadmitted
                        if r["verdicts"].get(leg) in COUNTS_AS_MEASURED)}
    return out


def product_only_legs(g: dict) -> frozenset:
    """Legs of indicators the record measures at product level (DD-066, G1-D)."""
    codes = {n["properties"]["code"] for n in g["nodes"]
             if "AssessmentIndicator" in n["labels"]
             and n["properties"].get("measurement_level") == "product"}
    return frozenset(l for l in CURRENT if l in codes)


def writeback(g: dict, payload: dict, ev: dict, cycle: str, task: str = TASK) -> dict:
    if payload.get("control_verdict") != "pass":
        raise SystemExit(f"REFUSING: the cycle's controls did not fire "
                         f"({payload.get('control_verdict')!r}); an INVALID cycle promotes "
                         f"nothing (DD-019)")
    specs = [n["properties"] for n in g["nodes"] if "MeasurementSpec" in n["labels"]]
    leg_of = collections.defaultdict(list)
    for s in specs:
        if s.get("leg"):
            leg_of[s["indicator_code"]].append(s["leg"])
    promoted, held, demoted, repointed = [], [], [], []
    for n in g["nodes"]:
        if "AssessmentIndicator" not in n["labels"]:
            continue
        p = n["properties"]
        code = p.get("code")
        if p.get("status") == "candidate":
            held.append((code, "candidate — `measured` is a claim about the framework, and "
                               "the framework has not adopted it (DD-054)"))
            continue
        legs = [l for l in leg_of.get(code, []) if l in CURRENT and l not in CANDIDATE_LEGS]
        # An indicator split into legs (G1) is measured when ANY leg with a current rule is.
        legs = legs or [l for l in leg_of.get(code, []) if l in CURRENT]
        if not legs:
            continue
        best = max((ev[l] for l in legs if l in ev),
                   key=lambda e: e["qualifying"], default=None)
        if best is None:
            continue
        # DD-069: re-derived against THIS cycle whatever the node said before. A `measured_by`
        # from another cycle is kept, as history, under `measured_previously`.
        prior = p.get("measured_by")
        if prior and prior.get("cycle") != cycle:
            p.setdefault("measured_previously", []).append(prior)
        if best["qualifying"] > 0:
            if p.get("measurement_status") != "measured":
                promoted.append(code)
            elif not prior or prior.get("cycle") != cycle:
                repointed.append(code)
            p["measurement_status"] = "measured"
            p["measured_by"] = {
                "cycle": cycle, "legs": legs, "params_hash": payload["params_hash"],
                "qualifying_findings": best["qualifying"], "counts": best["counts"],
                "definition": ("at least one pass/fail/not_applicable Finding on an admitted, "
                               "observable surface in a cycle with fired controls; `error` "
                               "does not count"),
                "recorded_by": task}
            if p.get("measurement_level") == "product":
                p["measured_by"]["surfaces"] = ("product surfaces only: the host-level leg is "
                                                "withdrawn (DD-066)")
            if any(l in BODY_LEGS for l in legs):
                p["measured_by"]["surfaces"] = (
                    "the body's one Finding, on its well-known row, for bodies with an admitted "
                    "product surface (DD-069)")
            p.pop("not_measured_reason", None)
        else:
            if p.get("measurement_status") == "measured":
                p["measurement_status"] = "harness_built"
                p.pop("measured_by", None)
                demoted.append(code)
            # E5's subject is the CYCLE, not a surface, so §0's definition — which requires a
            # Finding "on an admitted, observable surface" — can never be satisfied by it.
            # That is a limitation of the definition, not a gap in the measurement: E5 fired
            # in this cycle and in every cycle, and its Finding is on the log. Recorded as
            # what it is rather than as a missing measurement.
            if "E5" in legs:
                why = ("E5 judges the CYCLE, not a surface, so DD-055's definition of "
                       "`measured` — a Finding on an admitted, observable surface — cannot "
                       "apply to it. Its control Finding fired in this cycle and every "
                       "other; the status is a limitation of the definition, not a gap in "
                       "the measurement.")
            elif best["counts"]["error"] and best["unadmitted_qualifying"]:
                why = (f"every Finding on an admitted surface was `error`; the "
                       f"{best['unadmitted_qualifying']} qualifying Finding(s) of this cycle are "
                       f"on surfaces not admitted to the corpus, which DD-055 does not count")
            elif best["counts"]["error"]:
                why = ("every Finding was `error` — the collector could not observe any "
                       "admitted surface")
            else:
                why = "no admitted surface produced a Finding for this leg"
            p["not_measured_reason"] = {"cycle": cycle, "legs": legs, "reason": why,
                                        "counts": best["counts"], "recorded_by": task}
            held.append((code, why))
    # See `scripts/framework_writeback.py`: one definition of every denominator, regenerated
    # on every write-back (`cc_tasks/2026-09-07_scan_hygiene.md` §3). `indicators_measured` is
    # candidate-excluded there for the reason it was here — DD-054.
    fw.apply_counts(g)
    return {"promoted": sorted(promoted), "held": sorted(held), "demoted": sorted(demoted),
            "repointed": sorted(repointed),
            "indicators_measured": g["counts"]["indicators_measured"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle", default=None,
                    help="write back from a cycle other than params.cycle.name")
    ap.add_argument("--task", default=None,
                    help="the cc_task that ordered this run; recorded on the "
                         "`framework_writeback` event so the record of record names who "
                         "changed it")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    cycle = cycle_name(a.cycle)
    payload = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    out = writeback(g, payload, evidence(payload, product_only_legs(g)), cycle, a.task or TASK)
    print(json.dumps({**out, "cycle": cycle}, indent=1))
    # Through the shared writer, so the write and the `framework_writeback` event that records
    # it cannot come apart.
    ev = fw.save(g, script=SCRIPT, task=a.task or TASK, changes={**out, "cycle": cycle},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({k: v for k, v in ev.items() if k != "counts"}, indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
