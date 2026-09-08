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

import re

from . import (rule_a1, rule_a10, rule_a11_declared, rule_a2, rule_a3, rule_a4, rule_a5,
               rule_a6, rule_a8, rule_a9, rule_b3, rule_d1, rule_d4, rule_e5, rule_f4,
               rule_g1d)
from . import (rule_a1_v2, rule_a10_v2, rule_a11_declared_v2, rule_a2_v2, rule_a3_v2,
               rule_a6_v2, rule_a8_v2, rule_b3_v2, rule_d1_v2, rule_d4_v2, rule_e5_v2,
               rule_f4_v2)
from . import rule_a2_v3, rule_a3_v3, rule_d1_v3, rule_f4_v3
from . import rule_a1_v3, rule_a3_v4
from . import rule_a8_v3, rule_a10_v3
from . import rule_a1_v4, rule_a3_v5
from . import rule_a12

#: Every version ever shipped, keyed by rule id. Never prune it: a pruned entry is a stored
#: Finding that can no longer be re-derived.
V1 = [rule_a1, rule_a2, rule_a3, rule_a4, rule_a5, rule_a6, rule_a8, rule_a9, rule_a10,
      rule_a11_declared, rule_b3, rule_d1, rule_d4, rule_e5, rule_f4, rule_g1d]
V2 = [rule_a1_v2, rule_a2_v2, rule_a3_v2, rule_a6_v2, rule_a8_v2, rule_a10_v2,
      rule_a11_declared_v2, rule_b3_v2, rule_d1_v2, rule_d4_v2, rule_e5_v2, rule_f4_v2]

#: A third generation, for the four `v2` modules that shared one guard bug. See any of their
#: docstrings: `.get("status", 999)` returns `None` on a present-but-None key, and it stopped a
#: live cycle. `v2` stays here so every Finding recorded under it still re-derives.
V3 = [rule_a2_v3, rule_a3_v3, rule_d1_v3, rule_f4_v3, rule_a1_v3]

#: A fourth generation for A3 alone. `RULE-A1-v3` and `RULE-A3-v4` decide exactly what their
#: predecessors decided; what changed is where the evidence comes from — the SHARED
#: `link_probe` leg, collected once per surface instead of twice
#: (`cc_tasks/2026-09-07_scan_harness_v3.md` §1.3). Their predecessors stay in `REGISTRY`.
V4 = [rule_a3_v4]

#: A fifth generation, for the defect a SURFACE found that no fixture anticipated: a rule that
#: reaches a verdict from a probe whose error class is BLIND. `RULE-A10-v2` returned `pass` on
#: `scan-eia-flagship-1-open-data` because its invalid-route probe was killed mid-connection and
#: "not 200" was the only test it ran (`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.2), and
#: `RULE-A8-v2` would have credited an email-signup page on a third-party host as a resolving
#: latest-vintage pointer (§6.1). Both are the same shape: a verdict about the product reached
#: from something that is not evidence about the product.
#:
#: From this generation on, every rule calls `_common.unobserved_error` on each probe it scores
#: on, and `tests/test_scan_harness_v4.py` lints for it. Their predecessors stay in `REGISTRY`.
V5 = [rule_a8_v3, rule_a10_v3]

#: A sixth generation for the two legs harness-v4 left open and NAMED rather than fixed
#: (`cc_tasks/2026-09-08_scan_harness_v4_RESULT.md` §7.1): A1 and A3 filter link probes through
#: `_common.served()` and then return `fail` when nothing survives, so a page that WAS served
#: while every link on it was reset is scored as offering nothing. That is harness-v4's own
#: defect pointed the other way, and `only_errors` cannot catch it because the page observation
#: is real. A blind link is unobserved FOR THAT LINK; all blind is `error`; some blind is judged
#: over the rest with the blind count on the Finding. Predecessors stay in `REGISTRY`.
V6 = [rule_a1_v4, rule_a3_v5]

#: Rules for CANDIDATE indicators. They judge, they are recorded, and their Findings enter no
#: numerator and no denominator (DD-054). Kept in their own list so the reporting layer can
#: exclude them mechanically rather than by remembering a code.
CANDIDATE_RULES = [rule_a12]

#: Every generation, in order. A LIST of lists rather than four names a reader has to keep
#: track of: the registry-integrity tests read this, so a fifth generation is one entry here
#: and nothing else to remember — which is the same reasoning `parse_rule_id` gives for being
#: a regex instead of a per-rule table.
GENERATIONS = (V1, V2, V3, V4, V5, V6)

