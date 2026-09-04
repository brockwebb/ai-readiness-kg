"""Result-token resolution for the G1 findings memo and deck slide (task
2026-09-03_g1_freeze_calibration_redefinition_findings).

The memo's whole guarantee is that no number in it was typed by hand, which makes the resolver
the thing that has to be right: an unresolved token must never render as a plausible number, an
ambiguous name must never resolve to whichever Result was seen last, and a count stored as a
float must not print as "26.0" in prose.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import g1_resolve_results as res  # noqa: E402


def _log(tmp_path, events):
    p = tmp_path / "events.jsonl"
    p.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return p


def _created(aid, units, value, atype="Result", state="proposed", **props):
    return {"event_type": "artifact_created",
            "payload": {"artifact_id": aid, "artifact_type": atype, "to_state": state,
                        "properties": {"units": units, "value": value, **props}}}


def test_loads_results_by_units_and_ignores_other_artifact_types(tmp_path):
    log = _log(tmp_path, [
        _created("a", "g1_x_rate", 0.5, description="d"),
        _created("b", "g1_x_count", 12.0),
        {"event_type": "artifact_created",
         "payload": {"artifact_id": "c", "artifact_type": "DataFile",
                     "properties": {"name": "g1_x_rate", "path": "p"}}},
    ])
    got = res.load_results(log)
    assert set(got) == {"g1_x_rate", "g1_x_count"}
    assert got["g1_x_rate"]["value"] == 0.5 and got["g1_x_rate"]["description"] == "d"


def test_state_change_and_update_events_are_replayed(tmp_path):
    log = _log(tmp_path, [
        _created("a", "g1_x_rate", 0.5),
        {"event_type": "artifact_state_changed",
         "payload": {"artifact_id": "a", "to_state": "verified"}},
        {"event_type": "artifact_updated",
         "payload": {"artifact_id": "a", "properties": {"value": 0.6}}},
    ])
    got = res.load_results(log)
    assert got["g1_x_rate"]["state"] == "verified"
    assert got["g1_x_rate"]["value"] == 0.6


def test_a_name_registered_twice_is_ambiguous_not_last_write_wins(tmp_path):
    log = _log(tmp_path, [_created("a", "count", 1.0), _created("b", "count", 2.0),
                          _created("c", "count", 3.0)])
    got = res.load_results(log)
    assert "ambiguous" in got["count"]
    assert got["count"]["ambiguous"] == ["a", "b", "c"]
    _, errors = res.resolve_text("{{result:count:value}}", got, "f.md")
    assert len(errors) == 1 and "more than once" in errors[0]


def test_integral_values_render_without_a_trailing_zero(tmp_path):
    got = res.load_results(_log(tmp_path, [_created("a", "g1_n", 26.0), _created("b", "g1_r", 0.5457)]))
    out, errors = res.resolve_text("{{result:g1_n:value}} records at {{result:g1_r:value}}", got, "f.md")
    assert out == "26 records at 0.5457"
    assert errors == []


def test_unknown_name_and_unknown_field_leave_the_token_and_report(tmp_path):
    got = res.load_results(_log(tmp_path, [_created("a", "g1_n", 26.0)]))
    out, errors = res.resolve_text("{{result:g1_missing:value}} {{result:g1_n:median}}", got, "f.md")
    assert "{{result:g1_missing:value}}" in out          # never silently replaced
    assert "{{result:g1_n:median}}" in out
    assert len(errors) == 2
    assert "no registered Result named" in errors[0] and "has no field" in errors[1]


def test_error_lines_name_the_line_number(tmp_path):
    got = res.load_results(_log(tmp_path, [_created("a", "g1_n", 1.0)]))
    _, errors = res.resolve_text("line one\nline two\n{{result:nope:value}}\n", got, "memo.md")
    assert errors[0].startswith("memo.md:3:")


def test_escaped_placeholder_in_documentation_is_not_a_token():
    """The memo explains its own syntax; `{{result:<NAME>:value}}` must not be resolved."""
    assert res.TOKEN_RE.findall("{{result:<NAME>:value}}") == []
    assert res.TOKEN_RE.findall("{{result:g1_a-b.c:value}}") == [("g1_a-b.c", "value")]


def test_the_real_memo_resolves_end_to_end():
    """The committed memo must have no unresolved token — this is the guard that keeps a
    literal from creeping in as a token nobody registered."""
    memo = Path(__file__).resolve().parent.parent / "docs/research/2026-09-03_g1_eval_findings.md"
    results = res.load_results()
    text = memo.read_text(encoding="utf-8")
    _, errors = res.resolve_text(text, results, str(memo))
    assert errors == [], errors
    assert len(res.TOKEN_RE.findall(text)) > 100
