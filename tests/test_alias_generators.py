"""Surface-form alias generation (task 2026-09-06_aliases_homograph_judge_epoch2 §1.1).

The gold sample measured stratum D's recall at ZERO: six of twenty near-misses just under the
0.80 embedding floor were genuine matches, and every one was a surface-form variant an
exact-name rule cannot see — `Resource Description Framework (RDF)` against `the W3C RDF
(Resource Description Framework) standard`, `SDMx 2.0 Technical Specifications` against `SDMX
Technical Standards`. That is an alias-generation problem, not a threshold problem, and it has
named prior art:

* **Schwartz & Hearst (2003)**, "A simple algorithm for identifying abbreviation definitions in
  biomedical text", *PSB 2003* — the parenthetical pattern, still the baseline.
* **Christen (2012), *Data Matching* ch. 3** — standardisation before comparison: strip
  determiners, version tokens, generic suffixes.

Every generator here is a REFUSAL as much as a producer. The guard that matters is the one on
`generic_suffix_strip`: a stripped form may only become an alias when the stripped form
ALREADY names a term. Without it, "AI readiness framework" would mint "AI readiness" as a link
target and quietly merge a framework with a concept.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import alias_generators as ag  # noqa: E402


# ------------------------------------------------------------------ Schwartz & Hearst
@pytest.mark.parametrize("text,expected", [
    ("Resource Description Framework (RDF)", ("Resource Description Framework", "RDF")),
    ("the W3C RDF (Resource Description Framework) standard",
     ("Resource Description Framework", "RDF")),
    ("Statistical Data and Metadata eXchange (SDMX) is a standard",
     ("Statistical Data and Metadata eXchange", "SDMX")),
    ("Model Context Protocol (MCP)", ("Model Context Protocol", "MCP")),
])
def test_the_parenthetical_pattern_finds_the_pair_in_either_order(text, expected):
    assert expected in ag.schwartz_hearst(text)


@pytest.mark.parametrize("text", [
    "the data (which is open) is fine",       # parenthetical is a clause, not a short form
    "AI readiness (2026)",                    # a year is not a short form
    "quality (see section 3)",
    "a framework (a very long parenthetical that could not be an abbreviation of anything)",
])
def test_the_parenthetical_pattern_refuses_what_is_not_an_abbreviation(text):
    assert ag.schwartz_hearst(text) == []


def test_a_short_form_whose_letters_are_not_in_the_long_form_is_refused():
    """Schwartz & Hearst's core constraint: every character of the short form must appear in
    the long form, in order. Without it `Data Quality (FAIR)` would mint a false expansion."""
    assert ag.schwartz_hearst("Data Quality (FAIR)") == []
    assert ("Data Quality", "DQ") in ag.schwartz_hearst("Data Quality (DQ)")


# ------------------------------------------------------------------ standardisation strips
@pytest.mark.parametrize("name,stripped", [
    ("the W3C RDF standard", "W3C RDF standard"),
    ("The Open Data Institute", "Open Data Institute"),
    ("a data catalog", "data catalog"),
    ("An inventory", "inventory"),
])
def test_determiner_strip(name, stripped):
    assert ag.determiner_strip(name) == stripped


@pytest.mark.parametrize("name", ["theory of change", "Analysis", "Anonymisation"])
def test_determiner_strip_does_not_eat_a_word_that_merely_starts_with_the(name):
    assert ag.determiner_strip(name) is None


@pytest.mark.parametrize("name,stripped", [
    ("SDMX 2.0", "SDMX"), ("SDMX v2.0", "SDMX"), ("DCAT 3", "DCAT"),
    ("Croissant 1.0.1", "Croissant"),
])
def test_version_strip(name, stripped):
    assert ag.version_strip(name) == stripped


@pytest.mark.parametrize("name", ["ISO 8601", "NIST AI 600-1", "RFC 9309", "Section 515"])
def test_version_strip_leaves_a_number_that_is_part_of_the_name(name):
    """`ISO 8601` is not `ISO` at version 8601. The rule only fires when the remainder is
    still a plausible name AND the number reads as a version — a bare standard number does
    not, which is why the corpus's own standard names are the test cases."""
    assert ag.version_strip(name) is None


# ------------------------------------------------------------------ the guarded generators
def test_generic_suffix_strip_fires_only_when_the_stripped_form_already_names_a_term():
    known = {"sdmx", "dcat"}
    assert ag.generic_suffix_strip("SDMX Technical Standards", known) == "SDMX"
    assert ag.generic_suffix_strip("DCAT specification", known) == "DCAT"
    # the guard: nothing named `ai readiness` exists, so no alias is minted
    assert ag.generic_suffix_strip("AI readiness framework", known) is None
    assert ag.generic_suffix_strip("AI readiness framework", known | {"ai readiness"}) == "AI readiness"


def test_generic_suffix_strip_never_returns_a_bare_stripped_form_as_a_new_term():
    """§1.1: 'never create a term from a bare stripped form'. The generator returns the
    EXISTING form it matched, so the caller can only ever alias onto a term that exists."""
    assert ag.generic_suffix_strip("Some Novel Thing protocol", set()) is None


def test_technical_specifications_and_technical_standards_are_one_suffix():
    known = {"sdmx"}
    assert ag.generic_suffix_strip("SDMx 2.0 Technical Specifications", known,
                                   pre=ag.version_strip) == "SDMx"
    assert ag.generic_suffix_strip("SDMX Technical Standards", known) == "SDMX"


# ------------------------------------------------------------------ the composition
def test_variants_compose_strips_and_stops_at_the_first_hit():
    """`SDMx 2.0 Technical Specifications` needs version-strip AND suffix-strip to reach the
    term `SDMX`. A generator that only applies one rule cannot fix the case the gold sample
    actually found."""
    known = {"sdmx"}
    got = ag.variants("SDMx 2.0 Technical Specifications", known)
    assert any(v["resolved_form"].lower() == "sdmx" for v in got), got


def test_a_name_that_already_resolves_generates_nothing():
    assert ag.variants("SDMX", {"sdmx"}) == []


def test_every_variant_names_its_generator():
    got = ag.variants("the DCAT specification", {"dcat"})
    assert got and all(v["derivation"] in ag.GENERATORS for v in got)
