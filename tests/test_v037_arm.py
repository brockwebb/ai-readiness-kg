"""v0.3.7 ARM WIRING (chunked_pilot ADDENDUM-03 §3).

ADDENDUM-03 §1 built the contract as modules with unit tests. This file tests that the
production path actually USES them: the arm's shard/raw-dir/emission come from the profile,
`parse_chunk_raw` derives spans from the source before the parser sees them, an unlocatable
anchor is quarantined as `anchor_not_located` rather than as "missing grounding_span", type
conflicts are excluded from the judged stratum, and the pre-registered admitted-yield floor
fires.

Every test below enters through the real entrypoint. That is the whole point: the recurring
M2 failure mode in this project is a guard test that calls a helper directly and therefore
measures the helper rather than the guard. A test here that passes with the wiring deleted is
a broken test.

Zero model spend: nothing here calls model_stub.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg.extraction import anchors, merge  # noqa: E402

CHUNK = ("AIDRIN is a data readiness tool.\n"
         "It scores six dimensions on a 0-1 scale. The tool was released in 2024.\n"
         "Other systems exist too.")


@pytest.fixture
def cp():
    """The pilot script with its arm globals restored after each test — they are module
    state by design (so every function reads them at call time) and a leaked binding would
    silently point a later test at another arm's shard."""
    import chunked_pilot as mod
    from kg.extraction import model_stub
    keep = {k: getattr(mod, k) for k in
            ("PROFILE", "RUN_ID", "JUDGE_RUN_ID", "SHARD_NO", "TAG", "RAW_DIR",
             "CORPUS_EPOCH", "EMISSION", "ARM_MODEL", "DOCS", "DOC_PATHS", "PURPOSE",
             "CHUNK_FILTER")}
    prompt = model_stub._PROMPT_PATH
    yield mod
    for k, v in keep.items():
        setattr(mod, k, v)
    model_stub._PROMPT_PATH = prompt


# ---------------------------------------------------------------- 1. arm selection

def test_apply_arm_binds_every_arm_scoped_global_from_the_profile(cp):
    """A second arm on a second shard must not inherit the first arm's shard, raw dir or
    emission contract: two experiments interleaved on one append-only log cannot be
    separated afterwards."""
    cp.apply_arm("v0_3_7", "claude-haiku-4-5-20251001", "pilot_v037_arm_a_haiku")
    assert (cp.SHARD_NO, cp.TAG) == (17, "v0_3_7")
    assert cp.RAW_DIR == REPO / "events/raw/v0_3_7"
    assert cp.EMISSION == "anchor"
    assert cp.RUN_ID == "pilot_v037_arm_a_haiku"
    assert cp.JUDGE_RUN_ID == "pilot_v037_arm_a_haiku_judge"
    assert cp.model_cfg()["model_id"] == "claude-haiku-4-5-20251001"


def test_banked_arm_still_binds_to_its_own_shard(cp):
    """The v0.3.5 comparator is banked material; the arm switch must leave it exactly where
    it was or the comparison silently changes."""
    cp.apply_arm("chunked_v035", None, None)
    assert (cp.SHARD_NO, cp.TAG, cp.EMISSION) == (16, "chunked_v035", "verbatim")
    assert cp.ARM_MODEL is None


