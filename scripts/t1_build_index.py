#!/usr/bin/env python3
"""T1 — structural index (task 2026-08-29_corpus_t0_t1_substrate §1).

Deterministic derivation from the admitted bytes: layout-aware conversion, chunking, full
text search, and local embeddings. **Zero model_stub calls** — Docling and
sentence-transformers run locally and are local parsing/embedding, which the task's non-goals
permit and its §1 requires.

`evidence_class` is `structural` on every record: derived mechanically from the document,
never asserted about it. Structural records never enter a validated stratum and are excluded
from faithfulness reporting by construction (task's binding rule).

`state/corpus_index.db` is a REBUILDABLE PROJECTION, never a source of truth. The sources are
the admitted bytes plus the cached Docling markdown; `--phase rebuild` proves the claim by
building a second database from scratch and diffing the counts. If that diff is ever
non-empty the projection has acquired state of its own and the claim is false.

Phases: convert (Docling -> state/docling_md/) | index (chunks + FTS5 + embeddings)
      | rebuild (projection proof) | table (docs/corpus/manifest_table.md)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg.extraction import chunker                                   # noqa: E402

MANIFEST = REPO / "corpus" / "manifest.json"
MD_DIR = REPO / "state" / "docling_md"
DB = REPO / "state" / "corpus_index.db"
BIBLIO = REPO / "state" / "biblio_cache"
TABLE_OUT = REPO / "docs" / "corpus" / "manifest_table.md"
PICKUP_OUT = REPO / "docs" / "corpus" / "operator_pickup.md"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # instrument metadata, recorded in db
TASK = "cc_tasks/2026-08-29_corpus_t0_t1_substrate.md"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS documents (
  doc_id TEXT PRIMARY KEY, title TEXT, year TEXT, doc_type TEXT, source_url TEXT,
  content_hash TEXT, local_path TEXT, converted_by TEXT, md_chars INTEGER,
  n_chunks INTEGER, evidence_class TEXT, fidelity TEXT);
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id TEXT PRIMARY KEY, doc_id TEXT, idx INTEGER, start INTEGER, end INTEGER,
  n_tokens INTEGER, breadcrumb TEXT, oversize INTEGER, text TEXT, evidence_class TEXT,
  fidelity TEXT);
CREATE INDEX IF NOT EXISTS chunks_doc ON chunks(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(chunk_id UNINDEXED, doc_id UNINDEXED, text);
CREATE TABLE IF NOT EXISTS embeddings (
  chunk_id TEXT PRIMARY KEY, model TEXT, dim INTEGER, vec BLOB);
CREATE TABLE IF NOT EXISTS biblio (
  doc_id TEXT PRIMARY KEY, resolution TEXT, metadata_source TEXT, doi TEXT,
  openalex_id TEXT, venue TEXT, cited_by_count INTEGER, n_refs INTEGER,
  evidence_class TEXT);
CREATE TABLE IF NOT EXISTS citation_edges (
  from_doc TEXT, to_doc TEXT, metadata_source TEXT, evidence_class TEXT,
  PRIMARY KEY (from_doc, to_doc));
CREATE TABLE IF NOT EXISTS coupling (
  doc_a TEXT, doc_b TEXT, shared_refs INTEGER, evidence_class TEXT,
  PRIMARY KEY (doc_a, doc_b));
"""


ERR_DIR = REPO / "state" / "convert_errors"
MAX_ERR_CHARS = 2000          # ADDENDUM-02 §4


def _short(exc: Exception, doc_id: str | None = None, n: int = MAX_ERR_CHARS) -> str:
    """Bounded exception text for the shared log; the RAW message goes to its own file.

    Docling's ConversionError embeds the entire PDF page dictionary. One failure wrote
    ~230,000 lines into the shared log and took the process down with it, so an unbounded
    exception message is not a diagnostic, it is a denial of service on your own run. The
    full text is still kept — per document, where it can be read on purpose."""
    raw = str(exc)
    if doc_id:
        ERR_DIR.mkdir(parents=True, exist_ok=True)
        (ERR_DIR / f"{doc_id}.err.txt").write_text(raw, encoding="utf-8")
    t = " ".join(raw.split())
    if len(t) <= n:
        return t
    tail = f" ...[truncated {len(t):,}->{n} chars"
    tail += f"; full text in state/convert_errors/{doc_id}.err.txt]" if doc_id else "]"
    return t[:n] + tail


