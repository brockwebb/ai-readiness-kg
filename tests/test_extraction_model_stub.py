"""Model stub: Fable model id, OAuth-only config, API-key guard, and no-call behavior."""
import pytest

from kg.extraction import model_stub


def test_config_is_fable_oauth():
    cfg = model_stub.load_model_config()
    assert cfg["model_id"] == "claude-fable-5"
    assert cfg["provider"] == "claude_max_oauth"


def test_guard_rejects_api_key():
    with pytest.raises(model_stub.ModelConfigError, match="ANTHROPIC_API_KEY"):
        model_stub.guard_no_api_key(env={"ANTHROPIC_API_KEY": "sk-should-not-be-here"})


def test_guard_rejects_auth_token():
    with pytest.raises(model_stub.ModelConfigError, match="ANTHROPIC_AUTH_TOKEN"):
        model_stub.guard_no_api_key(env={"ANTHROPIC_AUTH_TOKEN": "oauth-token"})


def test_guard_passes_without_credentials():
    model_stub.guard_no_api_key(env={})  # no raise


def test_provenance_stamp_shape_and_override():
    stamp = model_stub.provenance_stamp("evt123")
    assert stamp["model_id"] == "claude-fable-5"
    assert stamp["extraction_event_id"] == "evt123"
    assert stamp["schema_version"] and stamp["timestamp"]
    # envelope-reported model overrides the config default
    assert model_stub.provenance_stamp("e", model_id="claude-fable-5-x")["model_id"] == "claude-fable-5-x"


def test_build_prompt_substitutes(monkeypatch):
    prompt = model_stub.build_prompt("doc-9", "THE DOCUMENT BODY")
    assert "doc-9" in prompt and "THE DOCUMENT BODY" in prompt
    assert "{{document_text}}" not in prompt and "{{document_id}}" not in prompt


def test_extract_json_tolerates_fences():
    assert model_stub._extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert model_stub._extract_json('preamble {"b": 2} trailing') == {"b": 2}
    with pytest.raises(model_stub.ModelConfigError):
        model_stub._extract_json("no json here")