def test_unknown_profile_and_unknown_emission_contract_are_refused(cp, tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        cp.apply_arm("no_such_profile", None, None)
    monkeypatch.setattr(cp, "profile_block",
                        lambda p: {"batch": 99, "raw_dir": "x", "corpus_epoch": "y",
                                   "emission_contract": "telepathy"})
    with pytest.raises(SystemExit) as exc:
        cp.apply_arm("chunked_v035", None, None)
    assert "telepathy" in str(exc.value)


def test_extract_on_a_second_arm_refuses_without_its_own_run_id(cp, monkeypatch):
    """Billing Arm A's calls to the banked arm's run id would charge one experiment's cost
    to another's ceiling and report it under the wrong name."""
    monkeypatch.setattr(sys, "argv",
                        ["chunked_pilot.py", "--phase", "extract", "--profile", "v0_3_7",
                         "--ceiling-tokens", "1000"])
    with pytest.raises(SystemExit) as exc:
        cp.main()
    assert "--run-id is required" in str(exc.value)


# ---------------------------------------------------------------- 2. the contract is WIRED

def _envelope():
    # No `document_id`: the harness owns provenance and injects it (pipeline strips any the
    # model emits), so a test envelope carrying one exercises the warning path, not the arm.
    return {"concepts": [{"id": "c1", "name": "data readiness",
                          "anchor": "data readiness tool"}]}


def test_parse_chunk_raw_derives_the_span_from_the_source_under_the_anchor_arm(cp):
    """Entry through the real parse path, not `apply_anchor_contract` directly."""
    cp.apply_arm("v0_3_7", None, None)
    raw = {"raw_result": json.dumps(_envelope())}
    result, _, _ = cp.parse_chunk_raw("doc-1", raw, CHUNK, CHUNK)
    assert [n["item"]["grounding_span"] for n in result.nodes] == \
        ["AIDRIN is a data readiness tool."]


def test_the_banked_arm_does_not_get_the_anchor_contract(cp):
    """MUTATION-STYLE CONTROL for the test above: under `verbatim` the same envelope has no
    span at all and is quarantined for that. If this passed under both arms, the test above
    would be measuring the parser, not the wiring."""
    cp.apply_arm("chunked_v035", None, None)
    raw = {"raw_result": json.dumps(_envelope())}
    result, _, _ = cp.parse_chunk_raw("doc-1", raw, CHUNK, CHUNK)
    assert result.nodes == []
    assert cp.reason_class(result.quarantined[0]["reason"]) == "missing_span"


def test_unlocatable_anchor_is_quarantined_as_anchor_not_located_not_as_missing_span(cp):
    """The erratum split these causes and ADDENDUM-03 §3 requires them reported apart. An
    item dropped for a bad anchor must NOT be filed under the parser's `missing_span`, which
    is a true statement naming the wrong cause."""
    cp.apply_arm("v0_3_7", None, None)
    # "tool" occurs twice in CHUNK ("readiness tool." and "The tool was"), so it violates
    # the contract's shortest-UNIQUE-substring rule and must be dropped, not disambiguated.
    env = {"concepts": [{"id": "c1", "name": "ghost", "anchor": "a phrase that is absent"},
                        {"id": "c2", "name": "twice", "anchor": "tool"}]}
    result, _, _ = cp.parse_chunk_raw("doc-1", {"raw_result": json.dumps(env)}, CHUNK, CHUNK)
    classes = [cp.reason_class(q["reason"]) for q in result.quarantined]
    assert classes == ["anchor_not_located", "anchor_not_located"]
    assert result.counts()["quarantined"] == 2       # counted, not silently dropped
    assert "ambiguous" in result.quarantined[1]["reason"]


def test_instrument_attribute_anchors_become_per_attribute_spans_on_the_parse_path(cp):
    """The per-attribute rule is the fix for the fabricated `method` values the probe found
    (F 0.25/0.17). Under the anchor contract it only survives if `attribute_anchors` are
    turned into the `grounding_spans` map the parser reads — otherwise every Instrument
    attribute is nulled at parse and the stratum is judged on names alone."""
    cp.apply_arm("v0_3_7", None, None)
    env = {"instruments": [{"id": "i1", "name": "AIDRIN", "anchor": "AIDRIN",
                            "method": "scores six dimensions", "year": "2024",
                            "attribute_anchors": {"method": "six dimensions",
                                                  "year": "released in 2024"}}]}
    result, _, _ = cp.parse_chunk_raw("doc-1", {"raw_result": json.dumps(env)}, CHUNK, CHUNK)
    assert [n["type"] for n in result.nodes] == ["Instrument"]
    item = result.nodes[0]["item"]
    assert item["method"] == "scores six dimensions"   # NOT nulled
    assert item["year"] == "2024"
    assert item["grounding_spans"]["method"] == "It scores six dimensions on a 0-1 scale."
    assert "nulled_at_parse" not in item


def test_an_instrument_attribute_with_no_anchor_is_nulled_not_kept(cp):
    """CONTROL for the test above: the rule must still bite. An attribute the model filled
    from background knowledge carries no anchor, so it gets no span and is nulled — the node
    itself stays admitted (attribute-level, never a node quarantine)."""
    cp.apply_arm("v0_3_7", None, None)
    env = {"instruments": [{"id": "i1", "name": "AIDRIN", "anchor": "AIDRIN",
                            "method": "fielded every 2 years", "attribute_anchors": {}}]}
    result, _, _ = cp.parse_chunk_raw("doc-1", {"raw_result": json.dumps(env)}, CHUNK, CHUNK)
    assert result.nodes[0]["item"]["method"] is None
    assert result.nodes[0]["item"]["nulled_at_parse"] == ["method"]


def test_reason_class_never_sweeps_an_unknown_failure_into_a_bucket(cp):
    assert cp.reason_class("something nobody has seen").startswith("other:")
    assert cp.reason_class("") == "other:unstated"


# ---------------------------------------------------------------- 3. type conflicts

def test_type_conflict_is_excluded_from_the_judged_stratum(cp):
    """merge.py rule 3: pooling an entity whose type is unresolved would put the conflict
    into the denominator of a pre-registered gate."""
    cp.apply_arm("v0_3_7", None, None)
    conflict = merge.reconcile_type([{"type": "Instrument", "chunk_id": "a"},
                                     {"type": "Concept", "chunk_id": "b"}])
    assert conflict["rule"] == merge.TYPE_CONFLICT
    decisions = {"doc-1": {merge.normalized_key("AIDRIN"): conflict}}
    assert cp.resolved_type(decisions, "doc-1", "AIDRIN", "Instrument") is None
    # and an entity the merge RESOLVED to Instrument is pooled as one even where a single
    # chunk typed it Concept — the whole point of reconciling at merge.
    resolved = merge.reconcile_type([
        {"type": "Instrument", "chunk_id": "a", "instrument_evidence": True},
        {"type": "Concept", "chunk_id": "b"}, {"type": "Concept", "chunk_id": "c"}])
    decisions = {"doc-1": {merge.normalized_key("AIDRIN"): resolved}}
    assert cp.resolved_type(decisions, "doc-1", "AIDRIN", "Concept") == "Instrument"


def test_instrument_evidence_reads_the_prompt_s_own_positive_criterion(cp):
    """Evidence is an attribute that SURVIVED the per-attribute span rule. An Instrument
    whose attributes were all nulled at parse carries no evidence, so it cannot outvote."""
    assert cp.instrument_evidence({"name": "AIDRIN", "method": "scores six dimensions"})
    assert not cp.instrument_evidence({"name": "AIDRIN", "method": None, "owner": None,
                                       "year": None, "nulled_at_parse": ["method"]})


# ---------------------------------------------------------------- 4. the yield floor

def test_admitted_yield_floor_fires_below_the_pre_registered_ratio(cp, monkeypatch):
    """Pre-registered 2026-08-29 before Arm A ran: an arm that clears the faithfulness gate
    by extracting almost nothing reports UNDER-EXTRACTION, not PASS."""
    cp.apply_arm("v0_3_7", None, None)
    base = {f"c{i}": {"admitted": 100, "doc_id": "d", "quarantined": 0, "reasons": {},
                      "output_tokens": 0, "nodes": 0, "edges": 0} for i in range(10)}
    low = {f"c{i}": {**base[f"c{i}"], "admitted": 59} for i in range(10)}
    monkeypatch.setattr(cp, "chunk_yield",
                        lambda tag: low if tag == cp.TAG else base)
    y = cp.yield_comparison()
    assert y["shared_chunks"] == 10 and y["ratio"] == 0.59
    assert y["under_extraction"] is True
    ok = {f"c{i}": {**base[f"c{i}"], "admitted": 61} for i in range(10)}
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: ok if tag == cp.TAG else base)
    assert cp.yield_comparison()["under_extraction"] is False


