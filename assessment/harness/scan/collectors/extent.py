"""Shallow text features: is there a document here before JavaScript runs?

Task `cc_tasks/2026-09-06_scan_targets.md` §2, for the B3-v2 "retrievable without JS" clause
and the A10-v2 pre-JS clause. **Not invented here.** These are the two features of
Kohlschütter, Fankhauser & Nejdl, *Boilerplate Detection using Shallow Text Features*
(WSDM 2010), already adopted in this repo as DD-030's corpus extent gate — visible character
count after tag and script removal, and the share of that text sitting inside `<a>` elements.

Reusing the ingest gate's own features has a consequence worth stating: a methodology page
that would have been refused admission to the corpus as a navigation surface cannot be scored
as a legible methodology document here. The instrument and the corpus agree about what counts
as a document, because they compute it the same way.

Measures only. Every floor lives in `params.yaml` and every verdict lives in a rule.
"""
from __future__ import annotations

import re

VERSION = "0.1.0"

_SCRIPTISH = re.compile(r"<(script|style|noscript|template)\b.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_ANCHOR = re.compile(r"<a\b[^>]*>(.*?)</a>", re.S | re.I)
_WS = re.compile(r"\s+")

#: How much visible text rides on the Observation for a reader's eye. Not a threshold and not
#: evidence truncation (the whole body is stored content-addressed), which is why it is a named
#: module constant rather than a params key — but named, because the lint is right that an
#: anonymous literal in a collector is a constant nobody can find.
_HEAD_CHARS = 400


def _visible(html: str) -> str:
    return _WS.sub(" ", _TAG.sub(" ", _SCRIPTISH.sub(" ", html))).strip()


def features(body: bytes, params: dict | None = None) -> dict:
    """`{visible_chars, link_chars, link_density, visible_text_head}`.

    `link_density` is 0.0 for an empty document rather than undefined: a page with no text has
    no text inside anchors either, and the caller's floor on `visible_chars` is what rejects
    it. Returning NaN or None here would push that decision into every rule.
    """
    html = body.decode("utf-8", "replace")
    visible = _visible(html)
    anchor_text = " ".join(_visible(m.group(1)) for m in _ANCHOR.finditer(html))
    n, a = len(visible), len(anchor_text)
    dp = int(((params or {}).get("reporting") or {}).get("ratio_decimal_places") or 0) or None
    return {"visible_chars": n, "link_chars": a,
            "link_density": (round(a / n, dp) if dp else a / n) if n else 0.0,
            "visible_text_head": visible[:_HEAD_CHARS],
            "extent_version": VERSION}


def looks_like_error_shell(body: bytes, tokens) -> list:
    """Which error-shell phrases appear in the visible text. A soft-404 is HTTP 200 with one
    of these and nothing else; the rule decides, this only reports."""
    head = _visible(body.decode("utf-8", "replace")).lower()
    return [t for t in tokens if t.lower() in head]
