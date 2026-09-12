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

**The skeleton is the source of the AUTHORED cells, not of the whole record**
(`cc_tasks/2026-09-11_framework_single_writer.md`). Since the record was first generated it has
been written back to: 22 `MeasurementSpec` nodes and their `MEASURED_BY` edges, every
`measurement_status` promotion and its `measured_by` block, A12's adoption as a *candidate*
under DD-054 with its own construct and internal refs, the recorded spec decisions, and six
`counts` keys the skeleton never carried. Regenerating "the obvious way" dropped all of it
(`2026-09-11_a3_a10_sources_RESULT.md` §7). So this module no longer writes the file:

* `generate()` parses the skeleton and returns ONLY what the skeleton authors;
* `merge(generated, current)` lays that over the record on disk, keeping everything the
  skeleton does not author — see `AUTHORED_PROPS`, `AUTHORED_EDGE_TYPES` and the docstring
  there for the exact rule;
* `build(current)` is the two together, and `main` hands the result to
  `framework_writeback.save`, the one writer, which refuses to drop anything without
  `--force --reason` and puts the delta on the event.

`tests/test_framework_single_writer.py` asserts that regenerating from the current skeleton over
`HEAD` is a byte-for-byte no-op, and stops being one only when the skeleton changes.

The candidate table (`### Candidate indicators (not part of the framework)`, under §10 of the
skeleton) is NOT parsed. Its rows are minted by `add_candidate_indicator.py` and rendered by
`render_framework.render_candidate_table`; reading them here as criterion rows is exactly how
A12 was re-authored into criterion G with its rationale in the Status cell.

    /opt/anaconda3/bin/python3 scripts/build_framework_graph.py [--dry-run] [--out PATH] [--force --reason TEXT]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw                                    # noqa: E402

