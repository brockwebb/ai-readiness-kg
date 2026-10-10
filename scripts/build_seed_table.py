#!/usr/bin/env python3
"""Write the seed table of known locations, per body and per object. **No network, no model call.**

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 4, DN-013-R1.
The recollection read each body's locations the way a stranger would, from the agency's own
pages, and left twelve bodies blank on at least one object. DN-013 §1: api.census.gov,
api.bls.gov, api.eia.gov, the BEA API, NASS Quick Stats and the data.gov API catalog are public
knowledge, in training data and in this repository's own files. This writes them down, with where
each came from, so part 2 (`cc_tasks/2026-10-07_seed_known_locations_verify.md`) can verify every
one by a single fetch. Nothing here is verified: every seed is `status: seeded_unverified`.

**Sources, each named on every seed it produced** (`seeded_from`, `declarations.SEED_SOURCES`):

* `model_knowledge:<model id>` — `MODEL_SEEDS` below: what the authoring session knows, each with a
  `confidence` (high, medium, low) and a note where the location is near the body but not the
  body's (FRED is the St. Louis Fed's, not the Board's). A seed is never dropped because it might
  be wrong: part 2 verifies it.
* `repo:<path>:<line>` — every URL this repository cites that has the shape of one of the objects
  and lives on one of the body's hosts: `docs/`, `corpus/evidence/frame/` (the recollection's
  retained pages), `docs/data/sources_per_check.json`, and `targets.yaml` `declared_locations`
  (`URL_SHAPES`, `BODY_DOMAINS`). The first `MAX_CITATIONS` citations per URL are kept.
* `developer_page:<page>` — a location the recollection read off the body's own page
  (`read_from.page`), and every page a `not_declared` or `unreadable` entry names as searched,
  recorded as a page to read for the object (`kind: page_to_read`).
* `catalog.data.gov` and `api.data.gov` — not fetched here. Each body carries the query part 2
  runs (`queries`): CKAN `package_search` filtered by the body's organization and by API resource
  formats, the organization record, and api.data.gov's documentation index.

The table lists the host of every seed and, at its foot, every host part 2 will contact
(`hosts`), so the fetch list is generated from the table and printed before the first request.

    /opt/anaconda3/bin/python3 scripts/build_seed_table.py [--check]

The table is a DATED snapshot (its file name carries the date): it records what the repository
cited when it was written, and part 2 updates its statuses in place. `--check` compares against
a fresh build and is meaningful only on the commit that wrote the table; a later commit that
cites a new URL makes it differ, which is not staleness of the snapshot.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import declarations                                          # noqa: E402

TASK = "cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md"
MODEL = "claude-opus-5-5"
OUT = REPO / "assessment" / "harness" / "scan" / "seeds" / "known_locations_2026-10-07.yaml"
FRAME = REPO / "state" / "scan_targets_fss_2026-09_v5.json"
TARGETS = REPO / "assessment" / "harness" / "scan" / "targets.yaml"

#: Where the repository's citations are read from (the task's list).
REPO_ROOTS = ("docs", "corpus/evidence/frame", "docs/data/sources_per_check.json",
              "assessment/harness/scan/targets.yaml")
#: Files under `docs/` that are not citations but derived bundles (fonts, PDFs, images).
SKIP_SUFFIXES = (".pdf", ".png", ".svg", ".woff", ".woff2", ".ttf", ".ico", ".jpg", ".gif")
#: How many `repo:` citations a seed keeps per URL. The first ones in path order; the rest add
#: nothing a verifier needs.
MAX_CITATIONS = 3

#: Hosts a body's objects may live on, by registrable suffix. The roster host's family (its API
#: and data subdomains) and, for the inventory only, the parent department's host.
BODY_DOMAINS = {
    "BEA": ["bea.gov"], "BJS": ["bjs.ojp.gov", "api.ojp.gov", "data.ojp.gov"],
    "BLS": ["bls.gov"], "BTS": ["bts.gov"], "CENSUS": ["census.gov"],
    "DRSMSU": ["federalreserve.gov"], "EIA": ["eia.gov"], "ERS": ["ers.usda.gov"],
    "NAHMSAPHIS": ["aphis.usda.gov"], "NASS": ["nass.usda.gov"], "NCES": ["nces.ed.gov"],
    "NCHS": ["cdc.gov"], "NCSES": ["ncses.nsf.gov"], "ORES": ["ssa.gov"],
    "SAMHSACBHS": ["samhsa.gov"], "SOI": ["irs.gov"],
}
DEPARTMENT_HOSTS = {
    "BEA": ["www.commerce.gov"], "BJS": ["www.justice.gov"], "BLS": ["www.dol.gov"],
    "BTS": ["www.transportation.gov"], "CENSUS": ["www.commerce.gov"], "DRSMSU": [],
    "EIA": ["www.energy.gov"], "ERS": ["www.usda.gov"], "NAHMSAPHIS": ["www.usda.gov"],
    "NASS": ["www.usda.gov"], "NCES": ["www.ed.gov"], "NCHS": ["hhs.gov", "www.hhs.gov"],
    "NCSES": ["www.nsf.gov"], "ORES": [], "SAMHSACBHS": ["www.hhs.gov", "hhs.gov"],
    "SOI": ["www.treasury.gov", "home.treasury.gov"],
}

#: object -> a URL shape. Deliberately loose: a seed is a candidate, verified by one fetch.
URL_SHAPES = {
    "inventory": re.compile(r"/data\.json$", re.I),
    "api_terms": re.compile(r"(terms[-_ ]?of[-_ ]?(service|use)|termsofservice|/tos\b|"
                            r"/terms(\.html?|/|$)|api[-_]?terms|license[-_]?agreement)", re.I),
    "changelog": re.compile(r"(change[-_]?log|release[-_]?notes|whats[-_]?new|what-s-new|"
                            r"developers?/updates|api[-_]?updates|/updates\.html)", re.I),
    "api_base": re.compile(r"(^https?://api\.|/api(/|$|\?)|/api/v\d|/publicapi/|"
                           r"/datarequest|/resource/[a-z0-9]{4}-[a-z0-9]{4}|/opengis/rest/)",
                           re.I),
}
URL_RE = re.compile(r"https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s\"'<>\\)\]}|,;`]*)?")

#: What the authoring session knows. `confidence` is the session's own, stated so a verifier
#: knows which seeds it expects to fail. `note` says what a seed is when it is not plainly the
#: body's object.
MODEL_SEEDS = {
    "BEA": {
        "api_base": [("https://apps.bea.gov/api/data", "high",
                      "the BEA API endpoint; every request carries UserID and method")],
        "api_terms": [("https://apps.bea.gov/API/signup/", "medium",
                       "the API's sign-up page, where its terms of service are presented"),
                      ("https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf",
                       "medium", "the API user guide, which states the terms of use")],
        "changelog": [("https://apps.bea.gov/api/whatsnew.htm", "low",
                       "a what's-new page for the API; the path is a guess")],
        "inventory": [("https://www.commerce.gov/data.json", "high",
                       "the Department of Commerce inventory, which data.gov harvests")],
    },
    "BJS": {
        "api_base": [("https://api.ojp.gov/bjsdataset/v1/", "medium",
                      "the BJS dataset API path its NCVS and NIBRS pages state"),
                     ("https://data.ojp.gov/api/views", "medium",
                      "OJP's Socrata catalog, which hosts BJS datasets")],
        "api_terms": [("https://dev.socrata.com/docs/", "low",
                       "Socrata's API documentation; the platform's terms, not BJS's own")],
        "inventory": [("https://www.justice.gov/data.json", "high",
                       "the Department of Justice inventory")],
    },
    "BLS": {
        "api_base": [("https://api.bls.gov/publicAPI/v2/timeseries/data/", "high",
                      "the BLS Public Data API, version 2"),
                     ("https://api.bls.gov/publicAPI/v1/timeseries/data/", "high",
                      "version 1, no registration key")],
        "api_terms": [("https://www.bls.gov/developers/termsOfService.htm", "medium",
                       "the BLS developers terms of service")],
        "changelog": [("https://www.bls.gov/developers/api_faqs.htm", "low",
                       "the API FAQ, which records version changes"),
                      ("https://www.bls.gov/bls/whatsnew.htm", "medium",
                       "the BLS what's-new page, for the site rather than the API")],
        "inventory": [("https://www.dol.gov/data.json", "high",
                       "the Department of Labor inventory")],
    },
    "BTS": {
        "api_base": [("https://data.bts.gov/api/views", "medium",
                      "BTS's Socrata data portal; every dataset has a /resource/ endpoint"),
                     ("https://data.bts.gov/api/catalog/v1", "low",
                      "the Socrata discovery API scoped to the portal")],
        "inventory": [("https://data.bts.gov/data.json", "medium",
                       "the Socrata portal's DCAT-US catalog"),
                      ("https://www.transportation.gov/data.json", "high",
                       "the Department of Transportation inventory")],
    },
    "CENSUS": {
        "api_base": [("https://api.census.gov/data", "high", "the Census Data API base"),
                     ("https://api.census.gov/data.json", "high",
                      "the API's discovery catalog (a dcat:Catalog of its datasets)")],
        "api_terms": [("https://www.census.gov/data/developers/about/terms-of-service.html",
                       "high", "the Census Data API terms of service")],
        "changelog": [("https://www.census.gov/data/developers/updates.html", "medium",
                       "the developers' updates page")],
        "inventory": [("https://www.commerce.gov/data.json", "high",
                       "the Department of Commerce inventory")],
    },
    "DRSMSU": {
        "api_base": [("https://www.federalreserve.gov/datadownload/", "medium",
                      "the Board's Data Download Program: a download tool, not a REST API"),
                     ("https://api.stlouisfed.org/fred/", "low",
                      "FRED is the St. Louis Fed's API, not the Board's; it republishes some "
                      "Board series and none of the SCF microdata")],
        "inventory": [("https://www.federalreserve.gov/data.json", "high",
                       "the Board's own inventory")],
    },
    "EIA": {
        "api_base": [("https://api.eia.gov/v2/", "high", "EIA API version 2")],
        "api_terms": [("https://www.eia.gov/opendata/terms-of-service.php", "high",
                       "the EIA open data terms of service")],
        "changelog": [("https://www.eia.gov/opendata/documentation.php", "medium",
                       "the API documentation, which carries the version notes")],
        "inventory": [("https://www.energy.gov/data.json", "high",
                       "the Department of Energy inventory")],
    },
    "ERS": {
        "api_base": [("https://api.ers.usda.gov/data/", "medium",
                      "ERS data APIs (ARMS and others), keyed through api.data.gov"),
                     ("https://www.ers.usda.gov/developer/", "high",
                      "the ERS developer page that documents them")],
        "api_terms": [("https://api.data.gov/", "low",
                       "api.data.gov issues the key; its terms apply to the key, not ERS's data")],
        "inventory": [("https://www.usda.gov/data.json", "high",
                       "the Department of Agriculture inventory")],
    },
    "NAHMSAPHIS": {
        "inventory": [("https://www.usda.gov/data.json", "high",
                       "the Department of Agriculture inventory")],
    },
    "NASS": {
        "api_base": [("https://quickstats.nass.usda.gov/api", "high", "the Quick Stats API"),
                     ("https://quickstats.nass.usda.gov/api/api_GET/", "high",
                      "its query endpoint")],
        "api_terms": [("https://quickstats.nass.usda.gov/api", "medium",
                       "the API page, which carries the usage terms")],
        "inventory": [("https://www.usda.gov/data.json", "high",
                       "the Department of Agriculture inventory")],
    },
    "NCES": {
        "api_base": [("https://nces.ed.gov/opengis/rest/services", "medium",
                      "the EDGE ArcGIS REST services NCES publishes"),
                     ("https://educationdata.urban.org/api/v1/", "low",
                      "the Urban Institute's Education Data Portal API over NCES data; not "
                      "NCES's own")],
        "inventory": [("https://www.ed.gov/data.json", "high",
                       "the Department of Education inventory")],
    },
    "NCHS": {
        "api_base": [("https://data.cdc.gov/api/views", "medium",
                      "CDC's Socrata portal, which hosts NCHS datasets"),
                     ("https://wonder.cdc.gov/controller/datarequest/", "high",
                      "the CDC WONDER API, which serves NCHS vital statistics")],
        "api_terms": [("https://wonder.cdc.gov/DataUse.html", "medium",
                       "WONDER's data use restrictions")],
        "inventory": [("https://data.cdc.gov/data.json", "medium",
                       "the Socrata portal's DCAT-US catalog"),
                      ("https://www.hhs.gov/data.json", "high",
                       "the Department of Health and Human Services inventory")],
    },
    "NCSES": {
        "api_base": [("https://api.nsf.gov/services/v1/awards.json", "low",
                      "NSF's awards API: NSF's, not an NCSES statistics API")],
        "inventory": [("https://www.nsf.gov/data.json", "high", "the NSF inventory")],
    },
    "ORES": {
        "inventory": [("https://www.ssa.gov/data.json", "high", "SSA's own inventory")],
    },
    "SAMHSACBHS": {
        "inventory": [("https://www.hhs.gov/data.json", "high",
                       "the Department of Health and Human Services inventory")],
    },
    "SOI": {
        "inventory": [("https://www.treasury.gov/data.json", "high",
                       "the Department of the Treasury inventory")],
    },
}


def host(u: str) -> str:
    return urllib.parse.urlsplit(u).netloc.lower()


def on_body(u: str, body: str, obj: str) -> bool:
    h = host(u)
    fam = any(h == d or h.endswith("." + d) for d in BODY_DOMAINS[body])
    if obj == "inventory":
        return fam or h in DEPARTMENT_HOSTS[body]
    return fam


#: A path segment that ends an API's base: the API's root (`api`, `publicAPI`, `data`, `rest`,
#: `services`), optionally followed by a version (`v2`). Everything after it addresses a resource
#: of the API, not the API.
_BASE_SEGMENT = re.compile(r"^(api|publicapi|data|rest|services|bjsdataset)$", re.I)
_VERSION_SEGMENT = re.compile(r"^v\d+(\.\d+)?$", re.I)


def normalise(u: str) -> str:
    """A cited URL as a location: no query or fragment (HTML-escaped `&amp;` tails included),
    no trailing punctuation."""
    p = urllib.parse.urlsplit(u.split("&amp")[0])
    path = p.path.rstrip(".,")
    return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), path, "", ""))


def api_base_of(u: str) -> str:
    """The API base a cited API URL lives under: the path up to its base segment and an
    immediately following version, or the host root for an `api.` host with no such segment.
    `http://api.census.gov/data/1986/cbp` is `http://api.census.gov/data`;
    `https://api.ojp.gov/bjsdataset/v1/4rg2-6x7i.csv` is `https://api.ojp.gov/bjsdataset/v1`."""
    p = urllib.parse.urlsplit(u)
    segs = [x for x in p.path.split("/") if x]
    for i, seg in enumerate(segs):
        if _BASE_SEGMENT.match(seg) or (_VERSION_SEGMENT.match(seg) and i == 0):
            end = i + 1
            if end < len(segs) and _VERSION_SEGMENT.match(segs[end]):
                end += 1
            return urllib.parse.urlunsplit((p.scheme, p.netloc, "/" + "/".join(segs[:end]),
                                            "", ""))
    if p.netloc.startswith("api."):
        return urllib.parse.urlunsplit((p.scheme, p.netloc, "/", "", ""))
    return u


def repo_files() -> list:
    out = []
    for root in REPO_ROOTS:
        p = REPO / root
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out += sorted(f for f in p.rglob("*") if f.is_file()
                          and not f.name.endswith(SKIP_SUFFIXES))
    return out


def repo_citations() -> dict:
    """`{url: ["repo:<path>:<line>", ...]}` for every URL in the repository roots."""
    cites: dict = defaultdict(list)
    for f in repo_files():
        rel = f.relative_to(REPO).as_posix()
        try:
            text = f.read_bytes().decode("utf-8", "replace")
        except OSError as exc:
            raise SystemExit(f"FATAL: cannot read {rel}: {exc}")
        for n, line in enumerate(text.splitlines(), 1):
            for m in URL_RE.finditer(line):
                u = normalise(m.group(0))
                if len(cites[u]) < MAX_CITATIONS and f"repo:{rel}:{n}" not in cites[u]:
                    cites[u].append(f"repo:{rel}:{n}")
    return cites


def targets_lines() -> dict:
    """`{url: line}` of each URL's first appearance in `targets.yaml`, for `repo:` citations of
    the recollection's declarations."""
    out = {}
    for n, line in enumerate(TARGETS.read_text(encoding="utf-8").splitlines(), 1):
        for m in URL_RE.finditer(line):
            out.setdefault(normalise(m.group(0)), n)
    return out


