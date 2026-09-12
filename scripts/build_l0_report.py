#!/usr/bin/env python3
"""Build the L0 report: resolve every number from the graph, then refuse typed ones.

Task `cc_tasks/2026-09-09_report_draft.md` §2 and §3. **Zero model spend, no network.**

**Adopted, not rebuilt.** The reference resolver, its SI checks and its Tier 2/3 prose QC are
Seldon's (`seldon.paper.build`, `seldon.paper.qc`) and are used as they stand. What this runner
supplies is the two knobs `resolve_references` documents and `build_paper` does not pass, plus
the report's own lint:

* `mark_proposed=False` — every Result in this project is `proposed`, which is the project's
  normal state and not a defect, so the marker would land on every number in the document and
  carry no information. The non-fatal SI-03 record is still emitted for each, and this runner
  counts and names them in its summary, so nothing is lost by not printing it sixty times.
* `value_formatter` — the graph stores every Result value as a float, and "16.0 agencies" is
  not what the measurement says. An integral float renders as an integer; a genuine fraction
  keeps its digits.

`build_paper` is not called because it hardcodes `paper_dir = project_dir / "paper"`. This
report is not a paper and lives in `docs/reports/`; erecting a `paper/` tree to satisfy a path
default would misdescribe the artifact.

**The bare-numeral lint is the second half of §3's gate.** A report whose every number resolves
from the graph is only half the claim; the other half is that no number got in any other way.

    /opt/anaconda3/bin/python3 scripts/build_l0_report.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, "/Users/brock/GitHub/seldon")
sys.path.insert(0, str(REPO))

REPORT_DIR = REPO / "docs" / "reports"
SECTIONS_DIR = REPORT_DIR / "sections"
OUT = REPORT_DIR / "2026-09_fss_ai_readiness_L0.md"

TASK = "cc_tasks/2026-09-09_report_draft.md"

#: A token the resolver left behind. If one of these survives into the built body, a number in
#: the report names a Result the graph does not hold.
UNRESOLVED = re.compile(r"\{\{(?:result|figure|cite):[^}]*\}\}")

#: `<!-- include: matrix_tierA -->` pastes `docs/reports/generated/matrix_tierA.md`.
#:
#: The design note requires the matrix to be RENDERED from the cycle's data rather than typed,
#: and Seldon's resolver handles Results, Figures and Citations but not table fragments. A
#: table retyped into prose is a copy, and it goes stale the first time a cell moves without
#: anything reporting that it has.
INCLUDE = re.compile(r"^[ \t]*<!--[ \t]*include:[ \t]*([A-Za-z0-9_\-]+)[ \t]*-->[ \t]*$",
                     re.M)
GEN_DIR_NAME = "generated"


def expand_includes(text: str, filename: str) -> tuple:
    """Paste every generated fragment. A missing fragment is fatal: an empty matrix in a report
    whose whole claim is the matrix would otherwise ship as a blank line."""
    missing = []

    def _sub(m):
        path = REPORT_DIR / GEN_DIR_NAME / f"{m.group(1)}.md"
        if not path.is_file():
            missing.append(f"{filename}: no generated fragment {path.relative_to(REPO)}")
            return m.group(0)
        return path.read_text(encoding="utf-8").rstrip("\n")

    return INCLUDE.sub(_sub, text), missing

# ---------------------------------------------------------------------------
# The bare-numeral lint (§3), and its exemptions, declared here rather than tuned
# ---------------------------------------------------------------------------

#: Lines that are not prose. A table row carries the matrix itself, a fenced block carries
#: machine output, and a heading carries a section number.
_TABLE = re.compile(r"^\s*\|")
_FENCE = re.compile(r"^\s*```")
_HEADING = re.compile(r"^\s*#")

#: Numerals a prose sentence may contain because they are not measurements. Each is a NAME:
#:
#: * a four-digit year, with or without a parenthesis, as in a citation;
#: * a section or item number written as `§3` or `1.`;
#: * an identifier the reader must be able to type: a leg code (`A11-declared`, `G1-D`), a
#:   decision number (`DD-059`, `AD-028`), an RFC number, an HTTP status class, a cycle date,
#:   a Result name, a file name, a `finding_id`, a git hash;
#: * anything inside backticks, which is code and not prose.
#:
#: The regex is declared in the source rather than assembled from the failures it has to
#: swallow, which is the difference between an exemption and a retune. A numeral that is
#: genuinely a measurement and is not in a `{{result}}` tag has no entry here and fails.
EXEMPT = [
    (re.compile(r"`[^`]*`"), "inline code"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "an ISO date or a cycle name"),
    (re.compile(r"\b\d+ U\.S\.C\.(?:\s*\d+)(?:\s*,\s*\d+)*"), "a statute citation"),
    (re.compile(r"\b(?:19|20)\d{2}\b"), "a year"),
    (re.compile(r"§\s?\d+(?:\.\d+)*"), "a section reference"),
    (re.compile(r"\b(?:DD|AD|PL|RFC)[- ]?\d+"), "a numbered decision, RFC or item"),
    (re.compile(r"\bA\d{1,2}(?:-[a-z]+)?\b"), "a leg code"),
    (re.compile(r"\bG1-D\b|\bB3\b|\bD1\b|\bD4\b|\bF4\b|\bE5\b|\bF\d\b"), "a leg or figure code"),
    (re.compile(r"\bv\d+\b"), "a rule version"),
    (re.compile(r"\b\d{3}\b(?=\s*(?:status|response|,|\)|\.))"), "an HTTP status"),
    (re.compile(r"^\s*\d+\.\s"), "an ordered-list marker"),
]

_DIGIT = re.compile(r"\d")


def _blank(m):
    return " " * len(m.group(0))


def _mask(line: str) -> str:
    """Blank out every resolved value and every exempt run, so what is left is prose the lint
    is entitled to judge."""
    line = MARKED.sub(_blank, line)
    for pattern, _why in EXEMPT:
        line = pattern.sub(_blank, line)
    return line


def lint_bare_numerals(text: str) -> list:
    """Every prose line carrying a numeral that is not an exempt name. §3's second clause.

    The appendix is exempt as a whole: it is a method section that names rule versions, request
    counts per netloc and fixture counts, and it is a table of identifiers rather than an
    argument. The exemption is by explicit marker in the source, not by guessing where the
    appendix starts.
    """
    out, in_fence, exempt_region = [], False, False
    # Judged over the PARAGRAPH, not the physical line. Markdown hard wraps are not semantic,
    # and a line-oriented lint reports a citation as a bare numeral the moment a rewrap puts
    # `44 U.S.C.` on one line and its section numbers on the next. The exemption patterns are
    # written against sentences; the unit they see is now a sentence's worth of text.
    para, start = [], 1
    for i, raw in enumerate(text.splitlines() + [""], 1):
        if _FENCE.match(raw):
            in_fence = not in_fence
            continue
        if "<!-- lint: numerals-exempt -->" in raw:
            exempt_region = True
            continue
        if "<!-- lint: numerals-enforced -->" in raw:
            exempt_region = False
            continue
        skip = in_fence or exempt_region or _TABLE.match(raw) or _HEADING.match(raw)
        if raw.strip() and not skip:
            if not para:
                start = i
            para.append(raw)
            continue
        if para:
            joined = " ".join(para)
            if _DIGIT.search(_mask(joined)):
                out.append((start, joined.strip()[:150]))
            para = []
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

#: Wrapped around every value the resolver substitutes, so the lint can tell a numeral that
#: CAME FROM the graph from one somebody typed.
#:
#: §3 asks for a lint over the BUILT body that finds no bare numeral "outside tags". After
#: resolution the body no longer contains tags: `{{result:...:value}}` has become `19`, and a
#: lint reading it flags every resolved number in the report, which is every number in the
#: report. Linting the SOURCE instead would satisfy the letter and check a different document
#: from the one that ships. Marking the substitutions keeps the lint on the built text and
#: still lets it answer the question actually being asked. The markers are stripped before the
#: file is written, so nothing reaches the reader.
MARK_OPEN, MARK_CLOSE = "\x00", "\x01"
MARKED = re.compile(f"{MARK_OPEN}[^{MARK_CLOSE}]*{MARK_CLOSE}")


def render_value(value):
    """`16.0` is a count of agencies and prints as `16`; `0.1936` is a bound and keeps it."""
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value)
    return f"{MARK_OPEN}{text}{MARK_CLOSE}"


def build(check: bool = False) -> int:
    from seldon.config import get_neo4j_driver, load_project_config
    from seldon.paper.build import (build_units_fallback_index, load_named_artifacts,
                                    resolve_references)
    from seldon.paper.qc import (format_violations, load_qc_config, load_style_config,
                                 run_tier2, run_tier3)

    sections = sorted(SECTIONS_DIR.glob("*.md"))
    if not sections:
        raise SystemExit(f"FATAL: no sections in {SECTIONS_DIR}")

    cfg = load_project_config(REPO)
    db = cfg["neo4j"]["database"]
    driver = get_neo4j_driver(cfg)
    try:
        artifacts = load_named_artifacts(driver, db)
        fallback = build_units_fallback_index(driver, db)
        # The "Sources per check" appendix, generated from the graph on every build like the
        # matrices, so the fragment the include pastes is never older than the graph it cites
        # (`cc_tasks/2026-09-11_report_sources_appendix.md` decision 1). A doc_id outside the
        # manifest is fatal inside the writer.
        sys.path.insert(0, str(REPO / "scripts"))
        import report_traceability
        with driver.session(database=db) as session:
            sources_appendix = report_traceability.write_sources_appendix(session)
    finally:
        driver.close()

    parts, errors, proposed, missing = [], [], set(), []
    for f in sections:
        text, miss = expand_includes(f.read_text(encoding="utf-8"), f.name)
        missing.extend(miss)
        resolved, errs = resolve_references(
            text=text, artifacts=artifacts, filename=f.name,
            # REPO, not the report directory: SI-08 resolves a Figure's `path` against this,
            # and every Figure in this graph carries a repo-relative path because that is what
            # the figure registrar writes. Pointing it at docs/reports/ would report every
            # figure as missing.
            paper_dir=REPO, units_fallback=fallback,
            allow_proposed=True, mark_proposed=False, value_formatter=render_value)
        errors.extend(errs)
        proposed |= {e.artifact_name for e in errs
                     if e.check_id == "SI-03" and e.artifact_name}
        parts.append(resolved)
    marked = "\n\n".join(p.strip() for p in parts) + "\n"
    body = marked.replace(MARK_OPEN, "").replace(MARK_CLOSE, "")

    fatal = [e for e in errors if e.fatal]
    unresolved = UNRESOLVED.findall(body)
    t2, t3 = [], []
    qc, style = load_qc_config(), load_style_config()
    for f, part in zip(sections, parts):
        clean = part.replace(MARK_OPEN, "").replace(MARK_CLOSE, "")
        t2.extend(run_tier2(clean, qc, f.name))
        t3.extend(run_tier3(clean, style, f.name))
    bare = lint_bare_numerals(marked)

    summary = {
        "sections": [f.name for f in sections],
        "words": len(body.split()),
        "fatal_reference_errors": [f"{e.check_id} {e.file}:{e.line} {e.message}" for e in fatal],
        "unresolved_tokens": unresolved,
        "proposed_results_rendered": len(proposed),
        "tier2_violations": len(t2),
        "tier3_findings": len(t3),
        "bare_numerals_in_prose": [f"line {n}: {s}" for n, s in bare],
        "missing_fragments": missing,
        "sources_appendix": sources_appendix,
    }
    blocked = bool(fatal or unresolved or bare or missing)
    summary["gate"] = "BLOCKED" if blocked else "PASS"
    if t2:
        summary["tier2_detail"] = format_violations(t2, "TIER 2").splitlines()[:24]
    if t3:
        summary["tier3_detail"] = format_violations(t3, "TIER 3").splitlines()[:24]

    print(json.dumps(summary, indent=1))
    if blocked:
        # §3: a failed gate writes NO report file. The half-built body is not left on disk to
        # be read as the product, and an earlier good build is not overwritten by a bad one.
        print(f"\nGATE BLOCKED — {OUT.relative_to(REPO)} not written ({TASK} §3).",
              file=sys.stderr)
        return 1
    if check:
        return 0
    OUT.write_text(body, encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="run the gate and write nothing")
    a = ap.parse_args(argv)
    return build(check=a.check)


if __name__ == "__main__":
    raise SystemExit(main())
