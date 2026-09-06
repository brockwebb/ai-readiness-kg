"""Plain HTTP observation: fetch a URL, store the whole body, record what came back.

The workhorse behind A1, A2, A8, A9, B3, F4 and the D4 catalog fetch. It decides nothing —
`parsed` carries only mechanical facts (content type, extension, link list), and every
threshold that would turn those into a verdict lives in a rule.
"""
from __future__ import annotations

import urllib.parse

from ..model import Observation, store_evidence
from ..manners import error_class_for

VERSION = "0.1.0"


def _links(body: bytes, base_url: str) -> list:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        out.append({"href": urllib.parse.urljoin(base_url, a["href"]),
                    "text": " ".join(a.get_text().split())})
    return out


def fetch(fetcher, leg: str, doc_id: str, url: str, params: dict, parse_links: bool = False,
          spec_code: str | None = None) -> list:
    if not fetcher.allowed(url):
        return [Observation.make(spec_code or leg, leg, doc_id, url, "http", VERSION, params,
                                 {"method": "GET", "url": url,
                                  "ua": params["manners"]["user_agent"]},
                                 {"status": None, "headers": {}, "body_sha256": None,
                                  "body_path": None, "bytes": 0, "elapsed_ms": 0},
                                 parsed=None, error_class="robots_disallowed")]
    try:
        r = fetcher.raw_get(url)
    except Exception as exc:                                  # dns / timeout / transport
        cls = "timeout" if "timeout" in type(exc).__name__.lower() else "dns"
        return [Observation.make(spec_code or leg, leg, doc_id, url, "http", VERSION, params,
                                 {"method": "GET", "url": url,
                                  "ua": params["manners"]["user_agent"]},
                                 {"status": None, "headers": {}, "body_sha256": None,
                                  "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                  "error": f"{type(exc).__name__}: {exc}"},
                                 parsed=None, error_class=cls)]
    digest, path = store_evidence(r["body"])
    ctype = (r["headers"].get("content-type") or "").split(";")[0].strip().lower()
    parsed = {"content_type": ctype, "final_url": r["final_url"],
              "extension": urllib.parse.urlsplit(r["final_url"]).path.rsplit(".", 1)[-1].lower()
              if "." in urllib.parse.urlsplit(r["final_url"]).path else None}
    if parse_links and ctype.startswith("text/html"):
        try:
            parsed["links"] = _links(r["body"], r["final_url"])
        except Exception as exc:
            parsed["links_error"] = f"{type(exc).__name__}: {exc}"
    return [Observation.make(spec_code or leg, leg, doc_id, url, "http", VERSION, params,
                             {"method": "GET", "url": url,
                              "ua": params["manners"]["user_agent"]},
                             {"status": r["status"], "headers": r["headers"],
                              "body_sha256": digest, "body_path": path,
                              "bytes": len(r["body"]), "elapsed_ms": r["elapsed_ms"]},
                             parsed=parsed, error_class=error_class_for(r["status"]))]
