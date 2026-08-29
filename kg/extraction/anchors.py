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

#: A sentence ends at .!? followed by whitespace, or at a line break — SUBJECT to the
#: exemptions below, which is where the real work is. Note that a sentence-ending period
#: followed by a newline is matched by the FIRST alternative (`\s+` consumes the newline),
#: so the second alternative only ever sees a newline that no punctuation preceded.
_SENT_END = re.compile(r"(?<=[.!?])\s+|\n")

#: Markdown lines that are structural units rather than prose. Docling emits all three
#: throughout this corpus, and a period inside one of them is never a sentence end.
#: MEASURED before this rule existed: an anchor on a table row returned
#: `| No Optimization | 19 .` — Docling writes decimals spaced (`19 . 5`), so the row split
#: at the decimal point. The truncated span is still verbatim-present in the source, so it
#: passes `is_grounded` and looks correct. That is the dangerous shape of this bug.
_TABLE_ROW = re.compile(r"^\s*\|")
_HEADING = re.compile(r"^\s*#{1,6}\s")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s)")

#: PRIOR ART, and why this is a rule set and not a library.
#: Sentence boundary disambiguation is a named, long-solved problem; the decomposition below
#: is the standard one (Grefenstette & Tapanainen 1994; Kiss & Strunk 2006 for unsupervised
#: Punkt; pysbd's "Golden Rules" for the modern rule-based statement): a period is NOT a
#: boundary when it follows a known abbreviation, an initial, or sits inside a number.
#: `nltk` (Punkt) and `spacy` are both importable in this environment and were evaluated.
#: Neither is adopted, for three reasons, in order of weight:
#:   1. The DOMINANT failure here is markdown line structure, which no prose segmenter
#:      models. Punkt would split `| No Optimization | 19 . 5 |` exactly as the naive rule
#:      did, because a table row is not a sentence and Punkt has no notion of one.
#:   2. This module needs boundaries AROUND ONE KNOWN OFFSET, not segmentation of a whole
#:      document — a much narrower problem than either library solves.
#:   3. `grounding.py`, whose normalization this file must not fork, is documented stdlib-only,
#:      and the repo declares exactly one runtime dependency (pyyaml). Adding a model download
#:      (Punkt data / a spaCy model) to the extraction path is a liability out of proportion
#:      to a bounded list of abbreviations (~/GitHub/CLAUDE.md §7, §8).
#: What IS adopted is the field's decomposition; what is rejected is its packaging.
_ABBREVIATIONS = frozenset("""
e.g i.e cf vs viz etc al esp approx ca ibid
fig figs tbl tab eq eqn no nos pp p vol vols ch chap sec secs art
dr mr mrs ms prof jr sr st rev hon
inc ltd co corp dept univ natl govt admin assn
u.s u.k u.n e.u d.c a.m p.m
jan feb mar apr jun jul aug sep sept oct nov dec
""".split())

#: NOTE: no multi-word abbreviation table. "et al." is already caught by the single-token
#: check, because the token ending at the period is "al." and `al` is in the set above. A
#: separate _MULTIWORD_ABBREV tuple was written first and then removed: a mutation deleting
#: it killed no test, which is the definition of code that cannot fire.


def _preceding_token(text: str, dot_index: int) -> str:
    """The word ending at `dot_index` (the index of the '.'), lower-cased, dot included."""
    j = dot_index
    while j > 0 and not text[j - 1].isspace():
        j -= 1
    return text[j:dot_index + 1].strip().lower()


def _is_sentence_boundary(text: str, m: re.Match) -> bool:
    """Is this regex hit a real sentence end?

    Every exemption below was produced by a MEASURED wrong span on this corpus, not by
    imagining what might go wrong."""
    if _is_hyphen_linebreak(text, m):
        return False
    dot = m.start() - 1                     # the [.!?] the lookbehind matched, if any
    prev = text[dot] if dot >= 0 else ""
    if prev not in ".!?":
        # A BARE line break — no sentence punctuation preceded it. Word wrap, unless it is a
        # paragraph break or bounds a structural line. (A period followed by a newline is
        # matched by the FIRST alternative, so it lands on the punctuation logic below and is
        # NOT routed here; getting that wrong swallowed real sentence ends.)
        return _newline_ends_the_unit(text, m)
    if prev != ".":
        return True                         # '!' and '?' are unambiguous
    before = text[:dot + 1]
    tok = _preceding_token(text, dot)
    if tok[:-1] in _ABBREVIATIONS:          # strip the trailing '.'
        return False
    if len(tok) == 2 and tok[0].isalpha():  # an initial: "J. Smith"
        return False
    # A number split across the period, including Docling's spaced decimals ("19 . 5").
    prev_ch = before[:-1].rstrip()[-1:] if before[:-1].rstrip() else ""
    next_ch = text[m.end():m.end() + 1]
    if prev_ch.isdigit() and next_ch.isdigit():
        return False
    return True


