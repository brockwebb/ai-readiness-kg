"""Model consumers for the G1 observed leg (task 2026-09-02_g1_eval_probe_family_v0 step 1).

A `Consumer` turns a prompt into a completion. One production implementation exists,
`ClaudeCLIConsumer`, which invokes `claude -p` THROUGH the repo's model choke point
(`kg/extraction/model_stub.invoke`) rather than beside it, so every eval call passes the
same three gates every extraction call passes:

- DD-007: subscription OAuth only; an `ANTHROPIC_API_KEY` in the environment refuses.
- DD-022: reserve-before-dispatch on the shared spend ledger; an undeclared run refuses,
  and a refusal is the clean-stop contract (`SpendRefusalStop`, exit 0).
- Invariant 5: the envelope must report exactly the pinned model; anything else raises
  `ModelSubstitutionError`, the response is discarded unparsed, and the run stops.

The hermetic empty cwd is inherited from the stub (root cause 2026-07-09: with the repo
cwd the model loads CLAUDE.md and narrates). Model identity is pinned in
`assessment/config/g1_consumer.toml`, never in code.

The public probe families stay stdlib-only; this module imports `kg` lazily, at first use,
because the eval family is by design a consumer of the repo's spend guard.
"""
from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Protocol

from .config import ConfigError

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Completion:
    text: str
    model_id: str
    usage: dict = field(default_factory=dict)
    duration_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    spend_run_id: Optional[str] = None
    spend_reservation_id: Optional[str] = None


class Consumer(Protocol):
    model_id: str

    def complete(self, prompt: str, *, call_id: str) -> Completion: ...


@dataclass(frozen=True)
class ConsumerConfig:
    model_id: str
    provider: str
    cli: str
    timeout_seconds: int
    call_class: str


def load_consumer_config(path, table: str = "consumer") -> ConsumerConfig:
    """`table` selects the pinned consumer (`consumer`) or the single control arm
    (`control`, design D13, task 2026-09-03_g1_eval_v2); both pass the same gates."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"consumer config not found: {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    if table not in ("consumer", "control"):
        raise ConfigError(f"{path}: unknown consumer table {table!r} (consumer | control)")
    c = data.get(table)
    if not isinstance(c, dict):
        raise ConfigError(f"{path}: missing [{table}] table")
    for key in ("model_id", "provider", "cli", "timeout_seconds", "call_class"):
        if key not in c or c[key] in ("", None):
            raise ConfigError(f"{path}: [{table}] missing {key!r}")
    if c["provider"] != "claude_max_oauth":
        raise ConfigError(f"{path}: provider must be 'claude_max_oauth' (DD-007); got {c['provider']!r}")
    if not isinstance(c["timeout_seconds"], int) or c["timeout_seconds"] < 1:
        raise ConfigError(f"{path}: timeout_seconds must be a positive integer")
    return ConsumerConfig(model_id=c["model_id"], provider=c["provider"], cli=c["cli"],
                          timeout_seconds=c["timeout_seconds"], call_class=c["call_class"])


class ClaudeCLIConsumer:
    """`claude -p` under the pinned model, via the repo choke point (see module docstring)."""

    def __init__(self, config: ConsumerConfig):
        self.config = config
        self.model_id = config.model_id
        self._stub = None

    def _load_stub(self):
        if self._stub is None:
            if str(_REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(_REPO_ROOT))
            from kg.extraction import model_stub  # noqa: WPS433 — lazy by design
            self._stub = model_stub
        return self._stub

    def complete(self, prompt: str, *, call_id: str) -> Completion:
        stub = self._load_stub()
        stub_config = {"model_id": self.config.model_id, "provider": self.config.provider,
                       "cli": self.config.cli}
        meta = stub.invoke(call_id, "", prompt=prompt, timeout=self.config.timeout_seconds,
                           config=stub_config, parse_json=False)
        return Completion(text=str(meta.get("output") or ""), model_id=meta["model_id"],
                          usage=dict(meta.get("usage") or {}), duration_ms=meta.get("duration_ms"),
                          cost_usd=meta.get("cost_usd"), spend_run_id=meta.get("spend_run_id"),
                          spend_reservation_id=meta.get("spend_reservation_id"))


class ScriptedConsumer:
    """Test double: prompt -> canned text. Never in production. Unmapped prompts raise so
    a test cannot pass on an answer it did not script."""

    def __init__(self, responses: Dict[str, str], model_id: str = "scripted-model"):
        self.responses = dict(responses)
        self.model_id = model_id
        self.calls = []

    def complete(self, prompt: str, *, call_id: str) -> Completion:
        self.calls.append((call_id, prompt))
        if prompt in self.responses:
            text = self.responses[prompt]
        elif call_id in self.responses:
            text = self.responses[call_id]
        else:
            raise KeyError(f"ScriptedConsumer: no response scripted for {call_id!r}")
        return Completion(text=text, model_id=self.model_id, usage={"inputTokens": 0, "outputTokens": 0})


__all__ = ["Consumer", "Completion", "ConsumerConfig", "load_consumer_config",
           "ClaudeCLIConsumer", "ScriptedConsumer"]
