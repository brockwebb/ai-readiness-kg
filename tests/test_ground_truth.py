"""Ground-truth yield re-derivation (task 2026-08-30_ground_truth_yield_floor).

The whole point of this task is that a NUMBER produced here replaces an unvalidated one, so
every guard that keeps the number honest is tested with a seeded known-bad, and each test
enters through the real entrypoint rather than through the helper it wants to prove
(methodology §7.5; the M2 failure mode has recurred five times in this project).

Zero model spend: nothing here calls model_stub.invoke.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import ground_truth as gt  # noqa: E402


# ---------------------------------------------------------------- 1. rubric immutability

def test_rubric_sha_is_pinned_to_the_file_on_disk():
    assert hashlib.sha256(gt.RUBRIC.read_bytes()).hexdigest() == gt.RUBRIC_SHA
    assert gt.verify_rubric() == gt.RUBRIC_SHA


def test_a_changed_rubric_stops_every_phase(monkeypatch, tmp_path):
    """§5: a rubric defect found mid-task is reported and the task stops. Patching it after
    annotations exist would measure the patch, so the pin refuses rather than warns."""
    fake = tmp_path / "rubric.md"
    fake.write_text("a rubric someone edited mid-task", encoding="utf-8")
    monkeypatch.setattr(gt, "RUBRIC", fake)
    with pytest.raises(SystemExit) as exc:
        gt.verify_rubric()
    assert "immutable" in str(exc.value)
    # and it is the FIRST thing every phase does, not an advisory
    for phase in ("sample", "annotate", "reconcile", "score"):
        with pytest.raises(SystemExit):
            gt.PHASES[phase](type("A", (), {"ceiling_tokens": 1})())


def test_the_rubric_carries_its_three_mandated_sources_and_negative_rules():
    """§1 requires the rubric be COMPILED from schema, consumers and prior art, each cited,
    with explicit negative rules drawn from the pilot's set-difference sample."""
    t = gt.RUBRIC.read_text(encoding="utf-8")
    for cited in ("kg/schema.yaml", "usafacts_operationalization_skeleton.md",
                  "Luan", "ACE", "TAC KBP"):
        assert cited in t, cited
    for negative in ("N1", "N5", "N10"):
        assert negative in t
    # negative examples must be REAL, from the recorded set-difference sample
    for real_example in ("Bias Indicator", "AI training", "unad-"):
        assert real_example in t


# ---------------------------------------------------------------- 2. annotator class

def test_annotator_must_outclass_the_production_extractor(monkeypatch):
    """§3.1: NOT Haiku. The extractor under test was claude-haiku-4-5; an annotator of the
    same class would measure agreement between two equals, not ground truth."""
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-haiku-4-5-20251001"})
    with pytest.raises(SystemExit) as exc:
        gt.annotator_model()
    assert "Haiku" in str(exc.value)
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-opus-5"})
    assert gt.annotator_model() == "claude-opus-5"


# ---------------------------------------------------------------- 3. the draw

def test_the_committed_sample_is_reproducible_from_its_recorded_seed():
    """A draw that cannot be reproduced is a draw that could have been re-rolled after seeing
    a result. The file is tracked and committed before annotation for the same reason."""
    payload = json.loads(gt.SAMPLE_PATH.read_text())
    assert payload["seed"] == gt.SAMPLE_SEED
    assert payload["rubric_sha256"] == gt.RUBRIC_SHA
    assert len(payload["chunks"]) == gt.N_CHUNKS == len(set(payload["chunks"]))
    # every drawn chunk must be in the comparator set, or §4.3 (score v0.3.5 too) is impossible
    comparator = set(gt.comparator_chunks())
    assert set(payload["chunks"]) <= comparator
    # both represented documents appear — proportional allocation, not an accident of the seed
    assert len({c.split("#")[0] for c in payload["chunks"]}) == 2


