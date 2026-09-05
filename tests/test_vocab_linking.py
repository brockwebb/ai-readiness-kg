"""Fellegi-Sunter thresholds over the vocabulary (task §1.3).

Fellegi & Sunter (1969) split record pairs three ways with two thresholds: above the upper
one, link automatically; below the lower one, reject automatically; between them sits the
clerical-review band a human reads. The whole point of the design is that the BAND is where
the judgment goes, and that the two automatic zones are cheap and defensible. These tests are
about the two automatic zones and the boundary between them; §2 is what happens in the band.

The tests that matter are again the refusals — the band is only affordable because the
automatic zones are narrow and honest about what they cannot decide.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog, vocab  # noqa: E402

import link_vocabulary as lv  # noqa: E402


@pytest.fixture
def venv(tmp_path, monkeypatch):
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    vocab.add_term("air:concept/dcat", "DCAT", "W3C Data Catalog Vocabulary.",
                   source="graph: 3 Concept nodes", node_labels=["Concept"])
    vocab.add_alias("air:concept/dcat", "Data Catalog Vocabulary", source="s")
    vocab.add_term("air:standard/dcat", "DCAT", "The standard, as a Standard node.",
                   source="graph: 4 Standard nodes", node_labels=["Standard"])
    vocab.add_term("air:concept/coverage", "Coverage", "Sampling coverage.",
                   source="graph: 2 Concept nodes", node_labels=["Concept"])
    vocab.add_term("air:coverage-curated", "Coverage", "A curated, label-agnostic term.",
                   source="docs/crosswalk/assessment_protocol.md")
    return tmp_path


# ------------------------------------------------------------------ upper threshold
def test_a_node_whose_name_is_a_terms_label_auto_links_within_its_own_label(venv):
    got = lv.auto_link([{"key": "d#n1", "label": "Concept", "name": "dcat"}])
    assert got["linked"] == [("d#n1", "air:concept/dcat")]
    assert got["unlinked"] == []


def test_an_alias_of_exactly_one_term_auto_links(venv):
    got = lv.auto_link([{"key": "d#n1", "label": "Concept", "name": "Data  Catalog Vocabulary"}])
    assert got["linked"] == [("d#n1", "air:concept/dcat")]


def test_blocking_keeps_a_standard_node_off_a_concept_terms_alias(venv):
    """`Data Catalog Vocabulary` is an alias of the CONCEPT term only. A Standard node
    carrying that name must not reach it — same string, different block."""
    got = lv.auto_link([{"key": "d#n1", "label": "Standard", "name": "Data Catalog Vocabulary"}])
    assert got["linked"] == []
    assert got["unlinked"][0]["key"] == "d#n1"


def test_a_standard_node_reaches_the_standard_term_of_the_same_name(venv):
    got = lv.auto_link([{"key": "d#n1", "label": "Standard", "name": "DCAT"}])
    assert got["linked"] == [("d#n1", "air:standard/dcat")]


def test_a_name_claimed_by_a_scoped_term_and_a_curated_term_auto_links_to_neither(venv):
    """Two claimants inside one block. §1.3: not auto-linked. The pair goes to the band."""
    got = lv.auto_link([{"key": "d#n1", "label": "Concept", "name": "Coverage"}])
    assert got["linked"] == []
    assert got["unlinked"][0]["key"] == "d#n1"


def test_a_node_with_no_name_is_never_linked(venv):
    got = lv.auto_link([{"key": "d#n1", "label": "Concept", "name": None},
                        {"key": "d#n2", "label": "Concept", "name": "   "}])
    assert got["linked"] == []
    assert len(got["unlinked"]) == 2


# ------------------------------------------------------------------ the band and the lower threshold
def _pairs(scored):
    return [(p["key"], p["term_id"], round(p["cosine"], 3)) for p in scored]


def test_the_band_is_half_open_on_both_ends():
    """[LOWER, 1.0): a cosine of exactly LOWER is IN the band (it is not auto-rejected), and a
    node that auto-linked never reaches the band at all. Stated as a test because an
    off-by-one at a pre-registered threshold silently moves a registered count."""
    rows = [{"key": "a", "label": "Concept", "name": "x", "span": ""},
            {"key": "b", "label": "Concept", "name": "y", "span": ""},
            {"key": "c", "label": "Concept", "name": "z", "span": ""}]
    sims = {"a": ("air:t1", lv.LOWER), "b": ("air:t1", lv.LOWER - 1e-9),
            "c": ("air:t1", 0.99)}
    band, rejected = lv.split_band(rows, sims)
    assert _pairs(band) == [("a", "air:t1", round(lv.LOWER, 3)), ("c", "air:t1", 0.99)]
    assert [r["key"] for r in rejected] == ["b"]


def test_a_rejected_node_is_reported_as_unresolved_rather_than_dropped():
    rows = [{"key": "b", "label": "Concept", "name": "y", "span": ""}]
    band, rejected = lv.split_band(rows, {"b": ("air:t1", 0.1)})
    assert band == []
    assert rejected[0]["key"] == "b" and rejected[0]["unresolved"] is True


def test_a_node_with_no_similar_term_at_all_is_rejected_not_crashed():
    rows = [{"key": "b", "label": "Concept", "name": "y", "span": ""}]
    band, rejected = lv.split_band(rows, {})
    assert band == [] and rejected[0]["key"] == "b"


def test_the_band_offers_one_term_per_node_not_a_shortlist():
    """§2 prices the band per pair. Offering five terms per node would multiply the spend
    without adding a decision: the reviewer's question is 'does this node denote this term',
    and the best-scoring term is the only one that question is worth asking about."""
    rows = [{"key": "a", "label": "Concept", "name": "x", "span": ""}]
    band, _ = lv.split_band(rows, {"a": ("air:t1", 0.9)})
    assert len(band) == 1
