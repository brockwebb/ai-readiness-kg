#!/usr/bin/env python3
"""Mechanical span-shape checks for the faithfulness probe (probe-protocol change, v1.0.0).

Task 2026-08-27_chunked_pilot §5 requires the *mid-noun-phrase truncation check* diagnosed in
`docs/research/2026-08-27_pilot_instrument_verdict.md` to be applied to both arms' facts before
judging, so the comparison is like-for-like. 13 of that run's 27 `span_truncated` facts had a
span the model cut before its head noun, e.g.

    "evaluate the completeness, timeliness, accuracy, and consistency of the state-reported
     commercial"          <- cut before "insurance data"

This module DETECTS and RECORDS that shape. It does not exclude anything from any metric:
excluding a class from a pre-registered denominator would move the threshold by other means,
which the gate forbids. The flag rides along on the fact so the verdict can report how much of
a stratum's failure is span shape rather than content.

The check is POS-based because the shape is grammatical: the span's last token is a
noun-modifier and the document's next token is the noun it modifies. nltk's perceptron tagger
is used (present in the extraction environment; a missing tagger raises rather than degrading
to a guess, since a check that silently answers "no" is worse than no check).
"""
from __future__ import annotations

import re

from . import grounding

CHECK_VERSION = "1.0.0"

#: Tags that cannot end a noun phrase: determiners, adjectives (incl. comparative/superlative),
#: possessives, cardinal numbers, prepositions/subordinators and coordinators.
_MODIFIER_TAGS = frozenset({"DT", "PDT", "PRP$", "JJ", "JJR", "JJS", "CD", "IN", "CC", "POS"})
#: Tags that make the following token a head noun.
_NOUN_TAGS = frozenset({"NN", "NNS", "NNP", "NNPS"})

_WORD = re.compile(r"[A-Za-z][A-Za-z\-’']*")
_TAIL_CONTEXT = 8          # tokens of span tail handed to the tagger for context
_LOOKAHEAD_CHARS = 120     # document text after the span, enough for the next token or two


def _pos_tag(tokens: list[str]) -> list[tuple[str, str]]:
    import nltk                      # hard dependency: see module docstring
    return nltk.pos_tag(tokens)


def is_mid_noun_phrase(span: str, source_text: str) -> bool:
    """True iff ``span`` stops on a noun-modifier whose head noun follows it in ``source_text``.

    Both are normalized with the grounding normalizer so the check sees the same text the
    grounding validator does. A span that does not locate in the source is not flagged — that
    is a grounding miss, a different (and louder) failure.
    """
    if not span or not span.strip() or not source_text:
        return False
    nspan, nsrc = grounding.normalize(span), grounding.normalize(source_text)
    at = nsrc.find(nspan)
    if at < 0:
        return False
    tail = _WORD.findall(nspan)[-_TAIL_CONTEXT:]
    ahead = _WORD.findall(nsrc[at + len(nspan): at + len(nspan) + _LOOKAHEAD_CHARS])
    if not tail or not ahead:
        return False
    tagged = _pos_tag(tail + ahead[:2])
    last_tag = tagged[len(tail) - 1][1]
    next_tag = tagged[len(tail)][1]
    return last_tag in _MODIFIER_TAGS and next_tag in _NOUN_TAGS


def check(span: str, source_text: str) -> dict:
    """The recorded result: the flag plus the version that produced it."""
    return {"span_mid_phrase": is_mid_noun_phrase(span, source_text),
            "span_check_version": CHECK_VERSION}
