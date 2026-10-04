#!/usr/bin/env python3
"""Reconcile this corpus against the FSS policy graph, and compare one document across both.

Task `cc_tasks/2026-10-02_commerce_guidance_admission.md` decisions 5, 6 and 10 (ADDENDUM-01).
**Zero model spend, no network.** Both graphs are read through the local Neo4j server in READ
sessions: `fss-policy-kg` (the FSS policy graph, the database the `icsp_notebook` repo projects)
and `seldon-ai-readiness-kg` (this one). Nothing in either database or in the FSS repository is
written. The FSS ledger (`icsp_notebook/corpus/manifest.yaml`) is read for source URLs and file
paths, and FSS corpus files are hashed in place.

Phases:

  glossary   decision 10 — the ground truth, fixed before either graph is queried: the defined
             terms of the Commerce guidance's appendix A1, parsed by script from the text this
             repo's extractor reads (`run_bulk_extraction.doc_text`), written to
             `docs/research/2026-10-02_commerce_guidance_glossary_terms.csv`.
  reconcile  decision 5 — every FSS Document matched to this manifest by primary URL, then
             content hash, then normalised title; the unmatched FSS documents screened under
             the 2026-08-24 triage rules (`scripts/fss_screen_2026-10-02.yaml`, one row per
             document with its clause); markdown + CSV under `docs/research/`.
  audit      decision 6 — the five phrases, definition layer versus text layer, both graphs.
  pipelines  decision 10 — the N glossary terms by graph: Definition node or not.

    /opt/anaconda3/bin/python3 scripts/fss_airkg_reconciliation.py --phase glossary
    /opt/anaconda3/bin/python3 scripts/fss_airkg_reconciliation.py --phase reconcile
    /opt/anaconda3/bin/python3 scripts/fss_airkg_reconciliation.py --phase audit
    /opt/anaconda3/bin/python3 scripts/fss_airkg_reconciliation.py --phase pipelines
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

TASK = "cc_tasks/2026-10-02_commerce_guidance_admission.md"
OUT = REPO / "docs" / "research"
STATE = REPO / "state"

FSS_DB = "fss-policy-kg"
AIRKG_DB = "seldon-ai-readiness-kg"
FSS_REPO = Path.home() / "GitHub" / "icsp_notebook"
FSS_LEDGER = FSS_REPO / "corpus" / "manifest.yaml"
FSS_DOC = "doc_genai_open_data_2025"
DOC_ID = "generative-ai-and-open-data-guidelines-and-best-practices-de"
SCREEN = REPO / "scripts" / "fss_screen_2026-10-02.yaml"

GLOSSARY_CSV = OUT / "2026-10-02_commerce_guidance_glossary_terms.csv"
RECON_CSV = OUT / "2026-10-02_fss_vs_airkg_corpus_reconciliation.csv"
RECON_JSON = STATE / "fss_vs_airkg_reconciliation_2026-10-02.json"
AUDIT_JSON = STATE / "definition_lookup_audit_2026-10-02.json"
PIPELINES_JSON = STATE / "commerce_two_pipelines_2026-10-02.json"

#: Decision 6's phrases, verbatim from the task.
PHRASES = ("AI-ready data", "AI-readiness", "data readiness", "machine-readable",
           "fitness for use")

#: The trustgraph benchmark's matching rule, as its task file states it
#: (`cc_tasks/2026-08-23_trustgraph_benchmark.md` line 14): "matching by type +
#: normalized-text similarity >= 0.8". The benchmark's matcher was never committed, so the
#: similarity function here is `difflib.SequenceMatcher.ratio` over `fold()`ed text, and the
#: RESULT says it is a reconstruction.
TG_SIMILARITY = 0.8

# ---------------------------------------------------------------- shared helpers


def fold(s: str | None) -> str:
    """NFKC + whitespace folding (ADDENDUM-01 decision 10's normaliser). Case is kept."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "")).strip()


def norm_title(s: str | None) -> str:
    """Lower-cased, punctuation-free, whitespace-collapsed title for the third match key."""
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"\([^)]*\)", " ", s)              # parentheticals: "(Department of Commerce, 2025)"
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_url(u: str | None) -> str:
    if not u:
        return ""
    u = u.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def driver():
    from neo4j import GraphDatabase
    user = os.environ.get("NEO4J_USER")
    pw = os.environ.get("NEO4J_PASS")
    if not (user and pw):
        envf = Path.home() / ".wintermute" / ".env"
        if not envf.is_file():
            raise SystemExit("FATAL: NEO4J_USER/NEO4J_PASS unset and ~/.wintermute/.env absent")
        kv = dict(l.split("=", 1) for l in envf.read_text().splitlines()
                  if "=" in l and not l.lstrip().startswith("#"))
        user = user or kv.get("NEO4J_USER", "").strip().strip('"')
        pw = pw or kv.get("NEO4J_PASS", "").strip().strip('"')
    if not (user and pw):
        raise SystemExit("FATAL: NEO4J_USER / NEO4J_PASS not found in env or ~/.wintermute/.env")
    return GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                                auth=(user, pw))


