"""The clause evidence the `v2` rules need and the `v1` collectors never gathered.

Task `cc_tasks/2026-09-06_scan_targets.md` §2. The 2026-09-06 rule review found that 12 of 16
`v1` rules implement only part of their `MeasurementSpec`'s signal. In most cases the missing
clause was not a missing branch in the rule — it was a fact nobody had collected. A rule is
pure and cannot go and look; this module is where the looking happens.

Every function here is a **pure parse of bytes already stored**, so it can be unit-tested
without a network and re-run over the evidence store without re-measuring anything. The one
exception is `follow_latest_pointer`, which by its nature must dereference, and takes a
fetcher for that reason.

Nothing here decides. Each function returns mechanical facts; every floor is in `params.yaml`
and every verdict is in a rule.
"""
from __future__ import annotations

import json
import re
import urllib.parse

VERSION = "0.1.0"


def _retain(params: dict, key: str):
    """A `reporting` parameter. Every one of these was an anonymous integer inside a collector
    until the §2.3 lint refused it — `msgs[:10]`, `low_text[:40]`, `round(frac, 4)`. None is a
    threshold; all of them shape what a reader sees, and a cap nobody can sweep is a cap nobody
    can question."""
    return (params.get("reporting") or {})[key]


# ------------------------------------------------------------------ A2: auth and rate limits
def api_declarations(body: bytes, headers: dict, params: dict) -> dict:
    """A2's signal: "record auth scheme, declared rate limits, and whether the description is
    machine-readable". `v1` recorded only the third.

    Auth and rate limits are declared in two places and both are read: the RESPONSE HEADERS
    (RFC 9110 `WWW-Authenticate`; the RateLimit header fields) and the DESCRIPTION itself
    (OpenAPI 3 `components.securitySchemes`, Swagger 2 `securityDefinitions`).
    """
    p = params["a2_api"]
    h = {k.lower(): v for k, v in (headers or {}).items()}
    out = {"auth_headers_seen": sorted(k for k in p["auth_headers"] if k in h),
           "rate_limit_headers_seen": sorted(k for k in p["rate_limit_headers"] if k in h),
           "openapi_parsed": False, "openapi_version": None,
           "auth_schemes_declared": [], "rate_limit_declared_in_description": False}
    try:
        doc = json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return out
    if not isinstance(doc, dict):
        return out
    out["openapi_parsed"] = True
    out["openapi_version"] = doc.get("openapi") or doc.get("swagger")
    blob = json.dumps(doc)
    comps = doc.get("components") if isinstance(doc.get("components"), dict) else {}
    for key in p["openapi_auth_keys"]:
        found = doc.get(key) or comps.get(key)
        if isinstance(found, dict) and found:
            out["auth_schemes_declared"] += sorted(found)
        elif isinstance(found, list) and found:
            out["auth_schemes_declared"] += [k for item in found
                                             if isinstance(item, dict) for k in item]
    out["auth_schemes_declared"] = sorted(set(out["auth_schemes_declared"]))
    out["rate_limit_declared_in_description"] = any(
        k.lower() in blob.lower() for k in p["openapi_rate_limit_keys"])
    return out


#: schema.org served as a STRING `@context` would make rdflib fetch https://schema.org to
#: expand it. A parse that reaches the network is not a parse: it would make a measurement
#: depend on a third-party host being up, it would make the control fixtures non-hermetic, and
#: it would break the promise that everything here is re-runnable over stored evidence. The
#: substitution is `@vocab`, which expands bare terms into the same namespace without a fetch.
_SCHEMA_ORG = re.compile(r"^https?://schema\.org/?$")


