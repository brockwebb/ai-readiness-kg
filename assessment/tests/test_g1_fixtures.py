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
    # v1 (task 2026-09-03 step 2, epoch g1srp-2026-09-03)
    "statcan-71-543-g-guide-labour-force-survey-2025": REPO / "corpus/g1eval/statcan-71-543-g-guide-labour-force-survey-2025.md",
    "nchs-2017-data-presentation-standards-proportions": REPO / "corpus/g1eval/nchs-2017-data-presentation-standards-proportions.pdf",
    "nchs-2023-data-presentation-standards-rates-counts": REPO / "corpus/g1eval/nchs-2023-data-presentation-standards-rates-counts.pdf",
    "census-acs-data-suppression-rules": REPO / "corpus/g1eval/census-acs-data-suppression-rules.pdf",
}
# Task floors (2026-09-02 step 3; 2026-09-03 step 2): >= 4 development / >= 2 held-out per class.
FLOOR = {"propositions.yaml": 4, "propositions_holdout.yaml": 2}


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


def test_every_class_meets_the_task_floor(fixture_set):
    """v1: SUPPRESSION and RELIABILITY_FLAG populated from the 2026-09-03 admissions; every
    class at or above the task floor (a shortfall would be recorded in the header, and the
    v0 files recorded two)."""
    floor = FLOOR[Path(fixture_set.path).name]
    for cls, n in fixture_set.counts_by_class().items():
        assert n >= floor, (cls, n, floor)


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


# ---------------------------------------------------------------- v2 product-surface fixtures
# (task 2026-09-03_g1_eval_v2 step 2): every passage part verbatim in its captured file, zero
# passage overlap between splits, floors per surface type, table passages of >= 3 rows.
FIX_V2 = FIX / "v2"
SOURCES_V2 = {
    "census-api-acs5-2023-b19013-counties-colorado": REPO / "corpus/g1eval/census-api-acs5-2023-b19013-counties-colorado.md",
    "census-api-acs5-2023-b19013-counties-idaho": REPO / "corpus/g1eval/census-api-acs5-2023-b19013-counties-idaho.md",
    "statcan-14-10-0287-01-lfs-2026-07-provinces-estimate-se-csv": REPO / "corpus/g1eval/statcan-14-10-0287-01-lfs-2026-07-provinces-estimate-se-csv.md",
    "statcan-14-10-0287-01-lfs-2025-12-provinces-estimate-se-csv": REPO / "corpus/g1eval/statcan-14-10-0287-01-lfs-2025-12-provinces-estimate-se-csv.md",
    "statcan-13-10-0096-01-cchs-2022-provinces-percent-ci-csv": REPO / "corpus/g1eval/statcan-13-10-0096-01-cchs-2022-provinces-percent-ci-csv.md",
    "statcan-13-10-0096-01-cube-metadata-csv": REPO / "corpus/g1eval/statcan-13-10-0096-01-cube-metadata-csv.md",
    "statcan-13-10-0113-01-cchs-2021-2022-quebec-health-regions-percent-ci-csv": REPO / "corpus/g1eval/statcan-13-10-0113-01-cchs-2021-2022-quebec-health-regions-percent-ci-csv.md",
    "statcan-13-10-0113-01-cube-metadata-csv": REPO / "corpus/g1eval/statcan-13-10-0113-01-cube-metadata-csv.md",
    "nchs-data-brief-530-perinatal-mortality-2022-2023": REPO / "corpus/g1eval/nchs-data-brief-530-perinatal-mortality-2022-2023.pdf",
    "nchs-data-brief-500-dental-visits-adults-65-2022": REPO / "corpus/g1eval/nchs-data-brief-500-dental-visits-adults-65-2022.pdf",
    "nchs-data-brief-515-high-total-cholesterol-2021-2023": REPO / "corpus/g1eval/nchs-data-brief-515-high-total-cholesterol-2021-2023.pdf",
    "bls-employment-situation-2026-08-news-release": REPO / "corpus/g1eval/bls-employment-situation-2026-08-news-release.md",
    "bls-employment-situation-2026-05-news-release-archive": REPO / "corpus/g1eval/bls-employment-situation-2026-05-news-release-archive.md",
}
FLOOR_V2 = {"propositions.yaml": 6, "propositions_holdout.yaml": 3}
SURFACES_UNDER_TEST = ("table_coded", "table_labeled", "footnoted", "flagged_cell")