TASK = "cc_tasks/2026-09-06_freeze_and_framework_graph.md"
SCRIPT = "scripts/build_framework_graph.py"
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
    into the expected six cells.

    Stops at the candidate heading, the same cut `render_framework.skeleton_rows` makes: the
    candidate table's rows carry the same leading code cell as a criterion row, and criterion
    G's section (the last `CRITERIA` marker) otherwise runs to the end of the file and swallows
    them."""
    from render_framework import CANDIDATE_HEADING
    lines = text.split(CANDIDATE_HEADING, 1)[0].splitlines()
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


def generate() -> dict:
    """The record as the SKELETON alone authors it. Never written as-is over an existing
    record — see `merge`."""
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


#: Indicator properties the skeleton's six cells author. Every other property on an indicator
#: node (`measurement_status`, `measured_by`, `not_measured_reason`, `candidate_*`,
#: `recorded_by`, ...) is a write-back and is preserved from the record on disk. A key here
#: that `generate` no longer emits for a row (a `frontier`/`as_of` the Status cell dropped) is
#: dropped from the record too — the skeleton is authoritative for exactly this list.
AUTHORED_PROPS = frozenset({
    "code", "construct", "indicator", "type", "tier", "tier_raw", "status", "evidence_raw",
    "gap", "criterion_code", "g1_leg_of", "frontier", "as_of",
})
#: `generate` sets a starting value for these; the record's value, once written back, wins.
DEFAULT_ONLY_PROPS = frozenset({"measurement_status"})
#: Edge types the skeleton authors, from a node the skeleton authors. `MEASURED_BY` is the
#: spec builder's; an authored type FROM a preserved node (A12's refs) or TO a preserved node
#: (crit:A -> A12's construct) is a write-back and stays.
AUTHORED_EDGE_TYPES = frozenset({"DECOMPOSES_INTO", "EVIDENCED_BY", "EVIDENCED_BY_INTERNAL"})
#: Top-level keys `generate` owns. `counts` is the shared writer's (`recount`); anything else
#: at the top level (`counts_basis`, a future key) is preserved.
AUTHORED_TOP = ("generated_from", "generated_by", "task", "schema_epoch", "unparsed_rows",
                "evidence_doc_ids_not_in_manifest")


def _merge_node(cur: dict, gen: dict) -> dict:
    """Authored properties from `gen`, everything else from `cur`, in `cur`'s key order so an
    unchanged record serialises to the same bytes."""
    cp, gp = cur.get("properties") or {}, gen.get("properties") or {}
    props = {}
    for k, v in cp.items():
        if k in AUTHORED_PROPS:
            if k in gp:
                props[k] = gp[k]
            # else: the skeleton stopped authoring it for this row; dropped
        else:
            props[k] = v
    for k, v in gp.items():
        if k not in props and (k in AUTHORED_PROPS or k in DEFAULT_ONLY_PROPS):
            props[k] = v
    return {**cur, "labels": gen["labels"], "properties": props}


def merge(generated: dict, current: dict | None) -> dict:
    """Lay what the skeleton authors over the record on disk; keep everything it does not.

    * a node the skeleton authors (criterion, construct, non-candidate indicator) takes its
      authored properties from `generated` and keeps its write-backs;
    * a node the skeleton does not author (`MeasurementSpec`, a candidate indicator and its
      construct) is kept whole;
    * an authored edge is one of `AUTHORED_EDGE_TYPES` whose `from` is a generated node and
      whose `to` is not a preserved node; it is present iff the skeleton emits it. Every
      other edge is kept whole. An authored edge the skeleton no longer emits is therefore
      dropped here — and `framework_writeback.save` refuses that drop unless it is forced
      with a reason, which is the whole point of the arrangement;
    * order is the record's; new authored nodes and edges are appended.
    """
    if current is None:
        return generated
    gen_nodes = {n["id"]: n for n in generated["nodes"]}
    cur_ids = {n["id"] for n in current["nodes"]}
    preserved_ids = cur_ids - set(gen_nodes)
    nodes = [_merge_node(n, gen_nodes[n["id"]]) if n["id"] in gen_nodes else n
             for n in current["nodes"]]
    nodes += [n for n in generated["nodes"] if n["id"] not in cur_ids]

    def authored(e: dict) -> bool:
        return (e["type"] in AUTHORED_EDGE_TYPES and e["from"] in gen_nodes
                and e["to"] not in preserved_ids)

    gen_edges = {fw._edge_key(e): e for e in generated["edges"]}
    edges = []
    for e in current["edges"]:
        k = fw._edge_key(e)
        if authored(e):
            if k in gen_edges:
                edges.append({**e, **gen_edges[k]})
            # else: the skeleton no longer carries it; `save` refuses the drop unless forced
        else:
            edges.append(e)
    have = {fw._edge_key(e) for e in edges}
    edges += [e for e in generated["edges"] if fw._edge_key(e) not in have]

    out = dict(current)
    for k in AUTHORED_TOP:
        out[k] = generated[k]
    out["nodes"], out["edges"] = nodes, edges
    return out


def build(current: dict | None = None) -> dict:
    """`generate()` merged over `current` (the record on disk, or None for a first build)."""
    return merge(generate(), current)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    out = Path(a.out)
    g = build(fw.load(out))
    out.parent.mkdir(parents=True, exist_ok=True)
    # Through the one writer: it recounts, refuses a drop that is not forced with a reason,
    # writes, and appends the `framework_writeback` event carrying the delta.
    ev = fw.save(g, script=SCRIPT, task=TASK, changes={"regenerated_from": g["generated_from"]},
                 dry_run=a.dry_run, path=out, **fw.force_kwargs(a))
    print(json.dumps({"counts": g["counts"],
                      "unparsed_rows": g["unparsed_rows"],
                      "evidence_doc_ids_not_in_manifest": g["evidence_doc_ids_not_in_manifest"][:10],
                      "unmatched_total": len(g["evidence_doc_ids_not_in_manifest"]),
                      "delta": ev["delta_summary"],
                      "written": ev["written"], "unchanged": ev.get("unchanged", False),
                      "event_id": ev.get("event_id")}, indent=1))
    print(f"-> {out.resolve().relative_to(REPO) if out.resolve().is_relative_to(REPO) else out}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