def test_yield_is_compared_only_on_chunks_BOTH_arms_cover(cp, monkeypatch):
    """The v0.3.5 arm banked 44 of 128 chunks. Dividing this arm's items over 128 by the
    baseline's over 44 would compare two different denominators and manufacture a verdict."""
    cp.apply_arm("v0_3_7", None, None)
    row = lambda n: {"admitted": n, "doc_id": "d", "quarantined": 0, "reasons": {},
                     "output_tokens": 0, "nodes": 0, "edges": 0}
    base = {"c1": row(100), "c2": row(100)}
    arm = {"c1": row(100), "c2": row(100), "c3": row(0), "c4": row(0)}
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: arm if tag == cp.TAG else base)
    y = cp.yield_comparison()
    assert y["shared_chunks"] == 2 and y["ratio"] == 1.0 and y["under_extraction"] is False
    assert y["arm_density_all_chunks"] == 50.0     # reported, but not the comparator


def test_only_filters_the_dispatch_list_and_refuses_a_name_that_matches_nothing(cp,
                                                                                monkeypatch):
    """A typo in --only must stop the pass, not quietly extract zero chunks and report
    success — a silent no-op is the failure mode standard 4 forbids."""
    cp.apply_arm("v0_3_7", None, "pilot_v037_arm_a_haiku")
    monkeypatch.setattr(cp.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "m", "truncation_suspect_tokens": 1})
    monkeypatch.setattr(cp, "members", lambda: {d: Path(__file__) for d in cp.PILOT_DOCS})
    args = type("A", (), {"only": "no-such-document", "limit": None, "workers": 1})()
    with pytest.raises(SystemExit) as exc:
        cp.phase_extract(args)
    assert "matches none of the pilot documents" in str(exc.value)


