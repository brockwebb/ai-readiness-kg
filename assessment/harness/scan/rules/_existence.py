"""Does the object EXIST? Read only from the locations declared or seeded for the body. **Pure.**

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1:
*existence is not discoverability.* Generation 14 (`_scope.py`) asked whether the SEARCH an
absence verdict stood on was complete, and searched where a stranger would: the product page's
links, guessed paths on the product host, and the locations a body's own pages declare. That
measured two things at once. Whether an agency publishes an API, its terms, a changelog or an
inventory is one question; whether a machine starting from the product page can find them is
another (the candidate discoverability indicator, `rule_a13.py`). A failed stranger's search was
reported as the absence of the thing.

**The existence legs** (A2, D1, F4, D4 and D4's consumers B1, B4, D3, G4) read only the locations
`targets.yaml` `declared_locations` records for the body, whether read from the agency's own pages
(`read_from`, the recollection's scheme 1) or seeded from a named source (`seeded_from`, scheme 2:
model knowledge, this repository's citations, catalog.data.gov, api.data.gov). The link probe, the
guessed paths and the link cap feed none of them. Three verdicts:

* `pass` — an Observation at a recorded location served the object (the caller's test).
* `error` — a recorded location exists and was not verified: refused, forbidden by robots.txt,
  answered 401/403/429/5xx, timed out, recorded `seeded_unverified`, or never fetched. The
  remainder names it (`remainder`).
* `fail` — every recorded location was observed and none is the object, AND every seed source in
  `params.existence.seed_sources` was searched for this body and this object (the declared block's
  `searched`). That makes `fail` a complete search over named sources, which is DN-012 d1's
  standard (DN-013 ADDENDUM 01 A1). A scheme-1 block records no search, so its absences stay
  `error`, naming the sources not searched.

A seed whose recorded status says it named no object (`params.existence.gone_statuses`:
`not_the_object`, `http_404`, `http_410`) is not a candidate; an Observation of a recorded
location that answered 404 or 410 says the same thing about it.

**Prior art.** The scope limitation of ISA 705 / AU-C 705 and the open-world assumption, as
`_scope.py` and `_common.absence_verdict` cite them; and, for "complete over named sources", the
systematic-review convention that a negative search is reported with the sources searched and the
query run (PRISMA 2020 item 7, "Present the full search strategies for all databases"). A
`not_declared` entry already named its pages (`declarations.UNRESOLVED_STATUSES`); this extends
that to every seed source.
"""
from __future__ import annotations

from . import _common as c
from ._scope import _same, _unresolved

#: The `declared` block schemes this module reads (`scan.declarations.SCHEME` and its
#: predecessor). Restated, because a rule may not import `scan.declarations`; held equal by
#: `tests/test_existence_and_discoverability.py`.
DECLARED_SCHEMES = (1, 2)

#: The objects, the declared field each lives in, and the noun a reason uses.
OBJECTS = {"api_base": "documented API base", "api_terms": "API terms endpoint",
           "changelog": "changelog or release-notes location", "inventory": "inventory"}

#: An Observation status that says the location holds nothing.
_GONE_HTTP = (404, 410)


def declared(observations: list) -> dict | None:
    """The body's `declared` block, MERGED over the Observations that carry one (each leg's block
    holds only its own field, and a rule consuming several legs needs them together), or `None`
    when none does."""
    out: dict = {}
    for o in observations:
        d = (o.parsed or {}).get("declared") if isinstance(o.parsed, dict) else None
        if not (isinstance(d, dict) and d.get("scheme") in DECLARED_SCHEMES):
            continue
        for k, v in d.items():
            if k == "unresolved":
                seen = out.setdefault("unresolved", [])
                seen += [u for u in v or [] if u not in seen]
            elif k == "searched":
                for obj, srcs in (v or {}).items():
                    have = out.setdefault("searched", {}).setdefault(obj, [])
                    have += [s for s in srcs or [] if s not in have]
            elif v is not None and k not in out:
                out[k] = v
    return out or None


def entries(decl: dict | None, obj: str) -> list:
    """`[{url, status, seeded_from, read_from, ...}]` recorded for one object."""
    if not decl:
        return []
    api = decl.get("api_base") or {}
    if obj == "api_base":
        if not api.get("url"):
            return []
        return [dict(api, urls=[u for u in (api.get("url"), api.get("description_url")) if u])]
    if obj == "api_terms":
        if not api.get("terms_url"):
            return []
        prov = api.get("terms") or {}
        return [dict(prov, url=api["terms_url"], urls=[api["terms_url"]],
                     read_from=(prov.get("read_from") or api.get("terms_read_from")
                                or api.get("read_from")))]
    field = {"changelog": "changelog_urls", "inventory": "inventory_urls"}[obj]
    return [dict(e, urls=[e["url"]]) for e in decl.get(field) or [] if e.get("url")]


