"""The ai-readiness graph's text reader (squiddy SQ-019; DN-049 R-208 and its Amendment). Zero calls.

Every span an ai-readiness-kg extraction carries is an offset into the text `scripts/run_bulk_extraction.py` `doc_text`
returns for its document: the DD-030 substrate body (`state/substrate_md/<doc_id>.md`) when there is one, else the
canonical file read as text, or through pypdf for a PDF. The kit's own reader (pypdfium2) would give a different text for
the same PDF and fail every span for a reason that is the reader, not the item. So this graph declares this reader
(`engine.extract.text_reader`), and the ingest span gate and the adopter both read through it.

`doc_text` is CALLED, never copied, and in ai-readiness-kg's own interpreter (`domain.airkg.python`, with its pypdf),
in a subprocess, because the kit's environment holds neither dixie nor pypdf and a different pypdf would be a different
text. One page: the text is a single string and its offsets are the extraction's.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

#: Run inside ai-readiness-kg's interpreter: argv is (repo, path, doc_id); prints {"text": ...}.
_CALL = ("import json, sys; sys.path.insert(0, sys.argv[1]); "
         "from scripts.run_bulk_extraction import doc_text; "
         "from pathlib import Path; "
         "print(json.dumps({'text': doc_text(Path(sys.argv[2]), sys.argv[3])}))")
_CACHE: dict[tuple, str] = {}


def airkg(graph) -> dict:
    cfg = (graph.domain.get("airkg") or {})
    missing = [k for k in ("repo", "python") if not cfg.get(k)]
    if missing:
        raise SystemExit(f"FATAL: domain.airkg lacks {missing}; the text reader calls ai-readiness-kg's doc_text in "
                         f"ai-readiness-kg's own interpreter")
    return cfg


def text(graph, path: Path, doc_id: str) -> str:
    """`doc_text(path, doc_id)`, once per (path, its mtime and size, doc_id) in this process."""
    path = Path(path)
    st = path.stat()
    key = (str(path), st.st_mtime_ns, st.st_size, doc_id)
    if key not in _CACHE:
        cfg = airkg(graph)
        r = subprocess.run([cfg["python"], "-c", _CALL, cfg["repo"], str(path), doc_id],
                           capture_output=True, text=True, cwd=cfg["repo"])
        if r.returncode != 0:
            raise SystemExit(f"FATAL: ai-readiness-kg's doc_text failed for {doc_id} ({path}): "
                             f"{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'rc=' + str(r.returncode)}")
        _CACHE[key] = json.loads(r.stdout.strip().splitlines()[-1])["text"]
    return _CACHE[key]


def pages(graph, path: Path, doc_id: str) -> list[str]:
    """The kit's text-reader contract (`squiddy.extract_daemon.document_pages`)."""
    return [text(graph, path, doc_id)]


#: Run inside ai-readiness-kg's interpreter: argv is (repo, path, doc_id); prints {chunk_id: [start, end, overlap
#: start or null]} for the document's chunks as ai-readiness-kg's chunker cuts them now.
_WINDOWS = ("import json, sys; sys.path.insert(0, sys.argv[1]); "
            "from scripts.run_bulk_extraction import doc_text; "
            "from kg.extraction.chunker import chunk_document; "
            "from pathlib import Path; "
            "t = doc_text(Path(sys.argv[2]), sys.argv[3]); out = {}\n"
            "for c in chunk_document(sys.argv[3], t):\n"
            "    o = t.rfind(c.overlap_text, 0, c.start) if c.overlap_text else -1\n"
            "    out[c.chunk_id] = [c.start, c.end, o if o != -1 and o + len(c.overlap_text) <= c.start else None]\n"
            "print(json.dumps(out))")
_WINDOW_CACHE: dict[tuple, dict] = {}


def windows(graph, path: Path, doc_id: str) -> dict:
    """Per chunk id, `[start, end, overlap start]`: where in the document the text a chunk's items were grounded in
    begins. ai-readiness-kg's chunker shows the model the previous chunk's last paragraph as OVERLAP before the body,
    and its grounding contract accepts a span anywhere in overlap plus body (`kg/extraction/chunker.py`,
    `Chunk.grounding_text`), so an item of a chunk may sit just before the chunk's recorded `chunk_start`. The chunker
    is CALLED, not copied; the adopter uses a chunk's overlap start only when the chunk as cut now has the start and end
    the event recorded (the chunker config is pinned by sha256 in the run profile)."""
    path = Path(path)
    st = path.stat()
    key = (str(path), st.st_mtime_ns, st.st_size, doc_id)
    if key not in _WINDOW_CACHE:
        cfg = airkg(graph)
        r = subprocess.run([cfg["python"], "-c", _WINDOWS, cfg["repo"], str(path), doc_id],
                           capture_output=True, text=True, cwd=cfg["repo"])
        if r.returncode != 0:
            raise SystemExit(f"FATAL: ai-readiness-kg's chunker failed for {doc_id} ({path}): "
                             f"{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'rc=' + str(r.returncode)}")
        _WINDOW_CACHE[key] = json.loads(r.stdout.strip().splitlines()[-1])
    return _WINDOW_CACHE[key]
