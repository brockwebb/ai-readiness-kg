#!/usr/bin/env python3
"""Build the USAFacts note: USAFACTS_NOTE.md and USAFACTS_NOTE.pdf. **Zero spend, no network.**

`cc_tasks/2026-10-14_usafacts_note.md` (DN-014 ADDENDUM 01 §5). Reads the authored source
(`reports/summary/usafacts_note_source.yaml`) and writes, into `reports/summary/`:

* `USAFACTS_NOTE.md`: the two-or-three paragraph narrative and a Sources section.
* `USAFACTS_NOTE.pdf`: rendered from the Markdown by THIS script (pandoc and typst, the concise
  report's and DCAT brief's call, via `dcat_brief_build`), so the PDF cannot drift from its
  Markdown (`~/GitHub/CLAUDE.md`: a report ships a PDF built by the same script as its Markdown).
* `usafacts_note_build_report.json`: the Markdown and PDF sha256s and the page count.

Two gates run before a byte is written, and any finding refuses the build:

* the text check (`scripts/summary_text_check.py` + `scripts/dcat_faq_lint.py`): the four things
  DN-014 cuts (process words, indicator codes, AI outside a published title, dashes), the tier
  letters and rule codes (ADDENDUM 01 §3), plus repository paths, file names and the operator's
  banned words. The same check the executive summary runs, on this note.
* the unsupported-sentence check: every reader-facing FACT sentence carries a `locator`, and
  every ref in it resolves against the evidence named in the source file (the framework record,
  the corpus manifest, the published grid, or a repository file). A sentence marked
  `kind: context` states nothing checkable and carries no locator. The derivation block's
  locators are resolved too. A sentence that is a fact without a resolving locator is the defect
  this check exists to catch.

    /opt/anaconda3/bin/python3 scripts/usafacts_note_build.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _p in ("", "scripts", "assessment"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import yaml  # noqa: E402

import dcat_brief_build as BB  # noqa: E402
import dcat_faq_build as FB  # noqa: E402
import dcat_faq_lint as LINT  # noqa: E402
import summary_build as SB  # noqa: E402
import summary_text_check as TC  # noqa: E402

GENERATOR = "scripts/usafacts_note_build.py"
TASK = "cc_tasks/2026-10-14_usafacts_note.md"
OUT = REPO / "reports" / "summary"
SOURCE = OUT / "usafacts_note_source.yaml"


# ----------------------------------------------------------------------------- locator resolver

class Evidence:
    """The evidence the unsupported-sentence check reads: the framework record, the corpus
    manifest and the published grid. A locator ref resolves against exactly one of them, or
    against a repository file; an unresolved ref is a finding."""

    def __init__(self, src: dict):
        self.record = json.loads((REPO / src["inputs"]["framework_record"]).read_text(encoding="utf-8"))
        self.manifest = json.loads((REPO / src["inputs"]["manifest"]).read_text(encoding="utf-8"))
        self.grid = json.loads((REPO / src["inputs"]["grid"]).read_text(encoding="utf-8"))
        self.nodes = {n["id"]: n for n in self.record["nodes"]}
        self.docs = set((self.manifest.get("entries") or {}).keys())
        self.legs = {c["leg"] for c in self.grid.get("columns", [])}
        self.crit_codes = {n["properties"].get("code") for n in self.record["nodes"]
                           if "AssessmentCriterion" in n["labels"]}

    def resolve(self, ref: str) -> str | None:
        """Return None if the ref resolves, else a one-line reason it does not."""
        if ref.startswith("record:"):
            body = ref[len("record:"):]
            node_id, _, prop = body.partition("#")
            n = self.nodes.get(node_id)
            if n is None:
                return f"no record node {node_id!r}"
            if prop:
                val = n["properties"].get(prop, "\x00")
                if val == "\x00" or val is None:
                    return f"record node {node_id!r} has no property {prop!r}"
            return None
        if ref.startswith("doc:"):
            did = ref[len("doc:"):]
            return None if did in self.docs else f"no corpus document {did!r}"
        if ref == "grid:presence_gate":
            pg = self.grid.get("presence_gate") or {}
            bad = (pg.get("missing_plain_name") or []) + (pg.get("missing_fix_line") or [])
            return None if not bad else f"grid presence gate not clean: {bad}"
        if ref == "grid:columns":
            return None if self.legs else "grid has no public-tier columns"
        if ref == "grid:maps_to_criteria":
            stray = [c["leg"] for c in self.grid.get("columns", [])
                     if (c["leg"][:1] not in self.crit_codes)]
            return None if not stray else f"grid columns with no criterion: {stray}"
        if ref.startswith("grid:"):
            leg = ref[len("grid:"):]
            return None if leg in self.legs else f"no public-tier column {leg!r}"
        if ref.startswith("file:"):
            spec = ref[len("file:"):]
            path, _, line = spec.partition("#L")
            p = REPO / path
            if not p.is_file():
                return f"no file {path!r}"
            if line:
                n = len(p.read_text(encoding="utf-8").splitlines())
                if n < int(line):
                    return f"file {path!r} has {n} lines, needs line {line}"
            return None
        return f"unknown locator scheme in {ref!r}"


# ----------------------------------------------------------------- the unsupported-sentence check

def iter_fact_sentences(src: dict):
    """(where, text, locator) for every reader-facing FACT sentence, in order."""
    for pi, para in enumerate(src["paragraphs"], 1):
        for si, s in enumerate(para, 1):
            kind = s.get("kind", "fact")
            if kind == "context":
                continue
            yield (f"paragraph {pi} sentence {si}", nws(s["text"]), s.get("locator") or [])


def iter_derivation_locators(obj, path="derivation"):
    """Every `locator`/`source_locator` list anywhere under the derivation block, with its path."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("locator", "source_locator") and isinstance(v, list):
                yield (path + "." + k, v)
            else:
                yield from iter_derivation_locators(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_derivation_locators(v, f"{path}[{i}]")


def nws(s: str) -> str:
    return " ".join(str(s).split())


def unsupported_findings(src: dict, ev: Evidence) -> list[dict]:
    out = []
    for where, text, locator in iter_fact_sentences(src):
        if not locator:
            out.append({"where": where, "reason": "fact sentence carries no locator", "text": text[:80]})
            continue
        for ref in locator:
            why = ev.resolve(ref)
            if why:
                out.append({"where": where, "ref": ref, "reason": why, "text": text[:80]})
    for where, locator in iter_derivation_locators(src.get("derivation", {})):
        for ref in locator:
            why = ev.resolve(ref)
            if why:
                out.append({"where": where, "ref": ref, "reason": why})
    return out


# ------------------------------------------------------------------------------------ markdown

def note_markdown(src: dict, manifest: dict) -> str:
    lines = [f"# {src['title']}", "", f"Prepared {src['prepared']}.", ""]
    for para in src["paragraphs"]:
        lines.append(" ".join(nws(s["text"]) for s in para))
        lines.append("")
    srcs = src["sources"]
    lines += [f"## {srcs['heading']}", ""]
    for n, e in enumerate(srcs["entries"], 1):
        lines.append(f"{n}. {SB.source_line(e, manifest)}")
    lines.append("")
    if srcs.get("provenance"):
        lines += [nws(srcs["provenance"]), ""]
    return "\n".join(lines).rstrip() + "\n"


def text_findings(md: str) -> list:
    return [{**f, "src": "text_check"} for f in TC.check(md)] + \
           [{**f, "src": "lint"} for f in LINT.lint(md)]


# ------------------------------------------------------------------------------------- outputs

def render(md_path: Path, pdf_path: Path, md: str, out_dir: Path) -> dict:
    build_dir = out_dir / "build"
    build_dir.mkdir(exist_ok=True)
    scratch = build_dir / md_path.name
    try:
        scratch.write_text(FB.strip_title(md), encoding="utf-8")
        BB.render_pdf(scratch, pdf_path, BB.h1(md))
    finally:
        scratch.unlink(missing_ok=True)
        if build_dir.is_dir() and not any(build_dir.iterdir()):
            build_dir.rmdir()
    return {"md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
            "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            "pages": BB.pdf_pages(pdf_path)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=None, help="test seam (default: reports/summary)")
    ap.add_argument("--source", default=None, help="test seam (default: the note source yaml)")
    ap.add_argument("--no-pdf", action="store_true", help="test seam: skip the pandoc render")
    a = ap.parse_args(argv)
    out = Path(a.out_dir) if a.out_dir else OUT
    src = yaml.safe_load((Path(a.source) if a.source else SOURCE).read_text(encoding="utf-8"))
    manifest = json.loads((REPO / src["inputs"]["manifest"]).read_text(encoding="utf-8"))

    md = note_markdown(src, manifest)

    # Gate 1: the unsupported-sentence check, with the source file as its evidence.
    ev = Evidence(src)
    uns = unsupported_findings(src, ev)
    # Gate 2: the text check (the four DN-014 cuts) and the lint (paths, file names, banned words).
    tf = text_findings(md)

    if uns or tf:
        for f in uns:
            print(f"UNSUPPORTED {f['where']}: {f.get('ref','(no locator)')} -> {f['reason']}")
        for f in tf:
            print(f"TEXT page:{f['line']} [{f['src']}:{f['rule']}] {f['match']!r} in {f.get('context','')!r}")
        raise SystemExit(f"FATAL: the note fails its gates "
                         f"({len(uns)} unsupported, {len(tf)} text); nothing is written")

    md_path = out / "USAFACTS_NOTE.md"
    md_path.write_text(md, encoding="utf-8")
    report = {"generated_by": GENERATOR, "task": TASK,
              "text_check": "0 findings", "unsupported_check": "0 findings",
              "fact_sentences": sum(1 for _ in iter_fact_sentences(src))}
    if not a.no_pdf:
        info = render(md_path, out / "USAFACTS_NOTE.pdf", md, out)
        report["render"] = {"markdown": "USAFACTS_NOTE.md", "pdf": "USAFACTS_NOTE.pdf", **info}
    (out / "usafacts_note_build_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
