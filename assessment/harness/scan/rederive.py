#!/usr/bin/env python3
"""Re-derivation gate: delete every Finding, re-judge from stored Observations, demand
byte-identical output. **Zero model calls, no network.**

Task §3. Skeleton §6b.5 claims that "thresholds can change and history can be re-scored
without re-measurement". This is the test of that claim, and it is a real test only because a
Finding's id is DERIVED — `sha256(rule_id | rule_version | sorted obs_ids | params_hash)` —
rather than assigned by a counter or a clock. An id from either would make the comparison
vacuous: it would differ every run whether or not the judgement did.

    /opt/anaconda3/bin/python3 assessment/harness/scan/rederive.py --from state/scan_smoke_2026-09-06.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))

from scan import errors                                        # noqa: E402
from scan import load_params                                   # noqa: E402
from scan.model import Observation, params_hash                # noqa: E402
from scan.rules import (CANDIDATE_LEGS, CURRENT, REGISTRY,      # noqa: E402
                        consumes, judge as judge_rule)

#: The task that ordered the re-judgement mode, recorded on every payload it writes.
TASK = "cc_tasks/2026-09-08_scan_harness_v4.md"
#: What a re-judged cycle's name and payload are called. `_rj1`, not a date: the re-judgement
#: is not a new measurement and must never look like one, and DD-041's rerun convention is a
#: suffix on the ORIGINAL name for exactly this reason.
REJUDGE_SUFFIX = "_rj1"



def rehydrate(rows: list) -> list:
    return [Observation(**r) for r in rows]


def rejudgeable(rows: list) -> list:
    """The Observation rows a RE-JUDGEMENT judges from: the surfaces, never the controls.

    A control Observation belongs to the cycle that ran the fixtures. Re-judging it would
    produce a control Finding for a control run that did not happen, and — because the control
    SET itself changed under v4 — one measured against a table it was never scanned under.
    The gate this re-judgement stands on is the five-fixture run recorded on the payload as
    `control_gate`. Named once, and called by both the re-judgement and the re-derivation gate,
    so the two cannot disagree about what was judged.
    """
    return [r for r in rows if not str(r.get("target_doc_id", "")).startswith("control:")]


def observations_for(payload: dict) -> list:
    """The Observation ROWS a payload's Findings were judged from.

    Its own, for a measured cycle. A RE-JUDGED cycle carries none — that is what makes it a
    re-judgement — and its evidence is the source cycle's, named on the payload as
    `derived_from`. Without this the gate would report every re-judged Finding as
    `missing_after_rederive`, which is not "the rules are non-deterministic", it is "the gate
    looked for the evidence in the wrong file".
    """
    rows = payload.get("observations_detail") or []
    if rows or not payload.get("derived_from"):
        return rows
    src = REPO / "state" / f"{payload['derived_from']}.json"
    if not src.is_file():
        raise SystemExit(
            f"REFUSING: {payload['cycle']} is derived from {payload['derived_from']}, whose "
            f"payload is not at {src}. A re-judged cycle cannot be re-derived without the "
            f"evidence it cites.")
    # The SAME subset `rejudge` judged from, through the same function. Handing back the
    # source cycle's control observations too would make the gate re-judge 64 fixture Findings
    # the re-judgement never recorded and report them as `unexpected_after_rederive` — the
    # gate looking in a wider place than the run, which reads as non-determinism and is not.
    return rejudgeable(json.loads(src.read_text(encoding="utf-8")).get("observations_detail")
                       or [])


def rederive(payload: dict, params: dict) -> dict:
    """Re-judge every leg from stored Observations alone and diff against the recorded
    Findings. Nothing is fetched; if this needed the network the split would be a fiction.

    The gate asks whether the RULES are deterministic, so it must hold the parameters fixed.
    Re-deriving under a different `params_hash` legitimately produces different Findings —
    that is §6b.5's whole point, that thresholds may change and history be re-scored — and
    comparing across the change would test the wrong thing and fail for the right reason,
    confusingly. So a params mismatch is reported as itself, not as a broken gate.
    """
    recorded_hash = payload.get("params_hash")
    current_hash = params_hash(params)
    if recorded_hash and recorded_hash != current_hash:
        return {"identical": False, "params_changed": True,
                "recorded_params_hash": recorded_hash, "current_params_hash": current_hash,
                "note": ("params.yaml has changed since this cycle ran, so its Findings carry "
                         "different ids by construction. Re-run the cycle; do not compare "
                         "across a parameter change.")}
    obs = rehydrate(observations_for(payload))
    # Control Findings are re-derived too. They are the ones whose determinism matters most —
    # they are what licenses the cycle — and the first version of this gate compared only the
    # surface Findings, so retaining the fixture Observations made it report the control
    # Findings as `unexpected_after_rederive` rather than checking them.
    recorded = {f["finding_id"]: f for f in
                payload["findings_detail"] + payload.get("control_findings_detail", [])}
    # Grouped by (surface, leg) — except E5, which judges the CYCLE. Its two control
    # Observations are one group, not one per fixture; grouping them per fixture re-derived
    # two E5 Findings where the cycle recorded one, which is how this was found.
    by_key: dict = {}
    for o in obs:
        by_key.setdefault(("*cycle*" if o.leg == "E5" else o.target_doc_id, o.leg), []).append(o)

    # Re-judge each recorded Finding under ITS OWN rule version, never under the leg's current
    # rule. Several versions now live side by side (rules/__init__ `CURRENT` vs `REGISTRY`), and
    # re-deriving a `RULE-A1-v1` Finding with `RULE-A1-v3` would silently re-score history
    # under a rule that did not exist when the surface was measured — the exact thing the
    # versioning is for. Rule versions the payload never used are simply not exercised.
    wanted = {f.get("rule_id") for f in recorded.values()} or set(CURRENT.values())
    # Iterate (surface x rule) rather than (surface x leg): a rule may read a SHARED leg
    # (`rules.consumes`) and collect nothing under its own, in which case there is no
    # `(doc, leg)` key at all and a leg-driven loop would silently never judge it. `consumes`
    # is the same function `run.py` groups with, so a re-derivation cannot group differently
    # from the cycle that recorded the Finding.
    docs = sorted({d for d, _ in by_key})
    rederived, mismatches = {}, []
    for doc_id in docs:
        for rule_id in sorted(r for r in wanted if REGISTRY.get(r) is not None):
            group = list(by_key.get((doc_id, REGISTRY[rule_id].LEG), []))
            for c in consumes(rule_id):
                group += by_key.get((doc_id, c), [])
            if not group:
                continue
            f = judge_rule(rule_id, group, params)
            rederived[f.finding_id] = f.to_dict()

    missing = sorted(set(recorded) - set(rederived))
    extra = sorted(set(rederived) - set(recorded))
    for fid in sorted(set(recorded) & set(rederived)):
        if recorded[fid] != rederived[fid]:
            mismatches.append(fid)
    return {"recorded": len(recorded), "rederived": len(rederived),
            "missing_after_rederive": missing, "unexpected_after_rederive": extra,
            "field_mismatches": mismatches,
            "identical": not (missing or extra or mismatches)}


# ------------------------------------------------------------------ re-judgement (§1.5)
#
# The re-derivation gate above asks "do these rules still produce what they produced?" and
# holds the parameters fixed to ask it. This asks the OTHER question skeleton §6b.5 promises
# can be asked: "what would these observations say under the rules we have NOW?" — the same
# machinery, pointed at a new params hash and a new cycle name.
#
# Prior art, and it is ordinary: re-analysis of retained raw data under a corrected scoring
# rule. The harness's own doctrine already licenses it — Observations are evidence and
# Findings are judgements over them (DD-052, and `model.py`'s OSCAL/Lighthouse lineage), so a
# corrected rule over retained evidence is a new judgement and not a new measurement. Nothing
# here fetches anything, and a re-judged cycle is its OWN cycle: it never overwrites the
# payload, the figures or the Results of the cycle it derives from.


def rules_by_leg(payload: dict) -> dict:
    """The rule each leg was actually judged by in this payload. Read off the Findings rather
    than assumed from `CURRENT`, because `CURRENT` is today's answer and the payload's is the
    one that was true when it was written."""
    out = {}
    for f in payload.get("findings_detail") or []:
        out.setdefault(f["leg"], f["rule_id"])
    return out


def rejudge(payload: dict, params: dict, cycle: str | None = None,
            control_gate: dict | None = None) -> dict:
    """Judge a stored cycle's Observations under CURRENT and the params on disk.

    Findings only. No Observation is created: every Finding cites the `obs_id`s the source
    cycle recorded, which are already on the append-only log, so publishing this payload adds
    judgements and no evidence. That is the whole claim being tested — that the evidence was
    sufficient and the JUDGEMENT was wrong.

    **A leg is not judged when its CURRENT rule consumes a leg the source cycle never
    collected.** Cycle 1 has no `link_probe` leg (it was introduced by harness-v3), and
    `RULE-A1-v3` / `RULE-A3-v4` read it; judging them from whatever else happens to be under
    `A1` would produce a number that looks like a re-judgement and is not one. Such legs
    register NOTHING and the reason is on the payload, because "not measured is a reason, not a
    zero" (DD-055) applies to a re-judgement exactly as it applies to a measurement.

    E5 is never re-judged, for the same reason one layer up: the control set itself changed
    (`invalid_route_unobserved` is a fifth fixture), so `RULE-E5-v2` reading the source cycle's
    four-fixture record against a five-fixture expectation would report the SOURCE cycle as
    invalid for a difference that is entirely in the instrument. The gate that licenses this
    re-judgement is the one this task ran, and it is recorded on the payload as `control_gate`.
    """
    src_cycle = payload["cycle"]
    cycle = cycle or f"{src_cycle}{REJUDGE_SUFFIX}"
    obs = rehydrate(rejudgeable(payload["observations_detail"]))
    by_key: dict = {}
    for o in obs:
        by_key.setdefault((o.target_doc_id, o.leg), []).append(o)
    legs_present = {leg for _d, leg in by_key}
    source_rules = rules_by_leg(payload)

    #: leg -> why it was not judged. Every entry is a leg that registers nothing.
    not_judged: dict = {}
    judgeable = []
    for leg, rule_id in CURRENT.items():
        if leg == "E5":
            not_judged[leg] = ("E5 judges the CYCLE, and the control set changed under v4 "
                               "(a fifth fixture): re-judging the source cycle's four-fixture "
                               "record against a five-fixture expectation would report a "
                               "change in the instrument as a failure of the cycle. This "
                               "task's own control gate is recorded as `control_gate`.")
            continue
        needs = consumes(rule_id)
        absent = [c for c in needs if c not in legs_present]
        if absent:
            not_judged[leg] = (f"{rule_id} consumes {absent}, which {src_cycle} did not "
                               f"collect; judging it from anything else would be a number "
                               f"that looks like a re-judgement and is not one")
            continue
        # A rule's evidence is its own leg PLUS the shared legs it declares. `RULE-A1-v3` and
        # `RULE-A3-v4` collect nothing under their own leg at all — `runner.collect_leg`
        # returns [] for `link_probe.legs_served` — so requiring the own leg to be present
        # skipped exactly the two rules the shared leg was built for, and called cycle 2
        # "recorded no observation on leg A1" when it recorded 1,118 of them under
        # `link_probe`. A rule is judgeable when SOME leg it reads is present.
        if REGISTRY[rule_id].LEG not in legs_present and not needs:
            not_judged[leg] = f"{src_cycle} recorded no observation on leg {leg}"
            continue
        judgeable.append(leg)

    findings, matrix_rows = [], []
    src_rows = {r["doc_id"]: r for r in payload.get("matrix") or []}
    for doc_id in sorted({d for d, _ in by_key}):
        verdicts = {}
        for leg in judgeable:
            rule_id = CURRENT[leg]
            group = list(by_key.get((doc_id, REGISTRY[rule_id].LEG), []))
            for c in consumes(rule_id):
                group += by_key.get((doc_id, c), [])
            if not group:
                continue          # this SURFACE has no evidence for this leg; see src row
            f = judge_rule(rule_id, group, params)
            findings.append(f)
            verdicts[leg] = f.verdict
        src = src_rows.get(doc_id, {})
        matrix_rows.append({"doc_id": doc_id, "url": src.get("url"),
                            "surface_kind": src.get("surface_kind", "flagship"),
                            "agency": src.get("agency", "unknown"),
                            "admitted": src.get("admitted", True),
                            "verdicts": verdicts,
                            "verdicts_as_measured": src.get("verdicts", {})})

    changed = {leg: {"source": source_rules.get(leg), "current": CURRENT[leg]}
               for leg in judgeable
               if source_rules.get(leg) and source_rules[leg] != CURRENT[leg]}
    moved = [{"doc_id": r["doc_id"], "leg": leg,
              "from": r["verdicts_as_measured"].get(leg), "to": v}
             for r in matrix_rows for leg, v in r["verdicts"].items()
             if r["verdicts_as_measured"].get(leg) not in (None, v)]
    return {
        "task": TASK,
        "cycle": cycle,
        "cycle_kind": "rejudged",
        "derived_from": src_cycle,
        "derived_from_params_hash": payload.get("params_hash"),
        "targets": payload.get("targets"),
        "harness_version": errors.harness_of(params), "params_version": params["params_version"], "params_hash": params_hash(params),
        "rejudged_note": (
            f"Findings only. Every Finding cites the `obs_id`s {src_cycle} recorded; not one "
            f"byte was re-fetched and not one Observation was created. The evidence is that "
            f"cycle's, the judgement is this one's."),
        "rules": sorted({f.rule_id for f in findings}),
        "rules_changed_since_source": changed,
        "legs_judged": sorted(judgeable),
        "legs_not_judged": not_judged,
        "verdicts_moved": moved,
        "surfaces": len(matrix_rows),
        "legs": len(judgeable),
        "findings": len(findings),
        "observations": len(obs),
        "observations_reused": len({o.obs_id for o in obs}),
        "verdict_counts": {v: sum(1 for f in findings if f.verdict == v)
                           for v in ("pass", "fail", "not_applicable", "error")},
        # No host was asked for anything. Stated as zero rather than omitted: a re-judged
        # cycle's manners claim is that it made no request at all.
        "requests_per_host": {}, "requests_total": 0,
        "error_class_counts_of_source": payload.get("error_class_counts"),
        "control_verdict": (control_gate or {}).get("verdict"),
        "control_reason": (control_gate or {}).get("reason"),
        "control_gate": control_gate,
        "control_findings": 0,
        "control_findings_detail": [],
        "matrix": matrix_rows,
        "findings_detail": [f.to_dict() for f in findings],
        # Empty BY CONSTRUCTION and asserted by the gate: a re-judgement that wrote an
        # Observation would be a measurement wearing a re-judgement's name.
        "observations_detail": [],
    }


def run_module():
    """`scan/run.py`, loaded BY PATH — `assessment/harness/` holds a second `run.py` and only
    the path disambiguates the two.

    A function rather than three lines inline, so a test can substitute a stub runner and check
    the ONE property `control_gate_record` owes independently of the five fixtures: that
    whatever the gate collects lands outside the committed evidence store. Exercising that
    through the real fixtures would cost seven minutes to test a redirect.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_run_for_rejudge",
                                                  HARNESS / "scan" / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def control_gate_record(params: dict) -> dict:
    """Run the five control fixtures and record what they returned. **Loopback only.**

    A re-judgement is licensed by the same thing a cycle is: DD-019's decoy discipline, a
    cycle with zero fired controls is INVALID. The record is kept on the payload rather than
    published as Findings, because publishing it would mean publishing the fixture
    Observations behind it — new Observations, which is exactly what a re-judgement must not
    create.
    """
    import tempfile
    run_mod = run_module()
    # The fixture bodies go to a THROWAWAY root and are gone when this returns. `run.py::main`
    # redirects `model.EVIDENCE_ROOT` to a per-cycle staging directory before collecting
    # anything (`cc_tasks/2026-09-07_scan_run_2.md` §1.1); a caller that reaches `run_controls`
    # directly inherits the DEFAULT, which is the committed store — and this one did, writing
    # 54 fixture blobs into `corpus/evidence/scan/` across three runs before
    # `tests/test_scan_hygiene.py` caught them. Nothing here is worth keeping: the gate's
    # Findings are RECORDED on the payload and never published, so no Observation will ever
    # cite these bytes, which is the definition of litter.
    #
    # Read at call time by `model.store_evidence`, which is the repo convention and the same
    # seam `tests/conftest.py` uses.
    from scan import model as _model
    was = _model.EVIDENCE_ROOT
    with tempfile.TemporaryDirectory(prefix="scan_control_gate_") as tmp:
        _model.EVIDENCE_ROOT = Path(tmp)
        try:
            cf, e5, control_obs, ok = run_mod.run_controls(params)
        finally:
            _model.EVIDENCE_ROOT = was
    verdicts: dict = {}
    for f in cf:
        verdicts.setdefault(f.leg, {})[f.target_doc_id] = f.verdict
    fixtures = sorted(params["e5_control"]["expected_verdicts"])
    return {"verdict": e5.verdict, "reason": e5.reason, "ok": bool(ok),
            "fixtures": fixtures, "rule": e5.rule_id,
            "verdicts": verdicts,
            "unexpected": sorted(u for o in control_obs
                                 for u in ((o.parsed or {}).get("unexpected") or [])),
            "error_classes": sorted({c for o in control_obs
                                     for c in ((o.parsed or {}).get("error_classes") or [])}),
            "note": ("The control gate this re-judgement stands on: five fixtures, every rule "
                     "its pre-registered verdict. Recorded, not published — publishing these "
                     "Findings would require publishing the fixture Observations behind them, "
                     "and a re-judgement creates no Observation.")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default=str(REPO / "state" / "scan_smoke_2026-09-06.json"))
    ap.add_argument("--under-current", action="store_true",
                    help="RE-JUDGE the stored Observations of --from under CURRENT and the "
                         "params on disk, writing state/<cycle>_rj1.json. Findings only; "
                         "nothing is fetched and no Observation is created.")
    ap.add_argument("--out", default=None, metavar="PATH",
                    help="where the re-judged payload is written (default "
                         "state/<cycle>_rj1.json)")
    a = ap.parse_args(argv)
    payload = json.loads(Path(a.src).read_text(encoding="utf-8"))
    params = load_params()
    if a.under_current:
        gate = control_gate_record(params)
        print(f"CONTROL GATE: {str(gate['verdict']).upper()} — {gate['reason']}")
        if not gate["ok"]:
            print("re-judgement INVALID; nothing written", file=sys.stderr)
            return 2
        out = rejudge(payload, params, control_gate=gate)
        dest = Path(a.out) if a.out else REPO / "state" / f"{out['cycle']}.json"
        # A re-judged cycle is its own cycle and never overwrites the one it derives from.
        if dest.resolve() == Path(a.src).resolve():
            raise SystemExit(f"REFUSING: the re-judged payload would overwrite its own source "
                             f"{dest}. A re-judgement is a new cycle, not an edit to an old one.")
        dest.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in out.items()
                          if k not in ("matrix", "findings_detail", "control_findings_detail",
                                       "observations_detail", "control_gate",
                                       "verdicts_moved")}, indent=1))
        print(f"{len(out['verdicts_moved'])} verdict(s) moved; -> {dest}", file=sys.stderr)
        return 0
    res = rederive(payload, params)
    print(json.dumps(res, indent=1))
    print("RE-DERIVATION GATE:", "PASS" if res["identical"] else "FAIL")
    return 0 if res["identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
