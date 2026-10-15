#!/usr/bin/env python3
"""The instrument specification: check the entries, render them, and read page two under them.
**Zero model spend.**

`cc_tasks/2026-10-15_instrument_specification_audit.md` Parts B and D, under
`docs/design/2026-10-15_DN-015_instrument_specification.md` (DN-015). One entry per check sits in
`assessment/instrument/RULE-*.yaml`; `assessment/instrument/config.yaml` names every input, output
and rule this script applies.

* `check`: every entry has every field DN-015 §2 requires; every source resolves to an admitted
  corpus document or a receipted standards URL, never prose; every state is the weakest of its
  branches' (DN-015 §3); every `pass`/`fail` Finding the rule produced on the cycle of record is
  matched by exactly one branch's `reason_match`, so a branch's state can be attributed to the
  cells that rest on it. Lists every problem and exits 1 if there is one.
* `build`: writes `reports/instrument/INSTRUMENT.md` (one table, then each check's branches) and
  `PAGE_TWO_VERDICT.md` (DN-015 §5 and §6 applied to the v3 grid), each with its PDF rendered by
  this script (`dcat_brief_build.render_pdf`, pandoc and typst), and `page_two_verdict.json`, the
  numbers the verdict's prose quotes. `build_report.json` records each PDF's Markdown sha256.

    /opt/anaconda3/bin/python3 scripts/instrument.py check
    /opt/anaconda3/bin/python3 scripts/instrument.py build [--no-pdf]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

GENERATOR = "scripts/instrument.py"
TASK = "cc_tasks/2026-10-15_instrument_specification_audit.md"
ENTRY_DIR = REPO / "assessment" / "instrument"
CONFIG = ENTRY_DIR / "config.yaml"


# ------------------------------------------------------------------------------------- loading

def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_entries(entry_dir: Path = ENTRY_DIR) -> list[dict]:
    """Every `RULE-*.yaml`, in the entries' own `order`."""
    out = []
    for p in sorted(entry_dir.glob("RULE-*.yaml")):
        e = yaml.safe_load(p.read_text(encoding="utf-8"))
        e["_path"] = str(p.relative_to(REPO))
        out.append(e)
    return sorted(out, key=lambda e: (e.get("order") or 999, e.get("rule_id", "")))


def admitted_doc_ids(cfg: dict) -> set:
    m = json.loads((REPO / cfg["inputs"]["manifest"]).read_text(encoding="utf-8"))
    return {k for k, v in m["entries"].items() if (v.get("screening") or {}).get("decision") == "included"}


def receipted_urls(cfg: dict) -> set:
    r = yaml.safe_load((REPO / cfg["inputs"]["receipts"]).read_text(encoding="utf-8"))
    return {x["url"] for x in r["receipts"] if x.get("status") == 200}


def load_grid(cfg: dict) -> dict:
    return json.loads((REPO / cfg["inputs"]["grid"]).read_text(encoding="utf-8"))


def cycle_findings(cycle: str) -> dict:
    """`{finding_id: finding}` from the cycle of record's state file."""
    s = json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))
    return {f["finding_id"]: f for f in s["findings_detail"]}


