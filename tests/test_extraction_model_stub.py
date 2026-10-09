"""Model stub: Fable model id, OAuth-only config, API-key guard, and no-call behavior."""
import json
import textwrap

from pathlib import Path

import pytest

from kg import spend
from kg.extraction import model_stub
from model_lock import FIXTURE_IDS, MODELS_HOME_ENV, build_models_home

# MODEL-001 (seldon AD-035): a stub config names a registry ROLE and the fixture lock
# (tests/model_lock.py) resolves it; the envelope must report that role's lock id.
ROLE = "document_extractor"
M = FIXTURE_IDS["opus"]


@pytest.fixture
def declared_run(tmp_path, monkeypatch):
    """A declared spend-ledger run on tmp_path (DD-022): invoke() refuses undeclared runs
    by design, so every test that reaches dispatch needs one."""
    controls = tmp_path / "controls.yaml"
    controls.write_text(textwrap.dedent("""\
        schema_version: "0.2"
        spend:
          daily_tokens: 1000000000
          call_class_floors: {cleanup: 36000, extraction: 111000, judge: 36000}
          empty_failure_backoff_seconds: [60, 300, 900]
          empty_failure_max_retries: 3
        """), encoding="utf-8")
    monkeypatch.setattr(spend, "_LEDGER_PATH", tmp_path / "spend_ledger.jsonl")
    monkeypatch.setattr(spend, "_CONTROLS_PATH", controls)
    spend.SpendLedger().declare("stub-test-run", 100_000_000,
                                declared_by="tests", call_class="extraction")
    monkeypatch.setenv(spend.RUN_ENV, "stub-test-run")
    return "stub-test-run"


def test_config_is_oauth_with_a_model_pin():
    # model_id is operator-tunable (Fable pilot, Opus re-baseline); provider is fixed OAuth.
    cfg = model_stub.load_model_config()
    assert cfg["model_id"]  # a model is pinned
    assert cfg["provider"] == "claude_max_oauth"


def test_guard_rejects_api_key():
    with pytest.raises(model_stub.ModelConfigError, match="ANTHROPIC_API_KEY"):
        model_stub.guard_no_api_key(env={"ANTHROPIC_API_KEY": "sk-should-not-be-here"})


def test_guard_rejects_auth_token():
    with pytest.raises(model_stub.ModelConfigError, match="ANTHROPIC_AUTH_TOKEN"):
        model_stub.guard_no_api_key(env={"ANTHROPIC_AUTH_TOKEN": "oauth-token"})


def test_guard_passes_without_credentials():
    model_stub.guard_no_api_key(env={})  # no raise


def test_prompt_version_is_v035():
    assert model_stub.prompt_version() == "0.3.5"


def test_provenance_stamp_shape_and_override():
    stamp = model_stub.provenance_stamp("evt123")
    assert stamp["extraction_event_id"] == "evt123"
    assert stamp["schema_version"] and stamp["timestamp"]
    assert stamp["prompt_version"] == "0.3.5"  # §4: prompt version stamped per item
    # envelope-reported model overrides the config default
    assert model_stub.provenance_stamp("e", model_id="claude-fable-5-x")["model_id"] == "claude-fable-5-x"


def test_build_prompt_substitutes(monkeypatch):
    prompt = model_stub.build_prompt("doc-9", "THE DOCUMENT BODY")
    assert "doc-9" in prompt and "THE DOCUMENT BODY" in prompt
    assert "{{document_text}}" not in prompt and "{{document_id}}" not in prompt


def test_model_substitution_error_carries_observed():
    err = model_stub.ModelSubstitutionError(expected="claude-fable-5", observed=["claude-opus-4-8"])
    assert err.expected == "claude-fable-5"
    assert err.observed == ["claude-opus-4-8"]
    assert isinstance(err, model_stub.ModelConfigError)


def test_extract_json_tolerates_fences():
    assert model_stub._extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert model_stub._extract_json('preamble {"b": 2} trailing') == {"b": 2}
    # No parseable JSON is a per-document invocation failure (driver retries/skips), NOT a
    # config fault fatal to every document — see _extract_json docstring (2026-07-09 fix).
    with pytest.raises(model_stub.ModelInvocationError):
        model_stub._extract_json("no json here")


