#!/usr/bin/env python3
"""Build the published tree: the data first, the index over it, the PDF as a view.

`cc_tasks/2026-09-12_publish_l0.md` decisions 1, 2, 4 and 5, under DN-002.
**Zero model spend, zero network.**

**Machine-first.** What publishes is the data — the matrices as JSON and CSV, the per-check
source appendix, every registered Result the report quotes with its state and provenance, the
framework record and the corpus manifest. The built markdown and the PDF are views of those
and are linked last. The index says so in one sentence, because a reader who meets the PDF
first will otherwise take the PDF for the product.

**One site, not a second one.** The tree is `docs/`, which is where the framework progress page
already lives (`docs/progress/index.html`) and what GitHub Pages serves when its source is set
to the default branch's `/docs` folder. This script writes the index at the tree's root; it
changes no repository setting and never could — it has no credential and makes no API call.

**Copies are hashed, not trusted.** Two canonical records live outside the served tree
(`framework/ai_readiness_framework.json`, `corpus/manifest.json`) and two citation files are
canonical at the repository root, where GitHub and Zenodo read them. A link on the site has to
resolve on the site, so each is copied into `docs/data/` — and every copy's sha256 and its
source path are written into `docs/data/index.json`, so a copy that has drifted from its
source is a test failure (`tests/test_publication.py`) rather than a silent stale file.

**The self row is measured or it is absent, never assumed.** Decision 2 has the six tier-0
legs run against the published host with the identified client. That needs a live host. When
`state/self_l0_<cycle>.json` exists this script renders its six verdicts; when it does not,
the index says in words that the row is not measured and why. It never renders a placeholder
verdict: a site publishing an AI-readiness instrument with an invented row about itself would
be the exact failure the instrument exists to find.

    /opt/anaconda3/bin/python3 scripts/build_l0_site.py [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, "/Users/brock/GitHub/seldon")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

TASK = "cc_tasks/2026-09-12_publish_l0.md"

SITE = REPO / "docs"
DATA = SITE / "data"
REPORTS = SITE / "reports"
PUBLICATION = REPORTS / "publication.yaml"

STEM = "2026-09_fss_ai_readiness_L0"

#: Canonical files that live outside the served tree and are copied into it so the index's
#: links resolve on the host. (published name, source path, what it is)
COPIES = [
    ("ai_readiness_framework.json", "framework/ai_readiness_framework.json",
     "The framework record: indicators, constructs, measurement specs and the evidence cells "
     "the source appendix reads its locators from."),
    ("corpus_manifest.json", "corpus/manifest.json",
     "The corpus manifest: every admitted document with its identity, its source URL and its "
     "content hash. Every doc_id in the source appendix is a key in this file."),
]

#: The citation files, which are generated rather than copied: one string, written to the
#: repository root where GitHub and Zenodo read it AND into the served tree where the index
#: links it. Two writes of one string cannot drift; a copy of a file can, which is why the
#: records above are hashed and these are not.
CITATION_FILES = [
    ("CITATION.cff", "CITATION.cff",
     "Citation metadata in Citation File Format."),
    ("zenodo.json", ".zenodo.json",
     "Zenodo deposition metadata, prepared and not deposited: the mint is the author's."),
]

#: The matrices, in the order the index lists them. `{suffix}` is the snapshot cycle's suffix.
MATRICES = [("tierA", "The 16 Tier A bodies × the six host-level checks."),
            ("tierC", "The three federal reference hosts, in no Tier A denominator (DD-059)."),
            ("product", "PARTIAL: product-level checks over declared flagship surfaces only.")]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publication() -> dict:
    import yaml
    doc = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))
    for k in ("snapshot_cycle", "title", "version", "authors", "site_url", "repository_url"):
        if not doc.get(k):
            raise SystemExit(f"FATAL: {PUBLICATION.name} declares no {k!r}")
    return doc


def cycle_suffix(cycle: str) -> str:
    import cycle_results
    return cycle_results.cycle_suffix(cycle)


def head_commit() -> str:
    r = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], capture_output=True,
                       text=True, cwd=REPO)
    if r.returncode:
        raise SystemExit(f"FATAL: cannot read HEAD: {r.stderr.strip()[-200:]}")
    return r.stdout.strip()


# --------------------------------------------------------------- the data the index links

def _with_presence(ref: dict) -> dict:
    """A provenance reference, plus whether the repository actually holds the path it names.

    Stated rather than assumed, because four of the published Results are `COMPUTED_FROM`
    `scan_matrix_2026-09-10`, whose registered path the repository deliberately does NOT hold:
    that cycle was measured and never reported, and its absence is what
    `tests/test_scan_figures.py` skips the figure suite on
    (`cc_tasks/2026-09-10_harness_v5_blind.md` decision 6). A reader following the chain will
    find nothing there, and the honest thing is for the published record to say so on the row
    rather than let them discover it as a broken link. The registry defect it exposes —
    a DataFile naming a path nothing writes — is recorded in
    `cc_tasks/2026-09-12_publish_l0_RESULT.md`, not patched here.
    """
    path = ref.get("path")
    return {**ref, "present_in_repository": bool(path) and (REPO / path).exists()}


def tagged_results() -> list:
    """Every Result the report quotes, with its value, its state and what produced it.

    The set is read from the report's own `{{result:...}}` tags, never typed, so it cannot
    disagree with the document it documents.
    """
    import rederive_tagged_results as rd
    from seldon.config import get_neo4j_driver, load_project_config
    names = rd.tagged_names()
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    out = []
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            for n in names:
                rows = s.run(
                    "MATCH (r:Result {name: $n}) WHERE r.state <> 'superseded' "
                    "OPTIONAL MATCH (r)-[:COMPUTED_FROM]->(d:DataFile) "
                    "OPTIONAL MATCH (r)-[:GENERATED_BY]->(sc:Script) "
                    "RETURN r.artifact_id AS artifact_id, r.state AS state, r.value AS value, "
                    "       r.description AS description, "
                    "       collect(DISTINCT {name: d.name, path: d.path}) AS computed_from, "
                    "       collect(DISTINCT {name: sc.name, path: sc.path}) AS generated_by",
                    n=n).data()
                if len(rows) != 1:
                    raise SystemExit(f"FATAL: {n!r} resolves to {len(rows)} live Results")
                r = rows[0]
                out.append({
                    "name": n, "value": r["value"], "state": r["state"],
                    "artifact_id": r["artifact_id"], "description": r["description"],
                    "computed_from": [_with_presence(x) for x in r["computed_from"]
                                      if x.get("name")],
                    "generated_by": [_with_presence(x) for x in r["generated_by"]
                                     if x.get("name")]})
    finally:
        driver.close()
    return out


def sources_per_check() -> dict:
    """The per-check source appendix as data: one row per (check, admitted source).

    Built from the same `report_traceability.sources_appendix` the report's markdown fragment
    is built from, so the JSON and the printed appendix are one measurement rendered twice.
    """
    import report_traceability
    from seldon.config import get_neo4j_driver, load_project_config
    manifest = json.loads((REPO / "corpus" / "manifest.json")
                          .read_text(encoding="utf-8"))["entries"]
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            text, report = report_traceability.sources_appendix(s)
            table = report_traceability.measure(s, report["legs"])
    finally:
        driver.close()
    if report["doc_ids_not_in_manifest"]:
        raise SystemExit(f"FATAL: the appendix would cite documents outside the manifest: "
                         f"{report['doc_ids_not_in_manifest']}; nothing written")
    rows = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("|--") or "| Check |" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if len(cells) != 5:
            raise SystemExit(f"FATAL: appendix row has {len(cells)} cells, not 5: {line[:120]}")
        leg, indicator, citation, doc, locator = cells
        doc_id = doc.strip("`")
        entry = manifest.get(doc_id) or {}
        rows.append({"check": leg, "indicator": indicator, "citation": citation,
                     "doc_id": doc_id or None, "locator": locator or None,
                     "source_url": ((entry.get("identity") or {}).get("source_url")
                                    if entry else None),
                     # The manifest keeps the document's digest under `identity`, beside the
                     # URL it was fetched from; `integrity` holds the CHECKS run on the bytes,
                     # not the digest. DD-003's provenance pair is `primary_url +
                     # content_hash`, and both halves belong on a published citation row.
                     "content_hash": ((entry.get("identity") or {}).get("sha256")
                                      if entry else None),
                     "acquired_at": ((entry.get("acquisition") or {}).get("acquired_at")
                                     if entry else None)})
    return {"task": TASK, "legs": report["legs"], "rows": rows,
            "rows_per_leg": report["rows_per_leg"],
            "legs_without_source": report["legs_without_source"],
            "missing_fields": report["missing_fields"],
            "per_leg_chain": {k: {kk: vv for kk, vv in v.items() if kk != "all_source_ids"}
                              for k, v in table.items()},
            "note": ("One row per check and admitted source. `citation` is the corpus "
                     "manifest's record of the source; `locator` is where inside it the "
                     "framework's evidence cell points. Generated from the graph.")}


# --------------------------------------------------------------- citation metadata

def citation_cff(pub: dict) -> str:
    import yaml
    doc = {
        "cff-version": "1.2.0",
        "message": "If you use these findings, please cite them as below.",
        "title": pub["title"],
        "abstract": " ".join(pub["abstract"].split()),
        "authors": pub["authors"],
        "version": pub["version"],
        "date-released": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "url": pub["site_url"],
        "repository-code": pub["repository_url"],
        "keywords": pub["keywords"],
        "type": "dataset",
    }
    header = (
        "# Citation File Format. GENERATED by scripts/build_l0_site.py from\n"
        "# docs/reports/publication.yaml; edit that file, not this one.\n"
        f"# {TASK} decision 4. No DOI is minted here: the deposit is the author's action\n"
        "# under his own name (DN-002 decision 5), and `.zenodo.json` beside this file is\n"
        "# the metadata that deposit would carry.\n")
    return header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)


def zenodo_json(pub: dict) -> str:
    doc = {
        "title": pub["title"],
        "description": " ".join(pub["abstract"].split()),
        "upload_type": "dataset",
        "version": pub["version"],
        "publication_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "creators": [{"name": f"{a['family-names']}, {a['given-names']}"}
                     for a in pub["authors"]],
        "keywords": pub["keywords"],
        "related_identifiers": [
            {"identifier": pub["repository_url"], "relation": "isSupplementTo",
             "scheme": "url"},
        ],
        "notes": (f"Prepared by {TASK} decision 4 and NOT deposited. No licence is declared: "
                  f"the repository carries no LICENSE file and the choice is the author's."),
    }
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


# --------------------------------------------------------------- robots, llms, sitemap

def robots_txt(pub: dict, crawlers: list) -> str:
    """A robots.txt that admits, by name, every AI crawler this instrument evaluates others on.

    **What it can and cannot do here, said on its face.** RFC 9309 §2.3 binds a robots.txt to
    an AUTHORITY — scheme, host and port — not to a path prefix. On a project Pages site the
    authority is the whole of `<user>.github.io`, whose `/robots.txt` belongs to the user site
    and not to this repository. This file is therefore the declaration this publisher makes and
    is served inside the tree; it governs nothing at the host root until the site is given a
    host of its own. That limitation is stated in the file rather than papered over, because
    the alternative is a site that reports itself compliant on a file no crawler will read.
    """
    lines = [
        "# robots.txt for the AI-readiness L0 publication.",
        "# GENERATED by scripts/build_l0_site.py from assessment/harness/scan/params.yaml",
        f"# (a4_crawlers.user_agents) under {TASK} decision 2. Do not edit by hand.",
        "#",
        "# Every user agent the A4 and A11-declared checks evaluate other publishers against",
        "# is admitted here by name, on every path. Nothing is disallowed.",
        "#",
        "# RFC 9309 SS2.3: a robots.txt governs the AUTHORITY it is served from. This file sits",
        "# at " + pub["site_url"] + "robots.txt, inside a project site, so the authority a",
        "# crawler actually reads is https://" + pub["site_url"].split("/")[2] + "/robots.txt,",
        "# which belongs to the user site and not to this repository. Until this publication",
        "# has a host of its own, this file is a DECLARATION and not an enforcement point, and",
        "# the site's own A4 row has to be read with that in mind.",
        "",
    ]
    for ua in crawlers:
        lines += [f"User-agent: {ua}", "Allow: /", ""]
    lines += ["User-agent: *", "Allow: /", "",
              f"Sitemap: {pub['site_url']}sitemap.xml", ""]
    return "\n".join(lines)


def llms_txt(pub: dict, files: list) -> str:
    """`/llms.txt` in the llmstxt.org shape: an H1, a blockquote summary, then linked lists.

    Adopted rather than invented — the format is a published convention (llmstxt.org, 2024)
    and the A5 discovery probe looks for the file at that path. The links are the same data
    links the index carries, in the same order, because two lists of the same thing that can
    disagree eventually will.
    """
    out = [f"# {pub['title']}", "",
           "> " + " ".join(pub["abstract"].split()), "",
           f"Snapshot cycle `{pub['snapshot_cycle']}`, version `{pub['version']}`. The data "
           f"below is the publication; the markdown and the PDF are views of it.", "",
           "## Data", ""]
    for rel, label in files:
        out.append(f"- [{label}]({pub['site_url']}{rel})")
    out += ["", "## Views", "",
            f"- [The report, markdown]({pub['site_url']}reports/{STEM}.md)",
            f"- [The report, PDF]({pub['site_url']}reports/{STEM}.pdf)",
            f"- [Framework progress page]({pub['site_url']}progress/)",
            "", "## Citation", "",
            f"- [CITATION.cff]({pub['site_url']}data/CITATION.cff)",
            f"- [Zenodo deposition metadata, prepared and not deposited]"
            f"({pub['site_url']}data/zenodo.json)",
            f"- [What is published, from where, at which digest]"
            f"({pub['site_url']}data/index.json)",
            "", "## Source", "",
            f"- [Repository]({pub['repository_url']})", ""]
    return "\n".join(out)


def sitemap_xml(pub: dict, paths: list, lastmod: str) -> str:
    urls = "".join(
        f"  <url><loc>{html.escape(pub['site_url'] + p)}</loc>"
        f"<lastmod>{lastmod}</lastmod></url>\n" for p in paths)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}</urlset>\n")


# --------------------------------------------------------------- the self row

#: Where decision 2's self-scan leaves its verdicts. Absent until the host is served.
def self_row_path(pub: dict) -> Path:
    return REPO / "state" / f"self_l0_{cycle_suffix(pub['snapshot_cycle'])}.json"


def self_row(pub: dict) -> dict | None:
    p = self_row_path(pub)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------- the index

def index_html(pub: dict, data_links: list, results_n: int, self_: dict | None,
               commit: str, built: str) -> str:
    e = html.escape

    def li(href, label):
        return (f'  <li><a href="{e(href)}"><code>{e(href)}</code></a> \u2014 {label}</li>')

    items = "\n".join(li(rel, e(label)) for rel, label in data_links)

    if self_:
        rows = "".join(
            f"<tr><td><code>{e(leg)}</code></td><td class=\"v {e(v['verdict'])}\">"
            f"{e(v['verdict'])}</td><td>{e(v.get('reason') or '')}</td></tr>"
            for leg, v in self_["legs"].items())
        selfblock = (
            f"<p>Measured against this host with the same identified client the agency "
            f"matrix was measured with, cycle <code>{e(self_['cycle'])}</code>. These "
            f"verdicts sit outside the agency matrix, as the three reference hosts do.</p>"
            f"<table><thead><tr><th>Check</th><th>Verdict</th><th>Reason</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            f"<p class=\"note\">A <code>fail</code> here is reported and left standing. "
            f"Repairing a site after scanning it is the thing this instrument measures "
            f"publishers for.</p>")
    else:
        selfblock = (
            "<p class=\"stop\"><strong>Not measured.</strong> The six host-level checks have "
            "not been run against this host, because at the time of this build the host was "
            "not serving this tree: GitHub Pages is not enabled for the repository "
            f"(<code>has_pages: false</code>), and every path under "
            f"<code>{e(pub['site_url'])}</code> answered HTTP 404. A verdict cannot be "
            "invented for a host that does not answer, and a placeholder row on a page whose "
            "whole subject is publishers who claim more than they serve would be the worst "
            "possible entry. The row appears here as soon as the scan has been run.</p>"
            "<p class=\"note\">There is a second limit the row will have to carry when it is "
            "measured, and it is structural rather than an omission: RFC 9309 binds "
            "<code>robots.txt</code> to an authority, not a path prefix, so a project Pages "
            "site cannot serve an effective one. <code>robots.txt</code>, "
            "<code>llms.txt</code> and the sitemap are published inside this tree and are "
            "declarations; they become enforcement points only when this publication has a "
            "host of its own.</p>")

    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(pub['title'])}</title>
<meta name="description" content="{e(' '.join(pub['abstract'].split())[:300])}">
<style>
:root {{ --fg:#0f172a; --muted:#64748b; --line:#e2e8f0; --bg:#ffffff; --acc:#1d4ed8; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fg:#e2e8f0; --muted:#94a3b8; --line:#334155; --bg:#0f172a; --acc:#93c5fd; }} }}
* {{ box-sizing:border-box }}
body {{ margin:0 auto; max-width:52rem; padding:2rem 1.25rem 4rem; background:var(--bg);
  color:var(--fg); font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,
  sans-serif }}
h1 {{ font-size:1.6rem; line-height:1.25; margin:0 0 .4rem }}
h2 {{ font-size:1.1rem; margin:2.4rem 0 .6rem; padding-bottom:.3rem;
  border-bottom:1px solid var(--line) }}
p.sub {{ color:var(--muted); margin:0 0 1.6rem }}
a {{ color:var(--acc) }}
code {{ font-size:.87em; background:rgba(127,127,127,.14); padding:.08em .34em;
  border-radius:4px }}
ol, ul {{ padding-left:1.3rem }}
li {{ margin:.42rem 0 }}
.note {{ color:var(--muted); font-size:.9em }}
.stop {{ border-left:3px solid #b45309; padding-left:.9rem }}
table {{ border-collapse:collapse; width:100%; margin:.6rem 0; font-size:.94em }}
th, td {{ text-align:left; padding:.38rem .5rem; border-bottom:1px solid var(--line);
  vertical-align:top }}
td.v {{ font-weight:600 }}
td.v.pass {{ color:#15803d }} td.v.fail {{ color:#b91c1c }}
td.v.error, td.v.not_applicable {{ color:var(--muted) }}
footer {{ margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line);
  color:var(--muted); font-size:.9em }}
</style>

<h1>{e(pub['title'])}</h1>
<p class="sub">Snapshot cycle <code>{e(pub['snapshot_cycle'])}</code> ·
version <code>{e(pub['version'])}</code> ·
built from commit <code>{e(commit)}</code> on <code>{e(built)}</code> (UTC).</p>

<p>{e(' '.join(pub['abstract'].split()))}</p>

<h2>The data</h2>
<ol>
{items}
</ol>

<h2>The views</h2>
<ul>
  <li><a href="reports/{STEM}.md"><code>reports/{STEM}.md</code></a> — the report as built
      markdown, every number resolved from the graph by name.</li>
  <li><a href="reports/{STEM}.pdf"><code>reports/{STEM}.pdf</code></a> — the report as PDF.</li>
  <li><a href="progress/"><code>progress/</code></a> — the framework progress page.</li>
</ul>
<p><strong>The PDF is a projection of the data above it.</strong> Every number in its prose
is one of the {results_n} registered Results published above, quoted by name and resolved from
the graph at build time; every figure it carries is drawn from the same Results. Nothing in it
is typed.</p>

<h2>This site's own row</h2>
{selfblock}

<h2>How to cite</h2>
<p><a href="data/CITATION.cff"><code>data/CITATION.cff</code></a> carries the citation
metadata; <a href="data/zenodo.json"><code>data/zenodo.json</code></a> is the deposition
metadata, prepared and not deposited. No DOI is minted and no licence is declared — both are
the author's to decide.</p>

<footer>
Built by <code>scripts/build_l0_site.py</code> under <code>{e(TASK)}</code>.
Source: <a href="{e(pub['repository_url'])}">{e(pub['repository_url'])}</a>.
</footer>
</html>
"""


