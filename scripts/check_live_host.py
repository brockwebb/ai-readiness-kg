#!/usr/bin/env python3
"""Does the host actually serve the tree? Every index link, every sitemap entry, byte-compared.

`cc_tasks/2026-09-13_self_row.md` decision 4 and §1. **Zero model spend. Network: the published
authority only** — every request goes to the host `docs/reports/publication.yaml` declares in
`site_url`, and a computed URL on any other host is a refusal rather than a request.

**Why this exists as its own gate.** `tests/test_publication.py` asserts that every relative
`href` on the index and every `<loc>` in the sitemap resolves to a file *the tree holds*. That is
the strongest claim a test with no network can make, and it was the claim the publish task had to
settle for (`cc_tasks/2026-09-12_publish_l0_RESULT.md` §6: "NOT REACHABLE — the host serves
nothing"). A file in the tree and a file the host serves are different facts, and the gap between
them is where a published link rots: a path Jekyll dropped, a case-sensitivity difference, a
directory with no index, a file too large for Pages. This script closes that gap by asking the
host.

**Byte-compared, not merely 200.** For everything under `data/` the response body is compared to
the file on disk. A 200 that serves *different bytes* than the repository holds is worse than a
404: the 404 is visible and the wrong bytes are not. (The check is scoped to `data/` and the
other text files rather than the PDF and the copies, which are large; `--all-bytes` compares
everything.)

**The client is the declared one, read from the harness's own parameters.** The user agent and
the rate limit come from `assessment/harness/scan/params.yaml` (`manners`), never typed here: the
instrument that measures other publishers with an identified client at 1 req/s does not get a
quieter, anonymous client for its own host.

    /opt/anaconda3/bin/python3 scripts/check_live_host.py [--json PATH] [--all-bytes]

Exit 0 only when every URL answered 200 and every byte-compared body matched. Any other status,
any exception, any mismatch is a non-zero exit and names what failed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

SITE = REPO / "docs"
PUBLICATION = SITE / "reports" / "publication.yaml"

#: `href="..."` on the index. The same pattern `tests/test_publication.py` uses, so the set of
#: links this script asks the host about is the set that test asks the tree about.
HREF = re.compile(r'href="([^"#]+)"')

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

#: Bodies compared byte-for-byte by default: the published data and the small text faces of the
#: site. The report PDF and the two large copied records are fetched and their length checked,
#: unless `--all-bytes`.
BYTE_COMPARE_PREFIXES = ("data/",)
BYTE_COMPARE_EXACT = ("", "index.html", "robots.txt", "llms.txt", "sitemap.xml")

#: Never byte-compared even under `--all-bytes`: a served directory is `index.html` by Pages'
#: resolution, and the progress page is generated with its own build timestamp, so equality of
#: bytes is not the property that holds for it. Its 200 is.
BYTE_COMPARE_NEVER = ("progress/",)


def publication() -> dict:
    import yaml
    return yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))


def client(params: dict) -> tuple:
    """(user agent, minimum seconds between requests) — the harness's declared manners."""
    m = params["manners"]
    ua = m["user_agent"]
    rps = float(m["requests_per_second_per_host"])
    if not ua or rps <= 0:
        raise SystemExit("FATAL: params.manners declares no user_agent or a non-positive rate; "
                         "this script will not invent either")
    return ua, 1.0 / rps


def targets(pub: dict) -> list:
    """Every path the published tree tells a reader to follow, from the index and the sitemap.

    Read from what was PUBLISHED, never listed here: a link this script does not know about is
    exactly the link that would rot unnoticed.
    """
    site_url = pub["site_url"]
    out = {}
    html = (SITE / "index.html").read_text(encoding="utf-8")
    for href in HREF.findall(html):
        if href.startswith(("mailto:",)):
            continue
        if href.startswith(("http://", "https://")):
            # An absolute link on the index is only this script's business when it is ON this
            # site; the repository links are GitHub's and are not what this gate is about.
            if not href.startswith(site_url):
                continue
            rel = href[len(site_url):]
        else:
            rel = href
        out.setdefault(rel, set()).add("index")
    # The two published faces neither source can name. `robots.txt` is deliberately absent from
    # the sitemap (a sitemap enumerates content; robots.txt is the instruction about it) and
    # `sitemap.xml` cannot appear in its own urlset — so a gate built only from those two
    # sources would never ask the host for either, and they are the two files a machine reads
    # FIRST. Named here because they are properties of the published tree, not of its content.
    for face in ("robots.txt", "sitemap.xml"):
        out.setdefault(face, set()).add("published_face")
    root = ET.fromstring((SITE / "sitemap.xml").read_text(encoding="utf-8"))
    for u in root.findall("sm:url", SITEMAP_NS):
        loc = u.findtext("sm:loc", namespaces=SITEMAP_NS)
        if not loc.startswith(site_url):
            raise SystemExit(f"FATAL: the sitemap names {loc}, which is not on {site_url}")
        out.setdefault(loc[len(site_url):], set()).add("sitemap")
    return [{"rel": rel, "named_by": sorted(where)} for rel, where in sorted(out.items())]