def manifest_docs() -> dict[str, dict]:
    e = json.loads(MANIFEST.read_text())["entries"]
    return {k: v for k, v in e.items() if v["screening"]["decision"] == "included"}


def local_path(doc_id: str, entry: dict) -> Path | None:
    for d in ("bulk", "bulk_md", "pilot", "cisco", "kernel", "triage", "crosswalk"):
        for ext in ("pdf", "md", "html", "htm", "txt"):
            p = REPO / "corpus" / d / f"{doc_id}.{ext}"
            if p.exists():
                return p
    return None


# ------------------------------------------------------------------ convert
def phase_convert(a) -> int:
    """Docling for PDF/HTML; markdown passes through unchanged (already text)."""
    MD_DIR.mkdir(parents=True, exist_ok=True)
    docs = manifest_docs()
    conv = None
    done = skipped = failed = 0
    t_start = time.time()
    for i, (doc_id, entry) in enumerate(sorted(docs.items()), 1):
        out = MD_DIR / f"{doc_id}.md"
        src = local_path(doc_id, entry)
        if src is None:
            print(f"[{i}] MISSING  {doc_id}"); failed += 1; continue
        if out.exists() and not a.refresh:
            skipped += 1; continue
        if a.limit and done >= a.limit:
            break
        md = by = None
        note = None
        if src.suffix.lower() in (".md", ".txt"):
            md, by = src.read_text("utf-8", "ignore"), "passthrough"
        else:
            try:
                if conv is None:
                    from docling.document_converter import DocumentConverter
                    conv = DocumentConverter()
                t = time.time()
                md = conv.convert(str(src)).document.export_to_markdown()
                by = "docling"
                print(f"[{i}/{len(docs)}] {doc_id[:52]:<54} {time.time() - t:5.1f}s "
                      f"{len(md):>8,} chars", flush=True)
            except Exception as exc:
                # Docling raises ConversionError whose message embeds the entire PDF page
                # dictionary — one failure wrote 230k lines of log and took the process down
                # with it. The diagnosis is in the first line; the page dump is noise.
                note = f"{type(exc).__name__}: {_short(exc, doc_id)}"
                print(f"[{i}/{len(docs)}] DOCLING-FAIL {doc_id[:44]:<46} {note}", flush=True)
        if md is None and src.suffix.lower() == ".pdf":
            # Fallback so a Docling failure does not silently drop a document from the
            # index. pypdf is the KNOWN-DAMAGED converter (DD-023: dropped characters at line
            # breaks), so the record says so and the RESULT lists every document carrying it.
            # Degraded text that is labelled degraded beats a hole that is labelled nothing.
            try:
                from pypdf import PdfReader
                md = "\n\n".join((pg.extract_text() or "")
                                  for pg in PdfReader(str(src)).pages)
                by = "pypdf_fallback"
                print(f"          fallback pypdf -> {len(md):,} chars (fidelity DEGRADED)",
                      flush=True)
            except Exception as exc:
                note = f"{note} | pypdf: {_short(exc, doc_id)}"
        if not md:
            print(f"[{i}] FAIL     {doc_id}: {note}", flush=True)
            failed += 1
            continue
        out.write_text(md, encoding="utf-8")
        (MD_DIR / f"{doc_id}.meta.json").write_text(json.dumps(
            {"doc_id": doc_id, "converted_by": by, "source": str(src.relative_to(REPO)),
             "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
             "md_chars": len(md), "evidence_class": "structural",
             "fidelity": "degraded" if by == "pypdf_fallback" else "layout_aware",
             **({"docling_error": note} if note else {})}, indent=1))
        done += 1
    print(f"\nconvert: {done} converted, {skipped} cached, {failed} failed "
          f"({time.time() - t_start:.0f}s)")
    return 0 if failed == 0 else 1


