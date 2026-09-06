#!/usr/bin/env python3
"""Parse the operationalization skeleton into the framework graph JSON. **Zero model spend.**

Task `cc_tasks/2026-09-06_freeze_and_framework_graph.md` §2.2. Mechanical: seven markdown
tables in, a node/edge JSON out. **Nothing is invented** — a cell that cannot be parsed is
listed in the RESULT rather than guessed, and a `doc_id` in an Evidence cell becomes an
`EVIDENCED_BY` edge **only if `corpus/manifest.json` holds it**; otherwise the cell's own
stated reason is kept on the indicator as a gap marker.

Schema epoch v0.4.0's `assessment_layer` (DD-051) governs the labels. They are deliberately
outside the parser's `node_types`/`edge_types` whitelist: the assessment layer is AUTHORED,
and an extraction able to mint an `AssessmentIndicator` would let a source document rewrite
the framework measuring it.

    /opt/anaconda3/bin/python3 scripts/build_framework_graph.py [--out framework/ai_readiness_framework.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
SKELETON = REPO / "docs" / "crosswalk" / "usafacts_operationalization_skeleton.md"
MANIFEST = REPO / "corpus" / "manifest.json"
OUT = REPO / "framework" / "ai_readiness_framework.json"

#: The seven criterion sections, in document order, with the letter each table's codes carry.
#: Read from the headings rather than hardcoded counts, so a table gaining a row is picked up.
CRITERIA = [
    ("A", "ACCESSIBLE", "## 2. Criterion A"),
    ("B", "UNDERSTANDABLE", "## 3. Criterion B"),
    ("C", "ACCURATE", "## 4. Criterion C"),
    ("D", "OPEN", "## 5. Criterion D"),
    ("E", "TEVV loop", "## 5b. Cross-cutting"),
    ("F", "release engineering", "## 5c. Cross-cutting"),
    ("G", "FSS-derived constructs", "## 5d. FSS-derived constructs"),
]

#: A `doc_id` reference inside an Evidence cell: a backticked token that is not a bare word of
#: prose. The manifest decides whether it is real; this only finds candidates.
_DOCID = re.compile(r"`([a-z0-9][a-z0-9._-]{6,})`")
#: An internal reference: `DD-033`, `internal: ...`, a repo path.
_INTERNAL = re.compile(r"\b(DD-\d{3})\b|`(assessment/[^`]+|cc_tasks/[^`]+|docs/[^`]+)`")
_ROW = re.compile(r"^\|\s*(?P<code>[A-G]\d{1,2})\s*\|(?P<rest>.*)\|\s*$")


def cells(rest: str) -> list:
    """Split a table row body on unescaped pipes, keeping cell text verbatim."""
    return [c.strip() for c in rest.split("|")]


def parse(text: str) -> tuple:
    """(rows, unparsed) — one dict per indicator row, plus any `| Xn |` line we could not split
    into the expected six cells."""
    lines = text.splitlines()
    bounds = []
    for letter, name, marker in CRITERIA:
        i = next((k for k, l in enumerate(lines) if l.startswith(marker)), None)
        if i is None:
            raise SystemExit(f"FATAL: heading not found: {marker!r}")
        bounds.append((letter, name, i))
    bounds.sort(key=lambda x: x[2])
    rows, unparsed = [], []
    for n, (letter, name, start) in enumerate(bounds):
        end = bounds[n + 1][2] if n + 1 < len(bounds) else len(lines)
        # the criterion's italic anchor line, where the skeleton has one
        anchor = next((l.strip("*") for l in lines[start:end] if l.startswith("*USAFacts anchor")
                       or l.startswith("*Cross-cutting")), "")
        for line in lines[start:end]:
            m = _ROW.match(line)
            if not m:
                continue
            c = cells(m.group("rest"))
            if len(c) != 6:
                unparsed.append({"criterion": letter, "line": line[:160],
                                 "reason": f"{len(c)} cells, expected 6"})
                continue
            construct, indicator, typ, evidence, tier, status = c
            rows.append({"code": m.group("code"), "criterion": letter,
                         "criterion_name": name, "criterion_anchor": anchor,
                         "construct": construct, "indicator": indicator, "type": typ,
                         "evidence_raw": evidence, "tier": tier, "status": status})
    return rows, unparsed


def split_g1(rows: list) -> list:
    """G1 is TWO indicators under one construct (DD-036's two-leg rule), and the skeleton
    carries them in one cell because a markdown table has one row per code. Splitting here is
    the only structural change the parser makes, and it is the one the protocol requires."""
    out = []
    for r in rows:
        if r["code"] != "G1":
            out.append(r)
            continue
        text = r["indicator"]
        for leg, marker, typ in (("G1-D", "**G1-D (declared)**", "AUTO"),
                                 ("G1-O", "**G1-O (observed)**", "EVAL")):
            i = text.find(marker)
            j = text.find("**G1-O (observed)**") if leg == "G1-D" else len(text)
            body = text[i:j].strip() if i >= 0 else text
            out.append({**r, "code": leg, "indicator": body, "type": typ,
                        "g1_leg_of": "G1",
                        "tier": "`public`" if leg == "G1-D" else "`paid`"})
    return out


def evidence_edges(row: dict, manifest_ids: set) -> tuple:
    """(corpus doc_ids, internal refs, gap_reason). A `doc_id` becomes an edge only when the
    manifest holds it; otherwise the cell's own words are kept."""
    raw = row["evidence_raw"]
    cands = _DOCID.findall(raw)
    real = [d for d in dict.fromkeys(cands) if d in manifest_ids]
    internal = sorted({m[0] or m[1] for m in _INTERNAL.findall(raw) if any(m)})
    gap = None
    if "**gap**" in raw or raw.strip().lower().startswith("gap"):
        gap = re.sub(r"\s+", " ", raw).strip()
    return real, internal, gap


def build() -> dict:
    text = SKELETON.read_text(encoding="utf-8")
    rows, unparsed = parse(text)
    rows = split_g1(rows)
    manifest_ids = set(json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"])

    nodes, edges = [], []
    seen_constructs = {}
    for letter, name, _ in CRITERIA:
        anchor = next((r["criterion_anchor"] for r in rows if r["criterion"] == letter), "")
        nodes.append({"id": f"crit:{letter}", "labels": ["AssessmentCriterion"],
                      "properties": {"code": letter, "name": name, "anchor": anchor}})
    unmatched_docids = []
    for r in rows:
        ckey = f"con:{r['criterion']}:{re.sub(r'[^a-z0-9]+', '-', r['construct'].lower()).strip('-')[:60]}"
        if ckey not in seen_constructs:
            seen_constructs[ckey] = True
            nodes.append({"id": ckey, "labels": ["AssessmentConstruct"],
                          "properties": {"name": r["construct"], "criterion_code": r["criterion"]}})
            edges.append({"from": f"crit:{r['criterion']}", "type": "DECOMPOSES_INTO", "to": ckey})
        iid = f"ind:{r['code']}"
        real, internal, gap = evidence_edges(r, manifest_ids)
        for d in _DOCID.findall(r["evidence_raw"]):
            if d not in manifest_ids and d not in [u["doc_id"] for u in unmatched_docids]:
                unmatched_docids.append({"indicator": r["code"], "doc_id": d})
        props = {"code": r["code"], "construct": r["construct"], "indicator": r["indicator"],
                 "type": r["type"],
                 # Two fields, because they answer two questions. `tier` is the ENUM the
                 # schema declares and the progress model groups on; `tier_raw` is the cell
                 # verbatim, which the renderer needs and which is not always just the enum —
                 # A11's cell is "`agency_instrumented` (observed leg requires edge logs;
                 # declared leg stays `public`)", and re-wrapping a stripped version of that
                 # in backticks is how the first round trip failed.
                 "tier": (re.search(r"`([a-z_]+)`", r["tier"]).group(1)
                          if re.search(r"`([a-z_]+)`", r["tier"]) else r["tier"].strip("` ")),
                 "tier_raw": r["tier"], "status": r["status"],
                 "evidence_raw": r["evidence_raw"],
                 "measurement_status": "measured" if r["code"] in ("G1-D", "G1-O") else "specified",
                 "gap": gap, "criterion_code": r["criterion"]}
        if r.get("g1_leg_of"):
            props["g1_leg_of"] = r["g1_leg_of"]
        m = re.search(r"as_of\s+(\d{4}-\d{2})", r["status"] + " " + r["indicator"])
        if m:
            props["frontier"] = True
            props["as_of"] = m.group(1)
        nodes.append({"id": iid, "labels": ["AssessmentIndicator"], "properties": props})
        edges.append({"from": ckey, "type": "DECOMPOSES_INTO", "to": iid})
        for d in real:
            edges.append({"from": iid, "type": "EVIDENCED_BY", "to": f"doc:{d}",
                          "properties": {"doc_id": d}})
        for ref in internal:
            edges.append({"from": iid, "type": "EVIDENCED_BY_INTERNAL", "to": f"internal:{ref}",
                          "properties": {"artifact_path": ref}})
    return {"generated_from": str(SKELETON.relative_to(REPO)),
            "generated_by": "scripts/build_framework_graph.py",
            "task": TASK, "schema_epoch": "0.4.0",
            "counts": {"criteria": len(CRITERIA), "constructs": len(seen_constructs),
                       "indicators": sum(1 for n in nodes if "AssessmentIndicator" in n["labels"]),
                       "evidenced_by": sum(1 for e in edges if e["type"] == "EVIDENCED_BY"),
                       "evidenced_by_internal": sum(1 for e in edges if e["type"] == "EVIDENCED_BY_INTERNAL"),
                       "gaps": sum(1 for n in nodes if n["properties"].get("gap"))},
            "unparsed_rows": unparsed,
            "evidence_doc_ids_not_in_manifest": unmatched_docids,
            "nodes": nodes, "edges": edges}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    g = build()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(g, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"counts": g["counts"],
                      "unparsed_rows": g["unparsed_rows"],
                      "evidence_doc_ids_not_in_manifest": g["evidence_doc_ids_not_in_manifest"][:10],
                      "unmatched_total": len(g["evidence_doc_ids_not_in_manifest"])}, indent=1))
    print(f"-> {Path(a.out).resolve().relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
