#!/usr/bin/env python3
"""Complete the seeds from data.gov, verify every seed by one GET, and write the result. **Zero model spend.**

`cc_tasks/2026-10-07_seed_known_locations_verify.md` decisions 1 and 2 (part 2 of DN-013-R1).
Part 1 (`scripts/build_seed_table.py`) wrote down where each body's API, API terms, changelog and
inventory are believed to be, from three sources, and verified none of them. This tool:

* `hosts`   prints and records the hosts the run may contact, BEFORE the first request: the seed
            table's `hosts` (every seed's host, catalog.data.gov and api.data.gov among them) and
            the 16 roster hosts. A data.gov seed on a host outside that list is printed as an
            amendment before its first request (`verify` refuses it otherwise).
* `datagov` runs the queries the seed table names for each body against catalog.data.gov (CKAN
            `package_search` by organization and API resource format, `organization_show`) and
            reads api.data.gov's documentation index, and writes every location found to a new
            table (`datagov_table`) with `seeded_from: catalog.data.gov:<query>` or
            `api.data.gov:<page>`. The part 1 table is not edited for this: its write set is
            statuses only.
* `verify`  GETs every distinct seed URL of both tables once.
* `classify` (no network) decides each seed's status per object by the tests in
            `seeds/verification.yaml`, writes the statuses (and `verified_at`) into both tables,
            and writes the per-seed report.
* `census`  (no network) requests per host and statuses, for the RESULT.

**Manners.** Every request goes through `scan.manners.Fetcher` (DD-060 identity, robots-first,
the standing per-host rate), as the cycle's own collectors do. A refusal is recorded as what it is.

**Checkpoint (CLAUDE.md §15).** The unit of work is one URL. Each fetch is appended to the fetch
log, flushed and fsynced, before the next is made; the URL is the key, so a URL already logged is
skipped and re-running a command is the resume command. A failed fetch is a row, never a crash
of the batch. Pilot and ceilings: the run is ~200 GETs at 1 req/s per host, with no model call
and no money; the wall-clock is bounded by the rate (about four minutes per busy host), so no
ceiling beyond the Fetcher's own timeouts is needed and none is invented.

    /opt/anaconda3/bin/python3 scripts/verify_seeded_locations.py hosts
    /opt/anaconda3/bin/python3 scripts/verify_seeded_locations.py datagov
    /opt/anaconda3/bin/python3 scripts/verify_seeded_locations.py verify
    /opt/anaconda3/bin/python3 scripts/verify_seeded_locations.py classify
    /opt/anaconda3/bin/python3 scripts/verify_seeded_locations.py census
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import declarations, load_params                          # noqa: E402

TASK = "cc_tasks/2026-10-07_seed_known_locations_verify.md"
CONFIG = REPO / "assessment" / "harness" / "scan" / "seeds" / "verification.yaml"
FRAME = REPO / "state" / "scan_targets_fss_2026-09_v5.json"
EVIDENCE = REPO / "corpus" / "evidence" / "frame"


def config() -> dict:
    """`seeds/verification.yaml`, read at call time."""
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _path(key: str) -> Path:
    return REPO / config()[key]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------------------------------------
# The checkpoint log and the evidence lane.
# --------------------------------------------------------------------------------------------

def logged() -> dict:
    """`{url: row}` from the fetch log, read at call time."""
    out, log = {}, _path("fetch_log")
    if log.is_file():
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                out[row["url"]] = row
    return out


def _append(row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def retain(body: bytes) -> tuple:
    d = hashlib.sha256(body).hexdigest()
    path = EVIDENCE / d[:2] / d
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(body)
    return d, str(path.relative_to(REPO))


def body_of(row: dict) -> bytes:
    """The retained bytes of a logged fetch, checked against the digest the row names."""
    if not row.get("retained_at"):
        return b""
    b = (REPO / row["retained_at"]).read_bytes()
    if hashlib.sha256(b).hexdigest() != row["sha256"]:
        raise SystemExit(f"REFUSING: {row['retained_at']} does not hash to {row['sha256']}")
    return b


#: When each host was last asked, in this process, for `_courtesy_wait`.
_LAST: dict = {}


def _courtesy_wait(fetcher, url: str) -> None:
    """Honour a host's `Crawl-delay` where it is longer than the standing rate.

    catalog.data.gov's robots.txt says `Crawl-Delay: 10`. The directive is not in RFC 9309
    (§2.2.4 lets a crawler interpret records it does not define), so the manners layer does not
    read it and runs every host at `requests_per_second_per_host`. A host that asks for ten
    seconds is asked every ten seconds here: the slower of the two always wins, and it costs this
    run minutes, not correctness. The delay is read through the Fetcher's own robots parse
    (`urllib.robotparser.RobotFileParser.crawl_delay`), so no second robots request is made."""
    import time
    parts = urllib.parse.urlsplit(url)
    fetcher.ensure_robots(url)
    rp = fetcher._robots_for(f"{parts.scheme}://{parts.netloc}")
    delay = None
    if rp is not None and hasattr(rp, "crawl_delay"):
        delay = rp.crawl_delay(fetcher.p["user_agent"])
    if not delay:
        return
    host = parts.netloc.lower()
    wait = float(delay) - (time.monotonic() - _LAST.get(host, -1e9))
    if wait > 0:
        time.sleep(wait)
    _LAST[host] = time.monotonic()


def fetch(url: str, fetcher, allowed_hosts: set, why: str) -> dict:
    """One GET through the manners layer, logged before it returns. A URL already on the log is
    not fetched again. A host outside the printed list is refused before any socket opens."""
    prior = logged().get(url)
    if prior is not None:
        return dict(prior, resumed=True)
    host = urllib.parse.urlsplit(url).netloc.lower()
    if host not in allowed_hosts:
        raise SystemExit(f"REFUSING: {url} is on {host}, which is not on the printed host list "
                         f"({_path('hosts_record').relative_to(REPO)}); run `hosts --amend` "
                         f"first so the list names it before the request")
    from scan.errors import RobotsDisallowed
    _courtesy_wait(fetcher, url)
    row = {"url": url, "task": TASK, "why": why, "fetched_at": now()}
    try:
        r = fetcher.raw_get(url)                  # robots-first: the Fetcher gates itself
        row.update(status=r["status"], final_url=r["final_url"], bytes=len(r["body"]),
                   content_type=(r["headers"].get("content-type") or "").split(";")[0]
                   .strip().lower(),
                   link_header=r["headers"].get("link"))
        if r["body"]:
            row["sha256"], row["retained_at"] = retain(r["body"])
    except RobotsDisallowed as exc:
        row.update(status=None, error=f"robots_disallowed: {exc}")
    except Exception as exc:                       # recorded as a row, never swallowed
        row.update(status=None, error=f"{type(exc).__name__}: {exc}")
    _append(row, _path("fetch_log"))
    return row


def record_run(fetcher, cmd: str) -> None:
    """The socket count of one invocation, robots reads and retries included
    (`manners.Fetcher.requests`), for the RESULT's requests-per-host table."""
    run = {"at": now(), "cmd": cmd, "requests": dict(fetcher.requests),
           "robots": [{k: r.get(k) for k in ("netloc", "status", "decision")}
                      for r in fetcher.robots_log]}
    _append(run, _path("runs_log"))
    print(json.dumps({"cmd": cmd, "requests": sum(fetcher.requests.values()),
                      "hosts": len(fetcher.requests)}))