@pytest.fixture(scope="module", params=["propositions.yaml", "propositions_holdout.yaml"])
def v2_set(request):
    return load_fixture_set(FIX_V2 / request.param)


def test_v2_every_span_is_verbatim_in_its_passage(v2_set):
    for p in v2_set.propositions:
        assert is_grounded(p.grounding_span, p.context_passage), p.id


def test_v2_every_passage_has_parts_and_a_surface_type(v2_set):
    for pid in v2_set.passage_ids():
        m = v2_set.passage_meta.get(pid)
        assert m and m.get("parts") and m.get("surface_type") in SURFACES_UNDER_TEST, pid
        assert "legend_on_surface" in m and "declared_leg_score" in m, pid


def test_v2_every_surface_type_meets_the_task_floor(v2_set):
    floor = FLOOR_V2[Path(v2_set.path).name]
    counts = v2_set.counts_by_surface()
    for sf in SURFACES_UNDER_TEST:
        assert counts.get(sf, 0) >= floor, (sf, counts, floor)


def test_v2_table_passages_are_blocks_of_at_least_three_rows(v2_set):
    for pid in v2_set.passage_ids():
        m = v2_set.passage_meta[pid]
        if m["surface_type"] in ("table_coded", "table_labeled", "flagged_cell"):
            rows = max(len(part["text"].splitlines()) for part in m["parts"] if part["doc_id"] == m["source_doc_id"])
            assert rows >= 3, (pid, rows)


def test_v2_footnoted_propositions_record_their_distance(v2_set):
    for p in v2_set.propositions:
        if p.surface_type == "footnoted":
            assert isinstance(p.footnote_distance_chars, int) and p.footnote_distance_chars > 0, p.id


def test_v2_table_coded_labels_never_decode_the_surface(v2_set):
    for p in v2_set.propositions:
        if p.surface_type == "table_coded":
            assert p.code_map and "variables" in p.code_map, p.id
            assert "B19013_001E" in p.estimate_label and "income" not in p.estimate_label.lower(), p.id


def test_v2_zero_passage_overlap_between_splits():
    dev = load_fixture_set(FIX_V2 / "propositions.yaml")
    hold = load_fixture_set(FIX_V2 / "propositions_holdout.yaml")
    d = {normalize(t) for t in dev.passages.values()}
    h = {normalize(t) for t in hold.passages.values()}
    assert not (d & h)
    # and no v2 passage repeats a v1 passage (the prose_labeled stratum) either
    for name in ("propositions.yaml", "propositions_holdout.yaml"):
        v1 = {normalize(t) for t in load_fixture_set(FIX / name).passages.values()}
        assert not (v1 & (d | h))


def _source_text_v2(doc_id):
    path = SOURCES_V2[doc_id]
    if not path.exists():
        pytest.skip(f"corpus file not present locally: {path}")
    if path.suffix == ".md":
        return path.read_text(encoding="utf-8")
    pypdf = pytest.importorskip("pypdf")
    return "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(path)).pages)


@pytest.mark.parametrize("doc_id", sorted(SOURCES_V2))
def test_v2_every_passage_part_is_verbatim_in_its_captured_file(doc_id):
    text = _source_text_v2(doc_id)
    seen = 0
    for name in ("propositions.yaml", "propositions_holdout.yaml"):
        fs = load_fixture_set(FIX_V2 / name)
        for pid, m in fs.passage_meta.items():
            for part in m["parts"]:
                if part["doc_id"] == doc_id:
                    seen += 1
                    assert is_grounded(part["text"], text), (name, pid, doc_id)
    assert seen, f"{doc_id} is admitted for v2 fixtures but no passage part cites it"