def _newline_ends_the_unit(source_text: str, m: re.Match) -> bool:
    """Does this line break end a unit, or is it just word wrap?

    MEASURED on the first Arm A chunk (2026-08-29), which is why this rule exists: Docling
    hard-wraps prose at ~110 characters, so `This survey aims to propose a taxonomy of data\n
    readiness for AI (DRAI) metrics` carries a newline in the MIDDLE of a sentence. Treating
    every newline as a sentence end cut spans like
    `Poor quality data produces inaccurate and ineffective AI models that` — truncated at the
    wrap, still verbatim-present in the source, and therefore still passing `is_grounded`.
    That is the same dangerous shape as the table-row bug, one layer down: 9 of 11
    `span_partial` quarantines on that chunk were wrap truncation, not paraphrase.

    A newline ends the unit when it is a PARAGRAPH break (a blank line, i.e. the run of
    newlines is longer than one) or when a markdown structural line sits on either side of
    it — a heading, table row or list item is bounded by its own line by definition. Inside
    a wrapped paragraph it is not a boundary at all.

    The asymmetry is deliberate. Over-extending a span joins two sentences, which still
    yields text cut verbatim from the source around the anchor; under-extending it produces
    a fragment that reads as a claim the document never made. Only one of those is a
    fabrication risk."""
    i = m.start() - 1
    while i >= 0 and source_text[i] in " \t":
        i -= 1
    if i >= 0 and source_text[i] == "\n":
        return True                        # a blank line: this is a paragraph break
    # NOTE: a symmetric lookahead ("is the NEXT newline-separated line empty") was written
    # first and removed — a mutation deleting it killed no test, because a blank line is two
    # newlines and the second one always satisfies the check above. Whichever of the two the
    # scan lands on, `containing_sentence` strips the trailing newline and returns the same
    # span. Dead code that cannot fire, exactly like the `_MULTIWORD_ABBREV` table before it.
    left, _ = _line_bounds(source_text, m.start(), m.start())
    before = source_text[left:m.start()]
    right_end = source_text.find("\n", m.end())
    after = source_text[m.end(): len(source_text) if right_end == -1 else right_end]
    return _is_structural_line(before) or _is_structural_line(after)


def _is_structural_line(line: str) -> bool:
    return bool(_TABLE_ROW.match(line) or _HEADING.match(line) or _LIST_ITEM.match(line))


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


def _line_bounds(source_text: str, start: int, end: int) -> tuple[int, int]:
    left = source_text.rfind("\n", 0, start) + 1
    right = source_text.find("\n", max(end - 1, start))
    return left, (len(source_text) if right == -1 else right)


def structural_line(source_text: str, start: int, end: int) -> str | None:
    """The whole line, when [start, end) sits on a markdown structural line; else None.

    A table row, a heading, and a list item are UNITS. Splitting one at an interior period
    produces a fragment that no reader would call a sentence — and, because the fragment is
    still copied from the source, one that passes every grounding check downstream."""
    left, right = _line_bounds(source_text, start, end)
    line = source_text[left:right]
    if _is_structural_line(line):
        return line.strip()
    return None


def containing_sentence(source_text: str, start: int, end: int) -> str:
    """The sentence of `source_text` containing [start, end), verbatim from the source.

    Markdown structure outranks prose sentence rules: see `structural_line`."""
    line = structural_line(source_text, start, end)
    if line is not None:
        return line
    left = 0
    for m in _SENT_END.finditer(source_text, 0, start):
        if _is_sentence_boundary(source_text, m):
            left = m.end()
    m = None
    for cand in _SENT_END.finditer(source_text, max(end - 1, start)):
        if _is_sentence_boundary(source_text, cand):
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


#: Layers whose items carry an anchor of their own. The node layers come from the parser's
#: own catalogue so a new node type cannot be added there and silently skipped here.
_ANCHORED_NON_NODE_LAYERS = ("edges", "cites", "proposed_relationships", "mentions")

#: Instrument per-attribute anchors -> the per-attribute span map the parser already reads
#: (`_null_uncovered_instrument_attrs`). Same mechanism as the node anchor, one level down.
ATTRIBUTE_ANCHORS_KEY = "attribute_anchors"
ATTRIBUTE_SPANS_KEY = "grounding_spans"


def anchored_layers() -> tuple[str, ...]:
    from .parser import LAYER_TYPES
    return tuple(LAYER_TYPES) + _ANCHORED_NON_NODE_LAYERS


def apply_to_output(output: dict, source_text: str) -> tuple[dict, list[dict]]:
    """Derive every item's `grounding_span` from its `anchor`, across the whole envelope.

    Returns `(rewritten output, dropped)` where `dropped` is a parser-shaped quarantine list
    `{kind, reason, item}`. An item whose anchor cannot be located is DROPPED here rather
    than passed on with no span: the parser would quarantine it one step later as "missing
    grounding_span", which is a true statement that names the wrong cause. `anchor_not_located`
    is its own quarantine class precisely so ADDENDUM-03 §3 can report it apart from
    `span_partial` — the erratum split those causes and the report must keep them split.

    `gleaned` is untouched: the contract defines it as names only, with no anchor, so it is
    not an anchored layer and never reaches the parser.
    """
    out = dict(output)
    dropped: list[dict] = []
    for layer in anchored_layers():
        items = out.get(layer)
        if not isinstance(items, list):
            continue
        kept = []
        for item in items:
            if not isinstance(item, dict):
                dropped.append({"kind": layer, "reason": f"{NOT_LOCATED}: item is not an object",
                                "item": item})
                continue
            new_item, reason = apply_anchor_contract(item, source_text)
            if reason:
                dropped.append({"kind": layer, "reason": reason, "item": item})
                continue
            attr_anchors = new_item.get(ATTRIBUTE_ANCHORS_KEY)
            if isinstance(attr_anchors, dict):
                spans = {}
                for attr, anchor in attr_anchors.items():
                    span, _ = derive_span(anchor, source_text)
                    if span:
                        spans[attr] = span
                # An attribute whose anchor did not locate gets NO span, which the parser
                # then nulls at attribute level. Dropping the whole Instrument for one bad
                # attribute anchor would be a harsher rule than the contract states.
                new_item[ATTRIBUTE_SPANS_KEY] = spans
            kept.append(new_item)
        out[layer] = kept
    return out, dropped