# ------------------------------------------------------------- 5. truncation vs empty

def test_an_empty_but_well_formed_extraction_is_not_truncation(cp):
    """MEASURED on data-readiness#c0029: a references section returned complete valid JSON,
    every typed layer `[]`, 23 entries in `mentions`. Under the exhaustive contract an empty
    extraction was near-impossible, so `has_extraction_layers` was a sound truncation test;
    under SALIENCE it is not, and it stopped the run on a correct answer."""
    bibliography = {"extract_plan": {"chunk_summary": "bibliography"}, "concepts": [],
                    "claims": [], "edges": [], "mentions": [{"name": "a paper"}],
                    "gleaned": []}
    assert cp.envelope_complete(bibliography) is True
    from kg.extraction import model_stub
    assert model_stub.has_extraction_layers(bibliography) is False   # the old test's verdict


def test_an_envelope_with_none_of_the_contract_s_keys_is_still_truncation(cp):
    """CONTROL: the guard must still bite. Loosening it into "anything that parses" would
    accept a fragment as a status, which is what the STOP rule exists to prevent."""
    assert cp.envelope_complete({"some": "other object"}) is False
    assert cp.envelope_complete("a bare string") is False
    assert cp.envelope_complete(None) is False


def test_a_truncated_chunk_stops_the_run_but_only_after_the_paid_for_rest_is_ingested(
        cp, ext_iso, monkeypatch, tmp_path):
    """A SystemExit raised inside a worker is a BaseException, so it bypassed the executor's
    `except Exception` and killed the pass before `phase_ingest` ran — 20 already-paid-for
    raws were left off the shard. STOP is kept; losing the pass is not."""
    cp.apply_arm("v0_3_7", None, "pilot_v037_arm_a_haiku")
    assert issubclass(cp.TruncatedChunk, Exception)      # NOT BaseException-only
    ingested = []
    monkeypatch.setattr(cp, "phase_ingest", lambda a: ingested.append(True) or 0)
    monkeypatch.setattr(cp.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "m", "truncation_suspect_tokens": 1})
    src = tmp_path / "doc.md"
    src.write_text("text", encoding="utf-8")
    monkeypatch.setattr(cp, "members", lambda: {d: src for d in cp.PILOT_DOCS})
    monkeypatch.setattr(cp.rbe, "doc_text", lambda p: "text")
    class FakeSet(list):
        structure_source, heading_level = "test", 1
    monkeypatch.setattr(cp.chunker, "chunk_document",
                        lambda d, t: FakeSet([type("C", (), {"chunk_id": f"{d}#c1",
                                                             "n_tokens": 1})()]))
    monkeypatch.setattr(cp, "raw_path", lambda *a, **k: tmp_path / "absent.json")
    monkeypatch.setattr(cp, "_extract_one",
                        lambda *a, **k: (_ for _ in ()).throw(cp.TruncatedChunk("cut short")))
    args = type("A", (), {"only": cp.PILOT_DOCS[0], "limit": None, "workers": 1})()
    with pytest.raises(SystemExit) as exc:
        cp.phase_extract(args)
    assert "truncated chunk response" in str(exc.value)
    assert ingested == [True], "the pass's other calls must be ingested before the stop"


