"""Resume correctness of the probe protocol (2026-08-27, task 2026-08-27_pilot_finish).

Both tests encode a defect found live while relaunching the ADDENDUM-05 §2 Instrument judge
after a daily-band refusal:

1. `probe_decompose.main` tested resume with `it["item_id"] in done and it["event_id"] in
   done` against a set of *item_ids only* — the second conjunct was never true, so a
   relaunch re-decomposed every item and appended a second copy of the fact set (177 lines
   for 24 items). Paid-for facts duplicated; model-sourced facts got new `fact_id`s.
2. Because `fact_id` hashes the sample's `event_id`, a rebuilt fact set orphans judge labels
   already on the shard, and `probe_aggregate.main` then died on `facts[fid]` KeyError.
   Orphans must be dropped loudly, never silently counted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import probe_aggregate as pa  # noqa: E402
import probe_decompose as pd  # noqa: E402

ITEM = {"item_id": "i-1", "event_id": "e" * 32, "kind": "node", "type": "Instrument",
        "stratum": "Instrument:pilot", "text": "AIDRIN", "grounding_span": "AIDRIN is a tool.",
        "doc_id": "doc-a", "window": None,
        "extra": {"id": "i-1", "name": "AIDRIN", "owner": "Hiniduma", "year": "2024"}}


def _metrics_dir(tmp_path: Path) -> Path:
    d = tmp_path / "corpus/staging/metrics"
    d.mkdir(parents=True)
    return d


def test_decompose_relaunch_is_a_no_op_when_facts_already_cover_the_sample(tmp_path, monkeypatch):
    metrics = _metrics_dir(tmp_path)
    (metrics / "probe_sample.jsonl").write_text(json.dumps(ITEM) + "\n", encoding="utf-8")
    facts = [{"fact_id": "f_aaa", "item_id": ITEM["item_id"], "event_id": ITEM["event_id"],
              "attribute": "owner", "fact_text": "owner: Hiniduma", "source": "deterministic",
              "decompose_version": "x"},
             {"fact_id": "f_bbb", "item_id": ITEM["item_id"], "event_id": ITEM["event_id"],
              "attribute": "year", "fact_text": "year: 2024", "source": "deterministic",
              "decompose_version": "x"}]
    facts_path = metrics / "probe_facts.jsonl"
    facts_path.write_text("".join(json.dumps(f) + "\n" for f in facts), encoding="utf-8")
    before = facts_path.read_text(encoding="utf-8")

    monkeypatch.setattr(pd, "REPO", tmp_path)
    monkeypatch.setattr(pd.model_stub, "invoke",
                        lambda *a, **k: pytest.fail("resume must not dispatch a model call"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(sys, "argv", ["probe_decompose.py"])

    assert pd.main() == 0
    assert facts_path.read_text(encoding="utf-8") == before, "relaunch duplicated the fact set"


def test_decompose_still_decomposes_an_item_whose_sample_was_rebuilt(tmp_path, monkeypatch):
    """Same item_id, NEW event_id (a rebuilt sample) is not 'done' — it must be decomposed."""
    metrics = _metrics_dir(tmp_path)
    rebuilt = {**ITEM, "event_id": "f" * 32}
    (metrics / "probe_sample.jsonl").write_text(json.dumps(rebuilt) + "\n", encoding="utf-8")
    (metrics / "probe_facts.jsonl").write_text(json.dumps(
        {"fact_id": "f_aaa", "item_id": ITEM["item_id"], "event_id": ITEM["event_id"],
         "attribute": "owner", "fact_text": "owner: Hiniduma", "source": "deterministic",
         "decompose_version": "x"}) + "\n", encoding="utf-8")

    monkeypatch.setattr(pd, "REPO", tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(sys, "argv", ["probe_decompose.py", "--dry-run"])

    assert pd.main() == 0
    written = [json.loads(l) for l in
               (metrics / "probe_facts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert any(f["event_id"] == rebuilt["event_id"] for f in written)


def test_aggregate_drops_orphaned_labels_loudly(tmp_path, monkeypatch, capsys):
    metrics = _metrics_dir(tmp_path)
    monkeypatch.setattr(pa, "REPO", tmp_path)
    (metrics / "run_sample.jsonl").write_text(json.dumps(ITEM) + "\n", encoding="utf-8")
    live = [{"fact_id": f"f_live{i}", "item_id": ITEM["item_id"], "event_id": ITEM["event_id"],
             "attribute": "owner", "fact_text": f"owner: X{i}", "source": "deterministic",
             "decompose_version": "x"} for i in range(3)]
    (metrics / "run_facts.jsonl").write_text("".join(json.dumps(f) + "\n" for f in live),
                                             encoding="utf-8")
    rows = [{"fact_id": f["fact_id"], "rater": r, "label": "entailed", "class": None,
             "confidence": 0.9} for f in live for r in ("a", "b")]
    rows.append({"fact_id": "f_orphan", "rater": "a", "label": "entailed", "class": None,
                 "confidence": 0.9})       # label from a fact set that no longer exists
    monkeypatch.setattr(pa, "load_labels",
                        lambda: (rows, {"a": "prov:SoftwareAgent", "b": "prov:SoftwareAgent"}))
    monkeypatch.setattr(sys, "argv", ["probe_aggregate.py", "--prefix", "run", "--run", "r"])

    assert pa.main() == 0
    out = json.loads((metrics / "run_aggregate.json").read_text(encoding="utf-8"))
    assert out["n_facts"] == 3 and out["n_labels"] == 6      # orphan excluded, not counted
    assert "f_orphan" not in out["per_fact"]
    assert "dropping 1 labelled fact_ids" in capsys.readouterr().err
