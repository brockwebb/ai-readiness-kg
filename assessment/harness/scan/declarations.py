"""Declared locations per body: where its API and its inventories are. DN-012 d3.

`cc_tasks/2026-10-06_absence_verdicts_rules.md` decision 4. spec:A2 says "the documented API
base" and the collector guessed three paths; ind:D4 says "data.gov/agency inventory" and the
collector read one host's `/data.json`. An absence verdict reached over a guess is not a
measurement of the product (DN-012 d1). This module is where the places the indicator names
are WRITTEN DOWN, with the page each was read from, so a rule can ask whether the search
reached them.

**The declaration travels on the evidence.** A collector that serves an `api_base` or
`inventory_urls` leg puts a `declared` block on every Observation of that leg (`record`), and
the rules read it from there. A rule is a pure function of its Observations and the params
(`rules/__init__`), so the declaration has to be IN them: a rule that reached into
`targets.yaml` would re-judge a stored cycle against today's declarations, and a re-derivation
would move whenever someone resolved a body. A stored cycle collected before this existed gets
the block from `scan/reread.py`, which records the declarations it applied on the payload, so
its re-derivation applies the same ones.

`load` is the only function here that touches the filesystem. Everything else is pure.
"""
from __future__ import annotations

import urllib.parse
from pathlib import Path

#: The shape of `targets.yaml` `declared_locations`, and of the `declared` block. A reader
#: checks the scheme before trusting any key.
SCHEME = 1

TARGETS_PATH = Path(__file__).resolve().parent / "targets.yaml"

#: What an inventory entry may be. A `data_json` is a Project Open Data catalog whose records
#: can be membership-tested; a `catalog_organization` is a catalog.data.gov organization page,
#: which lists a harvest source and is fetched to be observed, not membership-tested.
INVENTORY_KINDS = ("data_json", "catalog_organization")

#: The roles a declaration or an `unresolved` entry may name.
ROLES = ("api_base", "own_host", "department", "catalog_organization", "api_terms", "changelog")

#: Which `unresolved` roles belong to which field, so a leg's block carries only its own.
_ROLE_FIELD = {"api_base": "api_base", "api_terms": "api_terms", "changelog": "changelog_urls",
               "own_host": "inventory_urls", "department": "inventory_urls",
               "catalog_organization": "inventory_urls"}


class DeclarationError(ValueError):
    """`declared_locations` is malformed. Raised at load, never absorbed: a declaration the
    harness cannot read would turn every absence it governs into a silent guess again."""


def _url(v, where: str) -> str:
    if not isinstance(v, str) or urllib.parse.urlsplit(v).scheme not in ("http", "https") \
            or not urllib.parse.urlsplit(v).netloc:
        raise DeclarationError(f"{where}: {v!r} is not an absolute http(s) URL")
    return v


def validate(block: dict) -> dict:
    """The `declared_locations` block, checked field by field, or `DeclarationError`."""
    if not isinstance(block, dict) or block.get("scheme") != SCHEME:
        raise DeclarationError(f"declared_locations.scheme must be {SCHEME}; got "
                               f"{(block or {}).get('scheme')!r}")
    bodies = block.get("bodies")
    if not isinstance(bodies, dict):
        raise DeclarationError("declared_locations.bodies must be a map of body code -> entry")
    for code, b in bodies.items():
        where = f"declared_locations.bodies.{code}"
        if not isinstance(b, dict):
            raise DeclarationError(f"{where} must be a map")
        unknown = set(b) - {"api_base", "inventory_urls", "changelog_urls", "unresolved",
                            "department_is_own_host"}
        if unknown:
            raise DeclarationError(f"{where}: unknown field(s) {sorted(unknown)}")
        api = b.get("api_base")
        if api is not None:
            if not isinstance(api, dict):
                raise DeclarationError(f"{where}.api_base must be a map")
            _url(api.get("url"), f"{where}.api_base.url")
            for k in ("description_url", "terms_url"):
                if api.get(k) is not None:
                    _url(api[k], f"{where}.api_base.{k}")
            if not isinstance(api.get("read_from"), dict) or not api["read_from"].get("page"):
                raise DeclarationError(f"{where}.api_base carries no read_from.page; every "
                                       f"declaration names the page it was read from")
        for i, e in enumerate(b.get("inventory_urls") or []):
            w = f"{where}.inventory_urls[{i}]"
            if not isinstance(e, dict):
                raise DeclarationError(f"{w} must be a map")
            _url(e.get("url"), f"{w}.url")
            if e.get("kind") not in INVENTORY_KINDS:
                raise DeclarationError(f"{w}.kind {e.get('kind')!r} is not one of "
                                       f"{INVENTORY_KINDS}")
            if e.get("role") not in ROLES:
                raise DeclarationError(f"{w}.role {e.get('role')!r} is not one of {ROLES}")
            if not isinstance(e.get("read_from"), dict) or not e["read_from"].get("page"):
                raise DeclarationError(f"{w} carries no read_from.page")
        for i, e in enumerate(b.get("changelog_urls") or []):
            w = f"{where}.changelog_urls[{i}]"
            if not isinstance(e, dict):
                raise DeclarationError(f"{w} must be a map")
            _url(e.get("url"), f"{w}.url")
            if not isinstance(e.get("read_from"), dict) or not e["read_from"].get("page"):
                raise DeclarationError(f"{w} carries no read_from.page")
        for i, u in enumerate(b.get("unresolved") or []):
            w = f"{where}.unresolved[{i}]"
            if not isinstance(u, dict) or u.get("role") not in ROLES or not u.get("why"):
                raise DeclarationError(f"{w} must carry a role in {ROLES} and a why")
    return block