def test_extract_one_ENTERS_the_truncation_guard(cp, monkeypatch, tmp_path):
    """M2 CONTROL. The tests above call `envelope_complete` directly, which proves the
    predicate and NOT that the extraction path consults it. This one drives `_extract_one`
    with a stubbed model and asserts the guard fires from there."""
    cp.apply_arm("v0_3_7", None, "pilot_v037_arm_a_haiku")
    monkeypatch.setattr(cp, "RAW_DIR", tmp_path)
    monkeypatch.setattr(cp, "build_prompt", lambda *a, **k: "prompt")
    monkeypatch.setattr(cp.model_stub, "invoke", lambda *a, **k: {
        "model_id": "m", "usage": {"outputTokens": 10, "maxOutputTokens": 32000},
        "output": {"nothing": "the contract declares"}, "raw_result": "{}"})
    chunk = type("C", (), {"chunk_id": "d#c0001", "index": 1, "start": 0, "end": 1,
                           "n_tokens": 1, "heading_path": (), "oversize": False})()
    with pytest.raises(cp.TruncatedChunk):
        cp._extract_one("d", chunk, "sha", "title", {"model_id": "m"}, 40000)
    # ... and a legitimately empty bibliography chunk passes through the SAME entrypoint.
    monkeypatch.setattr(cp.model_stub, "invoke", lambda *a, **k: {
        "model_id": "m", "usage": {"outputTokens": 10, "maxOutputTokens": 32000},
        "output": {"concepts": [], "gleaned": []}, "raw_result": "{}"})
    chunk2 = type("C", (), {"chunk_id": "d#c0002", "index": 2, "start": 0, "end": 1,
                            "n_tokens": 1, "heading_path": (), "oversize": False})()
    assert cp._extract_one("d", chunk2, "sha", "title", {"model_id": "m"}, 40000) == "ok"


# ------------------------------------------------------- 6. wrapped prose is not a sentence

#: Verbatim from corpus/bulk_md/data-readiness-for-ai-a-360-degree-survey — Docling hard-wraps
#: prose at ~110 characters, so these newlines sit INSIDE sentences.
WRAPPED = ("Evaluation of data readiness is a crucial step in improving the quality and "
           "appropriateness of data\nusage for AI. R&D efforts have been spent on improving "
           "data quality. However, standardized metrics for evaluating data readiness for\n"
           "use in AI training are still evolving.\n\nIn this study, we perform a "
           "comprehensive survey of metrics used to verify data readiness for\nAI training.")


def test_a_line_wrap_inside_a_sentence_is_not_a_sentence_end():
    """MEASURED on the first Arm A chunks: treating every newline as a boundary cut spans
    like `...ineffective AI models that` — truncated at the wrap, still verbatim-present in
    the source, and therefore still passing every grounding check. Same dangerous shape as
    the table-row bug, one layer down."""
    span, reason = anchors.derive_span("crucial step", WRAPPED)
    assert reason is None
    assert span == ("Evaluation of data readiness is a crucial step in improving the quality "
                    "and appropriateness of data\nusage for AI.")
    assert span.endswith("usage for AI."), "the span must cross the wrap to its real end"


def test_a_blank_line_still_ends_the_unit():
    """CONTROL for the test above: relaxing the newline rule must not run spans together
    across paragraphs. A paragraph break is a real boundary and the only thing separating
    these two sentences — neither carries a structural marker."""
    span, reason = anchors.derive_span("standardized metrics", WRAPPED)
    assert reason is None
    assert span.endswith("are still evolving.")
    assert "In this study" not in span


def test_a_sentence_ending_period_before_a_newline_is_still_a_boundary():
    """The narrower failure the first fix caused: routing every match containing a newline
    to the wrap rule swallowed real sentence ends, because `(?<=[.!?])\\s+` consumes the
    newline too."""
    span, _ = anchors.derive_span("R&D efforts", WRAPPED)
    assert span == "R&D efforts have been spent on improving data quality."


#: Shape taken verbatim from corpus/bulk_md/fcsm-23-02-a-framework-for-data-quality-case-studies,
#: which carries 86 blank-line breaks after a line with NO terminal punctuation (Docling writes
#: them as newline-space-newline). The two documents Arm A ran on contain none at all, so this
#: rule is invisible on those and would ship untested without a fixture from a document that
#: has it.
FCSM = "Table 1 \n \nA Framework for Data Quality: Case Studies \nOctober 2023"


def test_a_blank_line_ends_the_unit_forward_with_no_punctuation_to_help():
    """Nothing here ends in `.!?`, so only the paragraph break can stop the span. Without it,
    a table caption swallows the title beneath it."""
    span, reason = anchors.derive_span("Table 1", FCSM)
    assert reason is None and span == "Table 1"


def test_a_blank_line_ends_the_unit_backward_with_no_punctuation_to_help():
    """The same rule scanning left, same fixture, same absence of punctuation."""
    span, reason = anchors.derive_span("Framework for Data", FCSM)
    assert reason is None
    assert span.startswith("A Framework for Data Quality: Case Studies")
    assert "Table 1" not in span


# ------------------------------------------------- 7. append-only re-ingest generations

