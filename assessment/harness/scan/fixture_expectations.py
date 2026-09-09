"""Derive each control fixture's expected verdicts from COLLECTOR DISPATCH. **Pure, no network.**

Task `cc_tasks/2026-09-08_a8_v4_blind_pointer_and_fixture_table.md` §1, decision 2.

**Why this exists.** The `resets_links_only` table was written by reading RULE source and
asking "which legs would this fixture touch". The answer was A1 and A3; it was wrong, because
`v2clauses.follow_latest_pointer` also dereferences with `raw_head` and A8 was blinded too. The
control gate caught it (`cc_tasks/2026-09-08_scan_run_3_RESULT.md` §1) — but a pre-registration
method that produced one wrong row will produce another, so the method is retired. A fixture
blinds an HTTP **method**; which legs issue which methods is a fact about the collectors, and
this reads it there.

**What it derives, and what it deliberately does not.** Blindness, and only blindness. A leg
whose evidence a fixture makes unobservable is `error` — that is the whole of DD-052 §6 and its
mirror, and it is decidable from dispatch. Whether a served surface then *passes* is the rule's
judgement over content, which no amount of dispatch analysis can reach, so for those entries
this reports `deferred` and takes the checked-in table's value. Every emitted row says which it
was. A script that pretended to derive `A12 = fail` on `refuses_identified_client` would be
guessing with a provenance trail, which is the thing being replaced.

**Three facts, all read from source:**

* which collector functions each leg calls — `runner.collect_leg`'s own `if leg ==` dispatch,
  split into blocks (a sliding window ran past the branch end and mis-credited three
  collectors, `scripts/scan_tool_map.py` records that);
* which HTTP method each of those functions issues — `raw_head` / `raw_get` call sites in the
  collector source;
* whether a probe is a DEREFERENCE — a fetch of a URL discovered on the surface rather than of
  the surface itself. Detected from the signature: a function taking a `links` or `pointers`
  argument is handed URLs it did not choose. That is what `links.probe` and
  `follow_latest_pointer` have in common and it is why one fixture blinds both.
"""
from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

VERSION = "0.1.0"

SCAN = Path(__file__).resolve().parent
RUNNER = SCAN / "runner.py"
COLLECTORS = SCAN / "collectors"

#: A parameter name that means "URLs this function did not choose" — the signature of a
#: dereference. Read from the signature rather than listed by function name, so a third
#: dereferencing collector is covered the day it is written.
DEREFERENCE_PARAMS = ("links", "pointers")

#: The status classes a fixture can produce that mean "not observed". `refused` statuses come
#: from `params.manners.unobservable_statuses`; a reset produces no status at all.
_BLIND_NOTE = {"reset": "the connection is reset, so no response arrives",
               "refused": "the host answers a refusal status on a robots-permitted path"}


#: The runner branches on the shared leg through a PARAMETER, `if leg == lp["shared_leg"]`,
#: not a literal — so a block parser reading literals names that block `lp` and the shared
#: link probe goes missing. `link_probe.shared_leg` is where the name actually lives, and
#: resolving it here is the difference between deriving A1 and A3 and silently deferring them.
_PARAM_LEG = {"lp": ("link_probe", "shared_leg")}


