#!/usr/bin/env python3
"""§4.5 of task 2026-08-29_crosswalk_operationalization — unattributed-overlap self-check.

Mechanical n-gram check (the task permits exactly this): every N-word shingle of a draft is
compared against the shingles of the admitted source texts it draws on. A hit is reported
with its source; hits inside an explicitly quoted span (text between double quotes) are
reported separately, because a short attributed quote is allowed by §4.1 and an unattributed
overlap is not. The check reports; it never edits.

Zero model calls.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

STOP_HEADINGS = re.compile(r'^\s{0,3}#{1,6}\s')


def read_text(p: Path) -> str:
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return " ".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    raw = p.read_text("utf-8", "ignore")
    if p.suffix.lower() in (".html", ".htm"):
        raw = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', raw, flags=re.S)
        raw = re.sub(r'<[^>]+>', ' ', raw)
    return raw


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def shingles(ws: list[str], n: int) -> dict[tuple, int]:
    return {tuple(ws[i:i + n]): i for i in range(len(ws) - n + 1)}


QUOTE_RE = re.compile("[\u201c\u201d\"]([^\u201c\u201d\"]{1,400}?)[\u201c\u201d\"]")


def quoted_shingles(draft: str, n: int) -> set[tuple]:
    """Shingles that lie wholly inside a double-quoted span. §4.1 permits a short attributed
    quote, so an overlap inside quotation marks is compliant and an overlap outside them is
    not — the check must tell them apart or it cannot answer the question it was written for.
    Word-level containment, not character offsets: the draft and the source are compared as
    normalized word sequences, so the span test has to be too."""
    out = set()
    for m in QUOTE_RE.finditer(draft):
        qw = words(m.group(1))
        for i in range(len(qw) - n + 1):
            out.add(tuple(qw[i:i + n]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True, action="append")
    ap.add_argument("--sources", required=True, help="dir of admitted source files")
    ap.add_argument("-n", type=int, default=8, help="shingle length (task §4.5: >= 8 words)")
    a = ap.parse_args()

    src = {}
    for f in sorted(Path(a.sources).iterdir()):
        if f.suffix.lower() in (".pdf", ".html", ".htm", ".txt", ".md"):
            src[f.stem] = shingles(words(read_text(f)), a.n)
    print(f"sources indexed: {len(src)} ({', '.join(sorted(src))})")

    total_hits = 0
    for d in a.draft:
        dp = Path(d)
        raw = dp.read_text("utf-8")
        body = "\n".join(l for l in raw.splitlines() if not STOP_HEADINGS.match(l))
        # Drop the reference apparatus before comparing. The title of a cited work
        # necessarily matches its source and is not plagiarism — it is the citation. What
        # the check is for is BODY PROSE that reproduces source wording without attribution,
        # so: cut everything from the references heading (numbered or not), and drop
        # bibliography-style bullets and the document's own title block anywhere they appear.
        body = re.split(r'\n#+\s*(?:\d+\.\s*)?References\b', body)[0]
        keep = []
        for line in body.splitlines():
            t = line.strip()
            if re.match(r'^[-*]\s+\*\*', t):        # "- **Author** (year). *Title*. DOI..."
                continue
            if re.match(r'^\*\*(Status|Deliverable target|Frame|Companion|Audience)', t):
                continue
            keep.append(line)
        body = "\n".join(keep)
        # Inline code spans are identifiers, not prose. A doc_id such as
        # `fcsm-20-04-a-framework-for-data-quality` is how this project CITES a document, and
        # it necessarily matches any source that cites the same document — the same reason
        # reference entries are dropped above. Stripping them keeps the check aimed at
        # reproduced wording instead of flagging the citation apparatus as plagiarism.
        body = re.sub(r'`[^`]{1,200}`', ' ', body)
        qs = quoted_shingles(body, a.n)
        ws = words(body)
        dsh = shingles(ws, a.n)
        hits = []
        for sh, pos in dsh.items():
            for name, table in src.items():
                if sh in table:
                    hits.append((" ".join(sh), name, sh in qs))
                    break
        print(f"\n=== {dp.name}: {len(ws)} words, {len(dsh)} {a.n}-gram shingles ===")
        unattributed = [h for h in hits if not h[2]]
        if not unattributed:
            print(f"  NO unattributed {a.n}-word overlap with any admitted source. PASS")
        for text, name, inq in hits:
            print(f"  {'QUOTED  ' if inq else 'OVERLAP '} [{name}] {text}")
        total_hits += len(unattributed)
    print(f"\ntotal UNATTRIBUTED overlaps >= {a.n} words: {total_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
