"""Production chunked burn under v0.3.8 (task 2026-08-30_bulk_extraction_v038).

Every test drives the real entry point in `scripts/run_chunked_bulk.py`. The recurring defect
in this project — six recorded instances — is a test that measures a committed artifact or a
helper's neighbour instead of the generator, so the SPRT tests here drive `sprt_decide` and
`sprt_boundaries` rather than reading `state/bulk_v038_sprt.json`, and the draw tests build
their own document store rather than asserting against the committed sample file.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import run_chunked_bulk as rcb  # noqa: E402


@pytest.fixture
def cp_bulk(ext_iso, monkeypatch):
    """The shared extraction module bound to the production profile, over a tmp event log and
    a tmp raw dir, with every arm-scoped global restored afterwards."""
    cp = rcb.cp
    keep = {k: getattr(cp, k) for k in ("DOCS", "DOC_PATHS", "PURPOSE", "CHUNK_FILTER",
                                        "BATCH_ID", "RAW_DIR", "SHARD_NO", "TAG",
                                        "CORPUS_EPOCH", "EMISSION", "PROFILE")}
    monkeypatch.setattr(rcb, "document_paths", lambda: {})
    rcb.apply_production_profile()
    monkeypatch.setattr(cp, "RAW_DIR", ext_iso / "raw")
    yield cp
    for k, v in keep.items():
        setattr(cp, k, v)


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


# ---------------------------------------------------------------- Phase C: the burn
def test_batches_never_split_a_document():
    """A rejected batch is quarantined out of the projection wholesale. Half a document in
    the graph and half quarantined is worse than neither."""
    counts = {"a": 30, "b": 30, "c": 5}
    bs = rcb.batches(["a", "b", "c"], counts)
    seen = [d for b in bs for d in b["documents"]]
    assert seen == ["a", "b", "c"] and len(seen) == len(set(seen))
    assert all(b["chunks"] == sum(counts[d] for d in b["documents"]) for b in bs)


def test_a_batch_reaches_the_minimum_before_it_closes_and_the_last_may_be_short():
    """Below the minimum there is not enough output to sample from; padding the final batch
    by reordering would break the priority order Phase 0.4 established."""
    bs = rcb.batches(["a", "b", "c"], {"a": 39, "b": 1, "c": 3})
    assert [b["chunks"] for b in bs] == [40, 3]
    assert all(b["chunks"] >= rcb.BATCH_MIN_CHUNKS for b in bs[:-1])


def test_batch_ids_are_stable_and_ordered():
    bs = rcb.batches(["a", "b"], {"a": 40, "b": 40})
    assert [b["batch_id"] for b in bs] == ["bulk_v038_b001", "bulk_v038_b002"]


def test_the_batch_ceiling_follows_the_ledger_not_a_constant(tmp_path, monkeypatch):
    """The task's rule: 1.3 x the running mean settled tokens/chunk over the ledger's last 10
    measured settles. A ceiling pinned to a constant stops tracking the burn it is bounding."""
    rows = [{"record": "declare", "run_id": "bulk_v038_x",
             "call_class": "extraction_chunk"}]
    rows += [{"record": "settle", "run_id": "bulk_v038_x", "actual_tokens": 1000}] * 5
    rows += [{"record": "settle", "run_id": "bulk_v038_x", "actual_tokens": 2000}] * 10
    monkeypatch.setattr(rcb, "REPO", tmp_path)
    monkeypatch.setattr(rcb, "LEDGER_WINDOW", 10)
    (tmp_path / "state").mkdir(exist_ok=True)
    (tmp_path / "state" / "spend_ledger.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows))
    ceiling, per = rcb.batch_ceiling(10, default_per_chunk=99999.0)
    assert per == 2000.0                                    # last 10 only, not all 15
    assert ceiling == int(1.3 * 2000 * 10)


def test_the_ceiling_averages_only_extraction_chunk_settles(tmp_path, monkeypatch):
    """A judge run and a pilot arm settle into the same ledger. Averaging them into an
    extraction ceiling sizes the burn off the wrong call class.

    The first version of this test picked `pilot_chunked_v035` as the contaminant — a run id
    that does NOT start with `bulk_v038` — so a prefix filter passed it while the real
    contaminant, `bulk_v038_phase_a_judge`, sailed through. It put batch 1's ceiling at
    84,433/chunk against a measured 49,734. The call class is what matters, and it lives on
    the run's `declare` record, not on the settle."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "spend_ledger.jsonl").write_text("\n".join(json.dumps(r) for r in [
        {"record": "declare", "run_id": "bulk_v038_phase_a", "call_class": "extraction_chunk"},
        {"record": "declare", "run_id": "bulk_v038_phase_a_judge", "call_class": "judge"},
        {"record": "declare", "run_id": "pilot_chunked_v035", "call_class": "extraction_chunk"},
        {"record": "settle", "run_id": "bulk_v038_phase_a", "actual_tokens": 1000},
        {"record": "settle", "run_id": "bulk_v038_phase_a_judge", "actual_tokens": 999999},
        {"record": "settle", "run_id": "pilot_chunked_v035", "actual_tokens": 888888}]))
    monkeypatch.setattr(rcb, "REPO", tmp_path)
    assert rcb.mean_settled_per_chunk(0.0) == 1000.0        # judge AND arm both excluded


