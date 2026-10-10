"""A13 v1 — DISCOVERABILITY: from the product page, can a machine reach what the body publishes?

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 3, DN-013-R1. A
CANDIDATE indicator (DD-054): its Findings sit on the matrix and enter no level and no score
(`docs/design/scoring_model.md`, "Candidate indicators and the ladder").

*A machine client starting from the product page reaches the body's API, its terms, its changelog
and its inventory without being told where they are.*

Existence (A2, D1, F4, D4) asks whether each object is published, at the locations recorded for
the body (`_existence.py`). This asks the other half of what the harness used to measure as one
thing: whether a client that knows only the product page gets there. Four objects, judged one by
one (`per_object`), then combined into the surface's verdict.

**Per object** (API, API terms, changelog, inventory):

* `not_applicable` — the object is not shown to exist: every recorded location answered 404/410
  or was recorded as naming no object, and every seed source was searched. Nothing to discover.
* `error` — whether it exists is not settled (a recorded location unverified, or seed sources
  not searched); or the product page was not served or its links were not read; or, for an
  object with a convention location, that location was not fetched.
* `pass` — the object exists (an Observation at a recorded location was served, or the record
  says `verified`), and either one of its recorded URLs is among the product page's links (on-host
  or off-host, and past the link probe's cap: an href on the page is reachable whether or not the
  harness probed it; for the API, any link into the API base), or it sits at a documented
  convention location:
  - the API: `/.well-known/api-catalog` on the product page's host served as a Linkset, or a
    `Link: <…>; rel="api-catalog"` header on the product page (RFC 9727, June 2025, §2 and §3);
  - the inventory: the recorded inventory IS `/data.json` at the root of the product page's host
    (OMB M-13-13 and the Project Open Data metadata schema; M-25-05 §4a iii repeats the address).
* `fail` — the object exists, the page was read whole, and neither holds.

**The surface's verdict** is the first that applies of: any object `fail` (a client demonstrably
cannot reach an object that exists); any `error`; any `pass`; otherwise `not_applicable`. A `fail`
on one object is established whatever another object's state, so `error` elsewhere does not mask
it; every object's state is in the reason.

**Evidence, all of it already collected by other legs** (`CONSUMES`): the product page
Observation of the shared link probe (its `links` and its response headers, never its probed
links: `CONSUMES_PAGE_ONLY`), and the A2, D1, F4 and D4 Observations, which carry the body's
recorded locations (`declared`) and the fetches of them. A12 is the other candidate. The API's
convention location, `/.well-known/api-catalog`, is read from any consumed Observation that
targets it; no collector fetches it yet, so the API's convention branch is `error` "not fetched"
until one does (the task's part 2).
"""
from __future__ import annotations

from . import _common as c
from . import _existence as ex
from ._scope import _same

RULE_ID, LEG = "RULE-A13-v1", "A13"

#: The page's link set comes from the shared link probe; the recorded locations and their fetches
#: from the four existence legs.
CONSUMES = ("link_probe", "A2", "D1", "F4", "D4")

#: Read the PAGE of these shared legs, never their dereferences: a fixture that blinds the link
#: probe's HEADs leaves this rule's evidence whole (`fixture_expectations.leg_probes`).
CONSUMES_PAGE_ONLY = ("link_probe",)

#: A `fail` says an object that exists is not reachable from the page: an absence claim.
CLAIM = "absence"
MEASURES = "product"

#: object -> (the existence record's object, its noun). Order is the reason's order.
OBJECTS = {"api": ("api_base", "the API"), "terms": ("api_terms", "the API's terms"),
           "changelog": ("changelog", "the changelog"), "inventory": ("inventory",
                                                                      "the inventory")}

#: Most decisive first: how per-object verdicts combine into the surface's.
_PRECEDENCE = ("fail", "error", "pass", "not_applicable")


def _page(observations: list):
    """The product page Observation: the link probe's fetch of the surface itself."""
    pages = [o for o in observations if o.leg == "link_probe"
             and (o.parsed or {}).get("probe") != "link"]
    return pages[0] if pages else None


def _root(url: str) -> str:
    return str(url or "").split("://", 1)[0] + "://" + c.host_of(url)


def _link_rels(headers: dict) -> list:
    """`[(target, rel)]` from an RFC 8288 `Link` header, by string work."""
    out = []
    h = {k.lower(): v for k, v in (headers or {}).items()}.get("link") or ""
    for part in h.split(","):
        if "<" not in part or ">" not in part:
            continue
        target = part[part.index("<") + 1:part.index(">")].strip()
        for p in part[part.index(">") + 1:].split(";"):
            k, _, v = p.strip().partition("=")
            if k.strip().lower() == "rel":
                out += [(target, r) for r in v.strip().strip('"').lower().split()]
    return out


def _is_object(o, obj: str, params: dict, entry: dict | None = None) -> bool:
    """An Observation at a recorded location that IS the object, by the test the object's
    existence leg applies to what it finds there: a JSON document at the API base (the API is
    present; whether it is DESCRIBED is A2's question, not this one), a catalog that was read as
    one for the inventory, and a served page for terms and changelog. A soft-404 shell served at
    an API base or an inventory path is not the object."""
    if not c.served(o) or c.unobserved(o, params):
        return False
    p = o.parsed or {}
    if obj == "api_base":
        return bool((p.get("api") or {}).get("openapi_parsed"))
    if obj == "inventory" and (entry or {}).get("kind") != "catalog_organization":
        return bool(p.get("present"))
    # Terms, changelog, and a catalog.data.gov organization page (`declarations.INVENTORY_KINDS`:
    # fetched to be observed, never membership-tested): a served page is the object.
    return True


