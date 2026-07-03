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


def test_guard_passes_without_api_key():
    model_stub.guard_no_api_key(env={})  # no raise


def test_provenance_stamp_shape():
    stamp = model_stub.provenance_stamp("evt123")
    assert stamp["model_id"] == "claude-fable-5"
    assert stamp["extraction_event_id"] == "evt123"
    assert stamp["schema_version"] and stamp["timestamp"]


def test_invoke_makes_no_call():
    with pytest.raises(NotImplementedError, match="operator-gated"):
        model_stub.invoke(doc_id="d", source_text="x")