# --------------------------------------------------------------------------------------------
# The host list.
# --------------------------------------------------------------------------------------------

def seed_table() -> dict:
    return yaml.safe_load(_path("seed_table").read_text(encoding="utf-8"))


def frame_bodies() -> dict:
    """`{code: {agency_name, parent_department, host}}` for the 16 Tier A bodies."""
    out = {}
    for r in json.loads(FRAME.read_text(encoding="utf-8"))["rows"]:
        if r.get("tier", "A") == "A":
            out.setdefault(r["agency"], {"agency_name": r["agency_name"],
                                         "parent_department": r.get("parent_department"),
                                         "host": r["host"]})
    return out


def base_hosts() -> list:
    """The task's list: every host the seed table names, catalog.data.gov, api.data.gov, and
    the 16 roster hosts."""
    t = seed_table()
    hosts = set(t["hosts"]) | {"catalog.data.gov", "api.data.gov"}
    hosts |= {h for b in t["bodies"].values() for h in b["roster_hosts"]}
    return sorted(hosts)


def allowed_hosts() -> set:
    rec = _path("hosts_record")
    if not rec.is_file():
        raise SystemExit("REFUSING: no host list has been printed yet; run `hosts` first")
    d = json.loads(rec.read_text(encoding="utf-8"))
    return set(d["hosts"]) | {h for a in d.get("amendments") or [] for h in a["hosts"]}


def cmd_hosts(amend: list | None = None, reason: str | None = None) -> int:
    rec = _path("hosts_record")
    if amend:
        d = json.loads(rec.read_text(encoding="utf-8"))
        new = sorted(set(amend) - allowed_hosts())
        if not new:
            print("no new host")
            return 0
        d.setdefault("amendments", []).append({"at": now(), "hosts": new, "why": reason})
        rec.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
        print(f"AMENDED host list (+{len(new)}), before any request to them: {', '.join(new)}")
        print(f"  why: {reason}")
        return 0
    hosts = base_hosts()
    if rec.is_file():
        d = json.loads(rec.read_text(encoding="utf-8"))
        if d["hosts"] != hosts:
            raise SystemExit("REFUSING: a different host list was already recorded")
    else:
        d = {"task": TASK, "printed_at": now(), "rule": (
            "every host the seed table names (its `hosts`), catalog.data.gov, api.data.gov and "
            "the 16 roster hosts"), "hosts": hosts}
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
    print(f"HOST LIST ({len(hosts)}), printed before the first request, {d['printed_at']}:")
    for h in hosts:
        print(f"  {h}")
    for a in d.get("amendments") or []:
        print(f"  AMENDMENT {a['at']}: {', '.join(a['hosts'])} ({a['why']})")
    return 0


# --------------------------------------------------------------------------------------------
# data.gov (decision 1).
# --------------------------------------------------------------------------------------------

def _seedlib():
    """`scripts/build_seed_table.py`, for the SAME `normalise`, `api_base_of` and body-host
    tests part 1 applied to every other source, so a data.gov seed is collapsed and attributed
    exactly as a repository citation was."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_build_seed_table",
                                                  REPO / "scripts" / "build_seed_table.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CATALOG = "https://catalog.data.gov"


def org_publishers(row: dict) -> dict:
    """`{publisher: count}` an organization page lists in its publisher filter
    (`#publisher-chips` `data-contextual-counts`), or {} when the page is not served."""
    if row.get("status") != 200 or not row.get("retained_at"):
        return {}
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body_of(row), "html.parser")
    chips = soup.find(id="publisher-chips")
    if chips is None or not chips.get("data-contextual-counts"):
        return {}
    return json.loads(chips["data-contextual-counts"])


def body_publishers(code: str, names: dict, cfg: dict) -> list:
    """The publishers that are this body: a publisher name containing the frame's
    `agency_name` or one of the body's configured aliases, case-insensitive."""
    keys = [frame_bodies()[code]["agency_name"]] + list(
        (cfg["datagov"]["publisher_aliases"] or {}).get(code) or [])
    keys = [k.casefold() for k in keys]
    return sorted(n for n in names if any(k in n.casefold() for k in keys))


def search_url(org: str | None, publisher: str, per_page: int, after: list | None) -> str:
    """catalog.data.gov's own search, as its organization page's `hx-get` calls it, with the
    publisher filter its `filters_autocomplete.js` adds (`publisher`) and its cursor (`after`:
    base64 of the last result's `_sort`, JSON with no spaces)."""
    import base64
    q = [("q", ""), ("sort", "relevance")] + ([("org_slug", org)] if org else []) + [
        ("publisher", publisher), ("per_page", str(per_page))]
    if after is not None:
        q.append(("after", base64.b64encode(json.dumps(after, separators=(",", ":"))
                                            .encode()).decode()))
    return f"{CATALOG}/search?" + urllib.parse.urlencode(q)


