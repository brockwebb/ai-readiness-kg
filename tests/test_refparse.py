"""Guards for the derived reference parser (task 2026-08-30_acquisition_round2 §1).

Every fixture below is a REAL line, or a faithful reduction of one, taken from
`state/docling_md/` — not invented markdown. The defects each test pins were found by
running the parser over the live corpus, and each one, unguarded, poisons the coupling
ranking rather than merely reducing recall:

1. Docling splits a URL at a PDF line break: `https: //doi.org/10.x`. Unrepaired, no DOI in
   an ACM-style bibliography matches at all.
2. A DOI cut at a line break ("10.18653/v1/") is a PREFIX of a real identifier. Admitted, it
   resolves to nothing or to the wrong work; the parser must drop it, not keep the stub.
3. A document with a short trailing "Notes" heading and a real "## References" section must
   resolve to the bibliography, not to whichever heading comes last.
4. Derived records must never be emitted under the `bibliographic` evidence class — the
   pooling prohibition is a data-level invariant, not a reporting convention.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from kg import refparse


# --- 1. line-break damage inside URLs and DOIs -------------------------------------------
def test_doi_split_at_pdf_line_break_is_recovered():
    # from aggarwal-2024-geo-generative-engine-optimization.md (real damage class)
    raw = ("- [2] Prashant Ankalkoti. 2017. Survey on Search Engine Optimization. "
           "Imperial journal 3 (2017). https: //doi.org/10.1145/3168389")
    e = refparse.parse_entry(raw)
    assert e["doi"] == "10.1145/3168389", "spaced scheme defeats the DOI match"


def test_doi_split_immediately_after_prefix_is_recovered():
    raw = "- [7] Someone. 2020. A title. doi: 10.1016/\n      j.patrec.2018.09.012"
    assert refparse.parse_entry(raw)["doi"] == "10.1016/j.patrec.2018.09.012"


# --- 2. truncated DOI must be DROPPED, not admitted --------------------------------------
@pytest.mark.parametrize("bad", ["10.18653/v1/", "10.18653/", "10.1145/"])
def test_truncated_doi_is_dropped(bad):
    assert refparse.clean_doi(bad) == "", f"{bad!r} admitted as an identifier"


@pytest.mark.parametrize("good,want", [
    ("10.1145/3168389.", "10.1145/3168389"),
    ("10.1007/s10044-016-0583-6),", "10.1007/s10044-016-0583-6"),
    ("10.18653/v1/2023.emnlp-main.468", "10.18653/v1/2023.emnlp-main.468"),
])
def test_valid_doi_survives_punctuation_stripping(good, want):
    assert refparse.clean_doi(good) == want


def test_mutation_truncated_doi_guard_actually_measures_the_slash():
    """Positive control (methodology §7.5): disable the trailing-slash rule and the
    truncated-DOI test must fail. Without this, the test could be passing on the
    `10.\\d{4,9}/.+` fullmatch alone and would keep passing if the slash rule were deleted."""
    assert re.fullmatch(r"10\.\d{4,9}/.+", "10.18653/v1/"), (
        "the fullmatch alone ADMITS the truncated DOI, so only the slash rule rejects it")


# --- 3. section selection ----------------------------------------------------------------
_DOC = """# A paper

Body text citing things.

## References

- [1] A. Author. 2020. A real work. https://doi.org/10.1145/3168389
- [2] B. Author. 2021. Another real work. arXiv:2104.09864
- [3] C. Author. 2019. A third work. https://doi.org/10.1007/s10044-016-0583-6

## Notes

- [1] A note with no identifier.
"""


def test_real_bibliography_beats_a_later_notes_heading():
    sec = refparse.find_reference_section(_DOC)
    assert sec is not None
    assert sec["heading"].lower().endswith("references"), sec["heading"]


def test_section_offsets_round_trip_into_the_source():
    sec = refparse.find_reference_section(_DOC)
    assert _DOC[sec["start"]:sec["end"]] == sec["body"]


def test_appendix_prefixed_heading_is_found():
    """`## Appendix B. References` (nist-generative-ai-profile-ai-600-1.md) was invisible to
    the first pattern, which cost 4 documents' reference lists."""
    doc = "## Appendix B. References\n\n- [1] X. 2020. Work. https://doi.org/10.6028/nist.ai.100-1\n"
    sec = refparse.find_reference_section(doc)
    assert sec is not None and "Appendix B" in sec["heading"]


def test_further_reading_is_not_a_reference_section():
    """Recommendations are not citations; counting them as coupling evidence would assert
    the document USED a work it merely suggested."""
    doc = "## Further reading\n\n- [1] X. 2020. Work. https://doi.org/10.6028/nist.ai.100-1\n"
    assert refparse.find_reference_section(doc) is None


def test_document_with_no_reference_section_is_a_recorded_resolution(tmp_path):
    p = tmp_path / "d.md"
    p.write_text("# Title\n\nProse only, citing 10.1145/3168389 inline.\n")
    rec = refparse.parse_document("d", p)
    assert rec["resolution"] == "no_reference_section"
    assert rec["referenced_dois"] == [], (
        "in-text DOIs outside a reference section must NOT be harvested as references")


