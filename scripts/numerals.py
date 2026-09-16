#!/usr/bin/env python3
"""A count, spelled. One map, so a published label and the gate that checks it cannot disagree.

`cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md` decision 1. **Zero spend, no network.**

The map existed already — inline in `scripts/check_protected_abstract_five_checks.sh`, which
reads `legs` off the published tier-A matrix and asserts the abstract spells its length. The
builder that writes the matrix LABELS carried the same numeral as a literal
(`build_l0_site.py:96`, "the six host-level checks"), so the gate and the thing it gates held
two copies of one fact and DD-066 moved only one of them: the abstract said five while four
published labels still said six.

So the map is here, imported by both. There is no second copy to forget.

**Out of range raises.** A label that spells a count is a label whose count is small enough to
spell; past twenty the numeral is the clearer rendering and the caller should print the integer.
Returning a fallback string would put "many host-level checks" on a published page, which is
the class of silent wrong answer this module exists to remove.

    from numerals import word
    word(5)                 # 'five'
    word(5).capitalize()    # 'Five'
"""
from __future__ import annotations

#: 0-20. Beyond that a published label should print the integer, and `word` says so.
WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
    19: "nineteen", 20: "twenty",
}


def word(n: int) -> str:
    """`n` in lowercase English. Capitalise at the call site; a sentence-initial numeral is the
    caller's business and a second map keyed on case is how the first drift happened."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"word() takes an int, not {type(n).__name__}: {n!r}")
    if n not in WORDS:
        raise ValueError(f"{n} is outside the spelled range 0-20; print the integer instead")
    return WORDS[n]
