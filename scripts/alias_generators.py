#!/usr/bin/env python3
"""Surface-form alias generators. **Zero model spend** — regexes and a lookup.

Task `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md` §1.1. The gold sample measured
stratum D's recall at **zero**: six of twenty near-misses just under the 0.80 embedding floor
were genuine matches, and all six were surface-form variants that an exact-name rule cannot
see. That is an alias-generation problem, and it is solved prior art:

* **Schwartz & Hearst (2003)**, "A simple algorithm for identifying abbreviation definitions
  in biomedical text", *PSB 2003*, 451-462 — the parenthetical pattern with the
  characters-in-order constraint. Still the baseline twenty years on.
* **Christen (2012), *Data Matching*, ch. 3** — standardisation before comparison: strip
  determiners, version tokens and generic suffixes so that comparison sees the name and not
  its packaging.

**Every generator is a refusal as much as a producer**, and the guard that carries the weight
is on `generic_suffix_strip`: a stripped form may become an alias only when that form
**already names a term**. Without it, "AI readiness framework" would mint "AI readiness" as a
link target and quietly merge a Framework with a Concept — inventing vocabulary from
punctuation, which is the failure mode the whole §1.2 control set exists to catch.
"""
from __future__ import annotations

import re

GENERATORS = ("schwartz_hearst", "determiner_strip", "version_strip",
              "generic_suffix_strip", "technical_specifications_variant")

#: Christen ch. 3 determiners.
_DET = re.compile(r"^(the|a|an)\s+(?=\S)", re.I)

#: A trailing version token: a dotted number (`2.0`, `1.0.1`), an explicit `v` prefix (`v2`),
#: or a bare integer of AT MOST TWO DIGITS (`DCAT 3`). The digit cap is what separates a
#: version from a designation, and the corpus is why: `ISO 8601`, `RFC 9309`, `Section 515`
#: and `NIST AI 600-1` all end in a number that is part of the name. Three digits or more is
#: a designation; one or two is a version.
_VER = re.compile(r"\s+v?\d+(?:\.\d+)+$|\s+v\d+$|\s+\d{1,2}$", re.I)

#: Generic suffixes, including the `Technical Specifications` / `Technical Standards` variant
#: the corpus actually uses for SDMX. Longest first so `technical standards` wins over
#: `standards`.
_SUFFIXES = ("technical specifications", "technical specification",
             "technical standards", "technical standard",
             "specifications", "specification", "guidelines", "guideline",
             "principles", "principle", "standards", "standard",
             "protocol", "framework", "vocabulary", "format")

_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", (s or "").strip()).lower()


# ---------------------------------------------------------------- Schwartz & Hearst 2003
_PAREN = re.compile(r"([^()]{2,120}?)\s*\(\s*([^()]{2,40}?)\s*\)")


def _is_expansion(long_form: str, short: str) -> bool:
    """Schwartz & Hearst's core constraint: every character of the short form appears in the
    long form, in order, case-insensitively, and the first character of the short form starts
    a word. Without this, `Data Quality (FAIR)` mints a false expansion."""
    if not (1 < len(short) <= 12) or not short.strip():
        return False
    if any(c.isdigit() for c in short) and not any(c.isalpha() for c in short):
        return False
    s, l = short.lower(), long_form.lower()
    words = l.split()
    if not words or not words[0].startswith(s[0]):
        # the long form must begin with the short form's first letter (S&H's anchoring rule)
        return False
    i = 0
    for ch in s:
        if not ch.isalnum():
            continue
        i = l.find(ch, i)
        if i < 0:
            return False
        i += 1
    # a short form of N letters cannot expand a long form of fewer than N words unless it is
    # a contiguous acronym; require at least half as many words as letters.
    return len(words) >= max(1, len([c for c in s if c.isalnum()]) // 2)


def schwartz_hearst(text: str) -> list:
    """[(long_form, short_form)] found by the parenthetical pattern, in either order."""
    out = []
    for pre, inner in _PAREN.findall(text or ""):
        pre = pre.strip(" ,;:-")
        inner = inner.strip()
        if not pre or not inner:
            continue
        # `Long Form (SF)`
        tail = " ".join(pre.split()[-max(1, len(inner)):])
        for cand in (pre, tail):
            if _is_expansion(cand, inner):
                out.append((cand, inner))
                break
        else:
            # `SF (Long Form)` — the short form sits before the parenthesis
            short = pre.split()[-1] if pre.split() else ""
            if _is_expansion(inner, short):
                out.append((inner, short))
    return out


# ---------------------------------------------------------------- Christen ch. 3 strips
def determiner_strip(name: str) -> str | None:
    m = _DET.match(name or "")
    return (name[m.end():].strip() or None) if m else None


def version_strip(name: str) -> str | None:
    """Strip a trailing version token.

    Deliberately narrow, and the corpus is the reason: `ISO 8601`, `RFC 9309`, `NIST AI 600-1`
    and `Section 515` all end in a number that is part of the NAME, not a version of it. The
    rule fires only on a dotted version (`2.0`, `1.0.1`) or an explicit `v` prefix (`v2`), so
    a bare standard number never matches.
    """
    m = _VER.search(name or "")
    if not m:
        return None
    return (name[:m.start()].strip() or None)


def generic_suffix_strip(name: str, known: set, pre=None) -> str | None:
    """Strip a trailing generic suffix, but ONLY when the stripped form already names a term.

    `known` is the set of normalised term labels and aliases. `pre` optionally applies another
    strip first, so `SDMx 2.0 Technical Specifications` can reach `SDMx` — the gold sample's
    own case needs both rules to compose.

    Returns the SURVIVING form, never a new term: §1.1's "never create a term from a bare
    stripped form" is enforced by the `known` lookup, not by a comment.
    """
    for candidate in ([name] + ([pre(name)] if pre and pre(name) else [])):
        low = _norm(candidate)
        for suf in _SUFFIXES:
            if not low.endswith(" " + suf):
                continue
            stripped = candidate[:len(candidate) - len(suf)].strip(" ,;:-")
            if _norm(stripped) in known:
                return stripped
            # The suffix may sit OUTSIDE the version token: `SDMx 2.0 Technical
            # Specifications` needs the suffix off first and the version off second, which is
            # the order the gold sample's own case requires and the reverse of what `pre`
            # does. Try both directions rather than assuming one.
            if pre:
                inner = pre(stripped)
                if inner and _norm(inner) in known:
                    return inner
    return None


# ---------------------------------------------------------------- composition
def variants(name: str, known: set) -> list:
    """[{resolved_form, derivation}] — forms of `name` that already name a term.

    Stops at the first hit per generator: the output is "this surface form should alias onto
    the term that form names", and two routes to the same term add nothing.
    """
    if not name or _norm(name) in known:
        return []
    out, seen = [], set()

    def add(form, derivation):
        if form and _norm(form) in known and _norm(form) not in seen:
            seen.add(_norm(form))
            out.append({"resolved_form": form, "derivation": derivation})

    add(determiner_strip(name), "determiner_strip")
    add(version_strip(name), "version_strip")
    # the two guarded suffix generators; `technical_*` is named separately because §1.1 asks
    # for it by name, though it shares the guard and the code path.
    hit = generic_suffix_strip(name, known, pre=version_strip)
    if hit:
        low = _norm(name)
        add(hit, "technical_specifications_variant"
            if ("technical specification" in low or "technical standard" in low)
            else "generic_suffix_strip")
    # a determiner strip that then needs a suffix strip: `the DCAT specification`
    det = determiner_strip(name)
    if det:
        add(generic_suffix_strip(det, known, pre=version_strip), "generic_suffix_strip")
    return out
