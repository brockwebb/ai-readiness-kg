#!/usr/bin/env python3
"""Resolve a Seldon artifact by name, once. **Read-only, no spend, no network beyond Neo4j.**

`cc_tasks/2026-09-07_scan_run_2.md` §1.4. Three registrars needed the same question — *is
there already an artifact with this name?* — and answered it three ways, one of which could
not work:

* `scripts/register_scan_figures.py::existing` queried the graph and was right.
* `scripts/register_hygiene_results.py` and `scripts/register_evidence_retention_result.py`
  did `name in $(seldon artifact list --type Script)`. **`seldon artifact list` does not print
  names** — only type, state and UUID — so the test was always False and every run minted a
  twin. Nothing downstream caught it: `seldon artifact create` enforces name uniqueness only
  on Results (AD-028). The twins surfaced much later, as
  `ValueError: Multiple Script artifacts with name=…`, at the moment a Result tried to
  reference one.

So the answer lives here, and the registrars import it. What a script owes is not to create
what it can find, and it cannot honour that with a check that cannot see.

**Superseded artifacts still resolve by name in the CLI.** `seldon result register
--script-name` matches over every artifact with the name, superseded included, so a name that
was ever duplicated stays unresolvable even after the twin is superseded. Callers pass
`--script-id`/`--data-ids` with the UUID this returns instead.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def live_artifact(name: str, repo: Path | None = None) -> str | None:
    """The one live (non-superseded) artifact id with this name, or None.

    Raises on more than one: two live artifacts sharing a name is a state no caller can act on
    correctly, and picking one silently is how a Result ends up linked to the wrong twin.
    """
    sys.path.insert(0, "/Users/brock/GitHub/seldon")
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(repo or REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            rows = [r["id"] for r in s.run(
                "MATCH (a {name: $n}) WHERE coalesce(a.state, '') <> 'superseded' "
                "RETURN a.artifact_id AS id ORDER BY a.created_at", n=name)]
    finally:
        driver.close()
    if len(rows) > 1:
        raise SystemExit(f"FATAL: {len(rows)} live artifacts named {name!r}: {rows}. "
                         f"Supersede all but one before registering anything against it.")
    return rows[0] if rows else None
