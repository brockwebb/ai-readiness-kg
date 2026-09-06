"""Evidence-first scan harness for the framework's public-tier AUTO legs.

Task `cc_tasks/2026-09-06_harness_scaffold.md`. Two exported verbs, matching §1:

    collect(spec, target) -> list[Observation]     # observes, judges nothing
    judge(rule_id, observations) -> Finding        # judges, observes nothing

Skeleton §6b.5 is the whole design: raw observed facts stored separately from calculated
warnings, warnings produced by deterministic versioned rules, "so thresholds can change and
history can be re-scored without re-measurement". `rederive.py` is the test of that claim.

**Zero model calls on the AUTO tier**, and it is a design property rather than a habit: a test
asserts that no model-provider client library is importable from this package.
"""
from __future__ import annotations

from pathlib import Path

HARNESS_VERSION = "0.1.0"
PARAMS_PATH = Path(__file__).resolve().parent / "params.yaml"


def load_params(path: Path | None = None) -> dict:
    import yaml
    return yaml.safe_load((path or PARAMS_PATH).read_text(encoding="utf-8"))


def collect(spec: dict, target: dict, params: dict | None = None, fetcher=None) -> list:
    """Observe one leg against one target. `spec` is a MeasurementSpec dict from the framework
    JSON; `target` is `{doc_id, url}`."""
    from .runner import collect_leg
    return collect_leg(spec, target, params or load_params(), fetcher)


def judge(rule_id: str, observations: list, params: dict | None = None):
    from .rules import judge as _judge
    return _judge(rule_id, observations, params or load_params())
