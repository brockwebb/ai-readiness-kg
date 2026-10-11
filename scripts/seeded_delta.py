#!/usr/bin/env python3
"""The seeded cycle's delta table. **No network, no model call, no re-judgement of record.**

`cc_tasks/2026-10-07_seed_known_locations_verify.md` decision 6: "For every body and object: the
recollection's declaration status, the seed sources that named a location, the verified status,
the existence verdict and the discoverability verdict. The headline count the report will need:
bodies and objects where the thing exists and a machine cannot find it from the product page."

Everything is read, never decided here:

* the recollection's status from the scheme-1 record part 2 wrote over (`targets.yaml` at
  `RECOLLECTION_COMMIT`): `declared` (a location read from the body's page), `not_declared`,
  `unreadable`, or `n/a` (the API's terms where no API was declared);
* the seed sources and statuses from both seed tables and `state/seed_verification_2026-10-11.json`;
* existence and discoverability from `RULE-A13-v1`'s own functions (`rule_a13._exists`,
  `rule_a13.per_object`) over each surface's stored Observations in `scan_2026-10-07_seeded`,
  under that payload's parameters. The A13 Findings in the payload are those same functions'
  output combined per surface; this splits them per object without judging anything new.

    /opt/anaconda3/bin/python3 scripts/seeded_delta.py [--check]

Writes `docs/research/2026-10-11_seeded_delta.md` and `state/seeded_delta_2026-10-11.json`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO))

from scan import load_params                                          # noqa: E402
from scan.model import Observation, params_hash                       # noqa: E402
from scan.rules import _existence as ex                               # noqa: E402
from scan.rules import rule_a13                                       # noqa: E402

TASK = "cc_tasks/2026-10-07_seed_known_locations_verify.md"
CYCLE = "scan_2026-10-07_seeded"
BEFORE, AFTER = "scan_2026-10-06_composite_c", "scan_2026-10-07_composite_d"
#: The commit before part 2 wrote scheme 2: `targets.yaml` there is the recollection's record.
RECOLLECTION_COMMIT = "512c1315"
LEGS = ["A2", "D1", "F4", "D4", "B1", "B4", "D3", "G4", "A9", "A13"]
OUT_MD = REPO / "docs" / "research" / "2026-10-11_seeded_delta.md"
OUT_JSON = REPO / "state" / "seeded_delta_2026-10-11.json"
#: object (A13's name) -> (the declaration/seed object, the recollection's unresolved role).
OBJECTS = {"api": ("api_base", "api_base"), "terms": ("api_terms", "api_terms"),
           "changelog": ("changelog", "changelog"), "inventory": ("inventory", None)}


def _load(name: str) -> dict:
    return json.loads((REPO / "state" / f"{name}.json").read_text(encoding="utf-8"))


def recollection_status(code: str, obj: str) -> str:
    text = subprocess.check_output(["git", "show", f"{RECOLLECTION_COMMIT}:assessment/harness/"
                                    "scan/targets.yaml"], cwd=REPO).decode()
    b = (yaml.safe_load(text)["declared_locations"]["bodies"]).get(code) or {}
    roles = {u["role"]: u.get("status", "unresolved") for u in b.get("unresolved") or []}
    api = b.get("api_base") or {}
    if obj == "api":
        return "declared" if api.get("url") else roles.get("api_base", "—")
    if obj == "terms":
        if api.get("terms_url"):
            return "declared"
        return roles.get("api_terms", "n/a" if not api.get("url") else "—")
    if obj == "changelog":
        return "declared" if b.get("changelog_urls") else roles.get("changelog", "—")
    inv = [e for e in b.get("inventory_urls") or [] if e.get("kind") == "data_json"]
    return "declared" if inv else "—"


def seeds_of(report: list, code: str, obj: str) -> tuple:
    """`(sources, statuses)` over the body's seeds of one object that are locations of it (a
    page searched for the object, `kind: page_to_read`, is not)."""
    sources, statuses = set(), Counter()
    seen = set()
    for r in report:
        if r["body"] != code or r["object"] != obj or r.get("kind") == "page_to_read":
            continue
        for s in r.get("seeded_from") or []:
            sources.add(s.split(":", 1)[0])
        if r["url"] not in seen:
            seen.add(r["url"])
            statuses[r["status"]] += 1
    return sorted(sources), dict(statuses)


def surfaces(payload: dict, params: dict) -> dict:
    """`{doc_id: (agency, [Observation] A13 reads)}` for every surface of the cycle."""
    by = defaultdict(list)
    for o in payload["observations_detail"]:
        if str(o.get("target_doc_id", "")).startswith("control:"):
            continue
        if o["leg"] in rule_a13.CONSUMES and not (
                o["leg"] == "link_probe" and (o.get("parsed") or {}).get("probe") == "link"):
            by[o["target_doc_id"]].append(Observation(**o))
    agency = {r["doc_id"]: r["agency"] for r in payload["matrix"]}
    return {d: (agency[d], obs) for d, obs in by.items()}


def leg_counts(payload: dict, docs: set) -> dict:
    out = {}
    for leg in LEGS:
        c = Counter(f["verdict"] for f in payload["findings_detail"]
                    if f["leg"] == leg and f["target_doc_id"] in docs)
        out[leg] = {v: c.get(v, 0) for v in ("pass", "fail", "error", "not_applicable")}
    return out


def build() -> dict:
    payload = _load(CYCLE)
    params = load_params()
    if params_hash(params) != payload["params_hash"]:
        raise SystemExit(f"REFUSING: params.yaml hashes to {params_hash(params)[:12]}…, not "
                         f"{CYCLE}'s {payload['params_hash'][:12]}…; the delta reads the "
                         f"cycle under the parameters it was judged with")
    report = json.loads((REPO / "state" / "seed_verification_2026-10-11.json").read_text(
        encoding="utf-8"))["seeds"]
    surf = surfaces(payload, params)
    rows, per_surface = [], []
    by_body = defaultdict(list)
    for doc, (code, obs) in sorted(surf.items()):
        each = rule_a13.per_object(obs, params)
        decl = ex.declared(obs)
        for name, (obj, _role) in OBJECTS.items():
            state, _ = rule_a13._exists(obs, decl, obj, params)
            per_surface.append({"body": code, "surface": doc, "object": name,
                                "exists": state, "discoverability": each[name]["verdict"],
                                "reason": each[name]["reason"]})
            by_body[(code, name)].append((state, each[name]["verdict"]))
    for (code, name), xs in sorted(by_body.items()):
        obj = OBJECTS[name][0]
        states = Counter(s for s, _ in xs)
        verdicts = Counter(v for _, v in xs)
        exists = ("yes" if states.get("yes") else "no" if states.get("no") == len(xs)
                  else "unknown")
        sources, statuses = seeds_of(report, code, obj)
        rows.append({"body": code, "object": name,
                     "recollection": recollection_status(code, name),
                     "seed_sources": sources, "seed_statuses": statuses,
                     "exists": exists, "surfaces": len(xs),
                     "discoverability": dict(verdicts),
                     "exists_unreachable_from_every_page": (
                         exists == "yes" and verdicts.get("fail", 0) == len(xs))})
    docs = {r["doc_id"] for r in payload["matrix"]}
    before, after = _load(BEFORE), _load(AFTER)
    head = {
        "pairs_exist": sum(1 for r in rows if r["exists"] == "yes"),
        "pairs_exist_unreachable_from_every_product_page": sum(
            1 for r in rows if r["exists_unreachable_from_every_page"]),
        "bodies_with_such_a_pair": len({r["body"] for r in rows
                                        if r["exists_unreachable_from_every_page"]}),
        "surface_object_pairs_exist_and_fail": sum(
            1 for s in per_surface if s["exists"] == "yes" and s["discoverability"] == "fail"),
        "surface_object_pairs_exist": sum(1 for s in per_surface if s["exists"] == "yes"),
    }
    return {"task": TASK, "cycle": CYCLE, "params_hash": payload["params_hash"],
            "recollection_commit": RECOLLECTION_COMMIT, "headline": head,
            "legs_before": {"cycle": BEFORE, "counts": leg_counts(before, docs)},
            "legs_after": {"cycle": AFTER, "counts": leg_counts(after, docs)},
            "rows": rows, "per_surface": per_surface}


def render(d: dict) -> str:
    h = d["headline"]
    lines = [
        "# The seeded cycle's delta: existence and discoverability per body and object",
        "",
        f"Generated by `scripts/seeded_delta.py` (`{d['task']}` decision 6) from "
        f"`state/{d['cycle']}.json` (params_hash `{d['params_hash'][:12]}…`), the seed tables "
        f"and `state/seed_verification_2026-10-11.json`. The recollection's status is "
        f"`targets.yaml` at `{d['recollection_commit']}`. Existence and discoverability are "
        f"`RULE-A13-v1`'s own `_exists` and `per_object` over each surface's stored "
        f"Observations; nothing is judged here. A13 is a candidate (DD-054): on the matrix, in "
        f"no level and no score.",
        "",
        "## Headline",
        "",
        f"* **{h['pairs_exist_unreachable_from_every_product_page']}** body × object pairs, in "
        f"**{h['bodies_with_such_a_pair']}** bodies, where the object exists and no product page "
        f"of the body reaches it (A13 `fail` for that object on every surface), of "
        f"{h['pairs_exist']} pairs where it exists.",
        f"* Per surface: {h['surface_object_pairs_exist_and_fail']} of "
        f"{h['surface_object_pairs_exist']} surface × object pairs where the object exists are "
        f"not reachable from that product page.",
        "",
        "## Per leg on the 46 surfaces, before and after (pass / fail / error / n/a)",
        "",
        f"| leg | `{d['legs_before']['cycle']}` | `{d['legs_after']['cycle']}` |",
        "|---|---|---|",
    ]
    fmt = lambda c: f"{c['pass']}/{c['fail']}/{c['error']}/{c['not_applicable']}"  # noqa: E731
    for leg in LEGS:
        b, a = d["legs_before"]["counts"][leg], d["legs_after"]["counts"][leg]
        lines.append(f"| {leg} | {fmt(b) if sum(b.values()) else '—'} | {fmt(a)} |")
    lines += ["", "## Per body and object", "",
              "Seed statuses count distinct locations (a page searched for the object is not "
              "one). Discoverability counts the body's surfaces by A13's per-object verdict.",
              "", "| body | object | recollection | seed sources | seed statuses | exists | "
              "discoverability (surfaces) |", "|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        st = ", ".join(f"{k} {v}" for k, v in sorted(r["seed_statuses"].items())) or "—"
        dv = ", ".join(f"{k} {v}" for k, v in sorted(r["discoverability"].items()))
        mark = " **(exists, unreachable)**" if r["exists_unreachable_from_every_page"] else ""
        lines.append(f"| {r['body']} | {r['object']} | {r['recollection']} | "
                     f"{', '.join(r['seed_sources']) or '—'} | {st} | {r['exists']} | "
                     f"{dv}{mark} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    d = build()
    md, js = render(d), json.dumps(d, indent=1, sort_keys=True) + "\n"
    if a.check:
        ok = OUT_MD.read_text(encoding="utf-8") == md and OUT_JSON.read_text(
            encoding="utf-8") == js
        print("seeded delta:", "CURRENT" if ok else "STALE")
        return 0 if ok else 1
    OUT_MD.write_text(md, encoding="utf-8")
    OUT_JSON.write_text(js, encoding="utf-8")
    print(json.dumps(d["headline"], indent=1))
    print(f"-> {OUT_MD.relative_to(REPO)}, {OUT_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
