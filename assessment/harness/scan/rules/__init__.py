"""Versioned rules: pure functions from Observations to a Finding. **No I/O, no network, no
clock, no model calls.**

Skeleton §6b.5: warnings are produced by deterministic, versioned rules "so thresholds can
change and history can be re-scored without re-measurement". That property is only real if a
rule cannot reach anything but its arguments, which is why `judge(observations, params)` takes
everything it may read and returns everything it decides.

`not_applicable` is a real verdict — a CSV surface has no JSON-LD to check, and calling that a
failure would score the format rather than the product. `error` means the COLLECTOR could not
observe; it never means the product failed.
"""
from __future__ import annotations

from . import (rule_a1, rule_a10, rule_a11_declared, rule_a2, rule_a3, rule_a4, rule_a5,
               rule_a6, rule_a8, rule_a9, rule_b3, rule_d1, rule_d4, rule_e5, rule_f4,
               rule_g1d)

MODULES = [rule_a1, rule_a2, rule_a3, rule_a4, rule_a5, rule_a6, rule_a8, rule_a9, rule_a10,
           rule_a11_declared, rule_b3, rule_d1, rule_d4, rule_e5, rule_f4, rule_g1d]

REGISTRY = {m.RULE_ID: m for m in MODULES}
#: leg -> rule id, so a MeasurementSpec can be pointed at its rule and back.
BY_LEG = {m.LEG: m.RULE_ID for m in MODULES}


def judge(rule_id: str, observations: list, params: dict):
    mod = REGISTRY.get(rule_id)
    if mod is None:
        raise KeyError(f"no rule {rule_id!r}; known: {sorted(REGISTRY)}")
    return mod.judge(observations, params)