def read(drv, db: str, cypher: str, **params) -> list[dict]:
    with drv.session(database=db, default_access_mode="READ") as s:
        return [r.data() for r in s.run(cypher, **params)]


# ---------------------------------------------------------------- decision 10: glossary

#: Appendix A1's entries open a paragraph as `<term><footnote number>: <definition>`. The
#: footnote numbers run 80..129 in this document; 123 is a figure credit, not a term.
_ENTRY = re.compile(r"(?m)^(?P<term>[A-Za-z][^\n:]{0,120}?)\s?(?P<fn>\d{2,3})\s?:\s(?P<rest>.*)$")
_FOOTNOTE_LINE = re.compile(r"^\s*\d{2,3} \S")
_PAGE_HEADER = "Generative Artificial Intelligence and Open Data: Guidelines and Best Practices"


def glossary_section(text: str) -> tuple[int, int]:
    start = text.find("A1. Glossary and additional background information \nAI-ready")
    if start < 0:
        raise SystemExit("FATAL: appendix A1 heading not found in the extracted text")
    end = text.find("A2. Frequently recommended", start)
    if end < 0:
        raise SystemExit("FATAL: appendix A2 heading (A1's end) not found")
    return start, end


def parse_glossary(text: str) -> list[dict]:
    """[{term, footnote, definition, char_start, char_end}] in document order.

    A definition is the entry's paragraph with footnote blocks, page numbers, running headers
    and figure captions removed; an entry that a page break splits (`Machine learning`) is
    rejoined. `definition` is what a grounding span would be checked against."""
    s, e = glossary_section(text)
    sec = text[s:e]
    hits = [m for m in _ENTRY.finditer(sec)
            if not _FOOTNOTE_LINE.match(m.group(0)) and "Figure" not in m.group("term")]
    out = []
    for i, m in enumerate(hits):
        stop = hits[i + 1].start() if i + 1 < len(hits) else len(sec)
        lines = sec[m.start("rest"):stop].split("\n")
        body, in_footnotes = [], False
        for ln in lines:
            st = ln.strip()
            if _FOOTNOTE_LINE.match(ln):
                in_footnotes = True
                continue
            if st.startswith(_PAGE_HEADER):
                in_footnotes = False
                continue
            if in_footnotes or re.fullmatch(r"\d{1,3}", st) or st.startswith("Figure A1."):
                continue
            body.append(st)
        definition = fold(" ".join(body))
        out.append({"term": fold(m.group("term")), "footnote": int(m.group("fn")),
                    "definition": definition,
                    "char_start": s + m.start(), "char_end": s + stop})
    return out


