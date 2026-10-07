"""A composite cycle of record: some legs from one cycle, the rest from another. **Pure but `load`.**

`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` decision 4. The recollection collects
only the twelve legs generation 14 re-scoped (A1, A2, A3, A9, B1, B3, B4, D1, D3, D4, F4, G4);
the six L0 host checks and every other product leg stay as `scan_2026-09-10_rj5` judged them.
The views regenerate from a DECLARED composite of the two, named on every matrix and in the
report's methods line with both cycle ids.

**Why a materialised payload and not leg-aware readers.** Every view reads the cycle of record
by one name (`docs/reports/publication.yaml` `snapshot_cycle`) and builds a payload path, three
matrix paths and a Result-name suffix from it. A composite payload under its own name is
therefore read by every view unchanged, and the few readers that follow a cycle's EVIDENCE (its
Observations, its event shard, its projected Findings) learn one more kind here, beside
`rejudged`, instead of every view learning about legs.

**What the payload holds, and what it does not.** Its `matrix` and `findings_detail` are the two
parts' own rows and Findings, selected by leg and never re-judged: every Finding in it is a
Finding already on the event log under its part's cycle, with the same `finding_id`. It carries
no Observation (`observations_detail: []`, as a re-judgement does): the evidence is each part's,
and `evidence` assembles it. No score is computed here.

**Prior art.** This is a projection over two immutable logs selected by a declared key, the
event-sourcing pattern this repo already runs (invariant 1); the selection rule is stated on the
payload (`composed_of`) so a stranger can rebuild it from the two parts and nothing else.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

KIND = "composite"
#: The shape of `composed_of`. A reader checks it before trusting a key.
SCHEME = 1


def is_composite(payload: dict | None) -> bool:
    return bool(payload) and payload.get("cycle_kind") == KIND


def overlay_legs(payload: dict) -> list:
    return list(payload["composed_of"]["overlay"]["legs"])


def part_of_leg(payload: dict, leg: str) -> str:
    """The cycle a leg's verdicts come from on this composite."""
    c = payload["composed_of"]
    return c["overlay"]["cycle"] if leg in c["overlay"]["legs"] else c["base"]["cycle"]


def parts(payload: dict) -> list:
    """`[(cycle, legs_or_None)]`: the overlay with its legs, then the base with `None`, meaning
    every leg the overlay does not carry."""
    c = payload["composed_of"]
    return [(c["overlay"]["cycle"], list(c["overlay"]["legs"])), (c["base"]["cycle"], None)]


def finding_part(payload: dict, finding: dict) -> str:
    return part_of_leg(payload, finding["leg"])


def _load(state: Path, cycle: str) -> dict:
    return json.loads((state / f"{cycle}.json").read_text(encoding="utf-8"))


def _measured(state: Path, p: dict) -> dict:
    """The payload whose COLLECTION `p` rests on: itself, or a re-judgement's source."""
    src = p.get("derived_from") if p.get("cycle_kind") == "rejudged" else None
    return _load(state, src) if src else p