def load(path: Path | None = None) -> dict:
    """`targets.yaml` `declared_locations`, validated. Read at call time and never cached, the
    same rule every parameter follows: a cached declaration would leak into a later cycle."""
    import yaml
    doc = yaml.safe_load((path or TARGETS_PATH).read_text(encoding="utf-8")) or {}
    block = doc.get("declared_locations")
    if block is None:
        raise DeclarationError(f"{path or TARGETS_PATH} has no declared_locations block")
    return validate(block)


def for_body(block: dict, body) -> dict | None:
    """The declaration of one body, or `None` when the body declares nothing."""
    return (block.get("bodies") or {}).get(body) if body else None


def control_fixture(base_url: str, params: dict) -> dict:
    """The declaration of a control fixture served at `base_url`. A fixture is not a body; it
    declares the locations it serves, relative to its own port (`params.declarations`)."""
    cf = params["declarations"]["control_fixture"]
    base = base_url.rstrip("/")
    page = {"page": base_url, "how": "params.declarations.control_fixture"}
    return {"api_base": {"url": base + cf["api_base_path"],
                         "terms_url": base + cf["api_terms_path"], "read_from": page},
            "inventory_urls": [{"url": base + p, "kind": "data_json", "role": "own_host",
                                "read_from": page} for p in cf["inventory_paths"]],
            "changelog_urls": [{"url": base + p, "read_from": page}
                               for p in cf["changelog_paths"]],
            "unresolved": []}


def _field_of(leg: str, params: dict) -> str | None:
    """The declared field a leg reads, by `params.declarations`, or None."""
    d = params["declarations"]
    for key, field in (("api_base_legs", "api_base"), ("inventory_legs", "inventory_urls"),
                       ("terms_legs", "api_terms"), ("changelog_legs", "changelog_urls")):
        if leg in d[key]:
            return field
    return None


def record(decl: dict | None, body, leg: str, params: dict) -> dict | None:
    """The `declared` block a collector puts on every Observation of `leg`, or `None` for a leg
    that reads no declared location.

    A body that declares nothing gets a block too, saying so: `api_base: None` is a recorded
    fact ("nothing was declared when this was collected"), where a missing block means the
    Observation predates declarations altogether, and the rules word the two differently.
    """
    field = _field_of(leg, params)
    if field is None:
        return None
    decl = decl or {}
    # D1's field is the API's terms endpoint, so an unresolved API base is its remainder too.
    wanted = {field} | ({"api_base"} if field == "api_terms" else set())
    unresolved = [u for u in (decl.get("unresolved") or []) if _ROLE_FIELD[u["role"]] in wanted]
    out = {"scheme": SCHEME, "body": body, "field": field, "unresolved": unresolved}
    if field in ("api_base", "api_terms"):
        out["api_base"] = decl.get("api_base")
    elif field == "inventory_urls":
        out["inventory_urls"] = list(decl.get("inventory_urls") or [])
        out["department_is_own_host"] = bool(decl.get("department_is_own_host"))
    else:
        out["changelog_urls"] = list(decl.get("changelog_urls") or [])
    return out


def admitted_hosts(decl: dict | None, leg: str, params: dict) -> frozenset:
    """The declared hosts `manners.on_roster_host` admits for `leg` of this body: the
    `api_base` host for the API legs, every `inventory_urls` host for the inventory legs, and
    nothing for any other leg."""
    field = _field_of(leg, params)
    if not decl or field is None:
        return frozenset()
    api = decl.get("api_base") or {}
    if field == "api_base":
        urls = [api.get("url"), api.get("description_url")]
    elif field == "api_terms":
        urls = [api.get("terms_url")]
    elif field == "inventory_urls":
        urls = [e["url"] for e in decl.get("inventory_urls") or []]
    else:
        urls = [e["url"] for e in decl.get("changelog_urls") or []]
    return frozenset(urllib.parse.urlsplit(u).netloc.lower() for u in urls if u)
