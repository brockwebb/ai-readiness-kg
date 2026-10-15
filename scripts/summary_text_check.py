#!/usr/bin/env python3
"""The executive summary's text check. **Zero spend, no network.**

`cc_tasks/2026-10-12_executive_summary_from_brief_v2.md` gate, from a word list committed with
the summary (`reports/summary/text_check.yaml`). Reads the built `SUMMARY.md` and returns a
finding for every reader-facing occurrence, in the body, of the four things the brief cuts
(DN-014 §6 and the task's rules for the text):

* a process word (cycle, claim, leg, composite, harness, verdict, gate, pipeline);
* an indicator code (a criterion letter A to G and one or two digits: A1, A13, D1, F4);
* "AI", or "Artificial Intelligence", anywhere but a published document's exact title;
* an em dash or an en dash.

The Sources section is reference material, a list of published titles normalised by the builder,
and is skipped (`skip_section_heading`): a published title may lawfully carry AI, a code or a
dash, and the brief allows AI "inside a published document's exact title". Every other line of
the file is checked. A URL is removed before the scan so a path or a code inside a link target is
not read as body text.

This is the sibling of `scripts/dcat_faq_lint.py`, which the summary build ALSO runs for
repository-path, file-name and operator-banned-word hygiene; this module covers the four the
brief names and the lint does not.

    /opt/anaconda3/bin/python3 scripts/summary_text_check.py reports/summary/SUMMARY.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
WORDS = REPO / "reports" / "summary" / "text_check.yaml"

#: A URL or a markdown link to one: its target and label are not body prose.
URL_RE = re.compile(r"\[[^\]]*\]\(https?://[^)]*\)|<https?://[^>\s]*>|https?://\S+")


def load_words(path: Path | None = None) -> dict:
    path = path or WORDS
    if not path.is_file():
        raise SystemExit(f"FATAL: the summary word list {path} is missing; the check cannot run")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _body_lines(text: str, skip_heading: str) -> list[tuple[int, str]]:
    """(1-based line number, line) for every line except those inside the skipped section, which
    runs from its heading to the next heading of the same or a higher level, or end of file, and
    except the contents of a fenced code block (the PDF-only raw typst of the page-2 grid: its
    human strings are checked through the clean-text rendering, not its typst directives)."""
    out, skipping, skip_level, fenced = [], False, 0, False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = re.match(r"^(#+)\s+(.*)$", line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if skipping and level <= skip_level:
                skipping = False
            if not skipping and title == skip_heading:
                skipping, skip_level = True, level
                continue
        if not skipping:
            out.append((n, line))
    return out


def check(text: str, words: dict | None = None) -> list[dict]:
    words = words or load_words()
    process = [w for w in (words.get("process_words") or [])]
    proc_re = [(w, re.compile(rf"\b{re.escape(w)}\w*", re.I)) for w in process]
    code_re = re.compile(words["indicator_code_pattern"])
    ai_re = re.compile(words["ai_pattern"])
    dash_re = re.compile(words["dash_pattern"])
    # DN-014 ADDENDUM 01 §3: tier letters and rule codes, forbidden with the indicator codes.
    tier_re = re.compile(words["tier_letter_pattern"]) if words.get("tier_letter_pattern") else None
    rule_re = re.compile(words["rule_code_pattern"]) if words.get("rule_code_pattern") else None
    skip = words.get("skip_section_heading") or "\x00"
    out = []
    for n, line in _body_lines(text, skip):
        bare = URL_RE.sub(" ", line)
        for w, pat in proc_re:
            for m in pat.finditer(bare):
                out.append({"rule": "process_word", "line": n, "match": m.group(0), "word": w,
                            "context": bare[max(0, m.start() - 30): m.end() + 30].strip()})
        for m in code_re.finditer(bare):
            out.append({"rule": "indicator_code", "line": n, "match": m.group(0),
                        "context": bare[max(0, m.start() - 30): m.end() + 30].strip()})
        if rule_re is not None:
            for m in rule_re.finditer(bare):
                out.append({"rule": "rule_code", "line": n, "match": m.group(0),
                            "context": bare[max(0, m.start() - 30): m.end() + 30].strip()})
        if tier_re is not None:
            for m in tier_re.finditer(bare):
                out.append({"rule": "tier_letter", "line": n, "match": m.group(0),
                            "context": bare[max(0, m.start() - 30): m.end() + 30].strip()})
        for m in ai_re.finditer(bare):
            out.append({"rule": "ai_outside_title", "line": n, "match": m.group(0),
                        "context": bare[max(0, m.start() - 30): m.end() + 30].strip()})
        for m in dash_re.finditer(line):
            out.append({"rule": "dash", "line": n, "match": m.group(0),
                        "context": line[max(0, m.start() - 30): m.end() + 30].strip()})
    return out


def main(argv=None) -> int:
    paths = argv if argv is not None else sys.argv[1:]
    if not paths:
        raise SystemExit("usage: summary_text_check.py <SUMMARY.md> [...]")
    findings = 0
    for p in paths:
        fs = check(Path(p).read_text(encoding="utf-8"))
        for f in fs:
            print(f"{p}:{f['line']} [{f['rule']}] {f['match']!r} in {f['context']!r}")
        findings += len(fs)
    print(f"{findings} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