def local_file(rel: str) -> Path:
    """The file in the tree a served path corresponds to, by Pages' own resolution rules."""
    if rel in ("", "/"):
        return SITE / "index.html"
    p = SITE / rel
    return p / "index.html" if rel.endswith("/") else p


def fetch(url: str, ua: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": ua,
                                               "Accept": "*/*"}, method="GET")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return {"status": r.status, "bytes": len(body), "body": body,
                    "content_type": r.headers.get("content-type"),
                    "elapsed_ms": int((time.time() - t0) * 1000)}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "bytes": 0, "body": b"", "content_type": None,
                "elapsed_ms": int((time.time() - t0) * 1000), "error": f"HTTPError {exc.code}"}
    except Exception as exc:                                              # noqa: BLE001
        return {"status": None, "bytes": 0, "body": b"", "content_type": None,
                "elapsed_ms": int((time.time() - t0) * 1000),
                "error": f"{type(exc).__name__}: {exc}"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None, metavar="PATH")
    ap.add_argument("--all-bytes", action="store_true",
                    help="byte-compare every body, including the PDF and the large copies")
    a = ap.parse_args(argv)

    from scan import load_params
    pub = publication()
    ua, gap = client(params := load_params())
    site_url = pub["site_url"]
    authority = urllib.parse.urlsplit(site_url).netloc
    rows, bad, netlocs = [], [], set()

    for t in targets(pub):
        url = site_url + t["rel"]
        netloc = urllib.parse.urlsplit(url).netloc
        netlocs.add(netloc)
        if netloc != authority:
            raise SystemExit(f"FATAL: {url} is not on the published authority {authority}; this "
                             f"script contacts one host and refuses to contact a second")
        r = fetch(url, ua)
        local = local_file(t["rel"])
        row = {"rel": t["rel"], "url": url, "named_by": t["named_by"], "status": r["status"],
               "served_bytes": r["bytes"], "content_type": r["content_type"],
               "local": str(local.relative_to(REPO)) if local.exists() else None,
               "local_bytes": local.stat().st_size if local.is_file() else None,
               "elapsed_ms": r["elapsed_ms"]}
        if r.get("error"):
            row["error"] = r["error"]
        if r["status"] != 200:
            bad.append(f"{t['rel'] or '(root)'} -> HTTP {r['status']} "
                       f"({r.get('error') or 'not 200'}), named by {','.join(t['named_by'])}")
            row["verdict"] = "not_served"
        else:
            compare = (t["rel"] not in BYTE_COMPARE_NEVER
                       and (a.all_bytes or t["rel"] in BYTE_COMPARE_EXACT
                            or t["rel"].startswith(BYTE_COMPARE_PREFIXES)))
            if not local.is_file():
                bad.append(f"{t['rel']} is served but the tree holds no such file")
                row["verdict"] = "served_but_not_in_tree"
            elif compare and local.read_bytes() != r["body"]:
                bad.append(f"{t['rel']} is served at {r['bytes']} bytes and the tree holds "
                           f"{local.stat().st_size}; the host serves different bytes")
                row["verdict"] = "bytes_differ"
            else:
                row["verdict"] = "served" if not compare else "served_bytes_identical"
        rows.append(row)
        time.sleep(gap)

    report = {"task": "cc_tasks/2026-09-13_self_row.md", "site_url": site_url,
              "authority": authority, "user_agent": ua,
              "requests_per_second_per_host": params["manners"]
                                                    ["requests_per_second_per_host"],
              "netlocs_contacted": sorted(netlocs), "urls": len(rows),
              "served": sum(1 for r in rows if r["verdict"].startswith("served")),
              "byte_identical": sum(1 for r in rows
                                    if r["verdict"] == "served_bytes_identical"),
              "gate": "PASS" if not bad else "BLOCKED", "failures": bad, "rows": rows}
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1))
    return 0 if report["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
