"""v0.3.7 emission contract (chunked_pilot ADDENDUM-01 §2, built under ADDENDUM-03 §1).

Four mechanisms, each with a seeded known-bad (methodology §7.5) and each mutation-checked to
confirm the test measures the guard rather than its neighbour — the M2 failure mode from task
204bc046, which has now recurred three times and is the specific thing ADDENDUM-03 §1.6 names:

  1. anchors  — model emits a pointer; the harness derives the span FROM THE SOURCE
  2. salience — no exhaustive-inventory instruction, one gleaning pass
  3. closed lists enforced at PARSE, raw preserved
  4. type reconciliation at MERGE, not per chunk

Zero model spend: nothing here calls model_stub.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg.extraction import anchors, grounding, merge  # noqa: E402
from kg.extraction.parser import (  # noqa: E402
    DIVERSION_REASONS, normalize_diversion_reason, parse_extraction)

CHUNK = ("AIDRIN is a data readiness tool.\n"
         "It scores six dimensions on a 0-1 scale. The tool was released in 2024.\n"
         "Other systems exist too.")


# ---------------------------------------------------------------- 1. the anchor contract

def test_span_is_cut_from_the_source_not_taken_from_the_model():
    """The warrant for skipping the model's typing is that the span comes from the document.
    A model-supplied `grounding_span` must NOT survive — honouring one reopens exactly the
    drift (`span_partial`) that the anchor contract exists to close."""
    item = {"name": "AIDRIN", "anchor": "six dimensions",
            "grounding_span": "A SPAN THE MODEL INVENTED THAT IS NOT IN THE SOURCE"}
    out, reason = anchors.apply_anchor_contract(item, CHUNK)
    assert reason is None
    assert out["grounding_span"] == "It scores six dimensions on a 0-1 scale."
    assert grounding.is_grounded(out["grounding_span"], CHUNK)
    assert "INVENTED" not in out["grounding_span"]


def test_missing_anchor_is_quarantined():
    _, reason = anchors.derive_span("", CHUNK)
    assert reason.startswith(anchors.NOT_LOCATED)


def test_unlocatable_anchor_is_quarantined_not_guessed():
    span, reason = anchors.derive_span("quantum entanglement", CHUNK)
    assert span is None and reason.startswith(anchors.NOT_LOCATED)


def test_ambiguous_anchor_is_quarantined():
    """The contract says shortest UNIQUE substring. A repeated anchor names no single place,
    so deriving a span from the first hit would be a coin flip written into the graph."""
    assert CHUNK.count("tool") == 2, "fixture no longer exercises ambiguity"
    span, reason = anchors.derive_span("tool", CHUNK)
    assert span is None and "ambiguous" in reason


def test_overlong_anchor_is_refused():
    """The entire cost argument rests on the anchor being short; an unbounded anchor is the
    retyping behaviour returning through a side door."""
    long_anchor = " ".join(f"w{i}" for i in range(anchors.MAX_ANCHOR_TOKENS + 1))
    span, reason = anchors.derive_span(long_anchor, CHUNK)
    assert span is None and "over the" in reason


def test_anchor_matches_across_hyphenated_line_break_and_ligature():
    """Reuses grounding.normalize's tolerances rather than forking them."""
    text = "The read-\nability of the ﬁle is high. Next sentence."
    span, reason = anchors.derive_span("readability", text)
    assert reason is None
    assert span == "The read-\nability of the ﬁle is high.", span


def test_hyphenated_line_break_is_not_a_sentence_boundary():
    """Seeded from a real defect found by this module's own smoke test: the newline inside
    `read-\\nability` was read as a sentence end, yielding "ability of the file is high." —
    a span that IS present in the source and is still wrong."""
    text = "The read-\nability of the file is high. Next sentence."
    span, _ = anchors.derive_span("file", text)
    assert span.startswith("The read-"), f"span cut mid-word at a hyphen line break: {span!r}"


def test_offset_map_agrees_with_the_shared_normalizer():
    """The locator rebuilds grounding.normalize to get offsets. If the rebuild ever diverges
    the mapping is untrustworthy, so it is verified rather than assumed."""
    for text in [CHUNK, "a­ b", "ﬁle read-\nable  spaced", "", "   ", "Ünïcodé ﬂow"]:
        norm, idx = anchors._normalize_with_map(text)
        assert norm == grounding.normalize(text), f"rebuild diverged on {text!r}"
        assert len(idx) == len(norm)


def test_unverifiable_offsets_fail_closed(monkeypatch):
    """Positive control for the fail-closed path: if the rebuild cannot be verified, the
    module must refuse to cut a span rather than cut one from coordinates it cannot vouch
    for. A wrong span is worse than a missing one — it still looks grounded."""
    monkeypatch.setattr(anchors, "_verify", lambda text, norm: False)
    assert anchors.locate_all("AIDRIN", CHUNK) is None
    span, reason = anchors.derive_span("AIDRIN", CHUNK)
    assert span is None and "offset mapping failed verification" in reason


# ------------------------------------------------------------------------- 2. salience