def test_the_draw_records_the_documents_discrepancy_rather_than_hiding_it():
    """§2 asks for one chunk per document across five documents; the comparator set spans two.
    The constructed sample must SAY so."""
    payload = json.loads(gt.SAMPLE_PATH.read_text())
    assert len(payload["drawn_from"]["documents"]) == 2
    assert "five documents" in payload["note"] and "TWO" in payload["note"]


# ---------------------------------------------------------------- 4. matching

def test_containment_matching_and_its_limit():
    assert gt.match("aidrin", ["the aidrin tool", "x"]) == "the aidrin tool"
    assert gt.match("aidrin", ["aidrin", "the aidrin tool"]) == "aidrin"   # exact wins
    assert gt.match("aidrin", ["gmsd", "lof"]) is None
    assert gt.match("", ["anything"]) is None


# ---------------------------------------------------------------- 5. the stop condition

def test_low_interpass_agreement_stops_the_task_without_scoring(monkeypatch, tmp_path):
    """§3.4: below 0.5 the rubric is underspecified. The task STOPS and reports — it must not
    patch the rubric and re-run, because that measures the patch."""
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1"])
    monkeypatch.setattr(gt, "chunk_text_of", lambda cid: ("doc", "chunk text"))
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-opus-5"})
    monkeypatch.setattr(gt.spend, "set_current_run", lambda r: None)
    disjoint = {"checklist": '{"items":[{"name":"alpha","type":"Concept","rule":"P6"}]}',
                "consumer": '{"items":[{"name":"omega","type":"Concept","rule":"P6"}]}'}
    monkeypatch.setattr(gt, "_invoke",
                        lambda kind, cid, prompt, model: {"raw_result": disjoint.get(kind, "{}")})
    rc = gt.phase_reconcile(type("A", (), {})())
    assert rc == 3, "a sub-threshold agreement must be a non-zero, reportable stop"
    rep = json.loads((tmp_path / "ground_truth_reconciled.json").read_text())
    assert rep["interpass_agreement"]["mean_informative"] == 0.0
    assert not (tmp_path / "ground_truth_scores.json").exists()


def test_agreement_above_threshold_proceeds(monkeypatch, tmp_path):
    """CONTROL for the test above: the stop must not fire on healthy agreement."""
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1"])
    monkeypatch.setattr(gt, "chunk_text_of", lambda cid: ("doc", "chunk text"))
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-opus-5"})
    monkeypatch.setattr(gt.spend, "set_current_run", lambda r: None)
    same = '{"items":[{"name":"AIDRIN","type":"Instrument","rule":"P1"}]}'
    monkeypatch.setattr(gt, "_invoke", lambda kind, cid, prompt, model: {"raw_result": same})
    assert gt.phase_reconcile(type("A", (), {})()) == 0
    rep = json.loads((tmp_path / "ground_truth_reconciled.json").read_text())
    assert rep["chunks"]["d#c1"]["n_ground_truth"] == 1
    assert rep["interpass_agreement"]["mean_informative"] == 1.0


# ---------------------------------------------------------------- 6. reconciliation rules

def _reconcile_once(monkeypatch, tmp_path, checklist, consumer, decisions):
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1"])
    monkeypatch.setattr(gt, "chunk_text_of", lambda cid: ("doc", "chunk text"))
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-opus-5"})
    monkeypatch.setattr(gt.spend, "set_current_run", lambda r: None)
    payloads = {"checklist": json.dumps({"items": checklist}),
                "consumer": json.dumps({"items": consumer}),
                "adjudicate": json.dumps({"decisions": decisions})}
    monkeypatch.setattr(gt, "_invoke",
                        lambda kind, cid, prompt, model: {"raw_result": payloads[kind]})
    gt.phase_reconcile(type("A", (), {})())
    return json.loads((tmp_path / "ground_truth_reconciled.json").read_text())["chunks"]["d#c1"]


