#!/usr/bin/env python3
"""The brief's material pack, generated from the record. **Zero spend, no network, reads only.**

`cc_tasks/2026-09-22_brief_material_pack_v2.md`, under DN-005: the framework is the goal and the
report, the site, the MCP and this pack are VIEWS of it. Every file under `docs/brief/` is
written by this script and by nothing else; no indicator, rule, verdict, Result, Finding or
corpus document is created or changed by it.

    scripts/build_brief_pack.py                 write every pack file (needs Neo4j)
    scripts/build_brief_pack.py --check         re-render into memory; exit 1 on any drift
    scripts/build_brief_pack.py --check --no-graph
                                                the same, over the files that need no graph
    scripts/build_brief_pack.py --capture-demo  execute the runbook's commands ONCE and store
                                                what they printed (docs/brief/D_demo_capture.json)

**Sources, and only these.** The framework record (`framework/ai_readiness_framework.json`), the
crosswalk skeleton it is generated from, the corpus manifest, the rule registry
(`assessment/harness/scan/rules`), the published matrices of the cycle of record
(`docs/reports/publication.yaml: snapshot_cycle`), `scripts/score.py` and
`scripts/report_traceability.py` as imported code, and the MCP verbs (`mcp/airkg_tools.py`), which
read Neo4j for Finding reasons, retained-body digests and registered Results. The pages that need
the graph are listed in `GRAPH_PAGES`; `--no-graph` renders every other page.

**Idempotence** is the regenerate-and-compare guard the other views use (`mcp/airkg_doc.py
--check`, `scripts/score.py --check`): a second run is a byte-for-byte no-op, and
`tests/test_brief_pack.py` asserts it. Nothing here reads a clock. The one page whose content
came from running commands (`D_demo_runbook.md`) is rendered from the stored capture, and the
capture is written only by `--capture-demo`, so the render stays deterministic.

**Numbers.** No numeral is typed into prose. Every number a page states in prose goes through
`Page.n(value, source)`, which records it with its source in `docs/brief/numbers.json`; the test
reads each page's prose and fails on a numeral the ledger does not hold for that page. Tables,
code blocks, block quotes and backticked spans are verbatim record or tool output and are not
prose.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "mcp"))

import yaml  # noqa: E402

OUT = REPO / "docs" / "brief"
CAPTURE = OUT / "D_demo_capture.json"
LEDGER = OUT / "numbers.json"
RECORD = REPO / "framework" / "ai_readiness_framework.json"
SKELETON = REPO / "docs" / "crosswalk" / "usafacts_operationalization_skeleton.md"
MANIFEST = REPO / "corpus" / "manifest.json"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
DN007 = REPO / "docs" / "design" / "2026-09-19_DN-007_operator_rulings_and_state.md"
DN003 = REPO / "docs" / "design" / "2026-09-14_DN-003_event_log_and_rejudgements.md"
FRAME_SECTION = REPO / "docs" / "reports" / "sections" / "10_frame.md"
SELDON_REPO = Path("/Users/brock/GitHub/seldon")
PY = "/opt/anaconda3/bin/python3"
TASK = "cc_tasks/2026-09-22_brief_material_pack_v2.md"
GENERATOR = "scripts/build_brief_pack.py"

#: The body the dogfood page and the worked data-flow example are about. MVP brief task
#: `5f1bf9f0`: "Census as first internal user".
DOGFOOD_BODY = "CENSUS"

#: The four criteria USAFacts named. Skeleton line 11: "USAFacts' four criteria (accessible,
#: understandable, accurate, open) as the top-level structure". Everything else in the record's
#: criterion list is an addition, and the section each addition comes from is DERIVED below from
#: the skeleton's tables, not declared here.
USAFACTS_CRITERIA = ("A", "B", "C", "D")

#: The three admitted USAFacts documents the `kept_verbatim_or_restated` column is measured
#: against (`cc_tasks/2026-09-22_brief_deck_assembly.md` decision 7). The record cannot say
#: whether an indicator kept USAFacts' words; the corpus can, by the grounding test the
#: extractor already uses. Paths come from the manifest, never from here.
USAFACTS_DOCS = ("usafacts-ai-ready-data-guide", "usafacts-fde-standards-detailed",
                 "usafacts-fde-standards-quick-reference")
#: The record fields tested, in order: the construct first, then the indicator text.
VERBATIM_FIELDS = ("construct", "indicator")

#: Federal policy instruments the brief asks provenance against (task decision 3). Each is a
#: regex over a manifest entry's doc_id and title, and over an indicator's evidence cell. The
#: patterns are the instrument's own names; a pattern that matches no admitted document is
#: reported as such, never widened until it does.
INSTRUMENTS = [
    ("Evidence Act", r"evidence.based.policymaking|evidence act"),
    ("M-25-05", r"m-25-05"),
    ("M-23-22", r"m-23-22"),
    ("Title 13", r"title[ -]13\b"),
    ("CIPSEA", r"cipsea|confidential information protection and statistical efficiency"),
    ("SPD (Statistical Policy Directive)", r"statistical policy directive|\bspd[ -]?\d"),
    ("DCAT-US", r"dcat-us|dcat.us"),
]

#: Pages that need Neo4j: Finding reasons, retained digests, SUPERSEDES chains and registered
#: Results live only on the projection.
GRAPH_PAGES = ("E_architecture.md", "F_results_pointer.md", "G_census_dogfood.md",
               "H_limits.md", "INDEX.md")

#: How many lines of a command's output the runbook shows, head and tail. The task: "its first
#: lines of output pasted under it". The tail is kept too because a pytest verdict is its last
#: line.
HEAD_LINES = 14
TAIL_LINES = 3
#: Seconds a runbook command may take before it is recorded as timed out.
COMMAND_TIMEOUT = 900
#: The MCP server speaks stdio and waits for a client; it gets this long with stdin closed.
SERVER_TIMEOUT = 30


# ------------------------------------------------------------------------------ sources

def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def git_out(*args: str, cwd: Path = REPO) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FATAL: git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


class Sources:
    """Every input, read once."""

    def __init__(self, graph=None):
        self.record = load_json(RECORD)
        self.manifest = load_json(MANIFEST)["entries"]
        self.publication = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))
        self.cycle = self.publication["snapshot_cycle"]
        self.skeleton = SKELETON.read_text(encoding="utf-8").splitlines()
        # The record carries `generated_from` as a PATH (the skeleton), not a commit; the
        # commit is the last one that wrote the record, which is what a reader can check out.
        self.record_commit = git_out("log", "-1", "--format=%H", "--",
                                     str(RECORD.relative_to(REPO)))
        self.nodes = {n["id"]: n for n in self.record["nodes"]}
        self.edges = self.record["edges"]
        self.inds = [n for n in self.record["nodes"] if "AssessmentIndicator" in n["labels"]]
        self.inds.sort(key=lambda n: code_key(n["properties"]["code"]))
        from framework_writeback import _candidate_ids
        self.candidates = _candidate_ids(self.record)
        from scan import rules as R
        self.R = R
        self.graph = graph
        self._tools = None
        self._score = None
        self._usafacts = None

    @property
    def usafacts(self) -> dict:
        """`{doc_id: text}` of the admitted USAFacts documents, read the way the extractor
        reads them (`run_bulk_extraction.doc_text`: the DD-030 substrate if one exists, else
        the PDF's text layer), so "grounds verbatim" here means what it means for an edge."""
        if self._usafacts is None:
            from run_bulk_extraction import doc_text
            out = {}
            for d in USAFACTS_DOCS:
                if d not in self.manifest:
                    raise SystemExit(f"FATAL: {d} is not in {rel(MANIFEST)}; the verbatim "
                                     "column cannot be measured against a document not admitted")
                path = REPO / self.manifest[d]["identity"]["canonical_path"]
                if not path.is_file():
                    raise SystemExit(f"FATAL: {rel(path)} ({d}) is not on disk; the corpus "
                                     "binaries are gitignored, re-acquire before rendering")
                out[d] = doc_text(path, d)
            self._usafacts = out
        return self._usafacts

    def kept(self, props: dict) -> str:
        """Decision 7: `verbatim (<doc_id>)` when the construct, then the indicator, grounds
        in a USAFacts document under `kg/extraction/grounding.py`; `restated` when neither
        grounds anywhere; `n/a (added criterion)` outside USAFacts' four criteria."""
        if props["criterion_code"] not in USAFACTS_CRITERIA:
            return "n/a (added criterion)"
        from kg.extraction.grounding import is_grounded
        for field in VERBATIM_FIELDS:
            for d in USAFACTS_DOCS:
                if is_grounded(props.get(field) or "", self.usafacts[d]):
                    return f"verbatim ({d})"
        return "restated"

    @property
    def tools(self):
        if self._tools is None:
            import airkg_tools as T
            self._tools = T.Tools(graph=self.graph)
        return self._tools

    @property
    def score(self) -> dict:
        if self._score is None:
            import score as S
            self._score = S.compute(self.cycle)
        return self._score

    def gread(self, cypher: str, **params) -> list:
        if self.graph is None:
            raise SystemExit("FATAL: a graph page was rendered without the graph")
        rows, _ = self.graph.read(cypher, **params)
        return rows

    def out_edges(self, frm: str, etype: str) -> list:
        return [e for e in self.edges if e["from"] == frm and e["type"] == etype]

    def in_edges(self, to: str, etype: str) -> list:
        return [e for e in self.edges if e["to"] == to and e["type"] == etype]

    def rule_for(self, code: str) -> list:
        """`[(leg, current rule id)]` for every current rule whose id parses to this indicator."""
        out = []
        for leg, rid in self.R.CURRENT.items():
            if self.R.parse_rule_id(rid)["indicator_code"] == code:
                out.append((leg, rid))
        return out

    def matrices(self) -> dict:
        from build_l0_site import cycle_suffix
        suf = cycle_suffix(self.cycle)
        out = {}
        for stem in ("tierA", "tierC", "product"):
            p = REPO / "docs" / "reports" / f"scan_matrix_{stem}_{suf}.json"
            out[stem] = (p, load_json(p))
        return out


def code_key(code: str) -> tuple:
    m = re.match(r"([A-Z])(\d+)(.*)", code)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (code, 0, "")


def rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def line_of(path: Path, needle: str, regex: bool = False) -> int:
    """1-indexed line of the first match. Fails loud: a box whose code moved is a diagram that
    is now wrong, and it must not render as if it were right."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        if (re.search(needle, line) if regex else needle in line):
            return i
    raise SystemExit(f"FATAL: {path} has no line matching {needle!r}; the diagram is stale")


def sym(path: Path, name: str) -> str:
    """`path:line` of a `def`/`class` symbol, or of a literal line when `name` has a space."""
    if " " in name or ":" in name:
        n = line_of(path, name)
    else:
        n = line_of(path, rf"^\s*(def|class)\s+{re.escape(name)}\b", regex=True)
    try:
        shown = str(path.relative_to(REPO))
    except ValueError:
        shown = "seldon/" + str(path.relative_to(SELDON_REPO))
    return f"{shown}:{n}"


# ------------------------------------------------------------------------------ pages

class Page:
    def __init__(self, name: str, chapter: str, sources: list, s: Sources):
        self.name = name
        self.chapter = chapter
        self.sources = sources
        self.nums = []
        self.lines = [header(s, "<!--", "-->")] if name.endswith(".md") else []

    def n(self, value, source: str, fmt: str | None = None) -> str:
        """A number in prose, with its source on the ledger."""
        if isinstance(value, float):
            shown = format(value, fmt or ".3f")
        else:
            shown = str(value)
        self.nums.append({"value": shown, "source": source})
        return shown

    def add(self, *lines: str) -> None:
        self.lines.extend(lines)

    def text(self) -> str:
        return "\n".join(self.lines).rstrip("\n") + "\n"


def header(s: Sources, open_: str, close: str) -> str:
    return (f"{open_} generated by {GENERATOR} ({TASK}); framework record at commit "
            f"{s.record_commit[:12]} (framework/ai_readiness_framework.json, generated_from "
            f"{s.record['generated_from']}); cycle of record {s.cycle}. Do not edit: re-run the "
            f"generator. {close}".rstrip())


def cell(v) -> str:
    """A value as a markdown table cell."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    elif isinstance(v, dict):
        v = json.dumps(v, sort_keys=True, ensure_ascii=False)
    return str(v).replace("|", "\\|").replace("\n", " ").strip()


def table(head: list, rows: list) -> list:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return out


def csv_text(s: Sources, head: list, rows: list) -> str:
    buf = io.StringIO()
    buf.write(header(s, "#", "") + "\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(head)
    for r in rows:
        w.writerow(["; ".join(map(str, c)) if isinstance(c, (list, tuple)) else
                    ("" if c is None else c) for c in r])
    return buf.getvalue()


# ------------------------------------------------------------------------------ skeleton

def skeleton_sections(s: Sources) -> list:
    """`[(line, heading, [codes in its tables])]` for every `## ` heading of the skeleton."""
    out, cur = [], None
    for i, line in enumerate(s.skeleton, 1):
        if line.startswith("## "):
            cur = [i, line[3:].strip(), []]
            out.append(cur)
        elif cur is not None:
            m = re.match(r"^\|\s*\*{0,2}([A-G]\d{1,2}(?:-[A-Z])?)\*{0,2}\s*\|", line)
            if m:
                cur[2].append(m.group(1))
    return [tuple(x) for x in out]


def criterion_sections(s: Sources) -> dict:
    """criterion letter -> (section line, heading), by which section's table rows carry its
    indicator codes. Derived, so a criterion moved to another section moves here with it."""
    out = {}
    for line, heading, codes in skeleton_sections(s):
        letters = Counter(c[0] for c in codes)
        for letter, _ in letters.most_common():
            out.setdefault(letter, (line, heading))
    return out


def feedback_items(s: Sources) -> list:
    """§8's numbered items: `[(line, text)]`."""
    start = next(i for i, l in enumerate(s.skeleton, 1)
                 if l.startswith("## 8. What this feeds back"))
    items = []
    for i in range(start, len(s.skeleton)):
        line = s.skeleton[i]
        if line.startswith("## ") and i + 1 != start:
            break
        if re.match(r"^\d+\. ", line):
            items.append((i + 1, line))
    return items


def skeleton_quote(s: Sources, needle: str) -> tuple:
    n = line_of(SKELETON, needle)
    return n, s.skeleton[n - 1]


# ------------------------------------------------------------------------------ B

def indicator_marks(s: Sources) -> list:
    secs = criterion_sections(s)
    crit = {n["properties"]["code"]: n["properties"] for n in s.record["nodes"]
            if "AssessmentCriterion" in n["labels"]}
    fb = feedback_items(s)
    codes = {n["properties"]["code"] for n in s.inds}
    rows = []
    for n in s.inds:
        p = n["properties"]
        code, letter = p["code"], p["criterion_code"]
        rules = s.rule_for(code)
        if n["id"] in s.candidates:
            mark = "candidate (DD-054: reported, not part of the framework)"
        elif letter in USAFACTS_CRITERIA:
            mark = f"added (operationalizes {letter} {crit[letter]['name']})"
        else:
            line, heading = secs[letter]
            mark = f"added (criterion {letter}, skeleton line {line}: {heading})"
        departures = []
        for line, text in fb:
            named = set(re.findall(r"\b([A-G]\d{1,2}(?:-[A-Z])?)\b", text)) & codes
            family = {c for c in re.findall(r"\b([A-G]\d{1,2})\b", text)}
            if code in named or (code.split("-")[0] in family and "-" in code):
                departures.append(f"skeleton line {line}: {text.strip()}")
        for k in ("construct_restated", "withdrawn_from"):
            if p.get(k):
                departures.append(f"record `{n['id']}.{k}`: {p[k]}")
        rows.append({
            "code": code, "criterion": letter, "construct": p["construct"],
            "indicator": p["indicator"], "type": p["type"],
            "measurement_tier": p.get("measurement_tier") or "unassigned",
            "measurement_basis": p.get("measurement_basis") or "",
            "rule": ", ".join(r for _, r in rules) or "none",
            "rule_built": "yes" if rules else "no",
            "access_tier": p["tier"], "status": p["status"], "mark": mark,
            "departure": " || ".join(departures),
            "kept_verbatim_or_restated": s.kept(p),
        })
    return rows


B_HEAD = ["code", "criterion", "construct", "indicator", "type", "measurement_tier",
          "measurement_basis", "rule", "rule_built", "access_tier", "status", "mark",
          "departure", "kept_verbatim_or_restated"]


def page_b(s: Sources) -> tuple:
    pg = Page("B_usafacts_delta.md", "B. Delta against the USAFacts framework",
              [rel(RECORD), rel(SKELETON), "assessment/harness/scan/rules/__init__.py"], s)
    rows = indicator_marks(s)
    secs = criterion_sections(s)
    crit = [n for n in s.record["nodes"] if "AssessmentCriterion" in n["labels"]]
    crit.sort(key=lambda n: n["properties"]["code"])
    l1, q1 = skeleton_quote(s, "It does not give an agency a test.")
    lf, qf = skeleton_quote(s, "USAFacts' four criteria")
    total = len(rows)
    built = sum(1 for r in rows if r["rule_built"] == "yes")
    with_dep = sum(1 for r in rows if r["departure"])
    kept = Counter(r["kept_verbatim_or_restated"].split(" (")[0] for r in rows)
    pg.add("# B. Delta against the USAFacts AI-ready data framework", "",
           "## How the delta is derived",
           "",
           "The framework record has no `origin` field, so no mark on this page is read off the "
           "record directly. Each mark is derived by three rules, and each rule cites the "
           "skeleton line it rests on:",
           "",
           f"1. Criteria A to D are USAFacts' four and are kept as the top-level structure "
           f"(`{rel(SKELETON)}:{lf}`).",
           "2. Criteria E, F and G are additions. The section of the skeleton each one comes "
           "from is the section whose tables carry its indicator codes, and that section's "
           "heading says why it was added (table below).",
           f"3. Within A to D, USAFacts named criteria and gave no indicator-level tests "
           f"(`{rel(SKELETON)}:{l1}`), so every indicator is an operationalization and is "
           "marked `added (operationalizes <criterion>)`.",
           "",
           f"> {q1.strip()}",
           "",
           "An indicator whose record `status` is `candidate` is marked that way instead. No "
           "indicator in the record has a status of withdrawn or dropped. The record cannot "
           "tell an indicator kept verbatim from USAFacts' text apart from one restated, so no "
           "mark says either. The `kept_verbatim_or_restated` column is measured against the "
           f"admitted USAFacts documents ({', '.join(f'`{d}`' for d in USAFACTS_DOCS)}): an "
           "indicator of criteria A to D is `verbatim (<doc_id>)` when its `construct`, else "
           "its `indicator`, string grounds verbatim in one of them under "
           "`kg/extraction/grounding.py` normalization, `restated` when neither grounds in any, "
           "and an indicator of criteria E, F and G is `n/a (added criterion)`; "
           f"{pg.n(kept['verbatim'], 'indicators whose construct or indicator grounds verbatim in a USAFacts document')} "
           f"are verbatim, {pg.n(kept['restated'], 'indicators of criteria A to D grounding in no USAFacts document')} "
           f"restated and {pg.n(kept['n/a'], 'indicators of criteria E, F and G')} n/a.",
           "",
           f"Of {pg.n(total, 'count of AssessmentIndicator nodes in the record')} indicator "
           f"nodes, {pg.n(built, 'indicators with a current rule in rules.CURRENT')} have a "
           "current rule in the registry. "
           f"{pg.n(with_dep, 'indicators with a departure quote')} carry a departure quote, "
           "either from skeleton §8 (items that name the indicator's code) or from a record "
           "property that records a restatement or a withdrawal.",
           "", "## Criteria", "")
    crows = []
    for c in crit:
        p = c["properties"]
        if p["code"] in USAFACTS_CRITERIA:
            mark = f"kept (USAFacts criterion; skeleton line {lf})"
        else:
            line, heading = secs[p["code"]]
            mark = f"added (skeleton line {line}: {heading})"
        sec = secs.get(p["code"])
        tag = re.match(r"(\d+[a-z]?)\.", sec[1]).group(1) if sec else None
        fb = [f"line {line}" for line, text in feedback_items(s)
              if re.search(rf"\b{re.escape(p['name'])}\b", text, re.I)
              or (tag and f"§{tag})" in text) or (tag and f"§{tag} " in text)]
        crows.append([p["code"], p["name"], mark, fb or "", p.get("anchor", "")])
    pg.add("A §8 item is linked to a criterion when it names the criterion or cites the "
           "skeleton section the criterion's indicators sit in.", "")
    pg.add(*table(["code", "name", "mark", "§8 items", "anchor (record)"], crows))
    pg.add("", "## Skeleton §8, what this feeds back to USAFacts", "",
           "Quoted whole. An item that names an indicator code is also quoted in that "
           "indicator's `departure` column below.", "")
    for line, text in feedback_items(s):
        pg.add(f"> `{rel(SKELETON)}:{line}` {text.strip()}", ">")
    if pg.lines[-1] == ">":
        pg.lines.pop()
    pg.add("", "## Indicators", "",
           "The same rows are in `B_usafacts_delta.csv`. `rule` is the current rule id from "
           "`rules.CURRENT` whose id parses to the indicator's code. `access_tier` is the "
           "record's `tier` (public, agency_instrumented or paid).", "")
    pg.add(*table(B_HEAD, [[r[h] for h in B_HEAD] for r in rows]))
    csvt = csv_text(s, B_HEAD, [[r[h] for h in B_HEAD] for r in rows])
    return pg, {"B_usafacts_delta.csv": csvt}


# ------------------------------------------------------------------------------ C

def provenance_rows(s: Sources) -> tuple:
    from report_traceability import locators
    rows, per_ind = [], {}
    for n in s.inds:
        p = n["properties"]
        locs = locators(p.get("evidence_raw") or "")
        docs = sorted(e["properties"]["doc_id"] for e in s.out_edges(n["id"], "EVIDENCED_BY"))
        per_ind[p["code"]] = {"locs": locs, "docs": docs,
                              "internal": sorted(e["to"] for e in
                                                 s.out_edges(n["id"], "EVIDENCED_BY_INTERNAL"))}
        for d in docs:
            ent = s.manifest.get(d)
            rows.append([p["code"], d,
                         (ent or {}).get("identity", {}).get("doc_type") or
                         ("not in manifest" if ent is None else "none recorded"),
                         (ent or {}).get("screening", {}).get("decision", ""),
                         "yes" if locs.get(d) else "no", locs.get(d, "")])
    return rows, per_ind


C_HEAD = ["indicator", "doc_id", "doc_type (manifest)", "screening", "pinpoint_locator",
          "locator (evidence cell)"]


def instrument_rows(s: Sources) -> list:
    out = []
    for name, pat in INSTRUMENTS:
        rx = re.compile(pat, re.I)
        docs = sorted(k for k, v in s.manifest.items()
                      if v["screening"]["decision"] == "included"
                      and rx.search(k + " " + (v["identity"].get("title") or "")))
        by_edge = sorted({e["from"][4:] for e in s.edges if e["type"] == "EVIDENCED_BY"
                          and e["properties"]["doc_id"] in docs}, key=code_key)
        by_text = sorted({n["properties"]["code"] for n in s.inds
                          if rx.search(n["properties"].get("evidence_raw") or "")},
                         key=code_key)
        out.append([name, f"`{pat}`", docs or "none admitted", by_edge or "none",
                    [c for c in by_text if c not in by_edge] or "none"])
    return out


def page_c(s: Sources) -> tuple:
    pg = Page("C_provenance.md", "C. Provenance",
              [rel(RECORD), rel(MANIFEST), "scripts/report_traceability.py"], s)
    rows, per = provenance_rows(s)
    n_ind = len(s.inds)
    located = sorted((c for c, v in per.items() if any(v["locs"].values())), key=code_key)
    no_edge = sorted((c for c, v in per.items() if not v["docs"]), key=code_key)
    edges_loc = sum(1 for r in rows if r[4] == "yes")
    not_in = [r for r in rows if r[2] == "not in manifest"]
    pg.add("# C. Provenance: indicator to source to locator", "",
           f"**Coverage, stated first.** {pg.n(len(located), 'indicators whose evidence cell carries a locator (report_traceability.locators)')} "
           f"of {pg.n(n_ind, 'AssessmentIndicator nodes in the record')} indicator evidence cells "
           "carry a pinpoint locator for at least one cited document. The test is "
           "`scripts/report_traceability.py::locators`, the same one the report's Locator "
           "column prints: a backticked doc id followed by a parenthetical. "
           f"{pg.n(edges_loc, 'EVIDENCED_BY edges whose document has a locator in the cell')} of "
           f"{pg.n(len(rows), 'EVIDENCED_BY edges in the record')} `EVIDENCED_BY` edges point at "
           "a document the cell locates. "
           f"{pg.n(len(no_edge), 'indicators with no EVIDENCED_BY edge')} indicators have no "
           "`EVIDENCED_BY` edge at all. The rest cite their sources as general support, with "
           "no place inside the source.",
           "",
           f"Indicators with a located cell: {', '.join(f'`{c}`' for c in located)}.",
           "",
           "**What `type` means here.** The manifest has no `source_type` field. Its field is "
           "`identity.doc_type`, with the values federal, academic, industry, standard, "
           "intergovernmental, practitioner and platform, so that is what this page prints. It "
           "does not split statute from OMB guidance, or a W3C recommendation from other "
           "standards. That split is not in the manifest, and this page does not guess it.",
           "")
    if not_in:
        pg.add(f"**Not in the manifest:** {pg.n(len(not_in), 'EVIDENCED_BY edges to doc ids absent from the manifest')} "
               "edges point at a doc id the manifest does not hold. They are listed in the CSV "
               "with type `not in manifest`.", "")
    pg.add("## Corpus documents per type", "",
           "Admitted means `screening.decision: included`. Cited means cited by at least one "
           "indicator's `EVIDENCED_BY` edge.", "")
    adm = Counter(v["identity"].get("doc_type") or "none recorded"
                  for v in s.manifest.values() if v["screening"]["decision"] == "included")
    cited_docs = {r[1] for r in rows}
    cit = Counter((s.manifest.get(d) or {}).get("identity", {}).get("doc_type") or
                  "not in manifest" for d in cited_docs)
    types = sorted(set(adm) | set(cit))
    pg.add(*table(["doc_type", "admitted", "cited by the framework"],
                  [[t, adm.get(t, 0), cit.get(t, 0)] for t in types] +
                  [["all", sum(adm.values()), sum(cit.values())]]))
    pg.add("", "## Federal policy instruments", "",
           "One row per instrument. A document matches when its doc id or title matches the "
           "instrument's pattern and it is admitted. `by edge` lists the indicators with an "
           "`EVIDENCED_BY` edge to a matched document. `by text only` lists the indicators "
           "whose evidence cell names the instrument but which have no such edge.", "")
    irows = instrument_rows(s)
    absent = [r[0] for r in irows if r[2] == "none admitted"]
    if absent:
        pg.add("No admitted document matches " + ", ".join(f"`{a}`" for a in absent) +
               ". Those rows are "
               "absences in this corpus. They are not claims about the instruments. The "
               "statistical-policy corpus is a separate graph (fss-policy-kg), and this page "
               "does not reach into it.", "")
    pg.add(*table(["instrument", "pattern", "admitted documents", "by edge", "by text only"],
                  irows))
    pg.add("", "## Per indicator", "",
           "One row per `EVIDENCED_BY` edge, in `C_provenance.csv` as well. Internal references "
           "(`EVIDENCED_BY_INTERNAL`) are listed after the table.", "")
    pg.add(*table(C_HEAD, rows))
    pg.add("", "### Internal references", "")
    pg.add(*table(["indicator", "internal references"],
                  [[c, v["internal"]] for c, v in sorted(per.items(), key=lambda kv: code_key(kv[0]))
                   if v["internal"]]))
    return pg, {"C_provenance.csv": csv_text(s, C_HEAD, rows)}


# ------------------------------------------------------------------------------ appendix

def leg_counts(s: Sources) -> dict:
    """`{leg: {matrix: Counter(verdict)}}` over the cycle of record's three matrices."""
    out = {}
    for stem, (path, m) in s.matrices().items():
        for row in m["rows"]:
            for leg, v in (row.get("verdicts") or {}).items():
                out.setdefault(leg, {}).setdefault(stem, Counter())[v] += 1
    return out


def page_indicator(s: Sources, n: dict, counts: dict) -> Page:
    from report_traceability import locators
    p = n["properties"]
    code = p["code"]
    pg = Page(f"appendix/indicator_{code}.md", "Appendix: per-indicator sheets",
              [rel(RECORD), rel(MANIFEST), "assessment/harness/scan/rules/__init__.py",
               "docs/reports/scan_matrix_*"], s)
    pg.add(f"# {code}: {p['indicator']}", "",
           f"Record node `{n['id']}`. Every value below is a field of that node or of an edge "
           "or node it reaches, printed verbatim.", "")
    rules = s.rule_for(code)
    pg.add(*table(["field", "value"], [
        ["criterion", p["criterion_code"]], ["construct", p["construct"]],
        ["type", p["type"]], ["access tier (`tier`)", p["tier"]],
        ["measurement tier", p.get("measurement_tier") or "unassigned"],
        ["measurement basis", p.get("measurement_basis")],
        ["measurement status", p.get("measurement_status")],
        ["status", p["status"]],
        ["candidate (DD-054)", "yes" if n["id"] in s.candidates else "no"],
        ["current rule", ", ".join(f"{leg}: {r}" for leg, r in rules) or "none"],
        ["gap", p.get("gap")],
    ]))
    specs = [s.nodes[e["to"]] for e in s.out_edges(n["id"], "MEASURED_BY")]
    pg.add("", "## Measurement spec", "")
    if specs:
        for sp in specs:
            pg.add(f"`{sp['id']}`", "")
            pg.add(*table(["field", "value"], sorted(sp["properties"].items())))
            pg.add("")
    else:
        pg.add("No `MEASURED_BY` edge in the record.", "")
    locs = locators(p.get("evidence_raw") or "")
    pg.add("## Evidence", "")
    docs = sorted(e["properties"]["doc_id"] for e in s.out_edges(n["id"], "EVIDENCED_BY"))
    pg.add(*table(["doc_id", "doc_type", "title", "locator (evidence cell)"],
                  [[d, (s.manifest.get(d) or {}).get("identity", {}).get("doc_type", "not in manifest"),
                    (s.manifest.get(d) or {}).get("identity", {}).get("title", ""),
                    locs.get(d) or "general support; no pinpoint"] for d in docs]))
    internal = [e["to"] for e in s.out_edges(n["id"], "EVIDENCED_BY_INTERNAL")]
    if internal:
        pg.add("", "Internal references: " + ", ".join(f"`{x}`" for x in internal) + ".")
    pg.add("", "Evidence cell, verbatim:", "", f"> {p.get('evidence_raw') or '(empty)'}", "")
    acts = [(e, s.nodes[e["from"]]) for e in s.in_edges(n["id"], "REMEDIATES")]
    pg.add("## Actions (prescriptions)", "")
    if acts:
        pg.add(*table(["action", "title", "outcome", "rule", "effort", "cost"],
                      [[a["id"], a["properties"].get("title"), e["properties"].get("outcome"),
                        e["properties"].get("rule_id"), a["properties"].get("effort_band"),
                        a["properties"].get("cost_band")]
                       for e, a in sorted(acts, key=lambda x: x[1]["id"])]))
    else:
        pg.add("No `REMEDIATES` edge reaches this indicator.")
    reqs = s.out_edges(n["id"], "REQUIRES")
    pg.add("", "## Requirements (what stands between it and a verdict)", "")
    if reqs:
        pg.add(*table(["requires", "kind", "closes", "route", "test"],
                      [[e["to"], s.nodes[e["to"]]["properties"].get("kind"),
                        e["properties"].get("closes"), e["properties"].get("route"),
                        e["properties"].get("test")]
                       for e in sorted(reqs, key=lambda e: e["to"])]))
    else:
        pg.add("No `REQUIRES` edge.")
    if p.get("requirement_none_reason"):
        pg.add("", f"> `requirement_none_reason`: {p['requirement_none_reason']}")
    pg.add("", f"## Verdicts on the cycle of record ({s.cycle})", "")
    rows = []
    for leg, _ in rules:
        for stem, c in sorted(counts.get(leg, {}).items()):
            rows.append([leg, stem] + [c.get(v, 0) for v in
                                       ("pass", "fail", "not_applicable", "error")] +
                        [sum(c.values())])
    if rows:
        pg.add(*table(["leg", "matrix", "pass", "fail", "not_applicable", "error", "cells"], rows))
    else:
        pg.add("No leg of this indicator is a column of the cycle of record's matrices.")
    rest = {k: v for k, v in p.items() if k in (
        "tier_note", "tier_source", "tier_rule", "tier_unassigned_reason", "not_measured_reason",
        "construct_restated", "withdrawn_from", "measured_by", "candidate_rationale",
        "frontier", "as_of", "measurement_level")}
    if rest:
        pg.add("", "## Other record fields", "")
        pg.add(*table(["field", "value"], sorted(rest.items())))
    return pg


def page_rules(s: Sources) -> Page:
    R = s.R
    pg = Page("appendix/rules.md", "Appendix: rule specs",
              ["assessment/harness/scan/rules/__init__.py", "assessment/harness/scan/rules/*.py"], s)
    current = set(R.CURRENT.values())
    cands = {m.RULE_ID for m in R.CANDIDATE_RULES}
    pg.add("# Rule registry", "",
           f"Every rule version ever shipped (`rules.REGISTRY`, {pg.n(len(R.REGISTRY), 'len(rules.REGISTRY)')} "
           f"versions), of which {pg.n(len(current), 'len(set(rules.CURRENT.values()))')} are current: "
           "the rule a new cycle judges with. Rules are pure functions from Observations to a "
           "Finding. A superseded version stays in the registry so that a stored Finding "
           "re-derives under its own rule id. `claim` and `measures` come from "
           "`rules.claim_of` and `rules.measures`. The summary is the first line of the "
           "module docstring.", "")
    rows = []
    for rid in sorted(R.REGISTRY, key=lambda r: (code_key(R.parse_rule_id(r)["indicator_code"]),
                                                  R.REGISTRY[r].LEG, int(r.rsplit("-v", 1)[1]))):
        m = R.REGISTRY[rid]
        doc = ((m.__doc__ or "").strip().splitlines() or [""])[0]
        rows.append([rid, m.LEG, R.parse_rule_id(rid)["indicator_code"],
                     "current" if rid in current else "superseded",
                     "candidate" if rid in cands else "", R.claim_of(rid), R.measures(rid),
                     f"`{rel(Path(m.__file__))}`", doc])
    pg.add(*table(["rule_id", "leg", "indicator", "state", "candidate", "claim", "measures",
                   "module", "summary"], rows))
    return pg


# ------------------------------------------------------------------------------ E

def mermaid(lines: list) -> list:
    return ["```mermaid", *lines, "```"]


def page_e(s: Sources) -> Page:
    H = REPO / "assessment" / "harness" / "scan"
    pg = Page("E_architecture.md", "E. Architecture",
              ["assessment/harness/scan/*.py", "scripts/build_projection.py",
               "scripts/load_framework_graph.py", "scripts/framework_writeback.py",
               "mcp/airkg_server.py", "seldon/seldon/core/dispatch.py", "CLAUDE.md",
               rel(DN003), "Neo4j (worked example)"], s)
    pg.add("# E. Architecture", "",
           "Four diagrams. Every box names the code it stands for, and the generator resolves "
           "each `file:line` against the code when it renders. A box whose code has moved "
           "stops the build, so no diagram here is drawn from memory. Each diagram is "
           "rendered by `mmdc` in `tests/test_brief_pack.py`.", "")
    # (a) operational
    import airkg_tools as T
    params = yaml.safe_load((H / "params.yaml").read_text(encoding="utf-8"))
    rps = params["manners"]["requests_per_second_per_host"]
    verbs = len(T.TOOL_ORDER)
    boxes_a = [
        ("site", "Agency site<br/>home, well-known, flagship surfaces", sym(H / "run.py", "targets")),
        ("fetch", f"Fetcher: identified UA, robots.txt first, {rps:g} req/s per host (params.yaml)", sym(H / "manners.py", "Fetcher")),
        ("robots", "robots_access: RFC 9309 decision per netloc", sym(H / "manners.py", "robots_access")),
        ("ua", "one declared User-Agent", sym(H / "params.yaml", "  user_agent:")),
        ("obs", "Observation + body sha256 in corpus/evidence/scan", sym(H / "model.py", "Observation")),
        ("rule", "rules.judge: versioned pure rule", sym(H / "rules" / "__init__.py", "judge")),
        ("fnd", "Finding: verdict + reason + rule_id", sym(H / "model.py", "Finding")),
        ("log", "events/cycle-&lt;cycle&gt;.jsonl (append-only)", sym(H / "publish.py", "write_events")),
        ("mat", "matrices + L0 Results", sym(REPO / "scripts" / "build_l0_matrices.py", "leg_results")),
        ("rep", "L0 report and PDF", sym(REPO / "scripts" / "build_l0_report.py", "build")),
        ("sitev", "site, CITATION.cff, zenodo", sym(REPO / "scripts" / "build_l0_site.py", "citation_cff")),
        ("mcp", f"MCP server ({verbs} read-only verbs, TOOL_ORDER)", sym(REPO / "mcp" / "airkg_server.py", "create_server")),
    ]
    lab = {k: f'{k}["{t}"]' for k, t, _ in boxes_a}
    pg.add("## (a) Operational view: from an agency site to a published verdict", "")
    pg.add(*mermaid(["flowchart LR",
                     f"  {lab['site']} --> {lab['fetch']}",
                     f"  {lab['ua']} -.-> fetch",
                     f"  {lab['robots']} -.-> fetch",
                     f"  fetch --> {lab['obs']}",
                     f"  obs --> {lab['rule']}",
                     f"  rule --> {lab['fnd']}",
                     f"  fnd --> {lab['log']}",
                     f"  log --> {lab['mat']}",
                     f"  mat --> {lab['rep']}",
                     f"  mat --> {lab['sitev']}",
                     f"  log --> {lab['mcp']}"]))
    pg.add("", "**How to read it.** Left to right is one cycle. The fetcher is the only part "
           "that touches the network. It sends one declared identity, reads robots.txt before "
           "anything else on a host, and keeps every response body under its sha256. Rules "
           "never fetch: they read Observations and return a Finding. The Findings go to the "
           "append-only log, and the matrices, the report, the site and the MCP are read from "
           "the log or from what it projects. Dotted arrows are configuration, not data.", "")
    pg.add(*table(["box", "code"], [[t.replace("<br/>", " "), f"`{loc}`"] for _, t, loc in boxes_a]))
    # (b) systems
    D = SELDON_REPO / "seldon" / "core" / "dispatch.py"
    boxes_b = [
        ("harness", "scan harness (run.py)", sym(H / "run.py", "run_cycle")),
        ("events", "event log shards events/*.jsonl", sym(REPO / "kg" / "eventlog.py", "def append")),
        ("proj", "build_projection.py: KG labels", sym(REPO / "scripts" / "build_projection.py", "build")),
        ("scanproj", "publish.py --project: Observation/Finding/Rule", sym(H / "publish.py", "project")),
        ("fwload", "load_framework_graph.py: framework labels", sym(REPO / "scripts" / "load_framework_graph.py", "load")),
        ("record", "framework/ai_readiness_framework.json", sym(REPO / "scripts" / "build_framework_graph.py", "main")),
        ("writer", "framework_writeback.save: the single writer", sym(REPO / "scripts" / "framework_writeback.py", "save")),
        ("neo", "Neo4j seldon-ai-readiness-kg", sym(REPO / "seldon.yaml", "database: seldon-ai-readiness-kg")),
        ("seldon", "Seldon artifact graph (seldon_events.jsonl)", sym(REPO / "seldon.yaml", "neo4j:")),
        ("disp", "standing dispatcher (seldon dispatch)", sym(D, "candidacy")),
        ("mcpb", "MCP server, read-only", sym(REPO / "mcp" / "airkg_server.py", "create_server")),
    ]
    lb = {k: f'{k}["{t}"]' for k, t, _ in boxes_b}
    pg.add("", "## (b) Systems view: processes, stores and the one owner of each layer", "")
    pg.add(*mermaid([
        "flowchart TB",
        "  subgraph repo_airkg[\"repo ai-readiness-kg\"]",
        f"    {lb['harness']} --> {lb['events']}",
        f"    {lb['writer']} --> {lb['record']}",
        "  end",
        "  subgraph owners[\"projection: one owner per layer\"]",
        f"    {lb['proj']}",
        f"    {lb['scanproj']}",
        f"    {lb['fwload']}",
        "  end",
        "  events --> proj",
        "  events --> scanproj",
        "  record --> fwload",
        f"  proj --> {lb['neo']}",
        "  scanproj --> neo",
        "  fwload --> neo",
        f"  {lb['seldon']} --> neo",
        "  subgraph repo_seldon[\"repo seldon\"]",
        f"    {lb['disp']}",
        "  end",
        "  disp -- launches a headless session per registered task --> repo_airkg",
        f"  neo --> {lb['mcpb']}",
        "  record --> mcpb",
    ]))
    own = line_of(REPO / "CLAUDE.md", "Each layer has exactly one owner")
    pg.add("", "**How to read it.** The two stores of record are the event log and the "
           "framework record. Neo4j is a projection of both and can be deleted and rebuilt. "
           "Each projected layer has exactly one writer. `build_projection.py` resets only the "
           "KG labels, `publish.py` owns Observation, Finding and Rule, and "
           "`load_framework_graph.py` owns the framework labels "
           f"(`CLAUDE.md:{own}`). The framework record itself has one writer, "
           "`framework_writeback.save`. Seldon's artifact graph lives in the same database "
           "under disjoint labels. The dispatcher is in the Seldon repository and launches one "
           "session per registered task. The MCP server reads the record and the projection "
           "and writes nothing.", "")
    pg.add(*table(["box", "code"], [[t, f"`{loc}`"] for _, t, loc in boxes_b]))
    # (c) one verdict, worked
    pg.add("", f"## (c) Data flow for one verdict: {DOGFOOD_BODY}, worked from the cycle of record", "")
    conc = s.score["bodies"][DOGFOOD_BODY]["concentration"]
    leg = conc["leg"]
    body = s.tools.get_body(DOGFOOD_BODY)
    row = next(l for l in body["legs"] if l["leg"] == leg)
    ev = row["evidence"][0]
    pg.add(f"The leg is `{leg}`, the one {DOGFOOD_BODY}'s rank rests on "
           "(`score.py` concentration, page G). Every value in the diagram is read from "
           "`get_body` and `get_evidence` against the projection.", "")
    def q(x):
        return str(x).replace('"', "'")
    pg.add(*mermaid([
        "flowchart LR",
        f'  u["{q(row["url"])}<br/>surface {q(row["surface"])}"] --> o["{q(ev["obs_id"])}<br/>collector {q(ev["collector"])}"]',
        f'  o --> b["body sha256 {q(ev["sha256"][:16])}…<br/>{q(ev["path"])}"]',
        f'  o --> r["{q(row["rule_id"])}"]',
        f'  r --> f["{q(row["finding_id"])}<br/>verdict {q(row["verdict"])}"]',
        f'  f --> m["{q(row["matrix"])}<br/>cell {DOGFOOD_BODY}/{leg}"]',
    ]))
    pg.add("", "**How to read it.** The URL was fetched once. The Observation carries the "
           "response body's digest, and the body sits under that digest in the evidence store. "
           "The rule read the Observation and produced the Finding, and the matrix cell names "
           "the Finding. A reader can re-hash the stored body and re-run the rule "
           "(`assessment/harness/scan/rederive.py`) without touching the network.", "")
    pg.add(*table(["field", "value"], [
        ["url", row["url"]], ["surface", row["surface"]], ["observation", ev["obs_id"]],
        ["observations on the Finding", len(row["evidence"])],
        ["captured_at", ev["captured_at"]], ["sha256", ev["sha256"]],
        ["retained body", ev["path"]], ["sha256 verified", ev["sha256_verified"]],
        ["rule", row["rule_id"]], ["finding", row["finding_id"]], ["verdict", row["verdict"]],
        ["reason", row["reason"]], ["matrix", row["matrix"]]]))
    # (d) judgement generations
    chain = s.gread(
        "MATCH p=(f:Finding {finding_id:$id})-[:SUPERSEDES*0..]->(x:Finding) "
        "RETURN x.finding_id AS id, x.cycle AS cycle, x.generation AS generation, "
        "x.verdict AS verdict, x.rule_id AS rule ORDER BY length(p)", id=row["finding_id"])
    from scan import publish as PB
    pg.add("", "## (d) Judgement generations: re-judgement without re-fetch (DN-003)", "")
    lines = ["flowchart RL"]
    for i, c in enumerate(chain):
        cy = c["cycle"] or "(no cycle property on the node)"
        lines.append(f'  g{i}["{q(c["id"])}<br/>{q(cy)} gen {c["generation"]}<br/>'
                     f'{q(c["rule"])}: {q(c["verdict"])}"]')
        if i:
            lines.append(f"  g{i-1} -- SUPERSEDES --> g{i}")
    lines.append(f'  obs["Observations of the source cycle<br/>{q(ev["obs_id"])}"]')
    lines.append(f"  obs -. SUPPORTS every generation .-> g0")
    lines.append(f"  obs -.-> g{len(chain)-1}")
    pg.add(*mermaid(lines))
    d1 = line_of(DN003, "A re-judgement creates no evidence")
    pg.add("", "**How to read it.** A re-judgement runs the current rules over Observations "
           "already on the log and fetches nothing. Its Findings cite the source cycle's "
           f"`obs_id`s and `SUPERSEDES` their predecessors one to one (`{rel(DN003)}:{d1}`). "
           "A Finding with no successor is current. The published report points at the "
           "current generation of its snapshot cycle, which is why the report can move to a "
           "new judgement without a new scan.", "")
    pg.add(f"> `{rel(DN003)}:{d1}` {DN003.read_text(encoding='utf-8').splitlines()[d1-1].strip()}", "")
    gens = [[c, PB.generation(c), PB.supersedes_of(c) or "none",
             PB.shard_name(PB.shard_for(c))] for c in
            [x["cycle"] for x in chain if x["cycle"]]]
    pg.add(*table(["cycle", "publish.generation", "publish.supersedes_of", "shard"], gens))
    pg.add("", "Code: " + ", ".join(f"`{x}`" for x in (
        sym(H / "rederive.py", "rejudge"), sym(H / "publish.py", "generation"),
        sym(H / "publish.py", "supersedes_of"), sym(H / "publish.py", "write_supersession"))) + ".")
    return pg


# ------------------------------------------------------------------------------ D

#: The runbook. Each step's `source_text` must appear VERBATIM in `source` (the test checks);
#: `run` is what was executed, and `substitution` says in words how it differs from the source.
DEMO_STEPS = [
    {"id": "neo4j", "title": "Neo4j is up and the framework projection is current",
     "source": "CLAUDE.md",
     "source_text": "python -m pytest tests/test_framework_projection_roundtrip.py",
     "run": f"{PY} -m pytest tests/test_framework_projection_roundtrip.py -q",
     "substitution": "this machine's interpreter; `-q`. No file in the repository documents a "
                     "command that STARTS Neo4j; on this machine the DBMS runs under Neo4j "
                     "Desktop, and this step is the check that it is up and current."},
    {"id": "seldon_go", "title": "Orient: `seldon go`", "source": "CLAUDE.md",
     "source_text": "seldon go --brief", "run": "seldon go --brief",
     "substitution": "none (no handoff path given, so it opens on the newest)"},
    {"id": "report", "title": "Open the report", "source": "docs/adopt/run_on_your_site.md",
     "source_text": "cat \"out/my-site/report/$(cat out/my-site/LATEST).md\"",
     "run": "cat docs/reports/2026-09_fss_ai_readiness_L0.md",
     "substitution": "the project's published report in place of an adopter run's; the PDF "
                     "beside it is `docs/reports/2026-09_fss_ai_readiness_L0.pdf`"},
    {"id": "score", "title": "Score one body", "source": "scripts/score.py",
     "source_text": "scripts/score.py --body NCHS",
     "run": f"{PY} scripts/score.py --body CENSUS", "substitution": "NCHS -> CENSUS"},
    {"id": "get_body", "title": "MCP verb `get_body`, in-process",
     "source": "docs/adopt/run_on_your_site.md",
     "source_text": "\"$PY\" -c 'import sys; sys.path.insert(0, \"mcp\"); import airkg_tools as T; print(T.Tools(graph=None, run=\"out/my-site\").get_body(\"MYSITE\")[\"summary\"])'",
     "run": f"{PY} -c 'import sys; sys.path.insert(0, \"mcp\"); import airkg_tools as T; print(T.Tools(graph=None).get_body(\"CENSUS\")[\"summary\"])'",
     "substitution": "`run=` dropped (the project's published tree), MYSITE -> CENSUS"},
    {"id": "get_prescriptions", "title": "MCP verb `get_prescriptions`, in-process",
     "source": "docs/adopt/run_on_your_site.md",
     "source_text": "\"$PY\" -c 'import sys; sys.path.insert(0, \"mcp\"); import airkg_tools as T; print(T.Tools(graph=None, run=\"out/my-site\").get_body(\"MYSITE\")[\"summary\"])'",
     "run": f"{PY} -c 'import sys; sys.path.insert(0, \"mcp\"); import airkg_tools as T; a = T.Tools(graph=None).get_prescriptions(body=\"CENSUS\"); print(a[\"failing_legs\"]); print([x[\"title\"] for x in a[\"actions\"][:5]])'",
     "substitution": "the same template, verb `get_prescriptions(body=\"CENSUS\")`, printing "
                     "the failing legs and the first five actions"},
    {"id": "get_requirements", "title": "MCP verb `get_requirements`, in-process",
     "source": "docs/adopt/run_on_your_site.md",
     "source_text": "\"$PY\" -c 'import sys; sys.path.insert(0, \"mcp\"); import airkg_tools as T; print(T.Tools(graph=None, run=\"out/my-site\").get_body(\"MYSITE\")[\"summary\"])'",
     "run": f"{PY} -c 'import sys; sys.path.insert(0, \"mcp\"); import airkg_tools as T; print(T.Tools(graph=None).get_requirements(body=\"CENSUS\")[\"summary\"])'",
     "substitution": "the same template, verb `get_requirements(body=\"CENSUS\")`"},
    {"id": "mcp_server", "title": "Start the MCP server (stdio)",
     "source": "docs/design/mcp_over_the_graph.md",
     "source_text": "/opt/anaconda3/bin/python3 mcp/airkg_server.py --no-graph",
     "run": f"{PY} mcp/airkg_server.py --no-graph < /dev/null",
     "substitution": "stdin closed, so the stdio server sees end-of-input at once; in a demo "
                     "the client (Claude Desktop) holds stdin open",
     "timeout": SERVER_TIMEOUT},
    {"id": "spot_render", "title": "Request a live spot scan of one body (render only)",
     "source": "cc_tasks/2026-09-19_spot_scan_RESULT.md",
     "source_text": "scripts/render_spot_scan.py --target BEA",
     "run": f"{PY} scripts/render_spot_scan.py --target CENSUS",
     "substitution": "BEA -> CENSUS; without `--write`, so no task file is created and no "
                     "host is contacted"},
    {"id": "spot_loopback", "title": "A spot scan end to end against the loopback fixtures",
     "source": "cc_tasks/2026-09-19_spot_scan_RESULT.md",
     "source_text": "tests/test_spot_scan.py -k loopback",
     "run": f"{PY} -m pytest tests/test_spot_scan.py -k loopback -q",
     "substitution": "this machine's interpreter; `-q`. Every URL is 127.0.0.1; no federal host"},
    {"id": "second_agency", "title": "How a second agency runs it: the adopter runbook, executed",
     "source": "docs/adopt/run_on_your_site.md",
     "source_text": "tests/test_adopter_path.py::test_the_runbook_runs_as_written",
     "run": f"{PY} -m pytest tests/test_adopter_path.py::test_the_runbook_runs_as_written -q",
     "substitution": "none; the test runs every bash block of the adopter page in a scratch "
                     "copy of the tree against a loopback \"site\""},
]


def capture_demo() -> int:
    """Execute every runbook step once and store what it printed. The one mode that runs
    commands, and the only writer of `D_demo_capture.json`."""
    from datetime import datetime, timezone
    out = {"task": TASK, "head": git_out("rev-parse", "HEAD"), "steps": []}
    for st in DEMO_STEPS:
        src = (REPO / st["source"]).read_text(encoding="utf-8")
        if st["source_text"] not in src:
            raise SystemExit(f"FATAL: step {st['id']}: {st['source']} does not contain "
                             f"{st['source_text']!r}")
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(f"[capture] {st['id']}: {st['run']}", flush=True)
        try:
            r = subprocess.run(["bash", "-c", st["run"]], cwd=REPO, capture_output=True,
                               text=True, timeout=st.get("timeout", COMMAND_TIMEOUT))
            rc, text = r.returncode, (r.stdout + r.stderr)
        except subprocess.TimeoutExpired as exc:
            rc = "timeout"
            text = ((exc.stdout or b"").decode() if isinstance(exc.stdout, bytes)
                    else (exc.stdout or "")) + f"\n[timed out after {exc.timeout} s]"
        lines = text.rstrip("\n").splitlines()
        out["steps"].append({"id": st["id"], "run": st["run"], "exit": rc,
                             "started_at": started, "lines_total": len(lines),
                             "head": lines[:HEAD_LINES],
                             "tail": lines[HEAD_LINES:][-TAIL_LINES:]})
        print(f"[capture] {st['id']}: exit {rc}, {len(lines)} lines", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    CAPTURE.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[capture] wrote {rel(CAPTURE)}")
    return 0


def page_d(s: Sources) -> Page:
    pg = Page("D_demo_runbook.md", "D. Using it: the offline demo",
              [rel(CAPTURE), "docs/adopt/run_on_your_site.md", "docs/design/mcp_over_the_graph.md",
               "cc_tasks/2026-09-19_spot_scan_RESULT.md", "CLAUDE.md", "scripts/score.py"], s)
    if not CAPTURE.is_file():
        raise SystemExit(f"FATAL: {rel(CAPTURE)} does not exist; run --capture-demo first")
    cap = load_json(CAPTURE)
    by_id = {x["id"]: x for x in cap["steps"]}
    failed = [x["id"] for x in cap["steps"] if x["exit"] != 0]
    pg.add("# D. The offline demo, from this machine", "",
           "Each command is copied from a file that already documents it. The source file "
           "and the exact source text are named under each step, and so is any substitution. "
           f"Every command was executed once, by `{GENERATOR} --capture-demo` at commit "
           f"`{cap['head'][:12]}`, and the lines it printed are pasted under it: the first "
           "lines, then the last lines when there were more. A command that failed is left in "
           "with its failure and a note.", "",
           f"Failed steps: {', '.join(f'`{f}`' for f in failed) if failed else 'none'}.", "")
    for i, st in enumerate(DEMO_STEPS, 1):
        c = by_id.get(st["id"])
        pg.add(f"## Step {st['id']}: {st['title']}", "",
               f"Source: `{st['source']}`, which documents `{st['source_text']}`.",
               f"Substitution: {st['substitution'].rstrip('.')}.", "",
               "```bash", st["run"], "```", "")
        if c is None:
            pg.add("**Not captured.** The step was added after the capture; re-run "
                   "`--capture-demo`.", "")
            continue
        if c["run"] != st["run"]:
            pg.add("**The captured command differs from this step's command.** Re-run "
                   "`--capture-demo`.", "")
        pg.add(f"Output (exit `{c['exit']}`, `{c['lines_total']}` lines, run at "
               f"`{c['started_at']}`):", "", "```text", *c["head"])
        if c["tail"]:
            pg.add("[…]", *c["tail"])
        pg.add("```", "")
        if c["exit"] != 0:
            pg.add(f"**Note.** This command exited `{c['exit']}`. It is left in as it ran; "
                   "see the RESULT of the task that captured it.", "")
    return pg


# ------------------------------------------------------------------------------ G

def page_g(s: Sources) -> Page:
    pg = Page("G_census_dogfood.md", "G. Census dogfood",
              ["mcp/airkg_tools.py::get_body", "mcp/airkg_tools.py::get_requirements",
               "scripts/score.py", rel(DN007)], s)
    b = s.tools.get_body(DOGFOOD_BODY)
    sc = s.score
    bs = sc["bodies"][DOGFOOD_BODY]
    cov = sc["coverage"]
    conc = b["score"]["concentration"]
    pg.add(f"# G. census.gov on the cycle of record ({b['cycle']})", "",
           "No new fetch. This is the published cycle read back through `get_body`, "
           "`get_requirements` and `scripts/score.py`.", "",
           f"> `get_body` summary: {b['summary']}", "",
           "## Score", "",
           f"Hierarchical score {pg.n(b['score']['score'], 'get_body score.score')}, rank "
           f"{pg.n(b['score']['rank'], 'get_body score.rank')} of "
           f"{pg.n(b['score']['of'], 'get_body score.of')}. Flat score "
           f"{pg.n(b['score']['flat'], 'get_body score.flat')}, rank "
           f"{pg.n(b['score']['flat_rank'], 'get_body score.flat_rank')}. Both schemes use "
           "equal weights, and neither has a basis over the other, so both are printed. "
           f"Coverage: {pg.n(cov['indicators']['measured'], 'score.py coverage.indicators.measured')} of "
           f"{pg.n(cov['indicators']['total'], 'score.py coverage.indicators.total')} framework "
           f"indicators and {pg.n(cov['criteria']['measured'], 'score.py coverage.criteria.measured')} of "
           f"{pg.n(cov['criteria']['total'], 'score.py coverage.criteria.total')} criteria are "
           "measured. Tier O and D indicators are not scored.", "")
    n = line_of(DN007, "one-leg criterion")
    pg.add("**The one-leg-criterion caveat.** The rank rests on a single leg: "
           f"`{conc['leg']}` "
           f"({pg.n(conc['pass'], 'concentration.pass')} pass of "
           f"{pg.n(conc['judged'], 'concentration.judged')} judged). Were that verdict "
           f"reversed, the body would rank {pg.n(conc['rank_if_reversed'], 'concentration.rank_if_reversed')}. "
           f"DN-007 §2 states this for every body on the cycle (`{rel(DN007)}:{n}`):", "",
           f"> {DN007.read_text(encoding='utf-8').splitlines()[n-1].lstrip('- ').strip()}", "")
    crit = bs.get("criteria") or {}
    if crit:
        pg.add("Criterion scores (`score.py`, hierarchical):", "")
        pg.add(*table(["criterion", "score"],
                      [[k, "not measured" if v.get("score") is None else round(v["score"], 3)]
                       for k, v in sorted(crit.items())]))
        pg.add("")
    pg.add("## Every judged leg", "",
           "One row per judged cell: its surface, verdict and reason, and the Finding and "
           "rule behind it. From `get_body` against the projection.", "")
    pg.add(*table(["leg", "surface", "verdict", "reason", "rule", "finding"],
                  [[l["leg"], l["surface"], l["verdict"], l["reason"], l["rule_id"],
                    l["finding_id"]] for l in b["legs"]]))
    pg.add("", "## What to do first: prescriptions, ranked", "",
           "This is `score.py`'s prescription join for the body. Actions on the body's "
           "failing legs are ordered cheapest effort band first, then by how much each would "
           "add to the score. The bands are notional (page H). `delta` is an upper bound: it "
           "assumes every failing row on that leg passes.", "")
    join = bs.get("prescriptions") or []
    if join:
        keys = [k for k in ("effort", "cost", "delta", "leg", "title", "action") if k in join[0]]
        pg.add(*table(keys, [[a.get(k) if not isinstance(a.get(k), float) else round(a[k], 3)
                              for k in keys] for a in join]))
    else:
        pg.add("`score.py` carries no prescription join for this body in `--json` form; see "
               "step `score` of the runbook (page D) for the printed join.")
    req = s.tools.get_requirements(body=DOGFOOD_BODY)
    pg.add("", "## What the harness cannot measure, and what would unlock it", "",
           f"> `get_requirements` summary: {req['summary']}", "")
    rows = []
    for r in req.get("by_requirement") or []:
        rows.append([r["id"], r.get("name"), r.get("kind"), r.get("who_provides"),
                     r.get("cost") or "pending",
                     [f"{x.get('indicator')}: {x.get('clause') or x.get('what')}"
                      for x in r.get("unlocks") or []]])
    if rows:
        pg.add(*table(["requirement", "name", "kind", "who provides", "cost (notional)",
                       "unlocks"], rows))
    nr = req.get("no_requirement") or []
    if nr:
        pg.add("", "Unobserved with no requirement recorded:", "")
        pg.add(*table(["indicator", "what", "reason"],
                      [[x.get("indicator"), x.get("what"), x.get("reason")] for x in nr]))
    pg.add("", f"> band note: {req.get('band_note', '')}")
    return pg


# ------------------------------------------------------------------------------ F

def tagged_results(path: Path) -> list:
    return sorted(set(re.findall(r"\{\{result:([A-Za-z0-9_.-]+):", path.read_text(encoding="utf-8"))))


def page_f(s: Sources) -> Page:
    pg = Page("F_results_pointer.md", "F. Results",
              [rel(PUBLICATION), rel(FRAME_SECTION), "Neo4j (Seldon Result artifacts)"], s)
    pub = s.publication
    ver = pub["version"]
    mats = sorted(p.name for p in (REPO / "docs" / "reports").glob(f"scan_matrix_*_{ver}.*"))
    pg.add("# F. Where the results live", "",
           "Pointers only. No number is re-typed here: each Result is named with its id, "
           "and its value is on the graph and in the report.", "")
    pg.add(*table(["what", "where"], [
        ["title", pub["title"]], ["version", ver], ["released", pub["released"][ver]],
        ["cycle of record", pub["snapshot_cycle"]],
        ["report (markdown)", "`docs/reports/2026-09_fss_ai_readiness_L0.md`"],
        ["report (PDF)", "`docs/reports/2026-09_fss_ai_readiness_L0.pdf`"],
        ["site", f"`docs/index.html`, served at {pub['site_url']} (whether it IS served is a "
                 "repository setting, `docs/reports/publication.yaml`)"],
        ["matrices", ", ".join(f"`docs/reports/{m}`" for m in mats)],
        ["citation files", "`CITATION.cff`, `.zenodo.json`"],
        ["repository", pub["repository_url"]],
    ]))
    names = tagged_results(FRAME_SECTION)
    rows = []
    for name in names:
        hits = s.gread("MATCH (a:Artifact:Result {name:$n}) RETURN a.artifact_id AS id, "
                       "a.state AS state ORDER BY a.artifact_id", n=name)
        rows.append([name, [h["id"] for h in hits] or "not on the graph",
                     [h["state"] for h in hits]])
    pg.add("", "## Headline Results", "",
           f"The headline Results are the ones the report's opening section quotes "
           f"(`{rel(FRAME_SECTION)}`, {pg.n(len(names), 'distinct {{result:}} names in 10_frame.md')} "
           "names), each looked up on the Seldon graph by name.", "")
    pg.add(*table(["Result", "artifact id", "state"], rows))
    return pg


# ------------------------------------------------------------------------------ H

def page_h(s: Sources, c_located: int) -> Page:
    pg = Page("H_limits.md", "H. Limits and roadmap",
              [rel(RECORD), "scripts/score.py", "scripts/report_traceability.py",
               "Neo4j (ResearchTasks 8a9a89d7, bb46ddb5)"], s)
    inds = [n["properties"] for n in s.inds]
    tiers = Counter(p.get("measurement_tier") or "unassigned" for p in inds)
    fw = [n["properties"] for n in s.inds if n["id"] not in s.candidates]
    tiers_fw = Counter(p.get("measurement_tier") or "unassigned" for p in fw)
    ms = Counter(p["measurement_status"] for p in fw)
    pg.add("# H. Limits and roadmap", "",
           "Only the open items the record and the graph already state. Nothing here is a "
           "new finding.", "", "## Measurement tiers", "")
    pg.add(*table(["measurement tier", "all indicator nodes", "framework (candidate excluded)"],
                  [[t, tiers.get(t, 0), tiers_fw.get(t, 0)] for t in ("M", "O", "D", "unassigned")] +
                  [["all", sum(tiers.values()), sum(tiers_fw.values())]]))
    pg.add("", "Measurement status of the framework's indicators (record "
           "`measurement_status`):", "")
    pg.add(*table(["status", "indicators"], sorted(ms.items())))
    pg.add("", "## Indicators the record does not mark measured, and why", "",
           "Every framework indicator whose record `measurement_status` is not `measured`, "
           "with its `requirement_none_reason` or `tier_unassigned_reason` where the record "
           "has one. The requirements that would unlock the rest are on each appendix sheet. "
           "The last column is read from the cycle of record's matrices instead of the "
           "record. Where it says `yes`, the record's `measurement_status` lags the cycle, "
           "which judges the leg anyway. That is a recorded discrepancy, and this page does "
           "not correct it.", "")
    judged = set(leg_counts(s))
    rows = [[p["code"], p["measurement_status"], p.get("measurement_tier") or "unassigned",
             p.get("requirement_none_reason") or p.get("tier_unassigned_reason") or "",
             "yes" if any(leg in judged for leg, _ in s.rule_for(p["code"])) else "no"]
            for p in fw if p["measurement_status"] != "measured"]
    pg.add(*table(["indicator", "status", "tier", "reason (record)",
                   "judged on the cycle of record"], rows))
    pg.add("", "## Evidence-cell locators", "",
           f"{pg.n(c_located, 'indicators with a located evidence cell (page C)')} of "
           f"{pg.n(len(inds), 'AssessmentIndicator nodes')} evidence cells carry a pinpoint "
           "locator (page C). ResearchTask `93d28c6e` holds the rest, and it is not scheduled.", "")
    sc = s.score
    pg.add("## Equal weights, and every rank rests on one leg", "",
           "Both scoring schemes weight equally, following the OECD/JRC Handbook default for "
           "when no basis exists for other weights (`docs/design/scoring_model.md`). With "
           "equal weights and sparse passes, each body's rank rests on a single leg. The "
           "concentration sentence for every scored body:", "")
    pg.add(*table(["body", "leg", "sentence (score.py)"],
                  [[b, v["concentration"]["leg"], v["concentration"]["sentence"]]
                   for b, v in sorted(sc["bodies"].items()) if v.get("concentration")]))
    fut = s.gread("MATCH (a:Artifact:ResearchTask) WHERE a.artifact_id STARTS WITH '8a9a89d7' "
                  "OR a.artifact_id STARTS WITH 'bb46ddb5' RETURN a.artifact_id AS id, "
                  "a.state AS state, a.description AS d ORDER BY a.artifact_id DESC")
    pg.add("", "## Roadmap items already on the graph", "")
    for r in fut:
        pg.add(f"* `{r['id'][:8]}` ({r['state']}):", "", f"  > {r['d']}", "")
    return pg


# ------------------------------------------------------------------------------ INDEX

def page_index(s: Sources, pages: list, extra: dict) -> Page:
    pg = Page("INDEX.md", "Index", [GENERATOR], s)
    pg.add("# The brief's material pack: where everything is", "",
           f"Every file under `docs/brief/` is written by `{GENERATOR}` "
           f"(`{TASK}`) and by nothing else. `--check` re-renders the pack and compares it byte "
           "for byte. The numbers each page states in prose are on `numbers.json`, with the "
           "source of each.", "")
    rows = []
    for p in pages:
        if p.name.startswith("appendix/indicator_"):
            continue
        rows.append([f"`{p.name}`", p.chapter, [f"`{x}`" for x in p.sources]])
    ind = [p for p in pages if p.name.startswith("appendix/indicator_")]
    rows.append([f"`appendix/indicator_<CODE>.md` ({pg.n(len(ind), 'indicator sheets written')} files)",
                 "Appendix: per-indicator sheets", [f"`{x}`" for x in ind[0].sources] if ind else ""])
    for name in sorted(extra):
        rows.append([f"`{name}`", "data beside its page", "the page of the same stem"])
    rows.append(["`D_demo_capture.json`", "D, captured command output",
                 f"`{GENERATOR} --capture-demo`"])
    rows.append(["`numbers.json`", "the prose-number ledger", "every page"])
    pg.add(*table(["file", "chapter", "generated from"], rows))
    pg.add("", "Chapter A (what it is and why) has no file here. Its one page is authored in "
           "the deck from `docs/design/2026-09-15_DN-005_reorientation_the_framework_is_the_goal.md`.")
    return pg


# ------------------------------------------------------------------------------ render

def render(graph) -> dict:
    """`{relative path: text}` for every pack file. `graph=None` renders the graph-free pages."""
    s = Sources(graph)
    pages, extra = [], {}
    b, bx = page_b(s)
    c, cx = page_c(s)
    pages += [b, c]
    extra.update(bx)
    extra.update(cx)
    counts = leg_counts(s)
    pages += [page_indicator(s, n, counts) for n in s.inds]
    pages.append(page_rules(s))
    pages.append(page_d(s))
    if graph is not None:
        located = sum(1 for n in s.inds if any(
            __import__("report_traceability").locators(n["properties"].get("evidence_raw") or "").values()))
        pages += [page_e(s), page_f(s), page_g(s), page_h(s, located)]
        pages.append(page_index(s, pages, extra))
    out = {p.name: p.text() for p in pages}
    out.update(extra)
    if graph is not None:
        ledger = {p.name: p.nums for p in pages if p.nums}
        out["numbers.json"] = json.dumps(ledger, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    return out


def graph_or_none(required: bool):
    import airkg_tools as T
    g = T.Graph()
    if g.available():
        return g
    if required:
        raise SystemExit(f"FATAL: Neo4j unreachable ({g.error}); the pages {GRAPH_PAGES} read "
                         f"Finding reasons, digests and Results from the projection. Start the "
                         f"DBMS or pass --no-graph with --check.")
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-graph", action="store_true")
    ap.add_argument("--capture-demo", action="store_true")
    a = ap.parse_args(argv)
    if a.capture_demo:
        return capture_demo()
    if a.no_graph and not a.check:
        raise SystemExit("REFUSING: --no-graph writes an incomplete pack; use it with --check")
    graph = None if a.no_graph else graph_or_none(required=True)
    files = render(graph)
    if a.check:
        drift = [k for k, v in sorted(files.items())
                 if not (OUT / k).is_file() or (OUT / k).read_text(encoding="utf-8") != v]
        if graph is not None:
            on_disk = {rel(p)[len("docs/brief/"):] for p in OUT.rglob("*") if p.is_file()}
            stray = sorted(on_disk - set(files) - {CAPTURE.name})
            drift += [f"{x} (on disk, not generated)" for x in stray]
        for d in drift:
            print(f"DRIFT {d}")
        print(f"{len(files)} files checked, {len(drift)} drifted")
        return 1 if drift else 0
    for k, v in files.items():
        p = OUT / k
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.is_file() or p.read_text(encoding="utf-8") != v:
            p.write_text(v, encoding="utf-8")
    print(f"wrote {len(files)} files under {rel(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
