"""Production chunked burn under v0.3.8 (task 2026-08-30_bulk_extraction_v038).

Every test drives the real entry point in `scripts/run_chunked_bulk.py`. The recurring defect
in this project — six recorded instances — is a test that measures a committed artifact or a
helper's neighbour instead of the generator, so the SPRT tests here drive `sprt_decide` and
`sprt_boundaries` rather than reading `state/bulk_v038_sprt.json`, and the draw tests build
their own document store rather than asserting against the committed sample file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import run_chunked_bulk as rcb  # noqa: E402


# ---------------------------------------------------------------- Phase B: the SPRT
def test_the_boundaries_are_a_function_of_the_pre_registered_constants_only():
    """p0/p1/alpha/beta were fixed in the task before Phase A ran, precisely so Phase A data
    could not tune them. A boundary that moved on anything else would defeat that."""
    b = rcb.sprt_boundaries()
    assert (b["p0"], b["p1"], b["alpha"], b["beta"]) == (0.05, 0.10, 0.05, 0.05)
    assert b["reject_intercept"] == pytest.approx(-b["accept_intercept"])
    assert 0 < b["slope"] < 1
    # symmetric alpha=beta puts the accept and reject lines equidistant from the slope line
    assert b["log_A"] > 0 > b["log_B"]


def test_a_clean_batch_accepts_and_a_dirty_one_rejects():
    b = rcb.sprt_boundaries()
    assert rcb.sprt_decide(0, 200, b) == "accept"          # 0/200 is far below p0
    assert rcb.sprt_decide(40, 200, b) == "reject"         # 20% is far above p1
    assert rcb.sprt_decide(0, 10, b) == "continue"         # too little evidence either way


def test_no_batch_can_be_accepted_before_the_minimum_and_that_minimum_is_arithmetic():
    """DD-026 applied to this plan. Below `min_facts_for_accept`, a PERFECT batch still
    cannot cross the accept line, so sampling fewer facts buys a foregone `continue`."""
    b = rcb.sprt_boundaries()
    n = rcb.min_facts_for_accept(b)
    assert rcb.sprt_decide(0, n - 1, b) == "continue"
    assert rcb.sprt_decide(0, n, b) == "accept"


def test_the_expected_sample_number_is_finite_at_the_indifference_point():
    """Wald's ASN ratio is singular where E[log-LR] = 0 — which is exactly the boundary slope,
    the rate at which the plan is LEAST decisive. A guard returning 0.0 there (the first cut
    of this function did) would set the Phase C sample budget to zero at the worst rate."""
    b = rcb.sprt_boundaries()
    peak = rcb.expected_sample_number(b, b["slope"])
    assert peak == pytest.approx(231.3, abs=1.0)
    assert peak > rcb.expected_sample_number(b, b["p0"])
    assert peak > rcb.expected_sample_number(b, b["p1"])


def test_a_degenerate_plan_is_refused_not_silently_divided_by():
    with pytest.raises(ValueError):
        rcb.min_facts_for_accept({"slope": 0.0, "accept_intercept": -1.0})


# ---------------------------------------------------------------- Phase 0.3: the cut
def test_the_cut_rule_is_the_task_s_rule_verbatim():
    """extract iff crosswalk_demand >= 1 OR t0_centrality > 0. Both halves matter: a rule
    that dropped the centrality clause would defer documents nothing else reaches."""
    assert rcb.wants_extraction({"crosswalk_demand": 1, "t0_centrality": 0})
    assert rcb.wants_extraction({"crosswalk_demand": 0, "t0_centrality": 0.4})
    assert rcb.wants_extraction({"crosswalk_demand": 3, "t0_centrality": 2})
    assert not rcb.wants_extraction({"crosswalk_demand": 0, "t0_centrality": 0})
    assert not rcb.wants_extraction({})


def test_a_provisional_priority_file_stops_the_cut(tmp_path, monkeypatch):
    """The cut decides what 159 documents do NOT get extracted. Taking it off a provisional
    ranking would write that decision onto an append-only log from a draft."""
    p = tmp_path / "t2.json"
    p.write_text(json.dumps({"label": "draft", "provisional": True, "t2_priority": []}))
    monkeypatch.setattr(rcb, "PRIORITY_PATH", p)
    with pytest.raises(SystemExit):
        rcb.priority_rows()


def test_the_cut_ignores_priority_rows_the_manifest_never_admitted(monkeypatch):
    """t2_priority is a projection and can lag the manifest. A request for an unadmitted
    document is refused at emit anyway — this keeps it from being counted in the cut."""
    monkeypatch.setattr(rcb, "priority_rows", lambda: [
        {"doc_id": "in", "crosswalk_demand": 2, "t0_centrality": 0},
        {"doc_id": "ghost", "crosswalk_demand": 2, "t0_centrality": 0}])
    monkeypatch.setattr(rcb.queue, "included_documents", lambda: {"in": {}})
    extract, defer = rcb.compute_cut()
    assert [r["doc_id"] for r in extract] == ["in"] and defer == []


# ---------------------------------------------------------------- Phase A: the draw
def _paths(tmp_path, names):
    out = {}
    for n in names:
        f = tmp_path / f"{n}.md"
        f.write_text("\n\n".join(f"## Section {i}\n\nBody text for {n} section {i}."
                                 for i in range(6)), encoding="utf-8")
        out[n] = f
    return out


def _store(monkeypatch, tmp_path, docs: dict[str, str]):
    """docs = {doc_id: doc_type}. Builds a burn set, a manifest projection and real files."""
    paths = _paths(tmp_path, docs)
    monkeypatch.setattr(rcb, "burn_set", lambda: sorted(docs))
    monkeypatch.setattr(rcb, "document_paths", lambda: paths)
    monkeypatch.setattr(rcb.queue, "project",
                        lambda: {d: {"doc_type": t} for d, t in docs.items()})
    return paths


def test_documents_any_arm_has_seen_are_held_out_of_the_confirmation_set(monkeypatch, tmp_path):
    """ADDENDUM-06 §0: 44 chunks from 2 documents is a cluster sample, and a profile measured
    on them is measured on a dev set. A confirmation drawn from the same documents would
    confirm nothing."""
    arm_doc = sorted(rcb.ARM_DOCS)[0]
    _store(monkeypatch, tmp_path, {arm_doc: "academic", "fresh": "academic"})
    assert rcb.confirmation_candidates() == {"academic": ["fresh"]}


def test_unconvertible_sources_are_excluded_rather_than_re_converted(monkeypatch, tmp_path):
    """ADDENDUM-06 §1 says the existing store, no re-conversion. 2 of the 35 burn documents
    are .html with no markdown conversion; converting them inside the run would break the
    pre-registration silently."""
    paths = _store(monkeypatch, tmp_path, {"ok": "academic", "raw": "academic"})
    html = tmp_path / "raw.html"
    html.write_text("<p>x</p>")
    paths["raw"] = html
    assert rcb.confirmation_candidates() == {"academic": ["ok"]}
    assert not rcb.readable(html)
    assert rcb.readable(paths["ok"])


def test_every_live_doc_type_lands_in_a_stratum(monkeypatch, tmp_path):
    """The departure from ADDENDUM-06's three-class collapse exists so that no admitted
    document type is unstratified — an unstratified type gets no Phase C monitoring band,
    which is the one thing ADDENDUM-06 §3 exists to prevent. This test fails the moment a new
    doc_type is admitted without a stratum, which is when someone needs to decide."""
    live = {"academic", "industry", "federal", "standard", "intergovernmental",
            "practitioner", "platform"}
    assert live <= set(rcb.STRATUM_OF), live - set(rcb.STRATUM_OF)


def test_the_allocation_spends_the_whole_sample_and_spreads_it(monkeypatch, tmp_path):
    strata = {"a": ["1"] * 11, "b": ["2"] * 7, "c": ["3"] * 7, "d": ["4"] * 6}
    q = rcb.allocate(strata, total=30)
    assert sum(q.values()) == 30
    assert max(q.values()) - min(q.values()) <= 1        # as-equal-as-possible
    assert q["a"] >= q["d"]                              # remainder to the richest stratum


def test_the_draw_is_reproducible_from_the_recorded_seed(monkeypatch, tmp_path):
    _store(monkeypatch, tmp_path, {f"d{i}": "academic" for i in range(4)})
    first = rcb.draw_confirmation()["chunks"]
    second = rcb.draw_confirmation()["chunks"]
    assert first == second and first


def test_a_document_rich_stratum_draws_distinct_documents(monkeypatch, tmp_path):
    """ADDENDUM-06 §1's clustering guard: where the stratum has >= 10 documents, two chunks
    from one document would be a cluster sample inside the stratum."""
    _store(monkeypatch, tmp_path, {f"d{i}": "academic" for i in range(12)})
    chunks = rcb.draw_confirmation()["chunks"]
    docs = [c["doc_id"] for c in chunks]
    assert len(docs) == len(set(docs))


def test_a_thin_stratum_may_repeat_documents_rather_than_come_up_short(monkeypatch, tmp_path):
    """Below the threshold the clustering guard is not applied — refusing to repeat would
    silently shrink the sample instead of reporting the constraint."""
    _store(monkeypatch, tmp_path, {"only": "academic"})
    payload = rcb.draw_confirmation()
    docs = [c["doc_id"] for c in payload["chunks"]]
    assert docs and len(docs) > len(set(docs))
    assert payload["strata"]["academic"]["distinct_documents_required"] is False


def test_the_draw_reports_a_short_stratum_instead_of_topping_it_up_elsewhere(monkeypatch,
                                                                            tmp_path):
    """A stratum with fewer chunks than its quota must show `drawn < quota`, not have the
    shortfall silently reallocated — the shortfall is the finding."""
    paths = _store(monkeypatch, tmp_path, {f"d{i}": "academic" for i in range(12)})
    for p in paths.values():
        p.write_text("one short paragraph only.", encoding="utf-8")
    payload = rcb.draw_confirmation()
    r = payload["strata"]["academic"]
    assert r["drawn"] <= r["quota"]
    assert payload["drawn_total"] == len(payload["chunks"])


def test_a_production_profile_declaring_a_shard_tag_is_refused(monkeypatch):
    """The whole reason `bulk_v038` exists rather than reusing the `v0_3_8` arm: replay()
    skips tagged shards, so a burn under a tagged profile costs real money and changes
    nothing in the graph."""
    monkeypatch.setattr(rcb.cp, "apply_arm", lambda *a, **k: {"shard_tag": "v0_3_8"})
    with pytest.raises(SystemExit) as exc:
        rcb.apply_production_profile()
    assert "shard_tag" in str(exc.value)


def test_the_production_profile_carries_the_arm_s_extraction_contract_byte_for_byte():
    """'Pin v0_3_8' binds the extraction contract. If these ever diverge, Phase A qualified
    something the burn does not run."""
    import yaml
    d = yaml.safe_load((REPO / "scripts/run_profiles.yaml").read_text())
    arm, prod = d["profiles"]["v0_3_8"], d["profiles"][rcb.PROFILE]
    for key in ("prompt_template", "template_sha256", "chunker_config",
                "chunker_config_sha256", "emission_contract"):
        assert prod[key] == arm[key], key
    assert not prod.get("shard_tag")
    assert prod["batch"] != arm["batch"]
    assert d["default"] == rcb.PROFILE


def test_applying_the_production_profile_leaves_the_shard_untagged(monkeypatch):
    """M2 control for the profile test above: the YAML can be right while `apply_arm` still
    routes the events to a tagged shard. `TAG` defaulted to the profile name before this was
    fixed, which would have tagged `bulk_v038` and hidden the whole burn from replay()."""
    monkeypatch.setattr(rcb, "document_paths", lambda: {})
    rcb.apply_production_profile()
    try:
        assert rcb.cp.TAG is None
        assert rcb.cp.PURPOSE == rcb.PROFILE
        assert rcb.cp.CORPUS_EPOCH == "bulk-v038"
        # and the events would land where replay() actually looks
        from kg import eventlog
        assert "_" not in eventlog._shard_path(rcb.cp.SHARD_NO, rcb.cp.TAG).stem
    finally:
        rcb.cp.apply_arm("chunked_v035", None, "pilot_chunked_v035")
        rcb.cp.PURPOSE = "chunked_pilot"
        rcb.cp.DOC_PATHS = None


def test_the_whole_document_runner_refuses_a_chunk_unit_profile():
    """`default:` now names a chunk-unit profile, so an unflagged fire of the whole-document
    runner would inherit it: a chunk-local anchor contract sent a whole document, which fails
    as a silent yield collapse rather than an error. The chunked driver, which needs only the
    profile's paths, opts in explicitly."""
    import run_bulk_extraction as rbe_mod
    from kg.extraction import model_stub
    # apply_profile rebinds module globals AND model_stub._PROMPT_PATH; restore both, or this
    # test leaks the chunked prompt into every later test that reads the pinned template.
    saved = (rbe_mod.PROFILE_NAME, model_stub._PROMPT_PATH)
    try:
        with pytest.raises(SystemExit) as exc:
            rbe_mod.apply_profile(rcb.PROFILE)
        assert "chunk-unit" in str(exc.value)
        with pytest.raises(SystemExit):
            rbe_mod.apply_profile(None)                   # inherits default: bulk_v038
        assert rbe_mod.apply_profile(rcb.PROFILE, chunk_unit_ok=True) == rcb.PROFILE
    finally:
        rbe_mod.apply_profile(saved[0] or "v1")
        model_stub._PROMPT_PATH = saved[1]


def test_the_stamped_prompt_version_comes_from_the_prompt_that_was_sent(monkeypatch):
    """The defect this caught in flight. `build_prompt` reads the template from the PROFILE;
    `prompt_version` reads it from `model_stub._PROMPT_PATH`. Those are two reads of one fact,
    and when they disagreed a production pass ran the v0.3.8 prompt while stamping
    `prompt_version: 0.3.5` on the raw and on every provenance record. Nothing downstream can
    detect that afterwards — the output is plausible and the provenance simply lies."""
    from kg.extraction import model_stub
    monkeypatch.setattr(rcb, "document_paths", lambda: {})
    rcb.apply_production_profile()
    assert rcb.cp.profile_template().name == "prompt_template_v0_3_8.md"
    assert rcb.cp.verify_prompt_binding() == "0.3.8"

    # and it REFUSES rather than proceeding when the two disagree
    monkeypatch.setattr(model_stub, "_PROMPT_PATH",
                        REPO / "kg/extraction/prompt_template.md")
    with pytest.raises(SystemExit) as exc:
        rcb.cp.verify_prompt_binding()
    assert "Provenance would record the wrong prompt" in str(exc.value)
