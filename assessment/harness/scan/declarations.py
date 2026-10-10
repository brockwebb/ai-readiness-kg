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

import re
import urllib.parse
from pathlib import Path

#: The shape of `targets.yaml` `declared_locations`, and of the `declared` block. A reader
#: checks the scheme before trusting any key.
#:
#: Scheme 2 (`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 5,
#: DN-013-R1) is scheme 1 plus provenance: an entry may be SEEDED from a named source rather than
#: read from the body's own page (`seeded_from`), carries what one live fetch found (`status`,
#: `verified_at`), and a body records which seed sources were searched per object (`searched`),
#: which is what lets an existence rule say `fail` over a complete search (`rules/_existence.py`).
#: No key scheme 1 defines changes meaning, so a scheme-1 file still loads and its `declared`
#: blocks are byte-identical to what they were.
SCHEME = 2
SCHEMES = (1, 2)

#: The seed sources (DN-013-R1; the task's decision 4), in the order a search names them. Equal
#: to `params.existence.seed_sources`, which the rules read; held equal by
#: `tests/test_existence_and_discoverability.py`. `developer_page` is the recollection's source,
#: the agency's own pages (`read_from`).
SEED_SOURCES = ("model_knowledge", "repo", "developer_page", "catalog.data.gov", "api.data.gov")

#: What one live fetch of a seeded location found. `http_<code>` is any HTTP status that is not
#: the object; `verified` is the object; `not_the_object` answered but is something else.
SEED_STATUSES = ("verified", "refused_robots", "not_the_object", "seeded_unverified")
_HTTP_STATUS = re.compile(r"^http_[1-5]\d\d$")

#: The objects a body's `searched` record and the seed table name. `catalog_organization` is
#: an inventory entry by kind; the seed table keeps it apart because data.gov keeps it apart.
SEED_OBJECTS = ("api_base", "api_terms", "changelog", "inventory", "catalog_organization")
SEARCH_OBJECTS = ("api_base", "api_terms", "changelog", "inventory")

TARGETS_PATH = Path(__file__).resolve().parent / "targets.yaml"

#: What an inventory entry may be. A `data_json` is a Project Open Data catalog whose records
#: can be membership-tested; a `catalog_organization` is a catalog.data.gov organization page,
#: which lists a harvest source and is fetched to be observed, not membership-tested.
INVENTORY_KINDS = ("data_json", "catalog_organization")

#: The roles a declaration or an `unresolved` entry may name.
ROLES = ("api_base", "own_host", "department", "catalog_organization", "api_terms", "changelog")

#: What an `unresolved` entry records (`cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md`
#: ADDENDUM_01 amendment 1). `unresolved`, the default, is a location nobody has looked for yet;
#: `not_declared` is one the body's own pages were searched for and do not publish; `unreadable`
#: is one the pages that would publish it refused to this client (HTTP 403, or robots.txt). The
#: last two name the pages searched, so the remainder a rule writes is a search a stranger can
#: repeat. All three keep the leg at `error` (DN-012 d1): what was not found is not absent.
UNRESOLVED_STATUSES = ("unresolved", "not_declared", "unreadable")

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


def _status(v, where: str) -> str:
    if v in SEED_STATUSES or (isinstance(v, str) and _HTTP_STATUS.match(v)):
        return v
    raise DeclarationError(f"{where}: status {v!r} is not one of {SEED_STATUSES} or http_<code>")