# ------------------------------------------------------------------ index
def _connect(path: Path) -> sqlite3.Connection:
    c = sqlite3.connect(path)
    c.executescript(SCHEMA)
    return c


def build_index(path: Path, *, embed: bool = True, quiet: bool = False) -> dict:
    """Build the whole projection from sources. Returns row counts."""
    if path.exists():
        path.unlink()
    con = _connect(path)
    docs = manifest_docs()
    model = None
    if embed:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBED_MODEL)

    n_chunks_total = 0
    for doc_id, entry in sorted(docs.items()):
        md = MD_DIR / f"{doc_id}.md"
        if not md.exists():
            continue
        meta = json.loads((MD_DIR / f"{doc_id}.meta.json").read_text())
        text = md.read_text("utf-8", "ignore")
        try:
            cs = chunker.chunk_document(doc_id, text)
        except chunker.ChunkerError:
            cs = []
        idn = entry["identity"]
        fidelity = meta.get("fidelity", "layout_aware")
        con.execute("INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (doc_id, idn.get("title"), str(idn.get("pub_year") or ""),
                     idn.get("doc_type"), idn.get("source_url"), idn.get("sha256"),
                     meta["source"], meta["converted_by"], meta["md_chars"], len(cs),
                     "structural", fidelity))
        rows, fts, texts, ids = [], [], [], []
        for ch in cs:
            crumb = " > ".join(ch.heading_path)
            # ADDENDUM-02 §3: the fidelity flag rides on every chunk, so any downstream
            # derivation inherits it without having to join back to the document.
            rows.append((ch.chunk_id, doc_id, ch.index, ch.start, ch.end, ch.n_tokens,
                         crumb, int(ch.oversize), ch.text, "structural", fidelity))
            fts.append((ch.chunk_id, doc_id, ch.text))
            texts.append(ch.text); ids.append(ch.chunk_id)
        con.executemany("INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.executemany("INSERT INTO chunks_fts VALUES (?,?,?)", fts)
        n_chunks_total += len(rows)
        if model is not None and texts:
            vecs = model.encode(texts, batch_size=64, show_progress_bar=False,
                                normalize_embeddings=True)
            con.executemany("INSERT OR REPLACE INTO embeddings VALUES (?,?,?,?)",
                            [(i, EMBED_MODEL, int(v.shape[0]), v.astype("float32").tobytes())
                             for i, v in zip(ids, vecs)])
        if not quiet:
            print(f"  {doc_id[:56]:<58} {len(rows):>4} chunks", flush=True)

    # T0 projection into the same db (bibliographic class, kept in its own tables)
    doi_to_doc = {}
    for f in sorted(BIBLIO.glob("*.json")):
        r = json.loads(f.read_text())
        w = r.get("work") or {}
        doi = (w.get("doi") or r.get("doi") or "")
        doi = doi.replace("https://doi.org/", "").lower() or None
        refs = w.get("referenced_dois") or w.get("referenced_works") or []
        con.execute("INSERT OR REPLACE INTO biblio VALUES (?,?,?,?,?,?,?,?,?)",
                    (r["doc_id"], r.get("resolution"), r.get("metadata_source"), doi,
                     w.get("id"), w.get("host_venue"), w.get("cited_by_count"),
                     len(refs), "bibliographic"))
        if doi:
            doi_to_doc[doi] = r["doc_id"]
    # corpus-internal citation edges: both endpoints admitted (task §0.3)
    refs_by_doc: dict[str, set] = {}
    for f in sorted(BIBLIO.glob("*.json")):
        r = json.loads(f.read_text()); w = r.get("work") or {}
        refs = {d.lower() for d in (w.get("referenced_dois") or [])}
        refs_by_doc[r["doc_id"]] = refs
        for d in refs:
            if d in doi_to_doc and doi_to_doc[d] != r["doc_id"]:
                con.execute("INSERT OR REPLACE INTO citation_edges VALUES (?,?,?,?)",
                            (r["doc_id"], doi_to_doc[d], r.get("metadata_source"),
                             "bibliographic"))
    # bibliographic coupling: shared references between corpus members (Kessler 1963)
    ids_ = sorted(refs_by_doc)
    for i, a_ in enumerate(ids_):
        for b_ in ids_[i + 1:]:
            shared = len(refs_by_doc[a_] & refs_by_doc[b_])
            if shared:
                con.execute("INSERT OR REPLACE INTO coupling VALUES (?,?,?,?)",
                            (a_, b_, shared, "bibliographic"))
    con.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", [
        ("built_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        ("task", TASK), ("embed_model", EMBED_MODEL if embed else "none"),
        ("chunker_config", json.dumps(chunker.load_config())),
        ("projection", "REBUILDABLE — sources are the admitted bytes + state/docling_md"),
    ])
    con.commit()
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("documents", "chunks", "chunks_fts", "embeddings", "biblio",
                        "citation_edges", "coupling")}
    con.close()
    return counts