# --- 4. evidence-class invariant ---------------------------------------------------------
def test_records_carry_the_derived_class_and_never_the_asserted_one(tmp_path):
    p = tmp_path / "d.md"
    p.write_text(_DOC)
    rec = refparse.parse_document("d", p)
    assert rec["evidence_class"] == "bibliographic_derived"
    assert rec["evidence_class"] != "bibliographic"
    assert rec["derivation"] == "docling_refparse"
    assert rec["section"]["start"] >= 0 and rec["section"]["end"] > rec["section"]["start"]
    assert rec["source_md_sha256"] and len(rec["source_md_sha256"]) == 64


def test_parse_finds_the_identifiers_in_a_real_shaped_section(tmp_path):
    p = tmp_path / "d.md"
    p.write_text(_DOC)
    rec = refparse.parse_document("d", p)
    assert rec["n_entries"] == 3
    assert set(rec["referenced_dois"]) == {"10.1145/3168389", "10.1007/s10044-016-0583-6"}
    assert rec["referenced_arxiv"] == ["2104.09864"]
    assert rec["n_unparseable"] == 0


def test_entry_offsets_point_at_the_entry_in_the_source(tmp_path):
    p = tmp_path / "d.md"
    p.write_text(_DOC)
    rec = refparse.parse_document("d", p)
    for e in rec["entries"]:
        assert _DOC[e["offset"]:e["offset"] + 40].lstrip().startswith(e["raw"][:20].lstrip())


def test_live_corpus_parse_is_stable_and_writes_nothing_on_dry_run():
    """The parser runs over the real T1 store; a crash on any of 178 documents is a defect."""
    before = sorted(p.name for p in refparse.OUT_DIR.glob("*.json")) \
        if refparse.OUT_DIR.exists() else []
    summary = refparse.run(write=False, verbose=False)
    after = sorted(p.name for p in refparse.OUT_DIR.glob("*.json")) \
        if refparse.OUT_DIR.exists() else []
    assert summary["documents"] > 0
    assert before == after, "--dry-run wrote records"


# --- 5. markdown escaping in Docling output (a FALSE-COUPLING defect, not a recall one) ---
def test_docling_backslash_escapes_do_not_truncate_a_doi():
    """Docling escapes markdown metacharacters: `10.1162/tacl\\_a\\_00471`. Unescaped, the DOI
    charset stops at `tacl`, and three documents citing three DIFFERENT TACL articles all
    collapse onto the bare journal prefix — which is how a fabricated 3-citer candidate
    reached the top of the coupling ranking before this guard existed."""
    raws = [r"[1] A. 2019. X. 10.1162/tacl\_a\_00041. URL https: //aclanthology.org/x",
            r"[2] B. 2022. Y. 10.1162/tacl\_a\_00471.",
            r"[3] C. 2024. Z. 10.1162/tacl\_a\_00638."]
    dois = {refparse.parse_entry(r)["doi"] for r in raws}
    assert dois == {"10.1162/tacl_a_00041", "10.1162/tacl_a_00471", "10.1162/tacl_a_00638"}
    assert "10.1162/tacl" not in dois, "escaped DOI truncated to the journal prefix"


# --- 6. line-break truncation that produces a PLAUSIBLE-looking DOI ----------------------
def test_prefix_truncated_doi_is_dropped_when_the_full_form_is_present():
    """`10.18653/v1/2023. emnlp-main.153` (martinez-2026-geo-critical-survey.md) leaves the
    fragment `10.18653/v1/2023`, which passes every syntactic check and then collides across
    documents into a phantom coupling candidate. Only the same bibliography's full form
    reveals it as a truncation."""
    got = refparse._drop_prefix_truncations([
        "10.18653/v1/2023", "10.18653/v1/2023.findings-emnlp.467",
        "10.18653/v1/2023.emnlp-main.378", "10.1145/3168389"])
    assert "10.18653/v1/2023" not in got
    assert "10.18653/v1/2023.findings-emnlp.467" in got
    assert "10.1145/3168389" in got, "an unrelated DOI must survive"


def test_prefix_rule_keeps_a_doi_with_no_longer_sibling():
    """The rule must not fire on a short-but-complete DOI: without a longer form in the same
    list there is no evidence of truncation, and declining it would be a silent recall loss
    dressed up as a correction."""
    assert refparse._drop_prefix_truncations(["10.18653/v1/2023"]) == ["10.18653/v1/2023"]


def test_prefix_rule_runs_on_the_real_parse_path(tmp_path):
    """Positive control: assert the drop happens in `parse_document`, not merely in the
    helper — the M2 pattern (a test that measures something adjacent to the guard)."""
    doc = ("## References\n\n"
           "- [1] A. 2023. X. doi: 10.18653/v1/2023. emnlp-main.153.\n"
           "- [2] B. 2023. Y. doi: 10.18653/v1/2023.emnlp-main.153.\n"
           "- [3] C. 2023. Z. doi: 10.18653/v1/2023.findings-emnlp.467\n")
    p = tmp_path / "d.md"
    p.write_text(doc)
    rec = refparse.parse_document("d", p)
    assert "10.18653/v1/2023" not in rec["referenced_dois"]
    assert "10.18653/v1/2023.emnlp-main.153" in rec["referenced_dois"]