def _provenance(e: dict, where: str, scheme: int) -> None:
    """Scheme 1: `read_from.page`, always. Scheme 2: `read_from.page` or `seeded_from` (a
    non-empty list, each item naming its source before a colon), and, where a fetch was made,
    its `status` with `verified_at`."""
    read = isinstance(e.get("read_from"), dict) and bool(e["read_from"].get("page"))
    if scheme == 1:
        if not read:
            raise DeclarationError(f"{where} carries no read_from.page; every declaration "
                                   f"names the page it was read from")
        return
    seeded = e.get("seeded_from")
    if seeded is not None:
        if not isinstance(seeded, list) or not seeded or not all(
                isinstance(x, str) and x.split(":", 1)[0] in SEED_SOURCES for x in seeded):
            raise DeclarationError(f"{where}.seeded_from must be a non-empty list of "
                                   f"'<source>[:<detail>]' with source in {SEED_SOURCES}")
    if not read and not seeded:
        raise DeclarationError(f"{where} carries neither read_from.page nor seeded_from; every "
                               f"location names where it came from")
    if "status" in e:
        st = _status(e["status"], where)
        if st != "seeded_unverified" and not e.get("verified_at"):
            raise DeclarationError(f"{where} is {st} and carries no verified_at; a status is "
                                   f"the result of a fetch, and a fetch has a time")


def validate(block: dict) -> dict:
    """The `declared_locations` block, checked field by field, or `DeclarationError`."""
    if not isinstance(block, dict) or block.get("scheme") not in SCHEMES:
        raise DeclarationError(f"declared_locations.scheme must be one of {SCHEMES}; got "
                               f"{(block or {}).get('scheme')!r}")
    scheme = block["scheme"]
    bodies = block.get("bodies")
    if not isinstance(bodies, dict):
        raise DeclarationError("declared_locations.bodies must be a map of body code -> entry")
    for code, b in bodies.items():
        where = f"declared_locations.bodies.{code}"
        if not isinstance(b, dict):
            raise DeclarationError(f"{where} must be a map")
        allowed = {"api_base", "inventory_urls", "changelog_urls", "unresolved",
                   "department_is_own_host"} | ({"searched"} if scheme >= 2 else set())
        unknown = set(b) - allowed
        if unknown:
            raise DeclarationError(f"{where}: unknown field(s) {sorted(unknown)}")
        searched = b.get("searched")
        if searched is not None:
            if not isinstance(searched, dict) or set(searched) - set(SEARCH_OBJECTS):
                raise DeclarationError(f"{where}.searched must map objects in "
                                       f"{SEARCH_OBJECTS} to the seed sources searched")
            for obj, srcs in searched.items():
                if not isinstance(srcs, list) or set(srcs) - set(SEED_SOURCES):
                    raise DeclarationError(f"{where}.searched.{obj} must list sources in "
                                           f"{SEED_SOURCES}")
        api = b.get("api_base")
        if api is not None:
            if not isinstance(api, dict):
                raise DeclarationError(f"{where}.api_base must be a map")
            _url(api.get("url"), f"{where}.api_base.url")
            for k in ("description_url", "terms_url"):
                if api.get(k) is not None:
                    _url(api[k], f"{where}.api_base.{k}")
            _provenance(api, f"{where}.api_base", scheme)
            terms = api.get("terms")
            if terms is not None:
                if scheme < 2 or not isinstance(terms, dict) or not api.get("terms_url"):
                    raise DeclarationError(f"{where}.api_base.terms is scheme 2 provenance for "
                                           f"a terms_url and must be a map beside one")
                if terms.get("seeded_from") or terms.get("read_from"):
                    _provenance(terms, f"{where}.api_base.terms", scheme)
                elif "status" in terms:
                    _status(terms["status"], f"{where}.api_base.terms")
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
            _provenance(e, w, scheme)
        for i, e in enumerate(b.get("changelog_urls") or []):
            w = f"{where}.changelog_urls[{i}]"
            if not isinstance(e, dict):
                raise DeclarationError(f"{w} must be a map")
            _url(e.get("url"), f"{w}.url")
            _provenance(e, w, scheme)
        for i, u in enumerate(b.get("unresolved") or []):
            w = f"{where}.unresolved[{i}]"
            if not isinstance(u, dict) or u.get("role") not in ROLES or not u.get("why"):
                raise DeclarationError(f"{w} must carry a role in {ROLES} and a why")
            status = u.get("status", "unresolved")
            if status not in UNRESOLVED_STATUSES:
                raise DeclarationError(f"{w}.status {status!r} is not one of "
                                       f"{UNRESOLVED_STATUSES}")
            if status != "unresolved":
                pages = u.get("pages_searched")
                if not isinstance(pages, list) or not pages:
                    raise DeclarationError(f"{w} is {status} and names no pages_searched; a "
                                           f"search that names no page cannot be repeated")
                for j, pg in enumerate(pages):
                    _url(pg, f"{w}.pages_searched[{j}]")
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
    """The declaration of one body, or `None` when the body declares nothing. A scheme-2 entry
    carries its scheme (`scheme: 2`) so `record` stamps it on the evidence; a scheme-1 entry is
    returned as it always was, so its blocks are byte-identical."""
    entry = (block.get("bodies") or {}).get(body) if body else None
    if entry is not None and block.get("scheme", 1) >= 2:
        return dict(entry, scheme=block["scheme"])
    return entry


