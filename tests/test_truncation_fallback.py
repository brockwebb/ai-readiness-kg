"""ADDENDUM-01 §3: truncation is a status, never zero — the per-layer fallback.
A stubbed truncated envelope triggers three resumed layer turns; the merged event
carries all three layer groups. Also covers the v0.3.5 parser precheck counter."""
import json
import textwrap

import pytest

from kg import spend
from kg.extraction import model_stub, parser


@pytest.fixture
def declared_run(tmp_path, monkeypatch):
    controls = tmp_path / "controls.yaml"
    controls.write_text(textwrap.dedent("""\
        schema_version: "0.2"
        spend:
          daily_tokens: 1000000000
          call_class_floors: {cleanup: 36000, extraction: 111000, judge: 36000}
        """), encoding="utf-8")
    monkeypatch.setattr(spend, "_LEDGER_PATH", tmp_path / "spend_ledger.jsonl")
    monkeypatch.setattr(spend, "_CONTROLS_PATH", controls)
    spend.SpendLedger().declare("trunc-test", 100_000_000, declared_by="tests",
                                call_class="extraction")
    monkeypatch.setenv(spend.RUN_ENV, "trunc-test")


CFG = {"model_id": "m", "cli": "claude", "provider": "claude_max_oauth",
       "truncation_suspect_tokens": 40000}

TURN_PAYLOADS = [
    {"concepts": [{"id": "c1", "name": "X", "grounding_span": "s"}]},
    {"instruments": [{"id": "i1", "name": "AIDRIN", "grounding_span": "s"}],
     "measures": [{"id": "m1", "text": "t", "grounding_span": "s"}]},
    {"edges": [{"type": "mentions", "from_id": "doc", "to_id": "c1", "grounding_span": "s"}],
     "cites": []},
]


class StubCLI:
    """Call 1: truncated-looking envelope (big output, no layers). Calls 2-4: layer turns."""

    def __init__(self, first_result='{"note": "looks truncated"}'):
        self.calls = []
        self.first_result = first_result

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        n = len(self.calls)
        if n == 1:
            result, out_tokens = self.first_result, 50_000
        else:
            result, out_tokens = json.dumps(TURN_PAYLOADS[n - 2]), 500

        class R:
            returncode = 0
            stdout = json.dumps({"result": result, "session_id": f"sess-{min(n,1)}",
                                 "modelUsage": {"m": {"inputTokens": 10,
                                                      "outputTokens": out_tokens}}})
            stderr = ""
        return R()


def test_truncated_envelope_triggers_per_layer_fallback(declared_run, monkeypatch):
    stub = StubCLI()
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    meta = model_stub.invoke_with_layer_fallback("doc-x", "text", config=CFG)
    assert meta["emission_mode"] == "per_layer"
    assert meta["parse_failed_truncated"] is True
    # all three layer groups present in the merged output
    assert meta["output"]["concepts"] and meta["output"]["instruments"] \
        and meta["output"]["measures"] and meta["output"]["edges"]
    assert len(stub.calls) == 4
    for cmd in stub.calls[1:]:
        assert "--resume" in cmd, "layer turns must resume the original session"
    assert meta["usage"]["outputTokens"] == 50_000 + 3 * 500


def test_unparseable_big_envelope_also_falls_back(declared_run, monkeypatch):
    stub = StubCLI(first_result="no json here at all —")
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    meta = model_stub.invoke_with_layer_fallback("doc-x", "text", config=CFG)
    assert meta["emission_mode"] == "per_layer"
    assert meta["output"]["instruments"][0]["name"] == "AIDRIN"


def test_small_layerless_output_is_not_treated_as_truncation(declared_run, monkeypatch):
    class SmallStub(StubCLI):
        def __call__(self, cmd, **kw):
            self.calls.append(cmd)

            class R:
                returncode = 0
                stdout = json.dumps({"result": '{"concepts": []}', "session_id": "s",
                                     "modelUsage": {"m": {"outputTokens": 900}}})
                stderr = ""
            return R()
    stub = SmallStub()
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    meta = model_stub.invoke_with_layer_fallback("doc-x", "text", config=CFG)
    assert len(stub.calls) == 1           # no fallback below the suspicion floor
    assert "emission_mode" not in meta


def test_parser_precheck_counts_span_lacks_name():
    doc = "The Data Pillar is described here. Quality matters."
    out = {"document_id": "d",
           "concepts": [
               {"id": "c1", "name": "Data Pillar",
                "grounding_span": "The Data Pillar is described here."},
               {"id": "c2", "name": "data quality",       # span lacks the name
                "grounding_span": "Quality matters."}]}
    res = parser.parse_extraction(out, doc, enforce_span_coverage=False)
    assert res.precheck_span_lacks_name == 1
    assert len(res.nodes) == 2            # precheck counts, it does not quarantine