def leg_blocks(src: str | None = None, params: dict | None = None) -> dict:
    """`runner.collect_leg`'s dispatch, split into per-leg blocks, with parameterised branch
    names resolved to the leg they actually select."""
    src = src if src is not None else RUNNER.read_text(encoding="utf-8")
    if params is None:
        from . import load_params
        params = load_params()
    marks = [(m.group(1), m.start()) for m in
             re.finditer(r'^\s*(?:el)?if leg (?:==|in) [\("\[]*([A-Za-z0-9_.\-]+)', src, re.M)]
    out: dict = {}
    for i, (token, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(src)
        leg = token
        if token in _PARAM_LEG:
            section, key = _PARAM_LEG[token]
            leg = params[section][key]
        out[leg] = out.get(leg, "") + src[start:end]
    return out


def collector_probes() -> dict:
    """`{module.function: {"methods": {...}, "dereference": bool}}`, read from the source.

    A function issues a method if it calls `raw_head`/`raw_get` anywhere in its body, including
    through a helper it calls in the same module — `collect_leg` reaches these through one or
    two hops and the method is what matters, not the depth.
    """
    out: dict = {}
    for path in sorted(COLLECTORS.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        # Module-level helpers a public function may call, so a method issued one hop down is
        # still attributed to the entry point.
        bodies = {n.name: ast.get_source_segment(text, n) or ""
                  for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name, body in bodies.items():
            reach = body + "".join(bodies.get(m, "") for m in bodies
                                   if m != name and re.search(rf"\b{re.escape(m)}\s*\(", body))
            methods = set()
            if "raw_head" in reach:
                methods.add("HEAD")
            if "raw_get" in reach:
                methods.add("GET")
            if not methods:
                continue
            node = next(n for n in tree.body
                        if isinstance(n, ast.FunctionDef) and n.name == name)
            args = {a.arg for a in node.args.args}
            out[f"{path.stem}.{name}"] = {
                "methods": methods,
                "dereference": bool(args & set(DEREFERENCE_PARAMS)),
            }
    return out


def _consumed(leg: str) -> tuple:
    """The SHARED legs this leg's current rule reads, via `rules.consumes`.

    Without this the derivation misses A1 and A3 entirely. Their own dispatch block collects
    nothing — `runner.collect_leg` returns `[]` for `link_probe.legs_served` — and every probe
    they judge on is issued under the shared `link_probe` leg. A derivation that reads only a
    leg's own block would defer exactly the two legs the fixture was built for, and would have
    confirmed their table rows by not looking at them.
    """
    from .rules import CURRENT, consumes
    rule = CURRENT.get(leg)
    return consumes(rule) if rule else ()


def leg_probes(legs) -> dict:
    """Per leg, the probes its collectors issue — its own block PLUS the shared legs its
    current rule consumes: `{leg: {"methods", "dereference_methods"}}`."""
    blocks = leg_blocks()
    probes = collector_probes()
    out: dict = {}
    for leg in legs:
        body = blocks.get(leg, "") + "".join(blocks.get(c, "") for c in _consumed(leg))
        methods, deref = set(), set()
        for fq, info in probes.items():
            mod, fn = fq.split(".")
            if re.search(rf"\b{re.escape(mod)}\.{re.escape(fn)}\s*\(", body):
                methods |= info["methods"]
                if info["dereference"]:
                    deref |= info["methods"]
        out[leg] = {"methods": methods, "dereference_methods": deref,
                    "consumes": list(_consumed(leg)),
                    "collectors": sorted(fq for fq in probes
                                         if re.search(
                                             rf"\b{re.escape(fq.split('.')[0])}\."
                                             rf"{re.escape(fq.split('.')[1])}\s*\(", body))}
    return out


def fixture_blindness(mode: dict) -> dict:
    """What a fixture's declared behaviour makes unobservable, from `fixtures.server.MODES`."""
    if mode.get("reset"):
        return {"blinds_all": True, "methods": {"GET", "HEAD"}, "why": _BLIND_NOTE["reset"],
                "scope": "every request"}
    if mode.get("reset_on_head"):
        return {"blinds_all": False, "methods": {"HEAD"}, "why": _BLIND_NOTE["reset"],
                "scope": "every HEAD; every GET is served"}
    if mode.get("refuse_status") is not None:
        return {"blinds_all": False, "methods": {"GET", "HEAD"},
                "why": _BLIND_NOTE["refused"],
                "scope": f"every path outside {sorted(mode.get('served_paths') or ())}",
                "served_paths": tuple(mode.get("served_paths") or ())}
    if mode.get("reset_on_invalid_route"):
        return {"blinds_all": False, "methods": {"GET"}, "why": _BLIND_NOTE["reset"],
                "scope": "the invalid-route path only", "single_path": True}
    return {"blinds_all": False, "methods": set(), "why": "nothing is blinded", "scope": "none"}


def expectations(fixture: str, mode: dict, legs, table) -> dict:
    """The expected verdict per leg, with how each was reached.

    `derived` rows are decidable from dispatch: every probe the leg depends on is unobservable,
    so the leg is `error`. `deferred` rows are not, and take the checked-in table's value —
    labelled, so a reader can see exactly how much of the table this script stands behind.
    """
    blind = fixture_blindness(mode)
    probes = leg_probes(legs)
    default = table.get("default") if isinstance(table, dict) else table
    out = {}
    for leg in legs:
        p = probes.get(leg, {"methods": set(), "dereference_methods": set()})
        table_value = (table.get(leg, default) if isinstance(table, dict) else table)
        if blind["blinds_all"]:
            out[leg] = {"verdict": "error", "how": "derived",
                        "why": f"every probe is unobservable: {blind['why']}"}
            continue
        # A leg whose DEREFERENCE probes are all blinded cannot see what the surface points at.
        # `resets_links_only` is exactly this and it is why A1, A3 and A8 are `error` there:
        # the page is served, the links and the latest-vintage pointer are not.
        if (p["dereference_methods"] and blind["methods"]
                and p["dereference_methods"] <= blind["methods"]
                and not blind.get("single_path")):
            out[leg] = {"verdict": "error", "how": "derived",
                        "why": (f"every dereference this leg issues is "
                                f"{sorted(p['dereference_methods'])} and the fixture blinds "
                                f"{sorted(blind['methods'])} ({blind['scope']}); the surface "
                                f"is served and what it points at is not")}
            continue
        out[leg] = {"verdict": table_value, "how": "deferred",
                    "why": ("blindness does not decide this leg here; the verdict is the "
                            "rule's judgement over served content and is taken from the "
                            "checked-in table")}
    return out


def check(params: dict, legs) -> dict:
    """Every fixture's derived table against the checked-in one. Differences are the report."""
    from .fixtures.server import MODES
    tables = params["e5_control"]["expected_verdicts"]
    diffs, derived_n, deferred_n = [], 0, 0
    per_fixture = {}
    for fixture, mode in MODES.items():
        table = tables.get(fixture)
        if table is None:
            diffs.append({"fixture": fixture, "leg": "*", "table": None, "derived": None,
                          "why": "the fixture has no pre-registered table"})
            continue
        got = expectations(fixture, mode, legs, table)
        per_fixture[fixture] = got
        for leg, info in got.items():
            derived_n += info["how"] == "derived"
            deferred_n += info["how"] == "deferred"
            have = (table.get(leg, table.get("default")) if isinstance(table, dict) else table)
            if info["how"] == "derived" and info["verdict"] != have:
                diffs.append({"fixture": fixture, "leg": leg, "table": have,
                              "derived": info["verdict"], "why": info["why"]})
    return {"fixtures": len(per_fixture), "derived": derived_n, "deferred": deferred_n,
            "differences": diffs, "per_fixture": per_fixture}