def cmd_datagov(fetcher) -> int:
    cfg, lib, t = config(), _seedlib(), seed_table()
    allowed = allowed_hosts()
    dg = cfg["datagov"]
    formats = {f.casefold() for f in dg["api_formats"]}
    out_bodies, hosts = {}, set()
    org_rows: dict = {}
    # Every publisher the catalog knows, with its count (`/api/publishers`, the list the search
    # page's publisher filter loads). A body's records are not all under the organization the
    # part 1 table names: the `census` organization holds the Geography Division's TIGER
    # records, and the Census Bureau's API records are under `commerce` as "U.S. Census Bureau".
    # So each body's publishers are ALSO searched across every organization; a (organization,
    # publisher) pair already searched is not searched twice.
    prow = fetch(f"{CATALOG}/api/publishers", fetcher, allowed,
                 "catalog.data.gov: the publisher list its search filter loads")
    all_pubs = ({p["name"]: p.get("count") for p in json.loads(body_of(prow)).get("publishers")
                 or [] if p.get("name")} if prow.get("status") == 200 else {})
    for code, b in t["bodies"].items():
        org = b["queries"]["catalog.data.gov"]["organization"]
        if org not in org_rows:
            org_rows[org] = fetch(f"{CATALOG}/organization/{org}", fetcher, allowed,
                                  f"catalog.data.gov: organization page ({org}), read for its "
                                  f"publishers")
        orow = org_rows[org]
        names = org_publishers(orow)
        pubs = body_publishers(code, names, cfg)
        cross = [p for p in body_publishers(code, all_pubs, cfg) if p not in pubs]
        runs, objs = [], {o: [] for o in declarations.SEED_OBJECTS}
        found: dict = {}
        for scope, pub in [(org, p) for p in pubs] + [(None, p) for p in cross]:
            expected = int((names if scope else all_pubs).get(pub) or 0)
            after, got, pages = None, 0, 0
            while pages < int(dg["max_pages"]):
                url = search_url(scope, pub, int(dg["rows"]), after)
                row = fetch(url, fetcher, allowed, f"catalog.data.gov: {code} records "
                                                   f"(organization {scope or 'any'}, "
                                                   f"publisher {pub})")
                pages += 1
                ok = row.get("status") == 200 and "json" in (row.get("content_type") or "")
                res = json.loads(body_of(row)).get("results") or [] if ok else []
                run = {"query": url, "status": row.get("status"), "results": len(res),
                       "error": row.get("error"), "api_bases": []}
                runs.append(run)
                for rec in res:
                    for dist in ((rec.get("dcat") or {}).get("distribution") or []):
                        if str(dist.get("format") or "").casefold() not in formats:
                            continue
                        for key in ("accessURL", "downloadURL"):
                            u = dist.get(key)
                            if not isinstance(u, str) or not u.startswith(("http://",
                                                                           "https://")):
                                continue
                            base = lib.normalise(lib.api_base_of(lib.normalise(u)))
                            if base not in run["api_bases"]:
                                run["api_bases"].append(base)
                            found.setdefault(base, {"examples": [], "records": 0})
                            found[base]["records"] += 1
                            if len(found[base]["examples"]) < 3 and u not in \
                                    found[base]["examples"]:
                                found[base]["examples"].append(u)
                got += len(res)
                if not res or got >= expected:
                    break
                after = res[-1].get("_sort")
        for base, info in sorted(found.items()):
            h = urllib.parse.urlsplit(base).netloc.lower()
            hosts.add(h)
            objs["api_base"].append({
                "url": base, "host": h,
                "seeded_from": sorted({f"catalog.data.gov:{r['query']}" for r in runs
                                       if base in r.get("api_bases", [])}),
                "status": "seeded_unverified",
                "on_body_host": lib.on_body(base, code, "api_base"),
                "records": info["records"], "examples": info["examples"],
                "note": ("the accessURL/downloadURL of a distribution whose format is "
                         + " or ".join(dg["api_formats"]) + ", collapsed to its API base "
                         "by build_seed_table.api_base_of")})
        org_url = f"{CATALOG}/organization/{org}"
        hosts.add("catalog.data.gov")
        objs["catalog_organization"].append({
            "url": org_url, "host": "catalog.data.gov",
            "seeded_from": [f"catalog.data.gov:{org_url}"], "status": "seeded_unverified"})
        out_bodies[code] = {
            "organization": org, "organization_page_status": orow.get("status"),
            "publishers_on_organization": len(names), "publishers_matched": pubs,
            "publishers_matched_in_other_organizations": cross,
            "runs": runs, "objects": objs,
            "no_seed": sorted(o for o, v in objs.items() if not v)}
    docs = fetch(dg["api_data_gov_docs"], fetcher, allowed,
                 "api.data.gov: the documentation index the seed table names")
    table = {
        "scheme": declarations.SEED_TABLE_SCHEME, "task": TASK,
        "generated_by": "scripts/verify_seeded_locations.py datagov",
        "generated_at": now(),
        "sources": {
            "catalog.data.gov": (
                "the CKAN action API the part 1 table names (`/api/3/action/package_search`, "
                "`organization_show`) answers 404 since the catalog was rebuilt; the same "
                "question is asked of the site's own search (`/search`, the endpoint its "
                "organization page calls), by organization and publisher, and every "
                "distribution whose format is API or Esri REST is a seed. Harvest records are "
                "served but name only a harvest source id, and `/harvest_source/<id>` answers "
                "404, so no harvested inventory URL is read from them"),
            "api.data.gov": (
                f"the documentation index the part 1 table names ({dg['api_data_gov_docs']}) "
                f"answers {docs.get('status')}; the site's own pages (/, /about/, "
                f"/docs/developer-manual/) list no API and no agency, so api.data.gov yields no "
                f"seed for any body")},
        "bodies": out_bodies,
        "hosts": sorted(hosts),
    }
    declarations.validate_seed_table(table)
    path = _path("datagov_table")
    head = ("# Seeds from catalog.data.gov and api.data.gov, per body and object. Generated by\n"
            "# scripts/verify_seeded_locations.py datagov (cc_tasks/2026-10-07_seed_known_\n"
            "# locations_verify.md decision 1). `classify` writes each seed's status. Do not edit\n"
            "# by hand.\n")
    path.write_text(head + yaml.safe_dump(table, sort_keys=False, allow_unicode=True,
                                          width=100), encoding="utf-8")
    new = sorted(hosts - allowed)
    print(json.dumps({"bodies": len(out_bodies), "api_seeds": {
        c: len(b["objects"]["api_base"]) for c, b in out_bodies.items()},
        "publishers": {c: b["publishers_matched"] for c, b in out_bodies.items()},
        "hosts_not_on_list": new}, indent=1))
    print(f"-> {path.relative_to(REPO)}")
    return 0