def _exists(observations: list, decl, obj: str, params: dict):
    """`(state, entries)`: `yes` with the live entries an Observation or the record verifies,
    `no` when nothing is shown to exist over a complete search, `unknown` with the remainder."""
    live = ex.live(observations, decl, obj, params)
    shown = []
    for e in live:
        hits = [o for o in ex.at(observations, e, under=(obj == "api_base"))
                if o.leg == {"api_base": "A2", "api_terms": "D1", "changelog": "F4",
                             "inventory": "D4"}[obj]]
        if e.get("status") == "verified" or any(_is_object(o, obj, params, e) for o in hits):
            shown.append(e)
    if shown:
        return "yes", shown
    rest = ex.remainder(observations, decl, obj, params)
    return ("unknown", rest) if rest else ("no", [])


def _linked(page_links: list, entry: dict, under: bool) -> str | None:
    for href in page_links:
        for u in entry["urls"]:
            if _same(href, u) or (under and str(href).lower().startswith(
                    u.rstrip("/").lower() + "/")):
                return href
    return None


def per_object(observations: list, params: dict) -> dict:
    """`{object: {"verdict", "reason"}}` for the four objects. Pure; the surface's Finding is
    built from it, and a delta table can call it over the same stored Observations."""
    conv = params["discoverability"]["convention"]
    decl = ex.declared(observations)
    page = _page(observations)
    page_ok = (page is not None and c.served(page) and not c.unobserved(page, params)
               and isinstance((page.parsed or {}).get("links"), list)
               and not (page.parsed or {}).get("links_error"))
    links = [l.get("href") if isinstance(l, dict) else l
             for l in ((page.parsed or {}).get("links") or [])] if page_ok else []
    page_url = page.target_url if page is not None else None
    out = {}
    for name, (obj, noun) in OBJECTS.items():
        state, got = _exists(observations, decl, obj, params)
        if state == "no":
            out[name] = {"verdict": "not_applicable",
                         "reason": f"{noun}: not shown to exist ({ex.search(decl, obj, params)})"}
            continue
        if state == "unknown":
            out[name] = {"verdict": "error",
                         "reason": f"{noun}: existence not settled: {'; '.join(got)}"}
            continue
        hit = next((h for e in got for h in [_linked(links, e, obj == "api_base")] if h), None)
        if hit:
            out[name] = {"verdict": "pass",
                         "reason": f"{noun}: linked from the product page ({hit})"}
            continue
        # The convention locations.
        if name == "api" and page_ok:
            rel = [t for t, r in _link_rels((page.response or {}).get("headers"))
                   if r == conv["api_catalog_link_rel"]]
            if rel:
                out[name] = {"verdict": "pass",
                             "reason": f"{noun}: the product page sends Link rel="
                                       f"\"{conv['api_catalog_link_rel']}\" to {rel[0]} "
                                       f"(RFC 9727 §3)"}
                continue
        if name == "inventory" and page_url:
            at_root = _root(page_url) + conv["inventory_path"]
            if any(_same(u, at_root) for e in got for u in e["urls"]):
                out[name] = {"verdict": "pass",
                             "reason": f"{noun}: at the convention location {at_root} "
                                       f"(OMB M-13-13)"}
                continue
        if not page_ok:
            why = ("the product page was not observed" if page is None else
                   "the product page was not served or its links were not read")
            out[name] = {"verdict": "error", "reason": f"{noun}: exists, and {why}"}
            continue
        if name == "api":
            want = _root(page_url) + conv["api_catalog_path"]
            seen = [o for o in observations if _same(o.target_url, want)
                    and not c.unobserved(o, params)]
            if not seen:
                out[name] = {"verdict": "error",
                             "reason": f"{noun}: exists, is not linked from the product page, "
                                       f"and the convention location {want} was not fetched"}
                continue
            ct = str(((seen[0].response or {}).get("headers") or {}).get(
                "content-type", "")).split(";")[0].strip().lower()
            if c.served(seen[0]) and ct in conv["api_catalog_media_types"]:
                out[name] = {"verdict": "pass",
                             "reason": f"{noun}: an API catalog is served at {want} ({ct}; "
                                       f"RFC 9727 §2)"}
                continue
        where = {"api": f", and no API catalog is served at "
                        f"{_root(page_url)}{conv['api_catalog_path']}",
                 "inventory": f", and it is not at {_root(page_url)}{conv['inventory_path']}"
                 }.get(name, "")
        out[name] = {"verdict": "fail",
                     "reason": f"{noun}: exists at {got[0]['url']} and is not reachable from the "
                               f"product page: not among its {len(links)} link(s){where}"}
    return out


def judge(observations: list, params: dict):
    obs = [o for o in observations if o.leg in CONSUMES and not (
        o.leg == "link_probe" and (o.parsed or {}).get("probe") == "link")]
    if not obs:
        return c.empty(RULE_ID, LEG, params)
    each = per_object(obs, params)
    verdict = next(v for v in _PRECEDENCE if any(r["verdict"] == v for r in each.values()))
    lead = {"fail": "an object that exists is not reachable from the product page",
            "error": "discoverability is not established for every object",
            "pass": "every object that exists is reachable from the product page",
            "not_applicable": "no object is shown to exist, so there is nothing to discover"
            }[verdict]
    return c.make(RULE_ID, LEG, obs, verdict,
                  f"{lead}: " + "; ".join(f"{k} {r['verdict']} ({r['reason']})"
                                          for k, r in each.items()), params)
