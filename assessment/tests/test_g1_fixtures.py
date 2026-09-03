"""Fixture discipline (invariant 3 — no grounding span, no write): every proposition's span
is verbatim in its passage, every passage is verbatim in its admitted source document when
the local corpus file is present, and the loader's normalisation agrees with the KG's."""
import sys
from pathlib import Path

import pytest

from harness.g1_fixtures import FixtureError, is_grounded, load_fixture_set, normalize
from harness.records import QualifierClass

FIX = Path(__file__).parent / "fixtures" / "g1"
REPO = Path(__file__).parents[2]
SOURCES = {
    "census-acs-general-handbook-2020": REPO / "corpus/g1eval/census-acs-general-handbook-2020.pdf",
    "ons-uncertainty-and-how-we-measure-it": REPO / "corpus/g1eval/ons-uncertainty-and-how-we-measure-it.md",
    "census-2020-disclosure-avoidance-handbook-2021": REPO / "corpus/g1eval/census-2020-disclosure-avoidance-handbook-2021.pdf",
}


@pytest.fixture(scope="module", params=["propositions.yaml", "propositions_holdout.yaml"])
def fixture_set(request):
    return load_fixture_set(FIX / request.param)


def test_every_span_is_verbatim_in_its_passage(fixture_set):
    for p in fixture_set.propositions:
        assert is_grounded(p.grounding_span, p.context_passage), p.id


def test_every_proposition_cites_an_admitted_source_and_a_producer_rule(fixture_set):
    for p in fixture_set.propositions:
        assert p.source_doc_id in SOURCES, p.id
        assert p.producer_rule and p.source_doc_id in p.producer_rule, p.id


def test_qualifier_classes_are_the_closed_enum(fixture_set):
    for p in fixture_set.propositions:
        for q in p.qualifiers:
            assert isinstance(q.cls, QualifierClass)


def test_empty_classes_are_recorded_not_silent(fixture_set):
    counts = fixture_set.counts_by_class()
    for cls, n in counts.items():
        if n == 0:
            assert cls in fixture_set.empty_classes, f"{cls} is empty with no recorded reason"
    assert "SUPPRESSION" in fixture_set.empty_classes


def test_loader_normalisation_matches_the_kg_grounding_module():
    sys.path.insert(0, str(REPO))
    from kg.extraction import grounding
    for text in ("sam-\npling error", "ﬁrst  line\n second", "±3,860   people"):
        assert normalize(text) == grounding.normalize(text)


def _source_text(doc_id):
    path = SOURCES[doc_id]
    if not path.exists():
        pytest.skip(f"corpus file not present locally: {path}")
    if path.suffix == ".md":
        return path.read_text(encoding="utf-8")
    pypdf = pytest.importorskip("pypdf")
    return "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(path)).pages)


@pytest.mark.parametrize("doc_id", sorted(SOURCES))
def test_every_passage_is_verbatim_in_the_source_document(doc_id):
    text = _source_text(doc_id)
    for name in ("propositions.yaml", "propositions_holdout.yaml"):
        fs = load_fixture_set(FIX / name)
        for p in fs.propositions:
            if p.source_doc_id == doc_id:
                assert is_grounded(p.context_passage, text), (name, p.id, p.passage_id)


def test_loader_rejects_an_ungrounded_span(tmp_path):
    bad = tmp_path / "p.yaml"
    bad.write_text(
        "passages: {a: 'the value is 5'}\npropositions:\n- id: x\n  source_doc_id: d\n  passage: a\n"
        "  grounding_span: 'the value is 6'\n  estimate: {value: 5, text: '5', unit: count, label: v}\n"
        "  qualifiers: [{class: MOE, value: 1, text: '1', unit: count}]\n  producer_rule: r\n")
    with pytest.raises(FixtureError):
        load_fixture_set(bad)
