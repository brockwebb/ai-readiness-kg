"""Which collector observes which leg, and how one cycle runs. **No judgements here.**

The `v2` legs need evidence the scaffold never gathered — a per-link Content-Type, a SHACL
report, a dereferenced latest-vintage pointer, meta-robots, an RFC 8288 Link header, a POD
validation, parsed changelog entries, and the shallow extent features that answer "is there a
document here before JavaScript runs". Collecting is this module's job; every threshold that
turns those facts into a verdict lives in `params.yaml` and every verdict lives in a rule.
"""
from __future__ import annotations

import re
import urllib.parse

from .collectors import dcat, extent, http, lighthouse, links, robots, sitemap, structured_data
from .collectors import v2clauses


def _body(o):
    """The stored bytes for an observation, or b"". Content-addressed, so this is a read of
    evidence already on disk and never a second fetch."""
    p = (o.response or {}).get("body_path")
    if not p:
        return b""
    from .manners import repo_root
    try:
        return (repo_root() / p).read_bytes()
    except OSError:
        return b""


def _enrich_extent(o, params: dict) -> None:
    ct = ((o.parsed or {}).get("content_type") or "")
    if ct and not ct.startswith("text/"):
        return
    body = _body(o)
    if body:
        o.parsed = dict(o.parsed or {}, extent=extent.features(body, params))


