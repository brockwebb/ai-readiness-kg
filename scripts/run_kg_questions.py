#!/usr/bin/env python3
"""Five research questions asked of the knowledge graph, graded. **Zero spend, no network.**

`cc_tasks/2026-10-02_kg_research_questions.md`, under DN-009 decisions 2 and 8 (the corpus is
the first place a claim is searched). A decision maker's questions of the literature review,
each treated as a test: the graph answers it (`answered`), answers part of it (`partial`), or
cannot (`cannot_answer`), and the grade, its reason and what would close it are computed here
from counts the queries return, so a re-run grades the same way and a changed graph changes the
grade rather than a sentence somebody forgot to edit.

    scripts/run_kg_questions.py            write docs/evidence/kg_questions.{yaml,md} (needs Neo4j)
    scripts/run_kg_questions.py --check    re-run into memory; exit 1 on drift, exit 2 when the
                                           corpus epoch moved under the stored answers

**Sources.** Q1 to Q4 ask the corpus layer (Definition, Instrument, Measure, Concept, Document),
which only Neo4j holds, through `mcp/airkg_tools.Graph` — the MCP server's own driver, credential
resolver, database guard and read transactions. Q5 is a framework question and is answered from
`framework/ai_readiness_framework.json`, the record, never from its projection: that is the MCP's
decision 3 (`mcp/airkg_tools.py` module docstring). The projection gate (DD-057) is recomputed on
every run and written into the file, so a reader can see whether the graph and the record agreed.

**Prior art.** The questions are competency questions in the sense of Grüninger and Fox (1995),
as `assessment/cq/cq_set_v2.yaml` already uses them; Q1's text net is CQ-02's rule, Q2's
construct vocabulary is CQ-08's ten framework construct names (pre-registered at `369d717`,
before any answer was seen), and Q3 is CQ-15 re-asked over Q1's set.

**Citation standard (task decision 3).** Every row carries `doc_id`, `locator` and
`grounding_span_id`. The graph has no separate span identifier: the grounding span is a property
of the node that carries it, so the span's id is that node's `key` (`<doc_id>::<local id>`), and
it counts as an extraction's span only when the node also carries `prov_extraction_event_id`.
A node asserted by another route (a curated OCR definition, say) has a key but no extraction
event, and its row is `partial`. A row with any of the three null is `complete: false`.

**Idempotence.** Nothing reads a clock, every collection is sorted, `yaml.safe_dump` is called
with fixed options, and `--check` is a byte-for-byte comparison of both files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for p in ("", "scripts", "mcp"):
    sys.path.insert(0, str(REPO / p))

import yaml  # noqa: E402

OUT_DIR = REPO / "docs" / "evidence"
OUT_YAML = OUT_DIR / "kg_questions.yaml"
OUT_MD = OUT_DIR / "kg_questions.md"
RECORD = REPO / "framework" / "ai_readiness_framework.json"
RECORD_PATH = "framework/ai_readiness_framework.json"
TASK = "cc_tasks/2026-10-02_kg_research_questions.md"
GENERATOR = "scripts/run_kg_questions.py"
SCHEMA_VERSION = 1
GRADES = ("answered", "partial", "cannot_answer")
CITATION_FIELDS = ("doc_id", "locator", "grounding_span_id")

#: Task decision 1: "under 15 words quoted, the rest by locator".
QUOTE_MAX_WORDS = 14
#: Read cap per query. The MCP's own cap is 200 rows (`airkg_guard.MAX_ROWS`); these queries are
#: bounded by their WHERE clauses, and a result at the cap is refused below rather than truncated.
READ_CAP = 5000

#: Q1's selection rule, on the Definition's `term`: the defined thing is a readiness or
#: ready-state FOR AI. Lexical and case-insensitive; the corpus spells it "AI-ready", "AI ready",
#: "AI-readiness", "AI readiness", "readiness for AI" and "ready for AI".
Q1_TERM_RX = (r".*\b(ai|artificial intelligence)[- ]read(y|iness)\b.*",
              r".*\bread(y|iness) for (ai|artificial intelligence)\b.*")
#: A term the rule catches that names an assessment, index, inspector or methodology is an
#: instrument's name, not a definition of readiness; it is listed apart and belongs to Q4.
Q1_INSTRUMENT_NAME_RX = r"\b(assessment|self-assessment|index|inspector|methodology)\b"

#: Q2's construct vocabulary: CQ-08's ten framework construct names (assessment/cq/cq_set_v2.yaml,
#: pre-registered at 369d717), each with the morphological stem that finds it in prose. Stems are
#: inflections of the name only — no synonyms, which would be this script's judgement.
Q2_CONSTRUCT_STEMS = (
    ("uncertainty", r"\buncertain"),
    ("provenance", r"\bprovenance"),
    ("license", r"\blicen[cs]"),
    ("revision", r"\brevis"),
    ("timeliness", r"\btimel(y|iness)"),
    ("discoverability", r"\bdiscoverab"),
    ("machine-readable", r"\bmachine[- ]readab"),
    ("semantic consistency", r"\bsemantic(ally)?[- ]consisten"),
    ("authority", r"\bauthorit(y|ative)"),
    ("disclosure", r"\bdisclos"),
)

#: Q4's selection rule, on the Instrument's `name`.
Q4_NAME_RX = r".*(readiness|ai-ready|ai ready).*"


# ------------------------------------------------------------------------------- helpers

def quote(span: str | None) -> str | None:
    """The first QUOTE_MAX_WORDS words of a span, whitespace collapsed; '…' marks a cut."""
    if not span:
        return None
    words = span.split()
    q = " ".join(words[:QUOTE_MAX_WORDS])
    return q + (" …" if len(words) > QUOTE_MAX_WORDS else "")


def cite(n: dict) -> dict:
    """The three citation fields of a corpus node, and whether all three are present."""
    ev = n.get("prov_extraction_event_id")
    row = {"doc_id": n.get("doc_id"),
           "locator": n.get("location") or None,
           "grounding_span_id": n.get("key") if ev else None,
           "extraction_event_id": ev}
    row["complete"] = all(row[k] for k in CITATION_FIELDS)
    return row


def read(graph, cypher: str, **params) -> list:
    rows, truncated = graph.read(cypher, limit=READ_CAP, **params)
    if truncated:
        raise SystemExit(f"FATAL: a query returned more than {READ_CAP} rows; widen READ_CAP "
                         f"deliberately rather than answer from a truncated result:\n{cypher}")
    return rows


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def epoch(graph) -> dict:
    """What the stored answers are answers OF. `--check` compares byte for byte only while this
    is unchanged; a moved epoch is a new question, not drift."""
    docs = read(graph, "MATCH (d:Document) WHERE d.doc_id IS NOT NULL "
                       "RETURN d.doc_id AS id, coalesce(d.content_hash, '') AS h ORDER BY id")
    fp = hashlib.sha256("\n".join(f"{r['id']}\t{r['h']}" for r in docs).encode()).hexdigest()
    counts = read(graph, "MATCH (d:Definition) WITH count(d) AS defs "
                         "MATCH (i:Instrument) RETURN defs, count(i) AS instruments")[0]
    return {"documents": len(docs), "documents_sha256": fp,
            "definitions": counts["defs"], "instruments": counts["instruments"],
            "framework_record_sha256": sha256_file(RECORD)}


# ------------------------------------------------------------------------------- Q1

Q1_CYPHER = """
MATCH (d:Definition)
WHERE toLower(coalesce(d.term, '')) =~ $rx0 OR toLower(coalesce(d.term, '')) =~ $rx1
OPTIONAL MATCH (doc:Document)-[:DEFINES]->(d)
RETURN properties(d) AS p, doc IS NOT NULL AS defines_edge
"""

#: CQ-02's net, widened to the same spellings: definitions of OTHER terms whose text mentions
#: AI readiness. Reported as a count and keys, never as definitions of the term.
Q1_TEXT_NET_CYPHER = """
MATCH (d:Definition)
WHERE (toLower(d.verbatim_text) =~ $trx0 OR toLower(d.verbatim_text) =~ $trx1)
  AND NOT (toLower(coalesce(d.term, '')) =~ $rx0 OR toLower(coalesce(d.term, '')) =~ $rx1)
