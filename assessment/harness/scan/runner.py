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

from . import declarations
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


def _with_declared(obs: list, block) -> list:
    """Every Observation of a declaration-reading leg carries the body's `declared` block
    (`declarations.record`), so the rule judging them can ask whether the search reached the
    places the body declared without reaching outside its arguments."""
    if block is not None:
        for o in obs:
            o.parsed = dict(o.parsed or {}, declared=block)
    return obs


#: The collector of a product-page Observation READ from a stored cycle, never fetched
#: (`cc_tasks/2026-10-07_seed_known_locations_verify_ADDENDUM_01.md` A, base decision 4). Its
#: `obs_id` differs from the stored one because the collector and the params are this cycle's;
#: its `captured_at`, `request` and `response` are the stored Observation's, and
#: `parsed.read_from_cycle` names that Observation. `run.run_cycle` excludes it from E5's "every
#: control precedes the first real host" clock, because no host was asked for it in this cycle.
STORED_PAGE_COLLECTOR = "stored_page"
STORED_PAGE_VERSION = "0.1.0"
#: The page facts carried over. `link_candidates` is not: it counts the stored cycle's link
#: PROBES, and this cycle probed none, so carrying it would put another cycle's requests on a
#: page Observation of this one. `declared` is not: this cycle's block is attached instead.
STORED_PAGE_KEYS = ("content_type", "final_url", "extension", "links", "links_error")


def stored_page(stored: dict, leg: str, doc_id: str, url: str, params: dict):
    """The link probe's product-page Observation for this surface, made from the Observation
    a stored cycle recorded for it (`target["stored_page"]`, set by `run.py --pages-from`). No
    request is made. Refuses a stored row of another surface or another URL."""
    from .model import Observation
    row = stored["row"]
    if row.get("target_doc_id") != doc_id or row.get("target_url") != url \
            or row.get("leg") != leg or (row.get("parsed") or {}).get("probe") == "link":
        raise ValueError(f"stored page {row.get('obs_id')} is not the {leg} page of "
                         f"{doc_id} at {url}")
    parsed = {k: row["parsed"][k] for k in STORED_PAGE_KEYS if k in (row.get("parsed") or {})}
    parsed["read_from_cycle"] = {"cycle": stored["cycle"], "obs_id": row["obs_id"],
                                 "captured_at": row["captured_at"]}
    return Observation.make(leg, leg, doc_id, url, STORED_PAGE_COLLECTOR, STORED_PAGE_VERSION,
                            params, dict(row.get("request") or {}),
                            dict(row.get("response") or {}), parsed=parsed,
                            error_class=row.get("error_class"),
                            captured_at=row["captured_at"])


def _convention_fetches(f, leg: str, doc_id: str, url: str, decl, params: dict,
                        admitted) -> list:
    """The discoverability candidate's convention locations (`RULE-A13-v1`), collected on A2
    because A13 reads only the legs it consumes and A2 is the API leg among them.

    For the product page's host and, where the body's recorded API base is `verified`, the API's
    host: RFC 9727's `/.well-known/api-catalog` (§2), and `/data.json` at the API host's root
    (OMB M-13-13; the product host's own `/data.json` is D4's fetch already, `d4_catalog.paths`,
    and is not asked for twice). Through the same gate every collector uses, robots-first.
    `ADDENDUM_01` A: "for each roster host and each verified API host"."""
    from .manners import on_roster_host
    conv = params["discoverability"]["convention"]
    roots = ["{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))]
    api = (decl or {}).get("api_base") or {}
    if api.get("url") and api.get("status") == "verified":
        api_root = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(api["url"]))
        if api_root.lower() != roots[0].lower():
            roots.append(api_root)
    out = []
    for i, root in enumerate(roots):
        of = "product_host" if i == 0 else "api_host"
        wanted = [(root + conv["api_catalog_path"], "api_catalog")]
        if of == "api_host":
            wanted.append((root + conv["inventory_path"], "convention_inventory"))
        for u, probe in wanted:
            if not on_roster_host(u, url, params, admitted):
                continue
            for o in http.fetch(f, leg, doc_id, u, params):
                o.parsed = dict(o.parsed or {}, probe=probe, convention_of=of)
                out.append(o)
    return out


