#!/usr/bin/env python3
"""Exercise the generation-12 rules (B1-v2, B2, B5, D2) on the retained evidence of the cycle of
record. **No network, no model, nothing published.**

`cc_tasks/2026-09-18_schema_field_rules.md`, taking `cc_tasks/2026-09-18_dcat_field_rules.md`
decision 3's third leg unchanged. The rules are pre-registered, not run: cycle 5 (2026-10-05) is
the first cycle that judges them, and nothing this script prints enters a matrix, a figure, a
Result or the report.

**How the retained evidence is re-read.** The cycle of record
(`docs/reports/publication.yaml:snapshot_cycle`) is a re-judgement; its Observations are its
`derived_from` cycle's. The surfaces are the ones cycle 5 will judge each leg on — every tier-A
surface a leg reaches under `run.targets` (the frame's `state/<targets>.json`), which for these
legs is every tier-A row but the well-known one.

* **B2 and B5** read A6's `parsed.raw` exactly as it was stored: every A6 Observation since
  cycle 1 keeps `extruct`'s whole extraction, so nothing is re-parsed.
* **B1-v2** reads that and D4's catalog, which carries no `dcat_fields` block on any stored
  cycle; the block is attached offline from the stored body, exactly as
  `exercise_dcat_field_rules.enriched_groups` does and `runner.collect_leg` now does at
  collection.
* **D2** reads A4's robots.txt, which carries no `content_signal` block on any stored cycle; it
  is attached offline from the stored body with `v2clauses.content_signals`, exactly what
  `runner.collect_leg` now does at collection.
* **B5** is grouped with `rules.body_groups`, the function `run.judge_bodies` uses.

Each rule is judged twice and the Finding ids compared.

    /opt/anaconda3/bin/python3 scripts/exercise_schema_field_rules.py
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

SURFACE_LEGS = ("B1", "B2", "D2")
LEGS = SURFACE_LEGS + ("B5",)

#: The distribution the RESULT §1 reports, pinned so a change to a rule, a reader or the
#: retained evidence is seen rather than absorbed. Unpublished: see the module docstring.
EXPECTED_DISTRIBUTION = {
    "B1": {"error": 9, "fail": 37, "not_applicable": 0, "pass": 0},
    "B2": {"error": 8, "fail": 38, "not_applicable": 0, "pass": 0},
    "B5": {"error": 4, "fail": 12, "not_applicable": 0, "pass": 0},
    "D2": {"error": 6, "fail": 40, "not_applicable": 0, "pass": 0},
}


def _payload(name: str) -> dict:
    return json.loads((REPO / "state" / f"{name}.json").read_text(encoding="utf-8"))


def tier_a_surfaces(params: dict, source: dict) -> dict:
    """`{doc_id: url}` — the tier-A surfaces these legs reach under `run.targets`: every row of
    the frame the source cycle scanned, less tier C and the well-known rows."""
    frame = _payload(source["targets"])
    keep = {r["doc_id"] for r in frame["rows"]
            if r.get("tier", "A") == "A" and r["surface_kind"] != "well_known"}
    return {r["doc_id"]: r["url"] for r in source["matrix"] if r["doc_id"] in keep}


def exercise() -> dict:
    import tag_prescriptions as tp
    import exercise_dcat_field_rules as dx
    from scan import load_params
    from scan.collectors import v2clauses
    from scan.model import Observation
    from scan.rules import CURRENT, body_groups, judge as judge_rule
    params = load_params()
    cor = _payload(dx.cycle_of_record())
    source_name = cor.get("derived_from") or cor["cycle"]
    source = _payload(source_name)
    surfaces = tier_a_surfaces(params, source)
    d4_groups, d4_missing, _ = dx.enriched_groups(params)

    by_doc: dict = {}
    missing = []
    for row in source["observations_detail"]:
        doc = row["target_doc_id"]
        if doc not in surfaces or row["leg"] not in ("A4", "A6"):
            continue
        o = Observation(**copy.deepcopy(row))
        if o.leg == "A4" and (o.parsed or {}).get("present"):
            body_path = (o.response or {}).get("body_path")
            path = REPO / body_path if body_path else None
            if path is None or not path.is_file():
                missing.append(body_path)
                continue
            o.parsed = dict(o.parsed, content_signal=v2clauses.content_signals(
                path.read_bytes(), surfaces[doc], params))
        by_doc.setdefault(doc, []).append(o)
    for doc, obs in d4_groups.items():
        if doc in surfaces:
            by_doc.setdefault(doc, []).extend(obs)

    dist = {leg: Counter({v: 0 for v in ("error", "fail", "not_applicable", "pass")})
            for leg in LEGS}
    outcomes = {leg: Counter() for leg in LEGS}
    rows, deterministic = [], True

    def record(leg, target, f1, f2):
        nonlocal deterministic
        deterministic &= f1.finding_id == f2.finding_id
        dist[leg][f1.verdict] += 1
        named = [o for o, frag in tp.OUTCOMES[leg].items() if frag in f1.reason]
        if f1.verdict == "fail":
            outcomes[leg].update(named)
        rows.append({"doc_id": target, "leg": leg, "verdict": f1.verdict, "outcomes": named,
                     "reason": f1.reason})

    for doc in sorted(by_doc):
        for leg in SURFACE_LEGS:
            group = by_doc[doc]
            record(leg, doc, judge_rule(CURRENT[leg], group, params),
                   judge_rule(CURRENT[leg], copy.deepcopy(group), params))
    everything = [o for obs in by_doc.values() for o in obs]
    for _body, group in body_groups(CURRENT["B5"], everything, params).items():
        f1 = judge_rule(CURRENT["B5"], group, params)
        record("B5", f1.target_doc_id, f1,
               judge_rule(CURRENT["B5"], copy.deepcopy(group), params))

    return {"cycle_of_record": dx.cycle_of_record(), "observations_from": source_name,
            "surfaces": len(by_doc), "robots_bodies_missing": missing,
            "catalog_bodies_missing": d4_missing, "deterministic": deterministic,
            "distribution": {leg: dict(sorted(c.items())) for leg, c in dist.items()},
            "fail_outcomes": {leg: dict(sorted(c.items())) for leg, c in outcomes.items()},
            "rows": rows}


def main(argv=None) -> int:
    out = exercise()
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    for r in out["rows"]:
        print(f"{r['doc_id'][:48]:50s} {r['leg']} {r['verdict']:5s} {r['reason'][:170]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
