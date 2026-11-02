"""The FCSM 20-04 Accessibility concern layer in the record (DN-018, Part A of
`cc_tasks/2026-10-21_fcsm_concern_edges_and_sixteen_checks_one_pager.md`).

The four concern nodes carry text VERBATIM from DN-018 section 3's Mapping A table and the
twenty-three SERVES_FCSM_CONCERN edges reproduce section 4's crosswalk: these are the assertions
that catch a record that drifted from the ruling, or a parser that silently accepted a table of
the wrong shape. Zero spend, no Neo4j: reads the committed record and DN-018.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import apply_fcsm_concerns as AC  # noqa: E402
import diagnostic_package as D  # noqa: E402

#: The four concerns, verbatim from DN-018 section 3's table, as the record must hold them.
EXPECTED_TEXT = {
    "fcsm_20_04_accessibility_c1": "Users can locate and obtain the data product",
    "fcsm_20_04_accessibility_c2": "Documentation is sufficient for users to understand the data product",
    "fcsm_20_04_accessibility_c3": "Data products are available in formats suitable for diverse users",
    "fcsm_20_04_accessibility_c4": "Metadata and supporting materials are provided",
}
#: DN-018 section 4, primary concern per check (the task's "order above").
EXPECTED_PRIMARY = {"A1": "c3", "A2": "c2", "A3": "c3", "A4": "c1", "A5": "c1", "A6": "c4",
                    "A8": "c4", "A9": "c1", "A10": "c3", "A11": "c1", "A12": "c1", "A13": "c1",
                    "B3": "c2", "D1": "c4", "D4": "c1", "F4": "c4"}
#: The seven checks DN-018 section 4 gives a second (`also`) concern, and which.
EXPECTED_ALSO = {"A1": "c1", "A2": "c4", "A3": "c1", "A6": "c1", "A9": "c3", "A13": "c4", "D4": "c4"}


@pytest.fixture(scope="module")
def record():
    return D.load_framework()


def test_four_concern_nodes_carry_the_verbatim_text_and_fixed_identity(record):
    concerns = {n["id"]: n["properties"] for n in record["nodes"] if "FcsmConcern" in n["labels"]}
    assert set(concerns) == set(EXPECTED_TEXT)
    for cid, props in concerns.items():
        assert props["text"] == EXPECTED_TEXT[cid]
        assert props["dimension"] == "Accessibility"
        assert props["domain"] == "Utility"
        assert props["framework"] == "FCSM 20-04"
        assert props["rmf_equivalent"] == "none"
        assert props["source"] == "Webb 2026, doi:10.5281/zenodo.18772590, v2"
        assert props["definition_segment"] == "fcsm_20_04#s389"


def test_the_verbatim_text_is_what_dn018_section_3_holds():
    """Not a copy of the record: parse DN-018 itself, so this fails if the ruling is edited and
    the record is not (or the reverse)."""
    nodes = AC.parse_concerns()
    assert {n["id"]: n["properties"]["text"] for n in nodes} == EXPECTED_TEXT


def test_twenty_three_edges_primary_and_also(record):
    specs = {n["properties"]["indicator_code"]: n["id"] for n in record["nodes"]
             if "MeasurementSpec" in n["labels"] and n["properties"].get("instrument_state")}
    by_spec = {}
    for e in record["edges"]:
        if e["type"] != "SERVES_FCSM_CONCERN":
            continue
        by_spec.setdefault(e["from"], {})[e["properties"]["role"]] = e["to"]
    edges = [e for e in record["edges"] if e["type"] == "SERVES_FCSM_CONCERN"]
    assert len(edges) == 23
    assert sum(1 for e in edges if e["properties"]["role"] == "primary") == 16
    assert sum(1 for e in edges if e["properties"]["role"] == "also") == 7
    for code, concern in EXPECTED_PRIMARY.items():
        got = by_spec[specs[code]]["primary"]
        assert got == f"fcsm_20_04_accessibility_{concern}", (code, got)
    for code, concern in EXPECTED_ALSO.items():
        got = by_spec[specs[code]].get("also")
        assert got == f"fcsm_20_04_accessibility_{concern}", (code, got)
    # no check outside the seven carries an `also` edge
    for spec_id, roles in by_spec.items():
        code = next(c for c, s in specs.items() if s == spec_id)
        assert ("also" in roles) == (code in EXPECTED_ALSO), code


def test_the_counts_keys_are_set(record):
    assert record["counts"]["fcsm_concern_nodes"] == 4
    assert record["counts"]["serves_fcsm_concern_edges"] == 23


def test_build_is_idempotent_over_the_record(record):
    """`build` upserts by identity, so a second application over a record that already has the
    layer changes nothing (which is why a re-run of the script writes the same bytes)."""
    g = copy.deepcopy(record)
    before_nodes = len(g["nodes"])
    before_edges = len(g["edges"])
    AC.build(g)
    assert len(g["nodes"]) == before_nodes
    assert len(g["edges"]) == before_edges
    assert {n["id"] for n in g["nodes"]} == {n["id"] for n in record["nodes"]}


def test_the_parser_refuses_a_table_of_the_wrong_shape(tmp_path, monkeypatch):
    """A later edit to DN-018 that adds or drops a row must fail the parse, not pass silently."""
    text = AC.DN018.read_text(encoding="utf-8")
    broken = "\n".join(l for l in text.splitlines() if not l.strip().startswith("| F4 |"))
    stub = tmp_path / "dn018.md"
    stub.write_text(broken, encoding="utf-8")
    monkeypatch.setattr(AC, "DN018", stub)
    with pytest.raises(SystemExit, match="section 4 has 15 check rows"):
        AC.parse_edges({c: f"spec:{c}" for c in AC.EXPECTED_CHECKS},
                       {f"fcsm_20_04_accessibility_c{i}" for i in range(1, 5)})
