#!/usr/bin/env python3
"""Anchor contract (v0.3.7; chunked_pilot ADDENDUM-01 §2.1, built under ADDENDUM-03 §1.1).

The model emits `name`, `type`, and an `anchor` — the shortest unique substring of the chunk
that points at the item, ≤ 10 tokens. The harness locates that anchor deterministically and
**derives the grounding span itself from the source text** as the containing sentence.

Why this replaces verbatim emission: under the retired contract the model retyped whole spans,
which produced 108–158K-token outputs, cost 65,637 settled tokens per chunk, and — because a
retyped span is a *copy* — introduced `span_partial` quarantines whenever the copy drifted
from the source by a character. An anchor is short, so it is cheap; and the span that reaches
the graph is cut from the document, so it cannot drift by construction. **The locate-at-birth
guarantee is unchanged and in fact strengthened: the span is document-derived, never
model-typed.**

Normalization is `grounding.normalize`, reused and never forked — but locating needs
*offsets*, which that function does not provide (it returns a string). So this module rebuilds
the same transformation while tracking each output character back to its source index, and
then **verifies** the rebuild against `grounding.normalize` itself. If the two ever disagree
the mapping is untrustworthy, and the anchor is reported as not located rather than used to
cut a span from coordinates we cannot vouch for. Failing closed is the point: a wrong span is
worse than a missing one, because a wrong one is still grounded-looking.
"""
from __future__ import annotations

import re
import unicodedata

from . import grounding

#: Anchor budget from the contract. Longer anchors are the retyping behaviour coming back in
#: through a side door — the whole cost argument rests on the anchor being short.
MAX_ANCHOR_TOKENS = 10

#: Quarantine reason. The contract names ONE reason for both "missing" and "ambiguous"; the
#: detail after the colon is diagnosis, not a second class.
NOT_LOCATED = "anchor_not_located"

#: A sentence ends at .!? followed by whitespace, or at a line break. Markdown line structure
#: matters here: a table row or list item is a unit, and running a span across `|` rows
#: produces a "sentence" no human would call one.
_SENT_END = re.compile(r"(?<=[.!?])\s+|\n")


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """(normalized text, index map) where map[i] is the source index of normalized char i.

    Mirrors `grounding.normalize` step for step: NFKC, de-hyphenate line breaks, collapse
    whitespace, strip. Callers must not trust the result without `_verify`."""
    # NFKC per character so each output character keeps a source index. Whole-string NFKC can
    # differ from per-character NFKC across combining sequences, which is exactly why the
    # result is verified below rather than assumed.
    chars: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(text):
        for out in unicodedata.normalize("NFKC", ch):
            chars.append(out)
            idx.append(i)

    # De-hyphenate: drop "-" + surrounding whitespace where a newline is inside the run.
    out_chars: list[str] = []
    out_idx: list[int] = []
    j = 0
    n = len(chars)
    while j < n:
        if chars[j] == "-":
            k = j + 1
            while k < n and chars[k].isspace():
                k += 1
            if k > j + 1 and "\n" in "".join(chars[j + 1:k]):
                j = k                      # drop the hyphen AND the whitespace run
                continue
        out_chars.append(chars[j])
        out_idx.append(idx[j])
        j += 1

    # Collapse whitespace runs to a single space, keeping the run's first source index.
    coll_chars: list[str] = []
    coll_idx: list[int] = []
    j = 0
    n = len(out_chars)
    while j < n:
        if out_chars[j].isspace():
            coll_chars.append(" ")
            coll_idx.append(out_idx[j])
            while j < n and out_chars[j].isspace():
                j += 1
        else:
            coll_chars.append(out_chars[j])
            coll_idx.append(out_idx[j])
            j += 1

    # strip()
    start, end = 0, len(coll_chars)
    while start < end and coll_chars[start] == " ":
        start += 1
    while end > start and coll_chars[end - 1] == " ":
        end -= 1
    return "".join(coll_chars[start:end]), coll_idx[start:end]


def _verify(text: str, norm: str) -> bool:
    """The rebuilt normalization must equal the one the rest of the pipeline uses."""
    return norm == grounding.normalize(text)


def anchor_token_count(anchor: str) -> int:
    return len(str(anchor or "").split())