def test_readers_keep_only_the_highest_ingest_generation(cp):
    """A parser fix at IDENTICAL chunk boundaries cannot be corrected by `chunk_superseded`:
    that mechanism keys on (chunk_id, start, end), so it would retire the corrected events
    along with the stale ones. Generations correct forward instead — nothing is edited or
    deleted, and every reader sees exactly one view of each chunk."""
    gens = {"d#c1": 2}
    stale = {"chunk_id": "d#c1", "provenance": {"ingest_generation": 1}}
    fresh = {"chunk_id": "d#c1", "provenance": {"ingest_generation": 2}}
    assert cp.is_live(stale, gens, set()) is False
    assert cp.is_live(fresh, gens, set()) is True


def test_events_written_before_generations_existed_are_generation_one(cp):
    """The banked v0.3.5 shard carries no generation field. Treating its events as
    generation 0 — or as unknown — would silently drop the entire comparator."""
    banked = {"chunk_id": "d#c1", "provenance": {}}
    assert cp._generation(banked) == cp.FIRST_GENERATION
    assert cp.is_live(banked, {"d#c1": 1}, set()) is True


def test_a_superseded_chunk_is_still_dead_whatever_its_generation(cp):
    """CONTROL: generations must not resurrect a chunk retired by a boundary change."""
    dead = {("d#c1", 0, 10)}
    ev = {"chunk_id": "d#c1", "chunk_start": 0, "chunk_end": 10,
          "provenance": {"chunk_start": 0, "chunk_end": 10, "ingest_generation": 9}}
    assert cp.is_live(ev, {"d#c1": 9}, dead) is False


# --------------------------------------------------- 8. Arm A2: the restored grounding rule

def test_v0_3_8_restores_the_first_grounding_rule_and_v0_3_7_is_untouched(cp):
    """The rule is restored in a NEW file. Editing the pinned one would invalidate Arm A's
    provenance, and the profile's sha check would refuse to run at all."""
    import hashlib
    v7 = REPO / "kg/extraction/prompt_template_v0_3_7.md"
    v8 = REPO / "kg/extraction/prompt_template_v0_3_8.md"
    assert hashlib.sha256(v7.read_bytes()).hexdigest() == \
        "9a410fc35e684cc5d9f0aefd4652164ef9209044d8e63454e070eb636cb5e840"
    # Assert on what the MODEL SEES, not on the file: the leading <!-- --> block is
    # provenance for humans and is stripped, so a rule merely NAMED in the header (this
    # file's header names the elaboration it deliberately leaves out) cannot be mistaken for
    # a rule the prompt gives. And compare whitespace-COLLAPSED: the templates are
    # hard-wrapped, so a rule sentence is split across lines and a literal substring test
    # would silently pass for the wrong reason.
    import re as _re
    flat = lambda t: " ".join(_re.sub(r"^<!--.*?-->", "", t, flags=_re.S).split())
    t7, t8 = flat(v7.read_text(encoding="utf-8")), flat(v8.read_text(encoding="utf-8"))
    key = "use the document's surface form as the name"
    assert key not in t7 and key in t8
    assert "FIRST GROUNDING RULE" not in t7 and "FIRST GROUNDING RULE" in t8
    # ONE variable: the character-exact elaboration stays absent from BOTH, on purpose.
    elaboration = "do not paraphrase, summarize, reword, fix typos"
    assert elaboration not in t7 and elaboration not in t8
    # and the anchor contract itself is carried over verbatim
    for clause in ("shortest substring of the chunk text that occurs exactly once in it",
                   "character-exact** as it appears in the chunk"):
        assert clause in t7 and clause in t8


def test_v0_3_8_profile_pins_the_new_template(cp):
    import hashlib
    prof = cp.profile_block("v0_3_8")
    sha = hashlib.sha256((REPO / prof["prompt_template"]).read_bytes()).hexdigest()
    assert prof["template_sha256"] == sha
    assert prof["batch"] == 18 and prof["shard_tag"] == "v0_3_8"
    assert prof["emission_contract"] == "anchor"
    assert prof["prompt_template"].endswith("prompt_template_v0_3_8.md")
    # a different shard from Arm A: two arms must never interleave on one append-only log
    assert prof["batch"] != cp.profile_block("v0_3_7")["batch"]
    assert prof["raw_dir"] != cp.profile_block("v0_3_7")["raw_dir"]


