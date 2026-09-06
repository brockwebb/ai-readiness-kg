"""KWIC backfill of bare grounding spans (task 2026-09-06_bare_span_backfill §2-§3).

Luhn (1960), "Key word-in-context index for technical literature", *American Documentation*
11(4): the useful unit is the mention PLUS its bounded context. The extractor emitted the
mention alone for 1,773 named nodes — a heading, a list item, a table cell handed to it with
no surrounding prose — and invariant 3 ("no grounding span, no write") accepted every one,
because the span IS present and IS verbatim. It just says nothing.

Segmentation is on CommonMark block structure (§4-§5), which is deterministic; nothing here
asks a model anything. The tests that matter are the REFUSALS: a backfill that quietly widens
a span to the wrong block is worse than leaving it bare, because the bare span is at least
honestly empty.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import bare_span_backfill as bs  # noqa: E402

DOC = """# AI Maturity Model

Some preamble that introduces the model.

## Dimensions

- Accessibility: the degree to which the organisation can obtain and share the data it needs.
- Accuracy
- Timeliness: whether data arrives in time to be used.

| Dimension | Score |
|---|---|
| Governance | 3 |

### Accountability

Accountability means an owner is named for every model in production.
"""


# ------------------------------------------------------------------ segmentation
def test_blocks_carry_their_kind_and_their_heading():
    blocks = bs.blocks(DOC)
    kinds = {b["kind"] for b in blocks}
    assert {"heading", "paragraph", "list_item", "table_row"} <= kinds, kinds
    li = [b for b in blocks if b["kind"] == "list_item" and "Timeliness" in b["text"]][0]
    assert li["heading"] == "Dimensions"


def test_each_block_records_a_char_range_that_indexes_back_into_the_document():
    """The range is provenance: it must reproduce the block's text exactly once the markup
    the block carried is stripped the same way. Comparing to the raw slice would fail on the
    `- ` and `## ` the span deliberately drops, so the check applies the same transform —
    which is what makes it a check on the RANGE rather than on the formatting."""
    for b in bs.blocks(DOC):
        assert bs.strip_marker(DOC[b["start"]:b["end"]]) == b["text"]


# ------------------------------------------------------------------ locating the mention
def test_a_name_is_found_in_the_smallest_block_that_contains_it():
    got = bs.locate(DOC, "Timeliness", location=None)
    assert got and got["kind"] == "list_item"
    assert "arrives in time" in got["text"]


def test_location_disambiguates_between_two_blocks_holding_the_same_name():
    doc = "## Alpha\n\nQuality matters here.\n\n## Beta\n\nQuality matters differently here.\n"
    a = bs.locate(doc, "Quality", location="Alpha")
    b = bs.locate(doc, "Quality", location="Beta")
    assert "matters here" in a["text"] and "differently" in b["text"]


def test_a_location_that_matches_nothing_falls_back_rather_than_failing():
    """`location` is model-authored free text — `DIME PROJECT banner` names no heading in any
    substrate. It may only disambiguate; it must never be able to lose a match."""
    got = bs.locate(DOC, "Timeliness", location="DIME PROJECT banner")
    assert got and "arrives in time" in got["text"]


def test_a_name_that_does_not_occur_returns_nothing():
    assert bs.locate(DOC, "Provenance", location=None) is None


# ------------------------------------------------------------------ span selection
def test_a_list_item_with_context_is_the_span():
    span, kind = bs.span_for(DOC, bs.locate(DOC, "Timeliness", None), "Timeliness")
    assert span.startswith("Timeliness") and "arrives in time" in span
    assert kind == "list_item"


def test_a_bare_heading_extends_into_the_following_block():
    """`### Accountability` alone is exactly as empty as the bare span it would replace."""
    span, kind = bs.span_for(DOC, bs.locate(DOC, "Accountability", None), "Accountability")
    assert "an owner is named" in span, span


def test_a_list_item_that_is_only_the_name_extends():
    """`- Accuracy` is 1 non-name token. Widening to the block alone buys nothing."""
    span, _ = bs.span_for(DOC, bs.locate(DOC, "Accuracy", None), "Accuracy")
    assert len(span.split()) >= bs.MIN_TOKENS, span


def test_the_span_is_capped_and_truncated_at_a_sentence_boundary():
    long_doc = "## H\n\n" + ("Alpha is a thing. " * 60) + "\n"
    span, _ = bs.span_for(long_doc, bs.locate(long_doc, "Alpha", None), "Alpha")
    assert len(span) <= bs.MAX_CHARS
    assert span.rstrip().endswith(".")


def test_a_span_that_lost_the_name_is_refused():
    """§2.5: a new span not containing its own name is a defect, not a better span."""
    assert bs.contains_name("Accountability means an owner is named", "Accountability")
    assert not bs.contains_name("an owner is named for every model", "Accountability")


def test_the_name_check_tolerates_inflection_and_case():
    assert bs.contains_name("The DATASETS are documented.", "dataset")
    assert bs.contains_name("machine-readable formats matter", "Machine-readable format")


# ------------------------------------------------------------------ the §3 floor
@pytest.mark.parametrize("span,name,thin", [
    ("Accessibility", "Accessibility", True),                       # bare
    ("- Accuracy", "Accuracy", True),                               # list bullet, no context
    ("| Governance | 3 |", "Governance", True),                     # table cell
    ("Accessibility: the degree to which the organisation can obtain the data.",
     "Accessibility", False),
    ("RDF 1.1", "RDF", True),                                       # the known cost, kept
])
def test_the_invariant_3_floor_flags_thin_spans(span, name, thin):
    """A span passes when it has >= 8 tokens OR >= 3 tokens outside the name. `RDF 1.1` is
    flagged and that is recorded as the floor's known cost: thinness is exactly what it
    measures, and carving an exception for short standard names would make the floor
    unfalsifiable."""
    assert bs.is_thin(span, name) is thin


def test_the_floor_passes_a_long_span_that_is_mostly_the_name():
    long_name = "Statistical Data and Metadata eXchange technical specification"
    assert not bs.is_thin(long_name + " is published by the SDMX initiative.", long_name)


def test_the_window_centres_on_the_mention_rather_than_truncating_from_the_start():
    """KWIC means keyword IN CONTEXT (Luhn 1960). A long block whose mention sits near the END
    must yield a span that still CONTAINS the mention — truncating from the block's start
    drops it, which is how 1,190 of 1,773 nodes failed the §2.5 name check on the first pass.
    """
    filler = "Some entirely unrelated sentence about governance. " * 20
    doc = f"## H\n\n{filler}The term Provenance means the lineage of a data product. More text.\n"
    block = bs.locate(doc, "Provenance", None)
    span, _ = bs.span_for(doc, block, "Provenance")
    assert len(span) <= bs.MAX_CHARS
    assert bs.contains_name(span, "Provenance"), span
    assert "lineage of a data product" in span


def test_a_mention_near_the_start_of_a_long_block_still_yields_a_forward_window():
    filler = " Trailing sentence about something else." * 40
    doc = f"## H\n\nProvenance means the lineage of a data product.{filler}\n"
    span, _ = bs.span_for(doc, bs.locate(doc, "Provenance", None), "Provenance")
    assert bs.contains_name(span, "Provenance") and len(span) <= bs.MAX_CHARS
    assert "lineage" in span