def _v037_prompt() -> str:
    """Whitespace-collapsed, because the prompt is hard-wrapped and a test that depends on
    where a line happens to break is measuring the wrapper, not the instruction."""
    raw = (REPO / "kg" / "extraction" / "prompt_template_v0_3_7.md").read_text(encoding="utf-8")
    return " ".join(raw.split())


def test_prompt_drops_the_exhaustive_inventory_instruction():
    """Seeded known-bad is the previous template's own wording: if it survives, the salience
    change did not happen."""
    text = _v037_prompt()
    # The seeded known-bads are the PREVIOUS template's actual instructions, verbatim. A bare
    # substring like "exhaustive list" would also match this template's own sentence saying an
    # exhaustive list is NOT wanted — which would be the test measuring a word, not a rule.
    for banned in ("an exhaustive list of the substantive ideas THIS CHUNK uses",
                   "the exhaustive Concept layer",
                   "concept_inventory",
                   "Be thorough: thin concept coverage is a known failure mode"):
        assert banned not in text, f"exhaustiveness instruction survived: {banned!r}"
    assert "Salience, not exhaustiveness" in text
    # and the old wording really was present in the template this was derived from
    prior = " ".join((REPO / "kg" / "extraction" / "chunked_template.md")
                     .read_text(encoding="utf-8").split())
    assert "the exhaustive Concept layer" in prior, "banned strings no longer seeded from v0.3.5"


def test_prompt_states_the_anchor_contract_and_forbids_typed_spans():
    text = _v037_prompt()
    assert "shortest substring of the chunk text that occurs exactly once" in text
    assert f"At most {anchors.MAX_ANCHOR_TOKENS} tokens" in text
    assert "Do **not** emit `grounding_span` at all" in text


def test_prompt_permits_exactly_one_gleaning_pass_names_only():
    text = _v037_prompt()
    assert "`gleaned`" in text and "names only" in text
    assert "ONE pass" in text


def test_prompt_restates_the_closed_diversion_list_that_the_parser_enforces():
    """The prompt and the parser must name the same vocabulary; a prompt that offers a value
    the parser normalizes away is instructing the model to waste output."""
    text = _v037_prompt()
    for reason in DIVERSION_REASONS:
        if reason == "unstated":       # harness-supplied for an omitted field, not offered
            continue
        assert f"`{reason}`" in text, f"{reason} missing from the prompt's closed list"


# --------------------------------------------------------- 3. closed list enforced at parse

@pytest.mark.parametrize("raw,expected", [
    ("cross_chunk", "cross_chunk"),
    ("distance_exceeded: 900 chars apart", "distance_exceeded"),
    ("structural_evidence_only — Table 2 groups Lexical Diversity", "structural_inference"),
    ("Structural Only", "structural_inference"),
    ("unsupported_edge_type", "other:schema_cannot_express"),
    ("a whole sentence the model made up", "other"),
    (None, "unstated"),
])
def test_diversion_reason_is_normalized_at_parse(raw, expected):
    assert normalize_diversion_reason(raw) == expected


def test_parse_normalizes_the_reason_and_preserves_the_raw_value():
    """Normalization is for the vocabulary, not a licence to discard what the model said."""
    raw = "structural_evidence_only — Table 2 groups Lexical Diversity under Textual Data"
    out = parse_extraction(
        {"document_id": "d", "concepts": [], "edges": [],
         "proposed_relationships": [{"suggested_edge": "groups", "from_id": "a", "to_id": "b",
                                     "grounding_span": "AIDRIN is a data readiness tool.",
                                     "diversion_reason": raw}]},
        CHUNK)
    pr = out.proposed_relationships[0]
    assert pr["diversion_reason"] == "structural_inference"
    assert pr["diversion_reason_raw"] == raw, "the model's own words were discarded"


def test_out_of_list_value_never_reaches_the_shard_as_itself():
    """Seeded known-bad: a value outside the list. It must be mapped, not passed through —
    the model emitted 34 distinct values over 10 chunks, so pass-through is the live case."""
    out = parse_extraction(
        {"document_id": "d", "concepts": [], "edges": [],
         "proposed_relationships": [{"suggested_edge": "x", "from_id": "a", "to_id": "b",
                                     "grounding_span": "AIDRIN is a data readiness tool.",
                                     "diversion_reason": "the table groups these together"}]},
        CHUNK)
    assert out.proposed_relationships[0]["diversion_reason"] == "other"


def test_one_definition_of_the_closed_list_in_the_repo():
    """chunked_pilot.py used to carry its own copy. Two copies of a vocabulary is how the
    'resolved' definition drifted across three call sites in the T0 layer."""
    import chunked_pilot
    assert chunked_pilot.normalize_reason is normalize_diversion_reason
    assert chunked_pilot.DIVERSION_REASONS is DIVERSION_REASONS


# ------------------------------------------------------- 4. type reconciliation at merge

def _obs(t, chunk, evidence=False):
    return {"name": "Lexical Diversity", "type": t, "chunk_id": chunk,
            "instrument_evidence": evidence}