def test_a_singleton_is_admitted_only_on_a_cited_rule(monkeypatch, tmp_path):
    """§3.3: items in exactly one pass are re-scored ONCE against the rubric; admitted iff a
    cited rule applies. Not admitted by default, and not dropped by default."""
    r = _reconcile_once(
        monkeypatch, tmp_path,
        checklist=[{"name": "AIDRIN", "type": "Instrument", "rule": "P1"},
                   {"name": "solo admit", "type": "Measure", "rule": "P2"},
                   {"name": "solo reject", "type": "Concept", "rule": "P6"}],
        consumer=[{"name": "AIDRIN", "type": "Instrument", "rule": "P1"}],
        decisions=[{"name": "solo admit", "verdict": "admit", "rule": "P2"},
                   {"name": "solo reject", "verdict": "reject", "rule": "N2"}])
    assert r["agreed"] == 1 and r["singletons"] == 2
    assert r["adjudicated_admit"] == 1
    assert r["n_ground_truth"] == 2
    assert r["excluded_rejected"] == ["solo reject"]
    assert r["excluded_unresolvable"] == []


def test_an_unresolvable_singleton_is_excluded_AND_COUNTED(monkeypatch, tmp_path):
    """§3.3's explicit words: 'never silently dropped'. An excluded item that vanished from the
    report would understate annotation uncertainty in the number this task exists to produce."""
    r = _reconcile_once(
        monkeypatch, tmp_path,
        checklist=[{"name": "AIDRIN", "type": "Instrument", "rule": "P1"},
                   {"name": "murky", "type": "Concept", "rule": "P6"}],
        consumer=[{"name": "AIDRIN", "type": "Instrument", "rule": "P1"}],
        decisions=[{"name": "murky", "verdict": "unresolvable", "rule": ""}])
    assert r["n_ground_truth"] == 1
    assert r["excluded_unresolvable"] == ["murky"]


def test_a_singleton_the_adjudicator_never_ruled_on_is_excluded_not_admitted(monkeypatch,
                                                                             tmp_path):
    """Fail-closed: a missing verdict must not become an admission by omission."""
    r = _reconcile_once(
        monkeypatch, tmp_path,
        checklist=[{"name": "AIDRIN", "type": "Instrument", "rule": "P1"},
                   {"name": "forgotten", "type": "Concept", "rule": "P6"}],
        consumer=[{"name": "AIDRIN", "type": "Instrument", "rule": "P1"}],
        decisions=[])
    assert r["n_ground_truth"] == 1
    assert r["excluded_unresolvable"] == ["forgotten"]


# ------------------------------------------- 7. the DRAW itself, not the file it wrote

def _draw(monkeypatch, tmp_path, v039, v035):
    """Drive phase_sample end to end against stubbed shards."""
    monkeypatch.setattr(gt, "SAMPLE_PATH", tmp_path / "sample.json")
    monkeypatch.setattr(gt.cp, "apply_arm", lambda *a, **k: None)
    monkeypatch.setattr(gt.cp, "chunk_yield",
                        lambda tag: {c: {} for c in (v039 if tag == "v0_3_9" else v035)})
    gt.phase_sample(type("A", (), {})())
    return json.loads((tmp_path / "sample.json").read_text())


def test_the_draw_takes_only_chunks_BOTH_arms_cover(monkeypatch, tmp_path):
    """M2 CONTROL. The test above reads the committed file, which a correct run wrote — it
    would pass even if the draw were broken. This one drives the draw. A chunk outside the
    comparator set has no v0.3.5 comparator, so §4.3 (score v0.3.5 on the same chunks) becomes
    impossible and the over-extraction number silently loses its denominator."""
    both = [f"doc-a#c{i:04d}" for i in range(20)]
    only_new = [f"doc-b#c{i:04d}" for i in range(20)]       # in v0_3_9, absent from v0.3.5
    payload = _draw(monkeypatch, tmp_path, both + only_new, both)
    assert set(payload["chunks"]) <= set(both)
    assert not any(c.startswith("doc-b") for c in payload["chunks"])


