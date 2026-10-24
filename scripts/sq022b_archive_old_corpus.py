#!/usr/bin/env python3
"""squiddy SQ-022b Part D (planned by SQ-022 Part D): an export of the old corpus labels in `seldon-ai-readiness-kg`,
gzip, beside the kit graph, once the corpus verbs read the kit's database. Nothing is dropped or written in the old
database; it stays writable and keeps serving the assessment layer.

    /opt/anaconda3/bin/python3 scripts/sq022b_archive_old_corpus.py --out graphs/ai-readiness/archive

WHAT. Every node carrying a label of kg/schema.yaml's `node_types` (properties whole, all its labels), and every
relationship of a type in `edge_types` (upper-cased, the old store's names) not leaving AssessmentIndicator,
Observation or Finding (parity_queries.yaml C12's clause), with its endpoints' keys and labels and its properties.
One JSON object per line, sorted, so the archive's sha256 is a function of the database's content. The gz is
gitignored above 50 MB; the manifest (counts, sha256 of the gz and of the uncompressed lines) is committed.
Zero calls; reads the old database through the mcp read guard.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "mcp"))
import airkg_guard as guard  # noqa: E402
import airkg_tools as T  # noqa: E402

GITIGNORE_ABOVE_BYTES = 50 * 1024 * 1024      # SQ-022 Part D: over 50 MB stays gitignored
EXCLUDED_SOURCES = ("AssessmentIndicator", "Observation", "Finding")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    schema = yaml.safe_load((REPO / "kg" / "schema.yaml").read_text(encoding="utf-8"))
    labels = sorted(schema["node_types"])
    types = sorted(str(t).upper() for t in schema["edge_types"])
    db = guard.project_database()
    g = T.Graph(db)
    lines, counts = [], Counter()
    for lab in labels:
        rows, _ = g.read(f"MATCH (n:{lab}) RETURN labels(n) AS l, properties(n) AS p", limit=10_000_000)
        for r in rows:
            lines.append(json.dumps({"kind": "node", "label": lab, "labels": sorted(r["l"]), "properties": r["p"]},
                                    sort_keys=True, ensure_ascii=False, default=str))
            counts[f"node:{lab}"] += 1
    where = " AND ".join(f"NOT x:{s}" for s in EXCLUDED_SOURCES)
    for t in types:
        rows, _ = g.read(f"MATCH (x)-[e:{t}]->(y) WHERE {where} RETURN coalesce(x.key, x.doc_id) AS s, labels(x) AS "
                         f"sl, coalesce(y.key, y.doc_id) AS o, labels(y) AS ol, properties(e) AS p", limit=10_000_000)
        for r in rows:
            lines.append(json.dumps({"kind": "edge", "type": t, "subject": r["s"], "subject_labels": sorted(r["sl"]),
                                     "object": r["o"], "object_labels": sorted(r["ol"]), "properties": r["p"]},
                                    sort_keys=True, ensure_ascii=False, default=str))
            counts[f"edge:{t}"] += 1
    lines.sort()
    raw = ("\n".join(lines) + "\n").encode("utf-8")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    gz = out / f"old_corpus_{db}_{stamp}.jsonl.gz"
    with gzip.GzipFile(gz, "wb", mtime=0) as fh:          # mtime 0: the gz bytes depend on the content only
        fh.write(raw)
    manifest = {"database": db, "written_utc": datetime.now(timezone.utc).isoformat(), "file": gz.name,
                "bytes": gz.stat().st_size, "sha256_gz": hashlib.sha256(gz.read_bytes()).hexdigest(),
                "sha256_jsonl": hashlib.sha256(raw).hexdigest(), "lines": len(lines),
                "nodes": sum(v for k, v in counts.items() if k.startswith("node:")),
                "edges": sum(v for k, v in counts.items() if k.startswith("edge:")),
                "by": dict(sorted(counts.items())), "gitignored": gz.stat().st_size > GITIGNORE_ABOVE_BYTES,
                "script": "scripts/sq022b_archive_old_corpus.py", "task": "squiddy SQ-022b Part D"}
    (out / f"old_corpus_{db}_{stamp}.manifest.json").write_text(json.dumps(manifest, indent=1) + "\n",
                                                               encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("file", "bytes", "sha256_gz", "lines", "nodes", "edges",
                                               "gitignored")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
