#!/usr/bin/env python3
"""Mechanical grounding validator (schema_v0.1.md §4/§5.5).

Every extracted node and edge must carry a verbatim ``grounding_span`` that string-matches
the source text. The match is whitespace- and OCR-tolerant but not fuzzy: a genuine miss is
quarantined, never ingested. "No grounding span, no write" is enforced in code here, not by
convention. Stdlib only.

Tolerances (and nothing beyond them):
- Unicode NFKC normalization — collapses OCR ligatures (ﬁ→fi, ﬂ→fl) and full/half-width forms.
- Hyphenation line-breaks — ``read-\\nabilty`` in the source matches ``readabilty`` in the span.
- Whitespace variance — any run of whitespace (newlines included) collapses to one space.

Case is preserved: grounding is a verbatim quote, so a case change is treated as a real miss.
"""
from __future__ import annotations

import re
import unicodedata

_HYPHEN_LINEBREAK = re.compile(r"-\s*\n\s*")   # de-hyphenate a word split across lines
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize for tolerant matching. Applied identically to source and span."""
    text = unicodedata.normalize("NFKC", text)
    text = _HYPHEN_LINEBREAK.sub("", text)     # join hyphenated line-breaks first...
    text = _WHITESPACE.sub(" ", text)          # ...then collapse remaining whitespace
    return text.strip()


def is_grounded(span: str, source_text: str) -> bool:
    """True iff ``span`` appears in ``source_text`` under tolerant normalization.

    An empty/whitespace-only span is not grounded (there is nothing to verify)."""
    if not span or not span.strip():
        return False
    return normalize(span) in normalize(source_text)


# --- Span-coverage invariant (task 2026-08-22_faithfulness_probe Phase 7; DD-015) ---------
# The TEVV probe found that a span which merely *locates* an item (its name, a fragment of
# its sentence) passes is_grounded() while entailing nothing about the item's content. For
# the text-bearing attributes below, the span must COVER the attribute's full value: the
# item text, normalized, must occur inside the normalized span. A miss is quarantined by the
# parser with reason `span_partial`. Attribute list is data here so the parser and the probe
# read one definition.
COVERAGE_ATTRIBUTES = ("verbatim_text", "text", "claim_text", "name", "term")


def covers(span: str, value: str) -> bool:
    """True iff ``value`` (the item's own text) occurs inside ``span`` under tolerant
    normalization — i.e. the span carries the whole statement, not a pointer to it."""
    if not span or not span.strip() or not value or not value.strip():
        return False
    return normalize(value) in normalize(span)


def partial_span_reason(item: dict, attributes: tuple[str, ...] = COVERAGE_ATTRIBUTES) -> str | None:
    """The first text attribute the span fails to cover, as a quarantine reason; None when
    the invariant holds (or no covered attribute is present)."""
    span = item.get("grounding_span") or ""
    for attr in attributes:
        val = item.get(attr)
        if isinstance(val, str) and val.strip() and not covers(span, val):
            return f"span_partial: grounding_span does not cover '{attr}'"
    return None
