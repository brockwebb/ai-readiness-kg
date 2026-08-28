#!/usr/bin/env python3
"""Deterministic structure-aware chunker (task 2026-08-27_chunked_pilot §2).

The chunked arm of the unit-of-extraction pilot. One variable is under test — the unit the
model sees — so this module changes nothing else: the same source text the whole-document
arm was given (``run_bulk_extraction.doc_text``) is partitioned, never re-derived from the
PDF by a different reader.

Rules, in the priority order the task states them:

1. Section-bounded — a chunk never crosses a heading boundary at the level that produces
   sections (the shallowest level carrying >= ``min_headings_for_level`` headings).
2. Paragraph-integral — only whole paragraphs are packed; a paragraph is never split.
3. Cap <= ``max_tokens`` by the real tokenizer. An oversize single paragraph is its own
   chunk, flagged ``oversize`` (rule 2 wins over rule 3 — the task orders them).
4. Overlap — the previous chunk's last paragraph, bounded to ``overlap_max_tokens`` by
   dropping leading sentences.
5. Breadcrumb ``doc_title > H1 > H2 > ...`` prepended to the MODEL INPUT only, never to the
   stored chunk text (it is not document text and must never appear in a grounding span).
6. Stable ``<doc_id>#c<NNNN>`` ids and offsets into the source text that round-trip:
   ``source[chunk.start:chunk.end] == chunk.text``.

INPUT REALITY (recorded, not silently reconciled). §2 names ``corpus/bulk_md/<doc_id>.md``
as the input. None of the five pilot documents has a file there — all five are PDFs read
through pypdf, whose output has zero ATX headings and (for four of five) not one blank
line. So the markdown rules are implemented AND a plain-text family stands in for them:
headings are detected by the numbered / ALLCAPS-standalone patterns used by Wintermute's
``stage_book.py``, and paragraphs are reconstructed from hard-wrapped lines by the
short-line rule. Which family fired is recorded on the chunk set as ``structure_source``.

Stdlib + pyyaml, plus tiktoken for the token count (see ``count_tokens``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).with_name("chunker_config.yaml")

# --- heading patterns (plain-text family) ------------------------------------------------
# "2 RELATED WORK", "3.1 Data Quality", "4.2.1 Privacy" — level = number of dot components.
_NUMBERED = re.compile(r"^\s*(\d+(?:\.\d+){0,4})\.?\s+(\S.*)$")
# "ABSTRACT", "RELATED WORK", "1 INTRODUCTION" handled above; this is the unnumbered form.
_ALLCAPS = re.compile(r"^[A-Z][A-Z0-9 &,\-:/()'’.]*$")
_ATX = re.compile(r"^(#{1,6})\s+(\S.*)$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class ChunkerError(RuntimeError):
    """Raised when the chunker cannot honor its own contract — never a silent degrade."""


def load_config(path: Path | None = None) -> dict:
    cfg = yaml.safe_load((path or _CONFIG_PATH).read_text(encoding="utf-8"))
    missing = [k for k in ("max_tokens", "overlap_max_tokens", "min_headings_for_level",
                           "heading_max_chars", "max_heading_repeats", "short_line_ratio",
                           "width_percentile", "tokenizer") if k not in cfg]
    if missing:
        raise ChunkerError(f"{_CONFIG_PATH.name} is missing required keys: {missing}")
    return cfg


# --- tokenizer ---------------------------------------------------------------------------
_ENCODER = None


def _encoder(cfg: dict):
    """The real tokenizer named by config. ``model_stub`` exposes none (it reads usage off
    the `claude -p` envelope after the fact), so §2.3's stated fallback — tiktoken
    cl100k_base — is what runs, and every chunk set records it."""
    global _ENCODER
    if _ENCODER is None:
        name = cfg["tokenizer"]
        if not name.startswith("tiktoken:"):
            raise ChunkerError(f"unsupported tokenizer {name!r}")
        import tiktoken           # hard dependency: a token cap guessed from chars is not a cap
        _ENCODER = tiktoken.get_encoding(name.split(":", 1)[1])
    return _ENCODER


def count_tokens(text: str, cfg: dict | None = None) -> int:
    return len(_encoder(cfg or load_config()).encode(text, disallowed_special=()))


# --- structure detection ------------------------------------------------------------------
@dataclass(frozen=True)
class Heading:
    line: int
    level: int
    title: str


def detect_headings(lines: list[str], cfg: dict) -> tuple[list[Heading], str]:
    """Return (headings, structure_source). ``structure_source`` is ``markdown`` when ATX
    headings exist, else ``plain_text`` for the numbered/ALLCAPS family."""
    atx = [Heading(i, len(m.group(1)), m.group(2).strip())
           for i, line in enumerate(lines) if (m := _ATX.match(line))]
    if atx:
        return atx, "markdown"

    # Running page headers/footers repeat verbatim on every page and are not section
    # headings; detecting them as such shreds the document (see chunker_config.yaml).
    counts: dict[str, int] = {}
    for line in lines:
        s = line.strip()
        if s:
            counts[s] = counts.get(s, 0) + 1
    repeats = cfg["max_heading_repeats"]

    out: list[Heading] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) > cfg["heading_max_chars"] or counts[s] > repeats:
            continue
        if m := _NUMBERED.match(s):
            title = m.group(2).strip()
            # A numbered heading's text is a title, not a sentence: reject trailing prose.
            if title and not title.endswith((".", ",", ";")):
                out.append(Heading(i, m.group(1).count(".") + 1, s))
                continue
        if len(s) >= cfg["allcaps_min_chars"] and _ALLCAPS.match(s) and any(c.isalpha() for c in s):
            out.append(Heading(i, 1, s))
    return out, "plain_text"


def choose_level(headings: list[Heading], cfg: dict) -> int | None:
    """The shallowest level carrying at least ``min_headings_for_level`` headings — the task's
    stated heuristic. None when no level qualifies (the ``no_structure`` case)."""
    counts: dict[int, int] = {}
    for h in headings:
        counts[h.level] = counts.get(h.level, 0) + 1
    for level in sorted(counts):
        if counts[level] >= cfg["min_headings_for_level"]:
            return level
    return None


# --- paragraph reconstruction --------------------------------------------------------------
@dataclass(frozen=True)
class Block:
    start: int          # char offset into source
    end: int
    text: str
    heading: Heading | None = None


def _line_spans(source: str) -> list[tuple[int, int, str]]:
    """(start, end, text) per line, offsets into ``source``; ``end`` excludes the newline."""
    spans, pos = [], 0
    for line in source.split("\n"):
        spans.append((pos, pos + len(line), line))
        pos += len(line) + 1
    return spans


def _measure_width(lines: list[str], cfg: dict) -> int:
    """The document's full-measure line width: the ``width_percentile``-th percentile of
    non-blank line lengths. Hard-wrapped PDF text has a sharp mode here."""
    lens = sorted(len(l.rstrip()) for l in lines if l.strip())
    if not lens:
        return 0
    idx = min(len(lens) - 1, int(round((cfg["width_percentile"] / 100.0) * (len(lens) - 1))))
    return lens[idx]


def paragraphs(source: str, headings: list[Heading], cfg: dict) -> list[Block]:
    """Whole paragraphs (and heading lines, each its own block) with source offsets.

    Blank-line separated where the source has blank lines (markdown); otherwise a line whose
    length is below ``short_line_ratio`` x the measured full width closes the paragraph —
    the standard reflow rule for hard-wrapped text.
    """
    spans = _line_spans(source)
    lines = [t for _, _, t in spans]
    hd = {h.line: h for h in headings}
    threshold = _measure_width(lines, cfg) * cfg["short_line_ratio"]

    blocks: list[Block] = []
    cur: list[int] = []                       # line indices in the open paragraph

    def flush() -> None:
        if not cur:
            return
        start, end = spans[cur[0]][0], spans[cur[-1]][1]
        text = source[start:end]
        if text.strip():
            blocks.append(Block(start, end, text))
        cur.clear()

    for i, line in enumerate(lines):
        if i in hd:
            flush()
            start, end = spans[i][0], spans[i][1]
            blocks.append(Block(start, end, source[start:end], heading=hd[i]))
            continue
        if not line.strip():                  # blank line: paragraph boundary (markdown)
            flush()
            continue
        cur.append(i)
        if len(line.rstrip()) < threshold:    # short line closes a hard-wrapped paragraph
            flush()
    flush()
    return blocks


# --- overlap ---------------------------------------------------------------------------------
def tail_within(text: str, max_tokens: int, cfg: dict) -> str:
    """The tail of ``text`` within ``max_tokens``: whole sentences from the end, and if even
    the last sentence is too long, its final whole words. Always a verbatim substring, so an
    overlap-grounded span still locates in the document."""
    if count_tokens(text, cfg) <= max_tokens:
        return text
    parts = _SENTENCE_END.split(text.strip())
    out = ""
    for i in range(len(parts) - 1, -1, -1):
        cand = " ".join(parts[i:])
        if count_tokens(cand, cfg) > max_tokens:
            break
        out = cand
    if out:
        return out
    words = text.split()
    for i in range(len(words) - 1, -1, -1):
        cand = " ".join(words[i:])
        if count_tokens(cand, cfg) > max_tokens:
            return " ".join(words[i + 1:])
    return text


# --- chunks -------------------------------------------------------------------------------
@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    index: int
    start: int
    end: int
    text: str
    n_tokens: int
    heading_path: tuple[str, ...] = ()
    overlap_text: str = ""
    oversize: bool = False
    last_paragraph: str = ""      # this chunk's final whole paragraph — the next chunk's overlap

    def model_text(self, doc_title: str) -> str:
        """What the model is shown: breadcrumb, then overlap, then the chunk body. The
        breadcrumb is NOT document text and never enters a grounding span."""
        crumb = " > ".join((doc_title,) + self.heading_path)
        head = f"[section: {crumb}]\n\n" if crumb else ""
        prev = f"{self.overlap_text}\n\n" if self.overlap_text else ""
        return f"{head}{prev}{self.text}"

    def grounding_text(self) -> str:
        """The text a span from this chunk must match: overlap + body, both verbatim
        document substrings. The breadcrumb is excluded by construction."""
        return f"{self.overlap_text}\n\n{self.text}" if self.overlap_text else self.text


@dataclass
class ChunkSet:
    doc_id: str
    chunks: list[Chunk]
    structure_source: str
    heading_level: int | None
    no_structure: bool
    tokenizer: str
    config: dict = field(repr=False, default_factory=dict)

    def __iter__(self):
        return iter(self.chunks)

    def __len__(self) -> int:
        return len(self.chunks)

    def __getitem__(self, i):
        return self.chunks[i]


def chunk_document(doc_id: str, source: str, cfg: dict | None = None) -> ChunkSet:
    """Partition ``source`` into section-bounded, paragraph-integral chunks."""
    cfg = cfg or load_config()
    if not source.strip():
        raise ChunkerError(f"{doc_id}: empty source text")

    lines = source.split("\n")
    headings, structure_source = detect_headings(lines, cfg)
    level = choose_level(headings, cfg)
    no_structure = level is None
    boundary_lines = {h.line for h in headings if not no_structure and h.level <= level}

    blocks = paragraphs(source, headings, cfg)
    max_tokens = cfg["max_tokens"]

    chunks: list[Chunk] = []
    path: list[str] = []                       # running heading breadcrumb
    cur: list[Block] = []
    cur_path: tuple[str, ...] = ()

    def emit(force: bool = False) -> None:
        """Close the open chunk. A chunk holding only heading lines and no document body is
        NOT a unit of extraction -- there is nothing in it to extract from -- so its headings
        ride forward into the next chunk instead (measured: 23 of 151 chunks over the five
        pilot documents, 17 of them in mitre-ai-maturity-model). ``force`` closes it anyway
        at end of document, so no heading text is dropped."""
        nonlocal cur, cur_path
        if not cur:
            return
        if not force and all(b.heading is not None for b in cur):
            return
        start, end = cur[0].start, cur[-1].end
        text = source[start:end]
        n = count_tokens(text, cfg)
        idx = len(chunks) + 1
        overlap = ""
        if chunks and chunks[-1].last_paragraph:
            overlap = tail_within(chunks[-1].last_paragraph, cfg["overlap_max_tokens"], cfg)
        chunks.append(Chunk(chunk_id=f"{doc_id}#c{idx:04d}", doc_id=doc_id, index=idx,
                            start=start, end=end, text=text, n_tokens=n,
                            heading_path=cur_path, overlap_text=overlap,
                            oversize=len(cur) == 1 and n > max_tokens,
                            last_paragraph=cur[-1].text))
        cur, cur_path = [], ()

    for b in blocks:
        if b.heading is not None:
            if b.heading.line in boundary_lines:
                emit()                          # rule 1: never cross a section boundary
            path = path[:b.heading.level - 1] + [b.heading.title]
            if cur and all(x.heading is not None for x in cur):
                cur_path = tuple(path)          # breadcrumb follows the deepest heading held
        # Rule 3 is measured on the text the model will actually see — the source slice,
        # inter-block whitespace included. A sum of separately-encoded blocks undercounts it
        # (measured: a 1,550-token chunk passed a 1,500 block-sum check), and a cap that can
        # be exceeded is not a cap.
        if cur and count_tokens(source[cur[0].start:b.end], cfg) > max_tokens:
            emit()
        if not cur:
            cur_path = tuple(path)
        cur.append(b)
    emit(force=True)

    if not chunks:
        raise ChunkerError(f"{doc_id}: produced no chunks from {len(source)} chars")
    return ChunkSet(doc_id=doc_id, chunks=chunks, structure_source=structure_source,
                    heading_level=level, no_structure=no_structure,
                    tokenizer=cfg["tokenizer"], config=cfg)
