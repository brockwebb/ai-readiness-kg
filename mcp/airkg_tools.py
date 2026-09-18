#!/usr/bin/env python3
"""The nine verbs the MCP server exposes over this graph. **Zero spend, no network.**

`cc_tasks/2026-09-17_mcp_over_the_graph.md` decisions 2 and 3, under DN-005 §2.4.

**The verb bodies live here and not in the server module**, which is the architecture
`icsp_notebook/kg/mcp_server.py` arrived at for fss-policy-kg (its `kg/verbs.py`): the server
is a thin shell that registers wrappers, so the verbs are callable — and testable — without a
stdio transport, a client, or a running server process.

**Decision 3, the rule that decides which source answers what:** the record
(`framework/ai_readiness_framework.json`) and the published matrices are the source of truth;
Neo4j is a projection. A question about the framework is answered from the record even though
the graph holds the same nodes, exactly as `scripts/prescriptions.py` does it. Neo4j answers
only what only it holds — the Observations and Findings of a cycle, the Documents and
Definitions of the corpus — and `get_overview` reports whether that projection is current, so
a client can tell whether a Cypher answer is a fact or a stale one (DD-057).

**Decision 2, the locator rule:** every fact carries the address a stranger would have to open
to check it (DD-001). A locator is a small dict with a `kind`, and `resolve_locator` opens the
thing it names — so a locator that is present and wrong fails, which is the defect a
presence-only check would pass. The kinds:

    record      framework/ai_readiness_framework.json + a node id
    record_key  the record + a top-level key
    config      docs/reports/publication.yaml + a key
    matrix      a published matrix file + a `<body>/<leg>` cell
    payload     a cycle payload under state/ + a key
    evidence    a retained response body + the sha256 it is named for
    graph       a label + an id property + an id, in the one project database
    document    a corpus doc_id (+ section, where the source carries one)
    source      a source file + a symbol in it
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent
REPO = MCP_DIR.parent
sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

import airkg_guard as guard  # noqa: E402

RECORD = REPO / "framework" / "ai_readiness_framework.json"
PUBLICATION = REPO / "docs" / "reports" / "publication.yaml"
STATE = REPO / "state"
RULES_SOURCE = REPO / "assessment" / "harness" / "scan" / "rules" / "__init__.py"
ROUNDTRIP_GATE = REPO / "tests" / "test_framework_projection_roundtrip.py"

#: What a band reads when no estimate stands behind it. Decision 2: "The pending bands print as
#: `pending`, never as a number." Every band carries a notional value since
#: `cc_tasks/2026-09-17_notional_bands.md`, so today this rule fires on nothing — it is kept
#: because a band the operator clears is a band with no estimate again, and the alternative is
#: an empty string that reads as "no effort".
PENDING = "pending"

#: A doc_id this repository's own artifacts carry. They are NOT in the manifest by
#: construction — the manifest is the gate into the corpus (DD-003) and an internal artifact is
#: not corpus — so they resolve against the file, never against a `Document` node.
INTERNAL_PREFIX = "internal:"

#: The labels the framework record owns, in the order `scripts/load_framework_graph.py` lists
#: them. Used only by the projection-gate comparison.
FRAMEWORK_LABELS = ("AssessmentCriterion", "AssessmentConstruct", "AssessmentIndicator",
                    "MeasurementSpec", "Action")

#: Labels a `graph` locator may name. A LITERAL whitelist, never a value off a payload —
#: invariant 4: this repository never interpolates payload text into Cypher, and a locator is
#: a dict a caller can hand back. Cypher has no parameter form for a label, so the only safe
#: interpolation is one from a closed set. `run_cypher` is the deliberate exception and has its
#: own two belts.
ADDRESSABLE_LABELS = FRAMEWORK_LABELS + (
    "AssessmentInternalRef", "Finding", "Observation", "Rule", "Document", "Definition")

#: `corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 12 '...': "..."` —
#: the shape `scripts/tag_prescriptions.py` writes every technique source in.
_TECHNIQUE = re.compile(r"^(?P<path>\S+)\s+\(doc_id\s+`(?P<doc_id>[^`]+)`\)"
                        r"(?:,\s*(?P<section>.+?))?\s*:\s*[\"“]", re.DOTALL)


# ------------------------------------------------------------------ the one-database reader

class Graph:
    """A lazy, read-only Neo4j reader bound to the ONE database `seldon.yaml` declares.

    Both belts of decision 1 are here: `guard.assert_allowed_db` on the name before a driver is
    built, and `execute_read` for every statement, which is the driver's own read transaction
    (`default_access_mode="r"` is rejected by driver 6.0.3 — the parity note fss-policy-kg's
    server carries). The keyword rail is the caller's belt and lives in `run_cypher`.
    """

    def __init__(self, database: str | None = None):
        self.database = guard.assert_allowed_db(database or guard.project_database())
        self._driver = None
        self._error = None

    def driver(self):
        """The driver, built once, on first use.

        **Credentials come from this repository's own resolver and NOT from
        `seldon.config.get_neo4j_driver`.** That function reads environment variables only and
        falls back to the literal `neo4j`/`password` when they are unset, which is invisible
        until something authenticates. An MCP client starts this server as a subprocess with an
        environment of its own choosing, so "unset" is the normal case there and not the
        exceptional one: driven over stdio, the server answered `AuthError` to every graph
        question while the identical code answered `green` in a shell that happened to export
        the pair. `scripts/build_projection.py::_neo4j_creds` is the resolver this repository
        already has — both spellings, then `~/.wintermute/.env`, then `SystemExit` naming all
        three (`CLAUDE.md`: "Neo4j creds come from `NEO4J_USER`/`NEO4J_PASS` (fallback:
        `~/.wintermute/.env`)"). One resolver, no second parser, and no guessed password.

        A missing credential raises `SystemExit` and is NOT caught here: it is not an outage,
        it is a mis-installed server, and the two must not read alike to a client.
        """
        if self._driver is None and self._error is None:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "_airkg_build_projection", REPO / "scripts" / "build_projection.py")
            bp = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = bp
            spec.loader.exec_module(bp)
            try:
                _uri, user, password = bp._neo4j_creds()
            except SystemExit as exc:
                # The shared resolver's own message is "no Neo4j credentials in env or
                # ~/.wintermute/.env". Standard 4 asks for the EXACT variable names, and the
                # reader of this one is whoever installed the server in a client that hands it
                # no environment, so the names are the whole diagnosis. The resolver itself is
                # not edited here: it is outside this task's write set and three other callers
                # depend on its message.
                raise SystemExit(
                    f"FATAL: {exc} — this server needs NEO4J_USERNAME/NEO4J_PASSWORD or "
                    f"NEO4J_USER/NEO4J_PASS in its environment, or a ~/.wintermute/.env "
                    f"holding one of those pairs. An MCP client starts this server with an "
                    f"environment of its own, so the file is the reliable one of the two."
                ) from exc
            try:
                import yaml
                from neo4j import GraphDatabase
                cfg = yaml.safe_load((REPO / "seldon.yaml").read_text(encoding="utf-8"))
                guard.assert_allowed_db(str(cfg["neo4j"]["database"]))   # belt 2
                self._driver = GraphDatabase.driver(cfg["neo4j"]["uri"],
                                                    auth=(user, password))
                with self._driver.session(database=self.database) as s:
                    s.run("RETURN 1").single()
            except Exception as exc:                        # noqa: BLE001 — reported, not swallowed
                self._error = f"{type(exc).__name__}: {exc}"
                self._driver = None
        return self._driver

    def available(self) -> bool:
        return self.driver() is not None

    @property
    def error(self) -> str | None:
        return self._error

    def read(self, cypher: str, limit: int | None = None, **params) -> list[dict]:
        """Every row of a read, capped. Raises when the database is unreachable: a tool that
        needed the graph and silently returned nothing would be indistinguishable from a tool
        that found nothing."""
        drv = self.driver()
        if drv is None:
            raise RuntimeError(f"Neo4j unreachable ({self._error}); "
                               f"database {self.database}")
        cap = guard.MAX_ROWS if limit is None else limit
        with drv.session(database=self.database) as s:
            rows = s.execute_read(
                lambda tx: [r.data() for i, r in enumerate(tx.run(cypher, **params))
                            if i < cap + 1])
        return rows[:cap], len(rows) > cap


# ------------------------------------------------------------------------------- locators

def rec_loc(node_id: str) -> dict:
    return {"kind": "record", "path": "framework/ai_readiness_framework.json",
            "node_id": node_id}


def rec_key_loc(key: str) -> dict:
    return {"kind": "record_key", "path": "framework/ai_readiness_framework.json", "key": key}


def config_loc(key: str) -> dict:
    return {"kind": "config", "path": "docs/reports/publication.yaml", "key": key}


def matrix_loc(path: str, cell: str) -> dict:
    return {"kind": "matrix", "path": path, "cell": cell}


def payload_loc(cycle: str, key: str) -> dict:
    return {"kind": "payload", "path": f"state/{cycle}.json", "key": key}


def evidence_loc(path: str, sha256: str) -> dict:
    return {"kind": "evidence", "path": path, "sha256": sha256}


def graph_loc(label: str, id_property: str, value: str) -> dict:
    return {"kind": "graph", "label": label, "id_property": id_property, "id": value}


def document_loc(doc_id: str, section: str | None = None, path: str | None = None) -> dict:
    """A corpus document, or an in-repo artifact when the doc_id is `internal:...`.

    `scripts/tag_prescriptions.py` cites both in the same shape. A corpus doc_id resolves
    against the `Document` node the manifest projected; an `internal:` one has no manifest
    entry by construction (it is this repository's own artifact, and the record lists them in
    `evidence_doc_ids_not_in_manifest` / `AssessmentInternalRef`), so it resolves against the
    FILE the quote names — which is the address a stranger would open either way.
    """
    return {"kind": "document", "doc_id": doc_id, "section": section, "path": path}


def source_loc(path: str, symbol: str) -> dict:
    return {"kind": "source", "path": path, "symbol": symbol}


# ---------------------------------------------------------------------------------- tools

class Tools:
    """The nine verbs. `graph=None` is a working server over the record alone: every framework
    and prescription answer still answers, and a graph question says in words that it cannot be
    answered rather than returning an empty result that reads like a finding."""

    def __init__(self, graph: Graph | None = None):
        self.graph = graph
        self._record = None
        self._publication = None

    # -- sources ------------------------------------------------------------------------

    @property
    def record(self) -> dict:
        if self._record is None:
            self._record = json.loads(RECORD.read_text(encoding="utf-8"))
        return self._record

    @property
    def publication(self) -> dict:
        if self._publication is None:
            import yaml
            self._publication = yaml.safe_load(PUBLICATION.read_text(encoding="utf-8"))
        return self._publication

    @property
    def cycle(self) -> str:
        return self.publication["snapshot_cycle"]

    def _presc(self):
        """`scripts/prescriptions.py`, loaded by path. Decision 2 says `get_prescriptions` is
        that script as a tool, so it IS that script: a second implementation of `failing()` is
        a second answer to "which legs does this body fail", and the two would drift."""
        import importlib.util
        if getattr(self, "_presc_mod", None) is None:
            spec = importlib.util.spec_from_file_location(
                "_airkg_prescriptions", REPO / "scripts" / "prescriptions.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            self._presc_mod = mod
        return self._presc_mod

    def _nodes(self, label: str) -> list[dict]:
        return [n for n in self.record["nodes"] if label in n["labels"]]

    def _node(self, node_id: str) -> dict | None:
        for n in self.record["nodes"]:
            if n["id"] == node_id:
                return n
        return None

    def _indicator(self, code: str) -> dict | None:
        for n in self._nodes("AssessmentIndicator"):
            if n["properties"].get("code") == code:
                return n
        return None

    @staticmethod
    def _rules():
        from scan.rules import CURRENT, parse_rule_id
        return CURRENT, parse_rule_id

    # -- 1. get_overview ----------------------------------------------------------------

    def get_overview(self) -> dict:
        """Call this FIRST. What is in the graph, what cycle its verdicts are from, and whether
        the projection behind any Cypher answer is current."""
        g = self.record
        inds = [n["properties"] for n in self._nodes("AssessmentIndicator")]
        by_tier: dict = {}
        by_basis: dict = {}
        crosstab: list = []
        pairs: dict = {}
        for p in inds:
            t = p.get("measurement_tier") or "unassigned"
            b = p.get("measurement_basis") or "unassigned"
            by_tier[t] = by_tier.get(t, 0) + 1
            by_basis[b] = by_basis.get(b, 0) + 1
            pairs[(t, b)] = pairs.get((t, b), 0) + 1
        for (t, b), n in sorted(pairs.items()):
            crosstab.append({"measurement_tier": t, "measurement_basis": b, "indicators": n})
        cycle = self.cycle
        presc = self._presc()
        bodies = presc.bodies(cycle)
        mats = presc.matrices(cycle)
        payload = self._payload(cycle)
        return {
            "graph": "ai-readiness-kg",
            "database": self.graph.database if self.graph else guard.project_database(),
            "call_first": ("This is the orientation tool. Every other tool's answer carries "
                           "locators; `resolve_locator` opens what one names."),
            "framework": {
                "indicators_total": len(inds),
                "indicators_by_measurement_tier": by_tier,
                "indicators_by_measurement_basis": by_basis,
                "by_tier_and_basis": crosstab,
                "tier_meaning": {
                    "M": "measurable now by this harness or a named structured field",
                    "O": "measurable with an open tool whose documentation is in the corpus",
                    "D": "declaration only — the act happens on the agency's side",
                    "unassigned": "no tier yet, and the node carries the test that failed"},
                "counts": g["counts"],
                "counts_basis": g["counts_basis"],
                "nodes": len(g["nodes"]),
                "edges": len(g["edges"]),
                "actions": sum(1 for n in g["nodes"] if "Action" in n["labels"]),
                "remediates_edges": sum(1 for e in g["edges"] if e["type"] == "REMEDIATES"),
                "locators": [rec_key_loc("counts"), rec_key_loc("counts_basis"),
                             rec_key_loc("nodes"), rec_key_loc("edges")],
            },
            "cycle_of_record": {
                "cycle": cycle,
                "measured": (payload.get("derived_from") or cycle).replace("scan_", ""),
                "kind": payload.get("cycle_kind"),
                "bodies": bodies,
                "n_bodies": len(bodies),
                "matrices": [{"kind": m["_kind"], "path": m["_path"], "legs": m["legs"],
                              "rows": len(m["rows"])} for m in mats],
                "locators": [config_loc("snapshot_cycle"), payload_loc(cycle, "derived_from")]
                            + [matrix_loc(m["_path"], f"{bodies[0]}/{m['legs'][0]}")
                               for m in mats],
            },
            "projection_gate": self.projection_gate(),
            "tools": [t for t in TOOL_ORDER],
        }

    def _payload(self, cycle: str) -> dict:
        p = STATE / f"{cycle}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def projection_gate(self) -> dict:
        """Is the framework layer in Neo4j the record, cell for cell, RIGHT NOW.

        DD-057 and `tests/test_framework_projection_roundtrip.py`: Cypher over this projection
        is valid only while that gate is green. The status is recomputed here rather than
        reported from a stored verdict, because the failure it guards — a write-back that never
        reached the database — is invisible to anything that trusts a cached answer.
        """
        base = {"gate": "tests/test_framework_projection_roundtrip.py",
                "decision": "DD-057",
                "means": ("green: a Cypher answer over the framework labels is the record. "
                          "stale: it is not, and `run_cypher` results about those labels are "
                          "not current. unverified: the database was not reachable."),
                "locators": [source_loc("tests/test_framework_projection_roundtrip.py",
                                        "test_every_json_node_is_in_the_graph_cell_for_cell")]}
        if self.graph is None or not self.graph.available():
            reason = (self.graph.error if self.graph is not None
                      else "no graph was given to this server")
            return {**base, "status": "unverified", "nodes_compared": 0, "mismatches": [],
                    "reason": f"Neo4j unreachable: {reason}"}
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_airkg_load_framework_graph", REPO / "scripts" / "load_framework_graph.py")
        loader = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loader
        spec.loader.exec_module(loader)
        got: dict = {}
        for label in FRAMEWORK_LABELS:
            rows, _ = self.graph.read(
                f"MATCH (n:{label}) RETURN n.id AS id, properties(n) AS p", limit=10_000)
            for r in rows:
                got[r["id"]] = dict(r["p"])
        mismatches = []
        compared = 0
        for n in self.record["nodes"]:
            compared += 1
            have = got.get(n["id"])
            if have is None:
                mismatches.append({"node": n["id"], "property": None,
                                   "record": "present", "graph": "MISSING"})
                continue
            have.pop("id", None)
            want = loader.flatten(n["properties"])
            for k in sorted(set(want) | set(have)):
                if want.get(k) != have.get(k):
                    mismatches.append({"node": n["id"], "property": k,
                                       "record": want.get(k), "graph": have.get(k)})
        return {**base, "status": "green" if not mismatches else "stale",
                "nodes_compared": compared, "mismatches": mismatches[:25],
                "reason": ("every node of the record is in the graph with every property "
                           "equal" if not mismatches else
                           f"{len(mismatches)} property mismatch(es); re-run "
                           f"scripts/load_framework_graph.py")}

    # -- 2. get_indicator ---------------------------------------------------------------

    def get_indicator(self, code: str) -> dict:
        """One indicator: what it says, what measures it, what remediates it, how it fared."""
        node = self._indicator(code)
        if node is None:
            return {"error": f"'{code}' is not an indicator in the framework of record",
                    "codes": [n["properties"]["code"] for n in
                              self._nodes("AssessmentIndicator")],
                    "locators": [rec_key_loc("nodes")]}
        p = dict(node["properties"])
        crit = next((n for n in self._nodes("AssessmentCriterion")
                     if n["properties"].get("code") == p.get("criterion_code")), None)
        construct = next((self._node(e["from"]) for e in self.record["edges"]
                          if e["type"] == "DECOMPOSES_INTO" and e["to"] == node["id"]
                          and (self._node(e["from"]) or {}).get("labels")
                          == ["AssessmentConstruct"]), None)
        spec = next((self._node(e["to"]) for e in self.record["edges"]
                     if e["type"] == "MEASURED_BY" and e["from"] == node["id"]), None)
        acts = []
        for e in self.record["edges"]:
            if e["type"] == "REMEDIATES" and e["to"] == node["id"]:
                a = self._node(e["from"])
                acts.append({"id": a["id"], "title": a["properties"]["title"],
                             "outcome": (e.get("properties") or {}).get("outcome"),
                             "effort": self.band_word(a["properties"], "effort"),
                             "cost": self.band_word(a["properties"], "cost"),
                             "verifies_by": a["properties"].get("verifies_by"),
                             "locator": rec_loc(a["id"])})
        rule = None
        leg = (spec or {}).get("properties", {}).get("leg")
        if leg:
            CURRENT, parse_rule_id = self._rules()
            rid = CURRENT.get(leg)
            if rid:
                rule = {**parse_rule_id(rid), "current": True, "leg": leg,
                        "locator": source_loc(
                            "assessment/harness/scan/rules/__init__.py", "CURRENT")}
        surfaced = {"code", "indicator", "construct", "criterion_code", "tier", "tier_raw",
                    "tier_source", "tier_rule", "measurement_tier", "measurement_basis",
                    "measurement_status", "type", "status"}
        out = {
            "code": code,
            "indicator": p.get("indicator"),
            "construct": p.get("construct"),
            "construct_id": construct["id"] if construct else None,
            "criterion": {"code": p.get("criterion_code"),
                          "name": crit["properties"]["name"] if crit else None,
                          "anchor": crit["properties"].get("anchor") if crit else None,
                          "locator": rec_loc(crit["id"]) if crit else None},
            "type": p.get("type"),
            "status": p.get("status"),
            "tier": p.get("tier"),
            "tier_source": p.get("tier_source"),
            "tier_rule": p.get("tier_rule"),
            "measurement_tier": p.get("measurement_tier"),
            "measurement_basis": p.get("measurement_basis"),
            "measurement_status": p.get("measurement_status"),
            "notes": {k: v for k, v in sorted(p.items()) if k not in surfaced},
            "spec": ({**spec["properties"], "id": spec["id"], "locator": rec_loc(spec["id"])}
                     if spec else None),
            "rule": rule,
            "actions": acts,
            "locators": [rec_loc(node["id"])]
                        + ([rec_loc(construct["id"])] if construct else []),
        }
        out["cycle_of_record"] = self._indicator_verdicts(code)
        return out

    def _indicator_verdicts(self, code: str) -> dict:
        cycle = self.cycle
        base = {"cycle": cycle, "locators": [config_loc("snapshot_cycle")]}
        if self.graph is None or not self.graph.available():
            return {**base, "verdicts": {},
                    "reason": "Neo4j unreachable: Findings are a graph answer and this "
                              "server did not guess one"}
        rows, _ = self.graph.read(
            "MATCH (f:Finding {cycle: $c, indicator_code: $code}) "
            "RETURN f.verdict AS v, count(*) AS n", limit=50, c=cycle, code=code)
        return {**base, "verdicts": {r["v"]: r["n"] for r in rows},
                "locators": base["locators"] + [graph_loc("Finding", "cycle", cycle)]}

    # -- 3. get_body --------------------------------------------------------------------

    def get_body(self, name: str) -> dict:
        """One publisher's row on the cycle of record: every judged leg, the Finding behind the
        verdict, and the retained bytes behind the Finding."""
        cycle = self.cycle
        presc = self._presc()
        all_bodies = presc.bodies(cycle)
        if name not in all_bodies:
            return {"error": f"'{name}' is not a body on cycle {cycle}",
                    "bodies": all_bodies, "locators": [config_loc("snapshot_cycle")]}
        cells = []
        for m in presc.matrices(cycle):
            for r in m["rows"]:
                if r["agency"] != name:
                    continue
                if m["_kind"] == "product" and not r.get("declared"):
                    continue
                surface = r.get("host_surface") or r.get("surface") or r["agency"]
                for leg in m["legs"]:
                    v = r["verdicts"].get(leg)
                    if v is None:
                        continue
                    cells.append({"leg": leg, "verdict": v, "surface": surface,
                                  "url": r.get("host_url") or r.get("url"),
                                  "matrix": m["_path"],
                                  "finding_id": (r.get("finding_ids") or {}).get(leg)})
        ev = self._evidence_for([c["finding_id"] for c in cells if c["finding_id"]])
        for c in cells:
            f = ev.get(c["finding_id"], {})
            c["reason"] = f.get("reason")
            c["rule_id"] = f.get("rule_id")
            c["evidence"] = f.get("observations", [])
            c["locators"] = [matrix_loc(c["matrix"], f"{name}/{c['leg']}")] + (
                [graph_loc("Finding", "finding_id", c["finding_id"])] if c["finding_id"] else [])
        n_fail = sum(1 for c in cells if c["verdict"] == "fail")
        return {
            "body": name, "cycle": cycle,
            "n_judged": len(cells), "n_failing": n_fail,
            "summary": (f"{n_fail} failing of {len(cells)} judged on {cycle}; "
                        f"{len(all_bodies)} bodies are on this cycle"),
            "legs": cells,
            "locators": [config_loc("snapshot_cycle")],
        }

    def _evidence_for(self, finding_ids: list) -> dict:
        """Finding → its Observations → the retained bytes, for many findings in ONE query."""
        if not finding_ids or self.graph is None or not self.graph.available():
            return {}
        rows, _ = self.graph.read(
            "MATCH (f:Finding) WHERE f.finding_id IN $ids "
            "OPTIONAL MATCH (o:Observation)-[:SUPPORTS]->(f) "
            "RETURN f.finding_id AS fid, f.reason AS reason, f.rule_id AS rule_id, "
            "       f.verdict AS verdict, f.indicator_code AS code, "
            "       f.target_doc_id AS target, f.current AS current, "
            "       f.evidence_unretained AS unretained, "
            "       collect({obs_id: o.obs_id, sha256: o.evidence_hash, raw_ref: o.raw_ref, "
            "                captured_at: o.captured_at, collector: o.collector, leg: o.leg, "
            "                error_class: o.error_class, "
            "                error_class_recorded: o.error_class_recorded, "
            "                surface_doc_id: o.surface_doc_id}) AS obs",
            limit=10_000, ids=list(finding_ids))
        out = {}
        for r in rows:
            obs = []
            for o in r["obs"]:
                if not o.get("obs_id"):
                    continue
                obs.append(self._observation(o))
            out[r["fid"]] = {"reason": r["reason"], "rule_id": r["rule_id"],
                             "verdict": r["verdict"], "indicator_code": r["code"],
                             "target_doc_id": r["target"], "current": r["current"],
                             "evidence_unretained": r["unretained"], "observations": obs}
        return out

    def _observation(self, o: dict) -> dict:
        """One Observation with the address of its evidence.

        **Not every Observation retains a response body, and that is by design, not a gap.**
        The `links` collector probes each download link with HEAD and records the status and
        the content type; `collectors/links.py` writes `body_sha256: None, body_path: None`
        deliberately, because there is no body to keep. Its evidence is the recorded fields on
        the Observation itself, so its locator is the Observation node — a locator that
        resolves — and not an `evidence` locator naming a file that was never written.

        This is a different fact from `Finding.evidence_unretained`, which is the append-only
        admission that evidence a Finding DOES cite is gone
        (`cc_tasks/2026-09-07_scan_hygiene.md`). Both are reported, under their own names.
        """
        got = self._bytes(o.get("raw_ref"), o.get("sha256"))
        if got["path"] is None:
            return {**o, **got, "retained": False,
                    "retention": (f"the `{o.get('collector')}` collector retains no response "
                                  f"body for this probe; the observation's own recorded "
                                  f"fields are the evidence"),
                    "locator": graph_loc("Observation", "obs_id", o["obs_id"])}
        return {**o, **got, "retained": True,
                "retention": "response body retained under its sha256",
                "locator": evidence_loc(o["raw_ref"], o["sha256"])}

    @staticmethod
    def _bytes(raw_ref: str | None, sha256: str | None) -> dict:
        """Is the evidence actually on disk, and does it hash to the name it is filed under.

        Both answers, never one: a path that exists proves nothing about the bytes, and the
        whole point of a content-addressed store is that the name IS the check.
        """
        if not raw_ref:
            return {"path": None, "exists": False, "sha256_verified": False,
                    "bytes": None}
        p = REPO / raw_ref
        if not p.exists():
            return {"path": raw_ref, "exists": False, "sha256_verified": False, "bytes": None}
        data = p.read_bytes()
        return {"path": raw_ref, "exists": True, "bytes": len(data),
                "sha256_verified": hashlib.sha256(data).hexdigest() == sha256}

    # -- 4. get_prescriptions -----------------------------------------------------------

    @staticmethod
    def band_word(a: dict, which: str) -> str:
        """One band as its word. A band with no estimate behind it reads `pending` and never a
        number (decision 2); a band with a document locator carries the locator, because that
        is the one a reader may rely on without adjusting it for their own shop."""
        value = a.get(f"{which}_band")
        src = a.get(f"{which}_source") or ""
        if not value or src.startswith("estimate:pending"):
            return PENDING
        return value if src.startswith("notional:") else f"{value} ({src})"

    def get_prescriptions(self, body: str | None = None, leg: str | None = None) -> dict:
        """`scripts/prescriptions.py` as a tool. With neither argument: every action, ranked by
        how many bodies fail it now."""
        presc = self._presc()
        cycle = self.cycle
        acts = presc.actions(self.record)
        all_bodies = presc.bodies(cycle)
        failing_legs = None
        if body is not None:
            if body not in all_bodies:
                return {"error": f"'{body}' is not a body on cycle {cycle}",
                        "bodies": all_bodies, "locators": [config_loc("snapshot_cycle")]}
            failing = presc.failing(cycle).get(body, {})
            failing_legs = sorted(failing)
            acts = [a for a in acts if a["leg"] in failing]
        if leg is not None:
            acts = [a for a in acts if a["leg"] == leg]
        rows = []
        for a in acts:
            rows.append({
                "id": a["id"], "title": a["title"], "description": a["description"],
                "leg": a["leg"], "outcome": a["outcome"], "indicator_id": a["indicator_id"],
                "effort": self.band_word(a, "effort"), "effort_source": a["effort_source"],
                "cost": self.band_word(a, "cost"), "cost_source": a["cost_source"],
                "technique_class": a["technique_class"],
                "technique_source": a["technique_source"],
                "verifies_by": a["verifies_by"],
                "applies_to_publisher": a["applies_to_publisher"],
                "value": a["value"],
                "failing_on": sorted(set(presc.failing(cycle).get(body, {}).get(a["leg"], [])))
                              if body else None,
                "locators": [rec_loc(a["id"]), rec_loc(a["indicator_id"])]
                            + [document_loc(d, sec, path) for d, sec, path in
                               (_technique_address(t) for t in a["technique_source"]) if d],
            })
        return {
            "cycle": cycle, "body": body, "leg": leg,
            "failing_legs": failing_legs,
            "bodies_on_cycle": len(all_bodies),
            "notional": "(notional)",
            "band_note": presc.band_note(presc.actions(self.record)),
            "ranked_by": "value.bodies_failing_now, then leg, then action id",
            "actions": rows,
            "locators": [rec_key_loc("nodes"), config_loc("snapshot_cycle")],
        }

    # -- 5. get_evidence ----------------------------------------------------------------

    def get_evidence(self, finding_id: str) -> dict:
        """One Finding, down to the bytes: every Observation it cites, the retained response
        body, its sha256, when it was captured, and the rule version that judged it."""
        if self.graph is None or not self.graph.available():
            return {"error": "Neo4j unreachable: evidence lives on the Observations in the "
                             "projection of the event log and this server did not guess it",
                    "locators": []}
        found = self._evidence_for([finding_id])
        if finding_id not in found:
            return {"error": f"no Finding `{finding_id}` in the graph",
                    "locators": [graph_loc("Finding", "finding_id", finding_id)]}
        f = found[finding_id]
        _, parse_rule_id = self._rules()
        parsed = parse_rule_id(f["rule_id"]) if f["rule_id"] else {}
        return {
            "finding_id": finding_id,
            "verdict": f["verdict"], "reason": f["reason"],
            "rule_id": f["rule_id"], "rule_version": parsed.get("version"),
            "indicator_code": f["indicator_code"], "target_doc_id": f["target_doc_id"],
            "current": f["current"], "evidence_unretained": f["evidence_unretained"],
            "observations": f["observations"],
            "note": ("`error_class_recorded` is the class the log holds and `error_class` the "
                     "corrected one, where an `observation_error_reclassified` overlay exists; "
                     "the log line is never edited."),
            "locators": [graph_loc("Finding", "finding_id", finding_id)],
        }

    # -- 6. get_document ----------------------------------------------------------------

    def get_document(self, doc_id: str) -> dict:
        """A corpus document by doc_id: its provenance, and what the graph hangs off it."""
        if self.graph is None or not self.graph.available():
            return {"error": "Neo4j unreachable: the corpus layer is a projection of the "
                             "event log and this server did not guess it", "locators": []}
        rows, _ = self.graph.read(
            "MATCH (d:Document {doc_id: $id}) RETURN properties(d) AS p", limit=2, id=doc_id)
        if not rows:
            near, _ = self.graph.read(
                "MATCH (d:Document) WHERE d.doc_id CONTAINS $frag "
                "RETURN d.doc_id AS id ORDER BY d.doc_id", limit=10,
                frag=doc_id.split("-")[0])
            return {"error": f"no Document `{doc_id}` in the graph",
                    "nearest": [r["id"] for r in near],
                    "locators": [graph_loc("Document", "doc_id", doc_id)]}
        p = dict(rows[0]["p"])
        counts, _ = self.graph.read(
            "MATCH (n) WHERE n.doc_id = $id AND NOT n:Document "
            "RETURN labels(n)[0] AS l, count(*) AS c", limit=50, id=doc_id)
        ev, _ = self.graph.read(
            "MATCH (i:AssessmentIndicator)-[:EVIDENCED_BY]->(d:Document {doc_id: $id}) "
            "RETURN i.code AS code ORDER BY i.code", limit=100, id=doc_id)
        return {**p, "doc_id": doc_id,
                "counts": {"definitions": 0, **{r["l"].lower() + "s": r["c"] for r in counts}},
                "evidences_indicators": [r["code"] for r in ev],
                "locators": [graph_loc("Document", "doc_id", doc_id), document_loc(doc_id)]}

    # -- 7. search_text -----------------------------------------------------------------

    def search_text(self, q: str, limit: int = 20) -> dict:
        """Lexical, case-insensitive search over the definition layer, the indicator text, the
        action descriptions and the technique quotes.

        `doc_id` and `section` are the corpus address where the text HAS one — a Definition
        carries both, and a technique quote carries them because `tag_prescriptions.py` writes
        the locator into the quote. Indicator and action text has no corpus document: it is the
        record's own prose, and its address is the `record` locator on the hit.
        """
        hits: list = []
        needle = q.lower()
        for n in self._nodes("AssessmentIndicator"):
            p = n["properties"]
            text = f"{p.get('indicator') or ''} {p.get('construct') or ''}"
            if needle in text.lower():
                hits.append({"kind": "indicator", "code": p.get("code"),
                             "text": p.get("indicator"), "doc_id": None,
                             "section": p.get("construct"), "locator": rec_loc(n["id"])})
        for n in self._nodes("Action"):
            p = n["properties"]
            if needle in f"{p.get('title') or ''} {p.get('description') or ''}".lower():
                hits.append({"kind": "action", "code": p.get("leg"), "text": p.get("title"),
                             "doc_id": None, "section": p.get("outcome"),
                             "locator": rec_loc(n["id"])})
            for t in p.get("technique_source") or []:
                if needle in t.lower():
                    doc_id, section, path = _technique_address(t)
                    hits.append({"kind": "technique", "code": p.get("leg"), "text": t,
                                 "doc_id": doc_id, "section": section,
                                 "locator": document_loc(doc_id, section, path) if doc_id
                                 else rec_loc(n["id"])})
        graph_hits = 0
        if self.graph is not None and self.graph.available():
            rows, _ = self.graph.read(
                "MATCH (d:Definition) WHERE toLower(d.verbatim_text) CONTAINS $q "
                "   OR toLower(coalesce(d.term, '')) CONTAINS $q "
                "RETURN d.key AS key, d.term AS term, d.verbatim_text AS text, "
                "       d.doc_id AS doc_id, d.location AS section "
                "ORDER BY d.key", limit=limit, q=needle)
            graph_hits = len(rows)
            for r in rows:
                hits.append({"kind": "definition", "code": r["term"], "text": r["text"],
                             "doc_id": r["doc_id"], "section": r["section"],
                             "locator": graph_loc("Definition", "key", r["key"])})
        return {"query": q, "hits": hits[:limit], "n_hits": len(hits),
                "truncated": len(hits) > limit,
                "searched": ["AssessmentIndicator.indicator (record)",
                             "Action.title/description (record)",
                             "Action.technique_source (record)",
                             "Definition.verbatim_text/term (graph)"
                             if graph_hits or (self.graph and self.graph.available())
                             else "Definition (SKIPPED: Neo4j unreachable)"],
                "locators": [rec_key_loc("nodes")]}

    # -- 8. get_cycle_of_record ---------------------------------------------------------

    def get_cycle_of_record(self) -> dict:
        """What cycle every verdict in this graph's published views comes from, and whether a
        later judgement of the same evidence exists."""
        cycle = self.cycle
        payload = self._payload(cycle)
        presc = self._presc()
        mats = [{"kind": m["_kind"], "path": m["_path"], "legs": m["legs"],
                 "rows": len(m["rows"]), "params_hash": m["params_hash"],
                 "locator": matrix_loc(m["_path"], f"{presc.bodies(cycle)[0]}/{m['legs'][0]}")}
                for m in presc.matrices(cycle)]
        out = {
            "cycle": cycle,
            "kind": payload.get("cycle_kind"),
            "derived_from": payload.get("derived_from"),
            "derived_from_params_hash": payload.get("derived_from_params_hash"),
            "judgement_params_hash": payload.get("params_hash"),
            "hash_meaning": ("`derived_from_params_hash` identifies the COLLECTION the "
                            "evidence came from; `judgement_params_hash` identifies this "
                            "judgement of it. A re-judgement re-reads stored observations and "
                            "fetches nothing."),
            "rejudged_note": payload.get("rejudged_note"),
            "rules": payload.get("rules"),
            "legs_judged": payload.get("legs_judged"),
            "legs_not_judged": payload.get("legs_not_judged"),
            "verdict_counts": payload.get("verdict_counts"),
            "matrices": mats,
            "locators": [config_loc("snapshot_cycle"),
                         payload_loc(cycle, "derived_from_params_hash"),
                         payload_loc(cycle, "params_hash")],
        }
        out["supersession"] = self._supersession(cycle)
        return out

    def _supersession(self, cycle: str) -> dict:
        """DN-004: a later judgement of the same evidence that moves no published number does
        not force a republication — and the report says so from the graph. The same query, from
        `scripts/snapshot_successor.py`, answers it here."""
        if self.graph is None or not self.graph.available():
            return {"status": "unverified",
                    "reason": "Neo4j unreachable: supersession is a fact about two Findings "
                              "and lives on the graph"}
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_airkg_snapshot_successor", REPO / "scripts" / "snapshot_successor.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        drv = self.graph.driver()
        with drv.session(database=self.graph.database) as s:
            info = mod.successor_info(s, cycle)
        line = mod.supersession_line(info)
        return {**info, "line": line, "decision": "DN-004 decision 1",
                "locators": [source_loc("scripts/snapshot_successor.py", "successor_info")]
                            + ([graph_loc("Finding", "cycle", info["successor"])]
                               if info else [])}

    # -- 9. run_cypher ------------------------------------------------------------------

    def run_cypher(self, query: str) -> dict:
        """The escape hatch, read-only. A write is refused with a sentence, not an exception."""
        refused = guard.refusal(query)
        if refused is not None:
            return {"refused": refused, "database": (self.graph.database if self.graph
                                                     else guard.project_database())}
        if self.graph is None or not self.graph.available():
            return {"error": "Neo4j unreachable", "database": guard.project_database()}
        rows, truncated = self.graph.read(query)
        return {"rows": rows, "row_count": len(rows), "truncated": truncated,
                "max_rows": guard.MAX_ROWS, "database": self.graph.database,
                "projection_gate": self.projection_gate()["status"],
                "locator": {"kind": "graph", "label": "*", "id_property": "database",
                            "id": self.graph.database}}

    # ------------------------------------------------------------------ the resolver

    def resolve_locator(self, loc: dict) -> dict:
        """Open what a locator names and say whether it is there. Decision 2's test."""
        kind = (loc or {}).get("kind")
        try:
            if kind in ("record", "record_key"):
                if not RECORD.exists():
                    return _no(f"{loc.get('path')} does not exist")
                if kind == "record_key":
                    return (_yes(f"record key `{loc['key']}`")
                            if loc.get("key") in self.record else
                            _no(f"the record has no top-level key `{loc.get('key')}`"))
                return (_yes(f"node {loc['node_id']}") if self._node(loc.get("node_id"))
                        else _no(f"the record holds no node `{loc.get('node_id')}`"))
            if kind == "config":
                return (_yes(f"publication.yaml:{loc['key']}")
                        if loc.get("key") in self.publication
                        else _no(f"publication.yaml has no key `{loc.get('key')}`"))
            if kind == "matrix":
                p = REPO / loc["path"]
                if not p.exists():
                    return _no(f"{loc['path']} does not exist")
                m = json.loads(p.read_text(encoding="utf-8"))
                body, _, leg = (loc.get("cell") or "").partition("/")
                row = next((r for r in m["rows"] if r["agency"] == body), None)
                if row is None:
                    return _no(f"{loc['path']} has no row for `{body}`")
                if leg not in m["legs"]:
                    return _no(f"{loc['path']} does not judge leg `{leg}`")
                return _yes(f"{loc['path']} cell {loc['cell']}")
            if kind == "payload":
                p = REPO / loc["path"]
                if not p.exists():
                    return _no(f"{loc['path']} does not exist")
                d = json.loads(p.read_text(encoding="utf-8"))
                return (_yes(f"{loc['path']}:{loc['key']}") if loc.get("key") in d
                        else _no(f"{loc['path']} has no key `{loc.get('key')}`"))
            if kind == "evidence":
                got = self._bytes(loc.get("path"), loc.get("sha256"))
                if not got["exists"]:
                    return _no(f"{loc.get('path')} is not on disk")
                if not got["sha256_verified"]:
                    return _no(f"{loc['path']} does not hash to {loc.get('sha256')}")
                return _yes(f"{loc['path']} ({got['bytes']} bytes, sha256 verified)")
            if kind == "graph":
                if self.graph is None or not self.graph.available():
                    return _no("Neo4j unreachable; a graph locator cannot be resolved")
                if loc.get("label") == "*":
                    return _yes(f"database {self.graph.database}")
                if loc.get("label") not in ADDRESSABLE_LABELS:
                    return _no(f"`{loc.get('label')}` is not a label this server addresses "
                               f"({', '.join(ADDRESSABLE_LABELS)}); a label cannot be a query "
                               f"parameter, so it comes from a closed set or not at all")
                rows, _ = self.graph.read(
                    f"MATCH (n:{loc['label']}) WHERE n[$k] = $v RETURN count(n) AS c",
                    limit=1, k=loc["id_property"], v=loc["id"])
                return (_yes(f"{loc['label']} {loc['id']}") if rows and rows[0]["c"]
                        else _no(f"no {loc['label']} with {loc['id_property']}="
                                 f"{loc['id']!r}"))
            if kind == "document":
                doc_id = loc.get("doc_id") or ""
                if doc_id.startswith(INTERNAL_PREFIX):
                    if not loc.get("path"):
                        return _no(f"`{doc_id}` is an internal reference and the locator "
                                   f"names no file")
                    f = REPO / loc["path"]
                    if not f.exists():
                        return _no(f"{loc['path']} does not exist")
                    section = (loc.get("section") or "").strip("`")
                    if section and section not in f.read_text(encoding="utf-8",
                                                              errors="replace"):
                        return _no(f"{loc['path']} does not contain `{section}`")
                    return _yes(f"{loc['path']}" + (f" ({section})" if section else ""))
                if self.graph is None or not self.graph.available():
                    return _no("Neo4j unreachable; a document locator cannot be resolved")
                rows, _ = self.graph.read(
                    "MATCH (d:Document {doc_id: $id}) RETURN count(d) AS c",
                    limit=1, id=doc_id)
                return (_yes(f"Document {doc_id}") if rows and rows[0]["c"]
                        else _no(f"no Document `{doc_id}`"))
            if kind == "source":
                p = REPO / loc["path"]
                if not p.exists():
                    return _no(f"{loc['path']} does not exist")
                return (_yes(f"{loc['path']}:{loc['symbol']}")
                        if loc.get("symbol") in p.read_text(encoding="utf-8")
                        else _no(f"{loc['path']} does not contain `{loc.get('symbol')}`"))
        except Exception as exc:                            # noqa: BLE001 — reported, not hidden
            return _no(f"{type(exc).__name__}: {exc}")
        return _no(f"unknown locator kind {kind!r}")


def _yes(detail: str) -> dict:
    return {"resolved": True, "detail": detail}


def _no(detail: str) -> dict:
    return {"resolved": False, "detail": detail}


def _technique_address(quote: str) -> tuple:
    """`(doc_id, section, path)` out of a technique source, or `(None, None, None)`.

    The quote is written by `scripts/tag_prescriptions.py` in one shape, so this parses that
    shape and reports failure rather than guessing: a doc_id invented from a path is a locator
    a stranger cannot check, which is the one thing a locator may not be.
    """
    m = _TECHNIQUE.match(quote.strip())
    if not m:
        return (None, None, None)
    section = (m.group("section") or "").strip().strip("'‘’")
    return (m.group("doc_id"), section or None, m.group("path"))


#: The order `get_overview` lists the tools in, and the order the server registers them.
TOOL_ORDER = ("get_overview", "get_indicator", "get_body", "get_prescriptions",
              "get_evidence", "get_document", "search_text", "get_cycle_of_record",
              "run_cypher")
