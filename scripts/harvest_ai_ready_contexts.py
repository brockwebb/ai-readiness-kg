#!/usr/bin/env python3
"""Every sentence in the unextracted corpus that says "AI ready", "AI-ready" or "AI readiness",
with a locator. **Zero model spend** — file reads, a regex and a person's reading.

Task `cc_tasks/2026-09-04_extract_g1eval_17_and_rerun_ADDENDUM-02.md` §3a. The question behind
it: CQ-02 asks how the corpus defines "AI-ready data" and answers `partial`, and 23 of the
documents that contribute nothing to the graph mention its terms. Before anyone decides those
23 are the missing definitions, the sentences themselves should be read, because the phrase is
a homonym. It names at least three different things:

* `adoption` — an organization, sector or nation being ready to adopt AI;
* `training_data` — data prepared as INPUT to model training;
* `data_product_consumption` — a published data product's fitness to be discovered and
  correctly processed by an AI system at inference time. **This is the framework's sense**, and
  the only one that would extend the construct the KG is the validity layer for.

Counting documents that "mention the terms" therefore measures nothing on its own; the senses
have to be separated by reading. This script does the mechanical half — find and locate every
sentence — and `--judge` merges the human half back in, the same shape the CQ harness uses.

    /opt/anaconda3/bin/python3 scripts/harvest_ai_ready_contexts.py --harvest
    /opt/anaconda3/bin/python3 scripts/harvest_ai_ready_contexts.py --judge state/ai_ready_senses.json

Population: the rows of `state/extraction_gap_2026-09-04.json` — the gap set as it stood
BEFORE this task's extraction, which is the set ADDENDUM-02 names. Documents extracted since
are marked `extracted_since: true` rather than dropped, so the table can say which sentences
are already in the graph and which are still outside it.
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

TASK = "cc_tasks/2026-09-04_extract_g1eval_17_and_rerun_ADDENDUM-02.md"
GAP = REPO / "state" / "extraction_gap_2026-09-04.json"
OUT = REPO / "assessment" / "results" / "ai_ready_term_contexts_2026-09-04.jsonl"

#: ADDENDUM-02 §3a: CQ-02's own two terms plus `ai readiness`, which the addendum adds. The
#: pattern tolerates the hyphen, an ordinary space, or the line break a PDF extractor leaves
#: mid-phrase — "AI-\nready" is the same phrase and missing it would undercount silently.
TERM_RE = re.compile(r"\bai[\s\-‐-―]+read(?:y|iness)\b", re.IGNORECASE)

SENSES = ("adoption", "training_data", "data_product_consumption", "other")


def segments(row: dict) -> list:
    """[(locator, text)] for one document, preserving case — the sentence is quoted verbatim
    in the RESULT, so this cannot use the gap diagnostic's lowercasing reader.

    Locators are what each substrate can honestly give: a markdown line carries its nearest
    preceding heading, a PDF page carries its page number. No locator is invented.
    """
    sub = REPO / "state" / "substrate_md" / f"{row['doc_id']}.md"
    path = REPO / (row.get("path") or "")
    if sub.is_file():
        return _md_sections(sub.read_text(encoding="utf-8", errors="ignore"), "substrate_md")
    if not row.get("path") or not path.is_file():
        return []
    if path.suffix.lower() in (".md", ".html", ".htm", ".txt"):
        return _md_sections(path.read_text(encoding="utf-8", errors="ignore"), "file")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:                                   # pragma: no cover
            raise SystemExit(f"FATAL: pypdf is required to read {path}: {exc}") from exc
        try:
            return [(f"p.{i}", pg.extract_text() or "")
                    for i, pg in enumerate(PdfReader(str(path)).pages, 1)]
        except Exception as exc:
            print(f"  unreadable pdf {row['doc_id']}: {exc}", file=sys.stderr)
            return []
    return []


def _md_sections(text: str, kind: str) -> list:
    """Markdown/HTML split into (locator, block) where the locator names the nearest heading
    above the block and the line it starts on."""
    out, heading, buf, start = [], "", [], 1
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            if buf:
                out.append((f"{heading or kind}:L{start}", "\n".join(buf)))
            heading = line.strip("# ").strip()[:80]
            buf, start = [], lineno + 1
            continue
        if not buf:
            start = lineno
        buf.append(line)
    if buf:
        out.append((f"{heading or kind}:L{start}", "\n".join(buf)))
    return out


#: Sentence boundary: terminal punctuation followed by whitespace and a capital or a digit.
#: Deliberately crude and deliberately documented — an over-split sentence is still readable
#: evidence, and a sentence splitter is not what this task is measuring.
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])")


def sentences(block: str) -> list:
    flat = re.sub(r"[ \t]*\n[ \t]*", " ", block)
    flat = re.sub(r"\s{2,}", " ", flat)
    return [s.strip() for s in _SENT_RE.split(flat) if s.strip()]


def harvest() -> list:
    gap = json.loads(GAP.read_text(encoding="utf-8"))
    from kg import queue
    extracted = {d for d, r in queue.project().items()
                 if r["extraction_state"] == "extracted"}
    rows, unreadable = [], []
    for row in gap["rows"]:
        segs = segments(row)
        if not segs:
            unreadable.append(row["doc_id"])
            continue
        n = 0
        for locator, block in segs:
            for sent in sentences(block):
                if not TERM_RE.search(sent):
                    continue
                n += 1
                rows.append({
                    "sentence_id": f"{row['doc_id']}#{n:03d}",
                    "doc_id": row["doc_id"],
                    "gap_class": row["class"],
                    "extracted_since": row["doc_id"] in extracted,
                    "locator": locator,
                    "terms_matched": sorted({m.group(0).lower()
                                             for m in TERM_RE.finditer(sent)}),
                    # Trimmed, because a PDF page with no sentence punctuation can return the
                    # whole page as one "sentence"; the locator is how the reader gets the rest.
                    "sentence": sent[:1200],
                    "sense": None,
                    "sense_reason": None,
                })
    if unreadable:
        print(f"{len(unreadable)} document(s) yielded no text: {', '.join(unreadable[:6])}",
              file=sys.stderr)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", action="store_true")
    ap.add_argument("--judge", default=None,
                    help="JSON of {sentence_id: {sense, sense_reason}} merged into the JSONL")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    out = Path(a.out)

    if a.harvest:
        rows = harvest()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                       encoding="utf-8")
        docs = sorted({r["doc_id"] for r in rows})
        print(json.dumps({"sentences": len(rows), "documents": len(docs),
                          "documents_extracted_since": len(
                              {r["doc_id"] for r in rows if r["extracted_since"]})}, indent=1))
        print(f"-> {out.resolve().relative_to(REPO)}", file=sys.stderr)
        return 0

    if a.judge:
        verdicts = json.loads(Path(a.judge).read_text(encoding="utf-8"))
        rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
        for r in rows:
            v = verdicts.get(r["sentence_id"])
            if v:
                r["sense"], r["sense_reason"] = v.get("sense"), v.get("sense_reason")
        unjudged = [r["sentence_id"] for r in rows if r["sense"] not in SENSES]
        if unjudged:
            raise SystemExit(f"FATAL: {len(unjudged)} sentence(s) unjudged or carrying a sense "
                             f"outside {SENSES}: {', '.join(unjudged[:5])}")
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                       encoding="utf-8")
        counts = {s: sum(1 for r in rows if r["sense"] == s) for s in SENSES}
        print(json.dumps({"counts": counts, "documents_by_sense": {
            s: sorted({r["doc_id"] for r in rows if r["sense"] == s}) for s in SENSES}}, indent=1))
        return 0

    ap.error("one of --harvest / --judge is required")


if __name__ == "__main__":
    raise SystemExit(main())