# --------------------------------------------------------------------------------------------
# Verify (decision 2): one GET per distinct seed URL, then a status per seed per object.
# --------------------------------------------------------------------------------------------

def datagov_table() -> dict:
    return yaml.safe_load(_path("datagov_table").read_text(encoding="utf-8"))


def all_seeds() -> list:
    """`[(table, body, object, seed)]` over both tables, in table order."""
    out = []
    for name, t in (("seed_table", seed_table()), ("datagov_table", datagov_table())):
        for code, b in t["bodies"].items():
            for obj, seeds in b["objects"].items():
                for e in seeds:
                    out.append((name, code, obj, e))
    return out


def cmd_verify(fetcher) -> int:
    allowed = allowed_hosts()
    urls = list(dict.fromkeys(e["url"] for _t, _c, _o, e in all_seeds()))
    off = sorted({urllib.parse.urlsplit(u).netloc.lower() for u in urls} - allowed)
    if off:
        raise SystemExit(f"REFUSING: seed host(s) not on the printed list: {off}; amend the "
                         f"list first (`hosts --amend ... --reason ...`)")
    done = logged()
    todo = [u for u in urls if u not in done]
    print(f"{len(urls)} distinct seed URLs; {len(urls) - len(todo)} already on the log; "
          f"{len(todo)} to fetch", flush=True)
    for i, u in enumerate(todo, 1):
        row = fetch(u, fetcher, allowed, "verify a seeded location by one GET (decision 2)")
        print(f"  [{i}/{len(todo)}] {row.get('status')} {u} "
              f"{row.get('error') or row.get('content_type')}", flush=True)
    return 0


def _visible_text(raw: bytes, content_type: str) -> str:
    """What a reader reads: visible text of HTML, text of a PDF, the body otherwise."""
    ct = (content_type or "").lower()
    if "pdf" in ct or raw[:5] == b"%PDF-":
        import io
        from pypdf import PdfReader
        try:
            return " ".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(raw)).pages)
        except Exception as exc:                  # an unreadable PDF reads as no text, named
            return f"<pdf unreadable: {type(exc).__name__}>"
    text = raw.decode("utf-8", "replace")
    if "html" in ct or "<html" in text[:2000].lower():
        from scan.rules import _text
        return _text.visible_text(text)
    return text


def machine_readable(raw: bytes) -> str | None:
    """`json` or `xml` when the body parses as one (an HTML document is not XML here), else
    None."""
    if not raw:
        return None
    try:
        json.loads(raw.decode("utf-8", "replace"))
        return "json"
    except Exception:
        pass
    head = raw.lstrip()[:200].lower()
    if head.startswith(b"<?xml") or (head.startswith(b"<") and not head.startswith(
            (b"<!doctype html", b"<html"))):
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            return None
        return None if root.tag.lower().endswith("html") else "xml"
    return None


def _same_or_under(final: str, seed: str) -> bool:
    strip = lambda u: urllib.parse.urlsplit(u)._replace(scheme="", query="",  # noqa: E731
                                                        fragment="").geturl().rstrip("/").lower()
    f, s_ = strip(final), strip(seed)
    return f == s_ or f.startswith(s_ + "/")


