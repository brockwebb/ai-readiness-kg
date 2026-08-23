#!/usr/bin/env python3
"""Gate candidate `shacl_conformance` (task 2026-08-23_trustgraph_benchmark, Phase 6).

Export the event log to RDF (benchmarks/trustgraph/export_projection_rdf.py), validate it
against the schema-generated SHACL shapes (airkg_shapes.ttl) with pySHACL, classify every
violation into the KNOWN classes declared in dixie_evidence.yaml::shacl_gate, and count the
violations outside them. The gate FIRES when unknown-class violations exceed
`threshold_unknown_violations` (0). Config is read, never adjusted (CLAUDE.md: thresholds are
operator decisions).

Known classes are matched by PREDICATE, not by count, so a new violation of a known shape
on an unexpected node still counts as unknown:
  dangling_cites_endpoint_untyped   sh:class on path airkg:cites whose value node carries no
                                    rdf:type -- a citation to a never-manifested Document
                                    (bulk-v1 closeout finding; edge_endpoint_validation gate).
  required_property_predates_schema sh:minCount on airkg:evidence_grade where the focus
                                    Claim's prov_schema_version is below the version that
                                    made it required (DD-010: required "under 0.3").

Positive control (`--mutate`): before validating, seed ONE bad-typed edge -- a `defines`
from a Concept to a Concept -- into the data graph. It must surface as an unknown-class
violation and fire the gate; if it does not, the gate is inert and the run fails loudly.

Off by default (`enabled: false`); `--force` evaluates anyway and reports. Exit codes:
0 pass / disabled, 2 gate fired, 3 positive control failed to fire.

Usage: python3 scripts/run_shacl_gate.py [--data projection.ttl] [--mutate] [--force]
                                         [--report out.json] [--no-export]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SH

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "benchmarks" / "trustgraph"))

from schema_to_owl import NS  # noqa: E402

CONFIG_PATH = REPO / "dixie_evidence.yaml"
EXAMPLES_PER_CLASS = 3


def load_gate_config(path: Path = CONFIG_PATH) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    gate = cfg.get("shacl_gate")
    if not gate:
        raise SystemExit(f"FATAL: {path} has no `shacl_gate` section")
    for key in ("enabled", "shapes", "known_violation_classes", "threshold_unknown_violations"):
        if key not in gate:
            raise SystemExit(f"FATAL: shacl_gate lacks required key {key!r}")
    return gate


# --- known-class predicates --------------------------------------------------------------

def _is_dangling_cites(data: Graph, res: dict) -> bool:
    return (res["component"] == "ClassConstraintComponent" and res["path"] == NS.cites
            and res["value"] is not None and data.value(res["value"], RDF.type) is None)


def _predates_required(versions_below: set[str]):
    def pred(data: Graph, res: dict) -> bool:
        if res["component"] != "MinCountConstraintComponent" or res["path"] != NS.evidence_grade:
            return False
        v = data.value(res["focus"], NS.prov_schema_version)
        return v is not None and str(v) in versions_below
    return pred


def build_classifiers(gate: dict) -> dict:
    out = {}
    for entry in gate["known_violation_classes"]:
        name = entry["name"]
        if name == "dangling_cites_endpoint_untyped":
            out[name] = _is_dangling_cites
        elif name == "required_property_predates_schema":
            out[name] = _predates_required(set(str(v) for v in entry["schema_versions_exempt"]))
        else:
            raise SystemExit(f"FATAL: known_violation_classes names {name!r} but no classifier implements it")
    return out


# --- validation --------------------------------------------------------------------------

def results_from(report: Graph) -> list[dict]:
    out = []
    for r in report.subjects(RDF.type, SH.ValidationResult):
        out.append({
            "shape": report.value(r, SH.sourceShape),
            "component": str(report.value(r, SH.sourceConstraintComponent)).split("#")[-1],
            "path": report.value(r, SH.resultPath),
            "focus": report.value(r, SH.focusNode),
            "value": report.value(r, SH.value),
            "message": str(report.value(r, SH.resultMessage) or ""),
        })
    return out


def _shape_label(shapes: Graph, shape) -> str:
    """Name a property shape by its parent node shape + path (blank nodes are unreadable).
    pySHACL copies shape nodes into the report graph with their identity preserved, so the
    parent lookup must happen in the SHAPES graph, where sh:property links live."""
    if isinstance(shape, URIRef):
        return shape.split("#")[-1]
    for parent in shapes.subjects(SH.property, shape):
        return f"{str(parent).split('#')[-1]}/{str(shapes.value(shape, SH.path)).split('#')[-1]}"
    return str(shape)


def evaluate(data: Graph, shapes: Graph, classifiers: dict) -> dict:
    from pyshacl import validate
    conforms, report, _text = validate(data, shacl_graph=shapes, inference="none",
                                       abort_on_first=False, meta_shacl=False)
    results = results_from(report)
    by_class: dict[str, int] = defaultdict(int)
    grouped: dict[tuple, dict] = {}
    unknown = []
    for res in results:
        cls = next((name for name, pred in classifiers.items() if pred(data, res)), None)
        key = (_shape_label(shapes, res["shape"]), res["component"], str(res["path"]).split("#")[-1], cls or "UNKNOWN")
        grp = grouped.setdefault(key, {"count": 0, "examples": []})
        grp["count"] += 1
        if len(grp["examples"]) < EXAMPLES_PER_CLASS:
            grp["examples"].append({"focus": str(res["focus"]), "value": str(res["value"]), "message": res["message"]})
        if cls is None:
            unknown.append(res)
        by_class[cls or "UNKNOWN"] += 1
    return {
        "conforms": bool(conforms),
        "violations_total": len(results),
        "violations_by_class": dict(by_class),
        "unknown_violations": len(unknown),
        "groups": [{"shape": k[0], "component": k[1], "path": k[2], "class": k[3], **v}
                   for k, v in sorted(grouped.items(), key=lambda kv: -kv[1]["count"])],
    }


def seed_mutation(data: Graph) -> dict:
    """Positive control: one `defines` edge Concept -> Concept (schema: Document -> Definition only)."""
    concepts = [s for s in data.subjects(RDF.type, NS.Concept)]
    if len(concepts) < 2:
        raise SystemExit("FATAL: positive control needs at least two Concept nodes")
    a, b = sorted(concepts, key=str)[:2]
    data.add((a, NS.defines, b))
    return {"edge": "defines", "from": str(a), "to": str(b), "from_type": "Concept", "to_type": "Concept"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=REPO / "benchmarks" / "trustgraph" / "projection.ttl")
    ap.add_argument("--no-export", action="store_true", help="validate --data as-is instead of re-exporting the event log")
    ap.add_argument("--mutate", action="store_true", help="positive control: seed one bad-typed edge into a scratch copy")
    ap.add_argument("--force", action="store_true", help="evaluate even when shacl_gate.enabled is false")
    ap.add_argument("--report", type=Path, default=None, help="write the evaluation as JSON")
    ap.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = ap.parse_args(argv)

    gate = load_gate_config(args.config)
    if not gate["enabled"] and not args.force:
        print("shacl_gate: disabled (enabled: false); pass --force to evaluate anyway")
        return 0

    if not args.no_export:
        from export_projection_rdf import export
        data, counts = export()
        args.data.parent.mkdir(parents=True, exist_ok=True)
        data.serialize(destination=str(args.data), format="turtle")
        print(f"exported {args.data}: {json.dumps(counts)}")
    else:
        data = Graph().parse(args.data, format="turtle")
    shapes = Graph().parse(REPO / gate["shapes"], format="turtle")
    classifiers = build_classifiers(gate)

    mutation = None
    if args.mutate:
        mutation = seed_mutation(data)   # in-memory scratch copy; the TTL on disk is untouched
        print(f"positive control seeded: {json.dumps(mutation)}")

    ev = evaluate(data, shapes, classifiers)
    ev["mutation"] = mutation
    ev["threshold_unknown_violations"] = gate["threshold_unknown_violations"]
    fired = ev["unknown_violations"] > gate["threshold_unknown_violations"]
    ev["gate_fired"] = fired
    if args.report:
        args.report.write_text(json.dumps(ev, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in ev.items() if k != "groups"}, indent=1))
    for grp in ev["groups"]:
        print(f"  {grp['count']:6d}  {grp['shape']}  {grp['component']}  {grp['path']}  -> {grp['class']}")

    if args.mutate:
        if not fired:
            print("POSITIVE CONTROL FAILED: seeded bad-typed edge did not fire the gate")
            return 3
        print("positive control OK: gate fired on the seeded edge")
        return 0
    return 2 if fired else 0


if __name__ == "__main__":
    sys.exit(main())
