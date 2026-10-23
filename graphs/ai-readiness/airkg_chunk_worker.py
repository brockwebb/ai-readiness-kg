#!/usr/bin/env python3
"""ai-readiness-kg's chunk extraction protocol, served to the kit (squiddy SQ-021; DN-049 R-211). Zero model calls.

RUN IN AI-READINESS-KG'S OWN INTERPRETER (`domain.airkg.python`), by `extract_protocol.py` beside it, the way
`text_reader.py` runs `doc_text`: the chunker, the prompt template, the anchor contract and the parser are that
repository's, CALLED and never copied, so the instrument a new model is piloted on is the one the old model ran
(`scripts/run_profiles.yaml` profile `bulk_v038`: prompt v0.3.8, its template and chunker config pinned by sha256,
`apply_arm` verifying both pins). R-211: "a model change is a new extraction instrument", so the model is the ONE
variable between the old instrument and an arm; everything this file does is the old harness.

    python airkg_chunk_worker.py units  < {"repo": R, "doc_ids": [...]}
    python airkg_chunk_worker.py parse  < {"repo": R, "doc_id": D, "responses": [{"chunk_id": C, "content": S}]}

`units`: per document, its text (`run_bulk_extraction.doc_text`, the text every span of this graph is an offset
into), the source file's sha256, and per chunk its offsets, its overlap start (located as `text_reader.windows` does),
its token count and the exact prompt the old instrument would send (`chunked_pilot.build_prompt`, the title being the
document id with hyphens as spaces, as `chunked_pilot.phase_extract` passes it).

`parse`: per response, what `chunked_pilot.parse_chunk_raw` makes of it (the anchor contract derives every span from
the chunk's grounding text, then the parser validates it), DD-024's bulk refusal of semantic edges at graph entry
(`chunked_pilot.semantic_edge_refused`, as `phase_ingest` applies it), and each surviving item in the shape
ai-readiness-kg's own projection gives it (`build_projection.node_key`, `node_label`, `node_props`, `edge_rel`,
`resolve_endpoint`: the functions squiddy's adopter reads SQ-019's items through), so an arm's item and an adopted
item are the same kind of row.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from pathlib import Path

PROFILE = "bulk_v038"


def _setup(repo: str):
    for p in (repo, str(Path(repo) / "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import chunked_pilot as cp
    cp.apply_arm(PROFILE)
    return cp


def _doc_path(repo: str, doc_id: str, paths: dict | None = None) -> Path:
    """The document's file: the caller's (`paths`, for a document the kit catalogued and ai-readiness-kg's queue does
    not hold, SQ-021 Part D), else the queue's canonical path, the file every old extraction read."""
    if (paths or {}).get(doc_id):
        p = Path(paths[doc_id])
        if not p.is_file():
            raise SystemExit(f"FATAL: {doc_id}: {p} does not exist")
        return p
    from kg import queue
    entry = queue.included_documents().get(doc_id)
    if entry is None:
        raise SystemExit(f"FATAL: {doc_id} is not an included document of ai-readiness-kg's queue")
    rel = (entry.get("identity") or {}).get("canonical_path")
    if not rel:
        raise SystemExit(f"FATAL: {doc_id} has no canonical_path in ai-readiness-kg's manifest")
    p = Path(rel)
    return p if p.is_absolute() else Path(repo) / p


def _chunks(cp, repo: str, doc_id: str, paths: dict | None = None):
    import run_bulk_extraction as rbe
    from kg.extraction import chunker
    path = _doc_path(repo, doc_id, paths)
    text = rbe.doc_text(path, doc_id)
    return path, text, list(chunker.chunk_document(doc_id, text))


def _overlap_start(text: str, c) -> int | None:
    """`text_reader.windows`' rule, the one SQ-019's adopter grounds an item's overlap by."""
    if not c.overlap_text:
        return None
    o = text.rfind(c.overlap_text, 0, c.start)
    return o if o != -1 and o + len(c.overlap_text) <= c.start else None