def org_slugs(block: dict) -> dict:
    out = {}
    for b, e in block["bodies"].items():
        for i in e.get("inventory_urls") or []:
            if i.get("kind") == "catalog_organization":
                out[b] = i["url"].rstrip("/").rsplit("/", 1)[-1]
    return out


def queries(body: str, slug: str | None) -> dict:
    """The data.gov queries part 2 runs for a body (decision 4's third bullet)."""
    ckan = "https://catalog.data.gov/api/3/action"
    out = {"catalog.data.gov": {
        "organization": slug,
        "runs": ([f"{ckan}/package_search?fq=organization:{slug}+AND+res_format:"
                  f"(API+OR+%22Esri+REST%22)&rows=1000",
                  f"{ckan}/organization_show?id={slug}&include_extras=true"]
                 if slug else []),
        "finds": ("API resources (accessURL of distributions whose format is API or Esri "
                  "REST) and the organization's harvest source; each becomes a seed with "
                  "seeded_from catalog.data.gov:<query>"),
        **({} if slug else {"why_none": "no catalog.data.gov organization is recorded"})}}
    out["api.data.gov"] = {
        "runs": ["https://api.data.gov/docs/"],
        "finds": (f"the agency's entry in api.data.gov's documentation index, searched for "
                  f"{body}'s name and its department's; each API listed becomes a seed with "
                  f"seeded_from api.data.gov:<page>")}
    return out


