#!/usr/bin/env python3
"""The two rails of the read-only MCP server: one database, and reads only.

`cc_tasks/2026-09-17_mcp_over_the_graph.md` decision 1. **Pure functions, no driver, no
network** — the whole point of lifting them out of the server module is that they unit-test
offline, which is how `icsp_notebook/kg/mcp_server.py` (the fss-policy-kg server) tests its own
two rails and why this file is shaped like that one.

**What was copied from fss-policy-kg:** the keyword rail itself, string-literal stripping
before the scan (so a query searching for the literal text `create` is not read as a `CREATE`
clause), and the posture that the guard is belt one and an explicit READ transaction is belt
two.

**What had to differ, and it is the whole rail:**

* **The database allow-list is inverted.** That server refuses a database named
  `wintermute-intake` or `seldon-*`, because its own database is `fss-policy-kg` and those are
  other projects' graphs. This project's database IS `seldon-ai-readiness-kg`, so the same
  pattern rail would refuse the only database this server may touch. The rail here is
  therefore an allow-list of exactly ONE name, read from `seldon.yaml:neo4j.database` — the
  file the project already declares it in — and never from a caller parameter.
* **Comments are stripped as well as string literals.** `MATCH (n) // harmless` on one line and
  `DELETE n` on the next is a write that a literal-only strip does not see, because the
  keyword is not inside quotes; it is the line-comment that hides it from a reader, not from
  the database.
* **`CALL` is closed, not filtered.** Decision 1 names "`CALL … write procedures`". A blocklist
  of write procedures is a list that a new procedure defeats, so this rail allows only the
  read procedures it names (`db.labels`, `db.relationshipTypes`, `db.propertyKeys`,
  `db.schema.*`) plus an anonymous `CALL { ... }` subquery whose body is itself scanned. Every
  other `CALL` is refused by name. `apoc.create.node` is refused because it is not on the
  list, not because anyone enumerated it.
* **A refusal is a returned message, not an exception** (decision 1), so `refusal()` returns
  the sentence or `None`. The database rail still raises `SystemExit`: a mis-scoped server must
  never start, and there is no caller to hand a message to at startup.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SELDON_YAML = REPO / "seldon.yaml"

#: The flood guard, the same 200 the fss-policy-kg server caps `run_cypher` at.
MAX_ROWS = 200

#: Write clauses. `DROP` and `FOREACH` are not in decision 1's list and are here anyway: they
#: are in the rail this one was copied from, and a rail that drops a verb on its way across is
#: not a copy.
_WRITE_KW = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|FOREACH|LOAD\s+CSV)\b", re.IGNORECASE)

#: Procedures a read may call. Anything else is refused BY NAME — see the module docstring on
#: why this is an allow-list.
READ_PROCEDURES = ("db.labels", "db.relationshiptypes", "db.propertykeys",
                   "db.schema.visualization", "db.schema.nodetypeproperties",
                   "db.schema.reltypeproperties", "db.indexes", "db.constraints")

_STRING_LIT = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_CALL_NAME = re.compile(r"\bCALL\s+([A-Za-z_][\w.]*)", re.IGNORECASE)


def _scrub(cypher: str) -> str:
    """Strings and comments out; everything a write could hide behind, gone. Replaced by `''`
    rather than deleted so token boundaries survive the strip."""
    out = _BLOCK_COMMENT.sub(" ", cypher)
    out = _LINE_COMMENT.sub(" ", out)
    return _STRING_LIT.sub("''", out)


def refusal(cypher: str) -> str | None:
    """The refusal sentence for a statement that is not a read, or `None` if it is one.

    Returns rather than raises (decision 1): the client asked a question and gets an answer
    saying why it will not be run, which is a fact about the server and not a crash.
    """
    if not cypher or not cypher.strip():
        return "refused: empty query — this server is read-only and has nothing to read"
    scrubbed = _scrub(cypher)
    # The CALL rail runs FIRST so a named procedure is refused as a procedure. `apoc.create.node`
    # trips the keyword rail too — `.` is a word boundary, so `\bCREATE\b` matches inside the
    # name — and "`create` is a write clause" is a true sentence about the wrong thing: the
    # caller needs to be told the procedure is not on the allow-list, which is why it was
    # refused and what a different procedure name would change.
    for name in _CALL_NAME.findall(scrubbed):
        if name.lower() not in READ_PROCEDURES:
            return (f"refused: `CALL {name}` is not one of the read procedures this "
                    f"read-only server allows ({', '.join(READ_PROCEDURES)}). A blocklist of "
                    f"write procedures is defeated by the next procedure; this is an "
                    f"allow-list.")
    m = _WRITE_KW.search(scrubbed)
    if m:
        verb = " ".join(m.group(1).split())
        return (f"refused: `{verb}` is a write clause and this server is read-only. "
                f"The graph is a projection; it is rebuilt from the event log and the "
                f"framework record, never edited through a query.")
    return None


def project_database() -> str:
    """The ONE database this server may touch, read from `seldon.yaml:neo4j.database`.

    Never a caller parameter and never a literal in this file: the project declares its
    database in one place, and a second copy here would be the drift the declaration exists to
    prevent.
    """
    import yaml
    cfg = yaml.safe_load(SELDON_YAML.read_text(encoding="utf-8"))
    db = cfg["neo4j"]["database"]
    if not isinstance(db, str) or not db.strip():
        raise SystemExit(f"FATAL: {SELDON_YAML} declares no neo4j.database")
    return db


def assert_allowed_db(db: str) -> str:
    """Refuse any database but this project's. Fails LOUD, at startup, so a mis-scoped server
    never serves: there is no client yet to return a message to."""
    allowed = project_database()
    if db != allowed:
        raise SystemExit(
            f"FATAL: refusing Neo4j database '{db}' — this server is scoped to "
            f"'{allowed}' (seldon.yaml:neo4j.database) and to no other graph")
    return db