def test_the_draw_is_reproducible_from_the_recorded_seed(monkeypatch, tmp_path):
    """A draw that differs run to run could have been re-rolled after seeing a result. Two
    independent invocations must agree exactly."""
    ids = [f"doc-a#c{i:04d}" for i in range(30)] + [f"doc-b#c{i:04d}" for i in range(14)]
    first = _draw(monkeypatch, tmp_path, ids, ids)
    second = _draw(monkeypatch, tmp_path / "again", ids, ids) if False else None
    (tmp_path / "again").mkdir()
    monkeypatch.setattr(gt, "SAMPLE_PATH", tmp_path / "again" / "sample.json")
    gt.phase_sample(type("A", (), {})())
    second = json.loads((tmp_path / "again" / "sample.json").read_text())
    assert first["chunks"] == second["chunks"]
    assert first["seed"] == second["seed"] == gt.SAMPLE_SEED


def test_the_draw_allocates_proportionally_across_represented_documents(monkeypatch, tmp_path):
    """Proportional to comparator coverage, largest-remainder — so the mix follows the data
    rather than an arbitrary quota, and no represented document is dropped."""
    ids = [f"doc-a#c{i:04d}" for i in range(30)] + [f"doc-b#c{i:04d}" for i in range(14)]
    payload = _draw(monkeypatch, tmp_path, ids, ids)
    assert payload["allocation"] == {"doc-a": 3, "doc-b": 2}
    assert sum(payload["allocation"].values()) == gt.N_CHUNKS
    assert len({c.split("#")[0] for c in payload["chunks"]}) == 2


def test_two_empty_passes_are_agreement_not_disagreement(monkeypatch, tmp_path):
    """MEASURED: three of the five sampled chunks are references/boilerplate where the correct
    answer is zero items, and both annotators independently returned zero. Scoring J(empty,
    empty) as 0.0 would have fired the §3.4 incident stop on a rubric that was working. J of
    two empty sets is 1 by convention, and such chunks carry no information about whether the
    rubric is specified finely enough, so the threshold reads the informative subset."""
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1", "d#c2"])
    monkeypatch.setattr(gt, "chunk_text_of", lambda cid: ("doc", "chunk text"))
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-opus-5"})
    monkeypatch.setattr(gt.spend, "set_current_run", lambda r: None)
    empty = '{"items":[]}'
    good = '{"items":[{"name":"AIDRIN","type":"Instrument","rule":"P1"}]}'
    monkeypatch.setattr(gt, "_invoke", lambda kind, cid, prompt, model: {
        "raw_result": empty if cid == "d#c1" else good})
    assert gt.phase_reconcile(type("A", (), {})()) == 0
    rep = json.loads((tmp_path / "ground_truth_reconciled.json").read_text())
    ag = rep["interpass_agreement"]
    assert ag["n_empty_empty"] == 1 and ag["n_informative"] == 1
    assert ag["mean_informative"] == 1.0
    # the empty-empty chunk itself must be scored as AGREEMENT, not as 0.0 — asserting only
    # the informative mean would leave that untested, since empty chunks are excluded from it
    assert ag["per_chunk"] == [1.0, 1.0]
    assert ag["mean_all_chunks"] == 1.0
    assert rep["chunks"]["d#c1"]["n_ground_truth"] == 0


def test_the_stop_still_fires_when_the_INFORMATIVE_chunks_disagree(monkeypatch, tmp_path):
    """CONTROL: the empty-empty carve-out must not become a way to dilute real disagreement.
    One empty-empty chunk alongside one disagreeing chunk must still stop."""
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1", "d#c2"])
    monkeypatch.setattr(gt, "chunk_text_of", lambda cid: ("doc", "chunk text"))
    monkeypatch.setattr(gt.model_stub, "load_model_config",
                        lambda *a, **k: {"model_id": "claude-opus-5"})
    monkeypatch.setattr(gt.spend, "set_current_run", lambda r: None)
    def raw(kind, cid, prompt, model):
        if cid == "d#c1":
            return {"raw_result": '{"items":[]}'}
        if kind == "adjudicate":
            return {"raw_result": '{"decisions":[]}'}
        name = "alpha" if kind == "checklist" else "omega"
        return {"raw_result": json.dumps(
            {"items": [{"name": name, "type": "Concept", "rule": "P6"}]})}
    monkeypatch.setattr(gt, "_invoke", raw)
    assert gt.phase_reconcile(type("A", (), {})()) == 3