#: Terms every entry uses and INSTRUMENT.md defines once, in its preamble.
GLOSSARY = {
    "SI client (SI system)": "a system that finds, reads and uses data on its own, such as an answer engine, an agent or a retrieval pipeline; the project's term for what is elsewhere called an AI system",
    "data page": "an agency's own web page for one data product, the page the harness measures (also 'product page' in rule code)",
    "harness": "this project's scanner: an identified, robots-compliant HTTP client that fetches the pages and records what it met",
    "cycle of record": "the scan whose results the published grid is built from (here scan_2026-10-07_composite_d)",
    "recorded location": "an address for an agency's API, terms, changelog or inventory that the harness was given, read from the agency's own pages or seeded from a named source",
    "error / not measured": "the harness could not observe: an access denial, its own robots compliance, an absence it could not confirm, or a server or network error; never a fail",
    "leg": "one check as the harness runs it, named by its indicator code (A1, D4); each leg has one rule, and the codes in a test field name other legs whose fetches this one reuses",
    "rule / branch": "the versioned code that turns observations into a verdict; a branch is one way the rule can reach a verdict, with its own reason text",
    "Observation": "one recorded fetch (request, response, parsed content) that a rule judges",
    "surface": "the page a verdict is about: a data page, or for site-level checks the agency's home host",
    "body": "the agency, as the harness's records name it",
    "complete search": "an absence is reported as a fail only when every candidate location was observed and every named source searched; otherwise the verdict is error (DN-012)",
    "seed source": "a named place a recorded location came from: the agency's own developer page, catalog.data.gov, api.data.gov, this repository's citations, or a model's knowledge, each recorded per location",
    "params.*": "a named parameter in the harness's configuration file (assessment/harness/scan/params.yaml); its value is stated where it matters",
}


# ------------------------------------------------------------------------------ source texts

_TEXT_CACHE: dict = {}


def _html_text(raw: str) -> str:
    import html as _html
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw)
    return _html.unescape(re.sub(r"<[^>]+>", " ", raw))


def source_text(cfg: dict, src: str) -> str | None:
    """The text of a corpus document (by doc_id) or a receipted standard (by url), or None when
    its body is not on this machine. Corpus bodies and fetched standards are gitignored, so a
    clean worktree has none; a quote there is unverifiable, not verified."""
    if src in _TEXT_CACHE:
        return _TEXT_CACHE[src]
    path = None
    if src.startswith("http"):
        r = yaml.safe_load((REPO / cfg["inputs"]["receipts"]).read_text(encoding="utf-8"))
        path = next((x.get("stored_at") for x in r["receipts"] if x["url"] == src), None)
    else:
        m = json.loads((REPO / cfg["inputs"]["manifest"]).read_text(encoding="utf-8"))
        path = ((m["entries"].get(src) or {}).get("identity") or {}).get("canonical_path")
    text = None
    if path and (REPO / path).is_file():
        fp = REPO / path
        if fp.suffix == ".pdf":
            from pypdf import PdfReader
            text = "\n".join(pg.extract_text() or "" for pg in PdfReader(str(fp)).pages)
        else:
            raw = fp.read_text(encoding="utf-8", errors="replace")
            text = _html_text(raw) if "<html" in raw[:5000].lower() else raw
    _TEXT_CACHE[src] = text
    return text


def _loose(text: str) -> str:
    """The grounding normalizer (kg/extraction/grounding.py) plus typographic quote and dash
    folding and Markdown link flattening, so a quote copied from a rendered page matches its
    source file."""
    from kg.extraction.grounding import normalize
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    t = t.replace("`", "").replace("*", "")   # Markdown code and emphasis marks
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2013", "-"), ("\u2014", "-")):
        t = t.replace(a, b)
    # Hyphenation is tolerated symmetrically: a PDF line break inside "machine-readable" reaches the
    # grounding normalizer as "machinereadable", so a word-internal hyphen is dropped on both sides.
    return re.sub(r"(?<=\w)-(?=\w)", "", normalize(t))


def check_quotes(cfg: dict, e: dict, problems: list, unverifiable: list) -> None:
    rid = e.get("rule_id")
    for i, q in enumerate((e.get("expected_behavior") or {}).get("quotes") or []):
        text = source_text(cfg, q.get("source", ""))
        if text is None:
            unverifiable.append(f"{rid} quote[{i}] ({q.get('source')}): source body not on this machine")
            continue
        if _loose(q.get("quote", "")) not in _loose(text):
            problems.append(f"{rid} quote[{i}]: not found verbatim in {q.get('source')}: {q.get('quote', '')[:90]!r}")


