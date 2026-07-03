#!/usr/bin/env python3
"""Model invocation stub — Claude Max OAuth only, never ANTHROPIC_API_KEY (DD-007).

This task makes ZERO LLM calls: ``invoke`` deliberately raises. What the stub *does* provide
now is (a) the provenance stamp every extracted item must carry (§4: model_id, schema_version,
extraction_event_id, timestamp) and (b) a hard guard that refuses to run under an API key.

The pilot run (a separate, operator-gated task) will implement ``invoke`` against a bare
``anthropic.Anthropic()`` client, which resolves the Claude Max OAuth profile from
``ant auth login`` when no ANTHROPIC_API_KEY is set. Fable (``claude-fable-5``) has thinking
always on; extraction depth is controlled by ``effort`` (see model_config.yaml).
"""
from __future__ import annotations

import datetime
import os
from pathlib import Path

try:
    import yaml
except ImportError:  # fail loud (standard 4)
    raise SystemExit("FATAL: 'pyyaml' is required to load model_config.yaml (pip install pyyaml)")

from kg import eventlog

_CONFIG_PATH = Path(__file__).resolve().parent / "model_config.yaml"
_FORBIDDEN_ENV = "ANTHROPIC_API_KEY"


class ModelConfigError(RuntimeError):
    """Config or credential misconfiguration — fail loud, never fall through (standard 4)."""


def load_model_config(path: Path | None = None) -> dict:
    """Load model_config.yaml. Fail loud on missing keys or a non-OAuth provider."""
    path = path or _CONFIG_PATH
    if not path.is_file():
        raise ModelConfigError(f"model config not found: {path}")
    with path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    for key in ("model_id", "provider"):
        if not cfg.get(key):
            raise ModelConfigError(f"model_config.yaml missing '{key}'")
    if cfg["provider"] != "claude_max_oauth":
        raise ModelConfigError(
            f"provider must be 'claude_max_oauth' (OAuth only, DD-007); got {cfg['provider']!r}"
        )
    return cfg


def guard_no_api_key(env: dict | None = None) -> None:
    """Refuse to proceed if an Anthropic API key is present in the environment (DD-007).
    OAuth is the only sanctioned auth path; a stray key would silently take precedence in the
    SDK's credential chain, so we fail loud rather than let it through."""
    env = os.environ if env is None else env
    if env.get(_FORBIDDEN_ENV):
        raise ModelConfigError(
            f"{_FORBIDDEN_ENV} is set; extraction uses Claude Max OAuth only (DD-007). "
            f"Unset it and authenticate via `ant auth login`."
        )


def provenance_stamp(extraction_event_id: str, config: dict | None = None) -> dict:
    """The universal provenance every extracted node/edge carries (§4)."""
    config = config or load_model_config()
    return {
        "model_id": config["model_id"],
        "schema_version": eventlog.schema_version(),
        "extraction_event_id": extraction_event_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def invoke(*args, **kwargs):
    """No-op in the module-build task. The pilot task implements this against a bare
    ``anthropic.Anthropic()`` (OAuth) after ``guard_no_api_key()``."""
    raise NotImplementedError(
        "model invocation is operator-gated; the extraction-module build makes no LLM calls. "
        "The pilot task implements invoke() against Claude Max OAuth (Fable)."
    )