def test_precision_and_recall_use_separate_numerators(monkeypatch, tmp_path):
    """Containment matching is many-to-one in BOTH directions. Counting matched ground-truth
    items and dividing by the arm's item count is not a precision — it produced 1.091 for
    Arm A3, an impossible value, before this was separated. Recall counts ground-truth items
    FOUND; precision counts arm items JUSTIFIED."""
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt.eventlog, "_EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1"])
    monkeypatch.setattr(gt, "verify_rubric", lambda: gt.RUBRIC_SHA)
    monkeypatch.setattr(gt.cp, "apply_arm", lambda *a, **k: None)
    monkeypatch.setattr(gt.cp, "chunk_yield",
                        lambda tag: {"d#c1": {"nodes": 1, "edges": 0}})
    # three ground-truth items all contained by ONE arm item
    (tmp_path / "ground_truth_reconciled.json").write_text(json.dumps({"chunks": {"d#c1": {
        "ground_truth": [{"name": "aidrin"}, {"name": "aidrin score"},
                         {"name": "score metric"}]}}}))   # all three ARE substrings
    monkeypatch.setattr(gt, "arm_items",
                        lambda tag, chunks: {"d#c1": {"the aidrin score metric bundle": {}}})
    gt.phase_score(type("A", (), {})())
    arms = json.loads((tmp_path / "ground_truth_scores.json").read_text())["arms"]
    r = arms["v0_3_9"]
    assert r["recall_matched"] == 3 and r["recall"] == 1.0     # all three GT items found
    assert r["precision_matched"] == 1                          # by ONE arm item
    assert r["precision_proxy"] == 1.0 and r["precision_proxy"] <= 1.0


def test_the_floor_is_derived_from_MEASURED_ground_truth_not_from_the_old_target(monkeypatch,
                                                                                 tmp_path):
    """The entire point of this task: the floor must come from what the chunks contain, not
    from the unvalidated 45.23 the pilot chased. A scorer that quietly kept the old target
    would reproduce the closure's own suspect number and look like a re-derivation."""
    monkeypatch.setattr(gt, "OUT_DIR", tmp_path)
    monkeypatch.setattr(gt.eventlog, "_EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(gt, "sample_chunks", lambda: ["d#c1", "d#c2"])
    monkeypatch.setattr(gt, "verify_rubric", lambda: gt.RUBRIC_SHA)
    monkeypatch.setattr(gt.cp, "apply_arm", lambda *a, **k: None)
    monkeypatch.setattr(gt.cp, "chunk_yield", lambda tag: {"d#c1": {"nodes": 0, "edges": 0},
                                                           "d#c2": {"nodes": 0, "edges": 0}})
    monkeypatch.setattr(gt, "arm_items", lambda tag, chunks: {})
    (tmp_path / "ground_truth_reconciled.json").write_text(json.dumps({"chunks": {
        "d#c1": {"ground_truth": [{"name": f"i{i}"} for i in range(10)]},
        "d#c2": {"ground_truth": [{"name": f"j{i}"} for i in range(20)]}}}))
    gt.phase_score(type("A", (), {})())
    out = json.loads((tmp_path / "ground_truth_scores.json").read_text())
    assert out["ground_truth_mean"] == 15.0
    assert out["rederived_floor"] == round(gt.FLOOR_FRACTION * 15.0, 3) == 9.0
    assert out["rederived_floor"] != round(0.60 * 45.227, 3)