def locate_all(anchor: str, source_text: str) -> list[tuple[int, int]] | None:
    """Every occurrence of `anchor` in `source_text`, as (start, end) SOURCE offsets.

    None when the offset mapping could not be verified — the caller must treat that as
    not-located, never as zero occurrences."""
    if not anchor or not str(anchor).strip():
        return []
    norm_src, idx = _normalize_with_map(source_text)
    if not _verify(source_text, norm_src):
        return None
    norm_anchor = grounding.normalize(anchor)
    if not norm_anchor:
        return []
    spans, at = [], norm_src.find(norm_anchor)
    while at != -1:
        last = at + len(norm_anchor) - 1
        # +1 on the end so the source slice is inclusive of the final matched character.
        spans.append((idx[at], idx[last] + 1))
        at = norm_src.find(norm_anchor, at + 1)
    return spans


def _is_hyphen_linebreak(source_text: str, m: re.Match) -> bool:
    """A newline that de-hyphenation joins is NOT a sentence boundary.

    `read-\nability` is one word. Treating its line break as a boundary cut the derived span
    mid-word and produced "ability of the file is high." — a span that is technically present
    in the source and still wrong, which is the failure mode this whole module exists to
    avoid. Found by the module's own smoke test before any of it shipped."""
    if "\n" not in m.group():
        return False
    before = source_text[:m.start()].rstrip()
    return before.endswith("-")


def containing_sentence(source_text: str, start: int, end: int) -> str:
    """The sentence of `source_text` containing [start, end), verbatim from the source."""
    left = 0
    for m in _SENT_END.finditer(source_text, 0, start):
        if not _is_hyphen_linebreak(source_text, m):
            left = m.end()
    m = None
    for cand in _SENT_END.finditer(source_text, max(end - 1, start)):
        if not _is_hyphen_linebreak(source_text, cand):
            m = cand
            break
    right = m.start() + 1 if m and m.group().startswith((".", "!", "?")) else (
        m.start() if m else len(source_text))
    # A boundary match that begins with whitespace/newline ends the sentence before it.
    if m and not m.group().strip():
        right = m.start()
    return source_text[left:right].strip()


def derive_span(anchor: str, source_text: str) -> tuple[str | None, str | None]:
    """(grounding_span, quarantine_reason). Exactly one of the two is None.

    The span is CUT FROM `source_text`; nothing the model typed reaches the graph."""
    n_tokens = anchor_token_count(anchor)
    if n_tokens == 0:
        return None, f"{NOT_LOCATED}: no anchor emitted"
    if n_tokens > MAX_ANCHOR_TOKENS:
        return None, (f"{NOT_LOCATED}: anchor is {n_tokens} tokens, over the "
                      f"{MAX_ANCHOR_TOKENS}-token contract")
    hits = locate_all(anchor, source_text)
    if hits is None:
        return None, (f"{NOT_LOCATED}: offset mapping failed verification against "
                      f"grounding.normalize; refusing to cut a span from untrusted offsets")
    if not hits:
        return None, f"{NOT_LOCATED}: not found in the chunk"
    if len(hits) > 1:
        return None, (f"{NOT_LOCATED}: ambiguous, {len(hits)} occurrences in the chunk "
                      f"(the contract requires the shortest UNIQUE substring)")
    span = containing_sentence(source_text, *hits[0])
    if not span:
        return None, f"{NOT_LOCATED}: located, but the containing sentence is empty"
    if not grounding.is_grounded(span, source_text):
        # Cannot happen by construction; asserted anyway, because "derived from the source"
        # is the entire warrant for skipping the model's typing.
        return None, f"{NOT_LOCATED}: derived span failed its own grounding check"
    return span, None


def apply_anchor_contract(item: dict, source_text: str) -> tuple[dict, str | None]:
    """Fill `grounding_span` on one item from its `anchor`. Returns (item, reason).

    An item that already carries a model-typed `grounding_span` does NOT keep it: under this
    contract the span is the harness's to derive, and honouring a typed one would reopen the
    drift the contract exists to close."""
    out = dict(item)
    span, reason = derive_span(out.get("anchor"), source_text)
    if reason:
        return out, reason
    out["grounding_span"] = span
    return out, None
