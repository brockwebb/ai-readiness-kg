"""What a reader of an HTML page sees, for rules that match words on a page. **Pure.**

`cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md` decision 1 (D1, A3). The
recollection found two false passes that share one cause: a rule matched a token against the
page's MARKUP rather than its text. `RULE-D1-v4` found `CC0` inside a script asset hash on
census.gov's terms page and `MIT` inside "permit" and "Limit" on eia.gov's; `RULE-A3-v7` took an
HTML page for an unfiltered file because the link's body was large. Both are the same fact
misread: markup is not content.

**What "visible text" means here.** The character data a browser renders: `<script>`,
`<style>`, `<noscript>` and `<template>` content removed, every attribute value removed (an
attribute is never rendered as text), character references decoded. That is the HTML Living
Standard's rendering model reduced to what a stdlib parser can state without a layout engine
(WHATWG HTML §15, "Rendering"; `script`, `style` and `template` are never rendered, and
`noscript` is not rendered when scripting is enabled, which is the client an AI tool emulates).
A rule may import `html.parser` (stdlib, no I/O); it may not import `urllib`, `os` or a clock
(`tests/test_scan_harness.py::test_no_rule_reaches_the_network_a_clock_or_the_filesystem`).

**Token matching** is at word boundaries, in the case an identifier's convention fixes (`CC0`,
`MIT`; an SPDX short identifier is written in one case, SPDX License List, "short identifier")
and case-insensitively for a phrase (`public domain`). A token with no space is an identifier;
one with a space is a phrase.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

#: Elements whose content is never rendered as text (WHATWG HTML §15.3.1 hides `script`,
#: `style`, `template`; `noscript` is not rendered for a scripting client).
NON_RENDERED = ("script", "style", "noscript", "template")

#: What makes a body HTML when its Content-Type does not say so (WHATWG MIME Sniffing §7.1,
#: "identifying a resource with an unknown MIME type": the HTML patterns, matched
#: case-insensitively after leading whitespace). The standard's list, trimmed to the tags whose
#: presence at the start of a body is unambiguous for this purpose.
HTML_SNIFF_PREFIXES = ("<!doctype html", "<html", "<head", "<body", "<script", "<iframe",
                       "<h1", "<div", "<font", "<table", "<a", "<style", "<title", "<b",
                       "<br", "<p", "<!--")

#: Media types that ARE HTML (WHATWG MIME Sniffing §4.6, "an HTML MIME type is text/html";
#: XHTML is the same document served as XML).
HTML_MEDIA_TYPES = ("text/html", "application/xhtml+xml")


class _Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list = []
        self.licence_links: list = []
        self._hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in NON_RENDERED:
            self._hidden += 1
        if tag in ("a", "link", "area"):
            a = {k.lower(): (v or "") for k, v in attrs}
            if "license" in a.get("rel", "").lower().split() and a.get("href"):
                self.licence_links.append(a["href"].strip())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in NON_RENDERED and self._hidden:
            self._hidden -= 1

    def handle_endtag(self, tag):
        if tag in NON_RENDERED and self._hidden:
            self._hidden -= 1

    def handle_data(self, data):
        if not self._hidden:
            self.parts.append(data)


def _parse(html: str) -> _Visible:
    p = _Visible()
    p.feed(str(html or ""))
    p.close()
    return p


def visible_text(html: str) -> str:
    """The page's rendered text, whitespace collapsed to single spaces."""
    return re.sub(r"\s+", " ", " ".join(_parse(html).parts)).strip()


def licence_links(html: str) -> list:
    """The `href` of every `a`, `area` or `link` whose `rel` carries the `license` link type
    (HTML Living Standard §4.6.7.9, link type "license": "Indicates that the main content of the
    current document is covered by the copyright license described by the referenced
    document"). Attributes are never matched as text; this is the one attribute that is a
    licence statement by definition, so it is read as one."""
    return _parse(html).licence_links


def is_identifier(token: str) -> bool:
    """True for a token whose case is fixed by convention (`CC0`, `MIT`, `CC-BY`, `ODC-BY`,
    `APACHE-2.0`): no space in it. A token with a space is a phrase (`PUBLIC DOMAIN`)."""
    return " " not in token


def find_token(text: str, token: str):
    """The first match of `token` in `text` at word boundaries, or None.

    A boundary is a non-word character or the end of the text, so `MIT` is not found in
    "permit" or "Limit", and `CC-BY` is found in "CC-BY-4.0". An identifier is matched in the
    case its convention fixes: as written in `params.d1_licence.recognised_tokens`, which writes
    every token upper case, and, for a versioned SPDX id, in SPDX's own spelling (`APACHE-2.0`
    and `Apache-2.0`). A phrase is matched case-insensitively."""
    if not token:
        return None
    if not is_identifier(token):
        return re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text, flags=re.IGNORECASE)
    forms = [token]
    if re.search(r"-\d", token):
        forms.append(token[:1] + token[1:].lower())
    for form in forms:
        m = re.search(r"(?<!\w)" + re.escape(form) + r"(?!\w)", text)
        if m:
            return m
    return None


def is_html(content_type: str | None, head: str | None = None) -> bool:
    """True when a response is an HTML page: its media type says so, or (no media type, or a
    generic one) its first bytes sniff as HTML."""
    ct = str(content_type or "").split(";", 1)[0].strip().lower()
    if ct in HTML_MEDIA_TYPES:
        return True
    if head:
        h = str(head).lstrip().lower()
        return any(h.startswith(p) and (len(h) == len(p) or not h[len(p)].isalnum())
                   for p in HTML_SNIFF_PREFIXES)
    return False
