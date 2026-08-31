#!/usr/bin/env python3
"""Any-format -> markdown substrate conversion, with an adequacy gate.

Task `cc_tasks/2026-08-31_ingestion_conversion.md`; subsumes ResearchTask 6c39a235.
**Zero model calls.** Every tool here is deterministic local software.

Why this module exists in the shape it does
-------------------------------------------
The task was written from the burn's report that two documents were "HTML with no markdown
conversion". Measured against the store, that premise does not hold: T1's Docling pass had
already converted all five crosswalk HTML documents. What it produced for three of them was a
*faithful conversion of a navigation page* — the acquired bytes contain a table of contents,
not the specification. `slsa-specification-v1-0.html` is 16,566 bytes of markup carrying
2,016 characters of visible text, 30% of it anchor text; the specification itself lives on
eight sub-pages the acquired page links to.

So the failure mode this module has to catch is not "conversion failed". It is **conversion
succeeded and produced nothing worth extracting** — which no success/failure signal can see.
That is why `assess()` exists alongside `convert()`, and why the gate reports an extent
suspicion rather than a conversion error.

Prior art
---------
- **Boilerplate detection**: Kohlschütter, Fankhauser & Nejdl, *Boilerplate Detection using
  Shallow Text Features* (WSDM 2010) — establishes that **text density and link density**
  are sufficient shallow features to separate content from navigation, without parsing
  semantics. `assess()` uses exactly those two features and invents no third.
- **Readability** (Mozilla) applies link density at block level for removal; this module
  applies it at document level for an admission judgement, which is the same feature used
  for a different decision.
- **Converters**: Docling (IBM Research), Pandoc, trafilatura. Measured head-to-head on
  `w3c-prov-dm-data-model.html` before choosing — see `CONVERTER_CHOICE`.

The tiered-pipeline pattern (cheap converter first, escalate on structural failure) is
adopted from the 2026 production consensus named in the task's prior-art block. No converter
is written here.
"""
from __future__ import annotations

import datetime
import hashlib
import html as _html
import re
import shutil
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent

#: Read at call time so tests can repoint them (repo convention for module path globals).
_SUBSTRATE_DIR = _REPO / "state" / "substrate_md"
_DOCLING_DIR = _REPO / "state" / "docling_md"

#: Measured on `w3c-prov-dm-data-model.html` (271,572 bytes), 2026-08-31, recorded because
#: the task prescribed pandoc+trafilatura and the measurement contradicts it:
#:
#:   converter     chars     headings  table rows  code fences  raw-HTML leaks
#:   trafilatura   121,801          0          15            0               0
#:   pandoc        237,802         84          39          126             315
#:   docling       174,978         84         147          120               0
#:
#: trafilatura destroys the heading structure outright (0 of 84), which is disqualifying for a
#: specification whose sections are the citable unit and whose headings the chunker uses as
#: boundaries. pandoc keeps headings but leaks 315 raw HTML blocks into the markdown and
#: recovers a quarter of the table rows. Docling keeps every heading, the most table content,
#: and emits no raw HTML. It is also already installed and already the T1 path.
CONVERTER_CHOICE = "docling"

#: Shallow-feature thresholds for the extent gate (Kohlschütter et al., WSDM 2010).
#: These flag for review; they never silently drop or admit anything.
#:
#: `MIN_VISIBLE_CHARS` is NOT tuned to the five crosswalk documents. It is the corpus's own
#: existing floor: `dixie_evidence.yaml integrity.min_bytes.markdown` is 256 bytes, and the
#: smallest legitimate document in the corpus is a one-page statutory excerpt. 2,000 sits an
#: order of magnitude below the smallest real specification in the corpus (the shortest W3C
#: Recommendation held converts to ~175,000 chars) and an order of magnitude above the
#: garbage floor, so the band is wide, not fitted.
MIN_VISIBLE_CHARS = 2000
#: Readability removes a block above 0.5; a whole *document* that is a quarter anchor text is
#: already a navigation surface, so the document-level ceiling is stricter than the block one.
MAX_LINK_DENSITY = 0.25

#: Closed list. A gap event outside it is a bug, not a new category.
GAP_CLASSES = (
    "unknown_format",          # no converter is registered for this extension
    "tool_missing",            # a registered converter is not installed here
    "conversion_failed",       # the converter ran and raised or produced nothing
    "thin_extent_suspected",   # conversion SUCCEEDED and the output is a navigation surface
)


class ConversionGap(RuntimeError):
    """A document the substrate cannot supply. Carries the gap class and its evidence."""

    def __init__(self, doc_id: str, gap_class: str, detail: dict):
        if gap_class not in GAP_CLASSES:
            raise ValueError(f"unknown gap class {gap_class!r}; must be one of {GAP_CLASSES}")
        self.doc_id, self.gap_class, self.detail = doc_id, gap_class, detail
        super().__init__(f"{doc_id}: {gap_class} {detail}")