def build(base: dict, overlay: dict, name: str, task: str, consumes,
          withhold: dict | None = None) -> dict:
    """The composite payload. `consumes(leg) -> tuple` is `rules.consumes` over `CURRENT`,
    passed in so this module imports no rule.

    `withhold` is `{leg: reason}`: overlay legs the composite does NOT take, so the base's cells
    stand for them, with the reason stated on `composed_of`. A whole leg or nothing: withholding
    single cells (say, only a leg's passes) would make the published rate a function of which
    verdicts were liked. The overlay's Findings on a withheld leg stay on the log, under the
    overlay's cycle; they are not shown as the cycle of record.

    Refuses rather than guesses: the overlay must be a targeted cycle (`scope: legs`); every
    overlay surface must be a base surface with the same legs on the overlay's leg set; and
    every (surface, leg) the base judged on an overlay leg must be judged by the overlay too,
    so no cell is silently dropped or kept from the wrong part.
    """
    if overlay.get("scope") != "legs" or not overlay.get("legs_collected"):
        raise SystemExit(f"REFUSING: {overlay.get('cycle')} is not a targeted cycle "
                         f"(scope: legs); a composite overlays a leg set it names")
    withhold = dict(withhold or {})
    stray_w = sorted(set(withhold) - set(overlay["legs_collected"]))
    if stray_w or not all(str(v).strip() for v in withhold.values()):
        raise SystemExit(f"REFUSING: withheld legs must be overlay legs and carry a reason: "
                         f"{stray_w or withhold}")
    legs = [l for l in overlay["legs_collected"] if l not in withhold]
    base_rows = {r["doc_id"]: r for r in base["matrix"]}
    over_rows = {r["doc_id"]: r for r in overlay["matrix"]}
    stray = sorted(set(over_rows) - set(base_rows))
    if stray:
        raise SystemExit(f"REFUSING: overlay surfaces not in the base: {stray}")
    base_cells = {(f["target_doc_id"], f["leg"]) for f in base["findings_detail"]
                  if f["leg"] in legs}
    over_cells = {(f["target_doc_id"], f["leg"]) for f in overlay["findings_detail"]}
    lost = sorted(base_cells - over_cells)
    if lost:
        raise SystemExit(f"REFUSING: {len(lost)} base cell(s) on the overlay's legs have no "
                         f"overlay Finding (first {lost[:3]}); the composite would drop them")
    off = sorted(c for c in over_cells if c[1] not in legs and c[1] not in withhold)
    if off:
        raise SystemExit(f"REFUSING: overlay Findings outside its declared legs: {off[:3]}")

    matrix = []
    for r in base["matrix"]:
        row = json.loads(json.dumps(r))
        o = over_rows.get(r["doc_id"])
        if o is not None:
            for leg in legs:
                if leg in o["verdicts"]:
                    row["verdicts"][leg] = o["verdicts"][leg]
                else:
                    row["verdicts"].pop(leg, None)
        matrix.append(row)
    findings = ([f for f in base["findings_detail"] if f["leg"] not in legs]
                + [f for f in overlay["findings_detail"] if f["leg"] in legs])
    ids = Counter(f["finding_id"] for f in findings)
    dup = [i for i, n in ids.items() if n > 1]
    if dup:
        raise SystemExit(f"REFUSING: a finding_id from both parts: {dup[:3]}")

    # The control gate per leg: each leg's rule was checked against the fixtures by the part
    # whose verdicts this composite shows for that leg.
    base_gate = (base.get("control_gate") or {}).get("verdicts") or {}
    over_ctrl: dict = {}
    for f in overlay.get("control_findings_detail") or []:
        over_ctrl.setdefault(f["leg"], {})[f["target_doc_id"]] = f["verdict"]
    gate_verdicts = {leg: (over_ctrl.get(leg) if leg in legs else base_gate.get(leg))
                     for leg in sorted(set(base_gate) | set(over_ctrl))}
    gate_verdicts = {k: v for k, v in gate_verdicts.items() if v}
    kept = [l for l in base.get("legs_judged") or [] if l not in legs]
    shared_dropped = sorted({s for leg in legs for s in consumes(leg)}
                            - {s for leg in kept for s in consumes(leg)} - set(kept))
    return {
        "task": task, "cycle": name, "cycle_kind": KIND,
        "composed_of": {
            "scheme": SCHEME,
            "rule": ("each leg's matrix cells and Findings are the overlay's where the leg is "
                     "one the overlay collected, and the base's otherwise; no Finding is "
                     "re-judged and no Observation is created"),
            "overlay": {"cycle": overlay["cycle"], "legs": legs,
                        "params_hash": overlay["params_hash"], "task": overlay.get("task"),
                        "kind": overlay.get("cycle_kind") or "measured",
                        "collected": list(overlay["legs_collected"]),
                        "withheld": {l: withhold[l] for l in sorted(withhold)}},
            "base": {"cycle": base["cycle"], "legs": "every leg the overlay does not carry",
                     "params_hash": base["params_hash"], "task": base.get("task"),
                     "kind": base.get("cycle_kind") or "measured",
                     "collection": base.get("derived_from") or base["cycle"]},
            # Base Observations of a shared leg only overlay legs consumed (link_probe) rest
            # under no composite Finding, so `evidence` leaves them out.
            "base_observation_legs_dropped": sorted(set(legs) | set(shared_dropped)),
        },
        "targets": base.get("targets"),
        "harness_version": overlay.get("harness_version"),
        "params_version": overlay.get("params_version"),
        # The parameters the composite was assembled under: the overlay's, which are the
        # committed parameters today. Each part's own is on `composed_of`.
        "params_hash": overlay["params_hash"],
        "legs_judged": sorted(set(base.get("legs_judged") or []) | set(legs)),
        "legs_not_judged": base.get("legs_not_judged") or {},
        "surface_legs": base.get("surface_legs") or {},
        "surfaces": len(matrix), "legs": base.get("legs"),
        "findings": len(findings), "observations": 0,
        "verdict_counts": {v: sum(1 for f in findings if f["verdict"] == v)
                           for v in ("pass", "fail", "not_applicable", "error")},
        "requests_per_host": {}, "requests_total": 0,
        "control_verdict": ("pass" if base.get("control_verdict") == "pass"
                            and overlay.get("control_verdict") == "pass" else "fail"),
        "control_reason": (f"base {base['cycle']}: {base.get('control_reason')}; overlay "
                           f"{overlay['cycle']}: {overlay.get('control_reason')}"),
        "control_gate": {"verdict": ("pass" if base.get("control_verdict") == "pass"
                                     and overlay.get("control_verdict") == "pass" else "fail"),
                         "rule": "per leg, the gate of the part the leg's verdicts come from",
                         "verdicts": gate_verdicts},
        "control_findings": 0, "control_findings_detail": [],
        "matrix": matrix, "findings_detail": findings, "observations_detail": [],
    }


def evidence(payload: dict, state: Path) -> dict:
    """The Observations and requests the composite's Findings rest on, assembled from its parts.

    Every overlay Observation, and every base-collection Observation except those of the legs
    the overlay replaced (and of shared legs only those legs consumed). The requests are each
    part's collection, summed per netloc, with the parts kept apart under
    `requests_per_host_by_part`; the base's collection measured every leg, so its count is what
    that collection issued, not what the base's surviving legs cost.
    """
    c = payload["composed_of"]
    over = _measured(state, _load(state, c["overlay"]["cycle"]))
    base = _measured(state, _load(state, c["base"]["cycle"]))
    dropped = set(c["base_observation_legs_dropped"])
    # The overlay's Observations of a withheld leg rest under no composite Finding.
    withheld = set((c["overlay"].get("withheld") or {}))
    real = lambda o: not str(o.get("target_doc_id", "")).startswith("control:")  # noqa: E731
    obs = ([o for o in base["observations_detail"] if real(o) and o.get("leg") not in dropped]
           + [o for o in over["observations_detail"] if real(o) and o.get("leg") not in withheld])
    per = Counter(base.get("requests_per_host") or {})
    per.update(over.get("requests_per_host") or {})
    return {"cycle": payload["cycle"], "params_hash": payload["params_hash"],
            "observations_detail": obs, "requests_per_host": dict(sorted(per.items())),
            "requests_per_host_by_part": {
                base["cycle"]: base.get("requests_per_host") or {},
                over["cycle"]: over.get("requests_per_host") or {}},
            "requests_total": sum(per.values())}