RETURN d.key AS key, d.term AS term ORDER BY key
"""


def q1(graph) -> tuple:
    params = {"rx0": Q1_TERM_RX[0], "rx1": Q1_TERM_RX[1]}
    rows, instrument_names = [], []
    for r in read(graph, Q1_CYPHER, **params):
        p = r["p"]
        row = {"term": p.get("term"), **cite(p),
               "normative_status": p.get("normative_status"),
               "defines_edge": bool(r["defines_edge"]),
               "quote": quote(p.get("grounding_span")),
               "node_key": p.get("key")}
        if re.search(Q1_INSTRUMENT_NAME_RX, (p.get("term") or "").lower()):
            instrument_names.append(row)
        else:
            rows.append(row)
    rows.sort(key=lambda x: x["node_key"])
    instrument_names.sort(key=lambda x: x["node_key"])
    net = read(graph, Q1_TEXT_NET_CYPHER, **params,
               trx0="(?s)" + Q1_TERM_RX[0], trx1="(?s)" + Q1_TERM_RX[1])
    docs = sorted({r["doc_id"] for r in rows})
    incomplete = [r for r in rows if not r["complete"]]
    if not rows:
        grade, reason = "cannot_answer", "no Definition's term matches the selection rule"
    elif incomplete or len(docs) < 2:
        grade = "partial"
        reason = (f"{len(rows)} definitions from {len(docs)} documents; "
                  f"{len(incomplete)} row(s) lack a citation field: "
                  + "; ".join(f"`{r['node_key']}` has no extraction event "
                              f"(defines_edge={str(r['defines_edge']).lower()})"
                              for r in incomplete))
    else:
        grade, reason = "answered", (f"{len(rows)} definitions from {len(docs)} documents, every "
                                     f"row with all three citation fields")
    to_close = ([f"stamp the asserting event's id on the {len(incomplete)} non-extraction "
                 f"Definition node(s) at projection, and write their DEFINES edge, so a curated "
                 f"definition cites like an extracted one"] if incomplete else [])
    return {
        "id": "Q1",
        "question": "What definitions of AI readiness and of AI-ready data exist in the corpus?",
        "grade": grade, "reason": reason, "to_close": to_close,
        "route": "neo4j: scripts/run_kg_questions.py via mcp/airkg_tools.Graph (read transactions)",
        "selection": {"label": "Definition", "property": "term", "regex_any": list(Q1_TERM_RX),
                      "instrument_names_listed_apart": Q1_INSTRUMENT_NAME_RX},
        "counts": {"definitions": len(rows), "documents": len(docs),
                   "rows_incomplete": len(incomplete),
                   "instrument_names_listed_apart": len(instrument_names),
                   "text_net_other_terms": len(net)},
        "rows": rows,
        "instrument_names": instrument_names,
        "text_net_other_terms": [{"key": r["key"], "term": r["term"]} for r in net],
    }, rows


# ------------------------------------------------------------------------------- Q2

Q2_STRUCTURE_CYPHER = """
OPTIONAL MATCH (c:Construct) WITH count(c) AS constructs
OPTIONAL MATCH (:Construct)-[g:GROUNDS]->(:Definition) WITH constructs, count(g) AS grounds
OPTIONAL MATCH (d:Definition)-[x]-(k:Concept)
RETURN constructs, grounds, count(x) AS definition_concept_edges
"""


def q2(graph, q1_rows: list) -> dict:
    s = read(graph, Q2_STRUCTURE_CYPHER)[0]
    keys = [r["node_key"] for r in q1_rows]
    texts = {r["key"]: r["t"] for r in read(
        graph, "MATCH (d:Definition) WHERE d.key IN $keys "
               "RETURN d.key AS key, d.verbatim_text AS t", keys=keys)}
    names = [n for n, _ in Q2_CONSTRUCT_STEMS]
    rows, by_construct = [], {n: [] for n in names}
    for r in q1_rows:
        t = (texts.get(r["node_key"]) or "").lower()
        named = [n for n, rx in Q2_CONSTRUCT_STEMS if re.search(rx, t)]
        for n in named:
            by_construct[n].append(r["node_key"])
        rows.append({"term": r["term"], **{k: r[k] for k in (*CITATION_FIELDS, "complete")},
                     "node_key": r["node_key"], "names": named,
                     "omits": [n for n in names if n not in named]})
    structural = s["constructs"] + s["grounds"] + s["definition_concept_edges"]
    if structural:
        grade, reason = "answered", "the graph links definitions to constructs"
    else:
        grade = "partial"
        reason = (f"the graph holds no edge from any Definition to any construct: "
                  f"{s['constructs']} `Construct` nodes, {s['grounds']} `GROUNDS` edges, "
                  f"{s['definition_concept_edges']} Definition–Concept edges. The rows are a "
                  f"lexical match of CQ-08's ten framework construct names against each "
                  f"definition's verbatim text, computed by this script, not held by the graph")
    shared = sorted(n for n in names if len(by_construct[n]) >= 2)
    return {
        "id": "Q2",
        "question": "What do the definitions share, and where do they differ, by construct?",
        "grade": grade, "reason": reason,
        "to_close": ["extract `grounds` (Construct -> Definition) edges, or promote Concepts to "
                     "Constructs per schema §Construct, so a definition's components are graph "
                     "edges and not a string match"] if not structural else [],
        "route": "neo4j: scripts/run_kg_questions.py via mcp/airkg_tools.Graph (read transactions)",
        "structure": dict(s),
        "vocabulary": {"source": "assessment/cq/cq_set_v2.yaml CQ-08 (pre-registered at 369d717)",
                       "stems": {n: rx for n, rx in Q2_CONSTRUCT_STEMS}},
        "counts": {"definitions": len(rows),
                   "naming_none": sum(1 for r in rows if not r["names"]),
                   "constructs_named_by_two_or_more": len(shared)},
        "by_construct": {n: sorted(by_construct[n]) for n in names},
        "rows": rows,
    }


# ------------------------------------------------------------------------------- Q3

Q3_CYPHER = """
MATCH (a)-[r:CONFLICTS_WITH]->(b)
RETURN labels(a)[0] AS label, properties(a) AS a, properties(b) AS b,
       r.prov_method AS method
