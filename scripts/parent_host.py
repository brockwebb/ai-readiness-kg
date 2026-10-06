#!/usr/bin/env python3
"""Parent-host cells: a verdict read from a host that answers for an organization above the
statistical unit is kept on the matrix and kept out of the unit's score. **Pure, no network.**

`cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md` decision 2, under DN-012 d5 and
audit finding C-13. The roster already said it of NCHS (`targets.yaml`: "robots.txt, /data.json
and /.well-known/ answer for a parent department, and a finding against them is not a finding
about the statistical agency"), and a rank built on cells the project disowns is not a rank.

**Which bodies.** Derived from the frame's own records; there is no list of bodies here, as the
task requires. A body's host answers for a parent organization when any of three roster
signals says so:

* **`host_shared_with`** on its cycle-1 roster row (`targets.yaml`): the roster's own words.
* **Its home is a section of the host.** The frame DataFile's `home` surface for the body (the
  recognized-agency link the frame roster was parsed from) is a page below the host's root, so
  the root, where `/robots.txt` and `/data.json` live, is somebody else's front door.
* **The .gov registry gives the host to the parent department.** CISA's registry, retained and
  attributed per frame host by the frame task (`state/fss_department_domains_2026-09.json`),
  attributes the host's registrable domain to the roster's `parent_department`, with no
  suborganization, and the host is that domain itself rather than a subdomain delegated to the
  unit. That is ORES on `www.ssa.gov`: the frame roster carries the bare host because the live
  recognized-agency list has no link for ORES, so the second signal cannot see it.

A body whose host is its own (`www.census.gov`, a delegated subdomain like `nces.ed.gov`) passes
none of the three and is never marked. Each mark carries the signals that made it.

**Which cells.** The legs whose collector reads a host-root file, from `parent_host.yaml`, plus
every current rule that `CONSUMES` one of them (read from the rules, so it cannot drift), and
only on a surface whose host IS the parent host: a flagship the unit publishes on a host of its
own is the unit's, whoever owns its home page's host.

    /opt/anaconda3/bin/python3 scripts/parent_host.py          the bodies, the legs, the reasons
"""
from __future__ import annotations

import functools
import json
import re
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

CONFIG = REPO / "scripts" / "parent_host.yaml"
TASK = "cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md"
DECISION = "DN-012 d5"

#: The mark a parent-host cell carries on a matrix row's `marks` and in `score.py`'s cells.
MARK = "parent_host"


@functools.lru_cache(maxsize=1)
def config() -> dict:
    import yaml
    c = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for key in ("host_file_legs", "roster"):
        if key not in c:
            raise SystemExit(f"FATAL: {CONFIG.relative_to(REPO)} declares no {key!r}")
    return c


def host_of(url: str | None) -> str:
    return (urllib.parse.urlsplit(url or "").hostname or "").lower()


def site_key(host: str) -> str:
    """The frame's own site bound (`targets.site_bound`): the host with one leading `www.`."""
    return host[4:] if host.startswith("www.") else host


def _norm(name: str) -> str:
    """The registry attribution's own normalisation (`normalisation` on that file): casefold,
    strip a leading "U.S." or "the", collapse whitespace."""
    s = " ".join((name or "").casefold().split())
    return re.sub(r"^(u\.s\.|the)\s+", "", s)


# ------------------------------------------------------------------------------ the legs

def ordered(legs) -> list:
    """Legs in `rules.CURRENT`'s order, which is the order every matrix and view uses."""
    from scan import rules
    order = list(rules.CURRENT)
    return sorted(legs, key=lambda l: order.index(l) if l in order else len(order))


def host_file_legs() -> frozenset:
    """The configured host-file legs and every current leg whose rule consumes one, to a fixed
    point (a consumer of a consumer reads the same file)."""
    from scan import rules
    legs = set(config()["host_file_legs"])
    unknown = sorted(legs - set(rules.CURRENT))
    if unknown:
        raise SystemExit(f"FATAL: {CONFIG.relative_to(REPO)} names {unknown}, which no current "
                         "rule judges")
    grew = True
    while grew:
        grew = False
        for leg, rid in rules.CURRENT.items():
            consumes = set(getattr(rules.REGISTRY[rid], "CONSUMES", ()) or ())
            if leg not in legs and consumes & legs:
                legs.add(leg)
                grew = True
    return frozenset(legs)


# ------------------------------------------------------------------------------ the bodies

def _frame(targets_doc: dict | None) -> dict:
    if targets_doc is not None:
        return targets_doc
    import build_l0_matrices as M
    from scan import load_params
    return M.targets(load_params())


