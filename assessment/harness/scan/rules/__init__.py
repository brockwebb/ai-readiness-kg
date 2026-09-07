"""Versioned rules: pure functions from Observations to a Finding. **No I/O, no network, no
clock, no model calls.**

Skeleton §6b.5: warnings are produced by deterministic, versioned rules "so thresholds can
change and history can be re-scored without re-measurement". That property is only real if a
rule cannot reach anything but its arguments, which is why `judge(observations, params)` takes
everything it may read and returns everything it decides.

`not_applicable` is a real verdict — a CSV surface has no JSON-LD to check, and calling that a
failure would score the format rather than the product. `error` means the COLLECTOR could not
observe; it never means the product failed.

**Two versions live here at once, and that is the point.** The 2026-09-06 conformance review
(`cc_tasks/2026-09-06_scan_targets.md` §2) found twelve `v1` rules implementing only part of
their `MeasurementSpec`. Each got a `v2` **module**; not one `v1` line was edited. `CURRENT`
is what a new cycle judges with; `REGISTRY` holds every version ever shipped, because the
re-derivation gate re-judges each stored Finding under **its own** `rule_id` — a Finding
recorded under `RULE-A1-v1` must re-derive to `RULE-A1-v1`, or history would be silently
re-scored under a rule that did not exist when it was measured.
"""
from __future__ import annotations

from . import (rule_a1, rule_a10, rule_a11_declared, rule_a2, rule_a3, rule_a4, rule_a5,
               rule_a6, rule_a8, rule_a9, rule_b3, rule_d1, rule_d4, rule_e5, rule_f4,
               rule_g1d)
from . import (rule_a1_v2, rule_a10_v2, rule_a11_declared_v2, rule_a2_v2, rule_a3_v2,
               rule_a6_v2, rule_a8_v2, rule_b3_v2, rule_d1_v2, rule_d4_v2, rule_e5_v2,
               rule_f4_v2)

#: Every version ever shipped, keyed by rule id. Never prune it: a pruned entry is a stored
#: Finding that can no longer be re-derived.
V1 = [rule_a1, rule_a2, rule_a3, rule_a4, rule_a5, rule_a6, rule_a8, rule_a9, rule_a10,
      rule_a11_declared, rule_b3, rule_d1, rule_d4, rule_e5, rule_f4, rule_g1d]
V2 = [rule_a1_v2, rule_a2_v2, rule_a3_v2, rule_a6_v2, rule_a8_v2, rule_a10_v2,
      rule_a11_declared_v2, rule_b3_v2, rule_d1_v2, rule_d4_v2, rule_e5_v2, rule_f4_v2]
MODULES = V1 + V2

REGISTRY = {m.RULE_ID: m for m in MODULES}

#: leg -> the rule a NEW cycle judges with: the highest version shipped for that leg. A4, A5,
#: A9 and G1-D stay at v1 — the review returned `spec_underspecified` for the first three
#: (the fix is in the spec, recorded as a `decision` property, not in the code) and the G1-D
#: `deviates` did not survive verification against the collector.
CURRENT = {m.LEG: m.RULE_ID for m in V1}
CURRENT.update({m.LEG: m.RULE_ID for m in V2})

#: Back-compatible alias. `BY_LEG` was the scaffold's name for what is now `CURRENT`.
BY_LEG = CURRENT


def judge(rule_id: str, observations: list, params: dict):
    mod = REGISTRY.get(rule_id)
    if mod is None:
        raise KeyError(f"no rule {rule_id!r}; known: {sorted(REGISTRY)}")
    return mod.judge(observations, params)
