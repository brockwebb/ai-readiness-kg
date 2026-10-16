#!/usr/bin/env python3
"""Each body's public data interface: assemble, check and tabulate `api_terms.yaml`.
**Zero spend, no network** (the desk research that fetched the pages is recorded in the file).

`cc_tasks/2026-10-16_readiness_brief.md` Part B. One entry per roster site (sixteen bodies and
three reference hosts), every term with the agency page's URL and a verbatim passage, or the
value "not stated". The "announced" block says, each yes / no / not determined with the URL
fetched, whether the agency serves a developer page, whether its data.json inventory lists the
API, whether `/.well-known/api-catalog` is served, and whether a roster data page links to it.

    /opt/anaconda3/bin/python3 scripts/api_terms_check.py assemble DIR   # per-body YAMLs -> api_terms.yaml
    /opt/anaconda3/bin/python3 scripts/api_terms_check.py check          # exits non-zero on a problem

`readiness_brief_build.py` renders page four and its slide from `table_rows`, only when `check`
returns no problem.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

API_TERMS = REPO / "reports" / "diagnostic" / "brief" / "api_terms.yaml"
TASK = "cc_tasks/2026-10-16_readiness_brief.md"

TERMS = ["api", "how_called", "key_obtained", "key_changes", "api_data_gov"]
ANNOUNCED = ["developer_page", "data_json_lists_api", "well_known_api_catalog", "data_page_links"]
ANNOUNCED_PLAIN = {"developer_page": "developer page", "data_json_lists_api": "data.json lists it",
                   "well_known_api_catalog": "api-catalog", "data_page_links": "data page links it"}
NOT_STATED = "not stated"
#: The agency's own site refused the fetch, so whether a page states the term is unknown; "not
#: stated" would claim an absence nobody observed. Allowed only on a row that lists the pages
#: searched (the refusal is the evidence), and counted apart from "not stated".
NOT_DETERMINED = "not determined"
NO_API = "no public api found"
ANNOUNCED_VALUES = {"yes", "no", "not determined"}


def _sources(term: dict) -> list[dict]:
    if term.get("sources"):
        return list(term["sources"])
    if term.get("url") or term.get("passage"):
        return [{"url": term.get("url"), "passage": term.get("passage")}]
    return []


def _is_gov(url: str) -> bool:
    m = re.match(r"https?://([^/]+)", str(url or ""))
    return bool(m) and m.group(1).lower().split(":")[0].endswith(".gov")


def check(doc: dict) -> list[str]:
    """Every row cites a URL and passage per term, or says "not stated"; every URL is a .gov page;
    every announced item is yes / no / not determined with the URL fetched; a "no public API found"
    row lists the pages searched; BLS states both API versions' terms; the roster is complete."""
    import diagnostic_package as D
    problems = []
    rows = (doc or {}).get("bodies") or []
    want = [b["body"] for b in D.roster_rows()]
    have = [r.get("body") for r in rows]
    if sorted(have) != sorted(want):
        problems.append(f"roster mismatch: missing {sorted(set(want) - set(have))}, extra {sorted(set(have) - set(want))}")
    for r in rows:
        b = r.get("body")
        for t in TERMS:
            term = r.get(t)
            if not isinstance(term, dict) or not str(term.get("value") or "").strip():
                problems.append(f"{b}.{t}: missing value")
                continue
            v = str(term["value"]).strip().lower()
            if v == NOT_STATED:
                continue
            if v.startswith(NOT_DETERMINED):
                if not r.get("pages_searched"):
                    problems.append(f"{b}.{t}: 'not determined' without pages_searched")
                continue
            if t == "api" and v.startswith(NO_API):
                if not r.get("pages_searched"):
                    problems.append(f"{b}.api: 'no public API found' without pages_searched")
                continue
            srcs = _sources(term)
            if not srcs:
                problems.append(f"{b}.{t}: value {term['value']!r} with no url and passage")
            for s in srcs:
                if not str(s.get("passage") or "").strip():
                    problems.append(f"{b}.{t}: source {s.get('url')!r} has no passage")
                if not _is_gov(s.get("url")):
                    problems.append(f"{b}.{t}: source {s.get('url')!r} is not a .gov page")
        ann = r.get("announced") or {}
        for a in ANNOUNCED:
            item = ann.get(a)
            if not isinstance(item, dict):
                problems.append(f"{b}.announced.{a}: missing")
                continue
            if str(item.get("value")).strip().lower() not in ANNOUNCED_VALUES:
                problems.append(f"{b}.announced.{a}: value {item.get('value')!r} not yes/no/not determined")
            if not str(item.get("url") or "").strip():
                problems.append(f"{b}.announced.{a}: no URL fetched")
    bls = next((r for r in rows if r.get("body") == "BLS"), None)
    if bls is not None:
        text = " ".join(str((bls.get(t) or {}).get("value", "")) for t in TERMS)
        if not (re.search(r"(1\.0|[Vv]ersion 1|v1)", text) and re.search(r"(2\.0|[Vv]ersion 2|v2)", text)):
            problems.append("BLS: the row does not state both API versions' terms")
    return problems


