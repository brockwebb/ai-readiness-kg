"""The controlled vocabulary and its alias-first resolution.

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §1.1-§1.3. The vocabulary is an
append-only event stream like everything else here: `term_added`, `term_alias_added`,
`term_deprecated`, `vocabulary_epoch`. A term is never edited and never deleted, so a
`RESOLVES_TO` edge written under epoch 1 still resolves after epoch 2 changes the label.

The tests that matter are the REFUSALS. An alias table that guesses is worse than no alias
table, because a wrong link is invisible where an unresolved node is counted — so the two
cases with teeth are (a) a name claimed by two terms resolves to NEITHER, and (b) a deprecated
term stops resolving without its history disappearing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg import eventlog, vocab  # noqa: E402


@pytest.fixture
def venv(tmp_path, monkeypatch):
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    return tmp_path


# ------------------------------------------------------------------ normalisation
@pytest.mark.parametrize("a,b", [
    ("AI readiness", "ai readiness"),          # case
    ("AI  readiness", "ai readiness"),         # internal whitespace
    ("  AI readiness ", "ai readiness"),       # edges
    ("AI-readiness", "ai readiness"),          # hyphen is a separator, not a character
    ("AI readiness.", "ai readiness"),         # trailing punctuation
    ("“AI readiness”", "ai readiness"),        # smart quotes (NFKC + strip)
    ("ﬁtness for use", "fitness for use"),     # NFKC ligature
    ("datasets", "dataset"),                   # plural fold
    ("Data Products", "data product"),         # both
    ("identifiers", "identifier"),
    ("policies", "policy"),                    # -ies
    ("indexes", "index"),                      # -es after x
])
def test_names_that_denote_the_same_term_normalise_together(a, b):
    assert vocab.normalize(a) == vocab.normalize(b)


@pytest.mark.parametrize("a,b", [
    ("bias", "bia"),          # -ss/-s nouns are not stripped to a stem
    ("access", "acces"),
    ("metadata", "metadatum"),
    ("provenance", "provenanc"),
    ("AI readiness", "AI ready"),   # readiness and ready are different terms, not inflections
])
def test_names_that_denote_different_things_stay_apart(a, b):
    assert vocab.normalize(a) != vocab.normalize(b)


def test_normalize_returns_none_for_nothing():
    assert vocab.normalize(None) is None
    assert vocab.normalize("   ") is None
    assert vocab.normalize("...") is None


# ------------------------------------------------------------------ the event stream
def test_a_term_projects_from_its_events(venv):
    vocab.add_term("air:ai-readiness", "AI readiness", "Whether an organisation can adopt AI.",
                   source="docs/crosswalk/assessment_protocol.md")
    vocab.add_alias("air:ai-readiness", "AI-readiness", source="graph aliases")
    t = vocab.project()["air:ai-readiness"]
    assert t["pref_label"] == "AI readiness"
    assert "AI-readiness" in t["alt_labels"]
    assert t["state"] == "active"
    assert t["sources"]


def test_a_deprecated_term_stops_resolving_but_keeps_its_history(venv):
    vocab.add_term("air:old", "Old term", "note", source="s")
    assert vocab.resolve("Old term") == "air:old"
    vocab.deprecate("air:old", reason="folded into air:new", replaced_by="air:new")
    assert vocab.resolve("Old term") is None
    t = vocab.project()["air:old"]
    assert t["state"] == "deprecated" and t["replaced_by"] == "air:new"


def test_an_epoch_is_declared_and_counted(venv):
    vocab.add_term("air:a", "A", "n", source="s")
    vocab.declare_epoch(1, "seed")
    assert vocab.epoch() == 1
    vocab.declare_epoch(2, "residue promotion")
    assert vocab.epoch() == 2


# ------------------------------------------------------------------ resolution, and its refusals
def test_a_name_matching_exactly_one_term_resolves(venv):
    vocab.add_term("air:dcat", "DCAT", "W3C Data Catalog Vocabulary.", source="w3c-dcat-3")
    vocab.add_alias("air:dcat", "Data Catalog Vocabulary", source="w3c-dcat-3")
    assert vocab.resolve("dcat") == "air:dcat"
    assert vocab.resolve("Data  Catalog  Vocabulary") == "air:dcat"


def test_a_name_claimed_by_two_terms_resolves_to_neither(venv):
    """§1.3: 'a node with two equally plausible terms is NOT auto-linked'. This is the test
    the whole alias layer is worth having — a table that picks one is silently wrong, and the
    node it mislabels is no longer counted as unresolved, so nothing ever finds the error."""
    vocab.add_term("air:coverage-a", "Coverage", "Sampling coverage of a population.", source="s1")
    vocab.add_term("air:coverage-b", "Coverage", "Catalog coverage of an agency's products.", source="s2")
    assert vocab.resolve("coverage") is None
    assert vocab.alias_index()[vocab.normalize("coverage")] == ["air:coverage-a", "air:coverage-b"]


def test_an_unknown_name_resolves_to_nothing_rather_than_the_closest_term(venv):
    vocab.add_term("air:dcat", "DCAT", "n", source="s")
    assert vocab.resolve("DCAT-US") is None
    assert vocab.resolve("") is None


def test_deprecating_one_of_two_claimants_makes_the_other_resolvable(venv):
    """The ambiguity refusal is not permanent state, it is a live read of the log."""
    vocab.add_term("air:c-a", "Coverage", "n", source="s1")
    vocab.add_term("air:c-b", "Coverage", "n", source="s2")
    assert vocab.resolve("Coverage") is None
    vocab.deprecate("air:c-b", reason="duplicate of air:c-a", replaced_by="air:c-a")
    assert vocab.resolve("Coverage") == "air:c-a"


def test_the_alias_index_is_built_once_and_can_be_passed_in(venv):
    """The loader resolves thousands of nodes; rebuilding the index per node would replay the
    whole log per node. The index is an argument so the caller can hoist it."""
    vocab.add_term("air:a", "Alpha", "n", source="s")
    idx = vocab.alias_index()
    assert vocab.resolve("alpha", index=idx) == "air:a"


@pytest.mark.parametrize("plural,singular", [
    ("data areas", "data area"),        # the suffix heuristic used to refuse -as outright
    ("schemas", "schema"),
    ("aliases", "alias"),               # ...while the exception list keeps `alias` itself whole
    ("biases", "bias"),
    ("processes", "process"),
    ("classes", "class"),
    ("vintages", "vintage"),
])
def test_the_plural_fold_reaches_the_words_the_suffix_rule_missed(plural, singular):
    assert vocab.normalize(plural) == vocab.normalize(singular)


@pytest.mark.parametrize("word", [
    "alias", "bias", "analysis", "status", "census", "corpus", "series", "access",
    "readiness", "completeness", "timeliness", "process", "class",
])
def test_singular_nouns_ending_in_s_survive_the_fold(word):
    """The list is closed and stated; a suffix rule wide enough to cover it would also merge
    terms nobody inspected."""
    assert vocab.normalize(word) == word


# ------------------------------------------------------------------ against the live vocabulary
def test_no_active_graph_derived_term_is_visible_to_every_blocking_scope():
    """Regression guard for a defect made and corrected in the authoring session.

    A term derived from graph nodes MUST record the KG label those nodes carried, because
    `alias_index(node_label=…)` treats a term with no labels as label-agnostic and shows it to
    every block. An unlabelled graph term therefore lets an `Instrument` named "Coverage" link
    to a term built from `Concept` nodes — exactly the cross-label merge §1.3's blocking rule
    exists to refuse, decided at seed time where no reviewer would ever see it.

    Curated terms (the framework, the discovery stack, the search-optimisation lineage) are
    deliberately label-agnostic: a person authored them to name a thing.
    """
    live = vocab.project()
    offenders = [tid for tid, t in live.items()
                 if t["state"] == "active" and not t.get("node_labels")
                 and (t.get("sources") or [""])[0].startswith("graph: ")]
    assert not offenders, f"{len(offenders)} label-agnostic graph terms: {offenders[:5]}"


def test_every_live_term_carries_a_source():
    live = vocab.project()
    missing = [tid for tid, t in live.items() if not t.get("sources")]
    assert not missing, f"{len(missing)} terms with no dcterms:source: {missing[:5]}"