# ---------------------------------------------------------------------------

def build(check: bool = False) -> int:
    from scan import load_params
    pub = publication()
    suffix = cycle_suffix(pub["snapshot_cycle"])
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    commit = head_commit()

    DATA.mkdir(parents=True, exist_ok=True)
    written, links = [], []

    # 1. the matrices, already beside the report, linked as JSON and CSV
    for stem, label in MATRICES:
        for ext in ("json", "csv"):
            rel = f"reports/scan_matrix_{stem}_{suffix}.{ext}"
            if not (SITE / rel).is_file():
                raise SystemExit(f"FATAL: {rel} does not exist; run "
                                 f"scripts/build_l0_matrices.py --cycle "
                                 f"{pub['snapshot_cycle']} first")
            links.append((rel, f"Matrix, {stem}, {ext.upper()}. {label}"))

    # 2. the per-check source appendix
    appendix = sources_per_check()
    # 3. the tagged Results
    results = tagged_results()
    payloads = [("data/sources_per_check.json", appendix,
                 "The per-check source appendix: every check, every admitted source, its "
                 "doc_id, its URL and its locator."),
                ("data/results_tagged.json",
                 {"task": TASK, "snapshot_cycle": pub["snapshot_cycle"],
                  "count": len(results), "results": results,
                  "provenance_paths_absent": sorted({
                      ref["path"] for r in results
                      for ref in r["computed_from"] + r["generated_by"]
                      if not ref["present_in_repository"]}),
                  "note": ("Every Result the report quotes by name, with its value, its "
                           "lifecycle state, and the DataFile and Script that produced it. "
                           "`present_in_repository` says whether the repository holds the "
                           "path each reference names, measured at build time; "
                           "`provenance_paths_absent` collects the ones it does not.")},
                 "Every registered Result the report quotes: name, value, state, provenance.")]

    for rel, doc, label in payloads:
        path = SITE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not check:
            path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        written.append(rel)
        links.append((rel, label))

    # 4. the citation files: one string each, written to the root and into the tree
    citations = {"CITATION.cff": citation_cff(pub), "zenodo.json": zenodo_json(pub)}
    cited = []
    for published, root_rel, label in CITATION_FILES:
        text = citations[published]
        if not check:
            (REPO / root_rel).write_text(text, encoding="utf-8")
            (DATA / published).write_text(text, encoding="utf-8")
        cited.append({"published": f"data/{published}", "also_written_to": root_rel,
                      "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                      "bytes": len(text.encode("utf-8")), "description": label})
        written += [f"data/{published}", root_rel]

    # 5. every copy, hashed against its source
    copied = []
    for name, src_rel, label in COPIES:
        src = REPO / src_rel
        if not src.is_file():
            raise SystemExit(f"FATAL: {src_rel} does not exist; it cannot be published")
        dst = DATA / name
        if not check:
            shutil.copyfile(src, dst)
        copied.append({"published": f"data/{name}", "source": src_rel,
                       "sha256": sha256(src), "bytes": src.stat().st_size,
                       "description": label})
        written.append(f"data/{name}")
        links.append((f"data/{name}", label))

    # 6. the data manifest: what is published, from where, at which digest
    manifest = {"task": TASK, "built_at": datetime.now(timezone.utc).isoformat(),
                "build_commit": commit, "snapshot_cycle": pub["snapshot_cycle"],
                "version": pub["version"], "site_url": pub["site_url"],
                "copies": copied, "citation_files": cited,
                "generated": [{"published": rel, "description": label}
                              for rel, label in links if rel.startswith("data/")
                              and rel not in {c["published"] for c in copied}
                              and rel not in {c["published"] for c in cited}],
                "matrices": [f"reports/scan_matrix_{s}_{suffix}.{x}"
                             for s, _l in MATRICES for x in ("json", "csv")],
                "note": ("`copies` are byte-for-byte copies of records canonical elsewhere in "
                         "the repository; the sha256 is of the SOURCE, so a drifted copy is "
                         "detectable. tests/test_publication.py asserts it.")}
    if not check:
        (DATA / "index.json").write_text(json.dumps(manifest, indent=1) + "\n",
                                         encoding="utf-8")
    written.append("data/index.json")

    # 7. robots, llms, sitemap, and the Jekyll opt-out
    crawlers = list(load_params()["a4_crawlers"]["user_agents"])
    # Every URL the index or llms.txt names, plus the two the reader reaches them through.
    # `robots.txt` is deliberately absent: a sitemap enumerates content, and robots.txt is the
    # instruction about it.
    pages = ["", "reports/" + STEM + ".md", "reports/" + STEM + ".pdf", "progress/",
             "llms.txt"] + [rel for rel, _l in links] + [
        "data/CITATION.cff", "data/zenodo.json", "data/index.json"]
    files = {
        "robots.txt": robots_txt(pub, crawlers),
        "llms.txt": llms_txt(pub, links),
        "sitemap.xml": sitemap_xml(pub, pages, built),
        ".nojekyll": ("# GitHub Pages serves this tree as static files. Without this marker\n"
                      "# Jekyll drops every path beginning with an underscore or a dot.\n"),
    }
    self_ = self_row(pub)
    files["index.html"] = index_html(pub, links, len(results), self_, commit, built)
    for name, text in files.items():
        if not check:
            (SITE / name).write_text(text, encoding="utf-8")
        written.append(name)

    summary = {"site": str(SITE.relative_to(REPO)), "snapshot_cycle": pub["snapshot_cycle"],
               "build_commit": commit, "built": built,
               "data_links": len(links), "tagged_results": len(results),
               "appendix_rows": appendix["rows_per_leg"],
               "legs_without_source": appendix["legs_without_source"],
               "self_row": "measured" if self_ else "not measured (host not served)",
               "crawlers_admitted": crawlers, "written": sorted(written),
               "check_only": check}
    print(json.dumps(summary, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="compute everything, write nothing")
    a = ap.parse_args(argv)
    return build(check=a.check)


if __name__ == "__main__":
    raise SystemExit(main())