# --------------------------------------------------------------------------------------- check

def _sources(value) -> list | None:
    """A source list, or None for the literal `none`."""
    if value in (None, "none"):
        return None
    if not isinstance(value, list):
        raise TypeError(f"not a list and not `none`: {value!r}")
    return value


def check_source_list(where: str, value, docs: set, urls: set, problems: list) -> list | None:
    try:
        items = _sources(value)
    except TypeError as exc:
        problems.append(f"{where}: {exc}")
        return None
    for i, s in enumerate(items or []):
        if not isinstance(s, dict):
            problems.append(f"{where}[{i}]: prose is not a source ({s!r})")
            continue
        if not str(s.get("section") or "").strip():
            problems.append(f"{where}[{i}]: no section")
        if "doc_id" in s:
            if s["doc_id"] not in docs:
                problems.append(f"{where}[{i}]: doc_id {s['doc_id']} is not an admitted corpus document")
        elif "url" in s:
            if s["url"] not in urls:
                problems.append(f"{where}[{i}]: url {s['url']} has no 200 receipt in the standards receipts")
        else:
            problems.append(f"{where}[{i}]: neither doc_id nor url")
    return items


def weakest(states: list, order: list) -> str:
    return min(states, key=order.index)


def branch_of(finding: dict, entry: dict) -> list[str]:
    """The ids of every branch whose `reason_match` matches the finding's reason and verdict."""
    return [b["id"] for b in entry.get("branches") or []
            if b.get("verdict") == finding["verdict"] and re.search(b["reason_match"], finding["reason"])]


def check(cfg: dict, entries: list, findings: dict | None = None, unverifiable: list | None = None) -> list[str]:
    problems: list[str] = []
    unverifiable = [] if unverifiable is None else unverifiable
    req = cfg["required_fields"]
    docs, urls = admitted_doc_ids(cfg), receipted_urls(cfg)
    order = cfg["state_order"]
    if findings is None:
        findings = cycle_findings(load_grid(cfg)["cycle"])
    seen_rules = set()
    for e in entries:
        rid = e.get("rule_id") or e["_path"]
        if rid in seen_rules:
            problems.append(f"{rid}: two entries")
        seen_rules.add(rid)
        for k in req["top"]:
            if e.get(k) in (None, "", [], {}):
                problems.append(f"{rid}: missing field `{k}`")
        for parent in ("question", "expected_behavior", "test", "claims"):
            for k in req[parent]:
                v = (e.get(parent) or {}).get(k)
                if v in (None, "", []):
                    problems.append(f"{rid}: missing field `{parent}.{k}`")
        if not (REPO / str(e.get("code", ""))).is_file():
            problems.append(f"{rid}: code path {e.get('code')} does not exist")
        check_source_list(f"{rid} question.established_by", (e.get("question") or {}).get("established_by"),
                          docs, urls, problems)
        eb = check_source_list(f"{rid} expected_behavior.sources",
                               (e.get("expected_behavior") or {}).get("sources"), docs, urls, problems)
        check_source_list(f"{rid} test.recognized_method_sources",
                          (e.get("test") or {}).get("recognized_method_sources", "none"), docs, urls, problems)
        quotes = (e.get("expected_behavior") or {}).get("quotes")
        if eb and not quotes:
            problems.append(f"{rid}: expected_behavior cites sources but quotes none of them")
        check_quotes(cfg, e, problems, unverifiable)
        bstates = []
        for b in e.get("branches") or []:
            bid = f"{rid} branch {b.get('id')}"
            for k in req["branch"]:
                if b.get(k) in (None, "", []):
                    problems.append(f"{bid}: missing field `{k}`")
            try:
                re.compile(str(b.get("reason_match", "")))
            except re.error as exc:
                problems.append(f"{bid}: reason_match does not compile: {exc}")
            bs = check_source_list(f"{bid} sources", b.get("sources"), docs, urls, problems)
            if b.get("state") not in cfg["states"]:
                problems.append(f"{bid}: state {b.get('state')!r} is not one of {cfg['states']}")
                continue
            if b["state"] == "specified" and not bs:
                problems.append(f"{bid}: specified with no source")
            bstates.append(b["state"])
        st = e.get("state")
        if st not in cfg["states"]:
            problems.append(f"{rid}: state {st!r} is not one of {cfg['states']}")
        elif e.get("reader_invalid"):
            # DN-015 §7: two "no" answers to the reader's first question set `invalid` whatever the
            # branches say; the reason must be on the entry.
            if st != "invalid" or not str(e["reader_invalid"].get("reason") or "").strip():
                problems.append(f"{rid}: reader_invalid requires state invalid and the reader's reason")
        elif st != "retired" and bstates:
            want = weakest(bstates, order)
            if st != want:
                problems.append(f"{rid}: state {st} but its weakest branch is {want} (DN-015 §3)")
        if st == "specified" and not eb:
            problems.append(f"{rid}: specified with expected_behavior.sources none")
        if eb is None and st == "specified":
            problems.append(f"{rid}: source none requires project_defined")
        pn = e.get("plain_name")
        if pn is not None and len(str(pn).split()) > cfg["plain_name_max_words"]:
            problems.append(f"{rid}: plain_name has {len(str(pn).split())} words, over {cfg['plain_name_max_words']}")
        flc = e.get("fix_line_check") or {}
        if flc.get("verdict") not in ("consistent", "rewritten", "not_applicable"):
            problems.append(f"{rid}: fix_line_check.verdict {flc.get('verdict')!r}")
        if flc.get("verdict") == "rewritten" and not str(flc.get("new_fix_line") or "").strip():
            problems.append(f"{rid}: fix_line_check rewritten with no new_fix_line")
        # Every decided Finding of this rule on the cycle of record rests on exactly one branch.
        for f in findings.values():
            if f["rule_id"] != e.get("rule_id") or f["verdict"] not in ("pass", "fail"):
                continue
            hit = branch_of(f, e)
            if len(hit) != 1:
                problems.append(f"{rid}: finding {f['finding_id']} ({f['verdict']}) matches "
                                f"{len(hit)} branches {hit}: {f['reason'][:120]}")
    return problems