def at(observations: list, entry: dict, under: bool = False) -> list:
    """The Observations that target one recorded location (or, `under`, any path beneath it:
    a request into an API base reaches the API)."""
    out = []
    for o in observations:
        u = str(o.target_url or "")
        for e in entry["urls"]:
            if _same(u, e) or (under and u.lower().startswith(e.rstrip("/").lower() + "/")):
                out.append(o)
                break
    return out


def _gone(o) -> bool:
    return (o.response or {}).get("status") in _GONE_HTTP


def missing_sources(decl: dict | None, obj: str, params: dict) -> list:
    """The seed sources not recorded as searched for this object, in `params` order."""
    want = list(params["existence"]["seed_sources"])
    got = set(((decl or {}).get("searched") or {}).get(obj) or [])
    return [s for s in want if s not in got]


def _provenance(e: dict) -> str:
    seeded = e.get("seeded_from")
    if seeded:
        return "seeded from " + ", ".join(seeded if isinstance(seeded, list) else [seeded])
    page = (e.get("read_from") or {}).get("page")
    return f"read from {page}" if page else "provenance not recorded"


def live(observations: list, decl: dict | None, obj: str, params: dict) -> list:
    """The recorded locations still standing as candidates: not recorded as naming no object, and
    not observed answering 404/410."""
    gone = set(params["existence"]["gone_statuses"])
    out = []
    for e in entries(decl, obj):
        if e.get("status") in gone:
            continue
        hits = at(observations, e, under=(obj == "api_base"))
        if hits and all(_gone(o) for o in hits if not c.unobserved(o, params)) \
                and any(not c.unobserved(o, params) for o in hits):
            continue
        out.append(e)
    return out


def remainder(observations: list, decl: dict | None, obj: str, params: dict) -> list:
    """What stands between "nothing found" and an absence verdict, for one object: each
    candidate location not verified, and, when no candidate served the object, every seed source
    not searched. An empty list licenses the caller's `fail`.

    Called only after the caller found no location that serves the object, so every live
    candidate observed and served is one that was read and is not the object."""
    noun = OBJECTS[obj]
    if decl is None:
        return [f"the body's recorded locations are not on these Observations, so whether a "
                f"{noun} exists is unknown"]
    out = []
    for e in live(observations, decl, obj, params):
        hits = at(observations, e, under=(obj == "api_base"))
        seen = [o for o in hits if not c.unobserved(o, params)]
        if seen:
            continue
        if hits:
            out.append(f"the recorded {noun} {e['url']} could not be verified "
                       f"({hits[0].error_class or 'HTTP ' + str((hits[0].response or {}).get('status'))};"
                       f" {_provenance(e)})")
        elif e.get("status") and e.get("status") not in ("verified", "seeded_unverified"):
            out.append(f"the recorded {noun} {e['url']} could not be verified "
                       f"({e['status']}; {_provenance(e)})")
        else:
            out.append(f"the recorded {noun} {e['url']} was not fetched ({_provenance(e)})")
    gap = missing_sources(decl, obj, params)
    if gap:
        out.append(f"seed sources not searched for this body's {noun}: {', '.join(gap)}")
        out += _unresolved(decl)
    return out


def search(decl: dict | None, obj: str, params: dict) -> str:
    """The search a `fail` was reached over, in words, for its reason."""
    srcs = ", ".join(params["existence"]["seed_sources"])
    n = len(entries(decl, obj))
    return (f"every recorded {OBJECTS[obj]} read ({n}); seed sources searched: {srcs}"
            if n else f"no seed source records a {OBJECTS[obj]} (searched: {srcs})")


def recorded_only(observations: list, decl: dict | None, objs, params: dict) -> list:
    """The Observations at a recorded location of any of `objs`: what an existence leg may judge
    from. A guessed path that happens to equal a recorded location counts, because the location
    is recorded; every other guessed path is discoverability's evidence, never existence's."""
    keep = []
    for o in observations:
        for obj in objs:
            if any(at([o], e, under=(obj == "api_base")) for e in entries(decl, obj)):
                keep.append(o)
                break
    return keep


def read_recorded_inventory(observations: list, params: dict, read_inventory) -> dict:
    """`_dcat_fields.read_inventory` over the catalogs observed at RECORDED inventory locations
    only, for D4's four consumers (B1, B4, D3, G4), with the merged `declared` block on the
    result as `decl`. The product host's own `/data.json`, fetched by D4's collector whether or
    not anyone recorded it, is discoverability's convention location and reaches existence only
    when the body's record names it. No recorded catalog observed at all reads as `no_catalog`
    over every D4 Observation, so the caller's remainder decides between `error` and `fail`."""
    decl = declared(observations)
    d4 = [o for o in observations if o.leg == "D4"]
    st = read_inventory(recorded_only(d4, decl, ("inventory",), params), params)
    if st["kind"] == "empty" and d4:
        st = {"kind": "no_catalog", "obs": d4}
    return dict(st, decl=decl)