"""


def q3(graph, q1_rows: list) -> dict:
    q1_keys = {r["node_key"] for r in q1_rows}
    edges = read(graph, Q3_CYPHER)
    rows, cross_doc, touching = [], 0, 0
    for e in sorted(edges, key=lambda x: (x["a"].get("key") or "", x["b"].get("key") or "")):
        a, b = e["a"], e["b"]
        same_doc = a.get("doc_id") == b.get("doc_id")
        cross_doc += 0 if same_doc else 1
        hit = a.get("key") in q1_keys or b.get("key") in q1_keys
        touching += 1 if hit else 0
        ca, cb = cite(a), cite(b)
        rows.append({"label": e["label"],
                     "doc_id": [ca["doc_id"], cb["doc_id"]],
                     "locator": [ca["locator"], cb["locator"]],
                     "grounding_span_id": [ca["grounding_span_id"], cb["grounding_span_id"]],
                     "complete": ca["complete"] and cb["complete"],
                     "same_document": same_doc, "touches_q1_definition": hit,
                     "about": [a.get("term") or a.get("claim_text"),
                               b.get("term") or b.get("claim_text")],
                     "prov_method": e["method"]})
    n_def = sum(1 for r in rows if r["label"] == "Definition")
    if touching:
        grade, reason = "answered", f"{touching} conflict edge(s) touch a Q1 definition"
    else:
        grade = "cannot_answer"
        reason = (f"the graph has a conflict representation (`CONFLICTS_WITH`, kg/schema.yaml "
                  f"`conflicts_with`, symmetric, Definition<->Definition and Claim<->Claim) and "
                  f"holds {len(rows)} such edges ({n_def} between Definitions); none touches the "
                  f"{len(q1_keys)} Q1 definitions and {cross_doc} join two documents. Conflicts "
                  f"were extracted one document at a time, so two documents' definitions of AI "
                  f"readiness cannot meet on an edge: the empty answer is a property of the "
                  f"extraction, never evidence that the definitions agree")
    return {
        "id": "Q3",
        "question": "Do any definitions conflict?",
        "grade": grade, "reason": reason,
        "to_close": ["a cross-document pairwise pass over the Q1 set that writes "
                     "`CONFLICTS_WITH` between Definitions of different documents, each edge "
                     "carrying both grounding spans, the conflict kind (scope, necessary "
                     "condition, or object of readiness) and its adjudicator — the shape "
                     "fss-policy-kg's adjudicated CONFLICTS_WITH overlay already has"]
                    if not touching else [],
        "route": "neo4j: scripts/run_kg_questions.py via mcp/airkg_tools.Graph (read transactions)",
        "counts": {"conflict_edges": len(rows), "between_definitions": n_def,
                   "cross_document": cross_doc, "touching_q1": touching},
        "rows": rows,
    }


# ------------------------------------------------------------------------------- Q4

Q4_CYPHER = """
MATCH (i:Instrument) WHERE toLower(i.name) =~ $rx
OPTIONAL MATCH (i)-[:MEASURES]->(c:Concept)
WITH i, collect(DISTINCT c.name) AS direct
OPTIONAL MATCH (i)-[:USES_MEASURE]->(m:Measure)
OPTIONAL MATCH (m)-[:MEASURES]->(mc:Concept)
RETURN properties(i) AS p, direct, count(DISTINCT m) AS measures,
       collect(DISTINCT mc.name) AS via_measures
