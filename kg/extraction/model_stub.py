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
import json
import os
import re
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:  # fail loud (standard 4)
    raise SystemExit("FATAL: 'pyyaml' is required to load model_config.yaml (pip install pyyaml)")

from kg import eventlog

_CONFIG_PATH = Path(__file__).resolve().parent / "model_config.yaml"
_PROMPT_PATH = Path(__file__).resolve().parent / "prompt_template.md"
# Credentials that must NOT be present: subscription OAuth only (DD-007). ANTHROPIC_API_KEY
# and ANTHROPIC_AUTH_TOKEN would both take precedence over the OAuth login.
_FORBIDDEN_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
# claude -p protocol invariants (not operator-tunable): JSON envelope, no tools (pure
# completion). "NoTool" is a non-existent tool name — an allowlist that grants nothing real.
_OUTPUT_FORMAT = "json"
_EMPTY_ALLOWLIST = "NoTool"


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
    """Refuse to proceed if an Anthropic API key or auth token is present (DD-007).
    Subscription OAuth (via `claude -p`) is the only sanctioned path; either variable would
    take precedence over the OAuth login, so we fail loud rather than let it through."""
    env = os.environ if env is None else env
    for name in _FORBIDDEN_ENV:
        if env.get(name):
            raise ModelConfigError(
                f"{name} is set; extraction uses subscription OAuth only (DD-007). "
                f"Unset it; `claude -p` authenticates via the existing Claude login."
            )


def prompt_version() -> str:
    """The extraction prompt template version (from its `prompt_version:` header line),
    stamped in extraction events per §4 so a re-run under a hardened prompt is traceable."""
    for line in _PROMPT_PATH.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*prompt_version:\s*(\S+)", line)
        if m:
            return m.group(1)
    raise ModelConfigError(f"no prompt_version header in {_PROMPT_PATH}")


def provenance_stamp(extraction_event_id: str, config: dict | None = None,
                     model_id: str | None = None) -> dict:
    """The universal provenance every extracted node/edge carries (§4). ``model_id`` overrides
    the config value with the model actually reported by the response envelope."""
    config = config or load_model_config()
    return {
        "model_id": model_id or config["model_id"],
        "schema_version": eventlog.schema_version(),
        "prompt_version": prompt_version(),
        "extraction_event_id": extraction_event_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def build_prompt(doc_id: str, source_text: str, config: dict | None = None) -> str:
    """Render prompt_template.md with the document. The rendered {{document_text}} IS the
    grounding source — validate spans against this same text (§5)."""
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    return (template
            .replace("{{schema_version}}", eventlog.schema_version())
            .replace("{{document_id}}", doc_id)
            .replace("{{document_text}}", source_text))


def _extract_json(result_text: str) -> dict:
    """Parse the extraction JSON object from the model's response text. Tolerates a leading
    ```json fence or surrounding prose by taking the outermost balanced object.

    Unusable model OUTPUT (empty / no JSON object / unparseable substring) is a per-document
    invocation failure — raise ModelInvocationError so the run driver retries once then skips
    the doc. It is NOT a ModelConfigError: a garbled response for one document must not fail
    loud and halt the whole run (that classification is reserved for config/credential faults
    that are fatal for every document)."""
    text = result_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ModelInvocationError("model response contains no JSON object")
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ModelInvocationError(f"model response JSON unparseable: {exc}")


class ModelInvocationError(RuntimeError):
    """A transport/CLI failure or an unusable envelope — the run driver may retry once."""


class ModelSubstitutionError(ModelConfigError):
    """The envelope reports a model other than the pinned one (e.g. a classifier reroute).
    Load-bearing gate: the driver records the substitution as an event and STOPs — the
    document's output is discarded unparsed, never substituted."""

    def __init__(self, expected: str, observed: list):
        self.expected = expected
        self.observed = observed
        super().__init__(f"expected {expected} but envelope reports models {observed}")


def invoke(doc_id: str, source_text: str, prompt: str | None = None,
           timeout: int = 1800, config: dict | None = None) -> dict:
    """Extract one document via ``claude -p`` on the subscription OAuth (no API key).

    Returns ``{output, model_id, usage, cost_usd, duration_ms, raw_result}`` where ``output``
    is the parsed extraction envelope. Raises ModelConfigError on a forbidden credential or a
    fallback model; ModelInvocationError on transport/CLI failure or an unparseable envelope.
    Never passes ``--bare`` (that path demands an API key).
    """
    config = config or load_model_config()
    guard_no_api_key()
    model_id = config["model_id"]
    prompt = prompt if prompt is not None else build_prompt(doc_id, source_text, config)

    cmd = [config.get("cli", "claude"), "-p", "--model", model_id,
           "--output-format", _OUTPUT_FORMAT, "--allowed-tools", _EMPTY_ALLOWLIST]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ModelInvocationError(f"claude -p timed out after {timeout}s for {doc_id}") from exc
    if proc.returncode != 0:
        raise ModelInvocationError(
            f"claude -p exited {proc.returncode} for {doc_id}: {proc.stderr.strip()[:300]}")

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ModelInvocationError(f"unparseable claude -p envelope for {doc_id}: {exc}") from exc
    if envelope.get("is_error"):
        raise ModelInvocationError(f"claude -p reported error for {doc_id}: {envelope}")

    model_usage = envelope.get("modelUsage", {})
    if model_id not in model_usage or len(model_usage) != 1:
        # A different/extra model served the call (classifier reroute / fallback). Raise the
        # substitution gate so the driver records it as an event and STOPs — never substitute.
        raise ModelSubstitutionError(expected=model_id, observed=list(model_usage))

    output = _extract_json(envelope.get("result", ""))
    return {
        "output": output,
        "model_id": model_id,
        "usage": model_usage.get(model_id, {}),
        "cost_usd": envelope.get("total_cost_usd"),
        "duration_ms": envelope.get("duration_ms"),
        "session_id": envelope.get("session_id"),
        "raw_result": envelope.get("result", ""),
    }