def _localise_context(node):
    if isinstance(node, list):
        return [_localise_context(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == "@context":
            if isinstance(v, str) and _SCHEMA_ORG.match(v.strip()):
                out[k] = {"@vocab": "https://schema.org/"}
                continue
            if isinstance(v, list):
                out[k] = [{"@vocab": "https://schema.org/"}
                          if isinstance(x, str) and _SCHEMA_ORG.match(x.strip()) else x
                          for x in v]
                continue
        out[k] = _localise_context(v)
    return out


# ------------------------------------------------------------------ A6: SHACL over the graph
def shacl_report(raw_markup: dict, params: dict, repo_root) -> dict:
    """A6's signal: "validate the DCAT graph against DCAT-AP SHACL shapes". `v1` matched a
    type name and stopped, so a graph declaring `Dataset` while violating every shape passed.

    The shapes are a stated MINIMAL subset — see the header of `shapes/dcat_ap_min.ttl` — and
    `shapes_profile` rides on the result so no reader can mistake a pass for DCAT-AP
    conformance. A graph pyshacl cannot load is `loaded: False`, which the rule reads as
    `error`: we failed to read it, the product did not fail.
    """
    p = params["a6_shacl"]
    out = {"loaded": False, "conforms": None, "violations": 0, "messages": [],
           "shapes_profile": p["shapes_profile"]}
    try:
        import rdflib
        from pyshacl import validate
        jsonld = (raw_markup or {}).get("json-ld") or []
        if not jsonld:
            return {**out, "reason": "no JSON-LD graph on the surface"}
        g = rdflib.Graph()
        g.parse(data=json.dumps(_localise_context(jsonld)), format="json-ld")
        shapes = rdflib.Graph()
        shapes.parse(str(repo_root / "assessment" / "harness" / "scan" / p["shapes_path"]),
                     format="turtle")
        conforms, results_graph, text = validate(g, shacl_graph=shapes, inference="none",
                                                 abort_on_first=False, meta_shacl=False,
                                                 advanced=False, debug=False)
        msgs = [ln.strip() for ln in (text or "").splitlines()
                if ln.strip().startswith("Message:")]
        return {**out, "loaded": True, "conforms": bool(conforms),
                "violations": len(msgs),
                "messages": msgs[:_retain(params, "validator_messages_retained")],
                "triples": len(g)}
    except Exception as exc:
        return {**out, "reason": f"{type(exc).__name__}: {exc}"}


# ------------------------------------------------------------------ A8: latest-vintage pointer
def find_latest_pointers(body: bytes, base_url: str, headers: dict, params: dict) -> list:
    """A8's signal has two clauses and `v1` implemented one: it read the declared date and
    never asked whether the latest-vintage pointer RESOLVES. This finds the candidates —
    RFC 8288 `Link` rels, href tokens, anchor text — and `follow_latest_pointer` dereferences
    them."""
    p = params["a8_latest"]
    html = body.decode("utf-8", "replace")
    found = []
    link_hdr = {k.lower(): v for k, v in (headers or {}).items()}.get("link") or ""
    for m in re.finditer(r'<([^>]+)>\s*;\s*([^,]*)', link_hdr):
        target, attrs = m.group(1), m.group(2).lower()
        rel = re.search(r'rel\s*=\s*"?([^";]+)', attrs)
        if rel and rel.group(1).strip() in p["link_rels"]:
            found.append({"how": f"Link header rel={rel.group(1).strip()}",
                          "url": urllib.parse.urljoin(base_url, target)})
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, text = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        low_href, low_text = href.lower(), " ".join(text.split()).lower()
        if any(t in low_href for t in p["href_tokens"]):
            found.append({"how": "href token", "url": urllib.parse.urljoin(base_url, href)})
        elif any(t in low_text for t in p["anchor_tokens"]):
            found.append({"how": f"anchor text "
                                 f"{low_text[:_retain(params, 'anchor_text_retained_chars')]!r}",
                          "url": urllib.parse.urljoin(base_url, href)})
    seen, uniq = set(), []
    for f in found:
        if f["url"] in seen:
            continue
        seen.add(f["url"])
        uniq.append(f)
    return uniq[:int(p["max_pointers_followed"])]


def follow_latest_pointer(fetcher, pointers: list, params: dict) -> dict:
    """Dereference. The only impure function in this module, because "does it resolve" cannot
    be answered from stored bytes."""
    p = params["a8_latest"]
    tried = []
    for ptr in pointers:
        if not fetcher.allowed(ptr["url"]):
            tried.append({**ptr, "status": None, "resolved": False,
                          "note": "robots_disallowed"})
            continue
        try:
            r = fetcher.raw_head(ptr["url"])
        except Exception as exc:
            tried.append({**ptr, "status": None, "resolved": False,
                          "note": f"{type(exc).__name__}"})
            continue
        ok = r["status"] in p["resolves_statuses"]
        tried.append({**ptr, "status": r["status"], "resolved": ok})
        if ok:
            break
    return {"pointers_found": len(pointers), "pointers_tried": tried,
            "latest_pointer_resolves": any(t["resolved"] for t in tried)}


# ------------------------------------------------------------------ A11: meta-robots
def meta_robots(body: bytes, params: dict) -> dict:
    """A11-declared's signal names TWO declared-layer sources — robots.txt **and** meta-robots
    directives — and `v1` read only the first, so a product page carrying
    `<meta name="robots" content="noindex,nofollow">` under a permissive robots.txt passed."""
    p = params["a11_meta"]
    html = body.decode("utf-8", "replace")
    directives = {}
    for m in re.finditer(r'<meta\b[^>]*>', html, re.I):
        tag = m.group(0)
        name = re.search(r'name\s*=\s*["\']?([^"\'>\s]+)', tag, re.I)
        content = re.search(r'content\s*=\s*["\']([^"\']*)', tag, re.I)
        if not name or not content:
            continue
        nm = name.group(1).lower()
        if nm in [x.lower() for x in p["meta_names"]]:
            directives[nm] = [t.strip().lower() for t in content.group(1).split(",")]
    restricting = sorted({t for toks in directives.values() for t in toks
                          if t in p["restricting_tokens"]})
    return {"meta_robots": directives, "meta_restricting_tokens": restricting,
            "meta_restricts": bool(restricting)}


# ------------------------------------------------------------------ D1: Link header + terms
def licence_link_header(headers: dict, base_url: str, params: dict) -> dict:
    """D1's signal names three licence sources — markup, an HTTP `Link` header, and the API's
    terms endpoint — and `v1` read only the markup, so a surface declaring its licence solely
    via `Link: <...>; rel="license"` (RFC 8288) was failed as having no licence at all."""
    p = params["d1_sources"]
    hdr = {k.lower(): v for k, v in (headers or {}).items()}.get("link") or ""
    hits = []
    for m in re.finditer(r'<([^>]+)>\s*;\s*([^,]*)', hdr):
        target, attrs = m.group(1), m.group(2).lower()
        rel = re.search(r'rel\s*=\s*"?([^";]+)', attrs)
        if rel and rel.group(1).strip() in p["link_header_rels"]:
            hits.append({"rel": rel.group(1).strip(),
                         "url": urllib.parse.urljoin(base_url, target)})
    return {"licence_link_header": hits, "licence_in_link_header": bool(hits)}


# ------------------------------------------------------------------ D4: POD v1.1 validation
def pod_validation(catalog: dict, params: dict, repo_root) -> dict:
    """D4's signal: "validate against the POD v1.1 schema". `v1` never gated on any validation
    result — the schema-derived counts were interpolated into the pass message only, so a
    catalog failing POD validation still passed as long as it existed and named the product.

    A REQUIRED-field subset; see the header of `shapes/pod_v1_1_min.schema.json`. Validation is
    on a bounded sample and the Finding records how many were checked, so nobody reads a sample
    as a census.
    """
    p = params["d4_validation"]
    out = {"validated": False, "schema_profile": p["schema_profile"]}
    try:
        import jsonschema
        schema = json.loads((repo_root / "assessment" / "harness" / "scan"
                             / p["schema_path"]).read_text(encoding="utf-8"))
    except Exception as exc:
        return {**out, "reason": f"{type(exc).__name__}: {exc}"}
    if not isinstance(catalog, dict):
        return {**out, "reason": "catalog is not a JSON object"}
    n = int(p["max_datasets_validated"])
    datasets = catalog.get("dataset")
    sample = datasets[:n] if isinstance(datasets, list) else []
    doc = {**{k: v for k, v in catalog.items() if k != "dataset"}, "dataset": sample}
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    return {**out, "validated": True, "conforms": not errors,
            "datasets_total": len(datasets) if isinstance(datasets, list) else 0,
            "datasets_validated": len(sample),
            "violations": len(errors),
            "messages": [f"{'/'.join(str(x) for x in e.path)}: {e.message}"
                         for e in errors[:_retain(params, "validator_messages_retained")]]}


# ------------------------------------------------------------------ F4: revision class
def changelog_entries(body: bytes, content_type: str, params: dict) -> dict:
    """F4's signal: "test whether it is machine-readable **and carries a revision class per
    entry**". `v1` stopped at the content type, so a JSON changelog with no change-class field
    passed."""
    p = params["f4_entries"]
    fields = [f.lower() for f in p["revision_class_fields"]]
    entries, classified = 0, 0
    if "json" in (content_type or ""):
        try:
            doc = json.loads(body.decode("utf-8", "replace"))
        except Exception:
            return {"entries": 0, "entries_classified": 0, "parse_failed": True}
        items = doc if isinstance(doc, list) else None
        if items is None and isinstance(doc, dict):
            for key in ("entries", "items", "releases", "changes", "changelog", "versions"):
                if isinstance(doc.get(key), list):
                    items = doc[key]
                    break
        items = items or []
        for it in items:
            if not isinstance(it, dict):
                continue
            entries += 1
            if any(k.lower() in fields for k in it):
                classified += 1
    else:
        text = body.decode("utf-8", "replace")
        for m in re.finditer(r"<(entry|item)\b.*?</\1>", text, re.S | re.I):
            entries += 1
            if re.search(r"<category\b", m.group(0), re.I):
                classified += 1
    frac = (classified / entries) if entries else 0.0
    return {"entries": entries, "entries_classified": classified,
            "classified_fraction": round(frac, _retain(params, "ratio_decimal_places")),
            "parse_failed": False}
