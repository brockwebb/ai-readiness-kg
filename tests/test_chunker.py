"""Chunker contract (task 2026-08-27_chunked_pilot §2).

The chunked arm's whole claim is that the *unit* changed and nothing else did. These tests
pin the unit: section-bounded, paragraph-integral, capped, bounded overlap, offsets that
round-trip, and a recorded fallback when a document has no structure at all.
"""
from __future__ import annotations

import pytest

from kg.extraction import chunker

CFG = chunker.load_config()


def _cfg(**over):
    return {**CFG, **over}


def _md(n_paras: int, words: int = 60) -> str:
    para = " ".join(f"word{i}" for i in range(words)) + "."
    return "\n\n".join(para for _ in range(n_paras))


# --- rule 1: section boundaries ------------------------------------------------------------
def test_a_chunk_never_crosses_a_heading_at_the_chosen_level():
    src = "".join(f"# Section {i}\n\n{_md(1, 20)}\n\n" for i in range(4))
    cs = chunker.chunk_document("doc", src)
    assert cs.structure_source == "markdown"
    assert cs.heading_level == 1
    assert not cs.no_structure
    # Four H1s, each small enough to fit — one chunk per section, no chunk holding two.
    assert len(cs) == 4
    for c in cs:
        assert c.text.count("# Section ") == 1


def test_level_choice_takes_the_shallowest_level_with_enough_headings():
    # One H1, four H2s -> H2 is the level that produces sections.
    src = "# Top\n\n" + "".join(f"## Sub {i}\n\n{_md(1, 20)}\n\n" for i in range(4))
    cs = chunker.chunk_document("doc", src)
    assert cs.heading_level == 2


# --- rule 2: paragraph integrity -------------------------------------------------------------
def test_no_paragraph_is_ever_split_across_chunks():
    # 40 paragraphs of ~90 tokens: the cap forces many chunks, none mid-paragraph.
    src = _md(40, 60)
    cs = chunker.chunk_document("doc", src)
    assert len(cs) > 1
    paras = [p for p in src.split("\n\n") if p.strip()]
    for c in cs:
        for piece in (p for p in c.text.split("\n\n") if p.strip()):
            assert piece in paras, "a chunk carried a fragment of a paragraph"


# --- rule 3: the cap ---------------------------------------------------------------------------
def test_cap_is_enforced_on_the_emitted_text_not_on_a_sum_of_blocks():
    src = _md(40, 60)
    cs = chunker.chunk_document("doc", src)
    for c in cs:
        if not c.oversize:
            assert chunker.count_tokens(c.text) <= CFG["max_tokens"]
            assert c.n_tokens == chunker.count_tokens(c.text)


def test_an_oversize_paragraph_becomes_its_own_flagged_chunk():
    big = " ".join(f"w{i}" for i in range(4000)) + "."
    src = f"{_md(1, 20)}\n\n{big}\n\n{_md(1, 20)}"
    cs = chunker.chunk_document("doc", src)
    over = [c for c in cs if c.oversize]
    assert len(over) == 1
    assert over[0].text.strip() == big
    assert over[0].n_tokens > CFG["max_tokens"]


# --- rule 4: overlap ----------------------------------------------------------------------------
def test_overlap_repeats_the_previous_chunks_last_paragraph_within_the_bound():
    src = _md(40, 60)
    cs = chunker.chunk_document("doc", src)
    assert len(cs) > 1
    assert cs[0].overlap_text == ""
    for prev, cur in zip(cs.chunks, cs.chunks[1:]):
        assert cur.overlap_text, "every chunk after the first carries overlap"
        assert chunker.count_tokens(cur.overlap_text) <= CFG["overlap_max_tokens"]
        assert cur.overlap_text in prev.text, "overlap must be verbatim from the previous chunk"


def test_a_long_last_paragraph_is_trimmed_to_its_final_sentences():
    text = " ".join(f"Sentence number {i} carries some filler words here." for i in range(200))
    trimmed = chunker.tail_within(text, 100, CFG)
    assert chunker.count_tokens(trimmed) <= 100
    assert text.endswith(trimmed)


# --- rule 6: offsets and ids ------------------------------------------------------------------
def test_offsets_round_trip_and_ids_are_stable():
    src = _md(40, 60)
    cs = chunker.chunk_document("doc", src)
    for i, c in enumerate(cs, 1):
        assert src[c.start:c.end] == c.text
        assert c.chunk_id == f"doc#c{i:04d}"
    assert [c.chunk_id for c in chunker.chunk_document("doc", src)] == [c.chunk_id for c in cs]


def test_the_breadcrumb_is_in_the_model_input_and_never_in_the_grounding_text():
    src = "# Alpha\n\n" + _md(1, 20) + "\n\n# Beta\n\n" + _md(1, 20) + "\n\n# Gamma\n\n" + _md(1, 20)
    cs = chunker.chunk_document("doc", src)
    c = cs[1]
    assert "[section:" in c.model_text("Doc Title")
    assert "Doc Title" in c.model_text("Doc Title")
    assert "[section:" not in c.grounding_text()
    assert c.grounding_text().endswith(c.text)


# --- the no-structure fallback -------------------------------------------------------------------
def test_a_document_with_no_headings_falls_back_to_paragraph_packing_and_records_it():
    src = _md(40, 60)
    cs = chunker.chunk_document("doc", src)
    assert cs.no_structure is True
    assert cs.heading_level is None
    assert len(cs) > 1
    for c in cs:
        assert c.heading_path == ()


# --- plain-text (pypdf) family ---------------------------------------------------------------------
def test_hard_wrapped_pdf_text_gets_headings_and_paragraphs_without_blank_lines():
    wrapped = ("This is a full measure line of text that runs to the right margin edge.\n"
               "Another full measure line of text that runs to the right margin edges.\n"
               "A short closing line.\n")
    src = ("1 INTRODUCTION\n" + wrapped * 3
           + "2 RELATED WORK\n" + wrapped * 3
           + "3 METHOD\n" + wrapped * 3)
    cs = chunker.chunk_document("doc", src)
    assert cs.structure_source == "plain_text"
    assert cs.heading_level == 1
    assert len(cs) == 3
    assert [c.heading_path[-1] for c in cs] == ["1 INTRODUCTION", "2 RELATED WORK", "3 METHOD"]
    for c in cs:
        assert src[c.start:c.end] == c.text


def test_config_is_data_and_a_missing_key_fails_loud(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("max_tokens: 100\n", encoding="utf-8")
    with pytest.raises(chunker.ChunkerError, match="missing required keys"):
        chunker.load_config(bad)


def test_empty_source_is_a_loud_error():
    with pytest.raises(chunker.ChunkerError, match="empty source"):
        chunker.chunk_document("doc", "   \n  ")


def test_a_headings_only_chunk_rides_forward_instead_of_being_emitted_empty():
    # Three H1s in a row with no body under the first two: the section boundaries are real,
    # but a chunk holding only "# A\n\n# B" has nothing to extract from.
    src = "# A\n\n# B\n\n# C\n\n" + _md(1, 20)
    cs = chunker.chunk_document("doc", src)
    assert cs.heading_level == 1
    assert len(cs) == 1
    assert cs[0].text.count("# ") == 3
    assert cs[0].heading_path == ("C",), "the breadcrumb follows the deepest heading held"


def test_a_document_ending_in_a_bare_heading_still_keeps_that_heading():
    src = "# A\n\n" + _md(1, 20) + "\n\n# B\n\n# C\n"
    cs = chunker.chunk_document("doc", src)
    assert "# C" in cs[-1].text
    assert "".join(c.text for c in cs).count("# C") == 1