def control_fixture(base_url: str, params: dict) -> dict:
    """The declaration of a control fixture served at `base_url`. A fixture is not a body; it
    declares the locations it serves, relative to its own port (`params.declarations`)."""
    cf = params["declarations"]["control_fixture"]
    base = base_url.rstrip("/")
    page = {"page": base_url, "how": "params.declarations.control_fixture"}
    # Scheme 2, with every seed source searched for every object: a fixture is its own world and
    # what it declares is all there is, so its absence branches stay reachable under the
    # existence rules (`rules/_existence.py`) exactly as they were under generation 14.
    return {"scheme": SCHEME,
            "searched": {o: list(SEED_SOURCES) for o in SEARCH_OBJECTS},
            "api_base": {"url": base + cf["api_base_path"],
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
    scheme = decl.get("scheme", 1)
    out = {"scheme": scheme, "body": body, "field": field, "unresolved": unresolved}
    if scheme >= 2:
        objs = {"api_base": ("api_base",), "api_terms": ("api_terms", "api_base"),
                "inventory_urls": ("inventory",), "changelog_urls": ("changelog",)}[field]
        out["searched"] = {o: list((decl.get("searched") or {}).get(o) or []) for o in objs}
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


#: The shape of the seed table (`assessment/harness/scan/seeds/known_locations_*.yaml`).
SEED_TABLE_SCHEME = 1


def validate_seed_table(table: dict) -> dict:
    """The seed table, checked, or `DeclarationError`. A seed names its URL, the host it lives
    on, where it came from (`seeded_from`, every source in `SEED_SOURCES`) and its status; the
    table's `hosts` covers every seed's host, because part 2 generates its fetch list from it."""
    if not isinstance(table, dict) or table.get("scheme") != SEED_TABLE_SCHEME:
        raise DeclarationError(f"seed table scheme must be {SEED_TABLE_SCHEME}")
    bodies = table.get("bodies")
    if not isinstance(bodies, dict) or not bodies:
        raise DeclarationError("seed table carries no bodies")
    hosts = set(table.get("hosts") or [])
    for code, b in bodies.items():
        objs = b.get("objects")
        if not isinstance(objs, dict) or set(objs) != set(SEED_OBJECTS):
            raise DeclarationError(f"seeds.{code}.objects must name exactly {SEED_OBJECTS}")
        for obj, seeds in objs.items():
            for i, e in enumerate(seeds):
                w = f"seeds.{code}.{obj}[{i}]"
                _url(e.get("url"), f"{w}.url")
                if e.get("host") != urllib.parse.urlsplit(e["url"]).netloc.lower():
                    raise DeclarationError(f"{w}.host {e.get('host')!r} is not the URL's host")
                if e["host"] not in hosts:
                    raise DeclarationError(f"{w}.host {e['host']} is not in the table's hosts")
                _provenance(dict(e, seeded_from=e.get("seeded_from")), w, 2)
                if not e.get("seeded_from"):
                    raise DeclarationError(f"{w} names no seeded_from")
                _status(e.get("status"), w)
        if sorted(b.get("no_seed") or []) != sorted(o for o, v in objs.items() if not v):
            raise DeclarationError(f"seeds.{code}.no_seed does not list its empty objects")
    return table
