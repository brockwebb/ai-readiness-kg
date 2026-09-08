#!/usr/bin/env python3
"""Generate `docs/design/scan_tool_map.md` from the harness itself. **Zero spend, no network.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §4. Three tables, none of them hand-kept:

1. **Collectors** — one row per module in `scan.collectors`, joined to the legs it serves and
   the rules those legs are CURRENTLY judged by. Read from `params.yaml`, the collectors
   package and `rules.CURRENT`, so a collector that stops serving a leg loses the row on the
   next regeneration rather than lingering in prose.
2. **`specified` indicators** — every indicator the framework has not built a harness for, each
   with a one-line verdict: `scan-observable` and which collector would serve it,
   `content-evaluation` (needs the second instrument), or `not web-observable`.
3. **Gaps an open-source collector would fill** — named, **not built**.

A generated document that anyone can hand-edit is a document that will be hand-edited, so
`tests/test_scan_frame.py` regenerates this file and diffs it against the checked-in copy.

    /opt/anaconda3/bin/python3 scripts/scan_tool_map.py --check
    /opt/anaconda3/bin/python3 scripts/scan_tool_map.py
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.rules import CURRENT, parse_rule_id                       # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
OUT = REPO / "docs" / "design" / "scan_tool_map.md"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
COLLECTORS = REPO / "assessment" / "harness" / "scan" / "collectors"
RUNNER = REPO / "assessment" / "harness" / "scan" / "runner.py"

#: Which library each collector leans on, read from its own imports rather than listed. A
#: hand-kept table of "what this uses" is the first thing to go stale.
_STDLIB = {"json", "re", "urllib", "shutil", "io", "hashlib", "collections", "datetime"}

#: Gaps §4 asks to be NAMED and not built: an open-source collector exists, the harness has no
#: row for it, and each names the indicator it would serve.
GAPS = [
    ("Sitemap crawl and URL inventory",
     "`ultimate-sitemap-parser`, or `scrapy` for a bounded crawl",
     "A5 discovery measures whether a sitemap is DECLARED and fetchable; nothing walks it to "
     "count what it exposes, so 'the sitemap lists 12 URLs' and 'it lists 120,000' read alike."),
    ("schema.org `Dataset` extraction at scale",
     "`extruct` (already a dependency) driven over a URL inventory rather than one page",
     "A6 markup is measured on the surface fetched; an agency that marks up 400 dataset pages "
     "and one that marks up its home page score the same."),
    ("OpenAPI / AsyncAPI detection and validation",
     "`openapi-spec-validator`, `prance`",
     "A2 records that a description parses and reads its auth and rate-limit declarations; it "
     "does not validate the document against the OpenAPI schema, so a malformed spec that "
     "happens to carry the right keys passes."),
    ("Response-header profile",
     "no library needed; the headers are already captured and discarded",
     "Caching, compression, CORS and content negotiation are all on responses the harness "
     "already holds. No indicator consumes them yet; A2 and D2 would."),
    ("Federal DCAT catalog presence",
     "the catalog's own API — **currently unavailable**: `catalog.data.gov`'s CKAN action "
     "endpoints answered HTTP 404 on 2026-09-08 (organization_list, harvest_source_list, "
     "package_search alike)",
     "Whether a product is registered in the federal catalog is the catalog-registration "
     "indicator. It cannot be collected while the catalog's machine interface is down, which "
     "is itself the finding Tier C exists to surface."),
]


def collector_rows(params: dict) -> list:
    """One row per collector module, joined to the legs it serves."""
    # The runner's leg dispatch, split into per-leg BLOCKS. A sliding regex window over the
    # whole file ran past the end of one `if leg == ...` branch into the next and credited
    # `extent` with A8 and A9 and `v2clauses` with twelve legs. A block ends where the next
    # branch begins, and that boundary is the only thing that makes the attribution true.
    src = RUNNER.read_text(encoding="utf-8")
    marks = [(m.group(1), m.start()) for m in
             re.finditer(r'^\s*(?:el)?if leg (?:==|in) [\("\[]*([A-Za-z0-9_.\-]+)', src, re.M)]
    blocks: dict = {}
    for i, (leg, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(src)
        blocks.setdefault(leg, "")
        blocks[leg] += src[start:end]
    rows = []
    for path in sorted(COLLECTORS.glob("*.py")):
        if path.stem.startswith("_") or path.stem == "__init__":
            continue
        mod = importlib.import_module(f"scan.collectors.{path.stem}")
        text = path.read_text(encoding="utf-8")
        # `from ..errors import` captures nothing under this pattern, which is right — a
        # relative import is not a library — so empties are dropped rather than rendered as
        # an empty code span.
        libs = sorted({m.group(1).split(".")[0]
                       for m in re.finditer(r"^\s*(?:import|from)\s+([\w.]+)", text, re.M)}
                      - _STDLIB - {"scan", "__future__", ""})
        libs = [l for l in libs if l and not l.startswith(".")]
        # Which legs reach this collector, read from the runner's own dispatch.
        legs = sorted({leg for leg, body in blocks.items()
                       if leg in CURRENT and f"{path.stem}." in body})
        if path.stem == "links":
            legs = sorted(set(legs) | {"A1", "A3"})      # served through the shared link probe
        fns = sorted(n for n, o in vars(mod).items()
                     if inspect.isfunction(o) and not n.startswith("_"))
        rows.append({
            "collector": path.stem,
            "version": getattr(mod, "VERSION", "-"),
            "libraries": ", ".join(f"`{l}`" for l in libs) or "stdlib only",
            "entry_points": ", ".join(f"`{f}`" for f in fns[:4]),
            "legs": legs,
            "rules": [CURRENT[l] for l in legs if l in CURRENT],
            "doc": (mod.__doc__ or "").strip().splitlines()[0] if mod.__doc__ else "",
        })
    return rows


def specified_rows() -> list:
    """Every indicator still at `measurement_status: specified`, with a verdict."""
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    inds = [n["properties"] for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]
            and n["properties"].get("measurement_status") == "specified"]
    out = []
    for p in sorted(inds, key=lambda x: x.get("code", "")):
        text = f"{p.get('indicator', '')} {p.get('construct', '')}".lower()
        if any(t in text for t in ("document", "narrative", "describ", "explain", "rationale",
                                   "quality of", "adequa", "sufficien", "readab")):
            verdict, how = "content-evaluation", "needs the second instrument (G1-style judged reading)"
        elif any(t in text for t in ("governance", "policy", "staff", "training", "budget",
                                     "process", "steward", "roles", "organisation",
                                     "organization")):
            verdict, how = "not web-observable", "an organisational fact, not a property of a served surface"
        else:
            verdict, how = "scan-observable", "`http` + `structured_data` would serve it"
        out.append({"code": p.get("code"), "name": " ".join(str(p.get("indicator") or "").split()),
                    "verdict": verdict, "how": how})
    return out


def render(params: dict) -> str:
    cols = collector_rows(params)
    spec = specified_rows()
    L = [
        "# Scan tool map",
        "",
        f"**Generated by `scripts/scan_tool_map.py`. Do not edit by hand** — "
        f"`tests/test_scan_frame.py` regenerates this file and diffs it against the copy in "
        f"the tree, so a hand edit fails the suite. Task {TASK} §4.",
        "",
        "Every row is read from the harness itself: `params.yaml`, the `scan.collectors` "
        "package, the runner's leg dispatch, `rules.CURRENT`, and the framework of record. A "
        "collector that stops serving a leg loses its entry on the next regeneration rather "
        "than lingering in prose.",
        "",
        "## 1. Collectors",
        "",
        "| collector | v | libraries | entry points | legs served | rules |",
        "|---|---|---|---|---|---|",
    ]
    for c in cols:
        L.append(f"| `{c['collector']}` | {c['version']} | {c['libraries']} | "
                 f"{c['entry_points']} | {', '.join(c['legs']) or '—'} | "
                 f"{', '.join(f'`{r}`' for r in dict.fromkeys(c['rules'])) or '—'} |")
    L += [
        "",
        "Evidence retained by every collector is the same and is not a per-row property: the "
        "whole response body, content-addressed under `corpus/evidence/scan/`, cited by the "
        "Observation that produced it. `manners.max_body_bytes` is `null`, so nothing is "
        "truncated (`cc_tasks/2026-09-06_harness_scaffold.md` §2.1).",
        "",
        "## 2. Indicators still at `specified`",
        "",
        f"{len(spec)} indicators have no harness. The verdict says whether one could exist.",
        "",
        "| code | indicator | verdict | why |",
        "|---|---|---|---|",
    ]
    for s in spec:
        L.append(f"| {s['code']} | {s['name'][:58]} | **{s['verdict']}** | {s['how']} |")
    L += [
        "",
        "## 3. Gaps an open-source collector would fill — named, not built",
        "",
        "| gap | what would serve it | indicator it would serve |",
        "|---|---|---|",
    ]
    for name, lib, why in GAPS:
        L.append(f"| {name} | {lib} | {why} |")
    L += ["", "Nothing in this table is built by this task. Each is a row so that the next "
              "task can pick one up with the reason already written down.", ""]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and diff against the checked-in file; non-zero on drift")
    a = ap.parse_args(argv)
    body = render(load_params())
    if a.check:
        have = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if have != body:
            print("DRIFT: docs/design/scan_tool_map.md differs from regeneration", file=sys.stderr)
            return 1
        print("tool map regenerates byte-identically")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"-> {OUT.relative_to(REPO)} ({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
