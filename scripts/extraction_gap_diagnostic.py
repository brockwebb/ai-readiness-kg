#!/usr/bin/env python3
"""Classify every admitted Document that contributes no extraction edges to the graph.

Task `cc_tasks/2026-09-04_extraction_gap_diagnostic.md` §1. **Zero model spend.** Diagnosis
only: this script decides nothing and runs no extraction.

**Premise, registered rather than remembered:** `kg_diag_documents_without_extractions` = 72
of 211 Document nodes (RESULT of `2026-09-04_kg_diagnostic_and_cq_harness` §0.1).

**Where each fact comes from — read from the pipeline, not guessed:**

* the corpus and its epochs — the dixie evidence ledger via `kg.queue.corpus_epochs`, the
  same source `run_bulk_extraction.corpus_members` reads;
* what may run — `kg.queue.project()`, the single derivation every queue surface reads
  (`extraction_request` / `extraction_deferred` / failures / oversize);
* what did run — `kg.queue.extractions()` over the event shards;
* what loaded — the Neo4j projection, which is what "has extraction edges" means;
* the file on disk — the manifest entry's `canonical_path`.

**Class precedence**, applied in this order so a document with two conditions lands in the
one that explains it best:

    source_missing > run_ok_no_edges > run_failed > excluded_by_design
                   > queued_not_run > never_queued

`run_ok_no_edges` is the only class that would indict the loader, so it is tested before the
classes that would excuse it.

    /opt/anaconda3/bin/python3 scripts/extraction_gap_diagnostic.py [--out state/extraction_gap_2026-09-04.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

KG_LABELS = ["Concept", "Claim", "Definition", "Measure", "Practice", "Standard",
             "Framework", "Instrument", "Platform", "Tool"]

CLASSES = ("never_queued", "queued_not_run", "run_failed", "run_ok_no_edges",
           "excluded_by_design", "source_missing")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def graph_facts(session) -> dict:
    """Document nodes, which of them carry extraction edges, and their node properties."""
    nodes = {r["id"]: r for r in session.run(
        "MATCH (d:Document) RETURN d.doc_id AS id, d.source_type AS source_type, "
        "d.pub_date AS pub_date, d.content_hash IS NOT NULL AS has_content_hash, "
        "d.primary_url AS primary_url").data()}
    with_edges = {r["id"] for r in session.run(
        "MATCH (d:Document)-[]->(x) WHERE any(l IN labels(x) WHERE l IN $kg) "
        "RETURN DISTINCT d.doc_id AS id", kg=KG_LABELS).data()}
    return {"nodes": nodes, "with_edges": with_edges}


def ledger_facts() -> dict:
    from kg import eventlog, queue
    rows = queue.project()
    epochs = queue.corpus_epochs()
    doc_epochs: dict = {}
    for epoch, members in epochs.items():
        for m in members:
            doc_epochs.setdefault(m, []).append(epoch)
    # Deferrals and cuts carry their reason on the event; a class that cites no reason is not
    # `excluded_by_design`, it is an unexplained gap.
    deferrals = queue.deferrals()
    cuts: dict = {}
    admitted: dict = {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        doc = ev.get("document_id") or ev.get("doc_id")
        if not doc:
            continue
        if t in ("extent_unremediable", "conversion_gap"):
            cuts.setdefault(doc, []).append(
                {"event": t,
                 "reason": str(ev.get("reason") or ev.get("note") or ev.get("detail") or "")[:400],
                 "ts": ev.get("ts") or ev.get("timestamp")})
        elif t == "manifest_add":
            admitted[doc] = ev.get("ts") or ev.get("timestamp")
    return {"rows": rows, "doc_epochs": doc_epochs, "deferrals": deferrals,
            "cuts": cuts, "admitted": admitted,
            "extractions": queue.extractions(), "failures": queue.failures(),
            "requests_ever": queue.requests_ever()}


def canonical_paths() -> dict:
    """doc_id -> path on disk (or None), from the manifest the runner itself reads."""
    # Same three imports and the same config/ledger path `run_bulk_extraction.py` uses
    # (lines 50-52 and 174-175: dixie_config(REPO / "dixie_evidence.yaml")). An ImportError here is fatal rather than an empty dict: silently
    # returning no paths made every document look like it had no source file, which is
    # exactly the wrong answer to the question this script exists to ask.
    from dixie.evidence.config import load_config as dixie_config
    from dixie.evidence.eventlog import EventLog as DixieLog
    from dixie.evidence.manifest import build_manifest
    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    log = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    out = {}
    for doc_id, entry in build_manifest(log).items():
        p = (entry.get("identity") or {}).get("canonical_path")
        out[doc_id] = p
    return out


def classify(doc: str, g: dict, l: dict, paths: dict) -> dict:
    row = l["rows"].get(doc) or {}
    state = row.get("extraction_state")
    ran = bool(l["extractions"].get(doc))
    path = paths.get(doc)
    on_disk = bool(path) and (REPO / path).is_file()
    fails = l["failures"].get(doc) or []
    deferral = l["deferrals"].get(doc)
    cut = l["cuts"].get(doc)

    if path and not on_disk:
        cls, why = "source_missing", f"manifest canonical_path {path} is not a file on disk"
    elif ran:
        cls, why = ("run_ok_no_edges",
                    f"{len(l['extractions'][doc])} extraction event(s) on the shards but no "
                    f"edge loaded into the projection — loader defect")
    elif fails:
        cls, why = "run_failed", f"{len(fails)} failure event(s): {str(fails[-1])[:200]}"
    elif cut:
        # `extent_unremediable` is the DECISION ("cut with reason, not remediated");
        # `conversion_gap` is a note about a converter and carries a payload dict, not a
        # rule. Prefer the decision, so the class cites the rule that excluded the document
        # rather than the machinery that failed on it.
        best = (next((c for c in reversed(cut) if c["event"] == "extent_unremediable"), None)
                or next((c for c in reversed(cut) if c["reason"].strip()), cut[-1]))
        cls, why = ("excluded_by_design",
                    f"cut with reason: {best['event']} — {best['reason'][:220] or '(no reason recorded on the event)'}")
    elif deferral:
        cls, why = ("excluded_by_design",
                    f"extraction_deferred, reason {deferral.get('reason')!r} "
                    f"({deferral.get('ts')})")
    elif state == "queued":
        cls, why = "queued_not_run", "live extraction_request, no run event"
    elif not l["requests_ever"].get(doc):
        cls, why = ("never_queued",
                    "admitted to the corpus; no extraction_request was ever emitted for it")
    else:
        cls, why = "queued_not_run", f"request exists, queue state {state!r}, no run event"

    node = g["nodes"].get(doc) or {}
    size = (REPO / path).stat().st_size if on_disk else None
    return {"doc_id": doc, "class": cls, "reason": why,
            "queue_state": state, "epochs": l["doc_epochs"].get(doc, []),
            "source_type": node.get("source_type"), "pub_date": node.get("pub_date"),
            "has_content_hash": node.get("has_content_hash"),
            "source_format": (Path(path).suffix.lstrip(".") if path else None),
            "bytes": size, "path": path, "on_disk": on_disk,
            "admitted_at": l["admitted"].get(doc),
            "has_document_node": doc in g["nodes"]}


# ---------------------------------------------------------------- §2 CQ overlap
_TERM_RE = __import__("re").compile(r"CONTAINS\s+'([^']+)'")


def cq_terms(cq: dict) -> list:
    """The literal search terms the CQ's own Cypher uses. Taken FROM the query rather than
    chosen here: a term list invented for this cross-check would make the overlap a judgment,
    and §2 asks for a count."""
    return sorted({s.strip().lower() for s in _TERM_RE.findall(cq["cypher_raw"]) if s.strip()})


def document_text(row: dict) -> str:
    """Best available text for a gap document: the converted markdown substrate if the
    conversion produced one, else the file itself (md/html read directly, pdf via pypdf).
    Returns '' when no text can be had, which is reported rather than counted as 'no match'."""
    sub = REPO / "state" / "substrate_md" / f"{row['doc_id']}.md"
    if sub.is_file():
        return sub.read_text(encoding="utf-8", errors="ignore").lower()
    path = row.get("path")
    if not path or not (REPO / path).is_file():
        return ""
    f = REPO / path
    if f.suffix.lower() in (".md", ".html", ".htm", ".txt"):
        return f.read_text(encoding="utf-8", errors="ignore").lower()
    if f.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            return " ".join((pg.extract_text() or "") for pg in PdfReader(str(f)).pages).lower()
        except Exception:
            return ""
    return ""


def cq_overlap(rows: list, cq_path: Path, run_path: Path) -> dict:
    """§2: for the CQs that failed or misled, how many of the gap documents mention their
    terms. A count of what the coverage gap might have contributed to the conciseness
    finding — not a claim that extracting them would have changed any verdict."""
    import yaml
    cqs = {q["id"]: q for q in yaml.safe_load(cq_path.read_text(encoding="utf-8"))["questions"]}
    recs = [json.loads(x) for x in run_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    targets = [r for r in recs
               if r["answerable_collapsed"] in ("no", "partial") or r["misleading_raw"]]
    texts = {}
    no_text = []
    for row in rows:
        txt = document_text(row)
        if not txt:
            no_text.append(row["doc_id"])
        texts[row["doc_id"]] = txt
    out = {"documents_with_readable_text": len(rows) - len(no_text),
           "documents_without_readable_text": no_text, "cqs": {}}
    for r in targets:
        terms = cq_terms(cqs[r["id"]])
        if not terms:
            out["cqs"][r["id"]] = {
                "category": r["category"], "terms": [],
                "testable": False,
                "note": "structural query with no literal search terms; not term-testable, "
                        "and no terms were invented for it",
                "answerable_collapsed": r["answerable_collapsed"],
                "misleading_raw": r["misleading_raw"]}
            continue
        hits = sorted(d for d, txt in texts.items() if txt and any(t in txt for t in terms))
        out["cqs"][r["id"]] = {
            "category": r["category"], "terms": terms, "testable": True,
            "documents_mentioning": len(hits), "sample": hits[:5],
            "answerable_collapsed": r["answerable_collapsed"],
            "misleading_raw": r["misleading_raw"]}
    tested = [v for v in out["cqs"].values() if v.get("testable")]
    out["cqs_examined"] = len(out["cqs"])
    out["cqs_term_testable"] = len(tested)
    out["cqs_with_at_least_one_unextracted_document_mentioning_their_terms"] = sum(
        1 for v in tested if v["documents_mentioning"] > 0)
    return out


# ---------------------------------------------------------------- §3 estimate
#: controls.yaml spend.call_class_floors.extraction_chunk — what the guard RESERVES per
#: chunk call before the run has settles of its own. An upper bound: `_estimate` switches to
#: the run's measured mean as soon as there are settles.
CHUNK_FLOOR = 20000


def estimate(rows: list, cfg) -> dict:
    """Chunk count and reserved-token estimate under the pipeline's current chunking.
    Computes; does not run and does not decide."""
    from kg.extraction.chunker import chunk_document
    chunks, unchunkable = 0, []
    for r in rows:
        txt = document_text(r)
        if not txt.strip():
            unchunkable.append(r["doc_id"])
            continue
        try:
            cs = chunk_document(r["doc_id"], txt, cfg)
            chunks += len(cs.chunks if hasattr(cs, "chunks") else cs)
        except Exception as exc:                       # a doc the chunker refuses is reported
            unchunkable.append(f"{r['doc_id']}: {type(exc).__name__}")
    return {"documents": len(rows), "chunks": chunks,
            "tokens_at_chunk_floor": chunks * CHUNK_FLOOR,
            "chunk_floor": CHUNK_FLOOR, "unchunkable": unchunkable}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(REPO / "state" / "extraction_gap_2026-09-04.json"))
    a = ap.parse_args(argv)

    from seldon.config import get_neo4j_driver, load_project_config
    config = load_project_config(REPO)
    driver = get_neo4j_driver(config)
    try:
        with driver.session(database=config["neo4j"]["database"]) as session:
            g = graph_facts(session)
    finally:
        driver.close()
    l = ledger_facts()
    paths = canonical_paths()

    gap = sorted(set(g["nodes"]) - g["with_edges"])
    rows = [classify(d, g, l, paths) for d in gap]

    # Documents admitted to the corpus with no Document NODE at all: a wider gap than the
    # task's premise, which counts only nodes. Reported, not classified into the six classes.
    no_node = sorted(set(l["rows"]) - set(g["nodes"]))
    counts = {c: sum(1 for r in rows if r["class"] == c) for c in CLASSES}

    out = {
        "generated_at": _now(), "database": config["neo4j"]["database"],
        "document_nodes": len(g["nodes"]),
        "documents_with_edges": len(g["with_edges"]),
        "gap_documents": len(gap),
        "counts": counts,
        "corpus_documents_in_manifest": len(l["rows"]),
        "manifest_documents_without_a_document_node": len(no_node),
        "manifest_documents_without_a_document_node_ids": no_node,
        "manifest_documents_without_a_document_node_epochs": sorted(
            {e for d in no_node for e in l["doc_epochs"].get(d, ["(none)"])}),
        "total_corpus_contributing_nothing": len(gap) + len(no_node),
        "rows": rows,
    }
    # §3: only the classes extraction would close. `excluded_by_design` is priced separately
    # and labelled as NOT in that set — it is a decision to revive, not a gap to fill.
    import yaml as _yaml
    from kg.extraction.chunker import load_config as _chunk_cfg
    ccfg = _chunk_cfg()
    to_run = [r for r in rows if r["class"] in ("never_queued", "queued_not_run")]
    band = int(_yaml.safe_load((REPO / "controls.yaml").read_text())["spend"]["daily_tokens"])
    est = estimate(to_run, ccfg)
    est_def = estimate([r for r in rows if r["class"] == "excluded_by_design"], ccfg)
    out["estimate"] = {
        "in_scope_classes": ["never_queued", "queued_not_run",
                             "run_failed (transient) — none present"],
        "to_run": est,
        "standing_daily_band": band,
        "inside_standing_band": est["tokens_at_chunk_floor"] <= band,
        "excluded_by_design_if_revived": est_def,
        "both_if_revived_tokens": est["tokens_at_chunk_floor"] + est_def["tokens_at_chunk_floor"],
        "note": ("Reserved-token estimate at the DD-022 first-call floor, an UPPER bound: the "
                 "guard switches to the run's own measured mean once it has settles. Nothing "
                 "was run and nothing was reserved."),
    }
    cqp = REPO / "assessment" / "cq" / "cq_set_v1.yaml"
    runp = REPO / "assessment" / "results" / "cq_v1_2026-09-04.jsonl"
    if cqp.is_file() and runp.is_file():
        out["cq_overlap"] = cq_overlap(rows, cqp, runp)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n",
                           encoding="utf-8")
    print(f"{len(gap)} gap documents; classes: {counts}")
    print(f"{len(no_node)} manifest documents have no Document node at all "
          f"(epochs: {', '.join(out['manifest_documents_without_a_document_node_epochs'])})")
    ov = out.get("cq_overlap")
    if ov:
        print(f"CQ overlap: {ov['cqs_with_at_least_one_unextracted_document_mentioning_their_terms']}"
              f" of {ov['cqs_term_testable']} term-testable CQs (of {ov['cqs_examined']} examined) "
              f"have >= 1 unextracted document mentioning their terms; "
              f"{ov['documents_with_readable_text']}/{len(rows)} documents had readable text")
    e = out["estimate"]
    print(f"estimate (§3 set): {e['to_run']['documents']} docs, {e['to_run']['chunks']} chunks, "
          f"{e['to_run']['tokens_at_chunk_floor']:,} tokens at the {CHUNK_FLOOR:,} floor — "
          f"{'INSIDE' if e['inside_standing_band'] else 'EXCEEDS'} the {e['standing_daily_band']:,} band")
    print(f"-> {Path(a.out).relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