def test_instrument_recall_uses_containment_and_honours_the_floor(cp, monkeypatch):
    """Pre-registered floor 0.90. Exact name equality would BEG the question A2 asks — a
    renamed entity is exactly the defect under test — so containment decides the verdict and
    the exact figure is reported beside it."""
    cp.apply_arm("v0_3_8", None, None)
    inst = lambda n, m: {"_type": "Instrument", "name": n, "method": m}
    base = {"c1": {"aidrin": inst("AIDRIN", "scores six dimensions"),
                   "gmsd": inst("GMSD", "gradient magnitudes"),
                   # typed Instrument but the document gave it NO attribute -> not evidence,
                   # so it must not enter the denominator (this is the v0.3.5-side definition)
                   "bare tool": {"_type": "Instrument", "name": "bare tool"},
                   "plain concept": {"_type": "Concept", "name": "plain concept"}}}
    # renamed, not missing: containment finds it, an exact key would not
    arm = {"c1": {"the aidrin tool": {"_type": "Instrument", "name": "the AIDRIN tool"}}}
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: {"c1": {}})
    monkeypatch.setattr(cp, "apply_arm", lambda *a, **k: None)
    calls = iter([arm, base])            # instrument_recall reads the arm, then the baseline
    monkeypatch.setattr(cp, "_proposed_nodes", lambda shared: next(calls))
    r = cp.instrument_recall()
    assert r["baseline_instrument_evidence"] == 2      # the Concept is not counted
    assert r["matched_exact"] == 0 and r["matched_containment"] == 1
    assert r["recall_containment"] == 0.5
    assert r["verdict"] == "genuine_recall_loss"       # 0.5 < 0.90


def test_instrument_recall_verdict_flips_at_the_floor(cp, monkeypatch):
    """CONTROL: the floor must actually bind in both directions."""
    cp.apply_arm("v0_3_8", None, None)
    mk = lambda i: {"_type": "Instrument", "name": f"tool {i}", "method": "m"}
    base = {"c1": {f"tool {i}": mk(i) for i in range(10)}}
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: {"c1": {}})
    monkeypatch.setattr(cp, "apply_arm", lambda *a, **k: None)
    for found, expected in ((9, "naming_defect_confirmed"), (8, "genuine_recall_loss")):
        arm = {"c1": {f"the tool {i} thing": mk(i) for i in range(found)}}
        calls = iter([arm, base])
        monkeypatch.setattr(cp, "_proposed_nodes", lambda shared: next(calls))
        r = cp.instrument_recall()
        assert r["recall_containment"] == found / 10
        assert r["verdict"] == expected, (found, r)


def test_shared_with_refuses_a_tag_with_no_coverage(cp, monkeypatch):
    """An empty restriction set must stop the pass, not silently widen it to every chunk."""
    cp.apply_arm("v0_3_8", None, "pilot_v038_arm_a2_haiku")
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: {})
    args = type("A", (), {"shared_with": "no_such_tag", "only": None, "limit": None,
                          "workers": 1})()
    with pytest.raises(SystemExit) as exc:
        cp.phase_extract(args)
    assert "no chunk_metrics" in str(exc.value)


def test_shared_with_actually_restricts_which_chunks_are_dispatched(cp, ext_iso, monkeypatch,
                                                                    tmp_path):
    """M2 CONTROL for --shared-with. The refusal test above only proves the empty case; this
    one proves the filter narrows a NON-empty pass. Without it A2 would run 48 chunks and be
    measured on 44, which is Arm A's shape, not an identical chunk set."""
    cp.apply_arm("v0_3_8", None, "pilot_v038_arm_a2_haiku")
    src = tmp_path / "doc.md"; src.write_text("text", encoding="utf-8")
    monkeypatch.setattr(cp, "members", lambda: {d: src for d in cp.PILOT_DOCS})
    monkeypatch.setattr(cp.rbe, "doc_text", lambda p: "text")
    monkeypatch.setattr(cp.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "m", "truncation_suspect_tokens": 1})
    monkeypatch.setattr(cp, "raw_path", lambda *a, **k: tmp_path / "absent.json")

    class FakeSet(list):
        structure_source, heading_level = "test", 1
    doc = cp.PILOT_DOCS[0]
    monkeypatch.setattr(cp.chunker, "chunk_document", lambda d, t: FakeSet(
        [type("C", (), {"chunk_id": f"{d}#c000{i}", "n_tokens": 1})() for i in (1, 2, 3)]))
    monkeypatch.setattr(cp, "chunk_yield", lambda tag: {f"{doc}#c0002": {}})
    dispatched = []
    monkeypatch.setattr(cp, "_extract_one",
                        lambda d, c, *a, **k: dispatched.append(c.chunk_id) or "ok")
    monkeypatch.setattr(cp, "phase_ingest", lambda a: 0)
    args = type("A", (), {"shared_with": "chunked_v035", "only": doc, "limit": None,
                          "workers": 1})()
    assert cp.phase_extract(args) == 0
    assert dispatched == [f"{doc}#c0002"], "only the covered chunk may be dispatched"