def build() -> dict:
    block = declarations.load()
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    roster = defaultdict(set)
    for r in frame["rows"]:
        if r["agency"] in BODY_DOMAINS:
            roster[r["agency"]].add(r["host"])
    if set(roster) != set(block["bodies"]) or set(BODY_DOMAINS) != set(block["bodies"]):
        raise SystemExit(f"FATAL: the bodies disagree: frame {sorted(roster)}, declared "
                         f"{sorted(block['bodies'])}, domains {sorted(BODY_DOMAINS)}")
    cites = repo_citations()
    tline = targets_lines()
    slugs = org_slugs(block)
    model_tag = f"model_knowledge:{MODEL}"
    bodies = {}
    for b in sorted(block["bodies"]):
        decl = block["bodies"][b]
        seeds: dict = {o: {} for o in declarations.SEED_OBJECTS}

        def add(obj, url, source, **extra):
            fresh = url not in seeds[obj]
            e = seeds[obj].setdefault(url, {"url": url, "host": host(url), "seeded_from": [],
                                             "status": "seeded_unverified"})
            # A location some source names as the object stays a location when it is also a
            # page the recollection searched: `page_to_read` marks an entry that is ONLY that.
            if not fresh and extra.get("kind") == "page_to_read":
                extra = {k: v for k, v in extra.items() if k not in ("kind", "note")}
            elif fresh is False and e.get("kind") == "page_to_read" and "kind" not in extra:
                e.pop("kind", None)
            repo_n = sum(1 for x in e["seeded_from"] if x.startswith("repo:"))
            if source not in e["seeded_from"] and not (source.startswith("repo:")
                                                       and repo_n >= MAX_CITATIONS):
                e["seeded_from"].append(source)
            for k, v in extra.items():
                e.setdefault(k, v)

        for obj, rows in MODEL_SEEDS.get(b, {}).items():
            for url, conf, note in rows:
                add(obj, url, model_tag, confidence=conf, note=note)
        # The recollection's declarations: read off the body's pages, and cited in targets.yaml.
        api = decl.get("api_base") or {}
        located = [("api_base", api.get("url"), api.get("read_from")),
                   ("api_base", api.get("description_url"), api.get("read_from")),
                   ("api_terms", api.get("terms_url"),
                    api.get("terms_read_from") or api.get("read_from"))]
        located += [("catalog_organization" if i.get("kind") == "catalog_organization"
                     else "inventory", i["url"], i.get("read_from"))
                    for i in decl.get("inventory_urls") or []]
        located += [("changelog", c["url"], c.get("read_from"))
                    for c in decl.get("changelog_urls") or []]
        for obj, url, rf in located:
            if not url:
                continue
            add(obj, url, f"repo:assessment/harness/scan/targets.yaml:{tline.get(url, 0)}")
            page = (rf or {}).get("page")
            if page and not str((rf or {}).get("how", "")).startswith("the roster host"):
                add(obj, url, f"developer_page:{page}")
        # The pages a `not_declared` / `unreadable` entry names as searched: pages to read.
        role_obj = {"api_base": "api_base", "api_terms": "api_terms", "changelog": "changelog",
                    "own_host": "inventory", "department": "inventory",
                    "catalog_organization": "catalog_organization"}
        for u in decl.get("unresolved") or []:
            for pg in u.get("pages_searched") or []:
                add(role_obj[u["role"]], pg,
                    f"repo:assessment/harness/scan/targets.yaml:{tline.get(pg, 0)}",
                    kind="page_to_read",
                    note=f"searched by the recollection for the {u['role']} and recorded "
                         f"{u.get('status', 'unresolved')}: {u.get('why')}")
        # Every other citation in the repository with an object's shape on the body's hosts.
        for url, where in cites.items():
            if url.startswith("https://catalog.data.gov/organization/"):
                if slugs.get(b) and url.rstrip("/").endswith("/" + slugs[b]):
                    for w in where:
                        add("catalog_organization", url, w)
                continue
            for obj, shape in URL_SHAPES.items():
                if shape.search(url) and on_body(url, b, obj):
                    for w in where:
                        add(obj, api_base_of(url) if obj == "api_base" else url, w)
                    break
        objs = {o: sorted(v.values(), key=lambda e: e["url"]) for o, v in seeds.items()}
        bodies[b] = {
            "roster_hosts": sorted(roster[b]),
            "department_hosts": DEPARTMENT_HOSTS[b],
            "catalog_organization": slugs.get(b),
            "queries": queries(b, slugs.get(b)),
            "objects": objs,
            "no_seed": [o for o, v in objs.items() if not v],
        }
    hosts = sorted({e["host"] for v in bodies.values() for es in v["objects"].values()
                    for e in es}
                   | {h for v in bodies.values() for h in v["roster_hosts"]}
                   | {"catalog.data.gov", "api.data.gov"})
    return {
        "scheme": 1,
        "task": TASK,
        "generated_by": "scripts/build_seed_table.py",
        "model": MODEL,
        "statuses": list(declarations.SEED_STATUSES) + ["http_<code>"],
        "sources": {
            "model_knowledge": (f"what {MODEL} knows, with its confidence; never dropped for "
                                f"being possibly wrong (part 2 verifies every seed)"),
            "repo": ("every URL this repository cites under " + ", ".join(REPO_ROOTS)
                     + " with an object's shape on one of the body's hosts; the first "
                     f"{MAX_CITATIONS} citations per URL"),
            "developer_page": ("a location the recollection read off the body's own page "
                               "(`read_from.page`), or a page it searched (`page_to_read`)"),
            "catalog.data.gov": "not fetched here; each body's `queries` names what part 2 runs",
            "api.data.gov": "not fetched here; each body's `queries` names what part 2 runs",
        },
        "bodies": bodies,
        "hosts": hosts,
    }


def render(table: dict) -> str:
    head = ("# Known locations per body and object, SEEDED, not verified. Generated by\n"
            "# scripts/build_seed_table.py (cc_tasks/2026-10-07_seed_known_locations_and_split_\n"
            "# discoverability.md decision 4); part 2 verifies each seed by one fetch and writes\n"
            "# the result to targets.yaml declared_locations under scheme 2. Do not edit by hand.\n")
    return head + yaml.safe_dump(table, sort_keys=False, allow_unicode=True, width=100)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the file on disk differs from a fresh build")
    a = ap.parse_args(argv)
    table = build()
    declarations.validate_seed_table(table)
    text = render(table)
    if a.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != text:
            print(f"STALE: {OUT.relative_to(REPO)}", file=sys.stderr)
            return 1
        print("seed table current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    summary = {b: {o: len(v["objects"][o]) for o in v["objects"]}
               for b, v in table["bodies"].items()}
    print(json.dumps({"bodies": summary, "hosts": len(table["hosts"]),
                      "no_seed": {b: v["no_seed"] for b, v in table["bodies"].items()
                                  if v["no_seed"]}}, indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