def phase_glossary() -> int:
    import run_bulk_extraction as rbe
    src = REPO / "corpus" / "bulk" / f"{DOC_ID}.pdf"
    text = rbe.doc_text(src, DOC_ID)
    terms = parse_glossary(text)
    fns = [t["footnote"] for t in terms]
    expected = [n for n in range(80, 130) if n != 123]
    if fns != expected:
        raise SystemExit(f"FATAL: glossary footnotes {fns} are not 80..129 minus 123; the "
                         f"parser missed or invented an entry")
    with GLOSSARY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "term", "footnote", "definition",
                                          "char_start", "char_end"])
        w.writeheader()
        for i, t in enumerate(terms, 1):
            w.writerow({"n": i, **t})
    print(json.dumps({"N": len(terms), "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                      "csv": str(GLOSSARY_CSV.relative_to(REPO))}, indent=1))
    return 0


def load_glossary() -> list[dict]:
    with GLOSSARY_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- decision 5: reconcile

def fss_ledger() -> dict[str, dict]:
    data = yaml.safe_load(FSS_LEDGER.read_text(encoding="utf-8"))
    docs = data.get("documents") if isinstance(data, dict) else data
    return {d["id"]: d for d in docs if isinstance(d, dict) and d.get("id")}


def airkg_manifest() -> list[dict]:
    m = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    entries = m["entries"]
    return list(entries.values()) if isinstance(entries, dict) else entries


def phase_reconcile() -> int:
    drv = driver()
    fss_docs = read(drv, FSS_DB, "MATCH (d:Document) RETURN d.id AS id, d.title AS title, "
                    "d.category AS category, d.source_url AS source_url, "
                    "d.local_path AS local_path, d.agency_or_govwide AS agency ORDER BY d.id")
    ledger = fss_ledger()
    entries = airkg_manifest()
    by_url, by_sha, by_title = {}, {}, {}
    for e in entries:
        ident = e.get("identity") or {}
        row = (e["doc_id"], (e.get("screening") or {}).get("decision"))
        if ident.get("source_url"):
            by_url.setdefault(norm_url(ident["source_url"]), row)
        if ident.get("sha256"):
            by_sha.setdefault(ident["sha256"], row)
        if ident.get("title"):
            by_title.setdefault(norm_title(ident["title"]), row)

    screen = yaml.safe_load(SCREEN.read_text(encoding="utf-8")) if SCREEN.is_file() else {}
    rows = []
    for d in fss_docs:
        led = ledger.get(d["id"], {})
        urls = [u for u in (d.get("source_url"), led.get("source_url"),
                            led.get("direct_download_url")) if u]
        sha = None
        lp = d.get("local_path") or led.get("local_path")
        if lp and (FSS_REPO / lp).is_file():
            sha = hashlib.sha256((FSS_REPO / lp).read_bytes()).hexdigest()
        match, key = None, None
        for u in urls:
            if norm_url(u) in by_url:
                match, key = by_url[norm_url(u)], "primary_url"
                break
        if not match and sha and sha in by_sha:
            match, key = by_sha[sha], "content_hash"
        if not match and norm_title(d["title"]) in by_title:
            match, key = by_title[norm_title(d["title"])], "normalised_title"
        sc = (screen.get("documents") or {}).get(d["id"], {}) if not match else {}
        rows.append({
            "fss_doc_id": d["id"], "title": d["title"], "source_type": d.get("category"),
            "agency": d.get("agency"), "source_url": urls[0] if urls else None,
            "fss_sha256": sha, "matched_by": key,
            "airkg_doc_id": match[0] if match else None,
            "airkg_decision": match[1] if match else None,
            "screen": sc.get("screen") if not match else None,
            "clause": sc.get("clause") if not match else None,
            "screen_reason": sc.get("reason") if not match else None,
        })
    unscreened = [r["fss_doc_id"] for r in rows if not r["matched_by"] and not r["screen"]]
    with RECON_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    matched_ids = {r["airkg_doc_id"] for r in rows if r["airkg_doc_id"]}
    included = [e for e in entries if (e.get("screening") or {}).get("decision") == "included"]
    summary = {
        "fss_documents": len(fss_docs),
        "matched": sum(1 for r in rows if r["matched_by"]),
        "matched_by": {k: sum(1 for r in rows if r["matched_by"] == k)
                       for k in ("primary_url", "content_hash", "normalised_title")},
        "matched_to_included": sum(1 for r in rows if r["airkg_decision"] == "included"),
        "matched_to_not_included": sorted(
            (r["fss_doc_id"], r["airkg_doc_id"], r["airkg_decision"]) for r in rows
            if r["matched_by"] and r["airkg_decision"] != "included"),
        "fss_only": sum(1 for r in rows if not r["matched_by"]),
        "fss_only_by_screen": {k: sum(1 for r in rows if not r["matched_by"] and r["screen"] == k)
                               for k in ("include_candidate", "excluded_by_rule", "off_topic")},
        "unscreened": unscreened,
        "airkg_included": len(included),
        "airkg_only_included": len([e for e in included if e["doc_id"] not in matched_ids]),
        "airkg_entries_all_decisions": len(entries),
    }
    RECON_JSON.write_text(json.dumps({"task": TASK, "summary": summary, "rows": rows},
                                     indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=str))
    return 0 if not unscreened else 3


# ---------------------------------------------------------------- decision 6: audit

def phrase_regex(phrase: str) -> str:
    """Case-insensitive, hyphen- and whitespace-tolerant: "AI-readiness" also finds "AI
    readiness" and the FSS text layer's doubled spaces ("AI  model"). A literal CONTAINS would
    report the FSS graph's statutory "machine readable" as absent because of a space."""
    toks = [re.escape(t) for t in re.split(r"[-\s]+", phrase.lower()) if t]
    return r"(?is).*\b" + r"[-\s]*".join(toks) + r".*"


def _definitional_regex(phrase: str) -> str:
    """A text-layer row that READS as a definition of the phrase: the phrase (optionally
    quoted, optionally followed by a footnote marker or "when used ...") followed by ":",
    "means", "is defined as" or "refers to". Those are the rows a definitional lookup should
    find; the matched rows are listed so the call can be checked, not trusted."""
    toks = [re.escape(t) for t in re.split(r"[-\s]+", phrase.lower()) if t]
    p = r"[-\s]*".join(toks)
    q = r"[\"'“”‘’`]*"
    return (r"(?is).*\b" + p + q + r"\s*\d{0,3}\s*(,[^.]{0,80}?)?"
            r"(:|\bmeans\b|\bis defined as\b|\brefers to\b).*")


def phase_audit() -> int:
    drv = driver()
    out = {"fss": {}, "airkg": {}}
    for ph in PHRASES:
        rx, drx = phrase_regex(ph), _definitional_regex(ph)
        # FSS: the definition layer is `get_definitions` — Definition.term_surface /
        # verbatim_text; the text layer is `search_text` — Segment.text.
        f_def_term = read(drv, FSS_DB, "MATCH (d:Definition) WHERE d.term_surface =~ $rx "
                          "RETURN count(d) AS n", rx=rx)[0]["n"]
        f_def_any = read(drv, FSS_DB, "MATCH (d:Definition) WHERE d.term_surface =~ $rx "
                         "OR d.verbatim_text =~ $rx RETURN count(d) AS n", rx=rx)[0]["n"]
        f_seg = read(drv, FSS_DB, "MATCH (s:Segment) WHERE s.text =~ $rx "
                     "RETURN count(s) AS n, count(DISTINCT split(s.seg_id,'#')[0]) AS docs",
                     rx=rx)[0]
        f_defn_like = read(drv, FSS_DB, "MATCH (s:Segment) WHERE s.text =~ $rx "
                           "OPTIONAL MATCH (s)-[:DEFINES]->(d:Definition) "
                           "RETURN s.seg_id AS seg, left(s.text, 240) AS text, "
                           "collect(d.term_surface) AS defines ORDER BY seg", rx=drx)
        # "Without a Definition OF THIS PHRASE": a segment can define something else.
        def defines_phrase(r):
            return any(re.match(rx, t or "") for t in r["defines"])
        out["fss"][ph] = {"definition_term": f_def_term, "definition_term_or_text": f_def_any,
                          "segment": f_seg["n"], "segment_docs": f_seg["docs"],
                          "definitional_segments": f_defn_like,
                          "definitional_segments_without_definition":
                              [r["seg"] for r in f_defn_like if not defines_phrase(r)]}
        # This graph: the definition layer is Definition.term / verbatim; the text layer is
        # every grounded span on any node (there is no Segment label here — the retained
        # source text is the grounding span, invariant 3).
        a_def_term = read(drv, AIRKG_DB, "MATCH (d:Definition) WHERE d.term =~ $rx "
                          "RETURN count(d) AS n", rx=rx)[0]["n"]
        a_def_any = read(drv, AIRKG_DB, "MATCH (d:Definition) WHERE d.term =~ $rx "
                         "OR d.grounding_span =~ $rx OR d.verbatim_text =~ $rx "
                         "RETURN count(d) AS n", rx=rx)[0]["n"]
        a_span = read(drv, AIRKG_DB, "MATCH (n) WHERE n.grounding_span =~ $rx "
                      "RETURN labels(n)[0] AS label, count(n) AS n ORDER BY n DESC, label",
                      rx=rx)
        a_defn_like = read(drv, AIRKG_DB, "MATCH (n) WHERE n.grounding_span =~ $rx "
                           "RETURN labels(n)[0] AS label, n.key AS key, n.term AS term, "
                           "left(n.grounding_span, 240) AS text ORDER BY label, key", rx=drx)
        out["airkg"][ph] = {"definition_term": a_def_term, "definition_term_or_text": a_def_any,
                            "grounded_span_by_label": a_span,
                            "definitional_spans": a_defn_like,
                            "definitional_spans_not_on_definition":
                                [r["key"] for r in a_defn_like if r["label"] != "Definition"]}
    AUDIT_JSON.write_text(json.dumps({"task": TASK, "phrases": PHRASES, "audit": out},
                                     indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({g: {p: {k: v for k, v in r.items() if k not in
                              ("definitional_segments", "definitional_spans")}
                          for p, r in d.items()} for g, d in out.items()}, indent=1, default=str))
    return 0


# ---------------------------------------------------------------- decision 10: pipelines

def glossary_proposals(gloss: list[dict]) -> tuple[dict, dict]:
    """({lower(term): {chunk, verbatim}}, {chunk: quarantine_reasons}) over the chunks whose
    range overlaps appendix A1, read from the persisted raw responses and the shard."""
    lo = min(int(g["char_start"]) for g in gloss)
    hi = max(int(g["char_end"]) for g in gloss)
    reasons, chunks = {}, set()
    shard = REPO / "events" / "batch-023.jsonl"
    for line in shard.read_text(encoding="utf-8").splitlines():
        if DOC_ID not in line or '"chunk_metrics"' not in line:
            continue
        e = json.loads(line)
        if e.get("doc_id") == DOC_ID and e["chunk_end"] > lo and e["chunk_start"] < hi:
            chunks.add(e["chunk_id"])
            reasons[e["chunk_id"]] = e.get("quarantine_reasons") or {}
    proposed = {}
    for cid in sorted(chunks):
        tag = cid.split("#")[1]
        raws = sorted((REPO / "events" / "raw" / "bulk_v038").glob(f"{DOC_ID}.{tag}.*.json"))
        if not raws:
            raise SystemExit(f"FATAL: no raw response persisted for {cid}")
        # The pipeline's own envelope reader (fenced or bare JSON), as chunked_pilot uses it.
        from kg.extraction import model_stub
        body = model_stub._extract_json(
            json.loads(raws[-1].read_text(encoding="utf-8")).get("raw_result") or "")
        for d in body.get("definitions") or []:
            proposed.setdefault((d.get("term") or "").lower(),
                                {"chunk": cid, "verbatim": d.get("verbatim_text")})
    return proposed, reasons


def phase_pipelines() -> int:
    from kg.extraction import grounding
    drv = driver()
    gloss = load_glossary()
    import run_bulk_extraction as rbe
    text = rbe.doc_text(REPO / "corpus" / "bulk" / f"{DOC_ID}.pdf", DOC_ID)
    # This graph: every Definition anchored to the document.
    a_defs = read(drv, AIRKG_DB,
                  "MATCH (d:Definition {doc_id: $doc}) "
                  "RETURN d.key AS id, d.term AS term, d.grounding_span AS span, "
                  "d.location AS location, d.prov_extraction_event_id AS extraction_event "
                  "ORDER BY d.key", doc=DOC_ID)
    f_defs = read(drv, FSS_DB, "MATCH (d:Definition) WHERE d.def_id STARTS WITH $p "
                  "RETURN d.def_id AS id, d.term_surface AS term, d.verbatim_text AS text",
                  p=FSS_DOC + "#")
    f_segs = read(drv, FSS_DB, "MATCH (:Document {id:$doc})-[:CONTAINS]->(s:Segment) "
                  "RETURN s.seg_id AS id, s.text AS text, s.seg_type AS type", doc=FSS_DOC)
    rows = []
    for g in gloss:
        entry = fold(f"{g['term']} {g['definition']}")
        gdef = fold(g["definition"])
        # This graph, ADDENDUM-01 decision 10: a Definition whose grounding span IS the
        # glossary entry. Operationalised on the entry's own source text (the slice of the
        # document the CSV's char offsets name), normalised exactly as the grounding validator
        # normalises (`grounding.normalize`): the span names the term's entry ("<term><fn>:")
        # and either lies inside the entry or contains the entry's opening 60 characters. A
        # span that stops after the entry's first sentence still counts — it is the entry;
        # a heading prefix ("Glossary and additional background information") still counts —
        # the entry is inside it.
        raw_entry = grounding.normalize(text[int(g["char_start"]):int(g["char_end"])])
        opener = grounding.normalize(text[int(g["char_start"]):int(g["char_start"]) + 60])
        label = grounding.normalize(f"{g['term']}{g['footnote']}:")
        def ours_match(d):
            span = grounding.normalize(d.get("span") or "")
            if label not in span and label not in raw_entry[:len(label) + 2]:
                return False
            body = span[span.find(label):] if label in span else span
            return bool(body) and (body in raw_entry or opener in span)
        a_hits = [d for d in a_defs if ours_match(d)]
        # FSS, decision 10: source_doc = the document and verbatim text matching the entry
        # after NFKC + whitespace folding.
        f_hits = [d for d in f_defs if fold(gdef)[:60] in fold(d.get("text"))]
        seg_hits = [s for s in f_segs if fold(gdef)[:60] in fold(s.get("text"))]
        # Secondary: the trustgraph rule, type + normalised-text similarity >= 0.8, between
        # each graph's best Definition and the glossary entry.
        def best(defs, key):
            sc = [(difflib.SequenceMatcher(None, fold(d.get(key)).lower(), entry.lower(),
                                          autojunk=False).ratio(), d)
                  for d in defs]
            return max(sc, key=lambda x: x[0]) if sc else (0.0, None)
        a_sim, a_best = best(a_defs, "span")
        f_sim, f_best = best(f_defs, "text")
        rows.append({
            "n": int(g["n"]), "term": g["term"],
            "airkg_definition": bool(a_hits),
            "airkg_ids": [d["id"] for d in a_hits],
            "fss_definition": bool(f_hits), "fss_ids": [d["id"] for d in f_hits],
            "fss_segment_ids": [s["id"] for s in seg_hits],
            "tg_rule_airkg": a_sim >= TG_SIMILARITY, "tg_sim_airkg": round(a_sim, 3),
            "tg_best_airkg": a_best and a_best["id"],
            "tg_rule_fss": f_sim >= TG_SIMILARITY, "tg_sim_fss": round(f_sim, 3),
        })
    # What the model PROPOSED as a Definition for each glossary term, against what was
    # admitted. The parser keeps only per-chunk quarantine counts by reason (`chunk_metrics`),
    # not the quarantined items, so a proposed glossary Definition with no node is identified
    # by difference and its chunk's `quarantine_reasons` are reported beside it.
    proposed, reasons = glossary_proposals(gloss)
    for r in rows:
        p = proposed.get(r["term"].lower())
        r["model_proposed_definition"] = bool(p)
        r["proposed_in_chunk"] = p and p["chunk"]
        r["quarantined_at_parse"] = bool(p) and not r["airkg_definition"]
        r["chunk_quarantine_reasons"] = (reasons.get(p["chunk"]) if r["quarantined_at_parse"]
                                         else None)
    summary = {
        "N": len(gloss),
        "model_proposed_definition": sum(r["model_proposed_definition"] for r in rows),
        "quarantined_at_parse": [(r["term"], r["proposed_in_chunk"], r["chunk_quarantine_reasons"])
                                 for r in rows if r["quarantined_at_parse"]],
        "airkg_definition": sum(r["airkg_definition"] for r in rows),
        "fss_definition": sum(r["fss_definition"] for r in rows),
        "fss_segment_present": sum(bool(r["fss_segment_ids"]) for r in rows),
        "tg_rule_airkg": sum(r["tg_rule_airkg"] for r in rows),
        "tg_rule_fss": sum(r["tg_rule_fss"] for r in rows),
        "airkg_definitions_on_document": len(a_defs),
        "fss_definitions_on_document": len(f_defs),
        "fss_segments_on_document": len(f_segs),
        "divergent": [r["term"] for r in rows if r["airkg_definition"] != r["fss_definition"]],
    }
    PIPELINES_JSON.write_text(json.dumps({"task": TASK, "summary": summary, "rows": rows,
                                          "airkg_definitions": a_defs}, indent=1, default=str)
                              + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=str))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True,
                    choices=("glossary", "reconcile", "audit", "pipelines"))
    a = ap.parse_args(argv)
    return {"glossary": phase_glossary, "reconcile": phase_reconcile,
            "audit": phase_audit, "pipelines": phase_pipelines}[a.phase]()


if __name__ == "__main__":
    raise SystemExit(main())