# ----------------------------------------------------- 9. Arm A3: the character-exact rule

def _rendered(path):
    """What the MODEL sees: the leading <!-- --> provenance block stripped, whitespace
    collapsed. A rule merely NAMED in a header is not a rule the prompt gives."""
    import re as _re
    t = (REPO / path).read_text(encoding="utf-8")
    return " ".join(_re.sub(r"^<!--.*?-->", "", t, flags=_re.S).split())


def test_v0_3_9_restores_character_exact_and_keeps_v0_3_8_intact(cp):
    """Three arms, one instruction each: v0.3.7 -> v0.3.8 adds the FIRST GROUNDING RULE,
    v0.3.8 -> v0.3.9 adds CHARACTER-EXACT. Each earlier template stays pinned so its arm's
    provenance survives."""
    import hashlib
    assert hashlib.sha256((REPO / "kg/extraction/prompt_template_v0_3_8.md")
                          .read_bytes()).hexdigest() == \
        "0c6fee1d8d4a4e42f197744c8c92f2f4d8c8dee6cf75470e63648bb21d0b9410"
    t7 = _rendered("kg/extraction/prompt_template_v0_3_7.md")
    t8 = _rendered("kg/extraction/prompt_template_v0_3_8.md")
    t9 = _rendered("kg/extraction/prompt_template_v0_3_9.md")
    exact = "do not paraphrase, summarize, reword, fix typos, expand abbreviations"
    assert exact not in t7 and exact not in t8 and exact in t9
    naming = "use the document's surface form as the name"
    assert naming not in t7 and naming in t8 and naming in t9   # A3 keeps A2's rule
    # adapted: it binds the ANCHOR, not a grounding_span the model no longer emits
    assert "`anchor` must be CHARACTER-EXACT" in t9
    assert "grounding_span must be CHARACTER-EXACT" not in t9
    assert "Do **not** emit `grounding_span` at all" in t9   # the model still emits none


def test_v0_3_9_adds_exactly_one_rule_over_v0_3_8(cp):
    """The chain's discipline: A3 must differ from A2 by ONE instruction. Compare the
    rendered bold rule headings; anything else changing means the arm is confounded."""
    import re as _re
    heads = lambda p: _re.findall(r"\*\*([A-Z][^*]{8,90})\*\*",
                                  _rendered(f"kg/extraction/prompt_template_{p}.md"))
    h8, h9 = heads("v0_3_8"), heads("v0_3_9")
    added = [h for h in h9 if h not in h8]
    removed = [h for h in h8 if h not in h9]
    assert removed == [], removed
    assert len(added) == 1 and "CHARACTER-EXACT" in added[0], added


def test_v0_3_9_profile_pins_the_new_template_on_its_own_shard(cp):
    import hashlib
    prof = cp.profile_block("v0_3_9")
    assert prof["template_sha256"] == hashlib.sha256(
        (REPO / prof["prompt_template"]).read_bytes()).hexdigest()
    assert prof["batch"] == 19 and prof["shard_tag"] == "v0_3_9"
    assert prof["emission_contract"] == "anchor"
    for other in ("v0_3_7", "v0_3_8"):
        assert prof["batch"] != cp.profile_block(other)["batch"]
        assert prof["raw_dir"] != cp.profile_block(other)["raw_dir"]


def test_verdict_retains_the_ss3_closure(cp):
    """`--phase judge` regenerates the verdict from the two banked arms and would silently
    delete the appended §3 closure — the document of record for the whole v0.3.7/8/9 chain.
    A regeneration that drops it must fail loudly here rather than be noticed later."""
    v = (REPO / "docs/research/2026-08-27_chunked_vs_wholedoc_verdict.md").read_text(
        encoding="utf-8")
    assert "# §3 CLOSURE" in v
    for required in (
            # ADDENDUM-05 §2's required language, verbatim in substance
            "tripwire, not a validity criterion",
            "floor met is not value validated",
            # ADDENDUM-06 §3's carried requirement
            "burn-time acceptance sampling",
            "One-time qualification licenses starting a burn",
            # the closure's operative consequence
            "BLOCKED"):
        assert required in v, f"the §3 closure lost: {required!r}"