# ------------------------------------------------------------------ shallow text features
def visible_text(markup: str) -> str:
    """Text a reader would see: scripts, styles and tags removed, whitespace collapsed."""
    body = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", markup)
    return " ".join(_html.unescape(re.sub(r"(?s)<[^>]+>", " ", body)).split())


def link_density(markup: str) -> float:
    """Share of visible text that sits inside anchors — Kohlschütter's link density.

    A specification is prose with links in it; a hub page is links with prose between them.
    The number separates them without knowing anything about either document."""
    body = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", markup)
    text = visible_text(markup)
    if not text:
        return 1.0
    anchored = "".join(
        visible_text(m) + " " for m in re.findall(r"(?is)<a\b[^>]*>(.*?)</a>", body))
    return min(1.0, len(anchored.strip()) / len(text))


def assess(doc_id: str, markup: str, converted: str) -> dict:
    """Is this conversion worth extracting from? Returns the evidence either way.

    Deliberately assesses the SOURCE markup, not only the converted output: a converter that
    faithfully renders a table of contents produces clean markdown, and judging the output
    alone cannot tell that apart from a short document."""
    text = visible_text(markup)
    density = link_density(markup)
    thin = len(text) < MIN_VISIBLE_CHARS
    navlike = density > MAX_LINK_DENSITY
    return {
        "visible_chars": len(text), "link_density": round(density, 4),
        "converted_chars": len(converted),
        "min_visible_chars": MIN_VISIBLE_CHARS, "max_link_density": MAX_LINK_DENSITY,
        "thin_text": thin, "nav_like": navlike,
        "adequate": not (thin or navlike),
        "why": ("ok" if not (thin or navlike) else
                ", ".join(filter(None, [
                    f"visible text {len(text):,} < {MIN_VISIBLE_CHARS:,}" if thin else "",
                    f"link density {density:.0%} > {MAX_LINK_DENSITY:.0%}" if navlike else ""]))),
    }


# ------------------------------------------------------------------ converters
def _docling_html(path: Path) -> str:
    from docling.document_converter import DocumentConverter
    return DocumentConverter().convert(str(path)).document.export_to_markdown()


def _pandoc_html(path: Path) -> str:
    if not shutil.which("pandoc"):
        raise FileNotFoundError("pandoc is not installed")
    r = subprocess.run(["pandoc", "-f", "html", "-t", "gfm", "--wrap=none", str(path)],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc exited {r.returncode}: {r.stderr[:300]}")
    return r.stdout


def _passthrough(path: Path) -> str:
    return path.read_text("utf-8", "ignore")


#: extension -> ordered tool chain. First tool that yields non-empty output wins; the tier
#: below it is the escalation path, per the adopted tiered-pipeline pattern.
REGISTRY: dict[str, tuple[str, ...]] = {
    ".md": ("passthrough",), ".txt": ("passthrough",),
    ".html": ("docling", "pandoc"), ".htm": ("docling", "pandoc"),
}
TOOLS = {"passthrough": _passthrough, "docling": _docling_html, "pandoc": _pandoc_html}

#: `.pdf` is deliberately absent: the existing T1 path owns PDFs and the task puts
#: re-conversion of the working PDF corpus out of scope. Routing PDFs here would re-convert
#: 170-odd documents to no benefit.
DELEGATED = {".pdf"}


def tool_versions() -> dict[str, str]:
    out = {}
    try:
        import docling
        out["docling"] = getattr(docling, "__version__", "unknown")
    except Exception:
        out["docling"] = "not installed"
    if shutil.which("pandoc"):
        r = subprocess.run(["pandoc", "--version"], capture_output=True, text=True)
        out["pandoc"] = r.stdout.splitlines()[0].split()[-1] if r.stdout else "unknown"
    else:
        out["pandoc"] = "not installed"
    return out


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def frontmatter(doc_id: str, src: Path, converter: str, meta: dict) -> str:
    """YAML frontmatter. Citability must survive conversion, so the source URL, the source
    sha256 and the converter identity all ride on the substrate file itself — a reader who
    has only this file can still say what it derives from and check it."""
    def esc(v):
        return "null" if v is None else '"' + str(v).replace('"', '\\"') + '"'
    lines = ["---", f"doc_id: {esc(doc_id)}",
             f"source_path: {esc(_rel(src))}",
             f"source_sha256: {esc(meta.get('source_sha256'))}",
             f"source_url: {esc(meta.get('source_url'))}",
             f"source_format: {esc(src.suffix.lower().lstrip('.'))}",
             f"version: {esc(meta.get('version'))}",
             f"acquired_at: {esc(meta.get('acquired_at'))}",
             f"converter: {esc(converter)}",
             f"converter_version: {esc(meta.get('converter_version'))}",
             f"converted_at: {esc(_now())}",
             f"evidence_class: \"structural\"",
             "---", ""]
    return "\n".join(lines)


def _rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(_REPO))
    except ValueError:
        return str(p)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_frontmatter(path: Path) -> dict:
    """Parse the YAML frontmatter block off a substrate file. Deliberately a small parser and
    not a YAML load: the block is written by `frontmatter()` in one shape, and a full loader
    would accept shapes this contract does not define."""
    text = path.read_text("utf-8", "ignore")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith('"') and v.endswith('"') and len(v) >= 2:
            v = v[1:-1].replace('\\"', '"')
        out[k.strip()] = None if v == "null" else v
    return out