def _terms_text(body: bytes, params: dict) -> dict:
    """The terms page as D1 stores it: the WHOLE body, decoded, up to the declared ceiling
    (`d1_sources.terms_text_max_bytes`; `ADDENDUM_01` A, "a truncated read is never judged").
    A page over the ceiling keeps its first `ceiling` bytes and says so, and `RULE-D1-v6`'s
    truncated-read branch makes that `error` ("read to N of its M bytes", N the ceiling). The
    body is stored as served, not as visible text: the rule reads visible text and the
    `license` links from it itself, and decides truncation by comparing what is kept with the
    bytes served, so a pre-stripped text would read as truncated on every page."""
    cap = int(params["d1_sources"]["terms_text_max_bytes"])
    over = len(body) > cap
    return {"terms_text": (body[:cap] if over else body).decode("utf-8", "replace"),
            "terms_text_ceiling": cap, "terms_text_truncated": over}


def _declared_api_urls(decl, already: list) -> list:
    """The declared API base and its description, where declared and not already probed."""
    api = (decl or {}).get("api_base") or {}
    return [u for u in (api.get("url"), api.get("description_url"))
            if u and u not in already]


def collect_leg(spec: dict, target: dict, params: dict, fetcher=None) -> list:
    from .manners import Fetcher, on_roster_host
    f = fetcher or Fetcher(params)
    leg, doc_id, url = spec["leg"], target["doc_id"], target["url"]
    base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    join = lambda p: urllib.parse.urljoin(base, p)          # noqa: E731
    # DN-012 d3 (`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4). The body's
    # declared locations, attached to the target by `run.targets` (or by `run.run_controls`
    # for a fixture). A target without the key declares nothing, and the leg's Observations say
    # so rather than guessing.
    decl = target.get("declared")
    body = target.get("agency")
    admitted = declarations.admitted_hosts(decl, leg, params)
    declared = declarations.record(decl, body, leg, params)

    lp = params["link_probe"]
    if leg == lp["shared_leg"] and target.get("stored_page") is not None:
        # Read, never re-fetched (`ADDENDUM_01` A; base decision 4): the product page this
        # surface's link probe recorded in a stored cycle, as THIS cycle's page Observation with
        # THIS cycle's `declared` block. No link is probed: only `RULE-A13-v1` reads this leg in
        # such a cycle, and it reads the page alone (`CONSUMES_PAGE_ONLY`).
        return _with_declared([stored_page(target["stored_page"], leg, doc_id, url, params)],
                              declared)
    if leg == lp["shared_leg"]:
        # The product page and every download link on it, observed ONCE per surface. A1 and A3
        # ask different questions of the same 25 objects; before this leg existed each HEADed
        # all of them independently, which is 559 duplicate requests against public federal
        # hosts in one cycle and no additional evidence (§1.3, and §0's manners note: RFC 9309
        # governs what may be fetched and licenses nothing about fetching it twice).
        page = http.fetch(f, leg, doc_id, url, params, parse_links=True)
        found = ((page[0].parsed or {}).get("links") or [])
        probed = links.probe(f, leg, doc_id, found, params, page_url=url, admitted=admitted)
        # The per-surface report (DN-012 d2): on-host candidates, probed, unprobed, cap. On the
        # page Observation, because it is a fact about the page's link set as a whole, and only
        # where the page's links were read: a page that was not HTML, or not served, offers no
        # candidate set to count.
        if isinstance(page[0].parsed, dict) and "links" in page[0].parsed:
            page[0].parsed = dict(page[0].parsed, link_candidates=links.account(
                probed, found, url, params, admitted))
        return _with_declared(page, declared) + probed
    if leg in lp["legs_served"]:
        # Nothing of their own: everything the CURRENT rules for these legs read is on the
        # shared leg above, which they declare through `CONSUMES`. The superseded rules that
        # collected here (`RULE-A1-v2`, `RULE-A3-v3`) stay in `REGISTRY` and are only ever
        # re-run against STORED observations by `rederive.py`, which never collects.
        return []
    if leg == "A2":
        out = []
        guessed = [join(p) for p in params["a9_m2m"]["probes"]
                   if "openapi" in p or "swagger" in p]
        # spec:A2 says GET "the documented API base". The guessed paths stay (a description
        # served at one is still a description), and the declared base and its description are
        # GOT as well, through the same gate every collector uses, admitted for this leg of
        # this body only.
        for u in guessed + [u for u in _declared_api_urls(decl, guessed)
                            if on_roster_host(u, url, params, admitted)]:
            obs = http.fetch(f, leg, doc_id, u, params)
            for o in obs:
                o.parsed = dict(o.parsed or {}, api=v2clauses.api_declarations(
                    _body(o), (o.response or {}).get("headers") or {}, params))
            out += obs
        out += _convention_fetches(f, leg, doc_id, url, decl, params, admitted)
        return _with_declared(out, declared)
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
        obs = robots.fetch(f, leg, doc_id, url, params)
        # D2 reads THIS observation through `CONSUMES = ("A4",)`
        # (`cc_tasks/2026-09-18_schema_field_rules.md` decision 6): the `Content-Signal`
        # directives in the file A4 already fetched, parsed from its stored body, so the host is
        # asked for `/robots.txt` once per surface for both legs.
        for o in obs:
            if (o.parsed or {}).get("present"):
                o.parsed = dict(o.parsed, content_signal=v2clauses.content_signals(
                    _body(o), url, params))
        return obs
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
        # spec:A9 names "OpenAPI at the documented base" among its entry points, so the declared
        # base is probed beside the conventional paths, as for A2.
        guessed = [join(p) for p in params["a9_m2m"]["probes"]]
        return _with_declared(
            [o for u in guessed + [u for u in _declared_api_urls(decl, guessed)
                                   if on_roster_host(u, url, params, admitted)]
             for o in http.fetch(f, leg, doc_id, u, params)], declared)
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
        # The token was a literal here; it is `params.b3_methodology.link_tokens` now, unchanged,
        # because `RULE-B3-v4` counts the same candidates to say how many were not followed.
        toks = params["b3_methodology"]["link_tokens"]
        # EVERY distinct candidate, in page order, up to the request bound
        # (`cc_tasks/2026-10-06_absence_verdicts_recollection_v2_ADDENDUM_01.md` amendment 2).
        # This collector used to follow the first and return, so a page linking several
        # methodology documents was judged on one, and `RULE-B3-v4` can only call that `error`.
        # The bound stays because manners bound requests (DN-012 d2); a candidate past it is not
        # followed, and the rule names it as the remainder, so the cap hides nothing. The set is
        # the rule's own (`rule_b3_v4._candidates`): distinct hrefs, first occurrence.
        cap = int(params["b3_methodology"]["max_followed"])
        seen: list = []
        for link in ((obs[0].parsed or {}).get("links") or []):
            href = link.get("href", "")
            if any(t in (href + link.get("text", "")).lower() for t in toks) \
                    and href not in seen:
                seen.append(href)
        for href in seen[:cap]:
            doc = http.fetch(f, leg, doc_id, href, params)
            for o in doc:
                _enrich_extent(o, params)
            obs += doc
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
                    o.parsed = dict(o.parsed or {}, probe="terms", **_terms_text(_body(o), params))
                obs += t
                # `.get("status", 999)` here is the same bug the four v3 rules exist for, and
                # it survived the rule fix because it lives in the COLLECTOR layer: it crashed
                # D1 on all three StatCan surfaces after StatCan began resetting connections
                # mid-cycle. A default fires on a MISSING key, never on a present one holding
                # `None`, and `status` is always present.
                st = (t[0].response or {}).get("status")
                if isinstance(st, int) and st < 400:
                    break
            # spec:D1's third source is "the API's terms endpoint". The paths above are this
            # harness's guesses at it on the product host; a DECLARED one (`api_base.terms_url`,
            # DN-012 d3) is read too, once, when it is not one of them.
            terms = ((decl or {}).get("api_base") or {}).get("terms_url")
            if terms and terms not in {o.target_url for o in obs} \
                    and on_roster_host(terms, url, params, admitted):
                t = http.fetch(f, leg, doc_id, terms, params)
                for o in t:
                    o.parsed = dict(o.parsed or {}, probe="terms", **_terms_text(_body(o), params))
                obs += t
        return _with_declared(obs, declared)
    if leg == "D4":
        obs = dcat.fetch_catalog(f, leg, doc_id, url, params)
        # ind:D4 says "data.gov/agency inventory": every DECLARED inventory is read too
        # (DN-012 d3), each once. A `data_json` entry is a catalog and is membership-tested
        # against the product; a `catalog_organization` page is fetched so that it is OBSERVED,
        # and tests nothing.
        fetched = {dcat.normalize_url(o.target_url, params) for o in obs}
        for e in (decl or {}).get("inventory_urls") or []:
            if dcat.normalize_url(e["url"], params) in fetched:
                continue
            fetched.add(dcat.normalize_url(e["url"], params))
            if not on_roster_host(e["url"], url, params, admitted):
                continue
            if e["kind"] == "data_json":
                obs += dcat.fetch_catalog_url(f, leg, doc_id, e["url"], url, params)
            else:
                obs += http.fetch(f, leg, doc_id, e["url"], params)
        _with_declared(obs, declared)
        from .manners import repo_root
        import json as _json
        for o in obs:
            if not (o.parsed or {}).get("present"):
                continue
            try:
                cat = _json.loads(_body(o).decode("utf-8", "replace"))
            except Exception as exc:
                # Recorded rather than skipped for the field legs: a served catalog that does
                # not parse holds no record a consumer can read a field from, and that is a
                # measurement, not an absence of one. `pod` stays unset exactly as before.
                o.parsed = dict(o.parsed, dcat_fields={
                    "scheme": v2clauses.DCAT_FIELDS_SCHEME, "parsed": False,
                    "reason": f"{type(exc).__name__}: {exc}"})
                continue
            o.parsed = dict(o.parsed, pod=v2clauses.pod_validation(cat, params, repo_root()))
            # The four DCAT-US field legs (B1, B4, D3, G4) read THIS observation through
            # `CONSUMES = ("D4",)`; the catalog is fetched once and read five ways.
            o.parsed = dict(o.parsed, dcat_fields=v2clauses.dcat_record_fields(cat, url, params))
        return obs
    if leg in params["dcat_fields"]["legs_served"]:
        # Nothing of their own, as for `link_probe.legs_served` above: every field these rules
        # read is on the D4 observation, which they declare through `CONSUMES`.
        return []
    if leg in params["schema_terms"]["legs_served"]:
        # Nothing of their own: B2 and B5 read the markup A6 already extracts (`parsed.raw`),
        # through `CONSUMES = ("A6",)` (`cc_tasks/2026-09-18_schema_field_rules.md`).
        return []
    if leg in params["content_signal"]["legs_served"]:
        # Nothing of its own: D2 reads the `content_signal` block on A4's robots.txt
        # observation, through `CONSUMES = ("A4",)`.
        return []
    if leg == "F4":
        out = []
        guessed = [join(p) for p in params["f4_changelog"]["paths"]]
        # spec:F4 says "any changelog or release-notes endpoint": a DECLARED one
        # (`changelog_urls`, DN-012 d3) is read beside the guessed paths.
        extra = [e["url"] for e in (decl or {}).get("changelog_urls") or []
                 if e["url"] not in guessed and on_roster_host(e["url"], url, params, admitted)]
        for u in guessed + extra:
            obs = http.fetch(f, leg, doc_id, u, params)
            for o in obs:
                o.parsed = dict(o.parsed or {}, changelog=v2clauses.changelog_entries(
                    _body(o), (o.parsed or {}).get("content_type") or "", params))
            out += obs
        return _with_declared(out, declared)
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