# ------------------------------------------------------------------------- page two (DN-015 §6)

def not_measured_class(reason: str, classes: dict) -> str:
    for name, pats in classes.items():
        if any(p in reason for p in pats):
            return name
    return "other_error"


def four_state(pages: list[str]) -> str:
    """DN-015 §6 over one agency's page verdicts (`pass`, `fail`, `error`; anything else is not a
    measured pass or fail and is treated as not measured)."""
    measured = [v for v in pages if v in ("pass", "fail")]
    if measured and len(measured) == len(pages):
        if all(v == "pass" for v in measured):
            return "pass"
        if all(v == "fail" for v in measured):
            return "fail"
    if "pass" in measured and "fail" in measured:
        return "partial"
    return "could_not_measure"


def page_two(cfg: dict, entries: list, grid: dict, findings: dict) -> dict:
    by_leg = {e["leg"]: e for e in entries}
    classes = cfg["not_measured_classes"]
    cols = [c["code"] for c in grid["columns"]]
    rows_out, moves = [], collections.Counter()
    cnm_by_agency, cnm_by_check = collections.Counter(), collections.Counter()
    nm_pages = collections.Counter()
    state_v3, state_new = collections.Counter(), collections.Counter()
    branch_cells = collections.defaultdict(collections.Counter)
    for r in grid["rows"]:
        cells = {}
        for leg in cols:
            cell = r["cells"][leg]
            verdicts = [p["verdict"] for p in cell["pages"]]
            new = four_state(verdicts)
            cells[leg] = {"v3": cell["state"], "four_state": new}
            state_v3[cell["state"]] += 1
            state_new[new] += 1
            moves[(cell["state"], new)] += 1
            if new == "could_not_measure":
                cnm_by_agency[r["agency"]] += 1
                cnm_by_check[leg] += 1
            for p in cell["pages"]:
                f = findings[p["finding_id"]]
                if f["verdict"] == "error":
                    nm_pages[not_measured_class(f["reason"], classes)] += 1
                elif f["verdict"] in ("pass", "fail") and leg in by_leg:
                    b = branch_of(f, by_leg[leg])
                    bst = next((x["state"] for x in by_leg[leg]["branches"] if b and x["id"] == b[0]), "unmatched")
                    branch_cells[leg][bst] += 1
        rows_out.append({"agency": r["agency"], "display_name": r["display_name"],
                         "page_count": r["page_count"], "cells": cells})
    checks = []
    for leg in cols:
        e = by_leg.get(leg)
        st = e["state"] if e else "no_entry"
        decl = bool(e and e.get("declaration"))
        checks.append({"leg": leg, "rule_id": e["rule_id"] if e else None, "state": st,
                       "declaration": decl, "on_page_two": st == "specified" and not decl,
                       "plain_name": e.get("plain_name") if e else None,
                       "pages_by_branch_state": dict(branch_cells[leg])})
    kept = [c["leg"] for c in checks if c["on_page_two"]]
    kept_states = collections.Counter(rows_out[i]["cells"][leg]["four_state"]
                                      for i in range(len(rows_out)) for leg in kept)
    n_cells = len(rows_out) * len(cols)
    changed = sum(n for (a, b), n in moves.items() if a != b)
    return {
        "generated_by": GENERATOR, "task": TASK, "cycle": grid["cycle"],
        "grid": cfg["inputs"]["grid"], "cells": n_cells, "agencies": len(rows_out), "n_checks": len(cols),
        "v3_states": dict(state_v3), "four_states": dict(state_new),
        "cells_changing_state": changed,
        "moves": {f"{a}->{b}": n for (a, b), n in sorted(moves.items())},
        "could_not_measure": state_new.get("could_not_measure", 0),
        "could_not_measure_by_agency": dict(cnm_by_agency.most_common()),
        "could_not_measure_by_check": dict(cnm_by_check.most_common()),
        "not_measured_pages_by_class": dict(nm_pages.most_common()),
        "checks": checks, "kept_on_page_two": kept,
        "removed_from_page_two": [c["leg"] for c in checks if not c["on_page_two"]],
        "page_two_after": {"cells": len(rows_out) * len(kept), "states": dict(kept_states)},
        "rows": rows_out,
    }


