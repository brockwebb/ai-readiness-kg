#!/usr/bin/env python3
"""Build the concise report from the checked run. **Zero spend, no network.**

`cc_tasks/2026-10-07_concise_report_prose.md` decision 7. Reads `reports/concise/run/
pipeline.json` (written by `scripts/concise_report_run.py`) and writes, into `reports/concise/`:

* `REPORT.md`: the title, the six sections as the check left them, claim markers stripped,
  and two parts built by code, not by a model: the sources the kept sentences rest on (from the
  prior-art claims they cite, titles read from the corpus ledger and the bibliography) and a
  note on how the report was written and checked, with its counts read from the run.
* `REPORT.pdf`: rendered from REPORT.md by this script (pandoc and typst, the DCAT brief's call),
  so the PDF cannot drift from its Markdown; `build_report.json` records both sha256s and the
  page count.
* `claims_trace.json`: every sentence of every round, with its claim markers, the checker's
  label and ids, the digit check and whether it was kept.
* `prose_gate.json`: the gate per section, every round, and the repetition warnings.
* `fresh_reader.json`: both reader rounds verbatim, with their grades.

Then runs `scripts/dcat_faq_lint.py` on REPORT.md (no task codes, repository paths, pipeline
words, em dashes, or a word on the operator's banned list) and refuses the build on a finding.

    /opt/anaconda3/bin/python3 scripts/concise_report_build.py
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

import concise_report_gate as G  # noqa: E402

TASK = "cc_tasks/2026-10-07_concise_report_prose.md"
GENERATOR = "scripts/concise_report_build.py"
OUT = REPO / "reports" / "concise"
MANIFEST = REPO / "corpus" / "manifest.json"
BIBS = (REPO / "docs" / "evidence" / "sources.bib", REPO / "docs" / "evidence" / "method_sources.bib")


# ------------------------------------------------------------------------------ sources

def bib_entries() -> dict:
    out = {}
    for p in BIBS:
        if not p.is_file():
            continue
        for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", p.read_text(encoding="utf-8"), re.S):
            fields = {k.lower(): re.sub(r"[{}]", "", v).strip()
                      for k, v in re.findall(r"(\w+)\s*=\s*\{(.*?)\},?\s*$", m.group(2), re.M)}
            out[m.group(1).strip()] = fields
    return out


def plain_title(t: str) -> str:
    """Typesetting only, never wording: an em dash inside a source's own title becomes a colon
    (the operator's rule bars the character from his output, and the lint enforces it), and a
    parenthetical holding a path or a host ("(docs/checks.md)") is dropped, because the URL the
    line ends with already gives it and the lint reads a path as repository vocabulary."""
    t = re.sub(r"\s*\u2014\s*", ": ", t)
    t = re.sub(r"\s*\([^()\s]*/[^()\s]*\)", "", t)
    return " ".join(t.split())


def fmt_source(title: str, who: str | None, year: str | None, url: str | None) -> str:
    head = plain_title(title).rstrip(".")
    by = ", ".join(x for x in (who, year) if x).rstrip(".")
    return f"{head}." + (f" {by}." if by else "") + (f" <{url}>" if url else "")


def source_line(e: dict, manifest: dict, bib: dict) -> tuple | None:
    """(key, "Title. Authors, year. URL") for one evidence entry of a prior-art claim."""
    if e.get("kind") == "document":
        ent = (manifest.get("entries") or {}).get(e["id"])
        if not ent:
            return None
        idn = ent["identity"]
        who = ", ".join(a for a in (idn.get("authors_or_org") or []) if a)
        year = str(idn.get("pub_year") or "")[:4]
        return e["id"], fmt_source(idn.get("title") or e["id"], who, year, idn.get("source_url"))
    if e.get("kind") == "citation":
        b = bib.get(e["id"], {})
        title, who = e.get("title") or b.get("title"), e.get("author") or b.get("author")
        if not title:
            return None
        if who and " and " in who:
            who = who.split(" and ")[0].split(",")[0] + " and others"
        year, url = e.get("year") or b.get("year"), e.get("url") or b.get("url")
        return e["id"], fmt_source(title, who, year, url)
    return None


def sources(ids: list, claims: dict) -> list:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
    bib = bib_entries()
    seen, out = set(), []
    for i in ids:
        c = claims.get(i)
        if not c or c["status"] != "prior_art":
            continue
        for e in c.get("evidence") or []:
            s = source_line(e, manifest, bib)
            # A design note of this project is not a source a reader can fetch; the claim that
            # cites one states the project's own position, which the report says in words.
            if s and s[0] not in seen and not s[0].startswith("airkg"):
                seen.add(s[0])
                out.append(s[1])
    return out


# ------------------------------------------------------------------------------ markdown

def cited_ids(sections: dict) -> list:
    out = []
    for sid in sorted(sections, key=int):
        for p in sections[sid]:
            for s in p:
                out += G.marker_ids(s)
    return list(dict.fromkeys(out))


def report_markdown(cfg: dict, sections: dict, claims: dict, note: str | None = None) -> str:
    """The reader-facing report: markers stripped, sources and the note built by code."""
    lines = [f"# {cfg['title']}", "", f"Prepared {cfg['prepared']}.", ""]
    for s in cfg["sections"]:
        lines += [f"## {s['title']}", ""]
        for p in sections.get(s["id"], sections.get(str(s["id"]), [])):
            lines += [" ".join(G.strip_markers(x) for x in p), ""]
    src = sources(cited_ids({str(k): v for k, v in sections.items()}), claims)
    if src:
        lines += ["## Sources", ""] + [f"{n}. {s}" for n, s in enumerate(src, 1)] + [""]
    if note:
        lines += ["## How this report was written", "", note, ""]
    return "\n".join(lines)


def written_note(pipe: dict) -> str:
    """Counts read from the run, so the note cannot disagree with the trace."""
    rows = [r for sec in pipe["final"]["rows"].values() for r in sec["rows"]]
    all_rows = [r for k in ("round1", "round2", "round3") if k in pipe
                for sec in pipe[k]["check"].values() for r in sec["rows"]]
    cut = sum(1 for r in all_rows if not r["kept"])
    ctl = pipe["control"]["rows"]
    if not pipe["control"]["passed"]:
        raise SystemExit("FATAL: the control did not pass; no report is built on its checks")
    kept = sum(1 for r in rows if r["kept"])
    return (f"A language model wrote each section from a fixed set of claims, each of which cites its "
            f"evidence. A second model, of a different family, then read every sentence against those "
            f"claims alone; a sentence it did not find supported was cut, never reworded, and code cut any "
            f"sentence holding a number that was not in a claim it cites. Across the drafts, {cut} "
            f"sentences were cut this way, and the report keeps {kept}. Before the check was trusted, one "
            f"false sentence was planted in each of the {len(ctl)} sections, and the checker caught "
            f"{sum(1 for c in ctl if c['caught'])} of {len(ctl)}.")


# ------------------------------------------------------------------------------ outputs

def render(md_path: Path, pdf_path: Path, md: str) -> dict:
    import dcat_brief_build as BB
    import dcat_faq_build as FB
    build_dir = md_path.parent / "build"
    build_dir.mkdir(exist_ok=True)
    scratch = build_dir / md_path.name
    try:
        scratch.write_text(FB.strip_title(md), encoding="utf-8")
        BB.render_pdf(scratch, pdf_path, BB.h1(md))
    finally:
        scratch.unlink(missing_ok=True)
        build_dir.rmdir()
    return {"markdown": md_path.name, "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
            "pdf": pdf_path.name, "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            "pages": BB.pdf_pages(pdf_path)}


def trace(pipe: dict) -> dict:
    out = {"generated_by": GENERATOR, "task": TASK, "labels": ["supported", "unsupported", "no_factual_content"],
           "rounds": {}}
    for k in ("round1", "round2", "round3"):
        if k in pipe:
            out["rounds"][k] = {sid: v for sid, v in pipe[k]["check"].items()}
    out["final"] = pipe["final"]["rows"]
    return out


def gate_out(pipe: dict) -> dict:
    out = {"generated_by": GENERATOR, "task": TASK, "rounds": {}}
    for k in ("round1", "round2", "round3"):
        if k in pipe:
            out["rounds"][k] = pipe[k]["gate"]
    out["final"] = pipe["final"]["gate"]
    out["sent_back"] = pipe["round2"]["sent_back"]
    return out


def main(argv=None) -> int:
    import concise_report_run as R
    import dcat_faq_lint
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=None, help="test seam (default: reports/concise)")
    ap.add_argument("--no-pdf", action="store_true", help="test seam: skip the pandoc render")
    a = ap.parse_args(argv)
    out = Path(a.out_dir) if a.out_dir else OUT
    pipe = json.loads((out / "run" / R.PIPELINE).read_text(encoding="utf-8"))
    if pipe.get("stopped") or "final" not in pipe:
        raise SystemExit(f"FATAL: the run did not finish ({pipe.get('stopped')}); nothing is built")
    cfg = R.load_config()
    claims = R.load_claims(cfg)
    md = report_markdown(cfg, pipe["final"]["sections"], claims, written_note(pipe))
    findings = dcat_faq_lint.lint(md) + [{"rule": d["rule"], "line": 0, "match": "dash"} for d in G.dash_findings(md)]
    if findings:
        for f in findings:
            print(f"REPORT.md:{f['line']} [{f['rule']}] {f['match']!r}")
        raise SystemExit(f"FATAL: REPORT.md fails the lint ({len(findings)} finding(s)); nothing is written")
    md_path = out / "REPORT.md"
    md_path.write_text(md, encoding="utf-8")
    report = {"generated_by": GENERATOR, "task": TASK, "lint": "0 findings"}
    if not a.no_pdf:
        report["render"] = render(md_path, out / "REPORT.pdf", md)
    (out / "claims_trace.json").write_text(json.dumps(trace(pipe), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "prose_gate.json").write_text(json.dumps(gate_out(pipe), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "fresh_reader.json").write_text(json.dumps({"generated_by": GENERATOR, "task": TASK,
                                                       "questions": cfg["fresh_reader"]["questions"],
                                                       "grading": cfg["fresh_reader"]["grade"],
                                                       "rounds": pipe["reader"]}, indent=1, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    (out / "build_report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