MODULES = [m for g in GENERATIONS for m in g] + CANDIDATE_RULES

REGISTRY = {m.RULE_ID: m for m in MODULES}

#: leg -> the rule a NEW cycle judges with: the highest version shipped for that leg. A4, A5,
#: A9 and G1-D stay at v1 — the review returned `spec_underspecified` for the first three
#: (the fix is in the spec, recorded as a `decision` property, not in the code) and the G1-D
#: `deviates` did not survive verification against the collector.
CURRENT = {}
for _gen in GENERATIONS:
    CURRENT.update({m.LEG: m.RULE_ID for m in _gen})
CURRENT.update({m.LEG: m.RULE_ID for m in CANDIDATE_RULES})

#: Legs whose Findings are reported and never counted.
CANDIDATE_LEGS = frozenset(m.LEG for m in CANDIDATE_RULES)

#: The legs a FRACTION may be computed over. `CURRENT` minus the candidates.
FRAMEWORK_LEGS = tuple(l for l in CURRENT if l not in CANDIDATE_LEGS)

#: Back-compatible alias. `BY_LEG` was the scaffold's name for what is now `CURRENT`.
BY_LEG = CURRENT


#: A rule id parses; it is never looked up. `RULE-<indicator>[-<qualifier>...]-<version>`.
#: The indicator code is the leading `[A-G]<digits>`, optionally followed by a single
#: UPPERCASE leg letter — that is the shape `build_framework_graph.py` mints (`_ROW`'s
#: `[A-G]\d{1,2}`, plus the `G1-D` / `G1-O` split of DD-036). A lowercase segment after it is
#: a rule QUALIFIER, not part of the indicator: `RULE-A11-declared-v2` measures A11, and
#: `RULE-G1-D-v1` measures G1-D. Case is what separates the two, which is why this is a regex
#: and not a table: a per-rule table would have to be edited for every new rule, and the one
#: that was forgotten would be the one that mattered.
_RULE_ID = re.compile(
    r"^RULE-"
    r"(?P<indicator_code>[A-G]\d{1,2}(?:-[A-Z])?)"
    r"(?P<qualifier>(?:-[a-z][a-z0-9_]*)*)"
    r"-(?P<version>v\d+)$")


def parse_rule_id(rule_id: str) -> dict:
    """`{indicator_code, qualifier, version}` for a rule id, or `ValueError`.

    The graph needs `Rule -> AssessmentIndicator` and needs each `Rule` to carry its own
    version. Neither can come from the recorded Finding: `_common.RULE_VERSION` is the
    literal `"v1"` for every rule ever shipped, and it is an INPUT to the derived
    `finding_id`, so it cannot be corrected without re-identifying every stored Finding.
    The rule id is the only place the version is actually true, so parse it there.
    """
    m = _RULE_ID.match(rule_id)
    if m is None:
        raise ValueError(f"unparseable rule id {rule_id!r}: expected RULE-<indicator>"
                         f"[-<qualifier>]-v<n>")
    return {"rule_id": rule_id, "indicator_code": m.group("indicator_code"),
            "qualifier": m.group("qualifier").lstrip("-") or None,
            "version": m.group("version")}


def consumes(rule_id: str) -> tuple:
    """Legs whose observations this rule reads IN ADDITION to its own.

    Declared on the rule module (`CONSUMES`) and read by the two callers that must agree —
    `run.py` when it builds the group a rule judges, and `rederive.py` when it rebuilds that
    group from stored observations. One declaration, two readers: a re-derivation that grouped
    differently from the cycle would move the derived `finding_id` and fail the gate for a
    reason that has nothing to do with the rule.
    """
    mod = REGISTRY.get(rule_id)
    if mod is None:
        raise KeyError(f"no rule {rule_id!r}; known: {sorted(REGISTRY)}")
    return tuple(getattr(mod, "CONSUMES", ()))


#: Legs a NEW cycle collects only because some CURRENT rule consumes them. They have no rule of
#: their own and produce no Finding — they are evidence, shared.
SHARED_LEGS = tuple(sorted({l for r in set(CURRENT.values()) for l in consumes(r)}))


def judge(rule_id: str, observations: list, params: dict):
    mod = REGISTRY.get(rule_id)
    if mod is None:
        raise KeyError(f"no rule {rule_id!r}; known: {sorted(REGISTRY)}")
    return mod.judge(observations, params)
