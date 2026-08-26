#!/usr/bin/env python3
"""Export one document's TrustGraph extraction: triples (all named graphs)
+ evidence chunks (librarian child documents, verbatim text) + provenance.

Talks to the deployed gateway's REST API (fork v2.8.15 wire formats):
  POST api/v1/flow/{flow}/service/triples   {"collection", "limit"}  # no "g": see graph-filter quirk below
      -> {"response": [ {s: TERM, p: TERM, o: TERM, g?: str}, ... ]}
      TERM = {"v": value, "e": is_entity(bool)} plus {"t": {...}} for
      RDF-star quoted triples, {"d": datatype}/{"l": lang} for literals
      (see trustgraph-base/trustgraph/messaging/translators/primitives.py)
  POST api/v1/librarian  {"operation": "list-documents", "include-children": true}
      (list-children is unregistered at the gateway in 2.8.15; filter by parent-id)
  POST api/v1/librarian  {"operation": "get-document-content",
                          "document-id": chunk} -> {"content": b64}

Output JSON:
{
  "document_id", "collection", "flow", "exported_at",
  "triples":   [ ... raw wire terms, graph-tagged ... ],
  "chunks":    [ {"chunk_id", "text", ...child metadata...} ],
}
Usage: export_tg_extraction.py --doc <doc_id> --collection <coll> \
          [--flow onto-bench] [--out extractions/<doc>.json]
"""
import argparse
import base64
import datetime
import json
import os
import sys
from pathlib import Path

import requests
import subprocess

HERE = Path(__file__).resolve().parent
DEFAULT_URL = os.getenv("TRUSTGRAPH_URL", "http://localhost:8088/")


def tok():
    env = HERE / "deploy/unpacked/.env"
    for line in env.read_text().splitlines():
        if line.startswith("IAM_BOOTSTRAP_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("FATAL: IAM_BOOTSTRAP_TOKEN not found in deploy/unpacked/.env")


def post(url, token, path, payload):
    r = requests.post(url.rstrip("/") + "/api/v1/" + path, json=payload,
                      headers={"Authorization": f"Bearer {token}"}, timeout=120)
    if r.status_code != 200:
        raise SystemExit(f"FATAL: POST {path} -> {r.status_code}: {r.text[:300]}")
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--collection", required=True)
    ap.add_argument("--flow", default="onto-bench")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--limit", type=int, default=1000000)
    ap.add_argument("--out")
    args = ap.parse_args()

    token = tok()
    out_path = Path(args.out) if args.out else HERE / "extractions" / f"{args.doc}.json"

    # 1. All triples in the document's collection, across ALL named graphs.
    # Graph filter quirk (2.8.15): the schema comment says g="*" means all
    # graphs, but the cassandra query service treats g=None (key absent) as
    # all-graphs and returns [] for "*" — and its named-graph filter also
    # returns [] even for graphs present in the data.  Omit "g" entirely:
    # every returned triple carries its own "g" tag (absent = default graph,
    # "urn:graph:source" = provenance).
    resp = post(args.url, token, f"flow/{args.flow}/service/triples", {
        "collection": args.collection,
        "limit": args.limit,
    })
    triples = resp.get("response", [])
    if not isinstance(triples, list):
        raise SystemExit(f"FATAL: unexpected triples response shape: {type(triples)}")

    # 2. Evidence chunks: librarian child documents of the source document.
    # list-children exists on the librarian processor but is not registered
    # in the gateway's operation registry (2.8.15) — the gateway refuses it
    # with "unknown operation".  Use list-documents + include-children and
    # filter by parent-id instead (registered documents:read op).
    kids = post(args.url, token, "librarian", {
        "operation": "list-documents", "include-children": True,
    })
    allm = kids.get("document-metadatas") or kids.get("document_metadatas") or []
    metas = [m for m in allm
             if (m.get("parent-id") or m.get("parent_id")) == args.doc]
    chunks = []
    for m in metas:
        cid = m.get("id") if isinstance(m, dict) else None
        if cid is None:
            raise SystemExit(f"FATAL: child metadata without id: {m}")
        content = post(args.url, token, "librarian", {
            "operation": "get-document-content", "document-id": cid,
        })
        b64 = content.get("content")
        if b64 is None:
            raise SystemExit(f"FATAL: no content for chunk {cid}")
        chunks.append({
            "chunk_id": cid,
            "text": base64.b64decode(b64).decode("utf-8"),
            "metadata": m,
        })

    # 3. COMPLETE quad dump from the triple store.  The REST triples query
    # (non-streaming) returns at most one Cassandra fetch page (5000 rows)
    # regardless of "limit" — recorded as a friction finding.  For full
    # fidelity, read the store through the Cassandra driver inside their
    # own triples container (table default.quads_by_collection; column d
    # is the named graph, "" = default graph).
    dump_py = (
        "import json,sys\n"
        "from cassandra.cluster import Cluster\n"
        "sess = Cluster(['cassandra']).connect()\n"
        "rows = sess.execute('SELECT d,s,p,o,otype,dtype,lang "
        "FROM \"default\".quads_by_collection WHERE collection=%s', "
        f"['{args.collection}'])\n"
        "out = [dict(g=r.d, s=r.s, p=r.p, o=r.o, otype=r.otype, "
        "dtype=r.dtype, lang=r.lang) for r in rows]\n"
        "json.dump(out, sys.stdout)\n"
    )
    proc = subprocess.run(
        ["docker", "exec", "-i", "trustgraph-triples-1", "python3", "-c", dump_py],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise SystemExit(f"FATAL: store dump failed: {proc.stderr[:400]}")
    quads = json.loads(proc.stdout)

    doc = {
        "document_id": args.doc,
        "collection": args.collection,
        "flow": args.flow,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "triple_count_api": len(triples),
        "quad_count_store": len(quads),
        "chunk_count": len(chunks),
        "triples_api": triples,
        "quads": quads,
        "chunks": chunks,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=1))
    print(f"{args.doc}: api={len(triples)} triples (page-capped at 5000), "
          f"store={len(quads)} quads, {len(chunks)} chunks -> {out_path}")


if __name__ == "__main__":
    main()