# -------------------------------------------------------------------------------------- render

def _src(items) -> str:
    if items in (None, "none"):
        return "none"
    out = []
    for s in items:
        out.append(f"`{s['doc_id']}` {s['section']}" if "doc_id" in s else f"<{s['url']}> {s['section']}")
    return "; ".join(out)


def _cell(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace("|", "\\|").strip()


def instrument_markdown(cfg: dict, entries: list, reads: dict | None = None) -> str:
    reads = reads or {}
    L = ["# The instrument specification: every check as a hypothesis", "",
         f"Generated by `{GENERATOR}` from `assessment/instrument/RULE-*.yaml` under DN-015 "
         f"(`{cfg['inputs']['dn015']}`). Each row answers the operator's four questions: is it a valid "
         "question; what behavior a published source expects; what test the harness runs and whether "
         "it is the recognized one; and what a result does and does not claim. A check is "
         "`specified` only when every branch of its rule rests on a published behavior; page two of "
         "the summary shows only `specified` checks that are not declarations.", "",
         "Terms used throughout: " + "; ".join(f"**{k}**: {v}" for k, v in GLOSSARY.items()) + ".", "",
         "| # | Check | Question | Expected behavior (source) | Test, and whether it is the recognized one | "
         "A pass claims | A fail claims | Neither claims | State |",
         # Pipe-table dash counts set the PDF's relative column widths (pandoc), left-aligned.
         "|:-|:-----|:-------|:------------|:---------|:-------|:----------|:-----|:--------|"]
    for e in entries:
        name = f"**{e['leg']}** `{e['rule_id']}`" + (f": {e['plain_name']}" if e.get("plain_name") else "")
        if e.get("declaration"):
            name += " (a declaration)"
        eb = e["expected_behavior"]
        L.append("| " + " | ".join(_cell(x) for x in [
            e.get("order"), name, e["question"]["text"],
            f"{eb['text']} Sources: {_src(eb['sources'])}.",
            e["test"]["recognized_method"], e["claims"]["pass"], e["claims"]["fail"], e["claims"]["neither"],
            f"**{e['state']}**. {e['state_reason']}"]) + " |")
    L += ["", "## Branches, confounds and fix lines", "",
          "Each rule's verdict branches, with the behavior each rewards or penalizes, its source and its "
          "state (DN-015 §2). A check's state is its weakest branch's (DN-015 §3).", ""]
    for e in entries:
        L += [f"### {e['leg']} `{e['rule_id']}`", "",
              f"Code: `{e['code']}`. Client: {_cell(e['test']['client'])}. Request: {_cell(e['test']['request'])}. "
              f"Reads: {_cell(e['test']['reads'])}.", "",
              "| Branch | Verdict | Behavior | Source | State |", "|:----|:--|:----------|:--------|:---|"]
        for b in e["branches"]:
            L.append("| " + " | ".join(_cell(x) for x in [b["id"], b["verdict"], b["behavior"], _src(b["sources"]),
                                                           b["state"]]) + " |")
        L += ["", f"Not measured: {_cell(e.get('not_measured'))}", "", "Confounds:", ""]
        for c in e["confounds"]:
            L.append(f"- {_cell(c['cause'])}. Distinguished: {_cell(c['distinguished'])}.")
        flc = e["fix_line_check"]
        L.append("")
        if flc["verdict"] == "rewritten":
            L.append(f"Fix line (`{flc['action']}`): rewritten from \"{flc['fix_line']}\" to "
                     f"\"{flc['new_fix_line']}\". {_cell(flc.get('note'))}")
        elif flc["verdict"] == "consistent":
            L.append(f"Fix line (`{flc['action']}`): \"{flc['fix_line']}\", consistent with the expected "
                     f"behavior. {_cell(flc.get('note'))}".rstrip())
        else:
            L.append("Fix line: none (not a grid column).")
        if e.get("settles"):
            L += ["", "What this entry settles:", ""]
            for k, v in e["settles"].items():
                L.append(f"- **{k.replace('_', ' ')}**: {_cell(v)}")
        rs = reads.get(e["rule_id"]) or []
        if rs:
            import instrument_read as IR  # the reader's own view of an entry, to tell a revised one
            now = hashlib.sha256(IR.entry_text(e).encode("utf-8")).hexdigest()
            L += ["", "Reader (DN-015 §7; role `judge`):", ""]
            for r in rs:
                a = r["answers"]
                L.append(f"- Round {r['round']} (`{r['model_id']}`): source {a['q1']['answer']}; misreading "
                         f"{a['q2']['answer']}; undefined terms {a['q3']['answer']}. {_cell(a['q1']['why'])}")
            if rs[-1]["entry_sha256"] != now:
                L.append("- The entry was revised after its last reading (its claims or terms, from the reader's "
                         "answers to questions 2 and 3); that revision has not been read.")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


STATE_WORD = {"pass": "pass", "fail": "fail", "partial": "partial", "could_not_measure": "could not measure"}


def verdict_markdown(v: dict, entries: list) -> str:
    by_leg = {e["leg"]: e for e in entries}
    kept, removed = v["kept_on_page_two"], v["removed_from_page_two"]
    cnm = v["could_not_measure"]
    L = ["# Page two under the instrument specification: the verdict", "",
         f"Generated by `{GENERATOR}` from `{v['grid']}` (cycle `{v['cycle']}`) and the instrument "
         "entries, under DN-015 §5 (page two shows only `specified` checks) and §6 (the cell has four "
         "states). `SUMMARY.pdf` is not rebuilt here; the rebuild is a follow-on task, registered after "
         "the operator reads this verdict.", "",
         "## Which checks may appear", "",
         "| Check | Plain name (what a pass asserts) | State | On page two |", "|---|---|---|---|"]
    for c in v["checks"]:
        L.append(f"| {c['leg']} | {_cell(c['plain_name'])} | {c['state']}"
                 f"{' (declaration)' if c['declaration'] else ''} | {'yes' if c['on_page_two'] else 'no'} |")
    L += ["", f"{len(kept)} of the grid's {v['n_checks']} checks are `specified` and may appear: "
              f"{', '.join(kept) or 'none'}. {len(removed)} come off: "
              + "; ".join(f"{leg} ({by_leg[leg]['state'] if leg in by_leg else 'no entry'})" for leg in removed) + ".",
          "", "## How many of the cells change state", "",
          f"Under DN-015 §6 a page the harness could not measure is no longer a fail. Of the "
          f"{v['cells']} cells ({v['agencies']} agencies by {v['n_checks']} checks), "
          f"**{v['cells_changing_state']} change state** and **{cnm} become \"could not measure\"**.", "",
          "| v3 state | four-state | cells |", "|---|---|---|"]
    for k, n in v["moves"].items():
        a, b = k.split("->")
        L.append(f"| {a} | {STATE_WORD.get(b, b)} | {n} |")
    L += ["", "Why the pages behind those cells were not measured (pages, not cells):", "",
          "| class | pages |", "|---|---|"]
    for k, n in v["not_measured_pages_by_class"].items():
        L.append(f"| {k.replace('_', ' ')} | {n} |")
    L += ["", "Where the \"could not measure\" cells concentrate, by agency (of "
              f"{v['n_checks']} checks each):", "", "| agency | cells |", "|---|---|"]
    names = {r["agency"]: r["display_name"] for r in v["rows"]}
    for a, n in v["could_not_measure_by_agency"].items():
        L.append(f"| {names.get(a, a)} | {n} |")
    L += ["", "And by check:", "", "| check | cells |", "|---|---|"]
    for a, n in v["could_not_measure_by_check"].items():
        L.append(f"| {a} | {n} |")
    pa = v["page_two_after"]
    L += ["", "## Page two after both rules", "",
          f"With only the {len(kept)} `specified` columns kept, page two would hold {pa['cells']} cells: "
          + ", ".join(f"{STATE_WORD.get(k, k)} {n}" for k, n in sorted(pa["states"].items())) + ".", "",
          "## Cells that rested on a project-defined branch", "",
          "For each grid check, how many measured pages (pass or fail) were decided by a branch in each "
          "state; a page decided by a `project_defined` or `invalid` branch carries no published claim.", "",
          "| check | pages by branch state |", "|---|---|"]
    for c in v["checks"]:
        L.append(f"| {c['leg']} | {', '.join(f'{k} {n}' for k, n in sorted(c['pages_by_branch_state'].items())) or 'none measured'} |")
    return "\n".join(L).rstrip() + "\n"


#: The PDF's page and type: landscape from the first page, small type, ragged right (the table's
#: cells are long). Pandoc's typst writer takes `header-includes` before the title is set.
PDF_HEADER = "#set page(flipped: true)\n#show figure: set block(breakable: true)"
#: Set again at the top of the body: the template's own text and paragraph settings follow the
#: header, so these must come after them.
PDF_BODY_PREAMBLE = "```{=typst}\n#set text(hyphenate: false)\n#set par(justify: false)\n```\n\n"
PDF_FONT_PT = 7


def render_pdf(md_path: Path, pdf_path: Path, title: str) -> None:
    """Pandoc and typst, as `dcat_brief_build.render_pdf` calls them, with this report's page."""
    import subprocess
    cmd = ["pandoc", str(md_path), "--from=markdown+pipe_tables+raw_attribute-smart", "--pdf-engine=typst",
           "--metadata", f"title={title}", "--variable", "papersize=us-letter",
           "--variable", f"header-includes={PDF_HEADER}", "--variable", f"fontsize={PDF_FONT_PT}pt",
           "--variable", "margin-x=1.2cm", "--variable", "margin-y=1.2cm", "-o", str(pdf_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: pandoc/typst failed for {md_path.name}:\n{r.stderr[-1500:]}")


def write_report(md_path: Path, md: str, pdf: bool) -> dict:
    """Write the Markdown, and render its PDF from it through a scratch copy without the H1 (the
    title goes in as pandoc metadata). Records the Markdown's sha256, so a test checks the pair by
    hash (git keeps no file times)."""
    md_path.write_text(md, encoding="utf-8")
    rec = {"markdown": md_path.name, "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()}
    if pdf:
        from pypdf import PdfReader
        m = re.match(r"\A# (.*)\n", md)
        if not m:
            raise SystemExit(f"FATAL: {md_path.name} has no title line")
        pdf_path = md_path.with_suffix(".pdf")
        scratch = md_path.with_name(f".{md_path.stem}.render.md")
        try:
            scratch.write_text(PDF_BODY_PREAMBLE + md[m.end():], encoding="utf-8")
            render_pdf(scratch, pdf_path, m.group(1))
        finally:
            scratch.unlink(missing_ok=True)
        rec.update({"pdf": pdf_path.name, "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                    "pages": len(PdfReader(str(pdf_path)).pages)})
    return rec


def load_reads(cfg: dict) -> dict:
    """`{rule_id: [read, ...]}` in round order, from the reader's run record."""
    p = REPO / cfg["reader"]["run_dir"] / "verify.json"
    if not p.is_file():
        return {}
    out: dict = {}
    for r in json.loads(p.read_text(encoding="utf-8")).get("reads", []):
        out.setdefault(r["rule_id"], []).append(r)
    return {k: sorted(v, key=lambda r: r["round"]) for k, v in out.items()}


def build(cfg: dict, pdf: bool = True) -> dict:
    entries = load_entries()
    grid = load_grid(cfg)
    findings = cycle_findings(grid["cycle"])
    out = REPO / cfg["outputs"]["dir"]
    out.mkdir(parents=True, exist_ok=True)
    v = page_two(cfg, entries, grid, findings)
    (out / cfg["outputs"]["verdict_json"]).write_text(json.dumps(v, indent=1) + "\n", encoding="utf-8")
    report = {"generated_by": GENERATOR, "task": TASK, "reports": [
        write_report(out / cfg["outputs"]["instrument_md"], instrument_markdown(cfg, entries, load_reads(cfg)), pdf),
        write_report(out / cfg["outputs"]["verdict_md"], verdict_markdown(v, entries), pdf)]}
    (out / cfg["outputs"]["build_report"]).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    b = sub.add_parser("build")
    b.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config()
    if a.cmd == "check":
        entries = load_entries()
        unverifiable: list = []
        problems = check(cfg, entries, unverifiable=unverifiable)
        print(f"{len(entries)} entries checked; {len(problems)} problem(s); "
              f"{len(unverifiable)} quote(s) unverifiable here")
        for u in unverifiable:
            print(f"  ? {u}")
        for p in problems:
            print(f"  - {p}")
        return 1 if problems else 0
    rep = build(cfg, pdf=not a.no_pdf)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