def test_instrument_evidence_beats_a_concept_majority():
    """Asymmetric on purpose: Instrument evidence is a POSITIVE observation, Concept is the
    default a chunk falls back to when it says nothing more. A majority of uninformative
    views must not outvote one informative one."""
    d = merge.reconcile_type([_obs("Concept", "c1"), _obs("Concept", "c2"),
                              _obs("Concept", "c3"), _obs("Instrument", "c4", True)])
    assert d["type"] == "Instrument" and d["rule"] == "instrument_evidence_wins"
    assert d["evidence_chunks"] == ["c4"]


def test_instrument_typing_without_evidence_does_not_win():
    """Seeded known-bad: the privileged type claimed WITHOUT grounded evidence must fall
    through to the count, or the rule becomes 'whoever says Instrument wins'."""
    d = merge.reconcile_type([_obs("Concept", "c1"), _obs("Concept", "c2"),
                              _obs("Instrument", "c3", False)])
    assert d["type"] == "Concept" and d["rule"] == "majority"


def test_majority_decides_when_no_instrument_evidence():
    d = merge.reconcile_type([_obs("Concept", "c1"), _obs("Standard", "c2"),
                              _obs("Concept", "c3")])
    assert d["type"] == "Concept" and d["rule"] == "majority"


def test_a_tie_is_flagged_not_broken_by_ordering():
    """A coin flip would put an arbitrary type in the graph and leave no trace that it was
    arbitrary. Order is varied to prove the outcome does not depend on it."""
    a = merge.reconcile_type([_obs("Concept", "c1"), _obs("Standard", "c2")])
    b = merge.reconcile_type([_obs("Standard", "c2"), _obs("Concept", "c1")])
    assert a["rule"] == merge.TYPE_CONFLICT and b["rule"] == merge.TYPE_CONFLICT
    assert a["conflict"] and a["type"] is None
    assert a["tied"] == b["tied"] == ["Concept", "Standard"]


def test_conflicted_entities_are_excluded_from_strata_pooling():
    """Pooling an entity whose type is unresolved puts the conflict into a gate denominator."""
    tie = merge.reconcile_type([_obs("Concept", "c1"), _obs("Standard", "c2")])
    ok = merge.reconcile_type([_obs("Concept", "c1"), _obs("Concept", "c2")])
    assert not merge.poolable(tie) and merge.poolable(ok)


def test_reconciliation_is_logged_per_entity_with_its_rule():
    """Mechanical AND logged: the log must record why, not only what."""
    decisions, log = merge.reconcile_document([
        _obs("Concept", "c1"), _obs("Instrument", "c2", True),
        {"name": "other thing", "type": "Standard", "chunk_id": "c1"}])
    assert len(log) == 2
    row = next(r for r in log if r["name"] == "Lexical Diversity")
    assert row["rule"] == "instrument_evidence_wins"
    assert row["observed"] == {"Concept": 1, "Instrument": 1}
    assert sorted(row["chunks"]) == ["c1", "c2"]
    assert merge.poolable(decisions[merge.normalized_key("Lexical Diversity")])


def test_merge_key_is_case_and_whitespace_insensitive():
    assert merge.normalized_key("Lexical  Diversity") == merge.normalized_key("lexical diversity")


# ------------------------------------------------------------------ 5. the pinned profile

def _profiles() -> dict:
    return yaml.safe_load((REPO / "scripts" / "run_profiles.yaml").read_text(encoding="utf-8"))


def test_v037_profile_pins_both_the_prompt_and_the_chunker():
    prof = _profiles()["profiles"]["v0_3_7"]
    for path_key, sha_key in (("prompt_template", "template_sha256"),
                              ("chunker_config", "chunker_config_sha256")):
        got = hashlib.sha256((REPO / prof[path_key]).read_bytes()).hexdigest()
        assert got == prof[sha_key], f"{path_key} drifted from its pin"


def test_comparison_profiles_are_retained_on_disk():
    """ADDENDUM-03 §1.5: the whole-document and chunked profiles stay for the comparison
    record. Deleting the arm you measured against destroys the measurement."""
    profs = _profiles()["profiles"]
    for keep in ("v1", "reextract_v035", "chunked_v035"):
        assert keep in profs, f"comparison profile {keep} was removed"


def test_apply_profile_refuses_a_drifted_pin(tmp_path, monkeypatch):
    """Positive control: a pin that is never checked reads like a guarantee and is not one."""
    import run_bulk_extraction as runner
    prof = {"prompt_template": "kg/extraction/prompt_template_v0_3_7.md",
            "template_sha256": "0" * 64}
    with pytest.raises(SystemExit, match="sha mismatch"):
        runner._verify_pin("v0_3_7", prof, "prompt_template", "template_sha256")


def test_a_declared_pin_without_a_sha_is_refused():
    import run_bulk_extraction as runner
    with pytest.raises(SystemExit, match="without chunker_config_sha256"):
        runner._verify_pin("x", {"chunker_config": "kg/extraction/chunker_config.yaml"},
                           "chunker_config", "chunker_config_sha256")