"""

Q4_STRUCTURE_CYPHER = """
OPTIONAL MATCH (:Instrument)-[o:OPERATIONALIZES]->() WITH count(o) AS operationalizes
OPTIONAL MATCH (:Framework)-[f:OPERATIONALIZED_BY]->(:Instrument)
RETURN operationalizes, count(f) AS operationalized_by
"""


def q4(graph) -> dict:
    s = read(graph, Q4_STRUCTURE_CYPHER)[0]
    rows = []
    for r in read(graph, Q4_CYPHER, rx=Q4_NAME_RX):
        p = r["p"]
        rows.append({"instrument": p.get("name"), **cite(p), "node_key": p.get("key"),
                     "owner": p.get("owner"), "year": p.get("year"),
                     "measures": r["measures"],
                     "concepts_measured": sorted({x for x in r["direct"] if x}),
                     "concepts_via_measures": sorted({x for x in r["via_measures"] if x}),
                     "quote": quote(p.get("grounding_span"))})
    rows.sort(key=lambda x: x["node_key"])
    distinct = sorted({(r["instrument"] or "").strip().lower() for r in rows})
    incomplete = [r for r in rows if not r["complete"]]
    no_target = [r for r in rows if not r["concepts_measured"] and not r["concepts_via_measures"]]
    if not rows:
        grade, reason = "cannot_answer", "no Instrument's name matches the selection rule"
    elif s["operationalizes"] == 0 or incomplete:
        grade = "partial"
        reason = (f"{len(rows)} Instrument nodes, {len(distinct)} distinct names. The graph holds "
                  f"{s['operationalizes']} `OPERATIONALIZES` edges (Instrument -> Construct), so "
                  f"what an instrument operationalises is read from `MEASURES` -> Concept, "
                  f"direct or through its Measures, as the stand-in; {len(no_target)} nodes "
                  f"measure no Concept either way; {len(incomplete)} rows lack a citation field")
    else:
        grade, reason = "answered", f"{len(rows)} instruments with constructs and citations"
    return {
        "id": "Q4",
        "question": "What standard instruments or tests of AI readiness exist, and what does each "
                    "operationalise?",
        "grade": grade, "reason": reason,
        "to_close": [f"entity-resolve the {len(rows)} Instrument nodes to {len(distinct)} or "
                     f"fewer instruments, and write `OPERATIONALIZES` to Constructs once Q2's "
                     f"construct layer exists"] if grade != "answered" else [],
        "route": "neo4j: scripts/run_kg_questions.py via mcp/airkg_tools.Graph (read transactions)",
        "selection": {"label": "Instrument", "property": "name", "regex": Q4_NAME_RX},
        "structure": dict(s),
        "counts": {"instrument_nodes": len(rows), "distinct_names": len(distinct),
                   "measuring_no_concept": len(no_target), "rows_incomplete": len(incomplete)},
        "rows": rows,
    }


# ------------------------------------------------------------------------------- Q5

def q5() -> dict:
    """From the record. Item = AssessmentIndicator, construct = AssessmentConstruct by its
    DECOMPOSES_INTO edge, primary source = the indicator's EVIDENCED_BY documents, definition =
    any edge from a construct or an indicator to a Definition."""
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in rec["nodes"]}
    lab = {i: n["labels"][0] for i, n in nodes.items()}
    con_of, docs_of, internal_of, def_edges = {}, {}, {}, 0
    for e in rec["edges"]:
        f, t, ty = e["from"], e["to"], e["type"]
        if ty == "DECOMPOSES_INTO" and lab.get(f) == "AssessmentConstruct" \
                and lab.get(t) == "AssessmentIndicator":
            con_of.setdefault(t, []).append(f)
        elif ty == "EVIDENCED_BY" and lab.get(f) == "AssessmentIndicator":
            docs_of.setdefault(f, []).append(e["properties"].get("doc_id") or t)
        elif ty == "EVIDENCED_BY_INTERNAL" and lab.get(f) == "AssessmentIndicator":
            internal_of.setdefault(f, []).append(t)
        if lab.get(f) in ("AssessmentConstruct", "AssessmentIndicator") and \
                (lab.get(t) == "Definition" or str(t).startswith("def")):
            def_edges += 1
    inds = sorted(i for i, l in lab.items() if l == "AssessmentIndicator")
    cons = sorted(i for i, l in lab.items() if l == "AssessmentConstruct")
    rows = []
    for i in inds:
        p = nodes[i]["properties"]
        docs = sorted(set(docs_of.get(i, [])))
        rows.append({"item": p.get("code"), "status": p.get("status"),
                     "construct": sorted(con_of.get(i, [])),
                     "doc_id": docs or None,
                     "locator": f"{RECORD_PATH}#{i}",
                     "grounding_span_id": None,
                     "complete": False,
                     "definition": None})
    items_of = {c: sorted(i for i in inds if c in con_of.get(i, [])) for c in cons}
    no_item = [c for c in cons if not items_of[c]]
    no_source = [c for c in cons if items_of[c] and not any(docs_of.get(i) for i in items_of[c])]
    rows_no_doc = [r["item"] for r in rows if not r["doc_id"]]
    internal_only = sorted(nodes[i]["properties"].get("code") for i in inds
                           if not docs_of.get(i) and internal_of.get(i))
    reason = (f"{len(inds)} items map to {len(cons)} constructs ({len(no_item)} constructs have no "
              f"item). The crosswalk's construct -> definition hop does not exist: the record "
              f"holds {def_edges} edges from a construct or an item to a Definition. Its "
              f"primary-source hop is `EVIDENCED_BY`, whose edges carry a doc_id and no grounding "
              f"span, so no row meets the citation standard; {len(rows_no_doc)} items cite no "
              f"document at all. The items are the framework instrument's; the ICSP working "
              f"group's January self-report survey (DN-005 §2.5) is not in the graph")
    return {
        "id": "Q5",
        "question": "For the FSS AI-readiness survey, which items map to which constructs and "
                    "definitions, and which constructs have no item?",
        "grade": "partial" if inds else "cannot_answer", "reason": reason,
        "to_close": [
            "a construct -> Definition edge in the framework record (`grounds`, schema "
            "§edge_types), authored per construct from the Q1 set, so the crosswalk reaches a "
            "definition",
            "carry each EVIDENCED_BY citation's section and verbatim quote, already prose in the "
            "indicator's `evidence_raw`, as edge properties validated by kg/extraction/grounding.py",
            "ingest the ICSP survey's items, when they exist, as items of a second instrument "
            "crosswalked onto the same constructs"],
        "route": f"record: {RECORD_PATH} (mcp/airkg_tools.py decision 3: framework questions are "
                 f"answered from the record)",
        "counts": {"items": len(inds), "constructs": len(cons),
                   "items_candidate": sum(1 for r in rows if r["status"] == "candidate"),
                   "constructs_with_no_item": len(no_item),
                   "constructs_with_no_primary_source": len(no_source),
                   "constructs_with_no_definition": len(cons) if def_edges == 0 else None,
                   "items_with_no_document": len(rows_no_doc),
                   "items_with_project_internal_evidence_only": len(internal_only)},
        "uncovered": {"constructs_with_no_item": no_item,
                      "constructs_with_no_primary_source": no_source,
                      "items_with_no_document": rows_no_doc,
                      "items_with_project_internal_evidence_only": internal_only},
        "rows": rows,
    }


# ------------------------------------------------------------------------------- render

def render(graph) -> tuple:
    import airkg_tools as T
    gate = T.Tools(graph=graph).projection_gate()
    a1, q1_rows = q1(graph)
    questions = [a1, q2(graph, q1_rows), q3(graph, q1_rows), q4(graph), q5()]
    for q in questions:
        assert q["grade"] in GRADES, q["id"]
    doc = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": f"{GENERATOR} ({TASK}). Do not edit: re-run the generator.",
        "terminology": "The graph says AI throughout. Any federal terminology change is applied "
                       "at presentation, not in the record (DN-009 decision 4).",
        "citation_standard": "every row carries doc_id, locator and grounding_span_id; "
                             "grounding_span_id is the grounded node's key, and is null when "
                             "the node carries no extraction event; a row with any of the three "
                             "null is complete: false",
        "projection_gate": {"status": gate["status"], "nodes_compared": gate["nodes_compared"],
                            "mismatches": len(gate["mismatches"])},
        "epoch": epoch(graph),
        "questions": questions,
    }
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100,
                          default_flow_style=False)
    return text, render_md(doc)


def _cell(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, list):
        return ", ".join(f"`{x}`" for x in v) if v else "—"
    return str(v).replace("|", "\\|").replace("\n", " ")


def render_md(doc: dict) -> str:
    L = ["# The knowledge graph asked five research questions", "",
         f"Generated by `{GENERATOR}` (`{TASK}`) in the same run as "
         f"`docs/evidence/kg_questions.yaml`, which holds every field; this page is its "
         f"reading copy. Do not edit: re-run the generator. {doc['terminology']}", "",
         f"Projection gate: **{doc['projection_gate']['status']}** "
         f"({doc['projection_gate']['nodes_compared']} framework nodes compared). Corpus epoch: "
         f"{doc['epoch']['documents']} documents, {doc['epoch']['definitions']} definitions, "
         f"{doc['epoch']['instruments']} instrument nodes.", "",
         f"Citation standard: {doc['citation_standard']}.", "",
         "| Q | grade | rows | route |", "|---|---|---|---|"]
    for q in doc["questions"]:
        L.append(f"| {q['id']} | {q['grade']} | {len(q['rows'])} | {_cell(q['route'])} |")
    for q in doc["questions"]:
        L += ["", f"## {q['id']}. {q['question']}", "", f"**Grade: {q['grade']}.** {q['reason']}."]
        if q["to_close"]:
            L += ["", "What would close it:"] + [f"- {t}" for t in q["to_close"]]
        L += ["", "Counts: " + ", ".join(f"{k} {v}" for k, v in q["counts"].items()) + "."]
        if q["id"] in ("Q1", "Q4"):
            name = "term" if q["id"] == "Q1" else "instrument"
            L += ["", f"| {name} | doc_id | locator | grounding_span_id | complete | quote |",
                  "|---|---|---|---|---|---|"]
            for r in q["rows"]:
                L.append(f"| {_cell(r[name])} | `{r['doc_id']}` | {_cell(r['locator'])} | "
                         f"{_cell(r['grounding_span_id'])} | {r['complete']} | "
                         f"{_cell(r['quote'])} |")
            if q["id"] == "Q4":
                L += ["", "| instrument node | measures | concepts measured (direct) | "
                      "concepts via measures |", "|---|---|---|---|"]
                for r in q["rows"]:
                    L.append(f"| `{r['node_key']}` | {r['measures']} | "
                             f"{_cell(r['concepts_measured'])} | "
                             f"{_cell(r['concepts_via_measures'])} |")
        elif q["id"] == "Q2":
            L += ["", "| construct (CQ-08) | definitions naming it |", "|---|---|"]
            for n, ks in q["by_construct"].items():
                L.append(f"| {n} | {len(ks)}: {_cell(ks)} |")
            L += ["", "| definition | names | omits |", "|---|---|---|"]
            for r in q["rows"]:
                L.append(f"| `{r['node_key']}` | {_cell(r['names'])} | {len(r['omits'])} |")
        elif q["id"] == "Q3":
            L += ["", "| label | about | doc_id | locator | same document | touches Q1 |",
                  "|---|---|---|---|---|---|"]
            for r in q["rows"]:
                L.append(f"| {r['label']} | {_cell(r['about'])} | {_cell(r['doc_id'])} | "
                         f"{_cell(r['locator'])} | {r['same_document']} | "
                         f"{r['touches_q1_definition']} |")
        elif q["id"] == "Q5":
            L += ["", "Uncovered: " + "; ".join(f"{k}: {_cell(v)}"
                                                for k, v in q["uncovered"].items()) + ".",
                  "", "| item | status | construct | documents | definition |",
                  "|---|---|---|---|---|"]
            for r in q["rows"]:
                L.append(f"| {r['item']} | {r['status']} | {_cell(r['construct'])} | "
                         f"{_cell(r['doc_id'])} | {_cell(r['definition'])} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    import airkg_tools as T
    graph = T.Graph()
    if not graph.available():
        raise SystemExit(f"FATAL: Neo4j unreachable ({graph.error}); Q1 to Q4 read the corpus "
                         f"layer, which only the projection holds")
    text, md = render(graph)
    if a.check:
        if not OUT_YAML.is_file():
            print(f"{OUT_YAML.relative_to(REPO)}: MISSING")
            return 1
        stored = yaml.safe_load(OUT_YAML.read_text(encoding="utf-8"))
        if stored.get("epoch") != yaml.safe_load(text)["epoch"]:
            print("EPOCH MOVED: the corpus or the record changed under the stored answers; "
                  "they are answers of the stored epoch, and a re-run is a new task")
            return 2
        drift = [p.relative_to(REPO).as_posix() for p, t in ((OUT_YAML, text), (OUT_MD, md))
                 if not p.is_file() or p.read_text(encoding="utf-8") != t]
        print("DRIFT: " + ", ".join(drift) if drift else "no drift")
        return 1 if drift else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_YAML.write_text(text, encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_YAML.relative_to(REPO)} and {OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