def verify_substrate(doc_id: str, substrate: Path | None = None) -> dict:
    """Re-hash the source named in the frontmatter and compare.

    A substrate file whose recorded `source_sha256` no longer matches the bytes on disk is
    derived from a document that has since changed, and every grounding span located in it is
    a claim about text that is no longer the admitted text. Detecting that is the whole reason
    the hash is on the file rather than only in an event."""
    path = substrate or (_SUBSTRATE_DIR / f"{doc_id}.md")
    if not path.is_file():
        return {"doc_id": doc_id, "ok": False, "issue": "substrate_missing",
                "path": _rel(path)}
    fm = read_frontmatter(path)
    if not fm.get("source_sha256") or not fm.get("source_path"):
        return {"doc_id": doc_id, "ok": False, "issue": "frontmatter_incomplete",
                "path": _rel(path), "frontmatter": fm}
    src = _REPO / fm["source_path"]
    if not src.is_file():
        return {"doc_id": doc_id, "ok": False, "issue": "source_missing",
                "source_path": fm["source_path"]}
    actual = sha256_file(src)
    if actual != fm["source_sha256"]:
        return {"doc_id": doc_id, "ok": False, "issue": "source_sha_mismatch",
                "source_path": fm["source_path"],
                "recorded": fm["source_sha256"], "actual": actual}
    return {"doc_id": doc_id, "ok": True, "source_path": fm["source_path"],
            "source_sha256": actual, "converter": fm.get("converter")}


def convert(doc_id: str, src: Path, meta: dict | None = None,
            write: bool = True) -> tuple[Path | None, dict]:
    """Convert one source to markdown substrate.

    Returns (substrate_path or None, report). Raises `ConversionGap` for every case the
    substrate cannot supply — including the case where conversion works and the result is a
    navigation page, because an undetected thin extent is what put a table of contents into
    an extraction queue in the first place.
    """
    meta = dict(meta or {})
    ext = src.suffix.lower()
    if ext in DELEGATED:
        raise ConversionGap(doc_id, "unknown_format",
                            {"format": ext, "note": "PDFs are owned by the existing T1 path; "
                                                    "this module does not re-convert them"})
    chain = REGISTRY.get(ext)
    if not chain:
        raise ConversionGap(doc_id, "unknown_format",
                            {"format": ext or "(none)", "path": _rel(src),
                             "registry": sorted(REGISTRY)})
    if not src.is_file():
        raise ConversionGap(doc_id, "conversion_failed",
                            {"format": ext, "error": f"source not found: {_rel(src)}"})

    raw = src.read_text("utf-8", "ignore")
    meta.setdefault("source_sha256", sha256_file(src))
    attempts, out, used = [], "", None
    for tool in chain:
        try:
            text = TOOLS[tool](src)
        except FileNotFoundError as exc:
            attempts.append({"tool": tool, "outcome": "tool_missing", "error": str(exc)[:200]})
            continue
        except Exception as exc:
            attempts.append({"tool": tool, "outcome": "error",
                             "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
            continue
        attempts.append({"tool": tool, "outcome": "ok", "chars": len(text or "")})
        if (text or "").strip():
            out, used = text, tool
            break
    if used is None:
        cls = ("tool_missing" if attempts and
               all(a["outcome"] == "tool_missing" for a in attempts) else "conversion_failed")
        raise ConversionGap(doc_id, cls, {"format": ext, "attempts": attempts})

    report = assess(doc_id, raw if ext in (".html", ".htm") else out, out)
    report.update({"converter": used, "attempts": attempts, "source_sha256": meta["source_sha256"]})
    if not report["adequate"]:
        raise ConversionGap(doc_id, "thin_extent_suspected",
                            {"format": ext, "converter": used, "source_url": meta.get("source_url"),
                             **{k: report[k] for k in
                                ("visible_chars", "link_density", "converted_chars",
                                 "min_visible_chars", "max_link_density", "why")}})

    meta.setdefault("converter_version", tool_versions().get(used))
    body = frontmatter(doc_id, src, used, meta) + out
    dest = _SUBSTRATE_DIR / f"{doc_id}.md"
    if write:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
    report["substrate_path"] = _rel(dest)
    report["substrate_chars"] = len(body)
    return (dest if write else None), report
