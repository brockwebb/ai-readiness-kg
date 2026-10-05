#!/usr/bin/env python3
"""Lint for the briefing FAQ and its attachment. **Zero spend, no network.**

`cc_tasks/2026-10-05_DCAT-003_ADDENDUM_01_faq_shippability.md` step 7. **The defect this exists
for:** a Desktop review on 2026-10-05 of `reports/dcat_us_3_faq/FAQ.md` at commit 1a5e6cc found
that the build had printed raw catalog notes into question 14, with repository paths, file names
and pipeline words ("PRIOR NOTE, PRESERVED", "basis (a)", "Cataloged by ..."), in a file that goes
out under the operator's name, and that em dashes, which the operator's standing rule bars from
his output, were in titles and in generated text (addendum, "Why", items 1 and 4). DCAT-003 step 4
had required "no task codes or pipeline vocabulary in either file", and its test caught neither.
The rules below are the addendum's list. `scripts/dcat_faq_build.py` runs them on both texts
before writing either file and refuses the build on any finding.

Positive control (`tests/test_dcat_faq.py`): the lint fails on FAQ.md as it stood at 1a5e6cc and
passes on the rebuilt file.

    /opt/anaconda3/bin/python3 scripts/dcat_faq_lint.py reports/dcat_us_3_faq/FAQ.md [...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

#: Removed before the path and extension rules run: a URL legitimately carries both
#: (".../wiki/DOI-DO/dcat-us/Home.md"). A markdown link whose target is a URL counts as that
#: URL, label included: in a quoted source the label names the linked file in the source's own
#: words ("[jsonschema/README.md](https://github.com/GSA/dcat-us/...)", the Overview page).
URL_RE = re.compile(r"\[[^\]]*\]\(https?://[^)]*\)|<https?://[^>\s]*>|https?://\S+")

#: (rule, pattern, applies-outside-URLs-only). Each is from the addendum's step 7 list, defect
#: report of 2026-10-05 (module docstring).
RULES = [
    ("em_dash", re.compile("—"), False),
    ("repository_path", re.compile(r"(?<![\w.-])(?:kg|docs|corpus|scripts|state|events|cc_tasks|reports)/"), True),
    ("file_extension", re.compile(r"\b[\w-]+\.(?:py|ya?ml|md|jsonl)\b"), True),
    ("pipeline_word", re.compile(r"CLAUDE\.md|PRIOR NOTE|basis \(|\bmanifest|\bcataloged\b|"
                                 r"assessed mechanically", re.I), False),
    ("task_code", re.compile(r"\b[A-Z]{1,4}-\d{3}\b"), True),
]


def _without_citation_titles(line: str) -> str:
    """A task code is legal inside a citation title (step 7). A title is the first part of a
    numbered source line ("3. Title. Issuer. ...") or an italic title opening an attachment
    location line ("*Title* (...)")."""
    m = re.match(r"^(\d+\.\s)(.*?\.)(\s.*)?$", line)
    if m:
        return m.group(1) + (m.group(3) or "")
    return re.sub(r"^\*[^*]+\*", "", line)


def lint(text: str) -> list[dict]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        bare = URL_RE.sub(" ", line)
        for rule, pat, url_free in RULES:
            subject = bare if url_free else line
            if rule == "task_code":
                subject = _without_citation_titles(subject)
            for m in pat.finditer(subject):
                out.append({"rule": rule, "line": n, "match": m.group(0),
                            "context": subject[max(0, m.start() - 40): m.end() + 40]})
    return out


def main(argv=None) -> int:
    paths = (argv if argv is not None else sys.argv[1:])
    bad = 0
    for p in paths:
        for f in lint(Path(p).read_text(encoding="utf-8")):
            bad += 1
            print(f"{p}:{f['line']} [{f['rule']}] {f['match']!r} in {f['context']!r}")
    print(f"{bad} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
