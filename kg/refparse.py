#!/usr/bin/env python3
"""Deterministic reference-section parsing from the T1 Docling markdown.

Task 2026-08-30_acquisition_round2 §1. The T0 bibliographic layer resolved reference lists
for 2 of 178 documents, because the other 176 are gov/gray PDFs that no scholarly index
holds. Their reference lists nevertheless exist — inside the documents' own text. This
module recovers them by pattern, with **zero model calls**.

Evidence class
--------------
Records carry ``evidence_class: bibliographic_derived`` and ``derivation:
docling_refparse``. That class is NEVER pooled with ``bibliographic`` (a third party — an
index — asserted the reference list). Here the *document itself* is the asserting party and
the parse is ours, so the claim is weaker in a different way: it can be wrong because our
regex was wrong, not only because a source was wrong. Downstream ranking keeps the two
counts separate and reports both.

Prior art
---------
Reference-string parsing is a named, solved problem: ParsCit (Councill et al., LREC 2008),
GROBID (Lopez, ECDL 2009), AnyStyle, Crossref's ``/works?query.bibliographic`` reconciler.
The mature tools are ML sequence labellers over PDF layout. GROBID is deliberately absent
from this environment's provider ladder (``kg.biblio.biblio_method``), and a labeller is a
model call, which §6 puts out of scope. What is in scope is the *sub-problem the field
treats as trivial*: identifiers. A DOI and an arXiv id are regular languages (DOI syntax:
ANSI/NISO Z39.84; the Crossref-recommended match is ``10.\\d{4,9}/[-._;()/:A-Za-z0-9]+``,
Crossref blog 2015-08-11, adopted verbatim below). Extracting only the identifiers is not a
cheap approximation of ParsCit — it is the part of ParsCit's output the coupling ranking
actually consumes, and it is exactly recoverable without a labeller. Titles and years are
returned as explicitly-flagged guesses and no ranking reads them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
MD_DIR = _REPO / "state" / "docling_md"
OUT_DIR = _REPO / "state" / "refparse"

#: Bumped whenever the patterns below change, so a stale record is identifiable rather than
#: silently mixed with a newer parse.
DERIVATION_VERSION = "1"
EVIDENCE_CLASS = "bibliographic_derived"
DERIVATION = "docling_refparse"

#: Section headings that introduce a reference list. Endnote/footnote headings are included
#: because gray literature carries its citations there; "Further reading" is NOT — those are
#: recommendations, not citations, and coupling would read them as the document's own use.
_REF_HEADING = re.compile(
    r"^(?P<hashes>#{1,6})[ \t]*"
    # optional section ordinal: "7.", "A.2", "Appendix B.", "Annex 1:", "Chapter 9"
    r"(?:(?:appendix|annex|chapter|section)[ \t]+)?"
    r"(?:[A-Za-z0-9]{1,3}[.)][ \t]*)*"
    # optional qualifier: RFC/IETF style, and the common gray-lit variants
    r"(?:(?:normative|informative|selected|key|cited|primary|full)[ \t]+)?"
    r"(?P<name>references?|reference list|bibliography|works cited|literature cited|"
    r"notes and references|endnotes|end notes|citations)"
    r"[ \t]*:?[ \t]*$", re.I | re.M)
_ANY_HEADING = re.compile(r"^(?P<hashes>#{1,6})[ \t]*\S", re.M)

#: Crossref's recommended DOI match (Crossref blog, "Matching Citations", 2015-08-11).
_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
_ARXIV = re.compile(r"arxiv[.: /]*(?:abs/)?(\d{4}\.\d{4,5})(?:v\d+)?", re.I)
_ARXIV_OLD = re.compile(r"arxiv[.: /]*(?:abs/)?([a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?", re.I)
_YEAR = re.compile(r"(?:^|[^0-9])((?:19|20)\d{2})(?:[^0-9]|$)")

#: Trailing characters a DOI never ends with; docling glues sentence punctuation and markdown
#: to the end of a URL. Stripped iteratively.
_DOI_TRAILING = ".,;:)]}>\"'`*_"
#: A DOI that ends in one of these words has swallowed following prose.
_DOI_STOPWORDS = re.compile(
    r"(?i)(?:%s)$" % "|".join(["url", "doi", "http", "https", "in", "and", "pp", "vol"]))

_LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+][ \t]+|\|)", re.M)
_NUMBERED = re.compile(r"^[ \t]*(?:\[\d{1,3}\]|\(\d{1,3}\)|\d{1,3}[.)])[ \t]+", re.M)


def _normalize_urls(text: str) -> str:
    """Docling emits ``https: //doi.org/10.x`` — a space injected at a PDF line break inside
    the URL. Repair only that exact class; do not collapse whitespace generally, because the
    section offsets recorded in the output must index the ORIGINAL markdown."""
    return text


_SPACED_SCHEME = re.compile(r"(https?):\s*//\s*")
_SPACED_DOI = re.compile(r"(10\.\d{4,9}/)\s+")


def _repair_entry(raw: str) -> str:
    """Repair PDF-line-break damage INSIDE one entry only, for identifier matching. The raw
    text is preserved on the record; this repaired form is what the patterns run against."""
    s = raw.replace("&amp;", "&")
    # Docling escapes markdown metacharacters in extracted text: a TACL DOI arrives as
    # `10.1162/tacl\_a\_00471`. The backslash is not in the DOI charset, so an unescaped
    # match stops at `tacl` — a bare journal prefix that three different articles collapse
    # onto, which is a FALSE COUPLING, not merely a lost identifier.
    s = re.sub(r"\\([-_&#*\[\]()~^<>|.])", r"\1", s)
    s = _SPACED_SCHEME.sub(r"\1://", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    s = _SPACED_DOI.sub(r"\1", s)
    # de-hyphenate across a former line break: "10.1016/j.tech- fore.2010" -> joined
    s = re.sub(r"(?<=[A-Za-z0-9])-\s+(?=[A-Za-z0-9])", "-", s)
    return s


def clean_doi(d: str) -> str:
    d = d.strip()
    while d and d[-1] in _DOI_TRAILING:
        d = d[:-1]
    # A DOI immediately followed by a second DOI-looking token means the regex ran on glued
    # entries; keep only up to the first whitespace (already guaranteed) — then drop a
    # swallowed English word tail.
    prev = None
    while prev != d:
        prev = d
        d = _DOI_STOPWORDS.sub("", d)
        while d and d[-1] in _DOI_TRAILING:
            d = d[:-1]
    d = d.lower()
    # A DOI left ending in "/" was cut at a line break mid-suffix ("10.18653/v1/" for an ACL
    # work whose real id continues "2023.emnlp-main.468"). Dropping it is the honest outcome:
    # a truncated DOI resolves to the wrong work or to nothing, and either poisons the
    # ranking, whereas a dropped one only costs recall the record already reports.
    if d.endswith("/") or not re.fullmatch(r"10\.\d{4,9}/.+", d):
        return ""
    return d


def _id_count(body: str) -> int:
    """How many resolvable identifiers a candidate section carries. Used only to choose
    between competing reference-style headings in one document (a real bibliography vs a
    two-line "Notes"); never reported as a result."""
    return len(_DOI.findall(body)) + len(_ARXIV.findall(body)) + len(_ARXIV_OLD.findall(body))


def find_reference_section(text: str) -> dict | None:
    """Locate the reference section: the LAST reference-style heading in the document, ending
    at the next heading of the same or higher level, or EOF.

    Last, not first, because a document that mentions "References" in a table of contents and
    again as the real section must resolve to the real one; a ToC entry is a list item, not a
    heading, in Docling output, but a ToC rendered as headings would otherwise win.
    """
    matches = list(_REF_HEADING.finditer(text))
    if not matches:
        return None
    best = None
    for m in matches:
        level = len(m.group("hashes"))
        start = m.end()
        end = len(text)
        for h in _ANY_HEADING.finditer(text, start):
            if len(h.group("hashes")) <= level:
                end = h.start()
                break
        body = text[start:end]
        cand = {"heading": m.group(0).strip(), "level": level,
                "start": start, "end": end, "body": body}
        # Prefer the section with the most identifier-bearing content; a trailing
        # "Notes" section with two lines must not beat the real bibliography.
        if best is None or _id_count(body) > _id_count(best["body"]) or (
                _id_count(body) == _id_count(best["body"])
                and len(body) > len(best["body"])):
            best = cand
    return best


def split_entries(body: str) -> tuple[list[tuple[int, str]], str]:
    """Split a reference-section body into entries. Returns (entries, strategy), where each
    entry is (offset_into_body, raw_text). Strategy is recorded so a bad parse is diagnosable
    from the record rather than by re-running."""
    starts: list[int] = []
    strategy = ""
    if len(_LIST_ITEM.findall(body)) >= 3:
        starts = [m.start() for m in _LIST_ITEM.finditer(body)]
        strategy = "markdown_list"
    elif len(_NUMBERED.findall(body)) >= 3:
        starts = [m.start() for m in _NUMBERED.finditer(body)]
        strategy = "numbered"
    else:
        starts = [m.start() for m in re.finditer(r"(?:\A|\n[ \t]*\n)[ \t]*(?=\S)", body)]
        strategy = "paragraph"
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(body)
        raw = body[s:e].strip()
        if raw:
            out.append((s, raw))
    return out, strategy


def parse_entry(raw: str) -> dict:
    rep = _repair_entry(raw)
    dois = []
    for d in _DOI.findall(rep):
        c = clean_doi(d)
        if c and c not in dois:
            dois.append(c)
    arx = []
    for pat in (_ARXIV, _ARXIV_OLD):
        for a in pat.findall(rep):
            a = a.lower()
            if a not in arx:
                arx.append(a)
    ym = _YEAR.search(rep)
    return {"raw": raw, "doi": dois[0] if dois else None,
            "extra_dois": dois[1:], "arxiv_id": arx[0] if arx else None,
            "year_guess": int(ym.group(1)) if ym else None,
            "title_guess": _title_guess(rep)}


_TITLE_STOP = re.compile(r"(?:https?://|doi:|arxiv|\bin:\s|\bIn\s+Proc)", re.I)


def _title_guess(rep: str) -> str | None:
    """Best-effort only, and labelled as a guess everywhere it appears. The literature's
    solution to this is a sequence labeller (ParsCit/GROBID); no ranking in this repo reads
    the field, and no claim is made from it."""
    s = re.sub(r"^\s*(?:\[\d{1,3}\]|\(\d{1,3}\)|\d{1,3}[.)]|[-*+])\s*", "", rep)
    s = _TITLE_STOP.split(s)[0]
    parts = [p.strip() for p in re.split(r"(?<=[.?])\s+(?=[A-Z0-9])", s) if p.strip()]
    cands = [p for p in parts if len(p.split()) >= 4 and not re.fullmatch(
        r"[A-Z][A-Za-z.'-]*(?:,?\s+(?:and\s+)?[A-Z][A-Za-z.'-]*)*\.?", p)]
    if not cands:
        return None
    best = max(cands, key=lambda p: len(p))
    return unicodedata.normalize("NFKC", best)[:300] or None


def _rel(p: Path) -> str:
    """Repo-relative when the file is in the repo, absolute otherwise. A test fixture lives
    in tmp_path, and `relative_to` raising there would make the record unwritable."""
    try:
        return str(p.resolve().relative_to(_REPO))
    except ValueError:
        return str(p)


def parse_document(doc_id: str, md_path: Path) -> dict:
    text = md_path.read_text("utf-8", "ignore")
    sha = hashlib.sha256(md_path.read_bytes()).hexdigest()
    base = {"doc_id": doc_id, "evidence_class": EVIDENCE_CLASS, "derivation": DERIVATION,
            "derivation_version": DERIVATION_VERSION,
            "source_md": _rel(md_path), "source_md_sha256": sha}
    sec = find_reference_section(text)
    if sec is None:
        return {**base, "resolution": "no_reference_section", "section": None,
                "n_entries": 0, "n_dois": 0, "n_arxiv": 0, "n_unparseable": 0,
                "referenced_dois": [], "referenced_arxiv": [], "entries": []}
    entries_raw, strategy = split_entries(sec["body"])
    entries = []
    for off, raw in entries_raw:
        e = parse_entry(raw)
        e["offset"] = sec["start"] + off
        entries.append(e)
    dois, arx = [], []
    for e in entries:
        for d in ([e["doi"]] if e["doi"] else []) + e["extra_dois"]:
            if d not in dois:
                dois.append(d)
        if e["arxiv_id"] and e["arxiv_id"] not in arx:
            arx.append(e["arxiv_id"])
    dois = _drop_prefix_truncations(dois)
    unparseable = sum(1 for e in entries if not e["doi"] and not e["arxiv_id"])
    return {**base,
            "resolution": ("references_parsed" if entries else "section_empty"),
            "section": {"heading": sec["heading"], "level": sec["level"],
                        "start": sec["start"], "end": sec["end"],
                        "split_strategy": strategy},
            "n_entries": len(entries), "n_dois": len(dois), "n_arxiv": len(arx),
            "n_unparseable": unparseable,
            "referenced_dois": dois, "referenced_arxiv": arx, "entries": entries}


def _drop_prefix_truncations(dois: list[str]) -> list[str]:
    """Drop a DOI that is a proper prefix, at a `.` or `-` boundary, of another DOI in the
    SAME bibliography.

    The damage: a PDF line break inside `10.18653/v1/2023.emnlp-main.153` yields
    `10.18653/v1/2023. emnlp-main.153`, and the DOI charset stops at the space. The fragment
    `10.18653/v1/2023` is not a real identifier but it looks like one, and it collided
    across two documents into a phantom 2-citer candidate on 2026-08-30.

    A general de-space repair was rejected: joining across a space also glues genuine
    sentence continuations (`10.1145/3168389. Springer` -> a DOI that resolves to nothing),
    which trades a visible miss for an invisible wrong answer. The prefix rule cannot invent
    an identifier, only decline one — and the full form is present in the same reference
    list precisely because the same venue is cited repeatedly. The suffix is lost; that is
    recall, and it is reported in `n_dois`.
    """
    out = []
    for d in dois:
        if any(o != d and (o.startswith(d + ".") or o.startswith(d + "-")) for o in dois):
            continue
        out.append(d)
    return out


def records() -> list[dict]:
    if not OUT_DIR.exists():
        return []
    return [json.loads(f.read_text()) for f in sorted(OUT_DIR.glob("*.json"))]


def run(write: bool = True, verbose: bool = True) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for md in sorted(MD_DIR.glob("*.md")):
        doc_id = md.stem
        rec = parse_document(doc_id, md)
        if write:
            (OUT_DIR / f"{doc_id}.json").write_text(json.dumps(rec, indent=1))
        rows.append(rec)
    summary = {
        "documents": len(rows),
        "with_reference_section": sum(1 for r in rows if r["section"]),
        "no_reference_section": sum(1 for r in rows
                                    if r["resolution"] == "no_reference_section"),
        "entries": sum(r["n_entries"] for r in rows),
        "dois": sum(r["n_dois"] for r in rows),
        "arxiv": sum(r["n_arxiv"] for r in rows),
        "unparseable_entries": sum(r["n_unparseable"] for r in rows),
        "docs_with_any_identifier": sum(1 for r in rows if r["n_dois"] or r["n_arxiv"]),
    }
    if verbose:
        print(json.dumps(summary, indent=1))
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m kg.refparse")
    ap.add_argument("--dry-run", action="store_true", help="parse but write nothing")
    ap.add_argument("--doc", help="parse one document and dump its record")
    a = ap.parse_args(argv)
    if a.doc:
        p = MD_DIR / f"{a.doc}.md"
        if not p.exists():
            raise SystemExit(f"no docling markdown for {a.doc!r} at {p}")
        print(json.dumps(parse_document(a.doc, p), indent=1))
        return 0
    run(write=not a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