def classify(row: dict, code: str, obj: str, seed: dict, cfg: dict, lib, params: dict) -> tuple:
    """`(status, reason)` for one seed of one object, from its one fetch. Pure but for reading
    the retained body."""
    tests = cfg["tests"]
    url = seed["url"]
    if row is None:
        return "seeded_unverified", "not fetched"
    err = row.get("error") or ""
    st = row.get("status")
    if seed.get("kind") == "page_to_read":
        # A page the recollection SEARCHED for the object, recorded here so its search can be
        # repeated; it is where the object would be announced, never the object.
        return ("refused_robots" if err.startswith("robots_disallowed") else
                "seeded_unverified" if st is None else
                f"http_{st}" if st >= 400 else "not_the_object",
                f"a page searched for the {obj}, not a location of it (kind: page_to_read)")
    lib_obj = "inventory" if obj == "catalog_organization" else obj
    # The body's object lives on the body's hosts (part 1's `BODY_DOMAINS`, and its
    # department's for an inventory), judged on the SEED's URL: a seed off them is not the
    # body's object whatever it answers, and a redirect within the body's own lane (www.nsf.gov
    # to nsf-gov-resources.nsf.gov) does not move the location off it.
    if obj != "catalog_organization" and not lib.on_body(url, code, lib_obj):
        return "not_the_object", (f"{url} is not on a host of the body (build_seed_table."
                                  f"BODY_DOMAINS{'/DEPARTMENT_HOSTS' if obj == 'inventory' else ''})")
    if err.startswith("robots_disallowed"):
        return "refused_robots", f"robots.txt disallows it to this client ({err})"
    if st is None:
        return "seeded_unverified", f"the GET failed before any status ({err})"
    gone_or_refused = st >= 400 and not (
        obj == "api_base" and tests["api_machine_readable_4xx"] and st not in (404, 410)
        and st not in params["manners"]["unobservable_statuses"])
    if gone_or_refused:
        return f"http_{st}", f"answered HTTP {st}"
    raw = body_of(row)
    final = row.get("final_url") or url
    ct = row.get("content_type") or ""
    if obj == "api_base":
        mr = machine_readable(raw)
        if mr:
            return "verified", f"HTTP {st}, a machine-readable ({mr}) body at the base"
        if st >= 400:
            return f"http_{st}", f"answered HTTP {st} with no machine-readable body"
        text = _visible_text(raw, ct)
        named = any(re.search(rf"\b{re.escape(t)}\b", text) if t.isupper() else
                    t.lower() in text.lower() for t in tests["api_landing_tokens"])
        if "html" in ct and _same_or_under(final, url) and named:
            return "verified", f"HTTP {st}, an HTML page at the base that documents an API"
        return "not_the_object", (f"HTTP {st} {ct or 'no content type'}: not machine-readable"
                                  + ("" if _same_or_under(final, url) else
                                     f", and redirected away from the base to {final}")
                                  + ("" if named else ", and names no API"))
    if obj == "api_terms":
        text = _visible_text(raw, ct).lower()
        hit = next((ph for ph in tests["terms_phrases"] if ph in text), None)
        return (("verified", f"HTTP {st}, the page states terms (\"{hit}\")") if hit else
                ("not_the_object", f"HTTP {st}, no terms phrase in its text"))
    if obj == "changelog":
        text = _visible_text(raw, ct)
        dates = set()
        for pat in tests["date_patterns"]:
            dates |= set(re.findall(pat, text))
        n = len(dates)
        if n < int(tests["changelog_min_dates"]):
            return ("not_the_object", f"HTTP {st}, {n} distinct date(s); fewer than "
                                      f"{tests['changelog_min_dates']}")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")
        heads = ([soup.title.get_text(" ", strip=True)] if soup.title else []) + [
            h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2"])]
        tok = next((t for t in tests["changelog_heading_tokens"]
                    for h in heads if t in h.lower()), None)
        return (("verified", f"HTTP {st}, {n} distinct dated entries, headed as a log of "
                             f"changes (\"{tok}\")") if tok else
                ("not_the_object", f"HTTP {st}, {n} distinct dates, but neither its title nor "
                                   f"an h1/h2 names it a log of changes"))
    if obj in ("inventory", "catalog_organization"):
        host = urllib.parse.urlsplit(final).netloc.lower()
        if host == "catalog.data.gov" and urllib.parse.urlsplit(final).path.startswith(
                "/organization/"):
            return "verified", f"HTTP {st}, a catalog.data.gov organization listing"
        if obj == "catalog_organization":
            return "not_the_object", f"HTTP {st} at {final}, not an organization listing"
        try:
            doc = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            doc = None
        key = tests["inventory_dataset_key"]
        if isinstance(doc, dict) and isinstance(doc.get(key), list):
            return "verified", (f"HTTP {st}, parses as DCAT-US data.json "
                                f"({len(doc[key])} `{key}` records)")
        if isinstance(doc, dict) and doc.get("success") is True:
            return "verified", f"HTTP {st}, a CKAN action API listing"
        return "not_the_object", f"HTTP {st}, not a DCAT-US catalog or a CKAN listing"
    raise ValueError(obj)


def cmd_classify() -> int:
    cfg, lib, params = config(), _seedlib(), load_params()
    rows = logged()
    report, counts = [], Counter()
    for table, code, obj, e in all_seeds():
        row = rows.get(e["url"])
        st, why = classify(row, code, obj, e, cfg, lib, params)
        report.append({"table": table, "body": code, "object": obj, "url": e["url"],
                       "seeded_from": e.get("seeded_from"), "kind": e.get("kind"),
                       "status": st, "reason": why,
                       "verified_at": row.get("fetched_at") if row else None,
                       "fetch": {k: row.get(k) for k in ("status", "final_url", "content_type",
                                                          "bytes", "sha256", "retained_at",
                                                          "error")} if row else None})
        counts[(table, st)] += 1
    out = {"task": TASK, "generated_at": now(), "config": str(CONFIG.relative_to(REPO)),
           "fetch_log": cfg["fetch_log"], "seeds": report}
    _path("report").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    _write_statuses(report)
    print(json.dumps({f"{t}:{s}": n for (t, s), n in sorted(counts.items())}, indent=1))
    return 0


def _write_statuses(report: list) -> None:
    """Each seed's status (and `verified_at` beside it) into its table, nothing else: the part 1
    table's write set is statuses only, so the table is re-dumped with the settings
    `build_seed_table.render` used and its header kept, and a diff shows only those lines."""
    by = {(r["table"], r["body"], r["object"], r["url"]): r for r in report}
    for name in ("seed_table", "datagov_table"):
        path = _path(name)
        text = path.read_text(encoding="utf-8")
        head = "".join(l for l in text.splitlines(True) if l.startswith("#"))
        t = yaml.safe_load(text)
        for code, b in t["bodies"].items():
            for obj, seeds in b["objects"].items():
                for i, e in enumerate(seeds):
                    r = by[(name, code, obj, e["url"])]
                    new = {}
                    for k, v in e.items():
                        if k == "verified_at":
                            continue
                        new[k] = r["status"] if k == "status" else v
                        if k == "status" and r["status"] != "seeded_unverified":
                            new["verified_at"] = r["verified_at"]
                    seeds[i] = new
        declarations.validate_seed_table(t)
        path.write_text(head + yaml.safe_dump(t, sort_keys=False, allow_unicode=True,
                                              width=100), encoding="utf-8")


# --------------------------------------------------------------------------------------------
# Declare (decision 2): the statuses, written to `targets.yaml` `declared_locations`, scheme 2.
# --------------------------------------------------------------------------------------------

#: A status that leaves a location standing but unverified: the host refused this client, or
#: failed, or was never asked. `rules/_existence.py` makes each `error`, naming it.
UNVERIFIED = ("refused_robots", "seeded_unverified")
_REFUSED_HTTP = re.compile(r"^http_(401|403|407|429|5\d\d)$")


def _standing(status: str) -> bool:
    return status == "verified" or status in UNVERIFIED or bool(_REFUSED_HTTP.match(status))


def _rank(c: dict) -> tuple:
    """Tie-break among candidates of one class: https first, then the number of sources that
    named the location, then the model's stated confidence, then the URL."""
    conf = {"high": 0, "medium": 1, "low": 2}.get(c.get("confidence") or "", 3)
    return (not c["url"].startswith("https://"), -len(c["sources"]), conf, c["url"])


def _merged(report: list) -> dict:
    """`{(body, object, url): candidate}` over both tables: one status per location (one GET
    each, judged per object), every source that named it, and the seed's kind."""
    out: dict = {}
    for r in report:
        k = (r["body"], r["object"], r["url"])
        c = out.setdefault(k, {"url": r["url"], "status": r["status"], "reason": r["reason"],
                               "verified_at": r["verified_at"], "kind": r.get("kind"),
                               "seeded_from": [], "sources": set(), "confidence": None})
        for x in r.get("seeded_from") or []:
            if x not in c["seeded_from"]:
                c["seeded_from"].append(x)
            c["sources"].add(x.split(":", 1)[0])
        if c["status"] != r["status"]:
            raise SystemExit(f"REFUSING: {k} carries two statuses ({c['status']}, "
                             f"{r['status']}) from one GET")
    for t in (seed_table(), datagov_table()):
        for code, b in t["bodies"].items():
            for obj, seeds in b["objects"].items():
                for e in seeds:
                    if e.get("confidence") and (code, obj, e["url"]) in out:
                        out[(code, obj, e["url"])]["confidence"] = e["confidence"]
    return out


def _prov(c: dict | None, rec: dict | None = None) -> dict:
    """A location's scheme-2 provenance: the recollection's `read_from` where it wrote one,
    every seed source that named it, and the status of its one GET with the GET's time."""
    out = {}
    if rec and rec.get("read_from"):
        out["read_from"] = rec["read_from"]
    if c and c["seeded_from"]:
        out["seeded_from"] = list(c["seeded_from"])
    st = c["status"] if c else "seeded_unverified"
    out["status"] = st
    if st != "seeded_unverified":
        out["verified_at"] = c["verified_at"]
    return out


def searched(code: str, rec: dict, dg: dict) -> dict:
    """Which seed sources were searched for each object of one body (`declared_locations`
    scheme 2 `searched`, `rules/_existence.missing_sources`).

    * `model_knowledge` and `repo`: part 1 searched both for every body and object
      (`scripts/build_seed_table.py`; a seed it did not write is a location it did not find).
    * `developer_page`: the recollection read the body's pages for each object; it searched an
      object unless its record says the page that would carry it was `unreadable` (or it is
      still `unresolved`). The API's terms were searched where the API was: a body with no API
      has no API terms page to find (its terms row read "n/a").
    * `catalog.data.gov`: searched when the organization page and every publisher query
      answered 200 (`datagov` runs). Its records were read for every object; they carry API
      resources and nothing that is a terms page or a changelog.
    * `api.data.gov`: the index part 1 names answers 404 and the site's pages list no API and
      no agency (`datagov` table `sources`), so the source was searched and holds nothing.
    """
    blocked = {u["role"] for u in rec.get("unresolved") or []
               if u.get("status", "unresolved") in ("unreadable", "unresolved")}
    dev = {"api_base": "api_base" not in blocked,
           "changelog": "changelog" not in blocked,
           "inventory": not ({"own_host", "department", "catalog_organization"} & blocked)}
    dev["api_terms"] = dev["api_base"] and "api_terms" not in blocked
    b = dg["bodies"][code]
    cat = b["organization_page_status"] == 200 and all(r["status"] == 200 for r in b["runs"])
    out = {}
    for obj in declarations.SEARCH_OBJECTS:
        srcs = ["model_knowledge", "repo"] + (["developer_page"] if dev[obj] else []) + (
            ["catalog.data.gov"] if cat else []) + ["api.data.gov"]
        out[obj] = [x for x in declarations.SEED_SOURCES if x in srcs]
    return out


def _description_of(c: dict, lib) -> bool:
    """Whether a verified API seed's retained body IS an API description (OpenAPI 3.x or
    Swagger 2.0), by the test `RULE-A2-v5` applies."""
    row = logged().get(c["url"])
    if c["status"] != "verified" or not row:
        return False
    from scan.collectors import v2clauses
    from scan.rules.rule_a2_v5 import is_description
    return bool(is_description(v2clauses.api_declarations(body_of(row), {}, load_params())))


def declare_body(code: str, rec: dict, cands: dict, dg: dict, lib) -> tuple:
    """One body's scheme-2 entry and the choices made, in words."""
    notes = []
    mine = lambda obj: [c for (b, o, _u), c in cands.items()           # noqa: E731
                        if b == code and o == obj and c.get("kind") != "page_to_read"]
    by_url = lambda obj, u: cands.get((code, obj, u))                  # noqa: E731
    entry = {k: v for k, v in rec.items() if k not in ("api_base", "inventory_urls",
                                                      "changelog_urls")}
    entry["searched"] = searched(code, rec, dg)
    # ---- api_base: ONE location (scheme 2 holds one). The recollection's, where it still
    # stands; else a verified machine-readable base; else a base that exists in the record and
    # could not be read (an `error` is honest when the true base is unreadable, and a landing
    # page would make A2 judge a page that cannot carry the description); else a verified
    # documentation landing page; else none.
    ra = rec.get("api_base")
    api = None
    if ra:
        c = by_url("api_base", ra["url"])
        if c is None or _standing(c["status"]):
            api = dict(ra, **{k: v for k, v in _prov(c, ra).items() if k != "read_from"})
            notes.append(f"api_base: the recollection's {ra['url']} kept ({api['status']})")
        else:
            notes.append(f"api_base: the recollection's {ra['url']} is {c['status']}; "
                         f"replaced")
    if api is None:
        pool = mine("api_base")
        mr = sorted([c for c in pool if c["status"] == "verified"
                     and "machine-readable" in c["reason"]], key=_rank)
        unv = sorted([c for c in pool if c["status"] != "verified" and _standing(c["status"])],
                     key=_rank)
        land = sorted([c for c in pool if c["status"] == "verified" and c not in mr], key=_rank)
        pick = (mr or unv or land or [None])[0]
        if pick:
            api = dict({"url": pick["url"]}, **_prov(pick))
            notes.append(f"api_base: {pick['url']} ({pick['status']}; "
                         f"{'machine-readable' if pick in mr else 'unverified base' if pick in unv else 'landing page'}"
                         f" of {len(pool)} candidate(s))")
        else:
            notes.append(f"api_base: none standing of {len(pool)} candidate(s)")
    if api is not None:
        desc = sorted([c for c in mine("api_base") if _description_of(c, lib)
                       and urllib.parse.urlsplit(c["url"]).netloc
                       == urllib.parse.urlsplit(api["url"]).netloc], key=_rank)
        if desc and not api.get("description_url"):
            api["description_url"] = desc[0]["url"]
            notes.append(f"api_base.description_url: {desc[0]['url']}")
        # ---- terms, one location beside the base, chosen the same way.
        rt = api.get("terms_url")
        tc = by_url("api_terms", rt) if rt else None
        if rt and (tc is None or _standing(tc["status"])):
            api["terms"] = {k: v for k, v in _prov(tc).items()}
            notes.append(f"terms: the recollection's {rt} kept ({api['terms']['status']})")
        else:
            if rt:
                notes.append(f"terms: the recollection's {rt} is {tc['status']}; replaced")
                api.pop("terms_url", None)
                api.pop("terms_read_from", None)
            pool = mine("api_terms")
            ver = sorted([c for c in pool if c["status"] == "verified"], key=_rank)
            unv = sorted([c for c in pool if c["status"] != "verified"
                          and _standing(c["status"])], key=_rank)
            pick = (ver or unv or [None])[0]
            if pick:
                api["terms_url"] = pick["url"]
                api["terms"] = _prov(pick)
                notes.append(f"terms: {pick['url']} ({pick['status']} of {len(pool)})")
            else:
                notes.append(f"terms: none standing of {len(pool)} candidate(s)")
        entry["api_base"] = api
    # ---- the lists: every recollection entry (kept with its status), then every standing
    # seed not already listed.
    for field, obj in (("changelog_urls", "changelog"), ("inventory_urls", "inventory")):
        out = []
        for e in rec.get(field) or []:
            o = "inventory" if e.get("kind") != "catalog_organization" else "catalog_organization"
            c = by_url(o if field == "inventory_urls" else obj, e["url"])
            out.append(dict(e, **{k: v for k, v in _prov(c, e).items() if k != "read_from"}))
        have = {e["url"] for e in out}
        objs = (obj, "catalog_organization") if field == "inventory_urls" else (obj,)
        for o in objs:
            for c in sorted(mine(o), key=_rank):
                if c["url"] in have or not _standing(c["status"]):
                    continue
                have.add(c["url"])
                e = {"url": c["url"]}
                if field == "inventory_urls":
                    host = urllib.parse.urlsplit(c["url"]).netloc.lower()
                    e["kind"] = "catalog_organization" if o == "catalog_organization" \
                        else "data_json"
                    e["role"] = ("catalog_organization" if o == "catalog_organization" else
                                 "department" if host in lib.DEPARTMENT_HOSTS[code] else
                                 "own_host")
                e.update(_prov(c))
                out.append(e)
        if out:
            entry[field] = out
        notes.append(f"{field}: {len(out)} ({sum(1 for e in out if e['status'] == 'verified')}"
                     f" verified)")
    order = ["api_base", "inventory_urls", "changelog_urls", "unresolved",
             "department_is_own_host", "searched"]
    return {k: entry[k] for k in order if k in entry}, notes


def cmd_declare() -> int:
    cfg, lib = config(), _seedlib()
    report = json.loads(_path("report").read_text(encoding="utf-8"))["seeds"]
    cands = _merged(report)
    rec_block = declarations.load()
    if rec_block["scheme"] != 1:
        raise SystemExit("REFUSING: declared_locations is not the recollection's scheme 1; "
                         "this writes scheme 2 over it once")
    dg = datagov_table()
    bodies, notes = {}, {}
    for code, rec in rec_block["bodies"].items():
        bodies[code], notes[code] = declare_body(code, rec, cands, dg, lib)
    block = declarations.validate({"scheme": 2, "bodies": bodies})
    _write_targets(block)
    out = json.loads(_path("report").read_text(encoding="utf-8"))
    out["declared"] = {"written_at": now(), "notes": notes}
    _path("report").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for code, ns in notes.items():
        print(code)
        for n in ns:
            print(f"  {n}")
    return 0


#: Comments inside the block that the YAML round trip drops, re-inserted before the line they
#: annotate (body, key).
_BLOCK_COMMENTS = {
    ("DRSMSU", "department_is_own_host"): [
        "      # The parent (Board of Governors of the Federal Reserve System) publishes on the "
        "roster host itself, so the own-host",
        "      # inventory IS the department's: there is no second data.json to declare."],
    ("ORES", "department_is_own_host"): [
        "      # The parent (Social Security Administration) publishes on the roster host "
        "itself, so the own-host",
        "      # inventory IS the department's: there is no second data.json to declare."],
}


def _write_targets(block: dict) -> None:
    """`targets.yaml` with only its `declared_locations` block replaced, dumped in the file's
    own style (sequences indented under their key, no line wrapping), the two in-block
    comments re-inserted, and a dated paragraph added to the block's header comment."""
    path = declarations.TARGETS_PATH
    lines = path.read_text(encoding="utf-8").splitlines(True)
    i = next(k for k, l in enumerate(lines) if l.startswith("declared_locations:"))

    class _D(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    body = yaml.dump({"declared_locations": block}, Dumper=_D, sort_keys=False,
                     allow_unicode=True, width=10 ** 9, default_flow_style=False)
    out, cur = [], None
    for l in body.splitlines(True):
        m = re.match(r"^    ([A-Z]+):$", l.rstrip("\n"))
        if m:
            cur = m.group(1)
        m2 = re.match(r"^      ([a-z_]+):", l)
        if m2 and (cur, m2.group(1)) in _BLOCK_COMMENTS:
            out += [c + "\n" for c in _BLOCK_COMMENTS[(cur, m2.group(1))]]
        out.append(l)
    para = [
        "#\n",
        "# Scheme 2 since 2026-10-11 (`cc_tasks/2026-10-07_seed_known_locations_verify.md`\n",
        "# decision 2, DN-013-R1), written by `scripts/verify_seeded_locations.py declare`. Every\n",
        "# location the recollection read keeps its `read_from`; each seeded location carries\n",
        "# `seeded_from`; each carries the `status` of its one GET with `verified_at`\n",
        "# (`state/seed_verification_fetches_2026-10-11.jsonl`); and each body records, per object,\n",
        "# the seed sources `searched`, which is what lets an existence rule say `fail` over a\n",
        "# complete search (`rules/_existence.py`). A seed that answered 404, 410 or proved not to\n",
        "# be the object stays in the seed tables with its status and is not a location here.\n",
    ]
    head = lines[:i]
    if not any("Scheme 2 since 2026-10-11" in l for l in head):
        head = head + para
    path.write_text("".join(head + out), encoding="utf-8")
    if declarations.load() != declarations.validate(block):
        raise SystemExit("REFUSING: targets.yaml does not read back as the block written")


#: Where search responses are kept: local, untracked (`state/evidence_staging/` is gitignored).
SEARCH_LANE = REPO / "state" / "evidence_staging" / "seed_verification_2026-10-11"


def body_path(row: dict) -> Path | None:
    return (REPO / row["retained_at"]) if row.get("retained_at") else None


def cmd_relocate() -> int:
    """Move the catalog.data.gov SEARCH responses out of the committed frame lane.

    A search response is cited as "this query ran and returned N records" (the data.gov table's
    `runs`), never as the evidence for a location: the location's own GET is that. 101 of them
    are 526 MB (66,084 TIGER records on the `census` organization alone), and the repository's
    rule for captures cited only by URL and digest is that the bytes stay local and the digest
    is committed (`.gitignore`, the `corpus/scan/` lane: "bytes stay local, provenance survives
    ... via primary_url + content_hash"; constitution §6, no large data files). Each move is a
    row appended to the fetch log, carrying the original row's fields, the new path and the old
    one, so the last row for a URL says where its bytes are; nothing is deleted."""
    rows = logged()
    moved = 0
    for url, row in rows.items():
        if "/search?" not in url or not row.get("retained_at") \
                or row["retained_at"].startswith("state/"):
            continue
        src = body_path(row)
        dst = SEARCH_LANE / row["sha256"][:2] / row["sha256"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
        body_of(dict(row, retained_at=str(dst.relative_to(REPO))))   # hash checked
        _append(dict(row, retained_at=str(dst.relative_to(REPO)),
                     relocated_from=row["retained_at"], relocated_at=now(),
                     why="a search response, cited by its query and count, not committed"),
                _path("fetch_log"))
        moved += 1
    # A digest another (non-search) row still cites stays in the frame lane.
    keep = {r["retained_at"] for r in logged().values() if r.get("retained_at")}
    removed = 0
    for row in rows.values():
        if "/search?" in row["url"] and row.get("retained_at") \
                and not row["retained_at"].startswith("state/") \
                and row["retained_at"] not in keep and body_path(row).exists():
            body_path(row).unlink()
            removed += 1
    print(json.dumps({"relocated": moved, "frame_copies_removed": removed,
                      "lane": str(SEARCH_LANE.relative_to(REPO))}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hosts")
    h.add_argument("--amend", nargs="*", default=None)
    h.add_argument("--reason", default=None)
    sub.add_parser("datagov", help="run the data.gov queries and write the data.gov seed table")
    sub.add_parser("verify", help="GET every distinct seed URL once (resume by skip)")
    sub.add_parser("classify", help="statuses per seed per object; no network")
    sub.add_parser("declare", help="write targets.yaml declared_locations, scheme 2; no network")
    sub.add_parser("relocate", help="move search responses to the local, untracked lane")
    f = sub.add_parser("fetch", help="GET URLs through the manners layer (resume by skip)")
    f.add_argument("urls", nargs="+")
    f.add_argument("--why", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "hosts":
        if a.amend is not None and not a.reason:
            raise SystemExit("REFUSING: an amendment states why")
        return cmd_hosts(a.amend, a.reason)
    if a.cmd == "classify":
        return cmd_classify()
    if a.cmd == "declare":
        return cmd_declare()
    if a.cmd == "relocate":
        return cmd_relocate()
    from scan.manners import Fetcher
    fetcher = Fetcher(load_params())
    if a.cmd == "verify":
        rc = cmd_verify(fetcher)
        record_run(fetcher, "verify")
        return rc
    if a.cmd == "datagov":
        rc = cmd_datagov(fetcher)
        record_run(fetcher, "datagov")
        return rc
    if a.cmd == "fetch":
        allowed = allowed_hosts()
        for u in a.urls:
            row = fetch(u, fetcher, allowed, a.why)
            print(json.dumps({k: row.get(k) for k in ("url", "status", "final_url",
                                                       "content_type", "bytes", "error",
                                                       "resumed")}))
        record_run(fetcher, "fetch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
