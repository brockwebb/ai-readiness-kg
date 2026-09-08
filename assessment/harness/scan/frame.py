"""Surface selection: which pages of an agency the instrument measures. **Pure. No network.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §2. The rule is declared in `params.frame` BEFORE
any agency page was fetched, and it is a function of a parsed link list rather than a
judgement, so it can be run, tested on stored bodies, and re-run. `targets.yaml` makes the same
argument for cycle 1 and states the reason this file inherits:

    *"Do not choose products because they look good or bad for the instrument; choose by the
    agency's own 'principal products' or 'featured data' listing, and cite where each came
    from."*

A selection made by an author reading sixteen listings and picking what seems representative
is not a sample, it is a preference. So every selected surface carries the listing it was read
from, the digest of that listing's body, the verbatim anchor text, and **its position on the
page** — the last because "the first three in the agency's own order" is only checkable if the
order is recorded.

**Where the rule finds nothing, the entry says so.** `no_machine_entry_point` and
`no_flagship_products` are recorded outcomes about the agency, never a gap in the roster and
never an invitation to substitute something by hand. An agency whose listing this rule cannot
read contributes its host-level surfaces and nothing else, and that is a finding about the
agency's publication surface rather than a hole in the frame.
"""
from __future__ import annotations

import urllib.parse

VERSION = "0.1.0"


def _clean(text: str) -> str:
    return " ".join(str(text or "").split())


def _path(url: str) -> str:
    return urllib.parse.urlsplit(url or "").path.lower()


def _same_host(url: str, page_url: str) -> bool:
    """A surface of THIS agency. The frame's unit of analysis is the surface and agencies group
    surfaces, so a link to another agency's product would put a row under the wrong group —
    and `manners.on_roster_host` already makes the same call for what may be fetched."""
    a, b = urllib.parse.urlsplit(url or ""), urllib.parse.urlsplit(page_url or "")
    return bool(a.netloc) and a.netloc == b.netloc


def _matches(link: dict, tokens: list) -> str | None:
    """The token this link matches on, in the anchor text or the path, or None.

    Returns the TOKEN and not a boolean: a selection that cannot say which token chose it
    leaves a target nobody can check, which is the defect
    `cc_tasks/2026-09-08_scan_harness_v4.md` §1.4 recorded one layer down when A8's matcher
    could not say why it matched.
    """
    hay = f"{_clean(link.get('text')).lower()} {_path(link.get('href'))}"
    return next((t for t in tokens if t in hay), None)


def machine_entry_point(links: list, page_url: str, params: dict) -> dict:
    """The agency's declared machine entry point: the FIRST link on its home page whose anchor
    or path carries one of `params.frame.machine_entry_point.tokens`.

    First, not best. "Best" is a judgement and there is no listing that ranks them; first in
    the agency's own order is a rule.
    """
    cfg = params["frame"]["machine_entry_point"]
    for i, link in enumerate(links):
        href = (link.get("href") or "").split("#")[0]
        if not href.startswith("http") or not _same_host(href, page_url):
            continue
        hit = _matches({**link, "href": href}, cfg["tokens"])
        if hit:
            return {"url": href, "anchor_text": _clean(link.get("text")),
                    "matched_token": hit, "position": i,
                    "selection_source": f"{page_url} link {i}, matched "
                                        f"frame.machine_entry_point.tokens {hit!r}"}
    return {"url": None, "marker": cfg["none_found_marker"],
            "selection_source": f"{page_url}: no link matches "
                                f"frame.machine_entry_point.tokens"}


def listing_page(links: list, page_url: str, params: dict) -> dict:
    """The agency's own product/data listing, as the first home-page link matching
    `params.frame.flagship_products.listing_tokens`."""
    cfg = params["frame"]["flagship_products"]
    for i, link in enumerate(links):
        href = (link.get("href") or "").split("#")[0]
        if not href.startswith("http") or not _same_host(href, page_url):
            continue
        if _path(href).rstrip("/") == _path(page_url).rstrip("/"):
            continue                                  # a link back to the home page
        hit = _matches({**link, "href": href}, cfg["listing_tokens"])
        if hit:
            return {"url": href, "anchor_text": _clean(link.get("text")),
                    "matched_token": hit, "position": i,
                    "selection_source": f"{page_url} link {i}, matched "
                                        f"frame.flagship_products.listing_tokens {hit!r}"}
    return {"url": None, "marker": "no_listing_page",
            "selection_source": f"{page_url}: no link matches "
                                f"frame.flagship_products.listing_tokens"}


def is_product(link: dict, listing_url: str, params: dict) -> bool:
    """Is this link a PRODUCT on the listing, rather than navigation around it?

    Three mechanical discriminators, none of them a judgement, and all three inherited from
    cycle 1's `targets.yaml` rather than re-derived: it is on the agency's own host, it goes
    DEEPER than the listing page (a link at or above the listing's own depth is a section),
    and its anchor is neither one of the declared reject tokens nor a single word.
    """
    cfg = params["frame"]["flagship_products"]
    href = (link.get("href") or "").split("#")[0]
    text = _clean(link.get("text"))
    if not href.startswith("http") or not _same_host(href, listing_url):
        return False
    if any(t in text.lower() for t in cfg["reject_tokens"]):
        return False
    if len(text.split()) < int(cfg["min_anchor_words"]):
        return False
    lp, hp = _path(listing_url).rstrip("/"), _path(href).rstrip("/")
    return hp != lp and hp.startswith(lp) and len(hp) > len(lp)


def flagship_products(links: list, listing_url: str, params: dict) -> dict:
    """The first `params.frame.flagship_products.n` products in the agency's OWN order.

    Position on the listing is recorded for every one of them, because "the first N in the
    agency's order" is a claim about the page and is only checkable against the page if the
    order is on the record.
    """
    cfg = params["frame"]["flagship_products"]
    out, seen = [], set()
    for i, link in enumerate(links):
        href = (link.get("href") or "").split("#")[0]
        if href in seen or not is_product(link, listing_url, params):
            continue
        seen.add(href)
        out.append({"url": href, "anchor_text": _clean(link.get("text")), "position": i,
                    "selection_source": f"{listing_url} link {i} "
                                        f"{_clean(link.get('text'))!r}"})
        if len(out) >= int(cfg["n"]):
            break
    if not out:
        return {"products": [], "marker": cfg["none_found_marker"],
                "selection_source": f"{listing_url}: no link satisfies frame."
                                    f"flagship_products"}
    return {"products": out}


def select(home_links: list, home_url: str, listing_links: list | None,
           listing_url: str | None, params: dict) -> dict:
    """The whole rule for one agency, over already-fetched link lists.

    Pure, so `tests/test_scan_frame.py` runs it on stored listing bodies — the property §2 asks
    for, and the only way the rule can be checked without contacting an agency again.
    """
    machine = machine_entry_point(home_links, home_url, params)
    flagships = (flagship_products(listing_links, listing_url, params)
                 if listing_links is not None and listing_url
                 else {"products": [],
                       "marker": params["frame"]["flagship_products"]["none_found_marker"],
                       "selection_source": "no listing page was found on the agency home"})
    return {"machine_entry_point": machine, "flagships": flagships}