def _cycle_one_shared() -> dict:
    import yaml
    doc = yaml.safe_load((REPO / config()["roster"]["cycle_one"]).read_text(encoding="utf-8"))
    return {a["code"]: a["host_shared_with"] for a in doc.get("agencies") or []
            if a.get("host_shared_with")}


def _registry() -> dict:
    path = REPO / config()["roster"]["registry_attribution"]
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {(r["host"], _norm(r["agency"])): r for r in doc["reverse_attribution"]}


def bodies(targets_doc: dict | None = None, shared: dict | None = None,
           registry: dict | None = None) -> dict:
    """`{body: {host, parent_department, signals: [...], registry: {...} | None}}` for every
    Tier A body whose host answers for a parent organization. The three inputs default to the
    frame's own files; a test passes its own."""
    frame = _frame(targets_doc)
    shared = _cycle_one_shared() if shared is None else shared
    registry = _registry() if registry is None else registry
    homes = {r["agency"]: r["url"] for r in frame.get("rows") or []
             if r.get("surface_kind") == "home" and r.get("tier", "A") == "A"}
    out = {}
    for a in frame.get("agency_detail") or []:
        if a.get("tier", "A") != "A":
            continue
        code, host = a["agency"], a["host"]
        reg = registry.get((host, _norm(a.get("agency_name", ""))))
        signals = []
        if code in shared:
            signals.append(f"the cycle-1 roster row carries `host_shared_with: {shared[code]}` "
                           f"({config()['roster']['cycle_one']})")
        home = homes.get(code)
        path = urllib.parse.urlsplit(home or "").path
        if home and path not in ("", "/"):
            signals.append(f"the frame's home surface for the body is `{home}`, a section of "
                           f"`{host}` rather than its root")
        if (reg and reg.get("in_registry") and not reg.get("registry_suborganization")
                and reg.get("registrable_domain") == site_key(host)
                and _norm(reg.get("registry_organization", ""))
                == _norm(a.get("parent_department", ""))):
            signals.append(f"the .gov registry attributes `{reg['registrable_domain']}` to "
                           f"{reg['registry_organization']}, the roster's parent department, "
                           f"with no suborganization, and `{host}` is that domain itself "
                           f"({config()['roster']['registry_attribution']})")
        if signals:
            out[code] = {"host": host, "parent_department": a.get("parent_department"),
                         "signals": signals,
                         "registry_agrees": bool(reg and reg.get("agrees_with_roster_parent")),
                         "registry": ({k: reg.get(k) for k in (
                             "registrable_domain", "registry_organization",
                             "registry_suborganization")} if reg else None)}
    return out


def answers_for(b: dict) -> str:
    """Whose host it is: the registry's words where the registry agrees with the roster's
    parent department, the roster's otherwise. The registry gives `federalreserve.gov` the
    suborganization "Federal Reserve Bank", which is not the Board the roster names, and the
    attribution file already records that disagreement (`agrees_with_roster_parent: false`)."""
    r = b.get("registry") or {}
    if r and b.get("registry_agrees"):
        return r.get("registry_suborganization") or r.get("registry_organization")
    return b.get("parent_department") or "a parent organization"


# ------------------------------------------------------------------------------ the cells

def marks_for_row(agency: str, url: str | None, legs, parent: dict, hf: frozenset) -> dict:
    """`{leg: MARK}` for the cells of one matrix row that were read from the body's parent host:
    a host-file leg, on a surface whose host is the body's roster host."""
    b = parent.get(agency)
    if not b or site_key(host_of(url)) != site_key(b["host"]):
        return {}
    return {leg: MARK for leg in legs if leg in hf}


def statement(parent: dict, cells: dict | None = None) -> list:
    """The disclosure, one entry per body, generated from the roster: which host, whose it is,
    why, and (when `cells` is given, `{body: {leg: n}}`) which cells left the score."""
    out = []
    for code in sorted(parent):
        b = parent[code]
        out.append({"body": code, "host": b["host"], "answers_for": answers_for(b),
                    "signals": b["signals"],
                    # In the order the matrices hold them (host matrix, then product), not sorted:
                    # `A11-declared` before `A4` is an alphabet, not the framework.
                    "cells": dict((cells or {}).get(code, {}))})
    return out


def main() -> int:
    parent = bodies()
    print(json.dumps({"task": TASK, "decision": DECISION,
                      "host_file_legs": ordered(host_file_legs()),
                      "bodies": statement(parent)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