def test_missing_cli_is_a_transient_invocation_error(monkeypatch, declared_run, tmp_path):
    # CLI auto-update window (2026-08-22): `claude` briefly unresolvable -> ModelInvocationError
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # MODEL-001: the CLI is the lock's, so the missing binary is a lock whose cli.path is gone.
    monkeypatch.setenv(MODELS_HOME_ENV, str(build_models_home(
        tmp_path / "models_home", cli_path=Path("/nonexistent/claude-binary"))))
    cfg = {"role": ROLE}
    with pytest.raises(model_stub.ModelInvocationError):
        model_stub.invoke("d", "text", prompt="p", config=cfg)
    # never-dispatched call released its reservation (DD-022): capacity fully restored
    ledger = spend.SpendLedger()
    assert ledger.committed(declared_run) == 0
    records = [json.loads(l) for l in ledger.path.read_text().splitlines()]
    assert any(r.get("record") == "release" for r in records)


def test_resume_session_id_adds_resume_flag(monkeypatch, declared_run):
    captured = {}
    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        class R: returncode = 0; stdout = json.dumps({"result": '{"ok": 1}', "modelUsage": {M: {}}}); stderr = ""
        return R()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(model_stub.subprocess, "run", fake_run)
    model_stub.invoke("d", "", prompt="p", config={"role": ROLE}, resume_session_id="sess-1")
    assert "--resume" in captured["cmd"] and "sess-1" in captured["cmd"]
    model_stub.invoke("d", "", prompt="p", config={"role": ROLE})
    assert "--resume" not in captured["cmd"]


def test_extract_json_recovers_toplevel_arrays():
    arr = '[{"id": "a", "verdict": "NONE"}, {"id": "b", "verdict": "supported"}]'
    assert model_stub._extract_json(arr) == json.loads(arr)
    assert model_stub._extract_json(f"Here are the results:\n```json\n{arr}\n```") == json.loads(arr)
    assert model_stub._extract_json(f"preamble {arr} trailing note") == json.loads(arr)
    # objects still win when the payload is an object
    assert model_stub._extract_json('{"facts": [1, 2]}') == {"facts": [1, 2]}


def test_parse_json_false_returns_prose_through_the_same_gates(monkeypatch, declared_run):
    """G1 EVAL observed leg (task 2026-09-02_g1_eval_probe_family_v0 step 1): the consumer
    elicits prose through this choke point. With parse_json=False the result text comes
    back unparsed; the DD-022 reservation is settled at the envelope's usage, and the
    model-identity gate still fires on a substituted model."""
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["cwd"] = kw.get("cwd")

        class R:
            returncode = 0
            stdout = json.dumps({"result": "Colorado had 564,757 one-person households, ±10,127.",
                                 "modelUsage": {M: {"inputTokens": 50, "outputTokens": 20}},
                                 "session_id": "s1"})
            stderr = ""
        return R()

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(model_stub.subprocess, "run", fake_run)
    meta = model_stub.invoke("g1-acs-moe-001.indirect", "", prompt="Restate the following …",
                             config={"role": ROLE}, parse_json=False)
    assert meta["output"] == "Colorado had 564,757 one-person households, ±10,127."
    assert meta["model_id"] == M and meta["usage"]["outputTokens"] == 20
    assert captured["cwd"] and "hermetic" in captured["cwd"]      # 2026-07-09 finding kept
    assert captured["cmd"][captured["cmd"].index("--model") + 1] == M
    ledger = spend.SpendLedger()
    assert ledger.committed(declared_run) == 70                    # settled at measured usage

    def substituted(cmd, **kw):
        class R:
            returncode = 0
            stdout = json.dumps({"result": "x", "modelUsage": {"other-model": {"inputTokens": 1}}})
            stderr = ""
        return R()

    monkeypatch.setattr(model_stub.subprocess, "run", substituted)
    with pytest.raises(model_stub.ModelSubstitutionError):
        model_stub.invoke("d", "", prompt="p", config={"role": ROLE}, parse_json=False)