def phase_index(a) -> int:
    DB.parent.mkdir(parents=True, exist_ok=True)
    counts = build_index(DB, embed=not a.no_embed)
    print("\nindex counts:", json.dumps(counts, indent=1))
    return 0


def phase_rebuild(a) -> int:
    """Projection proof: rebuild into a scratch file and diff the counts."""
    if not DB.exists():
        print("FATAL: no index to compare against; run --phase index first")
        return 2
    con = _connect(DB)
    before = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("documents", "chunks", "chunks_fts", "embeddings", "biblio",
                        "citation_edges", "coupling")}
    con.close()
    scratch = DB.with_suffix(".rebuild.db")
    after = build_index(scratch, embed=not a.no_embed, quiet=True)
    scratch.unlink()
    same = before == after
    print(json.dumps({"before": before, "after": after, "identical": same}, indent=1))
    print("\nPROJECTION PROOF: " + ("PASS — rebuilt from sources, counts identical"
                                    if same else "FAIL — the db holds state its sources do not"))
    return 0 if same else 1


# ------------------------------------------------------------------ manifest table
def phase_table(a) -> int:
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    con = _connect(DB)
    rows = con.execute("""
        SELECT d.doc_id, d.title, d.year, d.doc_type, d.source_url, d.n_chunks,
               b.resolution, b.doi, b.cited_by_count
        FROM documents d LEFT JOIN biblio b ON b.doc_id = d.doc_id
        ORDER BY d.doc_id""").fetchall()
    n_t0 = sum(1 for r in rows if r[6] not in (None, "bibliographic_partial", "harvest_error"))
    L = [
        "# Corpus manifest table",
        "",
        f"Projection of `corpus/manifest.json` + the T0/T1 substrate, generated by "
        f"`scripts/t1_build_index.py --phase table` ({TASK}). **Rebuildable — do not "
        f"hand-edit.**", "",
        f"{len(rows)} admitted documents. **T0** = a bibliographic record was resolved from a "
        f"third party ({n_t0} of {len(rows)}). **T1** = converted and chunked into "
        f"`state/corpus_index.db`. **T2** = extracted into the graph — deliberately empty "
        f"corpus-wide: extraction waits on the v0.3.7 contract (DD-023), and this task is "
        f"forbidden from it.", "",
        "| doc_id | title | year | type | T0 | T1 chunks | T2 | DOI | cited_by |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for doc_id, title, year, dtype, url, nch, res, doi, cited in rows:
        t0 = "—" if res in (None, "bibliographic_partial", "harvest_error") else "✓"
        t1 = str(nch) if nch else "—"
        t = (title or "")[:58].replace("|", "/")
        L.append(f"| `{doc_id}` | {t} | {(year or '')[:4]} | {dtype or ''} | {t0} | {t1} "
                 f"| — | {doi or ''} | {cited if cited is not None else ''} |")
    TABLE_OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    con.close()
    print(f"wrote {TABLE_OUT} ({len(rows)} rows, T0 resolved {n_t0})")
    return 0


def phase_pickup(a) -> int:
    """ADDENDUM-02 §2 — the 'on me to get' queue, PROJECTED not hand-written.

    Every document whose bytes could be better: acquisition_blocked, manual_download_needed,
    or fidelity: degraded where a better source plausibly exists. Ordered by t2_priority
    (provisional ordering is acceptable and is labelled)."""
    from kg import biblio
    prio = {r["doc_id"]: r for r in biblio.t2_priority()}
    cov = biblio.coverage()
    con = _connect(DB)
    rows = []
    for doc_id, conv, fid, url in con.execute(
            "SELECT doc_id, converted_by, fidelity, source_url FROM documents "
            "WHERE fidelity='degraded'"):
        err = ERR_DIR / f"{doc_id}.err.txt"
        why = "Docling could not convert this PDF; text came from pypdf, the converter DD-023 "
        why += "names as damaged. A clean or born-digital copy would restore layout fidelity."
        rows.append((doc_id, "fidelity: degraded", why, url,
                     prio.get(doc_id, {}).get("crosswalk_demand", 0),
                     prio.get(doc_id, {}).get("t0_centrality", 0),
                     f"state/convert_errors/{doc_id}.err.txt" if err.exists() else ""))
    con.close()
    # acquisition_blocked comes from the event log, which is where the block was recorded
    from kg import eventlog
    for ev in eventlog.replay():
        if ev.get("event_type") == "acquisition_blocked":
            rows.append((ev.get("doc_id"), "acquisition_blocked",
                         " ".join(str(ev.get("reason", "")).split())[:300],
                         ev.get("primary_url"),
                         prio.get(ev.get("doc_id"), {}).get("crosswalk_demand", 0),
                         prio.get(ev.get("doc_id"), {}).get("t0_centrality", 0), ""))
    # The event log is append-only, so re-running an admission pass legitimately records the
    # same block twice. A PROJECTION must collapse them: last event wins, one row per doc.
    dedup = {}
    for r in rows:
        dedup[(r[0], r[1])] = r
    rows = sorted(dedup.values(), key=lambda r: (-r[4], -r[5], r[0]))
    L = ["# Operator pickup list", "",
         f"Things only a human can get. **Projected by "
         f"`scripts/t1_build_index.py --phase pickup` — do not hand-edit.** Regenerated "
         f"alongside `manifest_table.md`.", "",
         f"Ordered by `t2_priority` (crosswalk demand, then T0 centrality). That ordering is "
         f"**provisional — T0 coverage {cov['resolved']}/{cov['total']}**; the demand "
         f"component is coverage-independent and already final, the centrality component is "
         f"not. `python -m kg.biblio resume` refreshes both.", "",
         "| doc / candidate | state | why | best-known URL | demand | centrality | detail |",
         "|---|---|---|---|---|---|---|"]
    for d, st, why, url, dem, cen, det in rows:
        L.append(f"| `{d}` | {st} | {why} | {url or ''} | {dem} | {cen} "
                 f"| {('`' + det + '`') if det else ''} |")
    if not rows:
        L.append("| — | *(nothing queued)* | — | — | — | — | — |")
    L += ["", "## Not listed here", "",
          "Closed-access candidates from the coupling expansion: the candidate list "
          "(`acquisition_candidates.md`) currently reaches no work cited by 3+ corpus "
          "members, because reference lists exist for only "
          f"{cov['docs_with_references']} of {cov['total']} documents. When "
          "`kg.biblio resume` lifts T0 coverage, re-run this phase and the closed-access "
          "candidates will appear."]
    PICKUP_OUT.parent.mkdir(parents=True, exist_ok=True)
    PICKUP_OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {PICKUP_OUT} ({len(rows)} rows)")
    return 0


PHASES = {"convert": phase_convert, "index": phase_index, "rebuild": phase_rebuild,
          "table": phase_table, "pickup": phase_pickup}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--no-embed", action="store_true")
    a = ap.parse_args()
    return PHASES[a.phase](a)


if __name__ == "__main__":
    raise SystemExit(main())