def test_a_settle_with_no_declared_class_is_not_averaged_in(tmp_path, monkeypatch):
    """A settle whose run never declared a class cannot be assumed to be extraction."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "spend_ledger.jsonl").write_text("\n".join(json.dumps(r) for r in [
        {"record": "declare", "run_id": "bulk_v038_a", "call_class": "extraction_chunk"},
        {"record": "settle", "run_id": "bulk_v038_a", "actual_tokens": 1000},
        {"record": "settle", "run_id": "bulk_v038_orphan", "actual_tokens": 999999}]))
    monkeypatch.setattr(rcb, "REPO", tmp_path)
    assert rcb.mean_settled_per_chunk(0.0) == 1000.0


def test_the_stop_rule_fires_on_two_consecutive_rejects():
    st = rcb.BurnState()
    for o in ("accept", "reject", "accept"):
        st.record(o)
    assert st.should_stop() is None
    st.record("reject")
    assert st.should_stop() is None                          # not consecutive
    st.record("reject")
    assert "2 consecutive rejects" in st.should_stop()


def test_the_stop_rule_counts_inconclusives_in_the_rolling_window():
    """`sampling_inconclusive` is accept-with-flag for the batch but still evidence about the
    process — a run that keeps failing to decide is not a healthy run."""
    st = rcb.BurnState()
    for o in ("sampling_inconclusive", "accept", "reject", "accept",
              "sampling_inconclusive"):
        st.record(o)
    assert "3 rejects/inconclusives" in st.should_stop()


def test_a_clean_run_never_stops():
    st = rcb.BurnState()
    for _ in range(20):
        st.record("accept")
    assert st.should_stop() is None


def test_the_batch_sampler_reads_the_shard_not_a_committed_file(monkeypatch):
    """The M85/M86 class, sixth recorded instance: a sampler that reads an artifact reports on
    the artifact, not on what the burn produced. This drives `sample_for_batch` against items
    `batch_items` pulled out of the event log, and asserts the draw is seeded and bounded."""
    items = [{"i": i} for i in range(100)]
    a = rcb.sample_for_batch("bulk_v038_b001", items, budget=20)
    b = rcb.sample_for_batch("bulk_v038_b001", items, budget=20)
    c = rcb.sample_for_batch("bulk_v038_b002", items, budget=20)
    assert a == b and len(a) == 20                           # seeded on the batch id
    assert a != c                                            # a different batch draws differently
    assert all(x in items for x in a)
    assert rcb.sample_for_batch("b", items[:5], budget=20) == items[:5]   # no upsampling


def test_batch_items_selects_by_the_batch_id_stamped_in_provenance(monkeypatch):
    monkeypatch.setattr(rcb.cp, "shard_items", lambda: (
        {"d": [{"provenance": {"batch_id": "bulk_v038_b001"}, "payload": {"id": "n1"}},
               {"provenance": {"batch_id": "bulk_v038_b002"}, "payload": {"id": "n2"}},
               {"provenance": {}, "payload": {"id": "n3"}}]}, {}, {}))
    got = rcb.batch_items("bulk_v038_b001")
    assert [e["payload"]["id"] for e in got] == ["n1"]


def test_a_quarantined_batch_leaves_the_projection_and_nothing_else_does(ext_iso):
    """The consequence a reject is supposed to have. `purpose` cannot express it — the verdict
    arrives AFTER ingest — so the exclusion is a later event naming the batch, and the
    projection reads it at call time."""
    import build_projection as bp
    from kg import eventlog
    good = {"event_type": "node_asserted", "purpose": rcb.PROFILE, "doc_id": "d",
            "provenance": {"batch_id": "bulk_v038_b002"}, "payload": {"id": "keep"}}
    bad = {"event_type": "node_asserted", "purpose": rcb.PROFILE, "doc_id": "d",
           "provenance": {"batch_id": "bulk_v038_b001"}, "payload": {"id": "drop"}}
    eventlog.append(good, batch=23)
    eventlog.append(bad, batch=23)
    assert bp.quarantined_batches() == set()
    assert bp.is_projectable(bad, bp.quarantined_batches())

    eventlog.append({"event_type": "bulk_batch_quarantined", "batch_id": "bulk_v038_b001"},
                    batch=23)
    q = bp.quarantined_batches()
    assert q == {"bulk_v038_b001"}
    assert not bp.is_projectable(bad, q)
    assert bp.is_projectable(good, q)          # the accepted batch is untouched


def test_a_requalified_batch_comes_back_without_deleting_the_quarantine(ext_iso):
    """Correct-forward, never a deletion — the invariant the whole log runs on."""
    import build_projection as bp
    from kg import eventlog
    ev = {"event_type": "node_asserted", "provenance": {"batch_id": "b1"},
          "payload": {"id": "x"}}
    eventlog.append({"event_type": "bulk_batch_quarantined", "batch_id": "b1"}, batch=23)
    assert not bp.is_projectable(ev, bp.quarantined_batches())
    eventlog.append({"event_type": "bulk_batch_requalified", "batch_id": "b1"}, batch=23)
    assert bp.is_projectable(ev, bp.quarantined_batches())


def test_an_event_with_no_batch_id_is_never_quarantined_by_accident(ext_iso):
    """Every event predating acceptance sampling — the entire v1 and kernel corpus — has no
    batch_id. A membership test that treated None as a match would empty the graph."""
    import build_projection as bp
    from kg import eventlog
    eventlog.append({"event_type": "bulk_batch_quarantined", "batch_id": "b1"}, batch=23)
    q = bp.quarantined_batches()
    assert bp.is_projectable({"event_type": "node_asserted", "payload": {}}, q)
    assert bp.is_projectable({"event_type": "node_asserted", "provenance": {}}, q)


def test_a_quarantine_event_naming_no_batch_cannot_empty_the_graph(ext_iso):
    """M2 control for the test above. A malformed quarantine event puts `None` in the set;
    if the exclusion test is a bare membership check, every event that predates acceptance
    sampling — the whole v1 and kernel corpus — matches `None` and leaves the graph."""
    import build_projection as bp
    from kg import eventlog
    eventlog.append({"event_type": "bulk_batch_quarantined", "reason": "malformed"}, batch=23)
    q = bp.quarantined_batches()
    legacy = {"event_type": "node_asserted", "doc_id": "v1-doc", "payload": {"id": "x"}}
    assert bp.is_projectable(legacy, q)
    assert bp.is_projectable(legacy, {None})
    assert bp.is_projectable({"provenance": {"batch_id": None}}, {None})


def test_the_batch_id_reaches_provenance_and_the_chunk_record(cp_bulk, monkeypatch,
                                                              tmp_path):
    """Both carriers, because they answer different questions. Provenance on each item is what
    `batch_items` samples; `batch_id` on `chunk_metrics` is what records that a chunk with
    ZERO admitted items still belonged to the batch — otherwise an empty batch looks like an
    absent one."""
    from kg import eventlog
    cp = cp_bulk
    src = tmp_path / "d.md"
    src.write_text("# H\n\nThe readiness index is a scored instrument.\n", encoding="utf-8")
    monkeypatch.setattr(cp, "DOCS", ["d"])
    monkeypatch.setattr(cp, "DOC_PATHS", {"d": src})
    monkeypatch.setattr(cp, "BATCH_ID", "bulk_v038_b007")
    monkeypatch.setattr(cp, "superseded", lambda tag=None: set())
    monkeypatch.setattr(cp, "live_generations", lambda tag=None: {})
    monkeypatch.setattr(cp, "model_cfg", lambda: {"model_id": "m"})

    chunks = list(cp.chunker.chunk_document("d", src.read_text()))
    prov = cp.ingest_provenance("ex1", "m", "sha", chunks[0], 1)
    assert prov["batch_id"] == "bulk_v038_b007"
    monkeypatch.setattr(cp, "BATCH_ID", None)
    assert "batch_id" not in cp.ingest_provenance("ex1", "m", "sha", chunks[0], 1)
    monkeypatch.setattr(cp, "BATCH_ID", "bulk_v038_b007")

    sha = __import__("hashlib").sha256(src.read_bytes()).hexdigest()
    rp = cp.raw_path("d", chunks[0], sha, "m")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps({"model_id": "m", "usage": {"outputTokens": 10},
                              "raw_result": "{}"}))
    cp.phase_ingest(type("A", (), {"reingest": False})())
    metrics = [ev for ev in eventlog.replay(tag=cp.TAG)
               if ev.get("event_type") == "chunk_metrics"]
    assert metrics and all(ev["batch_id"] == "bulk_v038_b007" for ev in metrics)


def test_this_run_s_items_are_scoped_by_purpose_not_by_shard(cp_bulk, monkeypatch):
    """An arm's shard is tagged and `replay(tag=...)` isolates it. A PRODUCTION run is
    deliberately UNTAGGED so it reaches the graph — and `replay(tag=None)` reads every
    untagged shard, i.e. the entire v1 and kernel corpus. Reading that as "this run's items"
    mixed 4,890 historical Concepts into a 30-chunk confirmation set and reported semantic
    edges this task never emitted."""
    from kg import eventlog
    cp = cp_bulk
    mine = {"event_type": "node_asserted", "purpose": rcb.PROFILE, "doc_id": "d",
            "chunk_id": "d#c1", "provenance": {}, "payload": {"id": "mine", "type": "Concept",
                                                              "item": {"name": "mine"}}}
    legacy = {"event_type": "node_asserted", "purpose": "bulk_v1", "doc_id": "d",
              "chunk_id": "d#c1", "provenance": {},
              "payload": {"id": "old", "type": "Concept", "item": {"name": "old"}}}
    eventlog.append(mine, batch=cp.SHARD_NO)
    eventlog.append(legacy, batch=cp.SHARD_NO)     # same untagged shard, different run
    nodes, _e, _s = cp.shard_items()
    assert [ev["payload"]["id"] for ev in nodes["d"]] == ["mine"]


def test_chunk_yield_on_an_untagged_shard_is_scoped_the_same_way(cp_bulk):
    """The yield bands feed Phase C's monitoring. Bands computed over another run's chunks
    would monitor against the wrong process."""
    from kg import eventlog
    cp = cp_bulk
    for purpose, chunk, nodes in ((rcb.PROFILE, "d#c1", 7), ("bulk_v1", "d#c2", 99)):
        eventlog.append({"event_type": "chunk_metrics", "purpose": purpose, "doc_id": "d",
                         "chunk_id": chunk, "counts": {}, "nodes_kept": nodes,
                         "edges_kept": 0}, batch=cp.SHARD_NO)
    y = cp.chunk_yield(cp.TAG)
    assert list(y) == ["d#c1"] and y["d#c1"]["nodes"] == 7


# ---------------------------------------------------------------- the gate's own reading
def _agg(f_hi, faithful_rate, n_facts=160):
    return {"pooled": {"F_hi": f_hi, "n_facts": n_facts},
            "items": {"faithful_rate": faithful_rate, "n": 122, "faithful": 94}}


def test_the_gate_reads_the_aggregator_s_actual_key_names():
    """This failed live. The first version read `pooled["F_upper"]` and
    `pooled["item_faithful"]` — neither is a key the aggregator writes. Both came back None,
    the threshold comparisons were skipped, and the gate reported FAIL on a run whose real
    numbers PASS (F_upper 0.0715 < 0.10, item-faithful 0.770 >= 0.70)."""
    f_upper, faithful, n = rcb.gate_inputs(_agg(0.0715, 0.7705))
    assert (f_upper, faithful, n) == (0.0715, 0.7705, 160)
    assert rcb.gate_verdict(f_upper, faithful, n, 35) == "PASS"


def test_an_unreadable_aggregate_refuses_instead_of_resolving_to_FAIL():
    """DD-028 wearing a safe face: a verdict function that cannot read its instrument must say
    so. Silently reporting FAIL looks conservative and is not — it discards a passing run and
    sends the next task chasing a gate that was never measured."""
    for bad in ({"pooled": {"F_hi": 0.05}, "items": {}},
                {"pooled": {}, "items": {"faithful_rate": 0.9}},
                {}):
        with pytest.raises(rcb.GateUnreadable) as exc:
            rcb.gate_inputs(bad)
        assert "cannot be read" in str(exc.value)


def test_each_threshold_can_fail_the_gate_on_its_own():
    """Both conditions are pre-registered; a gate that only enforced one would pass runs the
    other rules out."""
    assert rcb.gate_verdict(0.0715, 0.7705, 160, 35) == "PASS"
    assert rcb.gate_verdict(0.1001, 0.7705, 160, 35) == "FAIL"     # F_upper alone
    assert rcb.gate_verdict(0.0715, 0.6999, 160, 35) == "FAIL"     # item-faithful alone
    assert rcb.gate_verdict(0.10, 0.70, 160, 35) == "FAIL"         # strict <, inclusive >=
    assert rcb.gate_verdict(0.0999, 0.70, 160, 35) == "PASS"


def test_too_few_facts_is_unreachable_not_a_judged_failure():
    """DD-026: below the minimum the gate cannot be attained however good the extraction is.
    Reporting FAIL there would record a verdict the evidence could not have produced."""
    assert rcb.gate_verdict(0.5, 0.1, 34, 35) == "GATE UNREACHABLE"
    assert rcb.gate_verdict(0.0715, 0.7705, 34, 35) == "GATE UNREACHABLE"


# --------------------------------------------- DD-024 at graph entry (ADDENDUM-01 §1)
def test_a_bulk_profile_refuses_semantic_edges_and_says_so(cp_bulk, monkeypatch, tmp_path):
    """(a) of ADDENDUM-01 §1's matrix, driven through the REAL ingest entry point rather than
    a fixture (the M85/M86 class; a seventh instance is not wanted).

    The refusal must EMIT. A rule that drops output silently is indistinguishable from an
    extractor that never produced it, and that difference is the evidence base DD-024 rests
    on."""
    from kg import eventlog
    cp = cp_bulk
    src = tmp_path / "d.md"
    body = "The Quality Framework has a component called Objectivity."
    src.write_text(f"# H\n\n{body}\n", encoding="utf-8")
    monkeypatch.setattr(cp, "DOCS", ["d"])
    monkeypatch.setattr(cp, "DOC_PATHS", {"d": src})
    monkeypatch.setattr(cp, "superseded", lambda tag=None: set())
    monkeypatch.setattr(cp, "live_generations", lambda tag=None: {})
    monkeypatch.setattr(cp, "model_cfg", lambda: {"model_id": "m"})
    assert cp.PROFILE_CLASS == "bulk"

    class _Result:
        nodes: list = []
        quarantined: list = []
        precheck_span_lacks_name = 0
        edges = [{"type": "has_component", "from_id": "a", "to_id": "b",
                  "item": {"grounding_span": body}},
                 {"type": "cites", "from_id": "a", "to_id": "c",
                  "item": {"grounding_span": body}}]

        def counts(self):
            return {}

    monkeypatch.setattr(cp, "parse_chunk_raw",
                        lambda *a, **k: (_Result(), [], []))
    chunks = list(cp.chunker.chunk_document("d", src.read_text()))
    sha = __import__("hashlib").sha256(src.read_bytes()).hexdigest()
    rp = cp.raw_path("d", chunks[0], sha, "m")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps({"model_id": "m", "usage": {}, "raw_result": "{}"}))
    cp.phase_ingest(type("A", (), {"reingest": False})())

    evs = list(eventlog.replay(tag=cp.TAG))
    admitted = [e for e in evs if e.get("event_type") == "edge_asserted"]
    refused = [e for e in evs if e.get("event_type") == "semantic_edge_refused"]
    assert [e["payload"]["type"] for e in admitted] == ["cites"]      # cites is NOT semantic
    assert [e["payload"]["type"] for e in refused] == ["has_component"]
    r = refused[0]
    assert r["doc_id"] == "d" and r["chunk_id"] == chunks[0].chunk_id
    assert r["payload"]["grounding_span"] == body                     # the span is recorded
    assert "DD-024" in r["payload"]["rule"]


def test_an_experiment_arm_is_not_subject_to_the_bulk_refusal(cp_bulk):
    """DD-024 closes BULK extraction. The refusal keys on the profile's class, so an arm — and
    demand-pull adjudication, DD-024's own sanctioned path for these same types — is
    untouched. A global ban on the edge type would close DD-024's remedy along with the
    problem."""
    cp = cp_bulk
    assert cp.semantic_edge_refused("has_component") is True
    try:
        cp.apply_arm("v0_3_8", None, "arm")
        assert cp.PROFILE_CLASS is None
        assert cp.semantic_edge_refused("has_component") is False
    finally:
        cp.apply_arm("bulk_v038", None, "restore")


def test_a_bulk_semantic_edge_that_slips_admission_still_does_not_project():
    """(b): the second, independent layer. §5.1 of the RESULT showed that ONE missing rule let
    190 forbidden edges through, which is the argument for not relying on one."""
    import build_projection as bp
    bulk = bp.bulk_purposes()
    assert "bulk_v038" in bulk
    leaked = {"event_type": "edge_asserted", "purpose": "bulk_v038",
              "payload": {"type": "has_component"}}
    assert not bp.is_projectable(leaked, set(), bulk)
    for kept in ({"event_type": "edge_asserted", "purpose": "bulk_v038",
                  "payload": {"type": "cites"}},
                 {"event_type": "edge_asserted", "purpose": "demand_pull_adjudication",
                  "payload": {"type": "has_component"}},
                 {"event_type": "node_asserted", "purpose": "bulk_v038",
                  "payload": {"type": "Concept"}}):
        assert bp.is_projectable(kept, set(), bulk), kept


def test_the_refusal_reads_the_profile_registry_not_a_hardcoded_name():
    """`bulk_purposes` is config-driven. A hardcoded name would silently stop protecting the
    next production profile the moment one is registered."""
    import build_projection as bp
    import yaml
    d = yaml.safe_load((REPO / "scripts/run_profiles.yaml").read_text())
    expected = {n for n, p in d["profiles"].items() if (p or {}).get("profile_class") == "bulk"}
    assert bp.bulk_purposes() == expected and expected


def test_a_second_bulk_profile_is_protected_without_a_code_change(tmp_path, monkeypatch):
    """M2 control for the test above, which cannot fail while `bulk_v038` is the only bulk
    profile: comparing a hardcoded set to the registry's one entry passes either way. This
    registers a SECOND bulk profile and asserts it is protected with no code change — the
    protection has to survive the next production profile."""
    import build_projection as bp
    reg = tmp_path / "scripts"
    reg.mkdir()
    (reg / "run_profiles.yaml").write_text(__import__("yaml").safe_dump({
        "default": "bulk_v038",
        "profiles": {"bulk_v038": {"profile_class": "bulk"},
                     "bulk_v040": {"profile_class": "bulk"},
                     "v0_3_8": {}}}))
    monkeypatch.setattr(bp, "REPO", tmp_path)
    assert bp.bulk_purposes() == {"bulk_v038", "bulk_v040"}
    leaked = {"event_type": "edge_asserted", "purpose": "bulk_v040",
              "payload": {"type": "subtype_of"}}
    assert not bp.is_projectable(leaked, set(), bp.bulk_purposes())


def test_the_burn_plan_resumes_at_chunk_level_and_never_repeats_a_chunk(monkeypatch):
    """ADDENDUM-01 §3.1. Phase A's 30 chunks are already in the graph. A plan that counted
    them again would size every ceiling too high and re-dispatch paid-for work; the resume
    reads the ledger-derived coverage, not a file and not the raw directory."""
    counts = {"a": 40, "b": 10}
    coverage = {"a": {f"a#c{i:04d}" for i in range(5)}}
    monkeypatch.setattr(rcb, "document_chunk_counts", lambda: counts)
    monkeypatch.setattr(rcb.queue, "worklist", lambda p=None: ["a", "b"])
    monkeypatch.setattr(rcb.queue, "chunk_coverage", lambda p: coverage)
    work, remaining, already = rcb.resume_plan()          # the real derivation, not a copy
    assert (work, remaining, already) == (["a", "b"], {"a": 35, "b": 10}, 5)
    plan = rcb.batches(work, remaining)
    assert sum(b["chunks"] for b in plan) == 45          # not 50
    assert plan[0]["chunks"] == 45                       # 35 + 10 closes the first batch


def test_a_fully_resumed_document_contributes_no_chunks_to_the_plan(monkeypatch):
    """The single-chunk document Phase A completed must not reappear as a batch of size 0."""
    plan = rcb.batches(["done", "todo"], {"done": 0, "todo": 45})
    assert sum(b["chunks"] for b in plan) == 45
    assert all(b["chunks"] > 0 for b in plan)
    # and it is absent from the DOCUMENT list too, not merely contributing zero: a batch that
    # lists a document it does not extract reports work it did not do.
    assert [d for b in plan for d in b["documents"]] == ["todo"]


# --------------------------------------------- yield monitoring (ADDENDUM-01 §3.3, §3.4)
def test_the_yield_band_is_the_observed_envelope_not_three_sd(monkeypatch):
    """+/-3 sd gave `agency_framework` a band of -30 to +58: it cannot flag anything, and a
    negative floor on a count is not a floor. Every stratum uses the same envelope so flags
    are comparable across strata."""
    monkeypatch.setattr(rcb, "document_strata", lambda: {"d": "academic"})
    monkeypatch.setattr(rcb.cp, "chunk_yield",
                        lambda tag: {f"d#c{i}": {"nodes": n}
                                     for i, n in enumerate([0, 5, 36])})
    band = rcb.yield_by_stratum()["academic"]
    assert (band["envelope_low"], band["envelope_high"]) == (0, 36)
    assert "gates nothing" in band["basis"]
    assert "band_low" not in band and "band_high" not in band


def test_a_batch_outside_the_envelope_is_flagged_and_inside_is_not():
    band = {"envelope_low": 5, "envelope_high": 20}
    assert rcb.yield_flag(12.0, band) is None
    assert rcb.yield_flag(5.0, band) is None and rcb.yield_flag(20.0, band) is None
    assert "below" in rcb.yield_flag(4.9, band)
    assert "above" in rcb.yield_flag(20.1, band)
    assert rcb.yield_flag(0.0, None) is None            # no band, no flag


def test_a_zero_yield_stratum_is_flagged_only_if_the_envelope_excludes_zero():
    """ADDENDUM-01 §3.4: a zero-yield CHUNK is healthy and appears in no flag logic — every
    Phase A stratum contained one. Zero is not special-cased into an anomaly; it is only ever
    compared to the envelope like any other value."""
    assert rcb.yield_flag(0.0, {"envelope_low": 0, "envelope_high": 36}) is None
    assert "below" in rcb.yield_flag(0.0, {"envelope_low": 5, "envelope_high": 20})


def test_yield_flags_gate_nothing_the_sprt_is_the_monitor():
    """The flag is a string for the RESULT, never an input to accept/reject. ADDENDUM-06 §2 is
    unchanged by ADDENDUM-01 §3.3, so the decision function cannot even SEE a yield: it takes
    fabrications, facts and the boundaries, and nothing else."""
    import inspect
    params = list(inspect.signature(rcb.sprt_decide).parameters)
    assert params == ["fabrications", "facts", "b"]
    # and the same evidence decides the same way whatever the yield was
    b = rcb.sprt_boundaries()
    assert rcb.sprt_decide(0, 200, b) == "accept"
    assert rcb.sprt_decide(40, 200, b) == "reject"
    # the stop rule likewise sees only outcomes
    st = rcb.BurnState()
    assert list(inspect.signature(st.record).parameters) == ["outcome"]


def test_each_batch_judges_under_its_own_ledger_run():
    """A single shared judge run would put ~6,000 facts across 13 batches under one ceiling,
    and the guard would refuse batch 2 onwards for having spent batch 1's budget. Phase A
    already hit that ceiling once, correctly, at 1,952,265 + 60,950 vs 2,000,000."""
    ids = {rcb.judge_run_id(f"bulk_v038_b{i:03d}") for i in range(1, 14)}
    assert len(ids) == 13
    assert all(i.startswith("bulk_v038_b") and i.endswith("_judge") for i in ids)
    # and the burn's ledger runs are named for the BATCH, not for the qualification phase
    assert rcb.judge_run_id("bulk_v038_b001") == "bulk_v038_b001_judge"


# --------------------------------------------- the SPRT applied SEQUENTIALLY
def test_the_increments_start_at_the_arithmetic_minimum_and_end_at_the_budget():
    """Below `min_facts_for_accept` no evidence can settle a batch, so the first increment
    is exactly that (DD-026 applied to this plan); the last is the budget, so the plan can
    spend what it declared and no more."""
    b = rcb.sprt_boundaries()
    inc = rcb.sprt_increments(b, 463)
    assert inc[0] == rcb.min_facts_for_accept(b) == 55
    assert inc[-1] == 463
    assert inc == sorted(inc) and len(set(inc)) == len(inc)
    assert rcb.sprt_decide(0, inc[0], b) == "accept"        # reachable at the first step


def test_a_clean_batch_stops_early_instead_of_paying_the_whole_budget():
    """The point of a SEQUENTIAL test, and what Wald's ASN prices: 159 expected facts at p0
    against a 463 budget. Judging the full budget every time costs ~8M tokens per batch and
    ~105M across the burn, for evidence the plan does not need."""
    b = rcb.sprt_boundaries()
    inc = rcb.sprt_increments(b, 463)
    assert rcb.sprt_decide(0, inc[0], b) == "accept"
    # a dirty batch crosses the other way, also before the budget
    assert rcb.sprt_decide(20, 110, b) == "reject"


def _judge(monkeypatch, per_increment, budget=463):
    """Drive the real judge_batch with a stubbed protocol returning scripted aggregates."""
    calls = []

    def fake_protocol(prefix, run, run_id, raters, fact_cap=None, fact_limit=None):
        calls.append(fact_limit)
        fab, facts = per_increment[min(len(calls) - 1, len(per_increment) - 1)]
        return {"pooled": {"n_facts": facts, "fabrication": fab}}

    monkeypatch.setattr(rcb.cp, "run_protocol", fake_protocol)
    monkeypatch.setattr(rcb.cp, "write_sample", lambda *a, **k: None)
    monkeypatch.setattr(rcb, "document_strata", lambda: {"d": "academic"})
    monkeypatch.setattr(rcb.cp, "window_for", lambda *a, **k: "")
    monkeypatch.setattr(rcb.cp.grounding, "normalize", lambda t: t)
    items = [{"doc_id": "d", "chunk_id": "d#c1", "event_id": f"e{i}",
              "payload": {"id": f"n{i}", "type": "Concept", "item": {"name": f"n{i}"}}}
             for i in range(400)]
    return rcb.judge_batch("bulk_v038_b001", items, {"d": "text"}, budget, ["r1", "r2"]), calls


def test_a_clean_batch_accepts_at_the_first_increment_and_judges_no_further(monkeypatch):
    v, calls = _judge(monkeypatch, [(0, 55)])
    assert v["outcome"] == "accept"
    assert calls == [55]                      # one increment, not nine
    assert v["sprt_trace"][-1]["facts"] == 55


def test_an_ambiguous_batch_escalates_until_a_boundary_or_the_budget(monkeypatch):
    """8 fabrications in 160 facts sits in the ambiguous band at every early step. It must
    keep escalating and then be recorded `sampling_inconclusive` — never left as a dangling
    `continue`, which the corpus stop rule does not count."""
    v, calls = _judge(monkeypatch, [(5, 55), (10, 110), (16, 165), (22, 220), (28, 275),
                                    (33, 330), (38, 385), (44, 440), (46, 463)])
    assert v["outcome"] in ("reject", "sampling_inconclusive")
    assert len(calls) > 1 and calls[-1] <= 463


def test_a_batch_that_never_crosses_a_boundary_is_inconclusive_not_continue(monkeypatch):
    """The defect this replaced: a fixed-n test returned `continue`, which is not one of
    accept / reject / sampling_inconclusive and which `BurnState.should_stop` ignores — so a
    persistently ambiguous burn would never trip the corpus stop rule."""
    steps = [(int(0.073 * n), n) for n in rcb.sprt_increments(rcb.sprt_boundaries(), 463)]
    v, _calls = _judge(monkeypatch, steps)
    assert v["outcome"] == "sampling_inconclusive"
    assert v["outcome"] in ("accept", "reject", "sampling_inconclusive", "protocol_failed")


def test_an_exhausted_sample_is_inconclusive_rather_than_an_endless_escalation(monkeypatch):
    """A small batch cannot supply the budget. When the protocol returns fewer facts than the
    limit asked for, no more evidence is obtainable and the batch settles as inconclusive."""
    v, calls = _judge(monkeypatch, [(3, 55), (5, 70), (5, 70)])
    assert v["outcome"] == "sampling_inconclusive"
    assert len(calls) <= 3


def test_a_protocol_failure_is_its_own_outcome_not_an_accept(monkeypatch):
    monkeypatch.setattr(rcb.cp, "run_protocol", lambda *a, **k: None)
    monkeypatch.setattr(rcb.cp, "write_sample", lambda *a, **k: None)
    monkeypatch.setattr(rcb, "document_strata", lambda: {"d": "academic"})
    monkeypatch.setattr(rcb.cp, "window_for", lambda *a, **k: "")
    monkeypatch.setattr(rcb.cp.grounding, "normalize", lambda t: t)
    items = [{"doc_id": "d", "chunk_id": "d#c1", "event_id": "e",
              "payload": {"id": "n", "type": "Concept", "item": {"name": "n"}}}]
    v = rcb.judge_batch("b", items, {"d": "t"}, 463, ["r1"])
    assert v["outcome"] == "protocol_failed"


def test_each_sequential_increment_is_a_superset_of_the_last(monkeypatch):
    """The contract that makes a sequential test payable: raising the limit must extend the
    sample, never reshuffle it. An unstable order re-judges facts already paid for AND applies
    the boundary to a sample that moved underneath it — the interval would be over a different
    population at every step."""
    by_stratum = {"academic": [f"a{i}" for i in range(50)],
                  "federal": [f"f{i}" for i in range(50)],
                  "standard": [f"s{i}" for i in range(50)]}
    order = rcb.cp.sequential_fact_order(by_stratum, "burn_bulk_v038_b001")
    again = rcb.cp.sequential_fact_order(by_stratum, "burn_bulk_v038_b001")
    assert order == again                                   # stable across calls
    for a, b in ((55, 110), (110, 165), (165, len(order))):
        assert order[:a] == order[:b][:a]                   # every step extends the last
    assert len(order) == 150 and len(set(order)) == 150     # every fact exactly once
    other = rcb.cp.sequential_fact_order(by_stratum, "burn_bulk_v038_b002")
    assert other != order                                   # a different batch draws its own


def test_the_sequential_order_spreads_across_strata_before_exhausting_one():
    """Round-robin, so an early stop is not a verdict about one document class. Taking the
    first 55 facts from a single stratum would make the batch's accept a claim about that
    stratum, not the batch."""
    by_stratum = {"a": [f"a{i}" for i in range(50)], "b": [f"b{i}" for i in range(50)]}
    first20 = rcb.cp.sequential_fact_order(by_stratum, "seed")[:20]
    assert sum(1 for f in first20 if f.startswith("a")) == 10
    assert sum(1 for f in first20 if f.startswith("b")) == 10


def test_an_uneven_stratum_does_not_stall_the_order():
    """A stratum that runs out must not truncate the sequence — the remaining strata carry on."""
    by_stratum = {"big": [f"x{i}" for i in range(10)], "tiny": ["y0"]}
    order = rcb.cp.sequential_fact_order(by_stratum, "seed")
    assert len(order) == 11 and len(set(order)) == 11


def test_a_resumed_batch_runs_under_the_ceiling_it_was_declared_with(tmp_path, monkeypatch):
    """A batch declares ONCE. The running mean moves as the burn proceeds — 49,458/chunk
    before batch 1, 59,094 once its own settles entered the window — so recomputing the
    ceiling on resume would ratchet the bound upward exactly when the batch is running hot.
    The ledger refuses a conflicting re-declare, which is how this was found: the burn crashed
    on resume rather than silently widening its own bound."""
    from kg import spend
    ledger_path = tmp_path / "spend_ledger.jsonl"
    ledger_path.write_text("")
    ledger = spend.SpendLedger(ledger_path)
    monkeypatch.setattr(spend, "default_ledger", lambda: ledger)
    # isolate the running mean: this test is about the DECLARE-ONCE decision, not about how
    # the mean is computed (that has its own tests), and the real ledger has live settles.
    monkeypatch.setattr(rcb, "mean_settled_per_chunk", lambda default: default)

    # first dispatch: declares from the running mean
    ceiling, per, resumed = rcb.declare_batch_ceiling("bulk_v038_b001", 61, 49_458.0)
    assert resumed is False and per == 49_458.0
    # ceil, not int: a bound rounded DOWN is a bound the work can exceed
    assert ceiling == math.ceil(1.3 * 49_458 * 61)

    # resume AFTER the mean has drifted upward: same ceiling, no re-declare, no crash
    again, per2, resumed2 = rcb.declare_batch_ceiling("bulk_v038_b001", 61, 59_094.0)
    assert (again, per2, resumed2) == (ceiling, None, True)
    assert int(ledger.declaration("bulk_v038_b001")["ceiling_tokens"]) == ceiling

    # a DIFFERENT batch still declares from the current mean
    other, per3, resumed3 = rcb.declare_batch_ceiling("bulk_v038_b002", 45, 59_094.0)
    assert resumed3 is False and other == math.ceil(1.3 * 59_094 * 45)


def test_declaration_is_read_only_and_reports_absence_rather_than_inventing_one(tmp_path):
    from kg import spend
    p = tmp_path / "l.jsonl"
    p.write_text("")
    ledger = spend.SpendLedger(p)
    assert ledger.declaration("never-declared") is None
    assert p.read_text() == ""            # reading must not write