def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
    from .manners import Fetcher
    f = fetcher or Fetcher(params)
    leg, doc_id, url = spec["leg"], target["doc_id"], target["url"]
    base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    join = lambda p: urllib.parse.urljoin(base, p)          # noqa: E731

    lp = params["link_probe"]
    if leg == lp["shared_leg"]:
        # The product page and every download link on it, observed ONCE per surface. A1 and A3
        # ask different questions of the same 25 objects; before this leg existed each HEADed
        # all of them independently, which is 559 duplicate requests against public federal
        # hosts in one cycle and no additional evidence (§1.3, and §0's manners note: RFC 9309
        # governs what may be fetched and licenses nothing about fetching it twice).
        page = http.fetch(f, leg, doc_id, url, params, parse_links=True)
        found = ((page[0].parsed or {}).get("links") or [])
        return page + links.probe(f, leg, doc_id, found, params, page_url=url)
    if leg in lp["legs_served"]:
        # Nothing of their own: everything the CURRENT rules for these legs read is on the
        # shared leg above, which they declare through `CONSUMES`. The superseded rules that
        # collected here (`RULE-A1-v2`, `RULE-A3-v3`) stay in `REGISTRY` and are only ever
        # re-run against STORED observations by `rederive.py`, which never collects.
        return []
    if leg == "A2":
        out = []
        for p in params["a9_m2m"]["probes"]:
            if "openapi" in p or "swagger" in p:
                obs = http.fetch(f, leg, doc_id, join(p), params)
                for o in obs:
                    o.parsed = dict(o.parsed or {}, api=v2clauses.api_declarations(
                        _body(o), (o.response or {}).get("headers") or {}, params))
                out += obs
        return out
    if leg == "A12":
        # The two layers, observed against the SAME path so the comparison is real. A12 judges
        # a host, and the path it probes is the one the target row names — the agency's
        # flagship where it has one, the host root where it does not.
        obs = robots.fetch(f, leg, doc_id, url, params)
        probe = http.fetch(f, leg, doc_id, url, params)
        for o in probe:
            o.parsed = dict(o.parsed or {}, probe="a12_target")
        return obs + probe
    if leg == "A4":
        return robots.fetch(f, leg, doc_id, url, params)
    if leg == "A5":
        r = robots.fetch(f, "A4", doc_id, url, params)
        declared = ((r[0].parsed or {}).get("sitemaps") or []) if r else []
        return sitemap.fetch(f, leg, doc_id, url, params, declared_sitemaps=declared)
    if leg == "A6":
        obs = structured_data.fetch(f, leg, doc_id, url, params)
        from .manners import repo_root
        for o in obs:
            if (o.parsed or {}).get("raw"):
                o.parsed = dict(o.parsed, shacl=v2clauses.shacl_report(
                    o.parsed["raw"], params, repo_root()))
        return obs
    if leg == "A8":
        obs = structured_data.fetch(f, leg, doc_id, url, params)
        for o in obs:
            ptrs = v2clauses.find_latest_pointers(
                _body(o), o.target_url, (o.response or {}).get("headers") or {}, params)
            o.parsed = dict(o.parsed or {},
                            latest=v2clauses.follow_latest_pointer(
                                f, ptrs, params, surface_url=o.target_url))
        return obs
    if leg == "A9":
        return [o for p in params["a9_m2m"]["probes"]
                for o in http.fetch(f, leg, doc_id, join(p), params)]
    if leg == "A10":
        obs = lighthouse.fetch(f, leg, doc_id, url, params)
        for o in obs:
            body = _body(o)
            if not body:
                continue
            o.parsed = dict(o.parsed or {}, extent=extent.features(body, params),
                            error_shell_tokens=extent.looks_like_error_shell(
                                body, params["a10_shell"]["error_shell_tokens"]))
        return obs
    if leg == "A11-declared":
        obs = robots.fetch(f, leg, doc_id, url, params)
        # The signal names TWO declared-layer sources. The product page carries the second.
        page = http.fetch(f, leg, doc_id, url, params)
        for o in page:
            o.parsed = dict(o.parsed or {}, meta=v2clauses.meta_robots(_body(o), params))
        return obs + page
    if leg == "B3":
        obs = http.fetch(f, leg, doc_id, url, params, parse_links=True)
        for link in ((obs[0].parsed or {}).get("links") or []):
            if "methodolog" in (link.get("href", "") + link.get("text", "")).lower():
                doc = http.fetch(f, leg, doc_id, link["href"], params)
                for o in doc:
                    _enrich_extent(o, params)
                return obs + doc
        return obs
    if leg == "D1":
        obs = structured_data.fetch(f, leg, doc_id, url, params)
        for o in obs:
            o.parsed = dict(o.parsed or {}, **v2clauses.licence_link_header(
                (o.response or {}).get("headers") or {}, o.target_url, params))
        # Source 3: the terms endpoint. Probed only if the first two sources found nothing —
        # a licence already read is not worth three more requests against a public host.
        if not any((o.parsed or {}).get("licence_in_link_header") for o in obs):
            for p in params["d1_sources"]["terms_paths"][
                    :int(params["d1_sources"]["max_terms_probed"])]:
                t = http.fetch(f, leg, doc_id, join(p), params)
                for o in t:
                    o.parsed = dict(o.parsed or {}, probe="terms",
                                    terms_text=_body(o).decode("utf-8", "replace")[:20000])
                obs += t
                # `.get("status", 999)` here is the same bug the four v3 rules exist for, and
                # it survived the rule fix because it lives in the COLLECTOR layer: it crashed
                # D1 on all three StatCan surfaces after StatCan began resetting connections
                # mid-cycle. A default fires on a MISSING key, never on a present one holding
                # `None`, and `status` is always present.
                st = (t[0].response or {}).get("status")
                if isinstance(st, int) and st < 400:
                    break
        return obs
    if leg == "D4":
        obs = dcat.fetch_catalog(f, leg, doc_id, url, params)
        from .manners import repo_root
        import json as _json
        for o in obs:
            if not (o.parsed or {}).get("present"):
                continue
            try:
                cat = _json.loads(_body(o).decode("utf-8", "replace"))
            except Exception:
                continue
            o.parsed = dict(o.parsed, pod=v2clauses.pod_validation(cat, params, repo_root()))
        return obs
    if leg == "F4":
        out = []
        for p in params["f4_changelog"]["paths"]:
            obs = http.fetch(f, leg, doc_id, join(p), params)
            for o in obs:
                o.parsed = dict(o.parsed or {}, changelog=v2clauses.changelog_entries(
                    _body(o), (o.parsed or {}).get("content_type") or "", params))
            out += obs
        return out
    if leg == "G1-D":
        obs = http.fetch(f, leg, doc_id, url, params)
        toks = params["g1d_uncertainty"]["field_tokens"]
        for o in obs:
            body_path = (o.response or {}).get("body_path")
            if not body_path:
                continue
            from .manners import repo_root
            try:
                text = (repo_root() / body_path).read_bytes().decode("utf-8", "replace").lower()
            except Exception:
                continue
            # Structured FIELD, not prose. Where the field lives depends on the surface, and
            # the first smoke run failed all 17 surfaces by looking only at `<th>`: a StatCan
            # CSV declares its standard errors in the header ROW and has no HTML at all.
            ct = ((o.parsed or {}).get("content_type") or "")
            if ct.startswith("text/html") or "<th" in text:
                field_text = " ".join(re.findall(r"<th[^>]*>(.*?)</th>", text, re.S))
            elif ct.startswith("text/csv") or ct.startswith("application/csv"):
                field_text = text.split("\n", 1)[0]
            elif "json" in ct:
                # A JSON API declares its fields as keys; the Census API returns a header row
                # as the first array element.
                field_text = text[:4000]
            else:
                field_text = text.split("\n", 1)[0]
            o.parsed = dict(o.parsed or {},
                            uncertainty_field_source=ct or "unknown",
                            uncertainty_tokens=[t for t in toks if t.lower() in field_text])
        return obs
    raise KeyError(f"no collector wired for leg {leg!r}")
