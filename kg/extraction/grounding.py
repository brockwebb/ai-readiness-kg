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
