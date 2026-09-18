#!/usr/bin/env python3
"""Exercise the four DCAT-US field rules on the retained catalogs of the cycle of record.
**No network, no model, nothing published.**

`cc_tasks/2026-09-18_dcat_field_rules.md` decision 3, third leg. The rules are pre-registered,
not run: cycle 5 (2026-10-05) is the first cycle that judges them, and nothing this script
prints enters a matrix, a figure, a Result or the report. What it establishes is that each rule
can be exercised on real catalogs before it is registered, and what it would say.

**How the retained evidence is re-read.** The cycle of record
(`docs/reports/publication.yaml:snapshot_cycle`) is a re-judgement; its Observations are its
`derived_from` cycle's. Every D4 Observation there was collected before `dcat_fields` existed,
so it carries no field block, and the rules correctly return `error` on it
(`tests/test_dcat_field_rules.py`). This script therefore does, offline, exactly what
`runner.collect_leg` now does at collection time: it reads the stored catalog body the
Observation cites (`corpus/evidence/scan/…`, content-addressed and tracked), parses it, and
attaches `v2clauses.dcat_record_fields(catalog, product_url, params)` — with `product_url` the
surface URL the cycle collected for that row, the same argument D4's membership test used.
Then it judges each rule twice and compares the Finding ids.

    /opt/anaconda3/bin/python3 scripts/exercise_dcat_field_rules.py
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

LEGS = ("B1", "B4", "D3", "G4")

#: The distribution the RESULT §1 reports, pinned so a change to a rule, the collector block or
#: the retained evidence is seen rather than absorbed. Unpublished: see the module docstring.
#:
#: G4 was `{"error": 8, "fail": 35, "pass": 3}` under D4's substring membership test. Two of the
#: three passes were host-level `home` surfaces "owning" every record containing their URL
#: (that RESULT §1). `cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 4 moved the
#: test to DCAT-US's own URL fields (`dcat.product_records`), and those two surfaces now own no
#: record: they are `fail`, `no_product_record`. `d4_membership` below reports the move per
#: surface; still unpublished.
EXPECTED_DISTRIBUTION = {
    "B1": {"error": 8, "fail": 38},
    "B4": {"error": 8, "fail": 38},
    "D3": {"error": 8, "fail": 38},
    "G4": {"error": 8, "fail": 37, "pass": 1},
}


def cycle_of_record() -> str:
    import yaml
    pub = yaml.safe_load((REPO / "docs/reports/publication.yaml").read_text(encoding="utf-8"))
    return pub["snapshot_cycle"]


def _payload(name: str) -> dict:
    return json.loads((REPO / "state" / f"{name}.json").read_text(encoding="utf-8"))


def enriched_groups(params: dict) -> tuple:
    """`({doc_id: [Observation]}, missing_bodies, source_cycle)` — the cycle of record's
    surface D4 Observations with the field block attached from their stored bodies."""
    from scan.collectors import v2clauses
    from scan.model import Observation
    cor = _payload(cycle_of_record())
    source = cor.get("derived_from") or cor["cycle"]
    src = _payload(source)
    urls = {r["doc_id"]: r["url"] for r in cor["matrix"]}
    groups: dict = {}
    missing = []
    for row in src["observations_detail"]:
        if row["leg"] != "D4" or row["target_doc_id"] not in urls:
            continue
        o = Observation(**copy.deepcopy(row))
        if (o.parsed or {}).get("present"):
            body_path = (o.response or {}).get("body_path")
            path = REPO / body_path if body_path else None
            if path is None or not path.is_file():
                missing.append(body_path)
                continue
            try:
                cat = json.loads(path.read_bytes().decode("utf-8", "replace"))
            except ValueError as exc:
                o.parsed = dict(o.parsed, dcat_fields={
                    "scheme": v2clauses.DCAT_FIELDS_SCHEME, "parsed": False,
                    "reason": f"{type(exc).__name__}: {exc}"})
            else:
                o.parsed = dict(o.parsed, dcat_fields=v2clauses.dcat_record_fields(
                    cat, urls[o.target_doc_id], params))
        groups.setdefault(o.target_doc_id, []).append(o)
    return groups, missing, source


def d4_membership(params: dict) -> list:
    """Per surface with a served, parseable catalog: how many records the SUBSTRING test
    (`product_url in json.dumps(d)`, what `contains_product` records) and the DCAT-US FIELD test
    (`dcat.product_records`, what `RULE-D4-v3` reads) each assign to the product.

    `cc_tasks/2026-09-18_manners_status_and_b5_control.md` decision 4. Read from the same
    retained bodies `enriched_groups` reads; nothing is judged or published."""
    from scan.collectors.dcat import product_records
    cor = _payload(cycle_of_record())
    src = _payload(cor.get("derived_from") or cor["cycle"])
    urls = {r["doc_id"]: r["url"] for r in cor["matrix"]}
    out = []
    for row in src["observations_detail"]:
        if row["leg"] != "D4" or row["target_doc_id"] not in urls:
            continue
        if not (row.get("parsed") or {}).get("present"):
            continue
        path = REPO / ((row.get("response") or {}).get("body_path") or "")
        try:
            cat = json.loads(path.read_bytes().decode("utf-8", "replace"))
        except (OSError, ValueError):
            continue
        ds = [d for d in (cat.get("dataset") or []) if isinstance(d, dict)] \
            if isinstance(cat, dict) else []
        url = urls[row["target_doc_id"]]
        sub = sum(1 for d in ds if url in json.dumps(d))
        field = len(product_records(ds, url, params))
        out.append({"doc_id": row["target_doc_id"], "url": url, "catalog_records": len(ds),
                    "substring_records": sub, "field_records": field,
                    "member_substring": sub > 0, "member_field": field > 0})
    return sorted(out, key=lambda r: r["doc_id"])


def exercise() -> dict:
    import tag_prescriptions as tp
    from scan import load_params
    from scan.rules import V11, judge as judge_rule
    # The generation-11 rules by id, not `CURRENT`: B1's CURRENT rule became `RULE-B1-v2` in
    # generation 12 (`cc_tasks/2026-09-18_schema_field_rules.md`), which also reads A6's markup,
    # and this script reproduces `cc_tasks/2026-09-18_dcat_field_rules_RESULT.md` §1, which is
    # about the four DCAT-only rules. `exercise_schema_field_rules.py` exercises v2.
    CURRENT = {m.LEG: m.RULE_ID for m in V11}
    params = load_params()
    groups, missing, source = enriched_groups(params)
    dist: dict = {leg: Counter() for leg in LEGS}
    outcomes: dict = {leg: Counter() for leg in LEGS}
    deterministic = True
    rows = []
    for doc_id in sorted(groups):
        for leg in LEGS:
            f1 = judge_rule(CURRENT[leg], groups[doc_id], params)
            f2 = judge_rule(CURRENT[leg], copy.deepcopy(groups[doc_id]), params)
            deterministic &= f1.finding_id == f2.finding_id
            dist[leg][f1.verdict] += 1
            named = [o for o, frag in tp.OUTCOMES[leg].items() if frag in f1.reason]
            if f1.verdict == "fail":
                for o in named:
                    outcomes[leg][o] += 1
            rows.append({"doc_id": doc_id, "leg": leg, "verdict": f1.verdict,
                         "outcomes": named, "reason": f1.reason})
    return {"cycle_of_record": cycle_of_record(), "observations_from": source,
            "surfaces": len(groups), "catalog_bodies_missing": missing,
            "deterministic": deterministic,
            "distribution": {leg: dict(sorted(c.items())) for leg, c in dist.items()},
            "fail_outcomes": {leg: dict(sorted(c.items())) for leg, c in outcomes.items()},
            "d4_membership": d4_membership(params),
            "rows": rows}


def main(argv=None) -> int:
    sys.path.insert(0, str(REPO / "scripts"))
    out = exercise()
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    for r in out["rows"]:
        if r["verdict"] != "fail" or r["outcomes"] != ["no_product_record"]:
            print(f"{r['doc_id'][:48]:50s} {r['leg']} {r['verdict']:5s} {r['reason'][:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
