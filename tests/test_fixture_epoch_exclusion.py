"""Fixture epochs are excluded from extraction by RULE, not by 22 hand-emitted deferrals.

Task `cc_tasks/2026-09-05_extract_ai_ready_strand_11.md` §0.2, closing Issue `2e226acb`.

The 22 members of `g1dp-2026-09-02` / `g1srp-2026-09-03` / `g1sfc-2026-09-03` are the
*fixtures the G1 evaluation scores* — a Census API JSON slice, an NCHS Data Brief, a StatCan
cube. They were acquired to be measured, never to be read as literature, so they carry no
`extraction_request` and never will. Before this rule they landed in the gap diagnostic's
`never_queued` class, whose text is "admitted to the corpus; no extraction_request was ever
emitted for it" — true, and the wrong explanation: it reads as an oversight the corpus owes
work on, and it is the reason `never_queued` could not be driven to zero.

Why a rule rather than 22 events: the fixture epochs are still growing (three declarations in
four days), so a hand-emitted deferral per document is a step someone forgets on the fourth
epoch and the class silently refills. The membership is already declared once, in the dixie
ledger; tagging the EPOCH is the only place where the fact is stated once.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg import eventlog, queue  # noqa: E402


@pytest.fixture
def fixenv(tmp_path, monkeypatch):
    """A queue whose corpus is two documents, one in a fixture epoch and one not."""
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.3.5"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": {
        "fix-1": {"doc_id": "fix-1", "identity": {"title": "F"},
                  "screening": {"decision": "included", "rationale": "in"}},
        "lit-1": {"doc_id": "lit-1", "identity": {"title": "L"},
                  "screening": {"decision": "included", "rationale": "in"}}}}))
    profiles = tmp_path / "run_profiles.yaml"
    profiles.write_text(yaml.safe_dump({"default": "p", "profiles": {
        "p": {"corpus_epoch": "e", "template_sha256": "a" * 64}}}))
    decisions = tmp_path / "decisions.jsonl"
    decisions.write_text("".join(json.dumps(r) + "\n" for r in (
        {"event_type": "corpus_epoch_declared",
         "payload": {"epoch": "g1fix-test", "member_doc_ids": ["fix-1"]}},
        {"event_type": "corpus_epoch_declared",
         "payload": {"epoch": "lit-test", "member_doc_ids": ["lit-1"]}})))
    cfg = tmp_path / "dixie_evidence.yaml"

    def write_cfg(fixtures):
        cfg.write_text(yaml.safe_dump({"fixture_epochs": fixtures}), encoding="utf-8")

    write_cfg(["g1fix-test"])
    monkeypatch.setattr(queue, "_MANIFEST_PATH", manifest)
    monkeypatch.setattr(queue, "_PROFILES_PATH", profiles)
    monkeypatch.setattr(queue, "_LEDGER_PATH", tmp_path / "spend_ledger.jsonl")
    (tmp_path / "spend_ledger.jsonl").write_text("")
    monkeypatch.setattr(queue, "_DIXIE_DECISIONS", decisions)
    monkeypatch.setattr(queue, "_DIXIE_CONFIG", cfg)
    return {"write_cfg": write_cfg}


def test_a_fixture_epoch_member_is_deferred_with_no_event_on_the_log(fixenv):
    """The whole point: zero events, and the document still reads `excluded_by_design`."""
    assert queue.deferrals()["fix-1"]["reason"] == "eval_fixture"
    row = queue.project()["fix-1"]
    assert row["extraction_state"] == "deferred"
    assert row["deferred_reason"] == "eval_fixture"


def test_a_document_outside_a_fixture_epoch_is_untouched(fixenv):
    assert "lit-1" not in queue.deferrals()
    assert queue.project()["lit-1"]["extraction_state"] == "not_requested"


def test_the_rule_reads_the_config_rather_than_a_list_baked_into_the_code(fixenv):
    """Mutation guard: if the epoch names were hardcoded, retagging would not move anything."""
    fixenv["write_cfg"](["lit-test"])
    assert "fix-1" not in queue.deferrals()
    assert queue.deferrals()["lit-1"]["reason"] == "eval_fixture"


def test_a_fixture_document_cannot_be_queued(fixenv):
    """`never queued` has to be enforced, not hoped for. A deferral a request can revive is a
    default; §0.2 makes it a rule, so the request is refused at the entry point and names the
    epoch that refused it."""
    with pytest.raises(queue.QueueRefusal) as exc:
        queue.request("fix-1", 10, "cc", "because I felt like it")
    assert "g1fix-test" in str(exc.value)
    queue.request("lit-1", 10, "cc", "ordinary literature")   # the control: still allowed


def test_a_fixture_deferral_is_not_revived_by_an_event(fixenv):
    """`deferrals()` normally lets a later request revive a deferred document — that is the
    designed override for a human decision. A fixture exclusion is not a human decision about
    one document, so a request event that somehow reached the log (emitted before this rule,
    or by a path that bypassed `request`) must not silently re-arm extraction."""
    eventlog.append({"event_type": queue.REQUEST, "document_id": "fix-1", "priority": 10,
                     "requested_by": "cc", "reason": "legacy", "profile": "p",
                     "ts": "2026-09-05T00:00:00+00:00"}, batch=queue.QUEUE_BATCH)
    assert queue.deferrals()["fix-1"]["reason"] == "eval_fixture"
    assert queue.project()["fix-1"]["extraction_state"] == "deferred"
    assert "fix-1" not in queue.worklist()


# ------------------------------------------------------------------ against the live repo
def test_the_live_config_tags_every_g1_fixture_epoch_and_nothing_else():
    """Derived live, never hardcoded: the tagged set must be exactly the epochs whose members
    the G1 evaluation scores, and no epoch of literature may be in it."""
    tagged = set(queue.fixture_epochs())
    assert tagged == {"g1dp-2026-09-02", "g1srp-2026-09-03", "g1sfc-2026-09-03"}
    epochs = queue.corpus_epochs()
    assert tagged <= set(epochs), "a tagged epoch that no declaration ever created"
    assert "g1eval-2026-09-02" not in tagged, "the g1eval 17 are prior-art literature, not fixtures"


def test_no_live_fixture_document_carries_an_extraction_request():
    """If one ever does, the rule and the log disagree and the RESULT must say so."""
    members = {d for e in queue.fixture_epochs() for d in queue.corpus_epochs().get(e, ())}
    ever = queue.requests_ever()
    assert not (members & set(ever)), sorted(members & set(ever))
