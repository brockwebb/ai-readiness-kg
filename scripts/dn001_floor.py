#!/usr/bin/env python3
"""DN-001's citation floor over the evidence map. **Read-only, zero spend, no network beyond Neo4j.**

`cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards.md`
decision 3 asks for "the before and after floor count". DN-001 decision 1 states the floor for
the L0 report: every check whose result the report quotes reaches at least one admitted source
document (`AssessmentIndicator -[:EVIDENCED_BY]-> Document`, doc_id in `corpus/manifest.json`).
The concise report is written from `docs/evidence/claims.yaml`, so the floor here is the same
test applied to the claims file: a leg is QUOTED when a claim cites one of its Findings or one of
its Results, and the floor holds for that leg when `report_traceability.measure` finds a source.

Nothing is decided here. The leg of a Finding is read from the cycle of record's payload
(`state/<cycle>.json` `findings_detail`); the leg of a Result from its name
(`scan_<leg>_...` or `scan_l0_product_<leg>_...`); the source count from the one measurement in
`scripts/report_traceability.py`.

    /opt/anaconda3/bin/python3 scripts/dn001_floor.py [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

import report_traceability as RT                                    # noqa: E402

CLAIMS = REPO / "docs" / "evidence" / "claims.yaml"
#: `scan_a2_fail_<cycle>`, `scan_l0_product_d1_error_<cycle>`, `scan_l0_product_leg_rate_a2_...`
RESULT_LEG = re.compile(r"^scan_(?:l0_product_(?:leg_rate_)?)?([a-g]\d{1,2})_")


def quoted_legs(claims: dict, payload: dict) -> dict:
    """`{leg: [claim ids]}` for every leg a claim cites a Finding or Result of."""
    leg_of = {f["finding_id"]: f["leg"] for f in payload.get("findings_detail") or []}
    out: dict = {}
    for c in claims["claims"]:
        legs = set()
        for e in c.get("evidence") or []:
            if e["kind"] == "finding" and e["id"] in leg_of:
                legs.add(leg_of[e["id"]])
            elif e["kind"] == "result":
                # The evidence id is the Result's artifact_id; its name leads the note
                # (`build_evidence_map`: "<name>, value <v>, state <s>").
                m = RESULT_LEG.match((e.get("note") or "").split(",", 1)[0].strip()) or \
                    RESULT_LEG.match(e["id"])
                if m:
                    legs.add(m.group(1).upper())
        for leg in legs:
            out.setdefault(leg, []).append(c["id"])
    return {k: sorted(v) for k, v in sorted(out.items())}


def floor(session) -> dict:
    claims = yaml.safe_load(CLAIMS.read_text(encoding="utf-8"))
    cycle = claims["cycle_of_record"]
    payload = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    legs = quoted_legs(claims, payload)
    m = RT.measure(session, list(legs))
    rows = {leg: {"sources": m[leg].get("sources", 0),
                  "source_ids": sorted(m[leg].get("all_source_ids") or []),
                  "claims": legs[leg]} for leg in legs}
    below = sorted(l for l, r in rows.items() if not r["sources"])
    return {"cycle_of_record": cycle, "legs_quoted": len(rows),
            "legs_with_a_source": len(rows) - len(below), "legs_without_source": below,
            "claims_on_legs_without_source": sorted({c for l in below for c in rows[l]["claims"]}),
            "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    drv = get_neo4j_driver(cfg)
    try:
        with drv.session(database=cfg["neo4j"]["database"]) as s:
            out = floor(s)
    finally:
        drv.close()
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