def _announced_cell(r: dict) -> str:
    ann = r.get("announced") or {}
    # The column header names the four places in order; each cell gives the four answers.
    return " / ".join(str((ann.get(a) or {}).get("value", "")) for a in ANNOUNCED)


def table_rows(doc: dict) -> list[dict]:
    """One rendered row per site, in roster order."""
    import diagnostic_package as D
    by = {r["body"]: r for r in doc["bodies"]}
    out = []
    for b in D.roster_rows():
        r = by[b["body"]]
        # The code alone: page three pairs each full name with its code, and the full names
        # would push nineteen rows past one page.
        label = b["body"]
        key = r["key_obtained"]["value"]
        dg = str(r["api_data_gov"]["value"]).strip().lower()
        if dg == "yes":
            key = f"{key} (key issued through api.data.gov)"
        out.append({"body": label, "api": r["api"]["value"], "how_called": r["how_called"]["value"],
                    "key_obtained": key, "key_changes": r["key_changes"]["value"],
                    "announced": _announced_cell(r)})
    return out


def counts(doc: dict) -> dict:
    rows = doc["bodies"]
    no_api = [r["body"] for r in rows if str(r["api"]["value"]).strip().lower().startswith(NO_API)]
    undetermined = [r["body"] for r in rows if str(r["api"]["value"]).strip().lower().startswith(NOT_DETERMINED)]
    with_api = [r["body"] for r in rows if r["body"] not in no_api and r["body"] not in undetermined]
    not_stated = sum(1 for r in rows for t in TERMS if str(r[t]["value"]).strip().lower() == NOT_STATED)
    not_determined = sum(1 for r in rows for t in TERMS if str(r[t]["value"]).strip().lower().startswith(NOT_DETERMINED))
    announced_nowhere = [r["body"] for r in rows if r["body"] in with_api and
                         all(str((r["announced"].get(a) or {}).get("value")).strip().lower() != "yes" for a in ANNOUNCED)]
    return {"rows": len(rows), "api_with_terms": len(with_api), "no_api_found": len(no_api),
            "no_api_bodies": no_api, "api_not_determined": len(undetermined), "api_not_determined_bodies": undetermined,
            "terms_not_stated": not_stated, "terms_not_determined": not_determined,
            "api_announced_in_none_of_four": len(announced_nowhere), "announced_nowhere_bodies": announced_nowhere}


def assemble(src_dir: Path) -> dict:
    import diagnostic_package as D
    order = [b["body"] for b in D.roster_rows()]
    rows = []
    for code in order:
        p = src_dir / f"{code}.yaml"
        if not p.is_file():
            raise SystemExit(f"FATAL: no research entry for {code} at {p}")
        rows.append(yaml.safe_load(p.read_text(encoding="utf-8")))
    return {"generated_by": "scripts/api_terms_check.py", "task": TASK, "fetched_on": "2026-10-16",
            "method": ("desk research from each agency's own .gov pages (WebSearch to find, WebFetch to read), "
                       "verbatim passages; not a measured check by the public client"),
            "bodies": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("assemble")
    s.add_argument("src_dir", type=Path)
    sub.add_parser("check")
    a = ap.parse_args(argv)
    if a.cmd == "assemble":
        doc = assemble(a.src_dir)
        API_TERMS.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
        print(f"wrote {API_TERMS.relative_to(REPO)} ({len(doc['bodies'])} entries)")
        return 0
    doc = yaml.safe_load(API_TERMS.read_text(encoding="utf-8"))
    problems = check(doc)
    if problems:
        print("FAIL:\n  " + "\n  ".join(problems))
        return 1
    import json
    print(json.dumps({"check": "pass", **counts(doc)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