def cmd_units(req: dict) -> dict:
    cp = _setup(req["repo"])
    from kg import eventlog
    from kg.extraction import model_stub
    tpl = cp.profile_template()
    out = {"profile": PROFILE, "prompt_version": model_stub.prompt_version(),
           "schema_version": eventlog.schema_version(), "template": str(tpl),
           "template_sha256": hashlib.sha256(tpl.read_bytes()).hexdigest(), "docs": {}}
    for d in req["doc_ids"]:
        path, text, cs = _chunks(cp, req["repo"], d, req.get("paths"))
        title = d.replace("-", " ")
        chunks = []
        for c in cs:
            prompt = cp.build_prompt(d, c, title)
            chunks.append({"chunk_id": c.chunk_id, "index": c.index, "start": c.start, "end": c.end,
                           "overlap_start": _overlap_start(text, c), "n_tokens": c.n_tokens,
                           "oversize": bool(c.oversize), "heading_path": list(c.heading_path),
                           "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()})
        out["docs"][d] = {"path": str(path), "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "chars": len(text),
                          "chunks": chunks}
    # The positive control (DI-100 in this protocol's terms): a real chunk with one sentence appended to its body, cut
    # as a Chunk the same way so the same `build_prompt` frames it. Its grounding text is returned so `parse` grounds
    # the control's items in the text the model was shown, never in the document.
    out["synthetic"] = []
    for s in req.get("synthetic") or []:
        _path, _text, cs = _chunks(cp, req["repo"], s["doc_id"], req.get("paths"))
        base = next((c for c in cs if c.chunk_id == s["chunk_id"]), None)
        if base is None:
            raise SystemExit(f"FATAL: control chunk {s['chunk_id']} is not a chunk of {s['doc_id']} as cut now")
        body = base.text if not s.get("append") else f"{base.text.rstrip()} {s['append']}"
        c = dataclasses.replace(base, chunk_id=f"{base.chunk_id}:{s['name']}", text=body)
        prompt = cp.build_prompt(s["doc_id"], c, s["doc_id"].replace("-", " "))
        out["synthetic"].append({"name": s["name"], "doc_id": s["doc_id"], "chunk_id": c.chunk_id,
                                 "base_chunk_id": base.chunk_id, "grounding_text": c.grounding_text(),
                                 "prompt": prompt,
                                 "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()})
    return out


def cmd_parse(req: dict) -> dict:
    cp = _setup(req["repo"])
    import build_projection as bp
    from kg.extraction import model_stub
    schema = bp._load_schema()          # the schema squiddy's adopter projects SQ-019's items under (l002_adopt)
    kg_labels, edge_wl = list(schema["node_types"]), set(schema["edge_types"])
    from kg import queue
    document_ids = set(queue.included_documents())
    d = req["doc_id"]
    _path, text, cs = _chunks(cp, req["repo"], d, req.get("paths"))
    by_id = {c.chunk_id: c for c in cs}
    results = []
    for r in req["responses"]:
        c = by_id.get(r["chunk_id"])
        rec = {"chunk_id": r["chunk_id"], "status": None, "detail": None, "nodes": [], "edges": [],
               "quarantined": [], "semantic_edge_refused": 0, "mentions": 0, "diverted": 0}
        if r.get("grounding_text") is not None:     # a synthetic (control) chunk: grounded in what the model saw
            gtext = r["grounding_text"]
        elif c is None:
            rec.update(status="unknown_chunk", detail=f"{r['chunk_id']} is not a chunk of {d} as cut now")
            results.append(rec)
            continue
        else:
            gtext = c.grounding_text()
        content = r.get("content") or ""
        if not content.strip():
            rec.update(status="empty", detail="no answer text")
            results.append(rec)
            continue
        try:
            out = model_stub._extract_json(content)
        except Exception as exc:  # the old harness's own refusal of a non-JSON answer: a protocol failure, recorded
            rec.update(status="unparseable", detail=f"{type(exc).__name__}: {str(exc)[:200]}")
            results.append(rec)
            continue
        if not cp.envelope_complete(out):
            rec.update(status="unparseable", detail="the envelope carries none of the contract's output keys")
            results.append(rec)
            continue
        result, mentions, divs = cp.parse_chunk_raw(d, {"raw_result": content}, text, gtext)
        rec["status"] = "parsed"
        rec["mentions"], rec["diverted"] = len(mentions), len(divs)
        rec["quarantined"] = [{"kind": q.get("kind"), "class": cp.reason_class(q.get("reason")),
                               "reason": str(q.get("reason") or "")[:300]} for q in result.quarantined]
        for n in result.nodes:
            ev = {"doc_id": d, "payload": {"id": n["id"], "type": n["type"], "item": n["item"]},
                  "provenance": {}}
            label = bp.node_label(ev, kg_labels)
            if label is None:
                rec["quarantined"].append({"kind": "node", "class": "not_a_schema_type", "reason": str(n["type"])})
                continue
            props = bp.node_props(ev)
            for k in [k for k in props if k.startswith("prov_")]:
                props.pop(k)   # the harness stamps provenance; an arm's stamp is the kit side's (extract_protocol)
            rec["nodes"].append({"key": bp.node_key(d, n["id"]), "label": label, "props": props,
                                 "quote": str(n["item"].get("grounding_span") or ""),
                                 "anchor": n["item"].get("anchor"), "location": n["item"].get("location")})
        for e in result.edges:
            if cp.semantic_edge_refused(e["type"]):
                rec["semantic_edge_refused"] += 1
                continue
            ev = {"doc_id": d, "event_type": "edge_asserted",
                  "payload": {"type": e["type"], "from_id": e["from_id"], "to_id": e["to_id"], "item": e["item"]}}
            rel = bp.edge_rel(ev, edge_wl)
            if rel is None:
                rec["quarantined"].append({"kind": "edge", "class": "not_a_schema_edge", "reason": str(e["type"])})
                continue
            try:
                fk = bp.resolve_endpoint(d, e["from_id"], document_ids, {}, None)
                tk = bp.resolve_endpoint(d, e["to_id"], document_ids, {}, None)
            except bp.EndpointRefused as exc:
                rec["quarantined"].append({"kind": "edge", "class": "endpoint_refused", "reason": str(exc)[:200]})
                continue
            item = e["item"]
            span = str(item.get("grounding_span") or "")
            rec["edges"].append({"rel": rel, "subject": fk, "object": tk, "quote": span,
                                 "from_type": e.get("from_type"), "to_type": e.get("to_type"),
                                 "anchor": item.get("anchor"), "location": item.get("location"),
                                 "props": {"grounding_span": span, "prov_doc": d, "item": item}})
        results.append(rec)
    return {"doc_id": d, "prompt_version": model_stub.prompt_version(), "results": results}


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    req = json.loads(sys.stdin.read())
    if cmd == "units":
        out = cmd_units(req)
    elif cmd == "parse":
        out = cmd_parse(req)
    else:
        raise SystemExit(f"FATAL: unknown command {cmd!r}; expected units or parse")
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
